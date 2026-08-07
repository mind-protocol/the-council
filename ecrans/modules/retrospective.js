// retrospective.js — les albums de la partie.
// Le rail latéral porte deux boutons ; chacun ouvre un plein écran où les
// pièces défilent, avec le moment qu'elles fixent et leur date.
//
//   • les planches   — /retrospective (etat/retrospective.json), images sur
//     /captures/<fichier>. Ce qu'on a vu.
//   • les médailles  — /medailles (etat/medailles.json). Les rubans décernés
//     en Coulisses : hors univers de bout en bout, aucun PNJ n'en sait rien.
//
// Ce n'est pas un module de flux : rien ici n'entre dans la scène, rien n'en
// sort. Le temps ne bouge pas, la fiction non plus — on regarde en arrière.
"use strict";
window.Retrospective = (() => {
  let ouverte = null, album = null, i = 0;
  const cache = {};

  const texteDate = (d) => {
    if (!d) return "";
    let t = d.annee + " AC, " + d.lune + "e lune, " + d.jour + "e jour";
    if (d.minute != null) {
      const h = Math.floor(d.minute / 60), mn = d.minute % 60;
      t += " — " + h + "h" + String(mn).padStart(2, "0");
    }
    return t;
  };

  // Chaque album dit où il se sert, comment il se nomme, et comment se dessine
  // une de ses pièces. Le reste du module ne sait rien de leur contenu.
  const ALBUMS = {
    planches: {
      route: "/retrospective", clef: "planches",
      bouton: (n) => "Revoir la partie — " + n + " planches",
      vide: "Rien à revoir encore.",
      // Une planche sans `fichier` est un moment qu'on n'a pas encore
      // illustré : il garde sa place dans l'album, à sa date, avec un cadre
      // vide. C'est un trou honnête, et il se comble le jour où l'image existe.
      carte: (p) =>
        (p.fichier
          ? '<img class="retro-image" alt="" src="/captures/' + encodeURIComponent(p.fichier) + '">'
          : '<div class="retro-manque">Cette planche n\'a pas encore été peinte.</div>') +
        '<div class="retro-legende">' +
          '<div class="retro-quand">' + texteDate(p.date) +
            (p.moment ? " · " + p.moment : "") + "</div>" +
          '<div class="retro-titre">' + (p.titre || "") + "</div>" +
          '<div class="retro-texte">' + (p.texte || "") + "</div>" +
          (p.lieu ? '<div class="retro-lieu">' + p.lieu + "</div>" : "") +
          // Pourquoi ce moment-là et pas un autre : la seule chose de l'album
          // qui ne se voit pas sur l'image, donc elle s'affiche en clair.
          (p.pourquoi
            ? '<div class="retro-pourquoi"><p>' + p.pourquoi + "</p></div>"
            : "") +
        "</div>",
    },
    medailles: {
      route: "/medailles", clef: "medailles",
      bouton: (n) => "Le cabinet des médailles — " + n,
      vide: "Aucun ruban décerné.",
      carte: (m) =>
        '<div class="retro-ruban">' +
          '<div class="ruban-embleme">' + (m.embleme || "🎖️") + "</div>" +
          '<div class="ruban-titre">' + (m.medaille || "") + "</div>" +
          '<div class="ruban-a">' + (m.recipiendaire || "") + "</div>" +
          '<div class="ruban-citation">' + (m.citation || "") + "</div>" +
        "</div>" +
        '<div class="retro-legende">' +
          '<div class="retro-quand">' + texteDate(m.date) + "</div>" +
          (m.pour ? '<div class="retro-texte">' + m.pour + "</div>" : "") +
          (m.lieu ? '<div class="retro-lieu">Décernée : ' + m.lieu + "</div>" : "") +
        "</div>",
    },
  };

  async function charger(nom) {
    if (cache[nom]) return cache[nom];
    const a = ALBUMS[nom];
    try {
      const r = await fetch(a.route);
      cache[nom] = (await r.json())[a.clef] || [];
    } catch (e) { cache[nom] = []; }
    return cache[nom];
  }

  function rendre() {
    if (!ouverte) return;
    const liste = cache[album], p = liste[i];
    if (!p) return;
    ouverte.querySelector(".retro-plaque").innerHTML = ALBUMS[album].carte(p);
    ouverte.querySelector(".retro-compte").textContent = (i + 1) + " / " + liste.length;
    ouverte.querySelectorAll(".retro-pastille").forEach((b, n) =>
      b.classList.toggle("ici", n === i));
  }

  const aller = (n) => {
    const liste = cache[album] || [];
    if (!liste.length) return;
    i = (n + liste.length) % liste.length;
    rendre();
  };

  function clavier(e) {
    if (!ouverte) return;
    if (e.key === "Escape") fermer();
    else if (e.key === "ArrowRight" || e.key === " ") { aller(i + 1); e.preventDefault(); }
    else if (e.key === "ArrowLeft") aller(i - 1);
  }

  function fermer() {
    if (!ouverte) return;
    ouverte.remove();
    ouverte = null;
    album = null;
    document.removeEventListener("keydown", clavier);
  }

  async function ouvrir(nom, id) {
    if (!ALBUMS[nom]) { id = nom; nom = "planches"; }   // ouvrir(id) historique
    const liste = await charger(nom);
    if (!liste.length) return;
    fermer();
    album = nom;
    i = Math.max(0, liste.findIndex((p) => p.id === id));
    const d = document.createElement("div");
    d.id = "retro";
    d.className = "retro-" + nom;
    d.innerHTML =
      '<div class="retro-cadre">' +
        '<button class="retro-fermer" title="Fermer">×</button>' +
        '<button class="retro-prec" title="Précédente">‹</button>' +
        '<div class="retro-plaque"></div>' +
        '<button class="retro-suiv" title="Suivante">›</button>' +
        '<div class="retro-pied">' +
          '<span class="retro-pastilles">' +
            liste.map(() => '<button class="retro-pastille"></button>').join("") +
          "</span>" +
          '<span class="retro-compte"></span>' +
        "</div>" +
      "</div>";
    document.body.appendChild(d);
    ouverte = d;
    d.querySelector(".retro-fermer").addEventListener("click", fermer);
    d.querySelector(".retro-prec").addEventListener("click", () => aller(i - 1));
    d.querySelector(".retro-suiv").addEventListener("click", () => aller(i + 1));
    d.querySelectorAll(".retro-pastille").forEach((b, n) =>
      b.addEventListener("click", () => aller(n)));
    // Le fond ferme, le cadre non : on ne perd pas sa place en cliquant l'image.
    d.addEventListener("click", (e) => { if (e.target === d) fermer(); });
    document.addEventListener("keydown", clavier);
    rendre();
  }

  window.addEventListener("DOMContentLoaded", async () => {
    const corps = document.getElementById("liste-retrospective");
    if (!corps) return;
    for (const nom of ["planches", "medailles"]) {
      const liste = await charger(nom);
      if (!liste.length) {
        const p = document.createElement("p");
        p.className = "objectif-vide";
        p.textContent = ALBUMS[nom].vide;
        corps.appendChild(p);
        continue;
      }
      const b = document.createElement("button");
      b.className = "retro-ouvrir";
      b.id = "retro-ouvrir-" + nom;
      b.textContent = ALBUMS[nom].bouton(liste.length);
      b.addEventListener("click", () => ouvrir(nom));
      corps.appendChild(b);
    }
  });

  return { ouvrir, fermer };
})();
