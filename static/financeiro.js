const $ = (s) => document.querySelector(s);

async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

// Tolerante a campo ausente: um total novo que a API ainda não devolve não pode
// derrubar o resumo inteiro (o render dele roda por último).
function brl(n) {
  const v = Number.isFinite(n) ? n : 0;
  const casas = Number.isInteger(v) ? 0 : 2;
  return "R$ " + v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: 2 });
}

function botaoToggle(rotulo, ligado, cor, aoClicar) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "toggle-fin" + (ligado ? " on" : "");
  b.dataset.cor = cor;
  b.textContent = ligado ? `${rotulo} ✓` : rotulo;
  b.onclick = aoClicar;
  return b;
}

function colunaValor(valor, sub) {
  const col = document.createElement("div");
  col.className = "valor-col";
  const v = document.createElement("span");
  v.className = "valor-fin";
  v.textContent = valor;
  col.appendChild(v);
  if (sub) {
    const s = document.createElement("span");
    s.className = "qtd-fin";
    s.textContent = sub;
    col.appendChild(s);
  }
  return col;
}

function montarEntrada(e) {
  const li = document.createElement("li");
  if (e.pausado) li.className = "pausado";

  const info = document.createElement("div");
  info.className = "info-fin";
  const nome = document.createElement("span");
  nome.className = "nome-fin";
  nome.textContent = e.nome;
  info.appendChild(nome);
  if (e.obs) {
    const obs = document.createElement("span");
    obs.className = "sub-fin";
    obs.textContent = e.obs;
    info.appendChild(obs);
  }
  li.appendChild(info);

  if (e.pausado) {
    li.appendChild(colunaValor("—", "pausado"));
    return li;
  }

  li.appendChild(colunaValor(brl(e.valor), null));

  const acoes = document.createElement("div");
  acoes.className = "acoes-fin";
  acoes.appendChild(botaoToggle("recebido", !!e.pago, "pago",
    () => marcarEntrada(e.id, { pago: !e.pago })));
  li.appendChild(acoes);
  return li;
}

function montarConta(c) {
  const li = document.createElement("li");
  if (c.pago) li.className = "quitada";

  const info = document.createElement("div");
  info.className = "info-fin";
  const linha = document.createElement("span");
  linha.className = "nome-linha";
  const nome = document.createElement("span");
  nome.className = "nome-fin";
  nome.textContent = c.nome;
  linha.appendChild(nome);
  if (c.parcela) {
    const p = document.createElement("span");
    p.className = "parcela";
    p.textContent = c.parcela;
    // última parcela do plano: nada vem depois
    if (c.faltante === 0) p.classList.add("ultima");
    linha.appendChild(p);
  }
  info.appendChild(linha);

  const sub = document.createElement("span");
  sub.className = "sub-fin";
  sub.textContent = c.faltante > 0 ? `restam ${brl(c.faltante)}` : "última parcela";
  info.appendChild(sub);
  li.appendChild(info);

  li.appendChild(colunaValor(brl(c.valor), null));

  const acoes = document.createElement("div");
  acoes.className = "acoes-fin";
  acoes.appendChild(botaoToggle("pago", !!c.pago, "pago",
    () => marcarConta(c.id, { pago: !c.pago })));
  li.appendChild(acoes);
  return li;
}

// Fixo é conta sem parcela: só nome, valor e o check de pago.
function montarFixo(f) {
  const li = document.createElement("li");
  const info = document.createElement("div");
  info.className = "info-fin";
  const nome = document.createElement("span");
  nome.className = "nome-fin";
  nome.textContent = f.nome;
  info.appendChild(nome);
  li.appendChild(info);

  li.appendChild(colunaValor(brl(f.valor), null));

  const acoes = document.createElement("div");
  acoes.className = "acoes-fin";
  acoes.appendChild(botaoToggle("pago", !!f.pago, "pago",
    () => marcarFixo(f.id, { pago: !f.pago })));
  li.appendChild(acoes);
  return li;
}

function montarGasto(g) {
  const li = document.createElement("li");
  const info = document.createElement("div");
  info.className = "info-fin";
  const nome = document.createElement("span");
  nome.className = "nome-fin";
  nome.textContent = g.local;
  info.appendChild(nome);
  if (g.data) {
    const sub = document.createElement("span");
    sub.className = "sub-fin";
    sub.textContent = g.data.slice(8, 10) + "/" + g.data.slice(5, 7);
    info.appendChild(sub);
  }
  li.appendChild(info);
  li.appendChild(colunaValor(brl(g.valor), null));
  return li;
}

async function marcarEntrada(id, mudancas) {
  await api(`/api/financeiro/entrada/${id}`, {
    method: "PATCH", headers: { "content-type": "application/json" },
    body: JSON.stringify(mudancas),
  });
  await carregar();
}

async function marcarConta(id, mudancas) {
  await api(`/api/financeiro/conta/${id}`, {
    method: "PATCH", headers: { "content-type": "application/json" },
    body: JSON.stringify(mudancas),
  });
  await carregar();
}

async function marcarFixo(id, mudancas) {
  await api(`/api/financeiro/fixo/${id}`, {
    method: "PATCH", headers: { "content-type": "application/json" },
    body: JSON.stringify(mudancas),
  });
  await carregar();
}

