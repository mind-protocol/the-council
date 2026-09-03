/**
 * ASCII — la scène rendue en texte, pour qui ne peut pas la regarder.
 *
 * Une capture d'écran coûte cher à lire et ne dit que des pixels : il faut
 * DEVINER qui est qui. Ceci projette les corps de la simulation eux-mêmes sur
 * une grille de caractères — donc la même vérité que l'écran, mais déjà
 * nommée. C'est la règle « map is truth » appliquée à l'outillage.
 *
 * Ce n'est PAS une vue du container 🖥️ Présentation : ça ne dessine rien, ça
 * ne monte rien dans le DOM, et ça ne tourne pas dans la boucle de frame. On
 * l'appelle à la main, une fois, depuis la console :
 *
 *     ascii()                    // la grille + la légende
 *     ascii({larg: 100})         // plus fin
 *     ascii({zone: [x, y, l, h]}) // un cadrage serré
 *     asciiFaits()               // seulement les comptes, sans dessin
 *
 * Un caractère = une case, et la case porte le corps le PLUS notable qui s'y
 * trouve (un chef avant un homme, un vivant avant un mort) : à cette échelle
 * plusieurs hommes tombent dans la même case, et taire le chef pour un rang
 * serait mentir sur ce qui compte.
 */

// Les livrées du moteur sont des couleurs ; ce qui nous intéresse est le CAMP.
// Un caractère par livrée rencontrée, attribué dans l'ordre de rencontre —
// stable pour une même bataille, et la légende dit toujours lequel est lequel.
const SIGNES = ['O', 'X', '+', '=', '#', '%', '&', '@'];

function grouper(corps) {
  const livrees = [];
  for (const c of corps) if (!livrees.includes(c.livree)) livrees.push(c.livree);
  return livrees;
}

/** Le corps le plus notable l'emporte sur sa case. */
function poids(c) {
  if (c.gabarit === 'oiseau') return 2;
  if (c.panache) return 3;              // un chef porte panache
  if (c.posture === 'mort' || c.posture === 'terre') return 0;
  return 1;
}

export function rendreAscii(etat, { larg = 78, zone = null } = {}) {
  const corps = (etat && etat.corps) || [];
  if (!corps.length) return '(aucun corps — le monde est vide)';

  let x0, y0, l, h;
  if (zone) { [x0, y0, l, h] = zone; }
  else {
    const xs = corps.map((c) => c.pos.x), ys = corps.map((c) => c.pos.y);
    x0 = Math.min(...xs); y0 = Math.min(...ys);
    l = Math.max(1, Math.max(...xs) - x0); h = Math.max(1, Math.max(...ys) - y0);
  }
  // Un caractère de terminal est environ deux fois plus haut que large : sans
  // ce facteur, toute formation carrée paraît étirée en hauteur.
  const haut = Math.max(3, Math.round((larg * h) / l / 2));
  const livrees = grouper(corps);

  const cases = new Map();             // "cx,cy" → corps retenu
  const debords = { hors: 0 };
  for (const c of corps) {
    const cx = Math.floor(((c.pos.x - x0) / l) * (larg - 1));
    const cy = Math.floor(((c.pos.y - y0) / h) * (haut - 1));
    if (cx < 0 || cy < 0 || cx >= larg || cy >= haut) { debords.hors++; continue; }
    const clef = cx + ',' + cy;
    const tenant = cases.get(clef);
    if (!tenant || poids(c) > poids(tenant)) cases.set(clef, c);
  }

  const lignes = [];
  for (let y = 0; y < haut; y++) {
    let ligne = '';
    for (let x = 0; x < larg; x++) {
      const c = cases.get(x + ',' + y);
      if (!c) { ligne += ' '; continue; }
      if (c.gabarit === 'oiseau') { ligne += 'v'; continue; }
      if (poids(c) === 0) { ligne += '.'; continue; }   // à terre
      const s = SIGNES[livrees.indexOf(c.livree)] || '?';
      ligne += c.panache ? s.toLowerCase() : s;          // un chef en minuscule
    }
    lignes.push(ligne);
  }

  const legende = livrees.map((liv, i) => {
    const siens = corps.filter((c) => c.livree === liv);
    const debout = siens.filter((c) => poids(c) > 0).length;
    const chefs = siens.filter((c) => c.panache).length;
    return `  ${SIGNES[i] || '?'} ${liv} — ${debout}/${siens.length} debout` +
           (chefs ? `, ${chefs} a panache (${(SIGNES[i] || '?').toLowerCase()})` : '');
  });

  return [
    `— ${Math.round(l)} x ${Math.round(h)} m, ${larg}x${haut} caracteres ` +
    `(1 car. ~ ${(l / larg).toFixed(1)} m)`,
    ...lignes,
    '',
    ...legende,
    '  . a terre   v oiseau' + (debords.hors ? `   (${debords.hors} hors cadre)` : ''),
  ].join('\n');
}

