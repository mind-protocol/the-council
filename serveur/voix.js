// voix.js — la parole dite. Le viewport demande le son d'une réplique, on le
// prend chez Deepgram avec la voix conçue pour ce personnage (etat/voix.json),
// et on le garde sous voix/cache/ : une réplique déjà dite ne se repaie jamais,
// ni au rechargement de la page, ni au rejeu de l'historique.
//
// Deepgram ne prête que DEUX timbres français — Hector et Agathe. Le reste de la
// distribution se fabrique ici : on demande du linéaire non compressé, et on
// déclare dans l'en-tête WAV une fréquence d'échantillonnage légèrement autre
// que celle du son. Le grand castellan descend d'un ton, le mestre monte ; on
// les reconnaît à l'oreille sans les confondre. Au-delà de ±15 % ça grince, donc
// les facteurs restent serrés (`deepgram.ton` dans le registre).
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const RACINE = path.join(__dirname, "..");
const CACHE = path.join(RACINE, "voix", "cache");
const REGISTRE = path.join(RACINE, "etat", "voix.json");
const ECHANTILLON = 24000;             // ce que Deepgram nous rend vraiment
const MODELE_DEFAUT = "aura-2-hector-fr";

// Deepgram est branché : une phrase absente du cache est synthétisée, puis
// gardée — elle ne se repaie jamais. Lancer le serveur avec VOIX_API=0 coupe le
// robinet : le cache reste servi, le reste revient en 204 et c'est le navigateur
// qui dit la phrase.
const APPELER_API = process.env.VOIX_API !== "0";

function cle() {
  if (process.env.DEEPGRAM_API_KEY) return process.env.DEEPGRAM_API_KEY.trim();
  try {
    for (const ligne of fs.readFileSync(path.join(RACINE, ".env"), "utf-8").split("\n")) {
      if (ligne.startsWith("DEEPGRAM_API_KEY=")) return ligne.slice(17).trim();
    }
  } catch (e) {}
  return null;
}

// L'accord du timbre. Deepgram renvoie un WAV « de flux » : les tailles y sont
// laissées à 0x7fffffff parce qu'il ne les connaît pas d'avance, et un
// navigateur qui lit ça d'un blob ne sait pas où s'arrêter. On les rétablit —
// et pendant qu'on y est, on déclare la fréquence accordée.
function accorder(brut, ton) {
  if (brut.length < 44 || brut.toString("ascii", 0, 4) !== "RIFF") return brut;
  const wav = Buffer.from(brut);
  const canaux = wav.readUInt16LE(22) || 1;
  const bits = wav.readUInt16LE(34) || 16;
  const bloc = (canaux * bits) / 8;
  const rendu = Math.round(ECHANTILLON * (ton || 1));
  wav.writeUInt32LE(rendu, 24);              // fréquence déclarée
  wav.writeUInt32LE(rendu * bloc, 28);       // débit qui va avec
  wav.writeUInt32LE(wav.length - 8, 4);      // taille RIFF réelle
  wav.writeUInt32LE(wav.length - 44, 40);    // taille des données réelle
  return wav;
}

// Le timbre de celui qu'on n'a pas prévu : masculin par défaut faute de savoir,
// et un accord tiré de son id — stable, donc reconnaissable d'une scène à
// l'autre. Une femme qui parlerait ainsi se corrige en une ligne de registre.
function improviser(id) {
  const h = parseInt(crypto.createHash("sha1").update(String(id)).digest("hex").slice(0, 8), 16);
  return { modele: MODELE_DEFAUT, ton: Math.round((0.84 + (h % 23) / 22 * 0.28) * 100) / 100 };
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

async function dire(locuteur_id, texte, client_id, rejouer) {
  const qui = (client_id || "sans-nom").slice(0, 8);
  // Le bail gardait deux écrans de lire la même scène ensemble, du temps où la
  // salle parlait toute seule. Elle ne parle plus qu'au clic : deux écrans ne
  // peuvent se superposer que si deux mains le veulent, et refuser la seconde
  // serait un bouton qui ne fait rien. Un clic passe donc devant le bail — on
  // en garde la trace, pas le veto.
  if (rejouer) bail(client_id);
  else if (!bail(client_id)) {
    const tenu = (lirePartage().parleur || {}).id || "";
    noter({ client: qui, locuteur: locuteur_id, etat: "refus-bail", tenu_par: tenu.slice(0, 8) });
    return { code: 409, erreur: "un autre écran tient la parole" };
  }
  // Personne ne reste muet. Un timbre coûtait cher du temps des voix conçues ;
  // chez Deepgram ce n'est qu'un modèle et un accord, alors un pêcheur qui parle
  // une fois dans la partie a le sien, tiré de son id — donc toujours le même
  // d'une scène à l'autre. Ce qui mérite mieux s'écrit à la main dans le
  // registre, et le registre gagne.
  const fiche = registre()[locuteur_id] || { nom: locuteur_id, deepgram: improviser(locuteur_id) };
  const dit = nettoyer(texte);
  if (!dit) return { code: 400, erreur: "texte vide" };

  const dg = fiche.deepgram || {};
  const modele = dg.modele || MODELE_DEFAUT;
  const ton = Number(dg.ton) || 1;

  const empreinte = crypto.createHash("sha1")
    .update(modele + "|" + ton + "|" + dit).digest("hex").slice(0, 16);
  // `rejouer` : le joueur a survolé la ligne pour l'entendre. Ce n'est pas un
  // doublon du moteur, c'est une demande — la barrière d'écho ne s'applique pas.
  if (!rejouer && dejaDite(empreinte)) {
    noter({ client: qui, locuteur: locuteur_id, etat: "refus-echo", extrait: dit.slice(0, 40) });
    return { code: 409, erreur: "phrase déjà dite" };
  }
  noter({ client: qui, locuteur: locuteur_id, etat: "accorde", extrait: dit.slice(0, 40) });

  const fichier = path.join(CACHE, locuteur_id + "-" + empreinte + ".wav");
  if (fs.existsSync(fichier)) {
    return { code: 200, audio: fs.readFileSync(fichier), mime: "audio/wav", cache: true };
  }

  // Chaque demande vient d'un survol : on synthétise. VOIX_API=0 reste la seule
  // façon de fermer le robinet — le cache se sert encore, et le navigateur dit
  // le reste.
  if (!APPELER_API) {
    noter({ client: qui, locuteur: locuteur_id, etat: "hors-cache", extrait: dit.slice(0, 40) });
    return { code: 204, erreur: "hors cache — au navigateur de le dire" };
  }

  const k = cle();
  if (!k) return { code: 503, erreur: "DEEPGRAM_API_KEY absente" };

  const reponse = await fetch(
    "https://api.deepgram.com/v1/speak?model=" + encodeURIComponent(modele) +
      "&encoding=linear16&container=wav&sample_rate=" + ECHANTILLON,
    {
      method: "POST",
      headers: { Authorization: "Token " + k, "Content-Type": "application/json" },
      body: JSON.stringify({ text: dit }),
    }
  );
  if (!reponse.ok) {
    const detail = await reponse.text();
    noter({ client: qui, locuteur: locuteur_id, etat: "echec-api", code: reponse.status });
    return { code: reponse.status, erreur: detail.slice(0, 300) };
  }
  const audio = accorder(Buffer.from(await reponse.arrayBuffer()), ton);
  fs.mkdirSync(CACHE, { recursive: true });
  fs.writeFileSync(fichier, audio);
  return { code: 200, audio, mime: "audio/wav", cache: false };
}

module.exports = { liste, dire, bail, lireJournal, direLePort };