async function salvarGuardado(valor) {
  await api("/api/financeiro/mes", {
    method: "PATCH", headers: { "content-type": "application/json" },
    body: JSON.stringify({ guardado: valor }),
  });
  await carregar();
}

// Troca o valor por um input no lugar; salva no Enter ou no blur, Esc desiste.
function editarGuardado(alvo, atual) {
  // `text`, não `number`: as flechinhas de spinner atrapalham mais que ajudam,
  // e assim dá pra digitar vírgula decimal como no resto do vault.
  const inp = document.createElement("input");
  inp.type = "text";
  inp.inputMode = "decimal";
  inp.className = "valor-input";
  inp.value = atual || "";
  alvo.replaceWith(inp);
  inp.focus();
  inp.select();

  let encerrado = false;
  const fechar = async (salvar) => {
    if (encerrado) return;
    encerrado = true;
    if (salvar) await salvarGuardado(Number(inp.value.replace(",", ".")) || 0);
    else await carregar();
  };
  inp.onblur = () => fechar(true);
  inp.onkeydown = (e) => {
    if (e.key === "Enter") { e.preventDefault(); inp.blur(); }
    if (e.key === "Escape") { encerrado = true; carregar(); }
  };
}

function renderTotais(t) {
  const itens = [
    ["esperado", brl(t.esperado)],
    ["recebido", brl(t.recebido)],
    ["falta receber", brl(t.esperado - t.recebido)],
    ["recebidos", `${t.pagos}/${t.ativos}`],
  ];
  encherStats($("#totais"), itens);
}

// Caixa de baixo à esquerda: o que sai todo mês, separado do que entra.
function renderCustos(t) {
  encherStats($("#custos"), [
    ["custo fixo", brl(t.custo_fixo)],
    ["total em parcelas", brl(t.contas_a_pagar)],
  ]);
}

function encherStats(cont, itens) {
  cont.innerHTML = "";
  for (const [rot, val] of itens) {
    const d = document.createElement("div");
    d.className = "stat";
    const v = document.createElement("span");
    v.className = "stat-val";
    v.textContent = val;
    const r = document.createElement("span");
    r.className = "stat-rot";
    r.textContent = rot;
    d.appendChild(v);
    d.appendChild(r);
    cont.appendChild(d);
  }
}

// Caixa de baixo à direita: a reserva de emergência como barra de XP.
// 7 meses de custo fixo é a meta; o valor guardado é editado no clique.
function renderReserva(t) {
  const pct = t.pct_guardado || 0;
  $("#reserva-pct").textContent = pct + "%";
  $("#reserva-val").textContent = brl(t.guardado);
  $("#reserva-meta").textContent = "de " + brl(t.meta_guardado);
  $("#xp-barra").style.width = pct + "%";
  $("#reserva").classList.toggle("cheia", pct >= 100);

  const alvo = $("#reserva-val");
  alvo.title = "clique pra editar";
  alvo.onclick = () => editarGuardado(alvo, t.guardado);
}

async function carregar() {
  const d = await api("/api/financeiro");

  const ativos = d.recebimentos.filter((e) => !e.pausado);
  const pausados = d.recebimentos.filter((e) => e.pausado);
  const ul = $("#recebimentos");
  ul.innerHTML = "";
  for (const e of ativos) ul.appendChild(montarEntrada(e));
  const faltam = ativos.filter((e) => !e.pago).length;
  $("#recebimentos-conta").textContent = faltam ? `${faltam} a receber` : "tudo recebido";

  const up = $("#pausados");
  up.innerHTML = "";
  for (const e of pausados) up.appendChild(montarEntrada(e));
  $("#pausados-conta").textContent = pausados.length;
  $("#pausados-wrap").hidden = pausados.length === 0;

  const uf = $("#fixos");
  uf.innerHTML = "";
  for (const f of d.fixos) uf.appendChild(montarFixo(f));
  const fixosAbertos = d.fixos.filter((f) => !f.pago).length;
  $("#fixos-conta").textContent = fixosAbertos ? `${fixosAbertos} em aberto` : "tudo pago";

  const uc = $("#contas");
  uc.innerHTML = "";
  for (const c of d.contas) uc.appendChild(montarConta(c));
  const aPagar = d.contas.filter((c) => !c.pago).length;
  $("#contas-conta").textContent = aPagar ? `${aPagar} em aberto` : "tudo pago";

  const ug = $("#gastos");
  ug.innerHTML = "";
  for (const g of d.gastos) ug.appendChild(montarGasto(g));

  renderTotais(d.totais);
  renderCustos(d.totais);
  renderReserva(d.totais);
}

function ligarEventos() {
  $("#form-gasto").onsubmit = async (e) => {
    e.preventDefault();
    const local = $("#gasto-local").value.trim();
    if (!local) return;
    const valorTxt = $("#gasto-valor").value.trim();
    await api("/api/financeiro/gasto", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ local, valor: valorTxt || null }),
    });
    $("#gasto-local").value = "";
    $("#gasto-valor").value = "";
    await carregar();
  };
}

ligarEventos();
carregar();
