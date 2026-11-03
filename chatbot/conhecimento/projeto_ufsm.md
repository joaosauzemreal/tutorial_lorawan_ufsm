# Sobre o projeto e a rede LoRaWAN da UFSM

## O que é este projeto

Este é um projeto de extensão da disciplina **Projeto Integrador IV** da Universidade Federal de Santa Maria (UFSM). Ele ensina, passo a passo, a conectar um nó sensor (a placa **Heltec WiFi LoRa 32 V3**) à rede **LoRaWAN** do campus, que usa a **The Things Network (TTN)**.

O material do projeto tem três partes:
- **Tutorial escrito e código-fonte:** https://github.com/joaosauzemreal/tutorial_lorawan_ufsm
- **Apresentação teórica** sobre LoRa, LoRaWAN e a infraestrutura da UFSM: https://joaosauzemreal.github.io/tutorial_lorawan_ufsm/
- **Vídeo tutorial prático:** https://www.youtube.com/watch?v=S4UdSOCp6O0

## Configuração da rede LoRaWAN da UFSM (resumo)

- **Cluster da TTN:** Europa (**eu1**), console em https://eu1.cloud.thethings.network/console
- **Plano de frequência:** Australia 915-928 MHz, **FSB 2** (AU915, sub-banda 2: canais 8 a 15, de 916,8 a 918,2 MHz)
- **Versão LoRaWAN:** 1.0.2, parâmetros regionais RP001 1.0.2 Rev B
- **Ativação:** OTAA, com JoinEUI (AppEUI) zerado (`0000000000000000`)
- **Classe do dispositivo:** A
- **Placa usada no tutorial:** Heltec WiFi LoRa 32 V3 (ESP32-S3 + rádio SX1262 + display OLED 0,96")

## Como a rede do campus está organizada

1. **Dispositivo IoT (nó sensor):** a placa Heltec coleta o dado (no tutorial, a temperatura interna do processador) e o envia criptografado por rádio.
2. **Sinal de rádio:** frequência AU915, sub-banda 2, na faixa ISM, que não exige licença.
3. **Gateway do campus:** antena que recebe o sinal de rádio e repassa os pacotes pela internet. A apresentação do projeto cita o gateway do CT (Centro de Tecnologia) da UFSM.
4. **Servidor de rede (TTN, cluster eu1):** recebe os pacotes, confere a segurança e entrega os dados para a aplicação do usuário no console da TTN.

## Onde fica o gateway LoRaWAN da UFSM

Segundo a apresentação deste projeto, um gateway LoRaWAN da UFSM fica no **CT (Centro de Tecnologia)** da universidade. O gateway é uma antena que recebe o sinal de rádio das placas e repassa as mensagens para a TTN, no cluster eu1.

Para conseguir conectar, aproxime-se do CT, de preferência com visada direta para o prédio. A localização exata de outros gateways do campus não faz parte deste tutorial.

## O que este assistente sabe responder

O assistente responde dúvidas sobre este tutorial e sobre o funcionamento de LoRa, LoRaWAN e da The Things Network: conceitos, cadastro na TTN, configuração da Arduino IDE e da placa Heltec V3, licença da Heltec, o código de exemplo e erros comuns. Ele não substitui a documentação oficial da TTN e da Heltec, e não responde assuntos fora desses temas.
