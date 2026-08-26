// traces.js — LE JOURNAL DE DÉCISION : pourquoi il a fait ça, à cette seconde-là.
//
// CE QUI MANQUAIT. On sait dire ce qu'un homme a FAIT — il est là, il tient,
// il est mort. On ne sait pas dire ce qu'il ESSAYAIT de faire, ni ce qu'il
// avait envisagé d'autre. Alors, devant une bataille qui tourne mal, il ne
// reste qu'à rejouer en regardant l'écran et à deviner. Une capture exportée à
// 115 secondes doit répondre sans rejouer : que croyait-il, quelles options
// a-t-il envisagées, pourquoi celle-ci, et quand devait-il réexaminer.
//
// DEUX SORTES D'ÉCRITURES, ET IL NE FAUT PAS LES MÉLANGER.
//
//   `noter(genre, texte, details)` — un ÉVÉNEMENT : un message livré, une
//     croyance qui bouge, un contrat rompu, un téléport refusé. C'est court, ça
//     arrive souvent, et ça n'a pas d'auteur qui délibère.
//
//   `decider(trace)` — une DÉCISION, au format `TraceDecision` des contrats :
//     un acteur, ses croyances, ses options, son choix, sa raison, son prochain
//     examen. C'est rare, c'est cher, et c'est ce qu'on relit.
//
// L'ANNEAU EST BORNÉ, ET C'EST LA CONDITION POUR QU'ON PUISSE LE LAISSER
// ALLUMÉ. Une bataille de mille hommes sur dix minutes produirait des centaines
// de milliers de lignes ; un journal qui fait tomber l'onglet est un journal
// qu'on éteint, et un journal qu'on éteint ne sert jamais le jour où il
// faudrait. On garde donc les N derniers de chaque sorte, et l'on garde EN PLUS
// la dernière décision de chaque acteur, quel que soit son âge — parce que
// « que croyait-il » n'a pas de réponse si sa seule trace vient d'être poussée
// hors de l'anneau par le bavardage des autres.
//
// IL N'ÉCRIT RIEN SUR LE DISQUE. C'est de la mémoire de session, lue par le
// panneau de debug, par la bulle de pensée et par l'export d'une marque.
"use strict";

