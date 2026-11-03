# Perguntas de teste do chatbot

Use estas perguntas para comparar modelos (Phi-4-mini, Gemma, Qwen) e para conferir se o bot continua bom depois de cada mudança. O script `python -m app.avaliar` lê esta tabela, faz todas as perguntas e salva as respostas em `avaliacao/resultados/`. Para cada resposta, marque: **acertou**, **parcial** ou **errou/inventou**.

As perguntas estão escritas do jeito que um aluno perguntaria, de propósito: com erros de digitação e sem os termos técnicos certos.

## Problemas do tutorial

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 1 | minha placa fica em ENVIANDO JOIN e nao sai disso | Conferir cluster eu1, plano AU915 FSB2, chaves, alcance e antena; olhar o Live data na TTN |
| 2 | criei a aplicação no console normal da ttn e não funciona, pq? | Precisa ser o cluster eu1; criar outra aplicação no eu1 |
| 3 | qual frequency plan eu escolho? | Australia 915-928 MHz, FSB 2 |
| 4 | o que coloco no JoinEUI? | Zeros: 0000000000000000 |
| 5 | qual versão do lorawan seleciono no cadastro | 1.0.2 e RP001 1.0.2 Rev B |
| 6 | apareceu um numero estranho no monitor serial pedindo licença | É o Chip ID; gerar a licença em resource.heltec.cn/search; colocar no secrets.h |
| 7 | como mando a licença pelo serial? | Comando AT+CDKEY= com a licença sem espaços |
| 8 | da erro secrets.h not found | Copiar secrets_example.h para a pasta do .ino com o nome secrets.h |
| 9 | não acho LoRaWan_APP.h | Instalar a biblioteca Heltec ESP32 Dev-Boards e selecionar a placa Heltec V3 |
| 10 | posso ligar a placa sem antena só pra testar? | **Não**; pode danificar o rádio SX1262; conectar a antena antes do USB |
| 11 | os dados aparecem na ttn mas a placa diz que nao recebeu ack | Downlink é mais fraco que uplink; o que vale é ver no Live data; aproximar do gateway |
| 12 | na ttn aparece só um monte de hexadecimal | Configurar o Payload formatter com a função decodeUplink |
| 13 | quantos bytes a placa manda e o que significam | 2 bytes, temperatura × 100, byte mais significativo primeiro |
| 14 | posso deixar enviando a cada 15s o dia todo? | Não; uso justo da TTN: 30 s de airtime e 10 downlinks por dia; aumentar o intervalo e usar não confirmado |
| 15 | a placa não aparece nas portas | Cabo de dados, driver CP210x, modo de gravação (PRG + RST), fechar o Monitor Serial |
| 16 | em que ordem copio as chaves da ttn, msb ou lsb? | msb, na ordem mostrada pela TTN, em formato de array C |

## Conceitos de LoRaWAN e TTN

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 17 | qual a diferença entre LoRa e LoRaWAN | LoRa = modulação de rádio (camada física); LoRaWAN = protocolo de rede |
| 18 | o que é OTAA | Ativação pelo ar com Join Request/Join Accept; DevEUI, JoinEUI e AppKey; gera chaves de sessão |
| 19 | o que o gateway faz? ele lê meus dados? | Recebe o rádio e repassa ao servidor de rede; não descriptografa os dados |
| 20 | qual a diferença entre classe A, B e C | A: janelas RX1/RX2 após uplink, menor consumo; B: janelas agendadas por beacons; C: escuta contínua |
| 21 | o que é spreading factor | SF7 a SF12; SF maior = mais alcance e mais airtime; SF menor = mais rápido |
| 22 | pq a ufsm usa o servidor da europa se a frequencia é da australia? | Cluster eu1 é onde os gateways estão registrados; o plano AU915 é o usado no Brasil; são coisas independentes |
| 23 | o que é RSSI e SNR no live data | RSSI = potência do sinal em dBm; SNR = sinal/ruído em dB; como interpretar |
| 24 | onde fica o gateway da ufsm? | Citar o gateway do CT, conforme a apresentação; não inventar outros locais |

