"""Web app: ask in Twi, Ga, Ewe, Hausa or English, get the answer in the language you pick.

Run a local model server first (Ollama: `ollama pull llama3.2`, or llama-server on port 8080), then
    uvicorn app:app --app-dir src --port 8000
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from kasa.assistant import LANG_NAMES, Assistant
from kasa.kb import KB
from kasa.llm import LlamaServer
from kasa.wiki import Wikipedia

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="Local language assistant")
_bot: Assistant | None = None


def bot() -> Assistant:
    global _bot
    if _bot is None:
        llm = LlamaServer(os.environ.get("KASA_LLM_URL", "http://127.0.0.1:11434"), model=os.environ.get("KASA_MODEL", "llama3.2"))
        wiki = Wikipedia(cache_dir=Path(os.environ.get("KASA_CACHE", Path.home() / ".cache" / "kasa")))
        _bot = Assistant(llm, wiki, kb=KB())
    return _bot


class Ask(BaseModel):
    message: str
    lang: str = "en"
    reply_lang: str = "en"


@app.post("/chat")
def chat(req: Ask):
    if req.lang not in LANG_NAMES or req.reply_lang not in LANG_NAMES:
        return {"status": "error", "reply": "Unknown language."}
    try:
        r = bot().ask(req.message.strip()[:600], req.lang, req.reply_lang)
    except Exception as e:
        return {"status": "error", "reply": f"Something went wrong: {type(e).__name__}"}
    sources = [{"n": s["n"], "title": s["title"], "section": s["section"], "url": s["url"]} for s in r["sources"] if s["n"] in r["cited"]]
    return {"status": "ok", "reply": r["reply"], "question_en": r["question_en"], "answer_en": r["answer_en"], "sources": sources, "seconds": r["seconds"]}


@app.get("/languages")
def languages():
    return LANG_NAMES


@app.get("/")
def root():
    return FileResponse(STATIC / "index.html")
