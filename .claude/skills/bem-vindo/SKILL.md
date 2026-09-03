---
name: bem-vindo
description: Use na PRIMEIRA sessão de uma pessoa neste Second Brain — quando o arquivo second_brain/.primeira-vez ainda não existe, ou quando a pessoa pede pra "começar", "configurar", "me ajuda a montar isso". Faz a introdução ao app, conecta o que precisa (MCPs) e ajuda a semear o vault com a vida real da pessoa.
---

# Boas-vindas ao Second Brain

Esta skill roda **uma vez**, quando alguém acabou de ganhar uma cópia do Second Brain e
abre o Claude Code aqui pela primeira vez. Ela transforma um template morto no sistema
**daquela pessoa**.

**Anuncie no início:** "Parece que é a sua primeira vez aqui — deixa eu te apresentar o
Second Brain antes de qualquer coisa."

## Como saber que é a primeira vez

No começo de qualquer sessão, se `second_brain/.primeira-vez` **não existe**, é provável
que seja a primeira sessão desta pessoa. Confirme com ela numa frase ("é a primeira vez
que você usa isto?") antes de entrar no fluxo — ela pode só ter apagado o arquivo.

Se a pessoa pediu qualquer outra coisa, faça o que ela pediu primeiro; só ofereça a
introdução se ela topar. Não sequestre a sessão.

## O que é o app, em três frases

Diga isto com suas palavras, curto:

1. O app abre no navegador (rode `python abrir.py` ou o `iniciar.bat`) e mostra a tela
   **"Agora"**: 3 tarefas curadas pra você escolher uma e começar — feito pra vencer a
   paralisia de "por onde eu começo?".
2. Conforme você conclui tarefas e anota o que fez, um **Pokémon companheiro** ganha XP e
   evolui. É o único ponto de cor da tela, de propósito.
3. Tudo é `.md` numa pasta (`second_brain/`), roda **offline**, sem conta e sem chave. O
   Claude (você, aqui) entra só quando a pessoa quer organizar a bagunça do inbox ou
   mexer no vault.

## O fluxo que ela precisa entender

Só duas coisas: **despejar no `inbox.md`** (do jeito que sair) e, de vez em quando, pedir
`/triagem` — que lê o inbox e vira tarefas curadas no `tarefas.md`, que é o que a tela lê.
Aponte `second_brain/index.md` pra ela ver o desenho inteiro.

## Passos da configuração

Faça um de cada vez, perguntando antes de escrever qualquer coisa no vault.

1. **Granola (opcional).** Pergunte se ela usa o Granola pra gravar reuniões. Se usar,
   explique que o MCP já está declarado em `.mcp.json`, mas precisa ser autorizado numa
   sessão interativa (`/mcp` no Claude Code, ou nas conexões do claude.ai). Depois de
   conectado, a skill `/reuniao` processa as reuniões dela. Se ela não usa, siga em frente
   — nada quebra.

2. **Semear o vault com a vida real dela.** O template vem com exemplos ("apague quando
   começar"). Ofereça trocar por coisas de verdade, perguntando pouco e escrevendo você:
   - **Tarefas:** peça 3 a 5 coisas que ela precisa fazer nos próximos dias e escreva em
     `tarefas.md` no formato certo (com `passo:` concreto, `energia`, `prioridade`). Use a
     `/triagem` como referência de como primar.
   - **Recorrentes:** pergunte 2 ou 3 hábitos/rotinas (remédio, treino, ler) e adicione com
     `repete:`.
   - **Financeiro** (se ela quiser): pergunte as entradas do mês, os fixos e uma reserva
     inicial, e preencha `financeiro.md`. Não invente números.
   - **Dieta** (se ela quiser): só se ela tiver um plano. Senão, deixe o exemplo ou esvazie.
   - **Objetivos:** 1 ou 2 direções de longo prazo, se ela tiver.
   Apague os exemplos das seções que você preencher.

3. **Companheiro inicial.** O primeiro Pokémon é o topo de `pokemons.md` (bulbasaur). Se
   ela quiser outro inicial, é só reordenar a lista — o de cima é o que nasce.

## Fechar

Quando terminar (ou quando ela quiser parar), **crie o marcador** pra não repetir a
introdução na próxima sessão:

```bash
python -c "from pathlib import Path; Path('second_brain/.primeira-vez').write_text('ok\n', encoding='utf-8')"
```

Diga o que fazer agora: abrir o app (`python abrir.py`), fazer a primeira tarefa, ver o
companheiro ganhar XP. E que, quando a cabeça encher, é só despejar no inbox e pedir
`/triagem`.

Leia `docs/usando-com-claude.md` se ela perguntar como não gastar tokens à toa.
