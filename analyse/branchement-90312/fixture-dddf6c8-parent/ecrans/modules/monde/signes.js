// monde/signes.js — un signe par espèce de chose.
//
// Le survol donne un nom et un rôle ; il lui manquait de se lire SANS être lu.
// Un signe en tête de l'étiquette fait ce travail : on reconnaît une forge, une
// taverne, une roukerie avant d'avoir déchiffré le mot, et l'on balaie une
// ville du curseur en sachant ce qu'on traverse. C'est la même fonction qu'une
// légende de carte, en un caractère et sans légende.
//
// Trois disciplines :
//  - **Un signe dit l'ESPÈCE, jamais l'individu.** Toutes les tavernes ont le
//    même ; la Gaffe n'a pas le sien. Sans quoi ce n'est plus une légende, c'est
//    une décoration, et elle cesse d'apprendre quoi que ce soit.
//  - **Une seule table pour les métiers et pour les salles.** Les volumes du
//    château portent un usage par pièce (`chateau-roukerie`) et les intérieurs
//    portent le même mot comme identifiant de salle (`roukerie`) : on retire le
//    préfixe et les deux tombent sur la même entrée. Deux tables auraient
//    divergé au premier ajout.
//  - **Le repli est une CATÉGORIE, pas un point d'interrogation.** Un métier
//    qu'on n'a pas prévu retombe sur sa `cat` (artisanat, nuisance, culte…) :
//    c'est moins précis et ça reste vrai. Rien n'affiche jamais un signe
//    d'ignorance — mieux vaut pas de signe du tout.
"use strict";

// Par métier de bâtiment et par salle, la même table. Les clefs sans préfixe
// servent aux deux (`forge` est un métier de la ville ET une pièce du château).
const PAR_ESPECE = {
  // ── se loger ────────────────────────────────────────────────────────────
  maison: "🏠", "maison-pecheur": "🏠", "maison-officier": "🎖", manse: "🏡",
  taudis: "🛖", cabane: "🛖",
  appartements: "🛏", "appartements-reine": "🛏", "salle-levant": "🍽",
  enfants: "👶", "chambre-enfants": "👶", hotes: "🧳", "chambres-hotes": "🧳",

  // ── vendre, garder, transporter ─────────────────────────────────────────
  echoppe: "🏪", entrepot: "📦", hangar: "🛶", "chantier-bois": "🪵",
  "marche-quartier": "🧺", change: "🪙", grenier: "🌾", cellier: "🍷",
  "bureau-port": "⚓", quai: "⚓", greve: "🐚",

  // ── faire de ses mains ──────────────────────────────────────────────────
  forge: "⚒", "forge-bourg": "⚒", boulangerie: "🍞", brasserie: "🍻",
  moulin: "⚙", corderie: "🪢", voilerie: "🪡", sechoir: "🐟", saline: "🧂",
  officine: "⚗", "guilde-alchimistes": "⚗",

  // ── ce qui sent mauvais et qu'on met sous le vent ───────────────────────
  tannerie: "🐄", teinturerie: "🎨", poterie: "🏺", abattoir: "🔪",
  boucanerie: "🔥", "fosse-vidange": "🕳",

  // ── boire, dormir, se laver ─────────────────────────────────────────────
  taverne: "🍺", auberge: "🛏", bordel: "🌹", etuve: "♨", etuves: "♨",
  cuisines: "🍲", communs: "🧺", puits: "💧", "salle-froide": "❄",

  // ── prier ───────────────────────────────────────────────────────────────
  septuaire: "✴", "septuaire-quartier": "✴", "septuaire-bourg": "✴",
  "vieux-septuaire": "✴",

  // ── commander, garder, punir ────────────────────────────────────────────
  "corps-de-garde": "🛡", caserne: "⚔", baraques: "⚔", geole: "⛓",
  cachots: "⛓", guet: "👁", "chemin-ronde": "👁",
  porte: "🚪", "porte-de-mer": "🚪", "porte-dragon": "🚪", antichambre: "🚪",
  ecurie: "🐴",

  // ── le pouvoir, et ce qui n'appartient qu'à lui ─────────────────────────
  "donjon-rouge": "👑", "grande-salle": "🏛", "table-peinte": "🗺",
  galeries: "🖼", archives: "📜", roukerie: "🐦",
  "fosse-dragons": "🐉", fosses: "🐉",
  tour: "🗼", "tambour-de-pierre": "🗼", "tour-dragon-mer": "🗼",
  "guivre-des-vents": "🗼", "grand-escalier": "🪜",

  // ── ce qui n'a pas de toit ──────────────────────────────────────────────
  cour: "🧱", bourg: "🏘", lices: "🏇", "jardin-aegon": "🌿",
};

// Le repli : la catégorie que le bâti porte déjà pour chaque métier.
const PAR_CAT = {
  habitat: "🏠", commerce: "🪙", artisanat: "⚒", nuisance: "🕳",
  service: "🛏", plaisir: "🍺", culte: "✴", civique: "🛡", institution: "👑",
};

// Et le dernier repli, par nature de la chose désignée.
const PAR_GENRE = {
  bati: "🏠", salle: "🕯", "salle-dehors": "🏞", mur: "🧱", porte: "🚪",
  edifice: "🏛",
};

/**
 * Le signe d'une chose.
 * `cle`   — un métier de bâtiment ou un identifiant de salle, avec ou sans son
 *           préfixe `chateau-`.
 * `cat`   — sa catégorie, si le bâti en donne une (repli).
 * `genre` — sa nature (repli du repli) : `bati`, `salle`, `salle-dehors`, `mur`,
 *           `porte`, `edifice`.
 */
export function signe(cle, cat, genre) {
  const k = String(cle || "").replace(/^chateau-/, "");
  return PAR_ESPECE[k] || PAR_ESPECE[cle] || PAR_CAT[cat]
    || PAR_GENRE[genre] || "";
}