(function (racine, fabrique) {
  const api = fabrique(racine);
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleTraces = api;
})(typeof window !== "undefined" ? window : globalThis, function (racine) {

  const PLAFOND_EVENEMENTS = 4000;
  const PLAFOND_DECISIONS = 1500;

  let allume = true;
  let horloge = () => null;             // le temps de simulation, en secondes
  let compteur = 0;

  const evenements = [];                // anneau
  const decisions = [];                 // anneau
  const derniere = new Map();           // acteurId -> sa dernière décision

  /** Qui donne l'heure. Le moteur la pose une fois ; personne d'autre. */
  function reglerHorloge(fn) { horloge = (typeof fn === "function") ? fn : () => null; }
  function maintenant() { const t = horloge(); return typeof t === "number" ? t : null; }

  function ecrire(anneau, plafond, ligne) {
    anneau.push(ligne);
    if (anneau.length > plafond) anneau.splice(0, anneau.length - plafond);
    return ligne;
  }

  // -------------------------------------------------------------------------
  // LES ÉVÉNEMENTS
  // -------------------------------------------------------------------------
  /**
   * `noter` — une ligne de journal. `genre` est ce sur quoi on filtrera plus
   * tard : "message", "croyance", "contrat", "teleport", "route", "rupture".
   * On ne ferme pas ce vocabulaire : un genre inventé le jour où il sert vaut
   * mieux qu'une ligne rangée de force dans un genre qui ne la décrit pas.
   */
  function noter(genre, texte, details) {
    if (!allume) return null;
    return ecrire(evenements, PLAFOND_EVENEMENTS, {
      n: ++compteur,
      a: maintenant(),
      genre: genre || "note",
      texte: texte || "",
      acteurId: details && details.acteurId != null ? details.acteurId : null,
      details: details || null,
    });
  }

  // -------------------------------------------------------------------------
  // LES DÉCISIONS
  // -------------------------------------------------------------------------
  /**
   * `decider` — enregistre une `TraceDecision`. On ne la valide PAS ici : la
   * validation appartient aux contrats, et un journal qui refuserait une trace
   * mal formée perdrait précisément celle qu'on aurait voulu lire.
   */
  function decider(trace) {
    if (!allume || !trace) return null;
    const ligne = Object.assign({ n: ++compteur }, trace);
    if (ligne.declencheeA == null) ligne.declencheeA = maintenant();
    ecrire(decisions, PLAFOND_DECISIONS, ligne);
    if (ligne.acteurId != null) derniere.set(ligne.acteurId, ligne);
    return ligne;
  }

  /** La dernière décision d'un acteur — jamais poussée hors de l'anneau. */
  function pour(acteurId) { return derniere.get(acteurId) || null; }

  /** Les acteurs dont on a une décision, du plus récent au plus ancien. */
  function acteurs() {
    return Array.from(derniere.values())
      .sort((a, b) => (b.declencheeA || 0) - (a.declencheeA || 0))
      .map((d) => d.acteurId);
  }

  // -------------------------------------------------------------------------
  // LA LECTURE — un seul filtre, six critères, tous facultatifs
  //
  // C'est ce que le panneau de debug branche sur ses six cases : par acteur,
  // par seconde de simulation, par mission ou ordre, par option choisie ou
  // rejetée, par changement de croyance, par livraison de message.
  // -------------------------------------------------------------------------
  function filtrer(quoi) {
    quoi = quoi || {};
    const dansTemps = (t) =>
      (quoi.de == null || (t != null && t >= quoi.de)) &&
      (quoi.a == null || (t != null && t <= quoi.a));

    let d = decisions.filter((x) => dansTemps(x.declencheeA));
    if (quoi.acteurId != null) d = d.filter((x) => x.acteurId === quoi.acteurId);
    if (quoi.echelon) d = d.filter((x) => x.echelon === quoi.echelon);
    if (quoi.ordreId) d = d.filter((x) => x.ordreCourant &&
      (x.ordreCourant.id === quoi.ordreId || x.ordreCourant === quoi.ordreId));
    if (quoi.choix) d = d.filter((x) => x.choix === quoi.choix);
    if (quoi.option) d = d.filter((x) => (x.options || [])
      .some((o) => o.action === quoi.option));
    if (quoi.rejete) d = d.filter((x) => (x.options || [])
      .some((o) => o.action === quoi.rejete && o.action !== x.choix));

    let e = evenements.filter((x) => dansTemps(x.a));
    if (quoi.acteurId != null) e = e.filter((x) => x.acteurId === quoi.acteurId);
    if (quoi.genre) e = e.filter((x) => x.genre === quoi.genre);

    // Un filtre qui ne porte que sur les décisions ne doit pas rendre tous les
    // événements du monde : sans ça, cocher « option rejetée » remplit l'écran
    // de lignes de circulation et l'on ne voit plus la décision qu'on cherchait.
    const surDecisions = quoi.choix || quoi.option || quoi.rejete ||
                         quoi.ordreId || quoi.echelon;
    if (surDecisions && !quoi.genre) e = [];

    return { decisions: d, evenements: e };
  }

  /**
   * `reexamensManques` — la mesure que le doc réclame et que rien ne produit
   * aujourd'hui : un acteur dont l'heure de réexamen est passée et qui n'a pas
   * redécidé. Zéro attendu, sauf impossibilité tracée.
   */
  function reexamensManques(t) {
    const quand = (t == null) ? maintenant() : t;
    if (quand == null) return [];
    const manques = [];
    derniere.forEach((d, acteurId) => {
      if (d.prochainExamenA != null && d.prochainExamenA < quand)
        manques.push({ acteurId, echelon: d.echelon, du: d.prochainExamenA,
                       retard: quand - d.prochainExamenA, choix: d.choix });
    });
    return manques.sort((a, b) => b.retard - a.retard);
  }

  // -------------------------------------------------------------------------
  // L'EXPORT — ce qu'une marque emporte
  //
  // On garde PRIORITAIREMENT LA FIN, comme le veut le doc pour les perceptions :
  // ce qui explique une mauvaise décision est ce qui la précède de peu, pas
  // l'ouverture de la bataille.
  // -------------------------------------------------------------------------
  function extraire(opts) {
    opts = opts || {};
    const combien = opts.combien || 120;
    const filtre = filtrer(opts);
    return {
      a: maintenant(),
      acteurId: opts.acteurId == null ? null : opts.acteurId,
      decisions: filtre.decisions.slice(-combien),
      evenements: filtre.evenements.slice(-combien),
      derniere: opts.acteurId != null ? pour(opts.acteurId) : null,
      reexamensManques: reexamensManques(),
    };
  }

  function etat() {
    return { allume, evenements: evenements.length, decisions: decisions.length,
             acteurs: derniere.size, a: maintenant() };
  }

  /** Vider — au `vider()` du moteur, jamais en cours de bataille. */
  function vider() {
    evenements.length = 0; decisions.length = 0; derniere.clear(); compteur = 0;
  }

  function allumer(x) { if (x !== undefined) allume = !!x; return allume; }

  return { noter, decider, pour, acteurs, filtrer, reexamensManques,
           extraire, etat, vider, allumer, reglerHorloge,
           PLAFOND_EVENEMENTS, PLAFOND_DECISIONS };
});
