// portee.js — OÙ EST UN VOLUME, ET QUI PEUT L'OUVRIR D'ICI.
//
// C'est la pièce qui tient le BROUILLARD de cette échelle : un registre posé
// dans une salle, un carnet dans la poche d'un homme, un volume qui nomme ses
// lecteurs. Tout ce qui décide si une chose paraît sur l'étagère passe par ici
// — et nulle part ailleurs, pour qu'une fuite se rebouche en un seul endroit.
//
// Elle tient aussi l'ORDRE de l'étagère : le plus frais devant, ce qu'on vient
// de toucher sur le dessus. C'est la même question — ce qu'on a sous la main.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksPortee = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  /**
   * `creer(S, A)` — `S` l'état, `A` l'assemblage.
   *
   * On prend l'assemblage entier plutôt que les quelques fonctions qu'on
   * appelle : `ici()` a besoin du volume calculé et du carnet du joueur, qui
   * sont montés APRÈS cette pièce. Les helpers de lecture, eux, ne dépendent de
   * rien et se prennent tout de suite.
   */
  function creer(S, A) {
    const { tableauxDe } = A.lecture;
    function hote() { return document.getElementById("books"); }
    const salleCourante = () =>
      (window.Plan && Plan.salle) ? Plan.salle() : null;
    const chateauCourant = () =>
      (window.Plan && Plan.chateau) ? Plan.chateau() : null;

    function nomSalle(id) {
      const p = (window.Plans || {})[chateauCourant()];
      const s = p && (p.salles || []).find((x) => x.id === id);
      return s ? s.nom : null;
    }

    const moi = () => (window.Moi && window.Moi.personnage_id) || null;
    const present = (id) => !!(window.Presents && window.Presents[id]);
    const nomActeur = (id) => {
      const p = (window.Presents || {})[id];
      if (p && p.nom) return p.nom;
      const f = window.Gens && Gens.qui ? Gens.qui(id) : null;
      return (f && f.nom) || String(id || "").replace(/-/g, " ");
    };

    // Un livre posé : il appartient au château, et l'on peut aller le chercher.
    // On ne l'a d'abord montré que dans SA salle — et l'on a vu ce que ça donne :
    // celle qui tient les écritures descend à la porte du Dragon, et le registre
    // des communications disparaît de son écran. Un registre de maison n'est pas
    // un secret, c'est un meuble : il reste consultable de tout le château, et
    // l'on dit simplement où il se trouve. Ce qui reste strict, c'est le carnet
    // que quelqu'un porte sur lui.
    function poseIci(b) {
      if (!b.salle_id) return false;
      const chateau = chateauCourant();
      return !b.lieu_id || !chateau || b.lieu_id === chateau;
    }

    // Est-il sous la main, ou faut-il monter le chercher ?
    const sousLaMain = (b) => !!b.salle_id && b.salle_id === salleCourante();

    // Un livre porté : il vaut ce que vaut la présence de son porteur. Le mien
    // est toujours sur moi ; celui d'un autre ne s'ouvre que s'il est dans la
    // salle, et jamais s'il le tient pour lui.
    function porteIci(b) {
      if (!b.acteur_id) return false;
      if (b.acteur_id === moi()) return true;
      if (b.prive) return false;
      return present(b.acteur_id);
    }

    // Un volume peut NOMMER ses lecteurs. C'est ce qui manquait au carnet des
    // yeux : posé sur la Table Peinte, marqué `prive`, et donc privé de personne —
    // un `prive` sans porteur n'a pas de propriétaire, et le carnet s'ouvrait à
    // quiconque entrait dans le château. `lecteurs` ne DONNE rien : il retire. Le
    // volume reste où il est, avec ses règles de salle et de château ; simplement,
    // qui n'y est pas nommé ne l'ouvre pas. Un carnet qui ne quitte pas la chambre
    // ne se lit pas non plus depuis l'autre bout du royaume parce qu'on y a son nom.
    const lecteurs = (b) => Array.isArray(b.lecteurs) && b.lecteurs.length
      ? b.lecteurs : null;
    const permis = (b) => {
      const l = lecteurs(b);
      return !l || l.indexOf(moi()) !== -1;
    };

    // Ceux qu'on peut ouvrir d'où l'on est. Les notes du joueur ferment toujours
    // la marche : elles ne sont nulle part dans le château, donc partout.
    function ici() {
      const dedans = S.books ? S.books.filter(
        (b) => permis(b) && (poseIci(b) || porteIci(b))) : [];
      const p = A.volumePas();
      if (p) dedans.push(p);
      dedans.push(A.NOTE);
      return dedans;
    }

    // Qui, dans la salle, porte quelque chose : c'est ce qui fait apparaître et
    // disparaître l'onglet quand un homme entre ou sort.
    function portants() {
      if (!S.books) return "";
      return S.books.filter(porteIci).map((b) => b.acteur_id).sort().join(",");
    }

    // Le coffret d'un volume, s'il est rangé quelque part.
    const coffret = (b) =>
      (b && b.boite && S.boites.find((c) => c.id === b.boite)) || null;

    // LE CALCUL VOIT TOUT LE PLAN ; CE VOLUME NE DOIT MONTRER QUE CE QUE CE SIÈGE
    // PEUT OUVRIR. `/criticite` est une route de machine : elle ne connaît ni
    // siège, ni salle, ni `lecteurs`, et rend les quarante-deux affaires du
    // dépôt — les cahiers `nera-*` de Marlo compris. Poussé tel quel sur
    // l'étagère, ce volume les servait à Rhaenyra, qui n'en tient qu'une.
    //
    // On le borne donc sur L'ÉTAGÈRE ELLE-MÊME : le serveur a déjà fait le tri du
    // brouillard pour `books`, et un cahier qu'on ne peut pas ouvrir n'a pas à
    // livrer ses chiffres. C'est la même règle qu'ailleurs, appliquée une fois de
    // plus — pas une règle de plus.
    function affairesVues() {
      const vues = new Set();
      (S.books || []).forEach((b) => {
        if (!permis(b) || !(poseIci(b) || porteIci(b))) return;
        const t = String(b.titre == null ? "" : b.titre).replace(/\*\*/g, "").trim();
        if (t) vues.add(t);
        // Un registre par type ne PORTE pas une affaire, il la CITE : ses lignes
        // nomment des cahiers qu'on a le droit de lire d'ici, sinon il ne serait
        // pas sur l'étagère. On prend donc aussi ce qu'il nomme.
        tableauxDe(b).forEach((sec) => {
          const i = (sec.colonnes || []).findIndex((c) => /Affaire/i.test(String(c)));
          if (i < 0) return;
          (sec.lignes || []).forEach((l) => {
            const c = (l.cellules || [])[i];
            const v = String(c == null ? "" : c).replace(/\*\*/g, "").trim();
            if (v) vues.add(v);
          });
        });
      });
      return vues;
    }

    // D'où vient ce livre — ce qui tient lieu de sous-titre à son onglet.
    function provenance(b) {
      if (b.notes) return "Sur vous, hors du monde";
      // Un volume calculé n'est nulle part : il n'a ni salle ni porteur, et
      // demander où il est n'a pas de sens. Sans cette ligne il tombait dans le
      // dernier cas et s'annonçait « Porté par » suivi de rien.
      if (b.calcule) return "Nulle part — refait à chaque ouverture";
      if (poseIci(b)) {
        const nom = nomSalle(b.salle_id);
        if (sousLaMain(b)) return nom ? "Ici — " + nom : "Ici, sous la main";
        return nom ? "Reste " + (/^(Le |La |L')/.test(nom) ? "à " + nom : "dans " + nom)
                   : "Ailleurs dans le château";
      }
      return b.acteur_id === moi() ? "Sur vous" : "Porté par " + nomActeur(b.acteur_id);
    }

    // Plusieurs livres dans la même salle ne s'empilent pas : ils se rangent en
    // onglets, comme des volumes sur une étagère. On en ouvre un à la fois — un
    // homme ne lit pas deux registres en même temps.
    // Le plus frais devant. On rangeait par PROXIMITÉ — sous la main, puis le
    // sien, puis ce qu'il fallait aller chercher — et c'était une étagère : un
    // ordre qui ne bouge jamais, où le registre qu'on vient de remplir reste
    // enfoui au même endroit qu'hier. Une table de travail se range autrement :
    // ce qu'on vient de toucher est sur le dessus.
    //
    // La fraîcheur se lit d'abord dans `date_maj` (une date de jeu, écrite par
    // qui touche le volume), et à défaut dans la POSITION dans books.json : un
    // volume ajouté l'a été après les autres, et c'est déjà une information. Rien
    // de neuf à tenir, donc, et un volume sans date n'est pas puni — il garde son
    // rang d'arrivée.
    const quand = (b) => {
      const d = b.date_maj;
      if (!d) return -1;
      return ((d.annee || 0) * 12 + (d.lune || 0)) * 30 * 1440
        + (d.jour || 0) * 1440 + (d.minute || 0);
    };

    function rangs() {
      const dedans = ici();
      // L'ordre du fichier, pour départager ceux qui n'ont pas de date : plus
      // loin dans books.json veut dire posé plus tard.
      const arrivee = new Map((S.books || []).map((b, i) => [b.id, i]));
      return dedans.slice().sort((a, b) => {
        // Les notes du joueur ferment toujours la marche : elles ne sont pas du
        // monde, elles n'ont pas de fraîcheur, et elles sont toujours à portée.
        if (a.notes !== b.notes) return a.notes ? 1 : -1;
        const da = quand(a), db = quand(b);
        if (da !== db && (da >= 0 || db >= 0)) return db - da;
        return (arrivee.get(b.id) || 0) - (arrivee.get(a.id) || 0);
      });
    }

    return { hote, salleCourante, chateauCourant, nomSalle, moi, present,
             nomActeur, poseIci, sousLaMain, porteIci, lecteurs, permis, ici,
             portants, coffret, affairesVues, provenance, quand, rangs };
  }

  return { creer };
});
