/**
 * Test de fumée HEADLESS — la sim sous Node, sans navigateur, et les trois
 * propriétés déclarées qui se cassent silencieusement :
 *
 *   1. Déterminisme : même seed, même déroulé → état du monde IDENTIQUE
 *      (bit-exact), corps par corps.
 *   2. dt fixe : x5 = plus de pas par frame, jamais des pas plus grands —
 *      un run à x1 (frames de 100 ms) et un run à x5 (frames de 20 ms)
 *      accumulent les MÊMES flottants, l'état final doit être identique.
 *   3. introspect() obligatoire : chaque homme répond à l'introspection.
 *
 * La composition reflète src/main.js SANS la Présentation (c'est le point :
 * la sim tourne sans elle). Si main.js change de câblage, ce test casse
 * bruyamment — c'est voulu, il se met à jour avec.
 *
 * Usage : node coding/fumee.mjs   (code de sortie 0 = tout passe)
 */

import { composer } from './composer.mjs';
import { creerRng } from '../src/infra/rng.js';
import { creerMonde } from '../src/monde/expose.js';
import { creerCognition } from '../src/cognition/expose.js';
import { creerSoldat } from '../src/cognition/brains/soldat/brain.js';
import { creerCommandant } from '../src/cognition/brains/commandant/brain.js';
import { LIVRE_DE_MANOEUVRES } from '../src/cognition/doctrine/manoeuvres/livre.js';
import { CRITERES } from '../src/cognition/brains/commandant/estimation.js';
import { creerAction } from '../src/action/expose.js';
import { creerPhysique } from '../src/physique/expose.js';
import { creerOrchestration } from '../src/orchestration/expose.js';
import { creerSocial } from '../src/social/expose.js';
import { creerCorps } from '../src/corps/expose.js';
import { PARAMS } from '../src/params.js';
import { OISEAUX } from '../src/corps/oiseaux.js';
import { PREMIERE_LANCE, FACE_A_FACE, LA_VOLEE, BATAILLE_RANGEE, LA_CONROI, ASSAUT_DE_RUE } from '../src/scenarios/index.js';
import { LES_OISEAUX } from '../src/scenarios/les-oiseaux.js';
import { resoudreChocs } from '../src/physique/collisions/choc.js';
import { refusDeLaMonture } from '../src/action/steering/refus-monture.js';
import { resoudreMontage } from '../outils/montages.mjs';
import { readFileSync } from 'node:fs';

/** L'état complet des corps, sérialisé bit-exact (ordre stable du registre). */
function photographier(monde) {
  return JSON.stringify(
    [...monde.corps()].map((c) => [c.id, c.pos.x, c.pos.y, c.vel.x, c.vel.y, c.cap ?? null, c.vol?.z ?? null])
  );
}

/**
 * Fait tourner ~dureeS secondes sim en frames régulières.
 * @returns {string} la photo finale
 */
function courir(scenario, { frames, msParFrame, vitesse = 1, ressources }) {
  const sim = composer(scenario, ressources);
  if (vitesse !== 1) sim.orchestration.transport.reglerVitesse(vitesse);
  for (let f = 0; f < frames; f++) sim.orchestration.avancer(msParFrame);
  return { photo: photographier(sim.monde), sim };
}

export { courir, photographier };

// Exécution directe seulement (l'import des outils ne lance pas le test).
import { pathToFileURL } from 'node:url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  principal();
}

