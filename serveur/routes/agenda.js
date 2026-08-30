// POST /agenda, /notes, /nappe — ce que le joueur écrit de sa main, hors fiction.
const fs = require("fs");
const path = require("path");
const { RACINE, cheminNotes } = require("../contexte");
const { envoyer } = require("../http");
const { qui } = require("../siege");

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/agenda") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const { date, heure, texte } = JSON.parse(corps);
        if (!date || typeof heure !== "number") throw new Error("case manquante");
        const siege = qui(req, url);
        const dossier = siege
          ? path.join(RACINE, "etat", "joueurs", siege.personnage_id)
          : path.join(RACINE, "etat");
        const p = path.join(dossier, "agenda.json");
        let liste = [];
        try { liste = JSON.parse(fs.readFileSync(p, "utf-8")).notes || []; } catch (e) {}
        const clef = (d, h) => [d.annee, d.lune, d.jour, h].join("-");
        const k = clef(date, heure);
        liste = liste.filter((n) => clef(n.date, n.heure) !== k);
        const t = String(texte || "").trim();
        if (t) liste.push({ date, heure, texte: t.slice(0, 400) });
        fs.mkdirSync(dossier, { recursive: true });
        fs.writeFileSync(p, JSON.stringify({
          _: "Le calendrier du joueur — ce qu'il a inscrit lui-même dans les " +
             "cases de l'échelle « Les jours ». Ce n'est ni une parole ni un " +
             "acte (personne ne l'a entendu, le temps n'a pas bougé), mais " +
             "c'est SA main : le MJ en est prévenu par l'inbox et c'est à lui " +
             "de le porter dans le monde.",
          notes: liste,
        }, null, 2), "utf-8");
        // Le MJ est prévenu, comme pour toute action du joueur : son guetteur
        // sonne sur l'inbox du siège. Une case effacée se signale aussi — un
        // rendez-vous décommandé est une nouvelle, pas un silence.
        try {
          const boite = siege
            ? path.join(RACINE, "etat", "inbox", siege.personnage_id)
            : path.join(RACINE, "etat", "inbox");
          fs.mkdirSync(boite, { recursive: true });
          fs.writeFileSync(path.join(boite, "action-" + Date.now() + ".json"),
            JSON.stringify({
              type: "agenda",
              action: t ? "inscrit" : "efface",
              date, heure: heure, texte: t,
              joueur_id: siege ? siege.personnage_id : null,
              recu_a: new Date().toISOString(),
              _: "Le joueur a écrit de sa main dans son calendrier (échelle " +
                 "« Les jours »). Hors fiction : ni parole, ni acte, ni minute. " +
                 "À vous de le porter dans le monde s'il y a lieu — l'homme " +
                 "qu'on fait chercher, le `programme` daté, le pli qui part.",
            }, null, 2), "utf-8");
        } catch (e) {}
        return envoyer(res, 200, JSON.stringify({ ok: true, notes: liste }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  if (req.method === "POST" && url === "/notes") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const { texte } = JSON.parse(corps);
        if (typeof texte !== "string") throw new Error("texte manquant");
        const p = cheminNotes(qui(req, url));
        fs.mkdirSync(path.dirname(p), { recursive: true });
        fs.writeFileSync(p, texte, "utf-8");
        return envoyer(res, 200, JSON.stringify({ ok: true }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  // La main qui pousse une pièce. On écrit tout le plateau d'un coup : une
  // nappe fait quelques dizaines de pièces, et une écriture partielle
  // demanderait une identité stable pour chacune — ce qu'une pièce de bois
  // qu'on ramasse et qu'on repose n'a pas.
  if (req.method === "POST" && url === "/nappe") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const { pieces } = JSON.parse(corps);
        if (!Array.isArray(pieces)) throw new Error("pieces manquantes");
        const f = path.join(RACINE, "etat", "nappe.json");
        fs.writeFileSync(f, JSON.stringify({ pieces }, null, 2), "utf-8");
        return envoyer(res, 200, JSON.stringify({ ok: true }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  // PORTER AU REGISTRE. La nappe lit les livres ; ce point d'entrée est le seul
  // par où elle y écrit. Une pièce de craie qu'on ne porte pas au registre
  // n'existe pas : au prochain conseil, personne ne la retrouve. On écrit donc
  // DEUX FOIS, comme partout ailleurs — la ligne dans l'affaire, la même dans
  // le registre transversal, avec la colonne Affaire renseignée.
  //
  // Le numéro n'est pas donné par le client : il se calcule ici, dans la plage
  // de l'affaire, selon la forme. Un état prend la centaine libre suivante ;
  // un verrou, une clef, une action prennent leur rang dans la centaine de
  // leur parent. C'est la règle de numérotation, et elle n'est pas négociable
  // depuis une page web.
  return false;
}

module.exports = traiter;
