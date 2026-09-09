// GET /partie[?id=<partie>]   — la vue en cartes de la partie (« Le conseil »)
// POST /partie/geste          — une carte posée sur une carte, ou reprise
// POST /partie/jour           — le jour passe (arbitre seulement)
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
const { vue, jouer, ruban, partieDe, campDe, campsDe, vuDe, poserVu } = require("../domaine/partie");
const { envoyer } = require("../http");
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");

// Un refus du greffe revient en 200 : c'est une réponse de jeu (« Caraxes est
// déjà posé »), pas une panne, et elle s'affiche sous la carte.
//
// DEUX ECHECS QUI NE SE RESSEMBLENT PAS (audit du 7.9, B5) : « aucune partie
// ouverte » est une reponse (404, rien a jouer), « le greffe a plante » est une
// panne (502, avec la derniere ligne du traceback — domaine/partie.js l'a deja
// reduite a cela). L'ecran les confondait en « Aucune partie ouverte ».
function repondre(req, res, siege, camp) {
  return (err, r) => {
    if (err) return envoyer(res, 502, JSON.stringify({ ok: false, erreur: "greffe",
                                                        refus: ["le greffe a plante : " + err.message] }));
    if (r && !r.ok && !r.vue && !partieDe(req.url)) {
      return envoyer(res, 404, JSON.stringify(Object.assign({ erreur: "aucune-partie" }, r)));
    }
    // Le joueur vient de jouer : il a donc regardé. Le marque-page avance,
    // et tout ce que l'autre camp fera d'ici son prochain coup restera neuf.
    if (r && r.ok && r.vue && r.vue.dernier) poserVu(siege, partieDe(req.url), r.vue.dernier, camp);
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
  if (req.method === "GET" && url === "/table") {
    // « La table » : la même vue que /partie, mais tout le texte visible —
    // une page à part pour poser sa cognition pendant qu'on joue (ecrans/table.html).
    try { return envoyer(res, 200, fs.readFileSync(path.join(RACINE, "ecrans", "table.html")), "text/html; charset=utf-8"); }
    catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: "table.html" })); }
  }
  if (req.method === "GET" && url.split("?")[0] === "/ruban") {
    // « Le ruban » : tous les coups joués, dans le temps — une voie par camp,
    // une ligne par pièce. Rendu à la demande, jamais écrit.
    return ruban(req.url, (err, html) => err ? envoyer(res, 500, JSON.stringify({ erreur: err.message }))
                                            : envoyer(res, 200, html, "text/html; charset=utf-8"));
  }
  if (req.method === "GET" && url === "/coach") {
    // « Le coach » : la position lue à voix haute — forces, dangers, ligne à
    // tenir — en vues ASCII, à côté du plateau (ecrans/coach.html). Le MJ
    // l'écrit à la main ; ce n'est pas la vue, c'est ce qu'on en pense.
    // UN COACH PAR PARTIE. Il est ecrit a la main pour UNE position : servir
    // celui du pont et du moulin devant un crime de cour n'aide personne. On
    // sert `coach-<partie>.html` s'il existe, le coach generique sinon.
    const idc = partieDe(req.url);
    for (const nom of [idc ? "coach-" + idc + ".html" : null, "coach.html"]) {
      if (!nom) continue;
      try {
        return envoyer(res, 200, fs.readFileSync(path.join(RACINE, "ecrans", nom)),
                       "text/html; charset=utf-8");
      } catch (e) { /* on essaie le suivant */ }
    }
    return envoyer(res, 404, JSON.stringify({ erreur: "aucun coach" }));
  }
  if (req.method === "GET" && url === "/partie") {
    const siege = siegeDe(req);
    const id = partieDe(req.url);
    const camp = campDe(req.url);
    const dejaVu = vuDe(siege, id, camp);
    vue(req.url, null, (err, v) => {
      if (err) return envoyer(res, 502, JSON.stringify({ erreur: "greffe", partie: id,
                                                          detail: "le greffe a plante : " + err.message }));
      // PREMIÈRE OUVERTURE : on pose le marque-page sans rien marquer. C'est
      // ce coup d'œil-ci qui devient l'« avant » ; à partir du prochain, ce
      // que l'autre camp aura fait se verra.
      if (!dejaVu && v && v.dernier) poserVu(siege, id, v.dernier, camp);
      return envoyer(res, 200, JSON.stringify(v));
    }, dejaVu);
    return;   // réponse différée : le silence vaut « je m'en charge »
  }
  if (req.method === "POST" && url === "/partie/geste") {
    corps(req, (g) => {
      if (!g || !g.quoi) return envoyer(res, 400, JSON.stringify({ ok: false, refus: ["geste illisible"] }));
      const siege = siegeDe(req);
      const camp = campDe(req.url);
      // UN CAMP QUI NE JOUE PAS DANS CETTE PARTIE NE JOUE PAS DU TOUT. Le greffe
      // accepte N camps et n'a aucune raison de refuser un nom neuf — c'est
      // voulu. Mais l'ECRAN doit savoir qu'un `?camp=` inconnu est une adresse
      // perimee et non un camp qui entre : le 5.9, un onglet reste sur
      // `?camp=nicolas` du pont et du moulin a depose une demande dans un camp
      // fantome, au milieu d'un crime de cour.
      const camps = campsDe(partieDe(req.url));
      if (camp && camps.size && !camps.has(camp)) {
        return envoyer(res, 400, JSON.stringify({ ok: false, refus: [
          "le camp « " + camp + " » ne joue pas dans cette partie — les camps sont : "
          + [...camps].filter((c) => c !== "arbitre").join(", ")
          + ". Votre onglet est reste sur l'adresse d'une autre partie."] }));
      }
      // LE CORPS NE CHOISIT PAS SON CAMP (audit du 7.9, B1). Le camp est celui
      // que le serveur resout (`?camp=`, puis `_courante.json`) ; un `camp`
      // glisse dans le JSON qui dit autre chose est une usurpation, pas une
      // precision — on le refuse au lieu de le laisser ecraser le vrai.
      if (g.camp != null && String(g.camp) !== String(camp || "")) {
        return envoyer(res, 400, JSON.stringify({ ok: false, refus: [
          "le corps nomme le camp « " + g.camp + " » mais vous jouez « "
          + (camp || "aucun camp") + " » — le camp ne se choisit pas dans le geste."] }));
      }
      // LE JOUR NE PASSE QUE PAR L'ARBITRE (audit du 7.9, B2). Le greffe laisse
      // `jour` a tout camp ; l'ecran ne montre pas le bouton, mais rien ne
      // l'imposait — un camp pouvait faire tomber les menaces de l'autre.
      if (String(g.quoi) === "jour" && camp !== "arbitre") {
        return envoyer(res, 400, JSON.stringify({ ok: false, refus: [
          "seul l'arbitre fait passer le jour — vous jouez « " + (camp || "aucun camp") + " »."] }));
      }
      jouer(req.url, null, g, repondre(req, res, siege, camp),
            vuDe(siege, partieDe(req.url), camp));
    });
    return;
  }
  if (req.method === "POST" && url === "/partie/jour") {
    corps(req, () => {
      const siege = siegeDe(req);
      const camp = campDe(req.url);
      if (camp !== "arbitre") {   // B2 : le jour est a l'arbitre, et a lui seul
        return envoyer(res, 400, JSON.stringify({ ok: false, refus: [
          "seul l'arbitre fait passer le jour — vous jouez « " + (camp || "aucun camp") + " »."] }));
      }
      jouer(req.url, null, { quoi: "jour" }, repondre(req, res, siege, camp),
            vuDe(siege, partieDe(req.url), camp));
    });
    return;
  }
  return false;
}

module.exports = traiter;
