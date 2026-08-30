// Le Conseil — mini-serveur de jeu (aucune dépendance).
//
// Ce fichier ne fait plus qu'une chose : ouvrir le port et présenter la
// requête aux routes, dans l'ordre. Tout le reste vit à côté —
// `contexte.js`, `http.js`, `siege.js`, `dates.js`, `portraits.js` pour ce que
// tout le monde partage, `domaine/` pour les moteurs qui ne connaissent ni
// `req` ni `res`, `routes/` pour les URL elles-mêmes, un fichier par famille.
// Voir serveur/CLAUDE.md et docs/serveur-structuration.md.
const http = require("http");
const voix = require("./voix");
const { PORT } = require("./contexte");
const { envoyer } = require("./http");
const { direLaPeremption } = require("./monde3d");

// L'ORDRE COMPTE, et c'est celui du fichier d'avant : plusieurs routes se
// reconnaissent par préfixe (`/salles` avant `/salles/`, `/monde/` après
// `/chemin`), et la première qui prend la requête la garde. On n'y touche
// qu'en sachant ce qu'on déplace.
const ROUTES = [
  require("./routes/joueur"),      // /, /moi, /bascule
  require("./routes/presence"),    // /presence — qui est où, à cette minute
  require("./routes/atelier"),     // pages d'atelier, /admin, /regie
  require("./routes/chemin"),      // /chemin, /monde/…
  require("./routes/medias"),      // /retrospective, /medailles, captures, sons
  require("./routes/monde-jeu"),   // /salles, /entites, /gens
  require("./routes/carte"),       // /carte, /ville
  require("./routes/livres"),      // /books, /notes, /nappe, /plis
  require("./routes/terrain"),     // /terrain
  require("./routes/echiquier"),   // /echiquier
  require("./routes/fils"),        // /fils, /depeches, /objectifs (GET et POST)
  require("./routes/calendrier"),  // /calendrier
  require("./routes/voix"),        // /voix/*
  require("./routes/scene"),       // /scene — le fil servi au navigateur
  require("./routes/foule"),       // POST /foule/journal
  require("./routes/vue"),         // POST /vue
  require("./routes/bataille"),    // POST /marque-bataille, commentaires
  require("./routes/agenda"),      // POST /agenda, /notes, /nappe
  require("./routes/piece"),       // POST /piece
  require("./routes/marche"),      // POST /ou, /marche
  require("./routes/action"),      // POST /action — la parole du joueur
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
