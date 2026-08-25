(() => {
"use strict";
// ─────────────────────────────────────────────────────────────────────────────
// CE N'EST PAS UN SIMULATEUR DE BATAILLE, C'EST UN SIMULATEUR DE CERVEAU.
//
// La version d'avant dressait cinq hommes, des positions, des coups portés, des
// camps — et tout ce décor CACHAIT ce qu'on voulait voir. On passait son temps
// à déboguer le placement des figurants au lieu de regarder la machine.
//
// Ici il n'y a qu'UN homme, aucune position, aucun combat. Trois choses :
//
//   LE GRAPHE — les deux pistes, le score de chaque geste en direct, ce qui est
//     atteignable depuis l'état courant, et ce qui est INTERDIT (en pointillé
//     rouge : ce sont les affirmations du modèle, il faut les voir).
//   LE JOURNAL — une ligne par battement où quelque chose a bougé, et rien
//     quand rien ne bouge.
//   LE PUPITRE — de quoi fabriquer n'importe quelle situation à la main, et
//     envoyer n'importe quel stimulus quand on veut.
//
// La page ne contient AUCUNE règle : tout vient de `survival-stack/1-corps.js`.
// Elle affiche, elle ne décide pas.
// ─────────────────────────────────────────────────────────────────────────────
const C = window.Corps, PAS = 1 / 20;
let _s = 20161219;
const R = () => (_s = (_s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
const $ = (id) => document.getElementById(id);
const num = (id) => +$(id).value;
const n2 = (x) => (x >= 0 ? "+" : "") + x.toFixed(2).replace(".", ",");

// ---------------------------------------------------------------------------
// LE GRAPHE
// ---------------------------------------------------------------------------
// On ne dessine PAS les trente arêtes du modèle : on dessine celles qui partent
// de l'état COURANT. C'est la seule chose qu'on ait besoin de savoir à cet
// instant-là, et c'est ce qui rend la machine lisible d'un coup d'œil.
// L'épaisseur d'une arête est le score de sa cible : on voit qui pousse.
const POSE = {
  jambes: { cx: 0.30, cy: 0.52, rx: 0.20, ry: 0.34, titre: "les jambes" },
  bras:   { cx: 0.75, cy: 0.52, rx: 0.15, ry: 0.28, titre: "les bras" },
};
const noeuds = {};

function batir() {
  const g = $("graphe");
  for (const [piste, p] of Object.entries(POSE)) {
    const liste = piste === "jambes" ? C.JAMBES : C.BRAS;
    const t = document.createElement("div");
    t.className = "titre"; t.textContent = p.titre;
    t.style.left = (p.cx * 100) + "%"; t.style.top = "6px";
    g.appendChild(t);
    liste.forEach((nom, i) => {
      const a = -Math.PI / 2 + (i / liste.length) * Math.PI * 2;
      const d = document.createElement("div");
      d.className = "noeud";
      d.style.left = ((p.cx + Math.cos(a) * p.rx) * 100) + "%";
      d.style.top = ((p.cy + Math.sin(a) * p.ry) * 100) + "%";
      d.innerHTML = '<div class="rond"><div class="jauge"></div>' +
                    '<div class="nom">' + nom + '</div></div>' +
                    '<div class="score">—</div>';
      g.appendChild(d);
      noeuds[piste + "|" + nom] = d;
    });
  }
}

function peindre(tj, tb) {
  const g = $("graphe").getBoundingClientRect();
  const svg = $("aretes");
  svg.setAttribute("viewBox", "0 0 " + g.width + " " + g.height);
  const centre = (el) => {
    const b = el.getBoundingClientRect();
    return [b.left + b.width / 2 - g.left, b.top + b.height / 2 - g.top];
  };
  let d = '<defs><marker id="fleche" viewBox="0 0 8 8" refX="7" refY="4" ' +
          'markerWidth="5" markerHeight="5" orient="auto">' +
          '<path d="M0,0 L8,4 L0,8 z" fill="#e8c15a"/></marker></defs>';

  for (const piste of ["jambes", "bras"]) {
    const liste = piste === "jambes" ? C.JAMBES : C.BRAS;
    const table = piste === "jambes" ? tj : tb;
    const courant = (piste === "jambes" ? corps.jambes : corps.bras) ||
                    (piste === "jambes" ? "planté" : "garde");
    const interdits = piste === "jambes" ? C.INTERDIT_JAMBES : C.INTERDIT_BRAS;
    const max = Math.max(1e-6, ...liste.map((x) => table[x] || 0));

    for (const nom of liste) {
      const el = noeuds[piste + "|" + nom];
      const v = table[nom] || 0;
      const barre = (interdits[courant] || new Set()).has(nom);
      el.classList.toggle("actif", nom === courant);
      el.classList.toggle("barre", barre && nom !== courant);
      el.querySelector(".jauge").style.height = Math.round((v / max) * 100) + "%";
      el.querySelector(".score").textContent = v.toFixed(3);
    }

    // ---- LE GRAPHE ENTIER, ET PAS UNE ÉTOILE ------------------------------
    // On ne dessinait que les arêtes partant de l'état courant. Comme cet état
    // est presque toujours `planté` ou `garde`, on voyait toujours la même
    // étoile — donc rien de la MACHINE, seulement de l'instant. Un graphe qui
    // ne montre pas sa structure n'est pas un graphe.
    //
    // On trace donc TOUTES les transitions dirigées, en trois régimes :
    //   pâle          — la structure, ce que la machine permet en général ;
    //   or et fléché  — ce qui part de l'état courant, épais comme le score de
    //                   sa cible : on voit qui pousse, maintenant ;
    //   rouge tireté  — les INTERDITES, qui sont les affirmations du modèle et
    //                   qu'il faut voir même quand on n'y est pas.
    //
    // Chaque paire est courbée du côté de son sens, sinon a→b et b→a se
    // superposent et l'on ne distingue plus l'aller du retour.
    for (const a of liste) for (const b of liste) {
      if (a === b) continue;
      const [x1, y1] = centre(noeuds[piste + "|" + a]);
      const [x2, y2] = centre(noeuds[piste + "|" + b]);
      const dx = x2 - x1, dy = y2 - y1, n = Math.hypot(dx, dy) || 1;
      // Le décalage perpendiculaire : un huitième de la longueur, toujours du
      // même côté relatif au sens — donc l'aller et le retour se séparent.
      const mx = (x1 + x2) / 2 - dy / n * n * 0.10;
      const my = (y1 + y2) / 2 + dx / n * n * 0.10;
      // On s'arrête au bord du nœud, pas au centre : sinon la flèche se cache
      // sous la boîte de destination.
      const rec = 34;
      const ex = x2 - dx / n * rec, ey = y2 - dy / n * rec;
      const sx = x1 + dx / n * rec, sy = y1 + dy / n * rec;
      const chemin = "M" + sx + "," + sy + " Q" + mx + "," + my + " " + ex + "," + ey;
      const bloque = (interdits[a] || new Set()).has(b);
      const depuisIci = a === courant;
      let trait;
      if (bloque) {
        trait = '<path d="' + chemin + '" fill="none" stroke="#6d3129" ' +
          'stroke-opacity="' + (depuisIci ? 0.75 : 0.22) + '" stroke-width="' +
          (depuisIci ? 1.4 : 1) + '" stroke-dasharray="3 4"/>';
      } else if (depuisIci) {
        const v = table[b] || 0;
        trait = '<path d="' + chemin + '" fill="none" stroke="#e8c15a" ' +
          'stroke-opacity="' + Math.max(0.2, (v / max) * 0.9) + '" stroke-width="' +
          Math.max(1, (v / max) * 4) + '" marker-end="url(#fleche)"/>';
      } else {
        trait = '<path d="' + chemin + '" fill="none" stroke="#3a352d" ' +
          'stroke-opacity="0.5" stroke-width="1"/>';
      }
      d += trait;
    }
  }
  svg.innerHTML = d;
}

// ---------------------------------------------------------------------------
const lignes = [];
function journal(t, html) {
  lignes.push('<div class="l"><span class="t">' +
    t.toFixed(2).padStart(5) + "</span> " + html + "</div>");
  if (lignes.length > 500) lignes.shift();
  const c = $("logCorps"); c.innerHTML = lignes.join(""); c.scrollTop = c.scrollHeight;
}

function cadran(nom, v, min, max, teinte, note) {
  const p = Math.max(0, Math.min(1, (v - min) / (max - min)));
  return '<div class="cad">' + nom + " <b style='color:#d9d2c4'>" +
    v.toFixed(2).replace(".", ",") + "</b>" +
    (note ? "<br><span style='color:#5f594e'>" + note + "</span>" : "") +
    '<div class="bar"><i style="width:' + (p * 100) + '%;background:' + teinte + '"></i></div></div>';
}

// ---------------------------------------------------------------------------
// L'HOMME
// ---------------------------------------------------------------------------
let corps, t = 0, tourne = true, enAttente = [], vuDernier = null, prochainRepet = 0;

function remise() {
  corps = { dressage: num("dressage"), vecu: num("vecu") };
  t = 0; enAttente = []; vuDernier = null; prochainRepet = 0;
  lignes.length = 0; $("logCorps").innerHTML = "";
  journal(0, '<span class="ch">— la machine repart à zéro —</span>');
}

// LES SIGNAUX PASSENT PAR LES VRAIES FONCTIONS DU MODÈLE. Il n'y a volontairement
// pas de curseur « menace » ni « intégrité » : ce serait court-circuiter
// exactement ce qu'on est en train de tester. On règle le MONDE (combien
// d'hommes, à quelle distance, de quel côté), et le modèle en tire ce qu'un
// corps en perçoit.
function signaux() {
  const dist = num("dist"), cote = num("cote"), enn = num("ennemis");
  const proches = [];
  for (let i = 0; i < enn; i++)
    proches.push({ distance: dist + i * 0.6, deFace: cote, frappe: i === 0 });
  // La couverture, le coude, la contagion et l'imitation sont calculés par
  // `pas()` lui-même : il leur faut le CONTEXTE — la nuit, le vacarme, la
  // surdité —, et le contexte n'existe que là-bas. On se contente de passer les
  // voisins.
  return {
    integrite: C.integrite(num("vie"), num("coup")),
    souffle:   C.souffle(num("souffle")),
    // TROIS SIGNAUX LA OU IL Y AVAIT UN COMPTE. `appui` valait `tanh(amis -
    // ennemis)` : le bord d'une ligne et son milieu rendaient le meme nombre.
    // Le pourtour les separe, le coude dit s'il TOUCHE quelqu'un, et la
    // contagion fait entrer la peur des autres — la seule entree du plancher
    // qui vienne du dehors.
    menace:    C.menace(proches),
    issue:     C.issue(num("issue")),
    aPortee:   $("aportee").checked,
    ennemisProches: enn,
  };
}

// OU SONT LES SIENS — et c'est tout ce qui separe un homme du milieu du rang
// d'un homme du bout. Les angles sont RELATIFS a son cap : 0 droit devant,
// pi/2 a sa gauche, pi derriere. Aucun nom, aucun compte : des formes autour.
const DISPOSITIONS = {
  milieu:   (i) => [(i % 2 ? 1 : -1) * Math.PI / 2 + (i > 1 ? 0.5 : 0), 0.9 + i * 0.25],
  bout:     (i) => [Math.PI / 2 + i * 0.45, 0.9 + i * 0.3],
  devant:   (i) => [(i % 2 ? 1 : -1) * (0.2 + i * 0.12), 1.0 + i * 0.2],
  autour:   (i) => [i * (2 * Math.PI / Math.max(1, num("amis"))), 1.0],
  derriere: (i) => [Math.PI + (i % 2 ? 1 : -1) * (0.3 + i * 0.15), 1.0 + i * 0.2],
};
function voisins() {
  const n = num("amis"), f = DISPOSITIONS[$("rang").value] || DISPOSITIONS.milieu;
  // ON NE LEUR DONNE PLUS D'ALARME, ON LEUR DONNE UN GESTE. La v1 passait
  // `réflexe` — la variable INTÉRIEURE du voisin —, c'est-à-dire de la
  // télépathie dans la couche dont toute la discipline tient en une phrase : le
  // corps ne perçoit que des signes. On ne voit pas la peur d'un homme, on voit
  // qu'il recule, qu'il a lâché son bouclier, qu'il ne bouge plus.
  const v = $("leur").value;
  const out = [];
  for (let i = 0; i < n; i++) {
    const [a, d] = f(i);
    let j = "planté", b = "garde";
    if (v === "un-rompt") { if (i === n - 1) { j = "fuite"; b = "ballants"; } }
    else if (v === "frapper") { b = "frapper"; }
    else { const q = v.split("|"); j = q[0]; b = q[1] || "garde"; }
    out.push({ angle: a, distance: d, ami: true, memeGroupe: true, jambes: j, bras: b });
  }
  return out;
}

const FABRIQUE = {
  coup:    (f) => C.coupRecu(f * 2 * num("coup"), num("coup"), num("cote"), 1),
  frole:   (f) => C.coupFrole(0.45 + (1 - f) * 0.45, 0.45, num("cote")),
  fer:     (f) => C.ferQuiVient(0.05 + (1 - f) * 0.9, num("cote")),
  tombe:   (f) => C.voisinTombe(0.4 + (1 - f) * 5, num("cote"), true),
  partent: (f) => C.voisinPart(Math.max(1, Math.round(f * Math.max(1, num("amis")))),
                               Math.max(1, num("amis"))),
  dos:     (f) => C.dansLeDos(0.6 + (1 - f) * 3, -1, f),
};
const NOMS = { coup: "un coup le touche", frole: "un coup le frôle",
  fer: "un fer part vers lui", tombe: "son voisin tombe",
  partent: "les siens s'en vont", dos: "quelqu'un dans son dos" };

function envoyer(quoi) {
  const st = FABRIQUE[quoi](num("f" + quoi));
  st.t = t;
  enAttente.push(st);
  journal(t, '<span class="stim">▸ ' + NOMS[quoi] + "</span> " +
    '<span class="ch">(' + st.canal + " · force " + st.force.toFixed(2) +
    " · soudaineté " + st.soudainete.toFixed(2) + " · perçu dans " +
    Math.round(C.LATENCE[st.canal] * 1000) + " ms)</span>");
}

function battre() {
  corps.dressage = num("dressage"); corps.vecu = num("vecu");
  const s = signaux();
  // Un stimulus vit le temps de sa latence, plus un battement : après quoi il a
  // été perçu (ou il ne le sera jamais) et il sort de la boîte.
  enAttente = enAttente.filter((st) => t <= st.t + C.LATENCE[st.canal] + PAS);
  const av = { j: corps.jambes, b: corps.bras };
  const r = C.pas(corps, { t, dt: PAS, stimuli: enAttente, signaux: s,
    voisins: voisins(), nuit: $("nuit").checked, presse: num("presse") }, R());
  t += PAS;

  if (r.saillant) {
    const clef = r.saillant + "|" + r.saillance.toFixed(3);
    if (clef !== vuDernier) {
      vuDernier = clef;
      const sourd = r.saillance < 0.02;
      journal(t, '<span class="' + (sourd ? "sourd" : "stim") + '">' +
        (sourd ? "▪ " : "● ") + r.saillant + "</span> <span class='ch'>saillance " +
        r.saillance.toFixed(3) + (sourd ? " — il ne l'a pas senti" : "") + "</span>");
    }
  }
  if (av.j !== r.jambes || av.b !== r.bras) {
    journal(t, '<span class="bascule">' + (av.j || "?") + " · " + (av.b || "?") +
      "  →  " + r.jambes + " · " + r.bras + "</span>");
    journal(t, '<span class="ph">' + r.phrase + "</span>");
  }
}

// ---------------------------------------------------------------------------
// La simulation a son horloge, l'affichage suit. `requestAnimationFrame` ne bat
// pas dans un onglet caché — le temps du monde ne doit pas en dépendre.
let dernierTic = performance.now(), reste = 0;
function avancer() {
  const now = performance.now();
  const dt = Math.min(0.5, (now - dernierTic) / 1000); dernierTic = now;
  if (!tourne) return;
  reste += dt;
  while (reste >= PAS) {
    if ($("repeter").classList.contains("on") && t >= prochainRepet) {
      prochainRepet = t + +$("periode").value;
      envoyer($("repeter").dataset.quoi || "frole");
    }
    battre(); reste -= PAS;
  }
  $("horloge").textContent = t.toFixed(2).replace(".", ",") + " s";
}

function rendre() {
  const s = signaux();
  // L'affichage montre le régime CONTINU — les appels hors sursaut. Le pic d'un
  // stimulus passe dans le journal, pas dans les jauges : sinon elles
  // clignoteraient trois images et l'on ne lirait plus rien.
  const ctx = { sangFroid: corps.sangFroid == null ? 1 : corps.sangFroid,
                nuit: $("nuit").checked, presse: num("presse"),
                vacarme: C.vacarme(num("presse"), num("ennemis")) };
  const vs = voisins(), sg = C.signes(vs, ctx);
  s.appui = C.couverture(vs); s.coude = C.coude(vs);
  s.contagion = sg.contagion; s.imitation = sg.imitation;
  const ap = C.appels(s, null), ac = C.acquis(corps);
  const tj = {}, tb = {};
  for (const g of C.JAMBES) tj[g] = ((ap[g] + 1) / 2) * ((ac[g] + 1) / 2);
  for (const g of C.BRAS)   tb[g] = ((ap[g] + 1) / 2) * ((ac[g] + 1) / 2);
  peindre(tj, tb);

  const a = corps.sangFroid == null ? 1 : corps.sangFroid;
  const h = corps.hab || { tact: 0, ouie: 0, vue: 0 };
  const vac = C.vacarme(num("presse"), num("ennemis"));
  $("cadrans").innerHTML =
    cadran("sang-froid", a, -1, 1, "#e8c15a", "+1 à froid · −1 la glande a la main") +
    cadran("emprise du corps", C.emprise(a, corps), 0, 1, "#e0705c", "sur les couches 2·3·4") +
    cadran("exposition", corps.exposition || 0, 0, 1, "#c85a45", "la bouffée de corps-à-corps") +
    cadran("charge nerveuse", corps.chargeNerveuse || 0, 0, 1, "#a88fc4", "ce qui reste entre deux bouffées") +

    cadran("intégrité", s.integrite, -1, 1, "#8c2f22",
      (num("vie") / num("coup")).toFixed(2) + " coups encaissables") +
    cadran("couverture", s.appui, -1, 1, "#7fa8c4", "le pourtour, pas un compte") +
    cadran("coude", s.coude, -1, 1, "#7fa8c4", "touche-t-il quelqu'un") +
    cadran("contagion", s.contagion == null ? 1 : s.contagion, -1, 1, "#a88fc4",
      "ce qu'ils MONTRENT, par les canaux") +
    cadran("imitation", Math.max(0, ...Object.values(sg.imitation), 0), 0, 1, "#a88fc4",
      Object.entries(sg.imitation).sort((a, b) => b[1] - a[1])
        .slice(0, 2).map(([g, x]) => g + " " + x.toFixed(2)).join(" · ") || "—") +
    cadran("menace", s.menace, -1, 1, "#c98a5a") +
    cadran("habituation tact", h.tact, 0, 1, "#6f675b") +
    cadran("habituation ouïe", h.ouie, 0, 1, "#6f675b",
      "vacarme " + vac.toFixed(2) + " · surdité " + C.surdite(a).toFixed(2)) +
    cadran("habituation vue", h.vue, 0, 1, "#6f675b",
      $("nuit").checked ? "nuit : gain 0,32" : "plein jour");
}

// ---------------------------------------------------------------------------
$("marche").onclick = (e) => {
  tourne = !tourne; e.target.classList.toggle("on", tourne);
  e.target.textContent = tourne ? "Marche" : "Arrêt";
  dernierTic = performance.now(); reste = 0;
};
$("unpas").onclick = () => {
  tourne = false; $("marche").classList.remove("on"); $("marche").textContent = "Arrêt";
  battre(); $("horloge").textContent = t.toFixed(2).replace(".", ",") + " s";
};
$("remise").onclick = remise;
document.querySelectorAll("[data-st]").forEach((b) => {
  b.onclick = () => { envoyer(b.dataset.st); $("repeter").dataset.quoi = b.dataset.st; };
});
$("repeter").onclick = (e) => { e.target.classList.toggle("on"); prochainRepet = t; };

const AFFICHE = {
  dressage: n2, vecu: n2,
  vie: (v) => v.toFixed(0), coup: (v) => v.toFixed(0),
  souffle: (v) => v.toFixed(2).replace(".", ","),
  amis: (v) => v.toFixed(0), ennemis: (v) => v.toFixed(0),
  dist: (v) => v.toFixed(1).replace(".", ",") + " m",
  cote: (v) => (v > 0.5 ? "de face" : v > -0.3 ? "de flanc" : "dans le dos"),
  issue: (v) => v.toFixed(2).replace(".", ","), presse: (v) => v.toFixed(0),
};
for (const id of Object.keys(AFFICHE)) {
  const maj = () => { const e = $("v" + id); if (e) e.textContent = AFFICHE[id](num(id)); };
  $(id).addEventListener("input", maj); maj();
}

batir(); remise();
// LES DEUX HORLOGES SONT DES `setInterval`, ET C'EST VOULU. `requestAnimationFrame`
// ne bat pas dans un onglet caché — or ce banc se regarde dans un volet latéral,
// où il est justement caché. La simulation restait à zéro, puis le graphe est
// resté vide : deux fois le même piège. Sur un banc, ni le temps du monde ni
// l'affichage ne doivent dépendre de la composition d'images.
setInterval(avancer, PAS * 1000);   // le monde, à 20 Hz
setInterval(rendre, 100);           // l'œil, à 10 Hz — c'est bien assez
})();
