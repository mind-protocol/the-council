/**
 * 🧠 Compétences / Combattre — l'engagement au contact, sur CROYANCES :
 * - `sePreparer` : posture prête, on se tient (l'orientation face l'ennemi) ;
 * - `engager` : charger le contact adverse cru LE PLUS PROCHE, frapper(cible)
 *   à portée — l'acte (🏃) juge physiquement, un coup peut rater ;
 * - `pousserDerriere` : derrière la ligne, pression douce vers l'avant ;
 * - `rompre` : plus de souffle — reculer SANS tourner le dos (allure faible).
 * Les prédicats (contact, rapport de force, première ligne) sont PURS et
 * partagés avec les gardes : la condition de la garde est celle que la
 * compétence rencontre. Le rapport de force : mes prêts perçus (moi compris)
 * contre les adverses au contact — on n'attaque jamais seul.
 */

import { allerA, attendre, frapper } from '../intentions.js';

/** Les contacts crus adverses / alliés. PUR. */
export function contactsAdverses(representation) {
  const maLivree = representation.maLivree;
  return representation.contactsCrus().filter((c) => c.livree && maLivree && c.livree !== maLivree);
}

/** Le contact adverse cru le plus proche, ou null. PUR. */
export function adverseLePlusProche(representation) {
  const moi = representation.moi;
  if (!moi.pos) return null;
  let choix = null;
  let meilleurD = Infinity;
  for (const c of contactsAdverses(representation)) {
    const d = Math.hypot(c.pos.x - moi.pos.x, c.pos.y - moi.pos.y);
    if (d < meilleurD) {
      meilleurD = d;
      choix = { ...c, d };
    }
  }
  return choix;
}

/**
 * L'ennemi est-il au contact ? PUR. Le rayon est celui d'ENGAGEMENT par
 * défaut ; les gardes de SORTIE passent le rayon de désengagement (plus
 * large) — l'hystérésis qui empêche la machine de clignoter à la frontière.
 */
export function ennemiAuContact(representation, params, rayon = params.combat.rayonEngagement) {
  const proche = adverseLePlusProche(representation);
  return proche !== null && proche.d <= rayon;
}

/**
 * Suis-je DERRIÈRE la ligne ? D'abord sur la FORME CRUE de mon propre tas
 * (sa première ligne + son cap — une lecture de groupe, que le budget
 * d'attention n'affame pas) ; sinon, au couloir : un des nôtres cru entre
 * moi et l'ennemi le plus proche. PUR.
 */
export function derriereLaLigne(representation) {
  const moi = representation.moi;
  const ennemi = adverseLePlusProche(representation);
  if (!moi.pos || !ennemi) return false;

  // 1. ma ligne crue : en retrait de sa première ligne (dans l'axe du cap)
  const tas = representation.tasCru('escouade') ?? representation.tasCru('unite');
  if (tas?.premiereLigne && tas.cap !== undefined && tas.ageS < 3) {
    const retrait =
      (tas.premiereLigne.centre.x - moi.pos.x) * Math.cos(tas.cap) +
      (tas.premiereLigne.centre.y - moi.pos.y) * Math.sin(tas.cap);
    if (retrait > 0.8) return true;
  }

  // 1b. la forme dissoute (mêlée) : plus loin de l'ennemi que le BARYCENTRE
  // de mon tas → je suis dans la profondeur, pas au front
  if (tas?.barycentre && tas.ageS < 3) {
    const dGroupe = Math.hypot(tas.barycentre.x - ennemi.pos.x, tas.barycentre.y - ennemi.pos.y);
    if (ennemi.d > dGroupe + 0.6) return true;
  }

  // 2. sinon, le couloir sur les contacts crus (peut manquer de données)
  const ux = (ennemi.pos.x - moi.pos.x) / (ennemi.d || 1);
  const uy = (ennemi.pos.y - moi.pos.y) / (ennemi.d || 1);
  const maLivree = representation.maLivree;
  for (const c of representation.contactsCrus()) {
    if (!c.livree || c.livree !== maLivree) continue;
    const dx = c.pos.x - moi.pos.x;
    const dy = c.pos.y - moi.pos.y;
    const long = dx * ux + dy * uy; // projection sur l'axe vers l'ennemi
    const lat = Math.abs(-dx * uy + dy * ux);
    if (long > 0.3 && long < ennemi.d && lat < 0.8) return true;
  }
  return false;
}

/**
 * Le RAPPORT DE FORCE : mes prêts perçus (moi compris, si mon souffle tient)
 * contre les adverses au contact. PUR — chacun juge sur SES croyances.
 * @returns {{prets: number, adverses: number, rapport: number}}
 */
export function rapportDeForce(representation, params, souffleMoi) {
  let prets = souffleMoi >= params.combat.souffleEngage ? 1 : 0;
  // la readiness de MA ligne se lit sur le TAS (les lances levées comptées
  // par le percept de groupe) — pas homme par homme : le budget d'attention
  // reste aux menaces, le groupe reste un seul objet
  const tas = representation.tasCru('escouade') ?? representation.tasCru('unite');
  if (tas && tas.ageS < 2 && tas.prets) prets += tas.prets;
  // UN DOS QUI FUIT NE MENACE PERSONNE (même principe que la garde ⚙️) :
  // sans ce filtre, un nuage de déroute MIXTE s'auto-terrorise — chacun
  // compte les fuyards adverses comme un surnombre, et personne ne se rallie
  // L'adversaire se PÈSE en gabarit, pas en têtes (le rayon se voit) : un
  // homme vaut 1, un cheval ~1,7 — le surnombre perçu suit la masse en face
  const adverses = contactsAdverses(representation)
    .filter((c) => c.posture !== 'fuit')
    .reduce((s, c) => s + (c.rayon ?? params.rayonHomme) / params.rayonHomme, 0);
  return { prets, adverses, rapport: adverses > 0 ? prets / adverses : Infinity };
}

