// bataille2d.js — trois cents hommes devant une porte, et ce qui s'ensuit.
//
// CE QUE C'EST, ET CE QUE CE N'EST PAS. C'est une LUNETTE, exactement comme
// `foule2d` : un bac à sable posé sur le plan, qui ne touche à rien. Aucune
// écriture dans `etat/`, aucune minute de partie consommée, aucun fait de jeu.
// On peut la lancer, la voir tourner, la remettre à zéro : la partie n'en sait
// rien. Le jour où une bataille comptera vraiment, ce sera le MJ qui l'écrira,
// pas ce module.
//
// LES PV SONT EN MÉMOIRE ET N'EN SORTENT JAMAIS. C'est une contrainte assumée
// et pas une paresse : une simulation qui persiste est une simulation qu'il
// faut réconcilier, migrer, et déboguer à travers un fichier. Celle-ci se
// rejoue d'un bouton.
//
// L'ÉCHELLE EST 1:1, EN NOMBRE ET EN TAILLE. Trois cents corps, pas trois cents
// jetons valant dix hommes ; un homme fait 0,55 m d'épaules, marche à 1,3 m/s,
// frappe à 1,6 m. C'est ce qui rend la chose intéressante, parce que la
// géométrie décide alors toute seule : une porte de six mètres ne laisse
// passer que sept hommes de front, et les deux cent quatre-vingt-treize autres
// attendent dehors. Personne n'a écrit ce bouchon — il tombe des mètres.
//
// QUATRE MACHINES À ÉTATS, ET RIEN D'AUTRE.
//
//   le SOLDAT      colonne → forme → assaut → mêlée → (déroute) → blessé → mort
//   le VERROU      fermé → cède → ouvert            (la porte est un objectif,
//                                                    pas un décor)
//   la SURVIE      une morale par homme, qui tombe des morts qu'il VOIT tomber
//                  autour de lui — c'est elle qui décide de la déroute
//   le BOURGEOIS   saisi → fuite → rentre → terre → reprend sa journée
//                  (et le guet, lui, va DANS L'AUTRE SENS)
//
// LES ANNALES — CE QU'UN COMPORTEMENT DOIT LAISSER DERRIÈRE LUI. Une bataille
// qu'on regarde ne sert qu'à celui qui la regarde. Ce module tient donc, en
// plus des corps, une liste de FAITS datés, situés et attribués : la porte qui
// cède, un chef qui tombe, une escouade qui rompt, un blessé dans une rue, la
// peur qui gagne un quartier. C'est la seule sortie qu'un MJ puisse lire, et
// c'est elle qui rend la bataille traversable — on ne raconte pas des points
// qui bougent, on raconte ce qui est arrivé à qui, où, et à quelle heure.
//
// La règle qui les tient : UN COMPORTEMENT QUI N'ÉMET RIEN N'EXISTE PAS. Tout
// ce qu'on ajoutera ici — la chaîne de commandement, le roi, les pillards —
// doit produire sa ligne, faute de quoi on aura enrichi une simulation que
// personne ne peut lire.
//
// Elles sont BORNÉES PAR CONSTRUCTION, et il le faut : quinze chefs, quinze
// escouades, une ligne par quartier gagné par la peur. Le seul poste qui suive
// l'effectif est le blessé — et c'est voulu, parce qu'un blessé est justement
// la scène qu'on est venu chercher.
//
// LA DISRUPTION EST LE VRAI SUJET. `journee.js` est une fonction PURE : elle
// dit où est n'importe qui à n'importe quelle minute, sans état, et c'est ce
// qui permet à quatre cent mille personnes de vivre pour rien. On ne va donc
// PAS la salir. On se glisse par-dessus : `derange(cel, k, P)` est un droit de
// veto que `foule2d` demande pour chaque habitant qu'il s'apprête à dessiner.
// Tant que personne ne panique, il rend faux et ne coûte qu'un test ; ceux qui
// paniquent sortent de leur journée écrite et n'y rentrent qu'une fois calmés.
// La ville reste pure, la peur est une couche.
"use strict";
window.Bataille2d = (() => {

  // ---- les mesures, toutes en mètres et en secondes -------------------------
  // Rien ici n'est un réglage de jeu : ce sont des mesures d'homme. Quand un
  // chiffre paraît faux, c'est qu'il l'est — on le corrige contre la réalité,
  // pas contre l'envie que la bataille dure plus longtemps.
  const EPAULE      = 0.55;   // largeur d'un homme en armes
  // Du milieu du corps au poing qui tient l'arme. Purement d'affichage : rien
  // dans la mécanique ne le lit, ni l'allonge, ni le secteur, ni le coup.
  const POING       = 0.2;    // le fer sort de la main, pas du nombril
  const MARCHE      = 1.3;    // en colonne, sans se presser
  const CHARGE      = 3.0;    // les trente derniers mètres
  const FUITE       = 3.6;    // on court mieux quand on a peur
  // ---- ET AUCUNE DE CES ALLURES NE SE PREND D'UN COUP -----------------------
  // Les trois du dessus sont des vitesses de CROISIÈRE, et rien ne disait
  // comment on y arrivait : un homme à l'arrêt était à trois mètres par seconde
  // à l'image suivante, ce qui est un départ de sprinteur en armure. Ça se
  // voyait sur le plan sans qu'on sache le nommer — des lignes qui claquent
  // d'une allure à l'autre, une charge sans élan, une halte sans erre.
  //
  // 1,4 m/s² pour lancer quatre-vingts kilos d'homme et trente de fer : la
  // charge (3,0) se prend en un peu plus de deux secondes et sur trois mètres,
  // ce qui est le bon ordre pour des gens chargés. Le freinage est deux fois
  // plus vif, parce que planter ses talons ne demande aucun élan — c'est
  // l'asymétrie du corps, pas un réglage de confort, et c'est elle qui fait
  // qu'une charge se prépare tandis qu'une halte est immédiate.
  const ACCEL       = 1.4;    // m/s², avant la souplesse et le souffle
  const FREIN_PIED  = 3.0;    // m/s² — on s'arrête bien mieux qu'on ne part
  // L'homme moyen : ce que porte quiconque n'a pas d'arme du tableau. Il vit
  // dans `bataille/mesures.js` avec le tableau lui-même — les deux se lisent
  // l'un contre l'autre, donc ils ne se séparent pas.
  const { ALLONGE, CADENCE, DEGAT } = window.BatailleMesures;
  const Commandement = window.BatailleCommandement;
  // UNE BATAILLE NE CHOISIT PAS SES MORCEAUX D'HOMME. Les bancs, la page et
  // le jeu chargent la même pile ; on la vérifie ici, au seul endroit qu'ils
  // doivent tous franchir. Une épreuve ne peut donc plus paraître fonctionner
  // après avoir omis, volontairement ou non, la peur, la réflexion, l'envie,
  // l'interprétation ou leur arbitre.
  const COMPORTEMENTS_REQUIS = Object.freeze([
    ["Corps", window.Corps], ["BatailleCorps", window.BatailleCorps],
    ["Reflexion", window.Reflexion], ["BatailleReflexion", window.BatailleReflexion],
    ["Interpretation", window.Interpretation], ["Envie", window.Envie],
    ["QuiConduit", window.QuiConduit], ["BatailleCommandement", Commandement],
  ]);
  const comportementsAbsents = COMPORTEMENTS_REQUIS.filter((x) => !x[1]).map((x) => x[0]);
  if (comportementsAbsents.length)
    throw new Error("pile de comportements incomplète avant bataille2d.js : " +
                    comportementsAbsents.join(", "));

  // Une doctrine est un ordre appris, pas un comportement de remplacement.
  // Elle ne retire aucune couche et n'agit que lorsque l'arbitre laisse les
  // jambes à l'ordre. Les chiffres sont des distances humaines : 8–17 m
  // suffisent à faire tomber la densité d'une ligne sans transformer cent
  // hommes en points équidistants sur une grille.
  const DOCTRINES = Object.freeze({
    "anti-dragon-ouvert": Object.freeze({
      id:"anti-dragon-ouvert", nom:"ordre ouvert anti-dragon", danger:"dragon",
      rayonMin:8, rayonMax:17, vitesse:1.15, tenue:5,
      // L'ordre ne donne aucun moyen de blesser le dragon. Il réduit seulement
      // le sentiment collectif d'être enfermé dans une cible compacte ; la
      // peur individuelle et la rupture locale restent entièrement actives.
      ouvertureCollective:.52,
    }),
  });

  // UN COUP PEUT SUFFIRE, ET C'EST LE RETOUR À LA MESURE.
  //
  // Ce fichier a porté pendant un temps un facteur `ENDURANCE = 3` qui triplait
  // la vie d'un homme, avec pour seule justification qu'on voulait « pouvoir
  // regarder » la mêlée. C'était le seul chiffre du fichier qui ne mesurait
  // rien, et il payait ce qu'il achetait : trois cents points de vie contre
  // quatorze à trente par coup, c'est vingt coups portés pour abattre un homme
  // — une demi-minute de deux hommes qui se tapent dessus sans conclure. Aucune
  // rencontre à l'arme blanche n'a jamais ressemblé à ça.
  //
  // TRENTE. Un coup pleine force (30) tue net ; un coup ordinaire (22) laisse
  // debout un homme qui ne tiendra pas le suivant ; et la parade dégradée
  // (`PARADE`, jusqu'à +60 % sur qui est débordé) fait qu'être pris à trois,
  // c'est mourir au premier fer qui touche. Quatre secondes de contact en
  // moyenne, pas trente.
  //
  // CE QUE ÇA CHANGE AILLEURS, ET QU'IL FAUT SAVOIR :
  //   — `SEUIL_RECUL` (moitié des pv) se franchit désormais AU PREMIER COUP
  //     REÇU. C'est juste : un homme entamé décroche, il ne fait pas la moitié
  //     d'un duel de tournoi. Mais ça veut dire qu'un touché sort du rang.
  //   — `SANG` reprend sa valeur nue : la part de vie passée à demi vidé n'a
  //     pas changé, seule sa durée absolue s'est effondrée.
  //   — `RIPOSTE` a été divisée d'autant, sinon le seuil d'une porte tuait ses
  //     assaillants en deux secondes au lieu de vingt.
  //   — La porte elle-même (`VERROU_PV`, `HACHE`) ne bouge pas : le bois n'a
  //     jamais eu d'endurance, et il tombe à la même heure qu'avant.
  // LA VIE N'EST PLUS UN NOMBRE, C'EST UNE COURBE — voir `bataille/mesures.js`,
  // qui la tire en cloche autour de `ACTOR_AVERAGE_PV` et porte la note sur la
  // contradiction entre la létalité du contact et le temps qu'un corps met à
  // avoir peur. Ce qui reste ici est la MOYENNE, et elle ne sert qu'à deux
  // choses : documenter l'échelle, et donner un défaut aux hommes engendrés
  // avant que leur vie soit tirée.
  //
  // ⚠ TOUT SEUIL QUI SE COMPARE À UNE VIE DOIT LIRE `h.pvMax`, JAMAIS CECI.
  // C'est exactement la faute de `SEUIL_RECUL` : un seuil qui pointe sur une
  // moyenne cesse d'être vrai pour l'homme du haut et pour celui du bas de la
  // courbe — et il ne le dit pas.
  const PV = window.BatailleMesures.ACTOR_AVERAGE_PV;
  const TOUCHE      = 0.45;   // un coup sur deux porte, à peu près

  // ===========================================================================
  // LES ARMES — trois mesures, et elles se contredisent
  // ===========================================================================
  // Jusqu'ici tout le monde portait la même chose : 1,6 m d'allonge, un coup
  // toutes les 0,9 s, quatorze à trente. Un seul homme existait donc, tiré à
  // deux mille exemplaires, et la seule variation du fichier était sa vivacité.
  //
  // CE QUI FAIT UNE ARME, C'EST QU'ELLE ACHÈTE UNE CHOSE AVEC UNE AUTRE. Aucune
  // des trois mesures n'est un « niveau » : la lance touche la première et
  // frappe lentement, la hache ouvre un homme d'un coup et laisse son porteur
  // découvert entre deux, le coutelas ne vaut rien et frappe deux fois pendant
  // qu'une hache se relève. Si l'une des lignes était meilleure que les autres
  // sur les trois colonnes, il n'y aurait toujours qu'une arme dans ce fichier.
  //
  //   allonge   à quelle distance on engage — et c'est la mesure qui décide le
  //             plus, parce qu'elle ne dit pas seulement qui touche : elle dit
  //             QUI TOUCHE LE PREMIER. Un homme au coutelas doit traverser un
  //             mètre et demi sous la pointe pour avoir le droit de frapper.
  //   cadence   secondes entre deux coups, avant le souffle (`vigueur`)
  //   degat     par coup porté, avant la parade dégradée (`PARADE`)
  //   pivot     DEGRÉS PAR SECONDE, en régime établi. Le poids de la chose, et
  //             c'est la mesure qui manquait à la première passe : on n'oriente
  //             pas trois mètres de frêne à quarante-cinq degrés en une image.
  //             Ce n'est pas une vitesse imposée mais un PLAFOND : le fer met
  //             à s'y mettre le temps qu'il met à s'arrêter (voir `tourner`).
  //   secteur   de combien de degrés on peut être à côté et frapper quand même.
  //             La pointe veut être dessus ; un coutelas se donne de biais.
  //   garde     ce que le porteur ENCAISSE, en facteur. Le bouclier vit ici et
  //             nulle part ailleurs : il n'a pas d'entrée à lui, parce qu'un
  //             bouclier n'est pas un objet de plus, c'est la main gauche de
  //             celui qui tient une épée d'une seule.
  //
  // ON N'A PAS TOUCHÉ AUX CONSTANTES DU DESSUS : `ALLONGE`, `CADENCE`, `DEGAT`
  // restent l'homme moyen, et c'est ce que porte quiconque n'a pas d'arme —
  // la hache sur la porte, un homme d'un essai. Le tableau se lit CONTRE ces
  // trois chiffres-là, et une ligne qui les bat partout est une faute.
  // Le tableau des armes, `ARME_NUE` et le test de portée vivent désormais dans
  // `bataille/mesures.js` — parce que la page de débug `/bataille` en a besoin
  // AUSSI, et qu'une seconde copie aurait fait deux batailles au lieu d'une.
  // C'est très exactement ce que l'en-tête de `scripts/monde/sac.js` interdit.
  const { ARMES, ARME_NUE, enFace, peutFrapper } = window.BatailleMesures;

  // ---- LE FER A UNE INERTIE -------------------------------------------------
  // Le cap voulu (`h.cx, h.cy`) et le cap tenu (`h.fx, h.fy`) sont deux choses,
  // et tout est là. Le premier se pose librement — par la marche, par la cible
  // qu'on vient de choisir —, le second ne fait que le RATTRAPER, à la vitesse
  // que le poids de l'arme autorise. Un homme qui se retourne n'est donc plus
  // un homme qui s'est retourné : c'est un homme qui est en train de le faire,
  // et pendant ce temps il ne frappe personne.
  //
  // CE QUE ÇA AJOUTE, ET C'EST LE MEILLEUR DE LA PASSE : le débordé était puni
  // deux fois par des coefficients (`PARADE`, `PRESSE`) — deux façons d'écrire
  // « il encaisse plus ». Il l'est maintenant une troisième fois par une
  // MÉCANIQUE, et celle-là n'a pas de chiffre : celui qu'on prend de flanc doit
  // tourner sa lance de quatre-vingt-dix degrés, soit une seconde pleine
  // pendant laquelle son fer regarde ailleurs. C'est la première fois de ce
  // fichier qu'être pris à revers veut dire quelque chose de géométrique.
  //
  // Et le souffle y passe aussi : un bras mort tourne moins vite. C'est la
  // troisième chose que `vigueur` commande, après la cadence et le pas.
  // ---- ET LA ROTATION A UNE COURBE, PAS UN PAS ------------------------------
  // Une vitesse angulaire constante, c'est encore un objet sans masse : il part
  // à pleine vitesse au premier centième de seconde et s'arrête net au dernier.
  // On tient donc la VITESSE (`h.w`, en radians par seconde) comme une grandeur
  // à part, et l'arme n'impose plus une vitesse mais une ACCÉLÉRATION : le fer
  // met à se mettre en mouvement le même temps qu'il met à s'arrêter.
  //
  // La cible de vitesse est `√(2·a·|écart|)`, plafonnée au régime de l'arme —
  // c'est la loi de freinage, celle qui dit « à cet écart-là, voilà la vitesse
  // maximale depuis laquelle je peux encore m'arrêter pile ». Elle donne d'un
  // coup les trois moitiés du geste : ça monte, ça tient, ça redescend, et ça
  // n'oublie jamais de s'arrêter — pas d'oscillation autour du cap, pas de
  // dépassement à corriger, aucun réglage d'amortissement à trouver.
  //
  // TROIS FACTEURS SUR LE RÉGIME, ET AUCUN N'EST DE TROP :
  //   l'ARME     le gros du terme. Trois mètres de frêne contre un couteau.
  //   la SOUPLESSE  ce que l'homme vaut, tiré en cloche une fois pour toutes.
  //   le SOUFFLE (`vigueur`) un bras mort ne ramène rien. C'est la troisième
  //     chose que le souffle commande, après la cadence et le pas — et celle-ci
  //     décide qui se fait prendre de dos à la vingtième minute.
  const RAD = Math.PI / 180;
  const MONTEE = 3.5;   // en combien de fois son régime une arme se lance
  // LES ÉTATS OÙ LE FER APPARTIENT À L'ENNEMI ET NON AUX JAMBES. Dans ceux-là,
  // `versLe` ne touche plus au cap : c'est `frapper` — ou la branche du repli —
  // qui décide où pointe la chose. Voir le pavé de `versLe`.
  const AU_CONTACT = { melee: 1, assaut: 1, tient: 1 };

  /** Le cosinus de l'écart entre où il regarde et où est sa cible. */

  // QUI PORTE QUOI, ET ÇA NE SE TIRE PAS À PLAT. La garnison est une troupe
  // payée : elle a des lances, et une lance derrière un seuil est la meilleure
  // chose qu'on puisse avoir. L'assaut est plus mélangé — c'est un ost levé,
  // pas une garde —, et l'on y trouve des gens venus avec ce qu'ils avaient.
  // Les chefs portent l'épée parce qu'un homme qui commande a besoin de sa
  // voix et d'une main libre, pas parce qu'elle serait meilleure.
  const SACS = {
    garde:  [["lance", .30], ["epee", .40], ["hache", .18], ["epieu", .12]],
    assaut: [["epee", .28], ["hache", .24], ["lance", .18], ["epieu", .18],
             ["coutelas", .12]],
  };

  function armeDe(camp, opts) {
    // Une épreuve ou un ordre de bataille peut désormais donner un métier
    // réel à l'homme. Le sac aléatoire reste le défaut historique, jamais une
    // autorité qui écrase ce que le roster sait explicitement.
    if (opts && opts.arme && ARMES[opts.arme]) return ARMES[opts.arme];
    if (opts && opts.metier && window.BatailleRoster) {
      const m = window.BatailleRoster.METIERS[opts.metier];
      if (m && ARMES[m.arme]) return ARMES[m.arme];
    }
    // Le roi, sa garde, les têtes et tout ce qui commande : l'épée.
    if (opts && (opts.chef || opts.capitaine || opts.tete || opts.roi ||
                 opts.hors)) return ARMES.epee;
    const sac = SACS[camp];
    if (!sac) return ARME_NUE;
    let t = R();
    for (const [id, p] of sac) { t -= p; if (t <= 0) return ARMES[id]; }
    return ARMES[sac[0][0]];
  }
  // LA PORTE ÉTAIT UN MINUTEUR, ET C'EST TOUT LE DÉFAUT. 3 000 pv divisés par
  // sept haches à onze font TRENTE-NEUF SECONDES, et rien au monde ne pouvait
  // changer ces trente-neuf secondes : la garde est postée huit mètres EN
  // DEDANS, il n'y a ni tir, ni jet, ni hourd, donc pendant toute la phase de
  // la porte le défenseur n'a strictement aucune décision à prendre. Pas de
  // choix, pas de tactique — juste une horloge qu'on regarde descendre.
  //
  // Neuf mille : deux minutes de sept haches. Le chiffre n'est pas choisi pour
  // « faire durer », il est choisi pour qu'une porte coûte assez cher qu'on ne
  // puisse pas en payer quatre. C'est ce qui force à CONCENTRER, et concentrer
  // est la première décision d'un assaut.
  const VERROU_PV   = 9000;

  // CE QU'IL RESTE DE BOIS À CHAQUE PORTE, et ce n'est pas un réglage de
  // difficulté : c'est l'état d'un ouvrage qu'on a laissé vieillir. La Gadoue
  // est la porte du port — celle par où passent les charrettes du chantier de
  // la Vase, le sel, et tout ce qui entre en ville par l'eau. Elle travaille
  // tous les jours, personne ne l'a referrée depuis des années, et le Guet le
  // sait : c'est écrit dans les demandes de réfection que le sergent Waltyr
  // Poix envoie au Donjon et que personne ne lit.
  //
  // NEUF CENTS POINTS AU LIEU DE NEUF MILLE. Deux minutes de sept haches
  // deviennent DOUZE SECONDES. Ce n'est pas un détail d'ambiance : c'est
  // l'exercice entier qui se déplace, parce que la première porte tombe avant
  // que quiconque ait eu le temps d'y penser — la mesure que le rapport
  // portera au matin sera prise sur une porte qui n'existait déjà plus.
  const USURE = { "La porte de la Gadoue": 0.10 };

  // ⚠ ESSAI — REPASSÉE À `false`, ET VOICI CE QU'ELLE COÛTAIT. La porte du four
  // s'ouvrait au premier instant, pour sauter les deux minutes de hache et
  // aller voir la mêlée. Le raccourci n'était pas neutre : il ne retirait pas
  // deux minutes, il retirait la doctrine.
  //
  // La branche « verrou ouvert » est au DEUXIÈME rang de la cascade de
  // `deciderLesTetes`, juste après le repli. Elle avale donc tout ce qui est
  // en dessous, et pour toutes les ailes du corps à la fois : la consigne
  // d'avant-nuit de Petit Wend (« à deux cents pas de Cole »), l'appui de la
  // deuxième aile, le déclencheur de la troisième, et le `sans piller`. Les
  // deux corps de la porte principale recevaient un `avancer` nu, identique
  // d'un bout de la nuit à l'autre — donc jamais réémis, donc une tête muette
  // pendant quatre minutes d'affilée.
  //
  // Et plus bas, deux fonctions sortent sur `etat === "ouvert"` : personne ne
  // désigne de front à cette porte-là (`frontDUnVerrou`), et la garnison ne se
  // resserre jamais sur la brèche (`verrouQuiCede`). La mêlée sept contre sept
  // dans le seuil — le morceau qu'on était allé chercher — n'avait pas lieu à
  // la porte qu'on regardait.
  const PORTE_OUVERTE_ESSAI = false;
  const HACHE       = 11;     // pv de porte par homme au contact et par seconde
  // Les quatre mesures du commandement vivent dans `bataille/mesures.js` avec
  // leur source : ce sont des faits sur des yeux et sur une largeur de porte,
  // pas des réglages, et elles ne se touchent pas pour obtenir un comportement.
  const { FRONT_PORTE, VUE_BANNIERE, DELAI_BANN, VUE_DECLENCHEUR } =
    window.BatailleMesures;

  // CE QUE COÛTE DE TENIR UNE HACHE SUR UN SEUIL DÉFENDU. La riposte du poste :
  // les gardes du seuil frappent par-dessus et à travers ce qui vient au bois —
  // c'est la seule chose qui rende la phase de la porte JOUABLE des deux côtés.
  //
  // Elle est PROPORTIONNELLE À LA GARNISON DEBOUT de cette porte-là, et c'est
  // le point : à pleine garnison le seuil est intenable et l'assaut y laisse
  // ses hommes ; quand le poste a fondu, les haches travaillent tranquilles.
  // Le défenseur a donc quelque chose à préserver, et l'assaillant quelque
  // chose à faire tomber d'abord. Deux décisions là où il n'y en avait aucune.
  //
  // 0,055 pv par garde debout et par seconde : à deux cents gardes, les sept du
  // front encaissent onze par seconde à se partager — un homme au seuil tient
  // une vingtaine de secondes, il faut donc en relever trois ou quatre pour
  // ouvrir. À vingt gardes il n'en coûte plus rien.
  //
  // ELLE SUIT LES POINTS DE VIE, ET C'EST LA SEULE CHOSE À NE PAS OUBLIER SI
  // ON Y RETOUCHE. Ce chiffre est le seul du fichier qui retranche des pv en
  // valeur absolue et non par coup porté : quand `PV` a été divisé par dix, la
  // riposte a dû l'être aussi, faute de quoi le seuil d'une porte à pleine
  // garnison tuait ses assaillants en deux secondes et la phase de la porte
  // redevenait injouable — dans l'autre sens.
  const RIPOSTE    = 0.055;

  // TOMBER N'EST PAS MOURIR, et c'était le plus gros gâchis du module : un
  // homme à zéro passait `mort`, c'est-à-dire qu'il sortait du monde. Or celui
  // qui tombe et respire encore est le personnage le plus utile de toute la
  // bataille — il ne bouge plus, il est devant une porte qu'on peut nommer, il
  // parle, et il sait des choses : quel ordre il avait reçu, qui était son
  // chef, où allait son aile. On peut le secourir, le dépouiller, l'interroger.
  // Deux hommes sur cinq, donc, et une plaie qui met du temps à décider.
  const PART_BLESSE = 0.38;
  const SAIGNE      = [40, 260];  // secondes avant que la plaie tranche
  const PART_MEURT  = 0.45;       // ce qu'elle décide, quand elle tranche

  // La morale ne se règle pas non plus : elle dit qu'un homme rompt quand ceux
  // qu'il touche du coude tombent, pas quand un compteur global baisse.
  const VUE_MORT    = 18;     // on voit tomber jusque-là
  // ÊTRE À DEMI SAIGNÉ COÛTE PAR SECONDE, ET IL FAUT LIRE CE CHIFFRE AVEC `PV`.
  // Cette usure s'applique tant qu'un homme est sous la moitié de ses points.
  // Ce qui compte n'est pas le nombre de secondes qu'il y passe, c'est la PART
  // de sa vie de combattant — et depuis que `PV` vaut trente, cette part se
  // compte en une ou deux secondes au lieu de treize. La morale ne tombe donc
  // presque plus des blessures : elle tombe des MORTS QU'ON VOIT (`CHOC`), ce
  // qui est la bonne façon de la faire tomber. Un homme entamé n'a plus le
  // temps d'avoir peur de sa plaie ; il tombe, et ce sont ses voisins qui la
  // paient.
  //
  // Le facteur `ENDURANCE` qui divisait ce chiffre a été retiré avec les trois
  // cents points de vie — voir le pavé de `PV` en tête de fichier.

  // ROMPT — C'EST LUI QUI FAIT DURER UNE BATAILLE, ET PAS LES POINTS DE VIE.
  //
  // La mesure, sur quatre cuissons de 400 hommes à la Gadoue, 900 s :
  //
  //     endurance 1, ROMPT .30    410 s de mêlée   96 morts   131 fuyards
  //     endurance 3, ROMPT .30    397 s            75 morts   112 fuyards
  //     endurance 3, ROMPT .15    802 s            90 morts   102 fuyards
  //
  // Un homme mort ne fait pas durer une mêlée — c'est un homme qui RESTE EN
  // LIGNE qui la fait durer. Tripler les points de vie n'allonge donc rien du
  // tout : ça rend la nuit moins meurtrière, et c'est un autre sujet.
  //
  // CE QUE ÇA COÛTE, ET IL FAUT LE SAVOIR. Descendu à .15, un homme se bat
  // jusqu'à une morale que peu de gens ont eue. Les escouades rompent toujours
  // — six sur six, comme avant — mais bien plus tard, et l'on meurt davantage
  // parce qu'on reste. C'est le prix d'une bataille qu'on peut regarder : plus
  // de fer, moins de fuite. Remettre .30 rend la nuit plus vraisemblable et
  // deux fois plus courte, et c'est cette ligne-ci qu'on retouche.
  // `ROMPT` déposé : ce qui fait durer une bataille est maintenant la montée
  // de l'alarme et l'emprise du corps, pas un seuil sur une jauge.

  // --- le commandement -------------------------------------------------------
  // L'ORDRE DESCEND, ET RIEN NE REMONTE. C'est la règle de tout le reste du
  // jeu — la musique d'Ostor traverse un plancher dans un seul sens — et elle
  // vaut ici en fer. La tête ordonne à l'aveugle : elle ne saura jamais si son
  // ordre est arrivé, ni ce qu'il a déclenché.
  //
  // DEUX CANAUX, ET ILS NE VALENT PAS LA MÊME CHOSE.
  //
  //   la BANNIÈRE   on la voit de loin, elle arrive vite, elle ne dit qu'un
  //                 mot — et elle tombe avec celui qui la porte
  //   le COUREUR    il porte ce qu'on veut, il met le temps de courir, et il
  //                 peut ne jamais arriver
  //
  // Le second n'existe que parce que le premier peut manquer, et c'est là que
  // se joue le drame : une aile sans bannière est une aile qu'on ne commande
  // plus qu'à la vitesse d'un homme qui court dans une presse.
  const PAR_ESC      = 20;    // hommes par escouade — l'unité qui pense
  const ESC_PAR_AILE = 5;     // escouades par aile — l'unité qu'on commande
  // `VUE_BANNIERE` et `DELAI_BANN` sont dans `bataille/mesures.js`, avec
  // `VUE_DECLENCHEUR` et `FRONT_PORTE` — voir la destructuration plus haut.
  const COURSE       = 3.2;   // un homme qui porte un ordre ne flâne pas
  const DELIBERE     = [6, 14]; // ce que la tête met à changer d'avis
  const RELEVE       = 25;    // le temps qu'on met à relever une bannière
  // `CHOC_BANN` → le stimulus `signeTombe` ; `TIENT_BANN` → `M.APAISE_BANN`.
  const RALLIE_M     = 15;    // jusqu'où un chef rattrape un homme qui part
  // Le seuil de RETOUR au combat, plus haut que celui de rupture (0,30). C'est
  // la même hystérésis que la peur des habitants, et pour la même raison : sans
  // elle, un homme rallié rompt au pas suivant et l'armée clignote.
  // `RALLIE_SEUIL` déposé : voir `rallier`, qui lit désormais le corps.
  // Être « au donjon », c'est être dans sa cour — pas dans la même ville. Le
  // rayon est celui de l'anneau des quatre-vingts, plus la portée d'une arme :
  // au-delà, on marche encore vers lui.
  const AU_DONJON = 45;

  // ===========================================================================
  // LA GRAMMAIRE DES ORDRES — un ordre est une PHRASE, pas un mot
  // ===========================================================================
  // Le vocabulaire est resté court exprès, et il le reste : cinq verbes. Ce
  // qui enfle n'est pas la liste — ce sont les COMPLÉMENTS, et chacun d'eux
  // est une chose que la bannière ne sait pas porter, qu'un coureur peut
  // perdre en route, et qu'un chef doit remplacer de sa tête quand elle
  // n'arrive pas. C'est la réponse à l'objection qu'on se faisait plus haut :
  // un vocabulaire qui enfle perd ses conséquences, une phrase qui s'abîme en
  // gagne.
  //
  //   verbe        avancer · tenir · repli · suivre · appuyer
  //   objet        sur qui — une aile, un corps
  //   marge        « à deux cents pas »
  //   declencheur  « quand la porte cède » — l'ordre ATTEND, et il attend tout
  //                seul : rien n'a à lui parvenir le moment venu
  //   interdit     « sans piller »
  //   intention    POURQUOI — la seule clef qui serve quand tout le reste tombe
  //
  // UNE PHRASE PERD SES SUBORDONNÉES AVANT SON VERBE. C'est toute la règle de
  // la dégradation, et elle est écrite dans cet ordre-là : ce qui s'oublie en
  // premier est ce qui RESTREINT, ce qui survit toujours est ce qu'on FAIT.
  // Un homme essoufflé qui a couru cent cinquante mètres dans une presse rend
  // « suivre Vantre » d'un ordre qui disait « suivre Vantre à deux cents pas
  // sans t'engager » — et l'aile s'engagera, parce que personne ne lui a dit
  // de ne pas le faire.
  const CLAUSES = ["interdit", "declencheur", "marge", "objet"];

  // L'ÉTAT DE LA SIMULATION — un objet nommé, et non plus soixante-cinq
  // variables libres éparpillées sur onze mille lignes.
  //
  // POURQUOI. Tant que l'état vit en variables libres, RIEN NE PEUT SORTIR
  // DE CE FICHIER : un module extrait ne peut pas recevoir ce qu'il doit
  // lire, puisqu'il n'y a rien à lui passer. C'est le verrou du refactor,
  // et c'est la seule raison de ce changement — il ne modifie aucun
  // comportement, et l'étalon du moteur doit rendre la même bataille.
  //
  // Ce que l'objet contient, ce que chaque champ veut dire et qui a le
  // droit de l'écrire : `bataille/moteur/etat.js`.
  const S = window.BatailleEtatSim.creer();
  const ordreDe = (verbe, o) => Object.assign({ n: ++S._ordreN, verbe }, o || {});
  const memeOrdre = (a, b) => !!a && !!b && a.n === b.n;
  const copie = (o) => Object.assign({}, o);
  const aClause = (o) => CLAUSES.some((c) => o[c] !== undefined && o[c] !== null);
  const interdit = (o, quoi) => !!(o && o.interdit && o.interdit.includes(quoi));

  // LA BANNIÈRE NE DIT PAS UNE PHRASE : ELLE LÈVE UN SIGNAL CONVENU D'AVANCE.
  // Trois codes, arrêtés avant la nuit, et rien d'autre ne passe par elle.
  // Conséquence, et c'est le cœur : dès que la tête veut quelque chose de
  // PRÉCIS, la bannière ne lui sert plus à rien et il faut un homme. La
  // précision se paie en portage — et le portage peut tomber.
  // Ce que fait un homme dont l'escouade n'existe pas : il marche. C'est le
  // défaut d'avant, écrit une fois au lieu d'être supposé partout.
  const ORDRE_NU = { n: 0, verbe: "avancer" };

  const CODE_BANNIERE = ["avancer", "tenir", "repli"];
  const parBanniere = (o) => CODE_BANNIERE.includes(o.verbe) && !aClause(o);

  // Ce qu'un coureur endure entre deux oublis : des mètres, et double quand il
  // traverse du monde.
  //
  // MESURÉ À ZÉRO, PUIS CORRIGÉ. À quatre-vingts mètres, la dégradation ne
  // s'est produite AUCUNE FOIS sur une nuit entière à pleine échelle : un
  // coureur ne traverse pas la ville, il va du capitaine à une escouade de sa
  // PROPRE aile — trente à soixante mètres, jamais plus. Le mécanisme existait
  // dans le fichier et pas dans le monde, ce qui est la définition d'un
  // comportement qui n'émet rien. Trente-cinq mètres : une phrase complexe
  // arrive entière quand l'aile est serrée, et amputée dès qu'elle s'étire ou
  // qu'il faut jouer des coudes — ce qui est exactement le partage qu'on veut.
  const EPREUVE_M = 35;

  // `VUE_DECLENCHEUR` — dans `bataille/mesures.js`.

  // COMBIEN DE TEMPS UN CHEF ATTEND AVANT DE S'INVENTER UN ORDRE. Ce n'est pas
  // un quatrième réglage d'humeur : c'est la MÊME humeur, lue pour ce qu'elle
  // dit du silence. Le ferme tient longtemps sans nouvelles parce que tenir est
  // sa réponse à tout ; le versatile attend une éternité parce qu'il n'a envie
  // de rien décider ; celui qui n'a pas d'humeur est un soldat ordinaire, et un
  // soldat ordinaire ne reste pas trois minutes à regarder ses pieds.
  // Le sourd n'y figure pas par oubli : il ne compte pas le silence, parce que
  // pour lui il n'y a jamais eu autre chose. Il exécute son premier ordre
  // jusqu'au bout de la nuit, et c'est ce qui était déjà écrit de lui.
  // `SILENCE` est déposé : ce que chacun supporte de silence se demande
  // maintenant à `survival-stack/4-envie.js`, homme par homme et d'après ce
  // qu'il a autour de lui. Voir `initiative()`.
  // Ce qu'il fait alors, s'il n'a ni consigne ni intention à quoi se raccrocher,
  // vient de `survival-stack/3-interpretation.js` : c'est le cas limite de
  // l'interprétation — la lettre a fini de s'user, et il reste un homme.
  // `DE_SOI_MEME`, indexé sur une `humeur` que la couche 1 avait dissoute, est
  // déposé avec elle.
  // Et ce qu'une intention devient quand l'ordre qui la portait est devenu
  // impossible — l'aile qu'on devait suivre n'existe plus, la porte est tombée.
  const DE_LINTENTION = { entrer: "avancer", couvrir: "tenir", durer: "repli" };

  // --- LES DEUX FINS QUI NE PASSENT PAS PAR LE VERROU ------------------------
  //
  // Tout ce qui précède fait tomber une porte à coups de hache. Il y a deux
  // façons pour que la nuit se décide autrement, et elles ne se ressemblent
  // pas : l'une arrête l'assaut, l'autre l'ouvre pour rien.
  //
  //   LE ROI VERSE. Aegon n'est pas à la porte : il est à deux cent trente
  //     mètres en arrière, sur une charrette, dans l'axe même par lequel une
  //     armée qui rompt s'en retourne. On ne le tue donc pas d'un coup d'épée
  //     — personne ne peut l'atteindre — il est ÉCRASÉ PAR LES SIENS. Ce n'est
  //     pas un jet de dés : c'est la conséquence arithmétique d'une déroute qui
  //     lui passe dessus, et elle n'arrive que si l'assaut s'effondre.
  //   BOISDUR EMPORTE LA SALLE. Une porte ouverte de l'intérieur ne coûte pas
  //     un point de verrou. Mais il faut d'abord que le Donjon SACHE, et c'est
  //     là que se trouve le fait le plus cher de la nuit : un homme court, et
  //     pendant qu'il court la ville sait ce que le pouvoir ignore.
  //
  // Les deux clefs sont des HORLOGES, pas des chances. Elles se tirent une
  // fois, à la graine, et la nuit se joue sur laquelle tombe la première —
  // exactement comme les six têtes qui ne délibèrent pas ensemble.
  const ROI_RECUL   = 230;    // où on l'a posé, en arrière de la porte
  const ROI_ESCORTE = 40;     // les hommes autour de la charrette
  const ROI_PRESSE  = 7;      // le rayon dans lequel on le bouscule
  // En hommes-secondes de reflux, et à l'échelle : quinze fuyards pendant six
  // secondes versent la charrette, trois qui passent ne la versent pas.
  const ROI_VERSE   = 90;
  // (Il y avait ici un DETOUR_RUE de 1,4 — ce qu'on supposait qu'une rue
  // ajoute à la ligne droite, du temps où l'arrivée du messager se calculait.
  // Il court maintenant sur le même A* que la colonne : le détour n'est plus
  // estimé, il est parcouru, et la distance qu'il annonce est celle qu'il a
  // réellement faite.)
  // ELLES SE MESURENT SUR LA NUIT, PAS SUR L'ENVIE QU'ON EN A. Premières
  // valeurs : dix à quarante minutes de délibération, contre une nuit dont la
  // première porte commence à céder à QUATRE-VINGT-CINQ SECONDES. La salle
  // finissait donc d'en discuter longtemps après que tout était joué, et la
  // branche de celui qui a la clef ne pouvait se produire dans aucune
  // cuisson — un chemin mort, c'est-à-dire un mécanisme qui n'existe pas.
  //
  // Les deux fourchettes se chevauchent maintenant, et c'est le point : la
  // nuit se décide sur laquelle tombe la première, et il faut donc qu'aucune
  // des deux ne soit sûre de gagner. Celui qui a la clef part très
  // légèrement devant, parce qu'il a décidé avant d'entrer dans la salle —
  // c'est son personnage, pas un pouce sur la balance.
  //
  // ET ELLES SE MESURENT SUR LA NUIT QU'ON CUIT, pas sur celle qu'on imagine.
  // Le sac de production fait DIX MINUTES : la première porte commence à
  // céder à 1′25″, la quatrième est enfoncée à 7′15″, et le Donjon apprend à
  // 5′54″. Il reste donc QUATRE MINUTES de nuit pour que la salle tranche —
  // une délibération de dix minutes tombe après la dernière image, ce qui est
  // la même faute que la précédente d'un cran plus loin : le chemin n'était
  // plus mort, il était hors champ.
  const DELIBERE_TENIR  = [70, 240];      // le châtelain, qui n'a jamais choisi
  const DELIBERE_OUVRIR = [60, 220];      // et celui qui a la clef sur lui

  // --- ce qui distingue un corps d'un autre ---------------------------------
  // Trois réglages, et pas un de plus. Ils ne sont pas des bonus : ce sont les
  // trois façons dont une troupe peut ne pas se comporter comme la moyenne, et
  // chacune se paie. Le ferme meurt sur place au lieu de reculer ; le sourd ne
  // reçoit jamais l'ordre qui l'aurait sauvé ; le versatile n'est jamais là où
  // on l'attend.
  // LES TROIS PLANCHERS D'`humeur` SONT DÉPOSÉS. Ils vivent maintenant dans
  // `ECOLE_CORPS` — dressage, vécu, surdité, fond —, c'est-à-dire dans des
  // grandeurs d'homme au lieu de trois exceptions câblées dans `survie()`.

  // --- la peur ---------------------------------------------------------------
  // Elle a sa propre physique, et elle ne ressemble pas à celle des soldats.
  // On ne fuit pas un homme : on fuit UNE MASSE — et l'on ne fuit pas en
  // ligne droite, on fuit par la rue, parce qu'il y a des murs.
  const ALERTE      = 90;     // à partir d'où l'on voit et l'on part
  const FOYER_M     = 40;     // la maille qui agrège les soldats en masses
  const FOYER_MIN   = 3;      // sous trois hommes, ce n'est pas une armée
  const SAISI       = [0.4, 2.2];   // le temps de comprendre, avant de courir
  const FUITE_MIN   = 12;     // on court au moins ça avant de songer à rentrer
  const RENTRE_MAX  = 300;    // au-delà, on renonce et l'on se terre où l'on est
  const CALME       = 90;     // le temps qu'il faut pour ressortir
  const RUMEUR      = 30;     // la panique se prend aussi des autres
  const RUMEUR_MIN  = 2;      // il en faut deux qui courent pour y croire
  const PANIQUE_MAX = 4000;   // au-delà, on ne prend plus personne en charge
  // Les manteaux d'or ne fuient pas : ils vont voir. C'est leur métier, et
  // c'est la plus belle chose que cette couche sache produire — une rue qui se
  // vide dans un sens et se remplit d'or dans l'autre.
  const CONTRE = /^(guet|sergent|capitaine-guet)$/;
  const APPROCHE = 25;        // jusqu'où le guet s'avance, et pas plus loin

  // --- CEUX QUI PRENNENT LES ARMES -------------------------------------------
  // LE SEUL COMPORTEMENT QUI FASSE GROSSIR L'ASSAUT, et il manquait. La couche
  // de peur savait faire deux choses : fuir, et — pour le guet — aller voir.
  // Il n'y avait aucun moyen de REJOINDRE, ce qui est absurde pour cette
  // bataille-ci : l'armée de Cole EST le peuple, et un soulèvement qui ne
  // recrute pas en traversant ses propres rues n'est pas un soulèvement.
  //
  // ON NE TIRE PAS AU SORT, ON LIT L'HOMME. Le métier, l'âge, et un déphasage
  // qui vient de son identité — exactement comme ses heures de sortie. Le même
  // homme prendra toujours les armes, et son voisin ne le fera jamais.
  //
  //   LE MÉTIER — ceux qui ont des bras et un outil qui coupe. Un portefaix,
  //     un tanneur, un écarnisseur. Pas une septa, pas un clerc, pas un
  //     changeur : ils ont autant de raisons d'en vouloir au Donjon, et pas
  //     les mains pour ça.
  //   L'ÂGE — de seize à quarante-cinq ans, et c'est la cellule qui le dit.
  //   LE GUET NE REJOINT JAMAIS. Il va voir, c'est son métier, et c'est déjà
  //     l'autre moitié de cette couche.
  //
  // Il faut aussi qu'il ait VU la masse : on ne rejoint pas une rumeur. C'est
  // la seule condition qui ne tienne pas à l'homme, et c'est la bonne — elle
  // fait que le recrutement suit le chemin de l'armée, rue par rue, au lieu de
  // lever la ville d'un coup.
  //
  // ET IL Y A DEUX CAMPS, ce qui est le vrai sujet. Une ville qui se soulève
  // ne se soulève jamais entière : le même cri, dans la même rue, à la même
  // minute, envoie le portefaix chercher une hache et l'aubergiste barrer sa
  // porte. Ce n'est pas une opinion tirée au sort — c'est ce qu'on a à perdre.
  //
  //   AVEC — ceux qui n'ont rien qu'un outil qui coupe. Portefaix, tanneurs,
  //     brassiers, écarnisseurs, vidangeurs. Ils travaillent chez un autre.
  //   CONTRE — ceux qui ont une porte à eux et du stock derrière. Aubergiste,
  //     marchand, changeur, logeur, meunier, grenetier. Ils ne défendent pas
  //     le roi : ils défendent leur rue, et ça les met du même côté que lui
  //     pour la nuit. C'est plus vrai, et c'est plus cruel.
  //
  // Le reste de la ville ne prend pas les armes du tout — et c'est la majorité.
  const AVEC = /^(portefaix|tanneur|apprenti-tanneur|teinturier|apprenti-teinturier|brassier|fendeur|charbonnier|ecarnisseur|saigneur|cordier|videur|compagnon|marmiton|balayeur|frotteur|vidangeur|aide-vidangeur|valet-fosse|souffleur|palefrenier|aide-meunier|mitron|enfourneur)$/;
  const CONTRE_EUX = /^(aubergiste|tavernier|marchand|marchand-bois|changeur|logeur|loueur|meunier|grenetier|brasseur|boucher|forgeron|potier|voilier|etalier|clerc|clerc-halle|clerc-port|maitre-maison|intendant|gardien|garde-maison|garde-coffre|etuviste)$/;
  const PART_ARMES = 0.22;    // ce qu'une rue donne quand l'armée y passe
  const PART_BARRE = 0.30;    // ceux qui ont pignon se défendent plus volontiers
  // Les paliers auxquels un quartier qui se lève mérite une ligne. Bornés par
  // construction : quatre lignes par quartier, jamais une par homme. C'est la
  // même leçon que ce fichier a déjà apprise trois fois — un fait émis depuis
  // une couche qui tourne PAR PERSONNE doit être verrouillé PAR LIEU, sinon il
  // sort au rythme de la population et enterre la guerre sous sa propre rumeur.
  const PALIERS_ARMES = [1, 10, 40, 120];

  // Ce que chaque quartier a levé, des deux côtés. C'est le seul compteur de
  // cette couche, et il sert à deux choses : franchir les paliers, et dire à
  // la fin combien de gens cette nuit a mis dans la rue qui n'y étaient pas.


  function armer(p) {
    const z = situer(p.x, p.y).zone;
    let c = S.enArmes.get(z);
    if (!c) S.enArmes.set(z, c = { assaut: 0, garde: 0 });
    const n = ++c[p.prend];
    if (PALIERS_ARMES.indexOf(n) < 0) return;
    noter("prend-les-armes", p.x, p.y,
          { clef: "armes:" + p.prend + ":" + z + ":" + n,
            dit: { camp: p.prend, zone: z, combien: n,
                   role: p.role, age: p.an, femme: p.femme } });
  }

  const PAS = 1 / 20;         // le pas de simulation, fixe
  // La maille de voisinage suit L'ÉPAULE, pas le terrain : devant une porte,
  // trois cents hommes tiennent dans vingt mètres, et une maille de six mètres
  // y met cent personnes par case — c'est-à-dire qu'on refait du n² là où l'on
  // croyait l'avoir évité. Trois mètres coûtent quatre fois plus de cases
  // vides, qui ne coûtent rien, et divisent par trois le vrai travail.
  const MAILLE = 3;

  // ---- l'état ---------------------------------------------------------------


  // LES DEUX LIMITES DU SOL. `sousToit`, chargé par `enterrer()`, sait où sont
  // les murs ; `sousEau`, chargé depuis le relief qui dessine aussi la côte,
  // sait où un homme en armure ne peut pas poser le pied. Les garder séparées
  // est essentiel : un toit reste un intérieur possible, l'eau jamais.
  // ⚠ PAS `bati` : LE NOM EST DÉJÀ PRIS l. 6429 par le bâti qu'on PILLE, et le
  // four l'a dit tout de suite — « Identifier 'bati' has already been declared ».
  // Troisième collision de nom dans cette IIFE de six mille lignes après `corps`
  // et `semer`, et la seule qui se soit vue avant de tourner.

  // Une épreuve peut remplacer le sol de Port-Réal par un terrain abstrait.
  // Ce n'est pas un passe-droit pour un scénario : tous les lecteurs du sol
  // (pose, mouvement, vision et commandement) interrogent alors la même
  // fonction. `rejouer()` l'efface avant de dresser la scène suivante.







  // Toutes les unités qui ont un chef et peuvent recevoir un mouvement.
  // `escouades` reste le canal d'ordres de l'assaut ; `formations` est neutre
  // au camp et porte aussi bien une vintaine en marche qu'un poste de garde.


  // Un ralliement est un repère d'armée temporaire. Il porte les places des
  // échelons ; jamais une liste de destinations identiques pour les hommes.

  // Une seule carte subjective peut être ouverte à la fois. L'identifiant est
  // celui du commandant, jamais celui de son camp : changer de chef doit
  // réellement changer de monde connu, même entre deux hommes du même rang.

  // Une mission de ratissage n'est pas une connaissance partagée. Elle ne
  // contient que le terrain objectif et l'état physique des bâtiments ; les
  // faits, engagements et ordres entendus restent sur chaque formation.




                              // un par corps, et ils ne se parlent pas entre eux



  // (la grille de voisinage vit plus bas, avec `semer` — elle n'est plus une
  // `Map` mais deux tableaux d'entiers, pour la raison qu'on va lire ici même.)
  // LA PEUR SE RANGE DANS LA CELLULE, PAS DANS UNE MAP À CLEFS DE TEXTE.
  // C'était une `Map` indexée par « 11-3:4127 » : le veto est demandé pour
  // CHACUN des quatre cent mille habitants à chaque calcul de la foule, et
  // fabriquer cette clef quatre cent mille fois coûtait NEUF SECONDES par
  // image — pour un simple accès tableau. C'est mot pour mot la leçon que
  // `journee.js` porte déjà en commentaire ; il a fallu la réapprendre.
  //
  // Donc : un tableau creux posé sur la cellule (`cel._peur[k]`), indexé comme
  // le binaire, et une liste plate pour ce que la simulation doit parcourir.

  let compte = { a: 0, d: 0, morts: 0, blesses: 0, fuyards: 0, rallies: 0,
                 contreCharges: 0 };

  // --- les annales -----------------------------------------------------------
  // Une liste plate de faits, et un jeu de verrous pour que chacun ne s'écrive
  // qu'une fois. `dejaDit` est le seul mécanisme : on lui donne une clef, il
  // rend vrai la première fois et faux ensuite. Tout ce qui doit être unique —
  // le premier sang, un chef, une escouade, un quartier — passe par lui.


  // Un jugement appartient à l'unité qui l'a formé. Une WeakMap évite de lui
  // inventer un identifiant persistant et disparaît avec le tableau du rejeu.
  const jugementsRupture = new WeakMap();
  const dejaDit = (clef) => (S.dits.has(clef) ? true : (S.dits.add(clef), false));

  // REJOUABLE — et il a fallu le rendre vrai. La graine était posée à la
  // construction du module et n'était jamais remise : deux `rejouer()` dans la
  // même session donnaient deux batailles différentes, alors que le
  // commentaire promettait le contraire. Tant qu'on regardait, ça ne se voyait
  // pas ; le jour où l'on CUIT une bataille dans un fichier, un déroulé qui ne
  // se reproduit pas est un fichier qu'on ne peut ni vérifier ni corriger.
  // Il vit dans `bataille/hasard.js` — la première feuille détachée de ce
  // fichier, et la seule qu'on puisse tester pour de bon. On l'emprunte ici
  // sous les noms qu'il a toujours eus, pour que rien du reste ne bouge.
  const { R, entre, cloche } = window.BatailleHasard;
  const semerGraine = window.BatailleHasard.semer;

  // ---- la mise en place -----------------------------------------------------
  // On ne pose rien à la main : la porte et le donjon sont des repères du plan
  // cuit, avec leurs mètres. Si demain le plan bouge, la bataille bouge avec.
  function repereDuPlan(nom, genre) {
    const l = (S.plan && S.plan.reperes) || [];
    return l.find((r) => r.nom === nom) || l.find((r) => r.genre === genre) || null;
  }

  function portes() {
    return ((S.plan && S.plan.reperes) || []).filter((r) => r.genre === "porte");
  }

  // ---- SITUER UN FAIT -------------------------------------------------------
  // Un événement sans lieu ne se joue pas : « la porte cède » est une donnée,
  // « la porte cède, au bourg de la Gadoue, à quarante pas de la Vieille Porte »
  // est une scène. On situe donc par ce que le plan cuit connaît déjà — trente-
  // quatre repères nommés et douze quartiers — et jamais par des coordonnées.
  //
  // EN PAS, PAS EN MÈTRES. C'est la règle du jeu et ce n'est pas une coquetterie :
  // personne, dans cette ville, ne mesure une rue en mètres. Un pas fait 0,75 m.
  const PAS_M = 0.75;
  const enPas = (m) => Math.round(m / PAS_M / 5) * 5;

  // « à 135 pas de Le quai d'amont » — les noms du plan portent leur article,
  // et la préposition doit se contracter comme en français. Ça a l'air d'un
  // détail ; c'est la première chose que l'œil accroche dans un document qu'on
  // lit à voix haute, et ça suffit à le faire passer pour une sortie de machine.
  function duNom(nom) {
    if (/^Le /.test(nom))  return "du " + nom.slice(3);
    if (/^Les /.test(nom)) return "des " + nom.slice(4);
    if (/^La /.test(nom))  return "de la " + nom.slice(3);
    if (/^L'/.test(nom))   return "de l'" + nom.slice(2);
    return "de " + nom;
  }

  function situer(x, y) {
    let rep = null, dr = Infinity;
    for (const r of (S.plan && S.plan.reperes) || []) {
      const d = (r.x - x) ** 2 + (r.y - y) ** 2;
      if (d < dr) { dr = d; rep = r; }
    }
    let q = null, dq = Infinity;
    for (const c of (S.plan && S.plan.quartiers) || []) {
      const d = (c.x - x) ** 2 + (c.y - y) ** 2;
      if (d < dq) { dq = d; q = c; }
    }
    dr = Math.sqrt(dr);
    // Au-delà de trois cents mètres, un repère ne repère plus rien : on ne dit
    // pas « à mille pas du Donjon Rouge », qui ne situe personne.
    const bout = rep && dr < 300
      ? (dr < 12 ? "devant " + rep.nom : "à " + enPas(dr) + " pas " + duNom(rep.nom))
      : null;
    // LE REPÈRE L'EMPORTE, ET IL EST SEUL QUAND IL EST LÀ. Le plan ne donne
    // d'un quartier que son centre et son nombre de maisons — pas son emprise.
    // Le plus proche centre est donc une devinette, et cousue à un repère
    // précis elle produisait pire qu'une erreur : une INCOHÉRENCE. Deux blessés
    // à quarante pas l'un de l'autre, devant la même porte, l'un « au port » et
    // l'autre nulle part — parce que le seuil du quartier passait entre eux.
    // Dans un document qu'on lit d'affilée, ça se voit à la deuxième ligne et
    // ça décrédibilise tout le reste.
    //
    // Donc : un repère proche EST le lieu, et le quartier n'est que le recours
    // de ceux qui n'en ont aucun.
    const cq = q && Math.sqrt(dq) < 900 ? q.nom : null;
    return {
      quartier: bout ? null : cq,
      repere: bout ? rep.nom : null,
      ou: bout || cq || "hors la ville",
      // `zone` est le quartier le plus proche SANS condition — il ne s'affiche
      // jamais, il sert à regrouper. C'est la clef par laquelle on évite
      // d'écrire quatre-vingt-dix fois que la peur gagne un endroit.
      zone: q ? q.nom : "hors la ville",
    };
  }

  // ===========================================================================
  // LES TÉMOINS — ce qui rend un fait AMPLIFIABLE
  //
  // Un fait daté et situé est déjà utile. Un fait daté, situé, ET dont on sait
  // QUI l'a vu est autre chose : ce n'est plus une ligne à lire, c'est une
  // piste à remonter. La troupe ne lit pas les annales — elle va trouver la
  // teinturière du Culpucier qui était dans la rue à cette heure-là, et elle
  // lui demande. Et la teinturière peut mentir, se tromper, ou vouloir qu'on
  // la paie : c'est exactement la grammaire du jeu.
  //
  // ON NE PREND QUE LES PANIQUÉS, et ce n'est pas une limite mais la bonne
  // définition. Les quatre cent mille autres sont chez eux, porte fermée, et
  // n'ont rien vu ; ceux que la couche de peur a pris en charge sont
  // précisément les gens qui étaient DEHORS quand c'est arrivé.
  //
  // Le coût est nul à l'échelle du sac : quelques dizaines de faits, un
  // balayage de la liste des paniqués pour chacun.
  const VUE_TEMOIN = 50;      // au-delà, dans une rue, on ne voit plus qui tombe
  const TEMOINS_MAX = 6;      // on n'a pas besoin de la foule, on a besoin de noms

  function temoinsDe(x, y) {
    const l = [];
    for (const p of S.paniques) {
      // Celui qui s'est terré n'a plus rien vu : il est derrière sa porte.
      if (p.etat === "terre") continue;
      const d = Math.hypot(p.x - x, p.y - y);
      if (d > VUE_TEMOIN) continue;
      l.push({ d, p });
    }
    l.sort((a, b) => a.d - b.d);
    return l.slice(0, TEMOINS_MAX).map(({ d, p }) => ({
      id: p.id, age: p.an, role: p.role || null, femme: p.femme,
      // SON ADRESSE, et c'est le champ qui compte. Le reste décrit ; celui-ci
      // permet d'aller frapper à sa porte.
      chez: [+p.chez[0].toFixed(1), +p.chez[1].toFixed(1)],
      // LE QUARTIER, PAS LE REPÈRE LE PLUS PROCHE. `situer().ou` vise le repère
      // et donne « à 40 pas de la Salle de l'entrepôt » — ce qui, pour dire OÙ
      // HABITE quelqu'un, ne veut rien dire et produisait des monstres comme
      // « portefaix de aire de bris ». Ce dont on a besoin ici est le nom sous
      // lequel un quartier se demande dans la rue.
      ou: situer(p.chez[0], p.chez[1]).zone,
      pas: enPas(d),
      // Le guet ne témoigne pas comme un teinturier : il fait un rapport, il
      // est cru, et ce qu'il dit finit dans un registre.
      guet: !!p.contre,
    }));
  }

  /**
   * Porter un fait aux annales. `clef` le rend unique quand elle est donnée —
   * un chef ne tombe qu'une fois, un quartier n'est gagné qu'une fois.
   * Rend faux quand le fait avait déjà été dit, ce qui permet d'enchaîner.
   */
  // ---- DEVANT CHEZ QUI -------------------------------------------------------
  // « La bannière de l'aile ouest tombe » est une donnée ; « elle tombe à
  // trente pas de chez Nonne la lavandière » est une scène. Le module posait
  // les treize noms sur le plan et ne s'en servait jamais : ils étaient un
  // décor de vérification, alors qu'ils sont la seule chose qui donne à un
  // fait quelqu'un sur qui tomber.
  //
  // Un repère du plan situe dans la VILLE ; un nom situe dans une VIE. Les deux
  // se cumulent, et c'est le second que le MJ ira frapper le lendemain matin.
  const PRES_FIGURE = 45;     // au-delà, ce n'est plus devant chez lui

  /**
   * La peur vient d'atteindre quelqu'un qui a un nom : on écrit ce qu'il fait.
   * Une fois par personne et par nuit — c'est `clef` qui le garantit.
   */
  function laMaisonDaCote(x, y) {
    const f = presDe(x, y);
    if (!f || f.camp !== "ville") return;
    noter("habitant", f.x, f.y,
          { clef: "habitant:" + f.nom, dit: { nom: f.nom, fait: f.dit } });
  }

  function noter(quoi, x, y, o) {
    if (o && o.clef && dejaDit(o.clef)) return false;
    const l = situer(x, y);
    const f = presDe(x, y);
    S.annales.push(Object.assign({
      t: +S.temps.toFixed(2), quoi,
      x: +x.toFixed(1), y: +y.toFixed(1),
      quartier: l.quartier, repere: l.repere, ou: l.ou, zone: l.zone,
      pres: f ? f.nom : null,
      pres_pas: f ? enPas(Math.hypot(f.x - x, f.y - y)) : null,
      temoins: temoinsDe(x, y),
    }, o && o.dit));
    return true;
  }

  // LA TOPOLOGIE — le sol, le bâti, l'eau, et ce qu'un corps peut y faire.
  //
  // Elle est SORTIE : `bataille/moteur/monde/topologie.js`. Le code n'a pas
  // été réécrit, il a été déplacé — commentaires compris, parce que ce sont
  // eux qui portent les trois fautes qu'on a mis des semaines à trouver (un
  // homme posé dans un mur, la marge qui bloque une venelle, la rue plus
  // large que le masque).
  //
  // On redonne ici les mêmes noms au même sens : aucun des quarante et un
  // sites d'appel ne change, et l'étalon du moteur doit rendre exactement la
  // même bataille. C'est la forme que prendront les quatre extractions
  // suivantes — navigation, mouvement, collisions, combat.
  const Topologie = window.BatailleMondeTopologie.creer(S, { EPAULE });
  const { dehors, solConnu, obstacleConnu, obstacleEn, libreEn,
          reglerTerrainEpreuve, degager, murPres, obstaclePres,
          demiLibre } = Topologie;
  // ===========================================================================
  // L'ORDRE DE BATAILLE
  // ===========================================================================
  // Les effectifs, les noms et les humeurs sont ceux de `docs/bataille/`.
  // Ici on ne fait que les POSER : ce bloc dit combien, où, et dans quelle
  // forme — jamais pourquoi.
  //
  // L'ÉCHELLE EST UN OUTIL DE REPÉRAGE, PAS UN RÉGLAGE. À neuf mille cinq cents
  // hommes on ne voit plus une formation, on voit une tache — et l'on ne va pas
  // attendre dix minutes de cuisson pour s'apercevoir qu'un corps part du
  // mauvais côté. Un vingtième rend quatre cent soixante-quinze corps, c'est-à-
  // dire le coût de la bataille d'avant, et la MÊME géométrie : mêmes
  // distances, mêmes rues, mêmes largeurs de front. On règle la mise en place à
  // l'œil, puis on cuit à 1.
  //
  // ELLE TOUCHE LES DEUX CAMPS, ET IL A FALLU S'EN APERCEVOIR EN COMPTANT.
  //
  // Elle ne touchait que l'assaut, et l'argument tenait quand la garde faisait
  // cent vingt-cinq hommes : des postes tenus un par un, qu'on ne divise pas.
  // La garnison est passée à sept cent quatre — deux cents à la Gadoue, cent à
  // chacune des trois autres, trois cents à l'anneau — et l'argument est mort
  // ce jour-là sans que personne le remarque, parce qu'un chiffre absolu ne
  // proteste pas quand celui d'en face rétrécit.
  //
  // Mesuré porte par porte, avant correction :
  //
  //     --hommes 300     à la Gadoue   123 contre 201   soit 0,61
  //     --hommes 1700    à la Gadoue   700 contre 201   soit 3,48
  //
  // Autrement dit, régler la mise en place « à l'œil » à petite échelle ne
  // montrait pas la même bataille en plus petit : ça en montrait une autre, où
  // l'assaut est en infériorité à chacune des quatre portes. Une échelle qui
  // change l'issue n'est plus une échelle, c'est un réglage de difficulté qu'on
  // s'est caché à soi-même.
  //
  // Donc : TOUT CE QUI EST UNE MASSE SE DIVISE, la géométrie jamais. Les sept
  // hommes de front, les trois mille points de porte, les six cent treize
  // mètres de rue et la portée d'une bannière ne bougent pas d'un pouce —
  // c'est la même porte et la même ville. Seuls les effectifs suivent, des deux
  // côtés, et le rapport de forces est le même à toutes les échelles.
  // PLEINE ÉCHELLE. Le vingtième était un réglage de mise au point, et il
  // coûtait plus qu'il ne montrait : le plancher d'escouade ci-dessous remonte
  // les petits corps à vingt hommes SANS toucher aux gros, si bien qu'à 0,05
  // une armée pensée en 500/350/250/400/200 sortait en 25/20/20/20/20 — cinq
  // corps du même poids, et tout le dessin perdu. La garde, elle, n'a pas ce
  // plancher-là (`garnison`, trois hommes) : elle tombait à dix quand l'assaut
  // en gardait quarante-cinq. Le déséquilibre qu'on voyait à l'écran venait de
  // là, et de rien d'autre.

  const combien = (n) => Math.max(PAR_ESC, Math.round(n * S.ECHELLE));
  // Le plancher est plus bas que celui d'un corps : un poste de garde n'a pas
  // d'escouade, et trois hommes à une poterne sont une image juste là où trois
  // hommes ne font pas un corps d'assaut.
  const garnison = (n) => Math.max(3, Math.round(n * S.ECHELLE));

  // Les six corps. `recul` compte en mètres vers le DEHORS de la porte, `cote`
  // le long du rempart (positif vers le quai d'aval). Les deux se prennent sur
  // le repère du plan cuit : si la porte bouge un jour, l'armée bouge avec.
  //
  // LA FORME EST L'ARGUMENT, et c'est pour ça qu'il y en a quatre. Une colonne
  // arrive par la tête et s'engorge ; une ligne arrive à plat ; des paquets
  // arrivent de trois côtés et jamais ensemble ; une nuée n'arrive pas, elle
  // se répand. Personne n'écrit ces différences ensuite — elles tombent d'ici.
  const CORPS = [
    { id: "cole", nom: "Ser Criston Cole", hommes: 500, humeur: null,
      forme: "colonne", parRang: 8, recul: 110, cote: 0, rangTete: 0,
      dit: "le centre — il frappe la porte, et il est au PREMIER rang" },
    { id: "vantre", nom: "Ser Loryn Vantre", hommes: 350, humeur: null,
      porte: "La porte de Fer",
      forme: "colonne", parRang: 6, recul: 300, cote: 450, rangTete: 0,
      dit: "le port — il arrive en flanc, donc en retard, et il a les outils" },
    { id: "cranche", nom: "Ser Ormond Cranche", hommes: 250, humeur: "ferme",
      porte: "La porte du Roi",
      forme: "ligne", parRang: 25, recul: 170, cote: -130, rangTete: 0,
      dit: "l'aile ferme — il ne rompt pas, et il ne retire pas ses morts" },
    { id: "gueux", nom: "le sergent Rous Cantel", hommes: 400, humeur: "sourd",
      porte: "La Vieille Porte",
      forme: "nuee", largeur: 150, fond: 120, recul: 270, cote: -330, rangTete: 0,
      dit: "on leur a retiré les cors pour que ce soit réaliste — ils n'entendent rien" },
    { id: "bleusailles", nom: "Petit Wend", hommes: 200, humeur: "versatile",
      forme: "nuee", largeur: 130, fond: 100, recul: 130, cote: 230, rangTete: 0,
      dit: "les levées neuves — elles refluent, et elles reviennent en riant",
      // LA CONSIGNE — ce qu'on lui a dit AVANT, et qui ne se transmet donc
      // jamais. Elle est déjà dans sa tête au premier pas : c'est ce qui fait
      // qu'une aile coupée de tout n'est pas une aile vide, et c'est
      // historiquement le seul ordre qui arrive toujours à destination.
      // Celle-ci dit littéralement « gardez-vous à deux cents pas de Cole ».
      consigne: { verbe: "suivre", objet: { corps: "cole" }, marge: 200,
                  intention: "couvrir" } },
  ];

  // QUATRE PORTES, ET CHAQUE VERROU TOMBE À SON HEURE.
  //
  // Les six corps entraient tous par la Gadoue : six chaînes de commandement
  // qui se disputaient un seul seuil de six mètres, où sept hommes cognent à la
  // fois. Neuf mille cinq cents hommes derrière une porte, c'est une file, pas
  // un sac — et surtout ça n'a jamais eu lieu ainsi : une ville se prend par
  // plusieurs portes, et ce qui décide de tout est que l'une cède avant les
  // autres.
  //
  // Un corps sans `porte` prend celle qu'on donne au four (la Gadoue par
  // défaut) : Cole la frappe de face, Vantre arrive par les quais, Petit Wend
  // suit. Les trois autres ont la leur. Le Donjon reste commun — c'est ce qui
  // fait converger les colonnes au lieu de les disperser.

  const porteDuCorps = (c, defaut) => c.porte || defaut;

  // COMBIEN D'AILES UN CORPS A, À EFFECTIF PLEIN — et c'est ce nombre-là qui
  // fait foi à toutes les échelles. Un corps de deux mille quatre cents hommes
  // se commande en vingt-quatre ailes ; à un vingtième il a moins de monde
  // dedans, mais il se commande toujours en vingt-quatre. La structure est de
  // la fiction, l'effectif est du réglage.
  const ailesDe = (c) =>
    Math.max(1, Math.round(c.hommes / (PAR_ESC * ESC_PAR_AILE)));

  /** Le repère d'un corps : le dehors de la porte, et le long du rempart. */
  // ---- LA FORMATION EST UNE RELATION, PAS VINGT ITINÉRAIRES ---------------
  //
  // Un homme ne sait pas refaire la route de son chef. Il sait seulement qui
  // est son vintenar, quels dos lui sont familiers, et à peu près où il doit
  // se trouver par rapport à eux. La place est donc exprimée DANS le cadre de
  // la vintaine : un recul derrière le chef et une fraction de sa largeur.
  // Le terrain pourra comprimer cette largeur sans jamais changer l'identité
  // de l'unité.
  const FILES_VINTAINE = [-0.75, -0.25, 0.25, 0.75];
  const PAS_DE_RANG = 1.05;

  // LA LIAISON EST ICI ET NON PLUS HAUT, et c'est une contrainte d'execution
  // et non de gout : `FILES_VINTAINE` et `PAS_DE_RANG` sont declares juste
  // au-dessus, et un `const` n'est pas hoisse. Posee avant eux, cette ligne
  // levait « Cannot access 'FILES_VINTAINE' before initialization » au
  // chargement du moteur — avant qu'une seule bataille ait commence.
  const Unite = window.BatailleUniteIdentite.creer(S, { FILES_VINTAINE, PAS_DE_RANG, dehors, noter });
  const { axeDe, placeDeFormation, cadreNeuf, creerFormation, affecterFormation, changerDeFormation, formationDe, guideDe, successions } = Unite;

  /** Les places d'un corps, dans sa forme à lui. */
  function poserCorps(c, porte) {
    const { nx, ny, tx, ty } = axeDe(porte);
    const en = (recul, cote) => ({
      x: porte.x + nx * recul + tx * cote + entre(-.25, .25),
      y: porte.y + ny * recul + ty * cote + entre(-.25, .25),
    });
    const n = combien(c.hommes), l = [];

    if (c.forme === "nuee") {
      // Aucune formation, et c'est le propos. La BOÎTE est l'information : sa
      // largeur dit qu'ils tiennent trois rues et qu'aucun ordre ne les
      // traversera jamais d'un bout à l'autre.
      for (let i = 0; i < n; i++)
        l.push(en(c.recul + entre(-c.fond / 2, c.fond / 2),
                  c.cote + entre(-c.largeur / 2, c.largeur / 2)));
      return l;
    }
    if (c.forme === "paquets") {
      // Trois grappes qui n'ont pas le même chemin à faire. Elles n'arriveront
      // donc pas ensemble, et personne n'a eu à écrire qu'elles arrivent en
      // désordre : il suffisait de ne pas les poser au même endroit.
      const p = c.paquets, par = Math.ceil(n / p.length);
      for (let i = 0; i < n; i++) {
        const [r0, c0] = p[Math.min(p.length - 1, Math.floor(i / par))];
        const k = i % par;
        l.push(en(r0 + Math.floor(k / 7) * 1.3, c0 + (k % 7 - 3) * 1.2));
      }
      return l;
    }
    // Colonne et ligne sont la MÊME chose, et c'est tout l'intérêt de les avoir
    // écrites pareil : six de front font un serpent, trente font un mur, et
    // personne n'a eu à décider de la profondeur.
    const par = c.parRang;
    for (let i = 0; i < n; i++)
      l.push(en(c.recul + Math.floor(i / par) * 1.4,
                c.cote + (i % par - (par - 1) / 2) * 1.1));
    return l;
  }

  // LES NOMMÉS QUI NE SE BATTENT PAS. Ils ne sont PAS dans `hommes`, et c'est
  // une décision : un corps qui entre dans la boucle a une morale, une case de
  // grille et un coût par pas, et aucun de ceux-là n'a de raison d'en avoir.
  // Ce sont des repères humains — on les voit, on les nomme, et le jour où un
  // fait tombe à côté d'eux, la relecture saura devant QUI il est tombé.


  // Aegon, sa presse, et ce qui a arrêté la nuit s'il y a lieu. `arret` est
  // le seul état global de tout le module qui interdise quelque chose : quand
  // il est posé, plus aucun assaillant ne se reprend et plus aucune tête ne
  // délibère. C'est ce que veut dire « tout s'arrête ».


  // Le coureur parti de la première porte qui cède, et la salle qui l'attend
  // sans le savoir. `averti` est l'heure où le Donjon apprend ; tout ce que les
  // deux lords décident se compte à partir de là et jamais avant.
  // UN MESSAGER EST UN HOMME, PAS UNE FORMULE. La première version calculait
  // son arrivée — heure de départ, plus la distance divisée par la vitesse de
  // course — si bien que le seul porteur de toute la nuit qui ne pût jamais
  // échouer était précisément celui qui portait la nouvelle la plus chère.
  // Toute la chaîne de commandement de l'assaut repose sur l'inverse : un
  // coureur sort de son escouade, ne rend pas les coups, et peut mourir en
  // chemin avec son ordre. Le Donjon n'avait aucune raison d'être épargné.
  //
  // CHAQUE PORTE QUI CÈDE ENVOIE LE SIEN, et aucune ne sait ce que les autres
  // ont fait. Quatre postes, quatre hommes, à vingt minutes d'intervalle : le
  // premier qui arrive est celui qui compte, et si les quatre tombent, le
  // Donjon apprendra la chose en voyant la colonne monter la rue.


  // L'anneau s'est retiré de lui-même : plus personne ne tient le cercle, et
  // les assaillants trouveront une cour. C'est l'autre moitié de la seconde
  // fin — celle qui ne coûte pas un point de verrou parce qu'il n'y a plus de
  // verrou à coûter.


  // ---- LA TREMPE — CE QUI FAIT QUE DEUX HOMMES NE SONT PAS LE MÊME HOMME ----
  // C'EST D'ICI QUE PARTENT LES MOTIFS, et c'est ce qui manquait à toutes les
  // règles précédentes. Elles sont justes et elles sont IDENTIQUES pour tout le
  // monde : deux mille cinq cents hommes franchissent donc le même seuil au
  // même instant, et l'on obtient des vagues — une ligne qui recule d'un bloc,
  // une autre qui tient d'un bloc. Rien ne se déforme, rien ne s'effiloche,
  // aucun endroit ne cède avant les autres.
  //
  // Une seule valeur par homme, de −1 (il se garde) à +1 (il y va), tirée une
  // fois pour toutes et jamais retouchée. Elle entre dans le compte du cercle
  // — donc dans tout ce qui en découle : quand il engage, quand il décroche,
  // jusqu'où il poursuit un isolé.
  //
  // NORMALE, PAS UNIFORME, et ce n'est pas un détail : sur une loi plate on
  // aurait autant de casse-cou que d'ordinaires, et la ligne se déferait
  // partout à la fois. Sur une normale, la masse est au milieu et les extrêmes
  // sont rares — ce sont EUX qui font les accidents locaux : un point qui tient
  // quand tout lâche autour, un autre qui part trop tôt et entraîne ses trois
  // voisins par la contagion. C'est la somme de quatre tirages (Irwin–Hall),
  // bornée à [−1, 1] par construction, donc sans écrêtage qui referait une
  // bosse aux extrémités.
  const { trempe, souplesse } = window.BatailleHasard; // voir bataille/hasard.js

  // ---- L'ŒIL — LE TEMPS DE S'APERCEVOIR DE QUELQUE CHOSE --------------------
  // TOUT LE MONDE RÉÉVALUAIT AU MÊME RYTHME, un tiers de seconde pile, et c'est
  // une horloge d'ordinateur et non un homme. Ce qu'elle produit se voit :
  // quand une situation tourne, elle tourne pour tous les voisins dans le même
  // dixième de seconde — donc des lignes qui basculent d'un bloc, et la
  // contagion qu'on a écrite plus haut ne sert à rien puisque personne n'a le
  // temps de voir partir son voisin AVANT de partir lui-même.
  //
  // De cent millisecondes à trois secondes. La borne basse est le coup d'œil
  // du gars qui a déjà l'ennemi dans les yeux ; la haute est celui qui a le
  // dos tourné et qui met trois secondes à comprendre que la ligne d'à côté
  // s'est vidée. Entre les deux, tout le monde.
  //
  // BIAISÉE VERS LE COURT, et il faut qu'elle le soit : le carré tire la masse
  // vers le bas — la plupart des hommes réagissent en moins d'une seconde, et
  // les longs sont l'exception. Une loi plate donnerait une armée d'un et demi
  // de moyenne, c'est-à-dire une armée endormie.
  //
  // C'est le dernier grain de désynchronisation, et probablement le plus
  // important : il fait que deux hommes dans la même situation ne décident
  // jamais au même instant, donc que ce qui se propage a le temps de se
  // propager. Sans lui, la contagion et la trempe travaillent dans le vide.
  // TROIS FACTEURS, ET ILS SE MULTIPLIENT :
  //
  //   LE TIRAGE — le hasard du moment. On regardait ailleurs, ou pas.
  //   LA VIVACITÉ — ce que l'homme vaut, une fois pour toutes. Certains ont
  //     l'œil et d'autres non, et ça ne change pas d'une minute à l'autre.
  //     Centrée sur 1, de 0,6 à 1,4 : le plus vif remarque deux fois plus vite
  //     que le plus lourd, ce qui est déjà beaucoup.
  //   LE SOUFFLE — et c'est le plus juste des trois. Un homme à bout ne voit
  //     plus rien : il baisse la tête, il compte ses pas, et la ligne d'à côté
  //     peut se vider sans qu'il s'en aperçoive. À souffle nul, il met près du
  //     double de temps.
  //
  // La boucle est agréable : l'épuisement ralentit la perception, la perception
  // lente fait rater le moment de souffler, et l'on s'enfonce. C'est exactement
  // ce qui arrive à un homme fatigué, et personne n'a eu à l'écrire.
  const OEIL_MIN = 0.10, OEIL_MAX = 3.0;
  const OEIL_FATIGUE = 0.8;
  const { vivacite } = window.BatailleHasard; // ⚠ facteur de DÉLAI : 0,6 = le vif

  const oeil = (h) => {
    const base = OEIL_MIN + (OEIL_MAX - OEIL_MIN) * R() * R();
    if (!h) return base;
    const s = h.souffle === undefined ? 1 : h.souffle;
    return base * (h.vivacite || 1) * (1 + (1 - s) * OEIL_FATIGUE);
  };

  // ---- LE SOUFFLE -----------------------------------------------------------
  // CE N'EST PAS UNE BARRE QUI VA À ZÉRO, et c'est tout le sujet. Une jauge qui
  // se vide donne un homme qui se bat à plein régime puis s'arrête net : deux
  // états, une falaise entre les deux, et une bataille qui se joue en un seul
  // élan. Ce qu'on veut est l'inverse — une valeur qui GLISSE, qui ne touche
  // jamais ses bornes, et dont chaque point coûte un peu plus que le précédent.
  //
  // D'où la relaxation : `s += (cible − s) × k × dt`. Elle tend vers sa cible
  // sans jamais l'atteindre — asymptotique dans les deux sens, comme un 1/x.
  // Un homme épuisé ne tombe pas à zéro, il s'approche de zéro ; un homme au
  // repos ne repart pas à neuf, il remonte vers un. Il n'y a donc aucun seuil
  // où quelque chose bascule, et c'est ce qui donne le glissement.
  //
  // TROIS RÉGIMES, ET LEUR CIBLE :
  //   l'INTENSE  — la mêlée, la charge : on tire vers 0, et vite.
  //   le SOUTENU — la marche, la colonne, la course : vers 0,45. On peut le
  //                tenir longtemps, mais on ne récupère pas en marchant.
  //   le REPOS   — tenir sa ligne, souffler : vers 1, et c'est le seul état
  //                qui remonte.
  //
  // LES TAUX SONT CALÉS SUR UN RYTHME, pas choisis : environ une minute de
  // mêlée pour tomber au seuil où l'on cherche à souffler, et une trentaine de
  // secondes pour repartir. C'est la respiration d'un match — des poussées
  // d'une minute, des accalmies d'une demi-minute — et c'est ce qu'on veut
  // voir. La marche seule se stabilise à 0,45, donc au-dessus du seuil : on
  // n'a jamais besoin de souffler d'avoir marché, seulement de s'être battu.
  const SOUFFLE_CIBLE = { intense: 0.02, soutenu: 0.45, repos: 1 };
  const SOUFFLE_TAUX  = { intense: 0.020, soutenu: 0.010, repos: 0.035 };
  const REGIME = {
    melee: "intense", assaut: "intense", contre: "intense",
    colonne: "soutenu", forme: "soutenu", coureur: "soutenu",
    deroute: "soutenu", repli: "soutenu", fuite: "soutenu",
    tient: "repos", arrive: "repos", commande: "repos", rentre: "repos",
  };

  // ---- ET TOUS N'ONT PAS LE MÊME FOND ---------------------------------------
  // Troisième déviation individuelle, indépendante des deux autres — et il faut
  // qu'elle le soit : le courage n'est pas l'endurance, et l'homme qui tient le
  // plus longtemps n'est pas forcément celui qui avance le premier. Trois
  // tirages séparés font trois populations qui se recoupent mal, et c'est de ce
  // recoupement imparfait que sortent les individus qu'on remarque — le brave
  // sans souffle, le poussif qui ne lâche jamais.
  //
  // Elle joue DANS LES DEUX SENS, ce qui est le propre du fond : celui qui en a
  // se vide moins vite ET se refait plus vite. D'où la division d'un côté, la
  // multiplication de l'autre — un seul chiffre, deux effets opposés, comme
  // dans un corps.
  const { fond } = window.BatailleHasard;     // de 0,6 à 1,4, dans les deux sens

  function souffler(h, dt) {
    const r = h.repos ? "repos" : (REGIME[h.etat] || "soutenu");
    const c = SOUFFLE_CIBLE[r];
    const f = h.fond || 1;
    const k = SOUFFLE_TAUX[r] * (r === "repos" ? f : 1 / f);
    h.souffle += (c - h.souffle) * k * dt;
  }

  // CE QUE VAUT UN HOMME À BOUT DE SOUFFLE. Jamais zéro — on ne veut pas d'un
  // homme qui cesse d'exister —, mais assez pour que ça se voie : à souffle nul
  // il frappe et se déplace à 45 % de ce qu'il vaut frais. C'est ce qui fait
  // qu'une charge de la vingtième minute n'est pas celle de la première.
  const vigueur = (h) => 0.45 + 0.55 * (h.souffle === undefined ? 1 : h.souffle);

  // ---- LE CERCLE SOCIAL — ET C'EST LUI QUI FAIT LE RYTHME -------------------
  // DIX MÈTRES, ET PAS CINQ. On se bat à portée de bras et l'on REGARDE bien
  // plus loin : le cercle du combat dit avec qui l'on en découd, celui-ci dit
  // ce que fait la rue. Deux rayons parce que ce sont deux perceptions, et les
  // confondre reviendrait à dire qu'un homme ne voit que ce qu'il touche.
  //
  // LA FEATURE EST ICI, et elle tient en une phrase : je suis beaucoup plus
  // enclin à souffler si je vois d'autres souffler — et SURTOUT SI CE SONT LES
  // ENNEMIS. C'est l'asymétrie qui compte. Voir les siens souffler est une
  // permission ; voir l'adversaire souffler est une GARANTIE, parce qu'un homme
  // qui reprend son vent ne vous charge pas dans la seconde. Il pèse donc
  // double.
  //
  // Ce que ça produit n'est écrit nulle part et c'est le but : des RESPIRATIONS.
  // Une poignée d'hommes s'arrête, leurs voisins le voient, les vis-à-vis le
  // voient mieux encore, et une portion de front entière tombe au ralenti pour
  // vingt secondes avant de repartir. Personne ne l'a ordonné, aucune horloge
  // ne le cadence : c'est un accord tacite entre gens qui n'ont plus de jambes.
  // C'est exactement ce qui se passe dans une mêlée réelle, et c'est ce qui fait
  // qu'une bataille a des temps forts au lieu d'être un régime continu.
  const RAYON_SOCIAL = 10;
  const SOUFFLE_BAS  = 0.35;   // en dessous, on cherche à souffler
  const SOUFFLE_REPRIS = 0.75; // au-dessus, on repart — hystérésis, comme ailleurs

  function repos(h, dt) {
    h.revoirRepos = (h.revoirRepos || 0) - dt;
    if (h.revoirRepos > 0) return h.repos;
    h.revoirRepos = oeil(h);
    // On repart dès qu'on a repris son vent, sans regarder personne : la
    // contagion sert à s'ARRÊTER, pas à traîner.
    if (h.repos) { if (h.souffle > SOUFFLE_REPRIS) h.repos = false; return h.repos; }

    let amis = 0, ennemis = 0;
    autour(h.x, h.y, RAYON_SOCIAL, (o) => {
      if (o === h || !o.repos || !pese(o)) return;
      const d = (o.x - h.x) ** 2 + (o.y - h.y) ** 2;
      if (d > RAYON_SOCIAL * RAYON_SOCIAL) return;
      if (o.camp === h.camp) amis++; else ennemis++;
    });
    // L'ennemi qui souffle vaut deux amis qui soufflent.
    const permission = amis + ennemis * 2;
    // Le seuil monte avec ce qu'on voit : seul, il faut être à bout ; entouré
    // de gens qui reprennent leur vent, on s'arrête bien avant. La trempe
    // décale le tout — celui qui a du cœur souffle plus tard.
    const seuil = SOUFFLE_BAS + Math.min(.4, permission * .06) - (h.trempe || 0) * .1;
    if (h.souffle < seuil) h.repos = true;
    return h.repos;
  }

  // CE QU'UN CORPS DONNE À SES HOMMES — le tableau qui remplace `humeur`,
  // et qui se lit ligne à ligne contre lui.
  const ECOLE_CORPS = {
    cranche:     { dressage: 0.70, vecu: 0.60, sourd: 0 },      // « ferme »
    gueux:       { dressage: -0.30, vecu: -0.20, sourd: 0.85 }, // « sourd »
    bleusailles: { dressage: -0.60, vecu: -0.70, sourd: 0 },    // « versatile »
    cole:        { dressage: 0.30, vecu: 0.20, sourd: 0 },
    vantre:      { dressage: 0.10, vecu: 0.00, sourd: 0 },
  };
  const ECOLE_GARDE = { dressage: 0.45, vecu: 0.25, sourd: 0 };
  const ECOLE = (opts, camp, quoi) => {
    if (camp === "garde") return ECOLE_GARDE[quoi];
    const e = ECOLE_CORPS[(opts && opts.corps) || ""];
    return e ? e[quoi] : (quoi === "sourd" ? 0 : -0.15);
  };

  function homme(camp, x, y, opts) {
    const arme = armeDe(camp, opts);
    // A. ON NE POSE PLUS UN HOMME DANS UN MUR. Ici et non chez les appelants :
    // l'anneau du Donjon, la grille des postes de garde, le déploiement de
    // l'assaut, l'escorte et le roi passent tous par cette porte-là, et aucun
    // d'eux n'a jamais lu le masque. Neuf hommes sur quinze de l'anneau étaient
    // posés dans les murs du Donjon Rouge et y restaient la nuit entière.
    const _p = degager(x, y);
    x = _p[0]; y = _p[1];
    const h = {
      debugId: "homme-" + (++S.prochainHommeDebug),
      camp, x, y, vx: 0, vy: 0,
      // CE QU'IL A DANS LES MAINS, tiré une fois et pour toute la nuit. On ne
      // ramasse pas l'arme d'un mort dans ce fichier — ce serait juste, et ça
      // ferait converger toute la ville vers la meilleure ligne du tableau,
      // c'est-à-dire vers l'homme unique dont on vient de sortir.
      arme,
      metier: (opts && opts.metier) || null,
      typeTroupe: (opts && opts.typeTroupe) || null,
      // `monte` seul désigne aussi les officiers à cheval, qui marchent avec
      // leur colonne. Une monture de combat est un autre fait physique.
      montureCombat: !!(opts && opts.montureCombat),
      // OÙ SON FER EST (`fx,fy`) ET OÙ IL VOUDRAIT QU'IL SOIT (`cx,cy`). Le
      // second se pose librement — par la marche, par la cible qu'on choisit —,
      // le premier ne fait que le rattraper au poids de l'arme (`tourner`). Ce
      // n'est plus un vecteur d'affichage : c'est lui que `frapper` lit pour
      // savoir si le coup peut partir, et pour savoir d'où on le reçoit.
      fx: 0, fy: 0, cx: 0, cy: 0, w: 0,
      // Ce qu'il fait RÉELLEMENT sous les pieds, en mètres par seconde. Les
      // allures (`MARCHE`, `CHARGE`, `FUITE`) ne sont que des consignes ; cette
      // valeur-ci les rattrape à `ACCEL` près, et elle part de l'arrêt.
      vit: 0, pousse: false,
      // La circulation locale laisse une trace : un homme arrêté peut céder
      // latéralement devant un allié qui avance, davantage devant son chef.
      cedePassageA: -Infinity, cedePour: null, cedePourChef: false, cedeDistance: 0,
      immobileDepuis: 0,
      // DE QUELLE MAIN IL TIENT. Tiré une fois, à la naissance, comme l'arme :
      // une main qui changerait d'un battement à l'autre ferait sauter le fer
      // d'un côté à l'autre du corps vingt fois par seconde. Un sur dix est
      // gaucher — et c'est le tirage qui le dit, donc la même bataille rejouée
      // rend les mêmes gauchers.
      //
      // C'est un fait d'AFFICHAGE et rien d'autre : le fer part du poing, non
      // du nombril, et la ligne le montrait sortir du centre de la poitrine.
      // Rien dans la mécanique ne le lit — l'allonge, le secteur et le coup
      // restent mesurés depuis l'homme, comme avant.
      gaucher: R() < .1,
      trempe: trempe(),
      // Le souffle part plein, et il ne repartira jamais tout à fait de là.
      souffle: 1, repos: false,
      // ET ILS NAISSENT DÉSYNCHRONISÉS. Sans ces deux tirages, les deux mille
      // cinq cents décident tous au premier battement, et l'on repart pour une
      // armée qui pense d'un seul bloc pendant les trois premières secondes —
      // c'est-à-dire pendant la mise en place, qui est justement ce qui donne
      // le ton du reste.
      vivacite: vivacite(), fond: fond(), souplesse: souplesse(),
      // CE QUE CE CORPS-LA A APPRIS — pour la couche 1. Sans eux, les six
      // cents hommes de la mesure avaient tous `dressage = 0` et
      // `vecu = 0` : des acquis identiques, donc le meme geste pour tout
      // le monde au meme instant. L'uniformite qu'on prenait pour un
      // emballement etait en partie une absence de variete.
      //
      // La GARNISON est une troupe payee, dressee et qui a deja tenu un
      // seuil ; l'ASSAUT est ce qu'on a ramasse. Chacun tire ensuite sa
      // deviation autour de la sienne, comme les cinq autres.
      // ---- CE QUE `humeur` DISAIT, ÉCRIT DANS LA COUCHE 1 ---------------
      // `humeur` était un mot qui commandait trois planchers de morale :
      // « ferme » ne descend jamais sous un seuil, « sourd » ne rompt
      // jamais, « versatile » rompt tôt et revient vite. Trois exceptions
      // câblées dans `survie()`, chacune avec sa constante.
      //
      // Les trois se disent dans la couche 1, et PAS AU MÊME ENDROIT —
      // c'est même ce qui prouve qu'elles n'étaient pas la même chose :
      //
      //   FERME     → du dressage et du vécu. Cranche tient parce que ses
      //               hommes ont appris à tenir. Plus de plancher.
      //   SOURD     → une fermeture du CANAL SOCIAL, pas un courage —
      //               donc `sourd`, sur la perception.
      //   VERSATILE → un FOND court : il rompt tôt ET se reprend vite,
      //               une seule grandeur pour deux effets opposés.
      //
      // Le corps donne le milieu, l'homme donne l'écart.
      dressage: ECOLE(opts, camp, "dressage") + trempe() * 0.35,
      vecu:     ECOLE(opts, camp, "vecu") + trempe() * 0.35,
      sourd:    ECOLE(opts, camp, "sourd"),
      revoir: oeil(), revoirRepos: oeil(),
      // CINQUIÈME DÉVIATION — LA CARCASSE. C'était le dernier endroit du modèle
      // où deux hommes étaient interchangeables : le courage, l'œil,
      // l'endurance et la souplesse étaient déjà tirés en cloche, la vie non.
      // Ce que ça coûtait ne se voit pas sur une moyenne, ça se voit sur les
      // BORDS — sans dispersion, aucun homme ne survit à un coup auquel son
      // voisin succombe, donc ni miraculé ni homme de verre, et une ligne
      // d'hommes identiques tombe d'un bloc.
      // LA BOITE AUX LETTRES DE LA COUCHE 1. Elle recoit les stimuli entre
      // deux coups d'oeil de son proprietaire, et se vide quand il les lit.
      // Sans elle, un coup recu entre deux reveils n'aurait jamais eu lieu.
      // ⚠ PAS `corps` : LE CHAMP EXISTE DEJA et c'est le corps de TROUPE
      // (« cole », « gueux »). L'ecraser a fait planter le four au premier
      // battement — meme faute que `semer` ce matin, et c'est la deuxieme
      // fois qu'une IIFE de six mille lignes cache une collision de nom.
      recu: [], l1: null, l1etat: null, revoirCorps: 0,
      // Un danger sans combattant (feu, bête, éboulement) doit entrer dans la
      // même perception sans fabriquer un faux ennemi. Déclarés à la naissance
      // pour garder une forme d'objet stable, ces cinq champs expirent seuls.
      menaceExterieure: 0, menaceX: 0, menaceY: 0, menaceGenre: null,
      menaceJus: -Infinity,
      ruptureCause: null,
      // La déroute n'est pas un vecteur recalculé à chaque image. Au moment où
      // il rompt, chaque homme choisit une conduite et un cap depuis sa propre
      // graine stable ; ces champs en gardent l'inertie.
      fuiteStrategie: null, fuiteDepuis: -Infinity, fuiteSeverite: 0,
      fuiteDx: 0, fuiteDy: 0, fuiteAngle: 0, fuiteExterieure: false,
      fuiteGroupeX: null, fuiteGroupeY: null, fuiteGroupeVuA: -Infinity,
      fuiteGroupeAngle: 0, fuiteGroupeRayon: 0,
      // La décision gagnante, écrite À L'ENDROIT où elle gagne. Le survol ne
      // la reconstitue pas depuis `etat`, qui confond tenir son poste, attendre
      // du renfort et reprendre son souffle. `pensees` garde les quatre vrais
      // changements précédents sans enregistrer vingt fois la même seconde.
      pensee: { action: "tenir ma place", raison: "rien ne m'a encore fait bouger",
                systeme: "déploiement", depuis: 0 },
      pensees: [],
      // L'intérieur est un espace, pas une coordonnée cachée sous le toit.
      // `null` signifie la rue ; un index signifie que l'homme a franchi la
      // porte de ce bâtiment. Deux espaces différents ne se voient ni ne se
      // frappent, même si leurs points de rendu se touchent sur le plan.
      interieur: null, entreDepuis: null, pointInterieur: null,
      sortieBatiment: null,
      passageEtroit: false,
      rapportMission: null, rapports: [],
      rebelle: false, rebelleChef: false, batimentRebelle: null,
      // Une perception n'est inscrite que lorsqu'un de ses éléments utiles
      // change. On garde ainsi TOUTE la chronologie sémantique sans écrire
      // vingt photographies identiques par seconde et par homme.
      perceptions: [], perceptionCle: null, perceptionsOubliees: 0,
      // Instruments de dynamique, declares a la naissance.
      enMesure: false, mesureDepuis: 0, tempsEnMesure: 0,
      boutsMesure: 0, dernierBout: 0, boutMax: 0, degagement: 1,
      // `-1` ferait passer tout homme neuf pour un frappeur pendant les quatre
      // premières secondes. L'absence de coup doit rester hors de toute fenêtre.
      coupsTentes: 0, coupsPortes: 0, dernierCoup: -Infinity,
      // LA COUCHE 2 ET SA TRACE. `l2` est ce que `2-reflexion.js` a rendu au
      // dernier coup d'oeil ; `l2etat` est ce que la couche ne tient pas
      // elle-meme (l'horloge d'attente), tenu par `bataille/reflexion-adapt.js`
      // comme `l1etat` l'est par `corps-adapt.js`.
      // `conduit` est LE SEUL CHAMP QUE LA PEINTURE POURRA LIRE pour distinguer
      // un homme que sa stack conduit d'un homme que la cascade conduit : un
      // mot du meme genre que `etat`, pose au meme rythme, et que personne ne
      // lit encore. Voir la trace, tout en bas de `reflexion-adapt.js`.
      l2: null, l2etat: null,
      conduit: null, conduitDepuis: 0, conduitBras: null, conduitPhrase: null,
      conduitEtat: null,
      pv: 0, pvMax: 0, etat: "colonne", cible: null,
      prochain: entre(0, arme.cadence),         // les coups ne tombent pas en chœur
      escouade: (opts && opts.escouade) || 0,
      aile: (opts && opts.aile) || 0,
      // ⚠ LE POSTE SE DÉGAGE AUSSI, et l'oublier annulerait tout : les appelants
      // écrivent `{poste: [px, py]}` avec le point d'AVANT dégagement. L'homme
      // serait poussé hors du mur puis y retournerait de lui-même, puisque
      // tenir son poste veut dire y revenir.
      poste: (opts && opts.poste) ? degager(opts.poste[0], opts.poste[1]) : null,
      chef: !!(opts && opts.chef),
      capitaine: !!(opts && opts.capitaine),    // il porte la bannière de l'aile
      tete: !!(opts && opts.tete),              // il décide, et il ne se bat pas
      // LE NOM NE CHANGE RIEN À CE QU'IL ENCAISSE, et il faut que ça reste
      // vrai : le jour où un nommé a des pv à lui, on a ouvert la porte des
      // champions et de tous les cas particuliers qui suivent. Un nom ne
      // change que ce qu'on ÉCRIT quand il tombe.
      nom: (opts && opts.nom) || null,
      // Le mot court qu'on écrit sous le nom sur le plan. Il ne change rien non
      // plus : il dit seulement CE QU'EST celui qu'on vient de retrouver à
      // l'œil, ce qu'un nom seul ne dit jamais.
      role: (opts && opts.role) || null,
      corps: (opts && opts.corps) || null,
      // HORS DE LA CHAÎNE. Il est du camp de l'assaut, il occupe une place, il
      // encaisse les coups — mais il n'appartient à aucune escouade et à aucune
      // aile. Sans ce drapeau, les quarante hommes de la charrette gonflent
      // l'effectif de la première escouade du premier corps, qui ne rompt donc
      // plus jamais, et la force de sa première aile, qui ne se replie plus.
      // C'est exactement le piège que la tête avait déjà tendu une fois.
      hors: !!(opts && opts.hors),
      roi: !!(opts && opts.roi),
      porte: null,                              // l'ordre qu'un coureur emporte
      chez: null,                               // à quelle escouade il court
      // SA PLACE EN TRAVERS DE LA RUE, en fraction de la demi-largeur. Ce
      // n'était qu'un signe — −1 ou +1 —, donc deux files et rien entre elles.
      // On tient toujours SA droite (le signe est tiré une fois pour toutes),
      // mais on l'occupe sur toute sa profondeur : le mur, le milieu, et ce
      // qu'il y a entre. La largeur vraie est lue au pied, dans `soldat`.
      but: null, trace: null, avance: 0,
      // LA MESURE DE LA RUE SOUS SES PIEDS, en cache — voir `demiLibre`.
      // ⚠ DÉCLARÉE ICI, ET C'EST TOUT LE SUJET. Posés après coup sur l'objet,
      // ces trois champs changent sa forme cachée en cours de partie : le
      // moteur a été mesuré DIX FOIS plus lent avec eux ajoutés à la volée
      // (337 ms de calcul par seconde de bataille, contre 32). Un champ d'homme
      // se déclare à la naissance, sans exception.
      mesureX: 0, mesureY: 0, mesureDemi: -1,
      // Le rail jusqu'à la porte, sa clef, et où il en est dessus.
      rail: null, railClef: null, railS: 0,
      cote: (R() < .5 ? -1 : 1) * (0.18 + 0.82 * R()),
      // SA PLACE DANS SA VINTAINE. Elle ne contient aucun point du monde :
      // seulement une file et un recul par rapport au vintenar. Le chef porte
      // le chemin ; cet homme-ci porte la relation qui lui permet de suivre.
      formation: -1, placeFormation: null, formationS: 0,
      chefFormation: false,
    };
    // La carcasse se tire APRÈS, une fois pour toutes. `pvMax` est la seule
    // référence à laquelle un seuil ait le droit de se comparer.
    h.pvMax = window.BatailleMesures.pvDUnHomme(opts && opts.pvMoyen);
    h.pv = h.pvMax;
    // CE QU'IL VEUT, ET QU'IL APPORTE DE CHEZ LUI. Deux traits tirés une fois,
    // jamais recalculés : sa convoitise et sa docilité. Ils remplacent les deux
    // tableaux par humeur — `APPETIT` et `SILENCE` —, où tous les hommes d'un
    // corps voulaient exactement la même chose à la troisième décimale près.
    // L'humeur décale maintenant le centre au lieu de dicter la valeur, si bien
    // qu'un homme de Cranche peut être plus cupide qu'un homme de Petit Wend :
    // rare, et possible. Voir `survival-stack/4-envie.js`.
    h.envie = window.Envie.temperament((opts && opts.corps) || null,
                                       () => cloche(-1, 1));
    return h;
  }

  /** L'ordre de bataille. Trois cents contre une garnison, et un verrou. */
  function dresser(nomPorte, n) {
    semerGraine();               // la même bataille, à chaque fois qu'on la dresse
    const porte = nomPorte ? repereDuPlan(nomPorte, "porte") : portes()[3];
    const donjon = repereDuPlan("Le Donjon Rouge", "donjon");
    if (!porte || !donjon) throw new Error("ni porte ni donjon dans ce plan");
    S.entree = porte; S.objectif = donjon;

    S.hommes = []; S.prochainHommeDebug = 0;
    S.escouades = []; S.formations = []; S.routesFormation = new Map();
    S.deploiements = new Map(); S.carteCommandantId = null;
    S.ratissages = new Map(); S.prochainRatissage = 0;
    S.ailes = []; S.tetes = []; S.figures = [];
    S.temps = 0; S.reste = 0;
    // L'HORLOGE DU SILLAGE REPART AVEC LE RESTE. Elle se compare à `temps`, qui
    // vient d'être remis à zéro : laissée à sa valeur, elle attendrait que la
    // nouvelle bataille rattrape l'ancienne — quatre minutes sans une seule
    // trace, sans que rien ne le dise. C'est la même leçon que le roi versé et
    // que le bâti déjà pillé, apprise une troisième fois.
    S.sillageDu = 0;
    // Les comptes de l'image précédente aussi : gardés d'une bataille à
    // l'autre, ils feraient saigner les six chiffres au premier battement de
    // la suivante — cinq cents hommes « perdus » qui sont ceux d'avant.
    deboutAvant.clear(); deboutQuand.clear(); S.surligne = null;
    // LES DEUX HORLOGES REPARTENT AVEC LE RESTE. Une nuit où le roi a versé
    // laissait `arret` posé : la cuisson suivante commençait par une armée déjà
    // rompue, sans qu'une seule ligne le dise. C'est la même leçon que le bâti
    // déjà pillé, trente lignes plus bas, et elle se paie au même prix.
    S.roi = null; S.arret = null; S.messagers = []; S.anneauOuvert = false;
    S.conseil = { averti: 0, tenir: 0, ouvrir: 0, tranche: false };
    // LES ANNALES REPARTENT ICI, ET AVANT LES CORPS. Sinon une seconde cuisson
    // n'écrit plus rien — et surtout, tout ce que la mise en place a à dire
    // (l'humeur des six corps) serait effacé juste après avoir été écrit.
    S.annales = []; S.dits.clear();

    // SIX CORPS, ET PLUS UN SEUL BLOC. C'était trois cents hommes en colonne
    // par six ; ce sont maintenant six foules qui vont dans la même direction
    // pour six raisons différentes, et deux d'entre elles n'obéissent à
    // personne. Tout ce que la bataille produira d'intéressant vient de là.
    //
    // Des escouades de vingt : l'unité qui PENSE (un chemin par escouade, pas
    // par homme). Des ailes de cinq escouades : l'unité qu'on COMMANDE. Et
    // désormais une chaîne par corps — parce que l'intérêt n'est pas d'avoir
    // une chaîne qui marche, c'est d'en avoir six qui ne s'accordent pas.
    const PAR = PAR_ESC;
    const TOTAL = CORPS.reduce((s, c) => s + c.hommes, 0);
    // Un effectif d'essai vaut une échelle : `pas(90)` et les vieux appels à
    // trois cents hommes continuent de marcher, et ils disent maintenant
    // quelque chose de juste — trois cents hommes, c'est un trente-deuxième
    // de cette armée-là.
    if (n) S.ECHELLE = n / TOTAL;

    // UN VERROU PAR PORTE ENGAGÉE, ET UN SEUL. Deux corps qui entrent par la
    // même porte frappent le MÊME battant : sans cette mise en commun, chacun
    // aurait le sien, la porte tomberait deux fois, et le compte des sept
    // hommes de front n'aurait plus de sens.
    // Le repère de la porte PRINCIPALE, pour tout ce qui se place par rapport
    // à elle sans appartenir à un corps : les figures, le roi sur sa charrette,
    // les habitants qui ont une adresse. Chaque corps aura le sien, qui masque
    // celui-ci dans sa boucle.
    const axeP = axeDe(porte);
    const en = (recul, cote) => [porte.x + axeP.nx * recul + axeP.tx * cote,
                                 porte.y + axeP.ny * recul + axeP.ty * cote];

    // LA VILLE SE REBÂTIT ENTRE DEUX BATAILLES. Le bâti est chargé une fois et
    // gardé — mais son ÉTAT appartient à la bataille, pas au décor. Sans cette
    // remise à zéro, la seconde cuisson trouvait quarante-cinq mille maisons
    // déjà forcées : plus rien à piller, donc plus personne qui s'arrête, donc
    // un déroulé entièrement différent. La vérification l'a dit tout de suite
    // — mille trente-huit mètres d'écart et deux millions d'états faux — et
    // c'est précisément ce qu'elle est là pour dire : un fichier cuit qui ne se
    // rejoue pas ne se vérifie pas, et ne se corrige donc jamais.
    if (S.bati) {
      S.bati.etat.fill(0);
      if (S.bati.fouille) S.bati.fouille.fill(0);
      if (S.bati.occupation) S.bati.occupation.fill(0);
      if (S.bati.feux) S.bati.feux.clear();
      S.bati.forcees = 0; S.bati.brulees = 0; S.bati.butin = 0;
    }

    S.verrous = [];
    const verrouDe = (rep) => {
      let v = S.verrous.find((w) => w.nom === rep.nom);
      if (!v) {
        // ⚠ ESSAI — LA PORTE ENGAGÉE DÉJÀ OUVERTE. Deux minutes de hache avant
        // que la mêlée commence, c'est deux minutes à ne rien pouvoir observer
        // quand ce qu'on règle est le corps à corps. `PORTE_OUVERTE_ESSAI`
        // ouvre la porte du four — celle-là seule, les trois autres restent
        // fermées et servent de témoin.
        //
        // À REMETTRE À `false` : sans elle, une bataille cuite raconte un
        // assaut qui n'a jamais eu à forcer quoi que ce soit.
        const ouverte = PORTE_OUVERTE_ESSAI && rep.nom === porte.nom;
        // L'USURE FIXE LE `max`, PAS SEULEMENT LES POINTS — et c'est la seule
        // façon de l'écrire qui ne mente pas. Baisser `pv` en gardant un `max`
        // de neuf mille ferait annoncer « elle commence à céder » à la seconde
        // zéro, avant qu'un homme l'ait touchée : le seuil est à la MOITIÉ, et
        // la moitié de quoi, sinon de ce que cette porte-là tient ? Une porte
        // abîmée est une porte entière en moins bon bois — elle se fend au
        // milieu de ce qu'elle vaut, comme les autres.
        const usure = USURE[rep.nom] || 1;
        const pv = Math.round(VERROU_PV * usure);
        S.verrous.push(v = { nom: rep.nom, porte: rep,
                           pv: ouverte ? 0 : pv, max: pv, usure,
                           etat: ouverte ? "ouvert" : "ferme",
                           par: ouverte ? "essai" : null,
                           x: rep.x, y: rep.y, frappeurs: 0 });
        // ON LE DIT AU DÉPART, comme on dit qu'un corps est sourd. Sans cette
        // ligne, on relit au matin une porte tombée quatre fois trop vite et
        // l'on cherche le défaut dans le four, qui n'y sera pour rien.
        if (usure !== 1)
          noter("porte-abimee", rep.x, rep.y,
                { clef: "abimee:" + rep.nom,
                  dit: { porte: rep.nom, part: Math.round(usure * 100) } });
      }
      return v;
    };

    for (const c of CORPS) {
      // La porte de CE corps — la sienne s'il en a une, celle du four sinon.
      const rep = c.porte ? repereDuPlan(c.porte, "porte") : porte;
      c._entree = rep || porte;
      c._verrou = verrouDe(c._entree);
      const { nx, ny, tx, ty } = axeDe(c._entree);
      const en = (recul, cote) => [c._entree.x + nx * recul + tx * cote,
                                   c._entree.y + ny * recul + ty * cote];
      const places = poserCorps(c, c._entree);
      const e0 = S.escouades.length, a0 = S.ailes.length;
      const nEsc = Math.ceil(places.length / PAR);
      // LE NOMBRE D'AILES SE PREND SUR L'EFFECTIF PLEIN, JAMAIS SUR L'ÉCHELLE.
      // C'est le piège de la maquette, et il est silencieux : à un trente-
      // deuxième, un corps ne fait plus que quatre escouades, donc UNE aile —
      // et comme la réserve n'est ordonnée qu'aux ailes autres que la première,
      // plus aucune tête n'ordonnait quoi que ce soit. Quatre cents secondes de
      // bataille, six têtes, zéro ordre : le mécanisme entier était mort, et
      // rien ne le disait puisque la géométrie, elle, restait juste.
      //
      // L'échelle doit donc préserver la STRUCTURE autant que les distances :
      // même nombre d'ailes qu'à effectif plein, avec moins de monde dedans.
      const nAile = Math.min(nEsc, ailesDe(c));

      // L'ORDRE DE DÉPART EST CELUI QUE LA DOCTRINE DONNERAIT, et ce n'est pas
      // un détail de confort : les ailes commençaient toutes en « avancer », si
      // bien que la première délibération de chaque tête ordonnait la réserve —
      // vingt lignes de « tenir » à la seconde zéro, toutes identiques, en tête
      // du document. Or une réserve, au déploiement, EST déjà la réserve.
      // Personne ne le lui ordonne ; c'est là qu'on l'a mise.
      //
      // Un ordre ne vaut une ligne que lorsqu'il CHANGE quelque chose.
      // ET LA CONSIGNE PASSE AVANT LA DOCTRINE, au premier pas comme au
      // dernier : c'est ce qu'on a dit à ce corps-là avant d'entrer dans la
      // nuit, et aucune tête n'a besoin de le répéter.
      for (let a = 0; a < nAile; a++)
        S.ailes.push({ id: a0 + a, corps: c.id, rang: a,
                     ordre: (a === 0 && c.consigne)
                       ? ordreDe(c.consigne.verbe, c.consigne)
                       : ordreDe(a === 0 ? "avancer" : "tenir",
                                 { intention: a === 0 ? "entrer" : "couvrir" }),
                     capitaine: null, releve: 0,
                     banniere: { debout: false, x: porte.x, y: porte.y } });
      // LE PARTAGE DES ESCOUADES SUIT LE NOMBRE D'AILES RÉEL, pas la division
      // à effectif plein. `e / ESC_PAR_AILE` ne marche qu'à l'échelle 1 : à un
      // vingtième, six escouades ne rempliraient que les deux premières ailes
      // sur six, et les quatre autres — vides — auraient une force nulle, donc
      // un ordre de repli perpétuel. Une aile sans homme n'est pas une réserve,
      // c'est un trou dans la chaîne.
      const aileDeLEsc = (e) => a0 + Math.min(nAile - 1,
                                              Math.floor(e * nAile / nEsc));
      for (let e = 0; e < nEsc; e++) {
        const aile = aileDeLEsc(e);
        const rangAile = S.escouades.filter((x) => x.aile === aile).length;
        const u = creerFormation("assaut:" + (e0 + e), "assaut",
                                 "aile:" + aile, c.forme);
        S.escouades.push({ id: e0 + e, corps: c.id, entree: c._entree,
                         aile, rangAile,
                         trace: null, phase: "porte",
                         // Le cadre est ce que conduit le vintenar. Le chemin,
                         // le cap et l'allure vivent ici une fois ; les hommes
                         // n'en reçoivent que leur place relative.
                         formation: u.n, cadre: u.cadre,
                         // Elle part avec l'ordre de son aile, sinon la
                         // transmission croirait avoir un retard à rattraper
                         // avant même que la bataille ait commencé.
                         ordre: S.ailes[aileDeLEsc(e)].ordre,
                         attend: null, coureur: null,
                         // L'ordre qu'on tient en réserve d'un déclencheur, et
                         // le silence qui monte quand plus rien n'arrive. Les
                         // deux se lisent à chaque pas, et c'est de là que sort
                         // tout ce qu'un chef finit par décider de lui-même.
                         attente: null, depuis: 0, humeur: c.humeur,
                         // Le dernier ordre d'aile qu'on a pris en charge —
                         // confié à un homme ou perdu faute d'homme. Il vaut
                         // pour reçu du point de vue de la tête, qui n'a aucun
                         // moyen d'apprendre le contraire.
                         vu: null,
                         // Le sourd l'est dès le départ, et pour toujours.
                         // LA SURDITÉ VIENT DE L'ÉCOLE DU CORPS, pas du mot
                         // `humeur` : c'est le MÊME `sourd` que la couche 1
                         // lit sur la perception. Il n'y a aucune raison
                         // qu'un homme soit sourd aux signes par un chemin et
                         // son escouade sourde aux ordres par un autre — deux
                         // pièces pour un fait, c'est deux modèles.
                         sourde: ECOLE({ corps: c.id }, "assaut", "sourd") > 0.5,
                         sourd_ne: ECOLE({ corps: c.id }, "assaut", "sourd") > 0.5 });
        u.escouade = e0 + e;
      }

      for (let i = 0; i < places.length; i++) {
        const e = Math.floor(i / PAR);
        const dans = i % PAR;
        const h = homme("assaut", places[i].x, places[i].y,
                        { escouade: e0 + e, aile: aileDeLEsc(e),
                          corps: c.id, humeur: c.humeur,
                          chef: dans === 0 });
        affecterFormation(h, S.formations[S.escouades[e0 + e].formation],
                          dans, h.chef);
        // CHACUN PORTE SA PORTE. On pourrait la retrouver par son corps à
        // chaque pas ; on la lui accroche une fois, parce que c'est lu vingt
        // fois par seconde et par homme, et qu'une indirection de plus à ce
        // rythme-là se paie en secondes de cuisson.
        h.entree = c._entree; h.verrou = c._verrou;
        // Un assaillant a un poste, lui aussi : celui d'où il est parti. C'est
        // là qu'il revient quand on lui ordonne de tenir — sans ça, « tenir »
        // ne voudrait rien dire pour quelqu'un qui n'a jamais rien gardé.
        h.poste = [h.x, h.y];
        S.hommes.push(h);
      }

      // LA TÊTE NE SE BAT PAS, et c'est ce qui la rend intéressante : son seul
      // acte est de décider. Elle est quand même un CORPS — donc elle est dans
      // le sac, donc elle est quelque part, donc le jour où la ligne cède elle
      // est joignable. Elle se tient au rang que son caractère lui donne :
      // Cole au troisième, dans sa propre masse, ce qui ne l'empêche pas de
      // n'avoir jamais frappé un coup.
      const [hx, hy] = en(c.recul + (c.rangTete || 0) * 1.4, c.cote);
      const t = homme("assaut", hx, hy,
                      { tete: true, corps: c.id, nom: c.nom, humeur: c.humeur,
                        role: "chef de corps" });
      t.entree = c._entree; t.verrou = c._verrou;
      t.etat = "commande";
      t.poste = [t.x, t.y];
      t.decide = cloche(2, 5);
      S.hommes.push(t);
      S.tetes.push(t);

      // UN COMPORTEMENT QUI N'ÉMET RIEN N'EXISTE PAS — c'est la règle du
      // module, et l'humeur d'un corps la casse en silence. Un corps sourd ne
      // produit AUCUN `escouade-sourde` : ses escouades sortent de la
      // transmission avant d'y entrer, donc rien ne signale que deux mille
      // hommes n'écouteront jamais un ordre. À la relecture on verrait une tête
      // qui commande et des hommes qui n'obéissent pas, sans jamais savoir
      // pourquoi. On le dit une fois, au départ, et c'est assez.
      if (c.humeur)
        noter("corps-" + c.humeur, t.x, t.y,
              { clef: "humeur:" + c.id,
                dit: { corps: c.id, chef: c.nom, hommes: places.length,
                       humeur: c.humeur } });
    }

    // LE CAPITAINE SE NOMME APRÈS COUP, ET UN PAR AILE. Il était désigné par
    // un modulo sur l'indice — ce qui ne vaut que si chaque aile a exactement
    // cinq escouades pleines. Dès que l'échelle amincit les escouades, le
    // modulo tombe à côté et des ailes entières se retrouvent sans bannière,
    // c'est-à-dire hors de la chaîne, sans que rien ne le dise. On prend donc
    // le premier homme de l'aile qui n'est pas déjà chef d'escouade : un
    // soldat qu'on a monté en grade, pas un être à part. Il porte la bannière,
    // ce qui veut dire qu'il la fait tomber en tombant.
    for (const h of S.hommes) {
      if (h.camp !== "assaut" || h.tete || h.hors || h.chef) continue;
      const a = S.ailes[h.aile];
      if (!a || a.capitaine) continue;
      h.capitaine = true;
      // LE CENTENAR, ET IL EST MONTE. C'est ce qui rend l'echelon de cent
      // atteignable : un coureur peut le trouver et le rejoindre, parce qu'il
      // depasse la troupe et qu'il vient au-devant. Sans lui, la centaine est
      // une abstraction et le cout d'un ordre precis — un coureur par centaine
      // — n'a aucun objet. Voir `docs/bataille/roster/`.
      h.monte = true;
      a.capitaine = h;
      a.banniere = { debout: true, x: h.x, y: h.y };
    }

    // La garnison. Elle ne sort pas : elle tient la porte, puis la cour du
    // donjon. Un défenseur qui charge en rase campagne n'aurait aucune raison
    // de le faire, et c'est le genre de bêtise qu'on n'écrit pas.
    //
    // ET IL Y EN A UNE PAR PORTE, forcément — mais elles ne sont pas égales, et
    // c'est là que se joue le sort de la ville. La ville a une garnison, pas
    // quatre : ce qu'on met à une porte, on ne l'a plus à l'autre. Deux cents
    // hommes à celle qu'on croit menacée, cent aux autres. Celle qui cède la
    // première n'est pas celle qu'on frappe le plus fort, c'est celle qu'on a
    // le moins gardée — et personne ne l'a décidé, c'est tombé du compte.
    //
    // LE TIRAGE AU SORT EST DANS CE CHIFFRE, et c'est tout ce qu'il en reste :
    // on a tiré qui tient et qui assaille, donc la moitié des hommes de la
    // Gadoue défend une porte qu'elle n'a jamais gardée pendant que les gens
    // du port l'attaquent en connaissant chaque ruelle. On ne le simule pas —
    // on n'en a pas besoin, il suffit de ne pas l'oublier en le racontant.
    for (const v of S.verrous) {
      const premiere = v.porte.nom === porte.nom;
      const n = garnison(premiere ? 200 : 100);
      const { nx, ny, tx, ty } = axeDe(v.porte);
      const unitesPoste = [];
      for (let i = 0; i < n; i++) {
        const groupe = Math.floor(i / PAR_ESC), dans = i % PAR_ESC;
        if (!unitesPoste[groupe])
          unitesPoste[groupe] = creerFormation(
            "garde:" + v.porte.nom + ":" + groupe,
            "garde", "poste:" + v.porte.nom, "ligne");
        const c = (i % 9 - 4) * 1.0, r = Math.floor(i / 9) * 1.3;
        const px = v.porte.x - nx * (8 + r) + tx * c;
        const py = v.porte.y - ny * (8 + r) + ty * c;
        const h = homme("garde", px, py,
                        { poste: [px, py],
                          // Le sergent du poste est au milieu du premier rang.
                          // Il est déclaré mort dans la première minute et
                          // c'est tout le personnage : ses trois demandes de
                          // renfort sont datées, écrites, et personne ne les a
                          // lues. DANS UN EXERCICE IL NE MEURT PAS — on le met
                          // de côté, vivant, et il regarde prendre son poste
                          // pendant une heure. C'est une bouche à faire parler
                          // dès le lendemain, et il existe déjà dans l'état.
                          nom: (premiere && i === 4) ? "le sergent Waltyr Poix" : null,
                          role: (premiere && i === 4) ? "sergent du poste" : null });
        // Le sergent nommé conduit la première vintaine de la Gadoue. Ailleurs
        // et dans les groupes suivants, le premier homme est le chef anonyme.
        const chef = (premiere && groupe === 0) ? i === 4 : dans === 0;
        affecterFormation(h, unitesPoste[groupe], dans, chef);
        h.entree = v.porte; h.verrou = v;
        S.hommes.push(h);
      }
      // ET UN HOMME QU'ON PEUT ENVOYER. Il se tient douze mètres en dedans, dos
      // à la porte : un guet ne prend pas son élan au milieu de ceux qui la
      // frappent. Il ne fait rien de la nuit si sa porte tient — et s'il tombe
      // avant qu'on ait songé à lui, ce poste-là n'aura envoyé personne.
      const [mx, my] = dehors(v.porte);
      const m = homme("garde", v.porte.x - mx * 12, v.porte.y - my * 12, {});
      m.poste = [m.x, m.y];
      m.entree = v.porte; m.verrou = v;
      m.messager = false; m.parti = 0;
      v.messager = m;
      S.hommes.push(m);
    }
    // L'anneau du Donjon : trois cents hommes à l'échelle 1, six rangs
    // concentriques. Il ne
    // se resserre que si Coutre l'ordonne, et Coutre ne l'ordonne jamais à
    // temps — resserrer veut dire des torches, et une torche est une dépense.
    const nAnneau = garnison(300);
    const unitesAnneau = [];
    for (let i = 0; i < nAnneau; i++) {
      const groupe = Math.floor(i / PAR_ESC), dans = i % PAR_ESC;
      if (!unitesAnneau[groupe])
        unitesAnneau[groupe] = creerFormation(
          "garde:donjon:" + groupe, "garde", "poste:donjon", "anneau");
      const a = (i / nAnneau) * Math.PI * 2, r = 26 + (i % 6) * 2.2;
      const px = donjon.x + Math.cos(a) * r, py = donjon.y + Math.sin(a) * r;
      const h = homme("garde", px, py, { poste: [px, py] });
      affecterFormation(h, unitesAnneau[groupe], dans, dans === 0);
      S.hommes.push(h);
    }
    for (const h of S.hommes) if (h.camp === "garde") h.etat = "tient";

    // ---- CEUX QUI NE SE BATTENT PAS ---------------------------------------
    // Un roi porté sur une charrette, quatre personnes enfermées dans un
    // château, et huit habitants qui ont une adresse. Aucun n'est simulé : ce
    // sont des repères humains, posés pour que les faits aient quelqu'un sur
    // qui tomber. « La bannière de l'aile ouest tombe » est une donnée ;
    // « elle tombe à trente pas de chez Nonne la lavandière » est une scène.
    // `role` est le mot court qui s'écrit SUR LE PLAN, sous le nom : « châtelain »,
    // « sage-femme ». `dit` reste la phrase, pour la relecture. Sans ce mot, une
    // figure et un capitaine d'escouade portent exactement la même marque à
    // l'écran, et l'œil ne sait pas lequel des deux commande quelque chose.
    const fig = (camp, p, nom, role, dit) =>
      S.figures.push({ camp, x: p[0], y: p[1], nom, role, dit });
    const dans = (r, c) => en(-r, c);          // vers l'intérieur des murs

    // LE ROI EST UN CORPS, ET C'EST TOUTE LA DIFFÉRENCE. Il était une figure —
    // c'est-à-dire un nom peint sur le plan, que rien ne pouvait atteindre. Or
    // « s'il tombe, tout s'arrête » n'est une règle que si quelque chose peut
    // le faire tomber. Il entre donc dans le sac, avec ses hommes autour, à
    // l'endroit exact par lequel une armée qui rompt s'en retourne.
    //
    // L'escorte suit l'échelle, elle : c'est de l'assaut. La garnison ne la
    // suit pas parce que ce sont des postes tenus un par un ; quarante hommes
    // en cercle autour d'une charrette sont une masse, et une masse se divise.
    {
      const [rx, ry] = en(ROI_RECUL, 20);
      S.roi = homme("assaut", rx, ry,
                  { nom: "Aegon II", hors: true, roi: true,
                    role: "roi — s'il tombe, tout s'arrête" });
      S.roi.etat = "tient"; S.roi.poste = [rx, ry];
      S.roi.entree = porte; S.roi.verrou = verrouDe(porte);
      S.hommes.push(S.roi);
      const nEsc = Math.max(6, Math.round(ROI_ESCORTE * S.ECHELLE));
      for (let i = 0; i < nEsc; i++) {
        const a = (i / nEsc) * Math.PI * 2, r = 4 + (i % 3) * 1.4;
        const px = rx + Math.cos(a) * r, py = ry + Math.sin(a) * r;
        const g = homme("assaut", px, py, { hors: true, poste: [px, py] });
        g.etat = "tient"; g.entree = porte; g.verrou = verrouDe(porte);
        S.hommes.push(g);
      }
    }
    fig("garde", [donjon.x - 14, donjon.y - 10], "Ser Merryn Coutre", "châtelain",
        "châtelain — il veut rendre le Donjon intact, et il ne décide jamais à temps");
    fig("garde", [donjon.x + 12, donjon.y - 16], "Dame Elyanne de Rosby", "la doyenne",
        "soixante et onze ans, et elle refuse de quitter ses chambres pour un jeu");
    fig("garde", [donjon.x + 16, donjon.y + 8], "le sergent Gaunt le Portier", "il a la clef",
        "il est pour qu'on ouvre — la seule porte qui puisse s'ouvrir sans se casser");
    fig("garde", [donjon.x - 10, donjon.y + 14], "le septon Marris", "la Foi",
        "il a demandé que ça ne se fasse pas la nuit, et on ne lui a pas répondu");

    const mp = repereDuPlan("Le marché aux poissons", "marche-poissons");
    fig("ville", dans(20, 12), "Rob l'écailler", "écailler",
        "il sauve son étal avant sa femme, et il le sait déjà");
    fig("ville", dans(48, -18), "les deux Nayle", "quatorze et onze ans",
        "quatorze ans et onze ans — ils suivent l'armée, ils trouvent ça magnifique");
    fig("ville", dans(62, 26), "le vieux Wex", "sourd",
        "sourd, sur le pas de sa porte — il ne bougera pas");
    fig("ville", dans(120, -40), "mestre Ottyn", "apothicaire",
        "apothicaire — il ne ferme pas, il sait ce qu'il aura dans son échoppe dans une heure");
    fig("ville", mp ? [mp.x + 18, mp.y - 10] : dans(290, 0), "Nonne la lavandière", "lavandière",
        "trois enfants, elle en compte deux, et elle REMONTE vers le bruit");
    fig("ville", dans(150, 62), "sœur Jenn", "septuaire",
        "elle ouvre le septuaire et hurle qu'on y entre — deux cents y entrent");
    fig("ville", dans(205, -85), "Cateline la sage-femme", "sage-femme",
        "elle va vers la bataille depuis le début, et elle est en train d'accoucher quelqu'un");
    fig("ville", dans(265, -120), "la Veuve", "receleuse",
        "receleuse, rue des Sœurs — elle ne sort pas, et elle achète dès ce soir");

    // `entree` et `verrou` restent, mais ne désignent plus QUE la porte
    // principale — celle qu'on a demandée au four. Ils ne servent qu'à ce qui
    // parle de la bataille en général : le bandeau, le relevé, le cercle du
    // plan. Tout ce qui concerne un homme passe par le sien.
    S.entree = porte;
    S.verrou = S.verrous.find((v) => v.nom === porte.nom) || S.verrous[0] || null;

    // ---- ET ILS REGARDENT QUELQUE PART ---------------------------------------
    // ON NE VOYAIT AUCUNE ARME AVANT QUE LA TROUPE NE BOUGE, et la cause n'est
    // pas dans le dessin : `fx, fy` naissent à zéro, `tourner` rend la main tout
    // de suite quand il n'y a pas de cap voulu (`!h.cx && !h.cy`), et seul
    // `versLe` en pose un — c'est-à-dire seulement quand on marche. Un homme
    // qui tient son poste depuis le début n'avait donc PAS DE CAP DU TOUT, ce
    // qui est faux de toute façon : une garnison rangée devant une porte
    // regarde la porte, elle n'attend pas d'avoir marché pour savoir où est
    // l'ennemi. Le fer invisible n'était que le symptôme visible de ce trou.
    //
    // Chacun se tourne vers SA porte — celle de son escouade, pas la principale.
    // Les deux camps la regardent donc, chacun de son côté du seuil : c'est
    // exactement la figure de départ, et l'on obtient une haie de lances qui
    // pointe dans le bon sens avant le premier pas.
    //
    // On pose `cx, cy` autant que `fx, fy` : le cap VOULU et le cap TENU. Sans
    // le premier, `tourner` ferait revenir le second à zéro au battement
    // suivant, et les armes disparaîtraient une seconde fois.
    for (const h of S.hommes) {
      const p = h.entree || porte;
      if (!p) continue;
      const dx = p.x - h.x, dy = p.y - h.y, d = Math.hypot(dx, dy);
      if (d < .01) continue;
      h.cx = dx / d; h.cy = dy / d;
      h.fx = h.cx;   h.fy = h.cy;   h.w = 0;
    }

    majCompte();
  }

  // ---- le voisinage ---------------------------------------------------------
  // Trois cent quatre-vingts corps, c'est peu — mais « peu » au carré fait
  // cent quarante mille comparaisons vingt fois par seconde, et c'est ainsi
  // qu'une simulation simple devient lente sans qu'on comprenne pourquoi. Une
  // grille de six mètres ramène ça à ce qu'on touche du coude.
  //
  // LA CASE SE DÉSIGNE PAR UN ENTIER, JAMAIS PAR UNE CLEF DE TEXTE. C'est la
  // même leçon que la peur des habitants porte trente lignes plus haut, et il
  // a fallu la réapprendre ici aussi. `autour` fabriquait un `ci + ":" + cj`
  // par case consultée : chaque homme en consulte dix-huit par pas, deux fois
  // (une fois pour chercher l'ennemi, une fois pour jouer des coudes). À deux
  // mille hommes et vingt pas par seconde, cela faisait SEPT CENT VINGT MILLE
  // concaténations de chaînes par seconde de bataille — un coût fixe par
  // homme, que la mêlée n'expliquait pas et que le profil désignait seul.
  //
  // À la place, un tri par comptage : `debut[]` dit où commence chaque case
  // dans `corps[]`, et `corps[]` tient les indices des hommes rangés case par
  // case. Deux passes, aucune allocation — les deux tampons sont réutilisés
  // d'un pas à l'autre et ne grandissent que quand il le faut.
  //
  // La grille ne couvre PAS le plan entier : cinq kilomètres sur trois en
  // mailles de trois mètres feraient trois millions et demi de cases à remettre
  // à zéro vingt fois par seconde, pour une bataille qui tient dans un carré de
  // six cents mètres. On la taille donc sur les hommes eux-mêmes, à chaque pas.
  //
  // Mais on la CALE SUR LA MÊME TRAME que les clefs de texte d'avant : l'origine
  // tombe sur un multiple de MAILLE, donc les cases découpent le terrain
  // exactement là où elles le découpaient. Sans quoi le voisinage change au
  // ras des bords de case, et une optimisation qui promettait de ne rien
  // changer change la bataille.




  // Les hommes bougent APRÈS le semis (`soldat` puis `pousser`), donc leur
  // case peut déborder de la boîte d'un pas de marche. Huit cases de marge
  // valent vingt-quatre mètres : personne ne franchit ça en un vingtième de
  // seconde, et une case vide ne coûte rien.
  const MARGE_C = 8;

  // ---- LE CHEMIN APPARTIENT À L'ORDRE DE L'UNITÉ ---------------------------
  // Ni la porte ni le Donjon ne sont des cas du navigateur. Une destination
  // est un identifiant et deux mètres ; changer d'ordre invalide la route du
  // chef. Les dix-neuf autres gardent seulement leur place relative.
  const RAIL_DEVANT = 8;          // à quelle distance on regarde sur le rail

  function memeDestination(a, b) {
    return !!a && !!b && a.id === b.id &&
      Math.hypot(a.x - b.x, a.y - b.y) < 0.5;
  }

  function ordonnerFormation(id, destination, opts) {
    const u = typeof id === "number" ? S.formations[id]
      : S.formations.find((x) => x.id === id);
    if (!u || !destination || !Number.isFinite(destination.x) ||
        !Number.isFinite(destination.y)) return false;
    const d = { id: destination.id || ("point:" + Math.round(destination.x) + ":" +
                                      Math.round(destination.y)),
                x: destination.x, y: destination.y,
                nom: destination.nom || destination.id || "destination" };
    const mode = (opts && opts.mode) || "marcher";
    // La phrase naît avec l'ordre et voyage avec lui. Le rendu ne doit jamais
    // reconstruire après coup un vague « MARCHER » depuis l'état des jambes.
    const texte = (opts && opts.texte) || (mode === "marcher"
      ? "À " + d.nom + ". Restez avec votre unité."
      : "Tenez " + d.nom + ".");
    if (!memeDestination(u.ordre.destination, d) ||
        u.ordre.mode !== mode) {
      u.ordre = { mode, destination: d,
                  source: (opts && opts.source) || "ordre-unite",
                  version: (u.ordre.version || 0) + 1, donneA: S.temps,
                  ditA: S.temps, texte };
      u.cadre.trace = null; u.cadre.clef = null; u.cadre.s = 0;
      u.cadre.finition = null;
      u.cadre.phase = "ordre";
    } else if (u.ordre.texte !== texte && opts && opts.texte) {
      // Redire autrement le même déplacement est un nouvel ordre entendu,
      // mais pas une raison de recalculer la même route.
      u.ordre.texte = texte; u.ordre.donneA = S.temps; u.ordre.ditA = S.temps;
    }
    return true;
  }

  /**
   * Donner une FORME à un camp autour d'un point. Une forme n'est pas un
   * pochoir de coordonnées mondiales : elle se pose sur une EMPRISE DE SOL
   * COMMUNE. Dans un champ cette emprise s'élargit et porte une ligne ; dans
   * une rue elle se resserre et les mêmes unités prennent de la profondeur.
   * Une façade arrête la largeur disponible : on ne saute jamais par-dessus
   * pour offrir à la vintaine suivante une arrière-cour qui paraît « libre ».
   */
  function ancreCollectiveLibre(x, y) {
    if (!obstacleConnu() || !obstaclePres(x,y)) return {x,y};
    // Ceci arrive UNE FOIS pour le repère de toute l'armée. L'ancienne version
    // faisait la même recherche pour chaque vintaine : c'est elle qui imprimait
    // le damier dans les poches libres de chaque pâté.
    for (let r=1;r<=32;r+=1) for (let i=0;i<24;i++) {
      const a=i*Math.PI*2/24, px=x+Math.cos(a)*r, py=y+Math.sin(a)*r;
      if (!obstaclePres(px,py)) return {x:px,y:py};
    }
    return {x,y};
  }

  const longueurPoints = (pts) => {
    let n=0;
    for(let i=1;i<(pts||[]).length;i++)
      n+=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);
    return n;
  };

  // Un seul axe topologique pour tout le déploiement. On le prolonge par
  // tronçons afin qu'une armée nombreuse puisse contourner plusieurs pâtés
  // sans demander un A* gigantesque, ni un A* par unité.
  function traceDeploiement(centre, fx, fy, longueur) {
    const depart=ancreCollectiveLibre(centre.x,centre.y);
    if (!obstacleConnu()) return traceLocale([[depart.x,depart.y],
      [depart.x-fx*longueur,depart.y-fy*longueur]]);
    const tx=-fy,ty=fx,pts=[[depart.x,depart.y]];
    let courant=depart,total=0,garde=0;
    while(total<longueur&&garde++<Math.ceil(longueur/24)+8){
      const tranche=Math.min(42,Math.max(12,longueur-total));
      let meilleur=null;
      for(const recul of [tranche,tranche*.8,tranche*.62]){
        for(const lateral of [0,-4,4,-8,8,-13,13,-20,20]){
          const cible={x:courant.x-fx*recul+tx*lateral,
                       y:courant.y-fy*recul+ty*lateral};
          if(obstaclePres(cible.x,cible.y))continue;
          const chemin=!segmentMasqueBloque(courant.x,courant.y,
            cible.x,cible.y,true)
            ? [[courant.x,courant.y],[cible.x,cible.y]]
            : cheminDePorte(courant.x,courant.y,cible.x,cible.y,true);
          if(!chemin||chemin.length<2)continue;
          const len=longueurPoints(chemin);
          // Le détour réel coûte, et une dérive latérale coûte un peu : le
          // ruban préfère continuer la rue où il est sans exiger qu'elle soit
          // droite.
          const score=len+Math.abs(lateral)*.35+(tranche-recul)*.8;
          if(!meilleur||score<meilleur.score)meilleur={chemin,score};
        }
      }
      if(!meilleur)break;
      for(const p of meilleur.chemin.slice(1)){
        const avant=pts[pts.length-1];
        if(Math.hypot(p[0]-avant[0],p[1]-avant[1])>.05)pts.push([p[0],p[1]]);
      }
      const fin=pts[pts.length-1];
      courant={x:fin[0],y:fin[1]};
      total=longueurPoints(pts);
    }
    // Deux points suffisent à rendre l'échec honnête et observable. Toutes les
    // places resteront encore sur ce même bout de sol au lieu d'être projetées
    // chacune dans une poche différente.
    if(pts.length<2)pts.push([depart.x-fx*1,depart.y-fy*1]);
    return traceLocale(pts);
  }

  function intervalleSurRuban(trace,s,maxi){
    const q=surTrace(trace,Math.max(0,Math.min(trace.long,s)));
    if(!obstacleConnu())return {q,gauche:maxi,droite:maxi};
    const pas=.5,nx=q[2],ny=q[3];let gauche=0,droite=0;
    // On s'arrête au PREMIER obstacle de chaque côté. Une cour derrière une
    // maison n'appartient donc pas à la même ligne, même si son centre est libre.
    while(gauche+pas<=maxi&&!obstaclePres(q[0]-nx*(gauche+pas),
      q[1]-ny*(gauche+pas)))gauche+=pas;
    while(droite+pas<=maxi&&!obstaclePres(q[0]+nx*(droite+pas),
      q[1]+ny*(droite+pas)))droite+=pas;
    return {q,gauche,droite};
  }

  const ecartAncres = (a,b) => !a||!b ? 0
    : a.aile===b.aile ? 7.2
    : a.corps===b.corps ? 10.7
    : 17.2;

  function ajouterStat(map,id,p){
    if(id==null)return;
    if(!map.has(id))map.set(id,{n:0,s:0,lateral:0,minS:Infinity,maxS:-Infinity});
    const q=map.get(id);q.n++;q.s+=p.sRuban;q.lateral+=p.lateral;
    q.minS=Math.min(q.minS,p.sRuban);q.maxS=Math.max(q.maxS,p.sRuban);
  }

  function cibleCommandementSurRuban(trace,s,lateral,occupes,ecart){
    let retenu=null;
    const pasS=Math.max(2.4,ecart),profondeurs=[0];
    for(let d=pasS;d<=pasS*4;d+=pasS)profondeurs.push(d,-d);
    for(const ds of profondeurs){
      const ss=Math.max(0,Math.min(trace.long,s+ds));
      const coupe=intervalleSurRuban(trace,ss,24),q=coupe.q;
      const bas=-Math.max(0,coupe.gauche-.45),haut=Math.max(0,coupe.droite-.45);
      const vise=Math.max(bas,Math.min(haut,lateral)),candidats=[vise];
      for(let d=1.2;d<=24;d+=1.2)candidats.push(vise-d,vise+d);
      for(const c of candidats){
        if(c<bas||c>haut)continue;
        const x=q[0]+q[2]*c,y=q[1]+q[3]*c;
        if((occupes||[]).some((p)=>Math.hypot(x-p.x,y-p.y)<ecart))continue;
        retenu={x,y,fx:-q[3],fy:q[2],sRuban:ss,lateral:c};break;
      }
      if(retenu)break;
    }
    // Un ruban saturé reste un ruban : même l'ultime repli ne va pas chercher
    // un carré libre derrière une façade. Il garde le point de relation prévu,
    // et la répulsion locale fera gagner l'épaule qui manque.
    if(!retenu){
      const coupe=intervalleSurRuban(trace,s,24),q=coupe.q;
      const c=Math.max(-coupe.gauche,Math.min(coupe.droite,lateral));
      retenu={x:q[0]+q[2]*c,y:q[1]+q[3]*c,
        fx:-q[3],fy:q[2],sRuban:s,lateral:c};
    }
    const p=retenu;
    if(occupes)occupes.push(p);return p;
  }

  function planifierRassemblement(camp,centre,vers){
    const us=S.formations.filter((u)=>u.camp===camp&&u.membres.some((h)=>
      h.etat!=="mort"&&h.etat!=="blesse"));
    if(!us.length)return null;
    let fx=vers?vers.x-centre.x:1,fy=vers?vers.y-centre.y:0;
    const fd=Math.hypot(fx,fy)||1;fx/=fd;fy/=fd;
    const groupes=new Map();
    for(const u of us){
      const e=u.escouade!=null?S.escouades[u.escouade]:null;
      const corps=e?e.corps:(u.parent||u.id),aile=e?e.aile:u.parent;
      if(!groupes.has(corps))groupes.set(corps,{corps,unites:[]});
      groupes.get(corps).unites.push({u,corps,aile});
    }
    const corps=Array.from(groupes.values());
    for(const g of corps)g.unites.sort((a,b)=>(a.aile||0)-(b.aile||0)||
      a.u.rangParent-b.u.rangParent);
    // Front, soutien, réserve restent des échelons de COMMANDEMENT. Le nombre
    // de lignes physiques qu'ils occupent dépend désormais du sol disponible.
    const parEchelon=Math.max(1,Math.ceil(corps.length/3)),echelons=[];
    for(let i=0;i<corps.length;i+=parEchelon)
      echelons.push(corps.slice(i,i+parEchelon).flatMap((g)=>g.unites));
    const longueur=us.length*8+Math.max(0,echelons.length-1)*5+12;
    const trace=traceDeploiement(centre,fx,fy,longueur);
    const attributions=[],places=[],statsAiles=new Map(),statsCorps=new Map();
    let s=0,ligneSol=0;
    for(let rang=0;rang<echelons.length;rang++){
      const file=echelons[rang];let i=0,spanVise=0;
      for(let k=1;k<file.length;k++)spanVise+=ecartAncres(file[k-1],file[k]);
      const demiVise=Math.min(80,Math.max(10,spanVise/2+1));
      while(i<file.length){
        const sLigne=Math.max(0,Math.min(trace.long,s+((ligneSol%3)-1)*.22));
        const coupe=intervalleSurRuban(trace,sLigne,demiVise);
        const gauche=Math.max(0,coupe.gauche-.55),droite=Math.max(0,coupe.droite-.55);
        let fin=i,span=0;
        while(fin+1<file.length){
          const suivant=span+ecartAncres(file[fin],file[fin+1]);
          if(suivant>gauche+droite)break;
          span=suivant;fin++;
        }
        let debut=-span/2;
        debut=Math.max(-gauche,Math.min(droite-span,debut));
        for(let k=i;k<=fin;k++){
          if(k>i)debut+=ecartAncres(file[k-1],file[k]);
          const q=coupe.q,p={unite:file[k].u.id,corps:file[k].corps,
            aile:file[k].aile,x:q[0]+q[2]*debut,y:q[1]+q[3]*debut,
            fx:-q[3],fy:q[2],rang,ligneSol,sRuban:sLigne,lateral:debut};
          places.push(p);attributions.push({u:file[k].u,place:p});
          ajouterStat(statsAiles,p.aile,p);ajouterStat(statsCorps,p.corps,p);
        }
        i=fin+1;ligneSol++;
        s+=7.4+(ligneSol%2?.35:-.2);
      }
      s+=4.5;
    }
    // Les chefs prennent place PAR RAPPORT aux unités réellement posées, sur
    // le même ruban. Ils ne forment pas un second pochoir indépendant.
    const occupes=places.map((p)=>({x:p.x,y:p.y}));
    const capitainesPlan=new Map();
    for(const [aile,p] of statsAiles){
      const a=S.ailes[aile],capitaine=a&&a.capitaine;if(!capitaine)continue;
      const cible=cibleCommandementSurRuban(trace,Math.max(0,p.minS-3.2),
        p.lateral/p.n,occupes,2.7);cible.aile=aile;
      capitainesPlan.set(capitaine,cible);
    }
    const tetesPlan=new Map();
    for(const [corpsId,p] of statsCorps){
      const cible=cibleCommandementSurRuban(trace,
        Math.min(trace.long,p.maxS+4.2),p.lateral/p.n,occupes,3.2);
      cible.corps=corpsId;tetesPlan.set(corpsId,cible);
    }
    return {us,fx,fy,trace,places,attributions,tetesPlan,capitainesPlan};
  }

  function ordonnerRassemblement(camp, centre, opts) {
    if (!centre || !Number.isFinite(centre.x) || !Number.isFinite(centre.y))
      return false;
    const vers = opts && opts.vers;
    const plan=planifierRassemblement(camp,centre,vers);
    if(!plan)return false;
    const {us,fx,fy,trace,places,attributions,tetesPlan,capitainesPlan}=plan;
    const id=(opts&&opts.id)||("deploiement:"+camp);
    for(const {u,place:p} of attributions){
      const guide=guideDe(u);
      u.cadre.ralliement={deploiementId:id,phase:"retrouver",commenceA:S.temps,
        departX:guide?guide.x:p.x,departY:guide?guide.y:p.y,
        x:p.x,y:p.y,fx:p.fx,fy:p.fy,corps:p.corps,aile:p.aile,
        rang:p.rang,ligneSol:p.ligneSol,sRuban:p.sRuban,proches:0};
      ordonnerFormation(u.n,
        {id:"ralliement:"+camp+":"+u.id,
         nom:(opts&&opts.nom)||"la ligne de rassemblement",x:p.x,y:p.y},
        {mode:"rassembler",source:"ordre-rassemblement",
         texte:(opts&&opts.texte)||
           "Retrouvez les vôtres, puis prenez votre place dans la ligne."});
    }
    const commandants = new Map();
    const ordreInitial = (opts && opts.texte) ||
      "Retrouvez les vôtres, puis prenez votre place dans la ligne.";
    for (const h of S.tetes) if (h.camp === camp && tetesPlan.has(h.corps)) {
      const mem = Commandement.memoire({ proprietaire:h.debugId,
        echelon:"corps", camp });
      Commandement.recevoirOrdre(mem, ordreInitial, S.temps);
      commandants.set(h, { memoire:mem, role:"chef de corps", corps:h.corps });
      h.commandement = mem;
    }
    for (const [h, p] of capitainesPlan) {
      const mem = Commandement.memoire({ proprietaire:h.debugId,
        echelon:"aile", camp });
      Commandement.recevoirOrdre(mem, ordreInitial, S.temps);
      commandants.set(h, { memoire:mem, role:"centenar", corps:h.corps, aile:p.aile });
      h.commandement = mem;
    }
    S.deploiements.set(id, { id, camp, centre: { x: centre.x, y: centre.y }, fx, fy,
                           commenceA: S.temps, trace, places, tetes: tetesPlan,
                           capitaines: capitainesPlan, commandants,
                           commandeObserveA:-Infinity });
    return true;
  }

  // L'entrée publique des déploiements. Les formes futures ajoutent un
  // planificateur ici ; elles réutilisent la même exécution par échelons et ne
  // créent pas une nouvelle cascade dans `soldat()`.
  function ordonnerDeploiement(spec) {
    if (!spec || !spec.ancre || !spec.troupe) return false;
    const forme = spec.forme || "ligne-soutien-reserve";
    if (forme !== "ligne-soutien-reserve") return false;
    return ordonnerRassemblement(spec.troupe.camp, spec.ancre, {
      id: spec.id,
      vers: spec.front,
      nom: (spec.ordre && spec.ordre.destination) || spec.nom,
      texte: spec.ordre && spec.ordre.texte,
    });
  }

  /**
   * Ajouter une doctrine à l'ordre d'un déploiement entier.
   *
   * L'appelant choisit un enseignement déclaré dans le moteur, jamais une
   * branche de `soldat()`. Toutes les unités le reçoivent ; chaque homme passe
   * ensuite par la pile complète et peut obéir, se sidérer, dérober ou rompre.
   */
  function ordonnerDoctrineDeploiement(id, doctrineId) {
    const dep = S.deploiements.get(id), doctrine = DOCTRINES[doctrineId];
    if (!dep || !doctrine) return false;
    dep.doctrine = { id:doctrine.id, donneA:S.temps };
    let n = 0;
    for (const u of S.formations) {
      const r = u.cadre && u.cadre.ralliement;
      if (!r || r.deploiementId !== id) continue;
      u.doctrine = { id:doctrine.id, donneA:S.temps, source:"ordre-deploiement" };
      // Un ordre stocké seulement sur l'unité serait connu du moteur mais pas
      // de l'homme : sa couche 3 continuerait à peser une consigne vieille de
      // trois minutes et l'arbitre conclurait justement qu'il n'obéit plus.
      // On marque donc sa réception par l'escouade et force la prochaine
      // interprétation individuelle, sans choisir son résultat.
      const e = u.escouade != null ? S.escouades[u.escouade] : null;
      if (e) { e.depuis = 0; e.doctrine = doctrine.id; }
      for (const h of u.membres) h.revoirL3 = 0;
      n++;
    }
    for (const c of dep.commandants.values())
      Commandement.recevoirOrdre(c.memoire,
        "Au dragon : ouvrez les rangs, gardez vos chefs en vue, ralliez au passage.", S.temps);
    noter("doctrine-donnee", dep.centre.x, dep.centre.y,
      { dit:{ deploiement:id, doctrine:doctrine.id, unites:n } });
    return n > 0;
  }

  /** Déplacer le repère supérieur : les secteurs suivent, pas les hommes un à un. */
  function deplacerDeploiement(id, ancre, opts) {
    const dep = S.deploiements.get(id);
    if (!dep || !ancre || !Number.isFinite(ancre.x) || !Number.isFinite(ancre.y))
      return false;
    const dx = ancre.x - dep.centre.x, dy = ancre.y - dep.centre.y;
    const plan=planifierRassemblement(dep.camp,ancre,
      {x:ancre.x+dep.fx,y:ancre.y+dep.fy});
    if(!plan)return false;
    dep.centre = { x:ancre.x, y:ancre.y };
    dep.fx=plan.fx;dep.fy=plan.fy;dep.trace=plan.trace;
    dep.places=plan.places;dep.tetes=plan.tetesPlan;
    dep.capitaines=plan.capitainesPlan;
    // Un point dit OÙ porter le front ; le but dit CE QU'IL FAUT Y FAIRE.
    // Sans cette seconde moitié, « avancez sur l'ennemi » devenait « allez à
    // cette coordonnée » et deux lignes disciplinées s'arrêtaient chacune à
    // son dernier slot, parfois dix mètres avant le fer. `engager` reste une
    // faculté de déploiement générale : seul le premier échelon ferme
    // localement l'intervalle, les soutiens gardent leur profondeur.
    if (opts && opts.but) dep.but = opts.but;
    if (opts && Number.isFinite(opts.rayonEngagement))
      dep.rayonEngagement = opts.rayonEngagement;
    if (opts && opts.texte) for (const c of dep.commandants.values())
      Commandement.recevoirOrdre(c.memoire, opts.texte, S.temps);
    // Le déplacement recalcule le RUBAN entier sur le nouveau sol. Traduire
    // puis « sauver » chaque ancien slot séparément recréait exactement le
    // pochoir dans les arrière-cours.
    const placesParUnite=new Map(dep.places.map((p)=>[p.unite,p]));
    for (const u of S.formations) {
      const r = u.cadre.ralliement;
      if (!r || r.deploiementId !== id) continue;
      const place=placesParUnite.get(u.id);
      r.x=place ? place.x : r.x+dx; r.y=place ? place.y : r.y+dy;
      if(place){r.fx=place.fx;r.fy=place.fy;r.corps=place.corps;
        r.aile=place.aile;r.rang=place.rang;r.ligneSol=place.ligneSol;
        r.sRuban=place.sRuban;}
      r.routeMasque=null;
      // Une unité encore en train de retrouver les siens doit elle aussi
      // recevoir le déplacement du repère. Sinon les retardataires achèvent
      // leur rassemblement sur l'ancien champ pendant que l'armée avance.
      r.departX += dx; r.departY += dy;
      if (u.ordre.destination) {
        u.ordre.destination.x=r.x;u.ordre.destination.y=r.y;
      }
      u.ordre.version=(u.ordre.version||0)+1;
      u.cadre.trace=null;u.cadre.clef=null;u.cadre.s=0;u.cadre.finition=null;
      if (r.phase !== "retrouver") r.phase = "prendre-place";
      if (opts && opts.texte) {
        u.ordre.texte = opts.texte; u.ordre.donneA = S.temps; u.ordre.ditA = S.temps;
      }
      // Recevoir le déplacement du front donne aussi son ORIENTATION. Sans
      // cela, les hommes déjà rangés gardaient le dernier cap latéral de leur
      // mise en place jusqu'à leur prochain pas : une ligne avançait avec un
      // tiers des visages encore tournés vers son propre intervalle.
      for (const h of u.membres) {
        if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
        h.fx = r.fx; h.fy = r.fy;
      }
    }
    return true;
  }

  const Navigation = window.BatailleMondeNavigation.creer(S, { EPAULE, topologie: Topologie });
  const { segmentMasqueBloque, traceLocale, assurerRouteRalliement, cibleRalliementSurTrace, raccorderTraceFormation, calculerRouteFormation, surTrace, cheminDePorte } = Navigation;
  // Un calcul pour le vintenar, une trace pour les vingt. Le guide suit les
  // jalons du masque ; les autres prennent leur recul sur CETTE trace au lieu
  // de viser leur chef à travers la maison.
  function suivreRouteRalliement(h,u,r,guide,v,dt){
    const q=assurerRouteRalliement(r,guide,u);
    if(q.direct){
      if(h!==guide)return false;
      versLe(h,r.x,r.y,v,dt);
      const reste=Math.hypot(h.x-r.x,h.y-r.y);
      if(reste<q.meilleurReste-.7){q.meilleurReste=reste;q.avanceA=S.temps;}
      else if(S.temps-q.avanceA>6&&q.recalculs<2){
        const pts=cheminDePorte(h.x,h.y,r.x,r.y,true)||
          cheminDePorte(h.x,h.y,r.x,r.y,false);
        if(pts&&pts.length){q.direct=false;q.trace=traceLocale(pts);q.s=0;
          q.recalculs++;q.avanceA=S.temps;u.cadre.calculs++;}
      }
      return true;
    }
    if(!q.trace||q.s>=q.trace.long-.35)return false;
    if(h===guide){
      const p=surTrace(q.trace,Math.min(q.trace.long,q.s+1.15));
      const ax=h.x,ay=h.y;versLeSurRouteMasque(h,p[0],p[1],v,dt);
      const gagne=Math.hypot(h.x-ax,h.y-ay);q.s=Math.min(q.trace.long,q.s+gagne);
      q.tentatives=(q.tentatives||0)+1;
      q.dernierPas=gagne;q.dernierBut=[p[0],p[1]];
      if(Math.hypot(h.x-q.dernierX,h.y-q.dernierY)>.7){
        q.dernierX=h.x;q.dernierY=h.y;q.avanceA=S.temps;
      }else if(S.temps-q.avanceA>12&&q.recalculs<2){
        const n=q.recalculs+1;r.routeMasque=null;
        const neuve=assurerRouteRalliement(r,guide,u);neuve.recalculs=n;
      }
      return true;
    }
    const p=h.placeFormation||placeDeFormation(1);
    const cible=cibleRalliementSurTrace(q.trace,Math.max(0,q.s-p.recul),p,h);
    versLeSurRouteMasque(h,cible[0],cible[1],v*(q.s-p.recul>4?1.12:1),dt);
    return true;
  }

  function menerCommandantParMasque(h,p,cle,v,dt,compteur){
    const routeCle=cle+":"+p.x.toFixed(1)+":"+p.y.toFixed(1);
    let q=h.routeCommandement;
    if(!q||q.clef!==routeCle){
      const bloque=segmentMasqueBloque(h.x,h.y,p.x,p.y,true);
      const pts=bloque?cheminDePorte(h.x,h.y,p.x,p.y,false):null;
      q=h.routeCommandement={clef:routeCle,pts:pts||null,i:1,direct:!bloque||!pts,
        dernierX:h.x,dernierY:h.y,avanceA:S.temps,recalculs:0,
        meilleurReste:Math.hypot(h.x-p.x,h.y-p.y)};
      if(bloque){if(compteur)compteur.calculs++;else h.calculsCommandement=(h.calculsCommandement||0)+1;}
    }
    if(q.direct){
      versLe(h,p.x,p.y,v,dt);
      const reste=Math.hypot(h.x-p.x,h.y-p.y);
      if(reste<q.meilleurReste-.7){q.meilleurReste=reste;q.avanceA=S.temps;}
      else if(S.temps-q.avanceA>6&&q.recalculs<2){
        const pts=cheminDePorte(h.x,h.y,p.x,p.y,false);
        if(pts&&pts.length){q.direct=false;q.pts=pts;q.i=1;q.recalculs++;
          q.avanceA=S.temps;
          if(compteur)compteur.calculs++;else h.calculsCommandement=(h.calculsCommandement||0)+1;}
      }
      return true;
    }
    if(!q.pts||!q.pts.length)return false;
    while(q.i<q.pts.length-1&&Math.hypot(h.x-q.pts[q.i][0],h.y-q.pts[q.i][1])<.7)q.i++;
    const but=q.pts[Math.min(q.i,q.pts.length-1)];
    versLeSurRouteMasque(h,but[0],but[1],v,dt);
    if(Math.hypot(h.x-q.dernierX,h.y-q.dernierY)>.7){
      q.dernierX=h.x;q.dernierY=h.y;q.avanceA=S.temps;
    }else if(S.temps-q.avanceA>12&&q.recalculs<2){
      const n=q.recalculs+1;h.routeCommandement=null;
      menerCommandantParMasque(h,p,cle,v,dt,compteur);
      if(h.routeCommandement)h.routeCommandement.recalculs=n;
    }
    return true;
  }

  function rassemblerFormation(h, u, v, dt) {
    const r = u && u.cadre && u.cadre.ralliement, guide = guideDe(u);
    if (!r || !guide) return false;
    const dep = S.deploiements.get(r.deploiementId);
    if (h === guide) {
      // Le centenar a désormais une charge d'aile : son départ vers la place
      // de commandement ne doit pas empêcher sa vintaine d'origine de se dire
      // rassemblée, surtout aux petites échelles où elle peut n'avoir que deux
      // hommes dans le banc.
      const vifs = u.membres.filter((x) => x.etat !== "mort" && x.etat !== "blesse" &&
        !x.capitaine);
      const proches = vifs.filter((x) => x === guide ||
        Math.hypot(x.x - guide.x, x.y - guide.y) <= 8).length / (vifs.length || 1);
      r.proches = proches;
      if (r.phase === "retrouver" && proches >= .70 && S.temps - r.commenceA >= 2)
        r.phase = "prendre-place";
      if (r.phase === "retrouver")
        return versLe(h, r.departX, r.departY, v * .55, dt);
      // ARRIVER SUR LA LIGNE N'ACCOMPLIT PAS UN ORDRE D'ENGAGER. Le guide du
      // premier échelon transforme alors le repère fixe en front mobile : il
      // choisit l'ennemi réellement présent devant sa vintaine et ferme les
      // derniers mètres. Les autres suivent leur guide par leurs places
      // relatives ; personne ne reçoit une cible géométrique individuelle.
      if (r.phase === "en-place" && dep && dep.but === "engager" &&
          (r.rang || 0) === 0 && proches >= .65) {
        const cible = ennemiProche(h, dep.rayonEngagement || 45);
        if (cible) {
          const dx = cible.x - h.x, dy = cible.y - h.y, d = Math.hypot(dx, dy) || 1;
          h.fx = dx / d; h.fy = dy / d;
          penser(h, "fermer l'intervalle avec la ligne ennemie",
                 "notre ordre est d'engager et ma vintaine est avec moi",
                 "ordre de déploiement");
          return versLe(h, cible.x, cible.y, v * .88, dt);
        }
      }
      // Une vintaine qui s'étire fait ATTENDRE son chef là où il est. Elle ne
      // le renvoie jamais au point où le ralliement a commencé : ce retour
      // arrière faisait quitter leur emplacement à des unités déjà rangées.
      if (r.phase === "prendre-place" && proches < .55) return 0;
      if (r.phase === "prendre-place" &&
          suivreRouteRalliement(h,u,r,guide,v*.95,dt)) return true;
      const dxBut = h.x - r.x, dyBut = h.y - r.y;
      const travers = dxBut * (-r.fy) + dyBut * r.fx;
      const profondeur = dxBut * r.fx + dyBut * r.fy;
      // Le chef reçoit un petit secteur, pas le centre mathématique du secteur.
      // Il garde donc l'endroit où il est arrivé tant qu'il reste acceptable.
      const arrive = Math.abs(travers) <= 1.3 && Math.abs(profondeur) <= 1.0;
      if (arrive) {
        r.phase = "en-place"; h.fx = r.fx; h.fy = r.fy;
        return 0;
      }
      else {
        const dx = r.x - h.x, dy = r.y - h.y, d = Math.hypot(dx, dy) || 1;
        h.fx = dx / d; h.fy = dy / d;
      }
      return versLe(h, r.x, r.y, v * .95, dt);
    }
    const placeCapitaine = h.capitaine && dep && dep.capitaines &&
      dep.capitaines.get(h);
    if (placeCapitaine) {
      penser(h, "prendre la tête de mon aile",
             "les vintenar doivent pouvoir se ranger sur moi",
             "ralliement de l'aile");
      const dx = placeCapitaine.x - h.x, dy = placeCapitaine.y - h.y;
      const d = Math.hypot(dx, dy);
      if (d > 1) { h.fx = dx / d; h.fy = dy / d; }
      else { h.fx = r.fx; h.fy = r.fy; }
      if(d>1&&menerCommandantParMasque(h,placeCapitaine,
          "capitaine:"+r.deploiementId,v*.88,dt,u.cadre))return true;
      return versLe(h, placeCapitaine.x, placeCapitaine.y, v * .88, dt);
    }
    if(r.phase==="prendre-place"&&suivreRouteRalliement(h,u,r,guide,v,dt))return true;
    const p = h.placeFormation || placeDeFormation(1);
    const nx = -r.fy, ny = r.fx;
    const dxg = h.x - guide.x, dyg = h.y - guide.y;
    const lateralActuel = dxg * nx + dyg * ny;
    const reculActuel = -(dxg * r.fx + dyg * r.fy);
    const lateral = p.cote * 2.4 + (p.biaisCote || 0);
    const recul = p.recul + (p.biaisRecul || 0);
    const borne = (x, a, b) => Math.max(a, Math.min(b, x));
    // Si sa place actuelle est dans la bande permise, elle devient la cible :
    // la vintaine l'emporte avec elle sans le cristalliser au centre.
    const lateralVise = borne(lateralActuel,
      lateral - (p.margeCote || 0), lateral + (p.margeCote || 0));
    const reculVise = borne(reculActuel,
      recul - (p.margeRecul || 0), recul + (p.margeRecul || 0));
    const bx = guide.x - r.fx * reculVise + nx * lateralVise;
    const by = guide.y - r.fy * reculVise + ny * lateralVise;
    const ecart = Math.hypot(h.x - guide.x, h.y - guide.y);
    const allure = ecart > 10 ? 1.28 : ecart > 5 ? 1.12 : .92;
    const bouge = versLe(h, bx, by, v * allure, dt);
    if (Math.hypot(h.x - bx, h.y - by) < .45) {
      h.fx = r.fx; h.fy = r.fy;
    }
    return bouge;
  }

  function menerChefsAuRassemblement(dt) {
    for (const dep of S.deploiements.values()) {
      for (const h of S.tetes) {
        if (h.camp !== dep.camp || h.etat === "mort" || h.etat === "blesse") continue;
        const p = dep.tetes.get(h.corps);
        if (!p) continue;
        // Le chef de corps se place tôt : il est un repère pour ses ailes, pas
        // une récompense qui n'apparaît qu'une fois tout le monde déjà rangé.
        const dx = p.x - h.x, dy = p.y - h.y, d = Math.hypot(dx, dy);
        if (d > 1) { h.fx = dx / d; h.fy = dy / d; }
        else { h.fx = dep.fx; h.fy = dep.fy; }
        if(d>1&&!menerCommandantParMasque(h,p,
            "chef-corps:"+dep.id,MARCHE*.88,dt,null))
          versLe(h, p.x, p.y, MARCHE * .88, dt);
        penser(h, "prendre ma place derrière mon corps",
               "mes ailes doivent savoir où former le corps", "ralliement du corps");
      }
    }
  }

  function cibleDePlace(tr, s, place, h) {
    const q = surTrace(tr, Math.max(0, Math.min(tr.long, s)));
    // La fraction latérale reste la même ; la rue donne les mètres. Une ligne
    // se comprime donc d'elle-même en colonne dans une ruelle et se rouvre sur
    // une place, sans nouvel ordre et sans réassigner un seul homme.
    const ux = q[3], uy = -q[2];
    const demi = Math.max(0.35,
      Math.min((q[4] || 3) / 2, demiLibre(h, q[0], q[1], ux, uy)) - EPAULE);
    const cote = place ? place.cote : 0;
    return [q[0] + q[2] * cote * demi, q[1] + q[3] * cote * demi, q];
  }

  // LE GUIDE CONDUIT UNE UNITÉ, PAS SON PROPRE POINT. Sa vitesse de croisière
  // n'est donc qu'un plafond : quand la majorité utile de sa vintaine s'étire,
  // il raccourcit le pas et finit par attendre. On mesure les corps réels, pas
  // un quota de places pré-écrites ; la même règle vaut dans une rue, sur une
  // place, pour vingt hommes ou pour une unité réduite par les pertes.
  function allureDuGuide(u, guide, v) {
    if (!u || !guide) return v;
    const distances = u.membres.filter((h) => h !== guide && pese(h))
      .map((h) => Math.hypot(h.x - guide.x, h.y - guide.y))
      .sort((a, b) => a - b);
    if (!distances.length) return v;
    // Le septième décile protège la cohésion sans exiger que le dernier homme
    // coincé à un angle immobilise éternellement toute la colonne.
    const etirement = distances[Math.floor((distances.length - 1) * .7)];
    if (etirement >= 10) return v * .15;
    if (etirement >= 8) return v * .35;
    if (etirement >= 6) return v * .60;
    if (etirement >= 4.5) return v * .82;
    return v;
  }

  function suivreGuideDirect(h, guide, bx, by, v, dt) {
    const u = formationDe(h), c = u && u.cadre;
    if (h === guide) return versLe(h, bx, by, allureDuGuide(u, guide, v), dt);
    const p = h.placeFormation || placeDeFormation(1);
    const dx = bx - guide.x, dy = by - guide.y, d = Math.hypot(dx, dy);
    let ux, uy;
    if (d > .45) {
      ux=dx/d; uy=dy/d;
      if (c) { c.faceX=ux; c.faceY=uy; }
    } else {
      ux=(c && c.faceX) || guide.fx || 1;
      uy=(c && c.faceY) || guide.fy || 0;
      const n=Math.hypot(ux,uy)||1; ux/=n; uy/=n;
    }
    return versLe(h,
      guide.x - ux * p.recul - uy * p.cote * 2,
      guide.y - uy * p.recul + ux * p.cote * 2, v, dt);
  }

  function finirApprocheFormation(h, u, guide, d, v, dt) {
    const c=u.cadre;
    if (!c.finition || c.finition.id!==d.id) {
      c.finition={ id:d.id, pts:cheminDePorte(guide.x,guide.y,d.x,d.y), i:1 };
      c.calculs++;
    }
    const f=c.finition;
    if (!f.pts || !f.pts.length) return suivreGuideDirect(h,guide,d.x,d.y,v,dt);
    while(f.i<f.pts.length-1 && Math.hypot(guide.x-f.pts[f.i][0],guide.y-f.pts[f.i][1])<.7)
      f.i++;
    const p=f.pts[Math.min(f.i,f.pts.length-1)];
    return suivreGuideDirect(h,guide,p[0],p[1],v,dt);
  }

  function menerFormation(h, destination, v, dt) {
    const u = formationDe(h), guide = guideDe(u);
    if (!u || !guide || !destination) return false;
    const mission = u.ordre && u.ordre.source === "ordre-ratissage";
    ordonnerFormation(u.n, destination, mission
      // Un ratissage ne signifie pas toujours « fouiller » : son ordre
      // courant peut être le ralliement. Le moteur conserve le mode littéral
      // reçu au lieu de le réécrire à chaque homme et d'invalider sa route.
      ? { mode:u.ordre.mode || "fouiller", source:"ordre-ratissage", texte:u.ordre.texte }
      : { mode:"marcher", source:"conduite" });
    const c = u.cadre, d = u.ordre.destination;
    if (!S.J || !S.voirie) {
      finirApprocheFormation(h, u, guide, d, v, dt);
      return true;
    }

    if (!c.trace) {
      // LE PARENT DONNE LA ROUTE, LE VINTENAR DONNE LA PLACE. Deux vintaines
      // de la même aile qui exécutent le même ordre ne reposent pas deux fois
      // la même question au graphe. La première fait tracer ; les suivantes
      // héritent du tracé et prennent leur recul dans la colonne.
      // La géométrie dépend de l'échelon et du point réel, pas de la version
      // verbale de l'ordre. Deux formulations ou deux instants différents qui
      // visent le même lieu héritent donc bien du même tracé.
      const partage = (u.parent || u.id) + ":" + d.id + ":" +
        d.x.toFixed(1) + ":" + d.y.toFixed(1);
      let route = S.routesFormation.get(partage);
      if (!route) {
        const clef = "bataille:groupe:" + partage;
        route = { clef, trace: calculerRouteFormation(guide,d,clef),
                  par: u.id };
        S.routesFormation.set(partage, route);
        c.calculs++;
      }
      c.clef = route.clef; c.trace = route.trace;
      // Sept mètres entre deux vintaines : assez pour ne pas les confondre,
      // assez peu pour qu'une centaine reste une seule colonne.
      c.s = -(u.rangParent || 0) * 7;
    }
    const tr = c.trace;
    const changeRail = h.railClef !== c.clef;
    h.railClef = c.clef; h.rail = tr;
    if (!tr || !tr.long) {
      suivreGuideDirect(h,guide,d.x,d.y,v,dt);
      return true;
    }

    // La trace composite se termine au but. Il ne reste ici que la tolérance
    // submétrique d'arrivée, sans nouveau calcul de chemin.
    if (c.s >= tr.long - .25) {
      suivreGuideDirect(h,guide,d.x,d.y,v,dt);
      return true;
    }

    if (h === guide) {
      const q = surTrace(tr, Math.min(tr.long, c.s + RAIL_DEVANT));
      const ax = h.x, ay = h.y;
      versLe(h, q[0], q[1], allureDuGuide(u, guide, v), dt);
      c.s = Math.min(tr.long, c.s + Math.hypot(h.x - ax, h.y - ay));
      h.railS = c.s; c.largeur = q[4] || 0;
      return true;
    }

    const p = h.placeFormation || placeDeFormation(1);
    const voulu = Math.max(0, c.s - p.recul);
    const q = cibleDePlace(tr, voulu, p, h);
    const ax = h.x, ay = h.y;
    // Une route est la mémoire de l'unité. Un homme qui la reçoit pour la
    // première fois part de son origine ; laisser `railS` indéfini rendait son
    // retard NaN et désactivait silencieusement l'allure de rattrapage.
    if (!Number.isFinite(h.railS) || changeRail) h.railS = 0;
    versLe(h, q[0], q[1], v * (voulu - h.railS > 4 ? 1.15 : 1), dt);
    h.railS = Math.min(voulu, h.railS + Math.hypot(h.x - ax, h.y - ay));
    return true;
  }

  function versLaPorte(h, verrou, v, dt) {
    return menerFormation(h,
      { id: "porte:" + (verrou.nom || "?"), nom: verrou.nom,
        x: verrou.x, y: verrou.y }, v, dt) ||
      versLe(h, verrou.x, verrou.y, v, dt);
  }

  // L'ÉMOUSSEMENT AU CONTACT. Tout mouvement passe par ici — la marche, la
  // charge, la retraite, la fuite —, donc c'est le seul endroit où le poser.
  // Un homme au milieu de six ne se déplace pas à l'allure d'un homme seul : la
  // presse comptée par `pousser` le freine, et c'est ce qui donne au bouchon
  // devant une porte son épaisseur au lieu d'un flux continu.
  //
  // La forme `1/(1+k·n)` plutôt qu'une soustraction : elle ne peut jamais
  // rendre une vitesse négative, elle mord fort sur les premiers voisins et de
  // moins en moins ensuite — ce qui est la bonne courbe. Deux voisins gênent
  // beaucoup plus que le neuvième, qui ne change plus rien.
  const FREIN_PRESSE = 0.14;

  // Ce qu'on garde de son allure en marchant à reculons. De côté, l'écart se
  // partage : 72 % — la moyenne des deux, et c'est à peu près ce que vaut un
  // pas chassé en armes.
  const RECUL = 0.45;

  const Mouvement = window.BatailleMondeMouvement.creer(S, { ACCEL, AU_CONTACT, EPAULE, FREIN_PIED, FREIN_PRESSE, MAILLE, MARCHE, MARGE_C, MONTEE, PRES_FIGURE, RAD, RECUL, topologie: Topologie, hasardFuite: (h, x) => hasardFuite(h, x), memeEspace: (a, b) => memeEspace(a, b), vigueur: (h) => vigueur(h) });
  const { tourner, presDe, deplacer, surLeRail, caseDe, semer, autour, versLeSurRouteMasque, pousser, versLe } = Mouvement;
  // JUSQU'OÙ IL PEUT ENGAGER. Son allonge, plus le demi-pas qu'on fait toujours
  // en portant le coup — c'est le `+ .6` d'avant, qui vaut pour toutes les armes
  // puisque c'est une mesure de jambe et non de fer.
  //
  // C'EST LA LIGNE QUI CHANGE LE PLUS DE CHOSES DE TOUTE LA PASSE, et il faut
  // le savoir avant de lire une cuisson : la portée n'est plus la même des deux
  // côtés d'une rencontre. Une lance engage à trois mètres quarante un homme au
  // coutelas qui, lui, ne trouve personne à un mètre cinquante — il n'a pas
  // d'autre choix que d'avancer sous la pointe, et il le fait sans le savoir,
  // par le seul jeu de `colonne`. Le premier coup d'une mêlée appartient donc
  // désormais à quelqu'un, et ce n'est plus le hasard des cadences.
  const portee = (h) => ((h.arme && h.arme.allonge) || ALLONGE) + .6;
  const memeEspace = (a, b) => (a.interieur == null && b.interieur == null) ||
    (a.interieur != null && a.interieur === b.interieur);

  function ennemiProche(h, rayon) {
    let m = null, dmin = rayon * rayon;
    autour(h.x, h.y, rayon, (o) => {
      // On n'achève pas un homme à terre, et l'on ne poursuit pas un fuyard :
      // dans les deux cas il a cessé d'être dans la bataille, et c'est ce qui
      // fait qu'il en reste quelqu'un à trouver après.
      // Et l'on ne se bat pas contre un homme qui rentre : l'anneau qu'on
      // vient de faire ouvrir n'est plus un ennemi, c'est une garnison qui se
      // retire dans une cour dont on lui a dit de ne plus défendre l'entrée.
      if (!memeEspace(h, o) || o.camp === h.camp || o.etat === "mort" || o.etat === "blesse" ||
          o.etat === "prisonnier" ||
          o.etat === "deroute" || o.etat === "rentre") return;
      const d = (o.x - h.x) ** 2 + (o.y - h.y) ** 2;
      if (d < dmin) { dmin = d; m = o; }
    });
    return m;
  }

  // ---- ON CHASSE CELUI QUI S'EST DÉTACHÉ ------------------------------------
  // Le plus proche n'est pas le bon. Entre deux ennemis à un mètre l'un de
  // l'autre, on va sur celui qui n'a personne derrière lui — c'est ainsi qu'une
  // ligne mange une pointe, qu'un homme qui a pris dix pas d'avance sur les
  // siens ne les reprend jamais, et que se détacher devient une faute qui se
  // paie. Sans ça, trois hommes tapaient sur trois hommes en trois duels
  // parallèles, et le nombre ne servait à rien.
  //
  // Le tri est un SCORE, pas une préférence absolue : on ne traverse pas la
  // mêlée pour aller chercher un isolé à quinze mètres. La distance pèse, son
  // isolement pèse, et le plus souvent c'est quand même le voisin qu'on frappe.
  // ---- CE QU'UNE PROIE COÛTE, ET CE QU'ON EST PRÊT À PAYER ------------------
  // LE BIAIS DE CONSERVATION D'ÉNERGIE. Un homme préfère ne rien faire, et il
  // lui faut une raison pour bouger. Ce n'est pas une humeur : c'est la seule
  // chose qui explique pourquoi une mêlée réelle est faite de gens qui
  // s'observent, alors qu'un fichier de simulation produit spontanément des
  // gens qui courent tous vers le même point.
  //
  // TOUT SE COMPTE DANS LA MÊME MONNAIE — des mètres. Une proie coûte ce qu'il
  // faut marcher pour l'atteindre, plus ce que ses appuis rendent l'affaire
  // douteuse, plus ce que les nôtres, déjà dessus, la rendent inutile. On prend
  // la moins chère, et si même celle-là passe le budget, ON N'Y VA PAS.
  //
  // L'ENCOMBREMENT EST AU CARRÉ, ET C'EST LE POINT DE LA COURBE. Un seuil net
  // — « à cinq dessus je n'y vais pas » — refait exactement la faute que
  // l'hystérésis a coûté si cher à corriger : deux hommes de part et d'autre
  // d'un compte franchissent la barre en sens inverse à chaque battement. Le
  // carré, lui, ne décide rien brutalement : le deuxième arrivant coûte presque
  // rien (0,7 m), le troisième deux mètres et demi, le quatrième six, le
  // cinquième onze. Personne n'est interdit ; c'est de plus en plus cher, et
  // ça cesse tout seul d'en valoir la peine. Ce qui est la vraie raison : il
  // n'y a pas la place pour six lames autour d'un homme, donc le sixième ne
  // frappe pas, il regarde.
  const ENCOMBRE = 0.7;
  //
  // ET LE BUDGET EST DU SOUFFLE. Voilà ce qui rend le biais vivant plutôt
  // qu'arithmétique : ce n'est pas « on ne va pas au-delà de neuf mètres »,
  // c'est « je n'ai plus de jambes ». Un homme frais dépense quinze mètres
  // d'effort et traversera la rue pour un homme déjà à trois dessus ; le même,
  // vidé par une minute de mêlée, n'en dépense plus trois — il prend ce qui est
  // devant lui ou il ne prend rien.
  //
  // CE QUE ÇA PRODUIT, ET QU'ON NE POUVAIT PAS OBTENIR AUTREMENT : les frais y
  // vont. Une escouade qui vient d'arriver mange les isolés que la ligne
  // épuisée laissait tranquilles depuis dix minutes ; et la même escouade, un
  // quart d'heure plus tard, les laisse à son tour. La relève cesse d'être une
  // idée pour devenir quelque chose qui se voit sur le plan.
  const EFFORT_NU  = 3;    // ce qu'on paie même à bout de souffle
  const EFFORT_VIF = 12;   // ce que le souffle plein achète en plus

  function proieProche(h, rayon) {
    let m = null, best = Infinity, tenue = false, cher = 0;
    autour(h.x, h.y, rayon, (o) => {
      if (!memeEspace(h, o) || o.camp === h.camp || o.etat === "mort" || o.etat === "blesse" ||
          o.etat === "prisonnier" ||
          o.etat === "deroute" || o.etat === "rentre") return;
      const d2 = (o.x - h.x) ** 2 + (o.y - h.y) ** 2;
      if (d2 > rayon * rayon) return;
      // Ses appuis à lui, dans le même cercle court. Un ennemi seul vaut qu'on
      // fasse deux pas de plus ; un ennemi épaulé par quatre n'en vaut pas un.
      // ET LES NÔTRES QUI SONT DÉJÀ DESSUS, qui n'étaient comptés nulle part.
      let siens = 0, miens = 0;
      autour(o.x, o.y, RAYON_LOCAL, (v) => {
        if (v === o || v === h || !memeEspace(o, v) || !pese(v)) return;
        if ((v.x - o.x) ** 2 + (v.y - o.y) ** 2 > RAYON_LOCAL * RAYON_LOCAL) return;
        if (v.camp === o.camp) siens++; else if (v.camp === h.camp) miens++;
      });
      // ---- LA FLEMME, ET C'EST UNE VRAIE RÈGLE -----------------------------
      // On ne dépense pas son souffle pour rien. Un homme déjà entouré de cinq
      // des nôtres est un homme mort sans moi : y aller ne hâte pas sa chute
      // — il n'y a pas la place pour six lames autour d'un corps —, ça me coûte
      // la course, ça me sort de mon rang, et ça laisse un trou où j'étais.
      //
      // Ce que ça produit à l'œil est tout le point : sans elle, `proieProche`
      // fabriquait des grumeaux. Le premier isolé repéré aspirait tout ce qui
      // passait à cinq mètres, la ligne se vidait par paquets vers un seul
      // homme, et l'on voyait quinze assaillants tourner autour d'un cadavre
      // pendant que trente mètres de front restaient sans personne. Avec elle,
      // l'effort se RÉPARTIT tout seul : dès qu'une proie est servie, la
      // suivante devient la moins chère, et le front se remplit de proche en
      // proche sans que rien ne l'ordonne.
      //
      // C'est aussi la première pierre d'un biais qui a sa place partout ici :
      // un homme préfère ne rien faire, et il faut une raison pour qu'il bouge.
      // ON NE LÂCHE PAS L'HOMME QU'ON A DÉJÀ EN FACE, et c'est pour ça que
      // l'encombrement ne se compte pas sur lui. La flemme dit où l'on VA,
      // jamais d'où l'on part : sans cette exception, le cinquième arrivant
      // faisait décrocher les quatre autres, qui revenaient au battement
      // suivant puisque la place était libre — l'oscillation que l'hystérésis
      // et le temps de décision ont coûté si cher à supprimer ailleurs.
      const tenu = o === h.cible && h.etat === "melee";
      // ---- DEUX COMPTES, ET NON UN — ILS N'ONT PAS LA MÊME MONNAIE ---------
      // LA FAUTE ÉTAIT ICI, ET ELLE A ARRÊTÉ LA BATAILLE. Les deux termes
      // étaient additionnés dans un seul score, et ce score servait à la fois à
      // CLASSER les proies et à décider si l'on y allait. Or ils ne disent pas
      // la même chose :
      //
      //   `siens` dit si cet ennemi-là est un BON CHOIX — épaulé par quatre, il
      //   vaut moins qu'un isolé. C'est une préférence entre des proies.
      //   `miens` et la distance disent ce que la course ME COÛTE. C'est de
      //   l'effort, et c'est la seule chose qu'on ait le droit de comparer à
      //   des jambes.
      //
      // Les mélanger a produit ceci : un défenseur tenant son rang a TOUJOURS
      // cinq à dix voisins, donc un score de huit à seize mètres avant qu'on
      // ait fait un pas — au-dessus du budget d'un homme en marche (8,4 m).
      // `proieProche` rendait donc `null` pour toute la ligne adverse, personne
      // n'entrait au contact, et l'assaut traversait la ville sans se battre.
      // La leçon est celle que le fichier répète partout : une monnaie
      // physique ne se mélange pas à une préférence, même quand les deux
      // s'écrivent en mètres.
      // QUATRE APPUIS CONTRE QUATRE APPUIS, ÇA S'ANNULE. C'est ce qui manquait,
      // et c'est la vraie forme de la règle. « Un ennemi épaulé par quatre n'en
      // vaut pas un » n'est vrai que dit d'UN HOMME SEUL. Adossé à quatre des
      // siens, le même n'a aucune raison de reculer devant quatre : c'est une
      // ligne contre une ligne, et c'est exactement le cas normal d'une
      // bataille rangée.
      //
      // Pris en absolu, ce terme rendait donc toute troupe en ordre serré
      // inattaquable — l'assaut traversait la ville sans se battre, faute de
      // trouver un seul défenseur qui ne fût pas épaulé. Le comparatif remet
      // les choses d'aplomb : ce qui compte n'est pas ce qu'il a, c'est ce
      // qu'il a DE PLUS QUE MOI.
      //
      // Plancher à zéro, et pas de prime au surnombre : être mieux entouré que
      // lui ne rend pas la proie moins chère que si l'on était à égalité. Le
      // profit d'être plus nombreux se prend au combat (`PARADE`, `PRESSE`, le
      // revers), pas au choix de la cible — sinon on le compterait deux fois.
      const appui = h.cercle ? h.cercle.amis : 0;
      const effort = Math.sqrt(d2) + (tenu ? 0 : miens * miens * ENCOMBRE)
                   + Math.max(0, siens - appui) * 1.6;  // une allonge par appui de trop
      if (effort < best) { best = effort; m = o; tenue = tenu; cher = effort; }
    });
    // LE BUDGET, ET IL EST EN JAMBES. On garde ce qu'on tient déjà quoi qu'il
    // en coûte — on ne quitte pas un homme parce qu'on est fatigué de lui.
    // ET C'EST `cher` QU'ON PÈSE, PAS `best` : l'effort de la retenue élue, et
    // non son score de préférence. Sur le test d'entrée en mêlée — un rayon de
    // 2,2 m —, l'effort d'un voisin immédiat vaut au plus deux mètres, donc
    // même un homme à bout va au contact de ce qui est sous son nez. Le budget
    // ne mord que sur la COURSE : franchir douze mètres pour un isolé est un
    // luxe de gens frais, et c'est tout ce qu'on voulait dire.
    if (!m || tenue) return m;
    const vent = h.souffle === undefined ? 1 : h.souffle;
    return cher <= EFFORT_NU + EFFORT_VIF * vent ? m : null;
  }

  // ---- CE QU'UN HOMME VOIT AUTOUR DE LUI -----------------------------------
  // TOUT CE QUI SUIT TIENT SUR UNE SEULE MESURE : combien nous sommes, combien
  // ils sont, dans les cinq mètres. C'est ce qu'un homme au contact perçoit
  // réellement — pas l'ordre de bataille, pas le plan, pas le nombre des ailes :
  // qui est à portée de bras de lui et de qui.
  //
  // Elle sert trois choses qui étaient absentes, et qui sont ce qui fait qu'une
  // mêlée ressemble à une mêlée plutôt qu'à deux files qui s'entre-dévorent :
  // on ne s'avance pas sans être le plus fort ICI, on décroche quand on est
  // entamé, et l'on se jette à plusieurs sur celui qui s'est isolé.
  //
  // Le rayon est court exprès. À cinq mètres on parle de ses voisins immédiats
  // — trois pas — et non d'une portion de ligne : c'est la maille à laquelle un
  // homme décide, et c'est aussi la seule à laquelle la décision reste locale
  // (donc émergente) au lieu d'être un ordre déguisé.
  const RAYON_LOCAL  = 5;
  // ---- LE SEUIL D'ENTAME SE LIT AVEC `PV`, ET IL A FAILLI TOUT CASSER -------
  // Il valait 0,5 — « sous la moitié de ses points, on décroche » —, écrit pour
  // trois cents points de vie où la moitié faisait SEPT COUPS encaissés. À
  // trente points, la moitié fait quinze, et le dégât minimum d'un coup en
  // cloche vaut quinze aussi : TOUT HOMME TOUCHÉ UNE FOIS devenait entamé, pour
  // le reste de la nuit.
  //
  // Ce que ça donnait à l'écran est ce qu'on a vu : des hommes plantés à un
  // mètre d'un ennemi sans le frapper. L'entamé part dans la branche « cède le
  // pas », qui recule à 0,59 m/s en se mêlant au barycentre des siens — donc il
  // ne bouge presque pas, ne frappe plus, et tient position au contact. Une
  // ligne entière de statues, et pas une once de combat.
  //
  // 0,2 — six points. Il faut avoir pris vingt-quatre des trente pour cela,
  // c'est-à-dire un mauvais coup et non pas un coup. La règle retrouve ce
  // qu'elle voulait dire : ce n'est pas « blessé », c'est « à bout ».
  const SEUIL_RECUL  = 0.2;

  // Un homme COMPTE s'il peut encore peser : ni mort, ni à terre, ni en fuite,
  // ni en train de rentrer. Compter les corps ferait qu'un tas de morts amis
  // donne du courage, ce qui est l'inverse de la vérité.
  const pese = (o) => o.etat !== "mort" && o.etat !== "blesse" &&
                      o.etat !== "deroute" && o.etat !== "rentre" &&
                      o.etat !== "prisonnier";

  // Elle rend aussi le BARYCENTRE DES AMIS, parce qu'elle les parcourt déjà :
  // c'est ce vers quoi on se serre quand ça tourne mal (voir `serrer`), et le
  // calculer ailleurs coûterait un second balayage pour les mêmes hommes.
  function balance(h, rayon) {
    let amis = 0, ennemis = 0, ax = 0, ay = 0, reculent = 0;
    let mesAmis = 0, monAx = 0, monAy = 0;
    autour(h.x, h.y, rayon, (o) => {
      if (o === h || !memeEspace(h, o) || !pese(o)) return;
      const d = (o.x - h.x) ** 2 + (o.y - h.y) ** 2;
      if (d > rayon * rayon) return;
      if (o.camp === h.camp) {
        amis++; ax += o.x; ay += o.y;
        // « Les miens » n'est pas synonyme de « mon camp ». Dans une rue où
        // deux troupes se croisent, l'homme se resserre d'abord sur ceux de
        // son unité stable ; les autres ne deviennent pas ses camarades par
        // simple proximité.
        if (h.formation >= 0 && o.formation === h.formation) {
          mesAmis++; monAx += o.x; monAy += o.y;
        }
        // CE QUE FONT LES SIENS, et pas seulement combien ils sont. On le
        // compte ici parce qu'on les a déjà sous la main ; c'est de ça que se
        // nourrit la contagion (voir `decider`).
        if (o.recule) reculent++;
      } else ennemis++;
    });
    return { amis, ennemis, reculent, mesAmis,
             ax: amis ? ax / amis : h.x, ay: amis ? ay / amis : h.y,
             monAx: mesAmis ? monAx / mesAmis : h.x,
             monAy: mesAmis ? monAy / mesAmis : h.y };
  }

  // ---- ON SE COLLE À SES POTES QUAND ÇA TOURNE MAL --------------------------
  // C'EST CE QUI FAIT LES LIGNES, et c'est le comportement qui manquait. Les
  // trois autres règles disent quand on avance, quand on recule, sur qui on
  // frappe — aucune ne dit avec QUI l'on se tient. Sans elle, une troupe qui
  // s'arrête est un nuage de points isolés dont chacun se fait manger à son
  // tour par la règle de la chasse à l'isolé.
  //
  // Le grégarisme ne s'allume QUE dans le danger, et c'est le point : hors de
  // portée d'un ennemi, un homme suit son chemin et sa colonne. Dès qu'il en
  // voit un, il cherche l'épaule de son voisin — c'est le réflexe le mieux
  // documenté d'un homme en armes, et il n'a jamais eu besoin d'être ordonné.
  //
  // ET IL Y A UNE DISTANCE DE CONFORT. On se serre jusqu'à l'épaule, pas
  // au-delà : passé ce point on se repousse, sinon toute une aile s'effondre en
  // un seul tas et le front de sept hommes n'a plus de sens. C'est cette
  // double butée — attirance au loin, répulsion au contact — qui produit une
  // LIGNE plutôt qu'un amas, sans qu'on ait à dessiner la moindre formation.
  const COUDE = EPAULE * 1.5;     // l'espace qu'on laisse à son voisin

  function serrer(h, b, dt) {
    if (!b.amis) return false;
    const ax = b.mesAmis ? b.monAx : b.ax;
    const ay = b.mesAmis ? b.monAy : b.ay;
    const dx = ax - h.x, dy = ay - h.y;
    const d = Math.hypot(dx, dy);
    if (d < 1e-3) return false;
    // Trop loin : on se rapproche. Trop près : on s'écarte. Entre les deux, on
    // ne bouge pas — et c'est là que la ligne se tient.
    if (d > COUDE * 2) { versLe(h, b.ax, b.ay, MARCHE, dt); return true; }
    if (d < COUDE) {
      versLe(h, h.x - dx / d * 4, h.y - dy / d * 4, MARCHE * .5, dt);
      return true;
    }
    return false;
  }

  // AVOIR L'AVANTAGE, C'EST ÊTRE PLUS NOMBREUX, soi compris. À un contre un on
  // n'avance pas : on attend que quelqu'un arrive. C'est ce qui fait qu'une
  // ligne se forme au lieu de se dissoudre en duels, et ça ne coûte pas une
  // ligne de code de plus que la comparaison.
  // LA TREMPE COMPTE COMME DES HOMMES, et c'est la façon la plus honnête de la
  // faire entrer : celui qui a du cœur se compte pour un et demi, celui qui n'en
  // a pas pour une moitié. On ne touche à aucun seuil — on change ce qu'il VOIT
  // dans son cercle, et tout le reste en découle sans une ligne de plus.
  const avantage = (b, h) => b.amis + 1 + (h ? h.trempe : 0) > b.ennemis;

  // ---- ON NE CHANGE PAS D'AVIS SOIXANTE FOIS PAR SECONDE --------------------
  // LE TREMBLEMENT VENAIT D'ICI, et c'était une faute de conception, pas un
  // défaut d'affichage. Les trois règles au-dessus se lisent sur un seuil net :
  // un homme à égalité exacte le franchit dans un sens à un battement, dans
  // l'autre au suivant, et l'on obtient une bataille de points qui vibrent sur
  // place. Personne ne se comporte comme ça — on avance ou on recule, et l'on
  // s'y tient un moment avant de se raviser.
  //
  // Deux remèdes ensemble, parce qu'aucun des deux ne suffit :
  //
  //   L'HYSTÉRÉSIS — il faut un avantage NET pour entrer et un désavantage NET
  //   pour lâcher. Entre les deux, on garde la décision d'avant. C'est ce qui
  //   supprime l'oscillation à la frontière, là où elle naît.
  //
  //   LE TEMPS DE DÉCISION — même net, on ne se ravise pas avant un tiers de
  //   seconde. Deux hommes qui se croisent ne doivent pas se faire changer
  //   d'avis mutuellement à chaque image ; et ça borne le coût, puisqu'on ne
  //   recompte plus les voisins qu'à ce rythme-là.
  const MARGE_TENIR = 1;      // il faut un de plus pour changer d'avis
  // Le délai entre deux revirements n'est plus une constante : c'est `oeil(h)`,
  // propre à chaque homme, à sa vivacité et à son souffle. Voir sa déclaration.

  // ---- ON SUIT SES POTES ----------------------------------------------------
  // ET C'EST CE QUI FAIT D'UNE DÉCISION INDIVIDUELLE UN MOUVEMENT. Jusqu'ici
  // chaque homme comptait des têtes et tranchait seul : deux voisins dans la
  // même situation prenaient la même décision par coïncidence, jamais parce
  // qu'ils se voyaient. Or ce n'est pas ainsi qu'une ligne rompt — elle rompt
  // d'un bout, et le reste suit parce qu'il voit partir le premier.
  //
  // Ce que voir ses voisins reculer change : LE PRIX DE SA PROPRE DÉCISION. On
  // ne force personne — le nombre commande toujours —, on rend seulement plus
  // facile de partir quand les siens partent, et plus difficile d'y retourner
  // seul. Un homme entouré de gens qui tiennent hésitera à lâcher ; le même,
  // entouré de dos, lâchera pour beaucoup moins.
  //
  // BORNÉ À UN HOMME, et c'est important : la contagion déplace la marge d'une
  // unité, pas de dix. Sans cette borne, un seul qui recule fait tourner une
  // aile entière à l'image suivante — ce qui existe (c'est la panique) mais qui
  // est déjà modélisé ailleurs, par la morale et la déroute. Ici on veut la
  // pente, pas l'avalanche ; et l'hystérésis plus le tiers de seconde de
  // le temps de réaction de chacun empêchent la cascade instantanée — mieux :
  // comme personne ne s'aperçoit de rien au même instant, la pente a le temps
  // de se voir descendre.
  // ---- ON NE S'ARRÊTE PAS DE FUIR PARCE QU'UN AMI EST PASSÉ -----------------
  // UNE FUITE QUI S'INTERROMPT AU PREMIER RÉPIT N'EST PAS UNE FUITE. Avec la
  // seule hystérésis, un homme qui part en courant croise deux des siens trois
  // mètres plus loin, retrouve l'avantage local pendant un tiers de seconde, et
  // fait demi-tour vers ce qui vient de le mettre en déroute. Personne ne fait
  // ça — on court, et l'on ne se retourne que lorsqu'on ne voit plus personne.
  //
  // Deux conditions, et il faut les DEUX pour s'arrêter : vingt secondes au
  // moins, et plus rien en vue. Le temps seul ne suffirait pas (on s'arrêterait
  // nez à nez avec ses poursuivants) ; la vue seule non plus (un pilier, un
  // coude de rue, et l'on repartirait au combat après deux pas).
  //
  // TRENTE MÈTRES, de nuit, dans une rue : c'est à peu près où l'on cesse de
  // distinguer qui est derrière soi. Le contrôle est throttlé par son œil
  // comme le reste — un balayage à trente mètres est cher, et le refaire vingt
  // fois par seconde pour chaque fuyard le serait beaucoup trop.
  // Nommées pour le SOLDAT : `FUITE_MIN` existe déjà et appartient aux
  // bourgeois — douze secondes avant qu'un habitant songe à rentrer chez lui.
  // Ce n'est pas la même fuite et ce n'est pas le même homme.
  // ---- CE N'EST PAS UNE FUITE, C'EST UN PAS EN ARRIÈRE ----------------------
  // ON S'ÉTAIT TROMPÉ DE GESTE, ET DEUX FOIS DE SUITE. D'abord vingt secondes
  // de course sourde ; puis quinze mètres de décrochage. Les deux racontaient
  // la même chose fausse : qu'un homme pressé par le nombre S'EN VA. Il ne s'en
  // va pas. Il recule de deux pas, il garde son fer devant lui, il regarde si
  // quelqu'un vient l'épauler — et il n'a quitté ni sa ligne ni son camp.
  //
  // TROIS CONSÉQUENCES, ET IL FAUT LES TENIR ENSEMBLE :
  //
  //   IL NE CHANGE PAS DE COULEUR. Plus d'état `repli` ici : il reste `tient`,
  //   dans la teinte pleine de son camp. Le délavage doit rester réservé à ceux
  //   qui s'en vont pour de bon, sinon un plan où la moitié de la ligne pâlit
  //   toutes les dix secondes ne dit plus rien du tout.
  //
  //   IL NE COURT PAS. Plus de `FUITE` : c'est `MARCHE`, et `versLe` la ramène
  //   à 45 % puisqu'il va à reculons. Cinq mètres lui coûtent donc une bonne
  //   dizaine de secondes s'il les fait en entier — ce qui n'arrivera presque
  //   jamais, et c'est le point.
  //
  //   CE N'EST PLUS UNE DISTANCE, C'EST UNE DURÉE — parce qu'un homme qui
  //   recule ne se dit pas « cinq mètres », il se dit « le temps de voir ».
  //   Les cinq mètres restent, mais comme DIRECTION : le point vers lequel il
  //   va, qu'il n'atteindra pas.
  //
  // LA COURBE EN 1/x, ET C'EST ELLE QUI FAIT LE GRAIN. Log-uniforme entre 0,6 et
  // 6 secondes : médiane 1,9 s, mais une queue longue. La plupart des reculs
  // sont un battement de cœur — on cède le pas, on le reprend — et quelques-uns
  // durent six secondes, qui sont ceux qu'on voit à l'œil parce qu'ils ouvrent
  // un trou. Une loi plate aurait donné des reculs tous pareils ; c'est la
  // dissymétrie qui fait qu'une ligne ondule au lieu de vibrer.
  //
  // BLESSÉ, ON RECULE PLUS LONGTEMPS. Sous la moitié de ses points, ×2,2 : il
  // lui faut le double du temps pour se remettre en face, et c'est ce qui rend
  // une entaille coûteuse même quand elle ne tue pas. C'est la seule modulation
  // — la trempe joue déjà en amont, sur la décision de reculer.
  const RECUL_S   = [0.6, 6];   // log-uniforme : médiane 1,9 s
  const RECUL_M   = 5;          // la direction, pas la distance parcourue
  const RECUL_MAL = 2.2;        // ce que l'entaille ajoute à la durée

  function decider(h, b, dt) {
    h.revoir = (h.revoir || 0) - dt;

    // Celui qui recule : il ne décide rien tant que son pas en arrière n'est
    // pas fini. Après quoi il ne « sort » de rien — il redevient seulement
    // quelqu'un à qui le nombre parle, et c'est le calcul ci-dessous qui
    // tranche, tout de suite. Une ou deux secondes, c'est l'ordre de grandeur
    // d'un coup d'œil : on ne fabrique donc plus d'homme sourd.
    if (h.recule) {
      if (S.temps < h.reculeJusqua) return true;
      h.recule = false;
      h.revoir = 0;            // on ne fait pas attendre la décision d'après
    }

    // Ce que font les siens, ramené à −1 (ils tiennent), 0, ou +1 (ils s'en
    // vont). La majorité décide du signe ; on ne compte pas les voix de plus.
    const part = b.amis ? b.reculent / b.amis : 0;
    const pousse = part > .6 ? 1 : part < .3 ? -1 : 0;
    // Les siens s'en vont : il devient moins cher de partir, plus cher de
    // revenir. Ils tiennent : l'inverse, exactement.
    // Et sa trempe joue dans le même sens des deux côtés : celui qui a du cœur
    // lâche plus tard ET repart plus tôt. C'est ce qui fait qu'un point tient
    // quand tout cède autour de lui — et qu'un autre part avant les siens.
    const t = h.trempe || 0;
    // IL N'Y A PLUS QU'UNE MARGE, et c'est le vrai effet de la règle du dessus :
    // on décide encore quand PARTIR, on ne décide plus quand REVENIR. La
    // seconde marge existait pour ressortir d'une fuite ; c'est la vue qui en
    // décide désormais, et la garder ne ferait qu'un chiffre qui ne sert à rien
    // et qu'on croirait actif.
    const margeReculer = Math.max(0, MARGE_TENIR - pousse + t);
    if (h.revoir > 0) return false;
    if (!(b.ennemis > b.amis + 1 + margeReculer)) return false;
    // Il cède le pas. On tire ici la durée, une fois, et elle ne se retire pas :
    // un homme qui recule ne remet pas son compte à zéro parce qu'on l'a
    // bousculé en route.
    // Log-uniforme — `a·(b/a)^u` —, la seule façon simple d'obtenir une densité
    // en 1/x : beaucoup de courts, quelques longs, et rien d'arbitraire au
    // milieu.
    h.revoir = oeil(h);
    h.recule = true;
    h.reculeJusqua = S.temps + RECUL_S[0] * Math.pow(RECUL_S[1] / RECUL_S[0], R())
                   * (h.pv < h.pvMax * SEUIL_RECUL ? RECUL_MAL : 1);
    return true;
  }

  // CE QUE COÛTE D'ÊTRE ENTOURÉ, et c'est le défenseur qui le paie — pas
  // l'attaquant qui l'encaisserait en prime. Un homme ne frappe pas plus fort
  // parce qu'il a des amis ; c'est sa CIBLE qui cesse de pouvoir parer quand
  // elle en a trois sur le dos. Mettre le bonus du côté de celui qui frappe
  // compterait deux fois le même fait, et rendrait un duel à un contre un plus
  // meurtrier qu'il ne l'est.
  //
  // Le compte est le déficit de la cible : combien d'ennemis elle a de trop
  // dans son cercle, elle-même comprise dans les siens. Zéro quand elle est à
  // égalité ou mieux — on ne récompense pas d'être en surnombre, on punit
  // d'être débordé, ce qui n'est pas symétrique.
  // LE SURNOMBRE JOUE MAINTENANT DEUX FOIS, ET C'EST VOULU. Il ne suffit pas
  // qu'un homme débordé encaisse plus fort : il doit AUSSI être touché plus
  // souvent, et c'est même le plus vrai des deux. Celui qui a trois lames
  // devant lui ne pare pas moins bien, il ne peut pas parer les trois — le fer
  // qui arrive de sa gauche pendant qu'il tient celui de droite n'est pas un
  // coup plus dur, c'est un coup qui ne rencontre rien.
  //
  // On a donc SPLITÉ le même fait en deux moitiés au lieu d'en ajouter une :
  // `PARADE` descend de 0,30 à 0,18, et la différence passe dans `PRESSE`, du
  // côté du toucher. Le débordé meurt à peu près aussi vite qu'avant — mais
  // par des coups plus nombreux et non par des coups surhumains, ce qui se lit
  // tout autrement quand on regarde la mêlée.
  // ═══ LE HARNOIS — LE COUP PORTE, ET IL N'ENTRE PAS ════════════════════════
  //
  // CE QUI MANQUAIT, ET C'EST LE PLUS GROS DÉFAUT MESURÉ DU MODÈLE. `TOUCHE`
  // dit qu'un coup sur deux porte, et un coup porté enlevait 11 à 24 points sur
  // 25 : un homme mourait donc en TROIS COUPS TENTÉS. Mesuré sur deux vintaines
  // au contact : 35 % de morts chez le vainqueur, 50 % chez le vaincu, en trois
  // minutes.
  //
  // Le calcul de Sabin (`docs/recherche/dynamiques-du-combat-medieval.md`, § 0)
  // donne l'ordre de grandeur juste : **moins de 1 % des coups tue**. Sans quoi
  // « chaque armée perdrait 5 % de morts toutes les dix minutes » — or 5 % est
  // le total du VAINQUEUR pour la bataille entière. Nous étions trente à
  // cinquante fois au-dessus.
  //
  // ⚠ ET LE LEVIER N'EST PAS LES POINTS DE VIE. Multiplier la vie par cinq rend
  // les mêmes chiffres (mesuré : 10 % / 20 %, dans la fourchette attestée) mais
  // fabrique des hommes-éponges qui encaissent quinze coups francs. Ce que les
  // sources décrivent est autre chose : le plastron de plate est « pratiquement
  // impénétrable », et les hommes se battent prudemment, « ne portant
  // qu'occasionnellement un coup faible ». Le coup PORTE — on l'entend, il
  // compte, il fatigue, il fait reculer — mais il n'entre pas.
  //
  // D'où deux nombres au lieu d'un gros sac de vie :
  //
  //   PERCE    la part des coups portés qui trouvent un défaut — une jointure,
  //            un visage, une cuisse — et font leur dégât plein.
  //   ARRETE   ce que fait le coup dans tous les autres cas : il meurtrit, il
  //            épuise, il ne tue pas.
  //
  // L'espérance vaut 0,12 + 0,88 × 0,09 ≈ 0,20, soit exactement le cinquième
  // que la mesure réclamait — mais avec la bonne TEXTURE : un homme encaisse
  // longtemps, puis un coup passe et l'affaire est réglée. C'est ce qui donne
  // les longues attentes tendues ponctuées de brèves bouffées de violence, au
  // lieu d'une érosion régulière.
  //
  // La couche 1 le voit sans qu'on la touche : elle lit `avantCoup - o.pv`,
  // donc un coup arrêté lui parvient comme un petit coup et un coup qui perce
  // comme un grand. Le stimulus se règle tout seul.
  const PERCE  = 0.12;   // un coup porté sur huit trouve un défaut du harnois
  const ARRETE = 0.09;   // les sept autres meurtrissent et n'entrent pas
  const PARADE = 0.18;   // par ennemi de trop autour de la cible, sur le DÉGÂT
  const PARADE_MAX = 2;  // au-delà, une lame de plus ne change plus rien
  const PRESSE = 0.22;   // par ennemi de trop autour de la cible, sur le TOUCHER

  // ---- ET LES HOMMES NE SE VALENT PAS ---------------------------------------
  // Le toucher était un 45 % plat : le plus vif du camp et le plus lourd
  // avaient exactement la même main. Les trois déviations existaient pourtant
  // depuis le début — elles décidaient quand un homme s'engage, quand il
  // décroche, à quelle vitesse il s'aperçoit des choses — et aucune ne touchait
  // le seul geste qui tue quelqu'un.
  //
  // C'EST UN RAPPORT, PAS UN BONUS, et c'est ce qui le rend juste : un homme
  // médiocre reste dangereux contre plus médiocre que lui, et le meilleur
  // escrimeur de la porte ne touche pas mieux face à son égal. La déviation
  // seule ne dit rien ; ce qui dit quelque chose, c'est l'écart entre les deux.
  //
  // ⚠ `h.vivacite` EST UN FACTEUR DE DÉLAI, PAS UNE VITESSE. Voir `oeil()` :
  // 0,6 est le vif, 1,4 le lourd, et la valeur MULTIPLIE le temps de réaction.
  // Le rapport s'écrit donc `cible / attaquant` — l'inverse de ce que le nom
  // laisse croire. C'est le seul piège de ce bloc, et il coûte une inversion
  // silencieuse : rien ne planterait, les vifs seraient simplement les moins
  // dangereux de la bataille et personne ne le verrait sur un plan.
  const ADRESSE_MIN = 0.55, ADRESSE_MAX = 1.8;
  const TOUCHE_MAX  = 0.85;   // de face, on ne touche jamais à tous les coups
  // Le flanc est un GRAND avantage, le dos un ÉNORME. Ce ne sont pas deux
  // crans du même réglage : de côté, on pare encore de travers et l'on recule
  // d'un pas ; de dos, on n'a rien à opposer du tout, et la seule question est
  // de savoir si l'on s'est retourné à temps. D'où l'écart entre les deux —
  // et d'où le plafond qui se lève, sans quoi le second se lirait comme le
  // premier.
  const FLANC = 1.55, DOS = 2.9;
  const PLAFOND_DOS = 0.97;

  function frapper(h, o, dt) {
    // LES BRAS TOMBÉS NE FRAPPENT PAS. C'est la seule prise de la couche 1 qui
    // RETIRE une capacité au lieu de dicter une conduite : l'homme continue de
    // faire ce que sa tête a décidé, il ne peut simplement plus s'en servir.
    if (h.brasMorts) return;
    // Il VEUT regarder celui qu'il frappe — un homme au contact ne se tourne
    // pas dans le sens de sa marche, il se tourne vers le fer. Mais il ne s'y
    // tourne pas d'un coup : on pose le CAP, `tourner` fait le reste au pas que
    // le poids de l'arme autorise.
    const ex = o.x - h.x, ey = o.y - h.y, en = Math.hypot(ex, ey);
    if (en > .01) { h.cx = ex / en; h.cy = ey / en; }
    const arme = h.arme || ARME_NUE;
    h.prochain -= dt;
    if (h.prochain > 0) return;
    // ---- ET LE COUP NE PART QUE SI LE FER EST DESSUS -------------------------
    // C'est ici que le poids de l'arme cesse d'être une jolie animation et
    // devient une règle. Tant qu'il n'a pas ramené sa pointe dans son secteur,
    // il ne frappe pas — il tourne, et ça prend le temps que ça prend : près
    // d'une seconde pour amener trois mètres de frêne sur un homme qui vient
    // de le prendre de flanc, un tiers de seconde pour un coutelas.
    //
    // ⚠ LA CADENCE NE SE CAPITALISE PAS PENDANT LA ROTATION, et c'est la seule
    // chose à ne pas rater ici. Laisser `prochain` descendre en négatif pendant
    // qu'il se tourne lui rendrait, à l'instant où il arrive en face, autant de
    // coups qu'il a attendu de cadences — soit un homme qui perd son temps à
    // pivoter puis qui frappe trois fois dans la même image. On le tient donc à
    // zéro : il est PRÊT, il n'est pas EN AVANCE.
    if (!peutFrapper(h, o, arme)) {
      h.prochain = 0;
      return;
    }
    // LA CADENCE S'ALLONGE QUAND LE BRAS PÈSE. C'est ici que le souffle se
    // paie le plus cher, et c'est juste : on ne frappe pas moins fort quand on
    // est épuisé, on frappe MOINS SOUVENT.
    h.prochain += arme.cadence / vigueur(h);
    h.coupsTentes++;
    h.dernierCoup = S.temps;
    // Le cercle de la cible, tel qu'il a été compté à SON battement (voir
    // `h.cercle`). Une image en retard au pire, et gratuite — le recalculer
    // ici ferait un balayage de voisinage par coup porté.
    const c = o.cercle;
    const trop = c ? Math.min(PARADE_MAX, Math.max(0, c.ennemis - (c.amis + 1))) : 0;
    let plafond = TOUCHE_MAX;
    // L'adresse : la lourdeur de la cible sur la sienne, bornée. Aux extrêmes
    // du tirage — un 0,6 contre un 1,4 —, ça vaut 1,8 : le vif touche presque
    // deux fois plus souvent que le lourd, et pas trois. Un homme reste un
    // homme, et le nombre doit continuer de primer sur le talent.
    const adresse = Math.max(ADRESSE_MIN, Math.min(ADRESSE_MAX,
      (o.vivacite || 1) / (h.vivacite || 1)));
    // ---- D'OÙ ON L'ATTAQUE, ET C'EST LE PLUS GROS DES DEUX -------------------
    // On lit le cap de la CIBLE contre la direction d'où on lui arrive. `+1` :
    // elle nous fait face et nous voit venir. `−1` : on est dans son dos, elle
    // regarde ailleurs, et il n'y a plus rien entre notre fer et elle.
    //
    // C'EST CE QUI DONNE UNE GÉOMÉTRIE AU COMBAT, et il n'y en avait aucune. Le
    // surnombre (`trop`) était jusqu'ici la seule façon dont la position entrait
    // dans un coup — un compte de têtes dans un cercle, sans avant ni arrière.
    // Un homme pris à revers était exactement un homme pris de face.
    //
    // CE QUE ÇA PRODUIT TOUT SEUL, ET QUI EST LE VRAI GAIN : un homme engagé
    // TOURNE SON CAP VERS CELUI QU'IL FRAPPE. Donc le deuxième assaillant
    // arrive presque toujours de son flanc, et le troisième de son dos —
    // gratuitement, sans qu'une ligne l'organise. Le surnombre cesse d'être un
    // coefficient et devient ce qu'il est : des gens qui vous prennent par les
    // côtés pendant que vous en tenez un. Et l'homme qui décroche en gardant la
    // face reçoit ses coups de face ; celui qui tourne le dos les reçoit dans
    // le dos, à l'allure où il court. Les deux règles se tiennent.
    let revers = 1;
    if (o.fx || o.fy) {
      const dx = h.x - o.x, dy = h.y - o.y, dn = Math.hypot(dx, dy) || 1;
      const cos = o.fx * dx / dn + o.fy * dy / dn;
      const t = (1 - cos) / 2;                   // 0 de face, ½ de côté, 1 de dos
      revers = t <= .5 ? 1 + (FLANC - 1) * t * 2
                       : FLANC + (DOS - FLANC) * (t - .5) * 2;
      // LE PLAFOND SE LÈVE AVEC LUI, sinon le dos ne vaudrait rien de plus que
      // le flanc : à 0,85 les deux butent au même endroit et « énorme » se lit
      // comme « grand ». Un homme qui ne vous voit pas ne pare pas par miracle
      // — on ne lui laisse qu'un souffle de chance, pas un quart.
      plafond = TOUCHE_MAX + (PLAFOND_DOS - TOUCHE_MAX) * t;
    }
    // PLAFOND, PARCE QUE RIEN N'EST ACQUIS. Au bout des deux effets — le vif
    // contre le lourd, débordé de deux — le produit passe 1 et le coup ne se
    // tire plus : il tombe. Un homme même pris à trois se retourne encore par
    // hasard, et une mêlée où un camp touche à tous les coups n'est plus une
    // mêlée, c'est une exécution qui dure le temps des cadences.
    const tire = R(), seuil = Math.min(plafond, TOUCHE * adresse * revers * (1 + PRESSE * trop));
    if (tire > seuil) {
      // LE COUP QUI FROLE — pour la couche 1. C'est le stimulus le plus violent
      // du repertoire : le coup recu est fini, le coup manque annonce le
      // suivant. Le modele n'a pas de trajectoire de lame, donc pas d'ecart en
      // metres — mais il a mieux, DE COMBIEN LE JET A MANQUE SON SEUIL.
      if (o.recu && o.recu.length < 8 && window.Corps)
        o.recu.push(Object.assign(
          window.Corps.coupFrole(tire, seuil, enFace(o, h)), { t: S.temps }));
      // LE COUP QUI NE PORTE PAS S'ENTEND — c'est même le son le plus fréquent
      // d'une mêlée, et celui qui la fait exister. `metal` à 1 : du fer sur du
      // fer, brillant et long. Voir `son.js`. On ne tire RIEN au sort ici : le
      // hasard de la bataille est semé et rejouable, et une seule ligne de son
      // qui appellerait `R()` décalerait tout le déroulé. La dispersion d'un
      // choc à l'autre est fabriquée dans le module de son, avec son propre
      // hasard, qui n'a de conséquence sur rien.
      if (window.Son) Son.dire({ famille: "fer", x: o.x, y: o.y,
                                 force: 0.45 + 0.3 * revers, metal: 1 });
      return;
    }
    // LE BOUCLIER EST DU CÔTÉ DE CELUI QUI ENCAISSE, et il se cumule à la
    // parade dégradée au lieu de l'annuler : il rend un cinquième des coups,
    // même quand on est pris à trois. C'est peu, et c'est ce qu'on veut — un
    // bouclier ne sauve pas un homme débordé, il lui achète un coup de plus.
    const avantCoup = o.pv;
    h.coupsPortes++;
    // Une pique ne reçoit pas un bonus de classe contre « cavalerie ». Elle
    // restitue à celui qui arrive l'élan qu'il apporte : pointe en face,
    // piquier presque planté, cavalier encore lancé vers lui. Sans ces trois
    // faits géométriques, c'est une longue lance lente et rien de plus.
    const versPiquier = Math.hypot(o.vx || 0, o.vy || 0) > .01
      ? (((o.vx || 0) * (h.x - o.x) + (o.vy || 0) * (h.y - o.y)) /
         (Math.hypot(o.vx || 0, o.vy || 0) * (Math.hypot(h.x-o.x, h.y-o.y) || 1)))
      : 0;
    const contreCharge = arme === ARMES.pique && o.montureCombat &&
      (h.vit || 0) < .75 && (o.vit || 0) > 2.2 && versPiquier > .45;
    if (contreCharge) compte.contreCharges++;
    o.pv -= cloche(arme.degat[0], arme.degat[1])
          * (R() < PERCE ? 1 : ARRETE)
          * (1 + PARADE * trop)
          * ((o.arme && o.arme.garde) || 1)
          * (contreCharge ? 1 + Math.min(1.5, (o.vit || 0) / 4) : 1);
    if (o.recu && o.recu.length < 8 && window.Corps)
      o.recu.push(Object.assign(
        window.Corps.coupRecu(avantCoup - o.pv, (DEGAT[0] + DEGAT[1]) / 2,
                              enFace(o, h), (o.arme && o.arme.garde) || 1),
        { t: S.temps }));
    // LE COUP QUI PORTE EST SOURD, ET C'EST TOUTE LA DIFFÉRENCE. Le même
    // paramètre `metal` qui valait 1 sur une parade tombe ici vers 0 : pas de
    // résonance, un thud. Ce qu'il reste de métal vient de ce que l'homme
    // porte — un coup sur un écu sonne encore, un coup sur une chemise nue
    // n'est qu'un bruit. C'est le continuum qu'une banque d'échantillons ne
    // donne pas : on n'a pas quatre fichiers, on a un plan.
    if (window.Son) {
      // `garde` est un MULTIPLICATEUR DE DÉGÂT, pas une quantité d'armure :
      // 1 = rien sur le dos, 0,8 = un écu. C'est donc son complément qui dit
      // ce qui sonne, et il faut l'étaler — sans quoi le mieux protégé des
      // hommes vaudrait `metal: 0,07` et l'on n'entendrait aucune différence.
      const garde = (o.arme && o.arme.garde) || 1;
      Son.dire({ famille: "chair", x: o.x, y: o.y,
                 force: 0.5 + 0.4 * revers,
                 metal: Math.min(0.5, (1 - garde) * 2.5) });
    }
    if (o.pv <= 0) tomber(o);
  }

  function tomber(o) {
    o.pv = 0;
    // CELUI QUI TOMBE EST UN STIMULUS POUR SES VOISINS, et le balayage qui
    // applique le CHOC plus bas le fait deja : on ne rebalaie pas, on se
    // greffe. Le cri porte, donc c'est l'ouie â€” le seul canal qui traverse un
    // dos tourne.
    // LE RAYON EST CELUI DE `VUE_MORT`, ET C'EST LA DEPOSE DE `CHOC` QUI L'A
    // TRANCHE : on voyait tomber a dix-huit metres pour la morale et a six pour
    // la couche. Un seul oeil, un seul rayon.
    autour(o.x, o.y, VUE_MORT, (v) => {
      if (v === o || !v.recu || v.recu.length >= 8) return;
      if (v.camp !== o.camp) return;
      const d = Math.hypot(v.x - o.x, v.y - o.y);
      if (d > VUE_MORT) return;
      v.recu.push(Object.assign(
        window.Corps.voisinTombe(d, Math.cos(Math.atan2(o.y - v.y, o.x - v.x)), true),
        { t: S.temps }));
    });
    // UN HOMME QUI TOMBE CRIE, et c'est le seul son de la bataille qui porte à
    // trois cents mètres — d'où la criticité la plus haute après la panique :
    // c'est par là qu'on apprend, de loin, que quelque chose cède. Le cri se
    // pousse dans chacune des deux branches ci-dessous et non avant elles :
    // un homme qui meurt et un homme qui reste par terre ne font pas le même
    // bruit, et c'est le tirage qui vient de trancher lequel il est.
    // Deux hommes sur cinq restent en vie par terre. Le tirage se fait ICI et
    // une seule fois : un blessé n'est jamais re-visé (il sort des cibles), et
    // c'est la plaie, plus tard, qui dira s'il se relève ou non.
    if (R() < PART_BLESSE) {
      o.etat = "blesse";
      o.saigne = cloche(SAIGNE[0], SAIGNE[1]);
      compte.blesses++;
      // LE BLESSÉ EST LE SEUL FAIT QU'ON ÉCRIVE UN PAR UN, et c'est assumé :
      // c'est la scène qu'on vient chercher. Il ne bouge plus, il est à une
      // adresse, il parle, et il a un chef dont il peut donner le nom.
      noter("blesse", o.x, o.y, { dit: {
        camp: o.camp, escouade: o.camp === "assaut" ? o.escouade : null,
        chef: !!o.chef,
      } });
      if (window.Son) Son.dire({ famille: "cri-blesse", x: o.x, y: o.y, force: 0.8 });
    } else {
      if (window.Son) Son.dire({ famille: "cri-mort", x: o.x, y: o.y, force: 0.95 });
      achever(o);
    }
    // ON NE VOIT PLUS TOMBER DEUX FOIS. `CHOC` frappait la morale a dix-huit
    // metres ; le stimulus `voisinTombe` etait emis a six, dans `frapper`. Deux
    // rayons pour un seul oeil, donc deux modeles de la vue — et la depose de
    // `morale` tranche : il n'en reste qu'un, et c'est `VUE_MORT`, qui portait
    // la mesure. Le stimulus est donc emis LA-BAS avec ce rayon-ci.
    // Le premier sang de la journée, et la tête d'une escouade : deux faits
    // qu'on ne peut pas reconstituer après coup, et qui datent la bataille.
    noter("premier-sang", o.x, o.y, { clef: "premier-sang", dit: { camp: o.camp } });
    // QUI TOMBE MÉRITE UNE LIGNE, MAIS PAS N'IMPORTE QUI. À quatre cent
    // soixante-quinze escouades, un fait par chef d'escouade ferait quatre cent
    // soixante-quinze lignes que personne ne lira jamais — et l'on aurait
    // enrichi un journal de débogage en croyant écrire un document. On n'écrit
    // donc que ce qui CASSE LA CHAÎNE : un capitaine, qui emporte sa bannière ;
    // une tête, dont le corps n'aura plus jamais d'ordre neuf ; ou quelqu'un
    // qui a un nom, parce qu'un nom est ce qui rend une mort lisible.
    if (o.nom || o.capitaine || o.tete)
      noter(o.tete ? "tete-tombe" : "chef-tombe", o.x, o.y,
        { clef: (o.tete ? "tete:" : "chef:") + o.camp + ":" + (o.nom || o.aile),
          dit: { camp: o.camp, nom: o.nom, corps: o.corps, aile: o.aile,
                 escouade: o.escouade, mort: o.etat === "mort" } });
  }

  /** La plaie a tranché, ou le coup était franc. */
  function achever(o) {
    if (o.etat === "blesse") compte.blesses--;
    o.etat = "mort"; o.pv = 0;
    // L'HEURE DE LA CHUTE, et elle ne sert qu'à l'œil : un mort frais et un
    // mort d'il y a une heure étaient le même carré gris, si bien que le sol
    // se couvrait de confettis qu'on ne savait plus lire. Avec elle, le corps
    // se fond peu à peu dans le sol, et la densité des morts devient enfin ce
    // qu'elle devrait être — la carte de là où ça a cogné.
    o.tombe = S.temps;
    compte.morts++;
  }

  // UN BLESSÉ NE MEURT PAS FORCÉMENT, et il ne faut pas qu'il meure tous. Une
  // plaie qui s'arrête, c'est un homme qu'on retrouve au matin — c'est-à-dire
  // quelqu'un à qui la troupe peut parler trois jours plus tard. Les faire tous
  // mourir au bout de leur compte reviendrait à avoir écrit un délai de mort,
  // ce qui n'apporte rien à personne.
  function saigner(h, dt) {
    if (h.saigne === Infinity) return;
    h.saigne -= dt;
    if (h.saigne > 0) return;
    if (R() < PART_MEURT) {
      achever(h);
      noter("blesse-succombe", h.x, h.y, { dit: { camp: h.camp } });
    } else {
      h.saigne = Infinity;          // il tiendra jusqu'au matin
      noter("blesse-tient", h.x, h.y, { dit: { camp: h.camp } });
    }
  }

  // ═══ ROMPRE — LE SEUL ENDROIT PAR OÙ L'ON PART ═══════════════════════════
  // Trois lignes différentes basculaient un homme en `deroute`, chacune avec sa
  // copie de `compte.fuyards++`, et AUCUNE ne prévenait les voisins. Or « les
  // siens s'en vont » est, de tout le répertoire de la couche 1, le plus
  // puissant déclencheur de fuite qui existe — et c'est la contagion elle-même :
  //
  //   ce n'est pas COMBIEN sont partis, c'est QUELLE PROPORTION VIENT DE
  //   PARTIR. Trois hommes qui s'en vont d'un groupe de quatre est une
  //   catastrophe ; les mêmes trois d'un groupe de trente n'est rien.
  //
  // Sans ce stimulus, une ligne ne se défaisait pas EN VAGUE : chacun rompait
  // dans son coin, quand son propre compteur passait sous le seuil. La
  // propagation de proche en proche — celle qu'on voit sur tous les champs et
  // qu'on n'obtenait par aucun réglage — sort d'ici et de nulle part ailleurs.
  //
  // LE RAYON EST CELUI DE `VUE_MORT`, ET C'EST DÉLIBÉRÉ : on voit un homme
  // partir aussi loin qu'on le voit tomber. Deux rayons pour un même œil
  // seraient deux modèles de la vue. `voisinTombe` a été aligné dessus lors de
  // la dépose de `CHOC`.
  function hasardFuite(h, sel) {
    const no = +(String(h.debugId || "0").match(/\d+/) || [0])[0];
    let x = (no ^ sel) >>> 0;
    x = Math.imul(x ^ (x >>> 16), 0x45d9f3b) >>> 0;
    x = Math.imul(x ^ (x >>> 16), 0x45d9f3b) >>> 0;
    return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
  }

  function doctrineDe(h) {
    const u = formationDe(h), ordre = u && u.doctrine;
    return ordre && DOCTRINES[ordre.id] || null;
  }

  function doctrineReclame(h) {
    const d = doctrineDe(h);
    if (!d || h.tete || h.roi || h.hors || h.etat === "deroute" ||
        h.etat === "mort" || h.etat === "blesse" || h.etat === "prisonnier") return false;
    if (S.temps > (h.menaceJus || -Infinity) || (h.menaceExterieure || 0) < .12)
      return false;
    if (d.danger && h.menaceGenre !== d.danger) return false;
    // Au contact, l'ordre ouvert n'est plus la bonne réponse. Le fer local a
    // priorité sans que le scénario ait à retirer la doctrine.
    if (h.cercle && h.cercle.ennemis > 0) return false;
    // C'est le verrou essentiel : l'ordre ne déplace l'homme que s'il a gagné
    // l'arbitrage commun. Corps, réflexion ou envie peuvent donc le reprendre.
    return h.conduit === "ordre";
  }

  function cibleOrdreOuvert(h, d) {
    const cote = hasardFuite(h, 0x7f4a7c15) < .5 ? -1 : 1;
    const fuite = Math.atan2(h.y - h.menaceY, h.x - h.menaceX);
    const travers = .92 + hasardFuite(h, 0x6a09e667) * .52;
    const a = fuite + cote * travers;
    const rayon = d.rayonMin + (d.rayonMax - d.rayonMin) *
      hasardFuite(h, 0xbb67ae85);
    // Le masque reste souverain. On tourne progressivement la destination
    // autour de l'homme au lieu de projeter un slot derrière une façade ou
    // dans l'eau.
    for (let k = 0; k < 12; k++) {
      const aa = a + (k ? (k % 2 ? 1 : -1) * Math.ceil(k / 2) * Math.PI / 12 : 0);
      const r = rayon * (1 - Math.floor(k / 6) * .28);
      const x = h.x + Math.cos(aa) * r, y = h.y + Math.sin(aa) * r;
      if (!solConnu() || libreEn(x, y)) return { x, y };
    }
    return { x:h.x, y:h.y };
  }

  function executerDoctrine(h, dt) {
    const d = doctrineDe(h), menace = doctrineReclame(h);
    let e = h.doctrineEtat;
    if (menace) {
      if (!e || e.id !== d.id || e.phase === "finie") {
        const p = cibleOrdreOuvert(h, d);
        e = h.doctrineEtat = { id:d.id, phase:"ecartement", x:p.x, y:p.y,
          commenceA:S.temps, derniereMenace:S.temps };
      } else e.derniereMenace = S.temps;
      h.doctrineActive = true; h.doctrineAgi = true; h.doctrinePhase = e.phase;
      h.cible = null; h.etat = "rassemble";
      if (Math.hypot(h.x - e.x, h.y - e.y) <= 1.2) e.phase = "tenue";
      penser(h, e.phase === "tenue" ? "tenir un intervalle ouvert" : "ouvrir les rangs",
        "l'ordre anti-dragon tient mes jambes", "doctrine de déploiement");
      versLe(h, e.x, e.y, MARCHE * d.vitesse, dt);
      return true;
    }
    if (!e || !d || e.id !== d.id) { h.doctrineActive = false; return false; }
    const depuis = S.temps - e.derniereMenace;
    if (depuis <= d.tenue && h.conduit === "ordre") {
      h.doctrineActive = true; h.doctrinePhase = "tenue";
      h.etat = "rassemble"; versLe(h, e.x, e.y, MARCHE * .7, dt);
      return true;
    }
    if (depuis <= d.tenue + 22 && h.conduit === "ordre") {
      const u = formationDe(h);
      h.doctrineActive = true; h.doctrinePhase = "ralliement";
      h.etat = "rassemble";
      penser(h, "rallier ma vintaine", "le passage est fini et l'ordre le prévoit",
        "doctrine de déploiement");
      if (rassemblerFormation(h, u, MARCHE, dt)) return true;
    }
    e.phase = "finie"; h.doctrineActive = false; h.doctrinePhase = null;
    return false;
  }

  /**
   * Exécute la sortie de la couche 2 quand l'arbitre lui a réellement confié
   * les jambes. Elle ne crée pas une cinquième fuite : elle matérialise le cap
   * que `Reflexion.issue()` a déjà cherché sur le masque.
   */
  function executerReflexion(h, dt) {
    const r = h.l2;
    if (h.conduit !== "reflexion" || !r) return false;
    const issue = r.issue || {};
    if (r.tient < 0 && issue.force > .02 && (issue.x || issue.y)) {
      let dx = issue.x, dy = issue.y;
      // Devant un foyer, « céder » signifie bien gagner de la distance. La
      // réflexion peut garder une composante vers les siens, mais jamais
      // choisir par mélange un cap qui la ramène vers la flamme.
      if (h.menaceGenre === "incendie" && S.temps <= (h.menaceJus || -Infinity)) {
        const ax = h.x - h.menaceX, ay = h.y - h.menaceY;
        const an = Math.hypot(ax, ay) || 1;
        const ux = ax / an, uy = ay / an;
        if (dx * ux + dy * uy < .45) {
          dx = dx * .35 + ux * .65; dy = dy * .35 + uy * .65;
        }
        // Même homme, même biais : la foule ne dessine pas des rayons
        // identiques, mais ne tremble pas non plus à chaque image.
        const a = (hasardFuite(h, 0x51ed270b) * 2 - 1) * .22;
        const c = Math.cos(a), s = Math.sin(a);
        [dx, dy] = [dx * c - dy * s, dx * s + dy * c];
      }
      const n = Math.hypot(dx, dy) || 1;
      dx /= n; dy /= n;
      const portee = 4 + 4 * Math.max(0, h.menaceExterieure || 0);
      let but = { x:h.x + dx * portee, y:h.y + dy * portee };
      if (solConnu() && !libreEn(but.x, but.y)) {
        for (const a of [.42, -.42, .78, -.78]) {
          const c = Math.cos(a), s = Math.sin(a);
          const q = { x:h.x + (dx * c - dy * s) * portee,
                      y:h.y + (dx * s + dy * c) * portee };
          if (libreEn(q.x, q.y)) { but = q; break; }
        }
      }
      h.cible = null; h.etat = "tient";
      versLe(h, but.x, but.y,
             h.menaceGenre === "incendie" ? MARCHE * 1.25 : MARCHE, dt);
      penser(h, h.menaceGenre === "incendie" ? "gagner de l'air loin du feu" : "céder le pas",
             r.idee || "je vois une issue", "réflexion · couche 2");
      return true;
    }
    // Quand la réflexion gagne par patience, rester est une conduite : laisser
    // tomber dans la cascade ferait exécuter l'ordre qu'elle vient de battre.
    h.cible = null; h.etat = "tient";
    penser(h, "attendre une issue", r.idee || "je ne vois rien de mieux",
           "réflexion · couche 2");
    return true;
  }

  function preparationDoctrine(membres, danger) {
    let vivants = 0, prepares = 0, ouverture = 0;
    for (const h of membres || []) {
      if (!h || h.etat === "mort" || h.etat === "blesse" || h.etat === "prisonnier")
        continue;
      vivants++;
      const d = doctrineDe(h);
      if (d && (!danger || d.danger === danger)) {
        prepares++; ouverture += d.ouvertureCollective || 0;
      }
    }
    return vivants ? { part:prepares / vivants, ouverture:ouverture / vivants }
                   : { part:0, ouverture:0 };
  }

  function preparerFuite(h, contexte) {
    const borner = (x) => Math.max(0, Math.min(1, +x || 0));
    const b = h.cercle;
    const submersion = b
      ? borner((b.ennemis - b.amis) / Math.max(1, b.ennemis + b.amis)) : 0;
    const lesion = 1 - Math.max(0, h.pv) / Math.max(1, h.pvMax);
    const externe = S.temps <= (h.menaceJus || -Infinity)
      ? borner(h.menaceExterieure) : 0;
    const donnee = contexte && Number.isFinite(contexte.severite)
      ? borner(contexte.severite) : 0;
    const severite = Math.max(donnee, submersion, lesion * 0.8, externe * 0.8);
    const q = borner((severite - 0.28) / (0.85 - 0.28));
    // Une puissance relative écrasante incline fortement vers « chacun pour
    // soi », elle ne fabrique pas soixante-douze copies. Les bornes gardent
    // une minorité de chaque conduite aux deux extrêmes ; l'identité stable
    // décide laquelle, pas l'ordre des battements.
    const chanceSeul = 0.12 + 0.74 * (q * q * (3 - 2 * q));
    h.fuiteStrategie = hasardFuite(h, 0x9e3779b9) < chanceSeul
      ? "dispersion" : "regroupement";
    h.fuiteDepuis = S.temps; h.fuiteSeverite = severite;
    h.fuiteExterieure = externe > 0;

    let dx = -(h.fx || 1), dy = -(h.fy || 0);
    if (externe > 0) {
      dx = h.x - h.menaceX; dy = h.y - h.menaceY;
    } else {
      const e = ennemiProche(h, 28) || h.cible;
      if (e && e.camp !== h.camp) { dx = h.x - e.x; dy = h.y - e.y; }
    }
    let n = Math.hypot(dx, dy) || 1; dx /= n; dy /= n;
    const ouverture = h.fuiteStrategie === "dispersion" ? 1.05 : 0.48;
    h.fuiteAngle = (hasardFuite(h, 0x85ebca6b) * 2 - 1) * ouverture;
    const c = Math.cos(h.fuiteAngle), s = Math.sin(h.fuiteAngle);
    h.fuiteDx = c * dx - s * dy; h.fuiteDy = s * dx + c * dy;
    h.fuiteGroupeAngle = hasardFuite(h, 0xc2b2ae35) * Math.PI * 2;
    h.fuiteGroupeRayon = 2 + hasardFuite(h, 0x27d4eb2f) * 5;
  }

  function rompre(h, contexte) {
    if (h.etat === "deroute") return;
    preparerFuite(h, contexte);
    h.etat = "deroute";
    compte.fuyards++;
    if (!window.Corps) return;
    // Ses camarades encore en ligne, et lui qui vient d'en sortir. On compte
    // dans le même balayage que l'on notifie — la proportion se calcule sur
    // ceux qui restent, plus un.
    const vus = [];
    autour(h.x, h.y, VUE_MORT, (v) => {
      if (v === h || v.camp !== h.camp || !v.recu || v.recu.length >= 8) return;
      if (v.etat === "mort" || v.etat === "blesse" || v.etat === "deroute") return;
      if ((v.x - h.x) ** 2 + (v.y - h.y) ** 2 > VUE_MORT * VUE_MORT) return;
      vus.push(v);
    });
    for (const v of vus)
      v.recu.push(Object.assign(window.Corps.voisinPart(1, vus.length + 1),
                                { t: S.temps }));
  }

  /**
   * Faire de la rupture un fait d'unité, puis laisser `rompre()` produire les
   * hommes qui courent et la contagion vue par leurs voisins.
   *
   * `part` n'est pas un seuil de pertes : c'est la part du jugement collectif
   * déjà acquise par l'appelant. La progression est appliquée depuis l'arrière
   * de l'unité (`avantX`, `avantY`), conformément au dossier sur la fuite. Le
   * moteur ordinaire conserve ainsi son unique porte de sortie, `rompre`, au
   * lieu qu'une épreuve écrive directement `etat = "deroute"`.
   */
  function appliquerRuptureUnite(membres, options) {
    const o = options || {}, tous = Array.isArray(membres) ? membres.filter(Boolean) : [];
    const bilan = { total: tous.length, deja: 0, nouveaux: 0, rompus: 0 };
    if (!tous.length) return bilan;
    const part = Math.max(0, Math.min(1, +o.part || 0));
    const ax = Number.isFinite(o.avantX) ? o.avantX : 1;
    const ay = Number.isFinite(o.avantY) ? o.avantY : 0;
    const n = Math.hypot(ax, ay) || 1, ux = ax / n, uy = ay / n;
    const actifs = [];
    for (const h of tous) {
      if (h.etat === "deroute") { bilan.deja++; continue; }
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "prisonnier" ||
          h.etat === "rentre") continue;
      actifs.push(h);
    }
    // La cible porte sur l'effectif initial : les morts ne deviennent pas des
    // fuyards de remplacement et une rupture déjà commencée ne peut régresser.
    const cible = Math.ceil(part * tous.length);
    let manque = Math.max(0, cible - bilan.deja);
    actifs.sort((a, b) => (a.x * ux + a.y * uy) - (b.x * ux + b.y * uy));
    for (let i = 0; i < actifs.length && manque > 0; i++, manque--) {
      const h = actifs[i];
      h.ruptureCause = o.cause || "mon unité ne tient plus";
      rompre(h, { severite: o.severite });
      penser(h, "fuir", h.ruptureCause, "rupture d'unité");
      bilan.nouveaux++;
    }
    bilan.rompus = bilan.deja + bilan.nouveaux;
    return bilan;
  }

  /**
   * Le jugement collectif qui manquait au système de fuite.
   *
   * L'appelant ne choisit ni des hommes ni une part de fuyards. Il rapporte
   * seulement ce que l'unité peut juger : quelle part voit la menace, quelle
   * capacité de riposte elle croit avoir, et à quel point la menace a fermé
   * l'espace autour d'elle. Le système conserve le jugement maximal acquis ;
   * une boucle déjà vue ne redevient pas invisible au battement suivant.
   *
   * Les deux bornes de conversion restent une hypothèse de simulation, sans
   * source chiffrée : le dossier établit la causalité et la nature collective,
   * pas le pourcentage exact auquel une ligne médiévale cède.
   */
  function jugerRuptureUnite(membres, situation) {
    const s = situation || {}, borner = (x) => Math.max(0, Math.min(1, +x || 0));
    if (!Array.isArray(membres) || !membres.length)
      return { total: 0, deja: 0, nouveaux: 0, rompus: 0, jugement: 0, part: 0 };
    let j = jugementsRupture.get(membres);
    if (!j) { j = { jugement: 0, part: 0 }; jugementsRupture.set(membres, j); }
    const menaceVue = borner(s.menaceVue);
    const impuissance = 1 - borner(s.riposte);
    const preparation = preparationDoctrine(membres, s.danger);
    // Une ligne ouverte n'abat pas un dragon : `impuissance` ne bouge pas.
    // Elle cesse seulement d'être une cible collective enfermée dans sa propre
    // densité. La rupture individuelle demeure ensuite produite par le corps,
    // les voisins et les blessures exactement comme avant.
    const fermeture = borner(s.fermeture) * (1 - preparation.ouverture);
    const domination = menaceVue * impuissance * fermeture;
    j.jugement = Math.max(j.jugement, domination);
    const t = borner((j.jugement - 0.30) / (0.82 - 0.30));
    const part = t * t * (3 - 2 * t);
    j.part = Math.max(j.part, part);
    const raclee = s.severite == null
      ? borner(0.65 * j.jugement + 0.35 * impuissance * menaceVue)
      : borner(s.severite);
    const bilan = appliquerRuptureUnite(membres, {
      part: j.part, avantX: s.avantX, avantY: s.avantY, cause: s.cause,
      severite: raclee,
    });
    bilan.jugement = j.jugement; bilan.part = j.part; bilan.severite = raclee;
    bilan.preparation = preparation.part;
    bilan.fermetureEffective = fermeture;
    return bilan;
  }

  function protectionVisible(h) {
    let poids = 0, x = 0, y = 0;
    autour(h.x, h.y, 90, (o) => {
      if (o === h || o.camp !== h.camp || !memeEspace(h, o) || !pese(o)) return;
      const d2 = (o.x - h.x) ** 2 + (o.y - h.y) ** 2;
      if (d2 > 90 * 90) return;
      let w = 1;
      if (h.formation >= 0 && o.formation === h.formation) w += 1.5;
      if (o.chef || o.capitaine) w += 3;
      x += o.x * w; y += o.y * w; poids += w;
    });
    if (poids < 2) return null;
    return { x: x / poids, y: y / poids, poids };
  }

  function fuirVersProtection(h, dt) {
    const g = protectionVisible(h);
    if (g) {
      h.fuiteGroupeX = g.x; h.fuiteGroupeY = g.y; h.fuiteGroupeVuA = S.temps;
    }
    if (h.fuiteGroupeX == null || S.temps - h.fuiteGroupeVuA > 7) return false;
    const bx = h.fuiteGroupeX + Math.cos(h.fuiteGroupeAngle) * h.fuiteGroupeRayon;
    const by = h.fuiteGroupeY + Math.sin(h.fuiteGroupeAngle) * h.fuiteGroupeRayon;
    versLe(h, bx, by, FUITE * 0.92, dt);
    return true;
  }

  function fuirSelonCap(h, dt) {
    // Le danger peut bouger, mais un homme qui a choisi « chacun pour soi »
    // ne recalcule pas sa meilleure direction vingt fois par seconde. Plus la
    // raclée perçue était forte, plus le cap acquis pèse longtemps.
    if (S.temps <= (h.menaceJus || -Infinity)) {
      let dx = h.x - h.menaceX, dy = h.y - h.menaceY;
      const n = Math.hypot(dx, dy) || 1; dx /= n; dy /= n;
      const c = Math.cos(h.fuiteAngle), s = Math.sin(h.fuiteAngle);
      const vx = c * dx - s * dy, vy = s * dx + c * dy;
      const tau = h.fuiteStrategie === "dispersion"
        ? 6 + 12 * h.fuiteSeverite : 2.5;
      const a = 1 - Math.exp(-dt / tau);
      h.fuiteDx += (vx - h.fuiteDx) * a;
      h.fuiteDy += (vy - h.fuiteDy) * a;
      const m = Math.hypot(h.fuiteDx, h.fuiteDy) || 1;
      h.fuiteDx /= m; h.fuiteDy /= m;
    }
    versLe(h, h.x + h.fuiteDx * 36, h.y + h.fuiteDy * 36, FUITE, dt);
  }

  // ═══ CE QUI RESTE DE `survie()` — ET C'EST UN FAIT DU MONDE ══════════════
  // TOUT LE RESTE A ÉTÉ DÉPOSÉ. `morale`, `ROMPT`, `CHOC`, `SANG`, `REPRISE`,
  // `PLANCHER_FERME` et les trois planchers d'`humeur` disaient ce que la
  // couche 1 dit mieux : un homme rompt quand son corps prend la main, et le
  // corps prend la main par une glande qui monte en trois secondes et retombe
  // en quarante-cinq. Deux modèles qui décidaient de la même chose ne se
  // départageaient jamais ; on n'en garde qu'un.
  //
  // Ce qui subsiste ici n'est PAS une peur : c'est la charrette qui a versé.
  // Quand il n'y a plus rien autour de quoi rallier, ça ne se négocie avec
  // aucune humeur et aucune glande — c'est le monde qui a changé, pas l'homme.
  // C'est la seule chose de tout le module qui passe par-dessus une conduite,
  // et c'est pour ça qu'elle survit à la dépose.
  // CE QUI TOMBE ET QUI SE VOIT DE LOIN — la banniere abattue, la porte cedee.
  // `CHOC_BANN` retirait vingt centiemes de morale a toute l'aile ; le stimulus
  // fait la meme chose par le bon bout, en passant par l'oeil : il decroit avec
  // la distance, il s'habitue, et un homme qui regarde ailleurs ne le voit pas.
  function signeQuiTombe(h, x, y) {
    if (!window.Corps || !h.recu || h.recu.length >= 8) return;
    h.recu.push(Object.assign(
      window.Corps.signeTombe(Math.hypot(h.x - x, h.y - y), VUE_BANNIERE),
      { t: S.temps }));
  }

  function survie(h) {
    if (S.arret && h.camp === "assaut") rompre(h);
  }

  // UNE PENSÉE EST LA TRACE D'UNE DÉCISION, PAS UNE LIGNE DE STYLE. Tous les
  // retours de `soldat()` passent par ici au moment où leur branche est élue.
  // On peut donc contester la cause affichée en revenant exactement au système
  // qui l'a fournie, sans deviner depuis l'animation ce qui a dû se passer.
  function memoriserPerception(h) {
    if (!h) return;
    const c = h.cercle || null;
    const cible = h.cible && h.cible !== h ? h.cible : null;
    const a = ailleDe(h), e = a ? S.escouades[h.escouade] : null;
    const distanceCible = cible ? Math.hypot(cible.x - h.x, cible.y - h.y) : null;
    const p = {
      temps: +S.temps.toFixed(2),
      position: { x: +h.x.toFixed(1), y: +h.y.toFixed(1) },
      etat: h.etat,
      action: h.pensee && h.pensee.action,
      raison: h.pensee && h.pensee.raison,
      systeme: h.pensee && h.pensee.systeme,
      ordre: e ? dire(e.ordre) : null,
      cercle: c ? { amis: c.amis, ennemis: c.ennemis,
                    avantage: !!avantage(c, h) } : null,
      cible: cible ? { id: cible.debugId, nom: cible.nom || null,
                       camp: cible.camp, etat: cible.etat,
                       distance_m: +distanceCible.toFixed(1) } : null,
      corps: h.l1 ? { jambes: h.l1.jambes, bras: h.l1.bras,
                      sang_froid: +h.l1.sangFroid.toFixed(2),
                      exposition: +h.l1.exposition.toFixed(2),
                      charge: +h.l1.chargeNerveuse.toFixed(2),
                      emprise: +h.l1.emprise.toFixed(2) } : null,
      reflexion: h.l2 ? { idee: h.l2.idee, tient: +h.l2.tient.toFixed(2),
                          attend: +h.l2.attend.toFixed(2),
                          appui: +h.l2.appui.toFixed(2),
                          degage: h.l2.degage == null ? null : +h.l2.degage.toFixed(2) } : null,
      arbitre: h.conduit ? { jambes: h.conduit, bras: h.conduitBras } : null,
      physique: { pv: +Math.max(0, h.pv).toFixed(1), pv_max: +h.pvMax.toFixed(1),
                  souffle: h.souffle == null ? null : +h.souffle.toFixed(2),
                  presse: +(h.presse || 0).toFixed(1) },
    };
    // La position exacte n'entre pas dans la clef : marcher produirait une
    // entrée à chaque pas sans que sa perception ait changé. La distance à la
    // cible est ramenée à des bandes de deux mètres ; le passage d'une bande
    // est une information, les centimètres ne le sont pas.
    const cle = [p.etat, p.action, p.raison, p.systeme, p.ordre,
      p.cercle && p.cercle.amis, p.cercle && p.cercle.ennemis,
      p.cible && p.cible.id, distanceCible == null ? "" : Math.floor(distanceCible / 2),
      p.corps && p.corps.jambes, p.corps && p.corps.bras,
      p.corps && Math.round(p.corps.charge * 10),
      p.reflexion && p.reflexion.idee, p.arbitre && p.arbitre.jambes,
      Math.round((h.pv / Math.max(1, h.pvMax)) * 10),
      h.souffle == null ? "" : Math.round(h.souffle * 10), Math.round(h.presse || 0)
    ].join("|");
    if (cle === h.perceptionCle) return;
    h.perceptionCle = cle;
    h.perceptions.push(p);
    // La chronologie sert au diagnostic, pas à transformer une longue épreuve
    // en fuite mémoire. On conserve une vraie fenêtre sémantique (environ
    // vingt minutes dans C6) et, surtout, sa FIN : c'est le moment que le
    // joueur vient de marquer. Le compteur permet au rapport de dire
    // honnêtement qu'une partie plus ancienne existait.
    const MAX_PERCEPTIONS_MEMOIRE = 2048;
    if (h.perceptions.length > MAX_PERCEPTIONS_MEMOIRE) {
      const omises = h.perceptions.length - MAX_PERCEPTIONS_MEMOIRE;
      h.perceptions.splice(0, omises);
      h.perceptionsOubliees = (h.perceptionsOubliees || 0) + omises;
    }
  }

  function penser(h, action, raison, systeme) {
    if (!h) return;
    const avant = h.pensee;
    if (!avant || avant.action !== action || avant.raison !== raison ||
        avant.systeme !== systeme) {
      if (avant) {
        h.pensees = h.pensees || [];
        h.pensees.push(avant);
        if (h.pensees.length > 4) h.pensees.shift();
      }
      h.pensee = { action, raison, systeme, depuis: S.temps };
    }
    // Compatibilité avec les journaux et l'ancienne fiche. L'autorité est
    // désormais `pensee`; cette phrase n'est plus interprétée nulle part.
    h.branche = "j'essaie de " + action + " parce que " + raison;
    memoriserPerception(h);
  }

  // ===========================================================================
  // CE QUE CET HOMME-CI PORTE — son ordre, son chef, et depuis quand
  // ===========================================================================
  // MESURÉ AVANT D'ÊTRE ÉCRIT, et c'est ce qui justifie ces vingt lignes :
  // `banc-combattant.js` relève, sur la condition de référence, 0,0 % d'hommes
  // portant un ordre reçu et 0,0 % portant un chef connu. L'ordre vit sur
  // l'UNITÉ (`u.ordre`) et le chef aussi (`u.cadre.chef`) ; l'homme, lui, ne
  // sait rien — ni ce qu'on lui a dit, ni qui le commande.
  //
  // CE QUE ÇA COÛTE QUAND ÇA MANQUE. Un homme sans chef connu ne peut pas
  // « rester avec ses pairs » au sens du refactor : il n'a personne à suivre en
  // particulier, donc il suivra n'importe qui de la bonne couleur. Et un homme
  // sans ordre reçu ne peut pas être en RETARD sur son ordre — il lit toujours
  // celui de son unité, c'est-à-dire le plus récent, c'est-à-dire qu'il obéit
  // avant d'avoir entendu.
  //
  // ⚠ CE GESTE N'EST QU'UNE ÉCRITURE, ET RIEN NE LE LIT ENCORE. C'est
  // délibéré : le lot 3 tient en plusieurs pas, celui-ci est additif et doit
  // laisser l'étalon strictement identique. Le jour où la délibération lira
  // `h.ordreRecu` au lieu de `u.ordre`, ce sera un changement de modèle, mesuré
  // et annoncé comme tel.
  //
  // ⚠ ON NE PASSE PAS PAR `guideDe()`. Elle a un EFFET DE BORD — elle réaffecte
  // `u.cadre.chef` quand le chef courant est tombé. L'appeler ici la ferait
  // tourner plus tôt dans le battement qu'aujourd'hui, et une succession
  // observée un cran plus tôt est un changement de comportement. On lit donc
  // `u.cadre.chef` tel quel, sans le réparer.
  //
  // Le chef n'est « connu » que s'il est À PORTÉE DE VUE. Au-delà, l'homme
  // garde ce qu'il a vu en dernier, avec sa date et son endroit : c'est de la
  // mémoire, pas de l'omniscience, et c'est ce qui permettra plus tard à un
  // messager ou à un isolé de chercher là où il l'a vu.
  const VUE_CHEF = 18;              // la même portée que `VUE_MORT` : à vue d'œil

  function porterOrdreEtChef(h) {
    const u = formationDe(h);
    if (!u) return;
    // LA CLEF EST `version`, ET CE N'EST PAS UN DÉTAIL. Un ordre d'unité porte
    // `mode`, `destination`, `donneA`, `texte` et `version` — pas de `n` : la
    // première écriture de ce geste comparait `o.n`, c'est-à-dire `undefined`
    // à `undefined`, si bien que l'homme retenait son PREMIER ordre et ne
    // remarquait plus jamais les suivants. Quatre-vingt-treize pour cent des
    // hommes portaient donc un ordre, et c'était toujours le même. Ça ne se
    // voit pas en relisant : ça se voit en regardant une valeur.
    const o = u.ordre;
    if (o && (!h.ordreRecu || h.ordreRecu.version !== o.version)) {
      h.ordreRecu = { version: o.version, mode: o.mode,
                      destination: o.destination ? o.destination.nom || null : null,
                      texte: o.texte || null, recuA: S.temps };
    }
    const chef = u.cadre && u.cadre.chef;
    if (chef && chef !== h && chef.etat !== "mort" &&
        Math.hypot(chef.x - h.x, chef.y - h.y) <= VUE_CHEF) {
      h.chefConnuId = chef.debugId;
      h.chefVuA = S.temps; h.chefVuX = chef.x; h.chefVuY = chef.y;
    }
  }

  // ===========================================================================
  // LA COUCHE 3, EN TÊTE DE BATTEMENT — le rendez-vous qui manquait
  // ===========================================================================
  // ELLE ÉTAIT PLUS BAS, ET C'EST TOUT LE DÉFAUT. Ce bloc vivait à la 680e ligne
  // de la cascade de `soldat()`, si bien qu'un homme ne l'avait que si son
  // battement descendait jusque-là. Mesuré : 239 hommes vivants, 239 avec une
  // escouade — la condition d'entrée n'est donc JAMAIS fermée — et 135 seulement
  // avec une `l3`.
  //
  // CE QUE ÇA COÛTAIT, ET C'EST LA VRAIE FAUTE. `QuiConduit.barre(l3)` rend ZÉRO
  // quand la couche 3 est absente, et l'écrit en toutes lettres : « un homme
  // sans ordre du tout n'a pas de barre : il est livré à ses couches, ce qui est
  // la définition d'un homme sans nouvelles ». Avec une `l3` ordinaire, la barre
  // vaut 0,50 — « la seule raison pour laquelle une troupe reste une troupe ».
  //
  // Autrement dit : QUARANTE-TROIS POUR CENT DE L'ARMÉE ÉTAIT ARBITRÉE COMME
  // N'AYANT REÇU AUCUN ORDRE. Pas parce qu'elle n'en avait pas — tous en ont un
  // — mais parce que le chemin de code n'était pas allé le chercher. N'importe
  // quelle prétention du corps l'emportait alors sans rien avoir à franchir.
  //
  // On la calcule donc AU MÊME COUP D'ŒIL que les couches 1 et 2, ce que son
  // propre commentaire demandait déjà (« au rythme de son œil »). Le commentaire
  // du rendez-vous, deux lignes plus bas, disait qu'il n'existait aucun
  // rendez-vous des quatre couches et que celui-ci en donnait deux ; il en donne
  // trois. La 4 reste où elle est, et pour une raison : son calcul est
  // inséparable du jet de pillage qui le suit, et les séparer déplacerait un
  // tirage — un autre changement, qui mérite sa propre mesure.
  function observerL3(h, dt) {
    if (!window.Interpretation) return;
    const e = S.escouades[h.escouade];
    if (!e) return;
    const ordre = e.ordre || ORDRE_NU;
    h.revoirL3 = (h.revoirL3 || 0) - dt;
    if (h.revoirL3 > 0) return;
    h.revoirL3 = oeil(h);
    const c = h.cercle, a3 = S.ailes[e.aile];
    h.l3 = window.Interpretation.pas(ordre, {
      docile: h.envie ? h.envie.docile : 0,
      alarme: c ? Math.max(-1, 1 - (c.ennemis || 0) * 0.7) : 1,
      epaule: c ? Math.min(1, (c.amis || 0) / 4 * 2 - 1) : 0,
      frais: h.souffle != null ? h.souffle * 2 - 1 : 0,
      vu: (a3 && a3.banniere.debout && sousLaBanniere(h)) ? 1 : -1,
      // Depuis combien de temps il n'a rien reçu, rapporté à la minute :
      // +1 l'ordre vient de tomber, −1 il date d'une heure. C'est le même
      // compteur que celui de l'initiative, lu autrement — là il décide,
      // ici il use.
      depuis: Math.max(-1, 1 - (e.depuis || 0) / 60),
    });
  }

  function soldat(h, dt) {
    if (h.etat === "mort") return;
    porterOrdreEtChef(h);
    // Une cible n'est pas une liaison magique. Dès qu'un des deux franchit un
    // huis, l'autre le perd ; il devra le retrouver par une perception valide
    // dans le même espace.
    if (h.cible && !memeEspace(h, h.cible)) h.cible = null;
    // Il reste dans la grille de voisinage, et c'est voulu : les vivants se
    // séparent de lui comme de n'importe quel corps, donc la presse s'ouvre
    // autour de celui qui est tombé. Personne n'a écrit ce vide-là.
    if (h.etat === "blesse") {
      penser(h, "rester en vie", "je suis à terre et je perds du sang", "blessure");
      saigner(h, dt); return;
    }
    // La tête ne se bat pas, ne marche pas, ne rompt pas. Elle décide, et son
    // pas de simulation se résume à ça.
    if (h.tete) {
      penser(h, "lire la bataille", "je commande le corps et ne combats pas dans son rang",
             "commandement");
      return;
    }
    // Sortir d'une maison déjà remise ne se transforme pas en nouveau duel si
    // une seconde équipe y découvre quelqu'un une seconde plus tard. Cette
    // transition topologique doit précéder la recherche ordinaire de cible ;
    // sinon l'homme acquiert un adversaire intérieur, atteint l'huis, change
    // d'espace et conserve cette cible à travers le mur.
    const uniteRatissage = formationDe(h);
    if (uniteRatissage && uniteRatissage.ratissage && h.sortieBatiment != null) {
      h.cible = null; menerRatissage(h, uniteRatissage, dt); return;
    }
    survie(h);
    // ---- LA COUCHE 1 TOURNE ICI, ET ELLE NE CONDUIT RIEN -------------------
    // Mode observation : elle calcule, on la mesure, `soldat()` continue sur sa
    // cascade. Au rythme de l'OEIL de l'homme et non a 20 Hz â€” 2 550 cerveaux
    // vingt fois par seconde n'ont aucune raison d'exister, et `oeil()` est
    // exactement l'horloge qu'il faut : le temps qu'un homme met a s'apercevoir
    // de quelque chose.
    if (window.BatailleCorps) {
      h.revoirCorps = (h.revoirCorps || 0) - dt;
      if (h.revoirCorps <= 0) {
        const ecoule = Math.min(3, (h.dtCorps || 0) + dt);
        window.BatailleCorps.observer(h, {
          autour, temps: S.temps, nuit: true, degatTypique: (DEGAT[0] + DEGAT[1]) / 2,
          // Un porte-bannière ne porte un SIGNE que si sa hampe est encore
          // debout. Couchée, il n'est plus qu'un homme — et c'est la chute
          // elle-même qui est le stimulus, pas son absence.
          banniereDebout: (o) => {
            const a = ailleDe(o);
            return !!(a && a.banniere && a.banniere.debout);
          },
          pese, apaise: apaiseDe, libre: solConnu() ? libreEn : null,
        }, ecoule);
        // ---- ET LA COUCHE 2 DANS LE MEME BATTEMENT ------------------------
        // ELLE ETAIT CHARGEE ET APPELEE NULLE PART (🔒 90370). Son pourvoyeur
        // est `bataille/reflexion-adapt.js`, jumeau de `corps-adapt.js` : il
        // batit les onze signaux depuis ce que la bataille tient deja, et pose
        // `h.l2`. L'arbitre posé dans la même passe dira ensuite, à l'unique
        // embranchement plus bas, si cette réflexion conduit réellement.
        //
        // ICI ET PAS AILLEURS, PARCE QUE C'EST LE SEUL INSTANT OU DEUX SORTIES
        // SONT FRAICHES ENSEMBLE. 🔒 90360 dit qu'il n'existe aucun rendez-vous
        // des quatre couches ; celui-ci en donne deux — `h.l1` vient d'etre
        // pose, `h.l2` l'est dans la foulee, au meme coup d'oeil et avec le
        // meme `dt`. Les 3 et 4 restent aux rythmes qui sont les leurs.
        //
        // Sans les masques du bâti et de l'eau, la retraite est INCONNUE et
        // non ouverte. C'est le pourvoyeur qui porte la nuance.
        // LA COUCHE 3 AVANT L'ARBITRE, et non six cents lignes après lui :
        // c'est elle qui pose la BARRE que les trois prétendants doivent
        // franchir. La calculer après l'élection revenait à élire sans barre.
        observerL3(h, ecoule);
        if (window.BatailleReflexion)
          window.BatailleReflexion.observer(
            h, { autour, temps: S.temps, pese, libre: solConnu() ? libreEn : null }, ecoule);
        h.revoirCorps = oeil(h); h.dtCorps = 0;
        // ---- LA DIFFUSION DU CHEF ----------------------------------------
        // Un chef a portee doit faire redescendre l'alarme, et le savoir coute
        // un balayage a quinze metres. Le faire PAR HOMME serait deux mille
        // cinq cents balayages ; on le fait donc PAR CHEF — il y en a un par
        // escouade, soit cent vingt-cinq. Vingt fois moins, pour le meme fait.
        //
        // C'est la meme inversion que les foyers : quand un fait est rare et
        // ses temoins nombreux, c'est le fait qui parle, pas les temoins qui
        // cherchent.
        if ((h.chef || h.capitaine) && h.etat !== "deroute" &&
            h.etat !== "mort" && h.etat !== "blesse") {
          autour(h.x, h.y, RALLIE_M, (o) => {
            if (o === h || o.camp !== h.camp) return;
            if ((o.x - h.x) ** 2 + (o.y - h.y) ** 2 > RALLIE_M * RALLIE_M) return;
            o.chefVu = S.temps;
          });
        }
        // ---- LE BRANCHEMENT PROGRESSIF, PREMIERE TRANCHE ------------------
        // ON N'ATTEND PAS LES COUCHES 2, 3 ET 4 : elles existent deja, sous une
        // autre forme. La cascade de `soldat()` EST la tete — elle execute des
        // ordres, calcule des cibles, poursuit un but —, et `emprise` dit
        // exactement de combien le corps la couvre. Il n'y avait donc rien a
        // attendre, et le plan « on observe jusqu'a ce que tout soit ecrit »
        // etait une erreur : on ne verifie pas une couche en la regardant
        // calculer a cote.
        //
        // DEUX ETATS POUR COMMENCER, ET DEUX SEULEMENT. `sidération` et
        // `fuite` : les deux que la cascade ne sait pas produire pour ces
        // raisons-la, les deux qui se voient d'un coup d'oeil sur le plan, et
        // les deux dont on peut sortir sans rien casser. Le recul, le
        // resserrement et la ruee viendront quand ceux-ci auront tenu.
        //
        // ET SEULEMENT QUAND LE CORPS A VRAIMENT LA MAIN. Sous ce seuil, la
        // tete conduit et la couche se contente d'exister — ce qui est le cas
        // le plus frequent, et c'est voulu.
        // ⚠ PLUS DE SEUIL, PLUS DE DRAPEAU — LA COUCHE CONDUIT.
        // `pilote` et `emprise > 0,60` etaient le garde-fou de la premiere
        // passe : la couche existait A COTE de la morale, et les deux
        // decidaient de la meme chose. On garde les deux « au cas ou », et
        // l'on herite du pire des deux sans plus savoir lequel produit quoi.
        //
        // Ce que le seuil protegeait — l'emballement du gregarisme, qui est une
        // retroaction positive — est desormais borne par `c.social` : le niveau
        // ambiant auquel on s'habitue, dont seul le DEPASSEMENT passe. Une
        // ligne uniformement tendue ne transmet plus rien ; un seul homme qui
        // craque a l'instant transmet tout.
        //
        // `emprise` n'a pas disparu pour autant : elle agit DANS l'election,
        // par `SOUS_EMPRISE` — fuir, se figer et se ruer demandent que le corps
        // ait la main. Un homme calme ne part donc pas en courant, et ce n'est
        // plus un seuil pose dehors qui l'en empeche, c'est le modele.
        //
        // La tete et le roi restent hors couche : ils ne se battent pas.
        if (h.l1 && !h.tete && !h.roi) {
          const g = h.l1.jambes, b = h.l1.bras;
          // LES BRAS D'ABORD, parce qu'ils ne rendent pas la main. Un homme dont
          // le corps a laissé tomber les bras ne frappe plus, quoi que sa tête
          // décide par ailleurs — c'est le seul endroit où la couche 1 agit
          // SANS prendre tout l'homme, et c'est justement ce qu'on veut : elle
          // retire une capacité, elle ne dicte pas une conduite.
          h.brasMorts = (b === "ballants");
          // Les bras ballants restent une incapacité physique. Pour les jambes,
          // en revanche, l'arbitre est l'autorité unique : une couche chargée
          // n'agit pas simplement parce que son mot existe encore dans `h.l1`.
          if (h.conduit === "corps") {
          // `corpsAgi` — VRAI SI LA COUCHE A PRIS CE BATTEMENT-CI. Un fait de
          // battement, pas un régime. S'appelait `pilote`, qui disait une
          // conduite permanente : un nom qui avait survécu à sa fonction et
          // faisait chercher une conduite là où il n'y a qu'un affichage.
          // Nom posé par Wenna la Nommeuse (⚔️ 90320), gravé par le Fer.
          h.l1.corpsAgi = true;

          if (g === "sidération" && h.etat !== "deroute") {
            // Il s'arrête net, au milieu d'un geste qu'il ne finit pas.
            h.etat = "tient"; h.cible = null;
            penser(h, "m'arrêter net", "mon corps ne répond plus", "corps · couche 1");
            return;
          }
          if (g === "fuite" && h.etat !== "deroute") {
            rompre(h);
            penser(h, "fuir", "mon corps a rompu avant que je le décide",
                   "corps · couche 1");
            noter("escouade-rompt", h.x, h.y, { clef: "corps-" + (h.escouade || 0) });
            return;
          }
          if (g === "dérobade" && S.temps <= (h.menaceJus || -Infinity)) {
            const dx = h.x - h.menaceX, dy = h.y - h.menaceY;
            const n = Math.hypot(dx, dy) || 1, cote = h.cote < 0 ? -1 : 1;
            if (h.menaceGenre === "incendie") {
              // Un foyer persiste : l'écart latéral d'un souffle ne suffit pas,
              // il faut augmenter la distance. Le léger angle est stable par
              // combattant, donc les fuites ne tracent pas le même rayon.
              const a = (hasardFuite(h, 0x78dde6e4) * 2 - 1) * .28;
              const c = Math.cos(a), s = Math.sin(a);
              versLe(h, h.x + (dx / n * c - dy / n * s) * 4.2,
                        h.y + (dx / n * s + dy / n * c) * 4.2, CHARGE, dt);
            } else {
              // Sous un jet bref, on sort perpendiculairement de son axe.
              versLe(h, h.x - dy / n * cote * 3.2,
                        h.y + dx / n * cote * 3.2, CHARGE, dt);
            }
            h.etat = "tient";
            penser(h, h.menaceGenre === "incendie" ? "m'écarter du foyer" : "bondir hors du souffle",
                   h.menaceGenre === "incendie" ? "le feu tient encore" : "la chaleur me prend de côté",
                   "corps · couche 1");
            return;
          }
          if (g === "recul") {
            // ON RECULE FACE À EUX, et l'on emprunte le geste que la cascade
            // sait déjà faire — `versLe` avec le cap posé à l'envers, donc
            // ralenti de moitié par la marche arrière. On ne réécrit rien.
            const men = ennemiProche(h, RAYON_LOCAL) || h.cible;
            const externe = !men && S.temps <= (h.menaceJus || -Infinity);
            if (men || externe) {
              const mx = men ? men.x : h.menaceX, my = men ? men.y : h.menaceY;
              const dx = h.x - mx, dy = h.y - my, n = Math.hypot(dx, dy) || 1;
              let bx = h.x + dx / n * RECUL_M, by = h.y + dy / n * RECUL_M;
              if (h.cercle && h.cercle.amis) {
                bx = (bx + h.cercle.ax) / 2; by = (by + h.cercle.ay) / 2;
              }
              versLe(h, bx, by, MARCHE, dt);
              h.cx = -dx / n; h.cy = -dy / n;
              if (men && !h.brasMorts && Math.hypot(men.x - h.x, men.y - h.y) <= portee(h)) {
                h.cible = men; frapper(h, men, dt);
              }
              h.etat = "tient";
              penser(h, "céder le pas", "mon corps me pousse hors de la menace",
                     "corps · couche 1");
              return;
            }
          }
          if (g === "serrer" && h.cercle && h.cercle.amis) {
            // REFERMER LE TROU — `serrer()` existe déjà dans ce fichier et fait
            // exactement ça : chercher l'épaule sans se coller. La couche 1 ne
            // fait que le DÉCIDER, là où la cascade ne le décidait qu'en
            // décrochant.
            serrer(h, h.cercle, dt);
            const menace = ennemiProche(h, portee(h));
            if (menace && !h.brasMorts) { h.cible = menace; frapper(h, menace, dt); }
            h.etat = "tient";
            penser(h, "retrouver une épaule", "mon corps cherche les miens",
                   "corps · couche 1");
            return;
          }
          if (g === "ruée") {
            const proie = proieProche(h, 14);
            if (proie) {
              versLe(h, proie.x, proie.y, CHARGE, dt);
              if (!h.brasMorts && Math.hypot(proie.x - h.x, proie.y - h.y) <= portee(h)) {
                h.cible = proie; frapper(h, proie, dt);
              }
              h.etat = "melee";
              penser(h, "me jeter en avant", "mon corps a pris la main",
                     "corps · couche 1");
              return;
            }
          }
          // `planté` ne prend rien : c'est justement l'état où le corps n'a rien
          // à dire, donc la tête garde la main. On le laisse tomber dans la
          // cascade, et c'est ce qui fait que le branchement reste progressif.
          h.l1.corpsAgi = false;
          } else h.l1.corpsAgi = false;
        }
      } else h.dtCorps = (h.dtCorps || 0) + dt;
    }
    if (executerReflexion(h, dt)) return;
    if (executerDoctrine(h, dt)) return;
    // LE FER SUIT, IL NE SAUTE PAS. On fait tourner l'arme vers le cap voulu au
    // début du battement, avec un pas de retard sur ce que le reste va décider
    // — et c'est très bien ainsi : un homme qui change d'avis a son fer encore
    // tourné vers l'affaire précédente, ce qui est exactement ce qu'on cherche.
    tourner(h, dt);
    // ET L'ERRE RETOMBE QUAND PLUS RIEN NE POUSSE. Un homme qui cesse de
    // marcher — il est entré en mêlée, il souffle, il attend — ne passe par
    // aucun `versLe` ce battement-là, et sans ce freinage sa vitesse resterait
    // en réserve : il repartirait à pleine allure, depuis l'arrêt, trois
    // secondes plus tard.
    //
    // ⚠ SEULEMENT S'IL N'A PAS POUSSÉ, ET C'EST TOUTE L'AFFAIRE. La première
    // écriture freinait à chaque battement en pariant que `versLe` relancerait
    // dans le même : « la rampe rattrape sa consigne ». Elle ne la rattrape
    // pas — la rampe monte à `ACCEL` (1,4) et le frein descend à `FREIN_PIED`
    // (3,0), qui est plus grand PAR CONSTRUCTION puisqu'on s'arrête mieux
    // qu'on ne part. Le solde était donc négatif à chaque tour et la vitesse
    // de tout le monde s'effondrait vers zéro. Mesuré : mille sept cents
    // hommes qui n'atteignent jamais la porte, zéro contact, zéro blessé, la
    // porte seulement `abimee` au bout de dix minutes. Une bataille qui n'a
    // pas eu lieu.
    //
    // Le drapeau se lit AVANT d'être remis à faux, donc il porte l'état du
    // battement précédent — un pas de retard, et aucune horloge à comparer.
    if (!h.pousse && h.vit) h.vit = Math.max(0, h.vit - FREIN_PIED * dt);
    h.pousse = false;
    // On repart libre à chaque pas : seul celui qui est effectivement sur sa
    // trace, plus bas, se redéclarera sur voie. Sans cette remise à zéro, un
    // homme qui quitte la colonne pour la mêlée garde une tangente périmée et
    // se fait pousser le long d'une rue qu'il a quittée.
    h.surVoie = false;

    if (h.etat === "deroute") {
      if (!h.fuiteStrategie) preparerFuite(h, null);
      const seul = h.fuiteStrategie === "dispersion";
      // Celui qui cherche encore les siens reste manœuvrant et saisit tout de
      // suite une occasion de ralliement. Celui qui a conclu « chacun pour
      // soi » doit d'abord épuiser l'inertie de cette décision ; un chef peut
      // encore le reprendre ensuite, mais la fenêtre est bien plus étroite.
      const verrouRalliement = seul
        ? 12 + 22 * h.fuiteSeverite + hasardFuite(h, 0x165667b1) * 8 : 0;
      if (S.temps - h.fuiteDepuis >= verrouRalliement &&
          rallier(h, dt) && h.etat !== "deroute") return;

      if (!seul) {
        penser(h, "rejoindre les miens",
               "je crois qu'une masse amie peut encore me couvrir",
               "déroute · regroupement");
        if (fuirVersProtection(h, dt)) return;
      } else {
        penser(h, "fuir seul sans changer de cap",
               "la force en face me paraît trop grande pour qu'une ligne me protège",
               "déroute · dispersion");
      }
      if (S.temps <= (h.menaceJus || -Infinity)) {
        fuirSelonCap(h, dt);
        return;
      }
      // On fuit par où l'on est venu — un homme rompu ne cherche pas une
      // sortie, il refait le chemin qu'il connaît. ET IL LE REFAIT PAR LES
      // RUES : c'est la marche des fuyards civils, la même primitive, qui
      // descend le graphe de voirie de carrefour en carrefour. En ligne
      // droite, une déroute traversait le quartier de part en part.
      // LES QUATRE-VINGTS DE L'ANNEAU N'ONT PAS DE PORTE À EUX, et c'était une
      // panne qui attendait son heure : ils ne rompent qu'au donjon, c'est-à-
      // dire à la dernière demi-heure de la nuit, et `dehors(undefined)` jette
      // là où plus personne ne regarde. Ils s'en retournent par la porte
      // principale, faute d'en avoir gardé une.
      const sienne = h.entree || S.entree;
      const [nx, ny] = dehors(sienne);
      const bx = sienne.x + nx * 400, by = sienne.y + ny * 400;
      if (h.noeud === undefined) {
        h.v = h.vit || 0; h.surRue = false; h.arc = null; h.venu = null; h.s = 0;
        h.noeud = noeudProche(h.x, h.y);
      }
      // ON NE ROMPT PAS À PLEINE COURSE NON PLUS. `marcher` avance sur le
      // réseau de rues à `h.v`, qui était posé à `FUITE` une fois pour toutes
      // au moment où l'homme craque — donc un homme qui cédait passait de
      // l'arrêt à trois mètres soixante entre deux images, ce qui est
      // exactement le défaut qu'on vient de corriger de l'autre côté. On y
      // remet la même rampe, en repartant de l'erre qu'il avait : celui qui
      // rompt alors qu'il chargeait déjà file tout de suite, celui qui rompt
      // à l'arrêt met ses deux secondes à s'arracher — et c'est lui qu'on
      // rattrape.
      h.v = Math.min(FUITE, (h.v || 0) +
                     ACCEL * (h.souplesse || 1) * vigueur(h) * dt);
      h.vit = h.v;
      // Hors les murs il n'y a plus de rue, et c'est vrai : `marcher` rend
      // faux, on finit en rase campagne comme il se doit.
      if (!marcher(h, dt, bx, by, false)) versLe(h, bx, by, FUITE, dt);
      return;
    }

    // LE COUREUR NE SE BAT PAS TANT QU'IL PORTE. Il traverse la presse, et
    // c'est ce qui le rend fragile : il est visible, il est seul, et il ne
    // rend pas les coups. S'il tombe, l'ordre tombe avec lui — personne ne le
    // saura jamais, ni celui qui l'a envoyé, ni celle qui l'attendait.
    // DEUX COUREURS, ET ILS NE PORTENT PAS LA MÊME CHOSE. Celui de l'assaut
    // porte un ordre à une escouade ; celui du guet porte une nouvelle au
    // Donjon. Ils courent tous deux sans rendre un coup, et tous deux peuvent
    // tomber — c'est la seule chose qu'ils aient en commun, et c'est la bonne.
    if (h.messager) { courirAuDonjon(h, dt); return; }
    if (h.etat === "coureur") { courir(h, dt); return; }
    if (h.rapportMission) { courirRapport(h, dt); return; }

    // CELUI QUI RENTRE NE SE RETOURNE PAS. L'anneau qu'on a fait ouvrir se
    // retire dans la cour et ne rend plus un coup — et il faut que ce soit
    // vrai des deux côtés, sinon le premier assaillant arrivé le remet dans la
    // mêlée et l'on a écrit une reddition qui se bat.
    if (h.etat === "rentre") {
      if (h.poste) versLe(h, h.poste[0], h.poste[1], MARCHE, dt);
      penser(h, "rentrer au poste", "l'anneau a reçu l'ordre de s'ouvrir", "ordre reçu");
      return;
    }

    // ---- ON TIENT À SA VIE ---------------------------------------------------
    // Trois règles, une seule mesure (voir `balance`), et elles se lisent dans
    // cet ordre parce que c'est l'ordre dans lequel un homme y pense.
    //
    //   1. ENTAMÉ, ON DÉCROCHE. Sous la moitié de ses pv, on ne reste pas au
    //      contact : on sort de l'allonge à reculons. C'était le plus gros
    //      mensonge du modèle — un homme à trois points de vie frappait avec le
    //      même entrain qu'au premier coup, et personne n'a jamais fait ça.
    //   2. ON NE S'AVANCE PAS SANS ÊTRE LE PLUS FORT ICI. Pas de contact tant
    //      qu'on n'a pas l'avantage dans les cinq mètres. On ne fuit pas pour
    //      autant : on attend à distance d'allonge, et c'est cette attente qui
    //      FAIT la ligne — chacun tient parce que son voisin tient.
    //   3. EN INFÉRIORITÉ FRANCHE, ON PART EN COURANT, à reculons, face à eux.
    //      Pas `deroute` : la déroute est un état de morale dont on ne revient
    //      pas. Ceci est un mouvement, et il se rattrape dès qu'un ami arrive.
    //
    // `repli` est PARTAGÉ avec le décrochement d'aile, et c'est sans danger :
    // ce décrochement-là est piloté par `e.ordre`, relu à chaque battement, si
    // bien qu'un homme qui recule de son propre chef ne part pas pour autant
    // aux deux cent vingt mètres. Et `forceDe()` le compte encore vif — une
    // aile dont trois hommes reculent n'a pas l'air détruite. Les deux sens se
    // ressemblent d'ailleurs assez : dans les deux cas on s'en va EN ORDRE.
    const b = balance(h, RAYON_LOCAL);
    // ON LE GARDE SUR L'HOMME. Il sert deux fois : ici pour décider ce qu'il
    // fait, et dans `frapper` pour savoir ce qu'il ENCAISSE quand un autre le
    // vise. Le calculer une fois par battement et par homme au lieu d'une fois
    // par coup porté est toute la différence entre un balayage et cinquante.
    h.cercle = b;
    // L'entame ne tremble pas — les pv ne remontent pas, donc pas d'hystérésis
    // à lui donner. Le nombre, lui, oscille : c'est `decider` qui le tient.
    const entame = h.pv < h.pvMax * SEUIL_RECUL;
    const submerge = decider(h, b, dt);

    if (entame || submerge) {
      // Face à eux, en arrière : on ne tourne pas le dos à trois pas d'une
      // hache. LES DEUX MOTIFS FONT MAINTENANT LE MÊME GESTE — l'entaille et le
      // nombre poussent tous deux à céder le pas, et ni l'un ni l'autre n'est
      // une fuite. Ce qui les distinguait (courir, pâlir) était faux dans les
      // deux cas ; ce qui les distingue encore est la DURÉE, tirée dans
      // `decider`, et elle suffit.
      const men = ennemiProche(h, RAYON_LOCAL) || h.cible;
      if (men) {
        // ON NE RECULE PAS TOUT DROIT : on recule VERS LES SIENS. Le vecteur
        // est la somme de « m'éloigner de lui » et de « rejoindre l'épaule »,
        // ce qui fait qu'une aile qui décroche se replie en se resserrant au
        // lieu de s'éparpiller en éventail — et qu'elle est encore une troupe
        // quand elle s'arrête.
        const dx = h.x - men.x, dy = h.y - men.y;
        const n = Math.hypot(dx, dy) || 1;
        let bx = h.x + dx / n * RECUL_M, by = h.y + dy / n * RECUL_M;
        if (b.amis) { bx = (bx + b.ax) / 2; by = (by + b.ay) / 2; }
        // MARCHE, jamais FUITE : `versLe` la ramènera à 45 % puisqu'il va à
        // reculons, et c'est exactement ce qu'on veut voir — un homme qui cède
        // le terrain au pas, pas un homme qui détale.
        versLe(h, bx, by, MARCHE, dt);
        // ON RECULE EN FRAPPANT, ET C'EST LE MÊME ARGUMENT QUE LA PATIENCE.
        // Reculer n'est pas cesser de se battre : à un mètre d'une hache, un
        // homme qui cède le pas garde son fer devant lui et rend les coups —
        // aucun homme au monde ne recule les bras ballants devant quelqu'un
        // qu'il pourrait toucher. Sans cette ligne on fabrique des statues au
        // contact, et c'est ce qu'on a vu : des hommes plantés à un mètre d'un
        // ennemi, sans un geste, parce que la branche qui les tenait ne
        // contenait aucun moyen de frapper.
        if (Math.hypot(men.x - h.x, men.y - h.y) <= portee(h)) {
          h.cible = men; frapper(h, men, dt);
        }
        // ON SE RETIRE EN LE REGARDANT, ET C'EST CE QUI PAIE. Le cap posé à
        // l'envers de la course fait deux choses d'un coup : `versLe` le lira
        // au battement suivant et le ralentira d'autant, et `frapper` le lira
        // aussi — donc celui qui recule en face reçoit ses coups DE FACE. Celui
        // qui tourne le dos, lui, n'est plus dans cette branche du tout : il a
        // rompu, il est en `deroute`, et il offre son revers.
        // On pose le CAP, pas le fer : ramener une lance vers celui dont on
        // s'écarte prend une seconde, et pendant cette seconde-là on la reçoit
        // encore de trois quarts. C'est le prix du demi-tour, et il est juste.
        h.cx = -dx / n; h.cy = -dy / n;
        penser(h, "céder le pas",
               entame ? "je suis trop blessé pour rester au contact"
                      : "ils sont trop nombreux autour de moi",
               entame ? "survie" : "nombre local");
        // Il tient. Il a cédé deux pas, il n'a pas quitté sa ligne — et son
        // point garde la couleur pleine de son camp.
        h.etat = "tient";
        return;
      }
    }

    // On frappe ce qui est à portée — et l'on choisit l'isolé, pas le plus
    // proche (voir `proieProche`).
    // ---- ON SOUFFLE -------------------------------------------------------
    // Décidé APRÈS la fuite et l'entame — on ne s'arrête pas pour reprendre son
    // vent quand on est en train de se faire déborder —, et AVANT d'engager :
    // c'est le choix de ne pas y aller cette fois-ci. Un homme au repos tient
    // sa place et rend les coups qu'on lui porte, il ne cherche personne.
    if (repos(h, dt)) {
      h.etat = "tient";
      penser(h, "reprendre mon souffle",
             "mon effort a dépassé ce que je peux soutenir", "souffle");
      const menace = ennemiProche(h, portee(h));
      if (menace) { h.cible = menace; frapper(h, menace, dt); }
      else serrer(h, b, dt);
      return;
    }

    const proche = proieProche(h, portee(h));
    if (proche) {
      // ---- LA PATIENCE, ET POURQUOI IL EN FAUT UNE ------------------------
      // TROIS MINUTES, CINQ HOMMES À TERRE. La règle « on n'entre pas sans
      // avantage » était juste et elle a produit une bataille où personne ne se
      // bat : deux lignes à deux mètres l'une de l'autre, aucune des deux en
      // supériorité locale, et les deux mille cinq cents qui se regardent
      // jusqu'au matin. Mesuré sur la vidéo : 1 à terre à 2'22, 5 à 3'03.
      //
      // Elle confondait deux choses qui n'en sont pas une : ne pas S'AVANCER
      // sans avantage — ce qui est le comportement d'un homme sensé —, et ne
      // pas FRAPPER ce qui est déjà à portée de son bras, ce qu'aucun homme au
      // monde ne fait. À deux mètres d'un ennemi on ne délibère plus très
      // longtemps.
      //
      // D'OÙ LA PATIENCE : on tient, on cherche l'épaule du voisin, on attend
      // que le nombre tourne — mais pas indéfiniment. Au bout de quelques
      // secondes de nez à nez, quelqu'un finit par y aller. C'est ce
      // « quelqu'un » qui manquait, et c'est lui qui débloque une ligne.
      //
      // ELLE EST INDIVIDUELLE, et c'est ce qui la rend intéressante : tirée sur
      // la trempe, elle va d'une seconde et demie pour les plus chauds à sept
      // pour les plus prudents. Donc ce n'est jamais toute la ligne qui craque
      // ensemble — c'est un homme, puis son voisin qui voit le nombre tourner
      // là où il est, et la mêlée se rouvre par un point.
      if (h.patience === undefined || h.patience === null)
        h.patience = 4.5 - (h.trempe || 0) * 3;
      if (!avantage(b, h) && h.patience > 0) {
        h.patience -= dt;
        // À portée mais pas en nombre : on tient l'allonge sans entrer, et l'on
        // va chercher l'épaule du voisin. L'homme qui attend n'attend pas sur
        // place — sinon on fabrique un chapelet de points isolés à portée les
        // uns des autres et pourtant seuls, que la chasse à l'isolé mange un
        // par un.
        h.etat = "tient"; h.cible = proche;
        penser(h, "gagner une épaule",
               "je n'ai pas le nombre et ma patience tient encore", "nombre local");
        serrer(h, b, dt);
        return;
      }
      noter("contact", h.x, h.y, { clef: "contact" });
      h.etat = "melee"; h.cible = proche;
      penser(h, "frapper l'homme à portée",
             avantage(b, h) ? "nous avons le nombre ici"
                            : "nous sommes nez à nez depuis trop longtemps",
             "combat local");
      frapper(h, proche, dt);
      return;
    }
    // Plus personne à portée : on souffle et la patience se refait. Sans cette
    // remise, un homme qui a craqué une fois ne délibérerait plus jamais de sa
    // nuit — la retenue est un état, pas une ressource qu'on épuise.
    h.patience = null;

    // UN ORDRE DE MOUVEMENT N'A PAS DE CAMP. Une vintaine du guet qu'on envoie
    // du Donjon au port passe ici exactement comme une vintaine d'assaut qu'on
    // détournerait vers une place. Le combat garde la priorité : cette branche
    // n'est atteinte qu'une fois les dangers immédiats traités plus haut.
    const unite = formationDe(h);
    if (unite && unite.ratissage) {
      h.etat = h.interieur == null ? "rassemble" : "fouille";
      menerRatissage(h, unite, dt);
      return;
    }
    if (h.etat === "prisonnier") {
      penser(h, "rester sous garde", "notre groupe a rendu les armes",
        "reddition locale");
      return;
    }
    if (unite && unite.ordre && unite.ordre.source === "ordre-rassemblement" &&
        unite.ordre.mode === "rassembler" && unite.ordre.destination) {
      h.etat = "rassemble";
      const phase = unite.cadre.ralliement && unite.cadre.ralliement.phase;
      penser(h, phase === "retrouver" ? "retrouver ma vintaine"
               : phase === "prendre-place" ? "gagner notre place dans la ligne"
               : "tenir ma place dans la ligne",
             phase === "retrouver" ? "mon vintenar attend les siens ici"
               : phase === "prendre-place" ? "notre vintaine est encore en chemin"
               : "ma vintaine a une place dans son aile",
             "ordre de ralliement");
      rassemblerFormation(h, unite, MARCHE, dt);
      return;
    }
    if (unite && unite.ordre && unite.ordre.source === "ordre-unite" &&
        unite.ordre.mode === "marcher" && unite.ordre.destination) {
      h.etat = "colonne";
      penser(h, "rejoindre " + unite.ordre.destination.nom,
             "c'est l'ordre littéral reçu par mon unité", "ordre de formation");
      menerFormation(h, unite.ordre.destination, MARCHE, dt);
      return;
    }

    const tientSonPoste = h.camp === "garde" || h.hors;
    if (h.etat === "melee") h.etat = tientSonPoste ? "tient" : "colonne";

    if (tientSonPoste) {
      // ---- MAIS ON SAUTE SUR L'ISOLÉ -------------------------------------
      // « Il tient son poste et c'est assez » était vrai tant que la garde
      // n'avait aucune notion du nombre. Ça ne l'est plus : deux assaillants
      // esseulés à dix pas d'un paquet de quarante gardes se promenaient
      // tranquillement, parce qu'aucune ligne de ce fichier ne permettait à un
      // défenseur d'avancer d'un mètre. On regardait quarante hommes regarder
      // deux hommes passer.
      //
      // TROIS VERROUS, PARCE QU'UNE GARDE QUI CHARGE N'EST PLUS UNE GARDE :
      //   — un avantage FRANC, pas une majorité d'une voix ;
      //   — une LAISSE mesurée depuis son POSTE et non depuis lui, sinon il
      //     dérive de proche en proche et la porte se retrouve sans personne ;
      //   — et jamais l'escorte du roi (`hors`), qui tient un cercle de quatre
      //     mètres autour d'un garçon de seize ans et n'a rien à poursuivre.
      //
      // C'est le pendant exact de la chasse à l'isolé côté assaut : le même
      // calcul, la même proie, mais tenu en laisse.
      const LAISSE = 12;
      if (h.camp === "garde" && !h.hors && h.poste &&
          b.amis + 1 + (h.trempe || 0) > b.ennemis + 2) {
        const proie = proieProche(h, LAISSE);
        if (proie && Math.hypot(proie.x - h.poste[0], proie.y - h.poste[1]) < LAISSE) {
          h.etat = "melee"; h.cible = proie;
          penser(h, "charger l'isolé",
                 "nous avons l'avantage et il reste dans la laisse de mon poste",
                 "initiative défensive");
          versLe(h, proie.x, proie.y, CHARGE, dt);
          return;
        }
      }
      penser(h, h.poste ? "tenir mon poste" : "tenir auprès des miens",
             "c'est la place que la défense m'a donnée", "poste de défense");
      // Sinon il tient son poste, et il y revient s'il en a été poussé.
      //
      // LA CHARRETTE NE MARCHE PAS NON PLUS, et pour la raison inverse : les
      // quarante hommes du roi ne sont pas là pour prendre une porte. Ils
      // tiennent un cercle de quatre mètres autour d'un garçon de seize ans, et
      // ils le tiendront jusqu'à ce qu'on leur passe dessus.
      if (h.poste) versLe(h, h.poste[0], h.poste[1], MARCHE, dt);
      return;
    }

    // --- l'assaillant ---------------------------------------------------
    const e = S.escouades[h.escouade];
    // L'ORDRE SE LIT SUR L'ESCOUADE, PAS SUR L'AILE. C'est toute la mécanique :
    // l'aile a reçu la décision de la tête, mais l'escouade n'en sait que ce
    // qui lui est PARVENU. Les deux peuvent différer pendant longtemps, et
    // c'est exactement là que la chaîne de commandement devient une histoire.
    const ordre = (e && e.ordre) || ORDRE_NU;

    // ---- LA COUCHE 3, EN OBSERVATION ---------------------------------------
    // ELLE NE CONDUIT RIEN, et c'est la première passe telle que le README la
    // demande : on la fait tourner à côté de la cascade, on la lit sous le
    // doigt, et on la conteste homme par homme sur une vraie nuit avant de lui
    // donner quoi que ce soit à décider.
    //
    // ELLE EST PAR HOMME, ET C'EST TOUT LE CHANGEMENT D'ÉCHELLE. L'ordre se lit
    // sur l'escouade — vingt hommes, une phrase —, mais la manière de le tenir
    // est à chacun : vingt hommes, une phrase, vingt manières. C'est la seule
    // dépense de ce branchement, et c'est aussi tout ce qu'on vient y chercher.
    //
    // Au rythme de son œil, pas à vingt fois la seconde : `oeil(h)` est déjà
    // l'horloge de la couche 1, et une manière de tenir un ordre ne se révise
    // pas plus vite qu'on ne s'aperçoit de ce qui a changé.
    // ---- LA COUCHE 3 A ÉTÉ HOISSÉE ----------------------------------------
    // Elle se calcule désormais en tête de battement, dans `observerCouches()`,
    // AVANT l'élection qui la lit. Elle était ici, à la 680e ligne d'une
    // cascade de 855 : seuls les hommes dont le battement allait jusque-là
    // l'avaient — quarante-trois pour cent de l'armée décidait donc sans barre.

    // POURQUOI IL FAIT CE QU'IL FAIT, ET NON PAS SEULEMENT CE QU'IL FAIT.
    // `branche` était renseignée pour la garde et pour elle seule ; l'assaillant
    // traversait cette machine entière sans jamais dire par quelle règle il
    // était passé. On voyait donc « forme » — l'état d'arrêt — sur la moitié
    // d'un corps, et rien au monde ne distinguait la réserve qu'on a laissée
    // en arrière de l'homme qui attend sa place au seuil, de celui qui cherche
    // l'entrée de la rue, ou de celui qui vide une maison. Quatre causes, un
    // seul mot, et pas de diagnostic possible à l'œil.
    if (ordre.verbe === "repli") {
      // Un décrochement n'est pas une déroute : on s'en va en ordre, moins
      // vite, et l'on peut encore recevoir un ordre. C'est la différence entre
      // une armée qui recule et une armée qui n'existe plus.
      h.etat = "repli";
      penser(h, "décrocher avec les miens", "c'est l'ordre que mon escouade a reçu",
             "ordre reçu");
      const [nx, ny] = dehors(h.entree);
      versLe(h, h.entree.x + nx * 220, h.entree.y + ny * 220, MARCHE, dt);
      return;
    }
    if (ordre.verbe === "tenir") {
      h.etat = "forme";
      penser(h, "tenir ici", "c'est l'ordre que mon escouade a reçu", "ordre reçu");
      if (h.poste) versLe(h, h.poste[0], h.poste[1], MARCHE, dt);
      return;
    }

    // --- SUIVRE ET APPUYER — se tenir par rapport à QUELQU'UN ----------------
    //
    // C'est le seul comportement du module dont le but bouge, et c'est tout ce
    // qui séparait « tenir » d'un piquet planté. Suivre, ce n'est pas courir
    // derrière : c'est rester ENTRE lui et le dehors, à la distance qu'on a
    // dite — donc sur l'axe de la porte, en arrière de lui. Une aile qui suit
    // à deux cents pas recule quand il avance et avance quand il recule, et
    // l'on voit enfin sur le plan ce qu'est une réserve.
    //
    // APPUYER EST LA MÊME CHOSE AVEC UNE PORTE DE SORTIE : celui qui appuie
    // s'engage dès que le fer arrive à trente mètres de lui. C'est ce qui fait
    // qu'une deuxième aile RELÈVE la première au lieu de la regarder fondre.
    // `h.front` passe avant tout : celui qu'on vient de désigner pour relever
    // une hache va à la porte, quel que soit l'ordre de son escouade. C'est le
    // seul endroit où l'on est plus près du seuil que de son rang.
    if (!h.front && (ordre.verbe === "suivre" ||
        (ordre.verbe === "appuyer" && !ennemiProche(h, 30)))) {
      const c = centreObjet(ordre.objet);
      // L'objet a disparu. On ne suit pas un mort : on s'arrête, et l'initiative
      // corrigera au pas suivant — c'est elle qui a le droit de décider, pas la
      // machine du soldat.
      if (!c) {
        h.etat = "forme";
        penser(h, "m'arrêter", "le groupe désigné par mon ordre a disparu",
               "repère perdu");
        if (h.poste) versLe(h, h.poste[0], h.poste[1], MARCHE, dt);
        return;
      }
      const marge = ordre.marge || (ordre.verbe === "appuyer" ? 60 : 120);
      const [nx, ny] = dehors(h.entree);
      // Sa place dans le rang, pour que l'aile ne se ramasse pas sur un point.
      const q = (h.escouade % 5 - 2) * 6;
      const bx = c[0] + nx * marge - ny * q, by = c[1] + ny * marge + nx * q;
      const d = Math.hypot(bx - h.x, by - h.y);
      h.etat = d > 8 ? "colonne" : "forme";
      penser(h, d > 8 ? "rejoindre ma distance de " + enPas(marge) + " pas"
                      : "tenir ma distance de " + enPas(marge) + " pas",
             (ordre.verbe === "appuyer" ? "je dois appuyer " : "je dois suivre ") +
             nomObjet(ordre.objet), "ordre relatif");
      if (d > 3) versLe(h, bx, by, MARCHE, dt);
      return;
    }

    const verrouDeLHomme = h.verrou;
    if (verrouDeLHomme && verrouDeLHomme.etat !== "ouvert") {
      const verrou = verrouDeLHomme;
      const d = Math.hypot(verrou.x - h.x, verrou.y - h.y);
      // SEPT HOMMES DE FRONT, ET PAS UN DE PLUS. C'est la largeur de la porte,
      // et c'est la seule chose qui compte dans tout l'assaut : les trois cents
      // ne valent pas trois cents, ils valent sept à la fois. Sans ce compte,
      // un cercle de deux mètres autour du seuil tient trente hommes, la porte
      // tombe en quarante secondes, et l'on a fabriqué une bataille où le
      // nombre décide — c'est-à-dire l'inverse d'un siège.
      if (h.front) {
        if (d < ALLONGE + 1.2) {
          h.etat = "assaut";
          penser(h, "cogner la porte", "j'ai reçu une place au front", "front de porte");
          verrou.pv -= HACHE * dt;
          // ET LE SEUIL REND LES COUPS. Tenir une hache sous un poste garni
          // coûte des hommes : la riposte se partage entre les sept du front,
          // donc plus ils sont nombreux à cogner, moins chacun encaisse — ce
          // qui est juste, et ce qui fait qu'on n'y va pas à trois.
          //
          // On compte la garnison DEBOUT de cette porte-là, jamais l'effectif
          // nominal : un poste qu'on a saigné cesse de mordre, et c'est
          // exactement ce que l'assaillant vient chercher.
          //
          // On passe par `tomber()` et non par une mort sèche : c'est lui qui
          // tire les deux hommes sur cinq qui restent vivants par terre, et un
          // blessé au pied d'une porte est précisément la scène qu'on vient
          // chercher — il ne bouge plus, il est à une adresse, et il sait quel
          // ordre il avait reçu.
          if (verrou.riposte > 0) {
            h.pv -= (RIPOSTE * verrou.riposte / FRONT_PORTE) * dt;
            if (h.pv <= 0) tomber(h);
          }
          // L'HEURE DU DERNIER COUP, pour l'œil et pour lui seul. L'arc du
          // verrou descendait en silence : rien ne distinguait une porte que
          // sept hommes travaillent d'une porte que personne ne touche depuis
          // vingt minutes. Or c'est exactement le sujet de l'heure creuse.
          verrou.coup = S.temps;
        }
        else { h.etat = "colonne";
               penser(h, "relever une hache au seuil",
                      "une place du front m'a été donnée", "front de porte");
               versLaPorte(h, verrou, d > 40 ? MARCHE : CHARGE, dt); }
      } else if (d > 14) {
        h.etat = "colonne";
        penser(h, "rejoindre " + verrou.nom,
               "mon unité doit prendre cette porte", "ordre de formation");
        versLaPorte(h, verrou, d > 40 ? MARCHE : CHARGE, dt);
      } else {
        // Ceux qui attendent leur tour ne piétinent pas sur le seuil : ils se
        // rangent en arc devant, et c'est de là qu'ils voient tomber les leurs.
        h.etat = "forme";
        penser(h, "attendre une place au seuil",
               "le front est plein et je reste avec la relève", "front de porte");
        const a = (h.escouade / Math.max(1, S.escouades.length)) * Math.PI - Math.PI / 2;
        const [nx, ny] = dehors(h.entree);
        versLe(h, verrou.x + (nx * Math.cos(a) - ny * Math.sin(a)) * 9,
                  verrou.y + (ny * Math.cos(a) + nx * Math.sin(a)) * 9, MARCHE, dt);
      }
      return;
    }

    // --- LE PILLAGE ------------------------------------------------------
    //
    // Ici se décide ce qu'une armée devient une fois entrée. Ce n'est pas un
    // ordre : aucune tête ne dit « pillez », et aucune ne pourrait l'empêcher.
    // C'est un homme qui passe devant une porte et qui s'arrête, ou non.
    //
    // L'APPÉTIT VIENT DE L'HUMEUR DU CORPS, et c'est tout le personnage de
    // chacun. Cranche le ferme ne s'arrête pas — c'est ce qui fait qu'il arrive.
    // Petit Wend le versatile s'arrête devant tout, et son corps se dissout dans
    // les trois cents premiers mètres. les faux gueux le sourd ne pille pas : il
    // brûle, ce qui prend moins de temps et ne rapporte rien.
    if (h.etat === "pille") {
      penser(h, "vider cette maison", "j'ai déjà quitté la colonne pour ce butin",
             "envie · couche 4");
      piller(h, dt); return;
    }
    // « SANS PILLER » — et c'est le seul interdit qui morde vraiment, parce
    // qu'il porte sur la seule chose qu'un homme fasse sans qu'on lui dise.
    // C'est aussi le premier complément qu'un coureur oublie : celui qui
    // arrive essoufflé n'a jamais interdit quoi que ce soit.
    //
    // L'ENVIE SE DEMANDE À LA COUCHE 4, ET ELLE NE SE LIT PLUS DANS UN TABLEAU.
    // `APPETIT[h.humeur]` avait deux défauts, dont le second était grave : tous
    // les hommes d'un corps voulaient la même chose à la troisième décimale, et
    // — depuis que `humeur` a été dissoute dans la couche 1 — le champ n'existe
    // plus sur un homme, si bien que la ligne lisait « — » pour TOUT LE MONDE.
    // Cranche pillait comme les autres et Petit Wend ne se dissolvait plus,
    // sans qu'aucune erreur ne soit levée nulle part.
    //
    // ON CHERCHE LA MAISON D'ABORD, ET C'EST L'INVERSE D'AVANT. La convoitise
    // n'existe pas sans objet : un homme au milieu d'un champ ne veut rien, et
    // ce n'est pas « faiblement » — c'est rien. On regarde donc ce qu'il a sous
    // la main, puis on demande à la couche ce qu'il en pense.
    if (S.bati && !h.chef && !h.front) {
      // On ne quitte pas la colonne à chaque pas : un jet par seconde, sinon
      // tout le monde s'arrête au premier et l'armée n'avance jamais d'un mètre.
      h.tente = (h.tente || 0) - dt;
      if (h.tente <= 0) {
        h.tente = 1;
        const b = maisonLibre(h.x, h.y, PORTEE_MAISON);
        if (b >= 0) {
          const c = h.cercle;
          h.l4 = window.Envie.butin({
            cupide: h.envie ? h.envie.cupide : 0,
            porte: 1,
            // Ce qu'il touche du coude, jamais un compte global : la règle du
            // README, et de toute façon la seule chose qu'il puisse savoir.
            calme: c ? Math.max(-1, 1 - (c.ennemis || 0) * 0.7) : 1,
            frais: h.souffle != null ? h.souffle * 2 - 1 : 0,
            tenu: sousLaBanniere(h) ? 1 : -1,
            // « SANS PILLER » RETIENT, IL N'EMPÊCHE PLUS. C'est un changement
            // de forme assumé : la clause divise l'envie par six au lieu de la
            // fermer, si bien qu'un homme très cupide à qui l'on a dit désobéit
            // parfois — ce qui est la définition même d'un désir gratuit, et ce
            // que le tableau ne pouvait pas dire. Elle reste le seul mot du
            // vocabulaire qui morde sur une envie, et le premier qu'un coureur
            // essoufflé oublie en chemin.
            defendu: interdit(ordre, "piller") ? 1 : -1,
          });
          if (R() < window.Envie.tauxDeButin(h.l4)) {
            S.bati.etat[b] = 1; S.bati.forcees++;      // on la réserve en y allant
            h.maison = b; h.etat = "pille";
            penser(h, "quitter la colonne pour cette maison",
                   "mon envie de butin a vaincu l'ordre et le danger",
                   "envie · couche 4");
            h.reste_pille = cloche(PILLE_S[0], PILLE_S[1]);
            return;
          }
        }
      }
    }

    // --- la porte est tombée : la même unité reçoit une autre destination --
    // Le contrôleur ne sait pas ce qu'est un donjon. Ce point pourrait être un
    // carrefour, un quartier, une grange ou un chef aperçu : changer l'objectif
    // invalide UNE route, celle du vintenar, jamais vingt routes d'hommes.
    h.etat = "colonne";
    menerFormation(h,
      { id: "repere:" + (S.objectif.nom || "objectif"), nom: S.objectif.nom,
        x: S.objectif.x, y: S.objectif.y }, MARCHE, dt);
    penser(h, "rejoindre " + (S.objectif.nom || "l'objectif"),
           "c'est la destination commune de ma vintaine", "ordre de formation");
    if ((S.objectif.x - h.x) ** 2 + (S.objectif.y - h.y) ** 2 < AU_DONJON ** 2) {
      h.etat = "arrive";
      penser(h, "tenir dans la cour", "ma vintaine a atteint son objectif",
             "objectif atteint");
      noter("assaut-au-donjon", h.x, h.y, { clef: "au-donjon" });
    }
  }

  /** Un point sur une polyligne cumulée, plus sa normale et la largeur du lieu. */
  // ---- qui a le droit de cogner ---------------------------------------------
  // La place devant une porte se dispute, et elle se dispute par la DISTANCE :
  // les sept plus proches y sont, les autres attendent. On le décide une fois
  // par pas, pour toute l'armée — laisser chacun juger « reste-t-il une
  // place ? » revient à ce que trois cents hommes croient tous qu'il en reste
  // une, et l'on retrouve la grappe qu'on voulait éviter.
  //
  // LA RELÈVE EST GRATUITE : celui qui tombe cesse d'être le plus proche, et
  // le suivant prend sa place au pas d'après. Personne n'a écrit de rotation.
  function designerLeFront() {
    // UN FRONT PAR PORTE. Il n'y en avait qu'un, celui de la porte principale :
    // les trois autres verrous n'étaient donc frappés par personne, et leurs
    // colonnes attendaient devant un battant que rien n'entamait.
    // ON EFFACE UNE FOIS, PUIS CHAQUE PORTE DÉSIGNE LES SIENS. Chaque appel
    // remettait `front` à faux pour TOUTE l'armée avant de choisir : la
    // deuxième porte effaçait donc le front de la première, la troisième celui
    // de la deuxième, et il ne restait à la fin qu'un seul front pour quatre
    // battants. Symptôme : cinq cents hommes en « forme » et sept qui cognent,
    // pendant que trois portes ne recevaient pas un coup.
    for (const h of S.hommes) h.front = false;
    for (const v of S.verrous) frontDUnVerrou(v);
  }

  function frontDUnVerrou(verrou) {
    if (!verrou || verrou.etat === "ouvert") return;
    // CE QUE LE POSTE A ENCORE DE DEBOUT — c'est lui qui mord (voir RIPOSTE).
    // Debout veut dire debout : ni mort, ni à terre, ni en déroute. Un poste
    // qu'on a saigné cesse de tenir son seuil, et c'est ce qui donne à
    // l'assaillant une raison de faire autre chose que cogner.
    let debout = 0;
    for (const h of S.hommes) {
      if (h.camp !== "garde" || h.verrou !== verrou) continue;
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      debout++;
    }
    verrou.riposte = debout;
    const cand = [];
    for (const h of S.hommes) {
      // Ni la tête, ni un coureur, ni une aile qu'on a fait décrocher. Sans
      // ça, un homme qui porte un ordre à travers la presse se retrouverait
      // désigné pour cogner la porte au passage — et l'ordre n'arriverait
      // jamais, pour une raison que personne n'aurait pu deviner.
      if (h.camp !== "assaut" || h.tete || h.hors || h.etat === "mort" ||
          h.etat === "blesse" || h.etat === "deroute" ||
          h.etat === "coureur" || h.etat === "repli") continue;
      // NI CELUI QU'ON A ENVOYÉ FAIRE AUTRE CHOSE. Une aile qui tient ou qui
      // suit n'est pas là pour cogner : sans ce test, la réserve qu'on tient à
      // deux cents pas se faisait désigner au front dès qu'elle passait par
      // là, et l'ordre qu'on venait de lui donner ne voulait plus rien dire.
      //
      // MAIS CELLE QUI APPUIE, SI — et c'est toute la raison d'être du verbe.
      // Sept haches sur un seuil que le poste mord (voir RIPOSTE) tombent une
      // par une : sans personne pour prendre leur place, une porte ne s'ouvre
      // plus jamais. « Appuyer » est le mot pour RELEVER, et il n'y en a pas
      // d'autre dans toute la nuit.
      const eh = S.escouades[h.escouade];
      const v = eh && eh.ordre ? eh.ordre.verbe : "avancer";
      if (v !== "avancer" && v !== "appuyer") continue;
      cand.push([(h.x - verrou.x) ** 2 + (h.y - verrou.y) ** 2, h]);
    }
    // Une sélection partielle, pas un tri : on ne classe pas trois cents hommes
    // vingt fois par seconde pour n'en garder que sept.
    for (let n = 0; n < FRONT_PORTE && n < cand.length; n++) {
      let m = n;
      for (let i = n + 1; i < cand.length; i++) if (cand[i][0] < cand[m][0]) m = i;
      const t = cand[n]; cand[n] = cand[m]; cand[m] = t;
      cand[n][1].front = true;
    }
  }

  // ---- la machine du verrou -------------------------------------------------
  function porteQuiCede() {
    for (const v of S.verrous) verrouQuiCede(v);
  }

  function verrouQuiCede(verrou) {
    if (!verrou || verrou.etat === "ouvert") return;
    const entree = verrou.porte;
    if (verrou.pv <= 0) {
      verrou.pv = 0;
      verrou.etat = "ouvert";
      noter("porte-enfoncee", verrou.x, verrou.y,
            { clef: "enfoncee:" + entree.nom, dit: { porte: entree.nom } });
      // Elle cède, et la garnison NE RECULE PAS. Elle avait d'abord reflué sur
      // le donjon — c'était propre, et c'était une bataille sans bataille :
      // quarante-cinq hommes traversaient la ville sans jamais croiser un fer,
      // et les trois cents entraient dans une ville vide. Un homme qui garde
      // une porte tient la brèche, parce que la brèche est plus étroite que
      // tout ce qu'il aura derrière. On resserre son poste sur le seuil : c'est
      // là que la vraie mêlée se donne, et sept contre sept.
      const [nx, ny] = dehors(entree);
      let i = 0;
      for (const h of S.hommes) {
        if (h.camp !== "garde" || !h.poste) continue;
        if (Math.hypot(h.poste[0] - entree.x, h.poste[1] - entree.y) > 60) continue;
        const c = (i % 7 - 3) * 0.9, r = Math.floor(i / 7) * 1.2;
        h.poste = [entree.x - nx * (3 + r) - ny * c, entree.y - ny * (3 + r) + nx * c];
        i++;
      }
    } else if (verrou.pv < verrou.max * .5) {
      verrou.etat = "cede";
      noter("porte-cede", verrou.x, verrou.y,
            { clef: "cede:" + entree.nom, dit: { porte: entree.nom } });
      // ET C'EST ICI QU'UN HOMME PART EN COURANT. La première porte qui cède
      // est la première nouvelle que le Donjon puisse recevoir : avant, il n'y
      // a rien à dire ; après, il est trop tard pour que ça change quoi que ce
      // soit. Personne ne l'a envoyé — c'est un homme du guet qui a compris et
      // qui court, et c'est pour ça qu'il part de la porte et non d'un ordre.
      envoyerAuDonjon(verrou);
    }
  }

  /**
   * Un homme du guet part de CETTE porte-là pour le Donjon. Il part de
   * l'intérieur des murs et vingt secondes avant la brèche : c'est toute
   * l'avance qu'il aura sur la colonne, et elle suffit d'ordinaire.
   */
  // IL ÉTAIT DÉJÀ LÀ, ET IL FALLAIT QU'IL Y SOIT. La première version le
  // fabriquait au moment où sa porte cédait — et le four fige le nombre de
  // corps quand on dresse : un homme de plus en cours de bataille, et
  // l'échantillonnage des images clefs écrit dans un fil qui n'existe pas.
  // C'est d'ailleurs plus juste ainsi : un poste de garde n'invente pas un
  // coureur quand il en a besoin, il en a un sous la main depuis le début, et
  // cet homme-là peut très bien être mort avant qu'on ait songé à l'envoyer.
  function envoyerAuDonjon(verrou) {
    if (S.conseil.averti || !S.objectif) return;
    const h = verrou.messager;
    if (!h || h.messager || h.parti) return;
    if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") return;
    h.etat = "coureur";
    h.messager = true;
    h.parti = S.temps;
    h.trace = null; h.avance = 0;
    penser(h, "porter la nouvelle au Donjon Rouge",
           (verrou.porte && verrou.porte.nom ? verrou.porte.nom : "la porte") +
           " est en train de céder", "messager du Guet");
    S.messagers.push(h);
  }

  /**
   * Il court, et il ne rend pas les coups. Par les RUES, sur le même A* que la
   * colonne empruntera derrière lui — c'est le chemin qu'un homme d'ici prend,
   * et le cache le rend gratuit puisque l'assaut le calcule de toute façon.
   */
  function courirAuDonjon(h, dt) {
    penser(h, "porter la nouvelle au Donjon Rouge",
           (h.entree && h.entree.nom ? h.entree.nom : "ma porte") +
           " est en train de céder", "messager du Guet");
    if (!h.trace && S.J && S.voirie) {
      const dep = h.entree || S.entree;
      h.trace = S.J.chemin(S.voirie, [dep.x, dep.y], [S.objectif.x, S.objectif.y],
                         "bataille:donjon:" + (dep.nom || "?"));
      h.avance = 0;
    }
    const tr = h.trace;
    if (!tr || !tr.long) {
      versLe(h, S.objectif.x, S.objectif.y, COURSE, dt);
    } else {
      h.avance = Math.min(tr.long, h.avance + COURSE * dt);
      // Sur l'axe, comme avant — mais par le même chemin que la colonne, pour
      // qu'il n'y ait qu'un seul endroit au monde qui pose un homme sur un rail.
      surLeRail(h, surTrace(tr, h.avance), 0);
    }
    if ((S.objectif.x - h.x) ** 2 + (S.objectif.y - h.y) ** 2 > AU_DONJON ** 2) return;

    // IL EST ARRIVÉ, et c'est seulement maintenant que le Donjon sait quelque
    // chose. Tout ce que les deux lords décideront se compte à partir de cette
    // seconde-ci, qui est celle d'un homme et non celle d'une division.
    h.messager = false;
    h.etat = "tient";
    h.poste = [h.x, h.y];
    if (S.conseil.averti) return;
    S.conseil.averti = S.temps;
    noter("roi-averti", h.x, h.y,
          { clef: "roi-averti",
            dit: { porte: h.entree && h.entree.nom,
                   depuis: +(S.temps - h.parti).toFixed(1),
                   pas: enPas(tr ? tr.long : 0) } });
    S.conseil.tenir  = S.temps + cloche(DELIBERE_TENIR[0], DELIBERE_TENIR[1]);
    S.conseil.ouvrir = S.temps + cloche(DELIBERE_OUVRIR[0], DELIBERE_OUVRIR[1]);
  }

  /**
   * Celui qui n'arrivera pas. On le constate, on l'écrit — un homme qui tombe
   * avec sa nouvelle est exactement le genre de fait qu'on vient chercher — et
   * l'on ne le remplace pas : personne, à sa porte, ne sait qu'il est tombé.
   */
  function lesMessagers() {
    for (let i = S.messagers.length - 1; i >= 0; i--) {
      const h = S.messagers[i];
      if (h.messager && h.etat === "coureur") continue;
      if (h.messager && (h.etat === "mort" || h.etat === "blesse" ||
                         h.etat === "deroute")) {
        h.messager = false;
        noter("messager-tombe", h.x, h.y,
              { dit: { porte: h.entree && h.entree.nom,
                       depuis: +(S.temps - h.parti).toFixed(1),
                       reste: enPas(Math.hypot(S.objectif.x - h.x,
                                               S.objectif.y - h.y)) } });
      }
      S.messagers.splice(i, 1);
    }
  }

  // ===========================================================================
  // LE DONJON — ce qu'on y sait, et à quelle heure
  //
  // L'ÉCART EST LE SUJET, PAS L'ARRIVÉE. Entre la porte qui cède et le moment
  // où quelqu'un le dit dans la salle, il y a six cent treize mètres de rue qui
  // se vide en sens inverse — c'est-à-dire un quart d'heure pendant lequel la
  // ville sait ce que le pouvoir ignore. C'est la seule mesure de tout le
  // fichier qui dise quelque chose du POUVOIR.
  //
  // ET ELLE SE PAIE EN UN HOMME. L'heure d'arrivée n'est pas calculée : c'est
  // celle où un coureur pose le pied dans la cour, et il peut ne jamais l'y
  // poser. Voir `courirAuDonjon`, qui pose `conseil.averti` — ici on ne fait
  // plus que délibérer, ce qui est déjà tout ce que cette salle sait faire.
  //
  // RIEN NE SE DÉCIDE AVANT. Discuter d'ouvrir une porte avant de savoir qu'une
  // porte cède n'aurait aucun sens : on aurait fabriqué un conseil qui devine.
  function leConseil() {
    if (!S.conseil.averti || S.conseil.tranche) return;
    if (S.temps < Math.min(S.conseil.tenir, S.conseil.ouvrir)) return;
    S.conseil.tranche = true;
    if (S.conseil.tenir <= S.conseil.ouvrir) {
      // IL A TRANCHÉ, ET C'EST TOUT CE QU'IL FERA DE LA NUIT. Une ligne, parce
      // qu'un lecteur doit savoir que la question a été posée et par qui elle a
      // été fermée — sinon la porte qui ne s'ouvre pas ressemble à une porte
      // dont personne n'a parlé.
      noter("donjon-tranche", S.objectif.x, S.objectif.y,
            { clef: "donjon-tranche",
              dit: { par: "Ser Merryn Coutre", contre: "le sergent Gaunt le Portier",
                     apres: +(S.conseil.tenir - S.conseil.averti).toFixed(1) } });
      return;
    }
    ouvrirDeDedans();
  }

  /**
   * Ce qu'on ouvre au lieu de le casser. Zéro point de verrou, et une bataille
   * entièrement différente pour trois lignes : c'est la bifurcation la moins
   * chère du modèle, et la seule qui ne passe pas par une hache.
   *
   * ON OUVRE CE QUI EST ENCORE FERMÉ, et c'est la première version qui l'a
   * appris : elle n'ouvrait qu'une porte de ville, et la première cuisson a
   * montré que les quatre étaient enfoncées quatorze minutes après la première
   * nouvelle — c'est-à-dire un quart d'heure avant que la salle ait fini d'en
   * discuter. La branche existait et ne pouvait jamais se produire.
   *
   * Or la décision de Gaunt n'a jamais porté sur un battant particulier :
   * elle porte sur OUVRIR. Reste donc à voir ce qu'il y a encore à ouvrir à
   * l'heure où il l'emporte — une porte, si Gaunt peut encore y porter sa
   * clef ; le Donjon lui-même, sinon, et c'est le cas ordinaire.
   */
  function ouvrirDeDedans() {
    // CELLE QU'ON OUVRE EST CELLE OÙ ILS SONT. Gaunt le Portier a la clef et il
    // l'a sur lui ; il ne va pas la porter à un battant que personne ne frappe.
    let cible = null, best = -1;
    for (const v of S.verrous) {
      if (v.etat === "ouvert") continue;
      let n = 0;
      for (const h of S.hommes)
        if (h.camp === "assaut" && h.verrou === v && !h.hors &&
            h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") n++;
      if (n > best) { best = n; cible = v; }
    }
    if (cible) {
      cible.pv = 0; cible.etat = "ouvert"; cible.par = "dedans";
      noter("porte-ouverte", cible.x, cible.y,
            { clef: "ouverte:" + cible.nom,
              dit: { porte: cible.nom, par: "le sergent Gaunt le Portier",
                     hommes: best,
                     apres: +(S.conseil.ouvrir - S.conseil.averti).toFixed(1) } });
      // LA GARNISON DE CETTE PORTE-LÀ NE TIENT PAS LA BRÈCHE. On ne se bat pas
      // dans un seuil qu'on vient de vous ouvrir dans le dos : elle décroche
      // sur l'anneau, ce qui est la seule chose sensée qu'un homme puisse
      // faire, et qui met quinze hommes de plus autour du Donjon dans l'heure.
      for (const h of S.hommes) {
        if (h.camp !== "garde" || h.verrou !== cible) continue;
        if (h.etat === "mort" || h.etat === "blesse") continue;
        const dx = h.x - S.objectif.x, dy = h.y - S.objectif.y;
        const d = Math.hypot(dx, dy) || 1;
        h.poste = [S.objectif.x + dx / d * 30, S.objectif.y + dy / d * 30];
        signeQuiTombe(h, S.objectif.x, S.objectif.y);
      }
      return;
    }
    // PLUS UNE PORTE DEBOUT : ce qui reste à ouvrir est le Donjon, et c'est
    // exactement ce que Coutre voulait rendre intact. L'anneau des
    // quatre-vingts se retire à l'intérieur des murs — il ne rompt pas, il ne
    // meurt pas, il RENTRE, et les assaillants trouvent une cour au lieu d'un
    // cercle. C'est la seule fin de la nuit où personne ne meurt au donjon.
    S.anneauOuvert = true;
    let n = 0;
    for (const h of S.hommes) {
      if (h.camp !== "garde" || h.etat === "mort" || h.etat === "blesse") continue;
      if (Math.hypot(h.x - S.objectif.x, h.y - S.objectif.y) > AU_DONJON * 2) continue;
      const dx = h.x - S.objectif.x, dy = h.y - S.objectif.y;
      const d = Math.hypot(dx, dy) || 1;
      h.poste = [S.objectif.x + dx / d * 6, S.objectif.y + dy / d * 6];
      h.etat = "rentre";
      n++;
    }
    noter("donjon-ouvert", S.objectif.x, S.objectif.y,
          { clef: "donjon-ouvert",
            dit: { par: "le sergent Gaunt le Portier", contre: "Ser Merryn Coutre",
                   hommes: n,
                   apres: +(S.conseil.ouvrir - S.conseil.averti).toFixed(1) } });
  }

  // ===========================================================================
  // LE ROI SUR SA CHARRETTE
  //
  // Il ne meurt pas d'un coup d'épée, et c'est le point : personne, dans toute
  // cette nuit, ne peut l'atteindre. La garnison ne sort pas, et il est à deux
  // cent trente mètres derrière le fer. Ce qui peut le tuer, c'est SON PROPRE
  // MONDE qui reflue — neuf mille hommes qui refont en courant le chemin par
  // lequel ils sont venus, et il est posé au milieu.
  //
  // Donc : aucune chance tirée, aucun seuil de scénario. On compte les
  // hommes-secondes de déroute qui lui passent dessus, et quand il y en a
  // assez, la charrette verse. Une nuit où l'assaut tient ne le tue jamais ;
  // une nuit où il s'effondre le tue toujours. C'est ce qu'on voulait dire.
  function leRoiSurSaCharrette(dt) {
    if (S.arret || !S.roi || S.roi.etat === "mort" || S.roi.etat === "blesse") return;
    let n = 0;
    autour(S.roi.x, S.roi.y, ROI_PRESSE, (h) => {
      if (h.camp === "assaut" && h.etat === "deroute") n++;
    });
    if (!n) return;
    S.roi.presse = (S.roi.presse || 0) + n * dt;
    if (S.roi.presse < ROI_VERSE * S.ECHELLE) return;
    achever(S.roi);
    noter("roi-tombe", S.roi.x, S.roi.y,
          { clef: "roi", dit: { nom: S.roi.nom, presse: Math.round(S.roi.presse) } });
    S.arret = { quoi: "roi", t: +S.temps.toFixed(1), nom: S.roi.nom };
  }

  // ===========================================================================
  // LA CHAÎNE DE COMMANDEMENT
  //
  // Trois verbes, et pas un de plus. On a tenu la liste courte exprès : un
  // vocabulaire d'ordres qui enfle est un vocabulaire dont chaque mot cesse
  // d'avoir des conséquences visibles, et l'on ne raconte plus rien.
  //
  //   avancer   marcher sur l'objectif — la porte, puis le donjon
  //   tenir     rester où l'on est. On se bat si l'on est joint, on n'avance pas
  //   repli     décrocher vers l'arrière, en ordre, sans avoir rompu
  //
  // « tenir » est le plus important des trois, et c'est le moins évident : une
  // aile en réserve ne meurt pas, ne voit pas mourir, et ne rompt donc pas.
  // Toute la différence entre trois cents hommes qui s'entassent sur un seuil
  // et une armée qui en engage cent.
  // ===========================================================================

  /** Le nom du chef d'un corps — ce qu'on écrit au lieu d'un numéro d'aile. */
  const nomDuCorps = (id) => {
    const c = CORPS.find((x) => x.id === id);
    return c ? c.nom : null;
  };

  /** L'aile d'un homme, ou null s'il n'en a pas (garde, tête). */
  const ailleDe = (h) =>
    (h.camp === "assaut" && !h.tete && !h.hors ? S.ailes[h.aile] : null);

  /** Ce qu'une aile a encore debout, sur ce qu'elle avait. */
  function forceDe(a) {
    let vif = 0, tot = 0;
    for (const h of S.hommes) {
      if (h.camp !== "assaut" || h.tete || h.hors || h.aile !== a.id) continue;
      tot++;
      if (h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") vif++;
    }
    return tot ? vif / tot : 0;
  }

  // --- ce que la tête décide -------------------------------------------------
  // Sa doctrine tient en trois lignes, et c'est assez. On ne lui écrit pas une
  // intelligence : on lui écrit une DOCTRINE, c'est-à-dire quelques règles
  // simples qu'elle applique sans voir le détail — ce qui est exactement la
  // situation d'un homme à cent cinquante mètres de la porte.
  //
  // SIX TÊTES, ET AUCUNE NE COMMANDE LES AUTRES. Chacune ne voit que son
  // corps, ne délibère que pour lui, et ignore parfaitement ce que les cinq
  // autres viennent de décider. C'est de là que sortent les seules images
  // qu'on est venu chercher : deux corps qui pressent la même porte en même
  // temps, ou aucun. Personne n'a écrit ce désordre — il tombe de six horloges
  // qui ne battent pas ensemble.
  // ELLE NE S'APPELLE PLUS `decider`, ET C'EST UNE CORRECTION DE DÉFAUT. Une
  // seconde fonction du même nom est apparue plus haut — celle qui dit si un
  // homme au contact recule —, et deux `function decider` dans une même portée
  // ne cohabitent pas : la dernière déclarée efface l'autre. La tactique
  // appelait donc la chaîne de commandement avec un homme en guise de `dt`,
  // les têtes délibéraient vingt fois par seconde, et rien ne le disait.
  // Celle-ci porte le nom de ce qu'elle fait ; l'autre garde le sien.
  function deciderLesTetes(dt) {
    // Une tête ne délibère plus quand la charrette a versé : il n'y a plus
    // d'affaire à trancher, et son corps ne l'écouterait pas.
    if (S.arret) return;
    for (const tete of S.tetes) {
      if (tete.etat === "mort") continue;
      tete.decide -= dt;
      if (tete.decide > 0) continue;
      tete.decide = cloche(DELIBERE[0], DELIBERE[1]);
      // Les ailes de SON corps, et pas une de plus.
      const sien = S.ailes.filter((a) => a.corps === tete.corps);
      const cons = (CORPS.find((x) => x.id === tete.corps) || {}).consigne;
      // Celles qui peuvent encore tenir un rôle. Sous quatre dixièmes, une aile
      // décroche (branche du dessus) : elle ne presse plus, elle n'appuie plus,
      // et elle ne doit plus occuper la place dans le compte.
      const vifs = sien.filter((x) => forceDe(x) >= 0.4);
      for (const a of sien) {
        let veut;
        if (forceDe(a) < 0.4) veut = ordreDe("repli", { intention: "durer" });
        // SA porte, pas celle du voisin. Avec le verrou global, les quatre
        // têtes ordonnaient d'avancer dès que la première porte cédait — trois
        // corps se jetaient donc sur des battants encore debout parce qu'un
        // autre était tombé à l'autre bout de la ville, et sans qu'aucun
        // coureur ait porté la nouvelle.
        else if (tete.verrou && tete.verrou.etat === "ouvert")
          veut = ordreDe("avancer", { intention: "entrer" });
        // TANT QUE LA PORTE TIENT, UNE SEULE AILE LA PRESSE — la première du
        // corps. Les autres sont en réserve, non par prudence mais par
        // arithmétique : sept hommes cognent, et ceux qui attendent derrière
        // ne font qu'y perdre leur morale en regardant tomber les leurs.
        //
        // MAIS UNE RÉSERVE N'EST PLUS UN PIQUET, et c'est là que les
        // compléments servent. La deuxième aile APPUIE la première — elle se
        // tient à portée de relève au lieu de rester où on l'a posée. La
        // troisième reçoit son ordre d'entrer AVEC SON DÉCLENCHEUR : elle
        // attend que la porte cède, elle le verra elle-même, et personne
        // n'aura à lui porter quoi que ce soit à la minute où ça compte.
        // C'est le seul ordre de toute la nuit qui ne puisse pas se perdre.
        // LES RÔLES SE COMPTENT SUR LES AILES ENCORE DEBOUT, ET C'EST LA
        // RELÈVE. Ils se comptaient sur le rang de déploiement : quand la
        // première aile avait fondu, personne ne prenait sa place — la deuxième
        // continuait d'« appuyer » un mort et les suivantes tenaient leur
        // position pour la nuit. Cinquante-sept pour cent de l'armée à l'arrêt,
        // douze hommes sur la porte, et quatre cent trente-cinq qui rompent.
        //
        // ON A ESSAYÉ DE LES FAIRE SUIVRE, ET C'ÉTAIT PIRE. Toutes les ailes en
        // colonne derrière la première : l'immobilité tombait de 57 à 18 %,
        // mais `suivre` n'ouvre pas le droit de cogner (voir
        // `frontDUnVerrou`) — la Gadoue ne tombait plus du tout, les morts
        // passaient de 113 à 32 et les fuyards de 435 à ZÉRO. On avait rendu
        // la nuit calme, ce qui est l'inverse du sujet. Mesuré, puis jeté.
        //
        // Ce qui manquait n'était pas du mouvement, c'était un ESCALIER : la
        // deuxième aile devient la première quand la première n'existe plus.
        // Une aile sous quatre dixièmes est déjà en repli par la branche du
        // dessus — on la retire donc du compte des rôles, et tout le monde
        // monte d'un cran sans qu'on ait rien à écrire de plus.
        else if (a === vifs[0])
          veut = cons ? ordreDe(cons.verbe, cons)
                      : ordreDe("avancer", { intention: "entrer",
                                             interdit: ["piller"] });
        else if (a === vifs[1])
          veut = ordreDe("appuyer", { objet: { aile: vifs[0].id }, marge: 60,
                                      intention: "couvrir" });
        // ELLE SUIT EN ATTENDANT, ET C'EST CE QUI LA REND JOIGNABLE. L'ordre
        // portait le déclencheur seul : il partait en réserve, l'aile gardait
        // le `tenir` de son déploiement, et elle ne bougeait plus d'un pas de
        // la nuit. Or « quand la porte cède » DEMANDE DE LA VOIR CÉDER, à cent
        // soixante mètres. Une aile plantée à deux cent quatorze — c'est le
        // déploiement de Cranche, de Vantre et des gueux — n'était jamais en
        // vue de la porte qu'on venait de lui nommer.
        //
        // Mesuré sur `essai.reference` : la Gadoue cède à 154,25 s et cinq
        // escouades partent à 154,30 s — celles de Cole, le SEUL corps déployé
        // à cent neuf mètres de sa porte. La porte du Roi cède à 389,7 s, la
        // Vieille Porte à 474,9 : pas un déclencheur ne tombe. Le mécanisme
        // était juste, il n'avait qu'un défaut de géométrie.
        //
        // On lui donne donc l'objet et la marge en même temps que la réserve :
        // elle suit la première aile à cent vingt pas, ce qui la porte à portée
        // de vue du seuil sans la mettre dans la presse — et le jour où la
        // porte cède, elle est là pour entrer.
        else if (a === vifs[2] && tete.verrou)
          veut = ordreDe("avancer", { objet: { aile: vifs[0].id }, marge: 90,
                                      intention: "entrer",
                                      declencheur: { porte: tete.verrou.nom } });
        else veut = ordreDe("tenir", { intention: "couvrir" });
        // On ne redit pas ce qui est déjà dit : c'est la PHRASE qu'on compare,
        // pas son numéro, sinon chaque délibération produirait un ordre neuf
        // identique au précédent et vingt lignes de bruit par minute.
        if (a.ordre && dire(a.ordre) === dire(veut)) continue;
        a.ordre = veut;
        noter("ordre", tete.x, tete.y,
              { dit: { corps: tete.corps, chef: tete.nom, aile: a.id,
                       // Le rang DANS SON CORPS, parce que « l'aile n° 17 » ne
                       // veut rien dire pour personne : c'est un indice de
                       // tableau, et il ne dit ni à qui elle est ni où elle est.
                       rang: a.rang,
                       ordre: veut.verbe, phrase: dire(veut),
                       // PERSONNE NE POUVAIT L'ENTENDRE, et il fallait que la
                       // ligne le dise. La tête des faux gueux ordonne comme
                       // les autres — on lui a retiré les cors, `transmettre`
                       // sort sur `sourd_ne` au pas suivant, et l'ordre meurt
                       // dans sa bouche. Trois lignes sur quinze, dans la
                       // première cuisson : au dépouillement on lisait quinze
                       // ordres donnés pour douze qui pouvaient arriver.
                       //
                       // La tête, elle, n'en sait rien et n'en saura jamais
                       // rien — c'est « rien ne remonte ». Ce champ n'est donc
                       // pas ce qu'elle croit : c'est ce que le lecteur des
                       // annales a le droit de savoir, et lui seul.
                       sourd: S.escouades.every(
                         (e) => e.aile !== a.id || e.sourd_ne) || undefined,
                       force: +forceDe(a).toFixed(2) } });
      }
    }
  }

  // --- DIRE UN ORDRE, ET SAVOIR OÙ EST SON OBJET ----------------------------
  //
  // Les annales ne lisent pas un objet : elles lisent une phrase. Et un ordre
  // qui désigne quelqu'un a besoin de savoir où il est — une fois par pas pour
  // toute l'armée, jamais par homme. À deux mille cinq cents corps et vingt
  // pas par seconde, la différence entre les deux est la cuisson entière.
  const VERBE_DIT = { avancer: "marcher", tenir: "tenir", repli: "décrocher",
                      suivre: "suivre", appuyer: "appuyer" };



  function centres() {
    S.centreAile = []; S.centreCorps = {};
    const sx = [], sy = [], n = [];
    for (const h of S.hommes) {
      if (h.camp !== "assaut" || h.tete || h.hors) continue;
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      const a = h.aile;
      sx[a] = (sx[a] || 0) + h.x; sy[a] = (sy[a] || 0) + h.y; n[a] = (n[a] || 0) + 1;
    }
    for (const a of S.ailes) {
      // SOUS CINQ HOMMES, UNE AILE N'EST PLUS UN REPÈRE. Elle n'a pas disparu
      // du monde, mais on ne peut plus « se tenir à deux cents pas d'elle » :
      // l'ordre qui la désigne devient impossible, et c'est au chef d'en
      // trouver un autre. C'est exactement ce qu'on veut qu'il arrive.
      if (!n[a.id] || n[a.id] < 5) continue;
      S.centreAile[a.id] = [sx[a.id] / n[a.id], sy[a.id] / n[a.id]];
      if (!(a.corps in S.centreCorps)) S.centreCorps[a.corps] = S.centreAile[a.id];
    }
  }

  const centreObjet = (o) => (!o ? null
    : o.aile !== undefined ? (S.centreAile[o.aile] || null)
    : o.corps !== undefined ? (S.centreCorps[o.corps] || null) : null);

  // « de le sergent Rous Cantel » ne se lit pas, et « la 1e aile » non plus.
  // Deux règles de français, écrites une fois : le rang s'abrège en « 1re », et
  // « de » se contracte devant l'article. C'est le même soin que `sac.js` prend
  // sur ses propres lignes — une phrase engendrée qu'on lit à voix haute est
  // une phrase qui doit se lire à voix haute.
  const DU = (nom) => (!nom ? "" : /^le /.test(nom) ? "du " + nom.slice(3)
                                : /^les /.test(nom) ? "des " + nom.slice(4)
                                : "de " + nom);
  const RANG_DIT = (n) => n + (n === 1 ? "re" : "e");

  function nomObjet(o) {
    if (!o) return "";
    if (o.corps !== undefined) return nomDuCorps(o.corps) || o.corps;
    const a = S.ailes[o.aile];
    return a ? "la " + RANG_DIT(a.rang + 1) + " aile" +
               (nomDuCorps(a.corps) ? " " + DU(nomDuCorps(a.corps)) : "") : "";
  }

  /** L'ordre en toutes lettres — c'est ce qui s'écrit, et ce qui se compare. */
  function dire(o) {
    if (!o) return "";
    let s = VERBE_DIT[o.verbe] || o.verbe;
    if (o.objet) s += " " + nomObjet(o.objet);
    if (o.marge) s += " à " + enPas(o.marge) + " pas";
    if (o.declencheur && o.declencheur.porte)
      s += " quand « " + o.declencheur.porte + " » cède";
    if (o.interdit && o.interdit.length) s += " sans " + o.interdit.join(" ni ");
    return s;
  }

  // --- comment il descend ----------------------------------------------------
  function transmettre(dt) {
    for (const e of S.escouades) {
      const fu = S.formations[e.formation];
      // Une unité détachée au ratissage a déjà reçu un ordre autonome. Les
      // signaux de l'ancienne bataille de porte ne doivent pas lui voler un
      // homme ni écraser sa mission pendant l'épreuve.
      if (fu && fu.ratissage) continue;
      const a = S.ailes[e.aile];
      if (!a) continue;
      // SOURD DE NAISSANCE. Une escouade peut devenir sourde en route — plus
      // de bannière, plus personne à envoyer — et celle-là peut réentendre le
      // jour où un chef se relève. Celle de les faux gueux, non : ses deux mille
      // marchent au cantique et aucun ordre ne les a jamais concernés. On sort
      // avant tout le reste, sans quoi on lui chercherait un coureur à chaque
      // pas pour lui porter un ordre qu'elle n'écoutera pas.
      // LE SILENCE MONTE MÊME CHEZ LE SOURD DE NAISSANCE — il n'entend rien,
      // mais il a des yeux, et c'est le compteur qui décidera plus bas s'il
      // finit par faire quelque chose de lui-même.
      e.depuis += dt;

      // ÊTRE SOUS SA BANNIÈRE, C'EST N'ÊTRE PAS SEUL — ET ÇA SE TESTE ICI,
      // AVANT TOUTE SORTIE. C'était plus bas, après trois `continue`, si bien
      // qu'une escouade qui avait déjà reçu son ordre n'atteignait jamais la
      // ligne qui remet son compteur à zéro : elle voyait sa bannière à vingt
      // mètres et se croyait abandonnée depuis dix minutes. Tout le corps de
      // Cranche se mettait à tenir au bout d'une minute, sa porte ne tombait
      // plus, et rien dans les annales ne disait pourquoi.
      const chef = chefDe(e.id);
      const b = a.banniere;
      const enLien = b.debout && chef &&
        (chef.x - b.x) ** 2 + (chef.y - b.y) ** 2 < VUE_BANNIERE ** 2;
      if (enLien) e.depuis = 0;

      // L'ORDRE TENU EN RÉSERVE D'UN DÉCLENCHEUR. Il ne se transmet pas, il
      // ATTEND : l'escouade l'a reçu il y a un quart d'heure et elle regarde
      // la porte. Le jour où elle cède, elle part — sans coureur, sans
      // bannière, sans que personne ait eu à penser à elle.
      if (e.attente && declencheurTombe(e, e.attente.declencheur)) {
        const o = e.attente; e.attente = null;
        delete o.declencheur;
        e.ordre = o; e.depuis = 0;
        marquerOrdreRecu(e);
        const p = centreDe(e.id);
        if (p) noter("declencheur-tombe", p[0], p[1],
                     { dit: { escouade: e.id, aile: a.id, phrase: dire(o) } });
      }
      if (e.sourd_ne) continue;

      // ON N'ENVOIE UN ORDRE QU'UNE FOIS, ET C'EST LA RÈGLE « RIEN NE REMONTE »
      // LUE À L'ENVERS. La tête ne sait pas que son aile a dérivé — donc elle
      // ne la rappelle pas à l'ordre. Sans ce compteur, un chef qui s'invente
      // quelque chose divergeait de son aile, la divergence relançait un
      // coureur, le coureur le remettait en ligne, et l'on obtenait un
      // télégraphe : soixante-dix hommes sur les routes pour quinze escouades,
      // et pas une seule décision qui tienne trente secondes.
      if (e.vu === a.ordre.n) { e.attend = null; continue; }
      // L'ordre est déjà arrivé, ou il attend son heure.
      if (memeOrdre(e.ordre, a.ordre) || memeOrdre(e.attente, a.ordre)) {
        e.vu = a.ordre.n; e.attend = null; continue;
      }
      if (e.attend !== null) {
        // Par la bannière : il suffit d'attendre.
        e.attend -= dt;
        if (e.attend <= 0) { recevoir(e, a.ordre); e.attend = null; }
        continue;
      }
      // UN COUREUR QUI TOMBE BLOQUAIT SON ESCOUADE POUR TOUJOURS. On se
      // contentait de `if (e.coureur) continue` : le jour où l'homme meurt en
      // chemin, la référence reste, l'escouade attend un ordre que plus
      // personne ne porte, et elle n'est même pas déclarée sourde — elle est
      // simplement oubliée, en silence, jusqu'à la fin du sac.
      //
      // C'est le pire genre de faute dans un fichier qu'on cuit : elle ne
      // casse rien, elle ne se voit pas, et elle enlève juste une escouade de
      // l'histoire. On constate donc la chute, on l'écrit — parce qu'un ordre
      // perdu est exactement le genre de fait qu'on est venu chercher — et
      // l'on rouvre la porte à un second messager.
      if (e.coureur) {
        const c = e.coureur;
        if (c.etat === "coureur") continue;   // il court encore
        if (c.etat === "mort" || c.etat === "blesse" || c.etat === "deroute")
          noter("coureur-tombe", c.x, c.y,
                { dit: { vers: e.id, ordre: c.porte && c.porte.verbe,
                         phrase: dire(c.porte) } });
        e.coureur = null;
      }

      // LA BANNIÈRE NE PARLE QU'À QUI LA VOIT, ET QU'À UN CHEF. Un homme
      // regarde le dos de celui de devant ; c'est le chef qui lève la tête.
      // ELLE NE PORTE QU'UN SIGNAL CONVENU. Marcher, tenir, décrocher — et
      // rien qui ait un objet, une distance, une réserve. Tout le reste
      // demande un homme, et c'est ce qui rend la précision chère.
      if (enLien && parBanniere(a.ordre)) {
        e.attend = DELAI_BANN; e.vu = a.ordre.n;
        continue;
      }
      // Sinon, il faut y aller. Et s'il n'y a personne à envoyer, l'escouade
      // est SOURDE : elle exécutera son dernier ordre jusqu'au bout.
      // Qu'il parte ou qu'il n'y ait personne à envoyer, CET ordre-là est
      // joué : on l'a confié, ou on l'a perdu. Dans les deux cas la tête n'en
      // saura rien et ne le redira pas.
      e.vu = a.ordre.n;
      if (!envoyerCoureur(a, e)) {
        if (!e.sourde) {
          e.sourde = true;
          const p = centreDe(e.id);
          if (p) noter("escouade-sourde", p[0], p[1],
                       { clef: "sourde:" + e.id,
                         dit: { escouade: e.id, aile: a.id,
                                ordre: e.ordre && e.ordre.verbe,
                                phrase: dire(e.ordre) } });
        }
      }
    }
  }

  /**
   * CE QUI ARRIVE, ET OÙ ÇA SE RANGE. Un ordre sans déclencheur s'applique ;
   * un ordre qui en porte un se met en réserve et l'escouade se remet à
   * regarder. Dans les deux cas, elle vient d'avoir des nouvelles — le
   * compteur du silence repart de zéro, et c'est la seule chose qui empêche
   * un chef bien commandé de s'inventer un ordre à lui.
   */
  function recevoir(e, o) {
    const n = copie(o);
    e.depuis = 0;
    if (n.declencheur) {
      e.attente = n;
      // ET ELLE PREND SA POSTURE D'ATTENTE. Un ordre à déclencheur ne disait
      // rien de ce qu'on fait EN ATTENDANT : l'escouade gardait son ordre
      // précédent, qui est le `tenir` de son déploiement, et attendait de voir
      // céder une porte qu'elle n'avait aucun moyen d'approcher. Quand l'ordre
      // désigne quelqu'un, on tient la place qu'il dit — c'est la même phrase,
      // avec son verbe d'attente au lieu de son verbe d'entrée.
      if (n.objet) e.ordre = { verbe: "suivre", objet: n.objet, marge: n.marge,
                               intention: n.intention, n: n.n };
      marquerOrdreRecu(e);
      return;
    }
    e.attente = null;
    e.ordre = n;
    marquerOrdreRecu(e);
  }

  // La bulle appartient au cadre de formation, mais la phrase arrive à
  // l'escouade. Ce pont date l'instant où CES hommes l'ont effectivement
  // reçue — pas celui où une tête l'a prononcée cinquante mètres plus loin.
  function marquerOrdreRecu(e) {
    const u = e && S.formations[e.formation];
    if (!u || !e.ordre) return;
    u.ordre.texte = dire(e.ordre);
    u.ordre.donneA = S.temps;
    u.ordre.ditA = S.temps;
  }

  /**
   * « Quand la porte cède » — et il faut la VOIR céder. C'est toute la beauté
   * et tout le danger de la chose : une escouade postée à six cents mètres de
   * la porte qu'on lui a nommée attendra la nuit entière, et elle aura raison.
   */
  function declencheurTombe(e, d) {
    if (!d) return false;
    if (d.porte) {
      const v = S.verrous.find((w) => w.nom === d.porte);
      if (!v || v.etat === "fermee" || v.etat === undefined) return false;
      if (v.etat !== "ouvert" && v.etat !== "cede") return false;
      const p = centreDe(e.id);
      return !!p && Math.hypot(p[0] - v.x, p[1] - v.y) < VUE_DECLENCHEUR;
    }
    return false;
  }

  // ===========================================================================
  // CE QU'UN CHEF S'INVENTE QUAND RIEN N'ARRIVE
  // ===========================================================================
  // Un chef sans ordre neuf n'improvise pas dans le vide : il descend un
  // escalier de trois marches, et il s'arrête à la première qui le porte.
  //
  //   1. LA CONSIGNE — ce qu'on lui a dit avant la nuit. Elle ne se transmet
  //      pas, elle est déjà dans sa tête, et c'est le seul ordre qui arrive
  //      toujours à destination.
  //   2. L'INTENTION — le POURQUOI du dernier ordre reçu. Quand cet ordre est
  //      devenu impossible (l'aile qu'il devait suivre n'existe plus), il ne
  //      reste pas planté devant un mort : il refait un verbe depuis le motif.
  //   3. SON TEMPÉRAMENT — s'il n'a ni l'une ni l'autre. Et là c'est l'humeur
  //      de son corps qui parle, ce qui est la définition même d'un homme
  //      qu'on a cessé de commander.
  //
  // ON ÉCRIT LE MOTIF, TOUJOURS. Sans lui, on relit au matin une bataille où
  // des ailes désobéissent sans qu'on sache jamais pourquoi — et c'est
  // exactement ce qu'on est venu chercher ici.
  function initiative(dt) {
    for (const e of S.escouades) {
      const fu = S.formations[e.formation];
      if (fu && fu.ratissage) continue;
      const a = S.ailes[e.aile];
      if (!a) continue;
      // Un ordre devient PÉRIMÉ quand son objet a disparu du monde. Ça ne
      // s'attend pas : ça se constate au pas où ça arrive.
      const perime = !!(e.ordre && e.ordre.objet && !centreObjet(e.ordre.objet));
      // Il faut quelqu'un pour décider. Une escouade sans chef ne s'invente
      // rien du tout — elle continue, et c'est déjà écrit ailleurs. ON LE
      // CHERCHE AVANT LE SEUIL, désormais : c'est SA patience qu'on mesure, et
      // non celle d'un tableau. Le déplacement ne change rien au compte — une
      // escouade sans chef sortait déjà juste après.
      const chef = chefDe(e.id);
      if (!chef) { e.depuis = 0; continue; }
      // CE QU'IL SUPPORTE DE SILENCE — demandé à la couche 4, homme par homme.
      // `SILENCE[e.humeur]` donnait un seuil en secondes qui ne savait rien de
      // ce qui se passait autour : un chef dont la bannière est à terre et dont
      // l'aile a fondu attendait ses soixante secondes exactement comme un
      // chef dont la nuit était calme. Ici, les deux ne tiennent pas pareil.
      const c = chef.cercle;
      const seuil = window.Envie.silenceTenu(window.Envie.patience({
        docile: chef.envie ? chef.envie.docile : 0,
        signe: (a.banniere.debout && sousLaBanniere(chef)) ? 1 : -1,
        entier: forceDe(a) * 2 - 1,
        sur: perime ? -1 : 1,
        alarme: c ? Math.max(-1, 1 - (c.ennemis || 0) * 0.7) : 1,
        // Le sourd de naissance ne compte pas le silence : il n'y a jamais eu
        // autre chose pour lui, donc il porte son premier ordre jusqu'au bout.
        jamaisEntendu: !!e.sourd_ne,
      }));
      if (!perime && e.depuis < seuil) continue;

      const cons = (CORPS.find((x) => x.id === e.corps) || {}).consigne;
      let neuf = null, motif = null;
      if (perime && e.ordre.intention && DE_LINTENTION[e.ordre.intention]) {
        neuf = ordreDe(DE_LINTENTION[e.ordre.intention],
                       { intention: e.ordre.intention });
        motif = "son objet a disparu";
      } else if (cons && !perime) {
        neuf = ordreDe(cons.verbe, cons);
        motif = "sans nouvelles depuis " + Math.round(e.depuis) + " s";
      } else {
        // SA MANIÈRE DÉCIDE, ET C'EST LA COUCHE 3 QUI LA TIENT. On la lui
        // demande sur le chef, parce que c'est lui qui décide, et l'on retombe
        // sur « tenir » s'il n'a pas encore été observé — un homme sans
        // manière connue ne s'invente rien.
        neuf = ordreDe((chef.l3 && window.Interpretation.deSoiMeme(chef.l3))
                       || "tenir",
                       { intention: e.ordre && e.ordre.intention });
        motif = perime ? "son objet a disparu"
                       : "sans nouvelles depuis " + Math.round(e.depuis) + " s";
      }
      // On ne s'invente pas ce qu'on fait déjà — sans quoi le compteur
      // remettrait la même phrase toutes les vingt-cinq secondes, à jamais.
      e.depuis = 0;
      if (e.ordre && dire(e.ordre) === dire(neuf)) continue;
      e.ordre = neuf; e.attente = null;
      marquerOrdreRecu(e);
      const p = centreDe(e.id);
      if (p) noter("initiative", p[0], p[1],
                   { dit: { escouade: e.id, aile: a.id, corps: e.corps,
                            chef: nomDuCorps(e.corps),
                            phrase: dire(neuf), motif } });
    }
  }

  function chefDe(id) {
    for (const h of S.hommes)
      if (h.camp === "assaut" && h.escouade === id && h.chef &&
          h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") return h;
    return null;
  }

  function centreDe(id) {
    let x = 0, y = 0, n = 0;
    for (const h of S.hommes) {
      if (h.camp === "assaut" && h.escouade === id &&
          h.etat !== "mort" && h.etat !== "blesse") { x += h.x; y += h.y; n++; }
    }
    return n ? [x / n, y / n] : null;
  }

  // UN COUREUR EST UN HOMME EN MOINS, et c'est le prix. On le prend dans
  // l'escouade du capitaine — pas dans celle qu'on veut joindre, qui par
  // définition n'entend rien.
  function envoyerCoureur(a, e) {
    // QUI ENVOIE. C'était le capitaine, et lui seul — ce qui rendait cette
    // fonction rigoureusement inatteignable : on n'envoie un coureur que
    // lorsque la bannière est tombée, et la bannière tombe exactement quand le
    // capitaine tombe. La branche entière était morte par construction, et
    // l'aile passait droit à « sourde » sans que personne ait couru.
    //
    // Un ordre ne dépend pas d'un seul homme : à défaut du capitaine, c'est le
    // premier chef encore debout de l'aile qui dépêche quelqu'un. L'aile n'est
    // muette que lorsqu'il ne lui reste plus un seul gradé.
    const chef = (a.capitaine && a.capitaine.etat !== "mort" &&
                  a.capitaine.etat !== "blesse" && a.capitaine.etat !== "deroute")
                 ? a.capitaine : premierChefDe(a.id);
    if (!chef) return false;
    const but = centreDe(e.id);
    if (!but) return false;
    const src = chef.escouade;
    for (const h of S.hommes) {
      if (h.camp !== "assaut" || h.escouade !== src) continue;
      if (h.chef || h.capitaine || h.tete) continue;
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute" ||
          h.etat === "coureur") continue;
      h.etat = "coureur";
      // IL PORTE UNE COPIE, ET C'EST TOUT LE SUJET. L'ordre de l'aile ne bouge
      // pas ; celui qui court dans la presse, si — il s'abîme dans sa tête à
      // lui, et ce qu'il posera là-bas ne sera plus tout à fait ce qu'on lui a
      // dit. Sans copie, on dégraderait l'original et l'aile entière oublierait
      // ce que son chef vient d'ordonner.
      h.porte = copie(a.ordre);
      h.peine = 0;
      h.chez = e.id;
      penser(h, "remettre « " + dire(h.porte) + " » à l'escouade " + e.id,
             "mon aile ne peut pas lui transmettre cette phrase par sa bannière",
             "coureur d'ordre");
      e.coureur = h;
      noter("coureur-part", h.x, h.y,
            { dit: { aile: a.id, rang: a.rang, corps: a.corps,
                     chef: nomDuCorps(a.corps), vers: e.id,
                     ordre: a.ordre.verbe, phrase: dire(a.ordre) } });
      return true;
    }
    return false;
  }

  function courir(h, dt) {
    const e = S.escouades[h.chez];
    const but = centreDe(h.chez);
    penser(h, "remettre « " + dire(h.porte) + " » à l'escouade " + h.chez,
           "je porte l'ordre qui m'a été confié", "coureur d'ordre");
    // CELUI QUI ARRIVE ET NE TROUVE PLUS PERSONNE. C'était un `return` muet, et
    // c'est le troisième trou de la même famille que les deux qu'on a déjà
    // bouchés : l'homme est réabsorbé dans la colonne, son ordre disparaît, et
    // pas une ligne nulle part.
    //
    // Mesuré sur `essai.reference` : 54 coureurs partis, 50 arrivés, ZÉRO
    // `coureur-tombe`. Les quatre manquants portaient tous « décrocher » à
    // 403,3 s, vers les escouades de la deuxième aile de Cole — celle qui était
    // en train de fondre. `centreDe` rend `null` sous cinq hommes : l'escouade
    // n'était plus un repère, le coureur n'avait plus de destination, et le
    // dernier ordre que Criston Cole ait donné de la nuit n'est jamais arrivé
    // nulle part.
    //
    // C'est le fait le plus intéressant de la nuit et il n'était pas écrit :
    // l'ordre de repli d'un corps qui s'effondre se perd PARCE QUE le corps
    // s'effondre. On l'écrit.
    if (!e || !but) {
      noter("ordre-sans-personne", h.x, h.y,
            { dit: { vers: h.chez, ordre: h.porte && h.porte.verbe,
                     phrase: dire(h.porte) } });
      rendreCoureur(h);
      return;
    }
    const avant = { x: h.x, y: h.y };
    const d = versLe(h, but[0], but[1], COURSE, dt);
    // CE QU'IL PERD EN CHEMIN. On compte ses mètres, et double quand il traverse
    // du monde — une phrase se retient mal en jouant des coudes. Chaque épreuve
    // franchie lui coûte une subordonnée, en commençant par la fin : ce qui
    // restreint s'oublie avant ce qu'on doit faire.
    h.peine = (h.peine || 0) + Math.hypot(h.x - avant.x, h.y - avant.y) *
      (ennemiProche(h, 12) ? 2 : 1);
    if (h.peine >= EPREUVE_M) {
      h.peine -= EPREUVE_M;
      const perdu = degrader(h.porte);
      if (perdu) noter("ordre-deforme", h.x, h.y,
                       { dit: { vers: h.chez, perdu, phrase: dire(h.porte) } });
    }
    if (d > 4) return;
    // Il est arrivé. L'ordre entre — et s'il n'y avait plus de chef, il en
    // fait un : c'est la seule façon dont une escouade sourde redevient
    // commandable, et ça vaut d'être vu passer.
    recevoir(e, h.porte);
    e.attend = null;
    if (e.sourde) {
      e.sourde = false;
      noter("escouade-reprise", h.x, h.y,
            { dit: { escouade: e.id, ordre: h.porte.verbe } });
    }
    if (!chefDe(e.id)) {
      h.chef = true;
      noter("nouveau-chef", h.x, h.y, { dit: { escouade: e.id } });
    }
    noter("coureur-arrive", h.x, h.y,
          { dit: { vers: e.id, ordre: h.porte.verbe, phrase: dire(h.porte) } });
    rendreCoureur(h, e.id);
  }

  /**
   * UNE PHRASE PERD SES SUBORDONNÉES AVANT SON VERBE. On retire la première
   * clause encore présente dans l'ordre écrit plus haut — et les nombres ne
   * disparaissent pas d'un coup : ils s'arrondissent d'abord, et de travers.
   * « à deux cents pas » devient « à deux cent cinquante », puis plus rien.
   */
  function degrader(o) {
    for (const c of CLAUSES) {
      if (o[c] === undefined || o[c] === null) continue;
      if (c === "marge" && !o.arrondi) {
        o.arrondi = true;
        o.marge = Math.max(30, Math.round(o.marge / 50) * 50 +
                               (R() < 0.5 ? -50 : 50));
        return "marge";
      }
      delete o[c];
      return c;
    }
    return null;
  }

  function rendreCoureur(h, chez) {
    const e = S.escouades[h.chez];
    if (e && e.coureur === h) e.coureur = null;
    // Il reste où il est arrivé : on ne renvoie personne en arrière dans une
    // bataille. Son escouade devient celle qu'il vient de joindre.
    if (chez !== undefined) {
      h.escouade = chez;
      const cible = S.escouades[chez];
      if (cible && cible.formation != null)
        changerDeFormation(h, S.formations[cible.formation], !!h.chef);
    }
    h.porte = null; h.chez = null;
    h.etat = "colonne";
  }

  // --- la bannière -----------------------------------------------------------
  // Elle suit son porteur tant qu'il est debout, elle reste où il est tombé
  // ensuite. Sa chute est le seul choc de morale du module qui ne décroisse
  // pas avec la distance — et c'est voulu : on ne voit pas tomber un homme à
  // cent mètres, on voit tomber une bannière.
  function bannieres(dt) {
    for (const a of S.ailes) {
      const c = a.capitaine;
      const bas = !c || c.etat === "mort" || c.etat === "blesse" ||
                  c.etat === "deroute";
      if (a.banniere.debout && bas) {
        a.banniere.debout = false;
        a.releve = RELEVE;
        for (const h of S.hommes)
          if (h.camp === "assaut" && !h.tete && h.aile === a.id &&
              h.etat !== "mort" && h.etat !== "blesse")
            signeQuiTombe(h, a.banniere.x, a.banniere.y);
        // Le corps et le rang, comme pour les ordres : une bannière appartient
        // à quelqu'un, et « l'aile n° 13 » n'appartient à personne.
        noter("banniere-tombe", a.banniere.x, a.banniere.y,
              { dit: { aile: a.id, corps: a.corps, rang: a.rang,
                       chef: nomDuCorps(a.corps) } });
        continue;
      }
      if (a.banniere.debout) { a.banniere.x = c.x; a.banniere.y = c.y; continue; }
      // La relever prend du temps, et il faut quelqu'un pour la lever.
      a.releve -= dt;
      if (a.releve > 0) continue;
      const n = premierChefDe(a.id);
      if (!n) { a.releve = RELEVE; continue; }
      n.capitaine = true;
      a.capitaine = n;
      a.banniere = { debout: true, x: n.x, y: n.y };
      noter("banniere-relevee", n.x, n.y,
            { dit: { aile: a.id, corps: a.corps, rang: a.rang,
                     chef: nomDuCorps(a.corps) } });
    }
  }

  function premierChefDe(id) {
    for (const h of S.hommes)
      if (h.camp === "assaut" && !h.tete && h.aile === id && h.chef &&
          h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") return h;
    return null;
  }

  /** Voit-il sa bannière ? C'est ce qui le fait tenir. */
  // CE QUI LE FAIT REDESCENDRE PLUS VITE — le poste 3 de la depose.
  //
  // `TIENT_BANN` et `rallier` sont les deux SEULS mecanismes par lesquels un
  // commandement protege ses hommes au lieu de les deplacer. Ils vivaient dans
  // `morale`, qui va disparaitre ; ils passent donc a la couche 1, et par la
  // seule porte qui leur convienne : la constante de DESCENTE de l'alarme.
  //
  // On ne transporte pas le ralliement lui-meme — ramener un homme qui court
  // est un acte d'AUTORITE, donc de la couche 3, et `rallier()` reste ou il
  // est. Ce qui monte ici est la simple PRESENCE : un chef qu'on voit encore
  // debout a quinze metres.
  //
  // `chefVu` est estampe par le chef lui-meme (voir la diffusion dans
  // `soldat`). On le tient pour vrai le temps d'un coup d'oeil ; au-dela, il
  // n'est plus la, et c'est exactement ce qu'on veut dire.
  const CHEF_FRAIS = 3;
  function apaiseDe(h) {
    let a = 1;
    if (sousLaBanniere(h)) a *= window.Corps.M.APAISE_BANN;
    if (h.chefVu != null && S.temps - h.chefVu < CHEF_FRAIS)
      a *= window.Corps.M.APAISE_CHEF;
    return a;
  }

  function sousLaBanniere(h) {
    const a = ailleDe(h);
    if (!a || !a.banniere.debout) return false;
    return (h.x - a.banniere.x) ** 2 + (h.y - a.banniere.y) ** 2 < VUE_BANNIERE ** 2;
  }

  // --- le ralliement ---------------------------------------------------------
  // UN HOMME QUI ROMPT N'EST PLUS PERDU. C'était le cas jusqu'ici : `deroute`
  // était un état absorbant, et l'armée ne faisait que se vider. Un chef vivant
  // qui l'a encore sous la main le ramène — et comme un fuyard court plus vite
  // qu'un chef, ça ne marche que dans les premiers instants. C'est bien : le
  // ralliement doit être une chose qu'on rate le plus souvent.
  function rallier(h, dt) {
    let chef = null;
    autour(h.x, h.y, RALLIE_M, (o) => {
      if (chef || o.camp !== h.camp) return;
      if (!o.chef && !o.capitaine) return;
      if (o.etat === "mort" || o.etat === "blesse" || o.etat === "deroute") return;
      chef = o;
    });
    if (!chef) return false;
    // ⚠ IL REVIENT QUAND SON CORPS NE LE FAIT PLUS COURIR — et pas quand une
    // jauge repasse un seuil. C'est la depose de `RALLIE_TAUX` et de
    // `RALLIE_SEUIL`, et elle ne coute AUCUNE constante neuve : la couche 1
    // porte deja les deux moitiees de ce que ces deux nombres disaient.
    //
    //   la VITESSE du retour — c'est `apaise` : la presence de ce chef-ci fait
    //     retomber son alarme quatre fois plus vite (45 s deviennent 12).
    //   l'HYSTERESIS — c'est `INTERDIT_JAMBES` : on ne sort d'une fuite que par
    //     `planté`, jamais par un recul ni une ruee. Le seuil de retour plus
    //     haut que le seuil de rupture etait la meme idee, ecrite a la main.
    //
    // Et l'on garde ce qui faisait la valeur de ce mecanisme : un fuyard court
    // plus vite qu'un chef, donc la fenetre se referme en quelques secondes.
    // ⚔️ 90312 — LE PREMIER CRAN DU BRANCHEMENT, ET IL N'EN FAIT QU'UN.
    //
    // C'ETAIT LE SEUL ACCES A `h.l1` DE TOUT CE FICHIER HORS DE `soldat()`
    // (releve par Bren le 3e : quatorze appels vivants aux couches, un seul
    // ici). Un appelant unique, deja ecrit, qui lisait deja la couche en
    // direct : c'est l'essai le moins cher qui existe, et c'est pour ca qu'on
    // commence par lui et non par la nappe de `soldat()`.
    //
    // CE QUI CHANGE EST LA QUESTION, PAS LA REPONSE. On lisait le MOT de la
    // couche 1 — « est-ce qu'il dit fuite ? ». On demande maintenant a
    // l'arbitre QUI TIENT SES JAMBES ce battement-ci. Un homme se rallie
    // quand l'ordre les a reprises, et pas autrement : c'est la definition du
    // ralliement, et c'est le mot que `5-qui-conduit.js` rend deja.
    //
    // POURQUOI `!== "ordre"` ET NON `=== "corps"`. Les deux traduisent le
    // vieux test, et la difference porte sur deux cas que `h.l1.jambes` ne
    // savait pas ecrire. Un homme dont la REFLEXION tient les jambes est en
    // train de se raisonner pour sortir : le rallier serait le renvoyer en
    // ligne au moment precis ou il decide de n'y pas rester. Un homme que
    // l'ENVIE tient a lache la colonne pour une maison — un chef a portee ne
    // le ramene pas davantage. Aucun des deux n'obeit ; aucun des deux ne se
    // rallie.
    //
    // ⚠ LE GEL DE 🔒 90260 NE TOUCHE PAS CETTE LIGNE, et je l'ai verifie
    // plutot que suppose. Il mord sur les hommes qui TOMBENT — `soldat()`
    // rend la main a `mort` (l.2968) et a `blesse` (l.2970) AVANT l'observation,
    // donc leur derniere sortie de couche reste au chaud jusqu'au matin. Un
    // homme `deroute`, lui, traverse l'observation a chaque battement de son
    // oeil : `h.conduit` est ici aussi frais que `h.l1` l'etait, pas moins.
    // C'est pourquoi je branche avant de reparer le gel.
    //
    // SANS L'ARBITRE, LE VIEUX TEST. Ce n'est pas une politesse : c'est le bras
    // temoin de la mesure. Retirer `5-qui-conduit.js` de la chaine rend
    // exactement la conduite d'hier, sur le meme fichier, sans reecrire une
    // ligne — voir `analyse/branchement-90312/`.
    if (h.conduit) { if (h.conduit !== "ordre") return true; }
    else if (!h.l1 || h.l1.jambes === "fuite") return true;
    h.etat = "forme";
    h.ruptureCause = null; h.fuiteStrategie = null;
    h.fuiteGroupeX = null; h.fuiteGroupeY = null;
    compte.fuyards--;
    compte.rallies++;
    noter("ralliement", h.x, h.y, { dit: { escouade: h.escouade } });
    return true;
  }

  // ---- les foyers : on fuit une MASSE, pas un homme -------------------------
  // La menace se cherchait sur les quatre cent vingt-cinq corps, pour chaque
  // habitant qui panique et à chaque pas : deux mille fois quatre cent
  // vingt-cinq, vingt fois par seconde. C'était le seul endroit de la couche
  // qui ne passait pas à l'échelle — et c'était en plus le mauvais modèle.
  //
  // On agrège donc les soldats vivants par carrés de quarante mètres, et l'on
  // ne garde que les carrés qui portent au moins trois hommes. Trois douzaines
  // de foyers au lieu de quatre cents corps, et surtout : UN HOMME SEUL N'EST
  // PAS UNE ARMÉE. Un fuyard qui traverse une rue ne vide plus le quartier,
  // ce qui est exactement ce qu'on observe — on s'écarte d'un soldat, on fuit
  // une troupe.

  function fondreLesFoyers() {
    const cases = new Map();
    for (const h of S.hommes) {
      // Un blessé n'est pas une armée : on ne fuit pas un homme à terre, on
      // s'en approche ou l'on passe au large. C'est la même règle que le
      // fuyard isolé, et pour la même raison.
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      const c = Math.floor(h.x / FOYER_M) + ":" + Math.floor(h.y / FOYER_M);
      let f = cases.get(c);
      if (!f) cases.set(c, f = { x: 0, y: 0, n: 0 });
      f.x += h.x; f.y += h.y; f.n++;
    }
    S.foyers = [];
    for (const f of cases.values())
      if (f.n >= FOYER_MIN) S.foyers.push({ x: f.x / f.n, y: f.y / f.n, n: f.n });
  }

  /** Le foyer le plus proche, et sa distance. Rend null s'il n'y a rien. */
  function foyerProche(x, y) {
    let m = null, dmin = Infinity;
    for (const f of S.foyers) {
      const d = (f.x - x) ** 2 + (f.y - y) ** 2;
      if (d < dmin) { dmin = d; m = f; }
    }
    return m ? { f: m, d: Math.sqrt(dmin) } : null;
  }

  // ---- le réseau : fuir PAR LES RUES ----------------------------------------
  // La panique était un pilotage libre : on s'éloignait du fer en ligne droite,
  // donc à travers les maisons. C'était le défaut le plus visible de la couche
  // — une ville dont les murs arrêtent une armée mais pas ses habitants.
  //
  // ON NE CALCULE POURTANT AUCUN CHEMIN. Un A* par fuyard, c'est deux mille A*
  // par seconde, et il n'en est pas question. On marche le graphe de proche en
  // proche : arrivé à un carrefour, on prend la branche qui éloigne le plus (ou
  // qui rapproche le plus, quand on rentre), et l'on ne fait pas demi-tour. Un
  // homme qui fuit ne connaît pas le plan de la ville : il prend la rue qui
  // s'éloigne. C'est le bon modèle ET le modèle bon marché, ce qui n'arrive pas
  // souvent.
  const SEAU = 100;

  function tisserReseau() {
    if (S.reseau || !S.voirie) return;
    const seau = new Map();
    for (const [id, n] of S.voirie.noeuds) {
      const c = Math.floor(n.xyz[0] / SEAU) + ":" + Math.floor(n.xyz[1] / SEAU);
      let l = seau.get(c);
      if (!l) seau.set(c, l = []);
      l.push(id);
    }
    S.reseau = { seau, noeuds: S.voirie.noeuds };
  }

  function noeudProche(x, y) {
    if (!S.reseau) return null;
    const ci = Math.floor(x / SEAU), cj = Math.floor(y / SEAU);
    let meil = null, dmin = Infinity;
    for (let r = 1; r < 12 && meil === null; r++) {
      for (let di = -r; di <= r; di++) for (let dj = -r; dj <= r; dj++) {
        if (r > 1 && Math.abs(di) < r && Math.abs(dj) < r) continue;
        for (const id of S.reseau.seau.get((ci + di) + ":" + (cj + dj)) || []) {
          const p = S.reseau.noeuds.get(id).xyz;
          const d = (p[0] - x) ** 2 + (p[1] - y) ** 2;
          if (d < dmin) { dmin = d; meil = id; }
        }
      }
    }
    return meil;
  }

  // Une rue n'est pas un segment : c'est une polyligne, et la suivre est ce qui
  // fait la différence entre longer un mur et le traverser en diagonale. On
  // oriente et l'on cumule UNE FOIS par lien — les liens sont partagés par tous
  // ceux qui fuient dans la même rue, ce qui est le cas général.
  const _arcs = new WeakMap();
  function arcDe(lien) {
    let a = _arcs.get(lien);
    if (a) return a;
    const t = lien.arete.trace;
    const pts = lien.sens > 0 ? t : t.slice().reverse();
    const cum = new Float64Array(pts.length);
    for (let i = 1; i < pts.length; i++)
      cum[i] = cum[i - 1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]);
    a = { pts, cum, long: cum[cum.length - 1] || 0, vers: lien.vers };
    _arcs.set(lien, a);
    return a;
  }

  function choisirLien(noeudId, bx, by, fuir, venu) {
    const n = S.reseau && S.reseau.noeuds.get(noeudId);
    if (!n || !n.liens.length) return null;
    let meil = null, best = -Infinity;
    for (const l of n.liens) {
      const p = S.reseau.noeuds.get(l.vers);
      if (!p) continue;
      const d = Math.hypot(p.xyz[0] - bx, p.xyz[1] - by);
      // ON NE FAIT PAS DEMI-TOUR — sauf en cul-de-sac, où la pénalité se laisse
      // battre parce qu'il n'y a rien d'autre. Sans ça, un fuyard oscille entre
      // deux carrefours dès que la menace le dépasse.
      let s = (fuir ? d : -d) - (l.vers === venu ? 1e4 : 0);
      if (s > best) { best = s; meil = l; }
    }
    return meil;
  }

  /** Un pas de marche sur le réseau. Rend faux quand la rue manque. */
  function marcher(p, dt, bx, by, fuir) {
    if (!S.reseau) return false;
    // D'abord GAGNER LA RUE. On panique où l'on est — sur un seuil, au milieu
    // d'une cour —, pas sur un carrefour : sans ce premier bout en ligne
    // droite, le fuyard se téléporte de trente mètres à son premier pas.
    if (!p.surRue) {
      const n = S.reseau.noeuds.get(p.noeud);
      if (!n) return false;
      const dx = n.xyz[0] - p.x, dy = n.xyz[1] - p.y, d = Math.hypot(dx, dy);
      const pas = p.v * dt;
      if (d > pas) { p.x += (dx / d) * pas; p.y += (dy / d) * pas; return true; }
      p.x = n.xyz[0]; p.y = n.xyz[1]; p.surRue = true;
      return true;
    }
    let reste = p.v * dt, garde = 0;
    while (reste > 0 && garde++ < 8) {
      if (!p.arc) {
        const l = choisirLien(p.noeud, bx, by, fuir, p.venu);
        if (!l) return false;
        p.arc = arcDe(l); p.venu = p.noeud; p.noeud = l.vers; p.s = 0;
        if (p.arc.long <= 0) { p.arc = null; continue; }
      }
      const dispo = p.arc.long - p.s;
      if (reste < dispo) { p.s += reste; reste = 0; }
      else { reste -= dispo; p.arc = null; }
    }
    if (p.arc) { const q = surTrace(p.arc, p.s); p.x = q[0]; p.y = q[1]; }
    else { const n = S.reseau.noeuds.get(p.noeud);
           if (n) { p.x = n.xyz[0]; p.y = n.xyz[1]; } }
    return true;
  }

  // ---- la machine du bourgeois ----------------------------------------------
  // Cinq états, et ils ne tournent QUE sur ceux que `derange` a pris en charge :
  // les quatre cent mille autres n'existent pas ici, et c'est ce qui rend la
  // chose gratuite.
  //
  //   saisi    on ne part pas en courant : on se retourne, et l'on comprend
  //   fuite    par les rues, en s'éloignant de la masse
  //   rentre   la peur passée, on regagne son seuil — par les rues aussi
  //   terre    chez soi, porte fermée, et l'on ne ressort pas tout de suite
  //   contre   le guet, qui va dans l'autre sens
  /** Rendre quelqu'un à sa journée écrite. */
  // Chaque enregistrement CONNAÎT SA PLACE (`p.i`), et le dernier la reprend
  // quand on retire au milieu. Sans ça, reprendre la place de quelqu'un
  // demandait de balayer les quatre mille — pour chacun des dix-huit mille
  // habitants dehors, à chaque image. La page s'est arrêtée net, et c'était
  // mérité : une éviction doit coûter un échange, pas une recherche.
  function oublier(i) {
    const p = S.paniques[i];
    if (!p) return;
    if (p.cel._peur) p.cel._peur[p.k] = null;
    const dernier = S.paniques.pop();
    if (i < S.paniques.length) { S.paniques[i] = dernier; dernier.i = i; }
  }

  // Ceux qui sont déjà rentrés : leur place est la première qu'on reprend.
  // La liste se refait à chaque pas, en même temps qu'on les parcourt de toute
  // façon — elle ne coûte donc rien de plus qu'un `push`.


  function bourgeois(dt) {
    S.abris.length = 0;
    // À l'envers, parce qu'on retire en cours de route.
    for (let i = S.paniques.length - 1; i >= 0; i--) {
      const p = S.paniques[i];
      if (p.etat === "terre") S.abris.push(p);
      const m = foyerProche(p.x, p.y);
      p.age_t += dt;

      if (p.etat === "saisi") {
        p.attente -= dt;
        if (p.attente <= 0) {
          p.etat = p.contre ? "contre"
                 : p.prend === "assaut" ? "arme"
                 : p.prend === "garde" ? "barre" : "fuite";
          p.age_t = 0;
          if (p.prend) armer(p);
        }
        continue;
      }

      // IL A PRIS QUELQUE CHOSE ET IL Y VA. Il ne s'arrête pas au bord comme le
      // guet : il entre dedans. On ne le fait pas SE BATTRE — il n'est pas un
      // corps de la bataille, et le sac n'attend pas de fil pour lui — mais il
      // a quitté sa journée écrite pour de bon, il est dans la rue avec un
      // outil qui coupe, et c'est tout ce qu'il faut pour qu'on le retrouve au
      // matin et qu'on lui demande où il était.
      if (p.etat === "arme") {
        if (m) marcher(p, dt, m.f.x, m.f.y, false);
        continue;
      }

      // IL BARRE SA PORTE. Il ne bouge plus, il ne fuit plus, et il est chez
      // lui — donc à une adresse. C'est le seul de cette couche qui redevienne
      // un habitant sans avoir cessé d'être un acteur : demain il dira ce
      // qu'il a vu passer devant son seuil, et il aura une raison de mentir.
      if (p.etat === "barre") continue;

      if (p.etat === "contre") {
        // Il s'avance jusqu'à voir, et il s'arrête là. Un homme du guet n'est
        // pas suicidaire : il regarde, et il ira le dire.
        if (!m) { p.etat = "rentre"; continue; }
        if (m.d > APPROCHE) marcher(p, dt, m.f.x, m.f.y, false);
        // Il est arrivé au bord et il a vu. C'est le seul fait de la couche de
        // peur qui produise un TÉMOIN au sens plein : un homme du guet, qui a
        // un nom dans la ville, et qui ira le raconter au poste.
        //
        // UNE FOIS PAR HOMME, et le verrou est sur l'enregistrement, pas dans
        // le jeu de clefs : il s'arrête au bord et il y reste, donc la
        // condition reste vraie vingt fois par seconde jusqu'à la fin du sac.
        // PAR QUARTIER, PAS PAR HOMME — et c'est la troisième fois qu'on
        // apprend la même chose dans ce fichier. Tout fait émis depuis une
        // couche qui tourne PAR PERSONNE (la peur, la rumeur, le guet) doit
        // être verrouillé PAR LIEU, sinon il sort au rythme de la population
        // et il enterre la guerre sous sa propre rumeur. Vingt-huit hommes du
        // guet disaient vingt-huit fois la même phrase depuis deux endroits.
        //
        // Ce qu'on veut savoir tient en une ligne par quartier : le guet a vu,
        // à telle heure, et voilà combien d'hommes en armes il a comptés.
        else if (!p.vu) {
          p.vu = true;
          noter("guet-a-vu", p.x, p.y,
                { clef: "guet:" + situer(p.x, p.y).zone,
                  dit: { hommes: m.f.n } });
        }
        continue;
      }

      if (p.etat === "fuite") {
        if (!m) { p.etat = "rentre"; p.age_t = 0; continue; }
        // ON NE RENTRE PAS TANT QU'ON ENTEND. Le seuil de retour est plus haut
        // que celui de départ : sans cette hystérésis, un habitant posé juste à
        // la limite bascule entre fuir et rentrer à chaque pas, et l'on voit
        // une rue de gens qui tremblent sur place.
        if (m.d > ALERTE * 1.5 && p.age_t > FUITE_MIN) { p.etat = "rentre"; p.age_t = 0; }
        else marcher(p, dt, m.f.x, m.f.y, true);
        continue;
      }

      if (p.etat === "rentre") {
        if (m && m.d < ALERTE) { p.etat = "fuite"; p.age_t = 0; p.venu = null; continue; }
        const d = Math.hypot(p.chez[0] - p.x, p.chez[1] - p.y);
        // Le dernier bout se fait en ligne droite : le carrefour n'est pas la
        // porte, et l'on finit toujours par traverser sa rue.
        if (d < 12) { p.x = p.chez[0]; p.y = p.chez[1];
                      p.etat = "terre"; p.attente = CALME; continue; }
        if (p.age_t > RENTRE_MAX || !marcher(p, dt, p.chez[0], p.chez[1], false)) {
          // On a renoncé : la marche gloutonne peut tourner dans un quartier
          // sans jamais retomber sur sa rue. Alors on se terre où l'on est,
          // dans le premier renfoncement — ce qui vaut mieux qu'un habitant qui
          // fait des ronds jusqu'à la fin de la partie.
          p.etat = "terre"; p.attente = CALME;
        }
        continue;
      }

      // terre
      p.attente -= dt;
      if (p.attente <= 0 && (!m || m.d > ALERTE * 1.5)) oublier(i);
    }
  }

  // La rumeur court plus vite que la colonne : on ne panique pas seulement de
  // ce qu'on voit, mais de ce qu'on voit COURIR. C'est ce qui vide une rue
  // avant que le premier soldat n'y soit entré, et il n'y a rien de plus vrai
  // dans tout ce module. Une grille de vingt mètres sur les seuls paniqués —
  // deux mille au plus, donc rien.

  function semerLaRumeur() {
    S.semis.clear();
    for (const p of S.paniques) {
      if (p.etat === "terre" || p.contre) continue;   // on court après ceux qui courent
      const c = Math.floor(p.x / RUMEUR) + ":" + Math.floor(p.y / RUMEUR);
      let l = S.semis.get(c);
      if (!l) S.semis.set(c, l = []);
      l.push(p);
    }
  }

  function rumeur(x, y) {
    let n = 0;
    const ci = Math.floor(x / RUMEUR), cj = Math.floor(y / RUMEUR);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
      const l = S.semis.get((ci + i) + ":" + (cj + j));
      if (!l) continue;
      for (const p of l)
        if ((p.x - x) ** 2 + (p.y - y) ** 2 < RUMEUR * RUMEUR && ++n >= RUMEUR_MIN)
          return true;
    }
    return false;
  }

  /**
   * LE VETO. `foule2d` appelle ceci pour chaque habitant qu'il va dessiner,
   * juste après avoir lu sa journée écrite. On rend vrai quand on a pris cet
   * habitant en charge — et alors c'est nous qui disons où il est.
   *
   * Il faut que ce soit BON MARCHÉ, parce que c'est appelé des dizaines de
   * milliers de fois par calcul : tant que la bataille dort, c'est un test.
   */
  function derange(cel, k, P) {
    // LE VETO NE TIENT PAS À L'HORLOGE, IL TIENT À LA BATAILLE. Il était gardé
    // par `marche` : suspendre l'assaut renvoyait d'un coup tous les fuyards à
    // la place que leur journée écrite leur donnait — c'est-à-dire qu'on les
    // voyait se téléporter à leur puits pendant qu'une armée leur passait
    // dessus. Une pause arrête le temps, elle n'efface pas la peur.
    // Trois tests avant toute chose, dans l'ordre du moins cher : pas de
    // bataille, pas de masse à fuir, et l'on rend la main sans avoir rien
    // alloué. C'est le chemin que prennent quatre cent mille personnes.
    if (!S.hommes.length || S.temps <= 0) return false;
    const p = cel._peur ? cel._peur[k] : null;
    if (p) {
      P.x = p.x; P.y = p.y;
      // CELUI QUI A BARRÉ SA PORTE EST CHEZ LUI, ET IL Y RESTE. Le confondre
      // avec un fuyard le remettrait en mouvement dans la rue, alors que tout
      // son propos est de ne plus en bouger.
      P.quoi = (p.etat === "terre" || p.etat === "saisi" || p.etat === "barre")
               ? "sur-place" : "route";
      // Chacun garde sa couleur : on doit voir l'or du guet remonter la rue que
      // tout le monde descend, et le fer de ceux qui viennent de la prendre y
      // remonter avec lui — pour l'autre camp.
      P.vers = p.contre ? "ronde"
             : p.prend === "assaut" ? "armes"
             : p.prend === "garde" ? "barre" : "fuite";
      return true;
    }
    // On ne prend en charge que ceux qui sont DEHORS. Celui qui est chez lui y
    // reste : il a fermé sa porte, ce qui est exactement ce qu'on ferait.
    if (P.quoi === "chez") return false;
    if (!S.foyers.length) return false;
    const m = foyerProche(P.x, P.y);
    const vu = m && m.d < ALERTE;
    if (!vu && !rumeur(P.x, P.y)) return false;

    // LE PLAFOND N'EST PAS PREMIER ARRIVÉ, PREMIER SERVI. Il l'était, et l'on
    // atteignait les quatre mille places en six minutes — tenues pour l'essentiel
    // par des gens qui avaient paniqué par ouï-dire à huit cents mètres de là.
    // Résultat : un homme sur le point d'être piétiné se voyait refuser la
    // peur, parce qu'un autre s'était affolé le premier à l'autre bout de la
    // ville. Celui qui VOIT passe donc devant, en prenant la place de quelqu'un
    // qui est déjà rentré chez lui — la lui reprendre ne coûte rien : il est
    // sous son toit, et sa journée écrite l'y met aussi.
    if (S.paniques.length >= PANIQUE_MAX) {
      if (!vu) return false;
      let libre = false;
      while (S.abris.length && !libre) {
        const a = S.abris.pop();
        if (a.etat === "terre" && S.paniques[a.i] === a) { oublier(a.i); libre = true; }
      }
      if (!libre) return false;
    }

    // CHACUN SA PEUR, ET ELLE NE SE TIRE PAS AU SORT. Le déphasage vient de
    // l'identité du corps, comme ses heures de sortie : deux voisins ne partent
    // pas à la même seconde et ne courent pas à la même allure, et pourtant
    // rien n'est stocké. Un enfant et un vieillard courent moins vite qu'un
    // portefaix — c'est l'âge qui est dans la cellule qui le dit, pas un dé.
    const id = S.J.ident(cel, k);
    const h1 = ((id * 374761393) >>> 13 & 1023) / 1023;
    const h2 = ((id * 668265263) >>> 11 & 1023) / 1023;
    const an = cel.age_sexe ? (cel.age_sexe[k] & 0x7f) : 30;
    const role = (cel.roles_index && cel.role) ? cel.roles_index[cel.role[k]] : "";
    const contre = CONTRE.test(role || "");
    const vieux = an < 12 || an > 55;
    // TROISIÈME TIRAGE, ET C'EST CELUI DU CAMP. Il vient de l'identité comme
    // les deux autres, donc le même homme fera toujours le même choix — ce qui
    // est le minimum qu'on doive à quelqu'un qu'on peut aller retrouver le
    // lendemain et faire parler de sa nuit.
    const h3 = ((id * 2246822519) >>> 9 & 1023) / 1023;
    const jeune = an >= 16 && an <= 45;
    // On ne rejoint pas une rumeur : il faut avoir vu la masse de ses yeux.
    let prend = null;
    if (!contre && jeune && vu) {
      if (AVEC.test(role || "") && h3 < PART_ARMES) prend = "assaut";
      else if (CONTRE_EUX.test(role || "") && h3 < PART_BARRE) prend = "garde";
    }
    if (!cel._peur) cel._peur = new Array(cel.n).fill(null);
    const rec = {
      cel, k,
      x: P.x, y: P.y,
      chez: [cel.x0 + cel.x[k] / 100, cel.y0 + cel.y[k] / 100],
      etat: "saisi",
      // Celui qui va chercher une arme ne traîne pas non plus : il a décidé
      // avant d'avoir eu peur, et c'est précisément ce qui le distingue.
      attente: (contre || prend) ? 0.2 + h1 * 0.8
                                 : SAISI[0] + h1 * (SAISI[1] - SAISI[0]),
      v: contre ? MARCHE * 1.4
         : prend === "assaut" ? MARCHE * 1.3
         : (vieux ? 2.3 : FUITE) * (0.85 + h2 * 0.3),
      contre, prend, age_t: 0,
      // CE QUI FAIT D'UN PANIQUÉ UN TÉMOIN. Trois champs qu'on avait déjà
      // calculés et qu'on jetait : son identité, son âge, son métier. Avec
      // `chez` — qui est une ADRESSE — ça suffit à faire de lui quelqu'un que
      // la troupe peut aller trouver trois jours plus tard et faire parler.
      // C'est toute la différence entre une simulation et un gisement.
      id, an, role,
      // Le sexe est le bit 7 de l'octet d'âge, et il sert à une seule chose
      // ici : écrire « une épouse » au lieu de « un épouse ». Deviner le genre
      // d'après le nom du métier serait faux une fois sur trois, alors que la
      // cellule le sait pour de bon.
      femme: !!(cel.age_sexe && (cel.age_sexe[k] & 0x80)),
      noeud: noeudProche(P.x, P.y), arc: null, venu: null, s: 0, surRue: false,
    };
    rec.i = S.paniques.length;
    cel._peur[k] = rec;
    S.paniques.push(rec);
    // LA PEUR SE NOTE PAR QUARTIER, ET UNE SEULE FOIS PAR QUARTIER. Quatre
    // mille paniqués feraient quatre mille lignes que personne ne lira ; ce
    // qu'on veut savoir est plus simple — à quelle heure tel quartier a
    // compris, et s'il l'a vu ou entendu dire.
    //
    // C'ÉTAIT UNE MAILLE DE CENT VINGT MÈTRES, et c'était trop fin : quatre-
    // vingt-dix lignes sur cent quatre-vingt-douze, dont quatorze à la même
    // seconde et toutes rigoureusement identiques. Un document qui s'ouvre sur
    // quatorze fois la même phrase, on ne le lit pas — et la guerre, qui est le
    // sujet, se retrouvait noyée par sa propre rumeur. Douze quartiers : douze
    // lignes au plus, et chacune dit quelque chose.
    noter(vu ? "peur-gagne" : "rumeur-gagne", P.x, P.y, {
      clef: "peur:" + situer(P.x, P.y).zone,
      dit: { par: vu ? "on les a vus" : "on l'a entendu dire" },
    });
    // ET ON REGARDE CHEZ QUI ELLE VIENT D'ARRIVER. Douze lignes de quartiers
    // disent que la ville a compris ; elles ne disent pas ce que ça fait à
    // quelqu'un. Les huit qui ont une adresse ont chacun une conduite écrite
    // d'avance — Wex ne bouge pas, Nonne remonte vers le bruit, Jenn ouvre le
    // septuaire — et c'est ce qui se joue le lendemain, pas le nom du quartier.
    //
    // Huit lignes au plus dans toute la nuit, une par personne : bornées par
    // construction, comme tout ce qui sort d'une couche qui tourne par tête.
    laMaisonDaCote(P.x, P.y);
    P.vers = contre ? "ronde" : "fuite";
    P.quoi = "sur-place";      // le premier instant, on ne bouge pas
    return true;
  }

  // ---- la boucle ------------------------------------------------------------
  // PAS FIXE, et pas le temps de l'image. Une machine à états qu'on avance
  // d'un `dt` variable ne se rejoue pas deux fois pareil, et l'on passe la
  // soirée à chercher pourquoi la même bataille finit autrement. Vingt pas par
  // seconde, et l'on rattrape ce qu'il faut — sans jamais rattraper plus de
  // quatre pas d'un coup, sinon un onglet laissé en fond simule dix minutes en
  // une image et fige la page.
  // ---- LE SILLAGE -----------------------------------------------------------
  // SUR UNE IMAGE FIXE, RIEN NE DIT QUI BOUGE — et une capture d'écran est une
  // image fixe, comme une bataille en pause, comme le regard qu'on pose une
  // seconde sur le plan avant de revenir au fil. Un homme en marche, un homme
  // qui tient sa position et un homme en déroute sont trois points identiques.
  //
  // On garde donc DEUX positions passées par homme, et le dessin en tire un
  // trait qui s'efface. Ce n'est pas un effet : c'est la seule chose qui rende
  // lisibles, d'un coup d'œil, l'axe d'une colonne, le reflux d'une aile qui
  // rompt, et le fait qu'une masse arrêtée est arrêtée.
  //
  // ÉCHANTILLONNÉ, PAS ACCUMULÉ. À un vingtième de seconde, deux pas de recul
  // font dix centimètres — un trait plus court que l'homme, donc invisible.
  //
  // LE RELEVÉ SE CALE SUR L'ALLURE, ET ELLE EST ÉCRITE PLUS HAUT. Un tiers de
  // seconde paraissait raisonnable ; à 1,3 m/s cela fait quarante-quatre
  // centimètres, c'est-à-dire moins qu'un homme, et le banc l'a dit tout de
  // suite — zéro sillage sur une armée entière en marche. On relève donc toutes
  // les huit dixièmes : un marcheur laisse un mètre par segment et deux mètres
  // de mémoire, un fuyard près de trois. C'est visible dès qu'on voit l'homme.
  const SILLAGE_S = 0.8;


  function sillage() {
    if (S.temps - S.sillageDu < SILLAGE_S) return;
    S.sillageDu = S.temps;
    for (const h of S.hommes) {
      if (h.etat === "mort" || h.etat === "blesse") continue;
      h.sx2 = h.sx1; h.sy2 = h.sy1;
      h.sx1 = h.x; h.sy1 = h.y;
    }
  }

  // ---- LA MASSE QUI BOUGE --------------------------------------------------
  // Le pas d'un homme est un événement comme un autre — mais il y en a dix-sept
  // cents, et deux pas par seconde chacun feraient trois mille cinq cents
  // objets à fabriquer, trier et jeter par seconde pour que TOUS finissent en
  // nappe. On paierait l'élection au prix fort pour un résultat connu d'avance.
  //
  // On agrège donc au sol : une grille de quarante mètres, un appel par case
  // occupée. Vingt appels au lieu de trois mille cinq cents, et la nappe reçoit
  // exactement la même chose — avec sa distance, donc avec sa direction. C'est
  // ce qui fait qu'une fuite S'ENTEND VENIR : le grondement change de case
  // avant que la ligne ne bouge à l'écran.
  //
  // Quatre fois par seconde suffit : la nappe a huit secondes de descente.
  const MAILLE_SON = 40;

  function rumeur() {
    if (!window.Son || S.temps - S.rumeurDu < 0.25) return;
    S.rumeurDu = S.temps;
    const cases = new Map();
    for (const h of S.hommes) {
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "tient") continue;
      const i = Math.round(h.x / MAILLE_SON), j = Math.round(h.y / MAILLE_SON);
      const c = i + "," + j;
      const v = cases.get(c);
      if (v) { v.n++; v.x += h.x; v.y += h.y; }
      else cases.set(c, { n: 1, x: h.x, y: h.y });
    }
    // DEUX VERSEMENTS, PAS UN — et le second est celui qui fait la foule. Les
    // pieds nourrissent le grave ; les GORGES nourrissent le medium, et c'est
    // de là que sort le grain de murmure. Sans cette ligne, la bande des voix
    // ne recevait que les cris non élus — c'est-à-dire presque rien —, et une
    // mêlée de dix-sept cents hommes n'avait pas une seule gorge dedans.
    // La moitié : à tout instant, tout le monde ne crie pas.
    for (const v of cases.values()) {
      const x = v.x / v.n, y = v.y / v.n;
      Son.fond("pas", v.n, x, y);
      Son.fond("houle", v.n / 2, x, y);
    }
  }

  function avancer(dtReel) {
    S.reste += Math.min(dtReel, 0.5);
    let n = 0;
    while (S.reste >= PAS && n++ < 4) {
      S.reste -= PAS;
      S.temps += PAS;
      rumeur();
      // ---- OÙ IL ÉTAIT AU DÉBUT DU PAS ---------------------------------------
      // LA SIMULATION BAT À 20 HZ, L'ÉCRAN À 60 : sans ce relevé, une position
      // tenait trois images puis sautait, et le saut n'était même pas régulier —
      // `dt` de `requestAnimationFrame` ne tombe jamais juste, si bien que
      // l'accumulateur consomme zéro pas sur une image, un sur la suivante,
      // parfois deux. C'est ce battement inégal qu'on voit comme un tremblement,
      // et il est d'autant plus visible qu'on approche : à trente pixels le
      // mètre, un marcheur fait des bonds de deux pixels toutes les cinquante
      // millisecondes.
      //
      // On garde donc la position d'AVANT, et `peindre` dessine entre les deux
      // au prorata de ce qui reste dans l'accumulateur. Le modèle ne change pas
      // d'un iota — c'est le rendu qui cesse de montrer les paliers d'un calcul
      // qui n'a jamais prétendu battre à la vitesse de l'écran.
      for (const h of S.hommes) { h.px = h.x; h.py = h.y; }
      semer();
      // OÙ SONT LES AILES, une fois pour toutes. Un ordre qui désigne
      // quelqu'un a besoin de son centre, et vingt-cinq cents hommes qui le
      // recalculeraient chacun pour soi feraient de « suivre » le comportement
      // le plus cher du fichier. C'est le premier geste du pas, avant même que
      // les têtes décident : elles aussi regardent où en sont leurs ailes.
      centres();
      // Une chaîne cassée se répare avant que l'ordre suivant ne descende. Le
      // délai a été payé dans `successions`; une fois le nouveau chef élu, il
      // peut voir la bannière et recevoir au même battement que les autres.
      successions();
      // LE COMMANDEMENT AVANT LES CORPS, et dans cet ordre-là : la tête décide,
      // les bannières montent ou tombent, les ordres descendent — et seulement
      // ensuite les hommes exécutent ce qu'ils ont reçu. L'inverse ferait agir
      // tout le monde sur l'ordre du pas précédent, ce qui ajouterait un
      // vingtième de seconde de retard partout, invisible et faux.
      deciderLesTetes(PAS);
      bannieres(PAS);
      transmettre(PAS);
      // ET CE QUE PERSONNE N'A ORDONNÉ. Après la transmission, jamais avant :
      // un chef ne s'invente un ordre que lorsqu'on a fini de constater que
      // rien ne lui est parvenu.
      initiative(PAS);
      menerChefsAuRassemblement(PAS);
      observerCommandants();
      coordonnerRatissages();
      designerLeFront();
      // LE CONSEIL AVANT LES HACHES, et d'un vingtième de seconde seulement :
      // une porte qu'on ouvre de l'intérieur ne doit pas recevoir le coup du
      // même pas, sinon elle s'annoncerait enfoncée et ouverte à la même
      // seconde, et les annales diraient les deux.
      leConseil();
      lesMessagers();
      porteQuiCede();
      fairePercevoirIncendies();
      for (const h of S.hommes) soldat(h, PAS);
      for (const h of S.hommes) if (h.etat !== "mort") pousser(h, PAS);
      // LE SOUFFLE APRÈS LE MOUVEMENT, parce que c'est `h.etat` qui dit le
      // régime et qu'il vient seulement d'être arrêté par `soldat`. Le mettre
      // avant ferait payer à chacun l'effort du pas PRÉCÉDENT.
      for (const h of S.hommes) if (h.etat !== "mort") souffler(h, PAS);
      // Les masses AVANT les habitants, et la rumeur après eux : ce qui court
      // à ce pas-ci est ce qui fera paniquer le voisin au pas suivant.
      escouadesQuiRompent();
      // APRÈS que tout le monde a bougé : la presse qu'on lui compte est celle
      // de ce pas-ci, pas celle du précédent.
      leRoiSurSaCharrette(PAS);
      fondreLesFoyers();
      bourgeois(PAS);
      semerLaRumeur();
      sillage();
    }
    majCompte();
  }

  function majCompte() {
    let a = 0, d = 0;
    for (const h of S.hommes) {
      if (h.tete) continue;         // il commande, il ne fait pas nombre
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      if (h.camp === "assaut") a++; else d++;
    }
    compte.a = a; compte.d = d;
  }

  // ---- ce qu'une escouade laisse quand elle cesse d'en être une -------------
  // Une escouade ne « meurt » pas : elle se vide, et à un moment elle n'est
  // plus une unité. La moitié suffit — au-delà, les survivants n'exécutent
  // plus rien de ce qu'on leur avait dit. C'est le fait qui manque le plus au
  // récit d'une bataille, parce qu'il est le seul à parler d'un GROUPE.
  function escouadesQuiRompent() {
    if (!S.escouades.length) return;
    const vif = new Array(S.escouades.length).fill(0);
    const tot = new Array(S.escouades.length).fill(0);
    const cx = new Array(S.escouades.length).fill(0);
    const cy = new Array(S.escouades.length).fill(0);
    for (const h of S.hommes) {
      // La tête est du camp de l'assaut et porte une escouade nulle par
      // défaut : sans ce test, elle gonflerait à jamais l'effectif de la
      // première, qui ne romprait donc plus jamais.
      if (h.camp !== "assaut" || h.tete || h.hors) continue;
      const e = h.escouade;
      tot[e]++;
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      vif[e]++; cx[e] += h.x; cy[e] += h.y;
    }
    for (let e = 0; e < S.escouades.length; e++) {
      if (!tot[e] || vif[e] > tot[e] / 2) continue;
      // Le lieu du fait est celui des SURVIVANTS, pas celui des morts : c'est
      // là qu'il y a encore quelqu'un à voir.
      const x = vif[e] ? cx[e] / vif[e] : S.verrou.x, y = vif[e] ? cy[e] / vif[e] : S.verrou.y;
      noter("escouade-rompt", x, y,
            { clef: "rompt:" + e, dit: { escouade: e, restent: vif[e], sur: tot[e] } });
    }
  }

  // ---- le dessin ------------------------------------------------------------
  function repere() {
    const vue = S.vueDe && S.vueDe();
    if (!vue || !S.toile || !S.toile.width) return null;
    return CarteProjection.repere(vue, S.toile.width, S.toile.height);
  }

  function ajuster() {
    if (!S.toile || !S.hote) return;
    const r = S.hote.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const l = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (S.toile.width !== l || S.toile.height !== h) { S.toile.width = l; S.toile.height = h; }
  }

  // Éclaircir ou assombrir une teinte de la table, sans lui faire changer de
  // ton : on tire vers le blanc ou vers le noir, jamais vers une autre couleur.
  // `t` va de −1 (le quart plus sombre) à +1 (le quart plus clair).
  //
  // Les vingt-six teintes possibles sont mises en cache : la fonction est
  // appelée une fois par homme et par image — deux mille cinq cents fois
  // vingt par seconde — et refaire trois `parseInt` à chaque appel se paie.
  const _teintes = new Map();
  function eclaircir(hex, t) {
    const q = Math.round(t * 8);                 // dix-sept marches suffisent
    if (!q) return hex;
    const clef = hex + q;
    let v = _teintes.get(clef);
    if (v) return v;
    const rgb = lire(hex);                       // hex OU rgb(…) — voir `lire`
    const f = q / 8 * .25;                       // au plus un quart
    const c = (i) => {
      const x = rgb[i];
      return Math.max(0, Math.min(255, Math.round(f > 0 ? x + (255 - x) * f
                                                        : x * (1 + f))));
    };
    v = "rgb(" + c(0) + "," + c(1) + "," + c(2) + ")";
    _teintes.set(clef, v);
    return v;
  }

  const TEINTE = {
    assaut: "#8c2f22",        // le fer qui monte
    garde:  "#24506b",        // le fer qui tient
    mort:   "#5a5348",
    // PLUS DE COULEUR ABSOLUE POUR LA DÉROUTE NON PLUS — même raison que le
    // repli, et elle est plus grave ici : l'ocre repeignait cinq cents hommes
    // dans une teinte qui n'est celle d'aucun camp, au moment précis où l'on a
    // le plus besoin de savoir QUI s'en va. Un plan où la moitié des points
    // vire au brun ne dit plus rien de la bataille — il dit seulement qu'il se
    // passe quelque chose. Voir `DELAVES`.
    blesse: "#8a4a52",
    // Le coureur porte l'ordre : il doit se voir traverser la presse, sinon
    // toute la chaîne de commandement reste une abstraction de fichier.
    coureur:"#d8c37a",
    // PLUS DE COULEUR ABSOLUE POUR LE REPLI — voir `couleurDe`. Elle valait
    // quand `repli` ne désignait qu'une aile qu'on fait décrocher, c'est-à-dire
    // trois fois par nuit et du seul côté de l'assaut. Depuis que c'est aussi
    // la fuite individuelle, ce gris-bleu repeignait des assaillants dans la
    // teinte de la garde : on voyait des rouges devenir bleu clair en tournant
    // les talons, ce qui est exactement le contraire de ce qu'on veut lire.
    commande:"#c9a227",
    // La chute fraîche, le temps qu'elle se fonde dans le sol. Elle n'est pas
    // rouge vif : c'est du sang sur de la terre, pas une croix sur une carte.
    chute:  "#6d3129",
  };
  // ---- DE QUELLE COULEUR EST UN HOMME ---------------------------------------
  // LE CAMP D'ABORD, TOUJOURS. C'est la seule chose qu'on doit pouvoir lire sans
  // réfléchir sur un plan qui porte deux mille cinq cents points : de quel côté
  // est celui-là. Un état qui repeint un homme dans la teinte de l'autre camp
  // ne l'informe pas, il le trompe.
  //
  // Deux régimes, donc. Les états qui ont une couleur PROPRE — la mort, la
  // chute, le blessé, la déroute, le coureur — la gardent : ce sont des faits
  // qui priment sur l'appartenance, et l'on veut justement les repérer d'un
  // coup d'œil sans suivre les camps. Le repli, lui, n'est pas de ceux-là : un
  // homme qui recule est encore de son camp, et c'est même la première chose
  // qu'on veut savoir de lui. On le délave donc au lieu de le repeindre —
  // même teinte, tirée vers le gris, ce qui se lit comme un homme qui se
  // retire sans jamais le faire changer de bord.
  // DEUX CRANS SUR LE MÊME AXE, ET L'ORDRE COMPTE. Le repli est un homme qui
  // décroche en gardant sa place dans un rang ; la déroute est un homme qui
  // n'en a plus. Le second est donc plus délavé que le premier — mais aucun des
  // deux ne quitte la teinte de son camp, parce qu'un fuyard qu'on ne peut pas
  // attribuer est un fuyard qu'on ne peut pas compter.
  const DELAVES = { repli: .2, deroute: .38 };
  function couleurDe(h) {
    const k = DELAVES[h.etat];
    if (k !== undefined) return delaver(TEINTE[h.camp], k);
    return TEINTE[h.etat] || TEINTE[h.camp];
  }

  // Tirer une teinte vers le gris de son propre niveau : on perd la saturation,
  // on garde la clarté — donc la couleur reste reconnaissable et le point
  // s'éteint. `k` va de 0 (intacte) à 1 (gris pur).
  // ---- LIRE UNE COULEUR, QUELLE QUE SOIT SA FORME ---------------------------
  // ELLES ÉTAIENT DEUX À S'ÉCRIRE ET UNE SEULE À SE LIRE, et ça a mis les
  // fuyards en noir. `delaver` rend du `rgb(…)` ; `eclaircir` faisait
  // `parseInt(couleur.slice(1), 16)`, ce qui vaut `parseInt("gb(115,57,49)")`,
  // c'est-à-dire NaN — et `(NaN >> 16) & 255` vaut zéro sur les trois canaux.
  // Tout homme délavé (le repli, la déroute) et pourvu d'assez de trempe pour
  // que l'éclaircissement s'arme sortait donc en `rgb(0,0,0)`. Ceux dont la
  // trempe était sous un seizième y échappaient par le court-circuit `if (!q)`,
  // d'où un défaut qui avait l'air capricieux et ne l'était pas.
  //
  // On lit donc les deux formes au même endroit, une fois pour toutes. Tant que
  // la seule entrée était l'hexadécimal du tableau, `slice(1)` suffisait ; dès
  // que deux fonctions se sont enchaînées, il fallait ceci.
  function lire(c) {
    if (c[0] === "#") {
      const n = parseInt(c.slice(1), 16);
      return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }
    const m = c.match(/-?\d+/g);
    return m ? [+m[0], +m[1], +m[2]] : [0, 0, 0];
  }

  const _delaves = new Map();
  function delaver(hex, k) {
    const clef = hex + k;
    let v = _delaves.get(clef);
    if (v) return v;
    const [r, g, b] = lire(hex);
    const gris = Math.round(r * .299 + g * .587 + b * .114);
    const m = (x) => Math.round(x + (gris - x) * k);
    v = "rgb(" + m(r) + "," + m(g) + "," + m(b) + ")";
    _delaves.set(clef, v);
    return v;
  }

  // Deux minutes de bataille pour qu'un corps passe de la chute au sol. C'est
  // long à dessein — plus court, on verrait les morts s'effacer, et un mort ne
  // s'efface pas ; il cesse seulement d'être la nouvelle du moment.
  const SEDIMENT = 120;

  // Rempli à chaque image, lu par les étiquettes des têtes. C'est le seul
  // chiffre du plan qui change vingt fois par seconde, et il ne coûte rien :
  // la boucle qui le calcule est celle qui dessine.
  const debout = new Map();
  // Ce qu'il valait à l'image d'avant, et l'heure du dernier changement. Un
  // compte qui passe de vingt à dix-sept sans un frémissement, ce sont trois
  // morts qu'on n'a pas sentis — et c'est le seul chiffre du plan qu'on
  // regarde en continu.
  const deboutAvant = new Map();
  const deboutQuand = new Map();
  const SURSAUT = 1.1;          // secondes de bataille pendant lesquelles il brûle

  // ---- CE QU'ON DÉSIGNE DU DOIGT -------------------------------------------
  // Le survol rend déjà une fiche ; il ne montrait pas ce dont l'homme FAIT
  // PARTIE. Or c'est là tout le sujet du fichier : vingt hommes qui pensent
  // ensemble, cinq escouades qu'un seul ordre commande, une bannière qu'on
  // suit des yeux. `carte-ville` nous dit ce qu'il désigne, on allume la
  // maisonnée — et le lien vers la bannière, qui est la chose qu'on ne peut
  // pas déduire d'un point rouge.

  function souligner(sel) { S.surligne = sel || null; }

  function peindre() {
    // `toile` ET `ctx` : le nettoyage de « pas de bataille ici » retire la
    // toile et la met à `null` SANS toucher au contexte, qui reste donc un
    // objet valide pointant sur un canvas détaché. La garde ne testait que
    // `ctx` : le premier recadrage venu — un cran de molette suffit, puisque
    // `carte-ville` appelle `recadrer()` à chaque `cadrer()` — jetait alors une
    // TypeError sur `toile.width`. `ajuster()`, juste au-dessus, teste bien
    // `toile` : c'est ici qu'il manquait.
    if (!S.ctx || !S.toile || !S.toile.width) return;
    S.ctx.clearRect(0, 0, S.toile.width, S.toile.height);
    const rep = repere();
    if (!rep || !S.hommes.length) return;
    const dpr = window.devicePixelRatio || 1;
    // ---- LA POSITION D'ÉCRAN, ENTRE DEUX PAS DE CALCUL -----------------------
    // Ce qu'on dessine n'est plus `h.x` mais un point pris entre où il était au
    // début du pas et où il est à la fin, au prorata de ce qui dort dans
    // l'accumulateur. C'est le seul endroit du fichier où l'on mente sur une
    // position — et le mensonge porte sur un vingtième de seconde au plus,
    // toujours à l'intérieur du segment que l'homme vient réellement de
    // parcourir.
    //
    // ON NE LISSE PAS UN SAUT. Un homme qui prend le rail d'une rue, un coureur
    // qu'on lance, un blessé qu'on repose : leur position est ASSIGNÉE et non
    // intégrée, et tendre un trait par-dessus les ferait glisser sur cent mètres
    // de toits. Au-delà de ce qu'un homme peut couvrir en un pas, on ne lisse
    // plus rien — on saute, exactement là où le modèle a sauté.
    const a = Math.max(0, Math.min(1, S.reste / PAS));
    const BOND = 4;                  // mètres : au-delà, ce n'est plus un pas
    for (const h of S.hommes) {
      if (h.px === undefined) { h.ex = h.x; h.ey = h.y; continue; }
      const jx = h.x - h.px, jy = h.y - h.py;
      if (jx * jx + jy * jy > BOND * BOND) { h.ex = h.x; h.ey = h.y; continue; }
      h.ex = h.px + jx * a; h.ey = h.py + jy * a;
    }
    // Le calque appartient au commandant sélectionné, pas à la scène. Il se
    // peint sous les corps afin que croyances et flèches restent un document
    // semi-transparent posé sur le terrain, sans cacher les hommes réels.
    peindreCarteCommandant(rep, dpr);
    // À 1:1, un homme fait un demi-mètre : au cadrage de la ville entière il
    // vaut un huitième de pixel. On ne triche pas sur sa POSITION — seulement
    // sur sa taille à l'écran, faute de quoi une armée de trois cents hommes
    // est rigoureusement invisible, ce qui est fidèle et inutile.
    // UN HOMME FAIT UN DEMI-MÈTRE DE LARGE, DONC UN QUART DE RAYON. On posait
    // `EPAULE` comme rayon là où c'est une LARGEUR : chaque homme était dessiné
    // deux fois trop gros, et deux hommes côte à côte se recouvraient de moitié
    // — d'où une mêlée qui paraissait plus dense qu'elle n'est, et des lignes
    // qu'on ne pouvait pas compter à l'œil.
    //
    // LE PLAFOND SAUTE. Il figeait la taille à quatre pixels dès qu'on
    // approchait : à 0,17 m le pixel — le cadrage où l'on regarde vraiment se
    // battre — un homme aurait dû faire un pixel et demi et en faisait quatre.
    // Le PLANCHER reste : au cadrage de la ville entière un homme vaut un
    // huitième de pixel, et une armée rigoureusement invisible est fidèle et
    // inutile. On ne triche donc plus que là où l'on ne peut pas faire
    // autrement, et jamais dans l'autre sens.
    const r = Math.max(1.5 * dpr, rep.k * (EPAULE / 2));
    const L = S.toile.width + 8, H = S.toile.height + 8;

    // Les verrous d'abord, sous les corps : ce sont les objectifs, ils doivent
    // se lire même quand sept hommes sont dessus. Il y en a un par porte, et
    // les voir tourner à des vitesses différentes est précisément ce qu'on
    // vient regarder.
    for (const v of S.verrous) {
      const x = rep.ox + v.x * rep.k, y = rep.oy + v.y * rep.ky;
      const part = v.pv / v.max;
      const R1 = Math.max(7, rep.k * 4);
      // ELLE BAT QUAND ON LA TRAVAILLE, et c'est tout le sujet de l'heure
      // creuse : une porte que sept hommes cognent et une porte que personne ne
      // touche depuis vingt minutes descendaient toutes deux en silence, du
      // même arc lisse. Le battement est la seule chose qui donne à voir que
      // le front n'est pas plein — trois coups par minute au lieu de sept.
      const depuis = S.temps - (v.coup || -99);
      const frais = v.etat !== "ouvert" && depuis < 1.2;
      if (frais) {
        // Une onde brève, qui part du battant. Son opacité suit le nombre de
        // bras : un seul homme fait un frémissement, sept font un choc.
        const t = depuis / 1.2;
        S.ctx.globalAlpha = (1 - t) * Math.min(.5, .12 + (v.frappeurs || 1) * .06);
        S.ctx.strokeStyle = "#d9663f";
        S.ctx.lineWidth = Math.max(1.5, 2 * dpr);
        S.ctx.beginPath();
        S.ctx.arc(x, y, R1 + t * R1 * .9, 0, 6.2832);
        S.ctx.stroke();
        S.ctx.globalAlpha = 1;
      }
      S.ctx.strokeStyle = v.etat === "ouvert" ? "#7a8b5a" : "#b03a24";
      S.ctx.lineWidth = Math.max(2, 3 * dpr) * (frais ? 1.35 : 1);
      S.ctx.beginPath();
      S.ctx.arc(x, y, R1, -Math.PI / 2,
              -Math.PI / 2 + 6.2832 * Math.max(0, part));
      S.ctx.stroke();
    }

    // ---- LES SILLAGES, SOUS TOUT LE MONDE ---------------------------------
    // Ils passent avant les corps pour la même raison que les verrous : ce sont
    // des traces au sol, pas des objets. Un sillage par-dessus les hommes
    // ferait une résille de fils sur la mêlée.
    //
    // ON NE TRACE QUE CE QUI A VRAIMENT BOUGÉ. Un homme qui tient sa position
    // frémit de quelques centimètres à chaque pas (il joue des coudes) : sans
    // ce seuil, deux mille hommes arrêtés porteraient chacun un petit trait, et
    // « rien ne bouge » ressemblerait exactement à « tout bouge ».
    // ON JUGE SUR L'INTERVALLE RÉVOLU, JAMAIS SUR CELUI QUI COURT — et c'est
    // une correction de structure, pas de réglage. Le relevé tombe à la fin du
    // pas de simulation : à l'instant qui suit, `sx1` VAUT `x` pour tout le
    // monde, et une décision prise sur `x → sx1` répondait donc « personne ne
    // bouge » une image sur seize. Toute l'armée clignotait au rythme du
    // relevé. `sx1 → sx2` est un intervalle complet, toujours : il ne dépend
    // pas du moment où l'on regarde.
    //
    // Le seuil se lit contre l'allure de MARCHE, écrite en tête de fichier : un
    // marcheur couvre 1,04 m entre deux relevés, un homme qui tient sa position
    // ne fait que jouer des coudes. La moitié d'un pas de marche sépare
    // proprement les deux.
    const SEUIL_SILLAGE = 0.5;
    // ET UN PLAFOND, QUI EST LA MOITIÉ MANQUANTE DU SEUIL. Deux endroits
    // assignent une position au lieu de l'intégrer — l'homme qui prend le rail
    // d'une rue, le coureur qu'on lance sur sa trace : il saute alors de là où
    // il se tenait jusqu'à l'axe de la voie. Le corps, lui, saute proprement
    // (l'interpolation le laisse passer, voir plus haut) ; le SILLAGE, non — il
    // tirait un trait de cinquante mètres en travers des toits, et c'est le
    // trait qu'on voyait, pas le point, puisqu'il est cent fois plus long.
    // Le plus rapide du plan fait 3,6 m/s et le relevé tombe toutes les 0,8 s :
    // au-delà de cinq mètres, aucun homme n'a marché — il a été déplacé.
    const BOND_SILLAGE = 5;
    S.ctx.lineCap = "round";
    for (const h of S.hommes) {
      if (h.sx2 === undefined || h.etat === "mort" || h.etat === "blesse") continue;
      const dx = h.sx1 - h.sx2, dy = h.sy1 - h.sy2;
      const d2 = dx * dx + dy * dy;
      if (d2 < SEUIL_SILLAGE * SEUIL_SILLAGE) continue;
      if (d2 > BOND_SILLAGE * BOND_SILLAGE) continue;
      // La queue de tête compte aussi : c'est elle qui part du corps, donc c'est
      // elle qui trahit le saut le plus visiblement.
      const qx = h.ex - h.sx1, qy = h.ey - h.sy1;
      if (qx * qx + qy * qy > BOND_SILLAGE * BOND_SILLAGE) continue;
      const x = rep.ox + h.ex * rep.k, y = rep.oy + h.ey * rep.ky;
      if (x < -20 || y < -20 || x > L + 12 || y > H + 12) continue;
      // La déroute se lit dans sa propre couleur : c'est le seul mouvement du
      // plan qu'on veut reconnaître SANS avoir à suivre le sens du trait.
      // Le sillage suit la même règle que le corps, sinon la traînée reste
      // bleue derrière un homme redevenu rouge — et c'est le trait qu'on voit
      // en premier, puisqu'il est plus long que le point.
      S.ctx.strokeStyle = couleurDe(h);
      S.ctx.globalAlpha = .30;
      S.ctx.lineWidth = Math.max(1, r * .7);
      S.ctx.beginPath();
      S.ctx.moveTo(x, y);
      S.ctx.lineTo(rep.ox + h.sx1 * rep.k, rep.oy + h.sy1 * rep.ky);
      S.ctx.stroke();
      // La seconde queue, deux fois plus pâle : elle ne se voit pas seule, elle
      // ne sert qu'à courber le trait — et une courbe dit d'où l'on vient là où
      // un segment ne dit qu'une direction.
      if (h.sx2 !== undefined) {
        S.ctx.globalAlpha = .14;
        S.ctx.beginPath();
        S.ctx.moveTo(rep.ox + h.sx1 * rep.k, rep.oy + h.sy1 * rep.ky);
        S.ctx.lineTo(rep.ox + h.sx2 * rep.k, rep.oy + h.sy2 * rep.ky);
        S.ctx.stroke();
      }
    }
    S.ctx.globalAlpha = 1;

    // COMBIEN IL EN RESTE DEBOUT, PAR CORPS. Une tête sans ce chiffre n'est
    // qu'un nom posé sur le plan ; avec lui, on voit fondre les deux mille de
    // les faux gueux pendant que les neuf cents de Cranche ne bougent pas. Le compte se
    // fait dans la boucle qu'on parcourt déjà, avant le rognage à l'écran —
    // sinon un corps sorti du cadre paraîtrait mort.
    debout.clear();
    for (const h of S.hommes) {
      if (h.corps && h.etat !== "mort" && h.etat !== "blesse")
        debout.set(h.corps, (debout.get(h.corps) || 0) + 1);
      const x = rep.ox + h.ex * rep.k, y = rep.oy + h.ey * rep.ky;
      if (x < -8 || y < -8 || x > L || y > H) continue;
      if (h.etat === "mort") {
        // IL SE FOND DANS LE SOL, EN DEUX MINUTES. Le mort était un carré gris
        // à opacité fixe, pour toujours : au bout d'une heure de bataille le
        // plan se couvrait de confettis tous identiques, et l'on ne savait plus
        // lire ni où l'on venait de se battre, ni où l'on s'était battu au
        // début. Une chute fraîche est donc sombre et nette, puis elle passe à
        // la teinte du sol sans jamais disparaître tout à fait — un mort reste
        // un corps qu'on retrouvera au matin.
        const age = Math.min(1, (S.temps - (h.tombe || 0)) / SEDIMENT);
        S.ctx.globalAlpha = .78 - age * .42;
        S.ctx.fillStyle = age < .18 ? TEINTE.chute : TEINTE.mort;
        const c = r * (.86 - age * .18);
        S.ctx.fillRect(x - c, y - c, c * 2, c * 2);
        S.ctx.globalAlpha = 1;
        continue;
      }
      // Le blessé se lit comme un mort — couché, à plat — mais il garde sa
      // couleur de sang : sur le plan, on doit voir d'un coup d'œil combien
      // sont par terre et combien de ceux-là respirent encore.
      if (h.etat === "blesse") {
        S.ctx.globalAlpha = .8; S.ctx.fillStyle = TEINTE.blesse;
        S.ctx.fillRect(x - r, y - r * .55, r * 2, r * 1.1);
        S.ctx.globalAlpha = 1;
        continue;
      }
      // CE QU'ON DÉSIGNE S'ALLUME, LE RESTE S'EFFACE — et l'inverse serait pire
      // que rien : entourer les vingt hommes d'une escouade au milieu de deux
      // mille points de la même couleur ne les fait pas ressortir, ça ajoute du
      // bruit. C'est la BAISSE du reste qui les fait apparaître.
      const tenu = !S.surligne || (S.surligne.formation !== null &&
                                 h.formation === S.surligne.formation);
      S.ctx.globalAlpha = S.surligne ? (tenu ? 1 : .22) : 1;
      // À LA VILLE ENTIÈRE, LA MASSE SATURE. Sous le plancher de taille, deux
      // mille carrés de un pixel et demi à pleine encre se recouvrent et font
      // une tache uniforme : on perd le détail (c'est inévitable) ET la forme
      // (c'est réparable). En baissant l'encre à mesure qu'on s'éloigne, ce qui
      // se recouvre s'additionne — et la densité redevient lisible, c'est-à-dire
      // qu'on voit où sont les hommes au lieu de voir qu'il y en a.
      if (rep.k * EPAULE < 1.5 * dpr)
        S.ctx.globalAlpha *= Math.max(.34, rep.k * EPAULE / (1.5 * dpr));
      // La monture doit se lire avant même le survol. Ce n'est pas une icône :
      // l'ovale donne aussi son orientation et l'encombrement supplémentaire.
      if (h.montureCombat && r > 1.2) {
        S.ctx.save(); S.ctx.translate(x, y); S.ctx.rotate(-Math.atan2(h.fy || 0, h.fx || 1));
        S.ctx.strokeStyle = "#d1b06b"; S.ctx.lineWidth = Math.max(1, dpr);
        S.ctx.globalAlpha *= .8;
        S.ctx.beginPath(); S.ctx.ellipse(0, 0, r * 1.75, r * 1.15, 0, 0, 6.2832); S.ctx.stroke();
        S.ctx.restore();
      }
      // LA TREMPE SE VOIT, et c'est ce qui rend la variation lisible au lieu de
      // rester un chiffre dans un fichier. Une même teinte, éclaircie ou
      // assombrie du quart selon le cœur de l'homme : le camp reste
      // immédiatement reconnaissable — c'est la couleur qui le dit, pas la
      // clarté — mais une troupe cesse d'être une masse plate. Et à l'œil, un
      // paquet de points clairs qui tient là où le reste a lâché SE VOIT, sans
      // qu'on ait rien à mesurer.
      S.ctx.fillStyle = eclaircir(couleurDe(h), h.trempe || 0);
      if (r <= 2.4) S.ctx.fillRect(x - r, y - r, r * 2, r * 2);
      else { S.ctx.beginPath(); S.ctx.arc(x, y, r, 0, 6.2832); S.ctx.fill(); }
      S.ctx.globalAlpha = 1;
      // L'ordre ouvert se lit sur les mêmes corps et dans la même vue : un
      // fin anneau bleu, seulement pendant la manœuvre. Ce n'est ni une
      // seconde visualisation ni une particule par homme qui persiste.
      if (h.doctrineActive && r > 1.1) {
        S.ctx.strokeStyle = h.doctrinePhase === "ralliement" ? "#9ec8ca" : "#77b8c4";
        S.ctx.globalAlpha = .72; S.ctx.lineWidth = Math.max(.8, dpr);
        S.ctx.beginPath(); S.ctx.arc(x, y, r + 1.25 * dpr, 0, 6.2832); S.ctx.stroke();
        S.ctx.globalAlpha = 1;
      }
      // ---- LE FER, ET C'EST UNE LONGUEUR AVANT D'ÊTRE UNE COULEUR -----------
      // On dessine l'arme À SON ALLONGE VRAIE, en mètres, dans la direction où
      // l'homme regarde. C'est le seul rendu honnête : ce qu'on montre est
      // exactement ce que le modèle mesure, si bien qu'une rangée de lances se
      // lit comme une haie et qu'on VOIT pourquoi ceux d'en face doivent entrer
      // dedans. Un pictogramme d'arme, lui, aurait dit « lance » sans jamais
      // dire « trois mètres quarante ».
      //
      // ELLE DISPARAÎT AVEC LE ZOOM, et c'est réglé sur le mètre et non sur le
      // nombre d'hommes : sous trois pixels le mètre, une allonge fait quatre
      // pixels, tous les fers se ressemblent, et deux mille traits par-dessus
      // deux mille points ne font plus qu'un feutrage qui mange la densité —
      // c'est-à-dire la seule chose que la vue de loin sait dire.
      // ELLE SORT DU POING, PAS DU NOMBRIL. Le trait partait du centre exact du
      // corps : une rangée de lances faisait une haie de traits parfaitement
      // alignés sur les points, ce qu'aucune troupe n'a jamais eu l'air d'être.
      // On décale l'arme d'une demi-main sur le côté où il la tient — assez pour
      // que la haie respire, trop peu pour qu'on croie l'homme ailleurs qu'il
      // est. Un sur dix la porte à gauche (voir `gaucher` dans `homme`), et
      // c'est ce dixième qui fait qu'une ligne cesse de ressembler à un peigne.
      //
      // La perpendiculaire de `(fx, fy)` est `(−fy, fx)` : à l'écran, l'axe des
      // y descend, donc c'est bien la MAIN DROITE de qui regarde dans ce
      // sens-là. Le décalage porte sur les deux bouts du trait — l'arme glisse
      // de côté, elle ne pivote pas.
      if (rep.k >= 3 && h.arme && (h.fx || h.fy)) {
        const cote = h.gaucher ? -POING : POING;
        const dx = -h.fy * cote * rep.k, dy = h.fx * cote * rep.k;
        S.ctx.strokeStyle = h.arme.teinte;
        S.ctx.globalAlpha = h.etat === "melee" || h.etat === "assaut" ? .85 : .5;
        S.ctx.lineWidth = Math.max(1, (h.arme.degat[1] / 30) * dpr);
        S.ctx.beginPath();
        S.ctx.moveTo(x + dx, y + dy);
        S.ctx.lineTo(x + dx + h.fx * h.arme.allonge * rep.k,
                   y + dy + h.fy * h.arme.allonge * rep.k);
        S.ctx.stroke();
        S.ctx.globalAlpha = 1;
      }
      // TROIS GRADES, TROIS MARQUES, ET ELLES SE DISTINGUENT DE LOIN. Il n'y en
      // avait qu'une — le liseré du chef d'escouade —, si bien qu'un capitaine
      // qui porte la bannière d'une aile de cent hommes et un chef de vingt
      // avaient rigoureusement le même point à l'écran. Or ce sont eux qu'on
      // regarde tomber : perdre l'un coûte une escouade, perdre l'autre coûte
      // la morale de cinq.
      if (h.capitaine) {
        S.ctx.strokeStyle = "#f0dfa8"; S.ctx.lineWidth = Math.max(1.4, 1.8 * dpr);
        S.ctx.beginPath(); S.ctx.arc(x, y, r + 2.2 * dpr, 0, 6.2832); S.ctx.stroke();
      } else if (h.chef) {
        S.ctx.strokeStyle = "#e8d9a8"; S.ctx.lineWidth = Math.max(1, dpr);
        S.ctx.beginPath(); S.ctx.arc(x, y, r + 1.5 * dpr, 0, 6.2832); S.ctx.stroke();
      }
      // Le coureur traverse la presse avec un ordre dedans : il porte un halo,
      // parce qu'un point jaune de trois pixels dans deux mille points rouges
      // ne se suit pas des yeux, et que le suivre EST le spectacle.
      if (h.etat === "coureur") {
        S.ctx.globalAlpha = .55;
        S.ctx.strokeStyle = TEINTE.coureur; S.ctx.lineWidth = Math.max(1, dpr);
        S.ctx.beginPath(); S.ctx.arc(x, y, r + 4 * dpr, 0, 6.2832); S.ctx.stroke();
        S.ctx.globalAlpha = 1;
      }
    }

    // Entre le compte et les étiquettes qui le lisent : le sursaut se décide ici
    // parce qu'ici seulement `debout` est complet et pas encore servi.
    marquerLesPertes();
    peindreLeLien(rep, dpr);
    peindreLesBannieres(rep, dpr);
    peindreLesNommes(rep, dpr);
    peindreLesOrdres(rep, dpr);
  }

  function peindreFlecheCarte(rep, dpr, a, b, style) {
    if (!a || !b || !a.position || !b.position) return;
    const ax=rep.ox+a.position.x*rep.k, ay=rep.oy+a.position.y*rep.ky;
    const bx=rep.ox+b.position.x*rep.k, by=rep.oy+b.position.y*rep.ky;
    const dx=bx-ax, dy=by-ay, d=Math.hypot(dx,dy);
    if (d < 4) return;
    const ux=dx/d, uy=dy/d, pointe=Math.max(5*dpr, Math.min(11*dpr, d*.14));
    S.ctx.strokeStyle=style.couleur; S.ctx.fillStyle=style.couleur;
    S.ctx.globalAlpha=style.alpha; S.ctx.lineWidth=Math.max(1, style.largeur*dpr);
    S.ctx.setLineDash((style.tirets || []).map((x)=>x*dpr));
    S.ctx.beginPath(); S.ctx.moveTo(ax,ay); S.ctx.lineTo(bx,by); S.ctx.stroke();
    if (style.fleche) {
      S.ctx.setLineDash([]); S.ctx.beginPath(); S.ctx.moveTo(bx,by);
      S.ctx.lineTo(bx-ux*pointe-uy*pointe*.45, by-uy*pointe+ux*pointe*.45);
      S.ctx.lineTo(bx-ux*pointe+uy*pointe*.45, by-uy*pointe-ux*pointe*.45);
      S.ctx.closePath(); S.ctx.fill();
    }
  }

  function peindreCarteCommandant(rep, dpr) {
    if (S.carteCommandantId == null) return;
    const carte=carteCommandant(S.carteCommandantId);
    if (!carte) { S.carteCommandantId=null; return; }
    const champ=carte.champ, noeuds=new Map(carte.noeuds.map((n)=>[n.id,n]));
    const sx=(x)=>rep.ox+x*rep.k, sy=(y)=>rep.oy+y*rep.ky;
    S.ctx.save(); S.ctx.lineJoin="round"; S.ctx.lineCap="round";

    // Le polygone clair est ce que cet homme peut actuellement inspecter. Les
    // pointes sombres qui continuent un rayon arrêté montrent explicitement
    // qu'il existe du terrain derrière le masque, sans rien révéler de ce qui
    // s'y trouve.
    if (champ && champ.rayons.length) {
      S.ctx.fillStyle="rgba(91,151,178,.075)";
      S.ctx.strokeStyle="rgba(113,183,211,.30)"; S.ctx.lineWidth=Math.max(1,dpr);
      S.ctx.beginPath();
      champ.rayons.forEach((q,i)=>(i?S.ctx.lineTo(sx(q.x),sy(q.y)):S.ctx.moveTo(sx(q.x),sy(q.y))));
      S.ctx.closePath(); S.ctx.fill(); S.ctx.stroke();
      const ox=sx(champ.origine.x), oy=sy(champ.origine.y);
      for (const q of champ.rayons) if (q.bloque) {
        const ux=Math.cos(q.angle), uy=Math.sin(q.angle);
        S.ctx.strokeStyle="rgba(8,9,10,.38)"; S.ctx.lineWidth=Math.max(3,6*dpr);
        S.ctx.beginPath(); S.ctx.moveTo(sx(q.x),sy(q.y));
        S.ctx.lineTo(sx(champ.origine.x+ux*champ.rayon),
                   sy(champ.origine.y+uy*champ.rayon)); S.ctx.stroke();
      }
      S.ctx.fillStyle="rgba(113,183,211,.85)"; S.ctx.beginPath();
      S.ctx.arc(ox,oy,Math.max(3,3*dpr),0,6.2832); S.ctx.fill();
    }

    const styles={
      ordre:{couleur:"#e1b75f",alpha:.76,largeur:1.6,tirets:[],fleche:true},
      observe:{couleur:"#8fc8df",alpha:.48,largeur:1,tirets:[5,4],fleche:true},
      rapporte:{couleur:"#aaa18e",alpha:.42,largeur:1,tirets:[2,5],fleche:true},
      pression:{couleur:"#d85b45",alpha:.48,largeur:1.5,tirets:[7,4],fleche:true},
      conteste:{couleur:"#dd8e48",alpha:.42,largeur:1,tirets:[3,4],fleche:false},
      "occupe-axe":{couleur:"#e6a85e",alpha:.58,largeur:2,tirets:[2,3],fleche:false},
      communique:{couleur:"#7bc5cf",alpha:.55,largeur:1.2,tirets:[8,4],fleche:false},
    };
    for (const l of carte.liens) peindreFlecheCarte(rep,dpr,noeuds.get(l.de),
      noeuds.get(l.vers),styles[l.type]||styles.rapporte);

    for (const n of carte.noeuds) {
      if (n.id==="soi") continue;
      const x=sx(n.position.x), y=sy(n.position.y);
      if (n.id==="objectif") {
        const r=Math.max(5,5*dpr); S.ctx.fillStyle="rgba(225,183,95,.18)";
        S.ctx.strokeStyle="#e1b75f"; S.ctx.globalAlpha=.85; S.ctx.lineWidth=Math.max(1,1.4*dpr);
        S.ctx.beginPath(); S.ctx.moveTo(x,y-r); S.ctx.lineTo(x+r,y); S.ctx.lineTo(x,y+r);
        S.ctx.lineTo(x-r,y); S.ctx.closePath(); S.ctx.fill(); S.ctx.stroke();
        continue;
      }
      if (n.type==="commandant-allie") {
        S.ctx.strokeStyle="#7bc5cf"; S.ctx.globalAlpha=.72; S.ctx.lineWidth=Math.max(1,1.4*dpr);
        S.ctx.beginPath(); S.ctx.arc(x,y,Math.max(5,5*dpr),0,6.2832); S.ctx.stroke();
        continue;
      }
      const incertitude=Math.min(34,7+(1-(n.confiance||0))*20+(n.age||0)/45);
      S.ctx.fillStyle="rgba(207,77,54,.09)"; S.ctx.strokeStyle="rgba(226,105,77,.55)";
      S.ctx.globalAlpha=.9; S.ctx.lineWidth=Math.max(1,dpr); S.ctx.setLineDash([4*dpr,3*dpr]);
      S.ctx.beginPath(); S.ctx.arc(x,y,Math.max(6,incertitude*rep.k),0,6.2832); S.ctx.fill(); S.ctx.stroke();
      S.ctx.setLineDash([]); S.ctx.fillStyle="#dc664e";
      const r=Math.max(5,5*dpr); S.ctx.beginPath(); S.ctx.moveTo(x,y-r);
      S.ctx.lineTo(x+r*.9,y+r*.75); S.ctx.lineTo(x-r*.9,y+r*.75); S.ctx.closePath(); S.ctx.fill();
      // Deux marques purement descriptives : fer long et silhouette montée.
      // Elles ne changent aucune relation du graphe et n'impliquent donc
      // encore aucune manœuvre.
      if (n.signatures && n.signatures.longuesHampes) {
        S.ctx.strokeStyle="#f1d09a"; S.ctx.lineWidth=Math.max(1,dpr); S.ctx.beginPath();
        S.ctx.moveTo(x-r*1.5,y+r*1.2); S.ctx.lineTo(x+r*1.5,y-r*1.2); S.ctx.stroke();
      }
      if (n.signatures && n.signatures.montes) {
        S.ctx.strokeStyle="#e2bd6d"; S.ctx.beginPath();
        S.ctx.arc(x,y+r*1.45,r*.75,Math.PI,0); S.ctx.stroke();
      }
      if (rep.k>=1.4) {
        const force=n.force ? n.force.min+"–"+n.force.max : "?";
        S.ctx.font=Math.max(10,10*dpr)+"px Georgia,serif"; S.ctx.fillStyle="#f0dfbd";
        S.ctx.globalAlpha=.88; S.ctx.fillText(force+" · "+Math.round((n.confiance||0)*100)+" %",
          x+r+4*dpr,y-3*dpr);
      }
    }

    // Une légende compacte rend la sélection vérifiable jusque dans une
    // capture Mark. Elle ne suit pas la carte et ne peut donc être confondue
    // avec un ordre ou une position du monde.
    const marge=10*dpr, w=Math.min(S.toile.width-marge*2,360*dpr), h=58*dpr;
    S.ctx.setLineDash([]); S.ctx.globalAlpha=.90; S.ctx.fillStyle="rgba(17,19,20,.82)";
    S.ctx.fillRect(marge,marge,w,h); S.ctx.strokeStyle="rgba(113,183,211,.65)";
    S.ctx.strokeRect(marge,marge,w,h);
    S.ctx.fillStyle="#e9ddc4"; S.ctx.font="700 "+Math.max(11,12*dpr)+"px Georgia,serif";
    S.ctx.fillText("Carte de "+carte.nom,marge+9*dpr,marge+18*dpr);
    S.ctx.fillStyle="#bdb39e"; S.ctx.font=Math.max(9,10*dpr)+"px Arial,sans-serif";
    const resume=carte.resume;
    S.ctx.fillText(resume.croyances+" croyance(s) · "+resume.rayonsBloques+"/"+
      resume.rayons+" directions masquées",marge+9*dpr,marge+35*dpr);
    const ordre=carte.ordre ? "Ordre : "+carte.ordre : "Aucun ordre reçu";
    S.ctx.fillText(ordre.length>58?ordre.slice(0,57)+"…":ordre,marge+9*dpr,marge+50*dpr);
    S.ctx.restore();
  }

  /** Quel corps vient de perdre quelqu'un, et à quelle heure. */
  function marquerLesPertes() {
    for (const [id, n] of debout) {
      const avant = deboutAvant.get(id);
      // On ne marque QUE la baisse. Un corps qui reprend un homme — un rallié,
      // un blessé qu'on relève — ne doit pas faire saigner son chiffre.
      if (avant !== undefined && n < avant) deboutQuand.set(id, S.temps);
      deboutAvant.set(id, n);
    }
  }

  // ---- LE LIEN VERS LA BANNIÈRE --------------------------------------------
  // « Voir sa bannière, c'est ce qui le fait tenir » — le modèle le dit depuis
  // toujours (`sousLaBanniere`), et c'était la seule chose du fichier qu'on ne
  // pouvait NI voir NI déduire : rien, dans un point rouge, ne dit sous quelle
  // hampe il se range. Un trait qui n'apparaît qu'au survol le montre sans
  // encombrer la carte le reste du temps.
  //
  // Il vaut aussi comme mesure : un homme à cinquante mètres de sa bannière est
  // un homme qui va rompre, et l'on voit la longueur du trait avant d'avoir lu
  // le moindre chiffre.
  function peindreLeLien(rep, dpr) {
    if (!S.surligne || !S.surligne.lien) return;
    const [ax, ay, bx, by] = S.surligne.lien;
    S.ctx.save();
    S.ctx.strokeStyle = "#f0dfa8";
    S.ctx.globalAlpha = .5;
    S.ctx.lineWidth = Math.max(1, 1.2 * dpr);
    S.ctx.setLineDash([4 * dpr, 4 * dpr]);
    S.ctx.beginPath();
    S.ctx.moveTo(rep.ox + ax * rep.k, rep.oy + ay * rep.ky);
    S.ctx.lineTo(rep.ox + bx * rep.k, rep.oy + by * rep.ky);
    S.ctx.stroke();
    S.ctx.restore();
  }

  // ---- LES BANNIÈRES --------------------------------------------------------
  // Le modèle en tient une par aile depuis toujours — elle tombe, elle coûte de
  // la morale, on la relève — et rien de tout cela ne se voyait. C'est le seul
  // objet du sac qui dise d'un coup d'œil OÙ EST UNE AILE et si elle tient
  // encore : cinq escouades sont une abstraction, une hampe est un endroit.
  function peindreLesBannieres(rep, dpr) {
    if (!S.ailes.length) return;
    const L = S.toile.width + 12, H = S.toile.height + 12;
    const h0 = Math.max(9 * dpr, rep.k * 3.2);      // la hampe, en pixels
    for (const a of S.ailes) {
      const b = a.banniere;
      if (!b) continue;
      const x = rep.ox + b.x * rep.k, y = rep.oy + b.y * rep.ky;
      if (x < -12 || y < -12 || x > L || y > H) continue;
      const debout_ = b.debout;
      S.ctx.globalAlpha = debout_ ? .95 : .38;
      S.ctx.strokeStyle = debout_ ? "#f0dfa8" : TEINTE.mort;
      S.ctx.lineWidth = Math.max(1.2, 1.4 * dpr);
      S.ctx.beginPath();
      // Debout : verticale. À terre : couchée, du côté où l'homme est tombé.
      if (debout_) { S.ctx.moveTo(x, y); S.ctx.lineTo(x, y - h0); }
      else { S.ctx.moveTo(x, y); S.ctx.lineTo(x + h0, y + h0 * .25); }
      S.ctx.stroke();
      const [px, py] = debout_ ? [x, y - h0] : [x + h0, y + h0 * .25];
      S.ctx.fillStyle = debout_ ? TEINTE.assaut : TEINTE.mort;
      S.ctx.beginPath();
      S.ctx.moveTo(px, py);
      S.ctx.lineTo(px + h0 * .55, py + h0 * .18);
      S.ctx.lineTo(px, py + h0 * .36);
      S.ctx.closePath();
      S.ctx.fill();
      S.ctx.globalAlpha = 1;
    }
  }

  // ---- L'ORDRE AU-DESSUS DE CELUI QUI LE PORTE -----------------------------
  // Un ordre appartient à la troupe, mais il a un corps : son chef. L'écrire
  // au-dessus de vingt hommes répéterait vingt fois la même information ;
  // l'écrire dans un panneau latéral ferait perdre l'endroit où il agit.
  //
  // De près, la bulle donne le verbe et la destination. De loin, où les mots
  // ne pourraient matériellement plus tenir, elle se réduit au verbe. Mais
  // une bulle est un ACTE DE PAROLE, jamais le panneau permanent de l'état de
  // l'unité : une fois la phrase finie, elle disparaît. L'ordre reste dans la
  // mémoire, les sondes et le dossier au survol.
  const ORDRE_TEXTE_A = .55;       // pixels par mètre
  const ORDRE_CHANGE = 6;          // secondes de sursaut après un ordre neuf

  function ordreEnTrainDEtreDit(u) {
    const ditA = u && u.ordre && u.ordre.ditA;
    return Number.isFinite(ditA) && S.temps >= ditA && S.temps - ditA < ORDRE_CHANGE;
  }

  /** La phrase réellement détenue par cette unité, jamais son état moteur. */
  function ordreLitteral(u) {
    if (u && u.ratissage && u.ratissage.ordreLocal)
      return u.ratissage.ordreLocal;
    if (u && u.ordre && (u.ordre.source === "ordre-rassemblement" ||
                         u.ordre.source === "ordre-ratissage"))
      return u.ordre.texte;
    const e = u && u.escouade != null ? S.escouades[u.escouade] : null;
    const o = e && e.ordre;
    // Les ordres d'assaut ont déjà leur grammaire, leurs clauses perdues et
    // leur histoire de transmission. C'est CETTE version arrivée à l'escouade
    // que la bulle doit citer, non celle encore tenue par l'aile.
    if (o) {
      if (o.verbe === "tenir") return "Tenez ici.";
      if (o.verbe === "repli") return "Décrochez en ordre.";
      if (o.verbe === "avancer" && u.ordre && u.ordre.destination)
        return "À " + u.ordre.destination.nom + ". Restez avec votre vintaine.";
      const s = dire(o);
      if (s) return s.charAt(0).toUpperCase() + s.slice(1) + ".";
    }
    return (u && u.ordre && u.ordre.texte) || "Tenez ce poste.";
  }

  function ordreFaitBouger(u) {
    if (u && u.ordre && u.ordre.source === "ordre-rassemblement")
      return u.cadre.ralliement && u.cadre.ralliement.phase !== "en-place";
    const e = u && u.escouade != null ? S.escouades[u.escouade] : null;
    return e && e.ordre ? e.ordre.verbe !== "tenir"
      : !!(u && u.ordre && u.ordre.mode === "marcher");
  }

  function cheminBulle(x, y, l, h, r, pointeX, pointeY) {
    const rr = Math.min(r, l / 2, h / 2);
    S.ctx.beginPath();
    S.ctx.moveTo(x + rr, y);
    S.ctx.lineTo(x + l - rr, y); S.ctx.quadraticCurveTo(x + l, y, x + l, y + rr);
    S.ctx.lineTo(x + l, y + h - rr); S.ctx.quadraticCurveTo(x + l, y + h, x + l - rr, y + h);
    S.ctx.lineTo(Math.min(x + l - rr, pointeX + 4), y + h);
    S.ctx.lineTo(pointeX, pointeY);
    S.ctx.lineTo(Math.max(x + rr, pointeX - 4), y + h);
    S.ctx.lineTo(x + rr, y + h); S.ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
    S.ctx.lineTo(x, y + rr); S.ctx.quadraticCurveTo(x, y, x + rr, y);
    S.ctx.closePath();
  }

  function peindreLesOrdres(rep, dpr) {
    if (!S.formations.length) return;
    const L = S.toile.width, H = S.toile.height;
    const texteEntier = rep.k >= ORDRE_TEXTE_A * dpr;
    const font = Math.round(9.5 * dpr);
    const pris = [];
    const libre = (a) => !pris.some((b) => a[0] < b[2] && a[2] > b[0] &&
                                           a[1] < b[3] && a[3] > b[1]);
    const raccourcir = (s, n) => {
      const t = String(s || "");
      return t.length <= n ? t : t.slice(0, n - 1) + "…";
    };
    const lignesDe = (s, n, max) => {
      const mots = String(s || "").split(/\s+/), lignes = [];
      let ligne = "";
      for (const mot of mots) {
        const essai = ligne ? ligne + " " + mot : mot;
        if (ligne && essai.length > n) { lignes.push(ligne); ligne = mot; }
        else ligne = essai;
      }
      if (ligne) lignes.push(ligne);
      if (lignes.length > max) {
        lignes.length = max;
        lignes[max - 1] = raccourcir(lignes[max - 1], n - 1) + "…";
      }
      return lignes;
    };
    const verbeCompact = (x, y, marche_, teinte) => {
      S.ctx.strokeStyle = teinte;
      S.ctx.fillStyle = teinte;
      S.ctx.lineWidth = Math.max(1.3, 1.5 * dpr);
      S.ctx.beginPath();
      if (marche_) {
        S.ctx.moveTo(x - 5 * dpr, y); S.ctx.lineTo(x + 4 * dpr, y);
        S.ctx.moveTo(x + 1 * dpr, y - 3 * dpr); S.ctx.lineTo(x + 5 * dpr, y);
        S.ctx.lineTo(x + 1 * dpr, y + 3 * dpr);
      } else {
        // Deux pieds posés : une tenue, pas seulement un tiret minuscule.
        S.ctx.moveTo(x - 5 * dpr, y - 2 * dpr); S.ctx.lineTo(x - 5 * dpr, y + 2 * dpr);
        S.ctx.lineTo(x + 5 * dpr, y + 2 * dpr); S.ctx.lineTo(x + 5 * dpr, y - 2 * dpr);
      }
      S.ctx.stroke();
    };
    const candidats = [];
    for (const u of S.formations) {
      const chef = guideDe(u);
      if (!chef || !u.ordre) continue;
      if (!ordreEnTrainDEtreDit(u)) continue;
      const x = rep.ox + chef.ex * rep.k, y = rep.oy + chef.ey * rep.ky;
      if (x < -30 || y < -30 || x > L + 30 || y > H + 30) continue;
      candidats.push({ u, chef, x, y });
    }
    // L'ordre le plus récent gagne la meilleure place quand les chefs se
    // touchent : c'est précisément celui que l'œil cherche à cet instant.
    candidats.sort((a, b) => b.u.ordre.ditA - a.u.ordre.ditA);

    S.ctx.save();
    S.ctx.textBaseline = "middle";
    S.ctx.textAlign = "center";
    S.ctx.font = "600 " + font + "px ui-sans-serif, system-ui, sans-serif";
    for (const p of candidats) {
      const o = p.u.ordre;
      const marche_ = ordreFaitBouger(p.u);
      const phrase = "« " + ordreLitteral(p.u) + " »";
      const recent = true;
      const teinte = p.u.camp === "garde" ? "#83c5e8" : "#e3a06f";

      // À l'échelle de la ville : le verbe seul, ancré au chef. Il ne prétend
      // pas faire tenir un nom de place dans quatre pixels.
      if (!texteEntier) {
        const lw = 18 * dpr, lh = 14 * dpr;
        cheminBulle(p.x - lw / 2, p.y - 24 * dpr, lw, lh, 4 * dpr,
                    p.x, p.y - 6 * dpr);
        S.ctx.globalAlpha = recent ? .96 : .84;
        S.ctx.fillStyle = "rgba(18,16,13,.92)";
        S.ctx.fill();
        S.ctx.globalAlpha = 1;
        S.ctx.strokeStyle = recent ? "#f1ca72" : teinte;
        S.ctx.lineWidth = Math.max(1, (recent ? 1.7 : 1.1) * dpr);
        S.ctx.stroke();
        verbeCompact(p.x, p.y - 17.5 * dpr, marche_, recent ? "#f1ca72" : teinte);
        continue;
      }

      const lignes = lignesDe(phrase, 29, 3);
      S.ctx.font = "600 " + font + "px ui-sans-serif, system-ui, sans-serif";
      const largeur = Math.max(...lignes.map((x) => S.ctx.measureText(x).width)) + 12 * dpr;
      const hauteur = (8 + lignes.length * 11) * dpr;
      const ecart = 12 * dpr;
      const essais = [0, -largeur * .55, largeur * .55, -largeur, largeur];
      let boite = null;
      for (let niveau = 0; niveau < 3 && !boite; niveau++) {
        for (const decalage of essais) {
          const bx = p.x - largeur / 2 + decalage;
          const by = p.y - ecart - hauteur - niveau * (hauteur + 3 * dpr);
          const b = [bx, by, bx + largeur, by + hauteur];
          if (bx >= 2 && bx + largeur <= L - 2 && by >= 2 && libre(b)) {
            boite = b; break;
          }
        }
      }
      // Dans une presse illisible, aucun chef ne perd complètement son ordre :
      // seule la phrase cède, et son verbe compact reste au-dessus de lui.
      if (!boite) {
        S.ctx.globalAlpha = recent ? 1 : .82;
        verbeCompact(p.x, p.y - 8 * dpr, marche_, recent ? "#f1ca72" : teinte);
        continue;
      }
      pris.push(boite);
      const bx = boite[0], by = boite[1], pointeX = Math.max(bx + 6 * dpr,
        Math.min(boite[2] - 6 * dpr, p.x));
      cheminBulle(bx, by, largeur, hauteur, 5 * dpr, pointeX, p.y - 2 * dpr);
      S.ctx.globalAlpha = recent ? .96 : .86;
      S.ctx.fillStyle = recent ? "rgba(73,55,24,.94)" : "rgba(18,16,13,.90)";
      S.ctx.fill();
      S.ctx.globalAlpha = 1;
      S.ctx.strokeStyle = recent ? "#f1ca72" : teinte;
      S.ctx.lineWidth = Math.max(1, (recent ? 1.7 : 1.1) * dpr);
      S.ctx.stroke();
      S.ctx.fillStyle = recent ? "#ffe6a0" : "#f1e5ce";
      S.ctx.font = "600 " + font + "px ui-sans-serif, system-ui, sans-serif";
      for (let i = 0; i < lignes.length; i++)
        S.ctx.fillText(lignes[i], bx + largeur / 2, by + (8 + i * 11) * dpr);
    }
    S.ctx.restore();
  }

  // ---- LES NOMMÉS -----------------------------------------------------------
  // Un anneau, et un nom quand on est assez près pour le lire. C'est la seule
  // entorse au principe « aucun corps n'a de traitement spécial », et elle est
  // d'AFFICHAGE et non de simulation : le nommé encaisse exactement ce que les
  // autres encaissent, il est seulement le seul qu'on retrouve à l'œil.
  //
  // L'anneau se lit à toutes les échelles ; le nom ne s'écrit qu'à partir du
  // moment où deux noms ne se marchent plus dessus. Sans ce seuil, la vue de
  // la ville entière devient un tas d'étiquettes empilées sur quatre-vingts
  // pixels, ce qui est moins lisible que rien.
  const NOM_LISIBLE = 0.34;     // pixels par mètre — en dessous, l'anneau seul
  const ANNEAU = {
    assaut: "#d98a5a", garde: "#6fb0d8", ville: "#cfc0a0",
  };
  const OR = "#e8c15a";         // le roi, et rien d'autre

  // QUATRE RANGS, ET ILS NE SE VALENT PAS. Le plan les traitait tous pareil :
  // un anneau, un nom, dans l'ordre du tableau. Résultat, sur la vue de la
  // ville, « Cateline la sage-femme » recouvrait Aegon, et l'on ne savait
  // pas lequel des deux arrêtait la nuit en tombant.
  //
  // Deux nombres par rang, et tout en découle : `poids` décide qui écrit son
  // nom en premier quand deux étiquettes se disputent la même place, `seuil`
  // à partir de quel cadrage on l'écrit. Le roi n'a pas de seuil — on doit
  // pouvoir le trouver depuis la ville entière.
  const RANGS = {
    roi:     { poids: 4, seuil: 0,     teinte: OR },
    tete:    { poids: 3, seuil: 0.06 },
    nomme:   { poids: 2, seuil: 0.20 },
    figure:  { poids: 1, seuil: NOM_LISIBLE },
  };

  function couronne(x, y, s) {
    S.ctx.beginPath();
    S.ctx.moveTo(x - s, y + s * .55);
    S.ctx.lineTo(x - s, y - s * .40);
    S.ctx.lineTo(x - s * .5, y + s * .10);
    S.ctx.lineTo(x, y - s * .65);
    S.ctx.lineTo(x + s * .5, y + s * .10);
    S.ctx.lineTo(x + s, y - s * .40);
    S.ctx.lineTo(x + s, y + s * .55);
    S.ctx.closePath();
  }

  function peindreLesNommes(rep, dpr) {
    const L = S.toile.width + 8, H = S.toile.height + 8;
    // LES ÉTIQUETTES NE SE MARCHENT PLUS DESSUS. On garde les rectangles déjà
    // écrits et l'on saute ceux qui les croisent — le rang décidant qui passe.
    // Un nom sauté n'est pas perdu : son anneau reste, et il suffit de serrer
    // le cadrage pour le lire.
    const pris = [];
    const libre = (a) => !pris.some((b) => a[0] < b[2] && a[2] > b[0] &&
                                           a[1] < b[3] && a[3] > b[1]);

    S.ctx.textBaseline = "middle";

    const trace = (p) => {
      const x = rep.ox + p.x * rep.k, y = rep.oy + p.y * rep.ky;
      if (x < -60 || y < -30 || x > L + 60 || y > H + 30) return;
      const g = RANGS[p.rang] || RANGS.figure;
      const roi = p.rang === "roi";
      const teinte = g.teinte || ANNEAU[p.camp] || ANNEAU.ville;
      const R0 = Math.max((roi ? 8.5 : 6.5) * dpr, rep.k * (roi ? 6.5 : 5));
      S.ctx.globalAlpha = p.tombe ? .45 : 1;
      S.ctx.strokeStyle = teinte;
      S.ctx.lineWidth = Math.max(1.4, (roi ? 2.2 : 1.6) * dpr);

      // La figure ne se bat pas : son anneau est POINTILLÉ. C'est la seule
      // distinction qui compte vraiment sur ce plan — entre ceux qui peuvent
      // mourir dans la minute et ceux qui regardent.
      if (p.rang === "figure") S.ctx.setLineDash([3 * dpr, 3 * dpr]);
      S.ctx.beginPath(); S.ctx.arc(x, y, R0, 0, 6.2832); S.ctx.stroke();
      S.ctx.setLineDash([]);

      // Un second anneau sur ceux qui décident : la tête d'un corps n'est pas
      // un habitant, et l'œil doit pouvoir trier sans lire.
      if (p.rang === "tete" || roi) {
        S.ctx.lineWidth = Math.max(1, 1.2 * dpr);
        S.ctx.beginPath(); S.ctx.arc(x, y, R0 + 3 * dpr, 0, 6.2832); S.ctx.stroke();
      }
      if (roi) {
        S.ctx.fillStyle = OR;
        couronne(x, y - R0 - 6 * dpr, Math.max(4 * dpr, R0 * .5));
        S.ctx.fill();
      }
      // Tombé : on barre l'anneau. Un nommé à terre reste sur le plan — c'est
      // une bouche à faire parler au matin — mais il ne commande plus rien, et
      // ça doit se voir sans lire son étiquette.
      if (p.tombe) {
        const d = R0 * .72;
        S.ctx.beginPath();
        S.ctx.moveTo(x - d, y - d); S.ctx.lineTo(x + d, y + d);
        S.ctx.stroke();
      }

      if (rep.k <= g.seuil) { S.ctx.globalAlpha = 1; return; }

      // Deux lignes : le nom, et ce qu'il EST. Le second mot est ce qui manquait
      // — « Ser Merryn Coutre » ne dit pas qu'il tient le Donjon, et
      // « les faux gueux » ne dit pas qu'il a deux mille hommes derrière lui.
      const compteVif = p.rang === "tete" && debout.has(p.corps);
      const sous = compteVif ? debout.get(p.corps) + " debout" : (p.role || null);
      // IL SURSAUTE QUAND IL TOMBE. C'est le seul chiffre du plan qu'on regarde
      // en continu, et il passait de vingt à dix-sept sans un frémissement —
      // trois morts qu'on n'a pas sentis. Il brûle une seconde, puis se range.
      const saigne = compteVif &&
                     S.temps - (deboutQuand.get(p.corps) || -99) < SURSAUT;
      const F1 = Math.round((roi ? 12.5 : 11) * dpr);
      const F2 = Math.round(9 * dpr);
      S.ctx.font = (roi ? "600 " : "") + F1 + "px ui-sans-serif, system-ui, sans-serif";
      const l1 = S.ctx.measureText(p.nom).width;
      S.ctx.font = F2 + "px ui-sans-serif, system-ui, sans-serif";
      const l2 = sous ? S.ctx.measureText(sous).width : 0;
      const l = Math.max(l1, l2);
      const hb = sous ? 26 * dpr : 16 * dpr;
      const lb = l + 8 * dpr;
      // QUATRE PLACES, PAS UNE. Le nom s'écrivait toujours à droite : quatre
      // personnes enfermées dans trente mètres de cour — le châtelain, la
      // doyenne, celui qui veut ouvrir, le septon — se disputaient la même
      // bande, et deux d'entre eux n'avaient plus de nom à AUCUN cadrage. On
      // essaie donc à droite, à gauche, dessous, dessus, dans cet ordre.
      const d0 = R0 + 4 * dpr;
      const places = [
        [x + d0,      y - hb / 2],
        [x - d0 - lb, y - hb / 2],
        [x - lb / 2,  y + d0],
        [x - lb / 2,  y - d0 - hb],
      ];
      let boite = null;
      for (const [px2, py2] of places) {
        const b = [px2, py2, px2 + lb, py2 + hb];
        if (libre(b)) { boite = b; break; }
      }
      if (!boite) { S.ctx.globalAlpha = 1; return; }
      pris.push(boite);
      const bx = boite[0], ty = boite[1] + hb / 2;
      // UN FILET DE RAPPEL DÈS QUE L'ÉTIQUETTE A DÛ SE DÉPLACER. Les quatre
      // places ont réglé le chevauchement, elles ont créé l'autre moitié du
      // problème : un nom posé sous son homme, ou à sa gauche, n'appartient
      // plus visiblement à personne — et dans la cour du Donjon, où quatre
      // noms se partagent trente mètres, on ne sait plus lequel est lequel.
      // Le filet ne se dessine QUE dans ce cas : à droite, la place par
      // défaut, il n'apprendrait rien et salirait la carte.
      if (boite !== places[0] && bx !== places[0][0]) {
        S.ctx.save();
        S.ctx.strokeStyle = teinte;
        S.ctx.globalAlpha = (p.tombe ? .25 : .45);
        S.ctx.lineWidth = Math.max(1, dpr);
        S.ctx.beginPath();
        S.ctx.moveTo(x, y);
        // Vers le coin de la boîte qui regarde l'homme, jamais vers son milieu :
        // un trait qui entre dans l'étiquette la barre.
        S.ctx.lineTo(bx < x ? boite[2] : bx,
                   Math.max(boite[1], Math.min(boite[3], y)));
        S.ctx.stroke();
        S.ctx.restore();
      }

      S.ctx.globalAlpha = p.tombe ? .4 : .82;
      S.ctx.fillStyle = "rgba(18,16,13,.72)";
      S.ctx.fillRect(boite[0], boite[1], lb, hb);
      S.ctx.globalAlpha = p.tombe ? .55 : 1;
      S.ctx.fillStyle = teinte;
      S.ctx.font = (roi ? "600 " : "") + F1 + "px ui-sans-serif, system-ui, sans-serif";
      S.ctx.fillText(p.nom, bx + 4 * dpr, sous ? ty - 5 * dpr : ty);
      if (sous) {
        S.ctx.globalAlpha = saigne ? 1 : (p.tombe ? .4 : .7);
        if (saigne) S.ctx.fillStyle = "#d9663f";
        S.ctx.font = (saigne ? "600 " : "") + F2 +
                   "px ui-sans-serif, system-ui, sans-serif";
        S.ctx.fillText(sous, bx + 4 * dpr, ty + 7 * dpr);
      }
      S.ctx.globalAlpha = 1;
    };

    // On rassemble avant de peindre, et l'on trie par rang : c'est ce tri qui
    // fait que le roi écrit son nom avant une lavandière, et non l'ordre dans
    // lequel `dresser` les a poussés dans le tableau.
    const marques = [];
    for (const h of S.hommes) {
      if (!h.nom) continue;
      marques.push({ x: h.ex, y: h.ey, nom: h.nom, camp: h.camp, corps: h.corps,
                     role: h.role,
                     rang: h.roi ? "roi" : h.tete ? "tete" : "nomme",
                     tombe: h.etat === "mort" || h.etat === "blesse" });
    }
    for (const f of S.figures)
      marques.push({ x: f.x, y: f.y, nom: f.nom, camp: f.camp, role: f.role,
                     rang: "figure", tombe: false });
    // Un tombé passe après un debout de même rang : la place va à qui commande
    // encore.
    marques.sort((a, b) => (RANGS[b.rang].poids - (b.tombe ? .5 : 0)) -
                           (RANGS[a.rang].poids - (a.tombe ? .5 : 0)));
    for (const m of marques) trace(m);
  }

  function image() {
    const t = performance.now();
    const dt = S.dernier ? (t - S.dernier) / 1000 : 0;
    S.dernier = t;
    if (S.marche) avancer(dt);
    peindre();
    montre();
    S.boucle = requestAnimationFrame(image);
  }

  // ---- la barre -------------------------------------------------------------

  function batirBarre() {
    S.barre = document.createElement("div");
    S.barre.className = "cv-bat-barre";
    S.barre.innerHTML =
      '<button class="cv-b-jouer" title="Lancer ou suspendre l\'assaut">▶</button>' +
      '<span class="cv-b-etat">—</span>' +
      '<button class="cv-b-rejouer" title="Remettre l\'armée devant la porte">↺</button>';
    S.lecture = S.barre.querySelector(".cv-b-etat");
    S.barre.querySelector(".cv-b-jouer").addEventListener("click", (e) => {
      e.stopPropagation(); basculer();
    });
    S.barre.querySelector(".cv-b-rejouer").addEventListener("click", (e) => {
      e.stopPropagation(); rejouer();
    });
    ["pointerdown", "wheel", "dblclick"].forEach((t) =>
      S.barre.addEventListener(t, (e) => e.stopPropagation()));
    S.hote.appendChild(S.barre);
  }

  function montre() {
    if (!S.lecture) return;
    if (!S.hommes.length) { S.lecture.textContent = "—"; return; }
    const mm = Math.floor(S.temps / 60), ss = Math.floor(S.temps % 60);
    // COMBIEN DE PORTES SONT TOMBÉES, plutôt que l'état d'une seule. C'est le
    // seul chiffre qui dise où en est un sac : une ville tient tant qu'il lui
    // reste un battant.
    const ouvertes = S.verrous.filter((v) => v.etat === "ouvert").length;
    const porte = S.verrous.length <= 1
      ? (S.verrou && S.verrou.etat === "ouvert" ? "porte enfoncée"
         : Math.round((S.verrou ? S.verrou.pv / S.verrou.max : 1) * 100) + " % de porte")
      : ouvertes + "/" + S.verrous.length + " portes";
    // CINQ MESURES DE NATURE DIFFÉRENTE, ET ELLES NE PÈSENT PAS PAREIL. Elles
    // s'écrivaient d'affilée, au même poids, séparées par des points médians :
    // le RAPPORT DE FORCE — le seul chiffre qui décide de la nuit — se lisait
    // comme le compte des éclopés. On garde l'ordre, on hiérarchise l'encre :
    // l'heure et la force portent, l'état des portes suit, les pertes
    // s'effacent. Rien n'est retiré ; c'est l'œil qui n'a plus à trier.
    const pertes = [compte.blesses ? compte.blesses + " à terre" : null,
                    compte.fuyards ? compte.fuyards + " en fuite" : null]
                   .filter(Boolean).join(" · ");
    S.lecture.innerHTML =
      '<b class="cv-b-h">' + mm + "′" + (ss < 10 ? "0" : "") + ss + "</b>" +
      '<span class="cv-b-force"><b>' + compte.a + "</b> contre <b>" +
        compte.d + "</b></span>" +
      '<span class="cv-b-porte">' + porte + "</span>" +
      (pertes ? '<span class="cv-b-pertes">' + pertes + "</span>" : "");
  }

  function basculer() {
    if (!S.hommes.length) rejouer();
    // OUVRIR L'OREILLE ICI, ET NULLE PART AILLEURS. Aucun navigateur ne laisse
    // une page faire du bruit sans qu'on l'ait touchée — il faut donc un geste,
    // et celui-ci est le bon : c'est le seul du jeu qui déclenche à coup sûr ce
    // qu'on veut entendre. Un bouton « son » à part serait une case à cocher de
    // plus, et un éveil au chargement de la page ne marcherait tout simplement
    // pas. On suspend en même temps qu'on suspend l'assaut : une bataille en
    // pause ne gronde pas.
    if (window.Son) { if (S.marche) Son.dormir(); else Son.eveiller(); }
    S.marche = !S.marche;
    S.dernier = performance.now();
    if (S.barre) {
      S.barre.querySelector(".cv-b-jouer").textContent = S.marche ? "⏸" : "▶";
      S.barre.classList.toggle("marche", S.marche);
    }
    if (window.Foule2d) Foule2d.salir();
  }

  function rejouer(nomPorte, n) {
    // Sans effectif, c'est l'ÉCHELLE qui commande, et non plus trois cents
    // hommes en dur : la seule question qu'on se pose désormais est « à quelle
    // fraction de l'armée regarde-t-on ? ».
    S.terrainEpreuve = null;
    dresser(nomPorte || "La porte de la Gadoue", n);
    // On rend d'abord tout le monde à sa journée : les tableaux de peur vivent
    // sur les cellules, qui, elles, survivent à la bataille.
    for (const p of S.paniques) if (p.cel._peur) p.cel._peur[p.k] = null;
    S.paniques.length = 0; S.abris.length = 0; S.semis.clear(); S.foyers = [];
    S.incendiesSignales.clear(); S.prochainePerceptionIncendie = -Infinity;
    S.enArmes = new Map();
    tisserReseau();
    compte.morts = 0; compte.blesses = 0; compte.fuyards = 0; compte.rallies = 0;
    compte.contreCharges = 0;
    // (Les annales sont remises à zéro par `dresser`, AVANT qu'il ne pose les
    // corps. Elles l'étaient ici, après lui — donc tout ce que la mise en place
    // écrivait était effacé dans la foulée. C'est resté invisible tant que
    // `dresser` n'écrivait rien ; le jour où il a annoncé les humeurs des six
    // corps, ces six lignes-là ne sont jamais arrivées jusqu'au fichier.)
    S.dernier = performance.now();
    if (window.Foule2d) Foule2d.salir();
  }

  // La ville peut être regardée sans qu'une bataille y soit implicitement
  // convoquée. Cet état est volontairement plus fort que « pause » : il ne
  // garde ni hommes, ni unités, ni ordre de bataille caché sous le canvas.
  function vider() {
    S.hommes=[]; S.prochainHommeDebug=0; S.terrainEpreuve=null;
    S.escouades=[]; S.formations=[]; S.routesFormation=new Map();
    S.deploiements=new Map(); S.carteCommandantId=null;
    S.ratissages=new Map(); S.prochainRatissage=0;
    S.ailes=[]; S.tetes=[]; S.figures=[]; S.messagers=[];
    S.verrous=[]; S.entree=null; S.objectif=null; S.verrou=null;
    S.roi=null; S.arret=null; S.anneauOuvert=false;
    S.conseil={ averti:0, tenir:0, ouvrir:0, tranche:false };
    S.annales=[]; S.dits.clear(); S.temps=0; S.reste=0; S.marche=false;
    S.paniques.length=0; S.abris.length=0; S.semis.clear(); S.foyers=[];
    S.incendiesSignales.clear(); S.prochainePerceptionIncendie=-Infinity;
    S.enArmes=new Map(); deboutAvant.clear(); deboutQuand.clear(); S.surligne=null;
    compte.a=0; compte.d=0; compte.morts=0; compte.blesses=0;
    compte.fuyards=0; compte.rallies=0; compte.contreCharges=0;
    if (S.ctx && S.toile) S.ctx.clearRect(0,0,S.toile.width,S.toile.height);
    if (window.Foule2d) Foule2d.salir();
    montre();
  }

  // ---- l'attelage -----------------------------------------------------------

  function poser(h, donneVue, opts) {
    if (S.rate) return Promise.resolve(false);
    S.hote = h; S.vueDe = donneVue;
    S.source = (opts && opts.source) || S.source;
    if (!S.toile) {
      S.toile = document.createElement("canvas");
      S.toile.className = "cv-bataille";
      S.ctx = S.toile.getContext("2d");
    }
    if (S.toile.parentNode !== S.hote) S.hote.appendChild(S.toile);
    if (!S.barre) batirBarre();
    else if (S.barre.parentNode !== S.hote) S.hote.appendChild(S.barre);
    ajuster();
    if (!S.pret) S.pret = amorcer();
    return S.pret;
  }

  // LES DONNÉES D'ABORD, L'ÉCRAN ENSUITE — et les deux se séparent, parce que
  // le four n'a pas d'écran. `preparer` ne touche pas au document : c'est par
  // là qu'entre `scripts/monde/sac.js`, qui fait tourner cette même bataille
  // sans navigateur pour la cuire. Le jour où les deux divergent, on a deux
  // simulations, et c'est la fin de la confiance qu'on peut leur accorder.
  //
  // Le chemin du module se prend dans une variable : au navigateur il est
  // absolu (`/modules/…`), sous Node c'est une URL de fichier. Une ligne, et
  // le module devient exécutable des deux côtés.
  async function preparer(ou) {
    if (ou) S.source = ou;
    S.J = await import(window.CHEMIN_JOURNEE || "/modules/monde/journee.js");
    const r = await fetch(S.source + "/plan2d");
    if (!r.ok) throw new Error("plan2d : " + r.status);
    S.plan = await r.json();
    if (!repereDuPlan("Le Donjon Rouge", "donjon")) throw new Error("pas de donjon ici");
    // La voirie n'est demandée QUE parce qu'on en aura besoin après la porte.
    // Un demi-mégaoctet qu'on ne paie pas si l'on n'ouvre jamais l'échelle.
    S.voirie = await S.J.voirie(S.source);
    await Promise.all([enterrer(S.source), chargerEau(S.source)]);
    tisserReseau();
    await chargerBati(S.source);
    return true;
  }

  // ---- LES RUES QUI N'EN SONT PLUS -----------------------------------------
  //
  // Le graphe et le plan ne sont pas cuits par le même passage, ni forcément
  // dans le bon ordre : `bati.json` peut être plus vieux que `rues.json`, et
  // alors des rues ont été tracées là où des maisons étaient déjà posées.
  // Mesuré sur Port-Réal : 1,4 % du réseau court sous le bâti, et trente-cinq
  // arêtes y sont enfouies aux trois quarts.
  //
  // Ce n'est pas beaucoup, et ça se voit ÉNORMÉMENT : il suffit d'une venelle
  // de quarante mètres à travers un pâté pour qu'une colonne entière la prenne
  // — c'est le plus court chemin, l'A* ne connaît que ça — et l'on regarde
  // trois cents hommes traverser six maisons en file indienne.
  //
  // ON NE COURT PAS APRÈS LES DATES DES FICHIERS. On mesure chaque arête
  // contre le masque du bâti, et l'on rend celles qui sont enterrées TRÈS
  // chères. L'A* les évitera tant qu'il existe autre chose, et les prendra
  // quand même s'il n'y a rien d'autre — ce qui est le bon comportement : une
  // impasse vaut mieux qu'un chemin qui n'existe pas.
  const ENTERRE = 0.55;       // au-delà de ça sous les toits, ce n'est plus une rue
  const PENITENCE = 25;       // ce qu'on la fait payer

  // LA CÔTE VISIBLE ET LA CÔTE FRANCHISSABLE ONT LA MÊME SOURCE. `plan.cote`
  // est la courbe cuite par marching squares depuis `terrain.eau`; ici on
  // interpole ces mêmes quatre sommets et on tranche au même seuil de 0,5.
  // Il n'y a donc pas une rive décorative et une autre rive mécanique.
  async function chargerEau(src) {
    S.sousEau = null;
    try {
      const r = await fetch(src + "/terrain");
      if (!r.ok) return;
      const t = await r.json();
      const eau = t.eau, nx = +t.nx, ny = +t.ny, res = +t.res_m;
      if (!Array.isArray(eau) || eau.length !== ny || nx < 2 || ny < 2 || !(res > 0)) return;
      const region = S.plan && S.plan.region;
      const bornes = region && region.bornes;
      const polygones = region && Array.isArray(region.eau_polygones)
        ? region.eau_polygones : [];
      const dansPolygone = (x, y, poly) => {
        let dedans = false;
        for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
          const a = poly[i], b = poly[j];
          if (((a[1] > y) !== (b[1] > y)) &&
              x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0])
            dedans = !dedans;
        }
        return dedans;
      };
      const eauRegionale = (x, y) => {
        if (!bornes || bornes.length < 4 || x < bornes[0] || y < bornes[1] ||
            x > bornes[2] || y > bornes[3]) return true;
        return polygones.some((p) => p.length > 2 && dansPolygone(x, y, p));
      };
      S.sousEau = (x, y) => {
        const fx = x / res, fy = y / res;
        // Le raster de dix mètres garde l'autorité dans le cœur urbain. Au
        // dehors, la couronne régionale prend le relais avec les polygones qui
        // ont aussi produit le remplissage SVG visible.
        if (fx < 0 || fy < 0 || fx > nx - 1 || fy > ny - 1)
          return eauRegionale(x, y);
        const i = Math.min(nx - 2, Math.floor(fx));
        const j = Math.min(ny - 2, Math.floor(fy));
        const tx = fx - i, ty = fy - j;
        const a = +eau[j][i], b = +eau[j][i + 1];
        const d = +eau[j + 1][i], c = +eau[j + 1][i + 1];
        const haut = a * (1 - tx) + b * tx;
        const bas = d * (1 - tx) + c * tx;
        return haut * (1 - ty) + bas * ty > .5;
      };
    } catch (e) { S.sousEau = null; }
  }

  async function enterrer(src) {
    if (!S.voirie || S.voirie._enterre) return;
    let masque = null;
    try {
      const m = S.plan && S.plan.masque;
      if (!m) return;
      const r = await fetch(src + "/masque");
      if (!r.ok) return;
      const bits = new Uint8Array(await r.arrayBuffer());
      masque = { bits, pas: m.pas, nx: m.nx, ny: m.ny };
    } catch (e) { return; }
    const dedans = (x, y) => {
      const i = (x / masque.pas) | 0, j = (y / masque.pas) | 0;
      if (i < 0 || j < 0 || i >= masque.nx || j >= masque.ny) return false;
      const k = j * masque.nx + i;
      return (masque.bits[k >> 3] >> (k & 7)) & 1;
    };
    // LE MASQUE NE SERT PLUS QU'AUX RUES, ET IL ÉTAIT LE SEUL À SAVOIR OÙ SONT
    // LES MURS. Il vivait en variable locale de cette fonction, le temps de
    // pénaliser les arêtes enterrées, puis il était jeté. Or 🔒 90350 — « aucun
    // homme ne sait s'il a une retraite » — se lève avec exactement cette
    // donnée : un point derrière soi est franchissable ou il ne l'est pas.
    // On le garde donc, et `sousToit` est désormais la seule réponse de la
    // maison à cette question-là. Tant qu'il n'a pas été chargé — pas de plan,
    // pas de `fetch`, four sans serveur —, `sousToit` reste nul et les appelants
    // doivent rendre « on ne sait pas », JAMAIS « c'est libre ».
    S.sousToit = dedans;
    let n = 0;
    for (const [, nd] of S.voirie.noeuds) {
      for (const l of nd.liens) {
        const a = l.arete;
        if (a._sous === undefined) {
          let d = 0, t = 0;
          for (let i = 1; i < a.trace.length; i++) {
            const p = a.trace[i - 1], q = a.trace[i];
            const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
            const N = Math.max(1, Math.ceil(L / 2));
            for (let s = 0; s < N; s++) {
              t++;
              if (dedans(p[0] + (q[0] - p[0]) * s / N,
                         p[1] + (q[1] - p[1]) * s / N)) d++;
            }
          }
          a._sous = t ? d / t : 0;
          if (a._sous > ENTERRE) n++;
        }
        if (a._sous > ENTERRE) l.cout *= PENITENCE;
      }
    }
    S.voirie._enterre = n;
  }

  // ---- LE BÂTI, POUR LE PILLER ---------------------------------------------
  //
  // Une armée qui traverse une ville sans s'y arrêter n'est pas un sac, c'est
  // un défilé. Ce qui fait le sac, c'est que chaque maison est un objectif —
  // cinquante-trois mille objectifs, et une escouade qui doit choisir entre
  // avancer et s'arrêter. Personne n'écrit ce choix : il tombe de la
  // discipline du corps, et c'est de là que sort tout le reste. Un corps
  // discipliné arrive au Donjon à moitié de ses forces ; un corps qui se
  // dissout n'y arrive jamais.
  //
  // ON NE GARDE QUE CE QU'IL FAUT. Le fichier du bâti fait cinq mégaoctets et
  // porte seize colonnes ; on en retient quatre — où est la porte, ce qu'on y
  // fait, combien d'étages, et où en est le pillage. Le reste ne sert pas à
  // enfoncer un huis.

  // Les feux du sac sont rares et persistants ; les incendies du moteur urbain
  // sont des agrégats rafraîchis avec un TTL court. Dans les deux cas, la
  // perception balaie les FOYERS, jamais cinquante-trois mille maisons.


  const PAS_PERCEPTION_INCENDIE = .45;
  const PORTEE_PERCEPTION_INCENDIE = 55;
  const PILLE_S    = [25, 70];   // ce que coûte une maison, du seuil au butin
  const PORTEE_MAISON = 26;      // on ne quitte pas sa colonne pour plus loin
  const FEU        = 0.06;       // et parfois on met le feu en sortant

  // Ce qu'on trouve derrière une porte, par métier. Ce ne sont pas des points :
  // c'est ce qu'un homme peut emporter sur lui, et c'est pour ça qu'une manse
  // vaut trente taudis et qu'un puits ne vaut rien.
  const BUTIN = {
    manse: 40, change: 60, guilde: 30, septuaire: 25, "septuaire-quartier": 12,
    echoppe: 10, taverne: 8, auberge: 9, brasserie: 6, boulangerie: 4,
    forge: 7, poterie: 3, teinturerie: 5, tannerie: 3, corderie: 3,
    entrepot: 14, grenier: 10, moulin: 5, marche: 6, "marche-quartier": 6,
    "bureau-port": 20, caserne: 8, bordel: 9, etuve: 6, ecurie: 5,
    maison: 3, cabane: 1, taudis: 1,
  };

  async function chargerBati(src) {
    if (S.bati && S.bati.source === src) return;
    const r = await fetch(src + "/bati");
    if (!r.ok) { S.bati = null; return; }
    const d = await r.json();
    const col = {}; d._colonnes.forEach((c, i) => (col[c] = i));
    const l = d.bati, n = l.length;
    const x = new Float32Array(n), y = new Float32Array(n);
    const cx = new Float32Array(n), cy = new Float32Array(n);
    const val = new Uint8Array(n), etat = new Uint8Array(n);
    const fouille = new Uint8Array(n), occupation = new Uint8Array(n);
    const usage = new Array(n);
    for (let i = 0; i < n; i++) {
      const b = l[i];
      // LA PORTE, PAS LE CENTRE. On force un huis, on ne se matérialise pas
      // au milieu du salon — et c'est la porte qui donne sur la rue, donc le
      // seul point de la maison qu'un homme en colonne puisse atteindre.
      x[i] = b[col.porte_x] != null ? b[col.porte_x] : b[col.x];
      y[i] = b[col.porte_y] != null ? b[col.porte_y] : b[col.y];
      // Le centre ne sert jamais à trouver l'entrée. Il sert seulement à
      // rendre visible un homme qui A franchi l'huis : auparavant intérieur
      // et seuil partageaient les mêmes coordonnées, si bien qu'une fouille
      // correcte dans l'état ressemblait encore à un bouchon sur la carte.
      cx[i] = b[col.x] != null ? b[col.x] : x[i];
      cy[i] = b[col.y] != null ? b[col.y] : y[i];
      usage[i] = b[col.usage];
      const et = Math.max(1, b[col.etages] || 1);
      val[i] = Math.min(255, Math.round((BUTIN[usage[i]] ?? 2) * (1 + (et - 1) * .4)));
      etat[i] = 0;              // 0 intacte · 1 forcée · 2 pillée · 3 en feu
    }
    // Une grille plate sur les portes, du même bois que celle des corps : on
    // cherche « une maison à moins de vingt-six mètres » vingt fois par
    // seconde et par escouade, et une Map à clefs de texte se paierait ici
    // comme elle s'est payée partout ailleurs.
    const M = 40;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < n; i++) {
      if (x[i] < x0) x0 = x[i]; if (x[i] > x1) x1 = x[i];
      if (y[i] < y0) y0 = y[i]; if (y[i] > y1) y1 = y[i];
    }
    const nx = Math.max(1, Math.ceil((x1 - x0) / M) + 1);
    const ny = Math.max(1, Math.ceil((y1 - y0) / M) + 1);
    const cnt = new Int32Array(nx * ny + 1);
    const casier = (i) => Math.min(ny - 1, Math.max(0, ((y[i] - y0) / M) | 0)) * nx +
                          Math.min(nx - 1, Math.max(0, ((x[i] - x0) / M) | 0));
    for (let i = 0; i < n; i++) cnt[casier(i) + 1]++;
    for (let k = 0; k < nx * ny; k++) cnt[k + 1] += cnt[k];
    const rang = new Int32Array(n), curseur = cnt.slice();
    for (let i = 0; i < n; i++) rang[curseur[casier(i)]++] = i;
    S.bati = { source: src, n, x, y, cx, cy, val, etat, fouille, occupation, usage,
             M, x0, y0, nx, ny, debut: cnt, ordre: rang,
             forcees: 0, brulees: 0, butin: 0, feux:new Set() };
  }

  // COMBIEN CHACUN S'ARRÊTE, par humeur de corps. Une chance par seconde de
  // marche, pour un homme qui passe devant une porte encore fermée.
  //
  // Ce sont les seuls chiffres de tout le module qui décident d'une PERSONNE
  // plutôt que d'une physique, et ils sont assumés comme tels : ce sont des
  // caractères, pas des mesures. Cranche ne s'arrête jamais parce que c'est
  // Cranche ; Petit Wend s'arrête devant tout parce que ce sont des enfants qui
  // n'ont jamais rien eu.
  // `APPETIT` est déposé : l'envie de butin se demande à la couche 4, avec le
  // tempérament de l'homme et ce qu'il a sous la main. Voir la branche du
  // pillage dans `soldat()`.
  // les faux gueux brûle au lieu d'emporter — plus vite, et il ne reste rien.
  // MÊME CASSE SILENCIEUSE QUE `APPETIT`, ET ON LA RÉPARE AU PASSAGE : ce
  // tableau était indexé sur `h.humeur`, champ dissous dans la couche 1 et
  // absent des hommes depuis. Il rendait donc `FEU` pour tout le monde — les
  // faux gueux, dont le personnage entier est qu'ils BRÛLENT au lieu
  // d'emporter, mettaient le feu six pour cent du temps comme n'importe qui.
  // On s'indexe sur le corps, seule clef qui existe encore.
  const BRULE = { gueux: 0.75, cranche: 0, bleusailles: 0.10 };

  /** Forcer une maison : y aller, y rester, en ressortir. */
  function piller(h, dt) {
    const b = h.maison;
    if (b == null || !S.bati) { h.etat = "colonne"; return; }
    const d = Math.hypot(S.bati.x[b] - h.x, S.bati.y[b] - h.y);
    // On y va — en ligne droite, et c'est honnête : la porte donne sur la rue
    // où l'on marchait déjà, il y a vingt-six mètres au plus.
    if (d > 1.5) { h.surVoie = false; versLe(h, S.bati.x[b], S.bati.y[b], MARCHE, dt); return; }
    h.reste_pille -= dt;
    if (h.reste_pille > 0) return;
    // ON RESSORT. Le butin est celui de la maison, pas du temps passé — un
    // taudis fouillé une minute reste un taudis.
    S.bati.butin += S.bati.val[b];
    const brule = R() < (BRULE[h.corps] ?? FEU);
    S.bati.etat[b] = brule ? 3 : 2;
    if (brule) {
      S.bati.brulees++;
      S.bati.feux.add(b);
      // Le feu se voit de loin, et c'est le seul acte de cette bataille qui
      // change la ville pour de bon. On ne le note que de loin en loin, sinon
      // les annales ne parlent plus que de fumée.
      noter("maison-brulee", h.x, h.y,
            { clef: "feu:" + (h.corps || "?"), dit: { corps: h.corps } });
    }
    h.maison = null;
    h.etat = "colonne";
    // Il a perdu sa place dans la colonne : il la reprend où il en était, ce
    // qui le met derrière ceux qui n'ont pas ralenti. Personne ne l'attend.
    h.surRail = false;
  }

  /** La maison intacte la plus proche, dans la portée. Rend -1 s'il n'y en a pas. */
  function maisonLibre(px, py, portee) {
    if (!S.bati) return -1;
    const M = S.bati.M;
    const i0 = Math.max(0, Math.min(S.bati.nx - 1, ((px - S.bati.x0) / M) | 0));
    const j0 = Math.max(0, Math.min(S.bati.ny - 1, ((py - S.bati.y0) / M) | 0));
    const r = Math.ceil(portee / M);
    let meil = -1, dmin = portee * portee;
    for (let j = Math.max(0, j0 - r); j <= Math.min(S.bati.ny - 1, j0 + r); j++) {
      for (let i = Math.max(0, i0 - r); i <= Math.min(S.bati.nx - 1, i0 + r); i++) {
        const c = j * S.bati.nx + i;
        for (let k = S.bati.debut[c]; k < S.bati.debut[c + 1]; k++) {
          const b = S.bati.ordre[k];
          if (S.bati.etat[b]) continue;               // déjà forcée
          const d = (S.bati.x[b] - px) ** 2 + (S.bati.y[b] - py) ** 2;
          if (d < dmin) { dmin = d; meil = b; }
        }
      }
    }
    return meil;
  }

  // ===========================================================================
  // LE RATISSAGE — UNE MISSION COMMUNE, DES CONNAISSANCES LOCALES
  // ===========================================================================
  // Le bâtiment est le seul « intérieur » que le plan permette d'affirmer. On
  // sait où est sa porte et quel usage il a ; on n'invente ni chambres ni
  // escaliers. Franchir le seuil change donc `interieur`, qui suffit à couper
  // toute perception et tout combat à travers les murs.
  const VOIX_PAIRS = 11;
  const MAILLE_SECTEUR = 32;
  const FILE_HUIS = 16;       // profondeur d'une vintaine en file devant une porte

  function grainTexte(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i); h = Math.imul(h, 16777619);
    }
    return (h >>> 0) / 4294967296;
  }

  const cleSecteur = (m, b) =>
    Math.floor((S.bati.x[b] - m.x0) / MAILLE_SECTEUR) + ":" +
    Math.floor((S.bati.y[b] - m.y0) / MAILLE_SECTEUR);

  function batiments() {
    if (!S.bati) return [];
    const l = new Array(S.bati.n);
    for (let i = 0; i < S.bati.n; i++) l[i] = {
      id:i, x:S.bati.x[i], y:S.bati.y[i], usage:S.bati.usage[i],
      fouille:S.bati.fouille ? S.bati.fouille[i] : 0,
      occupe:!!(S.bati.occupation && S.bati.occupation[i]),
    };
    return l;
  }

  function faitRatissage(u, type, b, plus) {
    const r = u && u.ratissage;
    if (!r) return null;
    const f = Object.assign({
      id:r.missionId + ":" + type + ":" + b,
      type, batiment:b, usage:S.bati.usage[b], x:S.bati.x[b], y:S.bati.y[b],
      observeA:+S.temps.toFixed(1), source:"vu", auteur:u.id,
    }, plus || {});
    r.faits.set(f.id, f);
    assimilerFait(r, f);
    return f;
  }

  /**
   * Un danger qui ne vient pas d'un autre combattant.
   *
   * L'appelant calcule la géométrie du phénomène (ombre, rugissement, feu) et
   * livre une exposition par homme. Le moteur garde ce qui lui appartient :
   * les canaux sensoriels, leur latence, la réaction corporelle, la blessure et
   * la contagion produite par quelqu'un qui tombe. Ainsi un dragon n'a pas à
   * imiter un épéiste, et l'épreuve ne peut plus écrire `tombe = true` à côté
   * du système commun.
   *
   * Une exposition vaut :
   *   { homme, vue?, ouie?, chaleur?, soudainete?, deFace?, degat? }
   * Les forces sensorielles sont bornées à [0,1]. `degat` est une perte de PV
   * déjà intégrée sur le pas courant par le modèle physique du danger.
   */
  function dangerExterieur(expositions, source) {
    const bilan = { exposes: 0, vus: 0, entendus: 0, touches: 0,
                    degats: 0, chutes: 0 };
    if (!Array.isArray(expositions) || !window.Corps) return bilan;
    const borner = (x) => Math.max(0, Math.min(1, +x || 0));
    const pousser = (h, quoi, canal, force, soudainete, deFace) => {
      if (!h.recu || h.recu.length >= 8 || force <= 0) return false;
      h.recu.push({ quoi, canal, force: borner(force),
                    soudainete: borner(soudainete == null ? force : soudainete),
                    deFace: deFace == null ? 1 : Math.max(-1, Math.min(1, deFace)),
                    source: source || "danger extérieur", t: S.temps });
      return true;
    };

    for (const q of expositions) {
      const h = q && q.homme;
      if (!h || h.etat === "mort" || h.etat === "blesse" ||
          h.etat === "prisonnier" || h.etat === "rentre") continue;
      bilan.exposes++;
      const menace = borner(q.menace);
      if (menace > 0) {
        h.menaceExterieure = S.temps > (h.menaceJus || -Infinity)
          ? menace : Math.max(h.menaceExterieure || 0, menace);
        h.menaceX = Number.isFinite(q.menaceX) ? q.menaceX : h.x;
        h.menaceY = Number.isFinite(q.menaceY) ? q.menaceY : h.y;
        h.menaceGenre = q.genre || "danger-exterieur";
        h.menaceJus = Math.max(h.menaceJus || -Infinity,
                               S.temps + Math.max(0.15, +q.dureeMenace || 0.9));
      }
      const dragon = q.genre === "dragon";
      if (pousser(h, q.quoiVue || (dragon ? "dragon en approche" : "danger en approche"), "vue", q.vue,
                  q.soudaineteVue == null ? q.soudainete : q.soudaineteVue,
                  q.deFace)) bilan.vus++;
      if (pousser(h, q.quoiOuie || (dragon ? "rugissement au-dessus" : "danger entendu"), "ouie", q.ouie,
                  q.soudaineteOuie == null ? q.soudainete : q.soudaineteOuie,
                  q.deFace)) bilan.entendus++;
      if (pousser(h, q.quoiChaleur || (dragon ? "souffle brûlant" : "chaleur dangereuse"), "tact", q.chaleur,
                  q.soudaineteChaleur == null ? q.soudainete : q.soudaineteChaleur,
                  q.deFace)) bilan.touches++;

      const degat = Math.max(0, +q.degat || 0);
      if (!degat) continue;
      const avant = h.pv;
      h.pv -= degat;
      bilan.degats += Math.min(degat, Math.max(0, avant));
      if (h.pv <= 0) { tomber(h); bilan.chutes++; }
    }
    return bilan;
  }

  /** Rafraîchit des foyers calculés par un moteur extérieur (incendie urbain). */
  function signalerIncendies(sources, ttl = 1) {
    const vie = Math.max(.2, +ttl || 1);
    for (const q of Array.isArray(sources) ? sources : []) {
      if (!q || q.actif === false || !Number.isFinite(q.x) || !Number.isFinite(q.y)) continue;
      const id = q.id == null ? `${Math.round(q.x)}:${Math.round(q.y)}` : String(q.id);
      S.incendiesSignales.set(id, {
        id, x:+q.x, y:+q.y, rayon:Math.max(0, +q.rayon || 0),
        intensite:Math.max(0, Math.min(1, +q.intensite || 0)),
        expire:S.temps + vie,
      });
    }
    return S.incendiesSignales.size;
  }

  /** Les foyers actifs, agrégés spatialement avant d'être montrés aux hommes. */
  function incendiesActifs() {
    const cellules = new Map(), pas = 24;
    const ajouter = (x, y, intensite, rayon) => {
      const cle = Math.floor(x / pas) + ":" + Math.floor(y / pas);
      let q = cellules.get(cle);
      if (!q) cellules.set(cle, q = { id:"feu:" + cle, x:0, y:0, poids:0,
                                     intensite:0, rayon:0, n:0 });
      const w = Math.max(.05, intensite);
      q.x += x * w; q.y += y * w; q.poids += w; q.n++;
      q.intensite = Math.max(q.intensite, intensite);
      q.rayon = Math.max(q.rayon, rayon);
    };
    if (S.bati && S.bati.feux) for (const b of S.bati.feux)
      if (S.bati.etat[b] === 3) ajouter(S.bati.cx[b], S.bati.cy[b], .82, 4.5);
    for (const [id, q] of S.incendiesSignales) {
      if (q.expire < S.temps) { S.incendiesSignales.delete(id); continue; }
      ajouter(q.x, q.y, q.intensite, q.rayon);
    }
    return [...cellules.values()].map((q) => ({
      id:q.id, x:q.x / q.poids, y:q.y / q.poids,
      intensite:Math.min(1, q.intensite + .06 * Math.log2(Math.max(1, q.n))),
      rayon:Math.min(18, q.rayon + Math.sqrt(q.n - 1) * 2), n:q.n,
    }));
  }

  function fairePercevoirIncendies() {
    if (S.temps < S.prochainePerceptionIncendie || !S.hommes.length) return;
    S.prochainePerceptionIncendie = S.temps + PAS_PERCEPTION_INCENDIE;
    const sources = incendiesActifs();
    if (!sources.length) return;
    const maille = 64, grille = new Map();
    for (const q of sources) {
      const cle = Math.floor(q.x / maille) + ":" + Math.floor(q.y / maille);
      let xs = grille.get(cle); if (!xs) grille.set(cle, xs = []); xs.push(q);
    }
    const expositions = [];
    for (const h of S.hommes) {
      if (h.tete || h.hors || h.interieur != null || h.etat === "mort" ||
          h.etat === "blesse" || h.etat === "prisonnier" || h.etat === "rentre") continue;
      const ci = Math.floor(h.x / maille), cj = Math.floor(h.y / maille);
      let meilleur = null, bord0 = Infinity;
      for (let i=-1;i<=1;i++) for (let j=-1;j<=1;j++) {
        const xs = grille.get((ci+i) + ":" + (cj+j)); if (!xs) continue;
        for (const q of xs) {
          const bord = Math.max(0, Math.hypot(h.x-q.x, h.y-q.y) - q.rayon);
          if (bord < bord0 && bord <= PORTEE_PERCEPTION_INCENDIE) {
            meilleur = q; bord0 = bord;
          }
        }
      }
      if (!meilleur) continue;
      const I = meilleur.intensite;
      const vue = I * Math.max(.08, 1 - bord0 / 65);
      const menace = I * Math.max(0, 1 - bord0 / 28);
      const chaleur = I * Math.max(0, 1 - bord0 / 12);
      expositions.push({ homme:h, vue, ouie:vue * .48, chaleur, menace,
        menaceX:meilleur.x, menaceY:meilleur.y, genre:"incendie", dureeMenace:.8,
        soudainete:.18 + .55 * menace,
        quoiVue:"incendie actif", quoiOuie:"crépitement et cris",
        quoiChaleur:"rayonnement du feu" });
    }
    if (expositions.length) dangerExterieur(expositions, "incendies actifs");
  }

  // La faculté commune regarde depuis le corps du chef. Elle ne reçoit jamais
  // les centres globaux que les bancs calculent après coup : seulement les
  // hommes réellement visibles autour de lui, agrégés en une zone grossière.
  function chargeCommandant(h) {
    for (const dep of S.deploiements.values()) {
      if (!dep.commandants || !dep.commandants.has(h)) continue;
      return { dep, charge:dep.commandants.get(h) };
    }
    return null;
  }

  function forcePropreCommandant(h, c, dep) {
    return c.role === "chef de corps"
      ? S.hommes.filter((o) => o.camp === h.camp && o.corps === c.corps && pese(o)).length
      : S.formations.filter((u) => u.camp === h.camp && u.cadre.ralliement &&
          u.cadre.ralliement.deploiementId === dep.id &&
          u.cadre.ralliement.aile === c.aile)
        .reduce((n, u) => n + u.membres.filter(pese).length, 0);
  }

  function objectifCommandant(h, dep) {
    const u = formationDe(h), d = u && u.ordre && u.ordre.destination;
    if (d && Number.isFinite(d.x) && Number.isFinite(d.y))
      return { x:d.x, y:d.y, nom:d.nom || "objectif de l'unité" };
    if (dep && dep.centre) return { x:dep.centre.x, y:dep.centre.y,
      nom:dep.but === "engager" ? "front à engager" : "repère du déploiement" };
    return null;
  }

  // LA CARTE EST RECONSTRUITE DEPUIS UNE MÉMOIRE, JAMAIS DEPUIS LE CAMP
  // ADVERSE. Les positions réelles ne servent qu'au champ de vision et aux
  // commandants alliés avec lesquels cet homme a effectivement communiqué ;
  // le graphe filtre lui-même ceux qu'il ne connaît pas.
  function carteCommandant(debugId, champConnu) {
    const h = S.hommes.find((o) => o.debugId === debugId);
    const q = h && chargeCommandant(h);
    if (!h || !q || !h.commandement) return null;
    const champ = champConnu || Commandement.champVision({
      position:{ x:h.x, y:h.y }, rayon:65, rayons:48, pas:1.5,
      obstacle:obstacleConnu() ? obstacleEn : null });
    const identites = new Map([...q.dep.commandants.entries()].map(([a, ca]) =>
      [String(a.debugId), { id:a.debugId, nom:a.nom || ca.role,
        echelon:ca.memoire.echelon }]));
    const alliesConnus = new Map();
    for (const e of h.commandement.communications) {
      const deMoi = String(e.de) === String(h.debugId);
      const versMoi = String(e.vers) === String(h.debugId);
      const id = deMoi ? e.vers : versMoi ? e.de : null;
      const position = deMoi ? e.positionVers : versMoi ? e.positionDe : null;
      if (id == null || !position) continue;
      const a = identites.get(String(id));
      if (a) alliesConnus.set(String(id), Object.assign({}, a,
        { position:{ x:position.x, y:position.y } }));
    }
    const allies = [...alliesConnus.values()];
    const forcePropre = forcePropreCommandant(h, q.charge, q.dep);
    const graphe = Commandement.grapheTactique(h.commandement, {
      maintenant:S.temps, position:{ x:h.x, y:h.y }, nom:h.nom || q.charge.role,
      objectif:objectifCommandant(h, q.dep), forcePropre, champ, allies,
    });
    return Object.assign(graphe, {
      id:h.debugId, nom:h.nom || q.charge.role, role:q.charge.role,
      deploiement:q.dep.id, forcePropre,
      estimation:q.charge.estimation || Commandement.estimation(h.commandement,
        forcePropre, S.temps),
    });
  }

  function selectionnerCarteCommandant(debugId) {
    if (debugId == null || S.carteCommandantId === debugId) S.carteCommandantId = null;
    else if (carteCommandant(debugId)) S.carteCommandantId = debugId;
    peindre();
    return S.carteCommandantId == null ? null : carteCommandant(S.carteCommandantId);
  }

  function observerCommandants() {
    for (const dep of S.deploiements.values()) {
      if (!dep.commandants || S.temps - dep.commandeObserveA < 5) continue;
      dep.commandeObserveA = S.temps;
      const actifs = [...dep.commandants.entries()].filter(([h]) => pese(h));
      for (const [h, c] of actifs) {
        // Quarante-huit rayons sont calculés une fois pour le chef et servent
        // à toutes ses observations de ce battement. Une maison masque donc
        // vraiment ce qui est derrière elle sans payer une marche de rayon
        // pour chacun des centaines d'ennemis possibles.
        c.champ = Commandement.champVision({ position:{ x:h.x, y:h.y }, rayon:65,
          rayons:48, pas:1.5, obstacle:obstacleConnu() ? obstacleEn : null });
        const vus = S.hommes.filter((o) => !o.hors && !o.tete && pese(o) &&
          o.camp !== h.camp && memeEspace(h, o) &&
          Commandement.visibleDansChamp(c.champ, o, 1.2));
        if (vus.length) {
          // Un contact par maille observée. Fondre deux groupes séparés dans
          // leur centre moyen pouvait poser une croyance au milieu d'une
          // maison — exactement là où le chef ne voyait personne — et faisait
          // disparaître le trou tactique entre eux. La carte conserve donc la
          // résolution grossière de vingt-cinq mètres, jamais les positions
          // individuelles et jamais un barycentre global omniscient.
          const groupes = new Map();
          for (const o of vus) {
            const zone = Math.round(o.x / 25) + ":" + Math.round(o.y / 25);
            if (!groupes.has(zone)) groupes.set(zone, []);
            groupes.get(zone).push(o);
          }
          for (const [zone, groupe] of groupes) {
          const x = groupe.reduce((n, o) => n + o.x, 0) / groupe.length;
          const y = groupe.reduce((n, o) => n + o.y, 0) / groupe.length;
          const montes = groupe.filter((o) => o.montureCombat).length;
          const longuesHampes = groupe.filter((o) => o.arme === ARMES.pique).length;
          const signatures = {};
          if (montes) signatures.montes = {
            min:Math.max(1, Math.floor(montes * .7)), max:Math.ceil(montes * 1.3) };
          if (longuesHampes) signatures.longuesHampes = {
            min:Math.max(1, Math.floor(longuesHampes * .7)),
            max:Math.ceil(longuesHampes * 1.3) };
          Commandement.assimiler(c.memoire, {
            id:"vision:" + dep.id + ":" + h.debugId + ":" + zone + ":" + Math.floor(S.temps / 5),
            genre:"ennemi", sujet:{ genre:"zone", id:zone },
            zone:{ id:zone }, position:{ x, y }, statut:"actif",
            forceMin:Math.max(1, Math.floor(groupe.length * .65)),
            forceMax:Math.max(1, Math.ceil(groupe.length * 1.35)),
            signatures,
            source:"vu", auteur:h.debugId, observeA:+S.temps.toFixed(1),
            texte:"ennemis vus devant mon front" +
              (montes ? ", dont des hommes montés" : "") +
              (longuesHampes ? ", avec de longues hampes" : ""),
          }, +S.temps.toFixed(1));
          }
        }
        const forcePropre = forcePropreCommandant(h, c, dep);
        c.estimation = Commandement.estimation(c.memoire, forcePropre, S.temps);
      }
      // Deux chefs du même rang ne se parlent que s'ils se rencontrent et ont
      // effectivement quelque chose de neuf. Aucune radio implicite.
      for (let i = 0; i < actifs.length; i++) for (let j = i + 1; j < actifs.length; j++) {
        const [a, ca] = actifs[i], [b, cb] = actifs[j];
        if (ca.role !== cb.role || !memeEspace(a, b) || Math.hypot(a.x-b.x, a.y-b.y) > 11) continue;
        const ab = Commandement.inconnusPour(ca.memoire, cb.memoire);
        const ba = Commandement.inconnusPour(cb.memoire, ca.memoire);
        if (!ab.length && !ba.length) continue;
        const recusB = Commandement.transmettre(ca.memoire, cb.memoire,
          { maintenant:+S.temps.toFixed(1), faits:ab });
        const recusA = Commandement.transmettre(cb.memoire, ca.memoire,
          { maintenant:+S.temps.toFixed(1), faits:ba });
        const parole = { a:+S.temps.toFixed(1), de:a.debugId, vers:b.debugId,
          positionDe:{ x:+a.x.toFixed(1), y:+a.y.toFixed(1) },
          positionVers:{ x:+b.x.toFixed(1), y:+b.y.toFixed(1) },
          faits:recusA.length + recusB.length,
          ordreA:ca.memoire.ordre && ca.memoire.ordre.texte,
          ordreB:cb.memoire.ordre && cb.memoire.ordre.texte };
        Commandement.tracerCommunication(ca.memoire, parole);
        Commandement.tracerCommunication(cb.memoire, parole);
      }
    }
  }

  function confianceActuelle(c) {
    return Commandement.confiance(c, S.temps);
  }

  function assimilerFait(r, f) {
    if (!r || !f || f.batiment == null) return;
    let statut = "possible", forceMin = 0, forceMax = 0;
    if (f.type === "ennemis_trouves") {
      statut = "actif"; forceMin = Math.max(1, (f.nombre || 1) - 1); forceMax = (f.nombre || 1) + 1;
    } else if (f.type === "groupe_vaincu" || f.type === "chef_rebelle_identifie") {
      statut = "neutralise";
    } else if (f.type === "maison_claire" || f.type === "deja_fouillee") {
      statut = "clair";
    } else if (f.type === "maison_inaccessible") {
      statut = "inaccessible";
    } else return;
    return Commandement.assimiler(r.commandement, Object.assign({}, f, {
      genre:statut === "actif" ? "ennemi" : "lieu",
      sujet:{ genre:"lieu", id:f.batiment,
        nom:(f.usage || "bâtiment") + " n°" + f.batiment },
      position:{ x:f.x, y:f.y }, statut, forceMin, forceMax,
    }), +S.temps.toFixed(1));
  }

  function estimerSituation(u) {
    const r = u && u.ratissage;
    if (!r) return null;
    const e = Commandement.estimation(r.commandement, u.membres.filter(pese).length, S.temps);
    let posture = "chercher";
    if (e.rapport === "inferieur") posture = "eviter-et-appeler";
    else if (e.rapport === "superieur") posture = "reduire";
    else if (e.lieux) posture = "appuyer";
    return Object.assign(e, { posture });
  }

  function donnerOrdreLocal(u, texte, raison) {
    const r = u && u.ratissage;
    if (!r || r.ordreLocal === texte) return;
    r.ordreLocal = texte; r.raisonOrdre = raison; r.ordreLocalA = +S.temps.toFixed(1);
    if (u.ordre) {
      u.ordre.version = (u.ordre.version || 0) + 1;
      u.ordre.donneA = S.temps;
      u.ordre.ditA = S.temps;
    }
  }

  function phraseFait(f) {
    const lieu = "le " + (f.usage || "bâtiment") + " n°" + f.batiment;
    if (f.type === "ennemis_trouves") return "J'ai vu " + (f.nombre || "des") + " hommes armés dans " + lieu + ".";
    if (f.type === "groupe_vaincu") return "Nous avons vaincu le groupe de " + lieu + ".";
    if (f.type === "chef_rebelle_identifie") return "Le chef rebelle était avec le groupe de " + lieu + ".";
    if (f.type === "maison_claire") return "Aucun ennemi vu dans " + lieu + ".";
    if (f.type === "maison_inaccessible") return "Nous n'avons trouvé aucun passage vers " + lieu + ".";
    if (f.type === "deja_fouillee") return lieu.charAt(0).toUpperCase() + lieu.slice(1) + " avait déjà été fouillé.";
    return null;
  }

  function phraseEstimation(s) {
    return Commandement.direEstimation(s).replace(/ zones?\.$/, (x) => x === " zone." ? " lieu." : " lieux.");
  }

  function choisirSecteur(u, m) {
    const r = u.ratissage, chef = guideDe(u);
    if (!chef) return null;
    const pris = new Set();
    for (const e of r.engagements.values()) if (e.actif && e.par !== u.id) pris.add(e.secteur);
    let meilleur = null, dmin = Infinity;
    for (const [cle, bs] of m.secteurs) {
      if (pris.has(cle)) continue;
      const inconnus = bs.filter((b) => ![...r.faits.values()].some((f) =>
        f.batiment === b && (f.type === "maison_claire" || f.type === "groupe_vaincu" ||
                            f.type === "deja_fouillee")));
      if (!inconnus.length) continue;
      const cx = inconnus.reduce((n, b) => n + S.bati.x[b], 0) / inconnus.length;
      const cy = inconnus.reduce((n, b) => n + S.bati.y[b], 0) / inconnus.length;
      const d = Math.hypot(cx - chef.x, cy - chef.y);
      if (d < dmin) { dmin = d; meilleur = cle; }
    }
    if (!meilleur) return null;
    r.repos = false;
    r.rallieA = null;
    r.posteRdv = null;
    r.ralliementMarche = null;
    r.ralliementLocal = false;
    r.retourChef = null;
    r.secteur = meilleur;
    const e = { secteur:meilleur, par:u.id, depuis:+S.temps.toFixed(1), actif:true };
    r.engagements.set(meilleur + "|" + u.id, e); r.engagement = e;
    donnerOrdreLocal(u, "Prenez le secteur " + meilleur + ". Quatre hommes par maison ; les autres tiennent la rue.",
      "ce secteur est le plus proche qui ne soit ni attribué ni reconnu");
    m.engagementsPris++;
    noter("engagement-pair", chef.x, chef.y,
      { dit:{ chef:chef.nom || u.id, phrase:"Je prends le secteur " + meilleur + ".",
              secteur:meilleur, mission:m.id } });
    return meilleur;
  }

  function reglerConflits(u, m) {
    const r = u.ratissage;
    if (!r || !r.engagement) return;
    const concurrents = [...r.engagements.values()].filter((e) =>
      e.actif && e.secteur === r.engagement.secteur);
    concurrents.sort((a, b) => a.depuis - b.depuis || a.par.localeCompare(b.par));
    if (!concurrents.length || concurrents[0].par === u.id) return;
    // Une conversation de chefs ne fait pas disparaître une équipe déjà
    // derrière une porte. L'unité cède le secteur APRÈS cette maison ; avant,
    // elle abandonnait `courant` sur-le-champ et les hommes intérieurs se
    // mettaient à viser la maison suivante à travers les murs.
    if (r.courant != null && u.membres.some((h) => h.interieur === r.courant)) {
      r.quitterSecteurApres = true; return;
    }
    r.engagement.actif = false; r.engagement = null; r.secteur = null;
    r.courant = null; r.phase = "choisir"; m.conflitsResolus++;
  }

  function echangerEntrePairs(m) {
    const us = m.unites.map((id) => S.formations.find((u) => u.id === id)).filter(Boolean);
    for (let i = 0; i < us.length; i++) for (let j = i + 1; j < us.length; j++) {
      const a = us[i], b = us[j], ca = guideDe(a), cb = guideDe(b);
      if (!ca || !cb || !memeEspace(ca, cb) ||
          Math.hypot(ca.x - cb.x, ca.y - cb.y) > VOIX_PAIRS) continue;
      const ra = a.ratissage, rb = b.ratissage;
      const cle = a.id < b.id ? a.id + "|" + b.id : b.id + "|" + a.id;
      const dernier = m.rencontres.get(cle) ?? -Infinity;
      const nouveaute = [...ra.faits.keys()].some((k) => !rb.faits.has(k)) ||
        [...rb.faits.keys()].some((k) => !ra.faits.has(k)) ||
        [...ra.engagements.keys()].some((k) => !rb.engagements.has(k)) ||
        [...rb.engagements.keys()].some((k) => !ra.engagements.has(k));
      // On se présente une fois, puis on ne se reparle que si quelqu'un a
      // quelque chose de neuf. La proximité seule ne doit pas fabriquer un
      // conseil permanent au milieu de la rue.
      if (!nouveaute && dernier !== -Infinity) continue;
      const nouveauxA = [], nouveauxB = [];
      let faits = 0;
      for (const [k, f] of ra.faits) if (!rb.faits.has(k)) {
        const recu = Commandement.transmettre(ra.commandement, rb.commandement,
          { maintenant:+S.temps.toFixed(1), faits:[f] })[0];
        if (recu) { assimilerFait(rb, recu); nouveauxA.push(f); faits++; }
      }
      for (const [k, f] of rb.faits) if (!ra.faits.has(k)) {
        const recu = Commandement.transmettre(rb.commandement, ra.commandement,
          { maintenant:+S.temps.toFixed(1), faits:[f] })[0];
        if (recu) { assimilerFait(ra, recu); nouveauxB.push(f); faits++; }
      }
      for (const [k, e] of ra.engagements) if (!rb.engagements.has(k) ||
          rb.engagements.get(k).depuis > e.depuis) rb.engagements.set(k, Object.assign({}, e));
      for (const [k, e] of rb.engagements) if (!ra.engagements.has(k) ||
          ra.engagements.get(k).depuis > e.depuis) ra.engagements.set(k, Object.assign({}, e));
      const phrasesA = [], phrasesB = [];
      if (dernier === -Infinity) {
        phrasesA.push("Mon ordre est « " + ordreLitteral(a) + " ». Et le vôtre ?");
        phrasesB.push("Mon ordre est « " + ordreLitteral(b) + " ».");
      }
      for (const f of nouveauxA) { const p = phraseFait(f); if (p) phrasesA.push(p); }
      for (const f of nouveauxB) { const p = phraseFait(f); if (p) phrasesB.push(p); }
      phrasesA.push(phraseEstimation(estimerSituation(a)));
      phrasesB.push(phraseEstimation(estimerSituation(b)));
      const communication = { a:+S.temps.toFixed(1), de:a.id, vers:b.id,
        phrasesA, phrasesB, estimationA:estimerSituation(a), estimationB:estimerSituation(b) };
      Commandement.tracerCommunication(ra.commandement, communication);
      Commandement.tracerCommunication(rb.commandement, communication);
      m.communications.push(communication);
      if (m.communications.length > 80) m.communications.shift();
      m.rencontres.set(cle, S.temps); m.echanges++; m.faitsTransmis += faits;
      m.messages += phrasesA.length + phrasesB.length;
      noter("echange-pairs", (ca.x + cb.x) / 2, (ca.y + cb.y) / 2,
        { dit:{ entre:[ca.nom || a.id, cb.nom || b.id],
          ordreA:ordreLitteral(a), ordreB:ordreLitteral(b), faits,
          paroles:[phrasesA, phrasesB], mission:m.id } });
      reglerConflits(a, m); reglerConflits(b, m);
      if (ra.phase === "rendre-compte") ra.phase = "choisir";
      if (rb.phase === "rendre-compte") rb.phase = "choisir";
    }
  }

  function choisirMaison(u, m) {
    const r = u.ratissage, chef = guideDe(u);
    if (!chef || !r.secteur) return null;
    const faitsBat = new Set([...r.faits.values()].filter((f) =>
      f.type === "maison_claire" || f.type === "groupe_vaincu" || f.type === "deja_fouillee")
      .map((f) => f.batiment));
    for (const f of r.faits.values())
      if (f.type === "maison_inaccessible") faitsBat.add(f.batiment);
    let b = -1, dmin = Infinity;
    for (const q of m.secteurs.get(r.secteur) || []) {
      if (faitsBat.has(q)) continue;
      const d = Math.hypot(S.bati.x[q] - chef.x, S.bati.y[q] - chef.y);
      if (d < dmin) { dmin = d; b = q; }
    }
    if (b < 0) return null;
    r.repos = false;
    r.courant = b; r.phase = "approcher"; r.progres = 0; r.approche = null;
    r.combatDepuis = null;
    r.passage = { b, prochain:0, traverses:0 };
    r.marcheMaison = { x:chef.x, y:chef.y, avanceA:S.temps };
    // Une maison reçoit une petite équipe, pas la vintaine entière. Le
    // vintenar conserve la rue et fait tourner des groupes de quatre hommes.
    const disponibles = u.membres.filter((h) => h !== chef && pese(h));
    const n = Math.min(4, disponibles.length), depart = r.prochaineEquipe || 0;
    const equipe = [];
    for (let i = 0; i < n; i++) equipe.push(disponibles[(depart + i) % disponibles.length]);
    r.prochaineEquipe = disponibles.length ? (depart + n) % disponibles.length : 0;
    r.fouilleurs = new Set(equipe.map((h) => h.debugId));
    r.chefFouille = equipe[0] ? equipe[0].debugId : chef.debugId;
    donnerOrdreLocal(u, "Quatre hommes dans le " + (S.bati.usage[b] || "bâtiment") +
      " n°" + b + ". Les autres gardent l'huis et la rue.",
      "la maison suivante de notre secteur n'a pas encore été reconnue");
    ordonnerFormation(u.id,
      { id:"batiment:" + b, nom:"le " + (S.bati.usage[b] || "bâtiment") + " n°" + b,
        x:S.bati.x[b], y:S.bati.y[b] },
      { mode:"fouiller", source:"ordre-ratissage", texte:r.ordre });
    return b;
  }

  // Au rendez-vous, seuls les VINTENAR forment l'échelon supérieur. Leurs
  // hommes tiennent le dernier poste reçu : le chef cesse temporairement
  // d'être leur destination physique sans cesser d'être leur chef.
  function placeDeCommandementRdv(u, m) {
    if (!m.formationRdv) {
      const elements=m.unites.map((id) => S.formations.find((q) => q.id===id))
        .filter(Boolean).map((q) => { const h=guideDe(q); return h && { id:q.id,x:h.x,y:h.y }; })
        .filter(Boolean);
      const bs=m.batiments || [], front=bs.length ? {
        x:bs.reduce((n,b)=>n+S.bati.x[b],0)/bs.length,
        y:bs.reduce((n,b)=>n+S.bati.y[b],0)/bs.length,
      } : { x:m.rdv.x+1,y:m.rdv.y };
      // Trois mètres suffisent entre des CHEFS seuls et les gardent tous à
      // portée de parole. Leurs vintaines, elles, restent à leur dernier poste.
      m.formationRdv=new Map(Commandement.formerEchelon({ elements, ancre:m.rdv, front,
        espacement:3, libre:(x,y)=>libreEn(x,y)===true }).map((p)=>[p.id,p]));
    }
    return m.formationRdv.get(u.id) || { x:m.rdv.x,y:m.rdv.y,fx:1,fy:0 };
  }

  // Avant que les chefs se détachent, les VINTAINES rejoignent une ligne de
  // ralliement derrière le rendez-vous. Ce ne sont pas quatre coordonnées
  // d'hommes : chaque place est une ancre d'unité, et les hommes conservent
  // leurs relations de formation autour de leur vintenar.
  function placeDeRalliementRdv(u, m) {
    if (!m.ralliementRdv) {
      const elements=m.unites.map((id) => S.formations.find((q) => q.id===id))
        .filter(Boolean).map((q) => { const h=guideDe(q); return h && { id:q.id,x:h.x,y:h.y }; })
        .filter(Boolean);
      const bs=m.batiments || [], front=bs.length ? {
        x:bs.reduce((n,b)=>n+S.bati.x[b],0)/bs.length,
        y:bs.reduce((n,b)=>n+S.bati.y[b],0)/bs.length,
      } : { x:m.rdv.x+1,y:m.rdv.y };
      let fx=front.x-m.rdv.x, fy=front.y-m.rdv.y;
      const d=Math.hypot(fx,fy)||1; fx/=d; fy/=d;
      const ancre={x:m.rdv.x-fx*12,y:m.rdv.y-fy*12};
      m.ralliementRdv=new Map(Commandement.formerEchelon({ elements, ancre, front,
        espacement:10, libre:(x,y)=>libreEn(x,y)===true }).map((p)=>[p.id,p]));
    }
    return m.ralliementRdv.get(u.id) || { x:m.rdv.x,y:m.rdv.y,fx:1,fy:0 };
  }

  function vintaineRalliee(u, poste) {
    const chef=guideDe(u), xs=u.membres.filter(pese);
    if(!chef || !xs.length || Math.hypot(chef.x-poste.x,chef.y-poste.y)>2.5)return false;
    const proches=xs.filter((h)=>Math.hypot(h.x-chef.x,h.y-chef.y)<=12).length;
    return proches/xs.length>=.7;
  }

  function menerVintaineAuRdv(h,u,poste,dt) {
    const r=u.ratissage, chef=guideDe(u), d=u.ordre.destination;
    if(!r.ralliementMarche)r.ralliementMarche={x:chef.x,y:chef.y,avanceA:S.temps};
    const w=r.ralliementMarche;
    if(Math.hypot(chef.x-w.x,chef.y-w.y)>.8){
      w.x=chef.x;w.y=chef.y;w.avanceA=S.temps;
    }
    // Le graphe de rue peut couper une géométrie que le masque final refuse.
    // Après quinze secondes sans progression, l'unité ne repaie pas la même
    // route : elle termine localement, toujours derrière un seul guide.
    if(!r.ralliementLocal&&S.temps-w.avanceA>15){
      r.ralliementLocal=true;
      u.cadre.finition={id:d.id,
        pts:cheminDePorte(chef.x,chef.y,poste.x,poste.y,true),i:1};
      u.cadre.calculs++;
    }
    if(r.ralliementLocal)finirApprocheFormation(h,u,chef,d,MARCHE,dt);
    else menerFormation(h,d,MARCHE,dt);
  }

  function menerChefAuRdv(h,u,m,p,dt) {
    const r=u.ratissage;
    if (!r.retourChef || r.retourChef.id!==u.id) {
      const trace=S.J&&S.voirie ? S.J.chemin(S.voirie,[h.x,h.y],[p.x,p.y],
        "ratissage:chefs:"+m.id+":"+u.id) : null;
      r.retourChef={id:u.id,trace,avance:0,finition:null};
    }
    const q=r.retourChef;
    if(q.trace&&q.trace.long&&q.avance<q.trace.long){
      q.avance=Math.min(q.trace.long,q.avance+MARCHE*dt);
      surLeRail(h,surTrace(q.trace,q.avance),0);return;
    }
    if(!q.finition)q.finition={pts:cheminDePorte(h.x,h.y,p.x,p.y),i:1};
    const f=q.finition;
    if(f.pts&&f.pts.length){
      while(f.i<f.pts.length-1&&Math.hypot(h.x-f.pts[f.i][0],h.y-f.pts[f.i][1])<.7)f.i++;
      const but=f.pts[Math.min(f.i,f.pts.length-1)];versLe(h,but[0],but[1],MARCHE,dt);
    }else versLe(h,p.x,p.y,MARCHE,dt);
    if(Math.hypot(h.x-p.x,h.y-p.y)<1){h.fx=p.fx;h.fy=p.fy;}
  }

  function approcherPorte(h, u, b, dt, guideLocal) {
    const r = u.ratissage, guide = guideLocal || guideDe(u);
    if (!r.approche || r.approche.b !== b) {
      r.approche = { b, pts:cheminDePorte(guide.x, guide.y, S.bati.x[b], S.bati.y[b]), i:1,
        dernierX:guide.x, dernierY:guide.y, avanceA:S.temps, bloquee:false };
      u.cadre.calculs++;
    }
    const ap = r.approche;
    if (Math.hypot(guide.x - ap.dernierX, guide.y - ap.dernierY) > .8) {
      ap.dernierX = guide.x; ap.dernierY = guide.y; ap.avanceA = S.temps;
    }
    // Une porte erronée, une muraille prise pour un entrepôt ou un cul-de-sac
    // du masque ne retient plus toute l'unité pour l'éternité. Quinze secondes
    // sans gagner un mètre constituent une observation locale : cette maison
    // n'est pas accessible depuis ici, on la note et on en prend une autre.
    if (S.temps - ap.avanceA > 15) { ap.bloquee = true; return false; }
    if (!ap.pts || !ap.pts.length) {
      suivreGuideDirect(h, guide, S.bati.x[b], S.bati.y[b], MARCHE, dt); return true;
    }
    while (ap.i < ap.pts.length - 1 &&
           Math.hypot(guide.x - ap.pts[ap.i][0], guide.y - ap.pts[ap.i][1]) < .7) ap.i++;
    const p = ap.pts[Math.min(ap.i, ap.pts.length - 1)];
    h.passageEtroit = true;
    suivreGuideDirect(h, guide, p[0], p[1], MARCHE, dt);
    h.passageEtroit = false;
    return true;
  }

  function sortirDuBatiment(u, b) {
    for (const h of u.membres) if (h.interieur === b) {
      h.cible = null;
      h.pointInterieur = null; h.sortieBatiment = b;
      h.etat = "sortie-batiment";
    }
  }

  function sortirParHuis(h, dt) {
    const b = h.sortieBatiment;
    if (b == null) return false;
    h.cible = null;
    penser(h, "ressortir par la porte",
      "la fouille de cette maison est terminée", "franchissement en file");
    if (Math.hypot(S.bati.x[b] - h.x, S.bati.y[b] - h.y) > .55) {
      versLe(h, S.bati.x[b], S.bati.y[b], MARCHE, dt); return true;
    }
    h.x = S.bati.x[b]; h.y = S.bati.y[b];
    h.interieur = null; h.entreDepuis = null; h.sortieBatiment = null;
    h.etat = "rassemble";
    return true;
  }

  // Une porte n'est pas une place de rassemblement. Le chef la franchit,
  // puis les siens passent en file à raison d'environ trois hommes par seconde.
  // Le centre cuit du bâtiment est le seul point intérieur que nous connaissions
  // réellement ; chacun s'y rend depuis la porte, sans saut de coordonnées.
  function pointDerriereHuis(b, k, profondeur) {
    const dx = S.bati.cx[b] - S.bati.x[b], dy = S.bati.cy[b] - S.bati.y[b];
    const d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const p = Math.min(profondeur || 4, Math.max(1.4, d * .65));
    const a = k * 2.399963229728653;
    const lateral = Math.min(1.4, .3 * Math.sqrt(k)) * Math.sin(a);
    return [S.bati.x[b] + ux * p - uy * lateral,
            S.bati.y[b] + uy * p + ux * lateral];
  }

  function franchirHuis(h, u, b, m) {
    const r = u.ratissage;
    if (!r.passage || r.passage.b !== b)
      r.passage = { b, prochain:0, traverses:0 };
    const k = r.passage.traverses++;
    h.interieur = b; h.entreDepuis = S.temps; h.cible = null;
    h.pointInterieur = pointDerriereHuis(b, k, 4);
    h.etat = "fouille"; m.entrees++;
    if (r.phase === "approcher") r.phase = "fouille";
    r.passage.prochain = S.temps + .32;
  }

  function revelerRebelles(m, u, b) {
    if (!S.bati.occupation[b] || m.rebelles.has(b)) return;
    // C7 conditionne une seule découverte importante : le premier groupe
    // effectivement trouvé abrite le chef recherché. Les caches restent tirées
    // par le bâti ; seule l'identité nécessaire au test dépend de l'enquête
    // réellement menée, afin qu'une porte inaccessible ne rende pas le rapport
    // impossible par construction.
    if (m.batimentChef == null) m.batimentChef = b;
    const n = S.bati.occupation[b], ru = creerFormation("rebelles:" + m.id + ":" + b,
      "garde", "rebelles:" + m.id, "interieur");
    const ids = [];
    for (let i = 0; i < n; i++) {
      const chef = b === m.batimentChef && i === 0;
      const p = pointDerriereHuis(b, i + 3, 5.5);
      const h = homme("garde", p[0], p[1],
        { corps:"rebelles", chef:i === 0, poste:p,
          nom:chef ? "le chef rebelle" : null,
          role:chef ? "chef des rebelles" : "rebelle" });
      h.interieur = b; h.entreDepuis = S.temps; h.rebelle = true;
      h.rebelleChef = chef; h.batimentRebelle = b; h.etat = "tient";
      affecterFormation(h, ru, i, i === 0); S.hommes.push(h); ids.push(h.debugId);
    }
    m.rebelles.set(b, ids); m.groupesReveles++;
    // L'équipe de quatre découvre ; elle n'est pas condamnée à livrer seule un
    // combat contre sept hommes. Elle appelle juste assez de camarades pour
    // obtenir deux hommes d'avantage, tandis que le vintenar et le reste de la
    // vintaine continuent de tenir la rue.
    const r = u.ratissage;
    r.combatDepuis = S.temps;
    const disponibles = u.membres.filter((h) => h !== guideDe(u) && pese(h));
    const besoin = Math.min(disponibles.length, Math.max(4, n + 2));
    for (const h of disponibles) {
      if (r.fouilleurs.size >= besoin) break;
      r.fouilleurs.add(h.debugId);
    }
    faitRatissage(u, "ennemis_trouves", b, { nombre:n });
    noter("rebelles-trouves", S.bati.x[b], S.bati.y[b],
      { dit:{ batiment:b, usage:S.bati.usage[b], hommes:n, mission:m.id } });
  }

  function envoyerRapport(u, m, fait) {
    if (!m.commandement || !fait || m.rapportChefParti) return false;
    const porteur = u.membres.find((h) => h !== guideDe(u) && pese(h) && !h.rapportMission);
    if (!porteur) return false;
    porteur.rapportMission = { missionId:m.id, fait:Object.assign({}, fait),
      vers:m.commandement, unite:u.id, partiA:S.temps };
    porteur.cible = null;
    const b = fait.batiment;
    if (b != null && porteur.interieur === b) porteur.sortieBatiment = b;
    porteur.etat = "rapport";
    m.rapportChefParti = true; m.rapportChefFait=Object.assign({},fait);
    m.rapportPorteur=porteur.debugId; m.rapportsPartis++;
    noter("rapport-part", porteur.x, porteur.y,
      { dit:{ de:u.id, vers:m.commandement.nom || m.commandement.debugId,
              fait:fait.type, batiment:fait.batiment } });
    return true;
  }

  function courirRapport(h, dt) {
    const r = h.rapportMission, cible = r && r.vers;
    if (!r || !cible || cible.etat === "mort") { h.rapportMission = null; return; }
    penser(h, "porter le rapport au commandement",
      "nous avons identifié le chef rebelle", "rapport montant");
    if (!r.trace && S.J && S.voirie && h.interieur == null) {
      r.trace = S.J.chemin(S.voirie, [h.x, h.y], [cible.x, cible.y],
        "ratissage:rapport:" + r.missionId + ":" + r.unite);
      r.avance = 0;
    }
    if (Math.hypot(cible.x - h.x, cible.y - h.y) > 2) {
      if (r.trace && r.trace.long && r.avance < r.trace.long) {
        r.avance = Math.min(r.trace.long, r.avance + COURSE * dt);
        surLeRail(h, surTrace(r.trace, r.avance), 0);
      } else versLe(h, cible.x, cible.y, COURSE, dt);
      return;
    }
    cible.rapports.push(Object.assign({}, r.fait, { recuA:+S.temps.toFixed(1), porteur:h.debugId }));
    const m = S.ratissages.get(r.missionId);
    if (m) { m.rapportsArrives++; m.chefSignale = true; }
    noter("rapport-arrive", cible.x, cible.y,
      { dit:{ par:h.debugId, chef:cible.nom || cible.debugId,
              fait:r.fait.type, batiment:r.fait.batiment } });
    h.rapportMission = null; h.etat = "rassemble";
  }

  function menerRatissage(h, u, dt) {
    const r = u && u.ratissage, m = r && S.ratissages.get(r.missionId);
    if (!r || !m) return false;
    if (h.sortieBatiment != null) { sortirParHuis(h, dt); return true; }
    if (h.rapportMission) { courirRapport(h, dt); return true; }
    const chef = guideDe(u);
    if (!chef) return true;
    if (!r.secteur && r.phase !== "rendre-compte") choisirSecteur(u, m);
    if (!r.secteur) {
      h.cible = null;
      const chefUnite=guideDe(u);
      if(!r.repos){
        const poste=placeDeRalliementRdv(u,m);
        const ordre="Vintaine, ralliez le reste de la force au point de rencontre. Restez en formation.";
        donnerOrdreLocal(u,ordre,
          "notre secteur est terminé mais la vintaine n'a pas encore rejoint le corps");
        ordonnerFormation(u.id,{id:"ralliement:"+m.id+":"+u.id,
          nom:"le poste de ralliement",x:poste.x,y:poste.y},
          {mode:"marcher",source:"ordre-ratissage",texte:ordre});
        penser(h,"rejoindre le reste de la force",
          "notre secteur est terminé et nous devons rallier avant de nous mettre au repos",
          "ordre de ralliement");
        menerVintaineAuRdv(h,u,poste,dt);
        if(vintaineRalliee(u,poste)){
          r.repos=true;r.rallieA=+S.temps.toFixed(1);r.posteRdv={x:poste.x,y:poste.y};
          r.retourChef=null;
          donnerOrdreLocal(u,"Vintaine, repos au poste de ralliement. Chefs au point de rencontre.",
            "la vintaine a rejoint le corps et peut tenir sans suivre chaque mouvement de son chef");
        }
        return true;
      }
      const placeRdv = placeDeCommandementRdv(u, m);
      donnerOrdreLocal(u, "Vintaine, repos au poste de ralliement. Chefs au point de rencontre.",
        "la vintaine a rejoint le corps et aucun ennemi immédiat n'impose de la déplacer");
      if(h===chefUnite){
        penser(h,"rejoindre les autres chefs",
          "ma vintaine tient son dernier poste sans devoir me suivre","coordination entre pairs");
        menerChefAuRdv(h,u,m,placeRdv,dt);
      }else{
        penser(h,"tenir le poste au repos",
          "mon chef est parti rendre compte et aucun ennemi n'est à portée","ordre de repos");
        // Pas de cible métrique : l'homme conserve sa place présente. La
        // répulsion des corps continue, mais aucun ressort ne le recolle au chef.
      }
      return true;
    }
    if (r.courant == null && choisirMaison(u, m) == null) {
      if (r.engagement) r.engagement.actif = false;
      r.engagement = null; r.secteur = null; r.phase = "rendre-compte";
      return true;
    }
    const b = r.courant;
    const fouilleur = r.fouilleurs && r.fouilleurs.has(h.debugId);
    const chefFouille = u.membres.find((x) => x.debugId === r.chefFouille && pese(x)) ||
      u.membres.find((x) => r.fouilleurs && r.fouilleurs.has(x.debugId) && pese(x));
    // Le trajet de quartier a lui aussi un garde-fou. Le watchdog local ne
    // commence qu'à 45 m de la porte ; une route de voirie cassée pouvait donc
    // retenir la vintaine très loin pendant toute l'épreuve.
    if (h === chef && r.phase === "approcher" && r.marcheMaison) {
      const w = r.marcheMaison;
      if (Math.hypot(chef.x - w.x, chef.y - w.y) > .8) {
        w.x = chef.x; w.y = chef.y; w.avanceA = S.temps;
      }
      if (Math.hypot(S.bati.x[b] - chef.x, S.bati.y[b] - chef.y) > 12 &&
          S.temps - w.avanceA > 20) {
        faitRatissage(u, "maison_inaccessible", b,
          { conclusion:"la route vers cette porte n'a produit aucune progression" });
        r.courant = null; r.phase = "choisir-maison"; r.approche = null;
        return true;
      }
    }
    if (!fouilleur) {
      penser(h, "tenir les abords de la maison",
        "quatre des nôtres suffisent à fouiller pendant que nous gardons la rue",
        "couverture du ratissage");
      // Le gros suit jusqu'aux abords, mais ne se tasse jamais dans l'huis.
      const dRue = Math.hypot(S.bati.x[b] - h.x, S.bati.y[b] - h.y);
      if (dRue > 7) suivreGuideDirect(h, chef, S.bati.x[b], S.bati.y[b], MARCHE, dt);
      return true;
    }
    if (r.courant == null && r.quitterSecteurApres) {
      if (r.engagement) r.engagement.actif = false;
      r.engagement = null; r.secteur = null; r.quitterSecteurApres = false;
      r.phase = "choisir";
      return true;
    }
    if (h.interieur !== b) {
      const d = Math.hypot(S.bati.x[b] - h.x, S.bati.y[b] - h.y);
      const chefDedans = chefFouille && chefFouille.interieur === b;
      // Le chef doit réellement atteindre l'huis. Une fois qu'il l'a ouvert,
      // demander à chaque homme de tenir dans le même disque de 1,35 m crée un
      // bouchon insoluble : les corps se repoussent plus vite qu'ils ne peuvent
      // satisfaire la condition. Les suivants rejoignent donc la file à seize
      // mètres, puis le passage les absorbe un par un.
      if ((h === chefFouille && d > 2.5) ||
          (h !== chefFouille && (!chefDedans || d > FILE_HUIS))) {
        penser(h, "gagner la porte du bâtiment",
          "ma vintaine fouille ce secteur", "ordre de ratissage");
        // Après le passage du chef, sa position visible est au centre du bâti :
        // elle ne doit plus servir d'ancre de formation aux retardataires, sans
        // quoi ceux-ci visent le salon à travers la façade. Ils visent l'huis.
        if (h !== chefFouille && chefDedans && d <= 45) {
          h.passageEtroit = true;
          versLe(h, S.bati.x[b], S.bati.y[b], MARCHE, dt);
          h.passageEtroit = false;
        }
        else if (d <= 45) {
          const avance = approcherPorte(h, u, b, dt, chefFouille);
          if (avance === false && h === chefFouille) {
            faitRatissage(u, "maison_inaccessible", b,
              { conclusion:"la vintaine n'a trouvé aucun passage praticable vers cette porte" });
            r.courant = null; r.phase = "choisir-maison"; r.approche = null;
          }
        }
        else menerFormation(h, u.ordre.destination, MARCHE, dt);
        return true;
      }
      if (h !== chefFouille && S.temps < r.passage.prochain) {
        penser(h, "attendre mon tour au seuil",
          "le chef est entré et la porte ne laisse passer qu'un homme à la fois",
          "franchissement en file");
        return true;
      }
      franchirHuis(h, u, b, m);
    }
    if (r.phase !== "combat" && h.pointInterieur &&
        Math.hypot(h.pointInterieur[0] - h.x, h.pointInterieur[1] - h.y) > 1.25) {
      penser(h, "progresser dans la maison",
        "j'ai franchi le seuil et dois maintenant fouiller l'intérieur",
        "déplacement intérieur");
      versLe(h, h.pointInterieur[0], h.pointInterieur[1], MARCHE * .75, dt);
      return true;
    }
    if (r.phase === "combat") {
      donnerOrdreLocal(u, "Renfort dans le bâtiment. Le reste tient la rue.",
        "l'équipe de fouille a trouvé une résistance");
      const ennemi = ennemiProche(h, 8);
      penser(h, "réduire le groupe dans le bâtiment",
        "l'équipe de fouille a appelé du renfort après avoir trouvé des hommes armés",
        "combat de ratissage");
      if (ennemi) versLe(h, ennemi.x, ennemi.y, CHARGE, dt);
      return true;
    }
    penser(h, "fouiller l'intérieur",
      "nous avons franchi le seuil du " + (S.bati.usage[b] || "bâtiment"),
      "ordre de ratissage");
    if (h !== chefFouille) return true;
    const equipe = u.membres.filter((x) => r.fouilleurs && r.fouilleurs.has(x.debugId) && pese(x));
    const dedans = equipe.filter((x) => x.interieur === b).length;
    if (dedans < Math.min(3, equipe.length)) return true;
    r.progres += dt;
    if (r.progres < 7 + Math.min(8, (S.bati.val[b] || 2) * .12)) return true;
    if (S.bati.fouille[b] === 2) {
      m.doublons++; faitRatissage(u, "deja_fouillee", b);
      sortirDuBatiment(u, b); r.courant = null; r.phase = "choisir-maison"; return true;
    }
    // Une autre équipe a pu découvrir la résistance pendant que celle-ci
    // fouillait la même adresse. `3` signifie « combat en cours », jamais
    // « maison terminée » : la seconde équipe reste dedans et prête main-forte.
    if (S.bati.fouille[b] === 3) { r.phase = "combat"; return true; }
    if (S.bati.occupation[b]) {
      S.bati.fouille[b] = 3; revelerRebelles(m, u, b); r.phase = "combat";
      donnerOrdreLocal(u, "Renfort dans le " + (S.bati.usage[b] || "bâtiment") +
        " n°" + b + ". Le reste tient la rue.", "des hommes armés viennent d'y être découverts");
    } else {
      S.bati.fouille[b] = 2; m.batimentsClairs++;
      faitRatissage(u, "maison_claire", b, { conclusion:"aucun ennemi aperçu lors de la fouille" });
      sortirDuBatiment(u, b); r.courant = null; r.phase = "choisir-maison";
    }
    return true;
  }

  function suivreIssuesRatissage(m) {
    for (const [b, ids] of m.rebelles) {
      if (m.resolus.has(b)) continue;
      const xs = ids.map((id) => S.hommes.find((h) => h.debugId === id)).filter(Boolean);
      const encore = xs.filter((h) => pese(h));
      const unitesCombat = S.formations.filter((q) => q.ratissage && q.ratissage.courant === b);
      const uCombat = unitesCombat[0];
      const assaillants = unitesCombat.flatMap((q) =>
        q.membres.filter((h) => pese(h) && h.interieur === b));
      // Dans une pièce, un groupe dont les deux tiers sont à terre et qui reste
      // en nette infériorité ne livre pas un duel épuisé jusqu'au lendemain :
      // les survivants rendent leurs armes. C'est une issue locale, pas une
      // déroute du camp entier.
      const enlise = uCombat && uCombat.ratissage.combatDepuis != null &&
        S.temps - uCombat.ratissage.combatDepuis > 60 &&
        assaillants.length >= encore.length && assaillants.length >= 3;
      if (encore.length &&
          ((encore.length <= Math.max(2, Math.floor(xs.length * .35)) &&
            assaillants.length > encore.length) || enlise)) {
        for (const h of encore) { h.etat = "prisonnier"; h.cible = null; }
        noter("reddition-locale", S.bati.x[b], S.bati.y[b],
          { dit:{ batiment:b, prisonniers:encore.length, mission:m.id,
                  cause:enlise ? "encercles dans le bâtiment" : "groupe réduit" } });
      }
      if (xs.some((h) => pese(h))) continue;
      m.resolus.add(b); m.groupesVaincus++; S.bati.fouille[b] = 2;
      const u = uCombat;
      if (!u) continue;
      const f = faitRatissage(u, "groupe_vaincu", b, { nombre:xs.length });
      if (xs.some((h) => h.rebelleChef)) {
        m.chefIdentifie = true;
        const fc = faitRatissage(u, "chef_rebelle_identifie", b,
          { conclusion:"le chef rebelle était avec ce groupe" });
        envoyerRapport(u, m, fc);
      }
      for (const q of unitesCombat) {
        sortirDuBatiment(q, b); q.ratissage.courant = null;
        q.ratissage.phase = "choisir-maison";
      }
      noter("groupe-rebelle-vaincu", S.bati.x[b], S.bati.y[b],
        { dit:{ batiment:b, hommes:xs.length, chef:xs.some((h) => h.rebelleChef) || undefined } });
    }
  }

  function coordonnerRatissages() {
    for (const m of S.ratissages.values()) {
      // « Un messager est parti » n'est pas équivalent à « le commandement
      // sait ». Si le porteur tombe ou perd sa mission, un chef qui possède
      // encore le fait en envoie un autre au lieu de considérer la chaîne close.
      if(m.rapportChefParti&&m.rapportsArrives===0&&m.rapportChefFait){
        const p=S.hommes.find((h)=>h.debugId===m.rapportPorteur);
        if(!p||!p.rapportMission||!pese(p)){
          m.rapportChefParti=false;m.rapportPorteur=null;
          const u=m.unites.map((id)=>S.formations.find((q)=>q.id===id)).find((q)=>
            q&&q.ratissage&&[...q.ratissage.faits.values()].some((f)=>
              f.type==="chef_rebelle_identifie"));
          if(u)envoyerRapport(u,m,m.rapportChefFait);
        }
      }
      echangerEntrePairs(m);
      for (const id of m.unites) {
        const u = S.formations.find((q) => q.id === id);
        if (u && u.ratissage && !u.ratissage.secteur &&
            u.ratissage.phase !== "rendre-compte") choisirSecteur(u, m);
      }
      suivreIssuesRatissage(m);
    }
  }

  function ordonnerRatissage(spec) {
    if (!S.bati || !spec) return false;
    const id = spec.id || "ratissage:" + (++S.prochainRatissage);
    const zone = spec.zone || {};
    const cx = Number.isFinite(zone.x) ? zone.x : 0, cy = Number.isFinite(zone.y) ? zone.y : 0;
    const rayon = Number.isFinite(zone.rayon) ? zone.rayon : 90;
    const demandes = spec.batiments ? new Set(spec.batiments) : null;
    let bs = batiments().filter((b) => demandes ? demandes.has(b.id)
      : Math.hypot(b.x - cx, b.y - cy) <= rayon)
      .sort((a, b) => Math.hypot(a.x - cx, a.y - cy) - Math.hypot(b.x - cx, b.y - cy));
    if (spec.maxBatiments) bs = bs.slice(0, spec.maxBatiments);
    if (!bs.length) return false;
    const ids = new Set(spec.unites || []);
    const us = S.formations.filter((u) => ids.has(u.id));
    if (!us.length) return false;
    const x0 = Math.min(...bs.map((b) => b.x)), y0 = Math.min(...bs.map((b) => b.y));
    const m = {
      id, x0, y0, rdv:spec.rdv || { x:cx, y:cy }, batiments:bs.map((b) => b.id),
      secteurs:new Map(), unites:us.map((u) => u.id), rencontres:new Map(), rebelles:new Map(),
      resolus:new Set(), commandement:spec.commandement || null, communications:[], messages:0,
      formationRdv:null,
      ralliementRdv:null,
      contreOperations:spec.contreOperations || 0,
      entrees:0, batimentsClairs:0, doublons:0, engagementsPris:0, conflitsResolus:0,
      echanges:0, faitsTransmis:0, groupesPrevus:0, groupesReveles:0, groupesVaincus:0,
      rapportsPartis:0, rapportsArrives:0, rapportChefParti:false,
      rapportChefFait:null, rapportPorteur:null,
      chefIdentifie:false, chefSignale:false, batimentChef:null,
    };
    for (const q of bs) {
      S.bati.fouille[q.id] = 0; S.bati.occupation[q.id] = 0;
      const k = cleSecteur(m, q.id);
      if (!m.secteurs.has(k)) m.secteurs.set(k, []);
      m.secteurs.get(k).push(q.id);
    }
    const chances = spec.chances || {};
    const tirages = bs.map((q) => ({ q, p:chances[q.usage] ?? chances.defaut ?? .02,
      g:grainTexte(id + ":" + q.id) }));
    const touches = tirages.filter((x) => x.g < x.p)
      .sort((a, b) => a.g / Math.max(.001, a.p) - b.g / Math.max(.001, b.p));
    const min = Math.min(bs.length, spec.minGroupes || 0), max = spec.maxGroupes || Infinity;
    // Un exercice qui exige au moins N caches les répartit dans N secteurs
    // proches au lieu de tirer quatre portes contiguës. À l'intérieur de
    // chaque secteur, le rapport `tirage / chance(type)` décide toujours quel
    // bâtiment les abrite : une caserne reste beaucoup plus probable qu'un
    // taudis. Sans cette stratification, une cuisson pouvait cacher les quatre
    // groupes derrière la même rue et ne tester aucun ratissage.
    const selection = [], vus = new Set();
    if (min) {
      const secteurs = [...m.secteurs.entries()].map(([cle, qs]) => ({ cle, qs,
        d:Math.min(...qs.map((b) => Math.hypot(S.bati.x[b] - m.rdv.x, S.bati.y[b] - m.rdv.y))) }))
        .sort((a, b) => a.d - b.d);
      for (const s of secteurs.slice(0, min)) {
        const x = tirages.filter((t) => s.qs.includes(t.q.id))
          .sort((a, b) => a.g / Math.max(.001, a.p) - b.g / Math.max(.001, b.p))[0];
        if (x) { selection.push(x); vus.add(x.q.id); }
      }
    }
    for (const x of touches) if (!vus.has(x.q.id) && selection.length < max) {
      selection.push(x); vus.add(x.q.id);
    }
    const caches = selection.slice(0, max);
    for (const x of caches) {
      const n = 3 + Math.floor(grainTexte(id + ":groupe:" + x.q.id) * 5);
      S.bati.occupation[x.q.id] = n; m.groupesPrevus++;
    }
    m.batimentChef = null;
    for (const u of us) {
      const memoire = Commandement.memoire({ proprietaire:u.id, echelon:"vintaine", camp:u.camp });
      Commandement.recevoirOrdre(memoire,
        (spec.ordre && spec.ordre.texte) || "Fouillez ce quartier. Rendez compte de ce que vous trouvez.",
        S.temps);
      u.ratissage = { missionId:id, secteur:null, engagement:null, courant:null,
        phase:"choisir", progres:0, commandement:memoire,
        faits:memoire.faits, croyances:memoire.croyances, engagements:new Map(),
        ordre:(spec.ordre && spec.ordre.texte) || "Fouillez ce quartier. Rendez compte de ce que vous trouvez." };
      const chef = guideDe(u); if (chef) chef.commandement = memoire;
      u.ordre = { mode:"fouiller", destination:null, version:(u.ordre.version || 0) + 1,
        donneA:S.temps, ditA:S.temps, source:"ordre-ratissage", texte:u.ratissage.ordre };
    }
    S.ratissages.set(id, m);
    return true;
  }

  function rapportsRatissage() {
    return [...S.ratissages.values()].map((m) => ({
      id:m.id, batiments:m.batiments.length, secteurs:m.secteurs.size,
      entrees:m.entrees, batimentsClairs:m.batimentsClairs, doublons:m.doublons,
      engagementsPris:m.engagementsPris, conflitsResolus:m.conflitsResolus,
      echanges:m.echanges, faitsTransmis:m.faitsTransmis, messages:m.messages,
      communications:m.communications,
      groupesPrevus:m.groupesPrevus, groupesReveles:m.groupesReveles,
      groupesVaincus:m.groupesVaincus, contreOperations:m.contreOperations,
      chefIdentifie:m.chefIdentifie, chefSignale:m.chefSignale,
      rapportsPartis:m.rapportsPartis, rapportsArrives:m.rapportsArrives,
      congestion5:(() => {
        const ids=new Set(m.unites), xs=S.formations.filter((u) => ids.has(u.id))
          .flatMap((u) => u.membres).filter(pese);
        return xs.reduce((pic,h) => Math.max(pic, xs.filter((o) => o !== h &&
          Math.hypot(o.x-h.x,o.y-h.y) <= 5).length), 0);
      })(),
      congestionRdvEtrangere5:(() => {
        const ids=new Set(m.unites), us=S.formations.filter((u) => ids.has(u.id));
        const ns=new Set(us.map((u)=>u.n));
        const xs=us.flatMap((u)=>u.membres).filter((h)=>pese(h) &&
          Math.hypot(h.x-m.rdv.x,h.y-m.rdv.y)<=40);
        return xs.reduce((pic,h)=>Math.max(pic,xs.filter((o)=>o!==h &&
          ns.has(o.formation) && o.formation!==h.formation &&
          Math.hypot(o.x-h.x,o.y-h.y)<=5).length),0);
      })(),
      unitesAuRepos:m.unites.reduce((n,id) => {
        const u=S.formations.find((q)=>q.id===id);
        return n + (u && u.ratissage && u.ratissage.repos ? 1 : 0);
      },0),
      unitesRalliees:m.unites.reduce((n,id) => {
        const u=S.formations.find((q)=>q.id===id), r=u&&u.ratissage;
        return n + (r&&r.rallieA!=null ? 1 : 0);
      },0),
      effectifMission:m.unites.reduce((n,id) => {
        const u=S.formations.find((q)=>q.id===id), chef=guideDe(u);
        return n+(u ? u.membres.filter((h)=>h!==chef&&pese(h)).length : 0);
      },0),
      effectifRallie:m.unites.reduce((n,id) => {
        const u=S.formations.find((q)=>q.id===id), r=u&&u.ratissage, chef=guideDe(u);
        return n+(u&&r&&r.rallieA!=null ?
          u.membres.filter((h)=>h!==chef&&pese(h)).length : 0);
      },0),
      troupesRalliees:(() => {
        let n=0;
        for(const id of m.unites){
          const u=S.formations.find((q)=>q.id===id), r=u&&u.ratissage;
          if(!u||!r||!r.posteRdv)continue;
          const chef=guideDe(u);
          n+=u.membres.filter((h)=>h!==chef&&pese(h)&&
            Math.hypot(h.x-r.posteRdv.x,h.y-r.posteRdv.y)<=14).length;
        }
        return n;
      })(),
      troupesAuRdv:(() => {
        const ids=new Set(m.unites);
        return S.formations.filter((u)=>ids.has(u.id)).reduce((n,u) => {
          const chef=guideDe(u);
          return n + u.membres.filter((h)=>h!==chef && pese(h) &&
            Math.hypot(h.x-m.rdv.x,h.y-m.rdv.y)<=8).length;
        },0);
      })(),
      chefsEnPlace:(() => {
        if(!m.formationRdv)return 0;
        let n=0;
        for(const [id,p] of m.formationRdv){
          const u=S.formations.find((q)=>q.id===id), h=guideDe(u);
          if(h&&Math.hypot(h.x-p.x,h.y-p.y)<=2)n++;
        }
        return n;
      })(),
      formationRdv:m.formationRdv ? [...m.formationRdv.entries()].map(([unite,p]) =>
        (() => { const u=S.formations.find((q)=>q.id===unite), h=guideDe(u); return {
          unite, x:+p.x.toFixed(1), y:+p.y.toFixed(1),
          chefX:h ? +h.x.toFixed(1) : null, chefY:h ? +h.y.toFixed(1) : null,
          reste:h ? +Math.hypot(h.x-p.x,h.y-p.y).toFixed(1) : null,
        }; })())
        : [],
      unites:m.unites.map((id) => {
        const u = S.formations.find((q) => q.id === id), r = u && u.ratissage;
        const cf = u && r && u.membres.find((h) => h.debugId === r.chefFouille);
        const chef=u&&guideDe(u), pr=m.ralliementRdv&&m.ralliementRdv.get(id);
        const vivants=u ? u.membres.filter(pese) : [];
        return { id, secteur:r && r.secteur, courant:r && r.courant,
          phase:r && r.phase, repos:!!(r && r.repos), rallieA:r&&r.rallieA,
          posteRdv:r&&r.posteRdv,
          ralliement:pr ? { reste:chef ? +Math.hypot(chef.x-pr.x,chef.y-pr.y).toFixed(1) : null,
            cohesion:chef&&vivants.length ? +((vivants.filter((h)=>
              Math.hypot(h.x-chef.x,h.y-chef.y)<=12).length/vivants.length).toFixed(2)) : 0,
            route:u&&u.cadre ? { s:+(u.cadre.s||0).toFixed(1),
              long:u.cadre.trace ? +u.cadre.trace.long.toFixed(1) : null,
              finition:u.cadre.finition&&u.cadre.finition.pts ?
                u.cadre.finition.i+"/"+u.cadre.finition.pts.length : null,
              calculs:u.cadre.calculs } : null }
            : null,
          dedans:u && r && r.courant != null
            ? u.membres.filter((h) => pese(h) && h.interieur === r.courant).length : 0,
          faits:r ? r.faits.size : 0, engagements:r ? r.engagements.size : 0,
          situation:u ? estimerSituation(u) : null,
          croyances:r ? [...r.croyances.values()].map((c) => Object.assign({}, c,
            { confianceActuelle:+confianceActuelle(c).toFixed(2) })) : [],
          approche:r && r.approche ? { points:r.approche.pts ? r.approche.pts.length : 0,
            index:r.approche.i,
            prochain:r.approche.pts && r.approche.pts[r.approche.i] || null } : null,
          passage:r && r.passage ? { traverses:r.passage.traverses,
            prochain:+r.passage.prochain.toFixed(1) } : null,
          chefFouille:cf ? { id:cf.debugId, x:+cf.x.toFixed(1), y:+cf.y.toFixed(1),
            interieur:cf.interieur, cible:cf.pointInterieur,
            reste:cf.pointInterieur ? +Math.hypot(cf.pointInterieur[0]-cf.x,
              cf.pointInterieur[1]-cf.y).toFixed(1) : null } : null,
          ordre:u ? ordreLitteral(u) : null,
          ordreSuperieur:r && r.ordre, raisonOrdre:r && r.raisonOrdre };
      }),
    }));
  }

  function rapportsCommandement() {
    const xs = [];
    for (const dep of S.deploiements.values()) {
      if (!dep.commandants) continue;
      for (const [h, c] of dep.commandants) {
        const carte = carteCommandant(h.debugId, c.champ);
        xs.push({
          deploiement:dep.id, id:h.debugId, nom:h.nom || null, camp:h.camp,
          role:c.role, echelon:c.memoire.echelon, corps:c.corps || null,
          aile:c.aile == null ? null : c.aile,
          ordre:c.memoire.ordre && c.memoire.ordre.texte,
          ordreRecuA:c.memoire.ordre && c.memoire.ordre.recuA,
          faits:c.memoire.faits.size, estimation:c.estimation ||
            Commandement.estimation(c.memoire, 0, S.temps),
          croyances:[...c.memoire.croyances.values()].map((q) => Object.assign({}, q,
            { confianceActuelle:+Commandement.confiance(q, S.temps).toFixed(2) })),
          communications:c.memoire.communications.length,
          carte:carte ? { resume:carte.resume, noeuds:carte.noeuds,
            liens:carte.liens } : null,
        });
      }
    }
    return xs;
  }

  async function amorcer() {
    try {
      await preparer();
      // ON NE DRESSE RIEN TANT QUE PERSONNE N'A RIEN DEMANDÉ. L'armée était
      // rangée dès l'ouverture de l'échelle : trois cents points rouges devant
      // la porte de la Gadoue à tout moment, sur un plan qu'on avait ouvert
      // pour chercher une rue. Une bataille se convoque — c'est le bouton qui
      // la fait exister, pas le fait de regarder la ville.
      if (!S.boucle) S.boucle = requestAnimationFrame(image);
      if (window.ResizeObserver) new ResizeObserver(ajuster).observe(S.hote);
      return true;
    } catch (e) {
      console.warn("bataille2d : pas de bataille ici —", e);
      S.rate = e;
      if (S.barre) { S.barre.remove(); S.barre = null; }
      if (S.toile) { S.toile.remove(); S.toile = null; }
      return false;
    }
  }

  // ON NE REPEINT PAS DEUX MILLE HOMMES PAR MOUVEMENT DE SOURIS. `carte-ville`
  // appelle `cadrer()` — donc ceci — depuis `pointermove`, qui n'est pas cadencé
  // sur l'écran : un trackpad à 120 Hz ou une souris à 1000 Hz fait plusieurs
  // repeints complets par image affichée, tous jetés sauf le dernier. Le budget
  // d'image saute, des images tombent, et la carte paraît trembler AU MOMENT
  // PRÉCIS où on la tire — c'est-à-dire au seul moment où on la regarde bouger.
  //
  // Le retaillage, lui, reste immédiat : il touche `toile.width`, et une toile
  // à la mauvaise taille est fausse tout de suite, pas à la prochaine image.
  // Seul le DESSIN se laisse attendre — et s'il y a une boucle qui tourne, elle
  // le fera dans la milliseconde, sans qu'on ait rien à programmer. On ne peint
  // ici que si personne d'autre ne va le faire : à l'arrêt, il n'y a pas de
  // boucle, et un recadrage qui ne repeindrait pas laisserait l'armée en place
  // pendant qu'on tire le plan sous elle.
  function recadrer() { ajuster(); if (!S.boucle) peindre(); }
  function arreter() {
    if (S.boucle) cancelAnimationFrame(S.boucle);
    S.boucle = 0; S.marche = false;
  }

  /** De quoi lire la bataille depuis la console, sans la regarder. */
  function etat() {
    if (!S.hommes.length) return { dressee: false, temps: 0, marche: false };
    const par = {};
    for (const h of S.hommes) par[h.etat] = (par[h.etat] || 0) + 1;
    const combattants = S.hommes.filter((h) => !h.tete && !h.roi && !h.hors &&
      h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "rentre");
    const moyenne = (f) => combattants.length
      ? combattants.reduce((s, h) => s + f(h), 0) / combattants.length : 0;
    const durees = combattants.flatMap((h) => {
      const d = h.enMesure ? Math.max(0, S.temps - h.mesureDepuis) : h.dernierBout;
      return d > 0 ? [d] : [];
    }).sort((a, b) => a - b);
    const quantile = (q) => durees.length
      ? durees[Math.min(durees.length - 1, Math.floor((durees.length - 1) * q))] : 0;
    const dynamique = {
      combattants: combattants.length,
      enMesure: combattants.filter((h) => h.enMesure).length,
      frappeursRecents: combattants.filter((h) => S.temps - h.dernierCoup <= 5).length,
      coupsTentes: combattants.reduce((s, h) => s + h.coupsTentes, 0),
      coupsPortes: combattants.reduce((s, h) => s + h.coupsPortes, 0),
      bouts: combattants.reduce((s, h) => s + h.boutsMesure, 0),
      hommesMultiBouts: combattants.filter((h) => h.boutsMesure >= 2).length,
      boutMedian: +quantile(0.5).toFixed(1), boutP90: +quantile(0.9).toFixed(1),
      sangFroidMoyen: +moyenne((h) => h.l1 ? h.l1.sangFroid : 1).toFixed(2),
      expositionMoyenne: +moyenne((h) => h.l1 ? h.l1.exposition : 0).toFixed(2),
      chargeNerveuseMoyenne: +moyenne((h) => h.l1 ? h.l1.chargeNerveuse : 0).toFixed(2),
      sortieFermee: combattants.filter((h) => h.degagement < 0.2).length,
      presseForte: combattants.filter((h) => (h.presse || 0) >= 4).length,
    };
    // COMBIEN, ET POUR QUELLE RAISON. `par` compte les états, et un état ne dit
    // rien : « forme » recouvre la réserve qu'on a laissée en arrière, l'homme
    // qui attend sa place au seuil et celui dont le repère a fondu. Le relevé
    // par branche est la seule façon de répondre à « pourquoi seulement un
    // cinquième de ce corps avance-t-il », sans pointer les hommes un par un.
    // On coupe le complément chiffré des libellés — « à 40 pas » — sinon
    // chaque homme fait sa propre ligne et l'on ne compte plus rien.
    const branches = {};
    for (const h of S.hommes) {
      if (h.camp !== "assaut" || h.tete || h.hors) continue;
      if (h.etat === "mort" || h.etat === "deroute") continue;
      const b = (h.branche || "sans branche").split(/ (?:à|—) /)[0];
      branches[b] = (branches[b] || 0) + 1;
    }
    return {
      temps: +S.temps.toFixed(1), marche: S.marche,
      // Rangé du plus nombreux au moins nombreux : la première ligne est ce
      // que fait l'armée, quoi qu'on ait cru lui ordonner.
      branches: Object.fromEntries(
        Object.entries(branches).sort((a, b) => b[1] - a[1])),
      porte: S.entree && S.entree.nom, objectif: S.objectif && S.objectif.nom,
      verrou: S.verrou && { etat: S.verrou.etat, pv: Math.round(S.verrou.pv) },
      // Les quatre portes, chacune avec son compte : c'est le relevé qui dit
      // laquelle a cédé la première, et c'est de là que part tout le reste.
      // `par` dit COMMENT elle s'est ouverte, et c'est la seule chose qu'on
      // veuille savoir d'une porte : une qu'on enfonce a coûté trois mille
      // points et une demi-heure de morts sur un seuil, une qu'on ouvre n'a
      // rien coûté du tout.
      portes: S.verrous.map((v) => ({ nom: v.nom, etat: v.etat,
                                    pv: Math.round(v.pv),
                                    par: v.par || (v.etat === "ouvert" ? "hache" : null) })),
      // CE QUI A ARRÊTÉ LA NUIT, s'il y a lieu — et c'est le seul champ du
      // relevé qui puisse dire que la bataille n'a pas eu d'issue militaire.
      arret: S.arret,
      // Le Donjon : à quelle heure il a su, et lequel des deux lords a gagné.
      // L'écart entre `averti` et la porte qui cède est le fait le plus cher de
      // toute la nuit.
      donjon: { averti: S.conseil.averti || null, tranche: S.conseil.tranche,
                tenir: +S.conseil.tenir.toFixed(1),
                ouvrir: +S.conseil.ouvrir.toFixed(1),
                anneau: S.anneauOuvert ? "ouvert" : "tenu" },
      assaut: compte.a, garde: compte.d, morts: compte.morts,
      blesses: compte.blesses, fuyards: compte.fuyards,
      contreCharges: compte.contreCharges, etats: par,
      dynamique,
      faits: S.annales.length,
      // LE SAC, EN QUATRE CHIFFRES. C'est par eux qu'on le retiendra : combien
      // de portes forcées, combien de toits en feu, et ce que l'armée emporte.
      sac: S.bati ? { maisons: S.bati.n, forcees: S.bati.forcees,
                    brulees: S.bati.brulees, butin: Math.round(S.bati.butin) } : null,
      // La ville : combien ont peur, et dans quel état. C'est le seul relevé
      // qui dise si la couche de peur fait quelque chose — on ne la voit
      // autrement qu'en regardant une rue se vider.
      ville: (() => {
        const v = { paniques: S.paniques.length, foyers: S.foyers.length };
        for (const p of S.paniques) v[p.etat] = (v[p.etat] || 0) + 1;
        return v;
      })(),
      sangFroidMoyen: dynamique.sangFroidMoyen,
    };
  }

  // AVANCER SANS REGARDER. `requestAnimationFrame` ne bat pas dans un onglet
  // caché — ce qui est la bonne politique pour une lunette, et une impasse
  // pour l'éprouver : on ne va pas vérifier une machine à états à l'œil, en
  // temps réel, quatre minutes durant. `pas(90)` joue quatre-vingt-dix
  // secondes de bataille d'un trait et rend l'état. C'est aussi ce qui permet
  // de rejouer deux fois la même et de comparer.
  function pas(secondes) {
    if (!S.hommes.length) rejouer();
    const n = Math.round((secondes || 1) / PAS);
    // `avancer` consomme exactement un pas quand on lui en donne un : le
    // reliquat repart à zéro à chaque tour, et l'on ne dépend pas de l'horloge
    // réelle.
    for (let i = 0; i < n; i++) avancer(PAS);
    return etat();
  }

  // Les habitants qu'on a pris en charge, à plat. C'est le seul moyen de
  // VÉRIFIER que la peur passe par les rues au lieu de traverser les murs :
  // sans ce relevé, on ne peut que regarder des points et se persuader.
  const peur = () => S.paniques.map((p) => ({ x: p.x, y: p.y, etat: p.etat,
                                            surRue: p.surRue, contre: p.contre }));

  // Les corps eux-mêmes, tels quels — c'est ce que le four échantillonne à
  // chaque pas. On rend le tableau VIVANT et non une copie : le four le
  // parcourt cent mille fois, et recopier trois cents objets à chaque pas
  // coûterait plus cher que la simulation.
  const troupe = () => S.hommes;

  // LES RAILS QUE SUIVENT LES CHEFS. Un quart du chemin passe par des
  // ruelles, que le plan n'imprime pas au-delà de deux mètres par pixel : sans
  // ce relevé, on voit une colonne marcher sur du vide et l'on croit à un
  // décalage entre la carte et le calcul. Les escouades partagent leur A*, il
  // n'y a donc qu'une poignée de tracés distincts.
  const chemins = () => {
    const vus = new Set(), l = [];
    for (const u of S.formations) {
      const tr = u.cadre && u.cadre.trace;
      if (!tr || vus.has(tr)) continue;
      vus.add(tr);
      l.push(tr.pts.map((p) => [Math.round(p[0] * 10) / 10,
                                     Math.round(p[1] * 10) / 10]));
    }
    return l;
  };

  // LE ROSTER ENTRE ENFIN DANS LA BATAILLE. Cette fonction ne donne aucun
  // ordre et ne connaît aucune tactique : elle matérialise seulement la
  // composition d'un type dans une unité déjà existante. Les scénarios, puis
  // l'organisation de l'armée, peuvent donc parler de piquiers et de cavaliers
  // sans que ces mots restent des étiquettes de menu.
  function equiperUnite(id, typeId) {
    const Roster = window.BatailleRoster;
    const type = Roster && Roster.TYPES.find((x) => x.id === typeId);
    const u = S.formations.find((x) => x.id === id);
    if (!type || !u) return null;
    const xs = u.membres.filter((h) => !h.tete && !h.hors);
    const file = [];
    for (const [metier, n] of Object.entries(type.composition || {}))
      for (let i = 0; i < n; i++) file.push(metier);
    const chef = guideDe(u);
    const sansChef = file.filter((m, i) => !(m === "vintenar" &&
      i === file.indexOf("vintenar")));
    let rang = 0;
    for (const h of xs) {
      const metier = h === chef && type.composition.vintenar
        ? "vintenar"
        : (sansChef.length ? sansChef[Math.min(sansChef.length - 1,
            Math.floor(rang++ * sansChef.length / Math.max(1, xs.length - (chef ? 1 : 0))))]
          : file[0]);
      const m = Roster.METIERS[metier] || {};
      h.metier = metier || null;
      h.typeTroupe = type.id;
      h.arme = ARMES[m.arme] || ARME_NUE;
      h.montureCombat = !!(m.monte || (type.capacites && type.capacites.monte));
      if (h.montureCombat) h.monte = true;
    }
    u.typeTroupe = type.id;
    u.capacites = Object.assign({}, type.capacites || {});
    return { id:u.id, type:type.id, hommes:xs.length,
             montes:xs.filter((h) => h.montureCombat).length,
             piquiers:xs.filter((h) => h.arme === ARMES.pique).length };
  }

  // La formation rendue comme fait observable : qui mène, où l'unité va,
  // combien de routes elle a réellement demandées et combien des siens sont
  // encore à portée de leur propre chef. C'est la sonde qui empêche « pas un
  // A* par homme » de rester un commentaire invérifiable.
  const unites = () => S.formations.map((u) => {
    const chef = guideDe(u);
    const vivants = u.membres.filter((h) => h.etat !== "mort" &&
      h.etat !== "blesse" && h.etat !== "deroute");
    const distances = chef ? vivants.filter((h) => h !== chef)
      .map((h) => Math.hypot(h.x - chef.x, h.y - chef.y)).sort((a, b) => a - b) : [];
    const proches = distances.filter((d) => d <= 12).length;
    return {
      id: u.id, camp: u.camp, parent: u.parent,
      typeTroupe: u.typeTroupe || null,
      capacites: Object.assign({}, u.capacites || {}),
      chef: chef ? (chef.nom || (u.camp === "garde" ? "chef du poste" : "vintenar")) : null,
      // La position et l'identité du chef font partie du relevé de commande :
      // sans elles, une épreuve peut constater qu'un ordre existe mais pas que
      // quelqu'un l'a réellement conduit, ni qu'un successeur l'a repris.
      chefDebugId: chef ? chef.debugId : null,
      x: chef ? chef.x : null, y: chef ? chef.y : null,
      rangParent: u.rangParent,
      routeClef: u.cadre.clef || null,
      progressionRoute: Number.isFinite(u.cadre.s) ? u.cadre.s : null,
      membres: u.membres.length, debout: vivants.length,
      destination: u.ordre.destination ? u.ordre.destination.nom : null,
      destinationX: u.ordre.destination ? u.ordre.destination.x : null,
      destinationY: u.ordre.destination ? u.ordre.destination.y : null,
      mode: u.ordre.mode, forme: u.cadre.forme,
      doctrine: u.doctrine ? u.doctrine.id : null,
      doctrineActifs: u.membres.filter((h) => h.doctrineActive).length,
      doctrineOntAgi: u.membres.filter((h) => h.doctrineAgi).length,
      phaseRalliement: u.cadre.ralliement ? u.cadre.ralliement.phase : null,
      placeRalliement: u.cadre.ralliement ? {
        x: u.cadre.ralliement.x, y: u.cadre.ralliement.y,
        corps: u.cadre.ralliement.corps, aile: u.cadre.ralliement.aile,
        rang: u.cadre.ralliement.rang,
        ligneSol: u.cadre.ralliement.ligneSol,
        sRuban: u.cadre.ralliement.sRuban,
        libre: solConnu() ? libreEn(u.cadre.ralliement.x,
                                   u.cadre.ralliement.y) : null,
      } : null,
      ordreLitteral: ordreLitteral(u),
      ordreDitMaintenant: ordreEnTrainDEtreDit(u),
      calculsAStar: u.cadre.calculs,
      cohesion: distances.length ? proches / distances.length : (chef ? 1 : 0),
      distanceP90: distances.length ? distances[Math.floor((distances.length - 1) * .9)] : 0,
      sansChefDepuis: u.cadre.perduA === null ? null : S.temps - u.cadre.perduA,
      successionDans: u.cadre.reprendA === null ? null
        : Math.max(0, u.cadre.reprendA - S.temps),
    };
  });

  // Une marque doit rester enregistrable après une longue simulation. Le
  // screenshot et l'état courant sont petits ; la seule donnée naturellement
  // sans borne est la chronologie perceptive. On la borne en OCTETS et non en
  // nombre d'items, car une perception de commandant peut être bien plus
  // bavarde qu'une perception de piquier. La marche arrière est volontaire :
  // quand il faut choisir, les secondes qui précèdent le clic survivent.
  const MAX_OCTETS_HISTORIQUE_MARQUE = 512 * 1024;

  function octetsUtf8(texte) {
    if (typeof TextEncoder !== "undefined")
      return new TextEncoder().encode(texte).length;
    // Repli pour les vieux bancs JS sans TextEncoder. `encodeURIComponent`
    // donne un triplet `%XX` par octet non ASCII.
    return encodeURIComponent(texte).replace(/%[0-9A-F]{2}|./g, "x").length;
  }

  function queuePerceptionsPourMarque(h) {
    const source = Array.isArray(h && h.perceptions) ? h.perceptions : [];
    let debut = source.length, octets = 2; // les crochets JSON
    while (debut > 0) {
      const taille = octetsUtf8(JSON.stringify(source[debut - 1])) +
        (debut < source.length ? 1 : 0);
      // Même une perception anormalement grosse ne peut faire disparaître
      // l'instant final : on en garde toujours au moins une.
      if (octets + taille > MAX_OCTETS_HISTORIQUE_MARQUE &&
          debut < source.length) break;
      octets += taille; debut--;
    }
    const valeurs = source.slice(debut);
    const oublieesMemoire = Math.max(0, Number(h && h.perceptionsOubliees) || 0);
    const total = oublieesMemoire + source.length;
    return {
      valeurs,
      meta: {
        politique: "fin-conservee",
        total,
        conserve: valeurs.length,
        omis: oublieesMemoire + debut,
        octets_json: octets,
        debut_conserve_s: valeurs.length ? valeurs[0].temps : null,
        fin_conservee_s: valeurs.length ? valeurs[valeurs.length - 1].temps : null,
      },
    };
  }

  // LE DOSSIER D'UN HOMME, calculé seulement quand le joueur le marque. Les
  // rayons et les plus proches coûteraient trop cher dans la boucle ; une fois
  // au clic, leur coût est négligeable et leur valeur de diagnostic immense.
  function diagnostic(debugId) {
    const h = S.hommes.find((x) => x.debugId === debugId);
    if (!h) return null;
    const u = formationDe(h), chef = guideDe(u);
    const a = ailleDe(h), e = a ? S.escouades[h.escouade] : null;
    const rayons = [5, 12, 25, 50].map((rayon) => {
      const xs = S.hommes.filter((o) => o !== h &&
        Math.hypot(o.x - h.x, o.y - h.y) <= rayon);
      return {
        rayon_m: rayon, total: xs.length,
        allies: xs.filter((o) => o.camp === h.camp && pese(o)).length,
        ennemis: xs.filter((o) => o.camp !== h.camp && pese(o)).length,
        blesses: xs.filter((o) => o.etat === "blesse").length,
        morts: xs.filter((o) => o.etat === "mort").length,
        en_melee: xs.filter((o) => o.etat === "melee" || o.etat === "assaut").length,
        en_repli: xs.filter((o) => o.etat === "repli" || o.etat === "deroute").length,
      };
    });
    const proches = S.hommes.filter((o) => o !== h).map((o) => ({
      id: o.debugId, nom: o.nom || null, camp: o.camp, etat: o.etat,
      distance_m: +Math.hypot(o.x - h.x, o.y - h.y).toFixed(1),
      action: o.pensee && o.pensee.action,
      systeme: o.pensee && o.pensee.systeme,
    })).sort((x, y) => x.distance_m - y.distance_m).slice(0, 16);
    const distanceChef = chef && chef !== h
      ? Math.hypot(chef.x - h.x, chef.y - h.y) : 0;
    const proches12 = rayons.find((r) => r.rayon_m === 12);
    const alertes = [];
    if (proches12.ennemis > proches12.allies + 1) alertes.push("infériorité locale à 12 m");
    if (!proches12.allies) alertes.push("aucun allié vivant à 12 m");
    if (distanceChef > 18) alertes.push("séparé de son chef de plus de 18 m");
    if (h.souffle < .3) alertes.push("souffle sous 0,30");
    if (h.pv < h.pvMax * SEUIL_RECUL) alertes.push("blessure sous le seuil de recul");
    if (h.l1 && h.pensee && h.l1.jambes !== "planté" &&
        h.pensee.systeme !== "corps · couche 1")
      alertes.push("le corps propose « " + h.l1.jambes + " », un autre système conduit");
    let chargeCommandement = null;
    for (const dep of S.deploiements.values()) if (dep.commandants && dep.commandants.has(h)) {
      chargeCommandement = dep.commandants.get(h); break;
    }
    const memoireChef = h.commandement;
    const historique = queuePerceptionsPourMarque(h);
    return {
      format: "marque-bataille/v1",
      calcule_a: new Date().toISOString(),
      temps_bataille_s: +S.temps.toFixed(2),
      combattant: {
        id: h.debugId, nom: h.nom || null, role: h.role || null,
        camp: h.camp, corps: h.corps || null, etat: h.etat,
        position: { x: +h.x.toFixed(1), y: +h.y.toFixed(1) },
        arme: h.arme && h.arme.nom,
        metier: h.metier || null, type_troupe: h.typeTroupe || null,
        monte_combat: !!h.montureCombat,
        pensee: h.pensee && Object.assign({}, h.pensee,
          { duree_s: +(S.temps - h.pensee.depuis).toFixed(1) }),
        ordre: e ? dire(e.ordre) : null,
        ordre_litteral: u ? ordreLitteral(u) : null,
        traits: { trempe: +h.trempe.toFixed(2), oeil: +(1 / h.vivacite).toFixed(2),
                  fond: +h.fond.toFixed(2), dressage: +h.dressage.toFixed(2),
                  vecu: +h.vecu.toFixed(2) },
        physique: { pv: +Math.max(0, h.pv).toFixed(1), pv_max: +h.pvMax.toFixed(1),
                    souffle: +h.souffle.toFixed(2), presse: +(h.presse || 0).toFixed(1) },
        circulation: h.cedePour ? { dernier_passage_s:+h.cedePassageA.toFixed(2),
          pour:h.cedePour, chef:h.cedePourChef,
          distance_totale_m:+h.cedeDistance.toFixed(2) } : null,
        couches: {
          corps: h.l1 ? { jambes: h.l1.jambes, bras: h.l1.bras,
            phrase: h.l1.phrase, sang_froid: +h.l1.sangFroid.toFixed(2),
            exposition: +h.l1.exposition.toFixed(2),
            charge: +h.l1.chargeNerveuse.toFixed(2), emprise: +h.l1.emprise.toFixed(2) } : null,
          reflexion: h.l2 ? { idee: h.l2.idee, tient: +h.l2.tient.toFixed(2),
            attend: +h.l2.attend.toFixed(2), appui: +h.l2.appui.toFixed(2),
            degage: h.l2.degage == null ? null : +h.l2.degage.toFixed(2) } : null,
          ordre: h.l3 ? { maniere: h.l3.maniere, place: +h.l3.place.toFixed(2),
            serre: +h.l3.serre.toFixed(2), hate: +h.l3.hate.toFixed(2),
            lettre: +h.l3.lettre.toFixed(2) } : null,
          envie: h.l4 == null ? null : +h.l4.toFixed(2),
          arbitre: h.conduit ? { jambes: h.conduit, bras: h.conduitBras,
                                  phrase: h.conduitPhrase } : null,
        },
      },
      unite: u ? {
        id: u.id, parent: u.parent, chef: chef && (chef.nom || chef.debugId),
        distance_chef_m: +distanceChef.toFixed(1),
        destination: u.ordre.destination && u.ordre.destination.nom,
        ordre_litteral: ordreLitteral(u), calculs_a_star: u.cadre.calculs,
        ralliement: u.cadre.ralliement ? {
          phase: u.cadre.ralliement.phase,
          rang: u.cadre.ralliement.rang,
          ligne_sol: u.cadre.ralliement.ligneSol,
          place: { x:+u.cadre.ralliement.x.toFixed(1),
                   y:+u.cadre.ralliement.y.toFixed(1) },
          distance_place_m: chef ? +Math.hypot(chef.x-u.cadre.ralliement.x,
            chef.y-u.cadre.ralliement.y).toFixed(1) : null,
          route: u.cadre.ralliement.routeMasque ? {
            directe: !!u.cadre.ralliement.routeMasque.direct,
            progression_m: +(u.cadre.ralliement.routeMasque.s || 0).toFixed(1),
            longueur_m: u.cadre.ralliement.routeMasque.trace
              ? +u.cadre.ralliement.routeMasque.trace.long.toFixed(1) : null,
            premiers_jalons: u.cadre.ralliement.routeMasque.trace
              ? u.cadre.ralliement.routeMasque.trace.pts.slice(0,6)
                  .map((p)=>[+p[0].toFixed(1),+p[1].toFixed(1)]) : null,
            recalculee: u.cadre.ralliement.routeMasque.recalculs || 0,
            tentatives: u.cadre.ralliement.routeMasque.tentatives || 0,
            dernier_pas_m: +(u.cadre.ralliement.routeMasque.dernierPas || 0).toFixed(3),
            dernier_but: u.cadre.ralliement.routeMasque.dernierBut
              ? u.cadre.ralliement.routeMasque.dernierBut.map((v)=>+v.toFixed(1)) : null,
            sans_progres_depuis_s: +(S.temps-
              u.cadre.ralliement.routeMasque.avanceA).toFixed(1),
          } : null,
        } : null,
      } : null,
      commandement: memoireChef ? {
        echelon:memoireChef.echelon,
        ordre_recu:memoireChef.ordre && memoireChef.ordre.texte,
        estimation:chargeCommandement ? chargeCommandement.estimation
          : (u && u.ratissage ? estimerSituation(u) : null),
        croyances:[...memoireChef.croyances.values()].map((c) => Object.assign({}, c,
          { confiance_actuelle:+Commandement.confiance(c, S.temps).toFixed(2) })),
        communications:memoireChef.communications.slice(),
        carte:carteCommandant(h.debugId),
      } : null,
      voisinage: { rayons, plus_proches: proches },
      alertes,
      historique_perceptions: historique.valeurs,
      historique_perceptions_meta: historique.meta,
      bataille: etat(),
    };
  }

  // CE QUE LE MJ LIRA. On rend le tableau tel quel, dans l'ordre où les faits
  // sont arrivés — c'est un document, pas une vue : on ne le trie pas, on ne
  // le filtre pas, et surtout on ne le résume pas ici. Résumer est le travail
  // de celui qui raconte.
  const faits = () => S.annales;

  // ---- L'ALENTOUR — CE QUE LA RUE TENAIT À CETTE MINUTE-LÀ ------------------
  // À NE PAS CONFONDRE AVEC `temoins`, qui est au-dessus et qui répond à une
  // autre question. Les deux sont utiles et aucun ne remplace l'autre :
  //
  //   `temoins`  — DES NOMS. Ceux que la couche de peur a pris en charge à
  //                moins de cinquante mètres : des gens qui étaient dehors,
  //                qui ont vu, et qu'on peut aller trouver. Résolu au moment du
  //                fait, pour rien, en balayant la liste des paniqués.
  //   `alentour` — UN ÉTAT DE RUE. Tout ce que le quartier contenait à cette
  //                minute, panique ou pas : combien dans la rue, de quels
  //                métiers, combien derrière une porte et LAQUELLE. C'est ce
  //                qui manque au premier — il ne voit que les affolés, donc il
  //                ne voit rien du tout d'un fait qui tombe hors de la peur, et
  //                il ne dit jamais par quelle porte aller frapper.
  //
  // ON NE LE RÉSOUT PAS AU MOMENT DU FAIT, et c'est le point de conception : un
  // `noter()` qui appellerait la foule coûterait un balayage de cellules par
  // blessé — des milliers, à neuf mille cinq cents hommes, en plein pas de
  // simulation. Les faits portent déjà leurs mètres et leur seconde ; la
  // question se repose donc APRÈS, une fois, sur le fichier fini. Même partage
  // que partout ici : on ne stocke pas des positions, on garde de quoi les
  // recalculer.
  //
  // LA MINUTE DU FAIT, PAS L'HEURE COURANTE. `minute` est l'heure à laquelle la
  // bataille commence ; on y ajoute la seconde du fait. Sans elle on
  // demanderait qui est là MAINTENANT pour un événement d'il y a trois heures,
  // et l'on attribuerait la porte enfoncée à des gens qui dormaient encore.
  const ALENTOUR_R = 50;         // mètres — ce qu'on voit dans une rue

  function temoigner(o) {
    const opt = o || {};
    const F = window.Foule2d;
    if (!F || !F.presents) return { faits: 0, sans: S.annales.length };
    const R = opt.rayon || ALENTOUR_R;
    const quoi = opt.quoi ? new Set([].concat(opt.quoi)) : null;
    const min0 = typeof opt.minute === "number" ? opt.minute : null;
    let vus = 0, sans = 0;
    for (const f of S.annales) {
      if (f.alentour !== undefined) continue;       // déjà fait
      if (quoi && !quoi.has(f.quoi)) { sans++; continue; }
      const g = F.presents(f.x, f.y, R,
                           min0 === null ? undefined : min0 + f.t / 60);
      // Pas de cellules chargées autour de ce point : on ne SAIT pas, et l'on
      // ne prétend pas que personne n'a vu. Un « zéro » et un « on ignore » ne
      // se jouent pas pareil, et confondre les deux ferait mentir le fichier.
      if (!g) { sans++; continue; }
      f.alentour = {
        rayon: R,
        // Ceux qui étaient DEHORS : la rue et la place. Les seuls qui aient pu
        // voir quelque chose de leurs yeux.
        rue: g.croises,
        dont: g.metiers.slice(0, 3).map(([m, n]) => (n > 1 ? n + " " + m : m))
                       .join(", ") || null,
        // Derrière une porte, à cinquante mètres : ils n'ont rien vu, mais ils
        // ont ENTENDU — et l'on sait par quelle porte aller leur demander.
        derriere: g.toit,
        portes: g.portes.slice(0, 2).map(([s, n]) => n + " " + s).join(", ") || null,
      };
      vus++;
    }
    return { faits: vus, sans };
  }

  // ===========================================================================
  // CE QU'IL Y A SOUS LE DOIGT
  //
  // La toile de la bataille ne prend pas la souris (`pointer-events:none`), et
  // c'est très bien : trois couches empilées qui se disputeraient le pointeur,
  // c'est une carte qu'on ne peut plus tirer. Le plan garde donc la main et
  // POSE LA QUESTION — même geste que `derange`, où la foule demande à la
  // bataille si elle a le droit de dessiner quelqu'un.
  //
  // CE QU'ON RÉPOND EST CE QU'UN CORPS SAIT DE LUI-MÊME, et c'est déjà écrit
  // ailleurs : « chacun sait quel ordre il avait reçu, qui était son chef, et
  // où allait son aile ». Un survol n'ouvre donc aucune vérité neuve — il rend
  // lisible, du vivant, ce que la nuit rendra ramassable au matin.
  //
  // Le rayon est en PIXELS, converti par l'appelant : à la ville entière un
  // homme fait un huitième de pixel, et viser au mètre serait viser un cheveu.
  const RANG_SOUS = { roi: 6, tete: 5, nomme: 4, capitaine: 3, chef: 2,
                      coureur: 2, homme: 1 };

  function sousLeDoigt(x, y, rayon) {
    if (!S.hommes.length) return null;
    const r = Math.max(1.5, rayon || 6);
    const r2 = r * r;
    let best = null, bestRang = 0, bestD = Infinity;
    const peser = (o, rang, d) => {
      if (rang < bestRang || (rang === bestRang && d >= bestD)) return;
      best = o; bestRang = rang; bestD = d;
    };

    // Les figures d'abord : elles ne sont pas dans `hommes`, donc pas dans la
    // grille, et il n'y en a que douze.
    for (const f of S.figures) {
      const d = (f.x - x) * (f.x - x) + (f.y - y) * (f.y - y);
      if (d > r2) continue;
      peser({ quoi: "figure", nom: f.nom, role: f.role || null,
              camp: f.camp, dit: f.dit || null, x: f.x, y: f.y }, 4, d);
    }

    // Les hommes par la grille — la même que la mêlée, donc gratuite. Elle
    // n'existe qu'une fois la bataille semée : à l'arrêt on retombe sur la
    // boucle plate, qui coûte trois cents comparaisons et personne ne les
    // sentira sur un mouvement de souris.
    const regarder = (h) => {
      const d = (h.x - x) * (h.x - x) + (h.y - y) * (h.y - y);
      if (d > r2) return;
      // L'ESCOUADE NE SE LIT QUE POUR QUI EST DANS LA CHAÎNE, et c'est le même
      // garde-fou que `ailleDe` pose déjà. Un roi, une tête, un homme de la
      // charrette et TOUTE la garnison portent `escouade: 0` par défaut — donc
      // `escouades[0]`, qui appartient à quelqu'un d'autre. On voyait ainsi
      // Aegon II « ordre : avancer, n'entend plus rien », et un coureur du
      // Donjon obéir à une escouade de l'assaut. Le piège que la tête avait
      // déjà tendu une fois sur l'effectif, tendu une seconde fois.
      const a = ailleDe(h);
      const e = a ? S.escouades[h.escouade] : null;
      const u = formationDe(h), chefFormation = guideDe(u);
      const commandant = chargeCommandant(h);
      const o = {
        debugId: h.debugId,
        quoi: h.roi ? "roi" : h.tete ? "tete" : h.nom ? "nomme"
              : h.capitaine ? "capitaine" : h.etat === "coureur" ? "coureur"
              : (h.chef || h.chefFormation) ? "chef" : "homme",
        nom: h.nom || null, role: h.role || null, camp: h.camp, etat: h.etat,
        commandant:!!commandant,
        roleCommandant:commandant ? commandant.charge.role : null,
        carteCommandantActive:S.carteCommandantId === h.debugId,
        croyancesCommandant:h.commandement ? h.commandement.croyances.size : 0,
        // CE QU'IL A DANS LES MAINS, en toutes lettres et avec sa portée. Le
        // trait sur le plan dit déjà la longueur ; le doigt dit le nom, parce
        // qu'on ne devine pas « épieu » d'un segment de deux mètres deux.
        arme: h.arme ? h.arme.nom : null,
        allonge: h.arme ? h.arme.allonge : null,
        corps: h.corps || null, chefDuCorps: nomDuCorps(h.corps),
        // L'aile et l'escouade se comptent à partir de UN et par corps :
        // « l'aile n° 13 » n'appartient à personne, et c'est déjà la leçon que
        // les annales ont apprise pour les bannières.
        aile: a ? a.rang + 1 : null,
        // L'ORDRE SE DIT EN TOUTES LETTRES SOUS LE DOIGT. Ce n'est plus un mot
        // mais une phrase, et c'est justement ce qu'on veut voir en pointant un
        // homme : « suivre Ser Criston Cole à 200 pas » dit d'un coup pourquoi
        // il est planté là où il est. `attend` dit celui qu'il tient en réserve
        // d'un déclencheur — le seul cas où un homme obéit à ce qui n'est pas
        // encore arrivé.
        ordre: e ? dire(e.ordre) : null,
        unite: u ? u.id : null,
        parentUnite: u ? u.parent : null,
        chefFormation: chefFormation
          ? (chefFormation.nom || (u.camp === "garde" ? "chef du poste" : "vintenar")) : null,
        destination: u && u.ordre.destination ? u.ordre.destination.nom : null,
        calculsAStar: u ? u.cadre.calculs : null,
        successionDans: u && u.cadre.reprendA !== null
          ? Math.max(0, u.cadre.reprendA - S.temps) : null,
        distanceChef: chefFormation && chefFormation !== h
          ? Math.hypot(h.x - chefFormation.x, h.y - chefFormation.y) : 0,
        attend: e && e.attente ? dire(e.attente) : null,
        sourde: e ? !!e.sourde : false,
        // Le porteur de bannière la porte, donc il la fait tomber en tombant.
        banniere: h.capitaine && a ? !!a.banniere.debout : null,
        // CE QU'IL PORTE, TEL QU'IL LE PORTE ENCORE — c'est-à-dire déjà usé de
        // ce qu'il a couru. Pointer un coureur en pleine presse et lire la
        // phrase qui lui reste est la meilleure vue qu'on ait sur la chaîne.
        porte: h.etat === "coureur" ? dire(h.porte) : null,
        escorte: !!h.hors && !h.roi,
        // `debout` est rempli par le dessin, vingt fois par seconde. Tant que
        // rien n'a été peint — un four, un onglet caché — il est VIDE, et
        // « 0 debout » sur un corps de cinq cents hommes est un mensonge là où
        // le silence est juste. On distingue donc le zéro du rien.
        vivants: (h.corps && debout.size) ? debout.get(h.corps) || 0 : null,
        x: h.x, y: h.y,
        // ---- CE QU'IL A DANS LA TÊTE, ET POURQUOI ON L'EXPOSE --------------
        // `etat` MENTAIT PAR OMISSION, et c'est la raison d'être de ce bloc.
        // « tient » recouvre quatre situations qui n'ont rien à voir : il cède
        // le pas devant le nombre, il reprend son souffle, il est nez à nez et
        // attend qu'on l'épaule, ou il tient un poste qu'on lui a donné. Quatre
        // décisions différentes, un seul mot à l'écran — donc un plan qu'on ne
        // peut pas déboguer à l'œil. `branche` dit LAQUELLE des règles l'a pris.
        //
        // Le reste est la machine elle-même, en clair : la morale contre le
        // seuil où il rompra, le souffle contre celui où il cherchera à
        // souffler, le nombre qu'il voit dans ses cinq mètres. Ce sont les
        // trois entrées de toutes les décisions du fichier ; les lire sous le
        // doigt, c'est pouvoir dire « il devrait rompre » avant qu'il rompe, et
        // savoir qui a tort de nous ou de lui.
        //
        // LES TROIS DÉVIATIONS SONT LÀ AUSSI, parce qu'elles expliquent les
        // écarts qu'on n'explique pas autrement : deux hommes côte à côte, même
        // morale, même souffle, et l'un part quand l'autre reste. Ce n'est pas
        // un bug, c'est sa trempe, et il faut pouvoir le vérifier.
        branche: h.branche || null,
        // La branche historique reste exportée pour les bancs et les vieux
        // appelants. La pensée est désormais la trace canonique : une action,
        // sa cause immédiate et le système qui a gagné l'arbitrage. Ce sont
        // trois champs séparés afin que la loupe puisse les lire, les filtrer
        // et les comparer sans devoir démonter une phrase de debug.
        pensee: h.pensee ? {
          action: h.pensee.action,
          raison: h.pensee.raison,
          systeme: h.pensee.systeme,
          depuis: Math.max(0, +(S.temps - h.pensee.depuis).toFixed(1)),
          phrase: "j'essaie de " + h.pensee.action + " parce que " + h.pensee.raison,
        } : null,
        pensees: (h.pensees || []).slice(-2).reverse().map((p) => ({
          action: p.action, raison: p.raison, systeme: p.systeme,
          ilYa: Math.max(0, +(S.temps - p.depuis).toFixed(1)),
        })),
        // ---- CE QUE LA COUCHE 3 EN DIT, à côté de ce que la cascade a fait.
        // `branche` dit par quelle RÈGLE il en est là ; `maniere` dit comment
        // il tiendrait son ordre s'il décidait lui-même. Les deux côte à côte
        // sous le doigt : c'est toute la première passe du branchement, et
        // c'est ce qui permet de contester la couche avant de lui confier quoi
        // que ce soit. Rien ici ne pilote — voir `soldat()`.
        maniere: h.l3 ? h.l3.maniere : null,
        l3: h.l3 ? { place: +h.l3.place.toFixed(2), serre: +h.l3.serre.toFixed(2),
                     hate: +h.l3.hate.toFixed(2), lettre: +h.l3.lettre.toFixed(2) }
                  : null,
        // Ce qu'il veut, et que personne ne lui a demandé : sa convoitise du
        // moment, quand il a eu une maison sous la main. Voir la couche 4.
        envie: h.l4 != null ? +h.l4.toFixed(2) : null,
        // La couche 2 tournait déjà, mais demeurait invisible dans la loupe :
        // on ne pouvait donc pas savoir si elle proposait une meilleure issue
        // que la règle qui avait effectivement conduit l'homme.
        reflexion: h.l2 ? {
          idee: h.l2.idee,
          tient: +h.l2.tient.toFixed(2),
          attend: +h.l2.attend.toFixed(2),
          appui: +h.l2.appui.toFixed(2),
          degage: h.l2.degage != null ? +h.l2.degage.toFixed(2) : null,
        } : null,
        conduit: h.conduit || null,
        conduitBras: h.conduitBras || null,
        conduitPhrase: h.conduitPhrase || null,
        // ---- CE QUE SON CORPS DIT, A COTE DE CE QUE SA TETE A DECIDE -------
        // Le branchement progressif commence ICI, et il ne coute rien : la
        // couche 1 tourne deja pour chaque homme, on la MONTRE. Survoler
        // n'importe qui donne les deux lignes cote a cote — ce que la cascade a
        // choisi, et ce que le corps aurait fait. On voit donc la couche
        // travailler dans une vraie bataille avant qu'elle ne conduise quoi que
        // ce soit, et l'on peut la contester homme par homme.
        corpsDit: h.l1 ? h.l1.jambes + " · " + h.l1.bras : null,
        corpsPhrase: h.l1 ? h.l1.phrase : null,
        sangFroid: h.l1 ? +h.l1.sangFroid.toFixed(2) : null,
        exposition: h.l1 ? +h.l1.exposition.toFixed(2) : null,
        chargeNerveuse: h.l1 ? +h.l1.chargeNerveuse.toFixed(2) : null,
        empriseCorps: h.l1 ? +h.l1.emprise.toFixed(2) : null,
        corpsAgi: !!(h.l1 && h.l1.corpsAgi),
        pv: h.pv != null ? Math.max(0, Math.round(h.pv)) : null,
        pvMax: h.pvMax != null ? Math.round(h.pvMax) : null,
        entame: h.pv != null && h.pv < h.pvMax * SEUIL_RECUL,
        emprise: h.l1 ? +h.l1.emprise.toFixed(2) : null,
        souffle: h.souffle != null ? +h.souffle.toFixed(2) : null,
        soufflant: !!h.repos,
        cession: h.cedePour ? { pour:h.cedePour, chef:h.cedePourChef,
          ilYa:Math.max(0,+(S.temps-h.cedePassageA).toFixed(1)),
          distance:+h.cedeDistance.toFixed(2) } : null,
        // Le cercle est celui de SON dernier battement — la même mesure que
        // celle sur laquelle il vient de décider, pas un recomptage qui
        // pourrait dire autre chose que ce qu'il a vu.
        amis: h.cercle ? h.cercle.amis : null,
        ennemis: h.cercle ? h.cercle.ennemis : null,
        avantage: h.cercle ? avantage(h.cercle, h) : null,
        // Ce qui reste de son pas en arrière, et de sa patience de nez à nez.
        recule: h.recule ? Math.max(0, +(h.reculeJusqua - S.temps).toFixed(1)) : null,
        patience: h.patience != null ? +h.patience.toFixed(1) : null,
        // ⚠ `vivacite` est un facteur de DÉLAI : 0,6 est le vif. On le rend
        // donc à l'endroit sous le doigt, sinon la fiche ment.
        trempe: h.trempe != null ? +h.trempe.toFixed(2) : null,
        oeil: h.vivacite != null ? +(1 / h.vivacite).toFixed(2) : null,
        fond: h.fond != null ? +h.fond.toFixed(2) : null,
        // De quoi allumer sa maisonnée si l'appelant le veut. On le calcule
        // ici parce qu'ici seulement on tient l'homme : dehors, il n'y a plus
        // qu'une fiche de texte.
        _sel: {
          formation: u ? u.n : null,
          lien: (chefFormation && chefFormation !== h)
                ? [h.x, h.y, chefFormation.x, chefFormation.y]
                : (a && a.banniere && a.banniere.debout)
                  ? [h.x, h.y, a.banniere.x, a.banniere.y] : null,
        },
      };
      peser(o, RANG_SOUS[o.quoi] || 1, d);
    };
    if (S.gCol && S.gLig) autour(x, y, r, regarder);
    else for (const h of S.hommes) regarder(h);

    // Le verrou ne gagne jamais contre un homme : sept hommes cognent dessus,
    // et c'est d'eux qu'on veut la fiche quand on les vise. Il ne répond que
    // lorsqu'on montre le battant lui-même, où il n'y a personne.
    if (!best) {
      for (const v of S.verrous) {
        const d = (v.x - x) * (v.x - x) + (v.y - y) * (v.y - y);
        if (d > (r + 4) * (r + 4)) continue;
        peser({ quoi: "porte", nom: v.nom, etat: v.etat,
                part: v.max ? v.pv / v.max : 0, frappeurs: v.frappeurs || 0,
                x: v.x, y: v.y }, 1, d);
      }
    }
    return best;
  }

  // TOUT CE QUI PORTE UN NOM, à plat. C'est le seul relevé qui permette de
  // vérifier une mise en place sans la regarder : six têtes, un capitaine du
  // poste, un roi et douze témoins, avec leurs mètres. Une distribution qui se
  // lit dans la console est une distribution qu'on peut corriger.
  const nommes = () => [
    ...S.hommes.filter((h) => h.nom).map((h) => ({
      nom: h.nom, camp: h.camp, corps: h.corps, role: h.role || null,
      rang: h.roi ? "roi" : h.tete ? "tete"
            : h.capitaine ? "capitaine" : h.hors ? "escorte" : "homme",
      etat: h.etat, x: +h.x.toFixed(1), y: +h.y.toFixed(1),
      ou: situer(h.x, h.y).ou })),
    ...S.figures.map((f) => ({
      nom: f.nom, camp: f.camp, rang: "figure", role: f.role || null, dit: f.dit,
      x: +f.x.toFixed(1), y: +f.y.toFixed(1), ou: situer(f.x, f.y).ou })),
  ];

  /** Les places des chefs dans le repère supérieur, pour les épreuves et marks. */
  const echelons = () => {
    const xs = [];
    for (const dep of S.deploiements.values()) {
      for (const h of S.tetes) {
        const p = h.camp === dep.camp && dep.tetes.get(h.corps);
        if (p) xs.push({ deploiement:dep.id, role:"chef de corps", id:h.debugId,
                         nom:h.nom || null, corps:h.corps, x:h.x, y:h.y,
                         cibleX:p.x, cibleY:p.y });
      }
      for (const [h, p] of dep.capitaines) {
        xs.push({ deploiement:dep.id, role:"centenar", id:h.debugId, nom:h.nom || null,
                  corps:h.corps, aile:p.aile, x:h.x, y:h.y,
                  cibleX:p.x, cibleY:p.y });
      }
    }
    return xs;
  };

  /** L'ordre de bataille tel qu'il est posé — combien, où, sous quel nom. */
  const ordreDeBataille = () => ({
    echelle: S.ECHELLE,
    assaut: CORPS.map((c) => ({
      corps: c.id, chef: c.nom, forme: c.forme, humeur: c.humeur,
      hommes: S.hommes.filter((h) => h.corps === c.id && !h.tete).length,
      sur: c.hommes,
      ailes: S.ailes.filter((a) => a.corps === c.id).length,
      escouades: S.escouades.filter((e) => e.corps === c.id).length,
      dit: c.dit,
    })),
    garde: S.hommes.filter((h) => h.camp === "garde").length,
    // Le roi et les siens ne sont d'aucun corps, et c'est pour ça qu'ils se
    // comptent à part : ils ne prennent aucune porte et n'obéissent à personne.
    charrette: S.hommes.filter((h) => h.hors).length,
    figures: S.figures.length,
  });

  const comportements = () => ({
    complet: COMPORTEMENTS_REQUIS.every((x) => !!x[1]),
    modules: COMPORTEMENTS_REQUIS.map((x) => x[0]),
    selectionParEpreuve: false,
  });

  return { poser, preparer, recadrer, arreter, basculer, rejouer, vider, derange,
           etat, pas, peur, troupe, chemins, unites, ordonnerFormation,
           equiperUnite, terrainEpreuve: reglerTerrainEpreuve,
           ordonnerRassemblement, ordonnerDeploiement, deplacerDeploiement,
           ordonnerDoctrineDeploiement,
           ordonnerRatissage, rapportsRatissage, rapportsCommandement, batiments,
           faits, nommes, echelons, ordreDeBataille, diagnostic, comportements,
           sous: sousLeDoigt, souligner, carteCommandant,
           selectionnerCarteCommandant,
           carteCommandantSelectionnee: () => S.carteCommandantId == null
             ? null : carteCommandant(S.carteCommandantId),
           dangerExterieur, signalerIncendies, incendiesActifs, jugerRuptureUnite,
           temoigner,
           // Régler une future épreuve ne convoque plus l'armée sur une carte
           // encore vide. Si une scène existe déjà, le comportement historique
           // reste inchangé ; sinon `Scenarios.poser()` la dressera explicitement.
           echelle: (e) => { if (e) { S.ECHELLE = e; if (S.hommes.length) rejouer(); }
                             return S.ECHELLE; },
           portes: () => portes().map((p) => p.nom),
           // CE POINT EST-IL LIBRE ? Rend `null` tant que le masque n'est pas
           // chargé — « on ne sait pas » et non « c'est libre », comme
           // `libreEn` l'exige de ses appelants.
           //
           // POURQUOI ON L'OUVRE. Un banc qui veut compter les hommes dans les
           // murs a besoin de cette réponse ; s'il ne l'a pas, il relit
           // `/masque` de son côté et redécode les bits — et l'on a deux
           // lectures du bâti qui dériveront le jour où le masque changera de
           // pas. C'est la même règle que pour `mesures.js` : une seule
           // réponse, chez celui qui la tient.
           libre: (x, y) => (solConnu() ? libreEn(x, y) : null),
           eau: (x, y) => (S.sousEau ? S.sousEau(x, y) : null),
           bornes: () => S.plan && S.plan.bornes ? S.plan.bornes.slice() : null,
           rafraichir: () => { peindre(); montre(); } };
})();
