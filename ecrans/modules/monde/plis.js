// monde/plis.js — ce qui part par écrit : le corbeau qu'on lâche, le cavalier
// qui franchit la porte, la lettre scellée qu'on vient de remettre.
//
// `CLAUDE.md` en fait une discipline de jeu : « la cire, le sceau, le parchemin
// qu'on plie, la porte qui se referme, le corbeau qu'on lâche depuis la
// roukerie. Le joueur doit sentir que sa parole devient un objet qui voyage. »
// L'objet existait dans l'état — cinquante-six plis, vingt-trois en route — et
// nulle part ailleurs. La table de guerre en portait douze jetons ; le volume,
// rien.
//
// ── CE QU'ON NE FAIT PAS, ET POURQUOI ────────────────────────────────────────
// On ne simule PAS la position vraie du porteur. Un corbeau vole à soixante
// kilomètres-heure : il traverse les cinq kilomètres du terrain en cinq minutes
// de jeu. Interpoler sa vraie place entre `parti_le` et `attendu_le` reviendrait
// à ne jamais rien montrer — sur douze jours de vol vers Winterfell, onze jours
// et vingt-trois heures se passent au-dessus de la mer, hors du fichier.
//
// Ce qui a de la valeur, ce n'est pas le milieu du voyage : c'est le DÉPART et
// l'ARRIVÉE. Un corbeau qui se pose pendant un conseil est une interruption
// diégétique ; un corbeau au-dessus du détroit n'est rien. Un pli paraît donc
// ici le jour où il part de ce lieu, ou le jour où on l'y attend — et il s'en
// va sur son CAP VRAI, celui que `Geo.lieux` donne entre les deux places.
//
// ── LE CAP ───────────────────────────────────────────────────────────────────
// La carte de Westeros (`ecrans/modules/geo.js`, engendrée) porte les dix-neuf
// places avec leur point. Le cap se calcule de l'origine vers la destination et
// vaut dans le monde en mètres : un corbeau pour Villevieille part au sud-ouest,
// un corbeau pour Winterfell part au nord-est, et l'on peut le vérifier à l'œil
// sur la table peinte. Sur la carte, y descend vers le sud ; dans le monde, y
// monte vers le nord — d'où le signe.
"use strict";
import * as T from "/vendor/three.module.min.js";

const PORTEE = 1200;      // au-delà, un oiseau n'est plus qu'un point : on l'éteint
const MONTEE = 55;        // ce qu'un corbeau prend de hauteur avant de filer
const FUITE = 900;        // la distance sur laquelle il s'éloigne et se dissout

// La cire dit le camp autant que le sceau : on ne mélange pas un pli de la
// reine et un pli qu'on a intercepté.
const CIRE = { defaut: 0x8f2d2a, retenu: 0x6b6b6b, remis: 0x7a4a2c };
const PLUME = 0x14141a;   // le corbeau : noir bleuté, jamais noir pur
const CUIR = 0x5a4630;    // la sacoche du cavalier

/** Le cap de `a` vers `b`, en radians dans le repère du monde. */
export function cap(a, b) {
  const G = window.Geo && window.Geo.lieux;
  if (!G || !G[a] || !G[b]) return null;
  const p = G[a], q = G[b];
  const px = p.p ? p.p[0] : p[0], py = p.p ? p.p[1] : p[1];
  const qx = q.p ? q.p[0] : q[0], qy = q.p ? q.p[1] : q[1];
  if (qx === px && qy === py) return null;
  // y de la carte descend vers le sud ; y du monde monte vers le nord.
  return Math.atan2(-(qy - py), qx - px);
}

const jour = (d) => d ? (d.annee * 10000 + d.lune * 100 + d.jour) : null;

/**
 * Ce que ce lieu a d'un pli aujourd'hui : "part", "arrive", "pose", ou rien.
 * `ici` est l'id de lieu (peyredragon, port-real…), `aujourdhui` la date monde.
 */
export function role(p, ici, aujourdhui) {
  const t = jour(aujourdhui);
  if (p.etat === "remis") return p.vers === ici ? "pose" : null;
  if (p.etat === "retenu") return p.de_lieu === ici ? "pose" : null;
  if (jour(p.parti_le) === t && p.de_lieu === ici) return "part";
  if (jour(p.attendu_le) === t && p.vers === ici) return "arrive";
  return null;
}

