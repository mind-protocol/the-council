/**
 * 🏃 Steering / Vol — l'ACTUATEUR de vol : traduit une intention de vol
 * ({capVoulu, zVoulue, regime, reste?}) en ÉTAT DE VOL RÉALISABLE du tick
 * sous les lois du profil (❤️ oiseaux.js) — l'Intégration (⚙️) l'écrit.
 * Aucune décision : le QUOI vient du brain (🧠), ici seulement le POSSIBLE.
 * Fonction PURE (état courant + intention + dt → état suivant), lois gardées
 * Les lois gardées :
 * - virage coordonné : ω = (g·tanφ + a_battement)/V — la banque filtrée
 *   resserre le virage, le battement dissymétrique aide, JAMAIS de pivot ;
 * - vol lent (basseAllure) : lacet propulsé — les battements portent, la
 *   banque reste couchée sous banqueLente, le corps pivote presque sur place ;
 * - altitude : consigne filtrée (0,055 / 0,58), vz bornée [-24, +8] — SAUF
 *   au piqué : la verticale INTERCEPTE le plan de tir sur `reste` (jamais
 *   d'asymptote qui freine près du sol) ;
 * - vitesse : filtre ~2,6 s, oscillation ±3,5 % au battement, plancher NON
 *   catapulte ; au piqué la hauteur devient vitesse — V² = min(limite²,
 *   V_entrée² + 2·g·η·Δh), η = 0,45 (les refs d'entrée se capturent au
 *   changement de régime, portées par l'état de vol).
 */

const G = 9.81;
const angle = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

// les plafonds de banque par régime (degrés — l'orbite reste stable, le
// ralliement couche l'aile, le piqué se corrige fort, le souffle à peine)
const banqueMaxDeg = (profil, regime, z, altitudePasseEffective) => {
  if (regime === 'rallie') return profil.banqueRalliement;
  if (regime === 'pique') return z < altitudePasseEffective * 2.8 ? profil.banquePiqueBas : profil.banquePiqueHaut;
  if (regime === 'passe') return profil.banquePasse;
  if (regime === 'sortie') return 12;
  return 35; // croisière
};

/**
 * L'état de vol suivant d'un corps volant.
 * @param {{pos: {x,y}, cap: number, vol: {z, vz, vitesseAir, banque, pente, phaseAile, regime?, zRef?, vRef?}}} corps
 * @param {Object} profil — l'entrée ❤️ OISEAUX
 * @param {{capVoulu: number, zVoulue: number, regime: string, reste?: number}} intention
 * @param {number} dt
 * @returns {{pos, vel, cap, vol}}
 */
