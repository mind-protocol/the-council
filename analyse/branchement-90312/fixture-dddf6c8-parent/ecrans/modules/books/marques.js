// marques.js — CE QU'ON LIT D'UN VOLUME SANS L'OUVRIR.
//
// Trente-sept affaires dont chaque ligne portait le même mot (« Plan ») et le
// même début de sous-titre : une colonne qui dit la même chose sur toutes les
// lignes n'aide personne à choisir. Ce qui distingue une affaire d'une autre est
// DÉJÀ écrit dedans — le pilier qu'elle sert, l'état de ses actions, ce qu'elle
// pèse au plan. On ne l'écrit donc nulle part : on le REMONTE, et c'est tout ce
// que fait cette pièce.
//
// ELLE REND DEUX CELLULES, PAS UNE LIGNE. Le coffret tient la ligne — son clic,
// son signe, son nom, son ordre ; les marques tiennent ce qui se lit dedans. La
// frontière est celle-là et pas une autre : `marques.js` ne sait rien du
// coffret qui l'affiche, et pourrait servir n'importe quelle liste de volumes.
//
// ⚠ LES DEUX CELLULES ÉCRIVENT `tr.title`, et il faut le savoir avant de les
// appeler : le poids y met sa criticité, le mot y met le sous-titre quand il y
// a des marques. C'est un effet de bord, pas une lecture — l'ordre d'appel
// décide donc de l'infobulle, et il est celui d'origine : le poids d'abord.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé en sortant
// de `coffret.js`.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksMarques = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { genre, sansAccent } = A.lecture;

    // ---- Les marques — ce qu'on lit d'un volume SANS l'ouvrir ---------------
    // Trente-sept affaires dont chaque ligne portait le même mot (« Plan ») et le
    // même début de sous-titre (« Affaire ouverte à la Table Peinte le 26e jour
    // de la 3e lune… ») : une colonne qui dit la même chose sur toutes les lignes
    // n'aide personne à choisir. Ce qui distingue une affaire d'une autre est
    // DÉJÀ écrit dedans — le pilier qu'elle sert, et l'état de ses actions. On ne
    // l'écrit donc nulle part : on le remonte.
    //
    // Deux marques, pas plus. Le PILIER dit à quoi ça sert (quatre valeurs, plus
    // les garants qui les servent tous) et porte la couleur ; l'AVANCEMENT dit où
    // ça en est, et c'est le seul chiffre qui bouge tout seul. Une troisième
    // marque ne paraît que quand elle alarme : ce qui est bloqué, ce qui n'est pas
    // écrit. Le reste est dans le volume, à un clic.
    const PILIERS = [
      { id: "attaque",  cherche: "etre pas attaque",     nom: "n'être pas attaqué" },
      { id: "ville",    cherche: "preparer la ville",    nom: "préparer la ville" },
      { id: "rallier",  cherche: "rallier la population", nom: "rallier la population" },
      { id: "portes",   cherche: "ouvrir les portes",    nom: "ouvrir les portes" },
      { id: "garant",   cherche: "garant des trois",     nom: "les trois piliers" },
    ];

    // Le pilier tel que l'ouverture du volume le dit, dans les mots de la maison.
    // Un volume qui ne sait pas le dire n'en reçoit pas : « un volume qui ne sait
    // dire ni l'un ni l'autre n'a rien à faire dans le coffret », et l'absence de
    // marque est alors l'information.
    function pilierDe(b) {
      let dit = "";
      (b.tables || []).forEach((t) => {
        (t.lignes || []).forEach((l) => {
          const c = l.cellules || [];
          if (c.length > 1 && sansAccent(c[0]).indexOf("pilier") >= 0 && !dit) dit = c[1];
        });
      });
      if (!dit) return null;
      // Le pilier est le PREMIER nommé dans la phrase, pas le premier de notre
      // liste : « Pilier : rallier la population, sans quoi on est attaqué dans
      // les rues » sert le ralliement. Un volume nomme volontiers les autres pour
      // dire ce qu'il n'est pas.
      const n = sansAccent(dit);
      let trouve = null, ou = Infinity;
      PILIERS.forEach((p) => {
        const i = n.indexOf(p.cherche);
        if (i >= 0 && i < ou) { ou = i; trouve = p; }
      });
      return trouve;
    }

    // L'état des actions du volume : sa table ⚔️ porte une colonne à vocabulaire
    // fermé — à faire · en cours · faite · bloquée. On compte, on ne juge pas.
    function actionsDe(b) {
      const n = { total: 0, faites: 0, cours: 0, bloquees: 0 };
      (b.tables || []).forEach((t) => {
        if (String(t.titre || "").indexOf("⚔") < 0) return;
        const cols = t.colonnes || [];
        let i = cols.findIndex((c) => {
          const s = sansAccent(c);
          return s.indexOf("etat") >= 0 || s.indexOf("en est") >= 0;
        });
        if (i < 0) i = cols.length - 1;
        (t.lignes || []).forEach((l) => {
          const c = l.cellules || [];
          if (!c.length) return;
          n.total++;
          const e = sansAccent(c[i] || "").replace(/\*/g, "");
          if (e.indexOf("bloqu") >= 0) n.bloquees++;
          else if (e.indexOf("en cours") >= 0) n.cours++;
          else if (e.indexOf("fait") >= 0) n.faites++;
        });
      });
      return n;
    }

    // ---- LA CELLULE DU POIDS --------------------------------------------------
    // CE QUE LE CAHIER PÈSE, et de combien ça a bougé depuis hier. Le
    // nombre seul dit une taille ; l'écart dit un MOUVEMENT, et c'est le
    // seul des deux qu'on ne puisse pas retrouver en ouvrant le volume —
    // le plan d'hier n'existe plus nulle part une fois `books.json` réécrit.
    function cellulePoids(b, tr) {
      const po = A.poidsDe(b);
      const pds = document.createElement("td");
      pds.className = "book-coffret-poids";
      if (po) {
        const v = document.createElement("span");
        v.className = "book-chiffre";
        v.textContent = String(Math.round(po.score));
        pds.appendChild(v);
        if (po.ecart != null && Math.round(po.ecart) !== 0) {
          const e = document.createElement("span");
          const monte = po.ecart > 0;
          e.className = "book-ecart " + (monte ? "book-ecart-haut" : "book-ecart-bas");
          e.textContent = (monte ? "+" : "−") + Math.abs(Math.round(po.ecart));
          // UN ÉCART QUI MONTE N'EST PAS UNE BONNE NOUVELLE, et la couleur ne
          // doit pas le laisser croire : la criticité monte quand on ÉCRIT du
          // plan — un cahier qu'on vient d'étoffer pèse plus lourd sans être
          // plus avancé. Elle descend quand on FAIT, ou quand on renonce.
          e.title = monte
            ? "Plus lourd qu'hier : on y a écrit, ou un empêchement s'est ajouté."
            : "Plus léger qu'hier : des pas ont été faits, ou une chaîne a été coupée.";
          pds.appendChild(e);
        }
        tr.title = (b.titre || "ce volume") + " — " + Math.round(po.score)
          + " de criticité, " + po.pas + " pas, " + po.goulots + " sans doublure";
      }
      return pds;
    }

    // ---- LA CELLULE DU MOT ----------------------------------------------------
    // Elle rend son <td> ET le <span> de genre à pendre au NOM, quand le genre
    // distingue encore quelque chose. Deux sorties parce que ce sont deux
    // colonnes, et que c'est ici qu'on sait si la seconde a lieu d'être.
    function celluleMot(b, tr) {
      const mot = document.createElement("td");
      mot.className = "book-coffret-mot";
      const pil = pilierDe(b), act = actionsDe(b);
      // Le genre du volume ne s'écrit que s'il distingue. Dans un coffret
      // d'affaires, trente-sept fois le mot « Plan » occupe la place sans rien
      // apprendre ; l'onglet le dira quand on aura ouvert.
      const gg = (pil || act.total || b.tables) ? null : genre(b);
      let signeGenre = null;
      if (gg) {
        signeGenre = document.createElement("span");
        signeGenre.className = "book-genre";
        signeGenre.textContent = gg.nom;
      }
      if (pil || act.total) {
        // Les marques. Le sous-titre passe au survol : il dit de quelle main le
        // volume est et quand il fut ouvert, ce qui est vrai de tous et ne
        // choisit rien.
        mot.classList.add("book-marques");
        if (b.sous_titre) tr.title = (b.sous_titre || "").trim();
        if (pil) {
          // Un pilier s'empoigne : cliquer ne fait qu'une chose, ne garder que
          // celui-là, et recliquer rend le coffret. C'est ce qui sépare une
          // marque d'une étiquette : une couleur qu'on ne peut pas empoigner ne
          // sert qu'à décorer.
          const p = document.createElement("button");
          p.type = "button";
          p.className = "book-marque book-pilier pilier-" + pil.id
            + (S.pilierTenu === pil.id ? " tenu" : "");
          p.textContent = pil.nom;
          p.title = S.pilierTenu === pil.id
            ? "Revoir tout le coffret" : "Ne garder que « " + pil.nom + " »";
          p.onclick = (ev) => {
            ev.stopPropagation();
            S.pilierTenu = S.pilierTenu === pil.id ? null : pil.id;
            A.dessiner();
          };
          mot.appendChild(p);
        }
        if (act.total) {
          // Ce qui est fait sur ce qui est écrit. Le dénominateur compte autant
          // que le numérateur : trois faites sur cinq n'est pas trois sur
          // vingt-quatre, et c'est ce rapport-là qui dit où l'on en est.
          const a = document.createElement("span");
          a.className = "book-marque book-avance"
            + (act.faites >= act.total ? " pleine" : act.faites ? "" : " nulle");
          a.textContent = act.faites + " / " + act.total;
          a.title = act.total + " actions écrites, " + act.faites + " faites, "
            + act.cours + " en cours.";
          mot.appendChild(a);
        }
        if (act.cours) {
          const c = document.createElement("span");
          c.className = "book-marque book-encours";
          c.textContent = act.cours + " en cours";
          mot.appendChild(c);
        }
        // La troisième marque n'existe que quand elle alarme.
        if (act.bloquees) {
          const bl = document.createElement("span");
          bl.className = "book-marque book-bloque";
          bl.textContent = act.bloquees > 1
            ? act.bloquees + " bloquées" : "bloquée";
          mot.appendChild(bl);
        }
      } else if (b.tables || b.lignes) {
        // Un volume ouvert où rien n'est encore écrit. On ne le laisse pas
        // ressembler aux autres : c'est précisément ce qu'on cherche quand on
        // ouvre le coffret pour savoir ce qui traîne.
        mot.classList.add("book-marques");
        const v = document.createElement("span");
        v.className = "book-marque book-vide";
        v.textContent = "rien d'écrit";
        mot.appendChild(v);
      } else {
        // Le sous-titre d'un volume dit de quelle main il est et quand il fut
        // ouvert : c'est long, et l'on ne vient ici que pour choisir.
        const d = (b.sous_titre || "").trim();
        mot.textContent = d.length > 96 ? d.slice(0, 95).replace(/[\s,;—-]+$/, "") + "…" : d;
      }
      return { td: mot, genre: signeGenre };
    }

    return { PILIERS, pilierDe, actionsDe, cellulePoids, celluleMot };
  }

  return { creer };
});
