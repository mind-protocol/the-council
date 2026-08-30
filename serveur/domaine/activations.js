
// ---- la régie : ce que le MJ voit et que le joueur ne voit jamais ----------
// `/admin` n'est pas une échelle du décor : c'est l'envers. On y lit les têtes,
// les échéances et les mesures — c'est-à-dire tout ce que le brouillard cache.
// Aucune écriture, jamais : un seul écrivain reste la règle, et cette page ne
// l'est pas. Elle relit l'état à chaque requête, sans cache : à deux MJ, un
// cache d'une minute est un mensonge d'une minute.

// ---- journal des activations --------------------------------------------
// La liste reste legere. Prompt, message, rapport et thread complet ne sont
// lus que lorsqu'un MJ ouvre une activation : le graphe n'en paie jamais le
// poids au chargement ni pendant son animation.

const fs = require("fs");
const path = require("path");
const os = require("os");
const childProcess = require("child_process");
const bibliotheque = require("../bibliotheque");
const { RACINE } = require("../contexte");
const { qui } = require("../siege");

const DEPOT_ACTIVATIONS = path.join(RACINE, "etat", "activations");

// ---- LE PLAN ET LES TÊTES : est-ce que l'homme le porte VRAIMENT ? ----------
//
// Une action déclarée « en cours » dans un cahier est la PAROLE de l'homme :
// écrite de sa main, dans un registre que le joueur peut ouvrir, et c'est
// exactement ce qu'il dirait au conseil. C'est le vert déclaratif du plateau.
// Le vert VRAI serait autre chose : que l'action figure dans les ÉTAPES de sa
// tête (`etat/intentions.json`), avec une horloge — c'est-à-dire qu'elle est
// dans la boucle des acteurs et qu'elle avancera toute seule.
//
// AUJOURD'HUI, LA RÉPONSE EST ZÉRO PARTOUT. 584 actions au plan, 200 étapes
// dans les têtes, et pas une seule étape ne cite un numéro d'action : le plan
// du conseil et la boucle des acteurs sont deux mondes qui s'ignorent. Ce n'est
// pas une panne du détecteur, c'est le fait — et c'est pour le VOIR qu'on
// l'expose.
//
// UNE RÉSERVE DE DOCTRINE, ET LE DRAPEAU QUI LA LÈVE. `intentions.json` est la
// tête des PNJ : elle n'est JAMAIS montrée au joueur, c'est la règle cardinale
// du manuel. Ce que la route en tire ici — un booléen « ce numéro est-il cité
// dans ses étapes » — ne dit rien de ce qu'il pense ni de ce qu'il ignore, mais
// c'en est tout de même une lecture. Le joueur a tranché qu'on le fasse ;
// METTRE CETTE CONSTANTE À `false` l'éteint entièrement, sans autre chirurgie :
// la route cesse d'ouvrir le fichier et le champ `dans_la_tete` disparaît.
const LIRE_LES_TETES = true;

const _tetes = { cle: null, par: null, etapes: 0 };
// Les numéros cités dans les étapes de chaque tête, par personnage. On relit au
// changement de mtime seulement : le fichier fait 300 Ko et la route est
// appelée à chaque bascule de plateau.
function numerosDesTetes() {
  if (!LIRE_LES_TETES) return { par: {}, etapes: 0 };
  const f = path.join(RACINE, "etat", "intentions.json");
  let cle;
  try { cle = String(fs.statSync(f).mtimeMs); } catch (e) { return { par: {}, etapes: 0 }; }
  if (_tetes.cle === cle) return { par: _tetes.par, etapes: _tetes.etapes };
  const par = {};
  let etapes = 0;
  try {
    const brut = JSON.parse(fs.readFileSync(f, "utf-8"));
    (Array.isArray(brut) ? brut : []).forEach((a) => {
      if (!a || !a.personnage_id) return;
      const vus = par[a.personnage_id] || (par[a.personnage_id] = {});
      // Une étape vit dans `plan` (une liste) ou dans `etapes` selon les fiches.
      // On ne suppose aucun champ : on cherche le numéro N'IMPORTE OÙ dans
      // l'étape — `quoi`, `id`, un coût, un `si_bloque`. Un homme qui écrit
      // « 21030 » quelque part dans son étape la relie à l'action, et c'est le
      // seul geste qu'on lui demande.
      ["plan", "etapes"].forEach((k) => {
        if (!Array.isArray(a[k])) return;
        a[k].forEach((e) => {
          etapes++;
          (JSON.stringify(e).match(/(?:^|[^\d])(\d{4,6})(?![\d])/g) || [])
            .forEach((m) => { vus[m.replace(/\D/g, "")] = 1; });
        });
      });
    });
  } catch (e) { return { par: {}, etapes: 0 }; }
  _tetes.cle = cle; _tetes.par = par; _tetes.etapes = etapes;
  return { par: par, etapes: etapes };
}

