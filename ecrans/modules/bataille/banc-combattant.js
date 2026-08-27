// -*- coding: utf-8 -*-
/**
 * banc-combattant.js — CE QU'UN HOMME PORTE, ET QUI LE CONDUIT VRAIMENT.
 *
 *     node ecrans/modules/bataille/banc-combattant.js
 *     node ecrans/modules/bataille/banc-combattant.js --hommes 300 --duree 150
 *     node ecrans/modules/bataille/banc-combattant.js --epreuve rassemblement-armee
 *
 * POURQUOI CE FICHIER EXISTE. Le lot 3 du refactor promet de « brancher la
 * pensée courante sur la vraie trace d'arbitrage ». La formule est courte et
 * l'écart qu'elle vise est large : aujourd'hui `h.pensee` est écrite par
 * CINQUANTE-SIX endroits différents, dont chacun nomme son propre « système ».
 * Dix seulement nomment une couche de la survival stack ; les quarante-six
 * autres nomment la BRANCHE qui a bougé l'homme — « front de porte », « ordre
 * de formation », « messager du Guet ».
 *
 * Autrement dit : « j'essaie de X parce que Y » est raconté par le chemin de
 * code, pas par l'arbitre. Et l'arbitre, lui, existe : `QuiConduit` élit à
 * chaque battement laquelle des quatre tient les jambes, et le résultat est
 * posé dans `h.conduit`. Deux vérités sur le même homme au même instant, dont
 * une seule est lue par l'écran.
 *
 * CE BANC LES MET CÔTE À CÔTE, et c'est tout ce qu'il fait. Il ne juge pas : il
 * compte les hommes dont la pensée affichée contredit l'élection. Le jour où le
 * lot 3 est fait, ce compte tombe à zéro parce que la pensée SORT de l'élection
 * au lieu de la doubler.
 *
 * IL MESURE AUSSI CE QUE CHAQUE HOMME PORTE, parce que le lot 3 le demande dans
 * la même liste : son ordre reçu, son unité, son chef connu, sa mémoire
 * récente. Un homme qui n'a pas de chef connu ne peut pas « rester avec ses
 * pairs » : il suivra n'importe qui de la bonne couleur.
 *
 * EXTÉRIEUR AU MOTEUR, comme `banc-monde.js` : il regarde la troupe entre deux
 * pas et n'instrumente pas une ligne. Il ne peut donc pas fausser un étalon.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

const ICI = path.dirname(path.dirname(path.dirname(__dirname)));
const MODULES = path.join(ICI, "ecrans", "modules");
const SAC = path.join(ICI, "scripts", "monde", "sac.js");

const DEFAUTS = { hommes: 150, duree: 100, porte: "La porte de la Gadoue",
                  serveur: "http://localhost:3129", source: "/monde", epreuve: "" };
const PAS = 1 / 20;

function args() {
  const a = process.argv.slice(2), o = Object.assign({}, DEFAUTS);
  for (let i = 0; i < a.length; i++) {
    const c = a[i].replace(/^--/, "");
    if (c in DEFAUTS) o[c] = a[++i];
  }
  o.hommes = +o.hommes; o.duree = +o.duree;
  return o;
}

const sacSrc = fs.readFileSync(SAC, "utf8");
function morceau(quoi, re) {
  const m = sacSrc.match(re);
  if (!m) throw new Error("sac.js a changé de forme : « " + quoi + " » ne s'y retrouve plus.");
  return m[0];
}
const CHAINE = require(path.join(MODULES, "bataille", "moteur", "chaine.js"))
  .fichiers(process.argv.includes("--epreuve") ? "scene" : "moteur");
/* eslint-disable no-eval */
const planter = eval("(" + morceau("function planter",
  /function planter\(base\) \{[\s\S]*?\n\}/) + ")");
const chargerBataille = eval("(" + morceau("function chargerBataille",
  /function chargerBataille\(\) \{[\s\S]*?\n\}/) + ")");
