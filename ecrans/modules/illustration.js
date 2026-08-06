// illustration.js — quand un acteur illustre ses propos sur la table peinte.
// Un conseil est une séance de travail : on ne dit pas « la flotte tiendra le
// Gosier », on pose trois doigts dessus. Ce module donne aux acteurs la main sur
// la carte, de deux façons :
//
//   • item {type:"table", acteur_id, texte, jetons, traits, zones, cadre}
//     — un geste sur la carte, avec sa vignette dans le fil. Le chroniqueur le
//       raconte (ce n'est pas une parole) et la table du décor prend les pièces.
//
//   • un champ `montre` sur une `replique` ou un `geste`
//     — il parle ET sa main pose : la table du décor bouge pendant qu'il parle,
//       et sa carte du fil porte une mention discrète pour y revenir.
//
// Les pièces posées ainsi sont ÉPHÉMÈRES : elles vivent le temps de la scène et
// tombent au prochain `effacer`. Ce qui doit durer, le MJ l'écrit dans
// etat/jetons.json — un geste de démonstration n'est pas un fait acquis.
"use strict";
window.Illustration = (() => {
  const marquesDe = (m) => ({
    jetons: m.jetons || [], traits: m.traits || [], zones: m.zones || [],
    cadre: m.cadre,
  });
  const vide = (m) => !(m.jetons || []).length && !(m.traits || []).length &&
    !(m.zones || []).length;

  // La vignette dans le fil : la carte réduite au geste, cliquable pour ouvrir
  // la grande table sur le même cadrage. `vu` est le cadrage déjà résolu par
  // Carte.illustrer — la chronique doit rouvrir EXACTEMENT ce qui a été montré,
  // même quand la table aura changé.
  function vignette(hote, montre, vu) {
    if (!window.Carte || !window.Geo) return;
    const d = document.createElement("div");
    d.className = "chr-carte";
    d.innerHTML = Carte.miniature(montre) +
      '<span class="chr-carte-ouvrir">S\'approcher…</span>';
    d.addEventListener("click", () => Carte.ouvrir(vu || "auto"));
    hote.appendChild(d);
  }

  // Sur une réplique ou un geste : pas de seconde carte dans le fil — la table
  // du décor vient de bouger sous les yeux du joueur. Juste de quoi y revenir.
  function attacher(el, vu) {
    if (!el) return;
    const corps = el.querySelector(".chr-corps") || el;
    const a = document.createElement("span");
    a.className = "chr-vers-table";
    a.textContent = "la table en porte la marque";
    a.addEventListener("click", () => {
      if (window.Carte) Carte.ouvrir(vu || "auto");
    });
    corps.appendChild(a);
  }

  // Ce que tout item peut porter : `montre`. Appelé par paroles.js et gestes.js.
  function poser(el, it) {
    if (!it.montre || vide(it.montre) || !window.Carte) return;
    attacher(el, Carte.illustrer(marquesDe(it.montre)));
  }

  Bus.enregistrer("table", (it, ctx) => {
    const m = marquesDe(it);
    if (it.acteur_id && window.activerLocuteur) window.activerLocuteur(it.acteur_id);
    const p = (window.Presents || {})[it.acteur_id] || { nom: it.acteur_id };
    const el = Bus.chronique("chr-table", it.acteur_id ? p.nom : null,
      it.texte || "", { avatar: p.portrait_svg, role: p.titre });
    const vu = !vide(m) && window.Carte ? Carte.illustrer(m) : null;
    if (el && !vide(m)) vignette(el.querySelector(".chr-corps") || el, m, vu);
    // Une main sur la carte n'est pas une parole : c'est le chroniqueur qui la
    // décrit, comme un geste.
    if (window.Voix && it.texte) Voix.dire("narrateur", it.texte, ctx);
  });

  return { poser, attacher, vignette };
})();
