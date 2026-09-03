/**
 * 🏃 Action — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Traduit les Intentions (🧠) en vitesses désirées (⚙️). N'écrit jamais une
 * position. Signale les intentions irréalisables au puits injecté.
 */

import { trouverChemin } from './pathfinding/astar.js';
import { lisserChemin } from './pathfinding/lissage.js';
import { creerSuivi } from './steering/suivi-chemin.js';
import { consigneVol } from './steering/vol.js';
import { refusDeLaMonture } from './steering/refus-monture.js';

/**
 * @param {Object} deps
 * @param {{estLibre: Function, regionPour: Function}} deps.navgrid — vue 🌍
 * @param {(id: number) => Object | undefined} deps.corpsParId — vue 🌍 (positions)
 * @param {(idCorps: number, raison: string) => void} deps.signalerEchec — vers 🧠
 * @param {(idCorps: number, effortS: number) => void} deps.coutEffort — puits ❤️ (coûts des actes)
 * @param {(idCorps: number) => boolean} [deps.estVivant] — vue ❤️ (un mort n'agit plus)
 * @param {(idCorps: number) => number} [deps.facteurVitesseDe] — vue ❤️ (les blessures ralentissent)
 * @param {(idCorps: number) => number} [deps.vitesseMaxDe] — la vitesse max PAR CORPS (un homme en selle va au train de sa monture)
 * @param {(idCorps: number) => number|null} [deps.montureDe] — vue 🌍 (le refus s'applique au couple monté)
 * @param {(idCorps: number) => Object|null} deps.arcTirDe — vue ❤️ (l'arc de tir porté)
 * @param {(idCorps: number) => boolean} deps.puiserFleche — commande ❤️ (le carquois se compte)
 * @param {ReturnType<import('../infra/rng.js').creerRng>} deps.rng — la dispersion de la volée
 * @param {(idCorps: number, coup: {de: number}) => void} deps.subirCoup — puits ❤️ (l'acte a touché)
 * @param {(pos, rayon) => Array} deps.voisinsDans — vue 🌍 (snapshot : qui est devant ma lance)
 * @param {{vitesseMax: number, seuilWaypoint?: number}} deps.params
 */