// OÙ SE TIENT QUELQU'UN PAR RAPPORT AU JOUEUR — « quartier » ou « au loin ».
//
// Remplace le champ `echelle` d'intentions.json, supprimé. Le serveur NE
// CALCULE RIEN : il relit ce que `evaluer.py --json` a déposé, comme pour le
// reste du tissu. Dépôt absent ou périmé : on rend « quartier » pour tout le
// monde plutôt que de déclarer le château désert — mieux vaut afficher trop
// que faire croire que personne n'est là.
function ouQuartier(id) {
  try {
    const pt = path.join(RACINE, "etat", "tissu", "evaluation.json");
    const ev = JSON.parse(fs.readFileSync(pt, "utf-8"));
    const gens = ((ev || {}).quartier || {}).gens;
    if (!Array.isArray(gens) || !gens.length) return "quartier";
    return gens.includes(id) ? "quartier" : "au loin";
  } catch (e) { return "quartier"; }
}

function lireJsonSansFaillir(fichier, defaut) {
  try { return JSON.parse(fs.readFileSync(fichier, "utf-8")); }
  catch (_e) { return defaut; }
}

function rapportsEtJournalActivations() {
  const etat = lireJsonSansFaillir(path.join(DEPOT_ACTIVATIONS, "boucle.json"),
    { historique: [], acteurs: {} });
  const parSession = new Map();
  let courant = null, attente = [];
  try {
    const lignes = fs.readFileSync(path.join(DEPOT_ACTIVATIONS, "boucle.log.jsonl"), "utf-8")
      .split(/\r?\n/).filter(Boolean);
    lignes.forEach((ligne) => {
      let ev;
      try { ev = JSON.parse(ligne); } catch (_e) { return; }
      if (ev.evenement === "cycle.depart") {
        courant = null; attente = [ev]; return;
      }
      if (ev.evenement === "cli.depart" && ev.session) {
        courant = ev.session;
        parSession.set(courant, (parSession.get(courant) || []).concat(attente, [ev]));
        attente = [];
        return;
      }
      if (courant) {
        parSession.get(courant).push(ev);
        if (ev.evenement === "cycle.termine") courant = null;
      } else {
        attente.push(ev);
      }
    });
  } catch (_e) { /* aucun run journalise */ }
  return { etat, parSession };
}

