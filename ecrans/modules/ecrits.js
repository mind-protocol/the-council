// ecrits.js — ce qui vient d'être PORTÉ AU REGISTRE, dit dans le fil, avec un
// lien qui y mène.
//
// POURQUOI. Tout ce qui se décide à la Table Peinte finit dans un livre : une
// charge au registre des offices, une action qui passe de « à faire » à
// « faite », un prix enfin chiffré. Mais le joueur ne le voit pas : il doit
// croire le MJ sur parole que ce qui s'est dit a été écrit. C'est la moitié
// manquante de la boucle — on lui rend ce qui a bougé, nommé, et cliquable.
//
// Ce n'est PAS une notification technique : c'est le mestre qui repose sa
// plume. On l'écrit donc quand le joueur est dans la salle où ça s'écrit, et
// jamais pour du routinier — sinon le fil devient un journal de bord.
//
//   {"type":"ecrit", "texte":"pendant que vous parliez",
//    "entrees":[
//      {"livre":"registre-des-offices",
//       "titre":"Commandement de l'ost — ser Steffon Darklyn",
//       "quoi":"charge neuve, ses limites et ses deux sceaux"},
//      {"livre":"affaire-transmission-des-ordres",
//       "titre":"La route du sel",
//       "quoi":"le nom du patron, et l'heure changée à minuit"}]}
"use strict";
(() => {
  Bus.enregistrer("ecrit", (it) => {
    const entrees = (it.entrees || []).filter((e) => e && e.titre);
    if (!entrees.length) return;

    const entree = Bus.chronique("chr-ecrit", null,
      it.texte || "Porté au registre");
    if (!entree) return;
    const corps = entree.querySelector(".chr-corps") || entree;

    const liste = document.createElement("div");
    liste.className = "ecrits";

    entrees.forEach((e) => {
      const l = document.createElement("button");
      l.type = "button";
      l.className = "ecrit";
      l.innerHTML = '<span class="ecrit-titre"></span>' +
        (e.quoi ? '<span class="ecrit-quoi"></span>' : "");
      l.querySelector(".ecrit-titre").textContent = e.titre;
      if (e.quoi) l.querySelector(".ecrit-quoi").textContent = e.quoi;

      // Sans livre nommé, la ligne reste lisible mais ne mène nulle part : on
      // ne feint pas un lien mort.
      if (!e.livre) {
        l.disabled = true;
        l.classList.add("ecrit-sans-lien");
      } else {
        l.title = "Ouvrir dans les livres";
        l.onclick = () => {
          if (!(window.Books && Books.ouvrir && Books.ouvrir(e.livre))) {
            l.classList.add("ecrit-introuvable");
            l.title = "Ce volume n'est pas à portée d'ici";
          }
        };
      }
      liste.appendChild(l);
    });

    corps.appendChild(liste);
  });
})();
