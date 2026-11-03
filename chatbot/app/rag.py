"""Base de conhecimento: divide os documentos em trechos, gera os embeddings e faz a busca."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np

log = logging.getLogger("assistente.rag")

TITULO_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
IMG_HTML_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)
IMG_COM_LINK_RE = re.compile(r"\[!\[([^\]]*)\]\([^)]*\)\]\(([^)]*)\)")
IMG_MD_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
SEPARADOR_RE = re.compile(r"^\s*-{3,}\s*$", re.MULTILINE)


@dataclass
class Trecho:
    arquivo: str
    titulo: str  # caminho completo de títulos, ex.: "Passo a Passo > 2. Cadastrar Dispositivo"
    secao: str   # só o último título, usado para mostrar a fonte
    texto: str   # texto que vai para o modelo (já com arquivo e títulos no início)


def _limpar(md: str) -> str:
    md = IMG_COM_LINK_RE.sub(r"\1: \2", md)  # [![thumb](img)](link) -> "texto: link"
    md = IMG_HTML_RE.sub("", md)
    md = IMG_MD_RE.sub("", md)
    return md


def _quebrar_texto_longo(texto: str, max_chars: int) -> list[str]:
    if len(texto) <= max_chars:
        return [texto]
    partes, atual = [], ""
    for paragrafo in re.split(r"\n\s*\n", texto):
        if atual and len(atual) + len(paragrafo) + 2 > max_chars:
            partes.append(atual.strip())
            atual = ""
        while len(paragrafo) > max_chars:  # parágrafo gigante: corta no tamanho
            partes.append(paragrafo[:max_chars])
            paragrafo = paragrafo[max_chars:]
        atual += paragrafo + "\n\n"
    if atual.strip():
        partes.append(atual.strip())
    return partes


def dividir_markdown(md: str, arquivo: str, max_chars: int = 1500) -> list[Trecho]:
    """Divide um Markdown em trechos pelos títulos (#, ##, ###...).

    Cada trecho leva o caminho de títulos (ex.: "Passo a Passo > 2. Cadastrar Dispositivo"),
    para fazer sentido sozinho quando for entregue ao modelo.
    """
    md = _limpar(md)
    trechos: list[Trecho] = []
    caminho: list[tuple[int, str]] = []
    buffer: list[str] = []
    em_bloco_codigo = False

    def fechar_secao() -> None:
        corpo = SEPARADOR_RE.sub("", "\n".join(buffer)).strip()
        buffer.clear()
        if len(corpo) < 40:
            return
        titulo = " > ".join(t for _, t in caminho) or arquivo
        secao = caminho[-1][1] if caminho else arquivo
        for parte in _quebrar_texto_longo(corpo, max_chars):
            trechos.append(Trecho(arquivo, titulo, secao, f"[{arquivo}] {titulo}\n\n{parte}"))

    for linha in md.splitlines():
        # Só blocos de código na coluna 0 contam; os indentados (dentro de listas) não têm títulos.
        if linha.startswith("```"):
            em_bloco_codigo = not em_bloco_codigo
        m = None if em_bloco_codigo else TITULO_RE.match(linha)
        if m:
            fechar_secao()
            nivel = len(m.group(1))
            caminho = [(n, t) for n, t in caminho if n < nivel] + [(nivel, m.group(2))]
        else:
            buffer.append(linha)
    fechar_secao()
    return trechos


def listar_documentos(caminhos: list[Path]) -> list[Path]:
    arquivos: list[Path] = []
    for c in caminhos:
        if c.is_dir():
            arquivos.extend(sorted(c.glob("*.md")))
        elif c.is_file():
            arquivos.append(c)
        else:
            log.warning("Documento não encontrado: %s", c)
    return arquivos


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

async def esperar_ollama(cliente: httpx.AsyncClient, tentativas: int = 90) -> None:
    import asyncio

    for i in range(tentativas):
        try:
            r = await cliente.get("/api/version", timeout=5)
            r.raise_for_status()
            log.info("Ollama disponível (versão %s)", r.json().get("version"))
            return
        except Exception:
            if i == 0:
                log.info("Aguardando o Ollama responder em %s ...", cliente.base_url)
            await asyncio.sleep(2)
    raise RuntimeError(f"O Ollama não respondeu em {cliente.base_url}")


async def garantir_modelo(cliente: httpx.AsyncClient, modelo: str) -> None:
    """Baixa o modelo no Ollama se ele ainda não estiver instalado."""
    r = await cliente.get("/api/tags", timeout=30)
    r.raise_for_status()
    instalados = {m["name"] for m in r.json().get("models", [])}
    if modelo in instalados or f"{modelo}:latest" in instalados:
        return
    log.info("Baixando o modelo %s (pode levar alguns minutos)...", modelo)
    r = await cliente.post("/api/pull", json={"model": modelo, "stream": False}, timeout=None)
    r.raise_for_status()
    log.info("Modelo %s baixado.", modelo)


async def gerar_embeddings(cliente: httpx.AsyncClient, modelo: str, textos: list[str]) -> np.ndarray:
    vetores = []
    for i in range(0, len(textos), 16):
        r = await cliente.post("/api/embed", json={"model": modelo, "input": textos[i:i + 16]}, timeout=600)
        r.raise_for_status()
        vetores.extend(r.json()["embeddings"])
    v = np.asarray(vetores, dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
    return v


# ---------------------------------------------------------------------------
# Índice
# ---------------------------------------------------------------------------

class Indice:
    def __init__(self, trechos: list[Trecho], vetores: np.ndarray, modelo_embed: str,
                 vetores_fora: np.ndarray | None = None):
        self.trechos = trechos
        self.vetores = vetores
        self.modelo_embed = modelo_embed
        self.vetores_fora = vetores_fora  # exemplos de perguntas fora do assunto

    async def buscar(self, cliente: httpx.AsyncClient, consulta: str, k: int) -> tuple[list[tuple[Trecho, float]], float]:
        """Devolve os k trechos mais parecidos e a maior similaridade com os exemplos fora do assunto."""
        q = (await gerar_embeddings(cliente, self.modelo_embed, [consulta]))[0]
        pontuacoes = self.vetores @ q
        melhores = np.argsort(-pontuacoes)[:k]
        fora = float((self.vetores_fora @ q).max()) if self.vetores_fora is not None and len(self.vetores_fora) else 0.0
        return [(self.trechos[i], float(pontuacoes[i])) for i in melhores], fora


def ler_exemplos(caminho: Path) -> list[str]:
    if not caminho.exists():
        return []
    linhas = (l.strip() for l in caminho.read_text(encoding="utf-8").splitlines())
    return [l for l in linhas if l and not l.startswith("#")]


async def construir_indice(
    cliente: httpx.AsyncClient, caminhos: list[Path], modelo_embed: str, pasta_cache: Path,
    exemplos_fora: list[str] | None = None,
) -> Indice:
    trechos: list[Trecho] = []
    for arq in listar_documentos(caminhos):
        trechos.extend(dividir_markdown(arq.read_text(encoding="utf-8"), arq.name))
    if not trechos:
        raise RuntimeError("Nenhum documento encontrado para a base de conhecimento.")

    # Cache dos embeddings: só recalcula os trechos que mudaram.
    pasta_cache.mkdir(parents=True, exist_ok=True)
    arq_cache = pasta_cache / f"embeddings_{re.sub(r'[^a-zA-Z0-9]+', '_', modelo_embed)}.json"
    cache: dict[str, list[float]] = {}
    if arq_cache.exists():
        try:
            cache = json.loads(arq_cache.read_text())
        except Exception:
            log.warning("Cache de embeddings inválido; será recriado.")

    exemplos_fora = exemplos_fora or []
    textos = [t.texto for t in trechos] + exemplos_fora
    chaves = [hashlib.sha256(t.encode()).hexdigest() for t in textos]
    faltando = [i for i, c in enumerate(chaves) if c not in cache]
    if faltando:
        log.info("Gerando embeddings de %d textos...", len(faltando))
        novos = await gerar_embeddings(cliente, modelo_embed, [textos[i] for i in faltando])
        for i, v in zip(faltando, novos):
            cache[chaves[i]] = v.tolist()
    arq_cache.write_text(json.dumps({c: cache[c] for c in chaves}))

    todos = np.asarray([cache[c] for c in chaves], dtype=np.float32)
    vetores, vetores_fora = todos[:len(trechos)], todos[len(trechos):]
    log.info("Base de conhecimento pronta: %d trechos de %d documentos; %d exemplos fora do assunto.",
             len(trechos), len({t.arquivo for t in trechos}), len(exemplos_fora))
    return Indice(trechos, vetores, modelo_embed, vetores_fora)
