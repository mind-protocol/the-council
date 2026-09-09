// LA PARTIE D'UN SIÈGE — quel jsonl, quel camp, et la vue en cartes.
//
// Le calcul vit chez le greffier (scripts/partie.py --cartes, matière dans
// scripts/noyau/partie_cartes.py) : ici on ne fait que choisir le fichier et
// appeler Python, pour que la même vue serve le terminal et l'écran.
//
// QUELLE PARTIE : `?id=` d'abord, puis celle que `_courante.json` NOMME. On a
// commencé par « la plus récemment modifiée », et c'est faux dès qu'il y a deux
// parties : un banc d'essai touché par une autre session prend la place de la
// partie qu'on joue, sans rien dire. Le MJ nomme la partie en l'ouvrant.
// QUEL CAMP : `?camp=` d'abord, puis celui que `_courante.json` NOMME, sinon
// rien — et sans `--camp`, le greffier prend le premier camp de la partie. On
// envoyait « noir » à tout siège : sur une partie sans camp noir, le deck était
// vide et chaque geste refusé, sans qu'on sache pourquoi.
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");
const { RACINE } = require("../http");

const DOSSIER = path.join(RACINE, "etat", "parties");

// LES CAMPS QUI ONT DEJA JOUE dans cette partie, lus du jsonl. Le greffe
// accepte N camps et n'a donc aucune raison de refuser un nom neuf — c'est
// voulu. Mais l'ECRAN, lui, doit savoir qu'un `?camp=` inconnu est une adresse
// perimee et non un camp qui entre : c'est arrive le 5.9, l'onglet etait reste
// sur `?camp=nicolas` du pont et du moulin, et une demande du tueur est tombee
// dans un camp fantome au milieu d'un crime de cour.
function campsDe(id) {
  try {
    const brut = fs.readFileSync(path.join(DOSSIER, id + ".jsonl"), "utf-8");
    const out = new Set();
    // UN CAMP QUI N'A PAS ENCORE VISE EXISTE QUAND MEME s'il est NOMME par la
    // configuration de la partie (`camps` de etat/parties/<id>.json, 6.9) :
    // c'est le cas de l'ouverture depuis l'ecran, ou la racine est le premier
    // geste — sans cela, poser sa racine etait refuse faute de racine.
    try {
      const conf = JSON.parse(fs.readFileSync(path.join(DOSSIER, id + ".json"), "utf-8"));
      (conf.camps || []).forEach((c) => out.add(String(c)));
    } catch (e) {}
    for (const l of brut.split("\n")) {
      if (!l.trim()) continue;
      // CE QUI FAIT UN CAMP, C'EST D'AVOIR VISE — pas d'avoir ecrit. Le premier
      // jet retenait tout camp ayant depose une ligne, si bien qu'un camp
      // fantome se validait lui-meme des sa premiere faute : c'est exactement
      // le cas qu'on ferme. Un camp qui joue a une racine, et l'arbitre passe
      // toujours.
      try {
        const o = JSON.parse(l);
        if (o && o.camp && (o.coup === "viser" || o.camp === "arbitre")) out.add(String(o.camp));
      } catch (e) {}
    }
    return out;
  } catch (e) { return new Set(); }
}

function campDe(url) {
  const q = new URLSearchParams((url.split("?")[1] || ""));
  const c = (q.get("camp") || "").replace(/[^A-Za-z0-9_-]/g, "");
  if (c) return c;
  try {
    const cour = JSON.parse(fs.readFileSync(path.join(DOSSIER, "_courante.json"), "utf-8"));
    const n = String(cour && cour.camp || "").replace(/[^A-Za-z0-9_-]/g, "");
    if (n) return n;
  } catch (e) {}
  return null;
}

