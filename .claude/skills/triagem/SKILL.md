---
name: triagem
description: Use quando o usuário pedir triagem, quiser processar o inbox do second brain, organizar o braindump, ou atualizar tarefas.md a partir do que ele despejou. Lê second_brain/inbox.md, converte em tarefas acionáveis, distribui nos projetos/áreas e promove os próximos passos para tarefas.md.
---

# Triagem do Inbox

Transforma o braindump livre de `second_brain/inbox.md` em tarefas que o app entende.

**Anuncie no início:** "Usando a skill triagem para processar o inbox."

## Princípio

O usuário tem TDAH. O sistema inteiro existe para combater **paralisia de decisão**. Sua
tarefa aqui é absorver a bagunça para que a tela "Agora" continue mostrando 3 opções
curadas. Se você empurrar o braindump para `tarefas.md`, você devolve a paralisia e
quebra o produto.

Nunca invente punição, streak, cobrança ou decaimento. Nada de "você está atrasado".

## Processo

### 1. Ler o estado atual

Leia, nesta ordem:

- `second_brain/inbox.md` — o que precisa ser triado
- `second_brain/tarefas.md` — o que o app já vê (para não duplicar)
- `second_brain/index.md` — o mapa
- os arquivos de `second_brain/projetos/` e `second_brain/areas/` relevantes ao inbox

### 2. Classificar cada item do inbox

Para cada coisa despejada, decida **o que ela é**. Esta é a etapa que importa:

| Se é... | Vai para | Regra |
|---|---|---|
| **Tarefa** — dá pra começar hoje | `tarefas.md` | precisa de `passo:` concreto |
| **Projeto** — várias tarefas, tem fim | `projetos/<slug>.md` | promova só o próximo passo |
| **Área** — contínuo, nunca fica pronto | `areas/<slug>.md` | vira recorrente ou nada |
| **Objetivo** — longo prazo, não começável | `objetivos.md` | nunca vai pra `tarefas.md` |
| **Recorrente** — se repete | `tarefas.md` com `repete:` | registre também em `recorrentes.md` |
| **Referência** — link, ideia, anotação | nota do projeto/área | não é tarefa |
| **Lixo** — não serve mais | descarte | mencione o que descartou |

Na dúvida entre tarefa e projeto: se você não consegue escrever o `passo:` numa frase,
é projeto.

### 3. Primar as tarefas

Toda linha promovida a `tarefas.md` precisa de:

- **`passo:`** — a primeira ação física, tão pequena que dá vergonha não fazer.
  "abrir o doc e escrever a 1ª frase", não "escrever o relatório".
  Esta é a parte mais importante da triagem inteira: é o que vence a inércia.
- **`prioridade:`** — alta|media|baixa. Seja honesto; se tudo é alta, nada é.
- **`energia:`** — leve|pesada. Governa o XP e o "modo fácil".
- **`min:`** — estimativa em minutos. Alimenta o filtro de janela do calendário.
- **`repete:`** — só se for recorrente.

Não invente `prazo:` que o usuário não deu. Prazo falso vira ansiedade.

### 4. Reescrever para ser começável

Um item vago não vira tarefa — vira uma tarefa de *destravar*.

- "Continuar desenvolvendo o site" → não é acionável. Vire
  "Listar o que falta pro site estar pronto | passo: abrir o projeto e escrever 5 linhas".
- "Me alimentar bem" → não é tarefa, é resultado. O que dá pra fazer é
  "Cozinhar comida pra semana | repete:semanal".

### 5. Aplicar

- Escreva nos arquivos de destino, preservando o que já existe.
- **Esvazie a seção "Pra triar" do `inbox.md`** — deixe só o cabeçalho e o marcador.
- Mantenha `tarefas.md` entre ~15 e 25 linhas. Se passar disso, o app volta a paralisar:
  devolva as menos maduras para o backlog do projeto.
- Atualize o `**Próximo passo:**` no topo de cada arquivo de projeto tocado.

### 6. Relatar

Diga em prosa curta:

- quantos itens entraram e o que virou o quê;
- o que você **não** promoveu e por quê (ex.: vago demais, virou backlog);
- o que você descartou;
- qualquer coisa que precise de decisão do usuário.

Nunca invente que triou algo que não estava no inbox.

## Verificação

Depois de escrever, rode:

```bash
python -c "
from app.tasks import parse_tarefas, Tarefa
from app.storage import ler_texto
from app.engine import escolher_agora
from datetime import date
ts = [e for e in parse_tarefas(ler_texto('second_brain/tarefas.md')) if isinstance(e, Tarefa)]
print(len(ts), 'tarefas')
print('sem passo:', [t.titulo for t in ts if not t.passo and not t.repete])
for t in escolher_agora(ts, hoje=date.today()):
    print(' ->', t.titulo, '|', t.passo)
"
```

Confirme que o parser leu tudo e que as 3 sugeridas fazem sentido. Se alguma tarefa
não-recorrente estiver sem `passo:`, ela não está pronta — volte e escreva o passo.
