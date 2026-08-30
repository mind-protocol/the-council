
// ---- le monde en volume ---------------------------------------------------
// `monde/portreal.*.json` est l'atelier : le relief (grille de 10 m), le bâti
// (48 000 volumes en colonnes) et le graphe (36 Mo, toutes couches). On ne
// jette pas 36 Mo au navigateur : la voirie est TAILLÉE ici, couche par couche,
// et le résultat est gardé en mémoire tant que le fichier n'a pas rebougé — la
// chaîne (relief → graphe → densifier → coudre) réécrit ces fichiers en cours
// de session, et la page doit voir la version du moment sans qu'on redémarre.
//
// Le sous-sol et les passages cachés ne descendent que si on les demande
// nommément : c'est de la vérité brute, et `connu_de` y est écrit en clair.
// Les lieux que le monde 3D sait montrer. Un lieu = trois fichiers au même
// format (relief, bâti, graphe) et, quand il en a une à la bonne échelle, une
// carte 2D dont on tire la muraille. Peyredragon n'en a pas : son dessin est à
// 260 unités pour l'île entière quand celui de Port-Réal est à 12 m l'unité —
// ses murs sont donc livrés déjà en mètres dans son `bati`, et `carte` est nul.

const fs = require("fs");
const path = require("path");
const { RACINE } = require("./contexte");
const { envoyer } = require("./http");
const { qui } = require("./siege");

const LIEUX3D = {
  "port-real": {
    nom: "Port-Réal", sous: "les trois collines, les sept portes et la Néra",
    prefixe: "portreal", carte: path.join("etat", "villes", "port-real.json"),
    vue: [[9200, -2600, 2600], [2900, 1700, 40]],
    // Trois hauteurs de regard sur le même lieu, du plus large au plus serré.
    // C'est ce que lit `?echelle=` du banc d'essai et ce que prend l'échelle
    // « la ville » du décor — qui s'ouvre sur `ville`, jamais sur la baie.
    vues: {
      ville: [[4300, 3450, 1150], [2750, 1900, 40]],
      // À la verticale du Donjon Rouge : un plan, pas une perspective. Une vue
      // oblique flatte la silhouette et ment sur les distances — or c'est
      // justement pour mesurer une cour et un chemin de ronde qu'on l'ouvre.
      // Centré sur l'ENCEINTE du Donjon (3504-4224 × 960-1560 d'après la carte),
      // pas sur le repère qui en nomme le donjon. Presque à la verticale — 14°
      // de biais depuis le sud, assez pour que les tours aient un flanc et une
      // ombre, trop peu pour qu'on cesse de lire les distances comme sur un plan.
      chateau: [[3864, 1057, 835], [3864, 1260, 40]],
      salle: [[2810, 2210, 34], [2760, 2280, 22]],
    },
    // Où le joueur se tient quand il est dans ce lieu — la place forte, pas la
    // ville entière. C'est ce que la balise de `monde/vous.js` va planter dans
    // le relief : sans elle, l'échelle « la ville » montre un beau caillou dont
    // rien ne dit qu'on est dedans.
    vous: [3864, 1260, 40],
    // CE QUE LA VILLE CONTIENT. Le monde en volume est bâti par VILLE, mais un
    // joueur peut se tenir dans un BÂTIMENT : si `personnages.lieu_id` passait
    // de « port-real » à un id de maison, `ville3d` ne trouverait plus de lieu
    // à son nom et les trois hauteurs — la ville, le quartier, vous —
    // disparaîtraient de la rangée. Un bâtiment de Port-Réal EST à Port-Réal :
    // on l'écrit ici, une fois, le jour où l'un d'eux devient un lieu.
    //
    // Vide pour l'instant, et c'est juste : nos sièges se tiennent à
    // « port-real » et « peyredragon », qui sont les clefs de cette table.
    contient: [],
  },
  peyredragon: {
    nom: "Peyredragon", sous: "l'île, le Dragonmont et la rade",
    prefixe: "peyredragon",
    // Le château est servi en VRAI maillage (parois épaisses, portes percées),
    // pas en boîtes : deux cents mètres, ça se paie. Du coup la carte n'a plus
    // de muraille à donner — elle serait un doublon de ce que le maillage porte.
    carte: null, maillage: true,
    // De QUOI ce lieu est tiré, et par quel fichier on date sa dernière
    // génération. Le modèle et les fichiers servis sont deux choses distinctes :
    // toucher l'un sans relancer l'autre fait diverger le jeu et les images
    // SANS RIEN CASSER — c'est arrivé deux fois (des salles d'un plan abandonné,
    // une courtine restée à 26 m). On date, donc, et on le dit.
    sources: ["scripts/materialisation", "scripts/monde/peyredragon.py"],
    temoin: "monde/peyredragon.maillage.json",
    regenerer: "python scripts/monde/peyredragon.py",
    vue: [[6100, 1500, 1300], [4400, 2100, 120]],
    // Le maillage tient entre x 4316-4973 et y 1938-2227, jusqu'à 205 m :
    // le château se prend du sud-est, la salle à hauteur de cour.
    vues: {
      // MESURÉ DANS LE PANNEAU, pas déduit. À 1 300 m d'altitude l'île tenait
      // dans le cadre mais le château y faisait dix pixels : un onglet de 490
      // par 430 n'est pas un banc d'essai plein écran, et un cadrage qui va
      // bien sur l'un est vide sur l'autre. À 430 m et 620 de recul, la roche
      // remplit douze quinzièmes de la hauteur et la mer tient le reste.
      ville: [[5186, 1689, 430], [4820, 2038, 60]],
      // Centré sur le maillage, cadré serré sur son cœur plutôt que sur ses 657 m
      // d'un bout à l'autre — on vient voir une place forte, pas la mesurer. Et
      // 14° de biais depuis le sud : les tours gagnent un flanc sans que le plan
      // cesse de se lire.
      //
      // MESURÉ, pas estimé. Le cadrage d'avant ([[4913,1917,130],[4645,2082,55]])
      // disait 14° et en faisait 77 : la caméra était à SIX mètres au-dessus du
      // plateau du château (124 m) et visait un point à mi-falaise. Ce n'était
      // pas un quartier vu de haut, c'était une vue de plain-pied qui empilait
      // les trente-quatre salles dans deux cents pixels — d'où plus aucun nom
      // possible dessus. Le cœur bâti fait 289 × 241 m autour de [4459, 2099] ;
      // à 402 m de recul et 14° depuis la verticale, il tient dans le cadre et
      // chaque pièce a sa place à elle.
      chateau: [[4459, 2002, 530], [4459, 2099, 140]],
      salle: [[4820, 1900, 95], [4644, 2082, 60]],
    },
    vous: [4644, 2082, 60],
  },
};
const LIEU3D_DEFAUT = "port-real";