function rapportDepuisEntree(entree) {
  const relatif = String((entree && entree.rapport) || "").replace(/\//g, path.sep);
  const fichier = path.resolve(RACINE, relatif);
  if (!fichier.startsWith(path.resolve(DEPOT_ACTIVATIONS) + path.sep)) return null;
  return lireJsonSansFaillir(fichier, null);
}

function transcriptClaude(session) {
  if (!/^[a-zA-Z0-9-]+$/.test(String(session || ""))) return [];
  const projets = path.join(os.homedir(), ".claude", "projects");
  try {
    for (const dossier of fs.readdirSync(projets, { withFileTypes: true })) {
      if (!dossier.isDirectory()) continue;
      const fichier = path.join(projets, dossier.name, session + ".jsonl");
      if (!fs.existsSync(fichier)) continue;
      return fs.readFileSync(fichier, "utf-8").split(/\r?\n/).filter(Boolean)
        .map((ligne) => { try { return JSON.parse(ligne); } catch (_e) { return null; } })
        .filter(Boolean);
    }
  } catch (_e) { /* le journal local Claude peut ne pas exister */ }
  return [];
}

// Le MJ actif n'est pas une nouvelle piece d'etat : Claude ecrit deja son fil
// append-only sous `.claude/projects/<ce projet>/<session>.jsonl`. Plusieurs MJ
// peuvent etre ouverts (un par siege) ; celui qui a parle ou travaille le plus
// recemment est celui que la regie montre. Les narrateurs temporaires des
// activations ont un autre cwd et ne peuvent donc pas gagner cette election.
let cacheFilMjActif = { cle: null, valeur: null };

function texteBlocClaude(bloc) {
  if (typeof bloc === "string") return bloc;
  if (!bloc || typeof bloc !== "object") return "";
  if (typeof bloc.text === "string") return bloc.text;
  if (typeof bloc.content === "string") return bloc.content;
  if (Array.isArray(bloc.content)) return bloc.content.map(texteBlocClaude).filter(Boolean).join("\n");
  return "";
}

function bornerTexteClaude(texte, maximum) {
  texte = String(texte || "");
  return texte.length <= maximum ? texte : texte.slice(0, maximum) + "\n… [suite masquee]";
}

function apercuOutilClaude(bloc) {
  const entree = (bloc && bloc.input) || {};
  return entree.description || entree.command || entree.query || entree.path ||
    (Object.keys(entree).length ? JSON.stringify(entree) : "");
}

function lignesFinFichier(fichier, maximumOctets) {
  const taille = fs.statSync(fichier).size;
  const debut = Math.max(0, taille - maximumOctets);
  const longueur = taille - debut;
  const tampon = Buffer.alloc(longueur);
  const fd = fs.openSync(fichier, "r");
  try { fs.readSync(fd, tampon, 0, longueur, debut); }
  finally { fs.closeSync(fd); }
  let texte = tampon.toString("utf-8");
  if (debut > 0) texte = texte.slice(Math.max(0, texte.indexOf("\n") + 1));
  return texte.split(/\r?\n/).filter(Boolean);
}

function filMjActif() {
  const codeProjet = path.resolve(RACINE).replace(/[:\\/]/g, "-");
  const dossier = path.join(os.homedir(), ".claude", "projects", codeProjet);
  if (!fs.existsSync(dossier)) return { session: null, titre: null, items: [] };
  const candidats = fs.readdirSync(dossier, { withFileTypes: true })
    .filter((e) => e.isFile() && /^[a-zA-Z0-9-]+\.jsonl$/.test(e.name))
    .map((e) => {
      const fichier = path.join(dossier, e.name);
      return { fichier, nom: e.name, stat: fs.statSync(fichier) };
    }).sort((a, b) => b.stat.mtimeMs - a.stat.mtimeMs);
  if (!candidats.length) return { session: null, titre: null, items: [] };
  const choisi = candidats[0];
  const cle = choisi.fichier + ":" + choisi.stat.size + ":" + choisi.stat.mtimeMs;
  if (cacheFilMjActif.cle === cle) return cacheFilMjActif.valeur;

  const session = path.basename(choisi.nom, ".jsonl");
  let titre = null;
  try {
    const fd = fs.openSync(choisi.fichier, "r");
    const tampon = Buffer.alloc(Math.min(65536, choisi.stat.size));
    try { fs.readSync(fd, tampon, 0, tampon.length, 0); }
    finally { fs.closeSync(fd); }
    for (const ligne of tampon.toString("utf-8").split(/\r?\n/)) {
      try {
        const ev = JSON.parse(ligne);
        if (ev.type === "ai-title" && ev.aiTitle) { titre = ev.aiTitle; break; }
      } catch (_e) { /* premiere ligne partielle ou absente */ }
    }
  } catch (_e) { /* le fil reste lisible sans titre */ }

  const items = [];
  lignesFinFichier(choisi.fichier, 2 * 1024 * 1024).forEach((ligne) => {
    let ev;
    try { ev = JSON.parse(ligne); } catch (_e) { return; }
    const moment = ev.timestamp || null;
    if (ev.type === "user" && ev.message) {
      const contenu = ev.message.content;
      if (typeof contenu === "string") {
        const automatique = contenu.match(/^<(task-notification|system-reminder|local-command-[^>]+)>/);
        items.push(automatique
          ? { role: "outil", nom: automatique[1],
              texte: bornerTexteClaude(contenu, 2500), moment }
          : { role: "joueur", texte: bornerTexteClaude(contenu, 6000), moment });
      } else if (Array.isArray(contenu)) {
        contenu.filter((b) => b && b.type === "tool_result").forEach((b) => {
          const texte = texteBlocClaude(b).trim();
          if (texte) items.push({ role: "outil", nom: "resultat",
            texte: bornerTexteClaude(texte, 2500), moment });
        });
      }
      return;
    }
    if (ev.type !== "assistant" || !ev.message || !Array.isArray(ev.message.content)) return;
    ev.message.content.forEach((bloc) => {
      if (!bloc) return;
      if (bloc.type === "text" && bloc.text) {
        items.push({ role: "mj", texte: bornerTexteClaude(bloc.text, 6000), moment });
      } else if (bloc.type === "tool_use") {
        items.push({ role: "outil", nom: bloc.name || "outil",
          texte: bornerTexteClaude(apercuOutilClaude(bloc), 1500), moment });
      }
    });
  });
  const valeur = {
    session, titre: titre || ("MJ " + session.slice(0, 8)),
    modifie_le: choisi.stat.mtime.toISOString(),
    actif: Date.now() - choisi.stat.mtimeMs < 5 * 60 * 1000,
    tronque: choisi.stat.size > 2 * 1024 * 1024,
    items: items.slice(-60),
  };
  cacheFilMjActif = { cle, valeur };
  return valeur;
}

function prevoirActivations() {
  let previsions = { previsions: [], erreur: null };
  try {
    previsions = JSON.parse(childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "boucle_activation.py"), "--prevoir", "8"],
      { cwd: RACINE, encoding: "utf-8", timeout: 5000,
        windowsHide: true, maxBuffer: 2 * 1024 * 1024 }));
  } catch (e) {
    previsions = { previsions: [], erreur: String(e.message || e) };
  }
  return { previsions,
    en_cours: fs.existsSync(path.join(DEPOT_ACTIVATIONS, ".boucle.lock")) };
}

