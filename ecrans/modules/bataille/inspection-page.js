(() => {
"use strict";
const $ = (id) => document.getElementById(id);

function creer(etat) {
// ═══ SOUS LE DOIGT — LA MÊME TRACE QUE DANS LA CARTE DU JEU ═══════════════
let sousCourant = null, sousCle = null, sousMasque = null;
const echapper = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function installerLoupe() {
  const h = $("toile");
  if (!$("sbulle")) {
    const b = document.createElement("div"); b.id = "sbulle"; h.appendChild(b);
    // La carte et la bulle sont séparées de quelques pixels. Sans ce sas, le
    // `mousemove` intermédiaire ne trouve plus l'homme et détruit la bulle
    // avant que le pointeur puisse atteindre Mark.
    b.addEventListener("mouseenter", () => {
      if (sousMasque) { clearTimeout(sousMasque); sousMasque = null; }
    });
    b.addEventListener("mouseleave", () => programmerMasque(280));
  }
  if (!$("smark")) {
    const d = document.createElement("div"); d.id = "smark";
    d.innerHTML = '<h3></h3><div class="instant"></div>' +
      '<label>Qu’est-ce qui vous paraît faux ou intéressant ?' +
      '<textarea rows="5" maxlength="8000" placeholder="Ex. Il avance seul alors que sa vintaine attend."></textarea></label>' +
      '<div class="actions"><button class="annuler" type="button">Annuler</button>' +
      '<button class="sauver" type="button">Enregistrer la marque</button></div>' +
      '<div class="statut" aria-live="polite"></div>';
    h.appendChild(d);
  }
}

// Une ancienne épreuve ne connaît pas forcément encore son `focus`. Dans ce
// cas, cadrer toute la ville rend son sujet introuvable. On choisit le front
// local : d'abord les hommes réellement engagés, sinon la paire d'adversaires
// la plus proche et les troupes qui peuvent influencer leur scène.
function focusEpreuve(s) {
  if (s && s.focus) {
    const explicite = s.focus(Bataille2d);
    if (explicite && explicite.length) return explicite;
  }
  const debout = Bataille2d.troupe().filter((h) =>
    h && !h.hors && !h.tete && h.etat !== "mort" && h.etat !== "blesse");
  if (!debout.length) return Bataille2d.troupe();
  const engages = debout.filter((h) => h.enMesure ||
    /^(melee|frappe|recul|fuite|deroute)$/.test(h.etat || ""));
  let cx, cy;
  if (engages.length) {
    cx = engages.reduce((n, h) => n + h.x, 0) / engages.length;
    cy = engages.reduce((n, h) => n + h.y, 0) / engages.length;
  } else {
    const assaut = debout.filter((h) => h.camp === "assaut");
    const garde = debout.filter((h) => h.camp === "garde");
    let meilleur = Infinity, a = null, b = null;
    for (const x of assaut) for (const y of garde) {
      const d = (x.x - y.x) ** 2 + (x.y - y.y) ** 2;
      if (d < meilleur) { meilleur = d; a = x; b = y; }
    }
    if (!a || !b) return debout;
    // Tant que les camps sont à plusieurs rues l'un de l'autre, leur boîte
    // commune est précisément le faux « zoom » que l'on veut éviter. On suit
    // alors la pointe qui approche. Dès que les deux fronts peuvent tenir dans
    // la même etat.vue() locale, le centre passe entre eux.
    if (Math.sqrt(meilleur) > 105) { cx = a.x; cy = a.y; }
    else { cx = (a.x + b.x) / 2; cy = (a.y + b.y) / 2; }
  }
  const rayon2 = 65 * 65;
  const local = debout.filter((h) => (h.x - cx) ** 2 + (h.y - cy) ** 2 <= rayon2);
  return local.length >= 2 ? local : debout;
}

function programmerMasque(delai = 650) {
  if (sousMasque) clearTimeout(sousMasque);
  sousMasque = setTimeout(() => {
    const b = $("sbulle");
    if (b && b.matches(":hover")) return;
    if (b) b.style.display = "none";
    sousCourant = null; sousCle = null; sousMasque = null;
    if (etat.pret() && Bataille2d.souligner) Bataille2d.souligner(null);
  }, delai);
}

function positionSous(e, b) {
  const h = $("toile"), r = h.getBoundingClientRect();
  let x = e.clientX - r.left + 14, y = e.clientY - r.top + 16;
  // On mesure la fiche RÉELLE. L'ancienne réserve fixe de 420 px envoyait une
  // fiche de 170 px tout en haut de la carte dès que l'homme se trouvait sous
  // la moitié de l'écran — parfois à 150 px du pointeur.
  const largeur = b.offsetWidth || 390, hauteur = b.offsetHeight || 220;
  if (x + largeur + 5 > r.width) x = e.clientX - r.left - largeur - 14;
  if (y + hauteur + 5 > r.height) y = e.clientY - r.top - hauteur - 14;
  x = Math.max(5, Math.min(r.width - largeur - 5, x));
  y = Math.max(5, Math.min(r.height - hauteur - 5, y));
  b.style.left = Math.round(x) + "px"; b.style.top = Math.round(y) + "px";
}

function texteSous(s) {
  const p = s.pensee;
  const lignes = [
    '<span class="nom">' + echapper(s.nom || ({ tete:"Chef de corps", chef:"Chef d’escouade",
      capitaine:"Porte-bannière", coureur:"Coureur", roi:"Le roi" }[s.quoi]) || "Un homme") + '</span>',
    '<span>' + echapper(s.etat) + (s.arme ? " · " + echapper(s.arme) : "") + '</span>',
    p ? '<span class="pensee">j’essaie de ' + echapper(p.action) +
      '<em>' + echapper(p.systeme) + '</em></span>' : "",
    p ? '<span>parce que ' + echapper(p.raison) + ' · ' + p.depuis.toFixed(1) + ' s</span>' : "",
    s.corpsDit ? '<span>corps : ' + echapper(s.corpsDit) +
      (s.empriseCorps != null ? ' · emprise ' + s.empriseCorps : '') + '</span>' : "",
    s.reflexion ? '<span>réflexion : ' + echapper(s.reflexion.idee) +
      ' · tenir ' + s.reflexion.tient + '</span>' : "",
    s.maniere ? '<span>ordre intérieur : ' + echapper(s.maniere) + '</span>' : "",
    s.conduit ? '<span>arbitre : ' + echapper(s.conduit) + ' tient les jambes</span>' : "",
    s.ordre ? '<span>ordre reçu : ' + echapper(s.ordre) + '</span>' : "",
    s.unite ? '<span>unité : ' + echapper(s.unite) +
      (s.chefFormation ? ' · sous ' + echapper(s.chefFormation) : '') + '</span>' : "",
    s.destination ? '<span>destination : ' + echapper(s.destination) +
      ' · ' + s.calculsAStar + ' route(s)</span>' : "",
    s.cession ? '<span>circulation : je me suis écarté pour ' +
      (s.cession.chef ? 'mon chef' : 'un allié') + ' · ' +
      echapper(s.cession.ilYa) + ' s</span>' : "",
    s.amis != null ? '<span>autour : ' + s.amis + ' des siens · ' + s.ennemis +
      ' en face</span>' : "",
    s.pv != null ? '<span>corps : ' + s.pv + '/' + s.pvMax + ' pv · souffle ' +
      s.souffle + '</span>' : "",
    s.commandant ? '<span>commandement : ' + echapper(s.roleCommandant) + ' · ' +
      s.croyancesCommandant + ' croyance(s)</span>' : "",
    '<div class="actions-survol">' + (s.commandant
      ? '<button type="button" class="voir-carte' +
        (s.carteCommandantActive ? ' active' : '') + '">' +
        (s.carteCommandantActive ? 'Masquer sa carte' : 'Voir sa carte') + '</button>'
      : '') + '<button type="button" class="mark">Mark</button></div>',
  ];
  return lignes.join("");
}

function decrireIci(p) {
  if (!etat.toponymie()) return { texte: "sans repère nommé" };
  let repere = null;
  for (const r of etat.toponymie().reperes) {
    const d = Math.hypot(p.x - r.x, p.y - r.y);
    if (d <= 240 && (!repere || d < repere.distance_m)) repere = { ...r, distance_m:+d.toFixed(1) };
  }
  let axe = null;
  for (const a of etat.toponymie().axes) {
    const d = Math.hypot(p.x - a.x, p.y - a.y);
    if (d <= 80 && (!axe || d < axe.distance_m)) axe = { ...a, distance_m:+d.toFixed(1) };
  }
  return { axe, repere, texte: [axe && axe.nom, repere && ("près de " + repere.nom)]
    .filter(Boolean).join(", ") || "sans repère nommé" };
}

function capturerZone(s) {
  const h = $("toile"), r = h.getBoundingClientRect(), k = etat.parMetre(r);
  const ox = (r.width - etat.vue()[2] * k) / 2, oy = (r.height - etat.vue()[3] * k) / 2;
  const tx = ox + (s.x - etat.vue()[0]) * k, ty = oy + (s.y - etat.vue()[1]) * k;
  const cw = Math.min(560, r.width), ch = Math.min(400, r.height);
  const cx = Math.max(0, Math.min(r.width - cw, tx - cw / 2));
  const cy = Math.max(0, Math.min(r.height - ch, ty - ch / 2));
  const out = document.createElement("canvas"); out.width = 760;
  out.height = Math.max(1, Math.round(760 * ch / cw));
  const c = out.getContext("2d"); c.fillStyle = "#0d0c0a"; c.fillRect(0, 0, out.width, out.height);
  [$("fond"), h.querySelector("canvas.cv-bataille"),
   h.classList.contains("dragon") ? $("dragonCanvas") : null].forEach((src) => {
    if (!src || !src.width || !src.height) return;
    const sx = src.width / r.width, sy = src.height / r.height;
    c.drawImage(src, cx * sx, cy * sy, cw * sx, ch * sy, 0, 0, out.width, out.height);
  });
  const mx = (tx - cx) * out.width / cw, my = (ty - cy) * out.height / ch;
  c.strokeStyle = "#ff7a3d"; c.fillStyle = "rgba(255,122,61,.16)"; c.lineWidth = 3;
  c.beginPath(); c.arc(mx, my, 15, 0, Math.PI * 2); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(mx-23,my); c.lineTo(mx-9,my); c.moveTo(mx+9,my); c.lineTo(mx+23,my);
  c.moveTo(mx,my-23); c.lineTo(mx,my-9); c.moveTo(mx,my+9); c.lineTo(mx,my+23); c.stroke();
  let image = out.toDataURL("image/webp", .88);
  if (!image.startsWith("data:image/webp")) image = out.toDataURL("image/png");
  return { image, meta: { quand:new Date().toISOString(), source:"/bataille",
    montre:"la zone courante autour du combattant marqué",
    metres_par_pixel:+(etat.vue()[2] / r.width).toFixed(2),
    large_en_metres:Math.round(cw * etat.vue()[2] / r.width),
    cible:{ id:s.debugId, x:+s.x.toFixed(1), y:+s.y.toFixed(1) },
    couches:["masque", "bataille"] } };
}

function ouvrirMark(s) {
  if (!s || !s.debugId) return;
  installerLoupe();
  const diagnostic = Bataille2d.diagnostic(s.debugId), capture = capturerZone(s);
  const lieu = decrireIci(diagnostic.combattant.position), d = $("smark");
  d.className = "ouvert";
  d.querySelector("h3").textContent = "Mark — " +
    (diagnostic.combattant.nom || diagnostic.combattant.id);
  d.querySelector(".instant").textContent = [diagnostic.temps_bataille_s + " s de bataille",
    lieu.texte, diagnostic.combattant.pensee &&
    "j’essaie de " + diagnostic.combattant.pensee.action].filter(Boolean).join(" · ");
  const ta = d.querySelector("textarea"), sauver = d.querySelector(".sauver"),
        statut = d.querySelector(".statut");
  ta.value = ""; ta.disabled = false; sauver.disabled = false;
  sauver.textContent = "Enregistrer la marque"; statut.textContent = "Capture prête.";
  d.querySelector(".annuler").onclick = () => { d.className = ""; };
  sauver.onclick = async () => {
    const commentaire = ta.value.trim();
    if (!commentaire) { statut.textContent = "Écrivez un commentaire."; ta.focus(); return; }
    sauver.disabled = true; ta.disabled = true; statut.textContent = "Enregistrement…";
    try {
      const r = await fetch("/marque-bataille", { method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ commentaire, diagnostic, lieu,
                              image:capture.image, meta:capture.meta }) });
      const rep = await r.json(); if (!r.ok) throw new Error(rep.erreur || ("refus " + r.status));
      const h = rep.historique;
      const allegee = h && h.omis ? " · " + h.conserve +
        " perceptions récentes gardées, " + h.omis + " anciennes omises" : "";
      d.className = "ouvert sauvee"; statut.innerHTML = "Marque enregistrée dans <code>" +
        echapper(rep.ecrit) + "</code>" + allegee; sauver.disabled = false;
      sauver.textContent = "Fermer";
      sauver.onclick = () => { d.className = ""; };
    } catch (e) {
      sauver.disabled = false; ta.disabled = false; statut.textContent = "Échec : " + e.message;
    }
  };
  ta.focus();
}

function survolerScene(e) {
  if (!etat.pret() || !etat.vue() || !Bataille2d.sous) return false;
  if (e.target.closest && e.target.closest("#sbulle,#smark")) return true;
  installerLoupe();
  const h = $("toile"), r = h.getBoundingClientRect(), k = etat.parMetre(r);
  const x = etat.vue()[0] + (e.clientX - r.left - (r.width - etat.vue()[2] * k) / 2) / k;
  const y = etat.vue()[1] + (e.clientY - r.top - (r.height - etat.vue()[3] * k) / 2) / k;
  const s = Bataille2d.sous(x, y, Math.max(1.5, 7 / k)), b = $("sbulle");
  if (!s || !s.debugId) {
    // On laisse le temps de franchir les 14 px jusqu'à la fiche. Une nouvelle
    // cible annule immédiatement cette fermeture différée.
    if (b.style.display !== "none") programmerMasque();
    return false;
  }
  if (sousMasque) { clearTimeout(sousMasque); sousMasque = null; }
  const cle = s.debugId + ":" + s.etat + ":" + (s.branche || "") + ":" + s.pv + ":" +
    s.souffle + ":" + (s.carteCommandantActive ? "carte" : "sans-carte") + ":" +
    s.croyancesCommandant;
  if (cle !== sousCle) {
    b.innerHTML = texteSous(s); b.querySelector(".mark").onclick = (ev) => {
      ev.preventDefault(); ev.stopPropagation(); ouvrirMark(s);
    };
    const carte = b.querySelector(".voir-carte");
    if (carte) carte.onclick = (ev) => {
      ev.preventDefault(); ev.stopPropagation();
      const ouverte = Bataille2d.selectionnerCarteCommandant(s.debugId);
      s.carteCommandantActive = !!ouverte;
      carte.classList.toggle("active", !!ouverte);
      carte.textContent = ouverte ? "Masquer sa carte" : "Voir sa carte";
      sousCle = null;
    };
    sousCle = cle;
  }
  b.style.display = "block"; positionSous(e, b); sousCourant = s;
  if (Bataille2d.souligner) Bataille2d.souligner(s._sel || null);
  return true;
}

  return Object.freeze({
    focusEpreuve,
    installer: installerLoupe,
    survoler: survolerScene,
  });
}

window.BatailleInspection = Object.freeze({ creer });
})();
