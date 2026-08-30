// GET /retrospective, /medailles, /captures/*, /textures/*, /sons/cris/*.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/retrospective") {
      try {
        const t = JSON.parse(fs.readFileSync(
          path.join(RACINE, "etat", "retrospective.json"), "utf-8"));
        return envoyer(res, 200, JSON.stringify({ planches: t.planches || [] }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ planches: [] }));
      }
    }
    // Le cabinet des médailles : les rubans décernés en Coulisses. Hors
    // univers de bout en bout — aucun PNJ n'en a jamais entendu parler.
    if (url === "/medailles") {
      try {
        const t = JSON.parse(fs.readFileSync(
          path.join(RACINE, "etat", "medailles.json"), "utf-8"));
        return envoyer(res, 200, JSON.stringify({ medailles: t.medailles || [] }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ medailles: [] }));
      }
    }
    // Les images des planches. `basename` d'abord : un nom de fichier ne
    // remonte jamais d'un cran, quoi qu'il porte.
    if (url.startsWith("/captures/")) {
      const nom = path.basename(decodeURIComponent(url.slice("/captures/".length)));
      const ext = path.extname(nom).toLowerCase();
      const types = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };
      if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
      try {
        const corps = fs.readFileSync(path.join(RACINE, "captures", nom));
        return envoyer(res, 200, corps, types[ext]);
      } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
    }
    // Les textures du décor 3D. Même garde que les planches : `basename`
    // d'abord, un nom de fichier ne remonte jamais d'un cran. Elles changent
    // une ou deux fois par an — on les laisse en cache une journée, sinon
    // chaque rechargement de la page les retire du réseau pour rien.
    if (url.startsWith("/textures/")) {
      const nom = path.basename(decodeURIComponent(url.slice("/textures/".length)));
      const ext = path.extname(nom).toLowerCase();
      const types = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp" };
      if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
      try {
        const corps = fs.readFileSync(path.join(RACINE, "ecrans", "textures", nom));
        res.writeHead(200, { "Content-Type": types[ext], "Cache-Control": "public, max-age=86400" });
        return res.end(corps);
      } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
    }
    // Les cris. Les seuls fichiers sonores du jeu : tout le reste du son de
    // bataille est synthétisé dans `ecrans/modules/son.js`. Ils vivent hors
    // d'`ecrans/` parce qu'ils ne sont pas un écran — d'où la racine à part.
    // Même garde que les planches (`basename`, un nom ne remonte jamais d'un
    // cran), et le même cache d'une journée : ils ne changent jamais.
    if (url.startsWith("/sons/cris/")) {
      const nom = path.basename(decodeURIComponent(url.slice("/sons/cris/".length)));
      const ext = path.extname(nom).toLowerCase();
      const types = { ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
                      ".json": "application/json; charset=utf-8" };
      if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
      try {
        const corps = fs.readFileSync(path.join(RACINE, "sons", "cris", nom));
        res.writeHead(200, { "Content-Type": types[ext], "Cache-Control": "public, max-age=86400" });
        return res.end(corps);
      } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
    }
    // Les vues de salle. Une salle du plan peut avoir sa toile dans
    // `ecrans/salles/<id de la salle>.jpg` — l'id est celui de `plans.js`.
    // Le fil la pose au changement de salle, et SEULEMENT si elle existe :
    // d'où le manifeste ci-dessous, servi une fois au chargement. Sans lui,
    // la page devrait tenter l'image et la retirer sur erreur, ce qui la
    // ferait clignoter à chaque salle qui n'en a pas — c'est-à-dire presque
    // toutes. Rien à declarer nulle part : deposer le fichier suffit.
  }
  return false;
}

module.exports = traiter;
