# 💰 Financeiro

**O app lê este arquivo.** Cada linha é uma entrada; os campos vão depois do `|`.

Quatro seções:
- **`## Recebimentos`** — o que entra no mês (salário, um contrato, um cliente, uma
  mesada). `pausado:sim` é uma entrada que não vale este mês. Campos: `valor` (R$ no
  mês) · `pago` · `pausado` · `obs`.
- **`## Fixos`** — gasto que se repete todo mês e nunca acaba. É a soma dos Fixos que
  responde "quanto eu preciso por mês pra viver". Campos: `valor` · `pago`.
- **`## Contas`** — parcelamento com fim marcado (diferente de Fixo). `faltante` é o
  saldo das parcelas *futuras*, não o que falta neste mês — quem diz isso é o `pago`.
  Campos: `parcela` · `valor` · `faltante` · `pago`.
- **`## Gastos`** — o que você gastou (avulso). Campos: `data` · `valor`.

A linha `## Mês` guarda quanto você já tem na **reserva de emergência** (o campo
`guardado`). A meta da reserva é o custo fixo × 7.

> Números de exemplo. **Apague e ponha os seus quando começar.**

## Recebimentos

- Salário | valor:3500 | id:r001
- Freela | valor:800 | obs:varia mês a mês | id:r002

## Fixos

- Aluguel | valor:1200 | id:f001
- Internet | valor:100 | id:f002
- Luz | valor:150 | id:f003

## Contas

- Celular novo | parcela:2/10 | valor:180 | faltante:1440 | id:c001

## Gastos

- Mercado | data:2026-09-01 | valor:220 | id:g001

## Mês

- guardado | valor:500
