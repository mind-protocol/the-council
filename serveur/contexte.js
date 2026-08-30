// Le socle : la racine du dépôt, le port, la fenêtre de fil, et les chemins de
// l'état — où lire les croyances d'un siège, son heure, ses notes. Rien qui
// connaisse `req` ou `res` : le transport est dans http.js, le brouillard dans
// siege.js.

// Les tests d'intégration servent une partie miniature dans un dossier
// temporaire. En production, l'absence de variable garde le dépôt courant.

const fs = require("fs");
const path = require("path");
const childProcess = require("child_process");

const RACINE = process.env.CONSEIL_RACINE
  ? path.resolve(process.env.CONSEIL_RACINE) : path.join(__dirname, "..");

// 3129 est le port du jeu. Un atelier (vérification d'écran pendant qu'une
// partie tourne) passe un port en argument ou par PORT, pour ne pas se
// disputer le port de la partie en cours.
const PORT = Number(process.argv[2]) || Number(process.env.PORT) || 3129;

// Longueur d'une fenêtre de fil servie au navigateur. Le reste du passé se
// réclame page par page (`/scene?avant=N`) quand le joueur remonte la
// chronique. Le fichier, lui, garde tout — c'est la mémoire de la partie.
//
// 500 était trop : rien n'est perdu, mais tout est MONTÉ. Cinq cents entrées
// font autant de nœuds vivants dans la chronique, avec leurs vieillissements
// et leurs survols, et le défilement se paie à chaque image.
//
// 80 est calé sur la SCÈNE et non sur la session : un conseil fait une
// quarantaine de répliques, donc la fenêtre porte celle qu'on joue et celle
// d'avant. Ce qui précède est du passé qu'on relit, et il redescend tout seul
// quand on remonte (`/scene?avant=N`). Descendre plus bas ferait paginer à
// l'intérieur d'une même scène — c'est là qu'est la limite, pas dans le coût.
const MAX_FIL = 80;

// ---- les croyances, une par joueur --------------------------------------
// `vues`, `jetons`, `objectifs` ne décrivent pas le monde : ils décrivent ce
// qu'UN joueur croit du monde. À deux, les partager revient à donner la table
// de guerre de la reine à sa maîtresse de la voix. Chacun a donc son dossier —
// `etat/joueurs/<personnage_id>/` — et l'on retombe sur `etat/` quand il existe
// encore : une partie seule ne voit aucune différence.
//
// Le repli racine peut être absent (archivé une fois les deux joueuses
// migrées) : on rend alors null plutôt qu'un chemin qui n'ouvre rien. Un
// visiteur sans jeton n'a AUCUNE croyance à lui — il ne doit pas hériter de
// celles d'autrui, et une table vide est la seule réponse honnête.
function cheminEtat(nom, siege) {
  if (siege) {
    const p = path.join(RACINE, "etat", "joueurs", siege.personnage_id, nom);
    if (fs.existsSync(p)) return p;
  }
  const racineNom = path.join(RACINE, "etat", nom);
  return fs.existsSync(racineNom) ? racineNom : null;
}

// Les notes du joueur — un carnet HORS FICTION. Ce n'est pas un livre du monde
// et ce n'est pas une croyance : personne dans la salle ne l'écrit, aucun PNJ
// ne le lit, le MJ n'y touche pas. Du texte brut, gardé tel quel, un fichier
// par siège — ce que la reine griffonne n'est pas ce que griffonne sa
// maîtresse de la voix. Contrairement à `cheminEtat`, on rend le chemin où le
// fichier DEVRA s'écrire, même s'il n'existe pas encore.
function cheminNotes(siege) {
  return siege
    ? path.join(RACINE, "etat", "joueurs", siege.personnage_id, "notes.txt")
    : path.join(RACINE, "etat", "notes.txt");
}

// Les croyances du demandeur, ou le défaut fourni quand il n'en a pas.
function lireCroyance(nom, siege, defaut) {
  const p = cheminEtat(nom, siege);
  if (!p) return defaut;
  try { return JSON.parse(fs.readFileSync(p, "utf-8")); } catch (e) { return defaut; }
}

// L'heure de CE joueur. Le front de chacun vit dans `etat/horloges.json`
// (tenu par scripts/append_flux.py) ; `monde.date` n'est que le minimum des
// fronts — la date acquise pour tout le monde, celle du tick. Servir celle-là
// au navigateur ferait vieillir la carte d'un joueur au rythme du plus lent.
function dateDe(siege) {
  let monde = null;
  try { monde = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "monde.json"), "utf-8")).date || null; } catch (e) {}
  if (!siege) return monde;
  try {
    const h = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "horloges.json"), "utf-8"));
    if (h && h[siege.personnage_id]) return h[siege.personnage_id];
  } catch (e) {}
  return monde;
}

// OÙ EST TOUT LE MONDE, à cette minute-là — le calcul, pas le cache.
// `scripts/presence.py --json` fait le travail : routines, topologie, marche en
// cours. On ne le refait pas à chaque sonde (le navigateur en tire une toutes
// les quinze secondes, et par siège) : la réponse vaut tant que ni l'heure
// demandée ni les trois fichiers d'entrée n'ont bougé. Un échec rend null, et
// l'appelant retombe sur l'instantané figé — le jeu ne s'arrête pas pour ça.
let cachePresence = null;
function resoudrePresence(date) {
  if (!date) return null;
  let cle = [date.annee, date.lune, date.jour, date.minute].join(".");
  for (const f of ["presence.json", "routines.json", "chemins.json"]) {
    try { const s = fs.statSync(path.join(RACINE, "etat", f)); cle += "|" + s.mtimeMs; }
    catch (e) { cle += "|?"; }
  }
  if (cachePresence && cachePresence.cle === cle) return cachePresence.gens;
  let gens = null;
  try {
    gens = JSON.parse(childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "presence.py"), "--json", "--quand", cle.split("|")[0]],
      { cwd: RACINE, encoding: "utf-8", timeout: 20000,
        windowsHide: true, maxBuffer: 8 * 1024 * 1024,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) })).gens || null;
  } catch (e) { gens = null; }
  cachePresence = { cle, gens };
  return gens;
}

module.exports = { RACINE, PORT, MAX_FIL, cheminEtat, cheminNotes, lireCroyance, dateDe, resoudrePresence };
