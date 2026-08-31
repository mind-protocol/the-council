// -*- coding: utf-8 -*-
/**
 * banc-moteur.js — L'ÉTALON DU MOTEUR, pour qu'un déplacement de blocs se voie.
 *
 *     node ecrans/modules/bataille/banc-moteur.js            compare à l'étalon
 *     node ecrans/modules/bataille/banc-moteur.js --poser    (re)pose l'étalon
 *     node ecrans/modules/bataille/banc-moteur.js --hommes 200 --duree 90
 *
 * POURQUOI CE FICHIER EXISTE. `bataille2d.js` fait sept mille lignes et l'on
 * s'apprête à en sortir la peinture, puis la mise en place, puis à trancher la
 * migration des couches. Ce sont des DÉPLACEMENTS DE BLOCS : rien n'est censé
 * changer, et c'est précisément ce qu'on ne sait pas vérifier. Les deux bancs
 * de la maison portent sur les couches (`banc-qui-conduit.js`,
 * `banc-reflexion-adapt.js`) ; aucun ne porte sur la bataille elle-même. Sans
 * étalon, un bloc déplacé de travers ne se voit qu'à la nuit où l'on relit des
 * annales qui n'ont plus de sens, six semaines plus tard.
 *
 * IL N'A PAS DE JUGEMENT, ET C'EST VOULU. Il ne dit pas si la bataille est
 * BONNE — il dit si elle est LA MÊME. Un banc qui aurait un avis sur la
 * qualité d'une nuit devrait être réécrit chaque fois qu'on améliore le
 * modèle ; celui-ci se repose d'un `--poser` et l'on écrit dans le message de
 * commit ce qui a bougé et pourquoi.
 *
 * L'ATTENDU EST ZÉRO, JAMAIS « À PEU PRÈS ». C'est l'article 2 de la règle de
 * lecture de l'étalon 90110 (`analyse/etalon-90110/REGLE-DE-LECTURE.md`) et il
 * ne se négocie pas : à condition identique et graine tenue, la cuisson est
 * déterministe. Un écart non nul n'est pas une tolérance à élargir, c'est la
 * reproductibilité qui est cassée. On ne trouvera donc ici aucun seuil.
 *
 * CE QU'IL COMPARE, ET CE QU'IL SE REFUSE À COMPARER. L'issue (morts, blessés,
 * fuyards, effectifs par camp, l'état des verrous), la répartition des états,
 * et le compte des faits d'annales PAR TYPE. Jamais une position individuelle :
 * `hasard.js` n'a qu'une urne, un seul tirage décalé rebat tout ce qui suit, et
 * une liste de coordonnées ne dirait pas mieux « ce n'est plus la même
 * bataille » qu'un compte de morts — elle dirait seulement la même chose en
 * cinq mille lignes.
 *
 * IL N'ÉCRIT QUE SON ÉTALON. Rien dans `etat/`, rien dans `monde/`, aucune
 * tranche, aucune annale : ce n'est pas un four, c'est une balance.
 *
 * LA VILLE N'EST PAS CHARGÉE, et ce n'est pas une économie — c'est la
 * condition. `sac.js` lit le jour et la minute EN DIRECT dans `etat/monde.json`
 * pour faire sa tournée d'habitants : la même commande n'y cuit donc pas la
 * même nuit deux jours de suite. Un étalon qui dépendrait de l'heure de la
 * partie ne serait pas un étalon. Le banc monte la chaîne seule, comme
 * `analyse/etalon-90110/deux-causes.js`.
 *
 * IL EMPRUNTE SA MÉCANIQUE AU FOUR, IL NE LA RECOPIE PAS. `planter()` et
 * `chargerBataille()` sont lus dans `scripts/monde/sac.js` et évalués tels
 * quels ; si `sac.js` change de forme au point que l'emprunt ne trouve plus ses
 * morceaux, le banc s'arrête net — il refuse de deviner.
 *
 * LA CHAÎNE, ELLE, NE S'EMPRUNTE PLUS : elle se lit au manifeste
 * `bataille/moteur/chaine.js`, que le four lit aussi, et la page de scène avec
 * lui. C'est mieux qu'un emprunt. Un emprunt recopie une décision prise
 * ailleurs et suppose que l'ailleurs a raison ; le manifeste EST la décision,
 * et le banc mesure alors exactement la chaîne que le navigateur monte. Un
 * morceau découpé demain entre dans le four, dans la page et dans le banc par
 * la même ligne.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { pathToFileURL } = require("url");

const ICI = path.dirname(path.dirname(path.dirname(__dirname)));  // la racine
const MODULES = path.join(ICI, "ecrans", "modules");
const SAC = path.join(ICI, "scripts", "monde", "sac.js");
const ETALON = path.join(__dirname, "etalon-moteur.json");

// ---------------------------------------------------------------------------
// LA CONDITION — courte, et cuite en moins d'une minute
//
// 150 hommes et 100 s, ce n'est pas une bataille intéressante : c'est une
// bataille SUFFISANTE. Il faut que la colonne marche, que le fer se touche, que
// la porte encaisse, que des hommes tombent et que des ordres circulent — au
// delà, chaque seconde de plus est une seconde qu'on ne passera pas à lancer le
// banc. Un banc qu'on n'a pas le temps de lancer ne sert à rien du tout, et
// c'est la seule raison pour laquelle ces deux chiffres sont si petits.
// ---------------------------------------------------------------------------
const DEFAUTS = { hommes: 150, duree: 100, porte: "La porte de la Gadoue",
                  serveur: "", source: "/monde" };
const PAS = 1 / 20;               // le pas du module, et il ne se règle pas ici

function args() {
  const a = process.argv.slice(2), o = Object.assign({}, DEFAUTS);
  o.poser = a.includes("--poser");
  o.uneFois = a.includes("--une-fois");
  o.armes = a.includes("--armes");
  // `--relever` : IMPRIMER LA NUIT AU LIEU DE LA JUGER. Le banc ne savait que
  // dire oui ou non contre un étalon — utile pour la non-régression, muet dès
  // qu'on change une condition et qu'on veut simplement SAVOIR ce qui s'est
  // passé. Un banc qui ne sait pas rapporter oblige à en écrire un second.
  o.relever = a.includes("--relever");
  for (let i = 0; i < a.length; i++) {
    const c = a[i].replace(/^--/, "");
    if (c in DEFAUTS) o[c] = a[++i];
  }
  o.hommes = +o.hommes; o.duree = +o.duree;
  return o;
}

// ---------------------------------------------------------------------------
// L'EMPRUNT AU FOUR
// ---------------------------------------------------------------------------
const sacSrc = fs.readFileSync(SAC, "utf8");
function morceau(quoi, re) {
  const m = sacSrc.match(re);
  if (!m) throw new Error(
    "sac.js a changé de forme : « " + quoi + " » ne s'y retrouve plus.\n" +
    "  Le banc emprunte la mécanique du four au lieu de la recopier ; il ne\n" +
    "  devine pas. Rendez-lui son morceau, ou changez l'emprunt ici.");
  return m[0];
}
// `eval` DIRECT, et pas `(0, eval)` : les morceaux empruntés doivent voir
// `MODULES`, `path`, `fs` et `CHAINE` de CE fichier-ci. En mode strict la
// déclaration reste dans la portée de l'eval, d'où l'expression finale qui en
// ressort la valeur.
/* eslint-disable no-eval */
// LA CHAÎNE NE S'EMPRUNTE PLUS AU FOUR : elle se lit au manifeste, comme le
// four la lit. C'est mieux qu'un emprunt — un emprunt copie une décision prise
// ailleurs, le manifeste EST la décision, et le banc mesure alors exactement la
// chaîne que le navigateur monte. `planter` et `chargerBataille`, eux, restent
// empruntés : ce sont des mécaniques du four, pas des données partagées.
const CHAINE = require(path.join(MODULES, "bataille", "moteur", "chaine.js"))
  .fichiers("moteur");