export function creerAction({ navgrid, corpsParId, signalerEchec, coutEffort, subirCoup, voisinsDans, estVivant, facteurVitesseDe, vitesseMaxDe, montureDe, armeDe, bouclierDe, arcTirDe, puiserFleche, oiseauDe, rng, params }) {
  const suivi = creerSuivi({ vitesseMax: params.vitesseMax, seuilWaypoint: params.seuilWaypoint });

  /** @type {Map<number, {intention: Object, chemin: Array|null, index: number, arrive: boolean}>} */
  const taches = new Map();
  /** @type {Map<number, {x: number, y: number}>} — sortie du dernier phaseAction */
  const velDesirees = new Map();
  /** @type {Map<number, number>} — réarmement de l'acte de frappe (s) */
  const rearmes = new Map();
  /** @type {Map<number, {intensite: number, regard: {x,y}}>} — le refus des montures (viz) */
  const refusDebug = new Map();
  /** @type {Array<Object>} — les flèches en vol (résolues à l'atterrissage) */
  const enVol = [];
  /** @type {Array<{de: {x,y}, vers: {x,y}, touche: boolean, ageS: number}>} —
   *  les gestes récents, pour le calque coups (viz) */
  const coups = [];
  /** @type {Map<number, string>} — postures voulues (🧠), gestes écrits par ⚙️ */
  const posturesVoulues = new Map();
  /** @type {Map<number, {cap: number, vitesseRotation: number}>} — consignes
   *  d'orientation (🧠) traduites en taux : delta courant / durée du tour */
  const capsDesires = new Map();
  /** @type {Map<number, Object>} — l'état de vol réalisable du tick, par
   *  corps volant (steering/vol) — ⚙️ l'écrit tel quel */
  const volsDesires = new Map();

  return {
    /**
     * Reçoit l'intention courante d'un corps (remplace la précédente).
     * Appelé par 🧠 Cognition via le câblage du bootstrap.
     * @param {number} idCorps
     * @param {import('../cognition/intentions.js').Intention} intention
     */
    assigner(idCorps, intention) {
      // le jet se coupe quand l'intention change : l'enveloppe repartira de 0
      // MÊME CIBLE, CHEMIN GARDÉ : la dérive tolérée est PROPORTIONNELLE à la
      // distance restante (à 150 m, 5 % de dérive ne changent pas la route) —
      // sans quoi 300 assaillants rejetaient leur chemin de 150 m chaque fois
      // que le barycentre CRU de l'ennemi tremblait de 2 m
      const t = taches.get(idCorps);
      if (t?.chemin && t.intention.type === 'allerA' && intention.type === 'allerA') {
        const corps = corpsParId(idCorps);
        const dRestante = corps ? Math.hypot(intention.cible.x - corps.pos.x, intention.cible.y - corps.pos.y) : 0;
        const derive = Math.hypot(intention.cible.x - t.intention.cible.x, intention.cible.y - t.intention.cible.y);
        if (derive < Math.max(1, 0.05 * dRestante)) {
          // ARRIVÉ au bout, cible STRICTEMENT identique (une croyance fixe,
          // pas un slot qui respire) : acquis tant qu'on reste SUR PLACE —
          // c'est ce qui éteint la tempête des cibles inatteignables (au pied
          // du mur, chaque décision relançait une recherche pleine) ; délogé
          // de plus de 2 m, on recalcule (on a été poussé)
          // ARRIVÉ au bout du chemin : trois cas. Arrivée EXACTE (le bout est
          // la cible) → acquis tant qu'on reste sur place. Chemin TRONQUÉ
          // (borne d'exploration A*) qui a fait du chemin → jambe suivante.
          // CUL-DE-SAC (le bout n'a pas bougé du départ : cible murée) →
          // acquis aussi — sans quoi chaque décision relançait une recherche
          // pleine au pied du mur.
          if (t.arrive) {
            const bout = t.chemin[t.chemin.length - 1];
            const surPlace = corps && Math.hypot(corps.pos.x - bout.x, corps.pos.y - bout.y) <= 2;
            if (surPlace && derive < 0.05) {
              const exacte = Math.hypot(bout.x - t.intention.cible.x, bout.y - t.intention.cible.y) < 0.75;
              const progres = t.posDepart
                ? Math.hypot(bout.x - t.posDepart.x, bout.y - t.posDepart.y) > 3
                : false;
              if (exacte || !progres) return;
            }
            taches.set(idCorps, { intention, chemin: null, index: 0, arrive: false });
            return;
          }
          t.intention = intention;
          return;
        }
      }
      taches.set(idCorps, { intention, chemin: null, index: 0, arrive: false });
    },

    /**
     * Reçoit la consigne d'orientation d'un corps (🧠, rythme de l'attention) :
     * un cap ET une durée de tour (~N, humaine) — traduite ici en taux de
     * rotation depuis le cap réel courant. null = pas de préférence.
     * @param {number} idCorps @param {{cap: number, dureeS: number}|null} consigne
     */
    orienter(idCorps, consigne) {
      if (consigne === null) {
        capsDesires.delete(idCorps);
        return;
      }
      const capActuel = corpsParId(idCorps)?.cap ?? consigne.cap;
      const delta = Math.abs(
        Math.atan2(Math.sin(consigne.cap - capActuel), Math.cos(consigne.cap - capActuel))
      );
      capsDesires.set(idCorps, {
        cap: consigne.cap,
        vitesseRotation: delta / Math.max(0.05, consigne.dureeS),
      });
    },

    /** VUE debug (🖥️) : le refus courant des montures — id cavalier → {intensite, regard}. */
    refusPourDebug() {
      return refusDebug;
    },

    /**
     * PHASE action : calcule les chemins manquants (A*), avance le steering.
     * @param {number} dt
     */
    phaseAction(dt) {
      velDesirees.clear();
      refusDebug.clear();
      volsDesires.clear();
      for (const c of coups) c.ageS += dt;
      for (let i = coups.length - 1; i >= 0; i--) {
        if (coups[i].ageS > (coups[i].vie ?? 0.5)) coups.splice(i, 1);
      }
      // ── L'ATTERRISSAGE des flèches : l'impact se résout là où elle tombe,
      // sur qui s'y trouve MAINTENANT — pas au moment du lâcher ──
      for (let i = enVol.length - 1; i >= 0; i--) {
        const f = enVol[i];
        if (f.ageS < f.volS) continue;
        enVol.splice(i, 1);
        let victime = null;
        let dMin = Infinity;
        for (const v of voisinsDans(f.vers, params.tir.rayonImpact)) {
          if (v.posture === 'gisant') continue;
          const dv = Math.hypot(v.pos.x - f.vers.x, v.pos.y - f.vers.y);
          if (dv < dMin) {
            dMin = dv;
            victime = v;
          }
        }
        if (victime) subirCoup(victime.id, { de: f.deId, gravite: 1 });
        f.touche = victime !== null;
      }
      for (const [id, tache] of taches) {
        const corps = corpsParId(id);
        if (!corps) continue;
        if (estVivant && !estVivant(id)) continue; // un mort n'agit plus

        // ── LE VOL : l'intention tient (comme allerA) — l'actuateur borne
        // le voulu par le profil, chaque tick, depuis l'état de vol RÉEL ──
        if (tache.intention.type === 'voler') {
          const profil = oiseauDe?.(id);
          if (!profil || !corps.vol) continue; // sans ailes, l'intention meurt
          volsDesires.set(id, consigneVol(corps, profil, tache.intention, dt));
          continue;
        }

        // ── L'ACTE DE FRAPPER : l'intention nomme la cible, la lance juge —
        // allonge, arc du cap, la cible y est-elle ENCORE. Un coup peut rater.
        if (tache.intention.type === 'frapper') {
          coutEffort(id, dt); // l'engagement plein : ~45 s de souffle
          const cibleBrute = corpsParId(tache.intention.cible);
          // un gisant n'est plus une cible : le geste s'arrête (pas d'acharnement)
          const cible = cibleBrute && cibleBrute.posture !== 'gisant' ? cibleBrute : null;

          // LA FENTE : le geste porte le corps en avant, vers la cible — c'est
          // elle qui perce la garde adverse (⚙️). Un GESTE BREF : la fenêtre
          // qui précède le coup, pas une poussée continue (sinon le tapis
          // roulant fente/garde fait surfer le frappeur à travers la carte)
          const enFente = (rearmes.get(id) ?? 0) <= params.combat.dureeFenteS;
          if (cible && enFente) {
            const dx = cible.pos.x - corps.pos.x;
            const dy = cible.pos.y - corps.pos.y;
            const d = Math.hypot(dx, dy) || 1;
            const vFente = params.vitesseMax * params.combat.allureFente * (facteurVitesseDe?.(id) ?? 1);
            velDesirees.set(id, { x: (dx / d) * vFente, y: (dy / d) * vFente });
          }

          const restant = (rearmes.get(id) ?? 0) - dt;
          if (restant > 0) {
            rearmes.set(id, restant);
            continue;
          }
          // l'arme du PORTEUR juge : allonge, ZONE MORTE, arc, réarmement (❤️)
          const { allonge, priseMin, arc, periodeCoupS } = armeDe(id);
          let touche = false;
          let pare = false;
          if (cible) {
            const dx = cible.pos.x - corps.pos.x;
            const dy = cible.pos.y - corps.pos.y;
            const d = Math.hypot(dx, dy);
            const ecart = Math.atan2(Math.sin(Math.atan2(dy, dx) - corps.cap), Math.cos(Math.atan2(dy, dx) - corps.cap));
            // dans la zone morte, la pointe ne se présente pas — le coup fend le vide
            touche = d <= allonge + cible.rayon && d >= (priseMin ?? 0) && Math.abs(ecart) <= arc / 2;
            // LA PARADE : un coup porté qui arrive dans l'arc couvert du
            // bouclier de la cible (autour de SON cap) fait CLANG — un fait
            // d'angle, pas un compteur
            const bouclier = touche ? bouclierDe?.(tache.intention.cible) : null;
            if (bouclier) {
              const versAttaquant = Math.atan2(-dy, -dx); // depuis la cible
              const ecartBouclier = Math.atan2(Math.sin(versAttaquant - cible.cap), Math.cos(versAttaquant - cible.cap));
              pare = Math.abs(ecartBouclier) <= bouclier.arcCouverture / 2;
              // le CLANG use le bras : la parade coûte du souffle au porteur
              if (pare) coutEffort(tache.intention.cible, bouclier.coutParadeS);
            }
            // le geste se VOIT : la pointe part vers la cible (portée ou non)
            const portee = Math.min(d, allonge + cible.rayon);
            coups.push({
              de: { x: corps.pos.x, y: corps.pos.y },
              vers: { x: corps.pos.x + (dx / (d || 1)) * portee, y: corps.pos.y + (dy / (d || 1)) * portee },
              touche: touche && !pare,
              pare,
              ageS: 0,
            });
          }
          if (touche && !pare) subirCoup(tache.intention.cible, { de: id });
          rearmes.set(id, periodeCoupS); // porté, paré ou raté : le geste est fait
          continue;
        }

        // ── L'ACTE DE TIRER : la volée sur une ZONE — la flèche part, se
        // disperse, et touche QUI SE TROUVE là où elle tombe (ami compris).
        // Le carquois se compte : à vide, l'acte refuse, la garde basculera.
        if (tache.intention.type === 'tirer') {
          const arc = arcTirDe?.(id);
          if (!arc) continue;
          const restant = (rearmes.get(id) ?? 0) - dt;
          if (restant > 0) {
            rearmes.set(id, restant);
            continue;
          }
          rearmes.set(id, arc.periodeTirS);
          if (!puiserFleche(id)) continue; // plus une flèche — le geste meurt
          coutEffort(id, arc.coutTirS); // bander n'est pas un geste d'adresse
          const dTir = Math.hypot(
            tache.intention.zone.x - corps.pos.x,
            tache.intention.zone.y - corps.pos.y
          );
          const angle = rng.entre(0, Math.PI * 2);
          const rayon = rng.entre(0, arc.dispersionParMetre * dTir);
          const chute = {
            x: tache.intention.zone.x + Math.cos(angle) * rayon,
            y: tache.intention.zone.y + Math.sin(angle) * rayon,
          };
          // LA FLÈCHE VOLE : la chute est jouée au lâcher (on arrose une
          // zone, pas un homme), mais l'impact n'arrive qu'à l'atterrissage —
          // pendant le vol, la troupe MARCHE : les ratés sur cible mobile
          // émergent du temps de vol, ils ne sont écrits nulle part.
          const fleche = {
            fleche: true,
            deId: id,
            volS: dTir / arc.vitesseVol,
            de: { x: corps.pos.x, y: corps.pos.y },
            vers: chute,
            touche: null, // inconnu tant qu'elle vole
            ageS: 0,
          };
          fleche.vie = fleche.volS + 0.9; // la croix d'impact reste ~1 s
          coups.push(fleche);
          enVol.push(fleche);
          continue;
        }

        if (tache.intention.type !== 'allerA' || tache.arrive) continue;

        if (!tache.chemin) {
          const region = navgrid.regionPour(corps.pos, tache.intention.cible);
          const brut = trouverChemin(region, corps.pos, tache.intention.cible);
          tache.posDepart = { x: corps.pos.x, y: corps.pos.y };
          tache.chemin = brut && lisserChemin(brut, corps.pos, navgrid.estLibre);
          if (!tache.chemin) {
            tache.arrive = true; // irréalisable : on n'insiste pas
            signalerEchec(id, 'pasDeChemin');
            continue;
          }
          tache.index = 0;
        }

        const r = suivi.avancer(tache.chemin, tache.index, corps.pos);
        tache.index = r.index;
        tache.arrive = r.arrive;
        const allure = (tache.intention.allure ?? 1) * (facteurVitesseDe?.(id) ?? 1);
        // la vitesse max est PAR CORPS : le suivi sort un vecteur a
        // params.vitesseMax — on le remet a l'echelle de CE corps (monture)
        const echelle = (vitesseMaxDe?.(id, tache.intention.train) ?? params.vitesseMax) / params.vitesseMax;
        if (!r.arrive) {
          let vel = { x: r.vel.x * allure * echelle, y: r.vel.y * allure * echelle };
          // LE REFUS : monté, le cheval juge le terrain devant lui — le
          // cavalier veut, la monture refuse une masse hérissée (réflexe)
          const idMonture = montureDe?.(id);
          const monture = idMonture != null ? corpsParId(idMonture) : null;
          if (monture) {
            const refus = refusDeLaMonture({
              pos: monture.pos,
              livree: monture.livree,
              vel,
              voisinsDans,
              armeDe,
              params: params.cheval,
            });
            vel = refus.vel;
            if (refus.intensite > 0) refusDebug.set(id, { intensite: refus.intensite, regard: refus.regard });
            else refusDebug.delete(id);
          }
          velDesirees.set(id, vel);
        }
      }

      // tenir la posture prête USE (❤️) — une ligne ne reste pas levée sans fin
      for (const [id, posture] of posturesVoulues) {
        if (posture === 'pret') coutEffort(id, armeDe(id).coutPosturePret * dt); // la garde haute d'une pique épuise
      }

      // la locomotion coûte (❤️) : ∝ vitesse demandée, la marche reste douce
      for (const [id, vel] of velDesirees) {
        // bornee a 1 : le souffle du CHEVAL est differe — le cavalier ne paie
        // pas de sa poitrine le galop de sa monture
        const intensite = Math.min(1, Math.hypot(vel.x, vel.y) / params.vitesseMax);
        coutEffort(id, intensite * params.souffle.facteurMarche * dt);
      }
    },

    /**
     * Reçoit la posture voulue d'un corps (🧠) : un GESTE (lance levée…),
     * écrit tel quel par ⚙️. @param {number} idCorps @param {string} posture
     */
    poserPosture(idCorps, posture) {
      posturesVoulues.set(idCorps, posture);
    },

    /**
     * VUE pour ⚙️ Physique : les gestes voulus.
     * @returns {Iterable<{id: number, posture: string}>}
     */
    *posturesDesirees() {
      for (const [id, posture] of posturesVoulues) yield { id, posture };
    },

    /**
     * VUE pour ⚙️ Physique : la sortie du container — contrat minuscule.
     * @returns {Iterable<{id: number, vel: {x: number, y: number}}>}
     */
    *vitessesDesirees() {
      for (const [id, vel] of velDesirees) yield { id, vel };
    },

    /**
     * VUE pour ⚙️ Physique : l'état de vol réalisable du tick, par corps
     * volant (déjà borné par le profil — ⚙️ l'écrit tel quel).
     * @returns {Iterable<{id: number, etat: Object}>}
     */
    *volsDesires() {
      for (const [id, etat] of volsDesires) yield { id, etat };
    },

    /**
     * VUE pour ⚙️ Physique : les consignes d'orientation (un homme immobile
     * peut pivoter, chacun à son rythme).
     * @returns {Iterable<{id: number, cap: number, vitesseRotation: number}>}
     */
    *orientationsDesirees() {
      for (const [id, c] of capsDesires) yield { id, cap: c.cap, vitesseRotation: c.vitesseRotation };
    },

    /**
     * VUE debug pour 🖥️ (calque coups) : les gestes récents (≤ 0,5 s).
     * @returns {Array<{de, vers, touche, ageS}>}
     */
    coupsPourDebug() {
      return coups;
    },


    /**
     * VUE debug pour 🖥️ (calque chemins) : chemins et cibles courants.
     * @returns {Iterable<{id: number, chemin: Array, index: number}>}
     */
    *cheminsPourDebug() {
      for (const [id, t] of taches) {
        if (t.chemin && !t.arrive) yield { id, chemin: t.chemin, index: t.index };
      }
    },
  };
}
