// POST /ou et /marche — le transport seul : lire le corps, appeler le moteur
// (domaine/marche.js), rendre ce qu'il a répondu.
const { envoyer } = require("../http");
const { qui } = require("../http");
const { marcher, poser } = require("../domaine/marche");

// Les deux routes ont la même forme : on accumule le corps, on le passe au
// moteur avec le siège qui l'envoie, on rend `{ code, corps }`.
function servir(req, res, url, moteur) {
  let corps = "";
  req.on("data", (c) => (corps += c));
  req.on("end", () => {
    const r = moteur(corps, qui(req, url));
    envoyer(res, r.code, JSON.stringify(r.corps));
  });
}

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/ou") return servir(req, res, url, poser);
  if (req.method === "POST" && url === "/marche") return servir(req, res, url, marcher);
  return false;
}

module.exports = traiter;
