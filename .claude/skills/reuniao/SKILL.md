---
name: reuniao
description: Use quando a pessoa pedir pra processar uma reunião do Granola, puxar a transcrição/notas de uma reunião, ou transformar o que foi dito numa reunião em tarefas e anotações no vault. Lê as reuniões pelo MCP do Granola e destila o resultado em tarefas (inbox) e numa nota de área.
---

# Processar reunião do Granola

Pega o que aconteceu numa reunião gravada no Granola e transforma na parte que importa:
**ações viram tarefas** e **decisões/contexto viram anotação**. O resto (a transcrição
crua) fica no Granola — o vault guarda só o destilado.

**Anuncie no início:** "Usando a skill reuniao para processar a reunião no Granola."

## Antes de tudo

O MCP do Granola precisa estar conectado. Se as ferramentas do Granola não responderem,
peça pra pessoa autorizar o Granola numa sessão interativa (`/mcp` no Claude Code, ou nas
conexões do claude.ai) e pare por aqui — você não faz o OAuth.

## Processo

### 1. Achar a reunião

- Se a pessoa nomeou a reunião, ache pelo título (`list_meetings` / `query_granola_meetings`).
- Se não, liste as reuniões recentes e pergunte qual (ou confirme a última). Não processe
  tudo de uma vez sem ela pedir.

### 2. Ler

Puxe a transcrição e as notas (`get_meeting_transcript`). Leia pra entender: quem pediu o
quê, o que ficou decidido, o que ficou em aberto.

### 3. Destilar

Separe em três baldes:

| O que é | Vai pra |
|---|---|
| **Ação** — algo que a pessoa precisa fazer | uma linha no `inbox.md` (a `/triagem` prima depois) |
| **Decisão / contexto** que vale guardar | uma nota numa área (`areas/<assunto>.md`) |
| **Resto** (papo, transcrição) | fica no Granola, não entra no vault |

Regras:
- Ação vira **uma frase de tarefa acionável** ("Mandar a proposta revisada pro cliente"),
  não a transcrição da fala. Jogue no fim do `inbox.md`, sob o marcador.
- Não invente prazo que não foi dito.
- Se a reunião é recorrente e já existe uma área pra ela (um cliente, um time, um projeto),
  adicione a nota lá. Senão, pergunte se vale criar uma área nova (`areas/_modelo.md` é o
  esqueleto) antes de criar.
- **Não** copie dado sensível de terceiros que não precisa estar no vault.

### 4. Confirmar e escrever

Mostre pra pessoa, em prosa curta, o que você tirou (as ações e as decisões) **antes de
escrever**. Só depois do ok, escreva no `inbox.md` e na nota de área.

### 5. Relatar

Diga quantas ações entraram no inbox e onde a nota foi parar. Sugira rodar `/triagem`
pra primar as ações que acabaram de cair no inbox.
