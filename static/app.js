const $ = (s) => document.querySelector(s);
let offset = 0;

const ENERGIAS = ["leve", "média", "pesada"];

async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    // o FastAPI embrulha o erro em {"detail": "..."}; a tela quer só o recado
    const corpo = await r.text();
    let msg = corpo;
    try { msg = JSON.parse(corpo).detail ?? corpo; } catch { /* não era json */ }
    throw new Error(msg);
  }
  return r.status === 204 ? null : r.json();
}

// O .md é editado à mão e a energia pode vir vazia, sem acento ou torta.
// A tela sempre mostra uma das três — média é o padrão, igual no motor.
function normEnergia(valor) {
  const v = (valor || "").trim().toLowerCase();
  if (v === "media") return "média";
  return ENERGIAS.includes(v) ? v : "média";
}

function dataHoje() {
  const d = new Date();
  return d.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "short" });
}

async function carregarPokemon() {
  const p = await api("/api/pokemon");
  const sprite = $("#sprite");
  const antigo = sprite.src;
  const novo = p.sprite || "";
  sprite.alt = p.nome;
  $("#pk-nome").textContent = p.nome;
  $("#pk-xp").textContent = `${p.xp}/${p.xp_para_evoluir} XP`;
  $("#barra-xp").style.width = Math.min(100, (p.xp / p.xp_para_evoluir) * 100) + "%";

  // trocou de sprite = evoluiu (ou virou um companheiro novo): a cena da pokébola.
  // Na primeira carga `antigo` é vazio, então só troca sem teatro.
  if (antigo && novo && antigo !== novo) {
    evoluir(sprite, novo);
  } else {
    sprite.src = novo;
  }
}

// A pokébola tradicional, desenhada em SVG pra ficar nítida no tamanho do companheiro.
function criarPokebola() {
  const cx = document.createElement("div");
  cx.className = "evo-pokebola";
  cx.innerHTML = `
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs><clipPath id="pb-corte"><circle cx="50" cy="50" r="47"/></clipPath></defs>
      <g clip-path="url(#pb-corte)">
        <rect x="0" y="0" width="100" height="50" fill="#E3350D"/>
        <rect x="0" y="50" width="100" height="50" fill="#F0F0F0"/>
        <rect x="0" y="45" width="100" height="10" fill="#202020"/>
      </g>
      <circle cx="50" cy="50" r="47" fill="none" stroke="#202020" stroke-width="5"/>
      <circle cx="50" cy="50" r="15" fill="#202020"/>
      <circle cx="50" cy="50" r="10" fill="#F7F7F7" stroke="#202020" stroke-width="2"/>
    </svg>`;
  return cx;
}

// A coreografia: o pokémon vira bola → ela chacoalha e respira → brilha dourado → abre
// num flash e revela o novo. Os tempos casam com as animações declaradas no CSS.
function evoluir(sprite, novoSrc) {
  sprite.classList.remove("ganhou", "cutucou");
  const r = sprite.getBoundingClientRect();
  const ball = criarPokebola();
  ball.style.left = r.left + "px";
  ball.style.top = r.top + "px";
  ball.style.width = r.width + "px";
  ball.style.height = r.height + "px";
  document.body.appendChild(ball);

  sprite.classList.add("evo-sumir");        // pokémon encolhe e some
  ball.classList.add("evo-surgir");         // a bola surge no lugar
  setTimeout(() => ball.classList.add("evo-chacoalhar"), 430);
  setTimeout(() => ball.classList.add("evo-dourado"), 1660);
  setTimeout(() => {
    sprite.src = novoSrc;
    sprite.classList.remove("evo-sumir");
    sprite.classList.add("evo-revelar");    // o novo pokémon aparece num flash
    ball.classList.add("evo-abrir");        // a bola clareia e some
  }, 2160);
  setTimeout(() => {
    ball.remove();
    sprite.classList.remove("evo-revelar");
  }, 2950);
}

function brl(n) {
  const v = Number.isFinite(n) ? n : 0;
  const casas = Number.isInteger(v) ? 0 : 2;
  return "R$ " + v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: 2 });
}

