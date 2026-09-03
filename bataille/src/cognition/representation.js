/**
 * 🧠 Cognition / Représentation — LA mémoire : des croyances DATÉES sur des
 * OBJETS, jamais la vérité. Deux natures de croyances :
 * - INDIVIDUS suivis (mon chef, mon ancre) : {pos, cap, ageS}
 * - CONTACTS (les corps vus a portee d armes, toute livree) : ephemeres
 * - TAS ('escouade', 'unite') : {barycentre, etendue, effectif, ageS}
 * Vieillies chaque tick, rafraîchies par les percepts. La Décision ne lit
 * QUE ça (verrou de scale). Seedée au spawn : noms, escouade, chef, unité —
 * on connaît son monde avant la bataille.
 */

/**
 * @param {Object} seed — la connaissance de départ
 * @param {number} seed.monId
 * @param {{id: number, nom: string}[]} [seed.noms] — les gens que je connais
 * @param {number[]} [seed.amisIds] — mon escouade
 * @param {number[]} [seed.uniteIds] — mon unité (chef compris)
 * @param {number|null} [seed.chefId]
 * @param {{pos: {x,y}, cap?: number}|null} [seed.chefCru] — où je SAIS que le
 *   chef se tient au départ (on rejoint son chef au rassemblement — le
 *   retrouver n'est pas une enquête) ; croyance datée comme les autres
 * @param {string|null} [seed.maLivree] — la mienne : l'étranger se VOIT
 * @param {string} [seed.posture] — agression | defense (module les poids du commandement)
 * @param {{etiquette: string, effectif: number, direction?: string, pos?: {x, y}}[]} [seed.croyancesTas] —
 *   croyances seedées : la rumeur nue (« des ennemis quelque part »), une
 *   DIRECTION (« vers l'est »), ou une POSITION (on a VU l'autre bande avant
 *   le lever de rideau — du haut du mur, depuis le bivouac). Datée ageS 0 :
 *   elle vieillit comme tout percept, et périme (fraicheurEnnemi) si on n'agit pas
 * @param {Object|null} [seed.couverture] — la carte du « où j'ai regardé »
 */
