// GET /terrain — le champ, quand il y en a un.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");
const { qui, regardeur } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/terrain") {
      // Le champ, quand il y en a un : la troisième échelle du décor. Absent
      // ou vide = pas de terrain, et pas de bascule pour y aller.
      // Un terrain par lieu, même contrat que la ville : `etat/terrains/<lieu>.json`
      // est lu d'abord, `etat/terrain.json` ensuite. Strictement additif — tant
      // qu'aucun fichier ne porte le nom du lieu où se tient le joueur, on sert
      // exactement ce qu'on servait avant. C'est ce qui permet de tenir le champ
      // d'une ville où l'on n'est pas encore sans toucher à celui où l'on est —
      // et, à deux sièges dans deux lieux, de ne pas se marcher dessus.
      try {
        let ou = null;
        try {
          const siege = qui(req, url);
          const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
          const journal = lire("journal.json");
          const moi = regardeur(siege, journal);
          const pj = lire("personnages.json").find((p) => p.id === moi);
          if (pj) ou = pj.lieu_id || null;
        } catch (e) {}
        const fichiers = [];
        // un id de lieu est du kebab-case ; on refuse tout le reste, sinon
        // `..` dans un lieu_id ouvrirait le disque entier.
        if (ou && /^[a-z0-9-]+$/.test(ou)) {
          fichiers.push(path.join(RACINE, "etat", "terrains", ou + ".json"));
        }
        fichiers.push(path.join(RACINE, "etat", "terrain.json"));
        for (const f of fichiers) {
          if (!fs.existsSync(f)) continue;
          const champ = JSON.parse(fs.readFileSync(f, "utf-8"));
          if (!champ || !champ.id) continue;
          // Un champ qui nomme un autre lieu que celui où l'on est n'est pas
          // le nôtre : mieux vaut pas d'échelle qu'une échelle qui ment.
          if (ou && champ.lieu_id && champ.lieu_id !== ou) continue;
          return envoyer(res, 200, JSON.stringify({ champ }));
        }
        return envoyer(res, 200, JSON.stringify({ champ: null }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ champ: null }));
      }
    }
    // L'échiquier : les affaires du conseil, de ce qu'on a jusqu'à ce qu'on
    // veut. RIEN N'EST ÉCRIT À LA MAIN ICI — tout est DÉRIVÉ des six registres
    // par type de `etat/books.json` (`plan-etats-cibles`, `plan-verrous`,
    // `plan-clefs`, `plan-actions`, `plan-moyens`, `plan-offices`), qui sont
    // l'unité de rangement de la maison. Le guide des affaires tranche le cas
    // où les deux divergeraient : « quand les deux se contredisent, c'est le
    // registre qui a raison ». Une vue qui recopierait le plan dans un fichier
    // à part serait un mensonge en attente — il n'y a donc plus de fichier.
    //
    // La chaîne est celle du livre, et l'échiquier l'épouse de bas en haut :
    // moyens et offices, actions, clefs, verrous, états cibles. Un PLATEAU est
    // une affaire.
    //
    // LES ÉTATS CIBLES NE SONT PAS UNE RANGÉE, C'EST UN ARBRE. La colonne
    // `⬆️ Sert` du registre pointe vers l'état AMONT — « 200 sert 100 » —, et
    // les douze états de la Prise de Port-Réal sont en réalité un arbre de
    // quatre niveaux sous une seule racine. Les étaler à plat était un
    // contresens autant qu'un problème de place.
    //
    // Une COLONNE s'ouvre donc sous un état qui porte des verrous, et sous une
    // feuille qui n'en porte aucun — pour qu'une feuille rompue reste comptée.
    // Un état intermédiaire sans verrou ne prend pas de colonne : il COIFFE
    // celles de ses enfants, et sa portée est l'étendue de son sous-arbre.
    //
    // Ce que le serveur dérive et que personne n'écrit : l'arbre, la descente
    // (ce qui pend sous chaque état), la remontée — l'épreuve du guide, « une
    // action qui ne remonte à aucun état cible est une occupation » —, les
    // brèches d'un état (un verrou pour lequel une clef est RETENUE), et les
    // fautes : une pièce sans preuve, une action sans office, un moyen cité
    // qui n'est à aucun registre, une référence qui ne résout pas.
  }
  return false;
}

module.exports = traiter;
