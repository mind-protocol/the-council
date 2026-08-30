// etat.js — CE QUI CHANGE PENDANT QU'ON LIT, rassemblé et nommé.
//
// CE QU'IL REMPLACE. Vingt-trois variables libres déclarées au fil de mille
// neuf cents lignes de `books.js` — l'étagère rentrée, le volume ouvert, le
// coffret ouvert, le pilier tenu, la criticité, les notes du joueur, l'index
// des renvois. Elles marchaient : ce fichier ne corrige aucun défaut.
//
// POURQUOI ALORS. Parce que tant que l'état vit en variables libres, RIEN NE
// PEUT SORTIR DU MONOLITHE. La grille doit lire la criticité, le coffret doit
// lire le pilier tenu, l'étagère doit écrire le volume ouvert — et l'on ne peut
// rien leur passer : il n'y a pas d'objet, il y a des noms visibles depuis
// l'intérieur d'une fermeture et depuis nulle part ailleurs.
//
// CE QU'IL N'EST PAS. Un magasin où tout le monde écrit. Une donnée a UN
// écrivain et les autres la lisent : `etagere.js` tient l'étagère et ce qui est
// ouvert, `criticite.js` tient le calcul, `notes.js` tient le carnet du joueur,
// `renvois.js` tient l'index. Rassembler ne redistribue aucun droit — ça permet
// enfin de dire lequel, puisqu'on peut enfin les nommer.
//
// CE QU'IL NE CONTIENT PAS. Les genres de volume, les colonnes calculées,
// l'aide de leurs en-têtes : ce sont des constantes de lecture, pas de l'état.
// Un état est ce qui BOUGE pendant qu'on lit ; le reste est du savoir, et il
// vit dans la pièce qui s'en sert.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksEtat = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  // Les deux interrupteurs du coffret des affaires se retiennent d'une session
  // à l'autre, comme le reste du décor. Ils se lisent ici, à la création, et
  // c'est `coffret.js` qui les réécrit quand le joueur les touche.
  const MEMOIRE_IDEES = "conseil-books-idees";
  const MEMOIRE_POIDS = "book-affaires-par-poids";

  const retenu = (clef) => {
    try { return localStorage.getItem(clef) === "1"; } catch (e) { return false; }
  };

  /**
   * `creer` — un état neuf, aux valeurs exactes qu'avaient les déclarations.
   *
   * On rend un objet littéral d'un seul tenant plutôt que de le construire
   * champ par champ : la forme est alors unique et stable, et l'on lit d'un
   * coup tout ce qui peut bouger dans cette échelle du décor.
   */
  function creer() {
    return {
      // ---- l'étagère, telle que le serveur l'a servie ----------------------
      books: null,
      boites: [],            // les coffrets à portée (etat/boites.json)
      charge: false,
      ferme: false,          // le serveur a refusé l'étagère : pas de siège
      perime: false,         // on a déjà redemandé l'étagère une fois

      // ---- ce qu'on a sous les yeux ----------------------------------------
      ouvert: null,          // le volume qu'on lit
      ouverteBoite: null,    // le coffret ouvert, si c'en est un

      // ---- ce que le dernier tracé a constaté -------------------------------
      salleVue: undefined,   // la salle du dernier tracé
      chateauVu: undefined,  // le château du dernier CHARGEMENT
      portantsVus: "",       // qui portait un carnet au dernier tracé

      // ---- le coffret des affaires ------------------------------------------
      pilierTenu: null,      // le filtre : ne garder qu'un pilier
      idees: retenu(MEMOIRE_IDEES),   // l'interrupteur des idées
      parPoids: retenu(MEMOIRE_POIDS),// rangé par criticité, toutes mains mêlées
      ideesChargees: false,  // on n'a demandé la route qu'une fois
      parLivre: {},          // livre_id -> { m: la mission, titre: l'affaire }

      // ---- la criticité, calculée à la demande -------------------------------
      crit: null,
      critDemande: false,

      // ---- le carnet du joueur -----------------------------------------------
      notes: "",             // ce qu'il y a dans la zone, à la frappe près
      notesEcrit: null,      // ce que le serveur a effectivement gardé
      notesMinuteur: null,
      notesEtat: "",         // la mention sous la zone : « Gardé. »

      // ---- l'index des renvois, refait à chaque tracé -------------------------
      renvois: new Map(),    // un numéro → l'id du volume qui le définit
      fiches: new Map(),     // un numéro → {livre, titre, icone} pour le fil
    };
  }

  return { creer, MEMOIRE_IDEES, MEMOIRE_POIDS };
});
