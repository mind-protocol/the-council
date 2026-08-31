// Les pages d'atelier et l'envers du décor : /admin*, /criticite, /regie/*, les
// modules et le style servis au navigateur. Rien de tout cela n'est du jeu.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { chargeActeurs, criticite, detailActivation, filMjActif, prevoirActivations, resumeActivations, sante } = require("../agents").activations; // LA PORTE serveur des agents
const { chercherDansFlux, extraitDuFlux, filPersonnage, regie } = require("../agents").regie; // LA PORTE serveur des agents
const { vueChambres, chambre, rapport } = require("../agents").chambres; // LA PORTE serveur des agents
const { portraitDefaut, portraitFrais } = require("../peinture").portraits; // le composant de portrait du jeu
const { envoyer, fichierStatique } = require("../http");
const { monPersonnage, qui } = require("../http");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/jeu.css") return fichierStatique(res, "jeu.css", "text/css; charset=utf-8");
    // banc d'essai des voix : ne consomme pas le flux, donc ne double personne
    if (url === "/essai-voix") return fichierStatique(res, "essai-voix.html", "text/html; charset=utf-8");
    if (url === "/essai-son") return fichierStatique(res, "essai-son.html", "text/html; charset=utf-8");
    // Un module, ou un module d'une famille : `/modules/monde/relief.js`,
    // `/modules/books/lecture.js`. Rien qui ressemble à un
    // chemin remontant : chaque cran est du minuscule, des chiffres, un tiret
    // ou un souligné — un point ne passe nulle part ailleurs que dans le nom
    // du fichier, donc « .. » ne peut pas se former.
    //
    // TROIS CRANS, ET C'EST LE REFACTOR DU MOTEUR QUI LES A DEMANDÉS. La
    // borne était à un seul, et l'arborescence par acteur (`moteur/commun/`,
    // `moteur/monde/`, `moteur/unite/`…) en demande deux de plus. Un module
    // hors borne ne rendait pas une erreur lisible : il tombait en 404 sur
    // une page qui, elle, se chargeait — et l'on cherchait la faute dans le
    // fichier plutôt que dans la route.
    //
    // LA FEUILLE DE STYLE PASSE PAR ICI AUSSI. Une page qui sort son style en
    // fichier — `bataille.html` l'a fait — se retrouvait servie sans style et
    // sans que rien ne le dise ailleurs que dans la console : la page
    // s'affichait, illisible, et l'on cherchait le défaut dans le CSS.
    const m = url.match(
      /^\/modules\/((?:[a-z0-9_-]+\/){0,3})([a-z0-9_-]+\.(js|css))$/);
    if (m) return fichierStatique(res,
      path.join("modules", ...m[1].split("/").filter(Boolean), m[2]),
      m[3] === "css" ? "text/css; charset=utf-8" : "text/javascript; charset=utf-8");
    // ---- le monde en volume : banc d'essai --------------------------------
    // Une page à part, hors du jeu, pour juger le rendu 3D de Port-Réal avant
    // qu'il ne prenne la place de l'échelle « la ville ». Elle ne consomme ni
    // le flux ni l'inbox : on peut l'ouvrir pendant qu'une partie tourne.
    if (url === "/monde3d") return fichierStatique(res, "monde3d.html", "text/html; charset=utf-8");
    // La régie — l'envers du décor. Elle montre ce que le joueur ne doit
    // jamais voir : à n'ouvrir qu'hors de sa vue. Lecture seule de bout en bout.
    if (url === "/admin") return fichierStatique(res, "admin.html", "text/html; charset=utf-8");
    if (url === "/admin/donnees") {
      try { return envoyer(res, 200, JSON.stringify(regie())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    // L'ENVERS DU MODELE HABITANT. Lecture seule de `chambres/` et des
    // traces d'activite : la frise (qui s'est reveille, qui a parle a qui,
    // quand), la bande des salles, le detail d'une chambre au clic.
    // LES PORTRAITS PAR URL, ET C'EST UNE MESURE DE POIDS. Le jeu les
    // inline partout ; pour la frise des chambres, 56 visages inlines
    // faisaient 459 Ko sur 738 — les deux tiers du paquet, retransmis a
    // chaque chargement. Servis par URL ils partent en parallele, le
    // navigateur les garde, et la vue s'affiche sans les attendre.
    const mvisage = url.match(/^\/portraits\/([a-z0-9_-]+)\.svg$/);
    if (mvisage) {
      const svg = portraitFrais(mvisage[1]) || portraitDefaut(mvisage[1]);
      res.writeHead(200, { "Content-Type": "image/svg+xml; charset=utf-8",
                           "Cache-Control": "max-age=60" });
      return res.end(svg);
    }
    if (url === "/admin/chambres") {
      try { return envoyer(res, 200, JSON.stringify(vueChambres())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    // LE RAPPORT ENTIER D'UNE SESSION, redemande au clic : la vue
    // d'ensemble n'en porte que le strict necessaire.
    const mr = url.match(/^\/admin\/chambres\/rapport\/([0-9][0-9a-zA-Z._-]*\.json)$/);
    if (mr) {
      try {
        const d = rapport(mr[1]);
        if (!d) return envoyer(res, 404, JSON.stringify({ erreur: "pas de rapport" }));
        return envoyer(res, 200, JSON.stringify(d));
      } catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    const mc = url.match(/^\/admin\/chambres\/([a-z0-9-]+)$/);
    if (mc) {
      try {
        const d = chambre(mc[1]);
        if (!d) return envoyer(res, 404, JSON.stringify({ erreur: "pas de chambre" }));
        return envoyer(res, 200, JSON.stringify(d));
      } catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    if (url === "/admin/activations") {
      try { return envoyer(res, 200, JSON.stringify(resumeActivations())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    if (url === "/admin/activations/previsions") {
      try { return envoyer(res, 200, JSON.stringify(prevoirActivations())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    if (url === "/admin/sante") {
      try { return envoyer(res, 200, JSON.stringify(sante())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    // Les pas — la lecture à plat du plan, rangée par ce qu'un pas coûte s'il
    // rate. Hors du jeu et hors de la régie : elle ne montre rien que les
    // livres ne montrent déjà, elle répond seulement à l'autre question,
    // celle qu'aucun registre ne pose — « par quoi commencer ce matin ».
    if (url === "/pas") return fichierStatique(res, "pas.html", "text/html; charset=utf-8");
    // Pas sous `/admin` : ce n'est pas l'envers du decor, c'est une lecture du
    // plan que les livres eux-memes affichent.
    if (url === "/criticite") {
      try { return envoyer(res, 200, JSON.stringify(criticite(monPersonnage(req, url)))); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    if (url === "/admin/charge") {
      try { return envoyer(res, 200, JSON.stringify(chargeActeurs())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    if (url === "/admin/activations/mj-actif") {
      try { return envoyer(res, 200, JSON.stringify(filMjActif())); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    const ma = url.match(/^\/admin\/activations\/([a-zA-Z0-9-]+)$/);
    if (ma) {
      try {
        const detail = detailActivation(ma[1]);
        return detail
          ? envoyer(res, 200, JSON.stringify(detail))
          : envoyer(res, 404, JSON.stringify({ erreur: "activation absente" }));
      } catch (e) {
        return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) }));
      }
    }
    // Le fil d'un homme, refait de bout en bout — ce que Corneille ouvre en
    // touchant un visage sur le plan du château. Réservé aux sièges de régie :
    // ce fil ignore le brouillard, et il n'a rien à faire chez un joueur.
    const mp = url.match(/^\/regie\/personnage\/([a-zA-Z0-9_-]+)$/);
    if (mp) {
      const j = qui(req, url);
      if (!j || !j.regie) return envoyer(res, 403, JSON.stringify({ erreur: "hors régie" }));
      try { return envoyer(res, 200, JSON.stringify(filPersonnage(mp[1]))); }
      catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
    }
    if (url === "/regie/chercher" || url === "/regie/extrait") {
      const j = qui(req, url);
      if (!j || !j.regie) return envoyer(res, 403, JSON.stringify({ erreur: "hors régie" }));
      const p = new URLSearchParams(req.url.split("?")[1] || "");
      try {
        return envoyer(res, 200, JSON.stringify(url === "/regie/chercher"
          ? chercherDansFlux(p.get("q"), Number(p.get("max")) || 12)
          : extraitDuFlux(Number(p.get("de")) || 0, Number(p.get("a")) || 0)));
      } catch (e) {
        return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) }));
      }
    }
    // Le graphe animé ne recharge pas ses milliers de nœuds chaque seconde.
    // Il ne relit que les fronts des sièges, puis extrapole en temps réel
    // jusqu'au prochain changement écrit par append_flux.py.
    if (url === "/admin/horloges") {
      try {
        const horloges = JSON.parse(fs.readFileSync(
          path.join(RACINE, "etat", "horloges.json"), "utf-8"));
        return envoyer(res, 200, JSON.stringify({ horloges, lu_a: Date.now() }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ horloges: {}, lu_a: Date.now() }));
      }
    }
    // La foule : une page d'essai, un point par habitant, la journée en
    // accéléré. Hors du jeu — elle ne lit ni le flux ni l'inbox.
    if (url === "/foule") return fichierStatique(res, "foule.html", "text/html; charset=utf-8");
    const mv = url.match(/^\/vendor\/([a-z0-9_.-]+\.js)$/);
    if (mv) return fichierStatique(res, path.join("vendor", mv[1]), "text/javascript; charset=utf-8");
    // LE CHEMIN À PIED. Deux points en mètres, un itinéraire par les rues.
    // On rend la POLYLIGNE (pour la dessiner) et les MINUTES (pour la
    // montre) : la vitesse n'est pas un réglage, elle sort du chemin.
  }
  return false;
}

module.exports = traiter;
