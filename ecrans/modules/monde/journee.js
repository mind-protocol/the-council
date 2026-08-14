// monde/journee.js — où est chacun à cette minute-là, et par quelle rue.
//
// LA POSITION NE SE STOCKE PAS, ELLE SE CALCULE. C'est la règle que
// `scripts/presence.py` tient déjà pour le château, et elle vaut d'autant plus
// ici : quatre cent mille corps dont on ne garderait ne serait-ce qu'un vecteur
// chacun, c'est dix mégaoctets à tenir à jour soixante fois par seconde, pour
// des gens que personne ne regarde.
//
// `ou(corps, minute)` est donc une fonction PURE. Rien à faire tourner, rien à
// sauvegarder, rien à rattraper : le joueur avance de trois heures ou de trois
// jours, la ville est cohérente à l'instant d'après. Et l'on peut demander
// « qui était à ce puits à six heures » sans avoir simulé la matinée — ce sont
// les témoins d'un meurtre, l'alibi d'un homme, qui a vu partir la charrette.
//
// Trois horloges, qu'il ne faut jamais confondre :
//   l'image (60 Hz)   évaluer ~5 000 positions : des interpolations, pas d'état
//   la minute de jeu  on la LIT (monde.date.minute), on ne la simule pas
//   le jour (tick.py) les stocks, les seuils — rien à voir avec ceci
//
// Le seul calcul un peu dense est la JOURNÉE d'un corps : ses cinq ou six
// sorties. Une fois par corps et par jour, gardée tant que sa cellule est
// chargée. Le reste est de l'interpolation le long d'une polyligne.
"use strict";

// Une fois par LIEU, pas une fois par session. Ces trois caches étaient des
// singletons qui ignoraient leur `source` : passer de Port-Réal à Peyredragon
// gardait les besoins, la voirie et les chemins de Port-Réal, et le bourg se
// mettait à marcher sur des rues qui sont à cent lieues de là. Rien ne le
// signalait — les index de bâtiment existent des deux côtés.
let _lieu = null;       // la source servie par les caches ci-dessous
let _table = null;      // besoins + adresses
let _voirie = null;     // le graphe de surface, pour les chemins

function pourLieu(source) {
  if (_lieu === source) return;
  _lieu = source; _table = null; _voirie = null; _chemins.clear();
}
// Les journées se rangent DANS la cellule, dans un tableau indexé comme le
// binaire — pas dans une Map à clefs textuelles. Fabriquer « 11-3:4127:3 »
// quarante-quatre mille fois par image, c'est autant d'allocations pour un
// simple accès tableau : mesuré, c'est la moitié du coût d'une image.
const _chemins = new Map();    // "batA>batB" -> polyligne

/** La table des besoins et les adresses de chaque bâtiment. */
export async function table(source = "/monde") {
  pourLieu(source);
  if (!_table) {
    const r = await fetch(source + "/besoins");
    if (!r.ok) throw new Error("besoins : " + r.status);
    _table = await r.json();
  }
  return _table;
}

// --- le hasard qui n'en est pas un ----------------------------------------
// Un hachage, pas un tirage : deux voisins ne sortent jamais à la même minute,
// et pourtant rien n'est stocké et le résultat est le même à chaque appel.
// Sans ce déphasage, quarante ménages sortent à six heures pile et la ville
// devient un mécanisme d'horlogerie.
function melange(a, b, c) {
  let h = (a | 0) * 374761393 + (b | 0) * 668265263 + (c | 0) * 2246822519;
  h = (h ^ (h >>> 13)) * 1274126177;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;   // 0..1
}

// L'identité d'un corps, c'est sa cellule ET son rang dedans — pas son rang
// seul. Avec `k` pour toute graine, le douzième habitant de chacune des cent
// cinquante et une cellules sortait à la même minute, prenait le même côté de
// la rue et marchait à la même allure : la ville était synchronisée par
// tranches de deux cent cinquante mètres. La graine de cellule se calcule une
// fois, au premier accès, et ne coûte plus rien ensuite.
export function ident(cel, k) {
  if (cel._graine === undefined) {
    let h = 0;
    for (let i = 0; i < cel.clef.length; i++) h = (h * 31 + cel.clef.charCodeAt(i)) | 0;
    cel._graine = (h * 2654435761) | 0;
  }
  return (cel._graine + k * 2246822519) | 0;
}

/**
 * La journée d'un corps : ses sorties, en minutes, avec où il va.
 * Rend [{debut, fin, bat, service}] trié — `bat` -1 signifie « chez soi ».
 */
