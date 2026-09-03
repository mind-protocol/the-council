/**
 * 🧠 Brains / Oiseau / Machine — le cycle de vol en DONNÉE : chaque condition
 * est une garde NOMMÉE, justifiable et dessinable (même discipline que la
 * machine soldat). Les gardes sont PURES sur la Représentation (+ la
 * proprioception : cap/allure par velDe, altitude par moi.pos.z, temps dans
 * l'état par ctx.vecu) ; le VERROU vit dans l'action : le cap de descente se
 * FIGE à l'entrée du piqué (jamais de tourelle), la cible tenue est la masse
 * CRUE — un groupe qui se disperse déplace le point suivi, pas le choix.
 *
 * UNE machine pour les deux bêtes : tenir son poste → descendre → passer bas
 * → reprendre de la hauteur. Ce qui les sépare n'est PAS le graphe, ce sont
 * les chiffres du profil (❤️ oiseaux.js) — le corbeau tombe à 18 m/s et
 * tourne bas vingt secondes, le faucon fond à 78 et remonte en deux.
 *
 * L'oiseau ne fait de mal à personne : il n'y a pas d'état où il frappe.
 */

import { voler } from '../../intentions.js';

const angle = (a) => Math.atan2(Math.sin(a), Math.cos(a));

/** Ce qui l'intéresse en bas : la masse crue, tant qu'elle est fraîche. */
const cibleCrue = (ctx) => {
  const t = ctx.representation.tasCru('ennemis') ?? ctx.representation.tasCru('inconnu');
  return t?.barycentre && t.ageS < 12 ? t : null;
};
const capCru = (ctx) => {
  const v = ctx.velDe();
  return Math.hypot(v.x, v.y) > 1 ? Math.atan2(v.y, v.x) : null;
};
const versCible = (ctx) => {
  const t = cibleCrue(ctx);
  const moi = ctx.representation.moi.pos;
  if (!t || !moi) return null;
  const dx = t.barycentre.x - moi.x;
  const dy = t.barycentre.y - moi.y;
  return { cap: Math.atan2(dy, dx), d: Math.hypot(dx, dy) };
};

/** La géométrie de l'entrée : l'axe verrouillé, le point d'entrée, les restes. */
const geoApproche = (ctx) => {
  const t = cibleCrue(ctx);
  const moi = ctx.representation.moi.pos;
  if (!t || !moi) return null;
  if (ctx.axe == null) {
    ctx.axe = Math.atan2(t.barycentre.y - moi.y, t.barycentre.x - moi.x);
  }
  const u = { x: Math.cos(ctx.axe), y: Math.sin(ctx.axe) };
  const p = ctx.profil;
  const approche = { x: t.barycentre.x - u.x * p.approcheDist, y: t.barycentre.y - u.y * p.approcheDist };
  const dx = t.barycentre.x - moi.x;
  const dy = t.barycentre.y - moi.y;
  return {
    axe: ctx.axe,
    approche,
    dApp: Math.hypot(approche.x - moi.x, approche.y - moi.y),
    reste: dx * u.x + dy * u.y,
    lateral: Math.abs(-dx * u.y + dy * u.x),
    echelle: p.approcheDist / 150, // les fenêtres à l'échelle du profil
  };
};

