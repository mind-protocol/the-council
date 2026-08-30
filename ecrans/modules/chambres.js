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
// UNE SESSION EST UN CONTAINER, PAS UN POINT. Un rapport porte `cree_le` et
// `duree_ms` : la session a une durée réelle, et ce qu'elle a produit se pose
// DEDANS. Deux horloges, jamais mêlées — le container est en temps machine,
// les actes se placent à la fraction du temps de MONDE qu'ils ont consommée
// (`temps.debut_s / duree_s` de chaque activité du rapport).
(function () {
  "use strict";

  var S = null;
  var t0 = 0, t1 = 1;
  var choisie = null;
  var GAUCHE = 186;

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
    return new Date(t).toLocaleString("fr-FR").slice(0, 17);
  }

  function css() {
    if (document.getElementById("style-chambres")) return;
    var e = document.createElement("style");
    e.id = "style-chambres";
    e.textContent = [
      "#chambres{margin:-1.2rem;height:calc(100vh - 112px);min-height:620px;",
      "  display:grid;grid-template-columns:200px 1fr 340px;overflow:hidden}",
      ".ch-col{overflow:auto;border-right:1px solid #2a221a;padding:.7rem .8rem}",
      ".ch-col:last-child{border-right:0;border-left:1px solid #2a221a}",
      ".ch-tete{font:.68rem ui-monospace,monospace;letter-spacing:.12em;",
      "  text-transform:uppercase;color:#8a7659;margin:0 0 .6rem}",
      ".ch-salle{margin-bottom:.7rem}",
      ".ch-salle b{display:block;font-size:.76rem;color:#d8cfc3}",
      ".ch-salle span{font:.66rem ui-monospace,monospace;color:#8a7659}",
      ".ch-gens{display:flex;flex-wrap:wrap;gap:3px;margin-top:.25rem}",
      ".ch-g{font:.6rem ui-monospace,monospace;padding:.1em .3em;border-radius:2px;",
      "  border:1px solid #3a3026;color:#8a7659;cursor:pointer}",
      ".ch-g.a{border-color:#7a6432;color:#d8cfc3}",
      ".ch-scene{position:relative;display:flex;flex-direction:column;overflow:hidden}",
      ".ch-mini{height:30px;flex:0 0 30px;position:relative;cursor:pointer;",
      "  border-bottom:1px solid #2a221a;background:#120f0c}",
      ".ch-mini i{position:absolute;bottom:0;background:#8a6a2a;width:2px}",
      ".ch-mini .fen{position:absolute;top:0;bottom:0;background:#2b2317;",
      "  border-left:1px solid #4a3d2c;border-right:1px solid #4a3d2c}",
      ".ch-pistes{flex:1;overflow:auto;position:relative;touch-action:none}",
      ".ch-piste{display:grid;grid-template-columns:" + 186 + "px 1fr;",
      "  align-items:center;border-bottom:1px solid #1d1812;height:26px}",
      ".ch-piste.pale{opacity:.32}",
      ".ch-piste.vif{background:#171310}",
      ".ch-qui{display:flex;align-items:center;gap:6px;padding:2px 6px;",
      "  cursor:pointer;overflow:hidden;height:100%}",
      ".ch-visage{width:20px;height:20px;flex:0 0 20px;border-radius:50%;",
      "  overflow:hidden;background:#241d17;line-height:0}",
      ".ch-visage svg{width:100%;height:100%;display:block}",
      ".ch-nom{font:.7rem ui-monospace,monospace;color:#c8bfb3;white-space:nowrap;",
      "  overflow:hidden;text-overflow:ellipsis;flex:1}",
      ".ch-piste.zone .ch-nom{color:#c8a24a}",
      ".ch-fams{display:flex;gap:1px;flex:0 0 auto}",
      ".ch-fam{width:9px;height:9px;border-radius:1px;cursor:help}",
      ".ch-lane{position:relative;height:100%}",
      ".ch-sess{position:absolute;top:3px;bottom:3px;min-width:4px;",
      "  border:1px solid #7a6432;background:rgba(122,100,50,.18);",
      "  border-radius:2px;cursor:pointer;overflow:hidden}",
      ".ch-sess:hover{background:rgba(224,189,88,.3);border-color:#e0bd58}",
      ".ch-sess.echoue{border-color:#a3543a;background:rgba(163,84,58,.18)}",
      ".ch-acte{position:absolute;top:0;bottom:0;display:flex;align-items:center;",
      "  justify-content:center;font-size:10px;cursor:help;line-height:1}",
      ".ch-acte:hover{background:rgba(224,189,88,.4)}",
      ".ch-mot{position:absolute;top:50%;width:5px;height:5px;margin-top:-2.5px;",
      "  border-radius:50%;background:#c8bfb3;opacity:.55;cursor:help}",
      ".ch-mot.verbe{background:#e0bd58;opacity:1;width:8px;height:8px;",
      "  margin-top:-4px}",
      ".ch-bandeau{flex:0 0 auto;padding:.3rem .7rem;background:#100d0a;",
      "  border-top:1px solid #2a221a;font:.68rem ui-monospace,monospace;",
      "  color:#8a7659;line-height:1.7}",
      ".ch-bandeau b{color:#d8cfc3}",
      ".ch-vide{padding:2rem;color:#8a7659}",
      ".ch-fiche h3{margin:.2rem 0 .1rem;font-size:.95rem;color:#e8dfd3}",
      ".ch-fiche .ch-sous{font:.66rem ui-monospace,monospace;color:#8a7659;",
      "  margin-bottom:.6rem}",
      ".ch-bloc{margin:.7rem 0;padding:.5rem .6rem;border:1px solid #2a221a;",
      "  border-radius:3px}",
      ".ch-bloc h4{margin:0 0 .35rem;font:.64rem ui-monospace,monospace;",
      "  letter-spacing:.1em;text-transform:uppercase;color:#8a7659}",
      ".ch-bloc li{font-size:.76rem;color:#c8bfb3;margin-bottom:.3rem;",
      "  line-height:1.4}",
      ".ch-bloc ul{margin:0;padding-left:1.1em}",
      ".ch-cahier{white-space:pre-wrap;font-size:.72rem;color:#c8bfb3;",
      "  max-height:240px;overflow:auto;line-height:1.45}",
      ".ch-marque{display:inline-block;font:.6rem ui-monospace,monospace;",
      "  padding:.1em .4em;border-radius:2px;border:1px solid currentColor}",
      ".ch-oui{color:#7fb18c}.ch-non{color:#c07a4a}"
    ].join("");
    document.head.appendChild(e);
  }

  function poser() {
    document.getElementById("chambres").innerHTML =
      '<div class="ch-col" id="ch-salles"></div>' +
      '<div class="ch-scene">' +
      '<div class="ch-mini" id="ch-mini"></div>' +
      '<div class="ch-pistes" id="ch-pistes"></div>' +
      '<div class="ch-bandeau" id="ch-bandeau"></div></div>' +
      '<div class="ch-col" id="ch-fiche"><div class="ch-vide">' +
      "Touche une ligne pour ouvrir la chambre.</div></div>";
  }

  function bornes() {
    var min = Infinity, max = -Infinity;
    (S.evenements || []).forEach(function (e) {
      if (e.t < min) min = e.t;
      if (e.t > max) max = e.t;
    });
    (S.sessions || []).forEach(function (s) {
      if (s.debut < min) min = s.debut;
      if (s.fin > max) max = s.fin;
    });
    return isFinite(min) ? [min, max] : [Date.now() - 36e5, Date.now()];
  }

  // ON CADRE LA RAFALE, PAS L'INSTANT : les événements sont en paquets séparés
  // par des jours, et garder la largeur fait tomber le clic dans le vide.
  function cadrerLaRafale(vise) {
    var ev = (S.evenements || []).slice().sort(function (a, b) {
      return a.t - b.t;
    });
    if (!ev.length) { var b = bornes(); t0 = b[0]; t1 = b[1]; return; }
    var k = 0, ecart = Infinity;
    ev.forEach(function (e, i) {
      var d = Math.abs(e.t - vise);
      if (d < ecart) { ecart = d; k = i; }
    });
    var a = k, z = k;
    while (a > 0 && ev[a].t - ev[a - 1].t < 36e5) a -= 1;
    while (z < ev.length - 1 && ev[z + 1].t - ev[z].t < 36e5) z += 1;
    var marge = Math.max(60e3, (ev[z].t - ev[a].t) * 0.06);
    t0 = ev[a].t - marge;
    t1 = ev[z].t + marge;
  }

  function part(t) { return (t - t0) / Math.max(1, t1 - t0) * 100; }

  function rendreMini() {
    var b = bornes(), n = 170, seaux = new Array(n).fill(0);
    (S.evenements || []).forEach(function (e) {
      seaux[Math.floor((e.t - b[0]) / Math.max(1, b[1] - b[0]) * (n - 1))] += 1;
    });
    var pic = Math.max.apply(null, seaux) || 1;
    var h = ['<div class="fen" style="left:' +
             ((t0 - b[0]) / Math.max(1, b[1] - b[0]) * 100) + "%;width:" +
             Math.max(0.4, (t1 - t0) / Math.max(1, b[1] - b[0]) * 100) +
             '%"></div>'];
    seaux.forEach(function (v, i) {
      if (v) h.push('<i style="left:' + (i / n * 100) + "%;height:" +
                    (3 + v / pic * 22) + 'px"></i>');
    });
    document.getElementById("ch-mini").innerHTML = h.join("");
  }

  function rendrePistes() {
    var actifs = {}, parQui = {}, mots = {};
    (S.evenements || []).forEach(function (e) {
      if (e.t < t0 || e.t > t1) return;
      if (e.de) actifs[e.de] = 1;
      if (e.vers) actifs[e.vers] = 1;
      if (e.genre === "mot") (mots[e.de] = mots[e.de] || []).push(e);
    });
    (S.sessions || []).forEach(function (s) {
      (parQui[s.qui] = parQui[s.qui] || []).push(s);
      if (s.fin >= t0 && s.debut <= t1) actifs[s.qui] = 1;
    });

    var h = [];
    (S.lignes || []).forEach(function (l) {
      var vif = actifs[l.id] || choisie === l.id;
      h.push('<div class="ch-piste ' + (vif ? "vif" : "pale") +
             (l.zone ? " zone" : "") + '">');
      h.push('<div class="ch-qui" data-ouvrir="' + esc(l.id) + '">' +
             '<span class="ch-visage">' + (l.portrait || "") + "</span>" +
             '<span class="ch-nom">' + esc(l.id) + "</span>" +
             '<span class="ch-fams">');
      ORDRE.forEach(function (f) {
        var b = (l.gestes || {})[f] || {};
        h.push('<i class="ch-fam" style="background:' + FAM[f].c + ";opacity:" +
               (b.n ? Math.min(1, 0.5 + b.n / 12) : 0.12) + '" title="' +
               FAM[f].e + " " + FAM[f].n + " — " + (b.n || 0) +
               (b.n ? "" : " (jamais)") + '"></i>');
      });
      h.push('</span></div><div class="ch-lane">');

      // LES SESSIONS, EN CONTAINERS : leur largeur EST leur durée réelle.
      (parQui[l.id] || []).forEach(function (s) {
        if (s.fin < t0 || s.debut > t1) return;
        var g = part(s.debut), w = Math.max(0.3, part(s.fin) - g);
        h.push('<div class="ch-sess' +
               (s.issue === "echoue" || s.issue === "bloque" ? " echoue" : "") +
               '" style="left:' + g + "%;width:" + w + '%" title="' +
               esc(l.id + " · " + quand(s.debut) + " · " +
                   Math.round(s.duree_ms / 1000) + " s réelles · issue " +
                   (s.issue || "?") + " · " + s.gestes.length + " actes · " +
                   s.cout_usd.toFixed(2) + " $") + '">');
        // LES ACTES, DEDANS : placés à la fraction du temps de MONDE consommé.
        s.gestes.forEach(function (a) {
          var x = (a.debut_s - s.monde0) / Math.max(1, s.monde1 - s.monde0) * 100;
          var aw = Math.max(7, a.duree_s / Math.max(1, s.monde1 - s.monde0) * 100);
          h.push('<span class="ch-acte" style="left:' + x + "%;width:" +
                 Math.min(aw, Math.max(7, 100 - x)) + '%" title="' +
                 esc((a.type || "acte") + " · " + a.duree_s +
                     " s de monde · " + a.cout + " d’énergie — " + a.quoi) +
                 '">' + a.emoji + "</span>");
        });
        h.push("</div>");
      });
      // LES MOTS : un point par entrée de canal ; un verbe est plus gros.
      (mots[l.id] || []).forEach(function (e) {
        h.push('<i class="ch-mot' + (e.verbe ? " verbe" : "") + '" style="left:' +
               part(e.t) + '%" title="' +
               esc((e.verbe ? "[" + e.verbe + "] " : "") + "→ " + e.vers +
                   " · " + quand(e.t)) + '"></i>');
      });
      h.push("</div></div>");
    });
    document.getElementById("ch-pistes").innerHTML = h.join("");
    document.querySelectorAll("#ch-pistes [data-ouvrir]").forEach(function (n) {
      n.onclick = function () { ouvrir(n.dataset.ouvrir); };
    });
  }

  function bandeau() {
    if (!S) return;
    var vus = (S.evenements || []).filter(function (e) {
      return e.t >= t0 && e.t <= t1;
    });
    var sess = (S.sessions || []).filter(function (s) {
      return s.fin >= t0 && s.debut <= t1;
    });
    var cout = sess.reduce(function (a, s) { return a + s.cout_usd; }, 0);
    document.getElementById("ch-bandeau").innerHTML =
      "<b>" + quand(t0) + "</b> → <b>" + quand(t1) + "</b> · <b>" +
      sess.length + "</b> sessions (" + cout.toFixed(2) + " $) · <b>" +
      vus.length + "</b> événements · " + S.chambres + " chambres, <b>" +
      S.muettes + "</b> muettes · molette : zoom · glisser : déplacer" +
      "<br>" + ORDRE.map(function (f) {
        var t = 0;
        (S.lignes || []).forEach(function (l) {
          t += ((l.gestes || {})[f] || {}).n || 0;
        });
        return '<i style="color:' + FAM[f].c + '">' + FAM[f].e + "</i> " +
               FAM[f].n + " <b>" + t + "</b>";
      }).join(" · ");
  }

  function rendre() { rendreMini(); rendrePistes(); bandeau(); }

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

  function brancher() {
    var pistes = document.getElementById("ch-pistes");
    if (pistes.dataset.branche) return;
    pistes.dataset.branche = "1";
    // LE ZOOM N'EST PLUS CAPRICIEUX. Trois choses : un facteur doux (1.18),
    // l'ancrage sur le curseur, et des bornes dures — on ne sort pas du temps
    // connu et l'on ne descend pas sous la minute.
    pistes.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      var r = pistes.getBoundingClientRect(), b = bornes();
      var p = Math.max(0, Math.min(1, (ev.clientX - r.left - GAUCHE) /
                                      Math.max(1, r.width - GAUCHE)));
      var centre = t0 + (t1 - t0) * p;
      var large = Math.max(60e3, Math.min((t1 - t0) * (ev.deltaY > 0 ? 1.18 : 1 / 1.18),
                                          Math.max(12e4, b[1] - b[0])));
      t0 = centre - (centre - t0) / Math.max(1, t1 - t0) * large;
      t1 = t0 + large;
      rendre();
    }, { passive: false });
    var glisse = null;
    pistes.addEventListener("pointerdown", function (ev) {
      if (ev.target.closest("[data-ouvrir]")) return;
      glisse = { x: ev.clientX, t0: t0, t1: t1 };
    });
    pistes.addEventListener("pointermove", function (ev) {
      if (!glisse) return;
      var r = pistes.getBoundingClientRect();
      var d = (ev.clientX - glisse.x) / Math.max(1, r.width - GAUCHE) *
              (glisse.t1 - glisse.t0);
      t0 = glisse.t0 - d; t1 = glisse.t1 - d;
      rendre();
    });
    window.addEventListener("pointerup", function () { glisse = null; });
    document.getElementById("ch-mini").onclick = function (ev) {
      var r = this.getBoundingClientRect(), b = bornes();
      cadrerLaRafale(b[0] + (b[1] - b[0]) *
                     ((ev.clientX - r.left) / Math.max(1, r.width)));
      rendre();
    };
  }

  window.chargerChambres = function () {
    css();
    var e = document.getElementById("chambres");
    if (!e.dataset.pose) { poser(); e.dataset.pose = "1"; }
    fetch("/admin/chambres", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        S = d;
        if (!e.dataset.cadre) {
          var ev = S.evenements || [];
          cadrerLaRafale(ev.length ? ev[ev.length - 1].t : Date.now());
          e.dataset.cadre = "1";
        }
        rendreSalles();
        brancher();
        rendre();
      })
      .catch(function (err) {
        document.getElementById("chambres").innerHTML =
          '<div class="ch-vide">Les chambres ne répondent pas : ' + esc(err) +
          "</div>";
      });
  };
})();
