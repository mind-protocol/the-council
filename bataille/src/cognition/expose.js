/**
 * 🧠 Cognition — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Par homme : une Représentation (croyances datées sur des OBJETS — individus
 * suivis et tas) + un brain. Phases : perception (cadence propre ~2 Hz
 * échelonnée) puis décision. Ne lit le Monde que par la vue injectée ;
 * n'écrit jamais une position — émet des Intentions.
 */

import { creerRepresentation } from './representation.js';
import { creerCouverture } from './couverture.js';
import { creerPercevoir } from './perception/percevoir.js';
import { arbitrerOrientation } from './orientation.js';
import { decrireTas } from './langage/decrire.js';

/**
 * @param {Object} deps
 * @param {(idCorps, intention) => void} deps.emettreIntention — puits vers 🏃
 * @param {(idCorps, consigne: {cap: number, dureeS: number}|null) => void}
 *   deps.emettreOrientation — puits vers 🏃 : le cap désiré du CORPS (la
 *   lance) + la durée du tour, tirée ~N par consigne (pas robotique)
 * @param {(idCorps, posture: string) => void} [deps.emettrePosture] — puits vers 🏃 (geste)
 * @param {(idCorps, texte: string, dureeS?: number) => void} [deps.emettreParole]
 *   — puits vers 🖥️ (bulles) : la parole flavor se VOIT ; demain la
 *   Transmission 📯 (la voix qui porte). Absent en headless : silence.
 * @param {(idCorps) => boolean} [deps.estVivant] — vue ❤️ (un mort ne pense plus)
 * @param {{posDe, velDe, autourDe}} deps.vuePerception — vue 🌍 (snapshot + proprioception), bootstrap
 * @param {ReturnType<import('../infra/rng.js').creerRng>} deps.rng
 * @param {Object} deps.params
 */
// La fenetre de couverture gardee pour qui ne commande pas. 30 s : au-dela,
// la carte ne sert plus le fallback « chercher », elle sert le ratissage —
// et le ratissage est le metier du commandant.
const COUVERTURE_DEPUIS_RANG = 30;

// A quelle distance du point vise un homme pilote se considere arrive. Deux
// metres : la largeur d'un homme et son pas — plus serre, il pietine.
const ARRIVE_M = 2;

