/**
 * 🧠 Brains / Soldat — le combattant. La state machine OBJECTIF vit en
 * DONNÉE dans machine.js (obeir / desoeuvre{flâne, rejoint, s'écarte,
 * discute} + tuer/proteger/fuir réservés) ; le brain la cadence,
 * l'introspecte, et relaie le debug de formation.
 * Interface commune : decide() + introspect().
 */

import { creerCadence } from '../cadence.js';
import { creerMachine } from '../machine.js';
import { creerSeMettreEnFormation } from '../../competences/se-mettre-en-formation.js';
import { creerChercher, PRIORITES_TROUPIER, PRIORITES_COMMANDANT } from '../../competences/chercher.js';
import { decrireTas } from '../../langage/decrire.js';
import { pressionDePeur } from '../../competences/moral.js';
import { creerParoles } from '../../paroles.js';
import { MACHINE_SOLDAT, gardes, actions } from './machine.js';

/**
 * @param {Object} deps
 * @param {ReturnType<import('../../../infra/rng.js').creerRng>} deps.rng
 * @param {ReturnType<import('../../representation.js').creerRepresentation>} deps.representation
 * @param {{x, y, largeur, hauteur}} deps.zone
 * @param {{ordreDrill: number[], forme: Object}} deps.drill — savoir mémorisé
 * @param {Object} deps.params
 * @param {(id: number) => number} [deps.souffleDe] — vue ❤️ (ressenti sigmoïde)
 * @param {(id: number) => Object} [deps.armeDe] — vue ❤️ (je connais MA portée)
 * @param {(texte: string, dureeS: number) => void} [deps.dire] — le puits de
 *   parole (flavor) : bulles 🖥️ aujourd'hui, Transmission 📯 demain
 */
export function creerSoldat({ rng, representation, zone, drill, params, souffleDe, blessuresDe, armeDe, arcTirDe, flechesDe, montureDe, dire }) {
  const cadence = creerCadence({ rng, ...params.cadence });
  const formation = creerSeMettreEnFormation({ representation, drill, params });
  // le ROLE ne change que la liste de priorites du chercheur
  const estCommandant = drill.ordreDrill[0] === representation.monId;
  const chercheur = creerChercher({
    representation,
    rng,
    zone,
    params,
    priorites: estCommandant ? PRIORITES_COMMANDANT : PRIORITES_TROUPIER,
  });
  const machine = creerMachine({ definition: MACHINE_SOLDAT, gardes, actions });
  const ctx = {
    representation,
    rng,
    zone,
    params,
    formation,
    chercheur,
    drill, // les gardes résolvent avec le MÊME savoir que la compétence
    souffle: () => souffleDe?.(representation.monId) ?? 1, // ressenti ❤️ (readiness, passe 3)
    arc: () => arcTirDe?.(representation.monId) ?? null,
    fleches: () => flechesDe?.(representation.monId) ?? 0,
    arme: () => armeDe?.(representation.monId) ?? null, // je connais mon arme (❤️)
    monture: () => montureDe?.(representation.monId) ?? null, // je sais si je suis en selle (🌍)
    lireTas: (r) => r.tasCru('escouade') ?? r.tasCru('unite'),
  };
  const paroles = creerParoles({ graine: representation.monId, dire, params });
  // les jauges que la parole surveille (~1 Hz) : le MÊME ressenti que les gardes
  const jaugesParole = () => {
    const souffle = ctx.souffle();
    return {
      peur: pressionDePeur(representation, params, souffle),
      souffle,
      aArc: !!ctx.arc(),
      fleches: ctx.fleches(),
    };
  };
  let dernier = { objectifHumain: 'flâner', cible: null, debugFormation: null };

  return {

    // ── SE RELIRE (docs/sauvegarde.md) : la FEUILLE de la machine avant tout.
    etat() {
      return { role: 'soldat', machine: machine.etat(), dernier };
    },

    restaurer(d = {}) {
      machine.restaurer(d.machine);
      if (d.dernier) dernier = { ...d.dernier };
    },
    decide(dt) {
      machine.vieillir(dt);
      let r = null;
      if (cadence.echue(dt)) {
        const avant = machine.etat();
        r = machine.decider(ctx);
        // une bascule vient d'avoir lieu : la parole flavor peut la crier
        if (machine.etat() !== avant) paroles.evenement(avant, machine.etat());
        if (r) dernier = { debugFormation: null, ...r };
      }
      paroles.tick(dt, { etat: machine.etat(), jauges: jaugesParole });
      return r?.intention ?? null;
    },

    introspect() {
      const escouade = representation.tasCru('escouade');
      const recu = representation.ordre();
      const souffle = souffleDe?.(representation.monId) ?? 1;
      const m = params.moral;
      return {
        brain: 'soldat',
        etat: machine.etat(),
        objectifHumain: dernier.objectifHumain,
        machine: machine.description(),
        // les JAUGES : le ressenti et la pression, avec leurs seuils — ce que
        // les gardes lisent, montré tel quel (l'inspecteur affiche, point)
        jauges: [
          {
            nom: 'souffle',
            valeur: souffle,
            max: 1,
            seuils: [params.combat.souffleBas, params.combat.souffleEngage],
            sens: 'basMauvais',
          },
          {
            nom: 'moral (pression de peur)',
            valeur: pressionDePeur(representation, params, souffle),
            max: m.seuilRompt * 1.3,
            seuils: [m.seuilRassure, m.seuilRompt],
            sens: 'hautMauvais',
          },
        ],
        details: {
          ordre: recu ? `${recu.ordre.verbe} (de ${representation.nomDe(recu.emetteur)})` : 'aucun',
          escouadeCrue: escouade ? decrireTas(escouade) : 'nulle part',
          cible: dernier.cible,
          souffle: souffleDe?.(representation.monId),
          blessures: blessuresDe?.(representation.monId),
          ...(arcTirDe?.(representation.monId) ? { fleches: flechesDe?.(representation.monId) } : {}),
          dernieresParoles: paroles.introspect(),
          prochaineDecisionDansS: cadence.restant(),
        },
      };
    },

    /** Pour le calque formation (🖥️). */
    formationDebug() {
      return dernier.debugFormation;
    },

    /**
     * La POSTURE voulue — un GESTE physique (lance levée), lisible par
     * quiconque regarde : c'est le canal de la readiness. Émise par la
     * Cognition vers 🏃 puis écrite par ⚙️.
     */
    postureCourante() {
      const f = machine.etat();
      if (f === 'fuir') return 'fuit'; // la déroute se VOIT — c'est la contagion
      return f === 'tuer.pret' || f === 'tuer.engage' || f === 'tuer.tire' ? 'pret' : 'repos';
    },

    /** Condition fine pour l'orientation (🧠) : obeir | discute | rejoint | … */
    etatCourant() {
      return machine.etat().split('.').pop();
    },
  };
}