function partieDe(url) {
  const q = new URLSearchParams((url.split("?")[1] || ""));
  const id = (q.get("id") || "").replace(/[^A-Za-z0-9_-]/g, "");
  if (id && fs.existsSync(path.join(DOSSIER, id + ".jsonl"))) return id;
  try {
    const c = JSON.parse(fs.readFileSync(path.join(DOSSIER, "_courante.json"), "utf-8"));
    const n = String(c && c.partie || "").replace(/[^A-Za-z0-9_-]/g, "");
    if (n && fs.existsSync(path.join(DOSSIER, n + ".jsonl"))) return n;
  } catch (e) {}
  let fichiers;
  try { fichiers = fs.readdirSync(DOSSIER).filter((f) => f.endsWith(".jsonl")); }
  catch (e) { return null; }
  if (!fichiers.length) return null;
  fichiers.sort((a, b) => fs.statSync(path.join(DOSSIER, b)).mtimeMs
                        - fs.statSync(path.join(DOSSIER, a)).mtimeMs);
  return fichiers[0].replace(/\.jsonl$/, "");
}

// Rend la vue par `cb(erreur, vue)`. Une partie absente rend une vue vide,
// jamais une erreur : l'onglet doit pouvoir s'ouvrir sur rien.
function vue(url, camp, cb, vu) {
  const id = partieDe(url);
  if (!id) return cb(null, { partie: null, camp: camp, fronts: [], desseins: [],
                             deck: { main: [], route: [], remet: [], posees: [], detruites: [] } });
  camp = camp || campDe(url);
  const args = [path.join(RACINE, "scripts", "partie.py"), id, "--cartes",
                "--vu", String(vu || 0)].concat(camp ? ["--camp", camp] : []);
  execFile(process.env.PYTHON || "python", args,
    { cwd: RACINE, timeout: 20000, maxBuffer: 8 * 1024 * 1024, windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) },
    (err, stdout, stderr) => {
      if (err) return cb(new Error(derniereLigne(stderr, err)));
      try { return cb(null, JSON.parse(String(stdout))); }
      catch (e) { return cb(new Error("vue illisible : " + String(stdout).slice(0, 200))); }
    });
}

// Joue un geste et rend la position d'APRÈS par `cb(erreur, resultat)`.
// `resultat` porte `ok`, `refus[]`, `dit`, `avertissements[]` et `vue` — le
// greffier a déjà vérifié, et un refus n'est PAS une erreur de transport : il
// revient en 200 avec sa raison en clair, parce que c'est une réponse de jeu et
// qu'elle s'affiche sous la carte.
//
// LE CAMP DU SERVEUR PRIME SUR LE CORPS (audit du 7.9, B1). On faisait
// `Object.assign({ camp }, geste)` : un `camp` glisse dans le JSON du client
// ecrasait celui que le serveur avait resolu, et n'importe quel onglet pouvait
// passer pour l'adversaire — ou pour l'arbitre. La route refuse deja un camp
// du corps qui differe ; ici on l'ecrase quoi qu'il arrive.
//
// UNE FILE PAR PARTIE (audit du 7.9, B5 / A6). Chaque coup est un `python`
// qui relit le jsonl, calcule `n = dernier + 1` et ajoute une ligne : deux
// POST simultanes sur la meme partie donnaient deux lignes de meme `n`
// (charmed-2 n=106, 118, 122 ; successeurs n=55). Les coups d'une meme partie
// passent donc l'un apres l'autre ; deux parties differentes ne s'attendent pas.
function jouer(url, camp, geste, cb, vu) {
  const id = partieDe(url);
  if (!id) return cb(null, { ok: false, refus: ["aucune partie ouverte"], vue: null });
  camp = camp || campDe(url);
  const args = [path.join(RACINE, "scripts", "partie.py"), id, "--geste",
                JSON.stringify(camp ? Object.assign({}, geste, { camp: camp }) : geste),
                "--vu", String(vu || 0)].concat(camp ? ["--camp", camp] : []);
  enFile(id, (fin) => {
    execFile(process.env.PYTHON || "python", args,
      { cwd: RACINE, timeout: 20000, maxBuffer: 8 * 1024 * 1024, windowsHide: true,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) },
      (err, stdout, stderr) => {
        try {
          if (err) return cb(new Error(derniereLigne(stderr, err)));
          let r;
          try { r = JSON.parse(String(stdout)); }
          catch (e) { return cb(new Error("réponse illisible : " + String(stdout).slice(0, 200))); }
          return cb(null, r);
        } finally { fin(); }
      });
  });
}

