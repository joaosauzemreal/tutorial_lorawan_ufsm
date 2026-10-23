# 📡 Guia de Conectividade LoRaWAN na UFSM — Heltec WiFi LoRa 32 V3

Este repositório contém a documentação completa, o passo a passo de configuração e o código-fonte de referência para conectar o nó sensor **Heltec WiFi LoRa 32 V3** à infraestrutura de rede **LoRaWAN / The Things Network (TTN)** na **Universidade Federal de Santa Maria (UFSM)**.

---

## 🎥 Vídeo Tutorial

Prefere acompanhar em vídeo? O passo a passo completo deste guia, da criação da aplicação na TTN até o primeiro uplink, está gravado no vídeo abaixo (clique na imagem para assistir no YouTube):

[![Assista ao vídeo tutorial no YouTube](https://img.youtube.com/vi/S4UdSOCp6O0/maxresdefault.jpg)](https://www.youtube.com/watch?v=S4UdSOCp6O0)

> 📺 O vídeo também pode ser assistido na [página do projeto no GitHub Pages](https://joaosauzemreal.github.io/tutorial_lorawan_ufsm/#video), junto com a apresentação teórica sobre LoRa, LoRaWAN e a infraestrutura da UFSM.

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
<img width="870" height="762" alt="image" src="https://github.com/user-attachments/assets/0ef71949-dee6-4a65-81ad-0cb172f54237" />


### 2. Cadastrar Dispositivo (End Device)
1. Dentro da sua aplicação, clique em **+ Register end device**.
2. Selecione a opção **Enter end device specifics manually**.
3. **Frequency plan:** Selecione `Australia 915-928 MHz, FSB 2` (Utilizado no Brasil e na UFSM).
4. **LoRaWAN version:** Selecione `LoRaWAN Specification 1.0.2` (Padrão das bibliotecas Heltec).
5. **Regional Parameters version:** Selecione `RP001 Regional Parameters 1.0.2 Rev B`.
<img width="632" height="370" alt="image" src="https://github.com/user-attachments/assets/5cb62f40-ce69-4517-b429-aeed14841de8" />


### 3. Configurar Credenciais OTAA (EUIs e AppKey)
1. **JoinEUI (AppEUI):** Configure com zeros (`0000000000000000`).
2. **DevEUI:** Clique em **Generate** para criar uma chave única global ou insira o identificador físico do seu chip.
3. **AppKey:** Clique em **Generate** para criar a chave secreta de criptografia.
4. Clique em **Register end device**.
<img width="629" height="372" alt="image" src="https://github.com/user-attachments/assets/cacee287-d883-4d7d-9f45-d0e33363b3e9" />


### 4. Configurar Decodificador de Payload (Payload Formatter)
Para sincronizar o formato dos dados enviados pela placa e permitir que a TTN decodifique a mensagem recebida:
1. No menu da sua aplicação/dispositivo no console da TTN, acesse **Payload formatters** > **Uplink**.
2. Selecione o **Formatter type** como **Custom javascript formatter**.
3. No campo de código, insira a função de decodificação:
   ```javascript
   function decodeUplink(input) {
     var tempInt = (input.bytes[0] << 8) | input.bytes[1];
     if (tempInt & 0x8000) {
       tempInt = tempInt - 0x10000;
     }
     return {
       data: {
         cpu_temperature: tempInt / 100.0
       }
     };
   }


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

---
## 🚀 Upload do Código de Exemplo: Telemetria da Temperatura Interna da CPU

Esta seção descreve o procedimento completo para configurar as credenciais, realizar o upload do firmware de teste (localizado em `src/heltec_lorawan/`) e validar o envio da temperatura interna do microcontrolador (capturada via função nativa do ESP32-S3) para a rede LoRaWAN.

> 🚨 **ALERTA MÁXIMO DE SEGURANÇA — CONEXÃO DA ANTENA:**
> **ANTES de conectar o cabo USB para ligar ou alimentar a placa Heltec V3 ao computador, a antena de rádio DEVE obrigatoriamente estar conectada ao conector da placa.** Ligar ou alimentar o dispositivo sem a antena conectada durante as rotinas de inicialização/transmissão pode danificar irreversivelmente o circuito de recepção e transmissão de rádio (SX1262).

---

### 1. Configuração de Credenciais (`secrets.h`)

1. No repositório, acesse a pasta **`src/`** e navegue até a subpasta **`heltec_lorawan/`** (onde estão localizados o arquivo `.ino`/C++ do código de teste e os arquivos de cabeçalho).
2. Localize o arquivo de exemplo **`secrets_example.h`**.
3. Crie uma cópia desse arquivo no mesmo diretório e renomeie a cópia exatamente para **`secrets.h`**.
4. Abra o `secrets.h` e substitua os valores padrão pelas credenciais reais que foram geradas dentro do painel da TTN (`devEui`, `appEui`, `appKey`) e pela sua licença da Heltec (`license`).
5. Certifique-se de que no arquivo principal do código (`.ino`) exista a linha `#include "secrets.h"` para que o programa inclua e utilize suas chaves privadas.

> 🔒 *Importante:* O arquivo `secrets.h` é ignorado pelo `.gitignore` para garantir que suas credenciais privadas não sejam expostas publicamente ao enviar atualizações para o GitHub.

---

### 2. Conexão USB e Upload para a Placa

1. Verifique novamente se a antena está conectada ao conector RF da placa.
2. Conecte a Heltec V3 ao computador utilizando um cabo USB-C.
3. Abra o arquivo do código na **Arduino IDE**, selecione a porta serial correspondente em **Ferramentas > Porta** e clique em **Carregar (Upload)**.

---

### 3. Validação do Envio, Teste de Distância e Recepção de ACK

1. Após concluir o upload com sucesso, abra o Monitor Serial (115200 baud) ou verifique o display OLED integrado da placa para acompanhar o progresso de conexão (*Join*).
2. Desloque-se para uma distância razoável e sem obstruções severas em relação a um dos Gateways LoRaWAN do campus da UFSM.

<img width="1242" height="869" alt="image" src="https://github.com/user-attachments/assets/b112e789-ebb0-4496-b0e5-e39c7a212815" />

3. **Observação crítica sobre o enlace de comunicação (Uplink vs. Downlink):**
   - Dependendo da sua localização em relação aos Gateways da UFSM, a Heltec V3 pode conseguir enviar o *payload* com a temperatura (*Uplink*) até o Gateway, mas o sinal de resposta de confirmação do Gateway (*Downlink / ACK*) pode não ser forte o suficiente para alcançar a placa de volta devido a obstáculos.
   - **Consulta indispensável:** É fundamental consultar a aba **Live Data** no painel da TTN para confirmar se as mensagens estão chegando e sendo decodificadas no servidor, mesmo que a placa na bancada não tenha recebido a confirmação de ACK.
