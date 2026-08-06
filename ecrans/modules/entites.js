// entites.js — toute entité connue de l'état (gens, lieux, maisons, dragons) est
// rendue en gras et cliquable dans le fil. Au clic : une question type se compose
// dans le champ libre (« Qu'en est-il de X ? »), prête à partir ou à retoucher.
"use strict";
window.Entites = (() => {
  let parNom = new Map();
  let regex = null;
  let prets = false;

  const AMORCES = [
    "Vos pensées glissent vers {n}…",
    "{n}. Le nom s'attarde en vous…",
    "Un instant, votre esprit s'échappe vers {n}…",
  ];

  const echapper = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  // Le registre se rebâtit à chaque apport : le serveur donne les gens, les
  // lieux et les maisons ; plan.js ajoute les salles du château où l'on est.
  function ajouter(entites) {
    (entites || []).forEach((e) => {
      e.noms.forEach((n) => {
        const c = (n || "").toLowerCase();
        // premier arrivé, premier servi : un nom déjà pris ne change pas d'entité
        if (c.length > 2 && !parNom.has(c)) parNom.set(c, e);
      });
    });
    const noms = Array.from(parNom.keys());
    if (!noms.length) return;
    noms.sort((a, b) => b.length - a.length);
    regex = new RegExp("(?<![A-Za-zÀ-ÿ])(" + noms.map(echapper).join("|") + ")(?![A-Za-zÀ-ÿ])", "gi");
    prets = true;
    // Le registre vient de grandir : ce qui a déjà été relu au chargement doit
    // l'être une seconde fois, sinon les noms du nouvel apport ne seraient en
    // gras que dans la suite du fil. Les entités déjà posées ne bougent pas —
    // on ne repasse que sur le texte nu.
    document.querySelectorAll(".phrase[data-ent-ok]").forEach((p) => {
      delete p.dataset.entOk;
    });
    traiter(document.body);
  }

  fetch("/entites").then((r) => r.json()).then((d) => ajouter(d.entites))
    .catch(() => {});

  function envelopper(noeudTexte) {
    const t = noeudTexte.nodeValue;
    regex.lastIndex = 0;
    if (!regex.test(t)) return;
    regex.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let i = 0, m;
    while ((m = regex.exec(t))) {
      if (m.index > i) frag.appendChild(document.createTextNode(t.slice(i, m.index)));
      const e = parNom.get(m[1].toLowerCase());
      const b = document.createElement("b");
      b.className = "entite";
      b.dataset.id = e.id;
      b.dataset.type = e.type;
      b.textContent = m[1];
      frag.appendChild(b);
      i = m.index + m[1].length;
    }
    if (i < t.length) frag.appendChild(document.createTextNode(t.slice(i)));
    noeudTexte.replaceWith(frag);
  }

  function traiter(racine) {
    if (!prets) return;
    racine.querySelectorAll(".phrase").forEach((ph) => {
      if (ph.dataset.entOk) return;
      ph.dataset.entOk = "1";
      Array.from(ph.childNodes).forEach((n) => {
        if (n.nodeType === 3) envelopper(n);
        else if (n.nodeType === 1 && n.tagName === "I") {
          Array.from(n.childNodes).forEach((nn) => { if (nn.nodeType === 3) envelopper(nn); });
        }
      });
    });
  }

  // Un MOMENT de pensée : amorce immédiate dans le fil, résolu par le narrateur
  // (items `pensee` à suivre), sans interrompre la scène.
  function penser(id, type, nom) {
    const amorce = AMORCES[Math.floor(Math.random() * AMORCES.length)].replace("{n}", nom);
    if (window.PenseeAfficher) PenseeAfficher(amorce);
    Bus.envoyer({ type: "pensee", cible: id, cible_type: type, texte: nom });
  }

  // Le survol d'un nom de LIEU vise la table : elle se centre dessus le temps
  // qu'on le lise, puis se repose. Un court délai évite que l'œil qui balaie
  // une phrase ne fasse sauter la carte de place en place.
  let minuteur = null, vise = null;
  function relacher() {
    clearTimeout(minuteur);
    if (!vise) return;
    vise = null;
    if (window.Carte && Carte.deviser) Carte.deviser();
  }
  document.addEventListener("mouseover", (e) => {
    const ent = e.target.closest && e.target.closest('.entite[data-type="lieu"]');
    if (!ent) return;
    if (ent === vise) return;
    relacher();
    vise = ent;
    minuteur = setTimeout(() => {
      if (vise === ent && window.Carte && Carte.viser) Carte.viser(ent.dataset.id);
    }, 180);
  });
  document.addEventListener("mouseout", (e) => {
    const ent = e.target.closest && e.target.closest('.entite[data-type="lieu"]');
    if (ent && ent === vise) relacher();
  });

  document.addEventListener("click", (e) => {
    const ent = e.target.closest(".entite");
    if (!ent) return;
    penser(ent.dataset.id, ent.dataset.type, ent.textContent);
  });

  return { traiter, penser, ajouter };
})();
