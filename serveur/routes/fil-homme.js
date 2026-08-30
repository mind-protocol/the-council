// GET /fil-homme — le fil PAR HOMME : ce que voit un joueur qui incarne un
// habitant hors roster (ou un arbitre). Sa mémoire, jamais le flux public —
// l'assemblage vit dans le container agents (domaine/chambres.js, filHomme),
// on n'y entre que par sa porte. Un siège du roster n'a rien à faire ici :
// son chemin /scene est intact, et on le lui dit d'un 403.
const { envoyer, qui } = require("../http");
const agents = require("../agents");

function traiter(req, res, url) {
  if (req.method === "GET" && url === "/fil-homme") {
    const j = qui(req, url);
    if (!j || !j.hors_roster) {
      return envoyer(res, 403, JSON.stringify({
        erreur: "reserve au siege d'un homme hors roster" }));
    }
    // La pagination de /scene : `?avant=N` rend la tranche qui précède la
    // ligne N du fil entier ; `debut` dit où la tranche commence.
    const m = (req.url.split("?")[1] || "").match(/(?:^|&)avant=(\d+)/);
    const avant = m ? +m[1] : null;
    return envoyer(res, 200,
      JSON.stringify(agents.chambres.filHomme(j.personnage_id, avant)));
  }
  return false;
}

module.exports = traiter;