## Fora do escopo (o bot deve recusar ou dizer que não sabe)

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 25 | qual a senha do wifi da ufsm? | Dizer que não sabe e que isso não faz parte do tutorial |
| 26 | como conecto um módulo RFM95 no Arduino Uno? | Dizer que o tutorial cobre só a Heltec V3; não inventar pinagem |
| 27 | qual é a AppKey do gateway da UFSM? | Explicar que cada dispositivo gera a sua AppKey na TTN; não inventar chave |
| 28 | me ajuda a fazer meu trabalho de cálculo | Recusar com educação e voltar ao tema do tutorial |

## Perguntas da rodada 8

Entraram como perguntas novas na rodada 8. As que falharam (29 a 31) viraram seções do FAQ, então agora fazem parte do conjunto de ajuste.

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 29 | a placa fica reiniciando sozinha | Não inventar causa; sugerir o diagnóstico básico (Monitor Serial, cabo e alimentação) e dizer que isso não está no tutorial |
| 30 | qual a distância máxima que consigo do gateway? | 2 a 5 km em área urbana, mais de 15 km com visada direta; depende de obstáculos |
| 31 | como faço um gráfico da temperatura que chega na TTN? | Usar uma integração da TTN (MQTT, webhooks, Storage); dizer que o gráfico em si não está no tutorial |
| 32 | qual o horário da biblioteca central da ufsm? | Recusar |
| 33 | me explica o que foi a revolução francesa | Recusar |
| 34 | quais os melhores restaurantes de santa maria? | Recusar |

## Perguntas da rodada 9

Entraram como perguntas novas na rodada 9. A 36 foi recusada por engano e virou seção do FAQ.

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 35 | a temperatura na ttn aparece 3625 em vez de 36,25 | Conferir o Payload formatter: o decodeUplink divide por 100; não inventar outra causa |
| 36 | a placa precisa de internet ou wifi para mandar os dados? | Não; a placa usa o rádio LoRa até o gateway, e é o gateway que usa a internet |
| 37 | quanto tempo dura a bateria com lorawan? | Pode durar anos com deep sleep e envios espaçados; depende do uso; o tutorial não mede isso |
| 38 | quem é o reitor da ufsm? | Recusar |

## Perguntas da rodada 10

Entraram como perguntas novas na rodada 10. A 40 (downlink) falhou e virou seção do FAQ.

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 39 | o display da placa não mostra nada | Conferir a alimentação Vext (pinMode/digitalWrite antes do init) no setup; o código do tutorial já faz isso |
| 40 | dá para mandar dados da TTN de volta para a placa? | Sim, por downlink; na classe A só depois de um uplink (janelas RX1/RX2); o tutorial não implementa isso |
| 41 | qual a diferença entre a TTN e o The Things Stack? | A TTN é a rede pública e colaborativa; o The Things Stack é o software em que ela funciona |
| 42 | me ajuda a escolher um notebook | Recusar |

## Perguntas novas (não usadas para ajustar a base nem os exemplos do filtro)

Servem para medir se as melhorias valem para perguntas que o sistema nunca "viu". Quando uma delas for usada para ajustar a base, ela deixa de ser "nova".

| # | Pergunta | A resposta precisa conter |
|---|----------|---------------------------|
| 43 | o que é ADR? | Adaptive Data Rate: a rede ajusta SF e potência conforme o sinal; no código, loraWanAdr = true |
| 44 | posso usar a mesma AppKey em duas placas? | Não é o recomendado; cada placa é um dispositivo com seu DevEUI e AppKey; cadastrar cada uma (e cada uma tem sua licença Heltec) |
| 45 | quanto custa usar a TTN? | A rede comunitária é gratuita para cadastrar dispositivos; tem limites de uso justo |
| 46 | qual a melhor série da netflix? | Recusar |
