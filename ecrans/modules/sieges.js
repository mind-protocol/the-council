// sieges.js — le siège : qui l'on incarne, et par où l'on en change.
//
// Le jeu se joue à plusieurs sièges (`etat/joueurs.json`) — une reine sur son
// rocher, un homme de la vase à Port-Réal —, et l'on passe de l'un à l'autre
// sans rouvrir l'URL au jeton. Les jetons ne descendent JAMAIS jusqu'ici : on
// demande un personnage à /bascule, le serveur pose le cookie et renvoie à la
// racine. Rien de ce qui est privé à un siège ne transite par cette liste.
//
// Le contrôle vit dans le bandeau et non dans le panneau latéral : savoir qui
// l'on est ne se déplie pas, ça se lit. Il reste caché en partie seule — un
// seul siège au roster n'a rien à choisir.
"use strict";
(() => {
  window.addEventListener("DOMContentLoaded", () => {
    const zone = document.getElementById("siege");
    const bouton = document.getElementById("siege-bouton");
    const liste = document.getElementById("siege-liste");
    if (!zone || !bouton || !liste) return;

    const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                               .replace(/"/g, "&quot;");

    function fermer() {
      liste.hidden = true;
      bouton.setAttribute("aria-expanded", "false");
    }

    fetch("/moi").then((r) => r.json()).then((d) => {
      const sieges = (d && d.sieges) || [];
      if (!d || !d.multi || sieges.length < 2) return;
      const moi = d.moi && d.moi.personnage_id;
      const mien = sieges.find((s) => s.personnage_id === moi);

      zone.hidden = false;
      bouton.textContent = mien ? (mien.nom || mien.personnage_id) : "Choisir un siège";
      bouton.title = mien
        ? "Vous incarnez " + (mien.nom || mien.personnage_id) + " — cliquez pour changer de siège"
        : "Aucun siège : cliquez pour en prendre un";

      liste.innerHTML = sieges.map((s) => {
        const ici = s.personnage_id === moi;
        return '<button type="button" class="siege-choix' + (ici ? " actif" : "") +
               '" data-vers="' + esc(s.personnage_id) + '">' +
               esc(s.nom || s.personnage_id) + "</button>";
      }).join("");

      bouton.onclick = (e) => {
        e.stopPropagation();
        const ouvert = !liste.hidden;
        liste.hidden = ouvert;
        bouton.setAttribute("aria-expanded", String(!ouvert));
      };
      liste.onclick = (e) => {
        const b = e.target.closest(".siege-choix");
        if (!b) return;
        if (b.classList.contains("actif")) return fermer();
        location.href = "/bascule?vers=" + encodeURIComponent(b.dataset.vers);
      };
      // En CAPTURE : la carte, le plan et la table peinte arrêtent la
      // propagation de leurs clics, et un menu qui n'écouterait qu'en
      // remontée resterait ouvert dès qu'on clique sur le décor — c'est
      // précisément ce qu'il recouvre.
      const dehors = (e) => {
        if (!liste.hidden && !zone.contains(e.target)) fermer();
      };
      document.addEventListener("pointerdown", dehors, true);
      document.addEventListener("click", dehors, true);
      window.addEventListener("blur", fermer);
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") fermer();
      }, true);
    }).catch(() => {});
  });
})();
