# Usando o Second Brain com a IA sem gastar à toa

O app roda sozinho, offline, sem IA nenhuma. Mas na hora que você **conversa com o Claude
sobre o seu vault** (pra organizar o inbox, mexer nas tarefas, processar uma reunião), o
jeito que você fala muda muito quanto isso custa em tempo e em tokens — o "combustível"
que cada mensagem gasta. Quem usa mal faz a IA reler o vault inteiro toda hora e a conta
sobe rápido.

Nenhuma manha aqui é complicada. Todas economizam.

## A ideia em uma frase

Cada mensagem sua faz a IA reler a conversa e os arquivos que ela precisa. Quanto mais
bagunçado, longo e vago o pedido, mais ela lê, mais demora e mais custa. Então: **fale o
essencial, aponte o lugar exato, e deixe ela trabalhar**.

## As sete manhas

### 1. Fale o essencial, corte a cerimônia
Não precisa "você poderia, por favor, quando puder...". Diga a coisa. "organiza meu
inbox", "adiciona tarefa X", "o que tá vencendo essa semana".

### 2. Combine o rumo antes, solte a execução depois
Gaste as palavras no começo pra deixar claro o que você quer. Depois deixe a IA fazer sem
corrigir cada linha. Cada rodada de "não, muda isso" faz ela reler tudo de novo.

### 3. Aponte o arquivo, não mande "procurar no vault"
"olha em tarefas.md" custa pouco. "procura no meu vault onde eu falei disso" faz a IA
abrir dezenas de arquivos atrás da coisa. Se você sabe onde está, diga onde está.

### 4. Peça o retrato pronto antes de perguntar "como estão as coisas"
O sistema imprime um resumo do momento (git, inbox, tarefas, diário) em um segundo, sem a
IA precisar ler nada:

```
python -m scripts.estado
```

Se a IA tem acesso ao seu computador, peça pra ela rodar isso primeiro.

### 5. Não peça "abre no navegador / tira print" à toa
Ver a coisa na tela é caro. Na maioria das vezes rodar os testes (`python -m pytest -q`)
já confirma que funciona. Peça verificação visual só quando for aparência (cor, layout).

### 6. Não cole textão no chat: salve num arquivo e diga o caminho
Transcrição gigante, planilha, documento longo — não despeje tudo na mensagem. Salve num
arquivo e diga "está em tal lugar". A IA lê só o pedaço que precisa.

### 7. Uma sessão, um assunto
Conversa longa que mistura cinco assuntos vira bola de neve: cada mensagem nova reprocessa
tudo. Quando mudar de assunto, comece uma conversa nova.

## Bônus: ensine a IA uma vez, não toda vez

Se a IA fica errando a mesma coisa (um estilo que você não gosta, um formato errado), peça
pra ela **anotar a regra** no `CLAUDE.md` do projeto. Da próxima vez ela já começa sabendo.

## O que NÃO precisa de IA

Boa parte do dia não precisa de IA nenhuma, e aí não tem custo. O app abre, mostra as 3
opções da "Agora", você faz, anota no diário, o Pokémon evolui. A IA entra só quando você
quer que ela organize a bagunça do inbox ou te ajude com o vault. Use quando ajuda de
verdade, não por reflexo.
