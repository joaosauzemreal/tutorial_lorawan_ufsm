# FAQ de erros e dúvidas comuns — Heltec WiFi LoRa 32 V3 na rede LoRaWAN/TTN da UFSM

Cada seção abaixo descreve um problema, os sintomas, as causas prováveis e como resolver.

## Posso ligar a placa sem antena, só para testar?

**Não.** Nunca ligue nem alimente a Heltec WiFi LoRa 32 V3 sem a antena conectada, nem para um teste rápido. Sem antena, a energia transmitida pelo rádio volta para o circuito e pode **danificar de forma permanente o rádio LoRa (SX1262)** da placa.

Regras de segurança:
1. Conecte a antena **antes** de ligar o cabo USB.
2. Para trocar ou retirar a antena, **desligue a placa primeiro** (tire o cabo USB).
3. Confira se o conector da antena está bem encaixado.

O código do tutorial começa a transmitir (join) logo depois de ligar, então a placa transmite mesmo que você só queira testar o Monitor Serial ou o display.

## A placa fica em "ENVIANDO JOIN" e nunca conecta: o que conferir

Confira seis itens: o cluster **eu1**, o plano `Australia 915-928 MHz, FSB 2`, as chaves no `secrets.h` (ordem msb), a versão `LoRaWAN Specification 1.0.2` com `RP001 Regional Parameters 1.0.2 Rev B`, o alcance até o gateway e a antena.

**Sintomas:** o display mostra "ENVIANDO JOIN", o contador de tentativas só aumenta e a placa nunca passa para "JOIN SUCESSO".

Confira, nesta ordem:
1. **Cluster da TTN:** a aplicação precisa estar no cluster europeu **eu1**. A URL do console deve começar com `eu1.cloud.thethings.network`.
2. **Plano de frequência:** no cadastro do dispositivo, `Australia 915-928 MHz, FSB 2`. Na Arduino IDE, região `REGION_AU915`.
3. **Chaves:** DevEUI, JoinEUI (AppEUI) e AppKey no `secrets.h` iguais às do console da TTN, na ordem msb.
4. **Versão LoRaWAN:** `LoRaWAN Specification 1.0.2` e `RP001 Regional Parameters 1.0.2 Rev B`.
5. **Alcance:** aproxime-se de um gateway do campus, com visada direta.
6. **Antena:** desligue a placa, confira se a antena está bem conectada e ligue de novo.

Para descobrir qual desses itens é o problema, use a aba Live data da TTN (veja a seção "Como usar o Live data para descobrir por que o join falha").

## Como usar o Live data para descobrir por que o join falha

No console da TTN, abra o seu dispositivo (end device) e a aba **Live data**, e deixe a placa tentando o join. Há dois casos:

**Caso 1: aparece "Join request", mas nunca "Join accept".** A rede está ouvindo a placa. Então o cluster, a frequência, o alcance e a antena estão funcionando. O problema está nas **chaves** (DevEUI, JoinEUI ou AppKey diferentes do console, ou na ordem errada) ou na **versão LoRaWAN** do cadastro.

**Caso 2: não aparece nada.** A rede não está ouvindo a placa. O problema está no **cluster** (aplicação fora do eu1), no **plano de frequência** (não é AU915 FSB 2), no **alcance** (longe do gateway) ou na **antena**.

## Criei a aplicação no console da TTN e não funciona (cluster errado)

O console da TTN é dividido em **clusters** regionais, e cada um é um console separado: Europe 1 (**eu1**), North America 1 (**nam1**), Australia 1 (**au1**). Ao entrar no console pela página da TTN, é preciso escolher um deles.

Os gateways da UFSM estão registrados no cluster **eu1**. Se você criou a aplicação em qualquer outro cluster, a rede da UFSM não entrega as mensagens da sua placa, e o join nunca é aceito.

**Como resolver:**
1. Confira a URL do console onde você criou a aplicação. Ela precisa começar com `eu1.cloud.thethings.network`.
2. Se começar com outro endereço (por exemplo `nam1` ou `au1`), crie uma **nova** aplicação e um novo dispositivo em https://eu1.cloud.thethings.network/console. Não existe opção para mover uma aplicação de um cluster para outro.
3. Copie as chaves do novo dispositivo para o `secrets.h` e carregue o código na placa de novo.

