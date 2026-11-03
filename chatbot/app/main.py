"""Servidor web do Assistente LoRaWAN UFSM.

Rodar:  uvicorn app.main:app --host 0.0.0.0 --port 8000   (dentro da pasta chatbot/)
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import config, rag
from .motor import gerar_resposta_stream, preparar_conversa

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("assistente")

PASTA_STATIC = Path(__file__).parent / "static"

estado: dict = {"situacao": "iniciando", "erro": None, "indice": None}
cliente: httpx.AsyncClient | None = None


async def preparar() -> None:
    try:
        await rag.esperar_ollama(cliente)
        estado["situacao"] = "baixando modelos"
        await rag.garantir_modelo(cliente, config.EMBED_MODEL)
        await rag.garantir_modelo(cliente, config.CHAT_MODEL)
        estado["situacao"] = "indexando documentos"
        estado["indice"] = await rag.construir_indice(
            cliente, config.DOCS_PATHS, config.EMBED_MODEL, config.CACHE_DIR
        )
        estado["situacao"] = "pronto"
        log.info("Assistente pronto (modelo %s).", config.CHAT_MODEL)
    except Exception as e:  # noqa: BLE001
        log.exception("Falha ao preparar o assistente")
        estado["situacao"] = "erro"
        estado["erro"] = str(e)


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    global cliente
    cliente = httpx.AsyncClient(base_url=config.OLLAMA_URL, timeout=None)
    tarefa = asyncio.create_task(preparar())
    yield
    tarefa.cancel()
    await cliente.aclose()


app = FastAPI(title="Assistente LoRaWAN UFSM", lifespan=ciclo_de_vida, docs_url=None, redoc_url=None)


class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class PedidoChat(BaseModel):
    messages: list[Mensagem] = Field(min_length=1, max_length=40)


@app.get("/")
async def pagina():
    return FileResponse(PASTA_STATIC / "index.html")


@app.get("/api/status")
async def status():
    indice = estado["indice"]
    return {
        "situacao": estado["situacao"],
        "erro": estado["erro"],
        "modelo": config.CHAT_MODEL,
        "modelo_embeddings": config.EMBED_MODEL,
        "trechos": len(indice.trechos) if indice else 0,
    }


@app.post("/api/chat")
async def chat(pedido: PedidoChat):
    if estado["situacao"] != "pronto":
        raise HTTPException(503, f"O assistente ainda está se preparando ({estado['situacao']}).")
    historico = [m.model_dump() for m in pedido.messages]
    if historico[-1]["role"] != "user":
        raise HTTPException(400, "A última mensagem precisa ser do usuário.")

    try:
        mensagens, fontes = await preparar_conversa(cliente, estado["indice"], historico)
    except Exception as e:  # noqa: BLE001
        log.exception("Erro ao buscar nos documentos")
        raise HTTPException(502, f"Não consegui consultar o modelo de IA no servidor ({e.__class__.__name__}).") from e

    async def eventos():
        yield json.dumps({"tipo": "fontes", "fontes": fontes}, ensure_ascii=False) + "\n"
        try:
            async for pedaco in gerar_resposta_stream(cliente, config.CHAT_MODEL, mensagens):
                yield json.dumps({"tipo": "texto", "texto": pedaco}, ensure_ascii=False) + "\n"
            yield json.dumps({"tipo": "fim"}) + "\n"
        except Exception as e:  # noqa: BLE001
            log.exception("Erro ao gerar resposta")
            yield json.dumps({"tipo": "erro", "erro": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(eventos(), media_type="application/x-ndjson")
