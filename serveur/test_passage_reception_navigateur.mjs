#!/usr/bin/env node
"use strict";

import { spawn } from "node:child_process";
import assert from "node:assert/strict";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9341;
const PROFIL = join(tmpdir(), `conseil-passage-reception-${process.pid}`);
const DEPART = "http://localhost:3129/?jeton=homme%3Anlr";

const attendre = (ms) => new Promise((resoudre) => setTimeout(resoudre, ms));

async function attendreJson(url) {
  for (let i = 0; i < 80; i += 1) {
    try {
      const reponse = await fetch(url);
      if (reponse.ok) return reponse.json();
    } catch {}
    await attendre(100);
  }
  throw new Error("porte de débogage inaccessible");
}

function canal(adresse) {
  const socket = new WebSocket(adresse);
  let id = 1;
  const attentes = new Map();
  const ouvert = new Promise((resoudre, rejeter) => {
    socket.addEventListener("open", resoudre, { once: true });
    socket.addEventListener("error", rejeter, { once: true });
  });
  socket.addEventListener("message", (evenement) => {
    const message = JSON.parse(evenement.data);
    if (!message.id || !attentes.has(message.id)) return;
    const attente = attentes.get(message.id);
    attentes.delete(message.id);
    if (message.error) attente.rejeter(new Error(JSON.stringify(message.error)));
    else attente.resoudre(message.result);
  });
  return {
    ouvert,
    envoyer(method, params = {}) {
      const courant = id++;
      socket.send(JSON.stringify({ id: courant, method, params }));
      return new Promise((resoudre, rejeter) => attentes.set(courant, { resoudre, rejeter }));
    },
    fermer() { socket.close(); },
  };
}

async function evaluer(c, expression) {
  const rendu = await c.envoyer("Runtime.evaluate", {
    expression, awaitPromise: true, returnByValue: true,
  });
  if (rendu.exceptionDetails) throw new Error(rendu.exceptionDetails.text || "erreur du lecteur");
  return rendu.result.value;
}

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-first-run", "--disable-default-apps",
  `--user-data-dir=${PROFIL}`, `--remote-debugging-port=${PORT}`, DEPART,
], { stdio: "ignore", windowsHide: true });

try {
  const cibles = await attendreJson(`http://127.0.0.1:${PORT}/json`);
  const cible = cibles.find((item) => item.type === "page");
  assert.ok(cible, "aucune page dans le lecteur");
  const c = canal(cible.webSocketDebuggerUrl);
  await c.ouvert;
  await c.envoyer("Runtime.enable");

  let lien = null;
  for (let i = 0; i < 100 && !lien; i += 1) {
    lien = await evaluer(c, `(() => {
      if (!window.Books || !Books.ouvrir("registre-ouvrages-archive", "90094")) return null;
      const a = document.querySelector('tr[data-num="90094"] .book-passage-reception');
      return a ? a.href : null;
    })()`);
    if (!lien) await attendre(100);
  }
  assert.ok(lien, "la ligne 90094 n'offre aucun passage vers /reception");
  assert.ok(!/[?&](?:verdict|preuve)=/i.test(lien), "le passage transmet un jugement antérieur");

  await evaluer(c, `location.href = ${JSON.stringify(lien)}`);
  let champs = null;
  for (let i = 0; i < 80 && !champs; i += 1) {
    champs = await evaluer(c, `(() => {
      const ids = ["objet", "adresse", "producteur", "provenance", "critere"];
      if (!ids.every((id) => document.getElementById(id))) return null;
      const valeurs = Object.fromEntries(ids.map((id) => [id, document.getElementById(id).value]));
      return valeurs.objet ? valeurs : null;
    })()`);
    if (!champs) await attendre(100);
  }
  assert.deepEqual(champs, {
    objet: "La cale visuelle de Serenissima",
    adresse: "C:\\Users\\reyno\\le-conseil2\\chambres\\lucid\\ouvrages\\cale-visuelle\\index.html",
    producteur: "Lorenzo Bellavita (lucid)",
    provenance: "C:\\Users\\reyno\\le-conseil2\\import\\serenissima\\city-visuals",
    critere: "Ouvrir dans un navigateur la galerie construite à partir des dix-sept pièces anciennes, filtrer les catégories et contrôler que chaque image reste atteignable à son adresse de provenance",
  });
  c.fermer();
  console.log("test_passage_reception_navigateur: OK");
} finally {
  chrome.kill();
}
