// -*- coding: utf-8 -*-
/**
 * banc-monde.js — LES SONDES DU MONDE PHYSIQUE, avant d'y toucher.
 *
 *     node ecrans/modules/bataille/banc-monde.js
 *     node ecrans/modules/bataille/banc-monde.js --hommes 300 --duree 200
 *     node ecrans/modules/bataille/banc-monde.js --epreuve rassemblement-armee
 *
 * POURQUOI CE FICHIER EXISTE. Le lot 2 du refactor va sortir la topologie, la
 * navigation, le mouvement, les collisions et le combat de `bataille2d.js`, et
 * il promet ensuite « aucun téléport, aucune traversée de mur, aucun bouchon
 * artificiel au seuil ». Ces trois promesses ne se vérifient pas : RIEN NE LES
 * MESURE. `banc-moteur.js` compte des morts et des faits d'annales ; il ne sait
 * pas dire qu'un homme a franchi douze mètres en un vingtième de seconde.
 *
 * IL EST EXTÉRIEUR AU MOTEUR, ET C'EST LA CONDITION. Il n'instrumente rien :
 * il fait tourner la bataille et REGARDE la troupe entre deux pas, comme un
 * observateur posé au-dessus du champ. Une sonde qui vivrait dans le moteur
 * devrait y être ajoutée — donc modifier ce qu'on cherche justement à laisser
 * intact pendant une extraction. Celle-ci ne peut pas fausser l'étalon, parce
 * qu'elle n'écrit pas une ligne dans la chaîne.
 *
 * CE QU'IL MESURE, ET POURQUOI CHACUN.
 *
 *   téléports        un pas plus long que ce qu'un corps peut parcourir. C'est
 *                    le signe d'une position écrite en dehors du mouvement, et
 *                    c'est le premier interdit du refactor.
 *   dans le bâti     un homme vivant sur une case que le masque dit pleine. Le
 *                    dessin et la navigation doivent lire la MÊME géométrie ;
 *                    tant qu'ils ne le font pas, ce compte est non nul.
 *   A* par homme     zéro attendu. Une route se calcule par groupe conducteur
 *                    et par destination, jamais par combattant.
 *   densité          la vraie physique de la foule : au-dessus de 4 ou 5 par
 *                    mètre carré, le mouvement volontaire disparaît. On ne code
 *                    pas « il panique parce qu'il est serré », on lui retire
 *                    ses issues — encore faut-il savoir quand elles manquent.
 *   P90 au chef      la dispersion réelle d'une unité, celle que la moyenne
 *                    cache.
 *   arrêtés près     des hommes immobiles à 5–10 m d'un ennemi : la signature
 *                    d'un contact qui ne se ferme pas.
 *   sans pair        des hommes sans un seul camarade de LEUR unité à douze
 *                    mètres. Un homme seul suit n'importe qui.
 *
 * IL NE JUGE PAS, IL RELÈVE. Aucun seuil de réussite ici : ce banc sert à
 * savoir où l'on en est, et ce qu'on lit un jour donné devient la référence
 * qu'on écrit dans `analyse/refactor-moteur/`. Le jour où le lot 2 promet zéro
 * téléport, c'est ce compte-là qui le dira.
 */
"use strict";
const fs = require("fs");
const path = require("path");
// `planter`, emprunte au four, s'en sert pour poser CHEMIN_JOURNEE sur la
// fausse fenetre : il doit le trouver dans NOTRE portee, comme dans la sienne.
const { pathToFileURL } = require("url");

const ICI = path.dirname(path.dirname(path.dirname(__dirname)));
const MODULES = path.join(ICI, "ecrans", "modules");
const SAC = path.join(ICI, "scripts", "monde", "sac.js");

const DEFAUTS = { hommes: 150, duree: 100, porte: "La porte de la Gadoue",
                  serveur: "http://localhost:3129", source: "/monde", epreuve: "" };
const PAS = 1 / 20;

// LA VITESSE QU'AUCUN CORPS NE DÉPASSE. La fuite est à 3,6 m/s et un cheval au
// galop bien au-dessus ; on prend huit mètres par seconde, ce qui laisse tout
// le monde tranquille et ne signale que l'impossible. Un homme à cette allure
// n'a pas couru : il a été POSÉ ailleurs.
const PLAFOND_MS = 8;