export const gardes = {
  /** L'entrée est prise : près du point d'entrée, la cible dans la fenêtre le
   *  long de l'AXE, latéral borné, cap presque fermé, assez haut. */
  alignementNormal: (ctx) => {
    const g = geoApproche(ctx);
    const cap = capCru(ctx);
    const moi = ctx.representation.moi.pos;
    if (!g || cap === null || !moi) return false;
    const p = ctx.profil;
    return (
      g.dApp < 78 * g.echelle &&
      g.reste > 0.9 * p.approcheDist &&
      g.reste < 1.42 * p.approcheDist &&
      g.lateral < 62 * Math.sqrt(g.echelle) &&
      Math.abs(angle(g.axe - cap)) < ((p.banqueRalliement * Math.PI) / 180) * 0.5 &&
      (moi.z ?? 0) > p.altitudeRalliement * 0.88
    );
  },
  /** Le poste dure : on convertit la courbe en descente — mais JAMAIS sans
   *  champ ni cap : d'une entrée trop proche ou à contresens, aucune
   *  verticale ne rejoint le sol à temps (reprendre du champ EST le poste). */
  patienceRalliement: (ctx) => {
    const g = geoApproche(ctx);
    const cap = capCru(ctx);
    if (!g || cap === null || ctx.vecu.etatS < ctx.profil.patienceRalliementS) return false;
    return g.reste > 0.9 * ctx.profil.approcheDist && Math.abs(angle(g.axe - cap)) < 1.0;
  },
  cibleDisparue: (ctx) => cibleCrue(ctx) === null,
  /** ARRIVÉ EN BAS. Rien à viser : un oiseau ne crache pas, il descend. La
   *  garde héritée du dragon demandait la masse dans l'axe parce qu'il fallait
   *  l'atteindre ; ici la seule question est la hauteur, et c'est plus vrai. */
  arriveEnBas: (ctx) => {
    const moi = ctx.representation.moi.pos;
    return !!moi && (moi.z ?? 0) < ctx.profil.altitudePasse;
  },
  /** La ligne visée est passée derrière — ou perdue. */
  ligneDepassee: (ctx) => {
    const t = cibleCrue(ctx);
    if (!t) return ctx.vecu.etatS > 10; // cible évaporée : on ne descend pas sur le vide
    const moi = ctx.representation.moi.pos;
    const cap = capCru(ctx) ?? ctx.passe?.cap;
    if (!moi || cap == null) return false;
    const reste =
      (t.barycentre.x - moi.x) * Math.cos(cap) + (t.barycentre.y - moi.y) * Math.sin(cap);
    return reste < -Math.max(40, ctx.profil.opportunite * 0.75);
  },
  /** La passe est consommée : deux secondes pour le faucon, vingt pour le corbeau. */
  passeFinie: (ctx) => ctx.vecu.etatS > ctx.profil.dureePasseS,
  /** Assez haut, assez de champ, assez longtemps : le poste est repris. */
  posteRepris: (ctx) => {
    const moi = ctx.representation.moi.pos;
    if (!moi || ctx.vecu.etatS < 3) return false;
    if ((moi.z ?? 0) < ctx.profil.sortieDeclenche) return false;
    const v = versCible(ctx);
    return v === null || v.d > ctx.profil.approcheDist * 0.53;
  },
};

