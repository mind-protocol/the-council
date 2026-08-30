
// ---- le fil d'un homme, refait de bout en bout ---------------------------
// Ce que Corneille ouvre en touchant un visage sur le plan du château. Deux
// moitiés d'une même vie, que rien ne montrait ensemble jusqu'ici :
//
//   — CE QU'IL A DIT ET FAIT EN SCÈNE. Ses répliques et ses gestes dans
//     `etat/flux.jsonl`, plus les récits du narrateur qui le nomment : sans
//     eux, une réplique tombe sans la salle qui la porte.
//   — CE QU'IL A VÉCU HORS SCÈNE. Chacune de ses activations
//     (`etat/activations/*.json`) : l'appel du narrateur, sa tentative telle
//     qu'il l'a écrite, ce que le monde en a fait, et ce qu'il en a appris.
//
// L'ordre est celui du MONDE, pas celui des fichiers : les items du flux
// portent leur date au complet, les activations la journée du dossier qui les
// a ouvertes. Une activation dont la journée est illisible se pose à la fin,
// dans l'ordre où elle s'est terminée — jamais silencieusement au milieu.
//
// Lecture seule de bout en bout : rien n'entre dans `etat/`, rien n'entre dans
// le flux. Ce fil vit dans le navigateur de la régie et meurt avec sa page.

const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");
const { absolues, dateCourte, jourAbsolu } = require("../dates");
const { DEPOT_ACTIVATIONS, lireJsonSansFaillir, ouQuartier } = require("./activations");
const { qui } = require("../siege");

const JOUR_MINUTES = 1440;

function nomsDesPersonnages() {
  const brut = lireJsonSansFaillir(path.join(RACINE, "etat", "personnages.json"), []);
  const liste = Array.isArray(brut) ? brut : (brut.personnages || []);
  return new Map(liste.map((p) => [p.id, p.nom || p.id]));
}

function journeeDuDossier(message) {
  const m = String(message || "").match(/"date_du_monde"\s*:\s*\{[^}]*\}/);
  if (!m) return null;
  try { return JSON.parse("{" + m[0] + "}").date_du_monde || null; }
  catch (_e) { return null; }
}

