/**
 * Assemblage : croise le graphe DÉCLARÉ (CLAUDE.md) et le graphe RÉEL
 * (câblage de main.js), et produit le JSON intermédiaire.
 *
 * L'écart entre les deux est le livrable intéressant : il rend visibles les
 * contrats déclarés mais jamais câblés, les puits morts, et les containers
 * encore vides.
 */

import { lireContainers, lireDeclarations } from './lire-claude-md.mjs';
import { lireModules, lireNatures } from './lire-expose.mjs';
import { lireBootstrap } from './lire-bootstrap.mjs';
import { lireFeatures, lireCalques, divergencesObservables } from './lire-observables.mjs';

const cle = (flux) => `${flux.fournisseur}->${flux.consommateur}`;

/** Ordre stable : le JSON doit differ proprement d'une exécution à l'autre. */
function trier(liens) {
  return [...liens].sort((a, b) =>
    `${a.appelant}${a.appele}${a.dep}`.localeCompare(`${b.appelant}${b.appele}${b.dep}`)
  );
}

function divergencesDe(containers, declarations, liens) {
  const divergences = [];
  const nommes = new Map(containers.map((c) => [c.id, c]));
  const reels = liens.filter((l) => l.appelant !== 'bootstrap');

  for (const c of containers) {
    if (!c.implemente) {
      divergences.push({
        type: 'container-non-implemente',
        containers: [c.id],
        message: `${c.nom} a un CLAUDE.md mais pas d'expose.js — aucun code.`,
      });
    }
  }

  const nonDiffus = declarations.filter((d) => !d.diffus && d.fournisseur && d.consommateur);
  const diffus = new Set(declarations.filter((d) => d.diffus).map((d) => d.fournisseur));
  const declares = new Set(nonDiffus.map(cle));
  const cables = new Set(reels.filter((l) => l.etat === 'cable').map(cle));
  // Un puits mort est déjà signalé comme tel : ne pas le compter deux fois.
  const morts = new Set(reels.filter((l) => l.etat === 'stub').map(cle));

  for (const lien of reels) {
    if (lien.etat === 'stub') {
      divergences.push({
        type: 'puits-mort',
        containers: [lien.appelant, lien.appele],
        message: `${nommes.get(lien.appelant).nom} → ${nommes.get(lien.appele).nom} : `
          + `\`${lien.dep}\` est câblé mais son corps est vide${lien.note ? ` (${lien.note})` : ''}.`,
      });
    }
  }

  for (const k of new Set(nonDiffus.map(cle))) {
    if (cables.has(k) || morts.has(k)) continue;
    const [f, c] = k.split('->');
    const exemple = nonDiffus.find((d) => cle(d) === k);
    divergences.push({
      type: 'declare-non-cable',
      containers: [f, c],
      message: `${nommes.get(f).nom} → ${nommes.get(c).nom} : déclaré `
        + `(${exemple.charge}) mais absent du câblage.`,
    });
  }

  for (const k of new Set(reels.filter((l) => l.etat === 'cable').map(cle))) {
    const [f, c] = k.split('->');
    if (declares.has(k) || diffus.has(f)) continue;
    const exemple = reels.find((l) => cle(l) === k);
    divergences.push({
      type: 'cable-non-declare',
      containers: [f, c],
      message: `${nommes.get(f).nom} → ${nommes.get(c).nom} : câblé `
        + `(\`${exemple.membres.join(', ')}\`${exemple.via ? ` via ${exemple.via}` : ''}) `
        + `mais absent des CLAUDE.md.`,
    });
  }

  for (const k of new Set(nonDiffus.map(cle))) {
    const cotes = new Set(nonDiffus.filter((d) => cle(d) === k).map((d) => d.declarePar));
    const [f, c] = k.split('->');
    if (cotes.has(f) && cotes.has(c)) continue;
    divergences.push({
      type: 'declaration-unilaterale',
      containers: [f, c],
      message: `${nommes.get(f).nom} → ${nommes.get(c).nom} : déclaré seulement `
        + `par ${nommes.get([...cotes][0]).nom}, le pair ne le mentionne pas.`,
    });
  }

  return divergences;
}

/** @param {string} racineSrc dossier src/ @param {string} cheminMain */
export function construireGraphe(racineSrc, cheminMain) {
  const containers = lireContainers(racineSrc);
  const naturesParContainer = new Map();

  for (const container of containers) {
    const { modules, internes } = lireModules(container);
    container.modules = modules;
    container.internes = internes;
    naturesParContainer.set(container.id, lireNatures(container));
  }

  const declarations = lireDeclarations(containers);
  const { liens, boucle } = lireBootstrap(cheminMain, containers, naturesParContainer);
  const features = lireFeatures(containers);
  const etatCalques = lireCalques(racineSrc);
  const divergences = [
    ...divergencesDe(containers, declarations, liens),
    ...divergencesObservables(features, etatCalques),
  ];

  return {
    racine: racineSrc,
    containers,
    declarations,
    liens: trier(liens),
    boucle,
    features,
    calques: etatCalques,
    divergences,
    resume: {
      containers: containers.length,
      implementes: containers.filter((c) => c.implemente).length,
      modules: containers.reduce((n, c) => n + c.modules.length, 0),
      liensCables: liens.filter((l) => l.etat === 'cable').length,
      contratsDeclares: declarations.length,
      features: features.length,
      featuresAvecViz: features.filter((f) => f.viz.length || f.intrinseque).length,
      divergences: divergences.length,
    },
  };
}
