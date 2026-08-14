// 5-la-main.js — le cinquième fichier. IL NE PENSE PAS, IL DÉPARTAGE.
//
//   sa question : aucune. Il ne s'en pose pas, et c'est ce qui le distingue
//                 des quatre couches.
//   ce qu'il rend : QUI tient la main sur chaque emplacement, ce battement-ci,
//                 et de combien il a gagné.
//
// ─────────────────────────────────────────────────────────────────────────────
// CE FICHIER TRANCHE UNE CONTRADICTION QUI DURAIT, ET IL FAUT DIRE LAQUELLE
//
// Le README de ce dossier donnait au cinquième fichier deux métiers
// incompatibles, et refusait de le nommer tant qu'on n'avait pas choisi :
//
//   — règle de forme : « une couche qui rendrait un objet obligerait l'arbitre
//     à cesser d'être une SOMME » → il compose des nombres, il ne tranche rien.
//   — l'affaire, ⚔️ 90311 : « qui, du corps ou de la tête, tient la main sur un
//     GESTE DONNÉ » → il désigne un vainqueur.
//
// LA SOMME N'EST PAS CONSTRUCTIBLE, ET CE N'EST PAS UN AVIS — c'est ce que
// rendent les quatre modules, lu sur le disque :
//
//   1-corps          `{ jambes, bras }`        un MOT d'un répertoire fermé
//   2-reflexion      `{ tient, attend, appui, issue{x,y,force} }`  des nombres + un cap
//   3-interpretation `{ place, serre, hate, lettre }`              des modulations d'ordre
//   4-envie          `temperament`, `butin`, `patience`, `silenceTenu`  des durées et des désirs
//
// On n'additionne pas « fuite » et 0,42. Les quatre sorties sont normalisées
// chacune dans son espace, et deux d'entre elles ne sont pas des scalaires du
// tout. La règle 2 du README — tout sur [−1, 1], donc composable — est vraie
// des NOMBRES d'une couche ; elle ne rend pas commensurables un mot et un cap.
// La somme était une intention, pas une pièce.
//
// MAIS LE VAINQUEUR UNIQUE EST FAUX AUSSI, et le README le dit sans le voir :
// `ballants` retire la capacité de frapper « SANS PRENDRE TOUT L'HOMME ».
// Un homme dont le corps a lâché les bras garde la tête sur ses jambes. Si
// l'arbitrage se faisait par homme, ce cas serait inécrivable — or c'est le
// seul geste de couche 1 qui conduise réellement aujourd'hui sans discussion.
//
// D'OÙ LA FORME, ET ELLE SORT DES DEUX TEXTES SANS EN TRAHIR AUCUN :
// **l'arbitrage se fait par EMPLACEMENT, et la composition est DANS l'élection,
// pas à la place.** Chaque couche pose une PRÉTENTION — une force dans [0, 1],
// composée de ses propres nombres — sur les emplacements qui la concernent ; la
// plus forte prend l'emplacement, et les autres n'ont rien pour ce battement-là.
// On compose des forces (Wenna avait raison sur la matière) et l'on désigne une
// main (l'affaire avait raison sur le résultat).
//
// Ce n'est pas une invention : C'EST LA FORME DE L'ÉLECTION DE LA COUCHE 1,
// un étage plus haut. `elire()` pondère un répertoire par `appels`, `acquis` et
// `dysregule`, puis prend le plus fort. Ici on pondère quatre couches et l'on
// prend la plus forte. Le même problème revient au même endroit du modèle, et
// ce n'est pas une coïncidence — c'est le signe qu'on est au bon endroit.
//
// ─────────────────────────────────────────────────────────────────────────────
// L'ORDINAIRE EST D'OBÉIR — DONC L'ORDRE N'EST PAS UN PRÉTENDANT, C'EST LE SOL
//
// La couche 3 « ne demande pas s'il obéit, elle suppose qu'il obéit ». Elle ne
// réclame donc rien : elle FIXE LA BARRE que les autres doivent franchir. Un
// homme qui tient son ordre à la lettre est difficile à déloger ; un homme qui
// « n'en fait plus qu'à sa tête » a déjà lâché la barre, et le premier qui
// prétend passe.
//
// Conséquence de forme, et elle est bonne : quand personne ne franchit la
// barre, l'arbitre rend `"ordre"`, et l'appelant tombe dans la cascade comme
// aujourd'hui. Le branchement de ⚔️ 90312 se fait donc morceau par morceau, en
// retirant de la cascade ce dont une main est devenue capable — jamais d'un
// coup.
//
// ─────────────────────────────────────────────────────────────────────────────
// AUCUN TIRAGE ICI, ET C'EST DÉLIBÉRÉ
//
// Le 3e jour, une seule ligne de `Math.random()` dans `corps-adapt.js` a
// contourné la graine de `hasard.js` : écart pire 329 m, 931 172 états faux, un
// four qui ne rendait plus rien de ce que la simulation avait fait. Cette
// pièce-ci arbitre par comparaison et par horloge, elle ne tire rien, elle ne
// prend pas de `u` en argument, et elle n'en prendra pas. Un départage aléatoire
// entre deux prétentions égales serait exactement la même faute avec un autre
// visage : deux prétentions égales, c'est un homme qui hésite, et un homme qui
// hésite ne fait rien de nouveau — il garde ce qu'il faisait. Voir `exigence`.
//
// TOUT EST DANS [0, 1] pour les forces — une force de prétention n'a pas de
// pôle défavorable, elle a un zéro : « je ne demande rien ». Toute borne est
// une saturation. Aucune fonction n'écrit, aucune n'appelle une couche.
//
// EN OBSERVATION. Rien ici ne conduit encore : `soldat()` garde sa chaîne de
// `if`. Le branchement est l'action ⚔️ 90312, et il se fait après qu'on a
// regardé cette pièce se tromper sur une vraie nuit.
"use strict";
(() => {

  // Les mesures du monde sont partagées, pas recopiées : `M.SEJOUR` dit combien
  // de temps dure un geste d'homme, et c'est de là que sort la seule durée de
  // ce fichier. Même branchement que `corps-adapt.js`.
  const C = (typeof window !== "undefined" && window.Corps)
    || (typeof require !== "undefined" && require("./1-corps.js"));

  /** Lecture d'un nombre, zéro par défaut. */
  const G = (o, k, d) => (o && typeof o[k] === "number" ? o[k] : (d || 0));
  /** La part positive seule. */
  const P = (v) => Math.max(0, v);
  /** La part négative seule, rendue positive. */
  const N = (v) => Math.max(0, -v);
  /** Une grandeur déjà bornée sur [−1, 1], relue sur [0, 1]. Ce n'est PAS un
   *  écrêtage : rien n'est coupé, c'est le même segment lu dans l'autre sens.
   *  Une force de prétention n'a pas de pôle défavorable. */
  const demi = (v) => (Math.max(-1, Math.min(1, v)) + 1) / 2;

  // ===========================================================================
  // LE TEMPS QU'UNE MAIN NE REND PAS — et il sort de `M.SEJOUR`
  // ===========================================================================

  /** La plus courte durée de geste du répertoire du corps, `planté` excepté
   *  puisqu'il est le repos et n'a aucun minimum. Elle vaut 0,2 s : la dérobade.
   *
   *  POURQUOI C'EST ELLE ET PAS UN NOMBRE À MOI. Une main qui changerait de
   *  couche plus vite que le geste le plus bref ferait commencer un geste à un
   *  prétendant et finir à un autre — un homme qui part en esquive et arrive en
   *  charge. Le plancher du fichier est donc celui du répertoire qu'il arbitre,
   *  et il se corrige tout seul le jour où l'on corrigera une durée là-bas. */
  const TENUE_MIN = (() => {
    let m = Infinity;
    const t = (C && C.M && C.M.SEJOUR) || {};
    for (const g in t) if (g !== "planté" && t[g][0] > 0) m = Math.min(m, t[g][0]);
    return m === Infinity ? 0.2 : m;
  })();

  /** DE COMBIEN IL FAUT BATTRE CELUI QUI TIENT DÉJÀ. C'est une période
   *  réfractaire, et c'est un fait de moteur, pas un anti-rebond : un programme
   *  moteur lancé est balistique le temps de partir, puis redevient révisable.
   *  D'où la forme — proche de 1 juste après la prise, elle s'efface ensuite.
   *
   *  ET C'EST CE QUI REMPLACE UN TIRAGE. Deux prétentions égales ne se départent
   *  pas au sort : celui qui tient garde, parce qu'il tient. Un homme qui hésite
   *  ne fait pas quelque chose de nouveau, il continue.
   *
   *  @param tenu  secondes depuis que la main courante a été prise. */
  const exigence = (tenu) => Math.exp(-Math.max(0, tenu) / TENUE_MIN);

  // ===========================================================================
  // LA BARRE — CE QUE L'ORDRE VAUT
  // ===========================================================================

  /** À quel point l'ordre reçu tient encore les jambes de cet homme. C'est
   *  `lettre` et rien d'autre, relu sur [0, 1] : la couche 3 mesure déjà
   *  exactement ce rapport — ce qu'il consent à l'ordre contre ce qu'il se
   *  garde. Un homme sans ordre du tout (`l3` absent) n'a pas de barre : il est
   *  livré à ses couches, ce qui est la définition d'un homme sans nouvelles.
   *
   *  ⚠ ZÉRO EST L'ORDINAIRE, ET L'ORDINAIRE OBÉIT. `lettre = 0` rend une barre
   *  de 0,50 : il faut vouloir franchement autre chose pour désobéir. C'est la
   *  moitié du fichier, et c'est la seule raison pour laquelle une troupe reste
   *  une troupe. */
  function barre(l3) {
    if (!l3) return 0;
    return demi(G(l3, "lettre"));
  }

  // ===========================================================================
  // LES PRÉTENTIONS — chacune composée des nombres de SA couche
  // ===========================================================================

  /** LE CORPS, SUR LES JAMBES. Il prétend de tout le volant qu'il tient, et de
   *  rien du tout quand il est `planté`.
   *
   *  `planté` ne prend rien, et ce n'est pas une exception : c'est l'état où le
   *  corps n'a rien à dire. Le README le pose déjà comme la pièce qui maintient
   *  le déménagement progressif — on la garde mot pour mot, on la déplace
   *  seulement de la chaîne de `if` de `soldat()` jusqu'ici, où elle est une
   *  force et non un trou dans un aiguillage.
   *
   *  ET L'EMPRISE NE SE RÉAPPLIQUE PAS DEUX FOIS. `SOUS_EMPRISE` a déjà pondéré
   *  fuite, sidération et ruée DANS l'élection de la couche 1 : si l'on
   *  remultipliait ici, un homme calme verrait sa fuite écrasée au carré. Ce
   *  qu'on lit ici, c'est de combien le corps tient le volant — une fois. */
  function prendCorps(l1) {
    if (!l1 || l1.jambes === "planté") return 0;
    return Math.max(0, Math.min(1, G(l1, "emprise")));
  }

  /** LA RÉFLEXION, SUR LES JAMBES. Elle ne prétend que quand elle veut CHANGER
   *  quelque chose — tenir n'est pas une prétention, c'est ce qui se passe quand
   *  personne ne réclame.
   *
   *  Deux façons de vouloir autre chose, et une seule sort :
   *    — céder le pas : `tient` sous zéro, MULTIPLIÉ par `issue.force`. C'est la
   *      règle dure du module 2 : `degage` multiplie tout ce qui part. Un homme
   *      acculé ne prétend RIEN sur ses jambes, quelle que soit son envie de
   *      partir — et c'est précisément ce qui le fait se battre.
   *    — attendre le nombre : `attend` au-dessus de zéro. La patience est une
   *      conduite, pas une absence de conduite : elle demande les jambes pour
   *      les empêcher d'avancer, et sans ça un homme délibéré est indiscernable
   *      d'un homme qui obéit mollement. */
  function prendReflexion(l2) {
    if (!l2) return 0;
    const partir = N(G(l2, "tient")) * P(G(l2.issue || {}, "force"));
    const patienter = P(G(l2, "attend"));
    return Math.max(0, Math.min(1, Math.max(partir, patienter)));
  }

  /** L'ENVIE, SUR LES JAMBES. Le seul désir gratuit écrit à ce jour est le
   *  pillage : il quitte la colonne pour une maison. Il prétend de ce qu'il
   *  vaut, et l'appelant le passe tel quel — `4-envie` rend déjà un taux borné.
   *
   *  ⚠ IL PRÉTEND CONTRE L'ORDRE, ET C'EST TOUT L'INTÉRÊT. C'est la seule
   *  couche qui puisse faire désobéir un homme dont rien ne va mal, et la barre
   *  de la couche 3 est exactement ce qui décide s'il y arrive. */
  function prendEnvie(envie) {
    return Math.max(0, Math.min(1, G({ v: envie }, "v")));
  }

  // ===========================================================================
  // L'ÉLECTION D'UN EMPLACEMENT
  // ===========================================================================

  /** Départage des prétendants sur un emplacement.
   *
   *  @param pret  { nom: force } — les prétentions, l'ordre exclu.
   *  @param sol   la barre de l'ordre : ce qu'il faut franchir pour prendre.
   *  @param tenue { main, depuis } — qui tient, et depuis quel instant.
   *  @param t     l'instant courant, en secondes de bataille.
   *
   *  Rend `{ main, force, marge, second }`. `marge` est ce qui sépare le
   *  vainqueur du suivant — c'est le SIGNE auquel on sait si l'homme est décidé
   *  ou partagé, et il se lit dans la loupe. Une marge quasi nulle sur trois
   *  battements de suite, c'est un homme qu'on a mal modélisé, pas un homme
   *  indécis : la pièce le dit au lieu de le cacher. */
  function elire(pret, sol, tenue, t) {
    const courant = tenue && tenue.main ? tenue.main : "ordre";
    const tenu = tenue && typeof tenue.depuis === "number" ? t - tenue.depuis : Infinity;
    // Celui qui tient part avec son dû ; on ne le déloge pas d'un cheveu.
    const du = exigence(tenu);

    // ⚠ CELUI QUI TIENT SE PÈSE EN PREMIER, ET HORS DE LA BOUCLE. Écrit dans la
    // boucle, le résultat dépendait de l'ORDRE DES CLEFS de l'objet : un
    // prétendant plus faible examiné avant le tenant lui prenait la place, puis
    // le tenant devait le battre à son tour. Deux hommes identiques auraient
    // décidé différemment selon l'ordre où j'ai tapé trois lignes. Le Bassin ne
    // l'a pas montré — aucun de mes onze cas n'avait deux prétendants forts —,
    // il s'est vu à la relecture, et c'est la faute que ce fichier aurait
    // portée le plus longtemps.
    let main = "ordre", fort = sol;
    if (courant !== "ordre" && typeof pret[courant] === "number" && pret[courant] > sol) {
      main = courant; fort = pret[courant];
    }

    // Le meilleur des autres, et ce qu'il doit franchir pour prendre la main.
    let defi = null, defiV = -1;
    for (const nom in pret) {
      if (nom === main) continue;
      if (pret[nom] > defiV) { defiV = pret[nom]; defi = nom; }
    }
    let second = sol;
    if (defi !== null && defiV > fort + du) { second = fort; fort = defiV; main = defi; }
    else if (defiV > second) second = defiV;

    // `marge` PEUT ÊTRE NÉGATIVE, et c'est une information et non un défaut :
    // c'est le tenant qui garde la main contre plus fort que lui, parce que son
    // geste est parti. Le moment balistique se lit là, et nulle part ailleurs.
    return { main, force: fort, marge: fort - second, second };
  }

  // ===========================================================================
  // UN BATTEMENT
  // ===========================================================================

  /**
   * @param c   ce que les quatre couches viennent de rendre pour cet homme :
   *            { l1, l2, l3, envie } — n'importe lequel peut manquer.
   * @param e   l'état de l'arbitre pour cet homme, MUTÉ ici — c'est le seul
   *            objet que ce fichier écrive, et il est fourni par l'appelant,
   *            jamais posé au passage sur l'homme.
   * @param t   l'instant, en secondes de bataille.
   *
   * Rend `{ jambes, bras, corpsAgi, phrase }`.
   */
  function pas(c, e, t) {
    c = c || {}; e = e || {};
    // ⚠ `-Infinity` ET NON `t`, ET LE BASSIN A PRIS SIX CAS SUR ONZE DESSUS.
    // Posé à `t`, le premier battement de chaque homme croyait que l'ordre
    // venait de prendre la main à l'instant : `exigence(0) = 1,00`, donc il
    // fallait franchir la barre PLUS UN — ce que nulle prétention bornée à 1 ne
    // peut faire. Tout homme obéissait au premier battement, et comme la main
    // ne changeait jamais, il obéissait la nuit entière.
    //
    // La faute n'était pas dans la période réfractaire : elle était dans
    // l'affirmation qu'un homme qui n'a rien fait vient de faire quelque chose.
    // Un homme qui entre en scène obéit DEPUIS TOUJOURS — il n'a pas de geste
    // en cours à protéger.
    if (!e.jambes) e.jambes = { main: "ordre", depuis: -Infinity };
    if (!e.bras)   e.bras   = { main: "ordre", depuis: -Infinity };

    const sol = barre(c.l3);

    // --- LES JAMBES ---------------------------------------------------------
    const jambes = elire({
      corps:     prendCorps(c.l1),
      reflexion: prendReflexion(c.l2),
      envie:     prendEnvie(c.envie),
    }, sol, e.jambes, t);
    if (jambes.main !== e.jambes.main) { e.jambes.main = jambes.main; e.jambes.depuis = t; }
    jambes.depuis = e.jambes.depuis;

    // --- LES BRAS -----------------------------------------------------------
    // LES BRAS MORTS NE S'ARBITRENT PAS, ET C'EST LA SEULE EXCEPTION DU FICHIER.
    // `ballants` n'est pas sous `SOUS_EMPRISE` : son moteur est l'ÉPUISEMENT,
    // pas la peur. Un homme à bout laisse tomber les bras en pleine lucidité, et
    // aucune volonté ne les relève. Ce n'est donc pas une prétention qu'on met
    // en balance avec un ordre — c'est une capacité qui n'est plus là. La faire
    // concourir reviendrait à dire qu'un ordre assez ferme rend la force à un
    // bras qui n'en a plus.
    let bras;
    if (c.l1 && c.l1.bras === "ballants") {
      bras = { main: "corps", force: 1, marge: 1, second: sol, force_majeure: true };
      if (e.bras.main !== "corps") { e.bras.main = "corps"; e.bras.depuis = t; }
    } else {
      bras = elire({ corps: prendCorps(c.l1) }, sol, e.bras, t);
      if (bras.main !== e.bras.main) { e.bras.main = bras.main; e.bras.depuis = t; }
    }
    bras.depuis = e.bras.depuis;

    // LE SIGNE AUQUEL ON LE SAIT — et c'est le nom que Wenna a posé pour ma
    // main : `corpsAgi`, VRAI SI LA COUCHE A PRIS CE BATTEMENT-CI. Un fait de
    // battement, pas un régime. Il remplace `h.l1.pilote`, qui disait une
    // conduite permanente et n'était plus qu'un affichage.
    const r = { jambes, bras, corpsAgi: jambes.main === "corps" || bras.main === "corps" };
    r.phrase = phrase(r, c);
    return r;
  }

  /** LE MOT, ET IL N'A AUCUN EFFET — même règle que `idee` et `maniere` : on le
   *  lit dans la loupe pour voir l'arbitre se tromper avant de lui donner la
   *  main. Il dit QUI tient et À QUEL POINT, jamais ce qui est fait. */
  const phrase = (r, c) => {
    const j = r.jambes, serre = j.marge < 0.05;
    // LE MOMENT BALISTIQUE — il tient contre plus fort que lui, parce que son
    // geste est déjà parti. C'est trois dixièmes de seconde dans une vie
    // d'homme, et c'est la seule chose que la loupe ne pouvait pas montrer.
    if (j.marge < 0) return "son geste est parti, il ne le rattrape plus";
    if (j.main === "corps" && serre)     return "son corps l'emporte de peu";
    if (j.main === "corps")              return "son corps a la main";
    if (j.main === "reflexion" && serre) return "il se raisonne, de justesse";
    if (j.main === "reflexion")          return "il a trouvé quoi faire, et il le fait";
    if (j.main === "envie")              return "il a lâché la colonne pour son compte";
    if (r.bras.force_majeure)            return "il tient son ordre et n'a plus de bras";
    if (j.force < 0.1)                   return "personne ne le tient, pas même son ordre";
    return "il fait ce qu'on lui a dit";
  };

  // ===========================================================================
  const API = { TENUE_MIN, exigence, barre, demi,
                prendCorps, prendReflexion, prendEnvie, elire, pas, phrase };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.LaMain = API;
})();
