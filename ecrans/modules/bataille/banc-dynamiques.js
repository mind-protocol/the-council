// -*- coding: utf-8 -*-
/**
 * Les questions de conduite et les mesures historiques de `scenarios.js`,
 * contre la vraie chaîne.
 *
 *   node ecrans/modules/bataille/banc-dynamiques.js
 *   node ecrans/modules/bataille/banc-dynamiques.js contact rythme presse
 *
 * Contrairement a `banc-moteur`, ce banc juge le modele. Il ne pose aucun
 * etalon et n'ecrit rien : chaque NON reste une information a expliquer.
 */
"use strict";
const { planter, chargerBataille, DEFAUTS } = require("./banc-moteur.js");
const S = require("./scenarios.js");

const demandes = process.argv.slice(2).filter((x) => !x.startsWith("--"));
const liste = demandes.length ? demandes.map((id) => {
  const s = S.parId(id);
  if (!s) throw new Error("épreuve inconnue : " + id);
  return s;
}) : S.LISTE;

async function main() {
  planter(DEFAUTS.serveur);
  const B = chargerBataille();
  await B.preparer(DEFAUTS.source);
  let faux = 0, sans = 0;

  console.log("\nBANC DES DYNAMIQUES — mesures toutes les 5 s\n");
  for (const s of liste) {
    const t0 = Date.now();
    const r = await S.jouer(B, s, { mesure: 5 });
    console.log(String(s.n).padStart(2) + ". " + s.nom +
      "  [" + ((Date.now() - t0) / 1000).toFixed(1) + " s de calcul]");
    for (const v of r.verdicts) {
      const marque = v.tenu === true ? "ok  " : v.tenu === false ? "NON " : "—   ";
      if (v.tenu === false) faux++;
      if (v.tenu == null) sans++;
      console.log("    " + marque + v.dit +
        (v.observe != null ? " — observé : " + v.observe : "") +
        (v.attendu ? " · attendu : " + v.attendu : ""));
    }
    const f = r.fin;
    const pic = (champ) => r.suite.reduce((m, x) =>
      !m || x[champ] > m[champ] ? x : m, null);
    const picContact = pic("partContact"), picFrappent = pic("partFrappent");
    console.log("       allonge " + (100 * f.partContact).toFixed(1) + " % · frappeurs " +
      (100 * f.partFrappent).toFixed(1) + " % · " + f.coupsTentes + " coups · " +
      f.morts + " morts · " + f.fuyards + " fuyards · bouffée médiane " +
      f.boutMedian.toFixed(1) + " s");
    console.log("       pics : allonge " + (100 * picContact.partContact).toFixed(1) +
      " % à " + picContact.temps.toFixed(0) + " s · frappeurs " +
      (100 * picFrappent.partFrappent).toFixed(1) + " % à " +
      picFrappent.temps.toFixed(0) + " s\n");
  }
  console.log((faux ? "✗ " + faux + " NON" : "✓ aucun NON") +
              (sans ? " · " + sans + " sans objet" : "") + "\n");
  process.exit(faux ? 1 : 0);
}

main().catch((e) => { console.error("banc-dynamiques : " + (e && e.stack || e)); process.exit(1); });
