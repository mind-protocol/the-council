// habillage.js — ce que la feuille d'habillage ne peut pas écrire seule.
//
// Le visage d'un monde est d'abord une feuille, `/habillage.css`, chargée
// après toutes les autres (voir serveur/routes/habillage.js). Trois choses lui
// échappent, parce qu'elles ne sont pas du style : le titre de l'onglet, un
// bandeau qui porte un nom, et un logo qui doit rester lisible par un lecteur
// d'écran. Elles sont déclarées dans `<monde>/habillage/habillage.json`, servi
// sous `/habillage.json` :
//
//   { "titre":   "Charmed — San Francisco, 1906",      // l'onglet
//     "bandeau": { "titre": "La maison sur le Nexus",  // le texte à gauche
//                  "logo":  "logo.webp",               // /habillage/logo.webp
//                  "logo_alt": "Charmed" } }
//
// Rien ici ne dépend de l'ordre de chargement : ni la grille ni aucun module ne
// lit ce que ce fichier pose, donc un `fetch` qui arrive après le premier
// dessin ne coûte qu'un titre changé une demi-seconde plus tard.
//
// Un monde sans habillage reçoit `null` : ni attribut, ni bandeau. Le bandeau
// n'a aucune place dans la grille — c'est la feuille du monde qui le pose
// (`position:fixed`, en général) et qui décide de la place qu'on lui laisse.
// Qui déclare un bandeau dans le JSON lui doit donc sa règle dans le CSS.
"use strict";
(() => {
  function habiller(h) {
    if (!h || typeof h !== "object") return;
    document.documentElement.dataset.habillage = h.monde || "monde";
    if (h.titre) document.title = h.titre;

    const b = h.bandeau;
    if (!b || typeof b !== "object") return;
    const tete = document.createElement("header");
    tete.id = "habillage-bandeau";
    if (b.titre) {
      const t = document.createElement("span");
      t.className = "hb-titre";
      t.textContent = b.titre;
      tete.appendChild(t);
    }
    if (b.logo) {
      const img = document.createElement("img");
      img.className = "hb-logo";
      img.src = "/habillage/" + encodeURIComponent(b.logo);
      img.alt = b.logo_alt || "";
      tete.appendChild(img);
    }
    document.body.appendChild(tete);
  }

  fetch("/habillage.json").then((r) => (r.ok ? r.json() : null))
    .then(habiller).catch(() => {});
})();
