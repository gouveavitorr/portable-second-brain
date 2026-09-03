const $ = (s) => document.querySelector(s);

// rótulo curto pro badge de frequência
const FREQ = { "2x": "2x/semana", semanal: "semanal", quinzenal: "15 dias", mensal: "mensal" };

// legenda das cores: a categoria do item vira cor (tipo de Pokémon) na tela
const CATS = [
  ["proteina", "proteína"],
  ["carbo", "carbo"],
  ["salada", "salada"],
  ["fruta", "fruta"],
  ["liquido", "líquido"],
  ["molho", "molho"],
];

async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

function el(tag, cls, txt) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt !== undefined && txt !== null) e.textContent = txt;
  return e;
}

// "Arroz *ou* macarrão": o que está entre asteriscos no .md é alternativa —
// vira texto apagado pra não competir com o alimento principal.
function nomeComAlternativas(nome) {
  const span = el("span", "item-nome");
  nome.split(/\*(.+?)\*/).forEach((parte, i) => {
    if (!parte) return;
    span.appendChild(i % 2 ? el("em", "alt-item", parte) : document.createTextNode(parte));
  });
  return span;
}

// quantidade à direita, em coluna fixa e colorida pela categoria: a linha se lê
// da esquerda pra direita e os números ficam alinhados um embaixo do outro.
// `qtd_massa` vem do servidor só em grama/ml — colher, concha e xícara não vão
// pra tela: na hora de montar o prato o que vale é o peso.
function listaItens(itens) {
  const ul = el("ul", "itens-dieta");
  for (const i of itens) {
    const li = el("li");
    if (i.cat) li.dataset.cat = i.cat;
    li.appendChild(nomeComAlternativas(i.nome));
    li.appendChild(el("span", "item-qtd", i.qtd_massa || i.qtd || "—"));
    ul.appendChild(li);
  }
  return ul;
}

function montarRefeicao(r) {
  const bloco = el("article", "refeicao");

  const topo = el("div", "refeicao-topo");
  topo.appendChild(el("span", "hora-dieta", r.hora));
  topo.appendChild(el("span", "nome-refeicao", r.nome));
  if (r.kcal) topo.appendChild(el("span", "kcal-refeicao", `${r.kcal} kcal`));
  bloco.appendChild(topo);

  bloco.appendChild(listaItens(r.itens));

  // as substituições ficam fechadas: o dia se lê primeiro pela opção principal
  for (const s of r.subs) {
    const det = el("details", "sub-dieta");
    const sum = el("summary");
    sum.appendChild(el("span", null, s.titulo.toLowerCase()));
    if (s.kcal) sum.appendChild(el("span", "kcal-sub", `${s.kcal} kcal`));
    det.appendChild(sum);
    det.appendChild(listaItens(s.itens));
    bloco.appendChild(det);
  }
  return bloco;
}

function montarLegenda() {
  const ul = el("ul", "legenda-cat");
  for (const [cat, rotulo] of CATS) {
    const li = el("li", null, rotulo);
    li.dataset.cat = cat;
    ul.appendChild(li);
  }
  return ul;
}

// mercado: quantidade em destaque, sem nota — o resto está no dieta.md
function montarCompra(c) {
  const li = el("li", c.comprado ? "comprado" : null);

  const btn = el("button", "marcar-compra");
  btn.type = "button";
  btn.setAttribute("aria-label", c.comprado ? "desmarcar" : "marcar como comprado");
  btn.onclick = () => marcar(c.id, !c.comprado);
  li.appendChild(btn);

  li.appendChild(el("span", "item-nome", c.nome));
  li.appendChild(el("span", "qtd-compra", c.qtd_massa || c.qtd || "—"));
  return li;
}

async function marcar(id, comprado) {
  await api(`/api/dieta/compra/${id}`, {
    method: "PATCH", headers: { "content-type": "application/json" },
    body: JSON.stringify({ comprado }),
  });
  await carregar();
}

