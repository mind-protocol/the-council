const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const B = require("./plan").bibliotheque; // LA PORTE serveur du plan

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

  ecrire(path.join(racine, "etat", "maisons.json"), [{ id: "maison-a" }]);
  const maison = path.join(racine, "etat", "maisons", "maison-a", "documents", "books");
  ecrire(path.join(maison, "_ordre.json"), ["moyens-a"]);
  ecrire(path.join(maison, "moyens-a.json"),
    { id: "moyens-a", maison_id: "maison-a", n: 0 });
  assert.deepStrictEqual(B.charger(racine).map((x) => x.id), ["b", "a", "moyens-a"]);
  const maisonSession = B.ouvrir(racine);
  maisonSession.livres.find((x) => x.id === "moyens-a").n = 7;
  maisonSession.sauver();
  assert.strictEqual(JSON.parse(fs.readFileSync(path.join(maison, "moyens-a.json"))).n, 7);
  const nouveau = B.ouvrir(racine);
  nouveau.livres.push({ id: "nouveau", maison_id: "maison-a" });
  nouveau.sauver();
  assert.deepStrictEqual(JSON.parse(fs.readFileSync(path.join(maison, "_ordre.json"))),
    ["moyens-a", "nouveau"]);

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
