"""The assistant: understand a question in Twi, Ga, Ewe, Hausa or English, answer it from sources,
and reply in the language the user picks.

    question (any of the five) -> English, by the best translation model for that language
    English question -> Wikipedia search, ranked passages, answer with citations or "I don't know"
    English answer -> the reply language, with protected terms checked

Which model translates which direction comes from the benchmark in results/ (ROUTES below).
"""

from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .llm import LlamaServer
from .wiki import Passage, Wikipedia

ROOT = Path(__file__).resolve().parents[2]
LANG_NAMES = {"en": "English", "twi": "Twi (Akan)", "gaa": "Ga", "ewe": "Ewe", "hau": "Hausa"}
# best model per direction on the translation benchmark (results/mt_*); Ga has only OPUS-MT.
# English to Twi uses GhanaNLP's gloss-mt NLLB 1.3B, which beat plain NLLB 1.3B on FLORES (38.7 vs 37.4 chrF++)
ROUTES = {
    ("twi", "en"): "nllb_1.3b",
    ("en", "twi"): "glossmt_nllb_1.3b",
    ("ewe", "en"): "nllb_1.3b",
    ("en", "ewe"): "nllb_1.3b",
    ("hau", "en"): "nllb_1.3b",
    ("en", "hau"): "nllb_1.3b",
    ("gaa", "en"): "opus_mt",
    ("en", "gaa"): "opus_mt",
}
DONT_KNOW = "I don't know based on the sources I found."
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

QUERY_PROMPT = """Write a short Wikipedia search query (2 to 6 words) that would find the article answering this question. Use only names and words from the question; do not guess the answer. Reply with the query only.

Question: {question}"""

ANSWER_PROMPT = (
    """You answer questions about Ghana and everyday life using only the numbered passages below.

Rules:
- Answer in one or two short sentences, starting with the answer itself.
- Use only facts stated in the passages. Do not add anything from memory.
- Cite the passages you used like [1] or [2][3].
- If the passages do not state the answer, reply exactly: """
    + DONT_KNOW
    + """

Passages:
{passages}

Question: {question}

Answer:"""
)


@dataclass
class Term:
    en: str
    keep: bool  # keep the English form in every language (an acronym or a name)
    local: dict = field(default_factory=dict)  # lang -> local term, only where a person supplied it
    source: str = ""


def load_glossary(path: Path = ROOT / "data" / "glossary.csv") -> list[Term]:
    if not path.exists():
        return []
    out = []
    for r in csv.DictReader(path.open()):
        local = {k: r[k].strip() for k in ("twi", "gaa", "ewe", "hau") if r.get(k, "").strip()}
        out.append(Term(r["en"].strip(), r.get("keep", "").strip().lower() in ("1", "yes", "true"), local, r.get("source", "")))
    return out


def protected_in(text: str, glossary: list[Term]) -> list[Term]:
    return [t for t in glossary if t.keep and re.search(rf"(?<!\w){re.escape(t.en)}(?!\w)", text, re.I)]


def check_terms(source_en: str, translated: str, glossary: list[Term]) -> dict:
    """Which protected English terms in the source survive the translation unchanged."""
    found = protected_in(source_en, glossary)
    kept = [t.en for t in found if re.search(rf"(?<!\w){re.escape(t.en)}(?!\w)", translated, re.I)]
    return {"protected": [t.en for t in found], "kept": kept}


def localize_terms(text: str, lang: str, glossary: list[Term]) -> str:
    """Before translating a question into English, swap in the English for local terms a person supplied."""
    for t in glossary:
        loc = t.local.get(lang)
        if loc:
            text = re.sub(rf"(?<!\w){re.escape(loc)}(?!\w)", t.en, text, flags=re.I)
    return text


class Translator:
    def __init__(self):
        self._models = {}

    def __call__(self, text: str, src: str, tgt: str) -> str:
        if src == tgt:
            return text
        from .mt import load

        name = ROUTES[(src, tgt)]
        if name not in self._models:
            self._models[name] = load(name)
        # translate sentence by sentence so long answers are not cut
        parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]
        return " ".join(self._models[name].translate(parts, src, tgt))


