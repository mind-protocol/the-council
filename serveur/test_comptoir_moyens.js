const assert = require("assert");
const childProcess = require("child_process");
const http = require("http");
const net = require("net");
const path = require("path");

function portLibre() {
  return new Promise((resolve, reject) => {
    const prise = net.createServer();
    prise.once("error", reject);
    prise.listen(0, "127.0.0.1", () => {
      const port = prise.address().port;
      prise.close(() => resolve(port));
    });
  });
}

function obtenir(port, route) {
  return new Promise((resolve, reject) => {
    const req = http.get({ hostname: "127.0.0.1", port, path: route }, (res) => {
      let corps = "";
      res.setEncoding("utf-8");
      res.on("data", (morceau) => { corps += morceau; });
      res.on("end", () => resolve({ code: res.statusCode, type: res.headers["content-type"], corps }));
    });
    req.once("error", reject);
  });
}

async function attendre(port) {
  for (let i = 0; i < 40; i += 1) {
    try { return await obtenir(port, "/comptoir-moyens"); } catch (e) {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("le serveur d'épreuve n'a pas ouvert son port");
}

(async () => {
  const port = await portLibre();
  const racine = path.resolve(__dirname, "..");
  const serveur = childProcess.spawn(process.execPath, [path.join(__dirname, "serveur.js")], {
    cwd: racine,
    env: Object.assign({}, process.env, { PORT: String(port) }),
    stdio: "ignore",
  });
  try {
    const page = await attendre(port);
    assert.strictEqual(page.code, 200);
    assert.match(page.type, /^text\/html/);
    assert.match(page.corps, /Comptoir des moyens/);

    const reponse = await obtenir(port, "/comptoir-moyens.json");
    assert.strictEqual(reponse.code, 200);
    const resultat = JSON.parse(reponse.corps);
    assert.strictEqual(resultat.comparaisons.length, 6);
    assert.ok(resultat.code_sortie === 0 || resultat.code_sortie === 1);
    resultat.comparaisons.forEach((ligne) => {
      assert.ok(ligne.source_inscrite);
      assert.ok(ligne.source_observee);
      assert.strictEqual(ligne.ecart, ligne.observe - ligne.inscrit);
    });
    console.log("GET /comptoir-moyens + JSON courant : OK (code " + resultat.code_sortie + ")");
  } finally {
    serveur.kill();
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
