/**
 * 🧠 Langage / Répliques — le RÉPERTOIRE de la parole flavor : des variantes
 * par situation, en DONNÉE (comme les machines). Registre Westeros assumé.
 * Le tirage passe par le flux rng DÉDIÉ des paroles (jamais celui de la
 * sim) : le répertoire peut grossir sans changer une bataille.
 * Consommateur : cognition/paroles.js.
 */

export const REPLIQUES = {
  // ── la rupture : le moral casse, on tourne le dos ──
  rupture: [
    'Sauve qui peut !',
    "C'est perdu ! Fuyez !",
    'Les dieux nous ont abandonnés !',
    'Je veux pas mourir ici !',
    'Tout est perdu !',
  ],
  // la peur qui monte, avant le seuil — on tient encore, mais on le dit
  peurMonte: [
    'Ils sont trop nombreux…',
    'On va tous y rester…',
    'Tenez la ligne… tenez…',
    'Les dieux soient bons…',
    "Valar morghulis, qu'ils disaient…",
  ],
  // l'ennemi surgit : la rencontre commence
  alarme: [
    'Les voilà !',
    'Aux armes !',
    'Ils viennent !',
    'Debout ! Ils sont là !',
  ],
  // l'assaut part — le cri de charge du rang
  assaut: [
    'Sus ! À mort !',
    'Pas de quartier !',
    'Taillez-les !',
    'Pour le roi !',
  ],
  // la charge sonnée — on court sur l'ennemi
  charge: [
    'Chaaargez !',
    'En avant ! Écrasez-les !',
    'Pour le trône !',
  ],
  // la curée : ils rompent, la joie mauvaise
  curee: [
    'Ils rompent ! Ha !',
    'Courez, lâches !',
    'La curée ! Sus !',
    'Regardez-les détaler !',
  ],
  // le retour de fuir : on reprend ses esprits
  soulagement: [
    '…encore vivant.',
    'Les dieux sont bons.',
    'Plus jamais ça.',
  ],
  // le souffle qui manque
  souffleBas: [
    "Je n'en peux plus…",
    'Mes jambes me lâchent…',
    'Un instant… juste un instant…',
  ],
  // le carquois vidé
  carquoisVide: [
    'Plus de flèches !',
    'À sec ! Au couteau !',
  ],
  // le face-à-face tendu : les insultes portent plus loin que les piques
  defi: [
    'Approche, joli cœur !',
    'Ta mère était une chèvre !',
    'Viens, que je te raccourcisse !',
    "C'est tout ce qu'ils envoient ?",
    'Bâtard sans terre !',
  ],
  // le cercle de discussion : les rumeurs du camp
  bavardage: [
    'On dit que le roi est encore mort.',
    "L'hiver vient, mon gars.",
    'La solde est en retard. Comme toujours.',
    'Mon frère jure avoir vu un dragon. Il boit trop.',
    'Après ça, la taverne. Promis.',
    "Les corbeaux n'apportent que du mauvais.",
  ],
  // seul, désœuvré : on se parle à soi-même
  flanerie: [
    "Trop calme. J'aime pas ça.",
    "Mes bottes prennent l'eau.",
    'Un corbeau. Mauvais présage.',
    "Qu'est-ce qu'on attend, au juste ?",
  ],
};

/**
 * Tire une réplique du répertoire. Un tirage rng par appel — TOUJOURS,
 * même si la clé est inconnue (discipline de déterminisme : le flux de
 * tirages ne dépend pas du contenu du répertoire).
 * @param {{uniforme: () => number}} rng
 * @param {string} cle
 * @returns {string|null}
 */
export function choisir(rng, cle) {
  const variantes = REPLIQUES[cle];
  const tirage = rng.uniforme();
  if (!variantes || variantes.length === 0) return null;
  return variantes[Math.floor(tirage * variantes.length) % variantes.length];
}