export const actions = {
  /**
   * TENIR SON POSTE : avec une cible crue, la courbe vers le POINT D'ENTRÉE
   * (à approcheDist derrière l'axe) ; sans cible, le grand cercle au-dessus
   * du champ — on tient le ciel en attendant d'y voir quelque chose.
   */
  tenirLePoste(ctx) {
    const { representation, zone, profil } = ctx;
    const moi = representation.moi.pos;
    if (!moi) return { intention: null, objectifHumain: "prendre l'air", cible: null };
    const g = geoApproche(ctx);
    if (g) {
      const visee = g.dApp < 68 * g.echelle ? g.axe : Math.atan2(g.approche.y - moi.y, g.approche.x - moi.x);
      return {
        intention: voler(visee, profil.altitudeRalliement, 'rallie'),
        objectifHumain: "gagner l'entrée, au-dessus de ce qui bouge en bas",
        cible: g.approche,
      };
    }
    ctx.axe = null; // plus de cible crue : l'axe se lève
    const centre = { x: zone.x + zone.largeur / 2, y: zone.y + zone.hauteur / 2 };
    const dx = moi.x - centre.x;
    const dy = moi.y - centre.y;
    const r = Math.hypot(dx, dy);
    // le cercle d'un oiseau est SERRÉ : il tourne sur ce qu'il guette, à
    // quelques dizaines de mètres — pas sur le comté. Il s'ouvre avec la
    // hauteur du poste (le faucon voit de plus haut, donc de plus loin).
    const rayon = Math.max(22, Math.min(90, 16 + 0.26 * profil.altitudeRalliement));
    const correction = Math.max(-0.48, Math.min(0.48, (r - rayon) / 42));
    return {
      intention: voler(Math.atan2(dy, dx) + Math.PI / 2 + correction, profil.altitudeRalliement, 'croisiere'),
      objectifHumain: 'tourner large au-dessus du champ',
      cible: centre,
    };
  },

  /**
   * DESCENDRE : le cap se FIGE à l'entrée (le verrou — jamais de tourelle) ;
   * le nez suit la masse crue dans une correction bornée, la verticale
   * intercepte le plan de la passe sur le reste. Chez le faucon c'est un
   * piqué ailes fermées, chez le corbeau une spirale qui se laisse tomber.
   */
  descendre(ctx) {
    const v = versCible(ctx);
    const cap = capCru(ctx);
    if (!ctx.passe) ctx.passe = { cap: ctx.axe ?? v?.cap ?? cap ?? 0 };
    const visee = v && Math.abs(angle(v.cap - ctx.passe.cap)) < 0.9 ? v.cap : ctx.passe.cap;
    return {
      intention: voler(visee, ctx.profil.altitudePique, 'pique', v?.d),
      objectifHumain: 'abattre le nez — la hauteur devient vitesse',
      cible: cibleCrue(ctx)?.barycentre ?? null,
    };
  },

  /** PASSER BAS : le vol rasant. Deux secondes ou vingt, selon la bête. */
  passer(ctx) {
    const v = versCible(ctx);
    const cap = ctx.passe?.cap ?? capCru(ctx) ?? 0;
    const visee = v && Math.abs(angle(v.cap - cap)) < 0.6 ? v.cap : cap;
    return {
      intention: voler(visee, ctx.profil.altitudePasse, 'passe'),
      objectifHumain: 'passer bas, au ras de ce qui bouge',
      cible: cibleCrue(ctx)?.barycentre ?? null,
    };
  },

  /** REPRENDRE LE POSTE : hauteur et champ — les verrous se lèvent (la
   *  prochaine descente re-visera un axe frais). */
  reprendreLePoste(ctx) {
    ctx.passe = null;
    ctx.axe = null;
    const cap = capCru(ctx) ?? 0;
    return {
      intention: voler(cap, ctx.profil.altitudeSortie, 'sortie'),
      objectifHumain: 'remonter à son poste',
      cible: null,
    };
  },
};

export const MACHINE_OISEAU = {
  brain: 'oiseau',
  initial: 'poste',
  etats: {
    poste: { agir: 'tenirLePoste' }, // le grand cercle, ou la courbe vers l'entrée
    descend: { agir: 'descendre' }, // cap FIGÉ, la hauteur devient vitesse
    passe: { agir: 'passer' }, // le vol rasant — bref chez le rapace, long chez le corbeau
    remonte: { agir: 'reprendreLePoste' }, // reprendre hauteur et allure, relire le champ
  },
  transitions: [
    { de: 'poste', vers: 'descend', quand: 'alignementNormal', libelle: "l'entrée est prise — j'abats le nez" },
    { de: 'poste', vers: 'descend', quand: 'patienceRalliement', libelle: 'la ligne reste imparfaite — je verrouille mon cap et je tombe' },
    { de: 'descend', vers: 'passe', quand: 'arriveEnBas', libelle: 'me voilà en bas — je rase' },
    { de: 'descend', vers: 'remonte', quand: 'ligneDepassee', libelle: "rien n'est entré dans l'axe — je remonte sans raser le vide" },
    { de: 'passe', vers: 'remonte', quand: 'passeFinie', libelle: "j'ai vu ce qu'il y avait à voir — je reprends de la hauteur" },
    { de: 'remonte', vers: 'poste', quand: 'posteRepris', libelle: 'me revoilà haut — je relis le champ' },
    { de: 'remonte', vers: 'poste', quand: 'cibleDisparue', libelle: "plus rien en bas — je reprends mon cercle" },
  ],
};