// ===========================================================================
// MARCHER DANS LA VILLE — le graphe piéton, le bâti d'à côté, et la montre
//
// On joue une balade : le joueur pose un but sur la carte, et la troupe y va
// à pied, rue par rue, pendant que la montre tourne. Trois choses vivent ici
// et nulle part ailleurs, parce qu'elles ont toutes besoin des mêmes 7 Mo de
// ville qu'on ne va pas envoyer au navigateur :
//
//   1. LE CHEMIN — Dijkstra sur les 18 314 arêtes de `<x>.rues.json`. Le coût
//      est en MINUTES, pas en mètres : un escalier de Visenya ne se monte pas
//      à la vitesse d'une artère, et c'est ce qui fait que le chemin le plus
//      court n'est pas toujours le plus rapide. La vitesse de la balade sort
//      donc du chemin lui-même, comme demandé — on ne la règle nulle part.
//   2. CE QU'ON PASSE — à chaque pas, les bâtiments à portée de regard, avec
//      leur métier et leur quartier. C'est la matière de la balade : sans ça,
//      le MJ reçoit des coordonnées et ne peut rien en dire.
//   3. LA MONTRE ET LA POSITION — marcher coûte des minutes, et il n'y a pas
//      de raison qu'elles soient gratuites parce qu'on marche sur une carte.
//
// LE GRAPHE N'EST PAS CONNEXE, et c'est un fait des données : 134 composantes,
// dont une de 13 792 nœuds et 133 miettes. On raccroche donc toujours au plus
// proche nœud DE LA GRANDE, sans quoi un but posé sur un îlot rend « pas de
// chemin » pour une ville entière qui en a un.
// ===========================================================================
// ===========================================================================
// DEBUG — LE MIROIR DU NARRATEUR.  ⚠ À RETIRER ⚠
//
// Mettre à `false` (ou supprimer les vingt lignes qui s'en servent, cherchez
// DEBUG_MARCHE_AU_FIL) rend le jeu à sa règle. Tant que c'est `true`, chaque
// pas de balade ou de combat est ÉCRIT DANS LE FIL DU JOUEUR en plus d'être
// envoyé au MJ — on voit passer, en direct, exactement ce que le narrateur
// reçoit.
//
// CE QUE ÇA VIOLE, ET IL FAUT LE SAVOIR : « la page ne dit jamais ce qu'on
// perçoit, le récit est au MJ ». Ici elle le dit, et elle dit même le brut —
// `croise`, que le joueur ne doit jamais voir en temps normal parce que c'est
// la matière que le MJ va mettre en scène. C'est un outil de mise au point,
// pas une fonctionnalité : on regarde la tuyauterie pendant qu'on la règle.
const DEBUG_MARCHE_AU_FIL = true;

const VITESSES = {          // mètres par minute, à pied, dans une ville
  artere: 78, rue: 72, ruelle: 62, quai: 68, abord: 62, escalier: 26,
};
const _rues = { cle: null, g: null };
// Le reste de minute d'une marche en cours, par siege. Voir `/marche`.
const _resteMarche = {};
// L'INSTANT DE DEMARRAGE DE CE SERVEUR. Il sert de signature aux tampons de
// balade (`etat/marches/`) : un tampon signe d'un autre demarrage est une
// promenade que plus personne ne finira — on la ferme au lieu de s'y ajouter.
// Voir `/marche`.
const SESSION_SERVEUR = Date.now();

function graphePieton(lieu) {
  const d = LIEUX3D[lieu] || LIEUX3D[LIEU3D_DEFAUT];
  const f = path.join(RACINE, "monde", d.prefixe + ".rues.json");
  const cle = d.prefixe + ":" + String(fs.statSync(f).mtimeMs);
  if (_rues.cle === cle) return _rues.g;
  const src = JSON.parse(fs.readFileSync(f, "utf-8"));
  // On numérote : un Dijkstra sur des chaînes de caractères passe son temps
  // dans la table de hachage, et la ville en a quinze mille.
  const num = new Map();
  const xs = [], ys = [], adj = [];
  const idx = (nom) => {
    let i = num.get(nom);
    if (i === undefined) {
      const p = src.noeuds[nom];
      if (!p) return -1;
      i = xs.length;
      num.set(nom, i);
      xs.push(p[0]);
      ys.push(p[1]);
      adj.push([]);
    }
    return i;
  };
  for (const a of src.aretes || []) {
    const i = idx(a.de), j = idx(a.vers);
    if (i < 0 || j < 0) continue;
    const v = VITESSES[a.g] || VITESSES.rue;
    const min = (a.m || Math.hypot(xs[i] - xs[j], ys[i] - ys[j])) / v;
    adj[i].push([j, min, a.g]);
    adj[j].push([i, min, a.g]);
  }
  // La grande composante, une fois pour toutes.
  const comp = new Int32Array(xs.length).fill(-1);
  let meilleur = -1, taille = 0;
  for (let n = 0, c = 0; n < xs.length; n++) {
    if (comp[n] >= 0) continue;
    const pile = [n];
    comp[n] = c;
    let t = 0;
    while (pile.length) {
      const x = pile.pop();
      t++;
      for (const [y] of adj[x]) if (comp[y] < 0) { comp[y] = c; pile.push(y); }
    }
    if (t > taille) { taille = t; meilleur = c; }
    c++;
  }
  const g = { xs, ys, adj, comp, grande: meilleur, noms: src.noeuds,
              reperes: src.reperes || {} };
  _rues.cle = cle;
  _rues.g = g;
  return g;
}

// Le nœud le plus proche d'un point, dans la grande composante seulement.
function noeudProche(g, x, y) {
  let best = -1, bd = Infinity;
  for (let i = 0; i < g.xs.length; i++) {
    if (g.comp[i] !== g.grande) continue;
    const d = (g.xs[i] - x) ** 2 + (g.ys[i] - y) ** 2;
    if (d < bd) { bd = d; best = i; }
  }
  return best;
}