const planter = eval("(" + morceau("function planter",
  /function planter\(base\) \{[\s\S]*?\n\}/) + ")");
const chargerBataille = eval("(" + morceau("function chargerBataille",
  /function chargerBataille\(\) \{[\s\S]*?\n\}/) + ")");
/* eslint-enable no-eval */

/** L'empreinte d'un fichier de la chaîne — douze hexa, comme au verdict 90110. */
const empreinte = (f) => crypto.createHash("sha256")
  .update(fs.readFileSync(path.join(MODULES, f))).digest("hex").slice(0, 12);

// ---------------------------------------------------------------------------
// LE RELEVÉ — ce qu'on retient d'une nuit, et rien de plus
// ---------------------------------------------------------------------------
function cuire(B, o) {
  const t0 = Date.now();
  B.rejouer(o.porte, o.hommes);
  if (o.armes) {
    const us = B.unites();
    const a = us.filter((u) => u.camp === "assaut" && u.id.startsWith("assaut:"));
    const g = us.filter((u) => u.camp === "garde" && u.id.startsWith("garde:"));
    if (a[0]) B.equiperUnite(a[0].id, "conroi");
    if (a[1]) B.equiperUnite(a[1].id, "pique");
    if (g[0]) B.equiperUnite(g[0].id, "pique");
  }
  const n = Math.round(o.duree / PAS);
  for (let i = 0; i < n; i++) B.pas(PAS);
  const e = B.etat();
  const par = {};
  for (const f of B.faits()) par[f.quoi] = (par[f.quoi] || 0) + 1;
  // UNE CLEF POSÉE À `undefined` N'EST PAS UNE CLEF ABSENTE, et c'est ce qui
  // rendait toute comparaison sans `--armes` perdante. L'étalon s'écrit par
  // `JSON.stringify`, qui jette les `undefined` ; le relevé du jour, lui, garde
  // la clef en mémoire, et l'aplatissement compare alors « rien » à
  // « undefined ». Le banc se déclarait donc en désaccord avec lui-même. On ne
  // pose plus la clef qu'on a réellement quelque chose à y mettre.
  const types = o.armes ? B.unites().filter((u) => u.typeTroupe).map((u) => ({
    id: u.id, type: u.typeTroupe, capacites: u.capacites,
  })) : null;
  const releve = {
    temps: e.temps,
    // L'issue, celle du manifeste du four.
    morts: e.morts, blesses: e.blesses, fuyards: e.fuyards,
    assaut: e.assaut, garde: e.garde,
    // Le verrou de la porte engagée, puis les quatre — laquelle a cédé, à
    // combien de points de bois, et PAR QUOI : une hache et une conversation
    // ne finissent pas la même nuit.
    verrou: e.verrou || null,
    portes: (e.portes || []).map((p) => ({ nom: p.nom, etat: p.etat,
                                           pv: p.pv, par: p.par })),
    // Ce que fait la troupe au dernier instant. Agrégé, jamais nominatif.
    etats: e.etats,
    faits: e.faits,
    par_quoi: par,
  };
  if (types) releve.types = types;
  return { secondes: (Date.now() - t0) / 1000, releve };
}

