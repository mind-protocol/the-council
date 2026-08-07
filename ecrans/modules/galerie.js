// galerie.js — les acteurs en bandeau SOUS le décor (la carte, le plan).
// Chaque acteur a son médaillon rond ; le locuteur s'illumine.
// Ils étaient jadis répartis en couronne autour de la carte, ce qui les faisait
// flotter et mangeait la table par les bords. Rangés dessous, ils forment une
// rangée de visages en face de soi et l'ordre du flux est enfin lisible : la
// mise en place est celle du CSS (flex), il n'y a plus rien à calculer ici.
//
// La salle ne se déclare pas seulement, elle SE CONSTATE. Un item `salle` est
// rare — le MJ en pousse un par changement de lieu — alors que la scène, elle,
// se remplit et se vide en permanence : quelqu'un entre, quelqu'un est appelé,
// un pêcheur prend la parole devant la cour. Trois règles, donc :
//   • qui parle ou qui agit EST là — son médaillon apparaît de lui-même ;
//   • `entrent` / `sortent` sur n'importe quel item font entrer ou sortir
//     quelqu'un sans redéclarer toute la salle ;
//   • une salle pleine ne mange pas la table : au-delà de MAX visages, les plus
//     longtemps silencieux passent dans une pastille « et N autres » — et en
//     ressortent au premier mot qu'ils disent.
"use strict";
(() => {
  window.Presents = {};

  const MAX = 8;                   // au-delà, la rangée avale la carte
  let compteur = 0;                // battements écoulés
  const entendu = new Map();       // id → dernier battement où on l'a entendu
  const bruts = new Map();         // ce que l'item a écrit, avant complétion
  let ordre = [];                  // l'ordre d'arrivée dans la salle

  const zone = () => document.getElementById("acteurs");

  function vider() {
    const z = zone();
    if (z) z.innerHTML = "";
    window.Presents = {};
    entendu.clear();
    bruts.clear();
    ordre = [];
    pose = "";
  }

  // Un présent : ce que l'item en dit, complété par le registre des gens.
  function fiche(brut) {
    const f = window.Gens ? Gens.qui(brut.id) : {};
    return Object.assign({}, brut, {
      nom: brut.nom || f.nom || String(brut.id || "").replace(/-/g, " "),
      titre: brut.titre || f.titre,
      portrait_svg: brut.portrait_svg || f.portrait_svg,
    });
  }

  function entrer(brut, differe) {
    const id = typeof brut === "string" ? brut : brut && brut.id;
    if (!id) return;
    const brutN = typeof brut === "string" ? { id } : brut;
    // un présent déjà là ne se dédouble pas : on complète ce qu'on sait de lui.
    // On garde ce que l'ITEM a écrit à part — le registre des gens, quand il
    // arrivera, doit pouvoir combler ce qu'on avait deviné du seul id.
    bruts.set(id, Object.assign({}, bruts.get(id) || {}, brutN));
    window.Presents[id] = fiche(bruts.get(id));
    if (ordre.indexOf(id) === -1) ordre.push(id);
    if (!entendu.has(id)) entendu.set(id, compteur);
    if (!differe) dessiner();
  }

  function sortir(id) {
    if (!id) return;
    delete window.Presents[id];
    entendu.delete(id);
    bruts.delete(id);
    ordre = ordre.filter((x) => x !== id);
    dessiner();
  }

  // Quelqu'un vient de parler ou de faire : il est là, et il est frais.
  function toucher(id) {
    if (!id || Bus.enArchive()) return;
    if (!window.Presents[id]) entrer(id);
    entendu.set(id, ++compteur);
    dessiner();
  }

  // Qui se montre : les MAX derniers entendus. Le reste passe dans la pastille,
  // sans disparaître de la salle — il n'est pas sorti, on ne le voit plus.
  function montres() {
    const rangs = ordre.slice().sort((a, b) => entendu.get(b) - entendu.get(a));
    const gardes = new Set(rangs.slice(0, MAX));
    return { visibles: ordre.filter((id) => gardes.has(id)),
             tus: ordre.filter((id) => !gardes.has(id)) };
  }

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  function medaillon(p) {
    const slot = document.createElement("div");
    slot.className = "acteur";
    slot.id = "act-" + p.id;
    // pas de bulle ici : la parole vit dans le fil, la salle montre les gens.
    slot.innerHTML =
      '<div class="medaillon" id="med-' + p.id + '" title="' + esc(p.titre || "") + '">' +
      (p.portrait_svg || "") + '<span class="qui">' + esc(p.nom) +
      (p.titre ? '<small class="role"><i class="emb">' + Bus.embleme(p.titre) + "</i>" +
        esc(p.titre) + "</small>" : "") + "</span></div>";
    return slot;
  }

  let parle = null;
  let pose = "";                   // les visages actuellement montés, dans l'ordre

  // Les présents restent pleinement visibles tant qu'ils sont là : le silence
  // ne délave plus les visages.
  function froideur(slot) {
    slot.classList.remove("froid", "tres-froid");
  }

  function dessiner() {
    const z = zone();
    if (!z) return;
    const { visibles, tus } = montres();
    const veut = visibles.join("|") + (tus.length ? "|+" + tus.length : "");
    // Une réplique sur deux ne change PAS qui est là : rebâtir la rangée à
    // chaque battement rechargerait huit portraits SVG et couperait net
    // l'illumination du locuteur. On ne remonte les visages que s'ils bougent.
    if (veut === pose) {
      visibles.forEach((id) => {
        const slot = document.getElementById("act-" + id);
        if (slot) froideur(slot, id);
      });
      return;
    }
    pose = veut;
    z.innerHTML = "";
    visibles.forEach((id) => {
      const p = window.Presents[id];
      if (!p) return;
      const slot = medaillon(p);
      froideur(slot, id);
      if (id === parle) slot.classList.add("parle");
      z.appendChild(slot);
    });
    if (tus.length) {
      const chip = document.createElement("div");
      chip.className = "acteur acteur-reste";
      chip.title = tus.map((id) => (window.Presents[id] || {}).nom || id).join(", ");
      chip.innerHTML = '<div class="medaillon"><span class="qui">et ' +
        tus.length + " autres</span></div>";
      z.appendChild(chip);
    }
  }

  Bus.enregistrer("salle", (it) => {
    vider();
    (it.presents || []).forEach((p) => entrer(p, true));
    dessiner();
  });

  // Entrées et sorties : elles peuvent tomber sur N'IMPORTE quel item, parce
  // qu'elles se produisent en cours de scène. « Le page sort », « ser Robert
  // entre » — un mot dans l'item suffit, pas besoin de redéclarer la salle.
  ["salle", "recit", "replique", "geste", "table", "breve", "evenement", "vous"]
    .forEach((t) => Bus.enregistrer(t, (it) => {
      (it.entrent || []).forEach((x) => entrer(x));
      (it.sortent || []).forEach((x) => sortir(typeof x === "string" ? x : x && x.id));
    }));

  // Parler ou faire, c'est être là. C'est la règle qui répare tout le reste :
  // le MJ n'a plus à tenir un état de présence à jour pour que la salle soit
  // juste — il lui suffit de jouer les gens.
  Bus.enregistrer("replique", (it) => toucher(it.locuteur_id));
  ["geste", "table"].forEach((t) => Bus.enregistrer(t, (it) => toucher(it.acteur_id)));

  window.activerLocuteur = (id) => {
    // Le passé rechargé ne fait entrer personne : la salle est celle de MAINTENANT.
    if (Bus.enArchive()) return;
    parle = id;
    if (id && !window.Presents[id]) entrer(id);
    document.querySelectorAll(".acteur").forEach((a) => a.classList.remove("parle"));
    const s = document.getElementById("act-" + id);
    if (s) s.classList.add("parle");
  };

  // Le registre des gens arrive après les premiers items du flux : les visages
  // posés en attendant se complètent quand il est là.
  window.addEventListener("DOMContentLoaded", () => {
    if (window.Gens && Gens.quand) Gens.quand(() => {
      ordre.forEach((id) => { window.Presents[id] = fiche(bruts.get(id) || { id }); });
      pose = "";
      dessiner();
    });
  });

  // Changement de scène : la salle se vide. Le fil, lui, garde tout.
  Bus.enregistrer("effacer", () => { parle = null; vider(); });

  // ---- le rapprochement avec la présence du monde --------------------------
  // Se tenir dans une pièce est un fait du MONDE ; le flux, lui, est cloisonné
  // par audience. Un PNJ que deux scènes se partagent — le mestre, appelé chez
  // l'une alors qu'il était debout chez l'autre — restait donc affiché dans les
  // deux salles à la fois, une par écran : aucun `sortent` ne peut l'ôter des
  // deux, puisqu'il porte forcément une audience.
  //
  // `/presence` dit qui partage VRAIMENT notre pièce (et rien de plus : où sont
  // les autres ne descend pas jusqu'ici). Elle ÔTE et elle AJOUTE.
  //
  // Elle a longtemps servi à ôter seulement, au motif qu'entrer était l'affaire
  // du flux — mais le flux ne nomme que ceux qui parlent. Un conseil de neuf en
  // affichait six : le mestre debout au fond, Lucerys qui n'avait rien dit,
  // Nesse à la porte n'existaient nulle part à l'écran alors qu'on les voyait de
  // ses yeux. Une salle n'est pas la liste de ceux qui ont pris la parole.
  //
  // Ce qui vient de la présence entre donc SANS bruit : pas de compteur de
  // fraîcheur touché, pas de médaillon qui s'illumine — ils sont là, ils se
  // taisent, et ils s'estompent naturellement dans la pastille « et N autres ».
  // On n'ôte, à l'inverse, que ceux que la présence connaît et place ailleurs :
  // un pêcheur de passage, absent du fichier, garde son visage.
  async function rapprocher() {
    try {
      const d = await (await fetch("/presence")).json();
      if (!d || !d.connue) return;                  // partie seule, ou pièce inconnue
      const ici = new Set((d.avec || []).map((x) => x.id));
      const moi = window.Moi && window.Moi.personnage_id;
      if (moi) ici.add(moi);
      // ceux que la salle porte et que le flux n'a pas nommés
      (d.avec || []).forEach((x) => {
        if (window.Presents[x.id]) return;
        entrer({ id: x.id, nom: x.nom }, true);
      });
      dessiner();
      Object.keys(window.Presents).forEach((id) => {
        if (ici.has(id)) return;
        // Inconnu de la présence : on ne tranche pas, le flux a raison.
        if (!(d.connus || []).includes(id)) return;
        sortir(id);
      });
    } catch (e) {}
  }

  window.addEventListener("DOMContentLoaded", () => {
    rapprocher();
    setInterval(rapprocher, 20000);
  });
  // Un changement de salle est le moment où l'on se trompe : on rapproche là,
  // en plus du battement régulier.
  ["salle", "effacer"].forEach((t) => Bus.enregistrer(t, () => setTimeout(rapprocher, 300)));
})();
