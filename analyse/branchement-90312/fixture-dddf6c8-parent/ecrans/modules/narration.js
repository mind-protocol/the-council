// narration.js — le monde : brèves et récits. Tout va au fil ; la page de la
// carte reste la salle, sans texte. Ce qui est raconté se dit par la voix du
// chroniqueur — jamais par celle d'un personnage de la salle.
"use strict";
(() => {
  Bus.enregistrer("breve", (it, ctx) => {
    const entree = Bus.chronique("chr-breve", null, it.texte);
    if (window.Voix) Voix.dire("narrateur", it.texte, ctx, entree);
  });
  Bus.enregistrer("recit", (it, ctx) => {
    const entree = Bus.chronique("chr-recit", null, it.texte);
    if (window.Voix) Voix.dire("narrateur", it.texte, ctx, entree);
  });
})();
