// croiser.js — ce qu'un marcheur perçoit d'une bataille cuite.
//
// LE PROBLÈME. Le sac produit des centaines de faits datés et situés. La
// balade produit un pas tous les vingt mètres, daté et situé lui aussi. Les
// deux vivent côte à côte et ne se parlent pas : on peut traverser une ville
// en train de tomber sans que rien ne le dise.
//
// LA RÈGLE, ET ELLE EST DÉJÀ ÉCRITE AILLEURS. « Avant de narrer un fait :
// ont-ils une source pour savoir cela ? » Un fait de la bataille ne parvient
// au joueur que si l'un de ses trois était à portée, à cette minute-là. Ce
// module ne fait que répondre à cette question, et il y répond comme le reste
// du dépôt répond aux siennes : par une FONCTION PURE de (où, quand). Rien
// n'est stocké, rien n'est rejoué, rien ne se simule ici.
//
// TROIS PORTÉES, PARCE QU'UN HOMME N'A PAS QU'UN SENS. C'est tout le système,
// et c'est ce qui le rend général :
//
//   vu       — c'est en train d'arriver, et c'est dans la rue. Le détail :
//              qui, quoi. Une porte qui cède sous vos yeux.
//   entendu  — c'est en train d'arriver, loin. AUCUN détail, une direction et
//              rien de plus. C'est le seul canal qui tourne au coin d'une rue,
//              et c'est celui qui porte le plus loin de tous.
//   trace    — c'est DÉJÀ arrivé, et ça a laissé quelque chose par terre. Un
//              blessé qui respire, une porte défoncée, du sang sur un seuil.
//              Ça ne s'entend pas et ça ne s'invente pas : ça se voit en
//              passant, des heures après, et c'est le vrai gisement de scènes.
//
// LA TABLE EST LE SYSTÈME. Un type de fait, trois nombres, une persistance.
// Tout comportement qu'on ajoutera un jour — un pillard, un porteur d'ordre,
// une barricade — devient perceptible en écrivant SA LIGNE et rien d'autre.
// C'est le seul endroit à toucher, et c'est délibéré : un comportement neuf ne
// doit pas demander de retoucher la balade.
//
// PAS DE FICHIER, PAS DE BATAILLE, ZÉRO COÛT. Sans `etat/bataille.json`, tout
// ce module rend `null` au premier test et ne lit rien. C'est le cas normal.
"use strict";

const fs = require("fs");
const path = require("path");

