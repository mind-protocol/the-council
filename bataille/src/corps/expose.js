/**
 * ❤️ Corps — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Équipement (lance par défaut) + SOUFFLE (réserve dépensée par les coûts
 * des Actes 🏃, ressenti sigmoïde lu par la Décision 🧠). Le Corps constate,
 * il ne décide rien. La phase physiologie est SA phase du pipeline.
 */

import { creerEquipement } from './equipement.js';
import { creerSouffle } from './souffle.js';
import { creerBlessures } from './blessures.js';
import { creerCarquois } from './carquois.js';
import { OISEAUX } from './oiseaux.js';

/** @param {{souffle: Object}} params */
/** La cle du catalogue pour un profil deja monte (les vieux spawns n'en portent pas). */
const cleOiseau = (profil) => Object.keys(OISEAUX).find((k) => OISEAUX[k] === profil) ?? null;

export function creerCorps({ params }) {
  const equipement = creerEquipement();
  const souffle = creerSouffle(params.souffle);
  const blessures = creerBlessures(params.sante);
  const carquois = creerCarquois();
  /** @type {Map<number, Object>} — idCorps → l'entrée du catalogue OISEAUX */
  const oiseaux = new Map();

  return {
    /**
     * Au spawn (bootstrap) : le paquetage du scénario (lance par défaut),
     * souffle frais. @param {number} idCorps
     * @param {{arme?, bouclier?, arc?, fleches?, oiseau?: string}} [paquetage]
     *   — `oiseau` : la clé du catalogue (un oiseau PORTE son profil)
     */
    enregistrer(idCorps, paquetage) {
      equipement.enregistrer(idCorps, paquetage);
      souffle.enregistrer(idCorps);
      if (paquetage?.arc) carquois.enregistrer(idCorps, paquetage.fleches ?? 24); // une botte
      if (paquetage?.oiseau) {
        if (!OISEAUX[paquetage.oiseau]) throw new Error(`corps : oiseau inconnu '${paquetage.oiseau}'`);
        oiseaux.set(idCorps, OISEAUX[paquetage.oiseau]);
      }
    },

    // ── SE RELIRE (docs/sauvegarde.md) ────────────────────────────────────
    // L'usure ne se redevine pas : ce qu'un homme a encaisse, souffle et tire
    // est de la matiere. L oiseau se sauve par sa CLE de catalogue, jamais
    // par son profil — le profil est du parametre, il vit dans le code.

    /** @returns {{blessures, souffle, equipement, carquois, oiseaux}} */
    etat() {
      return {
        blessures: blessures.etat(),
        souffle: souffle.etat(),
        equipement: equipement.etat(),
        carquois: carquois.etat(),
        oiseaux: [...oiseaux.entries()].map(([id, o]) => [id, o.cle ?? cleOiseau(o)]),
      };
    },

    restaurer({ blessures: bl, souffle: so, equipement: eq, carquois: ca, oiseaux: oi = [] } = {}) {
      blessures.restaurer(bl);
      souffle.restaurer(so);
      equipement.restaurer(eq);
      carquois.restaurer(ca);
      oiseaux.clear();
      for (const [id, cle] of dr) {
        if (!OISEAUX[cle]) throw new Error(`corps : oiseau inconnu '${cle}' au chargement`);
        oiseaux.set(Number(id), OISEAUX[cle]);
      }
    },

    /** PHASE physiologie : dépense de l'effort du tick, récupération. */
    phasePhysiologie(dt) {
      souffle.phase(dt);
    },

    // ── COMMANDES (puits des Actes 🏃) ──
    /** Coût d'effort du tick (effort-secondes : 1.0 = 1 s d'engagement plein). */
    coutEffort(idCorps, effortS) {
      souffle.depenser(idCorps, effortS);
    },

    /** Un coup a touché (l'Acte 🏃) — gravité x3 dans un dos en fuite. */
    subirCoup(idCorps, coup) {
      blessures.subir(idCorps, coup?.gravite ?? 1);
    },

    /**
     * Le TRAUMA d'un choc (⚙️) : l'à-coup subi (Δv, m/s) devient des coups —
     * continu au-delà d'un cran. Être percuté par un demi-tonne au galop
     * n'est pas une bousculade : c'est ce qui fait TUER la charge.
     */
    subirChoc(idCorps, deltaV) {
      const b = params.choc.blessure;
      const gravite = (deltaV - b.deltaVMin) * b.coupsParDeltaV;
      if (gravite > 0) blessures.subir(idCorps, gravite);
    },

    // ── VUES ──
    /** Pour 🖥️ Rendu : la silhouette (des chiffres, jamais des types). */
    equipementDe(idCorps) {
      return equipement.de(idCorps);
    },

    /** L'arme portée (catalogue) — pour 🏃 (l'acte), ⚙️ (la garde), 🧠 (le ressenti de sa portée). */
    armeDe(idCorps) {
      return equipement.armeDe(idCorps);
    },

    /** Le bouclier ({arcCouverture}|null) — pour 🏃 (la parade est jugée au coup). */
    bouclierDe(idCorps) {
      return equipement.bouclierDe(idCorps);
    },

    /** Le RESSENTI (sigmoïde) — pour la Décision 🧠 et l'inspecteur. */
    souffleDe(idCorps) {
      return souffle.ressentiDe(idCorps);
    },

    /** Coups reçus — 🖥️ (flash) et 🧠 (demain). */
    blessuresDe(idCorps) {
      return blessures.de(idCorps);
    },

    /** L'arc de tir porté, ou null. Pour 🧠 (gardes) et 🏃 (l'acte). */
    arcTirDe(idCorps) {
      return equipement.arcTirDe(idCorps);
    },

    /** Flèches restantes — pour 🧠 (gardes), 🖥️ (jauge). */
    flechesDe(idCorps) {
      return carquois.de(idCorps);
    },

    /** L'acte puise une flèche (🏃). false = carquois vide, l'acte refuse. */
    puiserFleche(idCorps) {
      return carquois.puiser(idCorps);
    },

    /** LA MORT EST UN CONSTAT de la physiologie. Pour 🧠 et 🏃. */
    estVivant(idCorps) {
      return blessures.estVivant(idCorps);
    },

    /** Capacité réduite par les blessures — pour 🏃 (Steering). */
    facteurVitesseDe(idCorps) {
      return blessures.facteurVitesse(idCorps);
    },

    /** Le profil d'oiseau porté (catalogue), ou null. Pour 🏃 (le vol),
     *  🧠 (un savoir sur soi) et 🖥️ (le plumage rendu). */
    oiseauDe(idCorps) {
      return oiseaux.get(idCorps) ?? null;
    },

    /** La réserve brute — viz/debug. */
    reserveDe(idCorps) {
      return souffle.reserveDe(idCorps);
    },
  };
}
