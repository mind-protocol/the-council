// vue-salle.js — la toile de la salle, posée dans le fil au changement de salle.
//
// Le plan du château dit la TOPOLOGIE : où sont les pièces, laquelle est en
// braise. Il ne dit pas à quoi elles ressemblent. Cette toile-là comble ce
// trou, et rien d'autre — elle n'est pas un décor de fond, elle ne remplace
// pas le plan, et elle ne se met pas derrière le texte.
//
// AUTOMATIQUE, ET C'EST LA RÈGLE : le MJ n'écrit rien pour l'obtenir. La salle
// courante est déjà devinée de l'en-tête de lieu par `plan.js` (`Plan.salle()`),
// et l'existence d'une toile se lit du manifeste `/salles`. Déposer un fichier
// dans `ecrans/salles/<id de la salle>.jpg` suffit à ce qu'elle paraisse ; le
// retirer suffit à ce qu'elle cesse. Aucune table d'état à tenir.
//
// UNE FOIS PAR ARRIVÉE, pas une fois par item. On garde la dernière salle
// montrée : vingt répliques dans la Table Peinte ne posent qu'une toile. Un
// `effacer` (changement de scène) rouvre le droit — on revient dans une salle
// quittée, on la revoit.
"use strict";
(() => {
  let avec = null;          // les ids de salle qui ont une toile ; null tant qu'on ne sait pas
  let derniere = null;      // la dernière salle montrée

  // Une toile héritée peut rester au dépôt tandis que la salle adopte une
  // variante présente. L'Archive conserve ainsi sa pierre de Peyredragon et
  // montre les aménagements réversibles de Braavos sans écraser la pièce.
  const VARIANTES = { archives: "archives-braavos.png" };

  function cheminDe(id) {
    return "/salles/" + (VARIANTES[id] || (id + ".jpg"));
  }

  fetch("/salles")
    .then((r) => r.json())
    .then((d) => { avec = new Set(d.salles || []); })
    .catch(() => { avec = new Set(); });

  // Le nom de la salle, tel que le plan l'écrit — on ne le réinvente pas ici.
  function nomDe(id) {
    const plan = window.Plans && window.Plans[window.Plan && Plan.chateau()];
    const s = plan && (plan.salles || []).find((x) => x.id === id);
    return s ? s.nom : null;
  }
  function quoiDe(id) {
    const plan = window.Plans && window.Plans[window.Plan && Plan.chateau()];
    const s = plan && (plan.salles || []).find((x) => x.id === id);
    return (s && s.quoi) || "";
  }

  function poser() {
    if (!avec || !avec.size || !window.Plan) return;
    // `relire` recalcule depuis le bandeau, que le bus vient de reposer pour
    // cet item — sinon on suivrait la salle de l'item précédent.
    try { Plan.relire(); } catch (e) { return; }
    const id = Plan.salle();
    if (!id || id === derniere || !avec.has(id)) return;
    derniere = id;

    const nom = nomDe(id) || "";
    const entree = Bus.chronique("chr-salle-vue", null, quoiDe(id));
    if (!entree) return;
    const corps = entree.querySelector(".chr-corps");
    if (!corps) return;
    const fig = document.createElement("figure");
    fig.className = "salle-vue";
    const img = document.createElement("img");
    img.src = cheminDe(id);
    img.alt = nom;
    img.loading = "lazy";
    // Le manifeste peut avoir une longueur d'avance sur le disque (fichier
    // retiré à la main entre deux chargements) : si l'image manque, on efface
    // l'entrée entière plutôt que de laisser un cadre vide dans la chronique.
    img.addEventListener("error", () => { entree.remove(); derniere = null; });
    fig.appendChild(img);
    if (nom) {
      const lg = document.createElement("figcaption");
      lg.textContent = nom;
      fig.appendChild(lg);
    }
    corps.insertBefore(fig, corps.firstChild);
  }

  // ---- l'aperçu au survol du plan -------------------------------------------
  // Survoler une salle du plan du château en montre la toile, EN GRAND. Le plan
  // dit où sont les pièces ; la toile dit à quoi elles ressemblent — et c'est en
  // parcourant le plan qu'on a envie des deux à la fois.
  //
  // Délégué sur le document, et non posé sur les salles : `plan.js` redessine
  // son SVG à chaque battement, et des écouteurs posés sur les formes seraient
  // jetés avec elles au premier redessin.
  //
  // L'aperçu ne prend jamais la souris (`pointer-events:none` en CSS) : sinon
  // il se glisserait sous le curseur, ferait sortir du survol, et clignoterait
  // sans fin. Il ne se pose pas non plus au premier pixel touché — un balayage
  // du plan traverse huit salles, et huit toiles qui s'allument à la file sont
  // une gêne, pas une aide.
  const DELAI = 140;
  let apercu = null, minuteur = null, survolee = null;

  function cacher() {
    clearTimeout(minuteur);
    survolee = null;
    if (apercu) apercu.classList.remove("vu");
  }

  function montrer(id) {
    if (!apercu) {
      apercu = document.createElement("div");
      apercu.id = "salle-apercu";
      apercu.innerHTML = '<img alt=""><span></span>';
      document.body.appendChild(apercu);
    }
    const img = apercu.querySelector("img");
    const src = cheminDe(id);
    if (img.getAttribute("src") !== src) img.setAttribute("src", src);
    apercu.querySelector("span").textContent = nomDe(id) || "";
    apercu.classList.add("vu");
  }

  // TROIS ENDROITS NOMMENT LA SALLE, et le survol vaut pour les trois :
  //   • une salle du plan du château (`.plan-salle`) — on parcourt les pièces ;
  //   • l'en-tête de lieu du bandeau (`#lieu`) — « La chambre de la Table
  //     Peinte, Peyredragon », le nom de là où l'on est ;
  //   • la vignette posée dans le fil à l'arrivée (`.salle-vue`) — la revoir en
  //     grand sans remonter la chronique.
  // Le bouton « ↕ salle » de la colonne des présents n'en est PAS un : c'est la
  // bascule de tri, et y accrocher une toile la ferait s'ouvrir chaque fois
  // qu'on va changer l'ordre.
  function salleSousLeCurseur(cible) {
    if (!cible || !cible.closest) return null;
    const g = cible.closest(".plan-salle");
    if (g) return g.dataset.id || null;
    if (cible.closest("#lieu") || cible.closest(".salle-vue")) {
      return (window.Plan && Plan.salle && Plan.salle()) || null;
    }
    return null;
  }

  document.addEventListener("mouseover", (e) => {
    const id = salleSousLeCurseur(e.target);
    if (!id || !avec || !avec.has(id)) { if (survolee) cacher(); return; }
    if (id === survolee) return;
    clearTimeout(minuteur);
    survolee = id;
    minuteur = setTimeout(() => montrer(id), DELAI);
  });
  // Sortir du plan referme : sans ça, la toile resterait posée sur l'écran
  // après que la souris est partie ailleurs.
  document.addEventListener("mouseout", (e) => {
    if (!salleSousLeCurseur(e.target)) return;
    // On ne referme que si l'on sort VRAIMENT : passer d'une forme à l'autre
    // dans la même salle du plan ne doit pas faire battre la toile.
    if (!salleSousLeCurseur(e.relatedTarget)) cacher();
  });

  // Tout item porteur d'un `lieu` peut nous déplacer — pas seulement `salle`.
  // Un récit qui dit « elle descend au quai » change la salle sans redéclarer
  // la pièce, et la toile doit suivre.
  ["salle", "recit", "replique", "geste", "breve", "evenement", "vous", "table",
   "pensee", "ecrit", "marque"].forEach((t) => Bus.enregistrer(t, poser));

  // Changement de scène : on oublie où l'on était, pour que le retour dans une
  // salle déjà vue se marque de nouveau.
  Bus.enregistrer("effacer", () => { derniere = null; });
})();
