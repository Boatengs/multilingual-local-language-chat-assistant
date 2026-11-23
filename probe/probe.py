"""Look at candidate datasets: card, licence, columns and a few rows, saved as text for review."""
import json, sys, traceback
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

OUT = Path("probe/out"); OUT.mkdir(parents=True, exist_ok=True)
DATASETS = [
    "Ghana-NLP/GA_ENGLISH_PARALLEL_TEXT", "Ghana-NLP/EWE_ENGLISH_PARALLEL_TEXT", "Ghana-NLP/TWI_ENGLISH_PARALLEL_TEXT",
    "Ghana-NLP/ENGLISH_TWI_PARALLEL_TEXT", "adwumatech-ai/mghana-st", "ghanaopenai/twi-translation-glossary-chunks",
    "ghanaopenai/gloss-mt-parallel-en-twi", "ghananlpcommunity/ghana-qa", "openlanguagedata/flores_plus",
]
api = HfApi()
for repo in DATASETS:
    name = repo.replace("/", "__")
    rep = {"repo": repo}
    try:
        info = api.dataset_info(repo, files_metadata=True)
        rep["gated"] = info.gated
        rep["card_data"] = info.card_data.to_dict() if info.card_data else None
        rep["files"] = [(s.rfilename, s.size) for s in info.siblings][:200]
        try:
            rep["readme"] = Path(hf_hub_download(repo, "README.md", repo_type="dataset")).read_text()[:12000]
        except Exception as e:
            rep["readme"] = f"no README: {e}"
        try:
            from datasets import load_dataset, get_dataset_config_names
            cfgs = get_dataset_config_names(repo)
            rep["configs"] = cfgs[:60]
            samples = {}
            for c in cfgs[:4]:
                ds = load_dataset(repo, c, streaming=True)
                for split in ds:
                    rows = []
                    for i, r in enumerate(ds[split]):
                        rows.append({k: (v if isinstance(v, (str, int, float)) or v is None else str(type(v))) for k, v in r.items()})
                        if i >= 4: break
                    samples[f"{c}/{split}"] = rows
            rep["samples"] = samples
        except Exception as e:
            rep["load_error"] = f"{type(e).__name__}: {e}"[:1500]
    except Exception as e:
        rep["error"] = f"{type(e).__name__}: {e}"[:1500]
    (OUT / f"{name}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    print(repo, "ok" if "error" not in rep else rep["error"][:200], flush=True)