// --- LE QUART — tenir un poste, et le quitter par tournées ------------------
// Un homme du guet ne fait pas des courses : il PREND SON QUART. C'est la seule
// journée du jeu qui ait un état par défaut hors du logis — entre deux tours,
// il est au poste, et c'est là qu'on le trouve si l'on va frapper à la porte
// d'un corps de garde à trois heures du matin.
//
// Son quart se DÉDUIT de son identité : rien à écrire dans les corps, rien à
// tenir à jour, et le même homme reprend toujours le même. Trois quarts qui se
// relaient couvrent les vingt-quatre heures, et un tiers de l'effectif est
// dehors à tout instant — ce qui, à deux mille manteaux d'or, fait six cent
// soixante hommes dans les rues, y compris quand tout le monde dort.
//
// ON NE PATROUILLE PAS SEUL, et c'est le seul point où l'on triche un peu : le
// binôme n'existe pas comme personne. Le circuit se tire d'une graine faite du
// POSTE, du QUART et d'un numéro de tournée — deux hommes qui tombent sur le
// même numéro partent donc ensemble et suivent le même chemin, sans que ni l'un
// ni l'autre ait à savoir que l'autre existe. `patrouilles` règle la taille des
// groupes ; la remonter les éclaircit, la baisser les épaissit.
function quart(etapes, v, t, id, poste, chez, jour) {
  if (poste === undefined || poste < 0) return;
  const autour = t.dessert[poste] || [];
  const q = v.quarts[Math.floor(melange(id, 51, 0) * v.quarts.length) % v.quarts.length];
  // La graine du groupe : le poste et le quart, jamais le jour — une patrouille
  // n'est pas retirée au sort chaque matin, ce sont les mêmes qui tournent
  // ensemble. Le numéro, lui, tient à l'homme et à vie.
  const num = Math.floor(melange(id, 53, 0) * v.patrouilles);
  const graine = poste * 977 + q[0] * 13 + num;

  // Le quart de nuit déborde minuit : celui qu'on a commencé hier soir tient
  // encore ce matin. On pose donc les deux, et celui de la veille porte des
  // minutes négatives — que le reste du code compare sans y voir malice.
  for (let d = (q[0] + q[1] > 1440 ? -1440 : 0); d <= 0; d += 1440) {
    const debut = q[0] + d, fin = debut + q[1];
    let ici = debut;                       // où en est-on dans le quart
    for (let s = 0; s < v.tours; s++) {
      // Les tours se répartissent dans le quart, chacun dans sa tranche, et
      // l'heure exacte flotte : une ronde qui passe à heure fixe est une ronde
      // qu'on attend au coin de la rue.
      const tranche = q[1] / v.tours;
      const centre = debut + tranche * (s + .5);
      const ecart = (melange(graine, 300 + s, jour) * 2 - 1) * tranche * .3;
      const dep = Math.max(ici, centre + ecart - v.duree / 2);
      const ou = autour[Math.floor(melange(graine, 320 + s, jour) * autour.length)];
      if (ou === undefined || ou < 0) continue;
      const dv = v.duree_var === undefined ? .35 : v.duree_var;
      const duree = Math.max(v.duree * .3,
        v.duree * (1 + (melange(graine, 340 + s, jour) * 2 - 1) * dv));
      // AU POSTE jusqu'au départ. C'est l'étape qui manquait : sans elle, un
      // guet n'est nulle part entre deux rondes, c'est-à-dire chez lui.
      if (dep > ici + 1) {
        etapes.push({ debut: ici, fin: dep, bat: poste, service: "poste",
                      de: ici === debut ? chez : poste });
      }
      etapes.push({ debut: dep, fin: dep + duree, bat: ou, service: "ronde",
                    de: poste });
      ici = dep + duree;
    }
    if (fin > ici + 1) {
      etapes.push({ debut: ici, fin, bat: poste, service: "poste",
                    de: ici === debut ? chez : poste });
    }
  }
}

