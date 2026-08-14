// gens.js — la quatrième échelle du décor : « Les gens ».
// Une carte porte des lieux, celle-ci porte des visages. Le joueur y retrouve
// qui est qui — le nom, le rôle, la maison — rangé par camp affiché.
// Ce n'est PAS une fiche de renseignement : ni position, ni intentions, ni
// allégeance réelle. Ce que la cour sait de la cour, rien de plus.
// Un clic sur quelqu'un = un moment de pensée, même canal que les entités.
"use strict";
window.Gens = (() => {
  let gens = null;
  let charge = false;
  let filtre = "";
  // le registre sert deux choses : la vue « Les gens », et le fil, qui a besoin
  // du nom et du rôle de qui parle même quand il n'est pas dans la salle.
  const parId = new Map();
  const attendent = [];
  // le registre arrive après les premiers items du flux : qui a besoin des
  // visages (la galerie) se fait rappeler plutôt que de sonder en boucle
  const aPrevenir = [];

  const CAMPS = [
    { id: "noir", nom: "Les Noirs" },
    { id: "vert", nom: "Les Verts" },
    { id: "neutre", nom: "Ni l'un ni l'autre" },
  ];

  function hote() { return document.getElementById("gens"); }

  function charger() {
    if (charge) return;
    charge = true;
    fetch("/gens").then((r) => r.json()).then((d) => {
      gens = d.gens || [];
      parId.clear();
      gens.forEach((p) => parId.set(p.id, p));
      dessiner();
      // ce qui a été rendu avant que le registre n'arrive se répare ici
      while (attendent.length) reparer(attendent.pop());
      while (aPrevenir.length) { try { aPrevenir.pop()(); } catch (e) {} }
    }).catch(() => { charge = false; });
  }

  // Ce que le fil doit savoir de quelqu'un : son nom, son rôle, son visage.
  // La salle courante prime (le MJ peut y écrire un titre de circonstance),
  // le registre comble, et un inconnu garde au moins un nom lisible.
  function qui(id) {
    const p = (window.Presents || {})[id] || {};
    const f = parId.get(id) || {};
    return {
      nom: p.nom || f.nom || String(id || "").replace(/-/g, " ")
        .replace(/(^|\s)\p{Ll}/gu, (c) => c.toUpperCase()),
      titre: p.titre || f.titre || "",
      portrait_svg: p.portrait_svg || f.portrait_svg || "",
    };
  }

  // Une entrée du fil rendue avant le chargement : on lui pose son rôle après
  // coup plutôt que de la laisser orpheline.
  function reparer(entree) {
    if (!entree || !entree.isConnected) return;
    const f = parId.get(entree.dataset.qui);
    const nom = entree.querySelector(".chr-qui");
    if (!f || !nom || nom.querySelector(".chr-role")) return;
    if (nom.firstChild && nom.firstChild.nodeType === 3) nom.firstChild.nodeValue = f.nom;
    if (!f.titre) return;
    const s = document.createElement("span");
    s.className = "chr-role";
    s.innerHTML = '<i class="emb">' + Bus.embleme(f.titre) + "</i>";
    s.appendChild(document.createTextNode(f.titre));
    nom.appendChild(s);
  }

  // Le fil marque qui il a rendu ; tant que le registre n'est pas là, il note.
  function marquer(entree, id) {
    if (!entree) return entree;
    entree.dataset.qui = id;
    if (!parId.size) attendent.push(entree);
    return entree;
  }

  function medaillon(p) {
    const d = document.createElement("div");
    d.className = "gens-gars" + (p.joueur ? " gens-joueur" : "");
    d.title = p.titre || p.nom;
    d.innerHTML =
      // même visage que dans la salle et dans le fil : `visage.js` le dessine,
      // avec son cadrage, son anneau d'office et sa loupe au survol
      Visage.html(p, { classe: "gens-face" }) +
      '<div class="gens-dit"><b>' + p.nom + "</b>" +
      // le rôle porte son emblème, comme dans le fil et dans la salle : on
      // reconnaît un mestre, un capitaine ou un septon avant de lire le mot.
      (p.titre ? '<small><i class="emb">' + Bus.embleme(p.titre) + "</i>" +
        p.titre + "</small>" : "") + "</div>";
    d.onclick = () => Entites.penser(p.id, "personnage", p.nom);
    return d;
  }

  // Le même médaillon, à qui n'a qu'un id — le reste du décor s'en sert pour
  // désigner quelqu'un sans redessiner un visage à sa façon : deux dessins du
  // même homme sont deux hommes à l'œil. Avant que le registre ne soit arrivé,
  // il rend ce qu'il a (le nom, souvent la face de la salle) ; `quand()` sert
  // à se faire rappeler pour redessiner avec le portrait.
  function medaillonDe(id) {
    return medaillon(parId.get(id) || Object.assign({ id: id }, qui(id)));
  }

  function dessiner() {
    const h = hote();
    if (!h) return;
    if (!gens) { h.innerHTML = '<p class="gens-vide">…</p>'; return; }
    h.innerHTML = "";

    const barre = document.createElement("div");
    barre.className = "gens-barre";
    const ch = document.createElement("input");
    ch.type = "search";
    ch.placeholder = "Chercher un nom, un rôle…";
    ch.value = filtre;
    ch.oninput = () => { filtre = ch.value; lister(corps); };
    barre.appendChild(ch);
    const bt = document.createElement("button");
    bt.type = "button";
    bt.className = "gens-tri";
    bt.textContent = rangement === "vus" ? "↕ rencontres" : "↕ armorial";
    bt.title = rangement === "vus"
      ? "Rangés par salle traversée, la plus récente en tête — cliquer pour l'armorial"
      : "Rangés par camp et par maison — cliquer pour l'ordre des rencontres";
    bt.onclick = () => {
      rangement = rangement === "vus" ? "camp" : "vus";
      try { localStorage.setItem(CLE_RANG, rangement); } catch (e) {}
      dessiner();
    };
    barre.appendChild(bt);
    h.appendChild(barre);

    const corps = document.createElement("div");
    corps.className = "gens-corps";
    h.appendChild(corps);
    lister(corps);
  }

  // ─────────────────────────────────────────── « Mon gouvernement »
  //
  // LA MÊME COUR, VUE PAR LA CHARGE ET NON PAR LE CAMP. Le reste de cet écran
  // range des visages par bord : c'est ce qu'on demande quand on cherche qui
  // est qui. Il ne dit rien de ce que le plan attend de chacun, et c'est
  // l'autre question — celle qu'on se pose en distribuant le travail.
  //
  // CE N'EST PAS UN CONSEIL, C'EST UN TABLEAU. `docs/criticite.md` pose la
  // borne et elle est dure : le joueur peut lire la colonne, personne dans la
  // fiction ne parle en « perte 15 ». Donc aucune flèche, aucun « commencez
  // par », et le rangement suit le NUMÉRO D'OFFICE — l'ordre du registre, qui
  // ne dit rien. Un rangement par criticité aurait désigné un homme sans qu'on
  // l'ait demandé, ce qui est un avis déguisé en tri.
  //
  // SANS CALCUL, PAS DE SECTION. Le tableau ne s'annonce pas et ne laisse pas
  // de place vide : tant que `/criticite` n'est pas rentré, « Les gens » est
  // exactement l'écran qu'il était.
  let crit = null;
  let critDemande = false;
  function chargerCharge() {
    if (critDemande) return;
    critDemande = true;
    fetch("/criticite").then((r) => r.json()).then((d) => {
      crit = (d && d.charge) ? d : null;
      if (crit && gens) dessiner();
      // LE CALCUL RENTRE AVANT L'ÉTAGÈRE QUI LE BORNE, et c'est l'ordre normal :
      // `/criticite` est en cache côté serveur quand `/books` ne l'est pas. Sans
      // ce rappel, le tableau se dessinait une fois, sur une étagère vide, donc
      // sur zéro cahier visible — et ne se redessinait plus. On repasse tant que
      // l'étagère n'est pas là, et l'on renonce au bout d'une quinzaine de
      // secondes plutôt que de battre indéfiniment pour un siège qui n'en a pas.
      let restant = 15;
      const guetter = () => {
        if (!crit || !restant--) return;
        const v = (window.Books && Books.affairesVues) ? Books.affairesVues() : null;
        if (v && v.size) { if (gens) dessiner(); return; }
        setTimeout(guetter, 1000);
      };
      guetter();
    }).catch(() => { critDemande = false; });
  }

  // LE CALCUL VOIT TOUT LE PLAN ; CE TABLEAU NE COMPTE QUE CE QUE CE SIÈGE PEUT
  // OUVRIR. `/criticite` ne connaît ni siège ni `lecteurs` : la charge d'un
  // homme y inclut les cahiers de la Néra, qui sont à un autre joueur. On somme
  // donc cahier par cahier, en ne retenant que ceux de l'étagère — c'est
  // `Books.affairesVues()`, la borne déjà écrite pour le volume « Les pas », et
  // non une seconde du même genre. Sans étagère chargée, la somme est nulle et
  // l'homme tombe du tableau, ce qui vaut mieux qu'un chiffre gonflé.
  function sommeVue(parAffaire, vues) {
    let s = 0;
    Object.keys(parAffaire || {}).forEach((a) => {
      if (!a || vues.has(a)) s += parAffaire[a].s || 0;
    });
    return s;
  }

  // Le détail derrière la somme, sous la même borne d'étagère : par cahier, le
  // plus lourd en tête. C'est ce que l'infobulle montre — un total sans son
  // détail ne se vérifie pas, et un chiffre qu'on ne peut pas vérifier finit
  // par ne plus se lire.
  function detailVu(parAffaire, vues) {
    return Object.keys(parAffaire || {})
      .filter((a) => !a || vues.has(a))
      .map((a) => ({ a: a || "— hors cahier —", s: parAffaire[a].s || 0,
                     pas: parAffaire[a].pas || 0 }))
      .filter((d) => d.s > 0)
      .sort((x, y) => y.s - x.s);
  }

  // Les identifiants du plan et ceux du registre des gens ne se recouvrent pas
  // tout à fait — le plan écrit `jacaerys-velaryon` là où le registre écrit
  // `jacaerys`. On replie le court sur le long, jamais autrement, exactement
  // comme `rapprocher()` le fait côté script : une inclusion au milieu du mot
  // marierait deux inconnus.
  function figure(q) {
    if (parId.has(q)) return q;
    const c = gens.find((p) => q === p.id || q.indexOf(p.id + "-") === 0);
    return c ? c.id : null;
  }

  // ─────────────────────────────────────────── l'infobulle du tableau
  //
  // POURQUOI PAS `title`. Les quatre en-têtes en portaient un : il met une
  // seconde à sortir, se coupe où le système veut, ne tient pas une phrase de
  // deux lignes, et surtout il ne peut rien porter d'autre que du texte plat —
  // donc jamais le détail par cahier, qui est la seule chose qui rende un
  // chiffre vérifiable. On écrit le nôtre, et l'on RETIRE les `title` : deux
  // bulles pour la même colonne, c'est pire que pas de bulle du tout.
  //
  // ELLE EXPLIQUE, ELLE NE CONSEILLE PAS. Même borne que la table qu'elle
  // couvre : aucun « commencez par », aucune teinte de gravité, aucun palier.
  // Elle dit ce qui est compté et d'où ça vient — le reste est un avis.
  const gloses = new WeakMap();
  let bulle = null;

  function glose(el, html) {
    gloses.set(el, html);
    el.classList.add("gouv-glosee");
    el.removeAttribute("title");   // jamais les deux
    return el;
  }

  function montrerGlose(el) {
    const html = gloses.get(el);
    if (!html) return;
    if (!bulle) {
      bulle = document.createElement("div");
      bulle.className = "gouv-bulle";
      document.body.appendChild(bulle);
    }
    bulle.innerHTML = html;
    bulle.style.visibility = "hidden";
    bulle.style.display = "block";
    bulle.style.maxHeight = "";
    // On se pose sous la case, et au-dessus s'il n'y a plus de place — le
    // tableau vit en bas d'une colonne qui défile, donc le cas du bas est le
    // cas normal, pas l'exception. Et quand aucun des deux côtés ne suffit
    // (une bulle de sept cahiers sur un écran bas), on prend le plus grand et
    // l'on BORNE la hauteur : une bulle coupée en bas d'écran se lit à moitié,
    // une bulle qui déborde ne se lit pas du tout.
    const r = el.getBoundingClientRect();
    const b = bulle.getBoundingClientRect();
    const marge = 8;
    const dessous = window.innerHeight - r.bottom - 6 - marge;
    const dessus = r.top - 6 - marge;
    const bas = b.height <= dessous || dessous >= dessus;
    if (b.height > Math.max(dessous, dessus)) {
      bulle.style.maxHeight = Math.max(80, Math.max(dessous, dessus)) + "px";
    }
    const h = bas ? r.bottom + 6
                  : Math.max(marge, r.top - bulle.getBoundingClientRect().height - 6);
    bulle.style.left = Math.round(Math.min(Math.max(marge, r.left),
      window.innerWidth - b.width - marge)) + "px";
    bulle.style.top = Math.round(h) + "px";
    bulle.style.visibility = "visible";
  }

  function cacherGlose() {
    if (bulle) bulle.style.display = "none";
  }

  // Un seul jeu d'écouteurs sur la table, et non un par case : cinquante lignes
  // font trois cents cases, et autant d'abonnements qui survivraient au
  // redessin. La bulle se ferme aussi au défilement — elle est en position
  // fixe, elle resterait accrochée à un chiffre qui a bougé.
  function brancherGloses(racine) {
    racine.addEventListener("mouseover", (e) => {
      const el = e.target.closest(".gouv-glosee");
      if (el && racine.contains(el)) montrerGlose(el);
    });
    racine.addEventListener("mouseout", (e) => {
      const el = e.target.closest(".gouv-glosee");
      if (el && !el.contains(e.relatedTarget)) cacherGlose();
    });
    window.addEventListener("scroll", cacherGlose, true);
  }

  const echappe = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // L'en-tête d'une bulle : le nom de la colonne, puis ce qu'elle compte.
  function bulleColonne(titre, corps, pied) {
    return '<div class="gouv-bulle-titre">' + titre + "</div>"
      + '<div class="gouv-bulle-corps">' + corps + "</div>"
      + (pied ? '<div class="gouv-bulle-pied">' + pied + "</div>" : "");
  }

  // LE PRIX D'UN PAS, DIT UNE FOIS. Les trois colonnes comptent la même chose —
  // une somme de criticités, pas un nombre de lignes —, et c'est la confusion
  // naturelle : on lit « 141 » comme cent quarante et un pas.
  const UNITE = "Ce n'est pas un compte de lignes : c'est une somme de "
    + "<b>criticités</b>. Un pas vaut ce que le plan perd s'il rate "
    + "(<i>perte</i>, mesurée en l'enlevant et en regardant ce qui devient "
    + "inatteignable) plus ce qui, ailleurs, attend sa pièce (<i>attendu</i>). "
    + "Un pas que quelqu'un d'autre peut faire vaut zéro et ne compte pas.";

  const COLONNES = {
    vu: bulleColonne("Vu — ce qui lui parvient",
      "Les pas des cahiers dont il est <b>tenu_par</b>. C'est la seule chose "
      + "qu'une dépêche lui porte aujourd'hui : le routage tient sur ce champ "
      + "et sur rien d'autre.", UNITE),
    sien: bulleColonne("Sien ailleurs — sa charge, le cahier d'un autre",
      "Des pas dont <b>son office répond</b> — c'est écrit dans la colonne "
      + "🪶 Office de la ligne — mais qui vivent dans un cahier tenu par "
      + "quelqu'un d'autre. Personne ne les lui cache : aucun chemin ne les "
      + "lui porte.", UNITE),
    tire: bulleColonne("On lui tire — un moyen qu'il tient",
      "Des pas qui engagent un <b>moyen dont il est « qui le tient »</b>, sans "
      + "que son nom soit sur la ligne. C'est la colonne invisible à tout "
      + "tableau de charge : quelqu'un est bloqué par lui, et il ne sait pas "
      + "qu'on l'attend.", UNITE),
    aveugle: bulleColonne("Aveugle — la part qu'aucun chemin ne porte",
      "<code>(sien + tiré) ÷ (vu + sien + tiré)</code>, tronqué. À 0 %, tout "
      + "ce qui le concerne est dans ses cahiers et le routage suffit. À "
      + "100 %, il ne tient aucun cahier et le plan attend pourtant quelque "
      + "chose de lui.",
      "Un gros pourcentage sur un petit total n'est pas un problème : lisez-le "
      + "à côté des trois chiffres, jamais seul. Le tableau est rangé par "
      + "numéro d'office, pas par ce pourcentage — l'ordre ne désigne "
      + "personne."),
  };

  // LA COLONNE ARRONDIT, LA BULLE NE PEUT PAS. Trois cahiers à 70,6 · 70,6 ·
  // 58,8 s'arrondissent en 71 · 71 · 59, qui font 201 sous un total de 200 : le
  // détail semble démentir la somme qu'il explique. On garde donc la décimale
  // ici — c'est la seule place où le compte doit tomber juste — et la colonne
  // reste ronde, parce qu'elle se lit de haut en bas et non case par case.
  const exact = (x) => (Math.round(x * 10) / 10).toFixed(1).replace(/[.,]0$/, "")
    .replace(".", ",");

  // La bulle d'une CASE : le total, puis d'où il vient, cahier par cahier.
  // C'est là que le chiffre cesse d'être une opinion de machine.
  function bulleCase(nom, titre, L, detail, total) {
    const lignes = detail.slice(0, 7).map(
      (d) => '<div class="gouv-bulle-part"><span>' + echappe(d.a)
        + '</span><b>' + exact(d.s) + "</b></div>").join("");
    const reste = detail.length > 7
      ? '<div class="gouv-bulle-reste">… et ' + (detail.length - 7)
        + " autre(s) cahier(s)</div>" : "";
    const pas = detail.reduce((n, d) => n + d.pas, 0);
    return '<div class="gouv-bulle-titre">' + echappe(nom) + " · " + titre + "</div>"
      + '<div class="gouv-bulle-chiffre">' + exact(total) + " <small>de criticité sur "
      + pas + " pas</small></div>"
      + (lignes ? '<div class="gouv-bulle-liste">' + lignes + reste + "</div>"
                : '<div class="gouv-bulle-corps">Rien, sur les cahiers que ce '
                  + "siège peut ouvrir.</div>")
      + '<div class="gouv-bulle-pied">' + L + "</div>";
  }

  function gouvernement(q) {
    if (!crit || !crit.charge) return null;
    const vues = (window.Books && Books.affairesVues) ? Books.affairesVues() : null;
    if (!vues || !vues.size) return null;
    const offices = crit.offices || {};
    const lignes = Object.keys(crit.charge).map((cle) => {
      const h = crit.charge[cle];
      const v = sommeVue(h.vu, vues);
      const s = sommeVue(h.sien_ailleurs, vues);
      const t = sommeVue(h.tire, vues);
      const id = figure(cle);
      return { q: cle, id: id, nom: (id ? qui(id).nom : String(cle).replace(/-/g, " ")),
               offices: h.offices || [], moyens: h.moyens || [],
               cahiers: (h.cahiers || []).filter((a) => vues.has(a)),
               dv: detailVu(h.vu, vues), ds: detailVu(h.sien_ailleurs, vues),
               dt: detailVu(h.tire, vues),
               v: v, s: s, t: t, total: v + s + t };
    }).filter((L) => L.offices.length && L.total > 0)
      .filter((L) => !q || (L.nom + " " + L.offices.map(
        (o) => o + " " + ((offices[o] && offices[o].nom) || "")).join(" ")
      ).toLowerCase().includes(q))
      .sort((a, b) => a.offices[0].localeCompare(b.offices[0]));
    if (!lignes.length) return null;

    const bloc = document.createElement("div");
    bloc.className = "gens-gouv";
    bloc.innerHTML = '<div class="gens-gouv-titre">Mon gouvernement</div>'
      + '<div class="gens-gouv-note">Ce que le plan attend de chacun, cahier par'
      + " cahier — calculé à l'ouverture, écrit nulle part.</div>";
    const enveloppe = document.createElement("div");
    enveloppe.className = "book-table-enveloppe";
    const tb = document.createElement("table");
    tb.className = "book-table gens-gouv-table";
    // Les intitulés des colonnes reprennent mot pour mot ceux du terminal :
    // deux noms pour la même mesure, et l'on ne sait plus laquelle on lit.
    tb.innerHTML = "<thead><tr><th>L'homme</th><th>Ses offices</th>"
      + '<th data-calcule>Vu</th><th data-calcule>Sien ailleurs</th>'
      + '<th data-calcule>On lui tire</th><th data-calcule>Aveugle</th>'
      + "</tr></thead>";
    const th = tb.querySelectorAll("thead th");
    glose(th[1], bulleColonne("Ses offices",
      "Les charges dont il est titulaire au registre des offices, par numéro. "
      + "C'est par ce champ que la colonne « sien ailleurs » le retrouve sur "
      + "des lignes qu'il ne voit pas.", ""));
    ["vu", "sien", "tire", "aveugle"].forEach((k, i) => glose(th[i + 2], COLONNES[k]));
    const corps = document.createElement("tbody");
    lignes.forEach((L) => corps.appendChild(rangGouv(L, offices)));
    tb.appendChild(corps);
    enveloppe.appendChild(tb);
    bloc.appendChild(enveloppe);
    brancherGloses(bloc);
    return bloc;
  }

  const rond = (x) => (x ? String(Math.round(x)) : "—");

  // L'INTITULÉ D'UN OFFICE EST PARFOIS UN PARAGRAPHE. Le registre des offices
  // porte, sur la même ligne, le nom de la charge ET le motif de son ouverture —
  // O18 fait quatre cents signes. Ici on ne veut que la charge : on coupe à la
  // glose, et l'on borne ce qui reste. Le registre garde le texte entier ; c'est
  // la lecture qu'on abrège, jamais le livre.
  function intitule(nom) {
    const n = String(nom || "").split(" — ")[0].trim();
    return n.length > 52 ? n.slice(0, 51) + "…" : n;
  }

  function rangGouv(L, offices) {
    const tr = document.createElement("tr");
    const p = L.id ? parId.get(L.id) : null;

    const tdQui = document.createElement("td");
    tdQui.className = "gens-gouv-qui";
    // Un homme du plan que le registre des gens ne connaît pas garde son
    // identifiant en clair, faute de visage : c'est une jointure manquante, et
    // la cacher derrière un tiret la rendrait introuvable.
    tdQui.innerHTML = '<span class="gens-gouv-face">'
      + ((L.id && qui(L.id).portrait_svg) || "") + "</span><span>"
      + L.nom + "</span>";
    if (p) {
      tdQui.classList.add("gens-gouv-cliquable");
      tdQui.onclick = () => Entites.penser(p.id, "personnage", p.nom);
    }
    tr.appendChild(tdQui);

    const tdOff = document.createElement("td");
    tdOff.className = "gens-gouv-offices";
    tdOff.textContent = L.offices.map(
      (o) => o + ((offices[o] && offices[o].nom)
        ? " · " + intitule(offices[o].nom) : "")
    ).join("\n");
    tr.appendChild(tdOff);

    // Chaque chiffre porte son détail : de quels cahiers il sort, et combien de
    // pas il pèse. Un total qu'on ne peut pas ouvrir ne se relit pas.
    [["Vu", L.v, L.dv, "Ses cahiers : " + (L.cahiers.join(" · ") || "aucun")
        + ". C'est ce qu'une dépêche lui met entre les mains."],
     ["Sien ailleurs", L.s, L.ds, "Par ses offices " + (L.offices.join(" ") || "—")
        + ", dans des cahiers tenus par un autre."],
     ["On lui tire", L.t, L.dt, "Par les moyens qu'il tient : "
        + (L.moyens.join(" · ") || "aucun") + "."]
    ].forEach(([nom, x, detail, pied]) => {
      const td = document.createElement("td");
      td.className = "book-calcule";
      td.textContent = rond(x);
      if (x) glose(td, bulleCase(L.nom, nom, pied, detail, x));
      tr.appendChild(td);
    });
    const td = document.createElement("td");
    td.className = "book-calcule";
    // On imprime le pourcentage sans le teinter : trois paliers de couleur
    // rangeraient les hommes par gravité, ce qui est le conseil qu'on s'interdit.
    // On TRONQUE, comme `--charge` au terminal. Arrondir donnait un point
    // d'écart sur la moitié des lignes, et deux affichages du même chiffre qui
    // ne concordent pas font douter des deux.
    const pc = Math.floor(100 * (L.s + L.t) / L.total);
    td.textContent = pc + " %";
    // Le calcul est refait sous les yeux, avec SES chiffres : c'est la seule
    // façon qu'un pourcentage cesse d'être un verdict.
    glose(td, '<div class="gouv-bulle-titre">' + echappe(L.nom)
      + " · Aveugle</div>"
      + '<div class="gouv-bulle-calcul">(' + exact(L.s) + " + " + exact(L.t)
      + ") ÷ (" + exact(L.v) + " + " + exact(L.s) + " + " + exact(L.t) + ") = <b>"
      + pc + " %</b></div>"
      + '<div class="gouv-bulle-corps">'
      + (pc >= 99
         ? "Il ne tient aucun cahier où le plan l'attende : rien de ce qui le "
           + "concerne ne lui parvient par une dépêche."
         : pc === 0
           ? "Tout ce qui le concerne est dans ses cahiers. Le routage suffit."
           : "Il voit " + exact(L.v) + " de sa charge sur " + exact(L.total)
             + " ; le reste ne lui parvient par aucun chemin.")
      + "</div>"
      + '<div class="gouv-bulle-pied">Un gros pourcentage sur un petit total '
      + "n'est pas un problème. Lisez-le à côté des trois chiffres.</div>");
    tr.appendChild(td);
    return tr;
  }

  // Deux rangements, et ils ne répondent pas à la même question.
  //   « armorial »   — par camp puis par maison : qui est de quel bord.
  //   « rencontres » — par salle traversée, la plus récente en tête, et dans
  //                    chacune les gens dans l'ordre où on les y a vus. C'est
  //                    l'ordre où l'on cherche quelqu'un dont on a oublié le
  //                    nom : « la femme de tout à l'heure, en bas ».
  // L'ordre vient de `Vus`, tiré du fil ; rien n'est écrit dans `etat/`.
  const CLE_RANG = "conseil.gens.rangement";
  let rangement = "vus";
  try { rangement = localStorage.getItem(CLE_RANG) || "vus"; } catch (e) {}

  function lister(corps) {
    const q = filtre.trim().toLowerCase();
    const garde = (p) => !q ||
      (p.nom + " " + p.titre + " " + p.maison).toLowerCase().includes(q);
    if (rangement === "vus" && window.Vus) listerVus(corps, garde);
    else listerCamps(corps, garde);
    // LE TABLEAU SE POSE APRÈS COUP, ET EN TÊTE. Les deux rangements vident
    // `corps` avant de le remplir : l'y mettre d'abord revenait à l'effacer
    // aussitôt, sans erreur ni trace — la section n'apparaissait simplement
    // jamais. Il passe par le même filtre que les visages, sinon chercher un
    // nom laisserait au-dessus une grille qui ne parle de personne.
    const gouv = gouvernement(q);
    if (gouv) corps.insertBefore(gouv, corps.firstChild);
  }

  function listerVus(corps, garde) {
    corps.innerHTML = "";
    const carnet = Vus.carnet().filter((v) => parId.has(v.id));
    // par salle, dans l'ordre de la dernière fois qu'on y était
    const salles = [];
    const parSalle = new Map();
    carnet.forEach((v) => {
      const clef = v.lieu || "Ailleurs";
      if (!parSalle.has(clef)) { parSalle.set(clef, []); salles.push(clef); }
      const p = parId.get(v.id);
      if (garde(p)) parSalle.get(clef).push(p);
    });
    let vus = 0;
    salles.forEach((clef) => {
      const liste = parSalle.get(clef);
      if (!liste.length) return;
      vus += liste.length;
      const bloc = document.createElement("div");
      bloc.className = "gens-maison gens-salle";
      bloc.innerHTML = '<div class="gens-maison-titre">' + clef + "</div>";
      const rang = document.createElement("div");
      rang.className = "gens-rang";
      liste.forEach((p) => rang.appendChild(medaillon(p)));
      bloc.appendChild(rang);
      corps.appendChild(bloc);
    });
    // ceux que le fil n'a jamais montrés : ils existent, on ne les a pas vus.
    const jamais = gens.filter((p) => Vus.quand(p.id) === null && garde(p));
    if (jamais.length) {
      const bloc = document.createElement("div");
      bloc.className = "gens-maison gens-jamais";
      bloc.innerHTML = '<div class="gens-maison-titre">Jamais rencontrés</div>';
      const rang = document.createElement("div");
      rang.className = "gens-rang";
      jamais.forEach((p) => rang.appendChild(medaillon(p)));
      bloc.appendChild(rang);
      corps.appendChild(bloc);
      vus += jamais.length;
    }
    if (!vus) corps.innerHTML = '<p class="gens-vide">Personne de ce nom.</p>';
  }

  function listerCamps(corps, garde) {
    corps.innerHTML = "";
    let vus = 0;
    CAMPS.forEach((c) => {
      const dedans = gens.filter((p) => p.camp === c.id && garde(p));
      if (!dedans.length) return;
      vus += dedans.length;
      const sec = document.createElement("div");
      sec.className = "gens-camp camp-" + c.id;
      sec.innerHTML = '<div class="gens-camp-titre">' + c.nom + "</div>";
      // par maison, à l'intérieur du camp : on lit une cour, pas une liste
      const parMaison = new Map();
      dedans.forEach((p) => {
        if (!parMaison.has(p.maison)) parMaison.set(p.maison, []);
        parMaison.get(p.maison).push(p);
      });
      parMaison.forEach((liste, maison) => {
        const bloc = document.createElement("div");
        bloc.className = "gens-maison";
        bloc.innerHTML = '<div class="gens-maison-titre">' + maison + "</div>";
        const rang = document.createElement("div");
        rang.className = "gens-rang";
        liste.forEach((p) => rang.appendChild(medaillon(p)));
        bloc.appendChild(rang);
        sec.appendChild(bloc);
      });
      corps.appendChild(sec);
    });
    if (!vus) corps.innerHTML = '<p class="gens-vide">Personne de ce nom.</p>';
  }

  // relire quand l'état a bougé (un mort, un nouveau venu, un titre changé)
  function relire() { charge = false; gens = gens || null; charger(); }

  // Le registre est chargé d'emblée, pas à l'ouverture de la vue : le fil s'en
  // sert dès la première réplique pour nommer et titrer qui parle.
  charger();

  window.addEventListener("DOMContentLoaded", () => {
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "gens", nom: "Les gens", hote: "gens", ordre: 4,
        dispo: () => true,
        // Le registre est chargé une fois pour toutes ; l'ordre des
        // rencontres, lui, a changé depuis. On redessine à chaque ouverture,
        // sinon la vue montre l'état du monde à l'instant du chargement de la
        // page — c'est-à-dire avant que le fil n'ait rejoué quoi que ce soit.
        // La charge ne se demande qu'ici, et jamais au chargement de la page :
        // `/criticite` coûte une seconde et demie de python au premier appel,
        // et cette vue n'est presque jamais ouverte. Le serveur la garde en
        // cache ensuite, donc la redemander à chaque ouverture est gratuit.
        reparu: () => {
          charger();
          chargerCharge();
          // L'étagère borne le tableau : sans elle il ne s'affiche pas. Elle
          // arrive d'ordinaire bien avant, mais on la réclame par sûreté.
          if (window.Books && Books.charger) Books.charger();
          if (gens) dessiner();
        },
      });
    }
    // L'endroit, ici, c'est le rangement et ce qu'on cherchait : revenir sur
    // « Les gens » avec la recherche vidée, c'est revenir ailleurs.
    if (window.Nav) {
      Nav.enregistrer("gens", {
        clefs: ["rang", "cherche"],
        etat: () => ({ rang: rangement, cherche: filtre }),
        poser: (p) => {
          const r = p.rang === "camp" ? "camp" : "vus";
          const f = p.cherche || "";
          if (r === rangement && f === filtre) return true;
          rangement = r; filtre = f;
          try { localStorage.setItem(CLE_RANG, rangement); } catch (e) {}
          if (!gens) return false;
          dessiner();
          return true;
        },
      });
    }
    setInterval(() => { if (gens) { charge = false; charger(); } }, 120000);
  });

  // « préviens-moi quand tu sauras » — appelé tout de suite si c'est déjà le cas
  function quand(cb) {
    if (parId.size) { try { cb(); } catch (e) {} } else aPrevenir.push(cb);
  }

  // Le carnet de rencontres bouge à chaque item du fil. On ne redessine pas
  // pour autant : la vue n'est presque jamais ouverte, et quand elle l'est un
  // battement de retard ne coûte rien. Un seul redessin par demi-seconde.
  let attente = null;
  function rafraichirVus() {
    if (rangement !== "vus" || attente) return;
    const h = hote();
    if (!h || !gens || h.offsetParent === null) return;
    attente = setTimeout(() => { attente = null; dessiner(); }, 500);
  }

  return { relire, charger, qui, medaillon: medaillonDe, marquer, quand,
           rafraichirVus };
})();
