// desseins.js — « Vos desseins », la cinquième échelle du décor.
// Le royaume porte la guerre, le château porte la salle, les gens portent les
// visages ; celle-ci porte ce que la reine s'est engagée à faire. La liste du
// rail latéral ne tient que des titres barrés ou non ; ici on donne ce qui sert
// à décider : ce qui reste, pour quand, de quelle bouche c'est venu, et combien
// de jours il reste. Rien qui ne soit dans etat/objectifs.json — donc rien que
// le personnage ne sache déjà.
"use strict";
window.Desseins = (() => {
  const JOURS_PAR_LUNE = 30;
  let objectifs = null;
  let aujourdhui = null;
  let charge = false;

  const enJours = (d) => d ? (d.annee * 12 + (d.lune - 1)) * JOURS_PAR_LUNE + d.jour : null;
  const texteDate = (d) =>
    d ? d.annee + " AC, " + d.lune + "e lune, " + d.jour + "e jour" : "";

  // Le délai dit en langue, pas en chiffre nu : c'est ainsi qu'on y pense.
  function delai(o) {
    const a = enJours(aujourdhui), b = enJours(o.echeance);
    if (a === null || b === null) return null;
    const n = b - a;
    if (n < 0) return { classe: "retard", texte: n === -1 ? "en retard d'un jour"
      : "en retard de " + -n + " jours" };
    if (n === 0) return { classe: "urgent", texte: "aujourd'hui même" };
    if (n === 1) return { classe: "urgent", texte: "demain" };
    if (n <= 3) return { classe: "proche", texte: "dans " + n + " jours" };
    return { classe: "loin", texte: "dans " + n + " jours" };
  }

  const GROUPES = [
    { statut: "en-cours", nom: "Ce qui reste à faire" },
    { statut: "accompli", nom: "Ce qui est fait" },
    { statut: "echoue", nom: "Ce qui est perdu" },
  ];

  function hote() { return document.getElementById("desseins"); }

  function carte(o) {
    const d = document.createElement("article");
    d.className = "dessein statut-" + (o.statut || "en-cours");
    const t = document.createElement("h3");
    t.textContent = o.titre;
    d.appendChild(t);

    const marge = document.createElement("div");
    marge.className = "dessein-marge";
    if (o.source) {
      const s = document.createElement("span");
      s.className = "dessein-source";
      s.textContent = "de " + o.source;
      marge.appendChild(s);
    }
    if (o.echeance) {
      const e = document.createElement("span");
      const del = (o.statut || "en-cours") === "en-cours" ? delai(o) : null;
      e.className = "dessein-echeance" + (del ? " echeance-" + del.classe : "");
      e.title = "Échéance : " + texteDate(o.echeance);
      e.textContent = del ? del.texte : texteDate(o.echeance);
      marge.appendChild(e);
    }
    if (marge.childNodes.length) d.appendChild(marge);

    if (o.description) {
      const p = document.createElement("p");
      p.className = "dessein-dit";
      p.textContent = o.description;
      d.appendChild(p);
      // les noms cités y deviennent cliquables, comme dans le fil
      if (window.Entites) Entites.traiter(p);
    }
    // Demander où en est un dessein : hors fiction, comme le mode Question —
    // personne dans la salle ne l'entend, le temps ne bouge pas. Le MJ relit le
    // registre pour celui-là et le remet à jour.
    const point = document.createElement("button");
    point.className = "dessein-point";
    point.textContent = "Où en est-on ?";
    point.title = "Demander l'état de ce dessein — hors scène, sans faire " +
      "avancer le temps";
    point.onclick = (ev) => {
      ev.stopPropagation();
      if (point.disabled) return;
      point.disabled = true;
      point.textContent = "Demandé…";
      Bus.poster({
        type: "libre", mode: "question", cible: o.id, cible_type: "objectif",
        texte: "Où en est ce dessein — « " + o.titre + " » ? Relis le registre, " +
          "dis-moi ce qui a bougé et ce qu'il reste, et remets-le à jour.",
      });
    };
    d.appendChild(point);

    // le dessein entier est un moment de pensée, même canal que les entités
    d.onclick = (ev) => {
      if (ev.target.closest("b[data-entite], .entite, button")) return;
      Entites.penser(o.id, "objectif", o.titre);
    };
    return d;
  }

  function dessiner() {
    const h = hote();
    if (!h) return;
    h.innerHTML = "";
    if (!objectifs) { h.innerHTML = '<p class="objectif-vide">…</p>'; return; }
    if (!objectifs.length) {
      h.innerHTML = '<p class="objectif-vide">Aucun dessein — pour l\'instant.</p>';
      return;
    }
    const corps = document.createElement("div");
    corps.className = "desseins-corps";
    if (aujourdhui) {
      const j = document.createElement("div");
      j.className = "desseins-jour";
      j.textContent = texteDate(aujourdhui);
      corps.appendChild(j);
    }
    GROUPES.forEach((g) => {
      const dedans = objectifs.filter((o) => (o.statut || "en-cours") === g.statut);
      if (!dedans.length) return;
      // le plus pressé en tête : une échéance passée ou proche d'abord
      if (g.statut === "en-cours") {
        dedans.sort((a, b) => (enJours(a.echeance) || 1e9) - (enJours(b.echeance) || 1e9));
      }
      const sec = document.createElement("section");
      sec.className = "desseins-groupe groupe-" + g.statut;
      const t = document.createElement("div");
      t.className = "desseins-groupe-titre";
      t.textContent = g.nom + " — " + dedans.length;
      sec.appendChild(t);
      dedans.forEach((o) => sec.appendChild(carte(o)));
      corps.appendChild(sec);
    });
    h.appendChild(corps);
  }

  function charger() {
    if (charge) return;
    charge = true;
    fetch("/objectifs").then((r) => r.json()).then((d) => {
      // un serveur d'avant cette vue répond 404 : ne pas confondre « le
      // registre est vide » avec « le serveur ne sait pas le lire »
      if (!d || !d.objectifs) throw new Error("route absente");
      objectifs = d.objectifs;
      aujourdhui = d.aujourdhui || null;
      dessiner();
      // le rail latéral se nourrit du flux, qui ne rejoue que ce qui y est
      // passé : on lui donne l'état sur disque, qui fait foi.
      if (window.Objectifs && Objectifs.hydrater) Objectifs.hydrater(objectifs);
    }).catch(() => {
      charge = false;
      const h = hote();
      if (h && !objectifs) {
        h.innerHTML = '<p class="objectif-vide">Le registre des desseins est ' +
          "hors d'atteinte — le serveur du jeu doit être relancé.</p>";
      }
    });
  }

  function relire() { charge = false; charger(); }

  // Chargé d'emblée, pas à l'ouverture de la vue : le rail latéral en dépend
  // dès la première seconde.
  charger();

  window.addEventListener("DOMContentLoaded", () => {
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "desseins", nom: "Vos desseins", hote: "desseins", ordre: 5,
        dispo: () => true,
        reparu: () => { if (!objectifs) charger(); },
      });
    }
  });

  // Un dessein qui bouge dans le flux : l'état sur disque a suivi, on relit.
  Bus.enregistrer("objectif", () => setTimeout(relire, 300));

  return { charger, relire };
})();
