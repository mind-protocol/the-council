/**
 * BANC D'ECHELLE — combien d'hommes le moteur porte, et ce qui plie en premier.
 *
 * On ne sait pas mettre « du monde dans le monde » avant de savoir ce que
 * coute un homme. Ce banc compose des batailles de plus en plus grosses, fait
 * tourner du temps simule, et mesure trois choses par pas de sim :
 * la PERCEPTION (🧠), la DECISION (🧠), et le reste (🏃 ⚙️ 🌍).
 *
 * Le budget : a 60 images par seconde, un pas doit tenir sous 16,7 ms pour
 * suivre en x1 — et sous 3,3 ms pour tenir le x5.
 *
 * Usage : node coding/banc-echelle.mjs [dureeS] [n1,n2,...]
 */

import { composer } from './composer.mjs';
import { sauver } from '../src/partie.js';
import { foule } from './foule.mjs';

const DUREE_S = Number(process.argv[2] ?? 20);
const TAILLES = (process.argv[3] ?? '120,480,1000,2000,4000').split(',').map(Number);
const MS_PAR_FRAME = 100;


/**
 * Chronometre chaque phase. Les phases du pipeline appellent les methodes par
 * LOOKUP sur le container (`cognition.phasePerception(dt)`) : on peut donc les
 * envelopper apres composition, sans toucher au cablage.
 */
function chronometrer(sim) {
  const temps = {};
  const envelopper = (objet, methode, nom) => {
    const vrai = objet[methode].bind(objet);
    temps[nom] = 0;
    objet[methode] = (dt) => {
      const t = process.hrtime.bigint();
      vrai(dt);
      temps[nom] += Number(process.hrtime.bigint() - t) / 1e6;
    };
  };
  envelopper(sim.cognition, 'phasePerception', 'perception');
  envelopper(sim.cognition, 'phaseDecision', 'decision');
  envelopper(sim.action, 'phaseAction', 'action');
  envelopper(sim.physique, 'phasePhysique', 'physique');
  return temps;
}

const ms = (n) => n.toFixed(2).padStart(7);
const pct = (n, t) => `${String(Math.round((n / t) * 100)).padStart(3)}%`;
console.log(`\nBANC D'ECHELLE — ${DUREE_S} s de sim par taille`);
console.log('\n   corps │   ms/pas │  x1 (16,7) │  x5 (3,3) │  sauvegarde │  octets/corps');
console.log('  ───────┼──────────┼────────────┼───────────┼─────────────┼──────────────');

for (const n of TAILLES) {
  const sim = composer(foule(n));
  const temps = chronometrer(sim);
  const reel = [...sim.monde.corps()].length;
  // une passe a blanc : le premier pas paie la navgrid et les caches
  sim.orchestration.avancer(MS_PAR_FRAME);
  const t0 = process.hrtime.bigint();
  let pas = 0;
  for (let e = 0; e < DUREE_S * 1000; e += MS_PAR_FRAME) { sim.orchestration.avancer(MS_PAR_FRAME); pas += 6; }
  const parPas = Number(process.hrtime.bigint() - t0) / 1e6 / pas;
  const octets = JSON.stringify(sauver(sim)).length;
  console.log(`  ${String(reel).padStart(6)} │ ${ms(parPas)} │ ${(parPas < 16.7 ? '    oui   ' : '    NON   ')} │ ${(parPas < 3.3 ? '   oui   ' : '   NON   ')} │ ${(octets / 1024 / 1024).toFixed(2).padStart(8)} Mo │ ${String(Math.round(octets / reel)).padStart(8)}`);
  const total = Object.values(temps).reduce((a, b) => a + b, 0);
  console.log(`         └─ ` + Object.entries(temps)
    .sort((a, b) => b[1] - a[1])
    .map(([nom, v]) => `${nom} ${pct(v, total)}`).join('   '));
}
console.log('');
