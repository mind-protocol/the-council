// Le Conseil — mini-serveur de jeu (aucune dépendance).
// GET  /                → ecrans/jeu.html
// GET  /jeu.css         → ecrans/jeu.css
// GET  /modules/x.js    → ecrans/modules/x.js
// GET  /scene           → etat/flux.jsonl cumulé → {items:[...]}
// POST /action          → etat/inbox/action-<ts>.json
const http = require("http");
const fs = require("fs");
const path = require("path");
const os = require("os");
const childProcess = require("child_process");
const voix = require("./voix");
const bibliotheque = require("./bibliotheque");
// Ce qu'un marcheur perçoit d'une bataille cuite. Muet tant qu'il n'y a pas de
// `etat/bataille.json` — c'est-à-dire tout le temps, sauf les soirs où il y en
// a une.
const croiser = require("./croiser");

// Les tests d'intégration servent une partie miniature dans un dossier
// temporaire. En production, l'absence de variable garde le dépôt courant.
const RACINE = process.env.CONSEIL_RACINE
  ? path.resolve(process.env.CONSEIL_RACINE) : path.join(__dirname, "..");
// 3129 est le port du jeu. Un atelier (vérification d'écran pendant qu'une
// partie tourne) passe un port en argument ou par PORT, pour ne pas se
// disputer le port de la partie en cours.
const PORT = Number(process.argv[2]) || Number(process.env.PORT) || 3129;
// Longueur d'une fenêtre de fil servie au navigateur. Le reste du passé se
// réclame page par page (`/scene?avant=N`) quand le joueur remonte la
// chronique. Le fichier, lui, garde tout — c'est la mémoire de la partie.
//
// 500 était trop : rien n'est perdu, mais tout est MONTÉ. Cinq cents entrées
// font autant de nœuds vivants dans la chronique, avec leurs vieillissements
// et leurs survols, et le défilement se paie à chaque image.
//
// 80 est calé sur la SCÈNE et non sur la session : un conseil fait une
// quarantaine de répliques, donc la fenêtre porte celle qu'on joue et celle
// d'avant. Ce qui précède est du passé qu'on relit, et il redescend tout seul
// quand on remonte (`/scene?avant=N`). Descendre plus bas ferait paginer à
// l'intérieur d'une même scène — c'est là qu'est la limite, pas dans le coût.
const MAX_FIL = 80;

// La silhouette anonyme, servie à qui n'a pas encore de portrait dessiné :
// personne n'apparaît sans son rond. Le gabarit est lu une fois ; sa teinte
// est tirée du NOM, pour que deux inconnus ne se confondent pas et que le
// même homme garde sa couleur d'un écran à l'autre. Même calcul côté Python
// (`scripts/append_flux.py`) : les deux doivent tomber sur la même couleur.
let _defautSvg = null;
function teinteDuNom(nom) {
  let h = 0;
  for (const c of String(nom || "")) h = (h * 31 + c.codePointAt(0)) % 360;
  return h;
}
// LE PORTRAIT INLINÉ DANS LE FLUX EST DATÉ DU JOUR DE LA POUSSÉE, et il ne
// vieillit pas bien : `append_flux.py` recopie le SVG dans l'item au moment où
// on l'écrit, si bien qu'un homme poussé avant qu'on lui peigne un visage garde
// sa silhouette « Portrait inconnu » pour toujours — dans tout l'historique, et
// jusque dans la galerie des présents de la scène en cours.
//
// On ne réécrit pas `flux.jsonl` pour autant : il est append-only, et une
// réécriture casserait les curseurs des navigateurs ouverts. On rafraîchit à la
// SERVITURE — le fichier sur disque fait foi au moment où l'on sert. Peindre un
// portrait suffit donc à le faire apparaître partout, y compris dans le passé.
//
// Le cache se contrôle sur la date du fichier : `medaillons.py` peut refaire un
// visage pendant que le serveur tourne, il part au premier `/scene` suivant.
const _portraitsFrais = new Map();
function portraitFrais(id) {
  if (!id || /[^a-zA-Z0-9_-]/.test(id)) return null;
  const p = path.join(RACINE, "ecrans", "portraits", id + ".svg");
  let m;
  try { m = fs.statSync(p).mtimeMs; } catch (e) { return null; }
  const tenu = _portraitsFrais.get(id);
  if (tenu && tenu.m === m) return tenu.svg;
  try {
    const svg = fs.readFileSync(p, "utf-8");
    _portraitsFrais.set(id, { m, svg });
    return svg;
  } catch (e) { return null; }
}
function rafraichirPortraits(it) {
  ["presents", "entrent"].forEach((k) => {
    (it[k] || []).forEach((p) => {
      if (!p || typeof p !== "object") return;
      const svg = portraitFrais(p.id);
      if (svg) p.portrait_svg = svg;
    });
  });
}
function portraitDefaut(nom) {
  if (_defautSvg === null) {
    try {
      _defautSvg = fs.readFileSync(
        path.join(RACINE, "ecrans", "portraits", "_defaut.svg"), "utf-8");
    } catch (e) { _defautSvg = ""; }
  }
  const h = teinteDuNom(nom);
  return _defautSvg
    .replace(/\{\{CLE\}\}/g, String(nom || "x").replace(/[^a-zA-Z0-9_-]/g, "") || "x")
    .replace(/\{\{TEINTE\}\}/g, `hsl(${h},32%,52%)`)
    .replace(/\{\{TEINTE_SOMBRE\}\}/g, `hsl(${h},22%,22%)`)
    .replace(/\{\{TEINTE_ETOFFE\}\}/g, `hsl(${h},20%,28%)`)
    .replace(/\{\{TEINTE_CHAIR\}\}/g, `hsl(${h},18%,38%)`)
    .replace(/\{\{TEINTE_FOND\}\}/g, `hsl(${h},18%,17%)`);
}

// ---- les têtes : où l'on CROIT que sont les gens ------------------------
// `personnages.lieu_id` est la vérité, et la vérité n'a rien à faire sur une
// table de guerre. `etat/vues.json` porte l'autre moitié : la dernière position
// CONNUE du joueur, avec sa date et de quelle bouche il la tient. Ce module la
// projette en pièces de carte — et la fait vieillir, parce que le sel n'est pas
// la position, c'est son âge.
const JOURS_PAR_LUNE = 30, LUNES_PAR_AN = 12;
// Les dates s'écrivent de deux façons dans l'état : le triplet partout, et la
// forme courte « 129.3.22 » dans `mains.json`. On accepte les deux plutôt
// que de laisser une régie muette sur la moitié des fichiers.
const jourAbsolu = (d) => {
  if (typeof d === "string") {
    const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(d.trim());
    d = m ? { annee: +m[1], lune: +m[2], jour: +m[3] } : null;
  }
  return d && d.annee != null
    ? ((d.annee * LUNES_PAR_AN + (d.lune - 1)) * JOURS_PAR_LUNE) + (d.jour - 1) : null;
};

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

// ---- les croyances, une par joueur --------------------------------------
// `vues`, `jetons`, `objectifs` ne décrivent pas le monde : ils décrivent ce
// qu'UN joueur croit du monde. À deux, les partager revient à donner la table
// de guerre de la reine à sa maîtresse de la voix. Chacun a donc son dossier —
// `etat/joueurs/<personnage_id>/` — et l'on retombe sur `etat/` quand il existe
// encore : une partie seule ne voit aucune différence.
//
// Le repli racine peut être absent (archivé une fois les deux joueuses
// migrées) : on rend alors null plutôt qu'un chemin qui n'ouvre rien. Un
// visiteur sans jeton n'a AUCUNE croyance à lui — il ne doit pas hériter de
// celles d'autrui, et une table vide est la seule réponse honnête.
function cheminEtat(nom, siege) {
  if (siege) {
    const p = path.join(RACINE, "etat", "joueurs", siege.personnage_id, nom);
    if (fs.existsSync(p)) return p;
  }
  const racineNom = path.join(RACINE, "etat", nom);
  return fs.existsSync(racineNom) ? racineNom : null;
}

// Une page de livre peut être une FIGURE et non du texte : un levé au pas, un
// plan de salle, un arbre de parenté. Le dessin vit dans `ecrans/dessins/` —
// engendré par un script (plan_leves.py et ses frères), jamais tapé à la main —
// et la page ne porte que son nom de fichier. On l'inline au service, comme les
// portraits : la page du jeu ne charge aucune ressource, et un dessin effacé du
// disque laisse une page vide plutôt qu'une image cassée.
//
// Le nom de fichier ne peut pas sortir du dossier : pas de séparateur, pas de
// remontée. Un livre est une donnée de jeu comme une autre, et une donnée de
// jeu ne choisit pas quel fichier le serveur ouvre.
function inlinerFigure(page) {
  if (!page || typeof page !== "object" || !page.figure || page.figure_svg) return;
  const nom = String(page.figure);
  if (!/^[\w.-]+\.svg$/.test(nom) || nom.includes("..")) return;
  try {
    const p = path.join(RACINE, "ecrans", "dessins", nom);
    if (fs.existsSync(p)) page.figure_svg = fs.readFileSync(p, "utf-8");
  } catch (e) {}
}

// Les notes du joueur — un carnet HORS FICTION. Ce n'est pas un livre du monde
// et ce n'est pas une croyance : personne dans la salle ne l'écrit, aucun PNJ
// ne le lit, le MJ n'y touche pas. Du texte brut, gardé tel quel, un fichier
// par siège — ce que la reine griffonne n'est pas ce que griffonne sa
// maîtresse de la voix. Contrairement à `cheminEtat`, on rend le chemin où le
// fichier DEVRA s'écrire, même s'il n'existe pas encore.
function cheminNotes(siege) {
  return siege
    ? path.join(RACINE, "etat", "joueurs", siege.personnage_id, "notes.txt")
    : path.join(RACINE, "etat", "notes.txt");
}

// Les croyances du demandeur, ou le défaut fourni quand il n'en a pas.
function lireCroyance(nom, siege, defaut) {
  const p = cheminEtat(nom, siege);
  if (!p) return defaut;
  try { return JSON.parse(fs.readFileSync(p, "utf-8")); } catch (e) { return defaut; }
}

// L'heure de CE joueur. Le front de chacun vit dans `etat/horloges.json`
// (tenu par scripts/append_flux.py) ; `monde.date` n'est que le minimum des
// fronts — la date acquise pour tout le monde, celle du tick. Servir celle-là
// au navigateur ferait vieillir la carte d'un joueur au rythme du plus lent.
function dateDe(siege) {
  let monde = null;
  try { monde = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "monde.json"), "utf-8")).date || null; } catch (e) {}
  if (!siege) return monde;
  try {
    const h = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "horloges.json"), "utf-8"));
    if (h && h[siege.personnage_id]) return h[siege.personnage_id];
  } catch (e) {}
  return monde;
}

// OÙ EST TOUT LE MONDE, à cette minute-là — le calcul, pas le cache.
// `scripts/presence.py --json` fait le travail : routines, topologie, marche en
// cours. On ne le refait pas à chaque sonde (le navigateur en tire une toutes
// les quinze secondes, et par siège) : la réponse vaut tant que ni l'heure
// demandée ni les trois fichiers d'entrée n'ont bougé. Un échec rend null, et
// l'appelant retombe sur l'instantané figé — le jeu ne s'arrête pas pour ça.
let cachePresence = null;
function resoudrePresence(date) {
  if (!date) return null;
  let cle = [date.annee, date.lune, date.jour, date.minute].join(".");
  for (const f of ["presence.json", "routines.json", "chemins.json"]) {
    try { const s = fs.statSync(path.join(RACINE, "etat", f)); cle += "|" + s.mtimeMs; }
    catch (e) { cle += "|?"; }
  }
  if (cachePresence && cachePresence.cle === cle) return cachePresence.gens;
  let gens = null;
  try {
    gens = JSON.parse(childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "presence.py"), "--json", "--quand", cle.split("|")[0]],
      { cwd: RACINE, encoding: "utf-8", timeout: 20000,
        windowsHide: true, maxBuffer: 8 * 1024 * 1024,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) })).gens || null;
  } catch (e) { gens = null; }
  cachePresence = { cle, gens };
  return gens;
}

// L'ÉCART DE FRONT — de combien ce joueur devance ou traîne sur l'autre.
// À deux, les horloges divergent : l'un tient un conseil de trois heures
// pendant que l'autre traverse la cour. Tant que l'écart reste petit, personne
// n'a besoin de le savoir ; passé quelques heures, une scène commune devient
// impossible sans que l'un des deux le sache, et c'est ce que dit le signe.
// Rend un nombre de minutes signé (positif = en avance), ou null.
const ECART_SEUIL = 300; // 5 heures
function absolues(d) {
  if (!d) return null;
  return ((((d.annee || 0) * 12 + (d.lune || 0)) * 30 + (d.jour || 0)) * 1440)
    + (typeof d.minute === "number" ? d.minute : 0);
}
function ecartDe(siege) {
  const l = roster();
  if (!siege || !l || l.length < 2) return null;
  let h;
  try { h = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "horloges.json"), "utf-8")); }
  catch (e) { return null; }
  const mien = absolues(h && h[siege.personnage_id]);
  if (mien === null) return null;
  // On se compare aux sièges OCCUPÉS : un siège vacant avance au fil du monde
  // et n'a personne devant l'écran à qui l'écart voudrait dire quelque chose.
  const autres = l.filter((j) => j.personnage_id !== siege.personnage_id && j.occupe !== false)
    .map((j) => absolues(h && h[j.personnage_id])).filter((m) => m !== null);
  if (!autres.length) return null;
  // Le plus grand écart en valeur absolue : c'est celui qui gêne.
  let pire = 0;
  autres.forEach((m) => { if (Math.abs(mien - m) > Math.abs(pire)) pire = mien - m; });
  return Math.abs(pire) >= ECART_SEUIL ? pire : null;
}

// L'audience de la scene ouverte, lue dans le flux : le dernier `effacer`
// porte le `pour` de la scene en cours (voir scripts/append_flux.py). Le
// serveur doit la connaitre parce qu'il ecrit lui aussi dans le flux — la
// parole du joueur — et qu'une replique lachee sans audience dans une scene
// privee part droit chez l'autre camp.
// A DEUX JOUEURS, L'AUDIENCE N'EST PAS GLOBALE. Chacun est dans SA scene :
// pendant que la reine tient audience dans la grande salle, l'autre monte a la
// roukerie. Le dernier `effacer` du fichier appartient alors a n'importe qui —
// et prendre celui-la revient a estampiller la parole de l'un au nom de l'autre,
// ce qui la fait disparaitre de son propre ecran pour s'afficher sur celui d'en
// face. On ne retient donc que les `effacer` qui concernent CE joueur : les
// siens, et les scenes explicitement communes, qui valent pour tout le monde.
//
// UN `pour` ABSENT NE VEUT PAS DIRE « COMMUN ». Il dit « rien n'a ete declare »,
// et c'est le cas de TOUT le flux anterieur au passage a deux joueurs. Confondre
// les deux a coute une fuite entiere : la parole de la reine, heritant d'un
// `effacer` de l'ere mono-joueur, partait publique — donc sur l'ecran de sa
// maitresse de la voix, indefiniment, parce qu'aucun `effacer` ne portait son
// nom. On ne conclut donc au commun que sur le marqueur POSITIF `commun: true`
// que pose `append_flux.py --pour tous`.
//
// Rend "commun", un id de siege, ou null quand rien n'est etabli — trois etats
// distincts, parce que l'appelant doit pouvoir se fermer sur le troisieme.
function audienceCourante(siegeId, depuis) {
  try {
    const brut = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8");
    let pour = null;
    brut.split("\n").filter((l) => l.trim())
      // Ce qui precede l'arrivee du joueur a la table ne parle pas de lui : ces
      // scenes-la n'ont jamais eu d'audience a declarer.
      .slice(depuis || 0)
      .forEach((l) => {
        try {
          const it = JSON.parse(l);
          // UNE SCENE COMMUNE NE SE REFERME PAS TOUTE SEULE. Ne relire que les
          // `effacer` laissait « commun » en place indefiniment : le MJ rouvre
          // la scene privee d'un joueur avec une `salle` ou une simple replique
          // `--pour <lui>`, jamais avec un second `effacer`. L'audience restait
          // donc commune des heures apres, et tout ce que ce joueur TAPAIT
          // repartait sans `pour` — donc public, donc sur l'ecran du troisieme
          // siege, qui n'avait jamais mis les pieds dans cette salle.
          // Un item nominativement adresse a ce joueur seul REETABLIT donc son
          // audience privee. On exige un `pour` scalaire : un tableau est une
          // messe basse a l'interieur d'une scene, pas une scene nouvelle.
          if (it.type !== "effacer") {
            if (siegeId && it.pour === siegeId) pour = siegeId;
            return;
          }
          // La scene d'un tiers ne dit rien de l'endroit ou celui-ci se trouve.
          // `pour` peut nommer PLUSIEURS oreilles (une piece partagee, une
          // messe basse) : on y est concerne des qu'on y figure.
          if (it.pour && siegeId && (Array.isArray(it.pour)
                ? it.pour.indexOf(siegeId) === -1 : it.pour !== siegeId)) return;
          pour = it.pour || (it.commun ? "commun" : null);
        } catch (e) {}
      });
    return pour;
  } catch (e) { return null; }
}

// Qui frappe à la porte ? Le jeton d'abord (une URL qu'on partage), le cookie
// ensuite (les visites suivantes). Un jeton inconnu n'est personne.
// Sur QUI se centre ce qu'on rend — la carte, la ville, le terrain. C'est celui
// qui regarde, et non le personnage-joueur du journal : une carte centrée sur
// Peyredragon quand on est ailleurs ment sur l'endroit d'où l'on parle.
//
// Sauf pour un siège de RÉGIE, qui n'a pas de fiche et n'est donc nulle part :
// il regarde par-dessus l'épaule du siège principal. Sans cela sa carte n'a ni
// centre ni plan de château — et c'est le plan qu'il vient chercher, puisque
// c'est là qu'il touche un visage pour en ouvrir le fil.
function regardeur(siege, journal) {
  if (siege && siege.regie) {
    const principal = (roster() || []).find((s) => s.role === "principal");
    return (principal && principal.personnage_id) ||
      (journal && journal.personnage_joueur_id) || null;
  }
  return (siege && siege.personnage_id) ||
    (journal && journal.personnage_joueur_id) || null;
}

function qui(req, url) {
  const l = roster();
  if (!l) return null;
  const q = (req.url.split("?")[1] || "").match(/(?:^|&)jeton=([^&]*)/);
  const c = (req.headers.cookie || "").match(/(?:^|;\s*)jeton=([^;]*)/);
  const jeton = decodeURIComponent((q && q[1]) || (c && c[1]) || "");
  return l.find((j) => j.jeton === jeton) || null;
}

// QUI VOIT QUEL VOLUME — le tri de l'étagère, en un seul endroit.
// Les boîtes d'abord (un volume rangé prend la place de son coffret), puis les
// trois règles : les `lecteurs` nommés retirent, un porteur garde son privé,
// et le reste se lit dans le château où l'on est.
//
// PARTAGÉ AVEC L'ÉCHIQUIER, et c'est la raison d'être de cette fonction : le
// damier lisait `books.json` en entier, sans tri. Un homme de Port-Réal qui
// tient ses propres affaires y voyait donc les quarante-deux plateaux du
// conseil de Peyredragon, et pas un des siens. Un plan qu'on ne peut pas
// ouvrir dans les livres n'a rien à faire sur le damier ; deux tris qui
// divergent finissent par montrer à l'un le plan de l'autre.
function volumesVisibles(tous, moi) {
  // Où est chacun : c'est la fiche qui le dit, jamais le livre.
  const ou = {};
  try {
    JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "personnages.json"), "utf-8"))
      .forEach((p) => { ou[p.id] = p.lieu_id || null; });
  } catch (e) {}
  const ici = moi ? (ou[moi] || null) : null;
  // Les BOÎTES (etat/boites.json) : un coffret posé sur une table ou porté
  // sous le bras, où l'on range des volumes. Une boîte donne sa PLACE à ce
  // qu'elle contient — un volume rangé n'a plus de salle, plus de porteur,
  // plus de `prive` à lui : il prend ceux du coffret, et l'on déplace vingt
  // registres en déplaçant une boîte. On résout ici, AVANT le tri : sans quoi
  // un volume rangé n'aurait plus de place du tout, et le brouillard le
  // laisserait passer partout.
  let boites = [];
  try {
    const bb = JSON.parse(fs.readFileSync(
      path.join(RACINE, "etat", "boites.json"), "utf-8"));
    if (Array.isArray(bb)) boites = bb;
  } catch (e) {}
  const coffret = new Map(boites.map((c) => [c.id, c]));
  tous.forEach((b) => {
    const c = b.boite && coffret.get(b.boite);
    if (!c) return;
    b.lieu_id = c.lieu_id || null;
    b.salle_id = c.salle_id || null;
    b.acteur_id = c.acteur_id || null;
    b.prive = !!c.prive;
    // `lecteurs` ne se remplace pas, il s'ajoute : un coffret peut fermer plus
    // que le volume, jamais moins.
    if (Array.isArray(c.lecteurs) && c.lecteurs.length) {
      b.lecteurs = (Array.isArray(b.lecteurs) && b.lecteurs.length)
        ? b.lecteurs.filter((q) => c.lecteurs.indexOf(q) !== -1)
        : c.lecteurs.slice();
    }
  });
  // Le château d'un volume : celui où il est posé, ou celui où se trouve
  // l'homme qui le porte — sa fiche d'abord, le `lieu_id` du livre à défaut
  // (un porteur sans fiche reste où on l'a écrit).
  const chateau = (b) => (b.acteur_id && ou[b.acteur_id] !== undefined)
    ? ou[b.acteur_id] : (b.lieu_id || null);
  const liste = tous.filter((b) => {
    // `lecteurs` ne donne rien, il retire : le volume garde ses règles de
    // lieu, mais qui n'y est pas nommé ne l'ouvre pas.
    if (Array.isArray(b.lecteurs) && b.lecteurs.length
        && b.lecteurs.indexOf(moi) === -1) return false;
    if (b.acteur_id && b.acteur_id === moi) return true;
    if (b.prive && b.acteur_id) return false;
    const ch = chateau(b);
    return !ch || !ici || ch === ici;
  });
  return { liste, boites };
}

// Le personnage derrière une requête : le siège si l'on en tient un, le
// personnage joueur du journal à défaut. Rendu `null` quand un roster existe
// et qu'aucun jeton ne va avec — on ne sert alors rien plutôt que tout.
function monPersonnage(req, url) {
  const siege = qui(req, url);
  let moi = (siege && siege.personnage_id) || null;
  if (!moi && roster()) return null;
  if (!moi) {
    try {
      moi = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "journal.json"), "utf-8"))
        .personnage_joueur_id || null;
    } catch (e) {}
  }
  return moi;
}

function fichierStatique(res, relatif, type) {
  try {
    const corps = fs.readFileSync(path.join(RACINE, "ecrans", relatif));
    return envoyer(res, 200, corps, type);
  } catch (e) {
    return envoyer(res, 404, JSON.stringify({ erreur: relatif }));
  }
}

// ---- les dossiers de recherche, servis en lecture ------------------------
// L'onglet « Les dossiers » de `/bataille` donne à LIRE ce sur quoi le modèle
// est fondé — pas seulement la bibliographie : le raisonnement, les tableaux,
// les réserves, et la section finale qui confronte le dossier au code.
//
// ON NE RECOPIE RIEN ET ON NE RÉÉCRIT RIEN : le markdown part tel quel, et
// c'est la page qui le rend. Un dossier corrigé est à jour au rechargement
// suivant, et il n'existe nulle part de seconde version à tenir — c'est
// exactement le défaut qu'on paie ailleurs (la huitième liste de la chaîne,
// cf. l'en-tête de `sac.js`).
//
// Les deux comptes du rail ne disent pas la même chose : `references` est ce
// qui est cité, `liens` ce qu'on peut aller lire tout de suite. Un dossier de
// livres imprimés a beaucoup des premières et peu des seconds, et l'écart est
// une information sur sa nature.
function dossiersRecherche() {
  const dossier = path.join(RACINE, "docs", "recherche");
  let noms;
  try {
    noms = fs.readdirSync(dossier).filter((f) => f.endsWith(".md")).sort();
  } catch (e) { return []; }

  return noms.map((nom) => {
    const texte = fs.readFileSync(path.join(dossier, nom), "utf-8");
    const lignes = texte.split(/\r?\n/);
    const titre = (lignes.find((l) => l.startsWith("# ")) || "# " + nom).slice(2).trim();

    let sections = 0, references = 0, liens = 0, dansSources = false;
    for (const l of lignes) {
      if (l.startsWith("## ")) {
        sections++;
        dansSources = /^##\s+Sources\b/.test(l);
        continue;
      }
      if (!dansSources) continue;
      if (l.trim().startsWith("- ")) references++;
      liens += (l.match(/\]\(https?:\/\//g) || []).length;
    }

    return { fichier: nom, titre, texte,
             compte: { sections, references, liens, signes: texte.length } };
  });
}

// ---- le monde en volume ---------------------------------------------------
// `monde/portreal.*.json` est l'atelier : le relief (grille de 10 m), le bâti
// (48 000 volumes en colonnes) et le graphe (36 Mo, toutes couches). On ne
// jette pas 36 Mo au navigateur : la voirie est TAILLÉE ici, couche par couche,
// et le résultat est gardé en mémoire tant que le fichier n'a pas rebougé — la
// chaîne (relief → graphe → densifier → coudre) réécrit ces fichiers en cours
// de session, et la page doit voir la version du moment sans qu'on redémarre.
//
// Le sous-sol et les passages cachés ne descendent que si on les demande
// nommément : c'est de la vérité brute, et `connu_de` y est écrit en clair.
// Les lieux que le monde 3D sait montrer. Un lieu = trois fichiers au même
// format (relief, bâti, graphe) et, quand il en a une à la bonne échelle, une
// carte 2D dont on tire la muraille. Peyredragon n'en a pas : son dessin est à
// 260 unités pour l'île entière quand celui de Port-Réal est à 12 m l'unité —
// ses murs sont donc livrés déjà en mètres dans son `bati`, et `carte` est nul.
const LIEUX3D = {
  "port-real": {
    nom: "Port-Réal", sous: "les trois collines, les sept portes et la Néra",
    prefixe: "portreal", carte: path.join("etat", "villes", "port-real.json"),
    vue: [[9200, -2600, 2600], [2900, 1700, 40]],
    // Trois hauteurs de regard sur le même lieu, du plus large au plus serré.
    // C'est ce que lit `?echelle=` du banc d'essai et ce que prend l'échelle
    // « la ville » du décor — qui s'ouvre sur `ville`, jamais sur la baie.
    vues: {
      ville: [[4300, 3450, 1150], [2750, 1900, 40]],
      // À la verticale du Donjon Rouge : un plan, pas une perspective. Une vue
      // oblique flatte la silhouette et ment sur les distances — or c'est
      // justement pour mesurer une cour et un chemin de ronde qu'on l'ouvre.
      // Centré sur l'ENCEINTE du Donjon (3504-4224 × 960-1560 d'après la carte),
      // pas sur le repère qui en nomme le donjon. Presque à la verticale — 14°
      // de biais depuis le sud, assez pour que les tours aient un flanc et une
      // ombre, trop peu pour qu'on cesse de lire les distances comme sur un plan.
      chateau: [[3864, 1057, 835], [3864, 1260, 40]],
      salle: [[2810, 2210, 34], [2760, 2280, 22]],
    },
    // Où le joueur se tient quand il est dans ce lieu — la place forte, pas la
    // ville entière. C'est ce que la balise de `monde/vous.js` va planter dans
    // le relief : sans elle, l'échelle « la ville » montre un beau caillou dont
    // rien ne dit qu'on est dedans.
    vous: [3864, 1260, 40],
    // CE QUE LA VILLE CONTIENT. Le monde en volume est bâti par VILLE, mais un
    // joueur peut se tenir dans un BÂTIMENT : si `personnages.lieu_id` passait
    // de « port-real » à un id de maison, `ville3d` ne trouverait plus de lieu
    // à son nom et les trois hauteurs — la ville, le quartier, vous —
    // disparaîtraient de la rangée. Un bâtiment de Port-Réal EST à Port-Réal :
    // on l'écrit ici, une fois, le jour où l'un d'eux devient un lieu.
    //
    // Vide pour l'instant, et c'est juste : nos sièges se tiennent à
    // « port-real » et « peyredragon », qui sont les clefs de cette table.
    contient: [],
  },
  peyredragon: {
    nom: "Peyredragon", sous: "l'île, le Dragonmont et la rade",
    prefixe: "peyredragon",
    // Le château est servi en VRAI maillage (parois épaisses, portes percées),
    // pas en boîtes : deux cents mètres, ça se paie. Du coup la carte n'a plus
    // de muraille à donner — elle serait un doublon de ce que le maillage porte.
    carte: null, maillage: true,
    // De QUOI ce lieu est tiré, et par quel fichier on date sa dernière
    // génération. Le modèle et les fichiers servis sont deux choses distinctes :
    // toucher l'un sans relancer l'autre fait diverger le jeu et les images
    // SANS RIEN CASSER — c'est arrivé deux fois (des salles d'un plan abandonné,
    // une courtine restée à 26 m). On date, donc, et on le dit.
    sources: ["scripts/materialisation", "scripts/monde/peyredragon.py"],
    temoin: "monde/peyredragon.maillage.json",
    regenerer: "python scripts/monde/peyredragon.py",
    vue: [[6100, 1500, 1300], [4400, 2100, 120]],
    // Le maillage tient entre x 4316-4973 et y 1938-2227, jusqu'à 205 m :
    // le château se prend du sud-est, la salle à hauteur de cour.
    vues: {
      // MESURÉ DANS LE PANNEAU, pas déduit. À 1 300 m d'altitude l'île tenait
      // dans le cadre mais le château y faisait dix pixels : un onglet de 490
      // par 430 n'est pas un banc d'essai plein écran, et un cadrage qui va
      // bien sur l'un est vide sur l'autre. À 430 m et 620 de recul, la roche
      // remplit douze quinzièmes de la hauteur et la mer tient le reste.
      ville: [[5186, 1689, 430], [4820, 2038, 60]],
      // Centré sur le maillage, cadré serré sur son cœur plutôt que sur ses 657 m
      // d'un bout à l'autre — on vient voir une place forte, pas la mesurer. Et
      // 14° de biais depuis le sud : les tours gagnent un flanc sans que le plan
      // cesse de se lire.
      //
      // MESURÉ, pas estimé. Le cadrage d'avant ([[4913,1917,130],[4645,2082,55]])
      // disait 14° et en faisait 77 : la caméra était à SIX mètres au-dessus du
      // plateau du château (124 m) et visait un point à mi-falaise. Ce n'était
      // pas un quartier vu de haut, c'était une vue de plain-pied qui empilait
      // les trente-quatre salles dans deux cents pixels — d'où plus aucun nom
      // possible dessus. Le cœur bâti fait 289 × 241 m autour de [4459, 2099] ;
      // à 402 m de recul et 14° depuis la verticale, il tient dans le cadre et
      // chaque pièce a sa place à elle.
      chateau: [[4459, 2002, 530], [4459, 2099, 140]],
      salle: [[4820, 1900, 95], [4644, 2082, 60]],
    },
    vous: [4644, 2082, 60],
  },
};
const LIEU3D_DEFAUT = "port-real";

// ===========================================================================
// MARCHER DANS LA VILLE — le graphe piéton, le bâti d'à côté, et la montre
//
// On joue une balade : le joueur pose un but sur la carte, et la troupe y va
// à pied, rue par rue, pendant que la montre tourne. Trois choses vivent ici
// et nulle part ailleurs, parce qu'elles ont toutes besoin des mêmes 7 Mo de
// ville qu'on ne va pas envoyer au navigateur :
//
//   1. LE CHEMIN — Dijkstra sur les 18 314 arêtes de `<x>.rues.json`. Le coût
//      est en MINUTES, pas en mètres : un escalier de Visenya ne se monte pas
//      à la vitesse d'une artère, et c'est ce qui fait que le chemin le plus
//      court n'est pas toujours le plus rapide. La vitesse de la balade sort
//      donc du chemin lui-même, comme demandé — on ne la règle nulle part.
//   2. CE QU'ON PASSE — à chaque pas, les bâtiments à portée de regard, avec
//      leur métier et leur quartier. C'est la matière de la balade : sans ça,
//      le MJ reçoit des coordonnées et ne peut rien en dire.
//   3. LA MONTRE ET LA POSITION — marcher coûte des minutes, et il n'y a pas
//      de raison qu'elles soient gratuites parce qu'on marche sur une carte.
//
// LE GRAPHE N'EST PAS CONNEXE, et c'est un fait des données : 134 composantes,
// dont une de 13 792 nœuds et 133 miettes. On raccroche donc toujours au plus
// proche nœud DE LA GRANDE, sans quoi un but posé sur un îlot rend « pas de
// chemin » pour une ville entière qui en a un.
// ===========================================================================
// ===========================================================================
// DEBUG — LE MIROIR DU NARRATEUR.  ⚠ À RETIRER ⚠
//
// Mettre à `false` (ou supprimer les vingt lignes qui s'en servent, cherchez
// DEBUG_MARCHE_AU_FIL) rend le jeu à sa règle. Tant que c'est `true`, chaque
// pas de balade ou de combat est ÉCRIT DANS LE FIL DU JOUEUR en plus d'être
// envoyé au MJ — on voit passer, en direct, exactement ce que le narrateur
// reçoit.
//
// CE QUE ÇA VIOLE, ET IL FAUT LE SAVOIR : « la page ne dit jamais ce qu'on
// perçoit, le récit est au MJ ». Ici elle le dit, et elle dit même le brut —
// `croise`, que le joueur ne doit jamais voir en temps normal parce que c'est
// la matière que le MJ va mettre en scène. C'est un outil de mise au point,
// pas une fonctionnalité : on regarde la tuyauterie pendant qu'on la règle.
const DEBUG_MARCHE_AU_FIL = true;

const VITESSES = {          // mètres par minute, à pied, dans une ville
  artere: 78, rue: 72, ruelle: 62, quai: 68, abord: 62, escalier: 26,
};
const _rues = { cle: null, g: null };
// Le reste de minute d'une marche en cours, par siege. Voir `/marche`.
const _resteMarche = {};
// L'INSTANT DE DEMARRAGE DE CE SERVEUR. Il sert de signature aux tampons de
// balade (`etat/marches/`) : un tampon signe d'un autre demarrage est une
// promenade que plus personne ne finira — on la ferme au lieu de s'y ajouter.
// Voir `/marche`.
const SESSION_SERVEUR = Date.now();

function graphePieton(lieu) {
  const d = LIEUX3D[lieu] || LIEUX3D[LIEU3D_DEFAUT];
  const f = path.join(RACINE, "monde", d.prefixe + ".rues.json");
  const cle = d.prefixe + ":" + String(fs.statSync(f).mtimeMs);
  if (_rues.cle === cle) return _rues.g;
  const src = JSON.parse(fs.readFileSync(f, "utf-8"));
  // On numérote : un Dijkstra sur des chaînes de caractères passe son temps
  // dans la table de hachage, et la ville en a quinze mille.
  const num = new Map();
  const xs = [], ys = [], adj = [];
  const idx = (nom) => {
    let i = num.get(nom);
    if (i === undefined) {
      const p = src.noeuds[nom];
      if (!p) return -1;
      i = xs.length;
      num.set(nom, i);
      xs.push(p[0]);
      ys.push(p[1]);
      adj.push([]);
    }
    return i;
  };
  for (const a of src.aretes || []) {
    const i = idx(a.de), j = idx(a.vers);
    if (i < 0 || j < 0) continue;
    const v = VITESSES[a.g] || VITESSES.rue;
    const min = (a.m || Math.hypot(xs[i] - xs[j], ys[i] - ys[j])) / v;
    adj[i].push([j, min, a.g]);
    adj[j].push([i, min, a.g]);
  }
  // La grande composante, une fois pour toutes.
  const comp = new Int32Array(xs.length).fill(-1);
  let meilleur = -1, taille = 0;
  for (let n = 0, c = 0; n < xs.length; n++) {
    if (comp[n] >= 0) continue;
    const pile = [n];
    comp[n] = c;
    let t = 0;
    while (pile.length) {
      const x = pile.pop();
      t++;
      for (const [y] of adj[x]) if (comp[y] < 0) { comp[y] = c; pile.push(y); }
    }
    if (t > taille) { taille = t; meilleur = c; }
    c++;
  }
  const g = { xs, ys, adj, comp, grande: meilleur, noms: src.noeuds,
              reperes: src.reperes || {} };
  _rues.cle = cle;
  _rues.g = g;
  return g;
}

// Le nœud le plus proche d'un point, dans la grande composante seulement.
function noeudProche(g, x, y) {
  let best = -1, bd = Infinity;
  for (let i = 0; i < g.xs.length; i++) {
    if (g.comp[i] !== g.grande) continue;
    const d = (g.xs[i] - x) ** 2 + (g.ys[i] - y) ** 2;
    if (d < bd) { bd = d; best = i; }
  }
  return best;
}

// Dijkstra, tas binaire. Quinze mille nœuds : quelques millisecondes.
function cheminPieton(g, a, b) {
  const n = g.xs.length;
  const dist = new Float64Array(n).fill(Infinity);
  const prec = new Int32Array(n).fill(-1);
  const tas = [[0, a]];
  dist[a] = 0;
  const monter = (i) => {
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (tas[p][0] <= tas[i][0]) break;
      [tas[p], tas[i]] = [tas[i], tas[p]];
      i = p;
    }
  };
  const descendre = () => {
    const fin = tas.pop();
    if (!tas.length) return;
    tas[0] = fin;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < tas.length && tas[l][0] < tas[m][0]) m = l;
      if (r < tas.length && tas[r][0] < tas[m][0]) m = r;
      if (m === i) break;
      [tas[m], tas[i]] = [tas[i], tas[m]];
      i = m;
    }
  };
  while (tas.length) {
    const [d, x] = tas[0];
    descendre();
    if (x === b) break;
    if (d > dist[x]) continue;
    for (const [y, w] of g.adj[x]) {
      const nd = d + w;
      if (nd < dist[y] - 1e-9) {
        dist[y] = nd;
        prec[y] = x;
        tas.push([nd, y]);
        monter(tas.length - 1);
      }
    }
  }
  if (!isFinite(dist[b])) return null;
  const route = [];
  for (let x = b; x >= 0; x = prec[x]) route.push(x);
  route.reverse();
  return { route, minutes: dist[b] };
}