export function journee(cel, k, jour, rangs) {
  if (cel._jour !== jour) {
    cel._jour = jour;
    cel._journees = new Array(cel.n);
    // L'ENVELOPPE : la première minute où ce corps quitte son seuil, et la
    // dernière où il y revient. Deux nombres qui répondent à la seule question
    // posée à chaque image pour chaque habitant — « est-il dehors ? ». Sans
    // elle on parcourt ses sorties et l'on estime ses trajets quarante mille
    // fois par image, pour s'entendre répondre « il dort » dans neuf cas sur
    // dix. Mesuré : deux cents millisecondes par image, contre vingt.
    cel._tot = new Float32Array(cel.n).fill(NaN);
    cel._tard = new Float32Array(cel.n);
  }
  const cache = cel._journees[k];
  if (cache) return cache;

  const t = _table;
  // Tout ce dont on a besoin est dans le binaire : le domicile, le lieu de
  // travail, l'âge, et le rôle — dont le manifeste donne le rang. Aucune fiche
  // à charger, donc aucun mégaoctet de JSON pour faire marcher quelqu'un.
  const chez = cel.bat[k], travail = cel.travail[k];
  const age = cel.age_sexe[k] & 0x7f;
  const rang = rangs[cel.roles_index[cel.role[k]]];
  const adresses = t.dessert[chez] || [];
  const id = ident(cel, k);

  const etapes = [];
  // QUI PREND UN QUART NE VA PAS « AU TRAVAIL » : son travail EST son quart.
  // Sans cette ligne, l'homme du guet cumule les deux — neuf heures de labeur
  // par-dessus huit heures de veille —, et l'on voit deux mille manteaux d'or
  // partir au poste le matin comme des artisans, quart ou pas.
  const deQuart = !!(t.veilles && t.veilles[cel.roles_index[cel.role[k]]]);
  for (let n = 0; n < t.besoins.length; n++) {
    const b = t.besoins[n];
    if (deQuart && b.service === "travail") continue;
    if (b.rangs && b.rangs.indexOf(rang) < 0) continue;
    if (b.age && (age < b.age[0] || age > b.age[1])) continue;
    if (b.jours && b.jours.indexOf(jour % 7) < 0) continue;
    // `part` : tous ceux qui y ont droit ne le font pas. Le tirage vient du
    // même hachage que les heures — donc stable, et le même homme va aux
    // étuves les mêmes semaines, ce qui est exactement ce qu'on veut.
    if (b.part !== undefined && melange(id, 900 + n, jour) > b.part) continue;
    // « travail » n'est pas une adresse mais le bâtiment où ce corps-là
    // travaille : pour l'écrasante majorité c'est celui où il loge, et le
    // besoin ne produit alors aucun trajet — l'échoppe est au rez-de-chaussée.
    const ou = b.service === "travail"
      ? travail
      : adresses[t.services.indexOf(b.service)];
    if (ou === undefined || ou === null || ou < 0) continue;
    if (ou === chez) continue;
    for (let s = 0; s < b.par_jour; s++) {
      const centre = b.heures[s % b.heures.length];
      // PERSONNE N'A DE MONTRE. Une fenêtre étroite autour d'une heure ronde
      // suppose qu'on sait qu'il est six heures : on ne le sait pas. On sait
      // qu'il fait jour, que la cloche a sonné il y a un moment, que le feu est
      // pris. L'écart à l'heure « prévue » se compte donc en demi-heures, et il
      // se compose de deux choses distinctes :
      //
      //   LE PLI — le sien, le même toute sa vie. Un homme est matinal ou il
      //   traîne ; il ne tire pas son caractère au sort chaque matin. Tiré de
      //   la seule identité, sans le jour : c'est ce qui manquait, et c'est ce
      //   qui fait qu'on reconnaît les gens du coin de la rue.
      //
      //   LE JOUR — ce qui a traîné ce matin-là. Le petit qui pleure, la pluie,
      //   la queue au four. Retiré du jour ET de l'identité.
      //
      // Les deux se mêlent aux deux tiers pour le pli : deux voisins gardent
      // chacun leur heure, et aucun des deux ne la tient exactement.
      const pli = melange(id, 71, 0) * 2 - 1;              // -1..1, à vie
      const jourla = melange(id, n * 31 + s, jour) * 2 - 1; // -1..1, ce matin
      const debut = centre + (0.66 * pli + 0.34 * jourla) * b.largeur;
      // On ne reste pas tous le même temps non plus : le compte des minutes
      // qu'on passe au puits est une idée d'horloger. `duree_var` dit de
      // combien on s'en écarte — un tiers par défaut, et jamais moins d'un
      // quart de ce qui est écrit.
      const v = b.duree_var === undefined ? 0.35 : b.duree_var;
      const duree = Math.max(b.duree * 0.25,
                             b.duree * (1 + (melange(id, n * 31 + s + 7, jour) * 2 - 1) * v));
      etapes.push({ debut, fin: debut + duree, bat: ou, service: b.service });
    }
  }
  // --- la veille et la ronde ----------------------------------------------
  // Le seul métier dont le travail EST un déplacement, et le seul qui continue
  // après le couvre-feu, quand plus rien d'autre ne bouge. Le circuit se prend
  // dans les adresses du POSTE (celles du bâtiment où il sert), pas dans celles
  // de son logis : un homme du guet tourne autour de sa porte, pas de chez lui.
  const role = cel.roles_index[cel.role[k]];
  const veille = t.veilles && t.veilles[role];
  if (veille) quart(etapes, veille, t, id, travail, chez, jour);
  else {
    const ronde = t.rondes && t.rondes[role];
    if (ronde) {
      const autour = t.dessert[travail] || adresses;
      for (let s = 0; s < ronde.par_jour; s++) {
        const ou = autour[Math.floor(melange(id, 300 + s, jour) * autour.length)];
        if (ou === undefined || ou < 0 || ou === chez) continue;
        const centre = ronde.heures[s % ronde.heures.length];
        const debut = centre + (melange(id, 400 + s, jour) * 2 - 1) * ronde.largeur;
        etapes.push({ debut, fin: debut + ronde.duree, bat: ou, service: "ronde" });
      }
    }
  }

  etapes.sort((a, b) => a.debut - b.debut);
  let tot = Infinity, tard = -Infinity;
  for (const e of etapes) {
    const t = estime(chez, e.bat) / 78;      // l'allure moyenne suffit ici
    tot = Math.min(tot, e.debut - t);
    tard = Math.max(tard, e.fin + t);
  }
  cel._tot[k] = etapes.length ? tot : Infinity;
  cel._tard[k] = etapes.length ? tard : -Infinity;
  cel._journees[k] = etapes;
  return etapes;
}

