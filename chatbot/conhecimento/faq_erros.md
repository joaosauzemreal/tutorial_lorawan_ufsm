# FAQ de erros e dúvidas comuns — Heltec WiFi LoRa 32 V3 na rede LoRaWAN/TTN da UFSM

Cada seção abaixo descreve um problema, os sintomas, as causas prováveis e como resolver.

## Posso ligar a placa sem antena, só para testar?

**Não.** Nunca ligue nem alimente a Heltec WiFi LoRa 32 V3 sem a antena conectada, nem para um teste rápido. Sem antena, a energia transmitida pelo rádio volta para o circuito e pode **danificar de forma permanente o rádio LoRa (SX1262)** da placa.

Regras de segurança:
1. Conecte a antena **antes** de ligar o cabo USB.
2. Para trocar ou retirar a antena, **desligue a placa primeiro** (tire o cabo USB).
3. Confira se o conector da antena está bem encaixado.

O código do tutorial começa a transmitir (join) logo depois de ligar, então a placa transmite mesmo que você só queira testar o Monitor Serial ou o display.

## A placa fica tentando o Join e nunca conecta na rede (fica em "ENVIANDO JOIN")

**Sintomas:** o display OLED mostra "ENVIANDO JOIN" e o contador de tentativas só aumenta. No Monitor Serial aparecem várias tentativas de join sem sucesso.

**Causas prováveis, da mais comum para a menos comum:**
1. **Aplicação criada no cluster errado da TTN.** Os gateways da UFSM estão ligados ao cluster europeu **eu1** (`eu1.cloud.thethings.network`). Se a aplicação foi criada em outro cluster (nam1, au1), o join não é aceito. Confira a URL do console: ela precisa começar com `eu1.cloud.thethings.network`. Não dá para mover a aplicação de cluster; é preciso criar outra no eu1.
2. **Plano de frequência errado.** No cadastro do end device na TTN deve estar `Australia 915-928 MHz, FSB 2`. Na Arduino IDE, em Ferramentas, a região deve ser `REGION_AU915`. No código, a máscara de canais `userChannelsMask` deve começar com `0xFF00` (sub-banda 2).
3. **Chaves erradas.** DevEUI, JoinEUI (AppEUI) e AppKey no `secrets.h` precisam ser exatamente as mesmas do console da TTN. Um único byte trocado impede o join. No console da TTN, clique no ícone `<>` ao lado de cada chave para vê-la em formato de array C e copie na ordem **msb**, que é a ordem mostrada por padrão. Não inverta os bytes: a inversão (lsb) é usada pela biblioteca LMIC, não pela biblioteca da Heltec.
4. **Versão LoRaWAN diferente.** No cadastro deve estar `LoRaWAN Specification 1.0.2` e `RP001 Regional Parameters 1.0.2 Rev B`.
5. **Fora do alcance de um gateway.** Aproxime-se de um gateway do campus, de preferência com visada direta e sem prédios no caminho.
6. **Antena desconectada ou mal encaixada.** Desligue a placa, confira a antena e só depois ligue de novo.

**Como investigar:** no console da TTN, abra o dispositivo e veja a aba **Live data**. Se aparecer "Join request" mas não "Join accept", a rede está ouvindo a placa e o problema provavelmente está nas chaves ou na versão LoRaWAN. Se não aparecer nada, a placa não está sendo ouvida: verifique o cluster, a frequência, o alcance e a antena.

## Em que ordem copiar as chaves da TTN para o secrets.h: msb ou lsb?

Use a ordem **msb**, que é a ordem em que o console da TTN mostra as chaves por padrão.

São três chaves, todas copiadas do dispositivo (end device) no console da TTN para o arquivo `secrets.h`:
- `devEui`: DevEUI, 8 bytes;
- `appEui`: JoinEUI (AppEUI), 8 bytes, zerado no tutorial da UFSM;
- `appKey`: AppKey, 16 bytes.

Como copiar sem erro:
1. No console da TTN, ao lado de cada chave, clique no ícone `<>` para ver o valor em formato de array C, por exemplo `{ 0x70, 0xB3, 0xD5, ... }`.
2. Confira que está selecionada a ordem **msb**.
3. Clique no ícone de copiar e cole no array correspondente do `secrets.h`.

Não inverta os bytes. A ordem lsb (invertida) é usada pela biblioteca LMIC, não pela biblioteca da Heltec usada neste tutorial. Uma chave com a ordem errada faz o join falhar.

## Preciso de alguma chave ou senha do gateway da UFSM? (AppKey do gateway)

**Não.** Gateways não têm AppKey, e você não precisa de nenhum acesso ao gateway da UFSM. A **AppKey pertence a cada dispositivo**: ela é gerada por você, no console da TTN, quando cadastra o seu dispositivo na sua aplicação (clicando em **Generate**). O gateway apenas repassa as mensagens de rádio para a TTN, sem precisar de chaves suas.

Nunca compartilhe a sua AppKey. Ela fica no `secrets.h`, que não vai para o GitHub.