// --- LA TABLE DES PORTÉES ---------------------------------------------------
// `vu` et `entendu` sont des mètres. `trace` est la durée en SECONDES pendant
// laquelle le fait reste lisible au sol après qu'il s'est produit — `0` pour ce
// qui ne laisse rien, `Infinity` pour ce qu'on retrouvera au matin.
//
// Les chiffres ne sont pas des réglages de difficulté : ce sont des mesures.
// Une porte bardée de fer qu'on enfonce s'entend à sept cents mètres dans une
// ville de nuit ; un homme qui tombe ne s'entend pas à quarante.
const PORTEES = {
  "porte-cede":       { vu: 80,  entendu: 500, trace: 0 },
  "porte-enfoncee":   { vu: 80,  entendu: 700, trace: Infinity, trace_vu: 60 },
  "contact":          { vu: 60,  entendu: 250, trace: 0 },
  // Un corps qu'on relève, un pavé noirci : ça se voit du trottoir d'en face.
  "premier-sang":     { vu: 50,  entendu: 0,   trace: 3600, trace_vu: 20 },
  "blesse":           { vu: 40,  entendu: 35,  trace: Infinity },
  "blesse-succombe":  { vu: 30,  entendu: 0,   trace: Infinity },
  "blesse-tient":     { vu: 30,  entendu: 25,  trace: Infinity },
  "chef-tombe":       { vu: 50,  entendu: 60,  trace: 1800 },
  "tete-tombe":       { vu: 60,  entendu: 90,  trace: 3600 },
  "escouade-rompt":   { vu: 120, entendu: 150, trace: 0 },
  "escouade-sourde":  { vu: 0,   entendu: 0,   trace: 0 },
  "ralliement":       { vu: 90,  entendu: 110, trace: 0 },
  "ordre":            { vu: 40,  entendu: 60,  trace: 0 },
  "assaut-au-donjon": { vu: 150, entendu: 400, trace: 0 },
  "peur-gagne":       { vu: 60,  entendu: 80,  trace: 0 },
  "rumeur-gagne":     { vu: 60,  entendu: 0,   trace: 0 },
  "guet-a-vu":        { vu: 70,  entendu: 0,   trace: 0 },
  // LE FEU EST LE FAIT QUI PORTE LE PLUS LOIN DE TOUS, et de très loin. Une
  // maison qui brûle se voit d'un bout à l'autre d'un quartier, s'entend
  // moins qu'elle ne se voit, et laisse un trou noir dans la rue pour le
  // reste de la partie. C'est aussi le seul acte de cette nuit qui change la
  // ville pour de bon : sa trace ne s'éteint jamais.
  "maison-brulee":    { vu: 600, entendu: 200, trace: Infinity, trace_vu: 400 },
  // UN VOISIN QUI SORT AVEC UNE HACHE — ou celui d'en face qui met une planche
  // en travers de sa porte. Ça se voit dans la rue, ça ne s'entend pas, et ça
  // reste toute la nuit : sa porte est ouverte et il n'est pas chez lui. C'est
  // la trace la plus jouable de toutes, parce qu'elle a une ADRESSE et qu'elle
  // attend qu'on vienne lui demander où il était.
  "prend-les-armes":  { vu: 40,  entendu: 0,   trace: Infinity, trace_vu: 30 },
  // La chaîne de commandement se voit de près et ne s'entend pas : un coureur
  // qui part est un homme qui court, rien de plus, et il faut être dans la
  // même rue pour comprendre que c'en est un.
  "coureur-part":     { vu: 40,  entendu: 0,   trace: 0 },
  "coureur-arrive":   { vu: 40,  entendu: 0,   trace: 0 },
  "coureur-tombe":    { vu: 45,  entendu: 0,   trace: 900 },
  "banniere-tombe":   { vu: 130, entendu: 0,   trace: 600 },
  "banniere-relevee": { vu: 130, entendu: 0,   trace: 0 },
  "nouveau-chef":     { vu: 35,  entendu: 0,   trace: 0 },
  "escouade-reprise": { vu: 60,  entendu: 0,   trace: 0 },
  // Ce que chaque corps EST ne se perçoit pas : c'est une note du fichier sur
  // lui-même, pas un événement de la rue. Portée nulle, et c'est voulu.
  "corps-ferme":      { vu: 0,   entendu: 0,   trace: 0 },
  "corps-sourd":      { vu: 0,   entendu: 0,   trace: 0 },
  "corps-versatile":  { vu: 0,   entendu: 0,   trace: 0 },
};
// Ce qu'on ne connaît pas se voit de près et ne s'entend pas. Un fait neuf
// arrive donc timidement plutôt que de crier à travers la ville — c'est le bon
// défaut : on l'oublie dans la table sans que la partie devienne fausse.
const DEFAUT = { vu: 45, entendu: 0, trace: 0 };

// CE QUI ARRÊTE UNE MARCHE. Le manuel le dit déjà : « ce qui se lève en chemin
// devient un fil, et alors on arrête de marcher. » On ne le laisse pas au
// jugé — un joueur qui traverse un assaut sans que ses jambes s'arrêtent a
// perdu la scène. Ces faits-là, VUS, coupent la balade.
const ARRETENT = new Set(["porte-cede", "porte-enfoncee", "contact",
  "escouade-rompt", "assaut-au-donjon", "tete-tombe", "blesse",
  // Une maison qui brûle dans la rue où l'on marche arrête n'importe qui.
  "maison-brulee"]);

