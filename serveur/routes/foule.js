// POST /foule/journal — la page d'essai verse ce qu'elle a vu bouger.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");
const { envoyer } = require("../http");

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/foule/journal") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const { lignes } = JSON.parse(corps);
        if (!Array.isArray(lignes)) throw new Error("lignes");
        const dossier = path.join(RACINE, "monde", "journaux");
        fs.mkdirSync(dossier, { recursive: true });
        const nom = "foule-" + new Date().toISOString().slice(0, 13)
          .replace(/[-T:]/g, "") + ".jsonl";
        const texte = lignes.map((l) => JSON.stringify(l) + "\n").join("");
        fs.appendFileSync(path.join(dossier, nom), texte, "utf-8");
        return envoyer(res, 200, JSON.stringify(
          { ecrit: lignes.length, fichier: "monde/journaux/" + nom }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  // Le joueur écrit dans ses notes : on garde la chaîne TELLE QUELLE, sans
  // la lire, sans la relire au MJ, sans la faire entrer dans la partie. Une
  // écriture complète à chaque fois — c'est un carnet, pas un journal
  // d'événements, et le navigateur en est seul propriétaire.
  // ÉCRIRE DANS UNE CASE DU CALENDRIER — c'est LE JOUEUR qui tient la plume,
  // et ce qu'il écrit compte.
  //
  // Ce que ça n'est pas : une parole, un acte, une minute dépensée. Écrire
  // dans son propre calendrier ne se fait devant personne — aucun PNJ ne
  // l'entend, l'horloge ne bouge pas, rien n'entre dans `paroles.json` ni
  // dans `actes.json`. Le texte vit dans `etat/joueurs/<siège>/agenda.json`
  // (technique, hors docs/schema.md).
  //
  // Ce que ça EST, et c'est le point : une case écrite TOMBE DANS L'INBOX du
  // siège, comme n'importe quelle action. Le guetteur du MJ sonne, il la lit,
  // et c'est à lui de la porter dans le monde — l'homme qu'on fait chercher,
  // le `programme` daté, le pli qui part. Un calendrier que le MJ ne voit pas
  // n'est pas un calendrier, c'est un pense-bête ; et le joueur qui inscrit
  // « voir Rulf à sept heures » a le droit qu'on le lui tienne.
  // UNE VUE DE LA CARTE, POUR QUE LE MJ VOIE CE QUI SE PASSE.
  //
  // Pendant une bataille, il est aveugle au seul moment où ça compte. Il a
  // l'état et les annales du sac — mais où la ligne a cédé, de quel côté la
  // panique court, quelle rue bouchonne, à combien de pas de la porte est
  // l'homme qu'on lui fait jouer : ça se voit d'un coup d'œil et ça se
  // raconte mal. La page compose donc régulièrement le plan, la foule et la
  // bataille en une image centrée sur le joueur, et la dépose ici.
  //
  // UN CHEMIN STABLE, ET UN MOT DANS L'INBOX. `etat/vues/<siège>.png` est
  // écrasé à chaque fois — c'est un miroir posé sur la table, toujours à la
  // même place. Mais un miroir que personne ne regarde ne sert à rien : le
  // MJ ne va pas ouvrir un fichier dont rien ne lui dit qu'il a changé. On
  // dépose donc aussi, comme pour toute action du joueur, une entrée dans
  // `etat/inbox/<siège>/` qui porte le CHEMIN et la légende. Son guetteur
  // sonne, il ouvre l'image, il voit la bataille.
  //
  // L'ENTRÉE PORTE LE LIEN, JAMAIS L'IMAGE. Quarante kilo-octets de base64
  // par ping rendraient l'inbox illisible, et le MJ lit ses fichiers d'un
  // bloc : il n'a besoin que de savoir où regarder.
  //
  // Le rythme est celui des captures (`CADENCE` dans `capture.js`) : si le
  // guetteur sonne trop souvent au goût du MJ, c'est là qu'on l'espace, pas
  // ici. Et comme le MJ lit TOUS ses fichiers d'inbox en une fois, plusieurs
  // pings accumulés pendant qu'il écrivait se lisent ensemble — seul le
  // dernier compte, puisque le PNG est le même fichier écrasé.
  //
  // La légende est écrite À CÔTÉ, en JSON, et pas dessinée dans l'image :
  // une échelle et une heure incrustées dans des pixels ne se citent pas,
  // alors qu'un `metres_par_pixel` se relit et se calcule.
  return false;
}

module.exports = traiter;
