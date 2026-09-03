/**
 * 🧠 Compétences / Moral — LA PRESSION DE PEUR, sur croyances : trois
 * composantes — les pics de récence (un mort des miens vu, ❤️ constaté,
 * 👁️ perçu), l'équilibre des forces PERÇU (surclassé en face), et la
 * CONTAGION (les miens vus en fuite — la déroute se lit comme la readiness,
 * sur le tas). Au seuil : LA RUPTURE — presque d'un coup, parce que chaque
 * fuyard alourdit la pression des autres. PUR, partagé avec les gardes.
 */

import { allerA } from '../intentions.js';
import { contactsAdverses, adverseLePlusProche, rapportDeForce } from './combattre.js';

/**
 * La MENACE LOCALE crue, 0..1 : des adverses au contact = 1 ; sinon le tas
 * adverse cru le plus mordant (frais), dégradé continûment avec son TEMPS
 * D'ARRIVÉE — la menace se mesure en SECONDES, pas en mètres : tau =
 * distance vraie (3D) / allure CRUE de la menace (au pire, elle marche).
 * Au sol, rien ne change (20 m à pied ≈ 14 s — l'ancien horizon) ; mais un
 * galop ou un vol raccourcissent le monde : ce qui vient VITE menace de
 * LOIN, par la même règle. PUR. C'est elle qui donne prise à la contagion :
 * des fuyards sans menace crue à quelques secondes sont une débandade qui
 * s'essouffle.
 */
export function menaceLocale(representation, params) {
  // un dos qui fuit ne menace personne — seuls les adverses DEBOUT comptent
  if (contactsAdverses(representation).some((c) => c.posture !== 'fuit')) return 1;
  const moi = representation.moi;
  if (!moi.pos) return 0;
  let pire = 0;
  for (const etiquette of ['ennemis', 'inconnu']) {
    const t = representation.tasCru(etiquette);
    if (!t?.barycentre || !t.livree || !representation.maLivree || t.livree === representation.maLivree) continue;
    if (t.ageS > params.moral.oubliMenaceS) continue;
    const d = Math.hypot(t.barycentre.x - moi.pos.x, t.barycentre.y - moi.pos.y, t.z ?? 0);
    const allure = Math.max(t.vitesse ?? 0, params.vitesseMax); // au pire, elle marche vers moi
    const tau = d / allure;
    pire = Math.max(pire, Math.max(0, 1 - tau / params.moral.horizonMenaceS));
  }
  return pire;
}

/** La pression de peur, 0 = serein. PUR. */
export function pressionDePeur(representation, params, souffleMoi) {
  const m = params.moral;
  let pression = representation.peur();

  // surclassé en face (sur croyances) : la peur du nombre
  const { prets, adverses } = rapportDeForce(representation, params, souffleMoi);
  if (adverses > prets) {
    pression += m.poidsRapport * ((adverses - prets) / Math.max(1, prets));
  }

  // la contagion : les miens vus en fuite — PONDÉRÉE par la menace locale :
  // l'équilibre à 20 m l'emporte sur les fuyards (sinon une grappe en déroute
  // s'entretient elle-même et personne ne reprend jamais ses esprits)
  const tas = representation.tasCru('escouade') ?? representation.tasCru('unite');
  if (tas && tas.ageS < 2 && tas.fuyards && tas.effectif > 0) {
    // la PROPORTION des miens en fuite, pas le compte : deux fuyards ébranlent
    // une poignée, pas une grande unité — le nombre tient
    pression += m.poidsFuyards * (tas.fuyards / tas.effectif) * menaceLocale(representation, params);
  }

  return pression;
}

/** Le verbe : fuir — dos tourné, plein pas, LOIN de l'ennemi cru. */
export function fuir(ctx) {
  const moi = ctx.representation.moi;
  // on ne fuit que les adverses MENAÇANTS — fuir un fuyard, c'est la course
  // absurde de deux dos (chacun rallonge la fuite de l'autre)
  let menacant = null;
  if (moi.pos) {
    let dMin = Infinity;
    for (const c of contactsAdverses(ctx.representation)) {
      if (c.posture === 'fuit') continue;
      const d = Math.hypot(c.pos.x - moi.pos.x, c.pos.y - moi.pos.y);
      if (d < dMin) {
        dMin = d;
        menacant = { ...c, d };
      }
    }
  }
  const ennemi =
    menacant ??
    (ctx.representation.tasCru('inconnu')?.barycentre
      ? { pos: ctx.representation.tasCru('inconnu').barycentre, d: 1 }
      : null);
  if (!moi.pos || !ennemi) {
    // plus rien à fuir de connu : droit devant, loin
    const cible = { x: moi.pos?.x ?? 0, y: moi.pos?.y ?? 0 };
    return { intention: allerA(cible), objectifHumain: 'fuir !', cible };
  }
  const dx = moi.pos.x - ennemi.pos.x;
  const dy = moi.pos.y - ennemi.pos.y;
  const d = Math.hypot(dx, dy) || 1;
  const cible = { x: moi.pos.x + (dx / d) * 10, y: moi.pos.y + (dy / d) * 10 };
  return { intention: allerA(cible), objectifHumain: 'fuir !', cible };
}

/**
 * Reprendre ses esprits : les PICS de peur (morts des miens) sont retombés,
 * ET l'équilibre perçu est redevenu bon (pas surclassé) — les composantes,
 * pas la distance : on se rallie dans la masse des fuyards, pas à un rayon.
 */
export function espritsRepris(representation, params, souffleMoi) {
  // la MEME pression que la rupture, sous le seuil bas : peur retombée,
  // équilibre redevenu bon, ET la débandade autour finie (contagion) —
  // on ne se rallie pas seul au milieu d'une fuite
  return pressionDePeur(representation, params, souffleMoi) < params.moral.seuilRassure;
}
