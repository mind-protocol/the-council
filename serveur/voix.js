// voix.js — la parole dite. Le viewport demande le son d'une réplique, on le
// prend chez ElevenLabs avec la voix conçue pour ce personnage (etat/voix.json),
// et on le garde sous voix/cache/ : une réplique déjà dite ne se repaie jamais,
// ni au rechargement de la page, ni au rejeu de l'historique.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const RACINE = path.join(__dirname, "..");
const CACHE = path.join(RACINE, "voix", "cache");
const REGISTRE = path.join(RACINE, "etat", "voix.json");
const MODELE = "eleven_multilingual_v2";
const FORMAT = "mp3_44100_128";

// ElevenLabs est branché : une phrase absente du cache est synthétisée, puis
// gardée — elle ne se repaie jamais. Lancer le serveur avec VOIX_API=0 coupe le
// robinet : le cache reste servi, le reste revient en 204 et c'est le navigateur
// qui dit la phrase.
const APPELER_API = process.env.VOIX_API !== "0";

function cle() {
  try {
    for (const ligne of fs.readFileSync(path.join(RACINE, ".env"), "utf-8").split("\n")) {
      if (ligne.startsWith("ELEVENLABS_API_KEY=")) return ligne.split("=")[1].trim();
    }
  } catch (e) {}
  return null;
}

function registre() {
  try { return JSON.parse(fs.readFileSync(REGISTRE, "utf-8")); } catch (e) { return {}; }
}

// Le bail de parole. Deux écrans ouverts sur la partie — deux onglets, deux
// navigateurs, la fenêtre du jeu et un aperçu oublié — suivent le même flux et
// liraient la même phrase ensemble. C'est ici qu'on tranche, et pas dans le
// navigateur : c'est le seul endroit qui les voit tous.
// Le bail vit dans un FICHIER, pas dans la mémoire du processus. Rien ne garantit
// qu'il n'y ait qu'un serveur : une relance qui trouve le port occupé démarre
// ailleurs, et deux instances ont chacune leur mémoire — chacune accordait la
// parole de son côté, et la salle parlait en double. Le disque, lui, est commun.
const BAIL_MS = 6000;
const ECHO_MS = 45000;
const PARTAGE = path.join(RACINE, "etat", "voix-bail.json");

function lirePartage() {
  try { return JSON.parse(fs.readFileSync(PARTAGE, "utf-8")); }
  catch (e) { return { parleur: { id: null, t: 0 }, dites: {} }; }
}

function ecrirePartage(etat) {
  const t = Date.now();
  for (const k in etat.dites) if (t - etat.dites[k] > ECHO_MS) delete etat.dites[k];
  try {
    fs.mkdirSync(path.dirname(PARTAGE), { recursive: true });
    fs.writeFileSync(PARTAGE, JSON.stringify(etat), "utf-8");
  } catch (e) {}
}

function bail(client_id) {
  if (!client_id) return true;           // un client d'avant le bail : on ne le bâillonne pas
  const etat = lirePartage();
  const t = Date.now();
  const p = etat.parleur || { id: null, t: 0 };
  if (p.id && p.id !== client_id && t - p.t < BAIL_MS) return false;
  etat.parleur = { id: client_id, t: t };
  ecrirePartage(etat);
  return true;
}

// Seconde barrière, indépendante du bail et partagée elle aussi : une même
// phrase ne se dit pas deux fois. Peu importe qui la redemande — un autre écran,
// un autre serveur, un rechargement, un module qui appelle deux fois — le son
// n'est servi qu'une fois par fenêtre de temps. Le texte, lui, reste affiché.
function dejaDite(empreinte) {
  const etat = lirePartage();
  const t = Date.now();
  const vue = (etat.dites || {})[empreinte];
  if (vue && t - vue < ECHO_MS) return true;
  etat.dites = etat.dites || {};
  etat.dites[empreinte] = t;
  ecrirePartage(etat);
  return false;
}

