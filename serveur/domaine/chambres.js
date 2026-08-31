// CHAMBRES — la matière de l'onglet « Les chambres » de la régie.
//
// Ce module lit `chambres/` et les traces d'activité, et rend de quoi dessiner
// une FRISE : qui s'est réveillé, quand, et qui a parlé à qui. Il ne calcule
// rien du monde et n'écrit nulle part — c'est de la lecture d'envers du décor.
//
// POURQUOI PAS UN GRAPHE, ET C'EST UNE MESURE. 122 chambres, 60 canaux, et
// `mj` en touche 46 : la topologie est une ÉTOILE. Un force-directed rendrait
// un moyeu et des rayons, c'est-à-dire rien. Ce qu'on ne voit nulle part
// ailleurs, en revanche, c'est le FAN-OUT d'un réveil et la latence d'un
// échange — deux choses qui vivent sur un axe de temps réel.
//
// LE TEMPS EST CELUI DE LA MACHINE, PAS CELUI DU MONDE, et c'est voulu : on
// débogue un runtime. 364 des 367 entrées de canal portent `t` (epoch réel) ;
// trois portent `date`/`heure` (temps du monde), héritage du format documenté
// dans `chambre.py`. On normalise les deux ici, et l'on DIT lesquelles sont
// sans horodatage réel plutôt que de les placer au hasard.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
// Le composant de portrait du jeu, reutilise tel quel.
const { portraitDefaut, portraitFrais } = require("../peinture").portraits;

const CHAMBRES = path.join(RACINE, "chambres");
const ETAT = path.join(RACINE, "etat");

function lire(p, defaut) {
  try { return JSON.parse(fs.readFileSync(p, "utf-8")); }
  catch (e) { return defaut; }
}

function estZone(id) { return id === "mj"; }

/** Les habitants : un dossier de `chambres/`, et rien d'autre. */
function habitants() {
  let noms = [];
  try { noms = fs.readdirSync(CHAMBRES); } catch (e) { return []; }
  return noms.filter((n) => {
    try { return fs.statSync(path.join(CHAMBRES, n)).isDirectory(); }
    catch (e) { return false; }
  }).sort();
}

/** L'horodatage réel d'une entrée, ou null si elle n'en porte pas. */
function quand(entree) {
  const t = Number(entree && entree.t);
  return Number.isFinite(t) && t > 0 ? Math.round(t * 1000) : null;
}

/**
 * Les canaux, dédoublonnés par paire. Le `discussion.json` est canonique chez
 * l'un des deux (ordre lexical) mais reste accessible des deux côtés : sans ce
 * dédoublonnage, chaque échange compterait double.
 */
function canaux() {
  const vus = new Set();
  const sortie = [];
  for (const qui of habitants()) {
    const rel = path.join(CHAMBRES, qui, "relations");
    let autres = [];
    try { autres = fs.readdirSync(rel); } catch (e) { continue; }
    for (const autre of autres) {
      const cle = [qui, autre].sort().join(" ");
      if (vus.has(cle)) continue;
      const f = path.join(rel, autre, "discussion.json");
      if (!fs.existsSync(f)) continue;
      vus.add(cle);
      const entrees = (lire(f, {}) || {}).entrees || [];
      sortie.push({ a: [qui, autre].sort()[0], b: [qui, autre].sort()[1],
                    entrees });
    }
  }
  return sortie;
}

/**
 * Les événements de la frise, tous horodatés en millisecondes réelles.
 *
 * Quatre genres, et ils répondent chacun à une question du débogage :
 *   `mot`        — qui a parlé à qui, et à la seconde près : la latence.
 *   `activation` — qui la boucle a élu, avec son budget : le fan-out.
 *   `rapport`    — quand une session a rendu : la durée réelle d'une journée.
 *   `session`    — un fil déposé dans sa chambre : ce qu'il a vécu.
 */
