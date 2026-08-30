// POST /vue — l'image d'une bataille déposée pour les yeux du MJ.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");
const { envoyer } = require("../http");
const { qui } = require("../siege");

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/vue") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const { image, meta } = JSON.parse(corps);
        const m = /^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$/
          .exec(image || "");
        if (!m) throw new Error("ce n'est pas une image png, jpeg ou webp");
        const ext = m[1] === "jpeg" ? "jpg" : m[1];
        const siege = qui(req, url);
        const nom = (siege && siege.personnage_id) || "sans-siege";
        const dossier = path.join(RACINE, "etat", "vues");
        fs.mkdirSync(dossier, { recursive: true });
        const octets = Buffer.from(m[2], "base64");
        // Une borne, parce qu'un client peut poster ce qu'il veut. Une vue
        // compressée pèse une dizaine de kilo-octets ; au-delà d'un méga,
        // c'est autre chose et l'on n'en veut pas.
        if (octets.length > 1048576) throw new Error("vue trop lourde");

        // UNE ROTATION DE DIX, PAS UN FICHIER ÉCRASÉ. Une bataille se lit
        // dans son MOUVEMENT — la ligne qui recule de trente mètres entre
        // deux vues dit ce qu'aucune vue seule ne dit. Dix vues à trente
        // secondes font cinq minutes de recul, et à dix kilo-octets pièce
        // c'est cent kilo-octets en tout : moins qu'une seule vue en PNG.
        const GARDE = 10;
        const fichier = nom + "-" + Date.now() + "." + ext;
        fs.writeFileSync(path.join(dossier, fichier), octets);
        // L'index d'abord, le ménage ensuite : on ne supprime un fichier
        // qu'après avoir écrit la liste qui ne le mentionne plus, sinon un
        // MJ qui lit entre les deux ouvre un chemin qui n'existe déjà plus.
        const jindex = path.join(dossier, nom + ".json");
        let vues = [];
        try { vues = JSON.parse(fs.readFileSync(jindex, "utf-8")).vues || []; }
        catch (e) {}
        vues.unshift({
          fichier: "etat/vues/" + fichier,
          octets: octets.length,
          ...(meta && typeof meta === "object" ? meta : {}),
        });
        const jetees = vues.slice(GARDE);
        vues = vues.slice(0, GARDE);
        fs.writeFileSync(jindex, JSON.stringify({
          _: "Les " + GARDE + " dernières vues de la carte envoyées par la " +
             "page de ce siège, la plus RÉCENTE en tête. Une toutes les " +
             "trente secondes tant qu'une bataille est dressée ; le guetteur " +
             "sonne à chaque fois. Ouvrez `vues[0].fichier` pour voir où l'on " +
             "en est, et les suivantes pour voir d'où l'on vient.",
          vues,
        }, null, 2), "utf-8");
        for (const v of jetees) {
          try { fs.unlinkSync(path.join(RACINE, v.fichier)); } catch (e) {}
        }
        // Le guetteur du MJ sonne, comme pour toute action du joueur.
        try {
          const boite = siege
            ? path.join(RACINE, "etat", "inbox", siege.personnage_id)
            : path.join(RACINE, "etat", "inbox");
          fs.mkdirSync(boite, { recursive: true });
          const m = (meta && typeof meta === "object") ? meta : {};
          fs.writeFileSync(path.join(boite, "action-" + Date.now() + ".json"),
            JSON.stringify({
              type: "vue",
              fichier: "etat/vues/" + fichier,
              index: "etat/vues/" + nom + ".json",
              montre: m.montre || null,
              heure: m.heure || null,
              large_en_metres: m.large_en_metres || null,
              metres_par_pixel: m.metres_par_pixel || null,
              couches: m.couches || null,
              bataille: m.bataille || null,
              joueur_id: siege ? siege.personnage_id : null,
              recu_a: new Date().toISOString(),
              _: "Une vue de la carte, centrée sur le joueur, telle qu'il " +
                 "l'a sous les yeux. OUVREZ LE FICHIER : c'est une image, " +
                 "et elle dit d'un coup d'œil ce que trois cents lignes de " +
                 "relevé disent mal — où la ligne a cédé, de quel côté la " +
                 "panique court, à combien de pas de la porte il se tient. " +
                 "Hors fiction : ce n'est ni une parole, ni un acte, ni une " +
                 "minute. Rien à écrire dans l'état, rien à répondre au " +
                 "joueur — c'est pour VOS yeux. Les dix dernières vues sont " +
                 "gardées en rotation et listées dans `index`, la plus " +
                 "récente en tête : les précédentes disent le MOUVEMENT, " +
                 "c'est-à-dire de quel côté ça se déplace, ce qu'une vue " +
                 "seule ne peut pas dire.",
            }, null, 2), "utf-8");
        } catch (e) { /* l'image est écrite : le ping n'est pas vital */ }
        return envoyer(res, 200, JSON.stringify(
          { ecrit: "etat/vues/" + fichier, octets: octets.length,
            gardees: vues.length }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  // UNE MARQUE DE DEBUG DE LA BATAILLE. Elle n'entre ni dans la fiction ni
  // dans l'état canonique : c'est un paquet de preuve laissé par le joueur à
  // ceux qui travaillent sur le moteur. Un dossier autonome contient la
  // capture, le commentaire lisible et toutes les données structurées.
  return false;
}

module.exports = traiter;
