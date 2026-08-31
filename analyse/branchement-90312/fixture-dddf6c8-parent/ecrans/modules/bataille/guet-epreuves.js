// guet-epreuves.js — LE GUET : une famille d'épreuves d'un autre genre.
//
// CE QUI LA DISTINGUE DES AUTRES, ET IL FAUT LE DIRE EN TÊTE. Toutes les
// épreuves de `scenarios.js` partent de la nuit de la Gadoue et la DÉFORMENT :
// elles font tourner le moteur et jugent ce qui en sort. Celle-ci ne fait
// tourner aucun moteur. Le Guet n'est pas une bataille — c'est une INSTITUTION,
// et ce qu'on veut savoir d'elle est si elle TIENT DEBOUT : les postes sont-ils
// là où on les dit, les rondes bouclent-elles, un homme peut-il venir frapper à
// trois heures du matin, et quelle part de la ville est réellement à portée.
//
// Elle lit donc le monde cuit (`/monde/plan2d`, couche `guettes`, écrite par
// `scripts/monde/guet.py`) et le confronte à ce que le dossier de recherche
// exige. C'est une épreuve de VÉRACITÉ, pas de comportement — et c'est le bon
// outil pour la question posée : une institution incohérente sur le papier ne
// produira jamais une scène juste, quelque soin qu'on mette à la jouer.
//
// ═══ D'OÙ VIENNENT LES SEUILS ═══════════════════════════════════════════════
// De `docs/recherche/les-gardes-et-patrouilles-de-ville.md`, et de nulle part
// ailleurs — même règle que `scenarios.js`. Chaque sonde cite sa section.
"use strict";
(function (racine) {

  const EPREUVE_GUETTES = Object.freeze({
    id: "guet-guettes", n: "G1", famille: "Le Guet — postes et rondes",
    guet: true, echelle: "—", duree: 0,
    nom: "Les guettes tiennent (postes + rondes)",
    question: "Seize postes de quartier, leurs rondes calculées sur les rues : " +
              "est-ce que ça tient debout, et qu'est-ce que ça laisse dehors ?",
    quoi: "Le Guet de Port-Réal compte 2 079 manteaux d'or. Neuf cents tiennent la ville " +
          "la nuit depuis seize guettes posées sur des carrefours nommés ; leurs circuits " +
          "sont calculés sur le graphe des rues, six secteurs et l'on referme.",
    regarder: "LA VILLE, PAS LE TABLEAU. Neuf cents hommes sont là : six cent soixante " +
              "et onze massés devant leurs postes, deux cent vingt-huit qui marchent par " +
              "paires — le rapport de trois pour un se VOIT, on n'a pas à le dire. Aucun " +
              "circuit n'est tracé au sol, parce qu'aucun ne l'est dans le monde : passez " +
              "sur un poste OU sur une paire en chemin, et sa boucle apparaît avec sa " +
              "fraîcheur. Le point orange est la guette du Dragon-Tombé, la seule qui " +
              "n'entende aucun tocsin. Les verdicts sont à droite, en second.",
    manipulation: "« Poser » vide la bataille, cadre la ville et lâche les rondes ; " +
                  "« Mesurer » juge en plus. LA VUE EST CELLE DE LA BATAILLE — même " +
                  "caméra, même molette, même glissé — et l'allure suit la barre : à ×1 " +
                  "un homme fait ses 78 m par minute, donc un tour de quarante minutes " +
                  "prend quarante minutes. Prenez ×5 pour voir une nuit. La couche " +
                  "`guettes` se refait par `python scripts/monde/guet.py --lieu " +
                  "port-real --appliquer` après toute cuisson du plan.",
    forces: "Seize guettes · 900 hommes de nuit · 16 circuits",
    terrain: "Port-Réal entière, dans les murs et les faubourgs.",
    passe: "Seize guettes posées, seize boucles fermées de 25 à 45 minutes, trois hommes " +
           "au poste pour un en ronde, jamais moins de huit au poste, et les trois quarts " +
           "des toits à moins de sept minutes de marche.",
  });

  // ═══ G2 — LA RETRAITE ═════════════════════════════════════════════════════
  // L'épreuve qui prouve le § 0 du dossier, et la seule qui le puisse : ON NE
  // GARDE PAS UNE VILLE EN LA SURVEILLANT, ON LA VIDE. G1 montre les hommes du
  // Guet ; celle-ci montre CE QU'ILS GARDENT — la ville pleine à la tombée du
  // jour, la cloche de l'Aïeule, et la rue qui se vide en trois quarts d'heure
  // pour ne plus laisser dehors que des manteaux d'or.
  //
  // LA FOULE EST RÉELLE, pas un semis d'ambiance : on charge de vraies cellules
  // d'habitants (`monde/gens.js`) et l'on demande à `journee.js` ce que chacun
  // fait à cette minute-là — la même fonction qui fait marcher la ville dans la
  // partie. Ce qu'on simplifie, et il faut le dire : on pose l'homme À SON
  // ADRESSE plutôt que de l'interpoler le long de sa rue. On voit donc les gens
  // AUX puits, aux tavernes et aux étals, pas leurs trajets. C'est assez pour
  // la question posée, et ça évite de charger la voirie entière pour un banc.
  //
  // ON NE DESSINE QUE CE QUI EST À CIEL OUVERT. Un homme attablé dans une
  // taverne est sous un toit : le peindre, c'est poser un point dans la pierre.
  // La table des besoins dit lesquels comptent (`plein_air`).

  const EPREUVE_RETRAITE = Object.freeze({
    id: "guet-retraite", n: "G2", famille: "Le Guet — postes et rondes",
    guet: true, foule: true, echelle: "—", duree: 0,
    nom: "La retraite — la ville se vide, le Guet reste",
    question: "Au coup de l'Aïeule, la rue se vide-t-elle vraiment — et que " +
              "reste-t-il dehors une heure après ?",
    quoi: "Vingt et une heures. L'Aïeule sonne la retraite : on couvre les braises, " +
          "on ferme les portes, on vide les tavernes. Les habitants rentrent avec " +
          "les quelques minutes qu'il leur faut ; les seize guettes, elles, prennent " +
          "la rue pour la nuit.",
    regarder: "LE PIC, PUIS LA PENTE. La ville se remplit jusqu'au coup de cloche — " +
              "c'est la minute la plus chargée de la journée — puis les points " +
              "s'éteignent quartier par quartier. Une heure plus tard il ne reste " +
              "QUE le Guet : neuf cents hommes dans une ville de quatre cent mille " +
              "qui dort. C'est ça, une ville gardée.",
    manipulation: "L'horloge part de dix-neuf heures et court jusqu'au matin. La " +
                  "foule vient de vraies cellules d'habitants et de `journee.js` — " +
                  "la même fonction que la partie. Le couvre-feu se règle dans " +
                  "`scripts/monde/besoins.py` (`COUVRE_FEU`) et se recuit par " +
                  "`python scripts/monde/besoins.py`.",
    forces: "~900 hommes du Guet · un échantillon d'habitants réels",
    terrain: "Port-Réal, du crépuscule au point du jour.",
    passe: "La rue se remplit jusqu'à la retraite, se vide en moins d'une heure, et " +
           "au cœur de la nuit il ne reste dehors que des hommes du Guet.",
  });

  // ── LA FOULE ──────────────────────────────────────────────────────────────
  let foule = null, foulePrete = false, cfCourant = null;

  async function chargerFoule(plan) {
    if (foule) return foule;
    const [G, J] = await Promise.all([
      import("/modules/monde/gens.js"), import("/modules/monde/journee.js")]);
    const t = await J.table("/monde");
    const m = await G.manifeste("/monde");
    const rangs = J.rangs(m);
    const b = plan.bornes || [0, 0, 5280, 3600];
    const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
    // Un rayon large, mais on ÉCHANTILLONNE : quatre cent mille corps ne se
    // peignent pas, et n'apprendraient rien de plus que quatre mille.
    const cellules = await G.autour(cx, cy, 1800, "/monde");
    const dehors = new Set(t.plein_air || []);
    foule = { J, t, rangs, cellules, dehors,
              portes: t.portes || [], pas: 0 };
    // Le pas d'échantillonnage se règle sur la population chargée, pour tomber
    // sur quelques milliers de points quelle que soit la taille du lot.
    const total = cellules.reduce((s, c) => s + c.n, 0);
    foule.pas = Math.max(1, Math.round(total / 4000));
    foule.total = total;
    cfCourant = t.couvre_feu || null;
    foulePrete = true;
    return foule;
  }

  // DEHORS VEUT DIRE « HORS DE CHEZ SOI », et c'est le seul sens qui réponde à
  // la question. La première version ne comptait que les gens à CIEL OUVERT —
  // les puits, les étals — et rendait zéro à toute heure du soir : à vingt
  // heures, tout le monde est à la taverne, c'est-à-dire sous un toit. On
  // mesurait donc scrupuleusement une chose vraie qui ne disait rien du
  // couvre-feu, lequel n'interdit pas d'être dehors : il interdit de ne pas
  // être chez soi.
  //
  // Ce qu'on concède au passage, et il faut le dire : on pose l'homme à la
  // PORTE de son adresse, sur la chaussée, plutôt qu'à sa table. Un point sur
  // le seuil d'une taverne vaut mieux qu'un point dans sa cave, et l'on évite
  // de charger la voirie entière pour interpoler des trajets sur un banc.
  function dehorsA(f, cel, k, jour, minute) {
    const etapes = f.J.journee(cel, k, jour, f.rangs);
    for (const e of etapes) {
      if (e.debut > minute) break;
      if (minute >= e.fin) continue;
      // LE GUET N'EST PAS UN HABITANT DEHORS. Il est dans l'échantillon comme
      // tout le monde — deux mille sur quatre cent mille — et le couvre-feu le
      // laisse passer, à raison. Comptés avec les autres, ils faisaient dix-neuf
      // « habitants encore dehors » à deux heures du matin, à toute heure et
      // pour toujours : la sonde accusait la ville de ce qui EST la réponse.
      // Ils sont déjà peints, et par-dessus, comme manteaux d'or.
      if (e.service === "poste" || e.service === "ronde") return null;
      const p = f.portes[e.bat];
      return p ? [p[0], p[1]] : null;
    }
    return null;
  }

  // ── LES SONDES ────────────────────────────────────────────────────────────
  // `tenu` vaut true, false, ou null pour « sans objet » — la même convention
  // que `scenarios.js`, pour que `bilan()` n'ait pas à distinguer les familles.
  function verdicts(plan) {
    const G = (plan && plan.guettes) || [];
    const meta = (plan && plan.guet_meta) || {};
    const d = meta.desserte || {};
    const cloches = (plan && plan.cloches) || [];
    const out = [];
    const dire = (dit, attendu, tenu, observe) => out.push({ dit, attendu, tenu, observe });

    if (!G.length) {
      dire("le monde cuit porte une couche « guettes »", "16 guettes", false,
           "aucune — lancer scripts/monde/guet.py --appliquer");
      return out;
    }

    // 1 — les postes existent et sont adressés
    const nommees = G.filter((g) => g.carrefour && g.nom).length;
    dire("seize guettes, chacune sur un carrefour que la ville nomme déjà",
         "16 sur 16", G.length === 16 && nommees === 16,
         G.length + " guettes · " + nommees + " adressées");

    // 2 — une ronde est une BOUCLE (§ « un pour trois »)
    const avec = G.filter((g) => g.ronde && g.ronde.trace && g.ronde.trace.length > 2);
    const fermees = avec.filter((g) => {
      const t = g.ronde.trace, a = t[0], b = t[t.length - 1];
      return Math.hypot(a[0] - b[0], a[1] - b[1]) < 5;
    });
    dire("chaque ronde revient à son poste — une boucle, pas une étoile",
         "16 boucles fermées", avec.length === G.length && fermees.length === G.length,
         fermees.length + " fermées sur " + avec.length + " circuits");

    // 3 — la durée d'un tour. Une ronde plus courte qu'un quart d'heure n'est
    // pas une ronde, une ronde d'une heure laisse le poste trop longtemps seul.
    // LE TOUR, ARRETS COMPRIS — pas la marche pure. Un homme du guet pousse des
    // portes et parle a des gens ; ce qui decide de la frequence a laquelle une
    // rue revoit une patrouille est le tour reel, et c'est donc lui qu'on juge.
    const mn = avec.map((g) => g.ronde.minutes_tour || g.ronde.minutes)
                   .sort((a, b) => a - b);
    const hors = mn.filter((m) => m < 25 || m > 45).length;
    dire("un tour tient entre vingt-cinq et quarante-cinq minutes, arrêts compris",
         "25–45 min", mn.length > 0 && hors === 0,
         mn.length ? mn[0] + "–" + mn[mn.length - 1] + " min (médiane " +
                     mn[Math.floor(mn.length / 2)] + ")" : "aucun circuit");

    // 4 — le rapport poste/ronde (§ 9.1 : 76 % au poste, mesuré et conforme)
    const poste = G.reduce((s, g) => s + (g.au_poste || 0), 0);
    const rd = G.reduce((s, g) => s + (g.en_ronde || 0), 0);
    const rapport = rd ? poste / rd : 0;
    dire("trois hommes au poste pour un en ronde",
         "2,5 à 3,5", rapport >= 2.5 && rapport <= 3.5,
         rapport.toFixed(2) + " (" + poste + " au poste, " + rd + " en ronde)");

    // 5 — ON PEUT TOUJOURS VENIR FRAPPER. C'est ce qui fait d'un poste un poste,
    // et c'est la seule sonde dont l'échec se verrait immédiatement en scène.
    const creux = G.filter((g) => (g.au_poste || 0) < 8);
    dire("aucune guette ne descend sous huit hommes au poste",
         "≥ 8 partout", creux.length === 0,
         creux.length ? creux.length + " guette(s) trop maigres : " +
                        creux.map((g) => g.nom).join(", ")
                      : "minimum " + Math.min.apply(null, G.map((g) => g.au_poste)));

    // 6 — la desserte, mesurée sur les toits et jamais sur une surface
    const part = d.toits ? d.desservis / d.toits : 0;
    dire("les trois quarts des toits à moins de sept minutes de marche",
         "≥ 75 %", d.toits ? part >= 0.75 : null,
         d.toits ? Math.round(part * 1000) / 10 + " % · médiane " +
                   d.minutes_medianes + " min · d9 " + d.minutes_d9 + " min"
                 : "pas de mesure de desserte");

    // 7 — UNE RONDE SE RACONTE, et cette sonde a d'abord exigé DEUX rues nommées
    // par circuit. Elle échouait sur sept rondes sur seize, et la faute n'était
    // ni dans l'algorithme ni dans les guettes : PORT-RÉAL N'A QUE DIX-SEPT
    // RUES NOMMÉES pour 45 155 arêtes de voirie — 4,4 %, toutes des artères,
    // pendant que 42 000 rues et ruelles n'ont aucun nom. Un circuit de deux
    // kilomètres dans un quartier ne PEUT pas en traverser deux.
    //
    // On corrige donc l'attente, pas le seuil : ce qu'on exige d'une ronde est
    // qu'elle s'accroche à AU MOINS un nom qu'on puisse dire en scène. Et l'on
    // garde le chiffre qui explique tout sous les yeux, parce qu'il désigne le
    // vrai chantier — la toponymie, pas le Guet.
    const muettes = avec.filter((g) => !g.ronde.rues || g.ronde.rues.length < 1);
    const noms = avec.map((g) => (g.ronde.rues || []).length);
    dire("chaque ronde s'accroche à une rue qu'on peut nommer en scène",
         "≥ 1 rue nommée", muettes.length === 0,
         muettes.length ? muettes.length + " ronde(s) muettes"
                        : "de " + Math.min.apply(null, noms) + " à " +
                          Math.max.apply(null, noms) +
                          " · la ville n'a que 17 rues nommées sur 45 155 arêtes");

    // 8 — LE CROISEMENT AVEC LES CLOCHES, et c'est la sonde qui apprend quelque
    // chose. Le dossier mesure 1 059 toits sourds sur la colline de Rhaenys :
    // on ne sonne pas l'alarme sous les dragons. Une guette qui n'entend aucun
    // tocsin est un poste dont l'alarme arrive à pied — et il doit y en avoir.
    if (!cloches.length) {
      dire("le Guet et les cloches se croisent", "couche cloches", null,
           "pas de cloches cuites");
    } else {
      const alarme = cloches.filter((c) => c.tocsin);
      const sourdes = G.filter((g) => !alarme.some((c) =>
        Math.hypot(g.x - c.x, g.y - c.y) <= c.portee));
      dire("au moins une guette n'entend aucun tocsin — la colline de Rhaenys",
           "≥ 1 guette sourde", sourdes.length >= 1,
           sourdes.length ? sourdes.map((g) => g.nom).join(", ")
                          : "toutes les guettes entendent une alarme");
    }
    return out;
  }

  // ── LE RENDU ──────────────────────────────────────────────────────────────
  // LA FAMILLE PEINT SES PROPRES VERDICTS, et il le faut : `sondes-page.js`
  // commence par `Bataille2d.etat()` et sort aussitot si le moteur n'est pas
  // dresse, et sa boucle est gardee par `pret`. Un panneau qui ne s'affiche
  // qu'avec un moteur ne peut pas servir une famille qui s'en passe. On reprend
  // les memes classes — `verdict`, `ok`, `fort` — pour que la feuille de style
  // de la page s'applique sans une ligne de plus.
  const esc = (t) => String(t == null ? "" : t)
    .replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function peindre(cible, v, titre) {
    if (!cible) return;
    cible.innerHTML = "<h3>" + esc(titre || "Ce qu'on attendait") + "</h3>" +
      '<table class="verdicts">' + v.map((x) =>
        '<tr class="verdict ' + (x.tenu === true ? "ok" : x.tenu === false ? "fort" : "") +
        '"><td>' + esc(x.dit) +
        (x.attendu ? "<small>attendu : " + esc(x.attendu) + "</small>" : "") +
        '</td><td class="n">' +
        (x.observe != null ? esc(x.observe) + "<small>" : "") +
        (x.tenu === true ? "tenu" : x.tenu === false ? "NON" : "sans objet") +
        (x.observe != null ? "</small>" : "") +
        "</td></tr>").join("") + "</table>";
  }

  // ═══ LA VUE — CELLE DE LA BATAILLE, PAS UNE AUTRE ═════════════════════════
  // Première version : un SVG maison qui redessinait la ville à côté. Ça
  // marchait et c'était une faute — deux vues de la même ville divergent le
  // jour où l'une bouge, et celle-là n'avait ni la molette, ni le glissé, ni le
  // survol, ni l'allure réelle des hommes. On les avait déjà, en face.
  //
  // On pose donc une SURCOUCHE sur le canvas de `bataille2d`, dans SA
  // projection : la page tient la caméra (`vue`, un rectangle en mètres) et la
  // partage avec les deux. Zoom, glissé et cadrage viennent gratuitement, parce
  // que ce sont les siens. On ne dessine que ce que la bataille ne connaît pas
  // — les seize guettes, leurs circuits, et les hommes qui les parcourent.
  //
  // L'ALLURE EST CELLE D'UN HOMME : 78 m/min, soit 1,3 m/s, multipliée par la
  // vitesse de la barre (×1, ×2, ×5). À ×1, un tour de quarante minutes prend
  // quarante minutes. C'est long, et c'est le fait qu'on veut voir.

  const ALLURE = 78 / 60;        // mètres par seconde — l'allure de `journee.js`
  // Combien de temps une rue reste « fraîchement gardée » derrière une paire.
  // Choix d'affichage, pas un fait : il rend visible l'écart entre les guettes
  // riches et les maigres, qu'un fil plein masquait entièrement.
  const MEMOIRE = 3;             // minutes

  let toile = null, ctx = null, hoteVue = null, api = null;
  let chemins = [], attentes = [], horloge = 0, boucle = 0, montree = false;
  let ecoute = null, avecFoule = false, dehorsVus = 0;
  let souris = null, sous = null;

  function jalonner(pts) {
    const cum = [0];
    for (let i = 1; i < pts.length; i++)
      cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    return cum;
  }
  function ou(pts, cum, d) {
    const L = cum[cum.length - 1] || 1;
    d = ((d % L) + L) % L;
    let a = 0, b = cum.length - 1;
    while (a < b - 1) { const m = (a + b) >> 1; if (cum[m] <= d) a = m; else b = m; }
    const t = (d - cum[a]) / ((cum[a + 1] - cum[a]) || 1);
    return [pts[a][0] + (pts[a + 1][0] - pts[a][0]) * t,
            pts[a][1] + (pts[a + 1][1] - pts[a][1]) * t];
  }

  function installer(hote, plan, service) {
    hoteVue = hote; api = service || api;
    if (!toile) {
      toile = document.createElement("canvas");
      toile.id = "guetToile";
      toile.style.cssText = "position:absolute;inset:0;width:100%;height:100%;" +
        "pointer-events:none;display:none";
      ctx = toile.getContext("2d");
    }
    // LE SURVOL SE PREND SUR L'HÔTE, pas sur la surcouche : celle-ci laisse
    // passer les clics (`pointer-events:none`) pour que la molette et le glissé
    // de la page continuent d'agir sous elle. On écoute donc à côté — et l'on
    // REBRANCHE à chaque changement d'hôte : liés une fois pour toutes au
    // premier, ils restaient accrochés à un élément retiré du document, et le
    // survol cessait sans un mot.
    if (toile.parentNode !== hote) {
      if (ecoute) {
        ecoute.el.removeEventListener("mousemove", ecoute.bouge);
        ecoute.el.removeEventListener("mouseleave", ecoute.sort);
      }
      const bouge = (e) => {
        const r = hote.getBoundingClientRect();
        souris = [e.clientX - r.left, e.clientY - r.top];
      };
      const sort = () => { souris = null; };
      hote.addEventListener("mousemove", bouge);
      hote.addEventListener("mouseleave", sort);
      ecoute = { el: hote, bouge, sort };
      hote.appendChild(toile);
    }

    const G = (plan && plan.guettes) || [];
    const cl = ((plan && plan.cloches) || []).filter((c) => c.tocsin);
    chemins = G.map((g) => {
      const pts = g.ronde && g.ronde.trace ? g.ronde.trace : [[g.x, g.y]];
      const cum = jalonner(pts);
      const L = cum[cum.length - 1] || 1;
      // AUTANT D'HOMMES QUE DE PAIRES, ÉGALEMENT ESPACÉES SUR LA BOUCLE : c'est
      // ce qui rend visible la différence entre une grosse guette et une petite.
      const paires = Math.max(1, Math.round((g.en_ronde || 2) / 2));
      return { g, pts, cum, L, paires, attente: L / paires / 78,
               sourde: !cl.some((c) => Math.hypot(g.x - c.x, g.y - c.y) <= c.portee) };
    });
    chemins.forEach((c, i) => { c.i = i; });
    attentes = chemins.map((c) => Math.round(c.attente)).sort((a, b) => a - b);
    return chemins.length;
  }

  // La projection de la page, à l'identique : `vue` est un rectangle en mètres,
  // la toile est en pixels physiques. Rien d'autre à savoir.
  function cadre() {
    const v = api && api.vue ? api.vue() : null;
    if (!v || !hoteVue) return null;
    const r = hoteVue.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const l = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (toile.width !== l || toile.height !== h) { toile.width = l; toile.height = h; }
    return { v, k: l / v[2], dpr, l, h };
  }

  // Un hachage, pas un tirage : la même guette rend toujours le même semis, et
  // rien n'est stocké. Même principe que le déphasage des journées dans
  // `monde/journee.js` — deux hommes du même poste ne se tiennent pas au même
  // endroit, et pourtant on n'écrit aucune position nulle part.
  function melange(a, b) {
    let h = (a * 374761393 + b * 668265263) | 0;
    h = (h ^ (h >>> 13)) * 1274126177;
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }

  function peindreVue() {
    const c = cadre();
    if (!c || !ctx) return;
    const { v, k, dpr } = c;
    const X = (x) => (x - v[0]) * k, Y = (y) => (y - v[1]) * k;
    ctx.clearRect(0, 0, c.l, c.h);
    ctx.lineCap = "round"; ctx.lineJoin = "round";

    const trace = (pts) => {
      ctx.beginPath();
      ctx.moveTo(X(pts[0][0]), Y(pts[0][1]));
      for (let i = 1; i < pts.length; i++) ctx.lineTo(X(pts[i][0]), Y(pts[i][1]));
    };

    // ── LA VILLE, quand l'épreuve la demande ─────────────────────────────────
    // Les habitants d'abord et en dessous : ce sont eux qu'on garde, et le Guet
    // doit se lire PAR-DESSUS eux. À dix-neuf heures on ne voit qu'eux ; une
    // heure après la retraite, il ne reste que les autres.
    if (avecFoule && foulePrete && foule) {
      const jour = 3, minute = ((21 * 60 + horloge / 60) % 1440 + 1440) % 1440;
      ctx.fillStyle = "#7a6a58";
      const rg = Math.max(1, 1.4 * dpr);
      let vus = 0;
      for (const cel of foule.cellules) {
        for (let k = 0; k < cel.n; k += foule.pas) {
          const q = dehorsA(foule, cel, k, jour, minute);
          if (!q) continue;
          vus++;
          ctx.beginPath(); ctx.arc(X(q[0]), Y(q[1]), rg, 0, 6.2832); ctx.fill();
        }
      }
      dehorsVus = vus;
    }

    // ── LES HOMMES D'ABORD, PARCE QUE CE SONT EUX QU'ON REGARDE ──────────────
    // On peint TOUT LE MONDE : les neuf cents de la nuit, pas seulement les deux
    // cent vingt-huit qui tournent. C'est ce qui rend le rapport visible sans
    // qu'on ait à le dire — un gros tas immobile à chaque poste, un fil mince
    // dans les rues. Trois hommes au poste pour un en ronde : ça se voit.
    sous = null;
    const rh = Math.max(1.2, 1.9 * dpr);
    const cherche = souris ? [souris[0] * dpr, souris[1] * dpr] : null;
    const pres = (x, y, seuil) => cherche &&
      Math.hypot(x - cherche[0], y - cherche[1]) < seuil * dpr;

    for (const ch of chemins) {
      const pas = ch.L / ch.paires;

      // AU POSTE — dispersés devant la guette, dans un rayon de neuf mètres :
      // la salle basse, le banc devant, et le pas de la porte. Immobiles, parce
      // que c'est exactement ce qu'ils font.
      ctx.fillStyle = "#b8a882";
      for (let i = 0; i < ch.g.au_poste; i++) {
        const a = melange(ch.i, i) * 6.2832;
        const d = 2 + 7 * Math.sqrt(melange(ch.i, i + 4096));
        const x = X(ch.g.x + Math.cos(a) * d), y = Y(ch.g.y + Math.sin(a) * d);
        ctx.beginPath(); ctx.arc(x, y, rh, 0, 6.2832); ctx.fill();
      }

      // EN RONDE — deux hommes par paire, côte à côte, à leur place sur la
      // boucle. On ne patrouille pas seul, et l'on doit le VOIR.
      ctx.fillStyle = "#fff3d6";
      for (let i = 0; i < ch.paires; i++) {
        const d = horloge * ALLURE + i * pas;
        const p = ou(ch.pts, ch.cum, d);
        const q = ou(ch.pts, ch.cum, d + 2.2);      // le second, deux pas devant
        for (const m of [p, q]) {
          const x = X(m[0]), y = Y(m[1]);
          ctx.beginPath(); ctx.arc(x, y, rh, 0, 6.2832); ctx.fill();
          if (!sous && pres(x, y, 9)) sous = ch;
        }
      }

      // LE POSTE — un point plus gros, et orange s'il n'entend aucun tocsin.
      const px = X(ch.g.x), py = Y(ch.g.y);
      ctx.beginPath(); ctx.arc(px, py, Math.max(3, 4.5 * dpr), 0, 6.2832);
      ctx.fillStyle = ch.sourde ? "#d9642f" : "#e8c15a";
      ctx.fill();
      ctx.lineWidth = Math.max(1, 1.4 * dpr); ctx.strokeStyle = "#14120f"; ctx.stroke();
      if (!sous && pres(px, py, 14)) sous = ch;
    }

    // ── LE CIRCUIT, SEULEMENT AU SURVOL ──────────────────────────────────────
    // Seize boucles peintes en permanence, c'était un DIAGRAMME posé sur la
    // ville : joli, et faux comme information — un circuit n'existe pas dans le
    // monde, personne ne le voit tracé au sol. Ce qui existe, ce sont les
    // hommes. On garde donc la ville nue, et l'on ne montre la boucle que
    // lorsqu'on demande à qui appartient ce qu'on regarde.
    if (sous) {
      ctx.save();
      ctx.strokeStyle = "#6b5734"; ctx.lineWidth = Math.max(1.5, 2.5 * dpr);
      trace(sous.pts); ctx.stroke();

      // Et la fraîcheur par-dessus : chaque paire traîne une lueur de trois
      // minutes, le motif se répète tous les `pas` mètres. On lit d'un coup
      // combien de la boucle vient d'être vue, et combien attend.
      const pas = sous.L / sous.paires;
      const trainee = Math.min(pas, MEMOIRE * 78);
      ctx.strokeStyle = "#f0ad3c"; ctx.lineWidth = Math.max(2, 4 * dpr);
      trace(sous.pts);
      ctx.setLineDash([trainee * k, (pas - trainee) * k]);
      ctx.lineDashOffset = (trainee - (horloge * ALLURE) % pas) * k;
      ctx.stroke();
      ctx.restore();
      ctx.setLineDash([]);
    }

    // ── LES NOMS, seulement d'assez près pour les lire ───────────────────────
    // Même règle que les toponymes de la carte : de loin l'implantation, de
    // près le détail. Seize noms sur la ville entière est une bouillie.
    if (v[2] < 2600) {
      ctx.font = (11 * dpr) + "px Georgia, serif";
      ctx.fillStyle = "#c9b183";
      ctx.strokeStyle = "#14120fcc"; ctx.lineWidth = 3 * dpr;
      for (const ch of chemins) {
        const x = X(ch.g.x) + 9 * dpr, y = Y(ch.g.y) - 7 * dpr;
        ctx.strokeText(ch.g.nom, x, y); ctx.fillText(ch.g.nom, x, y);
      }
    }

    infobulle();
  }

  function infobulle() {
    let b = document.getElementById("guetBulle");
    if (!sous) { if (b) b.style.display = "none"; return; }
    if (!b) {
      b = document.createElement("div");
      b.id = "guetBulle";
      b.style.cssText = "position:absolute;z-index:12;pointer-events:none;" +
        "background:#14120fee;border:1px solid #4a4034;color:#d9d2c4;" +
        "font:12px/1.5 Georgia,serif;padding:6px 9px;max-width:270px";
      hoteVue.appendChild(b);
    }
    const g = sous.g;
    b.innerHTML = "<b style=\"color:#e8c15a;font-weight:400\">" + g.nom + "</b><br>" +
      g.effectif + " hommes · " + sous.paires + " paires en ronde · " +
      g.au_poste + " au poste<br>" +
      (g.ronde ? g.ronde.minutes_tour + " min de tour · " : "") +
      "une rue attend " + Math.round(sous.attente) + " min<br>" +
      g.toits + " toits desservis" +
      (sous.sourde ? "<br><b style=\"color:#d9642f;font-weight:400\">" +
        "n'entend aucun tocsin</b>" : "");
    b.style.display = "block";
    b.style.left = Math.min(souris[0] + 14, hoteVue.clientWidth - 280) + "px";
    b.style.top = Math.max(6, souris[1] - 10) + "px";
  }

  function battre(ts) {
    if (!montree) { boucle = 0; return; }
    if (battre.dernier) {
      const dt = Math.min(0.25, (ts - battre.dernier) / 1000);
      // 1:1 PAR DÉFAUT, et la barre de la page commande le reste. Un tour de
      // quarante minutes prend quarante minutes à ×1 — c'est long, et c'est
      // précisément le fait qu'on veut voir.
      if (!api || !api.marche || api.marche())
        horloge += dt * ((api && api.vitesse ? api.vitesse() : 1) || 1);
    }
    battre.dernier = ts;
    peindreVue();
    boucle = requestAnimationFrame(battre);
  }

  function montrer(oui) {
    montree = !!oui;
    if (toile) toile.style.display = montree ? "block" : "none";
    const b = document.getElementById("guetBulle");
    if (b && !montree) b.style.display = "none";
    if (boucle) { cancelAnimationFrame(boucle); boucle = 0; }
    battre.dernier = 0;
    if (montree) boucle = requestAnimationFrame(battre);
  }

  // PORTER LA NUIT A UNE HEURE DONNEE, sans attendre qu'elle se joue. C'est ce
  // qu'on veut quand on cherche quelque chose de precis — a quoi ressemble la
  // ville deux heures apres la retraite — et c'est aussi la seule façon de
  // verifier la vue la ou `requestAnimationFrame` ne bat pas.
  // L'HORLOGE PEUT REMONTER AVANT LA RETRAITE, et il le faut. Elle était bridée
  // à zéro — c'est-à-dire à vingt et une heures — si bien que G2 ne pouvait pas
  // montrer la ville SE REMPLIR : dix-neuf heures, vingt heures trente et le
  // coup de cloche rendaient le même compte, et la pente n'existait qu'après.
  // Or le pic est la moitié du fait.
  function porter(minutes) {
    horloge = (+minutes || 0) * 60;
    peindreVue();
    return horloge / 60;
  }

  const etatVue = () => ({
    guettes: chemins.length,
    hommes: chemins.reduce((s, c) => s + c.g.effectif, 0),
    enRonde: chemins.reduce((s, c) => s + c.paires * 2, 0),
    auPoste: chemins.reduce((s, c) => s + c.g.au_poste, 0),
    minutes: Math.round(horloge / 60),
    attente: attentes.length ? attentes[0] + " à " + attentes[attentes.length - 1] : null,
    sous: sous ? sous.g.nom : null,
    dehors: dehorsVus,
  });

  // ── LES SONDES DE G2 ──────────────────────────────────────────────────────
  // ON MESURE SUR LA VRAIE FOULE, pas sur la table des besoins : ce qu'on veut
  // savoir est ce que `journee.js` PRODUIT, et non ce qu'on a écrit qu'il
  // devrait produire. Le compte se fait sur l'échantillon déjà chargé pour la
  // vue — mêmes corps, mêmes adresses, même fonction.
  function compterDehors(f, minute, jour) {
    let n = 0;
    for (const cel of f.cellules)
      for (let k = 0; k < cel.n; k += f.pas)
        if (dehorsA(f, cel, k, jour, minute)) n++;
    return n;
  }

  function verdictsRetraite(plan, f) {
    const out = [];
    const dire = (dit, attendu, tenu, observe) => out.push({ dit, attendu, tenu, observe });
    const cf = f && f.t ? f.t.couvre_feu : null;
    const hh = (m) => String(Math.floor(((m % 1440) + 1440) % 1440 / 60)).padStart(2, "0") +
                      " h " + String(((m % 1440) + 1440) % 1440 % 60).padStart(2, "0");

    if (!cf) {
      dire("la ville a un couvre-feu", "retraite + ouverture", false,
           "aucun — voir COUVRE_FEU dans scripts/monde/besoins.py");
      return out;
    }
    dire("la ville a une heure de retraite et une d'ouverture",
         "deux cloches", true,
         hh(cf.retraite) + " → " + hh(cf.ouverture) + " · " + cf.rentrer + " min pour rentrer");

    // La cloche nommée doit EXISTER. Une retraite sonnée par une cloche qu'on
    // n'a pas est un couvre-feu que personne n'entend.
    const cloches = (plan && plan.cloches) || [];
    const nom = (id) => (cloches.find((c) => c.id === id) || {}).nom;
    const r = nom(cf.cloche_retraite), o = nom(cf.cloche_ouverture);
    dire("les deux cloches existent, et savent le dire",
         "l'Aïeule et le Ferrant", !!(r && o),
         (r || "?") + " sonne la retraite · " + (o || "?") + " ouvre le jour");

    if (!f || !f.cellules || !f.cellules.length) {
      dire("la rue se vide au coup de cloche", "mesuré sur la foule", null,
           "pas d'habitants chargés");
      return out;
    }
    const jour = 3;
    const av = compterDehors(f, cf.retraite - 30, jour);
    const pic = compterDehors(f, cf.retraite, jour);
    const ap30 = compterDehors(f, cf.retraite + 30, jour);
    const ap60 = compterDehors(f, cf.retraite + 60, jour);
    const nuit = compterDehors(f, (cf.retraite + 300) % 1440, jour);
    const ech = " (échantillon de " + Math.round(f.total / f.pas) + " sur " + f.total + ")";

    dire("la retraite tombe sur la rue la plus pleine de la soirée",
         "le pic est à la cloche", pic >= av,
         av + " à " + hh(cf.retraite - 30) + " → " + pic + " au coup de cloche" + ech);

    dire("une heure plus tard, la rue est vide",
         "moins d'un vingtième du pic", pic > 0 ? ap60 <= pic * 0.05 : null,
         ap30 + " après une demi-heure · " + ap60 + " après une heure");

    dire("au cœur de la nuit, il ne reste dehors que le Guet",
         "zéro habitant", nuit === 0,
         nuit === 0 ? "personne à " + hh(cf.retraite + 300) + " — " +
                      (plan.guettes || []).reduce((s, g) => s + (g.effectif || 0), 0) +
                      " manteaux d'or seuls dehors"
                    : nuit + " habitant(s) encore dehors");

    // ET LE GUET, LUI, NE RENTRE PAS. C'est la moitié qu'on oublie : un
    // couvre-feu qui coucherait aussi la garde ne serait pas un couvre-feu.
    const G = plan.guettes || [];
    dire("le couvre-feu ne couche pas ceux qui gardent",
         "16 guettes debout", G.length > 0,
         G.reduce((s, g) => s + (g.au_poste || 0), 0) + " au poste · " +
         G.reduce((s, g) => s + (g.en_ronde || 0), 0) + " en ronde, toute la nuit");
    return out;
  }

  // JOUER DISPATCHE PAR ÉPREUVE. G1 juge la charpente et n'a besoin que du plan ;
  // G2 juge ce que la ville FAIT, donc il lui faut la foule chargée d'abord.
  async function jouer(id) {
    const r = await fetch("/monde/plan2d");
    if (!r.ok) throw new Error("le plan de la ville n'a pas répondu : " + r.status);
    const plan = await r.json();
    if (id === "guet-retraite") {
      const f = await chargerFoule(plan);
      return { verdicts: verdictsRetraite(plan, f), plan, foule: true };
    }
    return { verdicts: verdicts(plan), plan };
  }

  racine.BatailleGuet = { EPREUVES: [EPREUVE_GUETTES, EPREUVE_RETRAITE],
                          jouer, verdicts, peindre, chargerFoule,
                          foule: (oui) => { avecFoule = !!oui; },
                          installer, montrer, porter, etatVue,
                          // `remettre(min)` : où l'on ouvre l'horloge. G1 part de la
                          // retraite, G2 deux heures avant, pour voir la ville se remplir.
                          remettre: (min) => { horloge = (+min || 0) * 60; peindreVue(); } };
})(typeof window !== "undefined" ? window : globalThis);