// L'instant vaut une demi-minute de part et d'autre : c'est ce qu'un pas de
// balade couvre, et l'on ne prétend pas mieux.
const INSTANT_S = 30;

// --- le sac, chargé une fois -------------------------------------------------
let _cache = null;

// C'EST `etat/bataille.json` QUI NOMME LE SAC, PAS LE LIEU. Le `lieu` qui
// arrive ici est l'identifiant du monde 3D — « port-real » —, et le fichier
// cuit s'appelle `portreal.sac.annales.json` : le tiret. On construisait le
// chemin depuis le lieu, donc on cherchait `port-real.sac.annales.json`, qui
// n'existe pas ; `charger` attrapait l'erreur et rendait `null`. Résultat : une
// bataille datée, un joueur qui la traverse, et RIEN — pas un bruit, pas une
// trace, pas un message d'erreur. Le seul défaut qui ne se voit jamais est
// celui qui rend la même chose que le cas normal.
//
// Le champ `sac` existait depuis le début et n'était lu par personne. Il fait
// désormais foi ; le lieu ne sert que de dernier recours, et l'absence du
// fichier se dit tout haut (voir `charger`) au lieu de se taire.
function clefFichiers(racine, nom) {
  const a = path.join(racine, "monde", nom + ".sac.annales.json");
  const mt = (f) => { try { return fs.statSync(f).mtimeMs; } catch (e) { return 0; } };
  return { a, sceau: mt(a) };
}

function fichierEtat(racine) {
  return path.join(racine, "etat", "bataille.json");
}

/**
 * Le sac en cours, ou null. Deux fichiers, et les deux sont nécessaires :
 *
 *   `monde/<lieu>.sac.annales.json` — ce qui s'est passé, en secondes de
 *      bataille. C'est du monde engendré : régénérable, jamais écrit à la main.
 *   `etat/bataille.json` — QUAND ça se passe dans la partie, et où en est la
 *      lecture. C'est une décision de jeu, donc c'est dans `etat/`.
 *      { "sac": "portreal", "debut": { "jour": 3, "minute": 1200 } }
 *
 * Sans le second, un sac n'est qu'un fichier : ses secondes ne tombent sur
 * aucune heure, et l'on ne peut RIEN en croiser. C'est voulu — une bataille
 * cuite n'est pas une bataille en cours tant qu'un MJ ne l'a pas datée.
 */
function charger(racine, lieu) {
  const b = fichierEtat(racine);
  const mtEtat = (() => { try { return fs.statSync(b).mtimeMs; } catch (e) { return 0; } })();
  if (!mtEtat) { _cache = { sceau: "0", sac: null }; return null; }
  let etat = null;
  try { etat = JSON.parse(fs.readFileSync(b, "utf-8")); } catch (e) { etat = null; }
  if (!etat || !etat.debut || typeof etat.debut.minute !== "number") return null;

  // Le sac nommé dans l'état ; à défaut le lieu, débarrassé de ses tirets —
  // « port-real » et « portreal » désignent la même ville, et un fichier cuit
  // ne porte pas les tirets de l'identifiant de monde.
  const nom = etat.sac || String(lieu || "portreal").replace(/-/g, "");
  const { a, sceau } = clefFichiers(racine, nom);
  const clef = nom + ":" + sceau + ":" + mtEtat;
  if (_cache && _cache.sceau === clef) return _cache.sac;

  let sac = null;
  try {
    const ann = JSON.parse(fs.readFileSync(a, "utf-8"));
    if (ann && Array.isArray(ann.detail)) {
      sac = { debut: etat.debut, faits: ann.detail, lieu: lieu || "portreal", nom };
      eteindre(sac.faits);
    }
  } catch (e) { sac = null; }
  // ON LE DIT QUAND ON NE TROUVE PAS. Une bataille datée dont le sac est
  // introuvable est une faute de MJ — un nom mal tapé, un sac jamais cuit — et
  // elle se répare en dix secondes SI on l'apprend. Sans cette ligne, elle se
  // joue comme une nuit tranquille et l'on cherche l'erreur ailleurs.
  if (!sac && (!_cache || _cache.sceau !== clef))
    console.error("croiser : bataille datée, mais monde/" + nom +
                  ".sac.annales.json est illisible ou absent — rien ne sera perçu.");
  _cache = { sceau: clef, sac };
  return sac;
}

