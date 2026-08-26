// contrats.js — LES SIX OBJETS QUE LES CINQ ACTEURS S'ÉCHANGENT.
//
// POURQUOI DES CONTRATS PLUTÔT QUE DES OBJETS LIBRES. Dans un moteur de onze
// mille lignes, un ordre est aujourd'hui tantôt une chaîne, tantôt un objet à
// deux champs, tantôt un état des jambes qu'on relit à l'envers pour deviner ce
// qui avait été demandé. Tant que la forme est libre, aucun module ne peut
// vérifier ce qu'il reçoit, et la faute se découvre trois couches plus bas sous
// la forme d'un `undefined` qui ne dit le nom de personne. Un contrat ne rend
// pas le code plus juste : il rend la faute LOCALE et NOMMÉE.
//
// CE QU'ILS NE FONT PAS. Ils ne décident rien, ne calculent rien, ne connaissent
// ni terrain ni scénario. Un contrat construit, normalise, et dit ce qui cloche.
//
// TROIS GESTES, PAS UN DE PLUS.
//   Contrats.ordre({...})            construit et normalise ;
//   Contrats.valider("ordre", o)     rend { ok, fautes:[…] }, ne lève jamais ;
//   Contrats.exiger("ordre", o)      lève en mode strict, trace sinon.
//
// LE MODE STRICT EST CELUI DES BANCS ET DU DÉVELOPPEMENT, jamais celui d'une
// partie qui tourne : une bataille ne doit pas s'arrêter parce qu'un champ
// facultatif est arrivé vide. En partie, `exiger` note la faute dans les traces
// et laisse passer — le défaut se lit alors dans le journal de décision plutôt
// qu'en pleine face du joueur.
//
// LA VERSION EST SUR CHAQUE OBJET, et c'est ce qui permettra de lire une marque
// exportée d'une version antérieure sans deviner sa forme.
"use strict";