## Quais opções escolher ao cadastrar o dispositivo (end device) na TTN

Plano `Australia 915-928 MHz, FSB 2`; versão LoRaWAN `LoRaWAN Specification 1.0.2`; parâmetros regionais `RP001 Regional Parameters 1.0.2 Rev B`; JoinEUI `0000000000000000`; DevEUI e AppKey gerados com **Generate**. A versão LoRaWAN e a versão dos parâmetros regionais são dois campos e sempre devem ser preenchidos juntos.

Em **+ Register end device** > **Enter end device specifics manually**, use exatamente:
- **Frequency plan:** `Australia 915-928 MHz, FSB 2`
- **LoRaWAN version:** `LoRaWAN Specification 1.0.2`
- **Regional Parameters version:** `RP001 Regional Parameters 1.0.2 Rev B`
- **JoinEUI (AppEUI):** `0000000000000000` (zeros)
- **DevEUI:** clique em **Generate**
- **AppKey:** clique em **Generate**

Depois clique em **Register end device**. A aplicação onde o dispositivo é cadastrado precisa estar no cluster **eu1**.

## Quais versões escolher no cadastro do dispositivo (versão LoRaWAN e versão dos parâmetros regionais)?

Escolha a versão `LoRaWAN Specification 1.0.2` com `RP001 Regional Parameters 1.0.2 Rev B`. São dois campos de versão no cadastro do dispositivo, e os dois precisam ser preenchidos:
1. **LoRaWAN version:** `LoRaWAN Specification 1.0.2`
2. **Regional Parameters version:** `RP001 Regional Parameters 1.0.2 Rev B`

A versão 1.0.2 é a usada pela biblioteca da Heltec.

## A placa precisa de internet ou Wi-Fi para mandar os dados?

**Não.** Neste tutorial, a placa envia os dados pelo **rádio LoRa** até o gateway. Quem usa a internet é o **gateway**, que repassa as mensagens para a TTN. O Wi-Fi da Heltec WiFi LoRa 32 V3 não é usado no tutorial.

Por isso a placa funciona em lugares sem Wi-Fi, desde que esteja ao alcance de um gateway LoRaWAN da UFSM.

## Posso usar outra placa ou módulo LoRa (RFM95, SX1276, Arduino Uno, outro ESP32)?

Este tutorial não ensina a ligar nem a programar outros módulos: ele cobre **só a placa Heltec WiFi LoRa 32 V3**, com a biblioteca da Heltec. Não há neste material ligação de pinos, bibliotecas nem código para outras placas. Outras placas e módulos (por exemplo RFM95 ou SX1276 ligados a um Arduino Uno ou a outro ESP32) usam outras bibliotecas, como a LMIC, e outra ligação de pinos, que **não fazem parte deste tutorial**. Por isso o assistente não tem a pinagem nem o código para eles.

O que vale para qualquer dispositivo na rede da UFSM é a configuração da rede: aplicação no cluster **eu1** da TTN, plano `Australia 915-928 MHz, FSB 2`, ativação OTAA e antena sempre conectada antes de ligar. Para a ligação de pinos e o código de outra placa, consulte a documentação do fabricante do módulo e da biblioteca escolhida.

## O que colocar no JoinEUI (AppEUI)?

Preencha o JoinEUI com **zeros**: `0000000000000000`. Você mesmo digita os zeros no cadastro do dispositivo; a TTN não gera o JoinEUI. Só o **DevEUI** e a **AppKey** têm o botão **Generate**.

No `secrets.h`, o `appEui` fica com os 8 bytes zerados: `{ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 }`.

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

A placa envia **2 bytes**, que juntos formam **um único número**: a temperatura da CPU multiplicada por 100.
- 1º byte: a parte alta do número (byte mais significativo, MSB);
- 2º byte: a parte baixa do número (byte menos significativo, LSB).

Exemplo: 36,25 °C → 3625 = `0x0E29` → 1º byte `0E`, 2º byte `29`. Na TTN, o `decodeUplink` junta os 2 bytes e divide por 100.