// Dijkstra, tas binaire. Quinze mille nœuds : quelques millisecondes.
function cheminPieton(g, a, b) {
  const n = g.xs.length;
  const dist = new Float64Array(n).fill(Infinity);
  const prec = new Int32Array(n).fill(-1);
  const tas = [[0, a]];
  dist[a] = 0;
  const monter = (i) => {
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (tas[p][0] <= tas[i][0]) break;
      [tas[p], tas[i]] = [tas[i], tas[p]];
      i = p;
    }
  };
  const descendre = () => {
    const fin = tas.pop();
    if (!tas.length) return;
    tas[0] = fin;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < tas.length && tas[l][0] < tas[m][0]) m = l;
      if (r < tas.length && tas[r][0] < tas[m][0]) m = r;
      if (m === i) break;
      [tas[m], tas[i]] = [tas[i], tas[m]];
      i = m;
    }
  };
  while (tas.length) {
    const [d, x] = tas[0];
    descendre();
    if (x === b) break;
    if (d > dist[x]) continue;
    for (const [y, w] of g.adj[x]) {
      const nd = d + w;
      if (nd < dist[y] - 1e-9) {
        dist[y] = nd;
        prec[y] = x;
        tas.push([nd, y]);
        monter(tas.length - 1);
      }
    }
  }
  if (!isFinite(dist[b])) return null;
  const route = [];
  for (let x = b; x >= 0; x = prec[x]) route.push(x);
  route.reverse();
  return { route, minutes: dist[b] };
}

// ---- le bâti d'à côté ------------------------------------------------------
// 48 377 bâtiments : on n'en garde que ce qu'on regarde en passant — où, quel
// métier, quel quartier, quelle taille — dans des tableaux compacts, avec une
// grille de 60 m pour n'en fouiller qu'une poignée par pas. Le JSON d'origine
// (5 Mo) est relâché aussitôt lu.
const _bati = { cle: null, i: null };

function batiIndex(lieu) {
  const d = LIEUX3D[lieu] || LIEUX3D[LIEU3D_DEFAUT];
  const f = path.join(RACINE, "monde", d.prefixe + ".bati.json");
  const cle = d.prefixe + ":" + String(fs.statSync(f).mtimeMs);
  if (_bati.cle === cle) return _bati.i;
  const src = JSON.parse(fs.readFileSync(f, "utf-8"));
  const c = src._colonnes;
  const C = (nom) => c.indexOf(nom);
  const [ix, iy, ifa, ipr, iet] =
    [C("x"), C("y"), C("facade_m"), C("profondeur_m"), C("etages")];
  const [iu, iq, icat] = [C("usage"), C("quartier"), C("cat")];
  // LA PORTE ET L'EMPRISE, qu'on ne chargeait pas. Chaque bâtiment de la ville
  // cuite porte une porte (`porte_x`, `porte_y`) qui tombe SUR la voirie — à
  // zéro mètre du graphe piéton, mesuré. C'est ce qui permet d'aller « chez le
  // tanneur » au lieu d'aller au pixel qu'on a touché : voir `butProche`.
  const [ipx, ipy] = [C("porte_x"), C("porte_y")];
  const n = src.bati.length;
  const xs = new Float32Array(n), ys = new Float32Array(n);
  const px = new Float32Array(n), py = new Float32Array(n);
  // Le rayon d'encombrement : la demi-diagonale de l'emprise. Il sert à savoir
  // si un clic est POSÉ SUR la maison ou à côté d'elle, ce qu'un simple « la
  // plus proche » ne dit pas — une halle de trente mètres et une masure de six
  // ne se ratent pas de la même façon.
  const ray = new Float32Array(n);
  const aire = new Float32Array(n), et = new Uint8Array(n);
  const usages = [], quartiers = [], cats = [];
  const iu8 = new Uint8Array(n), iq8 = new Uint8Array(n), ic8 = new Uint8Array(n);
  const tab = (liste, v) => {
    let k = liste.indexOf(v);
    if (k < 0) { liste.push(v); k = liste.length - 1; }
    return k;
  };
  const PAS = 60;
  const grille = new Map();
  for (let k = 0; k < n; k++) {
    const r = src.bati[k];
    xs[k] = r[ix]; ys[k] = r[iy];
    // Sans porte écrite, on retombe sur le centre : c'est faux de quelques
    // mètres et ça ne casse rien, alors qu'un NaN casserait le Dijkstra.
    px[k] = isFinite(r[ipx]) ? r[ipx] : r[ix];
    py[k] = isFinite(r[ipy]) ? r[ipy] : r[iy];
    ray[k] = Math.hypot(r[ifa] || 8, r[ipr] || 8) / 2;
    aire[k] = (r[ifa] || 0) * (r[ipr] || 0);
    et[k] = Math.min(255, r[iet] || 1);
    iu8[k] = tab(usages, r[iu] || "");
    iq8[k] = tab(quartiers, r[iq] || "");
    ic8[k] = tab(cats, r[icat] || "");
    const g = ((xs[k] / PAS) | 0) + "," + ((ys[k] / PAS) | 0);
    let l = grille.get(g);
    if (!l) grille.set(g, l = []);
    l.push(k);
  }
  const i = { xs, ys, px, py, ray, aire, et, iu8, iq8, ic8,
              usages, quartiers, cats, grille, PAS };
  _bati.cle = cle;
  _bati.i = i;
  return i;
}

// ---------------------------------------------------------------------------
// OÙ L'ON VA QUAND ON A CLIQUÉ LÀ.
//
// UN CLIC N'EST PAS UN POINT, C'EST UNE INTENTION. On envoyait au chemin les
// mètres exacts du pixel touché, et l'itinéraire finissait par un segment droit
// de la dernière rue jusqu'à ce pixel — à travers les murs s'il le fallait.
// Pire : ce qu'on annonçait au joueur était le plus proche des VINGT-CINQ
// repères de la ville, c'est-à-dire, la plupart du temps, un nom à trois cents
// mètres de l'endroit visé. On cliquait la taverne et la barre disait « La
// porte de Fer ».
//
// Or la ville cuite sait exactement où l'on entre : chaque bâtiment porte sa
// porte, et ces portes tombent SUR le graphe piéton (médiane mesurée : zéro
// mètre). Un clic posé sur une maison devient donc « la porte de cette
// maison-là », ce qui est à la fois précis, atteignable, et la seule chose
// qu'un homme puisse vouloir dire en montrant une maison du doigt.
//
// ON NE SNAPPE QUE SI L'ON EST DESSUS. Accrocher au plus proche dans un rayon
// fixe rendrait impossible d'aller sur une place ou un quai : tout point de la
// ville a une maison à vingt mètres. Le test est donc l'EMPRISE — on est sur le
// bâtiment, à une marge près — ce qui recouvre exactement ce que le survol
// montre déjà sous le curseur. Ce qu'on voit est où l'on va.
const MARGE_CLIC = 6;      // mètres de pardon : le doigt tremble, le zoom ment