function filPersonnage(id) {
  const noms = nomsDesPersonnages();
  const nom = noms.get(id) || id;
  const entrees = [];
  // rang : [minute absolue du monde, désambiguïsateur]. Les activations d'une
  // journée se posent après ce qui s'y est dit — le dossier ne donne que le
  // jour, et prétendre à la minute serait inventer une heure.
  const poser = (rang, second, e) => entrees.push(Object.assign({ _r: rang, _s: second }, e));

  let flux = [];
  try {
    flux = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim())
      .map((l) => { try { return JSON.parse(l); } catch (_e) { return null; } })
      .filter(Boolean);
  } catch (_e) { /* pas de flux : il reste ses activations */ }

  // Le narrateur ne nomme pas les gens par leur id : on le cherche par son nom,
  // et par son prénom seul quand il en a un — c'est ainsi qu'une salle parle.
  // On cherche le nom entier, et chaque morceau assez long pour ne désigner que
  // lui — mais aux BORNES du mot : sans elles, « Sara » attrape Sarnes, et le
  // fil d'une femme se remplit des récits d'une autre maison.
  const appellations = [nom].concat(nom.split(/\s+/).filter((x) => x.length > 3));
  const bornes = appellations.map((a) =>
    new RegExp("(^|[^\\p{L}])" + a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") +
      "($|[^\\p{L}])", "u"));
  const nomme = (t) => bornes.some((re) => re.test(String(t || "")));
  let date = null;
  flux.forEach((it, i) => {
    if (it.date) date = it.date;
    const rang = absolues(date);
    if (rang === null) return;
    const sien = it.locuteur_id === id || it.acteur_id === id;
    if (sien && (it.type === "replique" || it.type === "geste" || it.type === "table")) {
      poser(rang, i, { source: "scene", genre: it.type === "replique" ? "replique" : "geste",
        qui: nom, texte: it.texte || "", date, lieu: it.lieu || "" });
    } else if ((it.type === "recit" || it.type === "breve" || it.type === "marque")
               && nomme(it.texte)) {
      poser(rang, i, { source: "scene", genre: "narrateur", qui: "Le narrateur",
        texte: (it.titre ? it.titre + " — " : "") + (it.texte || ""), date, lieu: it.lieu || "" });
    }
  });

  // Les activations. On les lit toutes : le nom du fichier porte l'acteur, mais
  // c'est le champ `qui` du rapport qui fait foi.
  let fichiers = [];
  try {
    fichiers = fs.readdirSync(DEPOT_ACTIVATIONS)
      .filter((f) => /^\d{8}-.*\.json$/.test(f)).sort();
  } catch (_e) { /* aucune activation journalisée */ }
  let horsRang = 0;
  fichiers.forEach((f) => {
    const rapport = lireJsonSansFaillir(path.join(DEPOT_ACTIVATIONS, f), null);
    if (!rapport || rapport.qui !== id) return;
    const meta = rapport._activation || {};
    const act = rapport.activation || {};
    const jour = journeeDuDossier(meta.message);
    // Le jour du dossier, à sa toute fin : ce qui s'est dit ce jour-là dans la
    // salle vient d'abord, ce qu'il est allé faire ensuite.
    const rang = jour ? absolues(jour) + JOUR_MINUTES - 1 : Infinity;
    const second = jour ? f : (++horsRang);
    const tete = { source: "activation", date: jour || null,
      tache: (act.tache || {}).quoi || "", session: meta.session || "",
      termine_le: meta.cree_le || null, date_incertaine: !jour };
    if (meta.appel_pnj) {
      poser(rang, second, Object.assign({ genre: "appel", qui: "Le narrateur",
        texte: meta.appel_pnj }, tete));
    }
    const t = meta.tentative_pnj;
    if (t && t.quoi) {
      const bas = [];
      if (t.moyens && t.moyens.length) bas.push("Avec : " + t.moyens.join(" ; ") + ".");
      if (t.effet_recherche) bas.push("Pour : " + t.effet_recherche);
      if (t.renonce_si) bas.push("Renonce si : " + t.renonce_si);
      poser(rang, second, Object.assign({ genre: "tentative", qui: nom,
        texte: (t.verbe ? t.verbe.toUpperCase() + " — " : "") + t.quoi,
        detail: bas.join("\n") }, tete));
    }
    (act.activites || []).forEach((a) => {
      const quoi = (a.action || {}).quoi || a.quoi || "";
      if (quoi) {
        poser(rang, second, Object.assign({ genre: "activite", qui: nom,
          texte: ((a.action || {}).verbe ? (a.action.verbe + " — ") : "") + quoi,
          minutes: Math.round(Number((a.temps || {}).duree_s || 0) / 60) }, tete));
      }
      (a.resultats_produits || []).forEach((r) => {
        if (!r.apres) return;
        poser(rang, second, Object.assign({ genre: "resultat", qui: "Ce qu'il en retient",
          texte: String(r.apres), certitude: r.certitude || "" }, tete));
      });
      if (a.blocage) {
        poser(rang, second, Object.assign({ genre: "blocage", qui: "Ce qui l'arrête",
          texte: typeof a.blocage === "string" ? a.blocage : JSON.stringify(a.blocage) }, tete));
      }
    });
    if (act.issue && act.issue !== "avance") {
      poser(rang, second, Object.assign({ genre: "issue", qui: "L'issue",
        texte: String(act.issue) }, tete));
    }
  });

  entrees.sort((a, b) => (a._r - b._r) ||
    (typeof a._s === typeof b._s ? (a._s < b._s ? -1 : a._s > b._s ? 1 : 0) : 0));
  entrees.forEach((e) => { delete e._r; delete e._s; });
  return {
    id, nom, entrees,
    scenes: entrees.filter((e) => e.source === "scene").length,
    activations: new Set(entrees.filter((e) => e.source === "activation")
      .map((e) => e.session)).size,
  };
}

