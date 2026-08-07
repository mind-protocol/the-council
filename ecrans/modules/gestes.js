// gestes.js — ce qu'un acteur FAIT sans le dire : il sort, il verse, il tourne le
// dos, il pousse un coffre sur la table. Attribué à quelqu'un (donc son médaillon
// s'anime), mais rendu en récit et non en parole.
"use strict";
(() => {
  Bus.enregistrer("geste", (it, ctx) => {
    if (it.acteur_id && window.activerLocuteur) window.activerLocuteur(it.acteur_id);
    const p = window.Gens ? Gens.qui(it.acteur_id)
      : (window.Presents || {})[it.acteur_id] || { nom: it.acteur_id };
    const zone = Bus.enArchive() ? null : document.getElementById("act-" + it.acteur_id);
    if (zone) {
      zone.classList.add("agit");
      setTimeout(() => zone.classList.remove("agit"), 4000);
    }
    const entree = Bus.chronique("chr-acte", p.nom, it.texte,
      { avatar: p.portrait_svg, role: it.role || p.titre });
    if (window.Gens) Gens.marquer(entree, it.acteur_id);
    // un geste peut être une main sur la carte : les pièces suivent
    if (window.Illustration) Illustration.poser(entree, it);
    // un geste n'est pas une parole : c'est le chroniqueur qui le dit, pas l'acteur.
    if (window.Voix) Voix.dire("narrateur", it.texte, ctx, entree);
  });
})();
