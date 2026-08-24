// La bibliothèque accepte l'ancien tableau `etat/books.json` et le futur
// dossier `etat/books/`. Le dossier ne fait foi que lorsque `_ordre.json`
// existe : une copie partielle ne peut donc pas s'activer par accident.
const fs = require("fs");
const path = require("path");

const ID = /^[a-z0-9][a-z0-9._-]*$/;

function emplacements(racine) {
  const dossier = path.join(racine, "etat", "books");
  return {
    dossier,
    manifeste: path.join(dossier, "_ordre.json"),
    monolithe: path.join(racine, "etat", "books.json"),
  };
}

function ordre(manifeste) {
  const ids = JSON.parse(fs.readFileSync(manifeste, "utf-8"));
  if (!Array.isArray(ids) || ids.some((id) => typeof id !== "string"))
    throw new Error("books/_ordre.json doit être une liste d'identifiants");
  if (new Set(ids).size !== ids.length)
    throw new Error("books/_ordre.json contient un identifiant en double");
  const mauvais = ids.find((id) => !ID.test(id));
  if (mauvais) throw new Error("identifiant impropre à un nom de fichier : " + mauvais);
  return ids;
}

function cheminsSource(racine) {
  const e = emplacements(racine);
  if (!fs.existsSync(e.manifeste)) return [e.monolithe];
  return [e.manifeste].concat(ordre(e.manifeste)
    .map((id) => path.join(e.dossier, id + ".json")));
}

function charger(racine) {
  const e = emplacements(racine);
  if (!fs.existsSync(e.manifeste)) {
    const livres = JSON.parse(fs.readFileSync(e.monolithe, "utf-8"));
    if (!Array.isArray(livres)) throw new Error("etat/books.json doit porter une liste");
    return livres;
  }
  return ordre(e.manifeste).map((id) => {
    const fichier = path.join(e.dossier, id + ".json");
    if (!fs.existsSync(fichier)) throw new Error("volume absent : books/" + id + ".json");
    const livre = JSON.parse(fs.readFileSync(fichier, "utf-8"));
    if (!livre || Array.isArray(livre) || typeof livre !== "object")
      throw new Error("books/" + id + ".json doit porter un objet");
    if (livre.id !== id)
      throw new Error("books/" + id + ".json porte l'id " + JSON.stringify(livre.id));
    return livre;
  });
}

module.exports = { charger, cheminsSource };
