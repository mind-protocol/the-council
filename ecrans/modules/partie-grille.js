// partie-grille.js — la position en cases : ce qu'on voit, et ce qu'on peut poser.
//
// Sorti de `partie.js`, qui tenait déjà le plateau entier : ce fichier ne
// connaît ni le serveur, ni les coups, ni la vue. On lui passe un OUTILLAGE
// (dessiner une carte, savoir ce qu'on tient, poser un coup) et il rend des
// cases. C'est ce qui permet de changer la forme du plateau sans toucher au
// greffe, et de le tester sans navigateur.
//
// Une seule chose vit ici : LA LIGNE — un objet du plateau, les pièces qu'il
// engage rangées dedans, et une case vide au bout quand on peut y lâcher
// quelque chose. Toute case de l'écran est donc une case du JEU : ce qu'on y
// pose part au greffe, et là où il n'y a pas de case, on ne pose pas.
//
// L'AIRE A ÉTÉ RETIRÉE (6.9). C'étaient douze cases sans règle sous le
// plateau, un brouillon qui vivait dans le navigateur et ne partait nulle
// part. Elle prenait la place du deck et brouillait la seule chose que les
// cases doivent dire — où l'on a le droit de poser.
window.PartieGrille = (function () {
  "use strict";

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
    // LE NUMÉRO D'ARRIVÉE, discret, en bas à droite (6.9 au soir) : une seule
    // suite pour toute la partie, le nom qu'on dit à voix haute sans lire le titre.
    if (c.numero) d.appendChild(el("span", "pc-num", c.numero));
    const t = el("div", "pc-texte");
    t.appendChild(el("div", "pc-titre", c.titre || ""));
    if (c.corps) t.appendChild(el("div", "pc-corps", c.corps));
    // LE PIED PASSE PAR LA MÊME RÈGLE QUE LE BANDEAU (`court`) : « libre » et
    // « posée » ne s'écrivent nulle part, ce qui attend est une horloge et un
    // nombre de jours. Sans cela on retirait le mot du bandeau pour le laisser
    // deux lignes plus bas, et l'écran disait deux choses différentes de la
    // même carte.
    const bas = court((c.pied || {}).droite, c.jours);
    if (c.pied && (c.pied.gauche || bas)) {
      const p = el("div", "pc-pied");
      p.appendChild(el("span", "pc-pied-g", c.pied.gauche || ""));
      p.appendChild(el("span", "pc-pied-d", bas));
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
      // L'ARBITRE CONSTATE D'UN CLIC sur un état : le motif, puis Vrai ou Faux.
      // Le seul coup de l'arbitre qui ait un geste — le reste est à la ligne.
      if (arbitre() && c.type === "cible") {
        return bulle(d, "Constater « " + (c.titre || c.id) + " »", "le motif, et sa source",
          "Vrai", (m) => outil.jouer({ quoi: "constater", sur: c.id, verdict: "vrai", texte: m }),
          "Faux", (m) => outil.jouer({ quoi: "constater", sur: c.id, verdict: "faux", texte: m }));
      }
      const deja = d.classList.contains("pc-epingle");
      const h = plateau();
      if (h) h.querySelectorAll(".pc-epingle").forEach((x) => x.classList.remove("pc-epingle"));
      if (!deja) { d.classList.add("pc-epingle"); placer(d, t); }
    });
    // LE STATUT SE LIT SUR LA CARTE, pas seulement au survol. Il n'etait ecrit
    // que dans le volet et dans le nom des rangees du deck : sur le plateau il
    // ne restait qu'un style de bordure a interpreter — pointillee pour ce qui
    // arrive, pale pour ce qui se remet. Le mot vient du greffe
    // (`pied.droite`), passe par `court` : ce qui attend devient une horloge et
    // un nombre de jours, ce qui est ordinaire — libre, posée, une clef qui
    // tient — ne s'ecrit pas du tout.
    // UNE QUESTION QU'ON PEUT RELEVER LE DIT DANS SON BANDEAU. La poignee ⚔️
    // ne parait qu'au survol, sur une carte de 65 px au fond d'une colonne qui
    // defile : personne ne la trouve. Le bandeau, lui, est toujours la.
    if (c.type === "question" && c.repondre) c.pied = { gauche: "", droite: "⚔️ à répondre" };
    const dit = (c.pied || {}).droite;
    const statut = dit && dit !== "✅ tient" ? court(dit, c.jours) : "";
    // UN COMPTE DE JOURS SE LIT DE LOIN. C'est le seul chiffre du plateau, il
    // décide de tout ce qui se prépare — quand la pièce arrive, depuis combien
    // de temps une question attend — et il était écrit en 9,5 px gris, du même
    // gris que « répondue » ou « faite ». Il a sa propre classe et son propre
    // corps ; le reste des statuts garde le sien.
    if (statut) d.appendChild(el("span", "pc-etat" + (statut[0] === "⏳" ? " pc-jours" : ""), statut));
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
    if (c.maillonnable) d.appendChild(maillonneur(c));
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
    const st = court((c.pied || {}).droite, c.jours);
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

  // LE BANDEAU NE DIT QUE CE QUI N'EST PAS L'ORDINAIRE. « libre » et « posée »
  // sont les deux états normaux d'une pièce, et la carte les dit déjà sans un
  // mot : pleine et prenable pour l'une, rangée sous ce qui l'engage pour
  // l'autre. Un bandeau sur chaque carte du plateau couvrait le signe pour
  // n'apprendre rien — c'est le fond du bruit, pas de l'information.
  const MUET = { "libre": 1, "posée": 1, "posee": 1 };
  // CE QUI ATTEND SE COMPTE EN JOURS, DONC EN HORLOGE. « dans 4 j » tombait à
  // la ligne sur 65 px ; ⏳4 se lit d'un coup. Le nombre est celui du greffe :
  // les jours qui restent pour ce qui arrive, les jours DÉJÀ PASSÉS pour ce qui
  // attend un arbitrage ou une réponse (`jours`, posé par partie_cartes) — une
  // question qui traîne depuis six jours se voyait nulle part. La phrase
  // entière reste dans le volet, à un survol.
  const court = (m, jours) => {
    if (!m || MUET[m]) return "";
    const j = /dans (\d+) j/.exec(m);
    if (j) return "⏳" + j[1];
    if (/attente|attend l'arbitre/.test(m)) return "⏳" + (jours || "");
    return String(m).replace("se remet · ", "remet ");
  };

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

  // LE MAILLON SANS QU'ON LE DEMANDE (6.9). Même poignée, sur toute clef, garde
  // ou frappe à nous encore en jeu (`maillonnable`, partie_marques). Ce
  // coup-là COMPTE pour le jour et donne une carte à l'adversaire, à
  // l'inverse de la réponse à un ❓ : la bulle le dit.
  function maillonneur(c) {
    const b = el("span", "pc-rep pc-rep-libre", "⚔️");
    b.title = "Écrire le maillon de « " + (c.titre || "") + " » — compte pour le jour";
    b.draggable = false;
    b.addEventListener("mousedown", (e) => e.stopPropagation());
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      if (epuise()) return outil.dire(MOT_EPUISE);
      bulle(b, "Le maillon : qui, avec quoi, quel jour", "qui, avec quoi, quel jour", "Écrire",
            (texte) => outil.jouer({ quoi: "maillon", sur: c.id, texte: texte }),
            null, null, { note: "Compte pour votre coup du jour. L'adversaire lira la chaîne.", sansChamp: true });
    });
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
    // TOUT EN HAUT DE L'ECRAN, TOUJOURS (6.9). Le volet se posait au-dessus
    // de la carte, ou dessous faute de place : il couvrait tantot la rangee
    // du dessus, tantot celle du dessous, et l'oeil ne savait jamais ou lire.
    // Il a maintenant une place fixe, le haut de la fenetre, comme un bandeau
    // de lecture : on survole en bas, on lit en haut, et rien de ce qu'on
    // compare n'est cache. Seule exception : quand la carte elle-meme est
    // dans la bande du haut, le volet se decale a cote d'elle plutot que
    // dessus, pour qu'on voie encore ce qu'on lit.
    let left = r.left;
    if (r.top < 6 + h + 4) left = (r.left - w - 8 >= 6) ? r.left - w - 8 : r.right + 8;
    t.style.left = Math.max(6, Math.min(left, W - w - 6)) + "px";
    t.style.top = "6px";
    t.style.maxHeight = (H - 12) + "px";
  }

  // ---- le geste : on prend une carte, on la pose sur une autre -------------
  const aNous = (c) => c.camp === (outil.vue() && outil.vue().camp);
  // UN COUP PAR CAMP ET PAR JOUR — et l'écran ne le laisse plus casser. Le
  // greffe reste gradué : il écrit le second coup et le SIGNALE, parce qu'un
  // MJ qui rattrape une ligne à la main doit pouvoir le faire. Mais un joueur
  // devant le plateau n'a aucune raison de pouvoir jouer deux fois, et il le
  // faisait — trois fois dans le même tour sur « vingt jours », payés après
  // coup par trois jours de calendrier que personne n'avait vus venir.
  // Ce qui reste ouvert, c'est ce qui ne compte pas : demander une pièce,
  // questionner une carte d'en face, écrire le maillon qui répond. Le compte
  // vient du greffe (`coups_du_jour`, posé par `partie_cartes`) et jamais d'ici.
  const epuise = () => {
    const v = outil.vue();
    // la limite vient du greffe aussi (`coups_max`) : un par camp, ou deux
    // quand un humain et une IA se partagent le camp
    return !!v && v.camp !== "arbitre" && (((v.coups_du_jour || {})[v.camp]) || 0) >= (v.coups_max || 1);
  };
  const MOT_EPUISE = "Votre coup du jour est joué : un coup par camp et par jour. "
                   + "Restent les gestes qui ne comptent pas — demander une pièce, "
                   + "questionner une carte d'en face, écrire un maillon.";
  const arbitre = () => !!outil.vue() && outil.vue().camp === "arbitre";
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
  // LEUR PIÈCE SE TIRE À SOI : lâchée sur une de MES pièces libres, c'est un
  // achat si c'est la bourse, une frappe sinon — le greffier décide
  // (partie_gestes, branche « sur une ressource »). Ma pièce libre est donc
  // une cible, mais seulement pour une pièce d'en face : `accepte` le vérifie.
  const interdit = (coup) => (((outil.vue() || {}).coups_interdits) || []).indexOf(coup) >= 0;
  const cible = (c) => (c.type === "verrou") || (c.type === "frappe" && !aNous(c))
                    || (c.type === "clef" && aNous(c) && !interdit("rearmer"))   // une partie sans renfort n'allume pas nos clefs
                    || (c.type === "cible" && !(aNous(c) && c.apparence === "vrai"))
                    || (c.type === "piece" && aNous(c) && c.apparence === "libre");
  // ce que la cible accepte selon ce qu'on tient : une pièce à nous partout
  // sauf sur nos pièces ; une pièce d'en face SEULEMENT sur nos pièces
  const accepte = (c, t) => !!t && t.type === "piece"
                    && (c.type === "piece" ? !aNous(t) : aNous(t));
  // TOUTE PIÈCE À NOUS SE PREND, libre ou non. Une pièce engagée qu'on soulève
  // ne trouvera aucune case allumée, et si on la lâche quand même, c'est le
  // greffe qui refuse — avec sa phrase, qui apprend la règle. Éteindre la
  // carte, à l'inverse, ne dit jamais pourquoi.
  // `epuise` passe AVANT tout le reste : une carte qu'on ne peut plus jouer ne
  // se soulève pas, et le marquage `pc-interdit` de `jouable` la grise au repos.
  const prenable = (c) => !epuise()
                       && ((c.type === "piece" && aNous(c))
                       || ((c.type === "clef" || c.type === "verrou") && aNous(c))
                       // mon état au deck (→ sortir), ma pièce perdue (→ reconstruire) : vers la main
                       || (c.type === "cible" && aNous(c) && c.apparence !== "vrai")
                       // la leur, libre : on peut la tirer à soi (achat, frappe)
                       || (c.type === "piece" && !aNous(c) && c.apparence === "libre"));

  // CE QUI SE JOUE MAINTENANT — la règle du GREFFE, et non celle du glissé.
  // Les deux ne se recouvrent pas, et c'est voulu : toute pièce à nous se
  // soulève (`prenable`) pour que le refus vienne du greffe avec sa phrase,
  // mais une pièce gelée, engagée ailleurs, détruite ou qui attend encore son
  // arbitrage ne peut RIEN faire ce tour-ci. C'est cette liste-là qu'on
  // marque, parce que c'est la question qu'on se pose devant le plateau
  // immobile : qu'ai-je le droit de prendre ?
  // Une pièce EN ROUTE se joue : le greffe accepte qu'on l'engage d'avance, et
  // la clef est simplement « prête au tour N » (règle 4.1.3). L'exclure aurait
  // été plus faux que de ne rien marquer.
  function jouable(c) {
    if (c.repondre || c.questionnable) return true;   // gratuits : jamais fermés
    if (epuise()) return false;
    if (c.type === "piece") {
      if (!aNous(c)) return c.apparence === "libre";   // on ne tire à soi qu'une pièce libre
      if (c.apparence === "libre") return true;
      return c.apparence === "route" && !/attend l'arbitre/.test((c.pied || {}).droite || "");
    }
    return cible(c) || prenable(c);
  }

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
    if (!accepte(sur, piece)) return null;   // la leur ne va que sur les miennes, et réciproquement
    if (sur.type === "piece")
      return /💰/.test(sur.signe || sur.emoji || "") ? { signe: "🔄", mot: "achat" }
                                                    : { signe: "💥🔄", mot: "frappe ou retour" };
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
    if (aNous(tenue) && tenue.visee) {
      // UNE PIÈCE VISÉE RENTRE (6.9) : la frappe tombe, la pièce se remet — règle 23
      const deck = h.querySelector(".pc-deck");
      if (deck) marquer(deck, { signe: "\u21a9", mot: "rentrer" });
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
    // CE QU'ON NE PEUT PAS JOUER LE DIT AU REPOS, et pas seulement pendant un
    // glissé. La règle « ce qui n'est pas jouable ne s'allume pas » ne servait
    // qu'une fois la carte en main : devant le plateau immobile, une pièce en
    // route, gelée ou déjà engagée avait exactement l'air d'une pièce libre, et
    // l'on ne l'apprenait qu'en essayant. Le bandeau dit POURQUOI (⏳4, remet
    // 4 j, détruite) ; ce trait-ci dit QUE — bord gris pointillé, couleur
    // éteinte, curseur barré.
    // UNE QUESTION N'EST JAMAIS « INTERDITE » (6.9) : elle ne se prend ni ne se
    // lâche, mais elle est active — c'est elle qui suspend. La griser et la
    // tireter la faisait paraître suspendue à son tour. Même chose pour un
    // maillon fait : il est fait, il n'est pas empêché.
    if (!jouable(c) && c.type !== "question" && c.type !== "action") d.classList.add("pc-interdit");
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
        if (!accepte(c, t)) return;
        e.preventDefault();
        d.classList.add("pc-survol");
      });
      d.addEventListener("dragleave", () => d.classList.remove("pc-survol"));
      d.addEventListener("drop", (e) => {
        e.preventDefault();
        d.classList.remove("pc-survol");
        const t = outil.tenue();
        if (!accepte(c, t)) return;
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
              || sur.type === "cible" || sur.type === "piece";
    if (!neuf) return outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id });
    if (sur.type === "piece") {
      // UNE BOURSE ACHÈTE, et c'est le seul raccourci qui reste (6.9). Tout le
      // reste demande le verbe : on retourne aussi un homme avec une promesse,
      // un otage, une lettre — deux verbes dans la bulle, comme Vrai et Faux.
      const achat = /💰/.test(sur.signe || sur.emoji || "");
      if (achat)
        return bulle(ancre, "Acheter " + piece.titre + " avec " + sur.titre,
                     "à qui l'argent est remis, quand, pour quoi", "Acheter",
                     (texte) => outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id, texte: texte, verbe: "retourner" }));
      return bulle(ancre, piece.titre + " avec " + sur.titre,
                   "frapper : de nuit, par où — retourner : par quelle promesse, remise par qui",
                   "Retourner",
                   (texte) => outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id, texte: texte, verbe: "retourner" }),
                   "Frapper",
                   (texte) => outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id, texte: texte, verbe: "detruire" }));
    }
    const contre = sur.type === "cible" && aNous(sur) ? " pour « " : " contre « ";
    bulle(ancre, "Et " + piece.titre + " y fait quoi ?", piece.titre + contre + sur.titre + " »",
          "Poser", (texte) => outil.jouer({ quoi: "poser", piece: piece.id, sur: sur.id, texte: texte }));
  }

  const dejaUneClef = (bid) => ((outil.vue() || {}).fronts || []).some(
    (f) => f.id === bid && (f.pile || []).some((o) => o.type === "clef" && aNous(o)));

  // La bulle est posée sur le CORPS, en repère fixe, et non dans la carte : la
  // colonne des fronts défile en `overflow:auto`, et une bulle qui y vivrait
  // serait coupée au bord dès que le front est près de la marge.
  // `extra` (6.9) : un petit champ à droite de la phrase — « au jour », « combien ».
  // Facultatif, vide par défaut ; `valider` reçoit alors (texte, extra).
  function bulle(ancre, titre, placeholder, verbe, valider, verbe2, valider2, extra) {
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
    let petit = null;
    if (extra && extra.sansChamp) {
      b.appendChild(champ);
    } else if (extra) {
      // LA PHRASE A SA LIGNE, LE PETIT CHAMP LA SIENNE (6.9). Sur une seule
      // ligne, « combien » ecrasait la phrase a vingt caracteres et le nombre
      // a deux : on ne lisait ni l'un ni l'autre.
      b.appendChild(champ);
      const rang = el("div", "pc-bulle-rang");
      rang.appendChild(el("span", "pc-bulle-lab", extra.label));
      petit = document.createElement("input");
      petit.type = "number"; petit.min = "0"; petit.className = "pc-bulle-petit";
      petit.placeholder = extra.placeholder || "";
      rang.appendChild(petit);
      if (extra.aide) rang.appendChild(el("span", "pc-bulle-aide", extra.aide));
      b.appendChild(rang);
    } else {
      b.appendChild(champ);
    }
    if (extra && extra.note) b.appendChild(el("div", "pc-bulle-note", extra.note));
    const pied = el("div", "pc-bulle-p");
    const ok = el("button", "pc-bt", verbe);
    const non = el("button", "pc-bt pc-bt-nu", "Laisser");
    pied.appendChild(non);
    if (verbe2) {   // deux verbes : constater VRAI ou FAUX, du même motif
      const ok2 = el("button", "pc-bt pc-bt-second", verbe2);
      ok2.addEventListener("click", () => { const t = champ.value.trim(); b.remove(); valider2(t, petit && petit.value); });
      pied.appendChild(ok2);
    }
    pied.appendChild(ok);
    b.appendChild(pied);
    document.body.appendChild(b);
    champ.focus();
    const partir = () => b.remove();
    const aller = () => { const t = champ.value.trim(); partir(); valider(t, petit && petit.value); };
    ok.addEventListener("click", aller);
    non.addEventListener("click", partir);
    [champ, petit].filter(Boolean).forEach((x) => x.addEventListener("keydown", (e) => {
      if (e.key === "Enter") aller();
      if (e.key === "Escape") partir();
    }));
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
  function ligne(o, eng, cls, piecesAvant) {
    const l = el("div", "pc-ligne" + (cls ? " " + cls : ""));
    // LES PIÈCES AVANT LA CARTE quand on le demande (`piecesAvant`) : sur la
    // rangée d'un verrou posé sur une clef, la pièce PRODUIT le verrou — il en
    // est la conséquence et la fin de la chaîne —, donc elle se lit avant lui.
    // Partout ailleurs, l'objet d'abord, ses pièces rangées à sa suite.
    if (!piecesAvant) l.appendChild(carte(o));
    (eng[o.id] || []).forEach((p) => {
      const cp = carte(p);
      cp.classList.add("pc-mise");
      l.appendChild(cp);
    });
    if (piecesAvant) l.appendChild(carte(o));
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
    // FACE À FACE : ma racine d'abord (à gauche, tournée vers l'axe), la sienne
    // ensuite (à droite). Les deux se touchent au milieu ; ce qui pend de
    // chacune s'étale vers l'extérieur. C'est la disposition d'une partie.
    const racines = (parParent[""] || []).slice().sort((a, b) => (aNous(b) ? 1 : 0) - (aNous(a) ? 1 : 0));
    racines.forEach((r) => {
      const rangee = el("div", "pc-dessein pc-camp-" + (r.camp || "") + (aNous(r) ? " pc-dessein-nous" : " pc-dessein-eux"));
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

  // ---- LA CARTE EN LIGNES (6.9, à la demande du joueur) --------------------
  // « Il n'y a pas moyen de savoir où les verrous et les clefs s'appliquent. »
  // Les états vivaient dans une rangée, les verrous dans des colonnes à part,
  // et rien ne reliait les uns aux autres. Ici, UNE LIGNE PAR ÉTAT, l'arbre
  // par retrait (un enfant sous son parent, décalé d'un cran), et tout ce qui
  // s'applique à l'état s'écrit À SA DROITE, dans l'ordre de la chaîne :
  //
  //     E                                   (un état, rien dessus)
  //       e   r r c   →   R V               (son enfant ; les pièces, puis la
  //                                          clef qu'elles produisent ; puis la
  //                                          pièce, puis le verrou)
  //       e   →   R V   →   r c             (un verrou posé sur l'état, puis la
  //                                          pièce et la clef qui le lève)
  //
  // TOUJOURS LA PIÈCE AVANT CE QU'ELLE PRODUIT — clef comme verrou : la pièce
  // est la cause, la carte en est la conséquence. Chaque maillon garde
  // sa case vide s'il en a une : on pose une pièce sur l'état (verrou ou
  // clef), sur un verrou d'en face (clef), sur une clef à nous (renfort). Les
  // frappes, posées sur des pièces et non sur des états, gardent leur front.
  function lignes(vue) {
    const cibles = (vue && vue.cibles) || [];
    const fronts = ((vue && vue.fronts) || []).filter((f) => f.tete && f.tete.type === "verrou");
    const eng = engagees(vue);
    const parParent = {};
    cibles.forEach((c) => { (parParent[c.sert || ""] = parParent[c.sert || ""] || []).push(c); });
    const surs = {};
    fronts.forEach((f) => { (surs[f.sur] = surs[f.sur] || []).push(f); });
    const d = el("div", "pc-lignes");
    const fleche = () => el("span", "pc-fleche", "→");
    const petite = (q) => { const c = carte(q); c.classList.add("pc-sur"); return c; };
    const vus = new Set();
    function chaineClef(r, k) {
      if (vus.has(k.id)) return;
      vus.add(k.id);
      r.appendChild(ligne(k, eng, null, true));   // la pièce d'abord, la clef qu'elle produit ensuite
      (k.sous || []).filter((q) => q.type === "question").forEach((q) => r.appendChild(petite(q)));
      (surs[k.id] || []).forEach((f) => chaineVerrou(r, f));
    }
    function chaineVerrou(r, f) {
      if (vus.has(f.id)) return;
      vus.add(f.id);
      r.appendChild(fleche());
      r.appendChild(ligne(f.tete, eng, null, true));
      (f.pile || []).forEach((o) => {
        if (o.type === "question") r.appendChild(petite(o));
        else if (o.type === "clef") { r.appendChild(fleche()); chaineClef(r, o); }
      });
    }
    function rangeeEtat(c, prof, sortie) {
      const r = el("div", "pc-lg pc-lg-" + (aNous(c) ? "nous" : "eux") + " pc-camp-" + (c.camp || "")
                        + (prof ? " pc-lg-fils" : " pc-lg-racine"));
      r.style.paddingLeft = (prof * 30) + "px";
      r.style.setProperty("--pc-retrait", (prof * 30) + "px");   // le tiret qui relie l'enfant au parent
      r.appendChild(ligne(c, eng));
      // LA CHAÎNE SE REPLIE (6.9, à la demande du joueur) : l'état reste à
      // gauche, et tout ce qui s'applique à lui vit dans son propre conteneur,
      // qui passe au rang du dessous quand la largeur manque. Une clef et ses
      // pièces restent ensemble ; c'est entre deux maillons que ça se replie.
      const ch = el("div", "pc-lg-chaine");
      r.appendChild(ch);
      (c.sous || []).forEach((o) => {
        if (o.type === "question") ch.appendChild(petite(o));
        else if (o.type === "clef") { ch.appendChild(fleche()); chaineClef(ch, o); }
      });
      (surs[c.id] || []).forEach((f) => chaineVerrou(ch, f));
      // la case 🎯 vide au bout de notre racine : l'état suivant s'écrit là
      if (aNous(c) && !c.sert) ch.appendChild(viseur(c));
      sortie.push(r);
      (parParent[c.id] || []).forEach((f) => rangeeEtat(f, prof + 1, sortie));
    }
    // CHAQUE CAMP REGARDE VERS CHEZ LUI (6.9, à la demande du joueur). Leur
    // arbre en haut, racine contre la bande « EUX », ses états en dessous ; le
    // nôtre en bas, racine contre notre main, ses états AU-DESSUS d'elle — les
    // lignes de notre arbre sont rendues à l'envers. Entre les deux, la table.
    const racines = (parParent[""] || []).slice().sort((a, b) => (aNous(a) ? 1 : 0) - (aNous(b) ? 1 : 0));
    racines.forEach((rac, i) => {
      if (i) d.appendChild(el("div", "pc-lg-sep"));
      const lignesDe = [];
      rangeeEtat(rac, 0, lignesDe);
      if (aNous(rac)) lignesDe.reverse();
      lignesDe.forEach((r) => d.appendChild(r));
    });
    // PAS DE RACINE À NOUS : la case 🎯 seule, au rang racine (6.9). Sans elle
    // une partie ne s'ouvrait qu'à la ligne — la grille était vide et rien ne
    // s'y posait.
    if (!racines.some(aNous) && (outil.vue() || {}).camp !== "arbitre") {
      if (racines.length) d.appendChild(el("div", "pc-lg-sep"));
      const r = el("div", "pc-lg pc-lg-nous pc-lg-racine");
      r.appendChild(viseur(null));
      r.appendChild(el("span", "pc-lg-mot", "votre racine — rien n'est encore visé"));
      d.appendChild(r);
    }
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
      (texte, n) => outil.jouer({ quoi: "demander", texte: texte, nombre: n || undefined }),
      null, null, { label: "combien", placeholder: "1", aide: "vide = une seule" }));
    return v;
  }

  // SANS PARENT (6.9) : la case de la RACINE, quand le camp n'en a pas encore.
  // C'est par elle qu'une partie s'ouvre depuis l'écran. Et « au jour N » à
  // droite : l'état daté, qui tient sa place et n'entre au deck qu'à sa date.
  function viseur(parent) {
    const v = el("div", "pc-case pc-viseur" + (parent ? "" : " pc-viseur-racine"));
    v.title = parent ? "Écrire un état qui sert « " + parent.titre + " »" : "Écrire votre racine : ce qui doit être vrai à la fin";
    v.appendChild(el("span", "pc-type", "🎯"));
    v.addEventListener("click", () => epuise() ? outil.dire(MOT_EPUISE) : bulle(v,
      parent ? "Ce qui doit être vrai, sous « " + parent.titre + " »" : "Votre racine : ce qui doit être vrai à la fin",
      "une phrase constatable, jamais une action", "Viser",
      (texte, jour) => outil.jouer({ quoi: "viser", sert: parent ? parent.id : undefined, texte: texte, jour: jour || undefined }),
      null, null, { label: "au jour", placeholder: "", aide: "vide = tout de suite" }));
    return v;
  }

  // ---- les bandeaux et la légende ------------------------------------------
  // LA COULEUR NE SUFFIT PAS À DIRE À QUI C'EST : la rangée du haut n'avait
  // aucun titre, et l'on devait deviner que c'était eux. Un bandeau nomme la
  // bande — le rond du camp, VOUS ou EUX, le nom du camp, le compte.
  const ROND = { noir: "⚫", vert: "🟢", arbitre: "🟠", "1": "🔵", "2": "🔴", "3": "🟡", "4": "🟣", "5": "🟤" };
  const rond = (camp) => ROND[teinte(camp)] || "🔸";

  // LE BANDEAU DIT LE CAMP, PAS « EUX » (6.9). À quatre camps, « EUX » ne
  // désignait personne ; le rond et le nom suffisent, et la position (en haut,
  // en bas) dit le reste. Plus de compte de pièces : il prenait la place et ne
  // servait à rien — on les voit. Un mot dans le coin (`coin`), en petit, là où
  // le compte était : « main », « votre main ».
  function bandeau(camp, nous, coin) {
    const b = el("div", "pc-bandeau pc-teinte-" + teinte(camp));
    b.appendChild(el("span", "pc-bandeau-qui", rond(camp) + " " + (camp || "")));
    if (coin) b.appendChild(el("span", "pc-bandeau-coin", coin));
    return b;
  }

  // La légende, une ligne, toujours là : les signes et le code des formes. La
  // règle « s'apprend sans se lire » vaut pour le geste, pas pour le vocabulaire
  // — six signes, ça se rappelle.
  function legende() {
    const l = el("div", "pc-legende");
    // LA LÉGENDE PORTE LA COULEUR DE CHAQUE TYPE, depuis que le fond d'une carte
    // dit le type et non le camp. Sans elle, la palette s'apprend en devinant ;
    // avec elle, on la lit une fois et l'on n'y revient plus. Chaque entrée
    // prend la classe de sa famille : la couleur vient de la feuille, jamais
    // d'une seconde table ici — deux tables divergeraient au premier ajout.
    [["🎯", "état à prouver", "cible"], ["🔒", "verrou", "verrou"], ["🗝️", "clef", "clef"],
     ["❓", "question", "question"], ["📦", "pièce", "piece"], ["💥", "frappe", "frappe"],
     ["⚔️", "action faite", "action"]].forEach(([e, t, fam]) => {
      const s = el("span", "pc-leg pc-leg-" + fam);
      s.appendChild(el("b", "", e)); s.appendChild(document.createTextNode(" " + t)); l.appendChild(s);
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

  return {
    armer: (o) => { outil = o; },
    geste: geste, epuise: epuise, motEpuise: () => MOT_EPUISE,
    carte: carte, cible: cible, prenable: prenable, aNous: (c) => aNous(c),
    engagees: engagees, ligne: ligne, desseins: desseins, lignes: lignes,
    demandeur: demandeur, bandeau: bandeau, legende: legende, loguer: loguer, teinte: teinte, rond: rond,
  };
})();
