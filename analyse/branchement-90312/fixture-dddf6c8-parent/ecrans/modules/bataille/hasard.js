// hasard.js — le seul hasard de la bataille, et il est reproductible.
//
// POURQUOI CELUI-CI SORT EN PREMIER. C'est la seule feuille vraie du fichier :
// il ne dépend de rien, tout dépend de lui, et il n'a pas une ligne d'état
// partagé avec le reste. C'est donc le seul morceau qu'on puisse déplacer sans
// définir d'interface — les autres découpages en demanderont une, celui-ci non.
//
// C'est aussi le seul qu'on puisse TESTER pour de bon : quatre fonctions pures,
// une graine, et des propriétés qu'on sait énoncer (une moyenne, un écart-type,
// des bornes). Le jour où l'on voudra vérifier que la cuisson n'a pas dérivé,
// c'est ici qu'on regardera.
//
// REJOUABLE, ET IL A FALLU LE RENDRE VRAI. La graine était posée à la
// construction du module et n'était jamais remise : deux `rejouer()` dans la
// même session donnaient deux batailles différentes, alors que le commentaire
// promettait le contraire. Tant qu'on regardait, ça ne se voyait pas ; le jour
// où l'on CUIT une bataille dans un fichier, un déroulé qui ne se reproduit pas
// est un fichier qu'on ne peut ni vérifier ni corriger. D'où `semer()`, qu'on
// appelle au moment de dresser l'ordre de bataille.
//
// SCRIPT CLASSIQUE, PAS MODULE ES, et c'est délibéré. `bataille2d.js` est
// chargé par un `<script>` nu et trois modules le lisent en synchrone
// (`carte-ville.js`, `capture.js`) ; passer la chaîne en `type="module"` la
// ferait charger en différé, donc après eux. Le jour où l'on voudra les modules
// ES, ce sera un chantier à soi — pas un effet de bord d'un découpage.
"use strict";
window.BatailleHasard = (() => {

  // Un générateur congruentiel linéaire, celui de la bibliothèque C. Il ne vaut
  // rien en cryptographie et tout ici : il tient en une ligne, il est le même
  // dans un navigateur et dans le four, et il se rembobine.
  const GRAINE = 20161219;
  let _s = GRAINE;
  const R = () => (_s = (_s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;

  /** Remettre la graine — la même bataille, à chaque fois qu'on la dresse. */
  const semer = (g) => { _s = g === undefined ? GRAINE : g; };

  // Un tirage plat sur [a, b].
  const entre = (a, b) => a + R() * (b - a);

  // ---- ET LA MÊME CHOSE, MAIS EN CLOCHE -------------------------------------
  // UN INTERVALLE PLAT EST PRESQUE TOUJOURS UNE ERREUR DE MODÉLISATION, et ce
  // fichier en était plein. Quand on écrit « le dégât va de 14 à 30 », on ne
  // veut pas dire qu'un coup de 14 est aussi fréquent qu'un coup de 22 — on
  // veut dire qu'un coup ORDINAIRE fait 22 et qu'il arrive, rarement, qu'il
  // fasse très peu ou beaucoup. La loi plate dit le contraire : elle rend les
  // extrêmes aussi courants que le milieu, donc elle fabrique un monde sans
  // ordinaire, où tout est également remarquable et où plus rien ne l'est.
  //
  // Somme de quatre tirages (Irwin–Hall), donc bornée à [a, b] PAR
  // CONSTRUCTION : pas d'écrêtage, donc pas de bosse artificielle aux deux
  // extrémités — ce qui est exactement le défaut qu'une gaussienne tronquée
  // aurait introduit ici. Écart-type ≈ 0,144 × (b − a), soit à peu près trois
  // écarts et demi de part et d'autre du milieu.
  //
  // QUAND GARDER `entre` : quand l'intervalle n'est pas une VARIATION autour
  // d'un ordinaire mais un REMPLISSAGE ou une PHASE. Le semis d'un corps dans
  // son rectangle de formation doit être plat, sinon les hommes s'entassent au
  // milieu et les bords s'amincissent ; le décalage initial des cadences doit
  // être plat, sinon les coups se regroupent au lieu de se désynchroniser —
  // c'est même toute la raison d'être de ce tirage-là.
  const cloche = (a, b) =>
    (a + b) / 2 + ((R() + R() + R() + R() - 2) / 2) * (b - a) / 2;

  // ---- LES TROIS DÉVIATIONS — CE QUI FAIT QUE DEUX HOMMES DIFFÈRENT ---------
  // Elles sont ici parce qu'elles sont du hasard et rien d'autre : trois
  // tirages indépendants, faits une fois pour toutes à l'engendrement, jamais
  // retouchés ensuite. Ce qu'elles SIGNIFIENT appartient à la mêlée ; ce
  // qu'elles VALENT appartient à ce fichier.
  //
  // NORMALE, PAS UNIFORME, et ce n'est pas un détail : sur une loi plate on
  // aurait autant de casse-cou que d'ordinaires, et la ligne se déferait
  // partout à la fois. Sur une normale, la masse est au milieu et les extrêmes
  // sont rares — ce sont EUX qui font les accidents locaux : un point qui tient
  // quand tout lâche autour, un autre qui part trop tôt et entraîne ses trois
  // voisins par la contagion.
  //
  // ET ELLES SONT INDÉPENDANTES, ce qui est tout leur intérêt. Le courage n'est
  // pas l'endurance, et l'œil n'est ni l'un ni l'autre. C'est le recoupement
  // imparfait des trois qui sort les individus qu'on remarque — le brave sans
  // souffle, le poussif qui ne lâche jamais.

  /** Le cœur : de −1 (il se garde) à +1 (il y va). */
  const trempe = () => (R() + R() + R() + R() - 2) / 2;

  // ⚠ LA VIVACITÉ EST UN FACTEUR DE DÉLAI, PAS UNE VITESSE. 0,6 est le VIF,
  // 1,4 le lourd, et la valeur MULTIPLIE le temps de réaction (voir `oeil`) —
  // donc partout où on la compare, le rapport s'écrit à l'envers du nom. C'est
  // le piège le plus silencieux de la bataille : une inversion ne planterait
  // rien, les vifs seraient simplement les moins dangereux du champ et personne
  // ne le verrait sur un plan.
  const vivacite = () => 1 + trempe() * 0.4;   // de 0,6 à 1,4

  // Le fond joue DANS LES DEUX SENS, ce qui est le propre de l'endurance :
  // celui qui en a se vide moins vite ET se refait plus vite.
  const fond = () => 1 + trempe() * 0.4;       // de 0,6 à 1,4

  // QUATRIÈME DÉVIATION — LA SOUPLESSE. À quelle vitesse un homme ramène ce
  // qu'il a dans les mains sur quelqu'un qui n'était pas devant lui. Ce n'est
  // ni le courage, ni le souffle, ni l'œil : c'est le corps, les reins, le pied
  // qui pivote. Elle est donc tirée à part comme les trois autres, et son
  // recoupement imparfait avec elles fait le personnage qu'on remarque — le
  // lourdaud qui voit tout venir et n'arrive jamais à se retourner à temps.
  //
  // Plus serrée que les trois autres (±0,35 au lieu de ±0,40) : la vitesse à
  // laquelle on se tourne varie moins d'un homme à l'autre que le cœur ou le
  // souffle, et c'est l'ARME qui doit rester le gros du facteur.
  const souplesse = () => 1 + trempe() * 0.35; // de 0,65 à 1,35

  return { GRAINE, R, semer, entre, cloche, trempe, vivacite, fond, souplesse };
})();