// ---- Pokémons de meta (reserva à esquerda, Canadá à direita) ----
// Cada um cresce de tamanho conforme o guardado: pixelzinho a 0%, cheio a 100%. É
// menor que o companheiro de propósito — ele continua sendo o herói. O marcador
// vertical à esquerda repete o quanto, e o número de R$ lidera embaixo. Clicar no
// número registra um DEPÓSITO: o valor digitado é somado ao guardado (só sobe).
const META_MIN = 36;   // px do sprite a 0%
const META_MAX = 120;  // px do sprite a 100% (< 288 do companheiro)
const META_SEL = { reserva: "#meta-reserva", canada: "#meta-canada" };

function ladoSprite(pct) {
  return Math.round(META_MIN + (META_MAX - META_MIN) * (Math.max(0, Math.min(100, pct)) / 100));
}

function montarMeta(m) {
  const corpo = document.createElement("div");
  corpo.className = "meta-corpo";

  const topo = document.createElement("div");
  topo.className = "meta-topo";

  const trilho = document.createElement("div");
  trilho.className = "meta-trilho";
  if (m.pct >= 100) trilho.classList.add("cheia");
  const preench = document.createElement("div");
  preench.className = "meta-preench";
  preench.style.height = m.pct + "%";
  trilho.appendChild(preench);
  topo.appendChild(trilho);

  const cx = document.createElement("div");
  cx.className = "meta-sprite-cx";
  const img = document.createElement("img");
  img.className = "meta-sprite";
  img.src = m.sprite || "";
  img.alt = m.nome || m.rotulo;
  img.style.width = img.style.height = ladoSprite(m.pct) + "px";
  cx.appendChild(img);
  topo.appendChild(cx);
  corpo.appendChild(topo);

  const val = document.createElement("span");
  val.className = "meta-val";
  val.textContent = brl(m.guardado);
  val.title = "clique pra registrar um depósito";
  val.onclick = () => abrirDeposito(m.chave, val);
  corpo.appendChild(val);

  const rot = document.createElement("span");
  rot.className = "meta-rot";
  rot.textContent = m.rotulo;
  corpo.appendChild(rot);

  return corpo;
}

function pintarMeta(sel, m) {
  const cx = $(sel);
  cx.innerHTML = "";
  if (m) cx.appendChild(montarMeta(m));
}

async function carregarMetas() {
  const d = await api("/api/metas");
  const por = Object.fromEntries(d.metas.map((m) => [m.chave, m]));
  pintarMeta(META_SEL.reserva, por.reserva);
  pintarMeta(META_SEL.canada, por.canada);
}

// O depósito atualiza o card no lugar (não recria), pra as transições animarem o
// crescimento do sprite e a subida da barra. Por cima, o drama: o bicho brilha
// dourado, a barra pulsa e um "+R$X" sobe flutuando.
function animarDeposito(sel, m, ganho) {
  const corpo = $(sel).querySelector(".meta-corpo");
  if (!corpo) return pintarMeta(sel, m);   // sem card ainda: só pinta

  const img = corpo.querySelector(".meta-sprite");
  const preench = corpo.querySelector(".meta-preench");
  const trilho = corpo.querySelector(".meta-trilho");
  const val = corpo.querySelector(".meta-val");

  img.style.width = img.style.height = ladoSprite(m.pct) + "px";  // cresce (transição)
  preench.style.height = m.pct + "%";                             // enche (transição)
  trilho.classList.toggle("cheia", m.pct >= 100);
  val.textContent = brl(m.guardado);

  corpo.classList.remove("deposito"); void corpo.offsetWidth; corpo.classList.add("deposito");
  trilho.classList.remove("brilho"); void trilho.offsetWidth; trilho.classList.add("brilho");

  // "+R$X" subindo por cima do sprite
  const r = img.getBoundingClientRect();
  const flut = document.createElement("div");
  flut.className = "meta-ganho";
  flut.textContent = "+" + brl(ganho);
  flut.style.left = (r.left + r.width / 2) + "px";
  flut.style.top = r.top + "px";
  document.body.appendChild(flut);
  flut.addEventListener("animationend", () => flut.remove(), { once: true });
  setTimeout(() => flut.remove(), 1500);
}

async function depositarMeta(chave, ganho) {
  const d = await api(`/api/metas/${chave}/deposito`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ valor: ganho }),
  });
  const m = d.metas.find((x) => x.chave === chave);
  if (m) animarDeposito(META_SEL[chave], m, ganho);
}

