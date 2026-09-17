# 📡 Guia de Conectividade LoRaWAN na UFSM — Heltec WiFi LoRa 32 V3

Este repositório contém a documentação completa, o passo a passo de configuração e o código-fonte de referência para conectar o nó sensor **Heltec WiFi LoRa 32 V3** à infraestrutura de rede **LoRaWAN / The Things Network (TTN)** na **Universidade Federal de Santa Maria (UFSM)**.

---

## 📌 Conceitos Fundamentais

* **LoRa e LoRaWAN:** **LoRa** (Long Range) é a tecnologia de modulação por rádio de baixo consumo e longo alcance (camada física). **LoRaWAN** é o protocolo de rede (camada de enlace e rede) que gerencia a segurança, o endereçamento dos nós sensores, a confirmação de pacotes e a comunicação bidirecional com os Gateways.
* **Heltec WiFi LoRa 32 V3:** Placa de desenvolvimento baseada no microcontrolador **ESP32-S3** integrada ao rádio **SX1262** e a um display **OLED 0.96"**. Excelente desempenho computacional e suporte para comunicação LPWAN.
* **The Things Network (TTN):** Ecossistema de rede LoRaWAN global, aberto e colaborativo. A TTN recebe os pacotes de rádio captados pelos gateways no campus e os direciona para aplicações em nuvem.

---

## 🛠️ Passo a Passo: Configuração no Painel da TTN

> ⚠️ **ATENÇÃO CRÍTICA — CLUSTER EUROPEU (eu1):**
> Os gateways LoRaWAN instalados no campus da UFSM estão apontados para o servidor da Europa (**`eu1.cloud.thethings.network`**). Portanto, a sua aplicação e o seu dispositivo no console da TTN **DEVEM** obrigatoriamente ser criados na região **Europe (eu1)**, do contrário os gateways da universidade não retransmitirão os seus pacotes.

### 1. Criar Aplicação na TTN
1. Acesse o console da TTN na região Europeia: [https://eu1.cloud.thethings.network/console](https://eu1.cloud.thethings.network/console).
2. Faça login e selecione **Applications** > **+ Create application**.
3. Preencha o **Application ID** (ex: `ufsm-heltec-v3-telemetria`) e confirme.

### 2. Cadastrar Dispositivo (End Device)
1. Dentro da sua aplicação, clique em **+ Register end device**.
2. Selecione a opção **Enter end device specifics manually**.
3. **Frequency plan:** Selecione `Australia 915-928 MHz, FSB 2` (Utilizado no Brasil e na UFSM).
4. **LoRaWAN version:** Selecione `LoRaWAN Specification 1.0.2` (Padrão das bibliotecas Heltec).
5. **Regional Parameters version:** Selecione `RP001 Regional Parameters 1.0.2 Rev B`.

### 3. Configurar Credenciais OTAA (EUIs e AppKey)
1. **JoinEUI (AppEUI):** Configure com zeros (`0000000000000000`).
2. **DevEUI:** Clique em **Generate** para criar uma chave única global ou insira o identificador físico do seu chip.
3. **AppKey:** Clique em **Generate** para criar a chave secreta de criptografia.
4. Clique em **Register end device**.

---
# 📦 Biblioteca e Suporte Oficial Heltec para Arduino IDE

A [biblioteca oficial da Heltec](https://github.com/HelTecAutomation/Heltec_ESP32) instala os recursos necessários para o gerenciamento de licença, suporte ao rádio LoRa/LoRaWAN e controle dos periféricos do dispositivo.

---

### 🛠️ Passo a Passo de Instalação na Arduino IDE

1. Abra a **Arduino IDE**.
2. Na barra lateral esquerda, acesse a aba **Gerenciador de Bibliotecas** (ícone de livros ou atalho `Ctrl + Shift + I` / `Cmd + Shift + I`).
3. Na caixa de pesquisa, digite **`heltec esp32`**.
4. Localize a biblioteca **`Heltec ESP32 Dev-Boards`** desenvolvida por **Heltec Automation** e clique em **Instalar**.

---

### ⚙️ Seleção da Placa e Parâmetros de Compilação

Após a instalação, configure a IDE com as seguintes opções no menu **Ferramentas (Tools)**:

* **Placa:** `Heltec ESP32 Series Arduino` > `Heltec WiFi LoRa 32(V3)`
* **LoRaWAN Region:** `REGION_AU915`
* **LoRaWAN Debug Level:** `FREQ_AND_DIO` *(Exibe detalhes de frequência e transmissão na Serial)*
* **Upload Speed:** `115200` ou o que for de sua preferência
---
## 🔑 Ativação de Licença da Placa Heltec V3

Para utilizar a biblioteca oficial de LoRaWAN da Heltec, o microcontrolador necessita de uma **licença vinculada ao seu Chip ID**.

### O que é e por que é necessária?
A licença é uma chave de 32 bits gerada através do Chip ID único do ESP32-S3. Caso a memória flash da placa seja totalmente apagada ou o firmware travado na inicialização exibindo o Chip ID na porta serial, a licença precisa ser reinjetada.

### Como Obter a Licença Gratuita:
1. Abra o Monitor Serial na velocidade **115200 baud** e grave qualquer código básico na placa para identificar o **Chip ID de 12 dígitos** impresso na inicialização.
2. Acesse o site oficial de validação da Heltec: [https://resource.heltec.cn/search](https://resource.heltec.cn/search).
3. Cole o seu **Chip ID** de 12 dígitos na caixa de busca e clique em **Confirm**.
4. Copie a licença de 32 bits gerada (exemplo: `0x4819D3A6, 0x3C4015EF, 0xC76E3CE5, 0x9742010D`).
   <img width="709" height="416" alt="image" src="https://github.com/user-attachments/assets/ee225285-d21e-4dcc-8ada-d0d1257a7ae3" />


### Formas de Injetar a Licença:
* **Via Código C++ (Recomendado):** Declare no array `uint32_t license[4]` no seu código e passe na função `Mcu.setlicense(license, HELTEC_BOARD);` no `setup()`.
* **Via Comando AT (Serial):** Com o código carregado e a serial aberta, envie o comando AT+CDKEY=(LICENÇA):
  ```text
  AT+CDKEY=4819D3A63C4015EFC76E3CE59742010D
