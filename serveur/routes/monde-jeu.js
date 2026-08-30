// GET /salles, /entites, /gens — les gens et les lieux, servis au décor.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");
const { portraitDefaut, portraitFrais } = require("../portraits");
const { qui } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/salles") {
      try {
        const dossier = path.join(RACINE, "ecrans", "salles");
        const ids = fs.readdirSync(dossier)
          .filter((n) => /\.(jpg|jpeg|png|webp)$/i.test(n))
          .map((n) => n.replace(/\.[^.]+$/, ""));
        return envoyer(res, 200, JSON.stringify({ salles: ids }));
      } catch (e) { return envoyer(res, 200, JSON.stringify({ salles: [] })); }
    }
    if (url.startsWith("/salles/")) {
      const nom = path.basename(decodeURIComponent(url.slice("/salles/".length)));
      const ext = path.extname(nom).toLowerCase();
      const types = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp" };
      if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
      try {
        const corps = fs.readFileSync(path.join(RACINE, "ecrans", "salles", nom));
        res.writeHead(200, { "Content-Type": types[ext], "Cache-Control": "public, max-age=86400" });
        return res.end(corps);
      } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
    }
    if (url === "/entites") {
      try {
        const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
        const vus = new Set();
        const entites = [];
        const ajouter = (id, type, noms) => {
          const propres = noms.filter((n) => n && n.length > 2 && !vus.has(n.toLowerCase()));
          if (!propres.length) return;
          propres.forEach((n) => vus.add(n.toLowerCase()));
          entites.push({ id, type, noms: propres });
        };
        const persos = lire("personnages.json");
        const prenoms = {};
        persos.forEach((p) => {
          const t = p.nom.split(/[ ,]/)[0];
          prenoms[t] = (prenoms[t] || 0) + 1;
        });
        persos.forEach((p) => {
          const noms = [p.nom.split(",")[0].trim()];
          const prenom = p.nom.split(/[ ,]/)[0];
          if (prenoms[prenom] === 1) noms.push(prenom);
          ajouter(p.id, "personnage", noms);
        });
        lire("lieux.json").forEach((l) => ajouter(l.id, "lieu", [l.nom]));
        lire("maisons.json").forEach((m) => ajouter(m.id, "maison", [m.nom]));
        [["caraxes", "Caraxès"], ["vhagar", "Vhagar"], ["meleys", "Meleys"], ["syrax", "Syrax"],
         ["vermax", "Vermax"], ["arrax", "Arrax"], ["revefeu", "Rêvefeu"], ["sunfyre", "Sunfyre"],
         ["gosier", "le Gosier"]].forEach(([id, n]) => ajouter(id, id === "gosier" ? "lieu" : "dragon", [n]));
        return envoyer(res, 200, JSON.stringify({ entites }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ entites: [], erreur: String(e) }));
      }
    }
    // Les gens : qui est qui, et de quel côté. Une vue de mémoire, pas de
    // renseignement — on n'y donne NI position, NI intentions, NI allégeance
    // réelle : le nom, le rôle, la maison, et le camp affiché.
    if (url === "/gens") {
      try {
        const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
        const maisons = {};
        lire("maisons.json").forEach((m) => {
          maisons[m.id] = m;
          maisons[m.id.replace(/^maison-/, "")] = m;
        });
        // Qui porte la couronne du « joueur » sur CET ecran : celui qui
        // regarde, pas celui du journal. A deux, le journal designe Rhaenyra —
        // l'ecran d'Aurore marquait donc la reine comme le personnage joue.
        const siege = qui(req, url);
        let joueur_id = (siege && siege.personnage_id) || null;
        if (!joueur_id) {
          try { joueur_id = lire("journal.json").personnage_joueur_id || null; } catch (e) {}
        }
        const gens = lire("personnages.json")
          .filter((p) => p.etat !== "mort")
          .map((p) => {
            const m = maisons[p.maison_id] || null;
            // Tout le monde a un rond : faute de portrait dessiné, la
            // silhouette anonyme tient la place.
            let portrait_svg = "";
            const f = p.portrait && p.portrait.fichier;
            if (f) {
              try { portrait_svg = fs.readFileSync(path.join(RACINE, f), "utf-8"); } catch (e) {}
            }
            // LE CHAMP `portrait.fichier` N'EST PAS UNE CONDITION D'EXISTENCE.
            // Il manquait à une bonne part des fiches, et ces gens-là gardaient
            // la silhouette anonyme alors que leur médaillon était peint et
            // posé sur le disque — un manque invisible, puisque rien n'échoue.
            // `medaillons.py` écrit toujours `ecrans/portraits/<id>.svg` : cet
            // id EST l'adresse. On la tente donc quand le champ ne dit rien,
            // et peindre un visage suffit désormais à le faire paraître.
            if (!portrait_svg) portrait_svg = portraitFrais(p.id) || "";
            if (!portrait_svg) portrait_svg = portraitDefaut(p.nom || p.id);
            return {
              id: p.id, nom: p.nom, titre: p.titre || "",
              maison_id: m ? m.id : null,
              // une maison sans fiche (les grands lointains : Stark, Arryn…)
              // garde tout de même son nom, tiré de son id
              maison: m ? m.nom : p.maison_id
                ? p.maison_id.replace(/^maison-/, "").replace(/-/g, " ")
                    .replace(/(^|\s)\p{Ll}/gu, (c) => c.toUpperCase())
                : "Sans maison",
              camp: m ? (m.allegeance_affichee || "neutre") : "neutre",
              joueur: p.id === joueur_id,
              portrait_svg,
            };
          });
        return envoyer(res, 200, JSON.stringify({ gens }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ gens: [], erreur: String(e) }));
      }
    }
  }
  return false;
}

module.exports = traiter;
