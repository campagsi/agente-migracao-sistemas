from time import time
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

import agent  # seu agent.py

app = FastAPI(
    title="Agente Certidão PBH",
    description="Servidor OpenAI-compatible para o agente RAG (LangChain + LangGraph).",
)

# estado global simples, igual ao main do agent
rag_history: list[tuple[str, str]] = []
lc_agent = agent.build_agent(rag_history)  # ou build_graph_agent, se esse for o nome aí


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]


@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    user_msg = req.messages[-1].content

    print("[Agente] Consultando LLM...")
    resultado = lc_agent.invoke({"input": user_msg})
    print("[Agente] LLM respondeu.")

    # Extrair a resposta de forma segura
    if isinstance(resultado, dict):
        if "output" in resultado:
            answer = resultado["output"]
        elif "answer" in resultado:
            answer = resultado["answer"]
        elif "result" in resultado:
            answer = resultado["result"]
        else:
            answer = str(resultado)
    else:
        answer = str(resultado)

    # Atualiza histórico usado pelo seu agente (se fizer sentido)
    rag_history.append((user_msg, answer))

    # Monta resposta no formato OpenAI
    now = int(time())
    payload = {
        "id": f"chatcmpl-local-{now}",
        "object": "chat.completion",
        "created": now,
        "model": req.model or "local-agent",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }

    print("DEBUG payload enviado para o Continue:", payload)
    return payload


if __name__ == "__main__":
    # aqui é onde o servidor realmente sobe
    uvicorn.run(app, host="127.0.0.1", port=8001)
