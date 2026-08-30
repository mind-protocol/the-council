// -*- coding: utf-8 -*-
/**
 * MONDE_LOCAL — servir `/monde/…` sans serveur, en appelant la VRAIE route.
 *
 *     const { poserFetchLocal } = require("./monde_local.js");
 *     poserFetchLocal();          // `fetch("/monde/masque")` marche désormais
 *
 * POURQUOI CE FICHIER EXISTE. Les bancs sont des étalons à tolérance zéro, et
 * quatre d'entre eux — `banc-moteur`, `banc-monde`, `banc-combattant`,
 * `banc-epreuve` — mouraient sur `TypeError: fetch failed` dès qu'aucun serveur
 * ne tournait sur `:3129`. Une vérification qui exige un serveur vivant ne peut
 * ni tourner en CI, ni garder un commit, ni se lancer en fin de session : elle
 * dépend d'un état externe qu'on ne voit pas (quel port ? servant quel
 * `monde/` ?). C'est exactement la dépendance invisible que les huit listes de
 * scripts avaient déjà fait payer une fois à ce dépôt.
 *
 * IL NE RECOPIE AUCUNE ROUTE, ET C'EST TOUT LE POINT. La tentation était de
 * lire les fichiers de `monde/` directement — trois lignes, et l'affaire
 * semblait close. Mais `/monde/voirie?couche=L1-surface` n'est PAS un fichier :
 * c'est une route qui filtre le graphe piéton, et `/monde/plan2d`, `/monde/bati`,
 * `/monde/masque` choisissent leur lieu, leur préfixe et leur repli. Les
 * réécrire ici, c'est réintroduire par la porte de derrière la divergence que
 * `sac.js` refuse en allant chercher ses données par le vrai serveur. On garde
 * donc l'autorité au même endroit : `serveur/noyau/monde3d.js` expose
 * `serviceMonde`, on l'appelle EN MÉMOIRE avec une requête et une réponse de
 * papier. Ce qui change entre le navigateur et Node, ce n'est plus la source de
 * la donnée — c'est seulement le transport.
 *
 * C'est la même bascule que `moteur/chaine.js` fait déjà pour les scripts (le
 * navigateur pose des balises, Node évalue des sources), appliquée aux DONNÉES.
 *
 * CE QU'IL NE FAIT PAS. Il ne sert que `/monde/…`. Une URL absolue part au
 * réseau comme avant ; toute autre route relative est refusée en clair plutôt
 * que devinée — un banc qui aurait besoin de `/carte` doit le dire, pas
 * l'obtenir par accident.
 */
"use strict";
const fs = require("fs");
const path = require("path");

const RACINE = path.dirname(path.dirname(path.resolve(__dirname)));

/** La réponse de papier : elle ne parle à personne, elle retient. */
function reponseDePapier(resoudre) {
  const morceaux = [];
  return {
    _code: 200, _entetes: {},
    writeHead(code, entetes) { this._code = code; this._entetes = entetes || {}; },
    write(c) { morceaux.push(Buffer.isBuffer(c) ? c : Buffer.from(String(c), "utf-8")); },
    end(corps) {
      if (corps != null) this.write(corps);
      resoudre({ code: this._code, entetes: this._entetes, corps: Buffer.concat(morceaux) });
    },
  };
}

/** Le peu de `Response` dont les modules de bataille se servent réellement. */
function habiller(brut, url) {
  return {
    ok: brut.code >= 200 && brut.code < 300,
    status: brut.code,
    url: String(url),
    headers: { get: (n) => brut.entetes[n] || brut.entetes[String(n).toLowerCase()] || null },
    async arrayBuffer() {
      return brut.corps.buffer.slice(
        brut.corps.byteOffset, brut.corps.byteOffset + brut.corps.byteLength);
    },
    async text() { return brut.corps.toString("utf-8"); },
    async json() { return JSON.parse(brut.corps.toString("utf-8")); },
  };
}

/**
 * Servir une URL `/monde/…` par la route elle-même.
 * @param {string} url  par exemple `/monde/voirie?couche=L1-surface`
 */
// OU VIT LA ROUTE, AUJOURD'HUI. `serveur/` est en cours de decoupage : le module
// qui porte `serviceMonde` a deja change de dossier une fois pendant l'ecriture
// de ce fichier. On ne code donc pas son chemin en dur — on le CHERCHE parmi les
// places connues, et si aucune ne repond, on dit lesquelles on a ouvertes plutot
// que de laisser un `Cannot find module` nu. Un banc qui meurt doit dire ou
// regarder.
const SAUT = String.fromCharCode(10);
const PLACES = [
  ["serveur", "monde3d.js"],
  ["serveur", "noyau", "monde3d.js"],
  ["serveur", "domaine", "monde3d.js"],
  ["serveur", "routes", "monde-jeu.js"],
];

let _route = null;
function laRoute() {
  if (_route) return _route;
  const ouvertes = [];
  for (const bouts of PLACES) {
    const p = path.join(RACINE, ...bouts);
    ouvertes.push(path.relative(RACINE, p));
    if (!fs.existsSync(p)) continue;
    const m = require(p);
    if (m && typeof m.serviceMonde === "function") return (_route = m.serviceMonde);
  }
  throw new Error(
    "monde_local : aucun module ne porte `serviceMonde`." + SAUT
    + "Places ouvertes : " + ouvertes.join(", ") + SAUT
    + "Si `serveur/` a encore ete range, ajoute la nouvelle place a PLACES dans "
    + "scripts/monde/monde_local.js.");
}

function servirMonde(url) {
  // Resolue ici et pas en tete de fichier : un banc qui n'appelle jamais
  // `/monde/…` ne doit pas payer le chargement des lieux 3D.
  const serviceMonde = laRoute();
  const s = String(url);
  // La route reçoit le chemin SANS sa question, et relit `req.url` quand elle a
  // besoin du paramètre — c'est ainsi que `/monde/voirie?couche=…` trouve sa
  // couche. Passer la question dans le chemin donne un 404 « lieu inconnu ».
  const chemin = s.slice("/monde/".length).split("?")[0];
  const req = { url: s, method: "GET", headers: {} };   // pas de gzip : brut
  return new Promise((resoudre, rejeter) => {
    const res = reponseDePapier(resoudre);
    try { serviceMonde(req, res, chemin); } catch (e) { rejeter(e); }
  }).then((brut) => habiller(brut, s));
}

/**
 * Poser un `fetch` qui sert `/monde/…` en mémoire. Rend le `fetch` précédent,
 * pour qu'un appelant puisse le remettre.
 */
function poserFetchLocal() {
  const vrai = globalThis.fetch;
  globalThis.fetch = (u, o) => {
    const s = String(u);
    if (/^https?:/.test(s)) return vrai(s, o);
    if (s.startsWith("/monde/") || s === "/monde") return servirMonde(s === "/monde" ? "/monde/" : s);
    return Promise.reject(new Error(
      "monde_local ne sert que /monde/… — route demandée : " + s + "\n"
      + "Lancez le banc avec --serveur http://localhost:3129 s'il lui en faut d'autres."));
  };
  return vrai;
}

module.exports = { servirMonde, poserFetchLocal, RACINE };
