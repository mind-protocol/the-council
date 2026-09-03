/**
 * COMPOSER — la sim complète, sans 🖥️ Présentation.
 *
 * Reflet de `src/main.js` : même câblage, moins l'écran. Il vivait dans
 * coding/fumee.mjs ; il en sort parce que TROIS outils s'en servent
 * maintenant (fumée, banc de sauvegarde, vision ascii) et qu'une copie de plus
 * aurait été une seconde vérité sur le câblage.
 *
 * Si main.js change de câblage, tout ce qui est ici casse bruyamment — c'est
 * voulu, ça se met à jour avec.
 */

import { creerRng } from '../src/infra/rng.js';
import { creerMonde } from '../src/monde/expose.js';
import { creerCognition } from '../src/cognition/expose.js';
import { creerSoldat } from '../src/cognition/brains/soldat/brain.js';
import { creerCommandant } from '../src/cognition/brains/commandant/brain.js';
import { LIVRE_DE_MANOEUVRES } from '../src/cognition/doctrine/manoeuvres/livre.js';
import { creerAction } from '../src/action/expose.js';
import { creerPhysique } from '../src/physique/expose.js';
import { creerOrchestration } from '../src/orchestration/expose.js';
import { creerSocial } from '../src/social/expose.js';
import { creerCorps } from '../src/corps/expose.js';
import { PARAMS } from '../src/params.js';
import { creerOiseau } from '../src/cognition/brains/oiseau/brain.js';
import { OISEAUX } from '../src/corps/oiseaux.js';
import { pathToFileURL } from 'node:url';