_enc: dict = {}


def _embed():
    if "e" not in _enc:
        from sentence_transformers import SentenceTransformer

        _enc["e"] = SentenceTransformer(EMBED_MODEL, device="cpu")
    return _enc["e"]


def _rerank():
    if "r" not in _enc:
        from sentence_transformers import CrossEncoder

        _enc["r"] = CrossEncoder(RERANK_MODEL, device="cpu")
    return _enc["r"]


def retrieve(llm: LlamaServer, wiki: Wikipedia, question: str, pages: int = 6, top: int = 6) -> tuple[list[tuple[Passage, float]], dict]:
    q = llm.chat(QUERY_PROMPT.format(question=question), temperature=0.0, max_tokens=24)["text"]
    query = re.sub(r'^(query:\s*)|["\']', "", (q.strip().splitlines() or [""])[0], flags=re.I).strip()[:120]
    titles: list[str] = []
    for s in (query, question):
        if s:
            for t in wiki.search(s, limit=3):
                if t not in titles:
                    titles.append(t)
    titles = titles[:pages]
    passages = [p for t in titles for p in wiki.page(t)]
    if not passages:
        return [], {"query": query, "titles": titles}
    texts = [p.render() for p in passages]
    pv = _embed().encode(texts, batch_size=64)
    qv = _embed().encode([question])[0]
    sims = pv @ qv / (np.linalg.norm(pv, axis=1) * np.linalg.norm(qv) + 1e-9)
    cand = np.argsort(-sims)[:40]
    scores = _rerank().predict([(question, texts[i]) for i in cand], batch_size=32)
    order = np.argsort(-np.asarray(scores))[:top]
    return [(passages[cand[i]], float(scores[i])) for i in order], {"query": query, "titles": titles}


class Assistant:
    def __init__(self, llm: LlamaServer, wiki: Wikipedia, translator: Translator | None = None, glossary: list[Term] | None = None):
        self.llm, self.wiki = llm, wiki
        self.translate = translator or Translator()
        self.glossary = load_glossary() if glossary is None else glossary

    def ask(self, question: str, lang: str, reply_lang: str) -> dict:
        t0 = time.time()
        q_en = self.translate(localize_terms(question, lang, self.glossary), lang, "en") if lang != "en" else question
        t1 = time.time()
        ranked, info = retrieve(self.llm, self.wiki, q_en)
        if ranked:
            block = "\n\n".join(f"[{i + 1}] {p.render()}" for i, (p, _) in enumerate(ranked))
            answer_en = self.llm.chat(ANSWER_PROMPT.format(passages=block, question=q_en), temperature=0.0, max_tokens=160)["text"]
        else:
            answer_en = DONT_KNOW
        t2 = time.time()
        # citations stay as numbers; strip them for translation and add them back at the end
        cites = re.findall(r"\[\d+\]", answer_en)
        plain = re.sub(r"\s*\[\d+\]", "", answer_en).strip()
        reply = self.translate(plain, "en", reply_lang) if reply_lang != "en" else plain
        terms = check_terms(plain, reply, self.glossary) if reply_lang != "en" else {"protected": [], "kept": []}
        t3 = time.time()
        cited = sorted({int(c.strip("[]")) for c in cites})
        sources = [{"n": i + 1, "title": p.title, "section": p.section, "url": p.url, "revid": p.revid, "text": p.text} for i, (p, _) in enumerate(ranked)]
        return {
            "question": question,
            "lang": lang,
            "reply_lang": reply_lang,
            "question_en": q_en,
            "answer_en": answer_en,
            "reply": reply + ("" if not cited else " " + "".join(f"[{n}]" for n in cited)),
            "cited": cited,
            "sources": sources,
            "terms": terms,
            "seconds": {"to_english": round(t1 - t0, 2), "answer": round(t2 - t1, 2), "to_reply": round(t3 - t2, 2)},
            **info,
        }
