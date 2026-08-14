// scenario-3-contre-2.js — le banc d'essai de la couche 1.
//
// DEUX HOMMES CONTRE TROIS, DÉJÀ AU CONTACT, DE NUIT. Personne ne réfléchit,
// personne n'a reçu d'ordre : c'est la couche 1 toute seule, et c'est le seul
// moyen de savoir si elle tient debout.
//
//   A1 est débordé — D1 le prend de face, D2 de biais.
//   A2 est à égalité — D3 seul devant lui.
//   Les deux camps sont intacts, à souffle plein, à 4h30 du matin.
//
// CE QU'ON EN ATTEND, et ce sont des ORDRES, jamais des valeurs :
//   A1 lâche avant A2 · le conscrit avant le vétéran · la sidération existe chez
//   les novices et jamais chez les vieux · quand A1 part, A2 lâche plus tôt que
//   s'il avait été seul depuis le début.
//
// Le relevé narratif est le vrai livrable : c'est lui qui dit ce qu'on n'avait
// pas pensé à asserter.
"use strict";
const C = require("./1-corps.js");

// Un hasard à graine, local et reproductible — même exigence que le four.
let _s = 20161219;
const R = () => (_s = (_s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
const semer = () => { _s = 20161219; };

const PAS = 1 / 20;          // le pas du monde, celui de bataille2d
const DEGAT_TYPIQUE = 22;
const VIE = 30;
const CADENCE = 0.9;

// --- fabriquer un homme -----------------------------------------------------
const homme = (nom, camp, ecole) => ({
  nom, camp, dressage: ecole.dressage, vecu: ecole.vecu,
  vie: VIE, souffle: 1, debout: true, parti: false,
  prochain: R() * CADENCE, cible: null, ennemis: [], amis: [],
  // l'état de la couche 1 s'installe tout seul au premier battement
});

const ECOLES = {
  conscrit: { dressage: -0.8, vecu: -0.9 },
  guet:     { dressage:  0.1, vecu: -0.2 },
  soldat:   { dressage:  0.6, vecu:  0.3 },
  veteran:  { dressage:  0.9, vecu:  0.9 },
};

// --- une passe d'armes ------------------------------------------------------
// On ne rejoue pas `bataille2d` : on lui emprunte seulement ce qu'il faut pour
// que des stimuli naissent — un coup part, il touche ou il frôle. Le reste de
// la mêlée (positions, déplacements) est figé, parce que ce n'est pas ce qu'on
// mesure ici.
function courir(ecole, { seul = false, journal = null, vie = VIE } = {}) {
  semer();
  const A = [homme("A1", "a", ECOLES[ecole]), homme("A2", "a", ECOLES[ecole])];
  const D = [homme("D1", "d", ECOLES.soldat), homme("D2", "d", ECOLES.soldat),
             homme("D3", "d", ECOLES.soldat)];
  for (const h of A) h.vie = vie;
  // Qui est en face de qui, et à quelle distance.
  const FACE = seul
    ? { A1: [["D1", 1.2, 1], ["D2", 1.6, 0.4]], A2: [] }   // A2 absent : le témoin
    : { A1: [["D1", 1.2, 1], ["D2", 1.6, 0.4]], A2: [["D3", 1.4, 1]] };

  const tousA = seul ? [A[0]] : A;
  const parLeNom = {}; for (const h of A.concat(D)) parLeNom[h.nom] = h;

  const stimuli = [];       // la boîte aux lettres commune, vidée chaque battement
  const sortie = [];
  let amisAvant = tousA.length;
  const rompuA = {}, tombeA = {};

  for (let t = 0; t < 60; t += PAS) {
    const boite = {};
    for (const h of tousA) boite[h.nom] = [];

    // --- les défenseurs frappent -------------------------------------------
    for (const d of D) {
      const vise = tousA.find((a) => (FACE[a.nom] || []).some(([n]) => n === d.nom));
      if (!vise || vise.parti || !vise.debout) continue;
      const [, dist, deFace] = FACE[vise.nom].find(([n]) => n === d.nom);
      d.prochain -= PAS;
      // Le fer qui part : on l'annonce tant qu'il n'est pas parti.
      if (d.prochain > 0 && d.prochain < 0.5)
        boite[vise.nom].push(Object.assign(C.ferQuiVient(d.prochain, deFace), { t }));
      if (d.prochain > 0) continue;
      d.prochain += CADENCE;
      const seuil = 0.45, tire = R();
      if (tire > seuil) {
        boite[vise.nom].push(Object.assign(C.coupFrole(tire, seuil, deFace), { t }));
      } else {
        const degat = 14 + R() * 16;
        vise.vie -= degat;
        boite[vise.nom].push(Object.assign(C.coupRecu(degat, DEGAT_TYPIQUE, deFace, 1), { t }));
        if (vise.vie <= 0) {
          vise.debout = false; if (tombeA[vise.nom] == null) tombeA[vise.nom] = t;
          // Un homme qui tombe est un stimulus pour son voisin.
          for (const a of tousA) if (a !== vise && a.debout)
            boite[a.nom].push(Object.assign(C.voisinTombe(1.5, 1, true), { t }));
        }
      }
    }

    // --- chacun fait tourner sa couche 1 -----------------------------------
    const partisCeTour = tousA.filter((a) => a.parti).length;
    for (const h of tousA) {
      if (!h.debout) continue;
      const faces = (FACE[h.nom] || []).map(([n, dist, deFace]) =>
        ({ distance: dist, deFace, frappe: true }));
      // Le départ d'un voisin, en dérivée — c'est la contagion.
      const partisAutres = tousA.filter((a) => a !== h && a.parti).length;
      if (partisAutres > (h.vusPartis || 0)) {
        boite[h.nom].push(Object.assign(
          C.voisinPart(partisAutres - (h.vusPartis || 0), amisAvant), { t }));
        h.vusPartis = partisAutres;
      }
      // LE GREGARISME v2 NE PREND PLUS UN COMPTE, IL PREND DES FORMES. `appui`
      // n'existe plus : la couche calcule elle-meme couverture, coude, contagion
      // et imitation a partir de `voisins`, et c'est le point de la v2 — ca doit
      // passer par les canaux, donc par elle. On lui donne donc la geometrie.
      //
      // L'angle est RELATIF au cap de l'homme : 0 devant, +-pi derriere. On le
      // deduit de `deFace` (cos de l'angle) pour les ennemis, et l'on pose le
      // camarade a l'epaule — c'est la seule position que ce banc ait jamais
      // supposee, elle etait simplement implicite dans `appui(amis, faces)`.
      const voisins = (FACE[h.nom] || []).map(([n, dist, deFace]) =>
        ({ angle: Math.acos(Math.max(-1, Math.min(1, deFace))), distance: dist,
           ami: false, cap: null }));
      for (const a of tousA)
        if (a !== h && a.debout && !a.parti)
          voisins.push({ angle: -Math.PI / 2, distance: 1.0, ami: true, cap: 0,
                         jambes: a.jambes || "planté", bras: a.bras || "garde",
                         depuis: a.jusqua == null ? 9 : Math.max(0, t - (a.jusqua - 1)) });
      const signaux = {
        integrite: C.integrite(h.vie, DEGAT_TYPIQUE),
        souffle:   C.souffle(h.souffle),
        menace:    C.menace(faces),
        issue:     C.issue(1),          // rue ouverte derrière : la fuite est possible
        aPortee:   faces.length > 0,
        ennemisProches: faces.length,
      };
      const r = C.pas(h, { t, dt: PAS, stimuli: boite[h.nom], signaux, voisins,
                           nuit: true, presse: 1 }, R());
      // Le souffle se vide au contact et se refait au repos — emprunté à
      // bataille2d pour que la fatigue existe, sans la remodéliser.
      const dur = r.jambes === "ruée" || r.bras === "frapper";
      h.souffle += ((dur ? 0.02 : 0.45) - h.souffle) * (dur ? 0.020 : 0.010) * PAS * 20;
      if (r.jambes === "fuite" && !h.parti) { h.parti = true; rompuA[h.nom] = t; }
      if (journal && Math.abs(t % 0.2) < PAS / 2)
        sortie.push({ t: +t.toFixed(1), qui: h.nom, ...r });
    }
    if (tousA.every((a) => a.parti || !a.debout)) break;
  }
  return { rompu: rompuA, tombe: tombeA, journal: sortie,
           debout: Object.fromEntries(tousA.map((a) => [a.nom, a.debout])) };
}

// ===========================================================================
// LE RELEVÉ
// ===========================================================================
const dit = (x) => (x == null ? "—" : x.toFixed(2));

console.log("═══ LE RELEVÉ NARRATIF — deux soldats contre trois, de nuit ═══\n");
{
  const r = courir("soldat", { journal: true });
  let dernier = {};
  for (const l of r.journal) {
    if (dernier[l.qui] === l.phrase) continue;
    dernier[l.qui] = l.phrase;
    console.log(("  " + String(l.t).padStart(4) + "s " + l.qui).padEnd(14) +
                l.phrase);
    if (l.saillant) console.log("".padEnd(14) + "        (" + l.saillant +
      ", saillance " + dit(l.saillance) + " · réflexe " + dit(l.reflexe) +
      " · emprise " + dit(l.emprise) + ")");
  }
}

console.log("\n═══ B1 · LE DRESSAGE ORDONNE-T-IL LA RUPTURE ? ═══\n");
const rompus = {};
for (const e of ["conscrit", "guet", "soldat", "veteran"]) {
  const r = courir(e);
  rompus[e] = r.rompu;
  const a1 = r.rompu.A1, a2 = r.rompu.A2;
  console.log("  " + e.padEnd(10) +
    "A1 (débordé) " + (a1 == null ? "n'a pas rompu" : "rompt à " + a1.toFixed(1) + "s").padEnd(20) +
    "A2 (à égalité) " + (a2 == null ? "n'a pas rompu" : "rompt à " + a2.toFixed(1) + "s"));
}

console.log("\n═══ C1 · A1 LÂCHE-T-IL AVANT A2 ? ═══\n");
for (const e of Object.keys(rompus)) {
  const { A1, A2 } = rompus[e];
  const ok = A1 != null && (A2 == null || A1 <= A2);
  console.log("  " + e.padEnd(10) + (ok ? "OUI" : "NON") +
              (A1 == null ? "  (A1 n'a pas rompu)" : ""));
}

console.log("\n═══ C2 · LA CONTAGION — A2 lâche-t-il plus tôt qu'un homme seul ? ═══\n");
for (const e of Object.keys(rompus)) {
  const ensemble = rompus[e].A2;
  const t = courir(e, { seul: true }).rompu.A1;
  console.log("  " + e.padEnd(10) +
    "à deux : " + (ensemble == null ? "jamais" : ensemble.toFixed(1) + "s").padEnd(10) +
    "seul : " + (t == null ? "jamais" : t.toFixed(1) + "s"));
}

console.log("\n═══ B3 · L'ASYMÉTRIE DE L'ALARME ═══\n");
{
  // ON MESURE LA MÊME CHOSE DES DEUX CÔTÉS, sinon on ne mesure rien : le temps
  // de couvrir 63 % de l'écart, qui est la définition de la constante de temps.
  // La première version comparait « le temps d'atteindre +0,4 » à « le temps de
  // redescendre à −0,4 » — deux écarts différents, donc un rapport qui ne disait
  // rien du modèle. Elle rendait ×7,9 là où le modèle vaut ×15 par construction.
  const tempsPour = (depart, cible) => {
    let a = depart, t = 0;
    const but = depart + (cible - depart) * 0.632;
    while (t < 600 && (cible > depart ? a < but : a > but)) { a = C.activer(a, cible, PAS); t += PAS; }
    return t;
  };
  const monte = tempsPour(-1, 1), descend = tempsPour(1, -1);
  console.log("  constante de montée   : " + monte.toFixed(1) + " s");
  console.log("  constante de descente : " + descend.toFixed(1) + " s");
  console.log("  rapport               : ×" + (descend / monte).toFixed(1) +
              (descend / monte >= 10 ? "   ✓ ≥ 10" : "   ✗ attendu ≥ 10"));
}

console.log("\n═══ A4 · INVARIANCE D'ÉCHELLE — le test qui aurait sauvé SEUIL_RECUL ═══\n");
{
  const a = C.integrite(30, 22), b = C.integrite(300, 220);
  console.log("  integrite(30 pv, coup 22) = " + dit(a));
  console.log("  integrite(300 pv, coup 220) = " + dit(b) +
              (Math.abs(a - b) < 1e-9 ? "   ✓ identiques" : "   ✗ elles diffèrent"));
}

console.log("\n═══ A3 · LE ZÉRO JUSTE — au repos, rien ne se déclenche ═══\n");
{
  const c = { dressage: 0, vecu: 0 };
  const calme = { integrite: 1, souffle: 1, appui: 1, menace: -1, issue: 1,
                  aPortee: false, ennemisProches: 0 };
  let r;
  for (let t = 0; t < 30; t += PAS)
    r = C.pas(c, { t, dt: PAS, stimuli: [], signaux: calme, nuit: true, presse: 0 }, R());
  console.log("  après 30 s sans rien : " + r.jambes + " · " + r.bras +
              "   réflexe " + dit(r.reflexe) + " · emprise " + dit(r.emprise) +
              (r.jambes === "planté" && r.emprise < 0.1 ? "   ✓" : "   ✗"));
}

console.log("\n═══ B6 · ACCULÉ — la fuite est-elle ANNULÉE, ou seulement réduite ? ═══\n");
{
  const s = { integrite: 0, souffle: 0, appui: -1, menace: 1, issue: -1, aPortee: true };
  const ouvert = Object.assign({}, s, { issue: 1 });
  const ap = C.appels(s, null), apo = C.appels(ouvert, null);
  console.log("  appel de fuite, issue ouverte : " + dit(apo["fuite"]));
  console.log("  appel de fuite, dos au mur    : " + dit(ap["fuite"]) +
              (ap["fuite"] <= -0.999 ? "   ✓ annulée" : "   ✗ seulement réduite"));
}

console.log("\n═══ LES ARÊTES INTERDITES — aucune ne doit apparaître ═══\n");
{
  let vues = [];
  for (const e of Object.keys(ECOLES)) {
    const r = courir(e, { journal: true });
    const suite = {};
    for (const l of r.journal) {
      const av = suite[l.qui];
      if (av && C.INTERDIT_JAMBES[av] && C.INTERDIT_JAMBES[av].has(l.jambes))
        vues.push(e + " : " + av + " → " + l.jambes);
      suite[l.qui] = l.jambes;
    }
  }
  console.log(vues.length ? "  ✗ " + vues.join("\n  ✗ ")
                          : "  ✓ aucune arête interdite dans les quatre écoles");
}

console.log("\n═══ CE QUE LA MESURE A VRAIMENT SORTI — la couche n'a pas le temps ═══\n");
{
  for (const e of ["conscrit", "soldat", "veteran"]) {
    const r = courir(e);
    console.log("  " + e.padEnd(10) +
      "A1 tombe à " + (r.tombe.A1 == null ? "—" : r.tombe.A1.toFixed(1) + "s").padEnd(8) +
      "A2 tombe à " + (r.tombe.A2 == null ? "—" : r.tombe.A2.toFixed(1) + "s"));
  }
  console.log("\n  La constante de montée de l'réflexe est de 3,0 s.");
  console.log("  Un homme au contact vit moins que ça. La couche 1 est calibrée");
  console.log("  pour un combat que le modèle de dégâts n'autorise pas.\n");
}

console.log("═══ AU BANC — les mêmes, avec quatre fois la vie, pour VOIR la couche ═══\n");
{
  const r = courir("conscrit", { journal: true, vie: 120 });
  let dernier = {};
  for (const l of r.journal) {
    if (dernier[l.qui] === l.phrase) continue;
    dernier[l.qui] = l.phrase;
    console.log(("  " + String(l.t).padStart(5) + "s " + l.qui).padEnd(15) + l.phrase);
    if (l.saillant) console.log("".padEnd(15) + "   (" + l.saillant +
      " · réflexe " + dit(l.reflexe) + " · emprise " + dit(l.emprise) + ")");
  }
  console.log("\n  rupture : " + JSON.stringify(r.rompu) +
              "   chute : " + JSON.stringify(r.tombe));
}
