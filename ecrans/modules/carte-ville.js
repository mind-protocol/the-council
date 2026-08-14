// carte-ville.js — la ville en plan, dessinée, à toute heure.
//
// Ce qu'elle remplace : les trois hauteurs en volume. Le monde 3D est juste et
// il reste servi — mais il ne se voit pas la nuit, et cette partie se joue le
// soir. Or ce qu'on demande à cette échelle est plan, et rien d'autre : où est
// la rue des Sœurs, combien de pas jusqu'à la porte de la Gadoue, par où l'on
// sort quand la maison se referme.
//
// Rien n'est calculé ici. `scripts/monde/plan_ville.py` cuit une fois
// `monde/<x>.plan2d.json` — la côte, huit courbes de niveau, les voies chaînées
// par classe et 48 377 bâtiments en rectangles orientés — et ce module ne fait
// que le poser et le laisser regarder. Deux gestes, les mêmes que le plan du
// château : la molette approche, le glissé déplace, le double-clic repose.
//
// LE GRAIN SUIT L'APPROCHE, et c'est toute l'astuce d'un plan de 48 000
// maisons : de loin on ne montre que l'eau, le relief, les artères et les
// vingt institutions — de près, tout. Une carte qui affiche ses quarante mille
// toits à pleine page n'est pas une carte, c'est du bruit. Les paliers sont des
// classes sur le SVG ; c'est la feuille de style qui allume les couches, pas
// du JavaScript qui redessine.
"use strict";
window.CarteVille = (() => {
  const HOTE = "ville2d";
  let plan = null;          // le fichier cuit
  let svg = null;
  let vue = null;           // [x, y, l, h] — le viewBox courant, en mètres
  let base = null;          // le cadrage d'origine, pour le double-clic
  let source = null;        // la racine du monde servi ("/monde", "/monde/x")
  let moi = null;           // où se tient le joueur, en mètres

  const hote = () => document.getElementById(HOTE);
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // ---- quel monde ---------------------------------------------------------
  // Même repli que `ville3d` : le joueur se tient dans un BÂTIMENT, le monde
  // est bâti par VILLE. On demande au serveur ce qu'il offre, et l'on prend
  // celui qui nous contient — puis, faute de mieux, celui par défaut.
  function trouverSource(lieuId) {
    return fetch("/monde/lieux").then((r) => r.json()).then((d) => {
      const l = (d.lieux || []);
      const m = l.find((x) => x.id === lieuId) ||
                l.find((x) => (x.contient || []).indexOf(lieuId) >= 0) ||
                l.find((x) => x.id === d.defaut);
      return m ? m.source : null;
    }).catch(() => null);
  }

  // ---- le dessin ----------------------------------------------------------
  // L'ORDRE DES COUCHES EST LE DESSIN. L'eau dessous, le relief par-dessus,
  // puis les voies, puis le bâti — une maison est bâtie SUR le sol de la rue et
  // le mange, elle ne flotte pas dessous —, puis ce qui se lit : les noms, les
  // repères, et vous. C'est ce recouvrement qui donne à un plan de ville son
  // grain : ce qui reste de chaussée entre deux façades est ce qui reste
  // vraiment, et l'on voit d'un coup d'œil où l'on passe à deux et où l'on
  // passe de biais.
  // LE BÂTI SE COLORE PAR TYPE, PAS PAR FAMILLE. Le plan cuit porte une couche
  // par type — trente-sept à Port-Réal, du taudis au bureau du maître de port —
  // et sa table `types` dit à quelle famille chacun appartient. Chaque couche
  // reçoit donc DEUX classes : `cv-b-<famille>` donne la teinte, `cv-u-<type>`
  // la clarté. Un type qui manque à la feuille de style reste de la couleur de
  // sa famille, ce qui est un défaut acceptable ; une famille inconnue ne peut
  // pas arriver, c'est le même script qui sème et qui cuit.
  // L'ordre vient du fichier (du plus commun au plus rare) : ce qui est écrit
  // en premier est dessiné dessous.
  const bâtiCouches = () => Object.keys((plan && plan.types) || {})
    .filter((u) => (plan.bati || {})[u]);
  const famille = (u) => ((plan.types || {})[u] || {}).cat || "habitat";

  // LE SURVOL DIT CE QUE C'EST. Une couleur sans légende se devine à moitié :
  // on voit bien que ce pâté-là n'est pas de l'habitat, mais on ne sait pas si
  // c'est une tannerie ou une brasserie. Chaque couche porte donc son nom en
  // clair, et comme une couche est UN chemin pour tout un type, ça ne coûte
  // que trente-sept titres pour trente mille silhouettes — poser un `<title>`
  // par maison ferait un document de trente mille nœuds pour la même chose.
  // Le nom vient du monde (`usages.py`), jamais d'une table recopiée ici.
  const coucheBati = (u) => {
    const t = (plan.types || {})[u] || {};
    return '<path class="cv-bati cv-b-' + famille(u) + " cv-u-" + u +
      '" d="' + plan.bati[u] + '"><title>' + esc(t.nom || u) + "</title></path>";
  };
  const VOIES = ["ruelle", "abord", "escalier", "rue", "quai", "artere"];

  // ---- les rues ne sont pas des polygones ---------------------------------
  // Le fichier cuit donne les voies en polylignes : une suite de `L`, chacune
  // un segment droit, et les coudes se voyaient — une ville entière tracée à
  // l'équerre, ce qui n'a l'air ni médiéval ni tracé par des pieds.
  //
  // C'EST LA LARGEUR QUI FAIT LA COURBE, et rien d'autre. Une rue peinte au
  // trait fin garde ses angles ; la même rue peinte à sa largeur réelle, avec
  // des jointures rondes, les perd toutes : la chaussée s'arrondit d'elle-même
  // à chaque coude, comme une vraie. Le SVG le fait tout seul — les voies sont
  // écrites en MÈTRES (`stroke-width` en unités du plan, pas en pixels), avec
  // `stroke-linejoin: round`, et l'on n'a pas une ligne de JavaScript à écrire
  // ni un chemin à recalculer.

  function dessiner() {
    const h = hote();
    if (!h || !plan) return;
    const [x0, y0, x1, y1] = plan.bornes;
    base = [x0, y0, x1 - x0, y1 - y0];
    vue = vue || base.slice();
    const couche = (cl, d, extra) =>
      d ? '<path class="cv-' + cl + '" d="' + d + '"' + (extra || "") + "/>" : "";
    h.innerHTML =
      '<svg id="cv-svg" viewBox="' + vue.join(" ") + '" ' +
      'preserveAspectRatio="xMidYMid meet">' +
      '<rect class="cv-sol" x="' + x0 + '" y="' + y0 + '" width="' + (x1 - x0) +
        '" height="' + (y1 - y0) + '"/>' +
      couche("eau", plan.cote) +
      '<g class="cv-niveaux">' +
        (plan.niveaux || []).map((n) => couche("niveau", n.d)).join("") + "</g>" +
      '<g class="cv-voies">' +
        VOIES.map((g) => couche("voie cv-v-" + g, (plan.voies || {})[g])).join("") + "</g>" +
      '<g class="cv-bati">' + bâtiCouches().map(coucheBati).join("") + "</g>" +
      // L'ENCEINTE PAR-DESSUS LE BÂTI, et c'est voulu. Le rempart est ce qui
      // fait de Port-Réal une ville plutôt qu'un tas de toits : c'est le trait
      // le plus fort du plan, celui qui dit dedans et dehors, et il ne se
      // laisse pas manger par les maisons qui s'y adossent. Il tient à toutes
      // les échelles — de loin il EST la ville, de près il est le mur qu'on
      // longe pour aller à la porte de la Gadoue.
      '<g class="cv-rempart">' +
        couche("courtine", (plan.rempart || {}).courtine) +
        couche("tour", (plan.rempart || {}).tours) + "</g>" +
      '<g class="cv-noms">' + noms() + "</g>" +
      '<g class="cv-reperes">' + marques() + "</g>" +
      '<g class="cv-route"></g>' +
      '<g class="cv-vous">' + vous() + "</g></svg>";
    svg = h.querySelector("#cv-svg");
    grain();
    brancher();
    // La foule vient PAR-DESSUS, sur sa propre toile : le plan ne bouge pas,
    // elle change à chaque image, et les deux n'ont donc pas à être du même
    // matériau. Elle se repose après chaque redessin sans perdre son heure.
    plein();
    if (window.Foule2d) Foule2d.poser(h, () => vue, { source });
    // Et la bataille par-dessus la foule, sur sa propre toile encore : ce sont
    // trois cents corps qui ne suivent pas l'horloge de la ville mais la
    // seconde réelle. Deux temps, deux couches — on ne les mélange pas.
    if (window.Bataille2d) Bataille2d.poser(h, () => vue, { source });
  }

  // Les noms de quartier : posés au milieu de leurs maisons (le script en fait
  // le barycentre), et dimensionnés par leur POIDS — « La ville » porte 36 000
  // toits, « Le bourg de la Gadoue » cinquante-neuf, et l'œil doit le savoir
  // avant de lire.
  function noms() {
    return (plan.quartiers || []).map((q) => {
      const t = Math.max(34, Math.min(96, 26 * Math.log10(Math.max(10, q.n))));
      return '<text class="cv-quartier" x="' + q.x + '" y="' + q.y +
        '" font-size="' + t.toFixed(0) + '">' + esc(q.nom) + "</text>";
    }).join("");
  }

  // Les repères sont ce qui se cherche vraiment sur ce plan : les sept portes,
  // les quais, les marchés. Ils gardent leur nom à toutes les échelles — c'est
  // par eux qu'on se retrouve quand tout le reste est un grain de toits.
  function marques() {
    return (plan.reperes || []).map((r) =>
      '<g class="cv-repere cv-r-' + esc(r.genre) + '" data-nom="' + esc(r.nom) + '">' +
      '<title>' + esc(r.nom) + "</title>" +
      '<circle cx="' + r.x + '" cy="' + r.y + '" r="11"/>' +
      '<text x="' + (r.x + 18) + '" y="' + (r.y + 9) + '">' + esc(r.nom) + "</text></g>"
    ).join("");
  }

  // « VOUS ÊTES ICI » — et il vaut mieux ne rien montrer que montrer faux.
  // Tant que le lieu du joueur n'a pas d'adresse en mètres (`affecter.py`), on
  // n'invente pas un point : une marque plantée sur l'enceinte du Donjon Rouge
  // pendant qu'on répète au Grenier est pire qu'une carte sans marque.
  function vous() {
    if (!moi) return "";
    return '<g class="cv-ici"><title>Vous êtes ici' +
      (moi.nom ? " — " + esc(moi.nom) : "") + "</title>" +
      '<circle class="cv-ici-halo" cx="' + moi.x + '" cy="' + moi.y + '" r="70"/>' +
      '<circle class="cv-ici-point" cx="' + moi.x + '" cy="' + moi.y + '" r="16"/>' +
      (moi.nom ? '<text x="' + moi.x + '" y="' + (moi.y - 26) + '">' +
        esc(moi.nom) + "</text>" : "") + "</g>";
  }

  // ---- le grain ------------------------------------------------------------
  // Trois paliers, et le seuil se mesure en MÈTRES PAR PIXEL — pas en niveau de
  // zoom, qui ne veut rien dire tant qu'on ne sait pas la taille de la case.
  // Au-delà de 12 m/px une maison fait un demi-pixel : la dessiner, c'est
  // peindre du gris. En deçà de 1,2 m/px les ruelles se séparent et le bâti se
  // lit maison par maison. Entre les deux — c'est-à-dire tout le plein écran,
  // du plus large recul au quartier —, on montre la ville entière.
  function grain() {
    if (!svg || !vue) return;
    // UNE CARTE CACHÉE N'A PAS DE LARGEUR, et deviner la sienne ne donne pas un
    // palier approximatif : ça en donne un FAUX, figé jusqu'au prochain geste.
    // On ne fait rien tant qu'elle n'est pas mesurable ; le ResizeObserver
    // rappelle dès que le décor lui rend de la place.
    const large = svg.getBoundingClientRect().width;
    if (!large) return;
    const mpp = vue[2] / large;
    // LE SEUIL ÉTAIT À 4 m/px, ET IL TOMBAIT TROP TÔT. La ville entière tient
    // dans un volet de 700 à 900 px, soit 6 à 7,5 m/px : un cran de molette en
    // arrière depuis la vue courante et tout le bâti s'éteignait — c'est-à-dire
    // exactement quand la carte devient belle. Or ce n'est pas la lisibilité
    // qui commandait ce seuil, c'est une prudence de rendu qui ne se justifie
    // pas : le SVG dessine ses 27 000 silhouettes qu'on les regarde de près ou
    // de loin, la vue n'y change rien.
    //
    // On le repousse donc à 12, choisi pour que RIEN NE S'ÉTEIGNE AU PLEIN
    // ÉCRAN : le dézoom s'arrête à deux fois l'emprise, soit 10 560 m, ce qui
    // fait 11,7 m/px dans un volet de 900 px — juste en deçà. Les toits
    // tiennent donc jusqu'au bout du recul. Au-delà de 12, on n'est plus au
    // plein écran mais dans la vignette du décor (la ville dans 440 px), où
    // une maison mesure un demi-pixel et où la peindre revient à passer du
    // gris : là, et là seulement, le bâti s'efface.
    svg.classList.toggle("cv-loin", mpp > 12);
    svg.classList.toggle("cv-moyen", mpp <= 12 && mpp > 1.2);
    svg.classList.toggle("cv-pres", mpp <= 1.2);
    // LE BÂTI ET LA TOILE DES RUELLES N'ONT PAS LE MÊME SEUIL, et les confondre
    // était la faute : en repoussant l'effacement du bâti de 4 à 12 m/px, on a
    // repoussé du même coup les quatorze mille ruelles, qui se sont mises à
    // baver sur toute la carte — surtout sur le flanc de Rhaenys, où le semis
    // a tracé près de trois mille points de venelles pour PAS UNE maison.
    //
    // Deux choses de nature différente : une maison de loin est un grain de
    // ville, elle fait masse et elle est juste ; une ruelle de loin est un
    // cheveu qu'aucun œil ne suit, et mille cheveux font un voile. La toile
    // fine — venelles, abords, escaliers — s'éteint donc dès 3,5 m/px, là où
    // deux ruelles voisines cessent d'être distinguables, et le bâti tient
    // jusqu'au bout du recul.
    // 3,5 ÉTAIT ENCORE TROP TARD. La vue qui montre les quartiers d'un coup
    // d'œil tourne autour de 3 m/px : elle passait donc juste sous le seuil, et
    // c'est exactement là que la toile est le plus nuisible — quatorze mille
    // venelles à un demi-pixel, plus larges que vraies à cause du plancher,
    // qui font un grillage par-dessus la ville au lieu de la dire.
    //
    // On coupe donc à 2, et surtout ON NE COUPE PLUS D'UN COUP : entre 1,2 et
    // 2 la toile pâlit d'abord. Une couche qui disparaît net d'un cran de
    // molette se remarque ; une couche qui s'efface ne se remarque pas, et
    // c'est tout ce qu'on lui demande.
    svg.classList.toggle("cv-sans-toile", mpp > 2);
    svg.classList.toggle("cv-toile-pale", mpp > 1.2 && mpp <= 2);
    // Les traits sont écrits en mètres : sans correction ils épaississent en
    // approchant, et une artère finit large comme un quartier. On les tient à
    // une épaisseur APPARENTE constante en les divisant par l'échelle.
    svg.style.setProperty("--mpp", mpp.toFixed(3));
  }

  function cadrer() {
    if (!svg || !vue) return;
    svg.setAttribute("viewBox", vue.map((v) => v.toFixed(1)).join(" "));
    grain();
    if (window.Foule2d) Foule2d.recadrer();
    if (window.Bataille2d) Bataille2d.recadrer();
  }

  // ---- la prise ------------------------------------------------------------
  // Exactement les gestes du plan du château : molette pour approcher, glissé
  // pour déplacer, double-clic pour reposer. Deux cartes dans le même décor qui
  // ne se prendraient pas de la même main, c'est une carte qu'on n'ouvre plus.
  function brancher() {
    if (!svg || svg.dataset.branche) return;
    svg.dataset.branche = "1";
    const enMetres = (ev) => {
      const b = svg.getBoundingClientRect();
      return [vue[0] + (ev.clientX - b.left) / b.width * vue[2],
              vue[1] + (ev.clientY - b.top) / b.height * vue[3]];
    };
    svg.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const [mx, my] = enMetres(ev);
      // On zoome VERS LE POINTEUR : le point sous le doigt ne bouge pas. Un
      // zoom qui recentre sur le milieu fait perdre ce qu'on regardait à
      // chaque cran, et l'on passe son temps à se rattraper.
      const k = ev.deltaY > 0 ? 1.18 : 1 / 1.18;
      // On peut reculer jusqu'à DEUX FOIS l'emprise : la ville tient alors au
      // milieu avec sa marge de champs et de rade autour, ce qui est le bon
      // cadrage pour montrer où l'on va. Au-delà, on regarde du vide.
      const l = Math.max(140, Math.min(base[2] * 2, vue[2] * k));
      const r = l / vue[2];
      vue = [mx - (mx - vue[0]) * r, my - (my - vue[1]) * r, l, vue[3] * r];
      cadrer();
    }, { passive: false });
    let prise = null;
    svg.addEventListener("pointerdown", (ev) => {
      prise = { x: ev.clientX, y: ev.clientY, v: vue.slice(), bouge: 0 };
      svg.setPointerCapture(ev.pointerId);
      svg.classList.add("cv-tire");
    });
    svg.addEventListener("pointermove", (ev) => {
      if (!prise) return;
      prise.bouge = Math.max(prise.bouge,
        Math.abs(ev.clientX - prise.x) + Math.abs(ev.clientY - prise.y));
      const b = svg.getBoundingClientRect();
      vue = [prise.v[0] - (ev.clientX - prise.x) / b.width * prise.v[2],
             prise.v[1] - (ev.clientY - prise.y) / b.height * prise.v[3],
             prise.v[2], prise.v[3]];
      cadrer();
    });
    // Un glissé qui finit sur la carte n'est pas un clic : sans ce garde-fou,
    // déplacer le plan d'un doigt lancerait une marche vers l'endroit lâché.
    dernierBouge = 0;
    const lacher = () => {
      dernierBouge = prise ? prise.bouge : 0;
      prise = null;
      svg.classList.remove("cv-tire");
    };
    svg.addEventListener("pointerup", lacher);
    svg.addEventListener("pointercancel", lacher);
    svg.addEventListener("dblclick", () => { vue = base.slice(); cadrer(); });
    // Un repère cliqué se pense, comme un nom en gras du fil : c'est le même
    // canal d'introspection, et il ne coûte pas une minute. Un point de la
    // ville cliqué, lui, est un BUT : on demande le chemin pour y aller.
    svg.addEventListener("click", (ev) => {
      if (bougeAuClic(ev)) return;
      const r = ev.target.closest(".cv-repere");
      if (r && window.Bus && Bus.poster) {
        Bus.poster({ type: "pensee", cible: r.dataset.nom, cible_type: "lieu" });
        return;
      }
      // On ne part pas de nulle part. Sans adresse en mètres, le clic ne
      // faisait RIEN et rien ne le disait — on le dit.
      if (!moi) {
        barre("On ne sait pas d'où vous partez : ce lieu n'a pas d'adresse.");
        return;
      }
      const b = svg.getBoundingClientRect();
      partirVers([vue[0] + (ev.clientX - b.left) / b.width * vue[2],
                  vue[1] + (ev.clientY - b.top) / b.height * vue[3]]);
    });
    if (window.ResizeObserver) new ResizeObserver(grain).observe(svg);
  }

  // =========================================================================
  // LA MARCHE — jouer une balade à travers la ville
  //
  // On pose un but d'un clic, le serveur rend l'itinéraire par les rues, et
  // l'on y va. Ce qui compte, et qui n'est pas de la décoration :
  //
  //   • LA VITESSE SORT DU CHEMIN. Le serveur chiffre l'itinéraire en minutes
  //     — une artère se descend plus vite qu'un escalier de Visenya —, et
  //     l'allure de la balade en découle. Le sélecteur ×1…×10 n'accélère pas
  //     le marcheur : il accélère LE JEU. À ×1, une minute de fiction coûte
  //     une minute de vraie vie ; à ×10, six secondes.
  //   • LA MONTRE TOURNE POUR DE BON. Chaque tronçon de vingt mètres est
  //     envoyé au serveur, qui avance l'horloge du siège et celle du monde. On
  //     ne traverse pas Port-Réal gratuitement.
  //   • LE MJ REÇOIT LA TRACE, pas la position. Tous les vingt mètres, ce
  //     qu'on longe — le métier des maisons, le quartier, le repère le plus
  //     proche. C'est de ça qu'une balade se raconte.
  // =========================================================================
  const PAS_M = 20;         // le tronçon qu'on rapporte au MJ, en mètres
  let route = null;         // {points, metres, minutes, vers}
  let avance = 0;           // mètres parcourus depuis le départ
  let rapporte = 0;         // mètres déjà rapportés au MJ
  let vitesse = 3;          // le multiplicateur de la barre
  let enMarche = false;
  let derniereImage = 0;
  let dernierBouge = 0;

  const bougeAuClic = () => dernierBouge > 6;

  // Le point du chemin à `m` mètres du départ, et le nom de la rue qu'on suit.
  function surLeChemin(m) {
    const p = route.points;
    let reste = m;
    for (let i = 1; i < p.length; i++) {
      const d = Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
      if (reste <= d || i === p.length - 1) {
        const t = d ? Math.max(0, Math.min(1, reste / d)) : 1;
        return [p[i - 1][0] + (p[i][0] - p[i - 1][0]) * t,
                p[i - 1][1] + (p[i][1] - p[i - 1][1]) * t];
      }
      reste -= d;
    }
    return p[p.length - 1];
  }

  function partirVers(but) {
    if (!moi) return;
    const q = "?de=" + moi.x + "," + moi.y + "&vers=" + but[0].toFixed(1) + "," +
      but[1].toFixed(1);
    fetch("/chemin" + q).then((r) => r.json()).then((d) => {
      if (!d || !d.chemin) { barre("Aucune rue n'y mène."); return; }
      route = Object.assign({}, d.chemin, { vers: d.vers });
      avance = 0;
      rapporte = 0;
      enMarche = false;
      tracer();
      barre();
    }).catch(() => {});
  }

  function tracer() {
    const g = svg && svg.querySelector(".cv-route");
    if (!g) return;
    if (!route) { g.innerHTML = ""; return; }
    const d = "M" + route.points.map((p) => p[0].toFixed(1) + " " + p[1].toFixed(1))
      .join("L");
    const ici = surLeChemin(avance);
    g.innerHTML = '<path class="cv-route-trait" d="' + d + '"/>' +
      '<circle class="cv-route-but" cx="' + route.points[route.points.length - 1][0] +
      '" cy="' + route.points[route.points.length - 1][1] + '" r="14"/>';
    // la marque du joueur suit le pas, sans redessiner la ville
    const v = svg.querySelector(".cv-vous");
    if (v) {
      moi = { x: ici[0], y: ici[1], nom: moi ? moi.nom : null };
      v.innerHTML = vous();
    }
  }

  // ---- le plein écran -------------------------------------------------------
  // Une carte de cinq kilomètres dans un panneau d'un tiers d'écran, c'est une
  // carte qu'on lit à la molette. Ici on prend tout, et l'on rend la place
  // ensuite — c'est le seul bouton du plan qui ne parle pas de la fiction, donc
  // il se fait petit et il se tient dans le coin.
  //
  // LE SVG SE RECADRE TOUT SEUL (`preserveAspectRatio` fait le travail), LES
  // TOILES NON. La foule et la bataille sont des canvas en pixels : sans un
  // recadrage explicite, on passe en plein écran et les habitants restent
  // dessinés à l'ancienne taille, dans le coin, à côté de leurs rues. Et
  // `recadrer` REPEINT, il ne retaille pas seulement — en pause il n'y a pas
  // d'image suivante pour rattraper.
  function plein() {
    const h = hote();
    if (!h) return;
    let b = h.querySelector(".cv-plein");
    if (!b) {
      b = document.createElement("button");
      b.className = "cv-plein";
      b.type = "button";
      h.appendChild(b);
      b.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (document.fullscreenElement) document.exitFullscreen();
        else if (h.requestFullscreen) h.requestFullscreen().catch(() => {});
      });
      ["pointerdown", "wheel", "dblclick"].forEach((t) =>
        b.addEventListener(t, (ev) => ev.stopPropagation()));
      // Le navigateur rend la main par Échap sans passer par notre bouton : on
      // écoute donc l'événement, et pas le clic. Une seule fois pour toute la
      // session — l'hôte, lui, se réécrit à chaque redessin du plan.
      if (!plein.branche) {
        plein.branche = true;
        document.addEventListener("fullscreenchange", () => {
          const p = !!document.fullscreenElement;
          const bb = hote() && hote().querySelector(".cv-plein");
          if (bb) { bb.textContent = p ? "⤡" : "⤢";
                    bb.title = p ? "Rendre la place" : "Prendre tout l'écran"; }
          // TOUT DE SUITE, PUIS DEUX FOIS APRÈS. Le recadrage ne tenait qu'à
          // `requestAnimationFrame` — qui ne bat pas dans un onglet caché, et
          // qu'aucun test ne peut donc éprouver. Un redimensionnement ne se
          // suspend pas à une image : on le fait sur-le-champ, et les deux
          // images suivantes rattrapent les navigateurs qui n'ont pas fini
          // leur mise en page.
          const cale = () => {
            if (window.Foule2d) Foule2d.recadrer();
            if (window.Bataille2d) Bataille2d.recadrer();
          };
          cale();
          requestAnimationFrame(() => { cale(); requestAnimationFrame(cale); });
        });
      }
    }
    const p = document.fullscreenElement === h;
    b.textContent = p ? "⤡" : "⤢";
    b.title = p ? "Rendre la place" : "Prendre tout l'écran";
  }

  // La barre : ce qu'il reste, à quelle allure, et de quoi s'arrêter. Trois
  // boutons, pas douze — c'est une promenade, pas un tableau de bord.
  //
  // ON NE LA RECONSTRUIT PAS À CHAQUE IMAGE, et c'est tout le sujet : elle
  // l'était, et ⏸ comme Renoncer ne répondaient jamais. Un `innerHTML` par
  // image détruit le bouton ENTRE le `pointerdown` et le `click` — le doigt
  // appuie sur un élément qui n'existe plus quand le clic se conclut, donc le
  // clic n'a jamais lieu. Rien n'était cassé dans les gestionnaires : la barre
  // se dérobait sous le doigt soixante fois par seconde.
  //
  // D'où la coupure : `barre()` bâtit une fois des nœuds qui ne bougent plus,
  // `rafraichir()` n'écrit que du texte dedans. Le pas appelle le second.
  function barre(message) {
    const h = hote();
    if (!h) return;
    let b = h.querySelector(".cv-barre");
    if (!b) {
      b = document.createElement("div");
      b.className = "cv-barre";
      b.innerHTML =
        '<button data-cv="aller" class="cv-aller">▶</button>' +
        '<span class="cv-reste"><b></b><i></i><small></small></span>' +
        '<span class="cv-allure"><button data-cv="lent">−</button>' +
        "<b>×3</b><button data-cv=\"vite\">+</button></span>" +
        '<button data-cv="renoncer" class="cv-renoncer">Renoncer</button>' +
        '<span class="cv-dit"></span>';
      h.appendChild(b);
      b.addEventListener("click", (ev) => {
        const t = ev.target.closest("[data-cv]");
        if (!t) return;
        if (t.dataset.cv === "aller") { enMarche = !enMarche; derniereImage = 0; pas(); }
        if (t.dataset.cv === "renoncer") { route = null; enMarche = false; tracer(); }
        if (t.dataset.cv === "vite") vitesse = Math.min(10, vitesse + (vitesse < 3 ? 1 : 2));
        if (t.dataset.cv === "lent") vitesse = Math.max(1, vitesse - (vitesse > 3 ? 2 : 1));
        rafraichir();
      });
    }
    b.querySelector(".cv-dit").textContent = message || "";
    b.classList.toggle("un-mot", !!message);
    if (message) { b.classList.add("ouverte"); return; }
    rafraichir();
  }

  function rafraichir() {
    const h = hote();
    const b = h && h.querySelector(".cv-barre");
    if (!b) return;
    if (!route) { b.classList.remove("ouverte", "un-mot"); return; }
    // ON RÉTABLIT LES BOUTONS. `un-mot` masque tout sauf la phrase — il faut
    // donc le retirer dès qu'il y a de nouveau un chemin, sinon un « aucune
    // rue n'y mène » affiché une fois emportait la barre entière pour le reste
    // de la séance : les boutons étaient là, cachés par une classe qui n'avait
    // plus lieu d'être.
    b.classList.remove("un-mot");
    b.classList.add("ouverte");
    const reste = Math.max(0, route.metres - avance);
    const min = route.metres ? route.minutes * (reste / route.metres) : 0;
    b.querySelector(".cv-aller").textContent = enMarche ? "⏸" : "▶";
    b.querySelector(".cv-reste b").textContent = Math.round(reste) + " pas";
    b.querySelector(".cv-reste i").textContent =
      route.vers ? " — " + route.vers.nom : "";
    b.querySelector(".cv-reste small").textContent =
      (min < 1 ? "moins d'une minute" : Math.round(min) + " minutes") + " de marche";
    b.querySelector(".cv-allure b").textContent = "×" + vitesse;
  }

  // Le pas : une image, un peu de chemin, et tous les vingt mètres un mot au MJ.
  function pas(t) {
    if (!enMarche || !route) return;
    const maintenant = t || performance.now();
    if (!derniereImage) derniereImage = maintenant;
    const dt = Math.min(.25, (maintenant - derniereImage) / 1000);   // secondes
    derniereImage = maintenant;
    // mètres par seconde réelle = (mètres / minutes de fiction) × ×N / 60
    const allure = route.minutes > 0 ? route.metres / (route.minutes * 60) : 1.3;
    avance = Math.min(route.metres, avance + allure * vitesse * dt);
    tracer();
    if (avance - rapporte >= PAS_M || avance >= route.metres) {
      const fait = avance - rapporte;
      rapporte = avance;
      const p = surLeChemin(avance);
      const fin = avance >= route.metres - .5;
      // QUI EST LÀ SE COMPTE ICI, PAS AU SERVEUR. Les corps sont déjà chargés
      // dans cette page — `foule2d` les place à chaque image — et les
      // recalculer côté serveur voudrait dire y porter `journee.js`, la voirie
      // et quatre méga-octets de cellules pour redire ce qu'on sait déjà. Le
      // marcheur rapporte donc ce qu'il croise, comme il rapporte ses mètres.
      const gens = (window.Foule2d && Foule2d.presents(p[0], p[1])) || null;
      // LA RÉPONSE SE LIT, MAINTENANT. Elle était jetée — un POST qu'on
      // envoyait sans jamais regarder ce qui revenait. Or le serveur sait une
      // chose que la page ignore : si quelque chose s'est levé sur le chemin.
      // Une balade qui traverse un assaut sans s'arrêter est une scène perdue,
      // et c'est le genre de perte qui ne se voit pas.
      fetch("/marche", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x: p[0], y: p[1], metres: fait,
          minutes: route.metres ? route.minutes * (fait / route.metres) : 0,
          gens, fin }) })
        .then((r) => r.ok ? r.json() : null)
        .then((d) => {
          if (!d || !d.arret || !enMarche) return;
          enMarche = false; route = null; tracer(); rafraichir();
        }).catch(() => {});
      if (fin) { enMarche = false; route = null; tracer(); rafraichir(); return; }
    }
    rafraichir();
    requestAnimationFrame(pas);
  }

  // ---- où l'on se tient ----------------------------------------------------
  // Les adresses décidées en jeu (`scripts/affecter.py`) disent en mètres où
  // sont les choses de la fiction. Sans elles, pas de marque — voir `vous()`.
  function situer(lieuId, salleId) {
    return fetch(source + "/corps").then((r) => r.ok ? r.json() : null).then((d) => {
      const a = (d && d.affectations) || {};
      // L'HOMME AVANT SA MAISON. Une balade laisse au marcheur une adresse à
      // lui (`personnage:…`, écrite par `/marche` à chaque tronçon) : tant
      // qu'elle est là, elle prime sur celle du bâtiment où il logeait, sinon
      // la marque retournerait au Grenier à chaque relecture.
      const pid = (window.Moi && Moi.personnage_id) || null;
      const p = (pid && a["personnage:" + pid]) ||
                (salleId && (a["salle:" + salleId] || a["lieu:" + salleId])) ||
                (lieuId && a["lieu:" + lieuId]) || null;
      moi = (p && Array.isArray(p.xyz) && p.xyz.length >= 2)
        ? { x: p.xyz[0], y: p.xyz[1], nom: p.nom || null } : null;
    }).catch(() => { moi = null; });
  }

  // ---- l'échelle du décor --------------------------------------------------
  function charger() {
    return fetch("/carte").then((r) => r.json()).then((d) => {
      const lieu = d.joueur_lieu_id || null;
      return trouverSource(lieu).then((s) => {
        if (!s) return;
        source = s;
        return fetch(source + "/plan2d").then((r) => r.ok ? r.json() : null)
          .then((p) => {
            if (!p) return;
            plan = p;
            return situer(lieu, (window.Plan && Plan.salle) ? Plan.salle() : null);
          })
          .then(() => {
            dessiner();
            if (window.Plan && Plan.rebattre) Plan.rebattre();
          });
      });
    }).catch(() => {});
  }

  window.addEventListener("DOMContentLoaded", () => {
    charger();
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "ville2d", nom: "La ville", hote: HOTE, ordre: 2,
        dispo: () => !!plan,
        reparu: () => { dessiner(); },
      });
    }
    // La scène change de salle : la marque suit, sans redessiner la ville.
    document.addEventListener("scene-changee", () => {
      if (!plan || !source) return;
      situer(null, (window.Plan && Plan.salle) ? Plan.salle() : null).then(() => {
        const g = svg && svg.querySelector(".cv-vous");
        if (g) g.innerHTML = vous();
      });
    });
  });

  return { charger, dessiner, plan: () => plan, viser: (v) => { vue = v; cadrer(); } };
})();
