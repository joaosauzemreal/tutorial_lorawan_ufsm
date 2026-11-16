"""Faz todas as perguntas de avaliacao/perguntas_teste.md e salva as respostas.

Uso (na pasta chatbot/):
    python -m app.avaliar                      # usa o modelo configurado (CHAT_MODEL)
    python -m app.avaliar --modelo gemma3:4b   # testa outro modelo
    python -m app.avaliar --secao Validação    # só as seções cujo título contém este texto

Correção automática: a 4ª coluna da tabela ("Verificação") tem regras separadas por ";":
    [modelo]            a pergunta precisa chegar ao modelo (não pode ter resposta pronta)
    [recusa/detalhes]   precisa receber uma destas respostas prontas da triagem
                        (recusa, detalhes, cumprimento, agradecimento)
    eu1/europa          a resposta precisa conter um destes termos
    !nam1               a resposta não pode conter este termo
Maiúsculas e acentos são ignorados. A correção automática não substitui a leitura das
respostas: ela confere os itens principais, mas não percebe tudo o que foi inventado.
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
from .motor import gerar_resposta, preparar_conversa, resposta_pronta
from .prompts import AGRADECIMENTO, PEDIR_DETALHES, RECUSA, SAUDACAO
from .triagem import normalizar, resposta_antes_da_busca

NOMES_PRONTAS = {RECUSA: "recusa", PEDIR_DETALHES: "detalhes", SAUDACAO: "cumprimento",
                 AGRADECIMENTO: "agradecimento"}

LINHA_RE = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")


def ler_perguntas() -> list[dict]:
    """Lê as tabelas de perguntas_teste.md: | # | Pergunta | Esperado | Verificação (opcional) |"""
    texto = (config.AVALIACAO_DIR / "perguntas_teste.md").read_text(encoding="utf-8")
    perguntas, secao = [], ""
    for linha in texto.splitlines():
        if linha.startswith("## "):
            secao = linha[3:].strip()
        elif m := LINHA_RE.match(linha):
            colunas = [c.strip() for c in m.group(2).split("|")]
            perguntas.append({
                "numero": m.group(1), "pergunta": colunas[0],
                "esperado": colunas[1] if len(colunas) > 1 else "",
                "verificacao": colunas[2] if len(colunas) > 2 else "",
                "secao": secao,
            })
    return perguntas


def verificar(regras: str, resposta: str, pronta: str | None) -> list[str]:
    """Confere a resposta com as regras da coluna Verificação. Devolve o que falhou."""
    falhas = []
    texto = " " + normalizar(resposta) + " "
    tipo = NOMES_PRONTAS.get(pronta, "?") if pronta else "modelo"
    for regra in (r.strip() for r in regras.split(";")):
        if not regra:
            continue
        if regra.startswith("[") and regra.endswith("]"):
            aceitos = [normalizar(a) for a in regra[1:-1].split("/")]
            if normalizar(tipo) not in aceitos:
                falhas.append(f"esperava {regra}, veio [{tipo}]")
        elif regra.startswith("!"):
            achados = [t for t in regra[1:].split("/") if normalizar(t) and normalizar(t) in texto]
            if achados:
                falhas.append(f"não podia conter \"{achados[0]}\"")
        elif not any(normalizar(t) in texto for t in regra.split("/") if normalizar(t)):
            falhas.append(f"faltou \"{regra}\"")
    return falhas


