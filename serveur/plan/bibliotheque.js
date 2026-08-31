// La bibliothèque agrège le reliquat commun et les documents de chaque maison.
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

function maisons(racine) {
  const fichier = path.join(racine, "etat", "maisons.json");
  if (!fs.existsSync(fichier)) return [];
  const brut = JSON.parse(fs.readFileSync(fichier, "utf-8"));
  const liste = Array.isArray(brut) ? brut : (brut.maisons || []);
  return liste.map((m) => m && m.id).filter(Boolean).concat(["_sans-maison"]);
}

function sourcesMaisons(racine) {
  const sources = new Map();
  maisons(racine).forEach((maison) => {
    const base = path.join(racine, "etat", "maisons", maison, "documents", "books");
    const manifeste = path.join(base, "_ordre.json");
    if (!fs.existsSync(manifeste)) return;
    ordre(manifeste).forEach((id) => {
      const fichier = path.join(base, id + ".json");
      if (!fs.existsSync(fichier)) throw new Error("volume absent : " + fichier);
      const livre = JSON.parse(fs.readFileSync(fichier, "utf-8"));
      if (!livre || Array.isArray(livre) || typeof livre !== "object" || livre.id !== id)
        throw new Error(fichier + " ne porte pas l'id " + id);
      if (sources.has(id)) throw new Error("identifiant de volume en double : " + id);
      sources.set(id, fichier);
    });
  });
  return sources;
}

function manifestesMaisons(racine) {
  const result = new Map();
  maisons(racine).forEach((maison) => {
    const fichier = path.join(racine, "etat", "maisons", maison,
      "documents", "books", "_ordre.json");
    if (fs.existsSync(fichier)) result.set(maison, { fichier, ids: ordre(fichier) });
  });
  return result;
}

function cheminsSource(racine) {
  const e = emplacements(racine);
  const locaux = !fs.existsSync(e.manifeste) ? [e.monolithe] :
    [e.manifeste].concat(ordre(e.manifeste)
      .map((id) => path.join(e.dossier, id + ".json")));
  return locaux.concat(Array.from(sourcesMaisons(racine).values()));
}

function chargerLocaux(racine) {
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

function charger(racine) {
  const livres = chargerLocaux(racine)
    .concat(Array.from(sourcesMaisons(racine).values())
      .map((fichier) => JSON.parse(fs.readFileSync(fichier, "utf-8"))));
  indexer(livres);
  return livres;
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
  let manifestesAvant = manifestesMaisons(racine);
  return {
    livres,
    sauver() {
      const e = emplacements(racine);
      const a = indexer(avant);
      const v = indexer(livres);
      const courantsListe = charger(racine);
      const c = indexer(courantsListe);
      const sources = sourcesMaisons(racine);
      const nouveaux = v.ids.filter((id) => !a.parId.has(id));
      const maisonsValides = new Set(maisons(racine));
      const nouveauxParMaison = new Map();
      nouveaux.forEach((id) => {
        const maison = v.parId.get(id).maison_id;
        if (!maisonsValides.has(maison))
          throw new Error("un nouveau livre doit porter une maison_id connue : " + id);
        if (!nouveauxParMaison.has(maison)) nouveauxParMaison.set(maison, []);
        nouveauxParMaison.get(maison).push(id);
      });
      const externes = new Set([].concat(Array.from(sources.keys()), nouveaux));
      const locauxA = a.ids.filter((id) => !externes.has(id));
      const locauxV = v.ids.filter((id) => !externes.has(id));
      const locauxC = c.ids.filter((id) => !externes.has(id));
      if (!fs.existsSync(e.manifeste)) {
        if (!egaux(courantsListe, avant))
          throw new Error("etat/books.json a changé depuis la lecture — rien écrit");
        ecrireAtomique(e.monolithe, locauxV.map((id) => v.parId.get(id)));
        externes.forEach((id) => {
          if (!egaux(a.parId.get(id), v.parId.get(id)))
            ecrireAtomique(sources.get(id), v.parId.get(id));
        });
        avant = JSON.parse(JSON.stringify(livres));
        return;
      }
      const tous = new Set([].concat(a.ids, v.ids));
      const touches = Array.from(tous).filter((id) => !egaux(a.parId.get(id), v.parId.get(id)));
      const ordreTouche = !egaux(locauxA, locauxV);
      if (ordreTouche && !egaux(locauxC, locauxA))
        throw new Error("books/_ordre.json a changé depuis la lecture — rien écrit");
      const conflit = touches.find((id) => !egaux(c.parId.get(id), a.parId.get(id)));
      if (conflit) throw new Error("volume modifié depuis la lecture : " + conflit + " — rien écrit");
      const manifestesCourants = manifestesMaisons(racine);
      nouveauxParMaison.forEach((ids, maison) => {
        const av = manifestesAvant.get(maison), cv = manifestesCourants.get(maison);
        if (!egaux(av, cv))
          throw new Error("documents de " + maison + " modifiés depuis la lecture — rien écrit");
        const base = path.dirname(av.fichier);
        ids.forEach((id) => ecrireAtomique(path.join(base, id + ".json"), v.parId.get(id)));
        const ordreMaison = v.ids.filter((id) => v.parId.get(id).maison_id === maison);
        ecrireAtomique(av.fichier, ordreMaison);
      });
      locauxV.forEach((id) => {
        if (touches.includes(id)) ecrireAtomique(path.join(e.dossier, id + ".json"), v.parId.get(id));
      });
      if (ordreTouche) ecrireAtomique(e.manifeste, locauxV);
      locauxA.filter((id) => !v.parId.has(id))
        .forEach((id) => fs.unlinkSync(path.join(e.dossier, id + ".json")));
      externes.forEach((id) => {
        if (!v.parId.has(id))
          throw new Error("un document de maison ne se supprime pas par la bibliothèque globale");
        if (sources.has(id) && touches.includes(id))
          ecrireAtomique(sources.get(id), v.parId.get(id));
      });
      avant = JSON.parse(JSON.stringify(livres));
      manifestesAvant = manifestesMaisons(racine);
    },
  };
}

module.exports = { charger, cheminsSource, ouvrir };
