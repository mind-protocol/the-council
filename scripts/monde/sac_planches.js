// -*- coding: utf-8 -*-
/**
 * LES PLANCHES DU FOUR — voir la bataille pendant qu'elle cuit.
 *
 * Un four qui met dix heures et n'affiche qu'un compteur de secondes est un
 * four qu'on ne règle jamais : on lance, on attend, on découvre à la fin qu'une
 * escouade tournait en rond depuis la troisième minute. Or les positions sont
 * là, à chaque pas, et personne ne les regarde.
 *
 * On écrit donc une image de temps en temps. Pas un PNG — aucune dépendance à
 * installer, c'est la règle de `planches.py` et elle est bonne : le FOND est un
 * SVG posé une fois dans une page, et chaque instant n'est qu'un petit tas de
 * points en JSON. Quinze kilo-octets par planche à trois cents hommes, et la
 * page les enfile toute seule.
 *
 * LA PAGE SE RAFRAÎCHIT PENDANT LA CUISSON. Elle demande la liste, prend la
 * dernière planche, et recommence. Tant que le four tourne on suit l'assaut en
 * direct ; quand il a fini, la même page devient une réglette qu'on tire.
 *
 * LA VILLE Y EST AUSSI, depuis que le four fait lui-même la tournée que la
 * foule faisait en dessinant. On voit donc ce qu'on était venu voir : les rues
 * qui se vident devant la colonne, ceux qui se terrent, et l'or du guet qui
 * remonte à contre-courant. Le bouton « habitants » les éteint — ils sont le
 * décor de ce qui se passe, pas toujours le sujet.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const http = require("http");

const ICI = path.dirname(path.dirname(__dirname));
const DESSINS = path.join(ICI, "dessins", "sac");

// Les mêmes couleurs que le module — une planche qui ne ressemble pas à
// l'écran est une planche qu'il faut traduire dans sa tête à chaque coup d'œil.
// UN CONTOUR, ET IL EST DEVENU NÉCESSAIRE LE JOUR OÙ LE BÂTI EST ARRIVÉ. Un
// point rouge sur un fond beige se voit ; le même point sur une brique
// d'artisanat ou une manse ocre disparaît. Le remplissage dit le camp, le
// trait le DÉTACHE — c'est la même teinte poussée au sombre, donc il sépare
// sans ajouter une couleur de plus à lire.
const TEINTE = { assaut: "#8c2f22", garde: "#24506b",
                 deroute: "#a8763a", mort: "#5a5348",
                 // la ville : celui qui court, celui qui s'est terré, et l'or
                 // du guet qui remonte la rue que tout le monde descend
                 fuite: "#b03a24", terre: "#8a7c66", guet: "#d8930a" };
const TRAIT = { assaut: "#3d0f08", garde: "#0c1f2d", deroute: "#4d3312",
                mort: "#2b2721" };

class Planches {
  /**
   * @param {object} o        les arguments du four (porte, hommes…)
   * @param {object} plan     le plan cuit, pour le fond
   * @param {number} chaque   une planche toutes les N secondes de bataille
   */
  constructor(o, plan, chaque) {
    this.chaque = chaque;
    this.prochaine = 0;
    this.liste = [];
    this.dossier = path.join(DESSINS, (o.sortie || "sac"));
    fs.rmSync(this.dossier, { recursive: true, force: true });
    fs.mkdirSync(this.dossier, { recursive: true });
    this.page(o, plan);
    // DE QUOI REFABRIQUER LE FOND PLUS TARD. Le plan de la ville se recuit —
    // le bâti est passé de 48 377 à 53 716 bâtiments dans la même journée — et
    // un fond périmé montre une ville qui n'existe plus, avec une bataille
    // juste posée dessus. On garde donc les quelques arguments qui suffisent à
    // le redessiner sans rien recuire.
    fs.writeFileSync(path.join(this.dossier, "four.json"),
                     JSON.stringify({ porte: o.porte, hommes: o.hommes,
                                      sortie: o.sortie, chaque: this.chaque }));
  }

  /**
   * Le fond, écrit UNE FOIS dans son propre fichier — et il porte la ville
   * entière, bâti compris.
   *
   * Il tenait d'abord dans la page, et n'avait ni les toits ni la ville : un
   * cadre serré sur la porte et l'objectif, quatre traits de voirie. C'était
   * lisible et ça ne disait rien — une bataille dans Port-Réal se juge sur ce
   * qu'elle traverse, et un assaut sans maisons est un assaut dans un champ.
   *
   * Trois mégaoctets de chemins, donc, et c'est très bien : ils partent dans
   * `fond.svg`, servi une fois, mis en cache par le navigateur, pendant que la
   * page reste un fichier de quelques kilo-octets qu'on peut relire.
   */
  fond(o, plan) {
    const rep = (nom, genre) => (plan.reperes || []).find(
      (r) => r.nom === nom) || (plan.reperes || []).find((r) => r.genre === genre);
    const porte = rep(o.porte, "porte"), donjon = rep("Le Donjon Rouge", "donjon");
    const [x0, y0, x1, y1] = plan.bornes;
    const V = plan.voies || {}, R = plan.rempart || {}, T = plan.types || {};
    const trace = (d, cl) => d ? '<path class="' + cl + '" d="' + d + '"/>' : "";

    // Le bâti, une couche par métier, classée par CATÉGORIE — les mêmes que
    // `carte-ville` : l'habitat fait le beige de fond, l'artisanat la brique,
    // le commerce l'ocre. C'est ce qui rend une ville lisible d'un coup d'œil
    // sans qu'on ait à lire une légende.
    const bati = Object.keys(plan.bati || {}).map((k) => {
      const cat = (T[k] && T[k].cat) || "habitat";
      const n = (T[k] && T[k].n) || 0;
      // Les gros ensembles se distinguent des maisons : ils portent leur
      // propre classe, et restent visibles quand le menu s'éteint.
      const rare = n > 0 && n < 40 ? " rare" : "";
      return trace(plan.bati[k], "b b-" + cat + rare);
    }).join("");

    const svg =
      '<svg id="fond" viewBox="' + [x0, y0, x1 - x0, y1 - y0].join(" ") + '" ' +
      'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">' +
      '<rect class="sol" x="' + x0 + '" y="' + y0 + '" width="' + (x1 - x0) +
        '" height="' + (y1 - y0) + '"/>' +
      trace(plan.cote, "eau") +
      '<g class="niveaux">' +
        (plan.niveaux || []).map((n) => trace(n.d, "niveau")).join("") + "</g>" +
      '<g class="toile">' + trace(V.ruelle, "ruelle") + trace(V.abord, "ruelle") +
        trace(V.escalier, "ruelle") + "</g>" +
      '<g class="voies">' + trace(V.quai, "rue") + trace(V.rue, "rue") +
        trace(V.artere, "artere") + "</g>" +
      '<g class="bati">' + bati + "</g>" +
      '<g class="rempart">' + trace(R.courtine, "mur") + trace(R.tours, "mur") + "</g>" +
      '<g class="buts">' +
        '<circle class="but" cx="' + donjon.x + '" cy="' + donjon.y + '" r="60"/>' +
        '<circle class="but" cx="' + porte.x + '" cy="' + porte.y + '" r="34"/>' +
      "</g></svg>";

    fs.writeFileSync(path.join(this.dossier, "fond.svg"), svg, "utf8");
    return { bornes: [x0, y0, x1 - x0, y1 - y0],
             depart: Planches.cadre(porte, donjon) };
  }

  // DEUX CADRAGES, ET LA VILLE EST CELUI QU'ON GARDE. On ouvre sur l'action —
  // la porte et l'objectif, avec de la marge — parce qu'une bataille de trois
  // cents hommes vue de cinq kilomètres est trois cents pixels perdus. Mais le
  // recul va jusqu'aux bornes du plan, et c'est là qu'on voit ce qu'un sac
  // traverse.
  static cadre(porte, donjon) {
    const m = 420;
    const x0 = Math.min(porte.x, donjon.x) - m, x1 = Math.max(porte.x, donjon.x) + m;
    const y0 = Math.min(porte.y, donjon.y) - m, y1 = Math.max(porte.y, donjon.y) + m;
    return [x0, y0, x1 - x0, y1 - y0];
  }

  /** La page : quelques kilo-octets, qui vont chercher le fond. */
  page(o, plan) {
    const c = this.fond(o, plan);
    fs.writeFileSync(path.join(this.dossier, "index.html"), PAGE
      .replace("{{TITRE}}", o.hommes + " hommes · " + o.porte)
      .replace("{{BORNES}}", JSON.stringify(c.bornes))
      .replace("{{DEPART}}", JSON.stringify(c.depart))
      .replace("{{TEINTES}}", JSON.stringify(TEINTE))
      .replace("{{TRAITS}}", JSON.stringify(TRAIT))
      .replace("{{CHAQUE}}", String(this.chaque)), "utf8");
  }

  /**
   * Un instant, si l'heure en est venue. Rend vrai quand il a écrit.
   * Les positions sont arrondies au décimètre — c'est une planche, pas le
   * fichier cuit, et l'on divise le poids par deux pour un point de deux pixels.
   */
  peutetre(t, corps, releve, peur) {
    if (t < this.prochaine) return false;
    this.prochaine = t + this.chaque;
    const etats = releve();
    const x = [], y = [], e = [];
    for (const h of corps) {
      x.push(Math.round(h.x * 10) / 10);
      y.push(Math.round(h.y * 10) / 10);
      e.push(h.camp === "garde" && h.etat !== "mort" && h.etat !== "deroute"
             ? "garde" : (h.etat === "mort" || h.etat === "deroute" ? h.etat : "assaut"));
    }
    // LA VILLE, à part des corps en armes — parce qu'elle se dessine autrement
    // et parce qu'on veut pouvoir l'éteindre. Un habitant terré chez lui n'est
    // pas un habitant qui court : le premier se devine sous un toit, le second
    // est ce qu'on est venu voir.
    const px = [], py = [], pe = [];
    for (const p of (peur || [])) {
      px.push(Math.round(p.x * 10) / 10);
      py.push(Math.round(p.y * 10) / 10);
      pe.push(p.contre ? "guet" : (p.etat === "terre" ? "terre" : "fuite"));
    }
    const nom = "t" + String(Math.round(t)).padStart(5, "0") + ".json";
    fs.writeFileSync(path.join(this.dossier, nom),
                     JSON.stringify({ t: Math.round(t), x, y, e, etats,
                                      px, py, pe }));
    this.liste.push({ f: nom, t: Math.round(t) });
    // La liste se réécrit à chaque planche : c'est elle que la page interroge
    // pour savoir jusqu'où le four est allé.
    fs.writeFileSync(path.join(this.dossier, "liste.json"),
                     JSON.stringify({ planches: this.liste, fini: false }));
    return true;
  }

  /** Les rails suivis par les escouades, écrits une fois. */
  chemins(l) {
    fs.writeFileSync(path.join(this.dossier, "chemins.json"),
                     JSON.stringify(l || []));
  }

  fermer() {
    fs.writeFileSync(path.join(this.dossier, "liste.json"),
                     JSON.stringify({ planches: this.liste, fini: true }));
    return path.relative(ICI, path.join(this.dossier, "index.html"));
  }

  // LE FOUR SERT SES PROPRES PLANCHES, et ce n'est pas du luxe : la page va
  // chercher sa liste et ses instants par `fetch`, ce qu'un `file://` refuse.
  // Sans ce bout de serveur, il faudrait en lancer un à côté pour regarder —
  // c'est-à-dire ne jamais regarder.
  //
  // Il SURVIT à la cuisson, exprès : c'est au moment où le four s'arrête que
  // les planches deviennent une réglette qu'on tire. On rend la main par
  // Ctrl-C, et le message le dit.
  servir(port) {
    const T = { ".html": "text/html; charset=utf-8", ".json": "application/json" };
    const s = http.createServer((q, r) => {
      const nom = decodeURIComponent(q.url.split("?")[0]).replace(/^\/+/, "") || "index.html";
      // Un nom de fichier ne remonte pas d'un dossier : la même règle que
      // partout ailleurs dans le dépôt, et elle ne coûte qu'une ligne.
      if (!/^[\w.-]+$/.test(nom)) { r.writeHead(400); return r.end(); }
      const f = path.join(this.dossier, nom);
      fs.readFile(f, (e, d) => {
        if (e) { r.writeHead(404); return r.end(); }
        r.writeHead(200, { "content-type": T[path.extname(f)] || "text/plain",
                           "cache-control": "no-store" });
        r.end(d);
      });
    });
    // ON ESSAIE LE PORT SUIVANT. La première version renonçait dès que le port
    // était pris — et c'est arrivé au deuxième essai, parce qu'un four
    // précédent tenait encore le sien. Un outil qui se tait quand on relance
    // est un outil qu'on n'ouvre plus.
    return new Promise((ok) => {
      let p = port;
      s.on("error", () => {
        if (++p > port + 9) return ok(null);
        setImmediate(() => s.listen(p));
      });
      s.on("listening", () => ok("http://localhost:" + p + "/"));
      s.listen(p);
    });
  }
}