// --- le chemin : sur les rues, jamais à travers les murs -------------------
// Il ne se calcule pas par personne mais UNE FOIS par couple de bâtiments, et
// il est mis en cache. Comme l'adresse est résolue au bâtiment (son puits, sa
// boulangerie), une cellule chargée n'en demande qu'une poignée.
export async function voirie(source = "/monde") {
  pourLieu(source);
  if (_voirie) return _voirie;
  const r = await fetch(source + "/voirie?couche=L1-surface");
  if (!r.ok) throw new Error("voirie : " + r.status);
  const { aretes } = await r.json();

  // La TOPOLOGIE se lit dans la GÉOMÉTRIE, et pas dans les identifiants du
  // graphe : `/voirie` est une route de dessin, elle ne transporte ni `de` ni
  // `vers`, et les lui faire porter alourdirait de moitié un envoi que le
  // rendu reçoit déjà à chaque ouverture. Deux arêtes qui partagent une
  // extrémité sont voisines — les coordonnées sont écrites au décimètre, la
  // clef est donc exacte et non approchée.
  const clef = (p) => Math.round(p[0] * 10) + ":" + Math.round(p[1] * 10);
  const noeuds = new Map();   // clef -> {xyz, liens:[{vers, arete, cout, sens}]}
  const pose = (p) => {
    const c = clef(p);
    let n = noeuds.get(c);
    if (!n) noeuds.set(c, (n = { xyz: p, liens: [] }));
    return [c, n];
  };
  for (const a of aretes) {
    const t = a.trace;
    let d = a.longueur_m;
    if (!d) { d = 0; for (let i = 1; i < t.length; i++)
      d += Math.hypot(t[i][0] - t[i-1][0], t[i][1] - t[i-1][1]); }
    // une ruelle se marche moins vite qu'une artère : ce n'est pas de la
    // couleur, c'est ce qui fait que les flux prennent les grandes rues
    const cout = d * (a.genre === "artere" ? 1 : a.genre === "rue" ? 1.15
                     : a.genre === "escalier" ? 2.2 : 1.4);
    const [ca, A] = pose(t[0]), [cb, B] = pose(t[t.length - 1]);
    if (ca === cb) continue;                 // une boucle ne mène nulle part
    A.liens.push({ vers: cb, arete: a, cout, sens: 1 });
    B.liens.push({ vers: ca, arete: a, cout, sens: -1 });
  }
  _voirie = { noeuds, aretes };
  return _voirie;
}

// Retrouver le carrefour le plus proche d'une porte en balayant les onze mille
// nœuds, c'est onze mille comparaisons par extrémité de chemin — et il y a deux
// extrémités par trajet et des milliers de trajets par cellule. Un seau de 100 m
// ramène ça à quelques dizaines.
const SEAU_M = 100;
function ensemencer(v) {
  v.seau = new Map();
  for (const [id, n] of v.noeuds) {
    const c = Math.floor(n.xyz[0] / SEAU_M) + ":" + Math.floor(n.xyz[1] / SEAU_M);
    let l = v.seau.get(c);
    if (!l) v.seau.set(c, (l = []));
    l.push(id);
  }
}

