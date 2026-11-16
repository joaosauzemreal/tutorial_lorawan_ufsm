"""Triagem das mensagens antes (e logo depois) da busca nos documentos.

Modelos pequenos inventam respostas quando recebem algo vago, como uma palavra solta
("banana", "teste") ou letras aleatórias ("asdfg"). Aqui essas mensagens ganham uma
resposta pronta, sem passar pelo modelo:
- cumprimentos e agradecimentos: resposta simpática dizendo o que o assistente faz;
- rabiscos (letras aleatórias, só símbolos): pede para escrever a pergunta completa;
- palavras soltas que não se parecem com a documentação: pede para detalhar.
Palavras soltas do assunto ("OTAA", "gateway") seguem para o modelo, que recebe a
pergunta reescrita como "explique o que é ...".
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from . import config
from .prompts import AGRADECIMENTO, PEDIR_DETALHES, RECUSA, SAUDACAO

SAUDACOES = {
    "oi", "oii", "oie", "ola", "opa", "ei", "eai", "e ai", "hey", "hi", "hello", "salve",
    "bom dia", "boa tarde", "boa noite", "tudo bem", "tudo bom", "oi tudo bem", "ola tudo bem",
    "oi bom dia", "oi boa tarde", "oi boa noite", "ola bom dia", "ola boa tarde", "ola boa noite",
    "quem e voce", "quem e vc", "o que voce faz", "o que vc faz", "ajuda", "help", "menu",
    "qual seu nome", "qual o seu nome", "qual e o seu nome", "como voce se chama", "oi loria", "ola loria", "loria",
}
AGRADECIMENTOS = {
    "obrigado", "obrigada", "obg", "brigado", "brigada", "muito obrigado", "muito obrigada",
    "valeu", "vlw", "show", "top", "legal", "otimo", "ok", "okay", "certo", "beleza", "blz",
    "entendi", "perfeito", "tchau", "ate mais", "falou", "funcionou", "deu certo",
}
VOGAIS = set("aeiouy")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação: "Olá!!" -> "ola"."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto).split())


def palavras(texto: str) -> list[str]:
    return normalizar(texto).split()


@lru_cache(maxsize=1)
def vocabulario() -> frozenset[str]:
    """Palavras que aparecem na documentação: nunca contam como rabisco ("nwkskey", "appskey")."""
    from .rag import listar_documentos  # import aqui para evitar import circular
    palavras_doc: set[str] = set()
    for arq in listar_documentos(config.DOCS_PATHS):
        try:
            palavras_doc.update(normalizar(arq.read_text(encoding="utf-8")).split())
        except OSError:
            pass
    return frozenset(palavras_doc)


def parece_aleatoria(p: str) -> bool:
    if not p.isalpha() or p in vocabulario():
        return False  # siglas com números (sx1262, au915) e termos da documentação são válidos
    if len(p) >= 5 and not (set(p) & VOGAIS):
        return True  # "qwrtz", "sdfgh"
    if re.search(r"[^aeiouy]{5,}", p):
        return True  # "asdfghjk"
    if re.search(r"(.)\1{3,}", p):
        return True  # "aaaaa", "kkkkkk"
    return False


def eh_rabisco(texto: str) -> bool:
    """Letras aleatórias, só símbolos ou só números."""
    norm = normalizar(texto)
    letras = re.sub(r"[^a-z]", "", norm)
    if len(letras) < 2:
        return True  # "?", "123", "a"
    # Só é rabisco se todas as palavras com letras parecerem aleatórias ("asdfgh", "kkkkkk")
    com_letras = [p for p in norm.split() if re.search(r"[a-z]", p)]
    return all(parece_aleatoria(p) for p in com_letras)


def eh_curta(texto: str) -> bool:
    return len(palavras(texto)) <= config.MAX_PALAVRAS_CURTA


def resposta_antes_da_busca(pergunta: str) -> str | None:
    """Respostas que não dependem dos documentos (cumprimentos, agradecimentos, rabiscos)."""
    norm = normalizar(pergunta)
    if norm in SAUDACOES:
        return SAUDACAO
    if norm in AGRADECIMENTOS:
        return AGRADECIMENTO
    if eh_rabisco(pergunta):
        return PEDIR_DETALHES
    return None


def resposta_depois_da_busca(pergunta: str, primeira: bool, melhor_doc: float, similaridade_fora: float) -> str | None:
    """Decide, com as similaridades da busca, se a mensagem vai para o modelo.

    primeira: é a primeira pergunta da conversa (sem contexto anterior)?
    """
    if config.FILTRO_ASSUNTO and similaridade_fora - melhor_doc >= config.MARGEM_FILTRO:
        return RECUSA  # parece mais com os exemplos fora do assunto
    if melhor_doc < config.LIMIAR_MINIMO:
        return RECUSA  # nada na documentação se parece com a pergunta
    if primeira and eh_curta(pergunta) and melhor_doc < config.LIMIAR_CURTA:
        return PEDIR_DETALHES  # palavra solta que não é do assunto ("banana", "teste")
    return None
