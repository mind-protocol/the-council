// -*- coding: utf-8 -*-
/**
 * SAC — cuire une bataille au lieu de la calculer sous les yeux du joueur.
 *
 *     node scripts/monde/sac.js                       (300 hommes, la Gadoue)
 *     node scripts/monde/sac.js --hommes 2000
 *     node scripts/monde/sac.js --porte "La porte du Roi" --duree 900
 *     node scripts/monde/sac.js --serveur http://localhost:3129
 *
 * POURQUOI. Le direct impose un budget d'image ; le four n'en a aucun. Ce qui
 * était impossible à trois cents hommes le reste à dix mille — mais si l'on
 * accepte que la bataille soit CUITE, le plafond disparaît : on prend le temps
 * qu'il faut, une fois, et le client n'a plus qu'à rejouer. C'est très
 * exactement ce que `plan_ville.py` fait du plan, et `besoins.py` des journées.
 *
 * ON NE RÉÉCRIT PAS LA SIMULATION. Le four IMPORTE `ecrans/modules/bataille2d.js`
 * — le même fichier que le navigateur, avec les mêmes machines à états, les
 * mêmes mesures et le même hasard ensemencé. Deux implémentations d'une même
 * bataille, ce sont deux batailles : on ne peut plus se fier ni à l'une ni à
 * l'autre, et l'on passe ses soirées à chercher laquelle ment.
 *
 * IL VA CHERCHER SES DONNÉES PAR LE VRAI SERVEUR, pour la même raison. La
 * voirie n'est pas un fichier : c'est une route de `serveur.js` qui filtre le
 * graphe. La réécrire ici, c'est réintroduire la divergence par la porte de
 * derrière. Node sait faire `fetch` — on s'en sert.
 *
 * CE QU'IL ÉCRIT — des IMAGES CLEFS, pas des échantillons.
 *
 * Retenir la position de chacun à chaque pas, c'est cinq téraoctets pour un
 * sac. Retenir une position par seconde, c'est encore un demi-gigaoctet. Mais
 * un homme qui marche droit dans une rue n'a rien à raconter entre son entrée
 * et sa sortie : on n'écrit un point QUE lorsque la ligne droite depuis le
 * dernier point s'écarte de plus de `TOLERANCE` de la vérité. Un homme en
 * colonne coûte alors trois points par rue ; un homme dans la presse en coûte
 * trente, et c'est justement là qu'on veut de la précision.
 *
 * C'est la même idée que `journee.js` tient déjà pour les habitants : LA
 * POSITION NE SE STOCKE PAS, ELLE SE CALCULE — ici par interpolation entre
 * deux images clefs, là par interpolation le long d'une polyligne.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

const RACINE = path.dirname(path.dirname(path.dirname(path.resolve(__dirname))));
const ICI = path.dirname(path.dirname(__dirname));   // la racine du dépôt
const MONDE = path.join(ICI, "monde");
const MODULES = path.join(ICI, "ecrans", "modules");

// --- ce qui se règle -------------------------------------------------------
const TOLERANCE = 0.5;      // mètres : l'écart qu'on tolère à l'interpolation
const PAS = 1 / 20;         // le pas de la simulation, celui du module
const PLAFOND_BUF = 400;    // 20 s : au-delà on ferme, quoi qu'il arrive

function args() {
  const a = process.argv.slice(2), o = {
    hommes: 300, porte: "La porte de la Gadoue", duree: 1400,
    serveur: "http://localhost:3129", source: "/monde", sortie: null,
    // Une planche toutes les N secondes de bataille, pour regarder le four
    // travailler. À ZÉRO PAR DÉFAUT, et ce n'est pas de la timidité : ce
    // script sert aussi à mesurer, et une mesure qui écrit des fichiers sur le
    // côté ne mesure plus ce qu'on croit.
    planches: 0, port: 3150, tranche: 600, peuple: 1, tournee: 3,
  };
  for (let i = 0; i < a.length; i++) {
    const c = a[i].replace(/^--/, "");
    if (c in o) o[c] = /^\d+$/.test(a[i + 1]) ? +a[++i] : a[++i];
  }
  o.hommes = +o.hommes; o.duree = +o.duree;
  return o;
}

// ---------------------------------------------------------------------------
// Le décor de navigateur qui manque, et rien de plus. Trois objets : le module
// s'attend à `window`, à `requestAnimationFrame` (qu'il n'appellera jamais,
// puisqu'on n'appelle pas `poser`) et à savoir où trouver `journee.js`.
// ---------------------------------------------------------------------------
function planter(base) {
  globalThis.window = globalThis;
  globalThis.window.CHEMIN_JOURNEE =
    pathToFileURL(path.join(MODULES, "monde", "journee.js")).href;
  globalThis.requestAnimationFrame = () => 0;
  globalThis.cancelAnimationFrame = () => {};
  globalThis.document = { addEventListener() {} };
  // Les modules demandent « /monde/… » ; on les envoie au serveur qui sert
  // déjà le jeu. C'est lui l'autorité sur la voirie et sur le plan.
  const vrai = globalThis.fetch;
  globalThis.fetch = (u, o) => vrai(/^https?:/.test(u) ? u : base + u, o);
}

// LA CHAÎNE DE LA BATAILLE, DANS L'ORDRE, et c'est le même ordre que dans
// `ecrans/jeu.html`. Ce ne sont pas des modules ES mais des scripts qui
// s'assignent à `window.<Nom>` : chacun a donc besoin que le précédent soit
// déjà posé, exactement comme des balises `<script>` successives.
//
// AJOUTER UN MORCEAU DÉCOUPÉ, C'EST TOUCHER LES DEUX LISTES. Il n'y a pas de
// résolution de dépendances ici et il ne faut pas en écrire une : deux listes
// courtes et lisibles valent mieux qu'un chargeur qui aurait l'air malin.
const CHAINE = ["bataille/hasard.js", "bataille/mesures.js",
                "survival-stack/1-corps.js", "bataille/corps-adapt.js",
                // La couche 4 CONDUIT, elle : l'envie de butin et ce qu'un chef
                // supporte de silence sortent d'elle et de nulle part ailleurs
                // depuis qu'`APPETIT` et `SILENCE` sont déposés. Elle doit donc
                // être chargée avant `bataille2d.js`, et non après.
                "survival-stack/4-envie.js",
                // La couche 3 n'est qu'en observation, mais elle est lue par
                // `soldat()` à chaque battement : elle doit être posée avant.
                "survival-stack/3-interpretation.js",
                // LA COUCHE 2, SON POURVOYEUR ET LA MAIN. Le four ne les
                // chargeait pas : `jeu.html` les avait, cette liste-ci non, et
                // deux listes qu'on ne touche pas ensemble sont deux listes qui
                // divergent en silence. Une couche absente du four est une
                // couche qu'aucune cuisson ne mesure — c'est-a-dire une couche
                // dont on ne saura jamais rien.
                "survival-stack/2-reflexion.js",
                "survival-stack/5-qui-conduit.js",
                "bataille/reflexion-adapt.js",
                "bataille2d.js"];

/** Charger la bataille, qui n'est pas un module ES mais une suite de scripts. */
function chargerBataille() {
  for (const f of CHAINE) {
    const src = fs.readFileSync(path.join(MODULES, f), "utf8");
    // eslint-disable-next-line no-eval
    (0, eval)(src);
  }
  if (!globalThis.window.Bataille2d) throw new Error("bataille2d ne s'est pas posé");
  return globalThis.window.Bataille2d;
}

