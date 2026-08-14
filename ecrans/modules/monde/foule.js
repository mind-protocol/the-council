// monde/foule.js — les habitants dans le décor, à trois grains.
//
// Une foule qui ne dit rien est un économiseur d'écran coûteux. Celle-ci doit
// porter ce que le joueur ne pouvait pas savoir autrement : que les puits sont
// pleins à six heures, que le marché est noir de monde un jour de disette, que
// le flux s'arrête à une porte parce qu'on l'a fermée.
//
// LE PIÈGE, ET LA SORTIE. Vue de haut, la ville fait cinq kilomètres : un
// habitant y vaut un pixel, et quatre cent mille pixels orange sur des toits
// orange ne font pas une foule, ils font du grain. La réponse n'est pas de
// mieux dessiner mais de CHANGER DE NATURE avec la distance :
//
//   la ville entière   aucun individu — un semis d'un corps sur vingt-cinq,
//                      qui se lit comme une densité et bat au rythme des heures
//   le quartier        des points, mais seulement les SORTIS. Les 85 % restés
//                      chez eux ne sont jamais dessinés : ils n'apportent rien
//                      et coûteraient tout
//   la rue             tout le monde, un point par personne
//
// C'est la même donnée à trois grains, pas trois systèmes. Et le budget ne
// s'optimise pas : il disparaît, parce qu'on ne calcule jamais la position de
// quelqu'un qu'on ne dessinera pas.
//
// La couleur est FROIDE, et c'est un choix contre le fond : les toits de
// Port-Réal sont rouge-brun saturé, une foule chaude s'y noie. Le bleu pâle est
// la seule chose de la palette qui ne se confonde avec rien.
"use strict";
import * as T from "/vendor/three.module.min.js";
import * as G from "/modules/monde/gens.js";
import * as J from "/modules/monde/journee.js";

const PLAFOND = 14000;        // points dessinés au plus, tous grains confondus
// Ceux qui ont un nom : ils se distinguent de la foule sans la quitter. Or
// pâle, parce que c'est la couleur des repères du décor et qu'on les cherche
// du regard comme on cherche un nom sur une carte.
const COULEUR_NOMME = 0xf0d089;

// --- de quoi une foule est FAITE ------------------------------------------
// Le semis était bleu pâle, uniformément, et pour une bonne raison : les toits
// de Port-Réal sont rouge-brun saturé et une foule chaude s'y noie. Mais un
// bleu unique ne fait pas des gens, il fait une donnée — on lisait une densité,
// on ne voyait personne.
//
// La sortie n'est pas de renoncer au contraste, c'est de le déplacer : ce qui
// détache un habitant de son toit n'est plus sa teinte mais sa FORME (une
// silhouette debout, avec une tête) et sa CLARTÉ (des laines pâles sur des
// tuiles sombres). La couleur redevient alors ce qu'elle est dans la rue : de
// la laine, du lin, du cuir, et quelques teintures que seuls quelques-uns
// peuvent payer.
//
// Ce sont des teintures d'époque et pas une palette d'écran : garance et
// gaude pour les rares, guède délavée pour les moins pauvres, et pour presque
// tout le monde la laine telle qu'elle sort du mouton. Les dernières sont les
// plus fréquentes, et c'est l'ordre de ce tableau qui le dit — le tirage pèse
// vers la fin.
const LAINES = [
  0xb04a3a, // garance — le rouge des riches, un sur trente
  0x7a8b4a, // gaude et guède mêlées, un vert d'herbe passée
  0x5b6e8c, // guède délavée, le bleu du peuple qui peut teindre
  0x8a6b4a, // brun de noix
  0x9a8f78, // laine grise
  0xa89a7c, // écru
  0xbfae90, // lin blanchi au soleil
  0xc4b59a, // laine de mouton, non teinte
];
// La tête ne peut pas avoir sa propre couleur : un point n'a qu'une teinte de
// vertex, et elle multiplie toute la texture. On l'approche donc par un beige
// très clair dans le dessin — multiplié par n'importe quelle laine, il reste
// plus clair et plus chaud que le corps, ce qui suffit à le lire comme un
// visage. Le seul vrai remède serait un shader, et une tête ne le vaut pas.
const TETE = "#f0e2d2";

