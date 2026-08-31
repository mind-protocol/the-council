// reperes.js — deux flèches à la droite du fil, pour sauter de sa propre parole
// à la suivante. Relire une longue chronique, c'est chercher où l'on avait pris
// la parole : ces jalons-là sont les seuls que le joueur ait posés lui-même.
(function () {
  const CIBLE = ".chr-vous";

  function corps() { return document.getElementById("fil-corps"); }

  function jalons() {
    const z = corps();
    return z ? Array.from(z.querySelectorAll(CIBLE)) : [];
  }

  // Le jalon « courant » est le dernier dont le haut est passé au-dessus de la
  // ligne de lecture — un peu sous le bord haut, pour que sauter au suivant ne
  // ramène pas à celui qu'on est déjà en train de lire.
  function sauter(sens) {
    const z = corps();
    const l = jalons();
    if (!z || !l.length) return;
    const ligne = z.scrollTop + 12;
    let cible = null;
    if (sens > 0) {
      cible = l.find((d) => d.offsetTop > ligne + 4);
      if (!cible) cible = l[l.length - 1];
    } else {
      for (const d of l) { if (d.offsetTop < ligne - 4) cible = d; }
      if (!cible) cible = l[0];
    }
    z.scrollTo({top: Math.max(0, cible.offsetTop - 10), behavior: "smooth"});
    cible.classList.remove("chr-vise");
    void cible.offsetWidth;
    cible.classList.add("chr-vise");
  }

  function rafraichir(boite) {
    boite.classList.toggle("vide", jalons().length < 1);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const fil = document.getElementById("fil");
    const z = corps();
    if (!fil || !z) return;

    const boite = document.createElement("div");
    boite.id = "fil-reperes";
    boite.innerHTML =
      '<button type="button" data-sens="-1" title="Votre parole précédente">↑</button>' +
      '<button type="button" data-sens="1" title="Votre parole suivante">↓</button>';
    boite.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (b) sauter(Number(b.dataset.sens));
    });
    fil.appendChild(boite);

    rafraichir(boite);
    new MutationObserver(() => rafraichir(boite))
      .observe(z, {childList: true, subtree: true});
  });
})();
