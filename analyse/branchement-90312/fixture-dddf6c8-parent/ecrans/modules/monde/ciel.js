// monde/ciel.js — l'air, et c'est lui qui vend les kilomètres.
//
// Une ville de cinq kilomètres rendue sans atmosphère ressemble à une maquette
// de trente centimètres : tout y est net, donc tout y est proche. Ce qui donne
// l'échelle n'est pas la géométrie, c'est la PERTE — la brume qui blanchit les
// lointains, l'horizon qui se dissout, la mer qui prend la couleur du ciel.
//
// Trois pièces, et elles se tiennent :
//   1. une coupole dégradée du zénith à l'horizon (jamais un fond uni)
//   2. une brume EXPONENTIELLE, à la couleur exacte de l'horizon — sans quoi
//      la coupole et le lointain se décollent, et l'œil voit la triche
//   3. le ciel en carte d'environnement : la mer réfléchit alors la coupole,
//      et l'eau cesse d'être une nappe de peinture bleue
"use strict";
import * as T from "/vendor/three.module.min.js";
import { CIEL } from "/modules/monde/palette.js";

// La coupole : un dégradé vertical, rendu par l'intérieur. Elle est immense
// (rayon 400 km) et sans profondeur — elle se contente d'être le fond du monde.
// `sortie` : une ShaderMaterial n'est PAS convertie toute seule — ni la
// courbe de tons, ni l'espace de couleur. Sans ces deux chunks, le ciel sort
// en valeurs linéaires prises pour du sRGB : sombre, verdâtre, et décollé du
// reste de l'image. La coupole qui sert de carte d'environnement, elle, doit
// rester linéaire — d'où le drapeau.
function coupole(rayon = 400000, sortie = true) {
  const mat = new T.ShaderMaterial({
    side: T.BackSide, depthWrite: false, fog: false,
    uniforms: {
      zenith: { value: new T.Color(CIEL.zenith) },
      horizon: { value: new T.Color(CIEL.horizon) },
      bas: { value: new T.Color(CIEL.bas) },
    },
    vertexShader: `
      varying vec3 vP;
      void main() {
        vP = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      uniform vec3 zenith, horizon, bas;
      varying vec3 vP;
      void main() {
        float h = normalize(vP).z;                 // z est le haut, ici
        vec3 c = h > 0.0
          ? mix(horizon, zenith, pow(clamp(h, 0.0, 1.0), 0.42))
          : mix(horizon, bas, pow(clamp(-h, 0.0, 1.0), 0.55));
        gl_FragColor = vec4(c, 1.0);
        ${sortie ? "#include <tonemapping_fragment>\n#include <colorspace_fragment>" : ""}
      }`,
  });
  const m = new T.Mesh(new T.SphereGeometry(rayon, 32, 20), mat);
  m.frustumCulled = false;
  m.renderOrder = -1;
  return m;
}

// Le soleil de scripts/monde/batir.py : 52° d'inclinaison, 212° de lacet. La
// même lumière que les rendus de monde/rendus/, pour qu'on compare ce qui se
// compare — et le point de départ, avant que l'heure ne le déplace.
function soleil(distance = 6000) {
  const incl = T.MathUtils.degToRad(52), lacet = T.MathUtils.degToRad(212);
  const l = new T.DirectionalLight(CIEL.soleil, 2.5);
  l.position.set(
    Math.sin(incl) * Math.sin(lacet) * -distance,
    Math.sin(incl) * Math.cos(lacet) * distance,
    Math.cos(incl) * distance);
  return l;
}

// ── L'HEURE DANS LA LUMIÈRE ──────────────────────────────────────────────────
// La foule bougeait avec l'horloge de la partie et la lumière ne bougeait pas :
// il était midi pour toujours pendant que six cents personnes rentraient se
// coucher. Or l'heure est un objet de premier plan du jeu — le joueur la lit au
// chiffre près dans son bandeau, et `monde.date.minute` la tient à la minute.
// Elle doit se lire dans le volume SANS QU'ON AIT À LA DIRE : c'est le seul
// renseignement qu'un décor donne gratuitement, et le plus continu.
//
// Le modèle est simple et assumé : une course de soleil du levant au ponant,
// midi au sud et haut. On ne fait pas d'astronomie — pas de déclinaison, pas de
// saison, pas de latitude. Ce qu'on veut, c'est qu'un joueur qui ouvre l'onglet
// sache s'il est tôt ou tard avant d'avoir lu quoi que ce soit.
const LEVER = 6 * 60, COUCHER = 19 * 60;      // en minutes, l'amplitude du jour

/** La position du soleil et la couleur de l'heure, pour une minute donnée. */
export function heureDuJour(minute) {
  const m = ((minute % 1440) + 1440) % 1440;
  const jour = m >= LEVER && m <= COUCHER;
  // `u` : 0 au lever, 1 au coucher. Hors du jour il court sous l'horizon, ce
  // qui donne la lune — même géométrie, autre couleur, autre force.
  const u = jour ? (m - LEVER) / (COUCHER - LEVER)
                 : ((m < LEVER ? m + 1440 : m) - COUCHER) / (1440 - (COUCHER - LEVER));
  // Le lacet va du levant (est) au ponant (ouest) en passant par le sud.
  const lacet = Math.PI * (u - 0.5);
  // La hauteur : un arc, nul aux extrémités. Sous l'horizon la nuit.
  const haut = Math.sin(Math.PI * u) * (jour ? 1 : -1);
  const incl = Math.max(-0.35, haut) * (jour ? 1.05 : 0.5);
  // Rasante et rousse au ras de l'horizon, blanche et forte au zénith. C'est
  // la couleur qui dit l'heure, plus encore que l'angle.
  const bas = Math.max(0, 1 - Math.max(0, haut) * 3.2);
  return { jour, u, lacet, incl, bas, haut };
}

