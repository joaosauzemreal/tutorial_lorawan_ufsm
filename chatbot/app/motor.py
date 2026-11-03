"""Monta a conversa (pergunta + trechos encontrados) e conversa com o modelo no Ollama."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from . import config
from .prompts import SYSTEM_PROMPT, montar_pergunta
from .rag import Indice


async def preparar_conversa(
    cliente: httpx.AsyncClient, indice: Indice, historico: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Recebe o histórico [{role, content}, ...] terminando com a pergunta do usuário.

    Devolve as mensagens para o Ollama e a lista de fontes usadas.
    """
    perguntas = [m["content"] for m in historico if m["role"] == "user"]
    pergunta = perguntas[-1]
    # Para perguntas de continuação ("e como faço isso?"), a pergunta anterior ajuda a busca.
    consulta = "\n".join(perguntas[-2:])

    resultados = await indice.buscar(cliente, consulta, config.TOP_K)
    trechos = [t.texto for t, _ in resultados]

    fontes, vistos = [], set()
    for t, _ in resultados:
        chave = (t.arquivo, t.titulo)
        if chave in vistos:
            continue
        vistos.add(chave)
        caminho = config.LINKS_FONTES.get(t.arquivo)
        fontes.append({
            "arquivo": t.arquivo,
            "titulo": t.secao,
            "url": config.FONTES_URL_BASE + caminho if caminho else None,
        })

    anteriores = historico[:-1][-config.MAX_HISTORICO:]
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensagens += [{"role": m["role"], "content": m["content"]} for m in anteriores]
    mensagens.append({"role": "user", "content": montar_pergunta(pergunta, trechos)})
    return mensagens, fontes


def _corpo(modelo: str, mensagens: list[dict], stream: bool) -> dict:
    return {
        "model": modelo,
        "messages": mensagens,
        "stream": stream,
        "keep_alive": config.KEEP_ALIVE,
        "options": {"temperature": config.TEMPERATURE, "num_ctx": config.NUM_CTX},
    }


async def gerar_resposta_stream(
    cliente: httpx.AsyncClient, modelo: str, mensagens: list[dict]
) -> AsyncIterator[str]:
    async with cliente.stream("POST", "/api/chat", json=_corpo(modelo, mensagens, True), timeout=None) as r:
        if r.status_code != 200:
            detalhe = (await r.aread()).decode(errors="replace")
            raise RuntimeError(f"Ollama respondeu {r.status_code}: {detalhe}")
        async for linha in r.aiter_lines():
            if not linha.strip():
                continue
            dado = json.loads(linha)
            if dado.get("error"):
                raise RuntimeError(dado["error"])
            pedaco = dado.get("message", {}).get("content", "")
            if pedaco:
                yield pedaco
            if dado.get("done"):
                break


async def gerar_resposta(cliente: httpx.AsyncClient, modelo: str, mensagens: list[dict]) -> str:
    partes = [p async for p in gerar_resposta_stream(cliente, modelo, mensagens)]
    return "".join(partes)
