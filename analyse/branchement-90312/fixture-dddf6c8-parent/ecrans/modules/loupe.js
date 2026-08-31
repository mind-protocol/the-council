// loupe.js — se pencher sur une carte : molette, glissé, pincement.
// Générique : la loupe ne sait rien de la géographie. On lui donne un hôte, le
// cadrage courant, ses bornes, et de quoi le reposer ; elle rend un nouveau
// cadrage et laisse l'appelant redessiner.
//
// Pourquoi redessiner plutôt que zoomer l'image : dans ce jeu, toute épaisseur
// et tout corps de texte se calculent depuis la largeur du cadrage (var(--k)).
// Un cadrage neuf, c'est donc la géographie qui s'écarte pendant que les pièces,
// les noms et les traits gardent exactement leur taille — et les noms écartés
// faute de place reviennent d'eux-mêmes à mesure qu'on approche. Un zoom
// d'image grossirait tout ensemble et n'apprendrait rien.
//
// Le <svg> est remplacé à chaque redessin : les écoutants vivent sur l'HÔTE,
// jamais sur le dessin.
"use strict";
window.Loupe = (() => {
  const etats = new WeakMap();
  const SEUIL = 4;                 // px : en deçà, c'est un clic, pas un glissé

  // Un glissé qui finit sur une place ne doit pas ouvrir sa pensée : on garde la
  // trace du geste le temps que le clic remonte.
  function aGlisse(hote) {
    const e = etats.get(hote);
    return !!(e && e.glisse);
  }

  function borner(vb, b, min) {
    let [x, y, l, h] = vb;
    const r = h / l;
    l = Math.max(min, Math.min(l, b[2]));
    h = l * r;
    if (h > b[3]) { h = b[3]; l = h / r; }
    x = Math.max(b[0], Math.min(x, b[0] + b[2] - l));
    y = Math.max(b[1], Math.min(y, b[1] + b[3] - h));
    return [x, y, l, h];
  }

  // Les coordonnées de la carte sous le curseur, letterboxing compris.
  function enUnites(hote, cx, cy) {
    const svg = hote.querySelector("svg");
    if (!svg || !svg.getScreenCTM) return null;
    const m = svg.getScreenCTM();
    if (!m) return null;
    const p = new DOMPoint(cx, cy).matrixTransform(m.inverse());
    return { x: p.x, y: p.y, unitesParPixel: 1 / m.a };
  }

  function brancher(hote, opts) {
    if (!hote || etats.has(hote)) return;
    const e = {
      opts, glisse: false, pointeurs: new Map(),
      depart: null, ecart: 0, demande: null, cible: null,
    };
    etats.set(hote, e);

    const bornes = () => (typeof opts.bornes === "function" ? opts.bornes() : opts.bornes);
    const min = opts.min || 45;

    // Un seul redessin par frame, quoi qu'il arrive : la molette et le glissé
    // arrivent bien plus vite que l'écran ne se rafraîchit.
    function viser(vb) {
      e.cible = borner(vb, bornes(), min);
      if (e.demande) return;
      e.demande = requestAnimationFrame(() => {
        e.demande = null;
        opts.poser(e.cible);
      });
    }

    // ---- la molette : on approche là où est le doigt, pas au centre --------
    hote.addEventListener("wheel", (ev) => {
      if (!ev.target.closest("svg")) return;
      ev.preventDefault();
      const u = enUnites(hote, ev.clientX, ev.clientY);
      if (!u) return;
      const vb = e.cible || opts.vue();
      let d = ev.deltaY;
      if (ev.deltaMode === 1) d *= 16;            // certaines molettes comptent en lignes
      const f = Math.exp(d * (ev.ctrlKey ? 0.008 : 0.0015));
      viser([u.x - (u.x - vb[0]) * f, u.y - (u.y - vb[1]) * f, vb[2] * f, vb[3] * f]);
    }, { passive: false });

    // ---- le glissé (et le pincement à deux doigts) ------------------------
    hote.addEventListener("pointerdown", (ev) => {
      if (!ev.target.closest("svg") || ev.button > 0) return;
      e.pointeurs.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      if (e.pointeurs.size > 2) return;
      const u = enUnites(hote, ev.clientX, ev.clientY);
      if (!u) return;
      e.depart = {
        vb: (e.cible || opts.vue()).slice(),
        x: ev.clientX, y: ev.clientY, upp: u.unitesParPixel,
        pince: e.pointeurs.size === 2 ? ecartement(e.pointeurs) : 0,
      };
      e.ecart = 0;
      try { hote.setPointerCapture(ev.pointerId); } catch (err) {}
      hote.classList.add("loupe-tient");
    });

    function ecartement(m) {
      const p = Array.from(m.values());
      return Math.hypot(p[1].x - p[0].x, p[1].y - p[0].y);
    }
    function milieu(m) {
      const p = Array.from(m.values());
      return [(p[0].x + p[1].x) / 2, (p[0].y + p[1].y) / 2];
    }

    hote.addEventListener("pointermove", (ev) => {
      if (!e.pointeurs.has(ev.pointerId) || !e.depart) return;
      e.pointeurs.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      const d = e.depart;

      if (e.pointeurs.size === 2 && d.pince) {
        const f = d.pince / Math.max(1, ecartement(e.pointeurs));
        const [mx, my] = milieu(e.pointeurs);
        const u = enUnites(hote, mx, my);
        if (!u) return;
        const vb = e.cible || opts.vue();
        e.ecart = SEUIL + 1;
        viser([u.x - (u.x - vb[0]) * f, u.y - (u.y - vb[1]) * f, vb[2] * f, vb[3] * f]);
        d.pince = ecartement(e.pointeurs);
        return;
      }

      const dx = ev.clientX - d.x, dy = ev.clientY - d.y;
      e.ecart = Math.max(e.ecart, Math.hypot(dx, dy));
      if (e.ecart < SEUIL) return;
      e.glisse = true;
      viser([d.vb[0] - dx * d.upp, d.vb[1] - dy * d.upp, d.vb[2], d.vb[3]]);
    });

    const lacher = (ev) => {
      if (!e.pointeurs.has(ev.pointerId)) return;
      e.pointeurs.delete(ev.pointerId);
      if (e.pointeurs.size) return;
      e.depart = null;
      hote.classList.remove("loupe-tient");
      // le clic remonte juste après le pointerup : on ne baisse le drapeau
      // qu'ensuite, pour qu'un glissé n'ouvre pas la pensée d'un lieu.
      if (e.glisse) setTimeout(() => { e.glisse = false; }, 0);
    };
    hote.addEventListener("pointerup", lacher);
    hote.addEventListener("pointercancel", lacher);
    // Filet : si la capture du pointeur a échoué, le relâché peut tomber
    // ailleurs — et la carte resterait collée au curseur.
    window.addEventListener("pointerup", lacher);

    // ---- reposer la table -------------------------------------------------
    hote.addEventListener("dblclick", (ev) => {
      if (!ev.target.closest("svg")) return;
      if (ev.target.closest(".lieu-carte, .jeton, .trait")) return;
      e.cible = null;
      opts.reposer();
    });

    hote.classList.add("loupe");
  }

  // Un cadrage imposé du dehors (une démonstration, un changement de scène)
  // annule ce que la loupe visait : sinon la frame suivante le remettrait.
  function oublier(hote) {
    const e = etats.get(hote);
    if (!e) return;
    if (e.demande) { cancelAnimationFrame(e.demande); e.demande = null; }
    e.cible = null;
  }

  return { brancher, aGlisse, oublier };
})();
