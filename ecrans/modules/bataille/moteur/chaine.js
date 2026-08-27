// chaine.js — LE MANIFESTE UNIQUE. Une seule liste de scripts pour tout le dépôt.
//
// POURQUOI CE FICHIER EXISTE. Il y avait huit listes. `scripts/monde/sac.js` en
// tenait une, `jeu.html` une autre, `bataille/page.js` une troisième, les
// scripts d'analyse les suivantes — et elles avaient DÉJÀ divergé en silence :
// la couche 2 manquait au four (voir l'en-tête de `sac.js`), `roster.js` manque
// encore à `jeu.html` alors que `bataille2d.js` le lit, et `5-qui-conduit.js`
// n'est pas au même rang dans le jeu et dans le four. Une liste qui diverge ne
// fait pas tomber la page : elle fabrique une chaîne que PERSONNE ne mesure, et
// l'on découvre six semaines plus tard que le banc jugeait un autre moteur que
// celui qu'on regarde.
//
// CE QU'IL EST, ET CE QU'IL N'EST PAS. C'est un ORDRE de chargement, pas un
// graphe de dépendances : ces fichiers ne sont pas des modules ES, ils posent
// des globales à l'évaluation, et l'ordre est la seule chose qui les tienne. Il
// ne charge rien lui-même — le navigateur pose des balises, Node évalue des
// sources, et chacun le fait à sa façon. Ce fichier ne fait que DIRE QUOI, DANS
// QUEL ORDRE, ET POUR QUI.
//
// LES ENSEMBLES. Un consommateur ne charge pas tout : le four n'a que faire des
// dragons, la page de scène a besoin de ses épreuves. On déclare donc des
// ensembles, jamais des listes parallèles :
//
//   moteur  la simulation nue — le four, les bancs, le jeu, la scène ;
//   scene   ce que /bataille ajoute par-dessus : épreuves, incendie, dragons.
//
// Tout ensemble CONTIENT `moteur` dans le même ordre. C'est la règle qui rend
// la divergence impossible : on n'ajoute pas un fichier à un ensemble, on le
// déclare une fois avec les ensembles auxquels il appartient.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleChaine = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  // ---------------------------------------------------------------------
  // LES MORCEAUX, DANS L'ORDRE. Le `pourquoi` n'est pas de la décoration :
  // c'est ce qui empêche le prochain de déplacer une ligne « pour ranger ».
  // ---------------------------------------------------------------------
  const MORCEAUX = [
    // Le journal d'abord : les contrats lui déposent leurs fautes, et une
    // faute qui tombe avant que le journal existe est une faute qu'on perd.
    { f:"bataille/moteur/commun/traces.js", ens:["moteur"],
      pose:"BatailleTraces",
      pourquoi:"le journal de décision. Il ne dépend de rien et tout peut lui écrire." },
    { f:"bataille/moteur/commun/contrats.js", ens:["moteur"],
      pose:"BatailleContrats",
      pourquoi:"la forme des six objets échangés ; ne dépend que du journal." },
    { f:"bataille/moteur/monde/topologie.js", ens:["moteur"],
      pose:"BatailleMondeTopologie",
      pourquoi:"le sol, le bâti et l'eau. Première pièce du monde physique " +
               "sortie du monolithe ; `bataille2d.js` s'y lie au chargement, " +
               "donc avant lui, et elle ne dépend de rien." },
    { f:"bataille/moteur/monde/navigation.js", ens:["moteur"],
      pose:"BatailleMondeNavigation",
      pourquoi:"les routes de groupe. Elle prend la topologie en argument, " +
               "donc apres elle ; posee avant `bataille2d.js`, qui s'y lie." },
    { f:"bataille/moteur/monde/mouvement.js", ens:["moteur"],
      pose:"BatailleMondeMouvement",
      pourquoi:"le seul ecrivain de position. Prend la topologie, donc apres elle." },
    { f:"bataille/moteur/unite/identite.js", ens:["moteur"],
      pose:"BatailleUniteIdentite",
      pourquoi:"l'appartenance, la place et la succession. Elle prend `dehors` " +
               "de la topologie et `noter` du monolithe : apres l'une, avant l'autre." },
    { f:"bataille/moteur/etat.js", ens:["moteur"],
      pose:"BatailleEtatSim",
      pourquoi:"l'état de la simulation. `bataille2d.js` l'appelle à sa première " +
               "ligne exécutable : il doit être posé avant lui, et il ne dépend " +
               "de rien — c'est un objet littéral et rien d'autre." },

    { f:"bataille/hasard.js", ens:["moteur"],
      pose:"BatailleHasard",
      pourquoi:"une seule urne, et elle ouvre la chaîne : tout ce qui tire lit celle-ci." },

    { f:"bataille/mesures.js", ens:["moteur"],
      pose:"BatailleMesures",
      pourquoi:"les grandeurs physiques partagées ; personne ne recopie un mètre." },

    { f:"bataille/roster.js", ens:["moteur"],
      pose:"BatailleRoster",
      pourquoi:"la composition déclarative des forces. `bataille2d.js` la lit " +
               "(METIERS, assembler) : absente, le moteur prend un chemin " +
               "dégradé sans le dire — c'est ce qui arrivait dans jeu.html." },

    { f:"survival-stack/1-corps.js", ens:["moteur"], pose:"Corps",
      pourquoi:"la couche 1, avant son pourvoyeur." },
    { f:"bataille/corps-adapt.js", ens:["moteur"], pose:"BatailleCorps",
      pourquoi:"le pourvoyeur de la couche 1 : il bâtit ses stimuli depuis la bataille." },

    { f:"survival-stack/4-envie.js", ens:["moteur"], pose:"Envie",
      pourquoi:"elle CONDUIT — APPETIT et SILENCE sortent d'elle : avant bataille2d." },
    { f:"survival-stack/3-interpretation.js", ens:["moteur"], pose:"Interpretation",
      pourquoi:"lue par `soldat()` à chaque battement : posée avant lui." },
    { f:"survival-stack/2-reflexion.js", ens:["moteur"], pose:"Reflexion",
      pourquoi:"la couche qui cherche l'issue, avant son pourvoyeur." },
    { f:"survival-stack/5-qui-conduit.js", ens:["moteur"], pose:"QuiConduit",
      pourquoi:"la main : elle élit jambes et bras. Le four la posait ici, " +
               "jeu.html après reflexion-adapt — on tranche pour le four." },
    { f:"bataille/reflexion-adapt.js", ens:["moteur"], pose:"BatailleReflexion",
      pourquoi:"le pourvoyeur de la couche 2 ; il pose h.l2 et la trace h.conduit." },

    { f:"bataille/commandement.js", ens:["moteur"], pose:"BatailleCommandement",
      pourquoi:"faits, croyances, confiance et champ de vision d'un chef." },

    // --- ce que la page de scène ajoute, et elle seule ------------------
    { f:"bataille/scenarios.js", ens:["scene"], pose:"BatailleScenarios",
      pourquoi:"les épreuves. Le four n'en veut pas : il cuit une condition à lui." },
    { f:"bataille/incendie-ville.js", ens:["scene"], pose:"IncendieVille",
      pourquoi:"le feu qui court, lu par les épreuves de ville." },
    { f:"bataille/dragons.js", ens:["scene"], pose:"DragonEpreuve",
      pourquoi:"l'épreuve du dragon, installée par la page." },

    // --- le monolithe, puis l'enveloppe --------------------------------
    { f:"bataille2d.js", ens:["moteur"], pose:"Bataille2d",
      pourquoi:"il lit tout ce qui précède à l'évaluation. Il ferme la marche, " +
               "et il la fermera encore quand il ne sera plus qu'une façade." },
    { f:"bataille/moteur/index.js", ens:["moteur"], pose:"BatailleMoteur",
      pourquoi:"la façade interne : elle enveloppe le monolithe, donc après lui. " +
               "Le jour où la flèche s'inverse, cette ligne ne bouge pas." },
  ];

  // LA QUEUE EST FIXE, quel que soit l'ensemble. Les morceaux de scène veulent
  // être posés AVANT le monolithe — la page les installe dès que `Bataille2d`
  // répond — et l'enveloppe APRÈS lui. On garde donc l'ordre du tableau pour
  // tout ce qui précède, et l'on force ces deux-là à la fin, dans cet ordre.
  const QUEUE = ["bataille2d.js", "bataille/moteur/index.js"];
  const DERNIER = QUEUE[QUEUE.length - 1];

  /** Les fichiers d'un ensemble, chemins relatifs à `ecrans/modules/`. */
  function fichiers(ensemble) {
    const veut = (m) => m.ens.indexOf("moteur") >= 0 || m.ens.indexOf(ensemble) >= 0;
    const gardes = MORCEAUX.filter(veut).map((m) => m.f);
    const avant = gardes.filter((f) => QUEUE.indexOf(f) < 0);
    const fin = QUEUE.filter((f) => gardes.indexOf(f) >= 0);
    return avant.concat(fin);
  }

  /**
   * Les URL pour une page.
   *   prefixe  ce qui précède le chemin ("/modules/" par défaut) ;
   *   version  estampille de cache, ajoutée à chacune ;
   *   deja     les fichiers déjà posés en tête de page, à ne pas redemander.
   */
  function urls(ensemble, opts) {
    opts = opts || {};
    const prefixe = opts.prefixe == null ? "/modules/" : opts.prefixe;
    const deja = new Set(opts.deja || []);
    const v = opts.version ? String(opts.version) : null;
    return fichiers(ensemble).filter((f) => !deja.has(f)).map((f) => {
      const u = prefixe + f;
      return v ? u + (u.indexOf("?") >= 0 ? "&" : "?") + "v=" + v : u;
    });
  }

  /** Ce que chaque morceau est censé POSER — pour vérifier une chaîne montée. */
  function poses(ensemble) {
    const veut = (m) => m.ens.indexOf("moteur") >= 0 || m.ens.indexOf(ensemble) >= 0;
    return MORCEAUX.filter(veut).map((m) => ({ f:m.f, pose:m.pose }));
  }

  /** Ce qui manque sur une racine donnée : dit QUOI, jamais « ça a raté ». */
  function manquants(ensemble, racine) {
    const r = racine || (typeof window !== "undefined" ? window : globalThis);
    return poses(ensemble).filter((p) => p.pose && !r[p.pose]).map((p) => p.f);
  }

  return { MORCEAUX, DERNIER, fichiers, urls, poses, manquants };
});
