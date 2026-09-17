#ifndef SECRETS_H
#define SECRETS_H

#include <Arduino.h>

// ============================================================================
// MODELO DE CREDENCIAIS (SUBSTITUA PELOS SEUS VALORES E RENOMEIE PARA secrets.h)
// ============================================================================

// Obtenha em: https://resource.heltec.cn/search
uint32_t license[4] = { 0x00000000, 0x00000000, 0x00000000, 0x00000000 };

// Copie do console da TTN
uint8_t devEui[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint8_t appEui[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint8_t appKey[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

#endif