// ---------------------------------------------------------------------------
// LES IMAGES CLEFS
//
// Un « fil » par corps. On lui pousse (t, x, y, état) à chaque pas, et il ne
// GARDE que ce qui ne se devine pas : tant que le point courant se laisse
// deviner par une droite entre le dernier point gardé et lui, on ne garde
// rien — on retient juste le précédent, au cas où le suivant décroche.
//
// C'est une simplification de courbe faite à la volée, en un seul passage et
// sans mémoire : on ne peut pas cuire un sac en gardant les dix millions de
// positions pour les simplifier ensuite.
// ---------------------------------------------------------------------------
// ON COMPARE TOUT CE QU'ON A LAISSÉ TOMBER, PAS SEULEMENT LE DERNIER POINT.
// La première version ne mesurait l'écart que du point précédent à la droite
// — et la vérification l'a attrapée tout de suite : soixante mètres d'erreur.
// Un homme qui contourne un obstacle et revient sur son axe repart d'où il
// était : le dernier point est sur la droite, et toute la boucle du milieu a
// été rasée. Il faut donc garder en attente TOUS les points depuis l'ancre, et
// mesurer le pire d'entre eux.
class Fil {
  constructor(camp) {
    this.camp = camp;
    this.t = []; this.x = []; this.y = []; this.e = [];
    this.buf = [];            // les points en attente depuis l'ancre
    this.ancre = null;        // le dernier point gardé
    this.boite = null;        // l'emprise des points en attente
  }
  // CELUI QUI NE BOUGE PAS NE SE MESURE PAS. Un garde à son poste n'excède
  // jamais la tolérance : sa liste d'attente enflait donc jusqu'à quatre mille
  // points qu'on rebalayait à chaque pas, et la cuisson est passée de deux
  // secondes à une minute. Or si TOUT ce qui attend tient dans une boîte plus
  // petite que la tolérance, aucun de ces points ne peut s'écarter de plus que
  // ça d'une droite qui traverse la boîte : on le sait sans rien mesurer.
  petite() {
    const b = this.boite;
    return b && (b[2] - b[0]) < TOLERANCE * .7 && (b[3] - b[1]) < TOLERANCE * .7;
  }
  /** L'écart maximum des points en attente à la droite ancre → p. */
  pire(p) {
    const a = this.ancre, dt = p.t - a.t;
    if (dt <= 0) return Infinity;
    let m = 0;
    for (const q of this.buf) {
      const u = (q.t - a.t) / dt;
      const d = Math.hypot(a.x + (p.x - a.x) * u - q.x,
                           a.y + (p.y - a.y) * u - q.y);
      if (d > m) m = d;
    }
    return m;
  }
  garder(p) {
    this.t.push(p.t); this.x.push(p.x); this.y.push(p.y); this.e.push(p.e);
    this.ancre = p; this.buf = []; this.boite = [p.x, p.y, p.x, p.y];
  }
  enBoite(p) {
    const b = this.boite;
    if (p.x < b[0]) b[0] = p.x; if (p.y < b[1]) b[1] = p.y;
    if (p.x > b[2]) b[2] = p.x; if (p.y > b[3]) b[3] = p.y;
  }
  pousser(t, x, y, e) {
    const p = { t, x, y, e };
    if (!this.ancre) { this.garder(p); return; }
    // UN CHANGEMENT D'ÉTAT SE GARDE TOUJOURS, et des deux côtés : le dernier
    // instant de l'ancien état, puis le premier du neuf. C'est ce qui distingue
    // ce format d'une simple compression — le fil doit pouvoir dire « il est
    // mort à cet instant-là », et une interpolation ne dit jamais ça.
    if (e !== this.ancre.e) {
      const d = this.buf[this.buf.length - 1];
      if (d) this.garder(d);
      this.garder(p);
      return;
    }
    this.buf.push(p);
    this.enBoite(p);
    // L'immobile passe sans qu'on le mesure ; le plafond borne le pire cas,
    // pour qu'un balayage ne puisse jamais dépendre de la durée du sac.
    if (this.petite() && this.buf.length < PLAFOND_BUF) return;
    if (this.buf.length >= PLAFOND_BUF || this.pire(p) > TOLERANCE) {
      this.buf.pop();
      const d = this.buf[this.buf.length - 1];
      if (d) this.garder(d);
      this.buf.push(p);
      this.enBoite(p);
    }
  }
  fermer() {
    const d = this.buf[this.buf.length - 1];
    if (d) this.garder(d);
  }
  get n() { return this.t.length; }
}

// Les états, en un octet. L'ordre ne change jamais : il est écrit dans le
// manifeste, et le lecteur s'en sert pour retrouver les noms.
// ON AJOUTE À LA FIN, JAMAIS AU MILIEU. Le code d'un état est son rang, et il
// est écrit dans tous les sacs déjà cuits : insérer `blesse` entre `deroute` et
// `mort` aurait décalé sept états d'un cran, et les anciens fichiers se
// seraient relus faux sans que rien ne le signale.
const ETATS = ["colonne", "forme", "assaut", "melee", "arrive", "deroute", "mort",
               "tient", "saisi", "fuite", "rentre", "terre", "contre", "blesse",
               "coureur", "repli", "commande", "pille"];
const CODE = Object.fromEntries(ETATS.map((e, i) => [e, i]));

// ---------------------------------------------------------------------------
// LES ANNALES, EN FRANÇAIS
//
// Le module rend des faits ; il ne rend pas des phrases, et il ne doit pas. Un
// fait porte un verbe (`quoi`), une heure, un lieu et ce qu'il faut pour être
// dit — le camp, l'escouade, combien restent. La mise en mots se fait ICI,
// parce que c'est une affaire de sortie et non de simulation.
//
// LA PHRASE EST L'UNITÉ DE TRAVAIL DU MJ. Il ne lira pas un tableau de champs :
// il lira « 4′12″ — au bourg de la Gadoue, à 40 pas de La porte de la Gadoue —
// la porte cède », et il en fera une scène. Tout ce qui ne se lit pas d'une
// traite à voix haute est mal écrit.
// ---------------------------------------------------------------------------
const HEURE = (s) => Math.floor(s / 60) + "′" +
                     String(Math.floor(s % 60)).padStart(2, "0") + "″";

// `LE_CAMP` et non `CAMP` : le four a déjà un `CAMP` — le tableau d'octets des
// camps dans le binaire. Les deux ne se rencontrent pas (l'un est de portée
// module, l'autre local), mais deux choses du même nom dans le même fichier
// finissent toujours par se croiser un jour où l'on déplace une accolade.
const LE_CAMP = { assaut: "des assaillants", garde: "de la garde" };

// « la 1re escouade », pas « la 1e ». Un document qu'on lit à voix haute se
// lit mal dès la première ligne quand l'ordinal est faux.
const RANG = (n) => n + (n === 1 ? "re" : "e");

// Une aile se nomme, elle ne se numérote pas : « l'aile de gauche » se retient,
// « l'aile 2 » ne se retient pas. Au-delà de trois, on retombe sur le chiffre.
const AILE = (i) => ["de tête", "de gauche", "de droite"][i] || "n° " + (i + 1);

// « la 2e aile de Ser Perkin la Puce » — l'aile appartient à quelqu'un, et
// c'est la seule façon de s'y retrouver quand six corps en ont chacun quatre.
const DE = (nom) => (nom ? "de " + nom : "");

