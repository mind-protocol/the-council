// illustration.js — quand un acteur illustre ses propos sur la table peinte.
// Un conseil est une séance de travail : on ne dit pas « la flotte tiendra le
// Gosier », on pose trois doigts dessus. Ce module donne aux acteurs la main sur
// la carte, de deux façons :
//
//   • item {type:"table", acteur_id, texte, jetons, traits, zones, cadre}
//     — un geste sur la carte, avec sa vignette dans le fil. Le chroniqueur le
//       raconte (ce n'est pas une parole) et la table du décor prend les pièces.
//
//   • un champ `montre` sur une `replique` ou un `geste`
//     — il parle ET sa main pose : la table du décor bouge pendant qu'il parle,
//       et sa carte du fil porte une mention discrète pour y revenir.
//     `montre: {jetons, traits, zones, cadre}` pose sur la table peinte ;
//     `montre: {pieces:["2010","2001"]}` pose sur L'ÉCHIQUIER — le décor y
//     bascule, l'affaire s'ouvre, et la chaîne causale des pièces s'allume.
//
// Les pièces posées ainsi sont ÉPHÉMÈRES : elles vivent le temps de la scène et
// tombent au prochain `effacer`. Ce qui doit durer, le MJ l'écrit dans
// etat/jetons.json — un geste de démonstration n'est pas un fait acquis.
"use strict";
window.Illustration = (() => {
  const marquesDe = (m) => ({
    jetons: m.jetons || [], traits: m.traits || [], zones: m.zones || [],
    cadre: m.cadre,
  });
  const vide = (m) => !(m.jetons || []).length && !(m.traits || []).length &&
    !(m.zones || []).length;

  // La vignette dans le fil : la carte réduite au geste, cliquable pour ouvrir
  // la grande table sur le même cadrage. `vu` est le cadrage déjà résolu par
  // Carte.illustrer — la chronique doit rouvrir EXACTEMENT ce qui a été montré,
  // même quand la table aura changé.
  // Une vignette pèse ~470 Ko de tracé (la côte de Westeros y passe trois fois,
  // en haut-fond, en terre et en côte) et le cadrage en jette 95 % hors champ
  // sans les rendre gratuits pour autant. Une chronique de trois heures en
  // porte des dizaines : le défilement ramait à proportion de ce qu'on avait
  // joué, ce qui est le pire des couplages.
  //
  // `content-visibility` n'a pas suffi — il épargne la PEINTURE, pas le DOM ni
  // sa géométrie. On monte donc la carte quand elle approche de l'écran et on
  // la DÉMONTE quand elle s'en éloigne : à tout instant, deux ou trois
  // vignettes existent, quelle que soit la longueur de la scène. Le cadre garde
  // sa place (`aspect-ratio` posé d'avance), donc rien ne saute au défilement.
  const enVue = ("IntersectionObserver" in window) ? new IntersectionObserver(
    (ents) => ents.forEach((e) => (e.isIntersecting ? monter : demonter)(e.target)),
    { rootMargin: "400px 0px" }) : null;
  const arendre = new WeakMap();

  function monter(d) {
    if (d.dataset.pose === "1") return;
    const m = arendre.get(d);
    if (!m || !window.Carte) return;
    d.insertAdjacentHTML("afterbegin", Carte.miniature(m));
    d.dataset.pose = "1";
  }

  function demonter(d) {
    if (d.dataset.pose !== "1") return;
    const svg = d.querySelector("svg");
    if (svg) svg.remove();
    d.dataset.pose = "0";
  }

  function vignette(hote, montre, vu) {
    if (!window.Carte || !window.Geo) return;
    const d = document.createElement("div");
    d.className = "chr-carte";
    d.innerHTML = '<span class="chr-carte-ouvrir">S\'approcher…</span>';
    // La place se réserve AVANT de connaître la carte : c'est le cadrage qui
    // donne le rapport, et il ne dépend que de ce qu'on montre.
    try {
      const seul = { jetons: montre.jetons || [], traits: montre.traits || [],
                     zones: montre.zones || [] };
      const c = Carte.cadre(montre.cadre && montre.cadre !== "garder"
        ? montre.cadre : "auto", seul);
      if (c && c.h) d.style.aspectRatio = (c.l / c.h).toFixed(3);
    } catch (e) { /* pas de cadrage : la hauteur minimale du CSS fera l'affaire */ }
    d.addEventListener("click", () => Carte.ouvrir(vu || "auto"));
    // Le filet. Une case vide est un défaut PIRE que la lenteur qu'on soigne :
    // si l'observateur ne délivre pas — page rendue en arrière-plan, conteneur
    // de défilement exotique, navigateur qui n'en veut pas —, le survol et le
    // clic montent la carte de toute façon. Deux gestes qui prouvent que le
    // joueur la regarde, et qui ne coûtent rien quand elle est déjà là.
    d.addEventListener("mouseenter", () => monter(d));
    d.addEventListener("click", () => monter(d));
    hote.appendChild(d);
    arendre.set(d, montre);
    if (enVue) enVue.observe(d); else monter(d);
  }

  // ---- la co-référence : le texte et la pièce se désignent l'un l'autre ----
  // Sans ça, la phrase parle et la carte illustre à côté, chacune de son côté,
  // et c'est au joueur de faire la couture à l'œil. Un appui du MJ qui porte le
  // NOM d'une pièce montrée s'y accroche tout seul — aucune syntaxe nouvelle,
  // parce qu'une syntaxe de liaison à écrire à la main sous pression de tour ne
  // serait pas écrite. `ancre: ["…"]` sur la pièce ajoute des formulations.
  const clef = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

  function lier(el, montre) {
    if (!el) return;
    const noms = {};
    ["jetons", "traits", "zones"].forEach((k) => (montre[k] || []).forEach((m) => {
      if (!m.id) return;
      [m.nom].concat(m.ancre || []).forEach((n) => { if (n) noms[clef(n)] = m.id; });
    }));
    if (!Object.keys(noms).length) return;
    const corps = el.querySelector(".chr-texte") || el;
    corps.querySelectorAll("b.appui").forEach((b) => {
      const id = noms[clef(b.textContent)];
      if (!id) return;
      b.dataset.piece = id;
      b.classList.add("appui-piece");
    });
    if (!el.querySelector("b.appui[data-piece]")) return;

    // Le survol va dans les deux sens : la phrase allume la pièce, la pièce
    // allume la phrase. Deux sens, parce qu'une désignation à sens unique reste
    // une légende — et une légende n'est pas une langue.
    const marquer = (id, oui) => {
      el.querySelectorAll('[data-piece="' + CSS.escape(id) + '"]').forEach(
        (n) => n.classList.toggle("vise", oui));
      el.querySelectorAll('.carte-mini [data-id="' + CSS.escape(id) + '"]').forEach(
        (n) => n.classList.toggle("vise", oui));
    };
    const ancres = new Set(Object.keys(noms).map((k) => noms[k]));
    const de = (e) => {
      const b = e.target.closest("b.appui[data-piece]");
      if (b) return b.dataset.piece;
      const g = e.target.closest(".carte-mini [data-id]");
      return g && ancres.has(g.dataset.id) ? g.dataset.id : null;
    };
    let vise = null;
    el.addEventListener("mouseover", (e) => {
      const id = de(e);
      if (id === vise) return;
      if (vise) marquer(vise, false);
      vise = id;
      if (vise) marquer(vise, true);
    });
    el.addEventListener("mouseleave", () => {
      if (vise) marquer(vise, false);
      vise = null;
    });
  }

  // Sur une réplique ou un geste : pas de seconde carte dans le fil — la table
  // du décor vient de bouger sous les yeux du joueur. Juste de quoi y revenir.
  function attacher(el, vu) {
    if (!el) return;
    const corps = el.querySelector(".chr-corps") || el;
    const a = document.createElement("span");
    a.className = "chr-vers-table";
    a.textContent = "la table en porte la marque";
    a.addEventListener("click", () => {
      if (window.Carte) Carte.ouvrir(vu || "auto");
    });
    corps.appendChild(a);
  }

  // ---- Montrer un livre ---------------------------------------------------
  // MONTRER N'EST PAS DONNER, et c'est toute la mécanique : il garde le volume
  // en main, à bout de bras. Le joueur voit la page qu'on a bien voulu lui
  // laisser voir — pas de lien vers l'étagère, pas de suite. S'il en veut
  // davantage, il demande, et c'est une scène.
  //
  // L'extrait est GELÉ par append_flux.py au moment de la poussée. On ne relit
  // donc jamais books.json ici : ce que le fil garde est ce qui a été montré ce
  // jour-là, même si le registre a changé depuis. C'est l'inverse du choix fait
  // pour la carte, et c'est voulu — une table dit l'état du jour, un extrait
  // est une pièce à conviction.
  function livre(hote, m) {
    const e = m.extrait;
    if (!e) return;
    const d = document.createElement("div");
    d.className = "chr-livre";
    if (e.couleur || e.type) {
      d.style.setProperty("--book-teinte",
        (window.Books && Books.teinte) ? Books.teinte(e) : "var(--braise)");
    }

    const t = document.createElement("div");
    t.className = "chr-livre-titre";
    t.textContent = e.titre || "Un volume sans titre";
    d.appendChild(t);
    if (e.sous_titre) {
      const s = document.createElement("div");
      s.className = "chr-livre-sous-titre";
      s.textContent = e.sous_titre;
      d.appendChild(s);
    }

    const corps = document.createElement("div");
    corps.className = "chr-livre-corps";
    if (e.figure_svg || e.figure) {
      corps.appendChild(livrePage({ figure: e.figure, figure_svg: e.figure_svg,
                                    legende: e.legende }));
    } else if (e.lignes) {
      corps.appendChild(tableau(e));
    } else if (e.texte) {
      corps.appendChild(livrePage(e.texte));
    } else {
      const vierge = document.createElement("p");
      vierge.className = "book-page book-attente";
      vierge.textContent = "Rien n'y est encore écrit.";
      corps.appendChild(vierge);
    }
    d.appendChild(corps);

    // Ce qu'on ne vous a PAS montré. Un registre de quarante lignes dont on
    // vous en tend trois, ça se dit — c'est même l'essentiel de l'information.
    const reste = mentionDuReste(e);
    if (reste) {
      const r = document.createElement("div");
      r.className = "chr-livre-reste";
      r.textContent = reste;
      d.appendChild(r);
    }
    if (m.presente) presenter(d, m, e);
    hote.appendChild(d);
  }

  // ---- Présenter : il le pose ouvert, et le volume reste à lui -------------
  // Le cran du milieu entre montrer et passer. Le joueur peut tourner la page —
  // et c'est un GESTE, pas une navigation : ça coûte une minute, ça se passe
  // dans la salle, et le porteur peut poser la main dessus. On ne tourne donc
  // rien ici : on demande, le MJ répond en poussant la page suivante, ou en
  // montrant la main qui se referme.
  //
  // Un seul volume ouvert à la fois. Une carte plus ancienne perd son bouton
  // dès qu'on en présente une neuve : sans ça, le joueur feuillette dix
  // registres de trois scènes différentes, tous « ouverts » sur la table.
  let ouvert = null;

  function presenter(d, m, e) {
    if (Bus.enArchive()) return;
    if (ouvert && ouvert.isConnected) fermer(ouvert);
    ouvert = d;
    d.classList.add("chr-livre-ouvert");

    const suivante = suivantePage(e);
    if (suivante === null) {
      // Dernière page : il n'y a plus rien à tourner, et le dire vaut mieux
      // qu'un bouton mort — c'est une information sur le volume.
      const f = document.createElement("div");
      f.className = "chr-livre-fin";
      f.textContent = "C'est la dernière page.";
      d.appendChild(f);
      return;
    }
    const b = document.createElement("button");
    b.className = "chr-livre-tourner";
    b.textContent = "Tourner la page";
    b.addEventListener("click", () => {
      b.disabled = true;
      b.textContent = "Vous avancez la main…";
      Bus.poster({ type: "page", livre: m.livre, vers: suivante,
                   depuis: e.page == null ? null : e.page });
    });
    d.appendChild(b);
  }

  // La page d'après, ou null s'il n'y en a pas. Un registre se tourne aussi :
  // trois lignes à la fois, dans l'ordre où elles sont écrites.
  function suivantePage(e) {
    if (e.lignes && e.indices) {
      const dernier = e.indices[e.indices.length - 1];
      return (dernier + 1 < e.total_lignes) ? dernier + 1 : null;
    }
    if (e.total_pages == null) return null;
    const n = (e.page || 0) + 1;
    return n < e.total_pages ? n : null;
  }

  function fermer(d) {
    d.classList.remove("chr-livre-ouvert");
    const b = d.querySelector(".chr-livre-tourner");
    if (b) b.remove();
    const f = d.querySelector(".chr-livre-fin");
    if (f) f.remove();
  }

  // Le volume se referme tout seul au changement de scène : ce qui était ouvert
  // sur la table de la Chambre Peinte ne l'est plus dans la roukerie.
  Bus.enregistrer("effacer", () => { ouvert = null; });

  function mentionDuReste(e) {
    if (e.mention) return e.mention;
    if (e.lignes && e.total_lignes > e.lignes.length) {
      return "Le volume en porte " + e.total_lignes + " ; on vous en montre "
        + e.lignes.length + ".";
    }
    if (e.total_pages > 1) {
      return "Page " + ((e.page || 0) + 1) + " sur " + e.total_pages
        + " — le reste reste fermé.";
    }
    return null;
  }

  // La page a EXACTEMENT la mine qu'elle aurait dans le volume : c'est le même
  // renderer. Deux mines pour un même objet, et le joueur croit voir deux
  // objets. Si les livres n'ont pas encore chargé, on retombe sur du texte nu.
  function livrePage(p) {
    if (window.Books && Books.page) return Books.page(p);
    const par = document.createElement("p");
    par.className = "book-page";
    par.textContent = (p && p.legende) || (typeof p === "string" ? p : "");
    return par;
  }

  function tableau(e) {
    const env = document.createElement("div");
    env.className = "book-table-enveloppe";
    const tab = document.createElement("table");
    tab.className = "book-table";
    if ((e.colonnes || []).length) {
      const thead = document.createElement("thead");
      const tr = document.createElement("tr");
      e.colonnes.forEach((c) => {
        const th = document.createElement("th");
        th.textContent = c;
        tr.appendChild(th);
      });
      thead.appendChild(tr);
      tab.appendChild(thead);
    }
    const tbody = document.createElement("tbody");
    (e.lignes || []).forEach((l) => {
      const cellules = Array.isArray(l) ? l : (l.cellules || []);
      const note = Array.isArray(l) ? null : l.note;
      const tr = document.createElement("tr");
      cellules.forEach((c, i) => {
        const td = document.createElement("td");
        if (window.Books && Books.poser) Books.poser(td, c);
        else td.textContent = c == null ? "" : String(c);
        if (note && i === cellules.length - 1) {
          const n = document.createElement("div");
          n.className = "book-note";
          if (window.Books && Books.poser) Books.poser(n, note);
          else n.textContent = note;
          td.appendChild(n);
        }
        if (window.Entites) Entites.traiter(td);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tab.appendChild(tbody);
    env.appendChild(tab);
    return env;
  }

  // ---- LA MAIN SUR LE PLAN : `montre: {pieces:[…]}` -----------------------
  // Le symétrique des jetons de la table peinte, pour l'échiquier. La table
  // peinte dit OÙ porte la guerre ; l'échiquier dit COMMENT ce qu'on a devient
  // ce qu'on veut — et un conseiller qui déroule son raisonnement pose la main
  // sur le second exactement comme il la posait sur la première.
  //
  // Le renvoi inline (`[les neufs](44022)`, voir renvois.js) sert la MENTION EN
  // PASSANT ; ceci sert le RAISONNEMENT DÉROULÉ, celui qu'on tient sous les
  // yeux pendant qu'il parle. Même règle qu'ailleurs : c'est ÉPHÉMÈRE, ça tombe
  // au prochain `effacer`, et ce qui doit durer s'écrit au cahier de l'affaire.
  function plateau(el, pieces) {
    if (!window.Echiquier || !Echiquier.designer || Bus.enArchive()) return;
    if (!Echiquier.designer(pieces, { franc: true })) return;
    if (!el) return;
    const corps = el.querySelector(".chr-corps") || el;
    const a = document.createElement("span");
    a.className = "chr-vers-table chr-vers-plateau";
    a.textContent = "il montre le plan";
    a.addEventListener("click", () => Echiquier.designer(pieces, { franc: true }));
    corps.appendChild(a);
  }

  // Les pièces que le TEXTE de l'item nomme — `[le mât](45001)` —, telles que
  // le plan les reconnaît. `attention.js` a déjà posé les <b class="renvoi"> au
  // moment où la pièce s'est rendue, donc elles sont là, dans le même tour ;
  // c'est `renvois.js` qui les jugera 16 ms plus tard, et c'est trop tard pour
  // arbitrer un décor. On les marque `data-montre` pour qu'il ne redésigne pas
  // par-dessus nous : deux éclats pour un seul énoncé.
  function piecesDuTexte(el) {
    if (!el || !window.Echiquier || !Echiquier.sorte) return [];
    const out = [];
    el.querySelectorAll(".renvoi[data-cible]").forEach((r) => {
      const c = r.dataset.cible || "";
      if (!/^\d{4,6}$/.test(c) || !Echiquier.sorte(c)) return;
      r.dataset.montre = "1";
      if (out.indexOf(c) < 0) out.push(c);
    });
    return out;
  }

  // ---- QUAND LES DEUX ÉCHELLES TIRENT DANS LE MÊME ITEM --------------------
  // Marna retourne le volume à la page des noms et montre cinq corrections
  // datées : c'est un extrait de registre, et son texte cite des pièces du
  // plan. L'extrait veut les Livres, les renvois veulent l'échiquier.
  //
  // L'ÉCHIQUIER GAGNE LE DÉCOR, et le contenu donne raison à la règle : sur ces
  // cinq lignes, trois ne renommaient rien — un verrou nommé par ce qui manque
  // au lieu de ce qu'on espère est un AUTRE objet, une mesure passe de 107 à
  // 106, et une pièce disparaît. La page montre la correction ; seul le damier
  // montre ce que la correction déplace — une chaîne qui se recompose sans son
  // verrou. Ce que le joueur doit voir est le déplacement, pas la rature.
  //
  // Et ce n'est plus l'ordre d'exécution qui le décide. L'échiquier gagnait
  // déjà, mais par accident : les renvois se jugent 16 ms après le rendu, donc
  // ils passaient en dernier. Un extrait qui se mettrait un jour à prendre le
  // décor aurait renversé la règle sans que personne ne touche à cette
  // intention. On désigne donc ICI, explicitement, APRÈS que l'extrait s'est
  // rendu — et l'ordre des deux lignes est la règle elle-même.
  //
  // L'extrait ne se perd pas : il est entier dans le fil, et il gagne un chemin
  // vers son volume. Un geste, comme demandé.
  function versLeVolume(el, m) {
    const bloc = el && el.querySelector(".chr-livre");
    if (!bloc || !m.livre || !window.Books || !Books.ouvrir) return;
    const a = document.createElement("button");
    a.type = "button";
    a.className = "chr-livre-vers";
    a.textContent = "Ouvrir le volume";
    a.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (!Books.ouvrir(m.livre)) {
        a.disabled = true;
        a.textContent = "Ce volume n'est plus à portée d'ici";
      }
    });
    bloc.appendChild(a);
  }

  // Ce que tout item peut porter : `montre`. Appelé par paroles.js et gestes.js.
  function poser(el, it) {
    const m = it.montre;
    if (!m) return;
    const corps = el && (el.querySelector(".chr-corps") || el);
    // Ce que le texte nomme du plan, relevé AVANT que l'extrait se rende — on
    // veut la liste, pas encore l'éclat.
    const dites = m.livre ? piecesDuTexte(el) : [];
    // Un livre montré tient tout seul : il se repose à la relecture, parce
    // qu'il n'est pas l'état du monde mais ce qu'on a laissé voir ce jour-là.
    if (m.livre && corps) livre(corps, m);
    // ET L'ÉCHIQUIER PASSE APRÈS L'EXTRAIT, toujours : c'est par cet ordre-là
    // qu'il gagne le décor quand les deux tirent dans le même item. Un item qui
    // ne porte qu'un extrait ne passe pas ici du tout, et son geste ne bouge
    // pas d'un cheveu.
    const toutes = (m.pieces || []).concat(
      dites.filter((n) => (m.pieces || []).indexOf(n) < 0));
    if (toutes.length) plateau(el, toutes);
    if (dites.length) versLeVolume(el, m);
    // Une main sur la carte, rechargée du passé, ne repose rien : la table
    // montre l'état d'aujourd'hui, pas ce qu'on y désignait il y a trois jours.
    if (vide(m) || !window.Carte || Bus.enArchive()) return;
    attacher(el, Carte.illustrer(marquesDe(m)));
    // Pas de vignette ici (il vient de voir la table bouger), mais les appuis
    // de sa phrase désignent quand même les pièces du décor.
    lier(el, m);
  }

  Bus.enregistrer("table", (it, ctx) => {
    const m = marquesDe(it);
    if (it.acteur_id && window.activerLocuteur) window.activerLocuteur(it.acteur_id);
    const p = (window.Presents || {})[it.acteur_id] || { nom: it.acteur_id };
    const el = Bus.chronique("chr-table", it.acteur_id ? p.nom : null,
      it.texte || "", { avatar: p.portrait_svg, role: p.titre });
    const vu = !vide(m) && window.Carte ? Carte.illustrer(m) : null;
    if (el && !vide(m)) {
      vignette(el.querySelector(".chr-corps") || el, m, vu);
      lier(el, m);
    }
    // Une main sur la carte n'est pas une parole : c'est le chroniqueur qui la
    // décrit, comme un geste.
    if (window.Voix && it.texte) Voix.dire("narrateur", it.texte, ctx);
  });

  return { poser, attacher, vignette, livre, lier, plateau };
})();
