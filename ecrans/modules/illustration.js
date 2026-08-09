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
  function vignette(hote, montre, vu) {
    if (!window.Carte || !window.Geo) return;
    const d = document.createElement("div");
    d.className = "chr-carte";
    d.innerHTML = Carte.miniature(montre) +
      '<span class="chr-carte-ouvrir">S\'approcher…</span>';
    d.addEventListener("click", () => Carte.ouvrir(vu || "auto"));
    hote.appendChild(d);
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

  // Ce que tout item peut porter : `montre`. Appelé par paroles.js et gestes.js.
  function poser(el, it) {
    const m = it.montre;
    if (!m) return;
    const corps = el && (el.querySelector(".chr-corps") || el);
    // Un livre montré tient tout seul : il se repose à la relecture, parce
    // qu'il n'est pas l'état du monde mais ce qu'on a laissé voir ce jour-là.
    if (m.livre && corps) livre(corps, m);
    // Une main sur la carte, rechargée du passé, ne repose rien : la table
    // montre l'état d'aujourd'hui, pas ce qu'on y désignait il y a trois jours.
    if (vide(m) || !window.Carte || Bus.enArchive()) return;
    attacher(el, Carte.illustrer(marquesDe(m)));
  }

  Bus.enregistrer("table", (it, ctx) => {
    const m = marquesDe(it);
    if (it.acteur_id && window.activerLocuteur) window.activerLocuteur(it.acteur_id);
    const p = (window.Presents || {})[it.acteur_id] || { nom: it.acteur_id };
    const el = Bus.chronique("chr-table", it.acteur_id ? p.nom : null,
      it.texte || "", { avatar: p.portrait_svg, role: p.titre });
    const vu = !vide(m) && window.Carte ? Carte.illustrer(m) : null;
    if (el && !vide(m)) vignette(el.querySelector(".chr-corps") || el, m, vu);
    // Une main sur la carte n'est pas une parole : c'est le chroniqueur qui la
    // décrit, comme un geste.
    if (window.Voix && it.texte) Voix.dire("narrateur", it.texte, ctx);
  });

  return { poser, attacher, vignette, livre };
})();