/** @returns la sim complète, sans 🖥️. */
export function composer(scenario, ressources = {}) {
  const rng = creerRng(scenario.seed);

  const monde = creerMonde({ tailleCaseIndex: PARAMS.tailleCaseIndex });
  scenario.maisons.forEach((m) => monde.poserObstacle(m));
  if (ressources.masque) monde.poserMasque(ressources.masque);

  const social = creerSocial();
  const corpsContainer = creerCorps({ params: PARAMS });

  const action = creerAction({
    navgrid: monde.navgrid,
    corpsParId: monde.corpsParId,
    signalerEchec: () => {},
    coutEffort: (id, effortS) => corpsContainer.coutEffort(id, effortS),
    subirCoup: (id, coup) => corpsContainer.subirCoup(id, coup),
    estVivant: corpsContainer.estVivant,
    facteurVitesseDe: corpsContainer.facteurVitesseDe,
    armeDe: corpsContainer.armeDe,
    bouclierDe: corpsContainer.bouclierDe,
    arcTirDe: corpsContainer.arcTirDe,
    montureDe: monde.montureDe,
    // le train demande ('pas'|'trot'|'galop') choisit l'allure de la monture ; trot par defaut
    vitesseMaxDe: (id, train) => (monde.montureDe(id) != null ? PARAMS.cheval.allures[train ?? 'trot'] ?? PARAMS.cheval.allures.trot : PARAMS.vitesseMax),
    puiserFleche: corpsContainer.puiserFleche,
    oiseauDe: corpsContainer.oiseauDe,
    rng,
    voisinsDans: monde.voisinsDans,
    params: PARAMS,
  });

  const cognition = creerCognition({
    emettreIntention: action.assigner,
    emettreOrientation: action.orienter,
    emettrePosture: action.poserPosture,
    // pas d'emettreParole : headless, les paroles tombent dans le vide —
    // les tirages rng, eux, ont lieu quand même (déterminisme du déroulé)
    estVivant: corpsContainer.estVivant,
    vuePerception: {
      posDe: (id) => {
        const c = monde.corpsParId(id);
        return { x: c.pos.x, y: c.pos.y, z: c.vol?.z ?? 0 }; // on sait où l'on est, altitude comprise
      },
      velDe: (id) => {
        const c = monde.corpsParId(id);
        return { x: c.vel.x, y: c.vel.y };
      },
      autourDe: (id, rayon) =>
        monde.voisinsDans(monde.corpsParId(id).pos, rayon).filter((v) => v.id !== id),
      // l'horizon de masse regroupe LE MONDE une fois pour tous (percevoir.js) :
      // le snapshot entier, les mêmes fiches qu'autourDe (z, allure aplatis)
      tous: () => monde.corpsVus(),
    },
    rng,
    params: PARAMS,
  });

  const physique = creerPhysique({
    corps: monde.corps,
    obstaclesPres: monde.terrain.obstaclesPres,
    appliquerIntegration: monde.appliquerIntegration,
    vitessesDesirees: action.vitessesDesirees,
    volsDesires: action.volsDesires,
    orientationsDesirees: action.orientationsDesirees,
    posturesDesirees: action.posturesDesirees,
    armeDe: corpsContainer.armeDe,
    montureDe: monde.montureDe,
    desatteler: monde.desatteler,
    subirChoc: corpsContainer.subirChoc,
    params: PARAMS,
  });

  const orchestration = creerOrchestration({
    dtFixe: PARAMS.dtFixe,
    phases: [
      { nom: 'perception', executer: (dt) => cognition.phasePerception(dt) },
      { nom: 'decision', executer: (dt) => cognition.phaseDecision(dt) },
      { nom: 'action', executer: (dt) => action.phaseAction(dt) },
      { nom: 'physique', executer: (dt) => physique.phasePhysique(dt) },
      { nom: 'physiologie', executer: (dt) => corpsContainer.phasePhysiologie(dt) },
      { nom: 'index', executer: () => monde.reconstruireIndex() },
    ],
  });

  // par UNITE, reflet de main.js
  // la masse est une distribution : chacun son gabarit
  const tirerMasseCheval = () =>
    Math.max(PARAMS.cheval.masse.minKg, rng.normale(PARAMS.cheval.masse.moyenneKg, PARAMS.cheval.masse.ecartTypeKg));
  // l'unite montee : un cheval sous chaque homme, attele au spawn
  const monter = (idCavalier, pos, livree) => {
    const idCheval = monde.spawn({ pos: { x: pos.x, y: pos.y }, rayon: PARAMS.cheval.rayon, masse: tirerMasseCheval(), gabarit: 'cheval', livree, nom: 'un cheval' });
    if (idCheval == null) return;
    corpsContainer.enregistrer(idCheval, { arme: 'aucune' });
    monde.atteler(idCavalier, idCheval);
  };
  const tirerMasse = () => Math.max(PARAMS.masseHomme.minKg, rng.normale(PARAMS.masseHomme.moyenneKg, PARAMS.masseHomme.ecartTypeKg));
  const chargerUnite = (u) => {
    const idChef = monde.spawn({ pos: u.chef.pos, rayon: PARAMS.rayonHomme, masse: tirerMasse(), livree: u.livree, nom: u.chef.nom, panache: true, cap: u.capInitial ?? 0 });
    const ids = u.hommes.map((h) =>
      monde.spawn({ pos: h.pos, rayon: PARAMS.rayonHomme, masse: tirerMasse(), livree: u.livree, nom: h.nom, cap: u.capInitial ?? 0 })
    );
    const membres = [idChef, ...ids];
    membres.forEach((id) => corpsContainer.enregistrer(id, u.equipement));
    if (u.monture) membres.forEach((id) => monter(id, monde.corpsParId(id).pos, u.livree));
    const uid = social.unites.creer({ nom: u.nom, chef: idChef, ordreDrill: membres, forme: u.forme });
    const unite = social.unites.obtenir(uid);
    const drill = { ordreDrill: unite.ordreDrill, forme: unite.forme };
    const noms = [
      { id: idChef, nom: u.chef.nom },
      ...u.hommes.map((h, i) => ({ id: ids[i], nom: h.nom })),
    ];
    const attacherSoldat = (id, amisIds) => {
      cognition.attacher(id, {
        connaissance: { noms, amisIds, uniteIds: membres.filter((x) => x !== id), chefId: idChef, chefCru: { pos: u.chef.pos, cap: u.capInitial ?? 0 }, maLivree: u.livree, posture: u.posture },
        fabriqueBrain: ({ representation, dire }) =>
          creerSoldat({ rng, representation, zone: u.zone, drill, params: PARAMS, souffleDe: corpsContainer.souffleDe, blessuresDe: corpsContainer.blessuresDe, arcTirDe: corpsContainer.arcTirDe, flechesDe: corpsContainer.flechesDe, armeDe: corpsContainer.armeDe, montureDe: monde.montureDe, dire }),
      });
    };
    // le chef est un COMMANDANT (miroir de main.js, sans les bulles) —
    // SAUF si le scenario dit sansCommandant : un panache qui mene du front,
    // pas d'etat-major (les scenarios-laboratoire testent UNE mecanique ;
    // l'arbitre n'ecrase pas l'ordre injecte au lever de rideau)
    const emettreOrdre = (ordre) => {
      membres.forEach((id) => cognition.injecterOrdre(id, { ordre, emetteur: idChef }));
    };
    if (u.sansCommandant) {
      attacherSoldat(idChef, []);
    } else cognition.attacher(idChef, {
      connaissance: {
        noms,
        amisIds: [],
        uniteIds: membres.filter((x) => x !== idChef),
        chefId: idChef,
        maLivree: u.livree,
        posture: u.posture,
        croyancesTas: u.memoire?.ennemis
          ? [{ etiquette: 'ennemis', effectif: u.memoire.ennemis.effectif, direction: u.memoire.ennemis.direction, pos: u.memoire.ennemis.pos }]
          : [],
      },
      fabriqueBrain: ({ representation, dire }) =>
        creerCommandant({
          rng,
          representation,
          dire,
          souffleDe: corpsContainer.souffleDe,
          blessuresDe: corpsContainer.blessuresDe,
          armeDe: corpsContainer.armeDe,
          arcTirDe: corpsContainer.arcTirDe,
          flechesDe: corpsContainer.flechesDe,
          zone: scenario.zone, // le commandant raisonne sur le THÉÂTRE, pas la zone de flânerie
          drill,
          params: PARAMS,
          manoeuvres: LIVRE_DE_MANOEUVRES,
          emettreOrdre,
          carte: scenario.maisons, // on connait le pays ou l on se bat
        }),
    });
    u.hommes.forEach((h, i) => {
      const amisIds = u.hommes
        .map((autre, j) => ({ autre, j }))
        .filter(({ autre, j }) => j !== i && autre.escouade === h.escouade)
        .map(({ j }) => ids[j]);
      attacherSoldat(ids[i], amisIds);
    });
    if (u.ordreInitial === 'surMoi') {
      emettreOrdre({ verbe: 'EN_FORMATION', sur: { type: 'locuteur' } });
    }
    // l'assaut ordonne AVANT le lever de rideau (LA_VOLEE : la traversee)
    if (u.ordreInitial === 'ratisser') {
      emettreOrdre({ verbe: 'RATISSER', vers: { type: 'direction', nom: u.memoire?.ennemis?.direction ?? 'est' } });
    }
    // la charge sonnee avant le lever de rideau (LA_CONROI)
    if (u.ordreInitial === 'charger') {
      emettreOrdre({ verbe: 'CHARGER', vers: { type: 'direction', nom: u.memoire?.ennemis?.direction ?? 'est' } });
    }
    return { idChef, membres };
  };
  const unites = scenario.unites.map(chargerUnite);
  const tous = unites.flatMap((u) => u.membres);

  // les OISEAUX du scenario (reflet de main.js) : corps volant + profil + brain
  const idsOiseaux = [];
  for (const o of scenario.oiseaux ?? []) {
    const profil = OISEAUX[o.profil];
    if (!profil) throw new Error(`scenario : oiseau inconnu '${o.profil}'`);
    const id = monde.spawn({
      pos: { x: o.pos.x, y: o.pos.y },
      rayon: profil.longueur / 2,
      masse: profil.masse,
      gabarit: 'oiseau',
      livree: o.livree,
      nom: o.nom ?? profil.nom,
      cap: o.cap ?? 0,
      vol: { z: o.z ?? profil.altitudeRalliement, vitesseAir: profil.croisiere },
    });
    if (id === null) continue;
    idsOiseaux.push(id);
    corpsContainer.enregistrer(id, { arme: 'aucune', oiseau: o.profil });
    cognition.attacher(id, {
      connaissance: { maLivree: o.livree },
      fabriqueBrain: ({ representation }) =>
        creerOiseau({
          rng,
          representation,
          velDe: () => {
            const c = monde.corpsParId(id);
            return { x: c.vel.x, y: c.vel.y };
          },
          zone: scenario.zone,
          profil,
          params: PARAMS,
        }),
    });
  }
  monde.reconstruireIndex();

  // `rng` sort avec le reste : sans son etat, un monde relu repart du hasard
  // du premier jour et le deroule diverge (mesure : 60 corps sur 60).
  return { monde, cognition, action, physique, corpsContainer, orchestration, tous, unites, oiseaux: idsOiseaux, rng };
}

