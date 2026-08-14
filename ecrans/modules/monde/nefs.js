// monde/nefs.js — les coques : au mouillage, à quai, ou tirées sur la grève.
//
// Le bourg vit du poisson. Il a cinq hangars à barques, une corderie, une
// voilerie, cent cinquante mètres de quai bâti et deux rampes qui montent à la
// rue — et pas une coque à l'eau. Une rade vide sous un château qui tient la
// mer est le même mensonge qu'une salle sans personne.
//
// ── D'OÙ VIENT QUOI ──────────────────────────────────────────────────────────
// Le croquis de `etat/ville.json` (servi par `/ville`) donne le COMPTE et le
// FAIT : « neuf coques au mouillage sous les murs », « tirées sur la grève et
// non à l'eau : quatre jours qu'on ne pêche plus ». Ça, c'est de la fiction, et
// ça fait foi — une barque tirée au sec parce que la pêche a cessé est une
// information sur la partie, pas une décoration.
//
// Ses COORDONNÉES, non. Le croquis a son propre repère (260 × 180) et aucune
// transformation vers les mètres n'est déclarée. C'est le même cas que le plan
// des salles : une carte mentale a raison sur ce qu'elle dit, jamais sur où
// elle le met. La place vient donc du monde — la ligne de quai que porte la
// voirie, et le masque d'eau du relief.
//
// ── LA LIGNE D'EAU ───────────────────────────────────────────────────────────
// Une coque flotte à z = 0, l'étale : c'est le plan que pose `mer()`. Le quai,
// lui, est à 3,4 m — un tablier qui domine l'eau de trois mètres, ce qui est la
// hauteur d'un quai. On ne pose donc JAMAIS une nef à l'altitude du quai ;
// c'est l'erreur qui donne des bateaux sur les toits.
"use strict";
import * as T from "/vendor/three.module.min.js";

const ETALE = 0.0;        // le niveau de la mer, celui de `mer()`
const PORTEE = 2600;

const BOIS = 0x6b4f33;    // la coque, goudronnée
const PONT = 0x8a6f4a;
const MAT = 0x5a4028;
const VOILE = 0xcfc3a6;

// Les deux gabarits du lieu, en mètres. Une nef de guerre du Détroit fait une
// vingtaine de mètres et cale un mètre et demi ; une barque de pêche du bourg
// en fait six et cale trente centimètres. `tirant` est sous la flottaison,
// `franc` au-dessus — leur somme est le creux.
const GABARIT = {
  nef:    { L: 21.0, B: 6.2, tirant: 1.55, franc: 1.45 },
  barque: { L: 6.2,  B: 1.9, tirant: 0.38, franc: 0.52 },
};