export function consigneVol(corps, profil, intention, dt) {
  const v0 = corps.vol;
  const regime = intention.regime ?? 'croisiere';
  const basseAllure = regime === 'basseAllure';
  const pique = regime === 'pique';
  const erreur = angle(intention.capVoulu - corps.cap);
  // au changement de régime, l'état d'entrée se capture (le piqué convertit
  // LA hauteur perdue depuis SON entrée, pas depuis le décollage)
  const zRef = regime === v0.regime ? v0.zRef ?? v0.z : v0.z;
  const vRef = regime === v0.regime ? v0.vRef ?? v0.vitesseAir : v0.vitesseAir;

  // ── le virage : banqué (vol porté) ou lacet propulsé (vol lent) ──
  let banque = v0.banque;
  let cap = corps.cap;
  if (basseAllure) {
    const lacet = clamp(erreur * 1.25, -profil.lacetLent, profil.lacetLent);
    const banqueLente = (profil.banqueLente * Math.PI) / 180;
    banque += (clamp(erreur * 0.16, -banqueLente, banqueLente) - banque) * Math.min(1, dt * 3.2);
    cap += lacet * dt;
  } else {
    const banqueMax = (banqueMaxDeg(profil, regime, v0.z, profil.altitudePasse) * Math.PI) / 180;
    banque += (clamp(erreur * 1.9, -banqueMax, banqueMax) - banque) * Math.min(1, dt * 2.45);
    const battementLateral = clamp(erreur * 4.2, -profil.accelLateral, profil.accelLateral);
    cap += (((G * Math.tan(banque) + battementLateral) / Math.max(8, v0.vitesseAir)) * dt);
  }
  cap = angle(cap);

  // ── l'altitude ──
  let vz;
  if (pique) {
    // le point bas appartient à la LIGNE de descente : la verticale
    // intercepte le plan de la passe au moment où la ligne rejoint la cible
    const descenteMax = Math.min(36, profil.pique * 0.58);
    const pente = (profil.pentePasse * Math.PI) / 180;
    const avance = Math.min(profil.opportunite * 0.72, intention.zVoulue / Math.max(0.2, Math.tan(pente)));
    const reste = intention.reste ?? profil.approcheDist;
    // l'avance est portée à 2,5 s : l'occasion se juge à ~2 Hz (pas 40) — il
    // faut être ÉTABLI bas quand la fenêtre s'ouvre
    const tempsSol = clamp((reste - avance) / Math.max(1, v0.vitesseAir) - 2.5, 1.25, 14);
    const voulueVz = clamp((intention.zVoulue - v0.z) / tempsSol, -descenteMax, -2);
    vz = v0.vz + (voulueVz - v0.vz) * Math.min(1, dt * 1.75);
  } else {
    const descenteMax = regime === 'passe' ? 5.5 : regime === 'sortie' ? 2.5 : 4.5;
    const az = clamp((intention.zVoulue - v0.z) * 0.055 - v0.vz * 0.58, -descenteMax, 5.5);
    vz = clamp(v0.vz + az * dt, -24, 8);
  }
  // le plancher appartient à la BÊTE : un corbeau rase à trois mètres, un
  // faucon à deux — aucun ne touche le sol.
  const z = Math.max(profil.plancher, v0.z + vz * dt);

  // ── la vitesse ──
  let voulue;
  if (pique) {
    // la hauteur perdue devient vitesse (η = 0,45), plafonnée par la traînée
    voulue = Math.min(profil.pique, Math.sqrt(vRef * vRef + 2 * G * 0.45 * Math.max(0, zRef - z)));
  } else {
    voulue =
      basseAllure ? profil.volLent
      : regime === 'rallie' ? profil.approcheVitesse
      : regime === 'passe' ? profil.vitessePasse
      : regime === 'sortie' ? profil.vitesseSortie
      : profil.croisiere;
  }
  const minimum = basseAllure ? profil.volLentMin : profil.minimumVol;
  const freinMax = basseAllure ? profil.freinLent : 3.8;
  const cible = voulue * (1 + 0.035 * Math.sin(v0.phaseAile));
  // L'ACCÉLÉRATION appartient à la BÊTE. Un corbeau pousse doucement ; un
  // rapace en piqué tombe, et c'est la pesanteur qui le tire — sans ce champ,
  // le plafond commun bridait le fond à trente mètres par seconde.
  const a = clamp((cible - v0.vitesseAir) / 2.6, -freinMax, pique ? profil.accelPique : profil.accelMax);
  const vitesseAir = clamp(v0.vitesseAir + a * dt, Math.min(minimum, v0.vitesseAir), profil.limite);

  // ── le battement : sa fréquence suit le régime — la silhouette bat vrai ──
  const hz = basseAllure
    ? profil.battementLentHz
    : profil.battementHz + (vitesseAir > profil.presse || Math.abs(vz) > 6 ? 0.09 : 0);
  const phaseAile = (v0.phaseAile + 2 * Math.PI * hz * dt) % (2 * Math.PI);

  const vel = { x: Math.cos(cap) * vitesseAir, y: Math.sin(cap) * vitesseAir };
  return {
    pos: { x: corps.pos.x + vel.x * dt, y: corps.pos.y + vel.y * dt },
    vel,
    cap,
    vol: { z, vz, vitesseAir, banque, pente: Math.atan2(vz, Math.max(1, vitesseAir)), phaseAile, regime, zRef, vRef },
  };
}
