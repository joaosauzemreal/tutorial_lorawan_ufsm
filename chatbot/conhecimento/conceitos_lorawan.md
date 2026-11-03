# Conceitos de LoRa, LoRaWAN e The Things Network

Explicações gerais sobre como funciona uma rede LoRaWAN, para quem está começando.

## O que é LoRa

**LoRa** (de *Long Range*, longo alcance) é uma técnica de modulação de rádio, ou seja, a forma como os bits viram ondas de rádio. Ela é a **camada física** da comunicação. LoRa usa a modulação **CSS (Chirp Spread Spectrum)**: o sinal varia de frequência ao longo do tempo (os *chirps*). Isso dá ao LoRa uma resistência muito alta a ruído e permite receber sinais muito fracos, até abaixo do nível de ruído.

O resultado é **longo alcance** (de 2 a 5 km em área urbana e mais de 15 km com visada direta no campo) e **baixo consumo de energia**, em troca de uma **taxa de dados baixa**. LoRa serve para mandar mensagens pequenas de vez em quando, como a leitura de um sensor. Não serve para vídeo, áudio ou arquivos.

## O que é LoRaWAN

**LoRaWAN** é o **protocolo de rede** que funciona sobre o LoRa, mantido pela LoRa Alliance. Enquanto o LoRa define como o sinal de rádio é transmitido, o LoRaWAN define:
- como os dispositivos entram na rede (ativação);
- como as mensagens são endereçadas, autenticadas e criptografadas;
- quando o dispositivo pode receber mensagens (classes A, B e C);
- como a rede ajusta a taxa de dados de cada dispositivo (ADR).

Resumo: **LoRa é o rádio; LoRaWAN é a rede.** É possível usar LoRa sem LoRaWAN (comunicação direta entre dois rádios), mas aí não existem gateways, servidor de rede nem a segurança do LoRaWAN.

## Os três pilares do LoRaWAN

1. **Longo alcance:** poucos gateways cobrem um campus inteiro.
2. **Baixo consumo:** o dispositivo transmite pacotes pequenos e passa a maior parte do tempo em repouso profundo (*deep sleep*). Com bateria, pode durar anos.
3. **Sem licença:** usa faixas de frequência ISM, abertas. Não há mensalidade, chip de operadora nem licença da Anatel para o usuário.

## Arquitetura de uma rede LoRaWAN: dispositivo, gateway, servidor de rede e aplicação

Uma rede LoRaWAN tem quatro partes, numa topologia em estrela:

1. **Dispositivo final (end device ou nó sensor):** a placa com o sensor e o rádio LoRa, por exemplo a Heltec WiFi LoRa 32 V3. Ela envia mensagens por rádio.
2. **Gateway:** recebe por rádio as mensagens de todos os dispositivos ao alcance e as repassa pela internet para o servidor de rede. O gateway não interpreta, não descriptografa e não verifica as mensagens; ele só repassa. Quem confere se a mensagem é autêntica é o servidor de rede. O dispositivo não se conecta a um gateway específico: qualquer gateway que ouvir a mensagem a encaminha, e vários gateways podem receber a mesma mensagem.
3. **Servidor de rede (Network Server):** recebe os pacotes vindos dos gateways, descarta as cópias repetidas, confere a autenticidade das mensagens, controla o ADR e escolhe por qual gateway responder.
4. **Servidor de aplicação (Application Server):** descriptografa os dados e os entrega à aplicação do usuário, por exemplo no console da TTN, por MQTT ou por webhooks.

Na UFSM, o caminho é: placa Heltec → rádio AU915 FSB2 → gateway do campus → TTN (cluster eu1) → aplicação do usuário no console.

## Uplink e downlink

- **Uplink:** mensagem do dispositivo para a rede (por exemplo, a leitura de temperatura). É o uso principal.
- **Downlink:** mensagem da rede para o dispositivo (por exemplo, um comando, um ajuste de configuração ou a confirmação ACK).

O downlink costuma ser mais difícil de receber que o uplink, porque o dispositivo tem antena e sensibilidade mais limitadas e porque os gateways têm pouco tempo de transmissão disponível. Por isso pode acontecer de a mensagem chegar na TTN e a placa não receber o ACK.

## Mensagens confirmadas e não confirmadas (ACK)

- **Não confirmada:** o dispositivo envia e não espera resposta. Gasta menos energia e menos recursos da rede. É o recomendado para a maioria dos sensores.
- **Confirmada:** o dispositivo pede uma confirmação (ACK), que chega como um downlink. Se o ACK não chegar, o dispositivo tenta de novo. No código do tutorial, `isTxConfirmed = true` e `confirmedNbTrials = 4`.

Na TTN, cada ACK conta no limite de 10 downlinks por dia por dispositivo. Use mensagens confirmadas só quando for realmente necessário.

## Classes de dispositivos LoRaWAN: A, B e C