// Clicar no número abre um campo de DEPÓSITO (vazio, "+ quanto?"): o valor é somado,
// nunca substitui o total. Enter/blur confirma, Esc desiste. Corrigir pra menos é na
// mão, no financeiro.md — de propósito, pra só empurrar pra cima.
function abrirDeposito(chave, alvo) {
  const inp = document.createElement("input");
  inp.type = "text";
  inp.inputMode = "decimal";
  inp.className = "meta-input";
  inp.placeholder = "+ quanto?";
  alvo.replaceWith(inp);
  inp.focus();

  let encerrado = false;
  const fechar = async (confirmar) => {
    if (encerrado) return;
    encerrado = true;
    const ganho = Number((inp.value || "").replace(",", ".")) || 0;
    if (confirmar && ganho > 0) {
      inp.replaceWith(alvo);            // devolve o número antes de animar por cima
      await depositarMeta(chave, ganho);
    } else {
      await carregarMetas();            // desistiu: restaura o card
    }
  };
  inp.onblur = () => fechar(true);
  inp.onkeydown = (e) => {
    if (e.key === "Enter") { e.preventDefault(); inp.blur(); }
    if (e.key === "Escape") { encerrado = true; carregarMetas(); }
  };
}

// ---- companheiro vivo ----
// Uma energia sai do botão que a pessoa clicou e voa até a barra de XP; ao chegar, a
// barra engrossa e o companheiro dá um pulinho. Só nas ações icônicas (feito/anotar/
// bolinha de recorrente) — os checkboxes de "todas as tarefas" não disparam nada.
function celebrar(origem) {
  const barra = $(".barra");
  const sprite = $("#sprite");
  if (!origem || !barra || !sprite) return;

  const pulinho = () => {
    barra.classList.remove("pulsou"); void barra.offsetWidth; barra.classList.add("pulsou");
    sprite.classList.remove("ganhou"); void sprite.offsetWidth; sprite.classList.add("ganhou");
    // fantasma translúcido por cima do sprite: escala pra fora e some, simulando
    // que o companheiro cresceu com o XP que acabou de entrar
    const r = sprite.getBoundingClientRect();
    const fantasma = document.createElement("img");
    fantasma.src = sprite.src;
    fantasma.className = "sprite-fantasma";
    fantasma.style.left = r.left + "px";
    fantasma.style.top = r.top + "px";
    fantasma.style.width = r.width + "px";
    fantasma.style.height = r.height + "px";
    document.body.appendChild(fantasma);
    fantasma.addEventListener("animationend", () => fantasma.remove(), { once: true });
    setTimeout(() => fantasma.remove(), 1200);
  };

  const o = origem.getBoundingClientRect();
  const d = barra.getBoundingClientRect();
  const ox = o.left + o.width / 2, oy = o.top + o.height / 2;
  const dx = d.left + d.width / 2, dy = d.top + d.height / 2;

  const bolha = document.createElement("div");
  bolha.className = "energia-xp";
  bolha.style.left = ox + "px";
  bolha.style.top = oy + "px";
  document.body.appendChild(bolha);
  requestAnimationFrame(() => {
    bolha.style.transform = `translate(${dx - ox}px, ${dy - oy}px) scale(.3)`;
    bolha.style.opacity = "0";
  });
  let caiu = false;
  const chegar = () => { if (caiu) return; caiu = true; bolha.remove(); pulinho(); };
  bolha.addEventListener("transitionend", chegar, { once: true });
  setTimeout(chegar, 1000);   // rede: transitionend pode não vir se a aba perde foco
}

function textoJanela(min, eventoAtual) {
  if (eventoAtual) return `agora: ${eventoAtual.titulo} até ${eventoAtual.fim}`;
  if (min === null) return "";
  if (min >= 120) return `${Math.floor(min / 60)}h livres pela frente`;
  return `${min} min até o próximo compromisso`;
}