(function (racine, fabrique) {
  const api = fabrique(racine);
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleContrats = api;
})(typeof window !== "undefined" ? window : globalThis, function (racine) {

  const VERSION = 1;

  // Le mode strict s'allume tout seul sous Node (four et bancs) et reste
  // éteint dans un navigateur, sauf `?contrats=strict` — on veut pouvoir
  // durcir une page de scène sans toucher au code.
  let STRICT = (typeof window === "undefined");
  try {
    if (typeof window !== "undefined" && window.location &&
        /(^|[?&])contrats=strict/.test(window.location.search)) STRICT = true;
  } catch (_) { /* une page sans location n'est pas une faute */ }

  const fautes = [];                       // ce qui a été laissé passer

  const estNombre = (x) => typeof x === "number" && Number.isFinite(x);
  const estTexte  = (x) => typeof x === "string" && x.length > 0;
  const estListe  = (x) => Array.isArray(x);
  const dans      = (x, liste) => liste.indexOf(x) >= 0;

  // -------------------------------------------------------------------------
  // LES VOCABULAIRES FERMÉS
  //
  // Ils sont courts, et c'est une décision : la précision vient des compléments,
  // pas du nombre de verbes. Sept genres de geste couvrent tout ce qu'un corps
  // peut vouloir ; trois objectifs couvrent tout ce qu'une mission peut demander.
  // -------------------------------------------------------------------------
  const OBJECTIFS = ["detruire", "controler", "empecher"];
  const STATUT_ORDRE = ["emis", "porte", "recu", "remplace", "perime", "impossible"];
  const STATUT_MESSAGE = ["a_porter", "en_route", "cherche", "livre", "perdu", "impossible"];
  const STATUT_MISSION = ["active", "accomplie", "impossible", "remplacee"];
  const GESTES = ["marcher", "tourner", "attendre", "frapper", "parer", "pousser", "ceder"];
  const SOURCES_FAIT = ["vu", "entendu", "touche", "rapporte", "deduit"];
  const ECHELONS = ["combattant", "unite", "commandant", "general"];

  let compteur = 0;
  /** Un identifiant lisible et déterministe DANS une session : pas d'horloge. */
  function nomme(prefixe) { return prefixe + "-" + (++compteur); }

  // -------------------------------------------------------------------------
  // OBJECTIF — le complément commun des ordres et des missions
  // -------------------------------------------------------------------------
  function objectif(o) {
    if (!o) return null;
    return { type: o.type || null, cible: o.cible == null ? null : o.cible };
  }
  function validerObjectif(o, ou, f) {
    if (!o) { f.push(ou + " : objectif absent"); return; }
    if (!dans(o.type, OBJECTIFS))
      f.push(ou + ".type " + String(o.type) + " hors de [" + OBJECTIFS.join(", ") + "]");
    if (o.cible == null) f.push(ou + ".cible absente");
  }

  // -------------------------------------------------------------------------
  // ORDRE — un résultat et des contraintes, JAMAIS une liste de coordonnées.
  //
  // C'est l'interdit central du refactor : dès qu'un ordre porte des points
  // individuels, ce n'est plus un ordre, c'est une télécommande, et l'unité qui
  // le reçoit n'a plus rien à décider. Le validateur le refuse explicitement.
  // -------------------------------------------------------------------------
  function ordre(o) {
    o = o || {};
    return {
      version: VERSION,
      id: o.id || nomme("ordre"),
      auteurId: o.auteurId == null ? null : o.auteurId,
      destinataireIds: estListe(o.destinataireIds) ? o.destinataireIds.slice()
                     : (o.destinataireIds == null ? [] : [o.destinataireIds]),
      donneA: estNombre(o.donneA) ? o.donneA : null,
      recuA: estNombre(o.recuA) ? o.recuA : null,
      texte: o.texte || "",
      objectif: objectif(o.objectif),
      contraintes: estListe(o.contraintes) ? o.contraintes.slice() : [],
      urgence: estNombre(o.urgence) ? o.urgence : 0.5,
      expireA: estNombre(o.expireA) ? o.expireA : null,
      sourceOrdreId: o.sourceOrdreId || null,
      statut: o.statut || "emis",
    };
  }
  function validerOrdre(o) {
    const f = [];
    if (!o || typeof o !== "object") return ["ordre : objet attendu"];
    if (!estTexte(o.id)) f.push("ordre.id absent");
    if (o.auteurId == null) f.push("ordre.auteurId absent");
    if (!estListe(o.destinataireIds) || !o.destinataireIds.length)
      f.push("ordre.destinataireIds vide : un ordre s'adresse a quelqu'un");
    if (!estTexte(o.texte))
      f.push("ordre.texte absent : la bulle affiche la phrase reellement dite");
    validerObjectif(o.objectif, "ordre.objectif", f);
    if (!dans(o.statut, STATUT_ORDRE))
      f.push("ordre.statut " + String(o.statut) + " hors de [" + STATUT_ORDRE.join(", ") + "]");
    if (!estNombre(o.donneA)) f.push("ordre.donneA absent : un ordre a une heure");
    if (o.contraintes && !estListe(o.contraintes)) f.push("ordre.contraintes : liste attendue");
    if (aDesCoordonnees(o.contraintes))
      f.push("ordre.contraintes porte des positions individuelles : " +
             "un ordre decrit un resultat, pas une grille");
    return f;
  }
  /** Le refus dur : des couples x/y par homme cachés dans les contraintes. */
  function aDesCoordonnees(liste) {
    if (!estListe(liste)) return false;
    return liste.some((c) => c && typeof c === "object" &&
      (estListe(c.places) || estListe(c.points) ||
       (estNombre(c.x) && estNombre(c.y) && c.genre !== "zone" && c.genre !== "axe")));
  }

  // -------------------------------------------------------------------------
  // MESSAGE — le porteur cherche une IDENTITÉ MOBILE, pas une coordonnée.
  //
  // `dernierePositionConnue` a le droit d'être fausse : c'est ce que le porteur
  // croyait en partant. S'il ne trouve personne, il demande, cherche un signe
  // ou revient — mais il ne livre pas à un point du sol.
  // -------------------------------------------------------------------------
  function message(m) {
    m = m || {};
    return {
      version: VERSION,
      id: m.id || nomme("msg"),
      ordreId: m.ordreId || null,
      emetteurId: m.emetteurId == null ? null : m.emetteurId,
      destinataireId: m.destinataireId == null ? null : m.destinataireId,
      porteurId: m.porteurId == null ? null : m.porteurId,
      emisA: estNombre(m.emisA) ? m.emisA : null,
      livreA: estNombre(m.livreA) ? m.livreA : null,
      dernierePositionConnue: m.dernierePositionConnue || null,
      contenu: m.contenu == null ? null : m.contenu,
      alterations: estListe(m.alterations) ? m.alterations.slice() : [],
      statut: m.statut || "a_porter",
    };
  }
  function validerMessage(m) {
    const f = [];
    if (!m || typeof m !== "object") return ["message : objet attendu"];
    if (!estTexte(m.id)) f.push("message.id absent");
    if (m.emetteurId == null) f.push("message.emetteurId absent");
    if (m.destinataireId == null)
      f.push("message.destinataireId absent : on porte a quelqu'un, pas a un point");
    if (!dans(m.statut, STATUT_MESSAGE))
      f.push("message.statut " + String(m.statut) + " hors de [" + STATUT_MESSAGE.join(", ") + "]");
    if (!estNombre(m.emisA)) f.push("message.emisA absent");
    if (m.contenu == null && !m.ordreId)
      f.push("message sans contenu ni ordreId : il ne porte rien");
    if (m.statut === "livre" && !estNombre(m.livreA))
      f.push("message livre sans livreA : le delai de transmission est une mesure");
    return f;
  }

  // -------------------------------------------------------------------------
  // FAIT — ce qui a été vu, entendu, touché ou rapporté. JAMAIS une vérité.
  //
  // `forceMin`/`forceMax` disent l'intervalle : un homme qui voit une colonne
  // n'en connaît pas le compte. Un fait sans intervalle est une omniscience
  // déguisée, et c'est le premier endroit où le brouillard se trahit.
  // -------------------------------------------------------------------------
  function fait(x) {
    x = x || {};
    return {
      version: VERSION,
      id: x.id || nomme("fait"),
      genre: x.genre || null,
      auteurId: x.auteurId == null ? null : x.auteurId,
      sujet: x.sujet || null,
      position: x.position || null,
      zone: x.zone || null,
      observeA: estNombre(x.observeA) ? x.observeA : null,
      source: x.source || "vu",
      apprisDe: x.apprisDe == null ? null : x.apprisDe,
      confiance: estNombre(x.confiance) ? x.confiance : 1,
      forceMin: estNombre(x.forceMin) ? x.forceMin : null,
      forceMax: estNombre(x.forceMax) ? x.forceMax : null,
      signatures: estListe(x.signatures) ? x.signatures.slice() : [],
      texte: x.texte || "",
    };
  }
  function validerFait(x) {
    const f = [];
    if (!x || typeof x !== "object") return ["fait : objet attendu"];
    if (!estTexte(x.id)) f.push("fait.id absent");
    if (!estTexte(x.genre)) f.push("fait.genre absent");
    if (x.auteurId == null) f.push("fait.auteurId absent : un fait a un temoin");
    if (!estNombre(x.observeA)) f.push("fait.observeA absent : un fait a une heure");
    if (!dans(x.source, SOURCES_FAIT))
      f.push("fait.source " + String(x.source) + " hors de [" + SOURCES_FAIT.join(", ") + "]");
    if (x.source === "rapporte" && x.apprisDe == null)
      f.push("fait rapporte sans apprisDe : on ne sait plus qui l'a dit");
    if (!estNombre(x.confiance) || x.confiance < 0 || x.confiance > 1)
      f.push("fait.confiance hors de [0, 1]");
    if (!x.position && !x.zone && !x.sujet)
      f.push("fait sans position, zone ni sujet : il ne porte sur rien");
    if (estNombre(x.forceMin) !== estNombre(x.forceMax))
      f.push("fait : forceMin et forceMax vont par paire");
    if (estNombre(x.forceMin) && x.forceMin > x.forceMax)
      f.push("fait : forceMin au-dessus de forceMax");
    return f;
  }

  // -------------------------------------------------------------------------
  // MISSION — ce que le général demande. Elle ne dit jamais COMMENT.
  //
  // `conditionsAbandon` est le champ qu'on oublie et qui coûte le plus cher :
  // sans lui, une mission devenue impossible reste active pour toujours et le
  // commandant tourne en rond devant un mur.
  // -------------------------------------------------------------------------
  function mission(m) {
    m = m || {};
    return {
      version: VERSION,
      id: m.id || nomme("mission"),
      auteurId: m.auteurId == null ? null : m.auteurId,
      executantId: m.executantId == null ? null : m.executantId,
      objectif: objectif(m.objectif),
      conditionsSucces: estListe(m.conditionsSucces) ? m.conditionsSucces.slice() : [],
      conditionsAbandon: estListe(m.conditionsAbandon) ? m.conditionsAbandon.slice() : [],
      contraintes: estListe(m.contraintes) ? m.contraintes.slice() : [],
      priorite: estNombre(m.priorite) ? m.priorite : 0.5,
      creeeA: estNombre(m.creeeA) ? m.creeeA : null,
      reviseeA: estNombre(m.reviseeA) ? m.reviseeA : null,
      statut: m.statut || "active",
    };
  }
  function validerMission(m) {
    const f = [];
    if (!m || typeof m !== "object") return ["mission : objet attendu"];
    if (!estTexte(m.id)) f.push("mission.id absent");
    if (m.auteurId == null) f.push("mission.auteurId absent");
    if (m.executantId == null) f.push("mission.executantId absent");
    validerObjectif(m.objectif, "mission.objectif", f);
    if (!dans(m.statut, STATUT_MISSION))
      f.push("mission.statut " + String(m.statut) + " hors de [" + STATUT_MISSION.join(", ") + "]");
    if (!estNombre(m.creeeA)) f.push("mission.creeeA absent");
    if (!m.conditionsSucces.length)
      f.push("mission sans conditionsSucces : rien ne dira qu'elle est finie");
    if (!m.conditionsAbandon.length)
      f.push("mission sans conditionsAbandon : rien ne dira qu'elle est devenue impossible");
    return f;
  }

  // -------------------------------------------------------------------------
  // INTENTION DE GESTE — l'UNIQUE sortie d'un combattant vers le monde.
  //
  // Le monde décide de ce qui arrive ; le combattant ne décide que de ce qu'il
  // ESSAIE. `raison` n'est pas un ornement : c'est ce que la bulle « j'essaie de
  // X parce que Y » affiche au survol, et l'on refuse une intention sans elle.
  // -------------------------------------------------------------------------
  function intentionGeste(g) {
    g = g || {};
    return {
      version: VERSION,
      acteurId: g.acteurId == null ? null : g.acteurId,
      genre: g.genre || null,
      direction: g.direction || null,
      cibleId: g.cibleId == null ? null : g.cibleId,
      allure: estNombre(g.allure) ? g.allure : 0,
      urgence: estNombre(g.urgence) ? g.urgence : 0.5,
      contraintes: estListe(g.contraintes) ? g.contraintes.slice() : [],
      raison: g.raison || "",
      produitA: estNombre(g.produitA) ? g.produitA : null,
      valideJusqua: estNombre(g.valideJusqua) ? g.valideJusqua : null,
    };
  }
  function validerIntentionGeste(g) {
    const f = [];
    if (!g || typeof g !== "object") return ["geste : objet attendu"];
    if (g.acteurId == null) f.push("geste.acteurId absent");
    if (!dans(g.genre, GESTES))
      f.push("geste.genre " + String(g.genre) + " hors de [" + GESTES.join(", ") + "]");
    if (!estTexte(g.raison))
      f.push("geste.raison absente : j'essaie de X parce que Y n'aurait rien a dire");
    if (!estNombre(g.produitA)) f.push("geste.produitA absent");
    if (g.genre === "marcher" && !g.direction)
      f.push("geste marcher sans direction");
    if ((g.genre === "frapper" || g.genre === "pousser") && g.cibleId == null)
      f.push("geste " + g.genre + " sans cibleId");
    if (estNombre(g.allure) && (g.allure < 0 || g.allure > 1))
      f.push("geste.allure hors de [0, 1] : c'est une part de la vitesse possible");
    return f;
  }

  // -------------------------------------------------------------------------
  // TRACE DE DÉCISION — l'autorité de la bulle de pensée et de l'export.
  //
  // Une capture à 115 s doit répondre sans rejouer : que croyait-il, quelles
  // options a-t-il envisagées, pourquoi celle-ci, et quand devait-il réexaminer.
  // Les quatre questions sont les quatre champs qu'on refuse de laisser vides.
  // -------------------------------------------------------------------------
  function traceDecision(t) {
    t = t || {};
    return {
      version: VERSION,
      acteurId: t.acteurId == null ? null : t.acteurId,
      echelon: t.echelon || null,
      declencheeA: estNombre(t.declencheeA) ? t.declencheeA : null,
      ordreCourant: t.ordreCourant || null,
      objectifCourant: t.objectifCourant ? objectif(t.objectifCourant) : null,
      faitsUtilises: estListe(t.faitsUtilises) ? t.faitsUtilises.slice() : [],
      croyancesUtilisees: estListe(t.croyancesUtilisees) ? t.croyancesUtilisees.slice() : [],
      options: estListe(t.options) ? t.options.map(option) : [],
      choix: t.choix == null ? null : t.choix,
      raison: t.raison || "",
      prochainExamenA: estNombre(t.prochainExamenA) ? t.prochainExamenA : null,
    };
  }
  function option(o) {
    o = o || {};
    return {
      action: o.action || null,
      faisable: o.faisable !== false,
      projection: o.projection || null,
      risques: estListe(o.risques) ? o.risques.slice() : [],
      gains: estListe(o.gains) ? o.gains.slice() : [],
      score: estNombre(o.score) ? o.score : null,
      rejets: estListe(o.rejets) ? o.rejets.slice() : [],
    };
  }
  function validerTraceDecision(t) {
    const f = [];
    if (!t || typeof t !== "object") return ["trace : objet attendu"];
    if (t.acteurId == null) f.push("trace.acteurId absent");
    if (!dans(t.echelon, ECHELONS))
      f.push("trace.echelon " + String(t.echelon) + " hors de [" + ECHELONS.join(", ") + "]");
    if (!estNombre(t.declencheeA)) f.push("trace.declencheeA absente");
    if (t.choix == null) f.push("trace.choix absent : une decision a choisi quelque chose");
    if (!estTexte(t.raison)) f.push("trace.raison absente");
    if (!estNombre(t.prochainExamenA))
      f.push("trace.prochainExamenA absent : sans lui, un reexamen manque ne se voit pas");
    if (!estListe(t.options) || !t.options.length)
      f.push("trace sans options : un choix sans alternative n'est pas une decision");
    (t.options || []).forEach((o, i) => {
      if (!o.action) f.push("trace.options[" + i + "].action absente");
      if (!o.faisable && !(o.rejets || []).length)
        f.push("trace.options[" + i + "] infaisable sans motif de rejet");
    });
    return f;
  }

  // -------------------------------------------------------------------------
  // LE GUICHET
  // -------------------------------------------------------------------------
  const FORMES = {
    ordre:   { faire: ordre,          valider: validerOrdre },
    message: { faire: message,        valider: validerMessage },
    fait:    { faire: fait,           valider: validerFait },
    mission: { faire: mission,        valider: validerMission },
    geste:   { faire: intentionGeste, valider: validerIntentionGeste },
    trace:   { faire: traceDecision,  valider: validerTraceDecision },
  };

  function valider(nom, objet) {
    const forme = FORMES[nom];
    if (!forme) return { ok: false, fautes: ["forme inconnue " + String(nom)] };
    const f = forme.valider(objet);
    return { ok: f.length === 0, fautes: f };
  }

  /**
   * `exiger` — la même vérification, mais qui MORD en strict.
   * En partie, elle note et laisse passer : une bataille ne s'arrête pas pour
   * un champ vide, mais le défaut se lit dans le journal.
   */
  function exiger(nom, objet, ou) {
    const v = valider(nom, objet);
    if (v.ok) return objet;
    const ligne = (ou ? ou + " — " : "") + nom + " : " + v.fautes.join(" ; ");
    if (STRICT) throw new Error("contrat rompu · " + ligne);
    fautes.push(ligne);
    const j = racine && racine.BatailleTraces;
    if (j && j.noter) j.noter("contrat", ligne, { forme: nom });
    return objet;
  }

  function strict(x) { if (x !== undefined) STRICT = !!x; return STRICT; }
  function relevesFautes() { return fautes.slice(); }
  function viderFautes() { fautes.length = 0; }

  return {
    VERSION, OBJECTIFS, GESTES, ECHELONS, SOURCES_FAIT,
    STATUT_ORDRE, STATUT_MESSAGE, STATUT_MISSION,
    ordre, message, fait, mission, intentionGeste, traceDecision, objectif, option,
    valider, exiger, strict, fautes: relevesFautes, viderFautes,
  };
});
