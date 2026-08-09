// defilement.js — la place du joueur dans le fil, tenue pour de bon.
//
// Trois choses, et elles se tiennent :
//   1. On ne ramène JAMAIS le joueur en bas de force. Le bus le savait déjà pour
//      les items qui arrivent ; il ne le savait pas pour le rejeu d'ouverture,
//      qui replaçait tout le monde au pied du fil à chaque rechargement.
//   2. Quand du texte tombe pendant qu'il lit plus haut, une flèche le lui dit —
//      avec le nombre de lignes arrivées. Cliquer redescend, et rien d'autre ne
//      le fait bouger.
//   3. Sa place survit au rechargement, et même à la fermeture de la fenêtre.
//      Pas en pixels — le fil grandit entre deux visites, et un pixel ne veut
//      plus rien dire — mais en ANCRE : l'item du flux qui était en haut de
//      l'écran, et de combien il dépassait.
"use strict";
window.Defilement = (() => {
  const CLE = "lc-fil-place";
  const MARGE = 90;          // ce qu'on tolère pour dire « il est en bas »
  const CALME_MS = 900;      // sans rien de neuf pendant ce temps, le rejeu est fini
  const CAP_MS = 45000;      // garde-fou : un fil qui n'arrête jamais d'arriver

  let zone = null, fleche = null, compte = 0;
  let restauration = null;   // l'ancre qu'on cherche encore à retrouver
  let calme = null;          // le fil s'est-il tu ?
  let sauvegarde = null;

  const enBas = () => !zone || zone.scrollHeight - zone.scrollTop - zone.clientHeight < MARGE;

  // ---- l'ancre : où il en était, dit en items et non en pixels ------------
  function lire() {
    try { return JSON.parse(localStorage.getItem(CLE) || "null"); } catch (e) { return null; }
  }
  function ecrire(v) {
    try { localStorage.setItem(CLE, JSON.stringify(v)); } catch (e) {}
  }

  // L'item qui coupe le haut de la fenêtre : c'est lui qu'on retrouvera.
  function ancre() {
    if (!zone) return null;
    if (enBas()) return { bas: true };
    const haut = zone.scrollTop;
    for (const el of zone.querySelectorAll("[data-i]")) {
      if (el.offsetTop + el.offsetHeight > haut) {
        return { i: el.getAttribute("data-i"), decalage: Math.round(el.offsetTop - haut) };
      }
    }
    return { bas: true };
  }

  function noter() {
    if (restauration) return;         // on n'écrase pas ce qu'on est en train de restaurer
    clearTimeout(sauvegarde);
    sauvegarde = setTimeout(() => ecrire(ancre()), 250);
  }

  // ---- retrouver sa place ------------------------------------------------
  // Le rejeu d'ouverture pose les items un à un et pousse le fil en bas à chaque
  // fois. On ne lutte pas contre lui item par item : on repose l'ancre après
  // chaque salve, jusqu'à ce que le fil se calme — ou que le joueur touche à
  // quelque chose, et alors c'est lui qui a raison.
  function reposer() {
    if (!restauration || !zone) return false;
    if (restauration.bas) { zone.scrollTop = zone.scrollHeight; return true; }
    const el = zone.querySelector('[data-i="' + restauration.i + '"]');
    if (!el) return false;
    zone.scrollTop = Math.max(0, el.offsetTop - (restauration.decalage || 0));
    return true;
  }

  // On ne lâche pas l'ancre sur un chrono : un rejeu de deux cents lignes met
  // plus longtemps qu'on ne croit, et abandonner en cours de route rend le
  // joueur au bas du fil — puis le défilement du rejeu ÉCRASE son ancre, et sa
  // place est perdue pour de bon. On la lâche quand le fil se tait, ou quand le
  // joueur touche à quelque chose.
  function finirRestauration() {
    if (!restauration) return;
    clearTimeout(calme); calme = null;
    restauration = null;
    majFleche();
  }

  function attendreLeCalme() {
    clearTimeout(calme);
    calme = setTimeout(() => { reposer(); finirRestauration(); }, CALME_MS);
  }

  // ---- la flèche ---------------------------------------------------------
  function majFleche() {
    if (!fleche) return;
    const montrer = compte > 0 && !enBas();
    fleche.classList.toggle("visible", montrer);
    if (montrer) {
      fleche.querySelector(".fil-bas-compte").textContent = compte > 99 ? "99+" : compte;
      fleche.title = compte + (compte > 1 ? " nouvelles lignes plus bas" : " nouvelle ligne plus bas");
    }
  }

  function descendre() {
    if (!zone) return;
    restauration = null;
    // Le glissé doux est bon pour quelques écrans ; sur cent mille pixels il
    // rampe pendant dix secondes et le joueur croit que le bouton est mort.
    const reste = zone.scrollHeight - zone.scrollTop - zone.clientHeight;
    zone.scrollTo({ top: zone.scrollHeight, behavior: reste > 3000 ? "auto" : "smooth" });
    compte = 0;
    majFleche();
  }

  window.addEventListener("DOMContentLoaded", () => {
    zone = document.getElementById("fil-corps");
    if (!zone) return;

    fleche = document.createElement("button");
    fleche.type = "button";
    fleche.id = "fil-vers-bas";
    fleche.innerHTML = '<span class="fil-bas-compte"></span>' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v13M6 12.5l6 6 6-6"/></svg>';
    fleche.setAttribute("aria-label", "descendre au plus récent");
    fleche.addEventListener("click", descendre);
    (document.getElementById("fil") || document.body).appendChild(fleche);

    restauration = lire();

    // Ce qui arrive dans le fil : soit c'est le rejeu et on repose l'ancre,
    // soit c'est du neuf et on compte, sans bouger le joueur d'un pixel.
    new MutationObserver((lots) => {
      let ajouts = 0;
      for (const l of lots) for (const n of l.addedNodes) if (n.nodeType === 1) ajouts++;
      if (!ajouts) return;
      if (restauration) { reposer(); attendreLeCalme(); return; }
      if (!enBas()) { compte += ajouts; majFleche(); }
    }).observe(zone, { childList: true });

    zone.addEventListener("scroll", () => {
      if (enBas()) { compte = 0; }
      majFleche();
      noter();
    }, { passive: true });

    // Le joueur reprend la main dès qu'il touche à quoi que ce soit : on cesse
    // de lui reposer son ancre sous les doigts.
    ["wheel", "touchstart", "keydown", "mousedown"].forEach((e) =>
      zone.addEventListener(e, finirRestauration, { passive: true }));

    // Premier essai tout de suite, puis on laisse le rejeu nous rappeler à
    // chaque salve — et l'on s'arrête quand il se tait.
    reposer();
    attendreLeCalme();
    setTimeout(finirRestauration, CAP_MS);
    // Fermer la fenêtre est une façon de partir comme une autre.
    window.addEventListener("beforeunload", () => { if (!restauration) ecrire(ancre()); });
  });

  return { descendre, ancre };
})();