/* eslint-enable no-eval */

const vivant = (h) => h.etat !== "mort" && h.etat !== "blesse";

// ---------------------------------------------------------------------------
// REPLIER UN « SYSTÈME » DE PENSÉE SUR LES QUATRE MAINS DE L'ARBITRE
//
// `QuiConduit` n'a que quatre réponses : `corps`, `reflexion`, `envie`, `ordre`.
// Les cinquante-six étiquettes de `penser()` se rangent dessus — et tout ce qui
// n'est pas explicitement une couche tombe dans `ordre`, parce que c'est ce que
// « la branche de l'ordre a bougé cet homme » veut dire.
// ---------------------------------------------------------------------------
function replier(systeme) {
  if (!systeme) return null;
  const s = String(systeme).toLowerCase();
  if (s.indexOf("corps") === 0) return "corps";
  if (s.indexOf("réflexion") === 0 || s.indexOf("reflexion") === 0) return "reflexion";
  if (s.indexOf("envie") === 0) return "envie";
  return "ordre";
}

/** Un camarade de SA propre unité à douze mètres. */
function aUnPair(h, gens) {
  if (h.escouade == null) return false;
  return gens.some((o) => o !== h && o.escouade === h.escouade &&
    Math.hypot(o.x - h.x, o.y - h.y) <= 12);
}

const ATTAQUE = { assaut: 1, melee: 1 };