// Le verbe nu, pour les sacs cuits avant que les ordres soient des phrases.
const VERBE = (v) => ({ avancer: "marcher", tenir: "tenir", repli: "décrocher",
                        suivre: "suivre", appuyer: "appuyer" }[v] || v || "?");

// « ordonne à sa 2e aile de appuyer » — l'élision se perd dès qu'on colle une
// phrase engendrée derrière une préposition. Elle se remet ici, une fois.
const D_ = (s) => (/^[aàâeéèêiîoôuûyh]/i.test(s || "") ? "d'" + s : "de " + s);

const DIRE = {
  "contact":          () => "les deux fers se touchent pour la première fois",
  "premier-sang":     (f) => "le premier mort de la journée, " + (LE_CAMP[f.camp] || ""),
  // Ce qu'on savait d'elle avant que la nuit commence, et qui n'a jamais été
  // réparé. La ligne se lit au matin comme un reproche, et c'en est un.
  "porte-abimee":     (f) => "« " + f.porte + " » est mangée — il lui reste " +
                             f.part + " % de son bois, et personne ne l'ignorait",
  "porte-cede":       (f) => "« " + f.porte + " » commence à céder",
  "porte-enfoncee":   (f) => "« " + f.porte + " » est enfoncée",
  // LE NOM EST LA RAISON D'ÊTRE DE CETTE LIGNE. Elle disait « le chef de la
  // 1re escouade tombe » pour Ser Damon Beurrepré comme pour un capitaine
  // anonyme — c'est-à-dire qu'on avait pris la peine de nommer un homme pour
  // le perdre à la seule ligne où il comptait.
  "chef-tombe":       (f) => (f.nom
                               ? f.nom + " tombe"
                               : "un capitaine " + (LE_CAMP[f.camp] || "") + " tombe") +
                             (f.mort ? "" : ", vivant"),
  "tete-tombe":       (f) => (f.nom || "la tête") + " tombe" +
                             (f.mort ? " — son corps n'a plus personne pour le mener"
                                     : ", vivant, et il ne commande plus"),
  "escouade-rompt":   (f) => "la " + RANG(f.escouade + 1) + " escouade cesse d'en être une — " +
                             f.restent + " debout sur " + f.sur,
  "blesse":           (f) => "un homme " + (LE_CAMP[f.camp] || "") + " reste à terre, vivant" +
                             (f.chef ? ", et c'était un chef" : ""),
  "blesse-succombe":  (f) => "un blessé " + (LE_CAMP[f.camp] || "") + " cesse d'appeler",
  "blesse-tient":     (f) => "un blessé " + (LE_CAMP[f.camp] || "") +
                             " a cessé de saigner — il tiendra jusqu'au matin",
  "peur-gagne":       (f) => "la peur gagne " + f.zone + " — on les a vus",
  "rumeur-gagne":     (f) => "la peur gagne " + f.zone + " — on ne l'a qu'entendu dire",
  "guet-a-vu":        (f) => "un homme du guet s'est avancé jusqu'à voir : " +
                             f.hommes + " hommes en armes",
  "assaut-au-donjon": () => "le premier assaillant atteint le Donjon Rouge",

  // --- LES DEUX FINS QUI NE PASSENT PAS PAR LE VERROU ----------------------
  // Elles ne se lisent pas comme le reste, et il ne faut pas qu'elles s'y
  // fondent : une porte enfoncée est le résultat de trois mille points de
  // hache, une porte ouverte est le résultat d'une conversation.
  // Celui qui n'est pas arrivé. Personne, à sa porte, ne saura qu'il est tombé
  // — et personne au Donjon ne saura qu'on lui avait envoyé quelqu'un.
  "messager-tombe":   (f) => "l'homme parti de « " + f.porte + " » n'ira pas" +
                             " plus loin — il courait depuis " +
                             Math.round(f.depuis) + " secondes, et il lui" +
                             " restait " + f.reste + " pas",
  "roi-averti":       (f) => "au Donjon Rouge, on apprend que « " + f.porte +
                             " » cède — " + Math.round(f.depuis / 60) +
                             " minutes après qu'elle a commencé, et " + f.pas +
                             " pas plus loin",
  "donjon-tranche":   (f) => f.par + " a tranché : aucune porte ne s'ouvrira" +
                             (f.contre ? " — " + f.contre + " avait les chiffres" : ""),
  // Plus une porte debout : ce qui restait à ouvrir était le Donjon lui-même,
  // et l'anneau s'est retiré dans la cour au lieu de la défendre.
  "donjon-ouvert":    (f) => "le Donjon Rouge s'ouvre — " + f.par + " l'a" +
                             " emporté sur " + f.contre + ", et les " + f.hommes +
                             " de l'anneau rentrent sans qu'on croise un fer",
  "porte-ouverte":    (f) => "« " + f.porte + " » s'ouvre de l'intérieur, sans" +
                             " un coup de hache — " + f.par + " l'a emporté",
  "roi-tombe":        (f) => f.nom + " verse sous les siens — la charrette est" +
                             " passée sous la déroute, et tout s'arrête",

  // Un habitant qui a un nom, et ce qu'il fait quand ça lui arrive. Sa conduite
  // est écrite dans la mise en place : on ne la décide pas ici, on la rapporte.
  "habitant":         (f) => f.nom + " — " + f.fait,
  "maison-brulee":    (f) => "une maison brûle" +
                             (f.corps ? " — des hommes " + DE(f.corps) : ""),

  // --- LA RUE CHOISIT, ET ELLE NE CHOISIT PAS PAREIL -----------------------
  // Le même cri, la même minute, la même rue : l'un va chercher une hache,
  // l'autre barre sa porte. La ligne doit dire LEQUEL, et de quel métier —
  // c'est ce qui la rend jouable au lieu d'être un compteur.
  "prend-les-armes":  (f) => (f.combien === 1
      // `_roles` rend un OBJET — `{nom, rang}` — et non une chaîne. C'est déjà
      // ce que `lesTemoins` lit dix lignes plus bas ; on ne le réapprend pas
      // deux fois dans le même fichier.
      ? (f.femme ? "une " : "un ") +
        String((ROLES[f.role] && ROLES[f.role].nom) || f.role || "habitant").toLowerCase() +
        " de " + f.zone +
        (f.camp === "assaut" ? " prend les armes avec eux"
                             : " barre sa porte et se met en travers")
      : f.combien + " gens de " + f.zone +
        (f.camp === "assaut" ? " ont pris les armes avec eux"
                             : " se sont mis en travers")),

  // --- CE QUE CHAQUE CORPS EST ---------------------------------------------
  // Trois lignes au tout début, et elles ne coûtent rien : sans elles, on lit
  // ensuite une aile qui ne rompt jamais et une escouade qui n'obéit à rien
  // sans savoir que c'était voulu. Un fichier doit dire ses propres règles.
  "corps-ferme":      (f) => f.chef + " et ses " + f.hommes +
                             " hommes ne rompront pas — ils mourront sur place",
  "corps-sourd":      (f) => f.chef + " mène " + f.hommes +
                             " hommes qui n'entendront aucun ordre de la nuit",
  "corps-versatile":  (f) => f.chef + " mène " + f.hommes +
                             " hommes qui partiront vite et reviendront vite",

  // --- la chaîne de commandement -------------------------------------------
  // C'EST QUELQU'UN QUI ORDONNE, ET IL A UN NOM. « la tête ordonne à l'aile
  // n° 17 » ne se lit pas : ni qui parle, ni à qui. Six corps qui ne
  // s'accordent pas ne valent quelque chose dans le document que si l'on voit
  // lequel vient de faire quoi.
  // UN ORDRE EST UNE PHRASE, ET C'EST LE MODULE QUI L'ÉCRIT. Il connaît son
  // objet, sa distance, sa réserve ; ici on ne sait que le recopier. `phrase`
  // arrive donc toute faite, et `ordre` — le verbe nu — reste pour les sacs
  // cuits avant que les compléments existent.
  // ON DIT QUAND PERSONNE NE POUVAIT L'ENTENDRE. Un ordre à une aile dont
  // toutes les escouades sont sourdes de naissance meurt dans la bouche du
  // chef : il ne se transmet pas, il n'est pas perdu en chemin, il n'a
  // simplement jamais eu de destinataire. Sans cette incise, le dépouillement
  // compte quinze ordres donnés là où douze pouvaient arriver — et l'on
  // s'étonne ensuite qu'une aile n'ait rien fait de la nuit.
  "ordre":            (f) => (f.chef || "la tête") + " ordonne à sa " +
                             RANG((f.rang || 0) + 1) + " aile " +
                             D_(f.phrase || VERBE(f.ordre)) +
                             " — il lui reste " + Math.round(f.force * 100) + " % de ses hommes" +
                             (f.sourd ? ", et pas un homme de cette aile ne peut l'entendre" : ""),
  "coureur-part":     (f) => "un coureur part de la " + RANG((f.rang || 0) + 1) +
                             " aile " + DE(f.chef) +
                             " pour la " + RANG(f.vers + 1) + " escouade" +
                             (f.phrase ? " — « " + f.phrase + " »" : ""),
  "coureur-arrive":   (f) => "le coureur atteint la " + RANG(f.vers + 1) +
                             " escouade" +
                             (f.phrase ? " — il apporte : " + f.phrase : ""),
  // L'ORDRE QUI N'A PLUS DE DESTINATAIRE. Le coureur est arrivé ; c'est
  // l'escouade qui n'existe plus — sous cinq hommes, elle cesse d'être un
  // repère. Personne n'est tombé, rien n'a été intercepté, et pourtant l'ordre
  // est perdu : c'est le seul cas où la chaîne casse par le bas.
  "ordre-sans-personne": (f) => "le coureur arrive et ne trouve plus personne — " +
                             "la " + RANG(f.vers + 1) + " escouade a fondu, et " +
                             (f.phrase ? "« " + f.phrase + " »" : "l'ordre") +
                             " ne sera jamais porté à personne",
  "coureur-tombe":    (f) => "le coureur tombe en chemin — la " + RANG(f.vers + 1) +
                             " escouade n'aura jamais su qu'on lui disait " +
                             D_(f.phrase || VERBE(f.ordre)),

  // --- CE QUI S'ABÎME, CE QUI ATTEND, CE QU'ON S'INVENTE --------------------
  // Les trois faits que la chaîne de commandement ne savait pas dire, et sans
  // lesquels on relisait au matin une armée qui désobéit sans motif.
  "ordre-deforme":    (f) => "le coureur perd " +
                             ({ interdit: "la réserve qu'on y avait mise",
                                declencheur: "l'heure à laquelle il fallait le faire",
                                marge: "la distance exacte",
                                objet: "le nom de celui qu'il fallait suivre"
                               }[f.perdu] || f.perdu) +
                             " — il portera : " + f.phrase,
  "declencheur-tombe": (f) => "la " + RANG(f.escouade + 1) +
                             " escouade n'attendait que ça — personne n'a eu à" +
                             " le lui dire : « " + f.phrase + " »",
  "initiative":       (f) => "faute d'ordre, la " + RANG(f.escouade + 1) +
                             " escouade " + DE(f.chef) + " décide seule " +
                             D_(f.phrase) + " — " + f.motif,
  "escouade-sourde":  (f) => "la " + RANG(f.escouade + 1) + " escouade n'entend plus rien — " +
                             "elle continue de " + ({ avancer: "marcher", tenir: "tenir",
                               repli: "décrocher" }[f.ordre] || f.ordre),
  "escouade-reprise": (f) => "la " + RANG(f.escouade + 1) + " escouade reçoit enfin un ordre",
  "nouveau-chef":     (f) => "faute de chef, le coureur prend la tête de la " +
                             RANG(f.escouade + 1) + " escouade",
  "banniere-tombe":   (f) => "la bannière de la " + RANG((f.rang || 0) + 1) +
                             " aile " + DE(f.chef) + " tombe",
  "banniere-relevee": (f) => "on relève la bannière de la " + RANG((f.rang || 0) + 1) +
                             " aile " + DE(f.chef),
  "ralliement":       (f) => "un homme de la " + RANG(f.escouade + 1) +
                             " escouade est rattrapé et remis en ligne",
};