// LA CRITICITE DU PLAN, servie a cote des registres — jamais dedans.
//
// Une colonne « perte » posee dans `books.json` serait effacee au prochain
// `couverture.py`, qui regenere les registres a quatre colonnes exprement pour
// qu'ils ne portent rien de volatil. Or il n'y a pas plus volatil qu'un score :
// il bouge a chaque action cochee. On le CALCULE donc a la demande et l'ecran
// l'ajoute par-dessus le volume, par numero. Les livres restent ce qu'ils sont.
//
// LE CACHE SE CLE SUR LA TAILLE ET LA DATE DE `books.json`, parce que le calcul
// coute une seconde et demie et que la page le redemande a chaque ouverture de
// volume. Une seconde et demie une fois par ecriture du plan, c'est gratuit ;
// une fois par clic, c'est une page qui rame.
const cacheCriticite = new Map();
const cachePlanModele = new Map();

// LE PÉRIMÈTRE DU PLAN VIENT DE PYTHON. L'échiquier garde son rendu détaillé
// en JavaScript, mais il ne redéfinit plus ce qu'est une affaire ni ce que ce
// siège peut voir : `plan_modele.py` est la porte commune aux rapports, au
// bilan, à la criticité et à l'écran.
function planModele(vueDe) {
  const siege = vueDe || "__defaut__";
  const entrees = bibliotheque.cheminsSource(RACINE).concat([
                   path.join(RACINE, "etat", "boites.json"),
                   path.join(RACINE, "etat", "personnages.json"),
                   path.join(RACINE, "etat", "journal.json"),
                   path.join(RACINE, "etat", "actes.json"),
                   path.join(RACINE, "etat", "evenements.json"),
                   path.join(RACINE, "scripts", "bibliotheque.py"),
                   path.join(RACINE, "scripts", "plan_modele.py"),
                   path.join(RACINE, "scripts", "livre.py"),
                   path.join(RACINE, "scripts", "couverture.py")]);
  let cle = "";
  entrees.forEach((f) => {
    try { const s = fs.statSync(f); cle += s.size + ":" + s.mtimeMs + "|"; }
    catch (e) { cle += "?|"; }
  });
  const cache = cachePlanModele.get(siege);
  if (cache && cache.cle === cle) return cache.valeur;
  const valeur = JSON.parse(childProcess.execFileSync("python",
    [path.join(RACINE, "scripts", "plan_modele.py"), "--json"].concat(
      vueDe ? ["--vue-de", vueDe] : []),
    { cwd: RACINE, encoding: "utf-8", timeout: 30000,
      windowsHide: true, maxBuffer: 8 * 1024 * 1024,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) }));
  cachePlanModele.set(siege, { cle, valeur });
  return valeur;
}