// --- UNE TRACE PEUT EN ANNULER UNE AUTRE -----------------------------------
// Le défaut se voyait à la lecture et il était grave. Un blessé laisse une
// trace ÉTERNELLE — on le retrouve au matin, c'est tout l'intérêt du
// personnage. Mais quand la plaie a tranché, le sac écrit un second fait,
// `blesse-succombe`, au même endroit — et l'ancien continuait de courir. Le MJ
// lisait donc, à la même minute et à cinq pas l'un de l'autre :
//
//     TRACE  un blessé qui respire encore   (depuis 58 min)
//     TRACE  un blessé a cessé d'appeler    (depuis 54 min)
//
// C'est le même homme. Et le MJ qui fait parler le premier fait parler un
// mort — ce qui n'est pas une imprécision de rendu, c'est un fait faux servi
// au joueur, avec une bouche et une adresse.
//
// On apparie donc une fois, au chargement : chaque `blesse-succombe` éteint le
// `blesse` le plus proche qui le précède. Le blessé garde sa trace jusqu'à sa
// mort, et pas une seconde de plus.
const MEME_HOMME = 4;       // mètres : deux faits si proches sont le même corps

function eteindre(faits) {
  const vivants = faits.filter((f) => f.quoi === "blesse");
  for (const m of faits) {
    if (m.quoi !== "blesse-succombe" && m.quoi !== "blesse-tient") continue;
    let meilleur = null, dmin = MEME_HOMME;
    for (const b of vivants) {
      if (b.t > m.t || b._suite !== undefined) continue;
      const d = Math.hypot(b.x - m.x, b.y - m.y);
      if (d <= dmin) { dmin = d; meilleur = b; }
    }
    if (!meilleur) continue;
    // `blesse-tient` ne l'éteint PAS : il est toujours là, toujours vivant, et
    // c'est même la bonne nouvelle. On note seulement qu'il ne saigne plus.
    if (m.quoi === "blesse-succombe") meilleur._jusqua = m.t;
    meilleur._suite = m.quoi;
  }
}

/**
 * Les minutes absolues d'une date de partie.
 *
 * LA LUNE COMPTE, ET ELLE NE COMPTAIT PAS. On additionnait `jour * 1440 +
 * minute` et rien d'autre : une bataille datée du 3e jour tombait donc le 3e
 * jour de CHAQUE lune et de chaque année, indéfiniment. Personne ne s'en
 * serait aperçu tout de suite — la première nuit se joue juste, et c'est la
 * deuxième lune qui rejoue l'assaut trente jours plus tard, sans que rien
 * n'explique pourquoi la porte tombe une seconde fois.
 *
 * `ref` sert aux dates écrites à l'ancienne, qui n'ont que `jour` et `minute` :
 * on les lit alors dans la lune où l'on se trouve, qui est ce que le MJ voulait
 * dire en tapant `--dater 3 1200`. Les nouvelles portent leur lune (voir
 * `scripts/bataille.py --dater`) et n'ont pas besoin de ce filet.
 */
const enMinutes = (d, ref) => {
  if (!d || typeof d.jour !== "number") return null;
  const a = typeof d.annee === "number" ? d.annee : (ref && ref.annee) || 0;
  const l = typeof d.lune === "number" ? d.lune : (ref && ref.lune) || 1;
  return ((a * 12 + l) * 30 + d.jour) * 1440 + (d.minute || 0);
};

