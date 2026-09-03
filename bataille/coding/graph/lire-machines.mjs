/**
 * Lecteur des machines à états — AUCUN parsing : les machines sont des
 * DONNÉES (exports `MACHINE_*` des `brains/<nom>/machine.js`), on les
 * importe et on les lit. C'est le dividende de la décision « la machine
 * est une donnée » : le graphe dessiné est exactement celui qui s'exécute.
 */

import { readdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

/** @param {string} racineSrc @returns {Promise<Array<{brain, definition, source}>>} */
export async function lireMachines(racineSrc) {
  const dossier = join(racineSrc, 'cognition', 'brains');
  const machines = [];
  if (!existsSync(dossier)) return machines;

  for (const entree of readdirSync(dossier, { withFileTypes: true })) {
    if (!entree.isDirectory()) continue;
    const fichier = join(dossier, entree.name, 'machine.js');
    if (!existsSync(fichier)) continue;
    const module_ = await import(pathToFileURL(resolve(fichier)).href);
    for (const [nom, valeur] of Object.entries(module_)) {
      if (nom.startsWith('MACHINE_') && valeur && valeur.etats && valeur.transitions) {
        machines.push({
          brain: valeur.brain ?? entree.name,
          definition: valeur,
          source: `${racineSrc}/cognition/brains/${entree.name}/machine.js`,
        });
      }
    }
  }
  machines.sort((a, b) => a.brain.localeCompare(b.brain));
  return machines;
}
