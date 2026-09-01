"use strict";

const assert = require("assert");
const passage = require("../ecrans/modules/books/passage-reception");

const colonnes = [
  "Date", "Ouvrage", "Adresse", "Producteur", "Usage tenté",
  "Preuve observable", "Lecteur ou usager", "Verdict", "Limite",
];
const ligne = { cellules: [
  "**90094** 129.5.12",
  "La cale visuelle de Serenissima",
  "Présent : `C:\\ouvrage\\index.html` · provenance : `C:\\import\\city-visuals` · L’Archive, Braavos",
  "Lorenzo Bellavita (`lucid`)",
  "Ouvrir la galerie et filtrer les catégories",
  "preuve.png montre la galerie",
  "Lorenzo Bellavita (`lucid`)",
  "PREMIER USAGE RÉUSSI",
  "Aucun second habitant",
] };

const charge = passage.preparer({ id: "registre-ouvrages-archive" }, colonnes, ligne);
assert.deepStrictEqual(charge, {
  objet: "La cale visuelle de Serenissima",
  adresse: "C:\\ouvrage\\index.html",
  producteur: "Lorenzo Bellavita (lucid)",
  critere: "Ouvrir la galerie et filtrer les catégories",
  provenance: "C:\\import\\city-visuals",
});
const lien = passage.href(charge);
assert.ok(lien.startsWith("/reception?"));
assert.ok(!/verdict|preuve/i.test(lien), "le verdict et la preuve ne doivent pas voyager");
assert.strictEqual(
  passage.preparer({ id: "un-autre-volume" }, colonnes, ligne),
  null,
  "le passage reste borné au registre des ouvrages",
);

console.log("test_passage_reception: OK");
