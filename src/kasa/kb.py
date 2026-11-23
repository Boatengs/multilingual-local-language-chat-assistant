"""A small knowledge base of Ghanaian pages, fetched once and cut into passages.

data/kb/sources.csv lists each page. question_source=yes marks the pages the 20 test questions were
written from: the benchmark runs with and without them, so that the gain from adding pages that hold
the test answers is not counted as the assistant getting smarter.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .wiki import USER_AGENT, Passage, html_to_passages

ROOT = Path(__file__).resolve().parents[2]


def page_passages(url: str, html: str) -> list[Passage]:
    soup = BeautifulSoup(html, "lxml")
    for bad in soup.find_all(["nav", "header", "footer", "script", "style", "form", "aside", "noscript"]):
        bad.decompose()
    title = (soup.title.get_text(" ", strip=True) if soup.title else url)[:120]
    main = soup.find("main") or soup.find("article") or soup.body or soup
    wrapper = f'<div class="mw-parser-output">{main.decode_contents()}</div>'
    ps = html_to_passages(title, wrapper, 0)
    if not ps:
        # pages built from bare divs: fall back to the text lines, in chunks of about 120 words
        lines = [re.sub(r"\s+", " ", x).strip() for x in main.get_text("\n").split("\n")]
        lines = [x for x in lines if len(x.split()) >= 4]
        buf: list[str] = []
        for x in lines:
            buf.append(x)
            if sum(len(b.split()) for b in buf) >= 120:
                ps.append(Passage(title, "", "\n".join(buf), 0))
                buf = []
        if buf:
            ps.append(Passage(title, "", "\n".join(buf), 0))
    for p in ps:
        p.source_url = url
    return ps


def build(out: Path, sources: Path) -> None:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    rows, log = [], []
    for src in csv.DictReader(sources.open()):
        try:
            r = s.get(src["url"], timeout=60)
            r.raise_for_status()
            ps = page_passages(src["url"], r.text)
            for p in ps:
                rows.append(
                    {
                        "title": p.title,
                        "section": p.section,
                        "text": p.text,
                        "url": src["url"],
                        "topic": src["topic"],
                        "question_source": src["question_source"],
                    }
                )
            log.append({"url": src["url"], "status": r.status_code, "passages": len(ps)})
        except Exception as e:
            log.append({"url": src["url"], "error": f"{type(e).__name__}: {e}"[:200]})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    (out.parent / "build_log.json").write_text(json.dumps({"fetched_on": date.today().isoformat(), "pages": log}, indent=1))
    print(json.dumps(log, indent=1))


class KB:
    def __init__(self, path: Path = ROOT / "data" / "kb" / "passages.jsonl", include_question_sources: bool = False):
        self.items = []
        if path.exists():
            for line in path.read_text().splitlines():
                x = json.loads(line)
                if x["question_source"] == "yes" and not include_question_sources:
                    continue
                if len(re.findall(r"\w+", x["text"])) < 5:
                    continue
                self.items.append(Passage(x["title"], x["section"], x["text"], 0, x["url"]))
        self._vecs = None

    def vectors(self, encode):
        if self._vecs is None and self.items:
            self._vecs = encode([p.render() for p in self.items], batch_size=64)
        return self._vecs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path, default=Path("data/kb/sources.csv"))
    ap.add_argument("--out", type=Path, default=Path("data/kb/passages.jsonl"))
    a = ap.parse_args()
    build(a.out, a.sources)


if __name__ == "__main__":
    main()
