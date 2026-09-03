// PROFIL — quelle phase du tick coute cher, a grande echelle.
// Compose une bataille synthetique de ~N corps et chronometre CHAQUE phase
// isolement sur M ticks. Sortie : ms/tick par phase, et la part du total.
//   node coding/profil-cerveaux.mjs [corps=1600] [ticks=40]
import { composer } from './composer.mjs';
import { PARAMS } from '../src/params.js';

const N = Number(process.argv[2] ?? 1600);
const TICKS = Number(process.argv[3] ?? 40);
const dt = PARAMS.dtFixe;

// deux camps face a face, en rangs — de quoi faire travailler perception,
// clusters et decision comme une vraie melee (pas des hommes isoles).
function scenarioDe(n) {
  const parCamp = Math.floor(n / 2);
  const largeur = 40;
  const unite = (camp, base) => {
    const livree = camp === 0 ? 'bleu' : 'jaune';
    const y0 = camp === 0 ? 0 : 60;
    const cap = camp === 0 ? Math.PI / 2 : -Math.PI / 2;
    const hommes = [];
    for (let i = 0; i < base; i++) {
      hommes.push({ nom: 'h', pos: { x: (i % largeur) * 0.8, y: y0 + Math.floor(i / largeur) * 0.8 } });
    }
    return { nom: 'camp' + camp, livree, posture: 'agression',
             equipement: { arme: 'epee', bouclier: true }, capInitial: cap,
             forme: { type: 'rangs', largeur, espacementLateral: 0.8, espacementRang: 0.8 },
             zone: { x: 0, y: y0, largeur: largeur, hauteur: 40 },
             chef: { nom: 'chef' + camp, pos: { x: 0, y: y0 }, panache: true },
             hommes };
  };
  // CAMPS=1 (env) : une seule masse amie -> personne n'a d'ennemi cru -> tout
  // le monde est CALME -> le facteurCalme joue a plein. CAMPS=2 (defaut) : face
  // a face, le pire cas pour le LOD (beaucoup d'agents en alerte).
  if (process.env.CAMPS === '1') {
    return { seed: 42, zone: { x: 0, y: 0, largeur: 100, hauteur: 100 }, maisons: [],
             unites: [unite(0, n - 1)] };
  }
  return { seed: 42, zone: { x: 0, y: 0, largeur: 100, hauteur: 100 }, maisons: [],
           unites: [unite(0, parCamp - 1), unite(1, parCamp - 1)] };
}

const sim = composer(scenarioDe(N));
const { cognition, action, physique, corpsContainer, monde } = sim;
const nCorps = [...monde.corps()].length;

// les phases, dans l'ordre reel du tick
const phases = [
  ['perception', () => cognition.phasePerception(dt)],
  ['decision', () => cognition.phaseDecision(dt)],
  ['action', () => action.phaseAction(dt)],
  ['physique', () => physique.phasePhysique(dt)],
  ['physiologie', () => corpsContainer.phasePhysiologie(dt)],
  ['index', () => monde.reconstruireIndex()],
];

// rodage : 5 ticks pour que les caches et machines se stabilisent
for (let t = 0; t < 5; t++) for (const [, f] of phases) f();

const cumul = Object.fromEntries(phases.map(([nom]) => [nom, 0]));
for (let t = 0; t < TICKS; t++) {
  for (const [nom, f] of phases) {
    const t0 = performance.now();
    f();
    cumul[nom] += performance.now() - t0;
  }
}

const total = Object.values(cumul).reduce((a, b) => a + b, 0);
console.log(`${nCorps} corps · ${TICKS} ticks · dt ${dt}s\n`);
console.log('phase          ms/tick    part');
for (const [nom] of phases) {
  const msTick = cumul[nom] / TICKS;
  const part = (cumul[nom] / total) * 100;
  console.log(`${nom.padEnd(14)} ${msTick.toFixed(2).padStart(7)}  ${part.toFixed(1).padStart(5)}%`);
}
console.log(`${'TOTAL'.padEnd(14)} ${(total / TICKS).toFixed(2).padStart(7)}   (${(1000 / (total / TICKS)).toFixed(0)} tick/s max)`);
