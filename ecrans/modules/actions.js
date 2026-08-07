// actions.js — la barre unique du joueur : Parler / Agir / Attendre.
// Le temps n'a plus de zone à part : attendre est une action comme les autres.
"use strict";
(() => {
  window.addEventListener("DOMContentLoaded", () => {
    const zone = document.getElementById("fil-actions");
    zone.innerHTML =
      '<div id="mode-input" data-mode="dire">' +
      '<button id="mode-dire" class="actif"><i class="emb">💬</i>Parler</button>' +
      '<button id="mode-agir"><i class="emb">✋</i>Agir</button>' +
      '<button id="mode-penser" title="Peser la situation : ce que vous savez, ce qui s\'offre, ce que ça coûte">' +
      '<i class="emb">💭</i>Penser</button>' +
      '<button id="mode-attendre"><i class="emb">⏳</i>Attendre</button>' +
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
      // Toujours à portée dès qu'il reste du flux à jouer : parler n'interrompt
      // plus la scène, seul ce bouton l'arrête.
      '<button id="pause" class="pulse"><i class="emb">⏸️</i>Couper</button></div>' +
      '<div class="libre">' +
      '<textarea id="champ-libre" class="mode-dire" placeholder="Vos prochaines paroles…"></textarea>' +
      // L'heure de la fiction se tient contre le bouton d'envoi : au moment
      // d'agir, on doit savoir quand on agit sans lever les yeux au bandeau.
      // Améliorer : le joueur écrit vite et mal, le MJ rend la phrase telle
      // qu'elle aurait dû sortir de sa bouche. Ce n'est pas un mode — c'est un
      // filtre sur ce qu'on vient d'écrire, et il ne change ni le sens ni le
      // temps qui passe.
      '<div class="envoi"><span id="heure-barre" hidden></span>' +
      '<button id="ameliorer" title="Le MJ reformule vos mots dans la langue du récit — ' +
      'sans fautes, sans changer ce que vous voulez dire"><i class="emb">✒️</i>' +
      'Améliorer</button>' +
      '<button id="btn-libre"><i class="emb">💬</i>Parler</button></div></div>' +
      '<div id="attentes">' +
      '<button data-attente="avance"><i class="emb">⏱️</i>Un moment passe</button>' +
      '<button data-attente="avance-evenement"><i class="emb">⏭️</i>' +
      'Jusqu\'à ce que quelque chose arrive</button></div>';

    const champ = document.getElementById("champ-libre");
    const btn = document.getElementById("btn-libre");
    const libre = zone.querySelector(".libre");
    const attentes = document.getElementById("attentes");
    const inter = document.getElementById("mode-input");
    const boutons = {
      dire: document.getElementById("mode-dire"),
      agir: document.getElementById("mode-agir"),
      penser: document.getElementById("mode-penser"),
      attendre: document.getElementById("mode-attendre"),
      question: document.getElementById("mode-question"),
      meta: document.getElementById("mode-meta"),
      run: document.getElementById("mode-run"),
    };
    const AMORCES = {
      dire: "Vos prochaines paroles…",
      agir: "Ce que vous faites…",
      penser: "Ce que vous pesez — ou rien, et vous pesez tout",
      question: "Ce que vous voulez éclaircir — hors de la scène…",
      meta: "Hors univers : la partie, le casting, une médaille à décerner…",
      run: "Une consigne, ou rien — et l'on vous joue comme on vous connaît…",
    };
    const ENVOIS = {
      dire: '<i class="emb">💬</i>Parler',
      agir: '<i class="emb">✋</i>Agir',
      penser: '<i class="emb">💭</i>Peser',
      question: '<i class="emb">❓</i>Demander',
      meta: '<i class="emb">🎬</i>Commenter',
      run: '<i class="emb">🎭</i>Laisser faire',
    };
    let mode = "dire";

    // Le drapeau survit au rechargement : celui qui écrit mal écrit mal tout
    // le temps, il ne veut pas rearmer son filtre à chaque tour.
    const btnAm = document.getElementById("ameliorer");
    let ameliorer = localStorage.getItem("ameliorer") === "1";
    function marquerAm() {
      btnAm.classList.toggle("actif", ameliorer);
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
      const attente = m === "attendre";
      libre.style.display = attente ? "none" : "flex";
      attentes.classList.toggle("actif", attente);
      if (!attente) {
        champ.className = "mode-" + m;
        champ.placeholder = AMORCES[m];
        btn.innerHTML = ENVOIS[m];
        champ.focus();
      }
      marquerAm();
    }
    Object.keys(boutons).forEach((k) => (boutons[k].onclick = () => basculer(k)));

    btn.onclick = () => {
      const v = champ.value.trim();
      // penser sans objet est permis : on pèse toute la situation. Laisser faire
      // sans consigne aussi : c'est même son usage le plus courant.
      if (!v && mode !== "penser" && mode !== "run") return;
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
  });

  // La parole du joueur, relue depuis le flux. À deux, la même ligne se lit
  // « Vous » chez celui qui l'a dite et au nom du personnage chez l'autre —
  // et son médaillon s'illumine, parce que parler c'est être là.
  Bus.enregistrer("vous", (it) => {
    let qui = "Vous";
    if (it.joueur_id && window.Moi && it.joueur_id !== window.Moi.personnage_id) {
      const s = (window.Sieges || []).find((x) => x.personnage_id === it.joueur_id);
      qui = (s && s.nom) || it.joueur_id;
      if (window.activerLocuteur) window.activerLocuteur(it.joueur_id);
    }
    const entree = Bus.chronique(
      it.mode === "agir" ? "chr-vous chr-acte" : "chr-vous", qui, it.texte);
    // La ligne à reformuler garde son adresse : le MJ renverra la phrase
    // améliorée, et c'est CETTE entrée-là qu'on remplacera — pas une seconde
    // ligne en dessous, qui donnerait à voir le brouillon et sa correction.
    if (entree && it.ref) {
      ATTENDUES[it.ref] = entree;
      if (it.ameliorer) entree.classList.add("chr-brouillon");
    }
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
