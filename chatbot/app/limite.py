"""Limite de perguntas por pessoa (endereço IP), para o chat poder ficar aberto na internet."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request

# Endereços de quem repassa as requisições ao chat (o Tailscale Funnel ou um proxy reverso
# rodando no próprio servidor). Para eles, o IP real do visitante vem no X-Forwarded-For.
PROXIES_CONFIAVEIS = {"127.0.0.1", "::1"}


def ip_do_cliente(request: Request) -> str:
    ip = request.client.host if request.client else "desconhecido"
    if ip in PROXIES_CONFIAVEIS:
        encaminhado = request.headers.get("x-forwarded-for", "")
        if encaminhado:
            return encaminhado.split(",")[0].strip()
    return ip


class Limitador:
    """Janela deslizante: no máximo `por_minuto` e `por_dia` perguntas por chave,
    e no máximo `global_por_minuto` perguntas somando todo mundo."""

    def __init__(self, por_minuto: int, por_dia: int, global_por_minuto: int):
        self.por_minuto = por_minuto
        self.por_dia = por_dia
        self.global_por_minuto = global_por_minuto
        self.historico: dict[str, deque[float]] = defaultdict(deque)
        self.global_: deque[float] = deque()
        self._ultima_limpeza = time.monotonic()

    def _limpar(self, agora: float) -> None:
        if agora - self._ultima_limpeza < 600:
            return
        self._ultima_limpeza = agora
        for chave in [c for c, h in self.historico.items() if not h or agora - h[-1] > 86400]:
            del self.historico[chave]

    def verificar(self, chave: str) -> str | None:
        """Registra a pergunta e devolve None se ela for permitida, ou a mensagem de erro."""
        agora = time.monotonic()
        self._limpar(agora)

        while self.global_ and agora - self.global_[0] > 60:
            self.global_.popleft()
        if self.global_por_minuto and len(self.global_) >= self.global_por_minuto:
            return "O assistente está recebendo muitas perguntas agora. Tente de novo em um minuto."

        h = self.historico[chave]
        while h and agora - h[0] > 86400:
            h.popleft()
        ultimo_minuto = sum(1 for t in h if agora - t <= 60)
        if self.por_minuto and ultimo_minuto >= self.por_minuto:
            return "Você fez muitas perguntas em pouco tempo. Espere um minuto e tente de novo."
        if self.por_dia and len(h) >= self.por_dia:
            return "Você atingiu o limite de perguntas de hoje. Tente de novo amanhã."

        h.append(agora)
        self.global_.append(agora)
        return None
