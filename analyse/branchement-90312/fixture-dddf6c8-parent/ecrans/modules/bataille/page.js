(() => {
"use strict";

// LA CHAÎNE — ET ELLE N'EST PLUS ÉCRITE ICI.
//
// C'était la huitième liste du dépôt, et la note qui tenait cette place disait
// déjà le mal : `sac.js` en tenait une, `jeu.html` une autre, les scripts
// d'analyse trois de plus, et l'une d'elles avait divergé en silence. On ne
// « note » plus que le manifeste partagé est devenu nécessaire : il existe, et
// c'est `bataille/moteur/chaine.js` qui le porte, pour la page comme pour le
// four et le banc.
//
// Les trois premiers (`hasard`, `mesures`, `1-corps`) sont déjà chargés en tête
// de page par le banc du dessus : on les déclare `deja` plutôt que de les
// retrancher à la main d'une liste qu'on aurait recopiée.
const DEJA = ["bataille/hasard.js", "bataille/mesures.js", "survival-stack/1-corps.js"];

const $ = (id) => document.getElementById(id);
const PARAMETRES = new URL(window.location.href).searchParams;
// L'ESTAMPILLE EST L'INSTANT DE CHARGEMENT — plus jamais une constante qu'on
// bouge à la main. L'ancienne discipline (« se bouge à CHAQUE fois qu'on touche
// au moteur, et l'oubli ne se voit pas ») a été payée le 27 août : l'écran
// servait l'ancien moteur pendant que le banc mesurait le nouveau. Le serveur
// envoie `no-store` (mesuré le 30 : serveur/http.js, envoyer) — le cache ne
// devrait déjà rien garder ; l'instant rend chaque chargement inratable même si
// une couche de cache (bfcache, proxy) se croit plus maligne. Un signet reste
// stable : l'estampille ne vit que le temps de la page.
const VERSION_BATAILLE = String(Date.now());

// L'URL EST UN SIGNET DE TRAVAIL. Une épreuve, un volet ou un cadrage doit
// pouvoir être envoyé à quelqu'un sans la phrase « clique là, puis descends ».
// On remplace l'entrée courante pour les réglages continus ; ouvrir une
// épreuve ou changer de volet pousse une vraie étape dans l'historique.
function urlEtat(changements, pousser = false) {
  const u = new URL(window.location.href);
  for (const [cle, valeur] of Object.entries(changements)) {
    if (valeur == null || valeur === "") u.searchParams.delete(cle);
    else u.searchParams.set(cle, String(valeur));
  }
  history[pousser ? "pushState" : "replaceState"](null, "", u);
}
window.addEventListener("popstate", () => window.location.reload());
// `charge` dit qu'on a COMMENCÉ à charger, `pret` qu'on a FINI — et les deux
// sont nécessaires. Avec le seul premier, la sonde partait sur une promesse en
// cours (une promesse est vraie) et cherchait `Bataille2d` avant que le script
// ne soit arrivé. Le drapeau garde aussi les boutons de la barre, qu'on peut
// cliquer pendant les quelques secondes du premier chargement.
let charge = null, pret = false, vue = null, cadre = null,
    zoom = Math.max(0, Math.min(1, +(PARAMETRES.get("zoom") || 0)));
let toponymie = null, planVille = null;
let sceneActiveId = null;

const script = (src) => new Promise((ok, ko) => {
  const s = document.createElement("script");
  // Le banc est modifié en direct. Une vieille IIFE gardée par le navigateur
  // peut autrement afficher l'ancien moteur tout en lisant la nouvelle liste
  // d'épreuves : le disque et l'écran racontent alors deux scènes différentes.
  s.src = src + (src.includes("?") ? "&" : "?") + "v=" + VERSION_BATAILLE;
  s.onload = ok; s.onerror = () => ko(new Error(src));
  document.head.appendChild(s);
});

async function charger() {
  // Le manifeste est chargé en tête de page (une balise, avant celle-ci) : s'il
  // manque, on le dit au lieu de retomber sur une liste de secours. Une liste
  // de secours est exactement la neuvième liste qu'on vient de supprimer.
  if (!window.BatailleChaine)
    throw new Error("bataille/moteur/chaine.js n'est pas posé : la page ne sait " +
                    "plus quoi charger, et elle refuse de le deviner.");
  const CHAINE = window.BatailleChaine.urls("scene", { deja: DEJA });
  for (const s of CHAINE) await script(s);        // en série : chacun attend le précédent
  // CE QUI MANQUE SE NOMME. Sans ce contrôle, un morceau qui n'a pas répondu se
  // découvre bien plus loin, sous la forme d'un `undefined` au premier appel.
  const absents = window.BatailleChaine.manquants("scene", window);
  if (absents.length)
    throw new Error("la chaîne est incomplète : " + absents.join(", "));
  const planNomme = fetch("/monde/plan2d").then((r) => r.ok ? r.json() : null)
    .catch(() => null);
  await Bataille2d.preparer("/monde");
  const plan = await planNomme;
  planVille = plan;
  toponymie = plan ? { axes: plan.axes || [], reperes: plan.reperes || [] } : null;
  Bataille2d.poser($("toile"), () => vue, { source: "/monde" });
  DragonEpreuve.installer({ canvas: $("dragonCanvas"), stats: $("sondes"), note: $("dnote"),
                            bataille: Bataille2d });
  batirListe();
  batirRoster();
  const att = $("sattente"); if (att) att.remove();
  pret = true;
  tirer();
  // Le signet doit rouvrir la meme experience, pas seulement sa fiche. Le
  // feu reste pourtant remis a zero : son URL nomme le banc, pas une cuisson
  // ephemere qui n'est volontairement stockee nulle part.
  if (PARAMETRES.get("feu") === "ville") entrerFeu(false);
  else if (PARAMETRES.get("action") === "poser" &&
           scenarioParId(PARAMETRES.get("epreuve")))
    poserEpreuve(PARAMETRES.get("epreuve"));
  else {
    // La carte est un outil avant d'être une bataille. L'ouverture montre la
    // ville seule ; une force n'existe ici que parce qu'une épreuve la convoque.
    Bataille2d.vider();
    Bataille2d.echelle(+("" + $("sechelle").value));
    modeCarteSeule(true);
    cadrerVille(); Bataille2d.rafraichir();
  }
}

// ═══ JOUER UN SCÉNARIO ══════════════════════════════════════════════════════
// La page ne fait QUE piloter : c'est `scenarios.js` qui dresse, déforme,
// avance et juge — le même code que le banc headless appellera. Si l'un des
// deux se mettait à faire sa propre cuisine, on aurait deux batailles.
// ═══ LE ROSTER, DESSINÉ ════════════════════════════════════════════════════
// On ne recopie AUCUN nombre ici : tout sort de `roster.js`, qui fait autorité.
// La page ne fait que choisir comment le montrer — et elle emprunte les teintes
// du fer à `mesures.js`, pour qu'un métier lu dans la colonne se reconnaisse
// sur la carte sans qu'on ait à l'expliquer.
function batirRoster() {
  const R = window.BatailleRoster;
  if (!R) return;
  const corps = R.tout();
  const utilises = [];
  for (const a of corps) for (const m in a.metiers)
    if (a.metiers[m] && utilises.indexOf(m) < 0) utilises.push(m);

  const legende = utilises.map((m) => {
    const M = R.METIERS[m];
    return '<span title="' + M.dit.replace(/"/g, "'") + '"><i style="background:' +
      M.teinte + '"></i>' + M.nom + (M.substitut ? " *" : "") + "</span>";
  }).join("");

  const bloc = (a) => {
    // La barre : le mélange d'armes, à l'échelle du corps.
    const barre = utilises.map((m) => {
      const n = a.metiers[m] || 0;
      return n ? '<i style="width:' + (100 * n / a.total).toFixed(2) + "%;background:" +
        R.METIERS[m].teinte + '" title="' + n + " " + R.METIERS[m].nom + '"></i>' : "";
    }).join("");
    // Les blocs : une boîte par centaine, un trait par vintaine. Le dernier
    // trait est CREUX quand la vintaine est en sous-effectif — c'est
    // l'information qu'un tableau d'effectifs cacherait.
    let reste = a.vintaines;
    const cents = [];
    for (let c = 0; c < a.centaines; c++) {
      const n = Math.min(5, reste); reste -= n;
      let t = "";
      for (let v = 0; v < n; v++) {
        const derniere = (c === a.centaines - 1 && v === n - 1 && a.reste > 0);
        t += '<b class="' + (derniere ? "creuse" : "") + '"></b>';
      }
      cents.push('<span class="cent">' + t + "</span>");
    }
    return '<div class="rc"><h5>' + a.nom + " <em>— " + a.hommes + " h</em></h5>" +
      '<div class="melange">' + barre + "</div>" +
      '<div class="cents">' + cents.join("") + "</div>" +
      '<div class="cout">' + a.centaines + " centaines · " + a.pleines + " vintaines" +
      (a.reste ? " + une à " + a.reste : "") +
      ' · <b>' + a.coureursPourUnOrdre + " coureurs</b> pour un ordre précis</div></div>";
  };

  const total = corps.filter((a) => a.camp === "assaut")
    .reduce((s, a) => s + a.coureursPourUnOrdre, 0);

  // ── LE CATALOGUE, EN RONDS ───────────────────────────────────────────────
  // Un rond par homme, aux vrais espacements. PLEIN = il peut frapper
  // quelqu'un, CREUX = il attend. C'est la contrainte géométrique de la
  // recherche rendue en image : on ne la lit plus, on la voit.
  const figure = (id) => {
    const f = R.figurer(id);
    if (!f) return "";
    const t = f.type;
    const xs = f.ronds.map((r) => r.x), ys = f.ronds.map((r) => r.y);
    const x0 = Math.min(...xs) - 0.5, x1 = Math.max(...xs) + 0.5;
    const y0 = Math.min(...ys) - 0.5, y1 = Math.max(...ys) + 0.5;
    const L = 258, k = Math.min(L / (x1 - x0), 46 / (y1 - y0), 13);
    const w = (x1 - x0) * k, h = (y1 - y0) * k;
    const ronds = f.ronds.map((r) => {
      const c = (R.METIERS[r.metier] || {}).teinte || "#888";
      const cx = (r.x - x0) * k, cy = (r.y - y0) * k;
      return '<circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) +
        '" r="' + (k * 0.3).toFixed(1) + '" fill="' + (r.engage ? c : "none") +
        '" stroke="' + c + '" stroke-width="1" opacity="' +
        (r.engage ? 1 : 0.45) + '"><title>' + (R.METIERS[r.metier] || {}).nom +
        (r.engage ? " — il touche" : " — il attend") + "</title></circle>";
    }).join("");
    const marque = t.simule === "non" ? ' <em class="hs">non simulé</em>'
                 : t.simule === "substitue" ? ' <em class="sub">substitué</em>' : "";
    return '<div class="ty"><h5>' + t.n + ". " + t.nom + " <em>— " + t.hommes +
      " h</em>" + marque + "</h5>" +
      '<svg viewBox="0 0 ' + w.toFixed(0) + " " + h.toFixed(0) + '" width="' +
        w.toFixed(0) + '" height="' + h.toFixed(0) + '">' + ronds + "</svg>" +
      '<div class="meta">' + f.formation.nom + " · " + f.rangs + " rang" +
        (f.rangs > 1 ? "s" : "") + " · <b>" + Math.round(100 * f.partEngagee) +
        " %</b> peuvent frapper</div>" +
      "<p>" + t.pour + "</p></div>";
  };

  $("vueRoster").innerHTML =
    '<p class="chapo">Une unité se définit par <b>la façon dont on peut lui ' +
      "parler</b>. Trois modes, trois échelons, trois coûts.</p>" +
    '<div id="legende">' + legende + "</div>" +
    '<h6 class="sect">Le catalogue — ce qu\'on peut aligner</h6>' +
    '<p class="chapo">Rond <b>plein</b> : il peut frapper quelqu\'un. Rond ' +
      "<b>creux</b> : il attend. La profondeur décide, pas le courage.</p>" +
    R.TYPES.map((t) => figure(t.id)).join("") +
    '<h6 class="sect">Une composition — la nuit de la Gadoue</h6>' +
    corps.map(bloc).join("") +
    '<div class="ech">' +
      R.ECHELONS.map((e) => "<div><b>" + e.nom + "</b> — " +
        (e.hommes ? e.hommes + " hommes, " : "") + e.chef +
        (e.monte ? " (monté)" : "") + ", par <em>" +
        (e.parle === "voix" ? "la voix" : e.parle === "coureur" ? "un coureur"
          : "la bannière — 3 codes") + "</em>.<br>" + e.dit + "</div>").join("") +
      "<div>* Le moteur n'a pas de combat à distance : les archers et " +
      "arbalétriers portent le coutelas <b>en attendant</b>, et le fichier le " +
      "dit (<code>substitut</code>). Le jour où le tir existera, on bascule " +
      "ces lignes-là et rien d'autre.</div>" +
      "<div><b>" + total + " coureurs</b> pour porter un seul ordre précis à " +
      "tout l'assaut — dix-huit trajets, dix-huit occasions de tomber. C'est " +
      "la friction du commandement, et elle tombe de la structure.</div>" +
    "</div>";
}

let menuOuvert = null;
function afficherMenu(nom) {
  menuOuvert = nom;
  $("menu").classList.toggle("ferme", !nom);
  $("vueRoster").classList.toggle("on", nom === "roster");
  $("vueEpreuves").classList.toggle("off", nom !== "epreuves");
  $("mRoster").classList.toggle("on", nom === "roster");
  $("mEpreuves").classList.toggle("on", nom === "epreuves");
  urlEtat({ menu: nom || "ferme" });
  if (pret) rendu();
}
function ongletMenu(roster) {
  const demande = roster ? "roster" : "epreuves";
  afficherMenu(menuOuvert === demande ? null : demande);
}

let verdicts = null, choisie = PARAMETRES.get("epreuve");
const passages = {};                     // id -> le dernier verdict d'ensemble
let dragonActif = false, dragonMode = PARAMETRES.get("dragon") || "suite";
let dragonVilleActif = false;
let dragonRangeeActif = false;
let feuActif = false, feuInstalle = false;

// Le dragon n'est ni une page ni un second catalogue : c'est une épreuve de
// cette liste, avec les mêmes gestes et la même horloge. Son moteur reste
// spécialisé parce que son état comporte z, pente, banque et température —
// dimensions que `Bataille2d` ne porte pas encore.
const EPREUVE_DRAGON = Object.freeze({
  id: "dragon-survol", n: "D1", famille: "Dragons — vol et feu",
  nom: "Reconnaissance puis Dracarys", dragon: "suite", echelle: "1/1",
  duree: 300, porte: "plaine nue, hors ville",
  question: "La boucle suit-elle une cible mobile, puis le souffle imprime-t-il au sol la vraie intersection du cône 3D ?",
  quoi: "Syrax porte Rhaenyra autour d’une colonne de 72 hommes, ferme un tour de reconnaissance ; la troupe juge la menace, rompt, puis le dragon poursuit sa courbe et enchaîne ses passages de feu.",
  regarder: "La rupture part de l’arrière avant toute flamme ; le path ne présente aucun saut ; puis la courbe colorée par altitude, les passages successifs et le bord exact de l’empreinte conique restent visibles.",
  manipulation: "Une colonne avance en terrain nu. Le moteur reçoit ce qu’elle voit : une menace hors de portée qui ferme le cercle. Après le tour, Syrax prolonge sa tangente, vire, pique, ressource et recommence sans replacement de position ni de cap.",
  forces: "Syrax et Rhaenyra · 72 hommes en quatre files",
  terrain: "Aucune ville, aucun mur : une terre ferme choisie par le moteur ; la côte visible est aussi infranchissable aux hommes en armure.",
  passe: "La colonne a globalement rompu avant la première flamme ; aucun pas tracé ne révèle de téléportation ; plusieurs attaques naissent de la trajectoire continue ; aucune dose n’est déposée hors du cône-sol.",
});
const EPREUVE_DRAGON_ARMEE = Object.freeze({
  id: "dragon-armee", n: "D2", famille: "Dragons — vol et feu",
  nom: "Tout brûler — dragon contre armée", dragon: "armee", echelle: "1/1",
  duree: 720, porte: "grande plaine, hors ville",
  question: "Comment Syrax choisit-elle une ligne capable d’enchaîner plusieurs masses, saisit-elle une occasion réelle dans son axe, puis élit-elle la suivante sans téléportation ?",
  quoi: "Une armée réelle du moteur est distribuée en six corps séparés. Dès son entrée, sans boucle de reconnaissance, Syrax cherche une bande de 175 m contenant le plus d’hommes encore valides et peu exposés, corrigée par le coût du virage et la répétition des segments déjà traités.",
  regarder: "Le couloir prévu et ses étapes apparaissent avant le feu. Près de son entrée, Syrax freine et établit son cap en vol battu lent au lieu de dessiner de petits cercles. Dans le piqué, une masse rentable entrant réellement dans l’axe déclenche Dracarys sans attendre un point parfait.",
  manipulation: "Six masses manœuvrent sur environ trois cents mètres. Chaque souffle décote tous les segments enchaînés ; le ralliement alterne translation rapide et tenue brève à faible allure, puis les lignes fraîches passent devant les segments déjà traités.",
  forces: "Syrax et Rhaenyra · jusqu’à 216 soldats du moteur en six corps",
  terrain: "Une plaine sèche sans obstacles, choisie par les mêmes règles de sol que la bataille ; aucun soldat en armure n’est posé dans l’eau ni autorisé à y fuir.",
  passe: "Le premier piqué part sans orbite préalable ; plusieurs masses peuvent tomber dans un même passage ; les occasions alignées ne sont pas manquées ; à durée complète l’armée n’est plus une force combattante, sans saut dans le path.",
});
const EPREUVE_VHAGAR_ARMEE = Object.freeze({
  id: "dragon-armee-vhagar", n: "D2b", famille: "Dragons — vol et feu",
  nom: "Tout brûler — Vhagar contre armée", dragon: "armee-vhagar", echelle: "1/1",
  duree: 720, porte: "même grande plaine que D2, hors ville",
  question: "Que gagne Vhagar en portée et en largeur de feu, et que perd-elle en maniabilité et en fréquence de passage ?",
  quoi: "La même armée de six corps affronte Vhagar et Aemond. Le profil simulé porte 42 tonnes sur 82 m d’envergure : les virages, le freinage, le battement, le couloir de sélection et le cône-sol sont tous recalculés.",
  regarder: "La silhouette, l’ombre et le jet deviennent massifs ; l’entrée est plus longue, le lacet plus lent et le vol battu lent reste une tenue lourde, brève, à 6–8 m/s. En contrepartie, un souffle peut enchaîner davantage de masses.",
  manipulation: "Aucune règle des soldats ni aucun placement ne change par rapport à D2. Seul le profil du dragon transforme la cinématique, la portée, la température, le flux et la durée du souffle.",
  forces: "Vhagar et Aemond · jusqu’à 216 soldats du moteur en six corps",
  terrain: "La même plaine sèche et le même masque de sol que D2.",
  passe: "Vhagar reste plus lente à se réaligner que Syrax mais balaie une empreinte sensiblement plus grande ; elle ne se téléporte jamais et l’armée rompt sans courage artificiel.",
});
const EPREUVE_ARRAX_ARMEE = Object.freeze({
  id: "dragon-armee-arrax", n: "D2c", famille: "Dragons — vol et feu",
  nom: "Tout brûler — Arrax contre armée", dragon: "armee-arrax", echelle: "1/1",
  duree: 720, porte: "même grande plaine que D2, hors ville",
  question: "La maniabilité d’Arrax compense-t-elle une empreinte de feu beaucoup plus courte et plus étroite ?",
  quoi: "La même armée affronte Arrax et Lucerys. Le profil simulé porte 2,2 tonnes sur 22 m d’envergure : accélération latérale, fréquence d’aile, vitesse de piqué, rayon de virage et souffle sont adaptés à ce jeune dragon.",
  regarder: "Arrax reprend un cap et enchaîne les passages plus vite, mais doit descendre davantage et viser une bande étroite. Sa trace permet de distinguer un grand nombre de petites occasions d’un balayage réellement destructeur.",
  manipulation: "L’armée, le moteur de fuite, la carte et l’algorithme de choix restent identiques à D2 et D2b ; seules les constantes physiques du dragon changent.",
  forces: "Arrax et Lucerys · jusqu’à 216 soldats du moteur en six corps",
  terrain: "La même plaine sèche et le même masque de sol que D2.",
  passe: "Arrax est nettement plus agile mais son feu touche moins de corps par passage ; les attaques opportunistes restent continues, sans alignement parfait ni téléportation.",
});
const EPREUVE_VHAGAR_VILLE = Object.freeze({
  id:"vhagar-port-real", n:"D3", famille:"Dragons — vol et feu",
  nom:"Tout brûler — Vhagar contre Port-Réal", dragon:"ville-vhagar",
  echelle:"cadastre entier", duree:3600, porte:"Port-Réal entière, état en mémoire",
  question:"Combien de Port-Réal Vhagar peut-elle réellement allumer si chaque foyer doit naître de son cône-sol, puis se propager par le bâti et le vent ?",
  quoi:"Vhagar et Aemond entrent sans tour de reconnaissance. Le dragon relit en continu les secteurs de toits encore combustibles, choisit une bande atteignable, pique, saisit une occasion dans son axe, souffle, ressource et recommence depuis sa position réelle.",
  regarder:"Le path ne saute jamais. Le couloir choisi précède chaque attaque ; l’empreinte orange reste l’intersection exacte du cône 3D avec le sol. Les toits ne changent d’état qu’après dose suffisante ; la fumée dérive ensuite avec le vent et les feux secondaires poursuivent leur propre dynamique.",
  manipulation:"Aucun départ imposé. Vhagar est l’unique source initiale. Chaque toiture reçoit une dose fonction de la température, de la durée d’intersection, du matériau et de ses ouvertures ; F1 reprend ensuite rayonnement, croissance, combustion et brandons.",
  forces:"Vhagar et Aemond · toutes les emprises bâties combustibles du plan courant",
  terrain:"La carte, les survols, le zoom, le déplacement et les contours de bâtiments sont exactement ceux de l’onglet ville et de F1.",
  passe:"Zéro feu avant le premier Dracarys ; plusieurs bandes urbaines distinctes sont attaquées sans téléportation ; les bâtiments hors cône ne reçoivent aucune dose directe ; leur éventuelle ignition ne vient que de la propagation secondaire.",
});
const EPREUVE_DRAGON_RANGEE = Object.freeze({
  id:"dragon-bataille-rangee", n:"D4", famille:"Dragons — vol et feu",
  nom:"C6 avec petit dragon contre armée double", dragon:"rangee-arrax-garde",
  echelle:"1/10", duree:480, porte:"le même terrain cassé et praticable que C6",
  question:"Une armée deux fois moins nombreuse mais soutenue par un dragon bat-elle une ligne double qui conserve tout le système de commandement, de contact et de fuite de C6 ?",
  quoi:"C6 est posé sans réécriture : deux lignes se forment, se voient et avancent vers le même milieu sans tactique initiale. Le petit camp — environ 85 combattants — reçoit Arrax, le plus petit dragon combattant du banc ; l’autre aligne environ 170 hommes et reste sa seule cible stratégique.",
  regarder:"Les deux armées continuent à combattre par le moteur commun pendant qu’Arrax choisit ses bandes, pique et ressource avec sa physique propre. Les ennemis réagissent au dragon par le système de danger et de rupture ; un allié qui traverse réellement le cône peut néanmoins être brûlé.",
  manipulation:"La mise en place, le masque, les formations, les armes combinées et les ordres sont exactement ceux de C6 à l’échelle 1/10. D4 n’ajoute qu’Arrax au petit camp et relie sa sélection aux combattants de la grande armée.",
  forces:"Petit camp : armée C6 + Arrax et Lucerys · grand camp : deux fois ses combattants",
  terrain:"L’emprise choisie dynamiquement par C6 dans le vrai masque, avec ses bâtiments, lignes de vue interrompues et passages latéraux.",
  passe:"Le rapport initial doit rester proche de 1 contre 2 ; les deux lignes se rencontrent réellement ; Arrax ne se téléporte pas, attaque continûment et ne rend pas artificiellement courageuse l’armée opposée. Les pertes alliées éventuelles ne peuvent venir que d’une intersection réelle avec son feu.",
});
const EPREUVE_DRAGON_RANGEE_OUVERTE = Object.freeze({
  id:"dragon-bataille-rangee-ouverte", n:"D4b", famille:"Dragons — vol et feu",
  nom:"D4 avec ordre ouvert anti-dragon", dragon:"rangee-arrax-garde-ouvert",
  echelle:"1/10", duree:480, porte:"le même terrain, les mêmes forces et le même Arrax que D4",
  question:"Une armée instruite à ouvrir ses rangs survit-elle mieux sans devenir artificiellement courageuse ni renoncer à se rallier ?",
  quoi:"D4 est rejoué à l’identique. La grande armée a seulement reçu avant le contact un ordre appris : au dragon, chaque vintaine ouvre ses intervalles, garde ses chefs en vue, puis se rallie après le passage.",
  regarder:"Les anneaux bleus signalent les hommes dont l’ordre tient effectivement les jambes. Les destinations sont irrégulières et stables par combattant. Sidération, dérobade, fuite individuelle et rupture collective restent produites par la pile commune et peuvent interrompre la manœuvre.",
  manipulation:"Le scénario ne choisit aucune réaction et ne déplace aucun homme. Il transmet une doctrine à tout le déploiement par l’API d’ordre de Bataille2d ; le même soldat(), les mêmes quatre couches et le même arbitre décident ensuite de chaque conduite.",
  forces:"Identiques à D4 : petit camp C6 + Arrax et Lucerys · grande armée double, instruite à l’ordre ouvert",
  terrain:"Strictement celui que C6 choisit dans le masque commun, avec le même zoom, le même glissé, les mêmes survols et bâtiments.",
  passe:"La pile de comportements doit être déclarée complète ; toutes les unités de la grande armée reçoivent la doctrine ; les écarts ne forment ni lignes parallèles ni cercle régulier ; une part des hommes doit néanmoins rompre quand le corps ou le jugement collectif reprend la main.",
});
const EPREUVES_DRAGON = [EPREUVE_DRAGON, EPREUVE_DRAGON_ARMEE,
  EPREUVE_VHAGAR_ARMEE, EPREUVE_ARRAX_ARMEE, EPREUVE_VHAGAR_VILLE,
  EPREUVE_DRAGON_RANGEE, EPREUVE_DRAGON_RANGEE_OUVERTE];
const EPREUVE_INCENDIE = Object.freeze({
  id:"incendie-ville", n:"F1", famille:"Feu urbain — propagation",
  nom:"Douze départs simultanés dans Port-Réal", feu:"ville", echelle:"cadastre entier",
  duree:3600, porte:"Port-Réal entière, état en mémoire",
  question:"Des foyers séparés produisent-ils un front continu là où le bâti est serré, tout en respectant les rues, la maçonnerie et les sauts de brandons ?",
  quoi:"Douze bâtiments combustibles, éloignés les uns des autres par une sélection reproductible, prennent feu. Le rayonnement travaille de bord à bord ; le vent incline le danger et les brandons peuvent ouvrir des foyers discontinus sous le vent.",
  regarder:"Les couleurs suivent cinq états du même bâti que la carte : intact, prise, plein embrasement, braises, brûlé. Les traits courbes montrent les brandons ; au survol, le toit conserve sa fiche habituelle et ajoute son matériau inféré, son état et sa dose.",
  manipulation:"Graine fixe 0x129ac · vent d’ouest de 7 m/s vers l’est-sud-est · tissu sec · douze départs · aucune troupe et aucun dragon. Rien n’est écrit dans l’état de partie.",
  forces:"Aucune — seulement le bâti, son contenu et le vent",
  terrain:"Les contours finaux de portreal.plan2d.json : le dessin, la distance d’incendie et le masque partent de la même géométrie.",
  passe:"À courte distance les îlots denses doivent s’embraser ; les voies larges et édifices maçonnés doivent ralentir le front ; des foyers secondaires doivent apparaître sous le vent sans transformer chaque impact en allumage certain.",
});
const EPREUVES_SPECIALES = [EPREUVE_INCENDIE].concat(EPREUVES_DRAGON);
// LE GUET est une famille d'un autre genre, et elle entre par la meme porte que
// les dragons : une liste prependue, pas un second catalogue. Elle ne fait
// tourner aucun moteur — elle lit le monde cuit et le confronte au dossier.
const EPREUVES_GUET = () => (window.BatailleGuet ? window.BatailleGuet.EPREUVES : []);
// LES DEUX ACCESSEURS TOLERENT L'ABSENCE DU MOTEUR, et ce n'est pas de la
// prudence gratuite : `BatailleScenarios` n'arrive qu'avec la chaine de la
// scene, et la chaine peut ne jamais aboutir (mesure faite : « pas de donjon
// ici » pendant une re-cuisson du monde). Sans ces gardes, une famille qui n'a
// besoin d'aucun moteur — le Guet — disparaissait de l'ecran parce qu'un autre
// moteur n'avait pas demarre.
const scenarioParId = (id) => EPREUVES_GUET().find((s) => s.id === id) ||
  EPREUVES_SPECIALES.find((s) => s.id === id) ||
  (window.BatailleScenarios ? window.BatailleScenarios.parId(id) : null);
// Les anciennes mesures « Dynamique du combat » restent dans scenarios.js :
// les bancs headless s'en servent encore comme regressions du moteur. Elles ne
// sont en revanche plus des EPREUVES de la page /bataille. Les retirer ici
// evite de casser leur autorite de test pour resoudre une question de catalogue.
const visiblesDansBataille = (liste) => (liste || [])
  .filter((s) => s.famille !== "Dynamique du combat");
const tousScenarios = () => EPREUVES_GUET().concat(EPREUVES_SPECIALES,
  visiblesDansBataille(window.BatailleScenarios && window.BatailleScenarios.LISTE));

// Un passage tient si AUCUNE sonde n'a répondu faux. Un `null` ne le fait pas
// échouer — mais il ne le fait pas réussir non plus : il reste « à voir ».
function bilan(v) {
  if (!v || !v.length) return "rien";
  if (v.some((x) => x.tenu === false)) return "ko";
  return v.some((x) => x.tenu === null) ? "partiel" : "ok";
}

function batirListe() {
  let famille = null;
  $("liste").innerHTML = tousScenarios().map((s) => {
    const titre = s.famille !== famille
      ? '<div class="famille">' + (famille = s.famille) + "</div>" : "";
    const b = passages[s.id];
    const mot = b === "ok" ? "tenu" : b === "ko" ? "NON" : b === "partiel" ? "partiel" : "—";
    const cl = b === "ok" ? "ok" : b === "ko" ? "ko" : "rien";
    const ouverte = choisie === s.id;
    return titre + '<div class="epreuve' + (ouverte ? " on" : "") + '" data-id="' + s.id + '">' +
      '<button class="ep" type="button" aria-expanded="' + ouverte + '">' +
      '<span class="num">' + s.n + '</span><span class="tt">' + s.nom +
      '</span><span class="etat ' + cl + '">' + mot + '</span><span class="chevron">⌄</span></button>' +
      (ouverte ? '<div class="fiche">' + contenuFiche(s) + '</div>' : '') + '</div>';
  }).join("");
  for (const el of $("liste").querySelectorAll(".epreuve")) {
    el.querySelector(".ep").onclick = () => montrerFiche(el.dataset.id);
    const s = scenarioParId(el.dataset.id);
    const poser = el.querySelector(".poser"), mesurer = el.querySelector(".lancer"),
          recadrer = el.querySelector(".recadrer");
    // UNE EPREUVE QUI N'A PAS BESOIN DU MOTEUR N'ATTEND PAS QU'IL SOIT PRET.
    // `quandPret` avale le clic tant que la chaine n'a pas abouti : pour le
    // Guet, qui ne lit que le monde cuit, c'etait un bouton mort sans un mot.
    const garde = s.guet ? ((fn) => fn) : quandPret;
    if (poser) poser.onclick = garde(() => { urlEtat({ action:"poser" }); poserEpreuve(s.id); });
    if (mesurer) mesurer.onclick = garde(() => { urlEtat({ action:"mesurer" }); lancer(s.id); });
    if (recadrer) recadrer.onclick = quandPret(() => {
      urlEtat({ action:"recadrer" });
      if (s.dragon) cadrerDragon();
      else if (s.feu) cadrerFeu();
      else { cadrer(focusEpreuve(s)); Bataille2d.rafraichir(); }
    });
  }
  const ouverte = $("liste").querySelector(".epreuve.on");
  if (ouverte) requestAnimationFrame(() => ouverte.scrollIntoView({ block:"nearest" }));
}

function contenuFiche(s) {
  return (
    '<h4><span class="num">' + s.n + ".</span> " + s.nom + "</h4>" +
    // Les gestes sont la commande de l'épreuve, pas sa conclusion : ils
    // restent immédiatement sous son nom pendant qu'on lit ensuite le
    // protocole, au lieu d'être enfouis après toutes les conditions.
    '<div class="gestes"><button class="poser" type="button">' +
    (s.feu ? 'Poser les départs et regarder' : 'Poser et regarder') + '</button>' +
    '<button class="lancer" type="button">' +
    (s.feu ? 'Allumer et laisser courir' : 'Mesurer automatiquement') + '</button>' +
    '<button class="recadrer" type="button">Retrouver la scène</button></div>' +
    '<p class="question">' + s.question + "</p>" +
    "<p>" + s.quoi + "</p>" +
    "<dl>" +
      '<dt>Ce qu’il faut regarder</dt><dd class="regarder">' + s.regarder + "</dd>" +
      '<dt>Ce que l’épreuve provoque</dt><dd>' + s.manipulation + "</dd>" +
      "<dt>Forces</dt><dd>" + s.forces + "</dd>" +
      "<dt>Terrain</dt><dd>" + s.terrain + "</dd>" +
      "<dt>Ce qui tranche</dt><dd class=\"passe\">" + s.passe + "</dd>" +
      // On le dit ici parce que la barre ne peut plus le laisser croire :
      // l'épreuve IMPOSE sa condition, sinon elle ne serait pas reproductible.
      "<dt>Conditions de cuisson</dt><dd>échelle <b>" + s.echelle +
        "</b> · <b>" + s.duree + " s</b> de bataille · " +
        (s.porte ? "porte : " + s.porte : "la porte de la Gadoue") +
        "<br><em>l'épreuve impose ces valeurs — les réglages libres de la " +
        "barre sont ignorés pendant qu'elle tourne.</em></dd>" +
    "</dl>");
}

function montrerFiche(id) {
  const s = scenarioParId(id);
  if (!s) return;
  choisie = choisie === id ? null : id;
  urlEtat({ epreuve: choisie, action: null }, true);
  batirListe();
}

function reglerBarreDragon(oui) {
  $("sechelle").disabled = oui;
  // Le dragon partage la caméra de toutes les autres épreuves : son échelle
  // d'effectifs n'a pas de sens, mais le zoom reste un outil de carte.
  $("szoom").disabled = false;
  $("stoponymes").disabled = oui && !dragonVilleActif && !dragonRangeeActif;
  $("shorloge").textContent = oui && window.DragonEpreuve
    ? `${DragonEpreuve.MODELE.nom} · espace 3D` : "—";
}

function entrerDragon(mode, jouer) {
  sortirFeu();
  if (dragonVilleActif) {
    $("toile").classList.remove("feu");
    if (window.IncendieVille) IncendieVille.jouer(false);
  }
  if (marche && !dragonActif) basculerMarche();
  dragonActif = true; dragonMode = mode; dragonVilleActif = mode === "ville-vhagar";
  dragonRangeeActif = mode.startsWith("rangee-");
  if (dragonVilleActif) {
    assurerFeu();
    IncendieVille.remettre({ departs:false });
    IncendieVille.jouer(false);
    DragonEpreuve.lierIncendie(IncendieVille);
    $("toile").classList.add("feu");
  } else DragonEpreuve.lierIncendie(null);
  if (dragonRangeeActif) {
    BatailleScenarios.poser(Bataille2d, "bataille-rangee-naive");
    $("sechelle").value = "0.1";
  }
  urlEtat({ dragon:mode, feu:dragonVilleActif ? "dragon" : null });
  $("toile").classList.add("dragon");
  $("sondes").classList.add("dragon");
  reglerBarreDragon(true);
  DragonEpreuve.choisir(mode);
  $("shorloge").textContent = `${DragonEpreuve.MODELE.nom} · espace 3D`;
  DragonEpreuve.vitesse(vitesse);
  cadrerDragon();
  rendu();
  marche = DragonEpreuve.jouer(!!jouer);
  $("sjouer").textContent = marche ? "⏸ Pause" : "▶ Marche";
  $("sjouer").classList.toggle("on", marche);
}

function sortirDragon() {
  if (!dragonActif) return;
  DragonEpreuve.jouer(false);
  dragonActif = false; marche = false;
  urlEtat({ dragon:null, feu:null });
  $("toile").classList.remove("dragon", "feu");
  if (dragonVilleActif && window.IncendieVille) IncendieVille.jouer(false);
  dragonVilleActif = false; dragonRangeeActif = false; DragonEpreuve.lierIncendie(null);
  $("sondes").classList.remove("dragon");
  reglerBarreDragon(false);
  $("sjouer").textContent = "▶ Marche";
  $("sjouer").classList.remove("on");
}

function assurerFeu() {
  if (feuInstalle) return;
  IncendieVille.installer({ canvas:$("feuCanvas"), stats:$("sondes"), note:$("fnote"), plan:planVille });
  feuInstalle = true;
}

function reglerBarreFeu(oui) {
  $("sechelle").disabled = oui;
  $("szoom").disabled = false;
  $("stoponymes").disabled = false;
  if (oui) $("shorloge").textContent = "incendie urbain · état en mémoire";
}

function entrerFeu(jouer) {
  if (marche && !feuActif && !dragonActif) basculerMarche();
  sortirDragon(); assurerFeu();
  feuActif = true; urlEtat({ feu:"ville", dragon:null });
  $("toile").classList.add("feu"); $("sondes").classList.add("feu");
  reglerBarreFeu(true); IncendieVille.remettre(); IncendieVille.vitesse(vitesse);
  cadrerFeu(); rendu();
  marche = IncendieVille.jouer(!!jouer);
  $("sjouer").textContent = marche ? "⏸ Pause" : "▶ Marche";
  $("sjouer").classList.toggle("on", marche);
}

function sortirFeu() {
  if (!feuActif) return;
  IncendieVille.jouer(false); feuActif = false; marche = false;
  urlEtat({ feu:null }); $("toile").classList.remove("feu");
  $("sondes").classList.remove("feu"); reglerBarreFeu(false);
  $("sjouer").textContent = "▶ Marche"; $("sjouer").classList.remove("on");
}

/** Poser la condition et s'arrêter là — la barre reprend la main. */
// CE QUE LA PAGE PRÊTE AU GUET : sa caméra et sa barre. La surcouche se peint
// dans la MÊME projection que `bataille2d` — donc la molette, le glissé et le
// cadrage sont les siens, sans une ligne de plus. Et l'allure des hommes suit
// ×1/×2/×5 comme le reste : à ×1, un tour de quarante minutes prend quarante
// minutes, ce qui est le fait qu'on veut voir.
const serviceGuet = { vue: () => vue, marche: () => marche, vitesse: () => vitesse };

function poserEpreuve(id) {
  const S = window.BatailleScenarios, s = scenarioParId(id);
  if (!s) return;
  sceneActiveId = id;
  $("toile").classList.toggle("champ-ouvert", !!s.champOuvert);
  modeCarteSeule(false);
  if (s.guet) {
    // POSER = MONTRER, comme partout ailleurs : on installe la ville et les
    // rondes, on ne juge rien. C'est le geste qu'on veut le plus souvent —
    // regarder tourner, et decider soi-meme si ca tient.
    if (!window.BatailleGuet) return;
    sortirDragon(); sortirFeu();
    // LA VILLE SANS BATAILLE : `vider()` retire les hommes et l'ordre de
    // bataille, et laisse le plan. C'est exactement le fond qu'il faut.
    if (pret) { Bataille2d.vider(); cadrerVille(); }
    fetch("/monde/plan2d").then((r) => r.json()).then((plan) => {
      window.BatailleGuet.installer($("toile"), plan, serviceGuet);
      // G2 ouvre deux heures avant la retraite : on vient voir le PIC autant
        // que la pente. G1 part du coup de cloche.
        window.BatailleGuet.remettre(s.foule ? -120 : 0);
      // « Poser » sur G2 charge aussi la ville : c'est ce qu'on vient regarder.
      const suite = s.foule ? window.BatailleGuet.chargerFoule(plan)
                            : Promise.resolve(null);
      suite.then(() => {
        window.BatailleGuet.foule(!!s.foule);
        window.BatailleGuet.montrer(true);
      });
    });
    return;
  }
  if (s.dragon) { entrerDragon(s.dragon, false); return; }
  if (s.feu) { entrerFeu(false); return; }
  sortirDragon();
  sortirFeu();
  if (marche) basculerMarche();
  verdicts = null;                    // on n'a rien jugé : on ne montre rien
  $("sechelle").value = String(s.echelle);
  S.poser(Bataille2d, id);
  cadrer(focusEpreuve(s)); Bataille2d.rafraichir();
}

async function lancer(id) {
  const S = window.BatailleScenarios, s = scenarioParId(id);
  if (!s) return;
  sceneActiveId = id;
  $("toile").classList.toggle("champ-ouvert", !!s.champOuvert);
  modeCarteSeule(false);
  // UNE EPREUVE DU GUET NE FAIT PAS TOURNER LE MOTEUR : elle lit le monde cuit.
  // Elle sort donc avant tout ce qui touche a l'echelle, a la marche et a la
  // camera — il n'y a rien a regarder bouger, et pretendre le contraire
  // remettrait la scene a zero pour rien.
  if (s.guet) {
    if (!window.BatailleGuet) return;
    verdicts = null; sondesScene.remettre();
    const rg = await travail("Epreuve " + s.n + " — " + s.nom,
      () => window.BatailleGuet.jouer(id).then(async (r) => {
        // G2 demande la foule ; G1 la retire. Sans ce va-et-vient, on gardait
        // quatre mille habitants peints par-dessus une épreuve qui ne parle que
        // du Guet — et l'on ne savait plus lequel des deux on regardait.
        window.BatailleGuet.foule(!!r.foule);
        // ON POSE LA VILLE AVANT DE JUGER. Une epreuve se REGARDE : les seize
        // circuits, les hommes qui les parcourent, et le noir autour. Le
        // tableau de verdicts vient par-dessus, il ne remplace pas la vue.
        if (pret) { Bataille2d.vider(); cadrerVille(); }
        window.BatailleGuet.installer($("toile"), r.plan, serviceGuet);
        // G2 ouvre deux heures avant la retraite : on vient voir le PIC autant
        // que la pente. G1 part du coup de cloche.
        window.BatailleGuet.remettre(s.foule ? -120 : 0);
        window.BatailleGuet.montrer(true);
        return r;
      }));
    verdicts = rg.verdicts;
    passages[id] = bilan(rg.verdicts);
    // La famille peint elle-meme : la boucle de `sondes-page.js` est gardee par
    // `pret` et n'ecrira rien tant que le moteur n'est pas dresse.
    window.BatailleGuet.peindre($("sondes"), rg.verdicts,
      "Epreuve " + s.n + " — " + s.nom);
    batirListe();
    return;
  }
  if (s.dragon) { entrerDragon(s.dragon, true); return; }
  if (s.feu) { entrerFeu(true); return; }
  sortirDragon();
  sortirFeu();
  // Et la vue du Guet, qui n'est ni un dragon ni un feu mais qui tourne
  // aussi : une autre famille prend la toile, celle-ci s'efface.
  if (window.BatailleGuet) window.BatailleGuet.montrer(false);
  verdicts = null; sondesScene.remettre();
  $("sechelle").value = String(s.echelle);
  if (marche) basculerMarche();          // une épreuve n'est pas une promenade
  const r = await travail("Épreuve " + s.n + " — " + s.nom,
    () => S.jouer(Bataille2d, id, {
      pas: 30,
      // C'est ici que la page rend la main : une image entre deux bonds, et le
      // loader vit, et l'on voit la bataille avancer au lieu d'un écran figé.
      attendre: async (rel) => {
        // ON RECADRE AU PREMIER RELEVÉ, PAS À LA FIN. Une épreuve peut déplacer
        // sa troupe (la n° 4 la téléporte dans une rue) : la caméra restait
        // alors braquée sur le terrain que les hommes venaient de quitter, et
        // l'on regardait du vide pendant toute la cuisson en se demandant où
        // ils étaient passés. `rel.temps === 0` est le relevé pris JUSTE APRÈS
        // `avant()`, donc le premier instant où la troupe est à sa place.
        if (rel.temps === 0 || s.suivre)
          cadrer(focusEpreuve(s));
        $("chargeur").querySelector(".quoi").textContent =
          "Épreuve " + s.n + " — " + Math.round(rel.temps) + " s sur " + (s.duree || 0);
        Bataille2d.rafraichir();
        await image();
      },
    }));
  verdicts = r.verdicts;
  passages[id] = bilan(r.verdicts);
  batirListe();
  cadrer(focusEpreuve(s)); Bataille2d.rafraichir();
}

function dresser() {
  sortirDragon();
  sortirFeu();
  sondesScene.remettre();
  if (marche) basculerMarche();          // on ne redresse pas sous une boucle qui tourne
  if (sceneActiveId) { poserEpreuve(sceneActiveId); return; }
  // Changer l'échelle ou remettre une carte qui n'a pas encore d'épreuve ne
  // doit plus faire apparaître implicitement la scène pleine.
  Bataille2d.vider();
  Bataille2d.echelle(+$("sechelle").value);
  modeCarteSeule(true);
  cadrerVille(); Bataille2d.rafraichir();
}

function modeCarteSeule(oui) {
  for (const id of ["sjouer","spas1","spas10","spas60"])
    if ($(id)) $(id).disabled=oui;
  if (oui) {
    $("toile").classList.remove("champ-ouvert");
    $("shorloge").textContent="carte seule — choisissez une épreuve";
  }
}

function cadrerVille() {
  // L'emprise régionale peut maintenant couvrir plusieurs lieues. Ouvrir le
  // banc sur elle réduirait Port-Réal à une tache : le cadrage historique de
  // travail reste l'ouverture, puis la molette permet de prendre du recul.
  const b = planVille && planVille.region && planVille.region.cadrage_initial ||
    planVille && planVille.bornes;
  if (!b || b.length < 4) return;
  cadre = [b[0], b[1], b[2] - b[0], b[3] - b[1]];
  vue = null; zoomer();
}

// ON CADRE SUR LES HOMMES, ET NON SUR UN REPÈRE DU PLAN. C'est ce qui rend le
// banc utilisable à toutes les échelles sans réglage : la boîte englobante de
// la troupe dit exactement ce qu'il y a à regarder, et elle est juste que l'on
// dresse cent hommes ou deux mille cinq cents.
function cadrer(selection) {
  const t = selection && selection.length ? selection : Bataille2d.troupe();
  if (!t || !t.length) return;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const h of t) { if (h.x < x0) x0 = h.x; if (h.x > x1) x1 = h.x;
                       if (h.y < y0) y0 = h.y; if (h.y > y1) y1 = h.y; }
  const m = 25;
  cadre = [x0 - m, y0 - m, (x1 - x0) + 2 * m, (y1 - y0) + 2 * m];
  vue = null; zoomer();
}

function cadrerDragon() {
  if (!window.DragonEpreuve) return;
  cadre = DragonEpreuve.cadre();
  vue = null; zoomer();
}

function cadrerFeu() {
  assurerFeu(); cadre = IncendieVille.cadre(); vue = null; zoomer();
}

/** Le zoom pince autour du centre COURANT, pour ne pas défaire un déplacement. */
function zoomer() {
  if (!cadre) return;
  const k = 1 - zoom * 0.9;
  const cx = vue ? vue[0] + vue[2] / 2 : cadre[0] + cadre[2] / 2;
  const cy = vue ? vue[1] + vue[3] / 2 : cadre[1] + cadre[3] / 2;
  vue = [cx - cadre[2] * k / 2, cy - cadre[3] * k / 2, cadre[2] * k, cadre[3] * k];
  rendu();
}

/** L'échelle d'écran du moteur, en pixels CSS par mètre — même calcul que
 *  `repere()` dans `bataille2d.js`, sans le facteur de densité. */
function parMetre(r) { return Math.min(r.width / vue[2], r.height / vue[3]); }

// LA VUE PREND LE FORMAT DU CADRE, SINON ON REGARDE DES BANDES NOIRES.
// Le moteur centre la vue dans son canvas avec `min(L/l, H/h)` — donc dès que
// les deux formats diffèrent, il letterboxe, et le bâti ne remplit pas l'écran.
// On élargit donc la vue sur sa dimension trop courte, autour de son centre :
// le facteur d'échelle devient le même dans les deux sens, la lettre disparaît,
// et l'on ne voit jamais moins que ce qu'on avait demandé — on en voit plus.
function auFormat() {
  const r = $("toile").getBoundingClientRect();
  if (!vue || !r.width || !r.height) return;
  const format = r.width / r.height;
  const cx = vue[0] + vue[2] / 2, cy = vue[1] + vue[3] / 2;
  let l = vue[2], h = vue[3];
  if (l / h < format) l = h * format; else h = l / format;
  vue = [cx - l / 2, cy - h / 2, l, h];
}

const rendu = () => {
  auFormat();
  fond();
  if (pret) Bataille2d.recadrer();
  if (dragonActif) DragonEpreuve.vue(vue);
  if (feuActif || dragonVilleActif) IncendieVille.vue(vue);
};

const fondScene = BatailleFond.creer({
  vue: () => vue,
  pret: () => pret,
  planVille: () => planVille,
  toponymie: () => toponymie,
  infoFeu: (e) => {
    if ((!feuActif && !dragonVilleActif) || !vue) return null;
    const r = $("toile").getBoundingClientRect();
    const rep = CarteProjection.repere(vue, r.width, r.height);
    const p = CarteProjection.depuisPixel(vue, rep,
      e.clientX - r.left, e.clientY - r.top);
    return IncendieVille.inspecter(
      p[0], p[1]);
  },
});
const fond = () => fondScene.dessiner();

const inspectionScene = BatailleInspection.creer({
  vue: () => vue,
  pret: () => pret,
  toponymie: () => toponymie,
  parMetre,
});
const focusEpreuve = (scenario) => inspectionScene.focusEpreuve(scenario);
const installerLoupe = () => inspectionScene.installer();
const survolerScene = (evenement) => {
  const homme = inspectionScene.survoler(evenement);
  fondScene.survoler(evenement, homme);
};

// ═══ LE DÉPLACEMENT — on tire la carte, on ne la pilote pas ════════════════
// On lit la vue AU DÉBUT du geste et l'on s'y réfère jusqu'au relâchement :
// la corriger à chaque battement de souris ferait dériver le déplacement, la
// conversion pixels→mètres dépendant elle-même de la vue.
function tirer() {
  const h = $("toile");
  installerLoupe();
  h.addEventListener("mousemove", survolerScene);
  let tire = null;
  h.addEventListener("mousedown", (e) => {
    if (!pret || !vue || e.button || (e.target.closest && e.target.closest("#sbulle,#smark"))) return;
    tire = { x: e.clientX, y: e.clientY, v: vue.slice() };
    h.classList.add("tire"); e.preventDefault();
  });
  window.addEventListener("mousemove", (e) => {
    if (!tire) return;
    const k = parMetre(h.getBoundingClientRect());
    vue = [tire.v[0] - (e.clientX - tire.x) / k, tire.v[1] + (e.clientY - tire.y) / k,
           tire.v[2], tire.v[3]];
    rendu();
  });
  window.addEventListener("mouseup", () => {
    if (!tire) return; tire = null; h.classList.remove("tire");
  });
  // La molette approche du POINT SOUS LE CURSEUR, et pas du centre : c'est la
  // seule façon d'aller voir un détail sans le perdre en s'en approchant.
  // APPROCHER D'UN POINT DE L'ÉCRAN — la molette et le double-clic font le même
  // geste, à un facteur près. On l'écrit une fois : deux copies de ce calcul
  // dériveraient au premier réglage, et l'une des deux commencerait à viser le
  // centre du cadre au lieu du curseur sans que personne le remarque.
  const approcher = (clientX, clientY, f) => {
    const r = h.getBoundingClientRect();
    const rep = CarteProjection.repere(vue, r.width, r.height);
    const [mx, my] = CarteProjection.depuisPixel(vue, rep,
      clientX - r.left, clientY - r.top);
    vue = [mx - (mx - vue[0]) * f, my - (my - vue[1]) * f, vue[2] * f, vue[3] * f];
    rendu();
  };

  // LE DOUBLE-CLIC APPROCHE DU POINT VISÉ, et l'alt écarte. Un pas franc —
  // ×1,8 — parce qu'un double-clic est une intention nette : on désigne un
  // endroit et l'on veut y aller, pas l'effleurer comme à la molette.
  h.addEventListener("dblclick", (e) => {
    if (!pret || !vue) return;
    e.preventDefault();
    approcher(e.clientX, e.clientY, (e.altKey || e.shiftKey) ? 1.8 : 1 / 1.8);
  });

  h.addEventListener("wheel", (e) => {
    if (!pret || !vue) return;
    e.preventDefault();
    // LE PAS SUIT LE GESTE, IL N'EST PAS FIXE. Un pas constant ne peut pas
    // convenir aux deux : une molette crantée envoie un `deltaY` de 100 par
    // cran, un pavé tactile en envoie vingt petits pour le même mouvement de
    // doigt. À pas fixe, l'un rampe pendant que l'autre traverse la ville.
    // 1,00185^deltaY donne ~20 % pour un cran franc et presque rien pour un
    // frôlement, et les deux se cumulent naturellement. Borné, parce qu'un
    // `deltaY` en mode « page » peut valoir plusieurs centaines d'un coup.
    approcher(e.clientX, e.clientY,
              Math.min(2, Math.max(0.5, Math.pow(1.00185, e.deltaY))));
  }, { passive: false });
}

const sondesScene = BatailleSondes.creer({
  marche: () => marche,
  vitesse: () => vitesse,
  verdicts: () => verdicts,
});
const sonder = () => sondesScene.sonder();

// ---- l'attelage -----------------------------------------------------------
// TROIS VOLETS, et l'un d'eux ne coûte rien : « Un homme » est la page du
// dessous, les deux autres sont des couches posées par-dessus. On les éteint
// toutes avant d'allumer la bonne, pour qu'ajouter un quatrième volet un jour
// n'oblige pas à relire les bascules deux à deux.
const VOLETS = { homme: null, scene: "scene", sources: "sources" };
const BOUTONS = { homme: "ongHomme", scene: "ongScene", sources: "ongSources" };

function onglet(quoi) {
  // L'ancien appel booléen — `onglet(true)` valait « la scène » — vit encore
  // dans les épreuves qui rendent la main. On le traduit ici plutôt que de le
  // traquer partout : un booléen qui traverse et ne casse rien est pire qu'une
  // erreur, il ouvre le mauvais volet en silence.
  if (typeof quoi === "boolean") quoi = quoi ? "scene" : "homme";
  urlEtat({ volet:quoi });
  for (const [nom, id] of Object.entries(VOLETS)) {
    if (id) $(id).classList.toggle("ouvert", nom === quoi);
    $(BOUTONS[nom]).classList.toggle("on", nom === quoi);
  }
  if (quoi === "sources") { BatailleSources.chargerSiBesoin(); return; }
  if (quoi !== "scene") return;
  if (!charge) charge = charger().catch((e) => {
    const a = $("sattente");
    if (a) a.textContent = "La scène n'a pas pu charger : " + e.message +
      " — le serveur sert-il bien /monde ?";
    // On rend la promesse pour qu'un second clic réessaie au lieu de rester muet.
    charge = null; throw e;
  });
}

// ═══ NOTRE PROPRE BOUCLE — c'est elle qui permet ×2 et ×5 ══════════════════
// `Bataille2d.basculer()` lance la boucle DU MOTEUR, et `avancer()` y est
// plafonné à quatre pas de 0,05 s par image : au mieux le temps réel, jamais
// plus. On ne la touche pas — on ne s'en sert simplement pas ici, et la barre
// du moteur est masquée pour qu'il n'y ait qu'un pilote.
//
// `pas(secondes)` ARRONDIT au pas de simulation (`n = round(s / 0,05)`) : lui
// donner un seizième de seconde à chaque image rendrait `n = 0` et la bataille
// ne bougerait jamais. On tient donc une dette et l'on ne dépense que des pas
// entiers — le reliquat passe à l'image suivante.
let marche = false,
    vitesse = Math.max(1, Math.min(5, +(PARAMETRES.get("vitesse") || 1))),
    boucle = 0, dette = 0, dernier = 0;

function battre(ts) {
  if (!marche || !pret) { boucle = 0; return; }
  const dt = Math.min(0.25, (ts - dernier) / 1000);
  dernier = ts;
  dette += dt * vitesse;
  const n = Math.floor(dette / 0.05);
  if (n > 0) { dette -= n * 0.05; Bataille2d.pas(n * 0.05); Bataille2d.rafraichir(); }
  boucle = requestAnimationFrame(battre);
}

function basculerMarche() {
  if (feuActif) {
    marche = IncendieVille.jouer(!IncendieVille.enMarche());
    $("sjouer").textContent = marche ? "⏸ Pause" : "▶ Marche";
    $("sjouer").classList.toggle("on", marche); return;
  }
  if (dragonActif) {
    marche = DragonEpreuve.jouer(!DragonEpreuve.enMarche());
    $("sjouer").textContent = marche ? "⏸ Pause" : "▶ Marche";
    $("sjouer").classList.toggle("on", marche);
    return;
  }
  marche = !marche;
  $("sjouer").textContent = marche ? "⏸ Pause" : "▶ Marche";
  $("sjouer").classList.toggle("on", marche);
  if (marche) { dernier = performance.now(); dette = 0; boucle = requestAnimationFrame(battre); }
  else if (boucle) { cancelAnimationFrame(boucle); boucle = 0; }
}

// ═══ LE LOADER ═════════════════════════════════════════════════════════════
// `Bataille2d.pas()` est SYNCHRONE : sept minutes de bataille tiennent le fil
// d'exécution du début à la fin, sans peindre une image. Le navigateur ne
// montrera donc le loader que si on lui rend la main AVANT de commencer — d'où
// les deux images d'attente, qui ne sont pas une superstition mais la seule
// façon d'obtenir un rendu entre l'affichage et le calcul.
// ⚠ ON NE PARIE PAS SUR `requestAnimationFrame` SEUL. Il ne bat pas dans un
// onglet caché ni dans un volet qui ne compose plus — c'est la bonne politique
// pour une animation, et une impasse pour un calcul : un scénario lancé puis
// mis en arrière-plan resterait suspendu indéfiniment au premier `await`, sans
// rien dire. On court donc les deux et le premier arrivé gagne : l'image quand
// l'écran vit, le délai quand il dort. Même leçon que l'en-tête de `pas()` dans
// `bataille2d.js`, apprise une seconde fois.
const image = () => new Promise((r) => {
  let fini = false;
  const finir = () => { if (!fini) { fini = true; r(); } };
  requestAnimationFrame(finir);
  setTimeout(finir, 60);
});

async function travail(quoi, fn) {
  const c = $("chargeur");
  c.querySelector(".quoi").textContent = quoi;
  c.querySelector(".temps").textContent = "";
  c.classList.add("ouvert");
  const t0 = performance.now();
  // Une horloge qui ne tourne QUE si le calcul rend la main (un scénario le
  // fait, `pas(60)` non). Quand elle reste à zéro, c'est en soi une information.
  const tic = setInterval(() => {
    c.querySelector(".temps").textContent =
      ((performance.now() - t0) / 1000).toFixed(1) + " s";
  }, 100);
  await image(); await image();
  try { return await fn(); }
  finally { clearInterval(tic); c.classList.remove("ouvert"); }
}

// Tout ce qui touche au moteur passe par ce garde : la barre existe dès
// l'ouverture de l'onglet, le moteur seulement quelques secondes plus tard.
const quandPret = (fn) => () => { if (pret) fn(); };

// Quitter la scène ARRÊTE le dragon, dans les deux directions : une épreuve qui
// continue de tourner derrière un volet fermé mange une image sur deux et l'on
// s'en aperçoit en revenant, pas en partant.
const quitterScene = () => {
  if (dragonActif) DragonEpreuve.jouer(false);
  if (feuActif) IncendieVille.jouer(false);
  // Une vue qui continue de tourner derriere un volet ferme mange une image sur
  // deux, et l'on s'en apercoit en revenant — jamais en partant.
  if (window.BatailleGuet) window.BatailleGuet.montrer(false);
};
$("ongHomme").onclick = () => { quitterScene(); onglet("homme"); };
$("ongScene").onclick = () => onglet("scene");
$("ongSources").onclick = () => { quitterScene(); onglet("sources"); };
$("srcrelire").onclick = () => BatailleSources.charger();
$("mEpreuves").onclick = () => ongletMenu(false);
$("mRoster").onclick = () => ongletMenu(true);
$("sjouer").onclick = quandPret(basculerMarche);
// `+60 s` peut coûter plusieurs secondes à pleine échelle : il passe donc par
// le loader comme le reste. `+1 s` aussi, par cohérence — il ne clignote pas,
// il disparaît avant d'avoir été peint.
// ON AVANCE PAR TRANCHES, ET C'EST L'ÉCHELLE PLEINE QUI L'IMPOSE. À 2 550
// corps, dix secondes de bataille coûtent huit secondes de calcul : un `+60 s`
// d'un seul bloc tient le fil pendant près d'une minute, sans une image, et le
// compteur du loader reste à zéro — la page a l'air plantée alors qu'elle
// travaille. On découpe donc en tranches de cinq secondes en rendant la main
// entre chacune : le loader vit, la bataille se peint en avançant, et l'on peut
// voir ce qui se passe au lieu d'attendre le résultat.
const bond = (n) => quandPret(() => {
  if (feuActif) {
    IncendieVille.jouer(false); marche = false; IncendieVille.pas(n);
    $("sjouer").textContent = "▶ Marche"; $("sjouer").classList.remove("on");
    return;
  }
  if (dragonActif) {
    DragonEpreuve.jouer(false); marche = false;
    DragonEpreuve.pas(n);
    $("sjouer").textContent = "▶ Marche"; $("sjouer").classList.remove("on");
    return;
  }
  travail("+" + n + " s de bataille", async () => {
    for (let fait = 0; fait < n; fait += 5) {
      const t = Math.min(5, n - fait);
      Bataille2d.pas(t);
      Bataille2d.rafraichir();
      $("chargeur").querySelector(".quoi").textContent =
        "+" + n + " s de bataille — " + Math.min(n, fait + t) + " s";
      await image();
    }
  });
});
$("spas1").onclick = bond(1);
$("spas10").onclick = bond(10);
$("spas60").onclick = bond(60);
for (const b of document.querySelectorAll("#sbarre .vit"))
  b.onclick = () => {
    vitesse = +b.dataset.vit;
    urlEtat({ vitesse });
    if (window.DragonEpreuve) DragonEpreuve.vitesse(vitesse);
    if (window.IncendieVille) IncendieVille.vitesse(vitesse);
    for (const o of document.querySelectorAll("#sbarre .vit"))
      o.classList.toggle("on", o === b);
  };
$("sremise").onclick = quandPret(() => {
  verdicts = null;
  urlEtat({ action:"remise" });
  if (feuActif) entrerFeu(false);
  else if (dragonActif) entrerDragon(dragonMode, false); else dresser();
});
$("sechelle").onchange = () => {
  urlEtat({ echelle:$("sechelle").value, action:"libre" });
  if (pret) dresser();
};
$("szoom").oninput = (e) => {
  zoom = +e.target.value; urlEtat({ zoom:zoom.toFixed(2) });
  if (pret) zoomer();
};
$("stoponymes").onchange = () => {
  urlEtat({ toponymes:$("stoponymes").checked ? 1 : 0 });
  if (pret) fond();
};
$("smasque").onchange = () => {
  urlEtat({ masque:$("smasque").checked ? 1 : 0 });
  if (pret) fond();
};
window.addEventListener("resize", () => { if (pret) rendu(); });

// LA SCÈNE EST L'ONGLET PAR DÉFAUT. Le banc d'un homme reste à un clic, mais
// ce qu'on vient regarder ici, c'est la bataille : on ouvre dessus, et le
// chargement du moteur commence sans qu'on ait à le demander.
const echelleInitiale = PARAMETRES.get("echelle");
if (echelleInitiale && [...$("sechelle").options].some((o) => o.value === echelleInitiale))
  $("sechelle").value = echelleInitiale;
$("szoom").value = String(zoom);
$("stoponymes").checked = PARAMETRES.get("toponymes") !== "0";
$("smasque").checked = PARAMETRES.get("masque") === "1";
for (const b of document.querySelectorAll("#sbarre .vit"))
  b.classList.toggle("on", +b.dataset.vit === vitesse);
afficherMenu(PARAMETRES.get("menu") === "ferme" ? null
  : PARAMETRES.get("menu") === "roster" ? "roster" : "epreuves");
const voletInitial = ["homme", "scene", "sources"].includes(PARAMETRES.get("volet"))
  ? PARAMETRES.get("volet") : "scene";
// LA LISTE SE BATIT AVANT LE MOTEUR, et `charger()` la rebatira ensuite avec
// les familles qui en dependent. D'ici la, celles qui n'ont besoin de rien —
// le Guet — sont deja lisibles et jouables ; et elles le RESTENT si la chaine
// echoue, ce qui arrive (« pas de donjon ici » pendant une re-cuisson).
batirListe();
onglet(voletInitial);

setInterval(() => {
  if (!pret || !$("scene").classList.contains("ouvert")) return;
  if (dragonActif) {
    const oui = DragonEpreuve.enMarche();
    if (marche !== oui) {
      marche = oui; $("sjouer").textContent = oui ? "⏸ Pause" : "▶ Marche";
      $("sjouer").classList.toggle("on", oui);
    }
  } else if (feuActif) {
    const oui = IncendieVille.enMarche();
    if (marche !== oui) {
      marche = oui; $("sjouer").textContent = oui ? "⏸ Pause" : "▶ Marche";
      $("sjouer").classList.toggle("on", oui);
    }
  } else sonder();
}, 200);
})();
