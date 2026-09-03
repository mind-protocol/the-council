/**
 * 🧠 Paroles — la SURCOUCHE DE FLAVOR : un homme parle. Trois familles de
 * déclencheurs, aucune mécanique (personne n'écoute — encore) :
 *   1. les BASCULES de machine (rupture, assaut, curée…) — le brain signale ;
 *   2. les SEUILS de jauges (peur, souffle, carquois), avec hystérésis :
 *      un franchissement = une réplique, réarmée quand la jauge revient ;
 *   3. le BAVARDAGE désœuvré (discussion, flânerie) et les DÉFIS du
 *      face-à-face, à cadence propre ~N.
 * La parole sort par le puits `dire` (🖥️ bulles aujourd'hui, 📯 demain) —
 * absent en headless : les tirages rng ont lieu quand même (déterminisme :
 * le déroulé ne dépend pas de la présence d'une fenêtre).
 *
 * RNG DÉDIÉ (décision actée, mesurée) : le flavor tire sur SON flux, seedé
 * de l'id de l'homme — jamais sur le rng partagé de la sim. Preuve à l'appui :
 * branché sur le rng du brain, ses tirages décalaient le déroulé (le refus
 * vécu de La Conroi passait de 57 ticks à 0). Ajouter une vanne au répertoire
 * ne doit JAMAIS changer l'issue d'une bataille — c'est le sens de
 * « surcouche ». Revers assumé : deux scénarios aux mêmes ids donnent les
 * mêmes séquences de vannes (le seed du scénario n'entre pas ici).
 */

import { creerRng } from '../infra/rng.js';
import { choisir } from './langage/repliques.js';

// une bascule de machine → une clé du répertoire (évaluées dans l'ordre,
// la première qui matche gagne — même discipline que les transitions)
const EVENEMENTS = [
  { cle: 'rupture', proba: 0.1, force: true, quand: (de, vers) => vers === 'fuir' },
  { cle: 'soulagement', proba: 0.07, quand: (de) => de === 'fuir' },
  { cle: 'curee', proba: 0.08, quand: (de, vers) => vers === 'tuer.poursuit' },
  { cle: 'assaut', proba: 0.08, quand: (de, vers) => vers === 'tuer.engage' },
  { cle: 'charge', proba: 0.07, quand: (de, vers) => vers === 'obeir.charge' },
  { cle: 'alarme', proba: 0.05, quand: (de, vers) => vers === 'tuer.pret' && !de.startsWith('tuer') },
];

// un état bavard (feuille fine) → sa clé et sa cadence
const BAVARDAGES = {
  discute: { cle: 'bavardage', cadence: 'bavardage' },
  flane: { cle: 'flanerie', cadence: 'bavardage' },
  pret: { cle: 'defi', cadence: 'defi' },
};

/**
 * @param {Object} deps
 * @param {number} deps.graine — l'id de l'homme : seed du flux rng DÉDIÉ
 * @param {(texte: string, dureeS: number) => void} [deps.dire] — le puits (absent en headless)
 * @param {Object} deps.params — PARAMS (paroles, moral, combat)
 */
export function creerParoles({ graine, dire, params }) {
  // le flux dédié : brassage du seed (nombre d'or) pour décorréler les ids voisins
  const rng = creerRng(Math.imul((graine ?? 0) + 1, 0x9e3779b1) >>> 0);
  const p = params.paroles;
  const tirerPeriode = ({ moyennePeriodeS, ecartTypeS }) =>
    Math.max(2, rng.normale(moyennePeriodeS, ecartTypeS));

  let silenceRestant = rng.uniforme() * p.silenceMinS; // échelonnage au spawn
  let verifRestant = rng.uniforme() * p.verifJaugesS;
  let bavardRestant = tirerPeriode(p.bavardage);
  // l'hystérésis des seuils : dit une fois, réarmé au retour de la jauge
  let peurDite = false;
  let souffleDit = false;
  let flechesAvant = null;
  const dernieres = []; // ring des 3 dernières répliques (introspection)

  /** @returns {boolean} la réplique est-elle SORTIE (le cooldown peut l'avaler) */
  const prononcer = (cle, force = false) => {
    if (!force && silenceRestant > 0) return false;
    const texte = choisir(rng, cle);
    if (!texte) return false;
    dire?.(texte, p.dureeBulleS);
    silenceRestant = p.silenceMinS;
    dernieres.unshift(texte);
    if (dernieres.length > 3) dernieres.pop();
    return true;
  };

  return {
    /**
     * Une bascule de machine vient d'avoir lieu (appelé par le brain au
     * moment exact — pas de guet de journal). Toutes ne font pas crier :
     * proba par événement, tirée au flux dédié.
     * @param {string} de — feuille de départ @param {string} vers — feuille d'arrivée
     */
    evenement(de, vers) {
      const e = EVENEMENTS.find((x) => x.quand(de, vers));
      if (!e) return;
      if (rng.uniforme() > e.proba) return;
      prononcer(e.cle, e.force ?? false);
    },

    /**
     * Le temps passe : cooldowns, vérif des seuils (~1 Hz), bavardage.
     * @param {number} dt
     * @param {{etat: string, jauges: () => {peur, souffle, aArc, fleches}}} faits
     *   — jauges est une CLOSURE : évaluée à la cadence de vérif, pas par tick
     */
    tick(dt, { etat, jauges }) {
      silenceRestant -= dt;
      verifRestant -= dt;
      bavardRestant -= dt;

      if (verifRestant <= 0) {
        verifRestant = p.verifJaugesS;
        const j = jauges();
        const m = params.moral;
        const seuilPeur = (m.seuilRassure + m.seuilRompt) / 2;
        // la proba ne se tire qu'une fois le silence levé (sinon les
        // tentatives pré-cooldown brûlent le one-shot) : la plupart gardent
        // ça pour eux — le flag se pose et on ne retente pas
        if (!peurDite && j.peur > seuilPeur && silenceRestant <= 0) {
          peurDite = rng.uniforme() > p.probaSeuil || prononcer('peurMonte');
        } else if (peurDite && j.peur < m.seuilRassure) peurDite = false;
        if (!souffleDit && j.souffle < params.combat.souffleBas && silenceRestant <= 0) {
          souffleDit = rng.uniforme() > p.probaSeuil || prononcer('souffleBas');
        } else if (souffleDit && j.souffle > params.combat.souffleEngage) souffleDit = false;
        // le carquois : la TRANSITION vers zéro (pas l'état — un homme sans
        // arc, ou parti à vide, ne crie pas)
        if (j.aArc && flechesAvant > 0 && j.fleches === 0 && rng.uniforme() < p.probaSeuil) {
          prononcer('carquoisVide', true);
        }
        flechesAvant = j.aArc ? j.fleches : null;
      }

      if (bavardRestant <= 0) {
        const b = BAVARDAGES[etat.split('.').pop()];
        bavardRestant = tirerPeriode(p[b?.cadence ?? 'bavardage']);
        if (b) prononcer(b.cle);
      }
    },

    /** Les dernières répliques, plus récente en tête (inspecteur 🖥️). */
    introspect() {
      return [...dernieres];
    },
  };
}
