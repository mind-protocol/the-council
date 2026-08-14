// banc-reflexion-adapt.js — l'épreuve du Bassin pour `reflexion-adapt.js`.
//
// CE QU'ON ÉPROUVE ICI N'EST PAS LA COUCHE — elle a son propre banc — MAIS LA
// PRISE : ce que le pourvoyeur fait dire à la bataille. Un signal dont le signe
// est inversé passe tous les tests de la couche et rend un homme qui recule
// quand il devrait tenir. C'est la faute que ce fichier cherche.
//
//   node ecrans/modules/bataille/banc-reflexion-adapt.js
"use strict";
const path = require("path");
globalThis.window = globalThis;
require(path.join(__dirname, "..", "survival-stack", "2-reflexion.js"));
require(path.join(__dirname, "..", "survival-stack", "5-qui-conduit.js"));
const A = require("./reflexion-adapt.js");

let ok = 0, ko = 0;
function dit(nom, cond, quoi) {
  if (cond) { ok++; console.log("  ok  " + nom + "\n        " + quoi); }
  else { ko++; console.log("  KO  " + nom + "\n        " + quoi); }
}

/** Un homme nu, et le monde autour de lui. */
function homme(o) {
  return Object.assign({
    x: 0, y: 0, fx: 1, fy: 0, camp: "assaut", etat: "melee",
    pv: 25, pvMax: 25, souffle: 1, trempe: 0, presse: 0,
    l1: null, l2: null, l2etat: null, l3: null, l4: 0,
    conduit: null, conduitEtat: null,
  }, o || {});
}

/** `ctx` : un monde plat, une liste de formes, et un mur qu'on pose où l'on veut.
 *  `mur` est un prédicat sur (x, y) — vrai = sous un toit. `null` = pas de
 *  masque du tout, ce que le four sans serveur donne. */
function monde(formes, mur) {
  return {
    temps: 100,
    autour: (x, y, r, f) => formes.forEach(f),
    pese: (o) => o.etat !== "mort" && o.etat !== "blesse",
    // `undefined` = un sol sans une maison ; `null` = pas de masque du tout.
    libre: mur === null ? null : (x, y) => !(mur ? mur(x, y) : false),
  };
}

const F = (n, camp, x, y, o) => Array.from({ length: n }, (_, i) =>
  Object.assign({ camp, x: x + i * 0.8, y, etat: "melee", recule: false }, o || {}));

console.log("\n  LA PRISE DE LA COUCHE 2 — " + new Date(0).toISOString().slice(0, 0)
  + "onze signaux bâtis depuis la bataille\n");

// ── 1. LE SOL DERRIÈRE LUI ───────────────────────────────────────────────────
{
  const h = homme();
  A.observer(h, monde(F(3, "garde", 2, 0)), 0.5);
  dit("rase campagne : la retraite est ouverte",
      h.l2.degage > 0.9,
      "degage " + h.l2.degage.toFixed(2) + "  tient " + h.l2.tient.toFixed(2));
}
{
  // Le mur commence à 1 m derrière lui (x < −1), les ennemis sont devant.
  const h = homme();
  A.observer(h, monde(F(3, "garde", 2, 0), (x) => x < -1), 0.5);
  dit("dos au mur : il est acculé, et il tient à cause de ça",
      h.l2.degage < -0.9 && h.l2.tient > 0,
      "degage " + h.l2.degage.toFixed(2) + "  tient " + h.l2.tient.toFixed(2)
      + "  — « " + h.l2.idee + " »");
}
{
  // La même scène sans masque : on ne sait pas, donc on ne promet rien.
  const h = homme();
  A.observer(h, monde(F(3, "garde", 2, 0), null), 0.5);
  dit("sans masque du bâti : « on ne sait pas », jamais « c'est libre »",
      h.l2.degage === 0,
      "degage " + h.l2.degage.toFixed(2));
}
{
  // Ni mur ni presse ne suffit : c'est la PIRE des deux qui compte.
  const h = homme({ presse: 6 });
  A.observer(h, monde(F(3, "garde", 2, 0)), 0.5);
  dit("la presse acculle aussi bien qu'un mur",
      h.l2.degage < -0.9,
      "degage " + h.l2.degage.toFixed(2) + "  (sol libre, presse 6)");
}

// ── 2. LE NOMBRE, L'ÉPAULE, CE QUE FONT LES SIENS ────────────────────────────
{
  const h = homme();
  const seul = A.observer(h, monde(F(6, "garde", 2, 0)), 0.5);
  const h2 = homme();
  const tenu = A.observer(h2, monde(F(6, "assaut", -2, 0).concat(F(2, "garde", 2, 0))), 0.5);
  dit("seul contre six, il cède ; six contre deux, il tient",
      seul.tient < -0.3 && tenu.tient > 0.3,
      "tient " + seul.tient.toFixed(2) + " contre " + tenu.tient.toFixed(2));
}
{
  const proche = homme(); A.observer(proche, monde(F(1, "assaut", 1, 0)), 0.5);
  const loin = homme(); A.observer(loin, monde(F(1, "assaut", 9, 0)), 0.5);
  dit("l'épaule se sent à un mètre et plus à neuf",
      proche.l2.appui !== loin.l2.appui,
      "appui " + proche.l2.appui.toFixed(2) + " contre " + loin.l2.appui.toFixed(2));
}
{
  // Les siens reculent tous autour de lui : la contagion doit passer.
  const tiennent = homme();
  A.observer(tiennent, monde(F(4, "assaut", -2, 0).concat(F(4, "garde", 2, 0))), 0.5);
  const lachent = homme();
  A.observer(lachent, monde(F(4, "assaut", -2, 0, { recule: true })
                             .concat(F(4, "garde", 2, 0))), 0.5);
  dit("les siens qui reculent le font céder, à compte égal",
      lachent.l2.tient < tiennent.l2.tient - 0.2,
      "tient " + tiennent.l2.tient.toFixed(2) + " → " + lachent.l2.tient.toFixed(2));
}