No código do tutorial, cada mensagem (uplink) leva um **payload de 2 bytes** com a temperatura interna do processador ESP32-S3, enviado na porta 2:
1. A temperatura é lida em graus Celsius e multiplicada por 100, para guardar 2 casas decimais em um número inteiro de 16 bits com sinal. Exemplo: 36,25 °C vira 3625.
2. O número é dividido em 2 bytes: primeiro o byte mais significativo (MSB), depois o menos significativo (LSB). Exemplo: 3625 = `0x0E29`, então os bytes enviados são `0E 29`.
3. Na TTN, o Payload formatter (`decodeUplink`) junta os 2 bytes, trata números negativos e divide por 100, mostrando o campo `cpu_temperature`.

Os cabeçalhos do LoRaWAN (endereço, contador, verificação de integridade) são acrescentados automaticamente pela biblioteca e não fazem parte do payload. Para enviar outros dados, aumente `appDataSize` e preencha mais posições de `appData` na função `prepareTxFrame`, e atualize o `decodeUplink` na TTN.

## Erro de licença: a placa trava na inicialização e mostra o Chip ID no Monitor Serial

O número é o **Chip ID**. Gere a licença em https://resource.heltec.cn/search e coloque os 4 números no array `license` do `secrets.h`, ou envie pelo comando `AT+CDKEY=`.

**Sintomas:** logo após ligar, o Monitor Serial (115200 baud) mostra uma mensagem em inglês pedindo uma licença correta (algo como "Please provide a correct license!") junto com o ESP32ChipID, e o programa não avança.

**Causa:** o número que aparece é o **Chip ID** da placa. A biblioteca LoRaWAN da Heltec exige uma licença gratuita ligada ao Chip ID de cada placa. Isso não tem relação com o join nem com a TTN. Sem a licença correta, ou depois de apagar toda a memória flash, a placa para.

**Como resolver:**
1. Copie o Chip ID que aparece no Monitor Serial.
2. Acesse https://resource.heltec.cn/search, cole o Chip ID e clique em Confirm.
3. Copie a licença para o array `license` no arquivo `secrets.h`. A licença tem 4 números de 32 bits (128 bits no total), no formato `{ 0x4819D3A6, 0x3C4015EF, 0xC76E3CE5, 0x9742010D }` (exemplo).
4. Grave o código de novo na placa.

**Atenção:** cada placa tem a sua própria licença. A licença de uma placa não funciona em outra.

## Como enviar a licença da Heltec pelo Monitor Serial (comando AT+CDKEY)

Com o código já gravado e o Monitor Serial aberto em 115200 baud, envie `AT+CDKEY=` seguido dos 4 números da licença colados (32 caracteres, sem `0x`, vírgulas ou espaços). Por esse caminho não é preciso mexer no código.

Em vez de colocar a licença no código, dá para enviá-la pelo Monitor Serial, com o código já gravado na placa e o Monitor Serial aberto em 115200 baud.

O comando é `AT+CDKEY=` seguido dos 4 números da licença **colados um no outro**: sem `0x`, sem vírgulas e sem espaços. São 32 caracteres hexadecimais no total.

Exemplo: a licença `0x4819D3A6, 0x3C4015EF, 0xC76E3CE5, 0x9742010D` vira o comando:

```
AT+CDKEY=4819D3A63C4015EFC76E3CE59742010D
```

## Erro de compilação: "LoRaWan_APP.h: No such file or directory" ou a placa Heltec não aparece na lista

Instale a biblioteca **Heltec ESP32 Dev-Boards** pelo Gerenciador de Bibliotecas e selecione a placa **Heltec WiFi LoRa 32(V3)** em Ferramentas > Placa. As duas coisas são necessárias.

**Sintomas:** a Arduino IDE não compila e diz que não encontra `LoRaWan_APP.h` ou `HT_SSD1306Wire.h`, ou a opção "Heltec WiFi LoRa 32(V3)" não aparece no menu de placas.

**Causas prováveis e soluções:**
1. A biblioteca **Heltec ESP32 Dev-Boards** (da Heltec Automation) não foi instalada. Instale pelo Gerenciador de Bibliotecas, buscando "heltec esp32".
2. A placa selecionada não é a `Heltec WiFi LoRa 32(V3)`. Selecione em Ferramentas > Placa.
3. A IDE não tem suporte a placas ESP32 instalado. Se "Heltec WiFi LoRa 32(V3)" não aparecer em Ferramentas > Placa, instale o suporte a placas ESP32 pelo Gerenciador de Placas e reinicie a IDE.

