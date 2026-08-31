// monde/monde.js — l'assemblage. Un appel, un monde.
//
//     const monde = await ouvrir({ hote, etiquettes });
//
// C'est la seule pièce que le reste du jeu a besoin de connaître : le banc
// d'essai (/monde3d) et, demain, l'échelle « la ville » du décor s'en servent
// pareillement. Tout le reste — relief, bâti, voirie, enceinte, air, caméra —
// est derrière, module par module, et se remplace sans toucher aux autres.
//
// Rien n'est modélisé ici : on relit les mêmes JSON que Blender et on rebâtit à
// l'identique. Le .blend est l'atelier d'images ; ceci est l'atelier du jeu.
"use strict";
import * as T from "/vendor/three.module.min.js";
import { Relief, urbanite, mer } from "/modules/monde/relief.js";
import { batir as batirBati } from "/modules/monde/bati.js";
import { rubans } from "/modules/monde/voirie.js";
import { batir as batirEnceinte } from "/modules/monde/enceinte.js";
import { poser as poserAir } from "/modules/monde/ciel.js";
import { poser as poserReperes } from "/modules/monde/reperes.js";
import { orbite, VUES } from "/modules/monde/camera.js";
import { poser as poserMaillage } from "/modules/monde/maillage.js";
import { poser as poserFoule } from "/modules/monde/foule.js";
import { poser as poserSurvol } from "/modules/monde/survol.js";
import { signe } from "/modules/monde/signes.js";

// La tranche courante du test de boîte, tenue à part — même raison qu'en
// bati.js : une fermeture par pièce et par visée finit par se voir au
// ramasse-miettes, en plein mouvement de souris.
let T0 = 0, T1 = 0;
function fente(org, dir, min, max) {
  if (Math.abs(dir) < 1e-9) return org >= min && org <= max;
  let a = (min - org) / dir, b = (max - org) / dir;
  if (a > b) { const w = a; a = b; b = w; }
  if (a > T0) T0 = a;
  if (b < T1) T1 = b;
  return T0 <= T1;
}

const json = (u) => fetch(u).then((r) => {
  if (!r.ok) throw new Error(u + " → " + r.status);
  return r.json();
});