// ---------------------------------------------------------------------------
const PAGE = `<!doctype html><meta charset="utf-8"><title>{{TITRE}}</title>
<style>
  :root{
    --sol:#efe7d6;--eau:#b9d2d9;--voie:#a8926d;--mur:#8a8378;--encre:#3a2f22;
    --bati:#d9cbb0;--trait:rgba(110,85,50,.45);--niveau:rgba(150,120,70,.30);
    --habitat:#d9cbb0;--artisanat:#c08a5e;--commerce:#d6a93f;--plaisir:#b05a72;
    --service:#7fa08c;--civique:#8fa04e;--culte:#8c93bd;--institution:#a8443c;
    --nuisance:#6f6350;
  }
  @media (prefers-color-scheme:dark){
    :root{
      --sol:#1b1712;--eau:#1d2c33;--voie:#6d5c42;--mur:#6a6459;--encre:#e3d8c1;
      --bati:#2e2820;--trait:rgba(220,190,140,.22);--niveau:rgba(220,190,140,.16);
      --habitat:#2e2820;--artisanat:#4a3323;--commerce:#4d3d18;--plaisir:#42212c;
      --service:#25342e;--civique:#333a1e;--culte:#2f3245;--institution:#43201d;
      --nuisance:#2b2620;
    }
  }
  html,body{margin:0;height:100%;overflow:hidden;background:var(--sol);
    color:var(--encre);font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;}
  #scene{position:absolute;inset:0 0 46px 0;cursor:grab;touch-action:none;}
  #scene.tire{cursor:grabbing;}
  #porte-fond,#toile{position:absolute;inset:0;}
  #porte-fond svg,#toile{width:100%;height:100%;display:block;}
  /* LE RAIL. Un quart du chemin passe par des ruelles que le plan n'imprime
     plus au-delà de deux mètres par pixel — sans ce trait, la colonne marche
     sur du vide et l'on croit à un décalage. Il est pâle et pointillé : c'est
     une indication de lecture, pas un élément de la ville. */
  .rail{fill:none;stroke:#8c2f22;stroke-width:calc(1.6px * var(--mpp,4));
    opacity:.30;stroke-dasharray:calc(6px * var(--mpp,4)) calc(5px * var(--mpp,4));
    stroke-linecap:round;}
  .sol{fill:var(--sol);}
  .eau{fill:var(--eau);stroke:none;}
  .niveau{fill:none;stroke:var(--niveau);stroke-width:calc(1px * var(--mpp,4));}
  .artere{fill:none;stroke:var(--voie);stroke-width:9;}
  .rue{fill:none;stroke:var(--voie);stroke-width:5;opacity:.8;}
  .ruelle{fill:none;stroke:var(--voie);stroke-width:2.4;opacity:.5;}
  .mur{fill:none;stroke:var(--mur);stroke-width:7;}
  .but{fill:none;stroke:#8c2f22;stroke-width:calc(2px * var(--mpp,4));opacity:.5;}
  .b{stroke:var(--trait);stroke-width:calc(.5px * var(--mpp,4));}
  .b-habitat{fill:var(--habitat);} .b-artisanat{fill:var(--artisanat);}
  .b-commerce{fill:var(--commerce);} .b-plaisir{fill:var(--plaisir);}
  .b-service{fill:var(--service);} .b-civique{fill:var(--civique);}
  .b-culte{fill:var(--culte);} .b-institution{fill:var(--institution);}
  .b-nuisance{fill:var(--nuisance);}
  /* LE GRAIN, repris de carte-ville et pour les mêmes raisons : une maison de
     loin fait masse et reste juste, une ruelle de loin est un cheveu, et mille
     cheveux font un voile par-dessus la ville. */
  #fond.sans-toile .toile{display:none;}
  #fond.toile-pale .toile{opacity:.4;}
  #fond.loin .bati .b:not(.rare){display:none;}
  #barre{position:absolute;left:0;right:0;bottom:0;height:46px;display:flex;
    align-items:center;gap:1em;padding:0 1em;background:var(--sol);
    border-top:1px solid var(--trait);}
  #regle{flex:1 1 auto;}
  b{font-variant-numeric:tabular-nums;}
  #etats,#echelle{opacity:.6;}
  button{font:inherit;color:inherit;background:none;border:1px solid var(--trait);
    border-radius:3px;padding:.15em .5em;cursor:pointer;}
  button:hover{border-color:var(--encre);}
</style>
<div id="scene"><div id="porte-fond"></div><canvas id="toile"></canvas></div>
<div id="barre">
  <button id="debut" title="Revenir au début">⏮</button>
  <button id="lire" title="Lire la bataille">⏵</button>
  <button id="vitesse" title="Vitesse de lecture">×8</button>
  <button id="suivre" title="Coller à ce que le four vient de cuire">⤓</button>
  <input id="regle" type="range" min="0" max="0" value="0">
  <b id="heure">—</b><span id="etats"></span>
  <span id="ville-compte"></span><span id="echelle"></span>
  <button id="habitants">habitants</button><button id="ville">la ville</button><button id="action">l'action</button>
</div>
<script>
const BORNES = {{BORNES}}, DEPART = {{DEPART}};
const TEINTES = {{TEINTES}}, TRAITS = {{TRAITS}}, CHAQUE = {{CHAQUE}};
const scene = document.getElementById("scene");
const toile = document.getElementById("toile"), ctx = toile.getContext("2d");
const regle = document.getElementById("regle"), heure = document.getElementById("heure");
let svg = null, vue = DEPART.slice();
let planches = [], fini = false, suit = true, cache = new Map(), i = 0, courante = null;
let montreVille = true;

// --- le cadrage ------------------------------------------------------------
// Le SVG a preserveAspectRatio="xMidYMid meet" : son cadrage est CENTRÉ et
// laisse des marges. La toile doit reproduire ça exactement, sinon les corps
// marchent à côté de leurs rues — c'est la seule erreur qui se voit tout de
// suite, et c'est la même leçon que dans foule2d.
function repere(){
  const k = Math.min(toile.width / vue[2], toile.height / vue[3]);
  return {k, ox:(toile.width - vue[2]*k)/2 - vue[0]*k,
             oy:(toile.height - vue[3]*k)/2 - vue[1]*k};
}
function ajuster(){
  const r = scene.getBoundingClientRect(), d = window.devicePixelRatio || 1;
  toile.width = Math.round(r.width*d); toile.height = Math.round(r.height*d);
}
function grain(){
  if (!svg) return;
  const large = scene.getBoundingClientRect().width;
  if (!large) return;
  const mpp = vue[2] / large;
  svg.classList.toggle("loin", mpp > 12);
  svg.classList.toggle("sans-toile", mpp > 2);
  svg.classList.toggle("toile-pale", mpp > 1.2 && mpp <= 2);
  svg.style.setProperty("--mpp", mpp.toFixed(3));
  document.getElementById("echelle").textContent = mpp.toFixed(1) + " m/px";
}
function cadrer(){
  if (svg) svg.setAttribute("viewBox", vue.map((v)=>v.toFixed(1)).join(" "));
  grain(); peindre(courante);
}

// --- la molette et le glissé ----------------------------------------------
// On zoome VERS LE CURSEUR : sans ça, approcher d'un quartier demande de
// zoomer puis de rattraper au glissé, et l'on passe son temps à se rattraper.
scene.addEventListener("wheel", (e) => {
  e.preventDefault();
  const r = scene.getBoundingClientRect();
  const k = Math.min(r.width / vue[2], r.height / vue[3]);
  const mx = vue[0] + (e.clientX - r.left - (r.width - vue[2]*k)/2) / k;
  const my = vue[1] + (e.clientY - r.top - (r.height - vue[3]*k)/2) / k;
  const f = e.deltaY > 0 ? 1.18 : 1/1.18;
  const l = Math.max(60, Math.min(BORNES[2]*2, vue[2]*f));
  const h = l * vue[3] / vue[2];
  vue = [mx - (mx - vue[0]) * l/vue[2], my - (my - vue[1]) * h/vue[3], l, h];
  cadrer();
}, {passive:false});

let tire = null;
scene.addEventListener("pointerdown", (e) => {
  tire = {x:e.clientX, y:e.clientY, v:vue.slice()};
  scene.classList.add("tire"); scene.setPointerCapture(e.pointerId);
});
scene.addEventListener("pointermove", (e) => {
  if (!tire) return;
  const r = scene.getBoundingClientRect();
  const k = Math.min(r.width / tire.v[2], r.height / tire.v[3]);
  vue = [tire.v[0] - (e.clientX - tire.x)/k, tire.v[1] - (e.clientY - tire.y)/k,
         tire.v[2], tire.v[3]];
  cadrer();
});
for (const t of ["pointerup","pointercancel"])
  scene.addEventListener(t, () => { tire = null; scene.classList.remove("tire"); });
scene.addEventListener("dblclick", () => { vue = DEPART.slice(); cadrer(); });
document.getElementById("ville").addEventListener("click", () => {
  vue = BORNES.slice(); cadrer(); });
document.getElementById("action").addEventListener("click", () => {
  vue = DEPART.slice(); cadrer(); });
document.getElementById("habitants").addEventListener("click", (e) => {
  montreVille = !montreVille;
  e.target.style.opacity = montreVille ? 1 : .45;
  peindre(courante); });

// --- les corps -------------------------------------------------------------
function peindre(p){
  courante = p;
  if (!p || !toile.width) return;
  const rep = repere(), d = window.devicePixelRatio || 1;
  ctx.clearRect(0,0,toile.width,toile.height);
  // Un homme fait un demi-mètre : de loin il vaut un huitième de pixel. On ne
  // triche pas sur sa position, seulement sur sa taille à l'écran — sinon une
  // armée de trois cents hommes est rigoureusement invisible.
  const r = Math.max(1.5*d, Math.min(4*d, rep.k*0.55));
  const L = toile.width + 8, H = toile.height + 8;
  // LA VILLE D'ABORD, SOUS LE FER. Elle est le décor de ce qui se passe, pas
  // le sujet : un fuyard dessiné par-dessus un soldat ferait croire à un
  // corps à corps là où il n'y a qu'une rue qu'on traverse.
  if (montreVille && p.px) {
    const rv = Math.max(1.2*d, r*0.7);
    for (let n=0;n<p.px.length;n++){
      const x = rep.ox + p.px[n]*rep.k, y = rep.oy + p.py[n]*rep.k;
      if (x < -8 || y < -8 || x > L || y > H) continue;
      const e = p.pe[n];
      ctx.globalAlpha = e === "terre" ? .45 : .9;
      ctx.fillStyle = TEINTES[e] || TEINTES.fuite;
      ctx.beginPath(); ctx.arc(x, y, rv, 0, 6.2832); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
  // les morts d'abord, sous les vivants — sinon un charnier cache la mêlée
  for (const mort of [true,false]) for (let n=0;n<p.x.length;n++){
    const e = p.e[n];
    if ((e === "mort") !== mort) continue;
    const x = rep.ox + p.x[n]*rep.k, y = rep.oy + p.y[n]*rep.k;
    if (x < -8 || y < -8 || x > L || y > H) continue;
    ctx.globalAlpha = e === "mort" ? .5 : 1;
    // UN DISQUE DESSOUS, PAS UN TRAIT AUTOUR. Le contour était un trait
    // d'un pixel sur un point de trois : à moitié dedans, à moitié dehors, et
    // l'anticrénelage le mélangeait si bien au remplissage qu'il n'existait
    // pas — mesuré, zéro pixel à la couleur du trait. Un disque un peu plus
    // grand posé DESSOUS donne un anneau franc, opaque, de la largeur qu'on
    // veut, et coûte moins cher qu'un tracé.
    // ET SANS SEUIL, OU PRESQUE. J'en avais mis un à deux pixels, en croyant
    // qu'un anneau demandait de la place — or un homme fait 0,55 m, donc 1,5 à
    // 1,8 pixel aux échelles où l'on regarde une bataille : le seuil n'était
    // jamais atteint et le contour n'a jamais été tracé une seule fois.
    // L'anneau n'occupe pas le point, IL L'AGRANDIT : un cœur de 1,5 pixel
    // dans une bordure sombre en fait 3,5, et c'est ce qui le détache d'un
    // toit de brique.
    if (e !== "mort") {
      ctx.fillStyle = TRAITS[e] || TRAITS.assaut;
      ctx.beginPath(); ctx.arc(x, y, r + Math.max(1, r*0.45), 0, 6.2832); ctx.fill();
    }
    ctx.fillStyle = TEINTES[e] || TEINTES.assaut;
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
  }
  ctx.globalAlpha = 1;
  const m = Math.floor(p.t/60), s = p.t%60;
  heure.textContent = m + "′" + String(s).padStart(2,"0");
  document.getElementById("etats").textContent =
    Object.entries(p.etats||{}).map(([k,v])=>k+" "+v).join("  ");
  const nf = p.pe ? p.pe.filter((e)=>e!=="terre").length : 0;
  document.getElementById("ville-compte").textContent =
    p.px && p.px.length ? nf + " en fuite, " + (p.px.length-nf) + " terrés" : "";
}
async function charger(n){
  const f = planches[n]; if (!f) return null;
  if (cache.has(f.f)) return cache.get(f.f);
  const p = await (await fetch(f.f)).json();
  cache.set(f.f, p); return p;
}
async function montrer(n){ i = n; regle.value = n; peindre(await charger(n)); }
async function battre(){
  try{
    const l = await (await fetch("liste.json?" + Date.now())).json();
    planches = l.planches; fini = l.fini;
    regle.max = Math.max(0, planches.length - 1);
    if (suit) await montrer(planches.length - 1);
    majBoutons();
  }catch(e){}
  setTimeout(battre, fini ? 4000 : 900);
}
// --- LIRE ------------------------------------------------------------------
// Trois gestes différents, qu'on confondait dans un seul bouton : SUIVRE le
// four (coller à ce qui vient d'être cuit), LIRE (avancer dans le temps de la
// bataille), et tirer la réglette à la main. Le premier n'a de sens que
// pendant la cuisson, les deux autres après — et vouloir les servir tous les
// trois avec « ⏵ suivre le four » ne servait bien aucun des trois.
//
// LA VITESSE EST CELLE DE LA BATAILLE, pas un nombre de planches par seconde.
// ×1, c'est une seconde de Port-Réal par seconde de la nôtre ; à une planche
// toutes les CHAQUE secondes, cela fait une planche toutes les CHAQUE
// secondes réelles. On lit donc un assaut à sa vraie allure, ce qui est plus
// instructif qu'on ne croit — un quart d'heure de marche EST un quart d'heure.
const VITESSES = [1, 2, 4, 8, 16, 60];
let iv = 3, lit = false, dernierT = 0;

function majBoutons(){
  document.getElementById("lire").textContent = lit ? "⏸" : "⏵";
  document.getElementById("vitesse").textContent = "×" + VITESSES[iv];
  document.getElementById("suivre").style.opacity = suit ? 1 : .4;
}
// UN INTERVALLE, PAS UNE IMAGE. requestAnimationFrame est fait pour animer
// en continu ; ici l'on fait défiler des planches discrètes, espacées de
// plusieurs secondes de bataille. L'intervalle est donc l'outil juste — et il
// a un second mérite : il bat dans un onglet caché, là où l'image ne bat pas.
// La lecture ne s'arrête donc pas parce qu'on a changé de fenêtre, et elle
// s'éprouve sans avoir à regarder l'écran.
function boucle(){
  const ts = performance.now();
  if (lit) {
    if (!dernierT) dernierT = ts;
    const ecoule = (ts - dernierT) / 1000 * VITESSES[iv];   // secondes de bataille
    const pas = Math.floor(ecoule / CHAQUE);
    if (pas >= 1) {
      // ON REPORTE LE RESTE, on ne le jette pas. En remettant l'horloge à
      // l'instant courant, on perdait tout ce qui n'avait pas suffi à faire
      // une planche de plus — et la lecture rendait ×5 quand le bouton
      // annonçait ×8. Une vitesse qui ment est pire que pas de vitesse du
      // tout : on croit avoir mesuré une durée, et l'on s'est trompé d'un
      // tiers.
      dernierT += pas * CHAQUE / VITESSES[iv] * 1000;
      const n = i + pas;
      if (n >= planches.length) {
        // Au bout : on s'arrête sur la dernière si le four a fini, on colle à
        // la tête s'il travaille encore — c'est ce qu'on veut dans les deux cas.
        if (fini) { lit = false; montrer(planches.length - 1); majBoutons(); }
        else { suit = true; montrer(planches.length - 1); majBoutons(); }
      } else montrer(n);
    }
  }
}
setInterval(boucle, 80);

document.getElementById("lire").addEventListener("click", () => {
  lit = !lit; dernierT = 0;
  if (lit) { suit = false; if (i >= planches.length - 1) i = 0; }
  majBoutons();
});
document.getElementById("vitesse").addEventListener("click", () => {
  iv = (iv + 1) % VITESSES.length; majBoutons();
});
document.getElementById("debut").addEventListener("click", () => {
  suit = false; montrer(0); majBoutons();
});
document.getElementById("suivre").addEventListener("click", () => {
  suit = !suit; if (suit) { lit = false; montrer(planches.length - 1); }
  majBoutons();
});
regle.addEventListener("input", () => { suit = false; lit = false;
  montrer(+regle.value); majBoutons(); });
window.addEventListener("resize", () => { ajuster(); cadrer(); });

fetch("fond.svg").then((r)=>r.text()).then(async (t)=>{
  document.getElementById("porte-fond").innerHTML = t;
  svg = document.getElementById("fond");
  // Le rail se pose DANS le SVG, donc il se cadre tout seul avec lui et l'on
  // n'a pas une seconde projection à tenir juste.
  try{
    const l = await (await fetch("chemins.json")).json();
    if (l.length) {
      const g = document.createElementNS("http://www.w3.org/2000/svg","g");
      g.setAttribute("class","rails");
      for (const pts of l) {
        const d = "M" + pts.map((p)=>p[0]+" "+p[1]).join("L");
        const e = document.createElementNS("http://www.w3.org/2000/svg","path");
        e.setAttribute("class","rail"); e.setAttribute("d", d);
        g.appendChild(e);
      }
      // sous les repères, par-dessus le bâti
      svg.insertBefore(g, svg.querySelector(".buts"));
    }
  }catch(e){}
  ajuster(); cadrer(); battre();
});
</script>
`;

