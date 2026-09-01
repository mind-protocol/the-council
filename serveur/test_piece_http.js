const assert = require("assert");
const childProcess = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");

function ecrire(fichier, valeur) {
  fs.mkdirSync(path.dirname(fichier), { recursive: true });
  fs.writeFileSync(fichier, JSON.stringify(valeur, null, 1), "utf-8");
}

function portLibre() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.once("error", reject);
    s.listen(0, "127.0.0.1", () => {
      const port = s.address().port;
      s.close(() => resolve(port));
    });
  });
}

function posterA(port, route, corps) {
  return new Promise((resolve, reject) => {
    const texte = JSON.stringify(corps);
    const req = http.request({ hostname: "127.0.0.1", port, path: route,
      method: "POST", headers: { "content-type": "application/json",
        "content-length": Buffer.byteLength(texte) } }, (res) => {
      let rendu = "";
      res.on("data", (c) => { rendu += c; });
      res.on("end", () => resolve({ status: res.statusCode, corps: JSON.parse(rendu) }));
    });
    req.once("error", reject);
    req.end(texte);
  });
}

function poster(port, corps) { return posterA(port, "/piece", corps); }

function obtenir(port, route) {
  return new Promise((resolve, reject) => {
    const req = http.request({ hostname: "127.0.0.1", port, path: route,
      method: "GET" }, (res) => {
      let rendu = "";
      res.on("data", (c) => { rendu += c; });
      res.on("end", () => resolve({ status: res.statusCode, corps: JSON.parse(rendu) }));
    });
    req.once("error", reject);
    req.end();
  });
}

async function attendreServeur(proc) {
  return new Promise((resolve, reject) => {
    const delai = setTimeout(() => reject(new Error("serveur de test muet")), 10000);
    let sortie = "";
    proc.stdout.on("data", (c) => {
      sortie += c.toString();
      if (sortie.includes("Le Conseil écoute")) { clearTimeout(delai); resolve(); }
    });
    proc.stderr.on("data", (c) => { sortie += c.toString(); });
    proc.once("exit", (code) => {
      clearTimeout(delai);
      reject(new Error("serveur arrêté avant le test (" + code + ") : " + sortie));
    });
  });
}

(async () => {
  const racine = fs.mkdtempSync(path.join(os.tmpdir(), "conseil-piece-http-"));
  const dossier = path.join(racine, "etat", "books");
  const affaire = { id: "affaire-test", titre: "Affaire de test", tables: [
    { titre: "Ouverture", colonnes: ["Le champ", "Ce qu'on y écrit"],
      lignes: [{ cellules: ["LA PLAGE", "99000 à 99999"] }] },
    { titre: "États cibles", colonnes: ["N°", "L'état", "La preuve"], lignes: [] },
  ] };
  const registre = { id: "plan-etats-cibles", titre: "États",
    colonnes: ["N°", "L'état", "Affaire"], lignes: [] };
  ecrire(path.join(dossier, "_ordre.json"), [affaire.id, registre.id]);
  ecrire(path.join(dossier, affaire.id + ".json"), affaire);
  ecrire(path.join(dossier, registre.id + ".json"), registre);
  ecrire(path.join(racine, "etat", "personnages.json"),
    [{ id: "efficiency-maestro", nom: "Marco Mazzoni" }]);
  ecrire(path.join(racine, "etat", "joueurs.json"),
    [{ jeton: "principal-test", personnage_id: "joueur-test", nom: "Joueur" }]);
  fs.mkdirSync(path.join(racine, "chambres", "efficiency_maestro"), { recursive: true });
  fs.writeFileSync(path.join(racine, "chambres", "efficiency_maestro", "CLAUDE.md"),
    "# Marco\n", "utf-8");

  const port = await portLibre();
  const serveur = childProcess.spawn(process.execPath,
    [path.join(__dirname, "serveur.js"), String(port)], {
      cwd: path.join(__dirname, ".."),
      env: Object.assign({}, process.env, { CONSEIL_RACINE: racine, VOIX_API: "0" }),
      stdio: ["ignore", "pipe", "pipe"],
    });
  try {
    await attendreServeur(serveur);
    const reponse = await poster(port, {
      affaire: affaire.id, genre: "etat", texte: "La porte tient",
    });
    assert.strictEqual(reponse.status, 200);
    assert.strictEqual(reponse.corps.num, "99000");
    const a = JSON.parse(fs.readFileSync(path.join(dossier, affaire.id + ".json")));
    const r = JSON.parse(fs.readFileSync(path.join(dossier, registre.id + ".json")));
    assert.strictEqual(a.tables[1].lignes[0].cellules[0], "**99000**");
    assert.strictEqual(r.lignes[0].cellules[0], "**99000**");
    assert.deepStrictEqual(JSON.parse(fs.readFileSync(path.join(dossier, "_ordre.json"))),
      [affaire.id, registre.id]);

    const bordereau = {
      type: "bordereau-reception/2",
      preuve_geste: { etat: "FAIT" },
      resultat_sous_jacent: { etat: "NON ÉTABLI" },
      decision: "NON REÇU — RÉSULTAT NON ÉTABLI",
    };
    const sansSiege = await posterA(port, "/reception/depot", bordereau);
    assert.strictEqual(sansSiege.status, 403);
    const incomplet = await posterA(port,
      "/reception/depot?jeton=homme%3Aefficiency-maestro", { type: bordereau.type });
    assert.strictEqual(incomplet.status, 400);
    const depot = await posterA(port,
      "/reception/depot?jeton=homme%3Aefficiency-maestro", bordereau);
    assert.strictEqual(depot.status, 201);
    assert.match(depot.corps.lien,
      /^\/reception\/preuves\/efficiency-maestro\/[a-f0-9]{24}$/);
    const preuve = await obtenir(port, depot.corps.lien);
    assert.strictEqual(preuve.status, 200);
    assert.strictEqual(preuve.corps.depose_par, "efficiency-maestro");
    assert.deepStrictEqual(preuve.corps.bordereau, bordereau);
    assert.ok(fs.existsSync(path.join(racine, "chambres", "efficiency_maestro",
      "brouillons", "receptions", depot.corps.id + ".json")));
    assert.ok(!fs.existsSync(path.join(racine, "chambres", "efficiency-maestro",
      "brouillons", "receptions", depot.corps.id + ".json")));
    const absente = await obtenir(port,
      "/reception/preuves/efficiency-maestro/000000000000000000000000");
    assert.strictEqual(absente.status, 404);
    const second = await posterA(port,
      "/reception/depot?jeton=homme%3Aefficiency-maestro",
      Object.assign({}, bordereau, { preuve_durable: "ancienne" }));
    assert.strictEqual(second.corps.lien, depot.corps.lien);

    // Un manifeste cassé doit barrer la réception : 503, jamais une fausse
    // bibliothèque vide en 200.
    fs.unlinkSync(path.join(dossier, registre.id + ".json"));
    const indisponible = await obtenir(port, "/books");
    assert.strictEqual(indisponible.status, 503);
    assert.strictEqual(indisponible.corps.erreur, "bibliotheque-indisponible");
    assert.deepStrictEqual(indisponible.corps.books, []);
    console.log("POST /piece + dépôt /reception + GET /books invalide: OK");
  } finally {
    serveur.kill();
    fs.rmSync(racine, { recursive: true, force: true });
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
