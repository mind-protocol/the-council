/**
 * Lecteur de main.js — produit le graphe RÉEL (le câblage).
 *
 * Aucun container n'en importe un autre : les arêtes inter-container
 * n'existent QUE dans les littéraux d'injection du bootstrap. Un analyseur
 * d'imports rendrait ici huit îlots isolés.
 *
 * Convention de sens : `appelant` est le container construit (celui qui reçoit
 * la référence), `appele` celui dont l'expose est appelé. Le sens du FLUX de
 * données s'en déduit via la nature (une vue se tire, une commande se pousse).
 */

import { readFileSync } from 'node:fs';

/** Fin d'une chaîne ou d'un commentaire commençant en `i`, sinon `i`. */
function sauter(texte, i) {
  const c = texte[i];
  if (c === "'" || c === '"' || c === '`') {
    for (let j = i + 1; j < texte.length; j++) {
      if (texte[j] === '\\') j++;
      else if (texte[j] === c) return j + 1;
    }
    return texte.length;
  }
  if (c === '/' && texte[i + 1] === '/') {
    const fin = texte.indexOf('\n', i);
    return fin === -1 ? texte.length : fin;
  }
  if (c === '/' && texte[i + 1] === '*') {
    const fin = texte.indexOf('*/', i);
    return fin === -1 ? texte.length : fin + 2;
  }
  return i;
}

/** Contenu équilibré à partir du délimiteur ouvrant en `iOuvrante`. */
function extraire(texte, iOuvrante, ouvrant, fermant) {
  let profondeur = 0;
  for (let i = iOuvrante; i < texte.length; i++) {
    const saut = sauter(texte, i);
    if (saut !== i) { i = saut - 1; continue; }
    if (texte[i] === ouvrant) profondeur++;
    else if (texte[i] === fermant && --profondeur === 0) {
      return { contenu: texte.slice(iOuvrante + 1, i), fin: i + 1 };
    }
  }
  return null;
}

/** Découpe sur les virgules de profondeur 0 (hors chaînes et commentaires). */
function decouperNiveau(texte) {
  const morceaux = [];
  let profondeur = 0;
  let debut = 0;
  for (let i = 0; i < texte.length; i++) {
    const saut = sauter(texte, i);
    if (saut !== i) { i = saut - 1; continue; }
    const c = texte[i];
    if ('([{'.includes(c)) profondeur++;
    else if (')]}'.includes(c)) profondeur--;
    else if (c === ',' && profondeur === 0) {
      morceaux.push(texte.slice(debut, i));
      debut = i + 1;
    }
  }
  morceaux.push(texte.slice(debut));
  return morceaux;
}

/**
 * Propriétés d'un littéral objet. Un commentaire de fin de ligne tombe APRÈS
 * la virgule, donc syntaxiquement en tête de la propriété suivante : on le
 * réattribue à celle qu'il commente réellement.
 */
function proprietes(texteObjet) {
  const bruts = decouperNiveau(texteObjet).map((brut) => {
    let reste = brut;
    const amont = [];
    for (;;) {
      const m = reste.match(/^\s*\/\/([^\n]*)\n/);
      if (!m) break;
      amont.push(m[1].trim());
      reste = reste.slice(m[0].length);
    }
    const queue = reste.match(/\/\/([^\n]*)\s*$/);
    const aval = queue ? queue[1].trim() : null;
    if (queue) reste = reste.slice(0, queue.index);
    return { reste: reste.trim(), amont, aval };
  });

  const sortie = [];
  bruts.forEach((p, i) => {
    if (!p.reste) return;
    const suivant = bruts[i + 1];
    const sep = p.reste.indexOf(':');
    sortie.push({
      nom: sep === -1 ? p.reste : p.reste.slice(0, sep).trim(),
      valeur: sep === -1 ? p.reste : p.reste.slice(sep + 1).trim(),
      commentaire: p.aval || (suivant && suivant.amont.length ? suivant.amont.join(' ') : null),
    });
  });
  return sortie;
}

/** Références `variableContainer.membre…` présentes dans un texte. */
function referencesContainer(texte, varsContainer) {
  const vues = new Map();
  for (const m of texte.matchAll(/\b([A-Za-z_$][\w$]*)((?:\.[A-Za-z_$][\w$]*)+)/g)) {
    const container = varsContainer.get(m[1]);
    if (container && !vues.has(m[0])) {
      vues.set(m[0], { container, chemin: m[0], membre: m[2].slice(1) });
    }
  }
  return [...vues.values()];
}

/** Le littéral objet passé en argument, s'il y en a un. */
function objetArgument(args) {
  const i = args.indexOf('{');
  if (i === -1) return '';
  const bloc = extraire(args, i, '{', '}');
  return bloc ? bloc.contenu : '';
}

function fabriquesParContainer(texte, idsContainers) {
  const fabriques = new Map();
  for (const m of texte.matchAll(/import\s*\{([^}]*)\}\s*from\s*'\.\/([^']+)'/g)) {
    const segment = m[2].split('/')[0];
    if (!idsContainers.has(segment)) continue;
    for (const nom of m[1].split(',').map((n) => n.trim()).filter(Boolean)) {
      fabriques.set(nom, segment);
    }
  }
  return fabriques;
}

