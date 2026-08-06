// jetons.js — ce que la table PORTE : les pièces qu'on pousse dessus.
// geo.js donne la géographie (elle ne bouge jamais) ; ce module donne la guerre
// (elle bouge à chaque battement). Deux familles, une seule grammaire :
//   • les JETONS  — une pièce posée quelque part : un ost, une flotte, un dragon,
//                   un siège, une bataille, un camp, des vivres.
//   • les TRAITS  — un fil tendu entre deux endroits : une marche, une route de
//                   mer, un corbeau, une attaque, un serment, un mariage, une
//                   querelle.
// Rien ici n'est la vérité : c'est ce que la reine CROIT tenir. D'où `certitude`,
// qui délave la pièce et lui colle un point d'interrogation quand la nouvelle
// vient d'une rumeur. Une table de guerre honnête montre aussi ses trous.
//
// Échelle. Tout glyphe est dessiné dans une boîte de 10 unités centrée en (0,0),
// puis posé par `transform="translate(x,y) scale(ech)"` : les épaisseurs et les
// corps de texte s'écrivent donc en unités LOCALES (pas de var(--k) ici), et la
// vignette serrée comme la grande table gardent exactement le même grain.
"use strict";
window.Jetons = (() => {
  const G = window.Geo || {};
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  // ---- les glyphes ---------------------------------------------------------
  // Quelques traits chacun, pas plus : dans la vignette, une pièce fait neuf
  // pixels de large. Ce qui ne se lit pas à cette taille ne sert à rien.
  const GLYPHES = {
    // un bloc de piques sur sa ligne de front
    armee: '<path d="M-4 3H4"/><path d="M-2.6 3V-2.4"/><path d="M0 3V-3.6"/><path d="M2.6 3V-2.4"/>',
    // deux chevrons lancés : la colonne montée
    cavalerie: '<path d="M-4.4-3L-0.4 0-4.4 3"/><path d="M0.4-3L4.4 0 0.4 3"/>',
    // une coque, un mât, une voile
    flotte: '<path d="M-4.4 0.8Q0 4.6 4.4 0.8"/><path d="M0 0.8V-4.2"/><path d="M0-3.8L2.9-0.8 0-0.8"/>',
    // deux ailes qui se rejoignent sur un corps
    dragon: '<path d="M-5-1.4C-3-2.8-1.4-1.6 0 1.4 1.4-1.6 3-2.8 5-1.4"/><path d="M0 1.4V3.2"/>',
    // un donjon crénelé
    garnison: '<path d="M-2.8 3.4V-1.8H-1.6V-3H-0.5V-1.8H0.5V-3H1.6V-1.8H2.8V3.4Z"/>',
    // le même donjon, ceint (l'anneau est ajouté au montage)
    siege: '<path d="M-2.2 3.4V-1.4H-1.2V-2.4H-0.4V-1.4H0.4V-2.4H1.2V-1.4H2.2V3.4Z"/>',
    // deux épées croisées, gardes en bas
    bataille: '<path d="M-3.6-3.6L3.6 3.6"/><path d="M3.6-3.6L-3.6 3.6"/>' +
      '<path d="M-4.4 1.6L-1.6 4.4"/><path d="M4.4 1.6L1.6 4.4"/>',
    // une tente et son mât
    camp: '<path d="M-4 3.4L0-3.4 4 3.4Z"/><path d="M0-3.4V3.4"/>',
    // un sac lié : le grain, l'argent, ce qui manque toujours
    vivres: '<path d="M-3 3.4V-0.6Q0-3.4 3-0.6V3.4Z"/><path d="M-3 0.6H3"/>',
    // un buste : quelqu'un qu'on croit là. Ce n'est pas une force, c'est un nom.
    tete: '<circle cx="0" cy="-1.6" r="1.9"/><path d="M-3.2 3.6Q0-0.4 3.2 3.6"/>',
  };
  const DEFAUT = "armee";
  const NOM_GENRE = {
    armee: "Ost", cavalerie: "Cavalerie", flotte: "Flotte", dragon: "Dragon",
    garnison: "Garnison", siege: "Siège", bataille: "Bataille", camp: "Camp",
    vivres: "Vivres", tete: "Où l'on les croit",
  };
  const NOM_TRAIT = {
    marche: "Marche", mer: "Route de mer", corbeau: "Corbeau", attaque: "Attaque",
    retraite: "Retraite", serment: "Serment", vassal: "Hommage",
    mariage: "Mariage", querelle: "Querelle", menace: "Menace",
  };

  // Un fil tendu a une allure : sa courbure, son pointillé, sa pointe. C'est là
  // que se lit la différence entre un corbeau qui vole et un ost qui marche.
  const TRAITS = {
    marche:   { fleche: "pleine",   courbure: .14, epais: 1.5 },
    mer:      { fleche: "pleine",   courbure: .22, epais: 1.3, tirets: "3.4 2.2" },
    corbeau:  { fleche: "ouverte",  courbure: .34, epais: .9,  tirets: ".9 2.4" },
    attaque:  { fleche: "barbelee", courbure: .16, epais: 2.3 },
    retraite: { fleche: "ouverte",  courbure: .16, epais: 1.3, tirets: "2.6 2.4" },
    menace:   { fleche: "ouverte",  courbure: .18, epais: 1.5, tirets: "3 2" },
    serment:  { courbure: .24, epais: 1.1, marque: "noeud" },
    vassal:   { courbure: .20, epais: .9,  tirets: "4 2" },
    mariage:  { courbure: .24, epais: .9,  tirets: "1.2 1.8", marque: "anneau" },
    querelle: { courbure: .20, epais: 1.1, motif: "zigzag" },
  };

  const camp = (m) => "camp-" + (m.camp || "neutre");
  const sur = (m) => "cert-" + (m.certitude || "sure");

  // ---- géométrie -----------------------------------------------------------
  // Une marque se pose sur un lieu (par son id) ou sur un point nu de la carte,
  // pour ce qui n'a pas d'adresse : un ost en rase campagne, une voile au large.
  function position(ou, point) {
    if (Array.isArray(point) && point.length === 2) return point;
    const p = (G.lieux || {})[ou];
    return p ? [p[0], p[1]] : null;
  }
  const posJeton = (j) => position(j.ou, j.point);
  const posDe = (t) => position(t.de, t.point_de);
  const posVers = (t) => position(t.vers, t.point_vers);

  // La boîte englobante de tout ce qui est posé — sert au cadrage automatique
  // quand un conseiller montre un bout de carte et rien d'autre.
  function boite(marques) {
    const pts = [];
    (marques.jetons || []).forEach((j) => { const p = posJeton(j); if (p) pts.push(p); });
    (marques.traits || []).forEach((t) => {
      const a = posDe(t), b = posVers(t);
      if (a) pts.push(a);
      if (b) pts.push(b);
      (t.etapes || []).forEach((e) => pts.push(e));
    });
    if (!pts.length) return null;
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    return { x: Math.min(...xs), y: Math.min(...ys),
             l: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  }

  // Bézier quadratique : deux bouts, un point de contrôle jeté de côté. La
  // courbure évite que deux fils entre les mêmes places se recouvrent, et donne
  // à la table sa main humaine — rien n'est tracé à la règle.
  const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  function courbe(a, b, k) {
    const m = lerp(a, b, .5), dx = b[0] - a[0], dy = b[1] - a[1];
    return [m[0] - dy * k, m[1] + dx * k];
  }
  const enT = (a, c, b, t) => {
    const u = 1 - t;
    return [u * u * a[0] + 2 * u * t * c[0] + t * t * b[0],
            u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]];
  };
  // Découpe (de Casteljau) : la part parcourue et la part qui reste.
  function couper(a, c, b, t) {
    const A = lerp(a, c, t), B = lerp(c, b, t), M = lerp(A, B, t);
    return [[a, A, M], [M, B, b]];
  }
  const dQ = (a, c, b) => "M" + a[0].toFixed(1) + " " + a[1].toFixed(1) +
    "Q" + c[0].toFixed(1) + " " + c[1].toFixed(1) +
    " " + b[0].toFixed(1) + " " + b[1].toFixed(1);
  const dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);

  // Une pointe de flèche se dessine à la main : un <marker> demanderait des defs
  // et des ids uniques, or deux cartes coexistent sur la page.
  function pointe(p, dir, style, ech, classe) {
    const n = Math.hypot(dir[0], dir[1]) || 1;
    const u = [dir[0] / n, dir[1] / n], w = [-u[1], u[0]];
    const L = (style === "barbelee" ? 7.5 : 6) * ech, D = 2.7 * ech;
    const q = (a, b) => [(p[0] + u[0] * a + w[0] * b).toFixed(1),
                         (p[1] + u[1] * a + w[1] * b).toFixed(1)];
    if (style === "ouverte") {
      const g = q(-L, D), d = q(-L, -D);
      return '<path class="' + classe + ' pointe-ouverte" d="M' + g[0] + " " + g[1] +
        "L" + p[0].toFixed(1) + " " + p[1].toFixed(1) + "L" + d[0] + " " + d[1] +
        '" stroke-width="' + (1.3 * ech).toFixed(2) + '"/>';
    }
    // pleine, ou barbelée : la même tête, le talon creusé pour la seconde
    const g = q(-L, D), d = q(-L, -D), t = q(style === "barbelee" ? -L * .45 : -L * .8, 0);
    return '<path class="' + classe + ' pointe-pleine" d="M' + p[0].toFixed(1) + " " +
      p[1].toFixed(1) + "L" + g[0] + " " + g[1] + "L" + t[0] + " " + t[1] +
      "L" + d[0] + " " + d[1] + 'Z"/>';
  }

  // Une querelle ne se trace pas droit : on la fait grincer.
  function zigzag(a, c, b, ech) {
    const n = 14, amp = 1.5 * ech;
    let d = "";
    for (let i = 0; i <= n; i++) {
      const t = i / n, p = enT(a, c, b, t);
      const av = enT(a, c, b, Math.min(1, t + .01)), ar = enT(a, c, b, Math.max(0, t - .01));
      const dx = av[0] - ar[0], dy = av[1] - ar[1], m = Math.hypot(dx, dy) || 1;
      const s = (i % 2 ? 1 : -1) * (i === 0 || i === n ? 0 : 1);
      d += (i ? "L" : "M") + (p[0] - dy / m * amp * s).toFixed(1) + " " +
        (p[1] + dx / m * amp * s).toFixed(1);
    }
    return d;
  }

  // ---- les traits ----------------------------------------------------------
  function unTrait(t, ech, neuves) {
    let a = posDe(t), b = posVers(t);
    if (!a || !b) return "";
    const g = TRAITS[t.genre] || TRAITS.marche;
    const k = (typeof t.courbure === "number" ? t.courbure : g.courbure) *
      (t.sens === "gauche" ? -1 : 1);
    let c = courbe(a, b, k);
    if (Array.isArray(t.etapes) && t.etapes.length) c = t.etapes[0];  // une étape impose le pli

    // On recule des deux bouts : un fil qui part du centre d'une place mange son
    // point et son nom.
    const L = dist(a, b) || 1;
    const marge = Math.min(.28, (4.5 * ech) / L);
    if (marge > 0) {
      const c1 = couper(a, c, b, marge);
      a = c1[1][0]; c = c1[1][1];
      const c2 = couper(a, c, b, 1 - marge / (1 - marge));
      a = c2[0][0]; c = c2[0][1]; b = c2[0][2];
    }

    const cl = "trait trait-" + esc(t.genre || "marche") + " " + camp(t) + " " + sur(t) +
      (neuves && neuves.has(t.id) ? " neuve" : "");
    const ep = (t.epais || g.epais || 1.4) * ech;
    const tir = g.tirets ? ' stroke-dasharray="' +
      g.tirets.split(" ").map((v) => (parseFloat(v) * ech).toFixed(2)).join(" ") + '"' : "";
    const titre = "<title>" + esc((t.nom ? t.nom + " — " : "") +
      (NOM_TRAIT[t.genre] || "")) + (t.detail ? " · " + esc(t.detail) : "") +
      (t.certitude && t.certitude !== "sure" ? " (" + esc(t.certitude) + ")" : "") + "</title>";

    let s = '<g class="' + cl + '" data-id="' + esc(t.id || "") + '" data-nom="' +
      esc(t.nom || NOM_TRAIT[t.genre] || "") + '">' + titre;

    if (g.motif === "zigzag") {
      s += '<path class="fil" d="' + zigzag(a, c, b, ech) + '" stroke-width="' + ep.toFixed(2) + '"/>';
    } else if (typeof t.avancement === "number" && g.fleche) {
      // Une colonne en route : ce qui est fait est plein, ce qui reste est en
      // pointillé, et la pièce fantôme dit où elle en est.
      const q = Math.max(.02, Math.min(.98, t.avancement));
      const [g1, g2] = couper(a, c, b, q);
      s += '<path class="fil" d="' + dQ(g1[0], g1[1], g1[2]) + '" stroke-width="' + ep.toFixed(2) + '"/>' +
        '<path class="fil fil-reste" d="' + dQ(g2[0], g2[1], g2[2]) + '" stroke-width="' +
        (ep * .8).toFixed(2) + '" stroke-dasharray="' + (2.4 * ech).toFixed(2) + " " +
        (2.2 * ech).toFixed(2) + '"/>';
    } else {
      s += '<path class="fil" d="' + dQ(a, c, b) + '" stroke-width="' + ep.toFixed(2) + '"' + tir + "/>";
    }

    if (g.fleche) s += pointe(b, [b[0] - c[0], b[1] - c[1]], g.fleche, ech, "fil-pointe");
    if (g.marque === "anneau" || g.marque === "noeud") {
      const m = enT(a, c, b, .5);
      s += '<circle class="fil-marque' + (g.marque === "noeud" ? " plein" : "") +
        '" cx="' + m[0].toFixed(1) + '" cy="' + m[1].toFixed(1) + '" r="' +
        (1.9 * ech).toFixed(2) + '" stroke-width="' + (1 * ech).toFixed(2) + '"/>';
    }
    return s + "</g>";
  }

  function traits(liste, ech, neuves) {
    return (liste || []).map((t) => unTrait(t, ech, neuves)).join("");
  }

  // ---- les jetons ----------------------------------------------------------
  const chiffre = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

  const DEC = [0, -10];              // au-dessus du point, pour ne pas le manger
  const TAILLE = 1.15;               // la pièce pèse un peu plus qu'un point de lieu
  const ETAGE = 19;                  // de quoi empiler deux pièces sans manger leurs chiffres
  // Une tête n'est pas une force : elle pèse moins, elle se range SOUS la place
  // (les osts montent, les gens descendent) et elle porte son nom en clair —
  // trois noms sur une place, c'est lisible ; un ost sans son chiffre, non.
  const TAILLE_TETE = .78, ETAGE_TETE = 12.5;

  function unJeton(j, ech, opts, d, decal) {
    const p = posJeton(j);
    if (!p) return "";
    const x = p[0] + d[0] * ech, y = p[1] + (d[1] - decal) * ech;
    const gl = GLYPHES[j.genre] || GLYPHES[DEFAUT];
    const flou = j.certitude && j.certitude !== "sure";
    const tete = j.genre === "tete";
    const cl = "jeton jeton-" + esc(j.genre || DEFAUT) + " " + camp(j) + " " + sur(j) +
      (opts.neuves && opts.neuves.has(j.id) ? " neuve" : "");

    const detail = [j.nom, tete ? "" : (NOM_GENRE[j.genre] || ""),
      j.force ? chiffre(j.force) + " " + (j.unite || "hommes") : "",
      j.detail || "", flou ? (j.certitude === "rumeur" ? "on le dit" : "rapporté") : ""]
      .filter(Boolean).join(" — ");

    let s = '<g class="' + cl + '" data-id="' + esc(j.id || "") + '" data-nom="' +
      esc(j.nom || NOM_GENRE[j.genre] || "") + '" transform="translate(' +
      x.toFixed(1) + "," + y.toFixed(1) + ") scale(" +
      (ech * (tete ? TAILLE_TETE : TAILLE)).toFixed(4) + ')">' +
      "<title>" + esc(detail) + "</title>" +
      '<circle class="jeton-fond" r="5.6"/>' +
      (j.genre === "siege" ? '<circle class="jeton-ceinture" r="6.6"/>' : "") +
      '<g class="jeton-glyphe">' + gl + "</g>";
    if (flou) s += '<text class="jeton-doute" x="6.4" y="1.8">?</text>';
    // Le chiffre est au-dessus : sous la pièce, il tomberait sur le nom du lieu.
    if (j.force) s += '<text class="jeton-force" y="-7">' + esc(chiffre(j.force)) + "</text>";
    // Le nom d'une tête est TOUTE l'information : il reste en clair. Celui
    // d'un ost vient sous le doigt — dix pièces nommées feraient une bouillie.
    if (j.nom) s += '<text class="jeton-nom' + (tete ? " toujours" : "") +
      '" y="' + (tete ? "10.6" : "9.8") + '">' + esc(j.nom) + "</text>";
    return s + "</g>";
  }

  // Deux osts sur la même place se marcheraient dessus : on les range en rang
  // d'oignon autour du point d'ancrage. Et une pièce qui tomberait hors du
  // cadrage est simplement absente — comme les noms de lieux : mieux vaut le
  // manque qu'un jeton tranché par le bord. Elle reste sur la grande table.
  function pieces(liste, ech, opts) {
    const o = opts || {};
    const c = o.cadre;
    const tas = {};
    (liste || []).forEach((j) => {
      const p = posJeton(j);
      if (!p) return;
      const d = j.dec || DEC;
      if (c) {
        const x = p[0] + d[0] * ech, y = p[1] + d[1] * ech, r = 11 * ech;
        if (x - r < c.x || x + r > c.x + c.l || y - r < c.y || y + r > c.y + c.h) return;
      }
      const k = p[0].toFixed(1) + "/" + p[1].toFixed(1) + "/" + d.join(",");
      (tas[k] = tas[k] || []).push([j, d]);
    });
    let s = "";
    // On empile vers le haut, jamais de côté : deux pièces côte à côte, ce sont
    // leurs chiffres qui se chevauchent, et un compte illisible ne vaut rien.
    Object.keys(tas).forEach((k) => {
      // Les osts s'empilent vers le haut (leurs chiffres se chevaucheraient
      // côte à côte) ; les têtes descendent sous la place, en rang serré.
      tas[k].forEach(([j, d], i) => {
        s += unJeton(j, ech, o, d, j.genre === "tete" ? -i * ETAGE_TETE : i * ETAGE);
      });
    });
    return s;
  }

  // ---- les zones : une région qui a choisi son camp ------------------------
  function zones(liste) {
    const par = {};
    (G.regions || []).forEach((r) => (par[r.id] = r.d));
    return (liste || []).map((z) => par[z.region]
      ? '<path class="zone ' + camp(z) + '" d="' + par[z.region] + '"><title>' +
        esc(z.nom || "") + "</title></path>"
      : "").join("");
  }

  // ---- la légende : seulement ce qui est effectivement posé ----------------
  function legende(marques) {
    const vus = [];
    const voir = (t, id) => { if (vus.indexOf(t + id) === -1) vus.push(t + id); };
    (marques.jetons || []).forEach((j) => voir("j:", j.genre || DEFAUT));
    (marques.traits || []).forEach((t) => voir("t:", t.genre || "marche"));
    if (!vus.length) return "";
    return vus.map((v) => {
      const [t, id] = [v.slice(0, 2), v.slice(2)];
      return '<span class="leg-marque leg-' + esc(t === "j:" ? id : "t-" + id) + '">' +
        esc((t === "j:" ? NOM_GENRE[id] : NOM_TRAIT[id]) || id) + "</span>";
    }).join("");
  }

  // Un clic sur une pièce = un moment de pensée, comme un lieu ou un nom du fil :
  // on soupèse ce qu'on croit savoir. On ne déplace rien du doigt.
  function brancher(racine, apres) {
    racine.querySelectorAll(".jeton, .trait").forEach((g) => {
      g.addEventListener("click", (e) => {
        e.stopPropagation();
        const type = g.classList.contains("jeton") ? "force" : "manoeuvre";
        if (window.Entites && g.dataset.nom) Entites.penser(g.dataset.id || g.dataset.nom, type, g.dataset.nom);
        if (apres) apres();
      });
    });
  }

  return { position, boite, traits, pieces, zones, legende, brancher,
           GLYPHES, NOM_GENRE, NOM_TRAIT };
})();
