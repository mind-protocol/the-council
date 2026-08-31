// pensees.js — l'intériorité du personnage joueur : elle vit dans le fil, et se
// dit à mi-voix — sa voix à elle, mais plus près, comme on s'entend penser.
"use strict";
(() => {
  Bus.enregistrer("pensee", (it, ctx) => {
    const entree = Bus.chronique("chr-pensee", null, it.texte);
    if (window.Voix) Voix.dire("pensee-joueur", it.texte, ctx, entree);
  });
  window.PenseeAfficher = (texte) => Bus.chronique("chr-pensee", null, texte);
})();