// LES TÉMOINS SE COMPTENT PAR MÉTIER, ILS NE S'ÉNUMÈRENT PAS. La première
// version en listait deux et coupait : devant la porte, où le guet est partout,
// ça donnait « guet de Salle de l'entrepôt, guet de Salle de l'entrepôt… »
// vingt lignes de suite — c'est-à-dire une ligne qui coûte de la place et
// n'apprend rien. « quatre hommes du guet, un portefaix » se lit d'un coup et
// dit ce qu'il faut : qui était là, et de quelle espèce.
//
// Où chacun habite est dans le détail, pas ici. La ligne dit QUI a vu ; le
// fichier dit chez qui aller frapper.
// LE LIBELLÉ D'UN MÉTIER EXISTE DÉJÀ, ON NE LE RÉINVENTE PAS. `portreal.gens
// .json` porte `_roles`, qui donne pour chaque code son nom écrit en toutes
// lettres et accentué — « Homme du guet », « Septon supérieur », « Chef de
// feu ». On sortait le code brut (« chef-de-feu », « epouse ») : des slugs
// dans un document qu'on lit à voix haute, alors que la bonne réponse était
// dans le monde depuis le début.
let ROLES = {};
function chargerRoles() {
  try {
    const g = JSON.parse(fs.readFileSync(path.join(MONDE, "portreal.gens.json"), "utf8"));
    ROLES = g._roles || {};
  } catch (e) { ROLES = {}; }
}

/** Le nom d'un métier, en minuscule d'attaque — il entre au milieu d'une phrase. */
function metier(code) {
  const r = ROLES[code];
  const nom = r && r.nom ? r.nom : String(code || "").replace(/-/g, " ");
  return nom.charAt(0).toLowerCase() + nom.slice(1);
}

// Le pluriel se pose sur le PREMIER mot, qui est la tête du groupe : « hommes
// du guet », « chefs de feu », « maîtres de maison ». Ce n'est pas du français
// complet — « apprentis tanneurs » veut deux marques — mais c'est juste dans
// l'écrasante majorité des titres de métier, qui sont tous « untel DE quelque
// chose ». Et « portefaix » ne prend rien, comme tout ce qui finit déjà par s,
// x ou z.
function pluriel(nom) {
  const [tete, ...reste] = nom.split(" ");
  const t = /[sxz]$/.test(tete) ? tete : tete + "s";
  return [t, ...reste].join(" ");
}

function lesTemoins(tt) {
  // On groupe par métier ET par genre : « une épouse » et « un époux » ne se
  // comptent pas ensemble, et c'est le genre du CORPS qui tranche, pas une
  // devinette sur la terminaison du mot.
  const par = new Map();
  for (const t of tt) {
    const nom = metier(t.role);
    const clef = nom + (t.femme ? "|f" : "|h");
    const e = par.get(clef) || { nom, femme: t.femme, n: 0 };
    e.n++; par.set(clef, e);
  }
  return [...par.values()].sort((a, b) => b.n - a.n).slice(0, 3)
    .map((e) => (e.n > 1 ? e.n + " " + pluriel(e.nom)
                         : (e.femme ? "une " : "un ") + e.nom))
    .join(", ");
}

