// POST /marque-bataille et les commentaires du dossier d'architecture.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");
const { envoyer } = require("../http");

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/marque-bataille") {
    // Les pages récentes bornent déjà la chronologie. La marge supérieure
    // permet toutefois de sauver une marque produite par un onglet resté
    // ouvert avant ce correctif : le serveur la reçoit, puis garde sa FIN.
    // Au-delà, on cesse réellement d'accumuler le corps en mémoire.
    let corps = "", trop = false, recus = 0;
    req.on("data", (c) => {
      recus += c.length;
      if (recus > 32 * 1024 * 1024) { trop = true; corps = ""; }
      else if (!trop) corps += c;
    });
    req.on("end", () => {
      try {
        if (trop) throw new Error("marque trop lourde");
        const doc = JSON.parse(corps);
        const commentaire = String(doc.commentaire || "").trim();
        if (!commentaire) throw new Error("commentaire vide");
        if (commentaire.length > 8000) throw new Error("commentaire trop long");
        if (!doc.diagnostic || typeof doc.diagnostic !== "object")
          throw new Error("diagnostic manquant");
        // Défense en profondeur pour les anciens clients et les outils qui
        // postent directement. La chronologie est la seule partie sans
        // borne naturelle. On la réduit en partant du dernier item et on
        // laisse une preuve chiffrée de ce qui a été omis.
        const historique = Array.isArray(doc.diagnostic.historique_perceptions)
          ? doc.diagnostic.historique_perceptions : [];
        const metaAvant = doc.diagnostic.historique_perceptions_meta || {};
        const MAX_HISTORIQUE = 512 * 1024;
        let debut = historique.length, octetsHistorique = 2;
        while (debut > 0) {
          const taille = Buffer.byteLength(JSON.stringify(historique[debut - 1]), "utf8") +
            (debut < historique.length ? 1 : 0);
          if (octetsHistorique + taille > MAX_HISTORIQUE &&
              debut < historique.length) break;
          octetsHistorique += taille; debut--;
        }
        const historiqueConserve = historique.slice(debut);
        const totalHistorique = Math.max(historique.length,
          Number(metaAvant.total) || 0,
          historique.length + (Number(metaAvant.omis) || 0));
        const metaHistorique = Object.assign({}, metaAvant, {
          politique: "fin-conservee",
          total: totalHistorique,
          conserve: historiqueConserve.length,
          omis: Math.max(0, totalHistorique - historiqueConserve.length),
          octets_json: octetsHistorique,
          debut_conserve_s: historiqueConserve.length
            ? historiqueConserve[0].temps : null,
          fin_conservee_s: historiqueConserve.length
            ? historiqueConserve[historiqueConserve.length - 1].temps : null,
        });
        doc.diagnostic.historique_perceptions = historiqueConserve;
        doc.diagnostic.historique_perceptions_meta = metaHistorique;
        const m = /^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$/
          .exec(doc.image || "");
        if (!m) throw new Error("capture absente ou invalide");
        const octets = Buffer.from(m[2], "base64");
        if (octets.length > 2 * 1024 * 1024) throw new Error("capture trop lourde");
        const ext = m[1] === "jpeg" ? "jpg" : m[1];
        const brutId = doc.diagnostic.combattant && doc.diagnostic.combattant.id || "homme";
        const id = String(brutId).replace(/[^a-zA-Z0-9_-]/g, "-").slice(0, 60) || "homme";
        const iso = new Date().toISOString();
        const horodatage = iso.replace(/[:.]/g, "-");
        const racine = path.join(RACINE, "captures", "bataille-marques");
        const nomDossier = horodatage + "-" + id;
        const dossier = path.join(racine, nomDossier);
        fs.mkdirSync(dossier, { recursive: true });
        const imageNom = "zone." + ext;
        fs.writeFileSync(path.join(dossier, imageNom), octets);
        const rapport = {
          format: "marque-bataille/v1", cree_a: iso,
          commentaire, lieu: doc.lieu || null, capture: imageNom,
          meta_capture: doc.meta || null, diagnostic: doc.diagnostic,
        };
        fs.writeFileSync(path.join(dossier, "rapport.json"),
          JSON.stringify(rapport, null, 2), "utf-8");
        const h = doc.diagnostic.combattant || {};
        const p = h.pensee || {};
        const md = [
          "# Marque de bataille — " + (h.nom || h.id || "combattant"), "",
          "## Commentaire", "", commentaire, "",
          "## Instant", "",
          "- Créée : " + iso,
          "- Temps de bataille : " + (doc.diagnostic.temps_bataille_s ?? "?") + " s",
          "- Position : " + (doc.lieu && doc.lieu.texte ||
            (h.position ? h.position.x + ", " + h.position.y : "inconnue")),
          "- État : " + (h.etat || "?"),
          "- Pensée : j'essaie de " + (p.action || "?") + " parce que " + (p.raison || "?"),
          "- Système : " + (p.systeme || "?"),
          "- Historique : " + metaHistorique.conserve + " perceptions récentes conservées sur " +
            metaHistorique.total + " (fin préservée" +
            (metaHistorique.omis ? ", " + metaHistorique.omis + " anciennes omises" : "") + ")", "",
          "## Fichiers", "",
          "- `rapport.json` : chronologie perceptive et calculs complets",
          "- `" + imageNom + "` : zone au moment du clic, combattant cerclé", "",
          "![zone marquée](" + imageNom + ")", "",
        ].join("\n");
        fs.writeFileSync(path.join(dossier, "LISEZ-MOI.md"), md, "utf-8");

        fs.mkdirSync(racine, { recursive: true });
        const indexPath = path.join(racine, "index.json");
        let marques = [];
        try { marques = JSON.parse(fs.readFileSync(indexPath, "utf-8")).marques || []; }
        catch (e) {}
        marques.unshift({ dossier: nomDossier, cree_a: iso, combattant: h.nom || h.id,
                          commentaire, temps_bataille_s: doc.diagnostic.temps_bataille_s });
        fs.writeFileSync(indexPath, JSON.stringify({
          _: "Marques de debug déposées depuis la carte, la plus récente en tête.",
          marques,
        }, null, 2), "utf-8");
        return envoyer(res, 200, JSON.stringify({
          ecrit: "captures/bataille-marques/" + nomDossier,
          rapport: "captures/bataille-marques/" + nomDossier + "/rapport.json",
          capture: "captures/bataille-marques/" + nomDossier + "/" + imageNom,
          octets: octets.length,
          historique: metaHistorique,
        }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  // Un commentaire sur une feature du graphe d'architecture. Comme une
  // marque de bataille, il reste hors fiction et hors état canonique ; la
  // clef de feature et l'URL rendent le retour précis et reproductible.
  if (req.method === "POST" && url === "/architecture-bataille/commentaires") {
    let corps = "", trop = false;
    req.on("data", (c) => {
      if (trop) return;
      corps += c;
      if (Buffer.byteLength(corps, "utf8") > 64 * 1024) { trop = true; corps = ""; }
    });
    req.on("end", () => {
      try {
        if (trop) throw new Error("commentaire trop lourd");
        const doc = JSON.parse(corps);
        const feature = String(doc.feature || "").trim();
        const commentaire = String(doc.commentaire || "").trim();
        if (!/^[A-Z]{3}-[A-Z0-9-]{2,48}$/.test(feature))
          throw new Error("feature invalide");
        if (!commentaire) throw new Error("commentaire vide");
        if (commentaire.length > 8000) throw new Error("commentaire trop long");
        const entree = {
          format:"architecture-bataille/commentaire-v1",
          cree_a:new Date().toISOString(), feature,
          titre:String(doc.titre || "").slice(0, 180),
          commentaire,
          url:String(doc.url || "").slice(0, 1000),
          classification:String(doc.classification || "").slice(0, 80),
          visualisation:String(doc.visualisation || "").slice(0, 80),
        };
        const dossier = path.join(RACINE, "captures", "bataille-architecture");
        const fichier = path.join(dossier, "commentaires.jsonl");
        fs.mkdirSync(dossier, { recursive:true });
        fs.appendFileSync(fichier, JSON.stringify(entree) + "\n", "utf-8");
        return envoyer(res, 200, JSON.stringify({
          ecrit:"captures/bataille-architecture/commentaires.jsonl",
          commentaire:entree,
        }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur:String(e.message || e) }));
      }
    });
    return;
  }

  return false;
}

module.exports = traiter;
