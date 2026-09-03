/**
 * 🧠 Commandant / Estimation — l'appréciation de situation : des FAITS
 * dérivés, nommés en français, PURS sur la Représentation. Un fait déduit de
 * croyances périmées est faux POUR DE BONNES RAISONS.
 * L'incertitude est un fait de premier rang (ennemiLocalise, partInconnue).
 * La situation porte aussi quelques REQUÊTES (fermées sur la couverture) —
 * les faits scalaires seuls s'affichent dans la viz état-major.
 */

import { capDeDirection } from '../../langage/resoudre-lieu.js';

/**
 * LA LIGNE DE BARRAGE — pure géométrie, aucun mot « pont » nulle part : une
 * ligne candidate est un segment ⊥ à l'axe de menace, posé à une distance d
 * devant l'unité ; sur ce segment, la carte CONNUE (le pays où l'on se bat)
 * bouche gratuitement ; les TROUS sont ce qu'il reste à couvrir d'hommes.
 * Qualité = (ma largeur de front / trous, plafonnée à 1) × un déclin doux
 * avec la distance. Le goulot gagne mécaniquement.
 * @returns {{centre, trous, qualite}|null}
 */
function chercherMeilleureLigne({ depuis, capMenace, zone, carte, allies, largeurFront, params }) {
  if (!depuis || capMenace === null) return null;
  const u = { x: Math.cos(capMenace), y: Math.sin(capMenace) };
  const lat = { x: -u.y, y: u.x };
  const dansObstacle = (q) =>
    carte.some((o) => q.x >= o.x && q.x <= o.x + o.largeur && q.y >= o.y && q.y <= o.y + o.hauteur);
  // les ALLIÉS CRUS bouchent aussi : une bande amie tient déjà ce morceau de
  // ligne — c'est ce qui fait que deux commandants se COMPLÈTENT (la relève
  // se poste derrière, le trou rouvert se rebouche) sans se parler
  const dansAllie = (q) =>
    allies.some((a) => Math.hypot(q.x - a.pos.x, q.y - a.pos.y) <= a.rayon);
  const dansZone = (q) =>
    q.x >= zone.x && q.x <= zone.x + zone.largeur && q.y >= zone.y && q.y <= zone.y + zone.hauteur;

  const { pasAvant, porteeScan, demiLargeur, pasLateral, declinDistance } = params.barrage;
  let meilleure = null;
  for (let dist = 0; dist <= porteeScan; dist += pasAvant) {
    const c0 = { x: depuis.x + u.x * dist, y: depuis.y + u.y * dist };
    // les intervalles LIBRES du segment (hors zone et obstacles = bouché)
    let trous = 0;
    let plusGrand = null;
    let debut = null;
    for (let t = -demiLargeur; t <= demiLargeur + 1e-9; t += pasLateral) {
      const q = { x: c0.x + lat.x * t, y: c0.y + lat.y * t };
      const libre = dansZone(q) && !dansObstacle(q) && !dansAllie(q);
      if (libre && debut === null) debut = t;
      if ((!libre || t + pasLateral > demiLargeur) && debut !== null) {
        const fin = libre ? t : t - pasLateral;
        const long = fin - debut;
        trous += long;
        if (!plusGrand || long > plusGrand.long) plusGrand = { debut, fin, long };
        debut = null;
      }
    }
    if (!plusGrand) continue;
    const qualite =
      Math.min(1, largeurFront / Math.max(0.7, trous)) * (1 / (1 + dist / declinDistance));
    if (!meilleure || qualite > meilleure.qualite) {
      const milieu = (plusGrand.debut + plusGrand.fin) / 2;
      meilleure = {
        centre: { x: c0.x + lat.x * milieu, y: c0.y + lat.y * milieu },
        trous,
        qualite,
      };
    }
  }
  return meilleure;
}

/**
 * @param {ReturnType<import('../../representation.js').creerRepresentation>} representation
 * @param {{zone: {x,y,largeur,hauteur}, drill: {ordreDrill: number[]}, carte: Array}} contexte
 *   — carte : les obstacles CONNUS (on connaît le pays où l'on se bat, seedé)
 * @param {Object} params
 */
