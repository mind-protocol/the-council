// vus.js — le carnet de rencontres : qui j'ai vu, où, et dans quel ordre.
//
// La vue « Les gens » rangeait la cour par camp puis par maison : un armorial.
// C'est juste, et ce n'est pas ce qu'on cherche quand on ouvre la liste — on
// cherche la femme croisée tout à l'heure dans la petite salle, dont on a
// oublié le nom. Il fallait donc tenir un ordre de RENCONTRE.
//
// Rien à écrire dans `etat/` pour cela : le fil dit déjà tout. Chaque item
// porte son index de flux (`_i`) et, quand la scène change de lieu, son
// en-tête (`lieu`). On en tire deux choses :
//   • `vus`    : id → le plus grand index où on l'a vu (parlé, agi, présent) ;
//   • `jalons` : les index où le lieu change, avec le nom du lieu.
// Le lieu d'une rencontre se retrouve alors à la lecture : c'est le dernier
// jalon posé AVANT son index.
//
// Cette résolution paresseuse n'est pas de la coquetterie. Le fil se rejoue
// dans le désordre : au chargement on rend les items récents, et remonter la
// chronique en injecte de plus anciens PAR-DESSUS, après coup. Un simple
// compteur « dernier lieu vu » serait faux dès le premier défilement vers le
// haut ; les index, eux, se rangent tout seuls.
"use strict";
window.Vus = (() => {
  const vus = new Map();          // id → index de flux le plus récent
  let jalons = [];                // [{i, lieu}] triés par i croissant
  let trie = true;

  const rang = (it) => (typeof it._i === "number" ? it._i : Infinity);

  function noter(id, i) {
    if (!id || typeof i !== "number") return;
    if (!vus.has(id) || vus.get(id) < i) vus.set(id, i);
  }

  function jalon(it) {
    if (!it.lieu) return;
    const i = rang(it);
    if (i === Infinity) return;
    const dernier = jalons.length ? jalons[jalons.length - 1] : null;
    if (dernier && dernier.i === i) { dernier.lieu = it.lieu; return; }
    jalons.push({ i, lieu: it.lieu });
    trie = false;
  }

  // Le lieu où l'on se tenait à cet index : le dernier jalon posé avant lui.
  function ou(i) {
    if (typeof i !== "number") return "";
    if (!trie) { jalons.sort((a, b) => a.i - b.i); trie = true; }
    let bas = 0, haut = jalons.length - 1, trouve = "";
    while (bas <= haut) {
      const m = (bas + haut) >> 1;
      if (jalons[m].i <= i) { trouve = jalons[m].lieu; bas = m + 1; }
      else haut = m - 1;
    }
    return trouve;
  }

  // Ce que la vue « Les gens » consomme : la liste des rencontres, la plus
  // fraîche en tête, chacune avec le lieu où elle a eu lieu.
  function carnet() {
    return [...vus.entries()]
      .map(([id, i]) => ({ id, i, lieu: ou(i) }))
      .sort((a, b) => b.i - a.i);
  }

  function quand(id) { return vus.has(id) ? vus.get(id) : null; }

  const TOUS = ["salle", "recit", "replique", "geste", "table", "breve",
                "evenement", "vous", "pensee"];
  TOUS.forEach((t) => Bus.enregistrer(t, (it) => {
    const i = rang(it);
    jalon(it);
    (it.presents || []).forEach((p) => noter(typeof p === "string" ? p : p && p.id, i));
    (it.entrent || []).forEach((p) => noter(typeof p === "string" ? p : p && p.id, i));
    if (it.locuteur_id) noter(it.locuteur_id, i);
    if (it.acteur_id) noter(it.acteur_id, i);
    if (window.Gens && Gens.rafraichirVus) Gens.rafraichirVus();
  }));

  return { carnet, quand, ou };
})();
