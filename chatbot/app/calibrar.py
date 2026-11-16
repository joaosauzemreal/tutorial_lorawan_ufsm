"""Calibração da triagem: mede as similaridades de mensagens curtas, sem chamar o modelo de IA.

Leva poucos segundos. Para cada mensagem mostra a similaridade com o melhor trecho da
documentação e com os exemplos fora do assunto, buscando a mensagem como foi escrita e como
"o que é <mensagem>". Com isso dá para escolher LIMIAR_CURTA: as mensagens do assunto devem
ficar acima dele e as aleatórias, abaixo.

Uso (na pasta chatbot/):
    python -m app.calibrar
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import httpx

from . import config, rag
from .triagem import resposta_antes_da_busca

# (mensagem, deveria ir ao modelo?)
MENSAGENS = [
    # Do assunto: devem ser respondidas
    ("OTAA", True), ("ABP", True), ("gateway", True), ("antena", True), ("LoRa", True),
    ("LoRaWAN", True), ("TTN", True), ("join", True), ("AppKey", True), ("DevEUI", True),
    ("JoinEUI", True), ("payload", True), ("downlink", True), ("RSSI", True), ("SNR", True),
    ("spreading factor", True), ("ADR", True), ("licença heltec", True), ("secrets.h", True),
    ("AU915", True), ("classe A", True), ("Heltec V3", True), ("frequência", True),
    ("ENVIANDO JOIN", True), ("ACK", True), ("live data", True), ("display OLED", True),
    ("fair use", True), ("cluster eu1", True), ("payload formatter", True),
    # Fora do assunto ou vagas: não devem ir ao modelo
    ("banana", False), ("teste", False), ("futebol", False), ("carro", False), ("pizza", False),
    ("amor", False), ("gato", False), ("música", False), ("cadeira", False), ("azul", False),
    ("asdf", False), ("qwerty", False), ("abc", False), ("sim", False), ("não", False),
    ("por que", False), ("como", False), ("o que", False), ("me ajuda", False), ("prova", False),
    ("Neymar", False), ("ChatGPT", False), ("receita de bolo", False), ("Windows", False),
    ("matemática", False), ("ufsm", False), ("celular", False), ("internet", False),
]


async def principal() -> None:
    async with httpx.AsyncClient(base_url=config.OLLAMA_URL, timeout=None) as cliente:
        await rag.esperar_ollama(cliente)
        await rag.garantir_modelo(cliente, config.EMBED_MODEL)
        indice = await rag.construir_indice(cliente, config.DOCS_PATHS, config.EMBED_MODEL, config.CACHE_DIR,
                                            rag.ler_exemplos(config.EXEMPLOS_FORA))
        linhas = [
            f"# Calibração da triagem · {datetime.now():%d/%m/%Y %H:%M}",
            "",
            f"LIMIAR_CURTA={config.LIMIAR_CURTA} · MARGEM_FILTRO={config.MARGEM_FILTRO} · "
            f"EXPANDIR_CURTA={config.EXPANDIR_CURTA}",
            "",
            "| Mensagem | Assunto? | Doc | Fora | Doc \"o que é\" | Fora \"o que é\" | Triagem atual |",
            "|---|---|---|---|---|---|---|",
        ]
        for mensagem, assunto in MENSAGENS:
            res, fora = await indice.buscar(cliente, mensagem, 1)
            res2, fora2 = await indice.buscar(cliente, f"o que é {mensagem}", 1)
            doc, doc2 = res[0][1], res2[0][1]
            d, f = (doc2, fora2) if config.EXPANDIR_CURTA else (doc, fora)
            if resposta_antes_da_busca(mensagem):
                decisao = "resposta pronta (antes da busca)"
            elif config.FILTRO_ASSUNTO and f - d >= config.MARGEM_FILTRO:
                decisao = "recusa"
            elif d < config.LIMIAR_CURTA:
                decisao = "pedir detalhes"
            else:
                decisao = "vai ao modelo"
            certo = (decisao == "vai ao modelo") == assunto
            linhas.append(f"| {mensagem} | {'sim' if assunto else 'não'} | {doc:.3f} | {fora:.3f} | "
                          f"{doc2:.3f} | {fora2:.3f} | {decisao} {'✅' if certo else '❌'} |")
        texto = "\n".join(linhas)
    print(texto)
    pasta = config.AVALIACAO_DIR / "resultados"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"calibracao_{datetime.now():%Y%m%d_%H%M}.md"
    destino.write_text(texto + "\n", encoding="utf-8")
    print(f"\nSalvo em {destino}")


if __name__ == "__main__":
    asyncio.run(principal())
