// poignee.js — le séparateur entre la chronique et le décor, qu'on déplace.
//
// La page est une grille de quatre colonnes : le rail des récents, LES
// PRÉSENTS, LA CHRONIQUE, LE DÉCOR. La dernière était figée — trop étroite dès
// qu'on ouvre le conseil de guerre ou l'échiquier, trop large pour une scène de
// dialogue où seul le fil compte. Cette largeur appartient donc au lecteur : il
// tire le trait où il veut, et on s'en souvient.
//
// ATTENTION en touchant à la grille : douze règles de jeu.css déclarent
// `body{grid-template-columns}` et SEULE LA DERNIÈRE compte. Modifier une des
// onze autres ne fait rien du tout — c'est arrivé en écrivant ce module.
//
// Ce qui bouge est une VARIABLE, `--decor`, lue par `grid-template-columns`
// dans jeu.css ; la poignée elle-même est `position:fixed` et ne prend aucune
// place dans la grille — sans quoi la déplacer changerait ce qu'elle mesure.
//
// Regarder n'est pas agir : rien ici n'entre dans l'état, ne coûte une minute,
// ni ne part au serveur. La largeur vit dans `localStorage`, par navigateur.
"use strict";
window.Poignee = (() => {
  const CLE = "conseil-largeur-decor";
  const MIN = 360;                       // en deçà, la table peinte ne montre plus rien
  const DEFAUT = 560;                    // la valeur d'avant, qui reste le repère
  const marge = () => Math.max(MIN, Math.round(window.innerWidth * 0.28));
  const max = () => Math.round(window.innerWidth * 0.72);

  let el = null;

  const borner = (px) => Math.max(MIN, Math.min(max(), Math.round(px)));

  function poser(px, garder) {
    const v = borner(px);
    document.documentElement.style.setProperty("--decor", v + "px");
    if (el) el.style.right = v + "px";
    if (garder) { try { localStorage.setItem(CLE, String(v)); } catch (e) {} }
    // Les échelles qui dessinent sur mesure (la table peinte, le plan, le
    // damier) se calculent sur la place qu'on leur donne : sans ce rappel,
    // elles gardent le cadrage de l'ancienne largeur jusqu'au prochain
    // changement de vue.
    window.dispatchEvent(new Event("resize"));
  }

  function lue() {
    try {
      const v = parseInt(localStorage.getItem(CLE) || "", 10);
      if (v > 0) return v;
    } catch (e) {}
    return DEFAUT;
  }

  function tirer(e) {
    e.preventDefault();
    const bouger = (ev) => {
      const x = (ev.touches ? ev.touches[0].clientX : ev.clientX);
      poser(window.innerWidth - x, false);
    };
    const lacher = (ev) => {
      document.removeEventListener("mousemove", bouger);
      document.removeEventListener("touchmove", bouger);
      document.removeEventListener("mouseup", lacher);
      document.removeEventListener("touchend", lacher);
      document.body.classList.remove("tire");
      const x = (ev.changedTouches ? ev.changedTouches[0].clientX : ev.clientX);
      poser(window.innerWidth - x, true);
    };
    document.body.classList.add("tire");
    document.addEventListener("mousemove", bouger);
    document.addEventListener("touchmove", bouger, { passive: false });
    document.addEventListener("mouseup", lacher);
    document.addEventListener("touchend", lacher);
  }

  function construire() {
    el = document.createElement("div");
    el.id = "poignee";
    el.setAttribute("role", "separator");
    el.setAttribute("aria-orientation", "vertical");
    el.setAttribute("aria-label", "Largeur du décor — tirez, ou les flèches");
    el.tabIndex = 0;
    el.title = "Tirez pour élargir le décor · double-clic pour la largeur d'origine";
    el.addEventListener("mousedown", tirer);
    el.addEventListener("touchstart", tirer, { passive: false });
    el.addEventListener("dblclick", () => poser(DEFAUT, true));
    // Au clavier : les flèches, pas de souris exigée.
    el.addEventListener("keydown", (e) => {
      const pas = e.shiftKey ? 60 : 16;
      const w = parseInt(getComputedStyle(document.documentElement)
        .getPropertyValue("--decor"), 10) || DEFAUT;
      if (e.key === "ArrowLeft") { poser(w + pas, true); e.preventDefault(); }
      if (e.key === "ArrowRight") { poser(w - pas, true); e.preventDefault(); }
      if (e.key === "Home") { poser(DEFAUT, true); e.preventDefault(); }
    });
    document.body.appendChild(el);
  }

  window.addEventListener("DOMContentLoaded", () => {
    construire();
    poser(lue(), false);
  });
  // La fenêtre rétrécit : la largeur gardée peut devenir plus grande que la
  // moitié de l'écran. On la reborne sans l'oublier — elle revient telle
  // quelle quand la place revient.
  window.addEventListener("resize", () => {
    const w = parseInt(getComputedStyle(document.documentElement)
      .getPropertyValue("--decor"), 10) || DEFAUT;
    const v = borner(w);
    if (v !== w) {
      document.documentElement.style.setProperty("--decor", v + "px");
      if (el) el.style.right = v + "px";
    }
  });

  return { poser, largeur: () => parseInt(getComputedStyle(document.documentElement)
    .getPropertyValue("--decor"), 10) || DEFAUT, marge };
})();
