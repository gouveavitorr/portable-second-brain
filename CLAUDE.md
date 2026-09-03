# CLAUDE.md

O que uma sessão nova precisa saber antes de encostar em qualquer coisa aqui.

## Primeira sessão desta pessoa?

Se `second_brain/.primeira-vez` **não existe**, provavelmente é a primeira vez que o dono
deste computador usa o Second Brain. Antes de mais nada, ofereça a introdução: invoque a
skill **`bem-vindo`**, que apresenta o app, conecta o que precisa e ajuda a semear o vault
com a vida real da pessoa. (Se ela pediu outra coisa, atenda primeiro; só ofereça se topar.)

## Comece por aqui

```bash
python -m scripts.estado
```

Imprime o retrato do momento: git, inbox, diário, recorrentes vencidas, áreas. É offline,
roda em um segundo e não escreve nada. Rode antes de perguntar "em que pé as coisas estão".

Se a tarefa mexer no vault, leia `second_brain/index.md` — ele explica o fluxo
(inbox → triagem → tarefas → tela "Agora" → diário) e, mais importante, **por que** a
separação existe. Não reorganize o vault sem ler aquilo primeiro.

## O que é este repositório

Duas metades na mesma pasta:

| Metade | Onde | O que é |
|---|---|---|
| **O app** | `app/`, `static/`, `tests/`, `scripts/` | FastAPI local, anti-procrastinação. A tela "Agora" sugere 3 tarefas; um Pokémon evolui conforme você conclui. Ver `README.md`. |
| **O vault** | `second_brain/` | Os dados, em `.md`/`.json`, abríveis no Obsidian. **Fonte da verdade.** |

O app **lê** o vault. Quando os dois discordam, o vault ganha. O app roda **offline** — não
há chamada à API de nenhum LLM em runtime; quem usa o Claude são as skills, via Claude Code.

## Como verificar

**Por padrão: `pytest`, não o browser.**

```bash
python -m pytest -q
```

Não suba o app nem use o Browser pane pra "conferir visualmente" a menos que a pessoa peça
("abre no navegador", "tira um print"). Verificação visual à toa queima token e raramente
agrega em mudança de CSS/HTML.

O dono roda a instância dele com `python abrir.py`. Mudança em `.py` só vale depois de
reiniciar; estáticos recarregam sozinhos (`Cache-Control: no-cache` em `/` e `/static`).

## Desenho das telas

- **Coluna única, densa.** A largura é o recurso escasso; use pra achatar blocos repetidos,
  não pra criar colunas paralelas. Nada de trilho lateral.
- **O número lidera a linha.** A quantidade acionável vem primeiro e em destaque, o nome
  depois. Cards baixos e densos.
- **Cor é categoria/custo**, sempre na paleta dos tipos de Pokémon (na dieta: proteína =
  fogo, carbo = elétrico, salada = grama, fruta = fada, líquido = gelo, molho = venenoso).
  Fora o companheiro, quase tudo é cinza; cor só onde carrega informação.
- **Texto de apoio não vai pra tela.** Nota, receita, "como fazer" ficam no `.md`.

## Skills

| Skill | Quando |
|---|---|
| `bem-vindo` | primeira sessão da pessoa: introdução + configuração |
| `triagem` | processar `inbox.md` e promover próximos passos pro `tarefas.md` |
| `reuniao` | processar reunião do Granola e destilar em tarefas + anotação |

**O Granola** (reuniões) é opcional. Se as ferramentas do MCP não responderem, o usuário
precisa autorizá-lo numa sessão interativa (`/mcp` no Claude Code, ou nas conexões do
claude.ai). Você não faz o OAuth; oriente e siga.

## Convenções de trabalho

- **Escreva em português**, direto e sem cerimônia.
- **Commits em português**, no padrão `área: o que mudou` (ex.: `financeiro: nova entrada`,
  `tela: card mais denso`). O trabalho acontece na `main`.
- **Aprenda com o dono sem ele pedir.** Quando ele corrigir ou ajustar algo que vale além
  do momento, grave a regra no arquivo-dono ou aqui no `CLAUDE.md` — pra não gastar a mesma
  correção de novo. Não deixe um insight morrer porque ninguém mandou salvar.
- **CLAUDE.md roteia, não duplica.** Regra que tem arquivo-dono entra aqui só como ponteiro.
- **Credenciais e dados nunca vazam.** Este é um sistema pessoal; não commite dado sensível
  nem exponha o vault de ninguém.