async def principal(modelo: str, filtro_secao: str | None = None) -> None:
    perguntas = ler_perguntas()
    if filtro_secao:
        perguntas = [p for p in perguntas if normalizar(filtro_secao) in normalizar(p["secao"])]
    async with httpx.AsyncClient(base_url=config.OLLAMA_URL, timeout=None) as cliente:
        await rag.esperar_ollama(cliente)
        await rag.garantir_modelo(cliente, config.EMBED_MODEL)
        await rag.garantir_modelo(cliente, modelo)
        indice = await rag.construir_indice(cliente, config.DOCS_PATHS, config.EMBED_MODEL, config.CACHE_DIR,
                                            rag.ler_exemplos(config.EXEMPLOS_FORA))

        linhas = [
            f"# Avaliação: {modelo}",
            "",
            f"{datetime.now():%d/%m/%Y %H:%M} · embeddings: {config.EMBED_MODEL} · "
            f"TOP_K={config.TOP_K} · MARGEM_TRECHOS={config.MARGEM_TRECHOS} · temperatura={config.TEMPERATURE} · "
            f"filtro de assunto: {'ligado, margem ' + str(config.MARGEM_FILTRO) if config.FILTRO_ASSUNTO else 'desligado'} · "
            f"LIMIAR_CURTA={config.LIMIAR_CURTA} · LIMIAR_MINIMO={config.LIMIAR_MINIMO} · "
            f"EXPANDIR_CURTA={config.EXPANDIR_CURTA}",
            "",
            "Marque cada resposta: ✅ acertou · 🟡 parcial · ❌ errou/inventou",
            "",
        ]
        tempos = []
        placar: dict[str, list[int]] = {}   # seção -> [aprovadas, com verificação]
        reprovadas: list[str] = []
        for item in perguntas:
            numero, pergunta, esperado = item["numero"], item["pergunta"], item["esperado"]
            historico = [{"role": "user", "content": pergunta}]
            inicio = time.perf_counter()
            fontes, sim_fora = [], 0.0
            pronta = resposta_antes_da_busca(pergunta)
            if not pronta:
                mensagens, fontes, sim_fora = await preparar_conversa(cliente, indice, historico)
                pronta = resposta_pronta(historico, fontes, sim_fora)
            if pronta:
                resposta = f"_(resposta pronta da triagem: {NOMES_PRONTAS.get(pronta, '?')})_\n\n{pronta}"
            else:
                resposta = await gerar_resposta(cliente, modelo, mensagens)
            tempo = time.perf_counter() - inicio
            tempos.append(tempo)
            correcao = ""
            if item["verificacao"]:
                falhas = verificar(item["verificacao"], resposta, pronta)
                p = placar.setdefault(item["secao"], [0, 0])
                p[1] += 1
                if falhas:
                    reprovadas.append(f"- **{numero}.** {pergunta} — {'; '.join(falhas)}")
                    correcao = "❌ " + "; ".join(falhas)
                else:
                    p[0] += 1
                    correcao = "✅"
            print(f"[{numero}] {tempo:5.1f}s {correcao[:1] or ' '} {pergunta}")
            linhas += [
                f"## {numero}. {pergunta}",
                "",
                f"**Esperado:** {esperado}",
                "",
                f"**Correção automática:** {correcao or '(sem verificação)'}",
                "",
                "**Fontes encontradas (similaridade):** " + ", ".join(
                    "{} ({:.2f})".format(f["titulo"], f["similaridade"]) for f in fontes
                ),
                "",
                "**Filtro de assunto:** similaridade com exemplos fora do assunto {:.2f} · "
                "melhor trecho da documentação {:.2f} · diferença {:+.2f} (recusa a partir de {:+.2f})".format(
                    sim_fora, fontes[0]["similaridade"] if fontes else 0.0,
                    sim_fora - (fontes[0]["similaridade"] if fontes else 0.0), config.MARGEM_FILTRO),
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
        resumo = [f"Tempo médio por resposta: {sum(tempos) / len(tempos):.1f} s", "",
                  "## Correção automática", "", "| Seção | Aprovadas |", "|---|---|"]
        for secao, (ok, total) in placar.items():
            resumo.append(f"| {secao} | {ok}/{total} |")
        ok_total, total = sum(p[0] for p in placar.values()), sum(p[1] for p in placar.values())
        resumo += [f"| **Total** | **{ok_total}/{total}** |", ""]
        if reprovadas:
            resumo += ["Reprovadas:", ""] + reprovadas + [""]
        linhas[4:4] = resumo
        print("\n" + "\n".join(resumo))

    pasta = config.AVALIACAO_DIR / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    nome = re.sub(r"[^a-zA-Z0-9.-]+", "_", modelo)
    destino = pasta / f"{nome}_{datetime.now():%Y%m%d_%H%M}.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nResultados salvos em {destino}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", default=config.CHAT_MODEL)
    parser.add_argument("--secao", help="só as seções cujo título contém este texto")
    args = parser.parse_args()
    asyncio.run(principal(args.modelo, args.secao))