function criticite(vueDe) {
  // LA CLE PORTE AUSSI LE SCRIPT, et l'oublier a coute une demi-heure : on
  // ajoute une sortie au calcul, on recharge la page, et l'on relit le cache
  // d'avant sans qu'aucune erreur ne le dise. Un cache dont la clef ne couvre
  // pas le code qui produit la valeur ne se trompe pas de temps en temps : il
  // se trompe exactement quand on travaille dessus.
  // `poids-etats.json` EST une entree du calcul au meme titre que le plan : une
  // note portee de 5 a 8 change tous les scores en aval. L'oublier de la clef
  // donnait un ecran qui ne bougeait pas d'un dixieme apres une renotation, et
  // rien pour le dire — le meme piege que le script oublie, une porte plus loin.
  const cles = bibliotheque.cheminsSource(RACINE).concat([
                path.join(RACINE, "etat", "poids-etats.json"),
                path.join(RACINE, "scripts", "criticite.py"),
                path.join(RACINE, "scripts", "bibliotheque.py"),
                path.join(RACINE, "scripts", "couverture.py"),
                path.join(RACINE, "scripts", "etat_du_plan.py"),
                path.join(RACINE, "scripts", "plan_modele.py"),
                path.join(RACINE, "etat", "boites.json"),
                path.join(RACINE, "etat", "personnages.json")]);
  let cle = "";
  for (const f of cles) {
    try { const s = fs.statSync(f); cle += s.size + ":" + s.mtimeMs + "|"; }
    catch (e) { cle += "?|"; }
  }
  const siege = vueDe || "__defaut__";
  const cache = cacheCriticite.get(siege);
  if (cache && cache.cle === cle) return cache.valeur;
  let valeur;
  try {
    valeur = JSON.parse(childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "criticite.py"), "--json"].concat(
        vueDe ? ["--vue-de", vueDe] : []),
      { cwd: RACINE, encoding: "utf-8", timeout: 30000,
        windowsHide: true, maxBuffer: 8 * 1024 * 1024,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) }));
  } catch (e) {
    valeur = { pas: {}, etats: {}, cercles: [], erreur: String((e && e.message) || e) };
  }
  cacheCriticite.set(siege, { cle, valeur });
  return valeur;
}

// L'audit de coherence, servi a l'ecran au lieu du terminal. `tick.py
// --verifier` produisait deja tout ceci ; personne ne le lisait.
function sante() {
  try {
    const brut = childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "tick.py"), "--verifier", "--json"],
      { cwd: RACINE, encoding: "utf-8", timeout: 30000,
        windowsHide: true, maxBuffer: 8 * 1024 * 1024,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) });
    return Object.assign(JSON.parse(brut), { lu_a: Date.now() });
  } catch (e) {
    // Code de sortie 1 = il Y A des anomalies : c'est le cas nominal, et
    // execFileSync leve quand meme. La sortie est sur stdout, on la lit.
    const sortie = (e && e.stdout) ? String(e.stdout).trim() : "";
    if (sortie.startsWith("{")) {
      try { return Object.assign(JSON.parse(sortie), { lu_a: Date.now() }); }
      catch (_e) { /* tombe dans l'erreur ci-dessous */ }
    }
    return { anomalies: [], durs: 0, notes: 0, par_gravite: {},
             erreur: String((e && e.message) || e), lu_a: Date.now() };
  }
}