function melerCouleur(a, b, t) {
  return new T.Color(a).lerp(new T.Color(b), t);
}

// `poser(scene, rendu)` — installe l'air. Rend de quoi le régler ensuite : la
// brume se desserre quand on descend dans une ruelle, et se resserre quand on
// prend de la hauteur.
export function poser(scene, rendu, opts = {}) {
  const dome = coupole(opts.rayon);
  scene.add(dome);

  scene.fog = new T.FogExp2(CIEL.horizon, opts.densite ?? CIEL.densite_brume);
  scene.background = null;                 // la coupole EST le fond

  const sol = soleil();
  scene.add(sol);
  const ambiance = new T.HemisphereLight(CIEL.ambiance_haut, CIEL.ambiance_bas, 1.05);
  scene.add(ambiance);

  // La carte d'environnement : on rend la coupole une fois dans un cube, et
  // l'eau a de quoi réfléchir. Cent lignes de moins qu'un ciel physique, et le
  // gain est le même là où ça compte.
  let env = null;
  if (rendu) {
    const pmrem = new T.PMREMGenerator(rendu);
    const ciel = new T.Scene();
    ciel.add(coupole(1000, false));
    env = pmrem.fromScene(ciel, 0, 1, 2000).texture;
    scene.environment = env;
    pmrem.dispose();
  }

  let minuteCourante = null;

  return {
    dome, soleil: sol, ambiance, env,
    // la brume suit la caméra : à hauteur d'homme dans une rue on veut voir le
    // bout de la rue, à mille mètres on veut voir la ville se noyer
    selonAltitude(z) {
      const t = Math.min(1, Math.max(0, (z - 60) / 1400));
      scene.fog.density = (opts.densite ?? CIEL.densite_brume) * (1 - t * 0.55);
    },
    /**
     * L'heure de la partie. Déplace le soleil, le colore, et met le ciel et la
     * brume au ton — trois choses qui doivent bouger ENSEMBLE, sinon on obtient
     * un couchant orange sous un ciel de midi.
     */
    heure(minute, distance = 6000) {
      if (minute == null || minute === minuteCourante) return;
      minuteCourante = minute;
      const h = heureDuJour(minute);
      // +x est le LEVANT et +y le nord. Le soleil se lève donc en +x, passe au
      // sud (−y) à midi, et se couche en −x. Le signe de x n'est pas cosmétique :
      // sans lui l'astre se lève au ponant, et toutes les ombres du matin
      // tombent du mauvais côté du château.
      sol.position.set(
        Math.cos(h.incl) * -Math.sin(h.lacet) * distance,
        Math.cos(h.incl) * -Math.cos(h.lacet) * distance,
        Math.sin(h.incl) * distance);
      // De jour : blanc au zénith, roux à l'horizon. De nuit : une lune froide
      // et faible, qui éclaire assez pour qu'on distingue les masses.
      if (h.jour) {
        sol.color.copy(melerCouleur(CIEL.soleil, 0xffb271, h.bas));
        sol.intensity = 0.55 + 1.95 * Math.max(0, h.haut);
      } else {
        sol.color.set(0x8fa6c8);
        sol.intensity = 0.28;
      }
      // L'ambiance porte la nuit : sans elle, tout ce que le soleil ne touche
      // pas devient noir et l'on ne voit plus une rue à trois heures.
      const nuit = h.jour ? Math.max(0, h.bas - 0.55) / 0.45 : 1;
      ambiance.intensity = 1.05 - 0.55 * nuit;
      ambiance.color.copy(melerCouleur(CIEL.ambiance_haut, 0x2b3448, nuit));
      ambiance.groundColor.copy(melerCouleur(CIEL.ambiance_bas, 0x171a22, nuit));
      // Le ciel et la brume au même ton : c'est la brume qu'on voit au loin, et
      // un horizon de midi derrière un soleil couchant se remarque tout de suite.
      const teinte = h.jour
        ? melerCouleur(CIEL.horizon, 0xd08a5c, h.bas * 0.75)
        : melerCouleur(CIEL.horizon, 0x141a2a, 0.85);
      scene.fog.color.copy(teinte);
      // La coupole n'est pas un matériau à couleur : c'est un dégradé à trois
      // uniformes. On les mène tous les trois, sinon le zénith reste bleu de
      // midi au-dessus d'un horizon qui s'éteint.
      const u = dome.material && dome.material.uniforms;
      if (u) {
        u.horizon.value.copy(teinte);
        u.zenith.value.copy(h.jour
          ? melerCouleur(CIEL.zenith, 0x3f5f8e, h.bas * 0.6)
          : melerCouleur(CIEL.zenith, 0x080c18, 0.9));
        u.bas.value.copy(h.jour
          ? melerCouleur(CIEL.bas, 0x9a6a4e, h.bas * 0.7)
          : melerCouleur(CIEL.bas, 0x0d1018, 0.9));
      }
      return h;
    },
  };
}
