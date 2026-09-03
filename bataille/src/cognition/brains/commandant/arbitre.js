/**
 * 🧠 Commandant / Arbitre — LE moteur, écrit une fois, générique :
 * applicables (faits) → axes (projection) → score = Σ poids × axe →
 * ENGAGEMENT avec hystérésis, suivi de phases, mémoire des échecs.
 * Ajouter une manœuvre au livre n'ajoute jamais une branche ici.
 * Sur abandon (échec, patience, inapplicabilité), il fait crier
 * EN FORMATION — un commandant ne cesse pas de commander en silence, et le
 * REPOS est une CONCLUSION (une phase du livre), jamais un abandon : une
 * unité qui vient de subir le contact TIENT LES RANGS, elle ne discute pas.
 */

import { estimerSituation, CRITERES } from './estimation.js';
import { projeterAxes } from './projection.js';
import { motDirection } from '../../langage/decrire.js';

export function creerArbitre({ manoeuvres, representation, rng, params, zone, drill, carte, tire }) {
  const cfg = params.commandement;
  // personnalité : offsets de poids seedés — deux commandants diffèrent
  const poids = {};
  for (const [axe, w] of Object.entries(cfg.poids)) {
    poids[axe] = w + rng.normale(0, cfg.personnaliteEcart);
  }

  /** @type {{manoeuvre, phase: number, destination, tempsPhase, score}|null} */
  let engagement = null;
  /** @type {Map<string, number>} — nom → secondes de bouderie restantes */
  const boudees = new Map();
  let dernierDebug = null;
  let faitsPrecedents = null;

  const critere = (nom, situation) => {
    const c = CRITERES[nom];
    if (!c) throw new Error(`arbitre : critère inconnu '${nom}'`);
    return c(situation, engagement);
  };

  const scorer = (situation) =>
    manoeuvres.map((m) => {
      const applicable = m.applicabilite.every((f) => !!situation[f]);
      const boudee = (boudees.get(m.nom) ?? 0) > 0;
      // TOUTES les options de la manœuvre sont projetées et scorées — la
      // meilleure porte la manœuvre (« par la gauche » peut battre « de
      // front ») ; les autres restent visibles (viz de l'espace des choix)
      const options = applicable && !boudee ? projeterAxes(m, situation, params) : [];
      const biaisPosture = m.poids?.[situation.posture] ?? 0;
      const scorees = options.map((o) => {
        let score = biaisPosture;
        for (const [axe, v] of Object.entries(o.axes)) score += (poids[axe] ?? 0) * v;
        return { ...o, score };
      });
      const meilleureOption = scorees.reduce((a, b) => (b.score > (a?.score ?? -Infinity) ? b : a), null);
      return {
        manoeuvre: m,
        nom: m.nom,
        applicable,
        boudee,
        axes: meilleureOption?.axes ?? null,
        geo: meilleureOption?.geo ?? null,
        option: meilleureOption?.nom ?? null,
        options: scorees,
        score: meilleureOption?.score ?? -Infinity,
      };
    });

  /** Concrétise l'ordre d'une phase (les refs viennent de la géométrie). */
  const concretiser = (phase, geo) => {
    const ordre = { ...phase.ordre };
    if ((ordre.verbe === 'RATISSER' || ordre.verbe === 'CHARGER' || ordre.verbe === 'RECULER') && geo?.destination && situationPos()) {
      const de = situationPos();
      const cap = Math.atan2(geo.destination.y - de.y, geo.destination.x - de.x);
      ordre.vers = { type: 'direction', nom: motDirection(cap) };
    }
    return ordre;
  };
  let derniereSituation = null;
  const situationPos = () => derniereSituation?.positionUnite ?? derniereSituation?.moiPos;

  const entrerPhase = (situation, indexPhase, geo) => {
    engagement.phase = indexPhase;
    engagement.tempsPhase = 0;
    engagement.destination = geo?.destination ?? engagement.destination;
    engagement.poste = geo?.poste ?? engagement.poste; // où se FORMER (≠ où aller)
    const phase = engagement.manoeuvre.phases[indexPhase];
    if (phase.conclusion === 'infirmerEnnemi') representation.infirmerTas('ennemis');
    return concretiser(phase, geo);
  };

  const abandonner = (raison) => {
    boudees.set(engagement.manoeuvre.nom, cfg.malusEchecS);
    dernierDebug = { ...dernierDebug, abandon: raison };
    engagement = null;
    // tenir les rangs — le repos est une conclusion, jamais un abandon
    return { verbe: 'EN_FORMATION' };
  };

  return {
    /** Le temps passe (patiences de phase, bouderies). */
    vieillir(dt) {
      if (engagement) engagement.tempsPhase += dt;
      for (const [nom, t] of boudees) {
        if (t - dt <= 0) boudees.delete(nom);
        else boudees.set(nom, t - dt);
      }
    },

    /**
     * Une délibération complète. @returns {{aEmettre: Object|null, justification: string|null}}
     */
    deliberer() {
      const situation = estimerSituation(representation, { zone, drill, carte, tire: tire?.() ?? false }, params);
      derniereSituation = situation;
      const candidates = scorer(situation);
      const meilleure = candidates.reduce((a, b) => (b.score > a.score ? b : a), candidates[0]);
      let aEmettre = null;
      let justification = null;

      if (!engagement) {
        // PLANCHER : une utilité négative ne s'engage pas — mieux vaut tenir
        // les rangs que sonner une charge à contre-cœur (le chef défenseur
        // qui emmenait ses piques à l'autre bout de la carte)
        if (meilleure && meilleure.score > cfg.plancherEngagement) {
          engagement = { manoeuvre: meilleure.manoeuvre, phase: 0, destination: null, tempsPhase: 0, score: meilleure.score };
          aEmettre = entrerPhase(situation, 0, meilleure.geo);
          justification = `j'engage ${meilleure.nom}${meilleure.option ? ` (${meilleure.option})` : ''}`;
        }
      } else {
        const engagee = candidates.find((c) => c.nom === engagement.manoeuvre.nom);
        const phase = engagement.manoeuvre.phases[engagement.phase];
        if (engagee.applicable) engagement.score = engagee.score; // score vivant
        if (phase.echec && critere(phase.echec, situation)) {
          aEmettre = abandonner(`échec : ${phase.echec}`);
          justification = `échec (${phase.echec}) — repos`;
        } else if (phase.patience && engagement.tempsPhase > phase.patience) {
          aEmettre = abandonner('patience épuisée');
          justification = 'trop long — repos';
        } else if (phase.relance && critere(phase.relance, situation) && !critere(phase.succes, situation)) {
          aEmettre = entrerPhase(situation, engagement.phase, engagee.geo); // re-crier : bond suivant
          justification = 'la troupe est posée — bond suivant';
        } else if (critere(phase.succes, situation)) {
          if (phase.repete && critere(phase.repete, situation)) {
            aEmettre = entrerPhase(situation, engagement.phase, engagee.geo); // même phase, nouveau secteur
            justification = 'secteur suivant';
          } else if (engagement.phase + 1 < engagement.manoeuvre.phases.length) {
            aEmettre = entrerPhase(situation, engagement.phase + 1, engagee.geo);
            justification = 'phase suivante';
          } else {
            engagement = null; // manœuvre accomplie
            justification = 'manœuvre accomplie';
          }
        } else if (!engagee.applicable) {
          // évalué APRÈS le succès de phase : une manœuvre qui vient
          // d'accomplir sa phase mérite sa conclusion
          aEmettre = abandonner('plus applicable');
          justification = "la manœuvre n'a plus lieu d'être — repos";
        } else if (meilleure.nom !== engagement.manoeuvre.nom && meilleure.score > engagement.score * cfg.hysteresis + 0.05) {
          engagement = { manoeuvre: meilleure.manoeuvre, phase: 0, destination: null, tempsPhase: 0, score: meilleure.score };
          aEmettre = entrerPhase(situation, 0, meilleure.geo);
          justification = `${meilleure.nom}${meilleure.option ? ` (${meilleure.option})` : ''} devient nettement meilleure`;
        }
      }

      // MON POSTE — la croyance que la machine soldat consommera :
      // 1. la manœuvre engagée le déclare (geo.poste, ou la destination si
      //    posteChef) ; 2. SANS manœuvre, le chef rallie SA MEILLEURE LIGNE
      //    (jamais « sur place au milieu du grumeau ») — c'est elle qui
      //    redessine les fronts après le chaos, alliés-bouchent aidant
      const poste = engagement
        ? engagement.poste ?? (engagement.manoeuvre.posteChef ? engagement.destination : null)
        : situation.meilleureLigne()?.centre ?? null;
      representation.retenirPoste(poste ?? null);

      dernierDebug = {
        situation: Object.fromEntries(Object.entries(situation).filter(([, v]) => typeof v !== 'function' && typeof v !== 'object')),
        candidates: candidates.map(({ nom, option, applicable, boudee, axes, score }) => ({ nom, option, applicable, boudee, axes, score })),
        engagee: engagement
          ? { nom: engagement.manoeuvre.nom, phase: engagement.phase, phases: engagement.manoeuvre.phases.length, destination: engagement.destination, tempsPhase: engagement.tempsPhase }
          : null,
        justification,
        // la CARTE du rôle (calque etat-major) : ce que la délibération a vu —
        // l'axe de menace, la ligne crue, le poste retenu, la destination
        // engagée, et les OPTIONS pesées (chaque candidate avec sa géométrie)
        carte: {
          positionUnite: situation.positionUnite ?? null,
          capMenace: situation.capMenace ?? null,
          ennemi: situation.positionEnnemie ?? null,
          ligne: situation.meilleureLigne(), // mémoïsé — pas de second scan
          destination: engagement?.destination ?? null,
          poste: poste ?? null,
          // TOUTES les options de toutes les candidates — l'espace des choix
          options: candidates.flatMap((c) =>
            (c.options ?? []).map((o) => ({
              nom: o.nom ? `${c.nom} ${o.nom}` : c.nom,
              score: o.score,
              engagee: engagement?.manoeuvre.nom === c.nom && o.geo === c.geo,
              chemin: o.geo.chemin,
              destination: o.geo.destination,
              poste: o.geo.poste ?? null,
            }))
          ),
        },
      };
      return { aEmettre, justification };
    },

    /** Un fait saillant a-t-il basculé ? (force une délibération immédiate) */
    saillance() {
      const s = estimerSituation(representation, { zone, drill, carte, tire: tire?.() ?? false }, params);
      // auContact et ennemiTropPres : le CONTACT est saillant — sans eux, un
      // chef d'archers pouvait attendre sa cadence (~10 s) pour crier le
      // recul pendant que le fer fermait les 22 m de la fenêtre de tir
      const cles = ['ennemiLocalise', 'uniteFormee', 'uniteDispersee', 'auContact', 'ennemiTropPres'];
      const actuels = cles.map((k) => !!s[k]).join('|');
      const change = faitsPrecedents !== null && actuels !== faitsPrecedents;
      faitsPrecedents = actuels;
      return change;
    },

    /** Pour la viz état-major : la dernière délibération complète. */
    etatMajorDebug() {
      return dernierDebug;
    },
  };
}
