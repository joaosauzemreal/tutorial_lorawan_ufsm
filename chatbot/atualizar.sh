#!/usr/bin/env bash
# Atualiza o assistente com a versão do GitHub e reinicia o serviço.
# Uso (no servidor):  ~/tutorial_lorawan_ufsm/chatbot/atualizar.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

echo ">>> Baixando a versão mais recente do GitHub..."
git pull --ff-only

echo ">>> Conferindo dependências do Python..."
.venv/bin/pip install -q -r requirements.txt

echo ">>> Reiniciando o assistente (pode pedir a sua senha)..."
sudo systemctl restart assistente-lorawan

echo ">>> Aguardando o assistente ficar pronto..."
for _ in $(seq 1 60); do
  status=$(curl -s http://localhost:8000/api/status || true)
  if echo "$status" | grep -q '"situacao":"pronto"'; then
    echo ">>> Pronto: $status"
    exit 0
  fi
  sleep 2
done
echo ">>> O assistente ainda não ficou pronto. Veja: journalctl -u assistente-lorawan -n 50"
exit 1