// A agenda saiu da coluna principal e virou botão: ela é consulta pontual, não
// algo que se lê o dia inteiro. O espaço nobre ficou pro chat. O botão continua
// dizendo quantos compromissos existem, que é a única parte urgente.
async function carregarEventos() {
  const d = await api("/api/eventos");
  const botao = $("#abrir-agenda");
  if (!d.configurado) {
    botao.hidden = true;
    $("#janela").hidden = true;
    return;
  }
  botao.hidden = false;
  const restantes = d.eventos.filter((e) => !e.passado).length;
  botao.textContent = restantes ? `agenda (${restantes})` : "agenda";

  const ul = $("#eventos");
  ul.innerHTML = "";
  for (const e of d.eventos) {
    const li = document.createElement("li");
    const hora = document.createElement("span");
    hora.className = "hora";
    hora.textContent = e.dia_inteiro ? "dia inteiro" : `${e.inicio}–${e.fim}`;
    const titulo = document.createElement("span");
    titulo.textContent = e.titulo;
    if (d.evento_atual && d.evento_atual.titulo === e.titulo
        && d.evento_atual.inicio === e.inicio) {
      li.className = "agora";
    } else if (e.passado) {
      li.className = "passado";
    }
    li.appendChild(hora);
    li.appendChild(titulo);
    ul.appendChild(li);
  }
  $("#agenda-vazia").hidden = d.eventos.length > 0;

  const texto = textoJanela(d.janela_livre, d.evento_atual);
  $("#janela").textContent = texto;
  $("#janela").hidden = !texto;
}

// Energia como bateria de celular: 3 bloquinhos, um por nível. A CSS preenche
// 1/2/3 células na cor do nível. Mesma linguagem visual do pill de feito.
function montarBateria(energia) {
  const e = normEnergia(energia);
  const bat = document.createElement("span");
  bat.className = "bateria";
  bat.dataset.energia = e;
  bat.setAttribute("role", "img");
  bat.setAttribute("aria-label", `energia ${e}`);
  bat.title = e;
  for (let i = 0; i < 3; i++) {
    const cel = document.createElement("span");
    cel.className = "celula";
    bat.appendChild(cel);
  }
  return bat;
}

function montarCard(t) {
  const card = document.createElement("div");
  card.className = "card";

  const titulo = document.createElement("div");
  titulo.className = "titulo";
  titulo.textContent = t.titulo;
  card.appendChild(titulo);

  card.appendChild(montarBateria(t.energia));

  const btn = document.createElement("button");
  btn.textContent = "feito ✓";
  btn.onclick = () => concluir(t.id, btn);
  card.appendChild(btn);

  return card;
}

async function carregarAgora() {
  const dados = await api(`/api/agora?offset=${offset}`);
  const cont = $("#cards");
  cont.innerHTML = "";
  if (dados.tarefas.length === 0) {
    const p = document.createElement("p");
    p.className = "vazio";
    p.textContent = "sem tarefas abertas 🎉";
    cont.appendChild(p);
    return;
  }
  for (const t of dados.tarefas) cont.appendChild(montarCard(t));
}

// A coluna da direita: recorrentes agrupadas por frequência, cada grupo com sua cor
// de tipo. O estado ("volta em Xd") vem do servidor via `disponivel`/`volta_em` —
// nunca do "feito hoje", que era o que fazia a semanal reaparecer todo dia.
const FREQS = ["diario", "semanal", "mensal"];

function montarRecorrente(t) {
  const li = document.createElement("li");
  if (!t.disponivel) li.className = "feita";

  const btn = document.createElement("button");
  btn.className = "marcar";
  btn.type = "button";
  btn.setAttribute("aria-label", t.disponivel ? "marcar como feita" : "feita");
  if (t.disponivel) btn.onclick = () => concluir(t.id, btn);
  else btn.disabled = true;
  li.appendChild(btn);

  const corpo = document.createElement("div");
  corpo.className = "corpo";
  const titulo = document.createElement("span");
  titulo.className = "titulo";
  titulo.textContent = t.titulo;
  corpo.appendChild(titulo);
  if (t.disponivel) {
    corpo.appendChild(montarBateria(t.energia));
  } else {
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = `volta em ${t.volta_em}d`;
    corpo.appendChild(meta);
  }
  li.appendChild(corpo);

  return li;
}