## O que a placa envia? Tamanho e formato do payload

No código do tutorial, cada mensagem (uplink) leva um **payload de 2 bytes** com a temperatura interna do processador ESP32-S3, enviado na porta 2:
1. A temperatura é lida em graus Celsius e multiplicada por 100, para guardar 2 casas decimais em um número inteiro de 16 bits com sinal. Exemplo: 36,25 °C vira 3625.
2. O número é dividido em 2 bytes: primeiro o byte mais significativo (MSB), depois o menos significativo (LSB). Exemplo: 3625 = `0x0E29`, então os bytes enviados são `0E 29`.
3. Na TTN, o Payload formatter (`decodeUplink`) junta os 2 bytes, trata números negativos e divide por 100, mostrando o campo `cpu_temperature`.

Os cabeçalhos do LoRaWAN (endereço, contador, verificação de integridade) são acrescentados automaticamente pela biblioteca e não fazem parte do payload. Para enviar outros dados, aumente `appDataSize` e preencha mais posições de `appData` na função `prepareTxFrame`, e atualize o `decodeUplink` na TTN.

## Erro de licença: a placa trava na inicialização e mostra o Chip ID no Monitor Serial

**Sintomas:** logo após ligar, o Monitor Serial (115200 baud) mostra uma mensagem em inglês pedindo uma licença correta (algo como "Please provide a correct license!") junto com o ESP32ChipID, e o programa não avança.

**Causa:** o número que aparece é o **Chip ID** da placa. A biblioteca LoRaWAN da Heltec exige uma licença gratuita ligada ao Chip ID de cada placa. Isso não tem relação com o join nem com a TTN. Sem a licença correta, ou depois de apagar toda a memória flash, a placa para.

**Como resolver:**
1. Copie o Chip ID que aparece no Monitor Serial.
2. Acesse https://resource.heltec.cn/search, cole o Chip ID e clique em Confirm.
3. Copie a licença para o array `license` no arquivo `secrets.h`. A licença tem 4 números de 32 bits (128 bits no total), no formato `{ 0x4819D3A6, 0x3C4015EF, 0xC76E3CE5, 0x9742010D }` (exemplo).
4. Grave o código de novo na placa.

Depois de apagar toda a memória flash da placa, é preciso aplicar a licença de novo.

**Atenção:** cada placa tem a sua própria licença. A licença de uma placa não funciona em outra.

## Como enviar a licença da Heltec pelo Monitor Serial (comando AT+CDKEY)

Em vez de colocar a licença no código, dá para enviá-la pelo Monitor Serial, com o código já gravado na placa e o Monitor Serial aberto em 115200 baud.

O comando é `AT+CDKEY=` seguido dos 4 números da licença **colados um no outro**: sem `0x`, sem vírgulas e sem espaços. São 32 caracteres hexadecimais no total.

Exemplo: a licença `0x4819D3A6, 0x3C4015EF, 0xC76E3CE5, 0x9742010D` vira o comando:

```
AT+CDKEY=4819D3A63C4015EFC76E3CE59742010D
```

## Erro de compilação: "LoRaWan_APP.h: No such file or directory" ou a placa Heltec não aparece na lista

**Sintomas:** a Arduino IDE não compila e diz que não encontra `LoRaWan_APP.h` ou `HT_SSD1306Wire.h`, ou a opção "Heltec WiFi LoRa 32(V3)" não aparece no menu de placas.

**Causas prováveis e soluções:**
1. A biblioteca **Heltec ESP32 Dev-Boards** (da Heltec Automation) não foi instalada. Instale pelo Gerenciador de Bibliotecas, buscando "heltec esp32".
2. A placa selecionada não é a `Heltec WiFi LoRa 32(V3)`. Selecione em Ferramentas > Placa.
3. A IDE não tem suporte a placas ESP32 instalado. Se "Heltec WiFi LoRa 32(V3)" não aparecer em Ferramentas > Placa, instale o suporte a placas ESP32 pelo Gerenciador de Placas e reinicie a IDE.

Os menus "LoRaWAN Region" e "LoRaWAN Debug Level" só aparecem em Ferramentas com a placa Heltec selecionada.

## Erro de compilação: "secrets.h: No such file or directory"

**Causa:** o arquivo `secrets.h` não existe na mesma pasta do `heltec_lorawan.ino`. Ele não vem no repositório de propósito, porque guarda as suas chaves privadas.

**Como resolver:** copie o arquivo de modelo `src/secrets_example.h` para `src/heltec_lorawan/secrets.h` (a mesma pasta do `.ino`), preencha com as suas chaves da TTN e a licença da Heltec e compile de novo.

## A placa não aparece em Ferramentas > Porta ou o upload falha

**Sintomas:** nenhuma porta COM aparece, ou o upload termina com erro de conexão (por exemplo "Failed to connect to ESP32").