// ── 3. LES DEUX CAPS ─────────────────────────────────────────────────────────
{
  // Ennemi à l'est, les siens à l'ouest, sol libre : il doit sortir vers l'ouest.
  const h = homme();
  A.observer(h, monde(F(1, "garde", 4, 0).concat(F(3, "assaut", -4, 0))), 0.5);
  dit("l'issue part du fer et va vers les siens",
      h.l2.issue.x < -0.5 && h.l2.issue.force > 0,
      "issue (" + h.l2.issue.x.toFixed(2) + ", " + h.l2.issue.y.toFixed(2)
      + ")  force " + h.l2.issue.force.toFixed(2));
}

// ── 4. LES DEUX MÉMOIRES QUE LA COUCHE NE TIENT PAS ──────────────────────────
{
  // L'horloge d'attente : en infériorité, intact et calme, il attend — et
  // l'attente s'épuise. Cinq secondes plus tard, il doit entrer.
  // À SEPT MÈTRES IL N'ATTENDAIT PAS, ET LE BANC A EU RAISON DE LE DIRE : au-delà
  // du cercle de compte, quatre ennemis ne sont pas une infériorité — `nombre`
  // reste favorable, et un homme qui a le nombre pour lui n'attend rien. Il en
  // faut trois DANS le cercle, et pas encore au fer : c'est exactement la scène
  // où un homme laisse venir, et il a fallu la poser juste pour la voir.
  const h = homme({ etat: "assaut" });
  const scene = monde(F(4, "garde", 3, 0, { etat: "colonne" }));
  const a = A.observer(h, scene, 0.5);
  for (let i = 0; i < 12; i++) A.observer(h, scene, 0.5);
  // ET ON REGARDE LA DENT DE SCIE : douze battements plus tard, l'attente doit
  // etre EPUISEE et le rester, pas rebondir parce que la couche a change d'avis.
  const b = A.observer(h, scene, 0.5).attend;
  A.observer(h, scene, 0.5);
  dit("l'horloge d'attente s'épuise, et c'est ce fichier qui la tient",
      a.attend > 0.2 && b < a.attend - 0.2 && Math.abs(h.l2.attend - b) < 0.05,
      "attend " + a.attend.toFixed(2) + " → " + b.toFixed(2) + " → "
      + h.l2.attend.toFixed(2) + "  (sans dent de scie, "
      + h.l2etat.attendDepuis.toFixed(1) + " s d'attente)");
}
{
  // L'hystérésis : `deja` sort de sa propre sortie d'avant, PAS de `h.recule`.
  const h = homme();
  const scene = monde(F(5, "garde", 2, 0));
  const un = A.observer(h, scene, 0.5).tient;
  const deux = A.observer(h, scene, 0.5).tient;
  dit("l'hystérésis est dans la couche, pas dans `h.recule`",
      deux < un && h.recule === undefined,
      "tient " + un.toFixed(2) + " → " + deux.toFixed(2)
      + "  (h.recule jamais lu : " + (h.recule === undefined) + ")");
}

// ── 5. LA TRACE ──────────────────────────────────────────────────────────────
{
  const h = homme({ presse: 0 });
  A.observer(h, monde(F(5, "garde", 2, 0)), 0.5);
  dit("la trace est posée, et c'est un mot d'un répertoire fermé",
      ["corps", "reflexion", "envie", "ordre"].indexOf(h.conduit) >= 0,
      "conduit « " + h.conduit + " » depuis " + h.conduitDepuis
      + "  — « " + h.conduitPhrase + " »");
}
{
  // ET LE POINT DE TOUTE LA PASSE : rien de ce qui conduit n'a bougé.
  const h = homme();
  const avant = JSON.stringify({ etat: h.etat, x: h.x, y: h.y, pv: h.pv,
                                 cible: h.cible, recule: h.recule });
  A.observer(h, monde(F(5, "garde", 2, 0)), 0.5);
  const apres = JSON.stringify({ etat: h.etat, x: h.x, y: h.y, pv: h.pv,
                                 cible: h.cible, recule: h.recule });
  dit("le pourvoyeur ne conduit RIEN : ni état, ni position, ni cible",
      avant === apres, avant);
}

console.log("\n  " + (ko ? "✗ " + ko + " cas tombés sur " + (ok + ko)
                          : "✓ " + ok + " cas, tous tenus") + "\n");
process.exit(ko ? 1 : 0);
