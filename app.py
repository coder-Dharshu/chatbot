import json
import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ENV_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("Groq_Api") or os.getenv("GROQ_API")
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

app = FastAPI(title="Groq AI Chatbot", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_groq_client(custom_key: Optional[str] = None) -> Groq:
    effective_key = (custom_key or "").strip() or ENV_API_KEY
    if not effective_key:
        raise HTTPException(
            status_code=401,
            detail="Missing Groq API Key. Please provide your Groq API key in the 'Rules & Model' settings in the UI."
        )
    return Groq(api_key=effective_key)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 800
    stream: Optional[bool] = True
    system_prompt: Optional[str] = None
    api_key: Optional[str] = None

@app.get("/api/models")
def get_models(api_key: Optional[str] = None):
    """Returns available Groq chat models and the active default."""
    try:
        client = get_groq_client(api_key)
        remote_models = client.models.list()
        chat_models = [
            m.id for m in remote_models.data 
            if "whisper" not in m.id and "prompt-guard" not in m.id and "safeguard" not in m.id
        ]
        # Prioritize qwen/qwen3.8-27b as first choice for performance & reliability
        if "qwen/qwen3.8-27b" in chat_models:
            chat_models.remove("qwen/qwen3.8-27b")
            chat_models.insert(0, "qwen/qwen3.8-27b")
        if not chat_models:
            chat_models = [DEFAULT_MODEL]
        return {
            "current": DEFAULT_MODEL,
            "models": chat_models,
            "has_key": True
        }
    except Exception as e:
        return {
            "current": DEFAULT_MODEL,
            "models": ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"],
            "warning": str(e),
            "has_key": bool(ENV_API_KEY or (api_key and api_key.strip()))
        }

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Processes chat completions with streaming SSE or full JSON."""
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")

    client = get_groq_client(req.api_key)
    selected_model = req.model or DEFAULT_MODEL
    messages_payload = []

    if req.system_prompt:
        messages_payload.append({"role": "system", "content": req.system_prompt})
    elif not any(m.role == "system" for m in req.messages):
        default_sys = (
            "You are CodeDoctor, an elite code review and debugging assistant.\n\n"
            "CORE RULES:\n"
            "1. STRICT DOMAIN BOUNDARY: You ONLY answer programming, code review, debugging, and software architecture queries. "
            "If the user asks about anything else (recipes, casual talk, poetry, general trivia), you MUST decline with: "
            "'I am CodeDoctor, specialized strictly in code diagnostics, debugging, and software review. Please provide a code snippet or programming question.'\n"
            "2. NO CHIT-CHAT: Do not begin with conversational pleasantries ('Sure!', 'Hello!', 'I would be happy to help'). Start immediately with the diagnosis.\n"
            "3. MANDATORY 4-PART FORMAT for code reviews:\n"
            "   - 🔍 **Diagnosis**: Root cause and bug explanation.\n"
            "   - ⚠️ **Severity**: [Critical | High | Medium | Low]\n"
            "   - 🛠️ **Fixed Code**: Complete, corrected code snippet with syntax highlighting.\n"
            "   - 💡 **Optimization & Complexity**: Big-O time/space impact and best practices."
        )
        messages_payload.append({"role": "system", "content": default_sys})

    for m in req.messages:
        messages_payload.append({"role": m.role, "content": m.content})

    temperature = max(0.0, min(2.0, float(req.temperature if req.temperature is not None else 0.2)))
    max_tokens = max(100, min(1000, int(req.max_tokens if req.max_tokens is not None else 800)))

    if req.stream:
        def sse_generator():
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages_payload,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                for chunk in response:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield f"data: {json.dumps({'content': delta})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as err:
                yield f"data: {json.dumps({'error': str(err)})}\n\n"

        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        try:
            res = client.chat.completions.create(
                model=selected_model,
                messages=messages_payload,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return {
                "role": "assistant",
                "content": res.choices[0].message.content,
                "model": selected_model
            }
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Groq API Error: {str(e)}")


@app.get("/")
def index():
    for candidate in [BASE_DIR / "index.html", BASE_DIR / "static" / "index.html"]:
        if candidate.exists():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="index.html not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
