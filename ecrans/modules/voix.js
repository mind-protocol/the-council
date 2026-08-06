// voix.js — les répliques se disent à voix haute. Chaque personnage a la voix
// conçue pour lui (etat/voix.json) ; le serveur la fabrique et la met en cache.
// Coupable à tout moment par le bouton du panneau — et muet par principe pendant
// le rejeu de l'historique : on ne réécoute pas ce qui a déjà été dit.
"use strict";
window.Voix = (() => {
  // La salle parle : mp3 des voix conçues quand la phrase est en cache ou
  // synthétisable, voix du navigateur en secours. Seul un « non » explicite du
  // joueur, par le bouton du panneau, la tait.
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

  function taire() {
    if (renouvellement) { clearInterval(renouvellement); renouvellement = null; }
    if (audio) { audio.pause(); audio.src = ""; audio = null; }
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    const f = finir;
    attente = null; finir = null;
    if (f) f();
  }

  // Le bus s'en sert pour ne pas enchaîner par-dessus la voix : tant qu'on
  // parle, l'item suivant attend.
  function enAttente() { return attente; }

  // qui parle : un personnage de la salle, "narrateur" pour ce qui est raconté,
  // "pensee-joueur" pour ce que la reine s'entend penser.
  // el : l'entrée du fil correspondante — on la met en avant le temps qu'elle
  // se dise, pour que l'œil sache toujours où en est l'oreille.
  async function dire(locuteur_id, texte, ctx, el) {
    // rejeu d'historique, voix coupée, personnage sans voix, ou panne : rien.
    if (!actif || (ctx && ctx.instant) || panne) return;
    if (!connues[locuteur_id] || !(texte || "").trim()) return;
    if (dejaEnvoyee(locuteur_id + "|" + texte)) return;

    let resoudre;
    attente = new Promise((r) => (resoudre = r));
    const cette = attente;
    const relacher = () => {
      if (renouvellement) { clearInterval(renouvellement); renouvellement = null; }
      if (el) el.classList.remove("chr-dit");
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
        body: JSON.stringify({ locuteur_id: locuteur_id, texte: texte, client_id: MOI }),
      });
      // 409 : un autre écran tient la parole. Ce n'est pas une panne — cette
      // page suit le flux en silence et retentera à la phrase suivante.
      if (r.status === 409) return relacher();
      // 204 : rien en cache et le serveur n'appelle plus ElevenLabs. La phrase
      // se dit quand même — avec la voix du navigateur, accordée au personnage.
      if (r.status === 204) {
        if (el) el.classList.add("chr-dit");
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
      if (el) el.classList.add("chr-dit");
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
    b.textContent = panne ? "voix indisponible" : actif ? "on parle à voix haute" : "salle muette";
    b.title = panne || "";
    b.disabled = !!panne;
  }

  window.addEventListener("DOMContentLoaded", async () => {
    try {
      const l = await (await fetch("/voix/liste")).json();
      connues = l.voix || {};
      if (!l.disponible) panne = "clé ElevenLabs absente";
    } catch (e) { panne = "serveur muet"; }

    const zone = document.getElementById("zone-reglages-corps");
    if (zone) {
      const d = document.createElement("div");
      d.className = "reglage";
      d.innerHTML = '<div class="reglage-nom">Les voix</div>' +
        '<button id="regl-voix" class="bouton-voix"></button>' +
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

  return { dire, taire, enAttente, active: () => actif && !panne };
})();
