// visage.js — UN HOMME, UN SIGNE, ET LE MÊME PARTOUT.
//
// Le portrait d'un présent était bâti à trois endroits qui ne se parlaient pas :
// la colonne des présents (`galerie.js`), la chronique (`bus.js`), et le
// registre des gens. Chacun rognait, cerclait et posait l'emblème à sa façon —
// si bien que la bordure de l'office, ajoutée dans la salle, manquait dans le
// fil, et que le recadrage qui chasse le fond noir ne valait que pour la salle.
// Deux visages du même homme, à trente centimètres l'un de l'autre.
//
// Ce module est la seule main qui dessine un visage. Il rend une chaîne HTML,
// et non un élément, parce que ses appelants construisent tous des chaînes ;
// tout ce qui doit être retouché sur le SVG (la fenêtre) l'est donc AVANT
// l'insertion, en une passe, sans dépendre du DOM.
//
// Ce qu'un visage porte, et qui vaut partout :
//   • le portrait recadré sur son sujet — pas de fond mort, pas de liseré ;
//   • un anneau à la couleur de son office, la même que sa tache sur le plan ;
//   • l'emblème de cet office dans l'angle, assez grand pour se lire seul ;
//   • et, au survol, LA LOUPE : le visage en grand avec son nom et son titre,
//     parce qu'un portrait de quarante pixels ne se reconnaît pas toujours.
"use strict";
window.Visage = (() => {
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

  // ---- la fenêtre du portrait ---------------------------------------------
  // Les fichiers de `ecrans/portraits/` sont des carrés de 128 avec un disque
  // de fond sombre jusqu'au bord. Cerclé, cela donnait trois bagues au lieu
  // d'une : la bordure, un liseré clair (les coins du carré, que le rond rogne
  // sans les remplir), et le croissant noir du fond qui dépasse du sujet.
  //
  // On resserre la VUE plutôt que de retoucher trente-neuf fichiers. Deux
  // familles, deux cadrages, et les confondre coûterait quelque chose :
  //  • les photos portent une `<image>` posée en 12,12 sur 104 — on cadre
  //    dessus au pixel près, il ne reste rien du fond ;
  //  • les portraits DESSINÉS n'ont pas d'image mais un anneau héraldique à
  //    r=57.5, qui dit au service de qui l'homme est. Lui n'est pas du
  //    remplissage : on coupe le noir mort autour (r 61 à 63), on le garde.
  //
  // Hors de la forme attendue, on ne touche à rien plutôt que de couper au
  // hasard : un portrait bâti autrement garde sa vue d'origine.
  const VUE = /viewBox\s*=\s*(["'])\s*0\s+0\s+128\s+128\s*\1/;
  const IMAGE = /<image\b[^>]*>/i;
  const ATTR = (balise, nom) => {
    const m = new RegExp(nom + '\\s*=\\s*(["\'])([^"\']*)\\1', "i").exec(balise);
    return m ? parseFloat(m[2]) : NaN;
  };

  function cadrer(svg) {
    const s = String(svg || "");
    if (!s || !VUE.test(s)) return s;
    const img = IMAGE.exec(s);
    let vue = "3 3 122 122";
    if (img) {
      const x = ATTR(img[0], "x"), y = ATTR(img[0], "y");
      const w = ATTR(img[0], "width"), h = ATTR(img[0], "height");
      if (!(w > 0 && h > 0)) return s;
      vue = x + " " + y + " " + w + " " + h;
    }
    return s.replace(VUE, 'viewBox="' + vue + '"');
  }

  // ---- la couleur de l'office ---------------------------------------------
  // `Taches.teinte` en décide, et c'est déjà ce qu'on lit sur le plan du
  // château : un visage cerclé de cette couleur-là fait le pont entre la
  // rangée des présents et la tache qu'on vient de voir dans la salle. Sans
  // office reconnu, c'est une grisaille — elle ne prétend aucun rôle.
  function teinte(p) {
    if (!window.Taches || !Taches.teinte) return "";
    return Taches.teinte({ id: p.id, titre: p.titre, office: p.titre });
  }

  function embleme(titre) {
    if (window.Bus && Bus.embleme) return Bus.embleme(titre);
    if (window.Taches && Taches.office) return Taches.office({ titre: titre }) || "";
    return "";
  }

  // ---- le visage ----------------------------------------------------------
  // `p` : {id, nom, titre, portrait_svg}. `opts.classe` ajoute la classe que
  // l'appelant utilise déjà pour sa mise en place (`med-rond`, `chr-icone`…) :
  // le visage se pose dans SA case sans que celle-ci ait à se réécrire.
  // `opts.corps` remplace le portrait quand il n'y en a pas — le blason d'un
  // récit, par exemple, qui n'a ni office ni anneau à porter.
  // UN AVATAR QUI N'EST PAS UN SVG EST UN GLYPHE. Les annales passent « ⚜ »
  // là où une réplique passe un portrait entier : traité comme un visage, le
  // caractère se retrouvait dans une boîte à `line-height:0`, donc écrasé. On
  // regarde ce qu'on a reçu plutôt que de croire le nom du champ.
  const EST_SVG = /^\s*<svg\b/i;

  function html(p, opts) {
    const o = opts || {};
    const a = p || {};
    const brut = a.portrait_svg || "";
    const nu = o.corps || (brut && !EST_SVG.test(brut) ? brut : "");
    const portrait = nu || cadrer(brut);
    const e = !nu && a.titre ? embleme(a.titre) : "";
    const c = nu ? "" : teinte(a);
    return '<span class="visage' + (o.classe ? " " + o.classe : "") +
      (nu ? " visage-nu" : "") + '"' +
      (c ? ' style="--role:' + esc(c) + '"' : "") +
      ' data-nom="' + esc(a.nom || "") + '"' +
      (a.titre ? ' data-titre="' + esc(a.titre) + '"' : "") +
      (a.id ? ' data-id="' + esc(a.id) + '"' : "") + ">" +
      portrait +
      (e ? '<i class="emb-coin" aria-hidden="true">' + e + "</i>" : "") +
      "</span>";
  }

  // ---- la fiche au survol -------------------------------------------------
  // CE N'EST PAS UNE LOUPE, ET C'EST LE PLAN QUI L'A MONTRÉ. Née pour agrandir
  // un portrait trop petit, elle sert d'abord à DIRE QUI C'EST — et sur la
  // carte du château, où un homme n'est qu'une tache d'encre à deux lettres,
  // il n'y a rien à agrandir : il faut aller chercher son visage au registre.
  // Le même geste, deux sources, une seule fiche.
  //
  // POURQUOI UNE COPIE FLOTTANTE ET NON UN `scale()`. Le visage vit dans des
  // conteneurs qui défilent — la colonne des présents, la chronique — et tout
  // ce qui grandit sur place y est coupé par le bord du cadre. Une copie en
  // `position:fixed`, hors de tout parent, échappe seule à ce rognage. Sur la
  // carte, la question ne se pose même pas : il n'y a pas de copie à faire.
  //
  // Elle ne prend jamais le clic : c'est un renseignement, pas un bouton, et
  // le clic appartient à ce qu'on survole (parler à cet homme, ou ouvrir sa
  // salle). Elle porte le nom et le titre — c'est ce que l'emblème d'angle a
  // chassé de sous le visage, et ce qu'une tache ne dit pas du tout.
  const FOIS = 4;
  const COTE_CARTE = 240;          // px : la fiche d'une tache, qui n'a pas de
                                   // taille propre à multiplier
  // Deux bornes, et elles servent des cas opposés. Un PLANCHER, parce que le
  // multiplicateur seul laissait les petits médaillons de la salle (58px) à
  // 232px, c'est-à-dire moins que le visage du fil au repos : on ne survole
  // pas pour obtenir plus petit. Un PLAFOND, parce que le visage du fil fait
  // maintenant 124px et que quatre fois cela sortirait de l'écran sur un
  // portable — la fiche est un agrandissement, pas un rideau sur la page.
  const PLANCHER = 320;
  function borner(cote) {
    const plafond = Math.round(
      Math.min(window.innerWidth, window.innerHeight) * 0.56);
    return Math.min(Math.max(cote, Math.min(PLANCHER, plafond)), plafond);
  }
  let boite = null, cible = null;

  function fermer() {
    if (boite) boite.classList.remove("ouverte");
    cible = null;
  }

  // Ce qu'on montre, d'où que vienne le survol : un visage déjà dessiné qu'on
  // recopie en grand, ou un homme du registre qu'on dessine pour l'occasion.
  function fiche(src) {
    if (src.classList.contains("visage")) {
      const r = src.getBoundingClientRect();
      return { cote: borner(Math.round(Math.max(r.width, r.height) * FOIS)),
               role: src.style.getPropertyValue("--role"),
               dedans: src.innerHTML,
               nom: src.dataset.nom || "", titre: src.dataset.titre || "" };
    }
    // une tache de carte : elle n'a que son id, le registre a le reste
    const id = src.dataset.id || "";
    const f = (window.Gens && Gens.qui) ? (Gens.qui(id) || {}) : {};
    const p = { id: id, nom: f.nom || src.dataset.nom || id,
                titre: f.titre || "", portrait_svg: f.portrait_svg || "" };
    if (!p.portrait_svg) return null;   // sans visage, la fiche n'apprend rien
    return { cote: borner(COTE_CARTE), role: teinte(p),
             dedans: cadrer(p.portrait_svg) +
               (p.titre ? '<i class="emb-coin" aria-hidden="true">' +
                 embleme(p.titre) + "</i>" : ""),
             nom: p.nom, titre: p.titre };
  }

  function ouvrir(src) {
    if (src === cible) return;
    const f = fiche(src);
    if (!f) { fermer(); return; }
    cible = src;
    // Une bulle à la fois : l'encart du plateau se pose au même endroit, et
    // deux fiches superposées ne se lisent ni l'une ni l'autre. Vaut même pour
    // une bulle retenue — elle est de toute façon recouverte.
    if (window.Echiquier && Echiquier.fermer) Echiquier.fermer();
    if (!boite) {
      boite = document.createElement("div");
      boite.className = "visage-fiche";
      document.body.appendChild(boite);
    }
    boite.innerHTML =
      '<span class="visage visage-grand" style="' +
      (f.role ? "--role:" + esc(f.role) + ";" : "") +
      "width:" + f.cote + "px;height:" + f.cote + 'px">' + f.dedans + "</span>" +
      (f.nom ? '<span class="visage-fiche-nom">' + esc(f.nom) +
        (f.titre ? "<small>" + esc(f.titre) + "</small>" : "") + "</span>" : "");
    // On se pose à côté, du côté où il y a la place, et l'on reste dans
    // l'écran : un visage tout en bas de la colonne — ou une tache dans le coin
    // du plan — ne doit pas sortir du cadre pour être vu.
    const r = src.getBoundingClientRect();
    const marge = 12;
    boite.classList.add("ouverte");
    const b = boite.getBoundingClientRect();
    let x = r.right + marge;
    if (x + b.width > window.innerWidth - marge) x = r.left - marge - b.width;
    if (x < marge) x = marge;
    let y = r.top + r.height / 2 - b.height / 2;
    y = Math.max(marge, Math.min(y, window.innerHeight - marge - b.height));
    boite.style.left = Math.round(x) + "px";
    boite.style.top = Math.round(y) + "px";
  }

  // `.tache-gens` : un homme sur une carte — le plan du château, la ville, le
  // champ. Tous passent par `taches.js`, donc un seul sélecteur les couvre.
  const SOURCES = ".visage,.tache-gens[data-id]";

  document.addEventListener("mouseover", (ev) => {
    if (!ev.target.closest) return;
    const src = ev.target.closest(SOURCES);
    if (src && !src.classList.contains("visage-nu") && !ev.target.closest(".visage-fiche")) {
      ouvrir(src);
    } else if (!ev.target.closest(".visage-fiche")) {
      fermer();
    }
  });
  // Le survol ne suffit pas : on quitte un visage en défilant, en cliquant, en
  // faisant glisser la carte ou en changeant d'onglet — et la fiche resterait
  // pendue à l'écran.
  ["scroll", "mousedown", "blur", "wheel"].forEach((t) =>
    window.addEventListener(t, fermer, true));

  return { html, cadrer, teinte, embleme, fermer };
})();
