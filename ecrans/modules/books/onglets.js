// onglets.js — LA TRANCHE DU HAUT : ce qui est posé là, et ce qui est ouvert.
//
// Plusieurs volumes dans la même salle ne s'empilent pas : ils se rangent en
// onglets, comme sur une étagère, et l'on en ouvre un à la fois — un homme ne
// lit pas deux registres en même temps. Cette pièce fait les deux gestes que
// cela demande : GROUPER les volumes par coffret, puis ÉLIRE ce qu'on a sous
// les yeux ; et rendre les rubans d'onglets qui permettent d'en changer.
//
// ⚠ `ranger` ÉCRIT `S.ouvert` ET `S.ouverteBoite`, et c'est voulu : élire, ici,
// c'est décider. Une salle qui change, un homme qui sort avec son cahier, et ce
// qui était ouvert n'est plus à portée — il faut bien rouvrir quelque chose, et
// c'est le dessus de la pile. Ce n'est donc pas une lecture, et `etagere.js` ne
// doit pas l'appeler deux fois dans un tracé.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé en sortant
// de `etagere.js`. Seule la fin change de forme — les rubans étaient poussés
// dans `corps` au fil de l'eau, ils sont RENDUS en liste, et c'est l'étagère
// qui les pose. Une pièce qui écrit dans le corps d'une autre ne se déplace pas.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksOnglets = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { genre, teinte, compte } = A.lecture;

    // ---- GROUPER, PUIS ÉLIRE --------------------------------------------------
    function ranger(dedans) {
      // La tranche du haut mêle les COFFRETS et ce qui traîne à côté d'eux : une
      // table de travail porte des boîtes et des registres posés dessus, et l'on
      // n'oblige personne à ranger. Un coffret prend le rang de son volume le
      // plus frais — ce qu'on vient de toucher reste sur le dessus.
      const entrees = [];
      const parBoite = new Map();
      dedans.forEach((b) => {
        const c = A.coffret(b);
        if (!c) { entrees.push({ livre: b, livres: [b] }); return; }
        let e = parBoite.get(c.id);
        if (!e) {
          e = { boite: c, livres: [] };
          parBoite.set(c.id, e);
          entrees.push(e);
        }
        e.livres.push(b);
      });
      // Ce qu'on a sous les yeux : un coffret ouvert, ou un volume — jamais les
      // deux. Un coffret ouvert sans volume montre sa carte : ce qu'il y a
      // dedans, ligne à ligne. C'est ça, ouvrir une boîte.
      let active = S.ouverteBoite ? (parBoite.get(S.ouverteBoite) || null) : null;
      if (active) {
        if (S.ouvert && !active.livres.some((b) => b.id === S.ouvert)) S.ouvert = null;
      } else {
        S.ouverteBoite = null;
        active = entrees.find((e) => e.livres.some((b) => b.id === S.ouvert)) || null;
        if (active && active.boite) S.ouverteBoite = active.boite.id;
      }
      // Plus rien de retenu (on a changé de salle, un homme est sorti) : on
      // rouvre ce qui est sur le dessus de la pile.
      if (!active) {
        active = entrees[0];
        if (active.boite) { S.ouverteBoite = active.boite.id; S.ouvert = null; }
        else { S.ouverteBoite = null; S.ouvert = active.livre.id; }
      }
      return { entrees, active };
    }

    // ---- LES RUBANS -----------------------------------------------------------

    // un onglet : un signe, un titre, et d'où la chose sort.
    function onglet(o, actif, sous, clic) {
      const bt = document.createElement("button");
      bt.className = "book-onglet" + (actif ? " actif" : "");
      bt.style.setProperty("--book-teinte", teinte(o));
      const g = genre(o);
      bt.title = (g ? g.nom + " — " : "") + sous;
      const t = document.createElement("span");
      t.className = "book-onglet-titre";
      // L'emblème : de quoi reconnaître un volume SANS le lire. Trente onglets
      // de titres se ressemblent tous au coin de l'œil ; un signe et une
      // couleur, non. C'est la même fonction que les emblèmes d'office sur le
      // plan du château — on cherche une forme, pas un mot.
      if (o.embleme) {
        const e = document.createElement("span");
        e.className = "book-onglet-embleme";
        e.textContent = o.embleme;
        t.appendChild(e);
      }
      t.appendChild(document.createTextNode(o.titre || "Sans titre"));
      bt.appendChild(t);
      const ou = document.createElement("span");
      ou.className = "book-onglet-ou";
      ou.textContent = sous;
      bt.appendChild(ou);
      bt.onclick = clic;
      return bt;
    }

    // Les rubans d'onglets, dans l'ordre où ils se posent. Liste vide quand il
    // n'y a rien à choisir — une étagère d'un seul volume n'en est pas une.
    function tranches(entrees, active, dedans, seulesNotes) {
      const rubans = [];
      // À une seule entrée, pas d'onglet — une étagère d'un seul volume n'en est
      // pas une, et la provenance suffit à dire d'où il sort.
      if (entrees.length > 1) {
        const tranche = document.createElement("div");
        tranche.className = "books-tranche";
        entrees.forEach((e) => {
          const actif = e === active;
          if (e.boite) {
            // Un clic OUVRE le coffret : on voit ce qu'il y a dedans. Il ne se
            // met pas à lire un volume à notre place — on ouvre une boîte pour
            // regarder ce qu'elle contient, on prend le volume ensuite.
            const bt = onglet(
              e.boite, actif,
              A.provenance(e.boite) + " — " + compte(e.livres.length),
              () => { S.ouverteBoite = e.boite.id; S.ouvert = null; A.dessiner(); });
            bt.classList.add("book-coffret");
            if (actif) bt.classList.add("ouvert");
            tranche.appendChild(bt);
          } else {
            tranche.appendChild(onglet(
              e.livre, actif, A.provenance(e.livre),
              () => { S.ouverteBoite = null; S.ouvert = e.livre.id; A.dessiner(); }));
          }
        });
        tranche.classList.add("books-coffrets");
        rubans.push(tranche);
      } else if (!seulesNotes) {
        const ou = document.createElement("div");
        ou.className = "books-ou";
        ou.textContent = active && active.boite
          ? active.boite.titre + " — " + A.provenance(active.boite)
          : A.provenance(dedans[0]);
        rubans.push(ou);
      }

      // Un volume pris dans le coffret : on garde sa tranche au-dessus, pour
      // pouvoir passer de l'un à l'autre sans refermer la boîte.
      if (active.boite && S.ouvert && active.livres.length > 1) {
        const dedansBoite = document.createElement("div");
        dedansBoite.className = "books-tranche books-dedans";
        active.livres.forEach((b) => {
          const g = genre(b);
          dedansBoite.appendChild(onglet(
            b, b.id === S.ouvert, g ? g.nom : A.provenance(b),
            () => { S.ouvert = b.id; A.dessiner(); }));
        });
        rubans.push(dedansBoite);
      }
      return rubans;
    }

    return { ranger, tranches };
  }

  return { creer };
});
