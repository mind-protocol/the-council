// GET /books, /notes, /nappe, /plis — l'étagère, le carnet et ce qui est parti.
const fs = require("fs");
const path = require("path");
const { bibliotheque } = require("../scene"); // LA PORTE serveur de scene
const { RACINE, cheminNotes } = require("../http");
const { envoyer, inlinerFigure } = require("../http");
const { monPersonnage, qui, roster, volumesVisibles } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/books") {
      try {
        const tous = bibliotheque.charger(RACINE);
        const moi = monPersonnage(req, url);
        if (!moi && roster()) {
          return envoyer(res, 200, JSON.stringify({ books: [], boites: [], siege: false }));
        }
        const { liste, boites } = volumesVisibles(tous, moi);
        liste.forEach((b) => (b.pages || []).forEach(inlinerFigure));
        // On ne descend que les coffrets dont il reste quelque chose à
        // ouvrir : une boîte vide sur l'étagère est un onglet qui ment.
        const gardees = new Set(liste.map((b) => b.boite).filter(Boolean));
        return envoyer(res, 200, JSON.stringify({
          books: liste, boites: boites.filter((c) => gardees.has(c.id)) }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ books: [], boites: [] }));
      }
    }
    // Les notes du joueur : le seul volume de l'étagère qui ne soit pas du
    // monde. On le rend tel quel, sans rien en interpréter — c'est du texte,
    // pas du JSON, et ce que le joueur y a mis lui appartient.
    if (url === "/notes") {
      try {
        const p = cheminNotes(qui(req, url));
        const texte = fs.existsSync(p) ? fs.readFileSync(p, "utf-8") : "";
        return envoyer(res, 200, JSON.stringify({ texte }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ texte: "" }));
      }
    }
    // LA NAPPE. Les pièces de bois posées sur la table peinte : ce que le
    // conseil a disposé de ses mains. Ce n'est pas une croyance et ce n'est
    // pas un livre — c'est un MEUBLE, partagé par tous ceux qui entrent dans
    // la salle. D'où un seul fichier, et non un par siège : deux personnes
    // penchées sur la même table voient les mêmes pièces, sinon ce n'est plus
    // une table, ce sont deux tables qui se ressemblent.
    if (url === "/nappe") {
      try {
        const f = path.join(RACINE, "etat", "nappe.json");
        const d = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf-8")) : {};
        return envoyer(res, 200, JSON.stringify({ pieces: d.pieces || [] }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ pieces: [] }));
      }
    }
    // Les plis : ce qui est parti par écrit, et où ça en est. Le décor s'en
    // sert pour montrer un corbeau qui se lâche et un cavalier qui franchit
    // la porte — la table de guerre, elle, en tire ses jetons `pli`. On sert
    // le tout et l'on résout ce que le client ne peut pas résoudre seul :
    // `de` est un PERSONNAGE, et c'est son lieu du moment qui dit d'où le
    // pli est parti. Sans ça la page devrait charger tout `personnages.json`
    // pour lâcher un oiseau.
    if (url === "/plis") {
      try {
        const f = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "plis.json"), "utf-8"));
        const plis = Array.isArray(f.plis) ? f.plis : [];
        const gens = {};
        try {
          const pj = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "personnages.json"), "utf-8"));
          const liste = Array.isArray(pj) ? pj : (pj.personnages || []);
          for (const p of liste) if (p && p.id) gens[p.id] = p.lieu_id || null;
        } catch (e) { /* sans les gens, `de_lieu` reste nul : le client s'en passe */ }
        return envoyer(res, 200, JSON.stringify({
          plis: plis.map((p) => Object.assign({}, p, {
            de_lieu: gens[p.de] || (p.de || null),
          })),
        }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ plis: [] }));
      }
    }
  }
  return false;
}

module.exports = traiter;
