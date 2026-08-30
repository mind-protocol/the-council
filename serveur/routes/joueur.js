// GET /, /moi, /bascule — qui frappe à la porte, et à quelle table il s'assied.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");
const { qui, roster } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/") {
      // Un jeton dans l'URL se range dans un cookie : on ne le partage
      // qu'une fois, et le navigateur le represente à chaque requête.
      const j = qui(req, url);
      const entetes = j
        ? { "Set-Cookie": "jeton=" + encodeURIComponent(j.jeton) + "; Path=/; Max-Age=31536000; SameSite=Lax" }
        : null;
      try {
        const corps = fs.readFileSync(path.join(RACINE, "ecrans", "jeu.html"));
        return envoyer(res, 200, corps, "text/html; charset=utf-8", entetes);
      } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: "jeu.html" })); }
    }
    // Qui suis-je à cette table ? Le viewport en a besoin pour dire « Vous »
    // à l'un et « Daemon » à l'autre. Roster absent = partie mono-joueur.
    if (url === "/moi") {
      const l = roster(), j = qui(req, url);
      return envoyer(res, 200, JSON.stringify({
        multi: !!l,
        // `regie` : ce siège ne joue personne, il regarde. C'est lui qui
        // ouvre le fil d'un homme depuis le plan du château (modules/regie.js).
        moi: j ? { personnage_id: j.personnage_id, nom: j.nom || "", regie: !!j.regie } : null,
        sieges: (l || []).map((x) => ({ personnage_id: x.personnage_id, nom: x.nom || "" })),
      }));
    }
    // Débug — changer de siège sans rouvrir l'URL au jeton. On ne rend JAMAIS
    // les jetons au navigateur : on demande un personnage, le serveur pose le
    // cookie correspondant et renvoie à la racine. Outil de mise au point.
    if (url === "/bascule") {
      const l = roster();
      if (!l || l.length < 2) return envoyer(res, 404, JSON.stringify({ erreur: "roster" }));
      const q = (req.url.split("?")[1] || "").match(/(?:^|&)vers=([^&]*)/);
      const vers = decodeURIComponent((q && q[1]) || "");
      const j = qui(req, url);
      // Sans cible : le suivant du roster, en boucle.
      const i = j ? l.findIndex((x) => x.jeton === j.jeton) : -1;
      const cible = vers ? l.find((x) => x.personnage_id === vers) : l[(i + 1) % l.length];
      if (!cible) return envoyer(res, 404, JSON.stringify({ erreur: vers }));
      res.writeHead(302, {
        "Set-Cookie": "jeton=" + encodeURIComponent(cible.jeton) + "; Path=/; Max-Age=31536000; SameSite=Lax",
        Location: "/",
      });
      return res.end();
    }
    // ---- la présence : qui partage VOTRE pièce ---------------------------
    // `etat/presence.json` tient une entrée par personnage — se tenir quelque
    // part est un fait du monde, et non une mise en scène privée. Le flux, lui,
    // est cloisonné par `pour` : un PNJ que les deux scènes se partagent
    // apparaissait donc dans les deux pièces à la fois, une par écran, et aucun
    // `sortent` ne pouvait l'ôter des deux (il porte forcément une audience).
    //
    // On ne rend JAMAIS la carte des présences : seulement votre pièce et ceux
    // qui y sont. Où se tient l'autre joueuse, et avec qui, ne descend pas
    // jusqu'à votre machine — le brouillard vaut ici comme partout.
  }
  return false;
}

module.exports = traiter;
