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
//   boite                   — ou le COFFRET où il est rangé (etat/boites.json).
//                             Une boîte est un objet du monde comme lui : elle
//                             est posée ou portée, et elle donne sa place à
//                             tout ce qu'elle contient. Un volume rangé n'a
//                             donc ni salle, ni porteur, ni `prive` à lui — le
//                             serveur les lui recopie de la boîte avant de
//                             servir l'étagère
//   prive: true             — un carnet que son porteur ne montre pas : seul
//                             le joueur qui le porte le voit. Sans `acteur_id`
//                             il ne veut rien dire — un volume posé n'a pas de
//                             porteur : c'est `lecteurs` qu'il lui faut
//   lecteurs: [ "…", … ]    — les seuls qui puissent l'ouvrir. Ça ne DONNE
//                             rien : le volume garde ses règles de lieu, mais
//                             qui n'y est pas nommé ne le voit pas — le
//                             registre où vivent les noms, posé sur la table
//                             d'une salle où deux sièges entrent
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
  let chateauVu = undefined;  // le château du dernier CHARGEMENT
  let portantsVus = "";       // qui portait un carnet au dernier tracé
  let ferme = false;          // le serveur a refusé l'étagère : pas de siège
  let ouvert = null;          // le volume qu'on a sous les yeux
  let ouverteBoite = null;    // le coffret ouvert, si c'en est un
  let perime = false;         // on a déjà redemandé l'étagère une fois
  // Les coffrets à portée (etat/boites.json), tels que le serveur les sert.
  // Une boîte donne sa PLACE à ce qu'elle contient : le serveur a déjà recopié
  // sa salle, son porteur et son `prive` sur chacun de ses volumes, et l'on n'a
  // plus ici qu'à les regrouper sous un onglet.
  let boites = [];

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
  // Son emblème est une main, et pas une plume : ce volume-ci n'est écrit par
  // personne dans la fiction. C'est le seul de l'étagère dont le signe dise
  // « hors du monde ».
  const NOTE = { id: NOTES, notes: true, titre: "Vos notes", embleme: "✋",
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
    art.appendChild(tete(NOTE, t));

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

  // ---- Copier le volume -----------------------------------------------------
  // Un registre se recopie : c'est ce qu'on fait d'un registre depuis toujours.
  // On rend le volume en texte nu — le titre, les colonnes séparées par des
  // tabulations, les pages —, tel qu'il se lit, appuis compris : ce qui est
  // collé ailleurs doit être le même objet, pas un résumé.
  function texteDe(b) {
    if (b.notes) return notes;
    const l = [];
    l.push(b.titre || "Sans titre");
    if (b.sous_titre) l.push(b.sous_titre);
    tableauxDe(b).forEach((sec) => {
      if (!sec.colonnes.length && !sec.lignes.length) return;
      l.push("");
      if (sec.titre) l.push(sec.titre);
      if (sec.colonnes.length) l.push(sec.colonnes.join("\t"));
      sec.lignes.forEach((li) => {
        l.push((li.cellules || []).map((c) => c == null ? "" : String(c)).join("\t"));
        if (li.note) l.push("\t" + li.note);
      });
    });
    (b.pages || []).forEach((p) => {
      l.push("");
      // Une figure ne se recopie pas en texte : on dit qu'elle est là, avec sa
      // légende, plutôt que de laisser un trou dans la copie.
      if (p && typeof p === "object") {
        l.push("[figure" + (p.legende ? " — " + p.legende : "") + "]");
      } else {
        l.push(p == null ? "" : String(p));
      }
    });
    return l.join("\n");
  }

  // Le presse-papier moderne demande un contexte sûr ; la partie se joue aussi
  // par un tunnel qui n'en est pas toujours un. On garde la vieille manière en
  // second, sinon le bouton ment une fois sur deux.
  function auPressePapier(texte) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // Le refus arrive aussi quand l'API existe : page pas au premier plan,
      // permission coupée. On retombe alors sur la vieille manière au lieu de
      // dire au joueur que ça n'a pas marché.
      return navigator.clipboard.writeText(texte).catch(() => vieilleManiere(texte));
    }
    return vieilleManiere(texte);
  }

  function vieilleManiere(texte) {
    return new Promise((ok, non) => {
      const z = document.createElement("textarea");
      z.value = texte;
      z.setAttribute("readonly", "");
      z.style.cssText = "position:fixed;top:-9999px;opacity:0;";
      document.body.appendChild(z);
      z.select();
      let fait = false;
      try { fait = document.execCommand("copy"); } catch (e) {}
      document.body.removeChild(z);
      fait ? ok() : non(new Error("refus"));
    });
  }

  function boutonCopier(b) {
    const bt = document.createElement("button");
    bt.className = "book-copier";
    bt.type = "button";
    bt.textContent = "Copier";
    bt.title = "Recopier ce volume";
    bt.onclick = () => {
      const texte = texteDe(b);
      auPressePapier(texte).then(() => {
        bt.textContent = "Copié";
        bt.classList.add("fait");
      }).catch(() => {
        bt.textContent = "Pas copié";
      }).then(() => {
        setTimeout(() => {
          bt.textContent = "Copier";
          bt.classList.remove("fait");
        }, 1600);
      });
    };
    return bt;
  }

  // Le titre et sa main droite : on ne pose pas un bouton dans un titre, on
  // met les deux sur la même ligne.
  function tete(b, t) {
    const d = document.createElement("div");
    d.className = "book-tete";
    d.appendChild(t);
    d.appendChild(boutonCopier(b));
    return d;
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

  // Un volume peut NOMMER ses lecteurs. C'est ce qui manquait au carnet des
  // yeux : posé sur la Table Peinte, marqué `prive`, et donc privé de personne —
  // un `prive` sans porteur n'a pas de propriétaire, et le carnet s'ouvrait à
  // quiconque entrait dans le château. `lecteurs` ne DONNE rien : il retire. Le
  // volume reste où il est, avec ses règles de salle et de château ; simplement,
  // qui n'y est pas nommé ne l'ouvre pas. Un carnet qui ne quitte pas la chambre
  // ne se lit pas non plus depuis l'autre bout du royaume parce qu'on y a son nom.
  const lecteurs = (b) => Array.isArray(b.lecteurs) && b.lecteurs.length
    ? b.lecteurs : null;
  const permis = (b) => {
    const l = lecteurs(b);
    return !l || l.indexOf(moi()) !== -1;
  };

  // Ceux qu'on peut ouvrir d'où l'on est. Les notes du joueur ferment toujours
  // la marche : elles ne sont nulle part dans le château, donc partout.
  function ici() {
    const dedans = books ? books.filter(
      (b) => permis(b) && (poseIci(b) || porteIci(b))) : [];
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

  // ---- les tableaux d'un volume ---------------------------------------------
  // Un registre n'a qu'un tableau : c'est une seule sorte de chose, rangée. Une
  // AFFAIRE en a plusieurs, et pas par confort — ses états cibles, ses verrous,
  // ses clefs et ses actions n'ont pas les mêmes colonnes, et les entasser dans
  // une grille commune obligerait à inventer une colonne fourre-tout par type.
  // Donc `tables: [{titre, colonnes, lignes}]`, et le vieux couple
  // colonnes/lignes reste la forme courte du volume qui n'en a qu'un.
  function tableauxDe(b) {
    if (Array.isArray(b.tables) && b.tables.length) {
      return b.tables.map((t) => ({
        titre: t.titre || "",
        colonnes: t.colonnes || [],
        lignes: lignesDe(t),
      }));
    }
    return [{ titre: "", colonnes: b.colonnes || [], lignes: lignesDe(b) }];
  }

  // ---- Les renvois : un numéro écrit, et la ligne qui le définit ------------
  // Un cahier d'affaire ne se lit pas de haut en bas, il se lit en sautant :
  // « bloque 23100 », « dépend de 24000 », « ouvre 23010 ». Tout s'y cite par
  // son numéro, et jusqu'ici il fallait aller le chercher à la main, souvent
  // dans un autre volume. On accroche donc chaque numéro à la ligne qui le
  // porte — la donnée est déjà là, il n'y manquait que le chemin.
  //
  // L'ADRESSE d'une ligne est sa première cellule, dans un tableau dont la
  // première colonne s'appelle « N° ». Quatre à six chiffres : en deçà, un
  // numéro ne se distingue plus d'une quantité, et l'on accrocherait les douze
  // hommes de la barque. L'emoji qui précède un renvoi dit sa FAMILLE (état,
  // verrou, clef, action) — il ne sert pas à le reconnaître, le numéro suffit.
  const NUMERO = /\b\d{4,6}\b/g;
  const estAdresse = (t) => !!(t.colonnes && t.colonnes.length
    && /N°/.test(String(t.colonnes[0])));
  function numeroDe(l) {
    const c = (l.cellules || [])[0];
    const m = /^\s*(?:\*\*)?\s*(\d{4,6})\b/.exec(c == null ? "" : String(c));
    return m ? m[1] : null;
  }
  // Le millier d'un numéro : 23030 → « 23 ». C'est la série de son affaire.
  const serie = (n) => n.slice(0, -3);

  let renvois = new Map();   // un numéro → l'id du volume qui le définit

  // On n'indexe que ce qu'on peut OUVRIR d'où l'on est. Un renvoi vers un
  // volume hors de portée — dans un autre château, dans la poche d'un absent,
  // réservé à d'autres lecteurs — ne s'allume pas, et c'est juste : le
  // brouillard vaut ici comme ailleurs, et un numéro resté en texte nu dit
  // qu'on n'a pas ce registre-là sous la main.
  function indexer() {
    renvois = new Map();
    const cands = new Map();    // numéro → les volumes qui le portent
    const series = new Map();   // volume → combien de numéros par millier
    ici().forEach((b) => {
      if (b.notes) return;
      tableauxDe(b).forEach((t) => {
        if (!estAdresse(t)) return;
        t.lignes.forEach((l) => {
          const n = numeroDe(l);
          if (!n) return;
          if (!cands.has(n)) cands.set(n, []);
          cands.get(n).push(b.id);
          if (!series.has(b.id)) series.set(b.id, new Map());
          const s = series.get(b.id);
          s.set(serie(n), (s.get(serie(n)) || 0) + 1);
        });
      });
    });
    // Deux volumes peuvent porter le même numéro : un agrégat qui recopie un
    // état cible par affaire, et l'affaire qui le tient pour de bon. Celui qui
    // tient la SÉRIE gagne — l'agrégat n'a qu'un numéro du millier, l'affaire
    // en a trente. À égalité, le premier du fichier.
    cands.forEach((livres, n) => {
      let mieux = livres[0], score = -1;
      livres.forEach((id) => {
        const c = (series.get(id) || new Map()).get(serie(n)) || 0;
        if (c > score) { score = c; mieux = id; }
      });
      renvois.set(n, mieux);
    });
  }

  // Accrocher, dans un morceau déjà rendu, tous les numéros qui mènent quelque
  // part. On descend jusqu'aux nœuds de texte pour ne défaire ni le gras
  // d'appui ni les entités déjà posées ; on laisse tranquille la cellule qui
  // EST l'adresse (`data-ancre`) — un numéro n'a pas à se renvoyer à lui-même —
  // et l'on n'entre pas dans un dessin, où un bouton n'aurait pas de sens.
  function renvoyer(racine) {
    if (!renvois.size) return;
    const textes = [];
    (function marche(n) {
      for (let e = n.firstChild; e; e = e.nextSibling) {
        if (e.nodeType === 3) { textes.push(e); continue; }
        if (e.nodeType !== 1) continue;
        if (String(e.tagName).toLowerCase() === "svg") continue;
        if (e.dataset && e.dataset.ancre) continue;
        if (e.classList && e.classList.contains("book-renvoi")) continue;
        marche(e);
      }
    })(racine);
    textes.forEach((t) => {
      const s = t.nodeValue;
      NUMERO.lastIndex = 0;
      let m, i = 0, frag = null;
      while ((m = NUMERO.exec(s))) {
        const livre = renvois.get(m[0]);
        if (!livre) continue;
        if (!frag) frag = document.createDocumentFragment();
        if (m.index > i) frag.appendChild(document.createTextNode(s.slice(i, m.index)));
        frag.appendChild(lien(m[0], livre));
        i = m.index + m[0].length;
      }
      if (!frag) return;
      if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
      t.parentNode.replaceChild(frag, t);
    });
  }

  function lien(n, livre) {
    const bt = document.createElement("button");
    bt.type = "button";
    bt.className = "book-renvoi";
    bt.textContent = n;
    const b = (books || []).find((x) => x && x.id === livre);
    bt.title = b && b.titre ? b.titre : livre;
    bt.onclick = (e) => { e.preventDefault(); e.stopPropagation(); aller(n); };
    return bt;
  }

  // Y aller : le volume s'ouvre s'il n'était pas celui qu'on lisait, et la
  // ligne se signale un instant — sans quoi on atterrit dans une grille de
  // quarante lignes sans savoir laquelle on était venu chercher.
  function aller(n) {
    const livre = renvois.get(String(n));
    if (!livre) return false;
    if (livre !== ouvert && !ouvrir(livre)) return false;
    viser(String(n));
    return true;
  }

  function viser(n) {
    const h = hote();
    const tr = h && h.querySelector('tr[data-num="' + n + '"]');
    if (!tr) return;
    if (tr.scrollIntoView) tr.scrollIntoView({ behavior: "smooth", block: "center" });
    tr.classList.remove("book-vise");
    void tr.offsetWidth;   // relancer l'animation si l'on revient sur la même
    tr.classList.add("book-vise");
    setTimeout(() => tr.classList.remove("book-vise"), 2600);
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

  // Une page : du texte, ou une FIGURE. Un levé au pas, un plan de salle, un
  // arbre de parenté ne se disent pas en phrases — et le volume qui les porte
  // reste un volume, posé quelque part, qu'on peut refermer et emporter.
  // Le SVG arrive inliné par le serveur (voir inlinerFigure) ; s'il manque, on
  // ne laisse pas un trou muet : un dessin qu'on ne retrouve pas est une
  // information, et le joueur a le droit de savoir que la page existe.
  function page(p) {
    if (p && typeof p === "object" && p.figure) {
      const fig = document.createElement("figure");
      fig.className = "book-figure";
      if (p.figure_svg) {
        fig.innerHTML = p.figure_svg;
      } else {
        const manque = document.createElement("p");
        manque.className = "book-page book-attente";
        manque.textContent = "La feuille manque au volume.";
        fig.appendChild(manque);
      }
      if (p.legende) {
        const l = document.createElement("figcaption");
        poser(l, p.legende);
        if (window.Entites) Entites.traiter(l);
        fig.appendChild(l);
      }
      return fig;
    }
    const par = document.createElement("p");
    par.className = "book-page";
    poser(par, p);
    if (window.Entites) Entites.traiter(par);
    return par;
  }

  function carte(b) {
    const art = document.createElement("article");
    art.className = "book";
    art.style.setProperty("--book-teinte", teinte(b));

    const t = document.createElement("h3");
    if (b.embleme) {
      const e = document.createElement("span");
      e.className = "book-embleme";
      e.textContent = b.embleme;
      t.appendChild(e);
    }
    t.appendChild(document.createTextNode(b.titre || "Sans titre"));
    const g = genre(b);
    if (g) {
      const et = document.createElement("span");
      et.className = "book-genre";
      et.textContent = g.nom;
      t.appendChild(et);
    }
    art.appendChild(tete(b, t));
    if (b.sous_titre) {
      const s = document.createElement("div");
      s.className = "book-sous-titre";
      s.textContent = b.sous_titre;
      art.appendChild(s);
    }

    const tableaux = tableauxDe(b);
    let rien = 0;
    tableaux.forEach((sec) => {
      const lignes = sec.lignes;
      rien += lignes.length;
      // Un registre ouvert et encore vierge est une information : on montre ses
      // colonnes, réglées, et l'on dit qu'il attend sa première ligne.
      if (!lignes.length && !sec.colonnes.length) return;
      // Le titre d'un tableau se pose AU-DESSUS et hors de la grille : dans une
      // <caption>, il se collerait au tableau à la copie et se perdrait au
      // défilement horizontal, qui est justement le cas d'une affaire large.
      if (sec.titre) {
        const h = document.createElement("div");
        h.className = "book-table-titre";
        poser(h, sec.titre);
        art.appendChild(h);
      }
      const enveloppe = document.createElement("div");
      enveloppe.className = "book-table-enveloppe";
      const tab = document.createElement("table");
      tab.className = "book-table";
      if (sec.colonnes.length) {
        const thead = document.createElement("thead");
        const tr = document.createElement("tr");
        sec.colonnes.forEach((c) => {
          const th = document.createElement("th");
          th.textContent = c;
          tr.appendChild(th);
        });
        thead.appendChild(tr);
        tab.appendChild(thead);
      }
      const tbody = document.createElement("tbody");
      // Une ligne qui porte un numéro devient une adresse : c'est elle qu'on
      // vise quand on clique le renvoi qui la cite, d'ici ou d'un autre volume.
      const adresse = estAdresse(sec);
      lignes.forEach((l) => {
        const tr = document.createElement("tr");
        const num = adresse ? numeroDe(l) : null;
        if (num) tr.dataset.num = num;
        (l.cellules || []).forEach((c, i) => {
          const td = document.createElement("td");
          if (num && i === 0) td.dataset.ancre = "1";
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
    });

    (b.pages || []).forEach((p) => art.appendChild(page(p)));

    if (!rien && !(b.pages || []).length) {
      const vide = document.createElement("p");
      vide.className = "book-page book-attente";
      vide.textContent = "Rien n'y est encore écrit.";
      art.appendChild(vide);
    }

    // En dernier, sur le volume entier : les cellules, les notes de marge, les
    // titres de tableau et les pages suivies citent tous des numéros.
    renvoyer(art);

    return art;
  }

  // Le coffret d'un volume, s'il est rangé quelque part.
  const coffret = (b) =>
    (b && b.boite && boites.find((c) => c.id === b.boite)) || null;

  // La carte d'un coffret : ce qu'il y a dedans, ligne à ligne. C'est ce qu'on
  // voit quand on l'ouvre — on ne se met pas à lire un volume au hasard, on
  // regarde ce que la boîte contient et l'on prend celui qu'on veut. Chaque
  // ligne s'ouvre d'un clic.
  function carteBoite(e) {
    const c = e.boite;
    const art = document.createElement("article");
    art.className = "book book-coffret-carte";
    art.style.setProperty("--book-teinte", teinte(c));

    const ligneTitre = document.createElement("div");
    ligneTitre.className = "book-tete";
    const t = document.createElement("h3");
    if (c.embleme) {
      const em = document.createElement("span");
      em.className = "book-embleme";
      em.textContent = c.embleme;
      t.appendChild(em);
    }
    t.appendChild(document.createTextNode(c.titre || "Sans titre"));
    const g = document.createElement("span");
    g.className = "book-genre";
    g.textContent = "Coffret";
    t.appendChild(g);
    ligneTitre.appendChild(t);
    art.appendChild(ligneTitre);

    const s = document.createElement("div");
    s.className = "book-sous-titre";
    s.textContent = (c.sous_titre ? c.sous_titre + " " : "")
      + "— " + provenance(c) + ", " + e.livres.length
      + (e.livres.length > 1 ? " volumes." : " volume.");
    art.appendChild(s);

    const env = document.createElement("div");
    env.className = "book-table-enveloppe";
    const tab = document.createElement("table");
    tab.className = "book-table book-coffret-table";
    const tbody = document.createElement("tbody");
    e.livres.forEach((b) => {
      const tr = document.createElement("tr");
      tr.className = "book-coffret-ligne";
      tr.tabIndex = 0;
      tr.title = "Ouvrir — " + (b.titre || "ce volume");
      const ouvrir = () => { ouvert = b.id; dessiner(); };
      tr.onclick = ouvrir;
      tr.onkeydown = (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); ouvrir(); }
      };
      const signe = document.createElement("td");
      signe.className = "book-coffret-signe";
      signe.textContent = b.embleme || "";
      const nom = document.createElement("td");
      nom.className = "book-coffret-nom";
      nom.appendChild(document.createTextNode(b.titre || "Sans titre"));
      const gg = genre(b);
      if (gg) {
        const m = document.createElement("span");
        m.className = "book-genre";
        m.textContent = gg.nom;
        nom.appendChild(m);
      }
      const mot = document.createElement("td");
      mot.className = "book-coffret-mot";
      // Le sous-titre d'un volume dit de quelle main il est et quand il fut
      // ouvert : c'est long, et l'on ne vient ici que pour choisir.
      const d = (b.sous_titre || "").trim();
      mot.textContent = d.length > 96 ? d.slice(0, 95).replace(/[\s,;—-]+$/, "") + "…" : d;
      tr.appendChild(signe);
      tr.appendChild(nom);
      tr.appendChild(mot);
      tbody.appendChild(tr);
    });
    tab.appendChild(tbody);
    env.appendChild(tab);
    art.appendChild(env);
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
  // Le plus frais devant. On rangeait par PROXIMITÉ — sous la main, puis le
  // sien, puis ce qu'il fallait aller chercher — et c'était une étagère : un
  // ordre qui ne bouge jamais, où le registre qu'on vient de remplir reste
  // enfoui au même endroit qu'hier. Une table de travail se range autrement :
  // ce qu'on vient de toucher est sur le dessus.
  //
  // La fraîcheur se lit d'abord dans `date_maj` (une date de jeu, écrite par
  // qui touche le volume), et à défaut dans la POSITION dans books.json : un
  // volume ajouté l'a été après les autres, et c'est déjà une information. Rien
  // de neuf à tenir, donc, et un volume sans date n'est pas puni — il garde son
  // rang d'arrivée.
  const quand = (b) => {
    const d = b.date_maj;
    if (!d) return -1;
    return ((d.annee || 0) * 12 + (d.lune || 0)) * 30 * 1440
      + (d.jour || 0) * 1440 + (d.minute || 0);
  };

  function rangs() {
    const dedans = ici();
    // L'ordre du fichier, pour départager ceux qui n'ont pas de date : plus
    // loin dans books.json veut dire posé plus tard.
    const arrivee = new Map((books || []).map((b, i) => [b.id, i]));
    return dedans.slice().sort((a, b) => {
      // Les notes du joueur ferment toujours la marche : elles ne sont pas du
      // monde, elles n'ont pas de fraîcheur, et elles sont toujours à portée.
      if (a.notes !== b.notes) return a.notes ? 1 : -1;
      const da = quand(a), db = quand(b);
      if (da !== db && (da >= 0 || db >= 0)) return db - da;
      return (arrivee.get(b.id) || 0) - (arrivee.get(a.id) || 0);
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
    // L'index des numéros suit l'étagère : un homme qui sort avec son cahier
    // emporte les renvois qui y menaient.
    indexer();
    h.innerHTML = "";
    const corps = document.createElement("div");
    corps.className = "books-corps";

    const dedans = rangs();
    // L'étagère n'est jamais vide — le carnet du joueur y est toujours. Mais
    // une salle sans livre reste une information : on la dit au-dessus, plutôt
    // que de laisser croire qu'il n'y avait rien à y chercher.
    const seulesNotes = dedans.length === 1 && dedans[0].notes;
    if (seulesNotes && books) {
      const ou = document.createElement("div");
      ou.className = "books-ou";
      const p = document.createElement("p");
      p.className = "books-vide";
      // Une page sans siège n'a pas une étagère vide : elle n'a pas d'étagère.
      // Le serveur ferme et le dit ; on ne fait pas croire qu'il n'y avait rien
      // à chercher dans la salle — le joueur irait chercher la faute au MJ.
      if (ferme) {
        ou.textContent = "L'étagère est close";
        p.textContent = "Cette page n'est assise à aucun siège : ouvrez le jeu "
          + "par votre lien, et vos livres reviennent.";
      } else {
        const nom = nomSalle(salleVue);
        ou.textContent = nom ? "Ce qui traîne ici — " + nom : "Ce qui traîne ici";
        p.textContent = "Rien à lire ici, et personne n'a sorti son carnet.";
      }
      corps.appendChild(ou);
      corps.appendChild(p);
    }

    // La tranche du haut mêle les COFFRETS et ce qui traîne à côté d'eux : une
    // table de travail porte des boîtes et des registres posés dessus, et l'on
    // n'oblige personne à ranger. Un coffret prend le rang de son volume le
    // plus frais — ce qu'on vient de toucher reste sur le dessus.
    const entrees = [];
    const parBoite = new Map();
    dedans.forEach((b) => {
      const c = coffret(b);
      if (!c) { entrees.push({ livre: b, livres: [b] }); return; }
      let e = parBoite.get(c.id);
      if (!e) {
        e = { boite: c, livres: [] };
        parBoite.set(c.id, e);
        entrees.push(e);
      }
      e.livres.push(b);
    });
    // Ce qu'on a sous les yeux : un coffret ouvert, ou un volume — jamais les
    // deux. Un coffret ouvert sans volume montre sa carte : ce qu'il y a
    // dedans, ligne à ligne. C'est ça, ouvrir une boîte.
    let active = ouverteBoite ? (parBoite.get(ouverteBoite) || null) : null;
    if (active) {
      if (ouvert && !active.livres.some((b) => b.id === ouvert)) ouvert = null;
    } else {
      ouverteBoite = null;
      active = entrees.find((e) => e.livres.some((b) => b.id === ouvert)) || null;
      if (active && active.boite) ouverteBoite = active.boite.id;
    }
    // Plus rien de retenu (on a changé de salle, un homme est sorti) : on
    // rouvre ce qui est sur le dessus de la pile.
    if (!active) {
      active = entrees[0];
      if (active.boite) { ouverteBoite = active.boite.id; ouvert = null; }
      else { ouverteBoite = null; ouvert = active.livre.id; }
    }

    // un onglet : un signe, un titre, et d'où la chose sort.
    function onglet(o, actif, sous, clic) {
      const bt = document.createElement("button");
      bt.className = "book-onglet" + (actif ? " actif" : "");
      bt.style.setProperty("--book-teinte", teinte(o));
      const g = genre(o);
      bt.title = (g ? g.nom + " — " : "") + sous;
      const t = document.createElement("span");
      t.className = "book-onglet-titre";
      // L'emblème : de quoi reconnaître un volume SANS le lire. Trente onglets
      // de titres se ressemblent tous au coin de l'œil ; un signe et une
      // couleur, non. C'est la même fonction que les emblèmes d'office sur le
      // plan du château — on cherche une forme, pas un mot.
      if (o.embleme) {
        const e = document.createElement("span");
        e.className = "book-onglet-embleme";
        e.textContent = o.embleme;
        t.appendChild(e);
      }
      t.appendChild(document.createTextNode(o.titre || "Sans titre"));
      bt.appendChild(t);
      const ou = document.createElement("span");
      ou.className = "book-onglet-ou";
      ou.textContent = sous;
      bt.appendChild(ou);
      bt.onclick = clic;
      return bt;
    }

    const compte = (n) => n + (n > 1 ? " volumes" : " volume");

    // À une seule entrée, pas d'onglet — une étagère d'un seul volume n'en est
    // pas une, et la provenance suffit à dire d'où il sort.
    if (entrees.length > 1) {
      const tranche = document.createElement("div");
      tranche.className = "books-tranche";
      entrees.forEach((e) => {
        const actif = e === active;
        if (e.boite) {
          // Un clic OUVRE le coffret : on voit ce qu'il y a dedans. Il ne se
          // met pas à lire un volume à notre place — on ouvre une boîte pour
          // regarder ce qu'elle contient, on prend le volume ensuite.
          const bt = onglet(
            e.boite, actif,
            provenance(e.boite) + " — " + compte(e.livres.length),
            () => { ouverteBoite = e.boite.id; ouvert = null; dessiner(); });
          bt.classList.add("book-coffret");
          if (actif) bt.classList.add("ouvert");
          tranche.appendChild(bt);
        } else {
          tranche.appendChild(onglet(
            e.livre, actif, provenance(e.livre),
            () => { ouverteBoite = null; ouvert = e.livre.id; dessiner(); }));
        }
      });
      tranche.classList.add("books-coffrets");
      corps.appendChild(tranche);
    } else if (!seulesNotes) {
      const ou = document.createElement("div");
      ou.className = "books-ou";
      ou.textContent = active && active.boite
        ? active.boite.titre + " — " + provenance(active.boite)
        : provenance(dedans[0]);
      corps.appendChild(ou);
    }

    // Un volume pris dans le coffret : on garde sa tranche au-dessus, pour
    // pouvoir passer de l'un à l'autre sans refermer la boîte.
    if (active.boite && ouvert && active.livres.length > 1) {
      const dedansBoite = document.createElement("div");
      dedansBoite.className = "books-tranche books-dedans";
      active.livres.forEach((b) => {
        const g = genre(b);
        dedansBoite.appendChild(onglet(
          b, b.id === ouvert, g ? g.nom : provenance(b),
          () => { ouvert = b.id; dessiner(); }));
      });
      corps.appendChild(dedansBoite);
    }

    const lu = ouvert ? dedans.find((b) => b.id === ouvert) : null;
    if (lu) corps.appendChild(lu.notes ? carteNotes() : carte(lu));
    else if (active.boite) corps.appendChild(carteBoite(active));
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
    // Le serveur ne sert que l'étagère de CE siège, et il la coupe au château
    // où l'on se trouve : la réponse dépend donc d'où l'on est au moment où on
    // la demande. On retient ce château-là — un homme qui débarque ailleurs
    // doit redemander l'étagère, sans quoi il emporte celle qu'il a quittée.
    chateauVu = chateauCourant();
    fetch("/books").then((r) => r.json()).then((d) => {
      books = (d && d.books) || [];
      boites = (d && d.boites) || [];
      ferme = !!(d && d.siege === false);
      // Une page ouverte AVANT que le serveur ait appris les coffrets garde sa
      // liste jusqu'au prochain changement de château — c'est-à-dire, le plus
      // souvent, jamais : les volumes rangés disparaissent de l'étagère et l'on
      // croit le rangement cassé. Des livres qui se disent dans une boîte sans
      // qu'aucune boîte ne descende : la liste est périmée, on la redemande.
      // Une seule fois : si le serveur ne sait décidément rien des coffrets,
      // c'est qu'il est vieux, et redemander toutes les quatre secondes ne le
      // rajeunira pas.
      if (!perime && !boites.length && books.some((b) => b.boite) && !ferme) {
        perime = true;
        charge = false;
        setTimeout(charger, 4000);
      }
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
      // Changer de château, c'est changer d'étagère : ce n'est plus un tracé à
      // refaire, c'est une liste à redemander. On ne rappelle rien tant qu'on
      // ne sait pas où l'on est (au chargement, `chateauCourant()` est nul le
      // temps que la carte arrive) — le serveur, lui, l'a toujours su.
      const ch = chateauCourant();
      if (ch && !chateauVu) chateauVu = ch;       // la carte vient d'arriver
      else if (ch && chateauVu !== ch) { relire(); return; }
      if (salleVue === salleCourante() && portantsVus === portants()) return;
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
    }, 1000);
  });

  // `page` et `poser` sortent du module pour le fil : un extrait montré en
  // scène doit avoir EXACTEMENT la mine qu'il aura dans le volume, sans quoi
  // le joueur croit voir deux objets là où il n'y en a qu'un.
  // OUVRIR UN VOLUME NOMMÉ, depuis ailleurs que l'étagère — c'est ce qui permet
  // au fil de dire « porté au registre » avec un lien qui y mène. Sans ça, le
  // joueur doit croire le MJ sur parole que ce qui s'est dit a été écrit.
  function ouvrir(livreId) {
    if (!livreId) return false;
    const trouve = (books || []).find((b) => b && b.id === livreId);
    if (!trouve) return false;
    ouvert = livreId;
    ouverteBoite = trouve.boite || null;
    if (window.Plan && Plan.montrer) Plan.montrer("books");
    dessiner();
    const h = hote();
    if (h && h.scrollIntoView) h.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return true;
  }

  // `aller` sort aussi : le fil peut vouloir renvoyer à une ligne précise —
  // « c'est écrit au 23100 » — et non seulement au volume.
  return { charger, relire, page, poser, teinte, genre, ouvrir, aller }
})();