async function main() {
  const o = args();
  planter(o.serveur);
  const B = chargerBataille();
  await B.preparer(o.source);

  if (o.epreuve) {
    const Sc = globalThis.window.BatailleScenarios;
    const s = Sc && Sc.parId(o.epreuve);
    if (!s) throw new Error("épreuve inconnue : " + o.epreuve);
    Sc.poser(B, s);
    console.log("BANC DU COMBATTANT — épreuve « " + o.epreuve + " », " + o.duree + " s");
  } else {
    B.rejouer(o.porte, o.hommes);
    console.log("BANC DU COMBATTANT — " + o.hommes + " hommes à « " + o.porte + " », " +
                o.duree + " s");
  }

  const n = Math.round(o.duree / PAS);
  const conduit = {}, pensee = {}, etiquettes = {};
  let echantillons = 0, desaccord = 0, sansPensee = 0, sansConduit = 0;
  const porte = { ordre: 0, unite: 0, chefConnu: 0, memoire: 0,
                  commandement: 0, perceptions: 0 };
  // LES QUATRE COUCHES SONT-ELLES LA QUAND L'ARBITRE LES LIT ?
  // `l1` et `l2` ont chacune un adaptateur qui tourne AVANT l'election ; `l3` et
  // `l4` sont calculees EN LIGNE dans `soldat()`, aux 680e et 870e lignes d'une
  // cascade de 855 — donc apres, et seulement pour les hommes dont le battement
  // va jusque-la. Ce compte dit combien d'hommes ont une couche remplie.
  //
  // ⚠ UN COMPTE BAS N'EST PAS UN DEFAUT EN SOI, et il faut le lire avec ca en
  // tete : une envie absente est notee par `QuiConduit` comme une envie de ZERO
  // — aucune pretention, pas un `NaN` —, et c'est la semantique voulue, « la
  // convoitise n'existe pas sans objet ». Ce qui est un defaut, c'est que la
  // couche depende du CHEMIN : 239 hommes sur 239 ont une escouade, donc la
  // condition d'entree de `l3` n'est jamais fermee, et pourtant 135 seulement
  // ont une `l3`. Les 104 autres sont sortis de la cascade avant.
  const couche = { l1: 0, l2: 0, l3: 0, l4: 0 };
  let soloAttaque = 0, attaquants = 0;

  for (let i = 0; i < n; i++) {
    B.pas(PAS);
    if (i % 20) continue;                       // une fois par seconde suffit
    const gens = B.troupe().filter(vivant);
    for (const h of gens) {
      echantillons++;
      const c = h.conduit || null;
      const p = replier(h.pensee && h.pensee.systeme);
      if (c) conduit[c] = (conduit[c] || 0) + 1; else sansConduit++;
      if (p) pensee[p] = (pensee[p] || 0) + 1; else sansPensee++;
      if (h.pensee && h.pensee.systeme)
        etiquettes[h.pensee.systeme] = (etiquettes[h.pensee.systeme] || 0) + 1;
      if (c && p && c !== p) desaccord++;

      if (h.ordreRecu || h.ordre) porte.ordre++;
      if (h.escouade != null || h.formation != null) porte.unite++;
      if (h.chefConnuId != null || h.chefConnu != null) porte.chefConnu++;
      if (h.pensees && h.pensees.length) porte.memoire++;
      if (h.commandement) porte.commandement++;
      if (h.perceptions && h.perceptions.length) porte.perceptions++;
      if (h.l1 != null) couche.l1++;
      if (h.l2 != null) couche.l2++;
      if (h.l3 != null) couche.l3++;
      if (h.l4 != null) couche.l4++;

      if (ATTAQUE[h.etat]) {
        attaquants++;
        if (!aUnPair(h, gens)) soloAttaque++;
      }
    }
  }

  const pc = (a, b) => b ? (100 * a / b).toFixed(1) + " %" : "—";
  const dit = (nom, v, note) =>
    console.log("  " + nom.padEnd(34) + String(v).padStart(9) + (note ? "   " + note : ""));
  const table = (titre, o2) => {
    console.log("\n── " + titre + " ──");
    const t = Object.entries(o2).sort((a, b) => b[1] - a[1]);
    for (const [k, v] of t) dit(k, pc(v, echantillons), v + " relevé(s)");
    if (!t.length) console.log("  (rien)");
  };

  table("qui tient les jambes — l'élection de QuiConduit", conduit);
  table("ce que la pensée affichée dit — replié sur les mêmes quatre", pensee);

  console.log("\n── l'écart ──");
  dit("pensée ≠ élection", pc(desaccord, echantillons),
      desaccord + " sur " + echantillons);
  dit("sans élection", pc(sansConduit, echantillons));
  dit("sans pensée", pc(sansPensee, echantillons));

  console.log("\n── ce que chaque homme porte ──");
  dit("un ordre reçu", pc(porte.ordre, echantillons));
  dit("une unité", pc(porte.unite, echantillons));
  dit("un chef connu", pc(porte.chefConnu, echantillons));
  dit("une mémoire récente", pc(porte.memoire, echantillons));
  dit("une mémoire de commandement", pc(porte.commandement, echantillons));
  dit("des perceptions", pc(porte.perceptions, echantillons));

  console.log("");
  console.log("-- les quatre couches, au moment ou l'arbitre les lit --");
  dit("couche 1 — corps (adaptateur)", pc(couche.l1, echantillons));
  dit("couche 2 — reflexion (adaptateur)", pc(couche.l2, echantillons));
  dit("couche 3 — interpretation (en ligne)", pc(couche.l3, echantillons));
  dit("couche 4 — envie (en ligne)", pc(couche.l4, echantillons));
  console.log("\n── l'assaut solo ──");
  dit("hommes en attaque", attaquants);
  dit("dont sans pair de leur unité", pc(soloAttaque, attaquants),
      soloAttaque + " sur " + attaquants);

  console.log("\n── les étiquettes de pensée réellement vues ──");
  const et = Object.entries(etiquettes).sort((a, b) => b[1] - a[1]).slice(0, 14);
  for (const [k, v] of et)
    console.log("  " + (k.length > 40 ? k.slice(0, 38) + "…" : k).padEnd(42) +
                String(pc(v, echantillons)).padStart(8));
  console.log("  (" + Object.keys(etiquettes).length + " étiquettes distinctes)");
}

main().catch((e) => { console.error(e); process.exit(1); });
