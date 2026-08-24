const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const B = require("./bibliotheque");

function ecrire(fichier, valeur) {
  fs.mkdirSync(path.dirname(fichier), { recursive: true });
  fs.writeFileSync(fichier, JSON.stringify(valeur), "utf-8");
}

const racine = fs.mkdtempSync(path.join(os.tmpdir(), "conseil-bibliotheque-"));
try {
  ecrire(path.join(racine, "etat", "books.json"), [{ id: "ancien" }]);
  assert.deepStrictEqual(B.charger(racine), [{ id: "ancien" }]);

  ecrire(path.join(racine, "etat", "books", "_ordre.json"), ["b", "a"]);
  ecrire(path.join(racine, "etat", "books", "a.json"), { id: "a" });
  ecrire(path.join(racine, "etat", "books", "b.json"), { id: "b" });
  assert.deepStrictEqual(B.charger(racine).map((x) => x.id), ["b", "a"]);
  assert.strictEqual(B.cheminsSource(racine).length, 3);

  const une = B.ouvrir(racine);
  const deux = B.ouvrir(racine);
  une.livres.find((x) => x.id === "a").n = 1;
  deux.livres.find((x) => x.id === "b").n = 2;
  une.sauver();
  deux.sauver();
  assert.deepStrictEqual(B.charger(racine).map((x) => x.n), [2, 1]);

  const trois = B.ouvrir(racine);
  const quatre = B.ouvrir(racine);
  trois.livres.find((x) => x.id === "a").n = 3;
  quatre.livres.find((x) => x.id === "a").n = 4;
  trois.sauver();
  assert.throws(() => quatre.sauver(), /volume modifié/);
  assert.deepStrictEqual(
    fs.readdirSync(path.join(racine, "etat", "books"))
      .filter((n) => n.endsWith(".tmp") || n.startsWith(".bibliotheque-")),
    []);

  fs.unlinkSync(path.join(racine, "etat", "books", "b.json"));
  assert.throws(() => B.charger(racine), /volume absent/);
  console.log("bibliotheque.js: OK");
} finally {
  fs.rmSync(racine, { recursive: true, force: true });
}