export function creerCognition({ emettreIntention, emettreOrientation, emettrePosture, emettreParole, estVivant, vuePerception, rng, params }) {
  /** @type {Map<number, {representation, brain, tempsRestant}>} */
  const hommes = new Map();
  const percevoir = creerPercevoir({ vuePerception, params });

  const tirerPeriodePerception = () => {
    const { moyenneHz, ecartTypeHz } = params.perception.cadence;
    return 1 / Math.max(0.2, rng.normale(moyenneHz, ecartTypeHz));
  };
  const tirerPeriodeMasse = () => {
    const { moyenneHz, ecartTypeHz } = params.perception.masse.cadence;
    return 1 / Math.max(0.05, rng.normale(moyenneHz, ecartTypeHz));
  };

  return {
    /**
     * Attache une cognition à un corps (au spawn, par le bootstrap).
     * @param {number} idCorps
     * @param {{connaissance: Object, fabriqueBrain: ({representation, dire}) => Object}} config
     *   — connaissance : {noms, amisIds, uniteIds, chefId} (seed de la Représentation)
     */
    attacher(idCorps, { connaissance = {}, fabriqueBrain }) {
      const representation = creerRepresentation({
        monId: idCorps,
        couverture: creerCouverture(params.couverture),
        ...connaissance,
      });
      representation.reglerPeur(params.moral);
      // la parole de CET homme : le puits, fermé sur son id
      const dire = (texte, dureeS) => emettreParole?.(idCorps, texte, dureeS);
      const brain = fabriqueBrain({ representation, dire });
      hommes.set(idCorps, {
        representation,
        brain,
        tempsRestant: rng.uniforme() * tirerPeriodePerception(), // échelonnage
        tempsMasse: rng.uniforme() * tirerPeriodeMasse(), // le coup d'œil au loin, échelonné aussi
      });
    },

    // ── SE RELIRE (docs/sauvegarde.md) ────────────────────────────────────
    //
    // Une tete NE SE RECREE PAS ici : `restaurer` reprend l'acquis de tetes
    // DEJA attachees. L'ordre du chargement est donc : les corps, puis
    // `attacher()` pour chaque homme (avec sa semence : noms, amis, unite,
    // chef, livree, posture), puis ceci. Une tete restauree sans corps
    // croirait en quelqu'un qui n'existe pas.
    //
    // `tempsRestant` et `tempsMasse` — l'echelonnage des cadences — SORTENT
    // depuis que la map est le monde persistant. Ils ne sortaient pas, au
    // motif que « personne ne s'apercevra qu'un homme a regarde un
    // quarantieme de seconde plus tot ». C'etait juste pour une sauvegarde de
    // commodite ; ca ne l'est plus pour un monde qu'on ferme et qu'on rouvre :
    // mesure, une reprise derivait de 1,10 m en moyenne sur 20 s rejouees, et
    // cette derive s'accumule a chaque ouverture. Deux flottants par homme.
    // Les jauges de parole, elles, ne sortent toujours pas : un homme qui
    // redit une ligne ne vaut pas un champ.

    /**
     * LA DECIMATION SE DECIDE ICI, ET PAR LE ROLE. La carte du « ou j'ai
     * regarde » est le poste le plus lourd d'une sauvegarde ; elle ne sert
     * pas la meme chose selon qui la porte :
     *
     *   - le COMMANDANT s'en sert pour RATISSER — une manoeuvre deliberee qui
     *     couvre du terrain sur des minutes. Sa carte longue est son outil,
     *     elle sort entiere ;
     *   - l'homme du rang s'en sert pour ne pas re-scruter l'angle qu'il vient
     *     de faire. Cette memoire-la se refait toute seule en quelques
     *     secondes de regard : on n'en garde que le frais.
     *
     * Ce qu'on perd est donc borne et se repare tout seul : un homme recharge
     * re-balaye un angle, une fois. Voir docs/sauvegarde.md.
     *
     * @param {{couvertureDepuis?: number}} [opts] — la fenetre gardee pour
     *   ceux qui ne commandent pas, en secondes de sim
     * @returns {Array<[number, {representation, brain, posture}]>}
     */
    etat({ couvertureDepuis = COUVERTURE_DEPUIS_RANG } = {}) {
      return [...hommes.entries()].map(([id, h]) => {
        const brain = h.brain.etat?.() ?? null;
        const commande = brain?.role === 'commandant';
        return [id, {
          representation: h.representation.etat({
            couvertureDepuis: commande ? undefined : couvertureDepuis,
          }),
          brain,
          posture: h.posture ?? null,
          // les deux echeances de perception, la ou elles en sont
          tempsRestant: h.tempsRestant,
          tempsMasse: h.tempsMasse,
        }];
      });
    },

    /** @param {Array<[number, Object]>} liste — les tetes doivent etre attachees */
    restaurer(liste = []) {
      for (const [id, d] of liste) {
        const h = hommes.get(Number(id));
        if (!h) {
          console.warn(`cognition : tete #${id} restauree sans homme attache — ignoree`);
          continue;
        }
        h.representation.restaurer(d.representation);
        if (d.brain) h.brain.restaurer?.(d.brain);
        if (d.posture) h.posture = d.posture;
        // Une sauvegarde d'avant (sans les echeances) laisse celles du spawn :
        // elle se reprend, elle ne se rejoue simplement pas au bit pres.
        if (typeof d.tempsRestant === 'number') h.tempsRestant = d.tempsRestant;
        if (typeof d.tempsMasse === 'number') h.tempsMasse = d.tempsMasse;
      }
    },

    /**
     * PHASE perception : vieillit les croyances, perçoit aux échéances —
     * puis ORIENTE : l'arbitrage d'attention tourne au même rythme, sur les
     * percepts frais (la continuité, elle, est bornée en ⚙️).
     */
    phasePerception(dt) {
      percevoir.tick?.(dt);
      for (const [id, h] of hommes) {
        if (estVivant && !estVivant(id)) continue; // un mort ne perçoit plus
        h.representation.vieillir(dt);
        // ── l'HORIZON DE MASSE : le coup d'œil au loin, cadence lente —
        // indépendant du scan de détail (l'alerte n'accélère que le détail)
        h.tempsMasse -= dt;
        if (h.tempsMasse <= 0) {
          h.tempsMasse = tirerPeriodeMasse();
          const loin = percevoir.percevoirMasses(id, h.representation.contextePerception());
          h.representation.integrer(loin.posMoi, loin.percepts, []);
        }
        h.tempsRestant -= dt;
        if (h.tempsRestant > 0) continue;
        // ALERTE : un adverse cru au contact accélère mon re-scan (saillance)
        const enAlerte = h.representation
          .contactsCrus()
          .some((c) => c.livree && h.representation.maLivree && c.livree !== h.representation.maLivree);
        // CALME : sans adverse au contact ni ennemi cru en mémoire, on scrute moins (levier de scale n°1 — l'horizon de masse veille)
        const calme = !enAlerte && !h.representation.tasCru('ennemis');
        h.tempsRestant = tirerPeriodePerception() * (enAlerte ? params.perception.facteurAlerte : calme ? params.perception.facteurCalme : 1);
        const { posMoi, percepts, gisantsVus } = percevoir.percevoir(id, h.representation.contextePerception());
        h.representation.integrer(posMoi, percepts, gisantsVus);
        // la couverture se tamponne : je viens de balayer mon disque de vue
        h.representation.couverture?.tamponner(posMoi, params.perception.portee);

        h.orientationDebug = arbitrerOrientation({
          vitesse: vuePerception.velDe(id),
          etatBrain: h.brain.etatCourant?.(),
          formation: h.brain.formationDebug?.() ?? null,
          representation: h.representation,
          params,
        });
        if (h.orientationDebug) {
          const { moyenneS, ecartTypeS } = params.orientation.dureeRotation;
          emettreOrientation(id, {
            cap: h.orientationDebug.cap,
            dureeS: Math.max(0.15, rng.normale(moyenneS, ecartTypeS)),
          });
        } else {
          emettreOrientation(id, null);
        }
      }
    },

    /** PHASE décision : interroge chaque brain (cadence propre). */
    phaseDecision(dt) {
      for (const [idCorps, h] of hommes) {
        // la mort se CONSTATE (❤️) et se MANIFESTE : le corps tombe (gisant),
        // écrit par la chaîne normale — la mort se voit, elle ne se sait pas
        if (estVivant && !estVivant(idCorps)) {
          if (h.posture !== 'gisant') {
            h.posture = 'gisant';
            emettrePosture?.(idCorps, 'gisant');
          }
          continue;
        }
        // LE BRAIN TOURNE TOUJOURS, meme pilote : il percoit, il a peur, il
        // parle, sa machine avance. On ne remplace que ce qu'il VEUT FAIRE —
        // on commande un homme, on ne commande pas ses croyances.
        // ARRIVE, IL SE REND A LUI-MEME. Un ordre du joueur est un ordre, pas
        // une laisse : sans cela, un homme pilote reste fige sur son point
        // d'arrivee et ignore tout le reste de la bataille.
        if (h.pilote?.type === 'allerA') {
          const p = vuePerception.posDe(idCorps);
          const c = h.pilote.cible;
          if (p && Math.hypot(p.x - c.x, p.y - c.y) <= ARRIVE_M) h.pilote = null;
        }
        const intention = h.brain.decide(dt);
        const voulue = h.pilote ?? intention;
        if (voulue) emettreIntention(idCorps, voulue);
        // la posture est un GESTE : émise seulement quand elle change
        const posture = h.brain.postureCourante?.() ?? 'repos';
        if (posture !== h.posture) {
          h.posture = posture;
          emettrePosture?.(idCorps, posture);
        }
      }
    },

    /**
     * PILOTER — la main du joueur sur un homme. L'intention passee ici prend
     * le pas sur celle de sa tete, tant qu'elle n'est pas retiree (`null`).
     * Un homme pilote reste un homme : il voit, il craint, il crie ; il ne
     * choisit pas ou il va.
     * @param {number} idCorps @param {Object|null} intention
     */
    piloter(idCorps, intention) {
      const h = hommes.get(idCorps);
      if (h) h.pilote = intention ?? null;
    },

    /**
     * ÉCHAFAUDAGE — à remplacer par la chaîne 📯 (chef → voix → percept) :
     * injecte un ordre directement dans la Représentation.
     * @param {number} idCorps @param {Object|null} ordre
     */
    injecterOrdre(idCorps, ordre) {
      hommes.get(idCorps)?.representation.recevoirOrdre(ordre);
    },

    // ── VUES (🖥️) ──

    introspecter(idCorps) {
      return hommes.get(idCorps)?.brain.introspect();
    },

    /**
     * Calque perception : les croyances de cet homme (individus + tas),
     * chaque tas décrit en français (langage/decrire).
     */
    perceptionDebug(idCorps) {
      const h = hommes.get(idCorps);
      if (!h) return undefined;
      const snap = h.representation.snapshotDebug();
      return {
        portee: params.perception.portee,
        moi: snap.moi,
        individus: snap.individus,
        contacts: snap.contacts,
        tas: snap.tas.map((t) => ({ ...t, description: decrireTas(t) })),
      };
    },

    /** Calque formation : ancre crue + cible de slot (si en formation). */
    formationDebug(idCorps) {
      return hommes.get(idCorps)?.brain.formationDebug?.() ?? null;
    },

    /** Calque orientation : le dernier arbitrage (composantes + résultante). */
    orientationDebug(idCorps) {
      return hommes.get(idCorps)?.orientationDebug ?? null;
    },

    /** Calque couverture : où cet homme a regardé, et quand. */
    couvertureDebug(idCorps) {
      return hommes.get(idCorps)?.representation.couverture?.casesDebug() ?? null;
    },

    /** Calque état-major : la dernière délibération du rôle (null si pas commandant). */
    etatMajorDebug(idCorps) {
      return hommes.get(idCorps)?.brain.etatMajorDebug?.() ?? null;
    },
  };
}
