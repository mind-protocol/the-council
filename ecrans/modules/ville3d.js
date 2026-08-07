// ville3d.js — les échelles « la ville » et « le château », en volume.
//
// Ce qu'il y avait hors les murs était un croquis vu du dessus (`etat/ville.json`,
// rendu par terrain.js). Là où le monde en volume existe — Port-Réal, Peyredragon —
// c'est le vrai relief qui prend la place : la même chose, mais avec la hauteur du
// Dragonmont et l'ombre des collines. Le croquis reste pour les lieux sans maillage.
//
// Trois disciplines, et elles expliquent tout le fichier :
//  - On ne charge RIEN tant que le joueur n'a pas ouvert l'onglet. Un demi-million
//    de volumes derrière un `display:none` est un demi-million de volumes payés
//    pour rien, à chaque partie, chez tout le monde.
//  - Deux onglets, UN SEUL monde. « La ville » et « Le château » sont le même
//    relief regardé de deux hauteurs : la rade de loin, puis la place forte à la
//    verticale. Bâtir deux scènes pour ça coûterait deux fois un demi-million de
//    volumes et deux contextes WebGL, pour montrer les mêmes pierres. Ils
//    partagent donc l'hôte, et basculer ne fait que déplacer la caméra.
//  - On ouvre sur la vue NOMMÉE du lieu (`vues.ville`, `vues.chateau`), jamais sur
//    sa vue par défaut : la baie de Port-Réal est un joli premier regard pour un
//    banc d'essai, pas pour un onglet qui s'appelle « la ville ».
//  - On ne rend d'images QUE quand l'onglet est à l'écran. Une boucle
//    `requestAnimationFrame` qui tourne sous un onglet caché vole les images du fil.
window.Ville3D = (function () {
  "use strict";
  const HOTE = "ville3d";

  let LIEUX = null;      // ce que le serveur offre en volume
  let lieuId = null;     // où se tient le joueur
  let monde = null;      // ouvert une seule fois, au premier affichage
  let ouverture = null;  // la promesse de chargement, pour ne pas ouvrir deux fois
  let vivant = false;
  let derniere = "ville";   // la hauteur de regard demandée en dernier
  let vous = null;          // la balise « vous êtes ici »
  let noms = null;          // les noms des salles, à l'échelle du quartier
  let acteurs = null;       // les gens de la salle, en volume
  let livres = null;        // les registres et carnets de la pièce
  let catalogue = [];       // /books, relu une fois par ouverture
  let plis = null;          // ce qui part et ce qui arrive par écrit
  let courrier = [];        // /plis, relu au rythme des scènes
  let nefs = null;          // les coques : au mouillage ou au sec
  let marques = null;       // noms et positions de ce qui est actif
  let table = [];           // les jetons de /carte, tels quels
  let places = [];          // les lieux, pour nommer une place au loin
  let affectations = {};    // salle/lieu de la fiction -> mètres du monde
  let plante = "";          // la dernière position plantée, pour ne pas la refaire
  let salleDite = null;     // la salle que `/presence` donne au joueur
  let dernierOu = null;     // ses mètres, à l'image précédente
  let trajet = null;        // un voyage en cours : {de, vers, t0}

  const def = () => (LIEUX && lieuId) ? LIEUX.find((l) => l.id === lieuId) : null;
  const offert = () => !!def();

  // ---- le voile de chargement ------------------------------------------------
  // Trente secondes de silence noir passent pour une panne : on dit ce qu'on bâtit.
  function voile(hote) {
    const v = document.createElement("div");
    v.className = "ville3d-voile";
    v.innerHTML = '<div class="ville3d-quoi">le monde se lève…</div>';
    hote.appendChild(v);
    return {
      dire: (t) => { v.firstChild.textContent = t; },
      partir: () => { v.style.opacity = "0"; setTimeout(() => v.remove(), 700); },
      echouer: (t) => { v.firstChild.textContent = t; },
    };
  }

  // Quelle hauteur de regard, et où elle se pose. Un lieu qui ne déclare pas la
  // vue demandée retombe sur son premier regard plutôt que de ne rien montrer.
  // Une vue nommée dit une HAUTEUR et un ANGLE de regard ; elle ne dit pas où
  // regarder. Ouvrir « la ville » sur la rade quand le joueur est au bout du
  // port, c'est lui demander de se chercher lui-même à chaque fois. On garde
  // donc le point de vue tel qu'il est écrit — même recul, même inclinaison —
  // et on le TRANSLATE pour qu'il vise l'endroit où le joueur se tient.
  function regard(d, nom, m) {
    const v = (d.vues && d.vues[nom]) || d.vue;
    const ou = ouJeSuis(d, m);
    if (!v || !v[0] || !v[1] || !ou) return v;
    return [[0, 1, 2].map((i) => v[0][i] - v[1][i] + ou[i]), ou.slice()];
  }

  function poserVue(nom) {
    const d = def();
    if (!monde || !d) return;
    // « Vous » n'est pas une hauteur de regard de plus : c'est le joueur DEBOUT,
    // à l'endroit où il se tient, qui tourne la tête à la souris et marche au
    // ZQSD. On n'y pose donc pas une vue, on y descend — et la balise « vous
    // êtes ici » s'efface, puisqu'on est dedans.
    if (noms) noms.montrer(nom === "chateau");
    if (nom === "salle") {
      const ou = ouJeSuis(d);
      monde.camera.marcher(ou);
      if (vous) vous.montrer(false);
      return;
    }
    monde.camera.vers(...regard(d, nom));
    if (vous) vous.montrer(true);
  }

  async function batir(nom) {
    const hote = document.getElementById(HOTE);
    const d = def();
    if (!hote || !d) return null;
    const etiq = document.createElement("div");
    etiq.className = "ville3d-noms";
    hote.appendChild(etiq);
    const dit = voile(hote);
    try {
      const { ouvrir } = await import("/modules/monde/monde.js");
      const m = await ouvrir({
        hote, etiquettes: etiq, source: d.source, dire: dit.dire,
      });
      m.camera.vers(...((d.vues && d.vues[nom]) || d.vue));
      // La balise du joueur : plantée une fois pour toutes, et remise à
      // l'échelle du recul à chaque image — c'est pour ça qu'on passe une
      // fonction à `demarrer` plutôt que rien.
      // Les adresses décidées en jeu (`scripts/affecter.py`), s'il y en a. Sans
      // elles, la balise retombe sur la place forte du lieu — ce qui est juste
      // pour une reine dans son château, et faux pour tout le monde d'autre.
      try {
        const r = await fetch(d.source + "/corps");
        if (r.ok) affectations = (await r.json()).affectations || {};
      } catch (e) { affectations = {}; }
      indexerAffectations();
      // Le décor sait dire le métier d'un toit ; il ne sait pas que celui-là est
      // la Gaffe. Ce qu'on lui apprend ici vient de la partie, et il en hérite
      // le brouillard avec — voir `nommerEnJeu`.
      if (m.survol) m.survol.apposer(nommerEnJeu);
      const ou = ouJeSuis(d, m);
      // Les adresses viennent d'arriver : le cadrage d'attente posé plus haut
      // visait la vue écrite, on le recentre maintenant sur le joueur.
      if (nom !== "salle") m.camera.vers(...regard(d, nom, m));
      const { poser } = await import("/modules/monde/vous.js");
      vous = poser(m.scene, { xyz: ou, relief: m.relief, hote: etiq, nom: d.nom });
      // Et les noms des pièces. C'est l'échelle du QUARTIER qui les demande :
      // les repères de la ville s'y sont déjà tus (on est à moins de trois
      // cents mètres), et sans eux la place forte est un tas de toits dont
      // rien ne dit lequel est la roukerie. Le plan de château donne la
      // préséance et la coupe des noms, les intérieurs donnent les mètres.
      const { poser: poserNoms } = await import("/modules/monde/salles.js");
      noms = poserNoms(etiq, m.salles(), { plan: planCourant() });
      noms.montrer(nom === "chateau");
      // Et les gens qui s'y tiennent : la balise dit où l'on est, elle ne dit
      // pas avec qui. À l'échelle de la salle, c'est la question qui se pose.
      const { poser: poserActeurs } = await import("/modules/monde/acteurs.js");
      acteurs = poserActeurs(m.scene, { xyz: ou, relief: m.relief, hote: etiq });
      // Et ce qu'il y a sur la table. Un livre est un objet du monde, pas une
      // page d'onglet : sept registres autour de la Table Peinte doivent se
      // voir. Ceux qu'on porte suivent leur porteur — d'où `acteurs.ou`.
      const { poser: poserLivres } = await import("/modules/monde/livres.js");
      livres = poserLivres(m.scene, { xyz: ou, relief: m.relief, salle: salleDite });
      fetch("/books").then((r) => r.ok ? r.json() : null)
        .then((d) => { catalogue = (d && (d.books || d)) || []; })
        .catch(() => { catalogue = []; });
      // Et ce qui voyage. Les trois points de départ viennent des intérieurs du
      // lieu : on lâche un corbeau de la roukerie, pas du milieu de la cour.
      const { poser: poserPlis } = await import("/modules/monde/plis.js");
      const salleOu = (id, defaut) => {
        const s = m.salle && m.salle(id);
        return s ? [s.centre[0], s.centre[1], s.sol_z + (s.hauteur || 0) * 0.9] : defaut;
      };
      plis = poserPlis(m.scene, {
        relief: m.relief, lieu: lieuId, date: null,
        depuis: {
          corbeau: salleOu("roukerie", ou),
          cavalier: salleOu("porte-dragon", ou),
          barque: salleOu("quai", ou),
          pose: null,
        },
      });
      suivreCourrier();
      setInterval(suivreCourrier, 12000);
      // Et les coques. Le quai vient de la VOIRIE — c'est elle qui sait où
      // l'eau touche la pierre ; le plan des salles met le quai sur le
      // plateau, à cent vingt mètres au-dessus de la mer.
      // Les noms et les positions de ce qui est ACTIF. On ne relit ni
      // `vues.json` ni `intentions.json` : `/carte` a déjà fait le brouillard,
      // vieilli les certitudes et laissé tomber ce qu'on ne sait plus.
      const { poser: poserMarques } = await import("/modules/monde/marques.js");
      marques = poserMarques(m.scene, etiq, { lieu: lieuId, xyz: ou, relief: m.relief });
      const { poser: poserNefs } = await import("/modules/monde/nefs.js");
      const bordage = (m.donnees.VOIRIE.aretes || [])
        .filter((a) => a.genre === "quai")
        .flatMap((a) => a.trace || []);
      nefs = poserNefs(m.scene, { relief: m.relief, quai: bordage });
      fetch("/ville").then((r) => r.ok ? r.json() : null)
        .then((d) => { const c = d && d.champ && d.champ.corps; if (c && nefs) nefs.maj(c); })
        .catch(() => {});
      // Et la foule. Elle naît ÉTEINTE (monde.js) parce que le banc d'essai la
      // fait décocher ; ici il n'y a pas de case à cocher, et une ville vide à
      // sept heures du matin est un mensonge. On l'allume, et on lui donne
      // l'heure de la partie — sans quoi elle reste figée sur son défaut de
      // 6h45 et personne ne bouge jamais.
      if (m.foule) m.foule.visible = true;
      // La présence dit où le joueur se tient. On la relit toutes les trois
      // secondes : c'est le rythme des scènes, pas celui des images.
      suivrePresence();
      setInterval(suivrePresence, 3000);
      // Et si c'est par « Vous » qu'on entre, on entre debout : la vue nommée
      // posée plus haut n'était qu'un cadrage d'attente le temps du chargement.
      if (nom === "salle") { m.camera.marcher(ou); vous.montrer(false); }
      heurePartie(m);
      dit.partir();
      return m;
    } catch (e) {
      dit.echouer("le monde n'a pas pu se lever : " + e.message);
      return null;
    }
  }

  // ---- l'onglet paraît, l'onglet s'en va -------------------------------------
  function reparu(nom) {
    derniere = nom || derniere;
    if (!ouverture) {
      ouverture = batir(nom).then((m) => {
        monde = m;
        if (monde) { vivant = true; monde.demarrer(marquer); }
      });
      return;
    }
    if (!monde) return;
    // Le monde est déjà là : changer d'onglet, c'est changer de hauteur, pas
    // rebâtir. On repose la vue même si le joueur avait tourné autour — un
    // onglet nommé « le château » doit montrer le château, pas le dernier
    // cadrage qu'on y a laissé.
    poserVue(nom);
    // La toile a été dimensionnée sous un onglet caché, ou la fenêtre a bougé
    // pendant qu'on regardait ailleurs : on remesure avant de reprendre.
    monde.redimensionner();
    if (!vivant) { vivant = true; monde.demarrer(marquer); }
  }

  // Une image de plus : la balise se remet à l'échelle du recul et son fanion
  // se reprojette. Elle passe par `surImage` du monde, après le rendu, comme
  // les étiquettes de repères.
  // ---- où le joueur se tient, en mètres --------------------------------------
  // La salle courante est nommée par `plan.js` ; si elle a reçu une adresse
  // physique, ce sont SES mètres qui font foi. Sinon la place forte du lieu,
  // qui est ce qu'on avait avant et qui reste vrai pour qui l'habite.
  //
  // C'était la liaison manquante : la balise était plantée une fois pour toutes
  // sur une constante par lieu. Un joueur qui n'habite pas le château se voyait
  // donc annoncer qu'il était au Donjon Rouge, à deux kilomètres de sa cabane.
  // La salle vient de `/presence`, qui est la seule à en tenir le compte pour
  // le joueur : `append_flux.py` l'y pose à chaque item, comme il y pose les
  // PNJ. Le plan sert de recours quand la présence ne sait pas — il devine du
  // bandeau, ce qui marche tant que l'en-tête est franc.
  function ouJeSuis(d, m) {
    const repli = (d && d.vous)
      || ((d && d.vues && d.vues.chateau) ? d.vues.chateau[1] : (d ? d.vue[1] : [0, 0, 0]));
    const sid = salleDite || ((window.Plan && Plan.salle) ? Plan.salle() : null);
    // LE DEDANS D'ABORD. Une salle creusée sait où est sa dalle et son milieu ;
    // une affectation ne sait que le bâtiment qui la contient — et à Peyredragon
    // les deux ne sont pas au même endroit (la chambre de la Table Peinte est à
    // cinquante mètres du volume auquel elle est affectée, et trente-quatre au-
    // dessus de la grande salle). Se poser sur le bâtiment, c'est se poser sur
    // son toit ou dans son mur ; se poser sur la salle, c'est être dans la pièce.
    const mm = m || monde;
    const piece = (mm && mm.salle) ? mm.salle(sid) : null;
    if (piece && piece.centre) {
      return [piece.centre[0], piece.centre[1],
              piece.sol_z != null ? piece.sol_z : piece.centre[2]];
    }
    // `salle:` d'abord, `lieu:` en repli — La Gaffe n'est pas une salle du
    // plan, et le joueur y est pourtant bien assis.
    const a = sid ? (affectations["salle:" + sid] || affectations["lieu:" + sid]) : null;
    // `corps.json` sert tous les mondes d'un coup : une affectation dit le sien.
    // Des mètres de Port-Réal appliqués à Peyredragon ne sont pas une erreur de
    // quelques pas, c'est un autre continent.
    const mien = a && (!a.monde || !lieuId || a.monde === lieuId);
    return (mien && Array.isArray(a.xyz) && a.xyz.length >= 3) ? a.xyz : repli;
  }

  // ---- les noms que LA PARTIE a posés ---------------------------------------
  // Le décor nomme un toit par son métier — « Auberge », « Entrepôt » : c'est le
  // bâti qui le porte depuis qu'il a été semé, et c'est vrai pour tout le monde.
  // Ce que la partie ajoute est d'une autre nature : la Gaffe est l'auberge où
  // Marlo a dormi, et la reine ne sait pas qu'elle existe. D'où le filtre, qui
  // est le même que celui du serveur pour les étiquettes plantées (`visible`) :
  // affecter un endroit lui donne des mètres, le montrer dit que ce joueur-là
  // sait où il est. Les deux gestes sont séparés, et le survol respecte le
  // second — sans quoi il serait le trou par lequel tout le brouillard s'en va.
  let parBat = {};

  function connuDuJoueur(v) {
    const vu = v && v.visible;
    if (vu === true) return true;
    const moi = (window.Moi && window.Moi.personnage_id) || null;
    return !!(Array.isArray(vu) && moi && vu.includes(moi));
  }

  function indexerAffectations() {
    parBat = {};
    for (const clef of Object.keys(affectations)) {
      const genre = clef.split(":")[0];
      // Ce qui est DEDANS n'a pas de nom sur la ville : un livre et un homme
      // n'ont que le toit qui les abrite. Même règle qu'au serveur.
      if (genre !== "lieu" && genre !== "salle") continue;
      const v = affectations[clef];
      if (!v || v.bat == null) continue;
      if (v.monde && lieuId && v.monde !== lieuId) continue;
      if (!connuDuJoueur(v)) continue;
      if (!parBat[v.bat]) parBat[v.bat] = v;
    }
  }

  // Le décor a trouvé quelque chose ; on lui donne le nom qu'ELLE lui donne.
  // Un métier ne disparaît pas pour autant : il descend d'un cran et devient
  // ce que la chose EST — « La Gaffe / taverne — Le port et ses hangars ».
  function nommerEnJeu(t) {
    if (t.genre === "bati") {
      const a = parBat[t.n];
      if (!a || !a.nom) return t;
      const dessous = [t.titre, t.role].filter(Boolean).join(" — ");
      return Object.assign({}, t, { titre: a.nom, role: dessous });
    }
    if (t.genre === "salle") {
      // Le plan de château tient déjà, pour chaque pièce, la ligne qui dit ce
      // qu'elle est : c'est la même au survol du plan et au survol du volume.
      const p = planCourant();
      const s = p && (p.salles || []).find((x) => x.id === t.id);
      if (s) return Object.assign({}, t, { titre: s.nom || t.titre, role: s.quoi || "" });
    }
    return t;
  }

  // Où la présence dit que le joueur se tient. On la relit doucement : elle
  // change au rythme des scènes, pas des images.
  // Le courrier bouge au rythme des scènes, pas des images : douze secondes
  // suffisent, et la date du monde vient avec — c'est elle qui décide si un
  // corbeau part aujourd'hui.
  function suivreCourrier() {
    if (document.hidden || !plis) return;
    Promise.all([
      fetch("/plis").then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch("/carte").then((r) => r.ok ? r.json() : null).catch(() => null),
    ]).then(([c, k]) => {
      if (c && c.plis) courrier = c.plis;
      if (k && k.date) plis.situer({ date: k.date, lieu: lieuId });
      if (k && k.jetons) { table = k.jetons; places = k.lieux || []; }
      if (k && k.date && monde) monde.heure(k.date.minute, k.date.jour);
    });
  }

  function suivrePresence() {
    if (document.hidden) return;
    fetch("/presence")
      .then((r) => r.ok ? r.json() : null)
      .then((p) => { if (p && p.connue) salleDite = p.salle || null; })
      .catch(() => {});
  }

  // ---- le voyage -------------------------------------------------------------
  // Une position qui saute d'un bout de la ville à l'autre ne dit rien du
  // chemin : le joueur voit une balise ici, puis une balise là, et rien ne l'a
  // relié. Au-delà d'une portée de voix, on FAIT LE TRAJET — la balise glisse et
  // la caméra la suit. Ce n'est pas un ornement : c'est la seule chose qui
  // montre que Port-Réal est grand, et qu'aller au chantier du bout coûte huit
  // cents mètres.
  //
  // En deçà, on se pose sans façon : traverser une cour n'est pas un voyage.
  const VOYAGE_MIN = 120;      // mètres — au-delà, on se déplace à vue
  const VOYAGE_MS = 2200;

  function allerA(ou) {
    if (!vous) return;
    const de = trajet ? trajet.vers.slice() : dernierOu;
    const loin = de && Math.hypot(ou[0] - de[0], ou[1] - de[1]) > VOYAGE_MIN;
    if (!de || !loin) {
      vous.deplacer(ou);
      if (acteurs) acteurs.deplacer(ou);
      if (livres) livres.deplacer(ou, salleDite);
      if (plis) plis.situer({ depuis: { pose: ou } });
      dernierOu = ou.slice();
      trajet = null;
      return;
    }
    trajet = { de: de.slice(), vers: ou.slice(), t0: performance.now() };
  }

  function avancerVoyage() {
    if (!trajet) return;
    const k = Math.min(1, (performance.now() - trajet.t0) / VOYAGE_MS);
    // Départ et arrivée adoucis : un homme ne part pas à pleine vitesse.
    const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    const p = [0, 1, 2].map((i) => trajet.de[i] + (trajet.vers[i] - trajet.de[i]) * e);
    vous.deplacer(p);
    if (acteurs) acteurs.deplacer(p);
    if (livres) livres.deplacer(p, salleDite);
    if (plis) plis.situer({ depuis: { pose: p } });
    // La caméra accompagne sans se recadrer : on garde la hauteur et l'angle
    // qu'avait le joueur, on ne fait que suivre le point regardé.
    // À pied, on ne pilote pas la caméra : le joueur marche, et `marcher()` a
    // déjà été appelé. Deux mains sur le même volant font un tremblement.
    if (monde && monde.camera && monde.camera.cible && !monde.camera.apied) {
      monde.camera.cible.set(p[0], p[1], p[2]);
      if (monde.camera.poser) monde.camera.poser();
    }
    dernierOu = p;
    if (k >= 1) { dernierOu = trajet.vers.slice(); trajet = null; }
  }

  // L'heure de la partie, lue là où elle est déjà tenue : `window.Horloge`,
  // posée par bus.js à chaque item daté du flux, et à défaut la date servie par
  // /carte. Le décor ne tient aucune horloge à lui — il lit celle du monde.
  //
  // ENTRE DEUX BATTEMENTS, elle COULE. C'est le seul endroit du jeu où le temps
  // s'écoule tout seul, et il faut dire pourquoi : l'heure de la partie n'avance
  // que quand un item tombe, d'une minute ou deux à la fois. Une ville qui ne
  // bouge que sur les battements est une ville qui téléporte quatre mille
  // personnes de quatre-vingts mètres toutes les trois minutes, et qui reste
  // morte le reste du temps — c'est-à-dire pendant qu'on la regarde.
  //
  // Ce qui coule n'est donc PAS une seconde horloge du monde : c'est
  // l'interpolation d'affichage entre deux heures reçues. Elle part de l'heure
  // de la partie, avance à la vitesse RÉELLE, et se RECALE SEC dès qu'un item
  // donne une nouvelle heure. Rien ne s'écrit nulle part, l'heure du bandeau
  // reste celle de bus.js, et l'état ne la voit jamais.
  //
  // Le temps réel, et pas plus vite : un piéton de `journee.js` fait ses
  // soixante-dix mètres par minute de fiction. À une minute par seconde, il
  // traverserait la ville en dix secondes — on ne verrait pas une foule marcher,
  // on verrait des traits. À l'échelle 1:1 il marche à son pas, et l'écart avec
  // l'heure de la partie ne dépasse jamais le temps qu'on a passé à regarder.
  const COULE = 1 / 60000;     // minutes de fiction par milliseconde réelle
  let dateJeu = null;
  let ancre = null;            // { minute, jour, t0 } — la dernière heure reçue

  function heurePartie(m) {
    const d = window.Horloge || dateJeu;
    if (!m || !d) return;
    const jour = ((d.lune || 1) - 1) * 30 + (d.jour || 1);
    const minute = typeof d.minute === "number" ? d.minute : 6 * 60 + 45;
    if (!ancre || ancre.minute !== minute || ancre.jour !== jour) {
      ancre = { minute, jour, t0: performance.now() };
    }
    let mn = ancre.minute + (performance.now() - ancre.t0) * COULE;
    let j = ancre.jour;
    while (mn >= 1440) { mn -= 1440; j += 1; }   // la nuit passe, le jour suit
    m.heure(mn, j);
  }

  function marquer() {
    if (!vous || !monde) return;
    heurePartie(monde);
    const c = monde.rendu.domElement;
    // La salle change au fil des scènes : la balise suit, et la couronne des
    // gens avec elle. On ne bouge que si l'endroit a réellement changé — sans
    // quoi on refait le calcul du relief soixante fois par seconde.
    const ou = ouJeSuis(def());
    const signe = ou.join(",");
    if (signe !== plante) {
      plante = signe;
      // Loin = on fait le trajet à vue ; à côté = on se pose. `allerA` tranche.
      allerA(ou);
      // Le joueur a changé de salle pendant qu'on y était : on le suit sur
      // place. Ce qu'il avait parcouru à pied est perdu, et c'est juste — la
      // fiction vient de le poser ailleurs.
      if (monde.camera.apied) monde.camera.marcher(ou);
    }
    avancerVoyage();
    vous.nommer(nomDuLieu());
    vous.suivre(monde.cam, c.clientWidth, c.clientHeight);
    if (noms) {
      noms.ici(salleDite || ((window.Plan && Plan.salle) ? Plan.salle() : null));
      noms.suivre(monde.cam, c.clientWidth, c.clientHeight);
    }
    if (acteurs) {
      acteurs.maj(presents());
      acteurs.suivre(monde.cam, c.clientWidth, c.clientHeight);
      if (livres) {
        livres.maj(catalogue, (id) => acteurs.ou(id));
        livres.suivre(monde.cam);
      }
      if (plis) { plis.maj(courrier); plis.suivre(monde.cam, 0.016); }
      if (nefs) nefs.suivre(monde.cam, performance.now() / 1000);
      if (marques) {
        marques.maj(table, places);
        marques.suivre(monde.cam, c.clientWidth, c.clientHeight);
      }
    }
  }

  // Qui est dans la salle. La galerie du bandeau fait foi — quelqu'un dont le
  // visage y est se tient sous les yeux du joueur, et c'est exactement ce que
  // le décor doit montrer. Le registre des gens complète le titre quand la
  // scène ne l'a pas donné ; il ne l'écrase jamais.
  function presents() {
    const p = window.Presents || {};
    return Object.keys(p).map((id) => {
      const f = (window.Gens && Gens.qui) ? (Gens.qui(id) || {}) : {};
      return {
        id,
        nom: (p[id] || {}).nom || f.nom || id,
        titre: (p[id] || {}).titre || f.titre || "",
        joueur: !!(window.Moi && Moi.personnage_id === id),
      };
    });
  }

  // Le fanion dit la SALLE quand le plan la connaît — « La chambre de la Table
  // Peinte » vaut mieux que « Peyredragon » sur une carte de Peyredragon. Il
  // retombe sur le nom du lieu quand on ne se tient nulle part de nommé.
  // Le plan de château du lieu où l'on se tient — celui du SIÈGE quand il en a
  // un à lui (`port-real@marlo-vasse`), sans quoi deux joueurs du même lieu
  // liraient les mêmes salles.
  function planCourant() {
    const ch = (window.Plan && Plan.chateau) ? Plan.chateau() : lieuId;
    return (window.Plans || {})[ch || lieuId] || null;
  }

  function nomDuLieu() {
    const d = def();
    const ch = (window.Plan && Plan.chateau) ? Plan.chateau() : lieuId;
    const p = (window.Plans || {})[ch || lieuId];
    const sid = (window.Plan && Plan.salle) ? Plan.salle() : null;
    const s = (p && sid) ? (p.salles || []).find((x) => x.id === sid) : null;
    return s ? s.nom : (d ? d.nom : "");
  }

  function endormir() {
    if (monde && vivant) { monde.arreter(); vivant = false; }
  }

  // On ne peut pas se fier au seul `reparu` pour savoir qu'on est SORTI de
  // l'échelle : rien ne le notifie. La classe posée par plan.js fait foi.
  function guetter() {
    const hote = document.getElementById(HOTE);
    if (!hote || !window.MutationObserver) return;
    new MutationObserver(() => {
      if (hote.classList.contains("vue-off")) endormir();
    }).observe(hote, { attributes: true, attributeFilter: ["class"] });
  }

  // ---- où est le joueur ------------------------------------------------------
  function relire() {
    fetch("/carte").then((r) => r.json()).then((d) => {
      if (d.date) dateJeu = d.date;
      const neuf = d.joueur_lieu_id || null;
      if (neuf === lieuId) return;
      lieuId = neuf;
      // Changer de lieu, c'est un autre relief, un autre bâti, une autre voirie :
      // on ne recoud pas la scène, on la jette. Elle se rebâtira au prochain
      // affichage — et si le nouveau lieu n'a pas de volume, l'onglet disparaît.
      if (vous) { vous.disposer(); vous = null; }
      if (noms) { noms.disposer(); noms = null; }
      if (acteurs) { acteurs.disposer(); acteurs = null; }
      if (livres) { livres.disposer(); livres = null; }
      if (plis) { plis.disposer(); plis = null; }
      if (nefs) { nefs.disposer(); nefs = null; }
      if (marques) { marques.disposer(); marques = null; }
      if (monde) monde.disposer();
      const hote = document.getElementById(HOTE);
      if (hote) hote.innerHTML = "";
      monde = null; ouverture = null; vivant = false;
      if (window.Plan && Plan.rebattre) Plan.rebattre();
      const h = document.getElementById(HOTE);
      if (h && !h.classList.contains("vue-off")) reparu(derniere);
    }).catch(() => {});
  }

  fetch("/monde/lieux").then((r) => r.json()).then((d) => {
    LIEUX = d.lieux || [];
    if (window.Plan && Plan.rebattre) Plan.rebattre();
  }).catch(() => { LIEUX = []; });

  // Les deux onglets, dans l'ordre où l'on descend : la rade, puis la place forte.
  const ECHELLES = [
    { id: "ville3d", nom: "La ville", vue: "ville", ordre: 2 },
    { id: "chateau3d", nom: "Le quartier", vue: "chateau", ordre: 3 },
    // Et la troisième hauteur : une pièce dans le cadre, à hauteur d'homme.
    // C'est la seule où les gens de la salle se voient — plus haut, ils sont
    // trois points sous un toit et la foule reprend la parole.
    { id: "salle3d", nom: "Vous", vue: "salle", ordre: 3.1 },
  ];
  if (window.Plan && Plan.echelle) {
    ECHELLES.forEach((e) => Plan.echelle({
      id: e.id, nom: e.nom, hote: HOTE, ordre: e.ordre,
      // Le château n'a d'onglet que là où le lieu déclare cette hauteur-là :
      // sans `vues.chateau`, on ne va pas planter la caméra au hasard.
      dispo: () => offert() && !!((def().vues || {})[e.vue] || e.vue === "ville"),
      reparu: () => reparu(e.vue),
    }));
  }

  window.addEventListener("DOMContentLoaded", () => {
    guetter();
    relire();
    setInterval(relire, 60000);
  });

  return { offert, relire, monde: () => monde };
})();
