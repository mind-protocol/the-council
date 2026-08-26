/*
 * INCENDIE DE PORT-REAL — une propagation urbaine reproductible, sans canon.
 *
 * L'etat ne quitte jamais cette closure : aucun fichier d'etat, aucun fait de
 * partie. Le plan est lu, ses contours finaux deviennent les batiments du
 * calcul, puis un seuil pseudo-aleatoire stable decide QUAND une dose cumulee
 * suffit. Rejouer avec la meme graine rend donc exactement le meme incendie.
 *
 * Les valeurs et leurs raisons sont exposees dans
 * `docs/bataille/incendie-ville.md`. Deux mecanismes restent separes :
 *   1. la transmission locale, continue, par rayonnement et panache incline ;
 *   2. les brandons, discontinus, capables d'ouvrir un foyer loin du front.
 */
(() => {
  "use strict";

  const TAU = Math.PI * 2;
  const SVG_NOMBRES = /-?\d+(?:\.\d+)?/g;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const lisse = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
  const fmt = (x, n = 0) => Number(x || 0).toLocaleString("fr-FR", {
    minimumFractionDigits:n, maximumFractionDigits:n,
  });

  // Un vent d'ouest pousse VERS l'est-sud-est. Sept metres par seconde est un
  // vent soutenu, capable d'incliner un panache et de porter des brandons, sans
  // etre une tempete. Ce n'est pas le climat canonique de Port-Real : c'est la
  // condition fixe de cette epreuve comparative.
  const PARAMS = Object.freeze({
    graine: 0x129ac,
    departFeux: 12,
    ventVitesse: 7,
    ventAngleDeg: 14,                         // y du plan va vers le sud
    porteeLocale: 22,
    maille: 28,
    // La physique ne depend pas du rafraichissement : elle avance par secondes
    // entieres. C'est assez fin devant des croissances de 75 a 900 s et rend
    // le bouton +1 s semantiquement exact.
    pas: 1,
    // H20(d) = 3 exp(-d/4,2) donne, en vingt minutes pour deux maisons
    // ordinaires seches : 95 % a contact, 79 % a 3 m, 51 % a 6 m,
    // 24 % a 10 m et 2,5 % a 20 m.
    hasardContact20min: 3,
    longueurRayonnement: 4.2,
    dureeReference: 1200,
    humidite: 1,
    medianeBrandon: 35,
    dispersionBrandon: .82,
    porteeBrandonMax: 800,
  });

  const CLASSES = Object.freeze({
    leger: Object.freeze({ nom:"bois léger et chaume", susceptibilite:3,
      croissance:75, combustion:900, rayonnement:1.15, brandons:1.7,
      priseBrandon:.32, couleur:"#ffb12f" }),
    urbain: Object.freeze({ nom:"pans de bois, torchis et tuiles", susceptibilite:1,
      croissance:240, combustion:2700, rayonnement:1, brandons:.55,
      priseBrandon:.055, couleur:"#ed7138" }),
    stock: Object.freeze({ nom:"charpente à forte charge combustible", susceptibilite:2.2,
      croissance:150, combustion:3900, rayonnement:1.8, brandons:1.45,
      priseBrandon:.26, couleur:"#ff6a27" }),
    atelier: Object.freeze({ nom:"atelier mixte avec foyer maçonné", susceptibilite:.82,
      croissance:300, combustion:3000, rayonnement:1.08, brandons:.55,
      priseBrandon:.045, couleur:"#d95d39" }),
    maconnerie: Object.freeze({ nom:"maçonnerie avec planchers et charpente en bois",
      susceptibilite:.35, croissance:600, combustion:5400, rayonnement:.78,
      brandons:.22, priseBrandon:.015, couleur:"#b94d38" }),
    massif: Object.freeze({ nom:"pierre ou brique massive", susceptibilite:.08,
      croissance:900, combustion:7200, rayonnement:.62, brandons:.08,
      priseBrandon:.002, couleur:"#7b3b35" }),
    alchimie: Object.freeze({ nom:"maçonnerie et réserves de feu grégeois",
      susceptibilite:1.6, croissance:45, combustion:5400, rayonnement:4.2,
      brandons:2.8, priseBrandon:.75, couleur:"#79dc4c" }),
    inerte: Object.freeze({ nom:"inerte", susceptibilite:0, croissance:Infinity,
      combustion:0, rayonnement:0, brandons:0, priseBrandon:0, couleur:"#555" }),
  });

  const USAGES = Object.freeze({
    taudis:"leger", cabane:"leger",
    entrepot:"stock", ecurie:"stock", "chantier-bois":"stock", corderie:"stock",
    voilerie:"stock", grenier:"stock", moulin:"stock", "marche-quartier":"stock",
    forge:"atelier", boulangerie:"atelier", brasserie:"atelier", tannerie:"atelier",
    teinturerie:"atelier", etuve:"atelier", poterie:"atelier", abattoir:"atelier",
    manse:"maconnerie", "maison-officier":"maconnerie", "septuaire-quartier":"maconnerie",
    "corps-de-garde":"maconnerie", caserne:"maconnerie", geole:"maconnerie",
    "bureau-port":"maconnerie", "donjon-rouge":"massif", "fosse-dragons":"massif",
    "vieux-septuaire":"massif", "guilde-alchimistes":"alchimie",
    puits:"inerte", "fosse-vidange":"inerte",
  });

  const classeUsage = (usage) => CLASSES[USAGES[usage] || "urbain"];

  function hacher(s) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }

  function aleaStable(cle) {
    let x = (hacher(cle) ^ PARAMS.graine) >>> 0;
    x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
    return ((x >>> 0) + .5) / 4294967296;
  }

  function rng(seed) {
    let x = seed >>> 0;
    return () => {
      x += 0x6D2B79F5;
      let t = x; t = Math.imul(t ^ t >>> 15, t | 1);
      t ^= t + Math.imul(t ^ t >>> 7, t | 61);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function gauss(r) {
    const u = Math.max(1e-9, r()), v = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * v);
  }

  function contours(d) {
    // Le cuiseur n'ecrit que M/L/Z, en coordonnees absolues. Un M ouvre donc
    // un contour final du meme plan qui est visible et rasterise en collision.
    return (String(d || "").match(/M[^M]+?Z/g) || []).map((part) => {
      const ns = (part.match(SVG_NOMBRES) || []).map(Number), pts = [];
      for (let i = 0; i + 1 < ns.length; i += 2) pts.push({ x:ns[i], y:ns[i + 1] });
      return pts;
    }).filter((p) => p.length >= 3);
  }

  function geometrie(usage, points, rang) {
    let a2 = 0, cx = 0, cy = 0, x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < points.length; i++) {
      const p = points[i], q = points[(i + 1) % points.length], c = p.x * q.y - q.x * p.y;
      a2 += c; cx += (p.x + q.x) * c; cy += (p.y + q.y) * c;
      x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y);
    }
    const aire = Math.max(.5, Math.abs(a2) / 2);
    if (Math.abs(a2) > 1e-6) { cx /= 3 * a2; cy /= 3 * a2; }
    else { cx = (x0 + x1) / 2; cy = (y0 + y1) / 2; }
    const id = usage + ":" + Math.round(cx * 10) + ":" + Math.round(cy * 10) + ":" + rang;
    const mat = classeUsage(usage);
    return { id, usage, points, x:cx, y:cy, x0, y0, x1, y1, aire, mat, voisins:null,
      etat:"intact", allumeA:null, pleinA:null, eteintA:null, intensite:0,
      hasard: -Math.log(Math.max(1e-9, 1 - aleaStable(id + ":seuil"))),
      exposition: .75 + .6 * aleaStable(id + ":ouvertures"), dose:0,
      source:false, cause:null };
  }

  function dedans(p, b) {
    let oui = false;
    for (let i = 0, j = b.points.length - 1; i < b.points.length; j = i++) {
      const a = b.points[i], z = b.points[j];
      if (((a.y > p.y) !== (z.y > p.y)) &&
          p.x < (z.x - a.x) * (p.y - a.y) / ((z.y - a.y) || 1e-12) + a.x) oui = !oui;
    }
    return oui;
  }

  const distPointSegment = (p, a, b) => {
    const dx = b.x - a.x, dy = b.y - a.y;
    const t = clamp(((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy || 1), 0, 1);
    return Math.hypot(p.x - a.x - t * dx, p.y - a.y - t * dy);
  };

  function distanceContours(a, b) {
    const gx = Math.max(0, a.x0 - b.x1, b.x0 - a.x1);
    const gy = Math.max(0, a.y0 - b.y1, b.y0 - a.y1);
    let meilleur = Math.hypot(gx, gy);
    if (meilleur > PARAMS.porteeLocale) return meilleur;
    meilleur = Infinity;
    for (const p of a.points) for (let i = 0; i < b.points.length; i++)
      meilleur = Math.min(meilleur, distPointSegment(p, b.points[i], b.points[(i + 1) % b.points.length]));
    for (const p of b.points) for (let i = 0; i < a.points.length; i++)
      meilleur = Math.min(meilleur, distPointSegment(p, a.points[i], a.points[(i + 1) % a.points.length]));
    return meilleur;
  }

  let canvas = null, ctx = null, stats = null, note = null, plan = null, vue = null;
  let batiments = [], grille = new Map(), actifs = new Set(), traces = [], etat = null;
  let marche = false, vitesse = 1, boucle = 0, dernier = 0, hasard = rng(PARAMS.graine);
  let ro = null;

  const cleCellule = (i, j) => i + ":" + j;
  function cellulesBoite(b, marge = 0) {
    const q = [], m = PARAMS.maille;
    for (let i = Math.floor((b.x0 - marge) / m); i <= Math.floor((b.x1 + marge) / m); i++)
      for (let j = Math.floor((b.y0 - marge) / m); j <= Math.floor((b.y1 + marge) / m); j++) q.push(cleCellule(i, j));
    return q;
  }

  function indexer() {
    grille = new Map();
    for (const b of batiments) for (const c of cellulesBoite(b)) {
      const q = grille.get(c) || []; q.push(b); grille.set(c, q);
    }
  }

  function candidats(b, portee = PARAMS.porteeLocale) {
    const vus = new Set(), out = [];
    for (const c of cellulesBoite(b, portee)) for (const q of grille.get(c) || [])
      if (q !== b && !vus.has(q.id)) { vus.add(q.id); out.push(q); }
    return out;
  }

  function voisinsDe(b) {
    if (b.voisins) return b.voisins;
    b.voisins = candidats(b).map((q) => [q, distanceContours(b, q)])
      .filter((q) => q[1] <= PARAMS.porteeLocale);
    return b.voisins;
  }

  function allumer(b, cause, source = false) {
    if (!b || b.mat.susceptibilite <= 0 || b.etat !== "intact") return false;
    b.etat = "prise"; b.allumeA = etat.temps; b.cause = cause; b.source = source;
    b.dose = Math.max(b.dose, b.hasard); actifs.add(b);
    etat.allumes++; if (source) etat.sources++;
    return true;
  }

  function choisirDeparts() {
    // La Guilde doit etre une CONSEQUENCE observable de la propagation, pas
    // une bombe glissee arbitrairement parmi les douze allumettes initiales.
    const possibles = batiments.filter((b) => b.mat.susceptibilite >= 1 &&
      b.mat !== CLASSES.alchimie && b.aire > 8);
    if (!possibles.length) return [];
    const pris = [possibles[Math.floor(aleaStable("premier-depart") * possibles.length)]];
    while (pris.length < Math.min(PARAMS.departFeux, possibles.length)) {
      let elu = null, score = -Infinity;
      // Echantillon stable : assez large pour couvrir la ville, sans payer
      // douze fois les quarante-sept mille emprises au chargement.
      for (let k = 0; k < 2600; k++) {
        const q = possibles[Math.floor(hasard() * possibles.length)];
        if (pris.includes(q)) continue;
        const d = Math.min(...pris.map((p) => Math.hypot(q.x - p.x, q.y - p.y)));
        const s = d * (q.mat === CLASSES.leger || q.mat === CLASSES.stock ? 1.18 : 1);
        if (s > score) { score = s; elu = q; }
      }
      if (!elu) break;
      pris.push(elu);
    }
    return pris;
  }

  function remettre(options = {}) {
    marche = false; if (boucle) cancelAnimationFrame(boucle); boucle = 0;
    hasard = rng(PARAMS.graine); actifs = new Set(); traces = [];
    etat = { temps:0, sources:0, allumes:0, eteints:0, brandons:0, panachesVisibles:0,
      dragonAllumes:0, dernierAllume:0, histoire:[] };
    for (const b of batiments) Object.assign(b, { etat:"intact", allumeA:null, pleinA:null,
      eteintA:null, intensite:0, dose:0, source:false, cause:null });
    if (options.departs !== false)
      for (const b of choisirDeparts()) allumer(b, "départ imposé", true);
    rendre(); mettreStats();
  }

  const croise = (a, b, c, d) => {
    const abx = b.x - a.x, aby = b.y - a.y;
    const cdx = d.x - c.x, cdy = d.y - c.y;
    const den = abx * cdy - aby * cdx;
    if (Math.abs(den) < 1e-9) return null;
    const acx = c.x - a.x, acy = c.y - a.y;
    const t = (acx * cdy - acy * cdx) / den;
    const u = (acx * aby - acy * abx) / den;
    return t >= 0 && t <= 1 && u >= 0 && u <= 1
      ? { x:a.x + abx * t, y:a.y + aby * t } : null;
  };

  function batimentsDansBoite(x0, y0, x1, y1) {
    const vus = new Set(), out = [], m = PARAMS.maille;
    for (let i = Math.floor(x0 / m); i <= Math.floor(x1 / m); i++)
      for (let j = Math.floor(y0 / m); j <= Math.floor(y1 / m); j++)
        for (const b of grille.get(cleCellule(i, j)) || [])
          if (!vus.has(b.id)) { vus.add(b.id); out.push(b); }
    return out;
  }

  // Renvoie le point de la corde conique qui traverse le plus près de l'axe
  // du jet. Une grande emprise qui contient toute la corde est donc touchée
  // même si aucun de ses sommets ne tombe dans la flamme.
  function coupeToit(b, q) {
    if (b.x1 < Math.min(q.gauche.x, q.droite.x) ||
        b.x0 > Math.max(q.gauche.x, q.droite.x) ||
        b.y1 < Math.min(q.gauche.y, q.droite.y) ||
        b.y0 > Math.max(q.gauche.y, q.droite.y)) return null;
    const touches = [];
    if (dedans({ x:q.cx, y:q.cy }, b)) touches.push({ x:q.cx, y:q.cy });
    for (let i = 0; i < b.points.length; i++) {
      const p = croise(q.gauche, q.droite, b.points[i], b.points[(i + 1) % b.points.length]);
      if (p) touches.push(p);
    }
    if (!touches.length) return null;
    let elu = touches[0], u0 = Infinity;
    for (const p of touches) {
      const u = Math.abs((p.x - q.cx) * q.bx + (p.y - q.cy) * q.by);
      if (u < u0) { u0 = u; elu = p; }
    }
    return { point:elu, u:u0 };
  }

  /**
   * Dépose un souffle déjà intersecté avec z=0 par le moteur du dragon.
   * L'incendie ne reconstruit jamais un cône 2D : il ne lit que les cordes
   * exactes des disques 3D. La température décide de la dose ; le seuil stable
   * du bâtiment conserve une prise probabiliste, reproductible et matérielle.
   */
  function deposerSouffle(options) {
    if (!etat || !options || !options.tranches || !options.tranches.length) return 0;
    const tranches = options.tranches, dt = Math.max(0, +options.dt || 0);
    const temperature = options.temperature;
    const x0 = Math.min(...tranches.map((q) => Math.min(q.gauche.x, q.droite.x)));
    const y0 = Math.min(...tranches.map((q) => Math.min(q.gauche.y, q.droite.y)));
    const x1 = Math.max(...tranches.map((q) => Math.max(q.gauche.x, q.droite.x)));
    const y1 = Math.max(...tranches.map((q) => Math.max(q.gauche.y, q.droite.y)));
    let allumes = 0;
    for (const b of batimentsDansBoite(x0, y0, x1, y1)) {
      if (b.etat !== "intact" || b.mat.susceptibilite <= 0) continue;
      let pic = 293;
      for (const q of tranches) {
        const impact = coupeToit(b, q);
        if (!impact) continue;
        const T = typeof temperature === "function"
          ? temperature(q.s, Math.hypot(impact.u, q.v)) : 293;
        pic = Math.max(pic, T);
      }
      if (pic <= 545) continue;
      const normalise = clamp((pic - 545) / Math.max(1, (+options.noyau || 2200) - 545), 0, 1);
      // 20 s^-1 donne au noyau de Vhagar plusieurs chances d'allumer une
      // charpente durant les 0,1-0,3 s où le toit traverse réellement le jet.
      // La maçonnerie et la pierre restent respectivement ×0,35 et ×0,08.
      b.dose += normalise * normalise * dt * 20 * b.mat.susceptibilite * b.exposition;
      if (b.dose >= b.hasard && allumer(b, "souffle de " + (options.dragon || "dragon"))) {
        etat.dragonAllumes++; allumes++;
      }
    }
    return allumes;
  }

  // Cibles de vol, pas nouveaux bâtiments : on agrège les contours dans des
  // carreaux de cinquante mètres afin que le dragon choisisse des bandes de
  // tissu urbain encore combustible plutôt que 47 315 centroïdes redondants.
  function ciblesDragon(pas = 50) {
    const cellules = new Map();
    for (const b of batiments) {
      if (b.mat.susceptibilite <= 0 || b.etat === "brule") continue;
      const frais = b.etat === "intact" ? 1 : b.etat === "prise" ? .32 : .10;
      const poids = Math.min(240, b.aire) * Math.pow(b.mat.susceptibilite, .62) * frais;
      if (poids <= .01) continue;
      const cle = Math.floor(b.x / pas) + ":" + Math.floor(b.y / pas);
      const q = cellules.get(cle) || { id:"toits:" + cle, x:0, y:0, valeur:0, n:0 };
      q.x += b.x * poids; q.y += b.y * poids; q.valeur += poids; q.n++;
      cellules.set(cle, q);
    }
    return Array.from(cellules.values()).map((q) => ({ ...q,
      x:q.x / q.valeur, y:q.y / q.valeur })).sort((a, b) => b.valeur - a.valeur);
  }

  /**
   * Rend quelques foyers physiques, pas une source par maison. Ce contrat est
   * destiné à la perception des combattants : son coût dépend des panaches,
   * non du nombre total de polygones du plan.
   */
  function dangers(pas = 24) {
    const cellules = new Map();
    for (const b of batiments) {
      if (b.etat !== "prise" && b.etat !== "embrase" && b.etat !== "braises") continue;
      const base = b.etat === "embrase" ? 1 : b.etat === "prise" ? .42 : .26;
      const intensite = clamp(base + b.intensite * (b.etat === "braises" ? .34 : .58), 0, 1);
      const cle = Math.floor(b.x / pas) + ":" + Math.floor(b.y / pas);
      let q = cellules.get(cle);
      if (!q) cellules.set(cle, q = { id:"ville-feu:" + cle, x:0, y:0,
        poids:0, intensite:0, rayon:0, n:0 });
      const w = Math.max(.05, intensite) * Math.sqrt(Math.max(1, b.aire));
      q.x += b.x * w; q.y += b.y * w; q.poids += w; q.n++;
      q.intensite = Math.max(q.intensite, intensite);
      q.rayon = Math.max(q.rayon, Math.sqrt(b.aire / Math.PI));
    }
    return [...cellules.values()].map((q) => ({
      id:q.id, x:q.x/q.poids, y:q.y/q.poids,
      intensite:clamp(q.intensite + .05*Math.log2(Math.max(1,q.n)),0,1),
      rayon:Math.min(18, q.rayon + Math.sqrt(q.n-1)*1.8), n:q.n,
    }));
  }

  function resume() {
    const compte = { prise:0, embrase:0, braises:0, brule:0 };
    let aire = 0;
    for (const b of batiments) if (b.etat !== "intact") {
      compte[b.etat]++; aire += b.aire;
    }
    return { ...compte, temps:etat ? etat.temps : 0, aire,
      allumes:etat ? etat.allumes : 0, dragonAllumes:etat ? etat.dragonAllumes : 0,
      total:batiments.length, brandons:etat ? etat.brandons : 0,
      panachesVisibles:etat ? etat.panachesVisibles : 0 };
  }

  function facteurVent(source, cible) {
    const dx = cible.x - source.x, dy = cible.y - source.y, d = Math.hypot(dx, dy) || 1;
    const a = PARAMS.ventAngleDeg * Math.PI / 180;
    const aligne = (dx * Math.cos(a) + dy * Math.sin(a)) / d;
    return aligne >= 0
      ? Math.exp(.16 * PARAMS.ventVitesse * aligne)
      : Math.exp(.12 * PARAMS.ventVitesse * aligne);
  }

  function transmettre(source, cible, dt, distance) {
    if (cible.etat !== "intact" || cible.mat.susceptibilite <= 0) return;
    const d = distance == null ? distanceContours(source, cible) : distance;
    if (d > PARAMS.porteeLocale) return;
    const h20 = PARAMS.hasardContact20min * Math.exp(-d / PARAMS.longueurRayonnement);
    const taille = clamp(Math.sqrt(source.aire / 80), .55, 2.2);
    const taux = h20 / PARAMS.dureeReference * source.intensite * source.mat.rayonnement *
      cible.mat.susceptibilite * cible.exposition * facteurVent(source, cible) *
      PARAMS.humidite * taille;
    cible.dose += taux * dt;
    if (cible.dose >= cible.hasard) allumer(cible, "proximité de " + source.id);
  }

  function cibleAuPoint(x, y, rayon = 10) {
    const boite = { x0:x, y0:y, x1:x, y1:y }, qs = candidats(boite, rayon);
    let elu = null, d0 = Infinity;
    for (const b of qs) {
      if (b.etat !== "intact" || b.mat.susceptibilite <= 0) continue;
      const p = { x, y };
      let d = dedans(p, b) ? 0 : Infinity;
      for (let i = 0; i < b.points.length && d; i++)
        d = Math.min(d, distPointSegment(p, b.points[i], b.points[(i + 1) % b.points.length]));
      if (d < d0) { d0 = d; elu = b; }
    }
    return d0 <= rayon ? elu : null;
  }

  function emettreBrandon(source, dt) {
    const taux = source.mat.brandons * source.intensite / 90;
    if (hasard() >= 1 - Math.exp(-taux * dt)) return;
    let distance = PARAMS.medianeBrandon * Math.exp(PARAMS.dispersionBrandon * gauss(hasard));
    if (hasard() < .003) distance = 300 + hasard() * 500;
    distance = clamp(distance, 10, PARAMS.porteeBrandonMax);
    const angle = PARAMS.ventAngleDeg * Math.PI / 180 + gauss(hasard) * .24;
    const x = source.x + Math.cos(angle) * distance, y = source.y + Math.sin(angle) * distance;
    const cible = cibleAuPoint(x, y, 11);
    traces.push({ x0:source.x, y0:source.y, x1:x, y1:y, t:etat.temps, touche:!!cible });
    if (traces.length > 900) traces.splice(0, traces.length - 900);
    etat.brandons++;
    if (!cible) return;
    const p = clamp(cible.mat.priseBrandon * cible.exposition, 0, .92);
    cible.dose += -Math.log(Math.max(1e-9, 1 - p));
    if (cible.dose >= cible.hasard) allumer(cible, "brandon de " + source.id);
  }

  function avancerBatiment(b, dt) {
    const age = etat.temps - b.allumeA;
    if (age < b.mat.croissance) {
      b.etat = "prise"; b.intensite = .12 + .88 * lisse(age / b.mat.croissance);
    } else if (age < b.mat.croissance + b.mat.combustion * .72) {
      if (b.pleinA == null) b.pleinA = etat.temps;
      b.etat = "embrase"; b.intensite = 1;
    } else if (age < b.mat.croissance + b.mat.combustion) {
      b.etat = "braises";
      b.intensite = .55 * (1 - (age - b.mat.croissance - b.mat.combustion * .72) /
        (b.mat.combustion * .28));
    } else {
      b.etat = "brule"; b.intensite = 0; b.eteintA = etat.temps;
      actifs.delete(b); etat.eteints++;
      return;
    }
    if (b.intensite > .1) {
      for (const [q, d] of voisinsDe(b)) transmettre(b, q, dt, d);
      if (b.etat === "embrase" || b.etat === "braises") emettreBrandon(b, dt);
    }
  }

  function pas(secondes, options = {}) {
    let reste = Math.max(0, +secondes || 0);
    while (reste > 1e-8) {
      const dt = Math.min(PARAMS.pas, reste); reste -= dt; etat.temps += dt;
      for (const b of Array.from(actifs)) avancerBatiment(b, dt);
      traces = traces.filter((q) => etat.temps - q.t < 240);
    }
    if (options.peindre !== false) { rendre(); mettreStats(); }
  }

  function cadre() {
    if (!batiments.length) return plan ? [plan.bornes[0], plan.bornes[1],
      plan.bornes[2] - plan.bornes[0], plan.bornes[3] - plan.bornes[1]] : [0, 0, 100, 100];
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const b of batiments) { x0 = Math.min(x0, b.x0); y0 = Math.min(y0, b.y0);
      x1 = Math.max(x1, b.x1); y1 = Math.max(y1, b.y1); }
    return [x0 - 45, y0 - 45, x1 - x0 + 90, y1 - y0 + 90];
  }

  function redimensionner() {
    if (!canvas) return;
    const r = canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    const w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    rendre();
  }

  function visible(b, v) { return b.x1 >= v[0] && b.y1 >= v[1] && b.x0 <= v[0] + v[2] && b.y0 <= v[1] + v[3]; }
  const ecranY = (y, k, oy) => oy + (vue[1] + vue[3] - y) * k;
  function tracerPolygone(b, k, ox, oy) {
    ctx.beginPath();
    b.points.forEach((p, i) => ctx[i ? "lineTo" : "moveTo"](
      ox + (p.x - vue[0]) * k, ecranY(p.y, k, oy)));
    ctx.closePath();
  }

  // À l'échelle de la ville, la fumée est le signal naturel déjà fourni par
  // l'incendie. Les foyers proches sont regroupés à l'écran puis étirés dans
  // le sens DU vent : ce panache n'entre jamais dans la propagation physique.
  function dessinerFumee(L, H, k, ox, oy) {
    if (!actifs.size) { etat.panachesVisibles = 0; return; }
    const foyers = [];
    for (const b of actifs) {
      if (b.intensite <= .04 || !visible(b, vue)) continue;
      const x = ox + (b.x - vue[0]) * k, y = ecranY(b.y, k, oy);
      if (x < -35 || y < -35 || x > L + 35 || y > H + 35) continue;
      foyers.push({ b, x, y });
    }
    const regrouper = (pas) => {
      const groupes = new Map();
      for (const { b, x, y } of foyers) {
        const cle = Math.floor(x / pas) + ":" + Math.floor(y / pas);
        const poids = .35 + b.intensite;
        const q = groupes.get(cle) || { x:0, y:0, poids:0, n:0, embrases:0 };
        q.x += x * poids; q.y += y * poids; q.poids += poids; q.n++;
        if (b.etat === "embrase") q.embrases++;
        groupes.set(cle, q);
      }
      return groupes;
    };
    // Le coût dépend du nombre de panaches dessinés, jamais du nombre de
    // maisons en feu. Si le front s'étend, la maille visuelle grossit jusqu'à
    // respecter ce budget par image ; la physique garde tous ses bâtiments.
    const limite = k < .2 ? 180 : k < .55 ? 280 : 420;
    let pas = k < .2 ? 16 : k < .55 ? 22 : 30;
    let groupes = regrouper(pas);
    for (let i = 0; i < 4 && groupes.size > limite; i++) {
      pas *= Math.max(1.15, Math.sqrt(groupes.size / limite));
      groupes = regrouper(pas);
    }
    if (groupes.size > limite) groupes = new Map(Array.from(groupes.entries())
      .sort((a, b) => b[1].poids - a[1].poids).slice(0, limite));
    etat.panachesVisibles = groupes.size;
    if (!groupes.size) return;
    const a = PARAMS.ventAngleDeg * Math.PI / 180;
    const ux = Math.cos(a), uy = -Math.sin(a), vx = -uy, vy = ux;
    ctx.save();
    ctx.filter = "blur(2.4px)";
    for (const q of groupes.values()) {
      q.x /= q.poids; q.y /= q.poids;
      const plein = q.embrases / q.n;
      const largeur = clamp(6 + Math.sqrt(q.n) * 2.4, 8, 26);
      const longueur = clamp(42 + PARAMS.ventVitesse * 5 + Math.sqrt(q.n) * 4 + plein * 38,
                             58, 155);
      const ondulation = Math.sin(q.x * .031 + q.y * .019 + etat.temps * .045) * largeur * .7;
      const sx = q.x, sy = q.y;
      const mx = sx + ux * longueur * .48 + vx * ondulation;
      const my = sy + uy * longueur * .48 + vy * ondulation;
      const ex = sx + ux * longueur, ey = sy + uy * longueur;
      ctx.beginPath();
      ctx.moveTo(sx + vx * largeur * .45, sy + vy * largeur * .45);
      ctx.bezierCurveTo(mx + vx * largeur, my + vy * largeur,
                        ex + vx * largeur * 1.7, ey + vy * largeur * 1.7, ex, ey);
      ctx.bezierCurveTo(ex - vx * largeur * 1.7, ey - vy * largeur * 1.7,
                        mx - vx * largeur, my - vy * largeur,
                        sx - vx * largeur * .45, sy - vy * largeur * .45);
      ctx.closePath();
      const g = ctx.createLinearGradient(sx, sy, ex, ey);
      if (g && g.addColorStop) {
        g.addColorStop(0, plein > .45 ? "rgba(35,29,27,.88)" : "rgba(58,52,47,.78)");
        g.addColorStop(.45, "rgba(58,56,53,.62)");
        g.addColorStop(1, "rgba(105,105,100,0)");
        ctx.fillStyle = g;
      } else ctx.fillStyle = "rgba(77,72,66,.42)";
      ctx.fill();
      ctx.beginPath(); ctx.moveTo(sx, sy);
      ctx.quadraticCurveTo(mx, my, ex, ey);
      ctx.strokeStyle = `rgba(39,35,32,${.34 + plein * .28})`;
      ctx.lineWidth = largeur * .42; ctx.lineCap = "round"; ctx.stroke();
    }
    ctx.filter = "none";
    ctx.restore();
  }

  function rendre() {
    if (!ctx || !vue) return;
    const L = canvas.width, H = canvas.height, k = Math.min(L / vue[2], H / vue[3]);
    const ox = (L - vue[2] * k) / 2, oy = (H - vue[3] * k) / 2;
    ctx.clearRect(0, 0, L, H);
    for (const b of batiments) {
      if (b.etat === "intact" || !visible(b, vue)) continue;
      tracerPolygone(b, k, ox, oy);
      if (b.etat === "brule") ctx.fillStyle = "rgba(43,31,29,.82)";
      else if (b.etat === "braises") ctx.fillStyle = "rgba(112,43,29,.78)";
      else {
        const pulse = .72 + .18 * Math.sin(etat.temps * .21 + aleaStable(b.id + ":pulse") * TAU);
        ctx.fillStyle = b.etat === "embrase" ? `rgba(235,55,20,${pulse})` : `rgba(255,139,31,${.38 + .25 * b.intensite})`;
      }
      ctx.fill(); ctx.strokeStyle = b.etat === "brule" ? "#211917" : b.mat.couleur;
      ctx.lineWidth = clamp(k * .45, .6, 2.5); ctx.stroke();

      // Au cadre de la ville, un toit ne fait parfois qu'un pixel : le contour
      // reste exact mais le foyer deviendrait invisible. Un disque d'ecran
      // minimal signale alors le CENTRE du volume sans agrandir son emprise de
      // propagation. En s'approchant, il disparait au profit du vrai toit.
      if ((b.etat === "prise" || b.etat === "embrase") && k > .18) {
        const x = ox + (b.x - vue[0]) * k, y = ecranY(b.y, k, oy);
        const r = clamp(Math.sqrt(b.aire) * k * .32, 2, 18) * b.intensite;
        ctx.beginPath(); ctx.arc(x, y, r, 0, TAU);
        const g = ctx.createRadialGradient(x, y, 0, x, y, Math.max(1, r));
        g.addColorStop(0, "rgba(255,244,153,.9)"); g.addColorStop(.35, "rgba(255,126,30,.55)");
        g.addColorStop(1, "rgba(120,24,12,0)"); ctx.fillStyle = g; ctx.fill();
      }
    }

    dessinerFumee(L, H, k, ox, oy);

    ctx.save(); ctx.setLineDash([5, 6]); ctx.lineWidth = 1;
    for (const q of traces) {
      const age = (etat.temps - q.t) / 240;
      const x0 = ox + (q.x0 - vue[0]) * k, y0 = ecranY(q.y0, k, oy);
      const x1 = ox + (q.x1 - vue[0]) * k, y1 = ecranY(q.y1, k, oy);
      if (Math.max(x0, x1) < 0 || Math.min(x0, x1) > L || Math.max(y0, y1) < 0 || Math.min(y0, y1) > H) continue;
      ctx.beginPath(); ctx.moveTo(x0, y0);
      ctx.quadraticCurveTo((x0 + x1) / 2, Math.min(y0, y1) - Math.hypot(x1 - x0, y1 - y0) * .12, x1, y1);
      ctx.strokeStyle = q.touche ? `rgba(255,174,53,${.62 * (1 - age)})` : `rgba(155,111,66,${.3 * (1 - age)})`;
      ctx.stroke();
    }
    ctx.restore();
  }

  function inspecter(x, y) {
    if (!etat) return null;
    const c = cleCellule(Math.floor(x / PARAMS.maille), Math.floor(y / PARAMS.maille));
    const qs = (grille.get(c) || []).filter((b) => x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1 && dedans({x, y}, b));
    if (!qs.length) return null;
    const b = qs[qs.length - 1];
    const etats = { intact:"intact", prise:"prend feu", embrase:"pleinement embrasé",
      braises:"en braises", brule:"brûlé" };
    return { usage:b.usage, materiau:b.mat.nom, etat:etats[b.etat],
      risque:1 - Math.exp(-b.dose), source:b.source, cause:b.cause,
      age:b.allumeA == null ? null : etat.temps - b.allumeA };
  }

  function mettreStats() {
    if (!stats || !etat) return;
    const compte = resume(), aire = compte.aire;
    stats.innerHTML = `<h3>F1 · Incendies simultanés</h3><dl>` +
      `<dt>temps simulé</dt><dd>${fmt(etat.temps / 60, 1)} min</dd>` +
      `<dt>vent imposé</dt><dd>O → ESE · ${PARAMS.ventVitesse} m/s</dd>` +
      `<dt>départs imposés</dt><dd>${etat.sources}</dd>` +
      `<dt>prennent feu</dt><dd>${compte.prise}</dd>` +
      `<dt>pleinement embrasés</dt><dd>${compte.embrase}</dd>` +
      `<dt>en braises</dt><dd>${compte.braises}</dd>` +
      `<dt>bâtiments brûlés</dt><dd>${compte.brule}</dd>` +
      `<dt>touchés au total</dt><dd>${etat.allumes} / ${fmt(batiments.length)}</dd>` +
      `<dt>emprise touchée</dt><dd>${fmt(aire)} m²</dd>` +
      `<dt>brandons simulés</dt><dd>${fmt(etat.brandons)}</dd></dl>`;
    if (note) note.innerHTML = `<b>Hypothèse de vent</b> : ouest soutenu, canalisé vers l’est-sud-est ` +
      `par la baie — condition fixe de test, pas climat canonique. ` +
      `<span><i class="prise"></i> prise <i class="embrase"></i> embrasé ` +
      `<i class="braises"></i> braises <i class="brule"></i> brûlé</span>`;
  }

  function animer(ts) {
    if (!marche) { boucle = 0; return; }
    const dt = Math.min(.15, (ts - dernier) / 1000) * vitesse;
    dernier = ts; pas(dt);
    if (marche) boucle = requestAnimationFrame(animer); else boucle = 0;
  }

  function jouer(oui = !marche) {
    marche = !!oui;
    if (marche && !boucle) { dernier = performance.now(); boucle = requestAnimationFrame(animer); }
    else if (!marche && boucle) { cancelAnimationFrame(boucle); boucle = 0; }
    return marche;
  }

  function installer(options) {
    canvas = options.canvas; ctx = canvas.getContext("2d"); stats = options.stats;
    note = options.note; plan = options.plan;
    batiments = [];
    for (const usage of Object.keys((plan && plan.types) || {})) {
      let rang = 0;
      for (const pts of contours((plan.bati || {})[usage])) batiments.push(geometrie(usage, pts, rang++));
    }
    indexer(); remettre();
    ro = new ResizeObserver(redimensionner); ro.observe(canvas); redimensionner();
    return api;
  }

  const api = Object.freeze({
    PARAMS, CLASSES, installer, remettre, jouer, pas, cadre,
    vue(v) { vue = v && v.slice(); rendre(); },
    vitesse(x) { vitesse = clamp(+x || 1, .25, 20); },
    enMarche() { return marche; }, etat() { return etat; },
    batiments() { return batiments; }, inspecter, rendre, deposerSouffle,
    ciblesDragon, dangers, resume,
  });
  window.IncendieVille = api;
})();
