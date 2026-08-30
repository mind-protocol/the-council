// GET /chemin et /monde/* — l'itinéraire à pied et les couches du monde en volume.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");
const { LIEU3D_DEFAUT, butProche, cheminPieton, graphePieton, noeudProche,
        repereProche, serviceMonde } = require("../monde3d");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url.startsWith("/chemin")) {
      try {
        // `url` est déjà rincé de sa requête en tête de routeur : on relit
        // celle de `req.url`, la seule qui la porte encore.
        const q = new URLSearchParams((req.url.split("?")[1]) || "");
        const pt = (s) => (s || "").split(",").map(Number);
        const [ax, ay] = pt(q.get("de")), [bx, by] = pt(q.get("vers"));
        if (![ax, ay, bx, by].every((v) => isFinite(v)))
          return envoyer(res, 400, JSON.stringify({ erreur: "de/vers" }));
        const lieu = q.get("lieu") || LIEU3D_DEFAUT;
        const g = graphePieton(lieu);
        // LE BUT EST UNE PORTE QUAND ON A CLIQUÉ SUR UNE MAISON. Voir
        // `butProche` : c'est là qu'est la règle, et c'est elle qui rend un
        // clic précis sans obliger le joueur à viser au mètre.
        const cible = butProche(lieu, bx, by);
        const [vx, vy] = cible ? [cible.x, cible.y] : [bx, by];
        const a = noeudProche(g, ax, ay), b = noeudProche(g, vx, vy);
        const r = (a < 0 || b < 0) ? null : cheminPieton(g, a, b);
        if (!r) return envoyer(res, 200, JSON.stringify({ chemin: null }));
        const points = r.route.map((i) => [g.xs[i], g.ys[i]]);
        // Les deux bouts sont RACCROCHÉS, pas confondus : on marche du point
        // cliqué jusqu'à la rue, et de la rue jusqu'au but. Sans ces deux
        // segments, la marque saute au premier carrefour venu.
        points.unshift([ax, ay]);
        points.push([vx, vy]);
        let m = 0;
        for (let i = 1; i < points.length; i++)
          m += Math.hypot(points[i][0] - points[i - 1][0],
                          points[i][1] - points[i - 1][1]);
        // CE QU'ON ANNONCE EST CE QU'ON A VISÉ. Le repère le plus proche
        // reste rendu — il situe dans la ville —, mais il ne fait plus office
        // de destination : quand on a cliqué une maison, c'est elle le but,
        // avec son métier et son quartier. Un nommé de la partie
        // (`corps.json`) l'emporte sur son métier : on ne va pas « chez un
        // charpentier » quand on va chez Marlo.
        let nomme = null;
        if (cible) {
          try {
            const aff = JSON.parse(fs.readFileSync(
              path.join(RACINE, "etat", "corps.json"), "utf-8")).affectations || {};
            for (const cle in aff)
              if (aff[cle] && aff[cle].bat === cible.bat)
                { nomme = { cle, nom: aff[cle].nom || cle }; break; }
          } catch (e) { nomme = null; }
        }
        return envoyer(res, 200, JSON.stringify({
          chemin: { points, metres: Math.round(m),
                    minutes: Math.round(r.minutes * 10) / 10 },
          vers: repereProche(lieu, vx, vy),
          but: cible ? Object.assign({}, cible, {
            nom: nomme ? nomme.nom : null, cle: nomme ? nomme.cle : null,
          }) : null,
        }));
      } catch (e) {
        return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) }));
      }
    }
    if (url.startsWith("/monde/")) return serviceMonde(req, res, url.slice("/monde/".length));
    // L'album de la partie : les planches et le moment que chacune fixe.
    // Hors état de jeu — on n'y lit rien, on s'en souvient.
  }
  return false;
}

module.exports = traiter;
