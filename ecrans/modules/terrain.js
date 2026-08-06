// terrain.js — la troisième échelle : le champ, vu du dessus.
// Le royaume dit OÙ porte la guerre, le château dit qui est à trois portes de
// moi. Le terrain dit ce que mille hommes occupent réellement de sol, et dans
// quel ordre ils s'y tiennent.
//
// Un corps n'est plus un jeton : c'est un semis de CERCLES en formation, un
// cercle valant toujours le même nombre d'hommes sur tout le champ
// (`par_cercle`). Deux blocs se comparent donc à l'œil, sans lire un chiffre —
// c'est tout l'intérêt de descendre à cette échelle.
//
// Différence de traitement avec la table peinte : là-haut, une pièce est un
// SYMBOLE et garde sa taille à l'écran quel qu'en soit le cadrage. Ici, un
// homme occupe du SOL : les cercles et les formations sont en unités du champ
// et grossissent avec lui quand on approche. Seuls les textes, leurs décalages
// et les épaisseurs de trait restent constants (var(--k)).
//
// Ce champ n'est pas la vérité du monde : c'est ce que le joueur en sait. Un
// corps dont il ignore la position n'y figure pas ; un corps mal compté porte sa
// `certitude`.
//
// Le même dessin sert DEUX échelles, et c'est voulu : le champ (`/terrain`,
// `etat/terrain.json`) et la ville (`/ville`, `etat/ville.json`). Une ville vue
// du dessus pose exactement le même problème qu'un champ — du sol, et des corps
// dessus, chacun là où il se tient réellement. Seuls changent la route, l'hôte
// et le mot qu'on met sur la bascule. D'où la fabrique ci-dessous, instanciée
// deux fois en bas de fichier.
"use strict";
function ChampVu(o) {
  const P = o.id;                   // "terrain" | "ville" : préfixe des ids DOM
  let champ = null;                 // le champ courant, ou null : rien à montrer
  let vueVignette = null, vueGrande = null;

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  const chiffre = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

  // Un hasard reproductible : le semis d'un bois, la gîte d'un fuyard. Sans
  // graine, le décor bouillonnerait à chaque redessin de la loupe.
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

  // ---- le sol --------------------------------------------------------------
  const GENRES_SOL = {
    route: { bande: true, largeur: 7 },
    riviere: { bande: true, largeur: 6 },
    haie: { bande: true, largeur: 2.4 },
    bois: { aire: true }, champ: { aire: true }, marais: { aire: true },
    colline: { aire: true }, village: { semis: true },
    // ce qu'une ville a de plus qu'un champ : de l'eau qu'on ne traverse pas,
    // des murs qui ferment, une grève et des quais où l'on débarque
    eau: { aire: true }, greve: { aire: true },
    mur: { bande: true, largeur: 3 }, quai: { bande: true, largeur: 4 },
  };

  // Une polyligne lissée : on passe par les milieux, les sommets deviennent des
  // points de contrôle. Un chemin de terre n'a pas d'angles droits.
  function chemin(pts, ferme, brut) {
    if (!pts || pts.length < 2) return "";
    const p = pts.map((q) => [+q[0], +q[1]]);
    const mi = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    let d;
    // un champ a des bords droits : c'est un homme qui l'a tracé à la charrue
    if (brut) {
      return "M" + p.map((q) => q[0].toFixed(1) + " " + q[1].toFixed(1)).join("L") +
        (ferme ? "Z" : "");
    }
    if (ferme) {
      let m = mi(p[p.length - 1], p[0]);
      d = "M" + m[0].toFixed(1) + " " + m[1].toFixed(1);
      for (let i = 0; i < p.length; i++) {
        const s = p[i], n = mi(p[i], p[(i + 1) % p.length]);
        d += "Q" + s[0].toFixed(1) + " " + s[1].toFixed(1) + " " + n[0].toFixed(1) + " " + n[1].toFixed(1);
      }
      return d + "Z";
    }
    d = "M" + p[0][0].toFixed(1) + " " + p[0][1].toFixed(1);
    for (let i = 1; i < p.length - 1; i++) {
      const n = mi(p[i], p[i + 1]);
      d += "Q" + p[i][0].toFixed(1) + " " + p[i][1].toFixed(1) + " " + n[0].toFixed(1) + " " + n[1].toFixed(1);
    }
    const f = p[p.length - 1];
    return d + "L" + f[0].toFixed(1) + " " + f[1].toFixed(1);
  }

  const centroide = (p) => [p.reduce((s, q) => s + q[0], 0) / p.length,
                            p.reduce((s, q) => s + q[1], 0) / p.length];
  function dedans(p, x, y) {          // rayon lancé : le semis reste dans le bois
    let d = false;
    for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
      if ((p[i][1] > y) !== (p[j][1] > y) &&
          x < (p[j][0] - p[i][0]) * (y - p[i][1]) / (p[j][1] - p[i][1]) + p[i][0]) d = !d;
    }
    return d;
  }

  function unSol(s, i, k) {
    const g = GENRES_SOL[s.genre] || {};
    const cl = "sol sol-" + esc(s.genre || "champ");
    const t = s.nom ? "<title>" + esc(s.nom) + "</title>" : "";

    if (g.bande) {
      // un chemin de terre n'a pas d'angles droits, mais un mur si : on ne
      // lisse pas ce qui a été bâti à l'équerre
      const d = chemin(s.points, false, s.brut || s.genre === "mur");
      const w = s.largeur || g.largeur;
      return '<g class="' + cl + '">' + t +
        '<path class="sol-corps" d="' + d + '" stroke-width="' + w.toFixed(1) + '"/>' +
        '<path class="sol-bord" d="' + d + '" stroke-width="' + (w + 1.4 * k).toFixed(2) + '"/>' +
        "</g>";
    }
    if (g.semis) {                    // un hameau : quelques toits posés de biais
      const r = graine("v" + i);
      return '<g class="' + cl + '">' + t + (s.points || []).map((p) => {
        const c = 3 + r() * 2.4, a = (r() * 40 - 20).toFixed(0);
        return '<rect class="toit" x="' + (p[0] - c / 2).toFixed(1) + '" y="' +
          (p[1] - c / 2).toFixed(1) + '" width="' + c.toFixed(1) + '" height="' +
          (c * .78).toFixed(1) + '" transform="rotate(' + a + " " + p[0] + " " + p[1] + ')"/>';
      }).join("") + "</g>";
    }

    // une aire : bois, champ, marais, tertre
    const pts = s.points || [];
    const d = s.d || chemin(pts, true, s.genre === "champ");
    let dedansTxt = "";
    if (s.genre === "bois" && pts.length > 2) {
      const r = graine("b" + i);
      const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
      const x0 = Math.min(...xs), x1 = Math.max(...xs);
      const y0 = Math.min(...ys), y1 = Math.max(...ys);
      const n = Math.min(55, Math.max(6, Math.round((x1 - x0) * (y1 - y0) / 95)));
      for (let j = 0, pose = 0; j < n * 5 && pose < n; j++) {
        const x = x0 + r() * (x1 - x0), y = y0 + r() * (y1 - y0);
        if (!dedans(pts, x, y)) continue;
        pose++;
        dedansTxt += '<circle class="arbre" cx="' + x.toFixed(1) + '" cy="' +
          y.toFixed(1) + '" r="' + (1 + r() * .8).toFixed(1) + '"/>';
      }
    }
    if (s.genre === "colline" && pts.length > 2) {
      // deux courbes de niveau : la seconde rentrée vers le sommet
      const c = centroide(pts);
      const inte = pts.map((p) => [c[0] + (p[0] - c[0]) * .58, c[1] + (p[1] - c[1]) * .58]);
      dedansTxt += '<path class="niveau" d="' + chemin(inte, true) + '"/>';
    }
    return '<g class="' + cl + '">' + t +
      '<path class="sol-corps" d="' + d + '"/>' + dedansTxt + "</g>";
  }

  // ---- les formations ------------------------------------------------------
  // Un semis de cercles dans un repère local : +x vers l'avant, +y vers la
  // droite. La rotation vient après, une fois pour tout le corps.
  function disposition(n, forme, pas, sem) {
    const rangs = [], px = pas * 1.12, py = pas;
    const rangee = (r, largeur, decale) => {
      for (let f = 0; f < largeur; f++) {
        rangs.push([-r * px, (f - (largeur - 1) / 2) * py + (decale || 0)]);
      }
    };
    if (forme === "coin") {
      let reste = n, r = 0;
      while (reste > 0) { const l = Math.min(reste, r + 1); rangee(r, l); reste -= l; r++; }
    } else if (forme === "essaim" || forme === "tas") {
      const R = Math.sqrt(n) * pas * (forme === "tas" ? .48 : .78);
      for (let i = 0; i < n; i++) {
        // spirale de Vogel : un semis dense qui ne fait pas de trous
        const a = i * 2.399963, d = R * Math.sqrt((i + .5) / n);
        rangs.push([Math.cos(a) * d + (sem() - .5) * pas * .5,
                Math.sin(a) * d + (sem() - .5) * pas * .5]);
      }
    } else if (forme === "deroute") {
      // ce qui reste d'un corps rompu : ça part vers l'arrière et ça s'étale
      for (let i = 0; i < n; i++) {
        const t = i / Math.max(1, n - 1);
        rangs.push([-t * pas * n * .55 - sem() * pas,
                (sem() - .5) * pas * (2.5 + t * 9)]);
      }
    } else {
      let front;
      if (forme === "colonne") front = 4;
      else if (forme === "file") front = 2;
      else if (forme === "carre") front = Math.max(2, Math.round(Math.sqrt(n)));
      else front = Math.max(3, Math.ceil(n / (forme === "ligne3" ? 3 : 2)));  // ligne
      let reste = n, r = 0;
      while (reste > 0) { const l = Math.min(reste, front); rangee(r, l); reste -= l; r++; }
    }
    return rangs;
  }

  const FORMES_DESORDRE = { deroute: 1, essaim: .55, tas: .35 };
  const GENRES_CORPS = {
    pique: { r: 1.5 }, infanterie: { r: 1.5 },
    cavalerie: { r: 1.9, oeil: true },
    archers: { r: 1.15 }, prisonniers: { r: 1.25 }, convoi: { r: 1.6, carre: true },
    dragon: { r: 5.4, silhouette: "dragon" },
    // Tout ce qui se joue sur cent pas n'est pas une bataille : une cour où deux
    // partis se font face en est une aussi. Des convives ne sont pas des troupes
    // — ils n'ont ni cap ni rangs — mais ils occupent du sol, et c'est bien le
    // sol qu'on est venu regarder à cette échelle.
    convives: { r: 1.35, mot: "personnes" },
    // et ce qu'une ville porte : des gens qui ne sont pas des troupes, et des
    // coques. Une nef n'est pas un cercle non plus — c'est une longueur.
    gens: { r: 1.2, mot: "personnes" },
    nef: { r: 2.4, silhouette: "nef", mot: "voiles" },
  };

  // Vu du dessus, un dragon posé n'est pas un cercle : c'est une envergure. On
  // le dessine dans son repère (+x = le museau) et on le tourne avec le corps.
  function silhouetteDragon(r) {
    const f = (n) => (n * r).toFixed(2);
    const aile = (s) => "M" + f(.35) + " " + f(.18 * s) +
      "C" + f(.15) + " " + f(1.25 * s) + " " + f(-.85) + " " + f(1.85 * s) +
      " " + f(-1.55) + " " + f(1.25 * s) +
      "C" + f(-1.1) + " " + f(.75 * s) + " " + f(-.5) + " " + f(.55 * s) +
      " " + f(-.15) + " " + f(.3 * s) + "Z";
    return '<path class="aile" d="' + aile(1) + '"/><path class="aile" d="' + aile(-1) + '"/>' +
      '<path class="echine" d="M' + f(-1.5) + ' 0Q' + f(-.2) + " " + f(-.42) + " " +
      f(1.45) + " 0Q" + f(-.2) + " " + f(.42) + " " + f(-1.5) + ' 0Z"/>' +
      '<path class="queue" d="M' + f(-1.45) + " 0Q" + f(-2.2) + " " + f(.35) + " " +
      f(-2.9) + ' 0"/>' +
      '<circle class="museau" cx="' + f(1.62) + '" cy="0" r="' + f(.26) + '"/>';
  }
  // Vue du dessus, une coque : proue en +x, un banc de nage en travers.
  function silhouetteNef(r) {
    const f = (n) => (n * r).toFixed(2);
    return '<path class="coque" d="M' + f(1.5) + " 0Q" + f(.2) + " " + f(-.62) + " " +
      f(-1.3) + " " + f(-.44) + "L" + f(-1.45) + " " + f(.44) + "Q" + f(.2) + " " +
      f(.62) + " " + f(1.5) + ' 0Z"/>' +
      '<line class="banc" x1="' + f(-.1) + '" y1="' + f(-.52) + '" x2="' + f(-.1) +
      '" y2="' + f(.52) + '"/>';
  }

  const NOM_GENRE = {
    pique: "Piques", infanterie: "Gens de pied", cavalerie: "Cavalerie",
    archers: "Archers", prisonniers: "Prisonniers", convoi: "Convoi", dragon: "Dragon",
    convives: "À table", gens: "Gens du bourg", nef: "Nefs et barques",
  };
  const NOM_ETAT = {
    ordre: "en ordre", ebranle: "ébranlé", rompu: "rompu", fuite: "en fuite",
    rendu: "rendu", mort: "à terre",
  };

  function unCorps(c, k, parCercle) {
    const genre = GENRES_CORPS[c.genre] || GENRES_CORPS.pique;
    // `taille` : le même genre ne pèse pas pareil sur cent pas et sur une lieue.
    const g = c.taille ? Object.assign({}, genre, { r: genre.r * c.taille }) : genre;
    const sem = graine(c.id || c.nom || "corps");
    const n = Math.max(1, Math.min(90, c.cercles ||
      Math.round((c.hommes || parCercle) / parCercle)));
    const forme = c.formation || "ligne";
    const pas = c.pas || g.r * 1.95;      // les rangs se touchent sans se manger
    let P = disposition(n, forme, pas, sem);

    // un corps ébranlé n'a plus ses rangs au cordeau
    const flou = FORMES_DESORDRE[forme] ? 0 : (c.etat === "ebranle" ? .5 : c.etat === "rompu" ? 1 : 0);
    if (flou) P = P.map((p) => [p[0] + (sem() - .5) * pas * flou, p[1] + (sem() - .5) * pas * flou]);

    const a = ((c.cap || 0) - 90) * Math.PI / 180;   // 0 = le nord, 90 = l'est
    const av = [Math.cos(a), Math.sin(a)], dr = [-Math.sin(a), Math.cos(a)];
    const [cx, cy] = c.centre || [0, 0];
    const monde = P.map((p) => [cx + av[0] * p[0] + dr[0] * p[1],
                                cy + av[1] * p[0] + dr[1] * p[1]]);

    const cl = "corps corps-" + esc(c.genre || "pique") + " camp-" + esc(c.camp || "neutre") +
      " cert-" + esc(c.certitude || "sure") + " etat-" + esc(c.etat || "ordre");
    const detail = [c.nom, NOM_GENRE[c.genre] || "",
      c.hommes ? chiffre(c.hommes) + " " + (g.mot || "hommes") : "",
      NOM_ETAT[c.etat] || "", c.detail || "",
      c.certitude && c.certitude !== "sure" ? "(" + esc(c.certitude) + ")" : ""]
      .filter(Boolean).join(" — ");

    let s = '<g class="' + cl + '" data-id="' + esc(c.id || "") + '" data-nom="' +
      esc(c.nom || NOM_GENRE[c.genre] || "corps") + '"><title>' + esc(detail) + "</title>";

    // le sens de marche, tant que le corps en a un — une silhouette dit déjà
    // le sien par sa forme, elle n'a pas besoin qu'on le lui pointe
    if (!FORMES_DESORDRE[forme] && c.cap != null && !g.silhouette) {
      const t = Math.max(...monde.map((p) => (p[0] - cx) * av[0] + (p[1] - cy) * av[1])) + g.r + 3;
      const pointe = [cx + av[0] * t, cy + av[1] * t];
      const aile = 2.6 + g.r;
      s += '<path class="cap" d="M' +
        (pointe[0] - av[0] * aile + dr[0] * aile).toFixed(1) + " " +
        (pointe[1] - av[1] * aile + dr[1] * aile).toFixed(1) + "L" +
        pointe[0].toFixed(1) + " " + pointe[1].toFixed(1) + "L" +
        (pointe[0] - av[0] * aile - dr[0] * aile).toFixed(1) + " " +
        (pointe[1] - av[1] * aile - dr[1] * aile).toFixed(1) +
        '" stroke-width="' + (1.3 * k).toFixed(2) + '"/>';
    }

    monde.forEach((p) => {
      const rr = g.r * (c.etat === "mort" ? .7 : 1);
      if (g.silhouette === "nef") {
        s += '<g class="nef" transform="translate(' + p[0].toFixed(1) + "," +
          p[1].toFixed(1) + ") rotate(" + ((c.cap || 0) - 90).toFixed(0) + ')" ' +
          'stroke-width="' + (.9 * k).toFixed(2) + '">' + silhouetteNef(rr) + "</g>";
        return;
      }
      if (g.silhouette === "dragon") {
        s += '<g class="dragon" transform="translate(' + p[0].toFixed(1) + "," +
          p[1].toFixed(1) + ") rotate(" + ((c.cap || 0) - 90).toFixed(0) + ')" ' +
          'stroke-width="' + (1 * k).toFixed(2) + '">' + silhouetteDragon(rr) + "</g>";
        return;
      }
      if (g.carre) {
        s += '<rect class="homme" x="' + (p[0] - rr).toFixed(1) + '" y="' +
          (p[1] - rr).toFixed(1) + '" width="' + (rr * 2).toFixed(1) + '" height="' +
          (rr * 2).toFixed(1) + '" stroke-width="' + (.9 * k).toFixed(2) + '"/>';
      } else {
        s += '<circle class="homme" cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) +
          '" r="' + rr.toFixed(2) + '" stroke-width="' + (.9 * k).toFixed(2) + '"/>';
      }
      if (g.oeil) {
        s += '<circle class="monte" cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) +
          '" r="' + (rr * .34).toFixed(2) + '"/>';
      }
    });

    // Le nom se pose HORS du bloc, du côté opposé au gros de l'action : sur un
    // champ, les corps se touchent, et six noms empilés au même endroit ne
    // valent pas mieux que pas de noms du tout. `etiq` (en unités du champ,
    // depuis le centre du corps) tranche à la main quand c'est trop serré.
    const ext = g.r * (g.silhouette ? 1.9 : 1);
    const bo = monde.reduce((b, p) => [Math.min(b[0], p[0] - ext), Math.min(b[1], p[1] - ext),
      Math.max(b[2], p[0] + ext), Math.max(b[3], p[1] + ext)], [1e9, 1e9, -1e9, -1e9]);
    const mil = [(bo[0] + bo[2]) / 2, (bo[1] + bo[3]) / 2];
    let ou, ancre;
    if (c.etiq) {
      ou = [cx + c.etiq[0], cy + c.etiq[1]];
      ancre = c.ancre || (c.etiq[0] > 3 ? "start" : c.etiq[0] < -3 ? "end" : "middle");
    } else {
      const r0 = repere();
      let v = [mil[0] - (r0[0] + r0[2] / 2), mil[1] - (r0[1] + r0[3] / 2)];
      const n0 = Math.hypot(v[0], v[1]) || 1;
      v = [v[0] / n0, v[1] / n0];
      ou = [mil[0] + v[0] * ((bo[2] - bo[0]) / 2 + 3 * k),
            mil[1] + v[1] * ((bo[3] - bo[1]) / 2 + 3 * k) + (v[1] >= 0 ? 4.5 : -1.5) * k];
      ancre = v[0] > .45 ? "start" : v[0] < -.45 ? "end" : "middle";
    }
    // Aucun nom ne sort du champ : au besoin il se retourne contre le bord.
    const rr0 = repere();
    const larg = (String(c.nom || "").length + (c.hommes ? 5 : 0)) * 2.5 * k;
    const bord = 2 * k;
    let g0 = ancre === "start" ? ou[0] : ancre === "end" ? ou[0] - larg : ou[0] - larg / 2;
    if (g0 + larg > rr0[0] + rr0[2] - bord) {
      ancre = "end"; ou[0] = rr0[0] + rr0[2] - bord; g0 = ou[0] - larg;
    }
    if (g0 < rr0[0] + bord) { ancre = "start"; ou[0] = rr0[0] + bord; }
    ou[1] = Math.max(rr0[1] + 5 * k, Math.min(ou[1], rr0[1] + rr0[3] - 2 * k));

    s += '<text class="corps-nom" text-anchor="' + ancre + '" x="' + ou[0].toFixed(1) +
      '" y="' + ou[1].toFixed(1) + '">' + esc(c.nom || "") +
      (c.hommes ? '<tspan class="corps-compte"> · ' + chiffre(c.hommes) + "</tspan>" : "") +
      "</text>";
    return s + "</g>";
  }

  // ---- ce qui est arrivé au sol -------------------------------------------
  function unFait(f, i, k) {
    const [x, y] = f.centre || [0, 0];
    const R = f.rayon || 10;
    const sem = graine("f" + i + (f.id || ""));
    const cl = "fait fait-" + esc(f.genre || "note");
    const t = (f.nom || f.detail) ? "<title>" + esc([f.nom, f.detail].filter(Boolean).join(" — ")) + "</title>" : "";
    let s = '<g class="' + cl + '">' + t;

    if (f.genre === "feu") {
      // une brûlure n'est pas un disque : on fait tourner un rayon qui hésite
      const pts = [];
      for (let a = 0; a < 18; a++) {
        const th = a / 18 * Math.PI * 2, r = R * (.62 + sem() * .55);
        pts.push([x + Math.cos(th) * r, y + Math.sin(th) * r * .78]);
      }
      s += '<path class="brulure" d="' + chemin(pts, true) + '"/>';
      for (let j = 0; j < 9; j++) {
        const th = sem() * Math.PI * 2, r = R * sem();
        s += '<circle class="cendre" cx="' + (x + Math.cos(th) * r).toFixed(1) +
          '" cy="' + (y + Math.sin(th) * r * .78).toFixed(1) + '" r="' +
          (.7 + sem() * 1.3).toFixed(1) + '"/>';
      }
    } else if (f.genre === "morts") {
      for (let j = 0; j < Math.max(4, Math.round(R * .9)); j++) {
        const th = sem() * Math.PI * 2, r = R * Math.sqrt(sem());
        const px = x + Math.cos(th) * r, py = y + Math.sin(th) * r;
        const a2 = sem() * Math.PI;
        s += '<line class="mort" x1="' + (px - Math.cos(a2) * 1.4).toFixed(1) +
          '" y1="' + (py - Math.sin(a2) * 1.4).toFixed(1) +
          '" x2="' + (px + Math.cos(a2) * 1.4).toFixed(1) +
          '" y2="' + (py + Math.sin(a2) * 1.4).toFixed(1) +
          '" stroke-width="' + (1 * k).toFixed(2) + '"/>';
      }
    } else if (f.genre === "melee") {
      const e = R * .7;
      s += '<path class="fers" d="M' + (x - e) + " " + (y - e) + "L" + (x + e) + " " + (y + e) +
        "M" + (x + e) + " " + (y - e) + "L" + (x - e) + " " + (y + e) +
        '" stroke-width="' + (1.6 * k).toFixed(2) + '"/>';
    }
    if (f.nom) {
      s += '<text class="fait-nom" x="' + x.toFixed(1) + '" y="' +
        (y + R * .82 + 5 * k).toFixed(1) + '">' + esc(f.nom) + "</text>";
    }
    return s + "</g>";
  }

  // ---- la carte du champ ---------------------------------------------------
  const repere = () => (champ && champ.repere) || [0, 0, 200, 140];
  const parCercle = () => (champ && champ.par_cercle) || 25;

  function cadre(spec) {
    const r = repere();
    const n = Array.isArray(spec) && spec.length === 4 ? spec.map(Number) : r;
    return { vb: n.join(" "), x: n[0], y: n[1], l: n[2], h: n[3], k: n[2] / r[2] };
  }

  function svgChamp(c, grand) {
    if (!champ) return "";
    const k = c.k;
    let s = '<svg viewBox="' + c.vb + '" xmlns="http://www.w3.org/2000/svg" class="champ' +
      (grand ? " champ-grand" : " champ-petit") + '" style="--k:' + k.toFixed(4) +
      ";font-size:" + (5.2 * k).toFixed(2) + 'px">' +
      '<rect class="pre" x="' + c.x + '" y="' + c.y + '" width="' + c.l + '" height="' + c.h + '"/>';
    (champ.sol || []).forEach((x, i) => { s += unSol(x, i, k); });
    (champ.faits || []).forEach((x, i) => { s += unFait(x, i, k); });
    (champ.corps || []).forEach((x) => { s += unCorps(x, k, parCercle()); });
    // les noms du sol par-dessus tout : ils situent, ils ne se cachent pas
    (champ.sol || []).forEach((x) => {
      if (!x.nom || !x.etiq) return;
      s += '<text class="sol-nom" x="' + x.etiq[0] + '" y="' + x.etiq[1] + '"' +
        (x.cap ? ' transform="rotate(' + x.cap + " " + x.etiq[0] + " " + x.etiq[1] + ')"' : "") +
        ">" + esc(x.nom) + "</text>";
    });
    return s + "</svg>";
  }

  function legende() {
    const vus = [];
    (champ.corps || []).forEach((c) => {
      const n = NOM_GENRE[c.genre] || "Gens de pied";
      if (vus.indexOf(n) === -1) vus.push(n);
    });
    return '<span class="leg leg-noir">Noirs</span>' +
      '<span class="leg leg-vert">Verts</span>' +
      '<span class="leg leg-neutre">Sans parti</span>' +
      '<span class="leg-sep"></span>' +
      '<span class="leg-cercle">Un cercle : ' + parCercle() + " hommes</span>" +
      vus.map((v) => '<span class="leg-marque">' + esc(v) + "</span>").join("");
  }

  // ---- clics : on soupèse un corps, on ne le déplace pas -------------------
  function brancher(hote, apres, loupe) {
    if (!hote.dataset.branche) {
      hote.dataset.branche = "1";
      hote.addEventListener("click", (e) => {
        if (window.Loupe && Loupe.aGlisse(hote)) return;
        if (e.detail > 1) return;
        const g = e.target.closest(".corps");
        if (g) {
          if (window.Entites && g.dataset.nom) {
            Entites.penser(g.dataset.id || g.dataset.nom, "corps", g.dataset.nom);
          }
          if (apres) apres();
          return;
        }
        if (!apres && (e.target.closest("svg") || e.target.id === P + "-deployer")) ouvrir();
      });
    }
    if (window.Loupe) Loupe.brancher(hote, loupe);
  }

  function bornes() {
    const r = repere(), m = Math.max(r[2], r[3]) * .08;
    return [r[0] - m, r[1] - m, r[2] + m * 2, r[3] + m * 2];
  }
  const minZoom = () => repere()[2] / 8;

  // ---- le champ déployé (overlay) -----------------------------------------
  function batirOverlay() {
    if (document.getElementById(P + "-large")) return;
    const ov = document.createElement("div");
    ov.id = P + "-large";
    ov.hidden = true;
    ov.innerHTML =
      '<div id="' + P + '-cadre">' +
      '<div id="' + P + '-tete"><span id="' + P + '-titre"></span>' +
      '<span id="' + P + '-quand"></span>' +
      '<button id="' + P + '-fermer" title="' + o.quitter + '">' + o.quitter +
      "</button></div>" +
      '<div id="' + P + '-corps"></div>' +
      '<div id="' + P + '-legende"></div></div>';
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => { if (e.target === ov) fermer(); });
    ov.querySelector("#" + P + "-fermer").addEventListener("click", fermer);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !ov.hidden) fermer();
    });
  }
  function poserGrande(hote) { hote.innerHTML = svgChamp(cadre(vueGrande), true); }
  function ouvrir() {
    if (!champ) return;
    batirOverlay();
    const ov = document.getElementById(P + "-large");
    ov.querySelector("#" + P + "-titre").textContent = champ.nom || o.vide;
    ov.querySelector("#" + P + "-quand").textContent =
      [champ.quand, champ.echelle].filter(Boolean).join(" · ");
    ov.querySelector("#" + P + "-legende").innerHTML = legende() +
      '<span class="leg-manuel">Molette pour approcher, glisser pour déplacer, ' +
      "double-clic pour reposer " + o.sujet + "</span>";
    const c = ov.querySelector("#" + P + "-corps");
    ov.hidden = false;
    poserGrande(c);
    brancher(c, fermer, {
      vue: () => vueGrande || [].concat(repere()),
      bornes, min: minZoom(),
      poser: (vb) => { vueGrande = vb; poserGrande(c); },
      reposer: () => { vueGrande = null; poserGrande(c); },
    });
  }
  function fermer() {
    const ov = document.getElementById(P + "-large");
    if (ov) ov.hidden = true;
    vueGrande = null;
  }

  // ---- la vignette du décor ------------------------------------------------
  function poserVignette(hote) {
    const svg = svgChamp(cadre(vueVignette), false);
    const vieux = hote.querySelector("svg");
    if (vieux) vieux.outerHTML = svg;
    else hote.insertAdjacentHTML("afterbegin", svg);
  }

  function dessiner() {
    const hote = document.getElementById(P);
    if (!hote) return;
    if (!champ) { hote.innerHTML = ""; return; }
    hote.innerHTML = svgChamp(cadre(vueVignette), false) +
      '<div id="' + P + '-legende-petite">' + legende() + "</div>" +
      '<button id="' + P + '-deployer">' + o.deployer + "</button>";
    brancher(hote, null, {
      vue: () => vueVignette || [].concat(repere()),
      bornes, min: minZoom(),
      poser: (vb) => { vueVignette = vb; poserVignette(hote); },
      reposer: () => { vueVignette = null; poserVignette(hote); },
    });
  }

  // ---- l'état --------------------------------------------------------------
  const existe = () => !!champ;
  let amorce = true;         // au chargement, le décor obéit au choix du joueur

  function charger() {
    return fetch(o.route).then((r) => r.json()).then((d) => {
      const neuf = d && d.champ ? d.champ : null;
      const change = (neuf && neuf.id) !== (champ && champ.id);
      champ = neuf;
      if (change) {
        vueVignette = null; vueGrande = null;
        const h = document.getElementById(P);
        if (h && window.Loupe) Loupe.oublier(h);
        if (!champ) fermer();
      }
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
      // Un champ qui APPARAÎT en cours de partie, c'est la guerre qui prend le
      // décor : on y bascule. Au premier chargement, non — le joueur retrouve
      // l'échelle qu'il avait laissée. Un champ peut aussi refuser de s'imposer.
      if (change && !amorce && champ && champ.basculer !== false &&
          window.Plan && Plan.montrer) {
        Plan.montrer(P);
      }
      amorce = false;
    }).catch(() => {});
  }

  if (window.Plan && Plan.echelle) {
    Plan.echelle({ id: P, nom: o.nom, hote: P, ordre: o.ordre, dispo: existe });
  }

  window.addEventListener("DOMContentLoaded", () => {
    charger();
    setInterval(charger, 30000);
  });

  return { charger, dessiner, ouvrir, fermer, existe, champ: () => champ };
}

// Le champ : une bataille, un siège, une cour où deux partis se font face.
window.Terrain = ChampVu({
  id: "terrain", route: "/terrain", nom: "Le terrain", ordre: 3,
  vide: "Le champ", sujet: "le champ",
  quitter: "Quitter le champ", deployer: "Déployer le champ…",
});

// La ville : entre le château et le royaume — l'île, le bourg, le port et la
// rade, avec chaque corps posé là où il se trouve VRAIMENT. Le château dit qui
// est à trois portes de moi ; la ville dit ce qu'il y a hors les murs.
window.Ville = ChampVu({
  id: "ville", route: "/ville", nom: "La ville", ordre: 1.5,
  vide: "La ville", sujet: "la ville",
  quitter: "Quitter la ville", deployer: "Déployer la ville…",
});
