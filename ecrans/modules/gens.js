// gens.js — la quatrième échelle du décor : « Les gens ».
// Une carte porte des lieux, celle-ci porte des visages. Le joueur y retrouve
// qui est qui — le nom, le rôle, la maison — rangé par camp affiché.
// Ce n'est PAS une fiche de renseignement : ni position, ni intentions, ni
// allégeance réelle. Ce que la cour sait de la cour, rien de plus.
// Un clic sur quelqu'un = un moment de pensée, même canal que les entités.
"use strict";
window.Gens = (() => {
  let gens = null;
  let charge = false;
  let filtre = "";
  // le registre sert deux choses : la vue « Les gens », et le fil, qui a besoin
  // du nom et du rôle de qui parle même quand il n'est pas dans la salle.
  const parId = new Map();
  const attendent = [];
  // le registre arrive après les premiers items du flux : qui a besoin des
  // visages (la galerie) se fait rappeler plutôt que de sonder en boucle
  const aPrevenir = [];

  const CAMPS = [
    { id: "noir", nom: "Les Noirs" },
    { id: "vert", nom: "Les Verts" },
    { id: "neutre", nom: "Ni l'un ni l'autre" },
  ];

  function hote() { return document.getElementById("gens"); }

  function charger() {
    if (charge) return;
    charge = true;
    fetch("/gens").then((r) => r.json()).then((d) => {
      gens = d.gens || [];
      parId.clear();
      gens.forEach((p) => parId.set(p.id, p));
      dessiner();
      // ce qui a été rendu avant que le registre n'arrive se répare ici
      while (attendent.length) reparer(attendent.pop());
      while (aPrevenir.length) { try { aPrevenir.pop()(); } catch (e) {} }
    }).catch(() => { charge = false; });
  }

  // Ce que le fil doit savoir de quelqu'un : son nom, son rôle, son visage.
  // La salle courante prime (le MJ peut y écrire un titre de circonstance),
  // le registre comble, et un inconnu garde au moins un nom lisible.
  function qui(id) {
    const p = (window.Presents || {})[id] || {};
    const f = parId.get(id) || {};
    return {
      nom: p.nom || f.nom || String(id || "").replace(/-/g, " ")
        .replace(/(^|\s)\p{Ll}/gu, (c) => c.toUpperCase()),
      titre: p.titre || f.titre || "",
      portrait_svg: p.portrait_svg || f.portrait_svg || "",
    };
  }

  // Une entrée du fil rendue avant le chargement : on lui pose son rôle après
  // coup plutôt que de la laisser orpheline.
  function reparer(entree) {
    if (!entree || !entree.isConnected) return;
    const f = parId.get(entree.dataset.qui);
    const nom = entree.querySelector(".chr-qui");
    if (!f || !nom || nom.querySelector(".chr-role")) return;
    if (nom.firstChild && nom.firstChild.nodeType === 3) nom.firstChild.nodeValue = f.nom;
    if (!f.titre) return;
    const s = document.createElement("span");
    s.className = "chr-role";
    s.innerHTML = '<i class="emb">' + Bus.embleme(f.titre) + "</i>";
    s.appendChild(document.createTextNode(f.titre));
    nom.appendChild(s);
  }

  // Le fil marque qui il a rendu ; tant que le registre n'est pas là, il note.
  function marquer(entree, id) {
    if (!entree) return entree;
    entree.dataset.qui = id;
    if (!parId.size) attendent.push(entree);
    return entree;
  }

  function medaillon(p) {
    const d = document.createElement("div");
    d.className = "gens-gars" + (p.joueur ? " gens-joueur" : "");
    d.title = p.titre || p.nom;
    d.innerHTML =
      '<div class="gens-face">' + (p.portrait_svg || "") + "</div>" +
      '<div class="gens-dit"><b>' + p.nom + "</b>" +
      (p.titre ? "<small>" + p.titre + "</small>" : "") + "</div>";
    d.onclick = () => Entites.penser(p.id, "personnage", p.nom);
    return d;
  }

  function dessiner() {
    const h = hote();
    if (!h) return;
    if (!gens) { h.innerHTML = '<p class="gens-vide">…</p>'; return; }
    h.innerHTML = "";

    const barre = document.createElement("div");
    barre.className = "gens-barre";
    const ch = document.createElement("input");
    ch.type = "search";
    ch.placeholder = "Chercher un nom, un rôle…";
    ch.value = filtre;
    ch.oninput = () => { filtre = ch.value; lister(corps); };
    barre.appendChild(ch);
    h.appendChild(barre);

    const corps = document.createElement("div");
    corps.className = "gens-corps";
    h.appendChild(corps);
    lister(corps);
  }

  function lister(corps) {
    const q = filtre.trim().toLowerCase();
    const garde = (p) => !q ||
      (p.nom + " " + p.titre + " " + p.maison).toLowerCase().includes(q);
    corps.innerHTML = "";
    let vus = 0;
    CAMPS.forEach((c) => {
      const dedans = gens.filter((p) => p.camp === c.id && garde(p));
      if (!dedans.length) return;
      vus += dedans.length;
      const sec = document.createElement("div");
      sec.className = "gens-camp camp-" + c.id;
      sec.innerHTML = '<div class="gens-camp-titre">' + c.nom + "</div>";
      // par maison, à l'intérieur du camp : on lit une cour, pas une liste
      const parMaison = new Map();
      dedans.forEach((p) => {
        if (!parMaison.has(p.maison)) parMaison.set(p.maison, []);
        parMaison.get(p.maison).push(p);
      });
      parMaison.forEach((liste, maison) => {
        const bloc = document.createElement("div");
        bloc.className = "gens-maison";
        bloc.innerHTML = '<div class="gens-maison-titre">' + maison + "</div>";
        const rang = document.createElement("div");
        rang.className = "gens-rang";
        liste.forEach((p) => rang.appendChild(medaillon(p)));
        bloc.appendChild(rang);
        sec.appendChild(bloc);
      });
      corps.appendChild(sec);
    });
    if (!vus) corps.innerHTML = '<p class="gens-vide">Personne de ce nom.</p>';
  }

  // relire quand l'état a bougé (un mort, un nouveau venu, un titre changé)
  function relire() { charge = false; gens = gens || null; charger(); }

  // Le registre est chargé d'emblée, pas à l'ouverture de la vue : le fil s'en
  // sert dès la première réplique pour nommer et titrer qui parle.
  charger();

  window.addEventListener("DOMContentLoaded", () => {
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "gens", nom: "Les gens", hote: "gens", ordre: 4,
        dispo: () => true,
        reparu: charger,
      });
    }
    setInterval(() => { if (gens) { charge = false; charger(); } }, 120000);
  });

  // « préviens-moi quand tu sauras » — appelé tout de suite si c'est déjà le cas
  function quand(cb) {
    if (parId.size) { try { cb(); } catch (e) {} } else aPrevenir.push(cb);
  }

  return { relire, charger, qui, marquer, quand };
})();