function butProche(lieu, x, y) {
  const b = batiIndex(lieu);
  const R = 40;                       // au-delà, aucune emprise ne peut mordre
  const cx = (x / b.PAS) | 0, cy = (y / b.PAS) | 0;
  const port = Math.ceil(R / b.PAS);
  let best = -1, marge = Infinity;
  for (let i = cx - port; i <= cx + port; i++) {
    for (let j = cy - port; j <= cy + port; j++) {
      const l = b.grille.get(i + "," + j);
      if (!l) continue;
      for (const k of l) {
        const d = Math.hypot(b.xs[k] - x, b.ys[k] - y);
        // De combien on déborde de l'emprise : négatif = on est dessus. Entre
        // deux maisons qui se touchent, celle dont on déborde le moins.
        const m = d - b.ray[k];
        if (m < marge && m <= MARGE_CLIC) { marge = m; best = k; }
      }
    }
  }
  if (best < 0) return null;
  return {
    bat: best, x: b.px[best], y: b.py[best],
    usage: b.usages[b.iu8[best]], cat: b.cats[b.ic8[best]],
    quartier: b.quartiers[b.iq8[best]],
    aire: Math.round(b.aire[best]), etages: b.et[best],
  };
}

// Ce qu'on a sous les yeux à un pas donné. On rend les plus PROCHES, et l'on
// garde à part le plus gros du lot : dans une rue de masures, la halle qu'on
// longe est ce qu'on décrirait en premier, même si trois portes sont plus près.
// COMMENT ON DÉSIGNE UN BÂTIMENT. Il n'a pas de nom — la ville a été semée,
// pas peuplée d'enseignes —, mais il a une IDENTITÉ : son rang dans
// `bati.json`. C'est déjà la monnaie du jeu (`affecter.py --bati 36391`, et
// c'est par elle que le Grenier est devenu le bâtiment 36391 dans
// `corps.json`). On la fait donc circuler jusqu'au MJ : chaque bâtiment
// rapporté porte son `bat`, et le MJ peut le baptiser d'une ligne —
//
//     python scripts/affecter.py --affecter lieu:la-taverne-du-guet 12345 \
//            --nom "La Taverne du Guet" --vraiment
//
// — après quoi CETTE MÊME BALADE le nommera, pour toujours et pour les deux
// sièges. C'est la boucle entière : la ville engendrée fournit la matière, le
// jeu y accroche des noms, et ce qui a été nommé une fois revient nommé.
//
// LA LIMITE, ET IL FAUT LA CONNAÎTRE : le rang n'est stable que tant que
// `bati.json` n'est pas réengendré. S'il l'était, tous les rangs glisseraient
// — mais `affecter.py` écrit aussi les mètres (`xyz`), de sorte qu'un
// réamorçage se rattraperait par la position et non par le numéro.
function batiAutour(lieu, x, y, rayon, combien, nommes) {
  const b = batiIndex(lieu);
  const cx = (x / b.PAS) | 0, cy = (y / b.PAS) | 0;
  const port = Math.ceil(rayon / b.PAS);
  const vus = [];
  for (let i = cx - port; i <= cx + port; i++) {
    for (let j = cy - port; j <= cy + port; j++) {
      const l = b.grille.get(i + "," + j);
      if (!l) continue;
      for (const k of l) {
        const d = Math.hypot(b.xs[k] - x, b.ys[k] - y);
        if (d <= rayon) vus.push([d, k]);
      }
    }
  }
  vus.sort((p, q) => p[0] - q[0]);
  const su = nommes || new Map();
  const dit = (k, d) => {
    const n = su.get(k);
    return {
      bat: k, nom: (n && n.nom) || null, cle: (n && n.cle) || null,
      usage: b.usages[b.iu8[k]], cat: b.cats[b.ic8[k]],
      quartier: b.quartiers[b.iq8[k]],
      aire: Math.round(b.aire[k]), etages: b.et[k], a: Math.round(d),
    };
  };
  // UN MÉTIER PAR LIGNE, ET LE BANAL COMPTÉ À PART. Les quatre bâtiments les
  // plus proches sont, statistiquement, quatre maisons : les deux tiers de la
  // ville en sont, et un dixième de plus est du taudis. Rendre les quatre
  // premiers, c'est donc envoyer au MJ « une maison, une maison, une maison,
  // une maison » à chaque pas — vrai, et sans rien à en dire.
  //
  // Ce qui se raconte, c'est ce qui DÉPASSE : la forge, le puits, la taverne
  // du coin. On garde donc le plus proche de chaque métier distinct, les
  // remarquables d'abord, et l'on RÉSUME le tissu ordinaire d'un chiffre
  // (« et douze maisons ») — ce qui dit la densité sans occuper la place.
  //
  // CE QUI EST NOMMÉ PASSE AVANT TOUT. Un bâtiment que la partie a baptisé
  // n'est plus du tissu : c'est la boutique de la Veuve, et l'on ne longe pas
  // la boutique de la Veuve sans que ça compte. Il entre dans la liste quel
  // que soit son métier et quels que soient ses voisins.
  const ORDINAIRE = new Set(["maison", "taudis", "cabane"]);
  const parMetier = new Map();
  const banal = new Map();
  const connus = [];
  for (const [d, k] of vus) if (su.has(k)) connus.push(dit(k, d));
  for (const [d, k] of vus) {
    if (su.has(k)) continue;               // déjà pris, et pris nommément
    const u = b.usages[b.iu8[k]];
    if (ORDINAIRE.has(u)) {
      banal.set(u, (banal.get(u) || 0) + 1);
      if (!parMetier.has(u)) parMetier.set(u, dit(k, d));
      continue;
    }
    if (!parMetier.has(u)) parMetier.set(u, dit(k, d));
  }
  const notables = [...parMetier.entries()]
    .filter(([u]) => !ORDINAIRE.has(u)).map(([, v]) => v)
    .sort((p, q) => p.a - q.a).slice(0, combien || 4);
  // s'il n'y a VRAIMENT que du tissu ordinaire, on le dit plutôt que rien
  const reste = notables.length ? notables
    : [...parMetier.values()].sort((p, q) => p.a - q.a).slice(0, 2);
  const proches = connus.concat(reste);
  let gros = null;
  for (const [d, k] of vus) if (!gros || b.aire[k] > gros.aire) gros = dit(k, d);
  return { proches, connus, gros, combien: vus.length,
           tissu: [...banal.entries()].map(([u, n]) => [u, n]) };
}