/**
 * La silhouette, dessinée une fois dans un canvas et servie à tous les points.
 * Vue de face et toujours face à la caméra — un point de three.js est un
 * panneau qui se tourne, on ne lui demandera pas de profil.
 *
 * Le dessin est en NIVEAUX DE GRIS et il est multiplié par la couleur du
 * vertex : le corps est à mi-clarté (il prendra la laine), la tête est proche
 * du blanc (elle restera claire quelle que soit la laine). C'est ce qui donne
 * une tête et un vêtement avec une seule texture et un seul appel de dessin.
 */
function silhouette() {
  const N = 64;
  const c = document.createElement("canvas");
  c.width = c.height = N;
  const g = c.getContext("2d");
  g.clearRect(0, 0, N, N);
  const corps = "#8f8f8f", tete = TETE;
  // Les jambes : deux fuseaux qui se rejoignent. Sans elles, une silhouette
  // lue de loin ressemble à une bouteille.
  g.fillStyle = corps;
  g.beginPath();
  g.moveTo(N * 0.40, N * 0.58); g.lineTo(N * 0.44, N * 0.97);
  g.lineTo(N * 0.52, N * 0.97); g.lineTo(N * 0.50, N * 0.58);
  g.closePath(); g.fill();
  g.beginPath();
  g.moveTo(N * 0.50, N * 0.58); g.lineTo(N * 0.56, N * 0.97);
  g.lineTo(N * 0.64, N * 0.97); g.lineTo(N * 0.60, N * 0.58);
  g.closePath(); g.fill();
  // Le torse : épaules larges, taille prise — c'est la seule chose qui se lit
  // encore à quatre pixels de haut.
  g.beginPath();
  g.moveTo(N * 0.30, N * 0.34); g.lineTo(N * 0.70, N * 0.34);
  g.lineTo(N * 0.64, N * 0.62); g.lineTo(N * 0.36, N * 0.62);
  g.closePath(); g.fill();
  // La tête, et le cou qui l'attache.
  g.fillStyle = tete;
  g.fillRect(N * 0.45, N * 0.26, N * 0.10, N * 0.10);
  g.beginPath();
  g.arc(N * 0.50, N * 0.19, N * 0.115, 0, Math.PI * 2);
  g.fill();
  const t = new T.CanvasTexture(c);
  t.colorSpace = T.SRGBColorSpace;
  return t;
}

// À quelle altitude de caméra on change de grain, et de combien on échantillonne.
// Les seuils sont en mètres au-dessus du sol : au-delà de 1 200 m on embrasse
// la ville, en dessous de 300 m on est dans une rue.
// À aucun grain on ne dessine ceux qui sont chez eux : ils sont DANS les murs,
// et un point posé au milieu d'une maison est une erreur de lecture, pas une
// information. Le semis ne montre jamais que la ville en mouvement.
const GRAINS = [
  { altitude: 1200, sur: 25, taille: 9.0 },
  { altitude: 300,  sur: 4,  taille: 3.5 },
  { altitude: 0,    sur: 1,  taille: 1.8 },
];

const grainPour = (alt) => GRAINS.find((g) => alt >= g.altitude) || GRAINS[GRAINS.length - 1];