async function carregarRecorrentes() {
  const dados = await api("/api/tarefas");
  for (const freq of FREQS) {
    const ul = document.querySelector(`.grupo[data-freq="${freq}"] ul`);
    ul.innerHTML = "";
    const itens = dados.tarefas.filter((t) => t.repete === freq && !t.concluida);
    for (const t of itens) ul.appendChild(montarRecorrente(t));
    ul.closest(".grupo").hidden = itens.length === 0;
  }
}

// Contador de inbox: só mostra quantas linhas o braindump tem esperando triagem.
// A triagem em si é feita por fora do app (peço pro Claude aqui no terminal).
async function carregarInbox() {
  const b = $("#inbox-contador");
  const d = await api("/api/inbox");
  b.hidden = d.pendentes === 0;
  b.textContent = `inbox (${d.pendentes})`;
}

async function carregarAnotacoes() {
  const dados = await api("/api/diario");
  const ul = $("#anotacoes");
  ul.innerHTML = "";
  if (dados.anotacoes.length === 0) {
    const li = document.createElement("li");
    li.className = "vazio";
    li.textContent = "nada anotado hoje ainda";
    ul.appendChild(li);
    return;
  }
  for (const a of dados.anotacoes) {
    const li = document.createElement("li");
    const hora = document.createElement("span");
    hora.className = "hora";
    hora.textContent = a.hora;
    const texto = document.createElement("span");
    texto.textContent = a.texto;
    const energia = document.createElement("span");
    energia.className = "energia";
    energia.textContent = a.energia || "";
    li.appendChild(hora);
    li.appendChild(texto);
    li.appendChild(energia);
    ul.appendChild(li);
  }
}

async function carregarLista() {
  const dados = await api("/api/tarefas");
  const ul = $("#lista");
  ul.innerHTML = "";
  let abertas = 0;
  // recorrentes vivem na coluna da direita: aqui só o backlog de tarefas únicas.
  for (const t of dados.tarefas.filter((t) => !t.repete)) {
    const li = document.createElement("li");
    if (t.concluida) li.className = "concluida";
    else abertas++;
    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.checked = t.concluida;
    chk.onchange = () => alternar(t.id, chk.checked);
    const span = document.createElement("span");
    span.textContent = t.titulo;
    li.appendChild(chk);
    li.appendChild(span);
    ul.appendChild(li);
  }
  $("#conta").textContent = `${abertas} abertas`;
}

// Concluir qualquer coisa vira uma linha no diário "Acabei de fazer": por isso
// recarregamos as anotações junto. A coluna também, caso tenha sido uma recorrente.
async function concluir(id, origem) {
  if (origem) celebrar(origem);   // dispara já no clique, antes do sprite re-renderizar
  await api(`/api/tarefas/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ concluida: true }),
  });
  await Promise.all([carregarAgora(), carregarLista(), carregarRecorrentes(),
                     carregarAnotacoes(), carregarPokemon()]);
}

async function alternar(id, concluida) {
  await api(`/api/tarefas/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ concluida }),
  });
  await Promise.all([carregarAgora(), carregarLista(), carregarRecorrentes(),
                     carregarAnotacoes(), carregarPokemon()]);
}

function energiaEscolhida() {
  return $("#energias .ativa").dataset.energia;
}

// ---- captura rápida ----
// Sem navegação, sem confirmação, sem escolher pasta: escreve e dá enter. O foco
// nunca sai do campo, então dá pra despejar cinco coisas seguidas. Organizar é
// trabalho da /triagem depois.
let sumirOk;

function piscarOk(texto) {
  const p = $("#captura-ok");
  p.textContent = texto;
  p.classList.add("visivel");
  clearTimeout(sumirOk);
  sumirOk = setTimeout(() => p.classList.remove("visivel"), 1800);
}

