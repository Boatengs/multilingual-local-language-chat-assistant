"""Build the translation test sets.

flores      FLORES-200 devtest (CC BY-SA 4.0): 1,012 sentences, professionally translated from English.
            Twi, Ewe and Hausa. There is no Ga.
ghananlp    GhanaNLP's English parallel text (professional translation, CC BY 4.0 link on the card),
            500 random pairs per language (seed 42). Ga, Ewe and Twi. Ga and Ewe were translated from
            English; the Twi pairs come from two files, one translated each way, and keep that direction.
twi_terms   The test split of ghanaopenai/gloss-mt-parallel-en-twi (CC BY-NC 4.0): English to Twi
            chunks with the Twi terms the human reference uses for key noun phrases.
"""

from __future__ import annotations

import argparse
import io
import json
import random
import tarfile
import urllib.request
from pathlib import Path

import pandas as pd

FLORES_URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
GHANANLP = {
    "gaa": [("Ghana-NLP/GA_ENGLISH_PARALLEL_TEXT", "Public- GA_70.csv", "en")],
    "ewe": [("Ghana-NLP/EWE_ENGLISH_PARALLEL_TEXT", "Public - Ewe_70.csv", "en")],
    "twi": [
        ("Ghana-NLP/ENGLISH_TWI_PARALLEL_TEXT", "Public - Twi[En-Twi]_70.csv", "en"),
        ("Ghana-NLP/TWI_ENGLISH_PARALLEL_TEXT", "Public - Twi[Twi-En]_70.csv", "local"),
    ],
}
FLORES_CODES = {"twi": "twi_Latn", "ewe": "ewe_Latn", "hau": "hau_Latn"}
COLUMNS = ["id", "set", "lang", "en", "local", "source_side", "domain"]


def flores(n: int | None = None) -> pd.DataFrame:
    raw = urllib.request.urlopen(FLORES_URL, timeout=600).read()
    tar = tarfile.open(fileobj=io.BytesIO(raw))

    names = tar.getnames()

    def read(code):
        name = next(m for m in names if m.endswith(f"devtest/{code}.devtest"))
        return tar.extractfile(name).read().decode().splitlines()

    meta_name = next((m for m in names if m.endswith("metadata_devtest.tsv")), None)
    topics: list[str] = []
    if meta_name:
        meta = tar.extractfile(meta_name).read().decode().splitlines()
        header = meta[0].split("\t")
        topics = [dict(zip(header, m.split("\t"), strict=False)).get("topic", "") for m in meta[1:]]
    en = read("eng_Latn")
    rows = []
    for lang, code in FLORES_CODES.items():
        loc = read(code)
        assert len(loc) == len(en)
        for i, (e, t) in enumerate(zip(en, loc, strict=True)):
            rows.append(
                {
                    "id": f"flores_{lang}_{i}",
                    "set": "flores",
                    "lang": lang,
                    "en": e.strip(),
                    "local": t.strip(),
                    "source_side": "en",
                    "domain": topics[i] if i < len(topics) else "",
                }
            )
    return pd.DataFrame(rows, columns=COLUMNS)


def ghananlp(n_per_lang: int = 500, seed: int = 42) -> pd.DataFrame:
    from huggingface_hub import hf_hub_download

    rows = []
    for lang, files in GHANANLP.items():
        pool = []
        for repo, fname, original in files:
            df = pd.read_csv(hf_hub_download(repo, fname, repo_type="dataset"))
            df = df.dropna(subset=["text", "label"])
            for r in df.itertuples():
                en, loc = (r.text, r.label) if original == "en" else (r.label, r.text)
                pool.append(
                    {
                        "id": f"ghananlp_{lang}_{r.id}",
                        "set": "ghananlp",
                        "lang": lang,
                        "en": str(en).strip(),
                        "local": str(loc).strip(),
                        "source_side": original,
                        "domain": "",
                    }
                )
        # drop exact duplicate pairs and very short lines
        seen, uniq = set(), []
        for p in pool:
            key = (p["en"].lower(), p["local"].lower())
            if key in seen or len(p["en"].split()) < 3:
                continue
            seen.add(key)
            uniq.append(p)
        rng = random.Random(seed)
        uniq.sort(key=lambda p: p["id"])
        rows += rng.sample(uniq, min(n_per_lang, len(uniq)))
    return pd.DataFrame(rows, columns=COLUMNS)


def twi_terms() -> pd.DataFrame:
    from huggingface_hub import hf_hub_download

    df = pd.read_parquet(hf_hub_download("ghanaopenai/gloss-mt-parallel-en-twi", "data/test-00000-of-00001.parquet", repo_type="dataset"))
    out = pd.DataFrame(
        {
            "id": [f"twiterms_{i}_{c}" for i, c in zip(df["id"], df["chunk_index"], strict=True)],
            "set": "twi_terms",
            "lang": "twi",
            "en": df["english"].str.replace(r"^#+\s*", "", regex=True),
            "local": df["twi"].str.replace(r"^#+\s*", "", regex=True),
            "source_side": "en",
            "domain": df["source"],
            "gold_terms": [json.dumps(list(g), ensure_ascii=False, default=str) for g in df["gold_terms"]],
            "glossary": [json.dumps(list(g), ensure_ascii=False, default=str) for g in df["glossary"]],
        }
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/mt"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    stats = {}
    for name, fn in [("flores", flores), ("ghananlp", ghananlp), ("twi_terms", twi_terms)]:
        df = fn()
        df.to_parquet(a.out / f"{name}.parquet", index=False)
        stats[name] = df.groupby("lang").size().to_dict()
        stats[name + "_source_side"] = {f"{k[0]}/{k[1]}": int(v) for k, v in df.groupby(["lang", "source_side"]).size().items()}
    (a.out / "stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