// Le plancher de lisibilité, en pixels. En deçà, un habitant n'est plus une
// silhouette mais un grain : il ne se distingue ni du bruit du toit qu'il
// survole, ni de l'antialiasing. Depuis qu'il y a une forme à lire — une tête,
// des épaules, deux jambes — il en faut davantage : sous quatre pixels et demi
// de haut, la silhouette redevient le carré qu'elle était.
//
// Neuf et non quatre et demi : à quatre pixels et demi, une foule de deux cent
// soixante personnes n'allumait qu'un millième de l'écran — mesuré, et présenté
// à tort comme un succès parce qu'on comptait des pixels au lieu de regarder
// une proportion. Un habitant doit peser à l'écran ce qu'un habitant pèse dans
// la rue : quelque chose qu'on voit sans le chercher.
const MIN_PX = 9;

/**
 * La taille EN MÈTRES qu'il faut donner à un point pour qu'il occupe au moins
 * `MIN_PX` pixels à la distance où l'on regarde.
 *
 * La formule est celle du nuanceur de three.js, et elle ne fait PAS intervenir
 * le champ de vision : `gl_PointSize = size * (hauteur / 2) / distance`. On
 * avait glissé un `tan(fov/2)` là-dedans par analogie avec la projection des
 * triangles, ce qui surestimait chaque silhouette d'un facteur trois — on
 * croyait dessiner des gens de dix pixels, on en dessinait d'un pixel. C'est ce
 * qui restait après tout le reste, et c'était l'essentiel.
 */
function tailleMini(cam, vise) {
  const H = (cam.__hauteurPx || 0) || 800;   // posée par monde.js à chaque image
  const d = Math.max(1, Math.hypot(cam.position.x - vise.x,
                                   cam.position.y - vise.y, cam.position.z));
  return MIN_PX * 2 * d / H;
}

