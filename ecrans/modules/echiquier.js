// echiquier.js — « L'échiquier », une échelle du décor, ouverte PARTOUT.
//
// Il l'a longtemps été dans la seule salle de la Table Peinte, au motif que les
// affaires sont un outil de cette table-là. C'était vrai de l'objet et faux de
// l'usage : on décide dans l'escalier, on se souvient au quai, et une ligne de
// jeu qu'on ne peut pas relire là où l'on est n'est pas relue du tout. La
// disponibilité ne dépend donc plus ni du lieu, ni du chargement, ni du fait
// qu'une affaire soit déjà visible pour ce siège. L'entrée reste dans la barre
// partout dans la ville ; le plateau sait déjà rendre son état vide.
//
// La table peinte dit OÙ porte la guerre. L'échiquier dit COMMENT ce qu'on a
// devient ce qu'on veut — et il le dit avec le vocabulaire de la maison, celui
// du guide « Comment on ouvre une affaire », posé sur cette table même. Sept
// objets, pas un de plus, et leurs signes viennent du guide :
//
//   🏰 l'affaire      le conteneur de travail du conseil ; elle ne dit rien du
//                     monde, elle rassemble. Un plateau = une affaire.
//   🎯 l'état cible   ce qui doit devenir vrai dans le monde. Une colonne.
//   🔒 le verrou      le fait du monde qui empêche un état de tenir
//   🗝️ la clef        le mécanisme envisagé pour lever un verrou
//   ⚔️ l'action       ce qu'on décide effectivement de faire
//   🔨 le moyen       ce qu'on peut employer — cité, jamais créé
//   🪶 l'office       l'autorité sous laquelle une action est portée
//
// DESCENDRE, de haut en bas : que voulons-nous, qu'est-ce qui nous en empêche,
// comment le lèverait-on, que faisons-nous, avec quoi et sous quelle autorité.
// Le damier se lit donc de bas en haut, et c'est l'autre épreuve du guide —
// REMONTER : « depuis n'importe quelle action, la clef, le verrou, l'état
// cible, l'affaire. Si la remontée est impossible, l'action n'a pas de raison
// stratégique démontrée. » Une colonne qui ne descend jusqu'à aucune action se
// voit ici sans qu'on la cherche : sa réglette est rouge et son état cible
// porte le fanion. C'est ce que cette vue apporte, et c'est pour ça qu'elle
// existe.
//
// RIEN N'EST ÉCRIT ICI NI DANS AUCUN FICHIER D'ÉTAT : tout vient des six
// registres par type de `books.json`, dérivés par la route `/echiquier`. Le
// guide tranche — « quand l'affaire et le registre se contredisent, c'est le
// registre qui a raison ». Une vue qui recopierait le plan serait un mensonge
// en attente.
//
// AUCUN TEXTE SUR LE PLATEAU. Le damier est une position, et une position se
// regarde : des cases carrées et toutes égales, un jeton par pièce, des traits
// entre les rangs. Le plateau est PLEIN DE SA CASE — il prend tout
// l'emplacement du décor qu'on lui donne, et c'est la taille de la case qui se
// calcule sur la place, jamais la case qui s'étire.
//
// Tout ce qui s'écrit — le nom, ce que la pièce dit, sa preuve, son coût, où
// elle en est, les fautes — vit dans l'encart qui s'ouvre au survol. Le CLIC,
// lui, ouvre le volume de l'affaire dans les livres : c'est là qu'on travaille,
// et le plateau n'est qu'une manière de le regarder.
//
// LA FORME AVANT LA COULEUR, et la grammaire n'est pas de moi : elle vient des
// pièces de bois de `nappe.js` — tuile à huit côtés pour une affaire, rectangle
// pour un état cible, hexagone pour un verrou, losange pour une clef, barrette
// pour une action, rond pour un moyen, carré épais pour un office. Le sceau
// porte la silhouette, l'emoji porte le sens.
//
// L'occlusion, enfin, et elle se dit dans le vocabulaire du guide : UN ÉTAT
// CIBLE NE SE VOIT QUE PAR LES BRÈCHES DE SES VERROUS. Une dalle par verrou ;
// la brèche s'ouvre quand une clef RETENUE est écrite contre ce verrou-là, et
// pas avant. Un état à un verrou sans clef retenue est muré : on sait qu'on le
// veut, on ne peut pas encore le lire.
"use strict";
window.Echiquier = (() => {
  let affaires = [];       // toutes les affaires dérivées des registres
  let portraits = {};      // les visages, servis une fois chacun et partagés
  let missions = {};       // le catalogue des actes, servi à part et partagé
  let courante = null;     // celle qu'on a sous les yeux
  let charge = false;
  let epingle = null;      // la pièce dont l'encart est retenu
  let dessine = "";        // signature du dernier tracé

  const MEMOIRE = "conseil-echiquier-affaire";

  // Les cinq rangs, du haut vers le bas — l'ordre de la DESCENTE du guide. Le
  // premier n'est pas un rang de cases : les états cibles sont un ARBRE, et il
  // se dessine en canopée au-dessus du damier (voir CANOPEE plus bas).
  const CIME = { id: "etat", nom: "Les états cibles",
    sous: "ce qui doit devenir vrai dans le monde — un arbre, selon ce que chacun sert" };
  const RANGS = [
    { id: "verrou", nom: "Les verrous", sous: "le fait du monde qui empêche un état de tenir" },
    { id: "clef", nom: "Les clefs", sous: "le mécanisme envisagé pour lever un verrou" },
    { id: "action", nom: "Les actions", sous: "ce qu'on décide effectivement de faire" },
    { id: "moyen", nom: "Les moyens et les offices", sous: "avec quoi, et sous quelle autorité" },
  ];
  // La hauteur d'un étage de canopée, en part de case. Un jeton y tient au
  // large : la canopée porte des signes, pas des semis.
  const BANDE = 0.46;

  // ---- ce qui sort du cahier ------------------------------------------------
  // Quatre sens, deux directions. AMONT est ce à quoi cette pièce SERT — la
  // chaîne continue au-dessus, chez quelqu'un d'autre ; AVAL est ce dont elle
  // DÉPEND — le travail qui la débloquerait se fait ailleurs. La phrase est
  // écrite du point de vue de la pièce qu'on regarde, jamais de l'autre côté.
  // La phrase est celle du COMPTE, jamais d'une pièce : « 11 états servis »,
  // pas « sert 🎯 26000 ». On dit à qui l'on tient et à quel titre ; la pièce
  // exacte se lit au cahier, qui est à un clic.
  const SENS = {
    sert: ["état qu'elle sert là-bas", "états qu'elle sert là-bas"],
    attendue: ["pièce d'ici qu'on y attend", "pièces d'ici qu'on y attend"],
    servie: ["état de là-bas qui la sert", "états de là-bas qui la servent"],
    attend: ["pièce de là-bas qu'elle attend", "pièces de là-bas qu'elle attend"],
  };
  const compte = (n, s) => n + " " + SENS[s][n > 1 ? 1 : 0];
  // Combien de voisines la rangée montre au plus. Au-delà, un compte : vingt
  // emblèmes muets ne se lisent pas mieux que le chevron qu'on a retiré.
  const SORTIES = 6;

  // ---- les signes -----------------------------------------------------------
  // Ceux du guide, et pas d'autres : c'est la maison qui les a choisis, ils sont
  // déjà dans les registres, et le joueur les a sous les yeux quand il ouvre le
  // livre. Écrits en séquences d'échappement pour qu'aucun outil ne les abîme.
  const SIGNES = {
    affaire: "\u{1F3F0}",     // la tuile du conseil
    etat: "\u{1F3AF}",        // la cible
    verrou: "\u{1F512}",      // le cadenas fermé
    verrou_perce: "\u{1F513}", // le même, une clef retenue contre lui
    clef: "\u{1F5DD}\uFE0F",  // la clef ancienne
    action: "\u2694\uFE0F",   // les épées croisées
    moyen: "\u{1F528}",       // le marteau
    office: "\u{1FAB6}",      // la plume
  };
  function icone(nom, classe) {
    const s = SIGNES[nom];
    if (!s) return "";
    return '<span class="ech-icone ' + (classe || "") + '" aria-hidden="true">' + s + "</span>";
  }
  function glyphe(p) {
    // UNE ACTION PORTE LE VISAGE DE QUI LA TIENT. C'est la seule chose qu'on
    // veuille lire après « qu'est-ce qu'on fait » : QUI le fait. Le portrait
    // vient inliné du serveur, jamais d'une URL — la page ne charge aucune
    // ressource externe. Faute de teneur rattaché (un office vide, à désigner,
    // ou un nom qu'on ne reconnaît pas), on garde les épées : l'absence est déjà
    // une faute chez nous, et elle devient très lisible quand tous les autres
    // jetons ont un visage.
    if (p.genre === "action" && p.teneur_id && portraits[p.teneur_id]) {
      return '<span class="ech-visage" aria-hidden="true">' + portraits[p.teneur_id] + "</span>";
    }
    if (p.genre === "verrou") return icone(p.breche ? "verrou_perce" : "verrou");
    if (p.genre === "affaire" && p.embleme) {
      return '<span class="ech-icone" aria-hidden="true">' + p.embleme + "</span>";
    }
    return icone(p.genre);
  }

  // L'EMBLÈME D'UNE AFFAIRE EST CELUI DE SON VOLUME, servi par la route et
  // choisi par la maison — jamais un signe qu'on prendrait ici. Une affaire dont
  // aucun volume ne porte le nom garde le signe générique du guide, et cette
  // absence est une information : c'est un cahier qui reste à ouvrir.
  function signe(x) {
    return x.embleme
      ? '<span class="ech-icone" aria-hidden="true">' + x.embleme + "</span>"
      : icone("affaire");
  }

  // Ce qu'on montre au survol d'une affaire : son signe, son nom, et l'OBJET
  // que son volume écrit — « pourquoi cette affaire mérite l'attention du
  // conseil ». On ne compose rien : faute d'objet écrit, on ne dit rien.
  function surAffaire(x) {
    return { genre: "affaire", cle: null, embleme: x.embleme, nom: x.titre,
      dit: x.objet, affaire_id: x.id,
      mal: x.rompues ? x.rompues + (x.rompues > 1
        ? " états cibles ne descendent jusqu'à aucune action"
        : " état cible ne descend jusqu'à aucune action") : null };
  }

  function hote() { return document.getElementById("echiquier"); }
  const affaire =() => affaires.find((a) => a.id === courante) || affaires[0] || null;

  function ligne(classe, texte) {
    const d = document.createElement("div");
    d.className = classe;
    d.textContent = texte;
    return d;
  }

  // ---- l'état d'une montée -------------------------------------------------
  // LE ROUGE NE DIT PLUS QUE LA RUPTURE, et c'est la correction du 13e. Le
  // plateau confondait un plan INCOMPLET avec du TRAVAIL EN COURS : une chaîne
  // entière — état, verrou, clef retenue, action écrite, teneur nommé — qui
  // n'attend plus que d'être exécutée portait exactement les mêmes signaux
  // d'alarme qu'une colonne qui ne descend nulle part. Or c'est un plan qui
  // marche, et c'est l'état normal et souhaitable d'un plan vivant.
  //
  //   ROUGE — il manque une pièce, la REMONTÉE est cassée : une référence qui
  //           ne résout pas, une colonne où aucune action ne descend, une
  //           action que personne ne porte. Le serveur le dit par `rupture`,
  //           et lui seul (voir /echiquier) : on ne devine plus la gravité en
  //           lisant la prose d'une faute.
  //   ENCRE — la marche est payée : ce rang-là de la chaîne tient, dans la
  //           monnaie que le guide lui donne. C'est le plus fréquent, et ce
  //           n'est PAS du vert — voir plus bas.
  //   OR    — une clef à étudier. Ni faute ni travail : une DÉCISION qui attend
  //           le joueur, et la seule chose du plateau qui lui soit adressée.
  //   GRIS  — il manque une ligne à écrire à la plume (une preuve, un « levé
  //           quand », un numéro d'office). La LAMPE dit déjà ce qu'il y a à
  //           faire ; le trait n'a pas à s'en alarmer par-dessus.
  //
  // ET LE VERT NE VIT PAS SUR LES MARCHES. Une chaîne complète sur le papier
  // n'est pas du travail : « le plan est bien écrit » et « quelqu'un le porte »
  // sont deux choses, et c'est la seconde qui vaut d'être vue. Le vert est donc
  // réservé aux deux endroits qui peuvent l'affirmer — le jeton d'une ACTION
  // qu'un homme a déclarée en cours dans son cahier, et la RÉGLETTE d'une
  // colonne dont au moins une action est déclarée telle. Tout le reste, si
  // propre soit-il, est ÉCRIT ET PAS PORTÉ, et se lit à l'encre ordinaire.
  function rompt(p) { return !!p.rupture; }

  function etatMarche(p) {
    if (rompt(p)) return "saut";
    if (p.genre === "clef") {
      return p.tenue === "retenue" ? "payee"
        : p.tenue === "ecartee" ? "ecartee" : "decision";
    }
    return p.paie ? "payee" : "attente";
  }
  // Les cinq états de marche, dans l'ordre où on les déclare au tracé.
  const MARCHES = ["payee", "attente", "decision", "ecartee", "saut"];

  // PORTÉ : un homme a écrit de sa main, dans la colonne ⏳ État de son cahier,
  // que la chose est en cours ou faite. C'est déclaratif et ça se revendique —
  // c'est exactement ce qu'il dirait au conseil, et le joueur peut aller ouvrir
  // le volume pour le lire. `paie` ne vaut, pour une action, que cela.
  const porte = (p) => p.genre === "action" && !!p.paie && !rompt(p);

  // ---- un jeton ------------------------------------------------------------
  // Le dernier chiffre du numéro d'une pièce — « 28001 » donne 1, « M12 »
  // donne 2. Rien si la pièce n'est pas numérotée.
  function chiffre(p) {
    const n = String(p.numero == null ? "" : p.numero);
    const m = n.match(/(\d)(?!.*\d)/);
    return m ? m[1] : "";
  }

  function jeton(p) {
    const b = document.createElement("button");
    b.type = "button";
    // LE PROCHAIN PAS. Une pièce que vise un acte n'est pas une pièce comme les
    // autres : c'est là que ça débloque, et sur un plateau de cinquante-quatre
    // jetons elle doit se trouver SANS être cherchée. La lampe la nomme ; cette
    // classe la fait sauter aux yeux de loin, dalles d'occlusion comprises.
    //
    // DEUX ESPÈCES, DEUX MARQUES, et la différence se voit SANS SURVOLER —
    // c'est tout l'objet de ce partage. Ce que nos six détecteurs trouvent est
    // presque toujours de la TENUE DE REGISTRE : exhaustif, gratuit à trouver,
    // et de faible valeur. Un seul d'entre eux commande un travail qu'aucun
    // calcul ne pourra faire à notre place — « trouver ce qui empêche », quand
    // un état cible n'a pas un seul verrou écrit contre lui. Celui-là n'est pas
    // une case à cocher : c'est UNE DÉPÊCHE À LANCER, un homme à envoyer vivre
    // sa journée, et ce qu'il rapportera s'écrira comme un verrou au cahier.
    // Le mécanique reprendra alors la main pour dire ce qui manque autour : il
    // est l'aval du narratif, jamais son concurrent.
    const actes = (p.lampe || []).map((a) => missions[a]).filter(Boolean);
    const depeches = actes.filter((m) => m.espece === "narratif");
    const tenues = actes.filter((m) => m.espece !== "narratif");
    b.className = "ech-pion ech-g-" + p.genre +
      (tenues.length ? " ech-pas" : "") +
      (depeches.length ? " ech-quete" : "") +
      (p.genre === "verrou" ? (p.breche ? " ech-perce" : " ech-scelle") : "") +
      (p.genre === "clef" ? " ech-clef-" + (p.tenue || "etudier") : "") +
      // LE FANION EST RÉSERVÉ À LA RUPTURE. Une pièce qui manque d'une preuve
      // ou d'un numéro d'office n'est pas en faute : elle est mal tenue, et
      // c'est la lampe qui le dit. Le reste de ses `fautes` se lit dans la
      // bulle, en note, sans crier.
      (rompt(p) ? " ech-faute" : "") +
      // LE VERT — et il ne dit qu'une chose : un homme a déclaré porter cette
      // action. Écrit et pas porté ne prend rien : c'est le cas de l'immense
      // majorité du plan, et c'est la vérité.
      (porte(p) ? " ech-porte" : "") +
      // ET LE VERT VRAI, par-dessus : l'action est dans les ÉTAPES de la tête
      // de son teneur, avec son horloge. « Il dit qu'il le fait » et « c'est
      // dans sa tête » ne sont pas la même chose, et l'on doit pouvoir les lire
      // séparément. Aujourd'hui aucune étape ne cite un numéro d'action : ce
      // liseré ne se posera nulle part, et c'est l'information.
      (p.dans_la_tete ? " ech-tete" : "");
    b.dataset.piece = p.cle;
    b.setAttribute("aria-label", p.nom || p.cle);

    const sceau = document.createElement("span");
    sceau.className = "ech-sceau";
    sceau.innerHTML = glyphe(p);

    if (p.genre === "etat") {
      // L'occlusion : une dalle par verrou, posée sur la cible. On ne montre
      // pas ce qu'on ne possède pas — et l'on ne possède un état cible que par
      // les brèches qu'on a ouvertes dans ce qui l'empêche.
      const parts = p.part || [];
      const dalles = document.createElement("span");
      dalles.className = "ech-dalles";
      dalles.style.setProperty("--n", parts.length || 1);
      (parts.length ? parts : [{ breche: true }]).forEach((v) => {
        const dl = document.createElement("i");
        dl.className = "ech-dalle" + (v.breche ? " ech-dalle-levee" : "");
        dalles.appendChild(dl);
      });
      sceau.appendChild(dalles);
      const n = parts.filter((v) => v.breche).length;
      b.classList.add(!parts.length || n === parts.length ? "ech-but-ouvert"
        : n === 0 ? "ech-but-mure" : "ech-but-entrouvert");
    }
    // LE CHIFFRE DE LA PIÈCE, sur le sceau. Le plateau est muet par principe —
    // aucun mot dans une case —, mais un chiffre n'est pas un mot : c'est un
    // NOM COURT. Sans lui, on désigne un jeton en le montrant du doigt ; avec
    // lui, on dit « le verrou 3 » et l'on parle du plan sans l'avoir sous les
    // yeux. Le dernier chiffre du numéro, et pas davantage.
    //
    // CE QU'IL VAUT, MESURÉ, parce qu'il ne faut pas s'en faire une idée
    // fausse : dans une colonne-verrou et un rang donnés, il est unique sur
    // « L'entrée au donjon » (0 doublon sur 65) mais pas sur « Financement de
    // la campagne » (13 sur 78) — là, un seul verrou porte seize actions, et
    // les numéros repassent par le même chiffre tous les dix. C'est donc un nom
    // court pour se parler d'une case à l'autre, jamais une clef.
    // Une pièce sans numéro — un office — n'en porte aucun.
    // Il se pose sur le JETON et non dans le sceau : cinq des sept silhouettes
    // sont découpées au ciseau (six pans, losange, barrette), et un coin de
    // sceau est précisément ce que le découpage emporte.
    b.appendChild(sceau);
    const num = chiffre(p);
    if (num) {
      const n = document.createElement("i");
      n.className = "ech-chiffre";
      n.textContent = num;
      b.appendChild(n);
    }

    // Le fanion des fautes. Il DOIT se repérer sans survol — c'est là toute son
    // utilité : une action qui ne remonte à rien, un état où rien ne descend,
    // un moyen cité qui n'est à aucun registre.
    if (rompt(p)) {
      const f = document.createElement("i");
      f.className = "ech-fanion";
      b.appendChild(f);
    }

    // LA LAMPE — une pièce sous laquelle il y a quelque chose à faire le dit
    // sans qu'on la survole, comme le fanion dit la faute. Un point rouge dit
    // « il y a un problème » ; une lampe dit « voilà ce qu'il y a à faire », et
    // c'est toute la différence entre un plateau qui accuse et un plateau qui
    // sert. Elle se pose AU-DESSUS des dalles d'occlusion : un état muré doit
    // montrer la sienne, c'est même celui-là qui en a le plus besoin.
    //
    // ELLE NE REMPLACE PAS LE FANION, et la mesure l'a tranché : les deux
    // ensembles ne coïncident pas. 53 pièces portent une faute sans aucune
    // mission — un moyen ou un office cité dans une action et absent de son
    // registre, pour quoi le catalogue n'a pas d'acte —, et 57 portent une
    // mission sans faute propre : un état dont la chaîne descend jusqu'à une
    // clef qu'on n'a pas tranchée n'est pas en faute, il attend une décision.
    // Les deux signes disent donc deux choses différentes.
    //
    // UNE PAR ACTE, ET SUR LA SEULE PIÈCE QU'IL VISE. Marquer toute pièce dont
    // la chaîne descendante porte une mission couvrait le plateau de lampes qui
    // disaient toutes la même chose : un même acte allumait l'état cible, son
    // verrou et l'action qui l'avait fait voir. C'est la déduplication par
    // l'acte, déjà faite pour les missions, appliquée au marquage — le serveur
    // range dans `lampe` les actes qui visent CETTE pièce, et rien d'autre. Les
    // pièces d'amont continuent de dire la mission dans leur bulle, ce qui est
    // sa place.
    //
    // ET ELLE NE DIT PLUS QU'UNE ESPÈCE. 💡 reste ce qu'elle a toujours été —
    // ce qu'il y a à écrire ou à trancher au registre. 📯 est l'autre : une
    // dépêche, un homme à envoyer chercher ce que nul calcul ne trouvera. Deux
    // signes, deux coins, deux couleurs (voir jeu.css) : c'est la seule façon
    // que le joueur voie la différence sans rien survoler, et c'est la seule
    // qu'on lui demande de voir.
    const marque = (classe, signe, liste) => {
      if (!liste.length) return;
      const l = document.createElement("i");
      l.className = classe;
      l.textContent = signe;
      // Le plateau reste muet à l'œil ; il ne l'est pas pour qui écoute.
      l.title = liste.map(texteMission).join(" ");
      l.setAttribute("aria-label", l.title);
      b.appendChild(l);
    };
    marque("ech-lampe", "\u{1F4A1}", tenues);
    marque("ech-depeche", "\u{1F4EF}", depeches);

    // RIEN SUR LE JETON POUR CE QUI SORT DU CAHIER. On y avait posé un chevron
    // par sens ; sur un damier qui porte déjà six teintes de rang, des dalles,
    // des lampes, des fanions, des visages et cent traits de chaîne, c'était un
    // signe de plus et rien de lisible. Ce qu'on veut savoir n'est pas quelle
    // PIÈCE sort — remonter la chaîne causale d'affaire en affaire n'intéresse
    // personne à cette échelle —, c'est à quelles AFFAIRES celle-ci tient. Ça
    // se dit une fois, au bandeau, hors du damier (voir le rang des voisines).

    if (p.genre === "etat") {
      const parts = p.part || [];
      const br = document.createElement("span");
      br.className = "ech-breches";
      (parts.length ? parts : [{ breche: true }]).forEach((v) => {
        const i = document.createElement("i");
        if (v.breche) i.className = "ech-breche-ouverte";
        br.appendChild(i);
      });
      b.appendChild(br);
    }

    // Le survol ouvre l'encart et ALLUME LA CHAÎNE. LE CLIC LA RETIENT : la
    // bulle cesse de suivre la souris, la chaîne reste allumée, et l'on peut
    // lire tranquillement, promener le curseur dessus, relire. Une bulle qui
    // s'évanouit dès qu'on s'écarte est une bulle qu'on ne lit pas.
    //
    // Le clic ouvrait le volume de l'affaire, et l'on ne perd pas ce
    // chemin — c'est le seul du plateau vers les livres, et c'est là qu'on
    // travaille. Il passe dans la bulle retenue, en toutes lettres et sous
    // l'emblème de l'affaire : mieux vaut un renvoi qu'on voit qu'un clic muet
    // que rien n'annonçait et qu'on découvrait par hasard.
    b.addEventListener("mouseenter", () => { if (!epingle) { montrer(p, b); viser(p); } });
    b.addEventListener("mouseleave", () => { if (!epingle) { cacher(); lacher(); } });
    b.addEventListener("focus", () => { if (!epingle) { montrer(p, b); viser(p); } });
    b.addEventListener("blur", () => { if (!epingle) { cacher(); lacher(); } });
    b.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (epingle === p.cle) { relacher(); return; }   // second clic : on lâche
      retenir(p, b);
    });
    return b;
  }

  // ---- la chaîne causale, allumée au survol --------------------------------
  // C'est l'épreuve du guide rendue au geste. `vers` monte toujours : un moyen
  // vers son action, l'action vers sa clef, la clef vers son verrou, le verrou
  // vers son état, et un état vers celui qu'il SERT. Deux parcours du même
  // graphe suffisent donc à tout dire :
  //
  //   L'AVAL, en descendant les arêtes à rebours — tout ce qui CONSTRUIT la
  //   pièce : ses verrous, les clefs qui les ouvrent, les actions qui réalisent
  //   ces clefs, les moyens et offices qu'elles citent, et pour un état cible
  //   tout le sous-arbre des états qui le servent. Pleine encre.
  //
  //   L'AMONT, en remontant — ce à quoi la pièce SERT, jusqu'à la racine. C'est
  //   la REMONTÉE que le guide veut faire passer à chaque conseil : depuis
  //   n'importe quelle action, la clef, le verrou, l'état, l'affaire. Rendue
  //   plus pâle : ce n'est pas ce qu'on porte, c'est ce qui pèse sur nous.
  //
  // Tout le reste s'efface. On ne touche QUE l'opacité : pas une mesure ne
  // bouge, donc pas de reflow, et l'on peut traverser le plateau sans que
  // l'écran clignote.
  let haut = {}, bas = {};      // les arêtes de l'affaire courante, dans les deux sens
  let parCle = {};              // pour retrouver une pièce quand on n'a que son adresse
  let attente = null, relache = null, vise = null;

  function indexer(a) {
    haut = {}; bas = {}; parCle = {};
    (a ? a.pieces : []).forEach((p) => {
      parCle[p.cle] = p;
      haut[p.cle] = (p.vers || []).slice();
      (p.vers || []).forEach((v) => { (bas[v] = bas[v] || []).push(p.cle); });
    });
  }

  // En largeur, et l'ORDRE COMPTE : c'est celui de la bulle. En descendant on
  // rencontre les verrous avant les clefs, les clefs avant les actions ; en
  // remontant, le plus proche avant la racine.
  function parcourirOrdonne(depart, arcs) {
    const vus = {}, ordre = [], file = [depart];
    while (file.length) {
      const n = file.shift();
      (arcs[n] || []).forEach((m) => {
        if (!vus[m]) { vus[m] = true; ordre.push(m); file.push(m); }
      });
    }
    return ordre;
  }

  function parcourir(depart, arcs) {
    const vus = {};
    parcourirOrdonne(depart, arcs).forEach((c) => { vus[c] = true; });
    return vus;
  }

  // Une pièce, ou plusieurs. Le survol n'en désigne jamais qu'une ; la PAROLE,
  // elle, en désigne autant qu'elle en nomme — `montre: {pieces:[…]}` sur une
  // réplique, deux renvois dans la même phrase. Les chaînes s'additionnent
  // alors au lieu de se remplacer : ce qu'un homme montre en parlant est un
  // seul énoncé, pas deux survols qui se chassent l'un l'autre.
  function allumer(p) {
    const liste = (Array.isArray(p) ? p : [p]).filter((x) => x && x.cle);
    const d = document.querySelector(".ech-damier");
    if (!d || !liste.length) return;
    const aval = {}, amont = {}, cibles = {};
    liste.forEach((x) => {
      cibles[x.cle] = true;
      Object.assign(aval, parcourir(x.cle, bas));
      Object.assign(amont, parcourir(x.cle, haut));
    });
    vise = liste.map((x) => x.cle).join(",");
    d.classList.add("ech-en-chaine");
    d.querySelectorAll(".ech-pion").forEach((n) => {
      const c = n.dataset.piece;
      n.classList.toggle("ech-vise", !!cibles[c]);
      n.classList.toggle("ech-aval", !cibles[c] && !!aval[c]);
      n.classList.toggle("ech-amont", !cibles[c] && !!amont[c]);
    });
    // Un trait n'est de la chaîne que si SES DEUX BOUTS en sont : sans quoi une
    // clef écartée qui touche le même verrou s'allumerait par la bande.
    d.querySelectorAll(".ech-lien").forEach((l) => {
      const de = l.dataset.de, a = l.dataset.a;
      const dansAval = (aval[de] || cibles[de]) && (aval[a] || cibles[a]);
      const dansAmont = (amont[de] || cibles[de]) && (amont[a] || cibles[a]);
      l.classList.toggle("ech-lien-aval", !!dansAval);
      l.classList.toggle("ech-lien-amont", !dansAval && !!dansAmont);
    });
    d.querySelectorAll(".ech-branche").forEach((b) => {
      const n = b.querySelector(".ech-pion");
      const c = n ? n.dataset.piece : null;
      b.classList.toggle("ech-branche-dans", !!cibles[c] || !!aval[c] || !!amont[c]);
    });
    // Une réglette s'allume si sa colonne porte quelque chose de la chaîne.
    const cols = {};
    d.querySelectorAll(".ech-pion.ech-aval,.ech-pion.ech-amont,.ech-pion.ech-vise")
      .forEach((n) => { cols[String(n.dataset.piece).split("/")[0]] = true; });
    d.querySelectorAll(".ech-reglette").forEach((r) => {
      r.classList.toggle("ech-reglette-dans", !!cols[r.dataset.colonne]);
    });
  }

  function eteindre() {
    const d = document.querySelector(".ech-damier");
    vise = null;
    if (!d) return;
    d.classList.remove("ech-en-chaine");
    d.querySelectorAll(".ech-vise,.ech-aval,.ech-amont").forEach((n) => {
      n.classList.remove("ech-vise", "ech-aval", "ech-amont");
    });
    d.querySelectorAll(".ech-lien-aval,.ech-lien-amont").forEach((l) => {
      l.classList.remove("ech-lien-aval", "ech-lien-amont");
    });
    d.querySelectorAll(".ech-branche-dans").forEach((b) => b.classList.remove("ech-branche-dans"));
    d.querySelectorAll(".ech-reglette-dans").forEach((r) => r.classList.remove("ech-reglette-dans"));
  }

  // Un petit retard à l'entrée, une sortie tolérante : une souris qui traverse
  // le plateau ne doit rien allumer au passage, et passer d'un jeton au voisin
  // ne doit pas éteindre entre les deux.
  function viser(p) {
    clearTimeout(relache);
    if (vise === p.cle) return;
    clearTimeout(attente);
    // 120 ms et non 90 : depuis que la zone de frappe remplit sa part de case,
    // on traverse plus de jetons en traversant le plateau, et une amorce trop
    // courte allumerait tout sur son passage.
    attente = setTimeout(() => allumer(p), vise ? 40 : 120);
  }
  function lacher() {
    clearTimeout(attente);
    clearTimeout(relache);
    relache = setTimeout(eteindre, 140);
  }

  // ---- DÉSIGNER : le plateau s'allume parce qu'on en PARLE ------------------
  // La chaîne causale s'allumait à la souris et à elle seule. Or ce qu'un
  // conseiller nomme dans sa phrase — « les neufs », « la cinquième file » —
  // porte un numéro, et ce numéro est une pièce du plan : le joueur doit voir
  // DE QUOI L'HOMME PARLE PENDANT QU'IL PARLE, sans avoir à deviner qu'il y a
  // quelque chose à survoler quelque part. C'est le même mécanisme, déclenché
  // par la parole au lieu du curseur.
  //
  // Deux entrées, et une seule mécanique :
  //   • un renvoi de scène — `[les neufs](44022)` (voir renvois.js) : la
  //     mention en passant, une pièce, deux au plus.
  //   • `montre: {pieces:["2010","2001"]}` sur une réplique ou un geste : le
  //     raisonnement déroulé, l'homme qui pose la main sur le plan.
  //
  // FRANCHEMENT, PUIS ÇA SE POSE. Un joueur qui lit vite ne doit rien rater :
  // la chaîne s'allume pleine, on la tient le temps d'une phrase lue, puis elle
  // s'éteint — et il reste sur les jetons désignés une marque discrète qui dit
  // « c'est de ceux-là qu'on parlait ». Elle se rallume entière au survol du
  // renvoi, et tombe au prochain `effacer` comme les pièces de la carte : ce
  // qu'une main désigne est ÉPHÉMÈRE, ce qui dure s'écrit au cahier.
  const TENUE_FRANCHE = 2600;   // ms — le temps de lire la phrase qui la porte
  let designees = [];           // les clés posées par la parole en cours
  let apres = null, guet = null;

  // De quelle affaire relève une adresse, et à quel titre. Les deux listes sont
  // servies pour TOUTES les affaires, pas seulement pour le plateau ouvert :
  // sans ça, un renvoi vers une pièce d'un autre cahier resterait du texte nu —
  // ce qui serait un mensonge, la pièce existe.
  //
  // DEUX LISTES, ET LA DIFFÉRENCE COMPTE :
  //   `nums`  — la pièce est TRACÉE sur le damier : on bascule et l'on allume.
  //   `cites` — elle est écrite au cahier et n'atteint pas le damier (sa
  //             référence ne résout pas, ou elle pend sous un état sans
  //             colonne). Il n'y a rien à allumer, et c'est juste : c'est la
  //             faute même que le plateau existe pour montrer. On bascule
  //             quand même sur son cahier, et l'on dit pourquoi.
  // Sur 1182 adresses écrites, 1052 sont tracées et 130 ne le sont pas.
  function ouEst(numero) {
    const n = String(numero == null ? "" : numero).trim();
    if (!n) return null;
    const ici = affaire();
    // Le plateau ouvert d'abord : les numéros se croisent d'un cahier à
    // l'autre, et quand deux affaires portent la même adresse, celle qu'on a
    // sous les yeux est la bonne réponse.
    if (ici && (ici.nums || []).indexOf(n) >= 0) return { id: ici.id, tracee: true };
    let a = affaires.find((x) => (x.nums || []).indexOf(n) >= 0);
    if (a) return { id: a.id, tracee: true };
    if (ici && (ici.cites || []).indexOf(n) >= 0) return { id: ici.id, tracee: false };
    a = affaires.find((x) => (x.cites || []).indexOf(n) >= 0);
    return a ? { id: a.id, tracee: false } : null;
  }
  // `connait` reste un OUI ou NON — c'est ce que renvois.js demande, et c'est
  // ce qu'on teste à la console. `sorte` dit à quel titre, pour qui a besoin de
  // la nuance.
  function connait(numero) { return !!ouEst(numero); }
  function sorte(numero) {
    const o = ouEst(numero);
    return o ? (o.tracee ? "tracee" : "citee") : null;
  }

  // LE NOM D'AUJOURD'HUI, quand on l'a. Un renvoi est un POINTEUR VIVANT, pas
  // une citation gelée : quand la pièce change de nom, le mot dit reste dans la
  // réplique — on ne fait jamais dire à un homme qu'il s'était trompé, la pièce
  // existait quand il a parlé —, mais ce qu'on montre à côté doit être le nom
  // du jour. On ne le sert que pour le plateau ouvert : la route n'envoie le
  // détail que d'une affaire à la fois, et un nom qu'on n'a pas ne s'invente
  // pas. Faute de quoi, l'infobulle s'en tient au numéro, ce qui est vrai.
  function nom(numero) {
    const n = String(numero == null ? "" : numero).trim();
    const a = affaire();
    if (!n || !a || !a.pieces) return null;
    const p = a.pieces.find((x) => String(x.numero) === n);
    return p ? (p.nom || null) : null;
  }

  function oublier() {
    clearTimeout(apres); clearTimeout(guet);
    document.querySelectorAll(".ech-designe").forEach((n) => {
      n.classList.remove("ech-designe", "ech-designe-vif");
    });
    designees = [];
  }

  // Le plateau peut n'être pas encore tracé quand la parole tombe — on vient
  // peut-être de demander son cahier à la route. On repasse alors, sans jamais
  // s'acharner : au bout de trois secondes, c'est que la pièce n'est pas là.
  function poser2(nums, franc, essai) {
    const d = document.querySelector(".ech-damier");
    const a = affaire();
    const cibles = (d && a && a.pieces)
      ? a.pieces.filter((p) => nums.indexOf(String(p.numero)) >= 0) : [];
    if (!cibles.length) {
      // Une adresse seulement CITÉE n'aura jamais de jeton : on n'attend pas
      // trois secondes pour rien, le cahier est ouvert et c'est tout ce qu'on
      // pouvait faire.
      const rien = a && a.pieces && nums.every((n) => sorte(n) === "citee");
      if (!rien && essai < 25) guet = setTimeout(() => poser2(nums, franc, essai + 1), 120);
      return;
    }
    designees = cibles.map((p) => p.cle);
    designees.forEach((c) => {
      const n = d.querySelector('.ech-pion[data-piece="' + c + '"]');
      if (!n) return;
      n.classList.add("ech-designe");
      if (franc) n.classList.add("ech-designe-vif");
    });
    // Sous une bulle retenue, on ne vole pas la chaîne au joueur : sa lecture
    // en cours passe avant ce qu'on est en train de lui dire.
    if (epingle) return;
    allumer(cibles);
    if (!franc) return;
    apres = setTimeout(() => {
      document.querySelectorAll(".ech-designe-vif")
        .forEach((n) => n.classList.remove("ech-designe-vif"));
      if (!epingle) eteindre();
    }, TENUE_FRANCHE);
  }

  // `franc` : la première fois, quand la phrase se joue. Au survol du renvoi,
  // on rallume sans le coup d'éclat et sans minuterie — c'est un rappel, pas
  // une annonce.
  function designer(numeros, opts) {
    const nums = (Array.isArray(numeros) ? numeros : [numeros])
      .map((n) => String(n == null ? "" : n).trim()).filter(Boolean);
    if (!nums.length) return false;
    // L'AFFAIRE DE LA PREMIÈRE PIÈCE NOMMÉE commande le plateau : un homme
    // parle d'une affaire à la fois, et deux plateaux ne s'ouvrent pas ensemble.
    const ou = ouEst(nums[0]);
    if (!ou) return false;
    const id = ou.id;
    clearTimeout(apres); clearTimeout(guet);
    oublier();
    // QUAND LES DEUX ÉCHELLES SE DISPUTENT, LE DÉCOR VA À L'ÉCHIQUIER. Un
    // renvoi qui vise à la fois une ligne de registre et une pièce du plan
    // pose la question : voir la POSITION vaut mieux que lire la ligne, et la
    // ligne reste à un clic (renvois.js garde le chemin vers le volume).
    if (window.Plan && Plan.montrer) Plan.montrer("echiquier");
    if (courante !== id) {
      courante = id;
      try { localStorage.setItem(MEMOIRE, courante); } catch (e) {}
      if (epingle) relacher();
      ouvrir(id);          // asynchrone tant que le cahier n'est pas arrivé
    }
    poser2(nums, opts ? opts.franc !== false : true, 0);
    // Ce qu'on rend n'est pas un simple oui : « tracee » veut dire qu'un jeton
    // s'est allumé, « citee » que le bon cahier est ouvert et qu'il n'y avait
    // rien à allumer. L'appelant en fait ce qu'il veut ; les deux valent vrai.
    return ou.tracee ? "tracee" : "citee";
  }

  function relacherDesignation() {
    clearTimeout(apres); clearTimeout(guet);
    if (!epingle) eteindre();
  }

  // ---- RETENIR : la bulle qu'on garde sous les yeux -------------------------
  // Un seul chemin d'entrée et un seul de sortie, pour que les trois façons de
  // lâcher — le second clic sur le jeton, le clic à vide, Échap — fassent
  // exactement la même chose. Et l'on marque le jeton d'origine : une bulle
  // retenue dont on ne voit plus d'où elle vient est une bulle qu'on croit
  // cassée.
  function retenir(p, b) {
    clearTimeout(attente);
    clearTimeout(relache);
    epingle = p.cle;
    document.querySelectorAll(".ech-retenu").forEach((n) => n.classList.remove("ech-retenu"));
    if (b && b.classList) b.classList.add("ech-retenu");
    allumer(p);            // la chaîne reste allumée, et sans le retard d'entrée
    montrer(p, b, true);   // retenue, donc dépliée : preuve, coût, avancement, fautes
  }
  // UNE PIÈCE CITÉE DANS UNE IDÉE MÈNE À SON JETON. Les idées nommaient les
  // pièces et s'arrêtaient là : on lisait « afin d'atteindre 🎯 Porte acquise,
  // écrire 🗝️ Ceux du Guet… » sans pouvoir aller voir ni l'une ni l'autre. Or
  // c'est retenue qu'on lit une bulle, et c'est précisément là qu'on veut
  // suivre le nom qu'on vient de lire — la bulle le disait déjà d'un renvoi
  // vers le volume, elle ne le disait pas des pièces.
  //
  // On ne rend cliquable que ce qui A un jeton sur ce plateau : une pièce d'une
  // autre affaire, ou seulement citée, reste du texte nu. Jamais de lien mort.
  function pionDe(numero) {
    if (numero === undefined || numero === null) return null;
    const a = affaire();
    const p = a && a.pieces
      && a.pieces.find((x) => String(x.numero) === String(numero));
    if (!p || !p.cle) return null;
    const d = document.querySelector(".ech-damier");
    return d ? d.querySelector('.ech-pion[data-piece="' + p.cle + '"]') : null;
  }

  function versLaPiece(s, numero) {
    const n = pionDe(numero);
    if (!n) return;
    s.classList.add("ech-e-vers");
    s.setAttribute("role", "link");
    s.tabIndex = 0;
    const aller = (ev) => {
      ev.stopPropagation();
      ev.preventDefault();
      relacher();                                   // on lâche la bulle d'où l'on part
      n.scrollIntoView({ block: "nearest", inline: "nearest" });
      n.click();                                    // le jeton fait le reste : retenir, allumer
    };
    s.addEventListener("click", aller);
    s.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") aller(ev);
    });
    // Survoler le nom allume le jeton visé, avant même le clic : on voit où l'on
    // atterrira, ce qui vaut mieux que d'y atterrir pour le découvrir.
    s.addEventListener("mouseenter", () => n.classList.add("ech-designe-vif"));
    s.addEventListener("mouseleave", () => n.classList.remove("ech-designe-vif"));
  }

  function relacher() {
    epingle = null;
    document.querySelectorAll(".ech-retenu").forEach((n) => n.classList.remove("ech-retenu"));
    cacher();
    lacher();
  }

  // ---- ouvrir l'affaire dans les livres ------------------------------------
  function ouvrirLivre() {
    const a = affaire();
    if (!a || !window.Books || !Books.ouvrir) return;
    // Faute de volume — une affaire nommée au registre et qui n'a pas encore le
    // sien —, on ouvre le registre des états cibles : le guide dit que c'est
    // lui qui a raison, et l'on n'invente pas un lien mort.
    if (!Books.ouvrir(a.livre_id)) Books.ouvrir("plan-etats-cibles");
  }

  // ---- et le chemin inverse : d'un volume vers son plateau -----------------
  // Les livres n'ont pas à savoir ce qu'est une affaire : ils demandent si ce
  // volume-ci en a une, et par où l'ouvrir.
  function pourLivre(livreId) {
    if (!livreId) return null;
    const a = affaires.find((x) => x.livre_id === livreId);
    return a ? { id: a.id, titre: a.titre, embleme: a.embleme } : null;
  }

  // Ouvrir le plateau d'une affaire, d'où qu'on vienne : on bascule l'échelle,
  // on retient l'affaire comme si on l'avait choisie à la tirette, et l'on va
  // chercher son cahier s'il n'est pas encore là.
  function montrerAffaire(id) {
    const x = affaires.find((a) => a.id === id);
    if (!x) return false;
    courante = id;
    try { localStorage.setItem(MEMOIRE, courante); } catch (err) {}
    if (window.Plan && Plan.montrer) Plan.montrer("echiquier");
    cacher();
    dessine = "";
    if (x.pieces) dessiner(); else ouvrir(id);
    return true;
  }

  // ---- l'encart ------------------------------------------------------------
  // Tout ce que le plateau n'écrit pas se dit ici, et nulle part ailleurs.
  let encart = null;
  function boite() {
    if (encart) return encart;
    encart = document.createElement("div");
    encart.className = "ech-encart";
    encart.hidden = true;
    // Un clic sur l'encart le RETIENT et le DÉPLIE : c'est là que passe tout ce
    // que le survol ne montre plus — la preuve, le levé quand, le coût, où ça
    // en est, les brèches, les fautes. Un second clic le referme.
    // Un clic sur l'encart le RETIENT et le DÉPLIE quand il ne l'est pas déjà
    // — c'est par là qu'on retient la bulle d'une tuile ou du blason, qui n'ont
    // pas de jeton à cliquer. Une bulle DÉJÀ retenue, elle, ne se referme pas
    // quand on clique dedans : on y promène le curseur, on y suit un lien, on
    // appuie sur le renvoi vers le volume. Elle se lâche par le jeton, par le
    // vide, ou par Échap.
    encart.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (epingle) return;
      epingle = "encart";
      if (derniere) montrer(derniere.p, derniere.cible, true);
    });
    document.body.appendChild(encart);
    return encart;
  }

  // Ce qu'il MANQUE pour que la pièce monte d'un rang. C'est une phrase et non
  // un mot-clé : « en attente — retenue » sous une ligne qui dit déjà « à
  // étudier » se lisait comme une contradiction.
  const MONNAIE = {
    verrou: "il faut savoir à quoi il serait levé",
    clef: "il faut la retenir ou l'écarter",
    // ÉCRIT, PAS PORTÉ. Ce n'est pas une faute et ce n'est pas du travail :
    // l'action est écrite, elle remonte, quelqu'un en répond — et personne n'a
    // encore dit la faire. C'est l'état de 542 actions sur 584.
    action: "écrite, et personne n'a encore dit la faire",
    moyen: "il faut qu'il soit à son registre",
    office: "il faut qu'il soit à son registre",
  };

  // AU SURVOL, TROIS CHOSES : le signe, le nom, ce que la pièce dit. Rien
  // d'autre — c'est une bulle, pas une fiche, et l'on en survole cinquante en
  // traversant le plateau. La description est la colonne qui DIT la chose dans
  // le registre de son rang : « ce qui doit être vrai » pour un état cible,
  // « ce qui est vrai aujourd'hui » pour un verrou, « le principe » pour une
  // clef, « ce qu'on fait, et où » pour une action, « ce qu'il sait faire »
  // pour un moyen, « ce dont il répond » pour un office. Le serveur la range
  // dans `dit`, une fois pour toutes.
  //
  // TOUT LE RESTE — la preuve, le levé quand, le coût, l'avancement, les
  // brèches, les fautes — attend le clic sur l'encart, qui l'épingle et le
  // déplie. Rien n'est perdu, rien n'encombre. Ce qui doit se voir sans rien
  // survoler reste sur le plateau : le fanion des fautes, et lui seul.
  // Les rangs de la bulle, dans l'ordre de la DESCENTE du guide. Les états
  // cibles ouvrent la liste : ce sont ceux qui SERVENT la pièce survolée, et le
  // plateau les allume aussi — les taire ferait mentir la bulle sur ce qu'on
  // vient d'éclairer. Les moyens et les offices ferment, ensemble : ce sont les
  // deux colonnes de la dernière question, « avec quoi, et sous quelle
  // autorité ».
  const DESCENTE = ["etat", "verrou", "clef", "action", "moyen", "office"];
  const PAR_RANG = 4;   // ce qu'on montre par rang avant d'annoncer le reste
  let parRang = PAR_RANG;   // …et ce qu'on en garde quand la place manque

  // LA BULLE NE SE FAIT PAS DÉFILER. Sa taille de base commande tout le reste
  // (les cinq niveaux sont en `em`), et quand le contenu excède la hauteur de
  // fenêtre, c'est elle qui baisse — jusqu'au PLANCHER de lisibilité, pas plus
  // bas. Sous le plancher, ce sont les MAILLONS qui cèdent : on baisse
  // `parRang`, le mécanisme « et N autres » dit ce qu'on ne montre plus, et la
  // tête, la conclusion et la mission restent intactes. Jamais l'inverse.
  const BASE = 14.5;      // px, la taille de lecture de la description
  const CONFORT = 13;     // px, en dessous on préfère couper que rapetisser
  const PLANCHER = 11;    // px, en dessous on ne lit plus, on devine

  const reste = (n) => "et " + n + (n > 1 ? " autres" : " autre");

  // UN MAILLON : le signe et le titre, rien d'autre. C'est ce qui garde la
  // bulle lisible quand une chaîne en compte cinquante.
  function maillon(q, classe) {
    const l = document.createElement("div");
    l.className = "ech-e-maillon ech-m-" + q.genre + (classe ? " " + classe : "");
    l.innerHTML = glyphe(q);
    const t = document.createElement("span");
    t.textContent = q.nom || q.cle;
    l.appendChild(t);
    return l;
  }

  // La phrase, composée des pièces que le serveur a nommées. Une seule, jamais
  // une liste : quand plusieurs maillons cassent de la même façon, on nomme le
  // premier et l'on compte les autres.
  function conclusion(p) {
    const c = p.conclusion;
    const d = document.createElement("div");
    d.className = "ech-e-verdict ech-v-" + c.cas;
    const mot = (t) => d.appendChild(document.createTextNode(t));
    const piece = (q) => {
      if (!q) return;
      const s = document.createElement("span");
      s.className = "ech-e-cite";
      s.innerHTML = icone(q.genre);
      const t = document.createElement("i");
      t.textContent = q.nom;
      s.appendChild(t);
      versLaPiece(s, q.numero);
      d.appendChild(s);
    };
    // Quand ce qui casse est la pièce elle-même, on ne la renomme pas : elle est
    // écrite juste au-dessus.
    const ailleurs = c.cible && c.cible.numero !== p.numero;
    if (c.cas === "tient") {
      mot("la chaîne tient");
      // Le fanion et la phrase doivent dire la même chose : quelqu'un la fait,
      // et personne n'en répond au registre des offices.
      if (c.sans_office) { d.classList.add("ech-v-sans-office"); mot(" — mais aucun office ne la porte"); }
    }
    else if (c.cas === "sans-verrou") mot("aucun verrou écrit : c'est une intention, pas un plan");
    else if (c.cas === "sans-clef") {
      if (ailleurs) { mot("attend "); piece(c.cible); mot(" — "); }
      mot("rien n'est envisagé contre lui");
    } else if (c.cas === "a-l-etude") {
      if (ailleurs) { mot("attend "); piece(c.cible); mot(" — sa clef "); }
      else mot("sa clef ");
      piece(c.via);
      mot(" n'est qu'à l'étude");
    } else if (c.cas === "pas-tranchee") {
      if (ailleurs) { mot("attend "); piece(c.cible); mot(" — elle "); }
      else mot("elle ");
      mot("n'est pas tranchée : rien ne partira tant qu'on ne l'aura pas retenue");
    } else if (c.cas === "ecartee") {
      if (ailleurs) { mot("attend "); piece(c.cible); mot(" — elle "); }
      else mot("elle ");
      mot("est écartée : ce qui pend dessous ne sert plus");
    } else if (c.cas === "sans-action") {
      if (ailleurs) { mot("attend "); piece(c.cible); mot(" — elle "); }
      else mot("elle ");
      mot("est retenue, et personne ne la fait");
    } else if (c.cas === "sans-teneur") {
      if (ailleurs) { mot("attend "); piece(c.cible); mot(" — "); }
      mot("personne n'en répond");
    }
    if (c.autres) {
      mot(", et " + c.autres + (c.autres > 1 ? " autres dans le même cas" : " autre dans le même cas"));
    }
    return d;
  }

  // ---- LES MISSIONS : ce qu'il y aurait à faire ----------------------------
  // La conclusion dit où la chaîne casse ; elle s'arrêtait là, et le joueur
  // repartait avec un diagnostic et rien à faire. Une mission tient en une
  // phrase, et c'est le gabarit qui la rend lisible :
  //
  //     Afin d'atteindre {l'état cible}, {l'acte} {ce que ça lèverait}
  //     — {ce que ça ne suffit pas à lever}.
  //
  // Tout vient du serveur, calculé sur la seule topologie : ni date, ni prose.
  // Rien ne s'écrit nulle part — une mission s'affiche, elle ne commande rien
  // et ne touche aucun registre.
  //
  // DEUX, PAS TROIS, puis « et N autres ». Une bulle qui déroulerait les neuf
  // missions d'une racine est un mur, et l'on en survole cinquante en
  // traversant le plateau. Ce qui est montré est déjà dédupliqué par l'ACTE :
  // retenir une clef est UNE décision, quel que soit le nombre d'actions qui
  // l'attendent.
  const MISSIONS_VUES = 2;

  // La même phrase, en texte nu : c'est ce que porte la lampe du plateau pour
  // qui l'écoute au lieu de la voir. Une seule composition pour les deux, sans
  // quoi l'infobulle et la bulle finiraient par dire deux choses.
  function texteMission(m) {
    const p = [];
    if (m.but && !(m.piece && m.but.numero === m.piece.numero)) {
      p.push("Afin d'atteindre " + m.but.nom
        + (m.buts_autres ? (m.buts_autres > 1
          ? " (et " + m.buts_autres + " autres états cibles)" : " (et un autre état cible)") : "")
        + ",");
    }
    p.push(m.verbe, m.piece ? m.piece.nom : "");
    if (m.effet) p.push(m.effet);
    if (m.vers) p.push(m.vers.nom);
    let t = p.filter(Boolean).join(" ");
    if (m.precision) t += " — " + m.precision;
    return t + ".";
  }

  function traitMission(m) {
    const d = document.createElement("div");
    // À LA REINE, ou AU CONSEIL — et ça se voit sans lire. Retenir, écarter,
    // désigner : c'est sa parole, personne d'autre ne peut, et le texte est
    // déjà au registre. Écrire, trouver : c'est du travail, et ça se dépêche.
    //
    // Et l'ESPÈCE par-dessus, la même que sur le plateau : une ligne de tenue
    // de registre ne se lit pas comme une dépêche à lancer. Le signe repris en
    // tête de ligne est celui du jeton, pour qu'on reconnaisse d'un coup ce
    // qu'on vient de voir s'allumer là-bas.
    d.className = "ech-e-mission ech-e-mission-"
      + (m.sur === "reine" ? "reine" : "conseil")
      + (m.espece === "narratif" ? " ech-e-depeche" : "");
    const mot = (t) => d.appendChild(document.createTextNode(t));
    const piece = (q) => {
      if (!q) return;
      const s = document.createElement("span");
      s.className = "ech-e-cite";
      s.innerHTML = icone(q.genre);
      const t = document.createElement("i");
      t.textContent = q.nom;
      s.appendChild(t);
      versLaPiece(s, q.numero);
      d.appendChild(s);
    };
    // X ne se dit que s'il apprend quelque chose : quand l'acte porte SUR
    // l'état cible lui-même — un état sans verrou est sa propre racine —,
    // « afin d'atteindre X, faire quelque chose à X » tourne à vide.
    if (m.but && !(m.piece && m.but.numero === m.piece.numero)) {
      mot("Afin d'atteindre ");
      piece(m.but);
      if (m.buts_autres) {
        mot(m.buts_autres > 1 ? " (et " + m.buts_autres + " autres états cibles)"
          : " (et un autre état cible)");
      }
      mot(", ");
    }
    mot(m.verbe + " ");
    piece(m.piece);
    if (m.effet) {
      mot(" " + m.effet);
      if (m.vers) { mot(" "); piece(m.vers); }
    }
    if (m.precision) mot(" — " + m.precision);
    mot(".");
    return d;
  }

  function blocMissions(liste) {
    const actes = (liste || []).map((a) => missions[a]).filter(Boolean);
    if (!actes.length) return null;
    const b = document.createElement("div");
    b.className = "ech-e-missions";
    actes.slice(0, MISSIONS_VUES).forEach((m) => b.appendChild(traitMission(m)));
    if (actes.length > MISSIONS_VUES) {
      const r = document.createElement("div");
      r.className = "ech-e-reste";
      r.textContent = reste(actes.length - MISSIONS_VUES);
      b.appendChild(r);
    }
    return b;
  }

  // CE QU'ELLE PORTE, au-dessus et à mi-voix : la même grammaire que sur le
  // plateau, où l'amont est estompé. Une ligne, du plus proche à la racine —
  // c'est la REMONTÉE du guide, dite en toutes lettres. Survolée ou retenue, la
  // bulle la montre pareil : on ne perd pas son chemin en s'installant.
  function blocAmont(p) {
    const amont = parcourirOrdonne(p.cle, haut).map((c) => parCle[c]).filter(Boolean);
    if (!amont.length) return null;
    const a = document.createElement("div");
    a.className = "ech-e-amont";
    amont.slice(0, 4).forEach((q, i) => {
      if (i) a.appendChild(document.createTextNode(" "));
      const s = document.createElement("span");
      s.innerHTML = glyphe(q);
      const t = document.createElement("i");
      t.textContent = q.nom || q.cle;
      s.appendChild(t);
      a.appendChild(s);
    });
    if (amont.length > 4) a.appendChild(document.createTextNode(" " + reste(amont.length - 4)));
    return a;
  }

  function corpsCourt(p) {
    const f = document.createDocumentFragment();

    const am = blocAmont(p);
    if (am) f.appendChild(am);

    const tete = document.createElement("header");
    tete.className = "ech-e-tete";
    tete.innerHTML = glyphe(p);
    const nom = document.createElement("b");
    nom.textContent = p.nom || p.cle;
    // Le teneur se glisse DANS la tête, il n'ouvre pas une quatrième ligne :
    // c'est la même chose qu'on regarde — l'action et la main qui la porte.
    if (p.teneur) {
      const q = document.createElement("i");
      q.className = "ech-e-teneur";
      q.textContent = p.teneur;
      nom.appendChild(q);
    }
    tete.appendChild(nom);
    f.appendChild(tete);
    // La pièce survolée est la SEULE à garder sa description.
    if (p.dit) {
      const d = document.createElement("p");
      d.className = "ech-e-dit";
      d.textContent = p.dit;
      f.appendChild(d);
    }

    // LA CONCLUSION : une phrase, le premier maillon qui manque en descendant.
    // Elle vient toute faite du serveur — c'est de la topologie, pas du texte —
    // et on ne fait ici que la dire. Elle se pose SOUS la tête et AU-DESSUS des
    // maillons : c'est la réponse à « alors, où on en est ? », et ce qui suit
    // est là pour qui veut vérifier.
    if (p.conclusion) f.appendChild(conclusion(p));
    // ET CE QU'IL Y AURAIT À FAIRE, juste dessous : ce sont les missions de
    // toute la chaîne qui pend sous la pièce, dédupliquées par l'acte.
    if (p.genre !== "affaire") {
      const m = blocMissions(p.missions);
      if (m) f.appendChild(m);
    }

    if (p.mal) f.appendChild(ligne("ech-e-mal", p.mal));

    // UNE AFFAIRE MONTRE SES PIEDS D'ARBRE, et pas toute sa chaîne : sur une
    // affaire à racine unique, dérouler la chaîne entière reviendrait
    // exactement à survoler cette racine, et l'on aurait écrit deux fois la
    // même bulle. Ce que l'emblème ajoute, c'est ce que la racine ne dit pas :
    // COMBIEN d'arbres porte l'affaire, et lesquels.
    if (p.genre === "affaire") {
      const x = affaires.find((y) => y.id === p.affaire_id);
      // CE QUI EST VRAI DE L'AFFAIRE ENTIÈRE se dit ici, et nulle part
      // ailleurs. D'abord le compte de ce qu'elle réclame — dédupliqué une
      // dernière fois, deux colonnes ne réclament pas deux fois le même acte —,
      // puis ses deux premières missions.
      //
      // Et LE FAIT RETOURNÉ. « Ce verrou n'a pas de rechange » est vrai de
      // trente-deux verrous sur trente-trois : posé sur les jetons, il ne
      // dirait rien et noierait le reste. Un fait vrai de presque tout le monde
      // ne se jette pas pour autant — il se retourne et se dit UNE FOIS, au
      // chapeau : aucun verrou du plan n'a jamais eu deux clefs, quand le guide
      // prévoit qu'elles « se disputent la place ».
      if (x) {
        const n = (x.missions || []).length;
        if (n) {
          f.appendChild(ligne("ech-e-part", n > 1
            ? n + " choses à faire dans cette affaire" : "une chose à faire dans cette affaire"));
        }
        // CE QUI EST VRAI DE PRESQUE TOUTE L'AFFAIRE se dit ici, une fois. Une
        // action dont l'office est nommé en clair a quelqu'un pour la porter ;
        // ce qui manque est une ligne au registre, et c'est une discipline à
        // reprendre d'un coup — pas une décision par action, et surtout pas une
        // lampe par jeton.
        if (x.en_clair) {
          f.appendChild(ligne("ech-e-ligne ech-e-italique", x.en_clair > 1
            ? x.en_clair + " actions nomment leur office en clair — il leur manque"
              + " son numéro, pas un homme"
            : "une action nomme son office en clair — il lui manque son numéro,"
              + " pas un homme"));
        }
        // Et le même fait du côté des moyens : un galet ou une plume cités par
        // leur nom. Il portait un fanion rouge sur chaque jeton faute d'être
        // compté quelque part ; il est compté ici, et une fois.
        if (x.cites_en_clair) {
          f.appendChild(ligne("ech-e-ligne ech-e-italique", x.cites_en_clair > 1
            ? x.cites_en_clair + " moyens ou offices sont cités par leur nom et non"
              + " par leur numéro — ils existent, ils ne sont pas adressés"
            : "un moyen ou un office est cité par son nom et non par son numéro"
              + " — il existe, il n'est pas adressé"));
        }
        const r = x.rechange || {};
        if (r.verrous && !r.plusieurs) {
          const tete2 = r.verrous > 1
            ? "aucun de ses " + r.verrous + " verrous n'a de rechange"
            : "son verrou n'a pas de rechange";
          f.appendChild(ligne("ech-e-ligne ech-e-italique", tete2 + " — "
            + (r.aucune ? (r.aucune === r.verrous ? "aucune clef écrite contre eux"
                : "une clef au plus contre chacun, et " + r.aucune + " sans aucune")
               : "une clef contre chacun")
            + ", là où le guide veut qu'elles se disputent la place"));
        }
        const m = blocMissions(x.missions);
        if (m) f.appendChild(m);
      }
      // Les pieds d'arbre : les pièces quand on les a, sinon le résumé que la
      // route en a fait — un plateau qu'on n'a pas encore ouvert se survole.
      const pieds = x ? (x.pieces
        ? x.pieces.filter((q) => q.genre === "etat" && !(q.vers || []).length)
        : (x.pieds || [])) : [];
      if (pieds.length) {
        const corps = document.createElement("div");
        corps.className = "ech-e-chaine";
        pieds.slice(0, parRang).forEach((q) => corps.appendChild(maillon(q)));
        if (pieds.length > parRang) {
          const r = document.createElement("div");
          r.className = "ech-e-reste";
          r.textContent = reste(pieds.length - parRang);
          corps.appendChild(r);
        }
        f.appendChild(corps);
      }
      return f;
    }

    const ch = blocChaine(p);
    if (ch) f.appendChild(ch);
    return f;
  }

  // CE QUI LA PORTE : la chaîne aval, un maillon par ligne. Elle BRANCHE — un
  // état a plusieurs verrous, un verrou plusieurs clefs — et à cette taille un
  // arbre indenté ne se lit pas : on GROUPE PAR RANG, ce qui se lit d'un coup
  // et garde l'ordre de la descente. La bulle de survol et la bulle retenue
  // montrent la MÊME chaîne : retenir une bulle ne doit rien lui retirer.
  function blocChaine(p) {
    const aval = parcourirOrdonne(p.cle, bas).map((c) => parCle[c]).filter(Boolean);
    if (!aval.length) return null;
    const corps = document.createElement("div");
    corps.className = "ech-e-chaine";
    DESCENTE.forEach((g) => {
      const dedans = aval.filter((q) => q.genre === g);
      if (!dedans.length) return;
      // BORNER, ET LE DIRE. Une bulle de cinquante lignes est un mur : on coupe
      // à quatre par rang et l'on annonce ce qu'on ne montre pas, au lieu de
      // tronquer en silence.
      dedans.slice(0, parRang).forEach((q) => corps.appendChild(maillon(q)));
      if (dedans.length > parRang) {
        const r = document.createElement("div");
        r.className = "ech-e-reste";
        r.textContent = reste(dedans.length - parRang);
        corps.appendChild(r);
      }
    });
    return corps;
  }

  function corpsPiece(p) {
    const f = document.createDocumentFragment();
    const am2 = blocAmont(p);
    if (am2) f.appendChild(am2);
    const tete = document.createElement("header");
    tete.className = "ech-e-tete";
    tete.innerHTML = glyphe(p);
    const nom = document.createElement("b");
    nom.textContent = p.nom || p.cle;
    tete.appendChild(nom);
    if (p.numero) {
      const n = document.createElement("span");
      n.className = "ech-e-numero";
      n.textContent = p.numero;
      tete.appendChild(n);
    }
    f.appendChild(tete);

    if (p.dit) {
      const d = document.createElement("p");
      d.className = "ech-e-dit";
      d.textContent = p.dit;
      f.appendChild(d);
    }

    // RETENIR NE RETIRE RIEN. La bulle épinglée est celle qu'on lit vraiment :
    // elle ajoute le détail, elle ne remplace pas la conclusion ni les
    // missions — ce sont les deux phrases pour lesquelles la bulle existe, et
    // les perdre au moment où l'on s'installe pour lire serait absurde.
    if (p.conclusion) f.appendChild(conclusion(p));
    const mm = blocMissions(p.missions);
    if (mm) f.appendChild(mm);

    if (p.genre === "etat") {
      if (p.ou) f.appendChild(ligne("ech-e-ligne", "où : " + p.ou));
      const parts = p.part || [];
      const n = parts.filter((v) => v.breche).length;
      f.appendChild(ligne("ech-e-part", parts.length
        ? (n === 0 ? "aucune brèche — aucune clef retenue contre ses verrous"
           : n === parts.length ? "toutes les brèches ouvertes"
           : n + " brèche sur " + parts.length)
        : "aucun verrou écrit contre cet état"));
      parts.forEach((v) => {
        f.appendChild(ligne("ech-e-pierre" + (v.breche ? " ech-e-breche" : ""),
          (v.breche ? "brèche — " : "pierre — ") + v.nom));
      });
      if (p.sert) f.appendChild(ligne("ech-e-ligne", "sert l'état " + p.sert));
    }
    if (p.genre === "verrou" && p.leve_quand) {
      f.appendChild(ligne("ech-e-ligne ech-e-italique", "levé quand : " + p.leve_quand));
    }
    if (p.depend_de) {
      f.appendChild(ligne("ech-e-ligne", "dépend de : " + p.depend_de));
    }
    if (p.genre === "clef") {
      f.appendChild(ligne("ech-e-ligne", p.tenue === "retenue" ? "retenue"
        : p.tenue === "ecartee" ? "écartée" : "à étudier"));
      if (p.cout) f.appendChild(ligne("ech-e-ligne", "coûte : " + p.cout));
      if (p.moyens) f.appendChild(ligne("ech-e-ligne", "modules qualifiés : " + p.moyens));
    }
    if (p.genre === "action") {
      if (p.ou_ca_en_est) f.appendChild(ligne("ech-e-ligne", p.ou_ca_en_est));
      // PORTÉE OU SEULEMENT ÉCRITE, dit en toutes lettres : c'est la question
      // que le plateau pose et à laquelle la bulle doit répondre sans détour.
      f.appendChild(ligne("ech-e-ligne ech-e-" + (porte(p) ? "portee" : "ecrite"),
        porte(p)
          ? (p.dans_la_tete
              ? "portée — il l'a déclarée, et elle est dans ses étapes"
              : "portée — il l'a déclarée à son cahier")
          : "écrite, pas portée — personne n'a encore dit la faire"));
      if (p.office) f.appendChild(ligne("ech-e-ligne", "office : " + p.office));
      if (p.moyens) f.appendChild(ligne("ech-e-ligne", "moyens : " + p.moyens));
    }
    if (p.genre === "moyen" || p.genre === "office") {
      if (p.tient) f.appendChild(ligne("ech-e-ligne", "tenu par " + p.tient));
      if (p.ou) f.appendChild(ligne("ech-e-ligne", "à " + p.ou));
      if (p.tenue_du_moyen) f.appendChild(ligne("ech-e-ligne", p.tenue_du_moyen));
    }
    if (p.preuve) f.appendChild(ligne("ech-e-ligne", "la preuve : " + p.preuve));

    // La marche : ce que coûte la montée d'un rang, et son état.
    if (p.vers && p.vers.length && p.rang !== "etat") {
      const e = etatMarche(p);
      f.appendChild(ligne("ech-e-marche ech-e-marche-" + e,
        e === "payee" ? (p.paie || "monte")
          : e === "saut" ? "la remontée s'arrête ici"
          : e === "decision" ? "à trancher — il faut la retenir ou l'écarter"
          : e === "ecartee" ? "écartée — ce qui pend dessous ne sert plus"
          : "en attente — " + (MONNAIE[p.genre] || "")));
    }

    const ch2 = blocChaine(p);
    if (ch2) f.appendChild(ch2);

    // LE CHEMIN VERS LES LIVRES, en toutes lettres. Le clic sur le jeton
    // retient désormais la bulle ; le volume s'ouvre donc par un renvoi qu'on
    // VOIT, sous l'emblème de l'affaire. C'est plus clair que le clic muet
    // d'avant, qu'aucun signe n'annonçait.
    const pied = document.createElement("footer");
    pied.className = "ech-e-pied";
    const a = affaire();
    const ouvrir = document.createElement("button");
    ouvrir.type = "button";
    ouvrir.className = "ech-e-ouvrir";
    ouvrir.innerHTML = a ? signe(a) : icone("affaire");
    const t = document.createElement("span");
    t.textContent = a ? "Ouvrir le cahier — " + a.titre : "Ouvrir le registre";
    ouvrir.appendChild(t);
    ouvrir.addEventListener("click", (ev) => { ev.stopPropagation(); ouvrirLivre(); });
    pied.appendChild(ouvrir);
    f.appendChild(pied);

    // CE QUI CASSE ET CE QUI EST MAL TENU NE SE DISENT PAS DE LA MÊME ENCRE.
    // La rupture est rouge — la remontée s'arrête là. Le reste est une note :
    // une preuve qu'on n'a pas écrite, un office nommé en clair. C'est vrai, ça
    // se corrige, et ça ne mérite pas la couleur du sang.
    (p.fautes || []).forEach((x) => {
      f.appendChild(ligne(rompt(p) ? "ech-e-mal" : "ech-e-note", x));
    });
    return f;
  }

  function corpsTexte(titre, dit, mal) {
    const f = document.createDocumentFragment();
    const t = document.createElement("header");
    t.className = "ech-e-tete";
    const n = document.createElement("b");
    n.textContent = titre;
    t.appendChild(n);
    f.appendChild(t);
    if (dit) {
      const p = document.createElement("p");
      p.className = "ech-e-dit";
      p.textContent = dit;
      f.appendChild(p);
    }
    if (mal) f.appendChild(ligne("ech-e-mal", mal));
    return f;
  }

  // La bulle décrit le plateau : elle ne doit pas le couvrir. On la pose donc à
  // côté du DAMIER ENTIER, pas seulement à côté du jeton — sur ce rendu le décor
  // est à droite de l'écran, et la bulle va se ranger sur la chronique, qui a de
  // la place. Faute de place des deux côtés, on retombe sur le voisinage du
  // jeton, et dans tous les cas elle reste dans la fenêtre.
  const LARGE = 380;   // la largeur de lecture : ~48 signes par ligne
  const ETROIT = 300;  // en deçà, on ne maigrit plus : on préfère recouvrir

  function poser(cible) {
    const e = boite();
    e.hidden = false;
    e.style.left = "0px"; e.style.top = "0px";
    const damier = document.querySelector(".ech-damier");
    const g = damier ? damier.getBoundingClientRect() : null;
    const marge = 10;
    // ELLE MAIGRIT AVANT DE RENONCER. La bulle est passée de 250 à 380 px pour
    // la lisibilité, et sur une fenêtre étroite les deux gouttières autour du
    // damier ne l'accueillent plus — elle retombait alors sur le jeton, c'est-à-
    // dire par-dessus le plateau qu'elle décrit. On lui donne donc la plus large
    // des deux gouttières quand elle y tient encore lisiblement.
    e.style.width = "";
    if (g) {
      const place = Math.max(g.left - marge - 6, window.innerWidth - g.right - marge - 6);
      if (place < LARGE && place >= ETROIT) e.style.width = Math.floor(place) + "px";
    }
    // LA MISE À L'ÉCHELLE, avant de placer : ce sont les mesures d'APRÈS qui
    // servent à caler la bulle dans la fenêtre. Deux passes, parce qu'en
    // rapetissant le texte on change ses retours à la ligne, donc sa hauteur.
    // On vise un peu court : rapetisser le texte change ses retours à la ligne,
    // donc la hauteur qu'on vient de calculer. Trois passes, et six pixels de
    // garde — une bulle qui tombe au pixel près est une bulle qui rogne.
    e.style.fontSize = BASE + "px";
    for (let i = 0; i < 3; i++) {
      const h = e.getBoundingClientRect().height;
      const place = placeEnHauteur() - 6;
      if (h <= place) break;
      const t = parseFloat(e.style.fontSize) * place / h;
      e.style.fontSize = Math.max(PLANCHER, t).toFixed(2) + "px";
      if (t <= PLANCHER) break;
    }
    const r = cible.getBoundingClientRect();
    const b = e.getBoundingClientRect();
    let x = null;
    if (g) {
      if (g.left - marge - b.width >= 6) x = g.left - marge - b.width;
      else if (g.right + marge + b.width <= window.innerWidth - 6) x = g.right + marge;
    }
    if (x === null) {
      x = r.right + marge;
      if (x + b.width > window.innerWidth - 6) x = r.left - marge - b.width;
      if (x < 6) x = Math.max(6, Math.min(window.innerWidth - b.width - 6, r.left));
    }
    let y = r.top + r.height / 2 - b.height / 2;
    y = Math.max(6, Math.min(window.innerHeight - b.height - 6, y));
    e.style.left = Math.round(x) + "px";
    e.style.top = Math.round(y) + "px";
  }

  // Ce qu'on a sous les yeux, pour pouvoir le redéplier au clic sans avoir à
  // retrouver le jeton.
  let derniere = null;

  const placeEnHauteur = () => window.innerHeight - 12;

  function montrer(p, cible, complet) {
    const e = boite();
    // UNE BULLE À LA FOIS. La fiche d'un visage et l'encart du plateau se
    // posent tous deux en haut à gauche et se recouvraient, l'une par-dessus
    // l'autre — on lisait deux choses mêlées. La dernière demandée gagne, et
    // visage.js referme celle-ci quand c'est un homme qu'on survole.
    if (window.Visage && Visage.fermer) Visage.fermer();
    derniere = { p: p, cible: cible };
    // On tente au large, et l'on resserre tant que ça déborde : d'abord la
    // taille (dans `poser`), puis les maillons. Trois passes au plus, et la
    // première suffit dans l'immense majorité des cas.
    // L'ordre de ce qui cède, et il n'est pas négociable : la taille d'abord
    // (dans `poser`), puis les MAILLONS — de la vérification —, puis en dernier
    // recours la description, coupée aux lignes avec ses points de suite : le
    // volume est à un clic, et une bulle qui sort de l'écran ne se lit pas du
    // tout. La tête, la conclusion et la mission ne cèdent jamais.
    const essais = [{ r: PAR_RANG }, { r: 2 }, { r: 1 }, { r: 0 },
                    { r: 0, serre: 8 }, { r: 0, serre: 4 }];
    for (let i = 0; i < essais.length; i++) {
      parRang = essais[i].r;
      e.innerHTML = "";
      e.className = "ech-encart ech-e-" + (p.genre || "note") + (complet ? " ech-epingle" : "")
        + (essais[i].serre ? " ech-e-serre" : "");
      e.style.setProperty("--ech-lignes", essais[i].serre || "");
      e.appendChild(p.genre ? (complet ? corpsPiece(p) : corpsCourt(p))
        : corpsTexte(p.titre, p.dit, p.mal));
      e.hidden = false;
      if (window.Entites) Entites.traiter(e);
      poser(cible);
      // DEUX CONDITIONS, PAS UNE : tenir dans la fenêtre, et ne rien rogner.
      // `overflow:hidden` ne fait pas de barre — il coupe en silence, ce qui
      // est pire. On mesure donc aussi le débord interne.
      //
      // Et l'on ne se contente pas de « ça tient » : rapetisser tout le texte
      // pour sauver quatre maillons est un mauvais échange, puisque les
      // maillons sont ce qui compte le moins. Tant qu'on est sous le confort de
      // lecture, on continue de couper — ce sont les maillons qui cèdent,
      // ensuite la description, jamais la taille du reste.
      const tient = e.getBoundingClientRect().height <= placeEnHauteur() + 0.5
        && e.scrollHeight <= e.clientHeight + 1;
      if (tient && parseFloat(e.style.fontSize) >= CONFORT) break;
    }
    parRang = PAR_RANG;
  }

  function cacher() {
    if (encart) { encart.hidden = true; encart.innerHTML = ""; }
    derniere = null;
  }

  // ---- les marches, tracées d'un jeton à l'autre ---------------------------
  // La chaîne du guide, en traits : plein quand la montée est payée, pointillé
  // neutre quand elle attend (une clef à étudier n'a rien converti, et ce n'est
  // pas une faute), tirets rouges quand la remontée s'arrête là.
  // DROIT, PUIS COUDÉ. Les marches étaient des courbes de Bézier : sur cent
  // trente liens, chacune part en biais dès le premier pixel, et deux traits
  // voisins ne se distinguent plus nulle part — c'est le fouillis. Un lien va
  // donc TOUT DROIT en montant, tourne une fois à mi-hauteur, court à
  // l'horizontale, tourne encore et remonte droit dans sa cible. On ne suit
  // plus une courbe : on suit une verticale, et l'œil retrouve d'où elle part.
  // Les angles sont arrondis, parce qu'un coude vif fait un dessin d'ingénieur.
  const RAYON = 9;

  function coude(x1, y1, x2, y2, couloir) {
    const dx = x2 - x1;
    if (Math.abs(dx) < 1.5) return "M" + x1 + " " + y1 + "V" + y2;
    // Le couloir demandé, mais jamais collé à l'un des deux bouts : il faut de
    // quoi loger les deux arrondis et un morceau de droite de chaque côté.
    const bas = Math.min(y1, y2), haut = Math.max(y1, y2);
    // Sur un écart trop court — un office posé à hauteur de sa cible —, aucun
    // couloir ne tient : on coupe au milieu, sans quoi le premier segment droit
    // est de longueur nulle et le lien repart en biais dès son départ.
    let mi = (couloir == null || haut - bas < 26) ? (y1 + y2) / 2 : couloir;
    // La garde de bord cède elle aussi quand l'écart est court : bornée à cinq
    // pixels en dur, elle repoussait le couloir PAR-DESSUS le milieu sur un
    // écart de sept, et rendait le premier segment nul — la faute qu'elle
    // devait empêcher.
    const marge = Math.min(5, (haut - bas) / 3);
    mi = Math.max(bas + marge, Math.min(haut - marge, mi));
    const sgn = dx > 0 ? 1 : -1;
    // LE RAYON CÈDE AVANT LE TRACÉ, et il doit laisser un bout de droite de
    // chaque côté : un arrondi qui prend TOUT l'écart vertical rend le segment
    // de départ nul, et le lien repart en biais dès le premier pixel — ce qu'on
    // voulait supprimer. Deux pixels de droite au minimum à chaque bout.
    const DROIT = 2;
    const r = Math.max(1, Math.min(RAYON, Math.abs(dx) / 2,
      Math.abs(y1 - mi) - DROIT, Math.abs(mi - y2) - DROIT));
    return "M" + x1 + " " + y1 +
      "V" + (mi + r) +
      "Q" + x1 + " " + mi + "," + (x1 + sgn * r) + " " + mi +
      "H" + (x2 - sgn * r) +
      "Q" + x2 + " " + mi + "," + x2 + " " + (mi - r) +
      "V" + y2;
  }

  // Chaque bande trace SES marches, dans son propre calque : une pièce que la
  // coupe a mise en tête des deux bandes y a une copie de chaque côté, et le
  // tracé la cherche chez lui — c'est ce qui rend le pli sans casser l'arbre.
  function tracerLiens() {
    const damier = document.querySelector(".ech-damier");
    if (!damier) return;
    damier.querySelectorAll(".ech-bande").forEach(tracerBande);
  }

  function tracerBande(damier) {
    const a = affaire();
    // Pendant le changement d'affaire, la liste sommaire peut être courante
    // avant que son plateau détaillé (et donc `pieces`) soit arrivé.
    if (!damier || !a || !Array.isArray(a.pieces)) return;
    const svg = damier.querySelector(".ech-liens");
    if (!svg) return;
    const cadre = damier.getBoundingClientRect();
    if (!cadre.width || !cadre.height) return;   // panneau replié : rien à mesurer
    svg.setAttribute("viewBox", "0 0 " + cadre.width + " " + cadre.height);
    svg.style.width = cadre.width + "px";
    svg.style.height = cadre.height + "px";
    let d = '<defs>' +
      MARCHES.map((c) =>
        '<marker id="ech-fer-' + c + '" class="ech-fer-' + c + '" viewBox="0 0 8 8" ' +
        'refX="6.5" refY="4" markerWidth="5" markerHeight="5" orient="auto">' +
        '<path d="M0 1 7 4 0 7Z"/></marker>').join("") + "</defs>";
    const sceau = (cle) => {
      const n = damier.querySelector('.ech-pion[data-piece="' + cle + '"] .ech-sceau');
      if (!n) return null;
      const r = n.getBoundingClientRect();
      return { x: r.left - cadre.left + r.width / 2, haut: r.top - cadre.top,
               bas: r.bottom - cadre.top };
    };
    const marches = [];
    a.pieces.forEach((p) => {
      if (!p.vers || !p.vers.length) return;
      const o = sceau(p.cle);
      if (!o) return;
      const etat = etatMarche(p);
      p.vers.forEach((vid) => {
        const b = sceau(vid);
        if (b) marches.push({ de: p.cle, a: vid, o: o, b: b, etat: etat });
      });
    });

    // UN COULOIR PAR CIBLE. Sans cela, tous les liens d'un rang au suivant
    // tournent à la même hauteur : leurs segments horizontaux se recouvrent et
    // ne font plus qu'une barre en travers du plateau — le fouillis déplacé,
    // pas résolu. Les liens qui vont AU MÊME jeton partagent leur couloir et se
    // rejoignent en faisceau, ce qui est ce qu'on veut voir ; ceux qui vont
    // ailleurs passent chacun au sien, quelques pixels plus bas.
    const bandes = {};
    marches.forEach((m) => {
      const cle = Math.round(m.b.bas / 12) + "|" + m.a;
      if (!bandes[cle]) bandes[cle] = { bas: m.b.bas, x: m.b.x, cle: m.a };
    });
    const ordre = {};
    const parBande = {};
    Object.keys(bandes).forEach((k) => {
      const t = bandes[k], r = Math.round(t.bas / 12);
      (parBande[r] = parBande[r] || []).push(t);
    });
    Object.keys(parBande).forEach((r) => {
      parBande[r].sort((u, v) => u.x - v.x)
        .forEach((t, i) => { ordre[t.cle] = i; });
    });

    marches.forEach((m) => {
      const i = ordre[m.a] || 0;
      const ecart = 11 + (i % 4) * 7;
      const trait = coude(m.o.x, m.o.haut, m.b.x, m.b.bas, m.b.bas + ecart);
      d += '<path class="ech-lien ech-lien-' + m.etat + '" data-de="' + m.de +
        '" data-a="' + m.a + '" d="' + trait +
        '" marker-end="url(#ech-fer-' + m.etat + ')"/>';
    });
    svg.innerHTML = d;
  }

  // ---- la case, calculée sur la place qu'on a -----------------------------
  // Le plateau prend TOUT l'emplacement du décor, sans marge morte. La case
  // reste carrée et toutes les cases restent identiques — ce n'est pas la case
  // qui s'étire, c'est sa taille qui se calcule : la plus grande qui tienne à la
  // fois en largeur et en hauteur. Le plateau se centre sur ce qui reste.
  const GAP = 3, TETE = 10, ENTRE_BANDES = 18;
  const MAX = 260;
  const PAR_CASE = 4;      // ce qu'une case tient : deux sur deux, et pas une de plus
  const CASE_MIN = 30;     // sous quoi une case cesse d'être lisible

  // LA LARGEUR SE DONNE À CELUI QUI EN A BESOIN. Une colonne dont le rang le
  // plus chargé porte vingt-et-une pièces ne les montre pas dans un carré : à
  // 125 px de case, quinze d'entre elles étaient rognées et INVISIBLES — pas
  // serrées, absentes. Or le plateau n'occupait que la moitié de la largeur du
  // décor. Une colonne dense prend donc PLUSIEURS PISTES, et sa case devient un
  // rectangle couché ; les autres gardent leur carré. On n'ajoute une piste que
  // tant qu'elle ne coûte rien — c'est-à-dire tant que c'est la HAUTEUR qui
  // borne la case, jamais la largeur : de la place qui dormait, et rien d'autre.
  // UNE COLONNE PAR VERROU — et tout le reste rangé sous le verrou qu'il sert.
  //
  // Le plateau se lisait par état cible : deux colonnes pour cette affaire, et
  // quatre-vingt-quinze pièces à l'intérieur. Les liens n'avaient alors aucune
  // raison d'être courts, et le plan ne disait pas ce qu'il coûtait de dire.
  // Chaque verrou tient maintenant SA colonne, et chaque clef, action ou moyen
  // va dans celle du verrou auquel il remonte. Ce qui se voit alors n'est plus
  // une mise en page, c'est le PLAN : un verrou sous lequel il n'y a rien, un
  // autre qui porte à lui seul la moitié de l'affaire, une pièce qui sert trois
  // chaînes à la fois. On ne le déduit plus, on le regarde.
  //
  // Mesuré sur « Financement de la campagne » : 89 % des pièces remontent à un
  // verrou et un seul — l'affectation n'est donc presque jamais un arbitrage.
  function remontee(a) {
    if (a.remontee) return a.remontee;
    const P = {}; a.pieces.forEach((p) => { P[p.cle] = p; });
    const memo = {};
    const atteint = (cle, pile) => {
      if (memo[cle]) return memo[cle];
      if (pile[cle]) return {};              // le graphe peut boucler
      const p = P[cle];
      if (!p) return {};
      if (p.rang === "verrou") return { [cle]: 1 };
      pile[cle] = 1;
      const somme = {};
      (p.vers || []).forEach((v) => {
        const s = atteint(v, pile);
        Object.keys(s).forEach((k) => { somme[k] = (somme[k] || 0) + s[k]; });
      });
      delete pile[cle];
      memo[cle] = somme;
      return somme;
    };
    a.remontee = {};
    a.pieces.forEach((p) => {
      if (p.rang === "verrou" || !RANGS.some((r) => r.id === p.rang)) return;
      a.remontee[p.cle] = atteint(p.cle, {});
    });
    return a.remontee;
  }

  // Le plan de bataille du plateau : les colonnes-verrous, groupées sous leur
  // état cible pour que la canopée garde son arbre, et une colonne d'orphelins
  // au bout — ce qui ne remonte à AUCUN verrou est une information, pas un
  // déchet à cacher.
  const ORPHELINS = "__hors-plan";

  function disposer(a) {
    if (a.plan) return a.plan;
    const atteint = remontee(a);
    const P = {}; a.pieces.forEach((p) => { P[p.cle] = p; });
    const cols = [], parVerrou = {};
    const ajouter = (etat, verrou) => {
      const c = { etat: etat, verrou: verrou, pieces: {}, pistes: 1, partages: 0 };
      RANGS.forEach((r) => { c.pieces[r.id] = []; });
      cols.push(c);
      if (verrou) parVerrou[verrou] = c;
      return c;
    };
    a.colonnes.forEach((col) => {
      const siens = a.pieces.filter((p) => p.rang === "verrou" && p.colonne === col.id);
      if (!siens.length) { ajouter(col.id, null); return; }
      siens.forEach((v) => { ajouter(col.id, v.cle).pieces.verrou.push(v.cle); });
    });
    let perdus = null;
    a.pieces.forEach((p) => {
      if (p.rang === "verrou" || !RANGS.some((r) => r.id === p.rang)) return;
      const s = atteint[p.cle] || {};
      // LE VERROU DOMINANT : celui par où passent le plus de chemins. À égalité,
      // le plus à gauche, pour que deux pièces jumelles ne se séparent pas.
      let quel = null, poids = 0;
      Object.keys(s).forEach((k) => {
        if (!parVerrou[k]) return;
        if (s[k] > poids) { poids = s[k]; quel = k; }
      });
      const c = quel ? parVerrou[quel] : (perdus = perdus || ajouter(ORPHELINS, null));
      c.pieces[p.rang].push(p.cle);
      if (Object.keys(s).length > 1) c.partages++;
    });
    // LES VERROUS CREUX SE SERRENT. Un verrou sous lequel il n'y a rien n'a rien
    // à étaler : lui donner sa piste pleine, c'était payer dix pistes pour dix
    // jetons et affamer les colonnes qui portent le plan — mesuré ici, la case
    // tombait à 31 px pendant que trois cent soixante pixels de hauteur ne
    // servaient à rien. Ils se rassemblent donc par état cible, quatre par case
    // comme le reste. Ils restent VISIBLES, et c'est tout ce qui compte : un
    // verrou que rien ne lève doit se voir.
    const serres = [], reste = {};
    cols.forEach((c) => {
      const creux = !c.verrou || RANGS.every((r) =>
        r.id === "verrou" || !c.pieces[r.id].length);
      if (!creux) { serres.push(c); return; }
      if (!c.verrou) { serres.push(c); return; }
      let g = reste[c.etat];
      if (!g) {
        g = reste[c.etat] = { etat: c.etat, verrou: null, creuse: true,
          pieces: {}, pistes: 1, partages: 0 };
        RANGS.forEach((r) => { g.pieces[r.id] = []; });
        serres.push(g);
      }
      g.pieces.verrou.push(c.verrou);
    });
    serres.forEach((c) => {
      let max = 0;
      RANGS.forEach((r) => { if (c.pieces[r.id].length > max) max = c.pieces[r.id].length; });
      c.pistes = Math.max(1, Math.ceil(max / PAR_CASE));
    });
    a.plan = serres;
    return serres;
  }

  function pistesDe(a) {
    return disposer(a).map((c) => c.pistes);
  }

  // ---- LES BANDES ----------------------------------------------------------
  // Au-delà de DOUZE colonnes-verrous, le plateau se plie en deux. La coupe
  // tombe entre deux ÉTATS CIBLES et jamais au milieu de l'un d'eux : un état
  // et ses verrous forment un bloc, et l'on n'a pas démêlé les liens pour
  // recouper l'arbre en travers. Entre les coupes possibles, on prend celle qui
  // équilibre le mieux les PISTES — les colonnes n'ont pas la même largeur, et
  // c'est la piste, pas la colonne, qui coûte de la place.
  const AVANT_DE_PLIER = 12;

  function decouper(plan, etage) {
    const tout = [{ de: 0, fin: plan.length }];
    if (plan.length <= AVANT_DE_PLIER) return tout;
    const bornes = [];
    for (let i = 1; i < plan.length; i++) {
      if (plan[i].etat !== plan[i - 1].etat) bornes.push(i);
    }
    if (!bornes.length) return tout;
    const cumul = [0];
    plan.forEach((c, i) => { cumul[i + 1] = cumul[i] + c.pistes; });
    const total = cumul[plan.length];
    let quel = bornes[0], ecart = Infinity;
    bornes.forEach((i) => {
      const d = Math.abs(cumul[i] - (total - cumul[i]));
      if (d < ecart) { ecart = d; quel = i; }
    });
    return [{ de: 0, fin: quel }, { de: quel, fin: plan.length }];
  }

  // Une bande : un damier complet — sa canopée, ses réglettes, ses quatre rangs
  // — sur la tranche de colonnes qu'on lui donne. Le `.ech-damier` n'est plus
  // qu'un porteur, ce qui laisse intacts tous les gestes qui le fouillent (la
  // chaîne allumée, la bulle, les renvois par numéro).
  function batir(a, plan, etage, tr, P, ib) {
    const niv = a.niveaux || 1;
    const bande = document.createElement("div");
    bande.className = "ech-bande";
    bande.dataset.de = String(tr.de);
    bande.dataset.fin = String(tr.fin);
    let pistes = 0;
    for (let i = tr.de; i < tr.fin; i++) pistes += plan[i].pistes;
    bande.style.setProperty("--pistes", pistes);
    bande.style.setProperty("--niv", niv);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "ech-liens");
    svg.setAttribute("aria-hidden", "true");
    bande.appendChild(svg);

    // LA CANOPÉE — les états cibles ne sont pas une rangée, c'est un arbre.
    // Chaque état s'assied à son niveau et s'étend sur les colonnes de son
    // sous-arbre : celui qui ne porte aucun verrou n'a pas de colonne à lui, il
    // COIFFE celles de ses enfants. Un état qui débordait des deux côtés de la
    // coupe se retrouve en tête des DEUX bandes, taillé à ce qu'il y coiffe :
    // c'est un titre de colonne qui se répète en haut de page, pas un doublon.
    const gc = document.createElement("div");
    gc.className = "ech-gouttiere ech-gouttiere-cime rang-etat";
    gc.style.gridRow = "1 / span " + niv;
    gc.style.gridColumn = "1";
    gc.innerHTML = icone("etat");
    gc.addEventListener("mouseenter", () => {
      if (!epingle) montrer({ titre: CIME.nom, dit: CIME.sous }, gc);
    });
    gc.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
    bande.appendChild(gc);

    a.pieces.filter((p) => p.genre === "etat").forEach((p) => {
      const sous = (p.portee || []).filter((x) => etage[x]);
      if (!sous.length) return;
      let debut = Math.min.apply(null, sous.map((x) => etage[x].de));
      let fin = Math.max.apply(null, sous.map((x) => etage[x].de + etage[x].nb));
      debut = Math.max(debut, tr.de);
      fin = Math.min(fin, tr.fin);
      if (fin <= debut) return;
      const e = document.createElement("div");
      e.className = "ech-branche" + (p.rompu ? " ech-branche-rompue" : "");
      e.style.gridRow = String((p.niveau || 0) + 1);
      // La colonne définitive est posée par caler() : une colonne dense vaut
      // plusieurs pistes, et la branche coiffe des pistes, pas des colonnes.
      e.dataset.de = String(debut);
      e.dataset.nc = String(fin - debut);
      e.appendChild(jeton(p));
      bande.appendChild(e);
    });

    // LA RÉGLETTE EST LE VERDICT DE LA COLONNE-VERROU, et c'est le seul endroit
    // du plateau qui en rende un. Trois crans, et pas deux : ROUGE quand aucune
    // action n'en descend — le verrou est posé et rien ne le lève ; VERTE quand
    // au moins une de ses actions est déclarée en cours ou faite ; et l'encre
    // ordinaire entre les deux, qui dit la seule chose vraie : c'est écrit, ce
    // n'est pas porté. Rendue au verrou, elle vaut bien mieux qu'à l'état : le
    // verrou creux se voyait noyé dans le verdict de toute sa colonne.
    const coin = document.createElement("i");
    coin.style.gridRow = String(niv + 1);
    coin.style.gridColumn = "1";
    bande.appendChild(coin);
    for (let ci = tr.de; ci < tr.fin; ci++) {
      const c = plan[ci];
      const col = a.colonnes.filter((x) => x.id === c.etat)[0];
      const v = c.verrou ? P[c.verrou] : null;
      const creux = !c.pieces.action.length;
      const porte = c.pieces.action.some((k) => P[k] && P[k].porte);
      const e = document.createElement("div");
      e.className = "ech-reglette"
        + (creux ? " ech-reglette-rompue" : porte ? " ech-reglette-portee" : "");
      if (col) e.dataset.colonne = col.id;
      e.dataset.ci = String(ci);
      e.style.gridRow = String(niv + 1);
      e.addEventListener("mouseenter", () => {
        if (epingle) return;
        const compte = RANGS.map((r) => c.pieces[r.id].length);
        montrer({
          titre: v ? (v.titre || v.nom || "Verrou")
            : c.etat === ORPHELINS ? "Hors plan"
            : c.creuse ? c.pieces.verrou.length + " verrous sans suite"
            : (col ? col.titre : "Colonne"),
          dit: c.etat === ORPHELINS
            ? "ce qui ne remonte à aucun verrou : " + compte.slice(1).join(" · ")
            : c.creuse
            ? "posés" + (col ? " sous « " + col.titre + " »" : "") +
              ", et rien dessous pour les lever"
            : (v && v.dit ? v.dit : (col ? col.dit : "")),
          mal: creux
            ? (c.etat === ORPHELINS ? null
              : c.creuse ? "aucune clef, aucune action : ce sont des constats, pas un plan"
              : "aucune action ne descend de ce verrou — il est posé, rien ne le lève")
            : (c.partages
              ? c.partages + (c.partages > 1 ? " pièces servent" : " pièce sert")
                + " aussi d'autres verrous"
              : null)
        }, e);
      });
      e.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
      bande.appendChild(e);
    }

    RANGS.forEach((r, ri) => {
      const rangee = String(niv + 2 + ri);
      const g = document.createElement("div");
      g.className = "ech-gouttiere rang-" + r.id;
      g.style.gridRow = rangee;
      g.style.gridColumn = "1";
      g.innerHTML = icone(r.id === "moyen" ? "moyen" : r.id);
      g.addEventListener("mouseenter", () => {
        if (!epingle) montrer({ titre: r.nom, dit: r.sous }, g);
      });
      g.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
      bande.appendChild(g);

      let piste = 0;
      for (let ci = tr.de; ci < tr.fin; ci++) {
        const c = plan[ci];
        const dedans = c.pieces[r.id].map((k) => P[k]).filter(Boolean);
        // AUTANT DE CASES QUE LA COLONNE A DE PISTES, et non une case étirée :
        // c'est la règle des quatre pièces rendue VISIBLE. Chaque case garde son
        // cadre, son alternance et son carré ; celles dont ce rang n'a pas
        // besoin restent vides, ce qui se lit aussi bien qu'un jeton.
        const pj = c.pistes;
        // AU PRORATA, ET NON CENTRÉ. Centrer le bloc rendait les rangs légers
        // jolis et les liens longs : cinq clefs groupées au milieu d'une bande
        // de six pendaient loin de leurs vingt et une actions. Réparti sur toute
        // la bande, chaque clef tombe au-dessus des actions qui la servent.
        const n = dedans.length;
        const cases = [];
        for (let j = 0; j < pj; j++) cases.push([]);
        dedans.forEach((p, i) => { cases[Math.floor(i * pj / Math.max(1, n))].push(p); });
        for (let j = 0; j < pj; j++) {
          const case_ = document.createElement("div");
          case_.className = "ech-case rang-" + r.id + " c" + ((ri + piste + j) % 2);
          case_.style.gridRow = rangee;
          case_.dataset.ci = String(ci);
          case_.dataset.pj = String(j);
          cases[j].forEach((p) => case_.appendChild(jeton(p)));
          // Le compte du semis : c'est lui qui décide des sous-colonnes et de la
          // taille du sceau, à chaque mise en place.
          case_.dataset.n = String(cases[j].length);
          bande.appendChild(case_);
        }
        piste += pj;
      }
    });
    return bande;
  }

  function calculerCase() {
    const damier = document.querySelector(".ech-damier");
    const corps = document.querySelector(".ech-corps");
    const a = affaire();
    if (!damier || !corps || !a) return null;
    const cols = a.colonnes.length;
    if (!cols) return null;
    const r = corps.getBoundingClientRect();
    if (!r.width || !r.height) return null;
    // Ce qui coiffe le plateau est pris sur la place qui reste, sans quoi le
    // damier déborde par le bas de ce qu'il croit avoir et cesse d'être centré.
    let pris = 0;
    corps.childNodes.forEach((n) => {
      if (n.classList && !n.classList.contains("ech-damier") && n.offsetHeight) {
        pris += n.offsetHeight + (parseFloat(getComputedStyle(n).marginBottom) || 0);
      }
    });
    const gout = parseFloat(getComputedStyle(damier).getPropertyValue("--ech-gout")) || 22;
    const niv = a.niveaux || 1;
    const dispo = r.width - gout;
    const spans = pistesDe(a);
    // LA BANDE LA PLUS LARGE COMMANDE LA LARGEUR, et le nombre de bandes divise
    // la hauteur : les deux bandes partagent la même taille de case, sans quoi
    // le plateau se lirait comme deux plateaux.
    const bandes = decouper(disposer(a), null);
    let pistes = 0;
    bandes.forEach((tr) => {
      let n = 0;
      for (let i = tr.de; i < tr.fin; i++) n += spans[i];
      if (n > pistes) pistes = n;
    });
    const nb = bandes.length;
    // Quatre rangs de cases carrées, plus les étages de canopée qui valent
    // chacun une part de case : c'est ce dénominateur-là qu'on divise.
    const haut = (r.height - pris - nb * (TETE + GAP * (RANGS.length + niv))
      - ENTRE_BANDES * (nb - 1)) / (nb * (RANGS.length + BANDE * niv));
    const large = (dispo - GAP * pistes) / pistes;
    // Le nombre de cases ne se négocie pas contre la place : sur un panneau
    // trop étroit, c'est la case qui maigrit jusqu'au plancher, et au-delà le
    // plateau se laisse défiler. Escamoter des cases pour tenir dans la largeur
    // ferait mentir la règle des quatre au moment précis où elle sert.
    return { c: Math.max(CASE_MIN, Math.min(MAX, Math.floor(Math.min(large, haut)))),
      spans: spans, pistes: pistes };
  }

  // LE SEMIS D'UNE CASE SE COMPTE. Il était figé à deux jetons par rangée
  // (flex:1 1 45 %), donc vingt-et-une pièces faisaient onze rangées dans une
  // case qui n'en tient que deux — d'où le rognage : quinze jetons invisibles.
  // Une case ne porte plus que quatre pièces, et son semis est le carré qui va
  // avec : 1, 2 côte à côte, puis deux rangées. Le sceau y garde son calibre.
  function semis(n) {
    const lig = n <= 2 ? 1 : 2;
    return { sub: Math.max(1, Math.ceil(n / lig)), lig: lig };
  }

  // Les colonnes sont numérotées d'un bout à l'autre du plan ; chaque bande
  // repart de sa première piste. Le départ se compte donc DANS la bande.
  function caler(bande, spans) {
    const de = +bande.dataset.de || 0, fin = +bande.dataset.fin || spans.length;
    const depart = []; let t = 2;
    for (let i = de; i < fin; i++) { depart[i] = t; t += spans[i]; }
    bande.style.setProperty("--pistes", t - 2);
    const damier = bande;
    damier.querySelectorAll("[data-ci]").forEach((e) => {
      const i = +e.dataset.ci;
      if (!spans[i]) return;
      // Une case occupe UNE piste, à son rang dans la bande de sa colonne ; la
      // réglette, elle, coiffe toute la bande.
      if (!e.classList.contains("ech-case")) {
        e.style.gridColumn = depart[i] + " / span " + spans[i];
        return;
      }
      e.style.gridColumn = String(depart[i] + (+e.dataset.pj || 0));
      const s = semis(Math.max(1, +e.dataset.n || 0));
      e.style.setProperty("--span", 1);
      e.style.setProperty("--sub", s.sub);
      e.style.setProperty("--lig", s.lig);
    });
    damier.querySelectorAll(".ech-branche[data-de]").forEach((e) => {
      const d = +e.dataset.de, nc = +e.dataset.nc;
      let s = 0;
      for (let i = d; i < d + nc; i++) s += spans[i] || 0;
      e.style.gridColumn = (depart[d] || 2) + " / span " + Math.max(1, s);
    });
  }

  function ajuster() {
    const damier = document.querySelector(".ech-damier");
    const m = calculerCase();
    if (!damier || !m) return false;
    const sig = m.c + ":" + m.spans.join(",");
    if (damier.dataset.mise === sig) return false;
    damier.dataset.mise = sig;
    damier.style.setProperty("--ech-case", m.c + "px");
    // Un chiffre de trois pixels n'est plus un chiffre : sur une case serrée il
    // se retire, et le jeton redevient muet comme avant.
    damier.classList.toggle("ech-sans-chiffre", m.c < 44);
    damier.querySelectorAll(".ech-bande").forEach((b) => { caler(b, m.spans); });
    return true;
  }

  // On ajuste d'abord, on trace ensuite, et deux fois : tout de suite
  // (getBoundingClientRect force le calcul de mise en page, c'est déjà juste) et
  // à la frame suivante. Ne jamais s'appuyer sur la seule frame : un onglet en
  // arrière-plan n'en donne aucune.
  function replanter() {
    ajuster();
    tracerLiens();
    requestAnimationFrame(() => { ajuster(); tracerLiens(); });
  }

  function verifier() {
    const h = hote();
    if (!h || h.classList.contains("vue-off") || !affaire()) return;
    if (ajuster()) tracerLiens();
    else if (!h.querySelector(".ech-lien")) tracerLiens();
  }

  function surveiller() {
    const h = hote();
    if (!h) return;
    let prevu = null;
    const plusTard = () => {
      if (prevu) return;
      prevu = setTimeout(() => { prevu = null; verifier(); }, 80);
    };
    if (window.ResizeObserver) new ResizeObserver(plusTard).observe(h);
    window.addEventListener("resize", plusTard);
    setInterval(verifier, 2000);
  }

  // ---- le tracé ------------------------------------------------------------
  function dessiner() {
    const h = hote();
    if (!h) return;
    const a = affaire();
    // Un plateau dont on n'a que le chapeau ne se dessine pas : on va chercher
    // son cahier, et le tracé se fera au retour.
    if (a && !a.pieces) { ouvrir(a.id); return; }
    const sig = JSON.stringify([a && a.id, affaires.length]);
    if (sig === dessine && h.childNodes.length) { replanter(); return; }
    dessine = sig;
    h.innerHTML = "";
    if (!a) {
      h.innerHTML = '<p class="ech-rien">Aucune affaire n\'est ouverte au registre.</p>';
      return;
    }
    const corps = document.createElement("div");
    corps.className = "ech-corps";

    // LE CHEF DU PLATEAU : l'emblème de l'affaire courante, en grand, et à côté
    // la bascule — une tuile par affaire, chacune avec SON emblème, la courante
    // allumée et les autres en retrait. Rien d'écrit : le nom et l'objet se
    // lisent au survol, un clic change de plateau, un clic sur la courante ouvre
    // son volume. Un liseré rouge dit une affaire dont des colonnes ne
    // descendent jusqu'à aucune action — l'épreuve du guide, avant même
    // d'ouvrir le plateau.
    const bandeau = document.createElement("div");
    bandeau.className = "ech-affaires";

    const grand = document.createElement("button");
    grand.type = "button";
    grand.className = "ech-blason" + (a.rompues ? " ech-blason-rompu" : "");
    grand.dataset.affaire = a.id;
    grand.innerHTML = signe(a);
    grand.setAttribute("aria-label", a.titre);
    grand.addEventListener("mouseenter", () => { if (!epingle) montrer(surAffaire(a), grand); });
    grand.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
    grand.addEventListener("click", (ev) => { ev.stopPropagation(); ouvrirLivre(); });
    bandeau.appendChild(grand);

    // LE NOM DE L'AFFAIRE OUVERTE, en clair. Le blason la dit d'un coup d'œil,
    // le titre la nomme — sans lui, il fallait survoler pour savoir de quoi ce
    // plateau parle. Le « zéro texte » vaut pour le PLATEAU : les cases, les
    // jetons, la canopée, la gouttière. Ceci est hors du damier, comme l'était
    // le chapeau. Et seulement l'affaire ouverte : les autres restent des
    // emblèmes muets, c'est le contraste qui fait la lecture.
    const nomAffaire = document.createElement("h2");
    nomAffaire.className = "ech-titre";
    nomAffaire.textContent = a.titre;
    nomAffaire.addEventListener("mouseenter", () => {
      if (!epingle) montrer(surAffaire(a), nomAffaire);
    });
    nomAffaire.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
    nomAffaire.addEventListener("click", (ev) => { ev.stopPropagation(); ouvrirLivre(); });
    bandeau.appendChild(nomAffaire);

    // LA BASCULE : une liste déroulante, signe ET nom. Une rangée d'emblèmes
    // muets obligeait à survoler chaque tuile pour savoir de quelle affaire il
    // s'agissait — dix affaires, dix survols. Ici le nom est écrit à côté du
    // signe, et le déroulé ne prend la place qu'au moment où on le demande.
    // LE VOLUME : le plateau montre la forme d'une affaire, le cahier en porte
    // le texte. On passait de l'un à l'autre par un clic sur le blason, que
    // rien n'annonçait ; le chemin se voit désormais, et il se fait dans les
    // deux sens — les livres portent le bouton d'en face.
    const versLivre = document.createElement("button");
    versLivre.type = "button";
    versLivre.className = "ech-vers-livre";
    versLivre.innerHTML = '<i class="ech-chevron">📖</i><span>Le volume</span>';
    versLivre.title = "Ouvrir le cahier de cette affaire";
    versLivre.addEventListener("click", (ev) => { ev.stopPropagation(); ouvrirLivre(); });
    bandeau.appendChild(versLivre);

    // ---- À QUI CETTE AFFAIRE TIENT -------------------------------------------
    // Une rangée d'emblèmes, HORS DU DAMIER, et c'est tout. Le plateau montre la
    // forme d'UNE affaire ; ceci dit de qui elle dépend et qui dépend d'elle,
    // sans rien peindre sur les cases et sans proposer de remonter la chaîne
    // pièce à pièce — ce que personne ne veut faire à cette échelle.
    //
    // Chaque emblème est un chemin : un clic ouvre ce plateau-là. C'est la
    // première navigation du jeu qui suive le PLAN au lieu d'une liste — la
    // tirette aligne quarante et une affaires et ne sait rien de ce qui les
    // relie.
    //
    // L'ORDRE EST CELUI DU POIDS (le serveur l'a trié) : l'affaire à qui l'on
    // tient par onze arêtes passe avant celle qui n'en a qu'une. Et l'on borne :
    // au-delà, un compte, parce qu'une rangée de vingt emblèmes muets ne se lit
    // pas mieux que le chevron qu'on vient de retirer.
    const vs = a.voisines || [];
    if (vs.length) {
      const rang2 = document.createElement("div");
      rang2.className = "ech-voisines";
      vs.slice(0, SORTIES).forEach((v) => {
        const t = document.createElement("button");
        t.type = "button";
        t.className = "ech-voisine";
        t.innerHTML = v.embleme
          ? '<span class="ech-icone" aria-hidden="true">' + v.embleme + "</span>"
          : icone("affaire");
        // Le titre dit ce que l'emblème ne peut pas dire : le nom, et à quel
        // titre on y tient. On compte les arêtes, on ne les nomme pas une à une.
        const dit = Object.keys(v.sens || {})
          .sort((x, y) => v.sens[y] - v.sens[x])
          .map((s) => compte(v.sens[s], s)).join(", ");
        t.title = v.titre + (dit ? " — " + dit : "");
        t.setAttribute("aria-label", t.title);
        t.addEventListener("mouseenter", () => {
          if (!epingle) montrer({ titre: v.titre, dit: dit }, t);
        });
        t.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
        t.addEventListener("click", (ev) => {
          ev.stopPropagation();
          relacher();
          montrerAffaire(v.id);
        });
        rang2.appendChild(t);
      });
      if (vs.length > SORTIES) {
        const r = document.createElement("span");
        r.className = "ech-voisines-reste";
        r.textContent = "+" + (vs.length - SORTIES);
        r.title = vs.slice(SORTIES).map((v) => v.titre).join(" · ");
        rang2.appendChild(r);
      }
      bandeau.appendChild(rang2);
    }

    const autres = document.createElement("div");
    autres.className = "ech-bascule";

    const tirette = document.createElement("button");
    tirette.type = "button";
    tirette.className = "ech-tirette";
    tirette.setAttribute("aria-haspopup", "listbox");
    tirette.setAttribute("aria-expanded", "false");
    tirette.innerHTML = '<span class="ech-tirette-n">' + affaires.length +
      (affaires.length > 1 ? " affaires" : " affaire") + '</span><i class="ech-chevron">▾</i>';
    autres.appendChild(tirette);

    const liste = document.createElement("div");
    liste.className = "ech-liste";
    liste.setAttribute("role", "listbox");
    liste.hidden = true;
    affaires.forEach((x) => {
      const t = document.createElement("button");
      t.type = "button";
      t.className = "ech-choix" + (x.id === a.id ? " ech-choix-ici" : "") +
        (x.rompues ? " ech-choix-rompu" : "");
      t.dataset.affaire = x.id;
      t.setAttribute("role", "option");
      t.setAttribute("aria-selected", x.id === a.id ? "true" : "false");
      const sg = document.createElement("span");
      sg.className = "ech-choix-signe";
      sg.innerHTML = signe(x);
      const nm = document.createElement("span");
      nm.className = "ech-choix-nom";
      nm.textContent = x.titre;
      t.appendChild(sg);
      t.appendChild(nm);
      t.addEventListener("mouseenter", () => { if (!epingle) montrer(surAffaire(x), t); });
      t.addEventListener("mouseleave", () => { if (!epingle) cacher(); });
      t.addEventListener("click", (ev) => {
        ev.stopPropagation();
        replier();
        if (x.id === a.id) { ouvrirLivre(); return; }
        courante = x.id;
        try { localStorage.setItem(MEMOIRE, courante); } catch (err) {}
        cacher();
        ouvrir(courante);
      });
      liste.appendChild(t);
    });
    autres.appendChild(liste);

    function replier() {
      liste.hidden = true;
      tirette.setAttribute("aria-expanded", "false");
      document.removeEventListener("click", dehors, true);
      document.removeEventListener("keydown", echap, true);
      window.removeEventListener("resize", replier);
      window.removeEventListener("scroll", glisse, true);
    }
    function dehors(ev) { if (!autres.contains(ev.target)) replier(); }
    function echap(ev) { if (ev.key === "Escape") replier(); }
    // Le déroulé se replie quand la PAGE défile sous lui (il est ancré en
    // coordonnées d'écran, il partirait à la dérive) — pas quand c'est LUI
    // qu'on fait défiler : quarante affaires ne tiennent pas dans sa hauteur,
    // et un déroulé qui se referme à la molette ne se parcourt jamais.
    function glisse(ev) { if (!liste.contains(ev.target)) replier(); }
    tirette.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (!liste.hidden) { replier(); return; }
      liste.hidden = false;
      // Le corps de l'échiquier défile et rogne nécessairement ce qui le
      // dépasse. Le déroulé, lui, appartient à la fenêtre : on l'ancre sous
      // la tirette en coordonnées d'écran afin qu'aucune case ni aucun
      // conteneur intermédiaire ne puisse le cacher.
      const r = tirette.getBoundingClientRect();
      const largeur = Math.min(340, Math.max(230, window.innerWidth - 16));
      liste.style.width = largeur + "px";
      liste.style.left = Math.max(8, Math.min(r.right - largeur,
        window.innerWidth - largeur - 8)) + "px";
      liste.style.top = Math.min(r.bottom + 4,
        window.innerHeight - Math.min(640, window.innerHeight * .62) - 8) + "px";
      tirette.setAttribute("aria-expanded", "true");
      // Quarante affaires ne tiennent pas dans le déroulé : on l'ouvre sur
      // celle où l'on est, sinon la courante est hors de vue.
      const ici = liste.querySelector(".ech-choix-ici");
      if (ici) liste.scrollTop = Math.max(0, ici.offsetTop - liste.clientHeight / 2);
      document.addEventListener("click", dehors, true);
      document.addEventListener("keydown", echap, true);
      window.addEventListener("resize", replier);
      window.addEventListener("scroll", glisse, true);
    });

    bandeau.appendChild(autres);
    corps.appendChild(bandeau);

    // COMBIEN DE PISTES PAR COLONNE : une par tranche de quatre pièces du rang
    // le plus chargé. C'est fixé ici, une fois pour toutes, parce que ce sont
    // des CASES qu'on va poser — pas une largeur qu'on ajuste après coup.
    const plan = disposer(a);
    const larges = plan.map((c) => c.pistes);
    // Où commence chaque état cible dans la file des colonnes-verrous, et
    // combien il en coiffe : c'est ce qui rend son arbre à la canopée.
    const etage = {};
    plan.forEach((c, i) => {
      if (!c.etat || c.etat === ORPHELINS) return;
      if (!etage[c.etat]) etage[c.etat] = { de: i, nb: 0 };
      etage[c.etat].nb++;
    });
    // LE PLATEAU SE PLIE EN DEUX AU-DELÀ DE DOUZE COLONNES. Une colonne par
    // verrou rend le plan lisible et le plateau très large : dix-neuf pistes sur
    // quatre rangs, c'est une case affamée en largeur pendant que trois cents
    // pixels de hauteur ne servent à rien. On replie donc en deux bandes — et la
    // COUPE TOMBE ENTRE DEUX ÉTATS CIBLES, jamais au milieu de l'un d'eux : un
    // état et ses verrous restent d'une seule pièce, sinon on aurait démêlé les
    // liens pour recouper l'arbre.
    const damier = document.createElement("div");
    damier.className = "ech-damier";
    damier.style.setProperty("--cols", plan.length);
    damier.style.setProperty("--niv", a.niveaux || 1);

    const P = {}; a.pieces.forEach((p) => { P[p.cle] = p; });
    const coupes = decouper(plan, etage);
    damier.dataset.bandes = String(coupes.length);
    coupes.forEach((tr, ib) => {
      damier.appendChild(batir(a, plan, etage, tr, P, ib));
    });

    corps.appendChild(damier);
    h.appendChild(corps);
    indexer(a);
    replanter();
  }

  // ---- CHARGER, PLATEAU PAR PLATEAU ---------------------------------------
  // Trente-six cahiers font 2275 pièces : la route ne sert donc le DÉTAIL que
  // de l'affaire ouverte, et le chapeau des autres — de quoi tenir la bascule,
  // les comptes et la bulle du blason. Changer de plateau redemande la route,
  // et l'on garde ce qu'on a déjà reçu : on ne repaie pas deux fois le même
  // cahier dans une session.
  function ouvrir(id) {
    const x = affaires.find((a) => a.id === id);
    if (x && x.pieces) { dessine = ""; dessiner(); return; }
    fetch("/echiquier?affaire=" + encodeURIComponent(id))
      .then((r) => r.json()).then((d) => {
        const plein = (d.affaires || []).find((a) => a.pieces);
        if (plein) {
          const i = affaires.findIndex((a) => a.id === plein.id);
          if (i >= 0) affaires[i] = plein; else affaires.push(plein);
        }
        dessine = "";
        dessiner();
      }).catch(() => {});
  }

  function charger() {
    if (charge) return;
    charge = true;
    let veut0 = null;
    try { veut0 = localStorage.getItem(MEMOIRE); } catch (e) {}
    fetch("/echiquier" + (veut0 ? "?affaire=" + encodeURIComponent(veut0) : ""))
      .then((r) => r.json()).then((d) => {
      if (!d || !("affaires" in d)) throw new Error("route absente");
      affaires = d.affaires || [];
      // Les pièces ne portent que des adresses d'actes ; le texte est ici, une
      // fois pour toutes. Un acte réclamé par six pièces ne s'écrit qu'une fois.
      missions = d.missions || {};
      // UN PORTRAIT DOIT REMPLIR SON CADRE, pas s'y loger. Sans consigne, un
      // SVG carré posé dans un cadre haut se centre et laisse deux bandes
      // vides : on aurait agrandi le cadre sans agrandir le visage. `slice` le
      // fait couvrir et rogner par les côtés — c'est le cadrage d'un portrait,
      // et c'est la seule retouche qu'on fasse au dessin.
      portraits = {};
      Object.keys(d.portraits || {}).forEach((k) => {
        const svg = d.portraits[k];
        portraits[k] = /preserveAspectRatio/.test(svg) ? svg
          : svg.replace("<svg ", '<svg preserveAspectRatio="xMidYMid slice" ');
      });
      courante = d.ouverte || (affaires[0] || {}).id || null;
      dessine = "";
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
      // Les adresses du plan viennent d'arriver : ce qui attendait en texte nu
      // dans le fil peut s'allumer. Même geste que pour l'étagère et les gens —
      // un renvoi poussé avant nous resterait mort pour toute la session.
      if (window.Renvois && Renvois.raviver) Renvois.raviver();
      // Et l'on repasse dans les DEUX SENS sur ceux qui étaient déjà jugés :
      // un numéro que l'étagère avait servi avant nous devient une pièce du
      // plan, et une pièce qu'on vient d'effacer d'un cahier redevient du
      // texte nu. Les registres ne font pas que grandir.
      if (window.Renvois && Renvois.rafraichir) Renvois.rafraichir();
    }).catch(() => { charge = false; });
  }

  function relire() { charge = false; dessine = ""; charger(); }

  window.addEventListener("DOMContentLoaded", () => {
    charger();
    surveiller();
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "echiquier", nom: "L'échiquier", hote: "echiquier", ordre: 2.5,
        // Partout, y compris pendant le chargement et quand ce siège ne voit
        // encore aucune affaire. La boîte reste sous la Table Peinte dans la
        // fiction ; l'échelle est une vue de travail, et son état vide est une
        // information plutôt qu'une raison de faire disparaître sa porte.
        dispo: () => true,
        reparu: () => { dessiner(); replanter(); },
      });
    }
    // L'endroit, ici, c'est l'affaire qu'on lit — le plateau n'en montre qu'une.
    if (window.Nav) {
      Nav.enregistrer("echiquier", {
        clefs: ["affaire"],
        etat: () => ({ affaire: courante }),
        poser: (p) => {
          if (!p.affaire || p.affaire === courante) return true;
          if (!affaires.length) return false;   // les registres n'ont pas fini de rentrer
          return montrerAffaire(p.affaire);
        },
      });
    }
    document.addEventListener("click", () => { if (epingle) relacher(); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && epingle) relacher();
    });
    // Ce qu'une main a désigné en parlant tombe au changement de scène, comme
    // les pièces posées sur la table peinte : c'est une démonstration, pas un
    // fait acquis.
    if (window.Bus && Bus.enregistrer) Bus.enregistrer("effacer", oublier);
    // (plus de veille sur la salle : la disponibilité ne dépend plus du lieu)
  });

  return { charger, relire, connait, sorte, nom, designer, oublier,
           pourLivre, montrer: montrerAffaire, fermer: relacher,
           relacher: relacherDesignation };
})();