// ---- le bâti d'à côté ------------------------------------------------------
// 48 377 bâtiments : on n'en garde que ce qu'on regarde en passant — où, quel
// métier, quel quartier, quelle taille — dans des tableaux compacts, avec une
// grille de 60 m pour n'en fouiller qu'une poignée par pas. Le JSON d'origine
// (5 Mo) est relâché aussitôt lu.
const _bati = { cle: null, i: null };

function batiIndex(lieu) {
  const d = LIEUX3D[lieu] || LIEUX3D[LIEU3D_DEFAUT];
  const f = path.join(RACINE, "monde", d.prefixe + ".bati.json");
  const cle = d.prefixe + ":" + String(fs.statSync(f).mtimeMs);
  if (_bati.cle === cle) return _bati.i;
  const src = JSON.parse(fs.readFileSync(f, "utf-8"));
  const c = src._colonnes;
  const C = (nom) => c.indexOf(nom);
  const [ix, iy, ifa, ipr, iet] =
    [C("x"), C("y"), C("facade_m"), C("profondeur_m"), C("etages")];
  const [iu, iq, icat] = [C("usage"), C("quartier"), C("cat")];
  // LA PORTE ET L'EMPRISE, qu'on ne chargeait pas. Chaque bâtiment de la ville
  // cuite porte une porte (`porte_x`, `porte_y`) qui tombe SUR la voirie — à
  // zéro mètre du graphe piéton, mesuré. C'est ce qui permet d'aller « chez le
  // tanneur » au lieu d'aller au pixel qu'on a touché : voir `butProche`.
  const [ipx, ipy] = [C("porte_x"), C("porte_y")];
  const n = src.bati.length;
  const xs = new Float32Array(n), ys = new Float32Array(n);
  const px = new Float32Array(n), py = new Float32Array(n);
  // Le rayon d'encombrement : la demi-diagonale de l'emprise. Il sert à savoir
  // si un clic est POSÉ SUR la maison ou à côté d'elle, ce qu'un simple « la
  // plus proche » ne dit pas — une halle de trente mètres et une masure de six
  // ne se ratent pas de la même façon.
  const ray = new Float32Array(n);
  const aire = new Float32Array(n), et = new Uint8Array(n);
  const usages = [], quartiers = [], cats = [];
  const iu8 = new Uint8Array(n), iq8 = new Uint8Array(n), ic8 = new Uint8Array(n);
  const tab = (liste, v) => {
    let k = liste.indexOf(v);
    if (k < 0) { liste.push(v); k = liste.length - 1; }
    return k;
  };
  const PAS = 60;
  const grille = new Map();
  for (let k = 0; k < n; k++) {
    const r = src.bati[k];
    xs[k] = r[ix]; ys[k] = r[iy];
    // Sans porte écrite, on retombe sur le centre : c'est faux de quelques
    // mètres et ça ne casse rien, alors qu'un NaN casserait le Dijkstra.
    px[k] = isFinite(r[ipx]) ? r[ipx] : r[ix];
    py[k] = isFinite(r[ipy]) ? r[ipy] : r[iy];
    ray[k] = Math.hypot(r[ifa] || 8, r[ipr] || 8) / 2;
    aire[k] = (r[ifa] || 0) * (r[ipr] || 0);
    et[k] = Math.min(255, r[iet] || 1);
    iu8[k] = tab(usages, r[iu] || "");
    iq8[k] = tab(quartiers, r[iq] || "");
    ic8[k] = tab(cats, r[icat] || "");
    const g = ((xs[k] / PAS) | 0) + "," + ((ys[k] / PAS) | 0);
    let l = grille.get(g);
    if (!l) grille.set(g, l = []);
    l.push(k);
  }
  const i = { xs, ys, px, py, ray, aire, et, iu8, iq8, ic8,
              usages, quartiers, cats, grille, PAS };
  _bati.cle = cle;
  _bati.i = i;
  return i;
}

// ---------------------------------------------------------------------------
// OÙ L'ON VA QUAND ON A CLIQUÉ LÀ.
//
// UN CLIC N'EST PAS UN POINT, C'EST UNE INTENTION. On envoyait au chemin les
// mètres exacts du pixel touché, et l'itinéraire finissait par un segment droit
// de la dernière rue jusqu'à ce pixel — à travers les murs s'il le fallait.
// Pire : ce qu'on annonçait au joueur était le plus proche des VINGT-CINQ
// repères de la ville, c'est-à-dire, la plupart du temps, un nom à trois cents
// mètres de l'endroit visé. On cliquait la taverne et la barre disait « La
// porte de Fer ».
//
// Or la ville cuite sait exactement où l'on entre : chaque bâtiment porte sa
// porte, et ces portes tombent SUR le graphe piéton (médiane mesurée : zéro
// mètre). Un clic posé sur une maison devient donc « la porte de cette
// maison-là », ce qui est à la fois précis, atteignable, et la seule chose
// qu'un homme puisse vouloir dire en montrant une maison du doigt.
//
// ON NE SNAPPE QUE SI L'ON EST DESSUS. Accrocher au plus proche dans un rayon
// fixe rendrait impossible d'aller sur une place ou un quai : tout point de la
// ville a une maison à vingt mètres. Le test est donc l'EMPRISE — on est sur le
// bâtiment, à une marge près — ce qui recouvre exactement ce que le survol
// montre déjà sous le curseur. Ce qu'on voit est où l'on va.
const MARGE_CLIC = 6;      // mètres de pardon : le doigt tremble, le zoom ment

function butProche(lieu, x, y) {
  const b = batiIndex(lieu);
  const R = 40;                       // au-delà, aucune emprise ne peut mordre
  const cx = (x / b.PAS) | 0, cy = (y / b.PAS) | 0;
  const port = Math.ceil(R / b.PAS);
  let best = -1, marge = Infinity;
  for (let i = cx - port; i <= cx + port; i++) {
    for (let j = cy - port; j <= cy + port; j++) {
      const l = b.grille.get(i + "," + j);
      if (!l) continue;
      for (const k of l) {
        const d = Math.hypot(b.xs[k] - x, b.ys[k] - y);
        // De combien on déborde de l'emprise : négatif = on est dessus. Entre
        // deux maisons qui se touchent, celle dont on déborde le moins.
        const m = d - b.ray[k];
        if (m < marge && m <= MARGE_CLIC) { marge = m; best = k; }
      }
    }
  }
  if (best < 0) return null;
  return {
    bat: best, x: b.px[best], y: b.py[best],
    usage: b.usages[b.iu8[best]], cat: b.cats[b.ic8[best]],
    quartier: b.quartiers[b.iq8[best]],
    aire: Math.round(b.aire[best]), etages: b.et[best],
  };
}

// Ce qu'on a sous les yeux à un pas donné. On rend les plus PROCHES, et l'on
// garde à part le plus gros du lot : dans une rue de masures, la halle qu'on
// longe est ce qu'on décrirait en premier, même si trois portes sont plus près.
// COMMENT ON DÉSIGNE UN BÂTIMENT. Il n'a pas de nom — la ville a été semée,
// pas peuplée d'enseignes —, mais il a une IDENTITÉ : son rang dans
// `bati.json`. C'est déjà la monnaie du jeu (`affecter.py --bati 36391`, et
// c'est par elle que le Grenier est devenu le bâtiment 36391 dans
// `corps.json`). On la fait donc circuler jusqu'au MJ : chaque bâtiment
// rapporté porte son `bat`, et le MJ peut le baptiser d'une ligne —
//
//     python scripts/affecter.py --affecter lieu:la-taverne-du-guet 12345 \
//            --nom "La Taverne du Guet" --vraiment
//
// — après quoi CETTE MÊME BALADE le nommera, pour toujours et pour les deux
// sièges. C'est la boucle entière : la ville engendrée fournit la matière, le
// jeu y accroche des noms, et ce qui a été nommé une fois revient nommé.
//
// LA LIMITE, ET IL FAUT LA CONNAÎTRE : le rang n'est stable que tant que
// `bati.json` n'est pas réengendré. S'il l'était, tous les rangs glisseraient
// — mais `affecter.py` écrit aussi les mètres (`xyz`), de sorte qu'un
// réamorçage se rattraperait par la position et non par le numéro.
function batiAutour(lieu, x, y, rayon, combien, nommes) {
  const b = batiIndex(lieu);
  const cx = (x / b.PAS) | 0, cy = (y / b.PAS) | 0;
  const port = Math.ceil(rayon / b.PAS);
  const vus = [];
  for (let i = cx - port; i <= cx + port; i++) {
    for (let j = cy - port; j <= cy + port; j++) {
      const l = b.grille.get(i + "," + j);
      if (!l) continue;
      for (const k of l) {
        const d = Math.hypot(b.xs[k] - x, b.ys[k] - y);
        if (d <= rayon) vus.push([d, k]);
      }
    }
  }
  vus.sort((p, q) => p[0] - q[0]);
  const su = nommes || new Map();
  const dit = (k, d) => {
    const n = su.get(k);
    return {
      bat: k, nom: (n && n.nom) || null, cle: (n && n.cle) || null,
      usage: b.usages[b.iu8[k]], cat: b.cats[b.ic8[k]],
      quartier: b.quartiers[b.iq8[k]],
      aire: Math.round(b.aire[k]), etages: b.et[k], a: Math.round(d),
    };
  };
  // UN MÉTIER PAR LIGNE, ET LE BANAL COMPTÉ À PART. Les quatre bâtiments les
  // plus proches sont, statistiquement, quatre maisons : les deux tiers de la
  // ville en sont, et un dixième de plus est du taudis. Rendre les quatre
  // premiers, c'est donc envoyer au MJ « une maison, une maison, une maison,
  // une maison » à chaque pas — vrai, et sans rien à en dire.
  //
  // Ce qui se raconte, c'est ce qui DÉPASSE : la forge, le puits, la taverne
  // du coin. On garde donc le plus proche de chaque métier distinct, les
  // remarquables d'abord, et l'on RÉSUME le tissu ordinaire d'un chiffre
  // (« et douze maisons ») — ce qui dit la densité sans occuper la place.
  //
  // CE QUI EST NOMMÉ PASSE AVANT TOUT. Un bâtiment que la partie a baptisé
  // n'est plus du tissu : c'est la boutique de la Veuve, et l'on ne longe pas
  // la boutique de la Veuve sans que ça compte. Il entre dans la liste quel
  // que soit son métier et quels que soient ses voisins.
  const ORDINAIRE = new Set(["maison", "taudis", "cabane"]);
  const parMetier = new Map();
  const banal = new Map();
  const connus = [];
  for (const [d, k] of vus) if (su.has(k)) connus.push(dit(k, d));
  for (const [d, k] of vus) {
    if (su.has(k)) continue;               // déjà pris, et pris nommément
    const u = b.usages[b.iu8[k]];
    if (ORDINAIRE.has(u)) {
      banal.set(u, (banal.get(u) || 0) + 1);
      if (!parMetier.has(u)) parMetier.set(u, dit(k, d));
      continue;
    }
    if (!parMetier.has(u)) parMetier.set(u, dit(k, d));
  }
  const notables = [...parMetier.entries()]
    .filter(([u]) => !ORDINAIRE.has(u)).map(([, v]) => v)
    .sort((p, q) => p.a - q.a).slice(0, combien || 4);
  // s'il n'y a VRAIMENT que du tissu ordinaire, on le dit plutôt que rien
  const reste = notables.length ? notables
    : [...parMetier.values()].sort((p, q) => p.a - q.a).slice(0, 2);
  const proches = connus.concat(reste);
  let gros = null;
  for (const [d, k] of vus) if (!gros || b.aire[k] > gros.aire) gros = dit(k, d);
  return { proches, connus, gros, combien: vus.length,
           tissu: [...banal.entries()].map(([u, n]) => [u, n]) };
}

// Les métiers, en français, avec leur article. Les données parlent en slugs
// (`echoppe`, `maison-officier`, `fosse-vidange`) : c'est bon pour un index,
// c'est illisible dans un bandeau que le joueur a sous les yeux. Ce qui manque
// à la table retombe sur le slug tel quel — mieux vaut un mot brut qu'un trou.
const METIERS = {
  maison: "une maison", taudis: "un taudis", echoppe: "une échoppe",
  cabane: "une cabane", manse: "une belle demeure", taverne: "une taverne",
  boulangerie: "une boulangerie", "maison-officier": "un logis d'officier",
  forge: "une forge", puits: "un puits", entrepot: "un entrepôt",
  brasserie: "une brasserie", bordel: "un bordel", ecurie: "une écurie",
  tannerie: "une tannerie", auberge: "une auberge",
  "chantier-bois": "un chantier de bois", teinturerie: "une teinturerie",
  "septuaire-quartier": "un septuaire de quartier", etuve: "une étuve",
  poterie: "une poterie", abattoir: "un abattoir", moulin: "un moulin",
  "fosse-vidange": "une fosse à vidange", "marche-quartier": "un marché",
  "corps-de-garde": "un corps de garde", change: "une table de change",
  corderie: "une corderie", grenier: "un grenier à grain",
  voilerie: "une voilerie", caserne: "une caserne", geole: "une geôle",
  "donjon-rouge": "le Donjon Rouge", "fosse-dragons": "la Fosse aux Dragons",
  "vieux-septuaire": "le vieux septuaire", "bureau-port": "le bureau du port",
  "guilde-alchimistes": "la Guilde des Alchimistes",
};
const metier = (u) => METIERS[u] || u || "une maison";
// Le tissu se compte, donc il se met au pluriel. Trois mots suffisent : c'est
// tout ce qui, dans cette ville, se rencontre par paquets.
const PLURIELS = { maison: "maisons", taudis: "taudis", cabane: "cabanes" };

// --- QUI ON CROISE ----------------------------------------------------------
// Le compte et les métiers des gens rencontrés à un pas de balade, mis en une
// ligne lisible. Le calcul est fait par la page (voir `foule2d.presents`) :
// elle a les corps sous la main, le serveur ne les a pas, et les lui porter
// coûterait `journee.js`, la voirie et quatre méga-octets de cellules pour
// redire ce qui est déjà su.
//
// ON NE REND QUE CE QUI SE RENCONTRE. `dehors` est du monde qu'on croise ;
// `dedans` est un chiffre d'ambiance — il dit qu'un quartier est habité, pas
// qu'il y a foule. Le MJ ne doit jamais confondre les deux, sans quoi
// Culpucier endormi devient une cohue.
//
// QUELQUES RÔLES SEULEMENT. Il y en a quatre-vingt-huit et l'on n'en dit
// jamais plus de quatre : au-delà, ce n'est plus une rue qu'on décrit, c'est
// un recensement, et l'on retombe dans le mur de texte que le tunnel interdit.
const ROLES_DITS = 4;

function direGens(g) {
  if (!g || typeof g !== "object") return null;
  // Le rôle vient du binaire en kebab-case (`chef-de-feu`) : on lui rend ses
  // espaces et on s'arrête là. PAS DE PLURIEL AUTOMATIQUE — « chef de feu » se
  // pluralise sur la tête et non sur la queue, et une règle naïve écrirait
  // « chef de feus ». Le chiffre est devant, il suffit ; c'est le MJ qui met
  // la phrase en français, et c'est son métier.
  const dire = (m) => String(m).replace(/-/g, " ");
  const liste = Array.isArray(g.metiers) ? g.metiers : [];
  const tete = liste.slice(0, ROLES_DITS)
    .map(([m, n]) => (n > 1 ? n + " " + dire(m) : dire(m)));
  const reste = liste.slice(ROLES_DITS).reduce((s, p) => s + p[1], 0);
  if (reste) tete.push("et " + reste + " autre" + (reste > 1 ? "s" : ""));
  const portes = (Array.isArray(g.portes) ? g.portes : [])
    .slice(0, ROLES_DITS).map(([s, n]) => n + " " + s);
  return {
    rayon: g.rayon || null,
    // CE QU'ON CROISE — le seul chiffre qui compte pour un marcheur.
    croises: g.croises | 0,
    en_rue: g.rue | 0,
    attroupes: g.place | 0,
    // « 3 portefaix, 2 guet, 1 servante » — ou rien du tout, et le rien est
    // une information : une rue vide à trois heures du matin est exactement
    // ce qu'on était venu vérifier.
    metiers: tete.join(", ") || null,
    // CE QU'ON PEUT ALLER CHERCHER, et par quelle porte. « 12 à la taverne »
    // se joue ; « 12 portefaix » ne dit pas où frapper.
    sous_toit: g.toit | 0,
    portes: portes.join(", ") || null,
    // CEUX QUI SONT EN ARMES. Ligne à part, et en TÊTE de ce qu'on rapporte :
    // deux cents hommes rangés devant une porte ne sont pas un détail de la
    // rue, c'est la rue. Ils manquaient entièrement — le marcheur passait à
    // vingt pas d'eux et rapportait le compte des gens qui dormaient.
    //
    // Par camp et par état, parce que c'est tout ce qu'on voit d'un coup d'œil
    // et que ça décide de ce qu'on fait : « 180 garde/tient » est un mur, « 40
    // garde/deroute » est une porte perdue, et l'on ne s'approche pas des deux
    // de la même façon.
    en_armes: g.en_armes | 0,
    armes: (Array.isArray(g.armes) ? g.armes : []).slice(0, 6)
      .map(([c, n]) => n + " " + String(c).replace("/", " ")).join(" · ") || null,
    // CE QU'ILS FONT — la seule ligne qui porte une ACTION et non un état, et
    // celle dont un récit peut partir. « fuient : 6 portefaix, 2 servantes »
    // se joue ; « 8 personnes en rue » ne se joue pas, et c'était pourtant
    // tout ce qui remontait quand la ville se vidait sous les armes.
    //
    // QUATRE VERBES AU PLUS, comme les rôles : au-delà on ne décrit plus une
    // rue, on en fait l'inventaire — et l'inventaire est très exactement le
    // mur de texte que le tunnel interdit.
    font: (Array.isArray(g.font) ? g.font : []).slice(0, ROLES_DITS)
      .map(([v, par, n]) => n + " " + v + " (" +
        par.slice(0, 3).map(([m, k]) => k + " " + String(m).replace(/-/g, " "))
           .join(", ") + ")")
      .join(" · ") || null,
    detail_font: Array.isArray(g.font) ? g.font : [],
    // L'AMBIANCE, et rien de plus. Ne jamais lire ce chiffre comme une foule :
    // c'est le nombre de gens qui dorment derrière les murs qu'on longe.
    chez_eux: g.chez | 0,
    detail: liste,
    detail_toit: Array.isArray(g.metiers_toit) ? g.metiers_toit : [],
  };
}

// Le repère le plus proche, pour que la position se DISE : « à deux cents pas
// de la porte de la Gadoue » vaut mieux que « en 3340, 601 ».
// UN REPÈRE EST CE QU'ON NOMME EN LEVANT LA TÊTE : une porte, un marché, un
// quai, une colline. La table en contient aussi la structure du semis — des
// « halls », des « arcades », des « seuils » — qui ne sont des repères pour
// personne : « à 190 pas de Arcade de Le marché aux poissons » ne situe rien
// et se lit mal. On les écarte ici plutôt que de les corriger à l'affichage.
const REPERES_VRAIS = new Set([
  // Port-Réal — sept portes, trois collines, et ce qu'on voit de loin.
  "porte", "quai-amont", "quai-aval", "donjon",
  "fosse", "septuaire", "guilde", "casernes", "grand-marche", "marche-chevaux",
  "marche-poissons", "bureau-port", "aire-bris", "sommet-visenya",
  "sommet-aegon", "sommet-rhaenys",
  // Peyredragon — les treize. La liste est courte parce que l'île l'est : sur
  // trois cents mètres de château, la forge et les cuisines SONT ce qu'on
  // nomme en levant la tête, là où à Port-Réal ce ne serait qu'une maison de
  // plus. Aucun « seuil » ni « cour » ici : les treize nœuds nommés du graphe
  // sont treize repères, et c'est pour ça qu'on peut tous les prendre.
  "roukerie", "hotes", "garnison", "corps-de-garde", "ecuries", "forge",
  "cuisines", "grande-salle", "retrait", "tambour", "quai", "dragonmont",
]);

function repereProche(lieu, x, y) {
  const g = graphePieton(lieu);
  let best = null;
  for (const nom in g.reperes) {
    const cle = g.reperes[nom];
    if (!REPERES_VRAIS.has(String(cle).split(":")[0])) continue;
    const p = g.noms[cle];
    if (!p) continue;
    const d = Math.hypot(p[0] - x, p[1] - y);
    if (!best || d < best.a) best = { nom, a: Math.round(d) };
  }
  return best;
}

const _monde = { cle: null, couches: null, lieu: null };
function grapheTaille(lieu) {
  const d = LIEUX3D[lieu] || LIEUX3D[LIEU3D_DEFAUT];
  const f = path.join(RACINE, "monde", d.prefixe + ".graph.json");
  const cle = d.prefixe + ":" + String(fs.statSync(f).mtimeMs);
  if (_monde.cle === cle) return _monde.couches;
  const g = JSON.parse(fs.readFileSync(f, "utf-8"));
  const couches = {};
  for (const a of g.aretes || []) {
    (couches[a.couche] = couches[a.couche] || []).push(
      { genre: a.genre, largeur_m: a.largeur_m, trace: a.trace, nom: a.nom || undefined });
  }
  // Les repères, ce sont les choses qu'on nomme en regardant la ville : les
  // portes, les collines, les monuments. La densification en a semé onze mille
  // autres (cours, seuils, halls) qui sont de la structure, pas des repères —
  // les envoyer, c'est onze mille étiquettes sur l'écran.
  const REPERE = new Set(["porte", "forteresse", "monument", "septuaire", "guilde",
    "caserne", "marche", "quai", "office", "chantier", "sommet"]);
  couches._reperes = (g.noeuds || [])
    .filter((n) => n.nom && n.niveau === 0 && REPERE.has(n.genre))
    .map((n) => ({ id: n.id, nom: n.nom, genre: n.genre, xyz: n.xyz }));
  _monde.cle = cle; _monde.couches = couches;
  return couches;
}

// ---- les repères DÉCIDÉS en jeu ------------------------------------------
// Le graphe donne les noms que la ville porte d'elle-même : les portes, les
// collines, les monuments. Ceux-là sont vrais pour tout le monde et ne changent
// pas d'une partie à l'autre. Les affectations (`scripts/affecter.py`) donnent
// les noms que LA PARTIE a posés dessus — la taverne de Mag, le chantier du
// bout, la cabane où dort le joueur.
//
// Et elles ne se montrent QUE si on l'a demandé. C'est du brouillard, pas de
// l'affichage : affecter un endroit, c'est lui donner des mètres pour calculer ;
// le montrer, c'est dire que le joueur sait où il est. Les deux gestes sont
// séparés parce que les deux dates le sont — on affecte le chantier du bout le
// jour où l'on veut mesurer sa distance, on le montre le jour où le joueur y va.
//
// `visible: true` = tout le monde ; `visible: ["marlo-vasse"]` = ces sièges-là.
// Ce que Marlo a reconnu de ses yeux, la reine ne l'a pas vu.
//
// On relit le fichier à chaque requête, sans cache : il change PENDANT qu'on
// joue et tient sur quelques lignes. Les mètres sont recopiés dans
// l'affectation par le script, donc on n'ouvre jamais les cinq mégaoctets du
// bâti pour poser une étiquette.
const AFFECTE_VISIBLE = new Set(["lieu", "salle"]);

function reperesAffectes(lieu, siege) {
  if (lieu !== LIEU3D_DEFAUT) return [];
  let A;
  try {
    A = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "corps.json"),
                                   "utf8")).affectations || {};
  } catch (e) { return []; }
  const out = [];
  for (const clef of Object.keys(A)) {
    const v = A[clef];
    const genre = clef.split(":")[0];
    // Ce qui est DEDANS n'a pas de nom sur la ville : un livre et un homme
    // n'ont que le toit qui les abrite, sans quoi trois étiquettes se
    // superposent au même mètre carré.
    if (!AFFECTE_VISIBLE.has(genre)) continue;
    if (!v || !Array.isArray(v.xyz) || v.xyz.length < 3) continue;
    const vu = v.visible;
    if (!(vu === true || (Array.isArray(vu) && siege && vu.includes(siege)))) continue;
    out.push({ id: clef, nom: v.nom || clef.split(":")[1], genre: "affecte",
               xyz: v.xyz });
  }
  return out;
}

// ---- la péremption : le modèle a-t-il bougé depuis la dernière génération ?
// Un `statSync` par fichier de source, une fois toutes les cinq secondes. Le
// cache est volontairement court : les sources changent PENDANT qu'on joue, et
// un drapeau qui met une minute à s'allumer ne prévient plus de rien.
const PEREMPTION_TTL = 5000;
const _peremption = { quand: 0, par: {} };

// Une source est soit un fichier, soit un dossier dont on prend les `.py`. On
// ne descend pas dans les sous-dossiers : `__pycache__` n'est pas une source,
// et il rebouge à chaque import.
function sourcesPy(relatif) {
  const abs = path.join(RACINE, relatif);
  try {
    if (!fs.statSync(abs).isDirectory()) return [abs];
    return fs.readdirSync(abs).filter((n) => n.endsWith(".py"))
      .map((n) => path.join(abs, n));
  } catch (e) { return []; }
}

// Rend `null` pour un lieu qui ne déclare pas ses sources (on ne sait rien, on
// n'affirme rien), sinon l'état de fraîcheur avec la liste de ce qui est plus
// récent que la dernière génération.
function peremption(lieu) {
  const d = LIEUX3D[lieu];
  if (!d || !d.sources || !d.sources.length || !d.temoin) return null;
  const t = Date.now();
  if (t - _peremption.quand > PEREMPTION_TTL) { _peremption.quand = t; _peremption.par = {}; }
  if (_peremption.par[lieu] !== undefined) return _peremption.par[lieu];
  let r = null;
  try {
    // Témoin absent = jamais engendré : périmé, et c'est le cas le plus franc.
    let engendre = 0;
    try { engendre = fs.statSync(path.join(RACINE, d.temoin)).mtimeMs; } catch (e) { engendre = 0; }
    const recentes = [];
    for (const s of d.sources) {
      for (const f of sourcesPy(s)) {
        let m;
        try { m = fs.statSync(f).mtimeMs; } catch (e) { continue; }
        if (m > engendre)
          recentes.push({
            fichier: path.relative(RACINE, f).split(path.sep).join("/"),
            modifie: Math.round(m),
          });
      }
    }
    recentes.sort((a, b) => b.modifie - a.modifie);
    r = {
      perime: !engendre || recentes.length > 0,
      temoin: d.temoin, engendre: engendre ? Math.round(engendre) : null,
      sources: recentes, regenerer: d.regenerer || null,
    };
  } catch (e) { r = null; }
  _peremption.par[lieu] = r;
  return r;
}

// Au démarrage, on le DIT. Un drapeau que seule une requête JSON porte ne se
// voit pas quand on relance le serveur pour tout autre chose.
function direLaPeremption() {
  for (const id of Object.keys(LIEUX3D)) {
    const p = peremption(id);
    if (!p || !p.perime) continue;
    const n = p.sources.length;
    console.warn("Le monde 3D de " + LIEUX3D[id].nom + " est PÉRIMÉ : "
      + (p.engendre
        ? n + " source" + (n > 1 ? "s" : "") + " plus récente" + (n > 1 ? "s" : "")
          + " que " + p.temoin + " (" + p.sources.slice(0, 4).map((s) => s.fichier).join(", ")
          + (n > 4 ? ", …" : "") + ")"
        : p.temoin + " n'existe pas")
      + (p.regenerer ? " — relancez : " + p.regenerer : ""));
  }
}

function serviceMonde(req, res, chemin) {
  // `/monde/<quoi>` reste Port-Réal — tout ce qui existait continue de marcher.
  // `/monde/<lieu>/<quoi>` sert un autre lieu, et c'est ce que le client passe
  // en `source` à `ouvrir()`.
  let lieu = LIEU3D_DEFAUT, quoi = chemin;
  const barre = chemin.indexOf("/");
  if (barre > 0 && LIEUX3D[chemin.slice(0, barre)]) {
    lieu = chemin.slice(0, barre);
    quoi = chemin.slice(barre + 1);
  }
  const d = LIEUX3D[lieu];
  const zlib = require("zlib");
  const gzip = /\bgzip\b/.test(req.headers["accept-encoding"] || "");
  const rendre = (corps) => {
    const buf = Buffer.isBuffer(corps) ? corps : Buffer.from(corps, "utf-8");
    if (!gzip) return envoyer(res, 200, buf, "application/json; charset=utf-8");
    return envoyer(res, 200, zlib.gzipSync(buf, { level: 6 }),
      "application/json; charset=utf-8", { "Content-Encoding": "gzip" });
  };
  try {
    // La liste des localisations, pour que la page en propose le choix sans
    // qu'on la recopie à deux endroits.
    if (quoi === "lieux")
      return rendre(JSON.stringify({
        defaut: LIEU3D_DEFAUT,
        lieux: Object.keys(LIEUX3D).map((id) => {
          // `perime` est le drapeau court, `peremption` le détail (le témoin,
          // sa date, les sources plus récentes, la commande qui répare). Un
          // lieu qui ne déclare pas ses sources rend `false` et `null` : on ne
          // sait pas, donc on n'accuse pas.
          const p = peremption(id);
          return {
            id, nom: LIEUX3D[id].nom, sous: LIEUX3D[id].sous,
            carte: !!LIEUX3D[id].carte, maillage: !!LIEUX3D[id].maillage,
            // Les intérieurs : un lieu en a parce que le FICHIER est là, pas
            // parce qu'il s'appelle Peyredragon — même règle que pour les corps.
            interieurs: fs.existsSync(path.join(RACINE, "monde",
              LIEUX3D[id].prefixe + ".interieurs.json")),
            vue: LIEUX3D[id].vue, vues: LIEUX3D[id].vues || null,
            contient: LIEUX3D[id].contient || null,
            vous: LIEUX3D[id].vous || null,
            source: id === LIEU3D_DEFAUT ? "/monde" : "/monde/" + id,
            perime: !!(p && p.perime), peremption: p,
          };
        }),
      }));
    if (quoi === "terrain")
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".terrain.json")));
    // Le plan 2D, cuit par `scripts/monde/plan_ville.py` : la même ville que le
    // relief, mais dessinée. Un lieu en a un parce que le FICHIER est là —
    // même règle que les corps et les intérieurs, et rien à déclarer ici.
    if (quoi === "plan2d") {
      const f = path.join(RACINE, "monde", d.prefixe + ".plan2d.json");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans plan 2D", lieu }));
      return rendre(fs.readFileSync(f));
    }
    // Le masque du bâti : un bit par mètre carré, cuit avec le plan 2D. Il ne
    // sert qu'à une chose, et elle vaut le transfert — que la foule ne marche
    // jamais dans un mur. Servi en binaire brut, sans mise en forme : c'est un
    // tableau de bits, pas un document.
    if (quoi === "masque") {
      const f = path.join(RACINE, "monde", d.prefixe + ".masque.bin");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans masque", lieu }));
      const buf = fs.readFileSync(f);
      res.writeHead(200, { "Content-Type": "application/octet-stream",
                           "Content-Length": buf.length });
      return res.end(buf);
    }
    // Un maillage : un corps bâti donné tel quel, pour ce qui se regarde de
    // près. Un lieu qui n'en a pas rend `null` — le client ne pose rien.
    if (quoi === "maillage") {
      if (!d.maillage) return rendre(JSON.stringify(null));
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".maillage.json")));
    }
    // Les intérieurs : une pièce creuse par salle, murs épais et portes percées
    // (scripts/monde/peyredragon_interieurs.py). Même format que le maillage,
    // plus une clef `salles` qui donne à chacune sa tranche d'index. Un lieu en
    // est pourvu parce que le fichier existe — pas parce qu'on l'a nommé ici :
    // c'est la règle posée pour les corps, et elle vaut ici aussi.
    if (quoi === "interieurs") {
      const f = path.join(RACINE, "monde", d.prefixe + ".interieurs.json");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans intérieurs", lieu }));
      return rendre(fs.readFileSync(f));
    }
    if (quoi === "bati")
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".bati.json")));
    if (quoi === "carte") {
      // Un lieu sans carte 2D à la bonne échelle rend une carte VIDE plutôt
      // qu'une erreur : `enceinte.js` la parcourt et n'y trouve rien à bâtir,
      // ce qui est exactement ce qu'on veut — ses murs sont dans le bâti.
      if (!d.carte) return rendre(JSON.stringify({ sol: [], corps: [], acteurs: [] }));
      return rendre(fs.readFileSync(path.join(RACINE, d.carte)));
    }
    if (quoi === "voirie") {
      const c = grapheTaille(lieu);
      const q = (req.url.split("?")[1] || "").match(/(?:^|&)couche=([^&]*)/);
      const nom = decodeURIComponent((q && q[1]) || "L1-surface");
      return rendre(JSON.stringify({ couche: nom, aretes: c[nom] || [] }));
    }
    if (quoi === "reperes") {
      const j = qui(req);          // le second argument de `qui` ne sert pas
      return rendre(JSON.stringify({
        reperes: grapheTaille(lieu)._reperes
          .concat(reperesAffectes(lieu, j ? j.personnage_id : null)),
      }));
    }
    // Les corps : le manifeste en JSON, puis une cellule à la fois en BRUT.
    // Le binaire ne passe pas par `rendre` — il est déjà dense, et le gzipper
    // coûte plus de temps processeur qu'il ne rend d'octets.
    if (quoi === "gens") {
      // Ce n'est plus le nom du lieu qui décide s'il est peuplé, c'est
      // l'existence de son manifeste : `peupler.py <lieu>` en écrit un, et le
      // lieu devient peuplé le jour où le fichier apparaît.
      const mf = path.join(RACINE, "monde", d.prefixe + ".gens.json");
      if (!fs.existsSync(mf))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans corps", lieu }));
      return rendre(fs.readFileSync(mf));
    }
    // Les besoins : ce qu'un rôle fait de sa journée, et l'adresse de chaque
    // bâtiment (son puits, sa boulangerie…). C'est de là que sort le mouvement
    // — mais rien n'y bouge : la position se calcule côté page.
    // Les corps DÉCIDÉS en jeu : ceux qu'on a créés pour les grands (le roi
    // n'emprunte le corps de personne) et les emprunts déjà posés. C'est le
    // seul morceau de `etat/` que le décor lit — et il le lit seulement, il
    // n'y écrit jamais.
    //
    // `corps.json` est UN fichier pour tous les mondes : chaque affectation dit
    // le sien (`monde`). Le refuser hors du lieu par défaut était le geste d'une
    // époque où il n'y avait qu'un monde — et il plantait la reine dans un
    // champ : à Peyredragon la page recevait un 404, tombait sur zéro adresse,
    // et repliait la balise sur le point générique du lieu, dehors, alors que
    // ses appartements ont un bâtiment depuis le début. On sert donc toujours,
    // et c'est la page qui écarte ce qui n'est pas de son monde.
    if (quoi === "corps") {
      try {
        return rendre(fs.readFileSync(path.join(RACINE, "etat", "corps.json")));
      } catch (e) {
        return rendre(JSON.stringify({ liens: {}, corps: [] }));
      }
    }
    if (quoi === "besoins") {
      // Comme pour les corps : c'est l'existence du fichier qui dit si un lieu
      // sait faire marcher son monde, pas son nom. `besoins.py <lieu>` en écrit
      // un, et la foule s'y met en mouvement le jour où il paraît.
      const bf = path.join(RACINE, "monde", d.prefixe + ".besoins.json");
      if (!fs.existsSync(bf))
        return envoyer(res, 404, JSON.stringify({ erreur: "lieu sans besoins", lieu }));
      return rendre(fs.readFileSync(bf));
    }
    if (quoi.startsWith("gens/")) {
      // Jamais un morceau de chemin venu du client sans filtre : la clé de
      // cellule est deux entiers signés séparés d'un tiret, suivis de `.bin`,
      // et rien d'autre. Une seule forme d'URL par ressource — tolérer le
      // suffixe absent, c'est se réveiller un jour avec deux caches.
      const m = /^gens\/(-?\d+--?\d+)\.bin$/.exec(quoi);
      if (!m) return envoyer(res, 404, JSON.stringify({ erreur: "cellule", quoi }));
      const clef = m[1];
      // Chaque lieu range ses cellules chez lui. Port-Réal reste à la racine de
      // `monde/gens/` — c'est là qu'elles ont toujours été servies, et l'on ne
      // déplace pas une donnée en vol pour l'élégance. Sans ce découpage,
      // `/monde/<autre>/gens/...` rendrait les corps de Port-Réal sous le nom
      // d'un autre lieu.
      const f = d.prefixe === "portreal"
        ? path.join(RACINE, "monde", "gens", clef + ".bin")
        : path.join(RACINE, "monde", "gens", d.prefixe, clef + ".bin");
      if (!fs.existsSync(f))
        return envoyer(res, 404, JSON.stringify({ erreur: "cellule absente", clef }));
      return envoyer(res, 200, fs.readFileSync(f), "application/octet-stream");
    }
  } catch (e) {
    return envoyer(res, 404, JSON.stringify({ erreur: quoi, detail: String(e.message || e) }));
  }
  return envoyer(res, 404, JSON.stringify({ erreur: quoi }));
}

