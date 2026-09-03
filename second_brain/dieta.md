# 🥗 Dieta

**O app lê este arquivo.** É pra caber um plano alimentar (o seu, ou o que um nutri te
passar) num formato que a tela `/dieta` mostra: o dia à esquerda, a lista de mercado da
semana à direita, e a avaliação do corpo embaixo.

Formato:
- Refeições: `### HH:MM · Nome`, itens em `- nome | qtd:… | kcal:… | cat:…`, e `>` pra
  observação. `cat` só pinta o item na tela: `proteina`, `carbo`, `salada`, `fruta`,
  `liquido`, `molho`. Uma refeição pode ter `#### Substituição 1` com opções equivalentes.
- `## Compras`: `freq:` diz de quanto em quanto tempo repor; `comprado:` guarda quando
  você marcou na tela.
- `## Corpo`: avaliação — `antes` é a medição anterior, `agora` a mais recente.

> Tudo abaixo é exemplo, pra tela não abrir vazia. **Troque pelo seu plano.**

## Refeições

### 08:00 · Café da manhã
- Ovo mexido | qtd:2 unidades | kcal:150 | cat:proteina
- Pão integral | qtd:1 fatia | kcal:70 | cat:carbo
- Café com leite | qtd:200 ml | kcal:80 | cat:liquido

#### Substituição 1
- Iogurte natural | qtd:150 g | kcal:90 | cat:liquido
- Banana | qtd:1 unidade | kcal:90 | cat:fruta
> Bata tudo com um pouco de aveia se quiser um shake.

### 12:30 · Almoço
- Arroz | qtd:4 col. sopa | kcal:200 | cat:carbo
- Frango grelhado | qtd:150 g | kcal:240 | cat:proteina
- Salada de folhas | qtd:1 prato | kcal:30 | cat:salada

### 19:30 · Jantar
- Sopa de legumes | qtd:1 prato fundo | kcal:180 | cat:salada
- Ovo cozido | qtd:1 unidade | kcal:75 | cat:proteina

## Compras

### Semanal
- Ovos | qtd:1 dúzia | nota:café + jantar | freq:semanal | id:d001
- Frango peito | qtd:1 kg | nota:almoço | freq:semanal | id:d002
- Folhas e legumes | qtd:o que for da estação | nota:salada e sopa | freq:semanal | id:d003
- Banana | qtd:7 unidades | nota:1/dia | freq:semanal | id:d004

### Despensa — mensal
- Arroz | qtd:1 pacote | nota:almoço | freq:mensal | id:d005
- Café | qtd:1 pacote | nota:manhã | freq:mensal | id:d006

## Corpo

Preencha quando tiver uma avaliação. Exemplo:
datas | antes:01/01/2026 | agora:01/06/2026

### Composição
- Peso | antes:80,0 kg | agora:78,5 kg | delta:-1,5
- % de gordura | antes:24,0% | agora:22,5% | delta:-1,5
