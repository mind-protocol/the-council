/**
 * BANC — ce que pese une sauvegarde, et ce que la decimation fait gagner.
 *
 * Le navigateur ne sert a rien pour cette mesure : il bride la boucle d'images
 * des que l'onglet passe derriere, et il faut des centaines de secondes de sim
 * pour que la carte du regard ait quelque chose a decimer. Ici, mille secondes
 * de sim coutent quelques secondes de machine.
 *
 * Usage : node coding/banc-sauvegarde.mjs [dureeS]
 */

import { composer } from './composer.mjs';
import { sauver } from '../src/partie.js';
import { BATAILLE_RANGEE } from '../src/scenarios/index.js';

const DUREE_S = Number(process.argv[2] ?? 600);
const MS_PAR_FRAME = 100;

const octets = (o) => JSON.stringify(o).length;
const ko = (n) => (n / 1024).toFixed(1).padStart(8) + ' Ko';

const sim = composer(BATAILLE_RANGEE);
const nCorps = [...sim.monde.corps()].length;

console.log(`\nBANC — ${BATAILLE_RANGEE.titre}`);
console.log(`${nCorps} corps, ${DUREE_S} s de sim\n`);

const jalons = [0, 30, 60, 120, 300, 600, 1000].filter((t) => t <= DUREE_S);
let ecoule = 0;
console.log('  temps sim │      pleine │     decimee │  gain │  cases (rang / commandants)');
console.log('  ──────────┼─────────────┼─────────────┼───────┼───────────────────────────');
for (const jalon of jalons) {
  while (ecoule < jalon) { sim.orchestration.avancer(MS_PAR_FRAME); ecoule += MS_PAR_FRAME / 1000; }
  const pleine = sauver(sim, { couvertureDepuis: Infinity });
  const decimee = sauver(sim);
  const cases = (s, commande) => s.cognition
    .filter(([, h]) => (h.brain?.role === 'commandant') === commande)
    .reduce((a, [, h]) => a + (h.representation.couverture?.cases?.length ?? 0), 0);
  const p = octets(pleine), d = octets(decimee);
  console.log(`  ${String(jalon).padStart(8)}s │ ${ko(p)} │ ${ko(d)} │ ${String(Math.round(100 - (d / p) * 100)).padStart(4)}% │  ${cases(decimee, false)} gardees sur ${cases(pleine, false)}   /   ${cases(pleine, true)}`);
}

const fin = sauver(sim);
console.log(`\n  par corps : ${Math.round(octets(fin) / nCorps)} octets`);
console.log(`  a 4 000 corps, la meme densite donnerait ~${(octets(fin) / nCorps * 4000 / 1024 / 1024).toFixed(1)} Mo\n`);

// ── Et le tour complet, la ou il compte : APRES que le monde a diverge.
import { charger } from '../src/partie.js';
const avant = JSON.parse(JSON.stringify(sauver(sim)));
const posDe = (s) => s.monde.registre.corps.map((c) => `${c.id}:${c.pos.x},${c.pos.y}`).join('|');
for (let f = 0; f < 300; f++) sim.orchestration.avancer(MS_PAR_FRAME);   // 30 s de plus
const pendant = sauver(sim);
charger(avant, { monde: sim.monde, corpsContainer: sim.corpsContainer, cognition: sim.cognition });
const apres = sauver(sim);

const bouge = posDe(avant) !== posDe(pendant);
const revenu = posDe(avant) === posDe(apres);
const tetes = JSON.stringify(avant.cognition) === JSON.stringify(apres.cognition);
console.log(`  le monde a diverge pendant 30 s : ${bouge ? 'oui' : 'NON — la mesure ne prouve rien'}`);
console.log(`  positions revenues a l'instantane : ${revenu ? 'oui' : 'NON'}`);
console.log(`  tetes revenues a l'instantane     : ${tetes ? 'oui' : 'NON'}\n`);
process.exit(bouge && revenu && tetes ? 0 : 1);
