// GET /fils, /depeches, /objectifs et POST /fils — les fils du joueur et ses desseins.
const fs = require("fs");
const path = require("path");
const { RACINE, cheminEtat, dateDe, lireCroyance } = require("../http");
const { envoyer } = require("../http");
const { qui } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/fils") {
      try {
        const siege = qui(req, url);
        const aujourdhui = dateDe(siege);
        const noms = {};
        try {
          JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "personnages.json"), "utf-8"))
            .forEach((p) => { noms[p.id] = p.nom.split(",")[0].trim(); });
        } catch (e) {}
        const brut = lireCroyance("fils.json", siege, null);
        const liste = (brut && Array.isArray(brut.fils)) ? brut.fils : [];
        const fils = liste
          .filter((f) => (f.statut || "en-cours") === "en-cours")
          .map((f) => Object.assign({}, f, {
            // « sans nom » n'est pas un trou d'affichage : c'est l'information.
            // Un fil sur personne revient à la main du joueur, et il doit le voir.
            sur_nom: f.sur ? (noms[f.sur] || String(f.sur).replace(/-/g, " ")) : null,
            mode: f.mode === "delegue" ? "delegue" : "joue",
          }));
        return envoyer(res, 200, JSON.stringify({ fils, aujourdhui }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ fils: [], aujourdhui: null }));
      }
    }
    // ---- qui est ON, maintenant ------------------------------------------
    // Le runtime pose ce marqueur pendant le calcul effectif de toute session
    // d'homme, qu'elle vienne d'un CALL ou d'un CAST détaché. L'ancien registre
    // `etat/parloir/.instances` n'avait plus aucun producteur et laissait donc
    // tous les voyants éteints.
    //
    // Ce n'est PAS une information de fiction — le personnage ne sait rien du
    // fait qu'on le simule — mais ce n'en est pas une du monde non plus : la
    // pastille dit au joueur « cet homme travaille », ce qui est vrai à
    // l'écran. Aucune donnée de son dossier ne descend ici : son id et l'heure
    // de départ du calcul seulement.
    if (url === "/depeches") {
      const dos = path.join(RACINE, ".agents-runtime", "active");
      const actifs = [];
      try {
        for (const f of fs.readdirSync(dos)) {
          const p = path.join(dos, f);
          let d = {};
          try { d = JSON.parse(fs.readFileSync(p, "utf-8") || "{}"); } catch (e) {}
          if (!d.homme || !Number.isInteger(d.pid)) continue;
          // Un kill(pid, 0) ne tue rien : il vérifie que le worker existe. Un
          // crash avant le finally ne peut ainsi laisser un homme "on" à vie.
          try { process.kill(d.pid, 0); } catch (e) { continue; }
          const t = (d.t ? d.t * 1000 : fs.statSync(p).mtimeMs);
          actifs.push({ id: d.homme, depuis: Math.max(0, Math.round((Date.now() - t) / 1000)) });
        }
      } catch (e) {}
      return envoyer(res, 200, JSON.stringify({ actifs }));
    }
    if (url === "/objectifs") {
      try {
        const siege = qui(req, url);
        const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
        const aujourdhui = dateDe(siege);
        const noms = {};
        try {
          lire("personnages.json").forEach((p) => {
            noms[p.id] = p.nom.split(",")[0].trim();
          });
        } catch (e) {}
        // Sans jeton, pas de desseins : la liste vide, mais la date reste —
        // un rail daté vaut mieux qu'un panneau en erreur.
        const miens = lireCroyance("objectifs.json", siege, []);
        const objectifs = (Array.isArray(miens) ? miens : []).map((o) => Object.assign({}, o, {
          source: o.source_id === "vous-meme" ? "Vous-même"
            : noms[o.source_id] || (o.source_id || "").replace(/-/g, " "),
        }));
        return envoyer(res, 200, JSON.stringify({ objectifs, aujourdhui }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ objectifs: [], aujourdhui: null }));
      }
    }
    // LE CALENDRIER — les jours de CE siège, et rien des jours d'un autre.
    //
    // Pourquoi une route et pas une lecture de plus dans le navigateur : un
    // rendez-vous n'est pas un objet du jeu. C'est un `programme` daté à la
    // minute dans evenements.json, un pli qu'on attend, un fil qui tombe, un
    // dessein qui a un terme — quatre tables qui ne se ressemblent pas et
    // qu'il faut coudre sur une même règle horaire. On les coud ici.
    //
    // LE BROUILLARD, ET C'EST LA SEULE RÈGLE DURE : on ne montre un
    // événement que si le siège Y FIGURE (`acteurs` ou `porteur`). Un
    // programme où il n'est pas est le plan d'un autre — le lui afficher
    // serait ouvrir `intentions.json` par la fenêtre du calendrier. Rien
    // n'est deviné : ce qui remonte, il l'a fixé ou on le lui a promis.
  }
  if (req.method === "POST" && url === "/fils") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const d = JSON.parse(corps);
        const siege = qui(req, url);
        const mode = d.mode === "delegue" ? "delegue" : "joue";
        const p = cheminEtat("fils.json", siege);
        if (!p) return envoyer(res, 200, JSON.stringify({ ok: false }));
        const doc = JSON.parse(fs.readFileSync(p, "utf-8"));
        const f = (doc.fils || []).find((x) => x.id === d.fil_id);
        if (!f) return envoyer(res, 200, JSON.stringify({ ok: false }));
        // Un fil sur personne ne se délègue pas : il n'y a personne pour le
        // tenir. Le rail le sait déjà et n'offre pas l'interrupteur, mais on
        // ne se fie pas au navigateur pour une règle du jeu.
        if (mode === "delegue" && !f.sur) {
          return envoyer(res, 200, JSON.stringify({ ok: false, motif: "sans-nom" }));
        }
        f.mode = mode;
        fs.writeFileSync(p, JSON.stringify(doc, null, 1), "utf-8");
        const dossier = siege
          ? path.join(RACINE, "etat", "inbox", siege.personnage_id)
          : path.join(RACINE, "etat", "inbox");
        fs.mkdirSync(dossier, { recursive: true });
        fs.writeFileSync(path.join(dossier, "action-" + Date.now() + ".json"),
          JSON.stringify({
            type: "fil", fil_id: f.id, titre: f.titre, sur: f.sur || null, mode,
            recu_a: new Date().toISOString(),
            joueur_id: siege ? siege.personnage_id : null,
          }, null, 2), "utf-8");
        return envoyer(res, 200, JSON.stringify({ ok: true, mode }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ ok: false }));
      }
    });
    return;
  }
  // ON MARCHE. Le joueur suit un chemin sur la carte ; tous les vingt mètres,
  // le navigateur envoie ici où il en est, et c'est le SERVEUR qui en tire
  // les conséquences — parce qu'elles sont trois et qu'aucune n'est du
  // navigateur : la montre avance, la position s'écrit, et le MJ reçoit ce
  // qu'on vient de longer.
  //
  // UN SEUL FICHIER D'INBOX POUR TOUTE LA BALADE, ET IL N'Y ARRIVE QU'À LA
  // FIN. Un pas tous les vingt mètres fait cinquante fichiers pour un
  // kilomètre, donc cinquante réveils du guetteur pour une seule balade : le
  // MJ serait tiré de son siège à chaque pâté de maisons. Empiler les pas
  // dans un fichier de l'inbox ne suffisait pas à l'éviter — le guetteur
  // sonne dès qu'un fichier NOUVEAU paraît, c'est-à-dire au PREMIER tronçon,
  // pour un sac d'un seul pas, après quoi les pas suivants s'ajoutaient à un
  // fichier que le MJ était censé avoir lu et supprimé. On accumule donc la
  // balade HORS de l'inbox, dans `etat/marches/<siège>.json`, et on ne la
  // DÉPLACE dans l'inbox qu'une fois close : arrivée, ou arrêt en chemin.
  // Le MJ se réveille une fois, lit la trace entière, et raconte la
  // promenade d'un bloc.
  // OÙ JE SUIS, ET RIEN D'AUTRE. La marque sur la carte EST la vraie
  // position — mais `/marche` ne l'écrivait que tous les vingt mètres, parce
  // que c'est le grain du RÉCIT qu'on envoie au MJ. Entre deux rapports, et
  // surtout quand le joueur met en pause ou renonce, la position persistée
  // traînait jusqu'à vingt mètres derrière ce qu'il avait sous les yeux — et
  // c'est elle que lisent la perception, `--entre`, les coûts d'étape et le
  // prochain `croise`.
  //
  // On sépare donc les deux, parce que ce sont deux besoins différents : le
  // récit est cher et se rationne, la position est trois nombres et ne coûte
  // rien. Cette route N'AVANCE PAS LA MONTRE et n'écrit aucun pas — les
  // minutes se paient toujours sur `/marche`, et une position ne se paie pas.
  return false;
}

module.exports = traiter;
