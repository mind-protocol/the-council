// Le transport : la seule fonction qui écrive dans une réponse, le service
// d'un fichier d'écran, et l'inlinage d'une figure servie avec le flux.

const fs = require("fs");
const path = require("path");
const { RACINE } = require("./contexte");

function envoyer(res, code, corps, type, entetes) {
  res.writeHead(code, Object.assign({
    "Content-Type": type || "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  }, entetes || {}));
  res.end(corps);
}

function fichierStatique(res, relatif, type) {
  try {
    const corps = fs.readFileSync(path.join(RACINE, "ecrans", relatif));
    return envoyer(res, 200, corps, type);
  } catch (e) {
    return envoyer(res, 404, JSON.stringify({ erreur: relatif }));
  }
}

// Une page de livre peut être une FIGURE et non du texte : un levé au pas, un
// plan de salle, un arbre de parenté. Le dessin vit dans `ecrans/dessins/` —
// engendré par un script (plan_leves.py et ses frères), jamais tapé à la main —
// et la page ne porte que son nom de fichier. On l'inline au service, comme les
// portraits : la page du jeu ne charge aucune ressource, et un dessin effacé du
// disque laisse une page vide plutôt qu'une image cassée.
//
// Le nom de fichier ne peut pas sortir du dossier : pas de séparateur, pas de
// remontée. Un livre est une donnée de jeu comme une autre, et une donnée de
// jeu ne choisit pas quel fichier le serveur ouvre.
function inlinerFigure(page) {
  if (!page || typeof page !== "object" || !page.figure || page.figure_svg) return;
  const nom = String(page.figure);
  if (!/^[\w.-]+\.svg$/.test(nom) || nom.includes("..")) return;
  try {
    const p = path.join(RACINE, "ecrans", "dessins", nom);
    if (fs.existsSync(p)) page.figure_svg = fs.readFileSync(p, "utf-8");
  } catch (e) {}
}

module.exports = { envoyer, fichierStatique, inlinerFigure };
