// fils.js — « Ce qui court » : les affaires en cours, avec le nom de l'homme
// dessus et un interrupteur qui dit QUI TIENT LA PLUME. À gauche ce sur quoi
// on joue, à droite ce qui tourne en fond et revient en une ligne au passé.
//
// Le rail est un TABLEAU, pas un menu : basculer un fil ne joue rien: ça dit
// une intention, comme tout ce qui part de la barre. Et un fil délégué ne
// remonte jamais ICI — il remonte dans la scène, en `demande`, dans la bouche
// de l'homme. Format et doctrine : docs/fils.md.
"use strict";
window.Fils = (() => {
  const JOURS_PAR_LUNE = 30;
  let fils = [];
  let aujourdhui = null;

  const enJours = (d) =>
    d ? (d.annee * 12 + (d.lune - 1)) * JOURS_PAR_LUNE + d.jour : null;

  // Le délai se dit en langue, pas en chiffre nu — c'est ainsi qu'on y pense.
  function delai(f) {
    const a = enJours(aujourdhui), b = enJours(f.echeance);
    if (a === null || b === null) return null;
    const n = b - a;
    if (n < 0) return { classe: "retard", texte: n === -1 ? "en retard d'un jour" : "en retard de " + -n + " jours" };
    if (n === 0) return { classe: "urgent", texte: "aujourd'hui" };
    if (n === 1) return { classe: "urgent", texte: "demain" };
    if (n <= 3) return { classe: "proche", texte: "dans " + n + " jours" };
    return { classe: "loin", texte: "dans " + n + " jours" };
  }

  function basculer(f, mode) {
    if (f.mode === mode) return;
    if (mode === "delegue" && !f.sur) return;
    f.mode = mode;
    rendre();
    fetch("/fils", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fil_id: f.id, mode: mode }),
    }).catch(() => {});
  }

  function interrupteur(f) {
    const d = document.createElement("div");
    d.className = "fil-mode";
    if (!f.sur) {
      d.classList.add("fil-sans-nom");
      d.textContent = "Sans nom";
      d.title = "Personne ne tient cette affaire — elle revient à votre main.";
      return d;
    }
    [["joue", "Joué"], ["delegue", "Délégué"]].forEach(([cle, libelle]) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "fil-bouton" + (f.mode === cle ? " actif" : "");
      b.textContent = libelle;
      b.setAttribute("aria-pressed", f.mode === cle ? "true" : "false");
      b.title = cle === "joue"
        ? "Vous tenez la plume : ça se joue en scène."
        : "Il tient la plume : ça tourne hors champ et revient déjà fait.";
      b.onclick = (e) => { e.stopPropagation(); basculer(f, cle); };
      d.appendChild(b);
    });
    return d;
  }

  function ligne(f) {
    const l = document.createElement("div");
    l.className = "fil";
    const g = document.createElement("div");
    g.className = "fil-corps";

    const t = document.createElement("div");
    t.className = "fil-titre";
    t.textContent = f.titre;
    g.appendChild(t);

    const m = document.createElement("div");
    m.className = "fil-marge";
    const bouts = [];
    if (f.sur_nom) bouts.push(f.sur_nom);
    else bouts.push("sur personne");
    if (f.detail) bouts.push(f.detail);
    m.textContent = bouts.join(" · ");
    g.appendChild(m);

    const del = delai(f);
    if (del) {
      const e = document.createElement("span");
      e.className = "fil-echeance echeance-" + del.classe;
      e.textContent = del.texte;
      m.appendChild(document.createTextNode(" "));
      m.appendChild(e);
    }
    if (f.dernier) l.title = f.dernier;

    // Un clic sur le corps, c'est une pensée — le même canal que partout
    // ailleurs. On ne montre rien que le personnage ne sache déjà.
    g.onclick = () => {
      if (window.Entites && Entites.penser) Entites.penser(f.id, "fil", f.titre);
    };

    l.appendChild(g);
    l.appendChild(interrupteur(f));
    return l;
  }

  function rendre() {
    const zone = document.getElementById("liste-fils");
    if (!zone) return;
    zone.innerHTML = "";
    if (!fils.length) {
      zone.innerHTML = '<p class="objectif-vide">Rien ne court.</p>';
      return;
    }
    // Ce qu'on joue d'abord : c'est là que la main du joueur est attendue.
    const ordre = fils.slice().sort((a, b) => {
      if ((a.mode === "joue") !== (b.mode === "joue")) return a.mode === "joue" ? -1 : 1;
      const x = enJours(a.echeance), y = enJours(b.echeance);
      if (x === null) return 1;
      if (y === null) return -1;
      return x - y;
    });
    ordre.forEach((f) => zone.appendChild(ligne(f)));

    const compte = document.getElementById("fils-compte");
    if (compte) {
      const d = fils.filter((f) => f.mode === "delegue").length;
      compte.textContent = d + " délégué" + (d > 1 ? "s" : "") + ", " + (fils.length - d) + " joué";
    }
  }

  function charger() {
    fetch("/fils")
      .then((r) => r.json())
      .then((d) => { fils = d.fils || []; aujourdhui = d.aujourdhui || null; rendre(); })
      .catch(() => {});
  }

  window.addEventListener("DOMContentLoaded", charger);
  return { charger, rendre };
})();
