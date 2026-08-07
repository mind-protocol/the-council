// jetons.js — ce que la table PORTE : les pièces qu'on pousse dessus.
// geo.js donne la géographie (elle ne bouge jamais) ; ce module donne la guerre
// (elle bouge à chaque battement). Deux familles, une seule grammaire :
//   • les JETONS  — une pièce posée quelque part : un ost, une flotte, un dragon,
//                   un siège, une bataille, un camp, des vivres.
//   • les TRAITS  — un fil tendu entre deux endroits : une marche, une route de
//                   mer, un corbeau, une attaque, un serment, un mariage, une
//                   querelle.
// Rien ici n'est la vérité : c'est ce que la reine CROIT tenir. D'où `certitude`,
// qui délave la pièce et lui colle un point d'interrogation quand la nouvelle
// vient d'une rumeur. Une table de guerre honnête montre aussi ses trous.
//
// Échelle. Tout glyphe est dessiné dans une boîte de 10 unités centrée en (0,0),
// puis posé par `transform="translate(x,y) scale(ech)"` : les épaisseurs et les
// corps de texte s'écrivent donc en unités LOCALES (pas de var(--k) ici), et la
// vignette serrée comme la grande table gardent exactement le même grain.
"use strict";
window.Jetons = (() => {
  const G = window.Geo || {};
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  // ---- les glyphes ---------------------------------------------------------
  // Quelques traits chacun, pas plus : dans la vignette, une pièce fait neuf
  // pixels de large. Ce qui ne se lit pas à cette taille ne sert à rien.
  const GLYPHES = {
    // un bloc de piques sur sa ligne de front
    armee: '<path d="M-4 3H4"/><path d="M-2.6 3V-2.4"/><path d="M0 3V-3.6"/><path d="M2.6 3V-2.4"/>',
    // deux chevrons lancés : la colonne montée
    cavalerie: '<path d="M-4.4-3L-0.4 0-4.4 3"/><path d="M0.4-3L4.4 0 0.4 3"/>',
    // une coque, un mât, une voile
    flotte: '<path d="M-4.4 0.8Q0 4.6 4.4 0.8"/><path d="M0 0.8V-4.2"/><path d="M0-3.8L2.9-0.8 0-0.8"/>',
    // deux ailes qui se rejoignent sur un corps
    dragon: '<path d="M-5-1.4C-3-2.8-1.4-1.6 0 1.4 1.4-1.6 3-2.8 5-1.4"/><path d="M0 1.4V3.2"/>',
    // un donjon crénelé
    garnison: '<path d="M-2.8 3.4V-1.8H-1.6V-3H-0.5V-1.8H0.5V-3H1.6V-1.8H2.8V3.4Z"/>',
    // le même donjon, ceint (l'anneau est ajouté au montage)
    siege: '<path d="M-2.2 3.4V-1.4H-1.2V-2.4H-0.4V-1.4H0.4V-2.4H1.2V-1.4H2.2V3.4Z"/>',
    // deux épées croisées, gardes en bas
    bataille: '<path d="M-3.6-3.6L3.6 3.6"/><path d="M3.6-3.6L-3.6 3.6"/>' +
      '<path d="M-4.4 1.6L-1.6 4.4"/><path d="M4.4 1.6L1.6 4.4"/>',
    // une tente et son mât
    camp: '<path d="M-4 3.4L0-3.4 4 3.4Z"/><path d="M0-3.4V3.4"/>',
    // un sac lié : le grain, l'argent, ce qui manque toujours
    vivres: '<path d="M-3 3.4V-0.6Q0-3.4 3-0.6V3.4Z"/><path d="M-3 0.6H3"/>',
    // un buste : quelqu'un qu'on croit là. Ce n'est pas une force, c'est un nom.
    tete: '<circle cx="0" cy="-1.6" r="1.9"/><path d="M-3.2 3.6Q0-0.4 3.2 3.6"/>',
    // un feuillet plié et son sceau : un pli, à l'endroit où il en est de sa vie
    pli: '<path d="M-4.2-2.8H4.2V3.2H-4.2Z"/><path d="M-4.2-2.8L0 0.9 4.2-2.8"/>',
    // une flamme et son cœur : un incident. Ce qui a pris et qui se propage —
    // un feu, une rumeur, une peur : sur cette table, ça se compte pareil.
    incident: '<path d="M0 4.2Q-3.4 2.6-3.4 0Q-3.4-2.6-1.1-4.6Q-1.5-1.9 0.5-2.8' +
      'Q-0.3-0.5 1.7-1.6Q3.4-0.3 3.4 0.7Q3.4 2.8 0 4.2Z"/>' +
      '<path d="M0 3.4Q-1.5 2.4-1.5 1.1Q-1.5-0.2 0-1.3Q1.5-0.2 1.5 1.1Q1.5 2.4 0 3.4Z"/>',
    // un point et deux arcs qui s'ouvrent : quelqu'un, et ce qui lui parvient.
    // Pas une oreille dessinée — à neuf pixels, une oreille est une tache.
    oreille: '<circle cx="-3" cy="0" r="1.5"/>' +
      '<path d="M-0.4-2.6A3.2 3.2 0 0 1-0.4 2.6"/>' +
      '<path d="M1.8-4.4A5.4 5.4 0 0 1 1.8 4.4"/>',
  };
  const DEFAUT = "armee";
  const NOM_GENRE = {
    armee: "Ost", cavalerie: "Cavalerie", flotte: "Flotte", dragon: "Dragon",
    garnison: "Garnison", siege: "Siège", bataille: "Bataille", camp: "Camp",
    vivres: "Vivres", tete: "Où l'on les croit", pli: "Pli",
    incident: "Incident", dessein: "Dessein", oreille: "Oreille",
  };
  const NOM_TRAIT = {
    marche: "Marche", mer: "Route de mer", vol: "Vol",
    corbeau: "Corbeau", cavalier: "Porteur", propagation: "Propagation",
    attaque: "Attaque", retraite: "Retraite", serment: "Serment", vassal: "Hommage",
    mariage: "Mariage", querelle: "Querelle", menace: "Menace",
  };

  // ---- où en est un pli ----------------------------------------------------
  // Un message n'est pas un objet, c'est un état qui change : parti, remis,
  // confirmé, resté sans réponse, perdu, pris. La pièce porte une petite marque
  // sur son flanc — la même grammaire que le `?` du doute, à l'autre coin.
  const ETATS = {
    // écrit et pas parti : le seul état qui soit encore entre les mains du
    // joueur. Un trait nu, sans pointe — rien n'est allé nulle part.
    redige:     { nom: "écrit, pas parti",   marque: '<path d="M-2 0H2"/>' },
    parti:      { nom: "parti",              marque: '<path d="M-1.8 0H1.4"/><path d="M0.2-1.2 1.6 0 0.2 1.2"/>' },
    remis:      { nom: "remis",              marque: '<path d="M-1.7 0.1-0.4 1.5 1.8-1.5"/>' },
    confirme:   { nom: "reçu, confirmé",     marque: '<circle r="2.4"/><path d="M-1.2 0.1-0.2 1.1 1.3-1.2"/>' },
    attente:    { nom: "sans réponse encore", marque: '<circle r="1.9"/>' },
    muet:       { nom: "resté sans réponse", marque: '<circle r="1.9"/><path d="M-1.4 1.4 1.4-1.4"/>' },
    perdu:      { nom: "perdu",              marque: '<path d="M-1.7-1.7 1.7 1.7"/><path d="M1.7-1.7-1.7 1.7"/>' },
    intercepte: { nom: "pris en chemin",     marque: '<path d="M-2.4 0Q0-2.2 2.4 0Q0 2.2-2.4 0Z"/><circle r="0.75"/>' },
    // Les trois états d'une oreille. Ils ne se retapent pas : le serveur
    // dérive `parle` et `muette` de l'âge du dernier mot ; le MJ n'écrit que
    // `nouee` (elle n'a rien donné encore) et `perdu` (on sait qu'elle est
    // tombée). Il n'y a PAS d'état « retournée » — si on le savait, on la
    // couperait. C'est le silence long qui porte le doute, et il ne se lève pas.
    nouee:      { nom: "nouée, rien encore", marque: '<path d="M-2 0.9Q0-2.4 2 0.9"/><circle cy="1.2" r="0.7"/>' },
    parle:      { nom: "elle parle",         marque: '<path d="M-1.7 0.1-0.4 1.5 1.8-1.5"/>' },
    muette:     { nom: "silencieuse depuis", marque: '<circle r="1.9"/><path d="M-1.4 1.4 1.4-1.4"/>' },
  };

  // ---- les incidents : ce qui a pris, et jusqu'où ça a gagné ---------------
  // Un feu, une rumeur, une peur : sur cette table ça se suit pareil — un
  // FOYER, des endroits que ça a gagnés, une date par endroit, et une
  // estimation d'âmes touchées. Le MJ écrit UN objet ; le module en dérive le
  // foyer, chaque relais et chaque fil de propagation. Écrire quinze marques à
  // la main pour un seul incident, personne ne le tiendrait deux battements.
  const FEUX = {
    vif:    { nom: "il gagne encore" },
    couve:  { nom: "il couve" },
    eteint: { nom: "éteint" },
  };

  // Un incident posé tout entier ferait une toile d'araignée par-dessus la
  // baie : dix fils et quinze flammes pour quatre nouvelles, et plus personne
  // ne lit les osts. Les fils de propagation et les endroits qu'on PENSE
  // gagner ne se montrent donc qu'au survol de l'incident — on voit les foyers
  // et ce qui a réellement pris, et l'on va chercher la toile du doigt.
  //
  // L'éveil est gardé ICI et non posé sur le DOM : la loupe remplace le <svg>
  // soixante fois par seconde, et une classe accrochée après coup ne
  // survivrait pas au premier tour de molette. Le dessin la porte donc lui-même.
  let eveille = null;
  const eveiller = (id) => {
    if (eveille === id) return false;
    eveille = id || null;
    return true;
  };

  // `propage` accepte "rosby" (au plus court) ou un objet complet.
  const relaisDe = (r) => (typeof r === "string" ? { ou: r } : r || {});

  function deplierUn(inc) {
    const jetons = [], traits = [];
    const relais = (inc.propage || []).map(relaisDe).filter((r) => r.ou || r.point);
    const total = (inc.ames || 0) +
      relais.reduce((n, r) => n + (r.ames || 0), 0);
    const commun = { genre: "incident", camp: inc.camp, feu: inc.feu || "vif",
                     incident_id: inc.id, statut: "actif" };
    jetons.push(Object.assign({}, commun, {
      id: inc.id, ou: inc.ou, point: inc.point, nom: inc.nom, foyer: true,
      ames: inc.ames, jours: inc.jours, certitude: inc.certitude,
      contenu: inc.contenu, detail: inc.detail,
      total: total !== (inc.ames || 0) ? total : null,
      relais: relais.length,
    }));
    // `risque` : là où l'on PENSE que ça va gagner. Ce n'est pas une nouvelle,
    // c'est une crainte — le fil se fait maigre et pointillé, la pièce se vide,
    // et le compte d'âmes y est une estimation de ce qu'on perdrait, pas de ce
    // qu'on a perdu. On ne mélange jamais les deux à l'œil.
    const craints = (inc.risque || []).map(relaisDe).filter((r) => r.ou || r.point);
    const poser = (r, i, prevu) => {
      jetons.push(Object.assign({}, commun, {
        id: inc.id + (prevu ? "-risque-" : "-") + (r.ou || i), ou: r.ou, point: r.point,
        nom: r.nom || inc.nom, ames: r.ames, jours: prevu ? null : r.jours,
        // une crainte n'est jamais « sûre », quoi qu'en dise le foyer
        certitude: prevu ? (r.certitude || "rumeur") : (r.certitude || inc.certitude),
        detail: r.note || r.detail, contenu: inc.contenu, prevu: prevu || null,
      }));
      traits.push({
        id: inc.id + (prevu ? "-crainte-" : "-fil-") + (r.ou || i), genre: "propagation",
        camp: inc.camp, de: inc.ou, point_de: inc.point,
        vers: r.ou, point_vers: r.point, prevu: prevu || null,
        incident_id: inc.id,
        nom: inc.nom, certitude: prevu ? "rumeur" : (r.certitude || inc.certitude),
        feu: inc.feu || "vif",
        detail: r.note || r.detail, statut: "actif",
      });
    };
    relais.forEach((r, i) => poser(r, i, false));
    craints.forEach((r, i) => poser(r, i, true));
    return { jetons, traits };
  }

  // Ne garder qu'une affaire et tout ce qui la compose : un pli et la route
  // qu'il a prise, un incident et toute sa famille. Le reste de la table
  // disparaît — c'est le seul moyen de regarder UNE chose sur une carte qui en
  // porte quarante, et ça ne coûte rien puisqu'on la rend d'un clic.
  function isoler(m, id) {
    if (!id) return m;
    const sien = (x) => x.id === id || x.incident_id === id || x.pli_id === id;
    return { jetons: (m.jetons || []).filter(sien),
             traits: (m.traits || []).filter(sien), zones: [] };
  }

  // Rend des marques prêtes à dessiner : les incidents remplacés par ce qu'ils
  // impliquent, tout le reste inchangé.
  function deplier(m) {
    const jetons = [], traits = (m.traits || []).slice();
    (m.jetons || []).forEach((j) => {
      if (j.genre !== "incident") return jetons.push(j);
      const d = deplierUn(j);
      jetons.push(...d.jetons);
      traits.push(...d.traits);
    });
    return { jetons, traits, zones: m.zones || [] };
  }

  // ---- le plan : ce qui n'a pas encore eu lieu -----------------------------
  // Tout ce qu'on a posé jusqu'ici décrit ce qui EST (ou ce qu'on croit qui
  // est). Le plan décrit ce qu'on VEUT — et c'est l'autre moitié d'une table de
  // guerre : un conseil ne se tient pas pour constater, il se tient pour
  // décider qui fait quoi et avant quand. Chaque dessein a donc un geste, un
  // homme dessus (`par`) et une échéance (`echeance`) : ce qui n'atterrit sur
  // personne n'a pas été décidé.
  const GESTES = {
    // un donjon dans un anneau qui se referme
    assieger: '<path d="M-2.2 3.2V-1.4H-1.2V-2.4H-0.4V-1.4H0.4V-2.4H1.2V-1.4H2.2V3.2Z"/>' +
      '<circle r="4.5" stroke-dasharray="1.5 1.4"/>',
    // une pointe qui entre dans un mur
    prendre: '<path d="M2.8-3.6V3.6"/><path d="M-4.4 0H1.6"/><path d="M0-1.7 1.7 0 0 1.7"/>',
    // un écu : ce qu'on garde
    tenir: '<path d="M0-4 3.6-2.6V0.6Q3.6 3 0 4.4Q-3.6 3-3.6 0.6V-2.6Z"/>',
    // une course coupée net avant son but
    intercepter: '<path d="M-4.4 0H2.2"/><path d="M0.6-1.7 2.3 0 0.6 1.7"/>' +
      '<path d="M-1.2-3.4V3.4"/>',
    // les ailes, et ce qui tombe dessous
    frapper: '<path d="M-4.6-2.6C-2.8-3.9-1.4-2.9 0-0.7 1.4-2.9 2.8-3.9 4.6-2.6"/>' +
      '<path d="M0 0.4V4.2"/><path d="M-1.7 2.5 0 4.4 1.7 2.5"/>',
    // la flamme qu'on met soi-même
    bruler: '<path d="M0 4.2Q-3.4 2.6-3.4 0Q-3.4-2.6-1.1-4.6Q-1.5-1.9 0.5-2.8' +
      'Q-0.3-0.5 1.7-1.6Q3.4-0.3 3.4 0.7Q3.4 2.8 0 4.2Z"/>',
    // deux rives et la chaîne entre elles
    bloquer: '<path d="M-4-3.4V3.4"/><path d="M4-3.4V3.4"/>' +
      '<path d="M-4 0H4" stroke-dasharray="1.3 1.1"/>',
    // des piques qu'on dresse
    lever: '<path d="M-4 3.4H4"/><path d="M-2.4 3.4V-0.6"/><path d="M2.4 3.4V-0.6"/>' +
      '<path d="M0 3.4V-3.6"/><path d="M-1.7-2 0-3.9 1.7-2"/>',
    // le sac qui arrive
    ravitailler: '<path d="M-0.8 3.4V0.6Q1.6-1.8 3.4 0.6V3.4Z"/><path d="M-4.4-1H-1"/>' +
      '<path d="M-2.4-2.4-1-1-2.4 0.4"/>',
    // le mur, et ce qui en sort
    evacuer: '<path d="M-2.8-3.6V3.6"/><path d="M-1.6 0H4.2"/><path d="M2.6-1.7 4.3 0 2.6 1.7"/>',
    // un œil ouvert : on ne fait rien, on regarde
    guetter: '<path d="M-4.4 0Q0-3.4 4.4 0Q0 3.4-4.4 0Z"/><circle r="1.2"/>',
    // deux bouches qui se font face
    parler: '<path d="M-3.4-2.6Q-0.8 0-3.4 2.6"/><path d="M3.4-2.6Q0.8 0 3.4 2.6"/>' +
      '<path d="M0-1.4V1.4"/>',
  };
  const NOM_GESTE = {
    assieger: "Assiéger", prendre: "Prendre", tenir: "Tenir",
    intercepter: "Intercepter", frapper: "Frapper au dragon", bruler: "Brûler",
    bloquer: "Bloquer", lever: "Lever des hommes", ravitailler: "Ravitailler",
    evacuer: "Évacuer", guetter: "Guetter", parler: "Parler",
  };

  // Par quoi la chose est passée. Un mot porté par un prince sur un dragon n'a
  // ni le même poids ni le même démenti possible qu'un feuillet scellé.
  const CANAUX = {
    lettre: "par lettre", corbeau: "par corbeau", homme: "par un homme",
    dragon: "porté par un dragon", oral: "de vive voix", cri: "crié",
  };

  // ---- les filtres de la table ---------------------------------------------
  // Une table qui porte tout à la fois ne se lit plus. Quatre familles, qu'on
  // allume et qu'on éteint : les armes, les plis, les liens, les gens. Un genre
  // inconnu tombe dans les armes — c'était toute la table avant les filtres.
  const FILTRES = [
    { id: "militaire",     nom: "Les armes" },
    // Un dragon n'est pas une pièce parmi les autres : c'est ce qui décide
    // seul de la journée. Il a sa famille, qu'on garde allumée quand on éteint
    // tout le reste pour ne regarder QUE ça.
    { id: "dragons",       nom: "Les dragons" },
    { id: "communication", nom: "Les plis" },
    // Le plan ne décrit pas le monde, il décrit ce qu'on veut lui faire. Il a
    // donc sa famille : on l'allume pour préparer, on l'éteint pour regarder ce
    // qui EST — et ne jamais confondre les deux est tout l'intérêt.
    { id: "plan",          nom: "Le plan" },
    { id: "liens",         nom: "Les liens" },
    // « Les têtes », pas « les gens » : le décor a déjà une échelle de ce nom,
    // et deux boutons qui se disent pareil ne montrent jamais la même chose.
    { id: "gens",          nom: "Les têtes" },
    // Une oreille n'est pas un pli : un pli arrive une fois et c'est fini,
    // une oreille est permanente et toute sa valeur est sa fraîcheur. Sa
    // famille à elle, donc — on l'allume pour se demander ce qu'on saurait
    // d'un endroit, et le trou qu'on y voit est la réponse.
    { id: "oreilles",      nom: "Les oreilles" },
  ];
  const FILTRE_JETON = {
    armee: "militaire", cavalerie: "militaire", flotte: "militaire",
    dragon: "dragons", garnison: "militaire", siege: "militaire",
    bataille: "militaire", camp: "militaire", vivres: "militaire",
    pli: "communication", incident: "communication", tete: "gens",
    dessein: "plan", oreille: "oreilles",
  };
  const FILTRE_TRAIT = {
    marche: "militaire", mer: "militaire", attaque: "militaire",
    retraite: "militaire", menace: "militaire", vol: "dragons",
    corbeau: "communication", cavalier: "communication",
    propagation: "communication",
    serment: "liens", vassal: "liens", mariage: "liens", querelle: "liens",
  };
  // Tout ce qui porte `plan: true` tombe dans le plan, quel que soit son genre :
  // une marche projetée reste une marche, mais elle n'a rien à faire au milieu
  // des marches réelles quand on regarde la carte de ce qui EST.
  const filtreDe = (m, table, defaut) =>
    m.filtre || (m.plan ? "plan" : null) || table[m.genre || defaut] || "militaire";

  // `actifs` est un Set d'ids de filtres ; absent, tout passe.
  // Le dépliage passe D'ABORD : un incident n'est pas une marque, c'est une
  // famille de marques, et un filtre qui trierait l'objet non déplié laisserait
  // ses relais sur la table sans son foyer.
  function filtrer(m, actifs) {
    const d = deplier(m);
    if (!actifs) return d;
    const ok = (x) => actifs.has(x);
    return {
      jetons: d.jetons.filter((j) => ok(filtreDe(j, FILTRE_JETON, DEFAUT))),
      traits: d.traits.filter((t) => ok(filtreDe(t, FILTRE_TRAIT, "marche"))),
      zones: ok("liens") ? d.zones : [],
    };
  }

  // Un fil tendu a une allure : sa courbure, son pointillé, sa pointe. C'est là
  // que se lit la différence entre un corbeau qui vole et un ost qui marche.
  const TRAITS = {
    marche:   { fleche: "pleine",   courbure: .14, epais: 1.5 },
    mer:      { fleche: "pleine",   courbure: .22, epais: 1.3, tirets: "3.4 2.2" },
    corbeau:  { fleche: "ouverte",  courbure: .34, epais: .9,  tirets: ".9 2.4" },
    // un porteur suit les routes : moins courbé qu'un vol, plus lent à l'œil
    cavalier: { fleche: "ouverte",  courbure: .12, epais: 1.1, tirets: "2 1.8" },
    // une chose qui gagne de proche en proche : un fil maigre et pointillé,
    // qui n'a l'air de rien — c'est justement comme ça que ça se propage
    propagation: { fleche: "ouverte", courbure: .22, epais: .95, tirets: "1.4 2" },
    attaque:  { fleche: "barbelee", courbure: .16, epais: 2.3 },
    // un vol de dragon : la seule chose sur cette table qui ignore le sol —
    // très courbé, franc, et il ne mesure pas ses distances comme les autres
    vol:      { fleche: "pleine",   courbure: .30, epais: 1.6, tirets: "6 2.8" },
    retraite: { fleche: "ouverte",  courbure: .16, epais: 1.3, tirets: "2.6 2.4" },
    menace:   { fleche: "ouverte",  courbure: .18, epais: 1.5, tirets: "3 2" },
    serment:  { courbure: .24, epais: 1.1, marque: "noeud" },
    vassal:   { courbure: .20, epais: .9,  tirets: "4 2" },
    mariage:  { courbure: .24, epais: .9,  tirets: "1.2 1.8", marque: "anneau" },
    querelle: { courbure: .20, epais: 1.1, motif: "zigzag" },
  };

  const camp = (m) => "camp-" + (m.camp || "neutre");
  const sur = (m) => "cert-" + (m.certitude || "sure");
  // L'état d'un pli teinte la pièce ET le fil qui l'a portée : un corbeau
  // confirmé et un corbeau perdu ne doivent pas se ressembler sur la table.
  const eta = (m) => (m.etat && ETATS[m.etat] ? " etat-" + m.etat : "") +
    (m.feu && FEUX[m.feu] ? " feu-" + m.feu : "") +
    (m.foyer ? " foyer" : "") + (m.prevu ? " prevu" : "") +
    (m.incident_id && m.incident_id === eveille ? " eveille" : "") +
    (m.plan || m.genre === "dessein" ? " projete" : "") +
    (m.quoi ? " geste-" + m.quoi : "");
  // Toute marque née d'un incident porte son id : c'est par lui que le survol
  // réveille la famille entière, foyer compris.
  const dInc = (m) => (m.incident_id ? ' data-incident="' + esc(m.incident_id) + '"' : "");

  // ---- géométrie -----------------------------------------------------------
  // Une marque se pose sur un lieu (par son id) ou sur un point nu de la carte,
  // pour ce qui n'a pas d'adresse : un ost en rase campagne, une voile au large.
  function position(ou, point) {
    if (Array.isArray(point) && point.length === 2) return point;
    const p = (G.lieux || {})[ou];
    return p ? [p[0], p[1]] : null;
  }
  const posJeton = (j) => position(j.ou, j.point);
  const posDe = (t) => position(t.de, t.point_de);
  const posVers = (t) => position(t.vers, t.point_vers);

  // La boîte englobante de tout ce qui est posé — sert au cadrage automatique
  // quand un conseiller montre un bout de carte et rien d'autre.
  function boite(brutes) {
    const marques = deplier(brutes);   // un incident cadre AUSSI ce qu'il a gagné
    const pts = [];
    (marques.jetons || []).forEach((j) => { const p = posJeton(j); if (p) pts.push(p); });
    (marques.traits || []).forEach((t) => {
      const a = posDe(t), b = posVers(t);
      if (a) pts.push(a);
      if (b) pts.push(b);
      (t.etapes || []).forEach((e) => pts.push(e));
    });
    if (!pts.length) return null;
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    return { x: Math.min(...xs), y: Math.min(...ys),
             l: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  }

  // Bézier quadratique : deux bouts, un point de contrôle jeté de côté. La
  // courbure évite que deux fils entre les mêmes places se recouvrent, et donne
  // à la table sa main humaine — rien n'est tracé à la règle.
  const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  function courbe(a, b, k) {
    const m = lerp(a, b, .5), dx = b[0] - a[0], dy = b[1] - a[1];
    return [m[0] - dy * k, m[1] + dx * k];
  }
  const enT = (a, c, b, t) => {
    const u = 1 - t;
    return [u * u * a[0] + 2 * u * t * c[0] + t * t * b[0],
            u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]];
  };
  // Découpe (de Casteljau) : la part parcourue et la part qui reste.
  function couper(a, c, b, t) {
    const A = lerp(a, c, t), B = lerp(c, b, t), M = lerp(A, B, t);
    return [[a, A, M], [M, B, b]];
  }
  const dQ = (a, c, b) => "M" + a[0].toFixed(1) + " " + a[1].toFixed(1) +
    "Q" + c[0].toFixed(1) + " " + c[1].toFixed(1) +
    " " + b[0].toFixed(1) + " " + b[1].toFixed(1);
  const dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);

  // Une pointe de flèche se dessine à la main : un <marker> demanderait des defs
  // et des ids uniques, or deux cartes coexistent sur la page.
  function pointe(p, dir, style, ech, classe) {
    const n = Math.hypot(dir[0], dir[1]) || 1;
    const u = [dir[0] / n, dir[1] / n], w = [-u[1], u[0]];
    const L = (style === "barbelee" ? 7.5 : 6) * ech, D = 2.7 * ech;
    const q = (a, b) => [(p[0] + u[0] * a + w[0] * b).toFixed(1),
                         (p[1] + u[1] * a + w[1] * b).toFixed(1)];
    if (style === "ouverte") {
      const g = q(-L, D), d = q(-L, -D);
      return '<path class="' + classe + ' pointe-ouverte" d="M' + g[0] + " " + g[1] +
        "L" + p[0].toFixed(1) + " " + p[1].toFixed(1) + "L" + d[0] + " " + d[1] +
        '" stroke-width="' + (1.3 * ech).toFixed(2) + '"/>';
    }
    // pleine, ou barbelée : la même tête, le talon creusé pour la seconde
    const g = q(-L, D), d = q(-L, -D), t = q(style === "barbelee" ? -L * .45 : -L * .8, 0);
    return '<path class="' + classe + ' pointe-pleine" d="M' + p[0].toFixed(1) + " " +
      p[1].toFixed(1) + "L" + g[0] + " " + g[1] + "L" + t[0] + " " + t[1] +
      "L" + d[0] + " " + d[1] + 'Z"/>';
  }

  // Une querelle ne se trace pas droit : on la fait grincer.
  function zigzag(a, c, b, ech) {
    const n = 14, amp = 1.5 * ech;
    let d = "";
    for (let i = 0; i <= n; i++) {
      const t = i / n, p = enT(a, c, b, t);
      const av = enT(a, c, b, Math.min(1, t + .01)), ar = enT(a, c, b, Math.max(0, t - .01));
      const dx = av[0] - ar[0], dy = av[1] - ar[1], m = Math.hypot(dx, dy) || 1;
      const s = (i % 2 ? 1 : -1) * (i === 0 || i === n ? 0 : 1);
      d += (i ? "L" : "M") + (p[0] - dy / m * amp * s).toFixed(1) + " " +
        (p[1] + dx / m * amp * s).toFixed(1);
    }
    return d;
  }

  // ---- les traits ----------------------------------------------------------
  function unTrait(t, ech, neuves) {
    let a = posDe(t), b = posVers(t);
    if (!a || !b) return "";
    const g = TRAITS[t.genre] || TRAITS.marche;
    const k = (typeof t.courbure === "number" ? t.courbure : g.courbure) *
      (t.sens === "gauche" ? -1 : 1);
    let c = courbe(a, b, k);
    if (Array.isArray(t.etapes) && t.etapes.length) c = t.etapes[0];  // une étape impose le pli

    // On recule des deux bouts : un fil qui part du centre d'une place mange son
    // point et son nom.
    const L = dist(a, b) || 1;
    const marge = Math.min(.28, (4.5 * ech) / L);
    if (marge > 0) {
      const c1 = couper(a, c, b, marge);
      a = c1[1][0]; c = c1[1][1];
      const c2 = couper(a, c, b, 1 - marge / (1 - marge));
      a = c2[0][0]; c = c2[0][1]; b = c2[0][2];
    }

    const cl = "trait trait-" + esc(t.genre || "marche") + " " + camp(t) + " " + sur(t) +
      eta(t) + (neuves && neuves.has(t.id) ? " neuve" : "");
    const ep = (t.epais || g.epais || 1.4) * ech;
    const tir = g.tirets ? ' stroke-dasharray="' +
      g.tirets.split(" ").map((v) => (parseFloat(v) * ech).toFixed(2)).join(" ") + '"' : "";
    const titre = "<title>" + esc((t.nom ? t.nom + " — " : "") +
      (NOM_TRAIT[t.genre] || "") +
      (ETATS[t.etat] ? " · " + ETATS[t.etat].nom : "")) +
      (t.detail ? " · " + esc(t.detail) : "") +
      (t.certitude && t.certitude !== "sure" ? " (" + esc(t.certitude) + ")" : "") + "</title>";

    let s = '<g class="' + cl + '" data-id="' + esc(t.id || "") + '" data-nom="' +
      esc(t.nom || NOM_TRAIT[t.genre] || "") + '"' + dInc(t) + ">" + titre;

    if (g.motif === "zigzag") {
      s += '<path class="fil" d="' + zigzag(a, c, b, ech) + '" stroke-width="' + ep.toFixed(2) + '"/>';
    } else if (typeof t.avancement === "number" && g.fleche) {
      // Une colonne en route : ce qui est fait est plein, ce qui reste est en
      // pointillé, et la pièce fantôme dit où elle en est.
      const q = Math.max(.02, Math.min(.98, t.avancement));
      const [g1, g2] = couper(a, c, b, q);
      s += '<path class="fil" d="' + dQ(g1[0], g1[1], g1[2]) + '" stroke-width="' + ep.toFixed(2) + '"/>' +
        '<path class="fil fil-reste" d="' + dQ(g2[0], g2[1], g2[2]) + '" stroke-width="' +
        (ep * .8).toFixed(2) + '" stroke-dasharray="' + (2.4 * ech).toFixed(2) + " " +
        (2.2 * ech).toFixed(2) + '"/>';
    } else {
      s += '<path class="fil" d="' + dQ(a, c, b) + '" stroke-width="' + ep.toFixed(2) + '"' + tir + "/>";
    }

    if (g.fleche) s += pointe(b, [b[0] - c[0], b[1] - c[1]], g.fleche, ech, "fil-pointe");
    if (g.marque === "anneau" || g.marque === "noeud") {
      const m = enT(a, c, b, .5);
      s += '<circle class="fil-marque' + (g.marque === "noeud" ? " plein" : "") +
        '" cx="' + m[0].toFixed(1) + '" cy="' + m[1].toFixed(1) + '" r="' +
        (1.9 * ech).toFixed(2) + '" stroke-width="' + (1 * ech).toFixed(2) + '"/>';
    }
    return s + "</g>";
  }

  function traits(liste, ech, neuves) {
    return (liste || []).map((t) => unTrait(t, ech, neuves)).join("");
  }

  // ---- les jetons ----------------------------------------------------------
  const chiffre = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

  const DEC = [0, -10];              // au-dessus du point, pour ne pas le manger
  const DEC_BAS = [0, 11];           // dessous, pour ce qui n'est pas une force
  const TAILLE = 1.15;               // la pièce pèse un peu plus qu'un point de lieu
  const ETAGE = 19;                  // de quoi empiler deux pièces sans manger leurs chiffres
  // Une tête n'est pas une force : elle pèse moins, elle se range SOUS la place
  // (les osts montent, les gens descendent) et elle porte son nom en clair —
  // trois noms sur une place, c'est lisible ; un ost sans son chiffre, non.
  const TAILLE_TETE = .78, ETAGE_TETE = 12.5;
  // Un pli se range comme une tête, sous la place, et porte son nom en clair —
  // un message dont on ne lit pas l'objet ne sert à rien. Mais il est GROS :
  // sur cette table, ce qu'on a écrit pèse autant qu'un ost, et la marque
  // d'état doit se lire à la vignette sans qu'on ait à s'approcher.
  const TAILLE_PLI = 1.45, ETAGE_PLI = 23;
  // Ce qui n'est pas une force descend SOUS la place : les osts montent, les
  // gens, les plis et les oreilles descendent, et personne ne mange le nom du
  // lieu. Une seule table, pour que les trois rangs se cumulent proprement.
  const DESSOUS = { tete: true, pli: true, oreille: true };
  const JOURS_DIT = (n) => n <= 0 ? "aujourd'hui" : n === 1 ? "hier"
    : "il y a " + n + " jours";

  function unJeton(j, ech, opts, d, decal) {
    const p = posJeton(j);
    if (!p) return "";
    const x = p[0] + d[0] * ech, y = p[1] + (d[1] - decal) * ech;
    // Un dessein prend son glyphe de ce qu'on veut FAIRE, pas de ce qu'il est.
    const dessein = j.genre === "dessein";
    const gl = dessein ? (GESTES[j.quoi] || GESTES.tenir)
      : (GLYPHES[j.genre] || GLYPHES[DEFAUT]);
    const flou = j.certitude && j.certitude !== "sure";
    // Une oreille se range et se dessine comme une tête : ce n'est pas une
    // force, ça porte un nom, et ça pâlit avec les jours.
    const tete = j.genre === "tete" || j.genre === "oreille";
    const pli = j.genre === "pli";
    const et = ETATS[j.etat];
    const cl = "jeton jeton-" + esc(j.genre || DEFAUT) + " " + camp(j) + " " + sur(j) +
      eta(j) + (opts.neuves && opts.neuves.has(j.id) ? " neuve" : "");

    const detail = [j.nom,
      dessein ? (NOM_GESTE[j.quoi] || NOM_GENRE.dessein)
        : j.genre === "tete" ? "" : (NOM_GENRE[j.genre] || ""),
      // Ce qu'une oreille donne, et ce qu'elle coûte. Une oreille qu'on ne
      // paie pas est une oreille qu'on n'a pas — et le prix se lit ici.
      j.donne ? "elle donne : " + j.donne : "",
      j.prix ? "elle coûte : " + j.prix : "",
      // Ce qui n'atterrit sur personne n'a pas été décidé : l'homme et
      // l'échéance passent AVANT le reste dans ce que la pièce raconte.
      j.par ? "sur " + j.par : "",
      j.dans != null ? (j.dans <= 0 ? "échu" : j.dans === 1 ? "demain"
        : "dans " + j.dans + " jours") : "",
      // Par quoi c'est passé : une lettre, un homme, un dragon, une bouche. Ce
      // n'est pas un détail — un mot porté par un prince sur un dragon n'a ni
      // le même poids, ni le même démenti possible, qu'un feuillet scellé.
      CANAUX[j.canal] || "",
      et ? et.nom : "",
      // « on pense », pas « on craint » : la table sert aussi à suivre ce qu'on
      // VEUT voir se répandre, et un sacre qui gagne une place n'est pas un mal.
      j.prevu ? "on pense qu'il y gagnera" : "",
      FEUX[j.feu] && !j.prevu ? FEUX[j.feu].nom : "",
      j.ames != null ? (j.prevu ? "environ " : "quelque ") + chiffre(j.ames) +
        " âmes" + (j.prevu ? " y seraient prises" : " touchées") : "",
      j.total ? chiffre(j.total) + " âmes en tout" : "",
      // La vitesse ne se raconte pas, elle se divise : c'est le seul chiffre
      // qui dise si la chose court plus vite qu'un cavalier.
      (j.total && j.jours) ?
        "environ " + chiffre(Math.round(j.total / j.jours)) + " par jour" : "",
      j.relais ? "gagné " + j.relais + (j.relais > 1 ? " endroits" : " endroit") : "",
      j.jours != null ? JOURS_DIT(j.jours) : "",
      j.force ? chiffre(j.force) + " " + (j.unite || "hommes") : "",
      j.detail || "", flou ? (j.certitude === "rumeur" ? "on le dit" : "rapporté") : ""]
      .filter(Boolean).join(" — ") +
      // Ce qui a été écrit se lit sous le doigt, en toutes lettres : c'est la
      // seule pièce de la table qui a un CONTENU, et le cacher ferait de la
      // convocation la plus décisive de la partie un rond de plus.
      (j.contenu ? "\n\n« " + j.contenu + " »" : "") +
      (j.reponse ? "\n\nRéponse : « " + j.reponse + " »" : "");

    let s = '<g class="' + cl + '" data-id="' + esc(j.id || "") + '" data-nom="' +
      esc(j.nom || NOM_GENRE[j.genre] || "") + '"' + dInc(j) + ' transform="translate(' +
      x.toFixed(1) + "," + y.toFixed(1) + ") scale(" +
      (ech * (tete ? TAILLE_TETE : pli ? TAILLE_PLI : TAILLE)).toFixed(4) + ')">' +
      "<title>" + esc(detail) + "</title>" +
      '<circle class="jeton-fond" r="5.6"/>' +
      (j.genre === "siege" ? '<circle class="jeton-ceinture" r="6.6"/>' : "") +
      '<g class="jeton-glyphe">' + gl + "</g>";
    if (flou) s += '<text class="jeton-doute" x="6.4" y="1.8">?</text>';
    // La marque d'état se pose au flanc gauche, à l'opposé du doute : les deux
    // se lisent ensemble sans jamais se toucher.
    if (et) s += '<g class="jeton-etat" transform="translate(-6.6,-3.4)">' + et.marque + "</g>";
    // Le chiffre est au-dessus : sous la pièce, il tomberait sur le nom du lieu.
    if (j.force) s += '<text class="jeton-force" y="-7">' + esc(chiffre(j.force)) + "</text>";
    // Un incident ne compte pas des hommes qu'on commande : il compte des âmes
    // qu'on estime. Le tilde est là pour qu'on ne lise jamais ce chiffre comme
    // un effectif — et un foyer porte le TOTAL, pas seulement ce qu'il a pris.
    if (j.ames != null || j.total) s += '<text class="jeton-ames" y="-7">' +
      esc((j.prevu ? "?" : "~") + chiffre(j.total || j.ames)) + "</text>";
    // Un pli compte les JOURS, pas les hommes — et c'est ce compte qui rend un
    // silence lisible : « muet depuis neuf jours » n'est pas « muet depuis hier ».
    // Au-dessus, il tomberait sur le point de la place — un pli est rangé
    // DESSOUS, son « au-dessus » est le nom du lieu. Il va donc au flanc droit,
    // en face de la marque d'état.
    if (j.jours != null) s += '<text class="jeton-jours" x="7.4" y="-2.6">' +
      esc(j.jours <= 0 ? "ce jour" : j.jours + " j") + "</text>";
    // Un dessein ne compte pas les jours écoulés : il compte ceux qui restent.
    if (j.dans != null) s += '<text class="jeton-dans" y="-7.4">' +
      esc(j.dans <= 0 ? "échu" : "J−" + j.dans) + "</text>";
    // Le nom d'une tête est TOUTE l'information : il reste en clair. Celui
    // d'un ost vient sous le doigt — dix pièces nommées feraient une bouillie.
    // Un incident est NOMMÉ : c'est par son nom qu'on le suit d'un endroit à
    // l'autre. Mais seul son foyer l'écrit en clair — quinze relais qui
    // répètent le même nom feraient une bouillie le long de la propagation.
    // Un dessein s'écrit en clair : on ne devine pas ce qu'on a décidé de faire.
    const clair = tete || pli || j.foyer || dessein;
    if (j.nom) s += '<text class="jeton-nom' + (clair ? " toujours" : "") +
      '" y="' + (clair ? "10.6" : "9.8") + '">' + esc(j.nom) + "</text>";
    return s + "</g>";
  }

  // Deux osts sur la même place se marcheraient dessus : on les range en rang
  // d'oignon autour du point d'ancrage. Et une pièce qui tomberait hors du
  // cadrage est simplement absente — comme les noms de lieux : mieux vaut le
  // manque qu'un jeton tranché par le bord. Elle reste sur la grande table.
  function pieces(liste, ech, opts) {
    const o = opts || {};
    const c = o.cadre;
    const tas = {};
    (liste || []).forEach((j) => {
      const p = posJeton(j);
      if (!p) return;
      // Ce qui n'est pas une force se range SOUS la place : les têtes et les
      // plis descendent, les osts montent, et personne ne mange le nom du lieu.
      const d = j.dec || (DESSOUS[j.genre] ? DEC_BAS : DEC);
      if (c) {
        const x = p[0] + d[0] * ech, y = p[1] + d[1] * ech, r = 11 * ech;
        if (x - r < c.x || x + r > c.x + c.l || y - r < c.y || y + r > c.y + c.h) return;
      }
      const k = p[0].toFixed(1) + "/" + p[1].toFixed(1) + "/" + d.join(",");
      (tas[k] = tas[k] || []).push([j, d]);
    });
    let s = "";
    // On empile vers le haut, jamais de côté : deux pièces côte à côte, ce sont
    // leurs chiffres qui se chevauchent, et un compte illisible ne vaut rien.
    Object.keys(tas).forEach((k) => {
      // Les osts s'empilent vers le haut (leurs chiffres se chevaucheraient
      // côte à côte) ; les têtes et les plis descendent sous la place. On
      // CUMULE la hauteur de chacun au lieu de multiplier un pas unique : un
      // pli est trois fois plus haut qu'une tête, et deux rangs à pas fixe se
      // recouvriraient dès qu'ils se mêlent sur la même place.
      let bas = 0, haut = 0;
      tas[k].forEach(([j, d]) => {
        const pli = j.genre === "pli";
        const dessous = DESSOUS[j.genre];
        const pas = pli ? ETAGE_PLI : dessous ? ETAGE_TETE : ETAGE;
        s += unJeton(j, ech, o, d, dessous ? -bas : haut);
        if (dessous) bas += pas; else haut += pas;
      });
    });
    return s;
  }

  // ---- les zones : une région qui a choisi son camp ------------------------
  function zones(liste) {
    const par = {};
    (G.regions || []).forEach((r) => (par[r.id] = r.d));
    return (liste || []).map((z) => par[z.region]
      ? '<path class="zone ' + camp(z) + '" d="' + par[z.region] + '"><title>' +
        esc(z.nom || "") + "</title></path>"
      : "").join("");
  }

  // ---- la légende : seulement ce qui est effectivement posé ----------------
  function legende(marques) {
    const vus = [];
    const voir = (t, id) => { if (vus.indexOf(t + id) === -1) vus.push(t + id); };
    // Un dessein se nomme par son GESTE : « Dessein » douze fois ne dit rien,
    // « Assiéger · Intercepter · Frapper au dragon » dit le plan de la soirée.
    (marques.jetons || []).forEach((j) => j.genre === "dessein"
      ? voir("g:", j.quoi || "tenir") : voir("j:", j.genre || DEFAUT));
    (marques.traits || []).forEach((t) => voir("t:", t.genre || "marche"));
    // Les états de plis posés se nomment aussi : une marque qu'on ne sait pas
    // lire ne dit rien, et c'est toute la valeur du filtre des plis.
    (marques.jetons || []).concat(marques.traits || [])
      .forEach((m) => { if (ETATS[m.etat]) voir("e:", m.etat); });
    if (!vus.length) return "";
    return vus.map((v) => {
      const [t, id] = [v.slice(0, 2), v.slice(2)];
      const nom = t === "j:" ? NOM_GENRE[id] : t === "t:" ? NOM_TRAIT[id]
        : t === "g:" ? NOM_GESTE[id] : ETATS[id] && ETATS[id].nom;
      return '<span class="leg-marque leg-' +
        esc(t === "j:" ? id : t === "t:" ? "t-" + id
          : t === "g:" ? "geste geste-" + id : "etat etat-" + id) + '">' +
        esc(nom || id) + "</span>";
    }).join("");
  }

  // Un clic sur une pièce = un moment de pensée, comme un lieu ou un nom du fil :
  // on soupèse ce qu'on croit savoir. On ne déplace rien du doigt.
  function brancher(racine, apres) {
    racine.querySelectorAll(".jeton, .trait").forEach((g) => {
      g.addEventListener("click", (e) => {
        e.stopPropagation();
        const type = g.classList.contains("jeton") ? "force" : "manoeuvre";
        if (window.Entites && g.dataset.nom) Entites.penser(g.dataset.id || g.dataset.nom, type, g.dataset.nom);
        if (apres) apres();
      });
    });
  }

  return { position, boite, traits, pieces, zones, legende, brancher, filtrer,
           deplier, isoler, eveiller,
           GLYPHES, GESTES, NOM_GENRE, NOM_TRAIT, NOM_GESTE,
           ETATS, FEUX, CANAUX, FILTRES };
})();
