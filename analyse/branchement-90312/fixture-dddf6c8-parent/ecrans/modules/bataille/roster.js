// roster.js — qui compose les corps, sous quel chef, avec quelle arme.
//
// ═══ CE FICHIER FAIT AUTORITÉ, LE DOSSIER EXPLIQUE ══════════════════════════
// `docs/bataille/roster/` dit POURQUOI ces chiffres ; celui-ci dit CE QU'ILS
// SONT, et c'est lui que la page et le moteur lisent. La distinction n'est pas
// bureaucratique : le dépôt s'est déjà fait prendre une fois — `docs/bataille/`
// se déclarait « l'autorité pour les effectifs, les noms et les humeurs »
// pendant que `bataille2d.js` en tenait une copie à la main, et l'on a relevé
// DIX divergences que personne n'avait vues (voir `docs/bataille/ecarts-code-
// dossier.md`). Une prose ne peut pas faire autorité sur des nombres : elle ne
// s'exécute pas.
//
// ═══ LE PRINCIPE — UNE UNITÉ SE DÉFINIT PAR LA FAÇON DONT ON LUI PARLE ══════
// Pas par un effectif de tableau. Le moteur a trois modes de transmission, aux
// coûts très différents, et chaque échelon en épouse exactement un :
//
//   LA VOIX      20 hommes au plus, il faut être là, ça marche toujours.
//   LE COUREUR   précis, mais coûte un homme, du temps, et peut ne pas arriver
//                — et la phrase perd ses subordonnées avant son verbe.
//   LA BANNIÈRE  gratuite et instantanée, mais TROIS CODES convenus d'avance :
//                dès que la tête veut du précis, elle ne sert plus à rien.
//
// Conséquence qui tombe de la structure, sans qu'on l'écrive : un ordre précis
// coûte UN COUREUR PAR CENTAINE. Un corps de 400 hommes en coûte quatre ; les
// 1 700 de l'assaut en coûtent dix-sept. C'est ça, la friction du commandement.
//
// ═══ ON NE MODÉLISE PAS UNE LIGNE ═══════════════════════════════════════════
// « Il ne faut pas modéliser une ligne, il faut modéliser des grappes qui se
// comportent comme une ligne tant que la cohésion tient. La ligne doit être un
// résultat, pas une contrainte. » (`docs/recherche/dynamiques-du-combat-
// medieval.md`, § 2.3.) D'où des vintaines, et pas des rangs.
"use strict";
(function (racine) {

  // ═══ LES ÉCHELONS ═════════════════════════════════════════════════════════
  // ⚠ LES DEUX PREMIERS EXISTENT DÉJÀ DANS LE MOTEUR, sous d'autres noms :
  // `PAR_ESC = 20` et `ESC_PAR_AILE = 5` donnent exactement 20 et 100. On ne
  // change donc aucune structure — on NOMME ce qui était anonyme, et l'on
  // attache à chaque échelon le mode de transmission qui lui revient.
  const ECHELONS = [
    { id: "vintaine", nom: "Vintaine", aussi: "conroi", hommes: 20,
      chef: "vintenar", monte: false, parle: "voix",
      dit: "L'échelle où vit la cohésion — l'attachement aux camarades, qui " +
           "maintient l'homme sur le champ, par opposition au moral, qui l'y " +
           "amène. Chaque homme a un chef immédiat et une poignée de voisins " +
           "qu'il connaît, et c'est tout. C'est elle qui rompt d'un bloc.",
      source: "Vintaine anglaise (commissions of array) : 19 hommes commandés " +
              "par le vingtième. Conroi : 6 à 25 cavaliers qui s'entraînent " +
              "et chargent ensemble." },
    { id: "centaine", nom: "Centaine", aussi: "chambre", hommes: 100,
      chef: "centenar", monte: true, parle: "coureur",
      dit: "Le seul échelon qu'un coureur peut trouver et rejoindre en un " +
           "temps raisonnable — parce que son chef est À CHEVAL. C'est donc " +
           "l'unité de commandement réelle, et l'unité de coût d'un ordre.",
      source: "Centaine anglaise : 5 vintaines sous un centenar, « lequel est " +
              "monté même quand ses hommes sont à pied, parce qu'il doit voir " +
              "et se déplacer »." },
    { id: "corps", nom: "Corps", aussi: "bataille", hommes: null,
      chef: "tête", monte: true, parle: "banniere",
      dit: "Entièrement AD HOC : sa taille dépend du besoin, pas d'un tableau " +
           "d'effectifs. Sa tête ne se bat pas. Après le contact, elle perd le " +
           "contrôle — ce qui lui reste est sa présence, sa voix, et la " +
           "réserve qu'elle a gardée.",
      source: "La « bataille » (angl. battle, ward) : division d'armée ad hoc. " +
              "Une armée de campagne est rangée en trois — avant-garde, corps " +
              "de bataille, arrière-garde." },
  ];

  // ═══ LES MÉTIERS — ET NON DES UNIFORMES ═══════════════════════════════════
  // Un « régiment de deux cents hommes identiques » n'existe pas. La lance
  // fournie de 1445 fait SIX hommes de quatre métiers ; la lance bourguignonne
  // de 1471 en fait neuf de six métiers. Le mélange EST l'unité.
  //
  // ⚠ LES SUBSTITUTIONS SONT ÉCRITES, PAS SUBIES. Le moteur n'a aucun combat à
  // distance : archers et arbalétriers — qui font la moitié d'une lance fournie
  // — ne peuvent pas exister. On ne les efface pas pour autant, parce qu'un
  // roster amputé en silence est un roster qu'on croira complet. Ils sont ici,
  // avec l'arme de remplacement qu'ils portent EN ATTENDANT et le champ
  // `substitut` qui dit ce qu'ils sont vraiment. Le jour où le tir existera, on
  // bascule ces lignes-là et rien d'autre.
  const METIERS = {
    "homme-darmes": {
      nom: "Homme d'armes", arme: "lance", teinte: "#b9b6a4",
      dit: "Le premier rang. Son allonge de 2,80 m décide plus que tout le " +
           "reste, parce qu'elle ne dit pas seulement qui touche : elle dit " +
           "QUI TOUCHE LE PREMIER." },
    "pieton": {
      nom: "Piéton", arme: "epieu", teinte: "#9c9a86",
      dit: "Le gros du rang, derrière la pointe. Deux mètres vingt : il engage " +
           "avant le coutelas et après la lance." },
    "coutilier": {
      nom: "Coutilier", arme: "coutelas", teinte: "#a89880",
      dit: "Les flancs, la poursuite, le pillage. Il doit traverser un mètre " +
           "et demi sous la pointe adverse pour avoir le droit de frapper — " +
           "il le fait sans le savoir, par le seul jeu de la colonne." },
    "hachier": {
      nom: "Hachier", arme: "hache", teinte: "#c98a5a",
      dit: "Peu nombreux, envoyés sur ce qui doit céder : une porte, une " +
           "brèche. Ouvre un homme d'un coup et reste découvert entre deux." },
    "vintenar": {
      nom: "Vintenar", arme: "epee", teinte: "#dcd2c0", chef: true,
      dit: "La meilleure garde de la table (0,78) — et il la lui faut : il " +
           "doit survivre ET être vu. Sa voix est le seul canal qui marche " +
           "au contact." },
    "piquier": {
      nom: "Piquier", arme: "pique", teinte: "#aeb49a", antiMonte: true,
      dit: "Quatre mètres de hampe : il ferme un axe tant que les pointes " +
           "restent tournées ensemble. Il gagne l'allonge et paie chaque pivot." },
    "cavalier": {
      nom: "Cavalier", arme: "lance", teinte: "#d1b06b", monte: true,
      dit: "Sa monture lui donne de la mobilité et de l'élan, pas un bonus " +
           "abstrait. Coincé dans une masse ou reçu par des pointes, il perd " +
           "précisément ce qu'il était venu acheter." },
    // --- ce que le moteur ne sait pas encore faire -------------------------
    "archer": {
      nom: "Archer", arme: "coutelas", teinte: "#8d8f76",
      substitut: "arc", chef: false,
      dit: "TROIS des six hommes d'une lance fournie. Sans combat à distance, " +
           "il porte le coutelas — ce qui est d'ailleurs ce qu'un archer tire " +
           "quand on lui tombe dessus. La conséquence est juste par accident : " +
           "une troupe qui en est pleine ne tient pas un seuil." },
    "arbaletrier": {
      nom: "Arbalétrier", arme: "coutelas", teinte: "#7f8474",
      substitut: "arbalete", chef: false,
      dit: "Même substitution que l'archer, et même réserve. Sa cadence lente " +
           "et son pouvoir de perforation n'existent pas encore." },
  };

  // ═══ LES FORMATIONS — et elles POSENT DES RONDS ═══════════════════════════
  // Chacune rend une liste de places, en mètres, avec le rang de chacune. Ce
  // n'est pas de l'illustration : c'est la géométrie qui décide combien
  // d'hommes peuvent frapper, et c'est le chiffre le plus structurant de toute
  // la recherche.
  //
  // Les espacements sont ceux du moteur : 0,55 m d'épaules, donc 0,75 m de
  // coude à coude en ordre serré et 1,0 m entre deux rangs.
  const LARG = 0.75, PROF = 1.0;

  const FORMATIONS = {
    ligne: {
      nom: "Ligne", dit: "Deux rangs. Large et peu profonde : la plus grande " +
           "part du monde peut frapper, et la plus grande part du monde peut " +
           "être frappée.",
      poser: (n) => {
        const l = Math.ceil(n / 2), p = [];
        for (let i = 0; i < n; i++) {
          const rang = Math.floor(i / l), col = i % l;
          p.push({ x: (col - (l - 1) / 2) * LARG, y: rang * PROF, rang });
        }
        return p;
      } },
    colonne: {
      nom: "Colonne", dit: "Étroite et profonde. On la prend pour aller " +
           "quelque part, pas pour tenir un front — et de fait presque " +
           "personne n'y peut frapper.",
      poser: (n) => {
        const l = 4, p = [];
        for (let i = 0; i < n; i++) {
          const rang = Math.floor(i / l), col = i % l;
          p.push({ x: (col - (l - 1) / 2) * LARG, y: rang * PROF, rang });
        }
        return p;
      } },
    carre: {
      nom: "Carré (hérisson)", dit: "Quatre rangs de pointes. Six pour cent " +
           "des hommes touchent quelque chose — c'est le prix de ne pas " +
           "pouvoir être tourné.",
      poser: (n) => {
        const l = Math.max(2, Math.round(Math.sqrt(n))), p = [];
        for (let i = 0; i < n; i++) {
          const rang = Math.floor(i / l), col = i % l;
          p.push({ x: (col - (l - 1) / 2) * LARG, y: rang * PROF, rang });
        }
        return p;
      } },
    nuee: {
      nom: "Nuée", dit: "Pas de rang du tout. Chacun est son propre premier " +
           "rang, ce qui veut dire que chacun est aussi son propre flanc.",
      poser: (n) => {
        // Un semis déterministe — même unité, même dessin, toujours.
        const p = [];
        for (let i = 0; i < n; i++) {
          const a = i * 2.39996, r = 0.9 * Math.sqrt(i + 0.5);
          p.push({ x: Math.cos(a) * r, y: Math.sin(a) * r + 1.4, rang: 0 });
        }
        return p;
      } },
    tas: {
      nom: "Tas", dit: "Ce qu'une formation devient dans un goulet : plus de " +
           "rangs, plus de coudes, et personne ne peut plus reculer d'un pas.",
      poser: (n) => {
        const p = [];
        for (let i = 0; i < n; i++) {
          const rang = Math.floor(i / 5), col = i % 5;
          p.push({ x: (col - 2) * 0.62 + (rang % 2) * 0.31, y: rang * 0.7, rang });
        }
        return p;
      } },
    aucune: {
      nom: "Aucune", dit: "Unité de COMPTE et non de combat : ses hommes se " +
           "répartissent dans trois formations différentes une fois sur le " +
           "terrain. C'est elle qui interdit le « régiment uniforme ».",
      poser: (n) => {
        const p = [];
        for (let i = 0; i < n; i++) p.push({ x: (i - (n - 1) / 2) * 1.1, y: 0, rang: 0 });
        return p;
      } },
  };

  // ═══ LE CATALOGUE GÉNÉRIQUE ═══════════════════════════════════════════════
  // CE QUI ÉLARGIT AU-DELÀ D'UNE SEULE NUIT. Les corps de la Gadoue plus bas
  // ne sont qu'UNE composition ; ceci est la liste de ce qu'on peut aligner.
  //
  // `simule` est le champ qui empêche de se mentir :
  //   "oui"       le moteur sait tout faire de cette unité ;
  //   "substitue" elle existe, avec une arme de remplacement écrite ;
  //   "non"       rien n'en est simulé — on l'inscrit pour ne pas l'oublier,
  //               et on ne s'en sert pas.
  const TYPES = [
    { n: 1, id: "pied", nom: "Vintaine de pied", hommes: 20, simule: "oui",
      composition: { "vintenar": 1, "homme-darmes": 5, "pieton": 9, "coutilier": 4, "hachier": 1 },
      formation: "ligne",
      pour: "Tenir un front. Le cas ordinaire, et l'unité de mesure de tout le reste.",
      source: "Vintaine anglaise : 19 hommes commandés par le vingtième." },

    { n: 2, id: "pique", nom: "Vintaine de pique", hommes: 20, simule: "oui",
      composition: { "vintenar": 1, "piquier": 19 },
      formation: "carre",
      capacites: { longueHampe: true, antiMonte: true },
      pour: "Tenir contre du cheval, ou tenir un carrefour. Ne manœuvre pas.",
      source: "La colonne suisse à vingt rangs n'engage que 5 % de ses hommes." },

    { n: 3, id: "hache", nom: "Vintaine de hache", hommes: 20, simule: "oui",
      composition: { "vintenar": 1, "hachier": 15, "pieton": 4 },
      formation: "colonne",
      pour: "Ouvrir une porte, une brèche, une barricade. Elle ne tient rien.",
      source: "Les hommes de Vantre, dont le dossier dit qu'ils « valent " +
              "double contre le verrou »." },

    { n: 4, id: "trait", nom: "Vintaine de trait", hommes: 20, simule: "substitue",
      composition: { "vintenar": 1, "archer": 16, "pieton": 3 },
      formation: "ligne",
      pour: "Rien, aujourd'hui. Sans combat à distance elle est une vintaine " +
            "de coutelas déguisée — on la garde parce qu'une case vide est une " +
            "intention visible, et parce qu'elle sera juste le jour du tir.",
      source: "Trois des six hommes d'une lance fournie sont archers." },

    { n: 5, id: "levee", nom: "Vintaine de levée", hommes: 20, simule: "oui",
      composition: { "vintenar": 1, "coutilier": 15, "pieton": 4 },
      formation: "nuee",
      pour: "Le nombre, le flanc, la poursuite, le pillage. Ne tient pas un seuil.",
      source: "Ce qu'on ramasse — les gueux de Cantel, les bleusailles." },

    { n: 6, id: "lance-fournie", nom: "Lance fournie", hommes: 6, simule: "substitue",
      composition: { "homme-darmes": 1, "coutilier": 1, "archer": 3, "pieton": 1 },
      formation: "aucune",
      pour: "Compter et payer, pas combattre. Ses six hommes se dispersent " +
            "dans trois formations différentes une fois sur le terrain.",
      source: "Ordonnance française de 1445 : 1 homme d'armes, 1 coutilier, " +
              "1 page, 3 archers. Le page est ici un piéton, faute de non-combattants." },

    { n: 7, id: "conroi", nom: "Conroi", hommes: 12, simule: "oui",
      composition: { "vintenar": 1, "cavalier": 11 },
      formation: "ligne",
      capacites: { monte: true, mobile: true, choc: true },
      pour: "Reconnaître, menacer un flanc, poursuivre ou charger avec de " +
            "l'espace. Sa puissance dépend de son élan et de ce qu'il rencontre.",
      source: "Conroi : 6 à 25 cavaliers, qui s'entraînent ET chargent ensemble." },
  ];

  /**
   * LA FIGURE LITTÉRALE — un rond par homme, avec son métier et son rang.
   *
   * L'ordre de placement n'est pas décoratif : les armes LONGUES vont devant,
   * parce que l'allonge décide qui touche le premier. Le vintenar prend la
   * droite du premier rang — il doit survivre et être vu.
   */
  function figurer(id) {
    const t = TYPES.filter((x) => x.id === id)[0];
    if (!t) return null;
    const f = FORMATIONS[t.formation] || FORMATIONS.aucune;
    const places = f.poser(t.hommes);
    // Les métiers, du plus long fer au plus court — le vintenar mis à part.
    const ordre = Object.keys(t.composition)
      .filter((m) => m !== "vintenar")
      .sort((a, b) => (PORTEE[METIERS[b].arme] || 0) - (PORTEE[METIERS[a].arme] || 0));
    const file = [];
    if (t.composition["vintenar"]) file.push("vintenar");
    for (const m of ordre) for (let i = 0; i < t.composition[m]; i++) file.push(m);
    const rangMax = places.reduce((m, p) => Math.max(m, p.rang), 0);
    const ronds = places.map((p, i) => {
      const metier = file[i] || "pieton";
      return { x: p.x, y: p.y, rang: p.rang, metier, engage: engage(metier, p.rang, t) };
    });
    const engages = ronds.filter((r) => r.engage).length;
    return {
      type: t, formation: f, ronds, rangs: rangMax + 1,
      engages, partEngagee: engages / (t.hommes || 1),
    };
  }

  // L'allonge de chaque arme — recopiée de `bataille/mesures.js` UNIQUEMENT
  // pour trier les rangs et dire qui touche. Si les deux divergent, c'est
  // l'affichage qui est faux, jamais le combat : rien ici n'entre dans la
  // simulation.
  const PORTEE = { pique: 4.2, lance: 2.8, epieu: 2.2, hache: 1.5, epee: 1.4, coutelas: 0.9 };
  const CONTACT = 1.4;      // la distance à laquelle deux fronts se touchent

  /**
   * QUI PEUT FRAPPER — DÉRIVÉ DE L'ARME, JAMAIS DÉCLARÉ.
   *
   * ⚠ La première version portait un champ `rangsEngages` écrit à la main, et
   * il mentait tout de suite : une ligne sur deux rangs annonçait « 100 % des
   * hommes engagés », ce qui est absurde. Le nombre de rangs qui touchent n'est
   * pas une propriété de la formation — c'est une propriété du FER que tient
   * l'homme, à la profondeur où il se trouve.
   *
   * Un homme au rang `r` est à `r × 1,0 m` derrière le front. Il touche si son
   * allonge dépasse encore la distance de contact une fois ce recul retranché.
   * D'où, mécaniquement : une lance frappe du deuxième rang (2,8 − 1,0 = 1,8),
   * un épieu non (2,2 − 1,0 = 1,2), et rien ne frappe du troisième.
   *
   * C'est ce qui rend la figure INTÉRESSANTE plutôt que décorative : dans une
   * vintaine de pied, le deuxième rang est un mélange de lances qui touchent et
   * d'épieux qui attendent — on voit les pleins et les creux alterner dans le
   * même rang, ce qu'aucun pourcentage global ne dirait.
   */
  function engage(metier, rang, type) {
    if (type.formation === "nuee") return true;   // pas de rang : chacun est son front
    if (type.formation === "aucune") return false; // unité de compte, pas de combat
    const a = PORTEE[(METIERS[metier] || {}).arme] || 0;
    return a - rang * PROF >= CONTACT;
  }

  // ═══ LES RECETTES — une par corps, sur vingt hommes ═══════════════════════
  // C'est ici que le dessin des cinq corps devient MÉCANIQUE au lieu d'être un
  // adjectif. Cranche « le ferme » tient parce qu'il a huit lances au premier
  // rang ; les bleusailles ne tiennent pas parce qu'ils n'en ont aucune. On ne
  // leur câble aucun malus : la composition suffit, et elle se voit.
  //
  // Chaque recette totalise 20, vintenar compris.
  const RECETTES = {
    cranche:     { "vintenar": 1, "homme-darmes": 8, "pieton": 9, "coutilier": 1, "hachier": 1 },
    cole:        { "vintenar": 1, "homme-darmes": 5, "pieton": 9, "coutilier": 3, "archer": 1, "hachier": 1 },
    // Le dossier dit que « contre le verrou, ses hommes valent double » : c'est
    // par les haches que ça doit passer, et non par un coefficient.
    vantre:      { "vintenar": 1, "homme-darmes": 4, "pieton": 8, "coutilier": 3, "hachier": 4 },
    gueux:       { "vintenar": 1, "homme-darmes": 0, "pieton": 6, "coutilier": 8, "archer": 4, "hachier": 1 },
    bleusailles: { "vintenar": 1, "homme-darmes": 0, "pieton": 5, "coutilier": 10, "archer": 4, "hachier": 0 },
    garde:       { "vintenar": 1, "homme-darmes": 6, "pieton": 9, "coutilier": 1, "arbaletrier": 2, "hachier": 1 },
  };

  // Les corps, tels que `bataille2d.js` les pose — on ne redéfinit PAS leurs
  // effectifs ici, on les cite pour pouvoir composer. Toute divergence avec le
  // moteur est un défaut, pas une variante.
  const CORPS = [
    { id: "cole",        nom: "Ser Criston Cole",   hommes: 500, camp: "assaut" },
    { id: "vantre",      nom: "Ser Loryn Vantre",   hommes: 350, camp: "assaut" },
    { id: "cranche",     nom: "Ser Ormond Cranche", hommes: 250, camp: "assaut" },
    { id: "gueux",       nom: "le sergent Rous Cantel", hommes: 400, camp: "assaut" },
    { id: "bleusailles", nom: "Petit Wend",         hommes: 200, camp: "assaut" },
    { id: "garde",       nom: "le Guet de Port-Réal", hommes: 800, camp: "garde" },
  ];

  /**
   * Ce que devient un corps une fois assemblé : centaines, vintaines, métiers.
   *
   * ⚠ LA DERNIÈRE VINTAINE EST EN SOUS-EFFECTIF, ET C'EST VOULU. Vantre fait
   * 350 hommes, soit dix-sept vintaines pleines et dix hommes qui restent.
   * Arrondir à dix-huit fabriquerait dix hommes qui n'existent pas ; les jeter
   * en perdrait dix. Une unité est presque toujours en sous-effectif — on garde
   * donc le reste comme une vintaine incomplète, avec son vintenar quand même,
   * parce qu'un chef à neuf hommes reste un chef et que c'est justement le
   * genre d'unité qui casse en premier.
   */
  function assembler(id) {
    const c = CORPS.filter((x) => x.id === id)[0];
    const r = RECETTES[id];
    if (!c || !r) return null;
    const pleines = Math.floor(c.hommes / 20);
    const reste = c.hommes - pleines * 20;
    const vintaines = pleines + (reste > 0 ? 1 : 0);
    const centaines = Math.max(1, Math.round(vintaines / 5));
    const par = {};
    let total = 0;
    for (const m in r) { par[m] = r[m] * pleines; total += par[m]; }
    if (reste > 0) {
      // Le chef d'abord — c'est ce qui fait d'un reliquat une unité —, puis la
      // recette au prorata, et le drift de l'arrondi tombe sur les piétons,
      // qui sont le gros du rang et la variable d'ajustement naturelle.
      const ordre = Object.keys(r).sort((a, b) => (r[b] || 0) - (r[a] || 0));
      if (r["vintenar"]) { par["vintenar"] = (par["vintenar"] || 0) + 1; total++; }
      for (const m of ordre) {
        if (m === "vintenar" || total >= c.hommes) continue;
        const n = Math.min(Math.round(r[m] * reste / 20), c.hommes - total);
        par[m] = (par[m] || 0) + n; total += n;
      }
      if (total < c.hommes) { par["pieton"] = (par["pieton"] || 0) + (c.hommes - total);
                             total = c.hommes; }
    }
    return {
      corps: c.id, nom: c.nom, camp: c.camp, hommes: c.hommes,
      centaines, vintaines, pleines, reste, metiers: par, total,
      // Combien de coureurs pour un ordre PRÉCIS à tout le corps : un par
      // centaine, parce que la bannière ne porte que ses trois codes.
      coureursPourUnOrdre: centaines,
    };
  }

  const tout = () => CORPS.map((c) => assembler(c.id)).filter(Boolean);

  racine.BatailleRoster = { ECHELONS, METIERS, FORMATIONS, TYPES, PORTEE,
                            RECETTES, CORPS, figurer, assembler, tout };
  if (typeof module === "object" && module.exports) module.exports = racine.BatailleRoster;

})(typeof window !== "undefined" ? window : globalThis);
