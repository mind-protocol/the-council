// GET /partie[?id=<partie>]   — la vue en cartes de la partie (« Le conseil »)
// POST /partie/geste          — une carte posée sur une carte, ou reprise
// POST /partie/jour           — le jour passe
//
// Le calcul et l'écriture vivent dans domaine/partie.js, qui appelle le
// greffier. La seule chose qui s'écrit est le jsonl de la partie : rien de ce
// qui se joue ici ne touche `etat/` — porter un coup dans le monde reste au MJ.
//
// AUCUN RÉVEIL DU MJ ICI, et c'est délibéré. Un coup joué au conseil de guerre
// n'appelle personne : il s'écrit au jsonl, point. Le réveil avait été branché
// sur chaque coup le 3.9 puis retiré le jour même — il notifiait une session
// occupée à autre chose, qui repartait sur son fil sans jouer le camp adverse.
// Le camp d'en face se joue à la ligne, par le MJ, quand le MJ s'en occupe.
const { vue, jouer, partieDe, vuDe, poserVu } = require("../domaine/partie");
const { envoyer } = require("../http");

// Un refus du greffe revient en 200 : c'est une réponse de jeu (« Caraxes est
// déjà posé »), pas une panne, et elle s'affiche sous la carte.
function repondre(req, res, siege) {
  return (err, r) => {
    if (err) return envoyer(res, 502, JSON.stringify({ ok: false, refus: [err.message] }));
    // Le joueur vient de jouer : il a donc regardé. Le marque-page avance,
    // et tout ce que l'autre camp fera d'ici son prochain coup restera neuf.
    if (r && r.ok && r.vue && r.vue.dernier) poserVu(siege, partieDe(req.url), r.vue.dernier);
    return envoyer(res, 200, JSON.stringify(r));
  };
}

function siegeDe(req) {
  try { return require("../http").qui(req, "/partie"); } catch (e) { return null; }
}

function corps(req, suite) {
  let brut = "";
  req.on("data", (c) => {
    brut += c;
    if (brut.length > 64 * 1024) { brut = ""; req.destroy(); }   // un geste tient en trois champs
  });
  req.on("end", () => {
    try { suite(JSON.parse(brut || "{}")); }
    catch (e) { suite(null); }
  });
}

function traiter(req, res, url) {
  if (req.method === "GET" && url === "/partie") {
    const siege = siegeDe(req);
    const id = partieDe(req.url);
    const dejaVu = vuDe(siege, id);
    vue(req.url, "noir", (err, v) => {
      if (err) return envoyer(res, 502, JSON.stringify({ erreur: err.message }));
      // PREMIÈRE OUVERTURE : on pose le marque-page sans rien marquer. C'est
      // ce coup d'œil-ci qui devient l'« avant » ; à partir du prochain, ce
      // que l'autre camp aura fait se verra.
      if (!dejaVu && v && v.dernier) poserVu(siege, id, v.dernier);
      return envoyer(res, 200, JSON.stringify(v));
    }, dejaVu);
    return;   // réponse différée : le silence vaut « je m'en charge »
  }
  if (req.method === "POST" && url === "/partie/geste") {
    corps(req, (g) => {
      if (!g || !g.quoi) return envoyer(res, 400, JSON.stringify({ ok: false, refus: ["geste illisible"] }));
      const siege = siegeDe(req);
      jouer(req.url, "noir", g, repondre(req, res, siege), vuDe(siege, partieDe(req.url)));
    });
    return;
  }
  if (req.method === "POST" && url === "/partie/jour") {
    corps(req, () => {
      const siege = siegeDe(req);
      jouer(req.url, "noir", { quoi: "jour" }, repondre(req, res, siege), vuDe(siege, partieDe(req.url)));
    });
    return;
  }
  return false;
}

module.exports = traiter;
