/**
 * Lecteur des CLAUDE.md — produit le graphe DÉCLARÉ (l'intention).
 * Deux sources : le tableau des containers dans src/CLAUDE.md, et la section
 * « Reçoit / Fournit » de chaque container.
 */

import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

/** `| ⏱️ **Orchestration** | [orchestration/](…) | Possède le temps… |` */
const LIGNE_TABLE =
  /^\|\s*([^|*]*?)\s*\*\*([^*]+)\*\*\s*\|\s*\[([^\]]+)\]\([^)]*\)\s*\|\s*(.+?)\s*\|\s*$/;

/** `- Reçoit du container 🌍 Monde (via Perception) : percepts.` */
const LIGNE_CONTRAT = /^-\s*(Reçoit|Fournit)\b([^:]*):\s*(.+?)\s*$/;

/** Le tableau de src/CLAUDE.md : la liste de vérité des containers. */
export function lireContainers(racineSrc) {
  const texte = readFileSync(join(racineSrc, 'CLAUDE.md'), 'utf8');
  const containers = [];
  for (const ligne of texte.split('\n')) {
    const m = ligne.match(LIGNE_TABLE);
    if (!m) continue;
    const dossier = m[3].replace(/\/$/, '');
    containers.push({
      id: dossier,
      nom: m[2].trim(),
      emoji: m[1].trim(),
      dossier: `${racineSrc}/${dossier}`,
      intention: m[4].trim(),
      implemente: existsSync(join(racineSrc, dossier, 'expose.js')),
      modules: [],
    });
  }
  return containers;
}

/** Isole une section `## Titre` jusqu'au `##` suivant. */
function sectionDe(texte, titre) {
  for (const bloc of texte.split(/^##\s+/m)) {
    if (bloc.startsWith(titre)) return bloc.slice(titre.length);
  }
  return '';
}

/**
 * Le pair d'un contrat = le premier nom de container cité à GAUCHE du `:`.
 * Chercher le nom (et non l'emoji) évite les faux positifs des variantes
 * d'emoji, et se limiter à la gauche du `:` évite les containers mentionnés
 * en passant dans la description.
 */
function pairCite(gauche, containers) {
  let trouve = null;
  for (const c of containers) {
    const i = gauche.indexOf(c.nom);
    if (i >= 0 && (trouve === null || i < trouve.i)) trouve = { i, c };
  }
  return trouve ? trouve.c : null;
}

/**
 * Contrats déclarés par un container, normalisés en FLUX DE DONNÉES
 * (fournisseur → consommateur), qui est ce que décrivent les CLAUDE.md.
 * @returns {Array<{fournisseur, consommateur, canal, charge, verbe, declarePar, source}>}
 */
function lireContrats(container, containers) {
  const fichier = join(container.dossier, 'CLAUDE.md');
  if (!existsSync(fichier)) return [];
  const section = sectionDe(readFileSync(fichier, 'utf8'), 'Reçoit / Fournit');
  const contrats = [];

  for (const ligne of section.split('\n')) {
    const m = ligne.trim().match(LIGNE_CONTRAT);
    if (!m) continue;
    const [, verbe, gauche, charge] = m;
    const pair = pairCite(gauche, containers);
    const canalBrut = gauche.match(/\(([^)]*)\)/);

    contrats.push({
      fournisseur: verbe === 'Reçoit' ? pair && pair.id : container.id,
      consommateur: verbe === 'Reçoit' ? container.id : pair && pair.id,
      canal: canalBrut ? canalBrut[1].trim() : null,
      charge: charge.replace(/\.$/, ''),
      verbe: verbe.toLowerCase(),
      declarePar: container.id,
      source: `${container.dossier}/CLAUDE.md`,
      // `- Fournit à tous les containers : la cadence` n'a pas de pair nommé.
      diffus: pair === null,
    });
  }
  return contrats;
}

/** Tous les contrats déclarés, tous containers confondus. */
export function lireDeclarations(containers) {
  return containers.flatMap((c) => lireContrats(c, containers));
}