function evenements(canauxLus, habitantsLus) {
  const ev = [];
  let sansHeure = 0;
  for (const c of canauxLus || canaux()) {
    for (const e of c.entrees) {
      const t = quand(e);
      if (t === null) { sansHeure += 1; continue; }
      const de = e.de || null;
      // LE TEXTE, PAS SEULEMENT SA LONGUEUR. La frise ne portait que `taille`,
      // et la bulle devait renvoyer le lecteur « lire dans la chambre » — un
      // survol qui repond « va voir ailleurs » n'a pas repondu.
      const txt = String(e.texte || "");
      ev.push({ genre: "mot", t, de, vers: de === c.a ? c.b : c.a,
                taille: txt.length, extrait: txt.slice(0, 260),
                coupe: txt.length > 260,
                jour: e.date || null,
                verbe: e.verbe || null, verdict: e.verdict || null });
    }
  }
  const boucle = lire(path.join(ETAT, "activations", "boucle.json"), {}) || {};
  for (const h of boucle.historique || []) {
    const t = Date.parse(h.termine_le || "");
    if (!Number.isFinite(t)) continue;
    ev.push({ genre: "activation", t, de: h.qui, vers: null,
              tache: h.tache, budget: h.budget, depense: h.depense,
              importance: h.importance });
  }
  for (const qui of habitantsLus || habitants()) {
    const fil = path.join(CHAMBRES, qui, "fil");
    let fichiers = [];
    try { fichiers = fs.readdirSync(fil); } catch (e) { continue; }
    for (const f of fichiers) {
      let st;
      try { st = fs.statSync(path.join(fil, f)); } catch (e) { continue; }
      ev.push({ genre: f.endsWith("-salle.md") ? "salle" : "session",
                t: Math.round(st.mtimeMs), de: qui, vers: null,
                fichier: f, octets: st.size });
    }
  }
  ev.sort((x, y) => x.t - y.t);
  return { evenements: ev, sans_heure: sansHeure };
}

// LES SEPT FAMILLES DE GESTES D'UN HABITANT (docs/habitant.md). La frise ne
// montrait que « il a parlé » et « il a été activé » ; l'habitant fait sept
// choses, et ce qu'on veut voir c'est LESQUELLES il ne fait jamais.
// Mesure du 31.8 sur 122 chambres : 3 réveils, 3 verbes, 2 `demain.md`,
// 2 brouillons — presque toute la taxonomie est muette, et c'est le
// diagnostic. Une famille qui ne bat pas se voit ici avant d'être cherchée.
const FAMILLES = {
  percevoir: "son réveil : brief, creux, billets en percept, demain.md",
  lire: "Read/Grep/Glob sur le dépôt et son étagère",
  ecrire: "chez lui : cahier, brouillons, fiches, ses deux registres",
  verbe: "TENTER · FAIRE · DEMANDER — engager le monde",
  parler: "au parloir, ou un billet qui réveille l'autre",
  conclure: "demain.md — sa conclusion pour lui-même",
  subi: "ce que le lanceur dépose : son vécu au fil",
};

/** Le verbe d'une entrée de canal, ou null si c'est une parole ordinaire. */
function verbeDe(texte) {
  const m = /^\s*\[(TENTER|FAIRE|DEMANDER)\]/.exec(String(texte || ""));
  return m ? m[1] : null;
}

/**
 * Les gestes lus dans le fil d'une chambre. `trace.py` y écrit trois marques :
 * `> 📯` le réveil (ce qu'on lui a dit), `- 🤚 Outil` un geste d'outil,
 * `> 👂` une voix entendue en pleine session. On les compte plutôt que de les
 * dater : le fil ne porte que le mtime du fichier, pas l'heure de chaque pas.
 */
