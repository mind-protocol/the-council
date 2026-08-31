// fil-homme.js — le fil PAR HOMME : ce que voit un joueur qui incarne un
// habitant hors roster. Sa mémoire, jamais le flux public :
// le rendu /scene se tait, et l'on peint GET /fil-homme à sa place — la
// conclusion de veille en tête, le vécu de ses sessions, les billets de ses
// canaux. La conversation d'incarnation (échos + verdicts d'actions.js) passe
// par Bus.chronique en direct et reste intacte.
"use strict";
(() => {
  // Markdown minimal des bulles de mémoire — titres, gras, italique, puces.
  // Attention.html (le moteur du fil) rend déjà **gras**, puces et renvois,
  // mais rien des titres ni de l'italique, et il ne s'applique qu'au texte nu :
  // on échappe donc le HTML D'ABORD (XSS), puis on pose les balises — la
  // chronique voit du HTML et passe en passe-plat, sans double traitement.
  // Pas de lib : quatre regex suffisent à la mémoire d'un homme.
  function md(source) {
    let t = String(source == null ? "" : source)
      .replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    // titres # à #### : la ligne en intertitre discret ; son saut de ligne
    // est consommé — pre-wrap le rendrait deux fois (le bloc, puis le \n)
    t = t.replace(/^(#{1,4})\s+(.*)$\n?/gm, (m, h, titre) =>
      '<span class="md-titre md-t' + h.length + '">' + titre + "</span>");
    t = t.replace(/\*\*([^*\n][^*]*?)\*\*/g, "<strong>$1</strong>");
    // l'italique colle à ses mots (*mot*, jamais « 2 * 3 * 4 »)
    t = t.replace(/(^|[\s(«])\*(\S(?:[^*\n]*\S)?)\*(?=[\s.,;:!?)»…]|$)/gm,
      "$1<em>$2</em>");
    t = t.replace(/^[-–•]\s+/gm, '<span class="md-puce">•</span> ');
    return t;
  }

  const nomDe = (id) => {
    if (!id) return "";
    const p = window.Gens && Gens.qui ? Gens.qui(id) : null;
    return (p && p.nom) || String(id).replace(/-/g, " ");
  };

  // Une entrée du fil → sa bulle de chronique. Toutes portent `chr-fil` :
  // la mémoire d'un homme garde ses retours à la ligne (pre-wrap).
  function peindre(e, moi) {
    if (e.genre === "pensee") {
      return Bus.chronique("chr-pensee chr-fil", "Là où tu t'étais laissé", md(e.texte));
    }
    if (e.genre === "recit") return Bus.chronique("chr-recit chr-fil", null, md(e.texte));
    if (e.genre === "replique") {
      const p = window.Gens && Gens.qui ? Gens.qui(moi.personnage_id) : null;
      return Bus.chronique("chr-replique chr-fil",
        (p && p.nom) || moi.nom || moi.personnage_id, md(e.texte),
        p ? { avatar: p.portrait_svg, role: p.titre } : {});
    }
    if (e.genre === "entendu") {
      // l'entendu : la voix d'en face — on ne sait pas toujours laquelle
      return Bus.chronique("chr-replique chr-fil", "👂 Entendu", md(e.texte));
    }
    if (e.genre === "gestes") {
      // UNE bulle par journée, repliée : le résumé en tête, le détail au clic.
      const d = Bus.chronique("chr-breve chr-fil", null, e.texte);
      const t = d && d.querySelector(".chr-texte");
      if (t && e.detail && e.detail.length) {
        const det = document.createElement("details");
        const som = document.createElement("summary");
        som.textContent = e.texte;
        det.appendChild(som);
        const ul = document.createElement("ul");
        ul.className = "gestes-detail";
        for (const g of e.detail) {
          const li = document.createElement("li");
          li.textContent = g;
          ul.appendChild(li);
        }
        det.appendChild(ul);
        t.textContent = "";
        t.appendChild(det);
      }
      return d;
    }
    if (e.genre === "billet") {
      // un billet est un papier qui a voyagé, pas une voix
      const d = Bus.chronique("chr-billet chr-fil", nomDe(e.de), md(e.texte));
      const q = d && d.querySelector(".chr-qui");
      if (q && (e.date || e.heure)) {
        const s = document.createElement("span");
        s.className = "chr-billet-date";
        s.textContent = [e.date, e.heure].filter(Boolean).join(", ");
        q.appendChild(s);
      }
      return d;
    }
    return null;
  }

  window.addEventListener("DOMContentLoaded", () => {
    // bus.js remplit window.Moi depuis /moi — on attend cette réponse-là
    // (même motif qu'actions.js : == null couvre l'UNDEFINED d'avant bus).
    (function attendre(essais) {
      if (window.Moi == null && essais > 0)
        return setTimeout(() => attendre(essais - 1), 300);
      const moi = window.Moi;
      if (!moi || !moi.hors_roster) return;
      // 1. Le rendu /scene se tait : on ré-enregistre chaque peintre en
      // silence. Le sondage continue (bandeau, heure), mais plus rien du flux
      // public ne se peint — le fil de cet homme est SA mémoire.
      Object.keys(Bus.rendus).forEach((k) => Bus.enregistrer(k, () => {}));
      fetch("/fil-homme")
        .then((r) => r.json())
        .then((d) => {
          const zone = document.getElementById("fil-corps");
          if (!zone) return;
          // ce que la course du premier sondage a pu peindre s'efface
          zone.innerHTML = "";
          for (const e of (d && d.fil) || []) peindre(e, moi);
          zone.scrollTop = zone.scrollHeight;
        })
        .catch(() => {});
    })(40);
  });
})();
