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
from .motor import deve_recusar, gerar_resposta_stream, preparar_conversa
from .prompts import RECUSA

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("assistente")

PASTA_STATIC = Path(__file__).parent / "static"

estado: dict = {"situacao": "iniciando", "erro": None, "indice": None, "modelos_teste_prontos": []}
cliente: httpx.AsyncClient | None = None


async def preparar() -> None:
    try:
        await rag.esperar_ollama(cliente)
        estado["situacao"] = "baixando modelos"
        await rag.garantir_modelo(cliente, config.EMBED_MODEL)
        await rag.garantir_modelo(cliente, config.CHAT_MODEL)
        estado["situacao"] = "indexando documentos"
        estado["indice"] = await rag.construir_indice(
            cliente, config.DOCS_PATHS, config.EMBED_MODEL, config.CACHE_DIR,
            rag.ler_exemplos(config.EXEMPLOS_FORA),
        )
        estado["situacao"] = "pronto"
        log.info("Assistente pronto (modelo %s).", config.CHAT_MODEL)
    except Exception as e:  # noqa: BLE001
        log.exception("Falha ao preparar o assistente")
        estado["situacao"] = "erro"
        estado["erro"] = str(e)
        return
    # Modelos extras, só para comparação (MODELOS_TESTE): baixados depois que o chat já está no ar.
    for modelo in config.MODELOS_TESTE:
        try:
            await rag.garantir_modelo(cliente, modelo)
            estado["modelos_teste_prontos"].append(modelo)
        except Exception:  # noqa: BLE001
            log.exception("Não consegui baixar o modelo de teste %s", modelo)


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
    # Só para testes: escolher outro modelo da lista MODELOS_TESTE e ligar/desligar o raciocínio.
    modelo: str | None = None
    think: bool | None = None


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
        "modelos_teste": config.MODELOS_TESTE,
        "modelos_teste_prontos": estado["modelos_teste_prontos"],
    }


@app.post("/api/chat")
async def chat(pedido: PedidoChat):
    if estado["situacao"] != "pronto":
        raise HTTPException(503, f"O assistente ainda está se preparando ({estado['situacao']}).")
    modelo = config.CHAT_MODEL
    if pedido.modelo and pedido.modelo != config.CHAT_MODEL:
        if pedido.modelo not in config.MODELOS_TESTE:
            raise HTTPException(400, "Modelo não permitido. Os modelos de teste ficam em MODELOS_TESTE no .env.")
        if pedido.modelo not in estado["modelos_teste_prontos"]:
            raise HTTPException(503, f"O modelo {pedido.modelo} ainda está sendo baixado.")
        modelo = pedido.modelo
    historico = [{"role": m.role, "content": m.content} for m in pedido.messages]
    if historico[-1]["role"] != "user":
        raise HTTPException(400, "A última mensagem precisa ser do usuário.")

    try:
        mensagens, fontes, similaridade_fora = await preparar_conversa(cliente, estado["indice"], historico)
    except Exception as e:  # noqa: BLE001
        log.exception("Erro ao buscar nos documentos")
        raise HTTPException(502, f"Não consegui consultar o modelo de IA no servidor ({e.__class__.__name__}).") from e

    if deve_recusar(fontes, similaridade_fora):
        async def recusa():
            yield json.dumps({"tipo": "fontes", "fontes": []}) + "\n"
            yield json.dumps({"tipo": "texto", "texto": RECUSA}, ensure_ascii=False) + "\n"
            yield json.dumps({"tipo": "fim"}) + "\n"
        return StreamingResponse(recusa(), media_type="application/x-ndjson")

    async def eventos():
        yield json.dumps({"tipo": "fontes", "fontes": fontes}, ensure_ascii=False) + "\n"
        try:
            async for pedaco in gerar_resposta_stream(cliente, modelo, mensagens, pedido.think):
                yield json.dumps({"tipo": "texto", "texto": pedaco}, ensure_ascii=False) + "\n"
            yield json.dumps({"tipo": "fim"}) + "\n"
        except Exception as e:  # noqa: BLE001
            log.exception("Erro ao gerar resposta")
            yield json.dumps({"tipo": "erro", "erro": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(eventos(), media_type="application/x-ndjson")