// « Emmène-moi au moment où X est arrivé. » Corneille ne remonte pas dix mille
// lignes à la molette : elle demande, son MJ cherche, et le fil s'ouvre à
// l'endroit dit. Deux gestes distincts, et ils ne se confondent pas :
//
//   — CHERCHER (`/regie/chercher?q=`) rend les endroits du flux où la chose
//     est dite, avec leur date et trois lignes autour. C'est l'outil du MJ :
//     il lit, il tranche lequel des dix-sept est le bon moment, il répond.
//   — EXTRAIRE (`/regie/extrait?de=&a=`) rend la tranche elle-même, telle
//     qu'elle a été jouée. C'est ce que la page repose dans le fil quand le MJ
//     a dit où.
//
// On ne cherche PAS à la place du MJ. « Le moment où Steffon est arrivé » n'est
// pas une chaîne de caractères : c'est un jugement sur ce qui compte, et une
// recherche plein texte rendrait la première occurrence du mot, presque jamais
// la bonne. Le serveur donne les candidats, l'homme choisit.
function chercherDansFlux(q, max) {
  const besoin = String(q || "").trim().toLowerCase();
  if (!besoin) return { q, trouves: [] };
  const mots = besoin.split(/\s+/).filter((m) => m.length > 2);
  let flux = [];
  try {
    flux = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim())
      .map((l) => { try { return JSON.parse(l); } catch (_e) { return null; } });
  } catch (_e) { return { q, trouves: [] }; }
  const trouves = [];
  let date = null, lieu = "";
  flux.forEach((it, i) => {
    if (!it) return;
    if (it.date) date = it.date;
    if (it.lieu) lieu = it.lieu;
    const t = String(it.texte || "").toLowerCase();
    if (!t) return;
    // Tous les mots utiles, dans le même item : un « et » de plus ne doit pas
    // rendre la moitié du fil.
    const score = mots.length ? (mots.every((m) => t.indexOf(m) !== -1) ? mots.length : 0)
                              : (t.indexOf(besoin) !== -1 ? 1 : 0);
    if (!score) return;
    trouves.push({ i, type: it.type, date, lieu,
      qui: it.locuteur_id || it.acteur_id || null,
      extrait: String(it.texte).slice(0, 220) });
  });
  // Les derniers d'abord : on cherche presque toujours quelque chose de récent.
  return { q, total: trouves.length, trouves: trouves.slice(-(max || 12)).reverse() };
}

function extraitDuFlux(de, a) {
  let flux = [];
  try {
    flux = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim())
      .map((l) => { try { return JSON.parse(l); } catch (_e) { return null; } })
      .filter(Boolean);
  } catch (_e) { return { de: 0, a: 0, items: [] }; }
  const debut = Math.max(0, Math.min(de | 0, flux.length));
  const fin = Math.max(debut, Math.min(a | 0, flux.length, debut + 200));
  // Le nom vient avec : la page qui repose une vieille tranche dans le fil n'a
  // pas la galerie de cette scène-là sous la main, et « robert-quince » n'est
  // pas une façon de nommer un homme.
  const noms = nomsDesPersonnages();
  return { de: debut, a: fin, total: flux.length,
    items: flux.slice(debut, fin).map((it, k) => Object.assign({ _i: debut + k,
      _nom: noms.get(it.locuteur_id || it.acteur_id) || null }, it)) };
}

