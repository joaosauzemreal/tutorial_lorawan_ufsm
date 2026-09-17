#include "LoRaWan_APP.h"
#include "HT_SSD1306Wire.h"
#include <Arduino.h>

// Importa as credenciais privadas (devEui, appEui, appKey) e a licença Heltec do arquivo secrets.h
#include "secrets.h"

// ============================================================================
// 1. CONFIGURAÇÃO DO DISPLAY OLED INTEGRADO (SSD1306)
// ============================================================================
// Endereço I2C 0x3c, velocidade 500kHz, pinos SDA e SCL internos do ESP32-S3 Heltec V3
SSD1306Wire oledDisplay(0x3c, 500000, SDA_OLED, SCL_OLED, GEOMETRY_128_64, RST_OLED);

// ============================================================================
// 2. CONFIGURAÇÃO REGIONAL DE FREQUÊNCIA (AU915 - SUB-BANDA 2)
// ============================================================================
/* Reservado para ativação ABP (Não utilizado na ativação OTAA) */
uint8_t nwkSKey[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint8_t appSKey[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint32_t devAddr  = (uint32_t)0x00000000;

/* Máscara de Canais: Seleciona a Sub-banda 2 (FSB2 - Canais 8 a 15 + 65)
 * O valor 0xFF00 ativa a faixa de frequências de 916.8 MHz a 918.2 MHz (Padrão UFSM) */
uint16_t userChannelsMask[6] = { 0xFF00, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 };

// ============================================================================
// 3. PARÂMETROS OPERACIONAIS DA REDE LORAWAN
// ============================================================================
LoRaMacRegion_t loraWanRegion = ACTIVE_REGION; // Definido na IDE (LORAMAC_REGION_AU915)
DeviceClass_t   loraWanClass  = CLASS_A;        // Classe A: Maior economia de energia
uint32_t appTxDutyCycle       = 15000;          // Intervalo de transmissão: 15 segundos
bool overTheAirActivation     = true;           // Tipo de Ativação: OTAA (True)
bool loraWanAdr               = true;           // Adaptive Data Rate (ADR) ativado
bool isTxConfirmed            = true;           // Exige confirmação (ACK) da rede
uint8_t appPort               = 2;              // Porta da aplicação LoRaWAN
uint8_t confirmedNbTrials     = 4;              // Tentativas em caso de falha de ACK

// Variáveis de monitoramento e telemetria
uint32_t joinCounter = 0;
float cpuTemp = 0.0;

// ============================================================================
// 4. FUNÇÃO AUXILIAR DE INTERFACE GRÁFICA (OLED)
// ============================================================================
void drawStatus(String status, String info1, String info2) {
  oledDisplay.clear();
  oledDisplay.setTextAlignment(TEXT_ALIGN_LEFT);
  oledDisplay.setFont(ArialMT_Plain_10);
  oledDisplay.drawString(0, 0,  "--- HELTEC V3 LoRaWAN ---");
  oledDisplay.drawString(0, 16, "Status: " + status);
  oledDisplay.drawString(0, 32, info1);
  oledDisplay.drawString(0, 48, info2);
  oledDisplay.display();
}

// ============================================================================
// 5. PREPARAÇÃO E ESTRUTURAÇÃO DO PAYLOAD (DADOS ENVIADOS)
// ============================================================================
static void prepareTxFrame( uint8_t port ) {
    // Leitura da temperatura interna do processador ESP32-S3 em Celsius
    cpuTemp = temperatureRead();

    // Converte a temperatura flutuante para inteiro com 2 casas decimais 
    // Exemplo: 36.25 °C vira 3625 para otimizar o tamanho do pacote transmitido
    int16_t tempInt = (int16_t)(cpuTemp * 100);

    // Estrutura o Payload de 2 bytes utilizando deslocamento de bits (MSB / LSB)
    appDataSize = 2;
    appData[0] = (uint8_t)(tempInt >> 8);   // Byte mais significativo (MSB)
    appData[1] = (uint8_t)(tempInt & 0xFF); // Byte menos significativo (LSB)
}

// ============================================================================
// 6. CONFIGURAÇÃO INICIAL (SETUP)
// ============================================================================
void setup() {
  Serial.begin(115200);
  
  // Liga o barramento de alimentação externa Vext (Exigido para acionar o OLED)
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW); 
  delay(100);

  // Inicializa a tela OLED
  oledDisplay.init();
  drawStatus("INICIANDO...", "Licenca Ok", "Lendo Sensores...");

  // Registra a licença do chip (importada via secrets.h) na biblioteca Heltec
  Mcu.setlicense(license, HELTEC_BOARD);
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);
}

// ============================================================================
// 7. LOOP PRINCIPAL (MÁQUINA DE ESTADOS LORAWAN)
// ============================================================================
void loop() {
  switch( deviceState )
  {
    case DEVICE_STATE_INIT:
    {
      // Inicializa o stack do protocolo LoRaWAN na região e classe definidas
      LoRaWAN.init(loraWanClass, loraWanRegion);
      LoRaWAN.setDefaultDR(3); // Define Data Rate inicial (DR3 = SF7/125kHz no AU915)
      break;
    }
    case DEVICE_STATE_JOIN:
    {
      // Tenta a negociação OTAA (Join Request) com a rede da UFSM
      joinCounter++;
      drawStatus("ENVIANDO JOIN", "Tentativa #" + String(joinCounter), "AU915 FSB2");
      delay(10000);
      LoRaWAN.join();
      break;
    }
    case DEVICE_STATE_SEND:
    {
      // Coleta os dados dos sensores e envia o pacote via rádio
      prepareTxFrame( appPort );
      drawStatus("JOIN SUCESSO!", "Temp CPU: " + String(cpuTemp, 1) + " C", "Enviando Payload...");
      LoRaWAN.send();
      deviceState = DEVICE_STATE_CYCLE;
      break;
    }
    case DEVICE_STATE_CYCLE:
    {
      // Agenda a próxima transmissão com variação aleatória de tempo (Jitter)
      txDutyCycleTime = appTxDutyCycle + randr( -APP_TX_DUTYCYCLE_RND, APP_TX_DUTYCYCLE_RND );
      drawStatus("PACOTE ENVIADO", "Temp CPU: " + String(cpuTemp, 1) + " C", "Proximo envio: 15s");
      LoRaWAN.cycle(txDutyCycleTime);
      deviceState = DEVICE_STATE_SLEEP;
      break;
    }
    case DEVICE_STATE_SLEEP:
    {
      // Coloca a placa em modo de baixo consumo de energia até o próximo ciclo
      LoRaWAN.sleep(loraWanClass);
      break;
    }
    default:
    {
      deviceState = DEVICE_STATE_INIT;
      break;
    }
  }
}