function raconter(f) {
  const d = DIRE[f.quoi];
  let s = HEURE(f.t) + " — " + f.ou + " — " + (d ? d(f) : f.quoi);
  // DEVANT CHEZ QUI. Le lieu dit où dans la ville ; le nom dit chez qui, et
  // c'est celui-là qu'on ira trouver le lendemain. On ne le répète pas quand le
  // fait EST déjà celui de cette personne — « Nonne la lavandière — trois
  // enfants… · devant chez Nonne la lavandière » ne se lit pas.
  //
  // ET JAMAIS DEUX FOIS LE MÊME NOM DANS LA MÊME LIGNE. « le Portier l'a
  // emporté sur Ser Merryn Coutre, à 25 pas de chez Ser Merryn Coutre » est
  // exactement le genre de phrase qui fait passer un document pour une sortie
  // de machine — et c'est le four qui l'a produite au premier essai.
  if (f.pres && f.quoi !== "habitant" && !s.includes(f.pres))
    s += (f.pres_pas ? ", à " + f.pres_pas + " pas de chez " : ", devant chez ") +
         f.pres;
  // LA QUEUE DE TÉMOINS EST LA MOITIÉ UTILE DE LA LIGNE. Sans elle on lit un
  // compte rendu ; avec elle on lit une piste — et « personne dans la rue »
  // est une information au moins aussi bonne que trois noms, parce qu'elle dit
  // que ce fait-là, on ne pourra le savoir par aucune bouche.
  const t = f.temoins || [];
  if (!t.length) return s;
  return s + " · vu par " + lesTemoins(t);
}

