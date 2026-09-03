/**
 * 🧠 Brains / Machine — le runtime des machines à états DÉCLARATIVES.
 * La machine est une DONNÉE ({etats, transitions}), pas du flux de contrôle :
 * c'est ce qui la rend introspectable (inspecteur), dessinable (graphe
 * généré) et justifiable — chaque transition porte un `libelle` humain,
 * OBLIGATOIRE (une transition sans justification est un bug), et le journal
 * garde les dernières bascules avec leur raison.
 *
 * Règles d'exécution (déterminisme et traces lisibles) :
 * - les transitions s'évaluent DANS L'ORDRE de déclaration ;
 * - la première garde vraie gagne ; AU PLUS UNE transition par décision ;
 * - une transition dont la destination COUVRE l'état courant est ignorée
 *   (« aller à obeir » quand je suis déjà dans obeir.cherche = no-op —
 *   un super-état ne réinitialise pas sa sous-machine) ;
 * - `de: '*'` = de partout ; `de`/`vers` peuvent viser un super-état
 *   (l'arrivée descend sur son `initial`) ; profondeur max : 2 niveaux.
 * - les gardes sont PURES et ne lisent que le contexte (Représentation…) —
 *   jamais de rng : la raison affichée est LA condition qui a déclenché.
 */

/** Feuille d'arrivée d'un chemin d'état ('desoeuvre' → 'desoeuvre.flane'). */
function feuilleDe(definition, chemin) {
  const [haut, bas] = chemin.split('.');
  const etat = definition.etats[haut];
  if (bas) return chemin;
  return etat.sousEtats ? `${haut}.${etat.initial}` : haut;
}

/** L'état `chemin` couvre-t-il la feuille courante ? ('desoeuvre' couvre 'desoeuvre.discute') */
const couvre = (chemin, feuille) => chemin === '*' || feuille === chemin || feuille.startsWith(`${chemin}.`);

/** Valide la définition à la création : un défaut ici est un bug, on jette. */
function valider({ definition, gardes, actions }) {
  const chemins = new Set();
  for (const [nom, etat] of Object.entries(definition.etats)) {
    chemins.add(nom);
    if (etat.sousEtats) {
      if (!etat.initial || !etat.sousEtats[etat.initial]) {
        throw new Error(`machine : super-état '${nom}' sans initial valide`);
      }
      for (const [sousNom, sous] of Object.entries(etat.sousEtats)) {
        chemins.add(`${nom}.${sousNom}`);
        if (sous.sousEtats) throw new Error(`machine : '${nom}.${sousNom}' — profondeur max 2 niveaux`);
        if (sous.agir && !actions[sous.agir]) throw new Error(`machine : action inconnue '${sous.agir}'`);
      }
    }
    if (etat.agir && !actions[etat.agir]) throw new Error(`machine : action inconnue '${etat.agir}'`);
  }
  for (const t of definition.transitions) {
    if (!t.libelle) throw new Error(`machine : transition ${t.de} → ${t.vers} SANS libellé — la justification est obligatoire`);
    if (!gardes[t.quand]) throw new Error(`machine : garde inconnue '${t.quand}' (${t.de} → ${t.vers})`);
    if (t.de !== '*' && !chemins.has(t.de)) throw new Error(`machine : état de départ inconnu '${t.de}'`);
    if (!chemins.has(t.vers)) throw new Error(`machine : état d'arrivée inconnu '${t.vers}'`);
  }
  if (!chemins.has(definition.initial) && !chemins.has(definition.initial.split('.')[0])) {
    throw new Error(`machine : initial inconnu '${definition.initial}'`);
  }
}

/**
 * @param {Object} deps
 * @param {{initial: string, etats: Object, transitions: Array}} deps.definition
 * @param {Object<string, (ctx) => boolean>} deps.gardes — pures, par nom
 * @param {Object<string, (ctx) => {intention, objectifHumain}>} deps.actions — par nom
 * @param {number} [deps.tailleJournal]
 */
