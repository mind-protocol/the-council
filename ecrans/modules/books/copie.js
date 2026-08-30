// copie.js — RECOPIER UN VOLUME, ET LA LIGNE DE TITRE QUI LE PERMET.
//
// Un registre se recopie : c'est ce qu'on fait d'un registre depuis toujours.
// Cette pièce rend le volume en texte nu et le pose au presse-papier, avec la
// vieille manière en second — la partie se joue aussi par un tunnel qui n'est
// pas toujours un contexte sûr, et un bouton qui ment une fois sur deux ne vaut
// rien. Elle tient aussi la ligne de titre où ce bouton se range, avec celui
// qui mène à l'échiquier.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksCopie = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { tableauxDe } = A.lecture;

    // ---- Copier le volume -----------------------------------------------------
    // Un registre se recopie : c'est ce qu'on fait d'un registre depuis toujours.
    // On rend le volume en texte nu — le titre, les colonnes séparées par des
    // tabulations, les pages —, tel qu'il se lit, appuis compris : ce qui est
    // collé ailleurs doit être le même objet, pas un résumé.
    function texteDe(b) {
      if (b.notes) return S.notes;
      const l = [];
      l.push(b.titre || "Sans titre");
      if (b.sous_titre) l.push(b.sous_titre);
      tableauxDe(b).forEach((sec) => {
        if (!sec.colonnes.length && !sec.lignes.length) return;
        l.push("");
        if (sec.titre) l.push(sec.titre);
        if (sec.colonnes.length) l.push(sec.colonnes.join("\t"));
        sec.lignes.forEach((li) => {
          l.push((li.cellules || []).map((c) => c == null ? "" : String(c)).join("\t"));
          if (li.note) l.push("\t" + li.note);
        });
      });
      (b.pages || []).forEach((p) => {
        l.push("");
        // Une figure ne se recopie pas en texte : on dit qu'elle est là, avec sa
        // légende, plutôt que de laisser un trou dans la copie.
        if (p && typeof p === "object") {
          l.push("[figure" + (p.legende ? " — " + p.legende : "") + "]");
        } else {
          l.push(p == null ? "" : String(p));
        }
      });
      return l.join("\n");
    }

    // Le presse-papier moderne demande un contexte sûr ; la partie se joue aussi
    // par un tunnel qui n'en est pas toujours un. On garde la vieille manière en
    // second, sinon le bouton ment une fois sur deux.
    function auPressePapier(texte) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        // Le refus arrive aussi quand l'API existe : page pas au premier plan,
        // permission coupée. On retombe alors sur la vieille manière au lieu de
        // dire au joueur que ça n'a pas marché.
        return navigator.clipboard.writeText(texte).catch(() => vieilleManiere(texte));
      }
      return vieilleManiere(texte);
    }

    function vieilleManiere(texte) {
      return new Promise((ok, non) => {
        const z = document.createElement("textarea");
        z.value = texte;
        z.setAttribute("readonly", "");
        z.style.cssText = "position:fixed;top:-9999px;opacity:0;";
        document.body.appendChild(z);
        z.select();
        let fait = false;
        try { fait = document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(z);
        fait ? ok() : non(new Error("refus"));
      });
    }

    function boutonCopier(b) {
      const bt = document.createElement("button");
      bt.className = "book-copier";
      bt.type = "button";
      bt.textContent = "Copier";
      bt.title = "Recopier ce volume";
      bt.onclick = () => {
        const texte = texteDe(b);
        auPressePapier(texte).then(() => {
          bt.textContent = "Copié";
          bt.classList.add("fait");
        }).catch(() => {
          bt.textContent = "Pas copié";
        }).then(() => {
          setTimeout(() => {
            bt.textContent = "Copier";
            bt.classList.remove("fait");
          }, 1600);
        });
      };
      return bt;
    }

    // Le titre et sa main droite : on ne pose pas un bouton dans un titre, on
    // met les deux sur la même ligne.
    function tete(b, t) {
      const d = document.createElement("div");
      d.className = "book-tete";
      d.appendChild(t);
      const plateau = boutonPlateau(b);
      if (plateau) d.appendChild(plateau);
      d.appendChild(boutonCopier(b));
      return d;
    }

    // Le cahier d'une affaire a un plateau, et le plateau a ce cahier : le
    // chemin se fait dans les deux sens. Rien pour les volumes qui n'en ont pas
    // — on ne pose pas un bouton mort.
    function boutonPlateau(b) {
      if (!b || !window.Echiquier || !Echiquier.pourLivre) return null;
      const a = Echiquier.pourLivre(b.id);
      if (!a) return null;
      const bt = document.createElement("button");
      bt.className = "book-plateau";
      bt.type = "button";
      bt.innerHTML = '<i>⚄</i><span>L\'échiquier</span>';
      bt.title = "Voir cette affaire sur l'échiquier";
      bt.onclick = () => Echiquier.montrer(a.id);
      return bt;
  }

    return { texteDe, auPressePapier, boutonCopier, tete, boutonPlateau };
  }

  return { creer };
});