function proche(v, x, y) {
  if (!v.seau) ensemencer(v);
  const ci = Math.floor(x / SEAU_M), cj = Math.floor(y / SEAU_M);
  let meil = null, dmin = Infinity;
  for (let r = 1; r < 30 && meil === null; r++) {
    for (let di = -r; di <= r; di++) for (let dj = -r; dj <= r; dj++) {
      if (r > 1 && Math.abs(di) < r && Math.abs(dj) < r) continue;
      for (const id of v.seau.get((ci + di) + ":" + (cj + dj)) || []) {
        const p = v.noeuds.get(id).xyz;
        const d = (p[0] - x) ** 2 + (p[1] - y) ** 2;
        if (d < dmin) { dmin = d; meil = id; }
      }
    }
  }
  return meil;
}

// Le tas binaire du A*. Trente lignes qu'on écrit une fois et qu'on oublie.
class Tas {
  constructor() { this.c = []; this.v = []; }
  taille() { return this.c.length; }
  pousser(cout, val) {
    this.c.push(cout); this.v.push(val);
    let i = this.c.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this.c[p] <= this.c[i]) break;
      this.echanger(p, i); i = p;
    }
  }
  tirer() {
    const haut = this.v[0], n = this.c.length - 1;
    this.c[0] = this.c[n]; this.v[0] = this.v[n];
    this.c.pop(); this.v.pop();
    let i = 0;
    for (;;) {
      const g = 2 * i + 1, d = g + 1;
      let m = i;
      if (g < this.c.length && this.c[g] < this.c[m]) m = g;
      if (d < this.c.length && this.c[d] < this.c[m]) m = d;
      if (m === i) break;
      this.echanger(m, i); i = m;
    }
    return haut;
  }
  echanger(a, b) {
    const c = this.c[a]; this.c[a] = this.c[b]; this.c[b] = c;
    const v = this.v[a]; this.v[a] = this.v[b]; this.v[b] = v;
  }
}

/**
 * A* sur le graphe de surface. Rend {pts, long} — la polyligne ET sa longueur.
 *
 * La longueur voyage AVEC le chemin, et ce n'est pas un détail : elle est
 * demandée à chaque image pour chaque marcheur, et la recalculer là c'est
 * parcourir une polyligne de trente points soixante fois par seconde et par
 * personne. Mesuré : quatre cents millisecondes par image, contre vingt.
 */
export function chemin(v, depart, arrivee, clef) {
  const cache = _chemins.get(clef);
  if (cache) return cache;
  const a = proche(v, depart[0], depart[1]), b = proche(v, arrivee[0], arrivee[1]);
  const but = v.noeuds.get(b).xyz;
  const vus = new Map([[a, 0]]), venu = new Map();
  // Un TAS, pas un tableau retrié à chaque pas : avec `sort()` dans la boucle,
  // un A* de trois cents nœuds coûte cent fois son prix, et l'on parle de
  // milliers de chemins par cellule chargée.
  const file = new Tas();
  file.pousser(0, a);
  const h = (id) => {
    const p = v.noeuds.get(id).xyz;
    return Math.hypot(p[0] - but[0], p[1] - but[1]);
  };
  let trouve = false;
  while (file.taille()) {
    const id = file.tirer();
    if (id === b) { trouve = true; break; }
    const g = vus.get(id);
    for (const l of v.noeuds.get(id).liens) {
      const gv = g + l.cout;
      if (vus.has(l.vers) && vus.get(l.vers) <= gv) continue;
      vus.set(l.vers, gv);
      venu.set(l.vers, { de: id, lien: l });
      file.pousser(gv + h(l.vers), l.vers);
    }
  }
  const pts = [depart];
  if (trouve) {
    const suite = [];
    for (let id = b; venu.has(id); id = venu.get(id).de) {
      const { lien } = venu.get(id);
      const t = lien.arete.trace;
      suite.push(lien.sens > 0 ? t : t.slice().reverse());
    }
    suite.reverse();
    for (const t of suite) for (const p of t) pts.push(p);
  }
  pts.push(arrivee);
  // La SOMME CUMULÉE des tronçons, calculée une fois avec le chemin. Sans elle,
  // placer un marcheur à mi-parcours c'est reparcourir la polyligne depuis son
  // premier point, pour chaque marcheur et à chaque image : mesuré, cent huit
  // millisecondes par image au ras des rues, contre quinze.
  const cum = new Float64Array(pts.length);
  for (let i = 1; i < pts.length; i++)
    cum[i] = cum[i - 1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]);
  const trace = { pts, cum, long: cum[cum.length - 1] };
  _chemins.set(clef, trace);
  return trace;
}

