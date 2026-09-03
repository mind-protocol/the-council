/**
 * Lecteur des Observables — croise trois sources : les tableaux
 * `## Observables` des CLAUDE.md (les features déclarées), les tags `@viz`
 * des calques (ce que chaque calque revendique montrer), et le tableau
 * `calques:` de l'expose Présentation (ce qui est réellement branché).
 *
 * Vocabulaire des viz : `calque \`id\`` (vérifié mécaniquement),
 * `inspecteur \`champ\`` et `ui \`id\`` (déclaratifs — runtime seulement),
 * `intrinsèque` (la viz est la chose), `—` (aucune : divergence).
 */

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

/** `| \`slug\` | mécanique | viz |` */
const LIGNE_FEATURE = /^\|\s*`([\w-]+)`\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$/;
const REF_VIZ = /(calque|inspecteur|ui)\s*`([^`]+)`/g;

function sectionObservables(texte) {
  for (const bloc of texte.split(/^##\s+/m)) {
    if (bloc.startsWith('Observables')) return bloc;
  }
  return '';
}

/** Les features déclarées par les tableaux Observables. */
export function lireFeatures(containers) {
  const features = [];
  for (const c of containers) {
    const fichier = join(c.dossier, 'CLAUDE.md');
    if (!existsSync(fichier)) continue;
    const section = sectionObservables(readFileSync(fichier, 'utf8'));

    for (const ligne of section.split('\n')) {
      const m = ligne.match(LIGNE_FEATURE);
      if (!m || m[1] === 'Feature') continue;
      const [, slug, mecanique, cellule] = m;
      features.push({
        slug,
        container: c.id,
        mecanique,
        viz: [...cellule.matchAll(REF_VIZ)].map((r) => ({ type: r[1], id: r[2] })),
        intrinseque: /intrinsèque/i.test(cellule),
        source: `${c.dossier}/CLAUDE.md`,
      });
    }
  }
  return features;
}

/**
 * Les calques : fichiers de calques/, leurs tags @viz, et les ids réellement
 * branchés dans le tableau `calques:` de l'expose Présentation.
 */
export function lireCalques(racineSrc) {
  const dossier = join(racineSrc, 'presentation', 'calques');
  const calques = [];
  if (existsSync(dossier)) {
    for (const entree of readdirSync(dossier)) {
      if (!entree.endsWith('.js')) continue;
      const texte = readFileSync(join(dossier, entree), 'utf8');
      const tag = texte.match(/@viz\s+([^\n*]+)/);
      calques.push({
        id: entree.replace(/\.js$/, ''),
        fichier: `${racineSrc}/presentation/calques/${entree}`,
        revendique: tag ? tag[1].split(',').map((s) => s.trim()).filter(Boolean) : [],
      });
    }
  }

  // Branché = un `id: 'x'` dans l'expose dont x est un fichier de calques/.
  // Tolérant à la forme (littéral inline ou tableau CALQUES) : on ne se couple
  // pas à une écriture précise du code.
  const expose = join(racineSrc, 'presentation', 'expose.js');
  const branches = new Set();
  if (existsSync(expose)) {
    const texte = readFileSync(expose, 'utf8');
    const ids = new Set(calques.map((c) => c.id));
    for (const m of texte.matchAll(/id\s*:\s*'([^']+)'/g)) {
      if (ids.has(m[1])) branches.add(m[1]);
    }
  }
  return { calques, branches: [...branches] };
}

/** Les divergences features ↔ viz, dans les deux sens. */
export function divergencesObservables(features, { calques, branches }) {
  const divergences = [];
  const parId = new Map(calques.map((c) => [c.id, c]));
  const slugsDeclares = new Set(features.map((f) => f.slug));
  const branchesSet = new Set(branches);

  for (const f of features) {
    if (!f.viz.length && !f.intrinseque) {
      divergences.push({
        type: 'feature-sans-viz',
        containers: [f.container],
        message: `\`${f.slug}\` (${f.mecanique}) n'a aucune représentation visuelle.`,
      });
    }
    for (const v of f.viz.filter((v) => v.type === 'calque')) {
      const calque = parId.get(v.id);
      if (!calque) {
        divergences.push({
          type: 'viz-calque-inconnu',
          containers: [f.container],
          message: `\`${f.slug}\` référence le calque \`${v.id}\`, qui n'existe pas dans calques/.`,
        });
      } else if (!branchesSet.has(v.id)) {
        divergences.push({
          type: 'calque-non-branche',
          containers: [f.container, 'presentation'],
          message: `Le calque \`${v.id}\` (référencé par \`${f.slug}\`) existe mais n'est pas dans le tableau calques: de l'expose.`,
        });
      } else if (!calque.revendique.includes(f.slug)) {
        divergences.push({
          type: 'viz-non-revendiquee',
          containers: [f.container, 'presentation'],
          message: `\`${f.slug}\` dit être montré par le calque \`${v.id}\`, mais son @viz ne le revendique pas.`,
        });
      }
    }
  }

  for (const calque of calques) {
    if (!calque.revendique.length) {
      divergences.push({
        type: 'calque-sans-viz',
        containers: ['presentation'],
        message: `Le calque \`${calque.id}\` ne porte aucun tag @viz — on ne sait pas ce qu'il montre.`,
      });
    }
    for (const slug of calque.revendique.filter((s) => !slugsDeclares.has(s))) {
      divergences.push({
        type: 'viz-orpheline',
        containers: ['presentation'],
        message: `Le calque \`${calque.id}\` revendique \`${slug}\`, absent de tout tableau Observables.`,
      });
    }
  }

  return divergences;
}