// Les métiers, en français, avec leur article. Les données parlent en slugs
// (`echoppe`, `maison-officier`, `fosse-vidange`) : c'est bon pour un index,
// c'est illisible dans un bandeau que le joueur a sous les yeux. Ce qui manque
// à la table retombe sur le slug tel quel — mieux vaut un mot brut qu'un trou.
const METIERS = {
  maison: "une maison", taudis: "un taudis", echoppe: "une échoppe",
  cabane: "une cabane", manse: "une belle demeure", taverne: "une taverne",
  boulangerie: "une boulangerie", "maison-officier": "un logis d'officier",
  forge: "une forge", puits: "un puits", entrepot: "un entrepôt",
  brasserie: "une brasserie", bordel: "un bordel", ecurie: "une écurie",
  tannerie: "une tannerie", auberge: "une auberge",
  "chantier-bois": "un chantier de bois", teinturerie: "une teinturerie",
  "septuaire-quartier": "un septuaire de quartier", etuve: "une étuve",
  poterie: "une poterie", abattoir: "un abattoir", moulin: "un moulin",
  "fosse-vidange": "une fosse à vidange", "marche-quartier": "un marché",
  "corps-de-garde": "un corps de garde", change: "une table de change",
  corderie: "une corderie", grenier: "un grenier à grain",
  voilerie: "une voilerie", caserne: "une caserne", geole: "une geôle",
  "donjon-rouge": "le Donjon Rouge", "fosse-dragons": "la Fosse aux Dragons",
  "vieux-septuaire": "le vieux septuaire", "bureau-port": "le bureau du port",
  "guilde-alchimistes": "la Guilde des Alchimistes",
};
const metier = (u) => METIERS[u] || u || "une maison";
// Le tissu se compte, donc il se met au pluriel. Trois mots suffisent : c'est
// tout ce qui, dans cette ville, se rencontre par paquets.
const PLURIELS = { maison: "maisons", taudis: "taudis", cabane: "cabanes" };

// --- QUI ON CROISE ----------------------------------------------------------
// Le compte et les métiers des gens rencontrés à un pas de balade, mis en une
// ligne lisible. Le calcul est fait par la page (voir `foule2d.presents`) :
// elle a les corps sous la main, le serveur ne les a pas, et les lui porter
// coûterait `journee.js`, la voirie et quatre méga-octets de cellules pour
// redire ce qui est déjà su.
//
// ON NE REND QUE CE QUI SE RENCONTRE. `dehors` est du monde qu'on croise ;
// `dedans` est un chiffre d'ambiance — il dit qu'un quartier est habité, pas
// qu'il y a foule. Le MJ ne doit jamais confondre les deux, sans quoi
// Culpucier endormi devient une cohue.
//
// QUELQUES RÔLES SEULEMENT. Il y en a quatre-vingt-huit et l'on n'en dit
// jamais plus de quatre : au-delà, ce n'est plus une rue qu'on décrit, c'est
// un recensement, et l'on retombe dans le mur de texte que le tunnel interdit.
const ROLES_DITS = 4;

function direGens(g) {
  if (!g || typeof g !== "object") return null;
  // Le rôle vient du binaire en kebab-case (`chef-de-feu`) : on lui rend ses
  // espaces et on s'arrête là. PAS DE PLURIEL AUTOMATIQUE — « chef de feu » se
  // pluralise sur la tête et non sur la queue, et une règle naïve écrirait
  // « chef de feus ». Le chiffre est devant, il suffit ; c'est le MJ qui met
  // la phrase en français, et c'est son métier.
  const dire = (m) => String(m).replace(/-/g, " ");
  const liste = Array.isArray(g.metiers) ? g.metiers : [];
  const tete = liste.slice(0, ROLES_DITS)
    .map(([m, n]) => (n > 1 ? n + " " + dire(m) : dire(m)));
  const reste = liste.slice(ROLES_DITS).reduce((s, p) => s + p[1], 0);
  if (reste) tete.push("et " + reste + " autre" + (reste > 1 ? "s" : ""));
  const portes = (Array.isArray(g.portes) ? g.portes : [])
    .slice(0, ROLES_DITS).map(([s, n]) => n + " " + s);
  return {
    rayon: g.rayon || null,
    // CE QU'ON CROISE — le seul chiffre qui compte pour un marcheur.
    croises: g.croises | 0,
    en_rue: g.rue | 0,
    attroupes: g.place | 0,
    // « 3 portefaix, 2 guet, 1 servante » — ou rien du tout, et le rien est
    // une information : une rue vide à trois heures du matin est exactement
    // ce qu'on était venu vérifier.
    metiers: tete.join(", ") || null,
    // CE QU'ON PEUT ALLER CHERCHER, et par quelle porte. « 12 à la taverne »
    // se joue ; « 12 portefaix » ne dit pas où frapper.
    sous_toit: g.toit | 0,
    portes: portes.join(", ") || null,
    // CEUX QUI SONT EN ARMES. Ligne à part, et en TÊTE de ce qu'on rapporte :
    // deux cents hommes rangés devant une porte ne sont pas un détail de la
    // rue, c'est la rue. Ils manquaient entièrement — le marcheur passait à
    // vingt pas d'eux et rapportait le compte des gens qui dormaient.
    //
    // Par camp et par état, parce que c'est tout ce qu'on voit d'un coup d'œil
    // et que ça décide de ce qu'on fait : « 180 garde/tient » est un mur, « 40
    // garde/deroute » est une porte perdue, et l'on ne s'approche pas des deux
    // de la même façon.
    en_armes: g.en_armes | 0,
    armes: (Array.isArray(g.armes) ? g.armes : []).slice(0, 6)
      .map(([c, n]) => n + " " + String(c).replace("/", " ")).join(" · ") || null,
    // CE QU'ILS FONT — la seule ligne qui porte une ACTION et non un état, et
    // celle dont un récit peut partir. « fuient : 6 portefaix, 2 servantes »
    // se joue ; « 8 personnes en rue » ne se joue pas, et c'était pourtant
    // tout ce qui remontait quand la ville se vidait sous les armes.
    //
    // QUATRE VERBES AU PLUS, comme les rôles : au-delà on ne décrit plus une
    // rue, on en fait l'inventaire — et l'inventaire est très exactement le
    // mur de texte que le tunnel interdit.
    font: (Array.isArray(g.font) ? g.font : []).slice(0, ROLES_DITS)
      .map(([v, par, n]) => n + " " + v + " (" +
        par.slice(0, 3).map(([m, k]) => k + " " + String(m).replace(/-/g, " "))
           .join(", ") + ")")
      .join(" · ") || null,
    detail_font: Array.isArray(g.font) ? g.font : [],
    // L'AMBIANCE, et rien de plus. Ne jamais lire ce chiffre comme une foule :
    // c'est le nombre de gens qui dorment derrière les murs qu'on longe.
    chez_eux: g.chez | 0,
    detail: liste,
    detail_toit: Array.isArray(g.metiers_toit) ? g.metiers_toit : [],
  };
}