// La charge des acteurs : importance contre activations. Le quadrant qui
// compte est « importance haute, zero activation » — les menaces qui
// chargent en silence pendant qu'on regarde ailleurs.
function chargeActeurs() {
  const { etat } = rapportsEtJournalActivations();
  const personnages = lireJsonSansFaillir(path.join(RACINE, "etat", "personnages.json"), []);
  const listeP = Array.isArray(personnages) ? personnages : (personnages.personnages || []);
  const fiches = new Map(listeP.map((p) => [p.id, p]));
  const intentions = lireJsonSansFaillir(path.join(RACINE, "etat", "intentions.json"), []) || [];
  // L'ÉCHELLE NE SE DÉCLARE PLUS, elle se mesure : `evaluer.py --json` dépose
  // la liste des gens du quartier (même composante connexe qu'un siège occupé,
  // vingt minutes de marche au plus). Le champ `echelle` d'intentions.json a
  // disparu — il recopiait à la main ce que la topologie calcule, et mentait
  // dès que l'homme avait bougé.
  const echelles = new Map((Array.isArray(intentions) ? intentions : [])
    .map((t) => [t.personnage_id || t.id, ouQuartier(t.personnage_id || t.id)]));
  const sieges = lireJsonSansFaillir(path.join(RACINE, "etat", "joueurs.json"), []);
  const listeS = (sieges && (sieges.sieges || sieges)) || [];
  const assis = new Set((Array.isArray(listeS) ? listeS : [])
    .filter((s) => s && s.occupe).map((s) => s.personnage_id));

  const base = Number((etat.horloge || {}).base_secondes) || 0;
  const acteurs = Object.entries(etat.acteurs || {}).map(([id, a]) => {
    const fiche = fiches.get(id) || {};
    const repos = Number(a.disponible_a) || 0;
    return {
      id, nom: fiche.nom || id, titre: fiche.titre || "",
      lieu_id: fiche.lieu_id || "",
      importance: Number(a.importance) || 0,
      energie: Number(a.energie) || 0,
      activations: Number(a.activations) || 0,
      echelle: echelles.get(id) || "",
      assis: assis.has(id),
      // Le repos est une date en secondes de monde : ce qui compte a l'ecran,
      // c'est ce qu'il en RESTE a partir de maintenant.
      repos_restant_s: Math.max(0, repos - base),
    };
  });
  acteurs.sort((x, y) => y.importance - x.importance);

  // Le seuil de « ca compte » n'a pas de verite : la mediane des importances
  // non nulles separe mieux que n'importe quelle constante ecrite en dur.
  const vives = acteurs.map((a) => a.importance).filter((v) => v > 0).sort((x, y) => x - y);
  const seuil = vives.length ? vives[Math.floor(vives.length / 2)] : 0;
  return {
    acteurs, seuil,
    total_activations: (etat.historique || []).length,
    tour: (etat.rotation_activation || {}).tour || null,
    lu_a: Date.now(),
  };
}

function resumeActivations() {
  const { etat, parSession } = rapportsEtJournalActivations();
  const personnages = lireJsonSansFaillir(path.join(RACINE, "etat", "personnages.json"), []);
  const liste = Array.isArray(personnages) ? personnages : (personnages.personnages || []);
  const noms = new Map(liste.map((p) => [p.id, p.nom || p.id]));
  const activations = (etat.historique || []).slice().reverse().map((entree) => {
    const rapport = rapportDepuisEntree(entree) || {};
    const activation = rapport.activation || {};
    const meta = rapport._activation || {};
    const session = meta.session || "";
    const journal = parSession.get(session) || [];
    const resultat = journal.slice().reverse().find((x) => x.evenement === "cli.resultat") || {};
    const systeme = journal.find((x) => x.evenement === "cli.systeme") || {};
    const depart = journal.find((x) => x.evenement === "cli.depart") || {};
    const brutResultat = resultat.brut || {};
    const brutSysteme = systeme.brut || {};
    const architecture = meta.session_narrateur ? "narrateur_local" : "legacy_direct";
    return {
      id: session || path.basename(String(entree.rapport || "activation"), ".json"),
      session, qui: entree.qui, nom: noms.get(entree.qui) || entree.qui,
      termine_le: entree.termine_le || meta.cree_le || null,
      tache_id: entree.tache || ((activation.tache || {}).id) || "",
      tache: ((activation.tache || {}).quoi) || entree.tache || "",
      issue: activation.issue || "inconnue",
      activites: (activation.activites || []).length,
      budget: entree.budget == null ? meta.budget : entree.budget,
      depense: entree.depense == null ? activation.energie_depensee : entree.depense,
      duree_monde_secondes: entree.duree_monde_secondes == null
        ? (activation.activites || []).reduce((s, a) =>
            s + Number(((a.temps || {}).duree_s) || 0), 0)
        : entree.duree_monde_secondes,
      restitue: entree.restitue == null ? null : entree.restitue,
      energie_avant: entree.energie_avant == null ? null : entree.energie_avant,
      energie_apres: entree.energie_apres == null ? null : entree.energie_apres,
      importance: entree.importance == null ? meta.importance : entree.importance,
      front: entree.front || meta.front || "",
      duree_ms: meta.duree_ms == null ? brutResultat.duration_ms : meta.duree_ms,
      cout_usd: meta.cout_usd == null ? brutResultat.total_cost_usd : meta.cout_usd,
      modele: meta.modele || brutSysteme.model || "inconnu",
      effort: meta.effort || depart.effort || "inconnu",
      evenements: journal.length,
      architecture,
    };
  });
  return { activations, ...prevoirActivations() };
}

