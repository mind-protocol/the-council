// identite.js — L'UNITÉ : qui en est, qui la mène, et qui reprend quand il tombe.
//
// TROISIÈME PIÈCE SORTIE DU MONOLITHE, et la première qui ne soit pas du monde
// physique. DÉPLACEMENT et non réécriture : pas une ligne n'a changé.
//
// CE QU'ELLE TIENT. L'appartenance — un homme est dans SON unité, jamais dans
// celle dont il est le plus près —, la place de chacun dans la forme, et la
// succession quand le chef tombe. Le refactor le dit ainsi : « ses membres,
// jamais déduits d'une proximité fortuite ».
//
// ⚠ `guideDe()` A UN EFFET DE BORD, et il faut le savoir avant de l'appeler.
// Quand le chef courant est mort, blessé, en déroute ou passé dans une autre
// formation, elle en ÉLIT un autre et le pose dans `u.cadre.chef`. Ce n'est donc
// pas une lecture : c'est une décision, qui se produit au moment où on la
// demande. L'appeler plus tôt dans un battement qu'aujourd'hui ferait observer
// une succession un cran trop tôt — un changement de comportement déguisé en
// lecture. Le geste qui donne à chaque homme son chef connu, dans
// `bataille2d.js`, lit `u.cadre.chef` tel quel pour cette raison exacte.
//
// LA SUCCESSION NE TIRE PAS DANS L'URNE. Le successeur est celui dont le vécu,
// le dressage et la trempe rendent la prise de charge la moins improbable ; le
// délai vient de l'expérience moyenne des survivants. Une succession doit être
// rejouable et découler des hommes présents, pas consommer un tirage.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleUniteIdentite = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  /**
   * `creer(S, { FILES_VINTAINE, PAS_DE_RANG, dehors, noter })`
   *
   * `dehors` vient de la topologie ; `noter` écrit aux annales. On les prend en
   * argument plutôt que de les refaire : une unité n'a pas à savoir dessiner un
   * plan ni à tenir un registre.
   */
  function creer(S, opts) {
    opts = opts || {};
    const FILES_VINTAINE = opts.FILES_VINTAINE || [-0.75, -0.25, 0.25, 0.75];
    const PAS_DE_RANG = opts.PAS_DE_RANG || 1.05;
    const dehors = opts.dehors, noter = opts.noter;

    function axeDe(porte) {
      const [nx, ny] = dehors(porte);
      return { nx, ny, tx: -ny, ty: nx };
    }

    function placeDeFormation(i) {
      // Vingt hommes = quatre files sur cinq rangs, chef COMPRIS. L'ancienne
      // numérotation posait le chef seul au rang zéro puis quatre hommes par
      // rang derrière lui : elle fabriquait une pointe et une boule, alors que
      // le code prétendait fabriquer une ligne. Le chef prend l'une des deux
      // places centrales du premier rang ; les trois premiers suivants ferment
      // ce rang, puis la grille se remplit normalement.
      const ordrePremierRang = [1, 0, 2, 3];
      const case_ = i < 4 ? ordrePremierRang[Math.max(0, i)] : i;
      const file = case_ % FILES_VINTAINE.length;
      const rang = Math.floor(case_ / FILES_VINTAINE.length);
      // `cote` est relatif AU CHEF, puisque son corps est l'ancre mécanique.
      const cote = FILES_VINTAINE[file] - FILES_VINTAINE[1];
      return { rang, file, cote, recul: rang * PAS_DE_RANG };
    }

    function cadreNeuf(forme) {
      return {
        forme: forme || "colonne", chef: null,
        phase: "deploiement", trace: null, clef: null, s: 0,
        largeur: 0, profondeur: 0, cohesion: 1,
        calculs: 0,
        perduA: null, reprendA: null,
      };
    }

    function creerFormation(id, camp, parent, forme) {
      const rangParent = parent
        ? S.formations.filter((u) => u.parent === parent).length : 0;
      const u = {
        n: S.formations.length, id, camp, parent: parent || null,
        rangParent,
        membres: [], cadre: cadreNeuf(forme),
        escouade: null,
        ordre: { mode: "tenir", destination: null, version: 0, donneA: 0,
                 texte: "Tenez ce poste." },
      };
      S.formations.push(u);
      return u;
    }

    function affecterFormation(h, u, i, chef) {
      h.formation = u.n;
      const p = placeDeFormation(i);
      // Deux hommes d'un même rang n'ont pas une croix peinte sous les pieds.
      // Ces biais sont tirés de leur identité stable (donc sans consommer l'urne
      // de la bataille) et les marges disent la zone qu'ils peuvent occuper sans
      // que la formation cherche à les « corriger ».
      const no = +(String(h.debugId || "0").match(/\d+/) || [0])[0];
      const grain = (k) => (((Math.imul(no + 1, k) >>> 0) / 4294967296) - .5);
      p.biaisCote = grain(2654435761) * .5;
      p.biaisRecul = grain(2246822519) * .4;
      p.margeCote = .32; p.margeRecul = .28;
      h.placeFormation = p;
      h.formationS = 0;
      h.chefFormation = !!chef;
      u.membres.push(h);
      if (chef) u.cadre.chef = h;
      return h;
    }

    function changerDeFormation(h, u, chef) {
      const ancienne = formationDe(h);
      if (ancienne) {
        const i = ancienne.membres.indexOf(h);
        if (i >= 0) ancienne.membres.splice(i, 1);
        if (ancienne.cadre.chef === h) ancienne.cadre.chef = null;
      }
      return affecterFormation(h, u, chef ? 0 : u.membres.length, chef);
    }

    function formationDe(h) {
      if (!h || h.formation == null || h.formation < 0) return null;
      return S.formations[h.formation] || null;
    }

    function guideDe(u) {
      if (!u || !u.cadre) return null;
      let chef = u.cadre.chef;
      if (!chef || chef.etat === "mort" || chef.etat === "blesse" ||
          chef.etat === "deroute" || chef.formation !== u.n) {
        chef = u.membres.find((h) => h.chefFormation && h.etat !== "mort" &&
          h.etat !== "blesse" && h.etat !== "deroute") || null;
        u.cadre.chef = chef;
      }
      return chef;
    }

    // LE CHEF TOMBE : L'UNITÉ NE SAIT PAS IMMÉDIATEMENT QUI PARLERa PLUS FORT.
    // Le délai vient de l'expérience moyenne des survivants ; le successeur est
    // celui dont le vécu, le dressage et la trempe rendent la prise de charge la
    // moins improbable. Aucun tirage : une succession doit être rejouable et
    // découler des hommes déjà présents, pas consommer une nouvelle urne.
    function successions() {
      for (const u of S.formations) {
        const c = u.cadre, chef = guideDe(u);
        if (chef) { c.perduA = null; c.reprendA = null; continue; }
        const candidats = u.membres.filter((h) =>
          h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute" &&
          h.etat !== "coureur" && !h.messager && !h.tete && !h.hors);
        if (!candidats.length) continue;
        if (c.perduA === null) {
          const vecu = candidats.reduce((n, h) => n + (h.vecu || 0), 0) /
                       candidats.length;
          const delai = 6 - Math.max(-1, Math.min(1, vecu)) * 2;
          c.perduA = S.temps; c.reprendA = S.temps + delai;
          continue;
        }
        if (S.temps < c.reprendA) continue;
        candidats.sort((a, b) =>
          ((b.vecu || 0) * 2 + (b.dressage || 0) + (b.trempe || 0) * .5 +
           (b.capitaine ? 4 : 0)) -
          ((a.vecu || 0) * 2 + (a.dressage || 0) + (a.trempe || 0) * .5 +
           (a.capitaine ? 4 : 0)));
        const nouveau = candidats[0];
        for (const h of u.membres) {
          h.chefFormation = false;
          if (u.camp === "assaut") h.chef = false;
        }
        nouveau.chefFormation = true;
        if (u.camp === "assaut") nouveau.chef = true;
        nouveau.placeFormation = placeDeFormation(0);
        let rang = 1;
        for (const h of u.membres)
          if (h !== nouveau && h.etat !== "mort" && h.etat !== "blesse")
            h.placeFormation = placeDeFormation(rang++);
        const apres = S.temps - c.perduA;
        c.chef = nouveau; c.perduA = null; c.reprendA = null;
        noter("nouveau-chef", nouveau.x, nouveau.y,
              { dit: { unite: u.id, camp: u.camp,
                       apres: +apres.toFixed(1) } });
      }
    }
    return { axeDe, placeDeFormation, cadreNeuf, creerFormation,
             affecterFormation, changerDeFormation, formationDe, guideDe,
             successions };
  }

  return { creer };
});
