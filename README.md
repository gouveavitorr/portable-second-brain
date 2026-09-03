# Second Brain

Um organizador pessoal anti-procrastinação, feito pra quem trava no "por onde eu começo?".

Abre no navegador e mostra a tela **"Agora"**: em vez da sua lista inteira te encarando,
ele sugere **3 tarefas** pra você escolher uma e começar. Cada tarefa já vem com o
**primeiro passo** escrito. Conforme você conclui coisas (e anota o que fez), um **Pokémon
companheiro** ganha XP e evolui — o único ponto de cor da tela, de propósito.

Também tem tela de **dieta** (o dia, a lista de mercado, a evolução do corpo),
**financeiro** (o que entra, o que sai, e uma reserva de emergência que também vira meta
com Pokémon) e **objetivos** de longo prazo.

Tudo são arquivos `.md` numa pasta (`second_brain/`), que você abre também no
[Obsidian](https://obsidian.md) se quiser. **Roda 100% offline**, sem conta, sem chave de
API, sem nuvem. Seus dados ficam no seu computador.

## Rodar

Precisa de [Python 3.12+](https://www.python.org/downloads/).

```bash
pip install -r requirements.txt
python abrir.py
```

Ele sobe o servidor e abre a tela no navegador. Pra fechar, use o botão de desligar na
própria tela.

> Uma versão empacotada (um `.exe` que você baixa e clica, sem instalar Python) está no
> forno. Por enquanto é rodar do código como acima.

## Usar com o Claude (opcional)

O app funciona sozinho. Mas se você tem o [Claude Code](https://claude.com/claude-code),
ele lê e organiza o vault pra você: joga qualquer coisa no `second_brain/inbox.md` e peça
`/triagem` — o Claude transforma o braindump em tarefas curadas com passo concreto.

Na **primeira vez** que você abrir o Claude Code nesta pasta, peça pra ele te ajudar a
começar (ou é só dizer "oi"): ele roda a introdução, te explica o sistema e ajuda a montar
o vault com a sua vida.

Pra gastar menos tempo e tokens conversando com a IA, leia
[docs/usando-com-claude.md](docs/usando-com-claude.md).

## Como está organizado

- `app/` — o servidor (FastAPI) e a lógica.
- `static/` — as telas (HTML/CSS/JS).
- `second_brain/` — **os seus dados**, em `.md`/`.json`. É a fonte da verdade; o app lê daqui.
- `tests/` — a rede de segurança. `python -m pytest -q`.

O `second_brain/index.md` explica o fluxo e por que a separação inbox → tarefas existe.
