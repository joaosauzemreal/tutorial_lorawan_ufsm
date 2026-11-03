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
) -> tuple[list[dict], list[dict], float]:
    """Recebe o histórico [{role, content}, ...] terminando com a pergunta do usuário.

    Devolve as mensagens para o Ollama, a lista de fontes usadas e a maior similaridade
    da pergunta com os exemplos fora do assunto.
    """
    perguntas = [m["content"] for m in historico if m["role"] == "user"]
    pergunta = perguntas[-1]
    # Para perguntas de continuação ("e como faço isso?"), a pergunta anterior ajuda a busca.
    consulta = "\n".join(perguntas[-2:])

    resultados, similaridade_fora = await indice.buscar(cliente, consulta, config.TOP_K)
    trechos = [t.texto for t, _ in resultados]

    fontes, vistos = [], set()
    for t, nota in resultados:
        chave = (t.arquivo, t.titulo)
        if chave in vistos:
            continue
        vistos.add(chave)
        caminho = config.LINKS_FONTES.get(t.arquivo)
        fontes.append({
            "arquivo": t.arquivo,
            "titulo": t.secao,
            "url": config.FONTES_URL_BASE + caminho if caminho else None,
            "similaridade": round(nota, 3),  # 0 a 1: quanto o trecho se parece com a pergunta
        })

    anteriores = historico[:-1][-config.MAX_HISTORICO:]
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensagens += [{"role": m["role"], "content": m["content"]} for m in anteriores]
    mensagens.append({"role": "user", "content": montar_pergunta(pergunta, trechos)})
    return mensagens, fontes, similaridade_fora


def deve_recusar(fontes: list[dict], similaridade_fora: float) -> bool:
    """Recusa quando a pergunta se parece mais com os exemplos fora do assunto do que com a documentação."""
    if not config.FILTRO_ASSUNTO:
        return False
    melhor_doc = max((f["similaridade"] for f in fontes), default=0.0)
    return similaridade_fora - melhor_doc >= config.MARGEM_FILTRO


def _corpo(modelo: str, mensagens: list[dict], stream: bool, think: bool | None = None) -> dict:
    corpo = {
        "model": modelo,
        "messages": mensagens,
        "stream": stream,
        "keep_alive": config.KEEP_ALIVE,
        "options": {"temperature": config.TEMPERATURE, "num_ctx": config.NUM_CTX},
    }
    think = config.THINK if think is None else think
    if think is not None:  # liga/desliga o "raciocínio" de modelos como o qwen3
        corpo["think"] = think
    return corpo


class FiltroPensamento:
    """Remove blocos <think>...</think> que alguns modelos (ex.: qwen3) escrevem antes da resposta.

    Funciona com o texto chegando aos pedaços, mesmo com a marcação partida entre dois pedaços.
    """

    ABRE, FECHA = "<think>", "</think>"

    def __init__(self) -> None:
        self.pendente = ""
        self.dentro = False
        self.inicio = True  # ainda não saiu nenhum texto visível

    def _sufixo_parcial(self, texto: str, marca: str) -> int:
        for n in range(min(len(marca) - 1, len(texto)), 0, -1):
            if texto.endswith(marca[:n]):
                return n
        return 0

    def alimentar(self, pedaco: str) -> str:
        self.pendente += pedaco
        saida = []
        while self.pendente:
            if self.dentro:
                i = self.pendente.find(self.FECHA)
                if i < 0:
                    n = self._sufixo_parcial(self.pendente, self.FECHA)
                    self.pendente = self.pendente[len(self.pendente) - n:] if n else ""
                    break
                self.pendente = self.pendente[i + len(self.FECHA):]
                self.dentro = False
            else:
                i = self.pendente.find(self.ABRE)
                if i < 0:
                    n = self._sufixo_parcial(self.pendente, self.ABRE)
                    corte = len(self.pendente) - n
                    saida.append(self.pendente[:corte])
                    self.pendente = self.pendente[corte:]
                    break
                saida.append(self.pendente[:i])
                self.pendente = self.pendente[i + len(self.ABRE):]
                self.dentro = True
        texto = "".join(saida)
        if self.inicio:  # não começa a resposta com linhas em branco que sobraram do bloco
            texto = texto.lstrip()
            self.inicio = not texto
        return texto

    def finalizar(self) -> str:
        resto = "" if self.dentro else self.pendente
        self.pendente = ""
        return resto.lstrip() if self.inicio else resto


async def gerar_resposta_stream(
    cliente: httpx.AsyncClient, modelo: str, mensagens: list[dict], think: bool | None = None
) -> AsyncIterator[str]:
    filtro = FiltroPensamento()
    corpo = _corpo(modelo, mensagens, True, think)
    async with cliente.stream("POST", "/api/chat", json=corpo, timeout=None) as r:
        if r.status_code != 200:
            detalhe = (await r.aread()).decode(errors="replace")
            raise RuntimeError(f"Ollama respondeu {r.status_code}: {detalhe}")
        async for linha in r.aiter_lines():
            if not linha.strip():
                continue
            dado = json.loads(linha)
            if dado.get("error"):
                raise RuntimeError(dado["error"])
            # O raciocínio pode vir no campo "thinking" (ignorado) ou dentro do texto (filtrado).
            pedaco = filtro.alimentar(dado.get("message", {}).get("content", ""))
            if pedaco:
                yield pedaco
            if dado.get("done"):
                break
    resto = filtro.finalizar()
    if resto:
        yield resto


async def gerar_resposta(cliente: httpx.AsyncClient, modelo: str, mensagens: list[dict]) -> str:
    partes = [p async for p in gerar_resposta_stream(cliente, modelo, mensagens)]
    return "".join(partes)
