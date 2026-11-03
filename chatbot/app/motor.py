"""Monta a conversa (pergunta + trechos encontrados) e conversa com o modelo no Ollama."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from . import config
from .prompts import CLASSIFICADOR_PERGUNTA, CLASSIFICADOR_SISTEMA, SYSTEM_PROMPT, montar_pergunta
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
    return mensagens, fontes


async def pergunta_no_assunto(cliente: httpx.AsyncClient, modelo: str, historico: list[dict]) -> bool:
    """Pergunta ao modelo, com SIM/NAO, se a pergunta é sobre o tutorial. Em caso de dúvida, responde True."""
    perguntas = [m["content"] for m in historico if m["role"] == "user"]
    contexto = f"Pergunta anterior do mesmo usuário: {perguntas[-2]}" if len(perguntas) > 1 else ""
    corpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": CLASSIFICADOR_SISTEMA},
            {"role": "user", "content": CLASSIFICADOR_PERGUNTA.format(contexto=contexto, pergunta=perguntas[-1])},
        ],
        "stream": False,
        "keep_alive": config.KEEP_ALIVE,
        # Mesmo num_ctx da resposta: com um valor diferente o Ollama recarrega o modelo a cada troca.
        "options": {"temperature": 0, "num_predict": 5, "num_ctx": config.NUM_CTX},
    }
    if config.THINK is not None:
        corpo["think"] = False
    try:
        r = await cliente.post("/api/chat", json=corpo, timeout=60)
        r.raise_for_status()
        texto = r.json().get("message", {}).get("content", "")
    except Exception:  # noqa: BLE001  (se o classificador falhar, segue respondendo normalmente)
        return True
    texto = FiltroPensamento().alimentar(texto).strip().upper()
    return not (texto.startswith("NAO") or texto.startswith("NÃO"))


async def deve_recusar(cliente: httpx.AsyncClient, modelo: str, historico: list[dict], fontes: list[dict]) -> bool:
    """Decide se a pergunta deve receber a frase de recusa.

    Só recusa quando o filtro está ligado, a documentação não tem nenhum trecho muito parecido
    com a pergunta (similaridade abaixo de LIMIAR_FILTRO) e o classificador diz que o assunto é outro.
    """
    if not config.FILTRO_ASSUNTO:
        return False
    melhor = max((f["similaridade"] for f in fontes), default=0.0)
    if melhor >= config.LIMIAR_FILTRO:
        return False
    return not await pergunta_no_assunto(cliente, modelo, historico)


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
