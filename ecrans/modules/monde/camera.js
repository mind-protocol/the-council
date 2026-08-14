// monde/camera.js — l'orbite, à la main.
//
// Un contrôle importé de 300 lignes pour trois gestes, c'est une dépendance
// qu'on nourrit sans raison. Glisser tourne, la molette approche, le clic droit
// déplace — et le pas de la molette est PROPORTIONNEL à la distance : c'est ce
// qui permet de passer de mille mètres au-dessus de la baie à un homme dans une
// ruelle sans jamais changer d'outil.
//
// La caméra est en z-up : on ne tord pas les données du monde pour plaire à la
// convention de three.js.
"use strict";
import * as T from "/vendor/three.module.min.js";

export function orbite(cam, canevas, opts = {}) {
  cam.up.set(0, 0, 1);
  const cible = new T.Vector3(...(opts.cible || [2750, 1900, 40]));
  let rayon = opts.rayon ?? 2600;
  let theta = opts.theta ?? Math.PI * 0.78;
  let phi = opts.phi ?? 0.95;                 // 0 au zénith
  // Douze mètres de recul minimum, c'était un toit qu'on ne pouvait pas
  // approcher : à trois mètres, on lit une porte et l'épaisseur d'un mur.
  const min = opts.min ?? 3, max = opts.max ?? 40000;
  let auChangement = opts.auChangement || null;
  let auMode = opts.auMode || null;

  // ---- à pied --------------------------------------------------------------
  // La vue « vous » n'est pas une autre caméra : c'est la même, posée sur le
  // sol. `cible` cesse d'être le point qu'on regarde et devient l'endroit où
  // l'on POSE LES PIEDS — ce qui vaut d'être dit, parce que la foule et le
  // chargement des rues se règlent dessus et continuent donc de suivre le
  // joueur sans rien savoir du changement.
  const OEIL = 1.68;          // hauteur d'yeux, en mètres
  // m/s : marcher, puis courir. Ce ne sont PAS les allures d'un homme (1,4 et
  // 4) et c'est délibéré — un joueur qui traverse une cour n'a pas la patience
  // d'un piéton, et vingt secondes pour aller d'un mur à l'autre font croire
  // que la touche ne répond pas. On garde l'échelle du monde, on presse le pas.
  const PAS = 6, COURSE = 20;
  let apied = false;
  // Le sol vient de monde.js, injecté : sans lui, on marcherait à plat au
  // niveau de la mer et l'on traverserait le Dragonmont.
  //
  // Il prend TROIS arguments, et le troisième est tout le sujet : la hauteur
  // d'où l'on cherche. Un château servi en maillage a des planchers AU-DESSUS du
  // terrain — se poser sur `relief.sol` à Peyredragon, c'est se retrouver sous
  // la roche, dans le noir, à travers le sol. On cherche donc le premier
  // plancher SOUS ses pieds actuels, ce qui donne du même coup les escaliers,
  // les étages et le chemin de ronde sans un cas particulier.
  let sol = opts.sol || (() => 0);
  let dernier = 0;            // horodatage du dernier pas, pour la durée réelle

  function poserApied() {
    phi = Math.max(0.12, Math.min(Math.PI - 0.12, phi));
    cible.z = sol(cible.x, cible.y, cible.z);
    cam.position.set(cible.x, cible.y, cible.z + OEIL);
    // On regarde DANS l'axe, pas vers un point : le devant est l'opposé du
    // décalage d'orbite, ce qui garde exactement la même convention de theta —
    // et donc la même table ZQSD, sans un signe à retourner.
    const s = Math.sin(phi);
    cam.up.set(0, 0, 1);
    cam.lookAt(cam.position.x - s * Math.cos(theta),
               cam.position.y - s * Math.sin(theta),
               cam.position.z - Math.cos(phi));
    if (auChangement) auChangement({ rayon, phi, theta, cible, altitude: cam.position.z });
  }

  function poser() {
    if (apied) return poserApied();
    // L'angle est LIBRE : on ne barre ni le zénith ni l'horizon, et l'on
    // s'autorise à passer dessous. Le `up` calculé plus bas reste valide à
    // toute latitude, donc rien ne se casse en franchissant les pôles ; on
    // ramène seulement phi dans [0, π] par symétrie pour que theta ne soit pas
    // pris à contre-sens.
    if (phi < 0) { phi = -phi; theta += Math.PI; }
    if (phi > Math.PI) { phi = 2 * Math.PI - phi; theta += Math.PI; }
    rayon = Math.max(min, Math.min(max, rayon));
    cam.position.set(
      cible.x + rayon * Math.sin(phi) * Math.cos(theta),
      cible.y + rayon * Math.sin(phi) * Math.sin(theta),
      cible.z + rayon * Math.cos(phi));
    // Le haut de l'écran se CALCULE, il ne se décrète pas. Laisser `up` au zénith
    // marche partout sauf là où l'on regarde justement le zénith : au nadir, il
    // devient parallèle à l'axe de visée, `lookAt` n'a plus de base pour se tenir
    // et le monde part de travers — une vue du dessus renvoyait le château à huit
    // hauteurs d'écran sous le cadre. Cette expression est le vrai « haut » de
    // l'orbite : perpendiculaire à la visée par construction, à toute latitude,
    // et elle redonne (0,0,1) à l'horizontale, comme avant.
    cam.up.set(-Math.cos(phi) * Math.cos(theta),
               -Math.cos(phi) * Math.sin(theta),
               Math.sin(phi));
    cam.lookAt(cible);
    if (auChangement) auChangement({ rayon, phi, theta, cible, altitude: cam.position.z });
  }

  // Se placer comme une caméra de Blender : d'où l'on regarde, et quoi.
  function vers(loc, but) {
    // Une vue nommée est un point de vue en l'air : elle reprend forcément de la
    // hauteur, sinon on la demanderait et rien ne bougerait.
    if (apied) survoler();
    cible.set(but[0], but[1], but[2]);
    const dx = loc[0] - but[0], dy = loc[1] - but[1], dz = loc[2] - but[2];
    rayon = Math.hypot(dx, dy, dz);
    // Une vue posée À LA VERTICALE n'a pas d'azimut : `atan2(0,0)` rend zéro, et
    // zéro met le couchant en haut de l'écran — un plan couché sur le flanc.
    // On tranche pour le nord en haut, qui est la seule orientation qu'un plan
    // se permette.
    theta = (dx || dy) ? Math.atan2(dy, dx) : -Math.PI / 2;
    phi = Math.acos(Math.max(-1, Math.min(1, dz / (rayon || 1))));
    poser();
  }

  // Déplacer le point qu'on regarde, en pixels d'écran. C'est le calcul
  // d'OrbitControls, à l'identique : un pixel de glissé vaut la même longueur de
  // monde que le pixel qu'il recouvre, au plan de la cible — d'où le facteur
  // 2·distance·tan(fov/2)/hauteur, et non un coefficient choisi à la main.
  function deplacer(dx, dy) {
    if (apied) return;          // on ne fait pas glisser le sol sous ses pieds
    const k = 2 * rayon * Math.tan(cam.fov * Math.PI / 360) / canevas.clientHeight;
    const d = new T.Vector3(); cam.getWorldDirection(d);
    const droite = new T.Vector3().crossVectors(d, cam.up).normalize();
    const haut = new T.Vector3().crossVectors(droite, d).normalize();
    cible.addScaledVector(droite, -dx * k).addScaledVector(haut, dy * k);
  }


  let glisse = null;
  canevas.addEventListener("contextmenu", (e) => e.preventDefault());
  canevas.addEventListener("pointerdown", (e) => {
    canevas.setPointerCapture(e.pointerId);
    // La convention d'OrbitControls, celle de tout le monde : gauche tourne,
    // droit (et molette enfoncée, et maj+glisser, pour les montages où le clic
    // droit est mangé et les souris sans bouton du milieu) déplace. À pied,
    // rien de tout ça : on tourne la tête.
    glisse = { x: e.clientX, y: e.clientY,
               pan: !apied && (e.button === 2 || e.button === 1 || e.shiftKey) };
    canevas.style.cursor = apied ? "" : (glisse.pan ? "grabbing" : "move");
    // À pied, le clic prend la souris. Si le navigateur la refuse (iframe sans
    // permission, geste jugé insuffisant), le glissé reste là et fait le même
    // travail : on ne laisse personne sans moyen de tourner la tête.
    if (apied && !capturee() && canevas.requestPointerLock) {
      try { canevas.requestPointerLock(); } catch (x) { /* le glissé suffira */ }
    }
  });
  const lacher = () => { glisse = null; canevas.style.cursor = ""; };
  canevas.addEventListener("pointerup", lacher);
  canevas.addEventListener("pointercancel", lacher);
  canevas.addEventListener("pointermove", (e) => {
    if (!glisse || capturee()) return;   // capturée : c'est `mousemove` qui vise
    const dx = e.clientX - glisse.x, dy = e.clientY - glisse.y;
    glisse.x = e.clientX; glisse.y = e.clientY;
    if (glisse.pan) {
      deplacer(dx, dy);
    } else {
      // Un tour complet pour la largeur du panneau, comme OrbitControls, au lieu
      // d'un pas fixe qui rend le geste énorme dans un grand cadre et minuscule
      // dans un petit.
      theta -= 2 * Math.PI * dx / canevas.clientWidth;
      phi -= 2 * Math.PI * dy / canevas.clientHeight;
    }
    poser();
  });
  canevas.addEventListener("wheel", (e) => {
    e.preventDefault();
    // Un pavé tactile n'a pas de bouton du milieu et son glissé à deux doigts
    // arrive ici, pas dans `pointermove` : sans ce branchement, la moitié des
    // gens n'ont aucun moyen de se déplacer sur la carte. Un `deltaX` non nul
    // ne peut venir que d'un geste latéral — une molette n'en produit jamais —,
    // et maj+molette est le raccourci que tout le monde connaît.
    if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
      deplacer(-e.deltaX, -e.deltaY);
      return poser();
    }
    // À pied, la molette ne recule pas : on n'a pas de recul, on a des jambes.
    // Elle ouvre et referme le champ de vision, comme on plisse les yeux.
    if (apied) {
      cam.fov = Math.max(45, Math.min(105, cam.fov + Math.sign(e.deltaY) * 3));
      cam.updateProjectionMatrix();
      return;
    }
    // Le pas reste proportionnel à la distance — c'est lui qui permet de couvrir
    // mille mètres et trois pas avec le même geste. Sa FINESSE, elle, a fait
    // deux fois le voyage : 13 % dépassait la hauteur cherchée avant qu'on l'ait
    // vue, 6 % demandait trente-cinq crans pour descendre de la place forte à
    // une cour — et trente-cinq crans, on ne les fait pas, on croit que la
    // molette est cassée. 11 % : six crans pour diviser la distance par deux.
    rayon *= Math.exp(Math.sign(e.deltaY) * 0.11);
    poser();
  }, { passive: false });

  // ---- le regard, souris capturée ------------------------------------------
  // À pied, on tourne la tête sans tenir de bouton : c'est le geste que tout le
  // monde a dans les doigts, et il évite qu'un glissé serve à la fois à marcher
  // du regard et à cliquer sur ce qu'on voit. Échap rend la souris (le
  // navigateur s'en charge), et l'on reste debout — sortir de la vue est un
  // geste séparé.
  const capturee = () => document.pointerLockElement === canevas;
  document.addEventListener("mousemove", (e) => {
    if (!apied || !capturee()) return;
    theta -= e.movementX * 0.0022;
    phi -= e.movementY * 0.0022;
    poser();
  });

  // ---- ZQSD : marcher sur la carte ------------------------------------------
  // On lit `e.code`, pas `e.key` : `code` désigne la TOUCHE PHYSIQUE, donc
  // `KeyW` est le Z d'un azerty et le W d'un qwerty, `KeyA` le Q et le A. Une
  // seule table sert les deux dispositions, et l'on n'a pas à demander au joueur
  // sur quel clavier il tape.
  const TOUCHES = {
    KeyW: [0, 1], ArrowUp: [0, 1], KeyS: [0, -1], ArrowDown: [0, -1],
    KeyA: [-1, 0], ArrowLeft: [-1, 0], KeyD: [1, 0], ArrowRight: [1, 0],
  };
  const tenues = new Set();
  let marche = null;
  let course = false;

  function pas() {
    if (!tenues.size) { marche = null; return; }
    marche = requestAnimationFrame(pas);
    const t = performance.now();
    // Bornée : revenir sur un onglet laissé de côté rendrait un « dt » de vingt
    // secondes, et l'on se réveillerait à trente lieues de là.
    const dt = Math.min(0.05, (t - dernier) / 1000 || 0.016);
    dernier = t;
    let avant = 0, cote = 0;
    tenues.forEach((c) => { cote += TOUCHES[c][0]; avant += TOUCHES[c][1]; });
    if (!avant && !cote) return;
    // À pied, la vitesse est en MÈTRES PAR SECONDE et ne dépend plus du recul :
    // c'est un homme qui marche, pas une carte qu'on glisse. En orbite, le pas
    // reste proportionnel à la distance — c'est ce qui permet de couvrir la baie
    // et une ruelle avec le même geste.
    // On avance À PLAT, dans l'azimut du regard : une caméra penchée qui
    // avancerait le long de son axe de visée s'enfoncerait dans la colline.
    const v = (apied ? (course ? COURSE : PAS) * dt : rayon * 0.012)
              / Math.hypot(avant, cote);
    // La caméra est à l'azimut `theta` DE la cible : le devant de l'écran est
    // donc −(cos, sin), et la droite lui est perpendiculaire. Vérifiable à la
    // main sur la vue du château (theta = −π/2, nord en haut) : Z pousse au
    // nord, D pousse à l'est.
    cible.x += (-Math.cos(theta) * avant - Math.sin(theta) * cote) * v;
    cible.y += (-Math.sin(theta) * avant + Math.cos(theta) * cote) * v;
    poser();
  }

  // Le clavier est écouté sur LA TOILE, jamais sur la fenêtre. Dans la page de
  // jeu, le champ de réponse garde le focus en permanence — c'est voulu, le
  // joueur doit pouvoir écrire à tout instant. Un écouteur global n'aurait donc
  // eu que deux issues : ne jamais partir (si l'on s'efface devant le champ), ou
  // manger les lettres de ses répliques. On donne plutôt le focus à la carte
  // quand on la touche, et le ZQSD n'appartient qu'à elle. Cliquer dans le champ
  // le rend, sans qu'on ait rien à gérer.
  canevas.tabIndex = -1;
  canevas.style.outline = "none";
  canevas.addEventListener("pointerdown", () => canevas.focus({ preventScroll: true }));
  canevas.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    // F bascule entre le survol et la vue à hauteur d'homme ; maj fait courir.
    if (e.code === "KeyF") { e.preventDefault(); return apied ? survoler() : marcher(); }
    if (e.code === "ShiftLeft" || e.code === "ShiftRight") course = true;
    if (!TOUCHES[e.code]) return;
    e.preventDefault();
    dernier = performance.now();
    tenues.add(e.code);
    if (!marche) marche = requestAnimationFrame(pas);
  });
  canevas.addEventListener("keyup", (e) => {
    if (e.code === "ShiftLeft" || e.code === "ShiftRight") course = false;
    tenues.delete(e.code);
  });
  // Perdre le focus ou la fenêtre en tenant une touche ne rend jamais le
  // `keyup` : sans ça, on revient sur une carte qui glisse seule et ne s'arrête
  // plus.
  canevas.addEventListener("blur", () => tenues.clear());
  addEventListener("blur", () => tenues.clear());

  // ---- entrer dans le monde, et en ressortir --------------------------------
  // On garde le recul qu'on avait en survolant : ressortir doit rendre la vue
  // qu'on avait laissée, sinon la bascule coûte un recadrage à chaque fois.
  let recul = null;

  /**
   * Descendre sur ses pieds, là où l'on regardait.
   * `xy` peut porter une TROISIÈME valeur : la hauteur d'où l'on cherche le
   * plancher. C'est ce qui fait entrer dans la salle du troisième étage plutôt
   * que dans la cave qui est dessous — l'adresse de la fiction donne un z, et
   * il vaut mieux que le terrain.
   */
  function marcher(xy) {
    if (!apied) recul = { rayon, phi };
    apied = true;
    // Sans hauteur donnée, on cherche depuis le ciel : le premier plancher
    // rencontré en descendant est le toit ou le sol, jamais une cave.
    if (xy) cible.set(xy[0], xy[1], xy.length > 2 ? xy[2] : 4000);
    // On entre en regardant DEVANT SOI : garder le phi du survol (souvent près
    // du zénith) ferait ouvrir les yeux sur ses propres bottes.
    phi = Math.PI / 2 - 0.05;
    // Le plan proche : 4 m est juste pour survoler une ville, et c'est
    // exactement ce qui donnait l'impression d'être coincé SOUS le sol — à
    // hauteur d'yeux, tout ce qui est à moins de quatre pas est découpé, donc le
    // sol devant soi, et l'on regarde par le trou. À dix centimètres, on a ses
    // pieds et le mur qu'on frôle. Le tampon de profondeur est logarithmique
    // (monde.js), il encaisse le rapport sans strier le lointain.
    cam.near = 0.1;
    // Et le champ s'ouvre à 75°. Les 38° du survol sont un choix contre le
    // grand angle, qui rapetisse ce qu'il embrasse et fait perdre l'échelle
    // d'une ville — mais vus d'en haut. À hauteur d'homme, 38° est une longue-
    // vue : on ne voit pas ses pieds, pas les côtés d'une salle, et l'on tourne
    // sur soi-même pour comprendre où l'on est. 75° est le champ qu'un œil
    // reconnaît comme le sien.
    cam.fov = 75;
    cam.updateProjectionMatrix();
    dernier = performance.now();
    poser();
    canevas.focus({ preventScroll: true });
    if (auMode) auMode(true);
  }

  /** Reprendre de la hauteur, au-dessus de l'endroit où l'on se tenait. */
  function survoler() {
    if (!apied) return;
    apied = false;
    if (document.exitPointerLock && capturee()) document.exitPointerLock();
    cam.fov = 38; cam.near = 4; cam.updateProjectionMatrix();
    rayon = (recul && recul.rayon) || 600;
    phi = (recul && recul.phi) || 0.95;
    poser();
    if (auMode) auMode(false);
  }

  poser();
  return {
    vers, poser, cible, marcher, survoler,
    get apied() { return apied; },
    /** Le sol sous les pieds — injecté par monde.js, qui seul tient le relief. */
    surSol(f) { sol = f || (() => 0); if (apied) poser(); },
    surMode(f) { auMode = f || null; },
    get rayon() { return rayon; },
    get altitude() { return cam.position.z; },
    surChangement(f) { auChangement = f; },
  };
}

// Les mêmes vues que les rendus de monde/rendus/ : on compare ce qui se compare.
export const VUES = [
  ["La baie", [9200, -2600, 2600], [2900, 1700, 40]],
  ["Le plan", [2640, 1800, 3400], [2640, 1800, 0]],
  ["La ville", [4300, 3450, 1150], [2750, 1900, 40]],
  ["Le Donjon", [4180, 480, 330], [3432, 1224, 80]],
  ["Le Culpucier", [2980, 2020, 165], [2760, 2280, 20]],
  ["Une rue", [2810, 2210, 34], [2760, 2280, 22]],
];
