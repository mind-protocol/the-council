// books.js — « Les livres », une échelle du décor.
// Un book est un OBJET posé dans une salle : un registre sur la Table Peinte,
// un livre de comptes à l'intendance, un rôle d'équipage au quai. Il porte du
// JSON — un tableau à colonnes, des pages de texte — et il ne se consulte que
// là où il se trouve : on ne lit pas depuis l'autre bout du château un registre
// qui est resté sur la table.
//
// Un livre peut aussi n'être posé nulle part : il est SUR QUELQU'UN. C'est le
// carnet de voyage — il suit son porteur de château en château, et on ne peut
// l'ouvrir que là où l'homme se trouve. Un carnet qu'on lit alors que son
// porteur est à trois jours de route serait une fuite, pas une commodité.
//
// Format (etat/books.json, un tableau) :
//   id                      — l'objet
//   lieu_id, salle_id       — où il est POSÉ (un registre sur une table)
//   acteur_id               — ou sur QUI il est porté (un carnet de voyage) ;
//                             l'un ou l'autre, jamais les deux
//   prive: true             — un carnet que son porteur ne montre pas : seul
//                             le joueur qui le porte le voit
//   titre, sous_titre       — ce qu'on lit sur la couverture
//   type                    — le genre du volume (registre, carnet, plan,
//                             memento, dossier, regle, oeuvre) : il donne son
//                             mot sur l'onglet et sa teinte de tranche
//   couleur                 — pour forcer la teinte contre celle du type ;
//                             sans lui, elle est préremplie par le type
//   colonnes: [ "…", … ]    — l'en-tête du tableau (optionnel)
//   lignes: [ { cellules: [ … ], note: "…" }, … ]  (une ligne peut aussi être
//                             un simple tableau de cellules)
//   pages: [ "…", … ]       — du texte suivi, quand il n'y a pas de tableau
//
// Un dernier volume ferme l'étagère et n'est PAS dans `books.json` : les notes
// du joueur. Hors fiction, toujours à portée, gardées telles quelles par le
// serveur (`/notes`, un fichier de texte par siège). Rien de ce qui s'y écrit
// n'entre dans la partie.
"use strict";
window.Books = (() => {
  let books = null;
  let charge = false;
  let salleVue = undefined;   // la salle du dernier tracé
  let portantsVus = "";       // qui portait un carnet au dernier tracé
  let ouvert = null;          // le volume qu'on a sous les yeux

  // Les genres de volume. Le `type` d'un livre est facultatif ; quand il y en
  // a un, il prérremplit la teinte de la tranche — on reconnaît un carnet d'un
  // registre au coin de l'œil, sans lire l'onglet. Une clé `couleur` sur le
  // livre passe devant, pour le volume qui ne ressemble à aucun autre.
  const TYPES = {
    registre: { nom: "Registre", teinte: "var(--book-registre)" },
    carnet:   { nom: "Carnet",   teinte: "var(--book-carnet)" },
    plan:     { nom: "Plan",     teinte: "var(--book-plan)" },
    memento:  { nom: "Mémento",  teinte: "var(--book-memento)" },
    dossier:  { nom: "Dossier",  teinte: "var(--book-dossier)" },
    regle:    { nom: "Règle",    teinte: "var(--book-regle)" },
    oeuvre:   { nom: "Œuvre",    teinte: "var(--book-oeuvre)" },
  };
  const genre = (b) => TYPES[String(b.type || "").toLowerCase()] || null;
  const teinte = (b) => b.couleur || (genre(b) || {}).teinte || "var(--braise)";

  // ---- Les notes : le carnet du JOUEUR, hors du monde ---------------------
  // Un volume de plus sur l'étagère, et le seul qui ne soit pas un objet de la
  // fiction : personne ne l'écrit dans la salle, aucun PNJ ne le lit, le MJ
  // n'y touche pas. Le joueur y met ce qu'il veut, tel quel, et ça reste. Il
  // est toujours à portée — on ne pose pas ses propres notes sur une table, et
  // l'on n'a pas à traverser le château pour noter un nom.
  const NOTES = "vos-notes";
  const NOTE = { id: NOTES, notes: true, titre: "Vos notes",
                 couleur: "var(--book-carnet)" };
  let notes = "";          // ce qu'il y a dans la zone, à la frappe près
  let notesEcrit = null;   // ce que le serveur a effectivement gardé
  let notesMinuteur = null;
  let notesEtat = "";      // la mention sous la zone : « Gardé. »

  function direEtat(m) {
    notesEtat = m;
    const el = document.getElementById("book-notes-etat");
    if (el) el.textContent = m;
  }

  function enregistrer() {
    clearTimeout(notesMinuteur);
    if (notesEcrit === null || notes === notesEcrit) return;
    const envoi = notes;
    fetch("/notes", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texte: envoi }),
    }).then((r) => {
      if (!r.ok) throw new Error("refus");
      notesEcrit = envoi;
      if (notes === envoi) direEtat("Gardé.");
    }).catch(() => direEtat("Pas gardé — le serveur n'a pas répondu."));
  }

  // On n'écrit pas à chaque touche : on attend que la main s'arrête.
  function planifier() {
    direEtat("…");
    clearTimeout(notesMinuteur);
    notesMinuteur = setTimeout(enregistrer, 700);
  }

  function chargerNotes() {
    fetch("/notes").then((r) => r.json()).then((d) => {
      // Une relecture ne doit pas manger une phrase en train d'être tapée :
      // ce qui n'est pas encore parti au serveur reste ce qui fait foi.
      if (notesEcrit !== null && notes !== notesEcrit) return;
      notes = (d && typeof d.texte === "string") ? d.texte : "";
      notesEcrit = notes;
      const z = document.getElementById("book-notes-zone");
      if (z && z !== document.activeElement) z.value = notes;
    }).catch(() => { if (notesEcrit === null) notesEcrit = ""; });
  }

  function carteNotes() {
    const art = document.createElement("article");
    art.className = "book book-notes";
    art.style.setProperty("--book-teinte", teinte(NOTE));

    const t = document.createElement("h3");
    t.textContent = NOTE.titre;
    const et = document.createElement("span");
    et.className = "book-genre";
    et.textContent = "De votre main";
    t.appendChild(et);
    art.appendChild(t);

    const s = document.createElement("div");
    s.className = "book-sous-titre";
    s.textContent = "Hors du monde : nul ne le lit, et rien de ce qui s'y écrit n'a lieu.";
    art.appendChild(s);

    const zone = document.createElement("textarea");
    zone.id = "book-notes-zone";
    zone.className = "book-notes-zone";
    zone.spellcheck = false;
    zone.placeholder = "Ce que vous voulez garder — un nom, un chiffre, une rancune.";
    zone.value = notes;
    zone.addEventListener("input", () => { notes = zone.value; planifier(); });
    zone.addEventListener("blur", enregistrer);
    art.appendChild(zone);

    const etat = document.createElement("div");
    etat.id = "book-notes-etat";
    etat.className = "book-notes-etat";
    etat.textContent = notesEtat;
    art.appendChild(etat);
    return art;
  }

  function hote() { return document.getElementById("books"); }
  const salleCourante = () =>
    (window.Plan && Plan.salle) ? Plan.salle() : null;
  const chateauCourant = () =>
    (window.Plan && Plan.chateau) ? Plan.chateau() : null;

  function nomSalle(id) {
    const p = (window.Plans || {})[chateauCourant()];
    const s = p && (p.salles || []).find((x) => x.id === id);
    return s ? s.nom : null;
  }

  const moi = () => (window.Moi && window.Moi.personnage_id) || null;
  const present = (id) => !!(window.Presents && window.Presents[id]);
  const nomActeur = (id) => {
    const p = (window.Presents || {})[id];
    if (p && p.nom) return p.nom;
    const f = window.Gens && Gens.qui ? Gens.qui(id) : null;
    return (f && f.nom) || String(id || "").replace(/-/g, " ");
  };

  // Un livre posé : il appartient au château, et l'on peut aller le chercher.
  // On ne l'a d'abord montré que dans SA salle — et l'on a vu ce que ça donne :
  // celle qui tient les écritures descend à la porte du Dragon, et le registre
  // des communications disparaît de son écran. Un registre de maison n'est pas
  // un secret, c'est un meuble : il reste consultable de tout le château, et
  // l'on dit simplement où il se trouve. Ce qui reste strict, c'est le carnet
  // que quelqu'un porte sur lui.
  function poseIci(b) {
    if (!b.salle_id) return false;
    const chateau = chateauCourant();
    return !b.lieu_id || !chateau || b.lieu_id === chateau;
  }

  // Est-il sous la main, ou faut-il monter le chercher ?
  const sousLaMain = (b) => !!b.salle_id && b.salle_id === salleCourante();

  // Un livre porté : il vaut ce que vaut la présence de son porteur. Le mien
  // est toujours sur moi ; celui d'un autre ne s'ouvre que s'il est dans la
  // salle, et jamais s'il le tient pour lui.
  function porteIci(b) {
    if (!b.acteur_id) return false;
    if (b.acteur_id === moi()) return true;
    if (b.prive) return false;
    return present(b.acteur_id);
  }

  // Ceux qu'on peut ouvrir d'où l'on est. Les notes du joueur ferment toujours
  // la marche : elles ne sont nulle part dans le château, donc partout.
  function ici() {
    const dedans = books ? books.filter((b) => poseIci(b) || porteIci(b)) : [];
    dedans.push(NOTE);
    return dedans;
  }

  // Qui, dans la salle, porte quelque chose : c'est ce qui fait apparaître et
  // disparaître l'onglet quand un homme entre ou sort.
  function portants() {
    if (!books) return "";
    return books.filter(porteIci).map((b) => b.acteur_id).sort().join(",");
  }

  function lignesDe(b) {
    return (b.lignes || []).map((l) =>
      Array.isArray(l) ? { cellules: l } : (l || { cellules: [] }));
  }

  // Les appuis du MJ : **ce qui pèse** se rend en gras, comme dans le fil.
  // Un registre a besoin d'appuis plus qu'un récit : c'est là que tombent les
  // états et les liens (**acquis**, **contre**, **au loin**).
  const echappe = (s) => s.replace(/[&<>]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);

  function poser(el, texte) {
    const t = texte == null ? "" : String(texte);
    el.innerHTML = echappe(t).replace(/\*\*(\S(?:[^*]*\S)?)\*\*/g,
      '<b class="appui">$1</b>');
  }

  function carte(b) {
    const art = document.createElement("article");
    art.className = "book";
    art.style.setProperty("--book-teinte", teinte(b));

    const t = document.createElement("h3");
    t.textContent = b.titre || "Sans titre";
    const g = genre(b);
    if (g) {
      const et = document.createElement("span");
      et.className = "book-genre";
      et.textContent = g.nom;
      t.appendChild(et);
    }
    art.appendChild(t);
    if (b.sous_titre) {
      const s = document.createElement("div");
      s.className = "book-sous-titre";
      s.textContent = b.sous_titre;
      art.appendChild(s);
    }

    const lignes = lignesDe(b);
    // Un registre ouvert et encore vierge est une information : on montre ses
    // colonnes, réglées, et l'on dit qu'il attend sa première ligne.
    if (lignes.length || (b.colonnes || []).length) {
      const enveloppe = document.createElement("div");
      enveloppe.className = "book-table-enveloppe";
      const tab = document.createElement("table");
      tab.className = "book-table";
      if (b.colonnes && b.colonnes.length) {
        const thead = document.createElement("thead");
        const tr = document.createElement("tr");
        b.colonnes.forEach((c) => {
          const th = document.createElement("th");
          th.textContent = c;
          tr.appendChild(th);
        });
        thead.appendChild(tr);
        tab.appendChild(thead);
      }
      const tbody = document.createElement("tbody");
      lignes.forEach((l) => {
        const tr = document.createElement("tr");
        (l.cellules || []).forEach((c, i) => {
          const td = document.createElement("td");
          poser(td, c);
          // la note pend sous la dernière colonne : c'est une mention de marge
          if (l.note && i === (l.cellules.length - 1)) {
            const n = document.createElement("div");
            n.className = "book-note";
            poser(n, l.note);
            td.appendChild(n);
          }
          if (window.Entites) Entites.traiter(td);
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      tab.appendChild(tbody);
      enveloppe.appendChild(tab);
      art.appendChild(enveloppe);
    }

    (b.pages || []).forEach((p) => {
      const par = document.createElement("p");
      par.className = "book-page";
      poser(par, p);
      if (window.Entites) Entites.traiter(par);
      art.appendChild(par);
    });

    if (!lignes.length && !(b.pages || []).length) {
      const vide = document.createElement("p");
      vide.className = "book-page book-attente";
      vide.textContent = "Rien n'y est encore écrit.";
      art.appendChild(vide);
    }

    return art;
  }

  // D'où vient ce livre — ce qui tient lieu de sous-titre à son onglet.
  function provenance(b) {
    if (b.notes) return "Sur vous, hors du monde";
    if (poseIci(b)) {
      const nom = nomSalle(b.salle_id);
      if (sousLaMain(b)) return nom ? "Ici — " + nom : "Ici, sous la main";
      return nom ? "Reste " + (/^(Le |La |L')/.test(nom) ? "à " + nom : "dans " + nom)
                 : "Ailleurs dans le château";
    }
    return b.acteur_id === moi() ? "Sur vous" : "Porté par " + nomActeur(b.acteur_id);
  }

  // Plusieurs livres dans la même salle ne s'empilent pas : ils se rangent en
  // onglets, comme des volumes sur une étagère. On en ouvre un à la fois — un
  // homme ne lit pas deux registres en même temps.
  function rangs() {
    const dedans = ici();
    // ce qui est dans la salle d'abord, puis le sien, puis ce qu'il faudrait
    // aller chercher, puis ce que les autres portent
    return dedans.slice().sort((a, b) => {
      const rang = (x) => x.notes ? 4 : (sousLaMain(x) ? 0
        : (x.acteur_id === moi() ? 1 : (poseIci(x) ? 2 : 3)));
      return rang(a) - rang(b);
    });
  }

  function dessiner() {
    const h = hote();
    if (!h) return;
    // On refait l'étagère à neuf : si le joueur avait la main dans ses notes
    // (une salle qui change pendant qu'il écrit), on lui rend sa place à la
    // ligne près, sinon il retrouve son curseur au début du carnet.
    const z = document.getElementById("book-notes-zone");
    const ecrivait = z && z === document.activeElement
      ? { debut: z.selectionStart, fin: z.selectionEnd } : null;
    salleVue = salleCourante();
    portantsVus = portants();
    h.innerHTML = "";
    const corps = document.createElement("div");
    corps.className = "books-corps";

    const dedans = rangs();
    // L'étagère n'est jamais vide — le carnet du joueur y est toujours. Mais
    // une salle sans livre reste une information : on la dit au-dessus, plutôt
    // que de laisser croire qu'il n'y avait rien à y chercher.
    const seulesNotes = dedans.length === 1 && dedans[0].notes;
    if (seulesNotes && books) {
      const nom = nomSalle(salleVue);
      const ou = document.createElement("div");
      ou.className = "books-ou";
      ou.textContent = nom ? "Ce qui traîne ici — " + nom : "Ce qui traîne ici";
      corps.appendChild(ou);
      const p = document.createElement("p");
      p.className = "books-vide";
      p.textContent = "Rien à lire ici, et personne n'a sorti son carnet.";
      corps.appendChild(p);
    }

    // celui qu'on avait ouvert, s'il est encore à portée — sinon le premier
    if (!dedans.some((b) => b.id === ouvert)) ouvert = dedans[0].id;

    // la tranche des volumes : un onglet par livre, sa provenance en dessous.
    // À un seul livre, pas d'onglet — une étagère d'un seul volume n'en est
    // pas une, et la provenance suffit à dire d'où il sort.
    if (dedans.length > 1) {
      const tranche = document.createElement("div");
      tranche.className = "books-tranche";
      dedans.forEach((b) => {
        const bt = document.createElement("button");
        bt.className = "book-onglet" + (b.id === ouvert ? " actif" : "");
        bt.style.setProperty("--book-teinte", teinte(b));
        const g = genre(b);
        bt.title = (g ? g.nom + " — " : "") + provenance(b);
        const t = document.createElement("span");
        t.className = "book-onglet-titre";
        t.textContent = b.titre || "Sans titre";
        bt.appendChild(t);
        const o = document.createElement("span");
        o.className = "book-onglet-ou";
        o.textContent = provenance(b);
        bt.appendChild(o);
        bt.onclick = () => { ouvert = b.id; dessiner(); };
        tranche.appendChild(bt);
      });
      corps.appendChild(tranche);
    } else if (!seulesNotes) {
      const ou = document.createElement("div");
      ou.className = "books-ou";
      ou.textContent = provenance(dedans[0]);
      corps.appendChild(ou);
    }

    const lu = dedans.find((b) => b.id === ouvert);
    if (lu) corps.appendChild(lu.notes ? carteNotes() : carte(lu));
    h.appendChild(corps);

    if (ecrivait) {
      const nz = document.getElementById("book-notes-zone");
      if (nz) {
        nz.focus();
        try { nz.setSelectionRange(ecrivait.debut, ecrivait.fin); } catch (e) {}
      }
    }
  }

  function charger() {
    if (charge) return;
    charge = true;
    chargerNotes();
    fetch("/books").then((r) => r.json()).then((d) => {
      books = (d && d.books) || [];
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
    }).catch(() => { charge = false; });
  }

  function relire() { charge = false; charger(); }

  charger();

  // Une page qu'on ferme sur une phrase à moitié tapée : le minuteur n'aura
  // pas le temps de tomber, et une requête ordinaire serait coupée en vol. Le
  // beacon part quand même.
  window.addEventListener("pagehide", () => {
    if (notesEcrit === null || notes === notesEcrit) return;
    try {
      navigator.sendBeacon("/notes", new Blob(
        [JSON.stringify({ texte: notes })], { type: "application/json" }));
    } catch (e) {}
  });

  window.addEventListener("DOMContentLoaded", () => {
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "books", nom: "Les livres", hote: "books", ordre: 6,
        // L'échelle était masquée là où il n'y avait rien à ouvrir — un livre
        // se consulte dans la salle où il est posé. Depuis que le joueur a son
        // carnet, il y a toujours quelque chose : `ici()` n'est jamais vide.
        dispo: () => ici().length > 0,
        reparu: () => {
          if (salleVue !== salleCourante() || portantsVus !== portants()) dessiner();
        },
      });
    }
    // la salle change sans prévenir personne, et un homme entre avec son carnet
    // sans rien annoncer non plus : on suit les deux de loin, ça ne coûte que
    // deux comparaisons de chaînes.
    setInterval(() => {
      if (salleVue === salleCourante() && portantsVus === portants()) return;
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
    }, 1000);
  });

  return { charger, relire };
})();
