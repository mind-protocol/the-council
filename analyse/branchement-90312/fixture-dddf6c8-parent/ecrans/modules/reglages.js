// reglages.js — les curseurs du narrateur : Expliquer (sobre↔didactique) et
// Guider (libre↔guidée). Réels : (1) envoyés au MJ ({type:"reglage"}) qui adapte
// sa prose selon la doctrine de CLAUDE.md ; (2) un guidage bas masque les
// réactions suggérées côté client. Persistés en localStorage.
"use strict";
(() => {
  const DEFAUTS = { explication: 50, guidage: 50 };
  let valeurs = DEFAUTS;
  try { valeurs = Object.assign({}, DEFAUTS, JSON.parse(localStorage.getItem("lc-reglages") || "{}")); }
  catch (_) {}
  let minuterie = null;

  function appliquer() {
    document.body.classList.toggle("sans-gestes", valeurs.guidage < 30);
  }

  function notifier() {
    if (minuterie) clearTimeout(minuterie);
    minuterie = setTimeout(() => {
      Bus.envoyer({ type: "reglage", explication: valeurs.explication, guidage: valeurs.guidage });
    }, 800);
  }

  window.addEventListener("DOMContentLoaded", () => {
    const zone = document.getElementById("zone-reglages-corps");
    if (!zone) return;
    zone.innerHTML =
      '<div class="reglage"><div class="reglage-nom">Expliquer</div>' +
      '<input type="range" id="regl-explication" min="0" max="100" step="10" value="' + valeurs.explication + '">' +
      '<div class="reglage-bornes"><span>sobre</span><span>didactique</span></div></div>' +
      '<div class="reglage"><div class="reglage-nom">Guider</div>' +
      '<input type="range" id="regl-guidage" min="0" max="100" step="10" value="' + valeurs.guidage + '">' +
      '<div class="reglage-bornes"><span>libre</span><span>guidée</span></div></div>';
    ["explication", "guidage"].forEach((cle) => {
      document.getElementById("regl-" + cle).oninput = (e) => {
        valeurs[cle] = +e.target.value;
        localStorage.setItem("lc-reglages", JSON.stringify(valeurs));
        appliquer();
        notifier();
      };
    });
    appliquer();
  });
})();