// ---- la régie : ce que le MJ voit et que le joueur ne voit jamais ----------
// `/admin` n'est pas une échelle du décor : c'est l'envers. On y lit les têtes,
// les échéances et les mesures — c'est-à-dire tout ce que le brouillard cache.
// Aucune écriture, jamais : un seul écrivain reste la règle, et cette page ne
// l'est pas. Elle relit l'état à chaque requête, sans cache : à deux MJ, un
// cache d'une minute est un mensonge d'une minute.
function dateCourte(d) {
  if (!d) return "";
  if (typeof d === "string") return d;
  // `dernier_rapport` est tantôt une date nue, tantôt un rapport complet qui
  // porte la sienne. On ne veut pas d'un « undefined.undefined » à l'écran :
  // une régie qui affiche du bruit ne se relit plus.
  if (d.date) return dateCourte(d.date);
  if (d.annee == null) return "";
  return d.annee + "." + d.lune + "." + d.jour;
}

// ---- journal des activations --------------------------------------------
// La liste reste legere. Prompt, message, rapport et thread complet ne sont
// lus que lorsqu'un MJ ouvre une activation : le graphe n'en paie jamais le
// poids au chargement ni pendant son animation.
const DEPOT_ACTIVATIONS = path.join(RACINE, "etat", "activations");

// ---- LE PLAN ET LES TÊTES : est-ce que l'homme le porte VRAIMENT ? ----------
//
// Une action déclarée « en cours » dans un cahier est la PAROLE de l'homme :
// écrite de sa main, dans un registre que le joueur peut ouvrir, et c'est
// exactement ce qu'il dirait au conseil. C'est le vert déclaratif du plateau.
// Le vert VRAI serait autre chose : que l'action figure dans les ÉTAPES de sa
// tête (`etat/intentions.json`), avec une horloge — c'est-à-dire qu'elle est
// dans la boucle des acteurs et qu'elle avancera toute seule.
//
// AUJOURD'HUI, LA RÉPONSE EST ZÉRO PARTOUT. 584 actions au plan, 200 étapes
// dans les têtes, et pas une seule étape ne cite un numéro d'action : le plan
// du conseil et la boucle des acteurs sont deux mondes qui s'ignorent. Ce n'est
// pas une panne du détecteur, c'est le fait — et c'est pour le VOIR qu'on
// l'expose.
//
// UNE RÉSERVE DE DOCTRINE, ET LE DRAPEAU QUI LA LÈVE. `intentions.json` est la
// tête des PNJ : elle n'est JAMAIS montrée au joueur, c'est la règle cardinale
// du manuel. Ce que la route en tire ici — un booléen « ce numéro est-il cité
// dans ses étapes » — ne dit rien de ce qu'il pense ni de ce qu'il ignore, mais
// c'en est tout de même une lecture. Le joueur a tranché qu'on le fasse ;
// METTRE CETTE CONSTANTE À `false` l'éteint entièrement, sans autre chirurgie :
// la route cesse d'ouvrir le fichier et le champ `dans_la_tete` disparaît.
const LIRE_LES_TETES = true;

const _tetes = { cle: null, par: null, etapes: 0 };
// Les numéros cités dans les étapes de chaque tête, par personnage. On relit au
// changement de mtime seulement : le fichier fait 300 Ko et la route est
// appelée à chaque bascule de plateau.
function numerosDesTetes() {
  if (!LIRE_LES_TETES) return { par: {}, etapes: 0 };
  const f = path.join(RACINE, "etat", "intentions.json");
  let cle;
  try { cle = String(fs.statSync(f).mtimeMs); } catch (e) { return { par: {}, etapes: 0 }; }
  if (_tetes.cle === cle) return { par: _tetes.par, etapes: _tetes.etapes };
  const par = {};
  let etapes = 0;
  try {
    const brut = JSON.parse(fs.readFileSync(f, "utf-8"));
    (Array.isArray(brut) ? brut : []).forEach((a) => {
      if (!a || !a.personnage_id) return;
      const vus = par[a.personnage_id] || (par[a.personnage_id] = {});
      // Une étape vit dans `plan` (une liste) ou dans `etapes` selon les fiches.
      // On ne suppose aucun champ : on cherche le numéro N'IMPORTE OÙ dans
      // l'étape — `quoi`, `id`, un coût, un `si_bloque`. Un homme qui écrit
      // « 21030 » quelque part dans son étape la relie à l'action, et c'est le
      // seul geste qu'on lui demande.
      ["plan", "etapes"].forEach((k) => {
        if (!Array.isArray(a[k])) return;
        a[k].forEach((e) => {
          etapes++;
          (JSON.stringify(e).match(/(?:^|[^\d])(\d{4,6})(?![\d])/g) || [])
            .forEach((m) => { vus[m.replace(/\D/g, "")] = 1; });
        });
      });
    });
  } catch (e) { return { par: {}, etapes: 0 }; }
  _tetes.cle = cle; _tetes.par = par; _tetes.etapes = etapes;
  return { par: par, etapes: etapes };
}

// OÙ SE TIENT QUELQU'UN PAR RAPPORT AU JOUEUR — « quartier » ou « au loin ».
//
// Remplace le champ `echelle` d'intentions.json, supprimé. Le serveur NE
// CALCULE RIEN : il relit ce que `evaluer.py --json` a déposé, comme pour le
// reste du tissu. Dépôt absent ou périmé : on rend « quartier » pour tout le
// monde plutôt que de déclarer le château désert — mieux vaut afficher trop
// que faire croire que personne n'est là.
function ouQuartier(id) {
  try {
    const pt = path.join(RACINE, "etat", "tissu", "evaluation.json");
    const ev = JSON.parse(fs.readFileSync(pt, "utf-8"));
    const gens = ((ev || {}).quartier || {}).gens;
    if (!Array.isArray(gens) || !gens.length) return "quartier";
    return gens.includes(id) ? "quartier" : "au loin";
  } catch (e) { return "quartier"; }
}

function lireJsonSansFaillir(fichier, defaut) {
  try { return JSON.parse(fs.readFileSync(fichier, "utf-8")); }
  catch (_e) { return defaut; }
}

function rapportsEtJournalActivations() {
  const etat = lireJsonSansFaillir(path.join(DEPOT_ACTIVATIONS, "boucle.json"),
    { historique: [], acteurs: {} });
  const parSession = new Map();
  let courant = null, attente = [];
  try {
    const lignes = fs.readFileSync(path.join(DEPOT_ACTIVATIONS, "boucle.log.jsonl"), "utf-8")
      .split(/\r?\n/).filter(Boolean);
    lignes.forEach((ligne) => {
      let ev;
      try { ev = JSON.parse(ligne); } catch (_e) { return; }
      if (ev.evenement === "cycle.depart") {
        courant = null; attente = [ev]; return;
      }
      if (ev.evenement === "cli.depart" && ev.session) {
        courant = ev.session;
        parSession.set(courant, (parSession.get(courant) || []).concat(attente, [ev]));
        attente = [];
        return;
      }
      if (courant) {
        parSession.get(courant).push(ev);
        if (ev.evenement === "cycle.termine") courant = null;
      } else {
        attente.push(ev);
      }
    });
  } catch (_e) { /* aucun run journalise */ }
  return { etat, parSession };
}

function rapportDepuisEntree(entree) {
  const relatif = String((entree && entree.rapport) || "").replace(/\//g, path.sep);
  const fichier = path.resolve(RACINE, relatif);
  if (!fichier.startsWith(path.resolve(DEPOT_ACTIVATIONS) + path.sep)) return null;
  return lireJsonSansFaillir(fichier, null);
}

function transcriptClaude(session) {
  if (!/^[a-zA-Z0-9-]+$/.test(String(session || ""))) return [];
  const projets = path.join(os.homedir(), ".claude", "projects");
  try {
    for (const dossier of fs.readdirSync(projets, { withFileTypes: true })) {
      if (!dossier.isDirectory()) continue;
      const fichier = path.join(projets, dossier.name, session + ".jsonl");
      if (!fs.existsSync(fichier)) continue;
      return fs.readFileSync(fichier, "utf-8").split(/\r?\n/).filter(Boolean)
        .map((ligne) => { try { return JSON.parse(ligne); } catch (_e) { return null; } })
        .filter(Boolean);
    }
  } catch (_e) { /* le journal local Claude peut ne pas exister */ }
  return [];
}

// Le MJ actif n'est pas une nouvelle piece d'etat : Claude ecrit deja son fil
// append-only sous `.claude/projects/<ce projet>/<session>.jsonl`. Plusieurs MJ
// peuvent etre ouverts (un par siege) ; celui qui a parle ou travaille le plus
// recemment est celui que la regie montre. Les narrateurs temporaires des
// activations ont un autre cwd et ne peuvent donc pas gagner cette election.
let cacheFilMjActif = { cle: null, valeur: null };

function texteBlocClaude(bloc) {
  if (typeof bloc === "string") return bloc;
  if (!bloc || typeof bloc !== "object") return "";
  if (typeof bloc.text === "string") return bloc.text;
  if (typeof bloc.content === "string") return bloc.content;
  if (Array.isArray(bloc.content)) return bloc.content.map(texteBlocClaude).filter(Boolean).join("\n");
  return "";
}

function bornerTexteClaude(texte, maximum) {
  texte = String(texte || "");
  return texte.length <= maximum ? texte : texte.slice(0, maximum) + "\n… [suite masquee]";
}

function apercuOutilClaude(bloc) {
  const entree = (bloc && bloc.input) || {};
  return entree.description || entree.command || entree.query || entree.path ||
    (Object.keys(entree).length ? JSON.stringify(entree) : "");
}

function lignesFinFichier(fichier, maximumOctets) {
  const taille = fs.statSync(fichier).size;
  const debut = Math.max(0, taille - maximumOctets);
  const longueur = taille - debut;
  const tampon = Buffer.alloc(longueur);
  const fd = fs.openSync(fichier, "r");
  try { fs.readSync(fd, tampon, 0, longueur, debut); }
  finally { fs.closeSync(fd); }
  let texte = tampon.toString("utf-8");
  if (debut > 0) texte = texte.slice(Math.max(0, texte.indexOf("\n") + 1));
  return texte.split(/\r?\n/).filter(Boolean);
}

function filMjActif() {
  const codeProjet = path.resolve(RACINE).replace(/[:\\/]/g, "-");
  const dossier = path.join(os.homedir(), ".claude", "projects", codeProjet);
  if (!fs.existsSync(dossier)) return { session: null, titre: null, items: [] };
  const candidats = fs.readdirSync(dossier, { withFileTypes: true })
    .filter((e) => e.isFile() && /^[a-zA-Z0-9-]+\.jsonl$/.test(e.name))
    .map((e) => {
      const fichier = path.join(dossier, e.name);
      return { fichier, nom: e.name, stat: fs.statSync(fichier) };
    }).sort((a, b) => b.stat.mtimeMs - a.stat.mtimeMs);
  if (!candidats.length) return { session: null, titre: null, items: [] };
  const choisi = candidats[0];
  const cle = choisi.fichier + ":" + choisi.stat.size + ":" + choisi.stat.mtimeMs;
  if (cacheFilMjActif.cle === cle) return cacheFilMjActif.valeur;

  const session = path.basename(choisi.nom, ".jsonl");
  let titre = null;
  try {
    const fd = fs.openSync(choisi.fichier, "r");
    const tampon = Buffer.alloc(Math.min(65536, choisi.stat.size));
    try { fs.readSync(fd, tampon, 0, tampon.length, 0); }
    finally { fs.closeSync(fd); }
    for (const ligne of tampon.toString("utf-8").split(/\r?\n/)) {
      try {
        const ev = JSON.parse(ligne);
        if (ev.type === "ai-title" && ev.aiTitle) { titre = ev.aiTitle; break; }
      } catch (_e) { /* premiere ligne partielle ou absente */ }
    }
  } catch (_e) { /* le fil reste lisible sans titre */ }

  const items = [];
  lignesFinFichier(choisi.fichier, 2 * 1024 * 1024).forEach((ligne) => {
    let ev;
    try { ev = JSON.parse(ligne); } catch (_e) { return; }
    const moment = ev.timestamp || null;
    if (ev.type === "user" && ev.message) {
      const contenu = ev.message.content;
      if (typeof contenu === "string") {
        const automatique = contenu.match(/^<(task-notification|system-reminder|local-command-[^>]+)>/);
        items.push(automatique
          ? { role: "outil", nom: automatique[1],
              texte: bornerTexteClaude(contenu, 2500), moment }
          : { role: "joueur", texte: bornerTexteClaude(contenu, 6000), moment });
      } else if (Array.isArray(contenu)) {
        contenu.filter((b) => b && b.type === "tool_result").forEach((b) => {
          const texte = texteBlocClaude(b).trim();
          if (texte) items.push({ role: "outil", nom: "resultat",
            texte: bornerTexteClaude(texte, 2500), moment });
        });
      }
      return;
    }
    if (ev.type !== "assistant" || !ev.message || !Array.isArray(ev.message.content)) return;
    ev.message.content.forEach((bloc) => {
      if (!bloc) return;
      if (bloc.type === "text" && bloc.text) {
        items.push({ role: "mj", texte: bornerTexteClaude(bloc.text, 6000), moment });
      } else if (bloc.type === "tool_use") {
        items.push({ role: "outil", nom: bloc.name || "outil",
          texte: bornerTexteClaude(apercuOutilClaude(bloc), 1500), moment });
      }
    });
  });
  const valeur = {
    session, titre: titre || ("MJ " + session.slice(0, 8)),
    modifie_le: choisi.stat.mtime.toISOString(),
    actif: Date.now() - choisi.stat.mtimeMs < 5 * 60 * 1000,
    tronque: choisi.stat.size > 2 * 1024 * 1024,
    items: items.slice(-60),
  };
  cacheFilMjActif = { cle, valeur };
  return valeur;
}

function prevoirActivations() {
  let previsions = { previsions: [], erreur: null };
  try {
    previsions = JSON.parse(childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "boucle_activation.py"), "--prevoir", "8"],
      { cwd: RACINE, encoding: "utf-8", timeout: 5000,
        windowsHide: true, maxBuffer: 2 * 1024 * 1024 }));
  } catch (e) {
    previsions = { previsions: [], erreur: String(e.message || e) };
  }
  return { previsions,
    en_cours: fs.existsSync(path.join(DEPOT_ACTIVATIONS, ".boucle.lock")) };
}

// LA CRITICITE DU PLAN, servie a cote des registres — jamais dedans.
//
// Une colonne « perte » posee dans `books.json` serait effacee au prochain
// `couverture.py`, qui regenere les registres a quatre colonnes exprement pour
// qu'ils ne portent rien de volatil. Or il n'y a pas plus volatil qu'un score :
// il bouge a chaque action cochee. On le CALCULE donc a la demande et l'ecran
// l'ajoute par-dessus le volume, par numero. Les livres restent ce qu'ils sont.
//
// LE CACHE SE CLE SUR LA TAILLE ET LA DATE DE `books.json`, parce que le calcul
// coute une seconde et demie et que la page le redemande a chaque ouverture de
// volume. Une seconde et demie une fois par ecriture du plan, c'est gratuit ;
// une fois par clic, c'est une page qui rame.
const cacheCriticite = new Map();
const cachePlanModele = new Map();

// LE PÉRIMÈTRE DU PLAN VIENT DE PYTHON. L'échiquier garde son rendu détaillé
// en JavaScript, mais il ne redéfinit plus ce qu'est une affaire ni ce que ce
// siège peut voir : `plan_modele.py` est la porte commune aux rapports, au
// bilan, à la criticité et à l'écran.
function planModele(vueDe) {
  const siege = vueDe || "__defaut__";
  const entrees = bibliotheque.cheminsSource(RACINE).concat([
                   path.join(RACINE, "etat", "boites.json"),
                   path.join(RACINE, "etat", "personnages.json"),
                   path.join(RACINE, "etat", "journal.json"),
                   path.join(RACINE, "etat", "actes.json"),
                   path.join(RACINE, "etat", "evenements.json"),
                   path.join(RACINE, "scripts", "bibliotheque.py"),
                   path.join(RACINE, "scripts", "plan_modele.py"),
                   path.join(RACINE, "scripts", "livre.py"),
                   path.join(RACINE, "scripts", "couverture.py")]);
  let cle = "";
  entrees.forEach((f) => {
    try { const s = fs.statSync(f); cle += s.size + ":" + s.mtimeMs + "|"; }
    catch (e) { cle += "?|"; }
  });
  const cache = cachePlanModele.get(siege);
  if (cache && cache.cle === cle) return cache.valeur;
  const valeur = JSON.parse(childProcess.execFileSync("python",
    [path.join(RACINE, "scripts", "plan_modele.py"), "--json"].concat(
      vueDe ? ["--vue-de", vueDe] : []),
    { cwd: RACINE, encoding: "utf-8", timeout: 30000,
      windowsHide: true, maxBuffer: 8 * 1024 * 1024,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) }));
  cachePlanModele.set(siege, { cle, valeur });
  return valeur;
}

function criticite(vueDe) {
  // LA CLE PORTE AUSSI LE SCRIPT, et l'oublier a coute une demi-heure : on
  // ajoute une sortie au calcul, on recharge la page, et l'on relit le cache
  // d'avant sans qu'aucune erreur ne le dise. Un cache dont la clef ne couvre
  // pas le code qui produit la valeur ne se trompe pas de temps en temps : il
  // se trompe exactement quand on travaille dessus.
  // `poids-etats.json` EST une entree du calcul au meme titre que le plan : une
  // note portee de 5 a 8 change tous les scores en aval. L'oublier de la clef
  // donnait un ecran qui ne bougeait pas d'un dixieme apres une renotation, et
  // rien pour le dire — le meme piege que le script oublie, une porte plus loin.
  const cles = bibliotheque.cheminsSource(RACINE).concat([
                path.join(RACINE, "etat", "poids-etats.json"),
                path.join(RACINE, "scripts", "criticite.py"),
                path.join(RACINE, "scripts", "bibliotheque.py"),
                path.join(RACINE, "scripts", "couverture.py"),
                path.join(RACINE, "scripts", "etat_du_plan.py"),
                path.join(RACINE, "scripts", "plan_modele.py"),
                path.join(RACINE, "etat", "boites.json"),
                path.join(RACINE, "etat", "personnages.json")]);
  let cle = "";
  for (const f of cles) {
    try { const s = fs.statSync(f); cle += s.size + ":" + s.mtimeMs + "|"; }
    catch (e) { cle += "?|"; }
  }
  const siege = vueDe || "__defaut__";
  const cache = cacheCriticite.get(siege);
  if (cache && cache.cle === cle) return cache.valeur;
  let valeur;
  try {
    valeur = JSON.parse(childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "criticite.py"), "--json"].concat(
        vueDe ? ["--vue-de", vueDe] : []),
      { cwd: RACINE, encoding: "utf-8", timeout: 30000,
        windowsHide: true, maxBuffer: 8 * 1024 * 1024,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) }));
  } catch (e) {
    valeur = { pas: {}, etats: {}, cercles: [], erreur: String((e && e.message) || e) };
  }
  cacheCriticite.set(siege, { cle, valeur });
  return valeur;
}

// L'audit de coherence, servi a l'ecran au lieu du terminal. `tick.py
// --verifier` produisait deja tout ceci ; personne ne le lisait.
function sante() {
  try {
    const brut = childProcess.execFileSync("python",
      [path.join(RACINE, "scripts", "tick.py"), "--verifier", "--json"],
      { cwd: RACINE, encoding: "utf-8", timeout: 30000,
        windowsHide: true, maxBuffer: 8 * 1024 * 1024,
        env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) });
    return Object.assign(JSON.parse(brut), { lu_a: Date.now() });
  } catch (e) {
    // Code de sortie 1 = il Y A des anomalies : c'est le cas nominal, et
    // execFileSync leve quand meme. La sortie est sur stdout, on la lit.
    const sortie = (e && e.stdout) ? String(e.stdout).trim() : "";
    if (sortie.startsWith("{")) {
      try { return Object.assign(JSON.parse(sortie), { lu_a: Date.now() }); }
      catch (_e) { /* tombe dans l'erreur ci-dessous */ }
    }
    return { anomalies: [], durs: 0, notes: 0, par_gravite: {},
             erreur: String((e && e.message) || e), lu_a: Date.now() };
  }
}

// La charge des acteurs : importance contre activations. Le quadrant qui
// compte est « importance haute, zero activation » — les menaces qui
// chargent en silence pendant qu'on regarde ailleurs.
function chargeActeurs() {
  const { etat } = rapportsEtJournalActivations();
  const personnages = lireJsonSansFaillir(path.join(RACINE, "etat", "personnages.json"), []);
  const listeP = Array.isArray(personnages) ? personnages : (personnages.personnages || []);
  const fiches = new Map(listeP.map((p) => [p.id, p]));
  const intentions = lireJsonSansFaillir(path.join(RACINE, "etat", "intentions.json"), []) || [];
  // L'ÉCHELLE NE SE DÉCLARE PLUS, elle se mesure : `evaluer.py --json` dépose
  // la liste des gens du quartier (même composante connexe qu'un siège occupé,
  // vingt minutes de marche au plus). Le champ `echelle` d'intentions.json a
  // disparu — il recopiait à la main ce que la topologie calcule, et mentait
  // dès que l'homme avait bougé.
  const echelles = new Map((Array.isArray(intentions) ? intentions : [])
    .map((t) => [t.personnage_id || t.id, ouQuartier(t.personnage_id || t.id)]));
  const sieges = lireJsonSansFaillir(path.join(RACINE, "etat", "joueurs.json"), []);
  const listeS = (sieges && (sieges.sieges || sieges)) || [];
  const assis = new Set((Array.isArray(listeS) ? listeS : [])
    .filter((s) => s && s.occupe).map((s) => s.personnage_id));

  const base = Number((etat.horloge || {}).base_secondes) || 0;
  const acteurs = Object.entries(etat.acteurs || {}).map(([id, a]) => {
    const fiche = fiches.get(id) || {};
    const repos = Number(a.disponible_a) || 0;
    return {
      id, nom: fiche.nom || id, titre: fiche.titre || "",
      lieu_id: fiche.lieu_id || "",
      importance: Number(a.importance) || 0,
      energie: Number(a.energie) || 0,
      activations: Number(a.activations) || 0,
      echelle: echelles.get(id) || "",
      assis: assis.has(id),
      // Le repos est une date en secondes de monde : ce qui compte a l'ecran,
      // c'est ce qu'il en RESTE a partir de maintenant.
      repos_restant_s: Math.max(0, repos - base),
    };
  });
  acteurs.sort((x, y) => y.importance - x.importance);

  // Le seuil de « ca compte » n'a pas de verite : la mediane des importances
  // non nulles separe mieux que n'importe quelle constante ecrite en dur.
  const vives = acteurs.map((a) => a.importance).filter((v) => v > 0).sort((x, y) => x - y);
  const seuil = vives.length ? vives[Math.floor(vives.length / 2)] : 0;
  return {
    acteurs, seuil,
    total_activations: (etat.historique || []).length,
    tour: (etat.rotation_activation || {}).tour || null,
    lu_a: Date.now(),
  };
}

function resumeActivations() {
  const { etat, parSession } = rapportsEtJournalActivations();
  const personnages = lireJsonSansFaillir(path.join(RACINE, "etat", "personnages.json"), []);
  const liste = Array.isArray(personnages) ? personnages : (personnages.personnages || []);
  const noms = new Map(liste.map((p) => [p.id, p.nom || p.id]));
  const activations = (etat.historique || []).slice().reverse().map((entree) => {
    const rapport = rapportDepuisEntree(entree) || {};
    const activation = rapport.activation || {};
    const meta = rapport._activation || {};
    const session = meta.session || "";
    const journal = parSession.get(session) || [];
    const resultat = journal.slice().reverse().find((x) => x.evenement === "cli.resultat") || {};
    const systeme = journal.find((x) => x.evenement === "cli.systeme") || {};
    const depart = journal.find((x) => x.evenement === "cli.depart") || {};
    const brutResultat = resultat.brut || {};
    const brutSysteme = systeme.brut || {};
    const architecture = meta.session_narrateur ? "narrateur_local" : "legacy_direct";
    return {
      id: session || path.basename(String(entree.rapport || "activation"), ".json"),
      session, qui: entree.qui, nom: noms.get(entree.qui) || entree.qui,
      termine_le: entree.termine_le || meta.cree_le || null,
      tache_id: entree.tache || ((activation.tache || {}).id) || "",
      tache: ((activation.tache || {}).quoi) || entree.tache || "",
      issue: activation.issue || "inconnue",
      activites: (activation.activites || []).length,
      budget: entree.budget == null ? meta.budget : entree.budget,
      depense: entree.depense == null ? activation.energie_depensee : entree.depense,
      duree_monde_secondes: entree.duree_monde_secondes == null
        ? (activation.activites || []).reduce((s, a) =>
            s + Number(((a.temps || {}).duree_s) || 0), 0)
        : entree.duree_monde_secondes,
      restitue: entree.restitue == null ? null : entree.restitue,
      energie_avant: entree.energie_avant == null ? null : entree.energie_avant,
      energie_apres: entree.energie_apres == null ? null : entree.energie_apres,
      importance: entree.importance == null ? meta.importance : entree.importance,
      front: entree.front || meta.front || "",
      duree_ms: meta.duree_ms == null ? brutResultat.duration_ms : meta.duree_ms,
      cout_usd: meta.cout_usd == null ? brutResultat.total_cost_usd : meta.cout_usd,
      modele: meta.modele || brutSysteme.model || "inconnu",
      effort: meta.effort || depart.effort || "inconnu",
      evenements: journal.length,
      architecture,
    };
  });
  return { activations, ...prevoirActivations() };
}

function detailActivation(session) {
  const { etat, parSession } = rapportsEtJournalActivations();
  let entree = null, rapport = null;
  for (const candidate of (etat.historique || [])) {
    const r = rapportDepuisEntree(candidate);
    if (r && r._activation && r._activation.session === session) {
      entree = candidate; rapport = r; break;
    }
  }
  if (!entree || !rapport) return null;
  const meta = rapport._activation || {};
  const architecture = meta.session_narrateur ? "narrateur_local" : "legacy_direct";
  const transcript = transcriptClaude(session);
  const sessionPnj = meta.session_pnj || null;
  const transcriptPnj = sessionPnj ? transcriptClaude(sessionPnj) : [];
  const journal = parSession.get(session) || [];
  const resultat = journal.slice().reverse().find((x) => x.evenement === "cli.resultat") || {};
  const brutResultat = resultat.brut || {};
  let message = meta.message || null;
  if (!message) {
    const envoi = transcript.find((x) => x.type === "queue-operation"
      && x.operation === "enqueue" && typeof x.content === "string");
    const usager = transcript.find((x) => x.type === "user"
      && x.message && typeof x.message.content === "string");
    message = (envoi && envoi.content) || (usager && usager.message.content) || null;
  }
  let reponse = brutResultat.result || null;
  if (!reponse) {
    for (let i = transcript.length - 1; i >= 0 && !reponse; i--) {
      const ev = transcript[i];
      if (ev.type !== "assistant" || !ev.message) continue;
      const contenu = ev.message.content;
      if (typeof contenu === "string") reponse = contenu;
      else if (Array.isArray(contenu)) reponse = contenu
        .filter((b) => b && b.type === "text" && typeof b.text === "string")
        .map((b) => b.text).join("\n");
    }
  }
  return {
    entree, rapport, architecture,
    // La regie ne reconstruit jamais un prompt systeme : il est construit par
    // les constructeurs de depecher.py, puis depose tel quel dans le rapport.
    system_prompt: meta.system_prompt || null,
    message,
    reponse,
    thread: transcript,
    journal,
    pnj: sessionPnj ? {
      session: sessionPnj,
      system_prompt: meta.system_prompt_pnj || null,
      message: meta.appel_pnj || null,
      tentative: meta.tentative_pnj || null,
      thread: transcriptPnj,
    } : null,
    execution: {
      duree_ms: meta.duree_ms == null ? brutResultat.duration_ms : meta.duree_ms,
      cout_usd: meta.cout_usd == null ? brutResultat.total_cost_usd : meta.cout_usd,
      usage: Object.keys(meta.usage || {}).length ? meta.usage : (brutResultat.usage || {}),
      tours: meta.tours == null ? brutResultat.num_turns : meta.tours,
    },
  };
}

// ---- le fil d'un homme, refait de bout en bout ---------------------------
// Ce que Corneille ouvre en touchant un visage sur le plan du château. Deux
// moitiés d'une même vie, que rien ne montrait ensemble jusqu'ici :
//
//   — CE QU'IL A DIT ET FAIT EN SCÈNE. Ses répliques et ses gestes dans
//     `etat/flux.jsonl`, plus les récits du narrateur qui le nomment : sans
//     eux, une réplique tombe sans la salle qui la porte.
//   — CE QU'IL A VÉCU HORS SCÈNE. Chacune de ses activations
//     (`etat/activations/*.json`) : l'appel du narrateur, sa tentative telle
//     qu'il l'a écrite, ce que le monde en a fait, et ce qu'il en a appris.
//
// L'ordre est celui du MONDE, pas celui des fichiers : les items du flux
// portent leur date au complet, les activations la journée du dossier qui les
// a ouvertes. Une activation dont la journée est illisible se pose à la fin,
// dans l'ordre où elle s'est terminée — jamais silencieusement au milieu.
//
// Lecture seule de bout en bout : rien n'entre dans `etat/`, rien n'entre dans
// le flux. Ce fil vit dans le navigateur de la régie et meurt avec sa page.
const JOUR_MINUTES = 1440;

function nomsDesPersonnages() {
  const brut = lireJsonSansFaillir(path.join(RACINE, "etat", "personnages.json"), []);
  const liste = Array.isArray(brut) ? brut : (brut.personnages || []);
  return new Map(liste.map((p) => [p.id, p.nom || p.id]));
}

function journeeDuDossier(message) {
  const m = String(message || "").match(/"date_du_monde"\s*:\s*\{[^}]*\}/);
  if (!m) return null;
  try { return JSON.parse("{" + m[0] + "}").date_du_monde || null; }
  catch (_e) { return null; }
}

function filPersonnage(id) {
  const noms = nomsDesPersonnages();
  const nom = noms.get(id) || id;
  const entrees = [];
  // rang : [minute absolue du monde, désambiguïsateur]. Les activations d'une
  // journée se posent après ce qui s'y est dit — le dossier ne donne que le
  // jour, et prétendre à la minute serait inventer une heure.
  const poser = (rang, second, e) => entrees.push(Object.assign({ _r: rang, _s: second }, e));

  let flux = [];
  try {
    flux = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim())
      .map((l) => { try { return JSON.parse(l); } catch (_e) { return null; } })
      .filter(Boolean);
  } catch (_e) { /* pas de flux : il reste ses activations */ }

  // Le narrateur ne nomme pas les gens par leur id : on le cherche par son nom,
  // et par son prénom seul quand il en a un — c'est ainsi qu'une salle parle.
  // On cherche le nom entier, et chaque morceau assez long pour ne désigner que
  // lui — mais aux BORNES du mot : sans elles, « Sara » attrape Sarnes, et le
  // fil d'une femme se remplit des récits d'une autre maison.
  const appellations = [nom].concat(nom.split(/\s+/).filter((x) => x.length > 3));
  const bornes = appellations.map((a) =>
    new RegExp("(^|[^\\p{L}])" + a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") +
      "($|[^\\p{L}])", "u"));
  const nomme = (t) => bornes.some((re) => re.test(String(t || "")));
  let date = null;
  flux.forEach((it, i) => {
    if (it.date) date = it.date;
    const rang = absolues(date);
    if (rang === null) return;
    const sien = it.locuteur_id === id || it.acteur_id === id;
    if (sien && (it.type === "replique" || it.type === "geste" || it.type === "table")) {
      poser(rang, i, { source: "scene", genre: it.type === "replique" ? "replique" : "geste",
        qui: nom, texte: it.texte || "", date, lieu: it.lieu || "" });
    } else if ((it.type === "recit" || it.type === "breve" || it.type === "marque")
               && nomme(it.texte)) {
      poser(rang, i, { source: "scene", genre: "narrateur", qui: "Le narrateur",
        texte: (it.titre ? it.titre + " — " : "") + (it.texte || ""), date, lieu: it.lieu || "" });
    }
  });

  // Les activations. On les lit toutes : le nom du fichier porte l'acteur, mais
  // c'est le champ `qui` du rapport qui fait foi.
  let fichiers = [];
  try {
    fichiers = fs.readdirSync(DEPOT_ACTIVATIONS)
      .filter((f) => /^\d{8}-.*\.json$/.test(f)).sort();
  } catch (_e) { /* aucune activation journalisée */ }
  let horsRang = 0;
  fichiers.forEach((f) => {
    const rapport = lireJsonSansFaillir(path.join(DEPOT_ACTIVATIONS, f), null);
    if (!rapport || rapport.qui !== id) return;
    const meta = rapport._activation || {};
    const act = rapport.activation || {};
    const jour = journeeDuDossier(meta.message);
    // Le jour du dossier, à sa toute fin : ce qui s'est dit ce jour-là dans la
    // salle vient d'abord, ce qu'il est allé faire ensuite.
    const rang = jour ? absolues(jour) + JOUR_MINUTES - 1 : Infinity;
    const second = jour ? f : (++horsRang);
    const tete = { source: "activation", date: jour || null,
      tache: (act.tache || {}).quoi || "", session: meta.session || "",
      termine_le: meta.cree_le || null, date_incertaine: !jour };
    if (meta.appel_pnj) {
      poser(rang, second, Object.assign({ genre: "appel", qui: "Le narrateur",
        texte: meta.appel_pnj }, tete));
    }
    const t = meta.tentative_pnj;
    if (t && t.quoi) {
      const bas = [];
      if (t.moyens && t.moyens.length) bas.push("Avec : " + t.moyens.join(" ; ") + ".");
      if (t.effet_recherche) bas.push("Pour : " + t.effet_recherche);
      if (t.renonce_si) bas.push("Renonce si : " + t.renonce_si);
      poser(rang, second, Object.assign({ genre: "tentative", qui: nom,
        texte: (t.verbe ? t.verbe.toUpperCase() + " — " : "") + t.quoi,
        detail: bas.join("\n") }, tete));
    }
    (act.activites || []).forEach((a) => {
      const quoi = (a.action || {}).quoi || a.quoi || "";
      if (quoi) {
        poser(rang, second, Object.assign({ genre: "activite", qui: nom,
          texte: ((a.action || {}).verbe ? (a.action.verbe + " — ") : "") + quoi,
          minutes: Math.round(Number((a.temps || {}).duree_s || 0) / 60) }, tete));
      }
      (a.resultats_produits || []).forEach((r) => {
        if (!r.apres) return;
        poser(rang, second, Object.assign({ genre: "resultat", qui: "Ce qu'il en retient",
          texte: String(r.apres), certitude: r.certitude || "" }, tete));
      });
      if (a.blocage) {
        poser(rang, second, Object.assign({ genre: "blocage", qui: "Ce qui l'arrête",
          texte: typeof a.blocage === "string" ? a.blocage : JSON.stringify(a.blocage) }, tete));
      }
    });
    if (act.issue && act.issue !== "avance") {
      poser(rang, second, Object.assign({ genre: "issue", qui: "L'issue",
        texte: String(act.issue) }, tete));
    }
  });

  entrees.sort((a, b) => (a._r - b._r) ||
    (typeof a._s === typeof b._s ? (a._s < b._s ? -1 : a._s > b._s ? 1 : 0) : 0));
  entrees.forEach((e) => { delete e._r; delete e._s; });
  return {
    id, nom, entrees,
    scenes: entrees.filter((e) => e.source === "scene").length,
    activations: new Set(entrees.filter((e) => e.source === "activation")
      .map((e) => e.session)).size,
  };
}

// « Emmène-moi au moment où X est arrivé. » Corneille ne remonte pas dix mille
// lignes à la molette : elle demande, son MJ cherche, et le fil s'ouvre à
// l'endroit dit. Deux gestes distincts, et ils ne se confondent pas :
//
//   — CHERCHER (`/regie/chercher?q=`) rend les endroits du flux où la chose
//     est dite, avec leur date et trois lignes autour. C'est l'outil du MJ :
//     il lit, il tranche lequel des dix-sept est le bon moment, il répond.
//   — EXTRAIRE (`/regie/extrait?de=&a=`) rend la tranche elle-même, telle
//     qu'elle a été jouée. C'est ce que la page repose dans le fil quand le MJ
//     a dit où.
//
// On ne cherche PAS à la place du MJ. « Le moment où Steffon est arrivé » n'est
// pas une chaîne de caractères : c'est un jugement sur ce qui compte, et une
// recherche plein texte rendrait la première occurrence du mot, presque jamais
// la bonne. Le serveur donne les candidats, l'homme choisit.
function chercherDansFlux(q, max) {
  const besoin = String(q || "").trim().toLowerCase();
  if (!besoin) return { q, trouves: [] };
  const mots = besoin.split(/\s+/).filter((m) => m.length > 2);
  let flux = [];
  try {
    flux = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim())
      .map((l) => { try { return JSON.parse(l); } catch (_e) { return null; } });
  } catch (_e) { return { q, trouves: [] }; }
  const trouves = [];
  let date = null, lieu = "";
  flux.forEach((it, i) => {
    if (!it) return;
    if (it.date) date = it.date;
    if (it.lieu) lieu = it.lieu;
    const t = String(it.texte || "").toLowerCase();
    if (!t) return;
    // Tous les mots utiles, dans le même item : un « et » de plus ne doit pas
    // rendre la moitié du fil.
    const score = mots.length ? (mots.every((m) => t.indexOf(m) !== -1) ? mots.length : 0)
                              : (t.indexOf(besoin) !== -1 ? 1 : 0);
    if (!score) return;
    trouves.push({ i, type: it.type, date, lieu,
      qui: it.locuteur_id || it.acteur_id || null,
      extrait: String(it.texte).slice(0, 220) });
  });
  // Les derniers d'abord : on cherche presque toujours quelque chose de récent.
  return { q, total: trouves.length, trouves: trouves.slice(-(max || 12)).reverse() };
}

