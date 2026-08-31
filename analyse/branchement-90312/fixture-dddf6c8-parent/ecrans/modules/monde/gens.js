// monde/gens.js — les quatre cent mille corps, chargés par cellules de 250 m.
//
// CE MODULE NE DESSINE RIEN. Pas d'InstancedMesh, pas de géométrie, pas de
// matériau : c'est un chargeur, et le rendu viendra par-dessus. On sépare les
// deux parce que le coût de la foule n'est pas le même des deux côtés — ici
// c'est du réseau et de la mémoire, là-bas ce sera du budget d'images.
//
// Ce qu'il sert, ce n'est pas le JSON des corps (cent trente octets par âme,
// quarante-cinq mégaoctets pour la ville) mais son double dense : douze octets
// par corps, en structure de tableaux, servi par `/monde/gens/<i>-<j>.bin`.
// Les deux derniers champs — domicile et lieu de travail — ne servent pas à
// dessiner mais à FAIRE MARCHER : sans eux une silhouette ne sait pas d'où
// elle part (voir journee.js).
// Les vues typées se POSENT sur le tampon reçu (`new Uint16Array(buf, o, n)`)
// sans une seule recopie : charger une cellule ne coûte que son transfert.
//
// L'ordre du binaire est celui du tableau `gens` du JSON de la même cellule.
// Un index de rendu est donc une adresse : la silhouette n° 412 de la cellule
// 11-3 est le 412e corps de `monde/gens/11-3.json`, avec son nom et son métier.
"use strict";

// Un manifeste PAR LIEU, et pas un seul pour la session : le jeu sert
// désormais Port-Réal ET Peyredragon, et un cache à une seule case rendait le
// manifeste du premier lieu chargé à tous les suivants. Le symptôme est muet et
// coûteux : à Peyredragon on demandait les cellules de Port-Réal, on ramassait
// des 404, et la ville restait vide sans que rien ne se plaigne.
const _manifestes = new Map();   // source -> manifeste
const _enVol = new Map();        // source -> promesse en cours

/** Le manifeste d'un lieu — colonnes, rôles, maille, cellules. */
export async function manifeste(source = "/monde") {
  if (_manifestes.has(source)) return _manifestes.get(source);
  // La promesse est mise en cache pour que deux appels rapprochés ne demandent
  // pas deux fois le manifeste — mais on la RELÂCHE si elle échoue, sans quoi
  // un serveur qui redémarre pendant le chargement condamne le module pour
  // toute la session.
  if (!_enVol.has(source)) {
    _enVol.set(source, fetch(source + "/gens").then((r) => {
      if (!r.ok) throw new Error("manifeste des gens : " + r.status);
      return r.json();
    }).then((m) => { _manifestes.set(source, m); return m; })
      .catch((e) => { _enVol.delete(source); throw e; }));
  }
  return _enVol.get(source);
}

// Le cache : une entrée par cellule chargée, jetée quand elle sort du rayon.
// Rien de plus savant qu'une Map — le rayon fait neuf à vingt-cinq cellules,
// et une politique d'éviction fine coûterait plus qu'elle ne rendrait.
const _cache = new Map();

function decouper(clef, info, buf, roles_index) {
  const n = info.n;
  // Décalages : les cinq colonnes de uint16 d'abord, les deux de uint8
  // ensuite — l'ordre n'est pas cosmétique, il garde les uint16 alignés sur
  // deux octets, sans quoi la vue typée refuserait de se poser sur le tampon.
  const o = { x: 0, y: n * 2, z: n * 4, bat: n * 6, travail: n * 8,
              role: n * 10, age_sexe: n * 11 };
  return {
    clef, n, x0: info.x0, y0: info.y0, roles_index,
    x: new Uint16Array(buf, o.x, n),          // cm relatifs à x0
    y: new Uint16Array(buf, o.y, n),          // cm relatifs à y0
    z: new Uint16Array(buf, o.z, n),          // cm absolus
    bat: new Uint16Array(buf, o.bat, n),      // index du domicile
    travail: new Uint16Array(buf, o.travail, n),
    role: new Uint8Array(buf, o.role, n),     // index dans roles_index
    age_sexe: new Uint8Array(buf, o.age_sexe, n),
  };
}

/** L'âge d'un corps de la cellule (0..127). */
export const age = (c, k) => c.age_sexe[k] & 0x7f;
/** Vrai si c'est une femme — le huitième bit de l'âge. */
export const femme = (c, k) => (c.age_sexe[k] & 0x80) !== 0;
/** La position en MÈTRES dans le monde, pour poser une instance. */
export function position(c, k, out) {
  const p = out || {};
  p.x = c.x0 + c.x[k] / 100;
  p.y = c.y0 + c.y[k] / 100;
  p.z = c.z[k] / 100;
  return p;
}

async function charger(clef, source) {
  const m = await manifeste(source);
  const info = m.cellules[clef];
  if (!info) return null;
  const r = await fetch(source + "/gens/" + clef + ".bin");
  if (!r.ok) throw new Error("cellule " + clef + " : " + r.status);
  const buf = await r.arrayBuffer();
  return decouper(clef, info, buf, m.binaire.roles_index);
}

/**
 * Les cellules autour d'un point, en mètres. Charge ce qui manque, oublie ce
 * qui est sorti, et rend TOUTES les cellules du rayon — y compris celles qui
 * étaient déjà là. Appelable à chaque déplacement de caméra : ce qui n'a pas
 * bougé ne coûte rien.
 */
export async function autour(x, y, rayon_m, source = "/monde") {
  const m = await manifeste(source);
  const c = m.cellule_m;
  const i0 = Math.floor((x - rayon_m) / c), i1 = Math.floor((x + rayon_m) / c);
  const j0 = Math.floor((y - rayon_m) / c), j1 = Math.floor((y + rayon_m) / c);

  const voulues = new Set();
  const attentes = [];
  for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
    const cel = i + "-" + j;
    if (!m.cellules[cel]) continue;   // la mer, les champs : personne n'y loge
    // La clef de cache porte le LIEU : « 19-8 » n'est pas la même cellule à
    // Port-Réal et à Peyredragon.
    const clef = source + "|" + cel;
    voulues.add(clef);
    if (_cache.has(clef)) continue;
    // On inscrit la PROMESSE au cache, pas seulement son résultat : sans ça,
    // deux appels rapprochés demandent deux fois la même cellule au serveur.
    _cache.set(clef, charger(cel, source).catch((e) => {
      _cache.delete(clef);
      throw e;
    }));
  }
  for (const clef of voulues) attentes.push(_cache.get(clef));

  for (const clef of Array.from(_cache.keys()))
    if (!voulues.has(clef)) _cache.delete(clef);

  const lot = await Promise.all(attentes);
  return lot.filter(Boolean);
}

/** Vider le cache — changement de lieu, ou simple ménage. */
export function oublier() { _cache.clear(); }
