// Le Conseil — mini-serveur de jeu (aucune dépendance).
//
// Ce fichier ne fait plus qu'une chose : ouvrir le port et présenter la
// requête aux routes, dans l'ordre. Tout le reste vit à côté —
// `contexte.js`, `http.js`, `siege.js`, `dates.js`, `portraits.js` pour ce que
// tout le monde partage, `domaine/` pour les moteurs qui ne connaissent ni
// `req` ni `res`, `routes/` pour les URL elles-mêmes, un fichier par famille.
// Voir serveur/CLAUDE.md et docs/serveur-structuration.md.
const http = require("http");
// Les containers voisins entrent par LEUR porte serveur (index.js), jamais
// par un module interne — docs/organisation.md §2.
const monde = require("./monde");
const plan = require("./plan");
const temps = require("./temps");
const peinture = require("./peinture");
const voix = peinture.voix;
const { PORT } = require("./http");
const { envoyer } = require("./http");
const { direLaPeremption } = monde.monde3d;

// L'ORDRE COMPTE, et c'est celui du fichier d'avant : plusieurs routes se
// reconnaissent par préfixe (`/salles` avant `/salles/`, `/monde/` après
// `/chemin`), et la première qui prend la requête la garde. On n'y touche
// qu'en sachant ce qu'on déplace.
const ROUTES = [
  require("./routes/joueur"),      // /, /moi, /bascule
  monde.presence,                  // /presence — qui est où, à cette minute
  plan.atelier,                    // pages d'atelier, /admin, /regie
  monde.chemin,                    // /chemin, /monde/…
  peinture.medias,                 // /retrospective, /medailles, captures, sons
  monde.mondeJeu,                  // /salles, /entites, /gens
  monde.carte,                     // /carte, /ville
  plan.livres,                     // /books, /notes, /nappe, /plis
  monde.terrain,                   // /terrain
  plan.echiquier,                  // /echiquier
  require("./routes/fils"),        // /fils, /depeches, /objectifs (GET et POST)
  temps.calendrier,                // /calendrier
  peinture.routeVoix,              // /voix/*
  require("./routes/scene"),       // /scene — le fil servi au navigateur
  monde.foule,                     // POST /foule/journal
  plan.agenda,                     // POST /agenda, /notes, /nappe
  require("./routes/piece"),       // POST /piece
  monde.marche,                    // POST /ou, /marche
  require("./routes/action"),      // POST /action — la parole du joueur
  require("./routes/verbe"),       // POST /verbe — les trois verbes de l'habitant
];

http
  .createServer((req, res) => {
    const url = req.url.split("?")[0];
    // Une route rend `false` quand elle ne reconnaît pas l'URL — et RIEN
    // d'autre : celles qui répondent en différé (un POST qui attend son corps)
    // ne rendent rien du tout, et ce silence vaut « je m'en charge ».
    for (const route of ROUTES) if (route(req, res, url) !== false) return;
    envoyer(res, 404, JSON.stringify({ erreur: "inconnu" }));
  })
  .listen(PORT, () => {
    voix.direLePort(PORT);
    console.log("Le Conseil écoute sur http://localhost:" + PORT);
    direLaPeremption();
  })
  // Un serveur qui se rabat sur un autre port en silence, c'est deux parties
  // ouvertes en même temps et une salle qui parle en double. On préfère mourir.
  .on("error", (e) => {
    console.error(e.code === "EADDRINUSE"
      ? "Le port " + PORT + " est déjà pris : un serveur du Conseil tourne déjà. " +
        "On ne démarre pas de second serveur — arrêtez l'autre, ou utilisez celui-là."
      : String(e));
    process.exit(1);
  });
