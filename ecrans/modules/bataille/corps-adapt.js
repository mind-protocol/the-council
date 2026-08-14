// corps-adapt.js — la prise entre la bataille et la couche 1.
//
// ELLE NE CONDUIT RIEN, ET C'EST LE POINT DE CETTE PREMIÈRE PASSE. La couche 1
// (`survival-stack/1-corps.js`) tourne pour chaque homme, à côté de la cascade
// de `soldat()`, et se fait mesurer — sans qu'aucun de ses gestes ne remplace
// quoi que ce soit. Le drapeau `pilote` existe et vaut `false`.
//
// POURQUOI EN DEUX TEMPS. Le grégarisme est une BOUCLE DE RÉTROACTION POSITIVE :
// la peur d'un homme monte celle de son voisin, qui monte la sienne. Rien dans
// le modèle n'empêche la divergence, et ça n'a jamais tourné qu'avec des voisins
// que le banc fabriquait — deux, trois, jamais deux mille cinq cents qui se
// lisent mutuellement. Si ça s'emballe, on veut le voir sur un relevé, pas sur
// une bataille qu'on aura cassée en même temps.
//
// CE QU'ELLE FAIT, ET RIEN D'AUTRE :
//   elle construit les VOISINS — des formes autour, avec ce qu'elles montrent ;
//   elle construit les SIGNAUX — à partir de champs que la bataille tient déjà ;
//   elle appelle `Corps.pas()` au rythme de l'ŒIL de l'homme, pas à 20 Hz ;
//   elle range le résultat dans `h.l1`, que personne ne consomme encore.
"use strict";
(() => {

  const C = (typeof window !== "undefined" && window.Corps)
    || (typeof require !== "undefined" && require("../survival-stack/1-corps.js"));

  // ON NE FAIT PAS TOURNER 2 550 CERVEAUX VINGT FOIS PAR SECONDE. La bataille a
  // déjà la bonne horloge pour ça : `oeil()`, le temps qu'un homme met à
  // s'apercevoir de quelque chose — de 0,1 à 3 s, individuel, ralenti par la
  // fatigue. La couche s'y branche, et reçoit le `dt` accumulé depuis son
  // dernier passage : les constantes de temps (montée, descente, habituation)
  // sont des exponentielles, donc elles supportent un pas variable sans dériver.
  //
  // Ce qui NE supporte pas le pas variable, ce sont les stimuli : un coup reçu
  // entre deux coups d'œil doit quand même être vu. Ils s'accumulent donc dans
  // `h.recu`, et c'est la boîte aux lettres qui les garde jusqu'au réveil.
  const RAYON_VOISINS = 4.5;      // mètres : de quoi tenir un rang, pas une aile

  /** L'angle de `o` vu depuis `h`, RELATIF à son cap tenu. */
  function relatif(h, o) {
    const a = Math.atan2(o.y - h.y, o.x - h.x);
    const cap = (h.fx || h.fy) ? Math.atan2(h.fy, h.fx) : 0;
    let d = a - cap;
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    return d;
  }

  /**
   * @param h      l'homme de `bataille2d`
   * @param ctx    { autour, temps, nuit, degatTypique, pese }
   * @param dt     secondes depuis son dernier passage ici
   */
  function observer(h, ctx, dt) {
    const voisins = [], proches = [];
    ctx.autour(h.x, h.y, RAYON_VOISINS, (o) => {
      if (o === h || !ctx.pese(o)) return;
      const d = Math.hypot(o.x - h.x, o.y - h.y);
      if (d > RAYON_VOISINS) return;
      const ami = o.camp === h.camp;
      if (ami) {
        // CE QU'UNE FORME MONTRE, ET RIEN DE PLUS. Pas son camp nominal, pas son
        // rang, pas sa peur : son geste, son cap, et depuis quand il le tient.
        // `h.branche` de la bataille n'est pas un geste de la couche 1 — on ne
        // traduit donc PAS, on prend l'état de la couche s'il en a un, sinon on
        // laisse vide et le voisin ne pèse que par sa présence.
        const l = o.l1;
        voisins.push({
          angle: relatif(h, o), distance: d, ami: true,
          jambes: l ? l.jambes : null, bras: l ? l.bras : null,
          cap: (o.fx || o.fy) ? relatif(h, { x: o.x + o.fx, y: o.y + o.fy }) : null,
          depuis: l ? Math.max(0, ctx.temps - (l.depuis || 0)) : 99,
        });
      } else {
        voisins.push({ angle: relatif(h, o), distance: d, ami: false });
        proches.push({ distance: d, deFace: Math.cos(relatif(h, o)),
                       frappe: o.etat === "melee" || o.etat === "assaut" });
      }
    });

    const pvMax = h.pvMax || 25;
    const signaux = {
      integrite: C.integrite(Math.max(0, h.pv), ctx.degatTypique),
      souffle:   C.souffle(h.souffle == null ? 1 : h.souffle),
      menace:    C.menace(proches),
      // L'ISSUE N'EST PAS MODÉLISÉE DANS LA BATAILLE, et il faut le dire plutôt
      // que d'inventer. Il n'existe nulle part de « part de mon arrière qui est
      // libre » : ni mur, ni cul-de-sac, ni presse orientée. On prend donc la
      // presse comme approximation — être serré, c'est ne pas pouvoir reculer —
      // et l'on note que c'est le signal le plus faible des cinq tant que la
      // géométrie ne le donnera pas pour de bon.
      issue:     C.issue(Math.max(0, 1 - (h.presse || 0) / 6)),
      // ⚠ `proches` N'EST PAS TRIE — il sort de la grille de voisinage, dans
      // l'ordre ou elle balaie. Prendre `[0]` revenait a tester un ennemi
      // au hasard, pas le plus proche.
      aPortee:   proches.some((x) => x.distance <= 2.2),
      ennemisProches: proches.length,
    };

    if (!h.l1etat) h.l1etat = { dressage: h.dressage == null ? 0 : h.dressage,
                              vecu: h.vecu == null ? 0 : h.vecu };
    const r = C.pas(h.l1etat, {
      t: ctx.temps, dt, stimuli: h.recu || [], signaux, voisins,
      nuit: !!ctx.nuit, presse: h.presse || 0,
    }, Math.random());

    // La boîte aux lettres se vide une fois lue : un coup ne se sent qu'une fois.
    if (h.recu && h.recu.length) h.recu.length = 0;

    // `depuis` : l'instant du dernier changement de geste, pour que les VOISINS
    // sachent qui vient de bouger. C'est l'entrée de l'initiateur, et elle ne
    // peut se tenir qu'ici — un homme ne sait pas lui-même depuis quand il fait
    // ce qu'il fait, mais celui qui le regarde, si.
    const avant = h.l1;
    r.depuis = (avant && avant.jambes === r.jambes && avant.bras === r.bras)
      ? (avant.depuis || ctx.temps) : ctx.temps;
    h.l1 = r;
    return r;
  }

  const API = { observer, RAYON_VOISINS, pilote: false };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.BatailleCorps = API;
})();