**Causas prováveis e soluções:**
1. **Cabo USB só de carga.** Alguns cabos USB-C não transmitem dados. Teste outro cabo.
2. **Driver do conversor USB-serial.** A Heltec V3 usa um conversor USB-serial CP2102. No Windows, se a porta não aparecer, instale o driver CP210x da Silicon Labs.
3. **Placa não entrou em modo de gravação.** Segure o botão **PRG** (boot), aperte e solte o **RST**, solte o PRG e tente o upload de novo.
4. **Porta ocupada.** Feche o Monitor Serial ou outro programa que esteja usando a porta.

## Os dados chegam na TTN, mas a placa não recebe a confirmação (ACK)

**Sintomas:** na aba Live data da TTN as mensagens com a temperatura aparecem, mas a placa repete o envio ou indica que não recebeu confirmação.

**Causa:** o caminho de volta (downlink, do gateway para a placa) é mais difícil que o de ida. Dependendo da distância e dos obstáculos, o gateway ouve a placa, mas a placa não ouve a resposta.

**Como resolver:**
- O mais importante é confirmar na aba **Live data** da TTN que as mensagens estão chegando. Se chegam, a conexão está funcionando.
- Aproxime-se de um gateway ou procure um lugar com visada direta.
- Se não precisar de confirmação, use mensagens não confirmadas (`isTxConfirmed = false` no código). Isso também ajuda a respeitar o limite de downlinks da TTN (veja a seção sobre a política de uso justo).

## Na TTN aparecem só bytes em hexadecimal, sem o campo cpu_temperature

**Isso não é um problema de conexão:** se as mensagens aparecem na TTN, a placa já está conectada e enviando dados. Falta só traduzir os bytes.

**Causa:** o decodificador de payload (Payload formatter) não foi configurado ou está com erro.

**Como resolver:** no console da TTN, abra **Payload formatters > Uplink**, escolha **Custom javascript formatter** e cole a função `decodeUplink` do tutorial. Ela lê 2 bytes (o primeiro é o mais significativo), trata números negativos e divide por 100. Depois disso, as novas mensagens aparecem com `cpu_temperature` em graus Celsius. Mensagens antigas não são decodificadas de novo.

## O display OLED fica apagado

**Causa provável:** a alimentação externa Vext, que liga o display, não foi ativada.

**Como resolver:** no `setup()` precisam existir `pinMode(Vext, OUTPUT);` e `digitalWrite(Vext, LOW);` antes de `oledDisplay.init();`. O código do tutorial já faz isso. Se você trocou o código, confira essas linhas.

## Posso deixar a placa enviando a cada 15 segundos o dia inteiro? (política de uso justo da TTN)

**Não.** Enviar a cada 15 segundos o dia inteiro ultrapassa os limites da rede pública da TTN. Esse intervalo serve só para testes de alguns minutos, durante a prática do tutorial.

A política de uso justo (Fair Use Policy) da TTN permite, por dispositivo:
- no máximo **30 segundos de tempo no ar (airtime) de uplink a cada 24 horas**;
- no máximo **10 mensagens de downlink a cada 24 horas**. A confirmação (ACK) de uma mensagem confirmada é um downlink.

O exemplo do tutorial envia a cada 15 segundos (`appTxDutyCycle = 15000`) com confirmação (`isTxConfirmed = true`). Ligado o dia todo, isso dá milhares de mensagens e de ACKs por dia, muito acima dos dois limites.

**Para deixar a placa ligada por muito tempo:**
1. Aumente o intervalo entre envios: `appTxDutyCycle` é o intervalo em milissegundos. Por exemplo, `600000` = 10 minutos.
2. Use mensagens não confirmadas: `isTxConfirmed = false`.
3. Para saber quanto tempo no ar cada mensagem gasta, use uma calculadora de airtime LoRaWAN.

## O que significa setDefaultDR(3) no código?

`LoRaWAN.setDefaultDR(3)` define a taxa de dados (Data Rate) inicial. Na região **AU915**, DR3 corresponde a **SF9 com 125 kHz**. A tabela completa está na seção sobre Spreading Factor e Data Rate. Com o ADR ativado (`loraWanAdr = true`), a rede pode ajustar a taxa de dados automaticamente conforme a qualidade do sinal.

## Um problema que não está neste FAQ

Quando aparecer um problema diferente, siga esta ordem de diagnóstico:
1. **Monitor Serial (115200 baud):** veja a última mensagem antes de o problema acontecer. Com "LoRaWAN Debug Level" em `FREQ_AND_DIO`, aparecem as frequências usadas em cada envio, que devem estar entre 916,8 e 918,2 MHz (sub-banda 2).
2. **Aba Live data no console da TTN:** mostra se a rede está recebendo algo do dispositivo (join request, uplinks) e com que qualidade de sinal (RSSI e SNR).
3. **Revise a configuração da rede UFSM:** cluster eu1, plano AU915 FSB 2, LoRaWAN 1.0.2, ativação OTAA, JoinEUI zerado.
4. **Revise o hardware:** antena conectada antes de ligar, cabo USB de dados, placa selecionada corretamente na Arduino IDE.