function principal() {
let echecs = 0;
const verdict = (ok, nom, detail = '') => {
  console.log(`${ok ? 'OK    ' : 'ECHEC '} ${nom}${detail ? ' — ' + detail : ''}`);
  if (!ok) echecs++;
};

// ── 0. La sim compose et avance sans navigateur ──
const { photo: photoA, sim: simA } = courir(PREMIERE_LANCE, { frames: 100, msParFrame: 100 });
const ticksA = Math.round(simA.orchestration.transport.etat().tempsSim / PARAMS.dtFixe);
verdict(ticksA > 0, 'headless', `${ticksA} ticks exécutés sous Node, ${simA.tous.length} hommes`);

const bouge = [...simA.monde.corps()].some((c) => c.vel.x !== 0 || c.vel.y !== 0);
const initiales = new Set(PREMIERE_LANCE.unites.flatMap((u) => [u.chef, ...u.hommes]).map((h) => `${h.pos.x},${h.pos.y}`));
const deplaces = [...simA.monde.corps()].filter((c) => !initiales.has(`${c.pos.x},${c.pos.y}`)).length;
verdict(bouge || deplaces > simA.tous.length / 2, 'vivant', `${deplaces} corps ont quitté leur position de spawn`);

// ── 1. Déterminisme : même seed, même déroulé → même état ──
const { photo: photoB, sim: simB } = courir(PREMIERE_LANCE, { frames: 100, msParFrame: 100 });
verdict(photoA === photoB, 'déterminisme', 'deux runs même seed : états bit-exacts');

// ── 2. dt fixe : x5 en frames de 20 ms ≡ x1 en frames de 100 ms ──
// (100 × 1 et 20 × 5 accumulent les MÊMES flottants : l'égalité est exacte)
const { photo: photoC } = courir(PREMIERE_LANCE, { frames: 100, msParFrame: 20, vitesse: 5 });
verdict(photoA === photoC, 'dt-fixe', 'x5 = plus de pas, jamais des pas plus grands');

// ── 3. introspect() obligatoire sur tout brain ──
const muets = simA.tous.filter((id) => {
  const i = simA.cognition.introspecter(id);
  return !i || typeof i.brain !== 'string' || typeof i.etat !== 'string';
});
verdict(muets.length === 0, 'introspection', muets.length ? `ids muets : ${muets}` : `${simA.tous.length}/${simA.tous.length} hommes introspectables`);

// ── 3b. Machines à états : structure présente, journal justifié ──
const introspections = simA.tous.map((id) => simA.cognition.introspecter(id));
const sansMachine = introspections.filter((i) => !i.machine || !i.machine.etat || !Array.isArray(i.machine.transitions));
verdict(sansMachine.length === 0, 'machine', `${simA.tous.length - sansMachine.length}/${simA.tous.length} brains exposent leur machine`);

const bascules = introspections.reduce((n, i) => n + i.machine.journal.length, 0);
const injustifiees = introspections.flatMap((i) => i.machine.journal).filter((e) => !e.libelle);
verdict(bascules > 0 && injustifiees.length === 0, 'justifications',
  `${bascules} transitions au journal, toutes avec libellé`);

// ── 3c. Faits nommés : une applicabilité n'est JAMAIS une fonction ──
// L'arbitre teste l'applicabilité par `!!situation[f]` : une closure y est
// TOUJOURS vraie — la manœuvre devient applicable en permanence. Et le debug
// de l'état-major filtre les fonctions et les objets, donc un tel fait
// DISPARAÎT de la viz sans un mot. Les deux pannes sont silencieuses ; c'est
// par là qu'était entrée la marche (`prochainBond`, `presDe` posés parmi les
// faits). Un fait se nomme, se justifie et s'affiche : il est scalaire, ou
// c'est une garde de phase déclarée dans CRITERES.
const situationVue = introspections.find((i) => i.etatMajor?.situation)?.etatMajor.situation;
const fautes = [];
for (const m of LIVRE_DE_MANOEUVRES) {
  for (const f of m.applicabilite) {
    const t = situationVue && f in situationVue ? typeof situationVue[f] : 'absent';
    if (t !== 'boolean' && t !== 'number') fautes.push(`${m.nom}.${f} (${t})`);
  }
  for (const p of m.phases ?? []) {
    for (const g of [p.succes, p.echec]) if (g && !(g in CRITERES)) fautes.push(`${m.nom} garde '${g}' hors CRITERES`);
  }
}
const nbFaits = LIVRE_DE_MANOEUVRES.reduce((n, m) => n + m.applicabilite.length, 0);
verdict(!!situationVue && fautes.length === 0, 'faits-nommes',
  fautes.length ? fautes.join(', ') : `${nbFaits} applicabilités scalaires et affichables, gardes de phase toutes dans CRITERES`);

const etatsA = JSON.stringify(introspections.map((i) => i.machine.etat));
const etatsB = JSON.stringify(simB.tous.map((id) => simB.cognition.introspecter(id).machine.etat));
verdict(etatsA === etatsB, 'machines-deterministes', 'mêmes états de machine sur deux runs même seed');

// ── 4. Snapshot : l'index reflète exactement les corps du registre ──
simA.orchestration.avancer(100); // le snapshot du tick courant
const { tailleCase, cases } = simA.monde.indexDebug();
const attendu = new Map();
for (const c of simA.monde.corps()) {
  const k = `${Math.floor(c.pos.x / tailleCase)}|${Math.floor(c.pos.y / tailleCase)}`;
  attendu.set(k, (attendu.get(k) ?? 0) + 1);
}
const recu = new Map(cases.map((c) => [`${c.cx}|${c.cy}`, c.n]));
const fidele =
  attendu.size === recu.size &&
  [...attendu].every(([k, n]) => recu.get(k) === n);
verdict(fidele, 'index-fidele', `${cases.length} cases occupées = les corps, case par case`);

// ── 4b. Souffle : la marche use la réserve, le ressenti reste borné ──
const corpsF0 = composer(PREMIERE_LANCE); // frais : personne n'a marché
const souffleFrais = corpsF0.tous.every((id) => corpsF0.corpsContainer.souffleDe(id) > 0.9);
const reserves = simA.tous.map((id) => simA.corpsContainer.reserveDe(id));
const uses = reserves.filter((r) => r < 1).length;
const bornes = simA.tous.every((id) => {
  const s = simA.corpsContainer.souffleDe(id);
  return s >= 0 && s <= 1;
});
verdict(souffleFrais && uses > simA.tous.length / 2 && bornes, 'souffle',
  `${uses}/${simA.tous.length} réserves entamées après 100 s de vie, ressenti sigmoïde borné`);

// ── 5. FACE_A_FACE : les deux camps se VOIENT homme par homme ──
const { sim: simF } = courir(FACE_A_FACE, { frames: 60, msParFrame: 100 });
const contactsAdverses = (id) => {
  const snap = simF.cognition.perceptionDebug(id);
  const c = simF.monde.corpsParId(id);
  return (snap.contacts ?? []).filter((x) => x.livree && x.livree !== c.livree).length;
};
const bleusQuiVoient = simF.unites[0].membres.filter((id) => contactsAdverses(id) > 0).length;
const rougesQuiVoient = simF.unites[1].membres.filter((id) => contactsAdverses(id) > 0).length;
verdict(bleusQuiVoient > 0 && rougesQuiVoient > 0, 'contact',
  `face-à-face : ${bleusQuiVoient} bleus et ${rougesQuiVoient} rouges voient des ennemis homme par homme`);

// l'ordre initial est bien reçu et suivi — l'état COURANT ne suffit pas :
// à 5 m de l'ennemi, la rencontre préempte légitimement l'obéissance (tuer),
// donc on lit le VÉCU (journal) : est-il passé par obeir ?
const enObeissance = simF.tous.filter((id) => {
  const i = simF.cognition.introspecter(id);
  return i.etat.startsWith('obeir') ||
    i.machine.journal.some((e) => e.de.startsWith('obeir') || e.vers.startsWith('obeir'));
}).length;
verdict(enObeissance > simF.tous.length / 2, 'ordre-initial',
  `${enObeissance}/${simF.tous.length} sont passés en formation ordonnée au chargement`);

// ── 6. Combat : la rencontre déclenche tuer, l'assaut part, les coups portent ──
const { sim: simC } = courir(FACE_A_FACE, { frames: 240, msParFrame: 100 });
const etatsC = simC.tous.map((id) => simC.cognition.introspecter(id).machine.etat);
const enTuer = etatsC.filter((e) => e.startsWith('tuer')).length;
const coupsC = simC.tous.reduce((n, id) => n + simC.corpsContainer.blessuresDe(id), 0);
const assauts = simC.tous.reduce(
  (n, id) => n + simC.cognition.introspecter(id).machine.journal.filter((e) => e.libelle.includes('assaut')).length,
  0
);
verdict(enTuer > 0 && coupsC > 0 && assauts > 0, 'combat',
  `${enTuer} en tuer.* à 240 s, ${assauts} assauts déclarés, ${coupsC} coups portés`);

// ── 7. La mort : constatée (❤️), manifestée (gisant), figée (⚙️) ──
// la mort et la curee se testent a l ECHELLE : la bataille rangee 4v4 —
// fenetre longue, la deroute de masse arrive tard dans la bataille
const { sim: simM } = courir(BATAILLE_RANGEE, { frames: 2400, msParFrame: 100 });
let mortsM = 0;
let gisantsCorrects = true;
for (const c of simM.monde.corps()) {
  if (simM.corpsContainer.estVivant(c.id)) continue;
  mortsM++;
  if (c.posture !== 'gisant' || Math.hypot(c.vel.x, c.vel.y) > 1e-9) gisantsCorrects = false;
}
const boiteux = simM.tous.filter(
  (id) => simM.corpsContainer.estVivant(id) && simM.corpsContainer.facteurVitesseDe(id) < 1
).length;
const cureesM = simM.tous.reduce(
  (n, id) => n + simM.cognition.introspecter(id).machine.journal.filter((e) => e.libelle.includes('curée')).length,
  0
);
verdict(cureesM > 0, 'curee', `${cureesM} curées ouvertes — les fuyards se font rattraper (coups x3)`);
verdict(mortsM > 0 && gisantsCorrects, 'mort',
  `${mortsM} morts à 600 s — tous gisants et immobiles, ${boiteux} blessés qui boitent`);

// ── 8. Le choc : la quantite de mouvement se transfere, le lourd renverse ──
{
  // un demi-tonne a 8 m/s percute un homme de 80 kg a l'arret (fonction PURE)
  const corps = [
    { id: 1, pos: { x: 0, y: 0 }, rayon: 0.6, masse: 550 },
    { id: 2, pos: { x: 0.9, y: 0 }, rayon: 0.35, masse: 80 },
  ];
  const vels = new Map([[1, { x: 8, y: 0 }], [2, { x: 0, y: 0 }]]);
  const { velsCorrigees, renversements } = resoudreChocs(corps, vels, PARAMS.choc);
  const avant = 550 * 8;
  const apres = 550 * velsCorrigees.get(1).x + 80 * velsCorrigees.get(2).x;
  const conserve = Math.abs(apres - avant) < 1e-6;
  const asymetrie = velsCorrigees.get(2).x > 5 && velsCorrigees.get(1).x > 6; // le leger vole, le lourd continue
  const renverseLeger = renversements.some((r) => r.id === 2) && !renversements.some((r) => r.id === 1);
  verdict(conserve && asymetrie && renverseLeger, 'choc',
    `quantite de mouvement conservee (${avant.toFixed(0)} -> ${apres.toFixed(0)} kg.m/s) — le leger est renverse, pas le lourd`);
}

// ── 9. L'attelage : le cavalier est porte, la monture donne le train ──
{
  const simA = composer(LA_CONROI);
  let vMaxMonture = 0;
  let ticksRefus = 0;
  const renversesCumules = new Set();
  for (let f = 0; f < 1200; f++) {
    simA.orchestration.avancer(100);
    if (simA.action.refusPourDebug().size) ticksRefus++;
    for (const c of simA.monde.corps()) {
      if (c.gabarit === 'cheval') vMaxMonture = Math.max(vMaxMonture, Math.hypot(c.vel.x, c.vel.y));
      if (c.posture === 'renverse') renversesCumules.add(c.id);
    }
  }
  let ecarts = 0, cavaliers = 0;
  for (const id of simA.tous) {
    const idMonture = simA.monde.montureDe(id);
    if (idMonture == null) continue;
    cavaliers++;
    const cav = simA.monde.corpsParId(id);
    const mon = simA.monde.corpsParId(idMonture);
    if (Math.hypot(cav.pos.x - mon.pos.x, cav.pos.y - mon.pos.y) > 0.01) ecarts++;
  }
  let renversesVus = 0;
  let blessesParChoc = 0;
  for (const c of simA.monde.corps()) {
    if (c.gabarit === 'homme' && c.livree === 'rouge' && simA.corpsContainer.blessuresDe(c.id) > 0) blessesParChoc++;
  }
  for (const id of renversesCumules) renversesVus++;
  verdict(
    cavaliers > 0 && ecarts === 0 && vMaxMonture > PARAMS.cheval.allures.galop * 0.8 && renversesVus > 3 && blessesParChoc > 0,
    'attelage-charge',
    `${cavaliers} en selle, asservis au centimetre ; galop a ${vMaxMonture.toFixed(1)} m/s, ${renversesVus} renverses, ${blessesParChoc} rouges marques par le choc`);

  // ── 9ter. La passe : traverser, reprendre du champ, recharger — le cycle ──
  let repasses = 0;
  let recharges = 0;
  for (const id of simA.tous) {
    if (simA.monde.montureDe(id) == null) continue;
    const v = simA.cognition.introspecter(id).machine.vecu;
    if ((v.tempsParEtat['tuer.repasse'] ?? 0) > 0) repasses++;
    const n = Object.entries(v.bascules)
      .filter(([k]) => k.endsWith('→ obeir.charge'))
      .reduce((somme, [, x]) => somme + x, 0);
    if (n >= 2) recharges++;
  }
  verdict(repasses > 0 && recharges > 0, 'passe',
    `${repasses} cavaliers ont traverse et repris du champ, ${recharges} ont redonne la charge (2+) — le cycle charge-degagement-charge vit`);

  // ── 9bis. Le refus : le cheval ne s'enfonce pas dans une masse herissee ──
  // test PUR : un mur de 5 piques levees droit devant -> refus quasi total,
  // derobade laterale ; 5 epees levees -> le cheval passe (poids faible)
  const mur = (allonge) => Array.from({ length: 5 }, (_, i) => ({
    id: 900 + i,
    pos: { x: 8, y: 10 + (i - 2) * 1.2 },
    livree: 'rouge',
    posture: 'pret',
    allonge,
  }));
  const essai = (voisins) =>
    refusDeLaMonture({
      pos: { x: 0, y: 10 },
      livree: 'bleu',
      vel: { x: 8, y: 0 },
      voisinsDans: () => voisins,
      armeDe: (id) => ({ allonge: voisins.find((v) => v.id === id)?.allonge ?? 0 }),
      params: PARAMS.cheval,
    });
  const faceAuxPiques = essai(mur(4.5));
  const faceAuxEpees = essai(mur(1.1));
  const stoppe = faceAuxPiques.intensite >= 1 && Math.abs(faceAuxPiques.vel.x) < 0.5 && Math.abs(faceAuxPiques.vel.y) > 0.5;
  const passe = faceAuxEpees.intensite < 0.5 && faceAuxEpees.vel.x > 5;
  verdict(stoppe && passe && ticksRefus > 0,
    'refus',
    `5 piques levees : refus ${faceAuxPiques.intensite.toFixed(2)} (stoppe, derobe) ; 5 epees : ${faceAuxEpees.intensite.toFixed(2)} (passe) ; ${ticksRefus} ticks de refus vecus a La Conroi`);
}

// ── 10. L'horizon de masse : au loin on croit des MASSES — grossieres ──
{
  const { sim: simH } = courir(BATAILLE_RANGEE, { frames: 100, msParFrame: 100 });
  let voient = 0, precis = 0, total = 0;
  for (const id of simH.tous) {
    total++;
    const d = simH.cognition.perceptionDebug(id);
    const t = d.tas.find((x) => x.etiquette === 'ennemis');
    // une croyance sans position (la rumeur seedee par direction seule) n'est pas une masse vue
    if (!t || !t.barycentre) continue;
    const dist = Math.hypot(t.barycentre.x - d.moi.pos.x, t.barycentre.y - d.moi.pos.y);
    if (dist > 30 && t.lointain) voient++;
    // un percept lointain ne doit JAMAIS porter postures ni forme
    if (t.lointain && (t.prets !== undefined || t.cap !== undefined)) precis++;
  }
  verdict(voient > total / 2 && precis === 0,
    'masses',
    `${voient}/${total} croient une masse ennemie a +30 m — effectif a la poignee, sans postures ni forme`);
}

// ── 9. La volée : les carquois se vident pendant la traversée, puis le couteau ──
const { sim: simV } = courir(LA_VOLEE, { frames: 2000, msParFrame: 100 });
let flechesRestantes = 0;
let archersV = 0;
let auCouteau = 0;
let comptesFaux = 0;
let aTire = 0;
for (const id of simV.tous) {
  if (!simV.corpsContainer.arcTirDe(id)) continue;
  archersV++;
  flechesRestantes += simV.corpsContainer.flechesDe(id) ?? 0;
  // le journal est un ring : le VECU (cumulatif) fait foi
  const vecu = simV.cognition.introspecter(id).machine.vecu;
  if ((vecu.tempsParEtat['tuer.tire'] ?? 0) > 0) aTire++;
  const fl = simV.corpsContainer.flechesDe(id) ?? 0;
  if (fl < 0 || fl > 12) comptesFaux++; // le freestyle n'existe pas : 0 ≤ carquois ≤ botte
  if (fl === 0) auCouteau++; // carquois vidé : il ne reste que le couteau
}
const touchesV = simV.tous.filter((id) => simV.corpsContainer.blessuresDe(id) > 0).length;
verdict(
  archersV > 0 && aTire > 0 && flechesRestantes < archersV * 12 && comptesFaux === 0 && touchesV > 0,
  'volee',
  `${archersV} archers, ${archersV * 12 - flechesRestantes} flèches parties (comptées, bornées), ${touchesV} hommes touchés, ${auCouteau} carquois vidés`
);

// ── 11. Le terrain masque : la ville cuite bloque, la porte laisse passer ──
// Revenu le 1er septembre avec Gallipoli (etat/villes/gallipoli.json cuit par
// scripts/monde/cuire_ville.py). Le masque vit dans le moteur ; absent, le cas
// se SAUTE en le disant — un saut n'est ni un échec ni un silence.
{
  let bits = null, metaMasque = null;
  const chem = resoudreMontage(ASSAUT_DE_RUE.terrain.masque.fichier);
  try { bits = new Uint8Array(readFileSync(chem)); } catch { /* source absente */ }
  // La géométrie ne se répète PAS ici : la Porte de fer se lit dans le
  // `.masque.json` cuit à côté du `.bin`, seule autorité sur l'endroit où le
  // mur est percé. Un scénario reposé ailleurs sur la carte (voir POSE dans
  // assaut-de-rue.js) ne casse alors plus ce cas — c'était le cas avant, avec
  // un « 835, 600 » écrit à la main qui datait du tracé du bourg.
  try { metaMasque = JSON.parse(readFileSync(chem.replace(/\.bin$/, '.json'), 'utf8')); } catch { /* idem */ }
  if (!bits || !metaMasque) {
    console.log(`SAUTE  terrain-masque — masque ou meta absent : ${chem}`);
  } else {
    const ressources = { masque: { ...ASSAUT_DE_RUE.terrain.masque, bits } };
    const { photo: pA, sim: simT } = courir(ASSAUT_DE_RUE, { frames: 300, msParFrame: 100, ressources });
    const attendus = ASSAUT_DE_RUE.unites.reduce((n, u) => n + 1 + u.hommes.length, 0);
    verdict(simT.tous.length === attendus, 'masque-spawns',
      `${simT.tous.length}/${attendus} spawns acceptés — personne ne naît dans un mur`);
    // la vérité du masque : la Porte de fer est une percée du château
    // extérieur. Au centre de la porte un homme passe ; à 60 m autour, il y a
    // du mur. Les deux coordonnées sortent du meta, en mètres.
    const perce = metaMasque.perces.find((x) => /fer/i.test(x.nom || '')) ?? metaMasque.perces[0];
    const mpu = metaMasque.metres_par_unite ?? 1;
    const PORTE = { x: perce.ou[0] * mpu, y: perce.ou[1] * mpu };
    const porte = simT.monde.terrain.chevaucheObstacle(PORTE, 0.35);
    const autour = simT.monde.terrain.casesBloqueesDans({ x: PORTE.x - 30, y: PORTE.y - 30, largeur: 60, hauteur: 60 }).length;
    verdict(!porte && autour > 50, 'masque-porte',
      `la percée laisse passer (libre en ${PORTE.x},${PORTE.y}), le mur bloque autour (${autour} cases bloquées à 30 m)`);
    // et un homme vivant n'est jamais DANS un mur après 30 s de sortie
    const dedans = simT.tous.filter((id) => {
      const c = simT.monde.corpsParId(id);
      return c.posture !== 'gisant' && simT.monde.terrain.chevaucheObstacle(c.pos, c.rayon * 0.5);
    }).length;
    verdict(dedans === 0, 'masque-murs', `${dedans} homme(s) dans un mur après 30 s — le masque tient`);
    const { photo: pB } = courir(ASSAUT_DE_RUE, { frames: 300, msParFrame: 100, ressources });
    verdict(pA === pB, 'masque-determinisme', 'même seed sur la ville : états bit-exacts');

    // LA SORTIE FRANCHIT LE REMPART SANS LE TRAVERSER. Les Catalans naissent
    // DANS la place, les Génois attendent dehors : pour les joindre il faut
    // sortir, et le mur n'a que ses percées. C'est le chemin A* contre le
    // masque qui est mesuré — la faute qu'on guette est un homme qui coupe
    // à travers la courtine parce que la grille l'a oublié.
    //
    // Ce qui est affirmé tient sans connaître la géométrie : personne
    // n'occupe une case bloquée, à AUCUN moment de la sortie (et
    // non pas seulement à l'arrivée), et la troupe sort quand même.
    // On vise les hommes par leur NAISSANCE, jamais par l'index de leur
    // unité : le scénario gagne et perd des bannières au fil des sources.
    const simS = composer(ASSAUT_DE_RUE, ressources);
    const nesDedans = simS.tous.filter((id) => {
      const c = simS.monde.corpsParId(id);
      return c.livree === 'jaune' && c.pos.y <= PORTE.y + 0.5;
    });
    const departY = new Map(nesDedans.map((id) => [id, simS.monde.corpsParId(id).pos.y]));
    const fautifs = new Set();
    for (let f = 0; f < 400; f++) { // 40 s (a 80 s le compte est le meme : ce n est pas une course)
      simS.orchestration.avancer(100);
      if (f % 5) continue;
      for (const id of nesDedans) {
        const c = simS.monde.corpsParId(id);
        if (c.posture !== 'gisant' && simS.monde.terrain.chevaucheObstacle(c.pos, c.rayon * 0.5)) fautifs.add(id);
      }
    }
    const sortis = nesDedans.filter((id) => simS.monde.corpsParId(id).pos.y - departY.get(id) > 20);
    // une POIGNEE suffit a prouver que la voie existe : le compte exact est
    // celui du scenario du jour, et il change avec ses bannieres.
    verdict(nesDedans.length >= 20 && sortis.length >= 5 && fautifs.size === 0,
      'sortie-rempart',
      `${nesDedans.length} Catalans nés dans la place ; ${sortis.length} ont gagné vingt mètres au sud du rempart, ${fautifs.size} l'ont traversé — le mur tient tout du long`);
  }
}

// ── 9. La déroute : la peur casse l'unité surclassée — jamais depuis engage ──
const { sim: simD } = courir(FACE_A_FACE, { frames: 320, msParFrame: 100 });
const rupturesD = [];
for (const id of simD.tous) {
  for (const e of simD.cognition.introspecter(id).machine.journal) {
    if (e.libelle.includes('romps !')) rupturesD.push(e.de);
  }
}
const depuisEngage = rupturesD.filter((d) => d === 'tuer.engage').length;
verdict(rupturesD.length > 0 && depuisEngage === 0, 'deroute',
  `${rupturesD.length} ruptures — aucune depuis engage (au fer, pas le temps d'y penser)`);

// ── 12. Le vol : le poste du faucon — z tenu, banque bornée, path CONTINU ──
{
  const simV = composer(LES_OISEAUX);
  const faucon = simV.monde.corpsParId(simV.oiseaux[1]);
  const profilF = OISEAUX.faucon;
  let sautMax = 0;
  let banqueMax = 0;
  let zMin = Infinity;
  let zMax = -Infinity;
  let rotationCumulee = 0;
  let avant = null;
  for (let f = 0; f < 1800; f++) { // 180 s en frames de 100 ms
    simV.orchestration.avancer(100);
    if (avant) {
      sautMax = Math.max(sautMax, Math.hypot(faucon.pos.x - avant.x, faucon.pos.y - avant.y, faucon.vol.z - avant.z));
      rotationCumulee += Math.abs(Math.atan2(Math.sin(faucon.cap - avant.cap), Math.cos(faucon.cap - avant.cap)));
    }
    avant = { x: faucon.pos.x, y: faucon.pos.y, z: faucon.vol.z, cap: faucon.cap };
    if (f > 600) { // le cercle établi (après la mise en place)
      banqueMax = Math.max(banqueMax, Math.abs(faucon.vol.banque));
      zMin = Math.min(zMin, faucon.vol.z);
      zMax = Math.max(zMax, faucon.vol.z);
    }
  }
  const introF = simV.cognition.introspecter(simV.oiseaux[1]);
  const boucles = rotationCumulee / (2 * Math.PI);
  // le pas d'une frame ne peut pas dépasser ce que le piqué du profil permet
  const pasMax = profilF.pique * 0.1 * 1.35;
  verdict(
    sautMax < pasMax && banqueMax < 1.45 && zMin > 1 && zMax < 240 && boucles > 1.5 && introF.brain === 'oiseau',
    'vol',
    `le faucon vole (${boucles.toFixed(1)} tours en 180 s), z ${zMin.toFixed(0)}-${zMax.toFixed(0)} m, banque max ${((banqueMax * 180) / Math.PI).toFixed(0)}°, plus grand pas ${sautMax.toFixed(1)} m (borne ${pasMax.toFixed(1)}) — introspectable`
  );
  const { photo: pV1 } = courir(LES_OISEAUX, { frames: 300, msParFrame: 100 });
  const { photo: pV2 } = courir(LES_OISEAUX, { frames: 300, msParFrame: 100 });
  verdict(pV1 === pV2, 'vol-determinisme', 'même seed avec les oiseaux : états bit-exacts (z compris)');
}

// ── 13. DEUX BÊTES, DEUX MÉTIERS — la même machine, des chiffres différents.
// Le test de falsifiabilité du catalogue : si le corbeau n'est qu'un faucon
// ralenti, le profil n'est pas propagé. Le corbeau tient un poste bas et
// traîne dans sa passe ; le faucon se poste haut et fond.
{
  const simD = composer(LES_OISEAUX);
  const [idCorbeau, idFaucon] = simD.oiseaux;
  let zCorbeauMax = 0;
  let zFauconMax = 0;
  let vFauconMax = 0;
  let vCorbeauMax = 0;
  for (let f = 0; f < 4000; f++) { // 400 s
    simD.orchestration.avancer(100);
    const c = simD.monde.corpsParId(idCorbeau);
    const fa = simD.monde.corpsParId(idFaucon);
    zCorbeauMax = Math.max(zCorbeauMax, c.vol.z);
    zFauconMax = Math.max(zFauconMax, fa.vol.z);
    vCorbeauMax = Math.max(vCorbeauMax, c.vol.vitesseAir);
    vFauconMax = Math.max(vFauconMax, fa.vol.vitesseAir);
  }
  const vecuC = simD.cognition.introspecter(idCorbeau).machine.vecu;
  const vecuF = simD.cognition.introspecter(idFaucon).machine.vecu;
  const passeC = vecuC.tempsParEtat['passe'] ?? 0;
  const passeF = vecuF.tempsParEtat['passe'] ?? 0;
  verdict(
    zFauconMax > zCorbeauMax * 1.8 && vFauconMax > vCorbeauMax * 1.8 && passeC > passeF,
    'deux-betes',
    `le faucon se poste à ${zFauconMax.toFixed(0)} m et pointe à ${vFauconMax.toFixed(0)} m/s ; le corbeau à ${zCorbeauMax.toFixed(0)} m et ${vCorbeauMax.toFixed(0)} m/s — et il traîne ${passeC.toFixed(0)} s en passe basse contre ${passeF.toFixed(0)} s`
  );
}

// ── 14. LES OISEAUX NE FONT DE MAL À PERSONNE — et personne ne les craint :
// un corps d'un kilo pèse moins qu'un homme (poids de gabarit), il vole trop
// haut pour être un contact, et aucune de ses intentions ne blesse.
{
  const simP = composer(LES_OISEAUX);
  for (let f = 0; f < 3000; f++) simP.orchestration.avancer(100); // 300 s
  const blesses = simP.tous.filter((id) => simP.corpsContainer.blessuresDe(id) > 0).length;
  const morts = simP.tous.filter((id) => !simP.corpsContainer.estVivant(id)).length;
  let enTuer = 0;
  let ruptures = 0;
  for (const id of simP.tous) {
    if (simP.cognition.introspecter(id).etat.startsWith('tuer')) enTuer++;
    for (const e of simP.cognition.introspecter(id).machine.journal) {
      if (e.libelle.includes('romps')) ruptures++;
    }
  }
  verdict(blesses === 0 && morts === 0 && enTuer === 0 && ruptures === 0,
    'oiseaux-inoffensifs',
    `après 300 s sous deux oiseaux : ${blesses} blessé, ${morts} mort, ${enTuer} en tuer, ${ruptures} rupture — le ciel n'est pas une menace`);
}

process.exit(echecs ? 1 : 0);
}
