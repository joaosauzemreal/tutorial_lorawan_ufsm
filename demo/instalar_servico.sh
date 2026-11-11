#!/usr/bin/env bash
# Instala (ou atualiza) o painel de visitantes como serviço no servidor.
# Depois disso o painel liga sozinho junto com o servidor, na porta 8001.
#
# Uso (no servidor):  ~/tutorial_lorawan_ufsm/demo/instalar_servico.sh
# Rodar de novo depois de um "git pull" aplica as mudanças e reinicia o painel.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
PASTA="$(pwd)"
USUARIO="$(id -un)"

echo ">>> Preparando o Python (pasta .venv)..."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade paho-mqtt

if [ ! -f .env ]; then
  cp .env.example .env
  sed -i 's/^SIMULAR=0/SIMULAR=1/' .env
  echo ">>> Criei o .env em MODO DE ENSAIO (visitantes simulados)."
  echo "    Para usar a placa de verdade: preencha TTN_APP_ID e TTN_API_KEY no .env,"
  echo "    troque SIMULAR=1 por SIMULAR=0 e rode: sudo systemctl restart painel-visitantes"
fi

echo ">>> Instalando o serviço (pode pedir a sua senha)..."
sudo tee /etc/systemd/system/painel-visitantes.service > /dev/null <<EOF
[Unit]
Description=Painel do contador de visitantes LoRaWAN
After=network-online.target
Wants=network-online.target

[Service]
User=${USUARIO}
WorkingDirectory=${PASTA}
ExecStart=${PASTA}/.venv/bin/python -u servidor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable -q painel-visitantes
sudo systemctl restart painel-visitantes

echo ">>> Conferindo..."
for _ in $(seq 1 10); do
  if estado=$(curl -fs http://localhost:8001/api/estado); then
    echo ">>> Painel no ar: http://$(hostname -I | awk '{print $1}'):8001"
    command -v tailscale > /dev/null && echo "    Pelo Tailscale: http://$(tailscale ip -4 2>/dev/null | head -1):8001"
    echo "    Estado: ${estado:0:200}"
    exit 0
  fi
  sleep 1
done
echo ">>> O painel não respondeu. Veja o log: journalctl -u painel-visitantes -n 30"
exit 1
