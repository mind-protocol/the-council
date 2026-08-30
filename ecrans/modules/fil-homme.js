// fil-homme.js — le fil PAR HOMME : ce que voit un joueur qui incarne un
// habitant hors roster (ou un arbitre). Sa mémoire, jamais le flux public :
// le rendu /scene se tait, et l'on peint GET /fil-homme à sa place — la
// conclusion de veille en tête, le vécu de ses sessions, les billets de ses
// canaux. La conversation d'incarnation (échos + verdicts d'actions.js) passe
// par Bus.chronique en direct et reste intacte.
"use strict";
(() => {
  const nomDe = (id) => {
    if (!id) return "";
    const p = window.Gens && Gens.qui ? Gens.qui(id) : null;
    return (p && p.nom) || String(id).replace(/-/g, " ");
  };

  // Une entrée du fil → sa bulle de chronique. Toutes portent `chr-fil` :
  // la mémoire d'un homme garde ses retours à la ligne (pre-wrap).
  function peindre(e, moi) {
    if (e.genre === "pensee") {
      return Bus.chronique("chr-pensee chr-fil", "Là où tu t'étais laissé", e.texte);
    }
    if (e.genre === "recit") return Bus.chronique("chr-recit chr-fil", null, e.texte);
    if (e.genre === "replique") {
      const p = window.Gens && Gens.qui ? Gens.qui(moi.personnage_id) : null;
      return Bus.chronique("chr-replique chr-fil",
        (p && p.nom) || moi.nom || moi.personnage_id, e.texte,
        p ? { avatar: p.portrait_svg, role: p.titre } : {});
    }
    if (e.genre === "entendu") {
      // l'entendu : la voix d'en face — on ne sait pas toujours laquelle
      return Bus.chronique("chr-replique chr-fil", "👂 Entendu", e.texte);
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
      const d = Bus.chronique("chr-billet chr-fil", nomDe(e.de), e.texte);
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
      // 2. Un arbitre incarné n'a pas de verbes : sa page observe, sa session
      // se pilote ailleurs.
      if (moi.mj) {
        const barre = document.getElementById("fil-actions");
        if (barre) barre.hidden = true;
      }
      fetch("/fil-homme")
        .then((r) => r.json())
        .then((d) => {
          const zone = document.getElementById("fil-corps");
          if (!zone) return;
          // ce que la course du premier sondage a pu peindre s'efface
          zone.innerHTML = "";
          if (moi.mj) {
            const note = document.createElement("div");
            note.className = "fil-observation";
            note.textContent =
              "Poste d'observation — sa session se pilote par claude --resume";
            zone.appendChild(note);
          }
          for (const e of (d && d.fil) || []) peindre(e, moi);
          zone.scrollTop = zone.scrollHeight;
        })
        .catch(() => {});
    })(40);
  });
})();
