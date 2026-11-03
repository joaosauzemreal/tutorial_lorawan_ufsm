"""Configuração, lida das variáveis de ambiente (veja chatbot/.env.example)."""

import os
from pathlib import Path

_PASTA_CHATBOT = Path(__file__).resolve().parents[1]
_RAIZ_REPO = _PASTA_CHATBOT.parent


def _caminhos(valor: str | None, padrao: list[Path]) -> list[Path]:
    if not valor:
        return padrao
    return [Path(p) for p in valor.split(os.pathsep) if p.strip()]


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "phi4-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")

# Documentos da base de conhecimento: README do tutorial + pasta conhecimento/
DOCS_PATHS = _caminhos(os.getenv("DOCS_PATHS"), [_RAIZ_REPO / "README.md", _PASTA_CHATBOT / "conhecimento"])
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(_PASTA_CHATBOT / "cache")))
AVALIACAO_DIR = Path(os.getenv("AVALIACAO_DIR", str(_PASTA_CHATBOT / "avaliacao")))

TOP_K = int(os.getenv("TOP_K", "5"))                # quantos trechos vão junto com a pergunta
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))         # janela de contexto do modelo (tokens)
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_HISTORICO = int(os.getenv("MAX_HISTORICO", "6"))  # mensagens anteriores enviadas ao modelo
KEEP_ALIVE = os.getenv("KEEP_ALIVE", "60m")         # quanto tempo o modelo fica carregado na RAM

FONTES_URL_BASE = os.getenv(
    "FONTES_URL_BASE", "https://github.com/joaosauzemreal/tutorial_lorawan_ufsm/blob/main/"
)
LINKS_FONTES = {
    "README.md": "README.md",
    "faq_erros.md": "chatbot/conhecimento/faq_erros.md",
    "conceitos_lorawan.md": "chatbot/conhecimento/conceitos_lorawan.md",
    "projeto_ufsm.md": "chatbot/conhecimento/projeto_ufsm.md",
}
