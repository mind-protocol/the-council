// coffret.js — LA BOÎTE OUVERTE : ce qu'elle contient, ligne à ligne.
//
// On n'ouvre pas un coffret pour se mettre à lire un volume au hasard : on
// regarde ce qu'il y a dedans et l'on prend celui qu'on veut. Cette pièce rend
// cette liste — et les MARQUES qui la rendent choisissable, ce qu'on lit d'un
// volume SANS l'ouvrir : le pilier qu'il sert, où en sont ses actions, ce qu'il
// pèse au plan et de combien ça a bougé depuis hier.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksCoffret = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { teinte, compte } = A.lecture;
    const { MEMOIRE_IDEES, MEMOIRE_POIDS } = A.memoire;

    // La carte d'un coffret : ce qu'il y a dedans, ligne à ligne. C'est ce qu'on
    // voit quand on l'ouvre — on ne se met pas à lire un volume au hasard, on
    // regarde ce que la boîte contient et l'on prend celui qu'on veut. Chaque
    // ligne s'ouvre d'un clic.
    function carteBoite(e) {
      const c = e.boite;
      const art = document.createElement("article");
      art.className = "book book-coffret-carte";
      art.style.setProperty("--book-teinte", teinte(c));

      const ligneTitre = document.createElement("div");
      ligneTitre.className = "book-tete";
      const t = document.createElement("h3");
      if (c.embleme) {
        const em = document.createElement("span");
        em.className = "book-embleme";
        em.textContent = c.embleme;
        t.appendChild(em);
      }
      t.appendChild(document.createTextNode(c.titre || "Sans titre"));
      const g = document.createElement("span");
      g.className = "book-genre";
      g.textContent = "Coffret";
      t.appendChild(g);
      ligneTitre.appendChild(t);
      art.appendChild(ligneTitre);

      // Un pilier tenu : le coffret ne montre plus que lui. Les mains restent —
      // on veut voir QUI porte cette part du plan, c'est même toute la raison de
      // serrer. Un pilier qui ne garde rien se relâche de lui-même, plutôt que de
      // laisser une carte vide sans dire pourquoi.
      let livres = e.livres;
      let tenu = null;
      if (S.pilierTenu) {
        const gardes = livres.filter((b) => (A.pilierDe(b) || {}).id === S.pilierTenu);
        if (gardes.length) {
          livres = gardes;
          tenu = A.PILIERS.find((p) => p.id === S.pilierTenu);
        } else S.pilierTenu = null;
      }

      const s = document.createElement("div");
      s.className = "book-sous-titre";
      s.textContent = (c.sous_titre ? c.sous_titre + " " : "")
        + "— " + A.provenance(c) + ", " + livres.length
        + (livres.length > 1 ? " volumes" : " volume")
        + (tenu ? " sur " + e.livres.length + ", pour " + tenu.nom + "." : ".");
      if (tenu) {
        const revoir = document.createElement("button");
        revoir.type = "button";
        revoir.className = "book-revoir";
        revoir.textContent = "Tout revoir";
        revoir.onclick = () => { S.pilierTenu = null; A.dessiner(); };
        s.appendChild(revoir);
      }
      art.appendChild(s);

      // L'INTERRUPTEUR DES IDÉES, et seulement là où il a un sens : le coffret
      // des affaires. Éteint par défaut — on vient d'abord chercher un cahier —,
      // et son état se retient d'une session à l'autre comme le reste du décor.
      if (c.id === "boite-sujets") {
        if (S.idees) A.chargerIdees();
        const outils = document.createElement("div");
        outils.className = "book-coffret-outils";
        const bt = document.createElement("button");
        bt.type = "button";
        bt.className = "book-idees-bouton" + (S.idees ? " allume" : "");
        bt.setAttribute("aria-pressed", S.idees ? "true" : "false");
        const l = document.createElement("span");
        l.className = "book-idees-lampe";
        l.textContent = "\u{1F4A1}";
        bt.appendChild(l);
        bt.appendChild(document.createTextNode("idée"));
        bt.title = S.idees
          ? "Masquer l'idée principale de chaque affaire"
          : "Montrer, sous chaque affaire, ce qu'il y aurait à faire";
        bt.onclick = () => {
          S.idees = !S.idees;
          try { localStorage.setItem(MEMOIRE_IDEES, S.idees ? "1" : "0"); } catch (e) {}
          if (S.idees) A.chargerIdees();
          A.dessiner();
        };
        outils.appendChild(bt);

        // RANGER PAR CE QUE ÇA PÈSE — et l'ordre par main reste le défaut, parce
        // que c'est ainsi qu'on cherche un cahier : on sait de qui il est. Le
        // classement répond à l'autre question, celle qu'aucun rangement ne peut
        // poser en même temps : lequel de ces trente-sept porte le plus ? Il
        // casse donc les groupes, et c'est voulu — un classement qui reste
        // groupé par homme n'est pas un classement, c'est trente-sept petits.
        const bc = document.createElement("button");
        bc.type = "button";
        bc.className = "book-idees-bouton" + (S.parPoids ? " allume" : "");
        bc.setAttribute("aria-pressed", S.parPoids ? "true" : "false");
        bc.textContent = "⚖ par poids";
        bc.title = S.parPoids
          ? "Revenir au rangement par main"
          : "Ranger les affaires par ce qu'elles pèsent au plan, toutes mains mêlées";
        bc.onclick = () => {
          S.parPoids = !S.parPoids;
          try { localStorage.setItem(MEMOIRE_POIDS, S.parPoids ? "1" : "0"); } catch (e) {}
          A.dessiner();
        };
        outils.appendChild(bc);
        art.appendChild(outils);
      }

      const env = document.createElement("div");
      env.className = "book-table-enveloppe";
      const tab = document.createElement("table");
      tab.className = "book-table book-coffret-table";
      const tbody = document.createElement("tbody");

      // PAR MAIN, quand les volumes le disent. Trente-sept affaires en file sont
      // illisibles : celui qui ouvre le coffret cherche les SIENNES, ou celles
      // d'un homme dont il vient de parler. `tenu_par` ne déplace rien — le
      // cahier reste sur la table —, il dit sur quelle épaule le volume tombe.
      // Les mains gardent l'ordre où elles paraissent (donc la fraîcheur du tri
      // au-dessus, et non l'alphabet, qui range Aldon devant ce qu'on a touché
      // ce matin) ; « sur personne » ferme la marche, et c'est une information :
      // une affaire ouverte que personne ne porte n'a pas été confiée.
      const mains = [];
      livres.forEach((b) => {
        const qui = b.tenu_par || "";
        let g = mains.find((m) => m.id === qui);
        if (!g) mains.push((g = { id: qui, livres: [] }));
        g.livres.push(b);
      });
      const groupe = mains.some((m) => m.id);
      if (groupe) mains.sort((a, b) => (a.id ? 0 : 1) - (b.id ? 0 : 1));

      // La barre d'une main : le MÉDAILLON de « Les gens », pas un nom écrit.
      // On reconnaît une cour à ses têtes ; celui qui cherche les affaires du
      // Sanglier doit le trouver au visage, comme partout ailleurs dans le
      // décor. Le clic ouvre une pensée sur lui, comme partout ailleurs aussi.
      const barre = (m) => {
        const tr = document.createElement("tr");
        tr.className = "book-coffret-main" + (m.id ? "" : " book-coffret-main-vide");
        const td = document.createElement("td");
        td.colSpan = 4;
        td.className = "book-coffret-main-nom";
        // Le contenu vit dans un bloc À L'INTÉRIEUR de la cellule : une cellule
        // de tableau qu'on passe en `flex` cesse de participer au calcul des
        // colonnes, et la barre se met à dicter la largeur de toute la liste.
        const dedans = document.createElement("div");
        dedans.className = "book-coffret-main-bloc";
        td.appendChild(dedans);
        const face = (m.id && window.Gens && Gens.medaillon)
          ? Gens.medaillon(m.id) : null;
        if (face) {
          // Un visage de 132 pixels est une galerie ; ici c'est une barre de
          // liste, et le médaillon s'y couche : la face petite, le nom et le
          // rôle à sa droite. Le dessin ne change pas, seule sa taille change.
          face.classList.add("book-coffret-main-gars");
          dedans.appendChild(face);
        } else {
          dedans.appendChild(
            document.createTextNode(m.id ? A.nomActeur(m.id) : "Sur personne"));
        }
        const n = document.createElement("span");
        n.className = "book-coffret-main-compte";
        n.textContent = compte(m.livres.length);
        dedans.appendChild(n);
        tr.appendChild(td);
        tbody.appendChild(tr);
      };

      const classe = S.parPoids && c.id === "boite-sujets" && S.crit && S.crit.affaires;
      if (classe) {
        livres.slice().sort((x, y) => ((A.poidsDe(y) || {}).score || 0)
          - ((A.poidsDe(x) || {}).score || 0)).forEach((b) => ligneVolume(b, tbody));
      } else {
        (groupe ? mains : [{ id: "", livres: livres }]).forEach((m) => {
          if (groupe) barre(m);
          m.livres.forEach((b) => ligneVolume(b, tbody));
        });
      }
      tab.appendChild(tbody);
      env.appendChild(tab);
      art.appendChild(env);
      return art;
    }

    // Une ligne de la carte d'un coffret : le signe, le nom, et le mot qui dit
    // d'où le volume sort. Elle s'ouvre d'un clic.
    function ligneVolume(b, tbody) {
        const tr = document.createElement("tr");
        tr.className = "book-coffret-ligne";
        tr.tabIndex = 0;
        tr.title = "Ouvrir — " + (b.titre || "ce volume");
        const ouvrir = () => { S.ouvert = b.id; A.dessiner(); };
        tr.onclick = ouvrir;
        tr.onkeydown = (ev) => {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); ouvrir(); }
        };
        const signe = document.createElement("td");
        signe.className = "book-coffret-signe";
        signe.textContent = b.embleme || "";
        const nom = document.createElement("td");
        nom.className = "book-coffret-nom";
        nom.appendChild(document.createTextNode(b.titre || "Sans titre"));
        // L'OFFICE sous lequel le volume est tenu. La barre au-dessus dit déjà
        // QUI ; elle ne dit pas de quel chapeau — et trois hommes de cette table
        // en portent plusieurs. C'est aussi le sceau qu'on regarderait si
        // l'affaire tournait mal, donc ça se lit sans ouvrir.
        if (b.office) {
          const o = document.createElement("span");
          o.className = "book-coffret-office";
          o.textContent = b.office;
          nom.appendChild(o);
        }
        // LES MARQUES SONT À CÔTÉ (`marques.js`) : ce qui se lit d'un volume
        // sans l'ouvrir ne regarde pas la ligne qui l'affiche. Les deux
        // cellules écrivent `tr.title` — le poids d'abord, comme à l'origine.
        const pds = A.cellulePoids(b, tr);
        const m = A.celluleMot(b, tr);
        if (m.genre) nom.appendChild(m.genre);
        tr.appendChild(signe);
        tr.appendChild(nom);
        tr.appendChild(pds);
        tr.appendChild(m.td);
        tbody.appendChild(tr);

        // ET SOUS L'AFFAIRE, EN RETRAIT, SON IDÉE. Une ligne, jamais deux : ce
        // coffret en aligne trente-huit, et trois idées chacune seraient
        // exactement le mur que cette maison appelle le tunnel. Une affaire sans
        // mission n'affiche rien du tout — pas de ligne vide, pas de « rien à
        // signaler ».
        if (S.idees) {
          const q = S.parLivre[b.id];
          if (q) {
            const tri = document.createElement("tr");
            tri.className = "book-coffret-idee";
            const tdi = document.createElement("td");
            tdi.colSpan = 3;
            tdi.appendChild(A.traitIdee(q.m));
            tri.appendChild(tdi);
            tbody.appendChild(tri);
          }
        }
  }

    return { carteBoite, ligneVolume };
  }

  return { creer };
});
