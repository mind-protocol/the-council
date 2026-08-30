// actions.js — la barre unique du joueur : Parler / Agir / Penser / Question /
// Coulisses / Laisser faire / Composer. Plus de mode « Attendre » : lâcher la
// bride au MJ fait passer le temps mieux qu'un bouton d'avance.
"use strict";
(() => {
  window.addEventListener("DOMContentLoaded", () => {
    const zone = document.getElementById("fil-actions");
    zone.innerHTML =
      '<div id="mode-input" data-mode="dire">' +
      '<button id="mode-dire" class="actif"><i class="emb">💬</i>Parler</button>' +
      '<button id="mode-agir"><i class="emb">✋</i>Agir</button>' +
      // Le troisième verbe de l'habitant (habitant.md §3) : FAIRE, la mutation
      // proposée. Il n'apparaît qu'en incarnant un homme hors roster — un PJ
      // classique agit par la scène, pas par le staging.
      '<button id="mode-faire" hidden title="Proposer une mutation du monde : déplacer, verser, remettre — l\'arbitre tranche">' +
      '<i class="emb">🤲</i>Faire</button>' +
      '<button id="mode-penser" title="Peser la situation : ce que vous savez, ce qui s\'offre, ce que ça coûte">' +
      '<i class="emb">💭</i>Penser</button>' +
      '<button id="mode-question" title="Hors fiction : demander une précision">' +
      '<i class="emb">❓</i>Question</button>' +
      // Hors univers pour de bon : on parle de la partie, pas dedans. Ni le
      // personnage ni le monde n'entendent quoi que ce soit ici.
      '<button id="mode-meta" title="Hors univers : commenter la partie, décerner des médailles idiotes">' +
      '<i class="emb">🎬</i>Coulisses</button>' +
      // Lâcher la bride : le MJ tient le personnage un moment et joue à sa place,
      // dans sa manière. L'instruction est facultative — sans elle, il improvise.
      '<button id="mode-run" title="Laisser le MJ jouer votre personnage — instruction facultative">' +
      '<i class="emb">🎭</i>Laisser faire</button>' +
      // La main par-dessus le monde : on ne joue plus, on RÉPARE. Ici le MJ
      // sort de son rôle — plus de canon, plus de brouillard, plus rien
      // d'acquis : le joueur est propriétaire de sa partie et peut la changer
      // sans limites. Hors univers, hors horloge, mais l'état, lui, bouge.
      '<button id="mode-intervention" title="Intervention divine : le MJ sort de son rôle ' +
      'et modifie la partie sans limites — réparer, développer, changer ce qui a été joué">' +
      '<i class="emb">✨</i>Intervention</button>' +
      // PAS DE BOUTON « Composer ». Une chanson n'est plus une commande hors
      // univers : c'est une AFFAIRE DE LA MAISON. On l'obtient en la demandant
      // au barde, en scène, avec ce que ça coûte — et l'atelier (concept,
      // paroles Suno, prompt musical, .md ouvert au bloc-notes) reste le même
      // côté MJ, seulement il est declenché par un ordre et non par un mode.
      // Toujours à portée dès qu'il reste du flux à jouer : parler n'interrompt
      // plus la scène, seul ce bouton l'arrête.
      '<button id="pause" class="pulse"><i class="emb">⏸️</i>Couper</button></div>' +
      '<div class="libre">' +
      '<textarea id="champ-libre" class="mode-dire" placeholder="Vos prochaines paroles…"></textarea>' +
      // Plus d'heure contre le bouton d'envoi : le bandeau est descendu JUSTE
      // SOUS cette barre, et il porte déjà la date, l'heure, l'écart de front
      // et le lieu. Deux montres à trente pixels l'une de l'autre.
      // Améliorer : le joueur écrit vite et mal, le MJ rend la phrase telle
      // qu'elle aurait dû sortir de sa bouche. Ce n'est pas un mode — c'est un
      // filtre sur ce qu'on vient d'écrire, et il ne change ni le sens ni le
      // temps qui passe.
      '<div class="envoi">' +
      // Une pastille, pas un bouton : la plume seule, allumée ou éteinte. Le mot
      // « Améliorer » mangeait la largeur du bandeau, et c'est le NOM DE LA SALLE
      // qu'on veut lire au moment d'envoyer.
      '<button id="ameliorer" aria-pressed="false" title="Améliorer : le MJ reformule vos mots ' +
      'dans la langue du récit — sans fautes, sans changer ce que vous voulez dire">' +
      '<i class="emb">✒️</i></button>' +
      '<button id="btn-libre"><i class="emb">💬</i>Parler</button></div></div>';

    // Le bandeau — date, heure, écart de front, lieu, les deux flèches de nav —
    // prend la GAUCHE de la rangée d'envoi, sur la même ligne que Améliorer et
    // Parler. Une ligne à lui seul sous la barre poussait le composeur d'un
    // cran vers le haut pour trois mots ; ici il ne coûte pas un pixel de
    // hauteur, et l'on a le lieu et l'heure sous les yeux au moment d'envoyer.
    const rangee = zone.querySelector(".envoi");
    const bandeau = document.getElementById("bandeau");
    if (rangee && bandeau) rangee.prepend(bandeau);

    const champ = document.getElementById("champ-libre");
    const btn = document.getElementById("btn-libre");
    const libre = zone.querySelector(".libre");
    const inter = document.getElementById("mode-input");
    const boutons = {
      dire: document.getElementById("mode-dire"),
      agir: document.getElementById("mode-agir"),
      faire: document.getElementById("mode-faire"),
      penser: document.getElementById("mode-penser"),
      question: document.getElementById("mode-question"),
      meta: document.getElementById("mode-meta"),
      run: document.getElementById("mode-run"),
      intervention: document.getElementById("mode-intervention"),
    };
    const AMORCES = {
      dire: "Vos prochaines paroles…",
      agir: "Ce que vous faites…",
      faire: "Ce que vous changez au monde — l'arbitre tranche…",
      penser: "Ce que vous pesez — ou rien, et vous pesez tout",
      question: "Ce que vous voulez éclaircir — hors de la scène…",
      meta: "Hors univers : la partie, le casting, une médaille à décerner…",
      run: "Une consigne, ou rien — et l'on vous joue comme on vous connaît…",
      intervention: "Ce qu'il faut redresser, développer, ou changer — rien n'est verrouillé…",
    };
    const ENVOIS = {
      dire: '<i class="emb">💬</i>Parler',
      agir: '<i class="emb">✋</i>Agir',
      faire: '<i class="emb">🤲</i>Faire',
      penser: '<i class="emb">💭</i>Peser',
      question: '<i class="emb">❓</i>Demander',
      meta: '<i class="emb">🎬</i>Commenter',
      run: '<i class="emb">🎭</i>Laisser faire',
      intervention: '<i class="emb">✨</i>Intervenir',
    };
    let mode = "dire";

    // Le drapeau survit au rechargement : celui qui écrit mal écrit mal tout
    // le temps, il ne veut pas rearmer son filtre à chaque tour.
    const btnAm = document.getElementById("ameliorer");
    let ameliorer = localStorage.getItem("ameliorer") === "1";
    function marquerAm() {
      btnAm.classList.toggle("actif", ameliorer);
      btnAm.setAttribute("aria-pressed", ameliorer ? "true" : "false");
      // Seul ce qui est DIT ou FAIT se reformule : une question, une remarque
      // de coulisses ou une consigne de « laisser faire » n'a pas de style à
      // tenir — personne dans la fiction ne les entend.
      btnAm.hidden = mode !== "dire" && mode !== "agir";
    }
    btnAm.onclick = () => {
      ameliorer = !ameliorer;
      localStorage.setItem("ameliorer", ameliorer ? "1" : "0");
      marquerAm();
      champ.focus();
    };

    function basculer(m) {
      mode = m;
      inter.dataset.mode = m;
      Object.keys(boutons).forEach((k) => boutons[k].classList.toggle("actif", k === m));
      libre.style.display = "flex";
      champ.className = "mode-" + m;
      champ.placeholder = AMORCES[m];
      btn.innerHTML = ENVOIS[m];
      champ.focus();
      marquerAm();
    }
    Object.keys(boutons).forEach((k) => (boutons[k].onclick = () => basculer(k)));

    // ---- l'homme hors roster parle à son arbitre, pas à la scène ---------
    // Incarner un homme quelconque (siège fabriqué par /bascule) change le
    // canal : ses gestes passent par POST /verbe (habitant.md §3) — tenter,
    // faire, demander, dire — et le verdict de l'arbitre revient DANS la
    // réponse, en synchrone. Le call réveille un vrai `claude -p` : une à
    // trois minutes au premier réveil d'une zone, d'où l'attente affichée.
    // Un PJ du roster ne passe JAMAIS par ici : son chemin /action est intact.
    // penser = un reveil de soi (cast) : la reponse HTTP est un accuse,
    // la pensee vit dans sa chambre — d'ou son retour dans la barre.
    const VERBES_HOMME = { dire: "dire", agir: "tenter", faire: "faire",
                           question: "demander", penser: "penser" };
    function envoyerVerbe(m, texte) {
      const moi = window.Moi;
      // Écho immédiat : /verbe n'inscrit rien au flux de la scène, le sondage
      // ne rendra donc pas cette ligne — on la pose nous-mêmes.
      Bus.chronique(m === "question" ? "chr-question"
        : (m === "dire" ? "chr-vous" : "chr-vous chr-acte"),
        m === "question" ? "Question" : (moi.nom || moi.personnage_id), texte);
      const att = document.getElementById("attente");
      if (att) att.classList.add("actif");
      btn.disabled = true;
      const corps = { de: moi.personnage_id, verbe: VERBES_HOMME[m], texte: texte };
      if (moi.arbitre) corps.a = moi.arbitre;
      fetch("/verbe", { method: "POST",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(corps) })
        .then((r) => r.json())
        .then((d) => Bus.chronique("chr-reponse", "L'arbitre",
          (d && (d.verdict || d.erreur)) || "(pas de verdict)"))
        .catch((e) => Bus.chronique("chr-reponse", "L'arbitre",
          "Le verdict n'est pas revenu : " + e))
        .finally(() => {
          if (att) att.classList.remove("actif");
          btn.disabled = false;
        });
    }

    btn.onclick = () => {
      const v = champ.value.trim();
      // penser sans objet est permis : on pèse toute la situation. Laisser faire
      // sans consigne aussi : c'est même son usage le plus courant.
      if (!v && mode !== "penser" && mode !== "run") return;
      if (window.Moi && window.Moi.hors_roster && VERBES_HOMME[mode]) {
        envoyerVerbe(mode, v);
        champ.value = "";
        return;
      }
      // pas d'affichage optimiste : le serveur inscrit la parole au flux, et on
      // relit aussitôt — une seule source de vérité, qui survit au rechargement.
      Bus.poster({ type: "libre", mode: mode, texte: v,
        ameliorer: ameliorer && (mode === "dire" || mode === "agir") });
      champ.value = "";
      setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
    };
    champ.onkeydown = (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); btn.click(); }
    };
    basculer("dire");

    // La barre se taille au siège : bus.js remplit window.Moi depuis /moi (en
    // parallèle de nous) — on attend cette réponse-là plutôt que d'en refaire
    // une. Hors roster : Faire apparaît, et les modes qui parlent au MJ du
    // JOUEUR (penser, coulisses, laisser faire, intervention) se rangent — cet
    // homme-là n'a que ses quatre verbes vers son arbitre.
    (function tailler(essais) {
      // == et non === : avant que bus.js ait pose son null initial, Moi est
      // UNDEFINED — le === laissait filer ce cas et la taille n'avait jamais
      // lieu (vu au banc du 30.8 : Penser visible chez un homme incarne).
      if (window.Moi == null && essais > 0)
        return setTimeout(() => tailler(essais - 1), 300);
      if (!window.Moi || !window.Moi.hors_roster) return;
      boutons.faire.hidden = false;
      // penser revient (31.8) : c'est un verbe d'homme desormais — un reveil
      // de soi. Seuls les modes MJ-du-joueur se rangent.
      ["meta", "run", "intervention"].forEach((k) => {
        boutons[k].hidden = true;
      });
      if (boutons[mode] && boutons[mode].hidden) basculer("dire");
    })(40);

    // ---- parler à quelqu'un d'un clic ------------------------------------
    // Un visage dans la colonne des présents est une adresse : cliquer dessus
    // ouvre la parole vers lui. On n'envoie rien — on prépare la phrase et on
    // rend la main au joueur, curseur en place. C'est une commodité de saisie,
    // jamais une action : rien ne part tant qu'il n'a pas écrit.
    window.Barre = {
      adresser(nom) {
        if (!nom) return;
        if (mode !== "dire" && mode !== "agir") basculer("dire");
        const v = champ.value;
        const deja = new RegExp("^\\s*" + String(nom).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*,");
        if (!deja.test(v)) champ.value = nom + ", " + v.replace(/^\s+/, "");
        champ.focus();
        const n = champ.value.length;
        champ.setSelectionRange(n, n);
      },
    };
  });

  // La parole du joueur, relue depuis le flux. Elle porte le NOM du personnage,
  // pas « Vous » : dans le fil, une ligne de Rhaenyra doit se lire comme celle
  // de n'importe qui d'autre — c'est la même salle et la même chronique. À deux,
  // celle de l'autre siège prend son nom à lui, et son médaillon s'illumine,
  // parce que parler c'est être là.
  Bus.enregistrer("vous", (it) => {
    const nomDe = (id) => {
      const s = (window.Sieges || []).find((x) => x.personnage_id === id);
      return (s && s.nom) || (window.Moi && window.Moi.personnage_id === id
        && window.Moi.nom) || null;
    };
    let qui = (it.joueur_id && nomDe(it.joueur_id))
      || (window.Moi && window.Moi.nom) || "Vous";
    if (it.joueur_id && window.Moi && it.joueur_id !== window.Moi.personnage_id) {
      if (window.activerLocuteur) window.activerLocuteur(it.joueur_id);
    }
    // ET SON VISAGE AVEC SON NOM. Le fil lui posait un blason — 🗣️ quand il
    // parlait, ✋ quand il agissait —, c'est-à-dire un pictogramme de mode là où
    // tout le monde a une figure. Dans une salle où huit médaillons se
    // ressemblent, le seul homme sans visage était celui qu'on joue. Le
    // portrait vient d'où viennent les autres : la salle d'abord, le registre
    // ensuite (`Gens.qui`), et l'anneau d'office avec.
    const id = it.joueur_id || (window.Moi && window.Moi.personnage_id) || null;
    const p = (window.Gens && id) ? Gens.qui(id) : {};
    const entree = Bus.chronique(
      it.mode === "agir" ? "chr-vous chr-acte" : "chr-vous", qui, it.texte,
      { avatar: p.portrait_svg || "", role: p.titre || "" });
    if (window.Gens && id) Gens.marquer(entree, id);
    // La ligne à reformuler garde son adresse : le MJ renverra la phrase
    // améliorée, et c'est CETTE entrée-là qu'on remplacera — pas une seconde
    // ligne en dessous, qui donnerait à voir le brouillon et sa correction.
    if (entree && it.ref) {
      ATTENDUES[it.ref] = entree;
      if (it.ameliorer) entree.classList.add("chr-brouillon");
    }
    // Le joueur a une main comme les autres. `montre` marchait sur une réplique
    // et sur un geste de PNJ, jamais sur les siens : le personnage pouvait
    // parler de la carte, pas y poser une pièce. Or c'est LUI qui tient le
    // conseil — c'est même le seul dont la main sur la table décide de quelque
    // chose.
    if (entree && window.Illustration) Illustration.poser(entree, it);
  });

  // Les lignes du joueur qui attendent peut-être une réécriture, par référence.
  const ATTENDUES = {};

  // La phrase telle qu'elle aurait dû sortir de sa bouche. Elle REMPLACE le
  // brouillon : rien n'a été dit deux fois, et le temps n'a pas bougé.
  Bus.enregistrer("reecrit", (it) => {
    const entree = ATTENDUES[it.ref];
    if (!entree || !it.texte) return;
    const t = entree.querySelector(".chr-texte");
    if (!t) return;
    t.innerHTML = window.Attention ? Attention.html(it.texte, {}) : it.texte;
    entree.classList.remove("chr-brouillon");
    entree.classList.add("chr-ameliore");
    if (window.Entites) Entites.traiter(entree);
  });

  // Hors fiction : une question posée au narrateur, et sa réponse.
  Bus.enregistrer("question", (it) => Bus.chronique("chr-question", "Question", it.texte));
  Bus.enregistrer("reponse", (it) => Bus.chronique("chr-reponse", "Le narrateur", it.texte));

  // Hors univers : la loge. On y parle de la partie elle-même, jamais dedans —
  // aucun PNJ n'entend, l'horloge ne bouge pas, rien n'entre dans l'état.
  Bus.enregistrer("meta", (it) => Bus.chronique("chr-meta", "En coulisses", it.texte));

  // Les rênes lâchées : ce n'est pas une parole du personnage, c'est le joueur
  // qui s'écarte. On le marque dans le fil pour qu'on sache, en relisant, quels
  // gestes venaient de lui et lesquels ont été joués à sa place.
  Bus.enregistrer("run", (it) =>
    Bus.chronique("chr-run", "Vous laissez faire",
      it.texte || "Sans consigne — on vous joue comme on vous connaît."));
  // L'atelier de chanson. La commande du joueur, puis la fiche rendue : titre,
  // ce que ça raconte, et le fichier .md qu'on vient d'ouvrir au bloc-notes.
  Bus.enregistrer("composer", (it) =>
    Bus.chronique("chr-composer", "À composer",
      it.texte || "Sans consigne — on choisit ce qui mérite d'être chanté."));
  Bus.enregistrer("chanson", (it) => {
    const entree = Bus.chronique("chr-chanson", it.titre || "Chanson", it.texte || "");
    if (!entree) return;
    const corps = entree.querySelector(".chr-corps");
    if (it.style) {
      const s = document.createElement("div");
      s.className = "chanson-style";
      s.textContent = it.style;
      corps.appendChild(s);
    }
    if (it.fichier) {
      const f = document.createElement("div");
      f.className = "chanson-fichier";
      f.textContent = it.fichier;
      corps.appendChild(f);
    }
  });

  Bus.enregistrer("coulisses", (it) => {
    const entree = Bus.chronique("chr-coulisses", it.qui || "Le MJ", it.texte);
    // Une médaille se voit : titre en capitales, ruban, et la citation dessous.
    if (entree && it.medaille) {
      const m = document.createElement("div");
      m.className = "medaille";
      m.innerHTML = '<span class="medaille-ruban">' + (it.embleme || "🎖️") + "</span>" +
        '<span class="medaille-titre"></span>' +
        (it.citation ? '<span class="medaille-citation"></span>' : "");
      m.querySelector(".medaille-titre").textContent = it.medaille;
      if (it.citation) m.querySelector(".medaille-citation").textContent = it.citation;
      entree.querySelector(".chr-corps").appendChild(m);
    }
  });

  // L'intervention divine : la demande du joueur, puis ce que le MJ a
  // réellement redressé. Ces deux-là ne sont pas des coulisses — on n'y
  // commente pas la partie, on la CORRIGE : l'état bouge derrière.
  Bus.enregistrer("intervention", (it) =>
    Bus.chronique("chr-intervention", "Intervention", it.texte));
  Bus.enregistrer("reparation", (it) => {
    const entree = Bus.chronique("chr-reparation", it.qui || "Le fil est repris", it.texte);
    // Ce qui a été touché se dit en clair : le joueur doit savoir ce qui,
    // désormais, fait foi — sinon il rejoue sur une mémoire périmée.
    if (entree && it.touche && it.touche.length) {
      const l = document.createElement("ul");
      l.className = "reparation-touche";
      it.touche.forEach((t) => {
        const li = document.createElement("li");
        li.textContent = t;
        l.appendChild(li);
      });
      entree.querySelector(".chr-corps").appendChild(l);
    }
  });

  // Type "choix" déprécié : ignoré. L'input reste la barre permanente.
  Bus.enregistrer("choix", () => {});

  // L'événement arrive dans le fil, avec son bouton : c'est là qu'on agit.
  Bus.enregistrer("evenement", (it, ctx) => {
    const entree = Bus.chronique("chr-evenement", null, it.texte);
    if (!entree) return;
    const b = document.createElement("button");
    b.className = "bouton-evenement";
    b.textContent = it.bouton || "Voir de quoi il retourne";
    b.onclick = () => ctx.poster({ type: "evenement", texte: it.id || it.texte });
    entree.querySelector(".chr-corps").appendChild(b);
  });
})();