- **Classe A (padrão, a usada no tutorial):** o dispositivo dorme quase o tempo todo. Depois de cada uplink, abre duas janelas curtas de recepção (**RX1** e **RX2**). A rede só consegue mandar um downlink nessas janelas. É a classe que mais economiza bateria.
- **Classe B:** além das janelas da classe A, abre janelas de recepção em horários agendados, sincronizadas por sinais periódicos (*beacons*) dos gateways. Permite receber comandos sem esperar um uplink.
- **Classe C:** o rádio fica ouvindo o tempo todo, exceto quando está transmitindo. Recebe comandos quase na hora, mas consome muita energia; normalmente exige alimentação na tomada.

Todo dispositivo LoRaWAN precisa suportar a classe A.

## Ativação OTAA e ABP

Para entrar na rede, o dispositivo precisa ser ativado. Há duas formas:

**OTAA (Over-The-Air Activation), a usada no tutorial e a recomendada:**
1. O dispositivo envia uma mensagem **Join Request** com o seu DevEUI e o JoinEUI, assinada com a AppKey.
2. O servidor de rede confere e responde com um **Join Accept**.
3. Os dois lados calculam **chaves de sessão novas** (NwkSKey e AppSKey) e o dispositivo recebe um endereço na rede (**DevAddr**).

A cada novo join são geradas chaves novas, o que deixa a rede mais segura.

**ABP (Activation By Personalization):** o DevAddr e as chaves de sessão são gravados fixos no dispositivo, sem join. É mais simples, mas menos seguro, e causa problemas quando o contador de mensagens reinicia. O tutorial não usa ABP; os campos `nwkSKey`, `appSKey` e `devAddr` do código ficam zerados.

## Chaves e identificadores: DevEUI, JoinEUI (AppEUI), AppKey, NwkSKey, AppSKey, DevAddr

- **DevEUI:** identificador único do dispositivo, com 8 bytes. A TTN pode gerar um.
- **JoinEUI (antigo AppEUI):** identificador do servidor de join, com 8 bytes. No tutorial da UFSM é zerado (`0000000000000000`).
- **AppKey:** chave secreta raiz, com 16 bytes, usada no join OTAA. Nunca deve ser publicada; por isso fica no arquivo `secrets.h`, que é ignorado pelo Git.
- **NwkSKey (chave de sessão de rede):** gerada no join. Garante a integridade das mensagens entre o dispositivo e o servidor de rede.
- **AppSKey (chave de sessão de aplicação):** gerada no join. Criptografa os dados úteis (payload) de ponta a ponta, do dispositivo até o servidor de aplicação.
- **DevAddr:** endereço curto, com 4 bytes, que o dispositivo recebe ao entrar na rede.

O LoRaWAN usa criptografia **AES-128** em duas camadas (rede e aplicação). Nem o gateway nem o servidor de rede conseguem ler os dados da aplicação.

## Spreading Factor (SF), Data Rate (DR), airtime e ADR

O **Spreading Factor (SF)** é um ajuste do rádio LoRa que vai de **SF7 a SF12**. Resumo: **SF maior = mais alcance, porém mais tempo no ar e mais consumo de bateria; SF menor = menos alcance, porém transmissão mais rápida e econômica.**

O SF define quanto tempo cada símbolo de rádio dura:
- **SF menor (SF7):** transmissão mais rápida, menos tempo no ar (airtime) e menos consumo, mas alcance menor.
- **SF maior (SF12):** alcance e sensibilidade maiores, mas a mensagem fica muito mais tempo no ar e gasta mais bateria. Cada SF a mais praticamente dobra o tempo no ar.

O **Data Rate (DR)** é o número que o LoRaWAN usa para combinar SF e largura de banda. Na região **AU915**, para uplink:
- DR0 = SF12, 125 kHz
- DR1 = SF11, 125 kHz
- DR2 = SF10, 125 kHz
- DR3 = SF9, 125 kHz
- DR4 = SF8, 125 kHz
- DR5 = SF7, 125 kHz
- DR6 = SF8, 500 kHz

**Airtime** é o tempo que uma mensagem ocupa o canal de rádio. Depende do SF e do tamanho da mensagem. Ele importa por causa da bateria e dos limites de uso da rede (na TTN, 30 segundos por dia por dispositivo).

**ADR (Adaptive Data Rate):** com o ADR ativado, o servidor de rede observa a qualidade do sinal do dispositivo e manda ele usar o menor SF e a menor potência que ainda funcionam. Funciona melhor com dispositivos parados. No código do tutorial, `loraWanAdr = true`.

## Planos de frequência: AU915 e a sub-banda 2 (FSB2)

Na rede da UFSM, o plano de frequência escolhido no cadastro da TTN é **`Australia 915-928 MHz, FSB 2`**.

Cada região do mundo usa uma faixa de frequência para LoRaWAN. No Brasil, a LoRa Alliance indica o plano **AU915-928**, o mesmo da Austrália. Por isso o nome do plano começa com "Australia", e "FSB 2" indica a sub-banda usada pelos gateways da UFSM.

