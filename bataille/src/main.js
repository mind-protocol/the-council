/**
 * Bootstrap — le SEUL fichier qui connaît tous les containers. Compose par
 * injection (aucun container n'en importe un autre), charge le scénario,
 * possède la boucle de frame (seul contact avec le temps réel avec l'horloge).
 */

import { creerRng } from './infra/rng.js';
import { creerMonde } from './monde/expose.js';
import { creerCognition } from './cognition/expose.js';
import { creerSoldat } from './cognition/brains/soldat/brain.js';
import { creerCommandant } from './cognition/brains/commandant/brain.js';
import { LIVRE_DE_MANOEUVRES } from './cognition/doctrine/manoeuvres/livre.js';
import { creerGregaire } from './cognition/brains/gregaire/brain.js';
import { creerOiseau } from './cognition/brains/oiseau/brain.js';
import { OISEAUX } from './corps/oiseaux.js';
import { creerAction } from './action/expose.js';
import { creerPhysique } from './physique/expose.js';
import { creerOrchestration } from './orchestration/expose.js';
import { creerPresentation } from './presentation/expose.js';
import { creerSocial } from './social/expose.js';
import { enFormation, ratisser, repos, enTexte } from './social/ordres.js';
import { allerA } from './cognition/intentions.js';
import { creerCorps } from './corps/expose.js';
import { PARAMS } from './params.js';
import { SCENARIOS } from './scenarios/index.js';
import { chargerMondeEtat } from './scenarios/monde-etat.js';
import { sauver as sauverPartie, charger as chargerPartie } from './partie.js';

/**
 * Compose et lance UNE sim complète.
 * @param {HTMLElement} racine @param {Object} scenario
 * @param {{liste, actif, choisir}} [scenarios] — le catalogue pour le sélecteur (🖥️)
 * @param {{masque?: Object, plan?: Object}} [ressources] — les données du
 *   terrain déclaré par le scénario, DÉJÀ chargées (le bootstrap charge,
 *   demarrer compose — la composition reste synchrone)
 * @param {{habillage?: boolean}} [opts] — `habillage: false` = la carte seule.
 * @returns {{arreter: () => void}} — coupe la boucle de frame (rechargement)
 */