// La file d'attente : une promesse chainee par identifiant de partie. Le
// travail recoit `fin`, qu'il DOIT appeler quand le greffe a rendu la main ;
// le suivant ne part qu'apres. La file d'une partie disparait quand elle est
// vide, pour ne pas garder une entree par partie jamais rejouee.
const FILES = new Map();
function enFile(id, travail) {
  const avant = FILES.get(id) || Promise.resolve();
  const courant = avant.then(() => new Promise((fin) => {
    try { travail(fin); } catch (e) { fin(); throw e; }
  })).catch(() => {});
  FILES.set(id, courant);
  courant.then(() => { if (FILES.get(id) === courant) FILES.delete(id); });
}

// UN TRACEBACK PYTHON NE SE MONTRE PAS EN ENTIER : sa derniere ligne non vide
// (« KeyError: 'b1' », « json.decoder.JSONDecodeError: … ») dit tout ce qu'un
// ecran peut en faire. Le reste est pour le terminal du greffe.
function derniereLigne(stderr, err) {
  const lignes = String(stderr || "").split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const texte = lignes.length ? lignes[lignes.length - 1]
                              : String((err && err.message) || "le greffe n'a rien dit");
  return texte.slice(0, 300);
}

// LE RUBAN : la partie dans le temps (scripts/noyau/partie_ruban.py), rendue à
// la demande sur la partie courante ou `?id=`. Jamais écrit sur disque : il
// suit le jsonl, qui est déjà l'histoire complète.
function ruban(url, cb) {
  const id = partieDe(url);
  if (!id) return cb(null, "<p>aucune partie ouverte</p>");
  execFile(process.env.PYTHON || "python",
    [path.join(RACINE, "scripts", "partie.py"), id, "--ruban", "-"],
    { cwd: RACINE, timeout: 20000, maxBuffer: 16 * 1024 * 1024, windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) },
    (err, stdout, stderr) => err ? cb(new Error(derniereLigne(stderr, err)))
                                 : cb(null, String(stdout)));
}

// CE QUI A DÉJÀ ÉTÉ VU, par siège. Le jsonl est append-only : un seul entier
// suffit à dire exactement ce qui est neuf, et il survit à un rechargement
// comme à deux jours d'absence. Il n'avance qu'au moment où le joueur JOUE —
// on a agi, donc on a regardé ; entre deux de ses coups, tout ce que l'autre
// camp a fait reste marqué. C'est ce qui évite un bouton « j'ai vu ».
function cheminVu(siege, id, camp) {
  const qui = (siege && siege.personnage_id) || "joueur";
  // LE CAMP FAIT PARTIE DU MARQUE-PAGE. Deux joueurs devant la même machine
  // partagent le siège : sans le camp, ils partageaient aussi le « déjà vu »,
  // et le coup de l'un effaçait la relecture de l'autre. Un plateau sans camp
  // nommé garde l'ancien chemin, pour ne pas perdre les marque-pages posés.
  const c = String(camp || "").replace(/[^A-Za-z0-9_-]/g, "");
  return path.join(RACINE, "etat", "joueurs", qui,
                   "partie-" + id + (c ? "-" + c : "") + ".json");
}

function vuDe(siege, id, camp) {
  try { return parseInt(JSON.parse(fs.readFileSync(cheminVu(siege, id, camp), "utf-8")).vu, 10) || 0; }
  catch (e) { return 0; }
}

function poserVu(siege, id, n, camp) {
  try {
    const c = cheminVu(siege, id, camp);
    fs.mkdirSync(path.dirname(c), { recursive: true });
    fs.writeFileSync(c, JSON.stringify({
      vu: n,
      _: "Le dernier numéro de ligne de cette partie que ce siège a vu. " +
         "Tout ce qui est écrit après porte `neuf` sur le plateau. Avance " +
         "quand le joueur joue un coup, jamais à la simple lecture.",
    }, null, 2), "utf-8");
  } catch (e) { /* ne pas perdre un coup pour un marque-page */ }
}

module.exports = { partieDe, campDe, campsDe, vue, jouer, ruban, vuDe, poserVu, DOSSIER };
