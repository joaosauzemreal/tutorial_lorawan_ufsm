# 🤖 Assistente LoRaWAN UFSM (chatbot)

Chatbot que tira dúvidas sobre o tutorial e sobre LoRa, LoRaWAN e The Things Network. Ele roda **inteiramente no servidor**, com um modelo de linguagem local ([Phi-4-mini](https://ollama.com/library/phi4-mini)) executado pelo [Ollama](https://ollama.com). Nenhum dado vai para serviços externos.

## Como funciona

O assistente usa **RAG** (geração aumentada por recuperação):

1. Na inicialização, o [README do tutorial](../README.md) e os arquivos da pasta [`conhecimento/`](conhecimento/) são divididos em trechos pelos títulos. Cada trecho vira um vetor (*embedding*) gerado pelo modelo multilíngue `bge-m3`.
2. A cada pergunta, o sistema busca os trechos mais parecidos com ela e mantém só os que estão perto do melhor (veja `MARGEM_TRECHOS`).
3. Filtro de assunto: a pergunta também é comparada com exemplos de perguntas fora do assunto ([`app/exemplos_fora_do_assunto.txt`](app/exemplos_fora_do_assunto.txt)). Se ela se parecer mais com esses exemplos do que com a documentação, o assistente devolve uma frase de recusa pronta, sem chamar o modelo.
4. O Phi-4-mini recebe a pergunta, esses trechos e as instruções do assistente ([`app/prompts.py`](app/prompts.py)), e escreve a resposta, que aparece aos poucos na tela junto com as fontes usadas.

```
chatbot/
├── app/
│   ├── main.py            # servidor web (FastAPI): página, /api/chat e /api/status
│   ├── rag.py             # divide os documentos, gera embeddings e faz a busca
│   ├── motor.py           # monta a conversa e fala com o Ollama
│   ├── prompts.py         # instruções fixas do assistente
│   ├── avaliar.py         # roda as perguntas de teste e salva as respostas
│   ├── config.py          # configurações (lidas das variáveis de ambiente)
│   └── static/index.html  # interface do chat
├── conhecimento/          # o que o bot sabe, além do README do tutorial
│   ├── conceitos_lorawan.md
│   ├── faq_erros.md
│   └── projeto_ufsm.md
├── avaliacao/perguntas_teste.md
├── deploy/assistente-lorawan.service   # serviço systemd (instalação sem Docker)
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Requisitos do servidor

- Linux com **Docker** e o plugin **Docker Compose** (recomendado) **ou** Python 3.10+.
- **RAM:** pelo menos 8 GB livres. Os dois modelos ocupam cerca de 4 GB carregados.
- **Disco:** cerca de 6 GB livres.
- **Internet** na primeira execução, para baixar os modelos. Depois, funciona sem internet.
- GPU é opcional. Sem GPU tudo funciona, só que mais devagar (veja [Desempenho](#desempenho)).

## Instalação com Docker (recomendado)

```bash
git clone https://github.com/joaosauzemreal/tutorial_lorawan_ufsm.git
cd tutorial_lorawan_ufsm/chatbot
cp .env.example .env          # opcional: ajuste porta e modelos
docker compose up -d --build
docker compose logs -f app    # acompanhe até aparecer "Assistente pronto"
```

Na primeira vez, o download dos modelos leva alguns minutos. Depois, abra `http://IP-DO-SERVIDOR:8000` no navegador.

Para conferir o estado sem abrir a página: `curl http://localhost:8000/api/status`.

**Com GPU NVIDIA:** instale o [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) e descomente o bloco `deploy:` em `docker-compose.yml`.

## Instalação sem Docker

```bash
# 1. Ollama (instala e cria o serviço "ollama")
curl -fsSL https://ollama.com/install.sh | sh

# 2. Aplicação
git clone https://github.com/joaosauzemreal/tutorial_lorawan_ufsm.git
cd tutorial_lorawan_ufsm/chatbot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Teste rápido (os modelos são baixados na primeira execução)
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Para deixar rodando sempre, mesmo depois de reiniciar o servidor, edite os caminhos e o usuário em [`deploy/assistente-lorawan.service`](deploy/assistente-lorawan.service) e siga as instruções que estão no início do arquivo.

## Atualizar o que o bot sabe

O bot lê os documentos sempre que inicia. Depois de editar o `README.md` do tutorial ou os arquivos de `conhecimento/` e enviar para o GitHub, rode no servidor:

```bash
~/tutorial_lorawan_ufsm/chatbot/atualizar.sh    # instalação sem Docker (serviço systemd)
# ou, com Docker:  git pull && docker compose restart app
```

O `atualizar.sh` baixa a versão nova, confere as dependências, reinicia o serviço e espera o assistente ficar pronto.

Só os trechos que mudaram têm os embeddings recalculados.

Para ensinar algo novo ao bot (um erro novo, por exemplo), acrescente uma seção com título `##` em [`conhecimento/faq_erros.md`](conhecimento/faq_erros.md). Cada seção deve fazer sentido sozinha, porque é recortada e entregue ao modelo separadamente.

## Testar e comparar modelos

O arquivo [`avaliacao/perguntas_teste.md`](avaliacao/perguntas_teste.md) tem 28 perguntas, com o que cada resposta precisa conter. O script abaixo faz todas as perguntas e salva as respostas e o tempo de cada uma em `avaliacao/resultados/`:

```bash
docker compose exec app python -m app.avaliar                       # modelo atual
docker compose exec app python -m app.avaliar --modelo gemma3:4b    # outro modelo
docker compose exec app python -m app.avaliar --modelo qwen3:4b
```

Sem Docker: `.venv/bin/python -m app.avaliar --modelo gemma3:4b`.

Modelos que "pensam" antes de responder, como o `qwen3`, ficam bem mais rápidos com o raciocínio desligado: `THINK=false .venv/bin/python -m app.avaliar --modelo qwen3:14b`. Se o raciocínio estiver ligado, ele não aparece no chat, mas aumenta o tempo de resposta.

O modelo é baixado automaticamente se ainda não existir. Para trocar o modelo do chat, mude `CHAT_MODEL` no `.env` e rode `docker compose up -d`. Os nomes dos modelos estão em [ollama.com/library](https://ollama.com/library).

## Configurações (`.env`)

| Variável | Padrão | O que faz |
|---|---|---|
| `PORTA` | `8000` | Porta do chat no servidor (só Docker) |
| `CHAT_MODEL` | `phi4-mini` | Modelo que escreve as respostas |
| `EMBED_MODEL` | `bge-m3` | Modelo que faz a busca nos documentos |
| `TOP_K` | `5` | Quantos trechos são buscados para cada pergunta |
| `MARGEM_TRECHOS` | `0.04` | Só vão para o modelo os trechos com similaridade até esta distância do melhor trecho |
| `TEMPERATURE` | `0` | Criatividade (0 = sempre a mesma resposta, mais fiel aos trechos) |
| `NUM_CTX` | `8192` | Tamanho da janela de contexto, em tokens |
| `KEEP_ALIVE` | `60m` | Quanto tempo o modelo fica na RAM sem uso (`-1` = sempre) |
| `FILTRO_ASSUNTO` | `true` | Recusa perguntas que se parecem mais com os exemplos fora do assunto do que com a documentação. `false` desliga |
| `MARGEM_FILTRO` | `0.05` | Quanto a similaridade com os exemplos fora do assunto precisa superar a do melhor trecho da documentação para recusar |
| `LIMITE_POR_MINUTO` | `10` | Perguntas por minuto por pessoa (endereço IP). `0` = sem limite |
| `LIMITE_POR_DIA` | `200` | Perguntas por dia por pessoa |
| `LIMITE_GLOBAL_POR_MINUTO` | `120` | Perguntas por minuto somando todo mundo |
| `MODELOS_TESTE` | (vazio) | Modelos extras que podem ser escolhidos por pergunta via API, só para comparação. Ex.: `qwen3:14b,gemma3:12b` |
| `THINK` | (vazio) | `false` desliga o "raciocínio" de modelos como o `qwen3`, que fica mais rápido. Deixe vazio para modelos sem raciocínio |

## Desempenho

Sem GPU, quem define a velocidade é o processador. O tempo até a primeira palavra cresce com o tamanho do texto enviado ao modelo (os trechos mais o histórico). Se as respostas estiverem lentas:

- reduza `TOP_K` para `3`;
- use `KEEP_ALIVE=-1`, para o modelo não precisar ser carregado de novo depois de um tempo sem uso;
- rode `python -m app.avaliar` para medir o tempo médio antes e depois de cada mudança.

## Acesso pela rede

- Na rede da UFSM, o chat fica em `http://IP-DO-SERVIDOR:8000`. Talvez seja preciso liberar a porta no firewall do servidor.
- Para acesso de fora do campus, ou para colocar o chat dentro do GitHub Pages, o servidor precisa de um endereço **HTTPS**. Duas opções:
  - **Tailscale Funnel** (servidor já no Tailscale): `sudo tailscale funnel --bg 8000` publica o chat em `https://<máquina>.<tailnet>.ts.net`; `tailscale funnel status` mostra o endereço e `sudo tailscale funnel --bg 8000 off` desliga.
  - **Endereço da UFSM**: um subdomínio com HTTPS e proxy reverso configurado pelo setor de TI.
- Aberto na internet, o chat limita as perguntas por pessoa (veja `LIMITE_POR_MINUTO` e `LIMITE_POR_DIA`). O Ollama nunca fica exposto: só a aplicação fala com ele.

## Solução de problemas

- **A página diz "se preparando" por muito tempo:** veja `docker compose logs -f app`. Na primeira vez, o download dos modelos pode demorar.
- **"Não consegui consultar o modelo de IA":** confira se o Ollama está rodando (`docker compose ps` ou `systemctl status ollama`).
- **Respostas erradas sobre algum assunto:** veja quais fontes aparecem embaixo da resposta. Se a fonte certa não aparece, falta essa informação em `conhecimento/`, ou ela está escrita com palavras muito diferentes da pergunta.
