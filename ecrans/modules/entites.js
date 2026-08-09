// entites.js — toute entité connue de l'état (gens, lieux, maisons, dragons) est
// rendue en gras et cliquable dans le fil. Au clic : une QUESTION part au
// narrateur — hors fiction, temps figé — pour qu'on nous rappelle ou nous
// explique de quoi il retourne. Personne dans la salle ne l'entend.
"use strict";
window.Entites = (() => {
  let parNom = new Map();
  let regex = null;
  let prets = false;

  // Ce qu'on demande, selon la nature de la chose : la question doit appeler
  // du CONTEXTE utile à la décision en cours, pas une carte postale.
  const DEMANDES = {
    personnage: "Rappelle-moi qui est {n} : ce que je sais de lui, ce qui nous " +
      "lie, de quel côté je le crois, et ce qu'il pèse dans ce qui se joue " +
      "maintenant.",
    lieu: "Rappelle-moi ce qu'est {n} : qui le tient, ce qu'il vaut, à combien " +
      "de jours il est d'ici, et ce qui s'y joue à cette date.",
    maison: "Rappelle-moi ce qu'est la maison {n} : ce qu'elle m'a juré ou " +
      "refusé, ce qu'elle peut lever, et ce qu'elle change pour moi aujourd'hui.",
    dragon: "Rappelle-moi ce qu'est {n} : qui le monte, où je le crois, ce " +
      "qu'il peut faire et ce qu'il ne peut pas.",
    salle: "Rappelle-moi ce qu'est {n} : à quoi sert cette salle, qui y va, et " +
      "ce qui s'y trouve.",
    objectif: "Où en est ce dessein — « {n} » ? Rappelle-moi d'où il vient, ce " +
      "qui a bougé et ce qu'il reste.",
  };
  const DEFAUT = "Rappelle-moi ce qu'est {n} — ce que j'en sais et ce que ça " +
    "change pour moi maintenant.";

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
        // un nom pris dans un appui (**gras**) ou une incise reste cliquable
        else if (n.nodeType === 1 && (n.tagName === "I" || n.classList.contains("appui"))) {
          Array.from(n.childNodes).forEach((nn) => { if (nn.nodeType === 3) envelopper(nn); });
        }
      });
    });
  }

  // Le décor suit le doigt : demander ce qu'est une chose et la CHERCHER des
  // yeux sont le même geste. Chaque nature a son échelle — un bâtiment se
  // regarde d'en haut, un homme se cherche salle par salle, une place lointaine
  // est un point sur la table peinte. Muet si l'on ne sait pas où elle est :
  // mieux vaut ne rien montrer que montrer le mauvais endroit.
  function montrer(id, type) {
    const ici = window.Plan && Plan.chateau && Plan.chateau();
    // Une salle, ou le château où l'on se tient : le quartier, en volume. Là où
    // le monde n'est pas modelé, le plan dessiné prend le relais.
    if (type === "salle" || (type === "lieu" && id === ici)) {
      const cible = (type === "salle" ? "salle:" : "lieu:") + id;
      if (window.Ville3D && Ville3D.viser && Ville3D.viser(cible)) return;
      if (window.Plan && Plan.viser && Plan.viser({ salle: id })) return;
    }
    // Quelqu'un : le plan du château, sa salle allumée. S'il n'est pas sous ce
    // toit, on ne le cherche pas — le joueur ne sait pas forcément où il est.
    if (type === "personnage" && window.Plan && Plan.viser &&
        Plan.viser({ personnage: id })) return;
    // Tout le reste qui a une place connue : le royaume, cadré dessus et tenu.
    // On ne bascule le décor que si la table sait où c'est : rappeler le
    // royaume pour n'y rien montrer serait pire que de ne pas bouger.
    if (!window.Carte || !Carte.viser) return;
    if (!window.Jetons || !Jetons.position || !Jetons.position(id)) return;
    if (window.Plan && Plan.montrer) Plan.montrer("royaume");
    Carte.viser(id, { tenir: true });
  }

  // Une QUESTION au narrateur, hors fiction : le serveur l'inscrit au flux en
  // `question` (privée, zéro minute) et le MJ répond par un `reponse`. La scène
  // en cours ne bouge pas d'un souffle.
  function demander(id, type, nom) {
    const texte = (DEMANDES[type] || DEFAUT).replace(/\{n\}/g, nom);
    Bus.poster({ type: "libre", mode: "question", cible: id, cible_type: type, texte });
    setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
    // et l'œil va où la question va — le décor n'attend pas la réponse.
    try { montrer(id, type); } catch (e) {}
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
    demander(ent.dataset.id, ent.dataset.type, ent.textContent);
  });

  // `penser` reste le nom d'appel des autres modules (desseins, gens…) : ils
  // pointent tous sur la même demande, pour qu'un clic ait partout le même sens.
  return { traiter, demander, penser: demander, ajouter };
})();
