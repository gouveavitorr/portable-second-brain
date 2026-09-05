# Empacotar o Second Brain num .exe

Guia pra **você** (quem mantém o projeto) gerar o executável que os outros vão baixar e
clicar. O usuário final não vê nada disto — ele recebe só o `Second Brain.exe`.

## O que o .exe faz de diferente

- **Não precisa de Python** nem de `pip`: o interpretador vai dentro do exe (PyInstaller).
- **Roda offline**: os sprites do Pokémon estão embutidos (`static/pokemon/`), então nada
  toca a PokeAPI em runtime.
- **O vault nasce em `Documentos\SecondBrain`** na primeira execução (a semente é copiada
  de dentro do exe), não na pasta do exe — que pode ser read-only.
- **Sem janela de console**: ao clicar, abre direto o navegador; o log fica em
  `Documentos\SecondBrain\.servidor.log` se algo não subir.

## Passo a passo

1. **Baixe os sprites** (uma vez, com internet). Sem isto o app não roda offline:

   ```
   python -m scripts.baixar_sprites
   ```

   Isso versiona `static/pokemon/*.png` e `static/pokemon/cadeias.json`. Rode de novo se
   mudar o pool (`second_brain/pokemons.md`) ou as metas do financeiro.

2. **Rode o build:**

   ```
   build.bat
   ```

   Ele limpa o lixo de runtime do vault semente, instala o PyInstaller e empacota. Sai em
   `dist\Second Brain.exe` (arquivo único).

3. **Teste num lugar sem Python.** O ponto todo é rodar onde não há Python instalado. O
   mais perto disso: copie o exe pra uma pasta qualquer (ou outro perfil de usuário) e dê
   dois cliques. Tem que abrir a tela "Agora", concluir uma tarefa e ver o Pokémon ganhar
   XP — tudo com a internet desligada.

## Ícone (opcional)

Largue um `build\icone.ico` no repo antes de buildar e o exe usa ele. Sem isso, fica o
ícone padrão do PyInstaller. (Pra converter um PNG num .ico dá pra usar o Pillow ou
qualquer conversor online.)

## O aviso do SmartScreen

Um .exe não assinado dispara no Windows a tela azul **"O Windows protegeu o computador"**.
Não é vírus nem erro — é só o exe não ter uma assinatura digital (que custa caro por ano).
Não trava nada; some clicando em **"Mais informações" → "Executar assim mesmo"**.

Como a gente distribui pra irmão/amigo, não vale assinar. **Mande junto com o exe** um
recado curto avisando disso, ou o print do "Executar assim mesmo" — senão a pessoa acha
que quebrou e desiste na porta.

## Atualizar depois

Não tem auto-update. Versão nova = gerar o exe de novo e a pessoa baixar por cima. Pro
público que a gente tem, tá de bom tamanho — o vault dela em `Documentos\SecondBrain` não
é tocado, só o exe troca.
