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
// Longueur d'une fenêtre de fil servie au navigateur : 500 items. Le reste du
// passé se réclame page par page (`/scene?avant=N`) quand le joueur remonte la
// chronique. Le fichier, lui, garde tout — c'est la mémoire de la partie.
const MAX_FIL = 500;

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
// forme courte « 129.3.22 » dans `activites.json`. On accepte les deux plutôt
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
          if (it.type !== "effacer") return;
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
            vous: LIEUX3D[id].vous || null,
            source: id === LIEU3D_DEFAUT ? "/monde" : "/monde/" + id,
            perime: !!(p && p.perime), peremption: p,
          };
        }),
      }));
    if (quoi === "terrain")
      return rendre(fs.readFileSync(path.join(RACINE, "monde", d.prefixe + ".terrain.json")));
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
      echelle: t.echelle || "?",
      lieu: ouEst(t.personnage_id) || t.lieu_note || "",
      intention: t.intention || "",
      date_maj: dateCourte(t.date_maj),
      age_maj: age === null ? null : -age,
      etapes: encours.length,
      etapes_total: plan.length,
      sans_horloge: encours.filter((e) => typeof e.jours_restants !== "number").length,
      prochaine, prochaine_quoi: prochaineQuoi,
      declencheurs: (t.declencheurs || []).length,
      attitude: t.attitude_joueur || "",
      mandat: t.mandat || null,
      siege: occupes.has(t.personnage_id),
    };
  });
  const BUDGETS = { scene: 5, orbite: 20, royaume: null };
  const groupes = ["scene", "orbite", "royaume"].map((e) => ({
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
    if (t.age_maj !== null && t.age_maj >= 3 && t.echelle !== "royaume")
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
        qui: nom(t.personnage_id), echelle: t.echelle,
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

  // ---- 3. les activités ---------------------------------------------------
  const activites = (((lire("activites.json", {}) || {}).activites) || []).map((a) => {
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
  activites.forEach((a) => a.mesures.forEach((m) => {
    if (m.jours_avant_seuil !== null && m.jours_avant_seuil <= 10)
      alertes.push({ gravite: "tiede", texte: a.id + " : seuil atteint dans " + m.jours_avant_seuil + " jours (" + m.quoi + ")" });
  }));

  return {
    date: monde.date || null, date_texte: dateCourte(monde.date),
    tension: monde.tension == null ? null : monde.tension, phase: monde.phase || "",
    horloges: lire("horloges.json", {}),
    groupes, hors_echelle: horsEchelle, alertes,
    echeances, activites,
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
          multi: !!l, moi: j ? { personnage_id: j.personnage_id, nom: j.nom || "" } : null,
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
          // `resolu` est l'instantané qui en découle, routines et chemins compris,
          // refait à chaque poussée d'`append_flux.py`. On le préfère quand il est
          // là : sans lui, un homme laissé dans la grande salle avant-hier y serait
          // encore. Son absence n'arrête rien — on retombe sur les exceptions nues.
          let presence = {};
          let connus = [];
          try {
            const f = lire("presence.json");
            presence = f.presence || {};
            const r = f.resolu && f.resolu.gens;
            if (r) {
              presence = {};
              // Qui est SUIVI, transit compris : un homme dans l'escalier n'est
              // dans aucune pièce, mais on sait où il est — il ne doit pas passer
              // pour un inconnu de passage.
              connus = Object.keys(r);
              for (const id of Object.keys(r)) {
                // En chemin, on n'est dans la pièce de personne : on est dans
                // l'escalier, et l'on n'y partage rien.
                if (r[id].etat === "en-chemin") continue;
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
          const mien = moi && presence[moi];
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
            .filter((id) => id !== moi && meme(presence[id], mien))
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
            if (autresJoueurs.has(id) && !meme(presence[id], mien)) return;
            places[id] = {
              nom: noms[id] || id,
              titre: titres[id] || "",
              salle: presence[id].salle || null,
              lieu: presence[id].lieu || null,
              ici: meme(presence[id], mien),
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
      // Un module, ou un module d'une famille : `/modules/monde/relief.js`. Un
      // seul cran de sous-dossier, et rien qui ressemble à un chemin remontant.
      const m = url.match(/^\/modules\/(?:([a-z0-9_-]+)\/)?([a-z0-9_-]+\.js)$/);
      if (m) return fichierStatique(res,
        m[1] ? path.join("modules", m[1], m[2]) : path.join("modules", m[2]),
        "text/javascript; charset=utf-8");
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
      // La foule : une page d'essai, un point par habitant, la journée en
      // accéléré. Hors du jeu — elle ne lit ni le flux ni l'inbox.
      if (url === "/foule") return fichierStatique(res, "foule.html", "text/html; charset=utf-8");
      const mv = url.match(/^\/vendor\/([a-z0-9_.-]+\.js)$/);
      if (mv) return fichierStatique(res, path.join("vendor", mv[1]), "text/javascript; charset=utf-8");
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
            const moi = (siege && siege.personnage_id) || journal.personnage_joueur_id;
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
            const moi = (siege && siege.personnage_id) || journal.personnage_joueur_id;
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
      // la main. On les sert tous ; c'est la page qui ne montre que ceux de la
      // salle où le joueur se tient.
      if (url === "/books") {
        try {
          const books = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "books.json"), "utf-8"));
          return envoyer(res, 200, JSON.stringify({ books: Array.isArray(books) ? books : [] }));
        } catch (e) {
          return envoyer(res, 200, JSON.stringify({ books: [] }));
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
            const moi = (siege && siege.personnage_id) || journal.personnage_joueur_id;
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
      // Vos desseins : la page complète des objectifs, avec ce que la liste du
      // rail ne peut pas porter — l'échéance, le nombre de jours qui reste, et
      // de quelle bouche la chose est venue. Rien d'occulte : ce sont les
      // objectifs du joueur, pas ceux des autres.
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
            items = items.filter((it) => !it.pour
              || (Array.isArray(it.pour) ? it.pour.indexOf(moi) !== -1 : it.pour === moi));
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
          return envoyer(res, 200, JSON.stringify({ items, debut, total }));
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
          const r = await voix.dire(d.locuteur_id, d.texte, d.client_id);
          if (r.audio) return envoyer(res, 200, r.audio, "audio/mpeg");
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
          if (action.type === "libre" && ((action.texte || "").trim() || action.mode === "run")) {
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
                        const ici = pr[moi] && pr[moi].lieu;
                        const voisins = !ici ? [] : l
                          .filter((j) => j.personnage_id !== moi
                              && pr[j.personnage_id] && pr[j.personnage_id].lieu === ici)
                          .map((j) => j.personnage_id);
                        if (voisins.length) {
                          return { pour: [moi].concat(voisins).sort() };
                        }
                      } catch (e) {}
                    }
                    const a = audienceCourante(moi || null, (siege && siege.depuis) || 0);
                    if (a === "commun") return {};
                    if (a) return { pour: a };
                    return (moi && l && l.length > 1) ? { pour: moi } : {};
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
