"""Faz todas as perguntas de avaliacao/perguntas_teste.md e salva as respostas.

Uso (na pasta chatbot/):
    python -m app.avaliar                      # usa o modelo configurado (CHAT_MODEL)
    python -m app.avaliar --modelo gemma3:4b   # testa outro modelo
Com Docker:
    docker compose exec app python -m app.avaliar --modelo qwen3:4b
"""

from __future__ import annotations

import argparse
import asyncio
import re
import time
from datetime import datetime

import httpx

from . import config, rag
from .motor import gerar_resposta, preparar_conversa

LINHA_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")


def ler_perguntas() -> list[tuple[str, str, str]]:
    texto = (config.AVALIACAO_DIR / "perguntas_teste.md").read_text(encoding="utf-8")
    return [m.groups() for linha in texto.splitlines() if (m := LINHA_RE.match(linha))]


async def principal(modelo: str) -> None:
    perguntas = ler_perguntas()
    async with httpx.AsyncClient(base_url=config.OLLAMA_URL, timeout=None) as cliente:
        await rag.esperar_ollama(cliente)
        await rag.garantir_modelo(cliente, config.EMBED_MODEL)
        await rag.garantir_modelo(cliente, modelo)
        indice = await rag.construir_indice(cliente, config.DOCS_PATHS, config.EMBED_MODEL, config.CACHE_DIR)

        linhas = [
            f"# Avaliação: {modelo}",
            "",
            f"{datetime.now():%d/%m/%Y %H:%M} · embeddings: {config.EMBED_MODEL} · "
            f"TOP_K={config.TOP_K} · temperatura={config.TEMPERATURE}",
            "",
            "Marque cada resposta: ✅ acertou · 🟡 parcial · ❌ errou/inventou",
            "",
        ]
        tempos = []
        for numero, pergunta, esperado in perguntas:
            mensagens, fontes = await preparar_conversa(cliente, indice, [{"role": "user", "content": pergunta}])
            inicio = time.perf_counter()
            resposta = await gerar_resposta(cliente, modelo, mensagens)
            tempo = time.perf_counter() - inicio
            tempos.append(tempo)
            print(f"[{numero}/{len(perguntas)}] {tempo:5.1f}s  {pergunta}")
            linhas += [
                f"## {numero}. {pergunta}",
                "",
                f"**Esperado:** {esperado}",
                "",
                "**Fontes encontradas (similaridade):** " + ", ".join(
                    "{} ({:.2f})".format(f["titulo"], f["similaridade"]) for f in fontes
                ),
                "",
                f"**Resposta ({tempo:.1f} s):**",
                "",
                resposta.strip(),
                "",
                "**Nota:** ",
                "",
                "---",
                "",
            ]
        linhas.insert(4, f"Tempo médio por resposta: {sum(tempos) / len(tempos):.1f} s")
        linhas.insert(5, "")

    pasta = config.AVALIACAO_DIR / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    nome = re.sub(r"[^a-zA-Z0-9.-]+", "_", modelo)
    destino = pasta / f"{nome}_{datetime.now():%Y%m%d_%H%M}.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nResultados salvos em {destino}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", default=config.CHAT_MODEL)
    asyncio.run(principal(parser.parse_args().modelo))
