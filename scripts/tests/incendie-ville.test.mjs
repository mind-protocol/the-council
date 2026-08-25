import fs from "node:fs";
import assert from "node:assert/strict";

globalThis.window = globalThis;
globalThis.ResizeObserver = class { observe() {} };
const gradient = { addColorStop() {} };
const contexte = new Proxy({ createRadialGradient:() => gradient }, {
  get(cible, cle) { return cle in cible ? cible[cle] : (() => {}); },
  set(cible, cle, valeur) { cible[cle] = valeur; return true; },
});
const canvas = {
  width:0, height:0,
  getContext:() => contexte,
  getBoundingClientRect:() => ({ width:1200, height:800 }),
};
const stats = { innerHTML:"" }, note = { innerHTML:"" };
const plan = JSON.parse(fs.readFileSync(new URL("../../monde/portreal.plan2d.json", import.meta.url), "utf8"));

await import("../../ecrans/modules/bataille/incendie-ville.js");
IncendieVille.installer({ canvas, stats, note, plan });
IncendieVille.vue(IncendieVille.cadre());

const image = () => IncendieVille.batiments().map((b) => [b.id, b.etat, +b.dose.toFixed(8)]);
assert.equal(IncendieVille.etat().sources, 12, "douze départs sont imposés");
assert.ok(IncendieVille.batiments().length > 45_000, "le cadastre entier est chargé");
assert.ok(!IncendieVille.batiments().some((b) => b.source && b.mat === IncendieVille.CLASSES.alchimie),
  "la Guilde des Alchimistes ne fait pas partie des départs arbitraires");

IncendieVille.pas(900);
const une = image(), bilan = { ...IncendieVille.etat() };
assert.ok(bilan.allumes > bilan.sources, "le feu se propage au-delà des départs");
assert.ok(bilan.panachesVisibles <= 180,
  "la vue de ville plafonne la fumée à 180 panaches agrégés");
assert.ok(!IncendieVille.batiments().some((b) => b.mat.susceptibilite === 0 && b.etat !== "intact"),
  "les volumes inertes ne prennent jamais feu");

IncendieVille.remettre(); IncendieVille.pas(900);
assert.deepEqual(image(), une, "la graine rend la cuisson reproductible");

IncendieVille.remettre({ departs:false });
assert.equal(IncendieVille.etat().allumes, 0, "D3 commence sans feu artificiel");
const toit = IncendieVille.batiments().find((b) => b.mat.susceptibilite >= 1 && b.aire > 10);
const demi = Math.max(2, (toit.x1 - toit.x0) / 2 + 2);
const directs = IncendieVille.deposerSouffle({ dt:10, noyau:2200, dragon:"Vhagar",
  temperature:() => 2200,
  tranches:[{ s:40, R:demi, v:0, cx:toit.x, cy:toit.y, demi, bx:1, by:0,
    gauche:{ x:toit.x - demi, y:toit.y }, droite:{ x:toit.x + demi, y:toit.y } }],
});
assert.ok(directs > 0, "une corde chaude qui coupe un toit peut l'allumer");
assert.equal(IncendieVille.resume().dragonAllumes, directs,
  "les prises directes restent séparées de la propagation secondaire");
assert.ok(IncendieVille.ciblesDragon().length > 100,
  "la sélection du dragon lit des secteurs urbains agrégés");
console.log(`incendie-ville: ${bilan.sources} départs, ${bilan.allumes} allumés à 15 min, ` +
  `${IncendieVille.batiments().length} contours`);