async function capturar(e) {
  e.preventDefault();
  const campo = $("#captura-texto");
  const texto = campo.value.trim();
  if (!texto) return;
  campo.value = "";
  campo.focus();
  try {
    const r = await api("/api/inbox", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    piscarOk(`no inbox (${r.pendentes})`);
    await carregarInbox();
  } catch {
    campo.value = texto;   // não perde o que ele escreveu
    piscarOk("não salvou");
  }
}

// ---- desligar / reiniciar ----
// O botão de power fechado é um círculo; ao clicar, expande numa elipse dividida ao
// meio (esquerda reiniciar, direita desligar). Substitui a janela de console que
// antes era o interruptor do app.
function telaFinal(html) {
  document.body.innerHTML = `<div class="tela-final">${html}</div>`;
}

async function desligarApp() {
  // o servidor cai no meio da resposta; se der erro de rede, o desligar funcionou.
  try { await api("/api/desligar", { method: "POST" }); } catch { /* já foi */ }
  telaFinal("<p>App desligado.</p><p class='sub'>Pode fechar a aba.</p>");
}

async function reiniciarApp() {
  telaFinal("<p>Reiniciando…</p><p class='sub'>já volta</p>");
  try { await api("/api/reiniciar", { method: "POST" }); } catch { /* já foi */ }
  // dá tempo do servidor velho cair, depois pinga /api/agora até o novo responder.
  const ate = Date.now() + 30000;
  const tenta = async () => {
    try {
      const r = await fetch("/api/agora", { cache: "no-store" });
      if (r.ok) { location.reload(); return; }
    } catch { /* ainda fora do ar */ }
    if (Date.now() < ate) setTimeout(tenta, 500);
    else telaFinal("<p>Não voltou sozinho.</p><p class='sub'>Reabra pelo iniciar.bat.</p>");
  };
  setTimeout(tenta, 1200);
}

function ligarPower() {
  const power = $("#power");
  if (!power) return;
  const toggle = $("#power-toggle");
  const fechar = () => { power.classList.remove("aberto"); toggle.setAttribute("aria-expanded", "false"); };
  const abrir = () => { power.classList.add("aberto"); toggle.setAttribute("aria-expanded", "true"); };

  toggle.onclick = (e) => {
    e.stopPropagation();
    power.classList.contains("aberto") ? fechar() : abrir();
  };
  power.querySelector(".power-reiniciar").onclick = (e) => { e.stopPropagation(); reiniciarApp(); };
  power.querySelector(".power-desligar").onclick = (e) => { e.stopPropagation(); desligarApp(); };

  // clicar fora ou Esc recolhe pro círculo
  document.addEventListener("click", (e) => { if (!power.contains(e.target)) fechar(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") fechar(); });
}

function ligarEventos() {
  $("#data").textContent = dataHoje();
  ligarPower();

  const modal = $("#modal-agenda");
  $("#abrir-agenda").onclick = () => modal.showModal();
  $("#fechar-agenda").onclick = () => modal.close();
  // clicar fora fecha: o <dialog> nativo entrega o clique do backdrop no próprio modal
  modal.onclick = (e) => { if (e.target === modal) modal.close(); };

  $("#form-captura").onsubmit = capturar;

  $("#outras").onclick = () => { offset += 3; carregarAgora(); };
  $("#mostrar-add").onclick = () => { $("#form-add").hidden = !$("#form-add").hidden; };
  $("#form-add").onsubmit = async (e) => {
    e.preventDefault();
    const titulo = $("#novo-titulo").value.trim();
    if (!titulo) return;
    const energia = $("#nova-energia").value || null;
    await api("/api/tarefas", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ titulo, energia }),
    });
    $("#novo-titulo").value = "";
    $("#form-add").hidden = true;
    offset = 0;
    await Promise.all([carregarAgora(), carregarLista()]);
  };
  for (const b of document.querySelectorAll("#energias button")) {
    b.onclick = () => {
      $("#energias .ativa").classList.remove("ativa");
      b.classList.add("ativa");
      $("#anotacao").focus();
    };
  }
  $("#sprite").onclick = () => {
    const s = $("#sprite");
    s.classList.remove("cutucou"); void s.offsetWidth; s.classList.add("cutucou");
  };
  $("#form-anotar").onsubmit = async (e) => {
    e.preventDefault();
    const texto = $("#anotacao").value.trim();
    if (!texto) return;
    celebrar($("#anotar"));
    await api("/api/diario", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ texto, energia: energiaEscolhida() }),
    });
    $("#anotacao").value = "";
    await Promise.all([carregarAnotacoes(), carregarPokemon()]);
  };
}

async function init() {
  ligarEventos();
  await Promise.all([carregarPokemon(), carregarMetas(), carregarEventos(),
                     carregarAgora(), carregarLista(), carregarRecorrentes(),
                     carregarAnotacoes(), carregarInbox()]);
}
init();
