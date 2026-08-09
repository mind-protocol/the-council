// voix.js — les répliques se disent à voix haute, mais JAMAIS d'elles-mêmes ni
// les unes après les autres : chaque ligne du fil porte un BOUTON, on clique
// pour l'entendre et on reclique pour l'arrêter. Rien ne s'enchaîne, rien ne
// s'anticipe, rien ne se synthétise que le joueur n'ait cliqué. Chaque
// personnage a la voix conçue pour lui (etat/voix.json) ; le serveur la
// fabrique et la met en cache.
// Corollaire : tout le fil est écoutable, l'historique compris — recliquer une
// vieille réplique la redit, on ne lui oppose aucune barrière d'écho.
"use strict";
window.Voix = (() => {
  // La salle parle quand on l'écoute : son des voix conçues quand la phrase est
  // en cache ou synthétisable, voix du navigateur en secours. Le bouton du
  // panneau la tait pour de bon — et rien ne part alors au serveur.
  const MEMOIRE = "lc-voix-3";
  let actif = localStorage.getItem(MEMOIRE) !== "0";
  let connues = {};      // locuteur_id -> {nom}
  let panne = null;      // message d'échec : on cesse de demander jusqu'au rechargement
  let audio = null;      // la lecture en cours
  // Notre identité d'écran, le temps de la page. Le bail de parole se prend
  // auprès du SERVEUR et non dans localStorage : deux fenêtres dans deux
  // navigateurs différents ne partagent aucun stockage, et lisaient ensemble.
  // (On ne se fie pas non plus à document.hidden : Chrome déclare masquée toute
  // fenêtre recouverte, et la salle se taisait pour rien.)
  const MOI = Math.random().toString(36).slice(2);

  // Ce que cette page a déjà envoyé à dire : une phrase identique ne repart pas,
  // quelle que soit la main qui rappelle dire(). Le serveur a la même barrière ;
  // celle-ci évite en plus l'aller-retour.
  const envoyees = new Map();
  const ECHO_MS = 45000;
  function dejaEnvoyee(cle) {
    const t = Date.now();
    for (const [k, v] of envoyees) if (t - v > ECHO_MS) envoyees.delete(k);
    if (envoyees.has(cle)) return true;
    envoyees.set(cle, t);
    return false;
  }

  // Le timbre de secours : le navigateur n'a qu'une voix, on l'accorde par
  // personnage. Grave et lent pour le Serpent de Mer, haut et vif pour un
  // garçon de quatorze ans — de quoi les reconnaître sans les confondre.
  const TIMBRES = {
    "narrateur":      { hauteur: 1.00, vitesse: 1.00 },
    "pensee-joueur":  { hauteur: 1.05, vitesse: 0.92 },
    "rhaenyra":       { hauteur: 1.02, vitesse: 0.96 },
    "daemon":         { hauteur: 0.72, vitesse: 0.94 },
    "rhaenys":        { hauteur: 0.98, vitesse: 1.02 },
    "corlys":         { hauteur: 0.62, vitesse: 0.88 },
    "gerardys":       { hauteur: 0.88, vitesse: 1.06 },
    "robert-quince":  { hauteur: 0.58, vitesse: 0.84 },
    "mysaria":        { hauteur: 1.12, vitesse: 0.90 },
    "jacaerys":       { hauteur: 1.22, vitesse: 1.04 },
    "lucerys":        { hauteur: 1.35, vitesse: 1.06 },
    "aegon-ii":       { hauteur: 0.86, vitesse: 1.10 },
    "aemond":         { hauteur: 0.80, vitesse: 0.90 },
    "alicent":        { hauteur: 1.06, vitesse: 0.98 },
    "otto":           { hauteur: 0.68, vitesse: 0.90 },
    "criston":        { hauteur: 0.74, vitesse: 1.02 },
    "larys":          { hauteur: 0.94, vitesse: 0.86 },
    "helaena":        { hauteur: 1.28, vitesse: 0.88 },
    "orwyle":         { hauteur: 0.82, vitesse: 1.12 },
  };
  let voixFr = null;

  function timbre(id) {
    return TIMBRES[id] || { hauteur: 1, vitesse: 1 };
  }

  // La liste des voix arrive parfois après le chargement de la page.
  function chercherVoixFr() {
    const dispo = ("speechSynthesis" in window) ? speechSynthesis.getVoices() : [];
    voixFr = dispo.find((v) => /^fr/i.test(v.lang)) || null;
  }
  if ("speechSynthesis" in window) {
    chercherVoixFr();
    speechSynthesis.onvoiceschanged = chercherVoixFr;
  }

  // Renvoie true si la phrase est partie chez le navigateur. On tente même sans
  // voix française déclarée : `lang` suffit souvent au système à en choisir une,
  // et une voix étrangère vaut mieux qu'un silence.
  function direAuNavigateur(locuteur_id, texte, relacher) {
    if (!("speechSynthesis" in window)) return false;
    if (!voixFr) chercherVoixFr();
    const t = timbre(locuteur_id);
    const phrase = new SpeechSynthesisUtterance(texte);
    phrase.lang = "fr-FR";
    if (voixFr) phrase.voice = voixFr;
    phrase.pitch = t.hauteur;
    phrase.rate = t.vitesse;
    // Un poste sans moteur de parole avale l'énoncé sans jamais rendre la main :
    // le fil resterait suspendu. On borne l'attente sur la longueur du texte.
    const borne = Math.min(30000, Math.max(2500, (texte.length / 14) * 1000 / t.vitesse));
    const chien = setTimeout(relacher, borne);
    phrase.onend = phrase.onerror = () => { clearTimeout(chien); relacher(); };
    speechSynthesis.cancel();
    speechSynthesis.speak(phrase);
    return true;
  }

  function renouvelerBail() {
    fetch("/voix/dire", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ renouveler: true, client_id: MOI }),
    }).catch(() => {});
  }
  let attente = null;    // promesse résolue quand la réplique est finie de dire
  let finir = null;      // son dénouement — à appeler quoi qu'il arrive, sinon le fil reste suspendu
  let renouvellement = null;  // le bail se renouvelle tant qu'une phrase dure

  // Le silence : ce qu'appellent le bouton de la ligne quand elle parle, celui
  // du panneau, et le bouton Couper — on ne superpose jamais deux voix.
  function taire() {
    if (renouvellement) { clearInterval(renouvellement); renouvellement = null; }
    if (audio) { audio.pause(); audio.src = ""; audio = null; }
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    enCours = null;
    const f = finir;
    attente = null; finir = null;
    if (f) f();
  }

  // Le bus s'en sert pour ne pas enchaîner par-dessus la voix : tant qu'on
  // parle, l'item suivant attend.
  function enAttente() { return attente; }


  // ---- le bouton de voix : un par ligne ----------------------------------
  // Le survol ne suffisait pas — il ne se voit pas, il ne se vise pas, et il
  // part tout seul quand la souris passe. Chaque ligne du fil porte donc un
  // BOUTON : on clique pour l'entendre, on reclique pour l'arrêter. Trois
  // états, et le même bouton les porte tous — au repos un haut-parleur pâle,
  // trois points pendant qu'on cherche la voix, le haut-parleur en braise
  // pendant qu'on l'entend.
  const HP = '<svg viewBox="0 0 24 24" aria-hidden="true">' +
    '<path d="M4 9.5h3.5L12 5.5v13L7.5 14.5H4z"/>' +
    '<path class="onde onde1" d="M15 9.2a4 4 0 0 1 0 5.6"/>' +
    '<path class="onde onde2" d="M17.8 6.6a8 8 0 0 1 0 10.8"/></svg>';
  const POINTS = "<i></i><i></i><i></i>";

  function marquer(el, etat) {
    if (!el) return;
    const b = el.querySelector(".voix-bouton");
    if (!b) return;
    b.className = "voix-bouton " + (etat || "repos");
    b.innerHTML = etat === "attend" ? POINTS : HP;
    b.title = etat === "attend" ? "on cherche la voix…"
            : etat === "dit" ? "arrêter" : "l’entendre";
    b.setAttribute("aria-label", b.title);
  }

  // Le geste : entendre cette ligne, ou faire taire celle qu'on entend. Le même
  // bouton fait les deux — c'est ce qui permet de couper sans chercher ailleurs.
  function basculer(el) {
    if (!actif || panne) return;
    if (enCours === el) return taire();
    const d = dicibles.get(el);
    if (!d) return;
    taire();
    // Cliquer, c'est demander. Une ligne qu'on vient d'entendre se redit donc
    // sans discuter : les barrières d'écho sont là contre les doublons du
    // moteur, pas contre le joueur.
    parler(d.locuteur_id, d.texte, el, true);
  }

  // ---- ce qui peut se dire ----------------------------------------------
  // La salle ne parle pas : elle attend qu'on le lui demande, ligne par ligne.
  // Rien ne s'enchaîne, rien ne s'anticipe, rien ne se synthétise que le joueur
  // n'ait cliqué.
  const dicibles = new Map();   // élément du fil -> { locuteur_id, texte }
  let enCours = null;           // l'élément qu'on entend en ce moment

  // qui parle : un personnage de la salle, "narrateur" pour ce qui est raconté,
  // "pensee-joueur" pour ce que la reine s'entend penser.
  // el : l'entrée du fil correspondante — elle porte le bouton, et se met en
  // avant le temps qu'elle se dise.
  function dire(locuteur_id, texte, ctx, el) {
    if (!el || !(texte || "").trim()) return;
    if (dicibles.has(el)) return;
    dicibles.set(el, { locuteur_id: locuteur_id, texte: texte });
    el.setAttribute("data-voix", "1");

    const b = document.createElement("button");
    b.type = "button";
    b.className = "voix-bouton repos";
    b.innerHTML = HP;
    b.title = "l’entendre";
    b.setAttribute("aria-label", "l’entendre");
    b.addEventListener("click", (ev) => { ev.stopPropagation(); ev.preventDefault(); basculer(el); });
    const hote = el.querySelector(".chr-corps") || el;
    hote.insertBefore(b, hote.firstChild);
  }

  // rejouer : le joueur a survolé — on passe outre les barrières d'écho.
  async function parler(locuteur_id, texte, el, rejouer) {
    if (!actif || panne) return;
    if (!rejouer && dejaEnvoyee(locuteur_id + "|" + texte)) return;
    enCours = el;
    marquer(el, "attend");

    let resoudre;
    attente = new Promise((r) => (resoudre = r));
    const cette = attente;
    const relacher = () => {
      if (renouvellement) { clearInterval(renouvellement); renouvellement = null; }
      if (el) { el.classList.remove("chr-dit"); marquer(el, null); }
      if (enCours === el) enCours = null;
      if (attente === cette) { attente = null; finir = null; }
      resoudre();
    };
    // couper la voix doit aussi éteindre la mise en avant : c'est relacher, et
    // pas le simple dénouement de la promesse, que taire() appelle.
    finir = relacher;

    try {
      const r = await fetch("/voix/dire", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ locuteur_id: locuteur_id, texte: texte,
                               client_id: MOI, rejouer: !!rejouer }),
      });
      // 409 : un autre écran tient la parole. Ce n'est pas une panne — cette
      // page suit le flux en silence et retentera à la phrase suivante.
      if (r.status === 409) return relacher();
      // 204 : rien en cache et le serveur n'appelle plus Deepgram. La phrase
      // se dit quand même — avec la voix du navigateur, accordée au personnage.
      if (r.status === 204) {
        if (el) { el.classList.add("chr-dit"); marquer(el, "dit"); }
        if (direAuNavigateur(locuteur_id, texte, relacher)) {
          renouvellement = setInterval(renouvelerBail, 2000);
          return;
        }
        return relacher();
      }
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        panne = d.erreur || ("HTTP " + r.status);
        console.warn("voix indisponible :", panne);
        etiqueter();
        return relacher();
      }
      // le joueur a pu couper pendant que le son arrivait
      if (!actif || attente !== cette) return relacher();
      if (audio) { audio.pause(); audio.src = ""; }
      audio = new Audio(URL.createObjectURL(await r.blob()));
      audio.onended = audio.onerror = relacher;
      if (el) { el.classList.add("chr-dit"); marquer(el, "dit"); }
      // une longue tirade dépasse la durée du bail : on le tient tant qu'on parle.
      renouvellement = setInterval(renouvelerBail, 2000);
      await audio.play().catch(relacher);
    } catch (e) {
      console.warn("voix :", e);
      relacher();
    }
  }

  function etiqueter() {
    const b = document.getElementById("regl-voix");
    if (!b) return;
    b.classList.toggle("actif", actif && !panne);
    b.textContent = panne ? "voix indisponible"
      : actif ? "on parle — survolez une ligne" : "salle muette";
    b.title = panne || "";
    b.disabled = !!panne;
  }

  window.addEventListener("DOMContentLoaded", async () => {
    // Le ratissage passe APRÈS les modules : ce qu'ils enregistrent eux-mêmes
    // fait foi (ils savent qui parle et quel texte se dit vraiment), et l'on ne
    // ramasse que ce qu'ils ont laissé.
    const fil = document.getElementById("fil-corps");
    if (fil) {
      new MutationObserver((lots) => {
        for (const l of lots) for (const n of l.addedNodes) setTimeout(() => ratisser(n), 0);
      }).observe(fil, { childList: true });
      setTimeout(() => fil.querySelectorAll(".chr").forEach(ratisser), 0);
    }

    try {
      const l = await (await fetch("/voix/liste")).json();
      connues = l.voix || {};
      if (!l.disponible) panne = "clé Deepgram absente";
    } catch (e) { panne = "serveur muet"; }

    // Sa propre zone dans le panneau de gauche : couper la voix est le seul
    // geste du joueur qui ferme un robinet payant, il ne se cherche pas au fond
    // des réglages du narrateur.
    const zone = document.getElementById("zone-voix-corps")
      || document.getElementById("zone-reglages-corps");
    if (zone) {
      const d = document.createElement("div");
      d.className = "reglage";
      d.innerHTML = '<button id="regl-voix" class="bouton-voix"></button>' +
        '<div class="reglage-bornes"><span>' +
        Object.keys(connues).length + " voix conçues</span></div>";
      zone.appendChild(d);
      d.querySelector("#regl-voix").onclick = () => {
        actif = !actif;
        localStorage.setItem(MEMOIRE, actif ? "1" : "0");
        if (!actif) taire();
        etiqueter();
      };
    }
    etiqueter();
  });

  // ---- le ratissage : personne n'est oublié --------------------------------
  // Les modules appellent dire() pour ce qu'ils savent être de la parole — un
  // récit, une réplique, un geste, une pensée. Le reste du fil n'appelait rien,
  // et c'est justement ce qui s'entasse au BAS de l'écran : les réponses du
  // narrateur, les coulisses, ce que le joueur a dit lui-même. Un joueur qui
  // regarde le pied de sa chronique n'y voyait donc aucun bouton, et concluait
  // qu'il n'y en avait nulle part.
  // On ratisse donc nous-mêmes : toute bulle qui porte du texte reçoit son
  // bouton, quel que soit le module qui l'a faite — sauf celles où lire à voix
  // haute n'a aucun sens.
  const SANS_VOIX = ["chr-salle", "chr-suites", "chr-question", "chr-intervention",
                     "chr-run", "chr-meta", "chr-reglage"];

  function ratisser(el) {
    if (!el || el.nodeType !== 1 || !el.classList.contains("chr")) return;
    if (dicibles.has(el) || el.hasAttribute("data-voix")) return;
    for (const c of SANS_VOIX) if (el.classList.contains(c)) return;
    const t = el.querySelector(".chr-texte");
    const texte = ((t || el).innerText || "").trim();
    if (texte.length < 2) return;
    dire(el.getAttribute("data-qui") || "narrateur", texte, null, el);
  }

  // De quoi répondre sans deviner à « pourquoi ça ne parle pas ». Une lecture
  // qui s'arrête a toujours l'une de ces quatre causes.
  function etat() {
    return { actif, panne, lignes: dicibles.size,
             en_cours: !!enCours, attente: !!attente };
  }

  return { dire, taire, enAttente, etat, active: () => actif && !panne };
})();