export function estimerSituation(representation, { zone, drill, carte = [], tire = false }, params) {
  const unite = representation.tasCru('unite');
  const ennemis = representation.tasCru('ennemis');
  // la rumeur peut porter une DIRECTION (« ils sont à l'est ») — elle biaise
  // le choix des secteurs sans jamais interdire les autres
  const capRumeur = ennemis?.direction != null ? capDeDirection(ennemis.direction) : null;
  const couverture = representation.couverture;
  const moi = representation.moi;
  // l'effectif ATTENDU : le drill seedé MOINS les morts vus (croyance) —
  // une unité à 6 vivants ne s'épuise plus à viser une formation de 12
  const effectifDrill = Math.max(1, representation.attendu('unite'));
  const partInconnue = couverture ? couverture.partInconnue(zone) : 0;

  const faits = {
    posture: representation.posture,
    ennemiEnMemoire: !!ennemis,
    ennemiLocalise: !!ennemis?.barycentre && ennemis.ageS < params.commandement.fraicheurEnnemi,
    // la mêlée SE VOIT : un adverse cru à portée d'armes de MOI (le chef)
    auContact: representation
      .contactsCrus()
      .some((c) => c.livree && representation.maLivree && c.livree !== representation.maLivree),
    uniteAvecMoi: !!unite && unite.ageS < 6,
    uniteFormee:
      !!unite &&
      (unite.formeEffectif ?? 0) >= effectifDrill / 2 &&
      (unite.nettete ?? 0) >= params.perception.forme.netteteMin,
    uniteDispersee: !unite || unite.ageS > 8,
    partInconnueDeLaZone: partInconnue,
    partInconnueRestante: partInconnue > params.commandement.seuilInconnue,
    // le chef porte l'arc de son unité (l'équipement est un savoir sur soi) —
    // le fer tient et charge, l'arc harcèle : la doctrine se lit dans les
    // applicabilités, jamais dans un if de l'arbitre
    uniteTire: tire,
    uniteAuFer: !tire,
  };
  faits.ennemiNonLocalise = faits.ennemiEnMemoire && !faits.ennemiLocalise;
  // la distance crue à l'ennemi localisé — le harcèlement s'y règle
  {
    const p = unite?.barycentre ?? moi.pos;
    faits.distanceEnnemie =
      faits.ennemiLocalise && p
        ? Math.hypot(ennemis.barycentre.x - p.x, ennemis.barycentre.y - p.y)
        : null;
    faits.ennemiTropPres =
      faits.distanceEnnemie !== null && faits.distanceEnnemie < params.harcelement.pres;
  }

  // l'axe de menace : l'ennemi cru, sinon la rumeur — partagé par la ligne,
  // l'exposition, la charge
  const depuisUnite = unite?.barycentre ?? moi.pos;
  const capMenace =
    ennemis?.barycentre && depuisUnite
      ? Math.atan2(ennemis.barycentre.y - depuisUnite.y, ennemis.barycentre.x - depuisUnite.x)
      : capRumeur;
  // la bande amie crue : le tas anonyme de MA livrée, frais
  const bande = representation.tasCru('inconnu');
  const bandeAmie =
    bande?.barycentre && bande.livree === representation.maLivree && bande.ageS < 12 ? bande : null;

  // mémo : la ligne est demandée par plusieurs consommateurs d'une même
  // délibération (géométries, poste, viz) — un seul scan
  let ligneMemo;

  return {
    ...faits,
    capMenace, // l'axe partagé (ennemi cru, sinon rumeur) — un fait, la viz le dessine
    // requêtes (non affichées) — fermées sur les croyances
    positionEnnemie: ennemis?.barycentre ?? null,
    // la forme ennemie CRUE (cap + largeur perçus), si leur ligne se lit —
    // c'est elle qui ouvre les débordements (charger par la gauche/droite)
    formeEnnemie:
      ennemis?.cap !== undefined && ennemis.largeur && ennemis.ageS < params.commandement.fraicheurEnnemi
        ? { cap: ennemis.cap, largeur: ennemis.largeur }
        : null,
    margeDebord: params.commandement.margeDebord,
    qualiteDebord: params.commandement.qualiteDebord,
    desordreDebord: params.commandement.desordreDebord,
    distanceStandoff: params.harcelement.standoff, // la fenêtre de tir (harceler)
    positionUnite: depuisUnite,
    moiPos: moi.pos,
    aireZone: zone.largeur * zone.hauteur,
    /**
     * De combien ce point me porterait DEVANT la bande amie crue (m, ≥ 0),
     * projeté sur l'axe de menace — être devant les siens, c'est être exposé
     * SEUL : c'est ce qui fait avancer un camp EN LIGNE, sans un mot. Sans
     * bande amie crue : 0 (seul au monde, la question ne se pose pas).
     */
    avanceSurAllies: (point) => {
      if (!bandeAmie || capMenace === null || !point) return 0;
      return Math.max(
        0,
        (point.x - bandeAmie.barycentre.x) * Math.cos(capMenace) +
          (point.y - bandeAmie.barycentre.y) * Math.sin(capMenace)
      );
    },
    // la meilleure ligne de barrage entre moi et la menace (l'axe : l'ennemi
    // cru, sinon la rumeur) — consommée par tenir, dessinée par l'état-major
    meilleureLigne: () => {
      if (ligneMemo === undefined) {
        ligneMemo = chercherMeilleureLigne({
          depuis: depuisUnite,
          capMenace,
          zone,
          carte,
          // la bande amie tient déjà son morceau de ligne (V1 : la plus proche)
          allies: bandeAmie
            ? [{ pos: bandeAmie.barycentre, rayon: Math.max(1.5, bandeAmie.etendue) }]
            : [],
          largeurFront: (drill.forme?.largeur ?? 6) * (drill.forme?.espacementLateral ?? 1.2),
          params,
        });
      }
      return ligneMemo;
    },
    prochainSecteurVierge: () =>
      couverture && (unite?.barycentre ?? moi.pos)
        ? couverture.prochainSecteurVierge(
            unite?.barycentre ?? moi.pos,
            zone,
            capRumeur !== null ? { cap: capRumeur, poids: params.ratissage.biaisDirection } : null
          )
        : null,
    estCouverte: (pos) => (couverture ? couverture.estCouverte(pos) : false),
  };
}

/**
 * Les CRITÈRES de phases (succès/échec/répétition) — des noms, jamais du
 * code inline dans les manœuvres. (situation, engagement) → bool.
 */
export const CRITERES = {
  toujours: () => true,
  jamais: () => false, // la phase sans fin : tenir tient
  uniteFormee: (s) => s.uniteFormee,
  uniteDispersee: (s) => s.uniteDispersee,
  partInconnueRestante: (s) => s.partInconnueRestante,
  contactSubi: (s) => s.ennemiLocalise, // trouver l'ennemi INTERROMPT le ratissage
  auContact: (s) => s.auContact,
  ennemiPerdu: (s) => !s.ennemiLocalise,
  ennemiTropPres: (s) => s.ennemiTropPres,
  secteurCouvert: (s, engagement) =>
    !engagement?.destination || s.estCouverte(engagement.destination),
};
