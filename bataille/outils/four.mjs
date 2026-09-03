/**
 * LE FOUR — jouer une bataille SANS ÉCRAN, et rendre ce qu'on en a vu.
 *
 * La page du moteur vit dans une boucle de frame : elle a besoin d'un onglet
 * visible, et `requestAnimationFrame` s'arrête dès qu'on regarde ailleurs. Un
 * homme dépêché n'a pas d'onglet — il a une session et un shell. Ceci lui
 * donne la même simulation, sous Node, et lui rend du texte.
 *
 * Ce n'est PAS un moteur de plus : la composition est celle de `coding/
 * fumee.mjs` (qui est elle-même le reflet de `src/main.js` sans la
 * Présentation), et on l'importe au lieu de la recopier.
 *
 * Usage :
 *   node outils/four.mjs --scenario assaut-de-rue --secondes 20
 *   node outils/four.mjs --scenario assaut-de-rue --secondes 20 --vu 1
 *   node outils/four.mjs --liste
 *   node outils/four.mjs --scenario assaut-de-rue --secondes 20 --json
 *
 * `--vu <id>` rend LES YEUX DE CET HOMME (ses croyances datées) au lieu de la
 * vue omnisciente. C'est ce qu'on donne à un PNJ ; l'autre lui mentirait en
 * lui offrant la vérité du registre.
 *
 * `--borne <ms>` : une bataille qui ne converge pas ne doit pas bloquer un
 * tour de jeu. Dépassée, on rend ce qu'on a et on le DIT (`borne_atteinte`).
 */

import { readFileSync } from 'node:fs';
//  a ete extrait de fumee.mjs vers coding/composer.mjs. C'est la
// meme composition — src/main.js sans la Presentation — et on l'importe au
// lieu de la recopier.
import { composer } from '../coding/composer.mjs';
import { SCENARIOS } from '../src/scenarios/index.js';
import { PARAMS } from '../src/params.js';
import { resoudreMontage } from './montages.mjs';
import { rendreAscii, rendreFaits, rendreVu } from './ascii.mjs';

function lireArgs(argv) {
  const o = { secondes: 10, larg: 74, borne: 30000, msParFrame: 100 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--liste') o.liste = true;
    else if (a === '--json') o.json = true;
    else if (a.startsWith('--')) o[a.slice(2)] = argv[++i];
  }
  for (const k of ['secondes', 'larg', 'borne', 'msParFrame', 'vu']) {
    if (o[k] != null) o[k] = Number(o[k]);
  }
  return o;
}

/** Le masque de ville, quand le scénario en déclare un. Absent = on le dit. */
function chargerRessources(scenario) {
  const m = scenario.terrain && scenario.terrain.masque;
  if (!m || !m.fichier) return { ressources: {}, note: null };
  const chemin = resoudreMontage(m.fichier) || m.fichier;
  try {
    return { ressources: { masque: { ...m, bits: new Uint8Array(readFileSync(chemin)) } }, note: null };
  } catch {
    return { ressources: {}, note: `terrain absent (${chemin}) — joué sans le masque de ville` };
  }
}

export function cuire({ scenario, secondes = 10, msParFrame = 100, borne = 30000 }) {
  const { ressources, note } = chargerRessources(scenario);
  const sim = composer(scenario, ressources);
  const frames = Math.max(1, Math.round((secondes * 1000) / msParFrame));
  const debut = Date.now();
  let jouees = 0;
  for (let f = 0; f < frames; f++) {
    sim.orchestration.avancer(msParFrame);
    jouees++;
    if (Date.now() - debut > borne) break;
  }
  return {
    sim,
    note,
    borne_atteinte: jouees < frames,
    joue_s: (jouees * msParFrame) / 1000,
    demande_s: secondes,
    ms_reels: Date.now() - debut,
  };
}

/** L'état plat que les vues ASCII attendent — même forme que dans la page. */
function etatPlat(sim, scenario) {
  return {
    corps: Array.from(sim.monde.corps(), (c) => ({
      id: c.id, pos: { x: c.pos.x, y: c.pos.y }, livree: c.livree,
      nom: c.nom, panache: c.panache, gabarit: c.gabarit, posture: c.posture,
    })),
    scenario: scenario.titre,
    tempsSim: sim.orchestration.transport.etat().tempsSim,
  };
}

function principal() {
  const o = lireArgs(process.argv.slice(2));

  if (o.liste || (!o.scenario && !o.fichier)) {
    console.log('Scenarios :');
    for (const { id, scenario } of SCENARIOS) console.log(`  ${id.padEnd(24)} ${scenario.titre}`);
    if (!o.scenario) console.log('\nManque --scenario <id> (ou --fichier <composition.json>).');
    return o.scenario ? 0 : 1;
  }

  // --fichier : une COMPOSITION de l'etat (node serveur/domaine/ost.js > ost.json) plutot qu'un scenario du catalogue
  const entree = o.fichier ? { id: 'fichier', scenario: JSON.parse(readFileSync(o.fichier, 'utf-8')) }
    : SCENARIOS.find((s) => s.id === o.scenario);
  if (!entree) {
    console.error(`scenario inconnu : ${o.scenario} — --liste pour les voir`);
    return 1;
  }

  const cuisson = cuire({ scenario: entree.scenario, secondes: o.secondes,
                          msParFrame: o.msParFrame, borne: o.borne });
  const { sim } = cuisson;
  const etat = etatPlat(sim, entree.scenario);

  // LES YEUX D'UN HOMME — sa livree vient du registre (elle n'est pas dans son
  // snapshot de croyances), le reste vient de sa tete.
  let vue;
  if (o.vu != null) {
    const lui = etat.corps.find((c) => c.id === o.vu);
    if (!lui) { console.error(`aucun corps ${o.vu} — ils vont de 1 a ${etat.corps.length}`); return 1; }
    vue = rendreVu(sim.cognition.perceptionDebug(o.vu), { larg: o.larg, maLivree: lui.livree });
    vue = `${lui.nom || 'sans nom'} (${lui.livree}${lui.panache ? ', a panache' : ''})\n` + vue;
  } else {
    vue = rendreAscii(etat, { larg: o.larg });
  }

  const faits = rendreFaits(etat);
  if (o.json) {
    console.log(JSON.stringify({ ...faits, ...horsFiction(cuisson), vue }, null, 2));
    return 0;
  }
  const h = horsFiction(cuisson);
  console.log(vue);
  console.log('');
  console.log(`— ${h.joue_s} s jouees en ${h.ms_reels} ms` +
              (h.borne_atteinte ? ` — BORNE ATTEINTE (${cuisson.demande_s} s demandees)` : '') +
              (h.note ? `\n— ${h.note}` : ''));
  return 0;
}

const horsFiction = (c) => ({ joue_s: c.joue_s, ms_reels: c.ms_reels,
                              borne_atteinte: c.borne_atteinte, note: c.note });

import { pathToFileURL } from 'node:url';
// Lance seulement si on l'appelle en ligne de commande. Importe comme module
// (un test, un autre outil), process.argv[1] peut ne pas exister du tout.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(principal());
}
