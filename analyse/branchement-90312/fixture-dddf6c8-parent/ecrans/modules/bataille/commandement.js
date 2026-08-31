// commandement.js — ce qu'un chef croit, et ce qu'il peut en dire.
//
// Cette feuille ne connaît ni maison, ni porte, ni aile. Elle conserve des
// faits situés et sourcés, en tire des croyances vieillissantes et permet à
// deux mémoires de s'échanger ce qu'elles ont réellement appris. La doctrine
// reste chez l'appelant : savoir qu'un ennemi est probablement là ne dit pas
// encore s'il faut l'attaquer, l'éviter ou tenir devant lui.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleCommandement = api;
})(typeof window !== "undefined" ? window : globalThis, function () {
  const borner = (x, a, b) => Math.max(a, Math.min(b, x));

  function memoire(opts) {
    opts = opts || {};
    return {
      proprietaire:opts.proprietaire || null,
      echelon:opts.echelon || "unite",
      camp:opts.camp || null,
      ordre:null,
      faits:new Map(),
      croyances:new Map(),
      communications:[],
    };
  }

  function recevoirOrdre(m, ordre, maintenant) {
    if (!m || !ordre) return null;
    const o = typeof ordre === "string" ? { texte:ordre } : Object.assign({}, ordre);
    o.recuA = Number.isFinite(maintenant) ? maintenant : 0;
    m.ordre = o;
    return o;
  }

  function cleSujet(f) {
    if (f.sujet && f.sujet.id != null)
      return (f.sujet.genre || "sujet") + ":" + f.sujet.id;
    if (f.zone && f.zone.id != null) return "zone:" + f.zone.id;
    return (f.genre || "fait") + ":" + (f.id || "sans-id");
  }

  function confiance(c, maintenant) {
    const t = Number.isFinite(maintenant) ? maintenant : c.misAJourA || c.observeA || 0;
    const age = Math.max(0, t - (c.misAJourA || c.observeA || t));
    const horizon = c.source === "vu" ? 420 : 210;
    return Math.max(.08, c.confiance * Math.exp(-age / horizon));
  }

  function assimiler(m, fait, maintenant, transmission) {
    if (!m || !fait || !fait.id) return null;
    const f = Object.assign({}, fait);
    f.source = transmission && transmission.source || f.source || "vu";
    f.apprisDe = transmission && transmission.apprisDe || f.apprisDe || null;
    f.auteur = f.auteur || (transmission && transmission.auteur) || m.proprietaire;
    f.observeA = Number.isFinite(f.observeA) ? f.observeA : maintenant;
    m.faits.set(f.id, f);

    const cle = cleSujet(f), ancien = m.croyances.get(cle);
    const directe = f.source === "vu";
    // Une parole plus vieille ne défait pas ce que le chef a vu lui-même.
    if (ancien && ancien.source === "vu" && !directe &&
        ancien.observeA >= f.observeA) return ancien;

    const c = {
      id:cle, genre:f.genre || "inconnu", sujet:f.sujet || null,
      zone:f.zone || null, position:f.position || null,
      statut:f.statut || "possible",
      forceMin:Number.isFinite(f.forceMin) ? Math.max(0, f.forceMin) : 0,
      forceMax:Number.isFinite(f.forceMax) ? Math.max(0, f.forceMax) : 0,
      confiance:borner(Number.isFinite(f.confiance) ? f.confiance
        : directe ? (f.statut === "actif" ? 1 : .92)
          : (f.statut === "actif" ? .72 : .64), .05, 1),
      source:f.source, auteur:f.auteur, apprisDe:f.apprisDe,
      observeA:f.observeA, misAJourA:maintenant, fait:f.id,
      texte:f.texte || null,
      // Des indices observables, pas un type d'unité omniscient : silhouettes
      // montées et longues hampes peuvent être vus, mal comptés, transmis et
      // vieillir comme le reste du renseignement.
      signatures:f.signatures ? Object.assign({}, f.signatures) : null,
    };
    m.croyances.set(cle, c);
    return c;
  }

  function inconnusPour(source, destination) {
    if (!source || !destination) return [];
    return [...source.faits.values()].filter((f) => !destination.faits.has(f.id));
  }

  function transmettre(source, destination, opts) {
    opts = opts || {};
    if (!source || !destination) return [];
    const recus = [];
    const choix = opts.faits || inconnusPour(source, destination);
    for (const f of choix) {
      if (!f || destination.faits.has(f.id)) continue;
      const recu = Object.assign({}, f, {
        source:"dit", apprisDe:source.proprietaire,
        // L'auteur racine ne change jamais : trois répétitions d'une même
        // rumeur ne deviennent pas trois confirmations indépendantes.
        auteur:f.auteur || source.proprietaire,
      });
      destination.faits.set(recu.id, recu);
      assimiler(destination, recu, opts.maintenant || 0,
        { source:"dit", apprisDe:source.proprietaire, auteur:recu.auteur });
      recus.push(recu);
    }
    return recus;
  }

  function estimation(m, forcePropre, maintenant, filtre) {
    const actifs = !m ? [] : [...m.croyances.values()].filter((c) =>
      c.genre === "ennemi" && c.statut === "actif" &&
      confiance(c, maintenant) >= .22 && (!filtre || filtre(c)));
    const forceMin = Math.round(actifs.reduce((n, c) =>
      n + c.forceMin * confiance(c, maintenant), 0));
    const forceMax = Math.ceil(actifs.reduce((n, c) =>
      n + c.forceMax * confiance(c, maintenant), 0));
    const propre = Math.max(0, forcePropre || 0);
    let rapport = "inconnu";
    if (actifs.length && forceMin > propre * 1.1) rapport = "inferieur";
    else if (actifs.length && forceMax <= propre * .6) rapport = "superieur";
    else if (actifs.length) rapport = "incertain";
    const signatures = {};
    for (const c of actifs) for (const [nom, intervalle] of
      Object.entries(c.signatures || {})) {
      const q = confiance(c, maintenant), v = intervalle || {};
      const x = signatures[nom] || (signatures[nom] = { min:0, max:0 });
      x.min += Math.max(0, v.min || 0) * q;
      x.max += Math.max(0, v.max || 0) * q;
    }
    for (const x of Object.values(signatures)) {
      x.min = Math.floor(x.min); x.max = Math.ceil(x.max);
    }
    return { forcePropre:propre, forceMin, forceMax, lieux:actifs.length,
             rapport, signatures };
  }

  function direEstimation(e) {
    if (!e || !e.lieux) return "J'ai " + (e ? e.forcePropre : 0) +
      " hommes debout et aucun ennemi localisé avec assez de certitude.";
    return "J'ai " + e.forcePropre + " hommes debout. J'estime " + e.forceMin +
      " à " + e.forceMax + " ennemis possibles dans " + e.lieux +
      (e.lieux > 1 ? " zones." : " zone.");
  }

  function tracerCommunication(m, communication) {
    if (!m || !communication) return;
    m.communications.push(communication);
    if (m.communications.length > 80) m.communications.shift();
  }

  // CE QU'UN CHEF PEUT VOIR, PAS CE QUI EXISTE. Le champ est un éventail de
  // distances arrêtées par le premier obstacle. Il est volontairement
  // indépendant du plan de Port-Réal : l'appelant fournit seulement la
  // question `obstacle(x,y)`. Le même geste sert donc dans une rue, un bois,
  // derrière une crête ou sur un banc sans terrain.
  function champVision(opts) {
    opts = opts || {};
    const p = opts.position || { x:0, y:0 };
    const rayon = Math.max(1, +opts.rayon || 65);
    const nombre = Math.max(12, Math.round(+opts.rayons || 48));
    const pas = Math.max(.5, +opts.pas || 1.5);
    const obstacle = typeof opts.obstacle === "function" ? opts.obstacle : null;
    const rayons = [];
    let bloques = 0;
    for (let i = 0; i < nombre; i++) {
      const angle = -Math.PI + (i + .5) * Math.PI * 2 / nombre;
      const ux = Math.cos(angle), uy = Math.sin(angle);
      let porte = rayon, bloque = false;
      if (obstacle) for (let d = pas; d <= rayon; d += pas) {
        if (!obstacle(p.x + ux * d, p.y + uy * d)) continue;
        porte = Math.max(0, d - pas * .5); bloque = true; bloques++; break;
      }
      rayons.push({ angle, x:p.x + ux * porte, y:p.y + uy * porte,
                    portee:porte, bloque });
    }
    return { origine:{ x:p.x, y:p.y }, rayon, pas, rayons, bloques };
  }

  function visibleDansChamp(champ, position, marge) {
    if (!champ || !champ.rayons || !champ.rayons.length || !position) return true;
    const dx = position.x - champ.origine.x, dy = position.y - champ.origine.y;
    const d = Math.hypot(dx, dy);
    if (d > champ.rayon) return false;
    let a = Math.atan2(dy, dx) + Math.PI;
    if (a >= Math.PI * 2) a -= Math.PI * 2;
    const i = Math.max(0, Math.min(champ.rayons.length - 1,
      Math.floor(a / (Math.PI * 2) * champ.rayons.length)));
    return d <= champ.rayons[i].portee + Math.max(0, +marge || 0);
  }

  // LE GRAPHE TACTIQUE N'EST PAS UNE DOCTRINE. Il ne contient aucune règle
  // « si telle arme, alors telle manœuvre » : il rend seulement explicites les
  // relations géométriques déjà présentes dans la mémoire du chef. Une
  // croyance peut être vue ou rapportée, exercer une pression estimée, se
  // trouver sur l'axe de l'ordre ou près de l'objectif. Une stratégie pourra
  // plus tard reconnaître une configuration dans ce graphe sans que celui-ci
  // connaisse ni cavalerie, ni piques, ni scénario C6.
  function grapheTactique(m, opts) {
    opts = opts || {};
    if (!m) return null;
    const maintenant = Number.isFinite(opts.maintenant) ? opts.maintenant : 0;
    const soi = opts.position || { x:0, y:0 };
    const objectif = opts.objectif && Number.isFinite(opts.objectif.x) &&
      Number.isFinite(opts.objectif.y) ? opts.objectif : null;
    const champ = opts.champ || champVision({ position:soi, rayon:opts.rayon,
      rayons:opts.rayons, pas:opts.pas, obstacle:opts.obstacle });
    const noeuds = [{ id:"soi", type:"commandant", position:{ x:soi.x, y:soi.y },
      nom:opts.nom || m.proprietaire, camp:m.camp, echelon:m.echelon }];
    const liens = [];
    if (objectif) {
      noeuds.push({ id:"objectif", type:"objectif",
        position:{ x:objectif.x, y:objectif.y }, nom:objectif.nom || "objectif" });
      liens.push({ de:"soi", vers:"objectif", type:"ordre", poids:1 });
    }
    const interlocuteurs = new Set();
    for (const c of m.communications || []) {
      if (c.de != null) interlocuteurs.add(String(c.de));
      if (c.vers != null) interlocuteurs.add(String(c.vers));
    }
    for (const a of opts.allies || []) {
      if (!a || a.id == null || String(a.id) === String(m.proprietaire) ||
          !a.position || !interlocuteurs.has(String(a.id))) continue;
      const id = "allie:" + a.id;
      noeuds.push({ id, type:"commandant-allie", position:{ x:a.position.x, y:a.position.y },
        nom:a.nom || a.id, echelon:a.echelon || null });
      liens.push({ de:"soi", vers:id, type:"communique", poids:1 });
    }
    const ox = objectif ? objectif.x - soi.x : 0;
    const oy = objectif ? objectif.y - soi.y : 0;
    const ol2 = ox * ox + oy * oy;
    const croyances = [...m.croyances.values()].map((c) => ({
      croyance:c, confiance:confiance(c, maintenant),
    })).filter((q) => q.croyance.position && q.confiance >= .08);
    for (const q of croyances) {
      const c = q.croyance, id = "croyance:" + c.id;
      const position = { x:c.position.x, y:c.position.y };
      const distance = Math.hypot(position.x - soi.x, position.y - soi.y);
      noeuds.push({ id, type:c.genre, position, statut:c.statut,
        confiance:+q.confiance.toFixed(3), source:c.source,
        force:{ min:c.forceMin || 0, max:c.forceMax || 0 },
        signatures:c.signatures || {}, texte:c.texte || null,
        age:Math.max(0, maintenant - (c.misAJourA || c.observeA || maintenant)) });
      liens.push({ de:"soi", vers:id,
        type:c.source === "vu" ? "observe" : "rapporte",
        poids:+q.confiance.toFixed(3) });
      if (c.genre === "ennemi" && c.statut === "actif") {
        const pression = q.confiance * Math.max(1, c.forceMax || 1) /
          Math.max(8, distance);
        liens.push({ de:id, vers:"soi", type:"pression",
          poids:+pression.toFixed(3) });
        if (objectif) {
          const dobst = Math.hypot(position.x - objectif.x, position.y - objectif.y);
          if (dobst <= Math.max(18, distance * .28))
            liens.push({ de:id, vers:"objectif", type:"conteste",
              poids:+(q.confiance / Math.max(1, dobst / 12)).toFixed(3) });
          if (ol2 > 1) {
            const t = Math.max(0, Math.min(1,
              ((position.x-soi.x)*ox + (position.y-soi.y)*oy) / ol2));
            const px = soi.x + ox*t, py = soi.y + oy*t;
            const ecart = Math.hypot(position.x-px, position.y-py);
            if (t > .08 && t < .98 && ecart <= 16)
              liens.push({ de:id, vers:"objectif", type:"occupe-axe",
                poids:+(q.confiance * (1-ecart/16)).toFixed(3) });
          }
        }
      }
    }
    return {
      proprietaire:m.proprietaire, echelon:m.echelon, camp:m.camp,
      ordre:m.ordre && m.ordre.texte || null, maintenant,
      champ, noeuds, liens,
      resume:{ croyances:croyances.length,
        ennemis:croyances.filter((q) => q.croyance.genre === "ennemi" &&
          q.croyance.statut === "actif").length,
        rayonsBloques:champ.bloques,
        rayons:champ.rayons.length },
    };
  }

  // Former un échelon de chefs autour d'un repère supérieur. L'ordre latéral
  // vient de leurs positions d'approche afin qu'ils ne se croisent pas pour
  // rejoindre une place arbitraire. Seuls les chefs reçoivent une place ; leurs
  // unités restent libres de se former derrière eux selon leur propre modèle.
  function formerEchelon(opts) {
    opts = opts || {};
    const ancre = opts.ancre || { x:0, y:0 }, front = opts.front || { x:ancre.x+1, y:ancre.y };
    let fx = front.x-ancre.x, fy = front.y-ancre.y, d = Math.hypot(fx,fy) || 1;
    fx /= d; fy /= d;
    const tx = -fy, ty = fx, espacement = opts.espacement || 10;
    const elements = (opts.elements || []).slice().sort((a,b) =>
      ((a.x-ancre.x)*tx + (a.y-ancre.y)*ty) - ((b.x-ancre.x)*tx + (b.y-ancre.y)*ty));
    const places = [];
    for (let i=0;i<elements.length;i++) {
      const lateral = (i-(elements.length-1)/2)*espacement;
      const ideal = { x:ancre.x+tx*lateral, y:ancre.y+ty*lateral };
      let choisi = ideal;
      if (opts.libre && !opts.libre(ideal.x,ideal.y)) {
        for (const recul of [-2,2,-4,4,-6,6]) {
          const p={ x:ideal.x-fx*recul, y:ideal.y-fy*recul };
          if (opts.libre(p.x,p.y)) { choisi=p; break; }
        }
      }
      places.push({ id:elements[i].id, x:choisi.x, y:choisi.y, fx, fy, rang:i });
    }
    return places;
  }

  return { memoire, recevoirOrdre, assimiler, transmettre, inconnusPour,
           confiance, estimation, direEstimation, tracerCommunication,
           champVision, visibleDansChamp, grapheTactique, formerEchelon };
});
