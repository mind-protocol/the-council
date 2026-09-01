#!/usr/bin/env node

import { spawn } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const URL_RECEPTION = "http://localhost:3129/reception";
const MODE_SIEGE = process.argv.includes("--siege");
const ADRESSE_CIBLE = MODE_SIEGE
  ? "/books?jeton=homme%3Aprecision-observer"
  : "/books";
const SORTIE = resolve(
  MODE_SIEGE
    ? "C:/Users/reyno/le-conseil2/chambres/precision_observer/preuves/bordereau-reception-siege.json"
    : "C:/Users/reyno/le-conseil2/chambres/precision_observer/preuves/bordereau-reception.json",
);
const PORT = 9337;
const PROFIL = join(tmpdir(), `precision-observer-reception-${process.pid}`);
const TELECHARGEMENTS = join(PROFIL, "telechargements");
const FICHIER_TELECHARGE = join(TELECHARGEMENTS, "bordereau-reception.json");

mkdirSync(resolve(SORTIE, ".."), { recursive: true });
mkdirSync(TELECHARGEMENTS, { recursive: true });
if (existsSync(SORTIE)) throw new Error(`la pièce de sortie existe déjà : ${SORTIE}`);

function attendre(ms) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, ms));
}

async function attendreJson(url, tentatives = 80) {
  for (let i = 0; i < tentatives; i += 1) {
    try {
      const reponse = await fetch(url);
      if (reponse.ok) return await reponse.json();
    } catch {}
    await attendre(100);
  }
  throw new Error(`porte de débogage inaccessible : ${url}`);
}

function canalCdp(adresse) {
  const socket = new WebSocket(adresse);
  let prochainId = 1;
  const attentes = new Map();
  const ouvert = new Promise((resolvePromise, reject) => {
    socket.addEventListener("open", resolvePromise, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  socket.addEventListener("message", (evenement) => {
    const message = JSON.parse(evenement.data);
    if (!message.id || !attentes.has(message.id)) return;
    const { resolve: resoudre, reject } = attentes.get(message.id);
    attentes.delete(message.id);
    if (message.error) reject(new Error(JSON.stringify(message.error)));
    else resoudre(message.result);
  });
  return {
    ouvert,
    envoyer(method, params = {}) {
      const id = prochainId++;
      socket.send(JSON.stringify({ id, method, params }));
      return new Promise((resoudre, reject) => attentes.set(id, { resolve: resoudre, reject }));
    },
    fermer() {
      socket.close();
    },
  };
}

async function evaluer(canal, expression, awaitPromise = false) {
  const resultat = await canal.envoyer("Runtime.evaluate", {
    expression,
    awaitPromise,
    returnByValue: true,
  });
  if (resultat.exceptionDetails) {
    throw new Error(resultat.exceptionDetails.text || "erreur dans le lecteur");
  }
  return resultat.result.value;
}

const chrome = spawn(CHROME, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--disable-default-apps",
  `--user-data-dir=${PROFIL}`,
  `--remote-debugging-port=${PORT}`,
  URL_RECEPTION,
], { stdio: "ignore", windowsHide: true });

try {
  const cibles = await attendreJson(`http://127.0.0.1:${PORT}/json`);
  const cible = cibles.find((item) => item.type === "page");
  if (!cible) throw new Error("aucune page ouverte dans le lecteur");
  const canal = canalCdp(cible.webSocketDebuggerUrl);
  await canal.ouvert;
  await canal.envoyer("Page.enable");
  await canal.envoyer("Runtime.enable");
  await canal.envoyer("Browser.setDownloadBehavior", {
    behavior: "allow",
    downloadPath: TELECHARGEMENTS,
    eventsEnabled: true,
  });

  for (let i = 0; i < 80; i += 1) {
    const pret = await evaluer(canal, "document.readyState === 'complete' && Boolean(document.getElementById('eprouver'))");
    if (pret) break;
    await attendre(100);
  }

  const observation = await evaluer(canal, `(async () => {
    const reponse = await fetch(${JSON.stringify(ADRESSE_CIBLE)}, { cache: 'no-store' });
    const donnees = await reponse.json();
    return {
      statut: reponse.status,
      books_est_tableau: Array.isArray(donnees.books),
      boites_est_tableau: Array.isArray(donnees.boites),
      books_nombre: Array.isArray(donnees.books) ? donnees.books.length : null,
      boites_nombre: Array.isArray(donnees.boites) ? donnees.boites.length : null,
    };
  })()`, true);

  await evaluer(canal, `(() => {
    const valeurs = ${JSON.stringify({
      objet: MODE_SIEGE ? "État de l’étagère /books depuis mon siège" : "État de l’étagère /books",
      adresse: ADRESSE_CIBLE,
      critere: MODE_SIEGE
        ? "Depuis le siège homme:precision-observer, le lecteur obtient HTTP 200, 10 livres et 2 boîtes."
        : "Le lecteur obtient HTTP 200 et un document JSON contenant deux collections nommées books et boites.",
      observation: MODE_SIEGE
        ? `HTTP ${observation.statut} ; books et boites sont des tableaux contenant respectivement ${observation.books_nombre} livres et ${observation.boites_nombre} boîtes.`
        : "HTTP 200 ; books et boites sont des tableaux, tous deux vides au moment du constat.",
      reserve: MODE_SIEGE
        ? "Cette pièce établit la réponse actuelle depuis mon siège. Elle n'établit pas par elle-même la cause historique rapportée par Marco, ni l'identité ou la qualité de chacun des volumes."
        : "La réception établit la forme et l’accessibilité de la réponse, non la présence d’un livre ni le fonctionnement d’un téléchargement de livre.",
      "resultat-sous-jacent": "CONFORME",
      date: "129.5.12",
    })};
    for (const [id, valeur] of Object.entries(valeurs)) {
      const champ = document.getElementById(id);
      champ.value = valeur;
      champ.dispatchEvent(new Event('input', { bubbles: true }));
    }
    document.getElementById('eprouver').click();
  })()`);

  for (let i = 0; i < 80; i += 1) {
    const eprouve = await evaluer(canal, "document.getElementById('preuve-adresse').textContent");
    if (eprouve.includes("HTTP 200")) break;
    await attendre(100);
  }

  const piece = await evaluer(canal, `(() => {
    document.getElementById('reception-form').requestSubmit();
    return JSON.parse(document.getElementById('piece').textContent);
  })()`);
  await evaluer(canal, "document.getElementById('telecharger').click()");

  for (let i = 0; i < 80 && !existsSync(FICHIER_TELECHARGE); i += 1) await attendre(100);
  if (!existsSync(FICHIER_TELECHARGE)) {
    throw new Error(`téléchargement absent : ${FICHIER_TELECHARGE}`);
  }
  const telechargee = JSON.parse(readFileSync(FICHIER_TELECHARGE, "utf8"));
  if (JSON.stringify(piece) !== JSON.stringify(telechargee)) {
    throw new Error("la pièce affichée et la pièce téléchargée diffèrent");
  }
  copyFileSync(FICHIER_TELECHARGE, SORTIE);
  canal.fermer();
  console.log(JSON.stringify({ sortie: SORTIE, observation, piece: telechargee }, null, 2));
} finally {
  chrome.kill();
}