// --- le splatter de rue ----------------------------------------------------
// Rien à voir avec le semis des domiciles, qui dit où l'on LOGE et ne bouge
// jamais. Ici on marche : on tient sa droite, à moins de la moitié de la
// largeur de la voie moins une épaule — sinon les gens traversent les murs, et
// une ruelle de deux mètres doit se voir trop étroite pour deux hommes de front.
const EPAULE = 0.4;

function surLaVoie(tr, avance, cote, largeur, p) {
  const pts = tr.pts, cum = tr.cum;
  // Un chemin d'un seul point : la porte et la destination sont confondues.
  // Ça arrive, et sans ce garde-fou la dichotomie va chercher un tronçon qui
  // n'existe pas.
  if (pts.length < 2) {
    p.x = pts[0][0]; p.y = pts[0][1]; p.z = pts[0][2] || 0;
    p.dx = 0; p.dy = 0;
    return p;
  }
  // Dichotomie sur la somme cumulée : trouver le tronçon coûte le logarithme
  // du nombre de points, pas leur nombre.
  let lo = 1, hi = pts.length - 1;
  while (lo < hi) {
    const mi = (lo + hi) >> 1;
    if (cum[mi] < avance) lo = mi + 1; else hi = mi;
  }
  {
    const i = lo;
    const a = pts[i - 1], b = pts[i];
    const d = cum[i] - cum[i - 1];
    const reste = avance - cum[i - 1];
    const t = d ? Math.max(0, Math.min(1, reste / d)) : 0;
    const nx = d ? -(b[1] - a[1]) / d : 0, ny = d ? (b[0] - a[0]) / d : 0;
    const e = Math.max(0, largeur / 2 - EPAULE) * cote;
    p.x = a[0] + (b[0] - a[0]) * t + nx * e;
    p.y = a[1] + (b[1] - a[1]) * t + ny * e;
    // LE SENS DU TRONÇON, tant qu'on le tient. Il ne coûte rien ici — la
    // division est déjà faite pour la normale — et il permet à l'appelant de
    // dire à quelle vitesse ce corps s'en va, donc de le faire GLISSER entre
    // deux calculs au lieu de le téléporter. Sans ça, une foule qu'on ne
    // recalcule que quatre fois par seconde avance par bonds d'un mètre.
    p.dx = d ? (b[0] - a[0]) / d : 0;
    p.dy = d ? (b[1] - a[1]) / d : 0;
    // le z vient du TRACÉ, qui porte la pente — jamais de l'étage du domicile,
    // sans quoi le marcheur flotte au-dessus de la chaussée
    p.z = (a[2] || 0) + ((b[2] || 0) - (a[2] || 0)) * t;
    return p;
  }
}

/**
 * Où est ce corps à cette minute — la fonction pure, le cœur du module.
 * Rend {x, y, z, quoi} : "chez" (à son adresse), "route" (en chemin),
 * "sur-place" (arrivé, il attend ou fait la queue).
 */
