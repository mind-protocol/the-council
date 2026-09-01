// passage-reception.js — la cargaison neutre d'une ligne du registre vers
// le bordereau de réception.
//
// Cette pièce est volontairement une liste blanche. Le registre porte aussi
// le verdict et la preuve d'un premier lecteur ; les transmettre au suivant
// biaiserait son essai. Seuls le titre, l'adresse, le producteur, l'usage choisi
// et une provenance explicitement déclarée peuvent franchir ce passage.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksPassageReception = api;
})(typeof window !== "undefined" ? window : globalThis, function () {
  const REGISTRE = "registre-ouvrages-archive";

  const nu = (valeur) => String(valeur == null ? "" : valeur)
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .replace(/\s+/g, " ")
    .trim();

  const clef = (valeur) => nu(valeur).normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  function indexer(colonnes) {
    const index = {};
    (colonnes || []).forEach((nom, i) => { index[clef(nom)] = i; });
    return index;
  }

  // Quelques lignes distinguent déjà « Présent » et « provenance » dans la
  // cellule Adresse. On garde alors l'adresse présente comme destination et
  // l'ancienne adresse comme provenance, sans déduire quoi que ce soit des
  // autres formulations libres.
  function separerAdresse(valeur) {
    const texte = nu(valeur);
    const marque = /^(?:present|présent)\s*:\s*(.*?)\s*·\s*provenance\s*:\s*(.*)$/i.exec(texte);
    if (!marque) return { adresse: texte };
    const suite = marque[2].split(/\s*·\s*/);
    return { adresse: marque[1].trim(), provenance: suite[0].trim() };
  }

  function preparer(livre, colonnes, ligne) {
    if (!livre || livre.id !== REGISTRE || !ligne) return null;
    const i = indexer(colonnes);
    const requis = ["ouvrage", "adresse", "producteur", "usage tente"];
    if (requis.some((nom) => i[nom] == null)) return null;
    const cellules = ligne.cellules || [];
    const adresse = separerAdresse(cellules[i.adresse]);
    const passage = {
      objet: nu(cellules[i.ouvrage]),
      adresse: adresse.adresse,
      producteur: nu(cellules[i.producteur]),
      critere: nu(cellules[i["usage tente"]]),
    };
    const provenance = i.provenance == null
      ? adresse.provenance
      : nu(cellules[i.provenance]);
    if (provenance) passage.provenance = provenance;
    if (!passage.objet || !passage.adresse || !passage.producteur || !passage.critere) return null;
    return passage;
  }

  function href(passage) {
    if (!passage) return null;
    return "/reception?" + new URLSearchParams(passage).toString();
  }

  return { preparer, href };
});
