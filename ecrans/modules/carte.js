// carte.js — la table peinte : Westeros, piloté par l'état (/carte).
// La géométrie (côtes, régions, fleuves, position exacte des lieux) vient de
// geo.js, extrait des données de carte du mod AGOT par scripts/carte_geo.py.
// Elle est figée dans le dépôt : le jeu ne dépend ni du mod ni de CK3.
// Ce que la table PORTE — osts, flottes, dragons, marches, attaques, serments —
// vient de /carte (etat/jetons.json) et se dessine par jetons.js.
// Couleur des lieux = allégeance AFFICHÉE (le notoire, jamais la vérité cachée).
// Cliquer un lieu ou une pièce = un moment de pensée (canal des entités du fil).
// Le plateau n'a qu'une colonne étroite : Westeros entier y flotterait dans le
// vide. La vignette se cadre donc sur le théâtre de la Danse — la baie de la
// Néra — et « s'approcher de la table » ouvre le royaume en entier. Un
// conseiller qui montre un bout de carte peut, le temps de sa démonstration,
// imposer son propre cadrage : voir `illustrer`.
"use strict";
window.Carte = (() => {
  const G = window.Geo;

  // Étiquettes des lieux : [dx, dy, ancre], en unités de la grande carte.
  // Ancre "g" = texte aligné à droite (fin), "d" = à gauche, "c" = centré.
  // Autour de la baie, les noms rayonnent vers l'extérieur de la grappe.
  const ETIQ = {
    "harrenhal": [-4, 0, "g"],
    "port-real": [-4, 3.5, "g"],
    "rosby": [-4, 1, "g"],
    "stokeworth": [-4, 0, "g"],
    "sombreval": [-4, -1.5, "g"],
    "repaire-aux-corneilles": [0, -4, "c"],
    "griffes": [0, -4, "c"],
    "cracfosse": [-4, -1.5, "g"],
    "sweetport-sound": [-4, 1, "g"],
    "peyredragon": [4, 0, "d"],
    "lamarck": [-3, 4, "g"],
    "sharp-point": [4, 1, "d"],
    "pointe-massey": [4, 2.5, "d"],
    "winterfell": [4, 1, "d"],
    "les-eyrie": [4, 1, "d"],
    "vivesaigues": [-4, -1, "g"],
    "castral-roc": [-4, 1, "g"],
    "villevieille": [-4, 1, "g"],
    "accalmie": [4, 1, "d"],
  };
  const ANCRE = { g: "end", d: "start", c: "middle" };

  // Les mers n'ont pas de contour dans l'état : leurs noms sont posés à la main,
  // dans le repère de geo.js.
  const MERS = [
    [366, 290, "Le Détroit"],
    [268, 268, "La Morsure"],
    [288, 424, "La Néra"],
    [42, 330, "Mer du Crépuscule"],
    [305, 598, "Mer de Dorne"],
  ];

  // Le générateur pose l'étiquette d'une région en son centre. Trois d'entre
  // elles tombent alors sur un nom de lieu : on les décale. La Couronne, elle,
  // n'est qu'un anneau de côtes autour de la baie — aucun creux ne peut porter
  // son nom, et ses places la nomment assez : null = pas d'étiquette.
  const DECALE_REGION = {
    "the_crownlands": null,
    "the_riverlands": [215, 340],
    "the_westerlands": [140, 420],
  };

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  // ---- état ----------------------------------------------------------------
  let etat = { lieux: [], joueur_lieu_id: null, date: null,
               jetons: [], traits: [], zones: [] };
  // Ce qu'un conseiller vient de poser du doigt : vrai le temps de la scène,
  // effacé au changement de scène. Ce qui doit durer est écrit dans l'état par
  // le MJ (etat/jetons.json) et revient par /carte.
  let ephemeres = { jetons: [], traits: [], zones: [] };
  let neuves = new Set();          // les pièces posées à l'instant : elles s'animent
  // Deux niveaux par surface : le cadrage de REPOS (celui qu'impose la scène ou
  // une démonstration) et la VUE courante, que la loupe déplace. Un double-clic
  // repose la table ; un changement de scène efface les deux.
  let cadreVignette = "baie", vueVignette = null;
  let cadreTable = null, vueTable = null;

  const marques = () => ({
    jetons: etat.jetons.concat(ephemeres.jetons),
    traits: etat.traits.concat(ephemeres.traits),
    zones: etat.zones.concat(ephemeres.zones),
  });

  // ---- cadrage -------------------------------------------------------------
  // Un cadrage est nommé ("baie", "westeros"), donné en clair ([x,y,l,h]), ou
  // déduit de ce qu'on montre ("auto") : la boîte des pièces, avec de la marge.
  function cadre(spec, m) {
    let vb;
    if (Array.isArray(spec) && spec.length === 4) vb = spec.join(" ");
    else if (spec === "auto") vb = auto(m || marques());
    else vb = (G.cadres && G.cadres[spec]) || G.cadres.baie || G.viewBox;
    const n = String(vb).split(/\s+/).map(Number);
    return { vb: n.join(" "), x: n[0], y: n[1], l: n[2], h: n[3], ech: n[2] / G.largeur };
  }

  const RATIO = 1.2;               // celui de la baie : la colonne du décor s'y fait
  function auto(m) {
    const b = window.Jetons && Jetons.boite(m);
    if (!b) return G.cadres.baie;
    let { x, y, l, h } = b;
    const marge = Math.max(18, Math.max(l, h) * .35);
    x -= marge; y -= marge; l += marge * 2; h += marge * 2;
    if (l < 55) { x -= (55 - l) / 2; l = 55; }
    if (h < 46) { y -= (46 - h) / 2; h = 46; }
    if (l / h < RATIO) { const n = h * RATIO; x -= (n - l) / 2; l = n; }
    else { const n = l / RATIO; y -= (n - h) / 2; h = n; }
    return [x.toFixed(1), y.toFixed(1), l.toFixed(1), h.toFixed(1)].join(" ");
  }

  // ---- rendu ---------------------------------------------------------------
  // La bannière de qui tient la place, plantée du côté OPPOSÉ à son nom : le nom
  // et les armes se partagent la place, ils ne se la disputent pas. Les pièces
  // de guerre, elles, s'empilent au-dessus du point — les trois ne se touchent
  // jamais. Une bannière qui déborderait du cadrage est simplement absente ; la
  // place, son point et son nom restent.
  const BAN = 0.78;                // l'échelle des armes, sur celle de la carte
  function banniereDe(l, x, y, ancre, c, serre) {
    if (serre || !window.Blasons || !l.controle_id) return "";
    const armes = Blasons.banniere(l.controle_id);
    if (!armes) return "";
    const t = BAN * c.ech;
    const sens = ancre === "d" ? -1 : 1;
    const bx = x + sens * 7.6 * c.ech, by = y - 1.2 * c.ech;
    const demi = (Blasons.LARGEUR / 2 + 1.4) * t;
    if (bx - demi < c.x || bx + demi > c.x + c.l ||
        by + Blasons.HAUT * t < c.y || by + Blasons.BAS * t > c.y + c.h) return "";
    return '<g class="armes" transform="translate(' + bx.toFixed(1) + "," + by.toFixed(1) +
      ") scale(" + t.toFixed(4) + ')">' + armes + "</g>";
  }

  function svgCarte(c, opts) {
    const o = opts || {};
    const m = o.marques || marques();
    // Une seule échelle pilote épaisseurs et corps de texte, pour que la
    // vignette serrée et la grande table se ressemblent.
    let s = '<svg viewBox="' + c.vb + '" xmlns="http://www.w3.org/2000/svg"' +
      ' class="' + (o.classe || (o.grand ? "carte-grande" : "carte-petite")) + '"' +
      ' style="--k:' + c.ech.toFixed(4) +
      ';font-size:' + (8.5 * c.ech).toFixed(2) + 'px">';

    // La mer d'abord : sans elle, la côte ne sépare rien de rien. Puis le
    // haut-fond — un large trait pâle collé au rivage, comme sur les cartes
    // gravées : c'est lui qui fait « lire » le trait de côte avant la couleur.
    s += '<rect class="mer" x="' + c.x + '" y="' + c.y + '" width="' + c.l +
      '" height="' + c.h + '"/>' +
      '<path class="hautfond" d="' + G.terre + '" stroke-width="' + (5 * c.ech).toFixed(2) + '"/>';
    Object.keys(G.fonds).forEach((nom) => {
      if (G.fonds[nom]) s += '<path class="lointain" d="' + G.fonds[nom] + '"/>';
    });
    s += '<path class="terre" d="' + G.terre + '"/>';
    G.regions.forEach((r) => {
      s += '<path class="region-terre" data-region="' + esc(r.id) + '" d="' +
        r.d + '"><title>' + esc(r.nom) + "</title></path>";
    });
    if (window.Jetons) s += Jetons.zones(m.zones);
    if (G.eaux) s += '<path class="eaux" d="' + G.eaux + '"/>';
    s += '<path class="cote" d="' + G.terre + '"/>';

    if (o.grand) {
      G.regions.forEach((r) => {
        const p = r.id in DECALE_REGION ? DECALE_REGION[r.id] : r.etiquette;
        if (p) {
          s += '<text class="region" x="' + p[0] + '" y="' + p[1] + '">' +
            esc(r.court) + "</text>";
        }
      });
      MERS.forEach((mm) => {
        s += '<text class="mer-nom" x="' + mm[0] + '" y="' + mm[1] + '">' +
          esc(mm[2]) + "</text>";
      });
    }

    // Les fils passent SOUS les places et les pièces : une marche doit filer
    // derrière les murs qu'elle contourne, pas par-dessus.
    if (window.Jetons) s += Jetons.traits(m.traits, c.ech, neuves);

    // Les places de la baie se tiennent à cinq lieues les unes des autres : au
    // cadrage du royaume, leurs bannières feraient une bouillie d'étoffe. Une
    // place trop serrée garde son point et son nom, et retrouve ses armes quand
    // on approche — comme les noms, la parure vient avec la distance.
    const serres = {};
    etat.lieux.forEach((a) => {
      const pa = G.lieux[a.id];
      if (!pa) return;
      let d = Infinity;
      etat.lieux.forEach((b) => {
        const pb = G.lieux[b.id];
        if (!pb || b.id === a.id) return;
        d = Math.min(d, Math.hypot(pb[0] - pa[0], pb[1] - pa[1]));
      });
      serres[a.id] = d < 17 * c.ech;
    });

    etat.lieux.forEach((l) => {
      const p = G.lieux[l.id];
      if (!p) return;
      const [x, y] = p;
      const e = ETIQ[l.id] || [4, 1, "d"];
      const dx = e[0] * c.ech, dy = e[1] * c.ech;
      const nom = esc(l.nom.split(" (")[0]);

      // Hors du cadrage, on ne laisse pas un nom se faire trancher par le
      // bord : le lieu est simplement absent de la vignette (il reste sur la
      // grande table). Largeur estimée du texte, en unités du cadre.
      const large = nom.length * 4.2 * c.ech;
      const gauche = e[2] === "g" ? x + dx - large
        : e[2] === "c" ? x + dx - large / 2 : x + dx;
      const marge = 2 * c.ech;
      if (gauche < c.x + marge || gauche + large > c.x + c.l - marge ||
          y + dy < c.y + marge * 3 || y + dy > c.y + c.h - marge) return;

      const ici = l.id === etat.joueur_lieu_id;
      s += '<g class="lieu-carte allg-' + (l.allegeance || "neutre") +
        (ici ? " ici" : "") + '" data-id="' + esc(l.id) +
        '" data-nom="' + esc(l.nom) + '">' +
        "<title>" + nom + "</title>" +
        (ici ? '<circle class="anneau" cx="' + x + '" cy="' + y + '" r="' +
          (7 * c.ech).toFixed(2) + '"/>' : "") +
        '<circle class="point" cx="' + x + '" cy="' + y + '" r="' +
        ((l.type === "ville" ? 3.6 : 2.9) * c.ech).toFixed(2) + '"/>' +
        banniereDe(l, x, y, e[2], c, serres[l.id]) +
        '<text class="nom" x="' + (x + dx).toFixed(1) + '" y="' +
        (y + dy).toFixed(1) + '" text-anchor="' + ANCRE[e[2]] + '">' +
        nom + "</text></g>";
    });

    if (window.Jetons) {
      s += Jetons.pieces(m.jetons, c.ech, { neuves, cadre: c });
    }
    return s + "</svg>";
  }

  // Le <svg> est refait à chaque redessin — et la loupe en produit soixante par
  // seconde. Les écoutants vivent donc sur l'hôte, une seule fois, par
  // délégation : rien à rebrancher, rien à fuir.
  //   opts.apres — à faire après une pensée (refermer la table)
  //   opts.fond  — un clic hors de toute pièce (la vignette ouvre la table)
  function brancher(hote, opts) {
    const o = opts || {};
    if (!hote.dataset.branche) {
      hote.dataset.branche = "1";
      hote.addEventListener("click", (e) => {
        // un glissé n'est pas un clic, et le second clic d'un double non plus
        if (window.Loupe && Loupe.aGlisse(hote)) return;
        if (e.detail > 1) return;
        const g = e.target.closest(".lieu-carte, .jeton, .trait");
        if (g) {
          const type = g.classList.contains("lieu-carte") ? "lieu"
            : g.classList.contains("jeton") ? "force" : "manoeuvre";
          if (window.Entites && g.dataset.nom) {
            Entites.penser(g.dataset.id || g.dataset.nom, type, g.dataset.nom);
          }
          if (o.apres) o.apres();
          return;
        }
        if (o.fond && (e.target.closest("svg") || e.target.id === "carte-approcher")) o.fond();
      });
    }
    if (window.Loupe) Loupe.brancher(hote, o.loupe);
  }

  // On ne se penche pas dans le vide : la loupe reste sur le royaume, avec ce
  // qu'il faut de marge pour que les noms de la côte est aient leur mer.
  function bornes() {
    const w = cadre("westeros");
    const m = Math.max(w.l, w.h) * .06;
    return [w.x - m, w.y - m, w.l + m * 2, w.h + m * 2];
  }

  function dateEnClair(d) {
    if (!d) return "";
    return d.annee + " AC — " + d.lune + (d.lune === 1 ? "re" : "e") + " lune, " +
      d.jour + (d.jour === 1 ? "er" : "e") + " jour";
  }

  const LEGENDE_BASE =
    '<span class="leg leg-noir">Noirs</span>' +
    '<span class="leg leg-vert">Verts</span>' +
    '<span class="leg leg-neutre">Sans parti déclaré</span>' +
    '<span class="leg leg-ici">Vous êtes ici</span>';
  const MANUEL = '<span class="leg-manuel">Molette pour approcher, ' +
    'glisser pour déplacer, double-clic pour reposer la table</span>';
  function legende(manuel) {
    const m = marques();
    const p = window.Jetons ? Jetons.legende(m) : "";
    return LEGENDE_BASE + (p ? '<span class="leg-sep"></span>' + p : "") +
      (manuel ? MANUEL : "");
  }

  const vbDe = (c) => [c.x, c.y, c.l, c.h];

  // ---- la grande table (overlay) -----------------------------------------
  function batirOverlay() {
    if (document.getElementById("table-peinte")) return;
    const ov = document.createElement("div");
    ov.id = "table-peinte";
    ov.hidden = true;
    ov.innerHTML =
      '<div id="table-cadre">' +
      '<div id="table-tete"><span id="table-titre">La table peinte</span>' +
      '<span id="table-date"></span>' +
      '<button id="table-large" title="Voir tout le royaume">Le royaume entier</button>' +
      '<button id="table-fermer" title="Refermer">Quitter la table</button></div>' +
      '<div id="table-carte"></div>' +
      '<div id="table-legende"></div></div>';
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => { if (e.target === ov) fermerTable(); });
    ov.querySelector("#table-fermer").addEventListener("click", fermerTable);
    ov.querySelector("#table-large").addEventListener("click", (e) => {
      e.stopPropagation();
      ouvrirTable("westeros");
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !ov.hidden) fermerTable();
    });
  }
  function ouvrirTable(spec) {
    batirOverlay();
    if (spec) { cadreTable = spec; vueTable = null; }
    const ov = document.getElementById("table-peinte");
    ov.querySelector("#table-date").textContent = dateEnClair(etat.date);
    ov.querySelector("#table-legende").innerHTML = legende(true);
    const conteneur = ov.querySelector("#table-carte");
    if (window.Loupe && spec) Loupe.oublier(conteneur);
    poserTable(conteneur);
    brancher(conteneur, {
      apres: fermerTable,
      loupe: {
        vue: () => vueTable || vbDe(cadre(cadreTable || "westeros")),
        bornes, min: 45,
        poser: (vb) => { vueTable = vb; poserTable(conteneur); },
        reposer: () => { vueTable = null; poserTable(conteneur); },
      },
    });
    ov.hidden = false;
  }
  function poserTable(conteneur) {
    conteneur.innerHTML = svgCarte(cadre(vueTable || cadreTable || "westeros"), { grand: true });
  }
  function fermerTable() {
    const ov = document.getElementById("table-peinte");
    if (ov) ov.hidden = true;
    if (ov && window.Loupe) Loupe.oublier(ov.querySelector("#table-carte"));
    cadreTable = null;
    vueTable = null;
  }

  // ---- la table au centre du plateau -------------------------------------
  // Le fond (légende, bouton) ne se refait qu'au changement d'état ; la loupe,
  // elle, ne remplace que le dessin — soixante fois par seconde s'il le faut.
  function poserVignette(conteneur) {
    const svg = svgCarte(cadre(vueVignette || cadreVignette));
    const vieux = conteneur.querySelector("svg");
    if (vieux) vieux.outerHTML = svg;
    else conteneur.insertAdjacentHTML("afterbegin", svg);
  }

  function dessiner() {
    const conteneur = document.getElementById("carte");
    if (!conteneur) return;
    conteneur.innerHTML = svgCarte(cadre(vueVignette || cadreVignette)) +
      '<div id="carte-legende">' + legende() + "</div>" +
      '<button id="carte-approcher">S\'approcher de la table…</button>';
    brancher(conteneur, {
      fond: () => ouvrirTable(),
      loupe: {
        vue: () => vueVignette || vbDe(cadre(cadreVignette)),
        bornes, min: 45,
        poser: (vb) => { vueVignette = vb; poserVignette(conteneur); },
        reposer: () => { vueVignette = null; poserVignette(conteneur); },
      },
    });
  }

  // ---- viser un lieu : le survol d'un nom dans le fil ----------------------
  // Le joueur promène l'œil sur « Sombreval » dans une réplique : la table le
  // lui montre, le temps du survol, puis se repose exactement où elle était.
  // Rien n'est décidé ni consommé — c'est de l'attention, pas une action.
  const VISEE_PART = .5;           // au plus la moitié du royaume dans le cadre
  let vueAvantVisee = null, viseEnCours = null;

  function viser(id) {
    const hote = document.getElementById("carte");
    // le royaume n'est pas l'échelle affichée : on ne bascule pas le décor sous
    // les yeux du joueur pour un simple survol
    if (!hote || hote.classList.contains("vue-off")) return false;
    const p = window.Jetons && Jetons.position(id);
    if (!p) return false;
    if (viseEnCours === null) vueAvantVisee = vueVignette;
    viseEnCours = id;
    const c = cadre(vueVignette || cadreVignette);
    const b = bornes();
    // On respecte l'approche du joueur si elle est déjà serrée ; sinon on
    // resserre, sans quoi centrer sur une place au cadrage large ne se voit pas.
    const l = Math.min(c.l, b[2] * VISEE_PART), h = l * (c.h / c.l);
    const borner = (v, min, etendue, taille) =>
      Math.max(min, Math.min(v, min + etendue - taille));
    vueVignette = [borner(p[0] - l / 2, b[0], b[2], l),
                   borner(p[1] - h / 2, b[1], b[3], h), l, h];
    poserVignette(hote);
    return true;
  }

  function deviser() {
    if (viseEnCours === null) return;
    vueVignette = vueAvantVisee;
    viseEnCours = null;
    const hote = document.getElementById("carte");
    if (hote) poserVignette(hote);
  }

  function redessiner() {
    dessiner();
    const ov = document.getElementById("table-peinte");
    if (ov && !ov.hidden) ouvrirTable();
  }

  // ---- une démonstration : ce qu'un conseiller pose sur la table ----------
  // `montre` : {jetons, traits, zones, cadre, garder}. Les pièces arrivent
  // marquées « neuves » (elles s'animent), la table prend le cadrage demandé, et
  // le décor bascule sur le royaume — sinon le joueur regarde le plan du château
  // pendant qu'on lui montre la baie.
  function illustrer(montre) {
    if (!montre) return null;
    const seul = { jetons: montre.jetons || [], traits: montre.traits || [],
                   zones: montre.zones || [] };
    const nouvelles = new Set();
    ["jetons", "traits", "zones"].forEach((k) => {
      (montre[k] || []).forEach((m) => {
        if (m.id) nouvelles.add(m.id);
        // reposer une pièce déjà connue la remplace : une colonne avance, elle
        // ne se dédouble pas.
        const dedans = ephemeres[k].findIndex((x) => x.id && x.id === m.id);
        if (dedans !== -1) ephemeres[k][dedans] = m; else ephemeres[k].push(m);
      });
    });
    neuves = nouvelles;
    // « auto » se calcule sur ce qu'on MONTRE, pas sur tout ce que la table
    // porte : un doigt sur le Gosier ne doit pas rouvrir le royaume entier.
    let spec = montre.cadre || "auto";
    if (spec === "auto") spec = cadre("auto", seul).vb.split(/\s+/).map(Number);
    if (spec !== "garder") {
      // une démonstration reprend la table des mains du joueur : ce qu'il avait
      // approché ne doit pas revenir à la frame suivante.
      cadreVignette = spec;
      vueVignette = null;
      viseEnCours = null;          // une démonstration prime sur un survol
      const h = document.getElementById("carte");
      if (h && window.Loupe) Loupe.oublier(h);
    }
    if (window.Plan && Plan.montrer) Plan.montrer("royaume");
    redessiner();
    // La braise du « posé à l'instant » ne dure pas : passé un temps, la pièce
    // est simplement là, comme les autres.
    setTimeout(() => { neuves = new Set(); redessiner(); }, 9000);
    return spec;
  }

  // Une vignette autonome, pour le fil : la carte réduite au geste qu'on montre.
  function miniature(montre, opts) {
    const o = opts || {};
    const m = {
      jetons: (etat.jetons || []).concat(montre.jetons || []),
      traits: (etat.traits || []).concat(montre.traits || []),
      zones: (etat.zones || []).concat(montre.zones || []),
    };
    const seul = { jetons: montre.jetons || [], traits: montre.traits || [],
                   zones: montre.zones || [] };
    const c = cadre(montre.cadre && montre.cadre !== "garder" ? montre.cadre : "auto", seul);
    return svgCarte(c, { marques: m, classe: "carte-mini", grand: !!o.noms });
  }

  // Changement de scène : la table se nettoie de ce qui n'était qu'un geste.
  function effacer() {
    ephemeres = { jetons: [], traits: [], zones: [] };
    neuves = new Set();
    cadreVignette = "baie";
    vueVignette = null;
    const h = document.getElementById("carte");
    if (h && window.Loupe) Loupe.oublier(h);
    redessiner();
  }

  function rafraichir() {
    return fetch("/carte").then((r) => r.json())
      .then((d) => {
        etat = {
          lieux: d.lieux || [],
          joueur_lieu_id: d.joueur_lieu_id || null,
          date: d.date || null,
          jetons: d.jetons || [],
          traits: d.traits || [],
          zones: d.zones || [],
        };
        redessiner();
      })
      .catch(() => {});
  }

  // Changement de scène : les gestes de la scène passée quittent la table.
  // (Bus enchaîne les écoutants d'un même type : galerie.js vide la salle.)
  if (window.Bus) Bus.enregistrer("effacer", () => effacer());

  window.addEventListener("DOMContentLoaded", () => {
    if (!G) return;                       // geo.js absent : pas de carte
    rafraichir();
    setInterval(rafraichir, 60000);
  });

  return { illustrer, miniature, effacer, ouvrir: ouvrirTable, fermer: fermerTable,
           rafraichir, redessiner, cadre, svg: svgCarte, marques, viser, deviser };
})();
