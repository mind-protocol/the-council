// books.js — « Les livres », une échelle du décor.
// Un book est un OBJET posé dans une salle : un registre sur la Table Peinte,
// un livre de comptes à l'intendance, un rôle d'équipage au quai. Il porte du
// JSON — un tableau à colonnes, des pages de texte — et il ne se consulte que
// là où il se trouve : on ne lit pas depuis l'autre bout du château un registre
// qui est resté sur la table.
//
// Un livre peut aussi n'être posé nulle part : il est SUR QUELQU'UN. C'est le
// carnet de voyage — il suit son porteur de château en château, et on ne peut
// l'ouvrir que là où l'homme se trouve. Un carnet qu'on lit alors que son
// porteur est à trois jours de route serait une fuite, pas une commodité.
//
// Format (etat/books.json, un tableau) :
//   id                      — l'objet
//   lieu_id, salle_id       — où il est POSÉ (un registre sur une table)
//   acteur_id               — ou sur QUI il est porté (un carnet de voyage) ;
//                             l'un ou l'autre, jamais les deux
//   boite                   — ou le COFFRET où il est rangé (etat/boites.json).
//                             Une boîte est un objet du monde comme lui : elle
//                             est posée ou portée, et elle donne sa place à
//                             tout ce qu'elle contient. Un volume rangé n'a
//                             donc ni salle, ni porteur, ni `prive` à lui — le
//                             serveur les lui recopie de la boîte avant de
//                             servir l'étagère
//   prive: true             — un carnet que son porteur ne montre pas : seul
//                             le joueur qui le porte le voit. Sans `acteur_id`
//                             il ne veut rien dire — un volume posé n'a pas de
//                             porteur : c'est `lecteurs` qu'il lui faut
//   lecteurs: [ "…", … ]    — les seuls qui puissent l'ouvrir. Ça ne DONNE
//                             rien : le volume garde ses règles de lieu, mais
//                             qui n'y est pas nommé ne le voit pas — le
//                             registre où vivent les noms, posé sur la table
//                             d'une salle où deux sièges entrent
//   titre, sous_titre       — ce qu'on lit sur la couverture
//   type                    — le genre du volume (registre, carnet, plan,
//                             memento, dossier, regle, oeuvre) : il donne son
//                             mot sur l'onglet et sa teinte de tranche
//   couleur                 — pour forcer la teinte contre celle du type ;
//                             sans lui, elle est préremplie par le type
//   colonnes: [ "…", … ]    — l'en-tête du tableau (optionnel)
//   lignes: [ { cellules: [ … ], note: "…" }, … ]  (une ligne peut aussi être
//                             un simple tableau de cellules)
//   pages: [ "…", … ]       — du texte suivi, quand il n'y a pas de tableau
//
// Un dernier volume ferme l'étagère et n'est PAS dans `books.json` : les notes
// du joueur. Hors fiction, toujours à portée, gardées telles quelles par le
// serveur (`/notes`, un fichier de texte par siège). Rien de ce qui s'y écrit
// n'entre dans la partie.
//
// ---- CE FICHIER EST LA FAÇADE, ET RIEN D'AUTRE ----------------------------
//
// `books.js` faisait mille neuf cent quarante-neuf lignes dans une seule
// fermeture, et c'est ce qui le rendait intouchable : la grille, le brouillard,
// la criticité, les renvois et le carnet du joueur y partageaient vingt-trois
// variables libres qu'aucune pièce ne pouvait emporter en sortant. Le dossier
// `books/` les sépare ; ce fichier-ci les remonte.
//
// L'ASSEMBLAGE EST UN OBJET, PAS UNE CHAÎNE D'ARGUMENTS. Les dépendances de ces
// pièces sont CIRCULAIRES et le resteront : la grille appelle `renvoyer`, les
// renvois appellent `ouvrir`, l'étagère appelle les deux, et tout le monde
// appelle `dessiner`. On ne peut donc pas passer les fonctions à la création —
// on passe `A`, qu'on remplit au fur et à mesure, et chaque pièce y lit ce
// qu'elle appelle AU MOMENT de l'appeler. Ce qui ne dépend de rien (`lecture`)
// se prend par destructuration à la création, et se lit sans préfixe.
//
// L'ORDRE DE MONTAGE N'EST PAS UN GRAPHE DE DÉPENDANCES : ces fichiers ne sont
// pas des modules ES, ils posent des globales à l'évaluation. `lecture` d'abord
// parce que les autres la destructurent tout de suite ; le reste dans l'ordre
// qu'on veut, puisque tout passe par `A`.
//
// L'API RENDUE NE CHANGE PAS D'UN NOM. `charger, relire, page, poser, teinte,
// genre, ouvrir, aller, viser, fiche, affairesVues` — le fil, l'échiquier, les
// écrits, les gens et l'illustration s'en servent, et aucun n'a été touché.
"use strict";
window.Books = (() => {
  const S = BooksEtat.creer();

  // L'assemblage : ce que les pièces s'appellent les unes aux autres. On le
  // remplit pièce par pièce, et chacune y lit AU MOMENT de l'appel — c'est ce
  // qui permet aux dépendances circulaires de tenir sans qu'aucune ne connaisse
  // l'ordre de montage.
  const A = {
    lecture: BooksLecture,
    memoire: { MEMOIRE_IDEES: BooksEtat.MEMOIRE_IDEES,
               MEMOIRE_POIDS: BooksEtat.MEMOIRE_POIDS },
  };
  // Deux pièces qui poseraient le même nom se recouvriraient en silence, et
  // l'on chercherait le défaut dans celle qui perd. On mord tout de suite.
  const monter = (piece) => {
    const rendu = piece.creer(S, A);
    Object.keys(rendu).forEach((n) => {
      if (n in A) throw new Error("books : deux pièces posent « " + n + " »");
      A[n] = rendu[n];
    });
  };

  monter(BooksPortee);      // où est un volume, et qui peut l'ouvrir d'ici
  monter(BooksCriticite);   // les chiffres qui ne sont pas dans le volume
  monter(BooksIdees);       // ce qu'il y aurait à faire, sous chaque affaire
  monter(BooksNotes);       // le carnet du joueur, hors du monde
  monter(BooksCopie);       // recopier un volume, et sa ligne de titre
  monter(BooksRenvois);     // un numéro écrit, et la ligne qui le définit
  monter(BooksVolume);      // le volume ouvert : ses grilles, ses pages
  monter(BooksMarques);     // ce qu'on lit d'un volume sans l'ouvrir
  monter(BooksCoffret);     // la boîte ouverte, ligne à ligne
  monter(BooksOnglets);     // la tranche du haut : grouper, élire, poser
  monter(BooksEtagere);     // ce qui est à portée, le tracé, le cycle de vie

  A.charger();
  A.veiller();
  window.addEventListener("DOMContentLoaded", A.brancher);

  // `page` et `poser` sortent du module pour le fil : un extrait montré en
  // scène doit avoir EXACTEMENT la mine qu'il aura dans le volume, sans quoi
  // le joueur croit voir deux objets là où il n'y en a qu'un.
  // `ouvrir` sort pour que le fil puisse dire « porté au registre » avec un
  // lien qui y mène, et `aller` pour renvoyer à une ligne précise — « c'est
  // écrit au 23100 » — et non seulement au volume.
  // `affairesVues` sort pour que « Mon gouvernement », dans « Les gens », borne
  // ses comptes sur la MÊME étagère que le volume « Les pas ». `/criticite` est
  // une route de machine qui rend les quarante-deux affaires du dépôt, cahiers
  // d'un autre siège compris : deux écrans qui s'en servent doivent la borner de
  // la même main, sinon la fuite qu'on vient de reboucher ici rouvre ailleurs.
  return {
    charger: A.charger, relire: A.relire, page: A.page, ouvrir: A.ouvrir,
    aller: A.aller, viser: A.viser, fiche: A.fiche,
    affairesVues: A.affairesVues,
    poser: A.lecture.poser, teinte: A.lecture.teinte, genre: A.lecture.genre,
  };
})();
