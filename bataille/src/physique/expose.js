/**
 * ⚙️ Physique — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Bête et incorruptible : vitesses désirées + lois → positions.
 * Déroulé d'un pas : répulsions → intégration provisoire → collisions →
 * écriture via appliquerIntegration (SEUL appelant de l'écrivain 1/2).
 */

import { calculerRepulsions, ajouterRepulsionGisants } from './forces/repulsions.js';
import { ajouterCoudeACoude } from './forces/coude-a-coude.js';
import { pairesProches } from './forces/paires.js';
import { ajouterGarde } from './forces/garde.js';
import { resoudreCollisions } from './collisions/resolution.js';
import { resoudreChocs } from './collisions/choc.js';
import { integrer } from './integration.js';
import { quiEntend as quiEntendAPortee } from './acoustique/portee-voix.js';

/**
 * @param {Object} deps — vues et commandes injectées au bootstrap
 * @param {() => Iterable<Object>} deps.corps — vue 🌍
 * @param {(pos, rayon) => Object[]} deps.obstaclesPres — vue 🌍
 * @param {(id, pos, vel) => void} deps.appliquerIntegration — commande 🌍 (écrivain 1/2)
 * @param {() => Iterable<{id, vel}>} deps.vitessesDesirees — vue 🏃
 * @param {() => Iterable<{id, etat}>} [deps.volsDesires] — vue 🏃 (l'état de
 *   vol réalisable des corps volants — déjà borné par le profil, écrit tel quel)
 * @param {() => Iterable<{id, cap}>} deps.orientationsDesirees — vue 🏃
 * @param {() => Iterable<{id, posture}>} deps.posturesDesirees — vue 🏃 (geste, écrit tel quel)
 * @param {(id: number) => number|null} [deps.montureDe] — vue 🌍 (l'attelage : qui est en selle)
 * @param {(id: number) => void} [deps.desatteler] — commande 🌍 (la selle se vide : monture morte)
 * @param {(id: number, deltaV: number) => void} [deps.subirChoc] — puits ❤️ (le trauma d'un à-coup — la physiologie décide de la gravité)
 * @param {(pos, rayon) => Array<{id}>} [deps.voisinsDans] — vue 🌍 (index spatial : l'acoustique demande qui est à portée)
 * @param {Object} deps.params
 */