function constructionsDe(texte, fabriques) {
  const constructions = [];
  for (const m of texte.matchAll(/const\s+([A-Za-z_$][\w$]*)\s*=\s*([A-Za-z_$][\w$]*)\s*\(/g)) {
    const container = fabriques.get(m[2]);
    if (!container) continue;
    const args = extraire(texte, m.index + m[0].length - 1, '(', ')');
    constructions.push({
      variable: m[1],
      container,
      objet: args ? objetArgument(args.contenu) : '',
      debut: m.index,
      fin: args ? args.fin : m.index + m[0].length,
    });
  }
  return constructions;
}

/** Fonctions fléchées locales : `const spawnHomme = (…) => { … }`. */
function aidesLocales(texte) {
  const aides = new Map();
  for (const m of texte.matchAll(/const\s+([A-Za-z_$][\w$]*)\s*=\s*\(/g)) {
    const par = extraire(texte, m.index + m[0].length - 1, '(', ')');
    if (!par) continue;
    const fleche = texte.slice(par.fin).match(/^\s*=>\s*\{/);
    if (!fleche) continue;
    const corps = extraire(texte, par.fin + fleche[0].length - 1, '{', '}');
    if (corps) aides.set(m[1], { corps: corps.contenu, debut: m.index, fin: corps.fin });
  }
  return aides;
}

/** L'ordre des phases est une décision d'archi : on l'extrait tel quel. */
function lirePhases(objet, varsContainer) {
  const prop = proprietes(objet).find((p) => p.nom === 'phases');
  if (!prop) return [];
  const bloc = extraire(prop.valeur, prop.valeur.indexOf('['), '[', ']');
  if (!bloc) return [];

  return decouperNiveau(bloc.contenu)
    .map((element) => {
      const nom = element.match(/nom\s*:\s*'([^']+)'/);
      const [ref] = referencesContainer(element, varsContainer);
      return nom && ref ? { nom: nom[1], container: ref.container, appel: ref.chemin } : null;
    })
    .filter(Boolean);
}

const NATURES_POUSSEES = new Set(['commande', 'puits', 'cadence']);

/** Une vue se tire (le fournisseur est l'appelé) ; le reste se pousse. */
function fluxDe(lien) {
  return NATURES_POUSSEES.has(lien.nature)
    ? { fournisseur: lien.appelant, consommateur: lien.appele }
    : { fournisseur: lien.appele, consommateur: lien.appelant };
}

/**
 * @param {string} cheminMain
 * @param {Array} containers
 * @param {Map<string, Map>} naturesParContainer — annotations des expose.js
 */
export function lireBootstrap(cheminMain, containers, naturesParContainer) {
  const texte = readFileSync(cheminMain, 'utf8');
  const ids = new Set(containers.map((c) => c.id));
  const emojis = new Map(containers.filter((c) => c.emoji).map((c) => [c.emoji, c.id]));

  const fabriques = fabriquesParContainer(texte, ids);
  const constructions = constructionsDe(texte, fabriques);
  const aides = aidesLocales(texte);
  const varsContainer = new Map(constructions.map((c) => [c.variable, c.container]));

  const liens = [];
  const aidesUtilisees = new Set();

  for (const construction of constructions) {
    const natures = naturesParContainer.get(construction.container) || new Map();

    for (const prop of proprietes(construction.objet)) {
      const annotee = natures.get(prop.nom);
      const aide = aides.get(prop.valeur.trim());
      if (aide) aidesUtilisees.add(prop.valeur.trim());

      const nature = annotee ? annotee.nature : prop.nom === 'phases' ? 'cadence' : 'vue';
      const base = {
        appelant: construction.container,
        dep: prop.nom,
        nature,
        natureSource: annotee ? 'annotation' : 'defaut',
        annotation: annotee ? annotee.annotation : null,
        via: aide ? prop.valeur.trim() : null,
        source: 'src/main.js',
      };

      // Un puits vide : l'arête est câblée dans la signature, morte à l'exécution.
      if (/=>\s*\{\s*\}/.test(prop.valeur)) {
        const cible = [...emojis].find(([emoji]) => (prop.commentaire || '').includes(emoji));
        if (cible) {
          liens.push({ ...base, appele: cible[1], membres: [], etat: 'stub', note: prop.commentaire });
        }
        continue;
      }

      const refs = referencesContainer(aide ? aide.corps : prop.valeur, varsContainer);
      for (const container of new Set(refs.map((r) => r.container))) {
        if (container === construction.container) continue;
        liens.push({
          ...base,
          appele: container,
          membres: refs.filter((r) => r.container === container).map((r) => r.chemin),
          etat: 'cable',
          note: null,
        });
      }
    }
  }

  // Ce qui reste hors constructions et hors aides injectées : le bootstrap lui-même.
  let residu = texte;
  const masquer = ({ debut, fin }) => {
    residu = residu.slice(0, debut) + ' '.repeat(fin - debut) + residu.slice(fin);
  };
  constructions.forEach(masquer);
  for (const [nom, aide] of aides) if (aidesUtilisees.has(nom)) masquer(aide);
  residu = residu.replace(/^import[\s\S]*?;$/gm, '');

  for (const ref of referencesContainer(residu, varsContainer)) {
    liens.push({
      appelant: 'bootstrap',
      appele: ref.container,
      dep: ref.membre,
      membres: [ref.chemin],
      nature: 'cadence',
      natureSource: 'defaut',
      annotation: null,
      via: null,
      etat: 'cable',
      note: null,
      source: 'src/main.js',
    });
  }

  const orchestration = constructions.find((c) => c.container === 'orchestration');
  return {
    liens: liens.map((l) => ({ ...l, ...fluxDe(l) })),
    boucle: orchestration ? lirePhases(orchestration.objet, varsContainer) : [],
  };
}