/** Les comptes seuls — quand on veut savoir sans regarder. */
export function rendreFaits(etat) {
  const corps = (etat && etat.corps) || [];
  const par = {};
  for (const c of corps) {
    const e = (par[c.livree] ||= { total: 0, debout: 0, chefs: 0, montes: 0 });
    e.total++;
    if (poids(c) > 0) e.debout++;
    if (c.panache) e.chefs++;
    if (c.gabarit && c.gabarit !== 'homme') e.montes++;
  }
  return {
    scenario: etat && etat.scenario,
    tempsSim: etat && etat.tempsSim,
    corps: corps.length,
    camps: par,
  };
}

// ─────────────────────────────────────────────────────────────────────────
// LES YEUX D'UN HOMME
//
// Ce qui précède est OMNISCIENT : les deux camps, les effectifs justes, les
// morts, à travers les murs. C'est bon pour qui débogue, et c'est faux pour
// qui joue — donner ça à un homme, c'est lui donner la vérité brute.
//
// Ceci rend la même grille depuis SA tête : `cognition.perceptionDebug(id)`,
// c'est-à-dire ses croyances DATÉES — les gens qu'il suit, les contacts à
// portée d'armes, et les TAS (« une escouade, vers l'est ») avec leur âge.
// Ce qu'il n'a pas vu n'est pas là. Ce qu'il a vu il y a vingt secondes est
// là où il l'a laissé, pas où c'est.
//
// Le repère est LUI : il se tient au centre, le nord en haut. Un homme ne
// pense pas en coordonnées de monde.

/** Un tas vieilli s'efface : ce qu'on a vu il y a longtemps, on n'y croit plus qu'à moitié. */
function marqueAge(ageS) {
  if (ageS == null || ageS < 3) return null;   // frais : le signe plein
  if (ageS < 15) return '~';                   // vu il y a peu
  return '?';                                  // vieux : il n'en sait rien
}

export function rendreVu(perception, { larg = 60, portee = null, maLivree = null } = {}) {
  if (!perception) return '(cet homme n a pas de tete — mort, ou jamais ne)';
  // `moi` peut arriver sans `pos` selon la forme du snapshot : sans repere,
  // toute la grille est un mensonge — on le dit au lieu de centrer sur 0,0.
  const moi = perception.moi || {};
  if (!moi.pos || typeof moi.pos.x !== 'number') {
    return '(pas de repere : cet homme n a pas de position connue)';
  }
  const R = portee || perception.portee || 40;
  const haut = Math.max(3, Math.round(larg / 2));
  const grille = Array.from({ length: haut }, () => Array(larg).fill(' '));

  // Une croyance peut n'avoir PAS de position : on suit quelqu'un dont on a
  // perdu la trace, on sait qu'un tas existe sans savoir ou. C'est une tete
  // d'homme, pas un registre — l'absence de position est une information.
  const poser = (p, ch) => {
    if (!p || typeof p.x !== 'number' || typeof p.y !== 'number') return null;
    const { x, y } = p;
    // repère centré sur lui, en mètres, borné à sa portée
    const cx = Math.round(((x - moi.pos.x) / (2 * R) + 0.5) * (larg - 1));
    const cy = Math.round(((y - moi.pos.y) / (2 * R) + 0.5) * (haut - 1));
    if (cx < 0 || cy < 0 || cx >= larg || cy >= haut) return false;
    grille[cy][cx] = ch;
    return true;
  };

  const lignes = [];
  let hors = 0;

  const situe = (mis, texte) => {
    if (mis === null) lignes.push('  ' + texte + ' — sans position : il ne sait pas ou');
    else { if (mis === false) hors++; lignes.push('  ' + texte); }
  };

  for (const c of perception.contacts || []) {
    if (poser(c.pos, c.livree === maLivree ? 'o' : 'x') === false) hors++;
  }
  for (const i of perception.individus || []) {
    const m = marqueAge(i.ageS);
    situe(poser(i.pos, m || 'I'),
          `I ${i.nom || 'quelqu un'}${i.ageS != null ? ` (vu il y a ${Math.round(i.ageS)} s)` : ''}`);
  }
  for (const t of perception.tas || []) {
    const m = marqueAge(t.ageS);
    situe(poser(t.barycentre || t.pos, m || 'T'),
          `T ${t.description || t.etiquette}${t.ageS != null ? ` (il y a ${Math.round(t.ageS)} s)` : ''}`);
  }
  grille[Math.floor(haut / 2)][Math.floor(larg / 2)] = '@';

  return [
    `— ce qu il voit, ${Math.round(2 * R)} m de cote, lui au centre (@)`,
    ...grille.map((l) => l.join('').replace(/\s+$/, '')),
    '',
    ...(lignes.length ? lignes : ['  (il ne voit rien de nomme)']),
    '  @ lui   o des siens   x un etranger   ~ vu il y a peu   ? vieux' +
    (hors ? `   (${hors} hors de sa portee)` : ''),
  ].join('\n');
}
