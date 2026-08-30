// sieges.js — le siège : qui l'on incarne, et par où l'on en change.
//
// Le jeu se joue à plusieurs sièges (`etat/joueurs.json`) — une reine sur son
// rocher, un homme de la vase à Port-Réal —, et l'on passe de l'un à l'autre
// sans rouvrir l'URL au jeton. Les jetons ne descendent JAMAIS jusqu'ici : on
// demande un personnage à /bascule, le serveur pose le cookie et renvoie à la
// racine. Rien de ce qui est privé à un siège ne transite par cette liste.
//
// Le contrôle vit dans le panneau latéral, sous « Le siège ». Il était au
// bandeau du décor tant que ce bandeau existait ; celui-ci est descendu sous la
// case d'écriture, où l'on lit le lieu et l'heure — et changer de personnage
// n'est pas une information de scène, c'est une commande de rail. Le cadre
// reste replié en partie seule : un seul siège au roster n'a rien à choisir.
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
      // Les hommes hors roster : tout le reste du monde, incarnable au même
      // titre qu'un siège — le serveur les sert déjà triés par nom.
      const hommes = (d && d.hommes) || [];
      // Les arbitres : mj et les mj-<ville> qui ont une chambre — un MJ est
      // un habitant, il s'incarne par le même /bascule (poste d'observation).
      const arbitres = (d && d.arbitres) || [];
      if (!d || !d.multi ||
          (sieges.length < 2 && !hommes.length && !arbitres.length)) return;
      const moi = d.moi && d.moi.personnage_id;
      const mien = sieges.find((s) => s.personnage_id === moi)
        || hommes.find((s) => s.personnage_id === moi)
        || arbitres.find((s) => s.personnage_id === moi)
        || (d.moi ? { personnage_id: moi, nom: d.moi.nom } : null);

      zone.hidden = false;
      // Le contrôle vit dans le rail : c'est le cadre `zone-siege` qui porte le
      // titre, et il reste replié tant qu'il n'y a rien à choisir.
      const cadre = document.getElementById("zone-siege");
      if (cadre) cadre.hidden = false;
      bouton.textContent = mien ? (mien.nom || mien.personnage_id) : "Choisir un siège";
      bouton.title = mien
        ? "Vous incarnez " + (mien.nom || mien.personnage_id) + " — cliquez pour changer de siège"
        : "Aucun siège : cliquez pour en prendre un";

      const choix = (s) => {
        const ici = s.personnage_id === moi;
        return '<button type="button" class="siege-choix' + (ici ? " actif" : "") +
               '" data-vers="' + esc(s.personnage_id) + '">' +
               esc(s.nom || s.personnage_id) + "</button>";
      };
      // Deux groupes : les sièges de la partie d'abord, puis tous les autres
      // hommes du monde. Choisir l'un ou l'autre passe par le MÊME /bascule.
      liste.innerHTML = sieges.map(choix).join("") +
        (hommes.length
          ? '<div class="siege-groupe">Les hommes</div>' + hommes.map(choix).join("")
          : "") +
        (arbitres.length
          ? '<div class="siege-groupe">Les arbitres</div>' + arbitres.map(choix).join("")
          : "");

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