export function creerMachine({ definition, gardes, actions, tailleJournal = 8 }) {
  valider({ definition, gardes, actions });

  let feuille = feuilleDe(definition, definition.initial);
  const journal = []; // plus récent en tête : {de, vers, libelle, ilYaS}
  // le VÉCU cumulé — de quoi répondre à « où passes-tu ton temps ? » :
  // secondes par feuille, et nombre de bascules par transition déclarée
  const tempsParEtat = new Map();
  const bascules = new Map(); // clé "de → vers" (la déclaration, pas la feuille)

  const actionDe = (chemin) => {
    const [haut, bas] = chemin.split('.');
    const etat = bas ? definition.etats[haut].sousEtats[bas] : definition.etats[haut];
    return etat.agir ? actions[etat.agir] : null;
  };

  return {
    /** Le journal vieillit, le vécu s'accumule. @param {number} dt */
    vieillir(dt) {
      for (const entree of journal) entree.ilYaS += dt;
      tempsParEtat.set(feuille, (tempsParEtat.get(feuille) ?? 0) + dt);
    },

    /**
     * Une décision : au plus une transition (première garde vraie, dans
     * l'ordre), puis l'action de l'état courant.
     * @param {Object} ctx — passé aux gardes et à l'action
     * @returns {{intention, objectifHumain} | null}
     */
    decider(ctx) {
      for (const t of definition.transitions) {
        if (!couvre(t.de, feuille)) continue;
        if (couvre(t.vers, feuille)) continue; // destination déjà occupée : no-op
        if (!gardes[t.quand](ctx)) continue;
        const arrivee = feuilleDe(definition, t.vers);
        const cle = `${t.de} → ${t.vers}`;
        bascules.set(cle, (bascules.get(cle) ?? 0) + 1);
        journal.unshift({ de: feuille, vers: arrivee, libelle: t.libelle, ilYaS: 0 });
        if (journal.length > tailleJournal) journal.pop();
        feuille = arrivee;
        break;
      }
      const agir = actionDe(feuille);
      return agir ? agir(ctx) : null;
    },

    /** @returns {string} la feuille courante, ex. 'desoeuvre.discute' */
    etat() {
      return feuille;
    },

    /**
     * SE RELIRE — LE champ dont l'oubli est invisible au chargement et
     * catastrophique a la seconde d'apres : sans lui, un homme recharge en
     * pleine charge repart a l'etat initial, c'est-a-dire a flaner.
     * Le journal et le vecu ne se restaurent pas : de l'introspection.
     * Une feuille inconnue (definition changee entre deux versions) retombe
     * sur l'initial, et le DIT — un chargement silencieusement faux est pire
     * qu'un chargement degrade.
     * @param {string} f
     */
    restaurer(f) {
      if (typeof f !== 'string' || !f) return;
      const [haut, bas] = f.split('.');
      const etat = definition.etats[haut];
      const connu = !!etat && (!bas || !!etat.sousEtats?.[bas]);
      if (!connu) {
        console.warn(`machine : feuille inconnue '${f}' au chargement — retour a '${definition.initial}'`);
        feuille = feuilleDe(definition, definition.initial);
        return;
      }
      feuille = feuilleDe(definition, f);
    },

    /**
     * Pour introspect() : la structure ET le vécu — de quoi dessiner le
     * graphe et répondre à « pourquoi tu fais ça ? ».
     */
    description() {
      return {
        etat: feuille,
        etats: Object.entries(definition.etats).map(([nom, e]) => ({
          nom,
          reserve: !e.agir && !e.sousEtats,
          sousEtats: e.sousEtats ? Object.keys(e.sousEtats) : null,
        })),
        transitions: definition.transitions.map(({ de, vers, libelle }) => ({ de, vers, libelle })),
        journal: journal.map((e) => ({ ...e })),
        vecu: {
          tempsParEtat: Object.fromEntries(tempsParEtat),
          bascules: Object.fromEntries(bascules),
        },
      };
    },
  };
}
