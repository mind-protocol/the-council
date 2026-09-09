// GET /, /moi, /bascule — qui frappe à la porte, et à quelle table il s'assied.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");
const { qui, roster } = require("../http");

// Les fiches du monde — la liste dans laquelle on peut désormais s'incarner.
function fiches() {
  try {
    const l = JSON.parse(fs.readFileSync(
      path.join(RACINE, "etat", "personnages.json"), "utf-8"));
    return Array.isArray(l) ? l : [];
  } catch (e) { return []; }
}

function mjDisponible() {
  try {
    return fs.statSync(path.join(RACINE, "chambres", "mj")).isDirectory();
  } catch (e) { return false; }
}

// L'ESTAMPILLE DES RESSOURCES — pourquoi elle existe, le 6.9.
//
// La page charge ses feuilles et ses modules par des chemins nus (`/jeu.css`,
// `/modules/partie.css`). Le serveur les envoie déjà en `no-store`, et
// pourtant : tant qu'un onglet reste ouvert, il garde en mémoire le CSS qu'il
// a lu au chargement. On peut donc éditer une feuille, redémarrer le serveur,
// et voir l'ancien rendu — c'est arrivé, et la conclusion qu'on en tire est
// « ça ne marche pas », pas « il faut recharger ».
//
// On colle donc à chaque ressource locale la date de sa dernière écriture. Le
// chemin change quand le fichier change, jamais autrement : le navigateur
// reprend le neuf sans qu'on ait rien à lui demander, et garde le vieux tant
// que rien n'a bougé. Un fichier introuvable est laissé tel quel — on
// n'invente pas une version pour une ressource qu'on ne sert pas.
function estampiller(html) {
  return String(html).replace(/(href|src)="(\/[^"?#]+\.(?:css|js))"/g, (tout, attr, chemin) => {
    try {
      const t = Math.floor(fs.statSync(path.join(RACINE, "ecrans", chemin.slice(1))).mtimeMs);
      return attr + '="' + chemin + "?v=" + t + '"';
    } catch (e) { return tout; }
  });
}

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/") {
      // Un jeton dans l'URL se range dans un cookie : on ne le partage
      // qu'une fois, et le navigateur le represente à chaque requête.
      const j = qui(req, url);
      const entetes = j
        ? { "Set-Cookie": "jeton=" + encodeURIComponent(j.jeton) + "; Path=/; Max-Age=31536000; SameSite=Lax" }
        : null;
      try {
        const corps = estampiller(fs.readFileSync(path.join(RACINE, "ecrans", "jeu.html"), "utf-8"));
        return envoyer(res, 200, corps, "text/html; charset=utf-8", entetes);
      } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: "jeu.html" })); }
    }
    // Qui suis-je à cette table ? Le viewport en a besoin pour dire « Vous »
    // à l'un et « Daemon » à l'autre. Roster absent = partie mono-joueur.
    if (url === "/moi") {
      const l = roster(), j = qui(req, url);
      // `hommes` : tout le reste du monde, incarnable au même titre que les
      // sièges (habitant.md — tout homme est un habitant). Alphabétique ; le
      // front les groupe sous les sièges. Mono-joueur : rien, comme avant.
      const ps = l ? fiches() : [];
      const dedans = new Set((l || []).map((x) => x.personnage_id));
      const moi = j ? { personnage_id: j.personnage_id, nom: j.nom || "", regie: !!j.regie } : null;
      if (moi && j.hors_roster) {
        moi.hors_roster = true;
        moi.mj = !!j.mj;
      }
      return envoyer(res, 200, JSON.stringify({
        multi: !!l,
        // `regie` : ce siège ne joue personne, il regarde. C'est lui qui
        // ouvre le fil d'un homme depuis le plan du château (modules/regie.js).
        moi: moi,
        sieges: (l || []).map((x) => ({ personnage_id: x.personnage_id, nom: x.nom || "" })),
        hommes: ps.filter((p) => !dedans.has(p.id))
          .map((p) => ({ personnage_id: p.id, nom: p.nom || p.id }))
          .sort((a, b) => a.nom.localeCompare(b.nom, "fr")),
        // Le MJ unique est un poste d'observation, jamais un personnage ni
        // le retour des anciens arbitres géographiques.
        arbitres: l && mjDisponible()
          ? [{ personnage_id: "mj", nom: "MJ" }] : [],
      }));
    }
    // Débug — changer de siège sans rouvrir l'URL au jeton. On ne rend JAMAIS
    // les jetons au navigateur : on demande un personnage, le serveur pose le
    // cookie correspondant et renvoie à la racine. Outil de mise au point.
    if (url === "/bascule") {
      const l = roster();
      if (!l) return envoyer(res, 404, JSON.stringify({ erreur: "roster" }));
      const q = (req.url.split("?")[1] || "").match(/(?:^|&)vers=([^&]*)/);
      const vers = decodeURIComponent((q && q[1]) || "");
      const j = qui(req, url);
      // Sans cible : le suivant du roster, en boucle.
      const i = j ? l.findIndex((x) => x.jeton === j.jeton) : -1;
      const cible = vers ? l.find((x) => x.personnage_id === vers) : l[(i + 1) % l.length];
      // Une cible hors roster mais au monde : le jeton fabriqué `homme:<id>`,
      // que `qui()` (serveur/siege.js) résout en siège éphémère. Rien ne
      // s'écrit dans joueurs.json — le roster reste le roster.
      let jeton = cible && cible.jeton;
      if (!jeton && vers && fiches().some((p) => p.id === vers)) jeton = "homme:" + vers;
      if (!jeton && vers === "mj" && mjDisponible()) jeton = "homme:mj";
      if (!jeton) return envoyer(res, 404, JSON.stringify({ erreur: vers }));
      res.writeHead(302, {
        "Set-Cookie": "jeton=" + encodeURIComponent(jeton) + "; Path=/; Max-Age=31536000; SameSite=Lax",
        Location: "/",
      });
      return res.end();
    }
    // ---- la présence : qui partage VOTRE pièce ---------------------------
    // `etat/presence.json` tient une entrée par personnage — se tenir quelque
    // part est un fait du monde, et non une mise en scène privée. Le flux, lui,
    // est cloisonné par `pour` : un PNJ que les deux scènes se partagent
    // apparaissait donc dans les deux pièces à la fois, une par écran, et aucun
    // `sortent` ne pouvait l'ôter des deux (il porte forcément une audience).
    //
    // On ne rend JAMAIS la carte des présences : seulement votre pièce et ceux
    // qui y sont. Où se tient l'autre joueuse, et avec qui, ne descend pas
    // jusqu'à votre machine — le brouillard vaut ici comme partout.
  }
  return false;
}

module.exports = traiter;
