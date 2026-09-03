/**
 * Lecteur des expose.js et des modules internes — produit le graphe INTERNE
 * de chaque container, plus la NATURE de chaque dépendance injectée.
 *
 * La nature (vue / commande / puits) est annotée dans le JSDoc des expose :
 *   `@param {…} deps.appliquerIntegration — commande 🌍 (écrivain 1/2)`
 * C'est elle qui permet de retrouver le sens du flux de données à partir
 * d'un simple sens d'appel.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve, dirname } from 'node:path';

const IMPORT_LOCAL = /import\s*\{([^}]*)\}\s*from\s*'(\.[^']+)'/g;

/** Tous les .js d'un dossier, récursivement. */
function fichiersJs(dossier) {
  const trouves = [];
  for (const entree of readdirSync(dossier)) {
    const chemin = join(dossier, entree);
    if (statSync(chemin).isDirectory()) trouves.push(...fichiersJs(chemin));
    else if (entree.endsWith('.js')) trouves.push(chemin);
  }
  return trouves;
}

/** `src/monde/registre.js` → `monde_registre` (identifiant sûr pour Mermaid). */
export function idModule(containerId, cheminRelatif) {
  return `${containerId}_${cheminRelatif.replace(/\.js$/, '').replace(/[^\w]+/g, '_')}`;
}

/**
 * Modules d'un container et arêtes internes (qui importe qui).
 * @returns {{modules: Array, internes: Array<{de: string, vers: string}>}}
 */
export function lireModules(container) {
  if (!container.implemente) return { modules: [], internes: [] };

  const modules = [];
  const internes = [];

  for (const fichier of fichiersJs(container.dossier)) {
    const rel = relative(container.dossier, fichier).replace(/\\/g, '/');
    const texte = readFileSync(fichier, 'utf8');
    const id = idModule(container.id, rel);

    modules.push({
      id,
      fichier: fichier.replace(/\\/g, '/'),
      chemin: rel,
      estExpose: rel === 'expose.js',
      lignes: texte.split('\n').length,
    });

    for (const m of texte.matchAll(IMPORT_LOCAL)) {
      const cible = relative(
        container.dossier,
        resolve(dirname(fichier), m[2])
      ).replace(/\\/g, '/');
      internes.push({
        de: id,
        vers: idModule(container.id, cible),
        noms: m[1].split(',').map((n) => n.trim()).filter(Boolean),
      });
    }
  }
  return { modules, internes };
}

/** Aplatit un bloc JSDoc en une ligne exploitable. */
function aplatir(bloc) {
  return bloc.replace(/^\s*\/?\*+\/?/gm, ' ').replace(/\s+/g, ' ');
}

/**
 * Nature d'une dépendance d'après son annotation JSDoc.
 * L'ordre compte : « puits vers 🏃 » doit gagner sur un simple « vers ».
 */
function natureDe(annotation) {
  if (/écrivain|commande/i.test(annotation)) return 'commande';
  if (/puits|vers\s/i.test(annotation)) return 'puits';
  if (/vue/i.test(annotation)) return 'vue';
  return null;
}

/**
 * Nature annotée de chaque dépendance injectée, par nom de clé.
 * @returns {Map<string, {nature: string, annotation: string}>}
 */
export function lireNatures(container) {
  const natures = new Map();
  if (!container.implemente) return natures;

  const texte = readFileSync(join(container.dossier, 'expose.js'), 'utf8');
  for (const bloc of texte.match(/\/\*\*[\s\S]*?\*\//g) || []) {
    for (const morceau of aplatir(bloc).split('@param').slice(1)) {
      const m = morceau.match(/deps\.([A-Za-z_$][\w$]*)\s*—\s*([^@]*)/);
      if (!m) continue;
      const annotation = m[2].trim();
      const nature = natureDe(annotation);
      if (nature) natures.set(m[1], { nature, annotation });
    }
  }
  return natures;
}