// ---------------------------------------------------------------------------
// LA COMPARAISON — à plat, pour que le désaccord se nomme
//
// On aplatit les deux relevés en chemins (`par_quoi.blesse`, `portes.0.etat`)
// et l'on compare l'UNION des chemins : sans l'union, un compte qui tombe à
// zéro — c'est-à-dire un MÉCANISME qui a disparu, le plus gros de ce qu'on
// cherche — passerait inaperçu parce que sa clef n'existerait plus.
// ---------------------------------------------------------------------------
function aplatir(o, prefixe, dans) {
  dans = dans || new Map();
  if (o === null || typeof o !== "object") { dans.set(prefixe, o); return dans; }
  for (const [k, v] of Object.entries(o)) aplatir(v, prefixe ? prefixe + "." + k : k, dans);
  return dans;
}

function desaccords(a, b) {
  const A = aplatir(a, ""), B = aplatir(b, "");
  const clefs = [...new Set([...A.keys(), ...B.keys()])].sort();
  const l = [];
  for (const k of clefs) {
    const x = A.has(k) ? A.get(k) : "—", y = B.has(k) ? B.get(k) : "—";
    if (x !== y) l.push({ quoi: k, a: x, b: y });
  }
  return l;
}

// ---------------------------------------------------------------------------
// LA SORTIE — la forme des bancs de la maison
// ---------------------------------------------------------------------------
let echecs = 0, n = 0;
function dit(nom, cond, quoi) {
  n++; if (!cond) echecs++;
  console.log((cond ? "  ok    " : "  KO    ") + nom + (quoi ? "   — " + quoi : ""));
}

function lister(l, gauche, droite) {
  for (const d of l.slice(0, 24))
    console.log("          " + d.quoi + " : " + gauche + " " + d.a +
                "  ≠  " + droite + " " + d.b);
  if (l.length > 24) console.log("          … et " + (l.length - 24) + " autres");
}

