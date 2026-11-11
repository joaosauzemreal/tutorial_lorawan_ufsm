// Formatador de uplink para a TTN (opcional).
// Console da TTN > sua aplicação > Payload formatters > Uplink > Custom Javascript formatter.
// Serve para ver o número de visitantes já decodificado na aba "Live data".
// O painel (servidor.py) lê os bytes por conta própria e funciona sem este formatador.
//
// Substitui o formatador do tutorial: a porta 2 continua igual e a porta 3 ganha o contador.
function decodeUplink(input) {
  var b = input.bytes;
  function int16(i) {
    var v = (b[i] << 8) | b[i + 1];
    return v > 32767 ? v - 65536 : v;
  }

  if (input.fPort === 2 && b.length >= 2) {
    return { data: { cpu_temperature: int16(0) / 100 } };
  }
  if (input.fPort === 3 && b.length >= 4) {
    return {
      data: {
        visitantes: (b[0] << 8) | b[1],
        cpu_temperature: int16(2) / 100
      }
    };
  }
  return { data: {}, warnings: ["Porta ou tamanho de pacote desconhecido"] };
}