export function creerPhysique({ corps, obstaclesPres, appliquerIntegration, vitessesDesirees, volsDesires, orientationsDesirees, posturesDesirees, armeDe, montureDe, desatteler, subirChoc, voisinsDans, params }) {
  // Dernier tick, COPIÉ — vue debug pour le calque forces (🖥️). La physique
  // reste incorruptible : la vue est en lecture, remplacée à chaque pas.
  let dernierTick = new Map();
  let debugDemande = false;
  let chocsDebug = [];
  /** @type {Map<number, number>} — id → secondes restantes à terre (RENVERSÉ) */
  const renverses = new Map();

  return {
    /** ACOUSTIQUE — les ids à portée de cette parole (locuteur compris). Lecture pure, hors phase.
     * @param {{x, y}} posLocuteur @param {{intensite?: 'murmure'|'parole'|'cri'}} [options] @returns {number[]} */
    quiEntend(posLocuteur, options = {}) {
      if (!voisinsDans) throw new Error('quiEntend : aucun index spatial injecte (voisinsDans)');
      return quiEntendAPortee(posLocuteur, options, voisinsDans, params);
    },

    /** PHASE physique : un pas complet de dt fixe. @param {number} dt */
    phasePhysique(dt) {
      // les GISANTS sont hors du jeu des forces et du mouvement — le cadavre
      // reste où il est tombé (V1 : traversable ; barricades de morts à venir)
      const vivants = [];
      const gisants = [];
      // ── L'ATTELAGE : le cavalier est PORTÉ — hors du jeu des forces et de
      // l'intégration, sa position est celle de sa monture (écrite en fin de
      // pas). Monture morte → la selle se vide, il retombe sur ses pieds. ──
      const portes = new Map(); // cavalierId → corps de la monture
      const parId = new Map();
      for (const c of corps()) parId.set(c.id, c);
      for (const c of corps()) {
        const idMonture = montureDe?.(c.id);
        if (idMonture == null) continue;
        const monture = parId.get(idMonture);
        if (!monture || monture.posture === 'gisant') {
          desatteler?.(c.id); // la monture est tombée — à pied
          continue;
        }
        if (c.posture === 'gisant') {
          desatteler?.(c.id); // le mort tombe de selle — le cheval continue seul
          continue;
        }
        portes.set(c.id, monture);
      }
      for (const c of corps()) {
        if (portes.has(c.id)) continue; // porté : ni forces ni collisions propres
        if (c.vol) continue; // en vol : l'air est vide — ni forces, ni collisions, ni garde
        if (c.posture !== 'gisant') {
          vivants.push(c);
        } else {
          gisants.push(c);
          if (c.vel.x !== 0 || c.vel.y !== 0) {
            // un corps qui vient de tomber s'arrête : dernière écriture, vel nulle
            appliquerIntegration(c.id, c.pos, { x: 0, y: 0 }, c.cap);
          }
        }
      }
      // LA GRILLE DU TICK : les paires à portée de force (la plus longue : la
      // garde, allonge max + marge) — le O(n²) des forces est levé
      const paires = pairesProches([...vivants, ...gisants], 5.5);
      const pairesVivants = paires.filter(([a, b]) => a.posture !== 'gisant' && b.posture !== 'gisant');
      const pairesMixtes = paires.filter(([a, b]) => (a.posture === 'gisant') !== (b.posture === 'gisant'));
      const pairesIds = pairesVivants.map(([a, b]) => [a.id, b.id]);
      const forces = calculerRepulsions(vivants, obstaclesPres, params, pairesVivants);
      ajouterRepulsionGisants(vivants, gisants, forces, params.repulsionGisants, pairesMixtes);
      // LE DEBUG NE SE PAIE QUE S'IL EST REGARDÉ : la copie des forces et le
      // bloc par corps (quatre objets par homme et par tick) ne se font que si
      // quelqu'un a lu forcesDebug() depuis le tick précédent (le calque)
      const avecDebug = debugDemande;
      debugDemande = false;
      const avantCoude = avecDebug ? new Map([...forces].map(([id, f]) => [id, { x: f.x, y: f.y }])) : null;
      ajouterCoudeACoude(vivants, forces, params.coudeACoude, pairesVivants);
      // la pointe adverse SE VOIT : la garde se dérive de l'arme de chacun (❤️)
      ajouterGarde(vivants, forces, armeDe, params.garde.margeAllonge, params.garde.intensite, pairesVivants);

      const desirees = new Map();
      for (const { id, vel } of vitessesDesirees()) desirees.set(id, vel);
      // le cavalier VEUT, la monture PORTE : sa vitesse désirée passe au corps
      // qui la réalise (V1 : la monture obéit toujours — le refus viendra)
      for (const [idCavalier, monture] of portes) {
        const v = desirees.get(idCavalier);
        if (v) desirees.set(monture.id, v);
        desirees.delete(idCavalier);
      }
      // ── les RENVERSÉS : à terre, la volonté ne marche pas — le corps
      // glisse (frein du sol) puis se relève quand le temps est purgé ──
      for (const [id, restant] of renverses) {
        const r = restant - dt;
        if (r <= 0) renverses.delete(id);
        else renverses.set(id, r);
        desirees.set(id, { x: 0, y: 0 });
      }
      const capsVoulus = new Map();
      // la consigne ENTIÈRE ({cap, vitesseRotation}) — l'intégration lit les deux
      for (const c of orientationsDesirees()) capsVoulus.set(c.id, c);
      const postures = new Map();
      if (posturesDesirees) for (const { id, posture } of posturesDesirees()) postures.set(id, posture);

      // intégration provisoire (rien n'est écrit)
      const provisoires = [];
      const vels = new Map();
      const caps = new Map();
      for (const c of vivants) {
        const r = integrer(c, desirees.get(c.id), forces.get(c.id), capsVoulus.get(c.id), dt, params);
        provisoires.push({ id: c.id, pos: r.pos, rayon: c.rayon, masse: c.masse });
        vels.set(c.id, r.vel);
        caps.set(c.id, r.cap);
      }

      // ── le CHOC : transfert de quantité de mouvement — la poussée de
      // masse. L'a-coup fort renverse (posture physique, écrite par ⚙️) ──
      const { velsCorrigees, renversements, chocs } = resoudreChocs(provisoires, vels, params.choc, pairesIds);
      for (const [id, v] of velsCorrigees) vels.set(id, v);
      for (const r of renversements) {
        renverses.set(r.id, Math.max(renverses.get(r.id) ?? 0, r.dureeS));
        // l'à-coup violent est un TRAUMA : la physiologie (❤️) juge la gravité
        subirChoc?.(r.id, r.deltaV);
      }
      // le sol freine la glissade d'un corps à terre (demi-vie brève)
      const frein = Math.pow(0.5, dt / params.choc.demiVieGlissadeS);
      for (const id of renverses.keys()) {
        const v = vels.get(id);
        if (v) vels.set(id, { x: v.x * frein, y: v.y * frein });
      }
      chocsDebug = chocs;

      // résolution dure, puis LA seule écriture du tick
      const corrigees = resoudreCollisions(provisoires, obstaclesPres, params, pairesIds);
      const cavalierDe = new Map([...portes].map(([idCav, m]) => [m.id, idCav])); // sans ça : n corps x m montures par tick
      const debug = new Map();
      for (const p of provisoires) {
        const pos = corrigees.get(p.id) ?? p.pos;
        // le renversement est un FAIT physique : il couvre le geste voulu —
        // sauf 'gisant' (la mort prime, elle ne se relève pas)
        let posture = postures.get(p.id);
        if (renverses.has(p.id) && posture !== 'gisant') posture = 'renverse';
        appliquerIntegration(p.id, pos, vels.get(p.id), caps.get(p.id), posture);
        // le porté suit sa monture : même position, même vitesse, même cap —
        // un renversement de la monture jette aussi le cavalier à terre
        const idCavalier = cavalierDe.get(p.id); // la monture porte au plus un homme
        if (idCavalier != null) {
          if (renverses.has(p.id) && !renverses.has(idCavalier)) {
            renverses.set(idCavalier, renverses.get(p.id));
          }
          let postureCavalier = postures.get(idCavalier);
          if (renverses.has(idCavalier) && postureCavalier !== 'gisant') postureCavalier = 'renverse';
          appliquerIntegration(idCavalier, pos, vels.get(p.id), caps.get(p.id), postureCavalier);
        }
        if (!avecDebug) continue;
        const vd = desirees.get(p.id);
        const cx = pos.x - p.pos.x;
        const cy = pos.y - p.pos.y;
        const fTot = forces.get(p.id);
        const fAvant = avantCoude.get(p.id) ?? { x: 0, y: 0 };
        const coude = fTot ? { x: fTot.x - fAvant.x, y: fTot.y - fAvant.y } : null;
        debug.set(p.id, {
          vitesseDesiree: vd ? { x: vd.x, y: vd.y } : null,
          coude: coude && Math.hypot(coude.x, coude.y) > 1e-9 ? coude : null,
          // la correction dure appliquée par collisions/ (null si aucune)
          correction: Math.hypot(cx, cy) > 1e-9 ? { x: cx, y: cy } : null,
        });
      }
      // ── le VOL : l'état réalisable vient de 🏃 (steering/vol, borné par
      // le profil) — l'Intégration reste l'écrivain unique, z compris ──
      if (volsDesires) {
        for (const { id, etat } of volsDesires()) {
          appliquerIntegration(id, etat.pos, etat.vel, etat.cap, undefined, etat.vol);
        }
      }
      if (avecDebug) dernierTick = debug;
    },

    /**
     * VUE debug (calque forces, 🖥️) : le dernier tick — vitesse désirée et
     * correction de collision par corps, plus les portées des champs (la
     * GÉOMÉTRIE des halos ; le profil réel vit dans forces/repulsions.js).
     * @returns {{portees: {hommes: number, murs: number}, parCorps: Map}}
     */
    forcesDebug() {
      debugDemande = true; // le prochain tick le construira — une frame de retard, pour un calque
      return {
        portees: {
          hommes: params.repulsionHommes.portee,
          murs: params.repulsionMurs.portee,
          // la garde est PAR ARME : le halo du sélectionné suit la sienne
          gardeDe: (id) => armeDe(id).allonge + params.garde.margeAllonge,
          gisants: params.repulsionGisants.portee,
        },
        parCorps: dernierTick,
        // les chocs du dernier tick (flash d'impact sur le calque forces)
        chocs: chocsDebug,
      };
    },
  };
}
