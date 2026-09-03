/**
 * Émetteur Mermaid — ne connaît que le JSON intermédiaire.
 * C'est la pièce jetable : le jour où Mermaid plafonne (repli/dépli, filtres,
 * surlignage de chemin), seul ce fichier est réécrit.
 */

/** Styles de trait par nature d'appel — la forme porte le sens. */
const FLECHE = { vue: '-->', commande: '==>', puits: '-.->', cadence: '-->' };

const LEGENDE = [
  '`-->` vue (lecture, tirée par l\'appelant)',
  '`==>` commande (écriture, poussée par l\'appelant)',
  '`-.->` puits (événement poussé vers l\'appelé)',
  'trait rouge : câblé mais vide — trait gris pointillé : déclaré, jamais câblé',
];

const etiquette = (s) => String(s).replace(/"/g, '#quot;').replace(/\n/g, ' ');
const cellule = (s) => String(s).replace(/\|/g, '\\|');
const ancre = (id) => `c-${id}`;

/** Petit accumulateur : lignes du diagramme + linkStyle indexés. */
function diagramme(entete) {
  const lignes = [entete];
  const styles = [];
  let index = 0;
  return {
    ligne: (l) => lignes.push(`  ${l}`),
    arete(source, fleche, cible, texte, style) {
      const label = texte ? `|"${etiquette(texte)}"|` : '';
      lignes.push(`  ${source} ${fleche}${label} ${cible}`);
      if (style) styles.push(`  linkStyle ${index} ${style}`);
      index++;
    },
    rendre: () => ['```mermaid', ...lignes, ...styles, '```'].join('\n'),
  };
}

const noeud = (c) => `${c.id}["${etiquette(`${c.emoji} ${c.nom}`)}"]`;

/** Une arête par (appelant, appelé, nature) : les deps deviennent l'étiquette. */
function agreger(liens) {
  const paquets = new Map();
  for (const lien of liens) {
    const k = `${lien.appelant}|${lien.appele}|${lien.nature}|${lien.etat}`;
    if (!paquets.has(k)) paquets.set(k, { ...lien, deps: new Set() });
    paquets.get(k).deps.add(lien.dep);
  }
  return [...paquets.values()].map((p) => ({ ...p, deps: [...p.deps] }));
}

function classesAbsentes(d, containers) {
  const absents = containers.filter((c) => !c.implemente).map((c) => c.id);
  d.ligne('classDef absent fill:#f6f6f6,stroke:#bbb,stroke-dasharray:4 3,color:#888;');
  if (absents.length) d.ligne(`class ${absents.join(',')} absent;`);
}

/** Panorama 1 — qui appelle l'expose de qui. Vérité du code, uniquement. */
function panoramaAppels(graphe) {
  const d = diagramme('flowchart LR');
  d.ligne('bootstrap(["main.js — bootstrap"]);');
  for (const c of graphe.containers) d.ligne(`${noeud(c)};`);

  for (const lien of agreger(graphe.liens)) {
    d.arete(
      lien.appelant,
      FLECHE[lien.nature] || '-->',
      lien.appele,
      lien.deps.join(', '),
      lien.etat === 'stub' ? 'stroke:#c0392b,stroke-dasharray:3 3;' : null
    );
  }

  classesAbsentes(d, graphe.containers);
  for (const c of graphe.containers) d.ligne(`click ${c.id} "#${ancre(c.id)}";`);
  return d.rendre();
}

/**
 * Panorama 2 — le flux de données, déclaré ET réel.
 * Sens différent du premier : une vue se tire, donc l'appel remonte le flux.
 */
function panoramaFlux(graphe) {
  const d = diagramme('flowchart LR');
  for (const c of graphe.containers) d.ligne(`${noeud(c)};`);

  const vus = new Set();
  for (const lien of graphe.liens) {
    if (lien.appelant === 'bootstrap' || lien.etat !== 'cable') continue;
    const k = `${lien.fournisseur}->${lien.consommateur}`;
    if (vus.has(k)) continue;
    vus.add(k);
    d.arete(lien.fournisseur, '-->', lien.consommateur, null, null);
  }

  for (const div of graphe.divergences.filter((x) => x.type === 'declare-non-cable')) {
    const [f, c] = div.containers;
    d.arete(f, '-.->', c, 'déclaré', 'stroke:#bbb,stroke-dasharray:5 4;');
  }

  classesAbsentes(d, graphe.containers);
  return d.rendre();
}

/** La boucle : l'ordre des phases est une décision d'archi, on la montre. */
function boucle(graphe) {
  if (!graphe.boucle.length) return '_Aucune phase détectée._';
  const parId = new Map(graphe.containers.map((c) => [c.id, c]));
  const d = diagramme('flowchart LR');
  d.ligne('tick(["⏱️ tick — dt fixe"]);');

  graphe.boucle.forEach((phase, i) => {
    const c = parId.get(phase.container);
    d.ligne(`p${i}["${etiquette(`${i + 1} · ${phase.nom}`)}<br/>${etiquette(`${c.emoji} ${c.nom}`)}"];`);
  });
  d.arete('tick', '-->', 'p0', null, null);
  for (let i = 0; i < graphe.boucle.length - 1; i++) d.arete(`p${i}`, '-->', `p${i + 1}`, null, null);
  d.arete(`p${graphe.boucle.length - 1}`, '-.->', 'tick', 'pas suivant', null);
  return d.rendre();
}

const dossierDe = (chemin) =>
  chemin.includes('/') ? chemin.slice(0, chemin.lastIndexOf('/')) : '.';

/** Un éventail de 13 modules déborde ; les sous-dossiers le replient. */
function grouperParDossier(modules) {
  const groupes = new Map();
  for (const m of modules) {
    const dossier = dossierDe(m.chemin);
    if (!groupes.has(dossier)) groupes.set(dossier, []);
    groupes.get(dossier).push(m);
  }
  return groupes;
}

function noeudModule(m, court) {
  const libelle = court ? m.chemin.slice(m.chemin.lastIndexOf('/') + 1) : m.chemin;
  return m.estExpose ? `${m.id}[[${etiquette(libelle)}]]` : `${m.id}["${etiquette(libelle)}"]`;
}

/** Détail d'un container : ses modules, et ses contrats externes. */
function detail(container, graphe) {
  const parId = new Map(graphe.containers.map((c) => [c.id, c]));
  // LR : la croissance se fait en hauteur, qui se parcourt mieux qu'en largeur
  // dans un document.
  const d = diagramme('flowchart LR');

  d.ligne(`subgraph ${container.id}["${etiquette(`${container.emoji} ${container.nom}`)}"]`);
  d.ligne('  direction TB');
  for (const [dossier, modules] of grouperParDossier(container.modules)) {
    if (dossier === '.') {
      for (const m of modules) d.ligne(`  ${noeudModule(m, false)}`);
      continue;
    }
    d.ligne(`  subgraph ${container.id}__${dossier.replace(/\W+/g, '_')}["${etiquette(`${dossier}/`)}"]`);
    d.ligne('    direction TB');
    for (const m of modules) d.ligne(`    ${noeudModule(m, true)}`);
    d.ligne('  end');
  }
  d.ligne('end');

  const externes = new Set();
  const expose = (container.modules.find((m) => m.estExpose) || {}).id || container.id;

  for (const lien of agreger(graphe.liens)) {
    const style = lien.etat === 'stub' ? 'stroke:#c0392b,stroke-dasharray:3 3;' : null;
    const fleche = FLECHE[lien.nature] || '-->';
    if (lien.appele === container.id && lien.appelant !== container.id) {
      externes.add(lien.appelant);
      d.arete(lien.appelant, fleche, expose, lien.deps.join(', '), style);
    } else if (lien.appelant === container.id && lien.appele !== container.id) {
      externes.add(lien.appele);
      d.arete(expose, fleche, lien.appele, lien.deps.join(', '), style);
    }
  }

  for (const id of externes) {
    const c = parId.get(id);
    d.ligne(c ? `${noeud(c)};` : `${id}(["main.js — bootstrap"]);`);
  }
  for (const arete of container.internes) d.arete(arete.de, '-->', arete.vers, null, null);

  return d.rendre();
}

/** Un stateDiagram Mermaid par machine — dessiné depuis la donnée exécutée. */
function diagrammeMachine({ brain, definition: d }) {
  const feuille = (chemin) => chemin.split('.').pop();
  const lignes = ['stateDiagram-v2', '  direction LR'];

  for (const [nom, e] of Object.entries(d.etats)) {
    if (!e.sousEtats) continue;
    lignes.push(`  state ${nom} {`);
    lignes.push(`    [*] --> ${e.initial}`);
    for (const sousNom of Object.keys(e.sousEtats)) lignes.push(`    ${sousNom}`);
    lignes.push('  }');
  }

  lignes.push(`  [*] --> ${d.initial.split('.')[0]}`);
  if (d.transitions.some((t) => t.de === '*')) {
    lignes.push('  state "∗ de partout" as _partout');
  }
  for (const t of d.transitions) {
    const de = t.de === '*' ? '_partout' : feuille(t.de);
    lignes.push(`  ${de} --> ${feuille(t.vers)}: ${etiquette(t.libelle)}`);
  }

  const reserves = Object.entries(d.etats)
    .filter(([, e]) => !e.agir && !e.sousEtats)
    .map(([nom]) => nom);
  if (reserves.length) {
    for (const nom of reserves) lignes.push(`  ${nom}`);
    lignes.push('  classDef reserve fill:#f6f6f6,stroke:#bbb,stroke-dasharray:4 3,color:#888;');
    lignes.push(`  class ${reserves.join(',')} reserve`);
  }

  return [
    `### brain \`${brain}\``,
    '',
    'États réservés grisés : déclarés sans transition entrante — la feuille',
    'de route est dans le diagramme. Chaque arête porte sa justification.',
    '',
    '```mermaid',
    ...lignes,
    '```',
  ].join('\n');
}

function sectionMachines(graphe) {
  if (!graphe.machines || !graphe.machines.length) return '';
  return [
    '## Machines à états des brains',
    '',
    'Dessinées depuis les exports `MACHINE_*` des brains — la donnée dessinée',
    'est exactement celle qui s\'exécute (aucun parsing). Au runtime : le',
    'journal des transitions et l\'état courant sont dans l\'Inspecteur.',
    '',
    ...graphe.machines.map(diagrammeMachine),
    '',
  ].join('\n');
}

function celluleViz(f) {
  if (f.intrinseque) return 'intrinsèque';
  if (!f.viz.length) return '**—**';
  return f.viz.map((v) => `${v.type} \`${v.id}\``).join(' + ');
}

/** Couverture des Observables : chaque feature et sa viz, manques en gras. */
function tableauObservables(graphe) {
  if (!graphe.features.length) return '_Aucune section Observables trouvée._';
  const parId = new Map(graphe.containers.map((c) => [c.id, c]));
  const lignes = ['| Container | Feature | Mécanique | Viz |', '|---|---|---|---|'];
  for (const f of graphe.features) {
    const c = parId.get(f.container);
    lignes.push(
      `| ${c ? c.emoji : ''} ${c ? c.nom : f.container} | \`${f.slug}\` `
        + `| ${cellule(f.mecanique)} | ${celluleViz(f)} |`
    );
  }
  return lignes.join('\n');
}

function tableauDivergences(graphe) {
  if (!graphe.divergences.length) return '_Aucune divergence : le câblage et les CLAUDE.md coïncident._';
  const lignes = ['| Type | Containers | Constat |', '|---|---|---|'];
  for (const d of graphe.divergences) {
    lignes.push(`| \`${d.type}\` | ${d.containers.join(' → ')} | ${cellule(d.message)} |`);
  }
  return lignes.join('\n');
}

function sectionContainer(container, graphe) {
  const contrats = graphe.declarations.filter((d) => d.declarePar === container.id);
  const bloc = [
    `<a id="${ancre(container.id)}"></a>`,
    '',
    `## ${container.emoji} ${container.nom}`,
    '',
    container.intention,
    '',
    container.implemente
      ? `${container.modules.length} modules — [\`${container.dossier}/CLAUDE.md\`](../../${container.dossier}/CLAUDE.md)`
      : `⚠️ Déclaré mais pas implémenté — [\`${container.dossier}/CLAUDE.md\`](../../${container.dossier}/CLAUDE.md)`,
    '',
  ];
  if (container.implemente) bloc.push(detail(container, graphe), '');
  if (contrats.length) {
    bloc.push('| Sens | Pair | Charge |', '|---|---|---|');
    for (const c of contrats) {
      const pair = c.verbe === 'reçoit' ? c.fournisseur : c.consommateur;
      bloc.push(`| ${c.verbe} | ${pair || '_tous_'} | ${cellule(c.charge)} |`);
    }
    bloc.push('');
  }
  return bloc.join('\n');
}

/** @param {Object} graphe le JSON intermédiaire @returns {string} markdown */
export function emettreMarkdown(graphe) {
  const r = graphe.resume;
  return [
    '# Architecture — vue générée',
    '',
    '> Généré par `node coding/graph/construire.mjs`. Ne pas éditer à la main.',
    '',
    `${r.implementes}/${r.containers} containers implémentés · ${r.modules} modules · `
      + `${r.liensCables} liens câblés · ${r.contratsDeclares} contrats déclarés · `
      + `${r.featuresAvecViz}/${r.features} features observables · `
      + `**${r.divergences} divergences**`,
    '',
    '**Containers :** '
      + graphe.containers.map((c) => `[${c.emoji} ${c.nom}](#${ancre(c.id)})`).join(' · '),
    '',
    '## Panorama — qui appelle quel expose',
    '',
    'Sens de l\'**appel**. Aucun container n\'en importe un autre : ces arêtes',
    'viennent toutes des littéraux d\'injection de `src/main.js`.',
    '',
    LEGENDE.map((l) => `- ${l}`).join('\n'),
    '',
    panoramaAppels(graphe),
    '',
    '## Panorama — flux de données',
    '',
    'Sens du **flux**, pas de l\'appel : une vue se tire, donc l\'appel remonte',
    'le flux. C\'est le sens que décrivent les sections « Reçoit / Fournit ».',
    '',
    panoramaFlux(graphe),
    '',
    '## La boucle',
    '',
    boucle(graphe),
    '',
    sectionMachines(graphe),
    '## Observables — chaque feature a-t-elle une viz ?',
    '',
    'Déclaré dans les tableaux `## Observables` des CLAUDE.md ; les `calque`',
    'sont vérifiés contre `calques/` et les tags `@viz` ; `inspecteur` et `ui`',
    'sont déclaratifs (contrôle runtime à venir). `—` = à faire.',
    '',
    tableauObservables(graphe),
    '',
    '## Divergences déclaré / réel',
    '',
    tableauDivergences(graphe),
    '',
    ...graphe.containers.map((c) => sectionContainer(c, graphe)),
  ].join('\n');
}