export function demarrer(racine, scenario, scenarios, ressources = {}, { habillage = true } = {}) {
  const rng = creerRng(scenario.seed);

  // 🌍 — la feuille du graphe, en premier
  const monde = creerMonde({ tailleCaseIndex: PARAMS.tailleCaseIndex });
  scenario.maisons.forEach((m) => monde.poserObstacle(m));
  if (ressources.masque) monde.poserMasque(ressources.masque);

  const social = creerSocial(); // 📯
  const corpsContainer = creerCorps({ params: PARAMS }); // ❤️ (stub : lance par défaut)

  // 🏃 ← vues du 🌍
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

  // 🧠 ← puits d'intentions vers 🏃, vue perception sur le snapshot 🌍
  const cognition = creerCognition({
    emettreIntention: action.assigner,
    emettreOrientation: action.orienter,
    emettrePosture: action.poserPosture,
    // la parole flavor se VOIT (bulles 🖥️) ; demain elle PORTERA (📯)
    emettreParole: (id, texte, dureeS) => presentation.dire(id, texte, dureeS),
    estVivant: corpsContainer.estVivant,
    vuePerception: {
      posDe: (id) => {
        const c = monde.corpsParId(id);
        return { x: c.pos.x, y: c.pos.y, z: c.vol?.z ?? 0 }; // on sait où l'on est, altitude comprise
      },
      velDe: (id) => {
        const c = monde.corpsParId(id);
        return { x: c.vel.x, y: c.vel.y }; // proprioception
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

  // ⚙️ ← vues 🌍 + 🏃, commande d'écriture 1/2
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
    voisinsDans: monde.voisinsDans, // l'acoustique : qui est a portee d'une voix
    params: PARAMS,
  });

  // ⏱️ — l'ordre des phases est une décision d'archi
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

  // ── Chargement : par UNITÉ — spawns, connaissances seedées, brains.
  // Personne ne connaît personne d'un camp à l'autre : l'« ennemi » n'est
  // pas un tag, ce sera une croyance (🧠) le jour où on se percevra.
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
    // `personnage` : la fiche du jeu que ce corps incarne (registre.js) — le scenario l'affecte, le moteur la porte
    const idChef = monde.spawn({ pos: u.chef.pos, rayon: PARAMS.rayonHomme, masse: tirerMasse(), livree: u.livree, nom: u.chef.nom, panache: true, cap: u.capInitial ?? 0, personnage: u.chef.personnage ?? null });
    const ids = u.hommes.map((h) =>
      monde.spawn({ pos: h.pos, rayon: PARAMS.rayonHomme, masse: tirerMasse(), livree: u.livree, nom: h.nom, cap: u.capInitial ?? 0, personnage: h.personnage ?? null })
    );
    const membres = [idChef, ...ids];
    membres.forEach((id) => corpsContainer.enregistrer(id, u.equipement)); // lance par défaut
    if (u.monture) membres.forEach((id) => monter(id, monde.corpsParId(id).pos, u.livree));

    const uid = social.unites.creer({ nom: u.nom, chef: idChef, ordreDrill: membres, forme: u.forme });
    const unite = social.unites.obtenir(uid);
    const drill = { ordreDrill: unite.ordreDrill, forme: unite.forme }; // savoir mémorisé
    const noms = [
      { id: idChef, nom: u.chef.nom },
      ...u.hommes.map((h, i) => ({ id: ids[i], nom: h.nom })),
    ];

    const attacherSoldat = (id, amisIds) => {
      cognition.attacher(id, {
        connaissance: {
          noms,
          amisIds,
          uniteIds: membres.filter((x) => x !== id),
          chefId: idChef,
          chefCru: { pos: u.chef.pos, cap: u.capInitial ?? 0 }, // le rassemblement se sait
          maLivree: u.livree,
          posture: u.posture, // la doctrine descend jusqu au rang
        },
        fabriqueBrain: ({ representation, dire }) =>
          creerSoldat({ rng, representation, zone: u.zone, drill, params: PARAMS, souffleDe: corpsContainer.souffleDe, blessuresDe: corpsContainer.blessuresDe, arcTirDe: corpsContainer.arcTirDe, flechesDe: corpsContainer.flechesDe, armeDe: corpsContainer.armeDe, montureDe: monde.montureDe, dire }),
      });
    };
    // le chef est un COMMANDANT : l'homme (soldat) + le rôle (état-major),
    // qui parle à son unité — échafaudage d'émission, puis Transmission 📯
    const emettreOrdre = (ordre) => {
      membres.forEach((id) => cognition.injecterOrdre(id, { ordre, emetteur: idChef }));
      presentation.dire(idChef, enTexte(ordre));
    };
    // SANS COMMANDANT (scénario-laboratoire) : le chef est un panache qui
    // mène du front — pas d'état-major, l'ordre du lever de rideau tient
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

    // ordre initial du scenario (FACE_A_FACE : les lignes tiennent des le depart)
    if (u.ordreInitial === 'surMoi') {
      const ordre = enFormation({ type: 'locuteur' });
      membres.forEach((id) => cognition.injecterOrdre(id, { ordre, emetteur: idChef }));
    }
    // l'assaut ordonné AVANT le lever de rideau (LA_VOLEE : la traversée) —
    // la direction vient de la rumeur seedée de l'unité
    if (u.ordreInitial === 'ratisser') {
      const ordre = ratisser({ type: 'direction', nom: u.memoire?.ennemis?.direction ?? 'est' });
      membres.forEach((id) => cognition.injecterOrdre(id, { ordre, emetteur: idChef }));
    }
    // la charge sonnee avant le lever de rideau (LA_CONROI)
    if (u.ordreInitial === 'charger') {
      const ordre = { verbe: 'CHARGER', vers: { type: 'direction', nom: u.memoire?.ennemis?.direction ?? 'est' } };
      membres.forEach((id) => cognition.injecterOrdre(id, { ordre, emetteur: idChef }));
    }

    return { idChef, membres };
  };
  const unites = scenario.unites.map(chargerUnite);

  // ── LES OISEAUX du scénario : des corps volants (vol au registre), leur
  // profil porté (❤️), leur brain — hors du jeu des unités (ni drill, ni
  // forme). Ils ne touchent personne : ils volent au-dessus, c'est tout ──
  const chargerOiseau = (o) => {
    const profil = OISEAUX[o.profil];
    if (!profil) throw new Error(`scenario : oiseau inconnu '${o.profil}'`);
    const id = monde.spawn({
      pos: { x: o.pos.x, y: o.pos.y },
      rayon: profil.longueur / 2, // l'encombrement cliquable de l'ombre
      masse: profil.masse,
      gabarit: 'oiseau',
      livree: o.livree,
      nom: o.nom ?? profil.nom,
      cap: o.cap ?? 0,
      vol: { z: o.z ?? profil.altitudeRalliement, vitesseAir: profil.croisiere },
    });
    if (id === null) return null;
    corpsContainer.enregistrer(id, { arme: 'aucune', oiseau: o.profil });
    cognition.attacher(id, {
      connaissance: { maLivree: o.livree },
      fabriqueBrain: ({ representation }) =>
        creerOiseau({
          rng,
          representation,
          // proprioception : ma vitesse (le cap du vol s'en dérive)
          velDe: () => {
            const c = monde.corpsParId(id);
            return { x: c.vel.x, y: c.vel.y };
          },
          zone: scenario.zone,
          profil,
          params: PARAMS,
        }),
    });
    return id;
  };
  for (const o of scenario.oiseaux ?? []) chargerOiseau(o);
  monde.reconstruireIndex(); // premier snapshot

  // ÉCHAFAUDAGE — l'ordre (du TEXTE, format 📯) injecté en direct dans les
  // représentations ; demain il passera par la Transmission (voix, portée).
  // Les boutons parlent pour le chef de la PREMIÈRE unité (la nôtre).
  const notreUnite = unites[0];
  let modeActif = 'repos';
  const ordres = {
    donnerOrdre(mode) {
      modeActif = mode;
      const ordre =
        mode === 'surMoi' ? enFormation({ type: 'locuteur' })
        : mode === 'nu' ? enFormation()
        : repos();
      notreUnite.membres.forEach((id) => cognition.injecterOrdre(id, { ordre, emetteur: notreUnite.idChef }));
      // l'ordre se VOIT : le chef le crie (bulle = viz de la comm à venir)
      presentation.dire(notreUnite.idChef, enTexte(ordre));
    },
    modeActif: () => modeActif,
  };

  // Spawn drag & drop : homme sans unité → grégaire
  const spawnHomme = (pos) => {
    const id = monde.spawn({ pos, rayon: PARAMS.rayonHomme, masse: tirerMasse(), livree: 'bleu', nom: 'un inconnu' });
    if (id === null) return null;
    corpsContainer.enregistrer(id);
    cognition.attacher(id, {
      connaissance: { maLivree: 'bleu' },
      fabriqueBrain: ({ representation, dire }) =>
        creerGregaire({ rng, representation, zone: scenario.zone, params: PARAMS, dire }),
    });
    return id;
  };

  // 🖥️ ← vues de tous, commandes explicites
  const presentation = creerPresentation({
    vuesMonde: {
      corps: monde.corps,
      corpsParId: monde.corpsParId,
      terrain: monde.terrain,
      navgridDebug: monde.navgridDebug,
      indexDebug: monde.indexDebug,
      montureDe: monde.montureDe, // qui est en selle : le cavalier tient les rênes
    },
    vuesCorps: { equipementDe: corpsContainer.equipementDe, blessuresDe: corpsContainer.blessuresDe, souffleDe: corpsContainer.souffleDe, oiseauDe: corpsContainer.oiseauDe },
    cheminsDebug: action.cheminsPourDebug,
    refusDebug: action.refusPourDebug,
    coupsDebug: action.coupsPourDebug,
    forcesDebug: physique.forcesDebug,
    introspecter: cognition.introspecter,
    perceptionDebug: cognition.perceptionDebug,
    formationDebug: cognition.formationDebug,
    orientationDebug: cognition.orientationDebug,
    couvertureDebug: cognition.couvertureDebug,
    etatMajorDebug: cognition.etatMajorDebug,
    transport: orchestration.transport,
    ordres,
    // LE PJ — pour l'instant, le chef de notre unite. Le clic droit lui dit
    // ou aller ; la camera le suit. `piloter` court-circuite sa tete pour la
    // seule question « ou je vais » : il continue de voir, de craindre et de
    // parler (voir cognition.piloter).
    pj: {
      id: notreUnite.idChef,
      allerA: (pos) => {
        cognition.piloter(notreUnite.idChef, allerA(pos));
        presentation.dire(notreUnite.idChef, 'Par ici !');
      },
    },
    scenarios,
    spawn: spawnHomme,
    plan: ressources.plan ?? null, // le plan cuit (viz du calque terrain)
    habillage,
  });
  presentation.monter(racine);

  // Boucle de frame — seul endroit qui touche requestAnimationFrame
  let vivant = true;
  let derniere = performance.now();
  // BORNE ANTI-SPIRALE (temps reel) : sous surcharge (une grande melee), un
  // tick coute plus que 16 ms, la boucle prend du retard — et sans borne elle
  // le RATTRAPE en empilant des sous-ticks, ce qui la fait ramer plus, qui
  // ajoute du retard : la spirale de la mort, vue a 1 fps par a-coups de 0,5 s.
  // On borne donc le temps reel avance par frame : sous surcharge le monde
  // RALENTIT en douceur (slow-mo lisse) au lieu de sauter. Un onglet qui se
  // reveille tombe ici aussi (on jette le retard, on ne rejoue pas la sieste).
  // Le headless (fumee) appelle orchestration.avancer() en direct, hors d'ici.
  // UN seul pas fixe par frame sous surcharge : a 1600+ corps un tick coute
  // ~90 ms (bien plus que 16), alors rattraper en enchainant 3 sous-ticks
  // faisait 280 ms/frame (~3 fps par a-coups). Borne a un pas -> le monde
  // RALENTIT en douceur (~10 fps lisses au lieu du stutter). Quand les ticks
  // sont bon marche (petite melee), on tourne a 60 fps temps reel : la borne
  // ne mord qu'en surcharge. `dtFixe*1000 * 1.2` = juste au-dessus d'un pas.
  const PLAFOND_FRAME_MS = (PARAMS.dtFixe ?? 1 / 60) * 1000 * 1.2;
  const frame = (t) => {
    if (!vivant) return;
    orchestration.avancer(Math.min(t - derniere, PLAFOND_FRAME_MS));
    derniere = t;
    presentation.rendre();
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);

  // ── SAUVER / CHARGER (docs/sauvegarde.md, bataille/docs/sauvegarde.md)
  //
  // `sauver()` rend un instantane : de la donnee plate, JSON-able, sans une
  // seule reference vivante. `charger()` le reprend SUR LE MONDE COMPOSE —
  // les corps existent deja, les tetes sont deja attachees a leur semence.
  // Reprendre une partie depuis un fichier, c'est donc composer le scenario
  // puis appeler ceci, dans cet ordre, et jamais l'inverse.
  const pieces = { monde, corpsContainer, cognition, orchestration, rng };
  const sauver = () => sauverPartie(pieces, { titre: scenario.titre });
  const charger = (d) => chargerPartie(d, pieces);

  return { arreter: () => { vivant = false; }, sauver, charger,
           // ── DE QUOI CONDUIRE UN HOMME NOMME, ET LE TEMPS AVEC LUI.
           // La lecture existait deja (perception, hommes, et les vues ASCII
           // par-dessus) ; il n'y avait aucun moyen d'AGIR autrement qu'au clic
           // droit, et le clic droit ne parle qu'au chef de notre unite. Ces
           // trois-la ouvrent la boucle « je vois / je decide / j'ordonne » a
           // n'importe quel homme, donc a une conduite tenue de l'exterieur.
           //
           // `figer` coupe la boucle de frame SANS arreter la simulation : le
           // monde cesse d'avancer tout seul et n'avance plus que par `pas`.
           // C'est ce qui rend une poursuite jouable — sinon le temps file
           // pendant qu'on reflechit, et l'on decide toujours sur du perime.
           // C'est aussi le seul mode ou le monde avance pour qui ne recoit
           // pas d'images (un agent, un banc d'essai) : requestAnimationFrame
           // ne bat pas dans un onglet qui n'est pas compose.
           piloter: (id, pos) => cognition.piloter(id, allerA(pos)),
           figer: () => { vivant = false; },
           reprendre: () => {
             if (vivant) return;
             vivant = true;
             derniere = performance.now();
             requestAnimationFrame(frame);
           },
           // Un battement franc : on avance le monde de `ms` et on repeint.
           // Le temps reel n'entre pas en compte — deux appels identiques
           // produisent le meme monde, ce que la boucle de frame ne garantit
           // jamais.
           pas: (ms = 250) => { orchestration.avancer(ms); presentation.rendre(); },
           // LA VOIX QUI PORTE (⚙️ acoustique) : les vivants a portee de ce
           // que cet homme dit, lui excepte — tout le monde a portee entend,
           // personne d'autre. Rien n'est envoye ici (outils/boite-parole.js).
           quiEntend: (idLocuteur, options = {}) => {
             const lui = monde.corpsParId(idLocuteur);
             if (!lui) throw new Error('quiEntend : locuteur inconnu ' + idLocuteur);
             return physique.quiEntend({ x: lui.pos.x, y: lui.pos.y }, options)
               .filter((id) => id !== idLocuteur && corpsContainer.estVivant(id))
               .map((id) => monde.corpsParId(id))
               .filter((c) => (c.gabarit ?? 'homme') === 'homme') // les chevaux entendent, mais ne sont personne
               .map((c) => ({ id: c.id, nom: c.nom, livree: c.livree, personnage: c.personnage ?? null }));
           },
           locuteur: () => notreUnite.idChef, // les boutons d'ordre parlent pour lui
           // LE CORPS D'UNE FICHE : celui que le scenario a affecte a ce personnage,
           // vivant ; null s'il n'est pas sur ce champ — et alors il n'y a pas de voix.
           corpsDe: (personnage) => {
             const c = Array.from(monde.corps()).find((x) => x.personnage === personnage && corpsContainer.estVivant(x.id));
             return c ? c.id : null;
           },
           // FAIRE PARLER UNE FICHE — une bulle sur le corps de ce personnage
           // (🖥️ presentation.dire). C'est par la qu'une reponse d'un homme
           // reveille se voit LA OU IL SE TIENT, dans la rue. Rend false s'il
           // n'a pas de corps sur ce champ : on ne fait pas parler un absent.
           dire: (personnage, texte, dureeS = 6) => {
             const c = Array.from(monde.corps()).find((x) => x.personnage === personnage && corpsContainer.estVivant(x.id));
             if (!c) return false;
             presentation.dire(c.id, texte, dureeS);
             return true;
           },
           // LES YEUX D'UN HOMME : ses croyances datees, jamais la verite
           // du registre. C'est par la que passe la vue ASCII subjective.
           perception: cognition.perceptionDebug,
           // `monde.corps()` rend un ITERATEUR, pas un tableau : Array.from,
           // sinon `.map` rend un iterator helper que JSON ne serialise pas.
           hommes: () => Array.from(monde.corps(), (c) => ({ id: c.id, nom: c.nom,
                          livree: c.livree, panache: c.panache, personnage: c.personnage ?? null })) };
}

/**
 * Charge les données du terrain déclaré par un scénario (masque + plan cuit),
 * servies par le serveur de dev (montage — voir outils/montages.mjs).
 * Sans champ `terrain` : rien à charger, rien à attendre.
 */
/**
 * L'ombrage du relief : `<id>.ombrage.png`, cuit au repère EXACT du plan
 * (mètre pour mètre, y vers le sud). Rendu comme une Image prête à peindre,
 * ou null. Une image qui manque ne bloque rien et ne se plaint pas.
 */
const chargerOmbrage = (cheminPlan) =>
  new Promise((resoudre) => {
    const src = '/' + cheminPlan.replace(/\.plan\.json$/, '.ombrage.png');
    if (src === '/' + cheminPlan) return resoudre(null);
    const img = new Image();
    img.onload = () => resoudre(img);
    img.onerror = () => resoudre(null);
    img.src = src;
  });

const chargerTerrain = async (terrain) => {
  if (!terrain) return {};
  const rep = await fetch('/' + terrain.masque.fichier);
  if (!rep.ok) throw new Error('masque introuvable : ' + terrain.masque.fichier);
  const bits = new Uint8Array(await rep.arrayBuffer());
  let plan = null;
  if (terrain.plan) {
    // le plan est la VIZ : son absence dégrade le calque, pas la sim —
    // mais elle se SIGNALE (une viz muette n'est pas une viz)
    const rp = await fetch('/' + terrain.plan);
    if (rp.ok) plan = await rp.json();
    else console.warn('plan cuit introuvable (calque terrain dégradé) : ' + terrain.plan);
    // L'OMBRAGE DU RELIEF, s'il a été cuit à côté du plan (07_ombrage.py).
    // Facultatif par construction : une carte sans relief connu se dessine à
    // plat comme avant, et on ne dit rien — l'absence n'est pas une faute.
    if (plan) plan.ombrage = await chargerOmbrage(terrain.plan);
  }
  return { masque: { ...terrain.masque, bits }, plan };
};

// ── DEUX ROUTES, UN SEUL MOTEUR.
//
//   `/`          — LA CARTE, et rien d'autre. Zéro menu : pas de sélecteur de
//                  scénario, pas de calques à cocher, pas de transport, pas
//                  d'inspecteur. C'est ce qu'on montre.
//   `/bataille`  — la vue de travail : tout l'habillage actuel, intact.
//
// Le partage se lit sur le chemin et nulle part ailleurs — pas de réglage, pas
// de mémoire, pas de bascule dans l'écran. On sait où l'on est à l'URL.
const VUE_COMPLETE = /^\/bataille\/?$/.test(location.pathname);

// ── Choix du scénario : recharger = COMPOSER UN MONDE NEUF (décision actée :
// jamais de reset in place — même chemin que le premier chargement).
let instance = null;
let idActif = 'assaut-de-rue'; // remis sur un scénario de ville, maintenant que Gallipoli est cuite
const lancerScenario = async (id, compose) => {
  idActif = id;
  const scenario = compose || SCENARIOS.find((s) => s.id === id).scenario; // `compose` : le monde de l'état (scenarios/monde-etat.js)
  const ressources = await chargerTerrain(scenario.terrain); // AVANT de démonter l'ancien monde
  instance?.arreter();
  document.body.replaceChildren();
  // Sans habillage, le catalogue n'a pas de bouche pour se dire : on ne le
  // passe pas, plutôt que de le passer à un menu qui n'existe pas.
  const catalogue = VUE_COMPLETE ? {
    liste: SCENARIOS.map(({ id, scenario }) => ({ id, titre: scenario.titre })),
    actif: () => idActif,
    choisir: lancerScenario,
  } : null;
  instance = demarrer(document.body, scenario, catalogue, ressources,
                      { habillage: VUE_COMPLETE });
  // La telecommande de partie, a la main : sauver rend l'instantane, charger
  // le reprend. C'est la meme porte que l'ecran utilisera.
  window.partie = { sauver: () => instance.sauver(), charger: (d) => instance.charger(d) };
  // LA MAIN, a cote des yeux (`ascii`, `asciiVu`). Conduire un homme nomme et
  // battre le temps soi-meme : de quoi tenir une poursuite depuis la console,
  // ou depuis autre chose qu'une paire d'yeux.
  //   conduire.figer(); conduire.piloter(3, {x: 40, y: 10}); conduire.pas(500);
  window.conduire = {
    piloter: (id, pos) => instance.piloter(id, pos),
    figer: () => instance.figer(),
    reprendre: () => instance.reprendre(),
    pas: (ms) => instance.pas(ms),
    // la voix : `conduire.quiEntend(conduire.locuteur(), {intensite: 'cri'})`
    quiEntend: (id, options) => instance.quiEntend(id, options),
    locuteur: () => instance.locuteur(),
    corpsDe: (personnage) => instance.corpsDe(personnage), // le corps d'une fiche du jeu, ou null
    dire: (personnage, texte, dureeS) => instance.dire(personnage, texte, dureeS), // une bulle sur son corps
  };
};
// À la racine, le moteur joue LE MONDE DE L'ÉTAT (scenarios/monde-etat.js) ; /bataille garde le catalogue.
if (VUE_COMPLETE) lancerScenario(idActif); else chargerMondeEtat().then((s) => lancerScenario(s.id, s), (e) => { console.warn(e.message); lancerScenario(idActif); });

// ── LA SCENE EN TEXTE, pour qui ne peut pas la regarder (outils/ascii.mjs).
// Une capture d'ecran coute cher a lire et ne dit que des pixels ; ceci
// projette les CORPS eux-memes sur une grille de caracteres. Appelable a la
// main depuis la console : `ascii()`, `ascii({larg:100})`, `asciiFaits()`.
// Hors boucle de frame, hors container : ca ne dessine rien et ne monte rien.
import('../outils/ascii.mjs').then(({ rendreAscii, rendreFaits, rendreVu }) => {
  const etat = () => {
    const s = instance.sauver();
    // `monde.etat()` range les corps sous `registre` (src/monde/expose.js).
    return { corps: s.monde.registre.corps, scenario: s.scenario, tempsSim: s.tempsSim };
  };
  window.ascii = (o) => rendreAscii(etat(), o);
  window.asciiFaits = () => rendreFaits(etat());
  // LES YEUX D'UN HOMME — sa vue a lui, ses croyances datees, pas le registre.
  // C'est ce qu'on donne a un PNJ : `asciiVu(id)`. `asciiHommes()` les liste.
  // La livree du sujet n'est PAS dans son snapshot (`moi` ne porte que pos et
  // age) : sans elle, un homme prend les siens pour des etrangers. On la
  // prend au registre — c'est un fait sur son corps, pas une croyance.
  window.asciiVu = (id, o) => {
    const lui = instance.hommes().find((h) => h.id === id);
    return rendreVu(instance.perception(id), { maLivree: lui && lui.livree, ...o });
  };
  window.asciiHommes = () => instance.hommes();
  // la perception BRUTE, pour qui veut la lire au lieu de la voir
  window.asciiPerception = (id) => instance.perception(id);
});
