// blasons.js — les armes des maisons, réduites à ce qui se lit de loin.
// Sur la table peinte, une bannière fait douze pixels de haut : un lion rampant
// y serait une tache. On garde donc ce qu'une bannière dit vraiment à cette
// distance — ses ÉMAUX et sa partition — et la charge y est ramenée à deux ou
// trois traits épais, qui deviennent une bête à mesure qu'on approche.
//
// La source est `blason` dans etat/maisons.json (une description héraldique en
// toutes lettres) ; ce qu'il faut pour la DESSINER relève de la mise en page, et
// vit donc ici, à la main — comme les étiquettes de lieux dans carte.js. Les
// quatre grandes maisons sans entrée dans l'état (Tully, Arryn, Lannister,
// Stark) y figurent quand même : leurs sièges sont sur la carte.
"use strict";
window.Blasons = (() => {
  // Les émaux, tenus bas en saturation : ce sont des teintures sur toile, pas
  // des écrans. Ils doivent tenir sur le parchemin sans le trouer.
  const E = {
    gueules: "#a3392f", sable: "#241d18", or: "#c9a227", argent: "#e9e3d5",
    azur: "#3c6187", sinople: "#4a7346", pourpre: "#6b4a72",
    eau: "#8fb3a8", fumee: "#9c9a92", hermine: "#efe9dc", delave: "#7f9db5",
    sang: "#7d2622", nuit: "#1b1613", neige: "#c9d2d6", cendre: "#6f6a63",
  };

  // champ : une ou plusieurs teintures selon la partition.
  // partition : "plain" | "pal3" | "ecartele" | "fusele" | "seme" | "hermine"
  // charge : le nom d'un tracé ci-dessous ; email : sa teinture.
  const ARMES = {
    "maison-targaryen-noir": { champ: [E.nuit], charge: "dragon", email: E.gueules,
      note: "Dragon tricéphale de gueules sur champ de sable" },
    "maison-targaryen-vert": { champ: [E.nuit], charge: "dragon", email: E.gueules },
    "maison-hightower": { champ: [E.fumee], charge: "tour", email: E.argent },
    "maison-velaryon": { champ: [E.eau], charge: "hippocampe", email: E.argent },
    "maison-rosby": { champ: [E.hermine], partition: "hermine", charge: "chevrons", email: E.gueules },
    "maison-stokeworth": { champ: [E.sinople], charge: "agneau", email: E.argent },
    "maison-darklyn": { champ: [E.or, E.sable], partition: "fusele" },
    "maison-staunton": { champ: [E.argent], charge: "corneilles", email: E.sable, bordure: E.gueules },
    "maison-celtigar": { champ: [E.argent], partition: "seme", charge: "crabe", email: E.gueules },
    "maison-bar-emmon": { champ: [E.delave], charge: "espadon", email: E.argent },
    "maison-massey": { champ: [E.argent], charge: "spirales", email: E.gueules },
    "maison-strong": { champ: [E.azur, E.gueules, E.sinople], partition: "pal3" },
    "maison-baratheon": { champ: [E.or], charge: "cerf", email: E.sable },
    // sièges sur la carte, maisons absentes de l'état — armes canoniques
    "maison-tully": { champ: [E.gueules, E.azur], partition: "pal2", charge: "truite", email: E.argent },
    "maison-arryn": { champ: [E.delave], charge: "faucon", email: E.argent },
    "maison-lannister": { champ: [E.sang], charge: "lion", email: E.or },
    "maison-stark": { champ: [E.neige], charge: "loup", email: E.cendre },
  };

  // Les charges, dans la boîte de la bannière : x de -4 à 4, y de -5 à 3.
  // Deux ou trois traits épais chacune — ce qui reste d'une bête à douze pixels.
  const CHARGES = {
    // trois cols qui montent d'un même corps
    dragon: '<path d="M0 2.6V-.6M0-.6-3-3.4M0-.6 0-4.2M0-.6 3-3.4" fill="none" stroke-linecap="round"/>' +
      '<circle cx="-3.2" cy="-3.7" r=".72" stroke="none"/><circle cx="0" cy="-4.6" r=".72" stroke="none"/>' +
      '<circle cx="3.2" cy="-3.7" r=".72" stroke="none"/>',
    // une tour à degrés, coiffée de sa flamme
    tour: '<path d="M-2 2.6V-2h4v4.6z" stroke="none"/><path d="M-2.8 2.6h5.6" fill="none" stroke-linecap="round"/>' +
      '<path d="M0-2.2c-1.5-1-1-2.4 0-3.4 1 1 1.5 2.4 0 3.4z" stroke="none"/>',
    // une esse : le col et la queue de l'hippocampe
    hippocampe: '<path d="M1.8-4.2c-3 .6-3.4 2.6-1.6 3.6 1.8 1 1.4 2.8-1.6 3.4" fill="none" stroke-linecap="round"/>' +
      '<circle cx="2.1" cy="-4.3" r=".7" stroke="none"/>',
    chevrons: '<path d="M-3.2-2.4 0-4.4 3.2-2.4M-3.2.2 0-1.8 3.2.2M-3.2 2.8 0 .8 3.2 2.8" fill="none"/>',
    agneau: '<ellipse cx="-.4" cy=".4" rx="2.6" ry="1.9" stroke="none"/>' +
      '<circle cx="2.4" cy="-1.1" r="1.15" stroke="none"/>',
    corneilles: '<path d="M-3.6-.6c.9-1.2 1.5-1.2 1.9 0 .4-1.2 1-1.2 1.9 0" fill="none" stroke-linecap="round"/>' +
      '<path d="M-.2 2c.9-1.2 1.5-1.2 1.9 0 .4-1.2 1-1.2 1.9 0" fill="none" stroke-linecap="round"/>',
    crabe: '<circle cx="0" cy="0" r="1.15" stroke="none"/>' +
      '<path d="M-1.1-.8-2.4-2M1.1-.8 2.4-2M-1.2.6-2.5 1.6M1.2.6 2.5 1.6" fill="none" stroke-linecap="round"/>',
    espadon: '<path d="M-3.4-.6c2-1.8 4-1.8 5.6 0-1.6 1.8-3.6 1.8-5.6 0z" stroke="none"/>' +
      '<path d="M2.2-.6 4.6-2.4" fill="none" stroke-linecap="round"/>',
    spirales: '<path d="M-2.6 1.2a1.5 1.5 0 1 1 1.2-1.5" fill="none" stroke-linecap="round"/>' +
      '<path d="M.9 1.2a1.5 1.5 0 1 1 1.2-1.5" fill="none" stroke-linecap="round"/>' +
      '<path d="M-.9-2.4a1.5 1.5 0 1 1 1.2-1.5" fill="none" stroke-linecap="round"/>',
    cerf: '<path d="M0 2.4V-1.4" fill="none" stroke-linecap="round"/>' +
      '<path d="M0-1.4-2.6-4M0-1.4 2.6-4M-1.5-2.7-3.4-2.9M1.5-2.7 3.4-2.9" fill="none" stroke-linecap="round"/>',
    truite: '<path d="M-3 -.4c2-2 4.2-2 5.8 0-1.6 2-3.8 2-5.8 0z" stroke="none"/>' +
      '<path d="M-3-.4-4.4-2.2-4.4 1.4z" stroke="none"/>',
    faucon: '<path d="M-3.4-1.2c1.4-1.8 2.6-1.8 3.4 0 .8-1.8 2-1.8 3.4 0" fill="none" stroke-linecap="round"/>' +
      '<path d="M0 .2v2.2" fill="none" stroke-linecap="round"/>',
    lion: '<path d="M-2.8 2.4c-.6-2.6.6-4.4 2.6-4.4 1.2 0 2 .7 2.4 1.7" fill="none" stroke-linecap="round"/>' +
      '<circle cx="1.4" cy="-2.9" r="1.5" stroke="none"/>' +
      '<path d="M-2.8 2.4-4 3.4" fill="none" stroke-linecap="round"/>',
    loup: '<path d="M-2.8-1.6-2.2-4l1.8 1.4h1.6L3-4l.6 2.4c0 2.2-1.4 3.6-3.2 3.6s-3.2-1.4-3.2-3.6z" stroke="none"/>',
  };

  const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  // La toile. Rectangulaire, sans queue d'aronde : l'échancrure demanderait de
  // découper le champ, donc un clipPath, donc un identifiant unique par carte —
  // et à douze pixels, personne ne verra jamais la différence.
  const L = 4.6, HAUT = -5.4, BAS = 3.4;

  // Le champ, selon la partition. Tout est découpé à la main : une bannière de
  // douze pixels ne supporte ni motif ni dégradé.
  function toile(a) {
    const c = a.champ, p = a.partition || "plain";
    const rect = (x, w, f) => '<rect x="' + x + '" y="' + HAUT + '" width="' + w +
      '" height="' + (BAS - HAUT) + '" fill="' + f + '"/>';
    if (p === "pal3") {
      return rect(-L, L * 2 / 3, c[0]) + rect(-L / 3, L * 2 / 3, c[1]) + rect(L / 3, L * 2 / 3, c[2]);
    }
    if (p === "pal2") return rect(-L, L, c[0]) + rect(0, L, c[1]);
    if (p === "ecartele") {
      const h = (BAS - HAUT) / 2;
      return '<rect x="' + -L + '" y="' + HAUT + '" width="' + L + '" height="' + h + '" fill="' + c[0] + '"/>' +
        '<rect x="0" y="' + HAUT + '" width="' + L + '" height="' + h + '" fill="' + (c[1] || c[0]) + '"/>' +
        '<rect x="' + -L + '" y="' + (HAUT + h) + '" width="' + L + '" height="' + h + '" fill="' + (c[1] || c[0]) + '"/>' +
        '<rect x="0" y="' + (HAUT + h) + '" width="' + L + '" height="' + h + '" fill="' + c[0] + '"/>';
    }
    let s = rect(-L, L * 2, c[0]);
    if (p === "fusele") {           // fuselé : quelques losanges suffisent à le dire
      const d = [];
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 2; j++) {
          const x = -L + 1.5 + i * 3, y = HAUT + 2.2 + j * 4.4;
          d.push("M" + x + " " + (y - 2.1) + "l1.5 2.1-1.5 2.1-1.5-2.1z");
        }
      }
      s += '<path d="' + d.join("") + '" fill="' + c[1] + '"/>';
    }
    if (p === "hermine") {          // hermine : trois mouchetures et l'œil comprend
      s += '<path d="M-2.4-3.2v1.4M0-.6v1.4M2.4-3.2v1.4M-1.2 2v1.4" stroke="' + E.sable +
        '" stroke-width=".8" fill="none" stroke-linecap="round" opacity=".75"/>';
    }
    return s;
  }

  function armesDe(id) { return ARMES[id] || null; }

  // Une bannière, dessinée dans sa boîte locale puis posée par un transform.
  // `taille` est le facteur d'échelle voulu par l'appelant.
  function banniere(maisonId, opts) {
    const a = armesDe(maisonId);
    if (!a) return "";
    const o = opts || {};
    const semee = a.partition === "seme" && a.charge;
    let s = '<g class="banniere">';
    // la hampe, plantée dans la place
    s += '<path class="hampe" d="M' + (-L - .9) + " " + (HAUT - 1.4) + "V" + (BAS + 3.6) + '"/>';
    s += '<g class="toile">' + toile(a) +
      '<rect class="pli" x="' + -L + '" y="' + HAUT + '" width="' + (L * 2) +
      '" height="' + (BAS - HAUT) + '"/></g>';
    if (a.bordure) {
      s += '<rect class="bordure" x="' + -L + '" y="' + HAUT + '" width="' + (L * 2) +
        '" height="' + (BAS - HAUT) + '" fill="none" stroke="' + a.bordure + '" stroke-width="1.1"/>';
    }
    if (a.charge && CHARGES[a.charge]) {
      const g = '<g class="charge" fill="' + a.email + '" stroke="' + a.email +
        '" stroke-width="1.05">' + CHARGES[a.charge] + "</g>";
      if (semee) {
        // semé : la même charge répétée petit, trois fois vaut « partout »
        s += '<g transform="translate(-2,-3) scale(.42)">' + g + "</g>" +
          '<g transform="translate(2.1,-.4) scale(.42)">' + g + "</g>" +
          '<g transform="translate(-1.6,2) scale(.42)">' + g + "</g>";
      } else s += g;
    }
    return s + "</g>";
  }

  // La teinture dominante d'une maison — pour un liseré, une pastille, un rappel.
  function teinte(maisonId) {
    const a = armesDe(maisonId);
    return a ? a.champ[0] : null;
  }

  const decrit = (maisonId) => (armesDe(maisonId) || {}).note || "";

  return { banniere, teinte, armes: armesDe, decrit, LARGEUR: L * 2, HAUT, BAS, E };
})();