// Le repère le plus proche, pour que la position se DISE : « à deux cents pas
// de la porte de la Gadoue » vaut mieux que « en 3340, 601 ».
// UN REPÈRE EST CE QU'ON NOMME EN LEVANT LA TÊTE : une porte, un marché, un
// quai, une colline. La table en contient aussi la structure du semis — des
// « halls », des « arcades », des « seuils » — qui ne sont des repères pour
// personne : « à 190 pas de Arcade de Le marché aux poissons » ne situe rien
// et se lit mal. On les écarte ici plutôt que de les corriger à l'affichage.
const REPERES_VRAIS = new Set([
  // Port-Réal — sept portes, trois collines, et ce qu'on voit de loin.
  "porte", "quai-amont", "quai-aval", "donjon",
  "fosse", "septuaire", "guilde", "casernes", "grand-marche", "marche-chevaux",
  "marche-poissons", "bureau-port", "aire-bris", "sommet-visenya",
  "sommet-aegon", "sommet-rhaenys",
  // Peyredragon — les treize. La liste est courte parce que l'île l'est : sur
  // trois cents mètres de château, la forge et les cuisines SONT ce qu'on
  // nomme en levant la tête, là où à Port-Réal ce ne serait qu'une maison de
  // plus. Aucun « seuil » ni « cour » ici : les treize nœuds nommés du graphe
  // sont treize repères, et c'est pour ça qu'on peut tous les prendre.
  "roukerie", "hotes", "garnison", "corps-de-garde", "ecuries", "forge",
  "cuisines", "grande-salle", "retrait", "tambour", "quai", "dragonmont",
]);

function repereProche(lieu, x, y) {
  const g = graphePieton(lieu);
  let best = null;
  for (const nom in g.reperes) {
    const cle = g.reperes[nom];
    if (!REPERES_VRAIS.has(String(cle).split(":")[0])) continue;
    const p = g.noms[cle];
    if (!p) continue;
    const d = Math.hypot(p[0] - x, p[1] - y);
    if (!best || d < best.a) best = { nom, a: Math.round(d) };
  }
  return best;
}

const _monde = { cle: null, couches: null, lieu: null };
function grapheTaille(lieu) {
  const d = LIEUX3D[lieu] || LIEUX3D[LIEU3D_DEFAUT];
  const f = path.join(RACINE, "monde", d.prefixe + ".graph.json");
  const cle = d.prefixe + ":" + String(fs.statSync(f).mtimeMs);
  if (_monde.cle === cle) return _monde.couches;
  const g = JSON.parse(fs.readFileSync(f, "utf-8"));
  const couches = {};
  for (const a of g.aretes || []) {
    (couches[a.couche] = couches[a.couche] || []).push(
      { genre: a.genre, largeur_m: a.largeur_m, trace: a.trace, nom: a.nom || undefined });
  }
  // Les repères, ce sont les choses qu'on nomme en regardant la ville : les
  // portes, les collines, les monuments. La densification en a semé onze mille
  // autres (cours, seuils, halls) qui sont de la structure, pas des repères —
  // les envoyer, c'est onze mille étiquettes sur l'écran.
  const REPERE = new Set(["porte", "forteresse", "monument", "septuaire", "guilde",
    "caserne", "marche", "quai", "office", "chantier", "sommet"]);
  couches._reperes = (g.noeuds || [])
    .filter((n) => n.nom && n.niveau === 0 && REPERE.has(n.genre))
    .map((n) => ({ id: n.id, nom: n.nom, genre: n.genre, xyz: n.xyz }));
  _monde.cle = cle; _monde.couches = couches;
  return couches;
}

// ---- les repères DÉCIDÉS en jeu ------------------------------------------
// Le graphe donne les noms que la ville porte d'elle-même : les portes, les
// collines, les monuments. Ceux-là sont vrais pour tout le monde et ne changent
// pas d'une partie à l'autre. Les affectations (`scripts/affecter.py`) donnent
// les noms que LA PARTIE a posés dessus — la taverne de Mag, le chantier du
// bout, la cabane où dort le joueur.
//
// Et elles ne se montrent QUE si on l'a demandé. C'est du brouillard, pas de
// l'affichage : affecter un endroit, c'est lui donner des mètres pour calculer ;
// le montrer, c'est dire que le joueur sait où il est. Les deux gestes sont
// séparés parce que les deux dates le sont — on affecte le chantier du bout le
// jour où l'on veut mesurer sa distance, on le montre le jour où le joueur y va.
//
// `visible: true` = tout le monde ; `visible: ["marlo-vasse"]` = ces sièges-là.
// Ce que Marlo a reconnu de ses yeux, la reine ne l'a pas vu.
//
// On relit le fichier à chaque requête, sans cache : il change PENDANT qu'on
// joue et tient sur quelques lignes. Les mètres sont recopiés dans
// l'affectation par le script, donc on n'ouvre jamais les cinq mégaoctets du
// bâti pour poser une étiquette.
const AFFECTE_VISIBLE = new Set(["lieu", "salle"]);

function reperesAffectes(lieu, siege) {
  if (lieu !== LIEU3D_DEFAUT) return [];
  let A;
  try {
    A = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "corps.json"),
                                   "utf8")).affectations || {};
  } catch (e) { return []; }
  const out = [];
  for (const clef of Object.keys(A)) {
    const v = A[clef];
    const genre = clef.split(":")[0];
    // Ce qui est DEDANS n'a pas de nom sur la ville : un livre et un homme
    // n'ont que le toit qui les abrite, sans quoi trois étiquettes se
    // superposent au même mètre carré.
    if (!AFFECTE_VISIBLE.has(genre)) continue;
    if (!v || !Array.isArray(v.xyz) || v.xyz.length < 3) continue;
    const vu = v.visible;
    if (!(vu === true || (Array.isArray(vu) && siege && vu.includes(siege)))) continue;
    out.push({ id: clef, nom: v.nom || clef.split(":")[1], genre: "affecte",
               xyz: v.xyz });
  }
  return out;
}

// ---- la péremption : le modèle a-t-il bougé depuis la dernière génération ?
// Un `statSync` par fichier de source, une fois toutes les cinq secondes. Le
// cache est volontairement court : les sources changent PENDANT qu'on joue, et
// un drapeau qui met une minute à s'allumer ne prévient plus de rien.
const PEREMPTION_TTL = 5000;
const _peremption = { quand: 0, par: {} };

