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

  // Des encres, pas des couleurs de graphique : elles doivent tenir ensemble
  // sur du parchemin sans qu'aucune ne crie plus fort que les autres.
  const TEINTES = [
    "#8c2f39", "#2f5d8c", "#3f7a4d", "#8a6a1f", "#6a3f7a", "#2f7a78",
    "#a3542a", "#4a5a2f", "#7a2f5d", "#365b7a", "#7a5a2f", "#4f3f8c",
  ];
  function teinte(a) {
    if (a && a.teinte) return a.teinte;
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
    [/\bpages?\b|courrier|messager|porteur\b|servante|valet|cuisin|[ée]chanson/i, "✉"],
    [/porte-parole|parle pour|h[ée]raut/i, "🗣"],
    [/chuchoteur|espion|secret|ombre/i, "👁"],
    [/consort|[ée]poux|[ée]pouse|\bmari\b/i, "💍"],
    [/compagne|suivante|dame de compagnie|camari/i, "❦"],
    [/castellan|capitaine|sergent|\bgardes?\b|\bguet\b|chevalier|^ser\b|\bd'armes\b|garnison|[ée]p[ée]e/i, "⚔"],
    [/ma[iî]tre de port|\bmarin|p[êe]cheurs?\b|\bquai\b|d[ée]barquement|\bnefs?\b|\bvoiles?\b|saunier|amiral|flotte|mar[ée]es|serpent de mer|navire/i, "⚓"],
    [/tailleu|verredragon|obsidienne|\bforge|ma[çc]on|fosses\b/i, "⚒"],
    [/berger|\bsel\b|marais|paysan|laboureur|s[ée]choir/i, "🌾"],
    [/main du roi|chancelier|\bconseil\b|intendant|compt|cassette|registre|clerc|\blivre\b|\br[ôo]les?\b/i, "🗝"],
    [/cavali[eè]re? d|cavalier d|\bdragons?\b|\bvol\b|patrouille|\baile\b/i, "🐉"],
    [/\breine\b|\broi\b|\bprince\b|princesse|h[ée]riti|couronn[ée]|tr[ôo]ne/i, "👑"],
    [/\blord\b|seigneur|\bsire\b/i, "🏰"],
    [/\bdame\b|\blady\b|fille|fils/i, "❦"],
  ];
  function office(a) {
    if (a && a.embleme) return a.embleme;          // forcé à la main
    // Faute de titre — un garde de passage, un page sans fiche —, l'id dit
    // souvent l'office à lui seul : « page-ossy », « vieux-pecheur ».
    // Trois sources dans l'ordre, chacune rattrapant le silence de la
    // précédente : le titre affiché, le titre du registre (`office`), puis l'id.
    const essais = [a && a.titre, a && a.office, String((a && a.id) || "").replace(/-/g, " ")]
      .map((x) => String(x || "").split(/[;,—]/)[0].trim()).filter(Boolean);
    for (const t of essais) {
      for (const [re, e] of OFFICES) if (re.test(t)) return e;
    }
    return "";
  }

  // Ils sont douze dans la même salle : on ne les empile pas. Un seul reste au
  // centre ; les autres se rangent en couronne autour, puis en second cercle.
  // La couronne se DÉCALE aussi en x, d'un demi-pas par rang : deux rangs
  // parfaitement concentriques alignent leurs taches sur le même rayon et l'œil
  // y lit une colonne au lieu d'une foule. La graine garde le décalage stable.
  function couronne(n, r, cle) {
    if (n <= 1) return [[0, 0]];
    const sem = graine("c" + (cle || n));
    const p = [];
    const parRang = (i) => (i === 0 ? Math.min(n, 6) : 12);
    let pose = 0, rang = 0;
    while (pose < n) {
      const c = Math.min(n - pose, parRang(rang));
      const R = r * (2.45 + rang * 2.25);
      const dx = (rang % 2 ? .55 : -.35) * r;      // le rang se pousse de biais
      for (let i = 0; i < c; i++) {
        const th = -Math.PI / 2 + (i + (rang % 2 ? .5 : 0)) / c * Math.PI * 2;
        p.push([Math.cos(th) * R + dx + (sem() - .5) * r * .5,
                Math.sin(th) * R * .82]);
      }
      pose += c; rang++;
    }
    return p;
  }

  // Le signe complet, dans son repère : à charge de l'appelant de le translater.
  // `trait` : l'épaisseur du contour, dans les unités de SA carte.
  function marque(a, r, trait, classes) {
    const sem = graine("t" + ((a && (a.id || a.nom)) || ""));
    return '<g class="tache-gens ' + (classes || "") +
      (a.joueur ? " tache-joueur" : "") +
      '" data-id="' + esc(a.id || "") + '" data-nom="' + esc(a.nom || a.id || "") +
      '" style="color:' + esc(teinte(a)) + '">' +
      "<title>" + esc([a.nom, a.titre, a.ou_dit, a.detail].filter(Boolean).join(" — ")) + "</title>" +
      (a.joueur ? '<circle class="halo" r="' + (r * 1.5).toFixed(2) + '" stroke-width="' +
        (trait * 1.4).toFixed(2) + '"/>' : "") +
      '<path class="tache" d="' + contour(r, sem) + '" stroke-width="' + trait.toFixed(2) + '"/>' +
      '<text class="initiales" y="' + (r * .38).toFixed(2) + '" font-size="' +
      (r * 1.06).toFixed(2) + '">' + esc(initiales(a)) + "</text>" +
      // le signe de l'office se pose en pastille, à l'épaule droite : il se lit
      // avant les lettres et dit d'un coup d'œil qui fait quoi dans la salle
      (office(a) ? '<circle class="office-fond" cx="' + (r * .92).toFixed(2) + '" cy="' +
        (-r * .92).toFixed(2) + '" r="' + (r * .62).toFixed(2) + '" stroke-width="' +
        trait.toFixed(2) + '"/><text class="office" x="' + (r * .92).toFixed(2) + '" y="' +
        (-r * .62).toFixed(2) + '" font-size="' + (r * .86).toFixed(2) + '">' +
        office(a) + "</text>" : "") + "</g>";
  }

  return { teinte, initiales, distinguer, office, contour, couronne, marque, graine };
})();
