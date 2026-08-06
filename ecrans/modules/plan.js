// plan.js — la carte locale : le château vu d'en haut, salle par salle.
// La géométrie vient de plans.js (dessinée à la main, figée dans le dépôt).
// Le décor bascule entre deux échelles qui répondent à deux questions
// différentes : le royaume (« où porte la guerre ») et le château (« où suis-je
// et qui est à trois portes de moi »). La seconde est celle de la scène.
//
// La salle courante n'est écrite nulle part dans l'état : elle se lit dans
// l'en-tête de lieu du bandeau (« Petite salle du levant, Peyredragon »), que
// le bus repose à chaque item porteur d'un `lieu`. Un plan reconnaît les siens
// par ses `motifs`. Rien à tenir à jour à la main, rien à réécrire dans le flux.
//
// Cliquer une salle = un moment de pensée, même canal que les entités du fil :
// on y songe, on n'y va pas. Se déplacer se dit, ça ne se clique pas.
"use strict";
window.Plan = (() => {
  const P = window.Plans || {};
  let plan = null;          // le plan du lieu où se trouve le joueur
  let salleId = null;       // la salle courante, devinée du bandeau
  let vue = null;           // "chateau" | "royaume"

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  // sans accents ni casse : « Néra » et « nera » désignent la même chose
  const DIACRITIQUES = new RegExp("[\\u0300-\\u036f]", "g");
  const nu = (s) => String(s || "").normalize("NFD").replace(DIACRITIQUES, "").toLowerCase();

  // ---- la salle courante ---------------------------------------------------
  // Le flux peut la nommer (`salle_id` sur un item, reposé par le bus sur le
  // bandeau) : elle fait alors foi. Sinon on la devine de l'en-tête de lieu.
  // Règle : le PREMIER motif rencontré gagne, pas le plus long — un en-tête
  // nomme la salle puis la situe (« L'archive, trois étages sous la salle du
  // levant » est l'archive, pas la salle du levant). À égalité, le plus long.
  function deviner() {
    const bandeau = document.getElementById("lieu");
    if (!plan || !bandeau) return null;
    const dit = bandeau.dataset.salle;
    if (dit && plan.salles.some((s) => s.id === dit)) return dit;
    const t = nu(bandeau.textContent);
    if (!t || t === "—") return null;
    let trouve = null, ou = Infinity, taille = 0;
    plan.salles.forEach((s) => {
      (s.motifs || []).concat([s.nom]).forEach((m) => {
        const n = nu(m);
        const i = t.indexOf(n);
        if (i === -1) return;
        if (i < ou || (i === ou && n.length > taille)) { ou = i; taille = n.length; trouve = s.id; }
      });
    });
    return trouve;
  }

  // ---- les ornements -------------------------------------------------------
  // Une salle n'est pas un rond : c'est un puits, sept autels, une roukerie qui
  // sent l'oiseau. Sur la vignette étroite, les noms sautent (voir nomSalle) et
  // il ne reste que la forme — c'est donc là que le pictogramme fait tout le
  // travail : on reconnaît les fosses à leurs flammes sans savoir lire la carte.
  // Chaque glyphe est écrit en unités du plan, autour de son point d'ancrage,
  // pour une demi-taille `t` : il grandit avec le dessin comme le reste.
  const O = {};
  const nb = (v) => (Math.round(v * 100) / 100);
  const p = (d, plein) => '<path' + (plein ? ' class="plein"' : "") + ' d="' + d + '"/>';
  const cer = (x, y, r, plein) => '<circle' + (plein ? ' class="plein"' : "") +
    ' cx="' + nb(x) + '" cy="' + nb(y) + '" r="' + nb(r) + '"/>';

  // le puits de la cour : la margelle et son toit à deux pentes
  O.puits = (x, y, t) => cer(x, y, t * .5) +
    p("M" + nb(x - t) + "," + nb(y - t * .55) + " L" + nb(x) + "," + nb(y - t * 1.35) +
      " L" + nb(x + t) + "," + nb(y - t * .55));
  // la roukerie : un oiseau, deux coups d'aile
  O.corbeau = (x, y, t) => p("M" + nb(x - t) + "," + nb(y + t * .35) + " Q" + nb(x - t * .35) +
    "," + nb(y - t * .7) + " " + nb(x) + "," + nb(y + t * .1) + " Q" + nb(x + t * .35) + "," +
    nb(y - t * .7) + " " + nb(x + t) + "," + nb(y + t * .35)) + cer(x, y + t * .15, t * .16, true);
  // le septuaire : l'étoile à sept branches
  O.etoile = (x, y, t) => {
    let d = "";
    for (let i = 0; i < 7; i++) {
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / 7;
      d += (i ? " L" : "M") + nb(x + Math.cos(a) * t) + "," + nb(y + Math.sin(a) * t);
    }
    return p(d + " Z") + cer(x, y, t * .28);
  };
  // le jardin : trois arbres noirs
  O.arbres = (x, y, t) => [-1, 0, 1].map((k) => {
    const cx = x + k * t * 1.5;
    return cer(cx, y - t * .35, t * .5) +
      p("M" + nb(cx) + "," + nb(y + t * .15) + " L" + nb(cx) + "," + nb(y + t * .7));
  }).join("");
  // les fosses : le feu qui ne s'éteint pas
  O.flamme = (x, y, t) => p("M" + nb(x) + "," + nb(y - t) + " Q" + nb(x + t * .72) + "," +
    nb(y - t * .1) + " " + nb(x + t * .34) + "," + nb(y + t * .72) + " Q" + nb(x) + "," +
    nb(y + t) + " " + nb(x - t * .34) + "," + nb(y + t * .72) + " Q" + nb(x - t * .72) + "," +
    nb(y - t * .1) + " " + nb(x) + "," + nb(y - t) + " Z", true);
  // la Table Peinte : le plateau rond et les sièges autour
  O.ronde = (x, y, t) => {
    let s = cer(x, y, t * .62);
    for (let i = 0; i < 8; i++) {
      const a = (i * 2 * Math.PI) / 8;
      s += cer(x + Math.cos(a) * t, y + Math.sin(a) * t, t * .17, true);
    }
    return s;
  };
  // la grande salle : deux longues tables et l'estrade
  O.tables = (x, y, t) => p("M" + nb(x - t * 1.6) + "," + nb(y - t * .5) + " h" + nb(t * 3.2)) +
    p("M" + nb(x - t * 1.6) + "," + nb(y + t * .25) + " h" + nb(t * 3.2)) +
    p("M" + nb(x - t * .7) + "," + nb(y + t) + " h" + nb(t * 1.4));
  // la salle du levant : une table pour six
  O.table6 = (x, y, t) => p("M" + nb(x - t) + "," + nb(y - t * .3) + " h" + nb(t * 2)) +
    [-.6, 0, .6].map((k) => cer(x + k * t * 1.4, y - t * .95, t * .2, true) +
      cer(x + k * t * 1.4, y + t * .35, t * .2, true)).join("");
  // la garnison : deux lances croisées
  O.lances = (x, y, t) => p("M" + nb(x - t) + "," + nb(y + t) + " L" + nb(x + t) + "," +
    nb(y - t)) + p("M" + nb(x + t) + "," + nb(y + t) + " L" + nb(x - t) + "," + nb(y - t)) +
    cer(x, y, t * .22, true);
  // la tour du Dragon de Mer : le large, trois houles
  O.ondes = (x, y, t) => [-1, 0, 1].map((k) => p("M" + nb(x - t) + "," + nb(y + k * t * .62) +
    " q" + nb(t * .5) + ",-" + nb(t * .42) + " " + nb(t) + ",0 q" + nb(t * .5) + "," +
    nb(t * .42) + " " + nb(t) + ",0")).join("");
  // la porte : la herse, quatre barreaux et deux traverses
  O.herse = (x, y, t) => {
    let s = "";
    for (let k = -1.5; k <= 1.5; k++) {
      s += p("M" + nb(x + k * t * .62) + "," + nb(y - t * .6) + " v" + nb(t * 1.2));
    }
    return s + p("M" + nb(x - t) + "," + nb(y - t * .2) + " h" + nb(t * 2)) +
      p("M" + nb(x - t) + "," + nb(y + t * .45) + " h" + nb(t * 2));
  };
  // le quai : une coque et sa voile
  O.nef = (x, y, t) => p("M" + nb(x - t) + "," + nb(y + t * .2) + " q" + nb(t) + "," +
    nb(t * .75) + " " + nb(t * 2) + ",0") +
    p("M" + nb(x) + "," + nb(y + t * .2) + " V" + nb(y - t)) +
    p("M" + nb(x) + "," + nb(y - t) + " L" + nb(x + t * .72) + "," + nb(y) + " H" + nb(x));
  // le Tambour : l'escalier tournant qui monte à la Table Peinte
  O.colimacon = (x, y, t) => {
    let d = "M" + nb(x) + "," + nb(y);
    for (let i = 1; i <= 26; i++) {
      const a = (i / 26) * Math.PI * 2.6, r = (i / 26) * t;
      d += " L" + nb(x + Math.cos(a) * r) + "," + nb(y + Math.sin(a) * r);
    }
    return p(d);
  };
  // les cachots : les barreaux
  O.barreaux = (x, y, t) => {
    let s = p("M" + nb(x - t) + "," + nb(y) + " h" + nb(t * 2));
    for (let k = -1; k <= 1; k++) s += p("M" + nb(x + k * t * .7) + "," + nb(y - t * .6) +
      " v" + nb(t * 1.2));
    return s;
  };
  // l'archive : un rouleau
  O.rouleau = (x, y, t) => cer(x - t * .8, y, t * .38) + cer(x + t * .8, y, t * .38) +
    p("M" + nb(x - t * .8) + "," + nb(y - t * .38) + " h" + nb(t * 1.6));

  function orne(s) {
    if (!s.orne) return "";
    const [nom, x, y, t] = s.orne;
    const f = O[nom];
    return f ? '<g class="plan-orne">' + f(x, y, t || 8) + "</g>" : "";
  }
  // Les détails écrits à la main dans le plan (les marches taillées de
  // l'escalier, par exemple) : de la géométrie, pas un glyphe de bibliothèque.
  function details(s) {
    if (!(s.traits || []).length) return "";
    return '<g class="plan-detail">' + s.traits.map((d) => '<path d="' + d + '"/>').join("") + "</g>";
  }

  // ---- la muraille -----------------------------------------------------------
  // Le crénelage se calcule, il ne se dessine pas : on sème des merlons le long
  // de chaque pan, tournés vers le dehors (la normale que l'on pousse à l'écart
  // du centre du château). Un mur de château n'est pas un trait — c'est ce qui
  // fait qu'on le lit comme une enceinte au premier coup d'œil.
  function crenelage(pts) {
    if (!pts || pts.length < 3) return "";
    const cx = pts.reduce((a, q) => a + q[0], 0) / pts.length;
    const cy = pts.reduce((a, q) => a + q[1], 0) / pts.length;
    let s = "";
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      const dx = b[0] - a[0], dy = b[1] - a[1];
      const L = Math.hypot(dx, dy);
      if (!L) continue;
      const ux = dx / L, uy = dy / L;
      let nx = -uy, ny = ux;
      const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
      if ((mx - cx) * nx + (my - cy) * ny < 0) { nx = -nx; ny = -ny; }
      const n = Math.max(2, Math.round(L / 11));
      for (let k = 0; k < n; k++) {
        const d = ((k + 0.5) * L) / n;
        const px = a[0] + ux * d, py = a[1] + uy * d;
        s += '<path class="plan-merlon" d="M' + nb(px) + "," + nb(py) + " L" +
          nb(px + nx * 3.2) + "," + nb(py + ny * 3.2) + '"/>';
      }
    }
    return s;
  }
  // Une tour de guet est ronde ET crénelée : huit dents autour du disque.
  function guet(g) {
    let s = '<circle class="plan-guet" cx="' + g[0] + '" cy="' + g[1] + '" r="6.5"/>';
    for (let i = 0; i < 8; i++) {
      const a = (i * 2 * Math.PI) / 8;
      s += '<path class="plan-dent" d="M' + nb(g[0] + Math.cos(a) * 5.2) + "," +
        nb(g[1] + Math.sin(a) * 5.2) + " L" + nb(g[0] + Math.cos(a) * 8.4) + "," +
        nb(g[1] + Math.sin(a) * 8.4) + '"/>';
    }
    return s;
  }

  // ---- rendu ---------------------------------------------------------------
  function forme(s) {
    const f = s.forme;
    if (f.c) return '<circle cx="' + f.c[0] + '" cy="' + f.c[1] + '" r="' + f.c[2] + '"/>';
    if (f.r) return '<rect x="' + f.r[0] + '" y="' + f.r[1] + '" width="' + f.r[2] +
      '" height="' + f.r[3] + '" rx="' + (f.r[4] || 4) + '"/>';
    return '<path d="' + f.d + '"/>';
  }

  // Un corps de texte écrit en unités du plan grandit AVEC la carte : 14 unités
  // sont justes dans une vignette de 250 px et deviennent énormes dans une de
  // 700. On vise donc une taille APPARENTE constante — mesurée sur le rendu, pas
  // devinée — et la densité des noms suit la même mesure : une petite carte ne
  // porte que les salles maîtresses et celle où l'on se tient (les autres gardent
  // forme, infobulle et clic), une grande les porte toutes sans qu'ils se
  // marchent dessus. Seuil relevé à l'essai : au-delà de 360 px de large, les
  // trente et une étiquettes tiennent sans une seule collision.
  const CIBLE = { petit: 9.8, grand: 11.5 };   // px réels visés
  const SEUIL_TOUS = 360;                      // px réels

  function nomSalle(s, v) {
    if (!v.tous && !s.cle && s.id !== salleId) return "";
    const [x, y] = s.etiq;
    const lignes = s.lignes || [s.nom];
    const h = v.police * 1.13;   // interligne : jamais moins que le corps
    let t = "";
    lignes.forEach((l, i) => {
      t += '<text class="plan-nom" x="' + x + '" y="' + (y + i * h).toFixed(1) + '">' +
        esc(l) + "</text>";
    });
    // Quand la carte a la place d'écrire : qui est là avec vous, sous le nom.
    if (v.tous && s.id === salleId) {
      // « Ser Robert Quince » se dit Robert, pas Ser : le titre saute d'abord.
      const gens = Object.keys(window.Presents || {}).map((k) =>
        Presents[k].nom.replace(/^(ser|lord|dame|dama|mestre|prince(sse)?|reine|roi)\s+/i, "")
          .split(/[ ,]/)[0]);
      if (gens.length) {
        t += '<text class="plan-avec" x="' + x + '" y="' +
          (y + lignes.length * h + 1).toFixed(1) + '">' + esc(gens.join(" · ")) + "</text>";
      }
    }
    return t;
  }

  // La rose des vents : le plan est orienté (le levant est à droite, le
  // Dragonmont au nord), autant le dire. Dessinée en unités, elle grandit avec
  // la carte comme le reste du dessin.
  function rose(r) {
    const [x, y, t] = r;
    const b = t * 0.34;
    return '<g class="plan-rose"><path d="M' + x + ',' + (y - t) + ' L' + (x + b) + ',' +
      (y - b) + ' L' + (x + t) + ',' + y + ' L' + (x + b) + ',' + (y + b) + ' L' + x + ',' +
      (y + t) + ' L' + (x - b) + ',' + (y + b) + ' L' + (x - t) + ',' + y + ' L' + (x - b) +
      ',' + (y - b) + ' Z"/><path class="plan-rose-nord" d="M' + x + ',' + (y - t) + ' L' +
      (x + b) + ',' + (y - b) + ' L' + (x - b) + ',' + (y - b) + ' Z"/></g>';
  }

  function svgPlan(grand, v) {
    let s = '<svg viewBox="' + plan.viewBox + '" xmlns="http://www.w3.org/2000/svg"' +
      ' class="plan ' + (grand ? "plan-grand" : "plan-petit") + '"' +
      ' style="font-size:' + v.police.toFixed(2) + 'px">';

    (plan.fonds || []).forEach((f) => {
      s += '<path class="' + f.classe + '" d="' + f.d + '"/>';
    });
    // Le relief du dehors : les crêtes de la montagne, la houle de la baie.
    // Non cliquable, sous tout le reste — c'est ce qui empêche le plan de
    // flotter dans le vide et dit d'un coup d'œil où est la roche et où est l'eau.
    (plan.decor || []).forEach((f) => {
      s += '<path class="' + f.classe + '" d="' + f.d + '"/>';
    });

    const salle = (sa) => '<g class="plan-salle' + (sa.etage ? " etage" : "") +
      (sa.dehors ? " dehors" : "") + (sa.fond ? " fond" : "") +
      (sa.id === salleId ? " ici" : "") + '" data-id="' + esc(sa.id) +
      '" data-nom="' + esc(sa.nom) + '"><title>' + esc(sa.nom) +
      (sa.quoi ? " — " + esc(sa.quoi) : "") + "</title>" +
      forme(sa) + details(sa) + orne(sa) + nomSalle(sa, v) + "</g>";

    plan.salles.filter((x) => x.fond).forEach((x) => { s += salle(x); });
    s += '<path class="plan-mur" d="' + plan.mur + '"/>' + crenelage(plan.guet);
    (plan.guet || []).forEach((g) => { s += guet(g); });
    plan.salles.filter((x) => !x.fond).forEach((x) => { s += salle(x); });

    if (v.tous) {
      (plan.etiquettes || []).forEach((e) => {
        s += '<text class="' + (e.classe || "plan-large") + '" x="' + e.x + '" y="' +
          e.y + '">' + esc(e.texte) + "</text>";
      });
    }
    if (plan.rose) s += rose(plan.rose);
    return s + "</svg>";
  }

  // Deux passes : on trace d'après la place offerte, on mesure ce qui a été
  // rendu (la carte peut être bornée par la hauteur, pas par la largeur), et
  // on retrace si l'échelle devinée était fausse. Jamais de troisième passe.
  function poser(hote, grand, apres) {
    const vbL = parseFloat(plan.viewBox.split(/\s+/)[2]) || 420;
    const cible = grand ? CIBLE.grand : CIBLE.petit;
    const tracer = (large) => {
      const ech = Math.max(large, 40) / vbL;
      hote.innerHTML = svgPlan(grand, { police: cible / ech, tous: grand || large >= SEUIL_TOUS }) +
        (grand ? "" : '<button id="plan-deplier">Déplier le plan…</button>');
      return hote.querySelector("svg").getBoundingClientRect().width;
    };
    const devine = hote.clientWidth || vbL;
    const vrai = tracer(devine);
    if (vrai && Math.abs(vrai - devine) > 3) tracer(vrai);
    brancher(hote, apres);
  }

  function brancher(racine, apres) {
    racine.querySelectorAll(".plan-salle").forEach((g) => {
      g.addEventListener("click", (e) => {
        e.stopPropagation();
        if (window.Entites) Entites.penser(g.dataset.id, "salle", g.dataset.nom);
        if (apres) apres();
      });
    });
  }

  // ---- le plan déplié (overlay) -------------------------------------------
  function batirOverlay() {
    if (document.getElementById("plan-large")) return;
    const ov = document.createElement("div");
    ov.id = "plan-large";
    ov.hidden = true;
    ov.innerHTML =
      '<div id="plan-cadre">' +
      '<div id="plan-tete"><span id="plan-titre"></span>' +
      '<span id="plan-ou"></span>' +
      '<button id="plan-fermer" title="Replier">Replier le plan</button></div>' +
      '<div id="plan-corps"></div>' +
      '<div id="plan-legende"><span class="leg leg-ici">Vous êtes ici</span>' +
      '<span class="leg-etage">Un autre étage : au sommet, ou sous la roche</span>' +
      '<span class="leg-orne">Le signe dit ce qu\'on y fait</span>' +
      '<span class="leg-note">Une salle où l\'on songe, en la touchant du doigt</span></div></div>';
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => { if (e.target === ov) fermer(); });
    ov.querySelector("#plan-fermer").addEventListener("click", fermer);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !ov.hidden) fermer();
    });
  }
  function ouvrir() {
    if (!plan) return;
    batirOverlay();
    const ov = document.getElementById("plan-large");
    const ici = plan.salles.find((s) => s.id === salleId);
    ov.querySelector("#plan-titre").textContent = "Le plan de " + plan.nom;
    ov.querySelector("#plan-ou").textContent = ici ? ici.nom : "";
    const c = ov.querySelector("#plan-corps");
    // le cadre doit être visible avant de mesurer : un élément caché n'a pas
    // de taille, et la deuxième passe tracerait dans le vide
    ov.hidden = false;
    poser(c, true, fermer);
  }
  function fermer() {
    const ov = document.getElementById("plan-large");
    if (ov) ov.hidden = true;
  }

  // ---- la vignette et la bascule des deux échelles -------------------------
  let largeurRendue = 0, essais = 0;

  function dessiner() {
    const hote = document.getElementById("plan");
    if (!hote) return;
    if (!plan) { hote.innerHTML = ""; largeurRendue = 0; return; }
    poser(hote, false, null);
    const svg = hote.querySelector("svg");
    largeurRendue = svg.getBoundingClientRect().width;
    // tracé pendant que le décor n'a pas encore de largeur (chargement) : on ne
    // garde pas une échelle fausse, on repasse. Trois essais et l'on renonce —
    // si le plan reste sans largeur, c'est qu'il est masqué, et l'observateur
    // de taille rappellera dès qu'il reparaîtra.
    if (!largeurRendue && essais < 3) { essais++; setTimeout(dessiner, 60); }
    else if (largeurRendue) essais = 0;
    svg.addEventListener("click", ouvrir);
    hote.querySelector("#plan-deplier").addEventListener("click", (e) => {
      e.stopPropagation();
      ouvrir();
    });
  }

  // La carte a-t-elle changé de taille depuis son tracé ? Alors on la retrace :
  // c'est ce qui garde le corps du texte à la même taille apparente et lui fait
  // rendre les noms qu'elle a désormais la place de porter. Retracer change la
  // hauteur du décor, donc l'appel peut revenir en écho : on ne repart que si la
  // largeur a vraiment bougé.
  function verifier() {
    const hote = document.getElementById("plan");
    if (!plan || !hote || hote.classList.contains("vue-off")) return;
    const svg = hote.querySelector("svg");
    const l = svg ? svg.getBoundingClientRect().width : 0;
    if (l && Math.abs(l - largeurRendue) > 3) dessiner();
  }

  function surveiller() {
    const hote = document.getElementById("plan");
    if (!hote) return;
    // Un minuteur, pas requestAnimationFrame : dans un onglet d'arrière-plan les
    // frames ne sont jamais servies.
    let prevu = null;
    const plusTard = () => {
      if (prevu) return;
      prevu = setTimeout(() => { prevu = null; verifier(); }, 80);
    };
    // L'observateur de taille répond dans l'instant et attrape tout ce qui
    // change la carte — la fenêtre, mais aussi le bandeau des présents qui
    // s'épaissit et reprend de la hauteur au décor. Il ne parle en revanche
    // JAMAIS dans un onglet qui n'est pas à l'écran : ses notifications sont
    // servies avec les frames, comme requestAnimationFrame. D'où le rattrapage
    // à intervalle — une mesure de rectangle toutes les deux secondes ne coûte
    // rien, et le joueur qui revient sur son onglet retrouve une carte juste.
    if (window.ResizeObserver) new ResizeObserver(plusTard).observe(hote);
    setInterval(verifier, 2000);
  }

  // ---- les échelles du décor -----------------------------------------------
  // Le décor empile plusieurs cartes dans #cartes et n'en montre qu'une. Chacune
  // s'inscrit ici avec son hôte et le moment où elle a quelque chose à montrer :
  // le château seulement là où l'on a un plan, le terrain seulement quand il y a
  // un champ. Le royaume, lui, est toujours là — c'est le repli.
  const ECHELLES = [
    { id: "chateau", nom: "Le château", hote: "plan", ordre: 1,
      dispo: () => !!plan, reparu: verifier },
    { id: "royaume", nom: "Le royaume", hote: "carte", ordre: 2, dispo: () => true },
  ];
  function echelle(def) {
    if (ECHELLES.some((e) => e.id === def.id)) return;
    ECHELLES.push(def);
    ECHELLES.sort((a, b) => (a.ordre || 9) - (b.ordre || 9));
    rebattre();
  }
  const offertes = () => ECHELLES.filter((e) => {
    try { return e.dispo(); } catch (err) { return false; }
  });

  function appliquerVue() {
    const dispo = offertes();
    let choisie = dispo.find((e) => e.id === vue) || dispo.find((e) => e.id === "royaume") || dispo[0];
    if (!choisie) return;
    ECHELLES.forEach((e) => {
      const h = document.getElementById(e.hote);
      if (h) h.classList.toggle("vue-off", e !== choisie);
    });
    document.querySelectorAll("#vue-bascule button").forEach((b) => {
      b.classList.toggle("actif", b.dataset.vue === choisie.id);
    });
    if (choisie.reparu) choisie.reparu();
  }

  // Quand un conseiller montre quelque chose sur la table peinte, il ne sert à
  // rien de le montrer derrière le plan du château : le décor bascule.
  function montrer(quoi) {
    if (quoi === vue) return;
    vue = quoi;
    try { localStorage.setItem("conseil-vue", vue); } catch (e) {}
    appliquerVue();
  }

  // Une seule échelle offerte n'a pas besoin de bascule : c'est le décor.
  function bascule() { rebattre(); }
  function rebattre() {
    let barre = document.getElementById("vue-bascule");
    const dispo = offertes();
    if (dispo.length < 2) { if (barre) barre.remove(); return; }
    if (!barre) {
      barre = document.createElement("div");
      barre.id = "vue-bascule";
      // dans #cartes, pas dans #decor : la bascule coiffe les cartes, elle ne
      // flotte pas au-dessus du bandeau des présents.
      const hote = document.getElementById("cartes") || document.getElementById("decor");
      if (!hote) return;
      hote.appendChild(barre);
      barre.addEventListener("click", (e) => {
        const b = e.target.closest("button");
        if (!b) return;
        vue = b.dataset.vue;
        try { localStorage.setItem("conseil-vue", vue); } catch (err) {}
        appliquerVue();
      });
    }
    const veut = dispo.map((e) => e.id).join("|");
    if (barre.dataset.echelles === veut) return;
    barre.dataset.echelles = veut;
    barre.innerHTML = dispo.map((e) =>
      '<button data-vue="' + e.id + '">' + e.nom + "</button>").join("");
    appliquerVue();
  }

  // ---- le fil : les salles distinctives deviennent cliquables -------------
  function offrirEntites() {
    if (!plan || !window.Entites || !Entites.ajouter) return;
    Entites.ajouter(plan.salles
      .filter((s) => (s.alias || []).length)
      .map((s) => ({ id: s.id, type: "salle", noms: s.alias })));
  }

  // ---- le lieu où l'on se trouve ------------------------------------------
  function relire() {
    const avant = salleId;
    salleId = deviner();
    if (salleId !== avant) dessiner();
    const ov = document.getElementById("plan-large");
    if (ov && !ov.hidden && salleId !== avant) ouvrir();
    // une scène qui change, c'est souvent une salle qui se remplit ou se vide :
    // le bandeau des présents prend ou rend de la hauteur au décor, et la carte
    // n'a plus la même taille qu'à son tracé.
    verifier();
  }

  function charger() {
    fetch("/carte").then((r) => r.json()).then((d) => {
      const p = P[d.joueur_lieu_id];
      if (p === plan) return;
      plan = p || null;
      salleId = deviner();
      bascule();
      offrirEntites();
      // découvrir AVANT de tracer : un plan caché n'a pas de largeur, et le
      // tracé se réglerait sur une carte de zéro pixel.
      appliquerVue();
      dessiner();
    }).catch(() => {});
  }

  window.addEventListener("DOMContentLoaded", () => {
    try { vue = localStorage.getItem("conseil-vue"); } catch (e) {}
    // On ne valide pas l'échelle gardée ici : elle peut appartenir à un module
    // qui n'a pas encore ses données (le terrain arrive par le réseau).
    // `appliquerVue` retombe sur le royaume tant qu'elle n'est pas offerte.
    if (!vue) vue = "chateau";
    // tant qu'aucun plan n'est trouvé pour le lieu du joueur, le royaume tient
    // le décor : deux cartes empilées vaudraient moins qu'une.
    appliquerVue();
    charger();
    surveiller();
    setInterval(charger, 60000);
    // Le bandeau est reposé par le bus à chaque item porteur d'un `lieu` :
    // on suit ce texte plutôt que d'intercepter le flux, qui n'a qu'un rendu
    // par type et appartient déjà à d'autres modules.
    const bandeau = document.getElementById("lieu");
    if (bandeau) new MutationObserver(relire).observe(bandeau, {
      childList: true, characterData: true, subtree: true, attributes: true });
  });

  return { ouvrir, fermer, relire, montrer, echelle, rebattre };
})();
