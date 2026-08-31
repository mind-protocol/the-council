// La nav du décor — où l'on regarde, et comment y revenir.
//
// Le décor empile des échelles (le château, le royaume, les livres, l'échiquier,
// les gens, les jours…) et n'en montre qu'une. Jusqu'ici, seule l'échelle était
// retenue : on revenait dans « Les livres » sans le volume qu'on y lisait, et un
// rechargement de page rendait l'endroit exact introuvable. Trois choses ici :
//
//  1. L'ADRESSE LA PLUS PRÉCISE. Chaque échelle déclare ce qui, chez elle, fait
//     un endroit — le volume et son coffret, l'affaire ouverte, le rangement des
//     gens. `enregistrer(vue, {clefs, etat, poser})` : `etat` rend l'endroit,
//     `poser` y retourne. Une échelle sans détail n'a rien à déclarer.
//  2. LA BARRE D'ADRESSE. L'endroit s'écrit dans le `?…` de l'URL — donc il
//     survit à un rechargement, se met en signet, et se colle à quelqu'un.
//  3. LES DEUX FLÈCHES, à la place de la jauge de tension : le chemin parcouru
//     dans le décor, pas l'historique du navigateur. On ne pousse RIEN dans
//     `history` (une flèche « suivant » ne peut pas se deviner de `history`, et
//     mêler les deux ferait sortir de la page une fois sur deux) : on tient sa
//     propre pile, et l'URL est réécrite en place.
//
// Rien de tout cela n'entre dans l'état ni ne coûte une minute : regarder n'est
// pas agir. Ce module se charge AVANT les échelles, qui s'inscrivent auprès de
// lui au chargement.
window.Nav = (() => {
  const CLE_DERNIER = "conseil-nav";        // le dernier endroit, pour un onglet neuf
  const CLE_PILE = "conseil-nav-pile";      // le chemin, pour les deux flèches
  const MAX = 60;                           // au-delà, on oublie par le début

  // ---- ce que chaque échelle déclare d'elle-même ---------------------------
  const sources = {};
  const NOTRES = new Set(["vue"]);
  function enregistrer(vue, def) {
    sources[vue] = def || {};
    (def && def.clefs || []).forEach((k) => NOTRES.add(k));
  }

  const vueCourante = () => (window.Plan && Plan.vue) ? Plan.vue() : null;

  // L'endroit où l'on est, à l'instant : l'échelle, plus ce qu'elle dit d'elle.
  function ici() {
    const v = vueCourante();
    if (!v) return null;
    const a = { vue: v };
    const s = sources[v];
    if (s && s.etat) {
      let d = null;
      try { d = s.etat(); } catch (e) { d = null; }
      Object.keys(d || {}).forEach((k) => {
        const x = d[k];
        if (x != null && x !== "" && x !== false) a[k] = String(x);
      });
    }
    return a;
  }

  const cle = (a) => !a ? "" :
    Object.keys(a).sort().map((k) => k + "=" + a[k]).join("&");

  // ---- la barre d'adresse --------------------------------------------------
  // On ne touche QUE nos clefs : ce qu'un autre a mis dans le `?…` lui reste.
  function ecrireUrl(a) {
    if (!a) return;
    const p = new URLSearchParams(location.search);
    [...p.keys()].forEach((k) => { if (NOTRES.has(k)) p.delete(k); });
    Object.keys(a).forEach((k) => p.set(k, a[k]));
    const q = p.toString();
    const url = location.pathname + (q ? "?" + q : "") + location.hash;
    try { history.replaceState(history.state, "", url); } catch (e) {}
    try { localStorage.setItem(CLE_DERNIER, JSON.stringify(a)); } catch (e) {}
  }

  function lireUrl() {
    const p = new URLSearchParams(location.search);
    if (!p.get("vue")) return null;
    const a = {};
    [...p.keys()].forEach((k) => { if (NOTRES.has(k)) a[k] = p.get(k); });
    return a.vue ? a : null;
  }

  function lireGarde() {
    try {
      const a = JSON.parse(localStorage.getItem(CLE_DERNIER) || "null");
      return (a && a.vue) ? a : null;
    } catch (e) { return null; }
  }

  // ---- la pile : le chemin parcouru ---------------------------------------
  // Dans la session de l'onglet, pas dans `localStorage` : un chemin est le
  // fil d'une lecture, il n'a pas à traverser deux fenêtres ouvertes côte à côte.
  let pile = [], pos = -1;
  try {
    const g = JSON.parse(sessionStorage.getItem(CLE_PILE) || "null");
    if (g && Array.isArray(g.pile)) { pile = g.pile; pos = g.pos; }
  } catch (e) {}
  const garderPile = () => {
    try { sessionStorage.setItem(CLE_PILE, JSON.stringify({ pile, pos })); } catch (e) {}
  };

  function noter(a) {
    if (!a) return;
    if (pos >= 0 && cle(pile[pos]) === cle(a)) return;
    pile = pile.slice(0, pos + 1);
    pile.push(a);
    if (pile.length > MAX) pile = pile.slice(pile.length - MAX);
    pos = pile.length - 1;
    garderPile();
    rendreFleches();
  }

  // ---- aller quelque part --------------------------------------------------
  // `cible` tient tant que l'endroit n'est pas atteint : les livres et
  // l'échiquier chargent par le réseau, et l'endroit demandé n'existe pas encore
  // à la première tentative. Tant qu'une cible court, on ne note rien — sinon le
  // chemin se remplirait des étapes du retour.
  //
  // Et l'on TIENT quelques secondes après avoir touché au but, au lieu de lâcher
  // aussitôt : au chargement, tout le fil est rejoué d'un coup, et la dernière
  // main posée sur la table peinte rappelle le royaume par-dessus l'endroit
  // qu'on venait de rouvrir. Une reprise n'est pas une navigation — c'est du
  // passé qui repasse —, donc c'est l'adresse qui gagne.
  let cible = null, essais = 0, minuteur = null, tenirJusqu = 0;

  function viser(a, opt) {
    if (!a || !a.vue) return;
    cible = a; essais = 0;
    tenirJusqu = Date.now() + ((opt && opt.tenir) || 4000);
    if (!opt || !opt.silencieux) ecrireUrl(a);
    clearTimeout(minuteur);
    poser();
  }

  function poser() {
    if (!cible) return;
    const a = cible;
    if (window.Plan && Plan.montrer) Plan.montrer(a.vue);
    let fait = vueCourante() === a.vue;
    if (fait) {
      const s = sources[a.vue];
      if (s && s.poser) {
        const p = {};
        (s.clefs || []).forEach((k) => { if (a[k] != null) p[k] = a[k]; });
        try { fait = s.poser(p) !== false; } catch (e) { fait = false; }
      }
    }
    // Dix secondes de patience pour ATTEINDRE l'endroit, quatre de plus pour
    // l'y TENIR. Passé quoi l'on prend ce qu'on a : mieux vaut la bonne échelle
    // sans le bon volume qu'une flèche qui tourne dans le vide.
    if (fait && Date.now() > tenirJusqu) {
      cible = null; derniere = cle(ici()); rendreFleches(); return;
    }
    if (!fait && ++essais > 33) { cible = null; derniere = cle(ici()); return; }
    minuteur = setTimeout(poser, 250);
  }

  function aller(d) {
    const n = pos + d;
    if (n < 0 || n >= pile.length) return;
    pos = n; garderPile(); rendreFleches();
    viser(pile[pos]);
  }

  // ---- les deux flèches, à la place de la jauge ----------------------------
  let prec = null, suiv = null;
  function rendreFleches() {
    if (!prec) return;
    const nom = (a) => {
      if (!a) return "";
      const n = (window.Plan && Plan.nomVue) ? Plan.nomVue(a.vue) : null;
      return n || a.vue;
    };
    prec.disabled = pos <= 0;
    suiv.disabled = pos < 0 || pos >= pile.length - 1;
    prec.title = prec.disabled ? "Rien derrière" : "Revenir à « " + nom(pile[pos - 1]) + " »";
    suiv.title = suiv.disabled ? "Rien devant" : "Ravancer à « " + nom(pile[pos + 1]) + " »";
  }

  // ---- la veille : l'endroit peut changer sans passer par ici --------------
  // Un clic sur un coffret, un renvoi du fil, un conseiller qui montre l'affaire
  // dont il parle : personne n'a à prévenir la nav. On relit l'endroit, et l'on
  // note quand il a bougé. Deux mesures par seconde ne coûtent rien.
  let derniere = "";
  function veiller() {
    const a = ici();
    if (!a) return;
    const k = cle(a);
    if (k === derniere) return;
    derniere = k;
    if (cible) return;          // on est en train d'y aller : ce n'est pas une étape
    noter(a);
    ecrireUrl(a);
  }

  window.addEventListener("DOMContentLoaded", () => {
    const hote = document.getElementById("nav-hist");
    if (hote) {
      prec = hote.querySelector("#nav-prec");
      suiv = hote.querySelector("#nav-suiv");
      prec.addEventListener("click", () => aller(-1));
      suiv.addEventListener("click", () => aller(1));
    }
    // La lecture de l'adresse attend un tour de boucle, et ce n'est pas un
    // détail : les échelles s'inscrivent elles aussi au DOMContentLoaded, et
    // nav.js est chargé AVANT elles. Lire tout de suite, c'est lire une adresse
    // dont on ne connaît encore aucune clef — on retrouvait les livres, jamais
    // le volume.
    setTimeout(demarrer, 0);
  });

  function demarrer() {
    // L'URL d'abord — c'est elle qu'on a collée ou mise en signet ; le dernier
    // endroit gardé ensuite, pour l'onglet qu'on rouvre sans rien préciser.
    const demandee = lireUrl() || lireGarde();
    if (demandee) {
      // La pile reprise de la session peut déjà porter cet endroit en tête :
      // on ne l'y ajoute pas deux fois.
      if (pos < 0 || cle(pile[pos]) !== cle(demandee)) noter(demandee);
      derniere = cle(demandee);
      viser(demandee);
    }
    rendreFleches();
    // Le décor se pose en plusieurs temps (les échelles s'inscrivent, les
    // données rentrent) : on laisse retomber avant de veiller, sinon la première
    // seconde d'une page fraîche s'écrit dans le chemin.
    setTimeout(() => { veiller(); setInterval(veiller, 500); }, 1500);
    // une échelle qui bascule se voit tout de suite, sans attendre la mesure
    document.addEventListener("vue-changee", () => setTimeout(veiller, 60));
    // et le raccourci qu'on attend d'une nav
    document.addEventListener("keydown", (e) => {
      if (!e.altKey || e.ctrlKey || e.metaKey) return;
      const t = e.target;
      if (t && /^(INPUT|TEXTAREA)$/.test(t.tagName)) return;
      if (e.key === "ArrowLeft") { e.preventDefault(); aller(-1); }
      if (e.key === "ArrowRight") { e.preventDefault(); aller(1); }
    });
  }

  return { enregistrer, ici, viser, aller, url: ecrireUrl };
})();
