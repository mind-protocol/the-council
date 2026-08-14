// banc-la-main.js — l'épreuve du Bassin pour `5-la-main.js`.
//
// Neuf cas, et chacun est un homme qu'on peut se figurer. On ne mesure pas des
// décimales : on demande QUI tient la main, et l'on vérifie que c'est celui
// qu'on nommerait en regardant la scène. Un banc qui ne se raconte pas ne
// prouve rien.
//
//   node ecrans/modules/survival-stack/banc-la-main.js
"use strict";
const Main = require("./5-la-main.js");

let echecs = 0, n = 0;
function cas(titre, couches, attendu, opts) {
  n++;
  const e = {}; const t0 = (opts && opts.t) || 0;
  let r = Main.pas(couches, e, t0);
  // Un second battement, pour que la période réfractaire ait un état à tenir.
  if (opts && opts.puis) r = Main.pas(opts.puis, e, t0 + (opts.dt || 1.0));
  const ok = r.jambes.main === attendu.jambes
          && (attendu.bras == null || r.bras.main === attendu.bras);
  if (!ok) echecs++;
  console.log((ok ? "  ok  " : "  ÉCHEC ") + titre);
  console.log("        jambes " + r.jambes.main + " (" + r.jambes.force.toFixed(2)
    + ", marge " + r.jambes.marge.toFixed(2) + ")  bras " + r.bras.main
    + "  corpsAgi " + r.corpsAgi + "  — « " + r.phrase + " »");
  if (!ok) console.log("        attendu jambes=" + attendu.jambes
    + (attendu.bras ? " bras=" + attendu.bras : ""));
}

console.log("\nTENUE_MIN = " + Main.TENUE_MIN.toFixed(2) + " s"
  + "   (la plus courte durée de geste du répertoire du corps)");
console.log("exigence(0) = " + Main.exigence(0).toFixed(2)
  + "   exigence(TENUE_MIN) = " + Main.exigence(Main.TENUE_MIN).toFixed(2)
  + "   exigence(1 s) = " + Main.exigence(1).toFixed(2) + "\n");

// ── 1 ─ L'ORDINAIRE, ET IL DOIT ÊTRE L'ORDINAIRE ────────────────────────────
// Un homme qui va bien, dans une troupe qui va bien. Son corps n'a rien à dire,
// sa tête non plus. Si ce cas-là ne rend pas « ordre », le fichier est à jeter.
cas("l'homme ordinaire, son ordre en main",
  { l1: { jambes: "planté", bras: "garde", emprise: 0.05 },
    l2: { tient: 0.1, attend: 0, issue: { force: 0.8 } },
    l3: { lettre: 0 } },
  { jambes: "ordre", bras: "ordre" });

// ── 2 ─ LE CONSCRIT QUI CRAQUE ──────────────────────────────────────────────
cas("le conscrit : le corps a le volant, il part",
  { l1: { jambes: "fuite", bras: "ballants", emprise: 0.78 },
    l2: { tient: -0.5, attend: 0, issue: { force: 0.6 } },
    l3: { lettre: 0 } },
  { jambes: "corps", bras: "corps" });

// ── 3 ─ LE VÉTÉRAN QUI RECULE DE SANG-FROID ─────────────────────────────────
// Le corps propose un recul, mais il ne tient presque rien du volant : c'est la
// tête qui commande ce repli, pas la peur. L'ordre garde la main.
cas("le vétéran : son corps propose, sa tête dispose",
  { l1: { jambes: "recul", bras: "garde", emprise: 0.12 },
    l2: { tient: -0.2, attend: 0, issue: { force: 0.7 } },
    l3: { lettre: 0.3 } },
  { jambes: "ordre" });

// ── 4 ─ L'ACCULÉ ─ le cas pour lequel la couche 2 a été écrite ──────────────
// Il veut partir de toute son âme (`tient` à −0,9) et il n'a nulle part où
// aller. `issue.force` = 0 annule la prétention : il ne prend pas ses jambes,
// donc il reste, donc il se bat. Sans cette multiplication il vibrerait contre
// un mur.
cas("l'acculé : il veut partir, il n'a pas d'issue, il tient",
  { l1: { jambes: "planté", bras: "frapper", emprise: 0.3 },
    l2: { tient: -0.9, attend: 0, issue: { force: 0 } },
    l3: { lettre: 0 } },
  { jambes: "ordre" });