function args() {
  const a = process.argv.slice(2), o = Object.assign({}, DEFAUTS);
  for (let i = 0; i < a.length; i++) {
    const c = a[i].replace(/^--/, "");
    if (c in DEFAUTS) o[c] = a[++i];
  }
  o.hommes = +o.hommes; o.duree = +o.duree;
  return o;
}

// --- l'emprunt au four, comme `banc-moteur.js` -----------------------------
const sacSrc = fs.readFileSync(SAC, "utf8");
function morceau(quoi, re) {
  const m = sacSrc.match(re);
  if (!m) throw new Error("sac.js a changé de forme : « " + quoi + " » ne s'y " +
    "retrouve plus. Le banc emprunte la mécanique du four ; il ne devine pas.");
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

// ---------------------------------------------------------------------------
// LES SONDES
// ---------------------------------------------------------------------------

const vivant = (h) => h.etat !== "mort" && h.etat !== "blesse";

/** La densité vue par CHAQUE homme : combien de corps dans son mètre autour. */
function densites(hommes) {
  const R = 1, AIRE = Math.PI * R * R;
  const gens = hommes.filter(vivant);
  // une grille d'un mètre, pour ne pas faire n² sur mille hommes
  const cases = new Map();
  const clef = (x, y) => Math.floor(x) + ":" + Math.floor(y);
  for (const h of gens) {
    const k = clef(h.x, h.y);
    if (!cases.has(k)) cases.set(k, []);
    cases.get(k).push(h);
  }
  const out = [];
  for (const h of gens) {
    let n = 0;
    const i0 = Math.floor(h.x), j0 = Math.floor(h.y);
    for (let i = i0 - 1; i <= i0 + 1; i++)
      for (let j = j0 - 1; j <= j0 + 1; j++) {
        const c = cases.get(i + ":" + j);
        if (!c) continue;
        for (const o of c)
          if (o !== h && Math.hypot(o.x - h.x, o.y - h.y) <= R) n++;
      }
    out.push((n + 1) / AIRE);
  }
  return out;
}

/** Un camarade de SA propre unité, à douze mètres. */
function sansPair(hommes) {
  const gens = hommes.filter(vivant);
  let seuls = 0;
  for (const h of gens) {
    const sien = h.escouade;
    if (sien == null) { seuls++; continue; }
    const a = gens.some((o) => o !== h && o.escouade === sien &&
      Math.hypot(o.x - h.x, o.y - h.y) <= 12);
    if (!a) seuls++;
  }
  return { seuls, sur: gens.length };
}

/** Immobile, et un ennemi entre cinq et dix mètres. */
function arretesPres(hommes, bouge) {
  const gens = hommes.filter(vivant);
  let n = 0;
  for (const h of gens) {
    if ((bouge.get(h) || 0) > 0.05) continue;         // il avance : ce n'est pas lui
    const e = gens.some((o) => o.camp !== h.camp &&
      Math.hypot(o.x - h.x, o.y - h.y) >= 5 &&
      Math.hypot(o.x - h.x, o.y - h.y) <= 10);
    if (e) n++;
  }
  return { n, sur: gens.length };
}

function centile(t, p) {
  if (!t.length) return 0;
  const s = t.slice().sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor((s.length - 1) * p))];
}

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
    console.log("BANC DU MONDE — épreuve « " + o.epreuve + " », " + o.duree + " s");
  } else {
    B.rejouer(o.porte, o.hommes);
    console.log("BANC DU MONDE — " + o.hommes + " hommes à « " + o.porte + " », " +
                o.duree + " s");
  }

  const n = Math.round(o.duree / PAS);
  const teleports = [];            // { t, id, m, ms }
  let dansBati = 0, echantillonsBati = 0;
  const densiteMax = [];
  let tempsSerre = { "2-4": 0, "4-5": 0, "5+": 0 };
  const p90 = [];
  let arretes = 0, echantillonsArretes = 0;
  let seuls = 0, echantillonsSeuls = 0;

  let avant = new Map();
  for (const h of B.troupe()) avant.set(h, { x: h.x, y: h.y });

  for (let i = 0; i < n; i++) {
    B.pas(PAS);
    const hommes = B.troupe();
    const bouge = new Map();

    // --- téléports : un pas plus long qu'un corps ne le permet -----------
    for (const h of hommes) {
      const a = avant.get(h);
      if (a) {
        const d = Math.hypot(h.x - a.x, h.y - a.y);
        bouge.set(h, d);
        if (d / PAS > PLAFOND_MS && vivant(h))
          teleports.push({ t: +(i * PAS).toFixed(2), id: h.debugId,
                           m: +d.toFixed(1), ms: +(d / PAS).toFixed(1) });
      }
      if (!a) bouge.set(h, 0);
      avant.set(h, { x: h.x, y: h.y });
    }

    // Le reste ne se mesure pas à chaque battement : vingt fois par seconde
    // de bataille, ce sont des heures de calcul pour un relevé qui ne bouge
    // pas d'un battement à l'autre. Une fois par seconde suffit et se lit.
    if (i % 20) continue;

    for (const h of hommes) {
      if (!vivant(h)) continue;
      echantillonsBati++;
      if (B.libre(h.x, h.y) === false) dansBati++;
    }

    const d = densites(hommes);
    if (d.length) {
      densiteMax.push(Math.max.apply(null, d));
      const pic = Math.max.apply(null, d);
      if (pic >= 5) tempsSerre["5+"]++;
      else if (pic >= 4) tempsSerre["4-5"]++;
      else if (pic >= 2) tempsSerre["2-4"]++;
    }

    for (const u of B.unites()) if (u.debout > 1) p90.push(u.distanceP90);

    const ap = arretesPres(hommes, bouge);
    arretes += ap.n; echantillonsArretes += ap.sur;
    const sp = sansPair(hommes);
    seuls += sp.seuls; echantillonsSeuls += sp.sur;
  }

  const us = B.unites();
  const astar = us.reduce((s, u) => s + (u.calculsAStar || 0), 0);
  const gens = B.troupe().filter(vivant).length;
  const e = B.etat();

  const pc = (a, b) => b ? (100 * a / b).toFixed(1) + " %" : "—";
  const dit = (nom, valeur, note) =>
    console.log("  " + nom.padEnd(30) + String(valeur).padStart(10) +
                (note ? "   " + note : ""));

  console.log("\n── le monde physique ──");
  dit("téléports", teleports.length,
      teleports.length ? "le pire : " + Math.max.apply(null, teleports.map((x) => x.ms)) +
      " m/s à " + teleports[0].t + " s" : "aucun pas au-dessus de " + PLAFOND_MS + " m/s");
  dit("hommes dans le bâti", pc(dansBati, echantillonsBati),
      dansBati + " relevé(s) sur " + echantillonsBati);
  dit("A* calculés", astar,
      us.length + " unités · " + (gens ? (astar / gens).toFixed(3) : "—") + " par homme");
  dit("densité maximale", densiteMax.length ?
      Math.max.apply(null, densiteMax).toFixed(1) + " /m²" : "—",
      "secondes au-dessus de 2 : " + tempsSerre["2-4"] +
      " · de 4 : " + tempsSerre["4-5"] + " · de 5 : " + tempsSerre["5+"]);

  console.log("\n── les unités ──");
  dit("distance au chef, médiane", centile(p90, .5).toFixed(1) + " m");
  dit("distance au chef, P90", centile(p90, .9).toFixed(1) + " m");
  dit("sans pair de son unité", pc(seuls, echantillonsSeuls));
  dit("arrêtés à 5–10 m d'un ennemi", pc(arretes, echantillonsArretes));

  console.log("\n── l'issue, pour situer ──");
  dit("morts / blessés / fuyards", e.morts + " / " + e.blesses + " / " + e.fuyards);
  dit("assaut / garde", e.assaut + " / " + e.garde);
  const v = e.verrou;
  dit("verrou engagé", v ? v.etat + " · " + Math.round(v.pv) + " pv" : "—");
}

main().catch((e) => { console.error(e); process.exit(1); });
