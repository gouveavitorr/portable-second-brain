# 🧠 Second Brain

Painel do sistema. Se você não sabe onde algo vai, vai no [[inbox]].

## O fluxo

```
você despeja  →  inbox.md
                    ↓  /triagem (no Claude Code)
                  areas/            (backlog do que é contínuo; o app ignora)
                    ↓  promoção dos próximos passos
                 tarefas.md          ← o app lê SÓ isto
                    ↓
              tela "Agora": 3 opções pra começar
                    ↓
              você faz algo (da lista ou não)
                    ↓  campo "Acabei de fazer"
                 diario.md           ← só cresce, com horário
```

O `inbox` e o `diario` são espelhos: um é o que você **vai** fazer, o outro é o que você
**já** fez. Anotar no diário dá XP igual concluir tarefa. A `/triagem` não encosta nele.

Você só precisa fazer duas coisas: **despejar no inbox** e **rodar `/triagem` de vez em
quando**. O resto o Claude faz.

## Os arquivos

| Arquivo | O que é | O app lê? |
|---|---|---|
| [[inbox]] | braindump livre, sem formato | não |
| [[tarefas]] | próximos passos primados — a fila do dia | **sim** |
| [[diario]] | o que você fez, com horário — o app escreve, você lê | **sim** (escreve) |
| [[recorrentes]] | o que se repete (diário/semanal/mensal) | via `tarefas.md` |
| [[objetivos]] | longo prazo — dá direção, não vira tarefa | não |
| [[financeiro]] | o que entra, contas do mês, gastos, reserva | **sim** |
| [[dieta]] | plano alimentar, lista de mercado e avaliação do corpo | **sim** |
| `areas/` | o que é contínuo e nunca fica "pronto" | não |

## As telas

| Tela | O que faz |
|---|---|
| `/` — Agora | 3 opções pra começar, recorrentes, diário, "processar inbox" |
| `/dieta` | o dia à esquerda, mercado da semana à direita, o corpo embaixo |
| `/financeiro` | o que entra à esquerda, o que sai à direita, a reserva de emergência |
| `/objetivos` | os objetivos de longo prazo e o que está empurrando cada um |

## Por que a separação existe

O app foi feito pra combater paralisia de decisão mostrando **3 opções curadas**. Se ele
lesse o braindump inteiro, ele te devolveria a paralisia — foi o problema que ele resolve.

Por isso:

- **Objetivo** não é tarefa. "Aprender violão" não tem botão *feito*.
- **Área** não é tarefa. "Me alimentar bem" nunca fica pronto — vira recorrentes.
- **Tarefa** é o que você consegue começar hoje, e sabe qual é a primeira frase.

O companheiro Pokémon cresce conforme você conclui tarefas e anota no diário. É o único
ponto de cor da tela: o resto é cinza de propósito, pra não competir pela sua atenção.