// De quoi diagnostiquer sans deviner : qui a demandé quoi, et ce qu'on a répondu.
const journal = [];
function noter(entree) {
  journal.push(Object.assign({ t: new Date().toISOString() }, entree));
  if (journal.length > 80) journal.shift();
}
function lireJournal() {
  const etat = lirePartage();
  return {
    pid: process.pid,
    port_servi: PORT_SERVI,
    parleur: etat.parleur,
    phrases_en_memoire: Object.keys(etat.dites || {}).length,
    journal: journal.slice(-40),
  };
}

// Renseigné par serveur.js au démarrage : savoir QUEL serveur répond est la
// première question à poser quand la salle parle en double.
let PORT_SERVI = null;
function direLePort(p) { PORT_SERVI = p; }

// Ce que le viewport a le droit d'espérer : qui a une voix, et si la clé est là.
function liste() {
  const r = registre();
  const voix = {};
  for (const id in r) voix[id] = { nom: r[id].nom };
  return { voix, disponible: !!cle() };
}

// Le texte tel qu'il se dit : les guillemets et les tirets de dialogue sont de
// la typographie, pas de la parole.
function nettoyer(texte) {
  return String(texte || "")
    .replace(/[«»“”]/g, "")
    .replace(/^\s*[—–-]\s*/, "")
    .replace(/\s+/g, " ")
    .trim();
}

async function dire(locuteur_id, texte, client_id) {
  const qui = (client_id || "sans-nom").slice(0, 8);
  if (!bail(client_id)) {
    const tenu = (lirePartage().parleur || {}).id || "";
    noter({ client: qui, locuteur: locuteur_id, etat: "refus-bail", tenu_par: tenu.slice(0, 8) });
    return { code: 409, erreur: "un autre écran tient la parole" };
  }
  const fiche = registre()[locuteur_id];
  if (!fiche) return { code: 404, erreur: "aucune voix conçue pour " + locuteur_id };
  const dit = nettoyer(texte);
  if (!dit) return { code: 400, erreur: "texte vide" };

  const empreinte = crypto.createHash("sha1")
    .update(fiche.voice_id + "|" + MODELE + "|" + dit).digest("hex").slice(0, 16);
  if (dejaDite(empreinte)) {
    noter({ client: qui, locuteur: locuteur_id, etat: "refus-echo", extrait: dit.slice(0, 40) });
    return { code: 409, erreur: "phrase déjà dite" };
  }
  noter({ client: qui, locuteur: locuteur_id, etat: "accorde", extrait: dit.slice(0, 40) });

  const fichier = path.join(CACHE, locuteur_id + "-" + empreinte + ".mp3");
  if (fs.existsSync(fichier)) return { code: 200, audio: fs.readFileSync(fichier), cache: true };

  if (!APPELER_API) {
    noter({ client: qui, locuteur: locuteur_id, etat: "hors-cache", extrait: dit.slice(0, 40) });
    return { code: 204, erreur: "hors cache — au navigateur de le dire" };
  }

  const k = cle();
  if (!k) return { code: 503, erreur: "ELEVENLABS_API_KEY absente" };

  const reponse = await fetch(
    "https://api.elevenlabs.io/v1/text-to-speech/" + fiche.voice_id + "?output_format=" + FORMAT,
    {
      method: "POST",
      headers: { "xi-api-key": k, "Content-Type": "application/json" },
      body: JSON.stringify({
        text: dit,
        model_id: MODELE,
        voice_settings: { stability: 0.45, similarity_boost: 0.8, use_speaker_boost: true },
      }),
    }
  );
  if (!reponse.ok) {
    const detail = await reponse.text();
    return { code: reponse.status, erreur: detail.slice(0, 300) };
  }
  const audio = Buffer.from(await reponse.arrayBuffer());
  fs.mkdirSync(CACHE, { recursive: true });
  fs.writeFileSync(fichier, audio);
  return { code: 200, audio, cache: false };
}

module.exports = { liste, dire, bail, lireJournal, direLePort };
