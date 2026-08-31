// idees.js — CE QU'IL Y AURAIT À FAIRE, SOUS CHAQUE AFFAIRE.
//
// Le savoir vit sur l'autre échelle — l'échiquier —, et l'on n'y va pas quand
// on cherche un cahier. Cette pièce le fait descendre ici, une ligne par
// affaire, en retrait, derrière un interrupteur éteint par défaut.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksIdees = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {

    // ---- LES IDÉES : la mission de tête d'une affaire, sous son volume --------
    // Le coffret « Les sujets » aligne trente-huit affaires ; l'échiquier sait,
    // pour chacune, ce qu'il y aurait à faire — et ce savoir restait sur l'autre
    // échelle, où l'on ne va pas quand on cherche un cahier. L'interrupteur le
    // fait descendre ici, une ligne par affaire, en retrait.
    //
    // ON NE RECALCULE RIEN. La route `/echiquier` dérive déjà les missions et
    // range dans chaque affaire son `idee` — l'acte de tête, classé par la force
    // de son effet, sa portée, puis son coût. On rapproche par `livre_id`, qui
    // est l'appariement affaire↔volume que le serveur a déjà fait, et par rien
    // d'autre : un volume que ce rapprochement ne trouve pas n'affiche rien, et
    // son silence est l'information — c'est une affaire ouverte qui n'a encore
    // aucune ligne aux registres du plan.

    function chargerIdees() {
      if (S.ideesChargees) return;
      S.ideesChargees = true;
      fetch("/echiquier").then((r) => r.json()).then((d) => {
        const cat = (d && d.missions) || {};
        S.parLivre = {};
        ((d && d.affaires) || []).forEach((a) => {
          if (a.livre_id && a.idee && cat[a.idee]) {
            S.parLivre[a.livre_id] = { m: cat[a.idee], titre: a.titre };
          }
        });
        if (S.idees) A.dessiner();
      }).catch(() => { S.ideesChargees = false; });
    }

    // La phrase, dans le gabarit de l'échiquier — afin d'atteindre X, faire Y
    // aurait effet Z — composée par la même main que la bulle du plateau, pour
    // que les deux ne disent jamais deux choses de la même affaire.
    function traitIdee(m) {
      const d = document.createElement("div");
      d.className = "book-idee book-idee-" + (m.sur === "reine" ? "reine" : "conseil");
      const lampe = document.createElement("span");
      lampe.className = "book-idee-lampe";
      lampe.textContent = "\u{1F4A1}";
      d.appendChild(lampe);
      const mot = (t) => d.appendChild(document.createTextNode(t));
      // Les signes du guide « Comment on ouvre une affaire », les mêmes que sur
      // le plateau : c'est à ça qu'on reconnaît que c'est la même chose.
      const SIGNES = { etat: "\u{1F3AF}", verrou: "\u{1F512}",
        clef: "\u{1F5DD}️", action: "⚔️" };
      const piece = (q) => {
        if (!q) return;
        const s = document.createElement("span");
        s.className = "book-idee-cite";
        if (SIGNES[q.genre]) {
          const i = document.createElement("span");
          i.className = "book-idee-signe";
          i.textContent = SIGNES[q.genre];
          s.appendChild(i);
        }
        const t = document.createElement("i");
        t.textContent = q.nom;
        s.appendChild(t);
        d.appendChild(s);
      };
      if (m.but && !(m.piece && m.but.numero === m.piece.numero)) {
        mot("Afin d'atteindre ");
        piece(m.but);
        if (m.buts_autres) {
          mot(m.buts_autres > 1 ? " (et " + m.buts_autres + " autres états cibles)"
            : " (et un autre état cible)");
        }
        mot(", ");
      }
      mot(m.verbe + " ");
      piece(m.piece);
      if (m.effet) { mot(" " + m.effet); if (m.vers) { mot(" "); piece(m.vers); } }
      if (m.precision) mot(" — " + m.precision);
      mot(".");
      return d;
    }

    // ---- Les notes : le carnet du JOUEUR, hors du monde ---------------------
    // Un volume de plus sur l'étagère, et le seul qui ne soit pas un objet de la
    // fiction : personne ne l'écrit dans la salle, aucun PNJ ne le lit, le MJ
    // n'y touche pas. Le joueur y met ce qu'il veut, tel quel, et ça reste. Il
  // est toujours à portée — on ne pose pas ses propres notes sur une table, et

    return { chargerIdees, traitIdee };
  }

  return { creer };
});