function regie() {
  const lire = (f, defaut) => {
    try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8")); }
    catch (e) { return defaut; }
  };
  const monde = lire("monde.json", {});
  const aujourdhui = jourAbsolu(monde.date) || 0;
  const dans = (d) => { const n = jourAbsolu(d); return n === null ? null : n - aujourdhui; };

  const gens = {};
  (lire("personnages.json", []) || []).forEach((p) => { gens[p.id] = p; });
  const lieux = {};
  (lire("lieux.json", []) || []).forEach((l) => { lieux[l.id] = l; });
  const nom = (id) => (gens[id] && gens[id].nom) || id;
  const ouEst = (id) => {
    const p = gens[id];
    if (!p || !p.lieu_id) return "";
    return (lieux[p.lieu_id] && lieux[p.lieu_id].nom) || p.lieu_id;
  };

  // ---- 1. les têtes -------------------------------------------------------
  const intentions = lire("intentions.json", []) || [];
  const sieges = lire("joueurs.json", null);
  const listeSieges = (sieges && (sieges.sieges || sieges)) || [];
  const occupes = new Set((Array.isArray(listeSieges) ? listeSieges : [])
    .filter((s) => s && s.occupe).map((s) => s.personnage_id));
  const tousSieges = (Array.isArray(listeSieges) ? listeSieges : [])
    .map((s) => s && s.personnage_id).filter(Boolean);

  const tetes = intentions.map((t) => {
    const plan = t.plan || [];
    const encours = plan.filter((e) => e.etat !== "fait" && e.etat !== "abandonne");
    // La prochaine horloge qui tombe : c'est le tri par défaut, parce que
    // c'est la seule question qu'on se pose avant un tick.
    let prochaine = null, prochaineQuoi = "";
    encours.forEach((e) => {
      if (typeof e.jours_restants !== "number") return;
      if (prochaine === null || e.jours_restants < prochaine) {
        prochaine = e.jours_restants; prochaineQuoi = e.quoi || e.id || "";
      }
    });
    const age = dans(t.date_maj);
  return {
      id: t.personnage_id,
      nom: nom(t.personnage_id),
      echelle: ouQuartier(t.personnage_id),
      lieu: ouEst(t.personnage_id) || t.lieu_note || "",
      intention: t.intention || "",
      date_maj: dateCourte(t.date_maj),
      age_maj: age === null ? null : -age,
      etapes: encours.length,
      etapes_total: plan.length,
      // `jours_restants: null` n'est PAS une horloge oubliée : le schéma en
      // fait une posture permanente — tenir la porte de mer, peigner la grève
      // à chaque basse mer, ne pas voir ce qu'on l'a payé pour ne pas voir.
      // Elle n'est jamais « faite » et jamais décomptée, par construction.
      // Ne compter comme sans horloge que l'étape où le champ MANQUE, seul cas
      // où quelqu'un a réellement oublié de la poser. Mesure du 129.4.3 : sur
      // six acteurs signalés « rien ne tombera jamais », cinq étaient des
      // postures correctes et un seul, Maron Sec et son cycle de six jours,
      // était une vraie horloge manquante — l'alerte cachait le seul vrai cas.
      sans_horloge: encours.filter(
        (e) => !("jours_restants" in e) ||
               (e.jours_restants !== null && typeof e.jours_restants !== "number")
      ).length,
      prochaine, prochaine_quoi: prochaineQuoi,
      declencheurs: (t.declencheurs || []).length,
      attitude: t.attitude_joueur || "",
      mandat: t.mandat || null,
      siege: occupes.has(t.personnage_id),
    };
  });
  // PLUS DE PLAFOND D'ACTEURS : ce n'est pas le nombre de têtes qui coûte,
  // c'est où elles sont. Vingt têtes au loin pèsent moins que huit dans la
  // salle, et le quartier se resserre tout seul sur ce que le joueur atteint.
  const BUDGETS = { "quartier": null, "au loin": null };
  const groupes = ["quartier", "au loin"].map((e) => ({
    echelle: e, budget: BUDGETS[e],
    tetes: tetes.filter((t) => t.echelle === e)
      .sort((a, b) => (a.prochaine === null) - (b.prochaine === null)
        || (a.prochaine - b.prochaine) || (b.age_maj - a.age_maj)),
  }));
  const horsEchelle = tetes.filter((t) => !BUDGETS.hasOwnProperty(t.echelle));

  // Les deux fautes symétriques : un siège occupé qui garde une tête (on le
  // joue à sa place), un siège vacant qui n'en a pas (il dort sans qu'on le voie).
  const avecTete = new Set(intentions.map((t) => t.personnage_id));
  const alertes = [];
  tousSieges.forEach((id) => {
    if (occupes.has(id) && avecTete.has(id))
      alertes.push({ gravite: "grave", texte: nom(id) + " : siège OCCUPÉ et pourtant une tête dans intentions.json" });
    if (!occupes.has(id) && !avecTete.has(id))
      alertes.push({ gravite: "grave", texte: nom(id) + " : siège VACANT et aucune tête — il dort pendant qu'on regarde ailleurs" });
  });
  groupes.forEach((g) => {
    if (g.budget && g.tetes.length > g.budget)
      alertes.push({ gravite: "tiede", texte: "échelle « " + g.echelle + " » : " + g.tetes.length + " têtes pour ~" + g.budget });
  });
  tetes.forEach((t) => {
    if (t.age_maj !== null && t.age_maj >= 3 && t.echelle === "quartier")
      alertes.push({ gravite: "tiede", texte: t.nom + " : tête non relue depuis " + t.age_maj + " jours" });
    if (t.etapes && t.sans_horloge === t.etapes)
      alertes.push({ gravite: "tiede", texte: t.nom + " : aucune étape n'a d'horloge — rien ne tombera jamais" });
  });

  // ---- 2. le calendrier ---------------------------------------------------
  const echeances = [];
  (lire("evenements.json", []) || []).forEach((e) => {
    if (e.statut === "resolu" || e.statut === "annule" || e.statut === "devie") return;
    const j = dans(e.date_prevue);
    if (j === null) return;
    echeances.push({
      jours: j, quoi: e.description || e.id, famille: e.type === "canon" ? "canon" : "événement",
      qui: (e.acteurs || []).map(nom).join(", "), importance: e.importance || null,
      lieu: e.lieu_id ? ((lieux[e.lieu_id] && lieux[e.lieu_id].nom) || e.lieu_id) : "",
    });
  });
  intentions.forEach((t) => {
    (t.plan || []).forEach((e) => {
      if (e.etat === "fait" || e.etat === "abandonne") return;
      if (typeof e.jours_restants !== "number") return;
      echeances.push({
        jours: e.jours_restants, quoi: e.quoi || e.id, famille: "étape",
        qui: nom(t.personnage_id), echelle: ouQuartier(t.personnage_id),
        bloque: (e.depend_de || []).length ? "dépend de " + (e.depend_de || []).join(", ") : "",
      });
    });
  });
  (((lire("plis.json", {}) || {}).plis) || []).forEach((p) => {
    if (p.etat === "remis" || p.etat === "confirme" || p.etat === "perdu") return;
    const j = dans(p.attendu_le);
    if (j === null) return;
    echeances.push({
      jours: j, quoi: p.porte || p.id, famille: "pli",
      qui: nom(p.de) + " → " + nom(p.pour), etat: p.etat || "",
      lieu: p.vers ? ((lieux[p.vers] && lieux[p.vers].nom) || p.vers) : "",
    });
  });
  echeances.sort((a, b) => a.jours - b.jours);

  // ---- 3. les mains ---------------------------------------------------
  const mains = (((lire("mains.json", {}) || {}).mains) || []).map((a) => {
    const mesures = (a.mesure || []).map((m) => {
      const par = (m.rythme && typeof m.rythme.par === "number") ? m.rythme.par : 0;
      // Le seuil le plus proche dans le temps, à ce rythme-là. C'est le
      // seul chiffre qui compte : dans combien de jours ça devient une affaire.
      let jours = null, seuilQui = "";
      (a.seuils || []).filter((s) => s.mesure_id === m.id).forEach((s) => {
        if (s.franchi_le || !par) return;
        const ecart = (s.quand === "sous") ? (m.valeur - s.valeur) : (s.valeur - m.valeur);
        const vitesse = (s.quand === "sous") ? -par : par;
        if (vitesse <= 0) return;
        const d = Math.ceil(ecart / vitesse);
        if (d < 0) return;
        if (jours === null || d < jours) { jours = d; seuilQui = s.affaire || s.id; }
      });
      return { id: m.id, quoi: m.quoi, valeur: m.valeur, unite: m.unite || "",
        par, jours_avant_seuil: jours, seuil: seuilQui };
    });
    return {
      id: a.id, quoi: a.quoi,
      porteur: a.porteur ? (a.porteur.type === "lieu"
        ? ((lieux[a.porteur.id] && lieux[a.porteur.id].nom) || a.porteur.id)
        : nom(a.porteur.id)) : "— personne",
      sans_porteur: !a.porteur || a.porteur.type === "lieu",
      mandat: a.mandat || null,
      dernier_rapport: a.dernier_rapport ? dateCourte(a.dernier_rapport) : null,
      // Le brouillard s'applique au RAPPORT, pas au calcul : ce qui compte
      // n'est pas la mesure mais depuis quand personne ne l'a dite au joueur.
      rapport_age: a.dernier_rapport ? (() => {
        const j = dans(a.dernier_rapport && a.dernier_rapport.date
          ? a.dernier_rapport.date : a.dernier_rapport);
        return j === null ? null : -j;
      })() : null,
      rapport_a: (a.dernier_rapport && a.dernier_rapport.a) ? nom(a.dernier_rapport.a) : "",
      date_maj: dateCourte(a.date_maj),
      mesures,
      franchis: (a.seuils || []).filter((s) => s.franchi_le)
        .map((s) => ({ affaire: s.affaire || s.id, promeut: s.promeut || "", le: dateCourte(s.franchi_le) })),
    };
  });
  mains.forEach((a) => a.mesures.forEach((m) => {
    if (m.jours_avant_seuil !== null && m.jours_avant_seuil <= 10)
      alertes.push({ gravite: "tiede", texte: a.id + " : seuil atteint dans " + m.jours_avant_seuil + " jours (" + m.quoi + ")" });
  }));

  // LE TISSU — calcule en Python par `tisser.py` + `evaluer.py --json`.
  // La regie ne recalcule rien : elle relit et elle dit l'AGE. Un graphe de
  // la veille affiche comme l'etat du jour serait le meme mensonge que le
  // cache d'une minute que cette page refuse deja.
  let tissu = null;
  try {
    const pt = path.join(RACINE, "etat", "tissu", "evaluation.json");
    tissu = JSON.parse(fs.readFileSync(pt, "utf-8"));
    tissu.calcule_il_y_a_s = Math.round((Date.now() - fs.statSync(pt).mtimeMs) / 1000);
  } catch (e) { tissu = null; }

  // Le graphe complet servi a la regie. Le projecteur Python reste l'unique
  // definition des liens ; le serveur ne fait qu'ajouter les mesures de
  // l'evaluation sur les noeuds et des aretes fantomes pour les candidats.
  let graphe = null;
  try {
    const base = path.join(RACINE, "etat", "tissu");
    const brutNoeuds = JSON.parse(fs.readFileSync(path.join(base, "noeuds.json"), "utf-8"));
    const aretes = fs.readFileSync(path.join(base, "aretes.jsonl"), "utf-8")
      .split(/\r?\n/).filter(Boolean).map((ligne, i) => Object.assign({ id: "a:" + i }, JSON.parse(ligne)));
    const noeuds = Object.keys(brutNoeuds).map((id) => Object.assign({ id }, brutNoeuds[id]));
    const parId = new Map(noeuds.map((n) => [n.id, n]));
    const goulots = new Map(((tissu && tissu.goulots) || []).map((g) => [g.noeud, g]));
    const desequilibres = new Map(((tissu && tissu.desequilibres) || []).map((g) => [g.noeud, g]));
    const forces = new Map(((tissu && tissu.force) || []).map((f) => ["pers:" + f.qui, f]));
    const murs = new Map(((tissu && tissu.murs) || []).map((m) => [m.id, m]));
    const critique = ((tissu && tissu.critique && tissu.critique[0]) || {}).chaine || [];
    const critiques = new Set(critique.map((n) => n.id));
    const couplesCritiques = new Set();
    for (let i = 0; i + 1 < critique.length; i++)
      couplesCritiques.add(critique[i].id + "\u0000" + critique[i + 1].id);

    noeuds.forEach((n) => {
      n.goulot = goulots.get(n.id) || null;
      n.desequilibre = desequilibres.get(n.id) || null;
      n.force = forces.get(n.id) || null;
      n.mur = murs.get(n.id) || null;
      n.critique = critiques.has(n.id);
      n.double_genre = (n.genres || []).length > 1;
    });
    aretes.forEach((a, i) => {
      a.critique = couplesCritiques.has(a.de + "\u0000" + a.vers);
      for (const bout of ["de", "vers"]) {
        if (parId.has(a[bout])) continue;
        const original = a[bout];
        const id = "pendant:" + i + ":" + bout;
        const n = { id, genre: "pendant", genres: ["pendant"], ou: "adressage",
          quoi: original === "?" ? "extrémité non adressée" : String(original),
          pendant: true, bout_original: original };
        noeuds.push(n); parId.set(id, n); a[bout] = id; a.bout_original = original;
      }
    });

    // Les candidats restent des hypotheses : pointilles et transparents. Une
    // vraie arete `equilibre` les remplace automatiquement au prochain tissage.
    ((tissu && tissu.desequilibres) || []).forEach((d) => {
      (d.candidats || []).forEach((c, i) => {
        if (!parId.has(c.id) || !parId.has(d.noeud)) return;
        aretes.push({ id: "candidat:" + d.noeud + ":" + i, de: c.id,
          vers: d.noeud, nature: "candidat_equilibre", source: "evaluation/texte",
          flou: true, virtuel: true, texte: "candidat textuel non tissé" });
      });
    });

    const journal = lire("journal.json", {}) || {};
    const observateurs = [{ id: "mj", nom: "MJ — vérité complète" }];
    const joueur = journal.personnage_joueur_id;
    if (joueur) observateurs.push({ id: joueur, nom: nom(joueur) });
    if (gens["aurore-inchauspe"] && joueur !== "aurore-inchauspe")
      observateurs.push({ id: "aurore-inchauspe", nom: nom("aurore-inchauspe") });
    Object.values(gens).sort((a, b) => String(a.nom).localeCompare(String(b.nom), "fr"))
      .forEach((p) => {
        if (!p.id || observateurs.some((o) => o.id === p.id)) return;
        observateurs.push({ id: p.id, nom: p.nom || p.id });
      });

    // Qui émet l'importance narrative : les sièges occupés, et le principal
    // en tête. La régie diffuse depuis eux — un tissu n'a pas de centre en
    // soi, il en a un parce qu'un joueur est assis quelque part.
    const emetteurs = (Array.isArray(listeSieges) ? listeSieges : [])
      .filter((s) => s && s.occupe && s.personnage_id)
      .map((s) => ({ id: s.personnage_id, nom: s.nom || nom(s.personnage_id),
        role: s.role || "second" }));

    const suivables = aretes.filter((a) => !a.flou && !a.virtuel);
    const pendantes = suivables.filter((a) => parId.get(a.de).pendant || parId.get(a.vers).pendant);
    graphe = {
      noeuds, aretes, observateurs, sieges: emetteurs,
      resume: {
        noeuds: Object.keys(brutNoeuds).length,
        aretes: aretes.filter((a) => !a.virtuel).length,
        suivables: suivables.length,
        resolues: suivables.length - pendantes.length,
        pendantes: pendantes.length,
        floues: aretes.filter((a) => a.flou && !a.virtuel).length,
        doubles: noeuds.filter((n) => n.double_genre).length,
        natifs: aretes.filter((a) => a.natif).length,
        candidats: aretes.filter((a) => a.virtuel).length,
        routes: aretes.filter((a) => a.connaissance).length,
        murs_sans_route: murs.size,
      },
    };
  } catch (e) {
    graphe = { erreur: String(e.message || e), noeuds: [], aretes: [], observateurs: [] };
  }
  return {
    tissu, graphe,
    date: monde.date || null, date_texte: dateCourte(monde.date),
    tension: monde.tension == null ? null : monde.tension, phase: monde.phase || "",
    horloges: lire("horloges.json", {}),
    groupes, hors_echelle: horsEchelle, alertes,
    echeances, mains,
  };
}

module.exports = { nomsDesPersonnages, filPersonnage, chercherDansFlux, extraitDuFlux, regie };
