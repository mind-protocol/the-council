// regie.js — le siège de Corneille, et ce qu'il peut faire que les autres ne
// peuvent pas.
//
// Corneille n'incarne personne : c'est un siège de RÉGIE (`regie: true` dans
// `etat/joueurs.json`), sans fiche, sans tête, sans horloge. Il regarde. Ce
// module n'existe que pour lui, ne s'arme que si `/moi` le dit, et ne touche à
// rien d'autre : chez un joueur, il ne fait rien du tout.
//
// LE GESTE. Sur le plan du château, un visage touché ouvre un petit menu — une
// seule entrée, « Voir le personnage ». Ce qu'elle rend n'existe nulle part
// ailleurs sous cette forme : le serveur (`/regie/personnage/<id>`) recolle en
// un seul fil ce qu'un homme a dit et fait EN SCÈNE, les récits du narrateur
// qui le nomment, et ce qu'il a vécu HORS SCÈNE dans chacune de ses
// activations — l'appel qu'il a reçu, la tentative qu'il a écrite, ce que le
// monde en a fait, ce qu'il en a retenu.
//
// Ça se pose dans le fil, en bas, comme une lecture. Rien n'entre dans l'état,
// rien n'entre dans `flux.jsonl`, le temps ne bouge pas : ce fil-là vit dans
// cette page et meurt avec elle.
"use strict";
window.Regie = (() => {
  let actif = false;
  let menu = null;

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  const dateTexte = (d) => d
    ? d.annee + " AC · " + d.lune + "e lune, " + d.jour + "e jour" +
      (typeof d.minute === "number"
        ? " · " + Math.floor(d.minute / 60) + "h" + String(d.minute % 60).padStart(2, "0")
        : "")
    : "";

  // ---- le petit menu au bout du doigt --------------------------------------
  function fermer() {
    if (menu) { menu.remove(); menu = null; }
  }

  function ouvrirMenu(x, y, id, nom) {
    fermer();
    menu = document.createElement("div");
    menu.className = "regie-menu";
    menu.innerHTML = '<div class="regie-menu-tete">' + esc(nom || id) + "</div>" +
      '<button type="button" class="regie-menu-choix">Voir le personnage</button>';
    document.body.appendChild(menu);
    // rester dans l'écran : un visage au bord du plan ne pousse pas le menu dehors
    const b = menu.getBoundingClientRect();
    menu.style.left = Math.min(x, window.innerWidth - b.width - 8) + "px";
    menu.style.top = Math.min(y, window.innerHeight - b.height - 8) + "px";
    menu.querySelector(".regie-menu-choix").onclick = () => {
      fermer();
      voir(id, nom);
    };
  }

  // ---- le fil refait -------------------------------------------------------
  const TITRES = {
    replique: "en scène",
    geste: "en scène",
    narrateur: "le narrateur",
    appel: "on l'appelle",
    tentative: "ce qu'il tente",
    activite: "ce qu'il fait",
    resultat: "ce qu'il en retient",
    blocage: "ce qui l'arrête",
    issue: "l'issue",
  };

  async function voir(id, nom) {
    const zone = document.getElementById("fil-corps");
    if (!zone) return;
    const bloc = document.createElement("div");
    bloc.className = "regie-fil";
    bloc.innerHTML = '<div class="regie-fil-tete"><span>' + esc(nom || id) +
      '</span><em>on rassemble ce qu\'il a dit, fait et vécu…</em></div>';
    zone.appendChild(bloc);
    zone.scrollTo({ top: zone.scrollHeight, behavior: "smooth" });

    let d;
    try {
      const r = await fetch("/regie/personnage/" + encodeURIComponent(id));
      d = await r.json();
      if (d.erreur) throw new Error(d.erreur);
    } catch (e) {
      bloc.querySelector("em").textContent = "rien à lire : " + (e.message || e);
      return;
    }

    const entrees = d.entrees || [];
    let jour = "", session = "";
    let s = '<div class="regie-fil-tete"><span>' + esc(d.nom || id) + "</span><em>" +
      entrees.length + " moment(s) · " + d.scenes + " en scène · " +
      d.activations + " activation(s)</em>" +
      '<button type="button" class="regie-fil-fermer" title="Retirer du fil">×</button></div>';

    entrees.forEach((e) => {
      // Un jalon par journée du monde : sans lui, cent entrées se ressemblent.
      const j = e.date ? dateTexte({ annee: e.date.annee, lune: e.date.lune, jour: e.date.jour })
                       : "jour inconnu";
      if (j !== jour) {
        jour = j;
        s += '<div class="regie-jour">' + esc(j) +
          (e.date_incertaine ? " <i>(journée non lue dans le dossier)</i>" : "") + "</div>";
        session = "";
      }
      // Une activation s'annonce : ce qui suit s'est passé hors de toute salle.
      if (e.source === "activation" && e.session !== session) {
        session = e.session;
        s += '<div class="regie-activation">Hors scène — ' +
          esc(e.tache || "sans tâche nommée") + "</div>";
      }
      s += '<div class="regie-entree regie-' + esc(e.genre) + '">' +
        '<span class="regie-genre">' + esc(TITRES[e.genre] || e.genre) + "</span>" +
        '<span class="regie-qui">' + esc(e.qui || "") + "</span>" +
        '<div class="regie-texte">' + texte(e.texte) + "</div>" +
        (e.detail ? '<div class="regie-detail">' + texte(e.detail) + "</div>" : "") +
        (e.minutes ? '<div class="regie-detail">' + e.minutes + " minutes</div>" : "") +
        (e.lieu ? '<div class="regie-detail">' + esc(e.lieu) + "</div>" : "") +
        "</div>";
    });
    if (!entrees.length) {
      s += '<div class="regie-entree"><div class="regie-texte">Rien sur lui : ni parole ' +
        "en scène, ni activation. Il n'a pas encore vécu.</div></div>";
    }
    bloc.innerHTML = s;
    bloc.querySelector(".regie-fil-fermer").onclick = () => bloc.remove();
    // les noms restent cliquables comme partout ailleurs dans la chronique
    if (window.Entites) Entites.traiter(bloc);
    zone.scrollTo({ top: zone.scrollHeight, behavior: "smooth" });
  }

  // Les appuis en gras se lisent ici comme dans le reste du fil ; le reste est
  // échappé — ces textes viennent de sessions et ne sont pas du HTML.
  function texte(t) {
    return esc(t).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>");
  }

  // ---- « emmène-moi au moment où… » ---------------------------------------
  // Corneille le demande en clair dans son champ libre ; son MJ cherche
  // (`/regie/chercher?q=`, ou scripts/regie.py), tranche lequel des dix-sept
  // est le bon moment, et pousse UN item :
  //
  //   python scripts/append_flux.py --pour corneille \
  //     '{"type":"extrait","titre":"L\'arrivée de ser Steffon","de":7412,"a":7440}'
  //
  // La page va chercher la tranche et la repose dans le fil, telle qu'elle a
  // été jouée. Rien n'est rejoué dans la scène en cours : c'est une lecture
  // d'archive, posée à côté, avec sa date et son lieu.
  const GENRES = { replique: "réplique", geste: "geste", recit: "récit",
    breve: "brève", pensee: "pensée", vous: "le joueur", question: "question",
    reponse: "réponse", marque: "il s'est passé", salle: "la salle",
    coulisses: "coulisses", suites: "suites", ecrit: "au registre" };

  async function extrait(titre, de, a) {
    const zone = document.getElementById("fil-corps");
    if (!zone) return;
    const bloc = document.createElement("div");
    bloc.className = "regie-fil";
    bloc.innerHTML = '<div class="regie-fil-tete"><span>' + esc(titre || "Le moment") +
      "</span><em>on rouvre le fil à cet endroit…</em></div>";
    zone.appendChild(bloc);
    let d;
    try {
      const r = await fetch("/regie/extrait?de=" + (de | 0) + "&a=" + (a | 0));
      d = await r.json();
      if (d.erreur) throw new Error(d.erreur);
    } catch (e) {
      bloc.querySelector("em").textContent = "rien à rouvrir : " + (e.message || e);
      return;
    }
    let s = '<div class="regie-fil-tete"><span>' + esc(titre || "Le moment") +
      "</span><em>lignes " + d.de + " à " + d.a + " du fil</em>" +
      '<button type="button" class="regie-fil-fermer" title="Retirer du fil">×</button></div>';
    let jour = "";
    (d.items || []).forEach((it) => {
      if (!it.texte && it.type !== "salle") return;
      const j = it.date ? dateTexte(it.date) : "";
      if (j && j !== jour) { jour = j; s += '<div class="regie-jour">' + esc(j) +
        (it.lieu ? " · " + esc(it.lieu) : "") + "</div>"; }
      s += '<div class="regie-entree regie-' + esc(it.type) + '">' +
        '<span class="regie-genre">' + esc(GENRES[it.type] || it.type) + "</span>" +
        (it._nom ? '<span class="regie-qui">' + esc(it._nom) + "</span>" : "") +
        '<div class="regie-texte">' + texte(it.texte || "") + "</div></div>";
    });
    bloc.innerHTML = s;
    bloc.querySelector(".regie-fil-fermer").onclick = () => bloc.remove();
    if (window.Entites) Entites.traiter(bloc);
    zone.scrollTo({ top: zone.scrollHeight, behavior: "smooth" });
  }

  // ---- l'armement ----------------------------------------------------------
  // En CAPTURE, et avant tout le monde : plan.js branche ses écouteurs sur les
  // éléments eux-mêmes (en remontée). Sans capture, la pensée s'ouvrirait sous
  // le menu, ou le personnage se mettrait en marche vers une autre salle.
  function armer() {
    document.body.classList.add("regie");
    document.addEventListener("click", (e) => {
      if (!actif) return;
      const g = e.target.closest && e.target.closest(".tache-gens");
      if (!g) { fermer(); return; }
      e.stopPropagation();
      e.preventDefault();
      ouvrirMenu(e.clientX + 4, e.clientY + 4, g.dataset.id, g.dataset.nom);
    }, true);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") fermer(); }, true);
    window.addEventListener("blur", fermer);
  }

  window.addEventListener("DOMContentLoaded", () => {
    // `/moi` est déjà appelé par bus.js, mais on ne s'accroche pas à son
    // ordonnancement : deux appels à une lecture de fichier ne coûtent rien.
    fetch("/moi").then((r) => r.json()).then((d) => {
      if (!d || !d.moi || !d.moi.regie) return;
      actif = true;
      armer();
    }).catch(() => {});
  });

  // Les deux items que le MJ de la régie peut pousser. Enregistrés dans tous
  // les cas : un item de régie n'est servi qu'à un siège de régie (`pour`), et
  // un fil qui ne sait pas le rendre laisserait un trou muet.
  if (window.Bus) {
    Bus.enregistrer("extrait", (it) => extrait(it.titre || it.texte, it.de, it.a));
    Bus.enregistrer("dossier", (it) => voir(it.personnage_id || it.qui, it.nom));
  }

  return { voir, extrait, actif: () => actif };
})();
