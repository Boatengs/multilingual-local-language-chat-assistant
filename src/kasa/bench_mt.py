"""Translate every test set in both directions with one model, one shard at a time.

python -m kasa.bench_mt run --model nllb_600m --data data/mt --out preds --shard 0 --n-shards 4
python -m kasa.bench_mt report --data data/mt --preds preds --out results/mt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import LANGS

SETS = ["flores", "ghananlp"]  # twi_terms chunks are long transcripts; scored separately for terms


def load_sets(data: Path) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(data / f"{s}.parquet") for s in SETS if (data / f"{s}.parquet").exists()], ignore_index=True)


def jobs(df: pd.DataFrame):
    for (st, lang), g in df.groupby(["set", "lang"], sort=True):
        yield st, lang, "en", lang, g
        if st != "twi_terms":
            yield st, lang, lang, "en", g


def run(model_name: str, data: Path, out: Path, shard: int, n_shards: int) -> None:
    from .mt import load, timed

    df = load_sets(data)
    model = load(model_name)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{model_name}.part{shard}of{n_shards}.parquet"
    done = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    rows = [done] if len(done) else []
    for st, lang, src, tgt, g in jobs(df):
        if not model.supports(src, tgt):
            continue
        g = g.iloc[shard::n_shards]
        key = f"{st}|{src}>{tgt}"
        if len(done) and ((done["set"] == st) & (done["direction"] == f"{src}>{tgt}") & (done["lang"] == lang)).any():
            continue
        texts = g["en" if src == "en" else "local"].tolist()
        hyp, secs = timed(model, texts, src, tgt)
        part = pd.DataFrame(
            {
                "id": g["id"].values,
                "set": st,
                "lang": lang,
                "direction": f"{src}>{tgt}",
                "model": model_name,
                "hyp": hyp,
                "seconds_total": secs,
                "n": len(texts),
            }
        )
        rows.append(part)
        pd.concat(rows, ignore_index=True).to_parquet(path, index=False)
        print(f"{key} {lang} {len(texts)} sentences {secs:.0f}s", flush=True)
    if not rows:
        pd.DataFrame(columns=["id", "set", "lang", "direction", "model", "hyp", "seconds_total", "n"]).to_parquet(path, index=False)


def chrf(hyps, refs) -> float:
    from sacrebleu.metrics import CHRF

    return CHRF(word_order=2).corpus_score(hyps, [refs]).score


def bleu(hyps, refs) -> float:
    from sacrebleu.metrics import BLEU

    return BLEU().corpus_score(hyps, [refs]).score


def bootstrap_chrf(hyps, refs, n=1000, seed=42):
    """Resample sentences; chrF++ is recomputed from summed sentence statistics, which equals the corpus score."""
    from sacrebleu.metrics import CHRF

    c = CHRF(word_order=2)
    stats = np.array(c._extract_corpus_statistics(hyps, [refs]), dtype=float)
    rng = np.random.default_rng(seed)
    vals = [c._compute_score_from_stats(list(stats[rng.integers(0, len(stats), len(stats))].sum(0))).score for _ in range(n)]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def report(data: Path, preds: Path, out: Path, extra_preds: list[Path] | None = None) -> None:
    df = load_sets(data).set_index("id")
    parts = [pd.read_parquet(f) for f in sorted(preds.glob("*.parquet"))]
    for extra in extra_preds or []:
        parts.append(pd.read_parquet(extra))
    p = pd.concat(parts, ignore_index=True).drop_duplicates(["model", "id", "direction"], keep="last")
    rows = []
    for (model, st, lang, direction), g in p.groupby(["model", "set", "lang", "direction"]):
        ref_col = "local" if direction.startswith("en>") else "en"
        refs = df.loc[g["id"], ref_col].tolist()
        hyps = g["hyp"].fillna("").tolist()
        lo, hi = bootstrap_chrf(hyps, refs)
        secs = float(g.drop_duplicates(["seconds_total", "n"])["seconds_total"].sum())
        rows.append(
            {
                "model": model,
                "set": st,
                "lang": lang,
                "direction": direction,
                "n": len(g),
                "chrf": chrf(hyps, refs),
                "chrf_lo": lo,
                "chrf_hi": hi,
                "bleu": bleu(hyps, refs),
                "sec_per_sentence": secs / len(g),
            }
        )
    r = pd.DataFrame(rows).sort_values(["set", "lang", "direction", "chrf"], ascending=[True, True, True, False])
    out.mkdir(parents=True, exist_ok=True)
    r.to_csv(out / "scores.csv", index=False)
    p.to_parquet(out / "predictions.parquet", index=False)
    L = ["# Translation scores", "", "chrF++ (0 to 100, higher is better) with 95% bootstrap intervals, and BLEU.", ""]
    for (st, lang, direction), g in r.groupby(["set", "lang", "direction"], sort=True):
        L += [
            f"## {st}, {LANGS.get(lang, {}).get('name', lang)}, {direction}",
            "",
            "| Model | Sentences | chrF++ | BLEU | Seconds per sentence |",
            "|---|---|---|---|---|",
        ]
        for x in g.itertuples():
            L.append(f"| {x.model} | {x.n} | {x.chrf:.1f} ({x.chrf_lo:.1f} to {x.chrf_hi:.1f}) | {x.bleu:.1f} | {x.sec_per_sentence:.2f} |")
        L.append("")
    (out / "SCORES.md").write_text("\n".join(L))
    print("\n".join(L))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run")
    a.add_argument("--model", required=True)
    a.add_argument("--data", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--shard", type=int, default=0)
    a.add_argument("--n-shards", type=int, default=1)
    b = sub.add_parser("report")
    b.add_argument("--data", type=Path, required=True)
    b.add_argument("--preds", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--extra-preds", type=Path, nargs="*", default=[])
    x = ap.parse_args()
    if x.cmd == "run":
        run(x.model, x.data, x.out, x.shard, x.n_shards)
    else:
        report(x.data, x.preds, x.out, x.extra_preds)


if __name__ == "__main__":
    main()
