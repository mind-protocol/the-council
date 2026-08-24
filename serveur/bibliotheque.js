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

function indexer(livres) {
  if (!Array.isArray(livres)) throw new Error("la bibliothèque doit porter une liste");
  const ids = [];
  const parId = new Map();
  livres.forEach((livre) => {
    const id = livre && livre.id;
    if (!ID.test(String(id || "")))
      throw new Error("chaque volume doit porter un id utilisable comme fichier");
    if (parId.has(id)) throw new Error("identifiant de volume en double : " + id);
    ids.push(id);
    parId.set(id, livre);
  });
  return { ids, parId };
}

function egaux(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

function ecrireAtomique(fichier, valeur) {
  fs.mkdirSync(path.dirname(fichier), { recursive: true });
  // Un nom fixe (`volume.json.tmp`) permettait à deux processus de remplir le
  // même temporaire avant que le contrôle optimiste tranche. Le répertoire
  // unique reste sur le même disque, donc le renommage final reste atomique.
  const chantier = fs.mkdtempSync(path.join(path.dirname(fichier), ".bibliotheque-"));
  const temporaire = path.join(chantier, path.basename(fichier) + ".tmp");
  try {
    fs.writeFileSync(temporaire, JSON.stringify(valeur, null, 1), "utf-8");
    fs.renameSync(temporaire, fichier);
  } finally {
    fs.rmSync(chantier, { recursive: true, force: true });
  }
}

function ouvrir(racine) {
  const livres = charger(racine);
  let avant = JSON.parse(JSON.stringify(livres));
  return {
    livres,
    sauver() {
      const e = emplacements(racine);
      const a = indexer(avant);
      const v = indexer(livres);
      const courantsListe = charger(racine);
      const c = indexer(courantsListe);
      if (!fs.existsSync(e.manifeste)) {
        if (!egaux(courantsListe, avant))
          throw new Error("etat/books.json a changé depuis la lecture — rien écrit");
        ecrireAtomique(e.monolithe, livres);
        avant = JSON.parse(JSON.stringify(livres));
        return;
      }
      const tous = new Set([].concat(a.ids, v.ids));
      const touches = Array.from(tous).filter((id) => !egaux(a.parId.get(id), v.parId.get(id)));
      const ordreTouche = !egaux(a.ids, v.ids);
      if (ordreTouche && !egaux(c.ids, a.ids))
        throw new Error("books/_ordre.json a changé depuis la lecture — rien écrit");
      const conflit = touches.find((id) => !egaux(c.parId.get(id), a.parId.get(id)));
      if (conflit) throw new Error("volume modifié depuis la lecture : " + conflit + " — rien écrit");
      v.ids.forEach((id) => {
        if (touches.includes(id)) ecrireAtomique(path.join(e.dossier, id + ".json"), v.parId.get(id));
      });
      if (ordreTouche) ecrireAtomique(e.manifeste, v.ids);
      a.ids.filter((id) => !v.parId.has(id))
        .forEach((id) => fs.unlinkSync(path.join(e.dossier, id + ".json")));
      avant = JSON.parse(JSON.stringify(livres));
    },
  };
}

module.exports = { charger, cheminsSource, ouvrir };
