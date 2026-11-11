// ============================================================================
// DEMONSTRAÇÃO: CONTADOR DE VISITANTES VIA LoRaWAN (Heltec WiFi LoRa 32 V3)
// ============================================================================
// Cada vez que um visitante aperta o botão PRG da placa:
//   1. o contador sobe e aparece na tela OLED na hora;
//   2. a placa envia o novo total por rádio LoRa até o gateway da UFSM;
//   3. o LED branco da placa pisca quando o pacote sai pelo rádio;
//   4. o gateway repassa à The Things Network, e a página demo/ mostra o novo total.
//
// Segurar o botão PRG por 3 segundos zera o contador (e envia o zero).
// 30 s depois do último envio a placa manda o total mais uma vez (reenvio de garantia):
// se algum pacote se perdeu no ar, a página se corrige sozinha.
// O total fica gravado na memória flash: desligar a placa não perde a contagem.
//
// Mesmo cadastro da TTN do tutorial (mesmas chaves em secrets.h). A diferença é
// que este programa só transmite quando alguém aperta o botão, usa a porta 3 e
// não pede confirmação (ACK), por causa do limite de downlinks da TTN.
// ============================================================================

#include "LoRaWan_APP.h"
#include "HT_SSD1306Wire.h"
#include <Arduino.h>
#include <Preferences.h>

// Credenciais privadas (devEui, appEui, appKey) e licença Heltec
#include "secrets.h"

// ============================================================================
// 1. AJUSTES DA DEMONSTRAÇÃO
// ============================================================================
#define PINO_BOTAO          0      // Botão PRG da placa (GPIO0). Um botão externo maior pode ir
                                   // em outro pino livre, ligado ao GND (ex.: GPIO 7).
#define PINO_LED            35     // LED branco da Heltec V3 (LED_BUILTIN)
#define DATA_RATE           5      // DR5 = SF7 (pacote mais curto). Se o gateway estiver longe
                                   // e os pacotes não chegarem, use 3 (SF9).
#define INTERVALO_MINIMO_MS 10000  // Espera mínima entre dois envios. Apertos durante a espera
                                   // somam no contador e vão todos juntos no próximo pacote.
#define TEMPO_ZERAR_MS      3000   // Segurar o botão por este tempo zera o contador
#define REENVIO_MS          30000  // 30 s depois do último envio, manda o total mais uma vez.
                                   // Se um pacote se perdeu no ar, a página se corrige sozinha.
#define JANELAS_RX_MS       3000   // Depois de transmitir, o rádio escuta a resposta da rede
                                   // (1 s e 2 s depois). Nesse tempo não gravamos na flash.

// ============================================================================
// 2. DISPLAY OLED E REDE (iguais ao tutorial)
// ============================================================================
SSD1306Wire oledDisplay(0x3c, 500000, SDA_OLED, SCL_OLED, GEOMETRY_128_64, RST_OLED);

