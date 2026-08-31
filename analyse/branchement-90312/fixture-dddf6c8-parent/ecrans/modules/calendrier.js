// calendrier.js — « Les jours », l'échelle du décor qui répond à « qu'est-ce
// que j'ai devant moi, et à quelle heure ».
//
// POURQUOI. Un rendez-vous, dans cette partie, n'existe nulle part en tant que
// tel : c'est un `programme` daté à la minute, un pli qu'on attend, un fil qui
// tombe, un dessein qui a un terme. Quatre tables, aucune vue. Résultat connu :
// un rendez-vous manqué ne se voyait qu'en relisant la feuille de reprise, et
// celui du 23e chez Rulf s'est perdu comme ça — l'homme a attendu une partie de
// la nuit en bas. Cette échelle met les quatre sur une seule règle horaire.
//
// CE QU'ELLE NE FAIT PAS. Elle ne montre que ce où le siège FIGURE (le tri est
// fait au serveur, /calendrier) : le plan d'un autre n'est pas un agenda. Elle
// ne fait pas avancer le temps et ne propose aucun choix — on peut demander où
// en est une affaire, hors fiction, comme dans « Vos desseins ».
//
// DEUX VUES. La GRILLE (par défaut) : des carreaux, un par heure et par jour,
// teintés de la routine — où l'on est à cette heure-là — la case courante en
// braise, ce qui est passé éteint. L'AGENDA : la journée sur une règle
// continue, pour lire le détail. Le même état, deux lectures.
//
// ÉCRIRE DANS UNE CASE — c'est le joueur qui tient la plume. Un clic sur un
// carreau ouvre le champ, Entrée écrit, Échap annule (POST /agenda). Personne
// ne l'entend, l'horloge ne bouge pas, et ce n'est ni une parole ni un acte :
// on écrit dans son propre calendrier, pas devant la salle. Mais ça ne meurt
// pas dans un fichier — la case tombe dans l'inbox du siège, le guetteur du MJ
// sonne, et c'est à lui de la porter dans le monde (l'homme qu'on fait
// chercher, le `programme` daté, le pli qui part).
"use strict";
window.Calendrier = (() => {
  const MIN_PAR_JOUR = 1440;
  const PX_PAR_MIN = 0.62;          // ~14 h de journée tiennent dans un écran
  const GENRES = {
    "rendez-vous": { nom: "Rendez-vous", classe: "g-rdv" },
    "echeance":    { nom: "Échéance",    classe: "g-echeance" },
    "pli":         { nom: "Courrier",    classe: "g-pli" },
    "fil":         { nom: "Ce qui court", classe: "g-fil" },
    "dessein":     { nom: "Dessein",     classe: "g-dessein" },
  };

  let donnees = null, charge = false;
  // ce qu'il reste à caler une fois la journée dans la page (voir caler())
  let aCaler = null;
  // la vue retenue d'une session à l'autre — on rouvre là où on avait laissé
  let mode = (() => {
    try { return localStorage.getItem("conseil-calendrier") || "grille"; }
    catch (e) { return "grille"; }
  })();
  let detaille = null;   // l'entrée dépliée sous la grille, s'il y en a une

  const heure = (m) => (m === null || m === undefined) ? ""
    : (Math.floor(m / 60) + "h" + String(m % 60).padStart(2, "0"));
  const MOIS = ["", "1re", "2e", "3e", "4e", "5e", "6e", "7e", "8e", "9e", "10e", "11e", "12e"];
  const dateTexte = (d) => d ? (MOIS[d.lune] || d.lune + "e") + " lune, " + d.jour + "e jour" : "";
  function nomJour(ecart, d) {
    if (ecart === -1) return "Hier";
    if (ecart === 0) return "Aujourd'hui";
    if (ecart === 1) return "Demain";
    return "Dans " + ecart + " jours";
  }

  function hote() { return document.getElementById("calendrier"); }

  // Une entrée : ce qu'on doit lire d'un coup d'œil, et le reste au clic.
  function carte(e, avecHeure) {
    const g = GENRES[e.genre] || GENRES.echeance;
    const a = document.createElement("article");
    a.className = "cal-entree " + g.classe + (e.tenu ? " tenu" : "");
    const t = document.createElement("div");
    t.className = "cal-titre";
    if (avecHeure && e.minute !== null) {
      const h = document.createElement("span");
      h.className = "cal-heure";
      h.textContent = heure(e.minute);
      t.appendChild(h);
    }
    t.appendChild(document.createTextNode(e.titre || "—"));
    a.appendChild(t);

    const marge = document.createElement("div");
    marge.className = "cal-marge";
    const bout = (txt, cls) => {
      if (!txt) return;
      const s = document.createElement("span");
      if (cls) s.className = cls;
      s.textContent = txt;
      marge.appendChild(s);
    };
    bout(g.nom, "cal-genre");
    if (e.avec && e.avec.length) bout("avec " + e.avec.join(", "));
    if (e.lieu) bout(String(e.lieu).replace(/-/g, " "));
    if (e.tenu) bout(e.genre === "pli" ? "remis" : "fait", "cal-tenu");
    if (marge.childNodes.length) a.appendChild(marge);

    if (e.detail) {
      const p = document.createElement("p");
      p.className = "cal-detail";
      p.textContent = e.detail;
      a.appendChild(p);
      if (window.Entites) Entites.traiter(p);
    }

    // Hors fiction, comme le mode Question : personne ne l'entend, le temps ne
    // bouge pas. On ne rouvre pas une affaire depuis un agenda — on demande.
    const point = document.createElement("button");
    point.className = "cal-point";
    point.textContent = "Où en est-on ?";
    point.onclick = (ev) => {
      ev.stopPropagation();
      if (point.disabled) return;
      point.disabled = true;
      point.textContent = "Demandé…";
      Bus.poster({
        type: "libre", mode: "question", cible: e.id, cible_type: "evenement",
        texte: "Où en est « " + (e.titre || e.id) + " » (" + dateTexte(e.date) +
          (e.minute !== null ? ", " + heure(e.minute) : "") + ") ? " +
          "Relis l'état, dis-moi ce qui tient, ce qui a bougé, et ce que j'ai à faire d'ici là.",
      });
    };
    a.appendChild(point);
    return a;
  }

  // LA JOURNÉE COURANTE — la seule qui mérite une règle horaire. Le fond est sa
  // routine (où elle est à cette heure-là) : une heure déjà pavée n'est pas une
  // heure libre, et c'est ce qui manque à une simple liste.
  function journee(j) {
    const box = document.createElement("div");
    box.className = "cal-journee";
    const rule = document.createElement("div");
    rule.className = "cal-rule";
    rule.style.height = (MIN_PAR_JOUR * PX_PAR_MIN) + "px";

    (donnees.bandes || []).forEach((b) => {
      const d = document.createElement("div");
      d.className = "cal-bande" + (b.ferme ? " fermee" : "");
      d.style.top = (b.de * PX_PAR_MIN) + "px";
      d.style.height = Math.max(1, (b.a - b.de) * PX_PAR_MIN) + "px";
      d.title = (b.lieu || b.salle || "") + " — " + heure(b.de) + " à " + heure(b.a);
      const n = document.createElement("span");
      n.textContent = (b.lieu || b.salle || "").replace(/,.*$/, "");
      d.appendChild(n);
      rule.appendChild(d);
    });

    for (let h = 0; h < 24; h += 2) {
      const l = document.createElement("div");
      l.className = "cal-graduation";
      l.style.top = (h * 60 * PX_PAR_MIN) + "px";
      l.dataset.h = h + "h";
      rule.appendChild(l);
    }

    const datees = j.entrees.filter((e) => e.minute !== null);
    const flottantes = j.entrees.filter((e) => e.minute === null);
    // Trois hommes rendent leur page à sept heures, et c'est le cas ORDINAIRE
    // ici : une journée d'Aurore est faite de rendez-vous à la même minute.
    // Épingler chaque carte à son heure les empile l'une SOUS l'autre, invisibles.
    // On pose donc à l'heure dite, puis on repousse ce qui se chevauche vers le
    // bas — l'heure reste lisible dans la carte, et rien ne se cache.
    const poses = datees.map((e) => {
      const d = document.createElement("div");
      d.className = "cal-pose";
      d.dataset.voulu = e.minute * PX_PAR_MIN;
      d.style.top = (e.minute * PX_PAR_MIN) + "px";
      d.appendChild(carte(e, true));
      rule.appendChild(d);
      return d;
    });
    aCaler = { rule, poses };

    if (donnees.aujourdhui && typeof donnees.aujourdhui.minute === "number") {
      const now = document.createElement("div");
      now.className = "cal-maintenant";
      now.style.top = (donnees.aujourdhui.minute * PX_PAR_MIN) + "px";
      now.dataset.h = heure(donnees.aujourdhui.minute);
      rule.appendChild(now);
    }

    if (flottantes.length) {
      const f = document.createElement("div");
      f.className = "cal-flottantes";
      const t = document.createElement("div");
      t.className = "cal-flottantes-titre";
      t.textContent = "Dans la journée, sans heure dite";
      f.appendChild(t);
      flottantes.forEach((e) => f.appendChild(carte(e, false)));
      box.appendChild(f);
    }
    box.appendChild(rule);
    return box;
  }

  // ---- LA GRILLE ---------------------------------------------------------
  // Des carreaux : une colonne par jour, une ligne par heure. Ce qu'un agenda
  // continu ne donne pas et qu'on vient chercher ici : d'un coup d'œil, où sont
  // les trous. Un creux se VOIT dans une grille ; dans une liste, il faut le
  // calculer.
  const clefCase = (d, h) => [d.annee, d.lune, d.jour, h].join("-");

  // La routine teinte les carreaux : chaque salle où elle passe sa journée a sa
  // couleur, la même d'un jour sur l'autre. C'est ce qui fait qu'on lit la
  // journée sans lire un mot — la roukerie au matin, l'archive l'après-midi.
  function salles() {
    const vues = [];
    (donnees.bandes || []).forEach((b) => {
      const s = b.salle || b.lieu;
      if (s && vues.indexOf(s) < 0) vues.push(s);
    });
    return vues;
  }
  function bandeDe(h) {
    const m = h * 60 + 30;   // le milieu de l'heure tranche les chevauchements
    return (donnees.bandes || []).find((b) => m >= b.de && m < b.a) || null;
  }

  function chip(e) {
    const g = GENRES[e.genre] || GENRES.echeance;
    const c = document.createElement("button");
    c.className = "cal-chip " + g.classe + (e.tenu ? " tenu" : "");
    c.title = (e.minute !== null ? heure(e.minute) + " — " : "") + (e.titre || "");
    c.textContent = (e.minute !== null ? heure(e.minute) + " " : "") +
      (e.titre || "").replace(/^\W+/, "");
    c.onclick = (ev) => {
      ev.stopPropagation();
      detaille = (detaille === e.id) ? null : e.id;
      dessiner();
    };
    return c;
  }

  // Le mémo d'une case : un clic ouvre, Échap referme, la perte du focus écrit.
  function ouvrirMemo(cel, d, h, texte) {
    if (cel.querySelector("textarea")) return;
    const t = document.createElement("textarea");
    t.className = "cal-memo-champ";
    t.value = texte || "";
    t.placeholder = "ce que vous comptez y faire…";
    t.rows = 2;
    let fait = false;
    const fermer = (ecrire) => {
      if (fait) return;
      fait = true;
      if (!ecrire) { dessiner(); return; }
      fetch("/agenda", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date: d, heure: h, texte: t.value }),
      }).then((r) => r.json()).then((r) => {
        if (r && r.notes) donnees.notes = r.notes;
        dessiner();
      }).catch(() => dessiner());
    };
    t.onkeydown = (ev) => {
      if (ev.key === "Escape") { ev.stopPropagation(); fermer(false); }
      // Entrée écrit, Maj+Entrée passe à la ligne : un mémo tient en une ligne
      if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); fermer(true); }
      ev.stopPropagation();   // le champ libre du fil ne doit pas happer la frappe
    };
    t.onblur = () => fermer(true);
    cel.appendChild(t);
    t.focus();
    t.setSelectionRange(t.value.length, t.value.length);
  }

  function grille() {
    const jours = (donnees.jours || []);
    const maintenant = donnees.aujourdhui || null;
    const hMaintenant = maintenant && typeof maintenant.minute === "number"
      ? Math.floor(maintenant.minute / 60) : null;
    // On n'affiche pas les vingt-quatre heures : les heures où il ne se passe
    // jamais rien mangent l'écran. On borne sur ce qui est écrit, la nuit comprise
    // quand quelque chose y tombe.
    let bas = 5, haut = 22;
    jours.forEach((j) => j.entrees.forEach((e) => {
      if (e.minute === null) return;
      const h = Math.floor(e.minute / 60);
      bas = Math.min(bas, h); haut = Math.max(haut, h);
    }));
    (donnees.notes || []).forEach((n) => {
      bas = Math.min(bas, n.heure); haut = Math.max(haut, n.heure);
    });
    if (hMaintenant !== null) { bas = Math.min(bas, hMaintenant); haut = Math.max(haut, hMaintenant); }

    const memos = {};
    (donnees.notes || []).forEach((n) => { memos[clefCase(n.date, n.heure)] = n.texte; });
    const listeSalles = salles();

    const g = document.createElement("div");
    g.className = "cal-grille";
    g.style.setProperty("--cols", jours.length);

    const coin = document.createElement("div");
    coin.className = "cal-g-coin";
    g.appendChild(coin);
    jours.forEach((j) => {
      const t = document.createElement("div");
      t.className = "cal-g-jour" + (j.ecart === 0 ? " courant" : "") +
        (j.ecart < 0 ? " passe" : "");
      t.innerHTML = "<b>" + (j.ecart === 0 ? "Auj." : j.ecart === -1 ? "Hier"
        : j.ecart === 1 ? "Demain" : "+" + j.ecart) + "</b><span>" +
        j.date.jour + "e</span>";
      t.title = dateTexte(j.date);
      g.appendChild(t);
    });

    // la ligne du haut : ce qui tombe dans la journée sans heure dite
    const sansHeure = jours.some((j) => j.entrees.some((e) => e.minute === null));
    if (sansHeure) {
      const l = document.createElement("div");
      l.className = "cal-g-heure sans";
      l.textContent = "sans h.";
      g.appendChild(l);
      jours.forEach((j) => {
        const cel = document.createElement("div");
        cel.className = "cal-case sans-heure" + (j.ecart < 0 ? " passe" : "");
        j.entrees.filter((e) => e.minute === null).forEach((e) => cel.appendChild(chip(e)));
        g.appendChild(cel);
      });
    }

    for (let h = bas; h <= haut; h++) {
      const l = document.createElement("div");
      l.className = "cal-g-heure";
      l.textContent = h + "h";
      const b = bandeDe(h);
      if (b) l.title = b.lieu || b.salle || "";
      g.appendChild(l);
      jours.forEach((j) => {
        const cel = document.createElement("div");
        const passe = j.ecart < 0 || (j.ecart === 0 && hMaintenant !== null && h < hMaintenant);
        const ici = j.ecart === 0 && h === hMaintenant;
        cel.className = "cal-case" + (passe ? " passe" : "") + (ici ? " courante" : "");
        const b = bandeDe(h);
        if (b) {
          const i = listeSalles.indexOf(b.salle || b.lieu);
          if (i >= 0) cel.dataset.salle = String(i % 6);
          cel.title = (b.lieu || b.salle || "") + " — " + h + "h";
        }
        j.entrees.filter((e) => e.minute !== null && Math.floor(e.minute / 60) === h)
          .forEach((e) => cel.appendChild(chip(e)));
        const memo = memos[clefCase(j.date, h)];
        if (memo) {
          const m = document.createElement("div");
          m.className = "cal-memo";
          m.textContent = memo;
          cel.appendChild(m);
        }
        // écrire dedans : hors fiction, voir l'en-tête du fichier
        cel.onclick = () => ouvrirMemo(cel, j.date, h, memo || "");
        cel.title = (cel.title || "") + (memo ? "" : " — cliquer pour écrire");
        g.appendChild(cel);
      });
    }

    const enveloppe = document.createElement("div");
    enveloppe.className = "cal-grille-boite";
    enveloppe.appendChild(g);

    // Une main tendue, et une seule ligne : le carreau ne dit pas de lui-même
    // qu'on peut écrire dedans, et un joueur qui ne le sait pas ne l'essaiera
    // jamais.
    const dit = document.createElement("p");
    dit.className = "cal-dit";
    dit.textContent = "Touchez une case pour y écrire de votre main — Entrée inscrit, " +
      "Échap laisse. Personne ne l'entend, l'heure ne bouge pas ; le MJ en est prévenu.";
    enveloppe.appendChild(dit);

    // la légende des couleurs : où elle est, heure par heure
    if (listeSalles.length) {
      const leg = document.createElement("div");
      leg.className = "cal-legende";
      listeSalles.slice(0, 6).forEach((s, i) => {
        const b = (donnees.bandes || []).find((x) => (x.salle || x.lieu) === s);
        const e = document.createElement("span");
        e.dataset.salle = String(i % 6);
        e.textContent = ((b && b.lieu) || s).replace(/,.*$/, "");
        leg.appendChild(e);
      });
      enveloppe.appendChild(leg);
    }

    // le détail de la pièce touchée, déplié sous la grille
    if (detaille) {
      let trouve = null;
      jours.forEach((j) => j.entrees.forEach((e) => { if (e.id === detaille) trouve = e; }));
      if (trouve) {
        const d = document.createElement("div");
        d.className = "cal-detail-boite";
        d.appendChild(carte(trouve, true));
        enveloppe.appendChild(d);
      }
    }
    return enveloppe;
  }

  // LE CALAGE — deuxième passe, une fois les cartes DANS la page : on ne connaît
  // la hauteur d'une carte qu'une fois posée. Elle se fait ici, synchrone, et
  // non dans un requestAnimationFrame : un onglet qui n'est pas à l'écran ne
  // reçoit pas de frame, et l'agenda restait alors empilé sur lui-même.
  function caler() {
    if (!aCaler) return;
    const { rule, poses } = aCaler;
    aCaler = null;
    let bas = -1e9;
    poses.forEach((d) => {
      const voulu = Number(d.dataset.voulu);
      const y = Math.max(voulu, bas + 8);
      d.style.top = y + "px";
      if (y > voulu + 2) d.classList.add("repousse");
      bas = y + d.getBoundingClientRect().height;
    });
    // la règle s'allonge si la journée déborde de ses vingt-quatre heures
    rule.style.height = Math.max(MIN_PAR_JOUR * PX_PAR_MIN, bas + 20) + "px";
  }

  function dessiner() {
    const h = hote();
    if (!h) return;
    h.innerHTML = "";
    if (!donnees) { h.innerHTML = '<p class="cal-vide">…</p>'; return; }
    const corps = document.createElement("div");
    corps.className = "cal-corps";

    const tete = document.createElement("div");
    tete.className = "cal-tete";
    const quand = document.createElement("span");
    quand.textContent = (donnees.nom ? donnees.nom + " — " : "") +
      dateTexte(donnees.aujourdhui) +
      (donnees.aujourdhui && typeof donnees.aujourdhui.minute === "number"
        ? ", " + heure(donnees.aujourdhui.minute) : "");
    tete.appendChild(quand);
    [["grille", "Carreaux"], ["agenda", "Journée"]].forEach(([id, nom]) => {
      const b = document.createElement("button");
      b.className = "cal-mode" + (mode === id ? " actif" : "");
      b.textContent = nom;
      b.onclick = () => {
        mode = id;
        try { localStorage.setItem("conseil-calendrier", id); } catch (e) {}
        dessiner();
      };
      tete.appendChild(b);
    });
    corps.appendChild(tete);

    if (mode === "grille") {
      corps.appendChild(grille());
      h.appendChild(corps);
      return;
    }

    (donnees.jours || []).forEach((j) => {
      // un jour vide à plus de trois jours ne mérite pas sa ligne
      if (!j.entrees.length && j.ecart !== 0 && j.ecart > 3) return;
      const sec = document.createElement("section");
      sec.className = "cal-jour" + (j.ecart === 0 ? " courant" : "") +
        (j.ecart < 0 ? " passe" : "");
      const t = document.createElement("div");
      t.className = "cal-jour-titre";
      t.innerHTML = "<b>" + nomJour(j.ecart, j.date) + "</b> " +
        "<span>" + dateTexte(j.date) + "</span>" +
        (j.entrees.length ? "" : " <i>rien de pris</i>");
      sec.appendChild(t);
      if (j.ecart === 0) {
        sec.appendChild(journee(j));
      } else {
        j.entrees.forEach((e) => sec.appendChild(carte(e, true)));
      }
      corps.appendChild(sec);
    });
    h.appendChild(corps);
    caler();
    // on s'ouvre sur l'heure qu'il est, pas sur minuit
    const now = h.querySelector(".cal-maintenant");
    if (now && now.scrollIntoView) {
      try { now.scrollIntoView({ block: "center" }); } catch (e) {}
    }
  }

  function charger() {
    if (charge) return;
    charge = true;
    fetch("/calendrier").then((r) => r.json()).then((d) => {
      if (!d || !d.jours) throw new Error("route absente");
      donnees = d;
      dessiner();
    }).catch(() => {
      charge = false;
      const h = hote();
      if (h && !donnees) {
        h.innerHTML = '<p class="cal-vide">Le calendrier est hors d\'atteinte — ' +
          "le serveur du jeu doit être relancé.</p>";
      }
    });
  }
  function relire() { charge = false; charger(); }

  window.addEventListener("DOMContentLoaded", () => {
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "calendrier", nom: "Les jours", hote: "calendrier", ordre: 5.5,
        dispo: () => true,
        reparu: () => { charger(); },
      });
    }
    // Carreaux ou journée : deux façons de regarder le même temps, et l'on ne
    // revient pas dans l'une en croyant revenir dans l'autre.
    if (window.Nav) {
      Nav.enregistrer("calendrier", {
        clefs: ["jours"],
        etat: () => ({ jours: mode }),
        poser: (p) => {
          const m = p.jours === "agenda" ? "agenda" : "grille";
          if (m === mode) return true;
          mode = m;
          try { localStorage.setItem("conseil-calendrier", m); } catch (e) {}
          if (!donnees) return false;
          dessiner();
          return true;
        },
      });
    }
  });

  // Le temps a bougé, une affaire s'est close, un pli est remis : l'état sur
  // disque a suivi, on relit. Trois signaux valent mieux qu'un rafraîchissement
  // périodique — le calendrier ne doit pas travailler quand rien ne bouge.
  ["objectif", "ecrit", "marque"].forEach((t) => {
    if (window.Bus && Bus.enregistrer) Bus.enregistrer(t, () => setTimeout(relire, 400));
  });

  return { charger, relire };
})();