Os menus "LoRaWAN Region" e "LoRaWAN Debug Level" só aparecem em Ferramentas com a placa Heltec selecionada.

## Erro de compilação: "secrets.h: No such file or directory"

Copie `src/secrets_example.h` para a pasta `src/heltec_lorawan/` (a mesma do `.ino`), renomeie para `secrets.h` e preencha com as suas chaves e a sua licença.

**Causa:** o arquivo `secrets.h` não existe na mesma pasta do `heltec_lorawan.ino`. Ele não vem no repositório de propósito, porque guarda as suas chaves privadas.

**Como resolver:** copie o arquivo de modelo `src/secrets_example.h` para `src/heltec_lorawan/secrets.h` (a mesma pasta do `.ino`), preencha com as suas chaves da TTN e a licença da Heltec e compile de novo.

## A placa não aparece em Ferramentas > Porta ou o upload falha

Use um cabo USB-C de dados (cabos que só carregam não funcionam), instale o driver CP210x, coloque a placa em modo de gravação (segure PRG, aperte e solte RST, solte PRG) e feche o Monitor Serial.

**Sintomas:** nenhuma porta COM aparece, ou o upload termina com erro de conexão (por exemplo "Failed to connect to ESP32").

**Causas prováveis e soluções:**
1. **Cabo USB.** Use um cabo USB-C **de dados**. Cabos que só carregam a bateria não deixam o computador ver a placa; se estiver em dúvida, teste outro cabo.
2. **Driver do conversor USB-serial.** A Heltec V3 usa um conversor USB-serial CP2102. No Windows, se a porta não aparecer, instale o driver CP210x, baixado da página oficial da Silicon Labs: https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers
3. **Placa não entrou em modo de gravação.** Coloque a placa em modo de gravação com os dois botões dela, nesta ordem:
   1. aperte e **mantenha apertado** o botão **PRG** (boot);
   2. com o PRG ainda apertado, aperte e solte o botão **RST**;
   3. solte o **PRG**;
   4. clique em **Carregar** na Arduino IDE.
4. **Porta ocupada.** Feche o Monitor Serial ou outro programa que esteja usando a porta.

## Os dados chegam na TTN, mas a placa não recebe a confirmação (ACK)

Se as mensagens aparecem no Live data, a conexão funciona. O ACK é um downlink, mais difícil de receber: aproxime-se do gateway ou desligue a confirmação com `isTxConfirmed = false`.

**Sintomas:** na aba Live data da TTN as mensagens com a temperatura aparecem, mas a placa repete o envio ou indica que não recebeu confirmação.

**Causa:** o caminho de volta (downlink, do gateway para a placa) é mais difícil que o de ida. Dependendo da distância e dos obstáculos, o gateway ouve a placa, mas a placa não ouve a resposta.

**Como resolver:**
1. Confirme na aba **Live data** da TTN que as mensagens estão chegando. Se chegam, a conexão está funcionando, mesmo sem o ACK.
2. Aproxime-se de um gateway ou procure um lugar com visada direta, para a placa conseguir ouvir a resposta.
3. Para a placa parar de esperar o ACK, desligue a confirmação no código: `isTxConfirmed = false`. Isso também ajuda a respeitar o limite de 10 downlinks por dia da TTN.

## Na TTN aparecem só bytes em hexadecimal, sem o campo cpu_temperature

Configure o Payload formatter: em **Payload formatters > Uplink**, escolha **Custom javascript formatter** e cole a função `decodeUplink` do tutorial.

**Isso não é um problema de conexão:** se as mensagens aparecem na TTN, a placa já está conectada e enviando dados. Falta só traduzir os bytes.

**Causa:** o decodificador de payload (Payload formatter) não foi configurado ou está com erro.

**Como resolver:** no console da TTN, abra **Payload formatters > Uplink**, escolha **Custom javascript formatter** e cole a função `decodeUplink` do tutorial. Ela lê 2 bytes (o primeiro é o mais significativo), trata números negativos e divide por 100. Depois disso, as novas mensagens aparecem com `cpu_temperature` em graus Celsius. Mensagens antigas não são decodificadas de novo.

## O display OLED fica apagado

