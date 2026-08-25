// scenarios.js — des questions reproductibles posées au moteur.
//
// CE QUE ÇA RÉSOUT. On ne débogue pas un comportement sur une bataille entière :
// on veut une question à la fois, une condition de passage écrite d'avance, et
// de quoi la rejouer à l'identique après chaque retouche.
//
// ═══ D'OÙ VIENNENT LES CONDITIONS DE PASSAGE ════════════════════════════════
// De `docs/recherche/dynamiques-du-combat-medieval.md`, et de nulle part
// ailleurs. Aucun seuil de ce fichier n'est un réglage de confort : chacun cite
// la section qui le porte. C'est ce qui rend une épreuve DISCUTABLE — on peut
// contester la source, on ne peut pas contester qu'on l'a suivie.
//
// Les trois faits qui commandent toute la série, et qui sont incompatibles avec
// l'image du duel continu :
//   • une bataille dure des HEURES (Végèce : 2–3 h ; Towton : ~10 h) ;
//   • le vainqueur perd TRÈS PEU (5–10 %) ;
//   • un homme en armure ne tient ~90 SECONDES à pleine intensité (étude 2024).
// Donc : pendant l'immense majorité d'une bataille, l'immense majorité des
// hommes ne frappe personne et n'est frappée par personne.
//
// ═══ LA RÈGLE DE FORME ══════════════════════════════════════════════════════
// LE MÊME OBJET SERT LA PAGE ET LE BANC HEADLESS — même règle que `sac.js`
// impose à la simulation : deux implémentations d'une même épreuve sont deux
// épreuves. De la DONNÉE, plus `avant(B)` qui ne touche qu'à la troupe, plus
// des sondes qui lisent un relevé. Aucun `document`, aucun accès à l'écran.
//
// ⚠ CE QU'UN SCÉNARIO NE PEUT PAS FAIRE. Tant que `dresser()` n'est pas ouvert,
// on ne peut ni créer un homme, ni ouvrir une porte, ni poser un décor : on part
// de la nuit de la Gadoue et on la DÉFORME. Les épreuves ci-dessous sont
// écrites dans cette limite, et les numéros élevés la touchent du doigt.
"use strict";
(function (racine) {

  // Un champ peut être libre à 85 % et pourtant coupé en deux par six mètres
  // de courtine. Une moyenne de cases ne voit pas cette différence ; la
  // topologie, oui. Ce relevé sert au choix du terrain comme à la sonde :
  // passage d'un bord longitudinal à l'autre, puis taille du plus grand
  // obstacle connecté dans les deux axes du champ.
  function analyserCouloir(B, centre, ax, ay, longueur, largeur, pas) {
    const L=longueur||164,W=largeur||108,P=pas||4,tx=-ay,ty=ax;
    const nx=Math.floor(L/P)+1,ny=Math.floor(W/P)+1,n=nx*ny;
    const libre=new Uint8Array(n),vu=new Uint8Array(n),q=new Int32Array(n);
    const point=(i,j)=>({x:centre.x+ax*(-L/2+i*P)+tx*(-W/2+j*P),
                         y:centre.y+ay*(-L/2+i*P)+ty*(-W/2+j*P)});
    let libres=0,a=0,z=0;
    for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){
      const k=j*nx+i,p=point(i,j);
      if(B.libre(p.x,p.y)===true){libre[k]=1;libres++;if(i===0){vu[k]=1;q[z++]=k;}}
    }
    let traversable=false;
    while(a<z){
      const k=q[a++],i=k%nx,j=(k/nx)|0;if(i===nx-1)traversable=true;
      for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1]]){
        const ii=i+di,jj=j+dj;if(ii<0||jj<0||ii>=nx||jj>=ny)continue;
        const u=jj*nx+ii;if(libre[u]&&!vu[u]){vu[u]=1;q[z++]=u;}
      }
    }
    const fait=new Uint8Array(n);let obstacleMax=0,barriere=false;
    for(let depart=0;depart<n;depart++){
      if(libre[depart]||fait[depart])continue;
      a=0;z=0;q[z++]=depart;fait[depart]=1;
      let i0=depart%nx,i1=i0,j0=(depart/nx)|0,j1=j0;
      while(a<z){
        const k=q[a++],i=k%nx,j=(k/nx)|0;
        i0=Math.min(i0,i);i1=Math.max(i1,i);j0=Math.min(j0,j);j1=Math.max(j1,j);
        for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){
          if(!di&&!dj)continue;const ii=i+di,jj=j+dj;
          if(ii<0||jj<0||ii>=nx||jj>=ny)continue;
          const u=jj*nx+ii;if(!libre[u]&&!fait[u]){fait[u]=1;q[z++]=u;}
        }
      }
      const spanP=(i1-i0+1)*P,spanL=(j1-j0+1)*P;
      obstacleMax=Math.max(obstacleMax,spanP/L,spanL/W);
      if((j0===0&&j1===ny-1)||(i0===0&&i1===nx-1)||
         spanP>=L*.50||spanL>=W*.50)barriere=true;
    }
    return { traversable,barriere,partLibre:libres/n,
      obstacleMax:+obstacleMax.toFixed(2),longueur:L,largeur:W,pas:P };
  }

  // ── LE RELEVÉ ─────────────────────────────────────────────────────────────
  // Calculé une fois par bond, et c'est la SEULE chose que les sondes lisent :
  // deux sondes qui interrogeraient le moteur séparément liraient deux états.
  function relever(B) {
    const e = B.etat();
    if (!e || e.dressee === false) return null;
    const t = B.troupe();
    const unites = B.unites ? B.unites() : [];
    const evenements = B.faits ? B.faits().slice() : [];
    const mur = {}, jambes = {}, bras = {}, etats = {}, parCorps = {}, parCamp = {}, parType = {};
    let dansLeMur = 0, vivants = 0, inconnu = 0, auContact = 0, frappent = 0;
    let coupsTentes = 0, coupsPortes = 0;
    for (const h of t) {
      const camp = parCamp[h.camp] || (parCamp[h.camp] =
        { total: 0, vivants: 0, morts: 0, blesses: 0, deroute: 0 });
      camp.total++;
      if (h.etat === "mort") camp.morts++;
      else if (h.etat === "blesse") camp.blesses++;
      else { camp.vivants++; if (h.etat === "deroute") camp.deroute++; }
      coupsTentes += h.coupsTentes || 0;
      coupsPortes += h.coupsPortes || 0;
      if (h.typeTroupe) {
        const y = parType[h.typeTroupe] || (parType[h.typeTroupe] =
          { total:0, vivants:0, morts:0, blesses:0, coups:0, montes:0 });
        y.total++; y.coups += h.coupsTentes || 0;
        if (h.montureCombat) y.montes++;
        if (h.etat === "mort") y.morts++;
        else if (h.etat === "blesse") y.blesses++;
        else y.vivants++;
      }
      if (h.etat === "mort") continue;
      vivants++;
      etats[h.etat] = (etats[h.etat] || 0) + 1;
      if (h.corps) {
        const c = parCorps[h.corps] || (parCorps[h.corps] = { vivants: 0, fuite: 0 });
        c.vivants++;
        if (h.etat === "deroute") c.fuite++;
      }
      if (h.enMesure) auContact++;
      if (e.temps - (h.dernierCoup == null ? -Infinity : h.dernierCoup) <= 5) frappent++;
      const libre = B.libre(h.x, h.y);
      if (libre === null) inconnu++;
      else if (!libre) { dansLeMur++; mur[h.etat] = (mur[h.etat] || 0) + 1; }
      if (h.l1) {
        if (h.l1.jambes) jambes[h.l1.jambes] = (jambes[h.l1.jambes] || 0) + 1;
        if (h.l1.bras) {
          bras[h.l1.bras] = (bras[h.l1.bras] || 0) + 1;
        }
      }
    }
    // Géométrie neutre de bataille rangée : elle ne sait rien d'un flanc, d'une
    // réserve ou d'une tactique. Elle décrit seulement les deux masses selon
    // l'axe qui joint leurs centres — précisément ce dont les futurs détecteurs
    // devront partir avant de prétendre qu'un général a « vu » quelque chose.
    const actifs = t.filter((h) => h.etat !== "mort" && h.etat !== "blesse" &&
      !h.hors && !h.tete && (h.camp === "assaut" || h.camp === "garde"));
    const centres = {};
    for (const camp of ["assaut", "garde"]) {
      const xs = actifs.filter((h) => h.camp === camp);
      if (xs.length) centres[camp] = {
        x: xs.reduce((n, h) => n + h.x, 0) / xs.length,
        y: xs.reduce((n, h) => n + h.y, 0) / xs.length,
      };
    }
    let geometrie = null;
    if (centres.assaut && centres.garde) {
      let ax = centres.garde.x - centres.assaut.x;
      let ay = centres.garde.y - centres.assaut.y;
      const separation = Math.hypot(ax, ay) || 1; ax /= separation; ay /= separation;
      const tx = -ay, ty = ax;
      const quantile = (a, q) => {
        if (!a.length) return 0;
        const s = a.slice().sort((x, y) => x - y);
        return s[Math.max(0, Math.min(s.length - 1, Math.floor((s.length - 1) * q)))];
      };
      const camps = {};
      for (const camp of ["assaut", "garde"]) {
        const xs = actifs.filter((h) => h.camp === camp), sens = camp === "assaut" ? 1 : -1;
        const lateraux = xs.map((h) => h.x * tx + h.y * ty);
        const profonds = xs.map((h) => h.x * ax + h.y * ay);
        const face = xs.reduce((n, h) => n + ((h.fx || 0) * ax + (h.fy || 0) * ay) * sens, 0) /
          (xs.length || 1);
        camps[camp] = {
          centre: centres[camp],
          frontageP90: quantile(lateraux, .95) - quantile(lateraux, .05),
          profondeurP90: quantile(profonds, .95) - quantile(profonds, .05),
          faceAdversaire: face,
        };
      }
      geometrie = { separation, axe:{ x:ax, y:ay }, camps,
        terrain:analyserCouloir(B,
          {x:(centres.assaut.x+centres.garde.x)/2,
           y:(centres.assaut.y+centres.garde.y)/2},ax,ay,
          Math.max(100,separation+24),108,4) };
    }
    const erreursAppartenance = t.filter((h) => h.camp === "assaut" && !h.tete &&
      !h.hors && h.formation >= 0).filter((h) => {
        const u = unites[h.formation];
        return !u || u.id !== "assaut:" + h.escouade;
      }).map((h) => h.debugId);
    const ciblesATraversMur = t.filter((h) => h.cible && h.etat !== "mort" &&
      h.etat !== "blesse" && h.etat !== "prisonnier" &&
      !((h.interieur == null && h.cible.interieur == null) ||
        (h.interieur != null && h.interieur === h.cible.interieur)))
      .map((h) => h.debugId);
    return {
      temps: e.temps, vivants, dansLeMur, inconnu, auContact, frappent,
      partMur: vivants ? dansLeMur / vivants : 0,
      partContact: vivants ? auContact / vivants : 0,
      partFrappent: vivants ? frappent / vivants : 0,
      mur, jambes, bras, etats, parCorps, parCamp, parType, geometrie,
      coupsTentes, coupsPortes,
      bouts: e.dynamique ? e.dynamique.bouts : 0,
      hommesMultiBouts: e.dynamique ? e.dynamique.hommesMultiBouts : 0,
      boutMedian: e.dynamique ? e.dynamique.boutMedian : 0,
      boutP90: e.dynamique ? e.dynamique.boutP90 : 0,
      sangFroidMoyen: e.dynamique ? e.dynamique.sangFroidMoyen : 1,
      expositionMoyenne: e.dynamique ? e.dynamique.expositionMoyenne : 0,
      chargeNerveuseMoyenne: e.dynamique ? e.dynamique.chargeNerveuseMoyenne : 0,
      sortieFermee: e.dynamique ? e.dynamique.sortieFermee : 0,
      presseForte: e.dynamique ? e.dynamique.presseForte : 0,
      morts: e.morts, blesses: e.blesses, fuyards: e.fuyards,
      rallies: e.rallies || 0, verrou: e.verrou, faits: e.faits,
      // Une épreuve de commandement doit lire la chaîne elle-même, pas
      // inférer son fonctionnement au déplacement moyen de 2 550 corps.
      unites, evenements, erreursAppartenance,
      echelons: B.echelons ? B.echelons() : [],
      ordreDeBataille: B.ordreDeBataille ? B.ordreDeBataille() : null,
      ratissages: B.rapportsRatissage ? B.rapportsRatissage() : [],
      commandements: B.rapportsCommandement ? B.rapportsCommandement() : [],
      ciblesATraversMur,
      chefsSuperieurs: t.filter((h) => h.camp === "assaut" && h.tete &&
        h.etat !== "mort" && h.etat !== "blesse").map((h) => ({
          id:h.debugId, nom:h.nom || null, x:h.x, y:h.y, etat:h.etat,
        })),
      routesAStar: unites.reduce((n, u) => n + (u.calculsAStar || 0), 0),
      cohesionMoyenne: unites.length
        ? unites.reduce((n, u) => n + (u.cohesion || 0), 0) / unites.length : 0,
    };
  }

  // ── de quoi écrire un `avant` sans connaître le moteur ────────────────────
  const des = (B, f) => B.troupe().filter(f);
  const duCorps = (id) => (h) => h.corps === id && !h.tete;
  const duCamp = (c) => (h) => h.camp === c && !h.tete && !h.roi && !h.hors;
  const entamer = (h, part) => { h.pv = Math.max(2, Math.round((h.pvMax || 25) * part)); };

  // Sur toute la série : le pic d'une grandeur, et sa valeur de fin.
  const pic = (suite, f) => suite.reduce((m, r) => Math.max(m, f(r) || 0), 0);
  const jamais = (suite, f) => !suite.some((r) => f(r));

  const uniteQui = (r, f) => r && (r.unites || []).find(f);
  const unitesQui = (r, f) => r ? (r.unites || []).filter(f) : [];
  const distanceChef = (suite, f) => {
    const a = uniteQui(suite[0], f), b = uniteQui(suite[suite.length - 1], f);
    return a && b && a.x != null && b.x != null ? Math.hypot(b.x - a.x, b.y - a.y) : 0;
  };
  const membresDes = (B, f) => {
    const us = B.unites(), ids = new Set(us.filter(f).map((u) => u.id));
    const ns = new Set(us.map((u, i) => ids.has(u.id) ? i : -1).filter((i) => i >= 0));
    return B.troupe().filter((h) => ns.has(h.formation));
  };

  // ═══ LES QUESTIONS DE CONDUITE ═══════════════════════════════════════════
  // Celles-ci viennent avant les mesures historiques parce qu'elles répondent
  // à des questions que l'on peut réellement poser devant la carte : qui a
  // reçu quoi, qui mène, qui suit, et par quel homme la nouvelle voyage.
  const COMMANDES = [
    {
      n: "A0", id: "armee-aegon-complete", famille: "Forces de référence",
      nom: "Toute l’armée d’Aegon",
      question: "Que contient réellement l’ordre de bataille complet, avant toute déformation d’épreuve ?",
      quoi: "Les cinq corps d’assaut sont dressés à leur effectif plein devant leurs portes : " +
            "Cole, Vantre, Cranche, Cantel et Petit Wend. Les chefs de corps, Aegon et son " +
            "entourage restent des personnes distinctes de ces 1 700 combattants.",
      regarder: "Dépliez les corps sur la carte, survolez leurs chefs et vérifiez que les " +
                "vintaines et les ailes restent attribuées à leur propre chaîne.",
      manipulation: "Aucune tactique ni téléportation n’est ajoutée : cette épreuve ne fait que " +
                    "convoquer l’ordre de bataille canonique du moteur à l’échelle 1.",
      forces: "1 700 combattants d’Aegon dans cinq corps, cinq chefs de corps, Aegon et son escorte ; " +
              "le Guet conserve ses postes dans la ville.",
      terrain: "Les quatre approches de Port-Réal et les postes du Guet, sur le plan réel.",
      passe: "Les cinq corps doivent être présents à leur effectif déclaré, sans homme perdu par " +
             "l’échelle ou attribué au mauvais corps.",
      echelle: 1, duree: 0,
      focus: (B) => B.troupe().filter((h) => h.camp === "assaut"),
      sondes: [
        { dit: "les cinq corps d’Aegon sont présents au complet", attendu: "1 700 / 1 700",
          tenu: (fin) => {
            const o=fin&&fin.ordreDeBataille;
            return !!o && o.assaut.length===5 && o.assaut.every((c)=>c.hommes===c.sur);
          },
          mesure: (fin) => {
            const xs=fin&&fin.ordreDeBataille ? fin.ordreDeBataille.assaut : [];
            return xs.reduce((n,c)=>n+c.hommes,0)+" / "+xs.reduce((n,c)=>n+c.sur,0);
          } },
        { dit: "chaque corps a sa propre tête", attendu: "5 chefs de corps",
          tenu: (fin) => (fin&&fin.chefsSuperieurs||[]).length===5,
          mesure: (fin) => (fin&&fin.chefsSuperieurs||[]).length+" chef(s)" },
      ],
    },
    {
      n: "C1", id: "ordre-unite", famille: "Conduire les troupes",
      nom: "Une vintaine reçoit un ordre de marche",
      question: "L'ordre appartient-il à la vintaine, ou chaque homme se choisit-il un chemin ?",
      quoi: "Une vintaine du Guet quitte son poste pour un autre. Le chef ouvre " +
            "la route ; les autres gardent leur appartenance et règlent leur pas sur lui.",
      regarder: "Pointez le chef puis deux hommes derrière lui : tous doivent citer la même " +
                "phrase, une seule route A*, et des raisons individuelles de rattraper ou attendre.",
      manipulation: "Un ordre littéral neuf est donné à une seule vintaine de défense.",
      forces: "Une vintaine du Guet, isolée par la caméra mais pas retirée du monde.",
      terrain: "D'un poste de porte vers l'anneau du Donjon Rouge.",
      passe: "Une seule unité absorbe l'ordre, une seule route est calculée, le chef avance et " +
             "au moins 70 % des siens restent à douze mètres.",
      echelle: 0.05, duree: 20,
      avant: (B) => {
        const us = B.unites();
        const source = us.find((u) => u.camp === "garde" && u.parent && u.parent !== "poste:donjon");
        const cibleN = us.findIndex((u) => u.id === "garde:donjon:0");
        const chefCible = B.troupe().find((h) => h.formation === cibleN && h.chefFormation);
        if (!source || !chefCible) return;
        B.ordonnerFormation(source.id,
          { id: "epreuve:ordre-unite", nom: "le poste voisin", x: chefCible.x, y: chefCible.y },
          { texte: "Vingtaine, au poste voisin. Restez ensemble." });
      },
      focus: (B) => membresDes(B, (u) => u.destination === "le poste voisin"),
      sondes: [
        { dit: "une seule vintaine reçoit l'ordre", attendu: "1 unité",
          tenu: (fin) => unitesQui(fin, (u) => u.destination === "le poste voisin").length === 1,
          mesure: (fin) => unitesQui(fin, (u) => u.destination === "le poste voisin").length + " unité(s)" },
        { dit: "les mots donnés sont encore ceux que les hommes portent",
          attendu: "phrase intacte",
          tenu: (fin) => {
            const u = uniteQui(fin, (x) => x.destination === "le poste voisin");
            return !!u && u.ordreLitteral === "Vingtaine, au poste voisin. Restez ensemble.";
          },
          mesure: (fin) => (uniteQui(fin, (x) => x.destination === "le poste voisin") || {}).ordreLitteral || "aucun ordre" },
        { dit: "le chemin n'est calculé qu'une fois", attendu: "1 A*",
          tenu: (fin) => {
            const u = uniteQui(fin, (x) => x.destination === "le poste voisin"); return !!u && u.calculsAStar === 1;
          },
          mesure: (fin) => ((uniteQui(fin, (x) => x.destination === "le poste voisin") || {}).calculsAStar || 0) + " A*" },
        { dit: "le chef conduit réellement le départ", attendu: "> 10 m",
          tenu: (fin, s) => distanceChef(s, (u) => u.destination === "le poste voisin") > 10,
          mesure: (fin, s) => distanceChef(s, (u) => u.destination === "le poste voisin").toFixed(1) + " m" },
        { dit: "la vintaine reste groupée", attendu: "≥ 70 %",
          tenu: (fin) => {
            const u = uniteQui(fin, (x) => x.destination === "le poste voisin"); return !!u && u.cohesion >= .70;
          },
          mesure: (fin) => Math.round(100 * ((uniteQui(fin, (x) => x.destination === "le poste voisin") || {}).cohesion || 0)) + " %" },
      ],
    },
    {
      n: "C2", id: "croisement-amis", famille: "Conduire les troupes",
      nom: "Deux vintaines amies se croisent",
      question: "Quand deux groupes se traversent, chacun sait-il encore qui sont les siens ?",
      quoi: "Deux vintaines du même poste échangent leurs places. Elles partagent la rue, " +
            "mais ni leurs hommes, ni leurs chefs, ni leurs ordres.",
      regarder: "Au croisement, pointez des hommes mêlés géométriquement : leur unité et leur " +
                "ordre doivent rester différents.",
      manipulation: "Deux ordres simultanés et opposés, donnés à deux unités sœurs.",
      forces: "Deux vintaines du Guet appartenant au même poste.",
      terrain: "La rue de leur poste, sans téléportation vers un terrain abstrait.",
      passe: "Les deux chefs avancent, deux routes seulement sont payées et chaque unité " +
             "conserve au moins 70 % de cohésion.",
      // Trente secondes : les groupes partent compacts mais doivent se céder
      // physiquement une rue étroite. Douze secondes ne mesuraient que le
      // bouchon initial, avant que le second chef ait franchi deux mètres.
      echelle: 0.25, duree: 30,
      avant: (B) => {
        const us = B.unites();
        const parents = us.filter((u) => u.camp === "garde").reduce((m, u) =>
          ((m[u.parent] || (m[u.parent] = [])).push(u), m), {});
        // La première paire du registre peut être presque superposée : elle
        // « échange » alors deux places distantes d'un mètre et ne teste aucun
        // croisement. On prend les deux têtes sœurs les plus éloignées. Ce
        // n'est pas une chorégraphie ajoutée au moteur, seulement la sélection
        // d'un cas où l'épreuve annoncée a réellement lieu.
        const troupe = B.troupe();
        let paire = null, chefs = null, separation = -1;
        for (const fratrie of Object.values(parents)) {
          // Un croisement ne peut juger la conservation d'une formation que
          // si les deux unités en ont une au départ. Le Donjon contient aussi
          // des unités de garde déjà dispersées sur ses ouvrages : elles sont
          // légitimes dans le monde, mais ne répondent pas à cette question-ci.
          const groupe = fratrie.filter((u) => u.cohesion >= .7);
          for (let i = 0; i < groupe.length; i++) for (let j = i + 1; j < groupe.length; j++) {
            const na = us.findIndex((u) => u.id === groupe[i].id);
            const nb = us.findIndex((u) => u.id === groupe[j].id);
            const a = troupe.find((h) => h.formation === na && h.chefFormation);
            const b = troupe.find((h) => h.formation === nb && h.chefFormation);
            if (!a || !b) continue;
            const d = Math.hypot(b.x - a.x, b.y - a.y);
            if (d > separation) { separation = d; paire = [groupe[i], groupe[j]]; chefs = [a, b]; }
          }
        }
        if (!paire || !chefs) return;
        const [a, b] = chefs;
        B.ordonnerFormation(paire[0].id, { id: "epreuve:croisement:b", nom: "la place de B", x: b.x, y: b.y },
          { texte: "Première vintaine, gagnez la place d'en face." });
        B.ordonnerFormation(paire[1].id, { id: "epreuve:croisement:a", nom: "la place de A", x: a.x, y: a.y },
          { texte: "Seconde vintaine, gagnez la place d'en face." });
      },
      focus: (B) => membresDes(B, (u) => /^la place de [AB]$/.test(u.destination || "")),
      sondes: [
        { dit: "deux unités distinctes portent les deux ordres", attendu: "2 unités",
          tenu: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || "")).length === 2,
          mesure: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || "")).length + " unité(s)" },
        { dit: "les deux chefs ont quitté leur place", attendu: "> 2 m chacun",
          tenu: (fin, s) => ["la place de A", "la place de B"].every((d) =>
            distanceChef(s, (u) => u.destination === d) > 2),
          mesure: (fin, s) => ["la place de A", "la place de B"].map((d) =>
            distanceChef(s, (u) => u.destination === d).toFixed(1) + " m").join(" · ") },
        { dit: "il n'existe qu'une route par vintaine", attendu: "2 A*",
          tenu: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || ""))
            .reduce((n, u) => n + u.calculsAStar, 0) === 2,
          mesure: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || ""))
            .reduce((n, u) => n + u.calculsAStar, 0) + " A*" },
        { dit: "les deux groupes ressortent encore cohérents", attendu: "≥ 70 % chacun",
          tenu: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || ""))
            .every((u) => u.cohesion >= .70),
          mesure: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || ""))
            .map((u) => Math.round(u.cohesion * 100) + " %").join(" · ") },
        { dit: "aucune vintaine n'a absorbé les hommes de l'autre", attendu: "effectifs inchangés",
          tenu: (fin, s) => {
            const a = unitesQui(s[0], (u) => /^la place de [AB]$/.test(u.destination || ""));
            const b = unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || ""));
            return a.length === 2 && b.length === 2 && a.every((u) =>
              b.some((v) => v.id === u.id && v.membres === u.membres));
          },
          mesure: (fin) => unitesQui(fin, (u) => /^la place de [AB]$/.test(u.destination || ""))
            .map((u) => u.membres + " hommes").join(" · ") },
      ],
    },
    (() => {
      let ancienChef = null;
      return {
        n: "C3", id: "succession", famille: "Conduire les troupes",
        nom: "Le chef tombe pendant l'ordre",
        question: "L'unité perd-elle son but avec son chef ?",
        quoi: "Le chef d'une vintaine est blessé au moment du départ. Les hommes doivent " +
              "subir un délai réel, reconnaître un successeur, puis reprendre le même ordre.",
        regarder: "La bulle doit montrer l'absence de chef puis sa reprise ; aucun homme ne " +
                  "doit s'inventer une destination personnelle.",
        manipulation: "Le chef est blessé juste avant qu'un ordre de marche soit donné.",
        forces: "Une vintaine du Guet comptant au moins trois hommes debout.",
        terrain: "Entre deux postes existants.",
        passe: "Un autre chef reprend l'unité après le délai, sans recalculer le trajet par homme.",
        echelle: 0.05, duree: 12,
        avant: (B) => {
          const us = B.unites();
          const source = us.find((u) => u.camp === "garde" && u.parent !== "poste:donjon" && u.debout >= 3);
          const n = us.findIndex((u) => u.id === (source && source.id));
          const chef = B.troupe().find((h) => h.formation === n && h.chefFormation);
          const but = B.troupe().find((h) => h.chefFormation && h.formation !== n &&
            B.unites()[h.formation] && B.unites()[h.formation].camp === "garde");
          if (!source || !chef || !but) return;
          ancienChef = chef.debugId; chef.etat = "blesse";
          B.ordonnerFormation(source.id,
            { id: "epreuve:succession", nom: "le poste après la chute", x: but.x, y: but.y },
            { texte: "Même sans moi, conduisez la vintaine au poste voisin." });
        },
        focus: (B) => membresDes(B, (u) => u.destination === "le poste après la chute"),
        sondes: [
          { dit: "un autre homme a repris la tête", attendu: "nouveau chef",
            tenu: (fin) => {
              const u = uniteQui(fin, (x) => x.destination === "le poste après la chute");
              return !!u && !!u.chefDebugId && u.chefDebugId !== ancienChef;
            },
            mesure: (fin) => {
              const u = uniteQui(fin, (x) => x.destination === "le poste après la chute");
              return u && u.chef ? u.chef : "aucun chef";
            } },
          { dit: "le successeur reprend le même ordre", attendu: "phrase intacte",
            tenu: (fin) => {
              const u = uniteQui(fin, (x) => x.destination === "le poste après la chute");
              return !!u && u.ordreLitteral === "Même sans moi, conduisez la vintaine au poste voisin.";
            },
            mesure: (fin) => (uniteQui(fin, (x) => x.destination === "le poste après la chute") || {}).ordreLitteral || "ordre perdu" },
          { dit: "la reprise conserve une route mutualisée", attendu: "1 A*",
            tenu: (fin) => {
              const u = uniteQui(fin, (x) => x.destination === "le poste après la chute"); return !!u && u.calculsAStar === 1;
            },
            mesure: (fin) => ((uniteQui(fin, (x) => x.destination === "le poste après la chute") || {}).calculsAStar || 0) + " A*" },
        ],
      };
    })(),
    {
      n: "C4", id: "messagers", famille: "Conduire les troupes",
      nom: "Un coureur retrouve une unité qui avance",
      question: "Le messager vise-t-il une vieille coordonnée, ou les siens tels qu'ils sont maintenant ?",
      quoi: "Les ordres de l'assaut descendent la chaîne pendant que les escouades marchent. " +
            "Le coureur doit retrouver son destinataire mobile et s'y rattacher sans mélanger les autres.",
      regarder: "Les coureurs ont un halo. Pointez-en un : sa bulle doit montrer les mots " +
                "qu'il porte et l'unité actuelle qu'il cherche.",
      manipulation: "On laisse fonctionner quarante-cinq secondes la transmission normale de l'assaut.",
      forces: "Les têtes, ailes, vintaines et coureurs de l'assaut à petite échelle.",
      terrain: "De la colonne extérieure jusqu'aux unités qui remontent vers la porte.",
      passe: "Au moins un coureur part et arrive ; après son arrivée, aucun homme ordinaire " +
             "n'est rattaché à une autre vintaine que la sienne.",
      echelle: 0.05, duree: 45, suivre: true,
      focus: (B) => {
        const c = B.troupe().filter((h) => h.etat === "coureur");
        return c.length ? c : B.troupe().filter((h) => h.camp === "assaut" && h.tete);
      },
      sondes: [
        { dit: "des coureurs sont réellement partis", attendu: "> 0 départ",
          tenu: (fin) => (fin.evenements || []).some((f) => f.quoi === "coureur-part"),
          mesure: (fin) => (fin.evenements || []).filter((f) => f.quoi === "coureur-part").length + " départ(s)" },
        { dit: "au moins un a retrouvé son destinataire mobile", attendu: "> 0 arrivée",
          tenu: (fin) => (fin.evenements || []).some((f) => f.quoi === "coureur-arrive"),
          mesure: (fin) => (fin.evenements || []).filter((f) => f.quoi === "coureur-arrive").length + " arrivée(s)" },
        { dit: "la remise de l'ordre ne mélange aucune autre appartenance", attendu: "0 erreur",
          tenu: (fin) => (fin.erreursAppartenance || []).length === 0,
          mesure: (fin) => (fin.erreursAppartenance || []).length + " erreur(s)" },
      ],
    },
    {
      n: "C5", id: "rassemblement-armee", famille: "Conduire les troupes",
      nom: "Une armée désorganisée se rassemble",
      question: "Des hommes mêlés savent-ils retrouver les leurs, puis leurs chefs former une armée ?",
      quoi: "Les cinq corps d'assaut commencent en nuage : les membres d'une même vintaine " +
            "sont éloignés et les vintenar sont mêlés aux autres corps. L'appartenance, elle, " +
            "n'est pas effacée. Le vintenar attend d'abord les siens ; la vintaine formée " +
            "prend ensuite sa place propre dans son aile, puis dans son corps.",
      regarder: "Au départ, survolez un homme et utilisez le cercle bleu de son unité : ses " +
                "pairs sont dispersés. Avancez par bonds ; les petits groupes doivent d'abord " +
                "se reformer autour de leur vintenar, puis les vintenar d'une même aile prendre " +
                "le même axe sans fusionner leurs hommes.",
      manipulation: "Tous les combattants de l'assaut sont dispersés de façon déterministe sur " +
                    "un sol libre. L'ordre est commun ; le repère d'armée déroule une seule emprise " +
                    "navigable, puis y range corps, ailes et vintaines selon la largeur réellement disponible.",
      forces: "L'armée d'assaut complète au quart : les cinq corps, leurs ailes et leurs vintaines.",
      terrain: "Le terrain libre devant Port-Réal, avant le contact avec le Guet.",
      passe: "La cohésion doit être réellement basse au départ, dépasser 70 % à l'arrivée, " +
             "les effectifs de chaque vintaine rester identiques, les chefs occuper leur propre " +
             "place, et les trajets rester payés par vintaine plutôt que par homme.",
      // Trois minutes : un homme éparpillé à quarante mètres doit
      // retrouver les siens AVANT que son chef parcoure encore la largeur de
      // la ligne. Soixante-quinze secondes jugeait surtout la vitesse du banc,
      // et cent vingt n'en plaçaient encore que seize sur vingt-quatre.
      echelle: 0.25, duree: 180,
      avant: (B) => {
        const hommes = B.troupe().filter((h) => h.camp === "assaut" &&
          !h.hors && h.etat !== "mort");
        if (!hommes.length) return;
        const origine = hommes.map((h) => ({ x:h.x, y:h.y }));
        // On cherche un vrai terrain de rassemblement autour d'une position
        // déjà occupée. Le centroïde des cinq attaques tombe au milieu de la
        // ville ; disperser autour de lui rejetait presque tous les points sur
        // le bâti et renvoyait les hommes à leurs cinq portes d'origine.
        const candidats = origine.filter((p, i) => i % Math.max(1, Math.floor(origine.length / 30)) === 0);
        const score = (p) => {
          let n = 0;
          for (let y = -48; y <= 48; y += 12) for (let x = -48; x <= 48; x += 12)
            if (B.libre(p.x + x, p.y + y) === true) n++;
          return n;
        };
        const centre = candidats.sort((a, b) => score(b) - score(a))[0] || origine[0];
        const cx = centre.x, cy = centre.y;

        // Un nuage de Vogel : déterministe, sans paquets artificiels par unité.
        // Si un point tombe dans le bâti, une position libre d'un AUTRE homme
        // sert de repli ; même ce repli mélange donc encore les appartenances.
        const or = Math.PI * (3 - Math.sqrt(5)), libres = [];
        for (let k = 0; k < hommes.length * 12 && libres.length < hommes.length * 2; k++) {
          const rayon = 5 + 48 * Math.sqrt((k + .5) / (hommes.length * 12));
          const angle = k * or, x = cx + Math.cos(angle) * rayon, y = cy + Math.sin(angle) * rayon;
          if (B.libre(x, y) === true) libres.push({ x, y });
        }
        for (let i = 0; i < hommes.length; i++) {
          const h = hommes[i], j = (i * 97 + 41) % hommes.length;
          const pi = libres.length ? (i * 97 + 41) % libres.length : -1;
          const p = pi >= 0 ? libres.splice(pi, 1)[0] : origine[j];
          const x = p.x, y = p.y;
          h.x = x; h.y = y; h.ex = x; h.ey = y;
          h.cible = null; if (!h.tete) h.etat = "colonne"; h.rail = null;
          h.railClef = null; h.railS = 0;
        }

        // Le front regarde le Guet, mais le rassemblement reste CENTRÉ sur le
        // lieu où les hommes se cherchent. Dans l'ancienne version, tous les
        // chefs recevaient le même point quarante-huit mètres plus loin : une
        // partie du groupe quittait donc le ralliement avant d'avoir retrouvé
        // les siens, puis tout le monde finissait en boule sur ce point.
        const garde = B.troupe().filter((h) => h.camp === "garde" && h.etat !== "mort");
        const gx = garde.length ? garde.reduce((n, h) => n + h.x, 0) / garde.length : cx + 1;
        const gy = garde.length ? garde.reduce((n, h) => n + h.y, 0) / garde.length : cy;
        B.ordonnerDeploiement({
          id:"epreuve:rassemblement-general",
          troupe:{ camp:"assaut" }, ancre:{ x:cx, y:cy },
          front:{ x:gx, y:gy }, forme:"ligne-soutien-reserve",
          ordre:{ destination:"la ligne de rassemblement",
            texte:"Retrouvez votre vintaine. Vintenar, prenez votre place dans l'aile." },
        });
        // L'épreuve porte sur UNE armée qui se rassemble, pas sur sa rencontre
        // fortuite avec les postes du Guet dans la zone choisie.
        const t = B.troupe();
        for (let i = t.length - 1; i >= 0; i--)
          if (t[i].camp !== "assaut" || t[i].hors) t.splice(i, 1);
      },
      focus: (B) => B.troupe().filter((h) => h.camp === "assaut" && !h.hors),
      sondes: [
        { dit: "l'épreuve commence avec une armée réellement défaite", attendu: "< 35 % groupés",
          tenu: (fin, s) => {
            const us = unitesQui(s[0], (u) => u.destination === "la ligne de rassemblement");
            return us.length > 1 && us.reduce((n, u) => n + u.cohesion, 0) / us.length < .35;
          },
          mesure: (fin, s) => {
            const us = unitesQui(s[0], (u) => u.destination === "la ligne de rassemblement");
            return Math.round(100 * us.reduce((n, u) => n + u.cohesion, 0) / (us.length || 1)) + " % groupés";
          } },
        { dit: "les hommes retrouvent leur propre vintaine", attendu: "≥ 70 % groupés",
          tenu: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            return us.length > 1 && us.reduce((n, u) => n + u.cohesion, 0) / us.length >= .70;
          },
          mesure: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            return Math.round(100 * us.reduce((n, u) => n + u.cohesion, 0) / (us.length || 1)) + " % groupés";
          } },
        { dit: "aucun homme ordinaire ne rejoint les voisins par proximité", attendu: "0 erreur",
          // Les coureurs arrivés changent légitimement d'effectif : ils sont le
          // cas spécial déjà éprouvé en C4. Ici on juge seulement l'identité
          // des soldats ordinaires, portée par `escouade`.
          tenu: (fin) => (fin.erreursAppartenance || []).length === 0,
          mesure: (fin) => (fin.erreursAppartenance || []).length + " mauvaise(s) vintaine(s)" },
        { dit: "chaque vintaine reçoit une place distincte dans la hiérarchie", attendu: "1 place par vintaine",
          tenu: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            return us.length > 1 && new Set(us.map((u) => u.placeRalliement &&
              (u.placeRalliement.x.toFixed(1) + ":" + u.placeRalliement.y.toFixed(1))).filter(Boolean)).size === us.length;
          },
          mesure: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            const places = new Set(us.map((u) => u.placeRalliement &&
              (u.placeRalliement.x.toFixed(1) + ":" + u.placeRalliement.y.toFixed(1))).filter(Boolean));
            return places.size + " place(s) pour " + us.length + " vintaines";
          } },
        { dit: "les vintenar occupent leur place au lieu de se masser au même point", attendu: "≥ 70 % à moins de 4 m",
          tenu: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            return us.length > 1 && us.filter((u) => u.placeRalliement &&
              Math.hypot(u.x - u.placeRalliement.x, u.y - u.placeRalliement.y) <= 4).length / us.length >= .70;
          },
          mesure: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            const n = us.filter((u) => u.placeRalliement &&
              Math.hypot(u.x - u.placeRalliement.x, u.y - u.placeRalliement.y) <= 4).length;
            return Math.round(100 * n / (us.length || 1)) + " % en place";
          } },
        { dit: "les centenar prennent la tête de leur aile", attendu: "≥ 70 % à moins de 5 m",
          tenu: (fin) => {
            const xs = (fin.echelons || []).filter((h) => h.role === "centenar");
            return xs.length > 0 && xs.filter((h) =>
              Math.hypot(h.x - h.cibleX, h.y - h.cibleY) <= 5).length / xs.length >= .70;
          },
          mesure: (fin) => {
            const xs = (fin.echelons || []).filter((h) => h.role === "centenar");
            const n = xs.filter((h) => Math.hypot(h.x - h.cibleX, h.y - h.cibleY) <= 5).length;
            return Math.round(100 * n / (xs.length || 1)) + " % en place";
          } },
        { dit: "les chefs de corps se placent derrière leur propre corps", attendu: "tous à moins de 6 m",
          tenu: (fin) => {
            const xs = (fin.echelons || []).filter((h) => h.role === "chef de corps");
            return xs.length > 0 && xs.every((h) =>
              Math.hypot(h.x - h.cibleX, h.y - h.cibleY) <= 6);
          },
          mesure: (fin) => {
            const ds = (fin.echelons || []).filter((h) => h.role === "chef de corps").map((h) =>
              Math.hypot(h.x - h.cibleX, h.y - h.cibleY));
            return ds.length ? Math.round(Math.max(...ds)) + " m pour le plus loin" : "aucun chef";
          } },
        { dit: "le trajet appartient à la vintaine, jamais à chacun de ses hommes",
          attendu: "≤ 2 calculs par vintaine",
          tenu: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            return us.length > 0 && us.reduce((n, u) => n + u.calculsAStar, 0) <= us.length * 2;
          },
          mesure: (fin) => {
            const us = unitesQui(fin, (u) => u.destination === "la ligne de rassemblement");
            return us.reduce((n, u) => n + u.calculsAStar, 0) + " A* pour " + us.length + " vintaines";
          } },
      ],
    },
    {
      n: "C6", id: "bataille-rangee-naive", famille: "Conduire les troupes",
      nom: "Deux forces livrent une bataille rangée sans tactique",
      question: "Que produit la doctrine ordinaire quand deux lignes se voient et avancent sans manœuvre ?",
      quoi: "Les deux camps se forment hors de portée, face à face, avec piquiers et cavaliers " +
            "mêlés à leur infanterie. Une fois leurs corps rangés, " +
            "chacun reçoit seulement l'ordre d'avancer en gardant sa formation. Aucun flanc n'est " +
            "refusé, aucune réserve n'est engagée sur signal, aucun point faible n'est renforcé.",
      regarder: "Commencez par les deux fronts et leurs intervalles, puis avancez par bonds. Regardez " +
                "où naît le premier contact, si toute la ligne se jette ensemble ou si une partie " +
                "reste hors du fer, et quel camp commence à se courber ou à rompre.",
      manipulation: "Deux déploiements indépendants sont posés sur un terrain traversable mais coupé " +
                    "par quelques bâtiments, à cent vingt " +
                    "mètres. Après trois minutes de formation hors champ, les deux lignes reçoivent le " +
                    "même objectif de terrain : le milieu du champ. Le moteur courant décide seul de la suite.",
      forces: "Tous les combattants constitués des deux camps à l'échelle 1/10, dont plusieurs " +
              "vintaines de pique et conrois montés. L'assaut est plus nombreux : " +
              "ce déséquilibre appartient au témoin et ne doit pas être compensé par une tactique cachée.",
      terrain: "Une emprise assez large pour deux fronts, choisie dans le vrai masque : les zones de " +
               "départ restent praticables mais des bâtiments cassent plusieurs lignes de vue et " +
               "laissent des passages latéraux.",
      passe: "Les deux forces doivent partir formées et orientées, se rencontrer réellement, conserver " +
             "leurs appartenances et n'engager qu'une minorité des hommes à la fois. Les chefs doivent " +
             "voir et transmettre les capacités adverses ; toute adaptation d'ordre doit être postérieure " +
             "à cette information. Le test ne choisit pas son vainqueur à l'avance.",
      echelle: 0.10, duree: 480,
      avant: (B) => {
        const t = B.troupe();
        // Cette scène ne garde que les combattants inscrits dans une unité et
        // les chefs de corps. Les coureurs de porte et la charrette ne sont ni
        // une aile ni une réserve de bataille rangée.
        for (let i = t.length - 1; i >= 0; i--) {
          const h = t[i];
          if (h.hors || (h.camp !== "assaut" && h.camp !== "garde") ||
              (!h.tete && (h.formation == null || h.formation < 0))) t.splice(i, 1);
        }
        const combattants = t.filter((h) => !h.tete && h.etat !== "mort");
        if (!combattants.length) return;

        // Chercher une emprise rectangulaire cassée mais praticable. Choisir
        // simplement le maximum de sol libre produisait précisément le faux
        // champ d'exercice que C6 ne doit plus être : information complète,
        // deux grilles face à face, aucun terrain à interpréter. Le score vise
        // maintenant une proportion de masque, exige des départs dégagés et
        // au moins un passage longitudinal. Aucun bâtiment n'est inventé.
        const candidats = combattants.filter((h, i) =>
          i % Math.max(1, Math.floor(combattants.length / 36)) === 0);
        let meilleur = null;
        for (const c of candidats) for (let k = 0; k < 16; k++) {
          const a = k * Math.PI / 16, ax = Math.cos(a), ay = Math.sin(a);
          const tx = -ay, ty = ax;
          let libres = 0, total = 0, libresCentre = 0, totalCentre = 0;
          let libresDepart = 0, totalDepart = 0;
          for (let p = -82; p <= 82; p += 12) for (let l = -54; l <= 54; l += 9) {
            total++;
            const libre = B.libre(c.x + ax * p + tx * l, c.y + ay * p + ty * l) === true;
            if (libre) libres++;
            if (Math.abs(p) <= 38) { totalCentre++; if (libre) libresCentre++; }
            if (Math.abs(p) >= 46) { totalDepart++; if (libre) libresDepart++; }
          }
          let meilleurPassage = 0;
          for (const l of [-42,-28,-14,0,14,28,42]) {
            let n=0, ok=0;
            for (let p=-82;p<=82;p+=6) {
              n++; if (B.libre(c.x+ax*p+tx*l,c.y+ay*p+ty*l)===true) ok++;
            }
            meilleurPassage=Math.max(meilleurPassage,ok/n);
          }
          const part=libres/total, partCentre=libresCentre/totalCentre;
          const partDepart=libresDepart/totalDepart, obstacles=total-libres;
          const topologie=analyserCouloir(B,{x:c.x,y:c.y},ax,ay,164,108,4);
          const recevable=part>=.68&&part<=.96&&partDepart>=.76&&
            partCentre>=.50&&partCentre<=.94&&meilleurPassage>=.70&&obstacles>=6&&
            topologie.traversable&&!topologie.barriere;
          const score=(recevable?3:0)-Math.abs(part-.84)*2.5-
            Math.abs(partCentre-.76)*1.6+partDepart*.7+meilleurPassage*.5-
            topologie.obstacleMax*.6;
          // Les préférences de densité peuvent être relâchées ; une barrière
          // qui sépare matériellement les camps, jamais.
          if(!topologie.traversable||topologie.barriere)continue;
          if (!meilleur || score > meilleur.score)
            meilleur = { x:c.x, y:c.y, ax, ay, tx, ty, score,
              terrain:{ partLibre:part, partCentre, partDepart,
                meilleurPassage, obstacles, recevable, topologie } };
        }
        if (!meilleur) return;
        const m = meilleur, ancreA = { x:m.x - m.ax * 60, y:m.y - m.ay * 60 };
        const ancreG = { x:m.x + m.ax * 60, y:m.y + m.ay * 60 };

        const poserNuage = (camp, ancre, sens) => {
          const xs = t.filter((h) => h.camp === camp), or = Math.PI * (3 - Math.sqrt(5));
          const libres = [];
          for (let k = 0; k < xs.length * 30 && libres.length < xs.length; k++) {
            const r = 4 + 40 * Math.sqrt((k + .5) / (xs.length * 30));
            const a = k * or, x = ancre.x + Math.cos(a) * r, y = ancre.y + Math.sin(a) * r;
            if (B.libre(x, y) === true) libres.push({ x, y });
          }
          xs.forEach((h, i) => {
            const p = libres[i] || ancre;
            h.x = p.x; h.y = p.y; h.ex = p.x; h.ey = p.y;
            h.cible = null; h.rail = null; h.railClef = null; h.railS = 0;
            h.fx = m.ax * sens; h.fy = m.ay * sens;
            if (!h.tete) h.etat = "rassemble";
          });
        };
        poserNuage("assaut", ancreA, 1);
        poserNuage("garde", ancreG, -1);
        B.ordonnerDeploiement({
          id:"rangee:assaut", troupe:{ camp:"assaut" }, ancre:ancreA,
          front:ancreG, forme:"ligne-soutien-reserve",
          ordre:{ destination:"la ligne de l'assaut",
            texte:"Formez sur les bannières. Front à l'ennemi." },
        });
        B.ordonnerDeploiement({
          id:"rangee:garde", troupe:{ camp:"garde" }, ancre:ancreG,
          front:ancreA, forme:"ligne-soutien-reserve",
          ordre:{ destination:"la ligne du Guet",
            texte:"Formez sur vos chefs. Front à l'ennemi." },
        });
        // Le témoin devient discriminant : les chefs ne font plus face à une
        // masse uniforme. Les types sont répartis sans adapter les ordres ; le
        // moteur doit d'abord les rendre physiquement vrais, puis révéler si
        // le commandement les voit et en fait quelque chose.
        const auCamp = (camp) => B.unites().filter((u) => u.camp === camp &&
          u.id.startsWith(camp + ":"));
        const aa = auCamp("assaut"), gg = auCamp("garde");
        for (const u of aa.slice(0, 2)) B.equiperUnite(u.id, "conroi");
        for (const u of aa.slice(2, 4)) B.equiperUnite(u.id, "pique");
        for (const u of gg.slice(0, 2)) B.equiperUnite(u.id, "pique");
        for (const u of gg.slice(2, 3)) B.equiperUnite(u.id, "conroi");
        // La formation est un préalable de scène, pas le sujet mesuré. Le
        // relevé t=180 devient le vrai départ de C6.
        B.pas(180);
        B.deplacerDeploiement("rangee:assaut",
          { x:m.x, y:m.y },
          { texte:"Toute la ligne, avancez droit sur l'ennemi.", but:"engager" });
        B.deplacerDeploiement("rangee:garde",
          { x:m.x, y:m.y },
          { texte:"Toute la ligne, avancez droit sur l'ennemi.", but:"engager" });
      },
      focus: (B) => B.troupe().filter((h) => !h.hors &&
        (h.camp === "assaut" || h.camp === "garde")),
      suivre: true,
      sondes: [
        { dit:"les deux forces commencent hors de portée", attendu:"> 70 m entre les centres",
          tenu:(fin, s) => !!s[0].geometrie && s[0].geometrie.separation > 70,
          mesure:(fin, s) => s[0].geometrie ? Math.round(s[0].geometrie.separation) + " m" : "sans géométrie" },
        { dit:"aucune barrière continue ne coupe le champ en deux",
          attendu:"deux départs connectés · aucun obstacle sur ≥ 50 % d’un axe",
          tenu:(fin,s) => !!s[0].geometrie && !!s[0].geometrie.terrain &&
            s[0].geometrie.terrain.traversable && !s[0].geometrie.terrain.barriere,
          mesure:(fin,s) => {
            const q=s[0].geometrie&&s[0].geometrie.terrain;
            return q ? (q.traversable?"passage continu":"aucun passage")+
              " · plus grand obstacle "+Math.round(q.obstacleMax*100)+" %" : "terrain inconnu";
          } },
        { dit:"le sol resserre le déploiement au lieu de projeter un damier dans les poches libres",
          attendu:"toutes les ancres sur sol libre · davantage de lignes physiques que d’échelons là où ça serre",
          tenu:(fin,s) => {
            const us=(s[0].unites||[]).filter((u)=>u.placeRalliement);
            if(!us.length||us.some((u)=>u.placeRalliement.libre!==true))return false;
            const terrain=s[0].geometrie&&s[0].geometrie.terrain;
            // Sur une place ouverte, trois échelons peuvent naturellement
            // tenir sur trois lignes : ne pas inventer un étranglement pour
            // satisfaire la sonde. Quand le masque mord réellement sur l'axe,
            // au moins un camp doit en revanche prendre de la profondeur.
            if(!terrain||terrain.obstacleMax<.10)return true;
            return ["assaut","garde"].some((camp)=>{
              const xs=us.filter((u)=>u.camp===camp),p=xs.map((u)=>u.placeRalliement);
              return new Set(p.map((q)=>q.ligneSol)).size>
                new Set(p.map((q)=>q.rang)).size;
            });
          },
          mesure:(fin,s) => ["assaut","garde"].map((camp)=>{
            const p=(s[0].unites||[]).filter((u)=>u.camp===camp&&u.placeRalliement)
              .map((u)=>u.placeRalliement);
            return camp+" "+new Set(p.map((q)=>q.ligneSol)).size+" lignes de sol / "+
              new Set(p.map((q)=>q.rang)).size+" échelons";
          }).join(" · ")+((s[0].geometrie&&s[0].geometrie.terrain&&
            s[0].geometrie.terrain.obstacleMax<.10)?" · terrain ouvert":" · terrain resserré") },
        { dit:"les deux forces regardent réellement l'adversaire", attendu:"orientation ≥ 0,70 chacune",
          tenu:(fin, s) => !!s[0].geometrie && ["assaut", "garde"].every((c) =>
            s[0].geometrie.camps[c].faceAdversaire >= .70),
          mesure:(fin, s) => s[0].geometrie ? ["assaut", "garde"].map((c) =>
            c + " " + s[0].geometrie.camps[c].faceAdversaire.toFixed(2)).join(" · ") : "sans géométrie" },
        { dit:"les deux lignes se rapprochent", attendu:"au moins 50 m gagnés",
          tenu:(fin, s) => !!fin.geometrie && !!s[0].geometrie &&
            s[0].geometrie.separation - Math.min(...s.filter((r) => r.geometrie)
              .map((r) => r.geometrie.separation)) >= 50,
          mesure:(fin, s) => {
            const gs = s.filter((r) => r.geometrie).map((r) => r.geometrie.separation);
            return gs.length ? Math.round(gs[0] - Math.min(...gs)) + " m" : "sans géométrie";
          } },
        { dit:"les éléments de commandement contournent le bâti sans lancer un chemin par homme",
          attendu:"chaque chef gagne au moins 80 % de son trajet · routes bornées par unité",
          tenu:(fin,s) => {
            const depart=s[0], ids=(depart.echelons||[]).map((e)=>({id:e.id,
              d:Math.hypot(e.x-e.cibleX,e.y-e.cibleY)})).filter((e)=>e.d>5);
            const arrives=ids.filter((e)=>Math.min(...s.map((r)=>{
              const q=(r.echelons||[]).find((x)=>x.id===e.id);
              return q?Math.hypot(q.x-q.cibleX,q.y-q.cibleY):Infinity;
            }))<=Math.max(2,e.d*.2)).length;
            return ids.length>0&&arrives===ids.length&&
              (fin.routesAStar||0)<=Math.max(1,(fin.unites||[]).length*6);
          },
          mesure:(fin,s) => {
            const depart=s[0],ids=(depart.echelons||[]).map((e)=>({id:e.id,
              d:Math.hypot(e.x-e.cibleX,e.y-e.cibleY)})).filter((e)=>e.d>5);
            const arrives=ids.filter((e)=>Math.min(...s.map((r)=>{
              const q=(r.echelons||[]).find((x)=>x.id===e.id);
              return q?Math.hypot(q.x-q.cibleX,q.y-q.cibleY):Infinity;
            }))<=Math.max(2,e.d*.2)).length;
            return arrives+"/"+ids.length+" chefs arrivés · "+fin.routesAStar+
              " calculs pour "+(fin.unites||[]).length+" unités";
          } },
        { dit:"la bataille a réellement lieu", attendu:">= 5 % dans l'allonge et >= 10 coups",
          tenu:(fin, s) => pic(s, (r) => r.partContact) >= .05 && fin.coupsTentes >= 10,
          mesure:(fin, s) => pic(s, (r) => r.auContact) + " au contact · " + fin.coupsTentes + " coups" },
        { dit:"seule une minorité combat au même instant", attendu:"pic ≤ 35 %",
          tenu:(fin, s) => pic(s, (r) => r.partContact) > 0 && pic(s, (r) => r.partContact) <= .35,
          mesure:(fin, s) => Math.round(100 * pic(s, (r) => r.partContact)) + " % au pic" },
        { dit:"les appartenances résistent à la rencontre", attendu:"0 erreur",
          tenu:(fin) => (fin.erreursAppartenance || []).length === 0,
          mesure:(fin) => (fin.erreursAppartenance || []).length + " erreur(s)" },
        { dit:"le terrain retire réellement de l'information aux commandants",
          attendu:"plusieurs directions visuelles arrêtées par le masque",
          tenu:(fin, s) => s.some((r) => (r.commandements || []).some((c) =>
            c.carte && c.carte.resume && c.carte.resume.rayonsBloques >= 3)),
          mesure:(fin, s) => {
            const xs=s.flatMap((r)=>(r.commandements||[]).map((c)=>
              c.carte&&c.carte.resume ? c.carte.resume.rayonsBloques : 0));
            return (xs.length ? Math.max(...xs) : 0) + "/48 directions masquées au maximum";
          } },
        { dit:"les commandants emportent la même faculté subjective que pendant un ratissage",
          attendu:"ordres reçus · observations locales · estimations par chef",
          tenu:(fin, s) => {
            const cs=(fin.commandements || []);
            return cs.length >= 2 && cs.every((c) => c.ordre) &&
              cs.some((c) => c.croyances.some((q) => q.genre === "ennemi" && q.source === "vu")) &&
              cs.some((c) => c.estimation && c.estimation.lieux > 0) &&
              s.some((r) => {
                const connus=(r.commandements || []).filter((c) => c.estimation && c.estimation.lieux > 0).length;
                return connus > 0 && connus < (r.commandements || []).length;
              });
          },
          mesure:(fin) => {
            const cs=fin.commandements || [], vus=cs.filter((c) => c.estimation && c.estimation.lieux > 0);
            return cs.length + " chefs · " + vus.length + " avec ennemi localisé · " +
              cs.reduce((n,c) => n+c.croyances.length,0) + " croyances";
          } },
        { dit:"les armes combinées existent réellement dans la troupe",
          attendu:"piquiers armés de piques · cavaliers montés dans les deux camps",
          tenu:(fin) => !!fin.parType.pique && !!fin.parType.conroi &&
            fin.parType.pique.total > 0 && fin.parType.conroi.montes > 0 &&
            fin.parType.conroi.montes === fin.parType.conroi.total,
          mesure:(fin) => (fin.parType.pique ? fin.parType.pique.total : 0) +
            " piquiers · " + (fin.parType.conroi ? fin.parType.conroi.montes : 0) + " cavaliers" },
        { dit:"les chefs distinguent et transmettent chevaux et longues hampes",
          attendu:"au moins une estimation de chaque signature · communication locale",
          tenu:(fin) => {
            const cs=fin.commandements || [], sig=cs.flatMap((c) => c.croyances || [])
              .map((c) => c.signatures || {});
            return sig.some((s) => s.montes && s.montes.max > 0) &&
              sig.some((s) => s.longuesHampes && s.longuesHampes.max > 0) &&
              cs.some((c) => c.communications > 0);
          },
          mesure:(fin) => { const cs=fin.commandements || [];
            const sig=cs.flatMap((c)=>c.croyances||[]).map((c)=>c.signatures||{});
            return sig.filter((s)=>s.montes).length + " vues montées · " +
              sig.filter((s)=>s.longuesHampes).length + " vues de hampes · " +
              cs.reduce((n,c)=>n+c.communications,0) + " communications"; } },
        { dit:"un chef change réellement son ordre après ce renseignement",
          attendu:"ordre postérieur à une observation typée, pas seulement avance générale",
          tenu:(fin) => (fin.commandements || []).some((c) => {
            const premier=(c.croyances || []).filter((q)=>q.signatures &&
              Object.keys(q.signatures).length).reduce((m,q)=>Math.min(m,q.misAJourA),Infinity);
            return Number.isFinite(premier) && c.ordreRecuA > premier;
          }),
          mesure:(fin) => { const cs=fin.commandements || [], adaptes=cs.filter((c) => {
            const p=(c.croyances||[]).filter((q)=>q.signatures&&Object.keys(q.signatures).length)
              .reduce((m,q)=>Math.min(m,q.misAJourA),Infinity);
            return Number.isFinite(p) && c.ordreRecuA > p;
          }); return adaptes.length + "/" + cs.length + " ordre(s) adapté(s)"; } },
        { dit:"le témoin enregistre l'issue sans la présumer", attendu:"pertes mesurées par camp",
          tenu:(fin) => !!fin.parCamp.assaut && !!fin.parCamp.garde && fin.coupsTentes > 0,
          mesure:(fin) => ["assaut", "garde"].map((c) => {
            const x = fin.parCamp[c]; return c + " : " + x.morts + " morts, " + x.deroute + " en déroute";
          }).join(" · ") },
      ],
    },
    {
      n:"C7", id:"ratissage-ville", famille:"Conduire les troupes",
      nom:"Des vintaines se partagent la fouille d'un quartier",
      question:"Des chefs pairs peuvent-ils se répartir une mission, apprendre de leurs rencontres et faire remonter une découverte ?",
      quoi:"Quatre vintaines reçoivent le même ordre large : fouiller un quartier. Aucune rue ni maison " +
        "ne leur est attribuée. Les chefs annoncent le secteur qu'ils prennent, échangent leur ordre et " +
        "les faits réellement vécus lorsqu'ils se rencontrent. Certains bâtiments peuvent cacher un " +
        "petit groupe rebelle selon leur usage ; un seul de ces hommes est le chef recherché.",
      regarder:"Suivez d'abord les quatre chefs au point de départ : leurs bulles doivent garder le même " +
        "ordre littéral tandis que leurs engagements divergent. Puis ouvrez une maison fouillée : les " +
        "hommes franchissent le seuil. Lorsqu'un groupe tombe, cherchez le porteur qui repart vers le chef supérieur.",
      manipulation:"Le quartier est choisi dans le bâti réel près de l'armée. Les occupations sont " +
        "déterministes pour le rejeu mais pondérées par le type de bâtiment. Il n'existe aucune " +
        "contre-opération rebelle : aucun renfort, déplacement ou partage d'information adverse.",
      forces:"Quatre vintaines constituées et un chef supérieur au point de rencontre. Trois ou quatre " +
        "groupes rebelles de trois à sept hommes restent cachés jusqu'au franchissement de leur porte.",
      terrain:"Un morceau dense du Port-Réal produit par le vrai fichier du bâti, avec ses maisons, " +
        "échoppes, entrepôts, tavernes, manses et corps de garde.",
      passe:"Les unités doivent prendre des secteurs distincts par communication locale, entrer dans les " +
        "bâtiments, rencontrer au moins un groupe, identifier le chef rebelle et porter cette information " +
        "jusqu'au commandement sans jamais combattre à travers un mur.",
      // Quinze minutes suffisaient à fouiller, pas à éprouver le retour : au
      // verdict, certaines vintaines combattaient encore. On laisse ensuite
      // le temps aux unités de parcourir leur vraie route de ralliement.
      echelle:.05, duree:1300,
      avant:(B) => {
        const t = B.troupe(), us = B.unites().filter((u) => u.camp === "assaut" &&
          u.id.startsWith("assaut:")).slice(0, 4);
        if (us.length < 4) return;
        const ns = new Set(B.unites().map((u, i) => us.some((q) => q.id === u.id) ? i : -1)
          .filter((i) => i >= 0));
        const membres = t.filter((h) => ns.has(h.formation));
        const chef = t.find((h) => h.camp === "assaut" && h.tete);
        if (!membres.length || !chef) return;
        const bs = B.batiments().filter((b) => B.libre(b.x, b.y) === true);
        // C7 choisit un vrai quartier dense, pas le premier bâti rencontré au
        // pied de la muraille. Une maille de 80 m suffit à trouver la plus forte
        // concentration de portes sans inscrire un quartier particulier dans
        // le scénario.
        const mailles = new Map();
        for (const b of bs) {
          const k = Math.floor(b.x/80) + ":" + Math.floor(b.y/80);
          if (!mailles.has(k)) mailles.set(k, []);
          mailles.get(k).push(b);
        }
        const dense = [...mailles.values()].sort((a,b) => b.length-a.length)[0] || [];
        if (!dense.length) return;
        const mx=dense.reduce((n,b)=>n+b.x,0)/dense.length;
        const my=dense.reduce((n,b)=>n+b.y,0)/dense.length;
        const ancre=dense.sort((a,b)=>(a.x-mx)**2+(a.y-my)**2-(b.x-mx)**2-(b.y-my)**2)[0];
        const rdv = { x:ancre.x, y:ancre.y };
        const garder = new Set(membres.concat([chef]));
        for (let i = t.length - 1; i >= 0; i--) if (!garder.has(t[i])) t.splice(i, 1);
        // Les quatre unités arrivent ensemble au point de mission. Elles ne
        // sont pas préaffectées : cette proximité est précisément ce qui leur
        // permet de confronter leurs engagements avant de se séparer.
        for (const [g, u] of us.entries()) {
          // `formation` est l'index stable ; retrouver celui de l'unité évite
          // de supposer que l'échelle a conservé toutes les unités précédentes.
          const ui = B.unites().findIndex((q) => q.id === u.id);
          const ys = membres.filter((h) => h.formation === ui);
          ys.forEach((h, i) => {
            let x = rdv.x + (g - 1.5) * 5 + (i % 4) * .8;
            let y = rdv.y + Math.floor(i / 4) * .9;
            if (B.libre(x, y) !== true) { x = rdv.x + (g - 1.5) * 2; y = rdv.y + i * .35; }
            h.x=x; h.y=y; h.ex=x; h.ey=y; h.interieur=null; h.cible=null;
            h.etat="rassemble"; h.rail=null; h.railClef=null;
          });
        }
        chef.x = rdv.x - 8; chef.y = rdv.y - 8; chef.ex = chef.x; chef.ey = chef.y;
        chef.rapports = []; chef.etat = "tient";

        // Le centre de mission vient du bâtiment accessible le plus proche du
        // rassemblement, pas d'une adresse écrite pour ce scénario.
        const corridor = (b) => {
          // Dix sondes sur deux cents mètres pouvaient sauter une maison
          // entière — ou la muraille — et déclarer sa porte accessible. C7
          // doit éprouver le ratissage, pas les lacunes du graphe : on certifie
          // ici le corridor continu avec un pas inférieur à la case du masque.
          const n = Math.max(1, Math.ceil(Math.hypot(b.x-rdv.x, b.y-rdv.y) / .8));
          for (let k=1; k<n; k++) if (B.libre(rdv.x + (b.x-rdv.x)*k/n,
            rdv.y + (b.y-rdv.y)*k/n) !== true) return false;
          return true;
        };
        const accessibles = bs.filter((b) => Math.hypot(b.x-rdv.x, b.y-rdv.y) <= 220 && corridor(b))
          .sort((a, b) => Math.hypot(a.x-rdv.x, a.y-rdv.y) -
                           Math.hypot(b.x-rdv.x, b.y-rdv.y)).slice(0, 32);
        const centre = accessibles[0];
        if (!centre) return;
        B.ordonnerRatissage({
          id:"ratissage:quartier", unites:us.map((u) => u.id),
          zone:{ x:centre.x, y:centre.y, rayon:110 }, batiments:accessibles.map((b) => b.id),
          maxBatiments:32,
          rdv, commandement:chef, contreOperations:0, minGroupes:3, maxGroupes:4,
          chances:{
            "corps-de-garde":.55, caserne:.45, entrepot:.28, taverne:.20,
            auberge:.20, manse:.14, guilde:.18, forge:.12, "maison-officier":.12,
            echoppe:.07, maison:.025, taudis:.012, cabane:.01, defaut:.02,
          },
          ordre:{ texte:"Fouillez ce quartier. Dites aux autres ce que vous prenez et ce que vous avez vu. Faites remonter toute prise importante." },
        });
      },
      focus:(B) => B.troupe(), suivre:true,
      sondes:[
        { dit:"les caches viennent du type des bâtiments, sans contre-opération",
          attendu:"3–4 groupes · 0 contre-opération",
          tenu:(fin) => {
            const r = fin.ratissages[0]; return !!r && r.groupesPrevus >= 3 &&
              r.groupesPrevus <= 4 && r.contreOperations === 0;
          },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ?
            r.groupesPrevus + " groupes · " + r.contreOperations + " contre-opération" : "aucune mission"; } },
        { dit:"les chefs pairs échangent ordres, faits et engagements",
          attendu:"≥ 2 échanges et ≥ 1 fait transmis",
          tenu:(fin) => { const r=fin.ratissages[0]; return !!r && r.echanges >= 2 && r.faitsTransmis >= 1; },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ? r.echanges + " échanges · " +
            r.faitsTransmis + " faits transmis" : "aucune mission"; } },
        { dit:"les chefs prononcent leur ordre et une estimation située",
          attendu:"ordres littéraux · estimations de force · ≥ 8 messages",
          tenu:(fin) => { const r=fin.ratissages[0]; return !!r && r.messages >= 8 &&
            r.communications.some((c) => c.phrasesA.concat(c.phrasesB).some((p) => p.includes("Mon ordre est"))) &&
            r.communications.some((c) => c.estimationA && c.estimationB); },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ? r.messages +
            " messages · " + r.communications.length + " conversations tracées" : "aucune mission"; } },
        { dit:"un renseignement reçu devient une croyance, pas une vérité globale",
          attendu:"au moins une croyance directe et une croyance rapportée, avec confiance",
          tenu:(fin) => { const r=fin.ratissages[0]; if (!r) return false;
            const cs=r.unites.flatMap((u) => u.croyances || []);
            return cs.some((c) => c.source === "vu" && c.confianceActuelle > 0) &&
              cs.some((c) => c.source === "dit" && c.apprisDe && c.confianceActuelle > 0); },
          mesure:(fin) => { const r=fin.ratissages[0]; if (!r) return "aucune mission";
            const cs=r.unites.flatMap((u) => u.croyances || []);
            return cs.filter((c) => c.source === "vu").length + " directes · " +
              cs.filter((c) => c.source === "dit").length + " rapportées"; } },
        { dit:"les unités prennent réellement plusieurs secteurs",
          attendu:"au moins un engagement par unité",
          tenu:(fin) => { const r=fin.ratissages[0]; return !!r && r.engagementsPris >= 4; },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ? r.engagementsPris +
            " engagements · " + r.conflitsResolus + " conflits résolus" : "aucune mission"; } },
        { dit:"le repos ne commence qu'après le ralliement des vintaines au reste de la force",
          attendu:"≥ 1 unité revenue · aucun repos avant ralliement · ≥ 65 % de ses hommes au poste",
          tenu:(fin) => { const r=fin.ratissages[0]; if (!r) return false;
            const ps=r.formationRdv || [], sep=[];
            for(let i=0;i<ps.length;i++) for(let j=i+1;j<ps.length;j++)
              sep.push(Math.hypot(ps[i].x-ps[j].x,ps[i].y-ps[j].y));
            return ps.length >= 1 && (!sep.length || Math.min(...sep) >= 2.5) &&
              r.unitesRalliees >= 1 && r.unitesAuRepos === r.unitesRalliees &&
              r.troupesRalliees/Math.max(1,r.effectifRallie) >= .65 &&
              r.chefsEnPlace === r.unitesRalliees;
          },
          mesure:(fin) => { const r=fin.ratissages[0]; if (!r) return "aucune mission";
            const ps=r.formationRdv || [], sep=[];
            for(let i=0;i<ps.length;i++) for(let j=i+1;j<ps.length;j++)
              sep.push(Math.hypot(ps[i].x-ps[j].x,ps[i].y-ps[j].y));
            return r.unitesRalliees + " unités ralliées · " + r.unitesAuRepos+
              " au repos · " + r.troupesRalliees+"/"+r.effectifRallie+
              " hommes des unités revenues au poste · " + r.chefsEnPlace+
              " chefs en place · " +
              (sep.length ? Math.min(...sep).toFixed(1) : "—") + " m entre chefs · " +
              r.unites.map((u)=>u.id+":"+u.phase+"/"+
                (u.ralliement ? u.ralliement.reste+"m@"+u.ralliement.cohesion+"/"+
                  JSON.stringify(u.ralliement.route) : "en mission")).join(" · ");
          } },
        { dit:"les hommes franchissent les seuils et fouillent",
          attendu:"≥ 6 bâtiments clairs ou repris",
          tenu:(fin) => { const r=fin.ratissages[0]; return !!r &&
            r.batimentsClairs + r.groupesVaincus >= 6; },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ? r.entrees + " entrées · " +
            r.batimentsClairs + " clairs · " + r.groupesVaincus + " repris" : "aucune mission"; } },
        { dit:"au moins un groupe caché est effectivement découvert et vaincu",
          attendu:"≥ 1 groupe vaincu",
          tenu:(fin) => { const r=fin.ratissages[0]; return !!r && r.groupesReveles > 0 && r.groupesVaincus > 0; },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ? r.groupesReveles +
            " découverts · " + r.groupesVaincus + " vaincus" : "aucune mission"; } },
        { dit:"l'identité du chef rebelle remonte jusqu'au commandement",
          attendu:"chef identifié · rapport arrivé",
          tenu:(fin) => { const r=fin.ratissages[0]; return !!r && r.chefIdentifie &&
            r.chefSignale && r.rapportsArrives > 0; },
          mesure:(fin) => { const r=fin.ratissages[0]; return r ?
            (r.chefIdentifie ? "identifié" : "inconnu") + " · " + r.rapportsArrives + " rapport arrivé" : "aucune mission"; } },
        { dit:"personne ne cible un homme à travers un mur",
          attendu:"0 cible dans un autre espace",
          tenu:(fin, s) => s.every((r) => !r.ciblesATraversMur.length),
          mesure:(fin, s) => Math.max(...s.map((r) => r.ciblesATraversMur.length)) + " au pic" },
      ],
    },
  ];

  // ═══ LA SÉRIE ═══════════════════════════════════════════════════════════
  // Les mesures historiques restent du simple au composé. Elles forment une
  // famille ; elles ne prétendent plus être le seul parcours utile de la page.
  const DYNAMIQUES = [
    {
      n: 1, id: "sol",
      nom: "Occupation du sol au dressage",
      quoi: "Avant qu'aucun homme n'ait bougé, personne ne doit se trouver " +
            "dans un bâtiment. C'est la seule épreuve qui ne simule rien : elle " +
            "juge la mise en place seule. Si elle échoue, toutes les mesures de " +
            "traversée de murs sont faussées à la source, puisqu'une part des " +
            "hommes y est née.",
      forces: "L'ordre de bataille complet au vingtième — cinq corps d'assaut, " +
              "la garnison des quatre portes et de l'anneau.",
      terrain: "Port-Réal, la porte de la Gadoue. Le masque du bâti tel que " +
               "`plan_ville.py` le cuit.",
      passe: "Zéro homme dans le bâti à t = 0.",
      echelle: 0.05, duree: 0,
      sondes: [
        { dit: "personne n'est posé dans un mur",
          tenu: (fin, s) => s[0].dansLeMur === 0 },
        { dit: "le masque répond pour tout le monde",
          tenu: (fin, s) => s[0].inconnu === 0 },
      ],
    },
    {
      n: 2, id: "marche",
      nom: "Tenue du chemin en marche",
      quoi: "Les hommes marchent vers la porte puis vers le donjon. Aucun ne " +
            "doit couper à travers un pâté de maisons. L'épreuve isole le " +
            "DÉPLACEMENT : elle s'arrête avant que le premier fer ne tombe, " +
            "donc rien de ce qu'on y voit ne vient du combat.",
      forces: "Le même ordre de bataille, au vingtième.",
      terrain: "L'axe du port vers la colline d'Aegon — six cent treize mètres " +
               "de rue, largeurs réelles.",
      passe: "Moins d'un homme sur cinquante dans le bâti, à tout instant.",
      echelle: 0.05, duree: 180,
      sondes: [
        { dit: "moins d'un homme sur cinquante dans le bâti",
          tenu: (fin, s) => pic(s, (r) => r.partMur) < 0.02 },
        { dit: "aucun n'est encore mort — l'épreuve porte bien sur la marche",
          tenu: (fin) => fin.morts === 0 },
      ],
    },
    {
      n: 3, id: "repos",
      nom: "Approche avant la portée",
      quoi: "Les trente premières secondes isolent l'approche réelle : les " +
            "deux troupes sont encore séparées. Ce n'est pas une fausse rase " +
            "campagne — c'est la Gadoue telle qu'elle est dressée, avant le fer. " +
            "La couche sociale ne doit pas fabriquer seule une panique.",
      forces: "L'ordre de bataille complet au vingtième, à sa position réelle.",
      terrain: "L'approche de la Gadoue, avant le premier homme dans l'allonge.",
      passe: "Personne dans l'allonge, aucun coup réellement tenté, zéro fuyard.",
      echelle: 0.05, duree: 30,
      sondes: [
        { dit: "personne ne rompt", tenu: (fin) => fin.fuyards === 0 },
        { dit: "personne n'entre encore dans l'allonge",
          tenu: (fin, s) => jamais(s, (r) => r.auContact) },
        { dit: "aucun coup n'est réellement tenté", tenu: (fin) => fin.coupsTentes === 0 },
        { dit: "aucune jambe ne dit « fuite »",
          tenu: (fin, s) => jamais(s, (r) => r.jambes["fuite"]) },
        { dit: "aucun bras ne tombe", tenu: (fin, s) => jamais(s, (r) => r.bras["ballants"]) },
      ],
    },
    {
      n: 4, id: "croisee",
      nom: "Deux vintaines qui se croisent dans une rue",
      quoi: "La plus petite rencontre lisible : vingt contre vingt, une rue, " +
            "et personne d'autre. C'est l'echelle du GROUPE PRIMAIRE (3 a 25 " +
            "hommes), celle ou vit la cohesion et la seule ou l'on peut " +
            "suivre chaque homme a l'oeil. Tout ce que les epreuves suivantes " +
            "mesurent en pourcentages se voit ici en individus — et c'est " +
            "pour ca qu'elle vient avant elles.",
      forces: "Une vintaine d'assaut et une vintaine du Guet, chefs compris, " +
              "face a face a vingt-sept metres. Tout le reste de la nuit est " +
              "RETIRE du champ : ni corps voisin, ni porte a enfoncer, ni " +
              "banniere a regarder. Ce qui arrive n'arrive que par ces " +
              "quarante hommes.",
      terrain: "Une vraie rue INTRA MUROS. On part d'un homme du Guet — donc " +
               "d'un point ou quelqu'un se tient deja, donc libre — et l'on " +
               "cherche autour de lui un vis-a-vis a trente metres dont le " +
               "COULOIR ENTIER reponde libre au masque. Sans ce test du " +
               "couloir on tombait dehors, en rase campagne, la ou la colonne " +
               "d'assaut se forme avant la porte.",
      passe: "Le fer se touche, ET le camp qui l'emporte perd au plus un homme " +
             "sur dix (§ 7.2 : consensus medieval 5–10 % pour le vainqueur). " +
             "Une rencontre ou la moitie du monde meurt en trois minutes n'est " +
             "pas une rencontre, c'est un accident de modele.",
      echelle: 0.05, duree: 180,
      // ⚠ CETTE EPREUVE TRONQUE LA TROUPE, et c'est le seul endroit du fichier
      // qui le fasse. `B.troupe()` rend le TABLEAU VIVANT des hommes : on en
      // retire tout ce qui n'est pas nos quarante. Abus assume — il n'existe
      // que parce que `dresser()` n'a pas d'entree pour poser une poignee
      // d'hommes ou l'on veut. Le jour ou `poserScene(spec)` existera, cette
      // epreuve sera la premiere a s'ecrire proprement.
      //
      // ⚠ ET LE POSTE EST EN FACE, PAS SOUS LES PIEDS. Premiere version : les
      // deux camps posaient leur `poste` la ou ils se tenaient — donc chacun
      // gardait sa place et PERSONNE NE BOUGEAIT. Un homme en `tient` marche
      // vers son poste ; en le mettant sur la troupe adverse, on obtient une
      // approche sans avoir a inventer d'ordre. Ce sont ensuite les branches
      // de chasse et de recul du moteur qui font la rencontre.
      avant: (B) => {
        const t = B.troupe();
        const bon = (h) => !h.tete && !h.roi && !h.hors;
        const a = t.filter((h) => h.camp === "assaut" && bon(h)).slice(0, 20);
        const tousG = t.filter((h) => h.camp === "garde" && bon(h));
        if (a.length < 20 || tousG.length < 20) return;

        // ON CHERCHE LA RUE LA PLUS PROCHE DE LA PORTE, et pas la premiere
        // venue. La version d'avant prenait le premier garde de la liste : elle
        // est tombee sur un poste a MILLE HUIT CENT QUATRE-VINGT-CINQ METRES de
        // l'assaut, c'est-a-dire une ruelle au hasard a l'autre bout de la
        // ville. L'epreuve tournait bien et ne montrait rien — on ne savait
        // meme pas ou regarder.
        const cxa = a.reduce((s2, h) => s2 + h.x, 0) / a.length;
        const cya = a.reduce((s2, h) => s2 + h.y, 0) / a.length;
        tousG.sort((p2, q) => Math.hypot(p2.x - cxa, p2.y - cya) -
                              Math.hypot(q.x - cxa, q.y - cya));
        // Et l'on prend les vingt LES PLUS PROCHES, pas les vingt premiers du
        // tableau : le tri venait apres le prelevement, si bien que l'ancre
        // etait la bonne et la troupe quelconque. Sans consequence sur le
        // resultat — on les replace tous — mais c'est le genre de decalage qui
        // rend un relevé impossible a relire six semaines plus tard.
        const g = tousG.slice(0, 20);

        // LA RUE — on la trouve, on ne la calcule pas. Un centroide de troupe
        // tombe dans un pate de maisons une fois sur deux (celui d'un anneau,
        // c'est le donjon) ; la position d'un homme, elle, est libre par
        // construction.
        let A = null, P = null, U = null;
        for (const anc of tousG) {
          if (B.libre(anc.x, anc.y) !== true) continue;
          for (let k = 0; k < 24 && !P; k++) {
            const ang = k * Math.PI / 12, dx = Math.cos(ang), dy = Math.sin(ang), d = 30;
            const x = anc.x + dx * d, y = anc.y + dy * d;
            if (B.libre(x, y) !== true) continue;
            let ok = true;
            for (let u = 0.1; u < 1; u += 0.1)
              if (B.libre(anc.x + dx * d * u, anc.y + dy * d * u) !== true) { ok = false; break; }
            if (ok) { A = anc; P = { x: x, y: y }; U = { dx: dx, dy: dy }; }
          }
          if (P) break;
        }
        if (!P) return;                    // pas de rue trouvee : on ne bricole pas

        // Quatre rangs de cinq, chacun tourne vers l'autre. Un homme qui
        // tomberait dans un mur est decale — le masque tranche, pas nous.
        const poser = (l, ox, oy, u, vers) => l.forEach((h, i) => {
          const c = (i % 5 - 2) * 0.8, r = Math.floor(i / 5) * 1.0;
          h.x = ox + (-u.dy) * c + u.dx * r;
          h.y = oy + u.dx * c + u.dy * r;
          for (let e = 0; e < 8 && B.libre(h.x, h.y) === false; e++) {
            h.x -= u.dx * 0.7; h.y -= u.dy * 0.7;
          }
          h.etat = "tient"; h.cible = null;
          h.poste = [vers.x, vers.y];       // EN FACE — c'est ce qui les fait marcher
          const fx = vers.x - h.x, fy = vers.y - h.y, n = Math.hypot(fx, fy) || 1;
          h.fx = fx / n; h.fy = fy / n; h.cx = h.fx; h.cy = h.fy;
        });
        poser(g, A.x, A.y, U, P);
        poser(a, P.x, P.y, { dx: -U.dx, dy: -U.dy }, A);

        const garder = new Set(a.concat(g));
        for (let i = t.length - 1; i >= 0; i--) if (!garder.has(t[i])) t.splice(i, 1);
      },
      sondes: [
        { dit: "le fer se touche", tenu: (fin) => fin.morts + fin.blesses > 0 },
        { dit: "le camp qui l'emporte perd au plus un homme sur dix",
          tenu: (fin) => {
            const c = fin.parCamp || {};
            const noms = Object.keys(c);
            if (noms.length < 2 || fin.morts === 0) return null;
            const vq = noms.sort((x, y) => c[y].vivants - c[x].vivants)[0];
            return c[vq].morts / (c[vq].total || 1) <= 0.10;
          } },
        { dit: "et il reste du monde des deux cotes",
          tenu: (fin) => {
            const c = fin.parCamp || {};
            const noms = Object.keys(c);
            if (noms.length < 2) return null;
            return noms.every((k) => c[k].vivants > 0);
          } },
      ],
    },
    {
      n: 5, id: "contact",
      nom: "Proportion d'hommes au contact",
      quoi: "Le chiffre le plus structurant de la recherche. La géométrie " +
            "seule l'impose : seul le premier rang peut frapper, deux si les " +
            "armes sont longues — soit 12,5 % à huit rangs, 6 % à seize. " +
            "S'y ajoute que, parmi ceux-là, une minorité seulement porte des " +
            "coups sérieux. Un moteur où la moitié de l'armée se bat à la fois " +
            "produira des pertes d'un ordre de grandeur trop haut.",
      forces: "L'ordre complet au dixième, jusqu'à la mêlée du seuil.",
      terrain: "Le goulet de la porte : six mètres, sept hommes de front.",
      passe: "Au pic, au plus 25 % des vivants dans l'allonge et au plus 10 % " +
             "ayant réellement tenté un coup dans les cinq secondes (§ 3.3 : « 10–25 % au contact, 5 à 10 % en " +
             "train de frapper »).",
      echelle: 0.1, duree: 420,
      sondes: [
        { dit: "au plus un quart des vivants dans l'allonge",
          tenu: (fin, s) => pic(s, (r) => r.partContact) <= 0.25 },
        { dit: "au plus un dixième a réellement frappé depuis cinq secondes",
          tenu: (fin, s) => pic(s, (r) => r.partFrappent) <= 0.10 },
        { dit: "et il y a bien eu une mêlée",
          tenu: (fin, s) => pic(s, (r) => r.auContact) > 0 ? true : null },
      ],
    },
    {
      n: 6, id: "letalite",
      nom: "Attrition avant la rupture",
      quoi: "Le calcul de Sabin : si 5 % des hommes frappaient toutes les cinq " +
            "secondes avec 1 % de coups mortels, chaque armée perdrait 5 % " +
            "toutes les dix minutes — soit, en une heure, six fois le total " +
            "d'une bataille entière. Cette épreuve mesure si le moteur a le bon " +
            "ordre de grandeur, et c'est celle qui juge le mieux le modèle de " +
            "coup, de parade et d'armure.",
      forces: "L'ordre complet au dixième, sur sept minutes.",
      terrain: "La porte et la rue derrière.",
      passe: "Avant la première rupture, les morts restent minoritaires ; si " +
             "personne ne rompt, l'épreuve le dit au lieu d'inventer un vainqueur.",
      echelle: 0.1, duree: 420,
      sondes: [
        { dit: "les morts avant rupture restent sous un dixième",
          tenu: (fin, s) => {
            const r = s.find((x) => x.fuyards > 0);
            return r ? r.morts / (s[0].vivants || 1) <= 0.10 : null;
          } },
        { dit: "et la bataille a bien eu lieu",
          tenu: (fin) => fin.morts > 0 ? true : null },
      ],
    },
    {
      n: 7, id: "rythme",
      nom: "Rythme des bouffées de corps-à-corps",
      quoi: "Le combat en armure à pleine intensité est de l'ordre de la " +
            "minute et demie, pas de l'heure : trois rounds de 90 s suffisent " +
            "à porter le lactate de 1,0 à 8,2 mmol/L pour un seuil à 2,9. Un " +
            "homme y revient plusieurs fois, dégradé à chaque fois. Bouvines " +
            "l'atteste au niveau de l'unité — le comte de Saint-Pol se retire, " +
            "souffle FACE à l'ennemi, et repart avec ses chevaliers reposés.",
      forces: "L'ordre complet au dixième.",
      terrain: "Le seuil de la porte, où la presse empêche de se dégager.",
      passe: "Les bouts réels doivent rester courts et certains hommes doivent " +
             "rentrer plusieurs fois dans l'allonge. On ne déduit plus une " +
             "respiration d'une simple baisse d'effectif.",
      echelle: 0.1, duree: 420,
      sondes: [
        { dit: "le p90 d'une bouffée reste sous quatre-vingt-dix secondes",
          tenu: (fin) => fin.bouts ? fin.boutP90 <= 90 : null },
        { dit: "des hommes rentrent plusieurs fois dans l'allonge",
          tenu: (fin) => fin.bouts ? fin.hommesMultiBouts > 0 : null },
      ],
    },
    {
      n: 8, id: "recul",
      nom: "Recul continu avant toute rupture",
      quoi: "Céder du terrain est normal et n'est pas rompre : c'est un état " +
            "continu, et le signe visible de qui a l'ascendant. Les lignes " +
            "romaines se déplacent de centaines de mètres, les Helvètes " +
            "reculent d'un mille puis reprennent le combat. Un moteur qui n'a " +
            "que « tenir » et « fuir » saute cette marche et rend des batailles " +
            "binaires.",
      forces: "L'assaut entamé au quart de ses points de vie, la garnison " +
              "intacte — la situation où une troupe doit céder du terrain.",
      terrain: "Le seuil, avec de la rue derrière l'assaillant : il a où aller.",
      passe: "« recul » doit être bien plus fréquent que « fuite » (§ 6.2 : le " +
             "repoussement est une statistique de micro-reculs, pas une poussée).",
      echelle: 0.1, duree: 420,
      avant: (B) => { for (const h of des(B, duCamp("assaut"))) entamer(h, 0.25); },
      sondes: [
        { dit: "des hommes cèdent le pas",
          tenu: (fin, s) => pic(s, (r) => r.jambes["recul"]) > 0 },
        { dit: "le recul l'emporte largement sur la fuite",
          tenu: (fin, s) => {
            const r0 = pic(s, (r) => r.jambes["recul"]), f = pic(s, (r) => r.jambes["fuite"]);
            return r0 === 0 ? null : r0 > f * 3;
          } },
      ],
    },
    {
      n: 9, id: "rupture",
      nom: "Rupture d'un corps mal dressé",
      quoi: "La rupture est DISCONTINUE : on tient, puis les liens de " +
            "dissuasion mutuelle cassent d'un coup, et le massacre commence. " +
            "On soumet donc le corps le moins dressé du dossier — les " +
            "bleusailles, dressage −0,60 — à des pertes que rien ne soutient. " +
            "Si celui-là ne rompt pas, aucun ne le fera jamais : c'est la " +
            "borne haute de la question.",
      forces: "Les bleusailles entamées à 15 % de leurs points ; les quatre " +
              "autres corps intacts, pour qu'on voie si la rupture est LOCALE.",
      terrain: "Le seuil, rue ouverte derrière — sans issue, la fuite est " +
               "impossible et l'épreuve ne dirait rien (§ 6.3).",
      passe: "Au moins un fuyard, et la rupture reste circonscrite : elle ne " +
             "doit pas emporter toute l'armée.",
      echelle: 0.1, duree: 420,
      avant: (B) => { for (const h of des(B, duCorps("bleusailles"))) entamer(h, 0.15); },
      sondes: [
        { dit: "les jambes disent « fuite » au moins une fois",
          tenu: (fin, s) => !jamais(s, (r) => r.jambes["fuite"]) },
        { dit: "au moins un homme rompt", tenu: (fin) => fin.fuyards > 0 },
        { dit: "et la rupture ne prend pas toute l'armée",
          tenu: (fin, s) => fin.fuyards === 0 ? null
                : fin.fuyards < (s[0].vivants || 1) * 0.5 },
      ],
    },
    {
      n: 10, id: "presse",
      nom: "Le jeu derrière soi, et sa disparition",
      quoi: "Un homme ne peut se dérober que s'il y a de la place derrière " +
            "lui. Quand ce jeu disparaît — troupes trop serrées, poussée de " +
            "l'arrière, encerclement —, il ne peut plus ni employer son arme " +
            "ni reculer, et c'est précisément là que commence le massacre " +
            "unilatéral. L'épreuve la plus dure de la série : elle demande que " +
            "la presse produise de la SIDÉRATION plutôt que de la fuite.",
      forces: "L'ordre complet au dixième — la masse est le sujet.",
      terrain: "Le goulet de six mètres, qui fabrique le bouchon de lui-même : " +
               "sept hommes de front, les autres attendent dehors.",
      passe: "Là où la presse est forte, « recul » et « dérobade » doivent se " +
             "raréfier au profit de « planté » ou « sidération ».",
      echelle: 0.1, duree: 420,
      sondes: [
        { dit: "le goulet ferme réellement des sorties",
          tenu: (fin, s) => pic(s, (r) => r.sortieFermee) > 0 },
        { dit: "la presse humaine existe dans le même temps",
          tenu: (fin, s) => pic(s, (r) => r.presseForte) > 0 },
        { dit: "la presse produit de la sidération",
          tenu: (fin, s) => !jamais(s, (r) => r.jambes["sidération"]) },
        { dit: "et pas seulement de la fuite",
          tenu: (fin, s) => {
            const si = pic(s, (r) => r.jambes["sidération"]);
            return si === 0 ? null : si >= pic(s, (r) => r.jambes["fuite"]);
          } },
      ],
    },
    {
      n: 11, id: "rupture-unite",
      nom: "Rupture d'unité — jugement collectif",
      quoi: "Le jumeau de l'epreuve 4, meme mise en place au corps pres, plus " +
            "le jugement d'unité désormais porté par le moteur. On compare les " +
            "deux : tout écart vient de cette règle et de rien d'autre. Ce qu'elle " +
            "change : la rupture cesse d'etre un fait d'HOMME pour devenir un " +
            "fait d'UNITE. Aujourd'hui `fuite` est multipliee par l'emprise — " +
            "la glande, nulle dans 93,7 % des coups d'oeil — donc elle n'est " +
            "disponible que par breves pointes, et `plante` gagne le reste du " +
            "temps. Nous avons branche la fuite sur la PANIQUE quand les " +
            "sources la decrivent comme un JUGEMENT.",
      forces: "Les memes deux vintaines que l'epreuve 4, vingt contre vingt.",
      terrain: "La meme rue intra muros, trouvee de la meme facon.",
      passe: "Une unite rompt AVANT d'etre detruite, et le vainqueur s'en tire " +
             "a moins de 15 % de morts.",
      echelle: 0.05, duree: 180,
      avant: (B) => { const c = parId("croisee"); if (c && c.avant) c.avant(B); },

      // ═══ LA REGLE — RELATIVE, ET C'EST LA MESURE QUI L'A IMPOSEE ═════════
      //
      // PREMIERE VERSION : un seuil ABSOLU de pertes (0,35). Deux defauts.
      // D'abord le dossier est formel qu'aucun seuil de pertes n'est atteste —
      // les 5 % sont un total de fin de bataille, pas un point de rupture.
      // Ensuite, mesure faite, il cassait LES DEUX CAMPS a quinze et vingt
      // secondes : un seuil absolu ne sait pas dire qui perd.
      //
      // CE QUE SABIN DONNE A LA PLACE : « le moral des deux formations opposees
      // est etroitement lie ». La rupture est un JUGEMENT COMPARATIF — on rompt
      // parce que l'autre tient mieux, pas parce qu'on a franchi un compte. Un
      // seuil relatif ne peut donc, par construction, faire rompre qu'un camp.
      // Verifie : la forme relative ne casse que la garde, la forme absolue les
      // deux.
      //
      // ⚠ CE QUE LE BALAYAGE A MONTRE, ET QUI COMPTE PLUS QUE LA MARGE. Six
      // variantes — absolu 0,35 / 0,45 / 0,55 et relatif 0,15 / 0,25 / 0,35 —
      // rompent TOUTES entre quinze et vingt secondes. Le seuil ne regle pas le
      // MOMENT, seulement combien on meurt avant. Ce n'est donc pas lui le
      // verrou : c'est la letalite. A points de vie multiplies par cinq, la meme
      // regle rend 10 % de morts chez le vainqueur et 20 % chez le vaincu — la
      // fourchette attestee — et UN SEUL mort au moment de la bascule, ce qui
      // est exactement ce que le dossier decrit.
      //
      // La marge ci-dessous reste donc SANS SOURCE, et sans importance tant que
      // la letalite n'a pas bouge. On la garde basse pour ne pas ajouter un
      // second effet a celui qu'on veut mesurer.
      pendant: (B, r) => {
        const MARGE = 0.15;        // SANS SOURCE — et le balayage dit qu'elle pese peu
        const DEBUT = 20;          // on ne juge pas l'autre avant de l'avoir vu tenir
        if (r.temps < DEBUT) return;
        const t = B.troupe(), par = {};
        for (const h of t) {
          const c = par[h.camp] || (par[h.camp] =
            { total: 0, lachent: 0, vifs: [] });
          c.total++;
          if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
          c.vifs.push(h);
          if (h.etat === "repli" || (h.l1 && h.l1.jambes === "recul")) c.lachent++;
        }
        const camps = Object.keys(par);
        if (camps.length < 2) return;
        // LA TENUE : ce qu'il reste d'hommes qui poussent encore, sur l'effectif
        // de depart. Elle tombe par les morts ET par ceux qui cedent le pas —
        // « les rangs arriere cessent de pousser, le centre doute, le front se
        // relache ». Un homme qui recule ne saigne pas, mais il retire sa part.
        const tenue = (k) => (par[k].vifs.length - par[k].lachent) / par[k].total;
        for (const k of camps) {
          const c = par[k], autre = camps.filter((x) => x !== k)[0];
          if (!c.vifs.length) continue;
          if (tenue(k) >= tenue(autre) * (1 - MARGE)) continue;
          const fx = c.vifs.reduce((n, h) => n + (h.fx || 0), 0);
          const fy = c.vifs.reduce((n, h) => n + (h.fy || 0), 0);
          B.jugerRuptureUnite(c.vifs, {
            menaceVue: 1, riposte: 0, fermeture: 1,
            severite: Math.min(1, 0.30 + Math.max(0,
              1 - tenue(k) / Math.max(0.01, tenue(autre)))),
            avantX: fx, avantY: fy,
            cause: "l'autre ligne tient mieux et la nôtre cesse de pousser",
          });
          if (!B._rupture) B._rupture = {};
          if (!B._rupture[k])
            B._rupture[k] = { t: r.temps, morts: r.morts, tenue: +tenue(k).toFixed(2) };
        }
      },
      sondes: [
        { dit: "une unite a rompu",
          tenu: (fin) => fin.fuyards > 0 || !!(fin.etats && fin.etats["deroute"]) },
        { dit: "elle a rompu avant d'etre detruite",
          tenu: (fin, s2) => {
            const p = pic(s2, (x) => x.morts) / (s2[0].vivants || 1);
            return p === 0 ? null : p < 0.5;
          } },
        { dit: "le vainqueur s'en tire a moins de 15 % de morts",
          tenu: (fin) => {
            const c = fin.parCamp || {}, noms = Object.keys(c);
            if (noms.length < 2 || fin.morts === 0) return null;
            const vq = noms.sort((x, y) => c[y].vivants - c[x].vivants)[0];
            return c[vq].morts / (c[vq].total || 1) < 0.15;
          } },
      ],
    },
  ];

  for (const s of DYNAMIQUES) {
    s.famille = s.famille || "Dynamique du combat";
    s.question = s.question || s.quoi.split(". ")[0] + " ?";
    s.regarder = s.regarder || "Observez les proportions dans les sondes à droite et " +
      "pointez les hommes qui composent le pic : le verdict seul ne suffit pas.";
    s.manipulation = s.manipulation || "La scène impose l'échelle et la durée indiquées, " +
      "puis relève le même état toutes les cinq secondes.";
  }
  const LISTE = COMMANDES.concat(DYNAMIQUES);

  const parId = (id) => LISTE.filter((s) => s.id === id)[0] || null;

  /**
   * Jouer une épreuve de bout en bout.
   * @param opts { mesure, pas, aChaque(relevé), attendre(relevé) }
   *
   * ⚠ `async` POUR LE NAVIGATEUR. `B.pas()` est synchrone : sept minutes de
   * bataille tiennent le fil d'exécution du début à la fin, donc rien ne se
   * peint et la page a l'air plantée. `attendre` est le point où l'appelant
   * rend la main à l'écran ; le banc headless ne le passe pas.
   */
  /**
   * METTRE EN PLACE, ET S'ARRÊTER LÀ. C'est la moitié de `jouer` qu'on veut
   * souvent seule : poser la condition, puis REGARDER — avancer à la main,
   * marcher, mettre en pause, tourner autour. Dérouler l'épreuve entière et la
   * juger est l'autre geste, et il n'a aucune raison d'être le seul offert :
   * on ne comprend pas une épreuve en lisant son verdict.
   *
   * Rend le relevé de départ, qui dit ce que la mise en place a déjà cassé
   * avant que personne n'ait bougé.
   */
  function poser(B, sc) {
    const s = typeof sc === "string" ? parId(sc) : sc;
    if (!s) throw new Error("épreuve inconnue : " + sc);
    if (s.echelle && B.echelle() !== s.echelle) B.echelle(s.echelle);
    B.rejouer(s.porte || undefined);
    if (s.avant) s.avant(B);
    return relever(B);
  }

  async function jouer(B, sc, opts) {
    const s = typeof sc === "string" ? parId(sc) : sc;
    if (!s) throw new Error("épreuve inconnue : " + sc);
    const o = opts || {};
    poser(B, s);
    // La mesure bat a cinq secondes : c'est la fenetre de `frappeurs`. `pas`
    // ne regle que la frequence a laquelle le navigateur repeint.
    const bond = o.mesure || 5, peinture = o.pas || 30;
    let prochainePeinture = peinture;
    const suite = [];
    // Le relevé de DÉPART compte autant que celui d'arrivée : c'est lui qui dit
    // ce que la mise en place a déjà cassé avant que personne n'ait bougé.
    let r = relever(B);
    suite.push(r); if (o.aChaque) o.aChaque(r);
    if (o.attendre) await o.attendre(r);
    while (r && r.temps < s.duree) {
      B.pas(Math.min(bond, s.duree - r.temps));
      r = relever(B);
      // LE CROCHET D'EXPERIENCE. Il laisse une epreuve appliquer une regle qui
      // n'est PAS dans le moteur, pour l'eprouver avant de decider si elle y
      // entre. Reversible, isole, sans collision avec le fichier du moteur. Une
      // regle qui survit ici merite d'y etre ecrite ; une regle qui meurt ici
      // n'aura coute qu'une epreuve.
      if (s.pendant) s.pendant(B, r);
      suite.push(r); if (o.aChaque) o.aChaque(r);
      if (o.attendre && (r.temps + 1e-9 >= prochainePeinture || r.temps >= s.duree)) {
        await o.attendre(r); prochainePeinture += peinture;
      }
    }
    return { epreuve: s.id, n: s.n, suite, fin: r, verdicts: juger(s, suite) };
  }

  /**
   * Les sondes contre la série entière. `null` = la question ne se pose pas —
   * et ce n'est PAS « ça va » : une sonde qui ne peut pas répondre doit le dire,
   * sinon une épreuve qui n'a rien exercé se lit comme une épreuve réussie.
   */
  function juger(s, suite) {
    if (!suite || !suite.length) return [];
    const fin = suite[suite.length - 1];
    return (s.sondes || []).map((p) => {
      let t; try { t = p.tenu(fin, suite); } catch (e) { t = null; }
      let observe = null;
      try { observe = p.mesure ? p.mesure(fin, suite) : null; } catch (e) { observe = null; }
      return { dit: p.dit, tenu: t, attendu: p.attendu || null, observe };
    });
  }

  racine.BatailleScenarios = { LISTE, parId, relever, poser, jouer, juger };
  if (typeof module === "object" && module.exports) module.exports = racine.BatailleScenarios;

})(typeof window !== "undefined" ? window : globalThis);
