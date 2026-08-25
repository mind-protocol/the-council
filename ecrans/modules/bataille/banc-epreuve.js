// Exécuter une épreuve de la page sans peinture.
//   node ecrans/modules/bataille/banc-epreuve.js bataille-rangee-naive
"use strict";
const { planter, chargerBataille } = require("./banc-moteur.js");

const argv = process.argv.slice(2);
const id = argv.find((x) => !x.startsWith("--")) || "bataille-rangee-naive";
const valeur = (nom, defaut) => {
  const i = argv.indexOf("--" + nom); return i >= 0 ? argv[i + 1] : defaut;
};
const serveur = valeur("serveur", "http://localhost:3129");
const duree = +valeur("duree", 0);
const echelle = +valeur("echelle", 0);
const chefDebug = valeur("chef", "");
const hommeDebug = valeur("homme", "");

async function main() {
  planter(serveur);
  const B = chargerBataille();
  const Scenarios = require("./scenarios.js");
  await B.preparer("/monde");
  const source = Scenarios.parId(id);
  if (!source) throw new Error("épreuve inconnue : " + id);
  const scenario = (duree > 0 || echelle > 0) ? Object.assign({}, source,
    duree > 0 ? { duree } : {}, echelle > 0 ? { echelle } : {}) : source;
  const t0 = Date.now();
  const resultat = await Scenarios.jouer(B, scenario, { mesure:5 });
  console.log("\n" + scenario.n + " — " + scenario.nom +
    " · " + scenario.duree + " s simulées en " + ((Date.now()-t0)/1000).toFixed(1) + " s\n");
  let rouges = 0;
  for (const v of resultat.verdicts) {
    const ok = v.tenu === true; if (!ok) rouges++;
    console.log((ok ? "ok  " : v.tenu === false ? "NON " : "?   ") + v.dit +
      (v.observe != null ? " — " + v.observe : ""));
  }
  if (chefDebug) {
    const nommes=B.nommes().filter((x)=>(x.nom||"").toLowerCase().includes(chefDebug.toLowerCase()));
    const ids=new Set(nommes.map((x)=>x.nom));
    const echelons=B.echelons().filter((x)=>ids.has(x.nom));
    const corps=new Set(echelons.map((x)=>x.corps).filter(Boolean));
    const unites=B.unites().filter((u)=>u.placeRalliement&&corps.has(u.placeRalliement.corps));
    const trajectoire=resultat.suite.map((r)=>({t:+r.temps.toFixed(1),
      chefs:(r.echelons||[]).filter((x)=>ids.has(x.nom)).map((x)=>({
        id:x.id,reste:+Math.hypot(x.x-x.cibleX,x.y-x.cibleY).toFixed(1),
        x:+x.x.toFixed(1),y:+x.y.toFixed(1)})),
      unites:(r.unites||[]).filter((u)=>u.placeRalliement&&corps.has(u.placeRalliement.corps))
        .map((u)=>({id:u.id,reste:+Math.hypot(u.x-u.placeRalliement.x,
          u.y-u.placeRalliement.y).toFixed(1),calculs:u.calculsAStar}))}));
    const internes=B.troupe().filter((h)=>h.nom&&ids.has(h.nom)).map((h)=>({
      id:h.debugId,route:h.routeCommandement||null,calculs:h.calculsCommandement||0}));
    console.log("\nDEBUG CHEF " + chefDebug + "\n" + JSON.stringify({nommes,echelons,
      cibles:echelons.map((x)=>({id:x.id,libre:B.libre(x.cibleX,x.cibleY),
        reste:+Math.hypot(x.x-x.cibleX,x.y-x.cibleY).toFixed(1)})),
      trajectoire,internes,unites:unites.map((u)=>({id:u.id,x:+u.x.toFixed(1),y:+u.y.toFixed(1),
        cible:[+u.placeRalliement.x.toFixed(1),+u.placeRalliement.y.toFixed(1)],
        cibleLibre:B.libre(u.placeRalliement.x,u.placeRalliement.y),
        phase:u.phaseRalliement,cohesion:+u.cohesion.toFixed(2),
        distanceP90:+u.distanceP90.toFixed(1),calculs:u.calculsAStar}))},null,2));
  }
  if (hommeDebug) {
    const diagnostic = B.diagnostic(hommeDebug);
    console.log("\nDEBUG HOMME " + hommeDebug + "\n" +
      JSON.stringify(diagnostic, null, 2));
  }
  console.log("\n" + (rouges ? rouges + " sonde(s) rouge(s)" : "toutes les sondes sont vertes"));
  process.exit(rouges ? 1 : 0);
}

main().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