// ── 5 ─ LE MÊME, AVEC UNE RUE DERRIÈRE LUI ──────────────────────────────────
cas("le même, une rue derrière lui : il sort de là",
  { l1: { jambes: "planté", bras: "frapper", emprise: 0.3 },
    l2: { tient: -0.9, attend: 0, issue: { force: 0.9 } },
    l3: { lettre: 0 } },
  { jambes: "reflexion" });

// ── 6 ─ LA PATIENCE EST UNE CONDUITE ────────────────────────────────────────
// En infériorité, intact et calme : `attend` à +0,69, relevé au Bassin sur la
// couche 2. C'est un homme qui attend le nombre. Il lui faut ses jambes pour ne
// PAS avancer, et l'ordre dit d'avancer.
cas("celui qui attend que le nombre tourne",
  { l1: { jambes: "planté", bras: "garde", emprise: 0.1 },
    l2: { tient: -0.33, attend: 0.69, issue: { force: 0.5 } },
    l3: { lettre: 0 } },
  { jambes: "reflexion" });

// ── 7 ─ CELUI QUI N'EN FAIT PLUS QU'À SA TÊTE ───────────────────────────────
// `lettre` à −0,6 : la barre tombe à 0,20. Une envie de pillage médiocre suffit
// alors à l'emporter — c'est exactement ce que « il n'en fait plus qu'à sa
// tête » doit produire, et rien d'autre dans la pile ne le produisait.
cas("l'ordre lâché : une envie médiocre suffit à l'emporter",
  { l1: { jambes: "planté", bras: "garde", emprise: 0.05 },
    l2: { tient: 0, attend: 0, issue: { force: 0.5 } },
    l3: { lettre: -0.6 }, envie: 0.35 },
  { jambes: "envie" });

// ── 8 ─ LE MÊME HOMME, SON ORDRE TENU ───────────────────────────────────────
cas("la même envie, l'ordre tenu : elle ne passe pas",
  { l1: { jambes: "planté", bras: "garde", emprise: 0.05 },
    l2: { tient: 0, attend: 0, issue: { force: 0.5 } },
    l3: { lettre: 0.4 }, envie: 0.35 },
  { jambes: "ordre" });

// ── 9 ─ LA PÉRIODE RÉFRACTAIRE ──────────────────────────────────────────────
// Battement 1 : le corps prend, franchement. Battement 2, un dixième plus tard :
// la réflexion propose un poil plus fort — sous `TENUE_MIN`, elle ne prend pas.
// C'est ce qui remplace un tirage entre deux prétentions voisines.
const proche = {
  l1: { jambes: "fuite", bras: "garde", emprise: 0.70 },
  l2: { tient: -0.80, attend: 0, issue: { force: 0.90 } },
  l3: { lettre: 0 } };
cas("la main ne se rend pas dans le dixième de seconde",
  { l1: { jambes: "fuite", bras: "garde", emprise: 0.85 },
    l2: { tient: -0.3, attend: 0, issue: { force: 0.5 } },
    l3: { lettre: 0 } },
  { jambes: "corps" }, { puis: proche, dt: 0.1 });

// ── 10 ─ ET ELLE SE REND QUAND LE GESTE A EU LE TEMPS ───────────────────────
cas("la même, une seconde plus tard : elle passe",
  { l1: { jambes: "fuite", bras: "garde", emprise: 0.85 },
    l2: { tient: -0.3, attend: 0, issue: { force: 0.5 } },
    l3: { lettre: 0 } },
  { jambes: "reflexion" }, { puis: proche, dt: 1.0 });

// ── 11 ─ SANS ORDRE DU TOUT ─────────────────────────────────────────────────
// Un homme dont l'ordre est mort et à qui personne ne vient : barre à zéro, il
// est livré à ses couches. C'est la définition d'un homme sans nouvelles, et il
// ne doit surtout pas continuer d'obéir à rien.
cas("l'homme sans nouvelles : la moindre prétention passe",
  { l1: { jambes: "serrer", bras: "garde", emprise: 0.15 },
    l2: { tient: 0, attend: 0, issue: { force: 0 } } },
  { jambes: "corps" });

console.log("\n" + (echecs ? "  ✗ " + echecs + " échec(s) sur " + n
                            : "  ✓ " + n + " cas, tous tenus") + "\n");
process.exit(echecs ? 1 : 0);
