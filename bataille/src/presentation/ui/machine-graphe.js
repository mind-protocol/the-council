/**
 * 🖥️ UI / Graphe de machine — dessine la machine à états d'un brain
 * (introspection 🧠 : `machine`) : états et sous-états, état courant en
 * surbrillance, transitions (la dernière bascule en couleur), états
 * réservés grisés, badge ∗ pour les transitions « de partout ».
 * Layout déterministe minimal — les machines sont petites (≤ ~8 états).
 * Il AFFICHE la donnée de la machine, il n'interprète rien.
 */

const NS = 'http://www.w3.org/2000/svg';
const FEUILLE_L = 78;
const FEUILLE_H = 24;
const MARGE = 10;

function el(nom, attrs, parent) {
  const e = document.createElementNS(NS, nom);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  if (parent) parent.append(e);
  return e;
}

function texte(contenu, attrs, parent) {
  const t = el('text', { 'font-size': 10, fill: '#c7cdd8', 'text-anchor': 'middle', ...attrs }, parent);
  t.textContent = contenu;
  return t;
}

/** Positionne tous les états ; retourne {boites: Map<chemin, {x,y,l,h}>, l, h}. */
function disposer(machine) {
  const boites = new Map();
  let x = MARGE;
  let hMax = 0;

  for (const etat of machine.etats.filter((e) => !e.reserve)) {
    if (etat.sousEtats) {
      const cols = 2;
      const lignes = Math.ceil(etat.sousEtats.length / cols);
      const l = MARGE * 2 + cols * FEUILLE_L + (cols - 1) * 8;
      const h = 18 + MARGE + lignes * (FEUILLE_H + 8);
      boites.set(etat.nom, { x, y: MARGE, l, h, composite: true });
      etat.sousEtats.forEach((sousNom, i) => {
        boites.set(`${etat.nom}.${sousNom}`, {
          x: x + MARGE + (i % cols) * (FEUILLE_L + 8),
          y: MARGE + 18 + Math.floor(i / cols) * (FEUILLE_H + 8),
          l: FEUILLE_L,
          h: FEUILLE_H,
        });
      });
      x += l + 18;
      hMax = Math.max(hMax, h);
    } else {
      boites.set(etat.nom, { x, y: MARGE, l: FEUILLE_L, h: FEUILLE_H });
      x += FEUILLE_L + 18;
      hMax = Math.max(hMax, FEUILLE_H);
    }
  }

  let xr = MARGE;
  const yReserves = MARGE + hMax + 16;
  for (const etat of machine.etats.filter((e) => e.reserve)) {
    boites.set(etat.nom, { x: xr, y: yReserves, l: 64, h: 20, reserve: true });
    xr += 64 + 10;
  }

  const aReserves = machine.etats.some((e) => e.reserve);
  return { boites, l: Math.max(x, xr) + MARGE, h: yReserves + (aReserves ? 20 + MARGE : 0) };
}

const centre = (b) => ({ x: b.x + b.l / 2, y: b.y + b.h / 2 });

function fleche(svg, de, vers, couleur) {
  const a = centre(de);
  const b = centre(vers);
  const d = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  const ux = (b.x - a.x) / d, uy = (b.y - a.y) / d;
  const fin = { x: b.x - ux * (vers.l / 2 + 3), y: b.y - uy * (vers.h / 2 + 3) };
  el('line', { x1: a.x, y1: a.y, x2: fin.x, y2: fin.y, stroke: couleur, 'stroke-width': 1.2 }, svg);
  el('path', {
    d: `M ${fin.x} ${fin.y} L ${fin.x - 6 * ux + 3 * uy} ${fin.y - 6 * uy - 3 * ux} L ${fin.x - 6 * ux - 3 * uy} ${fin.y - 6 * uy + 3 * ux} Z`,
    fill: couleur,
  }, svg);
}

/** @param {Object} machine — introspection.machine @returns {SVGSVGElement} */
export function dessinerMachine(machine) {
  const { boites, l, h } = disposer(machine);
  const svg = el('svg', { viewBox: `0 0 ${l} ${h}`, width: '100%' });
  const derniere = machine.journal[0] ?? null;

  // transitions déclarées (hors ∗) — la dernière bascule en couleur
  for (const t of machine.transitions) {
    if (t.de === '*') continue;
    const de = boites.get(t.de);
    const vers = boites.get(t.vers);
    if (!de || !vers) continue;
    const active = derniere && derniere.libelle === t.libelle && derniere.ilYaS < 3;
    fleche(svg, de, vers, active ? '#57c9b8' : '#4a5062');
  }

  // badge ∗ sur les cibles des transitions « de partout »
  for (const t of machine.transitions.filter((t) => t.de === '*')) {
    const vers = boites.get(t.vers);
    if (!vers) continue;
    const active = derniere && derniere.libelle === t.libelle && derniere.ilYaS < 3;
    const couleur = active ? '#57c9b8' : '#4a5062';
    el('circle', { cx: vers.x - 7, cy: vers.y - 3, r: 5.5, fill: 'none', stroke: couleur }, svg);
    texte('∗', { x: vers.x - 7, y: vers.y, fill: couleur, 'font-size': 9 }, svg);
  }

  // boîtes — l'état courant en surbrillance
  for (const [chemin, b] of boites) {
    const courant = machine.etat === chemin;
    const nom = chemin.split('.').pop();
    el('rect', {
      x: b.x, y: b.y, width: b.l, height: b.h, rx: 6,
      fill: b.composite ? 'none' : courant ? '#153b36' : b.reserve ? 'none' : '#242a38',
      stroke: courant ? '#57c9b8' : b.reserve ? '#3a4052' : '#565d6d',
      'stroke-width': courant ? 2 : 1,
      ...(b.reserve ? { 'stroke-dasharray': '4 3' } : {}),
    }, svg);
    texte(nom, {
      x: b.composite ? b.x + b.l / 2 : b.x + b.l / 2,
      y: b.composite ? b.y + 13 : b.y + b.h / 2 + 3.5,
      fill: courant ? '#8fe8d8' : b.reserve ? '#5a6172' : b.composite ? '#8891a5' : '#c7cdd8',
    }, svg);
  }

  return svg;
}
