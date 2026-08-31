// combat.js — tenir sa position pendant que le temps passe.
//
// CE QUE C'EST : LA BALADE DONT L'HORLOGE EST DÉCROCHÉE DES JAMBES. Rien de
// plus, et c'est tout l'intérêt. `carte-ville.js` sait déjà faire tourner une
// scène en temps réel — un sélecteur ×1…×10, un bouton pause, un rapport au MJ
// tous les vingt mètres, et l'horloge du monde qui avance pour de bon. Mais son
// moteur est la DISTANCE : `avance` est en mètres, le rapport part quand on a
// marché, et un homme immobile ne produit donc jamais rien. C'est structurel,
// et c'est exactement ce qui manque à un combat.
//
// Debout devant une porte qu'on enfonce, il ne se passe rien de VOTRE fait et
// tout du fait des autres. Le moteur doit donc être le TEMPS : on reste où l'on
// est, les secondes tombent, et l'on rapporte ce qu'on perçoit d'ici.
//
// CE QU'IL N'Y AVAIT PAS À ÉCRIRE, et c'est ce qui rend ce module court :
//
//   • AUCUNE ROUTE SERVEUR. `croiser.autour(racine, lieu, x, y, date)` ne prend
//     qu'un point et une heure — pas d'itinéraire, pas d'identité. Et `/marche`
//     lit `metres` et `minutes` séparément : un tic immobile
//     ({metres: 0, minutes: 0.25}) passe tel quel. L'horloge avance, la
//     position s'écrit, ce qu'on longe et ce qu'on perçoit remontent au MJ.
//   • AUCUN CANAL NEUF VERS LE MJ. `/marche` empile déjà ses pas dans UN seul
//     fichier d'inbox, pour que le guetteur ne sonne qu'une fois au lieu de
//     quarante. Un combat de dix minutes tient dans le même sac.
//
// LA PAGE NE DIT JAMAIS CE QU'ON PERÇOIT. Même règle qu'à la balade, et elle
// est dure : la barre ne montre que l'heure et le corps. Ce qu'on a vu,
// entendu, ou trouvé par terre appartient au récit, et le récit arrive par le
// flux, de la main du MJ. Une barre qui afficherait « 3 blessés à 40 pas »
// ferait de la scène un tableau de bord.
//
// SE METTRE EN PAUSE ARRÊTE VOTRE HORLOGE, PAS LA BATAILLE. La perception se
// calcule à l'heure du siège : tant qu'on est en pause, on ne vieillit pas, et
// la porte qu'on est en train d'enfoncer attend. Ce n'est pas un défaut — c'est
// la règle de toute la maison, où le temps n'avance que quand quelqu'un le fait
// avancer. Le bouton est là pour qu'on puisse parler au MJ sans perdre la scène.
"use strict";
window.Combat = (() => {
  const HOTE = "ville2d";

  // Le grain du rapport, en secondes de FICTION. La balade rapporte tous les
  // vingt mètres, ce qui fait quinze secondes sur une artère et quarante-deux
  // dans les escaliers de Peyredragon : quinze tombe dans la même famille, et
  // c'est la cadence à laquelle une scène se raconte sans devenir un journal.
  // Un sac de six cents secondes fait donc quarante rapports — dix minutes
  // réelles à ×1, trois minutes vingt à ×3.
  const TIC_S = 15;

  let ouvert = false;      // le mode est-il installé
  let court = false;       // l'horloge tourne-t-elle
  let vitesse = 3;
  let ecoule = 0;          // secondes de fiction depuis le début de la scène
  let depuisTic = 0;       // secondes de fiction depuis le dernier rapport
  let derniereImage = 0;
  let date = null;         // ce que le serveur dit de l'heure, après chaque tic
  let ici = null;          // {x, y} — où l'on tient, en mètres
  let envoi = false;       // un rapport est en vol : on n'en empile pas deux
  let tics = 0;

  const hote = () => document.getElementById(HOTE);
  const deuxChiffres = (n) => (n < 10 ? "0" : "") + n;
  const hhmm = (m) => Math.floor(m / 60) + "h" + deuxChiffres(Math.round(m) % 60);
  const mmss = (s) => Math.floor(s / 60) + "′" + deuxChiffres(Math.floor(s) % 60) + "″";

  // ---- la barre -------------------------------------------------------------
  // Même découpe qu'à la balade, et pour la même raison : on bâtit une fois des
  // nœuds qui ne bougent plus, et le tic n'écrit que du texte dedans. Refaire
  // l'`innerHTML` soixante fois par seconde tuerait le clic à mi-course.
  function barre() {
    const h = hote();
    if (!h) return null;
    let b = h.querySelector(".cv-combat-barre");
    if (b) return b;
    b = document.createElement("div");
    b.className = "cv-combat-barre";
    b.innerHTML =
      '<button data-cb="marche" class="cv-cb-marche">▶</button>' +
      '<span class="cv-cb-heure"></span>' +
      '<span class="cv-cb-ecoule"></span>' +
      '<span class="cv-allure"><button data-cb="lent">−</button>' +
      '<b>×3</b><button data-cb="vite">+</button></span>' +
      '<button data-cb="retirer" class="cv-cb-retirer">Se retirer</button>';
    h.appendChild(b);
    b.addEventListener("click", (ev) => {
      const t = ev.target.closest("[data-cb]");
      if (!t) return;
      const q = t.dataset.cb;
      if (q === "marche") { court = !court; derniereImage = 0; if (court) tic(); }
      if (q === "retirer") fermer();
      if (q === "vite") vitesse = Math.min(10, vitesse + (vitesse < 3 ? 1 : 2));
      if (q === "lent") vitesse = Math.max(1, vitesse - (vitesse > 3 ? 2 : 1));
      rafraichir();
    });
    return b;
  }

  function rafraichir() {
    const b = hote() && hote().querySelector(".cv-combat-barre");
    if (!b) return;
    b.classList.toggle("marche", court);
    b.querySelector(".cv-cb-marche").textContent = court ? "⏸" : "▶";
    b.querySelector(".cv-cb-heure").textContent =
      date ? hhmm(date.minute || 0) : "—";
    // Ce qu'on montre du temps passé est le temps de FICTION, jamais le temps
    // réel : à ×10 les deux divergent d'un facteur dix, et c'est le premier qui
    // compte pour qui joue la scène.
    b.querySelector(".cv-cb-ecoule").textContent =
      ecoule > 0 ? mmss(ecoule) : "";
    b.querySelector(".cv-allure b").textContent = "×" + vitesse;
  }

  // ---- le tic ---------------------------------------------------------------
  // Une image, un peu de temps, et tous les TIC_S secondes un mot au MJ.
  function tic(t) {
    if (!court || !ouvert) return;
    const maintenant = t || performance.now();
    if (!derniereImage) derniereImage = maintenant;
    // Le plafond du quart de seconde est celui de la balade, et il a la même
    // raison d'être : un onglet qu'on quitte et qui revient rendrait un `dt` de
    // trente secondes, et l'on sauterait une demi-heure de fiction d'un coup.
    const dt = Math.min(.25, (maintenant - derniereImage) / 1000);
    derniereImage = maintenant;
    ecouler(dt * vitesse);
    requestAnimationFrame(tic);
  }

  // Le cœur, séparé de l'horloge qui le pousse. Deux raisons, et la seconde
  // n'est pas un détail de confort :
  //
  //   1. UN ONGLET EN ARRIÈRE-PLAN GÈLE LA SCÈNE, parce que
  //      `requestAnimationFrame` ne bat pas dans une page qui ne compose plus
  //      d'images. C'est VOULU et non subi : le temps de ce jeu n'avance que
  //      quand quelqu'un le fait avancer, et une bataille qui courrait pendant
  //      qu'on regarde ailleurs écrirait dans l'état sans personne pour la
  //      lire. Le dire ici, parce que ça se remarque et qu'on le prendrait
  //      autrement pour une panne.
  //   2. ON PEUT DONC LA POUSSER À LA MAIN — `Combat.avancer(30)` fait passer
  //      trente secondes de fiction sans dépendre du compositeur. C'est ce qui
  //      rend le mode vérifiable, et c'est aussi le levier d'un MJ qui veut
  //      faire tomber la suite sans attendre l'horloge.
  function ecouler(fiction) {
    if (!ouvert) return;
    ecoule += fiction;
    depuisTic += fiction;
    if (depuisTic >= TIC_S) rapporter(depuisTic);
    rafraichir();
  }

  // Ce qu'on envoie, et pourquoi c'est `/marche` : parce que c'est déjà la
  // route qui fait avancer l'horloge du siège et celle du monde, qui écrit la
  // position, et qui interroge la bataille. Un combat n'a pas d'autre besoin —
  // il a seulement zéro mètre à déclarer.
  function rapporter(secondes) {
    if (envoi || !ici) return;
    depuisTic = 0;
    envoi = true;
    tics++;
    // QUI EST LÀ SE COMPTE ICI, PAS AU SERVEUR — la page a déjà les corps sous
    // la main (`foule2d`), et les porter au serveur coûterait `journee.js` et
    // quatre méga-octets de cellules pour redire ce qu'on sait.
    const gens = (window.Foule2d && Foule2d.presents)
      ? Foule2d.presents(ici.x, ici.y) : null;
    fetch("/marche", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        x: ici.x, y: ici.y,
        metres: 0,
        minutes: secondes / 60,
        gens,
        // Ce qui distingue un homme qui tient sa position d'un homme qui
        // marche. Sans ce mot, le MJ recevrait quarante pas de zéro mètre et
        // devrait deviner que personne n'a bougé parce qu'on se battait.
        combat: true,
        fin: false,
      }),
    }).then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        envoi = false;
        if (!d) return;
        if (d.date) {
          date = d.date;
          // L'HEURE EST DICTÉE PAR LA CARTE. Pendant un combat, ce n'est plus
          // le fil qui publie l'heure : c'est ici qu'elle avance, et le bandeau
          // du joueur doit la suivre — sans quoi il lit l'heure du départ
          // pendant qu'on enfonce une porte. Le MJ garde le transport
          // (arrêter, relancer, accélérer), plus la montre.
          if (window.Bus && Bus.heureDeLaCarte) Bus.heureDeLaCarte(d.date.minute);
        }
        rafraichir();
      })
      .catch(() => { envoi = false; });
  }

  // ---- ouvrir, fermer -------------------------------------------------------
  function ouvrir() {
    const p = (window.CarteVille && CarteVille.ou) ? CarteVille.ou() : null;
    if (!p) return false;          // sans mètres, il n'y a pas de scène
    ici = { x: p.x, y: p.y };
    ouvert = true;
    court = false;
    ecoule = 0;
    depuisTic = 0;
    tics = 0;
    date = null;
    const b = barre();
    if (b) b.classList.add("ouverte");
    rafraichir();
    return true;
  }

  // On ferme en le DISANT. Le dernier rapport porte `fin`, ce qui referme le
  // sac d'inbox : sans lui, le guetteur attendrait une arrivée qui ne vient
  // plus, et le MJ lirait une scène qui n'a pas de dernière ligne.
  function fermer() {
    court = false;
    ouvert = false;
    if (ici) {
      const gens = (window.Foule2d && Foule2d.presents)
        ? Foule2d.presents(ici.x, ici.y) : null;
      fetch("/marche", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x: ici.x, y: ici.y, metres: 0,
                               minutes: depuisTic / 60, gens,
                               combat: true, fin: true }),
      }).catch(() => {});
    }
    depuisTic = 0;
    const b = hote() && hote().querySelector(".cv-combat-barre");
    if (b) b.classList.remove("ouverte", "marche");
  }

  // ---- par où l'on y entre --------------------------------------------------
  // UN BOUTON, ET IL SE POSE LUI-MÊME. Le mode aurait pu s'ouvrir tout seul dès
  // qu'une bataille datée tombe à portée — c'est tentant, et c'est faux : ce
  // serait la page qui déciderait qu'une scène commence, alors que la seule
  // chose qui fait commencer une scène dans ce jeu est quelqu'un qui décide.
  // Le joueur voit le bouton, il tient sa position quand il le veut.
  //
  // Il se pose dans `#ville2d` comme les autres boutons du plan, sans rien
  // demander à `carte-ville.js` — on ne se met pas dans le chemin du module
  // qui dessine.
  function entree() {
    const h = hote();
    if (!h || h.querySelector(".cv-tenir")) return;
    const b = document.createElement("button");
    b.className = "cv-tenir";
    b.type = "button";
    b.title = "Tenir cette position pendant que le temps passe";
    b.textContent = "Tenir la position";
    b.addEventListener("click", () => {
      if (ouvert) { fermer(); return; }
      if (!ouvrir()) b.textContent = "On ne sait pas où vous êtes";
    });
    h.appendChild(b);
  }

  // L'HÔTE EST REBÂTI SOUS NOUS, et c'est la vraie raison pour laquelle un
  // bouton posé une fois disparaissait. `carte-ville.dessiner()` refait le
  // contenu de `#ville2d` quand le plan arrive — deux secondes après le
  // chargement, pour trois méga-octets — et emporte tout ce qui s'y trouvait.
  // C'est d'ailleurs pourquoi `foule2d` et `bataille2d` ne se posent pas seuls :
  // ils sont APPELÉS par le dessin (`Foule2d.poser(h, …)`), une fois la page
  // refaite.
  //
  // Le patron de la maison serait donc un `Combat.poser(h)` appelé depuis
  // `dessiner()`. On s'en passe ici pour ne pas écrire dans un fichier qu'une
  // autre session tient ouverte : on OBSERVE l'hôte et l'on repose le bouton
  // s'il a disparu. Même résultat, aucune ligne chez le voisin — et le jour où
  // les deux plumes se rejoignent, ces quinze lignes se remplacent par l'appel.
  // ---- ce que le MJ peut, et ce qu'il ne peut plus -------------------------
  // TROIS BOUTONS, PAS UNE MONTRE. L'heure est dictée par la carte : elle
  // avance ici, en temps réel, et c'est elle qui paie les minutes au serveur.
  // Le MJ ne la POSE plus — il la conduit, et rien d'autre :
  //
  //     {"type":"horloge","action":"pause"}
  //     {"type":"horloge","action":"marche"}
  //     {"type":"horloge","action":"vitesse","vitesse":5}
  //
  // C'est volontairement pauvre. Le jour où l'on pourrait écrire « il est
  // maintenant six heures » depuis le fil, on aurait deux horloges qui se
  // contredisent au milieu d'une bataille — et l'une des deux serait celle sur
  // laquelle le joueur a fondé sa décision de tenir ou de fuir.
  //
  // Un ordre qui arrive alors qu'aucune scène ne court ne fait rien : on ne
  // lance pas un combat depuis le fil, c'est le joueur qui tient la position.
  if (window.Bus && Bus.enregistrer) {
    Bus.enregistrer("horloge", (it) => {
      if (!ouvert) return;
      if (it.action === "pause") court = false;
      else if (it.action === "marche") {
        if (!court) { court = true; derniereImage = 0; tic(); }
      } else if (it.action === "vitesse") {
        const v = +it.vitesse;
        if (isFinite(v)) vitesse = Math.max(1, Math.min(10, Math.round(v)));
      }
      rafraichir();
    });
  }

  function veiller() {
    entree();
    const h = hote();
    if (!h || !window.MutationObserver) return;
    new MutationObserver(() => {
      if (!h.querySelector(".cv-tenir")) entree();
    }).observe(h, { childList: true });
  }

  // On ne parie pas non plus sur l'ordre de chargement : un `DOMContentLoaded`
  // nu ne s'exécute jamais si l'événement est déjà passé quand le script
  // arrive. On regarde où en est le document au lieu de supposer.
  if (document.readyState === "loading")
    window.addEventListener("DOMContentLoaded", veiller);
  else veiller();

  return { ouvrir, fermer, avancer: ecouler,
           etat: () => ({ ouvert, court, ecoule, tics, date, ici }) };
})();
