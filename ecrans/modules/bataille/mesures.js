// mesures.js — le fichier de variables de la bataille.
//
// DEUXIÈME FEUILLE DÉTACHÉE DE `bataille2d.js`, après `hasard.js`. Elle n'a
// qu'une raison d'être, et c'est une raison de discipline : **rassembler en un
// seul endroit tout ce qui est un NOMBRE plutôt qu'une fonction**, pour qu'on
// puisse les compter, les contester, et les faire diminuer.
//
// ─────────────────────────────────────────────────────────────────────────────
// LA RÈGLE, ET ELLE A ÉTÉ PAYÉE COMPTANT
//
// « Jamais de constantes, toujours des fonctions. » Trois fois dans la même
// journée, une constante a menti :
//
//   `SEUIL_RECUL = 0.5` — « sous la moitié de ses points, on décroche ». Vrai à
//   300 points de vie où la moitié faisait sept coups encaissés. Le jour où les
//   points sont passés à 30, la moitié valait MOINS D'UN COUP : tout homme
//   touché une fois décrochait pour la nuit, et l'on a vu des lignes entières
//   de statues plantées à un mètre de l'ennemi.
//
//   `RIPOSTE = 0.55` — des points de vie retranchés en valeur absolue. Elle a
//   dû être divisée par dix à la main, en même temps que les points de vie.
//
//   Un budget d'effort comparé à un score qui servait aussi à classer. Les deux
//   s'écrivaient en mètres et ne disaient pas la même chose : toute troupe en
//   ordre serré est devenue inattaquable, et l'assaut a traversé la ville sans
//   se battre.
//
// LE TEST AVANT D'ÉCRIRE UN NOMBRE ICI : *si une autre grandeur du modèle
// double, celui-ci doit-il bouger ?* Si oui, ce n'est pas une mesure — c'est
// une fonction qu'on n'a pas encore écrite, et elle n'a rien à faire dans ce
// fichier.
// ─────────────────────────────────────────────────────────────────────────────
"use strict";
(() => {

  const H = (typeof window !== "undefined" && window.BatailleHasard)
    || (typeof require !== "undefined" && require("./hasard.js"));

  // ===========================================================================
  // LES POINTS DE VIE — une COURBE, pas un nombre
  // ===========================================================================
  // TOUS LES HOMMES AVAIENT EXACTEMENT LA MÊME VIE, et c'était le dernier
  // endroit du modèle où deux hommes étaient interchangeables. Le courage, l'œil,
  // l'endurance et la souplesse étaient déjà tirés en cloche ; la carcasse, non.
  //
  // Ce que ça coûtait ne se voit pas sur une moyenne, ça se voit sur les BORDS :
  // sans dispersion, aucun homme ne survit à un coup auquel son voisin succombe,
  // donc il n'y a ni miraculé ni homme de verre — et ce sont eux qu'on remarque
  // sur un champ de bataille. Une ligne d'hommes identiques tombe d'un bloc.
  //
  // ±40 % comme les quatre autres déviations, en cloche (Irwin–Hall, bornée par
  // construction). Un homme de vingt-cinq encaisse en moyenne un peu plus d'un
  // coup ; celui du haut de la courbe en encaisse deux, celui du bas tombe au
  // premier. C'est la même dispersion que la trempe, et c'est voulu : ce sont
  // des variations d'homme, pas des classes de personnages.
  const ECART_PV = 0.4;

  // ⚠ VINGT-CINQ EST UN PROVISOIRE, ET IL FAUT LE DIRE ICI PLUTÔT QUE DE LE
  // DÉCOUVRIR PLUS TARD.
  //
  // Ce nombre ne devrait PAS être un nombre : il est le seul de ce fichier qui
  // échoue au test ci-dessus, et il y échoue franchement. Il est contraint par
  // une autre grandeur du modèle, qui vit ailleurs :
  //
  //     ecrans/modules/survival-stack/1-corps.js  →  `alarmer()`, `M.MONTEE_S`
  //
  // LA CONTRADICTION, MESURÉE. La constante de montée de l'alarme est de trois
  // secondes : c'est le temps qu'un corps met à avoir peur. Or au banc
  // (`scenario-3-contre-2.js`, et la vue `/bataille`), un homme pris par deux
  // frappeurs tombe à 1,5 s, et à un contre un à 3,6 s. **Un homme au contact
  // meurt avant d'avoir peur.** Toute la couche 1 — l'habituation, la
  // sidération, la contagion, l'emprise du corps sur la tête — est calibrée
  // pour un combat que le modèle de dégâts n'autorise pas à exister.
  //
  // CE QUE LA VALEUR JUSTE DEVRAIT ÊTRE, ET ELLE SE DÉRIVE :
  //
  //     coups reçus par seconde  =  frappeurs × TOUCHE / CADENCE
  //     vie voulue en secondes   =  k × MONTEE_S          (k ≈ 3 à 5)
  //     ACTOR_AVERAGE_PV         =  vie voulue × coups/s × dégât typique
  //
  // Avec un frappeur, 45 % au toucher, 0,9 s de cadence et 22 de dégât moyen,
  // il faudrait de l'ordre de cent points pour qu'un duel dure quatre
  // constantes d'alarme. Cent, ce n'est pas vingt-cinq — et c'est précisément
  // la décision qu'on n'a pas encore prise : ou bien la mêlée dure et la
  // psychologie existe, ou bien elle est expéditive et la couche 1 ne sert que
  // hors du contact. **Les deux se défendent ; il faut choisir, pas régler.**
  //
  // On pose donc vingt-cinq — la valeur du jeu tel qu'il est aujourd'hui, à
  // peine sous les trente d'avant — et on laisse la note. Le jour où l'on
  // tranche, c'est ICI que ça se passe, en une ligne, et la formule ci-dessus
  // prend la place du nombre.
  // 14 aout, au soir : TRENTE-CINQ. Un premier pas vers la derivation
  // ci-dessus, decide a la main et assume comme tel — pas la centaine que
  // la formule reclame, mais de quoi voir dans quel sens ca bouge. Un homme
  // moyen encaisse desormais 1,6 coup au lieu de 1,14, et son integrite de
  // depart passe de −0,28 a −0,05 : il ne commence plus la nuit a moitie
  // effraye par sa seule carcasse.
  const ACTOR_AVERAGE_PV = 35;

  /**
   * La vie d'UN homme, tirée à sa naissance et jamais retouchée.
   * @param moyenne  de quoi donner une carcasse différente à un corps d'élite
   *                 ou à des gueux, sans toucher au reste du modèle.
   */
  const pvDUnHomme = (moyenne) => {
    const m = moyenne == null ? ACTOR_AVERAGE_PV : moyenne;
    return H.cloche(m * (1 - ECART_PV), m * (1 + ECART_PV));
  };


  // ===========================================================================
  // L'HOMME MOYEN, ET CE QU'IL A DANS LES MAINS
  // ===========================================================================
  // Ces trois-là ne sont PAS un réglage : c'est l'homme sans arme du tableau —
  // celui qui cogne une porte, celui d'un essai. Le tableau ci-dessous se lit
  // CONTRE eux, et une ligne qui les bat sur toutes les colonnes est une faute.
  const ALLONGE = 1.6;    // épée, hache, pique courte
  const CADENCE = 0.9;    // secondes entre deux coups
  const DEGAT   = [14, 30];

  const ARMES = {
    epee:     { nom: "épée et bouclier", allonge: 1.4, cadence: 0.85,
                degat: [11, 24], garde: 0.78, teinte: "#dcd2c0",
                pivot: 240, secteur: 40 },
    hache:    { nom: "hache d'armes",    allonge: 1.5, cadence: 1.25,
                degat: [19, 40], garde: 1,    teinte: "#c98a5a",
                pivot: 150, secteur: 35 },
    lance:    { nom: "lance",            allonge: 2.8, cadence: 1.15,
                degat: [15, 32], garde: 1,    teinte: "#b9b6a4",
                pivot: 95,  secteur: 20 },
    epieu:    { nom: "épieu",            allonge: 2.2, cadence: 0.90,
                degat: [11, 24], garde: 1,    teinte: "#9c9a86",
                pivot: 130, secteur: 25 },
    coutelas: { nom: "coutelas",         allonge: 0.9, cadence: 0.55,
                degat: [7, 17],  garde: 1,    teinte: "#a89880",
                pivot: 320, secteur: 60 },
  };
  // CE QUE LE TABLEAU DONNE, EN PV PAR SECONDE ET AU TOUCHER MOYEN — c'est la
  // colonne qu'on ne voit pas en le lisant, et c'est elle qu'il faut relire
  // chaque fois qu'on retouche un chiffre au-dessus :
  //
  //     coutelas  9,8   allonge 0,9   il faut entrer sous la pointe
  //     hache    10,6   allonge 1,5   et un coup sur deux tue net
  //     lance     9,2   allonge 2,8   elle touche la première, et c'est tout
  //     épieu     8,8   allonge 2,2   la lance du pauvre, et ça se voit
  //     épée      9,3   allonge 1,4   le plus dur à tuer, jamais le plus rapide
  //
  // Aucune ne mène sur deux colonnes. L'épée a d'abord été écrite à [13,27] et
  // c'était une faute qu'on aurait mise trois cuissons à voir : meilleur dégât,
  // meilleure cadence ET un bouclier — la ligne unique revenue par la fenêtre
  // qu'on venait de fermer.
  const ARME_NUE = { nom: "ce qu'il a trouvé", allonge: ALLONGE,
                     cadence: CADENCE, degat: DEGAT, garde: 1,
                     teinte: "#8f8778", pivot: 200, secteur: 45 };

  // ===========================================================================
  // OÙ EST SON FER, ET QUI IL PEUT ATTEINDRE
  // ===========================================================================
  // ELLES SONT ICI PARCE QU'ELLES SONT PARTAGÉES, et pour aucune autre raison.
  // `bataille2d.js` s'en sert pour la bataille ; la page de débug `/bataille`
  // s'en sert pour le banc de la couche 1. La première version de cette page
  // avait recopié le tableau des armes et réécrit son propre test de portée —
  // un disque de 2,2 m, sans orientation, deux fois trop grand et sans secteur.
  // C'est exactement ce que l'en-tête de `scripts/monde/sac.js` interdit :
  // « deux implémentations d'une même bataille, ce sont deux batailles, et l'on
  // passe ses soirées à chercher laquelle ment ».

  /** Le cosinus entre son cap tenu et la direction de l'autre. +1 pile en face,
   *  0 de flanc, −1 dans le dos. */
  function enFace(h, o) {
    if (!h.fx && !h.fy) return 1;
    const dx = o.x - h.x, dy = o.y - h.y, n = Math.hypot(dx, dy);
    if (n < .01) return 1;
    return (h.fx * dx + h.fy * dy) / n;
  }

  const RAD = Math.PI / 180;

  /** LES DEUX CONDITIONS, ET IL FAUT LES DEUX : assez près, et dans le secteur.
   *  Un homme à un mètre sur le flanc est hors d'atteinte tant qu'on ne s'est
   *  pas tourné — c'est ce qui donne un prix au fait d'être pris de côté, et
   *  c'est ce qu'un disque ne peut pas dire. */
  function peutFrapper(h, o, arme) {
    const a = arme || h.arme || ARME_NUE;
    const d = Math.hypot(o.x - h.x, o.y - h.y);
    return d <= a.allonge && enFace(h, o) >= Math.cos((a.secteur || 45) * RAD);
  }

  // ===========================================================================
  const API = { ACTOR_AVERAGE_PV, ECART_PV, pvDUnHomme,
                ALLONGE, CADENCE, DEGAT, ARMES, ARME_NUE, enFace, peutFrapper, RAD };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.BatailleMesures = API;
})();
