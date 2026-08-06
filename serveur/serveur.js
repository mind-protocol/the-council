// Le Conseil — mini-serveur de jeu (aucune dépendance).
// GET  /                → ecrans/jeu.html
// GET  /jeu.css         → ecrans/jeu.css
// GET  /modules/x.js    → ecrans/modules/x.js
// GET  /scene           → etat/flux.jsonl cumulé → {items:[...]}
// POST /action          → etat/inbox/action-<ts>.json
const http = require("http");
const fs = require("fs");
const path = require("path");
const voix = require("./voix");

const RACINE = path.join(__dirname, "..");
// 3129 est le port du jeu. Un atelier (vérification d'écran pendant qu'une
// partie tourne) passe un port en argument ou par PORT, pour ne pas se
// disputer le port de la partie en cours.
const PORT = Number(process.argv[2]) || Number(process.env.PORT) || 3129;

// ---- les têtes : où l'on CROIT que sont les gens ------------------------
// `personnages.lieu_id` est la vérité, et la vérité n'a rien à faire sur une
// table de guerre. `etat/vues.json` porte l'autre moitié : la dernière position
// CONNUE du joueur, avec sa date et de quelle bouche il la tient. Ce module la
// projette en pièces de carte — et la fait vieillir, parce que le sel n'est pas
// la position, c'est son âge.
const JOURS_PAR_LUNE = 30, LUNES_PAR_AN = 12;
const jourAbsolu = (d) => d && d.annee != null
  ? ((d.annee * LUNES_PAR_AN + (d.lune - 1)) * JOURS_PAR_LUNE) + (d.jour - 1) : null;

// Une nouvelle ne reste pas fraîche : de semaine en semaine, ce qu'on tenait
// pour sûr redevient un on-dit, puis se perd. Au-delà, on ne montre plus rien —
// une carte honnête montre aussi ses trous.
const PALIERS = [[7, null], [21, "rapportee"], [45, "rumeur"]];

function vieillir(certitude, age) {
  if (age == null) return certitude;
  for (const [seuil, degre] of PALIERS) if (age <= seuil) return degre || certitude;
  return null;                        // trop vieux : la tête sort de la table
}

const AGE_DIT = (n) => n <= 0 ? "aujourd'hui" : n === 1 ? "hier"
  : "il y a " + n + " jours";

function envoyer(res, code, corps, type, entetes) {
  res.writeHead(code, Object.assign({
    "Content-Type": type || "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  }, entetes || {}));
  res.end(corps);
}

// ---- les sièges : qui est à la table ------------------------------------
// `etat/joueurs.json` est un roster EN DUR — technique, hors docs/schema.md :
// [{jeton, personnage_id, nom}]. Le jeton fait office de clé : on ouvre le jeu
// une fois sur /?jeton=xxx, le serveur pose un cookie, et tout ce qui suit est
// signé. Sans roster, le jeu reste mono-joueur et rien ne change.
function roster() {
  try {
    const l = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "joueurs.json"), "utf-8"));
    return Array.isArray(l) && l.length ? l : null;
  } catch (e) { return null; }
}

// L'audience de la scene ouverte, lue dans le flux : le dernier `effacer`
// porte le `pour` de la scene en cours (voir scripts/append_flux.py). Le
// serveur doit la connaitre parce qu'il ecrit lui aussi dans le flux — la
// parole du joueur — et qu'une replique lachee sans audience dans une scene
// privee part droit chez l'autre camp.
function audienceCourante() {
  try {
    const brut = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8");
    let pour = null;
    brut.split("\n").forEach((l) => {
      if (!l.trim()) return;
      try {
        const it = JSON.parse(l);
        if (it.type === "effacer") pour = it.pour || null;
      } catch (e) {}
    });
    return pour;
  } catch (e) { return null; }
}

// Qui frappe à la porte ? Le jeton d'abord (une URL qu'on partage), le cookie
// ensuite (les visites suivantes). Un jeton inconnu n'est personne.
function qui(req, url) {
  const l = roster();
  if (!l) return null;
  const q = (req.url.split("?")[1] || "").match(/(?:^|&)jeton=([^&]*)/);
  const c = (req.headers.cookie || "").match(/(?:^|;\s*)jeton=([^;]*)/);
  const jeton = decodeURIComponent((q && q[1]) || (c && c[1]) || "");
  return l.find((j) => j.jeton === jeton) || null;
}