export function creerRepresentation({
  monId,
  noms = [],
  amisIds = [],
  uniteIds = [],
  chefId = null,
  chefCru = null,
  maLivree = null,
  posture = 'defense',   // de la SEMENCE : jamais mutee, donc jamais restauree
  croyancesTas = [],
  couverture = null,
}) {
  const moi = { pos: null, ageS: Infinity };
  const nomsParId = new Map(noms.map((n) => [n.id, n.nom]));
  const amis = new Set(amisIds);
  const unite = new Set(uniteIds);

  /** @type {Set<number>} — les individus que je cherche du regard */
  const suivis = new Set(chefId !== null ? [chefId] : []);
  /** @type {Map<number, {pos, cap, ageS}>} */
  const individus = new Map();
  // la position du chef est CONNUE au départ (le rassemblement d'avant
  // bataille) — croyance normale : elle vieillit, la perception la rafraîchit
  if (chefId !== null && chefId !== monId && chefCru?.pos) {
    individus.set(chefId, { pos: { ...chefCru.pos }, cap: chefCru.cap ?? 0, ageS: 0 });
  }
  /** @type {Map<number, {pos, cap, livree, ageS}>} — corps vus au contact,
   *  toute livrée ; oubliés vite (OUBLI_CONTACT_S) : c'est du présent, pas de
   *  la mémoire longue */
  const contacts = new Map();
  const OUBLI_CONTACT_S = 4;
  // LA PEUR : des PICS (un mort des miens, vu pour la premiere fois) qui
  // decroissent — le moral est une croyance, jamais un etat objectif
  let peur = 0;
  let picPeur = 0.35;
  let tauPeurS = 12;
  let mortsMiens = 0;
  // les morts SUS parmi les miens : l'attendu se décrémente par croyance
  // (« j'ai vu Paul tomber ») — jamais par la vérité du monde
  let mortsAmisVus = 0;
  let mortsUniteVus = 0;
  const mortsConnus = new Set();
  /** @type {Map<string, {barycentre, etendue, effectif, ageS}>} */
  const tas = new Map(
    croyancesTas.map((c) => [
      c.etiquette,
      // la rumeur : sans position, avec une DIRECTION (« à l'est »), ou avec
      // une POSITION (l'autre unité VUE avant le lever de rideau)
      { barycentre: c.pos ? { ...c.pos } : null, etendue: 0, effectif: c.effectif, poids: c.effectif, direction: c.direction, ageS: 0 },
    ])
  );
  /** @type {{ordre: Object, emetteur: number, ageS: number}|null} — dernier
   *  ordre ENTENDU (du texte + qui l'a dit, daté comme toute croyance ;
   *  injecté ; demain : reçu en percept 📯) */
  let ordreRecu = null;
  /** @type {{x, y}|null} — où j'ai décidé de me tenir (déposé par le rôle) */
  let posteVoulu = null;

  let enRetard = 0;
  const rattraper = () => {
    if (enRetard === 0) return;
    const dt = enRetard;
    enRetard = 0;
    moi.ageS += dt;
    for (const c of individus.values()) c.ageS += dt;
    for (const [id, c] of contacts) {
      c.ageS += dt;
      if (c.ageS > OUBLI_CONTACT_S) contacts.delete(id);
    }
    for (const t of tas.values()) t.ageS += dt;
    if (ordreRecu) ordreRecu.ageS += dt;
  };

  return {
    moi,
    monId,
    chefId,
    posture,
    couverture,
    maLivree,

    nomDe(id) {
      return nomsParId.get(id) ?? `l'inconnu #${id}`;
    },

    /** Ajoute un individu aux suivis (ex. : mon ancre de formation). */
    suivre(id) {
      if (id !== null && id !== monId) suivis.add(id);
    },

    /** Ce que la perception doit chercher/étiqueter pour moi. */
    contextePerception() {
      return { suivis: [...suivis], amisIds: amis, uniteIds: unite, maLivree };
    },

    /** Le temps passe : toutes les croyances vieillissent. @param {number} dt */
    vieillir(dt) {
      // LE VIEILLISSEMENT EST PARESSEUX : on ne parcourt pas quarante contacts
      // par homme à soixante hertz (mesuré : 18 % du temps de la colonne de
      // Gallipoli) — le retard s'accumule ici et se rattrape à la lecture,
      // c'est-à-dire au rythme des décisions et des perceptions, pas du tick
      enRetard += dt;
      peur *= Math.exp(-dt / tauPeurS); // les pics s'estompent
      couverture?.vieillir(dt);
    },

    /** Intègre une salve de percepts. @param {{x,y}} posMoi @param {Array} percepts */
    integrer(posMoi, percepts, gisantsVus = []) {
      rattraper();
      // le CHOC : chaque mort des MIENS, vu pour la premiere fois, est un pic
      for (const g of gisantsVus) {
        if (mortsConnus.has(g.id)) continue;
        mortsConnus.add(g.id);
        if (maLivree && g.livree === maLivree) {
          peur += picPeur;
          mortsMiens++;
        }
        if (amis.has(g.id)) mortsAmisVus++;
        if (unite.has(g.id)) mortsUniteVus++;
      }
      moi.pos = { x: posMoi.x, y: posMoi.y, z: posMoi.z ?? 0 }; // on se sait aussi là-haut
      moi.ageS = 0;
      let dejaUnInconnuCeTour = false;
      const tasVusCeTour = new Set();
      for (const p of percepts) {
        if (p.type === 'corpsVu' && suivis.has(p.id)) {
          individus.set(p.id, { pos: { ...p.pos }, cap: p.cap, ageS: 0 });
        } else if (p.type === 'contactVu') {
          contacts.set(p.id, { pos: { ...p.pos }, cap: p.cap, posture: p.posture, livree: p.livree, rayon: p.rayon, ageS: 0 });
        } else if (p.type === 'tasVu') {
          // tas anonyme : V1, on ne garde que le PLUS PROCHE de la salve
          // ('inconnu' — l'attention les livre tries par proximite) ;
          // la re-association multi-tas est differee
          const etiquette = p.etiquette ?? 'inconnu';
          if (etiquette === 'inconnu' && dejaUnInconnuCeTour) continue;
          if (etiquette === 'inconnu') dejaUnInconnuCeTour = true;
          // deux tas de même étiquette dans la même salve (un fragment près
          // du gros) : le plus GROS porte la croyance — un fragment ne doit
          // jamais écraser la ligne
          if (tasVusCeTour.has(etiquette) && (tas.get(etiquette)?.effectif ?? 0) >= p.effectif) continue;
          tasVusCeTour.add(etiquette);
          tas.set(etiquette, {
            lointain: p.lointain === true,
            livree: p.livree,
            barycentre: { ...p.barycentre },
            etendue: p.etendue,
            effectif: p.effectif,
            // les faits de gabarit et d'allure (la menace s'y mesure)
            poids: p.poids ?? p.effectif,
            vitesse: p.vitesse ?? 0,
            z: p.z ?? 0,
            prets: p.prets,
            fuyards: p.fuyards,
            // la forme crue (si le groupe en avait une lisible)
            nettete: p.nettete,
            formeEffectif: p.formeEffectif,
            cap: p.cap,
            largeur: p.largeur,
            profondeur: p.profondeur,
            premiereLigne: p.premiereLigne
              ? { centre: { ...p.premiereLigne.centre }, largeur: p.premiereLigne.largeur }
              : undefined,
            ageS: 0,
          });
        }
      }
    },

    /** @param {number} id @returns {{pos, cap, ageS} | undefined} */
    individuCru(id) {
      rattraper();
      return individus.get(id);
    },

    /** Regle les constantes de peur (bootstrap, depuis PARAMS). */
    reglerPeur({ picParMort, tauPeurS: tau }) {
      picPeur = picParMort;
      tauPeurS = tau;
    },

    /** LA PEUR courante (pics de récence, décroissante). Pour le moral (🧠). */
    peur() {
      return peur;
    },

    /** Combien des MIENS je sais tombés. */
    mortsVus() {
      return mortsMiens;
    },

    /**
     * Les corps crus au contact (toute livrée), ordre stable par id.
     * @returns {{id, pos, cap, livree, ageS}[]}
     */
    contactsCrus() {
      rattraper();
      return [...contacts]
        .map(([id, c]) => ({ id, ...c }))
        .sort((a, b) => a.id - b.id);
    },

    /** @param {'escouade'|'unite'|'ennemis'} etiquette */
    tasCru(etiquette) {
      rattraper();
      return tas.get(etiquette);
    },

    /**
     * L'effectif que je SAIS exister pour une étiquette (moi non compris) —
     * ce que je vois se compare à ce que je sais. @param {string} etiquette
     */
    attendu(etiquette) {
      rattraper();
      // décrémenté par les morts VUS : on ne cherche pas ceux qu'on a vus
      // tomber (ceux qu'on n'a PAS vus, si — c'est le réalisme du doute)
      if (etiquette === 'escouade') return Math.max(0, amis.size - mortsAmisVus);
      if (etiquette === 'unite') return Math.max(0, unite.size - mortsUniteVus);
      return 0;
    },

    /**
     * J'ai vérifié : cette croyance est fausse (conclusion d'un ratissage
     * bredouille, d'une piste vide…). @param {string} etiquette
     */
    infirmerTas(etiquette) {
      tas.delete(etiquette);
    },

    // ── MON POSTE — une croyance sur moi-même, déposée par le rôle (le même
    // esprit : le rôle n'émet que des paroles vers les AUTRES, mais il sait
    // où il a décidé de se tenir) ; consommée par la compétence de formation
    /** @param {{x, y}|null} pos */
    retenirPoste(pos) {
      posteVoulu = pos ? { x: pos.x, y: pos.y } : null;
    },
    /** @returns {{x, y}|null} */
    poste() {
      return posteVoulu;
    },

    // ── Ordre entendu (ÉCHAFAUDAGE : injecté en direct ; demain, percept 📯) ──
    /** @param {{ordre: Object, emetteur: number}|null} recu */
    recevoirOrdre(recu) {
      ordreRecu = recu ? { ...recu, ageS: 0 } : null;
    },
    /** @returns {{ordre: Object, emetteur: number}|null} */
    ordre() {
      rattraper();
      return ordreRecu;
    },

    // ── SE RELIRE (docs/sauvegarde.md) ────────────────────────────────────
    //
    // Ce qui sort ici est L'ACQUIS : ce qu'aucune semence ne sait redonner.
    // La semence elle-meme (noms, amis, unite, chefId, maLivree) reste passee
    // a `creerRepresentation` au chargement, comme au spawn.
    //
    // `contacts` NE SORT PAS : oublies en 4 s, c'est du present et non de la
    // memoire ; ils se refont a la premiere perception. Les faire vivre une
    // sauvegarde donnerait a un homme rechargé quatre secondes de vue qu'il
    // n'a pas eues.

    /**
     * @param {{couvertureDepuis?: number}} [opts] — decimation de la carte du
     *   regard (voir couverture.etat)
     * @returns {Object} — donnee plate, sans reference vivante
     */
    etat({ couvertureDepuis } = {}) {
      rattraper();
      return {
        moi: { pos: moi.pos ? { ...moi.pos } : null, ageS: moi.ageS },
        suivis: [...suivis],
        individus: [...individus].map(([id, c]) => [id, { pos: { ...c.pos }, cap: c.cap, ageS: c.ageS }]),
        tas: [...tas].map(([e, t]) => [e, { ...t, barycentre: t.barycentre ? { ...t.barycentre } : null }]),
        peur, picPeur, tauPeurS,
        mortsMiens, mortsAmisVus, mortsUniteVus,
        mortsConnus: [...mortsConnus],
        ordreRecu: ordreRecu ? { ...ordreRecu } : null,
        posteVoulu: posteVoulu ? { ...posteVoulu } : null,
        couverture: couverture?.etat?.({ depuis: couvertureDepuis }) ?? null,
      };
    },

    /** Remplace l'acquis. Ce qui n'a pas de champ ici n'existe pas au chargement. */
    restaurer(d = {}) {
      moi.pos = d.moi?.pos ? { ...d.moi.pos } : null;
      moi.ageS = d.moi?.ageS ?? Infinity;
      suivis.clear();
      for (const id of d.suivis ?? []) suivis.add(id);
      individus.clear();
      for (const [id, c] of d.individus ?? []) individus.set(Number(id), { ...c, pos: { ...c.pos } });
      contacts.clear();                     // du present : il se refera tout seul
      tas.clear();
      for (const [e, t] of d.tas ?? []) tas.set(e, { ...t, barycentre: t.barycentre ? { ...t.barycentre } : null });
      peur = d.peur ?? 0;
      if (d.picPeur !== undefined) picPeur = d.picPeur;
      if (d.tauPeurS !== undefined) tauPeurS = d.tauPeurS;
      mortsMiens = d.mortsMiens ?? 0;
      mortsAmisVus = d.mortsAmisVus ?? 0;
      mortsUniteVus = d.mortsUniteVus ?? 0;
      mortsConnus.clear();
      for (const id of d.mortsConnus ?? []) mortsConnus.add(Number(id));
      ordreRecu = d.ordreRecu ? { ...d.ordreRecu } : null;
      posteVoulu = d.posteVoulu ? { ...d.posteVoulu } : null;
      if (d.couverture) couverture?.restaurer?.(d.couverture);
    },

    /** Pour les vues debug (🖥️ calques). */
    snapshotDebug() {
      rattraper();
      return {
        moi,
        individus: [...individus].map(([id, c]) => ({ id, nom: nomsParId.get(id), ...c })),
        contacts: [...contacts].map(([id, c]) => ({ id, nom: nomsParId.get(id), ...c })),
        tas: [...tas].map(([etiquette, t]) => ({ etiquette, ...t })),
      };
    },
  };
}
