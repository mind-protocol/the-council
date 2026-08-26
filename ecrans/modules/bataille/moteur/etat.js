// etat.js — L'ÉTAT DE LA SIMULATION, nommé et rassemblé.
//
// CE QU'IL REMPLACE. Soixante-cinq variables libres déclarées au fil de onze
// mille lignes de `bataille2d.js`, entre la ligne 499 et la ligne 8948. Elles
// marchaient très bien — ce n'est pas leur correction qui posait problème, et
// ce fichier ne corrige aucun défaut.
//
// POURQUOI ALORS. Parce que tant que l'état vit en variables libres, RIEN NE
// PEUT SORTIR DU MONOLITHE. Un module de monde physique extrait demain devra
// lire les positions, le bâti, la voirie ; un module d'unité devra lire les
// escouades et les formations. On ne peut rien leur passer : il n'y a pas
// d'objet, il y a des noms visibles depuis l'intérieur d'une fermeture, et
// depuis nulle part ailleurs. C'est le verrou du refactor entier, et c'est la
// seule chose que ce fichier lève.
//
// CE QU'IL N'EST PAS. Ce n'est pas un magasin où tout le monde écrit. Le
// tableau d'autorité du refactor tient toujours : une donnée a UN écrivain, les
// autres la lisent. Rassembler l'état ne redistribue aucun droit — au
// contraire, ça permet enfin de dire lequel, puisqu'on peut enfin les nommer.
// Les groupes ci-dessous sont ces futurs propriétaires, écrits d'avance :
// quand le monde physique sortira, il emportera son groupe et pas un champ de
// plus.
//
// CE QU'IL NE CONTIENT PAS, ET DÉLIBÉRÉMENT. Les constantes de mesure — la
// largeur d'épaule, la vitesse de marche, les points de bois d'une porte. Elles
// restent où elles sont : ce sont des mesures d'homme, pas de l'état. Un état
// est ce qui CHANGE pendant une bataille ; le reste est du savoir.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleEtatSim = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  /**
   * `creer` — un état neuf, aux valeurs exactes qu'avaient les déclarations.
   *
   * On rend un objet littéral d'un seul tenant plutôt que de le construire
   * champ par champ : V8 lui donne alors une forme unique et stable, et les
   * mille trois cents accès qui remplacent les anciennes variables libres
   * restent monomorphes. Un état bâti par assignations successives changerait
   * de forme cinq fois et coûterait, lui, quelque chose.
   */
  function creer() {
    return {

      // ---- LE MONDE PHYSIQUE ------------------------------------------
      // Le sol, le bâti, l'eau, la voirie et le plan. Écrits par `preparer()`
      // au chargement, puis lus par tout le monde et réécrits par personne —
      // c'est le groupe qui partira le premier, au lot 2.
      plan: null,                     // le plan2d servi par /monde
      J: null,                        // le module de voirie, une fois importé
      voirie: null,                   // le graphe des rues
      sousToit: null,                 // où sont les murs — un intérieur possible
      sousEau: null,                  // où l'on ne pose pas le pied en armure
      bati: null,                     // le bâti qu'on pille, chargé à part
      terrainEpreuve: null,           // le sol abstrait d'une épreuve, s'il y en a
      source: "/monde",               // d'où viennent les données du monde

      // La grille de voisinage, en style CSR : deux tableaux d'entiers et
      // quatre bornes, jamais une Map à clefs de texte. Fabriquer une clef
      // « 11-3:4127 » quatre cent mille fois par image coûtait neuf secondes.
      gI0: 0, gJ0: 0,                 // le coin de la grille, en cases
      gCol: 0, gLig: 0,               // sa taille, en cases
      gDebut: new Int32Array(0),      // ncases + 1 bornes
      gCorps: new Int32Array(0),      // les indices dans `hommes`, rangés par case
      semis: new Map(),

      // ---- LES COMBATTANTS --------------------------------------------
      hommes: [],                     // les deux camps, dans le même tableau
      prochainHommeDebug: 0,          // identité stable pendant un rejeu
      roi: null,                      // Aegon, et sa presse
      figures: [],                    // ceux qui ne se battent pas

      // ---- LES UNITÉS -------------------------------------------------
      // `escouades` est le canal d'ordres de l'assaut ; `formations` est neutre
      // au camp et porte aussi bien une vintaine en marche qu'un poste de garde.
      escouades: [],
      formations: [],
      ailes: [],                      // cinq escouades chacune — ce qu'on COMMANDE
      tetes: [],                      // ceux qui décident, un par corps
      routesFormation: new Map(),
      deploiements: new Map(),        // les places des échelons d'un ralliement
      centreAile: [],                 // par id d'aile, refait à chaque pas
      centreCorps: {},                // l'aile de tête encore vivante de chaque corps
      enArmes: new Map(),             // zone -> { assaut, garde }

      // ---- LE COMMANDEMENT --------------------------------------------
      carteCommandantId: null,        // la seule carte subjective ouverte
      ratissages: new Map(),
      prochainRatissage: 0,
      messagers: [],                  // les coureurs partis vers le Donjon
      conseil: { averti: 0, tenir: 0, ouvrir: 0, tranche: false },
      _ordreN: 0,                     // le compteur d'ordres, pour `memeOrdre`

      // ---- L'OBJECTIF ET LES PORTES -----------------------------------
      objectif: null,                 // le Donjon Rouge, en mètres
      entree: null,                   // la porte visée, en mètres
      verrou: null,                   // le verrou de la porte engagée
      verrous: [],                    // un par porte engagée
      anneauOuvert: false,            // plus personne ne tient le cercle

      // ---- LA VILLE QUI SUBIT -----------------------------------------
      paniques: [],                   // les enregistrements, à plat
      foyers: [],                     // les masses agrégées de la foule
      reseau: null,
      abris: [],
      incendiesSignales: new Map(),
      prochainePerceptionIncendie: -Infinity,

      // ---- LE TEMPS ET LA BOUCLE --------------------------------------
      // `temps` est le temps de bataille, en secondes ; `reste` l'accumulateur
      // de pas fixes ; `dernier` la dernière image, en millisecondes du
      // navigateur. Trois horloges qui ne se confondent pas.
      temps: 0,
      reste: 0,
      dernier: 0,
      boucle: 0,                      // l'identifiant de requestAnimationFrame
      marche: false,                  // la bataille tourne-t-elle
      arret: null,                    // ce qui a arrêté la nuit, s'il y a lieu
      ECHELLE: 1,

      // ---- CE QU'ON A VU ET CE QU'ON EN DIT ---------------------------
      annales: [],
      dits: new Set(),
      sillageDu: 0,
      rumeurDu: -1,

      // ---- LA LUNETTE — l'affichage, et rien de la simulation ----------
      // Ce groupe n'a aucune influence sur une bataille : il ne décide rien,
      // et le four tourne sans lui. Il est ici parce qu'il vivait dans les
      // mêmes variables libres, et il partira dans les modules de page au
      // dernier lot, quand le rendu quittera le moteur.
      toile: null, ctx: null, hote: null, vueDe: null,
      barre: null, lecture: null,
      pret: null, rate: null,
      surligne: null,
    };
  }

  return { creer };
});
