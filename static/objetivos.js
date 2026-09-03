// Tela Objetivos: leitura pura. Cada card mostra o objetivo, seu texto, os
// projetos ligados e quantas tarefas ativas estão em andamento. Objetivo sem
// nada em andamento aparece apagado — o alerta de objetivo parado.

const lista = document.querySelector("#objetivos");

function card(o) {
  const li = document.createElement("li");
  li.className = "card-obj" + (o.em_andamento ? "" : " parado");

  const titulo = document.createElement("h2");
  titulo.className = "titulo-obj";
  titulo.textContent = o.titulo;
  li.appendChild(titulo);

  if (o.texto) {
    const p = document.createElement("p");
    p.className = "texto-obj";
    p.textContent = o.texto;
    li.appendChild(p);
  }

  const rodape = document.createElement("div");
  rodape.className = "rodape-obj";

  const sinal = document.createElement("span");
  sinal.className = "sinal-obj";
  sinal.textContent = o.em_andamento
    ? `${o.em_andamento} em andamento`
    : "nada em andamento";
  rodape.appendChild(sinal);

  if (o.projetos.length) {
    const chips = document.createElement("div");
    chips.className = "chips-obj";
    for (const p of o.projetos) {
      const c = document.createElement("span");
      c.className = "chip-obj";
      c.textContent = p.nome;
      chips.appendChild(c);
    }
    rodape.appendChild(chips);
  }

  li.appendChild(rodape);
  return li;
}

async function carregar() {
  const r = await fetch("/api/objetivos");
  const { objetivos } = await r.json();
  lista.replaceChildren();
  if (!objetivos.length) {
    const vazio = document.createElement("li");
    vazio.className = "vazio-obj";
    vazio.textContent = "Nenhum objetivo no objetivos.md ainda.";
    lista.appendChild(vazio);
    return;
  }
  for (const o of objetivos) lista.appendChild(card(o));
}

carregar();
