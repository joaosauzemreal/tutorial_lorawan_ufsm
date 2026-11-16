# Demonstração: contador de visitantes por LoRaWAN

Demonstração para eventos (feiras, visitas de escolas): cada visitante aperta o botão da placa e o número aparece no telão segundos depois, depois de passar pelo rádio LoRa, pelo gateway da UFSM e pela The Things Network.

```
 [botão PRG] → Heltec V3 ──rádio LoRa──▶ Gateway UFSM ──internet──▶ TTN ──MQTT──▶ servidor.py ──▶ painel no navegador
                 OLED mostra o total                                                     (página do projetor)
                 LED pisca ao enviar
```

O que acontece a cada aperto:

1. **Na placa:** o contador sobe e aparece na tela OLED na hora. O total fica gravado na memória flash, então desligar a placa não perde a contagem.
2. **Pelo rádio:** a placa envia o novo total (4 bytes, porta 3). Quando o pacote sai pelo rádio, o LED branco pisca 3 vezes e a tela mostra "Enviado ao gateway!".
3. **No painel:** quando a TTN recebe o pacote, a página do projetor anima o caminho placa → gateway → TTN → tela e mostra o novo número, com a força do sinal (RSSI), o SNR e o gateway que ouviu.

O LED pisca quando o rádio termina de transmitir, ou seja, quando o pacote **saiu** da placa. A prova de que ele **chegou** é o número mudar no painel. Como o pacote leva o total (e não "+1"), um pacote perdido não estraga a contagem: o próximo corrige.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `../src/demo_visitantes/demo_visitantes.ino` | Programa da placa |
| `servidor.py` | Escuta a TTN e serve a página do painel |
| `painel.html` | A página do projetor |
| `.env.example` | Modelo das configurações (ID da aplicação e chave da TTN) |
| `formatador_ttn.js` | Opcional: decodifica a porta 3 na aba Live data da TTN |

## 1. Gravar o programa na placa

O cadastro na TTN é o mesmo do tutorial principal: não precisa criar outro dispositivo.

1. Copie o seu `secrets.h` (o mesmo que você já usa em `src/heltec_lorawan/`) para dentro de `src/demo_visitantes/`.
2. Abra `src/demo_visitantes/demo_visitantes.ino` na Arduino IDE, com as mesmas opções de placa do tutorial (região **REGION_AU915**), e carregue.
3. A tela mostra "Conectando a rede..." e, depois do join, "Conectado a TTN!". A placa envia o total atual uma vez logo depois do join.
4. Aperte o botão marcado **PRG** (o outro, **RST**, reinicia a placa): o número sobe e o LED pisca.

| Ação | Resultado |
|---|---|
| Apertar e soltar PRG | +1 visitante |
| Segurar PRG por 3 s | Zera o contador (e envia o zero para o painel) |

Ajustes no topo do `.ino`:

- `INTERVALO_MINIMO_MS` (10 s): espera mínima entre dois envios. Se vários visitantes apertarem seguido, todos contam na hora na tela da placa e o total vai no próximo pacote. A tela mostra "Envia em N s".
- `REENVIO_MS` (30 s): depois do último envio, a placa manda o mesmo total mais uma vez. Se um pacote se perdeu no ar (sinal fraco), a página se corrige sozinha. Na página, esse reenvio só atualiza os detalhes, sem a animação.
- `DATA_RATE` (5 = SF7): o pacote mais curto possível. Se os pacotes não chegarem ao gateway no local do evento, troque para 3 (SF9), que alcança mais longe e ocupa o rádio por mais tempo.
- `PINO_BOTAO`: para usar um botão externo maior (mais fácil para o público), ligue-o entre um pino livre e o GND e coloque o número do pino aqui.

Os envios são **sem confirmação (sem ACK)**: a TTN permite só 10 downlinks por dia por dispositivo, e cada ACK gasta um. Com SF7, cada pacote fica uns 50 ms no ar; o limite de uso justo da TTN (30 s de tempo no ar por dia) dá para centenas de visitantes.

## 2. Criar a chave da TTN para o painel

O painel precisa de uma chave que só **lê** os pacotes da aplicação.

1. No console da TTN (cluster `eu1`), abra a sua aplicação.
2. Vá em **API keys** → **+ Add API key**.
3. Nome: `painel-visitantes`. Em **Rights**, escolha **Grant individual rights** e marque apenas **Read application traffic (uplink and downlink)**.
4. Clique em **Create API key** e copie a chave (começa com `NNSXS.`). Ela só aparece uma vez.

## 3. Rodar o painel

Precisa de Python 3.9 ou mais novo e da biblioteca `paho-mqtt`. O computador precisa de internet (a conexão com a TTN sai pela porta 8883).

```bash
cd demo
cp .env.example .env        # no Windows: copy .env.example .env
# edite o .env: TTN_APP_ID e TTN_API_KEY
pip install paho-mqtt
python servidor.py
```

Abra **http://localhost:8001** e aperte **F11** para tela cheia. O canto superior direito mostra se o painel está ligado à TTN.

**Para testar sem placa e sem TTN:**

```bash
python servidor.py --simular
```

Visitantes inventados aparecem a cada 6–15 s, e a página avisa que está em modo de ensaio.

### Num servidor Linux, como serviço (opcional)

Se você tiver um servidor Linux (ou um computador que fica sempre ligado), o painel pode rodar nele como serviço e abrir em qualquer aparelho da mesma rede (PC, celular, tablet). Um único comando, dentro da pasta `demo/`, prepara o Python, cria o `.env` e instala o serviço, que liga sozinho junto com o servidor:

```bash
./instalar_servico.sh
```

No final, o script mostra o endereço do painel, no formato `http://IP-DO-SERVIDOR:8001`.

Na primeira vez, o `.env` é criado em **modo de ensaio** (`SIMULAR=1`). Para usar a placa de verdade:

```bash
nano .env      # preencha TTN_APP_ID e TTN_API_KEY e troque SIMULAR=1 por SIMULAR=0
sudo systemctl restart painel-visitantes
```

Comandos úteis:

| Para | Comando |
|---|---|
| Atualizar depois de um `git pull` | `./instalar_servico.sh` (dentro de `demo/`) |
| Ver se está rodando | `systemctl status painel-visitantes` |
| Ver o log (pacotes recebidos, erros da TTN) | `journalctl -u painel-visitantes -f` |
| Desligar | `sudo systemctl disable --now painel-visitantes` |
