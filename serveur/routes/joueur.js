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

// L'arbitre d'un homme hors roster : le MJ de SA zone (habitant.md §3 — le
// front qui incarne un homme d'une autre ville passe son `mj-<ville>`). Dans
// la zone du joueur — celle du siège principal —, on rend null : /verbe prend
// alors son défaut, `mj`.
// Les arbitres incarnables : `mj` et les `mj-*` qui ont une chambre sur
// disque — leur existence n'est pas une fiche, c'est leur domicile. Et un
// domicile a un cahier : les dossiers nes de la migration des canaux
// (mj-aurore, mj-nicolas-reynolds — un relations/ sans claude.md) sont des
// vestiges du modele deux-MJ, pas des arbitres (tranche le 31.8 : le MJ du
// siege principal reste `mj`, jamais mj-rhaenyra).
function arbitres() {
  try {
    return fs.readdirSync(path.join(RACINE, "chambres"))
      .filter((n) => (n === "mj" || n.slice(0, 3) === "mj-") &&
        fs.statSync(path.join(RACINE, "chambres", n)).isDirectory() &&
        fs.existsSync(path.join(RACINE, "chambres", n, "claude.md")))
      .sort();
  } catch (e) { return []; }
}

function arbitreDe(id, ps, l) {
  const p = ps.find((x) => x.id === id);
  const principal = (l || []).find((s) => s.role === "principal");
  const fp = principal && ps.find((x) => x.id === principal.personnage_id);
  const zone = (fp && fp.lieu_id) || null;
  if (!p || !p.lieu_id || !zone || p.lieu_id === zone) return null;
  // La partie ville d'un id de zone se normalise SANS TIRETS (même règle
  // que agents/zone.py : "port-real" → "mj-portreal", jamais "mj-port-real").
  return "mj-" + p.lieu_id.replace(/-/g, "");
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
        const corps = fs.readFileSync(path.join(RACINE, "ecrans", "jeu.html"));
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
        // Un arbitre incarné n'a pas d'arbitre : sa page est un poste
        // d'observation, le front cache la barre des verbes sur ce drapeau.
        moi.mj = !!j.mj;
        // L'arbitre de ses verbes — le front le passera tel quel à /verbe.
        moi.arbitre = j.mj ? null : arbitreDe(j.personnage_id, ps, l);
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
        // Les arbitres, incarnables au même titre (habitant.md — un MJ est
        // un habitant) : le front les groupe sous les hommes.
        arbitres: l ? arbitres().map((id) => ({
          personnage_id: id, nom: "L'arbitre (" + id + ")" })) : [],
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
      // Un arbitre se prend comme un homme : même jeton fabriqué, même
      // serrure — c'est siege.js qui vérifie que sa chambre existe.
      if (!jeton && vers && arbitres().indexOf(vers) !== -1) jeton = "homme:" + vers;
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
