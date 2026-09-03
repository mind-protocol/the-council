/**
 * 🖥️ Présentation — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Fenêtre et télécommande : lit tout, n'altère rien sauf le spawn (écrivain
 * 2/2) et les commandes de transport. La sim tourne headless sans elle.
 */

import { creerCamera } from './camera.js';
import { creerRenderer } from './renderer.js';
import { dessinerTerrain } from './calques/terrain.js';
import { dessinerNavgrid } from './calques/navgrid.js';
import { dessinerIndex } from './calques/index.js';
import { dessinerForces } from './calques/forces.js';
import { dessinerHommes } from './calques/hommes.js';
import { dessinerChemins } from './calques/chemins.js';
import { dessinerCoups } from './calques/coups.js';
import { dessinerOiseaux } from './calques/oiseaux.js';
import { dessinerPerception } from './calques/perception.js';
import { dessinerFormation } from './calques/formation.js';
import { dessinerCouverture } from './calques/couverture.js';
import { dessinerEtatMajor } from './calques/etat-major.js';
import { dessinerLignes } from './calques/lignes.js';
import { dessinerOrientation } from './calques/orientation.js';
import { dessinerBulles } from './calques/bulles.js';
import { dessinerSelection } from './calques/selection.js';
import { dessinerOrdresDonnes } from './calques/ordres-donnes.js';
import { creerBulles } from './bulles.js';
import { monterLayout } from './ui/layout.js';
import { creerMenuGauche } from './ui/menu-gauche.js';
import { creerTransport } from './ui/transport.js';
import { creerOrdres } from './ui/ordres.js';
import { creerScenarios } from './ui/scenarios.js';
import { creerInspecteur } from './ui/inspecteur.js';
import { brancherNavigation } from './interactions/navigation.js';
import { brancherSelection } from './interactions/selection.js';
import { brancherDepot } from './interactions/depot.js';
import { brancherRedimension } from './interactions/redimension.js';
import { brancherPilotage } from './interactions/pilotage.js';

/**
 * @param {Object} deps — injectées au bootstrap
 * @param {{corps, corpsParId, terrain, navgridDebug, indexDebug}} deps.vuesMonde — vues 🌍
 * @param {{equipementDe}} deps.vuesCorps — vue ❤️ (la lance rendue)
 * @param {Function} deps.cheminsDebug — vue 🏃 (calque debug)
 * @param {Function} deps.introspecter — vue 🧠 (inspecteur)
 * @param {Function} deps.perceptionDebug — vue 🧠 (calque perception/mémoire)
 * @param {Function} deps.formationDebug — vue 🧠 (calque formation)
 * @param {Function} deps.orientationDebug — vue 🧠 (calque orientation)
 * @param {Function} deps.etatMajorDebug — vue 🧠 (calque état-major)
 * @param {{basculerPause, reglerVitesse, etat}} deps.transport — commandes ⏱️
 * @param {{basculerFormation, formationActive}} deps.ordres — commandes (échafaudage)
 * @param {{liste, actif, choisir}} deps.scenarios — le catalogue + la commande de rechargement (composée au bootstrap)
 * @param {(pos) => number | null} deps.spawn — écrivain 2/2 (composé au bootstrap)
 * @param {Object | null} [deps.plan] — le plan cuit d'une ville (viz du calque
 *   terrain, chargé au bootstrap) — du DESSIN ; la vérité reste le masque (🌍)
 * @param {{id: number, allerA: (pos) => void} | null} [deps.pj] — l'homme
 *   que le joueur dirige : le clic droit lui dit ou aller, et la camera le
 *   suit. Sans lui, la carte se navigue et personne n'obeit.
 * @param {boolean} [deps.habillage] — `false` : LA CARTE SEULE, zéro menu.
 *   Aucun panneau, aucune barre, aucun inspecteur ; les calques restent ceux
 *   qui naissent allumés, et la caméra se navigue toujours (naviguer n'est pas
 *   un menu). C'est la route `/` ; la vue de travail complète est `/bataille`.
 */
