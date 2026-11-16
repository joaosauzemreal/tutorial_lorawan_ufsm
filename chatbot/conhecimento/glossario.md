# Glossário de LoRaWAN e do tutorial

Definições curtas dos termos que aparecem no tutorial. Cada termo tem mais detalhes nas outras seções da documentação.

## OTAA (Over-The-Air Activation)

OTAA é a ativação pelo ar, a forma de entrar na rede usada no tutorial. A placa envia um **Join Request** com o DevEUI e o JoinEUI, assinado com a AppKey; a rede responde com um **Join Accept**, e os dois lados geram chaves de sessão novas (NwkSKey e AppSKey).

## ABP (Activation By Personalization)

ABP é a ativação sem join: o endereço (DevAddr) e as chaves de sessão ficam gravados fixos no dispositivo. É mais simples, mas menos segura que o OTAA. O tutorial não usa ABP.

## Gateway

O gateway é o equipamento com antena que recebe o rádio LoRa das placas e repassa os pacotes pela internet ao servidor de rede da TTN. O gateway não consegue ler o conteúdo das mensagens, porque os dados vão criptografados até o servidor. Na UFSM, o gateway fica no prédio do CT.

## Antena

A antena é a peça que transmite e recebe o sinal de rádio LoRa da placa Heltec WiFi LoRa 32 V3. Ela deve estar sempre conectada: **nunca ligue a placa sem a antena**, porque isso pode danificar o rádio SX1262. Conecte a antena antes do cabo USB e desligue a placa antes de retirá-la. Uma antena mal conectada ou mal posicionada também reduz o alcance até o gateway.

## Join

Join é o processo de entrada da placa na rede LoRaWAN pelo OTAA. Enquanto tenta, o display mostra "ENVIANDO JOIN"; quando a rede aceita, mostra "JOIN SUCESSO".

## Payload

Payload são os dados úteis da mensagem. No tutorial, a placa envia 2 bytes com a temperatura do processador multiplicada por 100, o byte mais significativo primeiro.

## Payload formatter (decodificador de payload)

O Payload formatter é a função em JavaScript, configurada na TTN, que converte os bytes recebidos em valores legíveis. No tutorial, a função `decodeUplink` transforma os 2 bytes no campo `cpu_temperature`.

## RSSI

RSSI (Received Signal Strength Indicator) é a potência do sinal recebido, em dBm, mostrada no Live data da TTN. Quanto mais perto de zero, mais forte: -60 dBm é forte; perto de -120 dBm é fraco.

## SNR

SNR (Signal-to-Noise Ratio) é a relação entre o sinal e o ruído, em dB, mostrada no Live data da TTN. Valores positivos são bons; quanto mais negativo, mais perto de perder a mensagem.

## AU915 (plano de frequência)

AU915 é o plano de frequência LoRaWAN de 915 a 928 MHz, o indicado para o Brasil. Na UFSM se usa `Australia 915-928 MHz, FSB 2`, ou seja, a sub-banda 2 (canais 8 a 15).

## Frequência

A frequência é a faixa de rádio em que a placa transmite. No tutorial, o plano de frequência é `Australia 915-928 MHz, FSB 2` (AU915, sub-banda 2), escolhido no cadastro do dispositivo na TTN e como `REGION_AU915` na Arduino IDE.

## Live data

Live data é a aba do console da TTN que mostra em tempo real o que a rede recebe da placa e envia para ela: join requests, uplinks, downlinks, RSSI e SNR. É a principal ferramenta para diagnosticar problemas.

## Uso justo da TTN (fair use)

A política de uso justo (Fair Use Policy) da TTN limita cada dispositivo a **30 segundos de airtime de uplink por dia** e **10 downlinks por dia**. Por isso, envie mensagens pequenas, com intervalos de vários minutos, e prefira mensagens não confirmadas.

## TTN (The Things Network)

A The Things Network é uma rede LoRaWAN pública e comunitária, em que qualquer pessoa pode cadastrar dispositivos gratuitamente. No tutorial, a aplicação é criada no cluster **eu1**, onde estão os gateways da UFSM.

## Classe A

Classe A é a classe de dispositivo LoRaWAN usada no tutorial e a que mais economiza energia: depois de cada uplink, a placa abre duas janelas curtas de recepção (RX1 e RX2).

## ACK

ACK é a confirmação de recebimento que a rede envia quando a mensagem é confirmada. Cada ACK conta como downlink no limite de uso justo da TTN.

## Uplink e downlink

Uplink é a mensagem que vai da placa para a rede (no tutorial, a temperatura). Downlink é a mensagem que vai da rede para a placa, como o ACK.

## Airtime

Airtime é o tempo que uma mensagem ocupa no ar. Ele aumenta com o tamanho da mensagem e com o spreading factor, e a TTN limita a 30 segundos de airtime de uplink por dia.

## ISM e LPWAN

ISM são as faixas de frequência de uso livre, sem licença, como a de 915 MHz usada pelo LoRa no Brasil. LPWAN (*Low Power Wide Area Network*) são as redes de longo alcance e baixo consumo, como o LoRaWAN.
