// GET /books, /notes, /nappe, /plis — l'étagère, le carnet et ce qui est parti.
const fs = require("fs");
const path = require("path");
const bibliotheque = require("../plan/bibliotheque"); // meme container : import direct
const { RACINE, cheminNotes } = require("../http");
const { envoyer, inlinerFigure } = require("../http");
const { monPersonnage, qui, roster, volumesVisibles } = require("../http");
const { coffretsChambre } = require("../agents").chambreLivres; // LA PORTE serveur des agents

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
        // LES COFFRETS DE CHAMBRE (modèle habitant) : des boîtes virtuelles
        // assemblées à la volée depuis `chambres/`, rien ne s'écrit dans
        // `etat/`. Le brouillard est décidé dans le module — sa chambre pour
        // un siège incarné, toutes les chambres à contenu pour la régie, rien
        // de plus pour un siège du roster sans chambre.
        let ch = { books: [], boites: [] };
        try { ch = coffretsChambre(qui(req, url), moi); } catch (e) {}
        return envoyer(res, 200, JSON.stringify({
          books: liste.concat(ch.books),
          boites: boites.filter((c) => gardees.has(c.id)).concat(ch.boites) }));
      } catch (e) {
        // Une bibliothèque invalide n'est pas une bibliothèque vide. Le 12e
        // jour de la 5e lune, un manifeste réclamait un volume absent : le
        // 200 silencieux a fait prendre un échec de chargement pour une
        // collection réellement vide. Le détail reste au journal du serveur ;
        // le lecteur reçoit une erreur stable, sans chemin interne.
        console.error("GET /books — bibliothèque indisponible :", e.message || e);
        return envoyer(res, 503, JSON.stringify({
          books: [], boites: [], erreur: "bibliotheque-indisponible",
        }));
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
