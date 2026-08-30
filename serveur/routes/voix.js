// GET /voix/liste, /voix/journal et POST /voix/dire.
const voix = require("../voix");
const { envoyer } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/voix/liste") return envoyer(res, 200, JSON.stringify(voix.liste()));
    // qui a demandé quoi, et ce qu'on lui a répondu — pour diagnostiquer un doublon
    if (url === "/voix/journal") return envoyer(res, 200, JSON.stringify(voix.lireJournal()));
  }
  if (req.method === "POST" && url === "/voix/dire") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", async () => {
      try {
        const d = JSON.parse(corps);
        // une phrase plus longue que le bail : le lecteur le renouvelle en route
        if (d.renouveler) return envoyer(res, 200, JSON.stringify({ ok: voix.bail(d.client_id) }));
        const r = await voix.dire(d.locuteur_id, d.texte, d.client_id, d.rejouer);
        if (r.audio) return envoyer(res, 200, r.audio, r.mime || "audio/mpeg");
        return envoyer(res, r.code, JSON.stringify({ erreur: r.erreur }));
      } catch (e) {
        return envoyer(res, 500, JSON.stringify({ erreur: String(e) }));
      }
    });
    return;
  }
  // Le journal de la foule : la page d'essai y verse les CHANGEMENTS d'état
  // qu'elle a vus passer (untel part vers le puits, untel y arrive, untel
  // rentre). Une ligne JSON par changement, en append — jamais une position
  // par image, ce serait des millions de lignes qui ne disent rien.
  //
  // Ça n'entre pas dans `etat/` : ce n'est pas de la partie, c'est de la
  // mesure. Un fichier par session de page, dans monde/journaux/.
  return false;
}

module.exports = traiter;