function fichierStatique(res, relatif, type) {
  try {
    const corps = fs.readFileSync(path.join(RACINE, "ecrans", relatif));
    return envoyer(res, 200, corps, type);
  } catch (e) {
    return envoyer(res, 404, JSON.stringify({ erreur: relatif }));
  }
}

http
  .createServer((req, res) => {
    const url = req.url.split("?")[0];
    if (req.method === "GET") {
      if (url === "/") {
        // Un jeton dans l'URL se range dans un cookie : on ne le partage
        // qu'une fois, et le navigateur le represente à chaque requête.
        const j = qui(req, url);
        const entetes = j
          ? { "Set-Cookie": "jeton=" + encodeURIComponent(j.jeton) + "; Path=/; Max-Age=31536000; SameSite=Lax" }
          : null;
        try {
          const corps = fs.readFileSync(path.join(RACINE, "ecrans", "jeu.html"));
          return envoyer(res, 200, corps, "text/html; charset=utf-8", entetes);
        } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: "jeu.html" })); }
      }
      // Qui suis-je à cette table ? Le viewport en a besoin pour dire « Vous »
      // à l'un et « Daemon » à l'autre. Roster absent = partie mono-joueur.
      if (url === "/moi") {
        const l = roster(), j = qui(req, url);
        return envoyer(res, 200, JSON.stringify({
          multi: !!l, moi: j ? { personnage_id: j.personnage_id, nom: j.nom || "" } : null,
          sieges: (l || []).map((x) => ({ personnage_id: x.personnage_id, nom: x.nom || "" })),
        }));
      }
      if (url === "/jeu.css") return fichierStatique(res, "jeu.css", "text/css; charset=utf-8");
      // banc d'essai des voix : ne consomme pas le flux, donc ne double personne
      if (url === "/essai-voix") return fichierStatique(res, "essai-voix.html", "text/html; charset=utf-8");
      const m = url.match(/^\/modules\/([a-z0-9_-]+\.js)$/);
      if (m) return fichierStatique(res, path.join("modules", m[1]), "text/javascript; charset=utf-8");
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
          let joueur_id = null;
          try { joueur_id = lire("journal.json").personnage_joueur_id || null; } catch (e) {}
          const gens = lire("personnages.json")
            .filter((p) => p.etat !== "mort")
            .map((p) => {
              const m = maisons[p.maison_id] || null;
              let portrait_svg = "";
              const f = p.portrait && p.portrait.fichier;
              if (f) {
                try { portrait_svg = fs.readFileSync(path.join(RACINE, f), "utf-8"); } catch (e) {}
              }
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
      if (url === "/carte") {
        try {
          const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
          const maisons = {};
          lire("maisons.json").forEach((m) => (maisons[m.id] = m));
          const lieux = lire("lieux.json").map((l) => ({
            id: l.id, nom: l.nom, type: l.type, controle_id: l.controle_id,
            allegeance: (maisons[l.controle_id] || {}).allegeance_affichee || "neutre",
          }));
          let joueur_lieu_id = null, date = null, joueur_id_carte = null;
          try {
            const journal = lire("journal.json");
            const pj = lire("personnages.json").find((p) => p.id === journal.personnage_joueur_id);
            if (pj) { joueur_lieu_id = pj.lieu_id || null; joueur_id_carte = pj.id; }
          } catch (e) {}
          try { date = lire("monde.json").date || null; } catch (e) {}
          // Ce que la table PORTE : osts, flottes, marches, sièges, serments.
          // Ce fichier n'est PAS la vérité du monde — c'est ce que le joueur
          // croit tenir, avec sa `certitude`. Absent = table nue.
          let jetons = [], traits = [], zones = [];
          try {
            const t = lire("jetons.json");
            const vif = (m) => !m.statut || m.statut === "actif";
            jetons = (t.jetons || []).filter(vif);
            traits = (t.traits || []).filter(vif);
            zones = t.zones || [];
          } catch (e) {}
          // Les têtes : projetées de `vues.json`, jamais de `lieu_id`. Elles se
          // posent SOUS le point de la place (les osts s'empilent au-dessus),
          // et elles pâlissent toutes seules avec les jours.
          try {
            const persos = {};
            lire("personnages.json").forEach((p) => (persos[p.id] = p));
            // La couche carte a ses propres ids ; `alias` fait le pont.
            const alias = {};
            lire("lieux.json").forEach((l) => {
              alias[l.id] = (l.alias && l.alias[0]) || l.id;
            });
            const aujourdhui = jourAbsolu(date);
            const tetes = [];
            (lire("vues.json").vues || []).forEach((v) => {
              const p = persos[v.personnage_id];
              if (!p || p.etat === "mort" || p.id === joueur_id_carte) return;
              const quand = jourAbsolu(v.date);
              const age = (quand != null && aujourdhui != null)
                ? Math.max(0, aujourdhui - quand) : null;
              const presume = v.canal === "presume";
              const cert = presume ? (v.certitude || "rapportee")
                : vieillir(v.certitude || "sure", age);
              if (!cert) return;                       // trop vieux : on ne sait plus
              const m = maisons[p.maison_id] || {};
              tetes.push({
                id: "tete-" + p.id,
                genre: "tete",
                camp: m.allegeance_affichee || "neutre",
                ou: alias[v.lieu_id] || v.lieu_id,
                nom: p.nom.split(",")[0].trim(),
                dec: [0, 11],
                certitude: cert,
                detail: [presume ? "on l'y suppose" : AGE_DIT(age),
                         v.source, v.note].filter(Boolean).join(" — "),
                statut: "actif",
                _frais: presume ? 9999 : (age == null ? 9999 : age),
              });
            });
            // Une place où l'on croit savoir dix têtes ferait une colonne de
            // noms plus haute que le royaume. On en montre trois — les plus
            // fraîches — et la quatrième pièce dit combien on en tait.
            const parPlace = {};
            tetes.sort((a, b) => a._frais - b._frais)
              .forEach((t) => (parPlace[t.ou] = parPlace[t.ou] || []).push(t));
            Object.keys(parPlace).forEach((ou) => {
              const l = parPlace[ou];
              l.slice(0, 3).forEach((t) => { delete t._frais; jetons.push(t); });
              if (l.length > 3) {
                const reste = l.slice(3);
                jetons.push({
                  id: "tetes-" + ou, genre: "tete", camp: "neutre", ou,
                  nom: "et " + reste.length + " autres", dec: [0, 11],
                  certitude: "rapportee", statut: "actif",
                  detail: reste.map((t) => t.nom).join(", "),
                });
              }
            });
          } catch (e) {}
          return envoyer(res, 200,
            JSON.stringify({ lieux, joueur_lieu_id, date, jetons, traits, zones }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ lieux: [], erreur: String(e) }));
        }
      }
      // La ville : l'échelle intermédiaire — hors les murs, mais pas le royaume.
      // Même contrat que le terrain : fichier absent ou sans `id` = pas de
      // bascule pour y aller.
      if (url === "/ville") {
        try {
          const champ = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "ville.json"), "utf-8"));
          return envoyer(res, 200, JSON.stringify({ champ: champ && champ.id ? champ : null }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ champ: null }));
        }
      }
      if (url === "/terrain") {
        // Le champ, quand il y en a un : la troisième échelle du décor. Absent
        // ou vide = pas de terrain, et pas de bascule pour y aller.
        try {
          const champ = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "terrain.json"), "utf-8"));
          return envoyer(res, 200, JSON.stringify({ champ: champ && champ.id ? champ : null }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ champ: null }));
        }
      }
      // Vos desseins : la page complète des objectifs, avec ce que la liste du
      // rail ne peut pas porter — l'échéance, le nombre de jours qui reste, et
      // de quelle bouche la chose est venue. Rien d'occulte : ce sont les
      // objectifs du joueur, pas ceux des autres.
      if (url === "/objectifs") {
        try {
          const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
          let aujourdhui = null;
          try { aujourdhui = lire("monde.json").date || null; } catch (e) {}
          const noms = {};
          try {
            lire("personnages.json").forEach((p) => {
              noms[p.id] = p.nom.split(",")[0].trim();
            });
          } catch (e) {}
          const objectifs = lire("objectifs.json").map((o) => Object.assign({}, o, {
            source: o.source_id === "vous-meme" ? "Vous-même"
              : noms[o.source_id] || (o.source_id || "").replace(/-/g, " "),
          }));
          return envoyer(res, 200, JSON.stringify({ objectifs, aujourdhui }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ objectifs: [], aujourdhui: null }));
        }
      }
      if (url === "/voix/liste") return envoyer(res, 200, JSON.stringify(voix.liste()));
      // qui a demandé quoi, et ce qu'on lui a répondu — pour diagnostiquer un doublon
      if (url === "/voix/journal") return envoyer(res, 200, JSON.stringify(voix.lireJournal()));
      if (url === "/scene") {
        try {
          const brut = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8");
          let items = brut.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
          // Le brouillard, à deux : un item peut porter `pour: "<personnage>"`
          // — une pensée, une question, un aparté. Il ne part qu'à celui-là.
          // Le tri se fait ICI et non dans le navigateur : ce qui n'est pas
          // pour vous ne descend jamais jusqu'à votre machine.
          if (roster()) {
            const j = qui(req, url);
            const moi = j && j.personnage_id;
            items = items.filter((it) => !it.pour || it.pour === moi);
          }
          return envoyer(res, 200, JSON.stringify({ items }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ items: [] }));
        }
      }
    }
    if (req.method === "POST" && url === "/voix/dire") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", async () => {
        try {
          const d = JSON.parse(corps);
          // une phrase plus longue que le bail : le lecteur le renouvelle en route
          if (d.renouveler) return envoyer(res, 200, JSON.stringify({ ok: voix.bail(d.client_id) }));
          const r = await voix.dire(d.locuteur_id, d.texte, d.client_id);
          if (r.audio) return envoyer(res, 200, r.audio, "audio/mpeg");
          return envoyer(res, r.code, JSON.stringify({ erreur: r.erreur }));
        } catch (e) {
          return envoyer(res, 500, JSON.stringify({ erreur: String(e) }));
        }
      });
      return;
    }
    if (req.method === "POST" && url === "/action") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", () => {
        try {
          const action = JSON.parse(corps);
          action.recu_a = new Date().toISOString();
          // Signature du siège : sans elle, le MJ ne saurait pas lequel des
          // deux vient de parler. Roster absent = rien ne change.
          const siege = qui(req, url);
          if (siege) action.joueur_id = siege.personnage_id;
          // À deux MJ, chacun guette SON joueur : l'action tombe dans le
          // sous-dossier de son siège. Sans roster (ou siège inconnu), tout
          // atterrit à la racine comme avant — le guetteur d'une partie seule
          // ne voit aucune différence.
          const dossier = siege
            ? path.join(RACINE, "etat", "inbox", siege.personnage_id)
            : path.join(RACINE, "etat", "inbox");
          fs.mkdirSync(dossier, { recursive: true });
          fs.writeFileSync(path.join(dossier, "action-" + Date.now() + ".json"),
            JSON.stringify(action, null, 2), "utf-8");
          // Ce que le joueur dit ou fait entre dans le flux : sans cela, sa parole
          // n'existe que dans le navigateur et disparaît au premier rechargement.
          if (action.type === "libre" && (action.texte || "").trim()) {
            // Une question est hors fiction : elle ne devient jamais une parole
            // prononcée par le personnage. Les coulisses le sont plus encore :
            // on y parle DE la partie, et rien de ce qui s'y dit n'a eu lieu.
            // Hors fiction, c'est une affaire privée : une question ou une
            // remarque de coulisses ne part qu'à celui qui l'a posée. Ce qui
            // est DIT ou FAIT, en revanche, se joue devant tout le monde.
            const prive = siege ? { pour: siege.personnage_id } : {};
            const item = action.mode === "question"
              ? Object.assign({ type: "question", texte: action.texte, delai_s: 0 }, prive)
              : action.mode === "meta"
              ? Object.assign({ type: "meta", texte: action.texte, delai_s: 0 }, prive)
              : Object.assign(
                  { type: "vous", mode: action.mode || "dire", texte: action.texte, delai_s: 0,
                    joueur_id: siege ? siege.personnage_id : undefined },
                  // Ce qui est dit dans une scene privee y reste : le joueur
                  // herite de l'audience de la scene, comme tout le reste.
                  audienceCourante() ? { pour: audienceCourante() } : {});
            fs.appendFileSync(path.join(RACINE, "etat", "flux.jsonl"),
              JSON.stringify(item) + "\n", "utf-8");
          }
          return envoyer(res, 200, JSON.stringify({ ok: true }));
        } catch (e) {
          return envoyer(res, 400, JSON.stringify({ ok: false, erreur: String(e) }));
        }
      });
      return;
    }
    envoyer(res, 404, JSON.stringify({ erreur: "inconnu" }));
  })
  .listen(PORT, () => {
    voix.direLePort(PORT);
    console.log("Le Conseil écoute sur http://localhost:" + PORT);
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
