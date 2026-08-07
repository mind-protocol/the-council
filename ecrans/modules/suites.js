// suites.js — « ce qui s'offre ensuite », au bas d'un « Laisser faire ».
//
// Quand le MJ rend la bride, il ne rend pas une page blanche : il pose deux à
// cinq suites possibles, telles que le personnage les voit. Le joueur en coche
// ce qu'il retient, écarte le reste, et la scène repart.
//
// Ce n'est PAS le menu de choix qu'on s'interdit partout ailleurs : le champ
// libre reste ouvert, cocher n'est jamais obligatoire, et le bloc se referme
// aussi bien sur « Rien de tout cela ». C'est une main tendue à la fin d'un
// passage où le joueur n'avait plus la parole, pas un rail.
//
// Les exclusives : une option portant un `groupe` en chasse les autres du même
// groupe — on ne part pas à la fois pour Accalmie et pour Port-Réal. Sans
// `groupe`, on coche autant qu'on veut.
"use strict";
(() => {
  // Ce qui a déjà été répondu : le flux est append-only et se rejoue en entier
  // au rechargement. Sans cette mémoire, un bloc tranché il y a trois heures
  // se rouvrirait tout neuf à chaque reprise.
  const CLE = "suites-repondues";
  function repondues() {
    try { return JSON.parse(localStorage.getItem(CLE) || "{}"); } catch (e) { return {}; }
  }
  function marquer(id, resume) {
    if (!id) return;
    const m = repondues();
    m[id] = resume || true;
    try { localStorage.setItem(CLE, JSON.stringify(m)); } catch (e) {}
  }

  Bus.enregistrer("suites", (it, ctx) => {
    const options = (it.options || []).filter((o) => o && o.texte);
    if (!options.length) return;
    const entree = Bus.chronique("chr-suites", null,
      it.texte || "Ce qui s'offre, maintenant");
    if (!entree) return;
    const corps = entree.querySelector(".chr-corps");

    const bloc = document.createElement("div");
    bloc.className = "suites";
    const liste = document.createElement("div");
    liste.className = "suites-liste";
    bloc.appendChild(liste);

    // Ce que le joueur retient, par id.
    const cochees = new Set();

    options.forEach((o, i) => {
      const id = o.id || "o" + i;
      const l = document.createElement("button");
      l.type = "button";
      l.className = "suite" + (o.groupe ? " suite-exclusive" : "");
      if (o.groupe) l.dataset.groupe = o.groupe;
      l.dataset.id = id;
      l.innerHTML = '<span class="suite-coche"></span>' +
        '<span class="suite-corps"><span class="suite-texte"></span>' +
        (o.detail ? '<span class="suite-detail"></span>' : "") + "</span>";
      l.querySelector(".suite-texte").textContent = o.texte;
      if (o.detail) l.querySelector(".suite-detail").textContent = o.detail;
      l.onclick = () => {
        if (bloc.classList.contains("clos")) return;
        const deja = cochees.has(id);
        // Une exclusive chasse ses sœurs : on ne part pas deux fois.
        if (o.groupe && !deja) {
          liste.querySelectorAll('.suite[data-groupe="' + CSS.escape(o.groupe) + '"]')
            .forEach((f) => {
              f.classList.remove("prise");
              cochees.delete(f.dataset.id);
            });
        }
        l.classList.toggle("prise", !deja);
        if (deja) cochees.delete(id); else cochees.add(id);
        maj();
      };
      liste.appendChild(l);
    });

    const pied = document.createElement("div");
    pied.className = "suites-pied";
    const oui = document.createElement("button");
    oui.className = "suites-tenir";
    const non = document.createElement("button");
    non.className = "suites-ecarter";
    non.textContent = "Rien de tout cela";
    pied.appendChild(oui);
    pied.appendChild(non);
    bloc.appendChild(pied);

    function maj() {
      oui.disabled = !cochees.size;
      oui.textContent = cochees.size > 1
        ? "Tenir ces " + cochees.size + " voies" : "Tenir cette voie";
    }
    maj();

    // Une fois tranché, le bloc se fige et dit ce qui a été retenu : le fil est
    // une chronique, pas un formulaire — on doit pouvoir relire son choix.
    function clore(resume) {
      bloc.classList.add("clos");
      liste.querySelectorAll(".suite").forEach((f) => {
        f.disabled = true;
        if (!f.classList.contains("prise")) f.classList.add("laissee");
      });
      pied.innerHTML = '<span class="suites-verdict"></span>';
      pied.querySelector(".suites-verdict").textContent = resume;
      marquer(it.id, resume);
    }

    oui.onclick = () => {
      const prises = options.filter((o, i) => cochees.has(o.id || "o" + i));
      if (!prises.length) return;
      ctx.poster({
        type: "suites", suites_id: it.id || null,
        retenues: prises.map((o, i) => ({ id: o.id || null, texte: o.texte })),
        ecartees: options.filter((o) => prises.indexOf(o) === -1)
          .map((o) => ({ id: o.id || null, texte: o.texte })),
        texte: prises.map((o) => o.texte).join(" · "),
      });
      clore("Retenu : " + prises.map((o) => o.texte).join(" · "));
      setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
    };
    non.onclick = () => {
      ctx.poster({
        type: "suites", suites_id: it.id || null, retenues: [], ecarte: true,
        ecartees: options.map((o) => ({ id: o.id || null, texte: o.texte })),
        texte: "aucune de ces suites",
      });
      clore("Écarté — vous chercherez ailleurs.");
      setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
    };

    corps.appendChild(bloc);

    // Rejeu d'un bloc déjà tranché : on le rend clos, avec son verdict.
    const dejaVu = it.id && repondues()[it.id];
    if (dejaVu) clore(typeof dejaVu === "string" ? dejaVu : "Déjà tranché.");
  });
})();
