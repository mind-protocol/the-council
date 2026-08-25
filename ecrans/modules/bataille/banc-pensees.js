// -*- coding: utf-8 -*-
/**
 * La trace humaine de la bataille.
 *
 *   node ecrans/modules/bataille/banc-pensees.js
 *
 * Ce banc ne juge pas si une décision est bonne. Il exige qu'elle soit
 * contestable : chaque homme vivant doit dire ce qu'il essaie de faire,
 * pourquoi, et quel système lui a donné cette conduite. Si une nouvelle
 * branche de `soldat()` oublie `penser()`, ce banc casse immédiatement.
 */
"use strict";

const { planter, chargerBataille, DEFAUTS } = require("./banc-moteur.js");

const exiger = (vrai, dit) => {
  console.log((vrai ? "ok  " : "NON ") + dit);
  if (!vrai) process.exitCode = 1;
};

async function main() {
  planter(DEFAUTS.serveur);
  const B = chargerBataille();
  await B.preparer(DEFAUTS.source);
  B.echelle(0.05);
  B.rejouer();
  B.pas(45);

  const vivants = B.troupe().filter((h) => h.etat !== "mort");
  const sansTrace = vivants.filter((h) => !h.pensee ||
    !h.pensee.action || !h.pensee.raison || !h.pensee.systeme);
  const brancheLibre = vivants.filter((h) => !h.branche ||
    !h.branche.startsWith("j'essaie de ") || !h.branche.includes(" parce que "));
  const historiquesTropLongs = vivants.filter((h) => (h.pensees || []).length > 4);
  const systemes = new Map();
  for (const h of vivants) {
    const k = h.pensee && h.pensee.systeme || "sans trace";
    systemes.set(k, (systemes.get(k) || 0) + 1);
  }

  console.log("\nBANC DES PENSÉES — toute décision doit pouvoir être contestée\n");
  exiger(sansTrace.length === 0,
          "chaque homme vivant expose action, raison et système");
  exiger(brancheLibre.length === 0,
          "aucune ancienne branche libre ne contourne la trace structurée");
  exiger(historiquesTropLongs.length === 0,
          "l'historique reste borné à quatre changements");
  exiger(systemes.size >= 4,
          "la trace distingue plusieurs systèmes réellement actifs");

  const echantillon = vivants.find((h) => h.pensee && h.l1 && h.l2);
  const lu = echantillon && B.sous(echantillon.x, echantillon.y, 1.5);
  exiger(!!(lu && lu.pensee && lu.pensee.phrase && lu.pensee.systeme),
          "le survol rend la pensée structurée, pas seulement l'état");
  exiger(!!(lu && lu.corpsDit && lu.reflexion && lu.reflexion.idee),
          "le survol rend aussi les avis concurrents des couches 1 et 2");

  const ids = new Set(vivants.map((h) => h.debugId));
  exiger(ids.size === vivants.length && !ids.has(undefined),
          "chaque homme possède une identité de debug unique");
  exiger(vivants.every((h) => h.perceptions && h.perceptions.length > 0),
          "chaque homme conserve sa chronologie perceptive depuis le départ");
  const dossier = echantillon && B.diagnostic(echantillon.debugId);
  exiger(!!(dossier && dossier.historique_perceptions.length &&
            dossier.voisinage.rayons.length === 4),
          "une marque calcule chronologie et voisinage à quatre rayons");
  exiger(!!(dossier && dossier.combattant.couches.corps &&
            dossier.combattant.couches.reflexion && dossier.bataille),
          "le dossier fige les couches et l'état global de la bataille");

  // Une longue épreuve ne doit plus rendre le bouton Mark inutilisable. On
  // gonfle volontairement la trace bien au-delà de son budget, puis on exige
  // que le rapport sacrifie le début — jamais les secondes qui précèdent le
  // clic du joueur.
  const traceReelle = echantillon.perceptions;
  const oublieesReelles = echantillon.perceptionsOubliees;
  echantillon.perceptions = Array.from({ length: 2400 }, (_, i) => ({
    temps:i, action:"perception-" + i, detail:"é".repeat(320),
  }));
  echantillon.perceptionsOubliees = 37;
  const lourd = B.diagnostic(echantillon.debugId);
  const hm = lourd.historique_perceptions_meta;
  exiger(Buffer.byteLength(JSON.stringify(lourd.historique_perceptions), "utf8") <=
          512 * 1024 + 1024,
          "une marque borne la chronologie à environ 512 Kio");
  exiger(lourd.historique_perceptions.at(-1).temps === 2399 &&
          lourd.historique_perceptions[0].temps > 0,
          "la réduction conserve la fin et retire le début");
  exiger(hm.politique === "fin-conservee" && hm.total === 2437 &&
          hm.omis === hm.total - hm.conserve,
          "le rapport chiffre explicitement les perceptions anciennes omises");
  echantillon.perceptions = traceReelle;
  echantillon.perceptionsOubliees = oublieesReelles;

  console.log("\n" + vivants.length + " hommes vivants · " + systemes.size +
              " systèmes visibles");
  for (const [nom, n] of [...systemes].sort((a, b) => b[1] - a[1]))
    console.log("  " + String(n).padStart(4) + "  " + nom);
  if (lu && lu.pensee)
    console.log("\nexemple : « " + lu.pensee.phrase + " » — " +
                lu.pensee.systeme + "\n");
}

main().catch((e) => {
  console.error("banc-pensees : " + (e && e.stack || e));
  process.exit(1);
});
