/**
 * ❤️ Corps / Oiseaux — LE CATALOGUE : un oiseau est une DONNÉE (le pendant
 * volant d'armes.js) — jamais un if/else sur l'espèce ailleurs. Chaque entrée
 * porte ses faits physiques : gabarit, régimes de vol, conduite de descente,
 * plumage rendu.
 *
 * Deux bêtes, et elles ne font pas le même métier. Le CORBEAU suit les
 * armées : il tient un large cercle haut, se laisse tomber en spirale quand
 * quelque chose l'intéresse, et tourne bas, longtemps, au-dessus de ce qu'il
 * guette. Le RAPACE DE CHASSE monte se poster, ferme les ailes et FOND — sa
 * passe dure deux secondes et il remonte aussitôt reprendre son poste.
 *
 * Le test de falsifiabilité : si le corbeau n'est qu'un faucon ralenti à
 * l'écran, le profil n'est pas correctement propagé. Leur différence n'est
 * pas cosmétique — elle est dans le piqué (18 m/s contre 78), la durée de la
 * passe (22 s contre 2,2) et la hauteur du poste (65 m contre 185).
 *
 * Aucun des deux ne fait de mal à personne : ils volent au-dessus de la
 * bataille, ils n'y entrent pas.
 *
 * `approcheDist` VAUT LE RAYON DU CERCLE (🧠 machine.js : 16 + 0,26 × la
 * hauteur du poste) : c'est en tournant que la bête se présente à son entrée,
 * elle ne va pas chercher un point d'approche ailleurs. Les découpler, c'est
 * un oiseau qui tourne éternellement sans jamais se décider.
 *
 * Unités : m, kg, m/s, Hz, s ; banques en DEGRÉS (converties à l'usage).
 */

export const OISEAUX = {
  // LE CORBEAU — il ne fond pas, il attend. Cercle large et haut, descente
  // en spirale, puis un long tour bas au-dessus de ce qui l'intéresse.
  corbeau: {
    nom: 'Un corbeau',
    silhouette: 'corvide',
    // gabarit — des faits qui SE VOIENT (le rendu et la perception les lisent)
    masse: 1.2, longueur: 0.64, envergure: 1.25, surface: 0.11,
    // vol : régimes et bornes de pilotage
    croisiere: 11, presse: 16, limite: 24, pique: 18,
    battementHz: 3.2, battementLentHz: 4.4, accelLateral: 5.5,
    volLent: 5, volLentMin: 3.5, freinLent: 4, lacetLent: 1.6,
    banqueLente: 18, banqueRalliement: 45, banquePiqueHaut: 40,
    banquePiqueBas: 45, banquePasse: 35, attenteLenteS: 12,
    minimumVol: 4, plancher: 3, // m — un corbeau rase le sol, il ne le touche pas
    accelMax: 1.8, accelPique: 3.2, // m/s² — il se laisse tomber, il ne fond pas
    // la passe : chez lui, c'est une PATIENCE — vingt secondes de tours bas
    pentePasse: 25, dureePasseS: 22, vitessePasse: 9,
    // conduite : le poste, l'entrée, les hauteurs
    approcheDist: 33, approcheVitesse: 10, altitudeRalliement: 65,
    altitudePasse: 16, altitudePique: 9, altitudeSortie: 65,
    vitesseSortie: 11, sortieDeclenche: 45, patienceRalliementS: 34,
    // ce qui vaut le coup d'œil : large et proche (il n'a pas besoin de viser)
    opportunite: 55, opportuniteLargeur: 22,
    // le plumage — des couleurs et des longueurs, pas des types
    plumage: { corps: '#23252b', trait: '#4a4e59', ventre: '#15171b' },
  },

  // LE RAPACE DE CHASSE — le poste haut, les ailes fermées, la passe brève.
  // Le piqué est toute son identité : quatre fois celui du corbeau.
  faucon: {
    nom: 'Un faucon',
    silhouette: 'rapace',
    masse: 0.9, longueur: 0.46, envergure: 1.05, surface: 0.07,
    croisiere: 14, presse: 24, limite: 85, pique: 78,
    battementHz: 4.2, battementLentHz: 5.5, accelLateral: 8,
    volLent: 6, volLentMin: 4.5, freinLent: 6, lacetLent: 2,
    banqueLente: 22, banqueRalliement: 60, banquePiqueHaut: 30,
    banquePiqueBas: 45, banquePasse: 40, attenteLenteS: 8,
    minimumVol: 5, plancher: 2,
    accelPique: 11, accelMax: 2.6, // m/s² — ailes fermées, la pesanteur le tire
    pentePasse: 55, dureePasseS: 2.2, vitessePasse: 30,
    approcheDist: 64, approcheVitesse: 16, altitudeRalliement: 185,
    altitudePasse: 9, altitudePique: 5, altitudeSortie: 185,
    vitesseSortie: 15, sortieDeclenche: 130, patienceRalliementS: 26,
    opportunite: 60, opportuniteLargeur: 8,
    plumage: { corps: '#6d6353', trait: '#cbbfa4', ventre: '#ded2b6' },
  },
};
