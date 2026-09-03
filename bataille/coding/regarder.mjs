/**
 * REGARDER — la sim sous Node, rendue par outils/ascii.mjs.
 *
 * Le navigateur bride la boucle d'images des que son panneau passe derriere :
 * on ne peut ni observer une sim longue, ni la voir avancer pendant qu'on
 * travaille. Ici la meme sim tourne headless, et l'on imprime la MEME vue
 * ascii que `window.ascii()` donne dans la console du jeu.
 *
 * Ce fichier ne dessine rien : tout le rendu vit dans outils/ascii.mjs, une
 * seule fois, pour l'ecran comme pour le terminal.
 *
 * Usage :
 *   node coding/regarder.mjs               600 s, une image toutes les 60 s
 *   node coding/regarder.mjs 120 10        120 s, une image toutes les 10 s
 *   node coding/regarder.mjs 120 10 --vu 1 en plus : ce que l'homme 1 VOIT
 */

import { composer } from './composer.mjs';
import { sauver } from '../src/partie.js';
import { rendreAscii, rendreFaits, rendreVu } from '../outils/ascii.mjs';
import { BATAILLE_RANGEE } from '../src/scenarios/index.js';

const DUREE_S = Number(process.argv[2] ?? 600);
const PAS_S = Number(process.argv[3] ?? 60);
const iVu = process.argv.indexOf('--vu');
const ID_VU = iVu >= 0 ? Number(process.argv[iVu + 1]) : null;
const MS_PAR_FRAME = 100;

const sim = composer(BATAILLE_RANGEE);

/** La meme forme d'etat que main.js donne a `window.ascii()`. */
const etat = () => {
  const s = sauver(sim, { titre: BATAILLE_RANGEE.titre });
  return { corps: s.monde.registre.corps, scenario: s.scenario, tempsSim: s.tempsSim };
};

let ecoule = 0;
for (let jalon = 0; jalon <= DUREE_S; jalon += PAS_S) {
  while (ecoule < jalon) { sim.orchestration.avancer(MS_PAR_FRAME); ecoule += MS_PAR_FRAME / 1000; }
  console.log(rendreAscii(etat()));
  console.log(rendreFaits(etat()));
  if (ID_VU != null) {
    const lui = [...sim.monde.corps()].find((c) => c.id === ID_VU);
    console.log(`\n  — ce que ${lui?.nom ?? ID_VU} voit —`);
    console.log(rendreVu(sim.cognition.introspecter?.(ID_VU)?.perception
      ?? sim.cognition.perceptionDebug(ID_VU), { maLivree: lui?.livree }));
  }
  console.log('');
}
