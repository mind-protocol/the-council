// nappe.js — la toile blanche jetée sur la table peinte, et les pièces de bois
// qu'on y pousse à la main.
//
// C'est la seule échelle du décor que le MJ n'écrit pas. Toutes les autres
// rendent un état : la carte rend des jetons, le plan rend des salles, les
// livres rendent des feuillets. Ici, c'est le JOUEUR qui pose, écrit, déplace
// et retire — et rien de ce qu'il fait n'entre dans la partie. La nappe montre
// le plan ; les registres le tiennent. Quand les deux divergent, le registre a
// raison (voir « La boîte et la nappe » et « Comment on ouvre une affaire »).
//
// VISIBLE DANS UNE SEULE SALLE, et c'est le point. La boîte est sous la Table
// Peinte : on ne pousse pas des pièces depuis la roukerie ou depuis un quai.
// `dispo()` interroge donc la salle courante, et l'échelle disparaît d'elle-même
// dès que le joueur en sort — comme la toile qu'on replie en quittant la pièce.
//
// LA FORME AVANT LA COULEUR. Sept formes, reconnaissables à la silhouette : une
// tuile à huit côtés pour une affaire, un rectangle pour un état cible, un
// hexagone sombre pour un verrou, un losange pour une clef, une barrette pour
// une action, un rond pour un moyen, un carré épais pour un office. Ce sont les
// pièces réelles, taillées dans la nuit du 25e au 26e.
//
// AUCUNE PIÈCE POUR LES LIENS : ils se disent par la géométrie — ce qui est
// collé, ce qui est d'aplomb, ce qui est loin. Une maison qui fabrique des
// pièces pour ses liens finit par avoir plus de liens que de choses.
"use strict";
const Nappe = (() => {
  // RENDU COUPÉ. La nappe ne s'affiche plus : ni onglet dans le décor, ni toile,
  // ni établi. Le module reste en place et les routes serveur aussi — les pièces
  // posées dorment dans etat/nappe.json, rien n'est perdu, et remettre ACTIF à
  // true rallume tout sans autre geste.
  const ACTIF = false;
  const HOTE = "nappe";
  const SALLE = "table-peinte";     // la seule salle où la boîte est posée
  const L = 1600, H = 1000;         // la toile, en unités à elle

  let pieces = [];                  // ce qui est posé
  let charge = false;
  let sel = null;                   // la pièce qu'on tient
  let outil = "etat";               // ce qu'on posera au prochain clic à vide
  let vueLarge = false;
  let stock = [];                   // les pièces DÉJÀ ÉCRITES, prises aux livres
  let pret = null;                  // celle qu'on tient au-dessus de la toile
  let cherche = "";
  let affaires = [];                // {id, titre, plage} — où porter une pièce
  let brouillon = { affaire: "", parent: "", office: "", moyens: "" };
  let dit = "";                     // ce que le registre vient de répondre

  const FORMES = [
    { id: "affaire", nom: "Affaire",    l: 190, h: 58 },
    { id: "etat",    nom: "État cible", l: 200, h: 62 },
    { id: "verrou",  nom: "Verrou",     l: 190, h: 62 },
    { id: "clef",    nom: "Clef",       l: 210, h: 70 },
    { id: "action",  nom: "Action",     l: 200, h: 40 },
    { id: "moyen",   nom: "Moyen",      l: 76,  h: 76 },
    { id: "office",  nom: "Office",     l: 96,  h: 76 },
  ];
  const DEF = {};
  FORMES.forEach((f) => (DEF[f.id] = f));

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  // ---- le contour d'une pièce, dans son repère (centre 0,0) -----------------
  function contour(g) {
    const f = DEF[g] || DEF.etat, a = f.l / 2, b = f.h / 2;
    if (g === "affaire") {           // tuile : quatre coins coupés
      const c = 15;
      return "M" + (-a + c) + "," + -b + " H" + (a - c) + " L" + a + "," + (-b + c) +
             " V" + (b - c) + " L" + (a - c) + "," + b + " H" + (-a + c) +
             " L" + -a + "," + (b - c) + " V" + (-b + c) + " Z";
    }
    if (g === "verrou") {            // six pans
      return "M" + -a + ",0 L" + (-a + 24) + "," + -b + " H" + (a - 24) +
             " L" + a + ",0 L" + (a - 24) + "," + b + " H" + (-a + 24) + " Z";
    }
    if (g === "clef") {              // losange
      return "M0," + -b + " L" + a + ",0 L0," + b + " L" + -a + ",0 Z";
    }
    if (g === "moyen") {             // le seul galet de la boîte
      return "M" + -a + ",0 a" + a + "," + a + " 0 1,0 " + (2 * a) + ",0 a" +
             a + "," + a + " 0 1,0 " + (-2 * a) + ",0 Z";
    }
    // rectangle (état), barrette (action), carré épais (office)
    return "M" + -a + "," + -b + " H" + a + " V" + b + " H" + -a + " Z";
  }

  // ---- le dessin ------------------------------------------------------------
  function lignes(texte, n) {
    const mots = String(texte || "").split(/\s+/).filter(Boolean);
    const out = [];
    let cur = "";
    mots.forEach((m) => {
      if ((cur + " " + m).trim().length <= n) cur = (cur + " " + m).trim();
      else { if (cur) out.push(cur); cur = m; }
    });
    if (cur) out.push(cur);
    return out.slice(0, 3);
  }

  function unePiece(p, i) {
    const f = DEF[p.genre] || DEF.etat;
    const par = Math.max(8, Math.round(f.l / 11));
    const ls = lignes(p.texte, par);
    const dy = -((ls.length - 1) * 7);
    return '<g class="np np-' + esc(p.genre) + (sel === i ? " np-tenue" : "") +
      '" data-i="' + i + '" transform="translate(' + p.x + "," + p.y + ')">' +
      '<path class="np-corps" d="' + contour(p.genre) + '"/>' +
      ls.map((l, k) =>
        '<text class="np-texte" y="' + (dy + k * 14 + 4) + '">' + esc(l) + "</text>").join("") +
      (p.texte ? "" : '<text class="np-vide" y="4">' + esc(f.nom) + "</text>") +
      "</g>";
  }

  function svg(grand) {
    return '<svg viewBox="0 0 ' + L + " " + H + '" class="np-toile' +
      (grand ? " np-grande" : "") + '" preserveAspectRatio="xMidYMid meet">' +
      '<rect class="np-fond" width="' + L + '" height="' + H + '"/>' +
      // les deux bords à la craie : l'inventaire à gauche, les charges à droite
      '<line class="np-craie" x1="230" y1="24" x2="230" y2="' + (H - 24) + '"/>' +
      '<line class="np-craie" x1="' + (L - 230) + '" y1="24" x2="' + (L - 230) +
        '" y2="' + (H - 24) + '"/>' +
      '<text class="np-bord" x="34" y="44">LES MOYENS</text>' +
      '<text class="np-bord" x="' + (L - 208) + '" y="44">LES OFFICES</text>' +
      pieces.map(unePiece).join("") + "</svg>";
  }

  function barre() {
    return '<div class="np-barre">' +
      FORMES.map((f) => '<button class="np-outil' + (outil === f.id ? " actif" : "") +
        '" data-outil="' + f.id + '" title="Poser : ' + f.nom + '">' +
        '<svg viewBox="-110 -45 220 90"><path d="' + contour(f.id) +
        '" transform="scale(' + (f.id === "moyen" || f.id === "office" ? 0.9 : 0.52) +
        ')"/></svg></button>').join("") +
      '<span class="np-aide">Prendre une pi\u00e8ce \u00e9crite \u00e0 gauche, ou une forme vierge ici \u00b7 ' +
      'cliquer la toile pour poser \u00b7 glisser \u00b7 double-cliquer pour \u00e9crire \u00b7 ' +
      '<b>Suppr</b> pour retirer</span>' +
      '<button class="np-vider" title="Tout retirer de la toile">Replier la nappe</button>' +
      "</div>";
  }

  // ---- ce qui est DÉJÀ ÉCRIT ------------------------------------------------
  // Une pièce vierge est une pièce qu'on va recopier à la main, et une pièce
  // recopiée à la main diverge du registre le jour même. On prend donc le stock
  // là où il est tenu : les affaires et les registres. La toile ne crée rien,
  // elle DISPOSE ce qui existe.
  const GENRE_TABLE = [
    [/états?\s+cibles?/i, "etat"], [/verrous?/i, "verrou"], [/clefs?/i, "clef"],
    [/actions?/i, "action"], [/moyens?/i, "moyen"], [/offices?/i, "office"],
  ];
  const nu = (t) => String(t == null ? "" : t).replace(/\*\*/g, "")
    .replace(/[\u3000\u2514]/g, " ").replace(/\s+/g, " ").trim();

  function catalogue(livres) {
    const out = [];
    affaires = [];
    (livres || []).forEach((b) => {
      const tables = Array.isArray(b.tables) && b.tables.length ? b.tables
        : [{ titre: b.titre, colonnes: b.colonnes, lignes: b.lignes }];
      tables.forEach((t) => {
        const trouve = GENRE_TABLE.find((x) => x[0].test(nu(t.titre)))
                    || GENRE_TABLE.find((x) => x[0].test(nu(b.titre)));
        if (!trouve) return;
        const g = trouve[1];
        (t.lignes || []).forEach((l) => {
          const c = (Array.isArray(l) ? l : (l.cellules || [])).map(nu);
          if (c.length < 2) return;
          const num = c[0], nom = c[1];
          if (!num || !nom) return;
          out.push({ genre: g, num: num, nom: nom, ou: nu(b.titre),
                     texte: (num + " " + nom).trim() });
        });
      });
      // l'affaire elle-même : son nom vaut une tuile, et c'est un endroit où
      // porter une pièce — à condition qu'elle ait une plage
      if (Array.isArray(b.tables) && b.tables.length &&
          /ouverture/i.test(nu(b.tables[0].titre))) {
        let plage = "";
        (b.tables[0].lignes || []).forEach((l) => {
          const c = ((l.cellules) || []).map(nu);
          if (/LA PLAGE/i.test(c[0] || "")) plage = (c[1] || "").match(/\d{3,6}/) ?
            (c[1] || "").match(/\d{3,6}/)[0] : "";
        });
        // repli sur le sous-titre : un cahier vierge y porte sa plage, la case
        // de l'ouverture ne se remplit qu'au moment où l'affaire s'ouvre
        if (!plage) {
          const m = String(b.sous_titre || "").match(/[Pp]lage\s+(\d{3,6})/);
          if (m) plage = m[1];
        }
        if (plage) affaires.push({ id: b.id, titre: nu(b.titre), plage: plage });
        const l = (b.tables[0].lignes || [])[0];
        const c = l ? (Array.isArray(l) ? l : (l.cellules || [])).map(nu) : [];
        if (c[1]) out.push({ genre: "affaire", num: "", nom: nu(b.titre),
                             ou: "affaire", texte: nu(b.titre) });
      }
    });
    return out;
  }

  function stockVu() {
    const q = cherche.toLowerCase();
    const vus = stock.filter((p) => !q ||
      (p.texte + " " + p.ou).toLowerCase().indexOf(q) >= 0);
    if (!vus.length) {
      return '<p class="np-rien">' + (stock.length
        ? "Rien de ce nom dans les livres."
        : "Aucune pi\u00e8ce \u00e9crite : les affaires sont vides.") + "</p>";
    }
    const ordre = ["affaire", "etat", "verrou", "clef", "action", "moyen", "office"];
    return ordre.map((g) => {
      const l = vus.filter((p) => p.genre === g);
      if (!l.length) return "";
      return '<div class="np-groupe">' + esc((DEF[g] || {}).nom || g) + "</div>" +
        l.map((p) => {
          const i = stock.indexOf(p);
          return '<button class="np-stock np-s-' + g +
            (pret === i ? " pret" : "") + '" data-s="' + i + '" title="' +
            esc(p.ou) + '"><b>' + esc(p.num) + "</b> " + esc(p.nom) + "</button>";
        }).join("");
    }).join("");
  }


  // ---- porter au registre ---------------------------------------------------
  // La craie ne compte pas. Tant qu'une pièce n'est pas au registre, elle n'a pas
  // de numéro, personne ne peut la citer, et elle disparaîtra au premier coup
  // d'éponge. Ce panneau est le seul endroit d'où la toile ÉCRIT dans les livres.
  const PORTABLE = { etat: 1, verrou: 1, clef: 1, action: 1 };
  const PARENT_DIT = { etat: "Sert l'état (facultatif)", verrou: "Bloque l'état n°",
                       clef: "Ouvre le verrou n°", action: "Réalise la clef n°" };

  function aNumero(t) { return /^\s*\**\s*\d{3,6}\b/.test(String(t || "")); }

  function panneau() {
    if (sel == null || !pieces[sel]) return "";
    const p = pieces[sel];
    if (!PORTABLE[p.genre]) {
      return '<div class="np-porter np-porter-non">Un moyen et un office ne se ' +
        'cr\u00e9ent pas dans une affaire : ils vivent dans leur registre, on les cite.</div>';
    }
    if (!nu(p.texte)) {
      return '<div class="np-porter np-porter-non">\u00c9crivez d\u2019abord ce ' +
        'qu\u2019elle dit \u2014 double-clic sur la pi\u00e8ce.</div>';
    }
    if (aNumero(p.texte)) {
      return '<div class="np-porter np-porter-non">D\u00e9j\u00e0 au registre.' +
        (dit ? ' <b>' + esc(dit) + '</b>' : '') + '</div>';
    }
    return '<div class="np-porter">' +
      '<span class="np-p-quoi">Porter au registre \u00b7 <b>' +
        esc((DEF[p.genre] || {}).nom) + '</b></span>' +
      '<select class="np-p-affaire"><option value="">\u2014 quelle affaire \u2014</option>' +
      affaires.map((a) => '<option value="' + esc(a.id) + '"' +
        (brouillon.affaire === a.id ? " selected" : "") + '>' + esc(a.titre) +
        " (" + esc(a.plage) + ")</option>").join("") + "</select>" +
      '<input class="np-p-parent" placeholder="' + esc(PARENT_DIT[p.genre]) +
        '" value="' + esc(brouillon.parent) + '">' +
      (p.genre === "action" ?
        '<input class="np-p-office" placeholder="Office O__" value="' + esc(brouillon.office) + '">' +
        '<input class="np-p-moyens" placeholder="Moyens M__ \u00b7 M__" value="' +
          esc(brouillon.moyens) + '">' : "") +
      '<button class="np-p-ok">Porter</button>' +
      (dit ? '<span class="np-p-dit">' + esc(dit) + "</span>" : "") + "</div>";
  }

  function porter(hote) {
    const p = pieces[sel];
    if (!p) return;
    dit = "";
    fetch("/piece", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ affaire: brouillon.affaire, genre: p.genre,
        texte: p.texte, parent: brouillon.parent.replace(/\D/g, ""),
        office: brouillon.office, moyens: brouillon.moyens }) })
      .then((r) => r.json())
      .then((d) => {
        if (d.erreur) { dit = d.erreur; poser(hote, true); return; }
        p.texte = d.num + " " + p.texte;
        dit = "Port\u00e9e sous " + d.num + " dans \u00ab " + d.affaire + " \u00bb.";
        brouillon = { affaire: brouillon.affaire, parent: "", office: "", moyens: "" };
        garder();
        relireLivres();
        poser(hote, true);
      })
      .catch((e) => { dit = String(e); poser(hote, true); });
  }

  // ---- où le clic tombe, en unités de la toile ------------------------------
  // La toile, et JAMAIS un pictogramme de la barre d'outils : celle-ci porte
  // sept <svg> qui viennent AVANT dans le document, et un querySelector("svg")
  // nu les attrape en premier. Le bug ne se voit pas — les écouteurs se posent,
  // ils ne répondent simplement jamais.
  const toileDe = (el) => el.querySelector("svg.np-toile");

  function point(el, ev) {
    const s = el.matches && el.matches("svg.np-toile") ? el : toileDe(el);
    const r = s.getBoundingClientRect();
    // la toile garde son rapport : on retrouve la boîte réellement dessinée
    const k = Math.min(r.width / L, r.height / H);
    const ox = (r.width - L * k) / 2, oy = (r.height - H * k) / 2;
    return [Math.round((ev.clientX - r.left - ox) / k),
            Math.round((ev.clientY - r.top - oy) / k)];
  }

  // ---- garder ---------------------------------------------------------------
  let prevu = null;
  function garder() {
    if (prevu) clearTimeout(prevu);
    prevu = setTimeout(() => {
      prevu = null;
      fetch("/nappe", { method: "POST", headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ pieces }) }).catch(() => {});
    }, 300);
  }

  // ---- les gestes -----------------------------------------------------------
  function poser(hote, grand) {
    hote.innerHTML = (grand ? barre() + panneau() : "") +
      (grand ? '<div class="np-corps-large"><div class="np-stocks">' +
        '<input class="np-cherche" placeholder="Chercher dans les livres\u2026" value="' +
        esc(cherche) + '">' + stockVu() + "</div>" : "") +
      svg(grand) + (grand ? "</div>" : "") +
      (grand ? "" : '<button class="np-deplier" title="Ouvrir la nappe">Ouvrir la nappe</button>');
    const s = toileDe(hote);

    if (!grand) {
      const b = hote.querySelector(".np-deplier");
      if (b) b.onclick = (e) => { e.stopPropagation(); ouvrir(); };
      s.onclick = ouvrir;
      return;
    }

    hote.querySelectorAll(".np-outil").forEach((b) => {
      b.onclick = () => { outil = b.dataset.outil; pret = null; poser(hote, true); };
    });
    // Une pi\u00e8ce du stock qu'on prend : elle attend au-dessus de la toile, et le
    // prochain clic la pose l\u00e0 o\u00f9 le doigt tombe.
    hote.querySelectorAll(".np-stock").forEach((b) => {
      b.onclick = () => {
        const i = +b.dataset.s;
        pret = (pret === i) ? null : i;
        if (pret != null) outil = stock[pret].genre;
        poser(hote, true);
      };
    });
    const lier = (cls, clef) => {
      const e = hote.querySelector(cls);
      if (!e) return;
      e.onchange = e.oninput = () => { brouillon[clef] = e.value; };
    };
    lier(".np-p-affaire", "affaire");
    lier(".np-p-parent", "parent");
    lier(".np-p-office", "office");
    lier(".np-p-moyens", "moyens");
    const ok = hote.querySelector(".np-p-ok");
    if (ok) ok.onclick = () => porter(hote);

    const ch = hote.querySelector(".np-cherche");
    if (ch) {
      ch.oninput = () => {
        const pos = ch.selectionStart;
        cherche = ch.value;
        poser(hote, true);
        const n = hote.querySelector(".np-cherche");
        if (n) { n.focus(); n.setSelectionRange(pos, pos); }
      };
    }
    hote.querySelector(".np-vider").onclick = () => {
      if (!pieces.length) return;
      pieces = []; sel = null; garder(); poser(hote, true);
    };

    let tient = null, decal = [0, 0], bouge = false;

    s.addEventListener("pointerdown", (ev) => {
      const g = ev.target.closest(".np");
      const p = point(s, ev);
      if (g) {
        const avant = sel;
        tient = +g.dataset.i;
        sel = tient;
        if (avant !== sel) { dit = ""; }
        decal = [pieces[tient].x - p[0], pieces[tient].y - p[1]];
        bouge = false;
        try { s.setPointerCapture(ev.pointerId); } catch (e) {}
        redessiner(hote);
        majPanneau(hote);
        return;
      }
      // la toile nue : on pose. Si l'on tenait une pièce écrite, c'est elle qui
      // tombe avec son texte ; sinon c'est une forme vierge.
      const q = pret != null ? stock[pret] : null;
      pieces.push({ genre: q ? q.genre : outil, x: p[0], y: p[1],
                    texte: q ? q.texte : "" });
      if (q) { pret = null; sel = pieces.length - 1; garder(); poser(hote, true); return; }
      dit = "";
      sel = pieces.length - 1;
      tient = sel; decal = [0, 0]; bouge = false;
      try { s.setPointerCapture(ev.pointerId); } catch (e) {}
      redessiner(hote);
      majPanneau(hote);
      garder();
    });

    s.addEventListener("pointermove", (ev) => {
      if (tient == null) return;
      const p = point(s, ev);
      pieces[tient].x = Math.max(20, Math.min(L - 20, p[0] + decal[0]));
      pieces[tient].y = Math.max(20, Math.min(H - 20, p[1] + decal[1]));
      bouge = true;
      redessiner(hote);
    });

    const lacher = () => { if (tient != null && bouge) garder(); tient = null; };
    s.addEventListener("pointerup", lacher);
    s.addEventListener("pointercancel", lacher);

    s.addEventListener("dblclick", (ev) => {
      const g = ev.target.closest(".np");
      if (!g) return;
      const i = +g.dataset.i;
      const t = window.prompt("Ce qui est écrit à la craie sur cette pièce :",
                              pieces[i].texte || "");
      if (t === null) return;
      pieces[i].texte = t;
      redessiner(hote);
      majPanneau(hote);
      garder();
    });
  }

  // Redessiner sans reposer les écouteurs : on remplace le contenu du <svg>,
  // pas le <svg> — sinon la capture du pointeur se perd au premier mouvement.
  // On remplace le seul panneau : refaire toute la vue perdrait la capture du
  // pointeur au milieu d'un glissé, et le champ de recherche son curseur.
  function majPanneau(hote) {
    const vieux = hote.querySelector(".np-porter");
    const html = panneau();
    if (!vieux && !html) return;
    const boite = document.createElement("div");
    boite.innerHTML = html;
    const neuf = boite.firstElementChild;
    if (vieux && neuf) vieux.replaceWith(neuf);
    else if (vieux) vieux.remove();
    else if (neuf) hote.querySelector(".np-barre").after(neuf);
    const ok = hote.querySelector(".np-p-ok");
    if (ok) ok.onclick = () => porter(hote);
    const lier = (cls, clef) => {
      const e = hote.querySelector(cls);
      if (e) e.onchange = e.oninput = () => { brouillon[clef] = e.value; };
    };
    lier(".np-p-affaire", "affaire");
    lier(".np-p-parent", "parent");
    lier(".np-p-office", "office");
    lier(".np-p-moyens", "moyens");
  }

  function redessiner(hote) {
    const s = toileDe(hote);
    if (!s) return;
    const fixe = s.querySelectorAll(".np-fond, .np-craie, .np-bord");
    s.innerHTML = Array.from(fixe).map((n) => n.outerHTML).join("") +
      pieces.map(unePiece).join("");
  }

  function toucheClavier(ev) {
    if (!vueLarge || sel == null) return;
    if (ev.key !== "Delete" && ev.key !== "Backspace") return;
    const a = document.activeElement;
    if (a && (a.tagName === "INPUT" || a.tagName === "TEXTAREA" || a.isContentEditable)) return;
    ev.preventDefault();
    pieces.splice(sel, 1);
    sel = null;
    const ov = document.getElementById("nappe-large");
    if (ov) redessiner(ov.querySelector(".np-cadre"));
    garder();
  }

  // ---- la grande toile ------------------------------------------------------
  function ouvrir() {
    if (!ACTIF) return;
    let ov = document.getElementById("nappe-large");
    if (!ov) {
      ov = document.createElement("div");
      ov.id = "nappe-large";
      ov.innerHTML = '<div class="np-cadre"></div>';
      ov.addEventListener("click", (e) => { if (e.target === ov) fermer(); });
      document.body.appendChild(ov);
    }
    ov.hidden = false;
    vueLarge = true;
    poser(ov.querySelector(".np-cadre"), true);
  }
  function fermer() {
    const ov = document.getElementById("nappe-large");
    if (ov) ov.hidden = true;
    vueLarge = false;
    dessiner();
  }
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && vueLarge) fermer();
    else toucheClavier(ev);
  });

  function dessiner() {
    if (!ACTIF) return;
    const hote = document.getElementById(HOTE);
    if (!hote) return;
    poser(hote, false);
  }

  function ici() {
    return window.Plan && Plan.salle && Plan.salle() === SALLE;
  }

  function relireLivres() {
    fetch("/books").then((r) => r.json()).then((d) => {
      stock = catalogue(d.books || []);
      if (vueLarge) {
        const ov = document.getElementById("nappe-large");
        if (ov) poser(ov.querySelector(".np-cadre"), true);
      }
    }).catch(() => {});
  }

  function relire() {
    fetch("/nappe").then((r) => r.json()).then((d) => {
      pieces = Array.isArray(d.pieces) ? d.pieces : [];
      charge = true;
      if (!vueLarge) dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
    }).catch(() => { charge = true; });
  }

  window.addEventListener("DOMContentLoaded", () => {
    if (!ACTIF) return;
    relire();
    relireLivres();
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "nappe", nom: "La nappe", hote: HOTE, ordre: 0.4,
        // La boîte est sous la Table Peinte : ailleurs, il n'y a pas de nappe à
        // déplier, et l'onglet n'a pas à proposer ce qu'on ne peut pas faire.
        dispo: () => ici(),
        reparu: () => dessiner(),
      });
    }
    // La salle change sans prévenir personne : on la suit de loin pour que
    // l'onglet apparaisse en entrant et disparaisse en sortant.
    let vue = null;
    setInterval(() => {
      const s = window.Plan && Plan.salle ? Plan.salle() : null;
      if (s === vue) return;
      vue = s;
      if (window.Plan && Plan.rebattre) Plan.rebattre();
      if (!ici() && vueLarge) fermer();
    }, 700);
  });

  return { relire, relireLivres, ouvrir, fermer, dessiner };
})();
