// GET /echiquier — le damier des affaires. Le calcul vit dans domaine/echiquier.js.
const { composer } = require("../domaine/echiquier");
const { envoyer } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET" && url === "/echiquier")
    return envoyer(res, 200, JSON.stringify(composer(req, url)));
  return false;
}

module.exports = traiter;
