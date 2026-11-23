import json
from pathlib import Path
from huggingface_hub import HfApi
api = HfApi(); out = {}
for org in ["ghanaopenai", "GhanaNLP", "ghananlpcommunity", "Ghana-NLP"]:
    try:
        out[org] = [(m.id, m.pipeline_tag, m.downloads, str(m.last_modified)[:10]) for m in api.list_models(author=org, limit=500, full=False, sort="downloads")]
    except Exception as e:
        out[org] = f"error {e}"
cands = ["Helsinki-NLP/opus-mt-en-tw", "Helsinki-NLP/opus-mt-tw-en", "Helsinki-NLP/opus-mt-en-ee", "Helsinki-NLP/opus-mt-ee-en", "Helsinki-NLP/opus-mt-en-ha", "Helsinki-NLP/opus-mt-ha-en",
         "Helsinki-NLP/opus-mt-en-gaa", "Helsinki-NLP/opus-mt-gaa-en", "facebook/nllb-200-distilled-600M", "facebook/nllb-200-distilled-1.3B", "facebook/nllb-200-3.3B",
         "google/translategemma-4b-it", "google/translategemma-12b-it", "CohereLabs/aya-expanse-8b", "google/madlad400-3b-mt"]
out["candidates"] = {}
for c in cands:
    try:
        i = api.model_info(c)
        out["candidates"][c] = {"ok": True, "gated": i.gated, "license": (i.card_data or {}).get("license") if i.card_data else None, "downloads": i.downloads}
    except Exception as e:
        out["candidates"][c] = {"ok": False, "err": str(e)[:200]}
for q in ["translategemma", "twi ewe ga translation", "gaa"]:
    try:
        out[f"search:{q}"] = [(m.id, m.downloads) for m in api.list_models(search=q, limit=30, sort="downloads")]
    except Exception as e:
        out[f"search:{q}"] = str(e)
Path("probe/out/models.json").write_text(json.dumps(out, indent=1, default=str))
