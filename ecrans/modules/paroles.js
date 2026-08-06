// paroles.js — les prises de parole. La salle montre QUI parle (le médaillon
// s'illumine) ; ce qui est DIT vit dans le fil, une seule fois.
"use strict";
(() => {
  Bus.enregistrer("replique", (it, ctx) => {
    window.activerLocuteur(it.locuteur_id);
    // qui parle : la salle d'abord, le registre des gens ensuite — un locuteur
    // absent de la salle (un homme qui entre, un lointain qu'on cite) doit tout
    // de même paraître avec son nom et son rôle, jamais avec son id.
    const p = window.Gens ? Gens.qui(it.locuteur_id)
      : (window.Presents || {})[it.locuteur_id] || { nom: it.locuteur_id };
    const entree = Bus.chronique("chr-replique", p.nom, it.texte,
      { avatar: p.portrait_svg, role: it.role || p.titre });
    if (window.Gens) Gens.marquer(entree, it.locuteur_id);
    // s'il montre en même temps qu'il parle, sa main pose sur la table peinte
    if (window.Illustration) Illustration.poser(entree, it);
    // et la réplique se dit, si le joueur a laissé les voix ouvertes
    if (window.Voix) Voix.dire(it.locuteur_id, it.texte, ctx, entree);
  });
})();
