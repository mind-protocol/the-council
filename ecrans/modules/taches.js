// taches.js — un homme sur une carte : une tache d'encre de sa couleur, ses
// initiales dedans. Rien de plus, et c'est le point : à l'échelle d'un plan ou
// d'une île, un portrait ne tient pas, mais savoir que Rulf Corne est au quai
// et le mestre à la roukerie vaut tous les mots.
//
// Le même signe sert deux cartes qui n'ont rien d'autre en commun — le château
// (`plan.js`, salle par salle) et la ville ou le champ (`terrain.js`, au point
// près. D'où ce module : la couleur, les deux lettres et la forme de la tache
// se décident ici, une fois, pour que le même homme se reconnaisse d'une
// échelle à l'autre.
"use strict";
window.Taches = (() => {
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  // Un hasard reproductible : sans graine, les taches bouillonneraient à chaque
  // redessin de la carte.
  function graine(s) {
    let h = 2166136261;
    for (let i = 0; i < String(s).length; i++) {
      h ^= String(s).charCodeAt(i); h = Math.imul(h, 16777619);
    }
    return () => {
      h += 0x6D2B79F5;
      let t = h;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // SANS OFFICE, PAS DE COULEUR — des encres neutres, et elles ne croisent
  // aucune de celles d'en dessous. C'était un tirage sur douze teintes vives
  // partagées avec les offices : une bardesse tombait exactement sur le bleu
  // des marins, et la carte affirmait un rôle qu'elle n'avait pas. Quatre
  // grisailles suffisent à ne pas confondre deux voisins sans rien prétendre.
  const TEINTES = ["#6f6a60", "#5f5a55", "#7a7268", "#544f4a"];

  // LA COULEUR DIT L'OFFICE, pas la personne. Elle était tirée d'un hachage de
  // l'id : deux couleurs voisines ne voulaient rien dire, et une salle de douze
  // taches était un jeu de billes. Or ce qu'on cherche sur un plan, ce n'est
  // jamais « où est le n° 7 », c'est « où sont mes gardes » et « qui tient la
  // roukerie » — une question de rôle, à laquelle une couleur répond du premier
  // coup d'œil, de loin, et sans lire les lettres.
  //
  // La table est indexée PAR LE SIGNE et non par un mot-clef à part : le signe
  // et sa couleur sortent du même test, donc ils ne peuvent pas diverger quand
  // on retouchera `OFFICES`. Un signe sans couleur ici retombe sur le hachage,
  // et un office ajouté demain marche sans qu'on ait rien à faire.
  const COULEURS = {
    "⚔": "#8c2f39",   // les armes : le sang
    "📜": "#2f5d8c",  // la chaîne : l'encre
    "⚓": "#2f7a78",  // la mer
    "🗝": "#8a6a1f",  // les comptes et les registres : l'or terni
    "👑": "#5d2f7a",  // la couronne : le pourpre
    "🏰": "#365b7a",  // les seigneurs : l'ardoise
    "🐉": "#b0472b",  // les dragons : la braise
    "🌾": "#4a5a2f",  // la terre et le sel
    "⚒": "#6b4a33",  // la forge et la taille
    "✧": "#6a3f7a",  // la foi
    "👁": "#3a3350",  // ce qui se chuchote : presque noir
    "⛓": "#4a4a52",  // les fers
    "💍": "#7a2f5d",  // ce qui lie
    "❦": "#8c5a6a",  // la maison, les dames, les suivantes
    "✉": "#5d6b7a",  // ce qui porte : le gris du papier
    "🗣": "#a3542a",  // la parole : le cuivre
    "🍼": "#9c5b6b",  // le berceau
  };
  function teinte(a) {
    if (a && a.teinte) return a.teinte;            // forcée à la main : elle gagne
    const c = COULEURS[office(a)];
    if (c) return c;
    // Sans office reconnu, une grisaille : mieux vaut une couleur qui ne dit
    // rien qu'une couleur qui ment sur un rôle.
    let h = 0;
    const s = String((a && (a.id || a.nom)) || "");
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    return TEINTES[h % TEINTES.length];
  }

  const PARTICULES = /^(de|des|du|la|le|les|d|l|von|the|dit|dite)$/i;
  // un titre n'est pas un nom : « Ser Robert Quince » fait RQ, pas SQ
  const TITRES = /^(ser|sire|mestre|grand|septa|septon|dame|messire|prince|princesse|roi|reine|lord|lady|maistre|nourrice|capitaine|sergent)$/i;
  function initiales(a) {
    if (a && a.initiales) return String(a.initiales).slice(0, 2).toUpperCase();
    // Ce qui suit une virgule est une épithète, pas un nom : « Rhaenys
    // Targaryen, la Reine Qui Ne Fut Jamais » fait RT, jamais RJ.
    let mots = String((a && (a.nom || a.id)) || "?").split(",")[0]
      .replace(/[«»"]/g, " ")
      .split(/[\s'’-]+/).filter((m) => m && !PARTICULES.test(m));
    const sansTitre = mots.filter((m) => !TITRES.test(m));
    if (sansTitre.length) mots = sansTitre;
    if (!mots.length) return "?";
    if (mots.length === 1) return mots[0].slice(0, 2).toUpperCase();
    return (mots[0][0] + mots[mots.length - 1][0]).toUpperCase();
  }

  // Deux Targaryen dans la même salle font deux fois « RT », et la carte ment.
  // Quand deux voisins tombent sur les mêmes lettres, la seconde devient la
  // première lettre par laquelle leurs PRÉNOMS diffèrent : Rhaenyra fait RR,
  // Rhaenys fait RS. On pose le résultat en `initiales`, que `marque` respecte.
  function distinguer(gens) {
    const par = new Map();
    gens.forEach((g) => {
      const c = initiales(g);
      if (!par.has(c)) par.set(c, []);
      par.get(c).push(g);
    });
    par.forEach((groupe) => {
      if (groupe.length < 2) return;
      const prenoms = groupe.map((g) => String(g.nom || g.id || "").split(",")[0]
        .split(/[\s'’-]+/).filter((m) => !TITRES.test(m))[0] || "");
      let i = 1;
      while (i < 12 && new Set(prenoms.map((p) => p[i] || "")).size < prenoms.length) i++;
      groupe.forEach((g, k) => {
        const c = prenoms[k][i];
        g.initiales = c ? (prenoms[k][0] + c).toUpperCase() : initiales(g);
      });
    });
    return gens;
  }

  // Une tache, pas un disque : un rayon qui hésite autour du cercle.
  function contour(r, sem) {
    const n = 11, pts = [];
    for (let i = 0; i < n; i++) {
      const a = i / n * Math.PI * 2, d = r * (.84 + sem() * .34);
      pts.push([Math.cos(a) * d, Math.sin(a) * d]);
    }
    const mi = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    let m = mi(pts[n - 1], pts[0]);
    let d = "M" + m[0].toFixed(2) + " " + m[1].toFixed(2);
    for (let i = 0; i < n; i++) {
      const s = pts[i], q = mi(pts[i], pts[(i + 1) % n]);
      d += "Q" + s[0].toFixed(2) + " " + s[1].toFixed(2) + " " + q[0].toFixed(2) + " " + q[1].toFixed(2);
    }
    return d + "Z";
  }

  // L'office, en un signe. Le titre suffit à le dire — c'est déjà par lui qu'on
  // reconnaît les gens dans le fil. Un homme sans office n'a pas de signe :
  // mieux vaut rien qu'un symbole passe-partout qui ne distingue personne.
  //
  // Deux précautions, apprises à l'essai : on ne lit que la PREMIÈRE clause du
  // titre (ce qui suit un « ; » ou une virgule dit d'où l'on vient, pas ce qu'on
  // fait — « Septa de la maison de la reine ; élève Aegon » n'est pas une
  // reine) ; et tout se borne aux limites de mot, sans quoi Peyredragon fait
  // des dragons de tout le monde et le verredragon d'une tailleuse aussi.
  // L'ordre compte : du plus précis au plus vague, le premier qui prend gagne.
  //
  // C'est la table de TOUT le jeu : `bus.js` s'y branche pour les emblèmes du
  // fil et de la galerie. Un homme porte donc le même signe à côté de son nom
  // et sur la carte — sans quoi on lit deux jeux de symboles pour les mêmes
  // gens.
  const OFFICES = [
    [/\bprisonni|lev[ée]e? des terres|\bcachots?\b|\bfers\b/i, "⛓"],
    [/\bmestre\b|maester|cha[iî]ne de/i, "📜"],
    [/\bsepta\b|\bsepton\b|silencieuse|\bfoi\b|\bdieux\b/i, "✧"],
    [/nourrice|berceau/i, "🍼"],
    // « coureur de la reine » est le titre que le registre donne à Tobb et à
    // Nesse : ils portent ses mots sur la route, et rien ne les distinguait
    // d'un inconnu faute de ce mot-là.
    [/\bpages?\b|courrier|coureu[rs]e?\b|messager|porteur\b|servante|valet|cuisin|[ée]chanson/i, "✉"],
    [/porte-parole|parle pour|h[ée]raut|ma[iî]tresse? de la voix|\bde la voix\b/i, "🗣"],
    [/chuchoteur|espion|secret|ombre/i, "👁"],
    [/consort|[ée]poux|[ée]pouse|\bmari\b/i, "💍"],
    [/compagne|suivante|dame de compagnie|camari/i, "❦"],
    [/castellan|capitaine|sergent|\bgardes?\b|\bguet\b|chevalier|^ser\b|\bd'armes\b|garnison|[ée]p[ée]e/i, "⚔"],
    [/ma[iî]tre d[eu] port|\bmarin|p[êe]cheurs?\b|\bbarques?\b|\bquai\b|\bm[ôo]le\b|d[ée]barquement|\bnefs?\b|\bvoiles?\b|saunier|amiral|flotte|mar[ée]es|serpent de mer|navire/i, "⚓"],
    [/tailleu|verredragon|obsidienne|\bforge|ma[çc]on|fosses\b/i, "⚒"],
    [/berger|\bsel\b|marais|paysan|laboureur|s[ée]choir/i, "🌾"],
    [/main du roi|chancelier|\bconseil\b|intendant|compt|cassette|registre|clerc|\blivre\b|\br[ôo]les?\b|\bdeniers?\b|\bcoffres?\b/i, "🗝"],
    [/cavali[eè]re? d|cavalier d|\bdragons?\b|\bvol\b|patrouille|\baile\b/i, "🐉"],
    [/\breine\b|\broi\b|\bprince\b|princesse|h[ée]riti|couronn[ée]|tr[ôo]ne/i, "👑"],
    [/\blord\b|seigneur|\bsire\b/i, "🏰"],
    [/\bdame\b|\blady\b|fille|fils/i, "❦"],
  ];
  // « Maître des deniers DE LA REINE » n'est pas une reine, et « qui porte les
  // mots DE SER Robert » n'est pas un chevalier : un complément de nom dit à
  // QUI l'on sert, pas ce qu'on fait. La faute passait inaperçue tant que la
  // couleur était tirée au hasard — dès qu'elle a dit l'office, la moitié du
  // conseil de Peyredragon est apparue couronnée. On ôte donc le génitif avant
  // de chercher, et ce qui reste est bien le métier.
  const GENITIF = new RegExp(
    "\\b(?:de\\s+la|de\\s+l['’]|de\\s+las?|du|des|de|d['’])\\s+" +
    "(?:reines?|rois?|princesses?|princes?|couronnes?|tr[ôo]nes?|" +
    "ser|sire|messire|lords?|ladys?|dames?|septas?|mestres?)\\b\\s*\\S*", "gi");
  function sansGenitif(t) {
    return String(t).replace(GENITIF, " ").replace(/\s+/g, " ").trim();
  }

  function office(a) {
    if (a && a.embleme) return a.embleme;          // forcé à la main
    // Faute de titre — un garde de passage, un page sans fiche —, l'id dit
    // souvent l'office à lui seul : « page-ossy », « vieux-pecheur ».
    // Trois sources dans l'ordre, chacune rattrapant le silence de la
    // précédente : le titre affiché, le titre du registre (`office`), puis l'id.
    const essais = [a && a.titre, a && a.office, String((a && a.id) || "").replace(/-/g, " ")]
      .map((x) => sansGenitif(String(x || "").split(/[;,—]/)[0].trim())).filter(Boolean);
    for (const t of essais) {
      for (const [re, e] of OFFICES) if (re.test(t)) return e;
    }
    return "";
  }

  // ---- ce que l'homme porte : la taille du rond --------------------------
  //
  // TOUTES LES TACHES AVAIENT LA MÊME TAILLE, et la carte disait donc que le
  // mestre et un page pèsent pareil sur le plan. Or `criticite.py --acteurs`
  // sait ce que chacun porte — la criticité des pas dont son office répond —,
  // et c'est le seul chiffre du jeu qui réponde à « sur qui tout repose ». On
  // le fait porter par le RAYON, qui est ce que l'œil lit avant la couleur et
  // avant les lettres.
  //
  // L'ÉCHELLE EST EN RACINE, pas en linéaire : la charge s'étale de 1.2 à 134,
  // et un rapport de cent entre deux ronds donne une punaise à côté d'une
  // soucoupe. La racine ramène l'écart à ce qu'un plan peut montrer sans que
  // les petits disparaissent.
  //
  // UN INCONNU VAUT 1, ET CE N'EST PAS ZÉRO. Un figurant sans office n'a pas
  // de charge écrite : ce n'est pas qu'il ne porte rien, c'est qu'on ne l'a
  // pas mesuré. On lui laisse donc la taille de référence plutôt que le
  // minimum — la carte ne doit pas affirmer une légèreté qu'elle ignore.
  const PLANCHER = .72, PLAFOND = 1.34, BONUS_JOUEUR = 1.18;
  let charges = null, maxPorte = 0, demande = false;

  // Les identifiants du plan et ceux du registre ne se recouvrent pas tout à
  // fait — le plan écrit `jacaerys`, le registre `jacaerys-velaryon`, et
  // l'inverse arrive aussi. On replie le court sur le long, JAMAIS au milieu
  // d'un mot : `wenda-du-marais` ne prend pas la charge de `wend`. C'est le
  // même repli que `rapprocher()` côté script, avec le même angle mort assumé
  // (`nesse-la-mere` héritera de `nesse`).
  function porte(a) {
    if (!charges) return 0;
    const id = String((a && a.id) || "");
    if (!id) return 0;
    if (charges[id] != null) return charges[id];
    for (const k in charges) {
      if (id.indexOf(k + "-") === 0 || k.indexOf(id + "-") === 0) return charges[k];
    }
    return 0;
  }

  function facteur(a) {
    const p = porte(a);
    const k = (!p || !maxPorte) ? 1
      : PLANCHER + (PLAFOND - PLANCHER) * Math.sqrt(p / maxPorte);
    return k * (a && a.joueur ? BONUS_JOUEUR : 1);
  }

  // Un seul appel pour tout le jeu, et il ne bloque rien : les cartes se
  // dessinent à taille égale tant qu'il n'est pas rentré, puis se redessinent.
  // `/criticite` coûte une seconde et demie de python au premier appel du
  // serveur — on ne la fait pas attendre à un plan.
  function chargerCharges() {
    if (demande || typeof fetch !== "function") return;
    demande = true;
    fetch("/criticite").then((r) => r.json()).then((d) => {
      const a = (d && d.acteurs) || null;
      if (!a) return;
      charges = {};
      Object.keys(a).forEach((k) => { charges[k] = +a[k].porte || 0; });
      maxPorte = Math.max(0, ...Object.keys(charges).map((k) => charges[k]));
      // Les cartes s'abonnent : aucune ne connaît ce module autrement que par
      // `marque()`, et l'on ne veut pas que ce module connaisse les cartes.
      try {
        document.dispatchEvent(new CustomEvent("taches-charges"));
      } catch (e) { /* un navigateur sans CustomEvent : tant pis, ça se redessine */ }
    }).catch(() => { demande = false; });
  }

  // ---- ranger une foule sans l'empiler ------------------------------------
  //
  // LA COURONNE NE SAVAIT PAS CE QU'ELLE RANGEAIT. Elle posait `n` points sur
  // des anneaux de rayon fixe, en supposant toutes les taches de la même
  // taille — ce qui était vrai jusqu'à ce que la criticité les fasse varier du
  // simple au double. Depuis, deux gros voisins se recouvrent sur un anneau
  // calculé pour des moyens, et le jitter aléatoire qui devait « casser les
  // colonnes » fabrique ses propres collisions.
  //
  // On range donc en deux temps, et le second est le vrai :
  //  1. UN SEMIS, pas des anneaux. La spirale de Vogel (angle d'or) répartit n
  //     points sans jamais les aligner — c'est ce que les anneaux décalés à la
  //     main essayaient d'imiter, en moins bien. Son échelle sort de l'AIRE
  //     totale à loger, donc elle s'ouvre d'elle-même quand les taches
  //     grossissent.
  //  2. UNE RELAXATION. Tant qu'il reste des paires qui se touchent, on les
  //     écarte chacune de la moitié du recouvrement, puis on retasse doucement
  //     vers le centre pour ne pas laisser la foule s'étaler. Vingt passes
  //     suffisent ; c'est du O(n²) sur des salles de vingt personnes, donc
  //     quelques centaines d'opérations par salle et par redessin.
  //
  // DÉTERMINISTE, et il le faut : la graine porte la clef de la salle, donc la
  // même salle se redessine à l'identique toutes les quinze secondes. Une
  // foule qui bouillonne à chaque `/presence` est illisible.
  //
  // `borne: [ax, ay]` confine les taches dans l'ellipse de la pièce. Quand la
  // pièce est trop petite pour la foule, le confinement gagne et il RESTE des
  // recouvrements — c'est voulu : mieux vaut douze personnes serrées dans leur
  // salle que trois qui débordent sur le couloir.
  const ANGLE_OR = Math.PI * (3 - Math.sqrt(5));

  function rayonDe(x, base) {
    if (typeof x === "number") return x;
    return base * ((x && x.taille) || 1) * facteur(x);
  }

  function ranger(items, base, cle, opts) {
    const o = opts || {};
    const n = items.length;
    if (n <= 0) return [];
    // Ce qui déborde de la tache doit être compté avec elle : la pastille des
    // initiales sort à 1.28 rayon de l'épaule, et le halo du joueur plus loin
    // encore. Sans ça, deux taches « qui ne se touchent pas » se marchent quand
    // même dessus par leurs coins — ce qu'on voyait à la porte du Dragon.
    const R = items.map((x) => rayonDe(x, base) * (x && x.joueur ? 1.3 : 1.14));
    if (n === 1) return [[0, 0]];
    const marge = base * .16;
    const sem = graine("r" + (cle || n));

    // 1. le semis. `c` sort de l'aire : la somme des disques, étalée sur un
    // disque de même aire, donne le pas de la spirale à un facteur près.
    let aire = 0;
    R.forEach((r) => { aire += (r + marge) * (r + marge); });
    const c = 1.9 * Math.sqrt(aire / n);
    // les plus gros au centre : ils y tiennent moins de place qu'au bord, et
    // c'est aussi là qu'on les cherche
    const ordre = R.map((r, i) => i).sort((a, b) => R[b] - R[a]);
    const p = new Array(n);
    ordre.forEach((idx, k) => {
      const th = k * ANGLE_OR, d = c * Math.sqrt(k);
      p[idx] = [Math.cos(th) * d + (sem() - .5) * base * .12,
                Math.sin(th) * d + (sem() - .5) * base * .12];
    });

    // 2. la relaxation
    const [ax, ay] = o.borne || [0, 0];
    const PASSES = 30, TASSE = 18;
    for (let pas = 0; pas < PASSES; pas++) {
      let bouge = 0;
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          let dx = p[j][0] - p[i][0], dy = p[j][1] - p[i][1];
          let d = Math.hypot(dx, dy);
          const min = R[i] + R[j] + marge;
          if (d >= min) continue;
          // exactement superposés : on les sépare dans une direction stable
          if (d < 1e-6) { const a = sem() * Math.PI * 2; dx = Math.cos(a); dy = Math.sin(a); d = 1; }
          const e = (min - d) / 2, ux = dx / d, uy = dy / d;
          p[i][0] -= ux * e; p[i][1] -= uy * e;
          p[j][0] += ux * e; p[j][1] += uy * e;
          bouge += e;
        }
      }
      // On retasse : sans ce rappel, chaque poussée est définitive et la foule
      // enfle d'une passe à l'autre au lieu de se réarranger. Mais SEULEMENT
      // dans les premières passes — retasser après la dernière séparation
      // recrée exactement le recouvrement qu'on vient de défaire, et c'est ce
      // qui laissait deux ou trois paires en contact à l'arrivée.
      if (pas < TASSE) {
        for (let i = 0; i < n; i++) { p[i][0] *= .97; p[i][1] *= .97; }
      }
      // LE MUR EST MOU, ET C'EST DÉLIBÉRÉ. Un confinement dur reporte tout le
      // manque de place sur les recouvrements : la Table Peinte à sept gardait
      // une paire superposée de deux unités parce que personne n'avait le droit
      // de sortir. Or déborder un peu d'une pièce se lit très bien — deux
      // taches l'une sur l'autre, non. On ne ramène donc que la MOITIÉ du
      // dépassement : la foule reste dans ses murs quand elle y tient, et
      // déborde franchement quand elle n'y tient pas.
      if (ax && ay) {
        for (let i = 0; i < n; i++) {
          const bx = Math.max(1, ax - R[i]), by = Math.max(1, ay - R[i]);
          const q = Math.hypot(p[i][0] / bx, p[i][1] / by);
          if (q > 1) {
            const t = 1 + (q - 1) * .5;
            p[i][0] /= t; p[i][1] /= t;
          }
        }
      }
      if (bouge < base * .01) break;
    }
    return p;
  }

  // L'ancienne porte, pour qui n'a que des taches de même taille : on ne veut
  // pas deux algorithmes de placement dans le même jeu.
  function couronne(n, r, cle) {
    return ranger(new Array(n).fill(r), r, cle);
  }

  // Le signe complet, dans son repère : à charge de l'appelant de le translater.
  // `trait` : l'épaisseur du contour, dans les unités de SA carte.
  //
  // LE RÔLE D'ABORD. Le signe de l'office tenait dans une pastille à l'épaule,
  // grosse comme la moitié d'une lettre : à l'échelle d'un plan, on ne le voyait
  // pas. Or ce qu'on cherche sur une carte, c'est « où sont mes gardes », pas
  // « où est RQ » — le rôle se lit de loin, le nom se lit de près. On les
  // échange donc : le signe occupe le cœur de la tache, les initiales passent à
  // l'épaule pour départager deux hommes du même office. Sans office reconnu,
  // rien ne bouge : les lettres restent au centre, seules.
  function marque(a, r, trait, classes) {
    const sem = graine("t" + ((a && (a.id || a.nom)) || ""));
    // Le facteur se prend ICI et pas chez l'appelant : le plan, la ville et le
    // champ passent tous par cette porte, et une échelle qui vaut sur une
    // carte et pas sur l'autre est pire que pas d'échelle du tout.
    chargerCharges();
    r = r * facteur(a);
    const e = office(a), lettres = esc(initiales(a));
    // LA PASTILLE ÉTAIT UNE SECONDE TACHE. Reprise telle quelle du signe
    // d'office qu'elle remplace, elle faisait 72 % de la largeur du rond : deux
    // lettres claires sur fond clair, posées à cheval sur le bord, tiraient
    // l'œil AVANT l'emblème qu'on venait de mettre au centre — et débordaient
    // sur le voisin. Le rôle d'abord veut dire que le nom passe après : on la
    // rentre dans l'épaule et on la réduit de moitié. Deux lettres y restent
    // lisibles au zoom du plan, et c'est le seul endroit où on les lit.
    const coeur = e
      ? '<text class="office" y="' + (r * .46).toFixed(2) + '" font-size="' +
        (r * 1.34).toFixed(2) + '">' + e + "</text>"
      : '<text class="initiales" y="' + (r * .38).toFixed(2) + '" font-size="' +
        (r * 1.06).toFixed(2) + '">' + lettres + "</text>";
    // deux lettres tiennent mal dans un rond : la pastille est une ellipse
    const ex = r * .78, ey = -r * .78;
    const epaule = e
      ? '<ellipse class="office-fond" cx="' + ex.toFixed(2) + '" cy="' + ey.toFixed(2) +
        '" rx="' + (r * .50).toFixed(2) + '" ry="' + (r * .36).toFixed(2) +
        '" stroke-width="' + (trait * .8).toFixed(2) +
        '"/><text class="initiales-epaule" x="' + ex.toFixed(2) + '" y="' +
        (ey + r * .15).toFixed(2) + '" font-size="' + (r * .42).toFixed(2) + '">' +
        lettres + "</text>"
      : "";
    return '<g class="tache-gens ' + (classes || "") +
      (a.joueur ? " tache-joueur" : "") +
      '" data-id="' + esc(a.id || "") + '" data-nom="' + esc(a.nom || a.id || "") +
      '" style="color:' + esc(teinte(a)) + '">' +
      "<title>" + esc([a.nom, a.titre, a.ou_dit, a.detail].filter(Boolean).join(" — ")) + "</title>" +
      // deux anneaux d'or : un serré qui cerne la tache, un large et pâle qui
      // se voit de loin quand le plan est dézoomé et que la tache fait trois
      // pixels. C'est le seul homme qu'on doit trouver sans le chercher.
      (a.joueur ? '<circle class="halo-loin" r="' + (r * 2.15).toFixed(2) +
        '" stroke-width="' + (trait * 2.2).toFixed(2) + '"/>' +
        '<circle class="halo" r="' + (r * 1.5).toFixed(2) + '" stroke-width="' +
        (trait * 1.6).toFixed(2) + '"/>' : "") +
      '<path class="tache" d="' + contour(r, sem) + '" stroke-width="' + trait.toFixed(2) + '"/>' +
      coeur + epaule + "</g>";
  }

  return { teinte, initiales, distinguer, office, contour, couronne, ranger,
           marque, graine, porte, facteur, couleurs: COULEURS };
})();
