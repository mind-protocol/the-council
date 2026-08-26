// corps_mesure.js — que dit la couche 1 sur une bataille entière ?
//
//     node scripts/monde/corps_mesure.js [--hommes 400] [--duree 120]
//
// LE TEST DE LA BOUCLE FERMÉE, et c'est le seul qui compte à ce stade. Le
// grégarisme est une rétroaction positive : la peur d'un homme monte celle de
// son voisin, qui monte la sienne. Rien dans le modèle n'empêche la divergence,
// et jusqu'ici la couche n'avait jamais tourné qu'avec des voisins fabriqués à
// la main — deux ou trois, jamais six cents qui se lisent mutuellement.
//
// On dresse donc une vraie bataille, on la fait tourner, et l'on relève à
// intervalles ce que la couche 1 dit de chaque homme. Elle ne conduit rien
// (`corps-adapt.js` est en observation) : si elle s'emballe, on le voit sur le
// relevé sans avoir cassé la bataille.
//
// CE QU'ON CHERCHE, PRÉCISÉMENT :
//   le réflexe MOYEN monte-t-il et redescend-il, ou monte-t-il et reste-t-il ?
//   la répartition des gestes est-elle plausible, ou tout le monde fait-il la
//     même chose (signe d'une contagion qui a tout emporté) ?
//   reste-t-il des hommes calmes ? un modèle où personne n'est calme est un
//     modèle emballé, quelle que soit la beauté de ses courbes.
"use strict";
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

const ICI = path.dirname(path.dirname(__dirname));
const MODULES = path.join(ICI, "ecrans", "modules");
const a = process.argv.slice(2);
const opt = (n, d) => { const i = a.indexOf("--" + n); return i >= 0 ? +a[i + 1] : d; };
const HOMMES = opt("hommes", 400), DUREE = opt("duree", 120);
const BASE = "http://localhost:3129";

globalThis.window = globalThis;
globalThis.window.CHEMIN_JOURNEE =
  pathToFileURL(path.join(MODULES, "monde", "journee.js")).href;
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.document = { addEventListener() {} };
const vrai = globalThis.fetch;
globalThis.fetch = (u, o) => vrai(/^https?:/.test(u) ? u : BASE + u, o);

// La chaîne se lit au manifeste, comme le four et le banc la lisent. Cet outil
// mesurait jusqu'ici une chaîne à lui — sans `roster.js`, comme `jeu.html` —,
// c'est-à-dire un moteur légèrement différent de celui qu'on fait tourner.
const CHAINE = require(path.join(MODULES, "bataille", "moteur", "chaine.js"))
  .fichiers("moteur");
for (const f of CHAINE) (0, eval)(fs.readFileSync(path.join(MODULES, f), "utf8"));
const B = globalThis.window.Bataille2d;

const n2 = (x) => (x >= 0 ? "+" : "") + x.toFixed(2);

(async () => {
  await B.preparer("/monde");
  B.rejouer("La porte de la Gadoue", HOMMES);
  const PAS = 1 / 20;
  const releves = [];

  for (let t = 0; t < DUREE; t += PAS) {
    B.pas(PAS);
    if (Math.abs(t % 10) < PAS / 2) releves.push(relever(t));
  }

  function relever(t) {
    // ⚠ LA MOYENNE SUR TOUTE LA BATAILLE EST LA MAUVAISE STATISTIQUE, et elle
    // a failli faire conclure a tort. Sur six cents hommes, une poignee
    // seulement touche du fer dans les deux premieres minutes : douze alarmes
    // se noient dans l'arrondi et le releve affiche « 100 % de calmes »,
    // exactement comme si la couche ne repondait a rien.
    //
    // On mesure donc CEUX QUI SONT DANS L'AFFAIRE — au contact ou tout pres —
    // et l'on garde le maximum, qui est le seul chiffre qui dise si quelque
    // chose s'est passe quelque part.
    const hs = B.troupe();
    let n = 0, somme = 0, calmes = 0, emprise = 0, hauts = 0, pire = 1;
    let nEngages = 0, sommeEng = 0, recus = 0;
    const gestes = {}, bras = {};
    for (const h of hs) {
      const l = h.l1; if (!l) continue;
      n++; somme += l.sangFroid; emprise += l.emprise;
      if (l.sangFroid < pire) pire = l.sangFroid;
      if (l.sangFroid > 0.8) calmes++;
      if (l.sangFroid < 0.5) hauts++;
      if (h.recu) recus += h.recu.length;
      // « engage » : il a quelqu'un d'en face a portee de bras.
      const eng = h.enMesure || l.sangFroid < 0.9;
      if (eng) { nEngages++; sommeEng += l.sangFroid;
        gestes[l.jambes] = (gestes[l.jambes] || 0) + 1;
        bras[l.bras] = (bras[l.bras] || 0) + 1; }
    }
    return { t, n, moy: n ? somme / n : 1, emp: n ? emprise / n : 0,
             calmes: n ? calmes / n : 0, hauts: n ? hauts / n : 0,
             pire, nEng: nEngages, moyEng: nEngages ? sommeEng / nEngages : 1,
             recus, gestes, bras };
  }

  console.log("LA COUCHE 1 SUR UNE BATAILLE — " + HOMMES + " hommes, " +
              DUREE + " s, en observation\n");
  console.log("    t   engagés  réflexe(eux)  le pire  alarmés   les jambes DE CEUX-LA");
  for (const r of releves) {
    const top = Object.entries(r.gestes).sort((x, y) => y[1] - x[1])
      .slice(0, 3).map(([g, c]) => g + " " + Math.round(100 * c / Math.max(1, r.nEng)) + "%").join("  ");
    console.log("  " + String(Math.round(r.t)).padStart(3) + "s " +
      String(r.nEng).padStart(7) + "   " + n2(r.moyEng).padStart(9) + "   " +
      n2(r.pire).padStart(6) + "   " +
      String(r.hauts).padStart(5) + "   " + top);
  }

  const der = releves[releves.length - 1] || { bras: {} };
  console.log("\n  les bras, à la fin : " +
    Object.entries(der.bras).sort((x, y) => y[1] - x[1])
      .map(([g, c]) => g + " " + c).join("  "));

  // LE VERDICT — et il se lit sur trois choses, pas sur une courbe.
  const moys = releves.map((r) => r.moy);
  const monte = moys[moys.length - 1] - moys[0];
  const calmesFin = releves[releves.length - 1].calmes;
  console.log("\n  ── ce que ça dit ──");
  console.log("  dérive du réflexe moyen  : " + n2(monte) +
    (monte > 0.8 ? "   ⚠ ça monte et ça ne redescend pas" : "   ok"));
  console.log("  hommes encore calmes     : " + Math.round(calmesFin * 100) + " %" +
    (calmesFin < 0.05 ? "   ⚠ plus personne n'est calme : emballement" : "   ok"));
  const varie = Object.keys(der.gestes || {}).length;
  console.log("  gestes différents en jeu : " + varie +
    (varie < 2 ? "   ⚠ tout le monde fait la même chose" : "   ok"));
})().catch((e) => { console.error("mesure : " + e.message); process.exit(1); });