// ---------------------------------------------------------------------------
async function main() {
  const o = args();
  planter(o.serveur);
  chargerRoles();

  process.stdout.write("four : " + o.hommes + " hommes à « " + o.porte +
                       " », " + o.duree + " s de bataille\n");
  const B = chargerBataille();
  const t0 = Date.now();
  await B.preparer(o.source);
  process.stdout.write("  données chargées en " + ((Date.now() - t0) / 1000).toFixed(1) + " s\n");

  B.rejouer(o.porte, o.hommes);
  const corps = B.troupe();
  const fils = corps.map((h) => new Fil(h.camp));

  // Le plan cuit : les planches en font leur fond, la tournée y prend les
  // bornes de la ville. Un seul chargement pour les deux.
  const plan2d = (+o.planches > 0 || +o.peuple !== 0)
    ? await (await fetch(o.source + "/plan2d")).json() : null;

  // Les planches ne se chargent que si on les demande : ni le module, ni un
  // seul octet écrit quand `--planches` vaut zéro.
  let planches = null;
  if (+o.planches > 0) {
    const { Planches } = require("./sac_planches.js");
    planches = new Planches(o, plan2d, +o.planches);
    const ou = await planches.servir(+o.port || 3150);
    process.stdout.write("  planches : une toutes les " + o.planches + " s" +
      (ou ? " — À REGARDER SUR " + ou : " (port pris, pas de serveur)") + "\n");
  }

  // ---- LA VILLE ------------------------------------------------------------
  //
  // Le four n'a pas d'écran, et c'est là tout le problème : la peur ne se
  // déclenche que par le veto que `foule2d` demande en DESSINANT chaque
  // habitant. Pas de dessin, pas de veto, pas de panique — la bataille se
  // jouait donc dans une ville vide, ce qui est la moitié du sujet en moins.
  //
  // Le four fait donc lui-même la tournée : il lit la journée écrite de chacun
  // (`journee.ou`, la fonction pure) et propose le veto (`derange`). Ce sont
  // exactement les deux appels que la foule enchaîne à l'écran, dans le même
  // ordre — on ne réécrit rien, on remplace juste l'œil qui manquait.
  //
  // ON NE BALAIE PAS QUATRE CENT MILLE PERSONNES VINGT FOIS PAR SECONDE. Ce
  // serait cent fois le coût de la bataille elle-même, pour recruter quelques
  // dizaines de fuyards. Deux économies, et elles suffisent :
  //   — la tournée passe UNE FOIS PAR SECONDE de bataille, pas à chaque pas.
  //     Ceux qui paniquent, eux, sont simulés à chaque pas par le module ; la
  //     tournée ne sert qu'à en RECRUTER de nouveaux, et une seconde de retard
  //     à prendre peur ne se voit pas ;
  //   — elle ne visite QUE LES CELLULES PROCHES DU FER. Un quartier à deux
  //     kilomètres n'a personne à effrayer, et le lui demander coûte le même
  //     prix que de le demander à la rue qu'on brûle.
  let G = null, J = null, voirie = null, rangs = null;
  let cellules = [], jour0 = 1, min0 = 480;
  const peuple = +o.peuple !== 0;
  if (peuple) {
    // Les deux mêmes modules que la foule, et ils sont déjà chargés : le
    // module de bataille les a demandés en se préparant, et leurs caches sont
    // internes. Les redemander ne coûte pas un octet de réseau.
    const url = (n) => pathToFileURL(path.join(MODULES, "monde", n)).href;
    G = await import(url("gens.js"));
    J = await import(url("journee.js"));
    voirie = await J.voirie(o.source);
    // La table des besoins et des adresses : `journee` la garde dans un cache
    // interne, mais elle ne se charge pas toute seule — sans cet appel, la
    // première journée demandée meurt sur un `dessert` qui n'existe pas. La
    // foule fait exactement le même geste en s'amorçant.
    await J.table(o.source);
    const manif = await G.manifeste(o.source);
    rangs = J.rangs(manif);
    // ON CHARGE LA VILLE UNE FOIS, ET ON N'Y REVIENT JAMAIS.
    //
    // La tournée rappelait `autour` à chaque seconde, autour d'une armée qui
    // s'étire de cent mètres à un kilomètre et demi. Or `gens.autour` ne fait
    // pas qu'ajouter : il JETTE les cellules sorties du rayon. Chaque seconde
    // en évinçait donc, et chaque éviction emportait trois choses — le cache
    // des journées, celui des chemins, et le tableau `_peur` que la bataille
    // avait posé dessus. D'où le coût (46 s de tournée sur 60 s de cuisson :
    // on recalculait sans cesse ce qu'on venait de jeter) ET un défaut plus
    // grave : un habitant dont la cellule était évincée perdait sa peur, et
    // se faisait recruter à nouveau au passage suivant.
    //
    // Les cent cinquante et une cellules font quatre méga-octets et demi. La
    // foule les charge toutes à l'écran sans y penser ; le four peut bien en
    // faire autant une fois pour toutes.
    const [bx, by, bx1, by1] = plan2d ? plan2d.bornes : [0, 0, 5280, 3600];
    cellules = await G.autour((bx + bx1) / 2, (by + by1) / 2,
                              Math.hypot(bx1 - bx, by1 - by) / 2, o.source);
    const d = await (await fetch("/carte")).json();
    jour0 = (d.date && d.date.jour) || 1;
    min0 = (d.date && typeof d.date.minute === "number") ? d.date.minute : 480;
    process.stdout.write("  la ville : " + manif.total.toLocaleString("fr-FR") +
      " habitants, à " + String(Math.floor(min0 / 60)).padStart(2, "0") + "h" +
      String(Math.floor(min0 % 60)).padStart(2, "0") + "\n");
  }

  const P = {};
  let vus = 0;                       // combien d'habitants la tournée a touchés
  const MAILLE_CEL = 250;            // la maille des cellules de `gens`

  async function tournee(t) {
    if (!peuple || !cellules.length) return;
    // Ce que la tournée doit couvrir : l'armée, la portée de la vue, et de
    // quoi laisser la rumeur courir au-delà.
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const h of corps) {
      if (h.etat === "mort") continue;
      if (h.x < x0) x0 = h.x; if (h.x > x1) x1 = h.x;
      if (h.y < y0) y0 = h.y; if (h.y > y1) y1 = h.y;
    }
    if (!isFinite(x0)) return;
    const m = 500;
    x0 -= m; y0 -= m; x1 += m; y1 += m;
    const minute = (min0 + t / 60) % 1440;
    const jour = jour0 + Math.floor((min0 + t / 60) / 1440);

    for (const cel of cellules) {
      // ON NE VISITE QUE LES CELLULES PROCHES DU FER. Un quartier à deux
      // kilomètres n'a personne à effrayer, et le lui demander coûte le même
      // prix qu'à la rue qu'on brûle. Le test est celui de deux rectangles
      // qui se touchent — quelques comparaisons pour économiser mille corps.
      if (cel.x0 > x1 || cel.x0 + MAILLE_CEL < x0 ||
          cel.y0 > y1 || cel.y0 + MAILLE_CEL < y0) continue;
      const peur = cel._peur;
      for (let k = 0; k < cel.n; k++) {
        // CELUI QUI A DÉJÀ PEUR NE SE RELIT PAS. La tournée ne sert qu'à
        // RECRUTER : ceux qui courent sont simulés à chaque pas par le
        // module, et leur journée écrite ne les concerne plus. On leur
        // calculait pourtant leur emploi du temps une fois par seconde —
        // quatre mille personnes, pour jeter le résultat.
        if (peur && peur[k]) continue;
        J.ou(cel, k, jour, minute, voirie, rangs, P);
        if (B.derange(cel, k, P)) vus++;
      }
    }
  }

  // OÙ PASSE LE TEMPS. Trois consommateurs, et l'on ne sait lequel pèse
  // qu'en les chronométrant : la simulation, l'échantillonnage des images
  // clefs, et la tournée de la ville. Deux lignes qui coûtent trois
  // millisecondes sur une cuisson d'une minute, et qui évitent d'optimiser au
  // jugé — ce qui est la seule façon de perdre une journée sûrement.
  const CHRONO = { sim: 0, fil: 0, tour: 0 };
  const t1 = Date.now();
  const pas = Math.round(o.duree / PAS);
  // COMBIEN DE FOIS ON FAIT LE TOUR DE LA VILLE. C'était une fois par seconde,
  // et ce chiffre-là je ne l'avais pas justifié — il coûtait quarante-sept
  // secondes sur soixante-quatre de cuisson, soit les trois quarts du four.
  //
  // Or la tournée ne sert qu'à RECRUTER, et le recrutement n'est pas pressé :
  // un habitant à quatre-vingt-dix mètres du fer, qui est la portée de la vue,
  // met vingt-cinq secondes à être rejoint au pas de marche. Prendre peur
  // trois secondes plus tard ne se voit pas — courir trois secondes plus tôt
  // ne le sauverait pas davantage. Les paniqués, eux, continuent d'être
  // simulés à chaque pas par le module : c'est la peur qui est fine, pas son
  // recrutement.
  const PAR_TOURNEE = Math.max(1, Math.round((+o.tournee || 3) / PAS));
  const CEDER = Math.max(1, Math.round(2 / PAS));   // rendre la main tous les 2 s
  let t = 0;
  for (let i = 0; i < pas; i++) {
    let _t = performance.now();
    B.pas(PAS);
    CHRONO.sim += performance.now() - _t;
    t += PAS;
    if (peuple && i % PAR_TOURNEE === 0) {
      _t = performance.now();
      await tournee(t);
      CHRONO.tour += performance.now() - _t;
    }
    // On échantillonne à CHAQUE pas — c'est le fil qui décide de garder ou
    // non. Échantillonner moins souvent, c'est rater le pas où un homme meurt.
    _t = performance.now();
    for (let k = 0; k < corps.length; k++) {
      const h = corps[k];
      fils[k].pousser(t, h.x, h.y, CODE[h.etat] ?? 0);
    }
    CHRONO.fil += performance.now() - _t;

    // ON REND LA MAIN, RÉGULIÈREMENT. Le petit serveur des planches vit dans
    // ce processus-ci : tant que la boucle tourne sans jamais céder, il ne
    // répond à personne. À trois cents hommes on ne s'en apercevait pas — la
    // tournée cédait toutes les trois secondes de bataille ; à trois mille,
    // ces trois secondes coûtent assez pour que la page devienne inutilisable
    // au moment précis où l'on veut la regarder. Un `setImmediate` toutes les
    // deux secondes de bataille ne coûte rien et rend le four causant.
    if (i % CEDER === 0) await new Promise((r) => setImmediate(r));
    // Le relevé d'états ne se demande QU'AU MOMENT D'ÉCRIRE. Il était calculé
    // à chaque pas pour être jeté vingt-neuf fois sur trente — `etat()`
    // parcourt tous les corps et fabrique des objets, et la cuisson est
    // tombée de ×20 à ×8,7 le temps réel pour rien.
    if (planches) planches.peutetre(t, corps, () => B.etat().etats,
                                   peuple ? B.peur() : null);
    if (i % 2000 === 0 && i)
      process.stdout.write("  " + Math.round(t) + " s / " + o.duree +
        "  (" + ((Date.now() - t1) / 1000).toFixed(0) + " s de four)\n");
  }
  for (const f of fils) f.fermer();
  process.stdout.write("  temps : simulation " + (CHRONO.sim / 1000).toFixed(1) +
    " s, images clefs " + (CHRONO.fil / 1000).toFixed(1) +
    " s, tournée " + (CHRONO.tour / 1000).toFixed(1) + " s\n");
  const cuisson = (Date.now() - t1) / 1000;
  // LE RAIL, POUR QU'ON LE VOIE. La colonne suit un A* — mais un quart de ce
  // chemin passe par des ruelles, et la toile fine s'éteint au-delà de deux
  // mètres par pixel, chez le viewer comme sur la carte du jeu. On voyait donc
  // des hommes marcher sur du vide, ce qui ressemble à s'y méprendre à une
  // carte et un pathfinding qui ne se superposent pas. Ils se superposent : ce
  // sont les rues qui ne sont pas dessinées à cette échelle.
  //
  // On exporte donc les traces suivies. Une seule en pratique — les escouades
  // partagent leur A* —, quelques centaines de points, rien du tout.
  if (planches) planches.chemins(B.chemins ? B.chemins() : []);
  const vue = planches ? planches.fermer() : null;

  // ON PREND LES ANNALES MAINTENANT. La vérification, plus bas, redresse la
  // même bataille — ce qui remet les annales à zéro. Les lire après, c'est
  // écrire un fichier d'événements vide et ne s'en apercevoir qu'à la lecture.
  const faits = B.faits().slice();

  // --- l'écriture, PAR TRANCHES DE TEMPS -----------------------------------
  //
  // Un seul bloc marchait à trois cents hommes et ne marche pas à dix mille :
  // le sac fait quatre heures, et les images clefs de neuf mille cinq cents
  // corps pèsent alors cent vingt mégaoctets. Personne ne charge cent vingt
  // mégaoctets pour regarder la première minute.
  //
  // On découpe donc le TEMPS, et non les corps — parce que c'est le temps
  // qu'un lecteur parcourt. Dix minutes par fichier, cinq mégaoctets chacun :
  // on ne charge que la tranche qu'on joue, et la suivante pendant qu'on
  // regarde celle-ci.
  //
  // CHAQUE TRANCHE EST AUTOSUFFISANTE, et c'est toute la subtilité. Pour
  // placer un homme à la seconde t il faut les deux images qui l'encadrent —
  // or la précédente peut être tombée AVANT le début de la tranche, et la
  // suivante après sa fin. Chaque tranche emporte donc, pour chaque corps, la
  // dernière image d'avant et la première d'après. Deux images de rab par
  // corps et par tranche ; sans elles, le premier instant de chaque tranche
  // serait faux, et le défaut se verrait comme un hoquet toutes les dix
  // minutes.
  const nom = o.sortie || "portreal.sac";
  const DOSSIER = path.join(MONDE, "sac");
  fs.mkdirSync(DOSSIER, { recursive: true });
  // On repart d'un dossier propre : une cuisson plus courte que la précédente
  // laisserait sinon traîner les tranches de la vieille, que le manifeste ne
  // mentionne plus mais qui pèsent sur le disque.
  for (const f of fs.readdirSync(DOSSIER))
    if (f.startsWith(nom + "-") && f.endsWith(".bin"))
      fs.rmSync(path.join(DOSSIER, f), { force: true });

  // Le temps de chaque fil au CENTIÈME, une fois pour toutes — c'est la
  // monnaie du fichier, et le pas de cinq centièmes y tombe juste.
  for (const f of fils) {
    f.cs = new Int32Array(f.n);
    for (let k = 0; k < f.n; k++) f.cs[k] = Math.round(f.t[k] * 100);
  }

  const CAMP = new Uint8Array(fils.length);
  for (let i = 0; i < fils.length; i++) CAMP[i] = fils[i].camp === "assaut" ? 0 : 1;

  const TR_CS = Math.max(1000, Math.round((+o.tranche || 600) * 100));
  const FIN_CS = Math.round(o.duree * 100);
  const nTr = Math.max(1, Math.ceil(FIN_CS / TR_CS));
  const curseur = new Int32Array(fils.length);   // avance avec les tranches
  const tranches = [];
  let total = 0, octets = 0;

  for (let k = 0; k < nTr; k++) {
    const t0 = k * TR_CS, t1 = Math.min(FIN_CS, (k + 1) * TR_CS);
    const idx = new Uint32Array(fils.length + 1);
    const bornes = [];
    let n = 0;
    for (let i = 0; i < fils.length; i++) {
      const cs = fils[i].cs;
      // La dernière image à `t0` ou avant. Le curseur ne recule jamais : les
      // tranches se suivent, donc on ne rebalaie pas les fils depuis le début
      // à chaque tranche — sinon le découpage coûte le carré du nombre de
      // tranches, ce qui se voit à la vingt-quatrième.
      let a = curseur[i];
      while (a + 1 < cs.length && cs[a + 1] <= t0) a++;
      curseur[i] = a;
      // ... jusqu'à la première à `t1` ou après, celle-là comprise.
      let b = a;
      while (b + 1 < cs.length && cs[b] < t1) b++;
      bornes.push([a, b]);
      n += b - a + 1;
      idx[i + 1] = n;
    }
    const T = new Uint32Array(n), X = new Float32Array(n);
    const Y = new Float32Array(n), E = new Uint8Array(n);
    let p = 0;
    for (let i = 0; i < fils.length; i++) {
      const f = fils[i], [a, b] = bornes[i];
      for (let j = a; j <= b; j++, p++) {
        T[p] = f.cs[j]; X[p] = f.x[j]; Y[p] = f.y[j]; E[p] = f.e[j];
      }
    }
    const fichier = nom + "-" + String(k).padStart(3, "0") + ".bin";
    const bin = Buffer.concat([
      Buffer.from(idx.buffer), Buffer.from(CAMP.buffer),
      Buffer.from(T.buffer), Buffer.from(X.buffer),
      Buffer.from(Y.buffer), Buffer.from(E.buffer),
    ]);
    fs.writeFileSync(path.join(DOSSIER, fichier), bin);
    tranches.push({ f: "sac/" + fichier, t0: t0 / 100, t1: t1 / 100,
                    images: n, octets: bin.length });
    // On garde les vues en mémoire : la vérification qui suit relit le fichier
    // tranche par tranche, et c'est elle qui décide si le découpage est juste.
    tranches[k]._ = { idx, T, X, Y, E };
    total += n; octets += bin.length;
  }

  const fin = B.etat();
  const manifeste = {
    _lisez_moi:
      "Une bataille CUITE. Les positions ne sont pas échantillonnées : ce sont " +
      "des IMAGES CLEFS, et l'on interpole entre deux. Le fichier est découpé " +
      "en TRANCHES DE TEMPS — on ne charge que celle qu'on joue. Chaque tranche " +
      "est autosuffisante : elle emporte, pour chaque corps, la dernière image " +
      "d'avant son début et la première d'après sa fin, sans quoi son premier " +
      "instant serait faux. Un corps s'y lit de index[i] à index[i+1] dans les " +
      "tableaux T (centièmes de s depuis le début de la bataille, PAS depuis la " +
      "tranche), X, Y (mètres) et E (état, cf. etats). Engendré par " +
      "scripts/monde/sac.js — ces fichiers se réécrivent entièrement, n'y " +
      "écrivez rien à la main.",
    porte: o.porte, hommes: o.hommes, duree_s: o.duree, pas_s: PAS,
    tolerance_m: TOLERANCE, etats: ETATS,
    corps: fils.length, images: total, octets: octets,
    binaire: {
      dossier: "sac",
      tranche_s: TR_CS / 100,
      tranches: tranches.map((t) => ({ f: t.f, t0: t.t0, t1: t.t1,
                                       images: t.images, octets: t.octets })),
      disposition: "uint32 index[corps+1], uint8 camp[corps] (0=assaut 1=garde), " +
                   "uint32 t[images] (centièmes de s), float32 x[images], float32 y[images], " +
                   "uint8 etat[images] — petit-boutiste, sans en-tête",
    },
    issue: { morts: fin.morts, blesses: fin.blesses, fuyards: fin.fuyards,
             assaut: fin.assaut, garde: fin.garde,
             verrou: fin.verrou, portes: fin.portes, sac: fin.sac,
             // Comment la nuit s'est décidée quand ce n'est pas la hache qui
             // l'a décidée : le roi versé, ou la salle du Donjon qui a tranché.
             arret: fin.arret, donjon: fin.donjon,
             etats: fin.etats,
             // PAR QUELLE RÈGLE CHACUN EN EST LÀ, au dernier instant. `etats`
             // dit ce qu'ils font, et ne dit rien : « forme » recouvre la
             // réserve laissée en arrière, celui qui attend sa place au seuil
             // et celui dont le repère a fondu. C'est la ligne qu'on lit quand
             // on se demande pourquoi un cinquième d'un corps avance seul.
             branches: fin.branches },
    annales: { fichier: nom + ".annales.json", faits: faits.length },
    cuisson_s: +cuisson.toFixed(1),
  };
  fs.writeFileSync(path.join(MONDE, nom + ".json"),
                   JSON.stringify(manifeste, null, 1), "utf8");

  // --- LES ANNALES ---------------------------------------------------------
  // Un fichier à part, et pas une clef du manifeste. Le manifeste est de la
  // tuyauterie — un lecteur le charge pour savoir où sont les octets ; les
  // annales sont un DOCUMENT, qu'un être humain ouvre et lit d'un bout à
  // l'autre. Les mélanger, c'est obliger le second à charger la première.
  //
  // ELLES SORTENT COMPLÈTES, ET C'EST VOULU. On ne filtre pas au four : une
  // cuisson coûte des minutes, et l'on n'oserait plus changer d'avis sur ce
  // qu'on veut lire. `scripts/monde/annales.js` en tire des vues — par niveau
  // (du tournant au moindre râle) et par aspect (le commandement, la ville, le
  // fer, les ouvrages) — pour le prix d'une lecture, autant de fois qu'on veut.
  // Ce fichier-ci reste la source ; les vues vont dans `exports/`.
  const parQuoi = {};
  for (const f of faits) parQuoi[f.quoi] = (parQuoi[f.quoi] || 0) + 1;
  const annales = {
    _lisez_moi:
      "CE QUI EST ARRIVÉ, dans l'ordre où c'est arrivé. Chaque fait porte son " +
      "heure (secondes depuis le début de l'assaut), son lieu en clair, et de " +
      "quoi le raconter. `recit` est la ligne à lire ; le reste est là pour " +
      "qui veut trier. Engendré par scripts/monde/sac.js avec le sac du même " +
      "nom — les deux se réécrivent ensemble, n'y touchez pas à la main.",
    porte: o.porte, hommes: o.hommes, duree_s: o.duree,
    faits: faits.length, par_quoi: parQuoi,
    // Le récit seul, d'affilée : c'est ce qu'on lit quand on veut savoir ce
    // qui s'est passé sans rien chercher de particulier.
    recit: faits.map(raconter),
    // Et le détail, pour qui veut le lieu au mètre ou l'escouade au numéro.
    detail: faits,
  };
  fs.writeFileSync(path.join(MONDE, nom + ".annales.json"),
                   JSON.stringify(annales, null, 1), "utf8");

  // --- LA VÉRIFICATION, et c'est elle qui décide du format -----------------
  // Un fichier cuit ne vaut que ce que vaut sa relecture. On refait donc
  // tourner LA MÊME bataille — la graine est remise par `dresser`, le déroulé
  // est identique — et l'on compare, à chaque pas et pour chaque corps, la
  // position vraie à celle qu'un lecteur reconstruirait par interpolation.
  // Si l'écart dépasse la tolérance qu'on s'est donnée, le format ment, et
  // aucune jolie compression ne rachète ça.
  //
  // ET ELLE RELIT PAR TRANCHES, comme le fera le lecteur. C'est le seul moyen
  // d'éprouver le découpage : une relecture qui garderait tout en mémoire
  // dirait que le format est bon même si chaque tranche était amputée de ses
  // images de bordure — et le défaut ne se verrait qu'au dixième hoquet, dans
  // le navigateur, six semaines plus tard.
  function relire(i, t) {
    const k = Math.min(tranches.length - 1, Math.floor(t / TR_CS));
    const { idx, T, X, Y, E } = tranches[k]._;
    const a = idx[i], b = idx[i + 1];
    if (b <= a) return null;
    let lo = a, hi = b - 1;
    if (t <= T[a]) return [X[a], Y[a], E[a]];
    if (t >= T[hi]) return [X[hi], Y[hi], E[hi]];
    while (lo < hi - 1) { const m = (lo + hi) >> 1; if (T[m] <= t) lo = m; else hi = m; }
    const dt = T[hi] - T[lo];
    const u = dt > 0 ? (t - T[lo]) / dt : 0;
    return [X[lo] + (X[hi] - X[lo]) * u, Y[lo] + (Y[hi] - Y[lo]) * u, E[lo]];
  }

  let pire = 0, somme = 0, n = 0, fauxEtats = 0;
  B.rejouer(o.porte, o.hommes);
  const c2 = B.troupe();
  let t2 = 0;
  for (let i = 0; i < pas; i++) {
    B.pas(PAS); t2 += PAS;
    // À CHAQUE PAS, pas seulement aux secondes rondes : le fichier date au
    // centième, il doit donc répondre juste à chaque instant qu'il prétend
    // couvrir. Un contrôle plus indulgent que le format ne vérifie rien.
    for (let k = 0; k < c2.length; k++) {
      const r = relire(k, Math.round(t2 * 100));
      if (!r) continue;
      const d = Math.hypot(c2[k].x - r[0], c2[k].y - r[1]);
      somme += d; n++;
      if (d > pire) pire = d;
      if ((CODE[c2[k].etat] ?? 0) !== r[2]) fauxEtats++;
    }
  }

  // --- ce qu'on a gagné ----------------------------------------------------
  const brut = fils.length * pas * 13;          // t + x + y + état, sans rien garder
  const ko = (n) => (n / 1024).toFixed(0) + " Ko";
  process.stdout.write(
    "\n  " + fils.length + " corps, " + pas + " pas\n" +
    "  images clefs : " + total.toLocaleString("fr-FR") +
      "  (" + (total / fils.length).toFixed(1) + " par corps)\n" +
    "  cuit         : " + ko(octets) + "\n" +
    "  échantillonné aurait fait : " + ko(brut) +
      "  → " + (brut / octets).toFixed(0) + " fois moins\n" +
    "  cuisson      : " + cuisson.toFixed(1) + " s pour " + o.duree +
      " s de bataille (×" + (o.duree / cuisson).toFixed(1) + " le temps réel)\n" +
    "\n  relecture (" + n.toLocaleString("fr-FR") + " comparaisons) :\n" +
    "    écart moyen  : " + (somme / n).toFixed(3) + " m\n" +
    "    écart pire   : " + pire.toFixed(3) + " m   (tolérance " + TOLERANCE + " m)\n" +
    "    états faux   : " + fauxEtats + "\n" +
    "\n  annales : " + faits.length + " faits — " +
      Object.entries(parQuoi).sort((a, b) => b[1] - a[1])
        .map(([k, v]) => k + " ×" + v).join(", ") + "\n" +
    faits.slice(0, 14).map((f) => "    " + raconter(f)).join("\n") +
    (faits.length > 14 ? "\n    … et " + (faits.length - 14) + " autres" : "") +
    "\n  tranches : " + tranches.length + " × " + (TR_CS / 100) + " s — " +
      ko(octets / tranches.length) + " en moyenne, " +
      ko(Math.max(...tranches.map((t) => t.octets))) + " la plus lourde\n" +
    "\n  → monde/" + nom + ".json + .annales.json, et les tranches dans monde/sac/\n" +
    (vue ? "  → " + vue.replace(/\\/g, "/") + "\n" : ""));
  // Le petit serveur des planches tient le processus en vie, et c'est voulu :
  // c'est à l'instant où le four s'arrête que la page devient une réglette
  // qu'on tire d'un bout à l'autre de la bataille.
  if (planches)
    process.stdout.write("\n  Les planches restent servies — la réglette se tire " +
                         "maintenant\n  que tout est cuit. Ctrl-C pour rendre la main.\n");
  if (pire > TOLERANCE * 1.5 || fauxEtats)
    process.stdout.write("  ⚠ le fichier ne rend pas ce que la simulation a fait.\n");
}

main().catch((e) => { console.error("sac :", e); process.exit(1); });