export function creerPresentation({ vuesMonde, vuesCorps, cheminsDebug, refusDebug, coupsDebug, introspecter, perceptionDebug, formationDebug, orientationDebug, couvertureDebug, etatMajorDebug, forcesDebug, transport, ordres, scenarios, spawn, plan = null, pj = null, habillage = true }) {
  let camera = null;
  let renderer = null;
  let transportUi = null;
  let ordresUi = null;
  let inspecteur = null;
  let idSelectionne = null;
  // Le joueur a saisi le decor : on lui laisse le regard tant qu'il le tient.
  let suivi = true; // la camera suit le PJ, jusqu'a ce que le joueur tire le decor
  /** @type {Array<{pos: {x, y}, t0: number}>} — les ondes du clic droit, en
   *  temps reel ; purgees des qu'eteintes (jamais plus de quelques entrees) */
  const ordresDonnes = [];
  let toile = null;                 // le canvas, garde a la pose
  const bulles = creerBulles({ tempsSim: () => transport.etat().tempsSim });

  // Calques activables : les calques de debug denses (navgrid, index)
  // naissent éteints — le canvas reste lisible par défaut.
  const CALQUES = [
    { id: 'terrain', libelle: 'Terrain', dessiner: dessinerTerrain, defaut: true },
    { id: 'navgrid', libelle: 'Navgrid (A*)', dessiner: dessinerNavgrid, defaut: false },
    { id: 'index', libelle: 'Index spatial', dessiner: dessinerIndex, defaut: false },
    { id: 'forces', libelle: 'Forces (physique)', dessiner: dessinerForces, defaut: false },
    { id: 'hommes', libelle: 'Hommes', dessiner: dessinerHommes, defaut: true },
    { id: 'chemins', libelle: 'Chemins (A*)', dessiner: dessinerChemins, defaut: false },
    { id: 'coups', libelle: 'Coups (frappes)', dessiner: dessinerCoups, defaut: true },
    { id: 'oiseaux', libelle: 'Oiseaux (vol)', dessiner: dessinerOiseaux, defaut: true },
    { id: 'perception', libelle: 'Perception', dessiner: dessinerPerception, defaut: true, debug: true },
    { id: 'couverture', libelle: 'Couverture (où j\'ai regardé)', dessiner: dessinerCouverture, defaut: true, debug: true },
    { id: 'etat-major', libelle: 'État-major (commandant)', dessiner: dessinerEtatMajor, defaut: true, debug: true },
    { id: 'lignes', libelle: 'Lignes (fronts)', dessiner: dessinerLignes, defaut: false },
    { id: 'formation', libelle: 'Formation', dessiner: dessinerFormation, defaut: true, debug: true },
    { id: 'orientation', libelle: 'Orientation (arbitrage)', dessiner: dessinerOrientation, defaut: true, debug: true },
    { id: 'bulles', libelle: 'Bulles (paroles)', dessiner: dessinerBulles, defaut: true },
    { id: 'ordres-donnes', libelle: 'Ordres donnés (clic droit)', dessiner: dessinerOrdresDonnes, defaut: true },
    { id: 'selection', libelle: 'Sélection', dessiner: dessinerSelection, defaut: true },
  ];
  // La carte seule (`/`) ne montre que le monde : ce qui lit une tête
  // (perception, arbitrage, état-major, formation) reste à la vue de travail.
  const calquesActifs = new Set(CALQUES.filter((c) => c.defaut && (habillage || !c.debug)).map((c) => c.id));

  const corpsSous = (posMonde) => {
    let trouve = null;
    for (const c of vuesMonde.corps()) {
      const d = Math.hypot(c.pos.x - posMonde.x, c.pos.y - posMonde.y);
      if (d <= c.rayon + 0.15) trouve = c.id; // le dernier dessiné gagne
    }
    return trouve;
  };

  /** Centre la caméra sur la bbox de la scène (obstacles + corps). */
  const cadrerScene = (canvas) => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    const etendre = (x, y) => {
      minX = Math.min(minX, x); minY = Math.min(minY, y);
      maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
    };
    for (const o of vuesMonde.terrain.obstacles()) {
      etendre(o.x, o.y);
      etendre(o.x + o.largeur, o.y + o.hauteur);
    }
    for (const c of vuesMonde.corps()) etendre(c.pos.x, c.pos.y);
    if (minX === Infinity) return;
    // OU L'ON REGARDE, une fois serre. Le centre de la boite englobante est le
    // bon repere pour tenir-tout, et le PIRE des qu'on zoome : deux camps aux
    // deux bouts, et le milieu est la rue vide entre eux (mesure : cadre a x3
    // sur ce scenario, l'ecran ne montrait pas un homme). On vise donc le plus
    // gros AMAS — l'homme qui a le plus de monde autour de lui.
    // Trois reperes possibles, du plus juste au plus faible : MOI si le joueur
    // dirige quelqu'un, sinon le plus gros amas, sinon la boite englobante.
    let centreM = { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
    const moi = pj && vuesMonde.corpsParId(pj.id);
    const tous = moi ? [] : [...vuesMonde.corps()];
    if (moi) {
      centreM = { x: moi.pos.x, y: moi.pos.y };
    } else if (tous.length) {
      const R = 15, R2 = R * R;
      // au-dela de mille corps, on echantillonne : ce cadrage se fait une fois,
      // il ne merite pas un million de distances.
      const pas = Math.max(1, Math.ceil(tous.length / 1000));
      let meilleur = null, meilleurN = -1;
      for (let i = 0; i < tous.length; i += pas) {
        const a = tous[i];
        let n = 0, sx = 0, sy = 0;
        for (let j = 0; j < tous.length; j += pas) {
          const b = tous[j];
          const dx = b.pos.x - a.pos.x, dy = b.pos.y - a.pos.y;
          if (dx * dx + dy * dy <= R2) { n++; sx += b.pos.x; sy += b.pos.y; }
        }
        if (n > meilleurN) { meilleurN = n; meilleur = { x: sx / n, y: sy / n }; }
      }
      if (meilleur) centreM = meilleur;
    }
    // CADRER, c'est zoomer PUIS centrer. On ne faisait que centrer : la scene
    // tombait au bon endroit a une echelle qui ne lui allait pas, et l'ecran
    // etait noir aux trois quarts. Invisible tant que la carte etait entouree
    // de panneaux ; intenable des qu'elle EST l'ecran.
    const l = canvas.clientWidth, h = canvas.clientHeight;
    const largeurM = Math.max(maxX - minX, 1e-6), hauteurM = Math.max(maxY - minY, 1e-6);
    if (l > 0 && h > 0) {
      const MARGE = 0.9;   // une scene qui touche les bords se lit mal
      const SERRE = 3;     // on ouvre SERRE sur l'action : le cadrage large
      // montre la carte, pas la bataille — a l'echelle du tenir-tout, un homme
      // fait deux pixels. On voit les hommes, on va chercher le reste a la
      // molette.
      const voulu = Math.min((l * MARGE) / largeurM, (h * MARGE) / hauteurM) * SERRE;
      camera.zoomer(voulu / camera.echelle(), { x: l / 2, y: h / 2 });
    }
    cadrer(canvas, centreM);
  };

  /** Amene ce point du monde au centre de l'ecran. */
  const cadrer = (canvas, pointM) => {
    const centre = camera.versEcran(pointM);
    camera.deplacer({ x: canvas.clientWidth / 2 - centre.x, y: canvas.clientHeight / 2 - centre.y });
  };

  return {
    /** Monte le DOM plein écran, branche interactions et transport. */
    monter(racine) {
      const { canvas, panneauGauche, panneauDroit, barreTransport } =
        monterLayout(racine, { habillage });

      camera = creerCamera({ pixelsParMetre: 28 }); // un cran de zoom en plus par defaut (24 -> 28, ~un cran de molette)
      renderer = creerRenderer({
        canvas,
        camera,
        calques: CALQUES.map(({ id, dessiner }) => ({
          id,
          dessiner,
          actif: () => calquesActifs.has(id),
        })),
      });
      renderer.redimensionner();
      window.addEventListener('resize', () => renderer.redimensionner());
      cadrerScene(canvas);

      // La carte seule s'arrête ici : on navigue, on ne commande pas. Tout ce
      // qui suit est de l'habillage — sections, transport, inspecteur, et la
      // sélection qui n'a plus de panneau où s'ouvrir.
      toile = canvas;
      if (pj) {
        brancherPilotage({
          canvas,
          camera,
          allerA: (pos) => {
            ordresDonnes.push({ pos: { x: pos.x, y: pos.y }, t0: performance.now() });
            if (ordresDonnes.length > 8) ordresDonnes.shift();
            pj.allerA(pos);
          },
        });
        // Le joueur QUITTE le suivi en saisissant le decor et en le tirant (un
        // clic ne compte pas : c'est une selection) — et il se balade ensuite
        // aussi longtemps qu'il veut. Il REVIENT sur son homme d'un double-clic.
        // On ne lui arrache jamais le regard des mains, et on ne le lui rend
        // pas non plus sans qu'il le demande.
        let departPan = null;
        canvas.addEventListener('pointerdown', (ev) => { if (ev.button === 0) departPan = { x: ev.clientX, y: ev.clientY }; });
        canvas.addEventListener('pointermove', (ev) => {
          if (departPan && Math.hypot(ev.clientX - departPan.x, ev.clientY - departPan.y) > 4) { suivi = false; departPan = null; }
        });
        canvas.addEventListener('pointerup', () => { departPan = null; });
        canvas.addEventListener('pointercancel', () => { departPan = null; });
        canvas.addEventListener('dblclick', () => { suivi = true; });
      }

      if (!habillage) {
        brancherNavigation({ canvas, camera });
        return;
      }

      const menu = creerMenuGauche(panneauGauche);
      if (scenarios) {
        menu.ajouterSection('Scénario', creerScenarios(scenarios).element);
      }
      if (ordres) {
        ordresUi = creerOrdres(ordres);
        menu.ajouterSection('Ordres', ordresUi.element);
      }
      menu.ajouterSection(
        'Bibliothèque',
        menu.creerBibliotheque((ev) => {
          ev.dataTransfer.setData('text/plain', 'homme');
          ev.dataTransfer.effectAllowed = 'copy';
        })
      );
      menu.ajouterSection(
        'Calques',
        menu.creerCasesACocher(
          CALQUES.map(({ id, libelle, defaut }) => ({ id, libelle, actif: defaut })),
          (id, actif) => {
            if (actif) calquesActifs.add(id);
            else calquesActifs.delete(id);
          }
        )
      );

      transportUi = creerTransport(barreTransport, transport);
      inspecteur = creerInspecteur(panneauDroit, {
        surFermeture: () => { idSelectionne = null; },
      });

      const selectionner = (id) => {
        idSelectionne = id;
        if (id == null) inspecteur.fermer();
        else inspecteur.ouvrir(id);
      };

      brancherNavigation({ canvas, camera });
      brancherSelection({ canvas, camera, corpsSous, selectionner });
      brancherDepot({ canvas, camera, spawner: (pos) => spawn(pos) });
      brancherRedimension({ panneau: panneauDroit });
    },

    /** Une frame : calques + inspecteur ouvert + transport. */
    rendre() {
      if (!renderer) return;
      // LE SUIVI — la camera est ATTACHEE a lui.
      //
      // Deux versions ratees avant celle-ci, et elles ratent pour la meme
      // raison : elles laissaient l'homme se promener dans l'image. La zone
      // franche le rattrapait d'un saut quand il en sortait ; l'amorti le
      // laissait deriver puis courait derriere. Dans les deux cas le decor
      // bougeait pour des raisons que le joueur ne commande pas.
      //
      // Un vrai suivi n'a pas de retard : l'homme est au centre, toujours, et
      // c'est LE MONDE qui defile autour de lui. On recadre donc a chaque
      // image, avant de peindre — la position vient d'etre integree, elle est
      // fraiche, et rien ne s'interpose entre elle et le rendu.
      //
      // Le joueur reprend la main quand il tire le decor, et la garde : la
      // camera ne revient sur son homme que s'il le demande (double-clic).
      if (pj && suivi && toile) {
        const moi = vuesMonde.corpsParId(pj.id);
        if (moi) cadrer(toile, moi.pos);
      }
      renderer.rendre({
        corps: vuesMonde.corps,
        corpsParId: vuesMonde.corpsParId,
        terrain: vuesMonde.terrain,
        plan,
        navgridDebug: vuesMonde.navgridDebug,
        montureDe: vuesMonde.montureDe,
        habillage, // la carte seule n'a pas de calques de verite (grille du masque)
        indexDebug: vuesMonde.indexDebug,
        forces: forcesDebug,
        equipement: vuesCorps?.equipementDe,
        blessuresDe: vuesCorps?.blessuresDe,
        souffleDe: vuesCorps?.souffleDe,
        oiseauDe: vuesCorps?.oiseauDe,
        chemins: cheminsDebug,
        refus: refusDebug,
        coups: coupsDebug,
        perception: perceptionDebug,
        formationDebug,
        orientationDebug,
        couverture: couvertureDebug,
        etatMajor: etatMajorDebug,
        bulles: bulles.actives,
        ordresDonnes: () => ordresDonnes,
        idSelectionne,
      });
      // Sans habillage, ces trois-la n'existent pas : la carte seule n'a ni
      // barre, ni ordres, ni inspecteur. Les appeler tuait la boucle de frame
      // des la premiere image — et une sim figee ressemble a une sim rendue.
      transportUi?.rafraichir();
      ordresUi?.rafraichir();
      const id = inspecteur?.idOuvert();
      if (id != null) inspecteur.rafraichir(introspecter(id));
    },

    /**
     * Fait parler un corps sur la map (réutilisable : ordres criés
     * aujourd'hui, transmissions 📯 demain).
     * @param {number} idCorps @param {string} texte @param {number} [dureeS]
     */
    dire(idCorps, texte, dureeS) {
      bulles.dire(idCorps, texte, dureeS);
    },
  };
}