export function ou(cel, k, jour, minute, v, rangs, out) {
  const p = out || {};
  // Le chemin le plus court est celui qu'on ne prend pas : si la journée de ce
  // corps est déjà connue et que l'heure tombe hors de son enveloppe, il est
  // chez lui et l'on n'a rien d'autre à calculer.
  if (cel._jour === jour && !Number.isNaN(cel._tot[k])
      && (minute < cel._tot[k] || minute > cel._tard[k]))
    return chezSoi(cel, k, p);
  const etapes = journee(cel, k, jour, rangs);
  // mètres par minute — un pas de ville. Un vieux, un enfant et un portefaix
  // chargé ne marchent pas à la même allure : le déphasage vient de l'identité,
  // comme les heures, et ne coûte donc rien.
  const id = ident(cel, k);
  const marche = 66 + melange(id, 3, 0) * 24;

  for (const e of etapes) {
    // D'OÙ L'ON PART N'EST PAS TOUJOURS DE CHEZ SOI. Une course commence au
    // seuil et y revient — mais un homme de quart part de son POSTE et y
    // retourne : sa tournée n'est pas un aller-retour depuis son lit. `de` le
    // dit ; sans lui, un guet du Culpucier traverserait la ville deux fois par
    // ronde, et l'on verrait deux mille hommes rentrer chez eux toutes les
    // trois heures.
    const chez = e.de === undefined ? cel.bat[k] : e.de;
    // L'HORAIRE se décide sur une estimation, la GÉOMÉTRIE sur le vrai chemin.
    // C'est ce qui évite de calculer un A* pour quelqu'un qui dort : à quatre
    // heures du matin, personne n'est en route, et personne ne doit coûter un
    // chemin. Le détour d'une rue vaut un tiers de plus que le vol d'oiseau —
    // c'est une estimation, pas une mesure, et elle n'a qu'à être stable.
    const trajet = estime(chez, e.bat) / marche;
    if (minute < e.debut - trajet) continue;          // pas encore parti
    if (minute >= e.fin + trajet) continue;           // déjà rentré
    const tr = cheminBat(v, chez, e.bat);
    const cote = melange(id, 7, jour) < 0.5 ? -1 : 1;
    const larg = 3;
    // ON MARCHE À SON PAS, ON NE COURT PAS POUR TENIR L'HORAIRE.
    //
    // La position se réglait sur la fraction du trajet écoulée — `part` allait
    // de zéro à un pendant la durée ESTIMÉE, et la géométrie, elle, suit le
    // vrai chemin. Quand la rue fait le tour d'un pâté que le vol d'oiseau
    // ignore, le vrai chemin est trois fois l'estimation et l'homme doit donc
    // le parcourir trois fois plus vite : mesuré, des habitants à QUATRE CENTS
    // MÈTRES PAR MINUTE, six fois le pas d'un homme. À l'écran ce sont eux
    // qu'on voit sauter, quelle que soit la cadence de calcul.
    //
    // Chacun avance donc de son `marche` à lui, et l'avance se BORNE au bout
    // du chemin : celui dont la rue est plus longue que prévu arrive à la
    // porte en avance ou en retard et il y attend, ce que fait n'importe qui.
    // L'horaire garde son estimation — il faut qu'il reste sans A*, c'est tout
    // son propos — et seule la géométrie cesse de mentir.
    if (minute < e.debut) {                           // il y va
      const avance = Math.min(tr.long, (minute - (e.debut - trajet)) * marche);
      surLaVoie(tr, avance, cote, larg, p);
      const v2 = avance >= tr.long ? 0 : marche;      // arrivé : il attend
      p.vx = p.dx * v2; p.vy = p.dy * v2;
      p.quoi = "route"; p.vers = e.service; p.bat = e.bat; return p;
    }
    if (minute < e.fin) {                             // il y est
      const q = tr.pts[tr.pts.length - 1];
      // ON NE POSE PLUS LES GENS, ON LES LAISSE ALLER ET VENIR. Le tirage était
      // fait UNE FOIS pour toute la durée de l'étape : chacun recevait son
      // angle et son rayon, et n'en bougeait plus d'un pouce jusqu'à l'heure du
      // retour. À douze au puits cela passait ; au grand marché, trois mille
      // points figés dans un disque font une TACHE RONDE, parfaitement
      // circulaire, posée sur le plan comme une pièce de monnaie — et l'œil ne
      // voit plus une foule, il voit un rond. Le défaut n'était pas le rayon,
      // c'était l'immobilité : une place se reconnaît à ce qu'elle remue.
      //
      // Donc la position se calcule à la minute, comme le reste. Chacun a une
      // suite de STATIONS — l'étal, la margelle, le coin où l'on cause — et
      // glisse de l'une à l'autre. Rien n'est stocké : la station n° n se tire
      // du hachage, exactement comme l'angle se tirait avant, et `ou` reste
      // pure. Deux tirages au lieu d'un, et une interpolation : c'est tout ce
      // que la flânerie coûte.
      //
      // L'ÉTENDUE reste celle de la table (`etendues`, dans besoins.py) : elle
      // seule sait qu'un marché est une PLACE et un puits une margelle. Et la
      // racine répartit toujours SUR la surface — un tirage linéaire du rayon
      // tasse tout au centre, c'est le défaut classique et il se voyait ici en
      // grand.
      const etendue = (_table.etendues && _table.etendues[e.service]) || 6.5;
      // Le pas de flânerie suit l'étendue, et pas l'inverse : on veut une
      // ALLURE de badaud, jamais une course. Deux minutes pour traverser une
      // margelle, six pour traverser une place — soit une dizaine de mètres à
      // la minute, le tiers d'un homme qui marche.
      const pas = 1.5 + etendue / 14;
      const s = (minute - e.debut) / pas, n = Math.floor(s), f = s - n;
      // Adouci aux deux bouts : on ralentit en arrivant à l'étal et l'on
      // repart sans à-coup. Une interpolation droite donnerait un défilé de
      // points à vitesse constante, ce qui est l'autre façon de ne pas faire
      // une foule.
      const u = f * f * (3 - 2 * f);
      const ax = melange(id, 13 + n * 2, jour) * 6.283,
            ar = Math.sqrt(melange(id, 11 + n * 2, jour)) * etendue,
            bx = melange(id, 15 + n * 2, jour) * 6.283,
            br = Math.sqrt(melange(id, 13 + n * 2, jour)) * etendue;
      const x0 = Math.cos(ax) * ar, y0 = Math.sin(ax) * ar,
            x1 = Math.cos(bx) * br, y1 = Math.sin(bx) * br;
      p.x = q[0] + x0 + (x1 - x0) * u;
      p.y = q[1] + y0 + (y1 - y0) * u;
      // La dérivée de l'adouci : `u = f²(3-2f)` donc `du/df = 6f(1-f)`, et `f`
      // avance d'un `pas` par minute. Le badaud ralentit donc en arrivant à son
      // étal et repart doucement, exactement comme il est dessiné.
      const dv = 6 * f * (1 - f) / pas;
      p.vx = (x1 - x0) * dv; p.vy = (y1 - y0) * dv;
      p.z = q[2] || 0; p.quoi = "sur-place"; p.vers = e.service; p.bat = e.bat; return p;
    }
    // il en revient : le même chemin, à l'envers
    // Le retour au même pas, et borné de la même façon : arrivé chez lui, il
    // reste à sa porte jusqu'à ce que sa journée le rende à son logis.
    const reste = Math.max(0, tr.long - (minute - e.fin) * marche);
    surLaVoie(tr, reste, -cote, larg, p);
    // Il REMONTE la polyligne : l'avance décroît avec la minute, donc la
    // vitesse est celle du tronçon au signe près.
    const v2 = reste <= 0 ? 0 : marche;
    p.vx = -p.dx * v2; p.vy = -p.dy * v2;
    // Celui qui rentre au POSTE ne rentre pas chez lui : la nuance vaut une
    // couleur sur le plan, et surtout elle vaut la vérité — on le trouvera au
    // corps de garde, pas à son lit.
    p.quoi = "route"; p.vers = e.de === undefined ? "chez" : "poste";
    p.bat = chez; return p;
  }
  return chezSoi(cel, k, p);
}