function extraitDuFlux(de, a) {
  let flux = [];
  try {
    flux = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim())
      .map((l) => { try { return JSON.parse(l); } catch (_e) { return null; } })
      .filter(Boolean);
  } catch (_e) { return { de: 0, a: 0, items: [] }; }
  const debut = Math.max(0, Math.min(de | 0, flux.length));
  const fin = Math.max(debut, Math.min(a | 0, flux.length, debut + 200));
  // Le nom vient avec : la page qui repose une vieille tranche dans le fil n'a
  // pas la galerie de cette scène-là sous la main, et « robert-quince » n'est
  // pas une façon de nommer un homme.
  const noms = nomsDesPersonnages();
  return { de: debut, a: fin, total: flux.length,
    items: flux.slice(debut, fin).map((it, k) => Object.assign({ _i: debut + k,
      _nom: noms.get(it.locuteur_id || it.acteur_id) || null }, it)) };
}

function regie() {
  const lire = (f, defaut) => {
    try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8")); }
    catch (e) { return defaut; }
  };
  const monde = lire("monde.json", {});
  const aujourdhui = jourAbsolu(monde.date) || 0;
  const dans = (d) => { const n = jourAbsolu(d); return n === null ? null : n - aujourdhui; };

  const gens = {};
  (lire("personnages.json", []) || []).forEach((p) => { gens[p.id] = p; });
  const lieux = {};
  (lire("lieux.json", []) || []).forEach((l) => { lieux[l.id] = l; });
  const nom = (id) => (gens[id] && gens[id].nom) || id;
  const ouEst = (id) => {
    const p = gens[id];
    if (!p || !p.lieu_id) return "";
    return (lieux[p.lieu_id] && lieux[p.lieu_id].nom) || p.lieu_id;
  };

  // ---- 1. les têtes -------------------------------------------------------
  const intentions = lire("intentions.json", []) || [];
  const sieges = lire("joueurs.json", null);
  const listeSieges = (sieges && (sieges.sieges || sieges)) || [];
  const occupes = new Set((Array.isArray(listeSieges) ? listeSieges : [])
    .filter((s) => s && s.occupe).map((s) => s.personnage_id));
  const tousSieges = (Array.isArray(listeSieges) ? listeSieges : [])
    .map((s) => s && s.personnage_id).filter(Boolean);

  const tetes = intentions.map((t) => {
    const plan = t.plan || [];
    const encours = plan.filter((e) => e.etat !== "fait" && e.etat !== "abandonne");
    // La prochaine horloge qui tombe : c'est le tri par défaut, parce que
    // c'est la seule question qu'on se pose avant un tick.
    let prochaine = null, prochaineQuoi = "";
    encours.forEach((e) => {
      if (typeof e.jours_restants !== "number") return;
      if (prochaine === null || e.jours_restants < prochaine) {
        prochaine = e.jours_restants; prochaineQuoi = e.quoi || e.id || "";
      }
    });
    const age = dans(t.date_maj);
  return {
      id: t.personnage_id,
      nom: nom(t.personnage_id),
      echelle: ouQuartier(t.personnage_id),
      lieu: ouEst(t.personnage_id) || t.lieu_note || "",
      intention: t.intention || "",
      date_maj: dateCourte(t.date_maj),
      age_maj: age === null ? null : -age,
      etapes: encours.length,
      etapes_total: plan.length,
      // `jours_restants: null` n'est PAS une horloge oubliée : le schéma en
      // fait une posture permanente — tenir la porte de mer, peigner la grève
      // à chaque basse mer, ne pas voir ce qu'on l'a payé pour ne pas voir.
      // Elle n'est jamais « faite » et jamais décomptée, par construction.
      // Ne compter comme sans horloge que l'étape où le champ MANQUE, seul cas
      // où quelqu'un a réellement oublié de la poser. Mesure du 129.4.3 : sur
      // six acteurs signalés « rien ne tombera jamais », cinq étaient des
      // postures correctes et un seul, Maron Sec et son cycle de six jours,
      // était une vraie horloge manquante — l'alerte cachait le seul vrai cas.
      sans_horloge: encours.filter(
        (e) => !("jours_restants" in e) ||
               (e.jours_restants !== null && typeof e.jours_restants !== "number")
      ).length,
      prochaine, prochaine_quoi: prochaineQuoi,
      declencheurs: (t.declencheurs || []).length,
      attitude: t.attitude_joueur || "",
      mandat: t.mandat || null,
      siege: occupes.has(t.personnage_id),
    };
  });
  // PLUS DE PLAFOND D'ACTEURS : ce n'est pas le nombre de têtes qui coûte,
  // c'est où elles sont. Vingt têtes au loin pèsent moins que huit dans la
  // salle, et le quartier se resserre tout seul sur ce que le joueur atteint.
  const BUDGETS = { "quartier": null, "au loin": null };
  const groupes = ["quartier", "au loin"].map((e) => ({
    echelle: e, budget: BUDGETS[e],
    tetes: tetes.filter((t) => t.echelle === e)
      .sort((a, b) => (a.prochaine === null) - (b.prochaine === null)
        || (a.prochaine - b.prochaine) || (b.age_maj - a.age_maj)),
  }));
  const horsEchelle = tetes.filter((t) => !BUDGETS.hasOwnProperty(t.echelle));

  // Les deux fautes symétriques : un siège occupé qui garde une tête (on le
  // joue à sa place), un siège vacant qui n'en a pas (il dort sans qu'on le voie).
  const avecTete = new Set(intentions.map((t) => t.personnage_id));
  const alertes = [];
  tousSieges.forEach((id) => {
    if (occupes.has(id) && avecTete.has(id))
      alertes.push({ gravite: "grave", texte: nom(id) + " : siège OCCUPÉ et pourtant une tête dans intentions.json" });
    if (!occupes.has(id) && !avecTete.has(id))
      alertes.push({ gravite: "grave", texte: nom(id) + " : siège VACANT et aucune tête — il dort pendant qu'on regarde ailleurs" });
  });
  groupes.forEach((g) => {
    if (g.budget && g.tetes.length > g.budget)
      alertes.push({ gravite: "tiede", texte: "échelle « " + g.echelle + " » : " + g.tetes.length + " têtes pour ~" + g.budget });
  });
  tetes.forEach((t) => {
    if (t.age_maj !== null && t.age_maj >= 3 && t.echelle === "quartier")
      alertes.push({ gravite: "tiede", texte: t.nom + " : tête non relue depuis " + t.age_maj + " jours" });
    if (t.etapes && t.sans_horloge === t.etapes)
      alertes.push({ gravite: "tiede", texte: t.nom + " : aucune étape n'a d'horloge — rien ne tombera jamais" });
  });

  // ---- 2. le calendrier ---------------------------------------------------
  const echeances = [];
  (lire("evenements.json", []) || []).forEach((e) => {
    if (e.statut === "resolu" || e.statut === "annule" || e.statut === "devie") return;
    const j = dans(e.date_prevue);
    if (j === null) return;
    echeances.push({
      jours: j, quoi: e.description || e.id, famille: e.type === "canon" ? "canon" : "événement",
      qui: (e.acteurs || []).map(nom).join(", "), importance: e.importance || null,
      lieu: e.lieu_id ? ((lieux[e.lieu_id] && lieux[e.lieu_id].nom) || e.lieu_id) : "",
    });
  });
  intentions.forEach((t) => {
    (t.plan || []).forEach((e) => {
      if (e.etat === "fait" || e.etat === "abandonne") return;
      if (typeof e.jours_restants !== "number") return;
      echeances.push({
        jours: e.jours_restants, quoi: e.quoi || e.id, famille: "étape",
        qui: nom(t.personnage_id), echelle: ouQuartier(t.personnage_id),
        bloque: (e.depend_de || []).length ? "dépend de " + (e.depend_de || []).join(", ") : "",
      });
    });
  });
  (((lire("plis.json", {}) || {}).plis) || []).forEach((p) => {
    if (p.etat === "remis" || p.etat === "confirme" || p.etat === "perdu") return;
    const j = dans(p.attendu_le);
    if (j === null) return;
    echeances.push({
      jours: j, quoi: p.porte || p.id, famille: "pli",
      qui: nom(p.de) + " → " + nom(p.pour), etat: p.etat || "",
      lieu: p.vers ? ((lieux[p.vers] && lieux[p.vers].nom) || p.vers) : "",
    });
  });
  echeances.sort((a, b) => a.jours - b.jours);

  // ---- 3. les mains ---------------------------------------------------
  const mains = (((lire("mains.json", {}) || {}).mains) || []).map((a) => {
    const mesures = (a.mesure || []).map((m) => {
      const par = (m.rythme && typeof m.rythme.par === "number") ? m.rythme.par : 0;
      // Le seuil le plus proche dans le temps, à ce rythme-là. C'est le
      // seul chiffre qui compte : dans combien de jours ça devient une affaire.
      let jours = null, seuilQui = "";
      (a.seuils || []).filter((s) => s.mesure_id === m.id).forEach((s) => {
        if (s.franchi_le || !par) return;
        const ecart = (s.quand === "sous") ? (m.valeur - s.valeur) : (s.valeur - m.valeur);
        const vitesse = (s.quand === "sous") ? -par : par;
        if (vitesse <= 0) return;
        const d = Math.ceil(ecart / vitesse);
        if (d < 0) return;
        if (jours === null || d < jours) { jours = d; seuilQui = s.affaire || s.id; }
      });
      return { id: m.id, quoi: m.quoi, valeur: m.valeur, unite: m.unite || "",
        par, jours_avant_seuil: jours, seuil: seuilQui };
    });
    return {
      id: a.id, quoi: a.quoi,
      porteur: a.porteur ? (a.porteur.type === "lieu"
        ? ((lieux[a.porteur.id] && lieux[a.porteur.id].nom) || a.porteur.id)
        : nom(a.porteur.id)) : "— personne",
      sans_porteur: !a.porteur || a.porteur.type === "lieu",
      mandat: a.mandat || null,
      dernier_rapport: a.dernier_rapport ? dateCourte(a.dernier_rapport) : null,
      // Le brouillard s'applique au RAPPORT, pas au calcul : ce qui compte
      // n'est pas la mesure mais depuis quand personne ne l'a dite au joueur.
      rapport_age: a.dernier_rapport ? (() => {
        const j = dans(a.dernier_rapport && a.dernier_rapport.date
          ? a.dernier_rapport.date : a.dernier_rapport);
        return j === null ? null : -j;
      })() : null,
      rapport_a: (a.dernier_rapport && a.dernier_rapport.a) ? nom(a.dernier_rapport.a) : "",
      date_maj: dateCourte(a.date_maj),
      mesures,
      franchis: (a.seuils || []).filter((s) => s.franchi_le)
        .map((s) => ({ affaire: s.affaire || s.id, promeut: s.promeut || "", le: dateCourte(s.franchi_le) })),
    };
  });
  mains.forEach((a) => a.mesures.forEach((m) => {
    if (m.jours_avant_seuil !== null && m.jours_avant_seuil <= 10)
      alertes.push({ gravite: "tiede", texte: a.id + " : seuil atteint dans " + m.jours_avant_seuil + " jours (" + m.quoi + ")" });
  }));

  // LE TISSU — calcule en Python par `tisser.py` + `evaluer.py --json`.
  // La regie ne recalcule rien : elle relit et elle dit l'AGE. Un graphe de
  // la veille affiche comme l'etat du jour serait le meme mensonge que le
  // cache d'une minute que cette page refuse deja.
  let tissu = null;
  try {
    const pt = path.join(RACINE, "etat", "tissu", "evaluation.json");
    tissu = JSON.parse(fs.readFileSync(pt, "utf-8"));
    tissu.calcule_il_y_a_s = Math.round((Date.now() - fs.statSync(pt).mtimeMs) / 1000);
  } catch (e) { tissu = null; }

  // Le graphe complet servi a la regie. Le projecteur Python reste l'unique
  // definition des liens ; le serveur ne fait qu'ajouter les mesures de
  // l'evaluation sur les noeuds et des aretes fantomes pour les candidats.
  let graphe = null;
  try {
    const base = path.join(RACINE, "etat", "tissu");
    const brutNoeuds = JSON.parse(fs.readFileSync(path.join(base, "noeuds.json"), "utf-8"));
    const aretes = fs.readFileSync(path.join(base, "aretes.jsonl"), "utf-8")
      .split(/\r?\n/).filter(Boolean).map((ligne, i) => Object.assign({ id: "a:" + i }, JSON.parse(ligne)));
    const noeuds = Object.keys(brutNoeuds).map((id) => Object.assign({ id }, brutNoeuds[id]));
    const parId = new Map(noeuds.map((n) => [n.id, n]));
    const goulots = new Map(((tissu && tissu.goulots) || []).map((g) => [g.noeud, g]));
    const desequilibres = new Map(((tissu && tissu.desequilibres) || []).map((g) => [g.noeud, g]));
    const forces = new Map(((tissu && tissu.force) || []).map((f) => ["pers:" + f.qui, f]));
    const murs = new Map(((tissu && tissu.murs) || []).map((m) => [m.id, m]));
    const critique = ((tissu && tissu.critique && tissu.critique[0]) || {}).chaine || [];
    const critiques = new Set(critique.map((n) => n.id));
    const couplesCritiques = new Set();
    for (let i = 0; i + 1 < critique.length; i++)
      couplesCritiques.add(critique[i].id + "\u0000" + critique[i + 1].id);

    noeuds.forEach((n) => {
      n.goulot = goulots.get(n.id) || null;
      n.desequilibre = desequilibres.get(n.id) || null;
      n.force = forces.get(n.id) || null;
      n.mur = murs.get(n.id) || null;
      n.critique = critiques.has(n.id);
      n.double_genre = (n.genres || []).length > 1;
    });
    aretes.forEach((a, i) => {
      a.critique = couplesCritiques.has(a.de + "\u0000" + a.vers);
      for (const bout of ["de", "vers"]) {
        if (parId.has(a[bout])) continue;
        const original = a[bout];
        const id = "pendant:" + i + ":" + bout;
        const n = { id, genre: "pendant", genres: ["pendant"], ou: "adressage",
          quoi: original === "?" ? "extrémité non adressée" : String(original),
          pendant: true, bout_original: original };
        noeuds.push(n); parId.set(id, n); a[bout] = id; a.bout_original = original;
      }
    });

    // Les candidats restent des hypotheses : pointilles et transparents. Une
    // vraie arete `equilibre` les remplace automatiquement au prochain tissage.
    ((tissu && tissu.desequilibres) || []).forEach((d) => {
      (d.candidats || []).forEach((c, i) => {
        if (!parId.has(c.id) || !parId.has(d.noeud)) return;
        aretes.push({ id: "candidat:" + d.noeud + ":" + i, de: c.id,
          vers: d.noeud, nature: "candidat_equilibre", source: "evaluation/texte",
          flou: true, virtuel: true, texte: "candidat textuel non tissé" });
      });
    });

    const journal = lire("journal.json", {}) || {};
    const observateurs = [{ id: "mj", nom: "MJ — vérité complète" }];
    const joueur = journal.personnage_joueur_id;
    if (joueur) observateurs.push({ id: joueur, nom: nom(joueur) });
    if (gens["aurore-inchauspe"] && joueur !== "aurore-inchauspe")
      observateurs.push({ id: "aurore-inchauspe", nom: nom("aurore-inchauspe") });
    Object.values(gens).sort((a, b) => String(a.nom).localeCompare(String(b.nom), "fr"))
      .forEach((p) => {
        if (!p.id || observateurs.some((o) => o.id === p.id)) return;
        observateurs.push({ id: p.id, nom: p.nom || p.id });
      });

    // Qui émet l'importance narrative : les sièges occupés, et le principal
    // en tête. La régie diffuse depuis eux — un tissu n'a pas de centre en
    // soi, il en a un parce qu'un joueur est assis quelque part.
    const emetteurs = (Array.isArray(listeSieges) ? listeSieges : [])
      .filter((s) => s && s.occupe && s.personnage_id)
      .map((s) => ({ id: s.personnage_id, nom: s.nom || nom(s.personnage_id),
        role: s.role || "second" }));

    const suivables = aretes.filter((a) => !a.flou && !a.virtuel);
    const pendantes = suivables.filter((a) => parId.get(a.de).pendant || parId.get(a.vers).pendant);
    graphe = {
      noeuds, aretes, observateurs, sieges: emetteurs,
      resume: {
        noeuds: Object.keys(brutNoeuds).length,
        aretes: aretes.filter((a) => !a.virtuel).length,
        suivables: suivables.length,
        resolues: suivables.length - pendantes.length,
        pendantes: pendantes.length,
        floues: aretes.filter((a) => a.flou && !a.virtuel).length,
        doubles: noeuds.filter((n) => n.double_genre).length,
        natifs: aretes.filter((a) => a.natif).length,
        candidats: aretes.filter((a) => a.virtuel).length,
        routes: aretes.filter((a) => a.connaissance).length,
        murs_sans_route: murs.size,
      },
    };
  } catch (e) {
    graphe = { erreur: String(e.message || e), noeuds: [], aretes: [], observateurs: [] };
  }
  return {
    tissu, graphe,
    date: monde.date || null, date_texte: dateCourte(monde.date),
    tension: monde.tension == null ? null : monde.tension, phase: monde.phase || "",
    horloges: lire("horloges.json", {}),
    groupes, hors_echelle: horsEchelle, alertes,
    echeances, mains,
  };
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
          multi: !!l,
          // `regie` : ce siège ne joue personne, il regarde. C'est lui qui
          // ouvre le fil d'un homme depuis le plan du château (modules/regie.js).
          moi: j ? { personnage_id: j.personnage_id, nom: j.nom || "", regie: !!j.regie } : null,
          sieges: (l || []).map((x) => ({ personnage_id: x.personnage_id, nom: x.nom || "" })),
        }));
      }
      // Débug — changer de siège sans rouvrir l'URL au jeton. On ne rend JAMAIS
      // les jetons au navigateur : on demande un personnage, le serveur pose le
      // cookie correspondant et renvoie à la racine. Outil de mise au point.
      if (url === "/bascule") {
        const l = roster();
        if (!l || l.length < 2) return envoyer(res, 404, JSON.stringify({ erreur: "roster" }));
        const q = (req.url.split("?")[1] || "").match(/(?:^|&)vers=([^&]*)/);
        const vers = decodeURIComponent((q && q[1]) || "");
        const j = qui(req, url);
        // Sans cible : le suivant du roster, en boucle.
        const i = j ? l.findIndex((x) => x.jeton === j.jeton) : -1;
        const cible = vers ? l.find((x) => x.personnage_id === vers) : l[(i + 1) % l.length];
        if (!cible) return envoyer(res, 404, JSON.stringify({ erreur: vers }));
        res.writeHead(302, {
          "Set-Cookie": "jeton=" + encodeURIComponent(cible.jeton) + "; Path=/; Max-Age=31536000; SameSite=Lax",
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
      if (url === "/presence") {
        try {
          const siege = qui(req, url);
          const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
          let moi = siege && siege.personnage_id;
          // LA RÉGIE N'EST NULLE PART, donc elle se tient où se tient le siège
          // principal — sinon son plan resterait vide et il n'y aurait aucun
          // visage à toucher, ce qui est tout ce qu'elle vient faire ici. Elle
          // ne perd rien au passage : le brouillard ne s'applique pas à un
          // siège qui n'incarne personne (voir `regie` dans etat/joueurs.json).
          const enRegie = !!(siege && siege.regie);
          if (enRegie) {
            const principal = (roster() || []).find((s) => s.role === "principal")
              || (roster() || [])[0];
            moi = (principal && principal.personnage_id) || null;
          }
          // Le repli sur le journal n'est bon qu'en partie SEULE. À deux, un
          // visiteur sans jeton hériterait de la pièce de la reine — et donc de
          // qui s'y trouve. Sans siège, on ne sait pas qui regarde : on ne dit rien.
          if (!moi) {
            const l = roster();
            if (!l || l.length < 2) {
              try { moi = lire("journal.json").personnage_joueur_id || null; } catch (e) {}
            }
          }
          // La position ne se stocke pas, elle se calcule — scripts/presence.py.
          // `presence` ne tient que les EXCEPTIONS (ce qu'une scène a constaté) ;
          // le reste se résout à L'HEURE DE CELUI QUI REGARDE.
          //
          // On lisait ici l'instantané `resolu` que `append_flux.py` fige à
          // chaque poussée. C'était faux d'une façon qu'on ne voyait pas : entre
          // deux items — c'est-à-dire presque toujours — le château restait
          // arrêté à la minute du dernier push, et PERSONNE N'ÉTAIT JAMAIS EN
          // MARCHE. Mesuré sur une journée de Peyredragon, quelqu'un traverse
          // 38 % des minutes ; le cache n'en montrait aucune. On recalcule donc
          // pour de bon, avec un cache court pour ne pas relancer Python à
          // chaque battement de sonde. Si le calcul échoue, on retombe sur
          // `resolu`, puis sur les exceptions nues : le jeu ne s'arrête pas.
          let presence = {};
          let connus = [];
          try {
            const f = lire("presence.json");
            presence = f.presence || {};
            const r = resoudrePresence(dateDe({ personnage_id: moi }))
              || (f.resolu && f.resolu.gens);
            if (r) {
              presence = {};
              // Qui est SUIVI, transit compris : un homme dans l'escalier n'est
              // dans aucune pièce, mais on sait où il est — il ne doit pas passer
              // pour un inconnu de passage.
              connus = Object.keys(r);
              for (const id of Object.keys(r)) {
                // En chemin, on n'est dans la pièce de personne : on est dans
                // l'escalier, et l'on n'y partage rien. Un joueur ne le voit
                // donc pas — il ne le croise pas.
                //
                // LA RÉGIE, SI. Elle ne partage aucune pièce avec personne :
                // elle regarde le château, et un homme qui traverse est
                // justement ce qu'elle vient voir. On lui rend le tracé entier
                // (`route`), le rang de la salle franchie et la fraction du pas
                // en cours — de quoi le poser entre deux portes. Il reste hors
                // de `avec` et son `ici` reste faux : il n'est chez personne.
                if (r[id].etat === "en-chemin") {
                  if (!enRegie) continue;
                  presence[id] = {
                    salle: r[id].salle, lieu: null,
                    marche: {
                      de: r[id].de || null, vers: r[id].vers || null,
                      vers_lieu: r[id].vers_lieu || null,
                      prochaine: r[id].prochaine || null,
                      route: r[id].route || [], franchi: r[id].franchi || 0,
                      pas: r[id].pas || 0, arrive_dans: r[id].arrive_dans || 0,
                    },
                  };
                  continue;
                }
                presence[id] = { salle: r[id].salle, lieu: r[id].lieu };
              }
            }
          } catch (e) {}
          // ET L'EXCEPTION REPREND LE DESSUS QUAND LE CALCUL NE SAIT PAS. Le
          // résolu ne connaît que les salles de la topologie du château : un
          // joueur posé par une scène dans un endroit qui n'y figure pas — une
          // taverne du bourg, un comptoir de change — en sort ABSENT, et il
          // passait alors pour n'être nulle part. Or une pièce constatée par une
          // scène est plus vraie qu'un calcul qui ne sait pas la placer : c'est
          // la règle de tout le fichier, « l'item poussé fait foi ».
          try {
            const brut = lire("presence.json").presence || {};
            for (const id of Object.keys(brut)) {
              if (!presence[id] && brut[id] && brut[id].salle) {
                presence[id] = { salle: brut[id].salle, lieu: brut[id].lieu };
                if (!connus.includes(id)) connus.push(id);
              }
            }
          } catch (e) {}
          // LA RÉGIE SE TIENT QUELQUE PART, et c'est elle qui le dit. Son
          // entrée de `etat/joueurs.json` porte `salle` et `lieu` : elle n'a
          // pas de corps dans `presence.json` — rien ne l'y met, rien ne l'en
          // sort —, mais elle a un poste d'observation, et le plan s'ouvre là.
          // Sans cette déclaration, elle retombe sur l'épaule du principal.
          let mien = moi && presence[moi];
          if (enRegie && siege.salle) mien = { salle: siege.salle, lieu: siege.lieu || "" };
          // Sans entrée pour le regardeur, on ne sait pas où il est : on ne dit
          // rien plutôt que de nommer une pièce au hasard. `connue: false` dit au
          // navigateur de s'en tenir à ce que le flux lui montre, comme avant.
          if (!mien) return envoyer(res, 200, JSON.stringify({ connue: false, avec: [] }));
          const meme = (a, b) => (a.salle && b.salle)
            ? a.salle === b.salle : (a.lieu || "") === (b.lieu || "");
          const noms = {};
          // le titre vient avec : c'est lui qui dit l'office, et le décor en
          // tire le signe qu'il pose sur chaque tache (voir taches.js)
          const titres = {};
          try {
            lire("personnages.json").forEach((p) => {
              noms[p.id] = p.nom;
              if (p.titre) titres[p.id] = p.titre;
            });
          } catch (e) {}
          const avec = Object.keys(presence)
            .filter((id) => id !== moi && !presence[id].marche
              && meme(presence[id], mien))
            .map((id) => ({ id, nom: noms[id] || id }));
          // `connus` : les gens dont la présence est tenue. Le navigateur en a
          // besoin pour distinguer « ailleurs » de « pas suivi » — un pêcheur de
          // passage n'est dans aucun fichier et garde son visage. Cela ne dit
          // toujours pas OÙ sont les autres : seulement qu'ils ne sont pas ici,
          // ce que le regardeur voit de ses yeux.
          // `places` : la maisonnée du château où l'on se tient, salle par
          // salle — de quoi poser un visage sur le plan. Ce n'est pas une
          // trahison du brouillard : ce sont ses propres gens, dans ses propres
          // murs, dont l'office dit l'endroit. Les personnages des AUTRES
          // joueurs en restent exclus tant qu'ils ne sont pas sous vos yeux :
          // savoir où se tient sa maîtresse de la voix ne se lit pas sur un plan.
          const autresJoueurs = new Set((roster() || [])
            .map((s) => s.personnage_id).filter((id) => id && id !== moi));
          const places = {};
          Object.keys(presence).forEach((id) => {
            // La régie voit aussi les autres joueurs, où qu'ils soient : c'est
            // le seul siège à qui l'on ne cache rien, et c'est sa définition.
            if (!enRegie && autresJoueurs.has(id) && !meme(presence[id], mien)) return;
            places[id] = {
              nom: noms[id] || id,
              titre: titres[id] || "",
              salle: presence[id].salle || null,
              lieu: presence[id].lieu || null,
              // un homme en marche n'est chez personne, pas même chez celui
              // dont il vient de franchir la porte
              ici: !presence[id].marche && meme(presence[id], mien),
              marche: presence[id].marche || null,
            };
          });
          return envoyer(res, 200, JSON.stringify({
            connue: true, salle: mien.salle || null, lieu: mien.lieu || null, avec,
            places,
            connus: connus.length ? connus : Object.keys(presence) }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ connue: false, avec: [] }));
        }
      }
      if (url === "/jeu.css") return fichierStatique(res, "jeu.css", "text/css; charset=utf-8");
      // banc d'essai des voix : ne consomme pas le flux, donc ne double personne
      if (url === "/essai-voix") return fichierStatique(res, "essai-voix.html", "text/html; charset=utf-8");
      if (url === "/essai-son") return fichierStatique(res, "essai-son.html", "text/html; charset=utf-8");
      // La vue de débug de la couche du corps (`modules/survival-stack/`) : un
      // combat d'essai à gauche, le journal complet à droite. Elle ne touche à
      // RIEN — ni état, ni flux, ni horloge : c'est un banc, pas une partie.
      if (url === "/bataille") return fichierStatique(res, "bataille.html", "text/html; charset=utf-8");
      // Ce sur quoi le banc est fondé : les dossiers de recherche entiers, lus
      // à chaque appel dans `docs/recherche/*.md`. Lecture seule, hors partie —
      // le banc ne touche à rien et celle-ci non plus.
      if (url === "/recherche") {
        try { return envoyer(res, 200, JSON.stringify({ dossiers: dossiersRecherche() })); }
        catch (e) { return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) })); }
      }
      // Un module, ou un module d'une famille : `/modules/monde/relief.js`. Un
      // seul cran de sous-dossier, et rien qui ressemble à un chemin remontant.
      //
      // LA FEUILLE DE STYLE PASSE PAR ICI AUSSI. Une page qui sort son style en
      // fichier — `bataille.html` l'a fait — se retrouvait servie sans style et
      // sans que rien ne le dise ailleurs que dans la console : la page
      // s'affichait, illisible, et l'on cherchait le défaut dans le CSS.
      const m = url.match(/^\/modules\/(?:([a-z0-9_-]+)\/)?([a-z0-9_-]+\.(js|css))$/);
      if (m) return fichierStatique(res,
        m[1] ? path.join("modules", m[1], m[2]) : path.join("modules", m[2]),
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
      if (url.startsWith("/chemin")) {
        try {
          // `url` est déjà rincé de sa requête en tête de routeur : on relit
          // celle de `req.url`, la seule qui la porte encore.
          const q = new URLSearchParams((req.url.split("?")[1]) || "");
          const pt = (s) => (s || "").split(",").map(Number);
          const [ax, ay] = pt(q.get("de")), [bx, by] = pt(q.get("vers"));
          if (![ax, ay, bx, by].every((v) => isFinite(v)))
            return envoyer(res, 400, JSON.stringify({ erreur: "de/vers" }));
          const lieu = q.get("lieu") || LIEU3D_DEFAUT;
          const g = graphePieton(lieu);
          // LE BUT EST UNE PORTE QUAND ON A CLIQUÉ SUR UNE MAISON. Voir
          // `butProche` : c'est là qu'est la règle, et c'est elle qui rend un
          // clic précis sans obliger le joueur à viser au mètre.
          const cible = butProche(lieu, bx, by);
          const [vx, vy] = cible ? [cible.x, cible.y] : [bx, by];
          const a = noeudProche(g, ax, ay), b = noeudProche(g, vx, vy);
          const r = (a < 0 || b < 0) ? null : cheminPieton(g, a, b);
          if (!r) return envoyer(res, 200, JSON.stringify({ chemin: null }));
          const points = r.route.map((i) => [g.xs[i], g.ys[i]]);
          // Les deux bouts sont RACCROCHÉS, pas confondus : on marche du point
          // cliqué jusqu'à la rue, et de la rue jusqu'au but. Sans ces deux
          // segments, la marque saute au premier carrefour venu.
          points.unshift([ax, ay]);
          points.push([vx, vy]);
          let m = 0;
          for (let i = 1; i < points.length; i++)
            m += Math.hypot(points[i][0] - points[i - 1][0],
                            points[i][1] - points[i - 1][1]);
          // CE QU'ON ANNONCE EST CE QU'ON A VISÉ. Le repère le plus proche
          // reste rendu — il situe dans la ville —, mais il ne fait plus office
          // de destination : quand on a cliqué une maison, c'est elle le but,
          // avec son métier et son quartier. Un nommé de la partie
          // (`corps.json`) l'emporte sur son métier : on ne va pas « chez un
          // charpentier » quand on va chez Marlo.
          let nomme = null;
          if (cible) {
            try {
              const aff = JSON.parse(fs.readFileSync(
                path.join(RACINE, "etat", "corps.json"), "utf-8")).affectations || {};
              for (const cle in aff)
                if (aff[cle] && aff[cle].bat === cible.bat)
                  { nomme = { cle, nom: aff[cle].nom || cle }; break; }
            } catch (e) { nomme = null; }
          }
          return envoyer(res, 200, JSON.stringify({
            chemin: { points, metres: Math.round(m),
                      minutes: Math.round(r.minutes * 10) / 10 },
            vers: repereProche(lieu, vx, vy),
            but: cible ? Object.assign({}, cible, {
              nom: nomme ? nomme.nom : null, cle: nomme ? nomme.cle : null,
            }) : null,
          }));
        } catch (e) {
          return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) }));
        }
      }
      if (url.startsWith("/monde/")) return serviceMonde(req, res, url.slice("/monde/".length));
      // L'album de la partie : les planches et le moment que chacune fixe.
      // Hors état de jeu — on n'y lit rien, on s'en souvient.
      if (url === "/retrospective") {
        try {
          const t = JSON.parse(fs.readFileSync(
            path.join(RACINE, "etat", "retrospective.json"), "utf-8"));
          return envoyer(res, 200, JSON.stringify({ planches: t.planches || [] }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ planches: [] }));
        }
      }
      // Le cabinet des médailles : les rubans décernés en Coulisses. Hors
      // univers de bout en bout — aucun PNJ n'en a jamais entendu parler.
      if (url === "/medailles") {
        try {
          const t = JSON.parse(fs.readFileSync(
            path.join(RACINE, "etat", "medailles.json"), "utf-8"));
          return envoyer(res, 200, JSON.stringify({ medailles: t.medailles || [] }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ medailles: [] }));
        }
      }
      // Les images des planches. `basename` d'abord : un nom de fichier ne
      // remonte jamais d'un cran, quoi qu'il porte.
      if (url.startsWith("/captures/")) {
        const nom = path.basename(decodeURIComponent(url.slice("/captures/".length)));
        const ext = path.extname(nom).toLowerCase();
        const types = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };
        if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
        try {
          const corps = fs.readFileSync(path.join(RACINE, "captures", nom));
          return envoyer(res, 200, corps, types[ext]);
        } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
      }
      // Les textures du décor 3D. Même garde que les planches : `basename`
      // d'abord, un nom de fichier ne remonte jamais d'un cran. Elles changent
      // une ou deux fois par an — on les laisse en cache une journée, sinon
      // chaque rechargement de la page les retire du réseau pour rien.
      if (url.startsWith("/textures/")) {
        const nom = path.basename(decodeURIComponent(url.slice("/textures/".length)));
        const ext = path.extname(nom).toLowerCase();
        const types = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp" };
        if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
        try {
          const corps = fs.readFileSync(path.join(RACINE, "ecrans", "textures", nom));
          res.writeHead(200, { "Content-Type": types[ext], "Cache-Control": "public, max-age=86400" });
          return res.end(corps);
        } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
      }
      // Les cris. Les seuls fichiers sonores du jeu : tout le reste du son de
      // bataille est synthétisé dans `ecrans/modules/son.js`. Ils vivent hors
      // d'`ecrans/` parce qu'ils ne sont pas un écran — d'où la racine à part.
      // Même garde que les planches (`basename`, un nom ne remonte jamais d'un
      // cran), et le même cache d'une journée : ils ne changent jamais.
      if (url.startsWith("/sons/cris/")) {
        const nom = path.basename(decodeURIComponent(url.slice("/sons/cris/".length)));
        const ext = path.extname(nom).toLowerCase();
        const types = { ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
                        ".json": "application/json; charset=utf-8" };
        if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
        try {
          const corps = fs.readFileSync(path.join(RACINE, "sons", "cris", nom));
          res.writeHead(200, { "Content-Type": types[ext], "Cache-Control": "public, max-age=86400" });
          return res.end(corps);
        } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
      }
      // Les vues de salle. Une salle du plan peut avoir sa toile dans
      // `ecrans/salles/<id de la salle>.jpg` — l'id est celui de `plans.js`.
      // Le fil la pose au changement de salle, et SEULEMENT si elle existe :
      // d'où le manifeste ci-dessous, servi une fois au chargement. Sans lui,
      // la page devrait tenter l'image et la retirer sur erreur, ce qui la
      // ferait clignoter à chaque salle qui n'en a pas — c'est-à-dire presque
      // toutes. Rien à declarer nulle part : deposer le fichier suffit.
      if (url === "/salles") {
        try {
          const dossier = path.join(RACINE, "ecrans", "salles");
          const ids = fs.readdirSync(dossier)
            .filter((n) => /\.(jpg|jpeg|png|webp)$/i.test(n))
            .map((n) => n.replace(/\.[^.]+$/, ""));
          return envoyer(res, 200, JSON.stringify({ salles: ids }));
        } catch (e) { return envoyer(res, 200, JSON.stringify({ salles: [] })); }
      }
      if (url.startsWith("/salles/")) {
        const nom = path.basename(decodeURIComponent(url.slice("/salles/".length)));
        const ext = path.extname(nom).toLowerCase();
        const types = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp" };
        if (!types[ext]) return envoyer(res, 404, JSON.stringify({ erreur: nom }));
        try {
          const corps = fs.readFileSync(path.join(RACINE, "ecrans", "salles", nom));
          res.writeHead(200, { "Content-Type": types[ext], "Cache-Control": "public, max-age=86400" });
          return res.end(corps);
        } catch (e) { return envoyer(res, 404, JSON.stringify({ erreur: nom })); }
      }
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
          // Qui porte la couronne du « joueur » sur CET ecran : celui qui
          // regarde, pas celui du journal. A deux, le journal designe Rhaenyra —
          // l'ecran d'Aurore marquait donc la reine comme le personnage joue.
          const siege = qui(req, url);
          let joueur_id = (siege && siege.personnage_id) || null;
          if (!joueur_id) {
            try { joueur_id = lire("journal.json").personnage_joueur_id || null; } catch (e) {}
          }
          const gens = lire("personnages.json")
            .filter((p) => p.etat !== "mort")
            .map((p) => {
              const m = maisons[p.maison_id] || null;
              // Tout le monde a un rond : faute de portrait dessiné, la
              // silhouette anonyme tient la place.
              let portrait_svg = "";
              const f = p.portrait && p.portrait.fichier;
              if (f) {
                try { portrait_svg = fs.readFileSync(path.join(RACINE, f), "utf-8"); } catch (e) {}
              }
              // LE CHAMP `portrait.fichier` N'EST PAS UNE CONDITION D'EXISTENCE.
              // Il manquait à une bonne part des fiches, et ces gens-là gardaient
              // la silhouette anonyme alors que leur médaillon était peint et
              // posé sur le disque — un manque invisible, puisque rien n'échoue.
              // `medaillons.py` écrit toujours `ecrans/portraits/<id>.svg` : cet
              // id EST l'adresse. On la tente donc quand le champ ne dit rien,
              // et peindre un visage suffit désormais à le faire paraître.
              if (!portrait_svg) portrait_svg = portraitFrais(p.id) || "";
              if (!portrait_svg) portrait_svg = portraitDefaut(p.nom || p.id);
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
          const siege = qui(req, url);
          // Le monde commun se lit à la racine ; ce que le demandeur CROIT se
          // lit dans son dossier quand il en a un.
          const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
          const lireSien = (f, defaut) => lireCroyance(f, siege, defaut);
          const maisons = {};
          lire("maisons.json").forEach((m) => (maisons[m.id] = m));
          const lieux = lire("lieux.json").map((l) => ({
            // `alias` part avec le reste : la couche carte a ses propres ids, et
            // sans le pont le registre affiche « repaire-aux-corneilles » là où
            // il faut lire « Repos-des-Freux ».
            id: l.id, nom: l.nom, type: l.type, alias: l.alias || [],
            controle_id: l.controle_id,
            allegeance: (maisons[l.controle_id] || {}).allegeance_affichee || "neutre",
          }));
          let joueur_lieu_id = null, date = null, joueur_id_carte = null;
          try {
            // Sur QUI la carte se centre, et quelle tête elle tait. À deux, ce
            // n'est pas le personnage-joueur du journal : c'est celui qui
            // regarde. Une carte centrée sur Peyredragon quand on est ailleurs
            // est une carte qui ment sur l'endroit d'où l'on parle.
            const journal = lire("journal.json");
            const moi = regardeur(siege, journal);
            const pj = lire("personnages.json").find((p) => p.id === moi);
            if (pj) { joueur_lieu_id = pj.lieu_id || null; joueur_id_carte = pj.id; }
          } catch (e) {}
          date = dateDe(siege);
          // Ce que la table PORTE : osts, flottes, marches, sièges, serments.
          // Ce fichier n'est PAS la vérité du monde — c'est ce que le joueur
          // croit tenir, avec sa `certitude`. Absent = table nue.
          let jetons = [], traits = [], zones = [];
          try {
            const t = lireSien("jetons.json", { jetons: [], traits: [] });
            const vif = (m) => !m.statut || m.statut === "actif";
            jetons = (t.jetons || []).filter(vif);
            traits = (t.traits || []).filter(vif);
            zones = t.zones || [];
            // L'âge d'un pli est de l'arithmétique, pas une note que le MJ
            // retape à chaque battement : il porte la date de son départ, le
            // serveur compte les jours contre la date du monde. C'est ce
            // compte-là qui rend un silence lisible — « muet depuis neuf
            // jours » n'est pas la même chose que « muet depuis hier ».
            const jourNow = jourAbsolu(date);
            const compter = (m) => {
              if (!m) return;
              // Ce qui a eu lieu compte les jours ÉCOULÉS ; un dessein compte
              // ceux qui RESTENT. Les deux se calculent ici pour la même raison :
              // le MJ ne doit pas retaper un chiffre à chaque battement.
              if (m.jours == null && m.date) {
                const parti = jourAbsolu(m.date);
                if (parti != null && jourNow != null) m.jours = Math.max(0, jourNow - parti);
              }
              if (m.dans == null && m.echeance) {
                const du = jourAbsolu(m.echeance);
                if (du != null && jourNow != null) m.dans = du - jourNow;
              }
            };
            jetons.concat(traits).forEach((m) => {
              compter(m);
              // Un incident porte ses relais DANS lui : chacun a sa propre date
              // d'arrivée, donc son propre compte de jours. C'est la colonne de
              // chiffres qui dit à quelle vitesse la chose gagne.
              ["propage", "risque"].forEach((k) => {
                if (Array.isArray(m[k])) m[k].forEach((r) => compter(r));
              });
            });
            // Les oreilles : une oreille n'a pas d'état qu'on retape, elle a
            // un DERNIER MOT et une date. Le serveur en tire les deux choses
            // qui se lisent sur la table — depuis combien de jours elle n'a
            // rien dit, et à quel point on peut encore s'y fier.
            //
            // Le MJ n'écrit que les deux états qu'un calcul ne saurait pas
            // deviner : `nouee` (elle n'a rien donné encore) et `perdu` (on
            // SAIT qu'elle est tombée). Le reste se dérive : elle parle, ou
            // elle s'est tue. Il n'existe pas d'état « retournée » — si la
            // reine le savait, elle la couperait ; c'est le silence qui porte
            // le doute, et le silence ne dit jamais lequel des trois c'est.
            const MUETTE_APRES = 3;
            jetons.forEach((j) => {
              if (j.genre !== "oreille") return;
              if (j.etat !== "nouee" && j.etat !== "perdu") {
                j.etat = (j.jours != null && j.jours > MUETTE_APRES)
                  ? "muette" : "parle";
              }
              // Elle pâlit comme une tête — mais elle ne SORT jamais de la
              // table. Une oreille qu'on n'entend plus depuis deux lunes est
              // précisément ce qu'il faut voir : la faire disparaître comme
              // une position périmée reviendrait à cacher le trou.
              if (j.jours != null && j.etat !== "nouee") {
                j.certitude = vieillir(j.certitude || "sure", j.jours) || "rumeur";
              }
            });
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
            (lireSien("vues.json", { vues: [] }).vues || []).forEach((v) => {
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
            JSON.stringify({ lieux, joueur_lieu_id, joueur_id: joueur_id_carte,
                             date, jetons, traits, zones }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ lieux: [], erreur: String(e) }));
        }
      }
      // La ville : l'échelle intermédiaire — hors les murs, mais pas le royaume.
      // Même contrat que le terrain : fichier absent ou sans `id` = pas de
      // bascule pour y aller.
      // Une ville par lieu quand le fichier existe : `etat/villes/<lieu>.json`
      // est lu d'abord, `etat/ville.json` ensuite. Strictement additif — tant
      // qu'aucun fichier ne porte le nom du lieu où se tient le joueur, on sert
      // exactement ce qu'on servait avant. C'est ce qui permet de préparer une
      // ville où l'on n'est pas encore sans toucher à celle où l'on est.
      if (url === "/ville") {
        try {
          let ou = null;
          try {
            const siege = qui(req, url);
            const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
            const journal = lire("journal.json");
            const moi = regardeur(siege, journal);
            const pj = lire("personnages.json").find((p) => p.id === moi);
            if (pj) ou = pj.lieu_id || null;
          } catch (e) {}
          // UN JOUEUR DONT ON IGNORE LA POSITION N'HÉRITE D'AUCUNE CARTE.
          // Le repli sur `etat/ville.json` ne valait que pour une partie seule,
          // où il n'y a qu'un lieu possible. À deux sièges il fuit : un homme
          // du Crochet sans `lieu_id` recevait l'île de Peyredragon — la
          // garnison de la reine, ses nefs, ses têtes. C'est la même règle que
          // `lireCroyance` applique déjà aux jetons et aux vues : sans siège
          // identifié, rien.
          if (!ou) return envoyer(res, 200, JSON.stringify({ champ: null }));
          const fichiers = [];
          // un id de lieu est du kebab-case ; on refuse tout le reste, sinon
          // `..` dans un lieu_id ouvrirait le disque entier.
          if (/^[a-z0-9-]+$/.test(ou)) {
            fichiers.push(path.join(RACINE, "etat", "villes", ou + ".json"));
          }
          fichiers.push(path.join(RACINE, "etat", "ville.json"));
          for (const f of fichiers) {
            if (!fs.existsSync(f)) continue;
            const champ = JSON.parse(fs.readFileSync(f, "utf-8"));
            if (!champ || !champ.id) continue;
            // Une ville qui nomme un autre lieu que celui où l'on est n'est pas
            // la nôtre : mieux vaut pas d'échelle qu'une échelle qui ment.
            if (ou && champ.lieu_id && champ.lieu_id !== ou) continue;
            return envoyer(res, 200, JSON.stringify({ champ }));
          }
          return envoyer(res, 200, JSON.stringify({ champ: null }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ champ: null }));
        }
      }
      // Les livres : des objets posés dans les salles — un registre, un livre
      // de comptes, un rôle d'équipage. Chacun porte du JSON qu'on consulte à
      // la main.
      //
      // On les servait TOUS, en laissant à la page le soin de n'en montrer que
      // ce qui est à portée. À un joueur, c'était une commodité ; à trois
      // sièges, c'est une fuite : le carnet privé de la reine, celui de Marlo
      // et tout ce qui traîne à Port-Réal partaient sur le fil d'Aurore, où
      // l'on n'a qu'à ouvrir la console pour les lire. Le brouillard ne se
      // tient pas dans l'affichage, il se tient à la porte — donc ici.
      //
      // Trois coupes, et pas une de plus (la salle, elle, reste à la page : un
      // registre de maison se consulte de tout le château) :
      //   — un carnet `prive` n'est qu'à son porteur ;
      //   — un volume à `lecteurs` n'est qu'à ceux qui y sont nommés ;
      //   — ce qui est posé ou porté dans un AUTRE château ne descend pas.
      //
      // Et l'étagère se FERME à qui n'a pas de siège. Le repli sur le
      // personnage-joueur du journal est bon quand on joue seul ; dès qu'il y a
      // un roster, il veut dire qu'une URL nue — un lien de tunnel qui traîne,
      // un cookie perdu — ouvre le carnet de la reine. On rend alors la liste
      // vide et l'on dit pourquoi (`siege: false`), plutôt que de laisser la
      // page annoncer qu'il n'y a rien à lire.
      if (url === "/books") {
        try {
          const tous = bibliotheque.charger(RACINE);
          const moi = monPersonnage(req, url);
          if (!moi && roster()) {
            return envoyer(res, 200, JSON.stringify({ books: [], boites: [], siege: false }));
          }
          const { liste, boites } = volumesVisibles(tous, moi);
          liste.forEach((b) => (b.pages || []).forEach(inlinerFigure));
          // On ne descend que les coffrets dont il reste quelque chose à
          // ouvrir : une boîte vide sur l'étagère est un onglet qui ment.
          const gardees = new Set(liste.map((b) => b.boite).filter(Boolean));
          return envoyer(res, 200, JSON.stringify({
            books: liste, boites: boites.filter((c) => gardees.has(c.id)) }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ books: [], boites: [] }));
        }
      }
      // Les notes du joueur : le seul volume de l'étagère qui ne soit pas du
      // monde. On le rend tel quel, sans rien en interpréter — c'est du texte,
      // pas du JSON, et ce que le joueur y a mis lui appartient.
      if (url === "/notes") {
        try {
          const p = cheminNotes(qui(req, url));
          const texte = fs.existsSync(p) ? fs.readFileSync(p, "utf-8") : "";
          return envoyer(res, 200, JSON.stringify({ texte }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ texte: "" }));
        }
      }
      // LA NAPPE. Les pièces de bois posées sur la table peinte : ce que le
      // conseil a disposé de ses mains. Ce n'est pas une croyance et ce n'est
      // pas un livre — c'est un MEUBLE, partagé par tous ceux qui entrent dans
      // la salle. D'où un seul fichier, et non un par siège : deux personnes
      // penchées sur la même table voient les mêmes pièces, sinon ce n'est plus
      // une table, ce sont deux tables qui se ressemblent.
      if (url === "/nappe") {
        try {
          const f = path.join(RACINE, "etat", "nappe.json");
          const d = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf-8")) : {};
          return envoyer(res, 200, JSON.stringify({ pieces: d.pieces || [] }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ pieces: [] }));
        }
      }
      // Les plis : ce qui est parti par écrit, et où ça en est. Le décor s'en
      // sert pour montrer un corbeau qui se lâche et un cavalier qui franchit
      // la porte — la table de guerre, elle, en tire ses jetons `pli`. On sert
      // le tout et l'on résout ce que le client ne peut pas résoudre seul :
      // `de` est un PERSONNAGE, et c'est son lieu du moment qui dit d'où le
      // pli est parti. Sans ça la page devrait charger tout `personnages.json`
      // pour lâcher un oiseau.
      if (url === "/plis") {
        try {
          const f = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "plis.json"), "utf-8"));
          const plis = Array.isArray(f.plis) ? f.plis : [];
          const gens = {};
          try {
            const pj = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "personnages.json"), "utf-8"));
            const liste = Array.isArray(pj) ? pj : (pj.personnages || []);
            for (const p of liste) if (p && p.id) gens[p.id] = p.lieu_id || null;
          } catch (e) { /* sans les gens, `de_lieu` reste nul : le client s'en passe */ }
          return envoyer(res, 200, JSON.stringify({
            plis: plis.map((p) => Object.assign({}, p, {
              de_lieu: gens[p.de] || (p.de || null),
            })),
          }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ plis: [] }));
        }
      }
      if (url === "/terrain") {
        // Le champ, quand il y en a un : la troisième échelle du décor. Absent
        // ou vide = pas de terrain, et pas de bascule pour y aller.
        // Un terrain par lieu, même contrat que la ville : `etat/terrains/<lieu>.json`
        // est lu d'abord, `etat/terrain.json` ensuite. Strictement additif — tant
        // qu'aucun fichier ne porte le nom du lieu où se tient le joueur, on sert
        // exactement ce qu'on servait avant. C'est ce qui permet de tenir le champ
        // d'une ville où l'on n'est pas encore sans toucher à celui où l'on est —
        // et, à deux sièges dans deux lieux, de ne pas se marcher dessus.
        try {
          let ou = null;
          try {
            const siege = qui(req, url);
            const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
            const journal = lire("journal.json");
            const moi = regardeur(siege, journal);
            const pj = lire("personnages.json").find((p) => p.id === moi);
            if (pj) ou = pj.lieu_id || null;
          } catch (e) {}
          const fichiers = [];
          // un id de lieu est du kebab-case ; on refuse tout le reste, sinon
          // `..` dans un lieu_id ouvrirait le disque entier.
          if (ou && /^[a-z0-9-]+$/.test(ou)) {
            fichiers.push(path.join(RACINE, "etat", "terrains", ou + ".json"));
          }
          fichiers.push(path.join(RACINE, "etat", "terrain.json"));
          for (const f of fichiers) {
            if (!fs.existsSync(f)) continue;
            const champ = JSON.parse(fs.readFileSync(f, "utf-8"));
            if (!champ || !champ.id) continue;
            // Un champ qui nomme un autre lieu que celui où l'on est n'est pas
            // le nôtre : mieux vaut pas d'échelle qu'une échelle qui ment.
            if (ou && champ.lieu_id && champ.lieu_id !== ou) continue;
            return envoyer(res, 200, JSON.stringify({ champ }));
          }
          return envoyer(res, 200, JSON.stringify({ champ: null }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ champ: null }));
        }
      }
      // L'échiquier : les affaires du conseil, de ce qu'on a jusqu'à ce qu'on
      // veut. RIEN N'EST ÉCRIT À LA MAIN ICI — tout est DÉRIVÉ des six registres
      // par type de `etat/books.json` (`plan-etats-cibles`, `plan-verrous`,
      // `plan-clefs`, `plan-actions`, `plan-moyens`, `plan-offices`), qui sont
      // l'unité de rangement de la maison. Le guide des affaires tranche le cas
      // où les deux divergeraient : « quand les deux se contredisent, c'est le
      // registre qui a raison ». Une vue qui recopierait le plan dans un fichier
      // à part serait un mensonge en attente — il n'y a donc plus de fichier.
      //
      // La chaîne est celle du livre, et l'échiquier l'épouse de bas en haut :
      // moyens et offices, actions, clefs, verrous, états cibles. Un PLATEAU est
      // une affaire.
      //
      // LES ÉTATS CIBLES NE SONT PAS UNE RANGÉE, C'EST UN ARBRE. La colonne
      // `⬆️ Sert` du registre pointe vers l'état AMONT — « 200 sert 100 » —, et
      // les douze états de la Prise de Port-Réal sont en réalité un arbre de
      // quatre niveaux sous une seule racine. Les étaler à plat était un
      // contresens autant qu'un problème de place.
      //
      // Une COLONNE s'ouvre donc sous un état qui porte des verrous, et sous une
      // feuille qui n'en porte aucun — pour qu'une feuille rompue reste comptée.
      // Un état intermédiaire sans verrou ne prend pas de colonne : il COIFFE
      // celles de ses enfants, et sa portée est l'étendue de son sous-arbre.
      //
      // Ce que le serveur dérive et que personne n'écrit : l'arbre, la descente
      // (ce qui pend sous chaque état), la remontée — l'épreuve du guide, « une
      // action qui ne remonte à aucun état cible est une occupation » —, les
      // brèches d'un état (un verrou pour lequel une clef est RETENUE), et les
      // fautes : une pièce sans preuve, une action sans office, un moyen cité
      // qui n'est à aucun registre, une référence qui ne résout pas.
      if (url === "/echiquier") {
        try {
          // ON NE LIT QUE CE QUE CE SIÈGE PEUT OUVRIR. Le damier servait
          // `books.json` en entier : Marlo, à Port-Réal, y trouvait les
          // quarante-deux plateaux du conseil de Peyredragon et pas un des
          // siens. Même tri que l'étagère, et pour la même raison — un plateau
          // qu'on ne peut pas ouvrir dans les livres est un plan qui n'est pas
          // le sien.
          const brut = bibliotheque.charger(RACINE);
          const moi = monPersonnage(req, url);
          if (!moi && roster()) {
            return envoyer(res, 200, JSON.stringify({ affaires: [] }));
          }
          const porteePlan = planModele(moi);
          const idsVisibles = new Set(porteePlan.volumes_ids || []);
          const idsActifs = new Set(porteePlan.affaires_ids || []);
          const livres = (Array.isArray(brut) ? brut : [])
            .filter((l) => l && idsVisibles.has(l.id));
          const parId = {};
          livres.forEach((l) => { if (l && l.id) parId[l.id] = l; });
          // Une cellule de numéro porte son gras de registre : on ne garde que
          // l'adresse. « **M01** » vaut M01, et une adresse ne se renumérote
          // jamais — c'est une adresse, pas un rang.
          const adresse = (c) => String(c == null ? "" : c).replace(/[*\s]/g, "");
          const adresses = (c) => (String(c == null ? "" : c).match(/[MO]?\d+/g) || []);
          const propre = (c) => String(c == null ? "" : c).replace(/\*\*/g, "").trim();
          // Le libellé d'une pièce commence par le signe que le registre lui a
          // donné : on l'ôte du nom, parce que le plateau montre le signe du
          // RANG et l'encart le nom en clair.
          const sansSigne = (c) => propre(c).replace(
            /^(?:[←-⯿☀-➿️‍⃣]|[\uD83C-\uD83E][\uDC00-\uDFFF])+\s*/, "");
          const rien = (c) => { const t = sansSigne(c); return !t || t === "—" || t === "-"; };
          const sansAccent = (s) => String(s == null ? "" : s)
            .normalize("NFD").replace(/[̀-ͯ]/g, "")
            .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
          const chiffre = (n) => parseInt(String(n).replace(/\D/g, ""), 10) || 0;


          // ---- LA SOURCE, ET ELLE A CHANGÉ : LES CAHIERS ----------------------
          // Il y avait deux plans dans `books.json`, et cette vue lisait le petit.
          // Les six registres par type comptent 156 lignes ; les cahiers
          // d'affaire, qui portent chacun leurs propres tables 🎯 🔒 🗝️ ⚔️, en
          // comptent 1164 — dont 580 actions contre 60. La plupart des affaires
          // les plus travaillées n'avaient pas une ligne au registre, et le
          // plateau montrait donc un plan qui n'était plus celui du conseil.
          //
          // Le guide le disait déjà : « l'affaire est l'unité de TRAVAIL, les six
          // registres par type sont l'unité de RANGEMENT ». Le travail est dans
          // les cahiers ; l'index a décroché. On lit donc les cahiers.
          //
          // UN CAHIER = UNE AFFAIRE = UN PLATEAU, et le gain est plus grand que
          // le compte : l'appariement par NOM disparaît. Le volume EST l'affaire
          // — son titre, son emblème, son lien, sa main —, là où l'on rapprochait
          // deux chaînes de caractères et où l'on perdait « L'entrée sans
          // bataille » en chemin.
          //
          // LES COLONNES SE TROUVENT PAR LEUR EN-TÊTE, jamais par leur rang : un
          // cahier écrit « Le prix » et « Ce que cela ferme » là où le registre a
          // une seule colonne de coût, et l'un d'eux n'a pas de colonne « Où ».
          // Ce qu'un cahier n'écrit pas, on ne l'invente pas : la case reste vide
          // et la conclusion en tient compte.
          const CANON = {
            etat: [["l etat"], ["ce qui doit etre vrai"], ["ou"], ["la preuve"],
                   ["sert"], ["affaire"]],
            verrou: [["le verrou"], ["bloque"], ["ce qui est vrai"], ["la preuve"],
                     ["leve quand"]],
            clef: [["la clef"], ["ouvre"], ["le principe"],
                   ["le prix", "ce qu elle coute"], ["la preuve"],
                   ["decision", "retenue"]],
            // `depend de` est la HUITIÈME, et elle n'était lue par personne.
            // C'est pourtant la seule colonne du plan qui porte le lien
            // `attend` — 397 actions sur 611 y écrivent un numéro, dont 71
            // pointent hors du cahier. Sans elle, la moitié des arêtes qui
            // sortent d'une affaire n'existe pas pour l'écran.
            action: [["l action"], ["realise"], ["ce qu on fait"], ["office"],
                     ["moyens"], ["la preuve"], ["ou ca en est", "etat"],
                     ["depend de"]],
          };
          const TITRE = { etat: "etats cibles", verrou: "verrous",
                          clef: "clefs", action: "actions" };
          const quelleColonne = (cols, choix) => {
            let i = -1;
            choix.some((m) => { i = cols.indexOf(m); return i >= 0; });
            if (i >= 0) return i;
            choix.some((m) => { i = cols.findIndex((c) => c.indexOf(m) === 0); return i >= 0; });
            return i;
          };
          // Une ligne de cahier ou de registre, rendue à la forme que tout le
          // reste de cette route attend. Une colonne absente donne une case vide.
          const normaliser = (t, genre) => {
            const cols = ((t && t.colonnes) || []).map(sansAccent);
            const rangs = CANON[genre].map((choix) => quelleColonne(cols, choix));
            return ((t && t.lignes) || []).map((l) => {
              const c = Array.isArray(l) ? l : (l && l.cellules);
              if (!Array.isArray(c) || !c.length) return null;
              return { c: [adresse(c[0])].concat(rangs.map((i) => (i >= 0 ? c[i] : ""))),
                       num: adresse(c[0]) };
            }).filter((x) => x && x.num);
          };
          // Le titre d'une table porte parfois une suite après un tiret cadratin
          // (« Ouverture de l'Affaire — forme neuve du 26e au soir ») : on
          // apparie sur son début, jamais sur l'égalité.
          const tablesDe = (v, genre) => (v.tables || []).filter((t) => {
            const titreTable = sansAccent(String((t && t.titre) || "").split("\u2014")[0]);
            return (" " + titreTable + " ").indexOf(" " + TITRE[genre] + " ") >= 0;
          });

          const etats = [], verrous = [], clefs = [], actions = [];
          const bacs = { etat: etats, verrou: verrous, clef: clefs, action: actions };
          const groupes = [];
          // UN CAHIER D'AFFAIRE SE RECONNAÎT À SA FORME, PAS À SON NOM. La
          // règle était « un id qui commence par `affaire-` », et elle tenait
          // tant qu'une seule maison écrivait des affaires. La Néra tient les
          // siennes sous `nera-*`, au même gabarit, ouverture comprise : le
          // damier les ignorait toutes les sept. Un volume qui porte
          // l'ouverture de l'affaire EST une affaire, où qu'il soit rangé et
          // quel que soit son id — et la table des états cibles reste exigée,
          // sans quoi il n'y a pas de plateau à dessiner.
          const brouillons = porteePlan.brouillons || [];
          livres.filter((l) => idsActifs.has(l.id)).forEach((v) => {
            // `ecrites` : TOUTES les adresses que le cahier porte à ses quatre
            // tables, qu'elles atteignent le damier ou non. Ce n'est pas la
            // même chose que les pièces tracées, et l'écart est le sujet —
            // 130 lignes sur 1182 réalisent une clef qui n'existe pas, ou
            // pendent sous un état sans colonne. Le plateau a raison de ne pas
            // les dessiner ; un conseiller a le droit de les citer quand même,
            // et un renvoi vers l'une d'elles ne doit pas devenir du texte nu.
            const g = { titre: sansSigne(v.titre || v.id), volume: v, etats: [],
                        ecrites: [] };
            Object.keys(bacs).forEach((genre) => {
              tablesDe(v, genre).forEach((t) => normaliser(t, genre).forEach((r) => {
                // DE QUEL CAHIER SORT CETTE LIGNE. Les quatre bacs sont
                // GLOBAUX — un verrou d'un autre cahier tombe déjà dans notre
                // colonne s'il bloque notre état —, et rien ne disait d'où
                // venait une ligne. Sans cette marque, on ne peut pas
                // distinguer une arête qui reste chez nous d'une arête qui sort.
                r.aff = g.titre;
                if (genre === "etat") { r.c[6] = g.titre; g.etats.push(r); }
                if (/^\d{4,6}$/.test(String(r.num)) && g.ecrites.indexOf(r.num) < 0) {
                  g.ecrites.push(r.num);
                }
                bacs[genre].push(r);
              }));
            });
            if (g.etats.length) groupes.push(g);
          });

          // ---- LES MOYENS ET LES OFFICES, D'OÙ QU'ILS VIENNENT ---------------
          // Ils étaient lus à deux ids fixes — `plan-moyens` et `plan-offices`,
          // les registres du Grand Plan de la reine. Une maison qui tient son
          // propre plan écrit les siens dans les TABLES d'un cahier
          // (`nera-moyens` porte les deux), et le damier lui rendait alors
          // toutes ses actions sans office et tous ses moyens inconnus. On
          // récolte donc par la FORME, dans tout ce que ce siège peut ouvrir :
          // une table qui porte une colonne « Le moyen » est un registre de
          // moyens, où qu'elle soit posée.
          //
          // LES COLONNES SE TROUVENT PAR LEUR NOM, JAMAIS PAR LEUR RANG. Le
          // registre des moyens a reçu deux colonnes de plus le jour où
          // `nos-moyens` y a été fusionné (« Ce qu'il vaut », « Ce qu'il peut
          // produire ») : lues au rang, la bulle disait « tenu par Tout ce qui
          // flotte dans la baie » et « à Corlys Velaryon ». Un registre qu'on
          // tient à la main gagne des colonnes, c'est sa vie ; une vue qui les
          // compte est une vue qui mentira un jour sans prévenir. Chaque ligne
          // emporte donc ses cases déjà résolues, et non le rang où les lire.
          const recolter = (genre) => {
            const tete = genre === "moyen" ? "le moyen" : "l office";
            const out = [];
            const prendre = (colonnes, lignes) => {
              const e = (colonnes || []).map(sansAccent);
              if (!e.some((c) => c.indexOf(tete) === 0)) return;
              const r = (mot, defaut) => {
                let i = e.indexOf(mot);
                if (i < 0) i = e.findIndex((x) => x.indexOf(mot) >= 0);
                return i >= 0 ? i : defaut;
              };
              const cases = genre === "moyen"
                ? { nom: r(tete, 1), dit: r("sait faire", 2), tient: r("qui le tient", 3),
                    ou: r("ou", 4), etat: r("etat", 5) }
                : { nom: r(tete, 1), dit: r("repond", 3), tient: r("titulaire", 2),
                    ou: -1, etat: r("decide seul", 4) };
              (lignes || []).forEach((l) => {
                const c = Array.isArray(l) ? l : (l && l.cellules);
                if (!Array.isArray(c) || !c.length) return;
                const x = { c: c, num: adresse(c[0]) };
                if (!x.num) return;
                Object.keys(cases).forEach((k) => {
                  x[k] = cases[k] >= 0 ? propre(c[cases[k]]) : "";
                });
                out.push(x);
              });
            };
            livres.forEach((v) => {
              prendre(v.colonnes, v.lignes);
              (v.tables || []).forEach((t) => prendre(t.colonnes, t.lignes));
            });
            return out;
          };
          const moyens = recolter("moyen"), offices = recolter("office");
          if (!groupes.length) return envoyer(res, 200, JSON.stringify({ affaires: [], brouillons }));

          const indexe = (t) => { const o = {}; t.forEach((x) => { o[x.num] = x; }); return o; };
          const iV = indexe(verrous), iM = indexe(moyens), iO = indexe(offices);
          // Un moyen et un office se citent par leur numéro — mais une action
          // écrite vite les nomme en toutes lettres. On rattrape le nom, et ce
          // qu'on ne rattrape pas devient une faute au lieu de disparaître.
          const parNom = (t) => {
            const o = {};
            t.forEach((x) => { o[sansAccent(sansSigne(x.nom))] = x; });
            return o;
          };
          const nM = parNom(moyens), nO = parNom(offices);
          // Les cases sont résolues à la récolte : il ne reste qu'à les lire.
          const cel = (t, genre, quoi) => (t && t[quoi]) || "";
          // Un article de tête n'est pas une différence : le registre écrit
          // « Maîtresse des nouvelles de la reine », l'action cite « la
          // maîtresse des nouvelles », et c'est le même office. Ce qui ne se
          // rattrape pas ainsi reste une faute et le montre — « à désigner »
          // n'est pas un office, et ne le deviendra pas par indulgence.
          const nu = (s) => sansAccent(s).replace(/^(?:l|le|la|les|du|de|des|d) /, "");
          const retrouver = (texte, index, noms) => {
            const code = adresses(texte).find((a) => index[a]);
            if (code) return index[code];
            const n = nu(sansSigne(texte));
            if (!n) return null;
            if (noms[n]) return noms[n];
            const cle = Object.keys(noms).find((k) => {
              const q = nu(k);
              return q && (n.indexOf(q) >= 0 || q.indexOf(n) >= 0);
            });
            return cle ? noms[cle] : null;
          };

          // Le volume de l'affaire — UN SEUL APPARIEMENT, et tout en sort : le
          // lien du clic, l'emblème que la maison lui a choisi, et la phrase qui
          // dit pourquoi l'affaire occupe le conseil. Le registre nomme
          // l'affaire en clair ; on la retrouve par son titre, et faute de titre
          // on n'invente ni lien mort ni emblème.
          const volumes = livres.filter((l) => l && String(l.id).indexOf("affaire-") === 0);
          const volumeDe = (nom) => {
            const n = sansAccent(nom);
            if (!n) return null;
            let v = volumes.find((l) => sansAccent(l.titre) === n);
            if (!v) v = volumes.find((l) => sansAccent(l.titre).indexOf(n) >= 0);
            return v || null;
          };
          // L'OBJET, au sens du guide : « une phrase, pourquoi cette affaire
          // mérite l'attention du conseil ». Les volumes l'écrivent dans leur
          // table d'ouverture, sous des intitulés voisins — on prend la ligne,
          // jamais on ne la compose. Faute d'ouverture écrite, le sous-titre du
          // volume dit déjà de quoi il traite.
          const objetDe = (v) => {
            if (!v) return null;
            const t = v.tables || [];
            for (const tb of t) {
              for (const l of (tb.lignes || [])) {
                const c = l && l.cellules;
                if (!c || !c[0]) continue;
                const tete = sansAccent(c[0]);
                if (tete.indexOf("objet") >= 0 || tete.indexOf("rend vrai") >= 0) {
                  return propre(c[1]);
                }
              }
            }
            return v.sous_titre ? propre(v.sous_titre) : null;
          };

          // ---- LE TENEUR D'UNE ACTION, ET SON VISAGE ----
          // Une action cite son office ; l'office nomme son titulaire ; le
          // titulaire est quelqu'un de `personnages.json`. La dernière jointure
          // se fait sur un nom écrit en toutes lettres — « Ser Robert Quince,
          // onze ans en charge » — donc on la fait SOBREMENT : on ne lit que la
          // tête de la cellule (avant la première virgule, le point ou le
          // tiret), on ôte les titres, et l'on n'accepte qu'une suite de mots
          // ENTIERS commune aux deux côtés. « Wend » ne devient pas « Wenda »,
          // et un office VIDE ne prend pas le visage de qui se trouve nommé
          // dans sa ligne. Mieux vaut pas de visage qu'un mauvais visage.
          let gens = [];
          try { gens = JSON.parse(fs.readFileSync(
            path.join(RACINE, "etat", "personnages.json"), "utf-8")); } catch (e) {}
          const sansTitre = (t) => {
            let x = t;
            for (let i = 0; i < 3; i++) {
              const y = x.replace(
                /^(ser|dame|messire|mestre|maitre|maitresse|lord|lady|prince|princesse|le|la|les|l) /, "");
              if (y === x) break;
              x = y;
            }
            return x;
          };
          const tete = (c) => sansTitre(sansAccent(
            String(c == null ? "" : c).replace(/\*\*/g, "").split(/[,;.(—]/)[0]));
          const VACANT = ["vide", "vacant", "a designer", "designer", "neant"];
          const suite = (a, b) => {
            if (!a.length || a.length > b.length) return false;
            for (let i = 0; i <= b.length - a.length; i++) {
              if (a.every((m, j) => m === b[i + j])) return true;
            }
            return false;
          };
          const personneDe = (texte) => {
            const t = tete(texte);
            if (!t || VACANT.some((v) => t.indexOf(v) >= 0)) return null;
            const mots = t.split(" ");
            let pris = null, long = 0;
            gens.forEach((g) => {
              if (!g || !g.nom) return;
              const n = sansAccent(g.nom);
              [n, sansTitre(n)].forEach((cle) => {
                const m = cle.split(" ");
                if ((suite(mots, m) || suite(m, mots)) && cle.length > long) {
                  pris = g; long = cle.length;
                }
              });
            });
            return pris;
          };
          // Le titulaire de l'office d'abord — c'est la chaîne du guide. À
          // défaut d'office numéroté, l'action nomme souvent la personne
          // elle-même (« Dame Aurore Inchauspé, maîtresse des nouvelles ») : on
          // la prend aussi. Ça ne lave pas la faute — aucun office ne porte
          // l'action, le fanion reste —, mais le plateau dit alors la vérité
          // entière : quelqu'un le fait, et personne n'en répond.
          const teneurDe = (o, cite) => (o ? personneDe(o.tient) : null) || personneDe(cite);
          // UN PORTRAIT NE SE SERT QU'UNE FOIS. Soixante actions, ce serait
          // soixante SVG dans la même réponse : on les range dans un
          // dictionnaire à part et l'action ne porte que l'identifiant de son
          // teneur. Le SVG est INLINÉ, jamais une URL — la page du jeu ne charge
          // aucune ressource externe.
          const portraits = {};
          const visage = (g) => {
            if (!g || !g.id) return null;
            if (portraits[g.id] === undefined) {
              let svg = "";
              const f = g.portrait && g.portrait.fichier;
              if (f) {
                try { svg = fs.readFileSync(path.join(RACINE, f), "utf-8"); } catch (e) {}
              }
              portraits[g.id] = svg || portraitDefaut(g.nom || g.id);
            }
            return g.id;
          };

          // Une clef est RETENUE, à étudier, ou écartée : c'est un état de la
          // clef, non un avancement. Une brèche dans un verrou, c'est une clef
          // retenue contre lui — rien d'autre ne perce la pierre.
          const tenueDe = (k) => {
            const e = sansAccent(k.c[6]);
            return e.indexOf("retenue") >= 0 ? "retenue"
              : e.indexOf("ecartee") >= 0 ? "ecartee" : "etudier";
          };
          const perce = (v) => clefs.some((k) =>
            adresses(k.c[2]).indexOf(v.num) >= 0 && tenueDe(k) === "retenue");

          // ---- LES MISSIONS : ce qu'il y aurait à faire ----------------------
          // La conclusion dit OÙ ça casse. Elle ne dit pas ce qu'on y ferait, et
          // c'était la moitié manquante : un plateau qui diagnostique et se tait.
          //
          // UN GABARIT, ET IL EST LUI-MÊME LE FILTRE :
          //
          //     Afin d'atteindre {X}, faire {Y} aurait effet {Z}.
          //
          // X se calcule EN REMONTANT — l'état cible que l'acte sert, et combien
          // d'autres il touche. Y est la seule part écrite en dur, par un verbe :
          // retenir, écarter, désigner, écrire, trouver. Z se calcule EN
          // REGARDANT L'AMONT IMMÉDIAT, et il doit être HONNÊTE : « le seul
          // verrou qui l'en sépare » quand c'est vrai, « un verrou sur deux »
          // quand ça ne suffit pas. Un détecteur dont on ne sait pas calculer le
          // X ou le Z n'est pas un détecteur : il se jette, il ne s'écrit pas
          // avec un Z vague.
          //
          // NI DATE NI PROSE : rien que la topologie et l'état des nœuds. Et
          // RIEN NE S'ÉCRIT — une mission s'affiche, elle ne touche aucun
          // registre. C'est du diagnostic rendu lisible, jamais une commande.
          //
          // LA DÉDUPLICATION SE FAIT PAR L'ACTE, PAS PAR LE DÉTECTEUR. « Toutes
          // les clefs de ce verrou sont à l'étude » et « cette action pend sous
          // une clef qui n'est pas retenue » désignent très souvent LE MÊME
          // ACTE : retenir cette clef-là. Un acte est donc identifié par le
          // couple (verbe, pièce) et posé UNE FOIS ; le premier détecteur qui le
          // trouve écrit sa phrase, les suivants s'y rangent. Sans cela le
          // plateau réclamerait trois fois la même décision sous trois libellés,
          // et c'est le tunnel — la faute que cette maison proscrit le plus dur.
          //
          // DEUX FAMILLES DE PORTEURS, et elles ne se confondent pas. À LA REINE
          // : retenir, écarter, désigner — c'est sa parole, personne d'autre ne
          // peut, et ça ne coûte rien à exécuter puisque le texte est déjà au
          // registre. AU CONSEIL : écrire, trouver — c'est du travail, et ça se
          // dépêche.
          const clefsDuVerrou = (v) => clefs.filter(
            (k) => adresses(k.c[2]).indexOf(v.num) >= 0);
          const actionsDeLaClef = (k) => actions.filter(
            (a) => adresses(a.c[2]).indexOf(k.num) >= 0);
          const verrousDeLetat = (n) => verrous.filter(
            (v) => adresses(v.c[2]).indexOf(n) >= 0);
          const verrousDeLaClef = (k) => verrous.filter(
            (v) => adresses(k.c[2]).indexOf(v.num) >= 0);
          const clefsDeLaction = (a) => clefs.filter(
            (k) => adresses(a.c[2]).indexOf(k.num) >= 0);
          const etatsDuVerrou = (v) => etats.filter(
            (e) => adresses(v.c[2]).indexOf(e.num) >= 0);
          const nomme = (q, genre) => ({
            genre: genre, numero: q.num, nom: sansSigne(q.c[1]) });

          // X — l'état cible qu'un verrou sert, et combien d'autres il touche.
          // On remonte, on ne devine pas : un verrou qui bloque trois états les
          // sert tous les trois, et le taire ferait mentir la mission sur sa
          // portée.
          const butDuVerrou = (v) => {
            const es = etatsDuVerrou(v);
            return { but: es.length ? nomme(es[0], "etat") : null,
                     buts_autres: Math.max(0, es.length - 1) };
          };
          // Z — la clause de suffisance, mesurée sur le seul graphe : combien de
          // verrous se dressent encore devant l'état qu'on vise.
          const suffisance = (v) => {
            const es = etatsDuVerrou(v);
            const n = es.length ? verrousDeLetat(es[0].num).length : 0;
            return n <= 1 ? "le seul verrou qui l'en sépare"
              : "un verrou sur " + n;
          };

          // LA FORCE D'UN ACTE — ce qu'il débloque, mesuré sur le seul graphe et
          // non jugé. Lever le dernier verrou d'un état cible bat lever un verrou
          // sur deux, qui bat porter une action sous une clef, qui bat ce qui ne
          // lève rien. Elle classe l'idée d'une affaire ET la réserve d'un homme :
          // une seule règle, pour que les deux listes se lisent pareil.
          const forceActe = (m) => {
            const t = String((m && m.precision) || "");
            if (t.indexOf("le seul verrou") === 0) return 1;
            let x = t.match(/^un verrou sur (\d+)/);
            if (x) return 1 + parseInt(x[1], 10);
            if (t.indexOf("la seule action") === 0) return 20;
            x = t.match(/^une action sur (\d+)/);
            if (x) return 20 + parseInt(x[1], 10);
            return 60;
          };
          const catalogue = {};
          const attaches = {};
          // Le classement d'une liste d'actes : la force d'abord, puis la portée
          // (celle qui remonte au plus d'états), puis le coût — la parole de la
          // reine avant le travail du conseil.
          const classerActes = (a, b) => {
            const ma = catalogue[a], mb = catalogue[b];
            if (!ma || !mb) return 0;
            return forceActe(ma) - forceActe(mb)
              || (mb.buts_autres || 0) - (ma.buts_autres || 0)
              || (ma.sur === "reine" ? 0 : 1) - (mb.sur === "reine" ? 0 : 1);
          };
          // DEUX ESPÈCES DE TROUS, et elles ne valent pas la même chose.
          //
          // Le trou MÉCANIQUE est celui que ces six détecteurs trouvent tout
          // seuls : un verrou sans clef, une clef qu'on n'a pas tranchée, une
          // action dont l'office n'a pas de numéro. Il est exhaustif, gratuit à
          // trouver, et de faible valeur — c'est de la tenue de registre, ça
          // s'écrit à la plume et ça se coche.
          //
          // Le trou NARRATIF, lui, est introuvable par calcul : « ce plan
          // suppose que Bar Emmon dira oui ». Il se trouve en TRAVAILLANT, par
          // un homme qu'on dépêche, et c'est le seul qui déplace quelque chose.
          // Quand il le rapporte, il l'écrit comme un VERROU au cahier de son
          // affaire — c'est la définition du guide — et le mécanique reprend la
          // main aussitôt pour dire ce qui manque autour. Le mécanique est
          // l'AVAL du narratif, jamais son concurrent.
          //
          // Un seul de nos six détecteurs commande un travail narratif : « un
          // état cible sans aucun verrou » — on veut quelque chose et personne
          // n'a encore dit ce qui empêche. Il ne se coche pas : il se dépêche.
          // Il porte donc son espèce, et le plateau le marque autrement.
          const poserM = (m) => {
            m.espece = m.detecteur === "sans-verrou" ? "narratif" : "mecanique";
            if (!catalogue[m.acte]) catalogue[m.acte] = m;
            return m.acte;
          };
          const attacher = (genre, num, acte) => {
            const c = genre + "/" + num;
            if (!attaches[c]) attaches[c] = [];
            if (attaches[c].indexOf(acte) < 0) attaches[c].push(acte);
          };

          // 1. TOUTES LES CLEFS D'UN VERROU SONT À L'ÉTUDE — personne n'a
          //    tranché, et rien ne bouge tant que personne ne tranche.
          verrous.forEach((v) => {
            const ks = clefsDuVerrou(v);
            if (!ks.length || !ks.every((k) => tenueDe(k) === "etudier")) return;
            ks.forEach((k) => attacher("verrou", v.num, poserM(Object.assign(
              butDuVerrou(v), {
                acte: "retenir/" + k.num, sur: "reine", detecteur: "a-l-etude",
                verbe: "retenir ou écarter", piece: nomme(k, "clef"),
                effet: "lèverait", vers: nomme(v, "verrou"),
                precision: suffisance(v) }))));
          });

          // 2. UNE ACTION DONT PERSONNE NE RÉPOND. Deux manques se cachaient
          //    sous ce détecteur, et l'on demandait à la reine de désigner un
          //    homme DÉJÀ NOMMÉ : « aucun office du registre ne la porte » est
          //    vrai aussi quand la cellule dit « Mestre Gerardys, la roukerie ».
          //    Ce qui manque là n'est pas un homme, c'est un NUMÉRO — et ce fait
          //    est vrai de presque toutes les actions du plan. Il va donc au
          //    chapeau de l'affaire, compté une fois, jamais sur les jetons :
          //    quatre cent cinquante lampes qui disent la même chose ne disent
          //    plus rien. Ne reste ici que la vraie décision : personne, nulle
          //    part, ne répond de cette action.
          actions.forEach((a) => {
            if (retrouver(a.c[4], iO, nO)) return;
            if (personneDe(a.c[4])) return;   // quelqu'un la porte : c'est un numéro qui manque
            const ks = clefsDeLaction(a);
            const k = ks[0] || null;
            const vs = k ? verrousDeLaClef(k) : [];
            const v = vs[0] || null;
            const soeurs = k ? actionsDeLaClef(k).length : 0;
            attacher("action", a.num, poserM(Object.assign(
              v ? butDuVerrou(v) : { but: null, buts_autres: 0 }, {
                // AU CONSEIL, ET PLUS À LA REINE. Tant qu'on croyait demander
                // un homme, c'était sa parole ; maintenant qu'on demande un
                // NUMÉRO, c'est du travail de greffe — on n'appelle pas la
                // reine pour reporter une ligne au registre des offices.
                acte: "office/" + a.num, sur: "conseil", detecteur: "sans-office",
                // « Désigner qui répond de » était faux dès que la cellule
                // nomme quelqu'un en clair — « Mestre Gerardys, la roukerie » —
                // sans que ce nom se reconnaisse dans `personnages.json` :
                // quelqu'un la porte bel et bien, c'est le LIEN qui n'est pas
                // écrit. On ne demande donc pas un homme, on demande un numéro.
                verbe: "écrire le numéro de l'office de", piece: nomme(a, "action"),
                effet: k ? "porterait" : "lui donnerait une main",
                vers: k ? nomme(k, "clef") : null,
                precision: !k ? "elle ne remonte à aucune clef"
                  : soeurs <= 1 ? "la seule action écrite sous elle"
                  : "une action sur " + soeurs + " sous elle" })));
          });

          // 3. UN ÉTAT CIBLE SANS AUCUN VERROU — on veut, et l'on n'a pas dit ce
          //    qui empêche. X remonte alors d'un cran : l'état que celui-ci sert.
          etats.forEach((e) => {
            if (verrousDeLetat(e.num).length) return;
            const p = adresse(e.c[5]);
            const pere2 = etats.find((x) => x.num === p) || null;
            attacher("etat", e.num, poserM({
              acte: "empeche/" + e.num, sur: "conseil", detecteur: "sans-verrou",
              but: nomme(pere2 || e, "etat"), buts_autres: 0,
              verbe: "trouver ce qui empêche", piece: nomme(e, "etat"),
              // Z ne se répète pas : l'acte vise déjà cet état-là, et
              // « donnerait sa première prise sur lui-même » n'apprend rien.
              effet: "ouvrirait la première prise sur lui", vers: null,
              precision: "aucun verrou n'est écrit contre lui" }));
          });

          // 4. UN VERROU SANS AUCUNE CLEF — le fait est nommé, rien n'est
          //    envisagé contre lui.
          verrous.forEach((v) => {
            if (clefsDuVerrou(v).length) return;
            attacher("verrou", v.num, poserM(Object.assign(butDuVerrou(v), {
              acte: "clef/" + v.num, sur: "conseil", detecteur: "sans-clef",
              verbe: "écrire une clef contre", piece: nomme(v, "verrou"),
              effet: "donnerait de quoi le lever", vers: null,
              precision: suffisance(v) })));
          });

          // 5. UNE ACTION SOUS UNE CLEF NON RETENUE — elle part sans que le
          //    mécanisme qu'elle sert ait été tranché. MÊME ACTE que le premier
          //    détecteur quand la clef est à l'étude : la dédup s'en charge.
          //    L'acte SE POSE SUR LE VERROU, et pas sur l'action qui l'a fait
          //    voir : c'est là que la conclusion rend son verdict (« sa clef
          //    n'est qu'à l'étude »), et deux calculs qui accrochent la même
          //    chose à deux rangs différents finissent par se contredire — une
          //    action qui « tient » sous une mission à faire.
          actions.forEach((a) => {
            clefsDeLaction(a).forEach((k) => {
              if (tenueDe(k) === "retenue") return;
              const v = verrousDeLaClef(k)[0] || null;
              attacher(v ? "verrou" : "clef", v ? v.num : k.num, poserM(Object.assign(
                v ? butDuVerrou(v) : { but: null, buts_autres: 0 }, {
                  acte: "retenir/" + k.num, sur: "reine", detecteur: "non-tranchee",
                  verbe: "trancher", piece: nomme(k, "clef"),
                  effet: v ? "lèverait" : "en déciderait le sort",
                  vers: v ? nomme(v, "verrou") : null,
                  precision: v ? suffisance(v)
                    : "elle n'ouvre aucun verrou connu" })));
            });
          });

          // 6. UNE CLEF RETENUE SANS ACTION — décidée, et personne ne la fait.
          //    Aucune aujourd'hui ; le cas se garde, un plan bouge.
          clefs.forEach((k) => {
            if (tenueDe(k) !== "retenue" || actionsDeLaClef(k).length) return;
            const v = verrousDeLaClef(k)[0] || null;
            attacher("clef", k.num, poserM(Object.assign(
              v ? butDuVerrou(v) : { but: null, buts_autres: 0 }, {
                acte: "action/" + k.num, sur: "conseil", detecteur: "sans-action",
                verbe: "écrire l'action de", piece: nomme(k, "clef"),
                effet: "la mettrait en marche", vers: null,
                precision: "elle est retenue et rien ne la fait" })));
          });

          // ---- LE REPLI : ce que seuls les registres connaissent ----
          // Les six registres cessent d'être la source ; ils ne se jettent pas
          // pour autant. Six affaires y vivent que nul cahier ne porte (deux ont
          // bien un volume, mais vide de tables). On ne reprend d'elles que ce
          // qui ne collisionne avec rien et qui CHAÎNE à leurs propres états :
          // reprendre en vrac ferait rentrer par la bande le petit plan qu'on
          // vient d'écarter.
          // Par GENRE, et non en vrac : les numéros se croisent d'un rang à
          // l'autre — un verrou 100 masquait l'état 100, et le repli ne reprenait
          // plus rien du tout.
          const connu = { etat: {}, verrou: {}, clef: {}, action: {} };
          Object.keys(bacs).forEach((genre) => {
            bacs[genre].forEach((r) => { connu[genre][r.num] = 1; });
          });
          const REGISTRE_PLAN = { etat: "plan-etats-cibles", verrou: "plan-verrous",
                                  clef: "plan-clefs", action: "plan-actions" };
          const repli = {};
          Object.keys(REGISTRE_PLAN).forEach((genre) => {
            repli[genre] = normaliser(parId[REGISTRE_PLAN[genre]], genre);
          });
          const memeNom = (x, y) => {
            const a3 = sansAccent(x), b3 = sansAccent(y);
            return !!a3 && !!b3 && (a3 === b3 || a3.indexOf(b3) >= 0 || b3.indexOf(a3) >= 0);
          };
          const orphelins = {};
          const horsAffaire = [];
          repli.etat.forEach((r) => {
            const nom = sansSigne(r.c[6]) || "Sans affaire";
            if (connu.etat[r.num] || groupes.some((g) => memeNom(g.titre, nom))) return;
            horsAffaire.push({ numero: r.num, titre: sansSigne(r.c[1]), affaire: nom });
            orphelins[r.num] = 1;
          });
          const chaine = (genre, pris, amont) => {
            repli[genre].forEach((r) => {
              if (connu[genre][r.num] || !adresses(r.c[2]).some((x) => amont[x])) return;
              bacs[genre].push(r); pris[r.num] = 1;
            });
          };
          const vRepli = {}, kRepli = {};
          chaine("verrou", vRepli, orphelins);
          chaine("clef", kRepli, vRepli);
          chaine("action", {}, kRepli);

          // ---- LA GOUTTIÈRE FRANCHISSABLE ------------------------------------
          // Le plateau s'arrêtait NET au bord du cahier. `pere()` traite un état
          // qui sert un état d'ailleurs comme une racine — la canopée se coupe
          // sans rien dire —, et la colonne `⛓️ Dépend de` n'était pas même lue.
          // Or ces arêtes-là existent, elles sont écrites, et elles sont
          // PROPRES : mesurées au niveau des PIÈCES, elles forment un graphe
          // acyclique de trois rangs. Ce sont les AFFAIRES qui bouclent, parce
          // qu'écraser deux cahiers en deux jetons fabrique un cycle qui n'est
          // nulle part dans le plan — c'est la raison pour laquelle il n'y a pas
          // de « plateau des affaires » et pourquoi le passage se fait ici,
          // pièce à pièce (voir docs/echiquier.md).
          //
          // QUATRE SENS, ET LEUR ORIENTATION EST CELLE DE LA CHAÎNE :
          //   sert     ⬆ notre état sert un état d'ailleurs — la canopée continue
          //   attendue ⬆ une action d'ailleurs attend cette pièce — on la nourrit
          //   servie   ⬇ un état d'ailleurs sert le nôtre — le travail est là-bas
          //   attend   ⬇ notre action attend une pièce d'ailleurs — le blocage y est
          const idAffaire = (titre) => sansAccent(titre).replace(/ /g, "-");
          // Qui porte ce numéro, et à quel rang. Les numéros se croisent d'un
          // cahier à l'autre (c'est documenté et ce n'est pas réparable au
          // calcul) : on garde donc TOUS les porteurs et l'on choisit celui qui
          // n'est pas chez nous.
          const chezQui = {};
          [["etat", etats], ["verrou", verrous], ["clef", clefs],
           ["action", actions]].forEach((paire) => {
            paire[1].forEach((r) => {
              (chezQui[r.num] = chezQui[r.num] || []).push({ genre: paire[0], r: r });
            });
          });
          // Ce qu'une action attend, retourné : le numéro attendu donne les
          // actions qui l'attendent. Une action peut dépendre de n'importe quel
          // rang — un verrou, une clef —, donc on retourne l'index une fois pour
          // toutes plutôt que de le chercher par genre.
          const attendu = {};
          actions.forEach((a) => adresses(a.c[8]).forEach((n) => {
            (attendu[n] = attendu[n] || []).push(a);
          }));
          const dehorsDe = (p, moi) => {
            const out = [], vu = {};
            const pose = (sens, r, genre) => {
              if (!r || !r.aff || r.aff === moi) return;
              const k = sens + "/" + r.num;
              if (vu[k]) return;
              vu[k] = 1;
              out.push({ sens: sens, numero: r.num, nom: sansSigne(r.c[1]),
                genre: genre, affaire: idAffaire(r.aff), affaire_titre: r.aff });
            };
            const mien = (chezQui[p.numero] || [])
              .find((x) => x.genre === p.genre && x.r.aff === moi);
            if (p.genre === "etat") {
              if (mien) adresses(mien.r.c[5]).forEach((n) => {
                const q = (chezQui[n] || [])
                  .find((x) => x.genre === "etat" && x.r.aff !== moi);
                if (q) pose("sert", q.r, "etat");
              });
              etats.forEach((o) => {
                if (adresses(o.c[5]).indexOf(p.numero) >= 0) pose("servie", o, "etat");
              });
            }
            if (p.genre === "action" && mien) {
              adresses(mien.r.c[8]).forEach((n) => {
                const q = (chezQui[n] || []).find((x) => x.r.aff !== moi);
                if (q) pose("attend", q.r, q.genre);
              });
            }
            (attendu[p.numero] || []).forEach((o) => pose("attendue", o, "action"));
            return out;
          };

          // Les têtes, une fois pour toute la requête (voir numerosDesTetes).
          const tetes = numerosDesTetes();
          const affaires = groupes.map((g) => {
            const pieces = [], colonnes = [];
            // CE QUI SE DIT EN COURS SANS ÊTRE DANS LA TÊTE : un homme qui dit
            // travailler et dont le plan de journée n'en porte pas trace. Ça se
            // sert au MJ, ça NE SE PEINT PAS sur le plateau — c'est un écart
            // entre deux registres, pas une information de personnage.
            const divergents = [];
            const chez = {};
            g.etats.forEach((e) => { chez[e.num] = e; });
            // L'arbre : `Sert` pointe vers l'amont. Un état qui sert un état
            // d'une AUTRE affaire est une racine ici — on ne dessine pas la
            // moitié d'un arbre qui vit ailleurs.
            const pere = (e) => { const p = adresse(e.c[5]); return chez[p] ? p : null; };
            const enfants = {};
            g.etats.forEach((e) => { enfants[e.num] = []; });
            g.etats.forEach((e) => { const p = pere(e); if (p) enfants[p].push(e.num); });
            const racines = g.etats.filter((e) => !pere(e)).map((e) => e.num)
              .sort((a, b) => chiffre(a) - chiffre(b));

            const verrousDe = (n) => verrous.filter((v) => adresses(v.c[2]).indexOf(n) >= 0);
            // Une colonne s'ouvre sous ce qui porte quelque chose, et sous une
            // feuille même vide — c'est elle que l'épreuve du guide doit compter.
            const ouvre = (n) => verrousDe(n).length > 0 || !enfants[n].length;

            const niveau = {}, portee = {}, sienne = {};
            const descendre = (n, d) => {
              niveau[n] = d;
              const debut = colonnes.length;
              if (ouvre(n)) {
                sienne[n] = n;
                colonnes.push({ id: n, numero: n, titre: sansSigne(chez[n].c[1]),
                  dit: propre(chez[n].c[2]), etat: n });
              }
              enfants[n].sort((a, b) => chiffre(a) - chiffre(b))
                .forEach((c) => descendre(c, d + 1));
              portee[n] = colonnes.slice(debut).map((c) => c.id);
            };
            racines.forEach((r) => descendre(r, 0));

            // ---- LA CONCLUSION : où ça casse, en descendant ----
            // UN SEUL MÉCANISME, pas six cas particuliers : on descend la
            // chaîne depuis la pièce et l'on s'arrête AU PREMIER TROU. Une
            // pièce, un coupable, une phrase — jamais une liste de griefs.
            // Tout se lit sur la topologie : ni date, ni prose, rien que ce que
            // le graphe dit déjà.
            //
            // Un état descend sur ses verrous ET sur les états qui le servent :
            // c'est ce que compte déjà l'épreuve du guide (la réglette rouge,
            // le fanion), et les deux calculs doivent dire la même vérité.
            const clefsDe = (v) => clefs.filter((k) => adresses(k.c[2]).indexOf(v.num) >= 0);
            const actionsDe = (k) => actions.filter((x) => adresses(x.c[2]).indexOf(k.num) >= 0);
            const dit = (q, genre) => ({
              genre: genre, numero: q.num, nom: sansSigne(q.c[1]),
            });
            const memo = {};
            const conclure = (q, genre) => {
              const memoire = genre + q.num;
              if (memo[memoire]) return memo[memoire];
              memo[memoire] = { cas: "tient" };     // garde-fou contre un cycle
              let r;
              if (genre === "action") {
                const of2 = retrouver(q.c[4], iO, nO);
                // La chaîne descend jusqu'au sol dès que QUELQU'UN la porte.
                // Mais si aucun office numéroté ne la porte, le jeton arbore
                // déjà son fanion : la conclusion doit le dire dans les mêmes
                // termes, sinon le joueur lit un drapeau rouge sous une phrase
                // qui dit que tout va bien. Ça ne casse pas la chaîne — ça
                // s'ajoute à elle.
                r = teneurDe(of2, q.c[4])
                  ? (of2 ? { cas: "tient" } : { cas: "tient", sans_office: true })
                  : { cas: "sans-teneur", cible: dit(q, "action") };
              } else if (genre === "clef") {
                // L'EMPÊCHEMENT D'UNE CLEF N'EST PAS SOUS ELLE, IL EST EN ELLE.
                // Une clef à l'étude concluait « la chaîne tient » dès qu'une
                // action portée pendait dessous — sur la pièce même que tout le
                // monde attend, et sur laquelle la mission se pose. Son état
                // propre passe donc AVANT ce qu'elle porte : rien ne partira
                // tant qu'on ne l'aura pas tranchée, et ce qui est écrit
                // dessous ne change rien à ça. Même règle pour une clef
                // écartée : ce qui pend sous elle ne sert plus à personne.
                const t = tenueDe(q);
                const sous = actionsDe(q);
                if (t === "etudier") r = { cas: "pas-tranchee", cible: dit(q, "clef") };
                else if (t === "ecartee") r = { cas: "ecartee", cible: dit(q, "clef") };
                else if (!sous.length) r = { cas: "sans-action", cible: dit(q, "clef") };
                else r = premier(sous.map((x) => [x, "action"]), dit(q, "clef"));
              } else if (genre === "verrou") {
                const ks = clefsDe(q);
                if (!ks.length) r = { cas: "sans-clef", cible: dit(q, "verrou") };
                else {
                  const tenues = ks.filter((k) => tenueDe(k) === "retenue");
                  if (!tenues.length) {
                    r = { cas: "a-l-etude", cible: dit(q, "verrou"),
                          via: dit(ks[0], "clef"), autres: ks.length - 1 };
                  } else r = premier(tenues.map((k) => [k, "clef"]), dit(q, "verrou"));
                }
              } else {
                const sous = verrousDe(q.num).map((v) => [v, "verrou"])
                  .concat((enfants[q.num] || []).sort((a2, b2) => chiffre(a2) - chiffre(b2))
                    .map((n) => [chez[n], "etat"]));
                if (!sous.length) r = { cas: "sans-verrou", cible: dit(q, "etat") };
                else r = premier(sous, dit(q, "etat"));
              }
              memo[memoire] = r;
              return r;
            };
            // Le premier enfant qui casse l'emporte ; les autres du MÊME cas se
            // comptent, pour qu'on puisse dire « et deux autres dans le même
            // cas » au lieu d'aligner les griefs.
            function premier(sous, dessus) {
              const vus = sous.map(([q, g]) => conclure(q, g));
              const i = vus.findIndex((v) => v.cas !== "tient");
              // « Personne n'en répond » NE S'ARRÊTE PAS À L'ACTION. Le caveat
              // remonte avec la chaîne, sans quoi une clef dont toutes les
              // actions sont portées hors registre dirait « la chaîne tient »
              // à plat — au-dessus de trois fanions et d'une mission à faire.
              // C'est la divergence qu'a révélée le calcul des missions ; on la
              // corrige ici, du côté qui mentait.
              if (i < 0) {
                const nu2 = vus.some((v) => v.sans_office);
                return nu2 ? { cas: "tient", sans_office: true } : { cas: "tient" };
              }
              const meme = vus.filter((v) => v.cas === vus[i].cas).length - 1;
              const r = Object.assign({}, vus[i]);
              r.autres = (r.autres || 0) + meme;
              // On garde le maillon d'où l'on est parti, pour que la phrase
              // puisse dire « X attend Y » quand ce n'est pas la pièce elle-même.
              if (!r.depuis) r.depuis = dessus;
              return r;
            }

            // ---- LA LAMPE : UNE PAR ACTE, SUR LA PIÈCE QU'IL VISE ----
            // Le champ `missions` d'une pièce est sa chaîne descendante entière
            // — c'est ce qu'il faut pour la bulle, et c'est trop pour le
            // plateau : un même acte y allumerait l'état cible, son verrou et
            // l'action qui l'a fait voir, trois lampes pour une décision. La
            // marque suit donc la même règle que les missions elles-mêmes, la
            // déduplication par l'ACTE : une idée, un acte, UNE lampe, posée sur
            // la pièce que l'acte vise — la clef à retenir, l'action dont il
            // faut désigner le teneur, le verrou contre quoi écrire une clef,
            // l'état qu'il faut mettre à l'épreuve. Les pièces d'amont
            // continuent de la DIRE dans leur bulle, ce qui est sa place.
            //
            // Une pièce peut être dessinée dans deux colonnes (un verrou qui
            // bloque deux états) : la lampe va sur la première, sans quoi on
            // compterait deux marques pour une décision.
            const posees = {};
            const lampeDe = (genre, num) => {
              const k = genre + "/" + num;
              if (posees[k]) return null;
              const a = Object.keys(catalogue).filter((x) => {
                const m = catalogue[x].piece;
                return m && m.genre === genre && m.numero === num;
              });
              if (!a.length) return null;
              posees[k] = 1;
              return a;
            };

            // ---- CE QUI PEND SOUS UNE PIÈCE, EN MISSIONS ----
            // La MÊME descente que la conclusion, et c'est voulu : les deux
            // calculs doivent dire la même vérité, sinon le joueur lit un
            // « la chaîne tient » au-dessus d'une chose à faire. On remonte les
            // actes de toute la chaîne aval, dédupliqués par l'acte, le plus
            // proche d'abord — la pièce elle-même, puis ce qui pend dessous.
            const memoM = {};
            const missionsDe = (q, genre) => {
              const memoire = genre + q.num;
              if (memoM[memoire]) return memoM[memoire];
              memoM[memoire] = [];              // garde-fou contre un cycle
              const sous = genre === "etat"
                ? verrousDe(q.num).map((v) => [v, "verrou"])
                    .concat((enfants[q.num] || []).sort((a2, b2) => chiffre(a2) - chiffre(b2))
                      .map((n) => [chez[n], "etat"]))
                : genre === "verrou" ? clefsDe(q).map((k) => [k, "clef"])
                : genre === "clef" ? actionsDe(q).map((a) => [a, "action"])
                : [];
              const out = [], vu = {};
              const ajoute = (a) => { if (!vu[a]) { vu[a] = 1; out.push(a); } };
              // D'ABORD L'ACTE QUI VISE CETTE PIÈCE — c'est celui dont elle
              // porte la lampe sur le plateau, et il serait absurde qu'elle
              // l'affiche au coin du sceau sans le dire dans sa bulle. Un acte
              // se pose sur le rang où la conclusion rend son verdict, mais il
              // se LIT aussi sur la pièce qu'il vise.
              Object.keys(catalogue).forEach((x) => {
                const m = catalogue[x].piece;
                if (m && m.genre === genre && m.numero === q.num) ajoute(x);
              });
              (attaches[genre + "/" + q.num] || []).forEach(ajoute);
              sous.forEach(([x, gg]) => missionsDe(x, gg).forEach(ajoute));
              memoM[memoire] = out;
              return out;
            };

            g.etats.forEach((e) => {
              const col = sienne[e.num] || null;
              const cle = (n) => (col || "arbre") + "/" + n;
              const pousse = (p) => { pieces.push(p); return p; };
              const sansPreuve = (c) => rien(c)
                ? ["sans preuve — rien ne dirait que c'est vrai"] : [];

              const mesVerrous = verrousDe(e.num);
              const mesClefs = clefs.filter((k) => adresses(k.c[2])
                .some((a) => mesVerrous.some((v) => v.num === a)));
              const mesActions = actions.filter((a) => adresses(a.c[2])
                .some((x) => mesClefs.some((k) => k.num === x)));

              // l'état cible : ce qui doit devenir vrai dans le monde
              const p = pere(e);
              pousse({
                cle: cle(e.num), genre: "etat", rang: "etat", colonne: col, numero: e.num,
                conclusion: conclure(e, "etat"), missions: missionsDe(e, "etat"),
                lampe: lampeDe("etat", e.num),
                nom: sansSigne(e.c[1]), dit: propre(e.c[2]), ou: propre(e.c[3]),
                preuve: propre(e.c[4]), sert: p, niveau: niveau[e.num] || 0,
                portee: portee[e.num] || [],
                part: mesVerrous.map((v) => ({
                  numero: v.num, nom: sansSigne(v.c[1]), breche: perce(v),
                })),
                vers: p ? [(sienne[p] || "arbre") + "/" + p] : [],
                paie: "cet état en sert un autre",
                sans_preuve: rien(e.c[4]),
              });

              if (!col) return;   // un état qui coiffe n'a rien qui pende sous lui

              // les verrous : le fait du monde qui empêche l'état de tenir
              mesVerrous.forEach((v) => {
                const f = sansPreuve(v.c[4]);
                if (rien(v.c[5])) f.push("on ne sait pas dire à quoi il serait levé");
                pousse({
                  cle: cle(v.num), genre: "verrou", rang: "verrou", colonne: col, numero: v.num,
                  conclusion: conclure(v, "verrou"), missions: missionsDe(v, "verrou"),
                  lampe: lampeDe("verrou", v.num),
                  nom: sansSigne(v.c[1]), dit: propre(v.c[3]), preuve: propre(v.c[4]),
                  leve_quand: propre(v.c[5]), breche: perce(v), vers: [cle(e.num)],
                  paie: rien(v.c[5]) ? null : "levé quand : " + sansSigne(v.c[5]),
                  fautes: f.length ? f : null,
                });
              });

              // les clefs : le mécanisme envisagé, et où il en est du jugement
              mesClefs.forEach((k) => {
                const amont = adresses(k.c[2]).filter((a) => mesVerrous.some((v) => v.num === a));
                const tenue = tenueDe(k);
                const f = [];
                // UNE RUPTURE, ET NON UNE REMARQUE. La différence commande la
                // couleur du plateau : `rupture` veut dire que la REMONTÉE est
                // cassée — il manque une pièce, la référence ne résout pas —, et
                // c'est la seule chose que l'écran peigne en rouge. Tout ce qui
                // manque et qui s'écrit à la plume (une preuve, un « levé
                // quand », un numéro d'office) est une LAMPE, pas une faute :
                // le plateau a déjà le dispositif qu'il faut pour le dire.
                let rupture = false;
                if (!adresses(k.c[2]).some((a) => iV[a])) {
                  f.push("n'ouvre aucun verrou connu — la clef n'est pas reliée au plan");
                  rupture = true;
                }
                pousse({
                  cle: cle(k.num), genre: "clef", rang: "clef", colonne: col, numero: k.num,
                  conclusion: conclure(k, "clef"), missions: missionsDe(k, "clef"),
                  lampe: lampeDe("clef", k.num),
                  nom: sansSigne(k.c[1]), dit: propre(k.c[3]), cout: propre(k.c[4]),
                  preuve: propre(k.c[5]), tenue: tenue, vers: amont.map(cle),
                  paie: tenue === "retenue" ? "clef retenue — " + sansSigne(k.c[5]) : null,
                  fautes: f.length ? f : null, rupture: rupture,
                });
              });

              // les actions : ce qu'on décide effectivement de faire
              mesActions.forEach((a) => {
                const amont = adresses(a.c[2]).filter((x) => mesClefs.some((k) => k.num === x));
                const ou = sansAccent(a.c[7]);
                const marche = ou.indexOf("fait") >= 0 || ou.indexOf("en cours") >= 0;
                const of = retrouver(a.c[4], iO, nO);
                const f = sansPreuve(a.c[6]);
                let rupture = false;
                if (!amont.length) {
                  f.push("ne remonte à aucune clef — l'action n'a pas de raison démontrée");
                  rupture = true;
                }
                const qui_tient = teneurDe(of, a.c[4]);
                const quiId = visage(qui_tient);
                // DANS SA TÊTE, OU SEULEMENT SUR LE PAPIER. Voir numerosDesTetes
                // et la constante LIRE_LES_TETES.
                const dansLaTete = !!(quiId && tetes.par[quiId]
                  && tetes.par[quiId][String(a.num)]);
                if (marche && !dansLaTete) divergents.push(a.num);
                if (!of) f.push("aucun office ne la porte : " + (propre(a.c[4]) || "à désigner"));
                // PERSONNE POUR LA PORTER : là, oui, il manque une pièce, et la
                // remontée s'arrête. Un office nommé EN CLAIR ne casse rien —
                // quelqu'un la porte très bien, ce qui lui manque est un NUMÉRO
                // et non un homme, et ce fait-là se dit une fois au chapeau.
                if (!of && !qui_tient) rupture = true;
                pousse({
                  cle: cle(a.num), genre: "action", rang: "action", colonne: col, numero: a.num,
                  conclusion: conclure(a, "action"), missions: missionsDe(a, "action"),
                  lampe: lampeDe("action", a.num),
                  nom: sansSigne(a.c[1]), dit: propre(a.c[3]), preuve: propre(a.c[6]),
                  ou_ca_en_est: propre(a.c[7]), office: propre(a.c[4]), moyens: propre(a.c[5]),
                  // Le visage de qui la porte : on ne sert que son identifiant,
                  // le dessin est au dictionnaire commun.
                  teneur_id: quiId, teneur: qui_tient ? qui_tient.nom : null,
                  vers: amont.map(cle), paie: marche ? propre(a.c[7]) : null,
                  fautes: f.length ? f : null, rupture: rupture,
                  dans_la_tete: dansLaTete,
                });

                // les moyens et les offices : cités par leur numéro, jamais créés
                const cite = (texte, genre, index, noms) => {
                  const t = retrouver(texte, index, noms);
                  const k = cle(genre + "-" + (t ? t.num : sansAccent(texte).slice(0, 14)));
                  let q = pieces.find((x) => x.cle === k);
                  if (!q) {
                    q = pousse({
                      cle: k, genre: genre, rang: "moyen", colonne: col,
                      numero: t ? t.num : null,
                      nom: t ? sansSigne(t.nom) : sansSigne(texte),
                      // La description d'une pièce est la colonne qui DIT la
                      // chose, et elle n'est pas au même rang dans les deux
                      // registres : « ce qu'il sait faire » pour un moyen, « ce
                      // dont il répond » pour un office — jamais le titulaire.
                      dit: t ? cel(t, genre, "dit") : "",
                      tient: t ? cel(t, genre, "tient") : "",
                      ou: t ? cel(t, genre, "ou") : "",
                      tenue_du_moyen: t ? cel(t, genre, "etat") : "",
                      vers: [], paie: t ? "au registre, " + t.num : null,
                      fautes: t ? null : ["cité ici et absent de son registre — un moyen "
                        + "et un office ne se créent jamais dans une affaire"],
                      // ET CE N'EST PAS UNE RUPTURE. « Le crédit de l'époux de
                      // la reine », « ce que la reine sait du Donjon » : la
                      // chose existe, elle est employée, elle est simplement
                      // citée par son nom au lieu de son numéro. C'est vrai de
                      // 477 pièces du plan — un fait vrai de presque tout le
                      // monde va au chapeau et se dit une fois, jamais sur un
                      // jeton (voir docs/echiquier.md).
                      rupture: false,
                    });
                  }
                  if (q.vers.indexOf(cle(a.num)) < 0) q.vers.push(cle(a.num));
                };
                if (!rien(a.c[4])) cite(a.c[4], "office", iO, nO);
                String(a.c[5] == null ? "" : a.c[5]).split(/·|;/).forEach((m) => {
                  if (!rien(m)) cite(m, "moyen", iM, nM);
                });
              });

              // L'ÉPREUVE DU GUIDE, colonne par colonne : un état cible sous
              // lequel aucune action ne descend est une intention sans plan.
              const c = colonnes.find((x) => x.id === col);
              c.rompue = !mesActions.length;
              c.sans_verrou = !mesVerrous.length;
              // ET LE VERDICT INVERSE, qui manquait : la colonne est-elle
              // PORTÉE ? Une colonne dont la chaîne descend jusqu'à une action
              // n'est qu'un plan bien écrit ; elle n'est du travail que si l'un
              // des hommes qui la tiennent a écrit « en cours » ou « fait »
              // dans son cahier. C'est cela que le vert dit, et rien d'autre.
              c.porte = pieces.some((q) => q.genre === "action"
                && q.colonne === col && q.paie);
            });

            // ---- LES VOISINES : à quelles autres affaires celle-ci tient -----
            // PREMIÈRE VERSION ÉCARTÉE, et le joueur a tranché en la voyant : on
            // posait la sortie SUR LE JETON, un chevron par pièce et par sens.
            // Sur un damier qui porte déjà six teintes de rang, des dalles
            // d'occlusion, des lampes, des fanions, des visages et cent traits
            // de chaîne, cela faisait UN SIGNE DE PLUS et rien de lisible — et
            // ça poussait à remonter la chaîne causale pièce à pièce, ce que
            // personne ne veut faire à cette échelle.
            //
            // Ce qu'il fallait est plus petit : SAVOIR À QUI CETTE AFFAIRE
            // TIENT, et pouvoir y aller. Donc on agrège — le calcul par pièce
            // reste la source, mais rien n'en sort au niveau de la pièce. Une
            // ligne par affaire voisine, avec son emblème, servie au bandeau et
            // jamais au damier.
            const voisinage = {};
            pieces.forEach((p) => {
              if (!p.numero) return;
              dehorsDe(p, g.titre).forEach((x) => {
                const v = voisinage[x.affaire] || (voisinage[x.affaire] = {
                  id: x.affaire, titre: x.affaire_titre, n: 0, sens: {} });
                v.n += 1;
                v.sens[x.sens] = (v.sens[x.sens] || 0) + 1;
              });
            });
            const voisines = Object.keys(voisinage).map((k) => {
              const v = voisinage[k];
              const vol = volumeDe(v.titre);
              return { id: v.id, titre: v.titre, n: v.n, sens: v.sens,
                embleme: (vol && vol.embleme) || null };
              // L'ORDRE EST CELUI DU POIDS, pas de l'alphabet : l'affaire à qui
              // l'on tient par onze arêtes passe avant celle qui n'en a qu'une.
            }).sort((a, b) => b.n - a.n || a.titre.localeCompare(b.titre));

            // ... et elle REMONTE dans l'arbre : un état qui coiffe des colonnes
            // toutes rompues est rompu lui-même, et le fanion se voit sur lui.
            pieces.filter((p) => p.genre === "etat").forEach((p) => {
              const sous = (p.portee || []).map((id) => colonnes.find((c) => c.id === id));
              const rompu = !sous.length || sous.every((c) => c && c.rompue);
              const f = p.sans_preuve ? ["sans preuve — rien ne dirait que c'est vrai"] : [];
              if (rompu) {
                f.push(p.portee && p.portee.length > 1
                  ? "aucune action ne descend d'aucun état qu'il coiffe"
                  : "aucune action ne descend jusqu'ici — une intention sans plan");
              }
              p.rompu = rompu;
              if (f.length) p.fautes = f;
              // Le SEUL défaut d'un état cible qui casse la remontée : rien ne
              // descend jusqu'à une action. Un état sans preuve écrite est mal
              // tenu, pas rompu.
              p.rupture = rompu;
              delete p.sans_preuve;
            });

            // Ce que l'affaire ENTIÈRE réclame — les actes de toutes ses pièces,
            // dédupliqués une dernière fois : deux colonnes qui pendent sous le
            // même verrou ne le réclament pas deux fois.
            const toutes = [], vuA = {};
            pieces.forEach((p) => (p.missions || []).forEach((a) => {
              if (!vuA[a]) { vuA[a] = 1; toutes.push(a); }
            }));
            // LE FAIT RETOURNÉ. « Ce verrou n'a pas de rechange » est vrai de
            // trente-deux verrous sur trente-trois : posé sur les jetons il ne
            // dirait rien et noierait le reste. Il ne se jette pas pour autant —
            // il se retourne et se dit UNE FOIS, au chapeau : aucun verrou du
            // plan n'a jamais eu deux clefs, quand le guide prévoit qu'elles
            // « se disputent la place ». Un fait vrai de presque tout le monde
            // va sur le blason, jamais sur une pièce.
            // CE QUI EST VRAI DE PRESQUE TOUTE L'AFFAIRE se dit au chapeau. Une
            // action dont l'office est nommé en clair a bien quelqu'un pour la
            // porter ; ce qui lui manque est une ligne au registre des offices,
            // et c'est une discipline à reprendre d'un coup, pas une décision
            // par action.
            const enClair = pieces.filter((q) => q.genre === "action"
              && (q.fautes || []).some((f) => f.indexOf("aucun office") === 0)
              && q.teneur).length;
            // Et le même fait, du côté des MOYENS : un galet ou une plume cités
            // par leur nom au lieu de leur numéro. Ce n'était compté nulle part,
            // donc c'était peint en rouge sur chaque jeton faute de mieux.
            const citesEnClair = pieces.filter(
              (q) => (q.genre === "moyen" || q.genre === "office") && !q.numero).length;

            const numsV = {}, mesV = [];
            pieces.filter((p) => p.genre === "verrou").forEach((p) => {
              if (!numsV[p.numero]) { numsV[p.numero] = 1; mesV.push(p.numero); }
            });
            const combienDeClefs = (n) => clefs.filter(
              (k) => adresses(k.c[2]).indexOf(n) >= 0).length;
            const rechange = {
              verrous: mesV.length,
              aucune: mesV.filter((n) => combienDeClefs(n) === 0).length,
              plusieurs: mesV.filter((n) => combienDeClefs(n) > 1).length,
            };

            // L'IDÉE PRINCIPALE — une affaire en réclame jusqu'à onze, et l'on
            // n'en montre qu'UNE là où l'on n'a la place que d'une ligne (le
            // coffret « Les sujets » en aligne trente-huit : trois idées chacune
            // seraient un mur). Le classement ne juge pas, il mesure, dans cet
            // ordre :
            //   1. LA FORCE DU Z — lever le dernier verrou d'un état cible bat
            //      lever un verrou sur deux, qui bat porter une action sous une
            //      clef, qui bat ce qui ne lève rien du tout.
            //   2. LA PORTÉE — à force égale, celle qui remonte au plus d'états.
            //   3. LE COÛT — à égalité encore, celle qui ne coûte qu'un mot au
            //      registre : la parole de la reine avant le travail du conseil.
            const idee = toutes.slice().sort((a, b) => classerActes(a, b))[0] || null;

            const v = g.volume || volumeDe(g.titre);
            return {
              // La clef de routage, telle que le cahier l'écrit — c'est elle qui
              // porte la réserve par homme, et rien d'autre.
              tenu_par: (v && v.tenu_par) || null, office: (v && v.office) || null,
              missions: toutes, rechange: rechange, idee: idee, en_clair: enClair,
              cites_en_clair: citesEnClair,
              // Ce que l'affaire porte VRAIMENT, et l'écart entre la parole et
              // la tête. Les deux vont au MJ ; seul `portees` se peint.
              portees: colonnes.filter((c) => c.porte).length,
              divergents: divergents,
              id: sansAccent(g.titre).replace(/ /g, "-"), titre: g.titre,
              livre_id: v ? v.id : null,
              // L'emblème est CELUI DU VOLUME, jamais un choix d'ici. Une
              // affaire dont aucun volume ne porte le nom garde le signe
              // générique de l'affaire, et c'est en soi une information.
              embleme: (v && v.embleme) || null, objet: objetDe(v),
              // L'INDEX DES ADRESSES, servi pour TOUTES les affaires et pas
              // seulement pour celle qu'on a ouverte. C'est ce qui permet à un
              // renvoi de scène — `[les neufs](44022)` — de savoir sur-le-champ
              // si le numéro qu'un conseiller vient de citer est une pièce du
              // plan, et laquelle. Sans lui, la page devrait interroger la route
              // pour chaque renvoi, ou pire : s'allumer à l'aveugle et parfois
              // mentir. On ne garde que les adresses qu'un renvoi peut porter —
              // quatre à six chiffres, la forme de `renvois.js` —, ce qui laisse
              // dehors les M01 et O17 des moyens et des offices.
              nums: (function () {
                const n = pieces.map((q) => q.numero)
                  .filter((x) => /^\d{4,6}$/.test(String(x || "")))
                  .filter((x, i, t) => t.indexOf(x) === i);
                return n;
              })(),
              // ET CE QUE LE CAHIER ÉCRIT SANS L'ATTEINDRE. Une ligne dont la
              // référence ne résout pas — l'action 21030 « réalise 21020 »
              // quand aucune clef 21020 n'existe — est écrite, numérotée,
              // citable en conseil, et n'a AUCUN jeton sur le damier. Le
              // plateau a raison de ne pas la dessiner : c'est la faute que le
              // guide veut voir. Mais la citer en scène est légitime, et un
              // renvoi vers elle doit mener à son cahier au lieu de retomber
              // en texte nu. On sert donc les deux listes, et l'écran fait la
              // différence : `nums` s'allume, `cites` ouvre le bon plateau et
              // dit pourquoi il n'y a rien à allumer.
              cites: (function () {
                const t = pieces.map((q) => String(q.numero || ""));
                return (g.ecrites || []).filter((n) => t.indexOf(n) < 0);
              })(),
              voisines: voisines,
              colonnes: colonnes, pieces: pieces,
              niveaux: Math.max(1, 1 + Math.max.apply(null,
                g.etats.map((e) => niveau[e.num] || 0))),
              rompues: colonnes.filter((c) => c.rompue).length,
            };
          });

          affaires.sort((a, b) => b.colonnes.length - a.colonnes.length);
          // ---- UN SEUL PLATEAU EN DÉTAIL ----
          // Trente-six cahiers font 2275 pièces et 1,8 Mo, quand le joueur n'en
          // regarde qu'un. Le détail ne part donc que pour l'affaire demandée ;
          // les autres n'envoient que leur chapeau — de quoi peupler la bascule,
          // les comptes et la bulle du blason. La page redemande la route quand
          // on change de plateau, et le catalogue des missions, lui, reste
          // entier : il sert aux comptes et aux livres.
          const demandee = ((req.url.split("?")[1]) || "").split("&")
            .map((x) => x.split("="))
            .filter((x) => x[0] === "affaire")
            .map((x) => decodeURIComponent(x[1] || ""))[0] || null;
          const ouverte = affaires.find((a) => a.id === demandee) || affaires[0] || null;
          const servies = affaires.map((a) => {
            if (a === ouverte) return a;
            return {
              id: a.id, titre: a.titre, livre_id: a.livre_id, embleme: a.embleme,
              objet: a.objet, missions: a.missions, rechange: a.rechange,
              en_clair: a.en_clair, cites_en_clair: a.cites_en_clair,
              portees: a.portees, divergents: a.divergents,
              nums: a.nums, cites: a.cites,
              idee: a.idee, rompues: a.rompues, colonnes: a.colonnes.length,
              // les pieds d'arbre, pour la bulle du blason : on les calcule ici
              // plutôt que d'envoyer les pièces entières.
              pieds: a.pieces.filter((q) => q.genre === "etat" && !(q.vers || []).length)
                .map((q) => ({ genre: "etat", numero: q.numero, nom: q.nom, cle: q.cle })),
            };
          });
          let aujourdhui = null;
          try {
            aujourdhui = JSON.parse(fs.readFileSync(
              path.join(RACINE, "etat", "monde.json"), "utf-8")).date || null;
          } catch (e) {}
          // LE CATALOGUE EST SERVI À PART, et les pièces ne portent que des
          // adresses d'actes. Un acte réclamé par une action, par sa clef, par
          // son verrou et par trois états ne se sérialise ainsi qu'UNE fois —
          // c'est la même économie que les portraits.
          return envoyer(res, 200, JSON.stringify({
            affaires: servies, ouverte: ouverte ? ouverte.id : null,
            vue_de: moi, brouillons: brouillons,
            collisions: porteePlan.collisions || [],
            pieces_hors_affaire: porteePlan.pieces_hors_affaire || [],
            index_hors_affaire: horsAffaire,
            portraits: portraits, aujourdhui: aujourdhui,
            missions: catalogue }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ affaires: [] }));
        }
      }
      // Vos desseins : la page complète des objectifs, avec ce que la liste du
      // rail ne peut pas porter — l'échéance, le nombre de jours qui reste, et
      // de quelle bouche la chose est venue. Rien d'occulte : ce sont les
      // objectifs du joueur, pas ceux des autres.
      // LES FILS — ce qui court, et qui tient la plume dessus. Par siège, comme
      // la table de guerre : les fils de la reine ne sont pas ceux d'Aurore.
      // Le mode ne change jamais le calcul, seulement par où ça passe (voir
      // docs/fils.md) — donc rien d'occulte ici, ce sont les affaires que le
      // joueur a lui-même sur les bras.
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
      // ---- qui est DEHORS, à la minute -------------------------------------
      // Un homme dépêché (`scripts/depecher.py`) vit sa journée dans sa propre
      // session, avec un budget de minutes. `parloir.ouvrir_instance` pose un
      // fichier dans `etat/parloir/.instances` au départ et le `finally` de la
      // dépêche l'ôte au retour : c'est le seul endroit du jeu qui sache, en
      // temps réel, que cet homme-là est en train de travailler pour de bon.
      //
      // Ce n'est PAS une information de fiction — le personnage ne sait rien du
      // fait qu'on le simule — mais ce n'en est pas une du monde non plus : la
      // pastille dit au joueur « on attend quelqu'un », ce qui est vrai à
      // l'écran et explique pourquoi la salle traîne. Aucune donnée du
      // dossier de l'homme ne descend ici : un id, et le temps qui reste.
      if (url === "/depeches") {
        const dos = path.join(RACINE, "etat", "parloir", ".instances");
        const MINUTES_DEFAUT = 15, MARGE = 90;   // cf. scripts/parloir.py
        const dehors = [];
        try {
          for (const f of fs.readdirSync(dos)) {
            const p = path.join(dos, f);
            let d = {};
            try { d = JSON.parse(fs.readFileSync(p, "utf-8") || "{}"); } catch (e) {}
            const t = (d.t ? d.t * 1000 : fs.statSync(p).mtimeMs);
            const depuis = Math.round((Date.now() - t) / 1000);
            const budget = (d.minutes || MINUTES_DEFAUT) * 60 + MARGE;
            // Périmée : sa session est morte sans que le `finally` passe. On ne
            // purge pas ici — c'est le travail de `parloir.vivants()`, qui écrit
            // et n'est pas une lecture d'affichage — on l'ignore, simplement.
            if (depuis > budget) continue;
            dehors.push({
              id: d.homme || f.split(".")[0],
              depuis, reste: budget - depuis,
            });
          }
        } catch (e) {}
        return envoyer(res, 200, JSON.stringify({ dehors }));
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
      if (url === "/calendrier") {
        try {
          const siege = qui(req, url);
          const aujourdhui = dateDe(siege);
          const moi = (siege && siege.personnage_id) ||
            (() => { try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "journal.json"), "utf-8")).personnage_joueur_id; } catch (e) { return null; } })();
          const p = new URLSearchParams(req.url.split("?")[1] || "");
          const devant = Math.min(30, Math.max(1, parseInt(p.get("jours"), 10) || 8));
          const derriere = 1; // la veille : ce qu'on a manqué se voit encore
          const lire = (f, d) => {
            try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8")); }
            catch (e) { return d; }
          };
          const jour = (d) => d ? ((d.annee || 0) * 12 + ((d.lune || 1) - 1)) * 30 + (d.jour || 0) : null;
          const noms = {};
          (lire("personnages.json", []) || []).forEach((x) => {
            if (x && x.id) noms[x.id] = String(x.nom || x.id).split(",")[0].trim();
          });
          const nommer = (id) => noms[id] || String(id || "").replace(/-/g, " ");

          const j0 = jour(aujourdhui);
          const dedans = (d) => {
            const n = jour(d);
            return n !== null && j0 !== null && n >= j0 - derriere && n <= j0 + devant;
          };
          const entrees = [];
          const entame = (t, n) => {
            const s = String(t || "").replace(/\s+/g, " ").trim();
            return s.length > n ? s.slice(0, n).replace(/\s\S*$/, "") + "…" : s;
          };
          // Un programme n'a pas toujours de `titre` : sa description en tient
          // lieu. On la coupe alors en deux — la tête sert de titre, la suite de
          // détail — au lieu de servir deux fois le même paragraphe.
          const coupe = (e) => {
            const desc = String(e.description || "").replace(/\s+/g, " ").trim();
            if (e.titre) return { titre: e.titre, detail: entame(desc, 240) };
            const tete = entame(desc, 88);
            const reste = desc.slice(tete.replace(/…$/, "").length).trim();
            return { titre: tete, detail: entame(reste, 240) };
          };

          // 1. Les événements où il figure — les rendez-vous, les remises, les
          // rapports promis. `resolu` reste visible sur la veille : un joueur
          // qui se rassoit doit voir ce qui vient de tomber, pas seulement ce
          // qui vient.
          (lire("evenements.json", []) || []).forEach((e) => {
            if (!e || !e.date_prevue || !dedans(e.date_prevue)) return;
            const acteurs = Array.isArray(e.acteurs) ? e.acteurs : [];
            if (!moi || (acteurs.indexOf(moi) < 0 && e.porteur !== moi)) return;
            const st = e.statut || "a-venir";
            if (st === "annule" || st === "devie") return;
            const autres = acteurs.filter((a) => a !== moi).map(nommer);
            const c = coupe(e);
            entrees.push({
              genre: autres.length ? "rendez-vous" : "echeance",
              id: e.id,
              date: e.date_prevue,
              minute: typeof e.date_prevue.minute === "number" ? e.date_prevue.minute : null,
              titre: c.titre,
              detail: c.detail,
              lieu: e.lieu_id || null,
              avec: autres,
              statut: st,
              tenu: st === "resolu",
            });
          });

          // 2. Le courrier qu'on attend — un pli est un rendez-vous avec une
          // date, tenu par un homme qui marche. `attendu_le` est l'heure dite.
          const plis = lire("plis.json", { plis: [] });
          ((plis && plis.plis) || []).forEach((x) => {
            if (!x || !x.attendu_le || !dedans(x.attendu_le)) return;
            const mien = x.pour === moi || x.de === moi;
            if (!mien) return;
            const enRoute = (x.etat || "en-route") === "en-route";
            entrees.push({
              genre: "pli",
              id: x.id,
              date: x.attendu_le,
              minute: typeof x.attendu_le.minute === "number" ? x.attendu_le.minute : null,
              titre: (x.pour === moi ? "Attendu de " + nommer(x.de) : "Doit atteindre " + nommer(x.pour)) +
                (x.canal ? " (" + x.canal + ")" : ""),
              detail: entame(x.porte, 200),
              lieu: x.vers || null,
              avec: [nommer(x.pour === moi ? x.de : x.pour)],
              statut: x.etat || "en-route",
              tenu: !enRoute,
            });
          });

          // 3. Ce qui court et qui a un terme — ses fils, ses desseins. Ni
          // l'un ni l'autre n'a d'heure : ils se posent en tête de journée.
          const fils = lireCroyance("fils.json", siege, null);
          ((fils && fils.fils) || []).forEach((f) => {
            if (!f || !f.echeance || !dedans(f.echeance)) return;
            if ((f.statut || "en-cours") !== "en-cours") return;
            entrees.push({
              genre: "fil", id: f.id, date: f.echeance, minute: null,
              titre: f.titre, detail: entame(f.detail, 200),
              lieu: null, avec: f.sur ? [nommer(f.sur)] : [],
              statut: f.mode === "delegue" ? "delegue" : "joue", tenu: false,
            });
          });
          const miens = lireCroyance("objectifs.json", siege, []);
          (Array.isArray(miens) ? miens : []).forEach((o) => {
            if (!o || !o.echeance || !dedans(o.echeance)) return;
            if ((o.statut || "en-cours") !== "en-cours") return;
            entrees.push({
              genre: "dessein", id: o.id, date: o.echeance, minute: null,
              titre: o.titre, detail: entame(o.description, 200),
              lieu: null, avec: [], statut: "en-cours", tenu: false,
            });
          });

          // 4. LE SQUELETTE DE LA JOURNÉE — sa routine, résolue comme le fait
          // presence.py : les bandes du modèle, @dortoir et @poste remplacés.
          // Ce n'est pas un rendez-vous, c'est le fond sur lequel les autres
          // se posent : une heure déjà fermée n'est pas une heure libre.
          let bandes = [];
          try {
            const r = lire("routines.json", {});
            const fiche = (r.gens || {})[moi] || null;
            const modele = fiche && (r.modeles || {})[fiche.modele];
            if (modele) {
              const dortoir = fiche.dortoir || modele.dortoir || null;
              const poste = fiche.poste || modele.poste || null;
              bandes = (modele.bandes || []).map((b) => {
                const jeton = b.salle === "@dortoir" ? dortoir : b.salle === "@poste" ? poste : null;
                return {
                  de: b.de, a: b.a,
                  salle: jeton ? jeton.salle : b.salle,
                  lieu: b.lieu || (jeton ? jeton.lieu : null),
                  ferme: b.ferme === true,
                };
              });
            }
          } catch (e) {}

          entrees.sort((a, b) => (jour(a.date) - jour(b.date)) ||
            ((a.minute === null ? -1 : a.minute) - (b.minute === null ? -1 : b.minute)));
          const jours = [];
          for (let k = -derriere; k <= devant; k++) {
            const n = j0 + k;
            const d = {
              annee: Math.floor(n / 360),
              lune: Math.floor((n % 360) / 30) + 1,
              jour: n % 30,
            };
            // le jour 0 d'une lune est le 30e de la précédente
            if (d.jour === 0) { d.jour = 30; d.lune -= 1; if (d.lune === 0) { d.lune = 12; d.annee -= 1; } }
            jours.push({
              date: d, ecart: k,
              entrees: entrees.filter((x) => jour(x.date) === n),
            });
          }
          // Ses mémos — ce que le joueur a lui-même écrit dans les cases.
          // Hors fiction : voir POST /agenda.
          let notes = [];
          try {
            const a = lireCroyance("agenda.json", siege, null);
            notes = (a && Array.isArray(a.notes) ? a.notes : []).filter((n) => n && dedans(n.date));
          } catch (e) {}
          return envoyer(res, 200, JSON.stringify({
            aujourdhui, moi, nom: moi ? nommer(moi) : null, bandes, jours, notes,
          }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ jours: [], aujourdhui: null, bandes: [] }));
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
            // LA RÉGIE VOIT TOUT, et c'est sa seule raison d'être. Le tri par
            // `pour` protège un joueur de ce que l'autre entend ; Corneille
            // n'est pas un joueur — il n'a ni tête, ni horloge, ni siège dans
            // la fiction, et un fil amputé ne lui servirait à rien. Le jeton
            // reste la serrure : sans lui, on n'est toujours personne. La
            // fenêtre et le `?avant=` ci-dessous s'appliquent comme pour tous.
            if (j && j.regie) items = items.slice();
            else {
            // Sans jeton, on n'est personne — et personne ne lit la partie.
            // Le filtre par `pour` ne suffit pas : l'immense majorite du flux
            // n'en porte aucun, donc un inconnu recevait l'histoire entiere.
            // Le jeton n'est pas qu'un siege, c'est la serrure : le jeu est
            // servi par un tunnel public, et une URL nue circule vite.
            if (!j) return envoyer(res, 200, JSON.stringify({ items: [] }));
            // Le point d'entree du siege. Un item sans `pour` est PUBLIC — ce
            // qui est juste pour la suite, et faux pour l'avant : tout
            // l'historique anterieur a l'arrivee d'un joueur n'en porte aucun,
            // et son navigateur rejouerait donc la partie entiere d'un autre.
            // On ne reecrit pas le flux pour autant (il est append-only) : on
            // coupe a la ligne ou ce joueur est entre a la table.
            const depuis = (j && j.depuis) || 0;
            if (depuis) items = items.slice(depuis);
            // `pour` peut porter PLUSIEURS oreilles : c'est la messe basse, ce
            // que deux personnes se disent a l'ecart dans une salle qui en
            // compte six. Un tableau n'est ni public ni prive a une seule
            // oreille, et il ne doit surtout pas retomber dans le cas « pas de
            // pour » — qui, lui, veut dire que tout le monde entend.
            // UN ITEM SANS `pour` N'EST PLUS PUBLIC PASSÉ L'ÈRE MULTI-JOUEURS.
            // C'est le verrou de lecture, et il ferme la faille par en bas :
            // même si un jour une plume réécrit un item sans audience — un
            // script à venir, une main dans le fichier —, il ne partira chez
            // personne au lieu de partir chez tout le monde.
            //
            // Le seuil se calcule tout seul : la ligne où le DERNIER joueur
            // s'est assis. Avant elle, un `pour` absent veut dire « il n'y
            // avait qu'une table » et reste lisible par les anciens (leur
            // propre `depuis` fait déjà le tri). Après elle, un `pour` absent
            // est un bug, et un bug ne se diffuse pas.
            const seuil = roster().reduce((m, j) => Math.max(m, j.depuis || 0), 0);
            items = items.filter((it, k) => it.pour
              ? (Array.isArray(it.pour) ? it.pour.indexOf(moi) !== -1 : it.pour === moi)
              : depuis + k < seuil);
            }
          }
          // Le flux est append-only et ne cesse de grossir : au bout de
          // quelques heures de partie, chaque sondage retransmet des milliers
          // de lignes et le navigateur rejoue tout au rechargement. On ne sert
          // donc qu'une FENÊTRE. `debut` dit combien de lignes ont été coupées
          // en tête et `total` la longueur réelle du fil : le curseur du client
          // reste ainsi compté sur le flux entier — sinon la fenêtre glissant à
          // chaque nouvel item, le neuf ne serait jamais vu.
          //
          // `?avant=N` remonte le temps : la page qui précède l'index N, servie
          // quand le joueur fait défiler la chronique vers le haut. Le passé
          // descend alors par tranches, à la demande, et jamais d'un bloc.
          const total = items.length;
          const q = (req.url.split("?")[1] || "").match(/(?:^|&)avant=(\d+)/);
          let fin = q ? Math.min(Number(q[1]), total) : total;
          if (!(fin >= 0)) fin = total;
          const debut = Math.max(0, fin - MAX_FIL);
          items = items.slice(debut, fin);
          // Un volume montré en scène : sa page peut être un dessin. Le flux
          // n'en garde que le NOM — un levé pèse deux cent mille signes, et
          // trente lignes qui le portent feraient un fil illisible à charger.
          // Le nom est empreinté (voir append_flux.py) : la feuille de ce
          // jour-là ne bouge plus, même si le dessin est refait demain.
          items.forEach((it) => {
            if (it.montre && it.montre.extrait) inlinerFigure(it.montre.extrait);
            rafraichirPortraits(it);
          });
          return envoyer(res, 200, JSON.stringify({ items, debut, total, ecart: ecartDe(qui(req, url)) }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ items: [], debut: 0 }));
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
          const r = await voix.dire(d.locuteur_id, d.texte, d.client_id, d.rejouer);
          if (r.audio) return envoyer(res, 200, r.audio, r.mime || "audio/mpeg");
          return envoyer(res, r.code, JSON.stringify({ erreur: r.erreur }));
        } catch (e) {
          return envoyer(res, 500, JSON.stringify({ erreur: String(e) }));
        }
      });
      return;
    }
    // Le journal de la foule : la page d'essai y verse les CHANGEMENTS d'état
    // qu'elle a vus passer (untel part vers le puits, untel y arrive, untel
    // rentre). Une ligne JSON par changement, en append — jamais une position
    // par image, ce serait des millions de lignes qui ne disent rien.
    //
    // Ça n'entre pas dans `etat/` : ce n'est pas de la partie, c'est de la
    // mesure. Un fichier par session de page, dans monde/journaux/.
    if (req.method === "POST" && url === "/foule/journal") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", () => {
        try {
          const { lignes } = JSON.parse(corps);
          if (!Array.isArray(lignes)) throw new Error("lignes");
          const dossier = path.join(RACINE, "monde", "journaux");
          fs.mkdirSync(dossier, { recursive: true });
          const nom = "foule-" + new Date().toISOString().slice(0, 13)
            .replace(/[-T:]/g, "") + ".jsonl";
          const texte = lignes.map((l) => JSON.stringify(l) + "\n").join("");
          fs.appendFileSync(path.join(dossier, nom), texte, "utf-8");
          return envoyer(res, 200, JSON.stringify(
            { ecrit: lignes.length, fichier: "monde/journaux/" + nom }));
        } catch (e) {
          return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
        }
      });
      return;
    }

    // Le joueur écrit dans ses notes : on garde la chaîne TELLE QUELLE, sans
    // la lire, sans la relire au MJ, sans la faire entrer dans la partie. Une
    // écriture complète à chaque fois — c'est un carnet, pas un journal
    // d'événements, et le navigateur en est seul propriétaire.
    // ÉCRIRE DANS UNE CASE DU CALENDRIER — c'est LE JOUEUR qui tient la plume,
    // et ce qu'il écrit compte.
    //
    // Ce que ça n'est pas : une parole, un acte, une minute dépensée. Écrire
    // dans son propre calendrier ne se fait devant personne — aucun PNJ ne
    // l'entend, l'horloge ne bouge pas, rien n'entre dans `paroles.json` ni
    // dans `actes.json`. Le texte vit dans `etat/joueurs/<siège>/agenda.json`
    // (technique, hors docs/schema.md).
    //
    // Ce que ça EST, et c'est le point : une case écrite TOMBE DANS L'INBOX du
    // siège, comme n'importe quelle action. Le guetteur du MJ sonne, il la lit,
    // et c'est à lui de la porter dans le monde — l'homme qu'on fait chercher,
    // le `programme` daté, le pli qui part. Un calendrier que le MJ ne voit pas
    // n'est pas un calendrier, c'est un pense-bête ; et le joueur qui inscrit
    // « voir Rulf à sept heures » a le droit qu'on le lui tienne.
    // UNE VUE DE LA CARTE, POUR QUE LE MJ VOIE CE QUI SE PASSE.
    //
    // Pendant une bataille, il est aveugle au seul moment où ça compte. Il a
    // l'état et les annales du sac — mais où la ligne a cédé, de quel côté la
    // panique court, quelle rue bouchonne, à combien de pas de la porte est
    // l'homme qu'on lui fait jouer : ça se voit d'un coup d'œil et ça se
    // raconte mal. La page compose donc régulièrement le plan, la foule et la
    // bataille en une image centrée sur le joueur, et la dépose ici.
    //
    // UN CHEMIN STABLE, ET UN MOT DANS L'INBOX. `etat/vues/<siège>.png` est
    // écrasé à chaque fois — c'est un miroir posé sur la table, toujours à la
    // même place. Mais un miroir que personne ne regarde ne sert à rien : le
    // MJ ne va pas ouvrir un fichier dont rien ne lui dit qu'il a changé. On
    // dépose donc aussi, comme pour toute action du joueur, une entrée dans
    // `etat/inbox/<siège>/` qui porte le CHEMIN et la légende. Son guetteur
    // sonne, il ouvre l'image, il voit la bataille.
    //
    // L'ENTRÉE PORTE LE LIEN, JAMAIS L'IMAGE. Quarante kilo-octets de base64
    // par ping rendraient l'inbox illisible, et le MJ lit ses fichiers d'un
    // bloc : il n'a besoin que de savoir où regarder.
    //
    // Le rythme est celui des captures (`CADENCE` dans `capture.js`) : si le
    // guetteur sonne trop souvent au goût du MJ, c'est là qu'on l'espace, pas
    // ici. Et comme le MJ lit TOUS ses fichiers d'inbox en une fois, plusieurs
    // pings accumulés pendant qu'il écrivait se lisent ensemble — seul le
    // dernier compte, puisque le PNG est le même fichier écrasé.
    //
    // La légende est écrite À CÔTÉ, en JSON, et pas dessinée dans l'image :
    // une échelle et une heure incrustées dans des pixels ne se citent pas,
    // alors qu'un `metres_par_pixel` se relit et se calcule.
    if (req.method === "POST" && url === "/vue") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", () => {
        try {
          const { image, meta } = JSON.parse(corps);
          const m = /^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$/
            .exec(image || "");
          if (!m) throw new Error("ce n'est pas une image png, jpeg ou webp");
          const ext = m[1] === "jpeg" ? "jpg" : m[1];
          const siege = qui(req, url);
          const nom = (siege && siege.personnage_id) || "sans-siege";
          const dossier = path.join(RACINE, "etat", "vues");
          fs.mkdirSync(dossier, { recursive: true });
          const octets = Buffer.from(m[2], "base64");
          // Une borne, parce qu'un client peut poster ce qu'il veut. Une vue
          // compressée pèse une dizaine de kilo-octets ; au-delà d'un méga,
          // c'est autre chose et l'on n'en veut pas.
          if (octets.length > 1048576) throw new Error("vue trop lourde");

          // UNE ROTATION DE DIX, PAS UN FICHIER ÉCRASÉ. Une bataille se lit
          // dans son MOUVEMENT — la ligne qui recule de trente mètres entre
          // deux vues dit ce qu'aucune vue seule ne dit. Dix vues à trente
          // secondes font cinq minutes de recul, et à dix kilo-octets pièce
          // c'est cent kilo-octets en tout : moins qu'une seule vue en PNG.
          const GARDE = 10;
          const fichier = nom + "-" + Date.now() + "." + ext;
          fs.writeFileSync(path.join(dossier, fichier), octets);
          // L'index d'abord, le ménage ensuite : on ne supprime un fichier
          // qu'après avoir écrit la liste qui ne le mentionne plus, sinon un
          // MJ qui lit entre les deux ouvre un chemin qui n'existe déjà plus.
          const jindex = path.join(dossier, nom + ".json");
          let vues = [];
          try { vues = JSON.parse(fs.readFileSync(jindex, "utf-8")).vues || []; }
          catch (e) {}
          vues.unshift({
            fichier: "etat/vues/" + fichier,
            octets: octets.length,
            ...(meta && typeof meta === "object" ? meta : {}),
          });
          const jetees = vues.slice(GARDE);
          vues = vues.slice(0, GARDE);
          fs.writeFileSync(jindex, JSON.stringify({
            _: "Les " + GARDE + " dernières vues de la carte envoyées par la " +
               "page de ce siège, la plus RÉCENTE en tête. Une toutes les " +
               "trente secondes tant qu'une bataille est dressée ; le guetteur " +
               "sonne à chaque fois. Ouvrez `vues[0].fichier` pour voir où l'on " +
               "en est, et les suivantes pour voir d'où l'on vient.",
            vues,
          }, null, 2), "utf-8");
          for (const v of jetees) {
            try { fs.unlinkSync(path.join(RACINE, v.fichier)); } catch (e) {}
          }
          // Le guetteur du MJ sonne, comme pour toute action du joueur.
          try {
            const boite = siege
              ? path.join(RACINE, "etat", "inbox", siege.personnage_id)
              : path.join(RACINE, "etat", "inbox");
            fs.mkdirSync(boite, { recursive: true });
            const m = (meta && typeof meta === "object") ? meta : {};
            fs.writeFileSync(path.join(boite, "action-" + Date.now() + ".json"),
              JSON.stringify({
                type: "vue",
                fichier: "etat/vues/" + fichier,
                index: "etat/vues/" + nom + ".json",
                montre: m.montre || null,
                heure: m.heure || null,
                large_en_metres: m.large_en_metres || null,
                metres_par_pixel: m.metres_par_pixel || null,
                couches: m.couches || null,
                bataille: m.bataille || null,
                joueur_id: siege ? siege.personnage_id : null,
                recu_a: new Date().toISOString(),
                _: "Une vue de la carte, centrée sur le joueur, telle qu'il " +
                   "l'a sous les yeux. OUVREZ LE FICHIER : c'est une image, " +
                   "et elle dit d'un coup d'œil ce que trois cents lignes de " +
                   "relevé disent mal — où la ligne a cédé, de quel côté la " +
                   "panique court, à combien de pas de la porte il se tient. " +
                   "Hors fiction : ce n'est ni une parole, ni un acte, ni une " +
                   "minute. Rien à écrire dans l'état, rien à répondre au " +
                   "joueur — c'est pour VOS yeux. Les dix dernières vues sont " +
                   "gardées en rotation et listées dans `index`, la plus " +
                   "récente en tête : les précédentes disent le MOUVEMENT, " +
                   "c'est-à-dire de quel côté ça se déplace, ce qu'une vue " +
                   "seule ne peut pas dire.",
              }, null, 2), "utf-8");
          } catch (e) { /* l'image est écrite : le ping n'est pas vital */ }
          return envoyer(res, 200, JSON.stringify(
            { ecrit: "etat/vues/" + fichier, octets: octets.length,
              gardees: vues.length }));
        } catch (e) {
          return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
        }
      });
      return;
    }

    // UNE MARQUE DE DEBUG DE LA BATAILLE. Elle n'entre ni dans la fiction ni
    // dans l'état canonique : c'est un paquet de preuve laissé par le joueur à
    // ceux qui travaillent sur le moteur. Un dossier autonome contient la
    // capture, le commentaire lisible et toutes les données structurées.
    if (req.method === "POST" && url === "/marque-bataille") {
      // Les pages récentes bornent déjà la chronologie. La marge supérieure
      // permet toutefois de sauver une marque produite par un onglet resté
      // ouvert avant ce correctif : le serveur la reçoit, puis garde sa FIN.
      // Au-delà, on cesse réellement d'accumuler le corps en mémoire.
      let corps = "", trop = false, recus = 0;
      req.on("data", (c) => {
        recus += c.length;
        if (recus > 32 * 1024 * 1024) { trop = true; corps = ""; }
        else if (!trop) corps += c;
      });
      req.on("end", () => {
        try {
          if (trop) throw new Error("marque trop lourde");
          const doc = JSON.parse(corps);
          const commentaire = String(doc.commentaire || "").trim();
          if (!commentaire) throw new Error("commentaire vide");
          if (commentaire.length > 8000) throw new Error("commentaire trop long");
          if (!doc.diagnostic || typeof doc.diagnostic !== "object")
            throw new Error("diagnostic manquant");
          // Défense en profondeur pour les anciens clients et les outils qui
          // postent directement. La chronologie est la seule partie sans
          // borne naturelle. On la réduit en partant du dernier item et on
          // laisse une preuve chiffrée de ce qui a été omis.
          const historique = Array.isArray(doc.diagnostic.historique_perceptions)
            ? doc.diagnostic.historique_perceptions : [];
          const metaAvant = doc.diagnostic.historique_perceptions_meta || {};
          const MAX_HISTORIQUE = 512 * 1024;
          let debut = historique.length, octetsHistorique = 2;
          while (debut > 0) {
            const taille = Buffer.byteLength(JSON.stringify(historique[debut - 1]), "utf8") +
              (debut < historique.length ? 1 : 0);
            if (octetsHistorique + taille > MAX_HISTORIQUE &&
                debut < historique.length) break;
            octetsHistorique += taille; debut--;
          }
          const historiqueConserve = historique.slice(debut);
          const totalHistorique = Math.max(historique.length,
            Number(metaAvant.total) || 0,
            historique.length + (Number(metaAvant.omis) || 0));
          const metaHistorique = Object.assign({}, metaAvant, {
            politique: "fin-conservee",
            total: totalHistorique,
            conserve: historiqueConserve.length,
            omis: Math.max(0, totalHistorique - historiqueConserve.length),
            octets_json: octetsHistorique,
            debut_conserve_s: historiqueConserve.length
              ? historiqueConserve[0].temps : null,
            fin_conservee_s: historiqueConserve.length
              ? historiqueConserve[historiqueConserve.length - 1].temps : null,
          });
          doc.diagnostic.historique_perceptions = historiqueConserve;
          doc.diagnostic.historique_perceptions_meta = metaHistorique;
          const m = /^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$/
            .exec(doc.image || "");
          if (!m) throw new Error("capture absente ou invalide");
          const octets = Buffer.from(m[2], "base64");
          if (octets.length > 2 * 1024 * 1024) throw new Error("capture trop lourde");
          const ext = m[1] === "jpeg" ? "jpg" : m[1];
          const brutId = doc.diagnostic.combattant && doc.diagnostic.combattant.id || "homme";
          const id = String(brutId).replace(/[^a-zA-Z0-9_-]/g, "-").slice(0, 60) || "homme";
          const iso = new Date().toISOString();
          const horodatage = iso.replace(/[:.]/g, "-");
          const racine = path.join(RACINE, "captures", "bataille-marques");
          const nomDossier = horodatage + "-" + id;
          const dossier = path.join(racine, nomDossier);
          fs.mkdirSync(dossier, { recursive: true });
          const imageNom = "zone." + ext;
          fs.writeFileSync(path.join(dossier, imageNom), octets);
          const rapport = {
            format: "marque-bataille/v1", cree_a: iso,
            commentaire, lieu: doc.lieu || null, capture: imageNom,
            meta_capture: doc.meta || null, diagnostic: doc.diagnostic,
          };
          fs.writeFileSync(path.join(dossier, "rapport.json"),
            JSON.stringify(rapport, null, 2), "utf-8");
          const h = doc.diagnostic.combattant || {};
          const p = h.pensee || {};
          const md = [
            "# Marque de bataille — " + (h.nom || h.id || "combattant"), "",
            "## Commentaire", "", commentaire, "",
            "## Instant", "",
            "- Créée : " + iso,
            "- Temps de bataille : " + (doc.diagnostic.temps_bataille_s ?? "?") + " s",
            "- Position : " + (doc.lieu && doc.lieu.texte ||
              (h.position ? h.position.x + ", " + h.position.y : "inconnue")),
            "- État : " + (h.etat || "?"),
            "- Pensée : j'essaie de " + (p.action || "?") + " parce que " + (p.raison || "?"),
            "- Système : " + (p.systeme || "?"),
            "- Historique : " + metaHistorique.conserve + " perceptions récentes conservées sur " +
              metaHistorique.total + " (fin préservée" +
              (metaHistorique.omis ? ", " + metaHistorique.omis + " anciennes omises" : "") + ")", "",
            "## Fichiers", "",
            "- `rapport.json` : chronologie perceptive et calculs complets",
            "- `" + imageNom + "` : zone au moment du clic, combattant cerclé", "",
            "![zone marquée](" + imageNom + ")", "",
          ].join("\n");
          fs.writeFileSync(path.join(dossier, "LISEZ-MOI.md"), md, "utf-8");

          fs.mkdirSync(racine, { recursive: true });
          const indexPath = path.join(racine, "index.json");
          let marques = [];
          try { marques = JSON.parse(fs.readFileSync(indexPath, "utf-8")).marques || []; }
          catch (e) {}
          marques.unshift({ dossier: nomDossier, cree_a: iso, combattant: h.nom || h.id,
                            commentaire, temps_bataille_s: doc.diagnostic.temps_bataille_s });
          fs.writeFileSync(indexPath, JSON.stringify({
            _: "Marques de debug déposées depuis la carte, la plus récente en tête.",
            marques,
          }, null, 2), "utf-8");
          return envoyer(res, 200, JSON.stringify({
            ecrit: "captures/bataille-marques/" + nomDossier,
            rapport: "captures/bataille-marques/" + nomDossier + "/rapport.json",
            capture: "captures/bataille-marques/" + nomDossier + "/" + imageNom,
            octets: octets.length,
            historique: metaHistorique,
          }));
        } catch (e) {
          return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
        }
      });
      return;
    }

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
    if (req.method === "POST" && url === "/piece") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", () => {
        try {
          const d = JSON.parse(corps);
          const sessionLivres = bibliotheque.ouvrir(RACINE);
          const livres = sessionLivres.livres;
          const nu = (t) => String(t == null ? "" : t).replace(/\*\*/g, "")
            .replace(/\s+/g, " ").trim();
          // les emblemes sortent du nom de colonne : au-dela de U+2000 il n'y a
          // plus de lettre francaise, seulement des signes et des paires hautes
          const sansEmoji = (t) => nu(t).replace(/[\u2000-\uFFFF]/g, "").trim();
          const GENRES = { etat: /états? cibles?/i, verrou: /verrous?/i,
                           clef: /clefs?/i, action: /actions?/i };
          const REGISTRE = { etat: "plan-etats-cibles", verrou: "plan-verrous",
                             clef: "plan-clefs", action: "plan-actions" };
          const PARENT = { etat: /sert/i, verrou: /bloque/i, clef: /ouvre/i,
                           action: /réalise|realise/i };
          if (!GENRES[d.genre]) throw new Error("forme inconnue : " + d.genre);
          if (!nu(d.texte)) throw new Error("une pièce sans nom ne se porte pas");
          if (d.genre !== "etat" && !/^\d{3,6}$/.test(String(d.parent || "").trim()))
            throw new Error("il faut le numéro de ce qu'elle sert");

          const aff = livres.find((b) => b.id === d.affaire);
          if (!aff || !Array.isArray(aff.tables)) throw new Error("affaire inconnue");

          // la plage, prise à la ligne LA PLAGE de l'ouverture
          let plage = 0;
          (aff.tables[0].lignes || []).forEach((l) => {
            const c = (l.cellules || []).map(nu);
            if (/LA PLAGE/i.test(sansEmoji(c[0] || ""))) {
              const m = (c[1] || "").match(/\d{3,6}/);
              if (m) plage = +m[0];
            }
          });
          // repli sur le sous-titre : un cahier vierge porte sa plage là, et la
          // case de l'ouverture n'est remplie qu'à l'ouverture de l'affaire.
          if (!plage) {
            const m = String(aff.sous_titre || "").match(/[Pp]lage\s+(\d{3,6})/);
            if (m) plage = +m[1];
          }
          if (!plage) throw new Error("cette affaire n'a pas de plage : ni dans " +
            "son ouverture, ni dans son sous-titre");

          // tout ce qui est déjà pris, dans l'affaire comme dans les registres
          const pris = new Set();
          livres.forEach((b) => (b.tables || [{ colonnes: b.colonnes, lignes: b.lignes }])
            .forEach((t) => (t.lignes || []).forEach((l) => {
              const c = (l.cellules || l || []).map(nu);
              const m = (c[0] || "").match(/^\d{3,6}$/);
              if (m) pris.add(+m[0]);
            })));

          let num = 0;
          if (d.genre === "etat") {
            for (let n = plage; n < plage + 1000; n += 100) if (!pris.has(n)) { num = n; break; }
          } else {
            const base = Math.floor(+d.parent / 100) * 100;
            const bornes = { verrou: [1, 9], clef: [10, 19], action: [20, 99] }[d.genre];
            for (let i = bornes[0]; i <= bornes[1]; i++)
              if (!pris.has(base + i)) { num = base + i; break; }
          }
          if (!num) throw new Error("plus de numéro libre pour cette forme");

          // la ligne, remplie par NOM de colonne : les tableaux n'ont pas tous
          // les mêmes, et un remplissage par rang écrirait de travers
          const valeurs = [
            [/^n°$/i, "**" + num + "**"],
            [PARENT[d.genre], d.parent ? String(d.parent) : "—"],
            [/office/i, nu(d.office) || (d.genre === "action" ? "**SANS OFFICE**" : "")],
            [/moyens/i, nu(d.moyens)],
            [/affaire/i, nu(aff.titre)],
          ];
          const ligne = (cols) => cols.map((c, i) => {
            if (i === 1) return nu(d.texte);
            const t = sansEmoji(c);
            const v = valeurs.find((x) => x[0].test(t));
            return v ? v[1] : "";
          });

          const dans = (livre) => {
            const t = (livre.tables || []).find((x) => GENRES[d.genre].test(sansEmoji(x.titre)));
            if (!t) return false;
            t.lignes = (t.lignes || []).filter((l) =>
              (l.cellules || []).some((c) => nu(c)));   // on chasse les lignes vides du patron
            t.lignes.push({ cellules: ligne(t.colonnes || []) });
            return true;
          };
          if (!dans(aff)) throw new Error("l'affaire n'a pas de tableau pour cette forme");
          const reg = livres.find((b) => b.id === REGISTRE[d.genre]);
          if (reg) {
            reg.lignes = reg.lignes || [];
            reg.lignes.push({ cellules: ligne(reg.colonnes || []) });
          }
          sessionLivres.sauver();
          return envoyer(res, 200, JSON.stringify({ num: String(num), affaire: nu(aff.titre) }));
        } catch (e) {
          return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
        }
      });
      return;
    }

    // Basculer un fil : le mode s'écrit tout de suite dans `fils.json` (sinon le
    // rail mentirait au rechargement), ET l'intention tombe dans l'inbox du
    // siège. Le clic ne JOUE rien — il dit ce que le joueur veut ; c'est au MJ
    // d'en tirer le mandat écrit et la scène qui va avec.
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
    if (req.method === "POST" && url === "/ou") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", () => {
        try {
          const p = JSON.parse(corps);
          const siege = qui(req, url);
          const pid = siege && siege.personnage_id;
          const x = +p.x, y = +p.y;
          if (!pid) return envoyer(res, 200, JSON.stringify({ ok: false, erreur: "sans siège" }));
          if (!isFinite(x) || !isFinite(y))
            return envoyer(res, 400, JSON.stringify({ erreur: "x/y" }));
          const f = path.join(RACINE, "etat", "corps.json");
          let L = { liens: {}, affectations: {} };
          try { L = JSON.parse(fs.readFileSync(f, "utf-8")); } catch (e) {}
          L.affectations = L.affectations || {};
          const cle = "personnage:" + pid;
          // ON FUSIONNE au lieu de remplacer : l'entrée peut porter un `nom`,
          // une `note` ou un `visible` qu'on n'a aucune raison d'effacer parce
          // que quelqu'un a fait trois pas.
          const avant = L.affectations[cle] || {};
          L.affectations[cle] = Object.assign({}, avant, {
            xyz: [Math.round(x * 10) / 10, Math.round(y * 10) / 10, 0],
            // LE PRÉFIXE, PAS L'IDENTIFIANT DE LIEU. `affecter.py` et
            // `bati.py` cherchent `monde/<monde>.bati.json` : écrire
            // « port-real » leur fait chercher un fichier qui n'existe pas,
            // et l'affectation devient illisible pour tout ce qui la relit.
            // C'est la même prise que `/marche` deux cents lignes plus bas.
            monde: (LIEUX3D[p.lieu || LIEU3D_DEFAUT] || {}).prefixe ||
                   p.lieu || LIEU3D_DEFAUT,
            note: p.note || avant.note || "en marche",
          });
          fs.writeFileSync(f, JSON.stringify(L, null, 2), "utf-8");
          return envoyer(res, 200, JSON.stringify({ ok: true }));
        } catch (e) {
          return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) }));
        }
      });
      return;
    }
    if (req.method === "POST" && url === "/marche") {
      let corps = "";
      req.on("data", (c) => (corps += c));
      req.on("end", () => {
        try {
          const p = JSON.parse(corps);
          const siege = qui(req, url);
          const pid = siege ? siege.personnage_id : null;
          const lieu = p.lieu || LIEU3D_DEFAUT;
          const x = +p.x, y = +p.y;
          if (!isFinite(x) || !isFinite(y))
            return envoyer(res, 400, JSON.stringify({ erreur: "x/y" }));
          const minutes = Math.max(0, +p.minutes || 0);
          const fichier = (f) => path.join(RACINE, "etat", f);
          const lire = (f, d) => {
            try { return JSON.parse(fs.readFileSync(fichier(f), "utf-8")); }
            catch (e) { return d; }
          };
          const ecrire = (f, o) =>
            fs.writeFileSync(fichier(f), JSON.stringify(o, null, 2), "utf-8");

          // 1. LA MONTRE. Marcher coûte des minutes ; elles se paient sur
          // l'horloge du siège ET sur celle du monde, qui suit toujours la
          // plus avancée (voir « UNE SEULE NUIT, UNE SEULE HEURE »).
          const monde = lire("monde.json", null);
          const horloges = lire("horloges.json", {});
          const avancer = (d, min) => {
            if (!d) return d;
            let m = (d.minute || 0) + min;
            let j = d.jour || 1, l = d.lune || 1, a = d.annee || 0;
            while (m >= 1440) { m -= 1440; j += 1; }
            while (j > 30) { j -= 30; l += 1; }
            while (l > 12) { l -= 12; a += 1; }
            return { annee: a, lune: l, jour: j, minute: Math.round(m) };
          };
          // LES SECONDES NE SE PERDENT PAS. Vingt mètres coûtent un quart de
          // minute : arrondi à chaque tronçon, une balade d'un kilomètre ne
          // coûterait RIEN du tout — cinquante fois zéro. On garde donc le
          // reste en mémoire, siège par siège, et l'horloge n'avance que
          // lorsqu'une minute entière a été marchée. Ce reste n'est pas de
          // l'état : le perdre au redémarrage coûte moins d'une minute.
          let date = null;
          const du = minutes + (_resteMarche[pid || "?"] || 0);
          const entieres = Math.floor(du);
          _resteMarche[pid || "?"] = du - entieres;
          if (pid && entieres > 0) {
            horloges[pid] = avancer(horloges[pid] || (monde && monde.date), entieres);
            date = horloges[pid];
            ecrire("horloges.json", horloges);
          } else if (pid) {
            date = horloges[pid] || (monde && monde.date);
          }
          if (monde && entieres > 0) {
            const apres = avancer(monde.date, minutes);
            // le monde ne recule jamais : si l'autre siège est plus avancé,
            // c'est lui qui fait foi.
            const clef = (d) => ((d.annee * 12 + d.lune) * 30 + d.jour) * 1440 + d.minute;
            if (!date || clef(apres) > clef(date)) monde.date = apres;
            else monde.date = date;
            ecrire("monde.json", monde);
          }

          // 2. OÙ L'ON EST — en mètres, et en clair. Les mètres vont dans les
          // affectations (`corps.json`), qui sont le seul endroit du jeu où
          // une chose de la fiction a une adresse physique ; le clair va dans
          // `presence.lieu`, qui est ce que le bandeau affiche. On NE TOUCHE
          // PAS à `presence.salle` : les salles nommées sont la topologie de
          // `chemins.json`, et une rue de la ville n'en est pas une — écrire
          // un id inventé ferait mentir tout ce qui lit cette table.
          // Ce que la partie a déjà baptisé, par rang de bâtiment. Une seule
          // lecture de `corps.json` sert à ça et à l'écriture de la position.
          const corpsJson = lire("corps.json", { liens: {}, affectations: {} });
          corpsJson.affectations = corpsJson.affectations || {};
          const nommes = new Map();
          for (const cle in corpsJson.affectations) {
            const a = corpsJson.affectations[cle];
            // PAS DE NOM, PAS DE NOM — on ne se rabat SURTOUT pas sur la clef.
            // Une affectation sans `nom` rendait « devant
            // lieu:place-du-puits-culpucier », c'est-à-dire un identifiant nu
            // dans une phrase que le joueur lit au bandeau (elle part dans
            // `presence.lieu`) et que le MJ reçoit dans son sac. Sans nom, on
            // laisse le métier parler : « devant un puits » est vrai, lisible,
            // et n'invente rien. Le jour où quelqu'un baptise l'endroit
            // (`affecter.py --nom`), il reprend son nom tout seul.
            if (a && a.bat != null) nommes.set(a.bat, { cle, nom: a.nom || null });
          }
          const autour = batiAutour(lieu, x, y, 45, 4, nommes);
          const pres = repereProche(lieu, x, y);
          // Devant chez quelqu'un, on dit chez qui — pas ce que c'est.
          const devant = autour.connus[0] || autour.gros;
          // « de » S'ÉLIDE, et cette phrase-là est sous les yeux du joueur : elle
          // va dans `presence.lieu`, c'est-à-dire dans le bandeau, et dans le sac
          // que lit le MJ. Les repères portent leur article — « Le Donjon Rouge »,
          // « La porte de Fer » —, d'où « à 263 pas de La porte de Fer » tant
          // qu'on collait « de » devant sans regarder.
          // `les` AVANT `le` dans l'alternation : une regex essaie ses branches
          // de gauche à droite, et « le » mordait dans « Les casernes » — d'où
          // « du s casernes du guet ». C'est la faute qu'on ne voit qu'en
          // essayant les vrais noms de la table.
          const dePlace = (nom) => {
            const s = String(nom || "").trim();
            const m = s.match(/^(les|la|le|l')\s*/i);
            // Pas d'article du tout : « de » s'élide quand même devant voyelle.
            if (!m) return (/^[aeiouyàâéèêîïôöûü]/i.test(s) ? "d'" : "de ") + s;
            const reste = s.slice(m[0].length);
            const a = m[1].toLowerCase();
            return (a === "le" ? "du " : a === "les" ? "des " :
                    a === "la" ? "de la " : "de l'") + reste;
          };
          const dit = (pres ? "À " + pres.a + " pas " + dePlace(pres.nom) : "Dans la ville") +
            (devant ? ", devant " + (devant.nom || metier(devant.usage)) : "");
          if (pid) {
            // Le MONDE d'une affectation est le préfixe du bâti engendré
            // (`portreal`), jamais l'id du lieu (`port-real`) : `affecter.py`
            // ouvre `monde/<monde>.bati.json`, et écrire l'id du lieu ici
            // faisait planter la liste des affectations sur un fichier absent.
            const pref = (LIEUX3D[lieu] && LIEUX3D[lieu].prefixe) || lieu;
            corpsJson.affectations["personnage:" + pid] = {
              xyz: [Math.round(x * 10) / 10, Math.round(y * 10) / 10, 0],
              monde: pref, note: p.fin ? "arrivé" : "en marche",
            };
            ecrire("corps.json", corpsJson);
            const presence = lire("presence.json", { presence: {} });
            presence.presence = presence.presence || {};
            const e = presence.presence[pid] || {};
            e.lieu = dit;
            if (date) e.date = date;
            presence.presence[pid] = e;
            ecrire("presence.json", presence);
          }

          // 3. CE QU'ON VIENT DE LONGER, pour le MJ.
          const pas = {
            x: Math.round(x), y: Math.round(y),
            metres: Math.round(+p.metres || 0), minutes: Math.round(minutes * 10) / 10,
            date, ou: dit, quartier: (autour.proches[0] || {}).quartier || null,
            // Chacun avec son RANG : c'est par lui que le MJ peut le baptiser
            // (`affecter.py --affecter lieu:<id> <bat> --nom "…"`), après quoi
            // il reviendra nommé dans toutes les balades.
            longe: autour.proches.map((b) =>
              (b.nom ? b.nom + " (" + metier(b.usage) + ", " : metier(b.usage) + " (") +
              b.a + " pas, bâtiment " + b.bat + ")"),
            connus: autour.connus.map((b) => ({ cle: b.cle, nom: b.nom, bat: b.bat, a: b.a })),
            // le tissu, en un mot : « et 14 maisons, 3 taudis »
            tissu: (autour.tissu || []).sort((p, q) => q[1] - p[1])
              .map(([u, n]) => n + " " + (n > 1 ? PLURIELS[u] || u : metier(u)))
              .join(", ") || null,
            marquant: autour.gros
              ? metier(autour.gros.usage) + ", " + autour.gros.aire + " m²" +
                (autour.gros.etages > 1 ? ", " + autour.gros.etages + " étages" : "")
              : null,
            // QUI ON CROISE — combien, et de quel métier, à trente mètres.
            // C'est la seule ligne du pas qui change d'une heure à l'autre :
            // les murs sont les mêmes à trois heures du matin et à midi, les
            // gens non. Sans elle, une balade décrivait une ville vide.
            gens: direGens(p.gens),
            // CE QU'ON CROISE DE LA BATAILLE, s'il y en a une de datée. Vu,
            // entendu, ou trouvé par terre — jamais autre chose. Un fait qui
            // n'est à portée d'aucun des trois sens ne parvient pas au joueur,
            // et c'est tout le brouillard de cette partie en une ligne.
            croise: croiser.autour(RACINE, lieu, x, y, date),
            fin: !!p.fin,
          };
          // ⚠ DEBUG — voir DEBUG_MARCHE_AU_FIL en tête de fichier. On écrit
          // dans le fil du joueur ce qui part au MJ, tel quel. `pour: [pid]`
          // le garde privé à ce siège ; `duree: 0` parce que la montre a déjà
          // été avancée dix lignes plus haut et qu'on ne la paie pas deux fois.
          if (DEBUG_MARCHE_AU_FIL && pid) {
            const c = pas.croise || {};
            const nb = (t) => (Array.isArray(t) ? t.length : 0);
            const perçus = [].concat(c.vu || [], c.entendu || [], c.traces || [])
              .slice(0, 4)
              .map((f) => "· " + (f.comment || "?") + " — " + (f.quoi || "?") +
                          (f.nom ? " (" + f.nom + ")" : "") +
                          (f.pas != null ? ", " + f.pas + " pas" : ""));
            const lignes = [
              "▣ " + (p.combat ? "COMBAT" : "BALADE") + " — " + pas.ou,
              pas.metres + " m, " + pas.minutes + " min" +
                (pas.quartier ? " — " + pas.quartier : ""),
              pas.longe && pas.longe.length ? "longe : " + pas.longe.join(" ; ") : null,
              pas.tissu ? "tissu : " + pas.tissu : null,
              pas.gens && pas.gens.en_armes
                ? "EN ARMES : " + pas.gens.en_armes +
                  (pas.gens.armes ? " — " + pas.gens.armes : "") : null,
              pas.gens && pas.gens.font ? "font : " + pas.gens.font : null,
              pas.gens && pas.gens.metiers
                ? "croise : " + pas.gens.croises + " — " + pas.gens.metiers : null,
              (nb(c.vu) + nb(c.entendu) + nb(c.traces))
                ? "PERÇU (" + nb(c.vu) + " vu / " + nb(c.entendu) + " entendu / " +
                  nb(c.traces) + " traces) :\n" + perçus.join("\n")
                : null,
            ].filter(Boolean);
            try {
              fs.appendFileSync(path.join(RACINE, "etat", "flux.jsonl"),
                JSON.stringify({ type: "breve", texte: lignes.join("\n"),
                                 // LA DATE, et ce n'est pas du décor : le
                                 // bandeau du fil n'écrit l'heure QUE sur un
                                 // item qui en porte une. Sans elle, on marche
                                 // quarante minutes, la carte avance, et le
                                 // bandeau reste à l'heure du départ — deux
                                 // heures différentes sur le même écran, ce
                                 // qui est exactement ce que `bus.js` dit
                                 // vouloir éviter.
                                 date,
                                 pour: [pid], delai_s: 0, duree: 0,
                                 debug: true }) + "\n", "utf-8");
            } catch (e) { /* le debug ne casse jamais la marche */ }
          }
          const dossier = pid
            ? path.join(RACINE, "etat", "inbox", pid)
            : path.join(RACINE, "etat", "inbox");
          // Le tampon de la balade en cours, hors de l'inbox pour ne pas
          // réveiller le guetteur avant l'arrivée. Sans roster il n'y a pas
          // d'id de siège : le sac de la partie seule s'appelle
          // `_sans-siege.json`, l'underscore le distinguant d'un vrai id.
          const tampons = path.join(RACINE, "etat", "marches");
          fs.mkdirSync(tampons, { recursive: true });
          const tampon = path.join(tampons, (pid || "_sans-siege") + ".json");
          // DÉPOSER = fermer le sac dans l'inbox et oublier le tampon. C'est le
          // seul geste qui réveille le MJ, et il n'arrive qu'une fois par
          // balade. `_session` et `_touche_a` sont de la tuyauterie du tampon :
          // on les retire, le sac que lit le MJ garde exactement son format.
          const deposer = (s) => {
            delete s._session;
            delete s._touche_a;
            fs.mkdirSync(dossier, { recursive: true });
            fs.writeFileSync(path.join(dossier, "marche-" + Date.now() + ".json"),
              JSON.stringify(s, null, 2), "utf-8");
            try { fs.unlinkSync(tampon); } catch (e) {}
          };
          let sac = null;
          try { sac = JSON.parse(fs.readFileSync(tampon, "utf-8")); }
          catch (e) { sac = null; }
          // UNE BALADE ABANDONNÉE NE MANGE PAS LA SUIVANTE. Le joueur qui
          // renonce ou ferme l'onglet laisse un tampon que rien ne fermera
          // jamais. Plutôt qu'une expiration savante : si le sac trouvé porte
          // la signature d'un AUTRE démarrage du serveur, ou si son dernier
          // pas remonte à plus de cinq minutes réelles — on marche un tronçon
          // toutes les quelques secondes, cinq minutes est une éternité en
          // chemin —, c'est une autre promenade. On la ferme vers l'inbox
          // telle qu'elle est, puis on en ouvre une neuve : rien n'est perdu,
          // le MJ reçoit la balade interrompue avec ses pas et son `fini`
          // resté faux, ce qui lui dit précisément qu'elle a été abandonnée.
          if (sac && Array.isArray(sac.pas)) {
            const vieux = Date.now() - (+sac._touche_a || 0) > 5 * 60 * 1000;
            if (sac._session !== SESSION_SERVEUR || vieux) {
              deposer(sac);
              sac = null;
            }
          }
          if (!sac || !Array.isArray(sac.pas)) {
            // « combat » quand l'homme TIENT SA POSITION au lieu de marcher :
            // même route, même sac, même horloge — mais le MJ doit savoir s'il
            // lit une promenade ou dix minutes passées devant une porte qu'on
            // enfonce. Sans ce mot, il recevrait quarante pas de zéro mètre et
            // devrait le deviner. Voir ecrans/modules/combat.js.
            sac = { type: p.combat ? "combat" : "marche", joueur_id: pid, lieu,
                    depart: pas.ou, recu_a: new Date().toISOString(), pas: [] };
          }
          sac.pas.push(pas);
          sac.arrivee = pas.ou;
          sac.metres = (sac.metres || 0) + pas.metres;
          sac.minutes = Math.round(((sac.minutes || 0) + pas.minutes) * 10) / 10;
          // CE QUI SE LÈVE EN CHEMIN ARRÊTE LA MARCHE. C'est la règle du
          // manuel — « alors on arrête de marcher » — et elle ne peut pas
          // rester à la main du MJ : quand le joueur traverse un assaut, ses
          // jambes doivent s'arrêter à l'instant où il le voit, pas trois pas
          // plus loin quand quelqu'un s'en aperçoit. Le sac se ferme dans la
          // foulée, sinon le guetteur attendrait une arrivée qui ne viendra
          // plus.
          const arret = !!(pas.croise && pas.croise.arret);
          // `arret` FERME UNE BALADE, PAS UN COMBAT. Ce qui se lève en chemin
          // coupe les jambes de qui marche — c'est la règle, et elle est bonne.
          // Mais celui qui TIENT SA POSITION est déjà arrêté : lui dire de
          // s'arrêter n'a aucun sens, et fermer son sac au premier « la porte
          // cède » clôturait la scène à la minute où elle commençait. Pire,
          // `combat.js` ne lit pas `arret` et continuait de ticker : le serveur
          // rouvrait un sac, que le fait suivant refermait, et l'on obtenait un
          // fichier par tic — le déluge exact que le tampon existe pour éviter.
          //
          // En combat, un fait qui arrêterait un marcheur n'est donc pas une
          // fin : c'est une nouvelle, et elle part en tranche par la règle
          // au-dessus.
          sac.fini = !!p.fin || (arret && !p.combat);
          if (arret) sac.arret = pas.croise.vu[0] || true;
          // ÇA SE RACONTE PENDANT, PAS APRÈS. C'était le concept, et le tampon
          // — qui n'a pas tort de protéger le guetteur — le perdait en route :
          // un homme qui voit une porte céder à quarante pas le faisait savoir
          // dix minutes plus tard, à l'arrivée. Une scène qui se joue en
          // différé n'est pas une scène ; le joueur attend devant un plan muet
          // pendant que le MJ ne sait rien.
          //
          // La conciliation n'est pas « tamponner OU diffuser », c'est
          // DIFFUSER CE QUI EST UNE NOUVELLE ET TAMPONNER CE QUI N'EN EST PAS
          // UNE. On dépose donc dès qu'un pas PERÇOIT quelque chose — vu,
          // entendu, ou trouvé par terre —, que l'homme marche ou qu'il tienne
          // sa position. Une promenade tranquille ne réveille toujours le MJ
          // qu'une fois, à l'arrivée : c'est le silence qui se tamponne, pas
          // la bataille.
          //
          // AVEC UN PLANCHER D'UNE MINUTE DE FICTION, sinon on retombe très
          // exactement dans le mal que le tampon vient de guérir : quarante
          // tics bruyants feraient quarante fichiers et quarante sonneries.
          // Le plancher se compte sur l'horloge du jeu et non sur la montre
          // réelle, parce que c'est ×N qui décide de la seconde des deux.
          const percu = pas.croise &&
            ((pas.croise.vu || []).length || (pas.croise.entendu || []).length ||
             (pas.croise.traces || []).length);
          const clefMin = date ? ((date.annee * 12 + date.lune) * 30 + date.jour) * 1440
                               + date.minute : 0;
          const versee = !sac.fini && percu &&
                         clefMin - (+sac._verse_a || 0) >= 1;
          if (versee) {
            sac._verse_a = clefMin;
            // On dépose une TRANCHE : ce qui est parti est parti, et la suite
            // s'accumule dans un sac neuf. Le MJ lit donc la scène par
            // morceaux dans l'ordre, jamais deux fois la même ligne. `suite`
            // lui dit que ce sac n'est pas un début — sans quoi il croirait
            // que l'homme vient d'arriver à chaque tranche.
            const tranche = sac;
            sac = { type: sac.type, joueur_id: pid, lieu, depart: pas.ou,
                    recu_a: new Date().toISOString(), pas: [],
                    _verse_a: clefMin, suite: true };
            deposer(tranche);
          }
          if (sac.fini) {
            deposer(sac);
          } else {
            sac._session = SESSION_SERVEUR;
            sac._touche_a = Date.now();
            fs.writeFileSync(tampon, JSON.stringify(sac, null, 2), "utf-8");
          }
          return envoyer(res, 200, JSON.stringify({ date, ou: dit, autour,
                                                    pas: sac.pas.length, arret }));
        } catch (e) {
          return envoyer(res, 500, JSON.stringify({ erreur: String(e.message || e) }));
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
          // L'adresse de la ligne, partagée entre l'inbox et le flux : c'est
          // par elle que le MJ retrouve la phrase à reformuler.
          const ref = "v" + Date.now().toString(36) +
            Math.random().toString(36).slice(2, 6);
          if (action.type === "libre") action.ref = ref;
          fs.mkdirSync(dossier, { recursive: true });
          fs.writeFileSync(path.join(dossier, "action-" + Date.now() + ".json"),
            JSON.stringify(action, null, 2), "utf-8");
          // Ce que le joueur dit ou fait entre dans le flux : sans cela, sa parole
          // n'existe que dans le navigateur et disparaît au premier rechargement.
          // « Laisser faire » se poste même vide : l'absence de consigne EST la
          // consigne — on joue le personnage comme on le connaît.
          if (action.type === "libre" && ((action.texte || "").trim() ||
              action.mode === "run" || action.mode === "composer")) {
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
              // Lâcher la bride n'est pas un geste dans la fiction : personne
              // dans la salle ne voit le joueur s'écarter. Ce qui suivra, en
              // revanche, sera bien du personnage — le MJ le poussera en
              // `vous`, à sa place et devant tout le monde.
              : action.mode === "run"
              ? Object.assign({ type: "run", texte: action.texte || "", delai_s: 0 }, prive)
              // L'atelier : on compose SUR la partie. Rien n'entre dans la
              // fiction, personne ne l'entend, l'horloge ne bouge pas.
              // La main par-dessus le monde : on ne joue pas, on répare. Rien
              // de ce qui se dit ici n'a été prononcé dans la salle — mais ce
              // qu'on y demande change le fil et l'état pour de bon.
              : action.mode === "intervention"
              ? Object.assign({ type: "intervention", texte: action.texte, delai_s: 0 }, prive)
              : action.mode === "composer"
              ? Object.assign({ type: "composer", texte: action.texte || "", delai_s: 0 }, prive)
              : Object.assign(
                  { type: "vous", mode: action.mode || "dire", texte: action.texte, delai_s: 0,
                    joueur_id: siege ? siege.personnage_id : undefined,
                    // L'adresse de la ligne, et le fait qu'elle attend d'être
                    // reformulée : le MJ répond par un `reecrit` portant ce
                    // même `ref`, et la page remplace le brouillon en place.
                    ref: ref,
                    ameliorer: action.ameliorer ? true : undefined },
                  // Ce qui est dit dans une scene privee y reste : le joueur
                  // herite de l'audience de la scene, comme tout le reste.
                  //
                  // Et quand rien ne l'etablit, ON SE FERME. `append_flux.py`
                  // refuse d'ecrire dans ce cas-la ; le serveur n'a pas ce luxe
                  // — un joueur qui parle attend que sa parole existe — alors il
                  // se rabat sur le plus etroit : sa propre scene. Une parole
                  // qu'on garde trop privee se rattrape d'un item ; une parole
                  // lachee au camp d'en face ne se rattrape pas.
                  //
                  // MAIS LA PIECE PASSE AVANT LA SCENE. Deux joueuses debout
                  // dans la meme roukerie s'entendent : c'est de la physique, et
                  // aucune etiquette de scene ne doit pouvoir le contredire. Le
                  // `pour` herite d'un `effacer` ouvert ailleurs, plus tot, a
                  // rendu muette une joueuse qui parlait pourtant a trois pieds
                  // de l'autre — six repliques tapees pour personne. On consulte
                  // donc `presence.json` en PREMIER : meme piece, parole
                  // entendue de la piece. (Meme regle dans `scripts/append_flux.py`.)
                  //
                  // ENTENDUE DE LA PIECE, PAS DU FICHIER. Rendre ici un `{}` —
                  // « pas de pour », donc public — donnait la parole de la reine
                  // et de sa maitresse de la voix au troisieme siege, qui se
                  // tenait a deux lieues de la. On nomme donc les oreilles :
                  // celles qui sont dans la salle, et elles seules.
                  (function () {
                    const moi = siege && siege.personnage_id;
                    const l = roster();
                    if (moi && l && l.length > 1) {
                      try {
                        const pr = JSON.parse(fs.readFileSync(
                          path.join(RACINE, "etat", "presence.json"), "utf-8")).presence || {};
                        // LA SALLE D'ABORD, LE LIEU ENSUITE. `lieu` est un
                        // en-tete de TEXTE : il ne vaut que si le MJ l'a ecrit,
                        // et il s'orthographie comme il veut. Deux sieges
                        // debout dans `grenier-salle` avaient donc, l'un « La
                        // salle du Grenier, rue des Sœurs », l'autre `null` —
                        // et ne s'entendaient pas, dans la meme piece, tout un
                        // soir. `salle` est un ID : c'est lui qui tranche des
                        // que les deux en portent un.
                        const cle = (x) => (x && (x.salle || x.lieu)) || null;
                        const parSalle = pr[moi] && pr[moi].salle;
                        const ici = cle(pr[moi]);
                        const meme = (a) => a && (parSalle && a.salle
                          ? a.salle === parSalle : cle(a) === ici);
                        const voisins = !ici ? [] : l
                          .filter((j) => j.personnage_id !== moi
                              && meme(pr[j.personnage_id]))
                          .map((j) => j.personnage_id);
                        if (voisins.length) {
                          return { pour: [moi].concat(voisins).sort() };
                        }
                      } catch (e) {}
                    }
                    const a = audienceCourante(moi || null, (siege && siege.depuis) || 0);
                    // À PLUSIEURS, AUCUNE SORTIE NE REND UN ITEM MUET. Un `{}`
                    // écrit ici est un item sans audience, et un item sans
                    // audience finissait chez tout le monde. Même le commun se
                    // NOMME : la liste des sièges occupés, jamais une absence.
                    const tous = () => (l || []).filter((j) => j.occupe && j.personnage_id)
                      .map((j) => j.personnage_id).sort();
                    if (!moi || !l || l.length < 2) return {};
                    if (a === "commun") return { pour: tous() };
                    if (a) return { pour: a };
                    // Audience inconnue : on se ferme sur l'auteur. C'est le
                    // seul défaut sûr — au pire il se parle à lui-même, jamais
                    // il ne parle au camp d'en face.
                    return { pour: moi };
                  })());
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
