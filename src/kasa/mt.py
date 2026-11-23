"""Translation models behind one interface: translate(texts, src, tgt) -> list of strings.

Language keys are twi, ewe, gaa, hau and en. Each model says which directions it supports.
"""

from __future__ import annotations

import time

import torch

NLLB = {"en": "eng_Latn", "twi": "twi_Latn", "ewe": "ewe_Latn", "hau": "hau_Latn"}
OPUS = {
    ("en", "twi"): "Helsinki-NLP/opus-mt-en-tw",
    ("en", "ewe"): "Helsinki-NLP/opus-mt-en-ee",
    ("ewe", "en"): "Helsinki-NLP/opus-mt-ee-en",
    ("en", "hau"): "Helsinki-NLP/opus-mt-en-ha",
    ("hau", "en"): "Helsinki-NLP/opus-mt-ha-en",
    ("en", "gaa"): "Helsinki-NLP/opus-mt-en-gaa",
    ("gaa", "en"): "Helsinki-NLP/opus-mt-gaa-en",
}
# MADLAD-400 target tags; checked against the tokenizer at load time, unsupported ones are dropped
MADLAD = {"en": "en", "twi": "ak", "ewe": "ee", "hau": "ha", "gaa": "gaa"}
SPECS = {
    "nllb_600m": "facebook/nllb-200-distilled-600M",
    "nllb_1.3b": "facebook/nllb-200-distilled-1.3B",
    "opus_mt": "Helsinki-NLP (one model per direction)",
    "madlad_3b": "google/madlad400-3b-mt",
    "glossmt_nllb_1.3b": "ghanaopenai/gloss-mt-nllb-1.3b",
}

torch.set_num_threads(4)


def _batches(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


class Model:
    name = ""

    def supports(self, src: str, tgt: str) -> bool:
        raise NotImplementedError

    def translate(self, texts: list[str], src: str, tgt: str) -> list[str]:
        raise NotImplementedError


class NLLB_(Model):
    def __init__(self, name: str, hub_id: str, beams: int = 4, codes: dict | None = None, only: set | None = None, tokenizer_id: str | None = None):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.name, self.beams, self.codes, self.only = name, beams, codes or NLLB, only
        self.tok = AutoTokenizer.from_pretrained(tokenizer_id or hub_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(hub_id).eval()

    def supports(self, src, tgt):
        if self.only is not None:
            return (src, tgt) in self.only
        return src in self.codes and tgt in self.codes and src != tgt

    def translate(self, texts, src, tgt):
        out = []
        self.tok.src_lang = self.codes[src]
        bos = self.tok.convert_tokens_to_ids(self.codes[tgt])
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        res = [None] * len(texts)
        for idx in _batches(order, 16):
            enc = self.tok([texts[i] for i in idx], return_tensors="pt", padding=True, truncation=True, max_length=256)
            with torch.inference_mode():
                gen = self.model.generate(**enc, forced_bos_token_id=bos, num_beams=self.beams, max_new_tokens=256)
            for i, t in zip(idx, self.tok.batch_decode(gen, skip_special_tokens=True), strict=True):
                res[i] = t
        out.extend(res)
        return out


class Opus(Model):
    name = "opus_mt"

    def __init__(self, beams: int = 4):
        self.beams = beams
        self._loaded = {}

    def supports(self, src, tgt):
        return (src, tgt) in OPUS

    def _get(self, pair):
        if pair not in self._loaded:
            from transformers import MarianMTModel, MarianTokenizer

            hub = OPUS[pair]
            self._loaded = {pair: (MarianTokenizer.from_pretrained(hub), MarianMTModel.from_pretrained(hub).eval())}
        return self._loaded[pair]

    def translate(self, texts, src, tgt):
        tok, model = self._get((src, tgt))
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        res = [None] * len(texts)
        for idx in _batches(order, 16):
            enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True, truncation=True, max_length=256)
            with torch.inference_mode():
                gen = model.generate(**enc, num_beams=self.beams, max_new_tokens=256)
            for i, t in zip(idx, tok.batch_decode(gen, skip_special_tokens=True), strict=True):
                res[i] = t
        return res


class Madlad(Model):
    name = "madlad_3b"

    def __init__(self, beams: int = 2):
        from transformers import AutoTokenizer, T5ForConditionalGeneration

        self.beams = beams
        self.tok = AutoTokenizer.from_pretrained(SPECS["madlad_3b"])
        self.model = T5ForConditionalGeneration.from_pretrained(SPECS["madlad_3b"], torch_dtype=torch.float32).eval()
        vocab = self.tok.get_vocab()
        self.codes = {k: v for k, v in MADLAD.items() if f"<2{v}>" in vocab}

    def supports(self, src, tgt):
        return tgt in self.codes and src != tgt and (src == "en" or src in self.codes)

    def translate(self, texts, src, tgt):
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        res = [None] * len(texts)
        for idx in _batches(order, 8):
            enc = self.tok([f"<2{self.codes[tgt]}> {texts[i]}" for i in idx], return_tensors="pt", padding=True, truncation=True, max_length=256)
            with torch.inference_mode():
                gen = self.model.generate(**enc, num_beams=self.beams, max_new_tokens=256)
            for i, t in zip(idx, self.tok.batch_decode(gen, skip_special_tokens=True), strict=True):
                res[i] = t
        return res


def load(name: str) -> Model:
    if name in ("nllb_600m", "nllb_1.3b"):
        return NLLB_(name, SPECS[name])
    if name == "glossmt_nllb_1.3b":
        # fine-tuned on English to Twi only
        return NLLB_(name, SPECS[name], codes={"en": "eng_Latn", "twi": "twi_Latn"}, only={("en", "twi")}, tokenizer_id=SPECS["nllb_1.3b"])
        # its saved tokenizer config needs transformers 5; the vocabulary is the base model's
    if name == "opus_mt":
        return Opus()
    if name == "madlad_3b":
        return Madlad()
    raise ValueError(name)


def timed(model: Model, texts, src, tgt):
    t0 = time.time()
    out = model.translate(texts, src, tgt)
    return out, time.time() - t0