// ---------------------------------------------------------------------------
// REVOIR DES PLANCHES DÉJÀ CUITES, sans rien recuire.
//
//     node scripts/monde/sac_planches.js            (le dernier dossier cuit)
//     node scripts/monde/sac_planches.js vue        (celui qu'on nomme)
//
// Le serveur vit dans le processus du four : il meurt avec lui, et l'on perd
// la réglette au moment précis où l'on voulait s'en servir — c'est arrivé, et
// c'était une fin de cuisson, pas une panne. Les planches, elles, restent sur
// le disque. Les reservir ne demande qu'un port.
if (require.main === module) {
  const nom = process.argv[2];
  const dossier = nom ? path.join(DESSINS, nom) : (() => {
    if (!fs.existsSync(DESSINS)) return null;
    const l = fs.readdirSync(DESSINS)
      .map((d) => ({ d, t: fs.statSync(path.join(DESSINS, d)).mtimeMs }))
      .sort((a, b) => b.t - a.t);
    return l.length ? path.join(DESSINS, l[0].d) : null;
  })();
  if (!dossier || !fs.existsSync(path.join(dossier, "index.html"))) {
    process.stderr.write("planches : rien à revoir dans " + DESSINS + "\n" +
      "  (cuire avec « node scripts/monde/sac.js --planches 5 »)\n");
    process.exit(1);
  }
  const p = Object.create(Planches.prototype);
  p.dossier = dossier;
  // ON REDESSINE LE FOND AVANT DE SERVIR, quand un serveur est là pour donner
  // le plan. C'est la ville qui bouge, pas les planches : les positions cuites
  // restent vraies, mais les rues et les toits qu'on peint dessous datent du
  // jour de la cuisson. Un coup de « --fond » et l'on regarde la même bataille
  // sur la ville d'aujourd'hui.
  const refaire = process.argv.includes("--fond");
  const four = (() => { try {
    return JSON.parse(fs.readFileSync(path.join(dossier, "four.json"), "utf8"));
  } catch (e) { return null; } })();
  const pret = (refaire && four)
    ? fetch((process.env.SERVEUR || "http://localhost:3129") + "/monde/plan2d")
        .then((r) => r.json())
        .then((plan) => { p.chaque = four.chaque || 4; p.page(four, plan);
                          process.stdout.write("fond redessine" + String.fromCharCode(10)); })
        .catch((e) => process.stderr.write("fond : " + e.message + " (le serveur du jeu tourne-t-il ?)" + String.fromCharCode(10)))
    : Promise.resolve();
  pret.then(() => p.servir(+process.env.PORT || 3150)).then((ou) => {
    process.stdout.write(ou
      ? path.basename(dossier) + " — " + ou + "\nCtrl-C pour rendre la main.\n"
      : "planches : aucun port libre entre 3150 et 3159\n");
    if (!ou) process.exit(1);
  });
}

module.exports = { Planches };
