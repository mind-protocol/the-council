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
// Le camp est le NOIR pour tout siège — la partie n'a pas encore d'amorce qui
// nomme ses camps par siège, et l'on ne devine pas.
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");
const { RACINE } = require("../http");

const DOSSIER = path.join(RACINE, "etat", "parties");

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
  const args = [path.join(RACINE, "scripts", "partie.py"), id, "--cartes",
                "--camp", camp || "noir", "--vu", String(vu || 0)];
  execFile(process.env.PYTHON || "python", args,
    { cwd: RACINE, timeout: 20000, maxBuffer: 8 * 1024 * 1024, windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) },
    (err, stdout, stderr) => {
      if (err) return cb(new Error(String(stderr || err.message || "").slice(0, 600)));
      try { return cb(null, JSON.parse(String(stdout))); }
      catch (e) { return cb(new Error("vue illisible : " + String(stdout).slice(0, 200))); }
    });
}

// Joue un geste et rend la position d'APRÈS par `cb(erreur, resultat)`.
// `resultat` porte `ok`, `refus[]`, `dit`, `avertissements[]` et `vue` — le
// greffier a déjà vérifié, et un refus n'est PAS une erreur de transport : il
// revient en 200 avec sa raison en clair, parce que c'est une réponse de jeu et
// qu'elle s'affiche sous la carte.
function jouer(url, camp, geste, cb, vu) {
  const id = partieDe(url);
  if (!id) return cb(null, { ok: false, refus: ["aucune partie ouverte"], vue: null });
  const args = [path.join(RACINE, "scripts", "partie.py"), id, "--geste",
                JSON.stringify(Object.assign({ camp: camp || "noir" }, geste)),
                "--camp", camp || "noir", "--vu", String(vu || 0)];
  execFile(process.env.PYTHON || "python", args,
    { cwd: RACINE, timeout: 20000, maxBuffer: 8 * 1024 * 1024, windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) },
    (err, stdout, stderr) => {
      if (err) return cb(new Error(String(stderr || err.message || "").slice(0, 600)));
      try { return cb(null, JSON.parse(String(stdout))); }
      catch (e) { return cb(new Error("réponse illisible : " + String(stdout).slice(0, 200))); }
    });
}

// CE QUI A DÉJÀ ÉTÉ VU, par siège. Le jsonl est append-only : un seul entier
// suffit à dire exactement ce qui est neuf, et il survit à un rechargement
// comme à deux jours d'absence. Il n'avance qu'au moment où le joueur JOUE —
// on a agi, donc on a regardé ; entre deux de ses coups, tout ce que l'autre
// camp a fait reste marqué. C'est ce qui évite un bouton « j'ai vu ».
function cheminVu(siege, id) {
  const qui = (siege && siege.personnage_id) || "joueur";
  return path.join(RACINE, "etat", "joueurs", qui, "partie-" + id + ".json");
}

function vuDe(siege, id) {
  try { return parseInt(JSON.parse(fs.readFileSync(cheminVu(siege, id), "utf-8")).vu, 10) || 0; }
  catch (e) { return 0; }
}

function poserVu(siege, id, n) {
  try {
    const c = cheminVu(siege, id);
    fs.mkdirSync(path.dirname(c), { recursive: true });
    fs.writeFileSync(c, JSON.stringify({
      vu: n,
      _: "Le dernier numéro de ligne de cette partie que ce siège a vu. " +
         "Tout ce qui est écrit après porte `neuf` sur le plateau. Avance " +
         "quand le joueur joue un coup, jamais à la simple lecture.",
    }, null, 2), "utf-8");
  } catch (e) { /* ne pas perdre un coup pour un marque-page */ }
}

module.exports = { partieDe, vue, jouer, vuDe, poserVu, DOSSIER };
