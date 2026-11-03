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
# Só vão para o modelo os trechos com similaridade de no máximo MARGEM_TRECHOS abaixo do melhor.
# Trechos bem menos parecidos que o melhor só distraem um modelo pequeno.
MARGEM_TRECHOS = float(os.getenv("MARGEM_TRECHOS", "0.04"))
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))         # janela de contexto do modelo (tokens)
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))  # 0 = sempre a mesma resposta, copia valores com mais fidelidade
MAX_HISTORICO = int(os.getenv("MAX_HISTORICO", "6"))  # mensagens anteriores enviadas ao modelo
_keep_alive = os.getenv("KEEP_ALIVE", "60m").strip()  # quanto tempo o modelo fica carregado (-1 = sempre)
# O Ollama aceita duração com unidade ("60m") ou número de segundos (-1); texto "-1" sem unidade dá erro.
KEEP_ALIVE: str | int = int(_keep_alive) if _keep_alive.lstrip("-").isdigit() else _keep_alive

# Filtro de assunto: a pergunta é recusada quando se parece mais com os exemplos de
# app/exemplos_fora_do_assunto.txt do que com a documentação, por pelo menos MARGEM_FILTRO.
FILTRO_ASSUNTO = os.getenv("FILTRO_ASSUNTO", "true").strip().lower() != "false"
MARGEM_FILTRO = float(os.getenv("MARGEM_FILTRO", "0.05"))
EXEMPLOS_FORA = Path(__file__).parent / "exemplos_fora_do_assunto.txt"

# Limite de perguntas, para o chat poder ficar aberto na internet (0 = sem limite).
LIMITE_POR_MINUTO = int(os.getenv("LIMITE_POR_MINUTO", "10"))          # por pessoa (IP)
LIMITE_POR_DIA = int(os.getenv("LIMITE_POR_DIA", "200"))               # por pessoa (IP)
LIMITE_GLOBAL_POR_MINUTO = int(os.getenv("LIMITE_GLOBAL_POR_MINUTO", "120"))  # somando todo mundo

# Modelos extras que podem ser escolhidos por pergunta, só para testes de comparação (separados por vírgula).
# Ex.: MODELOS_TESTE=qwen3:14b,gemma3:12b  — são baixados automaticamente depois que o chat inicia.
MODELOS_TESTE = [m.strip() for m in os.getenv("MODELOS_TESTE", "").split(",") if m.strip()]

# "Raciocínio" de modelos que pensam antes de responder (ex.: qwen3). false = mais rápido.
# Vazio = usa o padrão do modelo. Só defina para modelos que suportam raciocínio.
_think = os.getenv("THINK", "").strip().lower()
THINK: bool | None = {"true": True, "false": False}.get(_think)

FONTES_URL_BASE = os.getenv(
    "FONTES_URL_BASE", "https://github.com/joaosauzemreal/tutorial_lorawan_ufsm/blob/main/"
)
LINKS_FONTES = {
    "README.md": "README.md",
    "faq_erros.md": "chatbot/conhecimento/faq_erros.md",
    "conceitos_lorawan.md": "chatbot/conhecimento/conceitos_lorawan.md",
    "projeto_ufsm.md": "chatbot/conhecimento/projeto_ufsm.md",
}
