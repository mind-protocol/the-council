/*
 * BANC DRAGON — une cinématique 3D calculée, rendue en plan.
 *
 * Aucun état de partie n'est lu ni écrit ici. Les hypothèses physiques sont
 * documentées dans `docs/bataille/dragons-realistes.md`; ce fichier ne fait
 * que les exécuter et les rendre visibles.
 */
(() => {
  "use strict";

  const TAU = Math.PI * 2, G = 9.81, AMBIANTE = 293;
  const MODELES = Object.freeze({
    syrax: Object.freeze({
      id:"syrax", nom:"Syrax", cavalier:"Rhaenyra", epreuve:"D2",
      masse:8000, longueur:28, envergure:36, surface:360,
      poids:8000 * G, croisiere:18, presse:27, limite:55, pique:46,
      battement:.24, battementLent:.42, accelLateral:6.5,
      volLent:4.5, volLentMin:3.2, freinLent:7.2, lacetLent:.48,
      banqueLente:10, banqueRalliement:60, banquePiqueHaut:40,
      banquePiqueBas:45, banqueSouffle:22, attenteLente:9,
      flamme:65, noyau:2000, souffle:2.55, penteFeu:42,
      rayonFeu:.8, ouvertureFeu:.10, flux:2800,
      seuilOccasion:2.2,
      approcheDist:360, approcheVitesse:25, altitudeRalliement:205,
      altitudeTir:34, altitudePique:25, vitesseSouffle:39,
      altitudeSortie:210, vitesseSortie:27, sortieDeclenche:165,
      couloirArriere:18, couloirAvant:160, couloirLargeur0:6, couloirLargeur1:9,
      opportunite:165, opportuniteLargeur:6.3,
      couleur:"#a87832", trait:"#e1b867", ventre:"#d59c45",
    }),
    vhagar: Object.freeze({
      id:"vhagar", nom:"Vhagar", cavalier:"Aemond", epreuve:"D2b",
      masse:42000, longueur:67, envergure:82, surface:1800,
      poids:42000 * G, croisiere:15, presse:22, limite:44, pique:42,
      battement:.12, battementLent:.21, accelLateral:3.2,
      volLent:7.5, volLentMin:6, freinLent:4.6, lacetLent:.20,
      banqueLente:7, banqueRalliement:42, banquePiqueHaut:28,
      banquePiqueBas:32, banqueSouffle:14, attenteLente:6,
      flamme:115, noyau:2200, souffle:3.4, penteFeu:38,
      rayonFeu:1.5, ouvertureFeu:.145, flux:3900,
      seuilOccasion:2.2,
      approcheDist:500, approcheVitesse:21, altitudeRalliement:270,
      altitudeTir:58, altitudePique:42, vitesseSouffle:32,
      altitudeSortie:270, vitesseSortie:22, sortieDeclenche:215,
      couloirArriere:28, couloirAvant:245, couloirLargeur0:10, couloirLargeur1:17,
      opportunite:245, opportuniteLargeur:11,
      couleur:"#665f49", trait:"#9da078", ventre:"#7b7659",
    }),
    arrax: Object.freeze({
      id:"arrax", nom:"Arrax", cavalier:"Lucerys", epreuve:"D2c",
      masse:2200, longueur:15, envergure:22, surface:125,
      poids:2200 * G, croisiere:21, presse:31, limite:60, pique:57,
      battement:.48, battementLent:.68, accelLateral:9.2,
      volLent:3.8, volLentMin:2.5, freinLent:8.5, lacetLent:.75,
      banqueLente:14, banqueRalliement:70, banquePiqueHaut:52,
      banquePiqueBas:60, banqueSouffle:30, attenteLente:12,
      flamme:38, noyau:1850, souffle:1.7, penteFeu:45,
      rayonFeu:.45, ouvertureFeu:.07, flux:2100,
      seuilOccasion:.75,
      approcheDist:275, approcheVitesse:30, altitudeRalliement:175,
      altitudeTir:28, altitudePique:18, vitesseSouffle:44,
      altitudeSortie:175, vitesseSortie:32, sortieDeclenche:125,
      couloirArriere:12, couloirAvant:112, couloirLargeur0:4, couloirLargeur1:6,
      opportunite:118, opportuniteLargeur:5.8,
      couleur:"#d8d3c2", trait:"#f3eee1", ventre:"#b9c6c7",
    }),
  });
  let modele = MODELES.syrax;
  const estArmee = (mode) => String(mode).startsWith("armee");
  const estVille = (mode) => mode === "ville-vhagar";
  const estRangee = (mode) => String(mode).startsWith("rangee-");
  const estRangeeOuverte = (mode) => mode === "rangee-arrax-garde-ouvert";
  const modeleDuMode = (mode) => mode === "armee-vhagar" || mode === "ville-vhagar" ? MODELES.vhagar
    : mode === "armee-arrax" || mode === "rangee-arrax-garde" ||
      mode === "rangee-arrax-garde-ouvert" ? MODELES.arrax : MODELES.syrax;
  const BORNE = { x0: -500, y0: -300, x1: 500, y1: 300 };
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const lisse = (a, b, x) => {
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
  const angle = (a) => Math.atan2(Math.sin(a), Math.cos(a));
  const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const fmt = (x, n = 0) => Number.isFinite(x)
    ? x.toFixed(n).replace(".", ",") : "—";

  let toile = null, ctx = null, stats = null, note = null, ro = null, bataille = null;
  let incendie = null;
  let largeur = 0, hauteur = 0, dpr = 1, echelle = 1, ox = 0, oy = 0;
  let etat = null, marche = false, vitesse = 1, boucle = 0, dernier = 0;
  let vueCarte = null;
  let graine = 0x51a7c;
  const hasard = () => {
    graine = (Math.imul(graine, 1664525) + 1013904223) >>> 0;
    return graine / 4294967296;
  };

  function nouvelEtat(mode) {
    graine = 0x51a7c;
    const cible = { x: 135, y: 18, vx: 0.8, vy: 0 };
    const armee = estArmee(mode), ville = estVille(mode), rangee = estRangee(mode);
    const suite = mode === "suite";
    const phase = armee || ville || rangee ? "dracarys" : suite ? "reconnaissance" : mode;
    const rayon = 166;
    const d = phase === "reconnaissance"
      ? { x: cible.x, y: cible.y - rayon, z: 235, v: 18,
          cap: 0, banque: 0, pente: 0, vz: 0 }
      : { x: -480, y: 105, z: modele.altitudeRalliement + 30,
          v: Math.min(modele.presse, modele.croisiere + 2),
          cap: -0.10, banque: 0, pente: 0, vz: 0 };
    return {
      t: 0, mode, phase, suite, cible, hommes: [], dragon: d,
      phaseAile: 0, force: modele.poids / 1000, progression: 0, tourFait: false,
      attaque: phase === "dracarys" ? "ralliement" : "—",
      altitudeEntree: d.z, vitesseEntree: d.v, souffle: 0,
      chemin: [], chaleur: new Map(), projections: [], empreinte: [], derniereCoupe: null,
      exposition: new Map(), perception: new Map(), repere: null,
      reactionsVues: { fuite: new Set(), sidération: new Set(), recul: new Set(),
                       dérobade: new Set(), serrer: new Set(), ruée: new Set() },
      detteBataille: 0, dernierCentre: null, dernierPoint: -1, victimes: 0,
      prochainRugissement: 9, bilanDanger: null, bilanRupture: null,
      rupturePart: 0, ruptureA: null, premierFeuA: null,
      passages: 0, attaqueDepuis: 0, distanceAvant: Infinity, sautMax: 0,
      basseAllure: false, basseAllureDepuis: null,
      cibleHomme: null, cibleVerrouJus: 0,
      piqueHomme: null,
      cibleMembres: [], cibleGuidage: [], cibleEtapes: [], cibleCap: d.cap,
      capPassage: null,
      candidatsCibles: [], zonesTraitees: [], selections: [],
      effectifsInitiaux: null,
      selectionProchaine: false, cibleValeur: 0, cibleGain: 0,
      cibleChaines: 0, passagesManques: 0, passagesOpportunistes: 0,
      message: phase === "reconnaissance"
        ? `${modele.nom} prend l'orbite de la colonne mobile.`
        : rangee
          ? `${modele.nom} accompagne le petit camp de C6 et lit la ligne ennemie deux fois plus nombreuse.`
        : ville
          ? `${modele.nom} entre au-dessus de Port-Réal et cherche une bande de toits encore combustible.`
        : armee
          ? `${modele.nom} entre haut et cherche immédiatement une ligne de feu dans l'armée.`
          : `${modele.nom} entre haut, puis convertit sa hauteur en vitesse.`,
    };
  }

  function transformerVue() {
    const v = vueCarte && vueCarte.length === 4 ? vueCarte
      : [BORNE.x0, BORNE.y0, BORNE.x1 - BORNE.x0, BORNE.y1 - BORNE.y0];
    // La trajectoire, le feu, les soldats et le SVG de ville partagent un seul
    // contrat monde→écran. Réimplémenter ici le vieux y-vers-le-bas faisait
    // glisser le calque dragon dès que la carte nord-en-haut était déplacée.
    const rep = window.CarteProjection && CarteProjection.repere(v, largeur, hauteur);
    if (rep) { echelle = rep.k; ox = rep.ox; oy = rep.oy; return; }
    echelle = Math.min(largeur / Math.max(1, v[2]),
                       hauteur / Math.max(1, v[3]));
    ox = (largeur - v[2] * echelle) / 2 - v[0] * echelle;
    oy = (hauteur - v[3] * echelle) / 2 + (v[1] + v[3]) * echelle;
  }

  function transformerLocalDansMonde() {
    const r = etat && etat.repere;
    if (!r) {
      ctx.setTransform(dpr * echelle, 0, 0, -dpr * echelle,
                       dpr * ox, dpr * oy);
      return;
    }
    const c = Math.cos(r.cap), s = Math.sin(r.cap);
    const tx = r.x - c * 135 + s * 18;
    const ty = r.y - s * 135 - c * 18;
    ctx.setTransform(dpr * echelle * c, -dpr * echelle * s,
                     -dpr * echelle * s, -dpr * echelle * c,
                     dpr * (ox + echelle * tx), dpr * (oy - echelle * ty));
  }

  function redimensionner() {
    if (!toile) return;
    const r = toile.getBoundingClientRect();
    largeur = Math.max(1, r.width); hauteur = Math.max(1, r.height);
    dpr = Math.min(2, window.devicePixelRatio || 1);
    toile.width = Math.round(largeur * dpr);
    toile.height = Math.round(hauteur * dpr);
    transformerVue();
    rendre();
  }

  function cadreScene() {
    if (etat && estVille(etat.mode) && incendie && incendie.cadre) return incendie.cadre();
    if (!etat) return [BORNE.x0, BORNE.y0, BORNE.x1 - BORNE.x0, BORNE.y1 - BORNE.y0];
    const locaux = [etat.dragon, etat.cible];
    for (const h of etat.hommes) locaux.push(localDepuisMonde(h));
    for (const p of etat.chemin) locaux.push(p);
    for (const z of etat.zonesTraitees) locaux.push(z);
    const points = etat.repere ? locaux.map(mondeDepuisLocal) : locaux;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const p of points) {
      if (!p || !Number.isFinite(p.x) || !Number.isFinite(p.y)) continue;
      x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y);
      x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y);
    }
    if (!Number.isFinite(x0)) return [BORNE.x0, BORNE.y0,
      BORNE.x1 - BORNE.x0, BORNE.y1 - BORNE.y0];
    const marge = Math.max(30, Math.max(x1 - x0, y1 - y0) * 0.09);
    return [x0 - marge, y0 - marge,
      Math.max(60, x1 - x0 + 2 * marge), Math.max(60, y1 - y0 + 2 * marge)];
  }

  function prendreVue(v) {
    vueCarte = v && v.length === 4 ? v.slice() : null;
    if (!largeur || !hauteur) redimensionner();
    else { transformerVue(); rendre(); }
  }

  const auSol = (h) => h && (h.etat === "mort" || h.etat === "blesse");

  function mondeDepuisLocal(p) {
    const r = etat.repere, dx = p.x - 135, dy = p.y - 18;
    const c = Math.cos(r.cap), s = Math.sin(r.cap);
    return { x: r.x + c * dx - s * dy, y: r.y + s * dx + c * dy };
  }

  function localDepuisMonde(p) {
    const r = etat.repere, dx = p.x - r.x, dy = p.y - r.y;
    const c = Math.cos(r.cap), s = Math.sin(r.cap);
    return { x: 135 + c * dx + s * dy, y: 18 - s * dx + c * dy };
  }

  function directionLocale(x, y) {
    const c = Math.cos(etat.repere.cap), s = Math.sin(etat.repere.cap);
    return { x: c * x + s * y, y: -s * x + c * y };
  }

  function trouverPlaine(B, bases, etendue = false) {
    const angles = Array.from({ length: 24 }, (_, i) => i * TAU / 24);
    // Les positions de l'armée donnent les premiers candidats, mais elles sont
    // presque toutes au voisinage des portes. D2 demande une vraie plaine : on
    // complète donc par une grille déterministe de l'emprise, sans jamais
    // fabriquer de terrain au-delà de la carte.
    const candidats = [], vus = new Set();
    const ajouter = (x, y) => {
      const cle = Math.round(x / 60) + ":" + Math.round(y / 60);
      if (!vus.has(cle)) { vus.add(cle); candidats.push({ x, y }); }
    };
    for (const b of bases) ajouter(b.x, b.y);
    const bornes = typeof B.bornes === "function" ? B.bornes() : null;
    if (etendue && bornes) {
      const mx = 225, my = 150;
      for (let y = bornes[1] + my; y <= bornes[3] - my; y += 140)
        for (let x = bornes[0] + mx; x <= bornes[2] - mx; x += 160)
          ajouter(x, y);
    }

    for (const base of candidats) for (const cap of angles) {
      const c = Math.cos(cap), s = Math.sin(cap);
      let libre = true;
      // La colonne fait 48 m ; l'armée occupe six masses sur plus de trois
      // cents mètres. Dans les deux cas on valide le rectangle entier contre
      // le même masque que le moteur, même si la ville n'est pas rendue.
      const x0 = etendue ? -185 : -52, x1 = etendue ? 185 : 80;
      const y0 = etendue ? -105 : -6, y1 = etendue ? 105 : 6;
      const pas = etendue ? 6 : 8;
      for (let x = x0; x <= x1 && libre; x += pas)
        for (let y = y0; y <= y1 && libre; y += etendue ? 6 : 4)
          if (B.libre(base.x + c * x - s * y, base.y + s * x + c * y) !== true)
            libre = false;
      if (libre) return { x: base.x, y: base.y, cap };
    }
    // L'ancien repli rendait le premier point même après que le masque l'avait
    // refusé : c'est précisément ainsi que D2 se retrouvait sur l'eau. Une
    // épreuve sans terrain valide doit maintenant échouer à voix haute.
    throw new Error(etendue ? "D2 ne trouve aucune plaine entièrement sèche"
                            : "D1 ne trouve aucun couloir entièrement sec");
  }

  function preparerColonne() {
    if (!bataille) return;
    bataille.arreter();
    if (bataille.echelle() !== 0.1) bataille.echelle(0.1);
    bataille.rejouer();
    const troupe = bataille.troupe();
    const ordinaires = (h) => !h.tete && !h.roi && !h.hors && !h.capitaine;
    const bases = troupe.filter((h) => h.camp === "assaut" && ordinaires(h));
    const armee = estArmee(etat.mode);
    const disponibles = troupe.filter(ordinaires);
    const nombreArmee = Math.min(216, Math.floor(disponibles.length / 36) * 36);
    const hommes = armee ? disponibles.slice(0, nombreArmee)
      : troupe.filter((h) => h.camp === "garde" && ordinaires(h)).slice(0, 72);
    if ((!armee && hommes.length < 72) || (armee && hommes.length < 120))
      throw new Error(armee ? "D2 réclame au moins 120 soldats réels"
                            : "D1 réclame 72 soldats réels");
    etat.repere = trouverPlaine(bataille, bases, armee);

    for (let i = 0; i < hommes.length; i++) {
      const h = hommes[i];
      let local, capLocal = 0, avance = 135, groupe = 0;
      if (armee) {
        const centres = [[-125, -68], [0, -78], [125, -62],
                         [-105, 55], [20, 62], [140, 48]];
        const caps = [0.08, -0.05, 0.12, -0.08, 0.04, -0.12];
        const parGroupe = hommes.length / centres.length;
        groupe = Math.min(centres.length - 1, Math.floor(i / parGroupe));
        const j = i - groupe * parGroupe;
        const colonnes = 6, rang = Math.floor(j / colonnes), file = j % colonnes;
        const cx = etat.cible.x + centres[groupe][0];
        const cy = etat.cible.y + centres[groupe][1];
        capLocal = caps[groupe];
        const long = (rang - (parGroupe / colonnes - 1) / 2) * 2.65;
        const large = (file - (colonnes - 1) / 2) * 2.25;
        local = {
          x: cx + Math.cos(capLocal) * long - Math.sin(capLocal) * large +
             (hasard() - 0.5) * 0.32,
          y: cy + Math.sin(capLocal) * long + Math.cos(capLocal) * large +
             (hasard() - 0.5) * 0.28,
        };
        avance = 90 + groupe * 4;
      } else {
        const rang = Math.floor(i / 4), file = i % 4;
        local = {
          x: etat.cible.x - rang * 2.65 + (hasard() - 0.5) * 0.35,
          y: etat.cible.y + (file - 1.5) * 2.35 + (hasard() - 0.5) * 0.3,
        };
      }
      const p = mondeDepuisLocal(local), but = mondeDepuisLocal({
        x: local.x + Math.cos(capLocal) * avance,
        y: local.y + Math.sin(capLocal) * avance,
      });
      if (bataille.libre(p.x, p.y) !== true)
        throw new Error("la plaine retenue place encore un soldat hors sol sec");
      h.x = p.x; h.y = p.y; h.vx = 0; h.vy = 0; h.vit = 0;
      h.camp = "garde"; h.dragonGroupe = groupe;
      h.fx = Math.cos(etat.repere.cap + capLocal);
      h.fy = Math.sin(etat.repere.cap + capLocal);
      h.cx = h.fx; h.cy = h.fy; h.cible = null;
      h.etat = "tient"; h.poste = [but.x, but.y]; h.recu.length = 0;
      h.formation = -1; h.placeFormation = null; h.chefFormation = false;
      h.chef = false; h.capitaine = false; h.hors = false;
      etat.exposition.set(h, { dose: 0, pic: AMBIANTE, index: i });
    }
    const garder = new Set(hommes);
    for (let i = troupe.length - 1; i >= 0; i--)
      if (!garder.has(troupe[i])) troupe.splice(i, 1);
    etat.hommes = hommes;
    actualiserCible(0.05);
  }

  function preparerVille() {
    if (!incendie || !incendie.ciblesDragon || !incendie.cadre)
      throw new Error("D3 réclame le moteur d'incendie urbain");
    // Repère identité : les positions du dragon sont directement celles du
    // plan de Port-Réal, donc la caméra, le survol et le bâti restent uniques.
    etat.repere = { x:135, y:18, cap:0 };
    etat.hommes = incendie.ciblesDragon();
    const c = incendie.cadre(), d = etat.dragon;
    d.x = c[0] - 150; d.y = c[1] + c[3] * .52;
    d.z = modele.altitudeRalliement + 20; d.v = modele.approcheVitesse;
    d.cap = 0; d.banque = 0; d.vz = 0;
    if (!choisirCibleStrategique()) throw new Error("D3 ne trouve aucun toit combustible");
    actualiserCible(.05);
  }

  function preparerRangee() {
    if (!bataille) throw new Error("D4 réclame la bataille rangée C6 déjà posée");
    if (estRangeeOuverte(etat.mode) &&
        (!bataille.ordonnerDoctrineDeploiement ||
         !bataille.ordonnerDoctrineDeploiement("rangee:assaut", "anti-dragon-ouvert")))
      throw new Error("D4b n'a pas pu transmettre la doctrine au déploiement C6");
    etat.repere = { x:135, y:18, cap:0 };
    const tous = bataille.troupe().filter((h) => !h.hors &&
      (h.camp === "assaut" || h.camp === "garde"));
    const ordinaires = (h) => !h.tete && !h.roi && !h.capitaine;
    for (const h of tous) {
      h.dragonAllie = h.camp === "garde";
      h.dragonCible = h.camp === "assaut" && ordinaires(h);
      etat.exposition.set(h, { dose:0, pic:AMBIANTE, index:etat.exposition.size });
    }
    etat.hommes = tous;
    etat.effectifsInitiaux = {
      garde:tous.filter((h) => h.camp === "garde" && ordinaires(h)).length,
      assaut:tous.filter((h) => h.camp === "assaut" && ordinaires(h)).length,
    };
    const ennemis = tous.filter((h) => h.dragonCible);
    if (!ennemis.length) throw new Error("D4 ne trouve pas la grande armée de C6");
    const cx = ennemis.reduce((s, h) => s + h.x, 0) / ennemis.length;
    const cy = ennemis.reduce((s, h) => s + h.y, 0) / ennemis.length;
    const d = etat.dragon;
    d.x = cx - modele.approcheDist * 1.08; d.y = cy + 95;
    d.z = modele.altitudeRalliement + 25; d.v = modele.approcheVitesse;
    d.cap = Math.atan2(cy - d.y, cx - d.x); d.banque = 0; d.vz = 0;
    if (!choisirCibleStrategique()) throw new Error("D4 ne trouve aucune ligne ennemie");
    // C'est la pose initiale de l'épreuve, avant le premier point du path :
    // Le dragon entre déjà établi sur l'approche qu'il vient de choisir. Après
    // cet instant, aucune fonction ne replace le dragon et chaque ressource
    // repart de sa position physique courante.
    d.x = etat.cible.x - Math.cos(etat.cibleCap) * modele.approcheDist;
    d.y = etat.cible.y - Math.sin(etat.cibleCap) * modele.approcheDist;
    d.cap = etat.cibleCap;
    actualiserCible(.05);
  }

  function valeurCible(h) {
    if (estVille(etat.mode)) return Math.max(0, +h.valeur || 0);
    if (estRangee(etat.mode) && !h.dragonCible) return 0;
    if (auSol(h) || h.etat === "rentre") return 0;
    const e = etat.exposition.get(h);
    // « Tout brûler » ne confond pas un homme touché et une zone terminée.
    // La valeur descend avec la dose réellement reçue, puis tombe à zéro
    // seulement quand le corps est hors de combat.
    const frais = 1 - clamp(((e && e.dose) || 0) / 0.85, 0, 0.95);
    return frais * (h.etat === "deroute" ? 0.92 : 1);
  }

  function evaluerCouloir(ancre, cap, tous) {
    const d = etat.dragon, ux = Math.cos(cap), uy = Math.sin(cap);
    const membres = []; let gain = 0, frais = 0;
    const longueurCouloir = modele.couloirArriere + modele.couloirAvant;
    // Chaque profil engage la longueur qu'il parcourt pendant SON souffle plus
    // la portée de SON jet. Vhagar lit donc une bande beaucoup plus longue et
    // large qu'Arrax ; la sélection n'est pas seulement cosmétique.
    for (const q of tous) {
      const rx = q.p.x - ancre.p.x, ry = q.p.y - ancre.p.y;
      const longitudinal = rx * ux + ry * uy;
      const lateral = Math.abs(-rx * uy + ry * ux);
      const demi = modele.couloirLargeur0 +
        clamp((longitudinal + modele.couloirArriere) / longueurCouloir, 0, 1) *
        (modele.couloirLargeur1 - modele.couloirLargeur0);
      if (longitudinal < -modele.couloirArriere ||
          longitudinal > modele.couloirAvant || lateral > demi) continue;
      const valeur = valeurCible(q.h);
      if (valeur <= 0) continue;
      const deja = etat.zonesTraitees.some((z) =>
        (z.x - q.p.x) ** 2 + (z.y - q.p.y) ** 2 < 48 ** 2);
      const valeurFraiche = valeur * (deja ? 0.22 : 1);
      membres.push({ h: q.h, p: q.p, s: longitudinal, valeur,
        frais: valeurFraiche });
      gain += valeur; frais += valeurFraiche;
    }
    if (!membres.length) return null;
    membres.sort((a, b) => a.s - b.s);
    const etapes = [];
    for (const q of membres) {
      let e = etapes.at(-1);
      if (!e || q.s - e.dernier > 32) {
        e = { membres: [], x: 0, y: 0, poids: 0, frais: 0,
          premier: q.s, dernier: q.s };
        etapes.push(e);
      }
      e.membres.push(q.h); e.x += q.p.x * q.valeur; e.y += q.p.y * q.valeur;
      e.poids += q.valeur; e.frais += q.frais; e.dernier = q.s;
    }
    for (const e of etapes) { e.x /= e.poids || 1; e.y /= e.poids || 1; }
    const approche = { x: ancre.p.x - ux * modele.approcheDist,
                       y: ancre.p.y - uy * modele.approcheDist };
    const dx = approche.x - d.x, dy = approche.y - d.y;
    const distance = Math.hypot(dx, dy);
    const capApproche = Math.atan2(dy, dx);
    const virage = Math.abs(angle(capApproche - d.cap)) / Math.PI;
    // Une bonne ligne vue depuis l'armée peut être impossible à prendre depuis
    // le dragon : atteindre son point d'entrée en venant à contresens obligeait
    // Syrax à boucler autour de ce point. Le coût porte donc aussi sur l'angle
    // qu'il faudra encore fermer ENTRE l'arrivée et le couloir de feu.
    const entree = Math.abs(angle(cap - capApproche)) / Math.PI;
    const garde = modele.approcheDist * .42;
    const tropPres = clamp((garde - distance) / garde, 0, 1);
    const manoeuvre = 1 / (1 + 0.65 * virage + 2.8 * entree + 0.38 * tropPres);
    const primaire = etapes.reduce((a, e) => !a || e.frais > a.frais ? e : a, null);
    // Pour une armée, trois masses théoriquement enchaînables ne valent pas
    // trois fois une masse que le dragon est presque certain de prendre. La
    // cible primaire porte la décision ; le reste n'est qu'un bonus si le même
    // cap verrouillé le rencontre effectivement. En ville, une longue bande de
    // toits reste au contraire un objectif cohérent et conserve son gain.
    const valeurCouloir = estVille(etat.mode) ? frais
      : primaire.frais + Math.max(0, frais - primaire.frais) * 0.16;
    const accessibilite = estVille(etat.mode) ? manoeuvre : manoeuvre ** 2.15;
    return { h: ancre.h, p: ancre.p, membres: membres.map((q) => q.h),
      gain, frais, score: valeurCouloir * accessibilite, cap, etapes,
      guidage: primaire.membres.slice(), approche };
  }

  function choisirCibleStrategique() {
    if (estVille(etat.mode)) etat.hommes = incendie.ciblesDragon();
    const tous = etat.hommes.filter((h) => valeurCible(h) > 0)
      .map((h) => ({ h, p: localDepuisMonde(h) }));
    if (!tous.length) return false;
    // On extrait d'abord des ancres spatiales : tester les 216 × 216 couples
    // de corps répéterait trente-six fois la même ligne dans chaque bloc.
    const ancres = [];
    for (const q of tous) {
      if (ancres.every((a) => dist(a.p, q.p) > (estVille(etat.mode) ? 105 : 15))) ancres.push(q);
      if (ancres.length >= (estVille(etat.mode) ? 64 : 52)) break;
    }
    const evalues = [];
    for (const a of ancres) {
      const caps = [Math.atan2(a.p.y - etat.dragon.y, a.p.x - etat.dragon.x)];
      if (estVille(etat.mode)) {
        for (let i = 0; i < 12; i++) caps.push(i * Math.PI / 12);
      } else for (const b of ancres) {
          const separation = dist(a.p, b.p);
          if (b !== a && separation > 30 && separation < 210)
            caps.push(Math.atan2(b.p.y - a.p.y, b.p.x - a.p.x));
        }
      for (const cap of caps) {
        if (evalues.some((q) => dist(q.p, a.p) < 4 && Math.abs(angle(q.cap - cap)) < 0.08))
          continue;
        const q = evaluerCouloir(a, cap, tous);
        if (q && q.gain > 0) evalues.push(q);
      }
    }
    evalues.sort((a, b) => b.score - a.score);
    if (!evalues.length) return false;
    const distincts = [];
    for (const q of evalues) {
      if (distincts.every((p) => dist(p.p, q.p) > 52)) distincts.push(q);
      if (distincts.length >= 5) break;
    }
    etat.candidatsCibles = distincts;
    const meilleur = evalues[0];
    etat.cibleHomme = meilleur.h; etat.cibleMembres = meilleur.membres;
    etat.cibleGuidage = meilleur.guidage?.length ? meilleur.guidage.slice() : [meilleur.h];
    etat.cibleEtapes = meilleur.etapes; etat.cibleCap = meilleur.cap;
    etat.cibleValeur = meilleur.score; etat.cibleGain = meilleur.gain;
    etat.cibleChaines = meilleur.etapes.length;
    etat.cible.x = meilleur.p.x; etat.cible.y = meilleur.p.y;
    etat.cible.vx = 0; etat.cible.vy = 0; etat.dernierCentre = null;
    etat.cibleVerrouJus = Infinity; etat.selectionProchaine = false;
    const numero = etat.selections.length + 1;
    etat.selections.push({ numero, x: meilleur.p.x, y: meilleur.p.y,
      score: meilleur.score, gain: meilleur.gain, a: etat.t,
      cycle: etat.attaque, cap: meilleur.cap, chaines: meilleur.etapes.length });
    etat.message = estVille(etat.mode)
      ? `Cible ${numero} : bande de ${meilleur.etapes.length} secteur${meilleur.etapes.length > 1 ? "s" : ""} de toits encore combustibles.`
      : `Cible ${numero} : environ ${Math.round(meilleur.gain)} hommes sur ${meilleur.etapes.length} masse${meilleur.etapes.length > 1 ? "s" : ""} enchaînable${meilleur.etapes.length > 1 ? "s" : ""}.`;
    return true;
  }

  function actualiserCible(dt) {
    const actifs = etat.hommes.filter((h) => valeurCible(h) > 0);
    let lus;
    if (etat.phase === "reconnaissance") {
      // La reconnaissance lit l'armée entière. Choisir déjà une compagnie
      // ferait orbiter Syrax autour d'un détail avant qu'elle ait vu le tout.
      lus = (actifs.length ? actifs : etat.hommes).map(localDepuisMonde);
    } else {
      if (!etat.cibleMembres.length && !choisirCibleStrategique()) return;
      lus = etat.cibleGuidage.filter((h) => !auSol(h) && h.etat !== "rentre")
        .map(localDepuisMonde);
      if (!lus.length) lus = etat.cibleMembres.filter((h) => !auSol(h) && h.etat !== "rentre")
        .map(localDepuisMonde);
      // La cible peut être détruite pendant le souffle. On garde alors son
      // dernier point physique jusqu'à la sortie : aucune nouvelle décision
      // n'est permise au milieu d'un passage engagé.
      if (!lus.length) return;
    }
    const x = lus.reduce((s, p) => s + p.x, 0) / lus.length;
    const y = lus.reduce((s, p) => s + p.y, 0) / lus.length;
    const avant = etat.dernierCentre;
    if (avant && dt > 0) {
      const vx = (x - avant.x) / dt, vy = (y - avant.y) / dt;
      etat.cible.vx += (vx - etat.cible.vx) * Math.min(1, dt * 1.8);
      etat.cible.vy += (vy - etat.cible.vy) * Math.min(1, dt * 1.8);
      // La disparition d'un fuyard au bord du bac change le barycentre d'un
      // coup ; ce n'est pas une accélération réelle de la cible. La prédiction
      // ne peut donc dépasser un homme lancé à pleine fuite.
      const vc = Math.hypot(etat.cible.vx, etat.cible.vy);
      if (vc > 4.2) {
        etat.cible.vx *= 4.2 / vc; etat.cible.vy *= 4.2 / vc;
      }
    }
    etat.cible.x = x; etat.cible.y = y; etat.dernierCentre = { x, y };
    // Les corps continuent à bouger, donc le point visé et les étapes suivent
    // bien leur déplacement. En revanche, une passe déjà engagée garde son
    // cap : recalculer l'angle optimal à chaque dispersion des fuyards faisait
    // recommencer indéfiniment l'alignement sur la même cible. Le prochain cap
    // ne sera choisi qu'après la sortie du souffle (ou disparition réelle de
    // toute la cible).
    for (const e of etat.cibleEtapes) {
      const ps = e.membres.filter((h) => !auSol(h) && h.etat !== "rentre")
        .map(localDepuisMonde);
      if (ps.length) {
        e.x = ps.reduce((s, p) => s + p.x, 0) / ps.length;
        e.y = ps.reduce((s, p) => s + p.y, 0) / ps.length;
      }
    }
    if (etat.phase === "reconnaissance" && etat.cibleEtapes.length > 1) {
      const a = etat.cibleEtapes[0], b = etat.cibleEtapes.at(-1);
      const cap = Math.atan2(b.y - a.y, b.x - a.x);
      etat.cibleCap += angle(cap - etat.cibleCap) * Math.min(1, dt * 0.7);
    }
  }

  function marquerZoneTraitee() {
    const selection = etat.selections.at(-1);
    if (!selection) return;
    const etapes = etat.cibleEtapes.length ? etat.cibleEtapes
      : [{ x: etat.cible.x, y: etat.cible.y }];
    for (const e of etapes) etat.zonesTraitees.push({ x: e.x, y: e.y,
      numero: selection.numero, a: etat.t });
    etat.selectionProchaine = true;
  }

  function conduire(capVoulu, banqueMax, dt) {
    const d = etat.dragon;
    const erreur = angle(capVoulu - d.cap);
    const commande = clamp(erreur * 1.9, -banqueMax, banqueMax);
    d.banque += (commande - d.banque) * Math.min(1, dt * 2.45);
    // Syrax n'est pas une voilure fixe. À la composante de portance inclinée
    // s'ajoutent une dissymétrie de battement, la torsion du corps et la queue.
    // Cette accélération latérale reste bornée à 6,5 m/s² : elle resserre le
    // virage sans autoriser un pivot sur place ni une cassure du path.
    const battementLateral = clamp(erreur * 4.2,
      -modele.accelLateral, modele.accelLateral);
    const rotation = (G * Math.tan(d.banque) + battementLateral) / Math.max(8, d.v);
    d.accelLateral = G * Math.tan(d.banque) + battementLateral;
    d.rotation = rotation;
    d.cap += rotation * dt;
  }

  // À basse allure, le dragon ne se comporte plus comme une aile fixe qui
  // doit coucher son virage. Les battements portent le poids, la queue et la
  // dissymétrie des ailes font pivoter le corps, tandis que la translation
  // devient faible. C'est un lacet propulsé, pas un petit cercle coordonné.
  function conduireBasseAllure(capVoulu, dt) {
    const d = etat.dragon;
    const erreur = angle(capVoulu - d.cap);
    const lacet = clamp(erreur * 1.25, -modele.lacetLent, modele.lacetLent);
    const banqueLente = modele.banqueLente * Math.PI / 180;
    const commande = clamp(erreur * 0.16, -banqueLente, banqueLente);
    d.banque += (commande - d.banque) * Math.min(1, dt * 3.2);
    d.accelLateral = 0;
    d.rotation = lacet;
    d.cap += lacet * dt;
  }

  function altitude(hautVoulue, descenteMax, dt) {
    const d = etat.dragon;
    const az = clamp((hautVoulue - d.z) * 0.055 - d.vz * 0.58,
                     -descenteMax, 5.5);
    d.vz = clamp(d.vz + az * dt, -24, 8);
    d.z = Math.max(22, d.z + d.vz * dt);
    d.pente = Math.atan2(d.vz, Math.max(1, d.v));
  }

  function altitudePique(hautVoulue, resteAuSol, dt) {
    const d = etat.dragon;
    // Le point bas appartient à la ligne d'attaque, pas à une consigne
    // d'altitude asymptotique. L'ancien (haut-z)/5,2 freinait justement la
    // descente en approchant du sol : Arrax parcourait ~670 m avant d'atteindre
    // son plan de tir alors que sa passe n'en mesure que 275. Ici la verticale
    // intercepte le plan bas au moment où la ligne de feu rejoint la cible.
    // Le retrait de 1,2 s paie l'établissement progressif du piqué. La cible
    // ne doit pas arriver sous le ventre, mais sous le point où l'axe incliné
    // du jet rencontrera le sol : on retire donc cette avance géométrique.
    // La verticale maximale vaut environ 35° de la vitesse de piqué ; Arrax
    // corrige plus vivement que Vhagar sans gagner de maniabilité latérale.
    const descenteMax = Math.min(36, modele.pique * .58);
    const penteFeu = modele.penteFeu * Math.PI / 180;
    const avanceFeu = Math.min(modele.flamme * .72,
      hautVoulue / Math.max(.2, Math.tan(penteFeu)));
    const tempsSol = clamp((resteAuSol - avanceFeu) / Math.max(1, d.v) - 1.2,
      1.25, 14);
    const voulue = clamp((hautVoulue - d.z) / tempsSol, -descenteMax, -2);
    d.vz += (voulue - d.vz) * Math.min(1, dt * 1.75);
    d.z = Math.max(22, d.z + d.vz * dt);
    d.pente = Math.atan2(d.vz, Math.max(1, d.v));
  }

  function vitesseVers(voulue, dt, minimum = 12.5, freinMax = 3.8) {
    const d = etat.dragon;
    const impulsion = 1 + 0.035 * Math.sin(etat.phaseAile);
    const cible = voulue * impulsion;
    const a = clamp((cible - d.v) / 2.6, -freinMax, 2.2);
    // Après un vol battu lent, le plancher aérodynamique ne doit pas devenir
    // une catapulte numérique. Tant que la vitesse est sous ce plancher, elle
    // remonte par l'accélération calculée ; elle ne saute jamais à 12,5 m/s.
    d.v = clamp(d.v + a * dt, Math.min(minimum, d.v), modele.limite);
  }

  function avancerDragon(dt) {
    const d = etat.dragon;
    d.x += Math.cos(d.cap) * d.v * dt;
    d.y += Math.sin(d.cap) * d.v * dt;
    const f = etat.basseAllure ? modele.battementLent
      : modele.battement + (d.v > modele.presse || Math.abs(d.vz) > 6 ? 0.09 : 0);
    etat.phaseAile = (etat.phaseAile + TAU * f * dt) % TAU;
    // Force aérodynamique instantanée : la translation n'en reçoit qu'une
    // petite oscillation, le reste change l'aile, l'assiette et la portance.
    const poidsKN = modele.poids / 1000;
    const portage = etat.basseAllure ? .23 : 0;
    const poussee = etat.basseAllure ? .54 : .38;
    const relache = etat.basseAllure ? .18 : .13;
    etat.force = poidsKN * (1 + portage + poussee * Math.max(0, Math.sin(etat.phaseAile))
      - relache * Math.max(0, -Math.sin(etat.phaseAile)))
      + Math.max(0, -d.vz) * 0.7;
  }

  function reconnaissance(dt) {
    const d = etat.dragon, c = etat.cible;
    const futur = { x: c.x + c.vx * 8, y: c.y + c.vy * 8 };
    const dx = d.x - futur.x, dy = d.y - futur.y;
    const r = Math.hypot(dx, dy);
    const a = Math.atan2(dy, dx);
    const rayon = clamp(135 + 0.10 * d.z, 150, 230);
    const correction = clamp((r - rayon) / 105, -0.48, 0.48);
    conduire(a + Math.PI / 2 + correction, 35 * Math.PI / 180, dt);
    altitude(305 + 8 * Math.sin(etat.t / 18), 3.2, dt);
    vitesseVers(18.5, dt);
    avancerDragon(dt);
    const omega = G * Math.tan(Math.max(0, d.banque)) / Math.max(8, d.v);
    etat.progression += Math.max(0, omega) * dt;
    if (!etat.tourFait && etat.progression >= TAU) {
      etat.tourFait = true;
      etat.message = "Boucle complète : le centre de l'orbite a suivi la colonne.";
      if (etat.suite) transitionAttaque();
    }
  }

  function transitionAttaque() {
    const d = etat.dragon;
    // Aucun replacement : le ralliement part du dernier point de l'orbite.
    // Syrax prolonge d'abord sa tangente, gagne l'écartement nécessaire, puis
    // revient sur la cible par un virage coordonné.
    etat.phase = "dracarys"; etat.attaque = "ralliement";
    etat.altitudeEntree = d.z; etat.vitesseEntree = d.v;
    etat.souffle = 0; etat.prochainRugissement = etat.t;
    etat.attaqueDepuis = etat.t; etat.distanceAvant = Infinity;
    choisirCibleStrategique();
    etat.message = `Le tour est fait. ${modele.nom} ouvre sa courbe pour revenir en piqué.`;
  }

  function jugerRupture() {
    if (estVille(etat.mode)) return;
    if (!bataille || !bataille.jugerRuptureUnite ||
        (!etat.progression && !estArmee(etat.mode) && !estRangee(etat.mode))) return;
    const fermeture = estArmee(etat.mode) || estRangee(etat.mode)
      ? clamp(etat.t / 22, 0, 1)
      : clamp(etat.progression / TAU, 0, 1);
    const juges = estRangee(etat.mode) ? etat.hommes.filter((h) => h.dragonCible) : etat.hommes;
    const actifs = juges.filter((h) => !auSol(h) && h.etat !== "rentre");
    const voient = actifs.filter((h) => {
      const p = etat.perception.get(h);
      return p && etat.t - p.vue < 2;
    }).length;
    const cap = etat.repere ? etat.repere.cap : 0;
    // Le banc ne dit pas « fuyez ». Il rapporte au système commun les faits
    // perceptibles : presque toute la colonne voit la menace, aucune arme ne
    // peut atteindre trois cents mètres, et la trajectoire ferme peu à peu le
    // cercle. Le jugement et la part rompue sont calculés dans bataille2d.
    etat.bilanRupture = bataille.jugerRuptureUnite(juges, {
      menaceVue: actifs.length ? voient / actifs.length : 0,
      riposte: 0,
      danger: "dragon",
      fermeture,
      avantX: Math.cos(cap), avantY: Math.sin(cap),
      cause: estArmee(etat.mode) || estRangee(etat.mode)
        ? "le dragon ennemi s'aligne sur nous et nous n'avons aucun moyen de le combattre"
        : "le dragon ennemi nous tourne au-dessus et nous n'avons aucun moyen de le combattre",
    });
    etat.rupturePart = etat.bilanRupture.part;
    if (etat.bilanRupture.nouveaux && etat.ruptureA == null) etat.ruptureA = etat.t;
  }

  function faceAuDragon(h, p) {
    const f = directionLocale(h.fx || 1, h.fy || 0);
    const dx = etat.dragon.x - p.x, dy = etat.dragon.y - p.y;
    const n = Math.hypot(dx, dy) || 1;
    return clamp((f.x * dx + f.y * dy) / n, -1, 1);
  }

  /**
   * Le passage existe avant le feu : silhouette qui grossit puis rugissement.
   * Ces signaux ne déplacent directement personne. Ils entrent dans les mêmes
   * boîtes sensorielles que le fer, les cris et les voisins du moteur commun.
   */
  function fairePercevoirDragon() {
    if (estVille(etat.mode)) return;
    if (!bataille || !bataille.dangerExterieur) return;
    const d = etat.dragon, maintenant = etat.t;
    const menaceMonde = mondeDepuisLocal({ x: d.x, y: d.y });
    const rugit = maintenant + 1e-6 >= etat.prochainRugissement;
    if (rugit) etat.prochainRugissement = maintenant +
      (etat.phase === "reconnaissance" ? 17 : 999);
    const expositions = [];
    for (const h of etat.hommes) {
      if (estRangee(etat.mode) && !h.dragonCible) continue;
      if (auSol(h)) continue;
      const p = localDepuisMonde(h), dx = d.x - p.x, dy = d.y - p.y;
      const horizontal = Math.hypot(dx, dy), oblique = Math.hypot(horizontal, d.z);
      if (oblique > 430 && !rugit) continue;
      const mem = etat.perception.get(h) || { vue: -99, ouie: -99, chaleur: -99 };
      const q = { homme: h, genre:"dragon", deFace: faceAuDragon(h, p),
                  menaceX: menaceMonde.x, menaceY: menaceMonde.y };
      if (maintenant - mem.vue >= 0.65) {
        const apparent = modele.envergure / Math.max(35, oblique);
        const fermeture = Math.max(0, d.v * Math.cos(angle(Math.atan2(-dy, -dx) - d.cap)));
        const tau = oblique / Math.max(1, fermeture);
        q.vue = clamp(apparent * 2.8 + 0.55 / tau, 0.08, 1);
        q.menace = clamp(apparent * 3.6 + 0.8 / tau, 0.1, 1);
        q.soudaineteVue = clamp(0.18 + 1.8 / tau, 0.12, 1);
        mem.vue = maintenant;
      }
      if (rugit && maintenant - mem.ouie >= 1.5) {
        q.ouie = clamp(1.15 - oblique / 620, 0.25, 1);
        q.soudaineteOuie = 0.92; mem.ouie = maintenant;
      }
      if (q.vue || q.ouie) expositions.push(q);
      etat.perception.set(h, mem);
    }
    if (expositions.length)
      etat.bilanDanger = bataille.dangerExterieur(expositions, modele.nom);
  }

  function temperatureJet(s, r, enveloppe) {
    const L = modele.flamme;
    const rayon = modele.rayonFeu + modele.ouvertureFeu * s;
    const tc = AMBIANTE + (modele.noyau - AMBIANTE)
      * Math.exp(-Math.max(0, s - 0.25 * L) / (0.65 * L));
    const radial = Math.pow(Math.max(0, 1 - (r / rayon) ** 2), 0.35);
    return AMBIANTE + (tc - AMBIANTE) * radial * enveloppe;
  }

  /**
   * Intersection exacte du volume conique avec z=0.
   *
   * L'axe `a` plonge de PENTE_FEU. À la distance axiale s, le jet est un disque
   * de rayon R(s), dans le plan engendré par b (latéral horizontal) et c
   * (perpendiculaire à l'axe dans le plan vertical). Le sol impose :
   *
   *   z_centre + v · c_z = 0  donc  v = -z_centre / cos(pente)
   *
   * Si |v| <= R, le disque coupe le sol suivant une tranche de demi-largeur
   * sqrt(R²-v²). L'union de ces tranches est l'empreinte — sans cône 2D
   * inventé, sans projection aléatoire.
   */
  function intersectionConeSol(d) {
    const penteFeu = modele.penteFeu * Math.PI / 180;
    const cp = Math.cos(penteFeu), sp = Math.sin(penteFeu);
    const ch = Math.cos(d.cap), sh = Math.sin(d.cap);
    const bx = -sh, by = ch;
    const tranches = [];
    for (let s = 0; s <= modele.flamme + 1e-6; s += 0.75) {
      const R = modele.rayonFeu + modele.ouvertureFeu * s;
      const zCentre = d.z - sp * s;
      const v = -zCentre / cp;
      if (Math.abs(v) > R) continue;
      const avance = cp * s + sp * v;
      const cx = d.x + ch * avance, cy = d.y + sh * avance;
      const demi = Math.sqrt(Math.max(0, R * R - v * v));
      tranches.push({ s, R, v, cx, cy, demi, bx, by,
        gauche: { x: cx + bx * demi, y: cy + by * demi },
        droite: { x: cx - bx * demi, y: cy - by * demi } });
    }
    return tranches;
  }

  function deposerChaleur(dt) {
    const d = etat.dragon;
    const enveloppe = lisse(0, 0.01, etat.souffle)
      * (1 - lisse(modele.souffle * .84, modele.souffle, etat.souffle));
    const tranches = intersectionConeSol(d);
    etat.empreinte = tranches;
    if (!tranches.length || enveloppe <= 0) return;
    etat.derniereCoupe = {
      longueur: tranches.length > 1
        ? Math.hypot(tranches.at(-1).cx - tranches[0].cx,
                     tranches.at(-1).cy - tranches[0].cy) : 0,
      largeur: tranches.reduce((m, q) => Math.max(m, 2 * q.demi), 0),
      altitude: d.z,
    };

    if (estVille(etat.mode) && incendie && incendie.deposerSouffle) {
      const r = etat.repere, cr = Math.cos(r.cap), sr = Math.sin(r.cap);
      const point = (p) => mondeDepuisLocal(p);
      const tranchesMonde = tranches.map((q) => ({ ...q,
        cx:point({ x:q.cx, y:q.cy }).x, cy:point({ x:q.cx, y:q.cy }).y,
        bx:cr * q.bx - sr * q.by, by:sr * q.bx + cr * q.by,
        gauche:point(q.gauche), droite:point(q.droite),
      }));
      incendie.deposerSouffle({ tranches:tranchesMonde, dt, noyau:modele.noyau,
        dragon:modele.nom, temperature:(s, r3d) => temperatureJet(s, r3d, enveloppe) });
      // En ville la trace thermique utile est portée par les vrais contours
      // de bâtiments. La grille de sol du banc militaire ferait doublon et
      // coûterait des milliers de cellules sans changer une seule ignition.
      return;
    }

    // Dose sur une grille de deux mètres. `r` est bien la distance 3D à l'axe
    // dans le disque (sqrt(u²+v²)), et non la seule distance latérale au path.
    for (let i = 0; i < tranches.length; i += 2) {
      const q = tranches[i];
      const pasU = 2;
      const n = Math.max(1, Math.ceil((2 * q.demi) / pasU));
      for (let j = 0; j <= n; j++) {
        const u = q.demi ? -q.demi + (2 * q.demi * j / n) : 0;
        const r = Math.hypot(u, q.v);
        const T = temperatureJet(q.s, r, enveloppe);
        if (T < 545) continue;
        const x = q.cx + q.bx * u, y = q.cy + q.by * u;
        const gx = Math.round(x / 2), gy = Math.round(y / 2), cle = gx + ":" + gy;
        let h = etat.chaleur.get(cle);
        if (!h) {
          h = { x: gx * 2, y: gy * 2, dose: 0, pic: T, age: 0, r: 1.55 };
          etat.chaleur.set(cle, h);
        }
        h.dose += ((T - 545) / 1455) ** 2 * dt * 4.2;
        h.pic = Math.max(h.pic, T); h.age = 0;
      }
    }

    const tx = Math.cos(d.cap), ty = Math.sin(d.cap), expositions = [];
    const menaceMonde = mondeDepuisLocal({ x: d.x, y: d.y });
    for (const h of etat.hommes) {
      if (auSol(h)) continue;
      const p = localDepuisMonde(h);
      let chaleur = AMBIANTE;
      for (const q of tranches) {
        const dx = p.x - q.cx, dy = p.y - q.cy;
        const longitudinal = Math.abs(dx * tx + dy * ty);
        const u = dx * q.bx + dy * q.by;
        const horsLateral = Math.max(0, Math.abs(u) - q.demi);
        // L'intersection colorée reste le cône géométrique exact. Un corps a
        // toutefois une largeur et le front turbulent rayonne autour de cette
        // surface : on intègre un halo thermique de trois mètres, décroissant
        // continûment, au lieu de demander que le centre ponctuel du soldat
        // tombe à moins de 1,15 m d'une tranche échantillonnée tous les 0,75 m.
        if (longitudinal > 3.2 || horsLateral > 3.2) continue;
        const attenuation = Math.exp(-((longitudinal / 3) ** 2 + (horsLateral / 3) ** 2));
        const rCoeur = Math.min(Math.hypot(u, q.v), Math.max(0, q.R - 1.4));
        const tCoeur = temperatureJet(q.s, rCoeur, enveloppe);
        chaleur = Math.max(chaleur, AMBIANTE + (tCoeur - AMBIANTE) * attenuation);
      }
      if (chaleur <= 545) continue;
      const x = clamp((chaleur - 545) / (modele.noyau - 545), 0, 1);
      const e = etat.exposition.get(h);
      if (e) { e.dose += x * x * dt * 4.2; e.pic = Math.max(e.pic, chaleur); }
      const mem = etat.perception.get(h) || { vue: -99, ouie: -99, chaleur: -99 };
      const q = {
        homme: h, genre:"dragon", deFace: faceAuDragon(h, p),
        menace: clamp(0.55 + x, 0, 1),
        menaceX: menaceMonde.x, menaceY: menaceMonde.y,
        dureeMenace: 1.4,
        // Une fraction de seconde au noyau suffit à mettre un homme hors de
        // combat ; l'enveloppe et la distance 3D font toute la dispersion.
        // À près de 1 000–2 000 K, le passage ne dure souvent que deux ou
        // trois pas de 25 ms : intégrer seulement la chaleur instantanée à
        // 620 PV/s plafonnait donc toute brûlure à une trentaine de PV. Le flux
        // turbulent est traité comme une impulsion thermique brève et massive;
        // le bord reste graduel, le noyau met immédiatement hors de combat.
        degat: Math.pow(x, 1.15) * dt * modele.flux,
      };
      if (etat.t - mem.chaleur >= 0.16) {
        q.chaleur = clamp(0.28 + x * 0.9, 0, 1);
        q.soudaineteChaleur = clamp(0.45 + x, 0, 1);
        mem.chaleur = etat.t;
      }
      etat.perception.set(h, mem); expositions.push(q);
    }
    if (expositions.length && bataille && bataille.dangerExterieur) {
      const r = bataille.dangerExterieur(expositions, `souffle de ${modele.nom}`);
      etat.bilanDanger = r;
      etat.victimes = etat.hommes.filter(auSol).length;
    }

    // Le splatter est secondaire : il part du bord et de l'extrémité de
    // l'intersection calculée. Il n'ajoute jamais de dose hors du cône.
    if (hasard() < dt * 7) {
      const q = tranches[tranches.length - 1];
      const cote = hasard() < 0.5 ? -1 : 1;
      etat.projections.push({
        x: q.cx + q.bx * cote * (q.demi + hasard() * 7) + tx * hasard() * 9,
        y: q.cy + q.by * cote * (q.demi + hasard() * 7) + ty * hasard() * 9,
        age: 0, vie: 1.8 + hasard() * 2.4, r: 0.7 + hasard() * 1.7,
      });
    }
  }

  function opportuniteDansCap(cap, longueur = 165, demiMax = 6.3) {
    const d = etat.dragon, ux = Math.cos(cap), uy = Math.sin(cap);
    const vus = []; let gain = 0, x = 0, y = 0;
    for (const h of etat.hommes) {
      const valeur = valeurCible(h);
      if (valeur <= 0) continue;
      const p = localDepuisMonde(h), rx = p.x - d.x, ry = p.y - d.y;
      const longitudinal = rx * ux + ry * uy;
      const lateral = Math.abs(-rx * uy + ry * ux);
      const demiBase = Math.min(4.2, demiMax);
      const demi = demiBase + clamp(longitudinal / longueur, 0, 1) * (demiMax - demiBase);
      if (longitudinal < 24 || longitudinal > longueur || lateral > demi) continue;
      vus.push({ h, p, s: longitudinal, valeur });
      gain += valeur; x += p.x * valeur; y += p.y * valeur;
    }
    if (!vus.length) return null;
    vus.sort((a, b) => a.s - b.s);
    let chaines = 1;
    for (let i = 1; i < vus.length; i++) if (vus[i].s - vus[i - 1].s > 32) chaines++;
    x /= gain || 1; y /= gain || 1;
    return { gain, chaines, cap, centreCap: Math.atan2(y - d.y, x - d.x), membres: vus };
  }

  function opportuniteDevant(longueur = modele.opportunite,
                             demiMax = modele.opportuniteLargeur) {
    return opportuniteDansCap(etat.dragon.cap, longueur, demiMax);
  }

  // Même géométrie que `deposerChaleur` : D4 ne déclenche pas sur un couloir
  // prévisionnel si le cône 3D, à cette altitude précise, ne coupe encore
  // aucun corps. Le halo de 3,2 m est celui de l'enveloppe thermique déjà
  // appliquée aux soldats, pas un élargissement propre au ciblage.
  function opportuniteDansEmpreinteSol() {
    const d = etat.dragon, tx = Math.cos(d.cap), ty = Math.sin(d.cap);
    const tranches = intersectionConeSol(d);
    if (!tranches.length) return null;
    const vus = []; let gain = 0, x = 0, y = 0;
    for (const h of etat.hommes) {
      const valeur = valeurCible(h);
      if (valeur <= 0) continue;
      const p = localDepuisMonde(h);
      let chaleur = AMBIANTE;
      for (const q of tranches) {
        const dx = p.x - q.cx, dy = p.y - q.cy;
        const longitudinal = Math.abs(dx * tx + dy * ty);
        const u = dx * q.bx + dy * q.by;
        const horsLateral = Math.max(0, Math.abs(u) - q.demi);
        if (longitudinal > 3.2 || horsLateral > 3.2) continue;
        const attenuation = Math.exp(-((longitudinal / 3) ** 2 +
          (horsLateral / 3) ** 2));
        const rCoeur = Math.min(Math.hypot(u, q.v), Math.max(0, q.R - 1.4));
        const tCoeur = temperatureJet(q.s, rCoeur, 1);
        chaleur = Math.max(chaleur,
          AMBIANTE + (tCoeur - AMBIANTE) * attenuation);
      }
      // On attend une vraie cible létale, pas un homme seulement visible dans
      // la frange tiède. Mais le seuil doit suivre le flux du modèle : 0,42
      // était hors d'atteinte au sol pour le jet court d'Arrax (maximum ≈0,32
      // à 22 m), ce qui interdisait mathématiquement tous ses Dracarys. La loi
      // de dégâts inverse ici la dose nécessaire pour retirer 25 PV pendant
      // un contact conservateur de 0,1 s.
      const xThermique = clamp((chaleur - 545) / (modele.noyau - 545), 0, 1);
      const seuilLetal = Math.pow(25 / (modele.flux * .1), 1 / 1.15);
      if (xThermique < seuilLetal) continue;
      vus.push({ h, p, valeur }); gain += valeur;
      x += p.x * valeur; y += p.y * valeur;
    }
    if (!vus.length) return null;
    x /= gain || 1; y /= gain || 1;
    return { gain, chaines:1, cap:d.cap,
      centreCap:Math.atan2(y - d.y, x - d.x), membres:vus };
  }

  function meilleureOccasionPique(demiMax = 12) {
    const d = etat.dragon;
    const caps = [etat.capPassage ?? etat.cibleCap, d.cap];
    for (const h of etat.hommes) {
      if (valeurCible(h) <= 0) continue;
      const p = localDepuisMonde(h), distance = dist(d, p);
      if (distance < 18 || distance > modele.opportunite + 80) continue;
      const cap = Math.atan2(p.y - d.y, p.x - d.x);
      if (Math.abs(angle(cap - d.cap)) < 0.9 &&
          caps.every((a) => Math.abs(angle(a - cap)) > 0.035)) caps.push(cap);
    }
    let meilleur = null;
    for (const cap of caps) {
      const occasion = opportuniteDansCap(cap, modele.opportunite + 25, demiMax);
      if (!occasion) continue;
      const correction = Math.abs(angle(cap - d.cap));
      occasion.score = occasion.gain / (1 + correction * 1.35);
      if (!meilleur || occasion.score > meilleur.score) meilleur = occasion;
    }
    return meilleur;
  }

  function capVersHommePique(h) {
    if (!h || valeurCible(h) <= 0) return null;
    const d = etat.dragon, p = localDepuisMonde(h);
    // À la fin du piqué, viser la position présente revient à viser derrière
    // un homme qui court. On ne prédit que jusqu'à 1,4 s : assez pour ses
    // quelques mètres de fuite, jamais assez pour inventer sa prochaine
    // décision ou transformer le dragon en tourelle.
    const temps = clamp(dist(d, p) / Math.max(1, d.v), 0, 1.4);
    const futur = { x:p.x + (h.vx || 0) * temps,
                    y:p.y + (h.vy || 0) * temps };
    return Math.atan2(futur.y - d.y, futur.x - d.x);
  }

  function dracarys(dt) {
    const d = etat.dragon, c = etat.cible;
    const etaitBasseAllure = etat.basseAllure;
    etat.basseAllure = false;
    const futur = { x: c.x + c.vx * 7, y: c.y + c.vy * 7 };
    let distance = dist(d, futur);

    const engagerPique = (message) => {
      etat.capPassage = etat.cibleCap;
      etat.piqueHomme = null;
      etat.attaque = "pique"; etat.attaqueDepuis = etat.t;
      etat.altitudeEntree = d.z; etat.vitesseEntree = d.v;
      const ux = Math.cos(etat.capPassage), uy = Math.sin(etat.capPassage);
      etat.distanceAvant = (futur.x - d.x) * ux + (futur.y - d.y) * uy;
      etat.message = message;
    };
    const cibleEngageeValide = () => etat.cibleMembres.some((h) => valeurCible(h) > 0);

    if (etat.attaque === "ralliement") {
      const ux = Math.cos(etat.cibleCap), uy = Math.sin(etat.cibleCap);
      const approche = { x: futur.x - ux * modele.approcheDist,
                         y: futur.y - uy * modele.approcheDist };
      const distanceApproche = dist(d, approche);
      const echelleApproche = modele.approcheDist / 360;
      const visee = distanceApproche < 135 * echelleApproche ? etat.cibleCap
        : Math.atan2(approche.y - d.y, approche.x - d.x);
      const reste = (futur.x - d.x) * ux + (futur.y - d.y) * uy;
      const lateral = Math.abs(-(futur.x - d.x) * uy + (futur.y - d.y) * ux);
      const alignementNormal = distanceApproche < 155 * echelleApproche &&
        reste > .72 * modele.approcheDist && reste < 1.42 * modele.approcheDist &&
        lateral < 120 * Math.sqrt(echelleApproche) &&
        Math.abs(angle(etat.cibleCap - d.cap)) < modele.banqueRalliement * Math.PI / 180 * .5;
      if (alignementNormal && d.z > modele.altitudeRalliement * .88) {
        // Une courbe coordonnée peut ne jamais passer par le point mathématique
        // d'approche. Après un tour de mise en place, Syrax ne recommence pas
        // l'orbite : elle prend la masse devant elle et fige ce cap pour le
        // piqué. C'est le souffle, plus bas, qui décidera s'il existe vraiment
        // assez de corps dans l'axe.
        engagerPique(`Piqué aligné sur ${etat.cibleChaines} masse${etat.cibleChaines > 1 ? "s" : ""} enchaînable${etat.cibleChaines > 1 ? "s" : ""}.`);
      } else if (etat.t - etat.attaqueDepuis > 28) {
        // Un alignement imparfait ne justifie pas de choisir encore un nouvel
        // angle sur les mêmes hommes. Tant que la cible existe, le dragon
        // convertit la courbe en passe et laisse le guidage opportuniste du
        // piqué exploiter ce qui entrera réellement dans son axe.
        if (cibleEngageeValide()) {
          engagerPique(`La ligne reste imparfaite : ${modele.nom} verrouille néanmoins son cap et convertit l'approche en passe.`);
        } else {
          choisirCibleStrategique();
          etat.attaqueDepuis = etat.t;
          etat.message = `La cible a disparu : ${modele.nom} prolonge son vol et engage une autre ligne atteignable.`;
          conduire(visee, modele.banqueRalliement * Math.PI / 180, dt);
          altitude(modele.altitudeRalliement, 4.5, dt);
          vitesseVers(modele.approcheVitesse, dt); avancerDragon(dt);
        }
      } else if (distanceApproche < 230 * echelleApproche) {
        // Arrivé dans sa fenêtre, Syrax ne « consomme » plus son temps par de
        // petits tours. Elle casse sa vitesse, porte son poids aux ailes et
        // finit son lacet presque sur place. Dès que le cap est bon, le test
        // ci-dessus libère le piqué sans replacement.
        if (etaitBasseAllure && etat.t - etat.basseAllureDepuis > modele.attenteLente) {
          if (cibleEngageeValide()) {
            engagerPique(`La tenue sur place coûte trop : ${modele.nom} verrouille son cap et abat son nez.`);
          } else {
            choisirCibleStrategique();
            etat.attaqueDepuis = etat.t;
            etat.message = `La cible s'est dispersée : ${modele.nom} reprend de l’allure vers une autre entrée.`;
            altitude(modele.altitudeRalliement, 4.5, dt);
            vitesseVers(modele.approcheVitesse, dt); avancerDragon(dt);
          }
        } else {
          etat.basseAllure = true;
          if (!etaitBasseAllure) {
            etat.basseAllureDepuis = etat.t;
            etat.message = `${modele.nom} casse sa vitesse et se tient aux ailes pour établir son prochain piqué.`;
          }
          conduireBasseAllure(etat.cibleCap, dt);
          altitude(modele.altitudeRalliement, 4.5, dt);
          vitesseVers(modele.volLent, dt, modele.volLentMin, modele.freinLent);
          avancerDragon(dt);
        }
      } else {
        conduire(visee, modele.banqueRalliement * Math.PI / 180, dt);
        altitude(modele.altitudeRalliement, 4.5, dt);
        vitesseVers(modele.approcheVitesse, dt); avancerDragon(dt);
      }
    } else if (etat.attaque === "pique") {
      // Le passage est une LIGNE. On ne poursuit plus le barycentre avec le
      // nez pendant la descente : la correction reste bornée autour du cap
      // choisi, puis une occasion réellement dans l'axe peut déclencher le feu.
      const capPassage = etat.capPassage ?? etat.cibleCap;
      // En haut on acquiert une ligne large ; sous 95 m on centre le couloir
      // sur la largeur réellement balayée par le noyau au sol.
      // Dans D4 une masse rompue s'évente très vite. Syrax peut ouvrir le feu
      // dès que la longueur de son jet incliné atteint effectivement le sol ;
      // l'intersection 3D reste ensuite seule juge de ce qui brûle.
      const altitudeTirEffective = estRangee(etat.mode)
        ? Math.min(modele.flamme * Math.sin(modele.penteFeu * Math.PI / 180) * .96,
          modele.altitudeTir * 1.25)
        : modele.altitudeTir;
      const guide = meilleureOccasionPique(d.z < altitudeTirEffective * 2.8
        ? modele.opportuniteLargeur
        : modele.opportuniteLargeur * 1.9);
      if (etat.piqueHomme && valeurCible(etat.piqueHomme) <= 0)
        etat.piqueHomme = null;
      // L'occasion reste libre tant que le dragon est haut. Dans les quatre
      // dernières hauteurs de tir, choisir encore un autre fuyard à chaque
      // pas faisait osciller le cap entre plusieurs bonnes solutions et les
      // manquer toutes. On verrouille alors un corps réellement contenu dans
      // le meilleur couloir et l'on termine ce passage sur lui.
      if (!etat.piqueHomme && guide && d.z < altitudeTirEffective * 4.2) {
        let meilleur = null, ecart = Infinity;
        for (const q of guide.membres) {
          const a = Math.abs(angle(Math.atan2(q.p.y - d.y, q.p.x - d.x) - guide.cap));
          if (a < ecart) { ecart = a; meilleur = q.h; }
        }
        etat.piqueHomme = meilleur;
      }
      const capVerrouille = capVersHommePique(etat.piqueHomme);
      conduire(capVerrouille ?? (guide ? guide.cap : capPassage),
               (d.z < altitudeTirEffective * 2.8 ? modele.banquePiqueBas
                 : modele.banquePiqueHaut) * Math.PI / 180, dt);
      // Le point bas demandé est sous l'altitude de tir : l'inertie verticale
      // amène ainsi Syrax à 34–40 m au premier passage, au lieu de la faire
      // tourner autour de la cible en attendant la fin d'une descente trop douce.
      const uxPassage = Math.cos(capPassage), uyPassage = Math.sin(capPassage);
      const restePique = (futur.x - d.x) * uxPassage +
        (futur.y - d.y) * uyPassage;
      altitudePique(modele.altitudePique, restePique, dt);
      const perdue = Math.max(0, etat.altitudeEntree - d.z);
      const energetique = Math.min(modele.pique,
        Math.sqrt(etat.vitesseEntree ** 2 + 2 * G * 0.45 * perdue));
      vitesseVers(energetique, dt);
      avancerDragon(dt);
      distance = dist(d, futur);
      const occasion = estRangee(etat.mode)
        ? opportuniteDansEmpreinteSol()
        : opportuniteDevant();
      // Sous trente-quatre mètres, l'axe chaud — et pas seulement la frange du
      // cône — peut atteindre le sol pendant le passage. Plus haut, le rendu
      // serait spectaculaire mais la troupe ne recevrait qu'un bord tiède.
      const tentatives = etat.passages + etat.passagesManques;
      const seuilOccasion = estRangee(etat.mode) ? .55
        : estArmee(etat.mode) && tentatives < 2 ? modele.seuilOccasion : 0.8;
      if (d.z < altitudeTirEffective && occasion && occasion.gain >= seuilOccasion) {
        conduire(occasion.centreCap, modele.banqueSouffle * Math.PI / 180, dt);
        etat.attaque = "souffle";
        // L'empreinte exacte qui autorise le Dracarys reçoit la première
        // impulsion dans ce même pas. Sinon le corps-à-corps, exécuté juste
        // après, pouvait retirer l'unique cible avant le premier dépôt et
        // produire l'absurde « souffle réussi, zéro exposé ».
        etat.souffle = .012; etat.attaqueDepuis = etat.t;
        etat.passages++; etat.passagesOpportunistes++;
        if (etat.premierFeuA == null) etat.premierFeuA = etat.t;
        etat.message = `Dracarys d'occasion : ≈${Math.round(occasion.gain)} corps dans l'axe, sur ${occasion.chaines} masse${occasion.chaines > 1 ? "s" : ""}.`;
        deposerChaleur(dt);
      } else {
        const ux = Math.cos(capPassage), uy = Math.sin(capPassage);
        const reste = (futur.x - d.x) * ux + (futur.y - d.y) * uy;
        // Une passe se juge dans l'espace, pas au même chronomètre pour Arrax
        // et Vhagar. Le plafond arbitraire de 20 s faisait justement renoncer
        // Vhagar à 61 m, environ trois dixièmes de seconde avant son plan de
        // tir à 58 m. On ressource lorsque la ligne visée est réellement
        // passée derrière, avec une marge proportionnelle à la portée du jet.
        const depassement = Math.max(60, modele.opportunite * .75);
        if (reste < -depassement) {
        // Un passage manqué ne téléporte pas le dragon pour le « rejouer » :
        // il ressource et construit simplement une nouvelle courbe.
          etat.attaque = "sortie"; etat.attaqueDepuis = etat.t;
          etat.passagesManques++;
          // Une passe réellement manquée est l'abandon explicite du plan : à
          // la ressource, on relit la position actuelle des fuyards au lieu de
          // reprendre un troisième angle sur la masse initiale dispersée.
          etat.selectionProchaine = true;
          etat.message = `Aucune masse rentable n'est entrée dans l'axe : ${modele.nom} ressource sans souffler au hasard.`;
        }
      }
      etat.distanceAvant = Math.min(etat.distanceAvant, distance);
    } else if (etat.attaque === "souffle") {
      const occasion = opportuniteDevant(modele.opportunite,
                                         modele.opportuniteLargeur * 1.04);
      // Une correction de quelques degrés permet de prendre la seconde masse
      // sans transformer le souffle en lacet impossible à quarante mètres.
      const visee = occasion && Math.abs(angle(occasion.centreCap - d.cap)) < 0.30
        ? occasion.centreCap : (etat.capPassage ?? etat.cibleCap);
      conduire(visee, modele.banqueSouffle * Math.PI / 180, dt);
      altitude(modele.altitudePique, 5.5, dt);
      vitesseVers(modele.vitesseSouffle, dt); avancerDragon(dt);
      etat.souffle += dt; deposerChaleur(dt);
      if (etat.souffle >= modele.souffle) {
        etat.attaque = "sortie"; etat.attaqueDepuis = etat.t;
        marquerZoneTraitee();
        etat.empreinte = [];
        etat.message = "Souffle coupé : la braise refroidit, la carbonisation demeure.";
      }
    } else if (etat.attaque === "sortie") {
      conduire(d.cap, 0, dt);
      altitude(modele.altitudeSortie, 2.5, dt);
      vitesseVers(modele.vitesseSortie, dt); avancerDragon(dt);
      if (d.z > modele.sortieDeclenche && dist(d, c) > modele.approcheDist * .53 &&
          etat.t - etat.attaqueDepuis > 3) {
        etat.attaque = "ralliement"; etat.attaqueDepuis = etat.t;
        etat.capPassage = null;
        etat.distanceAvant = Infinity;
        const change = etat.selectionProchaine && choisirCibleStrategique();
        etat.message = change
          ? `Ressource achevée : ${modele.nom} engage la cible ${etat.selections.length}, choisie hors du passage précédent.`
          : `${modele.nom} poursuit son vol, élargit, puis prépare un nouveau passage.`;
      }
    } else {
      avancerDragon(dt);
    }
  }

  function enregistrer() {
    if (etat.t - etat.dernierPoint < 0.16) return;
    etat.dernierPoint = etat.t;
    const d = etat.dragon;
    const avant = etat.chemin.at(-1);
    if (avant) etat.sautMax = Math.max(etat.sautMax,
      Math.hypot(d.x - avant.x, d.y - avant.y, d.z - avant.z));
    etat.chemin.push({ x: d.x, y: d.y, z: d.z,
      phase: etat.phase === "dracarys" ? etat.attaque : "reconnaissance" });
    if (etat.chemin.length > 1400) etat.chemin.shift();
  }

  function avancerSoldats(dt) {
    if (estVille(etat.mode)) return;
    if (!bataille) return;
    etat.detteBataille += dt;
    while (etat.detteBataille + 1e-9 >= 0.05) {
      etat.detteBataille -= 0.05;
      bataille.pas(0.05);
      actualiserCible(0.05);
      for (const h of etat.hommes) {
        const j = h.l1 && h.l1.jambes;
        if (j && etat.reactionsVues[j]) etat.reactionsVues[j].add(h);
      }
    }
    etat.victimes = etat.hommes.filter(auSol).length;
  }

  function pas(dt) {
    if (!etat || dt <= 0) return;
    const n = Math.ceil(dt / 0.025), h = dt / n;
    for (let k = 0; k < n; k++) {
      etat.t += h;
      if (etat.phase === "reconnaissance") reconnaissance(h); else dracarys(h);
      fairePercevoirDragon();
      jugerRupture();
      avancerSoldats(h);
      if (estVille(etat.mode) && incendie) {
        incendie.pas(h, { peindre:false });
        // Agréger 47 000 toits n'a de sens que si de vrais combattants sont
        // présents, et au rythme de leur perception — jamais à chaque image.
        if (bataille && bataille.signalerIncendies && incendie.dangers &&
            bataille.troupe && bataille.troupe().length &&
            etat.t >= (etat.prochainSignalIncendie || 0)) {
          bataille.signalerIncendies(incendie.dangers(), .9);
          etat.prochainSignalIncendie = etat.t + .45;
        }
      }
      for (const c of etat.chaleur.values()) c.age += h;
      for (const p of etat.projections) p.age += h;
      etat.projections = etat.projections.filter((p) => p.age < p.vie);
      enregistrer();
    }
    if (estVille(etat.mode) && incendie) incendie.rendre();
    rendre(); mettreStats();
  }

  function fond() {
    const v = vueCarte && vueCarte.length === 4
      ? { x0: vueCarte[0], y0: vueCarte[1], x1: vueCarte[0] + vueCarte[2],
          y1: vueCarte[1] + vueCarte[3] } : BORNE;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const g = ctx.createLinearGradient(0, 0, 0, hauteur);
    g.addColorStop(0, "#151913"); g.addColorStop(1, "#0d100c");
    ctx.fillStyle = g; ctx.fillRect(0, 0, largeur, hauteur);
    transformerLocalDansMonde();
    ctx.lineWidth = 1 / echelle;
    for (let y = Math.floor(v.y0 / 50) * 50; y <= v.y1; y += 50) {
      ctx.strokeStyle = y % 100 === 0 ? "#273026" : "#20271f";
      ctx.beginPath(); ctx.moveTo(v.x0, y);
      for (let x = Math.floor(v.x0 / 20) * 20; x <= v.x1; x += 20)
        ctx.lineTo(x, y + Math.sin(x / 58 + y / 70) * 5);
      ctx.stroke();
    }
    for (let x = Math.floor(v.x0 / 90) * 90; x < v.x1; x += 90) {
      ctx.fillStyle = (Math.round(x / 90) & 1) ? "#161d15" : "#131a12";
      ctx.fillRect(x, v.y0, 44, v.y1 - v.y0);
    }
  }

  function tracerChemin() {
    const p = etat.chemin;
    ctx.lineCap = "round";
    for (let i = 1; i < p.length; i++) {
      const a = p[i - 1], b = p[i];
      const h = clamp(b.z / 330, 0, 1);
      ctx.lineWidth = (b.phase === "reconnaissance" ? 2.2 : 1.15) / echelle;
      ctx.strokeStyle = b.phase === "reconnaissance"
        ? `hsla(${32 + h * 165},75%,${48 + h * 15}%,.58)`
        : `hsla(${8 + h * 28},70%,${38 + h * 10}%,.52)`;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
  }

  function tracerChaleur() {
    for (const h of etat.chaleur.values()) {
      const refroidi = AMBIANTE + (h.pic - AMBIANTE)
        * (0.72 * Math.exp(-h.age / 12) + 0.28 * Math.exp(-h.age / 90));
      const chaud = clamp((refroidi - AMBIANTE) / 1300, 0, 1);
      const char = clamp(h.dose / 1.3, 0, 1);
      // Deux lectures superposées : la matière carbonisée reste, la chaleur
      // orange s'éteint. La première empêche la trace de disparaître sur ce sol
      // sombre ; la seconde montre encore la fonction de refroidissement.
      ctx.fillStyle = `rgba(91,31,17,${0.22 + 0.72 * char})`;
      ctx.beginPath(); ctx.ellipse(h.x, h.y, h.r * (1.45 + char), h.r * 0.92,
                                  0, 0, TAU); ctx.fill();
      ctx.strokeStyle = `rgba(171,66,30,${0.18 + 0.5 * char})`;
      ctx.lineWidth = 0.8 / echelle; ctx.stroke();
      ctx.fillStyle = chaud > 0.10
        ? `rgba(255,${Math.round(70 + 130 * chaud)},25,${0.12 + 0.72 * chaud})`
        : `rgba(24,13,10,${0.28 + 0.62 * char})`;
      ctx.beginPath(); ctx.ellipse(h.x, h.y, h.r * (1 + char), h.r * 0.7,
                                  0, 0, TAU); ctx.fill();
    }
    for (const p of etat.projections) {
      const a = 1 - p.age / p.vie;
      ctx.fillStyle = `rgba(255,88,28,${a * 0.8})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r * a, 0, TAU); ctx.fill();
    }
  }

  function tracerEmpreinte() {
    const q = etat.empreinte;
    if (!q || q.length < 2) return;
    ctx.save();
    ctx.fillStyle = "rgba(255,89,24,.16)";
    ctx.strokeStyle = "rgba(255,184,72,.92)";
    ctx.lineWidth = 1.4 / echelle;
    ctx.beginPath(); ctx.moveTo(q[0].gauche.x, q[0].gauche.y);
    for (let i = 1; i < q.length; i++) ctx.lineTo(q[i].gauche.x, q[i].gauche.y);
    for (let i = q.length - 1; i >= 0; i--) ctx.lineTo(q[i].droite.x, q[i].droite.y);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    // Quelques sections rendent le calcul lisible : elles sont les cordes
    // exactes des disques du jet coupés par z=0.
    ctx.strokeStyle = "rgba(255,218,141,.36)";
    ctx.lineWidth = 0.65 / echelle;
    for (let i = 0; i < q.length; i += 6) {
      ctx.beginPath(); ctx.moveTo(q[i].gauche.x, q[i].gauche.y);
      ctx.lineTo(q[i].droite.x, q[i].droite.y); ctx.stroke();
    }
    ctx.restore();
  }

  function tracerSelection() {
    if (etat.phase !== "dracarys" || !etat.selections.length) return;
    ctx.save();
    // Les cercles éteints sont les zones déjà traitées. Ils ne disent pas
    // « détruit » : ils matérialisent seulement la décote qui force le regard
    // à parcourir l'armée avant de revenir finir les survivants.
    for (const z of etat.zonesTraitees) {
      ctx.strokeStyle = "rgba(119,91,72,.55)"; ctx.fillStyle = "rgba(38,22,17,.18)";
      ctx.lineWidth = 1 / echelle; ctx.setLineDash([5 / echelle, 5 / echelle]);
      ctx.beginPath(); ctx.arc(z.x, z.y, 34, 0, TAU); ctx.fill(); ctx.stroke();
      ctx.setLineDash([]); ctx.fillStyle = "rgba(176,126,91,.72)";
      ctx.font = `700 ${11 / echelle}px ui-monospace,monospace`;
      ctx.fillText(String(z.numero), z.x - 3, z.y + 4);
    }
    // Les alternatives restent visibles comme une lecture du terrain, pas
    // comme des waypoints imposés. Seule la première est engagée.
    for (let i = 1; i < etat.candidatsCibles.length; i++) {
      const q = etat.candidatsCibles[i];
      ctx.strokeStyle = `rgba(208,174,100,${0.34 - i * 0.045})`;
      ctx.lineWidth = 0.8 / echelle;
      ctx.beginPath(); ctx.arc(q.p.x, q.p.y, 8 + i * 1.5, 0, TAU); ctx.stroke();
    }
    const c = etat.cible;
    const a = etat.cibleCap, ux = Math.cos(a), uy = Math.sin(a);
    const vx = -uy, vy = ux;
    const ax = c.x - ux * modele.couloirArriere, ay = c.y - uy * modele.couloirArriere;
    const bx = c.x + ux * modele.couloirAvant, by = c.y + uy * modele.couloirAvant;
    ctx.fillStyle = "rgba(255,154,52,.07)"; ctx.strokeStyle = "rgba(255,181,75,.72)";
    ctx.lineWidth = 1.15 / echelle; ctx.setLineDash([8 / echelle, 4 / echelle]);
    ctx.beginPath();
    ctx.moveTo(ax + vx * modele.couloirLargeur0, ay + vy * modele.couloirLargeur0);
    ctx.lineTo(bx + vx * modele.couloirLargeur1, by + vy * modele.couloirLargeur1);
    ctx.lineTo(bx - vx * modele.couloirLargeur1, by - vy * modele.couloirLargeur1);
    ctx.lineTo(ax - vx * modele.couloirLargeur0, ay - vy * modele.couloirLargeur0);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.setLineDash([]); ctx.strokeStyle = "rgba(255,215,132,.95)";
    ctx.beginPath(); ctx.arc(c.x, c.y, 13, 0, TAU);
    ctx.moveTo(c.x - 18, c.y); ctx.lineTo(c.x + 18, c.y);
    ctx.moveTo(c.x, c.y - 18); ctx.lineTo(c.x, c.y + 18); ctx.stroke();
    ctx.fillStyle = "#f2c56f"; ctx.font = `700 ${10 / echelle}px ui-monospace,monospace`;
    for (let i = 0; i < etat.cibleEtapes.length; i++) {
      const e = etat.cibleEtapes[i];
      ctx.fillStyle = "rgba(255,203,105,.22)"; ctx.beginPath();
      ctx.arc(e.x, e.y, 11, 0, TAU); ctx.fill();
      ctx.fillStyle = "#f2c56f"; ctx.fillText(String(i + 1), e.x - 3, e.y + 4);
    }
    ctx.fillStyle = "#f2c56f";
    ctx.fillText(`C${etat.selections.length} · ≈${Math.round(etat.cibleGain)} · ${etat.cibleChaines} ${estVille(etat.mode) ? "secteurs" : "masses"}`,
                 c.x + 16, c.y - 13);
    ctx.restore();
  }

  function tracerColonne() {
    const c = etat.cible;
    if (!estArmee(etat.mode)) {
      ctx.save(); ctx.translate(c.x - 18, c.y); ctx.rotate(0);
      ctx.fillStyle = "#8a7350"; ctx.fillRect(-4, -7, 8, 14);
      ctx.fillStyle = "#b53e32"; ctx.fillRect(-2.5, -18, 5, 12);
      ctx.restore();
    }
    for (const h of etat.hommes) {
      const p = localDepuisMonde(h), e = etat.exposition.get(h) || { dose: 0, index: 0 };
      const jambes = h.l1 && h.l1.jambes;
      ctx.save(); ctx.translate(p.x, p.y);
      if (auSol(h)) {
        ctx.rotate(-0.55 + ((e.index * 37) % 13) / 12);
        ctx.strokeStyle = "#24120f"; ctx.lineWidth = 2.3 / echelle;
        ctx.beginPath(); ctx.moveTo(-2.2, 0); ctx.lineTo(2.2, 0); ctx.stroke();
        ctx.fillStyle = h.etat === "mort" ? "#4b1712" : "#8d2f20";
        ctx.beginPath(); ctx.arc(0, 0, 1.2, 0, TAU); ctx.fill();
      } else {
        ctx.fillStyle = h.etat === "deroute" && h.fuiteStrategie === "regroupement" ? "#6fd3b5"
          : jambes === "fuite" || h.etat === "deroute" ? "#e7cf73"
          : jambes === "sidération" ? "#eee6d4"
          : jambes === "recul" || jambes === "dérobade" ? "#d89b58"
          : e.dose > 0.08 ? "#c84a23" : "#b6aa8d";
        ctx.beginPath(); ctx.arc(0, 0, 1.05, 0, TAU); ctx.fill();
        ctx.strokeStyle = jambes === "sidération" ? "#fff7df" : "#695f50";
        ctx.lineWidth = (jambes === "sidération" ? 1.4 : 0.7) / echelle;
        ctx.beginPath(); ctx.moveTo(-1.4, 1.8); ctx.lineTo(1.6, -1.6); ctx.stroke();
        if ((h.vit || 0) > 0.35) {
          const v = directionLocale(h.x - (h.px ?? h.x), h.y - (h.py ?? h.y));
          const vn = Math.hypot(v.x, v.y) || 1;
          ctx.strokeStyle = h.etat === "deroute" && h.fuiteStrategie === "regroupement"
            ? "rgba(111,226,191,.92)"
            : jambes === "fuite" || h.etat === "deroute"
              ? "rgba(255,224,106,.9)" : "rgba(206,190,151,.45)";
          ctx.lineWidth = 0.75 / echelle;
          ctx.beginPath(); ctx.moveTo(0, 0);
          ctx.lineTo(v.x / vn * Math.min(5, 1.2 + h.vit),
                     v.y / vn * Math.min(5, 1.2 + h.vit)); ctx.stroke();
        }
      }
      ctx.restore();
    }
    ctx.fillStyle = "#c8b893"; ctx.font = `${10 / echelle}px Georgia,serif`;
    ctx.fillText(`${estArmee(etat.mode) ? "armée" : "colonne"} — ${etat.hommes.length} soldats du moteur`,
                 c.x - 40, c.y + 24);
  }

  function tracerLoupeColonne() {
    const w = Math.min(330, largeur * 0.46), hPanel = 168;
    const x0 = 16, y0 = hauteur - hPanel - 18, grossissement = 3.15;
    const c = etat.cible;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.save();
    ctx.fillStyle = "rgba(9,12,9,.92)"; ctx.strokeStyle = "rgba(209,176,104,.55)";
    ctx.lineWidth = 1; ctx.fillRect(x0, y0, w, hPanel); ctx.strokeRect(x0 + .5, y0 + .5, w - 1, hPanel - 1);
    ctx.beginPath(); ctx.rect(x0 + 1, y0 + 26, w - 2, hPanel - 27); ctx.clip();

    // La même dose au sol, grossie autour des corps. La loupe ne recalcule
    // aucune géométrie : elle ne fait qu'agrandir les cellules déjà déposées.
    for (const q of etat.chaleur.values()) {
      const sx = x0 + w * .58 + (q.x - c.x) * grossissement;
      const sy = y0 + 92 + (q.y - c.y) * grossissement;
      if (sx < x0 || sx > x0 + w || sy < y0 + 26 || sy > y0 + hPanel) continue;
      const a = clamp(q.dose / 1.3, 0.08, 0.72);
      ctx.fillStyle = `rgba(183,55,24,${a})`;
      ctx.fillRect(sx - 3.1, sy - 3.1, 6.2, 6.2);
    }

    for (const soldat of etat.hommes) {
      const p = localDepuisMonde(soldat), e = etat.exposition.get(soldat) || { dose: 0, index: 0 };
      const sx = x0 + w * .58 + (p.x - c.x) * grossissement;
      const sy = y0 + 92 + (p.y - c.y) * grossissement;
      const jambes = soldat.l1 && soldat.l1.jambes;
      if (auSol(soldat)) {
        ctx.save(); ctx.translate(sx, sy); ctx.rotate(-.45 + ((e.index * 37) % 11) / 12);
        ctx.strokeStyle = soldat.etat === "mort" ? "#3d0f0c" : "#b0442d";
        ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-5, 0); ctx.lineTo(5, 0); ctx.stroke();
        ctx.fillStyle = "#30100d"; ctx.beginPath(); ctx.arc(0, 0, 2.5, 0, TAU); ctx.fill();
        ctx.restore(); continue;
      }
      ctx.fillStyle = soldat.etat === "deroute" && soldat.fuiteStrategie === "regroupement" ? "#79e0bf"
        : jambes === "fuite" || soldat.etat === "deroute" ? "#f0d36e"
        : jambes === "sidération" ? "#fff8e7"
        : jambes === "recul" || jambes === "dérobade" ? "#ef9a45"
        : e.dose > 0.08 ? "#d34e28" : "#c8baa0";
      ctx.beginPath(); ctx.arc(sx, sy, 3.2, 0, TAU); ctx.fill();
      const v = directionLocale(soldat.x - (soldat.px ?? soldat.x),
                                soldat.y - (soldat.py ?? soldat.y));
      const vn = Math.hypot(v.x, v.y);
      if (vn > .08 || jambes === "recul" || jambes === "dérobade" || jambes === "fuite") {
        const dx = vn > .08 ? v.x / vn : 1, dy = vn > .08 ? v.y / vn : 0;
        ctx.strokeStyle = soldat.etat === "deroute" && soldat.fuiteStrategie === "regroupement"
          ? "rgba(112,232,194,.95)" : "rgba(255,201,104,.9)"; ctx.lineWidth = 1.4;
        ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx + dx * 10, sy + dy * 10); ctx.stroke();
      }
    }
    ctx.restore();
    ctx.fillStyle = "#d8c699"; ctx.font = "700 10px ui-monospace,monospace";
    ctx.fillText("LOUPE · CORPS RÉELS ×3", x0 + 9, y0 + 17);
    ctx.fillStyle = "#9e9276"; ctx.font = "9px ui-monospace,monospace";
    ctx.fillText("vert : rejoindre les siens · jaune : partir seul · trait : vitesse", x0 + 9, y0 + hPanel - 8);
  }

  function tracerFlamme() {
    if (etat.attaque !== "souffle") return;
    const d = etat.dragon;
    const env = lisse(0, 0.01, etat.souffle)
      * (1 - lisse(modele.souffle * .84, modele.souffle, etat.souffle));
    const Lh = Math.sqrt(Math.max(1, modele.flamme ** 2 - d.z ** 2));
    const puls = 1 + 0.09 * Math.sin(etat.souffle * 19);
    ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(d.cap);
    ctx.globalCompositeOperation = "screen";
    ctx.shadowColor = `rgba(255,94,22,${0.9 * env})`;
    ctx.shadowBlur = 13 / echelle;
    const g = ctx.createLinearGradient(5, 0, Lh * puls, 0);
    g.addColorStop(0, `rgba(255,251,216,${0.9 * env})`);
    g.addColorStop(0.25, `rgba(255,220,70,${0.9 * env})`);
    g.addColorStop(0.68, `rgba(255,83,22,${0.72 * env})`);
    g.addColorStop(1, "rgba(112,24,13,0)");
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(10, -0.9); ctx.quadraticCurveTo(Lh * .55, -8.5, Lh * puls, -7);
    ctx.quadraticCurveTo(Lh * .62, 9.5, 10, 0.9); ctx.closePath(); ctx.fill();
    ctx.shadowBlur = 5 / echelle;
    ctx.fillStyle = `rgba(255,252,224,${0.72 * env})`;
    ctx.beginPath(); ctx.moveTo(10, -0.35); ctx.lineTo(Lh * .56, -2.2);
    ctx.lineTo(Lh * .72, 1.4); ctx.lineTo(10, .35); ctx.closePath(); ctx.fill();
    ctx.fillStyle = `rgba(255,255,244,${0.9 * env})`;
    ctx.beginPath(); ctx.ellipse(11.5, 0, 3.6, 1.2, 0, 0, TAU); ctx.fill();
    ctx.restore();
  }

  function tracerDragon() {
    const d = etat.dragon;
    const ombreX = d.x + d.z * 0.075, ombreY = d.y + d.z * 0.045;
    ctx.save(); ctx.translate(ombreX, ombreY); ctx.rotate(d.cap);
    ctx.fillStyle = `rgba(0,0,0,${clamp(0.42 - d.z / 900, .1, .34)})`;
    ctx.beginPath();
    ctx.ellipse(0, 0, modele.longueur * .64 + d.z / 60,
                modele.envergure * .14 + d.z / 170, 0, 0, TAU); ctx.fill();
    ctx.restore();
    ctx.strokeStyle = "rgba(215,203,169,.25)"; ctx.lineWidth = 1 / echelle;
    ctx.setLineDash([4 / echelle, 4 / echelle]);
    ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(ombreX, ombreY); ctx.stroke();
    ctx.setLineDash([]);

    ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(d.cap);
    const batt = 0.83 + 0.17 * Math.cos(etat.phaseAile);
    const demi = modele.envergure * batt / 2;
    const s = modele.longueur / 28;
    ctx.fillStyle = modele.couleur; ctx.strokeStyle = modele.trait;
    ctx.lineWidth = 0.9 / echelle;
    ctx.beginPath();
    ctx.moveTo(9 * s, 0); ctx.quadraticCurveTo(4 * s, -5 * s, -3 * s, -demi);
    ctx.quadraticCurveTo(-11 * s, -11 * s, -8 * s, -2.5 * s);
    ctx.lineTo(-17 * s, 0); ctx.lineTo(-8 * s, 2.5 * s);
    ctx.quadraticCurveTo(-11 * s, 11 * s, -3 * s, demi);
    ctx.quadraticCurveTo(4 * s, 5 * s, 9 * s, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = modele.ventre;
    ctx.beginPath(); ctx.ellipse(-1 * s, 0, 13.5 * s, 2.7 * s, 0, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-12 * s, -1.1 * s); ctx.lineTo(-21 * s, 0);
    ctx.lineTo(-12 * s, 1.1 * s); ctx.fill();
    ctx.fillStyle = "#ece1c3"; ctx.beginPath(); ctx.arc(1.5 * s, 0, 1.25 * s, 0, TAU); ctx.fill();
    ctx.fillStyle = "#15120e"; ctx.beginPath(); ctx.arc(2.1 * s, 0, .55 * s, 0, TAU); ctx.fill();
    ctx.restore();

    ctx.fillStyle = "#f0dfb8"; ctx.font = `700 ${10 / echelle}px ui-monospace,monospace`;
    ctx.fillText(`${Math.round(d.z)} m`, d.x + 15, d.y - 10);
  }

  function altimetre() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const x = largeur - 54, y0 = 72, y1 = hauteur - 48;
    ctx.strokeStyle = "#655e50"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x, y1); ctx.stroke();
    for (const m of [0, 50, 100, 200, 300]) {
      const y = y1 - (m / 340) * (y1 - y0);
      ctx.beginPath(); ctx.moveTo(x - 5, y); ctx.lineTo(x + 5, y); ctx.stroke();
      ctx.fillStyle = "#8e8779"; ctx.font = "10px ui-monospace,monospace";
      ctx.fillText(m + " m", x - 38, y - 3);
    }
    const y = y1 - clamp(etat.dragon.z / 340, 0, 1) * (y1 - y0);
    ctx.fillStyle = "#e6b855"; ctx.beginPath();
    ctx.moveTo(x - 8, y); ctx.lineTo(x + 8, y - 5); ctx.lineTo(x + 8, y + 5); ctx.fill();
  }

  function rendre() {
    if (!ctx || !etat) return;
    // Les hommes et le terrain appartiennent à la visualisation commune. Cette
    // toile transparente ne porte que les phénomènes absents de Bataille2d :
    // altitude, trajectoire, chaleur, flamme et silhouette du dragon.
    if (!estVille(etat.mode) && bataille && bataille.rafraichir) bataille.rafraichir();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, largeur, hauteur);
    transformerLocalDansMonde();
    tracerChaleur(); tracerEmpreinte(); tracerChemin(); tracerSelection();
    tracerFlamme(); tracerDragon();
    altimetre();
  }

  function mettreStats() {
    if (!etat || !stats) return;
    const d = etat.dragon;
    const ventX = 2.4, ventY = -0.8;
    const vx = Math.cos(d.cap) * d.v * Math.cos(d.pente) + ventX;
    const vy = Math.sin(d.cap) * d.v * Math.cos(d.pente) + ventY;
    const sol = Math.hypot(vx, vy);
    const rayon = Math.abs(d.rotation || 0) < 0.002 ? Infinity
      : Math.abs(d.v / d.rotation);
    if (estVille(etat.mode)) {
      const f = incendie && incendie.resume ? incendie.resume() : null;
      const coupe = etat.empreinte && etat.empreinte.length > 1
        ? { longueur:Math.hypot(etat.empreinte.at(-1).cx - etat.empreinte[0].cx,
                                etat.empreinte.at(-1).cy - etat.empreinte[0].cy),
            largeur:etat.empreinte.reduce((m, q) => Math.max(m, 2 * q.demi), 0) }
        : etat.derniereCoupe;
      stats.innerHTML = `<h3>D3 · Vhagar brûle Port-Réal</h3><dl>` +
        `<dt>dragon</dt><dd>${modele.nom} · ${modele.cavalier}</dd>` +
        `<dt>temps commun</dt><dd>${fmt(etat.t, 1)} s</dd>` +
        `<dt>altitude calculée</dt><dd>${fmt(d.z)} m</dd>` +
        `<dt>vitesse air / sol</dt><dd>${fmt(d.v, 1)} / ${fmt(sol, 1)} m/s</dd>` +
        `<dt>rayon instantané</dt><dd>${Number.isFinite(rayon) ? fmt(rayon) + " m" : "ligne droite"}</dd>` +
        `<dt>cycle de vol</dt><dd>${etat.attaque}${etat.basseAllure ? " · vol battu lent" : ""} · ${etat.passages} souffle${etat.passages > 1 ? "s" : ""} · ${etat.passagesManques} passe${etat.passagesManques > 1 ? "s" : ""} sans feu</dd>` +
        `<dt>lignes choisies</dt><dd>${etat.selections.length} · ${etat.zonesTraitees.length} secteurs traités</dd>` +
        `<dt>coupe cône-sol</dt><dd>${coupe ? fmt(coupe.longueur, 1) + " × " + fmt(coupe.largeur, 1) + " m" : "hors sol"}</dd>` +
        `<dt>allumés par Vhagar</dt><dd>${f ? f.dragonAllumes : 0}</dd>` +
        `<dt>touchés au total</dt><dd>${f ? fmt(f.allumes) + " / " + fmt(f.total) : "—"}</dd>` +
        `<dt>prise / embrasés</dt><dd>${f ? f.prise + " / " + f.embrase : "—"}</dd>` +
        `<dt>braises / brûlés</dt><dd>${f ? f.braises + " / " + f.brule : "—"}</dd>` +
        `<dt>emprise touchée</dt><dd>${f ? fmt(f.aire) + " m²" : "—"}</dd>` +
        `<dt>brandons secondaires</dt><dd>${f ? fmt(f.brandons) : "—"}</dd>` +
        `<dt>fumée rendue</dt><dd>${f ? f.panachesVisibles + " panaches agrégés" : "—"}</dd>` +
        `<dt>plus grand pas tracé</dt><dd>${fmt(etat.sautMax, 1)} m</dd></dl>`;
      if (note) note.textContent = etat.message;
      return;
    }
    if (estRangee(etat.mode)) {
      const ordinaires = etat.hommes.filter((h) => !h.tete && !h.roi && !h.capitaine);
      const bilanCamp = (camp) => {
        const xs = ordinaires.filter((h) => h.camp === camp);
        return { total:xs.length, morts:xs.filter((h) => h.etat === "mort").length,
          blesses:xs.filter((h) => h.etat === "blesse").length,
          deroute:xs.filter((h) => h.etat === "deroute").length };
      };
      const garde = bilanCamp("garde"), assaut = bilanCamp("assaut");
      const alliesTouches = ordinaires.filter((h) => h.camp === "garde" &&
        (etat.exposition.get(h) || {}).dose > 0).length;
      const ennemisTouches = ordinaires.filter((h) => h.camp === "assaut" &&
        (etat.exposition.get(h) || {}).dose > 0).length;
      const init = etat.effectifsInitiaux || { garde:0, assaut:0 };
      const us = bataille && bataille.unites ? bataille.unites() : [];
      const doctrineUnites = us.filter((u) => u.camp === "assaut" &&
        u.doctrine === "anti-dragon-ouvert");
      const doctrineActifs = doctrineUnites.reduce((n, u) => n + u.doctrineActifs, 0);
      const doctrineOntAgi = doctrineUnites.reduce((n, u) => n + u.doctrineOntAgi, 0);
      const doctrineHommes = doctrineUnites.reduce((n, u) => n + u.membres, 0);
      const mains = {};
      for (const h of ordinaires.filter((x) => x.camp === "assaut"))
        mains[h.conduit || "pas-encore"] = (mains[h.conduit || "pas-encore"] || 0) + 1;
      stats.innerHTML = `<h3>${estRangeeOuverte(etat.mode) ? "D4b" : "D4"} · C6 avec dragon contre armée double</h3><dl>` +
        `<dt>camp du dragon</dt><dd>garde · ${modele.nom} et ${modele.cavalier}</dd>` +
        `<dt>rapport initial</dt><dd>${init.garde} + dragon contre ${init.assaut}</dd>` +
        `<dt>doctrine grande armée</dt><dd>${doctrineHommes ? "ordre ouvert anti-dragon · " + doctrineActifs + " en manœuvre · " + doctrineOntAgi + " l’ont exécuté / " + doctrineHommes + " instruits" : "aucune · ligne C6 ordinaire"}</dd>` +
        `<dt>arbitrage des jambes</dt><dd>${Object.entries(mains).map(([k,v]) => k + " " + v).join(" · ")}</dd>` +
        `<dt>préparation au jugement</dt><dd>${etat.bilanRupture ? fmt((etat.bilanRupture.preparation || 0) * 100) + " % · fermeture effective " + fmt((etat.bilanRupture.fermetureEffective || 0) * 100) + " %" : "pas encore jugée"}</dd>` +
        `<dt>temps depuis l’entrée</dt><dd>${fmt(etat.t, 1)} s</dd>` +
        `<dt>altitude calculée</dt><dd>${fmt(d.z)} m</dd>` +
        `<dt>vitesse air / sol</dt><dd>${fmt(d.v, 1)} / ${fmt(sol, 1)} m/s</dd>` +
        `<dt>cycle de vol</dt><dd>${etat.attaque}${etat.basseAllure ? " · vol battu lent" : ""} · ${etat.passages} souffle${etat.passages > 1 ? "s" : ""} · ${etat.passagesManques} passe${etat.passagesManques > 1 ? "s" : ""} sans feu</dd>` +
        `<dt>garde maintenant</dt><dd>${garde.total - garde.morts - garde.blesses} debout · ${garde.deroute} en déroute</dd>` +
        `<dt>grande armée maintenant</dt><dd>${assaut.total - assaut.morts - assaut.blesses} debout · ${assaut.deroute} en déroute</dd>` +
        `<dt>pertes garde</dt><dd>${garde.blesses} blessés · ${garde.morts} morts</dd>` +
        `<dt>pertes grande armée</dt><dd>${assaut.blesses} blessés · ${assaut.morts} morts</dd>` +
        `<dt>exposés au souffle</dt><dd>${ennemisTouches} ennemis · ${alliesTouches} alliés</dd>` +
        `<dt>lignes choisies</dt><dd>${etat.selections.length} · ${etat.zonesTraitees.length} masses traitées</dd>` +
        `<dt>plus grand pas tracé</dt><dd>${fmt(etat.sautMax, 1)} m</dd></dl>`;
      if (note) note.textContent = etat.message;
      return;
    }
    let temp = AMBIANTE, longueur = 0;
    if (etat.attaque === "souffle") {
      const env = lisse(0, modele.souffle * .095, etat.souffle)
        * (1 - lisse(modele.souffle * .84, modele.souffle, etat.souffle));
      temp = temperatureJet(0, 0, env); longueur = modele.flamme * env;
    }
    const empreinte = etat.empreinte || [];
    const largeurEmpreinte = empreinte.reduce((m, q) => Math.max(m, 2 * q.demi), 0);
    const longueurEmpreinte = empreinte.length > 1
      ? Math.hypot(empreinte.at(-1).cx - empreinte[0].cx,
                   empreinte.at(-1).cy - empreinte[0].cy) : 0;
    const coupe = empreinte.length ? { longueur: longueurEmpreinte, largeur: largeurEmpreinte }
      : etat.derniereCoupe;
    const jambes = {};
    for (const h of etat.hommes) {
      if (auSol(h)) continue;
      const j = h.l1 && h.l1.jambes;
      if (j) jambes[j] = (jambes[j] || 0) + 1;
    }
    const deroutes = etat.hommes.filter((h) => h.etat === "deroute").length;
    const ontRompu = etat.hommes.filter((h) => !!h.ruptureCause).length;
    const regroupent = etat.hommes.filter((h) => h.fuiteStrategie === "regroupement").length;
    const dispersent = etat.hommes.filter((h) => h.fuiteStrategie === "dispersion").length;
    const secteursFuite = new Set(etat.hommes.filter((h) => h.etat === "deroute" &&
      Math.hypot(h.x - (h.px ?? h.x), h.y - (h.py ?? h.y)) > 0.001).map((h) => {
      const dx = h.x - (h.px ?? h.x), dy = h.y - (h.py ?? h.y);
      return Math.floor((((Math.atan2(dy, dx) + TAU) % TAU) / TAU) * 24);
    }));
    const touches = etat.hommes.filter((h) => (etat.exposition.get(h) || {}).dose > 0.03).length;
    const entames = etat.hommes.filter((h) => h.pv < h.pvMax && !auSol(h)).length;
    const perteMax = etat.hommes.reduce((m, h) => Math.max(m, h.pvMax - Math.max(0, h.pv)), 0);
    const blesses = etat.hommes.filter((h) => h.etat === "blesse").length;
    const morts = etat.hommes.filter((h) => h.etat === "mort").length;
    const dansEau = bataille && bataille.eau
      ? etat.hommes.filter((h) => bataille.eau(h.x, h.y) === true).length : null;
    const horsSol = bataille && bataille.libre
      ? etat.hommes.filter((h) => bataille.libre(h.x, h.y) !== true).length : null;
    const rentable = etat.hommes.reduce((s, h) => s + valeurCible(h), 0);
    const titre = estArmee(etat.mode) ? `${modele.epreuve} — ${modele.nom} contre armée`
      : etat.phase === "reconnaissance" ? "D1 — Reconnaissance" : "D1 — Dracarys";
    const selection = etat.selections.at(-1);
    const ecartsCibles = etat.selections.slice(1).map((s, i) =>
      Math.hypot(s.x - etat.selections[i].x, s.y - etat.selections[i].y));
    const choixHorsRessource = etat.selections.some((s) => s.cycle !== "ralliement");
    stats.innerHTML =
      `<h3>${titre}</h3>` +
      `<dl><dt>dragon</dt><dd>${modele.nom} · ${modele.cavalier}</dd>` +
      `<dt>gabarit simulé</dt><dd>${fmt(modele.masse / 1000, 1)} t · ${modele.longueur} m · ${modele.envergure} m d’envergure</dd>` +
      `<dt>temps</dt><dd>${fmt(etat.t, 1)} s</dd>` +
      `<dt>altitude calculée</dt><dd>${fmt(d.z)} m</dd>` +
      `<dt>vitesse air</dt><dd>${fmt(d.v, 1)} m/s · ${fmt(d.v * 3.6)} km/h</dd>` +
      `<dt>vitesse sol</dt><dd>${fmt(sol, 1)} m/s</dd>` +
      `<dt>verticale</dt><dd>${fmt(d.vz, 1)} m/s</dd>` +
      `<dt>inclinaison</dt><dd>${fmt(d.banque * 180 / Math.PI, 1)}°</dd>` +
      `<dt>rayon instantané</dt><dd>${Number.isFinite(rayon) ? fmt(rayon) + " m" : "ligne droite"}</dd>` +
      `<dt>cycle de vol</dt><dd>${etat.phase === "reconnaissance" ? "orbite" : etat.attaque}${etat.basseAllure ? " · vol battu lent" : ""} · ${etat.passages} passage${etat.passages > 1 ? "s" : ""} de feu</dd>` +
      `<dt>déclenchements</dt><dd>${etat.passagesOpportunistes} opportunistes · ${etat.passagesManques} passages sans feu</dd>` +
      `<dt>cible engagée</dt><dd>${selection ? "C" + selection.numero + " · ≈" + Math.round(etat.cibleGain) + " corps · " + etat.cibleChaines + " masses enchaînables" : "lecture d’ensemble"}</dd>` +
      `<dt>sélections successives</dt><dd>${etat.selections.length} · ${etat.zonesTraitees.length} segments déjà traités</dd>` +
      `<dt>changement de masse</dt><dd>${ecartsCibles.length ? fmt(Math.min(...ecartsCibles)) + " m au minimum" : "pas encore"} · ${choixHorsRessource ? "choix hors ressource" : "tous après ressource"}</dd>` +
      `<dt>valeur encore visible</dt><dd>≈${Math.round(rentable)} corps non neutralisés ou peu exposés</dd>` +
      `<dt>alternatives classées</dt><dd>${etat.candidatsCibles.length}</dd>` +
      `<dt>plus grand pas tracé</dt><dd>${fmt(etat.sautMax, 1)} m</dd>` +
      `<dt>force au battement</dt><dd>${fmt(etat.force)} kN</dd>` +
      `<dt>fréquence d'aile</dt><dd>${fmt(etat.basseAllure ? modele.battementLent : modele.battement + (d.v > modele.presse || Math.abs(d.vz) > 6 ? .09 : 0), 2)} Hz</dd>` +
      `<dt>jet visible</dt><dd>${fmt(longueur)} m</dd>` +
      `<dt>noyau</dt><dd>${temp > 400 ? fmt(temp) + " K" : "éteint"}</dd>` +
      `<dt>coupe cône-sol</dt><dd>${coupe ? fmt(coupe.longueur, 1) + " × " + fmt(coupe.largeur, 1) + " m" + (empreinte.length ? "" : " · dernière") : "hors sol"}</dd>` +
      `<dt>empreinte au sol</dt><dd>${etat.chaleur.size} cellules</dd>` +
      `<dt>sol des soldats</dt><dd>${dansEau == null ? "inconnu" : dansEau + " dans l’eau"} · ${horsSol == null ? "sol inconnu" : horsSol + " hors sol praticable"}</dd>` +
      `<dt>exposés au feu</dt><dd>${touches} / ${etat.hommes.length}</dd>` +
      `<dt>réactions maintenant</dt><dd>${jambes.fuite || 0} fuite · ${jambes.sidération || 0} sidération · ${(jambes.recul || 0) + (jambes.dérobade || 0)} écart · ${jambes.serrer || 0} resserrés</dd>` +
      `<dt>réactions vues</dt><dd>${etat.reactionsVues.fuite.size} fuite · ${etat.reactionsVues.sidération.size} sidération · ${etat.reactionsVues.recul.size + etat.reactionsVues.dérobade.size} écart · ${etat.reactionsVues.serrer.size} resserrés</dd>` +
      `<dt>rupture propagée</dt><dd>${ontRompu} / ${etat.hommes.length} · ${deroutes} courent encore</dd>` +
      `<dt>stratégies de fuite</dt><dd>${regroupent} vers les leurs · ${dispersent} seuls</dd>` +
      `<dt>éventail des caps</dt><dd>${secteursFuite.size} / 24 secteurs occupés</dd>` +
      `<dt>jugement d'unité</dt><dd>${fmt(etat.rupturePart * 100)} % rompu${etat.ruptureA == null ? "" : " dès " + fmt(etat.ruptureA, 1) + " s"}${etat.premierFeuA == null ? " · avant toute flamme" : etat.ruptureA != null && etat.ruptureA < etat.premierFeuA ? " · avant la flamme" : ""}</dd>` +
      `<dt>lésés encore debout</dt><dd>${entames}</dd>` +
      `<dt>perte maximale</dt><dd>${fmt(perteMax, 1)} PV</dd>` +
      `<dt>soldats tombés</dt><dd>${blesses} blessés · ${morts} morts</dd></dl>`;
    if (note) note.textContent = etat.message;
  }

  function animer(ts) {
    if (!marche) { boucle = 0; return; }
    const dt = Math.min(0.08, (ts - dernier) / 1000) * vitesse;
    dernier = ts; pas(dt);
    if (marche) boucle = requestAnimationFrame(animer); else boucle = 0;
  }

  function jouer(oui = !marche) {
    marche = !!oui;
    if (marche && !boucle) { dernier = performance.now(); boucle = requestAnimationFrame(animer); }
    else if (!marche && boucle) { cancelAnimationFrame(boucle); boucle = 0; }
    return marche;
  }

  function choisir(mode) {
    jouer(false); modele = modeleDuMode(mode); etat = nouvelEtat(mode);
    if (estVille(mode)) preparerVille();
    else if (estRangee(mode)) preparerRangee();
    else preparerColonne();
    enregistrer();
    rendre(); mettreStats();
  }

  function installer(options) {
    toile = options.canvas; stats = options.stats; note = options.note;
    bataille = options.bataille || window.Bataille2d || null;
    ctx = toile.getContext("2d");
    choisir("reconnaissance");
    ro = new ResizeObserver(redimensionner); ro.observe(toile);
    redimensionner();
    return api;
  }

  const api = {
    MODELES, get MODELE() { return modele; }, installer, choisir, jouer, pas, redimensionner,
    cadre: cadreScene, vue: prendreVue,
    vitesse(x) { vitesse = clamp(+x || 1, .25, 12); },
    enMarche() { return marche; },
    etat() { return etat; },
    lierIncendie(apiIncendie) { incendie = apiIncendie || null; },
    rendre,
  };
  window.DragonEpreuve = api;
})();