uint8_t nwkSKey[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint8_t appSKey[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint32_t devAddr  = (uint32_t)0x00000000;

uint16_t userChannelsMask[6] = { 0xFF00, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 }; // AU915 FSB2

LoRaMacRegion_t loraWanRegion = ACTIVE_REGION;
DeviceClass_t   loraWanClass  = CLASS_A;
uint32_t appTxDutyCycle       = 15000;   // Não usado aqui: só enviamos quando o botão é apertado
bool overTheAirActivation     = true;    // OTAA
bool loraWanAdr               = false;   // ADR desligado para o DATA_RATE acima valer
bool isTxConfirmed            = false;   // Sem ACK: cada ACK gasta um dos 10 downlinks/dia da TTN
uint8_t appPort               = 3;       // Porta 3 = pacotes da demonstração (o tutorial usa a 2)
uint8_t confirmedNbTrials     = 4;

// Indica se o rádio está transmitindo agora (variável da biblioteca LoRaWAN da Heltec).
// Com ela o LED só pisca quando o pacote realmente saiu pela antena.
extern "C" bool lora_txing;

// ============================================================================
// 3. ESTADO DA DEMONSTRAÇÃO
// ============================================================================
Preferences memoria;           // Guarda o contador na flash (NVS)
uint16_t visitantes = 0;       // Total de visitantes
uint32_t pacotesEnviados = 0;
bool conectado = false;        // Já fez o join com a rede?
bool envioPendente = false;    // Há um total novo esperando para ser enviado?
bool salvarPendente = false;   // Há um total novo esperando para ser gravado na flash?
uint32_t ultimoEnvio = 0;      // millis() do início do último envio
uint32_t proximaTentativa = 0; // Depois de uma falha, espera um pouco antes de tentar de novo
uint32_t tentativasJoin = 0;

// Transmissão em andamento
bool transmitindo = false;
bool envioEhReenvio = false;   // O pacote no ar é o reenvio de garantia?
bool reenvioPendente = false;  // Ainda falta o reenvio de garantia do último total?
uint16_t totalNoAr = 0;        // Total que está sendo transmitido
uint32_t inicioTx = 0;
uint32_t fimTx = 0;            // millis() do fim da última transmissão (0 = nenhuma ainda)

// Botão (com filtro de ruído)
bool botaoApertado = false;
bool zerouNesteAperto = false;
uint32_t inicioAperto = 0;
uint32_t ultimaMudancaBotao = 0;

// LED: pisca 3 vezes sem travar o programa (o rádio precisa de atenção constante)
uint8_t piscadasRestantes = 0;
uint32_t proximaTrocaLed = 0;
bool ledLigado = false;

// Mensagem da linha de baixo da tela
String rodape = "";
uint32_t rodapeAte = 0;        // 0 = mensagem fixa
bool telaSuja = true;

// ============================================================================
// 4. TELA
// ============================================================================
void mostrarRodape(const String &texto, uint32_t duracaoMs = 0) {
  rodape = texto;
  rodapeAte = duracaoMs ? millis() + duracaoMs : 0;
  telaSuja = true;
}

String rodapePadrao() {
  if (!conectado) return "Conectando a rede...";
  if (transmitindo) return "Transmitindo...";
  if (envioPendente) {
    uint32_t passou = millis() - ultimoEnvio;
    if (pacotesEnviados > 0 && passou < INTERVALO_MINIMO_MS) {
      return "Envia em " + String((INTERVALO_MINIMO_MS - passou) / 1000 + 1) + " s";
    }
    return "Enviando...";
  }
  return "Aperte o botao PRG!";
}

void desenharTela() {
  oledDisplay.clear();

  oledDisplay.setFont(ArialMT_Plain_10);
  oledDisplay.setTextAlignment(TEXT_ALIGN_LEFT);
  oledDisplay.drawString(0, 0, "VISITANTES");
  oledDisplay.setTextAlignment(TEXT_ALIGN_RIGHT);
  oledDisplay.drawString(128, 0, conectado ? "LoRaWAN ok" : "sem rede");

  oledDisplay.setFont(ArialMT_Plain_24);
  oledDisplay.setTextAlignment(TEXT_ALIGN_CENTER);
  oledDisplay.drawString(64, 16, String(visitantes));

  oledDisplay.setFont(ArialMT_Plain_10);
  oledDisplay.drawString(64, 52, rodapeAte ? rodape : rodapePadrao());
  oledDisplay.display();
}

// ============================================================================
// 5. CONTADOR NA FLASH
// ============================================================================
void salvarContador() {
  memoria.putUShort("visitantes", visitantes);
}

// ============================================================================
// 6. ENVIO LoRaWAN
// ============================================================================
// Payload de 4 bytes (porta 3):
//   bytes 0-1: total de visitantes (uint16, mais significativo primeiro)
//   bytes 2-3: temperatura da CPU x 100 (int16, mais significativo primeiro)
void montarPacote() {
  int16_t temp = (int16_t)(temperatureRead() * 100);
  appDataSize = 4;
  appData[0] = (uint8_t)(visitantes >> 8);
  appData[1] = (uint8_t)(visitantes & 0xFF);
  appData[2] = (uint8_t)(temp >> 8);
  appData[3] = (uint8_t)(temp & 0xFF);
}

void piscarLed(uint8_t vezes) {
  piscadasRestantes = vezes * 2;   // cada piscada = liga + desliga
  proximaTrocaLed = millis();
}

// O rádio está ocupado transmitindo ou escutando a resposta da rede?
bool radioOcupado() {
  return transmitindo || (fimTx != 0 && millis() - fimTx < JANELAS_RX_MS);
}

// Grava o contador na flash só quando o rádio está livre: uma gravação na flash
// trava o processador por alguns milissegundos e pode atrapalhar as janelas de recepção.
void salvarSePuder() {
  if (salvarPendente && !radioOcupado()) {
    salvarContador();
    salvarPendente = false;
  }
}

void tentarEnviar() {
  if (!conectado || transmitindo) return;
  if (millis() < proximaTentativa) return;

  bool reenvio = false;
  if (!envioPendente) {
    // Nada novo: faz o reenvio de garantia do último total, uma vez, 30 s depois
    if (!reenvioPendente || millis() - ultimoEnvio < REENVIO_MS) return;
    reenvio = true;
  }
  if (pacotesEnviados > 0 && millis() - ultimoEnvio < INTERVALO_MINIMO_MS) return;
  if (radioOcupado()) return;

  salvarSePuder();
  montarPacote();
  // SendFrame() devolve false quando a camada LoRaWAN aceitou o pacote; true se ela ainda
  // está ocupada com o envio anterior (aí tentamos de novo na próxima volta do loop).
  if (SendFrame() == true) return;

  if (!lora_txing) {
    // A camada LoRaWAN aceitou, mas o rádio não começou a transmitir: tenta de novo em 1 s
    Serial.println("Aviso: pacote aceito, mas o radio nao transmitiu. Tentando de novo.");
    proximaTentativa = millis() + 1000;
    return;
  }

  transmitindo = true;
  envioEhReenvio = reenvio;
  totalNoAr = visitantes;
  inicioTx = millis();
  ultimoEnvio = inicioTx;
  envioPendente = false;
  telaSuja = true;
}

// Acompanha a transmissão até o rádio terminar
void acompanharTransmissao() {
  if (!transmitindo) return;
  uint32_t duracao = millis() - inicioTx;

  if (lora_txing && duracao < 6000) return;   // ainda transmitindo

  transmitindo = false;
  fimTx = millis();
  telaSuja = true;

  if (!lora_txing && duracao < 2000) {
    // Terminou normalmente (um pacote em SF7 leva uns 50 ms no ar)
    pacotesEnviados++;
    reenvioPendente = !envioEhReenvio;
    piscarLed(3);
    mostrarRodape(envioEhReenvio ? "Reenviado" : "Enviado ao gateway!", 2500);
    Serial.printf("Pacote #%lu %s: %u visitantes (%lu ms no ar)\n", (unsigned long)pacotesEnviados,
                  envioEhReenvio ? "reenviado" : "enviado", totalNoAr, (unsigned long)duracao);
  } else {
    // O rádio não terminou a tempo (timeout de transmissão): tenta de novo
    envioPendente = true;
    proximaTentativa = millis() + 2000;
    mostrarRodape("Falha no radio, tentando", 2500);
    Serial.printf("Falha: a transmissao nao terminou (%lu ms). Tentando de novo.\n", (unsigned long)duracao);
  }
}

// ============================================================================
// 7. BOTÃO E LED (sem delay, para não atrapalhar o rádio)
// ============================================================================
void lerBotao() {
  bool apertado = digitalRead(PINO_BOTAO) == LOW;
  uint32_t agora = millis();

  if (apertado != botaoApertado && agora - ultimaMudancaBotao > 40) {
    ultimaMudancaBotao = agora;
    botaoApertado = apertado;
    if (apertado) {
      inicioAperto = agora;
      zerouNesteAperto = false;
    } else if (!zerouNesteAperto) {
      // Soltou o botão: conta um visitante
      if (visitantes < 65535) visitantes++;
      salvarPendente = true;
      envioPendente = true;
      rodapeAte = 0;
      telaSuja = true;
      Serial.printf("Visitante! Total: %u\n", visitantes);
    }
  }

  // Segurou por 3 s: zera
  if (botaoApertado && !zerouNesteAperto && agora - inicioAperto >= TEMPO_ZERAR_MS) {
    zerouNesteAperto = true;
    visitantes = 0;
    salvarPendente = true;
    envioPendente = true;
    mostrarRodape("Contador zerado", 2000);
    Serial.println("Contador zerado");
  }
}

void atualizarLed() {
  if (piscadasRestantes == 0 || millis() < proximaTrocaLed) return;
  ledLigado = !ledLigado;
  digitalWrite(PINO_LED, ledLigado ? HIGH : LOW);
  piscadasRestantes--;
  proximaTrocaLed = millis() + 150;
}

// ============================================================================
// 8. SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);

  pinMode(PINO_BOTAO, INPUT_PULLUP);
  pinMode(PINO_LED, OUTPUT);
  digitalWrite(PINO_LED, LOW);

  // Liga o Vext, que alimenta o OLED
  pinMode(Vext, OUTPUT);
  digitalWrite(Vext, LOW);
  delay(100);
  oledDisplay.init();

  memoria.begin("demo", false);
  visitantes = memoria.getUShort("visitantes", 0);
  envioPendente = true;  // Envia o total atual logo após conectar, para a página sincronizar

  desenharTela();

  Mcu.setlicense(license, HELTEC_BOARD);
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);
}