export async function ouvrir(o = {}) {
  const hote = o.hote || document.body;
  const racine = o.source || "/monde";
  const dire = o.dire || (() => {});

  dire("le relief, le bâti, les rues…");
  const [TER, BAT, VOIRIE, CARTE, REP, MAILLE, INT] = await Promise.all([
    json(racine + "/terrain"), json(racine + "/bati"),
    json(racine + "/voirie?couche=L1-surface"), json(racine + "/carte"),
    json(racine + "/reperes"),
    // Un lieu peut porter un morceau bâti en vrai maillage plutôt qu'en boîtes
    // instanciées — un château se regarde de près, une ville non. Absent : null.
    json(racine + "/maillage").catch(() => null),
    // Et le DEDANS : une pièce creuse par salle du plan, murs épais et portes
    // percées. Le maillage donne un château plein — on peut en faire le tour,
    // jamais y entrer. Sans cette couche, « la salle » est un point sur une
    // pelouse : le fichier existait, le serveur le servait, personne ne le
    // demandait.
    json(racine + "/interieurs").catch(() => null),
  ]);

  // ---- la toile ------------------------------------------------------------
  const scene = new T.Scene();
  const rendu = new T.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true });
  rendu.setPixelRatio(Math.min(devicePixelRatio, 2));
  rendu.setSize(hote.clientWidth || innerWidth, hote.clientHeight || innerHeight);
  // ACES écrase les tons moyens : une ville de toits bruns y devient une tache
  // noire, et on perd justement la lecture des quartiers. « Neutral » garde le
  // milieu de la courbe et ne brûle que le ciel.
  rendu.toneMapping = T.NeutralToneMapping;
  rendu.toneMappingExposure = 1.12;
  hote.appendChild(rendu.domElement);

  // Le champ de vision est SERRÉ (38°) : un grand angle rapetisse tout ce qu'il
  // embrasse, et c'est la première façon de perdre l'échelle d'une ville.
  const cam = new T.PerspectiveCamera(38, 1, 4, 600000);

  dire("l'air");
  const air = poserAir(scene, rendu, { densite: o.densite });

  // ---- le sol --------------------------------------------------------------
  dire("le relief");
  const relief = new Relief(TER);
  const C = {}; BAT._colonnes.forEach((n, i) => C[n] = i);
  const usage = urbanite(BAT.bati, C, relief, CARTE);
  const sol = relief.maillage(usage);
  const couronne = relief.couronne(o.portee ?? 90000);
  const nappe = mer(o.mer ?? 260000, air.env);
  nappe.position.set(relief.L / 2, relief.H / 2, 0);
  scene.add(sol, couronne, nappe);

  // ---- ce que les hommes ont posé dessus -----------------------------------
  dire("les " + BAT.bati.length.toLocaleString("fr") + " bâtiments");
  const bati = batirBati(BAT);
  dire("les " + VOIRIE.aretes.length.toLocaleString("fr") + " tronçons de rue");
  const voirie = rubans(VOIRIE.aretes, relief);
  dire("la muraille");
  const enceinte = batirEnceinte(CARTE, relief);
  scene.add(voirie, ...bati.objets, ...enceinte.objets);

  // Le maillage : ce qui mérite d'être vu de près, avec ses parois épaisses et
  // ses portes percées. Il vient EN PLUS du bâti, jamais à sa place — c'est au
  // lieu de ne pas livrer deux fois les mêmes murs.
  let maille = null;
  if (MAILLE && MAILLE.index && MAILLE.index.length) {
    dire("le château, pierre à pierre");
    maille = poserMaillage(MAILLE);
    scene.add(maille.objet);
  }

  // Les intérieurs : même format que le maillage, même pose. Ils viennent APRÈS
  // lui, dans ses murs — c'est le creux dedans le plein, et les deux se
  // dessinent en double face pour qu'un mur vu du dedans reste un mur.
  let dedans = null;
  if (INT && INT.index && INT.index.length) {
    dire("les salles, une à une");
    dedans = poserMaillage(INT);
    dedans.objet.name = "Les intérieurs";
    dedans.salles = INT.salles || [];
    scene.add(dedans.objet);
  }

  // ---- les gens ------------------------------------------------------------
  // La foule vient APRÈS le bâti et jamais avant : elle se lit contre lui. Un
  // lieu sans corps rend null, et la couche n'existe simplement pas — on ne
  // propose pas de décocher ce qui n'est pas là.
  dire("les habitants");
  const foule = await poserFoule(scene, {
    source: racine,
    // La caméra vise un point ; en vue oblique elle en est loin derrière, et
    // charger autour d'ELLE chargerait les mauvaises rues.
    vise: () => camera0(),
    surAttroupement: o.surAttroupement,
  });
  // `camera.cible` est le point VISÉ (un Vector3, pas une fonction) : c'est lui
  // qu'il faut suivre, jamais la position de la caméra.
  function camera0() {
    const c = camera && camera.cible;
    return c ? { x: c.x, y: c.y } : { x: cam.position.x, y: cam.position.y };
  }

  // ---- les noms ------------------------------------------------------------
  // Les repères du graphe qui portent un nom de SALLE sont un doublon, et un
  // doublon faux : ils sont semés sur un anneau autour de la cour, à cent
  // mètres des pièces qu'ils nomment (« Les cuisines » du graphe est à 137 m
  // des cuisines creusées). Là où le dedans existe, c'est lui qui dit où sont
  // les salles — le graphe garde les portes, les quais et les sommets.
  const nomsDuDedans = new Set(
    (dedans ? dedans.salles : []).map((s) => (s.nom || "").toLowerCase()));
  const etiq = o.etiquettes || null;
  const reperes = etiq
    ? poserReperes(etiq, (REP.reperes || [])
        .filter((r) => !nomsDuDedans.has((r.nom || "").toLowerCase())), relief)
    : null;

  // ---- la caméra -----------------------------------------------------------
  // ---- le plancher sous les pieds ------------------------------------------
  // Le relief seul ne suffit pas : un château servi en maillage a des planchers
  // au-dessus du terrain, et s'y poser au niveau du sol met le joueur DANS la
  // roche. On lance donc un rai vers le bas depuis un peu au-dessus de lui, et
  // l'on prend la première chose rencontrée — terrain, dalle, marche, chemin de
  // ronde. Les instances du bâti n'en sont PAS : les tester coûterait un demi-
  // million de boîtes par image, et l'on ne monte pas sur les toits d'une ville.
  const rai = new T.Raycaster();
  rai.far = 400;
  const BAS = new T.Vector3(0, 0, -1);
  const depart = new T.Vector3();
  // Les dalles des salles en font partie, et c'est tout l'intérêt : le maillage
  // du château est un bloc plein dont le rai ne rencontre que le TOIT. Entrer
  // dans une chambre du sommet sans ces planchers-là, c'est se poser à 124 m
  // quand la chambre est à 158 — trente-quatre mètres plus bas, dans la pierre.
  const solides = [sol, ...(maille ? [maille.objet] : []),
                   ...(dedans ? [dedans.objet] : []), ...enceinte.muraille,
                   enceinte.edifices].filter(Boolean);
  // La tête a besoin d'un peu d'air au-dessus d'elle : on part de plus haut que
  // les pieds pour que gravir une marche ne consiste pas à passer au travers.
  const ENJAMBEE = 1.1;
  function plancher(x, y, z) {
    const terre = relief.sol(x, y);
    depart.set(x, y, (z ?? terre) + ENJAMBEE);
    rai.set(depart, BAS);
    const touches = rai.intersectObjects(solides, false);
    // On garde le premier plancher qui n'est pas au-dessus de la tête, et jamais
    // sous le terrain : une face de dessous prise à l'envers enterrerait le
    // joueur aussi sûrement que le bug qu'on répare.
    for (const t of touches) {
      if (t.point.z >= terre - 0.2) return Math.max(t.point.z, terre);
    }
    return terre;
  }

  // La caméra n'a pas à connaître le relief ni la scène : elle a besoin d'une
  // hauteur sous les pieds. C'est ce qui rend la vue à la première personne
  // possible sans lui donner la moitié du monde.
  const camera = orbite(cam, rendu.domElement,
    { sol: plancher, ...(o.camera || {}) });
  camera.surChangement(({ altitude }) => air.selonAltitude(altitude));

  // ---- ce qu'il y a sous le curseur ----------------------------------------
  // Chaque couche sait nommer ce qu'elle porte ; survol.js ne fait que les
  // interroger l'une après l'autre et garder la plus proche. Rien ici n'est
  // laissé au raycast général : le bâti a son viseur à lui (bati.js, qui écarte
  // quarante-huit mille volumes en un produit scalaire) et les salles sont des
  // boîtes qu'on croise à la main. Seule l'enceinte, qui compte quelques
  // dizaines de pans, passe par le raycast ordinaire — il est bon marché à
  // cette taille-là et personne n'a besoin de le réécrire.
  const PORTEE = 3500;          // mètres : au-delà, un toit ne se désigne plus
  const TYPES = BAT._types || {};
  const pt = new T.Vector3();

  // Un toit derrière une colline n'est pas sous le curseur : on échantillonne
  // le relief entre l'œil et la trouvaille, et l'on se tait s'il passe devant.
  // Vingt-quatre points suffisent — c'est une colline qu'on cherche, pas un
  // caillou —, et c'est mille fois moins cher que de tirer le rai sur le
  // maillage du terrain.
  function derriereLaColline(rai, t) {
    const o = rai.ray.origin, d = rai.ray.direction;
    for (let i = 1; i < 24; i++) {
      const k = t * i / 24;
      const z = o.z + d.z * k;
      if (relief.sol(o.x + d.x * k, o.y + d.y * k) > z + 1.5) return true;
    }
    return false;
  }

  // La pièce couverte la plus étroite dont l'emprise couvre ce point. Elle sert
  // à nommer un volume que la table des métiers ne nomme pas : les corps du
  // château sont taillés un par pièce (`chateau-septuaire`, `chateau-communs`),
  // et la pièce sous eux porte le nom qui manque. On prend la plus PETITE parce
  // que les grandes se contiennent — la cour et le bourg couvrent tout, et
  // répondre « la cour » à qui montre le septuaire ne serait pas plus juste que
  // de répondre « le château ».
  function salleSous(x, y) {
    if (!dedans) return null;
    let elu = null, aire = Infinity;
    for (const s of dedans.salles) {
      const b = s.boite;
      if (!b || b.length !== 4 || s.couvert === false) continue;
      if (x < b[0] || x > b[2] || y < b[1] || y > b[3]) continue;
      const a = (b[2] - b[0]) * (b[3] - b[1]);
      if (a < aire) { aire = a; elu = s; }
    }
    return elu;
  }

  function sondeBati(rai) {
    const h = bati.viser(rai.ray, PORTEE);
    if (!h || derriereLaColline(rai, h.t)) return null;
    const b = BAT.bati[h.n];
    const usage = b[C.usage];
    // Le métier tel que la table le NOMME, jamais son identifiant : un lieu
    // peut poser des usages que sa table ne nomme pas (les corps du château, à
    // Peyredragon, sont un bloc par salle et se nomment par le dedans), et
    // « chateau-guet » à l'écran est une tuyauterie qui fuit. Faute de nom, on
    // dit le quartier — c'est vrai, c'est lisible, et ça n'invente rien.
    const cat = C.cat !== undefined ? b[C.cat] : (TYPES[usage] || {}).cat;
    const xyz = rai.ray.at(h.t, pt).toArray();
    let nom = (TYPES[usage] || {}).nom || "";
    // Faute de métier nommé, la pièce qui est là-dessous — et faute de pièce,
    // le quartier. On ne montre jamais l'identifiant du métier : « ✴ Le
    // château » se lit encore, « chateau-septuaire » est une tuyauterie qui
    // fuit.
    if (!nom) { const s = salleSous(xyz[0], xyz[1]); nom = s ? (s.nom || "") : ""; }
    return {
      t: h.t, genre: "bati", n: h.n, usage, xyz,
      signe: signe(usage, cat, "bati"),
      titre: nom || b[C.quartier] || "Une maison",
      role: nom ? (b[C.quartier] || "") : "",
    };
  }

  // Les murs, les portes et les grands édifices : leurs instances portent leur
  // nom depuis enceinte.js, une par pan de mur, toutes les mêmes.
  function sondeMurs(rai) {
    const objets = [enceinte.courtine, enceinte.portes, enceinte.edifices]
      .filter(Boolean);
    const l = rai.intersectObjects(objets, false);
    for (const h of l) {
      if (h.distance > PORTEE) break;
      const noms = (h.object.userData || {}).noms || [];
      const nom = noms[h.instanceId] || "";
      if (!nom) continue;
      const quoi = h.object === enceinte.portes ? "porte"
        : (h.object === enceinte.edifices ? "edifice" : "mur");
      return {
        t: h.distance, genre: "mur", xyz: h.point.toArray(),
        signe: signe(null, null, quoi),
        titre: nom,
        role: quoi === "porte" ? "une porte de la ville" : "",
      };
    }
    return null;
  }

  // Le dedans, quand le lieu en a un. On ne tire PAS le rai sur le maillage :
  // soixante-dix mille faces sans arbre de partition, c'est quatre-vingts
  // millisecondes par interrogation — un hoquet à chaque mouvement de souris,
  // pour apprendre le nom d'une pièce. Or les pièces SONT des boîtes, et il y
  // en a trente-quatre : on croise le rai avec elles, et c'est fini.
  //
  // Conséquence assumée : on nomme une salle à travers son mur. C'est déjà ce
  // que fait le plan à l'échelle du quartier (salles.js écrit les noms PAR-
  // DESSUS la pierre), et c'est la bonne réponse — quand on montre du doigt le
  // haut du Tambour, ce qu'on désigne est la chambre qui s'y trouve, pas le
  // moellon qui la cache.
  function sondeDedans(rai) {
    if (!dedans || !dedans.salles.length) return null;
    const o = rai.ray.origin, d = rai.ray.direction;
    let elu = null, meilleure = PORTEE;
    for (const s of dedans.salles) {
      const b = s.boite;
      if (!b || b.length !== 4) continue;
      const bas = s.sol_z != null ? s.sol_z : s.centre[2];
      const haut = bas + (s.hauteur || 6);
      T0 = -Infinity; T1 = Infinity;
      if (!fente(o.x, d.x, b[0], b[2])) continue;
      if (!fente(o.y, d.y, b[1], b[3])) continue;
      if (!fente(o.z, d.z, bas, haut)) continue;
      if (T1 < 0) continue;
      // Dedans, on prend la sortie : la pièce où l'on se tient ne doit pas
      // masquer ce qu'on regarde, elle répond quand il n'y a rien d'autre.
      const t = T0 > 0 ? T0 : T1;
      if (t < meilleure) { meilleure = t; elu = s; }
    }
    if (!elu) return null;
    const bas = elu.sol_z != null ? elu.sol_z : elu.centre[2];
    const couvert = elu.couvert !== false;
    return {
      t: meilleure, genre: "salle", id: elu.id,
      xyz: rai.ray.at(meilleure, pt).toArray(),
      boite: elu.boite, bas, haut: bas + (elu.hauteur || 6), couvert,
      signe: signe(elu.id, null, couvert ? "salle" : "salle-dehors"),
      titre: elu.nom || elu.id, role: "",
    };
  }

  // Une salle et un volume peuvent se disputer le même point, et c'est le
  // `couvert` de la pièce qui tranche — ce qui n'est pas un détail d'affichage
  // mais la différence entre une pièce et une enceinte :
  //  - **à ciel ouvert** (le bourg, la cour, le quai, les lices), la boîte est
  //    un contenant : ce qu'on montre du doigt DEDANS est le séchoir, pas « le
  //    bourg ». Sans cette règle, la boîte gagnerait toujours — elle commence à
  //    son bord — et pas une maison du bourg ne pourrait plus être nommée.
  //  - **couverte**, le volume et la pièce sont la MÊME chose vue deux fois :
  //    le bâti n'en donne que la carcasse (« chateau-guet »), le dedans en
  //    donne le nom (« Le chemin de ronde »). La pièce gagne.
  function sondeBatie(rai) {
    const b = sondeBati(rai), s = sondeDedans(rai);
    if (!b || !s) return b || s;
    const p = b.xyz, q = s.boite;
    const dedansElle = q && p[0] >= q[0] && p[0] <= q[2] && p[1] >= q[1]
      && p[1] <= q[3] && p[2] >= s.bas - 1 && p[2] <= s.haut + 1;
    if (dedansElle) return s.couvert ? s : b;
    return b.t < s.t ? b : s;
  }

  const survol = etiq ? poserSurvol({
    hote: etiq, canevas: rendu.domElement, cam,
    sondes: [sondeBatie, sondeMurs],
  }) : null;

  const couches = [
    { nom: "Le relief", objets: [sol] },
    { nom: "Le lointain", objets: [couronne] },
    { nom: "La mer", objets: [nappe] },
    { nom: "Les rues", objets: [voirie] },
    { nom: "Le bâti", objets: bati.objets },
    { nom: "La muraille", objets: enceinte.muraille },
    { nom: "Les monuments", objets: [enceinte.edifices] },
    ...(maille ? [{ nom: "Le château", objets: [maille.objet] }] : []),
    ...(dedans ? [{ nom: "Les intérieurs", objets: [dedans.objet] }] : []),
    ...(foule ? [{ nom: "Les gens", objets: [foule.objet], eteinte: true }] : []),
    { nom: "Les noms", objets: [], noms: true },
  ];

  function redimensionner() {
    const w = hote.clientWidth || innerWidth, h = hote.clientHeight || innerHeight;
    // Une page chargée dans un onglet masqué mesure ZÉRO partout — hôte comme
    // fenêtre. On sortait alors avec une toile de 0×0, c'est-à-dire une ville
    // noire, et rien ne revenait la corriger : « resize » ne se déclenche pas
    // quand un onglet redevient visible. L'observateur ci-dessous rattrape le
    // premier vrai calcul de mise en page ; ici on refuse simplement d'écrire
    // une taille absurde.
    if (w < 2 || h < 2) return;
    cam.aspect = w / h;
    cam.updateProjectionMatrix();
    rendu.setSize(w, h);
  }
  redimensionner();
  addEventListener("resize", redimensionner);
  new ResizeObserver(redimensionner).observe(hote);

  let tourne = false, surImage = null;
  function image() {
    if (!tourne) return;
    requestAnimationFrame(image);
    // La foule se remet à jour AVANT le rendu, et seulement si elle est
    // allumée : éteinte, elle ne coûte pas une soustraction.
    // La hauteur de la toile, en pixels : la foule s'en sert pour garder ses
    // points lisibles quel que soit le recul. La caméra la porte parce qu'elle
    // est la seule chose que toutes les couches reçoivent déjà.
    cam.__hauteurPx = rendu.domElement.clientHeight || 800;
    if (foule) foule.maj(cam, horloge.minute, horloge.jour);
    rendu.render(scene, cam);
    if (reperes) reperes.suivre(cam, rendu.domElement.clientWidth, rendu.domElement.clientHeight);
    if (survol) survol.suivre();
    if (surImage) surImage();
  }

  // L'horloge n'appartient PAS à cette couche : elle est celle de la partie
  // (monde.date), et le décor ne fait que la lire. Deux horloges qui avancent,
  // c'est une partie qui diverge.
  const horloge = { minute: o.minute ?? 6 * 60 + 45, jour: o.jour ?? 24 };

  return {
    T, scene, cam, rendu, relief, camera, air, reperes, couches, VUES, foule,
    horloge, survol,
    /**
     * Une salle du dedans, par son id de plan — son centre, sa dalle, sa
     * hauteur, ses portes. C'est l'adresse à laquelle on POSE quelqu'un : elle
     * est dans la pièce, pas sur le toit du bâtiment qui la contient.
     */
    salle(id) {
      if (!dedans || !id) return null;
      return dedans.salles.find((s) => s.id === id) || null;
    },
    /** Toutes les pièces du dedans, telles qu'elles ont été creusées. */
    salles() { return dedans ? dedans.salles : []; },
    /** L'heure du monde, lue depuis la partie. */
    heure(minute, jour) {
      horloge.minute = minute;
      if (jour !== undefined) horloge.jour = jour;
      // L'heure ne sert plus seulement à faire marcher la foule : elle mène
      // aussi le soleil. Deux choses qui doivent bouger ensemble — une ville
      // qui rentre se coucher sous un soleil de midi ne veut rien dire.
      if (air && air.heure) air.heure(horloge.minute);
    },
    donnees: { TER, BAT, VOIRIE, CARTE, REP, MAILLE },
    compte: {
      batiments: BAT.bati.length,
      troncons: VOIRIE.aretes.length,
      relief: [TER.nx, TER.ny, TER.res_m],
      murs: enceinte.nombre,
      maillage: maille ? maille.faces : 0,
    },
    demarrer(f) { surImage = f || null; if (!tourne) { tourne = true; image(); } },
    arreter() { tourne = false; },
    dessiner() { rendu.render(scene, cam); },
    redimensionner,
    disposer() {
      tourne = false;
      if (survol) survol.disposer();
      removeEventListener("resize", redimensionner);
      scene.traverse((x) => {
        if (x.geometry) x.geometry.dispose();
        if (x.material) [].concat(x.material).forEach((m) => m.dispose());
      });
      rendu.dispose();
      rendu.domElement.remove();
    },
  };
}
