// attention.js — chaque PHRASE porte ses boutons de geste, inline, révélés au survol.
// Un clic envoie {type:"reaction", locuteur_id, phrase, texte} sans interrompre le flux,
// puis le geste choisi reste inscrit au bout de la phrase.
"use strict";
window.Attention = (() => {
  // Les réactions sont CUSTOM : écrites à la main par le MJ pour une réplique
  // donnée (item.reactions). Aucun set générique. Pas de réactions = pas de boutons.
  function boutons(extras) {
    return (extras || []).map((g) =>
      '<button class="geste-btn" data-g="' + (g.id || g.texte) + '">' +
      g.texte + "</button>").join("");
  }

  function html(texte, meta) {
    const loc = (meta && meta.locuteur_id) || "";
    const btns = boutons(meta && meta.extras);
    const wrap = (ph, fin) =>
      '<span class="phrase-wrap"><span class="phrase" data-loc="' + loc + '">' + ph +
      "</span>" + (fin && btns ? '<span class="gestes">' + btns + "</span>" : "") + "</span>";
    if (texte.indexOf("<") !== -1) return wrap(texte, true);
    const phs = texte.split(/(?<=[.!?…»])\s+/);
    return phs.map((ph, i) => wrap(ph, i === phs.length - 1)).join(" ");
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest(".geste-btn");
    if (!b) return;
    const w = b.closest(".phrase-wrap");
    const ph = w.querySelector(".phrase");
    if (ph.classList.contains("reagie")) return;
    Bus.envoyer({ type: "reaction", locuteur_id: ph.dataset.loc || null,
      phrase: (ph.textContent || "").slice(0, 120), texte: b.dataset.g });
    ph.classList.add("reagie");
    const fait = document.createElement("span");
    fait.className = "geste-fait";
    fait.textContent = " — " + b.textContent;
    w.querySelector(".gestes").replaceWith(fait);
  });

  return { html };
})();
