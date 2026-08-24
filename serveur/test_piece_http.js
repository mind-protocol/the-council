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

function poster(port, corps) {
  return new Promise((resolve, reject) => {
    const texte = JSON.stringify(corps);
    const req = http.request({ hostname: "127.0.0.1", port, path: "/piece",
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
    console.log("POST /piece scindé: OK");
  } finally {
    serveur.kill();
    fs.rmSync(racine, { recursive: true, force: true });
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
