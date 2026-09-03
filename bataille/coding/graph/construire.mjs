/**
 * CLI : extraction → graphe.json → ARCHITECTURE.md
 * Usage : node coding/graph/construire.mjs
 */

import { writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { construireGraphe } from './construire-graphe.mjs';
import { lireMachines } from './lire-machines.mjs';
import { emettreMarkdown } from './emettre-mermaid.mjs';

const ici = dirname(fileURLToPath(import.meta.url));
const racine = resolve(ici, '..', '..');

// Les chemins du graphe restent relatifs à la racine du dépôt : le JSON est
// lisible et diffable quelle que soit la machine.
process.chdir(racine);

const graphe = construireGraphe('src', join('src', 'main.js'));
graphe.machines = await lireMachines('src');

writeFileSync(join(ici, 'graphe.json'), `${JSON.stringify(graphe, null, 2)}\n`, 'utf8');
writeFileSync(join(ici, 'ARCHITECTURE.md'), emettreMarkdown(graphe), 'utf8');

const r = graphe.resume;
console.log(`containers   ${r.implementes}/${r.containers} implémentés`);
console.log(`modules      ${r.modules}`);
console.log(`liens câblés ${r.liensCables}`);
console.log(`contrats     ${r.contratsDeclares} déclarés`);
console.log(`observables  ${r.featuresAvecViz}/${r.features} features avec viz`);
console.log(`divergences  ${r.divergences}`);

for (const d of graphe.divergences) console.log(`  · [${d.type}] ${d.message}`);

console.log('\ncoding/graph/graphe.json');
console.log('coding/graph/ARCHITECTURE.md');