/**
 * La CURÉE est-elle ouverte ? Des adverses crus au contact, et TOUS en
 * fuite — le combat local est fini, il ne reste qu'à courir. PUR.
 */
export function cureeOuverte(representation) {
  const adverses = contactsAdverses(representation);
  return adverses.length > 0 && adverses.every((c) => c.posture === 'fuit');
}

/** Le fuyard cru le plus proche, ou null. PUR. */
export function fuyardLePlusProche(representation) {
  const moi = representation.moi;
  if (!moi.pos) return null;
  let choix = null;
  let meilleurD = Infinity;
  for (const c of contactsAdverses(representation)) {
    if (c.posture !== 'fuit') continue;
    const d = Math.hypot(c.pos.x - moi.pos.x, c.pos.y - moi.pos.y);
    if (d < meilleurD) {
      meilleurD = d;
      choix = { ...c, d };
    }
  }
  return choix;
}

// ── Les verbes (contrat commun (ctx) → {intention, objectifHumain, cible}) ──

export function sePreparer(ctx) {
  const { prets, adverses } = rapportDeForce(ctx.representation, ctx.params, ctx.souffle());
  return {
    intention: attendre(),
    objectifHumain: `prêt — ${prets} des nôtres contre ${adverses} en face`,
    cible: null,
  };
}

export function engager(ctx) {
  const ennemi = adverseLePlusProche(ctx.representation);
  if (!ennemi) return { intention: attendre(), objectifHumain: "plus d'ennemi devant", cible: null };
  const nom = ctx.representation.nomDe(ennemi.id);
  // MA portée de frappe : l'allonge de MON arme (❤️) + une marge de geste —
  // le piquier frappe de loin, l'épéiste doit passer sous la pointe
  const porteeFrappe = (ctx.arme?.()?.allonge ?? 1.5) + ctx.params.combat.margeFrappe;
  if (ennemi.d > porteeFrappe) {
    // DÉFENSE : on croise le fer sans quitter son rang — la cible hors de
    // portée n'est pas poursuivie (le tapis roulant garde/charge ferait
    // surfer le mur hors de sa ligne) ; elle viendra, ou pas
    if (ctx.representation.posture === 'defense') {
      return { intention: attendre(), objectifHumain: `attendre ${nom} de pied ferme`, cible: null };
    }
    return { intention: allerA(ennemi.pos), objectifHumain: `charger ${nom}`, cible: ennemi.pos };
  }
  return { intention: frapper(ennemi.id), objectifHumain: `au fer contre ${nom}`, cible: ennemi.pos };
}

/** La curée : courir sur le fuyard, frapper le dos — l'acte compte triple. */
export function poursuivre(ctx) {
  const fuyard = fuyardLePlusProche(ctx.representation);
  if (!fuyard) return { intention: attendre(), objectifHumain: 'plus de fuyard à portée', cible: null };
  const nom = ctx.representation.nomDe(fuyard.id);
  const porteeFrappe = (ctx.arme?.()?.allonge ?? 1.5) + ctx.params.combat.margeFrappe;
  if (fuyard.d > porteeFrappe) {
    return { intention: allerA(fuyard.pos), objectifHumain: `courir sus à ${nom}`, cible: fuyard.pos };
  }
  return { intention: frapper(fuyard.id), objectifHumain: `frapper ${nom} dans sa fuite`, cible: fuyard.pos };
}

export function pousserDerriere(ctx) {
  const ennemi = adverseLePlusProche(ctx.representation);
  const moi = ctx.representation.moi;
  if (!ennemi || !moi.pos) return { intention: attendre(), objectifHumain: 'je tiens mon rang', cible: null };
  const cible = {
    x: moi.pos.x + ((ennemi.pos.x - moi.pos.x) / ennemi.d) * 1.5,
    y: moi.pos.y + ((ennemi.pos.y - moi.pos.y) / ennemi.d) * 1.5,
  };
  return {
    intention: allerA(cible, ctx.params.combat.allurePoussee),
    objectifHumain: 'pousser doucement ceux de devant',
    cible,
  };
}

export function rompre(ctx) {
  const ennemi = adverseLePlusProche(ctx.representation);
  const moi = ctx.representation.moi;
  if (!ennemi || !moi.pos) return { intention: attendre(), objectifHumain: 'souffler', cible: null };
  const cible = {
    x: moi.pos.x - ((ennemi.pos.x - moi.pos.x) / ennemi.d) * 2.5,
    y: moi.pos.y - ((ennemi.pos.y - moi.pos.y) / ennemi.d) * 2.5,
  };
  return {
    intention: allerA(cible, ctx.params.combat.allureRecul),
    objectifHumain: 'rompre d un pas, sans tourner le dos',
    cible,
  };
}
