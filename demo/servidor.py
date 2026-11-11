"""Painel do contador de visitantes (demonstração LoRaWAN).

Fica escutando a The Things Network (TTN) por MQTT. Cada pacote que a placa manda na
porta 3 traz o total de visitantes; o painel mostra esse total, por onde o pacote passou
(gateway, força do sinal) e atualiza a página do projetor na hora.

Uso:
    pip install paho-mqtt
    python servidor.py              # lê as chaves do arquivo .env desta pasta
    python servidor.py --simular    # sem placa e sem TTN: inventa visitantes (para ensaiar)

Depois abra http://localhost:8001 no navegador (tela cheia com F11).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import ssl
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA = Path(__file__).resolve().parent
ARQUIVO_ESTADO = PASTA / "estado.json"   # guarda o último total, para sobreviver a um reinício


def ler_env(caminho: Path) -> None:
    """Carrega CHAVE=valor do arquivo .env para as variáveis de ambiente (sem sobrescrever)."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


# ---------------------------------------------------------------------------
# Estado compartilhado entre o MQTT e as páginas abertas
# ---------------------------------------------------------------------------
class Estado:
    def __init__(self) -> None:
        self.trava = threading.Condition()
        self.versao = 0
        self.dados: dict = {
            "visitantes": None,       # None = ainda não chegou nenhum pacote
            "pacotes": 0,             # pacotes recebidos desde que o painel foi aberto
            "ultimo": None,           # detalhes do último pacote
            "historico": [],          # últimos pacotes (mais recente primeiro)
            "ttn": "desconectado",    # situação da conexão com a TTN
            "simulacao": False,
        }
        if ARQUIVO_ESTADO.exists():
            try:
                salvo = json.loads(ARQUIVO_ESTADO.read_text(encoding="utf-8"))
                self.dados["visitantes"] = salvo.get("visitantes")
                self.dados["ultimo"] = salvo.get("ultimo")
                self.dados["historico"] = salvo.get("historico", [])[:8]
            except (OSError, ValueError):
                pass

    def foto(self) -> tuple[int, str]:
        with self.trava:
            return self.versao, json.dumps(self.dados, ensure_ascii=False)

    def alterar(self, **mudancas) -> None:
        with self.trava:
            self.dados.update(mudancas)
            self.versao += 1
            self.trava.notify_all()

    def novo_pacote(self, pacote: dict) -> None:
        with self.trava:
            self.dados["visitantes"] = pacote["visitantes"]
            self.dados["pacotes"] += 1
            self.dados["ultimo"] = pacote
            self.dados["historico"] = ([pacote] + self.dados["historico"])[:8]
            self.versao += 1
            self.trava.notify_all()
            copia = {k: self.dados[k] for k in ("visitantes", "ultimo", "historico")}
        try:
            ARQUIVO_ESTADO.write_text(json.dumps(copia, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def esperar_mudanca(self, versao: int, segundos: float) -> int:
        with self.trava:
            self.trava.wait_for(lambda: self.versao != versao, timeout=segundos)
            return self.versao


estado = Estado()


# ---------------------------------------------------------------------------
# Leitura do pacote que a TTN entrega
# ---------------------------------------------------------------------------
def decodificar_payload(bruto: bytes) -> dict | None:
    """Payload da demonstração: 2 bytes de visitantes + 2 bytes de temperatura x100."""
    if len(bruto) < 2:
        return None
    visitantes = int.from_bytes(bruto[0:2], "big")
    temperatura = None
    if len(bruto) >= 4:
        temperatura = int.from_bytes(bruto[2:4], "big", signed=True) / 100
    return {"visitantes": visitantes, "temperatura": temperatura}


def ler_uplink(mensagem: dict, porta: int) -> dict | None:
    """Transforma o JSON de uplink da TTN no resumo que a página mostra."""
    up = mensagem.get("uplink_message") or {}
    if up.get("f_port") != porta or "frm_payload" not in up:
        return None
    valores = decodificar_payload(base64.b64decode(up["frm_payload"]))
    if valores is None:
        return None

    # Se mais de um gateway ouviu o pacote, mostramos o de sinal mais forte
    gateways = []
    for rx in up.get("rx_metadata") or []:
        gateways.append({
            "id": (rx.get("gateway_ids") or {}).get("gateway_id") or "gateway",
            "rssi": rx.get("rssi", rx.get("channel_rssi")),
            "snr": rx.get("snr"),
        })
    gateways.sort(key=lambda g: g["rssi"] if g["rssi"] is not None else -999, reverse=True)
    melhor = gateways[0] if gateways else {"id": None, "rssi": None, "snr": None}

    config = up.get("settings") or {}
    lora = (config.get("data_rate") or {}).get("lora") or {}
    frequencia = config.get("frequency")
    tempo_no_ar = up.get("consumed_airtime")  # ex.: "0.046336s"

    return {
        **valores,
        "dispositivo": (mensagem.get("end_device_ids") or {}).get("device_id"),
        "contador_quadro": up.get("f_cnt"),
        "gateway": melhor["id"],
        "rssi": melhor["rssi"],
        "snr": melhor["snr"],
        "gateways": len(gateways),
        "sf": lora.get("spreading_factor"),
        "frequencia_mhz": round(int(frequencia) / 1e6, 1) if frequencia else None,
        "tempo_no_ar_ms": round(float(tempo_no_ar.rstrip("s")) * 1000) if tempo_no_ar else None,
        "recebido_em": mensagem.get("received_at") or datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Conexão com a TTN (MQTT)
# ---------------------------------------------------------------------------
def iniciar_mqtt() -> None:
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        raise SystemExit("Falta a biblioteca do MQTT. Rode:  pip install paho-mqtt")

    app_id = os.environ.get("TTN_APP_ID", "").strip()
    chave = os.environ.get("TTN_API_KEY", "").strip()
    regiao = os.environ.get("TTN_REGIAO", "eu1").strip()
    dispositivo = os.environ.get("TTN_DEVICE_ID", "+").strip() or "+"
    porta = int(os.environ.get("PORTA_LORAWAN", "3"))
    if not app_id or not chave:
        raise SystemExit("Preencha TTN_APP_ID e TTN_API_KEY no arquivo .env (veja .env.example).")

    host = f"{regiao}.cloud.thethings.network"
    usuario = f"{app_id}@ttn"
    topico = f"v3/{usuario}/devices/{dispositivo}/up"

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"painel-visitantes-{random.randint(0, 99999)}")
    cliente.username_pw_set(usuario, chave)
    cliente.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    cliente.reconnect_delay_set(min_delay=2, max_delay=30)

    def ao_conectar(cli, _userdata, _flags, codigo, _props):
        if codigo.is_failure:
            print(f"[TTN] Conexão recusada: {codigo}. Confira TTN_APP_ID, TTN_API_KEY e TTN_REGIAO.")
            estado.alterar(ttn=f"recusada ({codigo})")
            return
        cli.subscribe(topico)
        print(f"[TTN] Conectado a {host}. Escutando {topico}")
        estado.alterar(ttn="conectado")

    def ao_desconectar(_cli, _userdata, _flags, codigo, _props):
        print(f"[TTN] Desconectado ({codigo}). Tentando de novo...")
        estado.alterar(ttn="reconectando")

    def ao_receber(_cli, _userdata, msg):
        try:
            pacote = ler_uplink(json.loads(msg.payload), porta)
        except (ValueError, TypeError, KeyError) as e:
            print(f"[TTN] Mensagem que não entendi: {e}")
            return
        if pacote:
            print(f"[TTN] {pacote['visitantes']} visitantes  (gateway {pacote['gateway']}, "
                  f"RSSI {pacote['rssi']} dBm, SNR {pacote['snr']} dB, SF{pacote['sf']})")
            estado.novo_pacote(pacote)

    cliente.on_connect = ao_conectar
    cliente.on_disconnect = ao_desconectar
    cliente.on_message = ao_receber
    estado.alterar(ttn="conectando")
    cliente.connect_async(host, 8883, keepalive=60)
    cliente.loop_start()


def iniciar_simulacao() -> None:
    """Inventa um visitante a cada 6–15 s, no mesmo formato que viria da TTN."""
    estado.alterar(ttn="simulação", simulacao=True)

    def rodar():
        total = estado.dados["visitantes"] or 0
        quadro = 0
        while True:
            time.sleep(random.uniform(6, 15))
            total += 1
            quadro += 1
            estado.novo_pacote({
                "visitantes": total, "temperatura": round(random.uniform(38, 45), 2),
                "dispositivo": "simulado", "contador_quadro": quadro,
                "gateway": "gateway-simulado", "rssi": random.randint(-110, -60),
                "snr": round(random.uniform(-5, 10), 1), "gateways": 1, "sf": 7,
                "frequencia_mhz": random.choice([916.8, 917.0, 917.2, 917.4, 917.6, 917.8, 918.0, 918.2]),
                "tempo_no_ar_ms": 51, "recebido_em": datetime.now(timezone.utc).isoformat(),
            })

    threading.Thread(target=rodar, daemon=True).start()


# ---------------------------------------------------------------------------
# Servidor web
# ---------------------------------------------------------------------------
class Pagina(BaseHTTPRequestHandler):
    def log_message(self, *_args):  # silencia o log de cada acesso
        pass

    def responder(self, codigo: int, tipo: str, corpo: bytes) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        caminho = self.path.split("?")[0]
        if caminho in ("/", "/index.html"):
            self.responder(200, "text/html; charset=utf-8", (PASTA / "painel.html").read_bytes())
        elif caminho == "/api/estado":
            self.responder(200, "application/json; charset=utf-8", estado.foto()[1].encode())
        elif caminho == "/api/eventos":
            self.eventos()
        else:
            self.responder(404, "text/plain; charset=utf-8", b"nao encontrado")

    def eventos(self) -> None:
        """Server-Sent Events: a página fica conectada e recebe cada mudança na hora."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        versao, texto = estado.foto()
        try:
            self.wfile.write(f"data: {texto}\n\n".encode())
            self.wfile.flush()
            while True:
                nova = estado.esperar_mudanca(versao, 15)
                if nova == versao:
                    self.wfile.write(b": ping\n\n")   # mantém a conexão viva
                else:
                    versao, texto = estado.foto()
                    self.wfile.write(f"data: {texto}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


def main() -> None:
    ler_env(PASTA / ".env")
    partes = argparse.ArgumentParser(description="Painel do contador de visitantes LoRaWAN")
    partes.add_argument("--simular", action="store_true", help="inventa visitantes, sem placa e sem TTN")
    partes.add_argument("--porta", type=int, default=int(os.environ.get("PORTA_WEB", "8001")))
    partes.add_argument("--host", default=os.environ.get("HOST_WEB", "0.0.0.0"))
    args = partes.parse_args()

    if args.simular or os.environ.get("SIMULAR", "").lower() in ("1", "true", "sim"):
        iniciar_simulacao()
    else:
        iniciar_mqtt()

    servidor = ThreadingHTTPServer((args.host, args.porta), Pagina)
    servidor.daemon_threads = True
    print(f"Painel no ar: http://localhost:{args.porta}   (Ctrl+C para parar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPainel encerrado.")


if __name__ == "__main__":
    main()