// Chez soi : c'est la réponse la plus fréquente de la journée, et c'est bien
// ainsi. La position de domicile, celle que la cellule porte déjà.
function chezSoi(cel, k, p) {
  p.x = cel.x0 + cel.x[k] / 100; p.y = cel.y0 + cel.y[k] / 100;
  p.z = cel.z[k] / 100; p.quoi = "chez"; p.vers = null; p.bat = cel.bat[k];
  p.vx = 0; p.vy = 0;                  // il dort : rien à faire glisser
  return p;
}

// Le vol d'oiseau majoré : ce que coûte un trajet sans avoir à le tracer.
const DETOUR = 1.35;
function estime(a, b) {
  const p = _table.portes[a], q = _table.portes[b];
  return Math.hypot(p[0] - q[0], p[1] - q[1]) * DETOUR;
}

function longueur(pts) {
  let d = 0;
  for (let i = 1; i < pts.length; i++)
    d += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return d;
}

// La clef du cache est NUMÉRIQUE : deux index de bâtiment, pas deux triplets de
// coordonnées concaténés. Fabriquer une chaîne à chaque appel, c'est allouer
// autant de fois qu'il y a de marcheurs et d'images.
function cheminBat(v, a, b) {
  return chemin(v, _table.portes[a], _table.portes[b], a * 100000 + b);
}

/**
 * Le rang de chaque rôle, tiré du manifeste des corps — `journee()` et `ou()`
 * en ont besoin, et le binaire ne porte que l'index du rôle.
 */
export function rangs(manifesteGens) {
  const r = {};
  for (const [role, d] of Object.entries(manifesteGens._roles)) r[role] = d.rang;
  return r;
}

/** Vider les caches — changement de jour, de lieu, ou simple ménage. */
export function oublier() { _lieu = null; _table = null; _voirie = null; _chemins.clear(); }