function montarGrupos(compras) {
  const cont = $("#compras");
  cont.innerHTML = "";
  // preserva a ordem em que os grupos aparecem no .md (do mais perecível ao mais durável)
  const ordem = [];
  const porGrupo = new Map();
  for (const c of compras) {
    const g = c.grupo || "Outros";
    if (!porGrupo.has(g)) { porGrupo.set(g, []); ordem.push(g); }
    porGrupo.get(g).push(c);
  }
  for (const g of ordem) {
    const itens = porGrupo.get(g);
    const sec = el("section", "grupo-compra");
    const h = el("h3");
    h.appendChild(el("span", null, g));
    const freq = itens[0].freq;
    if (freq) {
      const b = el("span", "freq-badge", FREQ[freq] || freq);
      b.dataset.freq = freq;
      h.appendChild(b);
    }
    sec.appendChild(h);
    const ul = el("ul", "lista-compra");
    for (const c of itens) ul.appendChild(montarCompra(c));
    sec.appendChild(ul);
    cont.appendChild(sec);
  }
}

// sinal da variação: sobe (laranja) ou desce (azul). Sem juízo de valor —
// perder gordura e perder músculo apontam pro mesmo lado.
function sinal(delta) {
  if (!delta) return "igual";
  if (delta.startsWith("-") || delta.startsWith("−")) return "desce";
  if (delta.startsWith("+")) return "sobe";
  return "igual";
}

function montarCorpo(c) {
  const sec = $("#corpo");
  if (!c || !c.grupos.length) { sec.hidden = true; return; }
  sec.hidden = false;
  $("#corpo-datas").textContent = `${c.antes} → ${c.agora}`;

  const cont = $("#medidas");
  cont.innerHTML = "";
  for (const g of c.grupos) {
    const bloco = el("section", "grupo-corpo");
    bloco.appendChild(el("h3", null, g.titulo));
    if (g.legenda) bloco.appendChild(el("p", "legenda-grupo", g.legenda));
    const ul = el("ul", "lista-medida");
    for (const m of g.medidas) {
      const li = el("li");
      li.appendChild(el("span", "nome-medida", m.nome));
      li.appendChild(el("span", "antes-medida", m.antes || ""));
      li.appendChild(el("span", "agora-medida", m.agora || ""));
      const d = el("span", "delta-medida", m.delta || "");
      d.dataset.sinal = sinal(m.delta);
      li.appendChild(d);
      ul.appendChild(li);
    }
    bloco.appendChild(ul);
    cont.appendChild(bloco);
  }

  const nota = $("#nota-corpo");
  nota.textContent = c.nota || "";
  nota.hidden = !c.nota;
}

// inbox só da dieta: "comprei o nhoque", "será que troco o kibe?". Mesmo atrito
// zero da captura da tela Agora, mas o texto cai no dieta.md em vez do inbox.
let sumirOkDieta;

function mostrarNotas(notas) {
  const ul = $("#notas-dieta");
  ul.innerHTML = "";
  for (const n of (notas || []).slice(0, 6)) ul.appendChild(el("li", null, n));
}

async function capturarDieta(e) {
  e.preventDefault();
  const campo = $("#captura-dieta-texto");
  const texto = campo.value.trim();
  if (!texto) return;
  campo.value = "";
  campo.focus();
  const ok = $("#captura-dieta-ok");
  try {
    const r = await api("/api/dieta/inbox", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    mostrarNotas(r.notas);
    ok.textContent = "anotado";
  } catch {
    campo.value = texto;
    ok.textContent = "não salvou";
  }
  ok.classList.add("visivel");
  clearTimeout(sumirOkDieta);
  sumirOkDieta = setTimeout(() => ok.classList.remove("visivel"), 1800);
}

async function carregar() {
  const d = await api("/api/dieta");
  mostrarNotas(d.notas);

  const cont = $("#refeicoes");
  cont.innerHTML = "";
  cont.appendChild(montarLegenda());
  for (const r of d.refeicoes) cont.appendChild(montarRefeicao(r));
  $("#kcal-dia").textContent = `${d.totais.kcal_dia} kcal`;

  montarGrupos(d.compras);
  const faltam = d.totais.itens - d.totais.comprados;
  $("#compras-conta").textContent = faltam ? `faltam ${faltam}` : "lista completa";

  montarCorpo(d.corpo);
}

$("#form-captura-dieta").onsubmit = capturarDieta;
carregar();
