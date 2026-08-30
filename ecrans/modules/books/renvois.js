// renvois.js — UN NUMÉRO ÉCRIT, ET LA LIGNE QUI LE DÉFINIT.
//
// Un cahier d'affaire ne se lit pas de haut en bas, il se lit en sautant :
// « bloque 23100 », « dépend de 24000 », « ouvre 23010 ». Tout s'y cite par
// son numéro, et jusqu'ici il fallait aller le chercher à la main, souvent
// dans un autre volume. On accroche donc chaque numéro à la ligne qui le
// porte — la donnée est déjà là, il n'y manquait que le chemin.
//
// ELLE TIENT AUSSI LE BROUILLARD DES RENVOIS : on n'indexe que ce qu'on peut
// OUVRIR d'où l'on est. Un numéro resté en texte nu dit qu'on n'a pas ce
// registre-là sous la main, et c'est une information juste.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksRenvois = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { tableauxDe, estAdresse, numeroDe, serie, NUMERO } = A.lecture;

    // L'ICÔNE d'une ligne. Elle est déjà écrite : chaque intitulé s'ouvre sur son
    // emoji (« 🪶 Se donner un exécutant »), et à défaut c'est celui du tableau
    // qui la porte (🎯 états, 🔒 verrous, 🗝️ clefs, ⚔️ actions). On ne demande
    // donc rien de neuf à personne — on ramasse ce qui est là.
    const PICTO = /^\s*(\p{Extended_Pictographic}️?)/u;
    const picto = (s) => {
      const m = PICTO.exec(s == null ? "" : String(s));
      return m ? m[1] : "";
    };
    // L'intitulé nu : sans son emoji de tête, sans ses appuis.
    const intitule = (s) => String(s == null ? "" : s)
      .replace(PICTO, "").replace(/\*\*/g, "").trim();

    // On n'indexe que ce qu'on peut OUVRIR d'où l'on est. Un renvoi vers un
    // volume hors de portée — dans un autre château, dans la poche d'un absent,
    // réservé à d'autres lecteurs — ne s'allume pas, et c'est juste : le
    // brouillard vaut ici comme ailleurs, et un numéro resté en texte nu dit
    // qu'on n'a pas ce registre-là sous la main.
    function indexer() {
      S.renvois = new Map();
      S.fiches = new Map();
      const cands = new Map();    // numéro → les volumes qui le portent
      const series = new Map();   // volume → combien de numéros par millier
      const infos = new Map();    // numéro → volume → {titre, icone}
      A.ici().forEach((b) => {
        if (b.notes) return;
        tableauxDe(b).forEach((t) => {
          if (!estAdresse(t)) return;
          t.lignes.forEach((l) => {
            const n = numeroDe(l);
            if (!n) return;
            if (!cands.has(n)) cands.set(n, []);
            cands.get(n).push(b.id);
            if (!infos.has(n)) infos.set(n, new Map());
            const etiquette = (l.cellules || [])[1];
            infos.get(n).set(b.id, {
              titre: intitule(etiquette),
              icone: picto(etiquette) || picto(t.titre),
            });
            if (!series.has(b.id)) series.set(b.id, new Map());
            const s = series.get(b.id);
            s.set(serie(n), (s.get(serie(n)) || 0) + 1);
          });
        });
      });
      // Deux volumes peuvent porter le même numéro : un agrégat qui recopie un
      // état cible par affaire, et l'affaire qui le tient pour de bon. Celui qui
      // tient la SÉRIE gagne — l'agrégat n'a qu'un numéro du millier, l'affaire
      // en a trente. À égalité, le premier du fichier.
      cands.forEach((livres, n) => {
        let mieux = livres[0], score = -1;
        livres.forEach((id) => {
          const c = (series.get(id) || new Map()).get(serie(n)) || 0;
          if (c > score) { score = c; mieux = id; }
        });
        S.renvois.set(n, mieux);
        const i = (infos.get(n) || new Map()).get(mieux) || {};
        S.fiches.set(n, { livre: mieux, titre: i.titre || "", icone: i.icone || "" });
      });
      // Le fil a pu poser des renvois avant que l'étagère ne soit chargée : ils
      // attendent en texte nu. Maintenant qu'on sait, on les rallume.
      if (window.Renvois && Renvois.raviver) Renvois.raviver();
    }

    // Ce qu'un numéro vaut, pour qui le cite AILLEURS que dans un livre : son
    // volume, son intitulé, sa famille. Rien si le registre n'est pas à portée —
    // et c'est ce silence qui tient le brouillard.
    function fiche(n) {
      return S.fiches.get(String(n)) || null;
    }

    // Accrocher, dans un morceau déjà rendu, tous les numéros qui mènent quelque
    // part. On descend jusqu'aux nœuds de texte pour ne défaire ni le gras
    // d'appui ni les entités déjà posées ; on laisse tranquille la cellule qui
    // EST l'adresse (`data-ancre`) — un numéro n'a pas à se renvoyer à lui-même —
    // et l'on n'entre pas dans un dessin, où un bouton n'aurait pas de sens.
    function renvoyer(racine) {
      if (!S.renvois.size) return;
      const textes = [];
      (function marche(n) {
        for (let e = n.firstChild; e; e = e.nextSibling) {
          if (e.nodeType === 3) { textes.push(e); continue; }
          if (e.nodeType !== 1) continue;
          if (String(e.tagName).toLowerCase() === "svg") continue;
          if (e.dataset && e.dataset.ancre) continue;
          if (e.classList && e.classList.contains("book-renvoi")) continue;
          marche(e);
        }
      })(racine);
      textes.forEach((t) => {
        const s = t.nodeValue;
        NUMERO.lastIndex = 0;
        let m, i = 0, frag = null;
        while ((m = NUMERO.exec(s))) {
          const livre = S.renvois.get(m[0]);
          if (!livre) continue;
          if (!frag) frag = document.createDocumentFragment();
          if (m.index > i) frag.appendChild(document.createTextNode(s.slice(i, m.index)));
          frag.appendChild(lien(m[0], livre));
          i = m.index + m[0].length;
        }
        if (!frag) return;
        if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
        t.parentNode.replaceChild(frag, t);
      });
    }

    function lien(n, livre) {
      const bt = document.createElement("button");
      bt.type = "button";
      bt.className = "book-renvoi";
      bt.textContent = n;
      const b = (S.books || []).find((x) => x && x.id === livre);
      bt.title = b && b.titre ? b.titre : livre;
      bt.onclick = (e) => { e.preventDefault(); e.stopPropagation(); aller(n); };
      return bt;
    }

    // Y aller : le volume s'ouvre s'il n'était pas celui qu'on lisait, et la
    // ligne se signale un instant — sans quoi on atterrit dans une grille de
    // quarante lignes sans savoir laquelle on était venu chercher.
    function aller(n) {
      const livre = S.renvois.get(String(n));
      if (!livre) return false;
      if (livre !== S.ouvert && !A.ouvrir(livre)) return false;
      viser(String(n));
      return true;
    }

    // VISER SE FAIT AUSSI EN TOUTES LETTRES. Un renvoi porte un numéro, mais tout
    // ce qui s'écrit n'en a pas : une ligne de règles s'appelle « EC.4 », un
    // paragraphe n'a pas d'adresse du tout. Un lien qui ouvre le volume et laisse
    // le joueur au haut d'une grille de deux cents lignes ne l'a mené nulle part.
    // On accepte donc, pour cible, un numéro OU un bout de ce qui est écrit.
    const sansSignes = (s) => String(s == null ? "" : s)
      .normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/\s+/g, " ").trim();

    function viser(cible) {
      const h = A.hote();
      if (!h || cible == null || cible === "") return false;
      const n = String(cible);
      let el = h.querySelector('tr[data-num="' + CSS.escape(n) + '"]');
      if (!el) {
        // Ce qu'on cherche en clair : d'abord les lignes de grille, puis les
        // titres de tableau et les pages. La première qui contient gagne — on ne
        // classe pas, on mène quelque part.
        const aig = sansSignes(n);
        if (!aig) return false;
        const cands = h.querySelectorAll(
          "tbody tr, .book-table-titre, .book-page, figcaption");
        for (let i = 0; i < cands.length; i++) {
          if (sansSignes(cands[i].textContent).indexOf(aig) >= 0) {
            el = cands[i];
            break;
          }
        }
      }
      if (!el) return false;
      if (el.scrollIntoView) el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.remove("book-vise");
      void el.offsetWidth;   // relancer l'animation si l'on revient sur la même
      el.classList.add("book-vise");
      setTimeout(() => el.classList.remove("book-vise"), 2600);
      return true;
  }

    return { indexer, fiche, renvoyer, lien, aller, viser, picto, intitule };
  }

  return { creer };
});
