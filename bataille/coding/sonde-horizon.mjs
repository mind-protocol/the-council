/**
 * SONDE — l'horizon de masse est-il ce qui coute ?
 *
 * `percevoirMasses` appelle `autourDe(id, porteeMax)` avec porteeMax = 400 m,
 * puis regroupe en tas ce qu'il ramene. Sur un theatre plus petit que 400 m,
 * ce disque contient TOUT LE MONDE, et le regroupement par chainage est en
 * O(n²) — le tout une fois par homme. Donc ~0,25 · n³ operations par seconde.
 *
 * L'experience : la meme foule, mesuree deux fois, en ne changeant QUE la
 * portee de l'horizon. Si la theorie est bonne, le temps s'effondre.
 */
import { composer } from './composer.mjs';
import { foule } from './foule.mjs';
import { PARAMS } from '../src/params.js';

const N = Number(process.argv[2] ?? 1000);
const DUREE_S = Number(process.argv[3] ?? 4);

function mesurer(etiquette) {
  const sim = composer(foule(N));
  const temps = { perception: 0 };
  const vrai = sim.cognition.phasePerception.bind(sim.cognition);
  sim.cognition.phasePerception = (dt) => {
    const t = process.hrtime.bigint();
    vrai(dt);
    temps.perception += Number(process.hrtime.bigint() - t) / 1e6;
  };
  sim.orchestration.avancer(100);
  const t0 = process.hrtime.bigint();
  let pas = 0;
  for (let e = 0; e < DUREE_S * 1000; e += 100) { sim.orchestration.avancer(100); pas += 6; }
  const total = Number(process.hrtime.bigint() - t0) / 1e6;
  console.log(`  ${etiquette.padEnd(34)} ${(total / pas).toFixed(2).padStart(7)} ms/pas   `
    + `dont perception ${(temps.perception / pas).toFixed(2).padStart(6)} ms `
    + `(${Math.round((temps.perception / total) * 100)}%)`);
  return total / pas;
}

console.log(`\nSONDE HORIZON — ${N} corps, ${DUREE_S} s de sim\n`);
const avant = mesurer(`horizon a ${PARAMS.perception.masse.porteeMax} m (tel quel)`);
PARAMS.perception.masse.porteeMax = PARAMS.perception.portee;   // plus d'horizon
const apres = mesurer(`horizon coupe (${PARAMS.perception.portee} m)`);
console.log(`\n  facteur : x${(avant / apres).toFixed(1)} — l'horizon de masse coute `
  + `${Math.round((1 - apres / avant) * 100)} % du pas\n`);
