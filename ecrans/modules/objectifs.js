// objectifs.js — les objectifs du joueur : donnés par le flux (type "objectif"),
// listés dans la colonne latérale, marqués comme des moments dans le fil.
// Cliquer un objectif = un moment de pensée (même canal que les entités).
"use strict";
window.Objectifs = (() => {
  const objectifs = new Map();

  function rendreListe() {
    const zone = document.getElementById("liste-objectifs");
    if (!zone) return;
    zone.innerHTML = "";
    if (!objectifs.size) {
      zone.innerHTML = '<p class="objectif-vide">Aucun — pour l\'instant.</p>';
      return;
    }
    objectifs.forEach((o) => {
      const d = document.createElement("div");
      d.className = "objectif statut-" + o.statut;
      d.title = (o.description || "") + (o.source ? " — " + o.source : "");
      d.textContent = o.titre;
      d.onclick = () => Entites.penser(o.id, "objectif", o.titre);
      zone.appendChild(d);
    });
  }

  window.addEventListener("DOMContentLoaded", rendreListe);

  // Le flux ne rejoue que ce qui y est passé : un dessein né avant que le
  // fil ne porte des items `objectif` n'y figure pas, et la liste dit « aucun »
  // alors que le registre en tient neuf. `etat/objectifs.json` fait foi ;
  // desseins.js nous le passe dès qu'il l'a lu.
  function hydrater(liste) {
    (liste || []).forEach((o) => {
      objectifs.set(o.id, {
        id: o.id, titre: o.titre, description: o.description,
        source: o.source, statut: o.statut || "en-cours",
      });
    });
    rendreListe();
  }

  Bus.enregistrer("objectif", (it, ctx) => {
    const action = it.action || "ajouter";
    if (action === "ajouter") {
      objectifs.set(it.id, { id: it.id, titre: it.titre, description: it.description,
        source: it.source, statut: "en-cours" });
    } else if (action === "retirer") {
      objectifs.delete(it.id);
    } else {
      const o = objectifs.get(it.id);
      if (o) o.statut = action === "accomplir" ? "accompli" : "echoue";
    }
    rendreListe();
    // le moment est marqué dans le fil ; la liste à gauche garde l'état
    if (["ajouter", "accomplir", "echouer"].includes(action)) {
      const titre = (objectifs.get(it.id) || { titre: it.titre || it.id }).titre;
      const coiffe = action === "ajouter" ? "Nouveau dessein"
        : action === "accomplir" ? "Dessein accompli" : "Dessein échoué";
      Bus.chronique("chr-objectif" + (action !== "ajouter" ? " chr-objectif-" + action : ""),
        coiffe, titre + (it.description || it.note ? " — " + (it.description || it.note) : ""));
    }
  });

  return { hydrater };
})();
