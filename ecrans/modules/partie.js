// partie.js — « Le conseil », une échelle du décor : la partie en cartes.
//
// La table peinte dit OÙ porte la guerre, l'échiquier dit COMMENT le plan se
// tient ; le conseil de guerre dit CONTRE QUI, et avec quoi, à ce jour. C'est
// la partie de mj-partie.md vue du siège qui la joue. LES MOTS SONT CEUX DE
// L'ÉCHIQUIER (docs/echiquier.md), donc ceux des cahiers d'affaire : on ne
// forge pas ici un second lexique sur les mêmes emojis, comme on l'a fait un
// temps — 🗝️ voulait alors dire « clef » sur un onglet et « ordre » sur
// l'autre, et « ordre » ne désignait rien. Ce qui reste dehors, c'est la
// tuyauterie du greffier : gel, deck, tour. Sept cartes, et leur signe :
//
//   🎯 l'état cible  ce qu'on veut voir vrai ; la colonne de gauche
//   🔒 le verrou     ce que l'autre camp tient contre nous ; en tête d'un front
//   🗝️ la clef       ce qu'on a posé contre un verrou ; sous lui, dans la pile
//   ❓ la question   ce qu'un conseiller demande avant d'exécuter ; sur la clef
//   ⚔️ l'action      ce qui a été fait, par qui
//   📦 la pièce      ce qu'on engage — 🐉 ⛵ ⚔️ 💰 👤 🏰 en sous-signe
//   💥 la frappe     ce qui vient sur une de nos pièces
//
// TOUT EST UNE CARTE, et l'état se lit à sa forme, jamais à un chiffre isolé :
// nette = libre · sous un front = posée · pointillée « dans 4 j » = en route ·
// grisée = se remet · barrée = détruite. Le deck est sous les yeux en
// permanence : c'est de là que tout part.
//
// v1 : ON JOUE. Un seul geste, toujours le même — ON PREND UNE CARTE ET ON LA
// POSE SUR UNE AUTRE. Ce que ça veut dire, c'est la carte du dessous qui le
// dit : une pièce sur un verrou pose une clef, sur une de nos clefs elle la
// renforce, sur une frappe elle protège. Une carte à nous rendue au deck est
// reprise, et ses pièces se remettent. L'écran ne connaît AUCUN nom de coup :
// il envoie « j'ai posé ceci sur cela » et le greffier traduit
// (scripts/noyau/partie_gestes.py).
//
// Ce qui n'est pas jouable ne s'allume pas quand on tient une carte : c'est
// comme ça que la règle s'apprend, sans avoir à la lire. Un refus n'est jamais
// un silence — il revient en une phrase, sous la barre.
//
// PAS DE BROUILLARD SUR CE PLATEAU (décidé le 3.9). Il reste entier dans la
// CHRONIQUE — ce que le joueur apprend d'un homme essoufflé, d'une rumeur
// fausse, d'un chiffre arrondi. Mais le plateau n'est pas dans la fiction :
// c'est l'outil du joueur, et aux échecs on voit les pièces d'en face. On
// servait naguère l'ennemi seulement par ce qu'il avait posé contre nous, et
// l'adversaire jouait alors des coups que personne ne voyait jamais.
//
// CE QUI A CHANGÉ porte une marque, et elle est EXACTE : le jsonl est
// append-only, donc le dernier numéro de ligne vu suffit à dire ce qui est
// neuf. La marque ne part pas au bout de trois secondes — elle tient jusqu'à
// votre prochain coup, donc elle survit à deux jours d'absence.
//
// Rien ici ne touche etat/ : le seul fichier qui s'allonge est le jsonl de la
// partie. Ce qu'un coup change dans le monde reste au MJ.
"use strict";
window.PartieVue = (() => {
  let vue = null;
  let charge = false;
  let dernier = "";
  let tenue = null;      // la carte qu'on a en main pendant le glissé
  let mot = "";          // ce que le greffier vient de dire, ou son refus
  let motMauvais = false;

  const hote = () => document.getElementById("partie");
  const el = (tag, cls, texte) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texte != null) e.textContent = texte;
    return e;
  };

  // ---- une carte : le signe seul, et le texte AU SURVOL --------------------
  // Le plateau était un mur de prose : vingt-neuf pavés de trois lignes, dont
  // une question de deux cents caractères qui tombait à trois mots par ligne
  // dans une colonne de 210 px. Le texte n'a pas disparu — il est là où on va
  // le chercher : sur la carte qu'on regarde, et une seule à la fois.
  function carte(c) {
    const d = el("div", "pc-carte pc-" + c.type + " pc-app-" + (c.apparence || "libre")
                        + " pc-camp-" + (c.camp || "noir"));
    d.dataset.id = c.id;
    d.appendChild(el("span", "pc-type", c.emoji));
    const t = el("div", "pc-texte");
    t.appendChild(el("div", "pc-titre", c.titre || ""));
    if (c.corps) t.appendChild(el("div", "pc-corps", c.corps));
    if (c.pied && (c.pied.gauche || c.pied.droite)) {
      const p = el("div", "pc-pied");
      p.appendChild(el("span", "pc-pied-g", c.pied.gauche || ""));
      p.appendChild(el("span", "pc-pied-d", c.pied.droite || ""));
      t.appendChild(p);
    }
    d.appendChild(t);
    if (c.neuf) d.classList.add("pc-neuf");
    if (c.visee) d.appendChild(el("span", "pc-visee", "💥"));
    if (c.type === "piece" && c.source) d.dataset.source = c.source;
    armer(d, c);
    return d;
  }

  // ---- le geste : on prend une carte, on la pose sur une autre ------------
  const aNous = (c) => c.camp === (vue && vue.camp);
  // Ce qu'une pièce en main peut atteindre. La règle est ici, en trois lignes,
  // et elle est la même que celle du greffier : un obstacle ou une frappe d'en
  // face, une de nos clefs. Le reste ne s'allume pas.
  const cible = (c) => (c.type === "verrou" && !aNous(c))
                    || (c.type === "frappe" && !aNous(c))
                    || (c.type === "clef" && aNous(c))
                    || (c.type === "verrou" && aNous(c));
  const prenable = (c) => (c.type === "piece" && aNous(c) && c.apparence === "libre")
                       || ((c.type === "clef" || c.type === "verrou") && aNous(c));

  function armer(d, c) {
    if (prenable(c)) {
      d.draggable = true;
      d.classList.add("pc-prenable");
      d.addEventListener("dragstart", (e) => {
        tenue = c;
        e.dataTransfer.setData("text/plain", c.id);
        e.dataTransfer.effectAllowed = "move";
        document.getElementById("partie").classList.add("pc-en-main");
        // Les cibles possibles s'allument SEULEMENT pour ce qu'on tient.
        document.querySelectorAll("#partie .pc-carte").forEach((x) => {
          if (x.dataset.jouable === "1" && c.type === "piece") x.classList.add("pc-appel");
        });
      });
      d.addEventListener("dragend", () => {
        tenue = null;
        document.getElementById("partie").classList.remove("pc-en-main");
        document.querySelectorAll("#partie .pc-appel").forEach((x) => x.classList.remove("pc-appel"));
      });
    }
    if (cible(c)) {
      d.dataset.jouable = "1";
      d.addEventListener("dragover", (e) => {
        if (!tenue || tenue.type !== "piece") return;
        e.preventDefault();
        d.classList.add("pc-survol");
      });
      d.addEventListener("dragleave", () => d.classList.remove("pc-survol"));
      d.addEventListener("drop", (e) => {
        e.preventDefault();
        d.classList.remove("pc-survol");
        if (!tenue || tenue.type !== "piece") return;
        demanderPuisJouer(tenue, c, d);
      });
    }
  }

  // Sur un verrou qu'aucune de nos clefs ne touche encore, on pose une clef
  // NEUVE : elle porte un titre, et ce titre est au joueur. Ailleurs (renfort,
  // garde) il n'y a rien à nommer, le coup part sans rien demander.
  function demanderPuisJouer(piece, sur, ancre) {
    if (sur.type !== "verrou" || aNous(sur) || dejaUneClef(sur.id))
      return jouer({ quoi: "poser", piece: piece.id, sur: sur.id });
    bulle(ancre, piece, sur);
  }

  const dejaUneClef = (bid) => (vue.fronts || []).some(
    (f) => f.id === bid && (f.pile || []).some((o) => o.type === "clef" && aNous(o)));

  // La bulle est posée sur le CORPS, en repère fixe, et non dans la carte : la
  // colonne des fronts défile en `overflow:auto`, et une bulle qui y vivrait
  // serait coupée au bord dès que le front est près de la marge.
  function bulle(ancre, piece, sur) {
    document.querySelectorAll(".pc-bulle").forEach((x) => x.remove());
    const b = el("div", "pc-bulle");
    const r = ancre.getBoundingClientRect();
    b.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 266)) + "px";
    b.style.top = Math.min(r.bottom + 4, window.innerHeight - 130) + "px";
    b.appendChild(el("div", "pc-bulle-t", "Et " + piece.titre + " y fait quoi ?"));
    const champ = document.createElement("input");
    champ.type = "text";
    champ.placeholder = piece.titre + " contre « " + sur.titre + " »";
    b.appendChild(champ);
    const pied = el("div", "pc-bulle-p");
    const ok = el("button", "pc-bt", "Poser");
    const non = el("button", "pc-bt pc-bt-nu", "Laisser");
    pied.appendChild(non); pied.appendChild(ok);
    b.appendChild(pied);
    document.body.appendChild(b);
    champ.focus();
    const partir = () => b.remove();
    const valider = () => { partir(); jouer({ quoi: "poser", piece: piece.id, sur: sur.id, texte: champ.value.trim() }); };
    ok.addEventListener("click", valider);
    non.addEventListener("click", partir);
    champ.addEventListener("keydown", (e) => {
      if (e.key === "Enter") valider();
      if (e.key === "Escape") partir();
    });
  }

  // ---- envoyer le geste ---------------------------------------------------
  function jouer(geste) {
    mot = "…"; motMauvais = false; dernier = ""; dessiner();
    fetch("/partie/geste", { method: "POST", headers: { "Content-Type": "application/json" },
                             body: JSON.stringify(geste) })
      .then((r) => r.json())
      .then((r) => {
        mot = r.ok ? ((r.dit || "") + ((r.avertissements || []).length ? " — " + r.avertissements[0] : ""))
                   : (r.refus || ["refusé"]).join(" · ");
        motMauvais = !r.ok;
        if (r.vue) vue = r.vue;
        dernier = ""; dessiner();
      })
      .catch(() => { mot = "le mestre n'a pas répondu"; motMauvais = true; dernier = ""; dessiner(); });
  }

  // PAS DE BOUTON POUR FAIRE PASSER LE JOUR, et c'est délibéré. Le temps ne
  // passe pas parce qu'on a cliqué : il passe parce que le monde tourne, et le
  // monde est au MJ. Un tour de partie vaut deux jours de `monde.date` ; c'est
  // lui qui écrit la ligne `tour` quand il avance l'horloge (par
  // `partie.py --tour`, ou `POST /partie/jour` qui reste ouvert pour lui).
  // Un bouton ici ferait de la partie une horloge séparée du monde — deux
  // temps qui dérivent l'un de l'autre — et donnerait au joueur un levier
  // hors fiction, ce que le manuel interdit partout ailleurs.

  // ---- un front : l'obstacle en tête, nos cartes empilées dessous ---------
  // NI EN-TÊTE NI PIED SUR UN FRONT. L'en-tête recopiait en capitales le
  // dessein qui est déjà en toutes lettres dans la colonne de gauche, et il
  // faisait trois lignes au-dessus de chaque colonne. Le pied disait « tenu par
  // eux » là où la couleur du cadre et le ✅ de la clef le disent déjà. Le
  // dessein servi reste accessible : il est en infobulle sur la colonne.
  function front(f) {
    const d = el("div", "pc-front pc-prevaut-" + (f.prevaut || "vert")
                        + (f.contre_nous === false ? " pc-front-nous" : ""));
    d.title = "contre « " + (f.sur_titre || "") + " » — " + (f.pourquoi || "");
    // PAS DE LIGNE « CE QUE ÇA SERT ». Essayée, et retirée aussitôt : tronquée
    // à une ligne elle était illisible, entière elle faisait trois lignes de
    // titres au-dessus de chaque colonne — la colonne des états cibles revenue par
    // la fenêtre. La chaîne reste dans l'infobulle de la colonne, et dans la
    // vue servie par `/partie` pour qui en a besoin.
    const pile = el("div", "pc-pile");
    pile.appendChild(carte(f.tete));
    (f.pile || []).forEach((o) => {
      const co = carte(o); co.classList.add("pc-sous");
      pile.appendChild(co);
      (o.sous || []).forEach((s) => {
        const cs = carte(s); cs.classList.add("pc-sous2");
        pile.appendChild(cs);
      });
    });
    d.appendChild(pile);
    return d;
  }

  function rangee(nom, cartes, vide) {
    const r = el("div", "pc-rangee");
    r.appendChild(el("div", "pc-lbl", nom));
    if (!cartes.length) r.appendChild(el("div", "pc-vide", vide || "—"));
    cartes.forEach((c) => r.appendChild(carte(c)));
    return r;
  }

  // ---- le plateau entier ---------------------------------------------------
  function dessiner() {
    const h = hote();
    if (!h) return;
    const sig = JSON.stringify(vue);
    if (sig === dernier) return;
    dernier = sig;
    h.innerHTML = "";
    if (!vue || !vue.partie) {
      h.appendChild(el("div", "pc-rien", charge ? "Aucune partie ouverte. Le conseil de guerre s'ouvrira quand le mestre en aura une à tenir."
                                                 : "Le mestre rassemble les cartes…"));
      return;
    }
    const bar = el("div", "pc-bar");
    bar.appendChild(el("span", "", "jour " + (vue.jours + 1) + " de la partie"));
    bar.appendChild(el("span", "", !vue.trone ? "👑 le trône n'est constaté à personne"
                                  : vue.trone === vue.camp ? "👑 le trône est à nous" : "👑 le trône est à eux"));
    bar.appendChild(el("span", "", vue.trait === vue.camp ? "à vous de jouer" : "on attend leur coup"));
    h.appendChild(bar);
    if (mot) {
      const m = el("div", "pc-mot" + (motMauvais ? " pc-mot-non" : ""), mot);
      h.appendChild(m);
    }

    // PLUS DE COLONNE « MES DESSEINS ». C'était un arbre d'objectifs qui ne
    // bougeait pas d'un tour à l'autre, occupant un cinquième de l'écran pour
    // répéter ce que les fronts disent déjà, et il ne servait aucune décision :
    // on ne joue pas sur un dessein, on joue sur ce qui s'y oppose. Ce qu'il
    // portait d'utile — la chaîne jusqu'au trône — vit sur chaque front.
    // Les questions ❓ posées sur un dessein, elles, ne se perdent pas : elles
    // remontent en tête du plateau, parce qu'elles attendent une réponse.
    // LEUR CÔTÉ, EN HAUT. Leurs pièces avaient d'abord été mises en rangée du
    // deck, sous « En main » — ce qui revenait à dire que Vhagar est dans la
    // main de la reine. La table d'un jeu à deux se lit de haut en bas : eux,
    // le terrain disputé, nous. La position suffit à dire à qui c'est, avec la
    // couleur du bord ; aucun libellé n'a à l'expliquer.
    if ((vue.eux || []).length) {
      const face = el("div", "pc-eux");
      vue.eux.forEach((c) => face.appendChild(carte(c)));
      h.appendChild(face);
    }

    const plateau = el("div", "pc-plateau");
    const attentes = (vue.cibles || []).flatMap((d) => (d.sous || []).map((s) => ({ s: s, d: d })));
    if (attentes.length) {
      const q = el("div", "pc-attentes");
      attentes.forEach(({ s, d: dess }) => {
        const cs = carte(s);
        cs.title = "sur « " + dess.titre + " »";
        q.appendChild(cs);
      });
      plateau.appendChild(q);
    }
    const fronts = el("div", "pc-fronts");
    if (!vue.fronts.length) fronts.appendChild(el("div", "pc-vide", "rien ne vous fait face — encore"));
    vue.fronts.forEach((f) => fronts.appendChild(front(f)));
    plateau.appendChild(fronts);
    h.appendChild(plateau);

    // Le deck est aussi une CIBLE : une carte à nous qu'on y ramène est
    // reprise, et ses pièces se remettent deux jours. Le geste est le même que
    // celui qui les a posées, à l'envers — rien de neuf à apprendre.
    const deck = el("div", "pc-deck");
    deck.addEventListener("dragover", (e) => {
      if (!tenue || tenue.type === "piece") return;
      e.preventDefault();
      deck.classList.add("pc-survol");
    });
    deck.addEventListener("dragleave", () => deck.classList.remove("pc-survol"));
    deck.addEventListener("drop", (e) => {
      e.preventDefault();
      deck.classList.remove("pc-survol");
      if (!tenue || tenue.type === "piece") return;
      jouer({ quoi: "reprendre", sur: tenue.id });
    });
    const d = vue.deck || {};
    deck.appendChild(rangee("En main", d.main || [], "rien de libre"));
    const ailleurs = (d.route || []).concat(d.remet || []);
    if (ailleurs.length) deck.appendChild(rangee("En route · se remet", ailleurs));
    if ((d.posees || []).length) deck.appendChild(rangee("Posées", d.posees));
    if ((d.detruites || []).length) deck.appendChild(rangee("Perdues", d.detruites));
    h.appendChild(deck);
  }

  // ---- charger : la vue vient du serveur, dérivée du jsonl ----------------
  function charger() {
    fetch("/partie", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((v) => { vue = v; charge = true; dessiner(); })
      .catch(() => { vue = null; charge = true; dessiner(); });
  }
  const relire = () => { dernier = ""; charger(); };

  window.addEventListener("DOMContentLoaded", () => {
    charger();
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "conseil", nom: "Le conseil", hote: "partie", ordre: 2.6,
        dispo: () => true,
        reparu: () => { charger(); },
      });
    }
    // Un changement de scène peut suivre un coup joué ailleurs : on relit.
    if (window.Bus && Bus.enregistrer) Bus.enregistrer("effacer", relire);
    if (window.Bus && Bus.enregistrer) Bus.enregistrer("partie", relire);
  });

  return { charger, relire, vue: () => vue };
})();