/**
 * Ce qu'on perçoit d'ici, maintenant.
 *
 * @param racine  le dossier du dépôt
 * @param lieu    « portreal »
 * @param x,y     les mètres du marcheur
 * @param date    { jour, minute } — celle du pas
 * @returns null s'il n'y a pas de bataille datée, sinon
 *          { vu:[], entendu:[], traces:[], arret:bool }
 */
function autour(racine, lieu, x, y, date) {
  const sac = charger(racine, lieu);
  if (!sac) return null;
  const now = enMinutes(date), t0 = enMinutes(sac.debut, date);
  if (now === null || t0 === null) return null;
  // Secondes écoulées depuis le premier pas de la bataille.
  const ecoule = (now - t0) * 60;
  // Avant qu'elle commence, il n'y a rien à percevoir — et surtout pas ses
  // traces : une porte n'est pas enfoncée la veille.
  if (ecoule < -INSTANT_S) return { vu: [], entendu: [], traces: [], arret: false };

  const vu = [], entendu = [], traces = [];
  for (const f of sac.faits) {
    const p = PORTEES[f.quoi] || DEFAUT;
    const dx = f.x - x, dy = f.y - y;
    const d = Math.hypot(dx, dy);
    const dt = ecoule - f.t;                    // > 0 : c'est déjà arrivé

    // 1. EN TRAIN D'ARRIVER. Le plus proche des sens gagne : ce qu'on voit,
    //    on ne se contente pas de l'entendre.
    if (Math.abs(dt) <= INSTANT_S) {
      if (d <= p.vu) { vu.push(dire(f, d, "vu", undefined, dx, dy)); continue; }
      if (d <= p.entendu) {
        entendu.push(dire(f, d, "entendu", undefined, dx, dy)); continue;
      }
    }
    // 2. DÉJÀ ARRIVÉ, ET ÇA TIENT ENCORE. La trace ne s'entend jamais — elle
    //    ne fait plus de bruit — et elle s'éteint quand un fait postérieur l'a
    //    remplacée : un blessé qui a succombé n'est plus un blessé.
    if (dt <= INSTANT_S || !(p.trace > 0) || dt > p.trace) continue;
    if (f._jusqua !== undefined && ecoule > f._jusqua) continue;
    // LA PORTÉE D'UNE TRACE N'EST PAS CELLE DE L'ÉVÉNEMENT, et elle n'est pas
    // non plus la même pour toutes. On ne repère pas un blessé à quarante pas
    // dans une rue du Culpucier — mais une porte de ville défoncée se voit du
    // bout de la rue, et une maison brûlée d'un bout à l'autre du quartier.
    // Le plafond unique à vingt-cinq mètres rendait ces deux-là invisibles,
    // c'est-à-dire qu'il annulait les seules traces qui marquent la ville.
    const portee = p.trace_vu !== undefined ? p.trace_vu : Math.min(p.vu, 25);
    if (d <= portee) traces.push(dire(f, d, "trace", dt, dx, dy));
  }
  // On ne rend pas tout : au plus proche, et peu. Le reste est du bruit, et le
  // manuel est formel — deux à quatre items pour une balade entière.
  const trier = (l) => l.sort((a, b) => a.a - b.a).slice(0, 4);
  const r = { vu: trier(vu), entendu: trier(entendu), traces: trier(traces) };
  r.arret = r.vu.some((e) => ARRETENT.has(e.quoi));
  return r;
}

// EN PAS, JAMAIS EN MÈTRES — c'est la règle du jeu, et elle vaut ici comme
// dans la balade : personne, dans cette ville, ne mesure une rue en mètres.
const PAS_M = 0.75;
const enPas = (m) => Math.round(m / PAS_M / 5) * 5;