function gestesDuFil(qui) {
  const compte = { percevoir: 0, lire: 0, ecrire: 0, parler: 0 };
  const fil = path.join(CHAMBRES, qui, "fil");
  let fichiers = [];
  try { fichiers = fs.readdirSync(fil); } catch (e) { return compte; }
  for (const f of fichiers) {
    let t = "";
    try { t = fs.readFileSync(path.join(fil, f), "utf-8"); } catch (e) { continue; }
    compte.percevoir += (t.match(/> 📯/g) || []).length;
    compte.parler += (t.match(/> 👂/g) || []).length;
    for (const m of t.matchAll(/- 🤚 `(\w+)/g)) {
      if (["Read", "Grep", "Glob"].includes(m[1])) compte.lire += 1;
      else if (["Write", "Edit"].includes(m[1])) compte.ecrire += 1;
    }
  }
  return compte;
}

/** Ce qu'il a écrit chez lui : le fichier, et quand il a bougé. */
function ecritsDe(qui) {
  const base = path.join(CHAMBRES, qui);
  const sortie = [];
  const voir = (rel, quoi) => {
    try {
      const st = fs.statSync(path.join(base, rel));
      if (st.isFile()) sortie.push({ quoi, fichier: rel, t: Math.round(st.mtimeMs) });
    } catch (e) { /* absent : c'est une information, pas une erreur */ }
  };
  voir("claude.md", "son cahier");
  voir("demain.md", "sa conclusion");
  voir("problemes.json", "les pannes de la machine");
  voir("en-souffrance.json", "ses fils ouverts");
  for (const d of ["brouillons", "books"]) {
    let noms = [];
    try { noms = fs.readdirSync(path.join(base, d)); } catch (e) { continue; }
    for (const n of noms) {
      try {
        const st = fs.statSync(path.join(base, d, n));
        sortie.push({ quoi: d === "books" ? "un volume à lui" : "un brouillon",
                      fichier: d + "/" + n, t: Math.round(st.mtimeMs) });
      } catch (e) { /* rien */ }
    }
  }
  return sortie.sort((a, b) => b.t - a.t);
}

/** Le tableau des sept familles pour une chambre : combien, et la dernière. */
function gestesDe(qui, canauxLus, boucleLue) {
  const fil = gestesDuFil(qui);
  const ecrits = ecritsDe(qui);
  const cahier = ecrits.find((x) => x.quoi === "son cahier");
  const demain = ecrits.find((x) => x.quoi === "sa conclusion");
  let verbes = 0, paroles = 0, dernierMot = null, premierMot = null;
  let dernierVerbe = null, premierVerbe = null;
  for (const c of canauxLus || canaux()) {
    if (c.a !== qui && c.b !== qui) continue;
    for (const e of c.entrees) {
      if (e.de !== qui) continue;
      const estVerbe = !!verbeDe(e.texte);
      if (estVerbe) verbes += 1; else paroles += 1;
      const t = quand(e);
      if (!t) continue;
      if (estVerbe) {
        if (!dernierVerbe || t > dernierVerbe) dernierVerbe = t;
        if (!premierVerbe || t < premierVerbe) premierVerbe = t;
      } else {
        if (!dernierMot || t > dernierMot) dernierMot = t;
        if (!premierMot || t < premierMot) premierMot = t;
      }
    }
  }
  // LE FIL PORTE LES HEURES QUE LE COMPTE JETAIT. `percevoir`, `lire` et
  // `subi` rendaient `t: null` — cinq familles sur sept sans date, et une
  // bulle qui ne pouvait pas repondre « quand ». Les mtimes du fil les
  // donnent : c'est la meme source qui a servi a les compter.
  let filT = [];
  try {
    const d = path.join(CHAMBRES, qui, "fil");
    filT = fs.readdirSync(d).map((f) => {
      try { return Math.round(fs.statSync(path.join(d, f)).mtimeMs); }
      catch (e) { return null; }
    }).filter(Boolean).sort((a, b) => a - b);
  } catch (e) { filT = []; }
  const filDernier = filT.length ? filT[filT.length - 1] : null;
  const filPremier = filT.length ? filT[0] : null;
  const boucle = boucleLue || lire(path.join(ETAT, "activations", "boucle.json"), {}) || {};
  const jauge = ((boucle.acteurs || {})[qui]) || {};
  const vieux = ecrits.length ? ecrits[ecrits.length - 1].t : null;
  return {
    percevoir: { n: fil.percevoir || jauge.activations || 0,
                 t: filDernier, premier: filPremier },
    lire: { n: fil.lire, t: filDernier, premier: filPremier },
    ecrire: { n: ecrits.length, t: ecrits.length ? ecrits[0].t : null,
              premier: vieux, amende: !!(cahier && cahier.t) },
    verbe: { n: verbes, t: dernierVerbe, premier: premierVerbe },
    parler: { n: paroles, t: dernierMot, premier: premierMot },
    conclure: { n: demain ? 1 : 0, t: demain ? demain.t : null,
                premier: demain ? demain.t : null },
    subi: { n: filT.length, t: filDernier, premier: filPremier },
  };
}

// UNE SESSION EST UN CONTAINER, PAS UN POINT. Un rapport d'activation porte
// `cree_le` et `duree_ms` : la session a donc une DUREE REELLE, et ce qui s'est
// passe dedans se pose dedans. Les activites, elles, portent un temps du MONDE
// (`temps.debut_s / duree_s`) — deux horloges, et on ne les melange pas : le
// container est en temps machine, les pastilles se placent a la fraction du
// temps de monde qu'elles ont consommee. C'est la seule facon honnete de
// montrer « ce qu'il a fait pendant sa session » sans inventer d'horodatage.
// L'EMOJI SE DERIVE DE CE QUE L'ACTIVITE A ENREGISTRE, PAS DE SON `type`.
// Mesure du 31.8 : 703 activites sur 703 portent `type: null` — le vocabulaire
// `TYPES_RESULTAT_ACTIVITE` existe dans `activation/socle.py` et RIEN ne
// l'ecrit. Lire ce champ, c'etait donc rendre un seul et meme glyphe partout.
// Les champs qui, eux, sont remplis disent la nature du pas : un blocage, un
// resultat produit, une source touchee, une cible nommee. On lit ceux-la.
const EMOJI_RESULTAT = {
  observation: "👁", progression_tache: "▶", variation_mesure: "📊",
  deplacement: "🚶", objet_produit: "📦", communication: "💬",
  fait: "✓", blocage: "⛔", echec: "✕",
};

// LE VOCABULAIRE EST UN CRAN PLUS BAS QUE LA OU ON LE CHERCHAIT. L'activite
// porte `type: null` — 703 fois sur 703 — mais chacun de ses RESULTATS porte
// le sien, et c'est bien celui de `TYPES_RESULTAT_ACTIVITE` : 1317 resultats
// repartis sur les huit types. Le pas prend donc le glyphe de son premier
// resultat ; un blocage l'emporte, parce qu'un pas qui bute n'est pas un pas
// qui produit.
// CE QU'UN PAS A FAIT, DIT EN FRANCAIS. Le meme constat que pour l'emoji, et
// la meme source : `activite.type` est nul 703 fois sur 703, le vocabulaire
// vit sur les RESULTATS. Sans ce libelle, toute infobulle s'appelait « un
// pas » — l'emoji distinguait, les mots non. Corriger un contournement sans
// recenser les autres lecteurs du meme champ laisse la faute vivante ailleurs.
const NOM_RESULTAT = {
  observation: "il a regardé", progression_tache: "il a avancé",
  variation_mesure: "un chiffre a bougé", deplacement: "il s'est déplacé",
  objet_produit: "il a produit", communication: "il a parlé",
  fait: "un fait acquis", blocage: "il a buté", echec: "un échec",
};

/** Le type derive d'un pas : celui de son premier resultat, blocage en tete. */
function typeActe(a) {
  if (!a) return null;
  if (a.blocage) return "blocage";
  const r = (a.resultats_produits || [])[0];
  return (r && (r.type || r.genre)) || null;
}

function emojiActe(a) { return EMOJI_RESULTAT[typeActe(a)] || "◦"; }

function nomActe(a) {
  const t = typeActe(a);
  // Plusieurs resultats de natures differentes : on nomme le premier et l'on
  // DIT qu'il y en a d'autres, plutot que de choisir en silence.
  const autres = new Set(((a && a.resultats_produits) || [])
    .map((r) => r.type || r.genre).filter(Boolean));
  const nom = NOM_RESULTAT[t] || "un pas";
  return autres.size > 1
    ? nom + " (+" + (autres.size - 1) + " autre" + (autres.size > 2 ? "s" : "") + ")"
    : nom;
}

function sessions(limite) {
  const base = path.join(ETAT, "activations");
  let noms = [];
  try { noms = fs.readdirSync(base); } catch (e) { return []; }
  noms = noms.filter((n) => /^[0-9].*\.json$/.test(n)).sort();
  if (limite) noms = noms.slice(-limite);
  const sortie = [];
  for (const n of noms) {
    const d = lire(path.join(base, n), null);
    if (!d) continue;
    const a = d._activation || {};
    const debut = Date.parse(a.cree_le || "");
    if (!Number.isFinite(debut)) continue;
    const duree = Math.max(1000, Number(a.duree_ms) || 1000);
    const act = d.activation || {};
    const gestes = (act.activites || []).map((x, i) => {
      const t = x.temps || {};
      const ac = x.action || {};
      // LE CHEMIN DIT LE « OU », ET RIEN D'AUTRE NE LE DIT. `cibles` nomme ce
      // sur quoi il agit ; seul `chemin_execution` nomme l'endroit d'ou il le
      // fait et celui qu'il atteint. Une bulle sans ca laisse croire que tout
      // se passe au meme endroit — c'est faux la moitie du temps.
      const ch = x.chemin_execution || [];
      const ou = ch.length
        ? { de: ch[0].de || null,
            vers: ch[ch.length - 1].vers || null,
            relation: ch[0].relation || null,
            etapes: ch.length }
        : null;
      return {
        quoi: String(x.quoi || ac.quoi || "").slice(0, 400),
        verbe: ac.verbe || x.type || null,
        type: x.type || null,
        emoji: emojiActe(x),
        nature: nomActe(x),
        type_derive: typeActe(x),
        cout: Number(x.cout_energie) || 0,
        debut_s: Number(t.debut_s) || 0,
        duree_s: Number(t.duree_s) || 0,
        rang: Number(x.ordre) || i + 1,
        ou: ou,
        cibles: (ac.cibles || []).slice(0, 6),
        // {ref, mode} — le mode est la moitie de l'information : « voit » et
        // « entend » ne se valent pas quand on juge ce qu'un homme peut savoir.
        touche: (x.sources_touchees || []).slice(0, 6),
        mobilise: (x.sources_mobilisees || []).slice(0, 6),
        sorties: (x.resultats_produits || []).slice(0, 4).map((r) => ({
          type: r.type || null, cible: r.cible || null,
          certitude: r.certitude || null,
          apres: String(r.apres || "").slice(0, 300),
        })),
        blocage: x.blocage || null,
      };
    });
    // La fenetre de monde couverte par la session : elle sert a placer les
    // pastilles DANS le container, en proportion.
    const monde0 = gestes.length ? Math.min(...gestes.map((g) => g.debut_s)) : 0;
    const monde1 = gestes.length
      ? Math.max(...gestes.map((g) => g.debut_s + g.duree_s)) : 1;
    sortie.push({
      qui: d.qui || n.replace(/^[0-9-]+-/, "").replace(/\.json$/, ""),
      // Le nom du rapport : c'est la clef par laquelle le clic redemande TOUT
      // le detail, sans qu'on ait a le porter dans la vue d'ensemble.
      fichier: n,
      session: a.session || a.session_pnj || null,
      modele: a.modele || null,
      debut, fin: debut + duree, duree_ms: duree,
      issue: act.issue || null,
      tache: a.tache || (d.tache || null),
      budget: a.budget || null,
      cout_usd: Number(a.cout_usd) || 0,
      horloge_pj: a.horloge_pj || null,
      date_locale: a.date_locale || null,
      monde0, monde1: monde1 > monde0 ? monde1 : monde0 + 1,
      gestes,
    });
  }
  return sortie;
}

/** L'état d'une chambre : ce que le panneau de droite montre au clic. */
function chambre(qui) {
  const base = path.join(CHAMBRES, qui);
  if (!fs.existsSync(base)) return null;
  let cahier = "";
  try { cahier = fs.readFileSync(path.join(base, "claude.md"), "utf-8"); }
  catch (e) { cahier = ""; }
  const pend = lire(path.join(base, "en-souffrance.json"), {}) || {};
  const pannes = lire(path.join(base, "problemes.json"), {}) || {};
  const rel = [];
  let autres = [];
  try { autres = fs.readdirSync(path.join(base, "relations")); } catch (e) {}
  for (const autre of autres) {
    const premier = [qui, autre].sort()[0], second = [qui, autre].sort()[1];
    const canonique = path.join(CHAMBRES, premier, "relations", second,
                                "discussion.json");
    const herite = path.join(CHAMBRES, second, "relations", premier,
                             "discussion.json");
    const f = fs.existsSync(canonique) ? canonique : herite;
    const entrees = fs.existsSync(f) ? ((lire(f, {}) || {}).entrees || []) : [];
    let fiche = "";
    try {
      fiche = fs.readFileSync(path.join(base, "relations", autre, "claude.md"),
                              "utf-8");
    } catch (e) { fiche = ""; }
    rel.push({ avec: autre, entrees: entrees.length,
               fiche: fiche.slice(0, 1200),
               derniers: entrees.slice(-4).map((e) => ({
                 de: e.de, t: quand(e),
                 texte: String(e.texte || "").slice(0, 600) })) });
  }
  rel.sort((x, y) => y.entrees - x.entrees);
  let fil = [];
  try {
    fil = fs.readdirSync(path.join(base, "fil")).map((f) => {
      const st = fs.statSync(path.join(base, "fil", f));
      return { fichier: f, octets: st.size, t: Math.round(st.mtimeMs) };
    }).sort((x, y) => y.t - x.t);
  } catch (e) { fil = []; }
  let livres = [];
  try { livres = fs.readdirSync(path.join(base, "books")); } catch (e) {}
  let brouillons = [];
  try { brouillons = fs.readdirSync(path.join(base, "brouillons")); } catch (e) {}
  const boucle = lire(path.join(ETAT, "activations", "boucle.json"), {}) || {};
  const jauge = ((boucle.acteurs || {})[qui]) || null;
  return {
    id: qui, zone: estZone(qui),
    // LE SIGNAL DE DÉRIVE, et c'est le plus utile de la fiche : un cahier
    // qui porte une section datée est un cahier qu'il a repris en main.
    cahier_amende: cahier.includes("## Amend"),
    cahier: cahier.slice(0, 4000),
    en_souffrance: {
      j_attends: (pend.j_attends || []).length,
      on_attend_de_moi: (pend.on_attend_de_moi || []).filter((x) => !x.tenu).length,
      detail: pend,
    },
    problemes: (pannes.entrees || []),
    relations: rel, fil, livres, brouillons,
    energie: jauge ? jauge.energie : null,
    activations: jauge ? jauge.activations : null,
    // Les sept familles de gestes, et ce qu'il a ecrit chez lui : c'est la
    // moitie de la taxonomie que la frise ne peut pas montrer ligne par ligne.
    gestes: gestesDe(qui),
    ecrits: ecritsDe(qui),
  };
}

/**
 * UN RAPPORT ENTIER, POUR LE CLIC. La vue d'ensemble porte le strict
 * necessaire — sinon 120 rapports complets font des megaoctets a chaque
 * chargement. Le detail exact se redemande a la piece, quand on le veut.
 */
function rapport(fichier) {
  if (!/^[0-9][0-9a-z._-]*\.json$/.test(fichier)) return null;
  const d = lire(path.join(ETAT, "activations", fichier), null);
  if (!d) return null;
  const a = d._activation || {};
  const act = d.activation || {};
  return {
    fichier, qui: d.qui || null,
    session: a.session || null, session_pnj: a.session_pnj || null,
    cree_le: a.cree_le || null, duree_ms: a.duree_ms || null,
    duree_api_ms: a.duree_api_ms || null, cout_usd: a.cout_usd || 0,
    modele: a.modele || null, effort: a.effort || null,
    tours: a.tours || null, usage: a.usage || null,
    budget: a.budget || null, budget_secondes: a.budget_secondes || null,
    importance: a.importance == null ? null : a.importance,
    front: a.front || null, present_secondes: a.present_secondes || null,
    horloge_pj: a.horloge_pj || null, date_locale: a.date_locale || null,
    tache: a.tache || d.tache || null,
    issue: act.issue || null,
    energie_depensee: act.energie_depensee == null ? null
                    : act.energie_depensee,
    phrase: act.phrase || act.conclusion || null,
    activites: (act.activites || []).map((x) => ({
      ordre: x.ordre, quoi: x.quoi, cible_id: x.cible_id || null,
      source: x.source || null, resultat: x.resultat || null,
      preuve: x.preuve || null, blocage: x.blocage || null,
      cout_energie: x.cout_energie, temps: x.temps || null,
      emoji: emojiActe(x), nature: nomActe(x), type_derive: typeActe(x),
      sources_touchees: x.sources_touchees || [],
      resultats_produits: (x.resultats_produits || []).map((r) => ({
        type: r.type || null, cible: r.cible || null,
        avant: r.avant || null, apres: r.apres || null,
      })),
    })),
    mutations: (d.mutations || act.mutations || []).length,
  };
}

/** La bande des salles : qui se tient où, d'après ce qu'une scène a constaté. */
function salles() {
  const p = lire(path.join(ETAT, "presence.json"), {}) || {};
  const gens = (p.resolu && p.resolu.gens) || p.presence || {};
  const par = {};
  for (const [id, ou] of Object.entries(gens)) {
    const cle = (ou && (ou.salle || ou.lieu)) || "sans salle";
    (par[cle] = par[cle] || { salle: cle, lieu: (ou || {}).lieu || "", gens: [] })
      .gens.push({ id, chambre: fs.existsSync(path.join(CHAMBRES, id)) });
  }
  for (const s of Object.values(par)) s.gens.sort((a, b) => a.id.localeCompare(b.id));
  return { salles: Object.values(par).sort((a, b) => b.gens.length - a.gens.length),
           date: (p.resolu && p.resolu.date) || null };
}

/** Le paquet de l'onglet : les lignes de la frise, ses événements, les salles. */
function vueChambres() {
  const tous = habitants();
  const canauxLus = canaux();
  const boucle = lire(path.join(ETAT, "activations", "boucle.json"), {}) || {};
  const { evenements: ev, sans_heure } = evenements(canauxLus, tous);
  const compte = {};
  for (const e of ev) {
    for (const qui of [e.de, e.vers]) {
      if (!qui) continue;
      const c = (compte[qui] = compte[qui] || { id: qui, zone: estZone(qui),
                                                mots: 0, activations: 0,
                                                premier: e.t, dernier: e.t });
      c.premier = Math.min(c.premier, e.t);
      c.dernier = Math.max(c.dernier, e.t);
      if (e.genre === "mot") c.mots += 1;
      if (e.genre === "activation" && qui === e.de) c.activations += 1;
    }
  }
  for (const [id, j] of Object.entries(boucle.acteurs || {})) {
    if (compte[id]) { compte[id].energie = j.energie; continue; }
  }
  const lignes = Object.values(compte).sort((a, b) =>
    (b.zone - a.zone) || (b.dernier - a.dernier));
  // Les sept familles pour CHAQUE ligne : c'est ce qui rend le silence
  // visible sans avoir a ouvrir une chambre apres l'autre.
  for (const l of lignes) {
    l.gestes = gestesDe(l.id, canauxLus, boucle);
  }
  // LE PORTRAIT, PAR LE COMPOSANT QUI EXISTE DEJA (serveur/portraits.js) :
  // le meme visage qu'a l'ecran de jeu, la meme silhouette de secours, la
  // meme teinte tiree du nom. On ne redessine pas un rond ici.
  // LE VISAGE PAR URL, PAS INLINE : voir la route /portraits/<id>.svg. Inliner
  // les 56 SVG pesait 459 Ko sur 738 — les deux tiers du paquet, renvoyes a
  // chaque chargement, devant une vue qui ne peut rien afficher avant.
  for (const l of lignes) l.visage = "/portraits/" + l.id + ".svg";
  return {
    familles: FAMILLES,
    sessions: sessions(120),
    lignes, evenements: ev, sans_heure,
    muettes: tous.filter((x) => !compte[x]).length,
    chambres: tous.length,
    canaux: canauxLus.length,
    salles: salles(),
    lu_a: Date.now(),
  };
}

// ---- LE FIL PAR HOMME — ce que voit un joueur qui incarne un habitant ----
//
// Le fil d'un homme est SA mémoire, jamais le flux public : sa conclusion de
// veille (demain.md), le vécu de ses sessions (fil/*.md), et les billets de
// ses canaux (relations/*/discussion.json). Lecture seule, robuste aux
// fichiers absents — une chambre vide rend un fil vide. Le format des fichiers
// fil appartient à scripts/agents/chambre.py ; ici on ne fait que le LIRE :
// 📯 (blockquote) le réveil, 🤚 (liste) un geste, 👂 (blockquote) l'entendu,
// le reste est sa voix. Vaut pour un MJ comme pour un homme — même chambre,
// même assembleur, c'est le principe du modèle (habitant.md §1).

/** "9h05" → minutes depuis minuit, ou null. */
function minutesDe(h) {
  const m = String(h || "").match(/^(\d+)h(\d*)$/);
  return m ? (+m[1]) * 60 + (+m[2] || 0) : null;
}

/** La clé d'ordre d'une entrée : le jour du monde, puis l'heure quand on l'a. */
function cleDe(d, min) {
  if (!d) return 0;
  return (((d.annee || 0) * 100 + (d.lune || 0)) * 100 + (d.jour || 0)) * 2000
    + (min === null || min === undefined ? 0 : min + 1);
}

/**
 * Une entrée de canal est « en voix » quand elle porte des mots et non de la
 * mécanique : les [VERBE] techniques et les JSON du canal ~mj n'apparaissent
 * pas dans le fil (le design le dit : un billet est un papier qui a voyagé).
 */
function enVoix(texte) {
  const t = String(texte || "").replace(/^\s+/, "");
  if (/^\[(TENTER|FAIRE|DEMANDER|DIRE)\]/.test(t)) return false;
  if (t[0] === "{") return false;
  if (t[0] === "[") { try { JSON.parse(t); return false; } catch (e) {} }
  return true;
}

/**
 * Un dépôt de fil (markdown) → ses entrées, dans l'ordre du fichier.
 * Les gestes 🤚 se replient en UNE SEULE entrée par journée, avec le détail.
 */
function parserFilMd(texte, date) {
  const entrees = [];
  const gestes = [];
  const lignes = String(texte || "").split(/\r?\n/);
  let para = [];
  const pousserPara = () => {
    const t = para.join("\n").trim();
    para = [];
    if (t) entrees.push({ genre: "replique", texte: t });
  };
  let i = 0;
  while (i < lignes.length) {
    const l = lignes[i];
    // l'en-tête du fichier (titre, id de session) n'est pas du vécu
    if (/^#\s/.test(l) || /^session\s+`/.test(l)) { i += 1; continue; }
    const g = l.match(/^-\s*🤚\s*`?(.*?)`?\s*$/);
    if (g) { pousserPara(); if (g[1]) gestes.push(g[1]); i += 1; continue; }
    if (/^>/.test(l)) {
      pousserPara();
      const bloc = [];
      while (i < lignes.length && /^>/.test(lignes[i])) {
        bloc.push(lignes[i].replace(/^>\s?/, ""));
        i += 1;
      }
      const t = bloc.join("\n").trim();
      if (t.indexOf("👂") === 0) {
        entrees.push({ genre: "entendu", texte: t.replace(/^👂\s*/, "") });
      } else if (t) {
        // 📯 le réveil — et tout blockquote sans marqueur se lit pareil
        entrees.push({ genre: "recit", texte: t.replace(/^📯\s*/, "") });
      }
      continue;
    }
    para.push(l);
    i += 1;
  }
  pousserPara();
  if (gestes.length) {
    const compte = {};
    for (const g of gestes) {
      const outil = g.split(/\s/)[0] || "?";
      compte[outil] = (compte[outil] || 0) + 1;
    }
    const resume = Object.keys(compte)
      .map((o) => (compte[o] > 1 ? o + " ×" + compte[o] : o)).join(", ");
    entrees.push({ genre: "gestes", nb: gestes.length,
                   texte: gestes.length + (gestes.length > 1 ? " gestes — " : " geste — ") + resume,
                   detail: gestes });
  }
  for (const e of entrees) e._cle = cleDe(date, null);
  return entrees;
}

/**
 * Le fil d'un homme, chronologique et borné : les 200 dernières entrées,
 * paginables par `avant` (l'index de la première entrée déjà tenue, comme
 * /scene). Sans `avant`, la conclusion de veille (demain.md) s'épingle en
 * tête — « là où tu t'étais laissé ».
 */
function filHomme(id, avant) {
  const base = path.join(CHAMBRES, id);
  if (!fs.existsSync(base)) return { fil: [], debut: 0, total: 0 };

  const corpus = [];
  // 2. les dépôts fil/*.md, ordre chronologique par nom de fichier
  let fichiers = [];
  try {
    fichiers = fs.readdirSync(path.join(base, "fil"))
      .filter((f) => f.endsWith(".md")).sort();
  } catch (e) {}
  for (const f of fichiers) {
    const m = f.match(/^(\d+)\.(\d+)\.(\d+)/);
    const date = m ? { annee: +m[1], lune: +m[2], jour: +m[3] } : null;
    let texte = "";
    try { texte = fs.readFileSync(path.join(base, "fil", f), "utf-8"); }
    catch (e) { continue; }
    for (const e of parserFilMd(texte, date)) corpus.push(e);
  }
  // 3. les billets des canaux — le discussion.json canonique de la paire
  let autres = [];
  try { autres = fs.readdirSync(path.join(base, "relations")); } catch (e) {}
  const billets = [];
  for (const autre of autres) {
    const premier = [id, autre].sort()[0], second = [id, autre].sort()[1];
    const chemins = [
      path.join(CHAMBRES, premier, "relations", second, "discussion.json"),
      path.join(CHAMBRES, second, "relations", premier, "discussion.json"),
      path.join(base, "relations", autre, "discussion.json"),
    ];
    const fc = chemins.find((p) => fs.existsSync(p));
    if (!fc) continue;
    const entrees = (lire(fc, {}) || {}).entrees || [];
    // l'exception du canal d'arbitrage : seule la voix passe, jamais la
    // mécanique — et elle vaut dans les deux sens (l'homme vers son MJ,
    // le MJ dans sa propre chambre).
    const arbitrage = estZone(autre) || estZone(id);
    let dprec = null;
    for (const e of entrees) {
      const texte = String(e.texte || "");
      if (arbitrage && !enVoix(texte)) continue;
      const date = e.date || dprec;
      if (e.date) dprec = e.date;
      const min = minutesDe(e.heure);
      billets.push({
        genre: "billet", de: e.de || autre, avec: autre,
        date: date ? date.annee + "." + date.lune + "." + date.jour : null,
        heure: e.heure || null, texte,
        _cle: cleDe(date, min),
      });
    }
  }
  billets.sort((x, y) => x._cle - y._cle);
  // La fusion : le vécu d'abord, les billets ensuite, puis un tri STABLE par
  // jour du monde — l'ordre interne de chaque source survit, et les billets
  // datés à la minute se placent dans leur journée.
  const tout = corpus.concat(billets);
  tout.sort((x, y) => x._cle - y._cle);
  const total = tout.length;
  const fin = (avant === null || avant === undefined)
    ? total : Math.max(0, Math.min(avant, total));
  const debut = Math.max(0, fin - 200);
  const fil = tout.slice(debut, fin).map((e) => {
    const s = Object.assign({}, e);
    delete s._cle;
    return s;
  });
  // 1. demain.md, épinglé en tête de la première page seulement
  if (avant === null || avant === undefined) {
    let demain = "";
    try { demain = fs.readFileSync(path.join(base, "demain.md"), "utf-8").trim(); }
    catch (e) {}
    if (demain) fil.unshift({ genre: "pensee", texte: demain });
  }
  return { fil, debut, total };
}

module.exports = { vueChambres, chambre, filHomme, rapport, FAMILLES };
