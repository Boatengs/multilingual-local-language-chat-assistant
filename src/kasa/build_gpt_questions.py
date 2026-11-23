import csv, re
from pathlib import Path
raw = Path("data/qa/raw/chatgpt_2026-11-23.txt").read_text(encoding="utf-8").strip().splitlines()[1:]
en = {r["id"]: r for r in csv.DictReader(open("data/qa/questions_en.csv", encoding="utf-8"))}
out, bad = [], []
for line in raw:
    f = line.split("\t")
    qid = f[0]
    parts = f[1:]
    if len(parts) < 4:
        parts = parts[:-1] + re.split(r"(?<=\?) (?=\S)", parts[-1])
    if len(parts) != 4:
        bad.append((qid, len(parts))); continue
    for lang, q in zip(["twi", "gaa", "ewe", "hau"], parts):
        e = en[qid]
        out.append({"id": qid, "topic": e["topic"], "lang": lang, "question": q.strip(), "answer": e["answer"], "source": "chatgpt"})
print("bad", bad, "rows", len(out), "ids", len({r['id'] for r in out}))
with open("data/qa/questions_gpt.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
