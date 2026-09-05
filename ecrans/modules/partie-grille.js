// partie-grille.js — la position en cases, et l'aire où l'on range à sa guise.
//
// Sorti de `partie.js`, qui tenait déjà le plateau entier : ce fichier ne
// connaît ni le serveur, ni les coups, ni la vue. On lui passe un OUTILLAGE
// (dessiner une carte, savoir ce qu'on tient, poser un coup) et il rend des
// cases. C'est ce qui permet de changer la forme du plateau sans toucher au
// greffe, et de le tester sans navigateur.
//
// Deux choses vivent ici :
//   — LA LIGNE : un objet du plateau, les pièces qu'il engage rangées dedans,
//     et une case vide au bout quand on peut y lâcher quelque chose ;
//   — L'AIRE : des cases libres, sans aucune règle, où le joueur pose ce qu'il
//     veut pour réfléchir. Rien n'en part vers le greffe — c'est un brouillon,
//     et il vit dans le navigateur, pas dans `etat/`.
window.PartieGrille = (function () {
  "use strict";

  const CASES = 12;                 // l'aire : deux rangs de six, ça suffit à trier
  let outil = null;
  // CE QU'UNE CASE DE L'ÉCRAN PORTE, retrouvé depuis le nœud : c'est ce qui
  // permet de dire, pendant un glissé, quel coup CETTE case-là produirait avec
  // la pièce qu'on tient. Une WeakMap plutôt qu'un champ posé sur le nœud : le
  // plateau se redessine en entier à chaque coup, et rien ne doit survivre au
  // DOM qu'on jette.
  const quoi = new WeakMap();

  // les sept emojis de type, ceux de l'échiquier (docs/echiquier.md)
  const TYPES = { cible: "🎯", verrou: "🔒", clef: "🗝️", action: "⚔️",
                  piece: "📦", question: "❓", frappe: "💥" };

  const el = (tag, cls, texte) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texte != null) e.textContent = texte;
    return e;
  };

  // ---- une carte : le signe seul, et le texte AU SURVOL --------------------
  // Le plateau était un mur de prose : vingt-neuf pavés de trois lignes, dont
  // une question de deux cents caractères qui tombait à trois mots par ligne
  // dans une colonne de 210 px. Le texte n'a pas disparu — il est là où on va
  // le chercher : sur la carte qu'on regarde, et une seule à la fois.
  // LA TEINTE SUIT LA MÊME RÈGLE QUE L'EMOJI DU GREFFE : noir, vert et arbitre
  // ont la leur ; les autres camps prennent 🔵 🔴 🟡 🟣 dans l'ordre d'entrée
  // dans la partie. `decks` porte les camps dans cet ordre.
  function teinte(camp) {
    if (!camp || camp === "noir" || camp === "vert" || camp === "arbitre") return camp || "noir";
    const camps = Object.keys((outil.vue() && outil.vue().decks) || {})
      .filter((x) => x !== "noir" && x !== "vert" && x !== "arbitre");
    const i = camps.indexOf(camp);
    return i < 0 ? "autre" : String(i + 1);
  }

  function carte(c) {
    const d = el("div", "pc-carte pc-" + c.type + " pc-app-" + (c.apparence || "libre")
                        + " pc-camp-" + (c.camp || "noir") + " pc-teinte-" + teinte(c.camp));
    d.dataset.id = c.id;
    quoi.set(d, c);   // la case se souvient de SON objet : c'est lui qui dira le coup
    // LE SIGNE DIT LA CHOSE (une porte, une bête, un corps), LE TYPE SE LIT EN
    // COIN. `signe` vient du greffe, deviné du texte ; à défaut c'est le type.
    d.appendChild(el("span", "pc-type", c.signe || c.emoji));
    if (c.signe && c.signe !== TYPES[c.type]) d.appendChild(el("span", "pc-sorte", TYPES[c.type] || c.emoji));
    const t = el("div", "pc-texte");
    t.appendChild(el("div", "pc-titre", c.titre || ""));
    if (c.corps) t.appendChild(el("div", "pc-corps", c.corps));
    if (c.pied && (c.pied.gauche || c.pied.droite)) {
      const p = el("div", "pc-pied");
      p.appendChild(el("span", "pc-pied-g", c.pied.gauche || ""));
      p.appendChild(el("span", "pc-pied-d", c.pied.droite || ""));
      t.appendChild(p);
    }
    // LA CROIX DU VOLET — elle ne sert qu'une fois épinglé, et elle est là
    // parce qu'un volet qui reste sans moyen de le fermer est un volet qui
    // gêne. Elle mange le clic pour ne pas dés-épingler par la bande.
    const croix = el("span", "pc-croix", "×");
    croix.title = "fermer";
    croix.addEventListener("click", (e) => { e.stopPropagation(); d.classList.remove("pc-epingle"); });
    t.appendChild(croix);
    d.appendChild(t);
    // UN CLIC ÉPINGLE LE VOLET. Au survol seul, on ne peut ni relire une carte
    // en regardant le reste du plateau, ni comparer deux textes, ni copier une
    // ligne : le volet meurt dès qu'on bouge la souris. Un seul volet épinglé à
    // la fois — deux textes de 300 px l'un sur l'autre ne se lisent pas.
    // Les cartes qui ont déjà un métier au clic (une question qu'on relève)
    // gardent le leur.
    d.addEventListener("click", (e) => {
      if (e.target && e.target.closest && e.target.closest(".pc-quest, .pc-rep, .pc-croix")) return;
      if (d.classList.contains("pc-cliquable")) return;
      const deja = d.classList.contains("pc-epingle");
      const h = plateau();
      if (h) h.querySelectorAll(".pc-epingle").forEach((x) => x.classList.remove("pc-epingle"));
      if (!deja) { d.classList.add("pc-epingle"); placer(d, t); }
    });
    // LE STATUT SE LIT SUR LA CARTE, pas seulement au survol. Il n'etait ecrit
    // que dans le volet et dans le nom des rangees du deck : sur le plateau il
    // ne restait qu'un style de bordure a interpreter — pointillee pour ce qui
    // arrive, pale pour ce qui se remet —, et une piece posee sous une clef
    // n'avait plus de rangee pour la nommer. Le mot vient du greffe
    // (`pied.droite`) : libre, posee, dans 4 j, se remet, attend l'arbitre,
    // detruite. « tient » ne s'ecrit pas : une clef qui tient est l'etat
    // normal, et un bandeau sur chaque bonne nouvelle est du bruit.
    // UNE QUESTION QU'ON PEUT RELEVER LE DIT DANS SON BANDEAU. La poignee ⚔️
    // ne parait qu'au survol, sur une carte de 65 px au fond d'une colonne qui
    // defile : personne ne la trouve. Le bandeau, lui, est toujours la.
    if (c.type === "question" && c.repondre) c.pied = { gauche: "", droite: "⚔️ à répondre" };
    const statut = (c.pied || {}).droite;
    if (statut && statut !== "✅ tient") d.appendChild(el("span", "pc-etat", court(statut)));
    // LE FILET DU SURVOL. Tant que le plateau se croit « en main », la CSS
    // masque tous les volets de texte (`pc-en-main .pc-texte`) — c'est voulu
    // pendant un glissé, et c'est un écran mort si l'état reste collé. Il le
    // restait : un lâcher redessine le plateau, la carte qu'on tenait s'en va
    // avec, et son `dragend` n'a plus de chemin jusqu'au document. On ne tient
    // plus rien, donc on rallume — au premier survol, là où le manque se voit.
    // (Les événements de souris sont suspendus pendant un vrai glissé : ce
    // rattrapage ne peut pas éteindre une lumière en cours.)
    d.addEventListener("mouseenter", () => {
      const h = plateau();
      if (!outil.tenue() && h && h.classList.contains("pc-en-main")) eteindre();
      placer(d, t);
    });
    if (c.neuf) d.classList.add("pc-neuf");
    if (c.touche != null) d.dataset.touche = c.touche;
    if (c.visee) d.appendChild(el("span", "pc-visee", "💥"));
    if (c.questionnable) d.appendChild(poignee(c));
    if (c.repondre) {
      d.appendChild(repondeur(c));
      // LA CARTE ENTIERE REPOND, pas seulement sa poignee. Une pastille de 28 px
      // au coin d'une carte qu'on peut GLISSER est le pire bouton du plateau :
      // appuyer dessus commence un glisse, et le clic n'arrive jamais. Le
      // ❓ lui-meme se clique donc en plein, et c'est le geste que tout le
      // monde essaie d'abord.
      if (c.type === "question") {
        d.classList.add("pc-cliquable");
        d.addEventListener("click", () => demanderMaillon(d, c));
      }
    } else if (c.type === "question") {
      // ET CELLE QU'ON NE PEUT PAS RELEVER DIT POURQUOI. Quatre questions sur
      // cinq d'une position ne se repondent par aucun geste — celles posees sur
      // un ETAT (aucun maillon ne leve leur suspension : c'est l'arbitre qui
      // tranche en constatant) et celles qu'on a posees soi-meme. Elles
      // avalaient le clic en silence, ce qui se lit comme un ecran casse.
      d.classList.add("pc-inerte");
      d.addEventListener("click", () => outil.dire && outil.dire(
        "Cette question-la ne se releve par aucun geste : un maillon ne relache "
        + "qu'une clef, un verrou ou une frappe A VOUS. Posee sur un etat — ou sur "
        + "une piece d'en face — elle se paie en travail, et l'arbitre tranche en "
        + "constatant."));
    }
    if (c.type === "piece" && c.source) d.dataset.source = c.source;
    d.addEventListener("contextmenu", (e) => {   // clic droit : copier l'id
      e.preventDefault();
      try { navigator.clipboard.writeText(String(c.id || "")); } catch (x) { /* pas de presse-papiers */ }
      if (outil.dire) outil.dire("copié : " + c.id);
    });
    visuel(d, c);            // les halos, bords et coins — le statut en forme
    t.appendChild(fiche(c)); // et TOUT dans le volet, en signes
    armer(d, c);
    return d;
  }

  // ---- LE STATUT EN FORME : bord, halo, opacité, coin ----------------------
  // Un vocabulaire court et orthogonal, chaque canal dit UNE chose :
  //   fond      = à qui (la teinte du camp, déjà posée)
  //   bord      = le verdict : plein tient · pointillé pas encore là · grisé hors jeu
  //   halo      = ce qui RÉCLAME un geste — trois seulement, sinon ce n'est plus un halo :
  //               orange = à moi de répondre · or = mûr à constater · rouge = frappe qui vient
  //   opacité   = disponible ou pris
  //   coin      = ce qui pend dessus (❓ 💥 ⏳ ● neuf — déjà posés par la carte)
  // Tout en classes ; la CSS ne touche jamais `transform` (le volet fixe en dépend).
  function visuel(d, c) {
    const v = outil.vue() || {};
    // un état dit son constat dans son CORPS (« acquis », « constaté faux »),
    // pas dans son pied : on lit les deux
    const st = (((c.pied || {}).droite || "") + " " + (c.corps || "")).toLowerCase();
    const app = c.apparence || "";
    const moi = aNous(c);
    // bord
    if (/dans \d+ j|attend l'arbitre|prêt|pret/.test(st) || app === "route") d.classList.add("pc-v-avenir");
    if (/se remet|tombé|tombe|levé|leve|retir/.test(st) || app === "remet") d.classList.add("pc-v-hors");
    if (/détruite|detruite/.test(st) || app === "detruite") d.classList.add("pc-v-mort");
    if (/sans ressource/.test(st)) d.classList.add("pc-v-creux");
    if (/tenu/.test(st) && c.type === "clef") d.classList.add("pc-v-office");
    if (app === "vrai" || /acquis|constaté vrai|constate vrai/.test(st)) d.classList.add("pc-v-vrai");
    if (/faux/.test(st) && c.type === "cible") d.classList.add("pc-v-faux");
    // opacité : pris
    if (app === "posee" || /posée|posee/.test(st)) d.classList.add("pc-v-pris");
    // halos
    const questions = (c.sous || []).filter((x) => x.type === "question");
    const ouverte = questions.some((q) => /attente/.test(((q.pied || {}).droite || "")));
    if (/suspendu/.test(st) || ouverte) d.classList.add("pc-v-suspendu");
    if ((/suspendu/.test(st) || ouverte) && moi && c.type !== "question") d.classList.add("pc-v-amoi");
    if (((v.signale || {}).constatables || []).map(String).indexOf(String(c.id)) >= 0) d.classList.add("pc-v-mur");
    if (c.visee && moi) d.classList.add("pc-v-vise");
    if (c.type === "piece" && dernieres(v).has(String(c.id))) d.classList.add("pc-v-derniere");
  }

  // LA DERNIÈRE PIÈCE POSÉE DE CHAQUE CAMP glow en bleu : c'est là que le
  // plateau a bougé en dernier, et c'est la première chose qu'un joueur qui
  // revient veut voir. Une par camp — la pièce ENGAGÉE touchée par la ligne
  // la plus récente (`touche`, posé par le greffe). Calculé une fois par vue.
  let dernieresCache = { n: -1, ids: new Set() };
  function dernieres(v) {
    if (dernieresCache.n === (v.dernier || 0)) return dernieresCache.ids;
    const d = v.deck || {};
    const toutes = [].concat(d.main || [], d.route || [], d.remet || [], d.posees || [], v.eux || []);
    const parCamp = {};
    toutes.forEach((c) => {
      if (!c.engagee_par || !c.engagee_par.length) return;
      const t = c.touche || 0;
      if (!parCamp[c.camp] || t > parCamp[c.camp].t) parCamp[c.camp] = { t: t, id: String(c.id) };
    });
    dernieresCache = { n: v.dernier || 0, ids: new Set(Object.values(parCamp).map((x) => x.id)) };
    return dernieresCache.ids;
  }

  // ---- LA FICHE : tout ce que la carte est, en une ligne de signes ---------
  // Le volet disait le titre et deux pieds. Il dit maintenant, en signes et sans
  // phrase : le camp, le type, le statut, ce qui la tient, ce qui pend dessus.
  const LIB = { cible: "état", verrou: "verrou", clef: "clef", action: "action",
                piece: "pièce", question: "question", frappe: "frappe" };
  function fiche(c) {
    const f = el("div", "pc-fiche");
    const puce = (txt, cls) => { const s = el("span", "pc-puce" + (cls ? " " + cls : ""), txt); f.appendChild(s); return s; };
    // L'ID D'ABORD, tel que le greffe le connaît : c'est ce qu'on recopie dans
    // une commande ou qu'on dit au mestre (« justifie t-stats »). Un clic le
    // copie — le volet ne prend pas la souris, donc c'est la carte qui écoute.
    puce("#" + (c.id || ""), "pc-puce-id");
    puce(rond(c.camp) + " " + (c.camp || ""), "pc-puce-camp");
    puce((TYPES[c.type] || c.emoji || "") + " " + (LIB[c.type] || c.type));
    const st = (c.pied || {}).droite;
    if (st) puce(st, "pc-puce-statut");
    if (c.engagee_par && c.engagee_par.length) puce("📍 " + c.engagee_par.join(", "), "pc-puce-pris");
    const q = (c.sous || []).filter((x) => x.type === "question");
    if (q.length) puce("❓ ×" + q.length + (q.some((x) => /attente/.test((x.pied || {}).droite || "")) ? " en attente" : ""), "pc-puce-q");
    if (c.visee) puce("💥 visée", "pc-puce-danger");
    if (c.neuf) puce("● neuf", "pc-puce-neuf");
    if (c.source) f.appendChild(el("div", "pc-fiche-src", "— " + c.source));
    return f;
  }

  // ---- LE ❓ : EXIGER LA CHAÎNE D'UNE PIÈCE D'EN FACE ----------------------
  // Le seul coup de l'écran qui ne soit pas un glissé, et c'est logique : une
  // question n'engage aucune pièce. Elle se paie d'une autre monnaie — une
  // seule fois par pièce dans toute la partie —, donc elle ne se glisse pas,
  // elle se clique. La poignée ne paraît qu'au survol, jamais pendant qu'on
  // tient une carte, et SEULEMENT là où le greffe dirait oui : `questionnable`
  // est écrit par `partie_cartes`, du même jugement que `partie_validite`.
  function poignee(c) {
    const b = el("span", "pc-quest", "❓");
    b.draggable = false;
    b.addEventListener("mousedown", (e) => e.stopPropagation());
    b.title = "Exiger la chaîne de « " + (c.titre || "") + " »";
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      bulle(b, "Qu'exigez-vous de « " + (c.titre || "") + " » ?",
            "par quoi, par qui, à quelle date", "Exiger",
            (texte) => outil.jouer({ quoi: "justifier", sur: c.id, texte: texte }));
    });
    return b;
  }

  // Le bandeau fait 65 px de large : « attend l'arbitre » y tombe a « attend
  // l'a… », ce qui ne dit plus rien. On raccourcit CES DEUX MOTS-LA, et eux
  // seuls — la phrase entiere du greffe reste dans le volet, a un survol.
  const COURT = { "attend l'arbitre": "arbitre ?" };
  const court = (m) => COURT[m] || String(m).replace("se remet · ", "remet ");

  // ---- LE MAILLON : REPONDRE A UN ❓ POSE SUR NOTRE PIECE ------------------
  // Le pendant de la poignee ❓, et il manquait : on pouvait suspendre la piece
  // d'en face depuis l'ecran sans que son camp puisse la relever. Une clef
  // suspendue ne prevaut plus — tant que le maillon n'est pas ecrit, elle est
  // morte sur la table, et la seule sortie passait par le mestre.
  // Gratuit : repondre n'engage pas une piece de plus, ca dit ce qu'on a fait
  // de celles qui sont deja posees. La poignee ne parait que sur NOS cartes
  // suspendues (`suspendue`, ecrit par partie_marques).
  function repondeur(c) {
    const b = el("span", "pc-rep", "⚔️");
    b.title = "Repondre : ecrire le maillon";
    // LE GLISSE MANGEAIT LE CLIC. La carte porteuse est une des notres, donc
    // `draggable` : un appui sur la poignee demarrait le glisse de la carte et
    // le clic ne venait jamais. On rend la poignee non tractable, et le
    // `dragstart` de la carte se retire quand il part d'elle.
    b.draggable = false;
    b.addEventListener("mousedown", (e) => e.stopPropagation());
    b.addEventListener("click", (e) => { e.stopPropagation(); demanderMaillon(b, c); });
    return b;
  }

  function demanderMaillon(ancre, c) {
    bulle(ancre, "Par quoi ? La reponse a la question",
          "qui, avec quoi, quel jour", "Repondre",
          (texte) => outil.jouer({ quoi: "maillon", sur: c.repondre, texte: texte }));
  }

  // LE VOLET EST EN REPÈRE FIXE, placé au survol. Posé en absolu sous la carte,
  // il sortait de l'écran au bas du deck et le `overflow:auto` du deck le
  // coupait — même raison que la bulle de pose. Dessous si la place y est,
  // sinon dessus ; jamais hors du bord droit.
  function placer(d, t) {
    const r = d.getBoundingClientRect();
    t.style.display = "block";
    const h = t.offsetHeight, w = t.offsetWidth || 300;
    t.style.display = "";
    const H = window.innerHeight || document.documentElement.clientHeight;
    const W = window.innerWidth || document.documentElement.clientWidth;
    t.style.left = Math.max(6, Math.min(r.left, W - w - 6)) + "px";
    // TOUJOURS AU-DESSUS, et par en dessous seulement s'il n'y a pas la place.
    // Le volet s'ouvrait sous la carte par defaut : dans le deck, en bas de
    // l'ecran, il tombait hors du cadre, et dans une colonne il couvrait la
    // rangee suivante — c'est-a-dire justement les cartes qu'on est en train de
    // comparer. Au-dessus, il ne couvre que ce qu'on vient de lire.
    const dessus = r.top - 6 - h;
    t.style.top = (dessus >= 6 ? dessus : Math.min(r.bottom + 4, Math.max(6, H - h - 6))) + "px";
  }

  // ---- le geste : on prend une carte, on la pose sur une autre -------------
  const aNous = (c) => c.camp === (outil.vue() && outil.vue().camp);
  // Ce qu'une pièce en main peut atteindre. La règle est ici, en trois lignes,
  // et elle est la même que celle du greffier : un obstacle ou une frappe d'en
  // face, une de nos clefs. Le reste ne s'allume pas.
  // Depuis le 5.9 un ÉTAT est une cible, des deux camps : une pièce sur un
  // état d'en face pose un verrou, sur un des nôtres une clef qui le sert.
  // Sans ça, une partie qui s'ouvre n'offrait aucun geste.
  // `vrai` n'est pas un champ des cartes servies : le greffe dit l'état constaté
  // par son APPARENCE. Une clef ne sert plus un état à nous déjà constaté vrai
  // (partie_gestes, branche `lever`) ; un verrou sur un état d'en face reste
  // recevable, constaté ou non. On s'allume donc sur exactement ce que le greffe
  // accepte — une lumière qui promet un coup refusé est pire que pas de lumière.
  const cible = (c) => (c.type === "verrou") || (c.type === "frappe" && !aNous(c))
                    || (c.type === "clef" && aNous(c))
                    || (c.type === "cible" && !(aNous(c) && c.apparence === "vrai"));
  // TOUTE PIÈCE À NOUS SE PREND, libre ou non : l'aire de rangement accepte ce
  // que le plateau refuse, et une pièce qu'on ne peut pas soulever ne peut pas
  // non plus être mise de côté pour y penser. Ce qui est illégal se refuse au
  // greffe, avec sa phrase — pas en rendant la carte inerte.
  const prenable = (c) => (c.type === "piece" && aNous(c))
                       || ((c.type === "clef" || c.type === "verrou") && aNous(c));

  // ---- CE QUE LE GESTE FERAIT, DIT SUR LA CIBLE ELLE-MÊME -----------------
  // Le glissé n'allumait qu'une chose : « ici, oui ». Il ne disait pas CE QUE
  // ça ferait — et la même pièce produit quatre coups différents selon l'endroit
  // où on la lâche : une clef, un renfort, une garde, un verrou. Le joueur ne
  // l'apprenait qu'après coup, à la phrase du greffier : l'ordre inverse de
  // celui qu'on veut, puisqu'on décide avant de lâcher.
  //
  // LA RÈGLE EST CELLE DE `partie_gestes.poser`, RECOPIÉE ICI ET NULLE PART
  // AILLEURS. Si les deux divergent, c'est cette fonction qui ment au joueur :
  // elle se relit contre le module python, jamais contre le souvenir qu'on en a.
  function geste(piece, sur) {
    if (!piece || piece.type !== "piece" || !sur || !cible(sur)) return null;
    if (sur.type === "verrou")
      return (aNous(sur) || dejaUneClef(sur.id)) ? { signe: "\u2795", mot: "renfort" }
                                                 : { signe: "\ud83d\udddd\ufe0f", mot: "clef" };
    if (sur.type === "clef") return { signe: "\u2795", mot: "renfort" };
    if (sur.type === "frappe") return { signe: "\ud83d\udd12", mot: "garde" };
    if (sur.type === "cible")
      return aNous(sur) ? { signe: "\ud83d\udddd\ufe0f", mot: "clef" }
                        : { signe: "\ud83d\udd12", mot: "verrou" };
    return null;
  }

  // Ce qu'on tient éclaire D'UN COUP tout ce qu'il peut atteindre, et chaque
  // endroit porte le signe du coup qu'il produirait : les cartes, les cases
  // vides au bout de leur ligne, et le deck quand ce qu'on tient s'y reprend.
  // Le mot sort au survol seulement — sur une case de 54 px il n'y a place que
  // pour le signe tant qu'on n'a pas choisi.
  const plateau = () => document.getElementById("partie");

  function allumer(tenue) {
    const h = plateau();
    if (!h || !tenue) return;
    h.classList.add("pc-en-main");
    if (tenue.type !== "piece") {
      // une clef, un verrou à nous : le seul endroit qui les reçoit est le deck
      const deck = h.querySelector(".pc-deck");
      if (deck) marquer(deck, { signe: "\ud83d\uddd1\ufe0f", mot: "reprendre" });
      tracer();
      return;
    }
    h.querySelectorAll("[data-jouable='1']").forEach((x) => {
      const g = geste(tenue, quoi.get(x));
      if (g) marquer(x, g);
    });
    tracer();
  }

  function marquer(x, g) {
    x.classList.add("pc-appel");
    x.dataset.geste = g.signe;
    x.dataset.mot = g.mot;
    x.dataset.coup = g.mot;
  }

  // ---- LES LIENS : d'où part la carte, où elle peut aller, et ce que ça fait
  // Le signe du coup était écrit sur la cible (`data-geste`) et rien ne
  // l'affichait : l'écran s'allumait sans dire lequel des quatre coups il
  // proposait, et le mot n'arrivait qu'après le lâcher, par la phrase du
  // greffier — l'ordre inverse de celui qu'on veut. Chaque cible porte donc
  // maintenant son signe ET son mot, en clair, et un trait courbe la relie à
  // la carte qu'on tient, de la couleur du coup.
  //
  // La couche est en repère FIXE et posée sur le body, jamais dans le plateau :
  // le deck a son `overflow:auto` et coupait tout ce qui dépassait d'une carte
  // (même raison que le volet de texte et la bulle de pose).
  const COULEURS = { clef: "--or-joueur", renfort: "--vert", verrou: "--sang",
                     garde: "--sang", reprendre: "--muted" };
  const SECOURS = { clef: "#c9a227", renfort: "#4a7c4e", verrou: "#9b2c2c",
                    garde: "#9b2c2c", reprendre: "#8a8f88" };
  let couche = null;

  function couleur(cs, mot) {
    const v = cs.getPropertyValue(COULEURS[mot] || "--or-joueur").trim();
    return v || SECOURS[mot] || SECOURS.clef;
  }

  function tracer() {
    effacer();
    const h = plateau();
    const src = h && h.querySelector(".pc-tenue");
    const buts = h ? [...h.querySelectorAll(".pc-appel")] : [];
    if (!h || !src || !buts.length) return;
    const cs = getComputedStyle(h);
    const r0 = src.getBoundingClientRect();
    const sx = r0.left + r0.width / 2, sy = r0.top + r0.height / 2;

    couche = document.createElement("div");
    couche.className = "pc-liens";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "pc-liens-svg");
    couche.appendChild(svg);

    buts.forEach((b) => {
      const mot = b.dataset.mot || "clef";
      const col = couleur(cs, mot);
      const r = b.getBoundingClientRect();
      const tx = r.left + r.width / 2, ty = r.top + r.height / 2;
      // LE TRAIT SE COURBE, il ne coupe pas. Une droite entre deux cases d'une
      // même grille passe sur les cases du milieu et l'on ne sait plus qui elle
      // joint ; l'arc s'en écarte d'un cinquième de sa longueur, du côté du
      // dessus, et l'on suit chaque lien de l'oeil sans le perdre.
      const dx = tx - sx, dy = ty - sy;
      const d = Math.hypot(dx, dy) || 1;
      const cx = (sx + tx) / 2 - (dy / d) * d * 0.2;
      const cy = (sy + ty) / 2 + (dx / d) * d * 0.2;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M" + sx + "," + sy + " Q" + cx + "," + cy + " " + tx + "," + ty);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", col);
      path.setAttribute("stroke-width", "2");
      path.setAttribute("stroke-linecap", "round");
      path.setAttribute("class", "pc-lien");
      svg.appendChild(path);
      const pt = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      pt.setAttribute("cx", tx); pt.setAttribute("cy", ty);
      pt.setAttribute("r", "3.5"); pt.setAttribute("fill", col);
      svg.appendChild(pt);

      // l'étiquette : le signe du coup et son mot, au-dessus de la cible
      const et = document.createElement("div");
      et.className = "pc-etiq";
      et.style.borderColor = col;
      et.style.setProperty("--c", col);
      et.appendChild(Object.assign(document.createElement("span"),
        { className: "pc-etiq-s", textContent: b.dataset.geste || "" }));
      et.appendChild(Object.assign(document.createElement("span"),
        { className: "pc-etiq-m", textContent: mot }));
      et.style.left = tx + "px";
      et.style.top = (r.top - 6) + "px";
      couche.appendChild(et);
    });
    document.body.appendChild(couche);
  }

  function effacer() {
    if (couche && couche.parentNode) couche.parentNode.removeChild(couche);
    couche = null;
  }

  function eteindre() {
    effacer();
    const h = plateau();
    if (!h) return;
    h.classList.remove("pc-en-main");
    h.querySelectorAll(".pc-appel, .pc-tenue, .pc-survol").forEach((x) => {
      x.classList.remove("pc-appel", "pc-tenue", "pc-survol");
      delete x.dataset.geste;
      delete x.dataset.mot;
    });
  }

  // UN LÂCHER REDESSINE LE PLATEAU, et la carte qu'on tenait s'en va avec :
  // son `dragend` peut alors ne jamais venir, et l'écran resterait éteint à
  // 42 % d'opacité sans que rien ne le rallume. On écoute donc aussi le
  // document, une fois pour toutes.
  document.addEventListener("dragend", eteindre, true);
  document.addEventListener("drop", eteindre, true);

  function armer(d, c) {
    if (prenable(c)) {
      d.draggable = true;
      if (c.apparence === "libre" || c.type !== "piece") d.classList.add("pc-prenable");
      d.addEventListener("dragstart", (e) => {
        if (e.target && e.target.closest && e.target.closest(".pc-quest, .pc-rep")) {
          e.preventDefault();   // on clique une poignee, on ne traine pas la carte
          return;
        }
        outil.tenue(c);
        e.dataTransfer.setData("text/plain", c.id);
        e.dataTransfer.effectAllowed = "move";
        d.classList.add("pc-tenue");
        allumer(c);
      });
      d.addEventListener("dragend", () => {
        outil.tenue(null);
        eteindre();
      });
    }
    if (cible(c)) {
      d.dataset.jouable = "1";
      d.addEventListener("dragover", (e) => {
        const t = outil.tenue();
        if (!t || t.type !== "piece") return;
        e.preventDefault();
        d.classList.add("pc-survol");
      });
      d.addEventListener("dragleave", () => d.classList.remove("pc-survol"));
      d.addEventListener("drop", (e) => {
        e.preventDefault();
        d.classList.remove("pc-survol");
        const t = outil.tenue();
        if (!t || t.type !== "piece") return;
        poser(t, c, d);
      });
    }
  }

  // ---- ce qu'on demande avant d'écrire ------------------------------------
  // Sur un verrou qu'aucune de nos clefs ne touche encore, sur un état — le
  // titre d'un verrou neuf, d'une clef neuve, est au joueur. Ailleurs (renfort,
  // garde) il n'y a rien à nommer : le coup part sans rien demander.
  function poser(piece, sur, ancre) {
    const neuf = (sur.type === "verrou" && !aNous(sur) && !dejaUneClef(sur.id))
              || sur.type === "cible";
    if (!neuf) return outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id });
    const contre = sur.type === "cible" && aNous(sur) ? " pour « " : " contre « ";
    const prep = noteDe(outil.vue(), piece.id);
    bulle(ancre, "Et " + piece.titre + " y fait quoi ?", prep || (piece.titre + contre + sur.titre + " »"),
          "Poser", (texte) => outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id, texte: texte || prep }));
  }

  const dejaUneClef = (bid) => ((outil.vue() || {}).fronts || []).some(
    (f) => f.id === bid && (f.pile || []).some((o) => o.type === "clef" && aNous(o)));

  // La bulle est posée sur le CORPS, en repère fixe, et non dans la carte : la
  // colonne des fronts défile en `overflow:auto`, et une bulle qui y vivrait
  // serait coupée au bord dès que le front est près de la marge.
  function bulle(ancre, titre, placeholder, verbe, valider) {
    document.querySelectorAll(".pc-bulle").forEach((x) => x.remove());
    const b = el("div", "pc-bulle");
    const r = ancre.getBoundingClientRect();
    const H = window.innerHeight || document.documentElement.clientHeight;
    const W = window.innerWidth || document.documentElement.clientWidth;
    b.style.left = Math.max(8, Math.min(r.left, W - 266)) + "px";
    b.style.top = Math.min(r.bottom + 4, H - 130) + "px";
    b.appendChild(el("div", "pc-bulle-t", titre));
    const champ = document.createElement("input");
    champ.type = "text";
    champ.placeholder = placeholder;
    b.appendChild(champ);
    const pied = el("div", "pc-bulle-p");
    const ok = el("button", "pc-bt", verbe);
    const non = el("button", "pc-bt pc-bt-nu", "Laisser");
    pied.appendChild(non); pied.appendChild(ok);
    b.appendChild(pied);
    document.body.appendChild(b);
    champ.focus();
    const partir = () => b.remove();
    const aller = () => { const t = champ.value.trim(); partir(); valider(t); };
    ok.addEventListener("click", aller);
    non.addEventListener("click", partir);
    champ.addEventListener("keydown", (e) => {
      if (e.key === "Enter") aller();
      if (e.key === "Escape") partir();
    });
  }

  // Les pièces indexées par CE QUI LES ENGAGE, comme le fait le greffe. La vue
  // les retire des cartes filles d'une clef — elles y répétaient son titre —,
  // donc c'est ici qu'on les retrouve pour les remettre à leur place.
  function engagees(vue) {
    const d = (vue && vue.deck) || {};
    const out = {};
    [].concat(d.main || [], d.route || [], d.remet || [], d.posees || [],
              d.detruites || [], (vue && vue.eux) || [])
      .forEach((c) => (c.engagee_par || []).forEach((q) => {
        (out[q] = out[q] || []).push(c);
      }));
    return out;
  }

  // ---- une case qui reçoit -------------------------------------------------
  function receveuse(cls, accepte, lache) {
    const v = el("div", cls);
    v.addEventListener("dragover", (e) => {
      if (!accepte(outil.tenue())) return;
      e.preventDefault();
      v.classList.add("pc-survol");
    });
    v.addEventListener("dragleave", () => v.classList.remove("pc-survol"));
    v.addEventListener("drop", (e) => {
      e.preventDefault();
      v.classList.remove("pc-survol");
      const t = outil.tenue();
      if (!accepte(t)) return;
      lache(t, v);
    });
    return v;
  }

  // ---- la ligne : un objet, ce qu'il engage, et où lâcher -------------------
  function ligne(o, eng, cls) {
    const l = el("div", "pc-ligne" + (cls ? " " + cls : ""));
    l.appendChild(carte(o));
    (eng[o.id] || []).forEach((p) => {
      const cp = carte(p);
      cp.classList.add("pc-mise");
      l.appendChild(cp);
    });
    // Une case vide au bout dit qu'on peut lâcher là ; sur un objet hors
    // d'atteinte il n'y en a pas. La règle s'apprend sans se lire.
    if (cible(o)) {
      const v = receveuse("pc-case", (t) => t && t.type === "piece", (t, c) => poser(t, o, c));
      // la case porte le MÊME objet que la carte de tête : elle s'allume donc du
      // même signe, et l'on vise l'une ou l'autre indifféremment
      quoi.set(v, o);
      v.dataset.jouable = "1";
      l.appendChild(v);
    }
    return l;
  }

  // ---- les états cibles : une rangée par racine ----------------------------
  // Chaque racine ouvre sa rangée : sa case 🎯, ce qu'elle sert en plus petit,
  // et les questions ❓ posées dessus. C'est l'en-tête de la grille : un
  // verrou se pose SUR un état, et l'on doit voir sur quoi.
  function desseins(vue) {
    const cibles = (vue && vue.cibles) || [];
    const d = el("div", "pc-desseins");
    if (!cibles.length) return d;
    const parParent = {};
    cibles.forEach((c) => { (parParent[c.sert || ""] = parParent[c.sert || ""] || []).push(c); });
    (parParent[""] || []).forEach((r) => {
      const rangee = el("div", "pc-dessein pc-camp-" + (r.camp || ""));
      rangee.appendChild(carte(r));
      const pose = (c, cls) => {
        (c.sous || []).forEach((q) => { const cq = carte(q); cq.classList.add("pc-sur"); rangee.appendChild(cq); });
        (parParent[c.id] || []).forEach((f) => {
          const cf = carte(f); cf.classList.add(cls); rangee.appendChild(cf);
          pose(f, cls);
        });
      };
      pose(r, "pc-fils");
      // UNE CASE 🎯 VIDE au bout de chacune de nos rangées : on y écrit l'état
      // suivant. Ce n'est pas un menu — c'est une case, comme les autres, où
      // l'on pose une phrase au lieu d'une pièce. Sous la racine seulement :
      // un état se pose sous son parent, et le parent naturel est la racine.
      if (aNous(r) && r.apparence !== "vrai") rangee.appendChild(viseur(r));
      d.appendChild(rangee);
    });
    return d;
  }

  // LA CASE 📦 VIDE au bout de « En main » : on y écrit ce qu'on demande au
  // mestre. Gratuit, hors compte ; la pièce arrive « attend l'arbitre » et
  // n'existe qu'une fois accordée. Une phrase suffit — le lieu et le tenant,
  // c'est l'arbitre qui les corrige.
  function demandeur() {
    const v = el("div", "pc-case pc-viseur pc-demandeur");
    v.title = "Demander une pièce au mestre";
    v.appendChild(el("span", "pc-type", "📦"));
    v.addEventListener("click", () => bulle(v, "Ce qu'il vous faut, et où",
      "une pièce : qui, quoi, où — le mestre l'arbitre", "Demander",
      (texte) => outil.jouer({ quoi: "demander", texte: texte })));
    return v;
  }

  function viseur(parent) {
    const v = el("div", "pc-case pc-viseur");
    v.title = "Écrire un état qui sert « " + parent.titre + " »";
    v.appendChild(el("span", "pc-type", "🎯"));
    v.addEventListener("click", () => bulle(v, "Ce qui doit être vrai, sous « " + parent.titre + " »",
      "une phrase constatable, jamais une action", "Viser",
      (texte) => outil.jouer({ quoi: "viser", sert: parent.id, texte: texte })));
    return v;
  }

  // ---- les bandeaux et la légende ------------------------------------------
  // LA COULEUR NE SUFFIT PAS À DIRE À QUI C'EST : la rangée du haut n'avait
  // aucun titre, et l'on devait deviner que c'était eux. Un bandeau nomme la
  // bande — le rond du camp, VOUS ou EUX, le nom du camp, le compte.
  const ROND = { noir: "⚫", vert: "🟢", arbitre: "🟠", "1": "🔵", "2": "🔴", "3": "🟡", "4": "🟣", "5": "🟤" };
  const rond = (camp) => ROND[teinte(camp)] || "🔸";

  function bandeau(camp, nous, n) {
    const b = el("div", "pc-bandeau pc-teinte-" + teinte(camp));
    b.appendChild(el("span", "pc-bandeau-qui", rond(camp) + " " + (nous ? "VOUS" : "EUX")));
    b.appendChild(el("span", "pc-bandeau-camp", camp || ""));
    if (n != null) b.appendChild(el("span", "pc-bandeau-n", n + " pièce" + (n > 1 ? "s" : "")));
    return b;
  }

  // La légende, une ligne, toujours là : les signes et le code des formes. La
  // règle « s'apprend sans se lire » vaut pour le geste, pas pour le vocabulaire
  // — six signes, ça se rappelle.
  function legende() {
    const l = el("div", "pc-legende");
    [["🎯", "état à prouver"], ["🔒", "verrou"], ["🗝️", "clef"], ["❓", "question"],
     ["📦", "pièce"], ["💥", "frappe"]].forEach(([e, t]) => {
      const s = el("span", "pc-leg"); s.appendChild(el("b", "", e)); s.appendChild(document.createTextNode(" " + t)); l.appendChild(s);
    });
    const f = el("span", "pc-leg pc-leg-formes",
                 "plein = libre · pointillé = en route · liseré or = posée · barré = perdue");
    l.appendChild(f);
    return l;
  }

  // ---- le journal dans le fil, non persisté --------------------------------
  // Chaque ligne nouvelle du greffe est DITE dans le fil, en item hors fiction,
  // joué sur place par `Bus.rendre(…, true)` : rien n'entre dans flux.jsonl,
  // rien ne survit au rechargement. Le fil raconte, le jsonl fait foi.
  let logVu = null;
  const NOMS = { viser: "vise", bloquer: "pose un verrou sur", lever: "pose une clef pour", rearmer: "renforce",
                 justifier: "questionne", agir: "répond sur", demander: "demande", detruire: "frappe",
                 retourner: "achète", retirer: "reprend", passer: "passe", constater: "constate",
                 arbitrer: "arbitre", tour: "passe le jour", consigne: "consigne", sortir: "sort" };
  function loguer(vue) {
    const j = (vue && vue.journal) || [];
    if (!window.Bus || !Bus.rendre) return;
    // PREMIER REGARD : ce qui s'est joué depuis notre dernier coup va DANS LE
    // FIL, pas au-dessus du plateau. Le bloc « Ce qui s'est joué depuis votre
    // coup » y tenait une place fixe et répétait ce que le fil dit déjà de
    // chaque ligne neuve. La relecture (le greffe, ids rhabillés) est dite ici
    // une fois, en items hors fiction, sans rien écrire ; ensuite chaque ligne
    // nouvelle arrive par le même chemin, au fur et à mesure.
    if (logVu === null) {
      logVu = vue.dernier || 0;
      ((vue && vue.relecture) || []).forEach((e) => {
        try { Bus.rendre({ type: "coulisses", qui: "le greffe · tour " + e.tour,
                           texte: rond(e.camp) + " " + (e.camp || "") + " " + (e.dit || "") }, true); }
        catch (x) { /* le fil n'est pas là : le jsonl a tout */ }
      });
      return;
    }
    j.filter((l) => l.n > logVu).forEach((l) => {
      const qui = rond(l.camp) + " " + (l.camp || "");
      const quoi = (NOMS[l.coup] || l.coup) + (l.sujet ? " « " + l.sujet + " »" : "")
                 + (l.verdict ? " — " + l.verdict : "")
                 + (l.engage && l.engage.length ? " · avec " + l.engage.join(", ") : "")
                 + (l.gratuit ? " (gratuit)" : "");
      const texte = l.texte && l.texte !== l.sujet ? " — " + l.texte : "";
      try { Bus.rendre({ type: "coulisses", qui: "le greffe · tour " + l.tour,
                         texte: l.emoji + " " + qui + " " + quoi + texte }, true); }
      catch (e) { /* le fil n'est pas là : on ne perd rien, le jsonl a tout */ }
    });
    logVu = Math.max(logVu, vue.dernier || 0);
  }

  // ---- l'aire : des cases sans règle ---------------------------------------
  // Le plateau ne dit que ce qui est ENGAGÉ. Avant d'engager, on veut pouvoir
  // rapprocher trois pièces et les regarder ensemble — c'est ce que fait la
  // main d'un joueur au-dessus d'un vrai plateau, et rien à l'écran ne le
  // permettait. Ce rangement n'est pas un coup : il ne part nulle part.
  const cle = (vue) => "pc-aire:" + ((vue && vue.partie) || "") + ":" + ((vue && vue.camp) || "");

  function lire(vue) {
    try { return JSON.parse(localStorage.getItem(cle(vue)) || "{}"); } catch (e) { return {}; }
  }
  function ecrire(vue, rangement) {
    try { localStorage.setItem(cle(vue), JSON.stringify(rangement)); } catch (e) { /* privé */ }
  }

  function aire(vue, redessiner) {
    const rangement = lire(vue);
    const d = (vue && vue.deck) || {};
    const parId = {};
    [].concat(d.main || [], d.route || [], d.remet || [], (vue && vue.eux) || [])
      .forEach((c) => { parId[c.id] = c; });

    // une pièce qui n'est plus libre a quitté l'aire toute seule : elle est sur
    // le plateau, et l'y laisser en double serait un mensonge
    Object.keys(rangement).forEach((id) => {
      const piece = id[0] === "~" ? id.slice(1) : id;   // une note suit sa pièce
      if (!parId[piece]) delete rangement[id];
    });

    const g = el("div", "pc-aire");
    for (let i = 0; i < CASES; i++) {
      const v = receveuse("pc-case pc-case-libre",
        (t) => t && t.type === "piece",
        (t) => { rangement[t.id] = i; ecrire(vue, rangement); redessiner(); });
      const qui = Object.keys(rangement).filter((id) => rangement[id] === i && id[0] !== "~");
      qui.forEach((id) => { if (parId[id]) v.appendChild(preparee(vue, rangement, parId[id], redessiner)); });
      g.appendChild(v);
    }
    return g;
  }

  // ---- PRÉPARER UN COUP SANS CIBLE ----------------------------------------
  // Une pièce rangée dans l'aire porte une NOTE : ce qu'on compte en faire —
  // « le chapelain : embaumer ce soir, pour le rite ». C'est le brouillon d'un
  // verrou ou d'une clef avant qu'il y ait quoi que ce soit à viser. Elle vit
  // avec le rangement, dans le navigateur ; rien n'en part au greffe. Quand on
  // pose enfin la pièce, la note est proposée comme titre — on ne réécrit pas.
  const cleNote = (id) => "~" + id;

  function preparee(vue, rangement, c, redessiner) {
    const d = carte(c);
    const note = rangement[cleNote(c.id)];
    if (note) {
      d.classList.add("pc-preparee");
      d.appendChild(el("div", "pc-note", note));
      d.title = note;
    }
    const b = el("span", "pc-note-bt", "✎");
    b.title = note ? "Modifier ce qu'on prépare" : "Écrire ce qu'on prépare avec cette pièce";
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      bulle(d, "Ce que vous préparez avec " + (c.titre || c.id), note || "un verrou, une clef, un achat… en une phrase",
            "Garder", (t) => { if (t) rangement[cleNote(c.id)] = t; else delete rangement[cleNote(c.id)];
                              ecrire(vue, rangement); redessiner(); });
    });
    d.appendChild(b);
    return d;
  }

  const noteDe = (vue, id) => lire(vue)[cleNote(id)] || "";

  const range = (vue, id) => typeof lire(vue)[id] === "number";

  function vider(vue, redessiner) {
    ecrire(vue, {});
    redessiner();
  }

  return {
    armer: (o) => { outil = o; },
    geste: geste,
    carte: carte, cible: cible, prenable: prenable, aNous: (c) => aNous(c),
    engagees: engagees, ligne: ligne, aire: aire, range: range, vider: vider, desseins: desseins,
    demandeur: demandeur, bandeau: bandeau, legende: legende, loguer: loguer, teinte: teinte,
    CASES: CASES,
  };
})();