// ---------------------------------------------------------------------------
async function main() {
  const o = args();
  planter(o.serveur);
  const B = chargerBataille();

  const chaine = CHAINE.map((f) => ({ f, sha: empreinte(f) }));
  const ensemble = crypto.createHash("sha256")
    .update(chaine.map((c) => c.f + ":" + c.sha).join("|")).digest("hex").slice(0, 12);
  const src2d = fs.readFileSync(path.join(MODULES, "bataille2d.js"), "utf8");
  const drapeau = (src2d.match(/const PORTE_OUVERTE_ESSAI = (\w+);/) || [])[1] || "?";

  console.log("\nBANC DU MOTEUR — " + o.hommes + " hommes à « " + o.porte +
              " », " + o.duree + " s");
  console.log("  chaîne  : " + CHAINE.length + " fichiers, empreinte d'ensemble " +
              ensemble + "   (lue au manifeste bataille/moteur/chaine.js)");
  const graine = (globalThis.window.BatailleHasard || {}).GRAINE;
  console.log("  graine  : " + graine + " · PORTE_OUVERTE_ESSAI=" + drapeau +
              " · ni peuple ni tournée : la ville n'entre pas dans la condition\n");

  // ── LE HASARD EST-IL SEMÉ AVANT D'ÊTRE TIRÉ ? ─────────────────────────────
  // Le repli `H ? H.R() : Math.random()` de `corps-adapt.js` est MUET : le
  // jour où une couche est chargée avant `hasard.js`, la cuisson cesse d'être
  // reproductible et rien ne le dit. C'est arrivé une fois. Deux lignes.
  dit("le hasard est posé et il se ressème",
      !!(globalThis.window.BatailleHasard &&
         typeof globalThis.window.BatailleHasard.semer === "function"));
  // HASARD OUVRE LA CHAÎNE — mais « premier de la liste » n'est plus le bon
  // test depuis que `bataille/moteur/` la précède. Ces morceaux-là ne tirent
  // rien : un journal, des validateurs et un objet d'état n'ont pas d'urne.
  // L'exigence n'a jamais porté sur le rang, elle porte sur le fait que RIEN
  // QUI TIRE ne soit posé avant l'urne — on le vérifie donc pour ce qu'il est.
  const avantHasard = CHAINE.slice(0, Math.max(0, CHAINE.indexOf("bataille/hasard.js")))
    .filter((f) => f.indexOf("bataille/moteur/") !== 0);
  dit("hasard.js ouvre la chaîne", avantHasard.length === 0,
      avantHasard.length === 0 ? "" :
      "il vient après « " + avantHasard.join(", ") + " » : tout ce qui tire avant lui tire hors graine");

  const t0 = Date.now();
  await B.preparer(o.source);
  console.log("  données chargées en " + ((Date.now() - t0) / 1000).toFixed(1) + " s");

  const un = cuire(B, o);
  console.log("  1re cuisson : " + un.secondes.toFixed(1) + " s");
  let deux = null;
  if (!o.uneFois) {
    deux = cuire(B, o);
    console.log("  2e cuisson  : " + deux.secondes.toFixed(1) + " s");
  }
  console.log("");

  if (o.relever) {
    console.log(JSON.stringify(un.releve, null, 1));
    return;
  }

  // ── 1 ─ LE MOTEUR SE REPRODUIT-IL DANS LA MÊME SESSION ? ──────────────────
  // On le vérifie AVANT de comparer quoi que ce soit : un étalon posé sur un
  // moteur qui ne se reproduit pas est un chiffre qu'on croira, et qui ne
  // voudra rien dire. `rejouer()` ressème la graine et remet la place à zéro —
  // c'est cela qu'on éprouve, autant que le déroulé.
  console.log("── deux cuissons, une seule session ──");
  if (deux) {
    const d = desaccords(un.releve, deux.releve);
    dit("la même condition rend la même bataille", d.length === 0,
        d.length ? d.length + " relevé(s) en désaccord — LE MOTEUR N'EST PAS REPRODUCTIBLE" : "");
    if (d.length) lister(d, "1re", "2e");
  } else console.log("  (sautée : --une-fois)");

  // ── 2 ─ CONTRE L'ÉTALON ───────────────────────────────────────────────────
  const condition = {
    hommes: o.hommes, duree_s: o.duree, porte: o.porte, pas_s: PAS,
    graine, porte_ouverte_essai: drapeau,
    peuple: 0, tournee: 0, planches: 0,
    chaine, chaine_sha: ensemble,
  };

  if (o.poser) {
    fs.writeFileSync(ETALON, JSON.stringify({
      _lisez_moi:
        "L'ÉTALON DU MOTEUR. Ce que rend `ecrans/modules/bataille2d.js` et sa " +
        "chaîne sur une bataille courte, à graine tenue. Il ne dit pas que la " +
        "bataille est bonne : il dit qu'elle est la MÊME. On le repose d'un " +
        "`--poser` quand on a CHOISI de changer le modèle, et l'on écrit alors " +
        "dans le commit ce qui a bougé et pourquoi. Un déplacement de blocs, " +
        "lui, ne doit rien bouger du tout — c'est toute la raison de ce fichier. " +
        "Engendré par ecrans/modules/bataille/banc-moteur.js, ne pas éditer à la main.",
      pose_le: new Date().toISOString().slice(0, 19).replace("T", " "),
      condition,
      releve: un.releve,
    }, null, 1), "utf8");
    console.log("\n  → étalon posé : " + path.relative(ICI, ETALON).replace(/\\/g, "/"));
    console.log("    " + un.releve.morts + " morts, " + un.releve.blesses +
                " blessés, " + un.releve.fuyards + " fuyards · " +
                un.releve.faits + " faits d'annales");
  } else if (!fs.existsSync(ETALON)) {
    dit("l'étalon existe", false, "aucun étalon posé — lancez-le une fois avec --poser");
  } else {
    const et = JSON.parse(fs.readFileSync(ETALON, "utf8"));
    const c = et.condition || {};
    console.log("\n── contre l'étalon du " + (et.pose_le || "?") + " ──");

    // LA CONDITION D'ABORD, ET C'EST UN REFUS DE LIRE, PAS UN VERDICT.
    // « On ne compare jamais deux cuissons sans dire d'abord combien d'hommes
    // et combien de secondes » — article 0 de la règle de lecture. Comparer
    // 150 hommes à 1700 rendrait un tableau de désaccords parfaitement vrai et
    // parfaitement muet.
    const memeCondition = c.hommes === o.hommes && c.duree_s === o.duree &&
                          c.porte === o.porte && c.graine === graine &&
                          c.porte_ouverte_essai === drapeau;
    if (!memeCondition) {
      dit("la condition est celle de l'étalon", false,
          "étalon : " + c.hommes + " hommes, " + c.duree_s + " s, graine " +
          c.graine + ", drapeau " + c.porte_ouverte_essai +
          " — le banc REFUSE de comparer deux nuits différentes");
    } else {
      // LA CHAÎNE A-T-ELLE BOUGÉ ? Ce n'est pas une faute, c'est le sujet : un
      // découpage change les empreintes par construction. On le DIT, parce que
      // ça change ce que le résultat signifie — même issue sous une chaîne
      // identique, c'est un banc qui tourne à vide ; même issue sous une chaîne
      // changée, c'est le déplacement de blocs qui est prouvé.
      const av = new Map((c.chaine || []).map((x) => [x.f, x.sha]));
      const bouge = chaine.filter((x) => av.get(x.f) !== x.sha)
                          .map((x) => x.f + (av.has(x.f) ? "" : " (neuf)"));
      const partis = (c.chaine || []).filter((x) => !chaine.some((y) => y.f === x.f))
                                     .map((x) => x.f + " (parti)");
      const tout = bouge.concat(partis);
      console.log("  chaîne  : " + (tout.length
        ? tout.length + " fichier(s) changé(s) depuis l'étalon — " + tout.join(", ")
        : "identique à l'étalon (le banc ne prouve donc rien de neuf aujourd'hui)"));

      const d = desaccords(et.releve, un.releve);
      dit("l'issue et les annales sont celles de l'étalon", d.length === 0,
          d.length ? d.length + " relevé(s) en désaccord" : "");
      if (d.length) lister(d, "étalon", "auj.");
    }
  }

  console.log("\n" + (echecs ? "  ✗ " + echecs + " échec(s) sur " + n
                             : "  ✓ " + n + " épreuve(s), toutes tenues") + "\n");
  process.exit(echecs ? 1 : 0);
}

module.exports = { planter, chargerBataille, CHAINE, DEFAUTS, PAS };
if (require.main === module)
  main().catch((e) => { console.error("banc-moteur : " + (e && e.stack || e)); process.exit(1); });