export function poser(scene, o = {}) {
  const relief = o.relief || null;
  let ici = o.lieu || null;
  let date = o.date || null;
  // D'où part ce qui part : la roukerie pour un corbeau, la porte pour un
  // cavalier, le quai pour une barque. Trois adresses, données par l'appelant
  // parce que lui seul lit les intérieurs du lieu.
  let quais = Object.assign({ corbeau: null, cavalier: null, barque: null }, o.depuis || {});

  const racine = new T.Group();
  racine.renderOrder = 996;
  scene.add(racine);

  const gLettre = new T.BoxGeometry(0.30, 0.21, 0.012);
  const gSceau = new T.CylinderGeometry(0.035, 0.035, 0.008, 10);
  gSceau.rotateX(Math.PI / 2);
  const gCorps = new T.SphereGeometry(0.19, 8, 6);
  const gAile = new T.BoxGeometry(0.62, 0.10, 0.02);

  let objets = [];
  let signature = "";
  let visible = true;

  const sol = (x, y) => Math.max(0, relief ? relief.sol(x, y) : 0);

  function vider() {
    objets.forEach((o2) => {
      racine.remove(o2.g);
      o2.g.traverse((m) => { if (m.material) m.material.dispose(); });
    });
    objets = [];
  }

  function lettre(etat) {
    const g = new T.Group();
    g.add(new T.Mesh(gLettre, new T.MeshLambertMaterial({ color: 0xd9cfb4 })));
    const s = new T.Mesh(gSceau, new T.MeshLambertMaterial({
      color: CIRE[etat] || CIRE.defaut,
    }));
    s.position.set(0.08, 0, 0.010);
    g.add(s);
    return g;
  }

  function corbeau() {
    const g = new T.Group();
    const m = new T.MeshLambertMaterial({ color: PLUME });
    g.add(new T.Mesh(gCorps, m));
    const a1 = new T.Mesh(gAile, m); a1.position.set(0, 0.16, 0.04);
    const a2 = new T.Mesh(gAile, m); a2.position.set(0, -0.16, 0.04);
    a1.rotation.x = -0.5; a2.rotation.x = 0.5;
    g.add(a1, a2);
    g.userData.ailes = [a1, a2];
    return g;
  }

  function cavalier() {
    const g = new T.Group();
    const m = new T.MeshLambertMaterial({ color: CUIR });
    const sac = new T.Mesh(new T.BoxGeometry(0.42, 0.26, 0.30), m);
    sac.position.z = 1.0;
    g.add(sac, lettre("defaut"));
    return g;
  }

  function maj(plis) {
    const liste = (plis || []).filter((p) => p && p.id);
    const retenus = [];
    for (const p of liste) {
      const r = role(p, ici, date);
      if (r) retenus.push([p, r]);
    }
    const sig = retenus.map(([p, r]) => p.id + ":" + r).join("|")
      + "@" + JSON.stringify(quais) + "@" + jour(date);
    if (sig === signature) return;
    signature = sig;
    vider();

    retenus.forEach(([p, r], n) => {
      const canal = p.canal === "cavalier" || p.canal === "barque" ? p.canal : "corbeau";
      const depart = quais[canal] || quais.corbeau;
      if (!depart && r !== "pose") return;

      let g, x, y, z, a = 0;
      if (r === "pose") {
        // Une lettre remise se pose là où elle est arrivée. Pas de mise en
        // scène : à plat, décalée de ses voisines, sur la table de la pièce.
        const base = quais.pose || depart;
        if (!base) return;
        const t = 2.399 * n, rr = 0.5 + (n % 4) * 0.16;
        x = base[0] + Math.cos(t) * rr; y = base[1] + Math.sin(t) * rr;
        z = (base[2] || sol(x, y)) + 0.79 + (n % 3) * 0.014;
        g = lettre(p.etat);
        g.rotation.z = (p.id.charCodeAt(0) % 40) / 40 * Math.PI;
      } else {
        const b = cap(r === "part" ? (p.de_lieu || ici) : p.vers,
                      r === "part" ? p.vers : (p.de_lieu || ici));
        // Sans cap connu, on ne devine pas : l'oiseau part vers le large plutôt
        // que vers une direction inventée.
        a = b === null ? Math.PI : b;
        // « part » s'éloigne, « arrive » se rapproche : même axe, sens inverse.
        const d = r === "part" ? FUITE * 0.45 : -FUITE * 0.45;
        x = depart[0] + Math.cos(a) * d;
        y = depart[1] + Math.sin(a) * d;
        if (canal === "corbeau") {
          z = (depart[2] || sol(x, y)) + MONTEE;
          g = corbeau();
        } else {
          z = sol(x, y) + (canal === "barque" ? 0.4 : 0);
          g = cavalier();
        }
        g.rotation.z = a + (r === "arrive" ? Math.PI : 0);
      }
      g.position.set(x, y, z);
      g.traverse((m) => { m.renderOrder = 996; });
      racine.add(g);
      objets.push({
        id: p.id, g, role: r, canal, vers: p.vers, de: p.de_lieu,
        cap: a, base: depart, scelle: !!p.scelle,
      });
    });
  }

  let phase = 0;
  return {
    objet: racine,
    maj,
    /** Le monde a changé de lieu, de jour, ou la pièce d'adresses. */
    situer(o2 = {}) {
      if (o2.lieu !== undefined) ici = o2.lieu;
      if (o2.date !== undefined) date = o2.date;
      if (o2.depuis) quais = Object.assign(quais, o2.depuis);
      signature = "";
    },
    montrer(v) { visible = v; racine.visible = v; },
    /** Un battement d'ailes, et la taille bornée — comme les acteurs. */
    suivre(cam, dt) {
      if (!visible) return;
      phase += (dt || 0.016) * 9;
      for (const o2 of objets) {
        const d = o2.g.position.distanceTo(cam.position);
        o2.g.visible = d < PORTEE;
        if (!o2.g.visible) continue;
        o2.g.scale.setScalar(Math.max(1, Math.min(6, d / 30)));
        const ailes = o2.g.userData.ailes;
        if (ailes) {
          const b = Math.sin(phase + o2.cap) * 0.55;
          ailes[0].rotation.x = -0.5 + b;
          ailes[1].rotation.x = 0.5 - b;
        }
      }
    },
    /** Ce qui est en l'air ou sur la table — pour le dire, et pour vérifier. */
    etat() {
      return objets.map((o2) => ({
        id: o2.id, role: o2.role, canal: o2.canal, vers: o2.vers,
        cap: o2.cap === null ? null : Math.round(o2.cap * 180 / Math.PI),
      }));
    },
    disposer() {
      vider();
      scene.remove(racine);
      [gLettre, gSceau, gCorps, gAile].forEach((g) => g.dispose());
    },
  };
}