// ============================================================================
// 9. LOOP
// ============================================================================
void loop() {
  switch (deviceState) {
    case DEVICE_STATE_INIT:
      LoRaWAN.init(loraWanClass, loraWanRegion);
      LoRaWAN.setDefaultDR(DATA_RATE);
      break;

    case DEVICE_STATE_JOIN:
      // Pede para entrar na rede (OTAA). Se a rede não responder, a própria biblioteca
      // tenta de novo a cada 30 s; enquanto isso a tela mostra "Conectando a rede...".
      tentativasJoin++;
      mostrarRodape("Pedido de join #" + String(tentativasJoin), 5000);
      desenharTela();
      LoRaWAN.join();   // A biblioteca muda o estado para SLEEP enquanto espera a resposta
      break;

    case DEVICE_STATE_SEND:
      // A biblioteca coloca este estado quando o join dá certo.
      // Aqui não enviamos nada sozinhos: só marcamos que estamos conectados.
      if (!conectado) {
        conectado = true;
        mostrarRodape("Conectado a TTN!", 2500);
        Serial.println("Join OK");
      }
      deviceState = DEVICE_STATE_SLEEP;
      break;

    case DEVICE_STATE_CYCLE:
      // Só acontece se o pedido de join não pôde ser feito: tenta de novo em 30 s
      LoRaWAN.cycle(30000);
      deviceState = DEVICE_STATE_SLEEP;
      break;

    case DEVICE_STATE_SLEEP:
    default:
      // Em vez de LoRaWAN.sleep() (que pode desligar a placa em deep sleep e apagar a tela),
      // fazemos só o trabalho do rádio e dos temporizadores e seguimos acordados.
      Mcu.timerhandler();
      Radio.IrqProcess();
      break;
  }

  lerBotao();
  atualizarLed();
  acompanharTransmissao();
  tentarEnviar();
  salvarSePuder();

  // Redesenha a tela quando algo mudou, quando uma mensagem temporária expira
  // e uma vez por segundo (para a contagem regressiva do próximo envio)
  static uint32_t ultimoDesenho = 0;
  if (rodapeAte && millis() > rodapeAte) {
    rodapeAte = 0;
    telaSuja = true;
  }
  if (telaSuja || millis() - ultimoDesenho > 1000) {
    telaSuja = false;
    ultimoDesenho = millis();
    desenharTela();
  }
}