O plano AU915 tem 64 canais de uplink de 125 kHz (canais 0 a 63, de 915,2 MHz em diante, a cada 200 kHz) e mais 8 canais de 500 kHz (canais 64 a 71). Um gateway comum escuta só 8 canais de 125 kHz por vez, então os canais são divididos em **sub-bandas** (FSB, *Frequency Sub-Band*) de 8 canais.

A rede da UFSM usa a **sub-banda 2 (FSB2)**: canais 8 a 15, de **916,8 a 918,2 MHz**, mais o canal 65 (500 kHz). O dispositivo precisa transmitir nessa mesma sub-banda; senão, o gateway não ouve. No código, isso é feito pela máscara `userChannelsMask[0] = 0xFF00`, que liga os canais 8 a 15.

## O que é a The Things Network (TTN)

A **The Things Network (TTN)** é uma rede LoRaWAN pública e colaborativa, usada no mundo todo. Pessoas e instituições instalam gateways e os registram na TTN, e qualquer pessoa pode cadastrar dispositivos gratuitamente e usar esses gateways. A TTN funciona sobre o software **The Things Stack**, da empresa The Things Industries.

Na TTN:
- **Aplicação (Application):** agrupa dispositivos e define o que fazer com os dados (decodificador de payload, integrações).
- **Dispositivo (End device):** cada placa cadastrada, com suas chaves.
- **Live data:** aba que mostra em tempo real o que a rede recebe e envia: join requests, uplinks, downlinks, RSSI e SNR. É a principal ferramenta de diagnóstico.
- **Payload formatter:** função em JavaScript que converte os bytes recebidos em valores legíveis (por exemplo, `cpu_temperature`).
- **Integrações:** formas de levar os dados para fora da TTN, como MQTT, webhooks (HTTP) e o armazenamento de dados (Storage Integration).

## Clusters da TTN: por que usar o eu1 na UFSM

Cluster e plano de frequência são coisas **independentes**. O cluster (**eu1**, na Europa) é o servidor da TTN onde os gateways da UFSM estão registrados, por isso a aplicação precisa ser criada nele. O plano de frequência (**AU915**) é a faixa de rádio que os dispositivos usam, e é o plano indicado para o Brasil. Um não depende do outro. O cluster não é escolhido pela localização de quem usa, e sim por ser o cluster em que os gateways da UFSM foram registrados.

A TTN é dividida em **clusters** regionais, cada um com o seu endereço de console: por exemplo **eu1** (Europa), **nam1** (América do Norte) e **au1** (Austrália). Cada gateway é registrado em um cluster. Os gateways da UFSM estão registrados no cluster **eu1**, então a aplicação e o dispositivo também devem ser criados no eu1 (`https://eu1.cloud.thethings.network/console`). O nome do cluster não tem relação com o plano de frequência: na UFSM se usa o cluster europeu com o plano de frequência AU915.

## Política de uso justo da TTN (Fair Use Policy)

A rede pública da TTN é compartilhada, então cada dispositivo deve respeitar:
- no máximo **30 segundos de airtime de uplink por dia**;
- no máximo **10 downlinks por dia**, contando os ACKs de mensagens confirmadas.

Na prática: envie mensagens pequenas, com intervalos de vários minutos, prefira mensagens não confirmadas e use SF baixo (o ADR ajuda nisso).

## RSSI e SNR: como ler a qualidade do sinal

Na aba Live data da TTN, cada mensagem recebida mostra:
- **RSSI (Received Signal Strength Indicator):** potência do sinal recebido, em dBm. Quanto mais perto de zero, mais forte. Algo como -60 dBm é um sinal forte; perto de -120 dBm é fraco, no limite.
- **SNR (Signal-to-Noise Ratio):** relação entre sinal e ruído, em dB. Valores positivos são bons. O LoRa consegue receber mesmo com SNR negativo (até cerca de -7,5 dB em SF7 e -20 dB em SF12), mas, quanto mais negativo, mais perto de perder a mensagem.

Se o RSSI estiver muito baixo ou o SNR muito negativo, aproxime-se do gateway, melhore a posição da antena ou deixe o ADR usar um SF maior.

## Glossário rápido

- **ACK:** confirmação de recebimento enviada pela rede.
- **ADR:** ajuste automático da taxa de dados.
- **Airtime:** tempo que uma mensagem ocupa no ar.
- **Gateway:** antena que recebe o rádio LoRa e repassa os pacotes pela internet.
- **ISM:** faixas de frequência de uso livre, sem licença.
- **Join:** processo de entrada do dispositivo na rede (OTAA).
- **LPWAN:** redes de longo alcance e baixo consumo (*Low Power Wide Area Network*), como o LoRaWAN.
- **Payload:** os dados úteis da mensagem (no tutorial, 2 bytes com a temperatura).
- **Uplink / downlink:** dispositivo para a rede / rede para o dispositivo.
