/**
 * Vécu des machines — outil de diagnostic headless : court un scénario et
 * imprime, pour le CHEF de la première unité et deux hommes tirés au sort
 * (seedé : reproductible), le temps passé dans chaque état, le nombre de
 * bascules par transition, et quelques variables utiles (ordre en cours,
 * objectif, état-major du chef).
 *
 * Usage : node coding/vecu.mjs [dureeS=300] [scenario=premiere-lance]
 */

import { composer } from './fumee.mjs';
import { SCENARIOS } from '../src/scenarios/index.js';

const dureeS = Number(process.argv[2] ?? 300);
const idScenario = process.argv[3] ?? 'premiere-lance';
const entree = SCENARIOS.find((s) => s.id === idScenario);
if (!entree) {
  console.error(`scenario inconnu '${idScenario}' — dispo : ${SCENARIOS.map((s) => s.id).join(', ')}`);
  process.exit(1);
}

const sim = composer(entree.scenario);
for (let f = 0; f < dureeS * 10; f++) sim.orchestration.avancer(100);

const { idChef, membres } = sim.unites[0];
// deux hommes « au hasard » mais REPRODUCTIBLES : tirés sur le seed du scénario
const hommes = membres.filter((id) => id !== idChef);
const tirer = (n) => hommes[(entree.scenario.seed * (n + 7)) % hommes.length];
const echantillon = [idChef, tirer(1), tirer(2)];

const barre = (part) => '█'.repeat(Math.round(part * 30)).padEnd(30, '·');

for (const id of echantillon) {
  const i = sim.cognition.introspecter(id);
  const nom = sim.monde.corpsParId(id)?.nom ?? `#${id}`;
  const role = id === idChef ? 'CHEF' : 'homme';
  console.log(`\n══ ${nom} (${role}, #${id}) — etat final : ${i.etat} ══`);
  console.log(`   objectif : ${i.objectifHumain ?? '—'}`);
  if (i.details?.ordre) console.log(`   ordre    : ${i.details.ordre}`);

  const vecu = i.machine?.vecu;
  if (!vecu) { console.log('   (pas de vécu — machine sans accumulation)'); continue; }

  const total = Object.values(vecu.tempsParEtat).reduce((s, v) => s + v, 0);
  console.log(`   ── temps par état (${total.toFixed(0)} s au total) ──`);
  for (const [etat, s] of Object.entries(vecu.tempsParEtat).sort((a, b) => b[1] - a[1])) {
    console.log(`   ${barre(s / total)} ${((s / total) * 100).toFixed(0).padStart(3)}%  ${etat} (${s.toFixed(0)} s)`);
  }

  const entrees = Object.entries(vecu.bascules).sort((a, b) => b[1] - a[1]);
  console.log(`   ── bascules (${entrees.reduce((s, [, n]) => s + n, 0)}) ──`);
  for (const [cle, n] of entrees) console.log(`   ${String(n).padStart(4)} ×  ${cle}`);

  if (i.etatMajor) {
    const em = i.etatMajor;
    console.log('   ── état-major ──');
    console.log(`   engagée : ${em.engagee ? `${em.engagee.nom} phase ${em.engagee.phase}` : 'aucune'}`);
    console.log(`   faits   : ${Object.entries(em.situation).filter(([, v]) => v === true).map(([k]) => k).join(', ')}`);
  }
}