**Causa provável:** a alimentação externa Vext, que liga o display, não foi ativada.

**Como resolver:** no `setup()` precisam existir `pinMode(Vext, OUTPUT);` e `digitalWrite(Vext, LOW);` antes de `oledDisplay.init();`. O código do tutorial já faz isso. Se você trocou o código, confira essas linhas.

## Posso deixar a placa enviando a cada 15 segundos o dia inteiro? (política de uso justo da TTN)

Não. A TTN permite por dispositivo **30 segundos de airtime de uplink** e **10 downlinks** por dia. Para uso contínuo, aumente `appTxDutyCycle` (ex.: `600000` = 10 minutos) e use `isTxConfirmed = false`.

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

## A placa fica reiniciando sozinha ou trava

Este problema não está coberto pelo tutorial, então não dá para apontar uma causa certa. Para investigar:
1. Abra o Monitor Serial (115200 baud) e veja a última mensagem antes de a placa reiniciar. O ESP32 costuma mostrar o motivo do reinício; uma mensagem com "Brownout", por exemplo, indica falta de energia.
2. Troque o cabo USB e a porta USB do computador, de preferência uma porta direta, sem hub. Falta de energia é uma causa comum de reinícios.
3. Confira se a antena está conectada.
4. Se você alterou o código, teste de novo com o código original do tutorial.

Se aparecer uma mensagem pedindo licença junto com o Chip ID, veja a seção sobre o erro de licença.

## Qual a distância máxima (alcance) até o gateway?

O alcance do LoRa é de cerca de **2 a 5 km em área urbana** e pode passar de **15 km com visada direta**, sem obstáculos entre a antena da placa e o gateway. O alcance real depende muito de prédios, árvores e relevo, da altura das antenas e do Spreading Factor usado.

No campus da UFSM, o gateway citado neste projeto fica no CT. Se a placa não conectar, aproxime-se do CT, de preferência com visada direta, e confira a qualidade do sinal (RSSI e SNR) na aba Live data da TTN.

## Dá para mandar dados da TTN para a placa (downlink)?

**Sim.** Mensagens da rede para a placa se chamam **downlink**. No console da TTN, abra o dispositivo, vá em **Messaging** e use a opção de **Downlink** para agendar uma mensagem (os bytes em hexadecimal e a porta, FPort).

Como a placa do tutorial é **classe A**, ela só recebe um downlink logo depois de enviar um uplink, nas janelas de recepção RX1 e RX2. Por isso o downlink agendado chega junto com o próximo envio da placa. A TTN permite no máximo 10 downlinks por dia por dispositivo.

O código do tutorial só envia dados e não trata as mensagens recebidas. Para usar downlinks, é preciso acrescentar isso ao código, o que não faz parte deste tutorial.

## Como guardar os dados ou fazer gráficos da temperatura?

O tutorial termina com os dados chegando na aba Live data da TTN; gráficos e armazenamento não fazem parte dele. O caminho é usar as **integrações** da TTN: no console, abra a sua aplicação e a seção **Integrations**. Há opções como:
- **MQTT** e **Webhooks**, para enviar cada mensagem a um programa ou serviço seu;
- **Storage Integration**, que guarda as mensagens por um tempo na própria TTN;
- integrações prontas com plataformas de painéis (dashboards), que fazem os gráficos.

Use o campo `cpu_temperature`, que aparece depois de configurar o Payload formatter.

## Um problema que não está neste FAQ

Quando aparecer um problema diferente, siga esta ordem de diagnóstico:
1. **Monitor Serial (115200 baud):** veja a última mensagem antes de o problema acontecer. Com "LoRaWAN Debug Level" em `FREQ_AND_DIO`, aparecem as frequências usadas em cada envio, que devem estar entre 916,8 e 918,2 MHz (sub-banda 2).
2. **Aba Live data no console da TTN:** mostra se a rede está recebendo algo do dispositivo (join request, uplinks) e com que qualidade de sinal (RSSI e SNR).
3. **Revise a configuração da rede UFSM:** cluster eu1, plano AU915 FSB 2, LoRaWAN 1.0.2, ativação OTAA, JoinEUI zerado.
4. **Revise o hardware:** antena conectada antes de ligar, cabo USB de dados, placa selecionada corretamente na Arduino IDE.