// ── LA CARÈNE ────────────────────────────────────────────────────────────────
// Une coque n'est pas une boîte affinée : c'est une surface réglée sur ses
// COUPLES. On pose une douzaine de sections en travers, on donne à chacune sa
// demi-largeur, son fond et son plat-bord, et l'on coud le tout. Trois courbes
// suffisent à ce que ça se lise comme un bateau et non comme une caisse :
//
//   la LARGEUR    pleine au milieu, fine aux bouts — c'est ce qui donne l'étrave
//   la TONTURE    le plat-bord remonte à l'avant et à l'arrière
//   la QUÊTE      le fond remonte aussi : une coque ne repose pas à plat
//
// Et le z 0 local est la FLOTTAISON, pas le fond. Un bateau s'enfonce : sous
// zéro le tirant d'eau, au-dessus le franc-bord. Poser la coque entière sur la
// nappe donnait des bateaux qui affleurent comme des jouets de bassin.
function carene(L, B, tirant, franc) {
  const S = 15, K = 5;                 // couples, et points par demi-couple
  const pos = [], idx = [];
  const large = (u) => Math.pow(Math.max(0, 1 - Math.pow(Math.abs(u), 2.3)), 0.55);
  const fond = (u) => -tirant * (1 - Math.pow(Math.abs(u), 2.6) * 0.82);
  const bord = (u) => franc * (0.62 + 0.38 * Math.pow(Math.abs(u), 1.8));
  // Une rangée de points par couple : du fond (au milieu) jusqu'au plat-bord,
  // d'un bord à l'autre. `t` négatif = bâbord, positif = tribord.
  for (let s = 0; s < S; s++) {
    const u = (s / (S - 1)) * 2 - 1;
    const hb = (B / 2) * large(u), zf = fond(u), zb = bord(u);
    for (let k = -K; k <= K; k++) {
      const t = Math.abs(k) / K, sgn = Math.sign(k);
      pos.push(u * L / 2,
               sgn * hb * Math.pow(t, 0.72),
               zf + (zb - zf) * Math.pow(t, 1.55));
    }
  }
  const R = 2 * K + 1;
  for (let s = 0; s < S - 1; s++) for (let k = 0; k < R - 1; k++) {
    const a = s * R + k, b = a + R;
    idx.push(a, b, b + 1, a, b + 1, a + 1);
  }
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

/**
 * Une coque complète. `nef` : pontée, mâtée, avec son château arrière.
 * Sinon une barque de pêche : ouverte, ses bancs de nage, et rien d'autre.
 */
// Neuf nefs identiques, ce sont NEUF transformations d'une même carène — pas
// neuf carènes. Le lissage des couples est le seul calcul un peu dense du
// module ; on le fait deux fois par lieu, pas quatorze.
const _carenes = new Map();
function carenePartagee(L, B, tirant, franc) {
  const k = [L, B, tirant, franc].join(":");
  if (!_carenes.has(k)) _carenes.set(k, carene(L, B, tirant, franc));
  return _carenes.get(k);
}

// Et l'on va jusqu'au bout : neuf nefs identiques, c'est UN patron bâti une
// fois et cloné neuf. `clone()` de three partage les géométries ET les
// matériaux — on passe de cent douze géométries à une quinzaine, et le rendu
// de quatorze coques cesse de coûter cent vingt-quatre appels distincts.
const _patrons = new Map();
function patron(nef) {
  const k = nef ? "nef" : "barque";
  if (!_patrons.has(k)) {
    const G = nef ? GABARIT.nef : GABARIT.barque;
    _patrons.set(k, coque(G.L, G.B, G.tirant, G.franc, nef));
  }
  return _patrons.get(k).clone();
}

function coque(L, B, tirant, franc, nef) {
  const g = new T.Group();
  const bois = new T.MeshLambertMaterial({ color: BOIS, side: T.DoubleSide });
  g.add(new T.Mesh(carenePartagee(L, B, tirant, franc), bois));

  // La préceinte : le bourrelet qui court au plat-bord. Sans elle, la coque
  // n'a pas d'arête et la lumière n'y accroche nulle part.
  const pre = new T.Mesh(new T.TorusGeometry(1, 0.055, 3, 18, Math.PI * 2),
    new T.MeshLambertMaterial({ color: 0x4a3524 }));
  pre.scale.set(L * 0.47, B * 0.47, 1);
  pre.position.z = franc * 0.72;
  g.add(pre);

  if (!nef) {
    // Les bancs de nage : trois planches en travers, et l'on sait que c'est
    // une barque et pas une écuelle.
    for (let i = -1; i <= 1; i++) {
      const b = new T.Mesh(new T.BoxGeometry(0.16, B * 0.82, 0.05),
        new T.MeshLambertMaterial({ color: PONT }));
      b.position.set(i * L * 0.22, 0, franc * 0.55);
      g.add(b);
    }
    return g;
  }

  // Le pont, posé au franc-bord et bordé de la préceinte.
  const pont = new T.Mesh(new T.BoxGeometry(L * 0.80, B * 0.80, 0.09),
    new T.MeshLambertMaterial({ color: PONT }));
  pont.position.z = franc * 0.80;
  g.add(pont);
  // Le château arrière : ce qui distingue une nef d'une grosse barque, et ce
  // qu'on reconnaît de loin à la silhouette.
  const ch = new T.Mesh(new T.BoxGeometry(L * 0.17, B * 0.62, franc * 1.15),
    new T.MeshLambertMaterial({ color: 0x74593a }));
  ch.position.set(-L * 0.34, 0, franc * 1.35);
  g.add(ch);

  const h = L * 0.92;
  const bmat = new T.MeshLambertMaterial({ color: MAT });
  const m = new T.Mesh(new T.CylinderGeometry(B * 0.045, B * 0.07, h, 7), bmat);
  m.rotation.x = Math.PI / 2;
  m.position.set(L * 0.04, 0, franc * 0.8 + h / 2);
  g.add(m);
  // La vergue et sa voile FERLÉE : une rade au mouillage n'a pas de toile
  // dehors, et une voile pleine sans vent est un contresens.
  const vergue = new T.Mesh(new T.CylinderGeometry(0.07, 0.07, B * 1.35, 6), bmat);
  vergue.position.set(L * 0.04, 0, franc * 0.8 + h * 0.74);
  g.add(vergue);
  const ferlee = new T.Mesh(new T.CylinderGeometry(B * 0.11, B * 0.11, B * 1.12, 7),
    new T.MeshLambertMaterial({ color: VOILE }));
  ferlee.position.copy(vergue.position);
  ferlee.position.z -= 0.16;
  g.add(ferlee);
  // Deux haubans par bord : trois traits qui tiennent le mât et disent l'échelle.
  for (const s of [-1, 1]) for (const d of [-0.30, 0.22]) {
    const a = new T.Vector3(L * 0.04, 0, franc * 0.8 + h * 0.86);
    const b = new T.Vector3(L * 0.04 + d * L, s * B * 0.42, franc * 0.8);
    const len = a.distanceTo(b);
    const c = new T.Mesh(new T.CylinderGeometry(0.035, 0.035, len, 4), bmat);
    c.position.copy(a).lerp(b, 0.5);
    c.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0),
      b.clone().sub(a).normalize());
    g.add(c);
  }
  return g;
}

