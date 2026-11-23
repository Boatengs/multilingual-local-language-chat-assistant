"""End to end test: ask every question in every language, reply in English for scoring, then grade.

    python -m kasa.e2e make-mt --questions data/qa/questions_en.csv --out data/qa/questions_mt.csv
    python -m kasa.e2e answer --questions data/qa/questions_all.csv --out out --shard 0 --n-shards 4
    python -m kasa.e2e grade --answers out/answers_0.jsonl --out out --llm http://127.0.0.1:8081

The grader prompt is OpenAI's SimpleQA template (MIT licence), unchanged, in grader_template.txt.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from .llm import LlamaServer

TEMPLATE = (Path(__file__).parent / "grader_template.txt").read_text()
LETTER = {"A": "CORRECT", "B": "INCORRECT", "C": "NOT_ATTEMPTED"}


def read_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(Path(path).open()))


def make_mt(questions: Path, out: Path, langs=("twi", "ewe", "gaa", "hau")) -> None:
    """Machine translated questions, a stand in until human translations exist. Marked source=mt."""
    from .assistant import Translator

    tr = Translator()
    rows = []
    for q in read_csv(questions):
        rows.append({"id": q["id"], "topic": q["topic"], "lang": "en", "question": q["question"], "answer": q["answer"], "source": "original"})
        for lang in langs:
            rows.append({"id": q["id"], "topic": q["topic"], "lang": lang, "question": tr(q["question"], "en", lang), "answer": q["answer"], "source": "mt"})
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def answer(questions: Path, out: Path, shard: int, n_shards: int, llm_url: str, cache: Path, kb_mode: str = "none") -> None:
    from .assistant import Assistant
    from .kb import KB
    from .wiki import Wikipedia

    rows = read_csv(questions)[shard::n_shards]
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"answers_{shard}.jsonl"
    done = {json.loads(x)["key"] for x in path.read_text().splitlines()} if path.exists() else set()
    llm = LlamaServer(llm_url)
    llm.wait()
    kb = None if kb_mode == "none" else KB(include_question_sources=(kb_mode == "official+question_sources"))
    bot = Assistant(llm, Wikipedia(cache_dir=cache), kb=kb)
    with path.open("a") as f:
        for r in rows:
            key = f"{r['id']}|{r['lang']}|{r['source']}"
            if key in done:
                continue
            try:
                res = bot.ask(r["question"], r["lang"], "en")
                res["error"] = None
            except Exception as e:
                res = {"answer_en": "", "error": f"{type(e).__name__}: {e}"}
            res.update(
                {"key": key, "id": r["id"], "topic": r["topic"], "lang": r["lang"], "source": r["source"], "gold": r["answer"], "question": r["question"]}
            )
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            print(key, res.get("question_en", ""), "->", res.get("answer_en", "")[:80], flush=True)


def grade(answers: Path, out: Path, llm_url: str, questions_en: Path) -> None:
    en = {q["id"]: q["question"] for q in read_csv(questions_en)}
    llm = LlamaServer(llm_url)
    llm.wait()
    path = out / answers.name.replace("answers_", "graded_")
    with path.open("w") as f:
        for line in answers.read_text().splitlines():
            r = json.loads(line)
            # grade against the original English question, so a mistranslated question counts against the system
            prompt = (
                TEMPLATE.replace("{question}", en[r["id"]])
                .replace("{target}", r["gold"])
                .replace("{predicted_answer}", re.sub(r"\s*\[\d+\]", "", r.get("answer_en", "")))
            )
            raw = llm.chat(prompt, temperature=0.0, max_tokens=4)["text"]
            m = re.search(r"(A|B|C)", raw)
            f.write(json.dumps({"key": r["key"], "grade": LETTER[m.group(0)] if m else "NOT_ATTEMPTED", "grader_raw": raw}) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("make-mt")
    a.add_argument("--questions", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    b = sub.add_parser("answer")
    b.add_argument("--questions", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--shard", type=int, default=0)
    b.add_argument("--n-shards", type=int, default=1)
    b.add_argument("--llm", default="http://127.0.0.1:8080")
    b.add_argument("--cache", type=Path, default=Path("wikicache"))
    b.add_argument("--kb", default="none", choices=["none", "official", "official+question_sources"])
    c = sub.add_parser("grade")
    c.add_argument("--answers", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--llm", default="http://127.0.0.1:8081")
    c.add_argument("--questions-en", type=Path, default=Path("data/qa/questions_en.csv"))
    x = ap.parse_args()
    if x.cmd == "make-mt":
        make_mt(x.questions, x.out)
    elif x.cmd == "answer":
        answer(x.questions, x.out, x.shard, x.n_shards, x.llm, x.cache, x.kb)
    else:
        grade(x.answers, x.out, x.llm, x.questions_en)


if __name__ == "__main__":
    main()
