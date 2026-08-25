(() => {
"use strict";
const $ = (id) => document.getElementById(id);

function creer(etat) {
// ═══ LE SOL PRATICABLE — ON DESSINE CE QUE LE MOTEUR VOIT ═════════════════
// On échantillonne `Bataille2d.libre()` sur la etat.vue() courante, plutôt que de
// recharger les sources du sol et d'en redécoder les bits. Deux raisons, et la seconde
// est la vraie : ça évite un second décodage à tenir d'accord avec le
// premier, et surtout ça garantit que **ce qu'on voit à l'écran est exactement
// ce que le test de collision répond**. Un banc qui dessinerait le plan SVG
// pourrait montrer un homme bien au milieu d'une rue alors que le masque le
// croit dans un mur — c'est-à-dire cacher le bug qu'on est venu chercher.
//
// L'échantillonnage est borné à `N` points sur le grand côté : au ras du sol on
// est plus fin que le pas du masque du bâti (un mètre), et de loin on
// sous-échantillonne — ce qui donne une limite grumeleuse et honnête, jamais un
// mensonge lisse.
const N = 700;
let hors = null;                                  // le canvas de composition

// LA MÊME CARTE QUE L'ONGLET « LA VILLE ». Le plan 2D apporte l'eau, les voies,
// les remparts et surtout l'usage des bâtiments par la couleur. Le sol commun reste
// l'autorité du moteur, mais sa nappe de diagnostic ne s'allume qu'à la demande :
// le dessin ordinaire ne doit pas porter une frange de pixels que « La ville »
// n'a pas. On ne duplique pas les formes : elles viennent du même
// `/monde/plan2d` que `carte-ville.js`.
const THEME = window.CarteVilleTheme;
const VILLE_VOIES = THEME.voies;
let svgVille = null, bulleVille = null, planSvg = null, modeSvg = null;
let traitsSvg = [], batiSvg = [];

const SVG_NS = "http://www.w3.org/2000/svg";
const echapper = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

function elementSvg(nom, attributs) {
  const n = document.createElementNS(SVG_NS, nom);
  for (const [cle, valeur] of Object.entries(attributs || {}))
    if (valeur != null) n.setAttribute(cle, valeur);
  return n;
}

function cheminSvg(parent, d, attributs) {
  if (!d) return null;
  const n = elementSvg("path", Object.assign({ d }, attributs));
  parent.appendChild(n);
  return n;
}

// Le fond de bataille reprend le matériau exact de « La ville » : un chemin
// SVG par usage. Outre la fidélité des couleurs, c'est ce qui rend chaque toit
// réellement interrogeable par le pointeur. Un canvas ne pouvait offrir ni
// cible DOM, ni nom d'usage sans refaire un second moteur de détection.
function cuireSvgVille() {
  const plan = etat.planVille(), mode = THEME.mode();
  if (!plan) return;
  if (svgVille && planSvg === plan && modeSvg === mode) return;
  if (svgVille) svgVille.remove();
  if (bulleVille) bulleVille.remove();
  traitsSvg = []; batiSvg = [];

  const h = $("toile"), teinte = THEME.palette(mode);
  svgVille = elementSvg("svg", {
    id:"sfond-ville", preserveAspectRatio:"xMidYMid meet",
    "aria-label":"Plan de Port-Réal",
  });
  h.insertBefore(svgVille, $("fond"));
  const [x0, y0, x1, y1] = plan.bornes;
  svgVille.appendChild(elementSvg("rect", {
    x:x0, y:y0, width:x1 - x0, height:y1 - y0, fill:teinte.sol,
  }));
  const region = plan.region || null;
  let terreClip = null;
  if (region && region.eau) {
    const terrains = elementSvg("g", { opacity:.54 }); svgVille.appendChild(terrains);
    const couleurs = {
      champ:THEME.melanger(teinte.sol, teinte.lum, 13),
      bois:THEME.melanger(teinte.sol, teinte.mur, 30),
      marais:THEME.melanger(teinte.sol, teinte.eau, 28),
    };
    for (const t of region.terrains || [])
      cheminSvg(terrains, t.d, { fill:couleurs[t.genre] || teinte.solIntra,
        stroke:THEME.melanger(teinte.sol, teinte.mur, 28), "stroke-width":2 });
    cheminSvg(terrains, region.arbres, {
      fill:THEME.melanger(teinte.sol, teinte.mur, 52), stroke:"none", opacity:.66,
    });
    cheminSvg(svgVille, region.eau, {
      fill:teinte.eau, stroke:teinte.eauTrait, "stroke-linejoin":"round",
    });
    const defs = elementSvg("defs"), clip = elementSvg("clipPath", { id:"sfond-terre" });
    const d = "M" + x0 + " " + y0 + "H" + x1 + "V" + y1 + "H" + x0 +
      "Z" + region.eau;
    clip.appendChild(elementSvg("path", { d, "fill-rule":"evenodd", "clip-rule":"evenodd" }));
    defs.appendChild(clip); svgVille.appendChild(defs); terreClip = "url(#sfond-terre)";
  }
  cheminSvg(svgVille, THEME.enceinte(plan), { fill:teinte.solIntra });
  const eau = cheminSvg(svgVille, plan.cote, {
    // Le contour cuit est une ISOLIGNE ouverte. Quand la région fournit déjà
    // un polygone d'eau fermé, le remplir ferait fermer cette ligne par une
    // diagonale à travers Port-Réal. Il ne reste alors que le trait détaillé.
    fill:region && region.eau ? "none" : teinte.eau,
    stroke:teinte.eauTrait, "stroke-linejoin":"round",
  });
  if (eau) traitsSvg.push([eau, 0, 2]);

  const niveaux = elementSvg("g"); svgVille.appendChild(niveaux);
  for (const n of plan.niveaux || []) {
    const q = cheminSvg(niveaux, n.d, { fill:"none", stroke:teinte.niveau });
    if (q) traitsSvg.push([q, 0, 1.1]);
  }

  const routesRegion = elementSvg("g", terreClip ? { "clip-path":terreClip } : {});
  svgVille.appendChild(routesRegion);
  for (const r of (region && region.routes) || []) {
    const bord = cheminSvg(routesRegion, r.d, { fill:"none",
      stroke:THEME.melanger(teinte.sol, teinte.mur, 48), opacity:.42,
      "stroke-linecap":"round", "stroke-linejoin":"round" });
    const q = cheminSvg(routesRegion, r.d, { fill:"none",
      stroke:THEME.melanger(teinte.voie, teinte.artere, 24), opacity:.72,
      "stroke-linecap":"round", "stroke-linejoin":"round" });
    if (bord) traitsSvg.push([bord, 9, 2]);
    if (q) traitsSvg.push([q, 5.4, 1.15]);
  }

  if (region && region.bourgs) {
    const bourgs = elementSvg("g", terreClip ? { "clip-path":terreClip } : {});
    svgVille.appendChild(bourgs);
    cheminSvg(bourgs, region.bourgs, {
      fill:THEME.melanger(teinte.sol, teinte.mur, 62), stroke:teinte.batiTrait,
      "stroke-width":.7, "stroke-linejoin":"round", opacity:.78,
    });
  }

  const voies = elementSvg("g"); svgVille.appendChild(voies);
  for (const usage of Object.keys(VILLE_VOIES)) {
    const [largeur, minimum, alpha] = VILLE_VOIES[usage];
    const q = cheminSvg(voies, (plan.voies || {})[usage], {
      fill:"none", stroke:usage === "quai" ? teinte.quai :
        usage === "artere" ? teinte.artere : teinte.voie,
      opacity:alpha, "stroke-linecap":"round", "stroke-linejoin":"round",
    });
    if (!q) continue;
    if (terreClip && usage !== "quai") q.setAttribute("clip-path", terreClip);
    traitsSvg.push([q, largeur, minimum]);
    if (usage === "escalier") q.dataset.escalier = "1";
  }

  if (region && region.port) {
    const port = elementSvg("g"); svgVille.appendChild(port);
    const pierreQuai = THEME.melanger(teinte.quai, teinte.mur, 68);
    for (const b of region.port.bassins || [])
      cheminSvg(port, b.d, { fill:THEME.melanger(teinte.eau, teinte.nuit, 12),
        stroke:teinte.eauTrait, "stroke-width":3 });
    for (const q of region.port.quais || []) {
      const p = cheminSvg(port, q.d, { fill:"none", stroke:pierreQuai,
        opacity:.82, "stroke-linecap":"round", "stroke-linejoin":"round" });
      if (p) traitsSvg.push([p, 11, 2.4]);
    }
    for (const q of region.port.appontements || []) {
      const p = cheminSvg(port, q.d, { fill:"none", stroke:pierreQuai,
        opacity:.82, "stroke-linecap":"square" });
      if (p) traitsSvg.push([p, 6, 1.5]);
    }
  }

  const bati = elementSvg("g"); svgVille.appendChild(bati);
  for (const usage of Object.keys(plan.types || {})) {
    if (!(plan.bati || {})[usage]) continue;
    const type = plan.types[usage] || {}, couleur = THEME.couleurUsage(plan, usage, mode);
    const q = cheminSvg(bati, plan.bati[usage], {
      fill:couleur, stroke:teinte.batiTrait, "stroke-linejoin":"round",
      "data-ville-usage":usage, "data-nom":type.nom || usage,
      tabindex:"-1", "aria-label":type.nom || usage,
    });
    batiSvg.push(q);
  }

  const rempart = elementSvg("g"); svgVille.appendChild(rempart);
  const courtine = cheminSvg(rempart, (plan.rempart || {}).courtine, {
    fill:"none", stroke:teinte.mur, "stroke-linecap":"round", "stroke-linejoin":"round",
  });
  if (courtine) traitsSvg.push([courtine, 6, 2.2]);
  const tours = cheminSvg(rempart, (plan.rempart || {}).tours, {
    fill:teinte.tour, stroke:teinte.mur,
  });
  if (tours) traitsSvg.push([tours, 0, .6]);

  bulleVille = document.createElement("div");
  bulleVille.id = "sbulle-ville"; bulleVille.setAttribute("role", "tooltip");
  h.appendChild(bulleVille);
  planSvg = plan; modeSvg = mode;
}

function cadrerSvgVille(r) {
  cuireSvgVille();
  if (!svgVille) return;
  svgVille.setAttribute("viewBox", etat.vue().join(" "));
  const mpp = etat.vue()[2] / Math.max(1, r.width);
  for (const [q, metres, pixels] of traitsSvg) {
    const largeur = Math.max(metres, pixels * mpp);
    q.setAttribute("stroke-width", largeur);
    if (q.dataset.escalier) q.setAttribute("stroke-dasharray", (3 * largeur) + " " + (2 * largeur));
  }
  for (const q of batiSvg) q.setAttribute("stroke-width", .5 * mpp);
}

function cacherBulleVille() {
  if (bulleVille) bulleVille.style.display = "none";
}

function survolerVille(e, occupe) {
  if (occupe || !svgVille) { cacherBulleVille(); return; }
  const cible = e.target && e.target.closest ? e.target.closest("[data-ville-usage]") : null;
  if (!cible || !svgVille.contains(cible)) { cacherBulleVille(); return; }
  // Un chemin SVG regroupe TOUTES les silhouettes d'un même usage. Le mettre
  // en surbrillance pour une maison sous le pointeur éclairait donc les trente
  // mille maisons à la fois. L'infobulle reste locale au pointeur ; le chemin,
  // lui, conserve sa couleur normale.
  const usage = cible.dataset.villeUsage, type = (etat.planVille().types || {})[usage] || {};
  const couleur = cible.getAttribute("fill");
  const rgb = couleur[0] === "#" ? THEME.rgb(couleur) :
    (couleur.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
  const sombre = .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2] < 135;
  const feu = etat.infoFeu ? etat.infoFeu(e) : null;
  bulleVille.innerHTML = '<strong>' + echapper(type.nom || usage) + '</strong>' +
    (type.cat ? '<span>' + echapper(type.cat) + '</span>' : '') +
    (feu ? '<span class="feu-bat"><b>' + echapper(feu.etat) +
      (feu.source ? ' · départ imposé' : '') + '</b>' + echapper(feu.materiau) +
      (feu.etat === 'intact' && feu.risque > .005
        ? ' · dose ' + Math.round(feu.risque * 100) + ' %' : '') + '</span>' : '');
  bulleVille.style.background = couleur;
  bulleVille.style.color = sombre ? "#fffaf0" : "#241b13";
  bulleVille.style.display = "block";
  const h = $("toile"), r = h.getBoundingClientRect(), b = bulleVille.getBoundingClientRect();
  let x = e.clientX - r.left + 13, y = e.clientY - r.top + 13;
  if (x + b.width > r.width - 8) x = e.clientX - r.left - b.width - 13;
  if (y + b.height > r.height - 8) y = e.clientY - r.top - b.height - 13;
  bulleVille.style.left = Math.max(8, x) + "px";
  bulleVille.style.top = Math.max(8, y) + "px";
}

function fond() {
  const c = $("fond"), h = $("toile");
  if (!c || !etat.vue() || !etat.pret()) return;
  const r = h.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  const L = Math.round(r.width * dpr), H = Math.round(r.height * dpr);
  if (c.width !== L || c.height !== H) { c.width = L; c.height = H; }
  const ctx = c.getContext("2d");
  const teinte = THEME.palette();
  ctx.clearRect(0, 0, L, H);
  cadrerSvgVille(r);

  // Le même centrage que le moteur, sinon le bâti glisse sous les hommes.
  const k = Math.min(L / etat.vue()[2], H / etat.vue()[3]);
  if ($("smasque") && $("smasque").checked) {
    const pas = Math.max(etat.vue()[2], etat.vue()[3]) / N;
    const nx = Math.max(1, Math.ceil(etat.vue()[2] / pas));
    const ny = Math.max(1, Math.ceil(etat.vue()[3] / pas));
    if (!hors) hors = document.createElement("canvas");
    if (hors.width !== nx || hors.height !== ny) { hors.width = nx; hors.height = ny; }
    const hc = hors.getContext("2d"), img = hc.createImageData(nx, ny), d = img.data;
    const mur = THEME.rgb(teinte.repere);
    for (let j = 0; j < ny; j++) {
      const y = etat.vue()[1] + (j + 0.5) * pas;
      for (let i = 0; i < nx; i++) {
        const l = Bataille2d.libre(etat.vue()[0] + (i + 0.5) * pas, y);
        if (l === null) continue;                     // masque absent : on n'invente pas
        if (l) continue;
        const o = (j * nx + i) * 4;
        d[o] = mur[0]; d[o + 1] = mur[1]; d[o + 2] = mur[2];
        d[o + 3] = 105;
      }
    }
    hc.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(hors, (L - etat.vue()[2] * k) / 2,
      (H - etat.vue()[3] * k) / 2, etat.vue()[2] * k, etat.vue()[3] * k);
  }
  dessinerToponymie(ctx, L, H, k, dpr);
}

// ═══ LE TERRAIN NOMMÉ — les mêmes données que la carte du jeu ═════════════
// Le banc continue de dessiner le MASQUE, parce que c'est lui que le moteur
// heurte. Les noms viennent seulement se poser par-dessus : ils n'embellissent
// pas la collision et ne changent aucune trajectoire, mais rendent une sonde
// dicible (« au Puits-des-Dragons », « sur la rue de Fer »).
function dessinerToponymie(ctx, L, H, k, dpr) {
  if (!etat.toponymie() || !$('stoponymes').checked || !etat.vue()) return;
  const teinte = THEME.palette();
  const ox = (L - etat.vue()[2] * k) / 2, oy = (H - etat.vue()[3] * k) / 2;
  const ecran = (x, y) => [ox + (x - etat.vue()[0]) * k, oy + (y - etat.vue()[1]) * k];
  const dedans = (p, marge = 80 * dpr) =>
    p[0] >= -marge && p[1] >= -marge && p[0] <= L + marge && p[1] <= H + marge;
  const mpp = dpr / k;                         // mètres par pixel CSS

  ctx.save();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round';
  for (const a of etat.toponymie().axes) {
    const p = ecran(a.x, a.y);
    // Au recul régional les axes urbains deviennent une pelote de noms. Les
    // routes d'approche sont déjà lisibles par leur tracé et leur destination;
    // la toponymie fine revient dès que la ville reprend la moitié du cadre.
    if (!dedans(p) || mpp > 7 || (mpp > 2.2 && (a.importance || 1) < 3)) continue;
    ctx.save(); ctx.translate(p[0], p[1]); ctx.rotate((a.angle || 0) * Math.PI / 180);
    ctx.font = ((a.importance || 1) >= 3 ? 12 : 10.5) * dpr +
      "px Georgia,serif";
    ctx.globalAlpha = (a.importance || 1) >= 3 ? 1 : .72;
    ctx.strokeStyle = teinte.sol; ctx.lineWidth = 3.5 * dpr;
    ctx.fillStyle = THEME.melanger(teinte.encre, teinte.artere, 68);
    ctx.strokeText(a.nom, 0, 0); ctx.fillText(a.nom, 0, 0); ctx.restore();
  }

  const minimum = mpp > 7 ? 4 : (mpp <= .85 ? 1 : (mpp <= 2.2 ? 2 : 3));
  ctx.textAlign = 'left';
  const region = etat.planVille().region;
  for (const r of (region && region.lieux) || []) {
    const minimumRegion = mpp > 7 ? 3 : (mpp <= 2.2 ? 2 : 3);
    if ((r.importance || 2) < minimumRegion) continue;
    const p = ecran(r.x, r.y); if (!dedans(p, 30 * dpr)) continue;
    const rayon = ((r.importance || 2) >= 3 ? 4.5 : 3.2) * dpr;
    ctx.beginPath(); ctx.arc(p[0], p[1], rayon, 0, Math.PI * 2);
    ctx.fillStyle = teinte.repere; ctx.strokeStyle = teinte.sol;
    ctx.lineWidth = 1.5 * dpr; ctx.fill(); ctx.stroke();
    ctx.font = ((r.importance || 2) >= 3 ? 12 : 10) * dpr + "px Georgia,serif";
    ctx.strokeStyle = teinte.sol; ctx.lineWidth = 3 * dpr; ctx.fillStyle = teinte.encre;
    ctx.strokeText(r.nom, p[0] + 9 * dpr, p[1]);
    ctx.fillText(r.nom, p[0] + 9 * dpr, p[1]);
  }
  for (const r of etat.toponymie().reperes) {
    if ((r.importance || 3) < minimum) continue;
    const p = ecran(r.x, r.y); if (!dedans(p, 30 * dpr)) continue;
    const rayon = ((r.importance || 3) >= 3 ? 4.5 : 3.2) * dpr;
    ctx.beginPath(); ctx.arc(p[0], p[1], rayon, 0, Math.PI * 2);
    ctx.fillStyle = teinte.repere; ctx.strokeStyle = teinte.sol;
    ctx.lineWidth = 1.5 * dpr; ctx.fill(); ctx.stroke();
    ctx.font = ((r.importance || 3) >= 3 ? 11 : 10) * dpr + "px Georgia,serif";
    ctx.strokeStyle = teinte.sol; ctx.lineWidth = 3 * dpr; ctx.fillStyle = teinte.encre;
    ctx.strokeText(r.nom, p[0] + 9 * dpr, p[1]);
    ctx.fillText(r.nom, p[0] + 9 * dpr, p[1]);
  }
  ctx.restore();
}

  return Object.freeze({ dessiner: fond, survoler: survolerVille, cacherSurvol: cacherBulleVille });
}

window.BatailleFond = Object.freeze({ creer });
})();
