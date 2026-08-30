// lecture.js — CE QU'ON LIT D'UN VOLUME SANS RIEN SAVOIR D'AUTRE.
//
// PREMIÈRE PIÈCE SORTIE DU MONOLITHE, et la seule qui ne dépende de rien : pas
// d'état, pas de serveur, pas de salle où l'on se trouve. On lui donne un
// volume tel que `etat/books.json` l'écrit, elle rend sa teinte, ses tableaux,
// ses adresses. C'est ce qui la rend montable en premier, et lisible seule.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé en sortant
// de `books.js`. Le seul ajout est l'enveloppe.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksLecture = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  // Les genres de volume. Le `type` d'un livre est facultatif ; quand il y en
  // a un, il prérremplit la teinte de la tranche — on reconnaît un carnet d'un
  // registre au coin de l'œil, sans lire l'onglet. Une clé `couleur` sur le
  // livre passe devant, pour le volume qui ne ressemble à aucun autre.
  const TYPES = {
    registre: { nom: "Registre", teinte: "var(--book-registre)" },
    carnet:   { nom: "Carnet",   teinte: "var(--book-carnet)" },
    plan:     { nom: "Plan",     teinte: "var(--book-plan)" },
    memento:  { nom: "Mémento",  teinte: "var(--book-memento)" },
    dossier:  { nom: "Dossier",  teinte: "var(--book-dossier)" },
    regle:    { nom: "Règle",    teinte: "var(--book-regle)" },
    oeuvre:   { nom: "Œuvre",    teinte: "var(--book-oeuvre)" },
  };
  const genre = (b) => TYPES[String(b.type || "").toLowerCase()] || null;
  const teinte = (b) => b.couleur || (genre(b) || {}).teinte || "var(--braise)";

  const sansAccent = (s) => String(s == null ? "" : s)
    .normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  // LE GENRE DE LA COLONNE SE MESURE, il ne se déclare pas. On regarde les
  // cellules : si tout ce qui n'est pas vide se lit comme un nombre, on compare
  // des nombres ; sinon on compare des mots, en français, l'emoji de tête et
  // les appuis retirés — sans quoi « 🪶 Se donner un exécutant » se rangerait
  // sous 🪶 et toutes les lignes d'un même signe formeraient un bloc.
  const nuTexte = (s) => String(s == null ? "" : s)
    .replace(/\*\*/g, "")
    .replace(/^\s*\p{Extended_Pictographic}️?\s*/u, "")
    .trim();
  const nombreDe = (s) => {
    const t = nuTexte(s).replace(/[   ]/g, "").replace(",", ".");
    return /^-?\d+(\.\d+)?$/.test(t) ? parseFloat(t) : null;
  };


  // Les appuis du MJ : **ce qui pèse** se rend en gras, comme dans le fil.
  // Un registre a besoin d'appuis plus qu'un récit : c'est là que tombent les
  // états et les liens (**acquis**, **contre**, **au loin**).
  const echappe = (s) => s.replace(/[&<>]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);

  function poser(el, texte) {
    const t = texte == null ? "" : String(texte);
    el.innerHTML = echappe(t).replace(/\*\*(\S(?:[^*]*\S)?)\*\*/g,
      '<b class="appui">$1</b>');
  }


  function lignesDe(b) {
    return (b.lignes || []).map((l) =>
      Array.isArray(l) ? { cellules: l } : (l || { cellules: [] }));
  }

  // ---- les tableaux d'un volume ---------------------------------------------
  // Un registre n'a qu'un tableau : c'est une seule sorte de chose, rangée. Une
  // AFFAIRE en a plusieurs, et pas par confort — ses états cibles, ses verrous,
  // ses clefs et ses actions n'ont pas les mêmes colonnes, et les entasser dans
  // une grille commune obligerait à inventer une colonne fourre-tout par type.
  // Donc `tables: [{titre, colonnes, lignes}]`, et le vieux couple
  // colonnes/lignes reste la forme courte du volume qui n'en a qu'un.
  function tableauxDe(b) {
    if (Array.isArray(b.tables) && b.tables.length) {
      return b.tables.map((t) => ({
        titre: t.titre || "",
        colonnes: t.colonnes || [],
        lignes: lignesDe(t),
      }));
    }
    return [{ titre: "", colonnes: b.colonnes || [], lignes: lignesDe(b) }];
  }

  // ---- Les renvois : un numéro écrit, et la ligne qui le définit ------------
  // Un cahier d'affaire ne se lit pas de haut en bas, il se lit en sautant :
  // « bloque 23100 », « dépend de 24000 », « ouvre 23010 ». Tout s'y cite par
  // son numéro, et jusqu'ici il fallait aller le chercher à la main, souvent
  // dans un autre volume. On accroche donc chaque numéro à la ligne qui le
  // porte — la donnée est déjà là, il n'y manquait que le chemin.
  //
  // L'ADRESSE d'une ligne est sa première cellule, dans un tableau dont la
  // première colonne s'appelle « N° ». Quatre à six chiffres : en deçà, un
  // numéro ne se distingue plus d'une quantité, et l'on accrocherait les douze
  // hommes de la barque. L'emoji qui précède un renvoi dit sa FAMILLE (état,

  // L'ADRESSE d'une ligne, et la série de son affaire. Deux pièces s'en
  // servent — la grille, qui pose l'ancre, et les renvois, qui la visent —,
  // donc elles se lisent ici et non dans l'une des deux.
  //
  // L'ADRESSE d'une ligne est sa première cellule, dans un tableau dont la
  // première colonne s'appelle « N° ». Quatre à six chiffres : en deçà, un
  // numéro ne se distingue plus d'une quantité, et l'on accrocherait les douze
  // hommes de la barque. L'emoji qui précède un renvoi dit sa FAMILLE (état,
  // verrou, clef, action) — il ne sert pas à le reconnaître, le numéro suffit.
  const NUMERO = /\b\d{4,6}\b/g;
  // Une table porte des adresses si sa premiere colonne est un N° (les plans)
  // OU si ses lignes commencent par un numero (les REGISTRES tamponnes en
  // serie 9xxxx — D.35, tranche le 31.8 : un fait arrete est adressable).
  const estAdresse = (t) => !!(t.colonnes && t.colonnes.length
    && /N°/.test(String(t.colonnes[0])))
    || (t.lignes || []).some((l) => {
      const c = (l.cellules || [])[0];
      return /^\s*(?:\*\*)?\s*\d{4,6}\b/.test(c == null ? "" : String(c));
    });
  function numeroDe(l) {
    const c = (l.cellules || [])[0];
    const m = /^\s*(?:\*\*)?\s*(\d{4,6})\b/.exec(c == null ? "" : String(c));
    return m ? m[1] : null;
  }
  // Le millier d'un numéro : 23030 → « 23 ». C'est la série de son affaire.
  const serie = (n) => n.slice(0, -3);

  const compte = (n) => n + (n > 1 ? " volumes" : " volume");

  return { TYPES, genre, teinte, sansAccent, nuTexte, nombreDe, echappe, poser,
           lignesDe, tableauxDe, NUMERO, estAdresse, numeroDe, serie, compte };
});
