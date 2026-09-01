// volume.js — LE VOLUME OUVERT : ses grilles, ses pages, sa mine.
//
// C'est la pièce qui RENVOIE UN VOLUME EN OBJET LISIBLE : les tableaux et leur
// tri, les pages suivies et leurs figures, les chiffres teintés, les colonnes
// calculées ajoutées à la lecture sans être écrites au registre. Elle ne décide
// de rien — ni de ce qui paraît sur l'étagère, ni de ce qui est ouvert.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksVolume = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { genre, teinte, poser, tableauxDe, estAdresse, numeroDe,
            nuTexte, nombreDe } = A.lecture;

    // ─────────────────────────────────────────── les chiffres, et le tri
    //
    // UN REGISTRE SE LIT AUTREMENT QU'UNE PAGE. Sur une page, un nombre est un mot
    // comme un autre ; dans une grille de trois cents lignes, c'est le seul chose
    // que l'œil cherche — un compte d'hommes, un jour, une somme, un numéro. On
    // les teinte donc, et l'on chiffre à espacement fixe pour que les colonnes
    // s'alignent d'elles-mêmes sans qu'on ait à déclarer laquelle est numérique.
    //
    // APRÈS `renvoyer`, JAMAIS AVANT : un renvoi est lui aussi un numéro, et il
    // est déjà un lien. L'envelopper d'un second signe le ferait clignoter de
    // deux façons pour dire une seule chose. On saute donc ce qui est déjà posé.
    const CHIFFRE = /\d+(?:[   ]\d{3})*(?:[.,]\d+)?/g;
    function chiffrer(racine) {
      const textes = [];
      (function marche(n) {
        for (let e = n.firstChild; e; e = e.nextSibling) {
          if (e.nodeType === 3) { textes.push(e); continue; }
          if (e.nodeType !== 1) continue;
          const nom = String(e.tagName).toLowerCase();
          if (nom === "svg" || nom === "a") continue;
          if (e.classList && (e.classList.contains("book-renvoi")
            || e.classList.contains("book-chiffre"))) continue;
          marche(e);
        }
      })(racine);
      textes.forEach((t) => {
        const s = t.nodeValue;
        if (!/\d/.test(s)) return;
        CHIFFRE.lastIndex = 0;
        let m, i = 0, frag = null;
        while ((m = CHIFFRE.exec(s))) {
          if (!frag) frag = document.createDocumentFragment();
          if (m.index > i) frag.appendChild(document.createTextNode(s.slice(i, m.index)));
          const sp = document.createElement("span");
          sp.className = "book-chiffre";
          sp.textContent = m[0];
          frag.appendChild(sp);
          i = m.index + m[0].length;
        }
        if (!frag) return;
        if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
        t.parentNode.replaceChild(frag, t);
      });
    }

    // TROIS ÉTATS, PAS DEUX — et le troisième est le plus important. L'ordre du
    // registre veut dire quelque chose : les numéros y montent par série, une
    // affaire à la suite de l'autre, et c'est ainsi que la chose a été écrite. Un
    // tri qui ne se défait pas efface cet ordre-là pour de bon aux yeux du
    // lecteur. Donc : registre → croissant → décroissant → registre.
    //
    // (le genre d'une colonne se mesure dans `lecture.js` : `nuTexte`, `nombreDe`)
    function trier(tab) {
      const thead = tab.tHead;
      const tbody = tab.tBodies[0];
      if (!thead || !tbody || tbody.rows.length < 3) return;
      const ordre = Array.prototype.slice.call(tbody.rows);
      ordre.forEach((tr, i) => { tr.dataset.rang = i; });
      const ths = Array.prototype.slice.call(thead.rows[0].cells);
      let colonne = -1, sens = 0;

      ths.forEach((th, i) => {
        th.dataset.triable = "1";
        // L'EXPLICATION PASSE AVANT LE MODE D'EMPLOI. `trier` s'exécute après la
        // pose des en-têtes et écrasait l'aide des colonnes calculées par
        // « Ranger sur cette colonne » — on perdait la seule phrase qui disait ce
        // que « Attendu » veut dire, pour redire ce que le curseur montre déjà.
        th.title = th.title ? (th.title + "\n\nCliquer pour ranger.")
          : "Ranger sur cette colonne";
        th.addEventListener("click", () => {
          if (colonne === i) sens = (sens + 1) % 3; else { colonne = i; sens = 1; }
          ths.forEach((x) => { delete x.dataset.tri; });
          if (sens === 0) colonne = -1; else th.dataset.tri = sens === 1 ? "haut" : "bas";

          const rangs = Array.prototype.slice.call(tbody.rows);
          if (sens === 0) {
            rangs.sort((a, b) => (+a.dataset.rang) - (+b.dataset.rang));
          } else {
            const val = (tr) => {
              const c = tr.cells[i];
              return c ? c.textContent : "";
            };
            const tout = rangs.every((tr) => {
              const t = nuTexte(val(tr));
              return !t || nombreDe(t) !== null;
            });
            rangs.sort((a, b) => {
              const x = val(a), y = val(b);
              let d;
              if (tout) {
                const nx = nombreDe(x), ny = nombreDe(y);
                // une cellule vide tombe TOUJOURS en bas, dans les deux sens :
                // « rien d'écrit » n'est pas une petite valeur, c'est un trou
                if (nx === null) return ny === null ? 0 : 1;
                if (ny === null) return -1;
                d = nx - ny;
              } else {
                d = nuTexte(x).localeCompare(nuTexte(y), "fr",
                  { numeric: true, sensitivity: "base" });
              }
              return sens === 1 ? d : -d;
            });
          }
          rangs.forEach((tr) => tbody.appendChild(tr));
        });
      });
    }

    // Une page : du texte, ou une FIGURE. Un levé au pas, un plan de salle, un
    // arbre de parenté ne se disent pas en phrases — et le volume qui les porte
    // reste un volume, posé quelque part, qu'on peut refermer et emporter.
    // Le SVG arrive inliné par le serveur (voir inlinerFigure) ; s'il manque, on
    // ne laisse pas un trou muet : un dessin qu'on ne retrouve pas est une
    // information, et le joueur a le droit de savoir que la page existe.
    function page(p) {
      if (p && typeof p === "object" && p.figure) {
        const fig = document.createElement("figure");
        fig.className = "book-figure";
        if (p.figure_svg) {
          fig.innerHTML = p.figure_svg;
        } else {
          const manque = document.createElement("p");
          manque.className = "book-page book-attente";
          manque.textContent = "La feuille manque au volume.";
          fig.appendChild(manque);
        }
        if (p.legende) {
          const l = document.createElement("figcaption");
          poser(l, p.legende);
          if (window.Entites) Entites.traiter(l);
          fig.appendChild(l);
        }
        return fig;
      }
      const par = document.createElement("p");
      par.className = "book-page";
      poser(par, p);
      if (window.Entites) Entites.traiter(par);
      return par;
    }

    function carte(b) {
      // On ne demande le calcul qu'à l'ouverture d'un volume, et une seule fois :
      // il coûte deux secondes au serveur, et la moitié des écrans du jeu n'ouvre
      // jamais un livre. C'est aussi ce qui fait apparaître l'onglet « Les pas » :
      // il n'existe qu'une fois le calcul rentré, et son arrivée redessine.
      A.chargerCriticite();
      const art = document.createElement("article");
      art.className = "book";
      art.style.setProperty("--book-teinte", teinte(b));

      const t = document.createElement("h3");
      if (b.embleme) {
        const e = document.createElement("span");
        e.className = "book-embleme";
        e.textContent = b.embleme;
        t.appendChild(e);
      }
      t.appendChild(document.createTextNode(b.titre || "Sans titre"));
      const g = genre(b);
      if (g) {
        const et = document.createElement("span");
        et.className = "book-genre";
        et.textContent = g.nom;
        t.appendChild(et);
      }
      art.appendChild(A.tete(b, t));
      if (b.sous_titre) {
        const s = document.createElement("div");
        s.className = "book-sous-titre";
        s.textContent = b.sous_titre;
        art.appendChild(s);
      }

      const tableaux = tableauxDe(b);
      let rien = 0;
      tableaux.forEach((sec) => {
        const lignes = sec.lignes;
        rien += lignes.length;
        // Un registre ouvert et encore vierge est une information : on montre ses
        // colonnes, réglées, et l'on dit qu'il attend sa première ligne.
        if (!lignes.length && !sec.colonnes.length) return;
        // Le titre d'un tableau se pose AU-DESSUS et hors de la grille : dans une
        // <caption>, il se collerait au tableau à la copie et se perdrait au
        // défilement horizontal, qui est justement le cas d'une affaire large.
        if (sec.titre) {
          const h = document.createElement("div");
          h.className = "book-table-titre";
          poser(h, sec.titre);
          art.appendChild(h);
        }
        const enveloppe = document.createElement("div");
        enveloppe.className = "book-table-enveloppe";
        const tab = document.createElement("table");
        tab.className = "book-table";
        // Une ligne qui porte un numéro devient une adresse : c'est elle qu'on
        // vise quand on clique le renvoi qui la cite, d'ici ou d'un autre volume.
        const adresse = estAdresse(sec);
        // Y a-t-il seulement un score à montrer ici ? On regarde AVANT de poser
        // les en-têtes : trois colonnes vides sur un tableau de moyens, ce serait
        // trois colonnes de largeur perdue pour dire « rien ».
        const scores = (adresse && S.crit && S.crit.pas
          && lignes.some((l) => S.crit.pas[numeroDe(l)])) ? S.crit.pas : null;
        // UN ÉTAT CIBLE N'EST PAS UN PAS : on ne le « rate » pas, on l'atteint ou
        // non. Sa colonne n'est donc pas une perte — c'est son poids, et le fait
        // qu'une chaîne mène jusqu'à lui. Vingt-six sur cent trente-neuf n'en ont
        // aucune, et c'est ce qu'un registre d'états cibles doit dire en premier.
        const buts = (!scores && adresse && S.crit && S.crit.etats
          && lignes.some((l) => S.crit.etats[numeroDe(l)])) ? S.crit.etats : null;
        const ajout = scores ? A.COLS_CRIT : (buts ? A.COLS_BUT : []);
        const passagePossible = typeof BooksPassageReception !== "undefined"
          && lignes.some((l) => BooksPassageReception.preparer(b, sec.colonnes, l));
        if (sec.colonnes.length) {
          const thead = document.createElement("thead");
          const tr = document.createElement("tr");
          sec.colonnes.concat(passagePossible ? ["Second essai"] : []).concat(ajout).forEach((c) => {
            const th = document.createElement("th");
            th.textContent = c;
            if (ajout.indexOf(c) >= 0) {
              th.dataset.calcule = "1";
              th.title = (A.AIDE[c] || "") + A.HORS;
            }
            tr.appendChild(th);
          });
          thead.appendChild(tr);
          tab.appendChild(thead);
        }
        const tbody = document.createElement("tbody");
        lignes.forEach((l) => {
          const tr = document.createElement("tr");
          const num = adresse ? numeroDe(l) : null;
          if (num) tr.dataset.num = num;
          (l.cellules || []).forEach((c, i) => {
            const td = document.createElement("td");
            if (num && i === 0) td.dataset.ancre = "1";
            poser(td, c);
            // la note pend sous la dernière colonne : c'est une mention de marge
            if (l.note && i === (l.cellules.length - 1)) {
              const n = document.createElement("div");
              n.className = "book-note";
              poser(n, l.note);
              td.appendChild(n);
            }
            if (window.Entites) Entites.traiter(td);
            tr.appendChild(td);
          });
          if (passagePossible) {
            const td = document.createElement("td");
            td.className = "book-passage-cellule";
            const passage = BooksPassageReception.preparer(b, sec.colonnes, l);
            if (passage) {
              const lien = document.createElement("a");
              lien.className = "book-passage-reception";
              lien.href = BooksPassageReception.href(passage);
              lien.textContent = "Former le bordereau";
              lien.title = "Préremplir un second essai sans transmettre le verdict ni la preuve antérieurs";
              td.appendChild(lien);
            }
            tr.appendChild(td);
          }
          if (scores) {
            const s = scores[num] || {};
            // UN CERCLE SE DIT AVANT UN CHIFFRE. Une pièce prise dans une chaîne
            // qui se mord la queue a une perte de zéro — non parce qu'elle est
            // substituable, mais parce que rien derrière elle n'est atteignable.
            // Afficher « 0 » là serait le contraire de la vérité.
            [s.perte, s.portee, s.attendu].forEach((v, k) => {
              const td = document.createElement("td");
              td.className = "book-calcule";
              if (s.cercle != null && k === 0) {
                td.textContent = "🔁";
                td.title = "Prise dans un cercle de dépendances : rien ne part.";
              } else {
                td.textContent = v ? String(v) : "—";
              }
              if (k === 0 && v) td.dataset.poids = v >= 10 ? "fort"
                : (v >= 3 ? "moyen" : "faible");
              tr.appendChild(td);
            });
          }
          if (buts) {
            const e = buts[num] || {};
            const tp = document.createElement("td");
            tp.className = "book-calcule";
            tp.textContent = e.poids != null ? String(e.poids) : "—";
            const ta = document.createElement("td");
            ta.className = "book-calcule";
            ta.textContent = e.poids == null ? "—" : (e.atteignable ? "✅" : "🚫");
            if (e.poids != null && !e.atteignable) {
              ta.title = "Aucune chaîne écrite ne mène jusqu'à cet état.";
              ta.dataset.poids = "fort";
            }
            tr.appendChild(tp);
            tr.appendChild(ta);
          }
          tbody.appendChild(tr);
        });
        tab.appendChild(tbody);
        trier(tab);
        enveloppe.appendChild(tab);
        art.appendChild(enveloppe);
      });

      (b.pages || []).forEach((p) => art.appendChild(page(p)));

      if (!rien && !(b.pages || []).length) {
        const vide = document.createElement("p");
        vide.className = "book-page book-attente";
        vide.textContent = "Rien n'y est encore écrit.";
        art.appendChild(vide);
      }

      // En dernier, sur le volume entier : les cellules, les notes de marge, les
      // titres de tableau et les pages suivies citent tous des numéros.
      A.renvoyer(art);
      // Les chiffres en dernier, et seulement dans les grilles : dans une page
      // suivie, un nombre est un mot de la phrase, et le teinter la trouerait.
      art.querySelectorAll(".book-table td").forEach(chiffrer);

      return art;
  }

    return { chiffrer, trier, page, carte };
  }

  return { creer };
});