function detailActivation(session) {
  const { etat, parSession } = rapportsEtJournalActivations();
  let entree = null, rapport = null;
  for (const candidate of (etat.historique || [])) {
    const r = rapportDepuisEntree(candidate);
    if (r && r._activation && r._activation.session === session) {
      entree = candidate; rapport = r; break;
    }
  }
  if (!entree || !rapport) return null;
  const meta = rapport._activation || {};
  const architecture = meta.session_narrateur ? "narrateur_local" : "legacy_direct";
  const transcript = transcriptClaude(session);
  const sessionPnj = meta.session_pnj || null;
  const transcriptPnj = sessionPnj ? transcriptClaude(sessionPnj) : [];
  const journal = parSession.get(session) || [];
  const resultat = journal.slice().reverse().find((x) => x.evenement === "cli.resultat") || {};
  const brutResultat = resultat.brut || {};
  let message = meta.message || null;
  if (!message) {
    const envoi = transcript.find((x) => x.type === "queue-operation"
      && x.operation === "enqueue" && typeof x.content === "string");
    const usager = transcript.find((x) => x.type === "user"
      && x.message && typeof x.message.content === "string");
    message = (envoi && envoi.content) || (usager && usager.message.content) || null;
  }
  let reponse = brutResultat.result || null;
  if (!reponse) {
    for (let i = transcript.length - 1; i >= 0 && !reponse; i--) {
      const ev = transcript[i];
      if (ev.type !== "assistant" || !ev.message) continue;
      const contenu = ev.message.content;
      if (typeof contenu === "string") reponse = contenu;
      else if (Array.isArray(contenu)) reponse = contenu
        .filter((b) => b && b.type === "text" && typeof b.text === "string")
        .map((b) => b.text).join("\n");
    }
  }
  return {
    entree, rapport, architecture,
    // La regie ne reconstruit jamais un prompt systeme : il est construit par
    // les constructeurs de depecher.py, puis depose tel quel dans le rapport.
    system_prompt: meta.system_prompt || null,
    message,
    reponse,
    thread: transcript,
    journal,
    pnj: sessionPnj ? {
      session: sessionPnj,
      system_prompt: meta.system_prompt_pnj || null,
      message: meta.appel_pnj || null,
      tentative: meta.tentative_pnj || null,
      thread: transcriptPnj,
    } : null,
    execution: {
      duree_ms: meta.duree_ms == null ? brutResultat.duration_ms : meta.duree_ms,
      cout_usd: meta.cout_usd == null ? brutResultat.total_cost_usd : meta.cout_usd,
      usage: Object.keys(meta.usage || {}).length ? meta.usage : (brutResultat.usage || {}),
      tours: meta.tours == null ? brutResultat.num_turns : meta.tours,
    },
  };
}

module.exports = { numerosDesTetes, ouQuartier, lireJsonSansFaillir, rapportsEtJournalActivations,
  transcriptClaude, filMjActif, prevoirActivations, planModele, criticite, sante,
  chargeActeurs, resumeActivations, detailActivation, DEPOT_ACTIVATIONS };
