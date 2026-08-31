// etagere.js — L'ÉTAGÈRE : ce qui est à portée, ce qui est ouvert, et le tracé.
//
// C'est la pièce qui DÉCIDE, et la seule qui parle au serveur. Elle demande
// l'étagère, refait le tracé quand la salle change ou qu'un homme entre avec
// son carnet, branche l'échelle au décor, et POSE ce que les autres rendent —
// les rubans d'onglets (`onglets.js`), la carte d'un coffret, celle d'un volume.
//
// ELLE ÉCRIT `S.books`, `S.charge`, `S.ferme` et les trois constats du dernier
// tracé — personne d'autre n'y touche. `S.ouvert` et `S.ouverteBoite`, elle les
// partage avec `onglets.js`, qui les tranche à chaque tracé : voir l'avertissement
// en tête de cette pièce-là.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksEtagere = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {

    function dessiner() {
      const h = A.hote();
      if (!h) return;
      // L'ONGLET DOIT ÊTRE LÀ AVANT QU'ON OUVRE QUOI QUE CE SOIT. Le calcul était
      // demandé à l'ouverture d'un volume ; « Les pas » n'apparaissait donc
      // qu'après en avoir lu un autre — c'est-à-dire jamais pour qui vient
      // justement le chercher. On le demande à l'étagère.
      A.chargerCriticite();
      // On refait l'étagère à neuf : si le joueur avait la main dans ses notes
      // (une salle qui change pendant qu'il écrit), on lui rend sa place à la
      // ligne près, sinon il retrouve son curseur au début du carnet.
      const z = document.getElementById("book-notes-zone");
      const ecrivait = z && z === document.activeElement
        ? { debut: z.selectionStart, fin: z.selectionEnd } : null;
      S.salleVue = A.salleCourante();
      S.portantsVus = A.portants();
      // L'index des numéros suit l'étagère : un homme qui sort avec son cahier
      // emporte les renvois qui y menaient.
      A.indexer();
      h.innerHTML = "";
      const corps = document.createElement("div");
      corps.className = "books-corps";

      const dedans = A.rangs();
      // L'étagère n'est jamais vide — le carnet du joueur y est toujours. Mais
      // une salle sans livre reste une information : on la dit au-dessus, plutôt
      // que de laisser croire qu'il n'y avait rien à y chercher.
      const seulesNotes = dedans.length === 1 && dedans[0].notes;
      if (seulesNotes && S.books) {
        const ou = document.createElement("div");
        ou.className = "books-ou";
        const p = document.createElement("p");
        p.className = "books-vide";
        // Une page sans siège n'a pas une étagère vide : elle n'a pas d'étagère.
        // Le serveur ferme et le dit ; on ne fait pas croire qu'il n'y avait rien
        // à chercher dans la salle — le joueur irait chercher la faute au MJ.
        if (S.ferme) {
          ou.textContent = "L'étagère est close";
          p.textContent = "Cette page n'est assise à aucun siège : ouvrez le jeu "
            + "par votre lien, et vos livres reviennent.";
        } else {
          const nom = A.nomSalle(S.salleVue);
          ou.textContent = nom ? "Ce qui traîne ici — " + nom : "Ce qui traîne ici";
          p.textContent = "Rien à lire ici, et personne n'a sorti son carnet.";
        }
        corps.appendChild(ou);
        corps.appendChild(p);
      }

      // GROUPER, ÉLIRE, POSER LES ONGLETS — tout cela vit à côté
      // (`onglets.js`). ⚠ `ranger` ÉCRIT `S.ouvert` et `S.ouverteBoite` : élire,
      // c'est décider, et l'on ne l'appelle donc qu'une fois par tracé.
      const { entrees, active } = A.ranger(dedans);
      A.tranches(entrees, active, dedans, seulesNotes)
        .forEach((n) => corps.appendChild(n));

      const lu = S.ouvert ? dedans.find((b) => b.id === S.ouvert) : null;
      if (lu) corps.appendChild(lu.notes ? A.carteNotes() : A.carte(lu));
      else if (active.boite) corps.appendChild(A.carteBoite(active));
      h.appendChild(corps);

      if (ecrivait) {
        const nz = document.getElementById("book-notes-zone");
        if (nz) {
          nz.focus();
          try { nz.setSelectionRange(ecrivait.debut, ecrivait.fin); } catch (e) {}
        }
      }
    }

    function charger() {
      if (S.charge) return;
      S.charge = true;
      A.chargerNotes();
      // Le serveur ne sert que l'étagère de CE siège, et il la coupe au château
      // où l'on se trouve : la réponse dépend donc d'où l'on est au moment où on
      // la demande. On retient ce château-là — un homme qui débarque ailleurs
      // doit redemander l'étagère, sans quoi il emporte celle qu'il a quittée.
      S.chateauVu = A.chateauCourant();
      fetch("/books").then((r) => r.json()).then((d) => {
        S.books = (d && d.books) || [];
        S.boites = (d && d.boites) || [];
        S.ferme = !!(d && d.siege === false);
        // Une page ouverte AVANT que le serveur ait appris les coffrets garde sa
        // liste jusqu'au prochain changement de château — c'est-à-dire, le plus
        // souvent, jamais : les volumes rangés disparaissent de l'étagère et l'on
        // croit le rangement cassé. Des livres qui se disent dans une boîte sans
        // qu'aucune boîte ne descende : la liste est périmée, on la redemande.
        // Une seule fois : si le serveur ne sait décidément rien des coffrets,
        // c'est qu'il est vieux, et redemander toutes les quatre secondes ne le
        // rajeunira pas.
        if (!S.perime && !S.boites.length && S.books.some((b) => b.boite) && !S.ferme) {
          S.perime = true;
          S.charge = false;
          setTimeout(charger, 4000);
        }
        dessiner();
        if (window.Plan && Plan.rebattre) Plan.rebattre();
      }).catch(() => { S.charge = false; });
    }

    function relire() { S.charge = false; charger(); }

    // OUVRIR UN VOLUME NOMMÉ, depuis ailleurs que l'étagère — c'est ce qui permet
    // au fil de dire « porté au registre » avec un lien qui y mène. Sans ça, le
    // joueur doit croire le MJ sur parole que ce qui s'est dit a été écrit.
    // `cible` est facultative : un numéro d'adresse, ou un bout de ce qui est
    // écrit là (« EC.4 », « deux colonnes à tout registre »). Le volume s'ouvre
    // et l'on DESCEND jusqu'à la ligne, au lieu de laisser le joueur au haut
    // d'une grille où il doit rechercher ce qu'on venait de lui montrer.
    function ouvrir(livreId, cible) {
      if (!livreId) return false;
      const trouve = (S.books || []).find((b) => b && b.id === livreId);
      if (!trouve) return false;
      S.ouvert = livreId;
      S.ouverteBoite = trouve.boite || null;
      if (window.Plan && Plan.montrer) Plan.montrer("books");
      dessiner();
      const h = A.hote();
      if (h && h.scrollIntoView) h.scrollIntoView({ behavior: "smooth", block: "nearest" });
      // La ligne visée l'emporte sur le volume : deux `scrollIntoView` de suite
      // se règlent l'un l'autre, et c'est le second qu'on veut voir gagner.
      if (cible != null && cible !== "") A.viser(cible);
      return true;
    }

    // ---- BRANCHER L'ÉCHELLE AU DÉCOR ------------------------------------------
    // Tout ceci se faisait au chargement du module ; ça se demande maintenant en
    // un geste, depuis `books.js`. Rien d'autre n'a changé — même écoute, même
    // intervalle, même ordre.
    function brancher() {
      if (window.Plan && Plan.echelle) {
        Plan.echelle({
          id: "books", nom: "Les livres", hote: "books", ordre: 6,
          // L'échelle était masquée là où il n'y avait rien à ouvrir — un livre
          // se consulte dans la salle où il est posé. Depuis que le joueur a son
          // carnet, il y a toujours quelque chose : `ici()` n'est jamais vide.
          dispo: () => A.ici().length > 0,
          reparu: () => {
            if (S.salleVue !== A.salleCourante() || S.portantsVus !== A.portants()) dessiner();
          },
        });
      }
      // Ce qui fait un endroit ici : le coffret ouvert, et le volume qu'on y lit.
      // Sans cela, revenir aux livres rendait l'étagère fermée — l'échelle était
      // gardée, la page ne l'était pas.
      if (window.Nav) {
        Nav.enregistrer("books", {
          clefs: ["coffret", "livre"],
          etat: () => ({ coffret: S.ouverteBoite, livre: S.ouvert }),
          poser: (p) => {
            if (!p.livre && !p.coffret) return true;
            if (p.livre && p.livre === S.ouvert) return true;
            if (!p.livre && p.coffret === S.ouverteBoite) return true;
            if (!S.books) return false;              // l'étagère n'est pas rentrée
            if (p.livre) return ouvrir(p.livre);
            const c = S.boites.find((b) => b && b.id === p.coffret);
            if (!c) return false;
            S.ouverteBoite = p.coffret; S.ouvert = null;
            dessiner();
            return true;
          },
        });
      }
      // Le registre des gens arrive après la première étagère : une carte de
      // coffret dessinée avant lui montre des noms sans visage. On se fait
      // rappeler une fois, et l'on redessine avec les têtes.
      if (window.Gens && Gens.quand) Gens.quand(() => dessiner());
      // la salle change sans prévenir personne, et un homme entre avec son carnet
      // sans rien annoncer non plus : on suit les deux de loin, ça ne coûte que
      // deux comparaisons de chaînes.
      setInterval(() => {
        // Changer de château, c'est changer d'étagère : ce n'est plus un tracé à
        // refaire, c'est une liste à redemander. On ne rappelle rien tant qu'on
        // ne sait pas où l'on est (au chargement, `chateauCourant()` est nul le
        // temps que la carte arrive) — le serveur, lui, l'a toujours su.
        const ch = A.chateauCourant();
        if (ch && !S.chateauVu) S.chateauVu = ch;       // la carte vient d'arriver
        else if (ch && S.chateauVu !== ch) { relire(); return; }
        if (S.salleVue === A.salleCourante() && S.portantsVus === A.portants()) return;
        dessiner();
        if (window.Plan && Plan.rebattre) Plan.rebattre();
      }, 1000);
    }

    return { dessiner, charger, relire, ouvrir, brancher };
  }

  return { creer };
});
