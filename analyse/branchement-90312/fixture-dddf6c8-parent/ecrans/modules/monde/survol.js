// monde/survol.js — ce qu'il y a sous le curseur, nommé.
//
// Une ville en volume est muette : quarante-huit mille toits, et rien qui dise
// lequel est la tannerie, lequel est l'entrepôt du quai, lequel est la taverne
// où le joueur a dormi. Les repères (reperes.js) nomment les monuments, les
// salles (salles.js) nomment le dedans — entre les deux, tout le tissu de la
// ville restait anonyme, alors que chaque volume PORTE son métier depuis qu'il
// a été semé (scripts/monde/usages.py). L'information existait ; personne ne
// pouvait la demander.
//
// Trois disciplines, et elles expliquent tout le fichier :
//  - **On ne montre QUE ce qu'on interroge.** Une seule étiquette, sous le
//    curseur, celle de la chose désignée. C'est la règle des repères, et pour la
//    même raison : cinquante noms posés en permanence font une légende, pas une
//    ville.
//  - **On ne vise pas soixante fois par seconde.** La boucle d'images appelle,
//    et l'on ne relève la chose désignée qu'au plus dix fois par seconde. Viser
//    est le seul calcul de ce module ; le faire à chaque image le rendrait cher
//    pour rien — l'œil ne lit pas plus vite que ça.
//  - **Le module ne sait RIEN du monde.** Il reçoit des sondes (« voici comment
//    on interroge le bâti », « voici les salles ») et n'en connaît que le
//    contrat : un rai entre, un `{t, signe, titre, role}` sort. C'est ce qui
//    permet à la partie d'ajouter les noms qu'ELLE a posés — la Gaffe, le
//    chantier du bout — sans que cette page ait à lire `etat/`.
"use strict";
import * as T from "/vendor/three.module.min.js";

const PAUSE = 90;     // millisecondes entre deux visées, au plus

export function poser(o = {}) {
  const hote = o.hote;
  const canevas = o.canevas;
  const cam = o.cam;
  const sondes = o.sondes || [];
  if (!hote || !canevas || !cam) return null;

  const el = document.createElement("div");
  el.className = "monde-survol";
  el.style.display = "none";
  hote.appendChild(el);

  const rai = new T.Raycaster();
  const ndc = new T.Vector2();
  let sx = -1e4, sy = -1e4;          // le curseur, en pixels du cadre
  let dedans = false, glisse = false, visible = true;
  let dernier = 0;
  let lg = 0, ht = 0;                // la taille de l'étiquette, relevée à froid
  let apposer = null;                // ce que la partie ajoute aux noms
  let dit = null;                    // ce qui est affiché, pour ne pas le refaire

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const bouger = (e) => {
    const r = canevas.getBoundingClientRect();
    sx = e.clientX - r.left; sy = e.clientY - r.top;
    dedans = true;
  };
  const partir = () => { dedans = false; };
  // Tant qu'on tourne autour de la ville, on regarde le monde bouger, pas un
  // nom : l'étiquette se tait et revient quand la main s'arrête.
  const prendre = () => { glisse = true; };
  const lacher = () => { glisse = false; };
  canevas.addEventListener("pointermove", bouger);
  canevas.addEventListener("pointerleave", partir);
  canevas.addEventListener("pointerdown", prendre);
  canevas.addEventListener("pointerup", lacher);
  canevas.addEventListener("pointercancel", lacher);

  function cacher() {
    if (dit !== null) { el.style.display = "none"; dit = null; }
  }

  function viser() {
    const w = canevas.clientWidth, h = canevas.clientHeight;
    if (!w || !h) return cacher();
    // À pied, souris capturée : on désigne ce qu'on REGARDE, c'est-à-dire le
    // milieu du cadre — il n'y a plus de curseur à suivre.
    const capturee = document.pointerLockElement === canevas;
    let px = sx, py = sy;
    if (capturee) { px = w / 2; py = h / 2; }
    else if (!dedans || glisse) return cacher();
    ndc.set(px / w * 2 - 1, -(py / h) * 2 + 1);
    rai.setFromCamera(ndc, cam);

    let elu = null;
    for (const s of sondes) {
      let t;
      try { t = s(rai); } catch (e) { t = null; }
      if (t && (!elu || t.t < elu.t)) elu = t;
    }
    if (apposer && elu) elu = apposer(elu) || elu;
    if (!elu || !elu.titre) return cacher();

    // Le signe de l'espèce vient avec le nom (signes.js). Il se pose EN TÊTE et
    // hors de la colonne du texte : on le lit avant le mot, et c'est tout son
    // office — reconnaître une forge d'une taverne en balayant la ville, sans
    // déchiffrer. Il dit l'espèce, jamais l'individu.
    const empreinte = (elu.signe || "") + " " + elu.titre
      + " " + (elu.role || "");
    if (empreinte !== dit) {
      dit = empreinte;
      // Une DIV pour la colonne de texte, et pas un span : les deux hôtes
      // d'étiquettes du jeu posent `span { position:absolute }` pour leurs
      // repères, et un span imbriqué sortirait du flux — la boîte se
      // refermerait sur le seul signe, le texte flottant à côté.
      el.innerHTML = (elu.signe ? "<u>" + esc(elu.signe) + "</u>" : "")
        + "<div><b>" + esc(elu.titre) + "</b>"
        + (elu.role ? "<i>" + esc(elu.role) + "</i>" : "") + "</div>";
      el.style.display = "";
    } else {
      // On ne MESURE jamais dans le même souffle qu'on écrit. Lire une largeur
      // juste après avoir changé le texte oblige le navigateur à refaire la
      // mise en page sur-le-champ : une demi-milliseconde sur le banc d'essai,
      // soixante dans le décor du jeu, qui est une page entière. On garde donc
      // la taille du battement précédent pour placer l'étiquette qu'on vient
      // d'écrire, et on relève la nouvelle au battement suivant — quand la
      // page s'est remise en forme d'elle-même et que la lecture ne coûte rien.
      lg = el.offsetWidth || lg; ht = el.offsetHeight || ht;
    }
    // Sous le curseur et un peu à droite — jamais dessous, où la main le cache.
    // Au bord du cadre, il passe de l'autre côté plutôt que de sortir.
    const droite = (px + 16 + lg) < w;
    el.style.left = (droite ? px + 16 : px - 16 - lg) + "px";
    el.style.top = Math.max(2, Math.min(h - ht - 2, py - ht / 2)) + "px";
  }

  return {
    /** La partie enrichit ou remplace un nom : la Gaffe plutôt qu'« Auberge ». */
    apposer(f) { apposer = f || null; dit = null; },
    montrer(v) { visible = v; if (!v) cacher(); },
    /**
     * Appelée à chaque image ; ne vise qu'au rythme de l'œil.
     * On revise même quand le curseur n'a pas bougé : c'est le MONDE qui passe
     * dessous — on tourne, on approche, et le toit désigné n'est plus le même.
     * Le rejet en gros du viseur rend ce calcul-là assez court pour qu'on
     * puisse le refaire dix fois par seconde sans y penser.
     */
    suivre() {
      if (!visible) return;
      const t = performance.now();
      if (t - dernier < PAUSE) return;
      dernier = t;
      viser();
    },
    disposer() {
      canevas.removeEventListener("pointermove", bouger);
      canevas.removeEventListener("pointerleave", partir);
      canevas.removeEventListener("pointerdown", prendre);
      canevas.removeEventListener("pointerup", lacher);
      canevas.removeEventListener("pointercancel", lacher);
      el.remove();
    },
  };
}