export async function poser(scene, o = {}) {
  const source = o.source || "/monde";
  // Un lieu sans corps n'a pas de foule : on rend null et l'appelant n'ajoute
  // simplement pas la couche. Pas d'erreur, pas de couche vide à décocher.
  let manif;
  try {
    manif = await G.manifeste(source);
    await J.table(source);
  } catch (e) { return null; }
  const rangs = J.rangs(manif);
  // Les services à ciel ouvert, dits par la table (`besoins.py`). Une table
  // ancienne qui ne les déclare pas ne fait rien disparaître : sans la clef, on
  // dessine tout le monde comme avant.
  const table = await J.table(source);
  const pleinAir = new Set(table.plein_air || table.services || []);
  // Les corps décidés en jeu. Un lieu qui n'en a pas rend un objet vide : la
  // couche marche sans, elle est simplement anonyme.
  let nommes = { liens: {}, corps: [] };
  try {
    nommes = await fetch(source + "/corps").then((r) => r.ok ? r.json() : nommes);
  } catch (e) {}
  const CREES = (nommes.corps || []).filter((c) => c.bat !== undefined);
  let voirie = null;
  // Le graphe des rues n'est chargé que si la foule est allumée : c'est un
  // demi-mégaoctet et trois cents millisecondes qu'on ne paie pas d'avance.
  const graphe = () => voirie || (voirie = J.voirie(source));

  const pos = new Float32Array(PLAFOND * 3);
  const col = new Float32Array(PLAFOND * 3);
  const geo = new T.BufferGeometry();
  geo.setAttribute("position", new T.BufferAttribute(pos, 3));
  geo.setAttribute("color", new T.BufferAttribute(col, 3));
  geo.setDrawRange(0, 0);
  const mat = new T.PointsMaterial({
    size: 3.5, vertexColors: true, sizeAttenuation: true,
    map: silhouette(),
    // PAS d'`alphaTest` : mesuré, il fait disparaître le nuage entier — zéro
    // pixel à l'écran contre trois cents sans lui. Il n'est de toute façon pas
    // nécessaire ici, `depthWrite` étant déjà à faux : rien ne s'écrit dans le
    // tampon de profondeur, donc rien ne peut mal s'y trier.
    //
    // ET PAS DE TEST DE PROFONDEUR NON PLUS. Le rendu du monde est bâti sur un
    // tampon de profondeur LOGARITHMIQUE — nécessaire pour tenir six cent mille
    // mètres de portée sans que les murs vibrent —, et ce tampon-là se calcule
    // dans le nuanceur de fragments. Les points n'y écrivent pas leur
    // profondeur comme les triangles : le test les rejette à tort, et de façon
    // erratique. Mesuré : douze pixels avec, cent onze sans, et rehausser les
    // silhouettes de quatre mètres n'y changeait rien — donc ce n'était pas
    // l'assise, c'était le test lui-même.
    //
    // Le prix est connu et assumé : une foule se voit à travers une colline ou
    // un mur. C'est exactement le marché que passent déjà `vous.js` et
    // `acteurs.js`, et pour la même raison — mieux vaut des gens qu'on voit à
    // travers la pierre que des gens qu'on ne voit jamais.
    depthTest: false,
    transparent: true, opacity: 0.95, depthWrite: false,
  });
  const nuage = new T.Points(geo, mat);
  nuage.frustumCulled = false;
  nuage.visible = false;
  nuage.renderOrder = 3;
  scene.add(nuage);

  // Les laines, prêtes à l'emploi. Le tirage pèse vers la fin du tableau —
  // `u * u` prend deux fois plus souvent la seconde moitié — parce que la
  // garance coûte cher et que la laine grise ne coûte rien.
  const LAINE = LAINES.map((h) => new T.Color(h));
  const cNomme = new T.Color(COULEUR_NOMME);
  const teint = new T.Color();

  /** La laine de quelqu'un — la même toute sa vie, tirée de son identité. */
  function habit(cel, k, out) {
    const id = J.ident(cel, k);
    // Un hachage, pas un tirage : on ne stocke rien et l'homme du coin de la
    // rue porte le même habit demain qu'aujourd'hui.
    let h = (id ^ 0x5f3a7b1d) >>> 0;
    h = Math.imul(h ^ (h >>> 15), 2246822519) >>> 0;
    const u = ((h ^ (h >>> 13)) >>> 0) / 4294967296;
    const c = LAINE[Math.min(LAINE.length - 1, Math.floor(u * u * LAINE.length))];
    // Deux hommes en laine grise ne sont pas de la même laine : un peu de
    // clarté en plus ou en moins, tiré du même hachage.
    const k2 = 0.88 + (((h >>> 8) & 0xff) / 255) * 0.26;
    return out.copy(c).multiplyScalar(k2);
  }
  const P = { x: 0, y: 0, z: 0, quoi: "chez", vers: null };
  let cellules = [], enCharge = false, cle = "";
  const compte = { dessines: 0, dehors: 0, cellules: 0, grain: 1,
                   nommes: CREES.length + Object.keys(nommes.liens || {}).length };

  // --- les attroupements ----------------------------------------------------
  // Le SEUL événement que cette couche sache produire, et il ne devient jamais
  // un menu : au-delà d'un seuil, dans une cellule, hors des heures où un
  // rassemblement va de soi, ce n'est plus de la circulation — c'est un monde
  // qui se rassemble, et ça remonte au MJ comme n'importe quel franchissement.
  const SEUIL = o.seuil ?? 400;
  const dits = new Map();
  function guetter(clef, n, minute) {
    if (n < SEUIL) { dits.delete(clef); return; }
    const marche = minute > 8 * 60 && minute < 12 * 60;
    if (marche) return;               // un marché plein n'est pas un attroupement
    if (dits.has(clef)) return;
    dits.set(clef, minute);
    if (o.surAttroupement) o.surAttroupement({ cellule: clef, ames: n, minute });
  }

  // Un bourg n'est pas une capitale. Port-Réal a quatre cent mille âmes et il
  // faut la pagination ; Peyredragon en a huit cents, réparties sur cinq
  // cellules qui tiennent dans un demi-mégaoctet. Charger « autour de la
  // caméra » y produit régulièrement ZÉRO habitant — le château est à l'ouest,
  // le bourg à l'est, et un rayon de trois cents mètres ne rencontre personne.
  // Sous ce seuil, on prend donc tout le lieu d'un coup, une fois.
  // Le rayon reste BORNÉ à ce que le manifeste couvre : `G.autour` balaie une
  // grille, et un rayon « infini » y coûterait des millions d'itérations pour
  // cinq cellules.
  const PETIT = 20000;
  const tout = (() => {
    if ((manif.total || 0) > PETIT) return null;
    const c = Object.values(manif.cellules || {});
    if (!c.length) return null;
    const m = manif.cellule_m || 250;
    const x0 = Math.min(...c.map((v) => v.x0)), x1 = Math.max(...c.map((v) => v.x0)) + m;
    const y0 = Math.min(...c.map((v) => v.y0)), y1 = Math.max(...c.map((v) => v.y0)) + m;
    return { x: (x0 + x1) / 2, y: (y0 + y1) / 2,
             rayon: Math.max(x1 - x0, y1 - y0) / 2 + m };
  })();

  async function charger(x, y, rayon) {
    if (tout) { x = tout.x; y = tout.y; rayon = tout.rayon; }
    const k = Math.round(x / 250) + ":" + Math.round(y / 250) + ":" + rayon;
    if (k === cle || enCharge) return;
    enCharge = true;
    try {
      cellules = await G.autour(x, y, rayon, source);
      cle = k;
    } finally { enCharge = false; }
  }

  return {
    objet: nuage,
    compte,
    /** Allumer ou éteindre — la couche ne coûte rien tant qu'elle est éteinte. */
    get visible() { return nuage.visible; },
    set visible(v) { nuage.visible = !!v; },

    /**
     * Une image. `cam` donne le point regardé et l'altitude ; `minute` et
     * `jour` viennent de l'horloge du monde, jamais d'ici — cette couche ne
     * tient aucune horloge, elle lit celle de la partie.
     */
    async maj(cam, minute, jour) {
      if (!nuage.visible) return;
      const alt = Math.max(1, cam.position.z);
      let g = grainPour(alt);
      // L'échantillonnage est une réponse à QUATRE CENT MILLE habitants, pas une
      // règle de dessin. Sur un bourg de huit cents âmes il ne fait qu'une
      // chose : effacer les trois quarts des gens qu'on a — et le plafond de
      // quatorze mille points n'était même pas approché. Sous le seuil des
      // petits lieux, on dessine tout le monde, quelle que soit la hauteur.
      if (tout && g.sur > 1) g = { altitude: g.altitude, sur: 1, taille: g.taille };
      // On regarde le point visé, pas la caméra : de biais, la caméra est
      // loin derrière ce qu'on observe, et l'on chargerait les mauvaises rues.
      const vise = o.vise ? o.vise() : { x: cam.position.x, y: cam.position.y };
      const rayon = alt > 1200 ? 1000 : alt > 300 ? 500 : 250;
      // LA TAILLE SE DÉCIDE AVANT DE POSER LES GENS, et pas après : un point est
      // un panneau CENTRÉ sur sa position, et sa profondeur est celle de son
      // centre — une seule, pour tout le panneau. Posé à quatre-vingt-dix
      // centimètres du sol alors qu'il fait neuf mètres de haut, il est enterré
      // jusqu'aux épaules, et en vue oblique le terrain qui le précède le rejette
      // D'UN BLOC : mesuré, douze pixels avec le test de profondeur contre cent
      // onze sans. On croyait à un défaut de taille ; c'était un défaut d'assise.
      // La silhouette est dessinée tête en haut, pieds en bas : son centre doit
      // donc être à MI-HAUTEUR du panneau au-dessus du sol, et elle se tient
      // alors debout dessus au lieu d'y être plantée.
      const taille = Math.max(g.taille, tailleMini(cam, vise));
      const assise = taille / 2;
      charger(vise.x, vise.y, rayon);
      if (!cellules.length) return;
      const v = await graphe();

      let n = 0, dehors = 0;
      for (const cel of cellules) {
        let ici = 0;
        for (let k = 0; k < cel.n; k += g.sur) {
          J.ou(cel, k, jour, minute, v, rangs, P);
          if (P.quoi === "chez") continue;
          dehors += g.sur;
          if (P.quoi === "sur-place") ici += g.sur;
          // Arrêté SOUS UN TOIT : il n'est pas plus visible que celui qui dort
          // chez lui, et la règle est la même — on ne pose pas un point au
          // milieu d'un bâtiment. Le tas qu'on dessinait dans les cuisines du
          // château était caché par le maillage, et l'on croyait la ville vide
          // alors qu'on lui dessinait des habitants dans la pierre. Ceux du
          // puits, de la grève, du quai, de l'étal et du chemin de ronde
          // restent : eux sont dehors pour de bon.
          if (P.quoi === "sur-place" && !pleinAir.has(P.vers)) continue;
          if (n >= PLAFOND) continue;
          pos[n * 3] = P.x; pos[n * 3 + 1] = P.y; pos[n * 3 + 2] = P.z + assise;
          habit(cel, k, teint);
          // Ce que la couleur disait avant — qui marche, qui est arrêté — n'est
          // pas perdu : il passe dans la CLARTÉ. Celui qui est arrêté à l'étal
          // ou dans la file s'assombrit d'un quart ; celui qui va quelque part
          // garde son plein éclat. On lit toujours le flux d'un coup d'œil, et
          // l'on a des gens plutôt qu'un code de couleurs.
          if (P.quoi !== "route") teint.multiplyScalar(0.76);
          col[n * 3] = teint.r; col[n * 3 + 1] = teint.g; col[n * 3 + 2] = teint.b;
          n++;
        }
        guetter(cel.clef, ici, minute);
      }
      // Les corps CRÉÉS : ceux qui n'empruntent celui de personne. Ils sont à
      // leur adresse, sans journée — leur position à la minute près relève des
      // scènes, pas de la foule. On les pose quand même, parce qu'un Donjon
      // Rouge où l'on sait que le roi est là se regarde autrement.
      for (const c of CREES) {
        if (n >= PLAFOND) break;
        pos[n * 3] = c.x; pos[n * 3 + 1] = c.y; pos[n * 3 + 2] = c.z + assise;
        col[n * 3] = cNomme.r; col[n * 3 + 1] = cNomme.g; col[n * 3 + 2] = cNomme.b;
        n++;
      }
      geo.attributes.position.needsUpdate = true;
      geo.attributes.color.needsUpdate = true;
      geo.setDrawRange(0, n);
      // La taille est donnée en MÈTRES et le point rétrécit avec la distance :
      // à huit cents mètres de recul, un point de trois mètres cinquante occupe
      // un tiers de pixel, et quatre mille habitants n'allument pas cent
      // quarante pixels sur des toits bruns. Mesuré, pas supposé — c'est
      // exactement ce qu'on voyait : rien.
      //
      // On garde donc la taille en mètres, mais avec un PLANCHER à l'écran :
      // en dessous de deux pixels et demi, un homme cesse d'être un homme et
      // devient un grain de bruit. C'est la même discipline que pour la balise
      // du joueur et les gens de la salle — de près sa taille vraie, de loin
      // une taille lisible. (Elle est calculée plus haut, avant la boucle :
      // c'est elle qui donne l'assise, et l'assise doit être connue au moment
      // où l'on pose chacun.)
      mat.size = taille;
      compte.dessines = n; compte.dehors = dehors;
      compte.cellules = cellules.length; compte.grain = g.sur;
    },

    disposer() {
      scene.remove(nuage);
      geo.dispose(); mat.dispose();
    },
  };
}
