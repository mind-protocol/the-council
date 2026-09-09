// partie.js — « Le conseil », une échelle du décor : la partie en cartes.
//
// La table peinte dit OÙ porte la guerre, l'échiquier dit COMMENT le plan se
// tient ; le conseil de guerre dit CONTRE QUI, et avec quoi, à ce jour. C'est
// la partie de mj-partie.md vue du siège qui la joue. LES MOTS SONT CEUX DE
// L'ÉCHIQUIER (docs/echiquier.md), donc ceux des cahiers d'affaire : on ne
// forge pas ici un second lexique sur les mêmes emojis, comme on l'a fait un
// temps — 🗝️ voulait alors dire « clef » sur un onglet et « ordre » sur
// l'autre, et « ordre » ne désignait rien. Ce qui reste dehors, c'est la
// tuyauterie du greffier : gel, deck, tour. Sept cartes, et leur signe :
//
//   🎯 l'état cible  ce qu'on veut voir vrai ; la colonne de gauche
//   🔒 le verrou     ce que l'autre camp tient contre nous ; en tête d'un front
//   🗝️ la clef       ce qu'on a posé contre un verrou ; sous lui, dans la pile
//   ❓ la question   ce qu'un conseiller demande avant d'exécuter ; sur la clef
//   ⚔️ l'action      ce qui a été fait, par qui
//   📦 la pièce      ce qu'on engage — 🐉 ⛵ ⚔️ 💰 👤 🏰 en sous-signe
//   💥 la frappe     ce qui vient sur une de nos pièces
//
// TOUT EST UNE CARTE, et l'état se lit à sa forme, jamais à un chiffre isolé :
// nette = libre · sous un front = posée · pointillée « dans 4 j » = en route ·
// grisée = se remet · barrée = détruite. Le deck est sous les yeux en
// permanence : c'est de là que tout part.
//
// v1 : ON JOUE. Un seul geste, toujours le même — ON PREND UNE CARTE ET ON LA
// POSE SUR UNE AUTRE. Ce que ça veut dire, c'est la carte du dessous qui le
// dit : une pièce sur un verrou pose une clef, sur une de nos clefs elle la
// renforce, sur une frappe elle protège. Une carte à nous rendue au deck est
// reprise, et ses pièces se remettent. L'écran ne connaît AUCUN nom de coup :
// il envoie « j'ai posé ceci sur cela » et le greffier traduit
// (scripts/noyau/partie_gestes.py).
//
// Ce qui n'est pas jouable ne s'allume pas quand on tient une carte : c'est
// comme ça que la règle s'apprend, sans avoir à la lire. Un refus n'est jamais
// un silence — il revient en une phrase, sous la barre.
//
// PAS DE BROUILLARD SUR CE PLATEAU (décidé le 3.9). Il reste entier dans la
// CHRONIQUE — ce que le joueur apprend d'un homme essoufflé, d'une rumeur
// fausse, d'un chiffre arrondi. Mais le plateau n'est pas dans la fiction :
// c'est l'outil du joueur, et aux échecs on voit les pièces d'en face. On
// servait naguère l'ennemi seulement par ce qu'il avait posé contre nous, et
// l'adversaire jouait alors des coups que personne ne voyait jamais.
//
// CE QUI A CHANGÉ porte une marque, et elle est EXACTE : le jsonl est
// append-only, donc le dernier numéro de ligne vu suffit à dire ce qui est
// neuf. La marque ne part pas au bout de trois secondes — elle tient jusqu'à
// votre prochain coup, donc elle survit à deux jours d'absence.
//
// Rien ici ne touche etat/ : le seul fichier qui s'allonge est le jsonl de la
// partie. Ce qu'un coup change dans le monde reste au MJ.
"use strict";
window.PartieVue = (() => {
  let vue = null;
  let charge = false;
  let dernier = "";
  let tenue = null;      // la carte qu'on a en main pendant le glissé
  let mot = "";          // ce que le greffier vient de dire, ou son refus
  let envoi = false;     // un coup à nous est en route vers le greffier
  let vuDernier = null;  // le n de la dernière ligne au dernier regard
  let leurCoup = 0;      // combien de lignes ils ont écrites depuis
  let animerDepuis = null; // le n d'avant leur coup : ce qui est au-dessus s'anime au prochain dessin
  let motMauvais = false;

  const hote = () => document.getElementById("partie");
  const el = (tag, cls, texte) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texte != null) e.textContent = texte;
    return e;
  };

  // LA CARTE, LE GESTE ET LA GRILLE VIVENT DANS `partie-grille.js`. Ils y sont
  // ensemble parce que c'est une seule chose : ce qu'on voit d'une carte et ce
  // qu'on peut en faire. Ici restent le serveur, la vue et le plateau.
  // Le module joue par `jouer` et porte la bulle : ce qu'on demande au joueur
  // avant d'écrire (un titre de clef, la phrase d'un état) est un geste, pas
  // du transport.
  PartieGrille.armer({ vue: () => vue, tenue: (c) => (c === undefined ? tenue : (tenue = c)),
                       jouer: (g) => jouer(g),
                       // DIRE SANS JOUER : une phrase sous la barre, sans ligne au
                       // livre et sans minute. C'est par la que l'ecran explique un
                       // geste impossible au lieu d'avaler le clic en silence.
                       dire: (t) => { mot = t; motMauvais = false; dernier = ""; dessiner(); } });
  const carte = (c) => PartieGrille.carte(c);
  const cible = (c) => PartieGrille.cible(c);
  const prenable = (c) => PartieGrille.prenable(c);


  // ---- CE QUI EST JOUABLE, ÉCRIT EN TOUTES LETTRES ------------------------
  // Le geste est un glissé, et un glissé ne s'annonce pas : les cibles ne
  // s'allument QUE pendant qu'on tient déjà une carte. Il fallait donc savoir
  // qu'un coup existe pour découvrir qu'il en existe. Pire, sur une position
  // sans front — le cas le plus fréquent — il n'y a AUCUNE cible, et le joueur
  // essayait indéfiniment un geste qui ne pouvait pas aboutir. Cette ligne dit
  // le compte, avec les mêmes prédicats que `prenable` et `cible` : elle ne
  // peut donc pas mentir sur ce que le greffe acceptera.
  function jouable() {
    const dans = [];
    (vue.fronts || []).forEach((f) => {
      dans.push(f.tete);
      (f.pile || []).forEach((x) => dans.push(x));
    });
    (vue.cibles || []).forEach((c) => dans.push(c));   // un état se tient, ou se sert
    const mains = ((vue.deck || {}).main || []).filter(prenable);
    const buts = dans.filter(cible);
    const reprises = dans.filter(prenable);
    if (vue.trait !== vue.camp) return "Le trait est à eux : leur coup s'écrit à la ligne, par le mestre.";
    if (PartieGrille.epuise()) return PartieGrille.motEpuise();
    if (!mains.length && !reprises.length) return "Aucune pièce libre en main : rien à poser d'ici.";
    if (!buts.length)
      return mains.length + " pièce" + (mains.length > 1 ? "s" : "") + " libre" + (mains.length > 1 ? "s" : "")
           + ", et rien à atteindre. Demander et détruire s'écrivent à la ligne, par le mestre.";
    return "Glissez une de vos " + mains.length + " pièces libres sur l'une des " + buts.length
         + " cartes qui s'allumeront : sur un état d'en face, c'est un verrou ; sur un des vôtres, une clef. "
         + "La case 🎯 vide sous vos états reçoit un état neuf."
         + (reprises.length ? " Ramenez une des vôtres dans la main pour la reprendre." : "");
  }

  // ---- L'ÉCRAN SUIT L'ADRESSE ---------------------------------------------
  // `?id=<partie>` et `?camp=<camp>` sont lus par le serveur, mais sur l'URL de
  // SA requête — et la page les portait sans jamais les transmettre. Deux
  // joueurs sur la même machine tombaient donc tous les deux sur le camp de
  // `_courante.json`, chacun regardant la main de l'autre, et « ce qu'il vient
  // de jouer » n'avait aucun sens puisque c'était le même siège. On repasse ces
  // deux clefs, et rien d'autre : le reste de l'adresse ne regarde pas le
  // greffe.
  function adresse(chemin) {
    const q = new URLSearchParams(location.search);
    const p = new URLSearchParams();
    ["id", "camp"].forEach((k) => { if (q.get(k)) p.set(k, q.get(k)); });
    const s = p.toString();
    return s ? chemin + "?" + s : chemin;
  }

  // ---- envoyer le geste ---------------------------------------------------
  // LA PORTE DURE DU « UN COUP PAR JOUR ». Les cartes ne se soulèvent déjà plus
  // (`PartieGrille.epuise`), mais le blocage se tient AUSSI ici, sur le seul
  // chemin par lequel un coup part vers le greffe : c'est la dernière porte, et
  // aucun geste — bulle laissée ouverte avant le premier coup, case cliquée,
  // raccourci à venir — ne passe à côté. Ce qui ne compte pas passe : demander,
  // justifier, le maillon qui répond. Le compte est celui du greffe.
  const COMPTES = ["poser", "viser", "reprendre", "passer"];
  function jouer(geste) {
    if (COMPTES.indexOf((geste || {}).quoi) >= 0 && PartieGrille.epuise()) {
      mot = PartieGrille.motEpuise(); motMauvais = true; dernier = ""; dessiner();
      return;
    }
    mot = "le mestre inscrit le coup…"; motMauvais = false; envoi = true; dernier = ""; dessiner();
    fetch(adresse("/partie/geste"), { method: "POST", headers: { "Content-Type": "application/json" },
                             body: JSON.stringify(geste) })
      .then((r) => r.json())
      .then((r) => {
        mot = r.ok ? ((r.dit || "") + ((r.avertissements || []).length ? " — " + r.avertissements[0] : ""))
                   : (r.refus || ["refusé"]).join(" · ");
        motMauvais = !r.ok;
        if (r.vue) { vue = r.vue; if (r.vue.dernier != null) vuDernier = r.vue.dernier; PartieGrille.loguer(r.vue); }
        if (r.ok) vuLeurs();
        envoi = false; dernier = ""; dessiner();
      })
      .catch(() => { mot = "le mestre n'a pas répondu"; motMauvais = true; envoi = false; dernier = ""; dessiner(); });
  }

  // PAS DE BOUTON POUR FAIRE PASSER LE JOUR, et c'est délibéré. Le temps ne
  // passe pas parce qu'on a cliqué : il passe parce que le monde tourne, et le
  // monde est au MJ. Un tour de partie vaut deux jours de `monde.date` ; c'est
  // lui qui écrit la ligne `tour` quand il avance l'horloge (par
  // `partie.py --tour`, ou `POST /partie/jour` qui reste ouvert pour lui).
  // Un bouton ici ferait de la partie une horloge séparée du monde — deux
  // temps qui dérivent l'un de l'autre — et donnerait au joueur un levier
  // hors fiction, ce que le manuel interdit partout ailleurs.

  // ---- un front : l'obstacle en tête, nos cartes empilées dessous ---------
  // NI EN-TÊTE NI PIED SUR UN FRONT. L'en-tête recopiait en capitales le
  // dessein qui est déjà en toutes lettres dans la colonne de gauche, et il
  // faisait trois lignes au-dessus de chaque colonne. Le pied disait « tenu par
  // eux » là où la couleur du cadre et le ✅ de la clef le disent déjà. Le
  // dessein servi reste accessible : il est en infobulle sur la colonne.
  function front(f) {
    const d = el("div", "pc-front pc-prevaut-" + (f.prevaut || "vert")
                        + (f.contre_nous === false ? " pc-front-nous" : ""));
    d.title = "contre « " + (f.sur_titre || "") + " » — " + (f.pourquoi || "");
    // PAS DE LIGNE « CE QUE ÇA SERT ». Essayée, et retirée aussitôt : tronquée
    // à une ligne elle était illisible, entière elle faisait trois lignes de
    // titres au-dessus de chaque colonne — la colonne des états cibles revenue par
    // la fenêtre. La chaîne reste dans l'infobulle de la colonne, et dans la
    // vue servie par `/partie` pour qui en a besoin.
    // UNE LIGNE PAR OBJET, ET SES PIÈCES POSÉES DEDANS. La pile empilait des
    // cartes sans dire laquelle tenait laquelle, et les pièces engagées
    // n'étaient nulle part : la vue les retire des cartes filles parce qu'elles
    // y répétaient le titre de la clef. On les remet ici, à leur place — ce
    // qu'on a mis là est ce avec quoi on tient, et ça doit se voir.
    // QUI PRÉVAUT, ÉCRIT EN TÊTE. C'est LA chose que ce plateau a à dire — un
    // front est une dispute, et son verdict décide de la partie — et elle ne
    // vivait que dans l'infobulle de la colonne. L'ancien en-tête avait été
    // retiré parce qu'il recopiait le dessein ; celui-ci ne recopie rien : il
    // dit qui tient, et par quoi. Le motif vient du greffe (`pourquoi`), qui
    // sait dire « levé par 🗝️ … », « suspendu par ❓ … », « aucune clef ne le lève ».
    const nous = f.prevaut && vue.camp && f.prevaut === vue.camp;
    const verdict = el("div", "pc-verdict" + (nous ? " pc-verdict-nous" : ""));
    verdict.appendChild(el("span", "pc-verdict-q", (nous ? "à vous" : "à eux")));
    verdict.appendChild(el("span", "pc-verdict-p", f.pourquoi || ""));
    d.appendChild(verdict);
    const pile = el("div", "pc-pile");
    pile.dataset.prevaut = PartieGrille.teinte(f.prevaut);   // le bord double va au camp qui prévaut
    const eng = engagees();
    // LA CARTE DU DESSOUS (6.9). Un verrou posé sur une CLEF vivait dans son
    // front sans dire sur quoi il était, et la clef, dans la rangée de son
    // état, ne disait pas qu'elle était couverte : « la clef est posée sur
    // quoi ? » — on était perdu. Le greffe sert `dessous`, la clef visée ;
    // elle se montre en tête du front, sous le mot « sur », et le verrou
    // s'empile dessus. C'est le langage du plateau, une carte sur une carte,
    // pas une ligne de titres.
    // À DROITE, PAS EN DESSOUS (6.9, à la demande du joueur) : la clef bloquée
    // d'abord, puis le verrou après elle, sur la même rangée — on lit de gauche
    // à droite « cette clef, bloquée par ce verrou ».
    // DANS L'ORDRE : LA CLEF (et ce qu'elle engage), PUIS LA PIÈCE, PUIS LE
    // VERROU. La pièce produit le verrou — il en est la conséquence et la fin
    // de la chaîne —, donc elle se lit avant lui : « cette clef, bloquée par
    // le lecteur, d'où ce verrou ».
    if (f.dessous) {
      const rang = el("div", "pc-rang-sur");
      const sur = el("div", "pc-dessous");
      sur.appendChild(ligne(f.dessous, eng));
      sur.appendChild(el("span", "pc-dessous-l", "bloquée par"));
      rang.appendChild(sur);
      rang.appendChild(ligne(f.tete, eng, null, true));
      pile.appendChild(rang);
    } else {
      pile.appendChild(ligne(f.tete, eng));
    }
    (f.pile || []).forEach((o) => {
      pile.appendChild(ligne(o, eng, "pc-sous"));
      (o.sous || []).forEach((s) => {
        if (s.type === "piece") return;         // déjà servie par `engagees`
        const cs = carte(s); cs.classList.add("pc-sous2");
        pile.appendChild(cs);
      });
    });
    d.appendChild(pile);
    return d;
  }

  const engagees = () => PartieGrille.engagees(vue);
  const ligne = PartieGrille.ligne;

  function rangee(nom, cartes, vide) {
    const r = el("div", "pc-rangee");
    if (nom) r.appendChild(el("div", "pc-lbl", nom));
    if (!cartes.length) r.appendChild(el("div", "pc-vide", vide || "—"));
    cartes.forEach((c) => r.appendChild(carte(c)));
    return r;
  }

  // ---- le plateau entier ---------------------------------------------------
  function dessiner() {
    const h = hote();
    if (!h) return;
    const sig = JSON.stringify(vue);
    if (sig === dernier) return;
    dernier = sig;
    h.innerHTML = "";
    // LE HOVER REVENAIT PLUS. `pc-en-main` masque les volets pendant qu'on
    // tient une carte (`display:none !important`), et il ne se retirait qu'au
    // `dragend` de la carte tirée — or un coup joué redessine le plateau, la
    // carte quitte le DOM avant son dragend, et l'événement ne vient jamais :
    // le plateau restait « en main » à vide, sans un seul texte au survol,
    // jusqu'au rechargement. Un redessin efface la main : il n'y a plus rien
    // de tenu quand toutes les cartes viennent d'être refaites.
    h.classList.remove("pc-en-main");
    tenue = null;
    // LA MOITIÉ QUI A LA MAIN SE COLORE : le trait en mots dans la barre ne
    // suffisait pas, on cherchait qui doit jouer. Le fond de leur côté ou du
    // nôtre le dit (partie.css, « la moitié qui a la main »).
    h.classList.remove("pc-trait-nous", "pc-trait-eux");
    if (vue && vue.partie && vue.trait) h.classList.add(vue.trait === vue.camp ? "pc-trait-nous" : "pc-trait-eux");
    if (!vue || !vue.partie) {
      h.appendChild(el("div", "pc-rien", charge ? "Aucune partie ouverte. Le conseil de guerre s'ouvrira quand le mestre en aura une à tenir."
                                                 : "Le mestre rassemble les cartes…"));
      return;
    }
    // UN SIÈGE QUI N'EST DANS AUCUN CAMP de cette partie voit tout en face et
    // rien en main — un plateau qui n'a pas de sens. On le dit, avec les camps
    // qui existent et l'adresse qui les choisit, au lieu de laisser deviner.
    const camps = Object.keys(vue.decks || {});
    if (camps.length && camps.indexOf(vue.camp) < 0 && vue.camp !== "arbitre") {   // l'arbitre n'a pas de deck, et c'est normal
      h.appendChild(el("div", "pc-rien", "Vous regardez « " + vue.partie + " » sans y avoir de camp. Ses camps : "
        + camps.join(", ") + ". Ajoutez ?id=" + vue.partie + "&camp=<le vôtre> à l'adresse."));
      return;
    }
    const bar = el("div", "pc-bar");
    bar.appendChild(el("span", "", "jour " + (vue.jours + 1) + " de la partie"));
    // « EUX » NE DÉSIGNE PERSONNE À PLUS DE DEUX CAMPS (6.9). Sur main haute,
    // quatre camps : « le trône est à eux » et « on attend leur coup » ne
    // disaient pas lequel — et c'est la seule chose qu'on cherche en revenant
    // devant le plateau. La couleur est celle du joueur : on nomme le camp,
    // avec son rond, partout où l'on disait « eux ».
    const nomme = (c) => PartieGrille.rond(c) + " " + c;
    bar.appendChild(el("span", "", !vue.trone ? "👑 le trône n'est constaté à personne"
                                  : vue.trone === vue.camp ? "👑 le trône est à nous"
                                  : "👑 le trône est à " + nomme(vue.trone)));
    bar.appendChild(el("span", "", vue.trait === vue.camp ? "à vous de jouer"
                                  : vue.trait ? "on attend " + nomme(vue.trait)
                                  : "tous ont joué — le jour peut passer"));
    // LE COUP DU JOUR — la règle que tout le monde casse, enfin affichée
    const n = ((vue.coups_du_jour || {})[vue.camp]) || 0;
    const max = vue.coups_max || 1;   // deux quand un humain et une IA se partagent le camp
    const cj = el("span", "pc-coup-jour" + (n ? (n > max ? " pc-coup-trop" : " pc-coup-fait") : " pc-coup-passer"),
      n === 0 ? "● coup du jour : à jouer — ou passer"
      : n > max ? "⚠ " + n + " coups ce jour — " + max + " seulement compte" + (max > 1 ? "nt" : "")
      : max > 1 ? "✓ " + n + " coup" + (n > 1 ? "s" : "") + " sur " + max + " ce jour" : "✓ coup du jour : joué");
    if (n === 0 && vue.camp !== "arbitre") {   // PASSER est un coup : un clic, une confirmation
      cj.title = "Passer ce jour sans rien poser";
      cj.addEventListener("click", () => { if (confirm("Passer ce jour sans rien poser ?")) jouer({ quoi: "passer" }); });
    }
    bar.appendChild(cj);
    if (vue.camp === "arbitre") {   // LE JOUR PASSE — l'arbitre seul, et ça se voit
      const j = el("button", "pc-bt pc-jour", "⏭️ le jour passe");
      j.addEventListener("click", () => { if (confirm("Passer le jour ? Les frappes atterrissent, les arrivées entrent.")) jouer({ quoi: "jour" }); });
      bar.appendChild(j);
    }
    h.appendChild(bar);
    if (envoi) h.appendChild(el("div", "pc-bat", "le mestre inscrit le coup…"));
    else if (leurCoup) h.appendChild(el("div", "pc-bat pc-bat-eux",
      leurCoup === 1 ? "ils viennent de jouer — un coup de plus au livre"
                     : "ils viennent de jouer — " + leurCoup + " coups de plus au livre"));
    // CE QU'ILS ONT JOUÉ, ET PAS SEULEMENT QU'ILS ONT JOUÉ. La pastille rouge
    // et « ils viennent de jouer » disaient qu'une carte avait bougé ; à deux
    // joueurs, la seule question en revenant devant le plateau est « qu'a-t-il
    // fait ? ». Le greffe le sait — c'est `partie.py --relire` —, et la vue le
    // porte maintenant : les lignes du livre depuis NOTRE dernier coup, ids
    // rhabillés de leurs titres. La liste se vide d'elle-même quand on joue :
    // le marque-page avance, donc ce qu'on vient de lire ne se relit pas.
    // PLUS DE BLOC AU-DESSUS DU PLATEAU (5.9) : la relecture est dite dans le
    // fil, au premier regard, par `PartieGrille.loguer` — même chemin que
    // chaque ligne neuve, hors fiction, jamais écrite dans flux.jsonl.
    h.appendChild(el("div", "pc-jouable", jouable()));
    if (mot) {
      const m = el("div", "pc-mot" + (motMauvais ? " pc-mot-non" : ""), mot);
      h.appendChild(m);
    }

    // PLUS DE COLONNE « MES DESSEINS ». C'était un arbre d'objectifs qui ne
    // bougeait pas d'un tour à l'autre, occupant un cinquième de l'écran pour
    // répéter ce que les fronts disent déjà, et il ne servait aucune décision :
    // on ne joue pas sur un dessein, on joue sur ce qui s'y oppose. Ce qu'il
    // portait d'utile — la chaîne jusqu'au trône — vit sur chaque front.
    // Les questions ❓ posées sur un dessein, elles, ne se perdent pas : elles
    // remontent en tête du plateau, parce qu'elles attendent une réponse.
    // LEUR CÔTÉ, EN HAUT. Leurs pièces avaient d'abord été mises en rangée du
    // deck, sous « En main » — ce qui revenait à dire que Vhagar est dans la
    // main de la reine. La table d'un jeu à deux se lit de haut en bas : eux,
    // le terrain disputé, nous. La position suffit à dire à qui c'est, avec la
    // couleur du bord ; aucun libellé n'a à l'expliquer.
    // UNE PIÈCE POSÉE N'EST PLUS DANS LA BANDE. Elle est dans la grille, sous
    // le verrou qui l'engage — la montrer aussi ici, c'est la compter deux
    // fois. On dessine donc le plateau D'ABORD, et la bande ne garde que ce
    // qui n'y figure pas : le libre, ce qui arrive, ce qui se remet, et une
    // posée dont le tenant n'a pas de ligne (un verrou sur un état).
    const plateau = el("div", "pc-plateau");
    // LES ÉTATS CIBLES EN UNE RANGÉE, pas en colonne : celle-ci avait été retirée
    // (immobile, un cinquième de l'écran), mais sans front l'écran ne disait
    // plus même ce qu'on vise. Une rangée de cases 🎯 par racine, ses ❓ dessus.
    // LA CARTE EN LIGNES (6.9) : une ligne par état, l'arbre par retrait, et
    // tout ce qui s'applique à l'état à sa droite, dans l'ordre de la chaîne
    // (partie-grille.js, `lignes`). Les verrous ont quitté les colonnes : ils
    // sont sur la ligne de ce qu'ils bloquent. Les fronts ne gardent que les
    // FRAPPES, posées sur des pièces et non sur des états.
    plateau.appendChild(PartieGrille.lignes(vue));
    const frappes = (vue.fronts || []).filter((f) => f.tete && f.tete.type === "frappe");
    if (frappes.length) {
      const fronts = el("div", "pc-fronts");
      frappes.forEach((f) => fronts.appendChild(front(f)));
      plateau.appendChild(fronts);
    }
    const dessinees = new Set([...plateau.querySelectorAll(".pc-carte")].map((n) => n.dataset.id));
    const horsGrille = (c) => !dessinees.has(c.id);
    // UNE BANDE PAR CAMP D'EN FACE, dans l'ordre des camps de la partie (6.9).
    // Une seule bande prenait le camp de sa première carte pour nommer tout le
    // reste : sur main haute elle disait « 🔴 EUX openai · 24 pièces » pour
    // dix-sept pièces d'OpenAI, cinq du successeur et deux du continent. À
    // deux camps, rien ne change : une bande. À quatre, chacun a la sienne,
    // avec son rond, son nom, son compte — et le lavis du trait va à la seule
    // bande de celui qui doit jouer, dans SA couleur.
    const eux = (vue.eux || []).filter(horsGrille);
    const ordre = Object.keys(vue.decks || {}).filter((c) => c !== vue.camp);
    eux.map((c) => c.camp).forEach((c) => { if (ordre.indexOf(c) < 0) ordre.push(c); });
    ordre.forEach((campEux) => {
      const siennes = eux.filter((c) => c.camp === campEux);
      if (!siennes.length) return;
      const face = el("div", "pc-eux pc-teinte-" + PartieGrille.teinte(campEux)
                             + (vue.trait === campEux ? " pc-a-lui" : ""));
      face.dataset.camp = campEux;
      face.appendChild(PartieGrille.bandeau(campEux, false, "main"));
      siennes.forEach((c) => face.appendChild(carte(c)));
      h.appendChild(face);
    });
    h.appendChild(plateau);

    // Le deck est aussi une CIBLE : une carte à nous qu'on y ramène est
    // reprise, et ses pièces se remettent deux jours. Le geste est le même que
    // celui qui les a posées, à l'envers — rien de neuf à apprendre.
    const deck = el("div", "pc-deck");
    // UNE PIÈCE VISÉE PAR UNE FRAPPE RENTRE AUSSI (6.9) : la frappe tombe et la
    // pièce se remet quatre jours — règle 23. Le seul geste du plateau qui
    // demande confirmation, parce qu'il a un prix et qu'on le lâche vite.
    const reprenable = (t) => t && (t.type !== "piece" || t.apparence === "detruite" || (t.visee && t.camp === vue.camp));
    deck.addEventListener("dragover", (e) => {
      if (!reprenable(tenue)) return;
      e.preventDefault();
      deck.classList.add("pc-survol");
    });
    deck.addEventListener("dragleave", () => deck.classList.remove("pc-survol"));
    deck.addEventListener("drop", (e) => {
      e.preventDefault();
      deck.classList.remove("pc-survol");
      if (!reprenable(tenue)) return;
      if (tenue.type === "piece" && tenue.apparence !== "detruite"
          && !confirm("Rentrer « " + tenue.titre + " » ? La frappe tombe, la pièce se remet 4 jours.")) return;
      jouer({ quoi: "reprendre", sur: tenue.id });   // clef, verrou → retirer · état → sortir · perdue → reconstruire
    });
    const d = vue.deck || {};
    // « MAIN » NE PREND PLUS UNE LIGNE (6.9) : le mot est dans le coin du
    // bandeau du deck, la rangée commence directement par les cartes.
    const main = rangee(null, (d.main || []).filter(horsGrille), "rien de libre");
    main.classList.add("pc-main");   // la rangée se nomme : son fond porte la couleur pleine du camp
    main.appendChild(PartieGrille.demandeur());   // la case 📦 vide : demander une pièce
    deck.appendChild(main);
    const ailleurs = (d.route || []).concat(d.remet || []).filter(horsGrille);
    if (ailleurs.length) deck.appendChild(rangee("En route · se remet", ailleurs));
    // PLUS DE RANGÉE « POSÉES » : une pièce engagée est DANS la grille, sous la
    // clef ou le verrou qui la tient (partie-grille.js, `ligne`). La rangée
    // datait du temps où la vue les retirait des cartes filles et où le deck
    // était le seul endroit à les dire — elle ne faisait plus que les répéter.
    // une perdue encore engagée est barrée dans la grille : pas deux fois
    const perdues = (d.detruites || []).filter(horsGrille);
    if (perdues.length) deck.appendChild(rangee("Perdues", perdues));
    deck.insertBefore(PartieGrille.bandeau(vue.camp, true, "votre main"), deck.firstChild);
    h.appendChild(deck);
    h.appendChild(PartieGrille.legende());
  }

  // ---- charger : la vue vient du serveur, dérivée du jsonl ----------------
  function charger() {
    fetch(adresse("/partie"), { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((v) => {
        // CE QU'ILS ONT ÉCRIT PENDANT QU'ON REGARDAIT. Le camp d'en face joue à
        // la ligne, par le mestre : sans ce compte, son coup n'arrivait à
        // l'écran qu'au prochain changement de scène, et le joueur attendait
        // devant une position déjà périmée. On compare le n de la dernière
        // ligne, rien d'autre — la relecture n'avance PAS le marque-page
        // (le serveur ne le pose qu'à la première ouverture), donc les pastilles
        // du neuf tiennent jusqu'au prochain coup à nous, comme avant.
        if (v && v.dernier != null) {
          if (vuDernier != null && v.dernier > vuDernier) {
            leurCoup += v.dernier - vuDernier;
            animerDepuis = vuDernier;
          }
          vuDernier = v.dernier;
        }
        vue = v; charge = true; dessiner();
        PartieGrille.loguer(v);   // chaque ligne neuve dite dans le fil, sans rien écrire
        animerLeurCoup();
      })
      .catch(() => { vue = null; charge = true; dessiner(); });
  }

  // LEUR COUP SE VOIT ARRIVER. La marque du neuf tient jusqu'à notre prochain
  // coup, et c'est bien — mais elle est muette : une carte qui vient de
  // changer sous nos yeux entre deux battements du guet ressemblait à une carte
  // qui avait changé avant-hier. Ce qu'ils ont touché depuis notre dernier
  // regard (toute carte dont `touche` dépasse le n d'avant) se pose sur la
  // table d'un mouvement, en cascade, et le bandeau descend avec. Une fois :
  // la classe part au bout de l'animation, la marque reste.
  function animerLeurCoup() {
    if (animerDepuis == null) return;
    const seuil = animerDepuis; animerDepuis = null;
    const h = document.getElementById("partie");
    if (!h) return;
    const cartes = Array.from(h.querySelectorAll(".pc-carte[data-touche]"))
      .filter((d) => Number(d.dataset.touche) > seuil);
    cartes.forEach((d, i) => {
      d.style.setProperty("--pc-rang", i);
      d.classList.add("pc-arrive");
      d.addEventListener("animationend", () => d.classList.remove("pc-arrive"), { once: true });
    });
    const bat = h.querySelector(".pc-bat-eux");
    if (bat) bat.classList.add("pc-arrive");
  }

  // Le guet ne bat que si l'onglet est SOUS LES YEUX : une vue cachée qui
  // interroge le serveur toutes les six secondes est du réseau pour personne.
  function guetter() {
    const h = document.getElementById("partie");
    if (h && h.offsetParent !== null && !envoi) charger();
  }
  const relire = () => { dernier = ""; charger(); };
  // Un coup à nous vaut « j'ai vu » : le compte de leurs coups repart de zéro.
  const vuLeurs = () => { leurCoup = 0; };

  window.addEventListener("DOMContentLoaded", () => {
    // La ceinture de la bretelle ci-dessus : un glissé lâché n'importe où finit
    // toujours par rendre la main, même si sa carte n'existe plus.
    window.addEventListener("dragend", () => {
      const h = document.getElementById("partie");
      if (h) h.classList.remove("pc-en-main");
      h && h.querySelectorAll(".pc-appel").forEach((x) => x.classList.remove("pc-appel"));
      tenue = null;
    }, true);
    window.addEventListener("drop", () => {
      const h = document.getElementById("partie");
      if (h) h.classList.remove("pc-en-main");
    }, true);
    charger();
    setInterval(guetter, 6000);
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "conseil", nom: "Le conseil", hote: "partie", ordre: 2.6,
        dispo: () => true,
        reparu: () => { charger(); },
      });
    }
    // Un changement de scène peut suivre un coup joué ailleurs : on relit.
    if (window.Bus && Bus.enregistrer) Bus.enregistrer("effacer", relire);
    if (window.Bus && Bus.enregistrer) Bus.enregistrer("partie", relire);
  });

  return { charger, relire, vue: () => vue };
})();
