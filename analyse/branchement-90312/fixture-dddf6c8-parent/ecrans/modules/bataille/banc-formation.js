// -*- coding: utf-8 -*-
/**
 * Le déplacement d'une unité, indépendamment du scénario de la porte.
 *
 *   node ecrans/modules/bataille/banc-formation.js
 *
 * Une vintaine de la défense quitte l'anneau du Donjon pour rejoindre un
 * autre poste. Le but n'est pas tactique : il prouve que le navigateur prend
 * une origine, une destination et une unité quelconques, et qu'il ne calcule
 * jamais un chemin par homme.
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

  const avant = B.unites();
  const source = avant.find((u) => u.camp === "garde" &&
    u.parent && u.parent !== "poste:donjon");
  const cibleN = avant.findIndex((u) => u.id === "garde:donjon:0");
  const chefCible = B.troupe().find((h) => h.formation === cibleN && h.chefFormation);
  if (!source || !chefCible) throw new Error("unités de défense introuvables");

  const sourceN = avant.findIndex((u) => u.id === source.id);
  const chefSource = B.troupe().find((h) => h.formation === sourceN && h.chefFormation);
  const membresSource = B.troupe().filter((h) => h.formation === sourceN);
  const depart = [chefSource.x, chefSource.y];
  const destinationSource = {
    id: "essai:autre-poste", nom: "un autre poste",
    x: chefCible.x, y: chefCible.y,
  };
  B.ordonnerFormation(source.id, destinationSource,
    { texte: "Au poste voisin. Gardez votre vintaine avec vous." });
  // Vingt secondes : assez pour quitter le poste, avant que l'assaut parti à
  // plus de cent mètres n'impose au guet la priorité du combat.
  B.pas(20);

  const apres = B.unites();
  const mue = apres.find((u) => u.id === source.id);
  const autres = apres.filter((u) => u.id !== source.id);
  const distance = Math.hypot(chefSource.x - depart[0], chefSource.y - depart[1]);

  console.log("\nBANC DE FORMATION — défense mobile, destination arbitraire\n");
  exiger(mue.destination === "un autre poste", "l'ordre appartient à l'unité de défense");
  exiger(mue.ordreLitteral === "Au poste voisin. Gardez votre vintaine avec vous.",
          "la bulle cite les mots réellement donnés à l'unité");
  exiger(mue.calculsAStar === 1, "un seul A* pour toute l'unité");
  exiger(distance > 10, "le chef a réellement quitté son poste");
  exiger(mue.cohesion >= 0.70, "au moins 70 % des hommes restent à douze mètres du chef");
  exiger(autres.every((u) => u.destination !== "un autre poste"),
          "aucune autre unité n'a absorbé cet ordre");
  exiger(membresSource.every((h) => h.formation === sourceN),
          "l'appartenance à la vintaine reste stable");
  B.ordonnerFormation(source.id, destinationSource,
    { texte: "Même poste. Ne vous séparez pas." });
  B.pas(.1);
  const redit = B.unites().find((u) => u.id === source.id);
  exiger(redit.ordreLitteral === "Même poste. Ne vous séparez pas." &&
          redit.calculsAStar === 1,
          "redire le même trajet change les mots sans repayer un A*");

  console.log("\nchef déplacé de " + distance.toFixed(1) + " m · cohésion " +
              (mue.cohesion * 100).toFixed(0) + " % · " + mue.calculsAStar + " A*\n");

  // À une échelle où une aile contient plusieurs vintaines, le même ordre ne
  // doit toujours produire qu'une route à l'échelon parent.
  B.echelle(0.25);
  B.rejouer();
  B.pas(1);
  const marche = B.unites().filter((u) => u.camp === "assaut" && u.destination);
  const groupes = new Set(marche.map((u) => u.parent + ":" + u.destination));
  const aStars = marche.reduce((n, u) => n + u.calculsAStar, 0);
  if (aStars > groupes.size) console.log(marche.map((u) => ({
    unite:u.id, parent:u.parent, destination:u.destination,
    calculs:u.calculsAStar,
  })));
  exiger(aStars <= groupes.size,
          "les vintaines sœurs héritent de la route de leur aile");
  exiger(aStars < marche.length,
          "la chaîne calcule moins de routes qu'elle ne déplace de vintaines");
  console.log("\n" + marche.length + " vintaines en marche · " + groupes.size +
              " ordres d'aile · " + aStars + " A*\n");

  // Deux unités amies se croisent sans devenir une seule foule.
  B.rejouer();
  const avantCroisement = B.unites();
  const paire = avantCroisement.filter((u) => u.camp === "garde" &&
    u.parent === "poste:La porte de la Gadoue").slice(0, 2);
  if (paire.length < 2) throw new Error("deux vintaines du même poste introuvables");
  const na = avantCroisement.findIndex((u) => u.id === paire[0].id);
  const nb = avantCroisement.findIndex((u) => u.id === paire[1].id);
  const ca = B.troupe().find((h) => h.formation === na && h.chefFormation);
  const cb = B.troupe().find((h) => h.formation === nb && h.chefFormation);
  const ma = B.troupe().filter((h) => h.formation === na);
  const mb = B.troupe().filter((h) => h.formation === nb);
  B.ordonnerFormation(paire[0].id, { id: "croisement:b", nom: "la place de B",
                                     x: cb.x, y: cb.y });
  B.ordonnerFormation(paire[1].id, { id: "croisement:a", nom: "la place de A",
                                     x: ca.x, y: ca.y });
  B.pas(12);
  const apresCroisement = B.unites();
  const ua = apresCroisement.find((u) => u.id === paire[0].id);
  const ub = apresCroisement.find((u) => u.id === paire[1].id);
  exiger(ma.every((h) => h.formation === na) && mb.every((h) => h.formation === nb),
          "deux unités qui se croisent n'échangent aucun homme");
  exiger(ua.cohesion >= .70 && ub.cohesion >= .70,
          "les deux unités ressortent encore cohérentes du croisement");

  // Un ordre neuf doit produire une route neuve, mais toujours une seule.
  const ancienneDestination = ua.destination;
  B.ordonnerFormation(ua.id, { id: "contre-ordre", nom: "le contre-ordre",
                               x: ca.x + 35, y: ca.y + 10 });
  B.pas(8);
  const deviee = B.unites().find((u) => u.id === ua.id);
  if (!(deviee.destination !== ancienneDestination && deviee.calculsAStar === 2))
    console.log({ ancienneDestination, contreOrdre:deviee.destination,
      calculs:deviee.calculsAStar });
  exiger(deviee.destination !== ancienneDestination && deviee.calculsAStar === 2,
          "un contre-ordre remplace la route sans la multiplier par homme");

  // Enfin le cas qui casse une vraie chaîne : le chef tombe pendant l'ordre.
  B.echelle(0.05);
  B.rejouer();
  const avantPerte = B.unites();
  const perdue = avantPerte.find((u) => u.camp === "garde" &&
    u.parent !== "poste:donjon" && u.debout >= 3);
  const np = avantPerte.findIndex((u) => u.id === perdue.id);
  const ancienChef = B.troupe().find((h) => h.formation === np && h.chefFormation);
  const but = B.troupe().find((h) => h.chefFormation && h.formation !== np &&
    B.unites()[h.formation].camp === "garde");
  ancienChef.etat = "blesse";
  B.ordonnerFormation(perdue.id, { id: "apres-chute", nom: "le poste voisin",
                                   x: but.x, y: but.y });
  B.pas(12);
  const reprise = B.unites().find((u) => u.id === perdue.id);
  exiger(!!reprise.chef && reprise.chef !== ancienChef.nom,
          "la vintaine se donne un nouveau chef après un délai");
  exiger(reprise.calculsAStar === 1,
          "le nouveau chef reprend l'ordre sans A* individuel");

  // Les coureurs visent le centre ACTUEL de l'escouade. À l'arrivée, ils
  // quittent réellement leur ancienne unité et rejoignent celle à laquelle ils
  // viennent de remettre l'ordre ; aucun homme ordinaire ne change avec eux.
  B.rejouer();
  B.pas(45);
  const unitesApresCourriers = B.unites();
  const arrives = B.faits().filter((f) => f.quoi === "coureur-arrive").length;
  const chaineJuste = B.troupe().filter((h) => h.camp === "assaut" &&
    !h.tete && !h.hors && h.formation >= 0).every((h) => {
      const u = unitesApresCourriers[h.formation];
      return u && u.id === "assaut:" + h.escouade;
    });
  exiger(arrives > 0, "des coureurs retrouvent une escouade qui a bougé");
  exiger(chaineJuste,
          "un coureur arrivé rejoint sa nouvelle unité sans mélanger les autres");
}

main().catch((e) => {
  console.error("banc-formation : " + (e && e.stack || e));
  process.exit(1);
});
