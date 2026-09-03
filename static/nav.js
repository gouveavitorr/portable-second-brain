// Navegação compartilhada por todas as páginas. Cada página só declara
// <nav id="nav" data-atual="<chave>"></nav> e importa este arquivo — os botões,
// as cores e a regra de "não linkar pra página onde já estou" moram aqui.
// Uma cor de tipo do Pokémon por destino.
const PAGINAS = [
  { chave: "agora", href: "/", nome: "Agora" },
  { chave: "dieta", href: "/dieta", nome: "Dieta" },
  { chave: "financeiro", href: "/financeiro", nome: "Financeiro" },
  { chave: "objetivos", href: "/objetivos", nome: "Objetivos" },
];

(function montarNav() {
  const alvo = document.querySelector("#nav");
  if (!alvo) return;
  const atual = alvo.dataset.atual;
  for (const p of PAGINAS) {
    if (p.chave === atual) continue;
    const a = document.createElement("a");
    a.href = p.href;
    a.className = `nav-btn ${p.chave}`;
    a.textContent = p.nome;
    alvo.appendChild(a);
  }
})();
