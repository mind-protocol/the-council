// annales.js — les événements marquants : ce que l'Histoire retiendra.
// Une ligne rouge et or dans la chronique, et la liste dans le rail latéral.
// Le MJ les pousse avec parcimonie : un fait qui change le cours, pas un beat.
"use strict";
(() => {
  const annales = [];

  const texteDate = (d) =>
    d ? d.annee + " AC, " + d.lune + "e lune, " + d.jour + "e jour" : "";

  function rendreListe() {
    const zone = document.getElementById("liste-annales");
    if (!zone) return;
    zone.innerHTML = annales.length
      ? ""
      : '<p class="objectif-vide">Rien encore — l\'Histoire attend.</p>';
    annales.slice().reverse().forEach((a) => {
      const d = document.createElement("div");
      d.className = "annale";
      d.innerHTML = '<span class="annale-quand">' + texteDate(a.date) + "</span>" +
        '<span class="annale-quoi">' + a.titre + "</span>";
      if (window.Entites) Entites.traiter(d);
      zone.appendChild(d);
    });
  }

  window.addEventListener("DOMContentLoaded", rendreListe);

  Bus.enregistrer("marque", (it) => {
    // Une marque rechargée du passé est plus ANCIENNE que tout ce qu'on tient :
    // elle prend la tête de la liste, sinon le rail la donnerait pour récente.
    const a = { date: it.date, titre: it.titre || it.texte };
    if (Bus.enArchive()) annales.unshift(a); else annales.push(a);
    rendreListe();
    const d = Bus.chronique("chr-marque", null, it.texte, { avatar: "⚜" });
    if (!d) return;
    const coiffe = document.createElement("span");
    coiffe.className = "marque-coiffe";
    coiffe.textContent = "Il s'est passé " + (it.date ? "— " + texteDate(it.date) : "");
    const corps = d.querySelector(".chr-corps");
    if (corps) corps.insertBefore(coiffe, corps.firstChild);
  });
})();