// Une source est soit un fichier, soit un dossier dont on prend les `.py`. On
// ne descend pas dans les sous-dossiers : `__pycache__` n'est pas une source,
// et il rebouge à chaque import.
function sourcesPy(relatif) {
  const abs = path.join(RACINE, relatif);
  try {
    if (!fs.statSync(abs).isDirectory()) return [abs];
    return fs.readdirSync(abs).filter((n) => n.endsWith(".py"))
      .map((n) => path.join(abs, n));
  } catch (e) { return []; }
}

// Rend `null` pour un lieu qui ne déclare pas ses sources (on ne sait rien, on
// n'affirme rien), sinon l'état de fraîcheur avec la liste de ce qui est plus
// récent que la dernière génération.
function peremption(lieu) {
  const d = LIEUX3D[lieu];
  if (!d || !d.sources || !d.sources.length || !d.temoin) return null;
  const t = Date.now();
  if (t - _peremption.quand > PEREMPTION_TTL) { _peremption.quand = t; _peremption.par = {}; }
  if (_peremption.par[lieu] !== undefined) return _peremption.par[lieu];
  let r = null;
  try {
    // Témoin absent = jamais engendré : périmé, et c'est le cas le plus franc.
    let engendre = 0;
    try { engendre = fs.statSync(path.join(RACINE, d.temoin)).mtimeMs; } catch (e) { engendre = 0; }
    const recentes = [];
    for (const s of d.sources) {
      for (const f of sourcesPy(s)) {
        let m;
        try { m = fs.statSync(f).mtimeMs; } catch (e) { continue; }
        if (m > engendre)
          recentes.push({
            fichier: path.relative(RACINE, f).split(path.sep).join("/"),
            modifie: Math.round(m),
          });
      }
    }
    recentes.sort((a, b) => b.modifie - a.modifie);
    r = {
      perime: !engendre || recentes.length > 0,
      temoin: d.temoin, engendre: engendre ? Math.round(engendre) : null,
      sources: recentes, regenerer: d.regenerer || null,
    };
  } catch (e) { r = null; }
  _peremption.par[lieu] = r;
  return r;
}

// Au démarrage, on le DIT. Un drapeau que seule une requête JSON porte ne se
// voit pas quand on relance le serveur pour tout autre chose.
function direLaPeremption() {
  for (const id of Object.keys(LIEUX3D)) {
    const p = peremption(id);
    if (!p || !p.perime) continue;
    const n = p.sources.length;
    console.warn("Le monde 3D de " + LIEUX3D[id].nom + " est PÉRIMÉ : "
      + (p.engendre
        ? n + " source" + (n > 1 ? "s" : "") + " plus récente" + (n > 1 ? "s" : "")
          + " que " + p.temoin + " (" + p.sources.slice(0, 4).map((s) => s.fichier).join(", ")
          + (n > 4 ? ", …" : "") + ")"
        : p.temoin + " n'existe pas")
      + (p.regenerer ? " — relancez : " + p.regenerer : ""));
  }
}