// Un hachage stable : deux mouillages ne se ressemblent pas, et pourtant la
// rade est la même à chaque image et d'une session à l'autre.
function melange(a, b) {
  let h = (a | 0) * 374761393 + (b | 0) * 668265263;
  h = (h ^ (h >>> 13)) * 1274126177;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

export function poser(scene, o = {}) {
  const relief = o.relief || null;
  let quai = (o.quai || []).slice();     // la polyligne du quai, en mètres
  const racine = new T.Group();
  racine.renderOrder = 995;
  scene.add(racine);

  let objets = [];
  let signature = "";
  let visible = true;

  const sol = (x, y) => (relief ? relief.sol(x, y) : 0);
  const eau = (x, y) => sol(x, y) <= 0.4;

  // On retire, on ne DÉTRUIT pas : géométries et matériaux appartiennent au
  // patron et sont partagés par tous ses clones. Les jeter ici viderait les
  // treize autres coques du même gabarit.
  function vider() {
    objets.forEach((o2) => racine.remove(o2.g));
    objets = [];
  }

  /** L'axe du quai, et sa normale vers le large. */
  function axe() {
    if (quai.length < 2) return null;
    const a = quai[0], b = quai[quai.length - 1];
    const cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
    const t = Math.atan2(b[1] - a[1], b[0] - a[0]);
    // Des deux perpendiculaires, celle qui mène à l'eau. On ne devine pas le
    // côté du large : on le CHERCHE, en regardant où le sol descend.
    for (const s of [1, -1]) {
      const n = t + s * Math.PI / 2;
      if (eau(cx + Math.cos(n) * 60, cy + Math.sin(n) * 60)) {
        return { cx, cy, t, n, L: Math.hypot(b[0] - a[0], b[1] - a[1]) };
      }
    }
    return { cx, cy, t, n: t - Math.PI / 2, L: Math.hypot(b[0] - a[0], b[1] - a[1]) };
  }

  /** Le premier point d'eau depuis la terre, sur ce cap. La ligne de rivage. */
  function rivage(x, y, n) {
    let dedans = 0, dehors = 400;
    for (let i = 0; i < 14; i++) {
      const d = (dedans + dehors) / 2;
      if (eau(x + Math.cos(n) * d, y + Math.sin(n) * d)) dehors = d; else dedans = d;
    }
    return dehors;
  }

  /**
   * Le SEC, en remontant depuis l'eau. Une barque tirée est sur le sable, pas
   * à la ligne d'eau : on recule vers la terre jusqu'à trouver du sol franc.
   * Chercher « un peu en deçà du rivage » ne suffit pas — quand le point de
   * départ est déjà sur l'eau, le décalage tombe à zéro et la barque flotte.
   */
  function echouage(x, y, n, recul) {
    let px = x, py = y;
    for (let d = 0; d <= 260; d += 4) {
      px = x - Math.cos(n) * d; py = y - Math.sin(n) * d;
      if (sol(px, py) > 0.8) {
        // trouvé le sable : on remonte encore un peu, l'étrave hors de l'eau
        const q = d + recul;
        return [x - Math.cos(n) * q, y - Math.sin(n) * q];
      }
    }
    return [px, py];
  }

  /**
   * `corps` : les entrées de genre `nef` de `/ville`. On y lit `cercles` (le
   * nombre de coques), `cap`, et le `detail` — qui dit si elles flottent.
   */
  function maj(corps) {
    const nefs = (corps || []).filter((c) => c && c.genre === "nef");
    const sig = nefs.map((c) => c.id + ":" + c.cercles + ":" + c.cap).join("|")
      + "@" + quai.length;
    if (sig === signature) return;
    signature = sig;
    vider();
    const A = axe();
    if (!A) return;

    nefs.forEach((c, k) => {
      const n = Math.max(1, c.cercles | 0);
      // « Tirées sur la grève », « au sec », « non à l'eau » : le detail du
      // croquis décide, parce que c'est un fait de la partie et non un hasard.
      const sec = /grève|greve|au sec|non à l'eau|non a l'eau|tirée|tiree/i
        .test(c.detail || "");
      const capNef = ((c.cap || 0) * Math.PI) / 180;
      for (let i = 0; i < n; i++) {
        const r1 = melange(k * 97 + i, 11), r2 = melange(k * 97 + i, 23);
        // Le long du quai d'abord, puis vers le large : une rade se remplit
        // en profondeur, pas en une file parallèle au bord.
        const le = (i / Math.max(1, n - 1) - 0.5) * A.L * (sec ? 0.9 : 1.7)
          + (r1 - 0.5) * 18;
        let x = A.cx + Math.cos(A.t) * le;
        let y = A.cy + Math.sin(A.t) * le;
        const bord = rivage(x, y, A.n);
        // Le z LOCAL d'une coque est sa flottaison. Au mouillage elle se pose
        // donc sur l'étale, et le tirant d'eau passe dessous tout seul ; tirée
        // au sec, c'est la QUILLE qui touche, et il faut la relever d'autant.
        const G = sec ? GABARIT.barque : GABARIT.nef;
        let z;
        if (sec) {
          // Une barque tirée est SUR le sable, l'étrave vers la terre, un peu
          // en deçà de la ligne d'eau — c'est ce qui se voit d'un village qui
          // ne pêche plus.
          const p = echouage(x, y, A.n, 3 + r2 * 7);
          x = p[0]; y = p[1];
          z = Math.max(ETALE, sol(x, y)) + G.tirant;
        } else {
          const d = bord + 45 + r2 * 190;
          x += Math.cos(A.n) * d; y += Math.sin(A.n) * d;
          if (!eau(x, y)) continue;          // jamais une coque sur le sec
          z = ETALE;
        }
        const g = patron(!sec);
        g.position.set(x, y, z);
        // Au mouillage, une coque évite au vent : elles ne sont pas parallèles
        // au cordeau, mais elles regardent toutes à peu près le même point.
        g.rotation.z = sec ? A.n + Math.PI + (r1 - 0.5) * 0.5
                           : capNef + (r1 - 0.5) * 0.6;
        g.traverse((m) => { m.renderOrder = 995; });
        racine.add(g);
        objets.push({ id: c.id + "#" + i, g, sec, nom: c.nom, z });
      }
    });
  }

  return {
    objet: racine,
    maj,
    /** Le quai vient de la voirie : on le repose quand on change de lieu. */
    situer(pts) { quai = (pts || []).slice(); signature = ""; },
    montrer(v) { visible = v; racine.visible = v; },
    /** Le roulis : lent, faible, et seulement pour ce qui flotte. */
    suivre(cam, t) {
      if (!visible) return;
      for (const o2 of objets) {
        const d = o2.g.position.distanceTo(cam.position);
        o2.g.visible = d < PORTEE;
        if (!o2.g.visible || o2.sec) continue;
        const p = (t || 0) * 0.6 + o2.g.position.x * 0.05;
        o2.g.rotation.x = Math.sin(p) * 0.035;
        o2.g.position.z = o2.z + Math.sin(p * 1.3) * 0.12;
      }
    },
    etat() {
      return objets.map((o2) => ({
        id: o2.id, nom: o2.nom, sec: o2.sec,
        xy: [Math.round(o2.g.position.x), Math.round(o2.g.position.y)],
        z: +o2.g.position.z.toFixed(2),
      }));
    },
    disposer() {
      vider();
      scene.remove(racine);
      // Les carènes sont partagées : elles ne se jettent pas avec un objet,
      // elles se jettent avec le module.
      _patrons.forEach((p) => p.traverse((m) => {
        if (m.geometry) m.geometry.dispose();
        if (m.material) m.material.dispose();
      }));
      _patrons.clear();
      _carenes.forEach((g) => g.dispose());
      _carenes.clear();
    },
  };
}
