// LES CHAMBRES — l'onglet de débogage du modèle habitant.
//
// PAS UN GRAPHE, ET C'EST UNE MESURE. 122 chambres, 60 canaux, et `mj` en
// touche 46 : la topologie est une ÉTOILE. Un force-directed rendrait un moyeu
// et des rayons. Ce qu'on ne voit nulle part ailleurs, c'est le FAN-OUT d'un
// réveil et la LATENCE d'un échange — deux choses qui vivent sur un axe de
// temps réel. D'où une frise.
//
// EN DOM, PAS EN CANVAS, ET C'EST LA CORRECTION DU 31.8. Le premier jet
// peignait des points sur une toile : le survol, les emojis, les portraits et
// le texte riche y sont tous coûteux, et le zoom à la molette y était
// capricieux. Cinquante-six lignes ne justifiaient jamais un canvas. On choisit
// le support d'après les INTERACTIONS voulues, pas d'après le volume.
//
// UNE SESSION EST UN CONTAINER, PAS UN POINT. Un rapport porte ses activités :
// la boîte les contient, une case par acte, avec son emoji et son détail au
// survol.
//
// PAS D'AXE DE TEMPS — UN ORDRE, ET IL SUFFIT. La frise à l'échelle du temps
// réel était une fausse bonne idée : vingt et un jours d'histoire pour trois
// rafales donnent une vue vide neuf fois sur dix, il faut zoomer pour trouver
// quoi que ce soit, et le zoom devient l'interface. On ne débogue pas avec une
// loupe. Chaque piste est donc une SUITE, la plus récente à gauche, sans
// échelle : tout est visible au chargement, rien ne se cherche. La date exacte
// reste au survol, là où elle sert — et nulle part ailleurs.
(function () {
  "use strict";

  var S = null;
  var choisie = null;
  var GAUCHE = 236;

  // LES SEPT FAMILLES DE GESTES (docs/habitant.md). Ce qu'on cherche à l'œil
  // n'est pas ce qui bat : c'est ce qui NE BAT JAMAIS.
  var FAM = {
    percevoir: { c: "#c8a24a", e: "◈", n: "percevoir" },
    lire:      { c: "#6f9bd1", e: "▤", n: "lire" },
    ecrire:    { c: "#7fb18c", e: "✎", n: "écrire chez lui" },
    verbe:     { c: "#e0bd58", e: "▲", n: "les 3 verbes" },
    parler:    { c: "#c8bfb3", e: "●", n: "parler" },
    conclure:  { c: "#b98cc0", e: "◆", n: "conclure" },
    subi:      { c: "#8a7659", e: "·", n: "subi" }
  };
  var ORDRE = ["percevoir", "lire", "ecrire", "verbe", "parler", "conclure",
               "subi"];

  function esc(x) {
    return String(x == null ? "" : x).replace(/[<>&"]/g, function (c) {
      return { "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c];
    });
  }
  function quand(t) {
    return new Date(t).toLocaleString("fr-FR").slice(0, 16);
  }

  function css() {
    if (document.getElementById("style-chambres")) return;
    var e = document.createElement("style");
    e.id = "style-chambres";
    // ON PARLE LA LANGUE DE LA REGIE : ses variables (--or, --fond, --bord,
    // --pale) et sa serif. Le premier jet peignait des hex approchants a cote
    // de la palette — proches mais faux, ce qui se voit plus qu'une couleur
    // franchement autre.
    e.textContent = [
      "#chambres{margin:-1.2rem;height:calc(100vh - 112px);min-height:640px;",
      "  display:grid;grid-template-columns:236px 1fr 360px;overflow:hidden;",
      "  background:var(--fond)}",
      ".ch-col{overflow:auto;padding:1rem .9rem;background:var(--fond)}",
      ".ch-col:first-child{border-right:1px solid var(--bord)}",
      ".ch-col:last-child{border-left:1px solid var(--bord);background:var(--fond2)}",
      ".ch-tete{font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;",
      "  color:var(--or);margin:0 0 .9rem;padding-bottom:.5rem;",
      "  border-bottom:1px solid var(--bord)}",
      /* la colonne des salles */
      ".ch-salle{margin-bottom:1rem}",
      ".ch-salle b{display:block;font-size:.86rem;color:var(--texte);",
      "  font-weight:normal;line-height:1.3}",
      ".ch-salle span{font:.66rem ui-monospace,monospace;color:var(--pale);",
      "  opacity:.7}",
      ".ch-gens{display:flex;flex-wrap:wrap;gap:4px;margin-top:.4rem}",
      ".ch-g{font:.64rem ui-monospace,monospace;padding:.16em .45em;",
      "  border-radius:3px;border:1px solid var(--bord);color:var(--pale);",
      "  cursor:pointer;transition:border-color .15s,color .15s}",
      ".ch-g:hover{border-color:var(--or);color:var(--texte)}",
      ".ch-g.a{border-color:#5c4a2a;color:var(--texte)}",
      /* la scene */
      ".ch-scene{display:flex;flex-direction:column;overflow:hidden}",
      ".ch-pistes{flex:1;overflow-y:auto;overflow-x:hidden}",
      ".ch-piste{display:grid;grid-template-columns:" + GAUCHE + "px 1fr;",
      "  align-items:center;height:48px;border-bottom:1px solid rgba(58,49,40,.4)}",
      ".ch-piste:nth-child(even){background:rgba(28,24,21,.45)}",
      ".ch-piste.pale{opacity:.3}",
      ".ch-piste.pale img.ch-visage{filter:grayscale(1)}",
      ".ch-piste:hover{background:rgba(200,164,74,.06)}",
      /* le nom et son visage */
      ".ch-qui{display:flex;align-items:center;gap:9px;padding:0 12px;",
      "  cursor:pointer;overflow:hidden;height:100%}",
      "img.ch-visage{width:38px;height:38px;flex:0 0 38px;border-radius:50%;",
      "  object-fit:cover;display:block;background:var(--fond2);",
      "  border:1px solid var(--bord);box-shadow:0 1px 3px rgba(0,0,0,.5);",
      "  transition:border-color .15s}",
      ".ch-qui:hover img.ch-visage{border-color:var(--or)}",
      ".ch-ident{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1}",
      ".ch-nom{font-size:.84rem;color:var(--texte);white-space:nowrap;",
      "  overflow:hidden;text-overflow:ellipsis}",
      ".ch-piste.zone .ch-nom{color:var(--or);letter-spacing:.04em}",
      ".ch-fams{display:flex;gap:2px}",
      ".ch-fam{width:13px;height:6px;border-radius:3px;cursor:help;",
      "  transition:transform .12s}",
      ".ch-fam:hover{transform:scaleY(1.9)}",
      /* le couloir : une suite, le plus recent a gauche */
      ".ch-lane{display:flex;align-items:center;gap:5px;height:100%;min-width:0;",
      "  overflow-x:auto;overflow-y:hidden;padding:0 10px;scrollbar-width:thin;",
      "  -webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 34px),transparent);",
      "  mask-image:linear-gradient(90deg,#000 calc(100% - 34px),transparent)}",
      // AUCUNE BARRE DE DEFILEMENT VISIBLE. Ce qui dit qu on peut faire
      // defiler, c est le degrade de bord du couloir — pas une glissiere
      // grise heritee du systeme. Le defilement lui-meme reste entier :
      // molette, pave tactile, clavier.
      ".ch-lane,.ch-pistes,.ch-col{scrollbar-width:none;",
      "  -ms-overflow-style:none}",
      ".ch-lane::-webkit-scrollbar,.ch-pistes::-webkit-scrollbar,",
      ".ch-col::-webkit-scrollbar,.ch-cahier::-webkit-scrollbar",
      "{width:0;height:0;display:none}",
      ".ch-cahier{scrollbar-width:none}",
      /* le container d'une session */
      ".ch-sess{display:flex;align-items:center;flex:0 0 auto;height:34px;",
      "  border:1px solid rgba(200,164,74,.45);border-radius:7px;",
      "  background:linear-gradient(180deg,rgba(200,164,74,.18),rgba(200,164,74,.07));",
      "  box-shadow:inset 0 1px 0 rgba(255,225,160,.12),0 1px 3px rgba(0,0,0,.45);",
      "  cursor:pointer;padding:0 4px;gap:2px;transition:transform .12s,",
      "  border-color .12s,box-shadow .12s}",
      ".ch-sess:hover{border-color:var(--or);transform:translateY(-1px);",
      "  box-shadow:inset 0 1px 0 rgba(255,225,160,.2),0 3px 8px rgba(0,0,0,.55)}",
      ".ch-sess.echoue{border-color:rgba(192,90,68,.55);",
      "  background:linear-gradient(180deg,rgba(192,90,68,.2),rgba(192,90,68,.07))}",
      ".ch-sess.echoue:hover{border-color:var(--rouge)}",
      ".ch-acte{display:flex;align-items:center;justify-content:center;",
      "  width:28px;height:28px;font-size:19px;line-height:1;cursor:help;",
      "  border-radius:5px;flex:0 0 auto;transition:background .12s}",
      ".ch-acte:hover{background:rgba(200,164,74,.3)}",
      /* les paroles */
      ".ch-mot{width:8px;height:8px;border-radius:50%;background:var(--pale);",
      "  opacity:.45;cursor:help;flex:0 0 auto;transition:opacity .12s,",
      "  transform .12s}",
      ".ch-mot:hover{opacity:1;transform:scale(1.5)}",
      ".ch-mot.verbe{background:var(--or);opacity:1;width:13px;height:13px;",
      "  box-shadow:0 0 0 2px rgba(200,164,74,.2)}",
      ".ch-reste{font:.68rem ui-monospace,monospace;color:var(--pale);",
      "  opacity:.55;padding:0 6px;cursor:help;flex:0 0 auto}",
      /* le bandeau */
      ".ch-bandeau{flex:0 0 auto;padding:.5rem .9rem;background:var(--fond2);",
      "  border-top:1px solid var(--bord);font-size:.72rem;color:var(--pale);",
      "  line-height:1.9}",
      ".ch-bandeau b{color:var(--texte);font-family:ui-monospace,monospace}",
      ".ch-leg{display:inline-block;padding:.1em .5em;margin-right:.3em;",
      "  border-radius:10px;border:1px solid var(--bord)}",
      /* le panneau de droite */
      ".ch-vide{padding:2.5rem 1rem;color:var(--pale);text-align:center;",
      "  font-style:italic}",
      ".ch-fiche h3{margin:0 0 .15rem;font-size:1.2rem;color:var(--texte);",
      "  font-weight:normal}",
      ".ch-fiche .ch-sous{font:.68rem ui-monospace,monospace;color:var(--pale);",
      "  margin-bottom:1rem}",
      ".ch-bloc{margin:.9rem 0;padding:.7rem .8rem;border:1px solid var(--bord);",
      "  border-radius:5px;background:var(--fond)}",
      ".ch-bloc h4{margin:0 0 .5rem;font-size:.64rem;letter-spacing:.14em;",
      "  text-transform:uppercase;color:var(--or);font-weight:normal}",
      ".ch-bloc li{font-size:.8rem;color:var(--texte);margin-bottom:.4rem;",
      "  line-height:1.5}",
      ".ch-bloc ul{margin:0;padding-left:1.1em}",
      ".ch-cahier{white-space:pre-wrap;font-size:.76rem;color:var(--texte);",
      "  max-height:260px;overflow:auto;line-height:1.55;opacity:.9}",
      ".ch-marque{display:inline-block;font:.62rem ui-monospace,monospace;",
      "  padding:.15em .5em;border-radius:10px;border:1px solid currentColor}",
      /* L'INFOBULLE — pas celle du systeme. `title=` rend une ligne grise
         apres une seconde d'attente, sans mise en forme et sans structure :
         on ne peut y montrer ni un titre, ni un chiffre aligne, ni un extrait.
         Celle-ci parait tout de suite, suit le curseur, et porte de vraies
         lignes. */
      ".ch-bulle{position:fixed;z-index:60;max-width:430px;pointer-events:none;",
      "  background:linear-gradient(180deg,#221d17,#191512);color:var(--texte);",
      "  border:1px solid var(--or);border-radius:7px;padding:.6rem .75rem;",
      "  box-shadow:0 8px 26px rgba(0,0,0,.7);font-size:.78rem;line-height:1.5;",
      "  opacity:0;transition:opacity .1s}",
      ".ch-bulle.vu{opacity:1}",
      ".ch-bulle h5{margin:0 0 .35rem;font-size:.9rem;color:var(--or);",
      "  font-weight:normal;display:flex;align-items:center;gap:.4rem}",
      ".ch-bulle .cl{display:grid;grid-template-columns:auto 1fr;gap:.1rem .7rem;",
      "  font:.7rem/1.6 ui-monospace,monospace;color:var(--pale);",
      "  margin-bottom:.4rem}",
      ".ch-bulle .cl b{color:var(--texte);font-weight:normal}",
      ".ch-bulle .txt{color:var(--texte);opacity:.92;border-top:1px solid ",
      "  var(--bord);padding-top:.4rem;margin-top:.1rem}",
      ".ch-bulle h5 .ff{color:var(--pale);font-size:.72rem;font-weight:normal}",
      ".ch-bulle .txt.sort{border-left:2px solid var(--or);padding-left:.5rem;",
      "border-top:none;margin-top:.4rem;opacity:.8;font-style:italic}",
      ".ch-bulle .pied{margin-top:.45rem;font-size:.66rem;color:var(--pale);",
      "  opacity:.7;font-style:italic}",
      ".cl2{display:grid;grid-template-columns:auto 1fr;gap:.15rem .7rem;",
      "  font:.7rem/1.6 ui-monospace,monospace;color:var(--pale)}",
      ".cl2 b{color:var(--texte);font-weight:normal;word-break:break-all}",
      ".ch-champ{margin:.4rem 0 0;font-size:.75rem;color:var(--texte);",
      "  line-height:1.5;opacity:.9}",
      ".ch-champ i{color:var(--or);font-style:normal;font-size:.62rem;",
      "  letter-spacing:.1em;text-transform:uppercase;margin-right:.35em}",
      ".ch-champ s{color:var(--pale);opacity:.65}",
      ".ch-bloc.vise{border-color:var(--or);",
      "  box-shadow:0 0 0 1px rgba(200,164,74,.3)}",
      ".ch-oui{color:var(--vert)}.ch-non{color:var(--orange)}"
    ].join("");
    document.head.appendChild(e);
  }

  // L'INFOBULLE : un seul noeud, deplace et rempli. On ne recree rien, et
  // rien n'intercepte la souris (pointer-events:none) — une bulle qui vole le
  // curseur fait clignoter ce qu'elle decrit.
  var bulle = null;
  function bulleDe(html, ev) {
    if (!bulle) {
      bulle = document.createElement("div");
      bulle.className = "ch-bulle";
      document.body.appendChild(bulle);
    }
    bulle.innerHTML = html;
    bulle.classList.add("vu");
    var b = bulle.getBoundingClientRect();
    var x = ev.clientX + 16, y = ev.clientY + 14;
    if (x + b.width > window.innerWidth - 8) x = ev.clientX - b.width - 16;
    if (y + b.height > window.innerHeight - 8) y = ev.clientY - b.height - 14;
    bulle.style.left = Math.max(6, x) + "px";
    bulle.style.top = Math.max(6, y) + "px";
  }
  function cacherBulle() { if (bulle) bulle.classList.remove("vu"); }

  // UNE REF EST UN NOM QUALIFIE : `salle:passages-maegor`, `pers:larys`,
  // `res:act:larys:1:1`. La bulle sert le nom, et le genre en petit — un id
  // brut oblige le lecteur a decoder, ce qui est le contraire d'un survol.
  var GENRE = { salle: "salle", pers: "qqun", lieu: "lieu", res: "ce qu'il a tire",
                act: "un pas", pli: "un pli", livre: "un livre" };
  function nommer(ref) {
    var r = String(ref == null ? "" : ref);
    var i = r.indexOf(":");
    if (i < 0) return { genre: null, nom: r };
    return { genre: GENRE[r.slice(0, i)] || r.slice(0, i),
             nom: r.slice(i + 1).replace(/-/g, " ") };
  }
  function refs(liste, avecMode) {
    return (liste || []).map(function (x) {
      var r = nommer(x && x.ref != null ? x.ref : x);
      var q = avecMode && x && x.mode ? x.mode
            : (r.genre && r.genre !== "salle" ? r.genre : null);
      return r.nom + (q ? " (" + q + ")" : "");
    }).join(", ");
  }
  var LIEUX = { salle: 1, lieu: 1 };
  // Le monde compte en secondes. Un survol veut des minutes et un rang.
  function duree(sec) {
    var s = Math.round(sec || 0);
    if (s < 60) return s + " s";
    var m = Math.floor(s / 60);
    return m + " min" + (s % 60 ? " " + (s % 60) + " s" : "");
  }

  var MOTS = [];   // les paroles rendues, dans l'ordre de la frise

  function couples(paires) {
    return '<div class="cl">' + paires.filter(Boolean).map(function (p) {
      return "<span>" + esc(p[0]) + "</span><b>" + esc(p[1]) + "</b>";
    }).join("") + "</div>";
  }

  function poser() {
    document.getElementById("chambres").innerHTML =
      '<div class="ch-col" id="ch-salles"></div>' +
      '<div class="ch-scene">' +
      '<div class="ch-pistes" id="ch-pistes"></div>' +
      '<div class="ch-bandeau" id="ch-bandeau"></div></div>' +
      '<div class="ch-col" id="ch-fiche"><div class="ch-vide">' +
      "Touche une ligne pour ouvrir la chambre.</div></div>";
  }

  function rendrePistes() {
    // TOUT SE RANGE PAR PAIRE (quand, quoi) ET SE SERT DANS L'ORDRE, le plus
    // recent d'abord. Pas d'echelle : la position ne dit que le RANG, et le
    // rang suffit a deboguer — la date exacte est au survol.
    var parQui = {};
    function poserChez(qui, item) {
      if (!qui) return;
      (parQui[qui] = parQui[qui] || []).push(item);
    }
    (S.sessions || []).forEach(function (x) {
      poserChez(x.qui, { t: x.debut, genre: "sess", s: x });
    });
    (S.evenements || []).forEach(function (e) {
      if (e.genre === "mot") poserChez(e.de, { t: e.t, genre: "mot", e: e });
    });
    Object.keys(parQui).forEach(function (k) {
      parQui[k].sort(function (a, b) { return b.t - a.t; });
    });

    var h = [];
    MOTS.length = 0;   // le registre des paroles se refait a chaque rendu
    (S.lignes || []).forEach(function (l) {
      var suite = parQui[l.id] || [];
      h.push('<div class="ch-piste ' + (suite.length ? "vif" : "pale") +
             (l.zone ? " zone" : "") + '">');
      // Le nom au-dessus, les sept familles dessous : deux lignes valent mieux
      // qu'une seule ou tout se dispute la largeur.
      h.push('<div class="ch-qui" data-ouvrir="' + esc(l.id) + '">' +
             '<img class="ch-visage" loading="lazy" alt="" src="' +
             esc(l.visage || ("/portraits/" + l.id + ".svg")) + '">' +
             '<span class="ch-ident">' +
             '<span class="ch-nom">' + esc(l.id) + "</span>" +
             '<span class="ch-fams">');
      ORDRE.forEach(function (f) {
        var b = (l.gestes || {})[f] || {};
        h.push('<i class="ch-fam" style="background:' + FAM[f].c + ";opacity:" +
               (b.n ? Math.min(1, 0.5 + b.n / 12) : 0.12) +
               '" data-fam="' + f + '" data-qui="' + esc(l.id) + '"></i>');
      });
      h.push('</span></span></div><div class="ch-lane">');

      // ON NE SERT PAS MILLE POINTS : au-dela d'une trentaine, l'oeil ne lit
      // plus un ordre, il lit une bouillie. Le reste se dit en clair.
      var montres = suite.slice(0, 30);
      montres.forEach(function (x) {
        if (x.genre === "sess") {
          var z = x.s;
          h.push('<div class="ch-sess' +
                 (z.issue === "echoue" || z.issue === "bloque" ? " echoue" : "") +
                 '" data-sess="' + esc(z.fichier || "") + '">');
          z.gestes.forEach(function (a, k) {
            h.push('<span class="ch-acte" data-sess="' + esc(z.fichier || "") +
                   '" data-acte="' + k + '">' + a.emoji + "</span>");
          });
          if (!z.gestes.length) h.push('<span class="ch-acte">·</span>');
          h.push("</div>");
        } else {
          // UN INDEX, PAS UNE CHAINE CONCATENEE. `de|vers|t` ne portait que
          // trois champs et obligeait a re-parser ; l'index rend l'evenement
          // ENTIER a la bulle — son texte compris.
          MOTS.push(x.e);
          h.push('<i class="ch-mot' + (x.e.verbe ? " verbe" : "") +
                 '" data-mot="' + (MOTS.length - 1) + '"></i>');
        }
      });
      if (suite.length > montres.length) {
        h.push('<span class="ch-reste" title="' +
               esc("les " + (suite.length - montres.length) +
                   " plus anciens ne sont pas montrés") + '">+' +
               (suite.length - montres.length) + "</span>");
      }
      h.push("</div></div>");
    });
    var scene = document.getElementById("ch-pistes");
    scene.innerHTML = h.join("");
    scene.querySelectorAll("[data-ouvrir]").forEach(function (n) {
      n.onclick = function () { ouvrir(n.dataset.ouvrir); };
    });
    brancherSurvol(scene, parQui);
  }

  // UN SEUL ECOUTEUR POUR TOUTE LA SCENE. Cinquante-six pistes, des centaines
  // d'actes : poser un gestionnaire par element couterait autant de fermetures
  // que de pastilles. On ecoute la scene et l'on regarde d'ou vient le geste.
  function brancherSurvol(scene, parQui) {
    function sessionDe(f) {
      var trouve = null;
      (S.sessions || []).forEach(function (x) { if (x.fichier === f) trouve = x; });
      return trouve;
    }
    scene.onmousemove = function (ev) {
      var acte = ev.target.closest(".ch-acte");
      var sess = ev.target.closest(".ch-sess");
      var mot = ev.target.closest(".ch-mot");
      var fam = ev.target.closest(".ch-fam");
      var qui = ev.target.closest(".ch-qui");
      if (acte) {
        var z = sessionDe(acte.dataset.sess);
        var a = z && z.gestes[+acte.dataset.acte];
        if (!a) return cacherBulle();
        var ou = a.ou || {};
        var rDe = ou.de ? nommer(ou.de) : null;
        var rVers = ou.vers && ou.vers !== ou.de ? nommer(ou.vers) : null;
        var dOu = rDe ? rDe.nom + (LIEUX[rDe.genre] ? "" :
                        " (" + rDe.genre + ")") : null;
        var vers = rVers ? rVers.nom + (LIEUX[rVers.genre] ? "" :
                           " (" + rVers.genre + ")") : null;
        var motOu = rDe && LIEUX[rDe.genre] ? "où" : "depuis";
        var sortie = (a.sorties || [])[0];
        return bulleDe(
          "<h5>" + a.emoji + " " +
          esc(a.verbe ? a.verbe.toLowerCase() : (a.nature || "un pas")) +
          ' <span class="ff">' + esc(a.nature || "") + "</span></h5>" +
          couples([
            ["qui", z.qui],
            // OU : la question qu'aucune bulle ne repondait. Deux cases quand
            // il agit a distance — se tenir dans un passage et ecouter les
            // cuisines n'est pas se tenir dans les cuisines.
            dOu ? [motOu, dOu + (ou.relation ? " · " + ou.relation : "")] : null,
            vers ? ["vers", vers] : null,
            a.cibles && a.cibles.length ? ["sur", refs(a.cibles)] : null,
            a.touche && a.touche.length ? ["il touche", refs(a.touche, true)] : null,
            ["quand", "pas n° " + a.rang + " · " + duree(a.debut_s) +
                      " après le début"],
            ["combien de temps", duree(a.duree_s) + " de monde"],
            ["ce qu'il paie", a.cout + " points"],
            sortie ? ["il en tire", (sortie.type || "?") +
                      (sortie.cible ? " sur " + nommer(sortie.cible).nom : "") +
                      (sortie.certitude ? " · " + sortie.certitude : "")] : null,
            a.blocage ? ["ça bute sur", a.blocage] : null,
            ["dans la session de", quand(z.debut)]]) +
          '<div class="txt">' + esc(a.quoi) + "</div>" +
          (sortie && sortie.apres
            ? '<div class="txt sort">' + esc(sortie.apres) +
              (sortie.apres.length >= 300 ? "…" : "") + "</div>" : "") +
          ((a.sorties || []).length > 1
            ? '<div class="pied">et ' + ((a.sorties || []).length - 1) +
              " autre(s) résultat" +
              ((a.sorties || []).length > 2 ? "s" : "") + " — clic</div>"
            : '<div class="pied">clic : le rapport entier, texte compris</div>'),
          ev);
      }
      if (sess) {
        var y = sessionDe(sess.dataset.sess);
        if (!y) return cacherBulle();
        var n = {};
        y.gestes.forEach(function (g) { n[g.emoji] = (n[g.emoji] || 0) + 1; });
        return bulleDe(
          "<h5>" + esc(y.qui) + " — une session</h5>" +
          couples([["quand", quand(y.debut)],
                   ["durée réelle", Math.round(y.duree_ms / 1000) + " s"],
                   ["issue", y.issue || "?"],
                   ["budget", (y.budget || "?") + " points"],
                   ["coût", y.cout_usd.toFixed(2) + " $"],
                   ["modèle", y.modele || "?"],
                   ["actes", y.gestes.length + " — " +
                    Object.keys(n).map(function (e) { return e + n[e]; }).join(" ")],
                   y.tache ? ["tâche", String(y.tache).slice(0, 60)] : null]) +
          '<div class="pied">clic : le rapport entier, acte par acte</div>', ev);
      }
      if (mot) {
        var m = MOTS[+mot.dataset.mot];
        if (!m) return cacherBulle();
        var j = m.jour;
        return bulleDe(
          "<h5>" + (m.verbe ? "▲ " + esc(m.verbe) : "● une parole") + "</h5>" +
          couples([["de", m.de], ["à", m.vers],
                   ["quand", quand(m.t)],
                   j ? ["au monde", "le " + j.jour + "e de la " + j.lune +
                        "e lune, an " + j.annee] : null,
                   m.verdict ? ["verdict", m.verdict] : null,
                   ["longueur", m.taille + " signes"]]) +
          (m.extrait
            ? '<div class="txt">' + esc(m.extrait) +
              (m.coupe ? "…" : "") + "</div>"
            : "") +
          '<div class="pied">clic sur la ligne : sa chambre, à droite</div>', ev);
      }
      if (fam) {
        var ligne = null;
        (S.lignes || []).forEach(function (x) {
          if (x.id === fam.dataset.qui) ligne = x;
        });
        var b = ligne && (ligne.gestes || {})[fam.dataset.fam] || {};
        var F = FAM[fam.dataset.fam];
        // UN « JAMAIS » NE SE LIT QUE COMPARE. Seul, il ressemble a une
        // panne ; a cote de ce que les autres font de ce geste, il devient
        // une mesure — et c'est toute la raison d'etre de cette frise.
        var tot = 0, ceux = 0;
        (S.lignes || []).forEach(function (x) {
          var g = (x.gestes || {})[fam.dataset.fam] || {};
          if (g.n) { tot += g.n; ceux += 1; }
        });
        return bulleDe(
          "<h5>" + F.e + " " + esc(F.n) + "</h5>" +
          couples([["chez", fam.dataset.qui],
                   ["combien", b.n ? b.n + " fois" : "jamais"],
                   b.t ? ["la dernière", quand(b.t)] : null,
                   b.premier ? ["la première", quand(b.premier)] : null,
                   ["dans la ville", ceux + " habitant" + (ceux > 1 ? "s" : "") +
                    " le font · " + tot + " fois en tout"],
                   ["sa part", tot ? Math.round((b.n || 0) / tot * 100) + " %"
                                   : "aucun ne le fait"]]) +
          '<div class="txt">' + esc(DITS[fam.dataset.fam] || "") + "</div>" +
          (b.n ? "" : '<div class="pied">un geste que personne ne lui a ' +
                      "donné les moyens de faire — c'est ce qu'on cherche</div>"),
          ev);
      }
      if (qui) {
        var id = qui.dataset.ouvrir, li = null;
        (S.lignes || []).forEach(function (x) { if (x.id === id) li = x; });
        var suite = (parQui[id] || []);
        // OU IL SE TIENT : la bande des salles le sait deja, la bulle ne le
        // demandait pas. C'est pourtant la premiere chose qu'on veut d'un
        // nom sur une frise.
        var sa = null;
        // `gens` porte des OBJETS ({id, ...}), pas des chaines — un indexOf
        // sur l'identifiant ne trouvait jamais rien, et le « ou » restait muet.
        ((S.salles || {}).salles || []).forEach(function (x) {
          (x.gens || []).forEach(function (g) {
            if ((g && g.id != null ? g.id : g) === id) sa = x;
          });
        });
        var sess = suite.filter(function (x) { return x.genre === "sess"; });
        var mots = suite.filter(function (x) { return x.genre === "mot"; });
        var der = suite[0];
        var derS = sess[0] && sess[0].s;
        return bulleDe(
          "<h5>" + esc(id) + "</h5>" +
          couples([
            ["nature", li && li.zone ? "zone (MJ)" : "habitant"],
            sa ? ["où", String(sa.salle).replace(/-/g, " ") +
                  (sa.lieu ? " · " + sa.lieu : "")] : null,
            ["sessions", sess.length + (sess.length ? "" : " — jamais activé")],
            ["paroles", String(mots.length)],
            li && li.energie != null ? ["énergie", li.energie.toFixed(1)] : null,
            der ? ["dernière trace", quand(der.t) + " · " +
                   (der.genre === "sess" ? "une journée" : "une parole")] : null,
            derS && derS.tache
              ? ["ce qu'il poursuit", String(derS.tache).slice(0, 70)] : null,
            derS ? ["sa dernière journée", (derS.issue || "?") + " · " +
                    derS.gestes.length + " pas · " +
                    derS.cout_usd.toFixed(2) + " $"] : null]) +
          '<div class="pied">clic : sa chambre, à droite</div>', ev);
      }
      cacherBulle();
    };
    scene.onmouseleave = cacherBulle;
    scene.onclick = function (ev) {
      var a = ev.target.closest("[data-sess]");
      if (a && a.dataset.sess) {
        ev.stopPropagation();
        ouvrirRapport(a.dataset.sess,
                      a.classList.contains("ch-acte") ? +a.dataset.acte : null);
      }
    };
  }

  // Ce que chaque famille veut dire, en clair — la taxonomie de docs/habitant.md.
  var DITS = {
    percevoir: "son réveil : le brief, ses creux, les billets en percept, demain.md",
    lire: "Read, Grep, Glob — le dépôt et son étagère ./livres/",
    ecrire: "chez lui, et rien n'y fait foi : son cahier, ses brouillons, ses fiches",
    verbe: "TENTER, FAIRE, DEMANDER — les trois façons d'engager le monde",
    parler: "au parloir, ou un billet qui réveille l'autre",
    conclure: "demain.md — ce qu'il se dit à lui-même pour le lendemain",
    subi: "ce que le lanceur dépose : son vécu au fil"
  };

  function bandeau() {
    if (!S) return;
    var actes = (S.sessions || []).reduce(function (a, x) {
      return a + x.gestes.length;
    }, 0);
    var cout = (S.sessions || []).reduce(function (a, x) {
      return a + x.cout_usd;
    }, 0);
    document.getElementById("ch-bandeau").innerHTML =
      "<b>" + (S.sessions || []).length + "</b> sessions · <b>" + actes +
      "</b> actes · " + cout.toFixed(2) + " $ · <b>" +
      (S.evenements || []).length + "</b> événements · " + S.chambres +
      " chambres, <b>" + S.muettes + "</b> muettes · le plus récent à gauche" +
      "<br>" + ORDRE.map(function (f) {
        var t = 0;
        (S.lignes || []).forEach(function (l) {
          t += ((l.gestes || {})[f] || {}).n || 0;
        });
        return '<span class="ch-leg"><i style="color:' + FAM[f].c + '">' +
               FAM[f].e + "</i> " + FAM[f].n + " <b>" + t + "</b></span>";
      }).join("");
  }

  function rendre() { rendrePistes(); bandeau(); }

  function rendreSalles() {
    var d = S.salles || { salles: [] };
    var h = ['<div class="ch-tete">Les salles — ' + d.salles.length +
             " occupées</div>"];
    d.salles.forEach(function (s) {
      h.push('<div class="ch-salle"><b>' + esc(s.lieu || s.salle) + "</b><span>" +
             s.gens.length + " · " + esc(s.salle) + '</span><div class="ch-gens">' +
             s.gens.map(function (g) {
               return '<i class="ch-g' + (g.chambre ? " a" : "") +
                      '" data-qui="' + esc(g.id) + '">' + esc(g.id) + "</i>";
             }).join("") + "</div></div>");
    });
    var c = document.getElementById("ch-salles");
    c.innerHTML = h.join("");
    c.querySelectorAll("[data-qui]").forEach(function (n) {
      n.onclick = function () { ouvrir(n.dataset.qui); };
    });
  }

  function ouvrir(qui) {
    choisie = qui;
    rendrePistes();
    var f = document.getElementById("ch-fiche");
    f.innerHTML = '<div class="ch-vide">…</div>';
    fetch("/admin/chambres/" + encodeURIComponent(qui))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.erreur) {
          f.innerHTML = '<div class="ch-vide">' + esc(d.erreur) + "</div>";
          return;
        }
        var h = ['<div class="ch-fiche"><h3>' + esc(d.id) + '</h3>' +
                 '<div class="ch-sous">' + (d.zone ? "zone (MJ)" : "habitant") +
                 (d.energie != null ? " · énergie " + d.energie.toFixed(1) : "") +
                 (d.activations != null ? " · " + d.activations + " activations" : "") +
                 ' · <span class="ch-marque ' +
                 (d.cahier_amende ? "ch-oui" : "ch-non") + '">' +
                 (d.cahier_amende ? "cahier amendé" : "cahier au semis") +
                 "</span></div>"];
        if (d.gestes) {
          h.push('<div class="ch-bloc"><h4>Ses gestes</h4><ul>');
          ORDRE.forEach(function (fa) {
            var b = d.gestes[fa] || {};
            h.push('<li style="' + (b.n ? "" : "opacity:.45") + '"><i style="color:' +
                   FAM[fa].c + '">' + FAM[fa].e + "</i> " + FAM[fa].n + " — <b>" +
                   (b.n || 0) + "</b>" +
                   (b.t ? " · " + quand(b.t) : (b.n ? "" : " · jamais")) + "</li>");
          });
          h.push("</ul></div>");
        }
        var p = d.en_souffrance || {};
        if (p.j_attends || p.on_attend_de_moi) {
          h.push('<div class="ch-bloc"><h4>Ce qui pend</h4><ul>');
          ((p.detail || {}).j_attends || []).forEach(function (x) {
            h.push("<li>il attend <b>" + esc(x.de || "?") + "</b> — " +
                   esc(String(x.quoi || "").slice(0, 150)) + "</li>");
          });
          ((p.detail || {}).on_attend_de_moi || [])
            .filter(function (x) { return !x.tenu; }).forEach(function (x) {
              h.push("<li>doit à <b>" + esc(x.pour || "?") + "</b> — " +
                     esc(String(x.quoi || "").slice(0, 150)) + "</li>");
            });
          h.push("</ul></div>");
        }
        if ((d.problemes || []).length) {
          h.push('<div class="ch-bloc"><h4>Pannes de la machine</h4><ul>');
          d.problemes.forEach(function (x) {
            h.push("<li><b>" + esc(x.id || "?") + "</b> " +
                   esc(String(x.quoi || "").slice(0, 160)) + "</li>");
          });
          h.push("</ul></div>");
        }
        if ((d.ecrits || []).length) {
          h.push('<div class="ch-bloc"><h4>Ce qu’il a écrit chez lui</h4><ul>');
          d.ecrits.slice(0, 8).forEach(function (x) {
            h.push("<li>" + esc(x.quoi) + " — " + quand(x.t) + "</li>");
          });
          h.push("</ul></div>");
        }
        if ((d.relations || []).length) {
          h.push('<div class="ch-bloc"><h4>Ses canaux</h4><ul>');
          d.relations.forEach(function (r) {
            h.push('<li><b data-qui="' + esc(r.avec) +
                   '" style="cursor:pointer">' + esc(r.avec) + "</b> — " +
                   r.entrees + " entrées</li>");
          });
          h.push("</ul></div>");
        }
        h.push('<div class="ch-bloc"><h4>Son cahier</h4><div class="ch-cahier">' +
               esc(d.cahier || "") + "</div></div></div>");
        f.innerHTML = h.join("");
        f.querySelectorAll("[data-qui]").forEach(function (n) {
          n.onclick = function () { ouvrir(n.dataset.qui); };
        });
      });
  }

  // LE CLIC : TOUT, ET EXACT. La vue d'ensemble montre des formes ; ici on
  // rend le rapport tel qu'il a ete depose — chaque pas avec son texte entier,
  // sa source, son resultat, sa preuve, ce qu'il a touche et ce qu'il a
  // produit, et la comptabilite de la session jusqu'aux jetons.
  function ouvrirRapport(fichier, acteVise) {
    var f = document.getElementById("ch-fiche");
    f.innerHTML = '<div class="ch-vide">…</div>';
    fetch("/admin/chambres/rapport/" + encodeURIComponent(fichier))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.erreur) {
          f.innerHTML = '<div class="ch-vide">' + esc(d.erreur) + "</div>";
          return;
        }
        var u = d.usage || {};
        var h = ['<div class="ch-fiche"><h3>' + esc(d.qui || "?") + "</h3>" +
                 '<div class="ch-sous">une session · ' + esc(d.cree_le || "") +
                 "</div>"];
        h.push('<div class="ch-bloc"><h4>La session</h4><div class="cl2">');
        [["issue", d.issue], ["tâche", d.tache],
         ["durée réelle", d.duree_ms ? Math.round(d.duree_ms / 1000) + " s" : null],
         ["dont API", d.duree_api_ms ? Math.round(d.duree_api_ms / 1000) + " s" : null],
         ["budget", d.budget != null ? d.budget + " points (" +
            (d.budget_secondes || 0) + " s de monde)" : null],
         ["énergie dépensée", d.energie_depensee],
         ["importance", d.importance != null ? d.importance.toFixed(3) : null],
         ["coût", d.cout_usd ? d.cout_usd.toFixed(4) + " $" : null],
         ["modèle", (d.modele || "") + (d.effort ? " · effort " + d.effort : "")],
         ["tours", d.tours],
         ["jetons", u.input_tokens != null
            ? (u.input_tokens + " entrée · " + (u.output_tokens || 0) + " sortie")
            : null],
         ["session", d.session], ["session du PNJ", d.session_pnj],
         ["front", d.front], ["rapport", d.fichier]
        ].forEach(function (p) {
          if (p[1] === null || p[1] === undefined || p[1] === "") return;
          h.push("<span>" + esc(p[0]) + "</span><b>" + esc(p[1]) + "</b>");
        });
        h.push("</div></div>");
        if (d.phrase) {
          h.push('<div class="ch-bloc"><h4>Sa phrase</h4><div class="ch-cahier">' +
                 esc(d.phrase) + "</div></div>");
        }
        (d.activites || []).forEach(function (a, k) {
          h.push('<div class="ch-bloc' +
                 (acteVise === k ? " vise" : "") + '" id="acte-' + k + '">' +
                 "<h4>" + a.emoji + " pas " + (a.ordre || k + 1) + " · " +
                 esc(a.nature || "un pas") +
                 (a.temps ? " · " + (a.temps.duree_s || 0) + " s de monde" : "") +
                 " · " + (a.cout_energie || 0) + " d’énergie</h4>");
          h.push('<div class="ch-cahier">' + esc(a.quoi || "") + "</div>");
          if (a.source) h.push('<p class="ch-champ"><i>sa source</i> ' +
                               esc(a.source) + "</p>");
          if (a.resultat) h.push('<p class="ch-champ"><i>ce qu’il en sort</i> ' +
                                 esc(a.resultat) + "</p>");
          if (a.preuve) h.push('<p class="ch-champ"><i>sa preuve</i> ' +
                               esc(a.preuve) + "</p>");
          if (a.blocage) h.push('<p class="ch-champ ch-non"><i>blocage</i> ' +
                                esc(a.blocage) + "</p>");
          if ((a.sources_touchees || []).length) {
            // UNE SOURCE TOUCHEE EST UN OBJET {ref, mode}, pas une chaine :
            // la joindre telle quelle rendait « [object Object] ». Le MODE
            // dit ce qu'il en a fait — parcourt, releve, ouvre — et c'est la
            // moitie interessante.
            h.push('<p class="ch-champ"><i>touché</i> ' +
                   a.sources_touchees.map(function (x) {
                     if (!x || typeof x !== "object") return esc(x);
                     return esc(x.ref || x.id || "?") +
                            (x.mode ? " <s>" + esc(x.mode) + "</s>" : "");
                   }).join(" · ") + "</p>");
          }
          (a.resultats_produits || []).forEach(function (r) {
            h.push('<p class="ch-champ"><i>' + esc(r.type || "résultat") +
                   (r.cible ? " → " + esc(r.cible) : "") + "</i> " +
                   (r.avant ? "<s>" + esc(String(r.avant).slice(0, 220)) +
                              "</s> " : "") +
                   esc(String(r.apres || "").slice(0, 260)) + "</p>");
          });
          h.push("</div>");
        });
        h.push("</div>");
        f.innerHTML = h.join("");
        if (acteVise != null) {
          var cible = document.getElementById("acte-" + acteVise);
          if (cible) cible.scrollIntoView({ block: "center" });
        }
      });
  }

  window.chargerChambres = function () {
    css();
    var e = document.getElementById("chambres");
    if (!e.dataset.pose) { poser(); e.dataset.pose = "1"; }
    fetch("/admin/chambres", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        S = d;
        rendreSalles();
        rendre();
      })
      .catch(function (err) {
        document.getElementById("chambres").innerHTML =
          '<div class="ch-vide">Les chambres ne répondent pas : ' + esc(err) +
          "</div>";
      });
  };
})();