function serviceMonde(req, res, chemin) {
  // `/monde/<quoi>` reste Port-Réal — tout ce qui existait continue de marcher.
  // `/monde/<lieu>/<quoi>` sert un autre lieu, et c'est ce que le client passe
  // en `source` à `ouvrir()`.
  let lieu = LIEU3D_DEFAUT, quoi = chemin;
  const barre = chemin.indexOf("/");
  if (barre > 0 && LIEUX3D[chemin.slice(0, barre)]) {
    lieu = chemin.slice(0, barre);
    quoi = chemin.slice(barre + 1);
  }
  const d = LIEUX3D[lieu];
  const zlib = require("zlib");
  const gzip = /\bgzip\b/.test(req.headers["accept-encoding"] || "");
  const rendre = (corps) => {
    const buf = Buffer.isBuffer(corps) ? corps : Buffer.from(corps, "utf-8");
    if (!gzip) return envoyer(res, 200, buf, "application/json; charset=utf-8");
    return envoyer(res, 200, zlib.gzipSync(buf, { level: 6 }),
      "application/json; charset=utf-8", { "Content-Encoding": "gzip" });
  };
  try {
    // La liste des localisations, pour que la page en propose le choix sans
    // qu'on la recopie à deux endroits.
    if (quoi === "lieux")
      return rendre(JSON.stringify({
        defaut: LIEU3D_DEFAUT,
        lieux: Object.keys(LIEUX3D).map((id) => {
          // `perime` est le drapeau court, `peremption` le détail (le témoin,
          // sa date, les sources plus récentes, la commande qui répare). Un
          // lieu qui ne déclare pas ses sources rend `false` et `null` : on ne
          // sait pas, donc on n'accuse pas.
          const p = peremption(id);
          return {
            id, nom: LIEUX3D[id].nom, sous: LIEUX3D[id].sous,
            carte: !!LIEUX3D[id].carte, maillage: !!LIEUX3D[id].maillage,
            // Les intérieurs : un lieu en a parce que le FICHIER est là, pas
            // parce qu'il s'appelle Peyredragon — même règle que pour les corps.
            interieurs: fs.existsSync(path.join(RACINE, "monde",
              LIEUX3D[id].prefixe + ".interieurs.json")),
            vue: LIEUX3D[id].vue, vues: LIEUX3D[id].vues || null,
            contient: LIEUX3D[id].contient || null,
            vous: LIEUX3D[id].vous || null,
            source: id === LIEU3D_DEFAUT ? "/monde" : "/monde/" + id,
            perime: !!(p && p.perime), peremption: p,
          };
        }),
      }));
    if (quoi === "terrain")
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".terrain.json")));
    if (quoi === "terrain-region") {
      const f = path.join(RACINE, "monde", d.prefixe + ".region-terrain.json");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur:"lieu sans relief régional", lieu }));
      return rendre(fs.readFileSync(f));
    }
    // Le plan 2D, cuit par `scripts/monde/plan_ville.py` : la même ville que le
    // relief, mais dessinée. Un lieu en a un parce que le FICHIER est là —
    // même règle que les corps et les intérieurs, et rien à déclarer ici.
    if (quoi === "plan2d") {
      const f = path.join(RACINE, "monde", d.prefixe + ".plan2d.json");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans plan 2D", lieu }));
      return rendre(fs.readFileSync(f));
    }
    // Le masque du bâti : un bit par mètre carré, cuit avec le plan 2D. Il ne
    // sert qu'à une chose, et elle vaut le transfert — que la foule ne marche
    // jamais dans un mur. Servi en binaire brut, sans mise en forme : c'est un
    // tableau de bits, pas un document.
    if (quoi === "masque") {
      const f = path.join(RACINE, "monde", d.prefixe + ".masque.bin");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans masque", lieu }));
      const buf = fs.readFileSync(f);
      res.writeHead(200, { "Content-Type": "application/octet-stream",
                           "Content-Length": buf.length });
      return res.end(buf);
    }
    // Un maillage : un corps bâti donné tel quel, pour ce qui se regarde de
    // près. Un lieu qui n'en a pas rend `null` — le client ne pose rien.
    if (quoi === "maillage") {
      if (!d.maillage) return rendre(JSON.stringify(null));
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".maillage.json")));
    }
    // Les intérieurs : une pièce creuse par salle, murs épais et portes percées
    // (scripts/monde/peyredragon_interieurs.py). Même format que le maillage,
    // plus une clef `salles` qui donne à chacune sa tranche d'index. Un lieu en
    // est pourvu parce que le fichier existe — pas parce qu'on l'a nommé ici :
    // c'est la règle posée pour les corps, et elle vaut ici aussi.
    if (quoi === "interieurs") {
      const f = path.join(RACINE, "monde", d.prefixe + ".interieurs.json");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans intérieurs", lieu }));
      return rendre(fs.readFileSync(f));
    }
    if (quoi === "bati")
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".bati.json")));
    if (quoi === "carte") {
      // Un lieu sans carte 2D à la bonne échelle rend une carte VIDE plutôt
      // qu'une erreur : `enceinte.js` la parcourt et n'y trouve rien à bâtir,
      // ce qui est exactement ce qu'on veut — ses murs sont dans le bâti.
      if (!d.carte) return rendre(JSON.stringify({ sol: [], corps: [], acteurs: [] }));
      return rendre(fs.readFileSync(path.join(RACINE, d.carte)));
    }
    if (quoi === "voirie") {
      const c = grapheTaille(lieu);
      const q = (req.url.split("?")[1] || "").match(/(?:^|&)couche=([^&]*)/);
      const nom = decodeURIComponent((q && q[1]) || "L1-surface");
      return rendre(JSON.stringify({ couche: nom, aretes: c[nom] || [] }));
    }
    if (quoi === "reperes") {
      const j = qui(req);          // le second argument de `qui` ne sert pas
      return rendre(JSON.stringify({
        reperes: grapheTaille(lieu)._reperes
          .concat(reperesAffectes(lieu, j ? j.personnage_id : null)),
      }));
    }
    // Les corps : le manifeste en JSON, puis une cellule à la fois en BRUT.
    // Le binaire ne passe pas par `rendre` — il est déjà dense, et le gzipper
    // coûte plus de temps processeur qu'il ne rend d'octets.
    if (quoi === "gens") {
      // Ce n'est plus le nom du lieu qui décide s'il est peuplé, c'est
      // l'existence de son manifeste : `peupler.py <lieu>` en écrit un, et le
      // lieu devient peuplé le jour où le fichier apparaît.
      const mf = path.join(RACINE, "monde", d.prefixe + ".gens.json");
      if (!fs.existsSync(mf))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans corps", lieu }));
      return rendre(fs.readFileSync(mf));
    }
    // Les besoins : ce qu'un rôle fait de sa journée, et l'adresse de chaque
    // bâtiment (son puits, sa boulangerie…). C'est de là que sort le mouvement
    // — mais rien n'y bouge : la position se calcule côté page.
    // Les corps DÉCIDÉS en jeu : ceux qu'on a créés pour les grands (le roi
    // n'emprunte le corps de personne) et les emprunts déjà posés. C'est le
    // seul morceau de `etat/` que le décor lit — et il le lit seulement, il
    // n'y écrit jamais.
    //
    // `corps.json` est UN fichier pour tous les mondes : chaque affectation dit
    // le sien (`monde`). Le refuser hors du lieu par défaut était le geste d'une
    // époque où il n'y avait qu'un monde — et il plantait la reine dans un
    // champ : à Peyredragon la page recevait un 404, tombait sur zéro adresse,
    // et repliait la balise sur le point générique du lieu, dehors, alors que
    // ses appartements ont un bâtiment depuis le début. On sert donc toujours,
    // et c'est la page qui écarte ce qui n'est pas de son monde.
    if (quoi === "corps") {
      try {
        return rendre(fs.readFileSync(path.join(RACINE, "etat", "corps.json")));
      } catch (e) {
        return rendre(JSON.stringify({ liens: {}, corps: [] }));
      }
    }
    if (quoi === "besoins") {
      // Comme pour les corps : c'est l'existence du fichier qui dit si un lieu
      // sait faire marcher son monde, pas son nom. `besoins.py <lieu>` en écrit
      // un, et la foule s'y met en mouvement le jour où il paraît.
      const bf = path.join(RACINE, "monde", d.prefixe + ".besoins.json");
      if (!fs.existsSync(bf))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans besoins", lieu }));
      return rendre(fs.readFileSync(bf));
    }
    if (quoi.startsWith("gens/")) {
      // Jamais un morceau de chemin venu du client sans filtre : la clé de
      // cellule est deux entiers signés séparés d'un tiret, suivis de `.bin`,
      // et rien d'autre. Une seule forme d'URL par ressource — tolérer le
      // suffixe absent, c'est se réveiller un jour avec deux caches.
      const m = /^gens\/(-?\d+--?\d+)\.bin$/.exec(quoi);
      if (!m) return envoyer(res, 404, JSON.stringify({ erreur: "cellule", quoi }));
      const clef = m[1];
      // Chaque lieu range ses cellules chez lui. Port-Réal reste à la racine de
      // `monde/gens/` — c'est là qu'elles ont toujours été servies, et l'on ne
      // déplace pas une donnée en vol pour l'élégance. Sans ce découpage,
      // `/monde/<autre>/gens/...` rendrait les corps de Port-Réal sous le nom
      // d'un autre lieu.
      const f = d.prefixe === "portreal"
        ? path.join(RACINE, "monde", "gens", clef + ".bin")
        : path.join(RACINE, "monde", "gens", d.prefixe, clef + ".bin");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "cellule absente", clef }));
      return envoyer(res, 200, fs.readFileSync(f), "application/octet-stream");
    }
  } catch (e) {
    return envoyer(res, 404, JSON.stringify({ erreur: quoi, detail: String(e.message || e) }));
  }
  return envoyer(res, 404, JSON.stringify({ erreur: quoi }));
}

module.exports = { PLURIELS, LIEUX3D, LIEU3D_DEFAUT, VITESSES, SESSION_SERVEUR, graphePieton, noeudProche, cheminPieton, batiIndex, butProche, batiAutour, direGens, repereProche, grapheTaille, reperesAffectes, peremption, direLaPeremption, serviceMonde, _rues, _resteMarche, DEBUG_MARCHE_AU_FIL, metier };