// LE CAP, EN MOTS D'ÉPOQUE. Personne ne dit « azimut 135 » : on dit « vers le
// levant », et l'on montre du doigt. Huit aires suffisent — au-delà, on
// prétend une précision que l'oreille n'a pas.
const AIRES = ["au nord", "au nord-est", "au levant", "au sud-est",
               "au sud", "au sud-ouest", "au couchant", "au nord-ouest"];
function cap(dx, dy) {
  if (!isFinite(dx) || !isFinite(dy) || (!dx && !dy)) return null;
  // Le plan a son y vers le sud, comme toute image : un dy positif descend.
  const a = Math.atan2(dx, -dy);                    // 0 = nord, sens horaire
  const i = Math.round(((a + Math.PI * 2) % (Math.PI * 2)) / (Math.PI / 4)) % 8;
  return AIRES[i];
}

function dire(f, d, comment, depuis, dx, dy) {
  const o = { quoi: f.quoi, comment, a: Math.round(d), pas: enPas(d),
              ou: f.ou || null, quartier: f.quartier || null,
              _dx: dx, _dy: dy };
  // CE QU'ON ENTEND N'A PAS DE DÉTAIL, et c'est le point. Un fracas au loin
  // est un fracas : ni son auteur, ni son camp, ni son nom. Recopier la fiche
  // du fait ici rendrait au joueur, par la bande, tout ce que le brouillard
  // lui refuse — et personne ne s'en apercevrait.
  if (comment === "entendu") {
    // LE LIEU D'UN BRUIT EST UNE DIRECTION, PAS UN NOM. `f.quartier` est vide
    // dès qu'un repère est proche — c'est voulu du côté des annales, où le
    // repère l'emporte — et ce champ rendait donc `null` exactement pour les
    // faits les plus intéressants : « un fracas, quelque part ». On donnait au
    // joueur un bruit sans origine, ce qui n'est pas du brouillard mais du
    // vide.
    //
    // Ce qu'un homme sait vraiment d'un fracas lointain, c'est D'OÙ IL VIENT.
    // On rend donc un cap depuis le marcheur, plus le quartier — `zone` vaut
    // toujours, lui — et jamais le repère : entendre une porte tomber ne dit
    // pas LAQUELLE.
    o.ou = f.zone || f.quartier || null;
    o.vers = cap(o._dx, o._dy);
    delete o._dx; delete o._dy;
    return o;
  }
  delete o._dx; delete o._dy;
  if (f.nom) o.nom = f.nom;
  if (f.camp) o.camp = f.camp;
  if (f.corps) o.corps = f.corps;
  if (f.chef) o.chef = f.chef;
  if (depuis !== undefined) {
    // Depuis combien de temps c'est là : une heure change tout ce qu'on peut
    // encore faire d'un blessé.
    o.depuis_min = Math.round(depuis / 60);
  }
  return o;
}

module.exports = { autour, charger, PORTEES, ARRETENT, enMinutes };

// ---------------------------------------------------------------------------
// EN LIGNE DE COMMANDE — pour que le MJ puisse poser la question sans passer
// par un navigateur et sans qu'on réécrive la table des portées ailleurs.
//
//     node serveur/croiser.js <lieu> <x> <y> <annee> <lune> <jour> <minute>
//
// Rend le même objet que `autour()`, en JSON, sur la sortie standard.
// C'est ce qu'appelle `scripts/bataille.py --maintenant`. La doctrine est
// celle du four, qui importe `bataille2d.js` plutôt que de le refaire : deux
// implémentations d'une même perception, ce sont deux brouillards, et l'on
// passe ses soirées à chercher lequel ment.
if (require.main === module) {
  const [lieu, x, y, annee, lune, jour, minute] = process.argv.slice(2);
  const racine = path.dirname(__dirname);
  const r = autour(racine, lieu, +x, +y,
                   { annee: +annee, lune: +lune, jour: +jour, minute: +minute });
  process.stdout.write(JSON.stringify(r));
}
