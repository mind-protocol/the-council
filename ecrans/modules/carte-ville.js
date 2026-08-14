// carte-ville.js — la ville en plan, dessinée, à toute heure.
//
// Ce qu'elle remplace : les trois hauteurs en volume. Le monde 3D est juste et
// il reste servi — mais il ne se voit pas la nuit, et cette partie se joue le
// soir. Or ce qu'on demande à cette échelle est plan, et rien d'autre : où est
// la rue des Sœurs, combien de pas jusqu'à la porte de la Gadoue, par où l'on
// sort quand la maison se referme.
//
// Rien n'est calculé ici. `scripts/monde/plan_ville.py` cuit une fois
// `monde/<x>.plan2d.json` — la côte, huit courbes de niveau, les voies chaînées
// par classe et 48 377 bâtiments en rectangles orientés — et ce module ne fait
// que le poser et le laisser regarder. Deux gestes, les mêmes que le plan du
// château : la molette approche, le glissé déplace. Et un troisième qui n'est
// pas de la carte mais du jeu : le clic est un ORDRE DE MARCHE, on y va.
//
// LE GRAIN SUIT L'APPROCHE, et c'est toute l'astuce d'un plan de 48 000
// maisons : de loin on ne montre que l'eau, le relief, les artères et les
// vingt institutions — de près, tout. Une carte qui affiche ses quarante mille
// toits à pleine page n'est pas une carte, c'est du bruit. Les paliers sont des
// classes sur le SVG ; c'est la feuille de style qui allume les couches, pas
// du JavaScript qui redessine.
"use strict";
window.CarteVille = (() => {
  const HOTE = "ville2d";
  let plan = null;          // le fichier cuit
  let svg = null;
  let vue = null;           // [x, y, l, h] — le viewBox courant, en mètres
  // L'emprise du plan : elle borne le recul de la molette (deux fois) et dit
  // ce qui est « hors du plan » quand on clique dans la marge.
  let base = null;
  // ET LE PLANCHER, QUI EST SON PENDANT : jusqu'où la molette approche, en
  // mètres de large. Deux crans sous les 30 m d'origine (1,18 par cran), parce
  // qu'un homme n'est plus un point depuis qu'il porte un fer à son allonge —
  // voir le pavé de la molette.
  const PLANCHER = 21;
  let source = null;        // la racine du monde servi ("/monde", "/monde/x")
  let moi = null;           // où se tient le joueur, en mètres
  // Le glissé en cours. Il vivait dans `brancher()` ; le survol a besoin de
  // savoir qu'on tire la carte pour se taire pendant ce temps.
  let prise = null;

  const hote = () => document.getElementById(HOTE);
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // ---- quel monde ---------------------------------------------------------
  // Même repli que `ville3d` : le joueur se tient dans un BÂTIMENT, le monde
  // est bâti par VILLE. On demande au serveur ce qu'il offre, et l'on prend
  // celui qui nous contient — puis, faute de mieux, celui par défaut.
  function trouverSource(lieuId) {
    return fetch("/monde/lieux").then((r) => r.json()).then((d) => {
      const l = (d.lieux || []);
      const m = l.find((x) => x.id === lieuId) ||
                l.find((x) => (x.contient || []).indexOf(lieuId) >= 0) ||
                l.find((x) => x.id === d.defaut);
      return m ? m.source : null;
    }).catch(() => null);
  }

  // ---- le dessin ----------------------------------------------------------
  // L'ORDRE DES COUCHES EST LE DESSIN. L'eau dessous, le relief par-dessus,
  // puis les voies, puis le bâti — une maison est bâtie SUR le sol de la rue et
  // le mange, elle ne flotte pas dessous —, puis ce qui se lit : les noms, les
  // repères, et vous. C'est ce recouvrement qui donne à un plan de ville son
  // grain : ce qui reste de chaussée entre deux façades est ce qui reste
  // vraiment, et l'on voit d'un coup d'œil où l'on passe à deux et où l'on
  // passe de biais.
  // LE BÂTI SE COLORE PAR TYPE, PAS PAR FAMILLE. Le plan cuit porte une couche
  // par type — trente-sept à Port-Réal, du taudis au bureau du maître de port —
  // et sa table `types` dit à quelle famille chacun appartient. Chaque couche
  // reçoit donc DEUX classes : `cv-b-<famille>` donne la teinte, `cv-u-<type>`
  // la clarté. Un type qui manque à la feuille de style reste de la couleur de
  // sa famille, ce qui est un défaut acceptable ; une famille inconnue ne peut
  // pas arriver, c'est le même script qui sème et qui cuit.
  // L'ordre vient du fichier (du plus commun au plus rare) : ce qui est écrit
  // en premier est dessiné dessous.
  const bâtiCouches = () => Object.keys((plan && plan.types) || {})
    .filter((u) => (plan.bati || {})[u]);
  const famille = (u) => ((plan.types || {})[u] || {}).cat || "habitat";

  // LE SURVOL DIT CE QUE C'EST. Une couleur sans légende se devine à moitié :
  // on voit bien que ce pâté-là n'est pas de l'habitat, mais on ne sait pas si
  // c'est une tannerie ou une brasserie. Chaque couche porte donc son nom en
  // clair — et comme une couche est UN chemin pour tout un type, ça ne coûte
  // que trente-sept noms pour quarante-cinq mille silhouettes.
  //
  // PLUS DE `<title>`, ET C'EST TOUT LE POINT. L'infobulle du navigateur met
  // près d'une seconde à venir, se pose où elle veut et s'habille du système :
  // sur une carte qu'on parcourt, elle arrive toujours trop tard pour la
  // maison qu'on regardait. Le nom est donc porté en `data-nom` et rendu par
  // `survoler()`, sans délai et à la couleur du bâtiment.
  const coucheBati = (u) => {
    const t = (plan.types || {})[u] || {};
    return '<path class="cv-bati cv-b-' + famille(u) + " cv-u-" + u +
      '" data-nom="' + esc(t.nom || u) + '" d="' + plan.bati[u] + '"/>';
  };
  const VOIES = ["ruelle", "abord", "escalier", "rue", "quai", "artere"];

  // ---- les rues ne sont pas des polygones ---------------------------------
  // Le fichier cuit donne les voies en polylignes : une suite de `L`, chacune
  // un segment droit, et les coudes se voyaient — une ville entière tracée à
  // l'équerre, ce qui n'a l'air ni médiéval ni tracé par des pieds.
  //
  // C'EST LA LARGEUR QUI FAIT LA COURBE, et rien d'autre. Une rue peinte au
  // trait fin garde ses angles ; la même rue peinte à sa largeur réelle, avec
  // des jointures rondes, les perd toutes : la chaussée s'arrondit d'elle-même
  // à chaque coude, comme une vraie. Le SVG le fait tout seul — les voies sont
  // écrites en MÈTRES (`stroke-width` en unités du plan, pas en pixels), avec
  // `stroke-linejoin: round`, et l'on n'a pas une ligne de JavaScript à écrire
  // ni un chemin à recalculer.

  function dessiner() {
    const h = hote();
    if (!h || !plan) return;
    const [x0, y0, x1, y1] = plan.bornes;
    base = [x0, y0, x1 - x0, y1 - y0];
    vue = vue || base.slice();
    const couche = (cl, d, extra) =>
      d ? '<path class="cv-' + cl + '" d="' + d + '"' + (extra || "") + "/>" : "";
    h.innerHTML =
      '<svg id="cv-svg" viewBox="' + vue.join(" ") + '" ' +
      'preserveAspectRatio="xMidYMid meet">' +
      '<rect class="cv-sol" x="' + x0 + '" y="' + y0 + '" width="' + (x1 - x0) +
        '" height="' + (y1 - y0) + '"/>' +
      couche("eau", plan.cote) +
      '<g class="cv-niveaux">' +
        (plan.niveaux || []).map((n) => couche("niveau", n.d)).join("") + "</g>" +
      '<g class="cv-voies">' +
        VOIES.map((g) => couche("voie cv-v-" + g, (plan.voies || {})[g])).join("") + "</g>" +
      '<g class="cv-bati">' + bâtiCouches().map(coucheBati).join("") + "</g>" +
      // L'ENCEINTE PAR-DESSUS LE BÂTI, et c'est voulu. Le rempart est ce qui
      // fait de Port-Réal une ville plutôt qu'un tas de toits : c'est le trait
      // le plus fort du plan, celui qui dit dedans et dehors, et il ne se
      // laisse pas manger par les maisons qui s'y adossent. Il tient à toutes
      // les échelles — de loin il EST la ville, de près il est le mur qu'on
      // longe pour aller à la porte de la Gadoue.
      '<g class="cv-rempart">' +
        couche("courtine", (plan.rempart || {}).courtine) +
        couche("tour", (plan.rempart || {}).tours) + "</g>" +
      // Les enseignes SOUS les noms et les repères : ce sont six cent soixante
      // marques de métier, et elles ne doivent jamais passer devant les sept
      // portes ni le nom d'un quartier, qui sont ce par quoi on se retrouve.
      '<g class="cv-enseignes"></g>' +
      '<g class="cv-noms">' + noms() + "</g>" +
      '<g class="cv-reperes">' + marques() + "</g>" +
      '<g class="cv-route"></g>' +
      '<g class="cv-vous">' + vous() + "</g></svg>";
    svg = h.querySelector("#cv-svg");
    // La bulle vit HORS du SVG : c'est du texte d'interface, il se pose en
    // pixels et non en mètres, et il n'a donc rien à faire dans un dessin qui
    // se cadre. Elle est refaite avec le plan, l'`innerHTML` ci-dessus ayant
    // emporté la précédente.
    bulle = document.createElement("div");
    bulle.className = "cv-bulle";
    bulle.style.display = "none";
    h.appendChild(bulle);
    bulleType = null;
    teintes = {};             // nouveau document, nouveaux styles à lire
    cadreHote = null; cadreSvg = null;
    semerEnseignes();
    grain();
    enseignes();
    brancher();
    // La foule vient PAR-DESSUS, sur sa propre toile : le plan ne bouge pas,
    // elle change à chaque image, et les deux n'ont donc pas à être du même
    // matériau. Elle se repose après chaque redessin sans perdre son heure.
    plein();
    centrer();
    if (window.Foule2d) Foule2d.poser(h, () => vue, { source });
    // Et la bataille par-dessus la foule, sur sa propre toile encore : ce sont
    // trois cents corps qui ne suivent pas l'horloge de la ville mais la
    // seconde réelle. Deux temps, deux couches — on ne les mélange pas.
    if (window.Bataille2d) Bataille2d.poser(h, () => vue, { source });
  }

  // Les noms de quartier : posés au milieu de leurs maisons (le script en fait
  // le barycentre), et dimensionnés par leur POIDS — « La ville » porte 36 000
  // toits, « Le bourg de la Gadoue » cinquante-neuf, et l'œil doit le savoir
  // avant de lire.
  function noms() {
    return (plan.quartiers || []).map((q) => {
      const t = Math.max(34, Math.min(96, 26 * Math.log10(Math.max(10, q.n))));
      return '<text class="cv-quartier" x="' + q.x + '" y="' + q.y +
        '" font-size="' + t.toFixed(0) + '">' + esc(q.nom) + "</text>";
    }).join("");
  }

  // Les repères sont ce qui se cherche vraiment sur ce plan : les sept portes,
  // les quais, les marchés. C'est par eux qu'on se retrouve quand tout le reste
  // est un grain de toits.
  //
  // LE DISQUE ET SON ÉCART SONT PASSÉS À LA FEUILLE DE STYLE, parce qu'écrits
  // ici ils étaient en MÈTRES : un rayon de onze mètres fait neuf pixels quand
  // on voit la ville et soixante-dix quand on est dans la rue. C'était le gros
  // point rouge — un repère qui grossit jusqu'à couvrir le quartier qu'il
  // désigne. Le rayon et l'écart du nom se posent donc en `--mpp` comme tous
  // les traits de ce plan, et gardent une taille APPARENTE constante ; le
  // texte se pose sur le point, la CSS l'écarte.
  function marques() {
    return (plan.reperes || []).map((r) =>
      '<g class="cv-repere cv-r-' + esc(r.genre) + '" data-nom="' + esc(r.nom) + '">' +
      '<title>' + esc(r.nom) + "</title>" +
      '<circle cx="' + r.x + '" cy="' + r.y + '"/>' +
      '<text x="' + r.x + '" y="' + r.y + '">' + esc(r.nom) + "</text></g>"
    ).join("");
  }

  // ---- les enseignes -------------------------------------------------------
  // C'EST LA SEULE COUCHE QUE LE JAVASCRIPT REDESSINE, et c'est assumé. Tout le
  // reste de ce module est posé une fois et allumé par la feuille de style ;
  // ici on ne peut pas. Six mille six cents enseignes en nœuds permanents,
  // c'est un document qu'on ne fait plus bouger — et de toute façon aucune
  // règle CSS ne sait dire « seulement celles qu'on regarde ». On coupe donc au
  // cadre, à chaque `cadrer()` : un balayage de six mille points ne se mesure
  // pas, là où six mille `<text>` se sentent à chaque geste.
  //
  // LE PLAFOND FAIT LE GRAIN, et il vaut mieux qu'un seuil d'échelle. Une
  // fenêtre large tient des milliers de portes ; on n'en garde que RARETÉ
  // D'ABORD — la fosse aux dragons et les deux guildes avant les trois mille
  // échoppes. La couche s'ouvre donc d'elle-même comme le reste du plan : de
  // loin les singularités, de près la rue entière, sans qu'on ait à écrire un
  // palier de plus.
  // LE PLAFOND EST UN COÛT AVANT D'ÊTRE UN GOÛT. Poser deux cent vingt emoji
  // mesuré à 31 ms par cran de molette — un emoji en couleurs se rastérise, ce
  // n'est pas un trait —, sur une carte dont un recadrage nu en coûte déjà 18.
  // À cent quarante on revient sous les vingt, et l'on ne perd rien à l'œil :
  // dans un volet de 700 px, deux cent vingt marques faisaient une marque tous
  // les quarante pixels, ce qui est un semis et plus une enseigne.
  const PLAFOND = 140;      // enseignes affichées d'un coup, au plus
  // AUX FORTES APPROCHES SEULEMENT. Le seuil a d'abord été posé à 2 m/px, le
  // même que la toile des ruelles, et c'était trop tôt : à cette distance on
  // regarde des quartiers, et cent quarante marques de métier étalées sur la
  // moitié de la ville font une couche de bruit par-dessus le plan — le
  // contraire de ce qu'on lui demande. Une enseigne se lit quand on est dans
  // la rue, pas quand on survole le port.
  // 0,3 m/px, soit environ deux cents mètres en travers d'un volet ordinaire :
  // la rue et ses abords, l'échelle à laquelle on cherche la forge. En deçà,
  // le plafond ne mord presque jamais — la couche montre simplement ce qui est
  // devant soi, ce qui est le bon comportement quand on est descendu si près.
  //
  // CE SEUIL EST DEVENU UN PALIER, et c'est la même idée dite deux fois : à
  // partir d'ici on n'est plus sur une carte de la ville, on est DANS une rue.
  // Les enseignes s'allument, et ce qui sert à traverser la ville s'éteint —
  // les noms de quartier et les repères, qui n'ont plus rien à dire quand on
  // voit les portes des maisons. `grain()` en pose la classe `cv-rue`.
  const MPP_RUE = .3;

  let semis = null;         // [{x, y, u}] à plat, cuit une fois
  let posees = null;        // ce qui est écrit dans la couche, pour ne pas le réécrire
  function semerEnseignes() {
    // Le SVG vient d'être refait : la couche est vide, quoi qu'on ait posé
    // dedans tout à l'heure. Oublier ce garde-fou, c'est une carte redessinée
    // qui reste sans enseignes jusqu'au prochain cran de molette.
    posees = null;
    semis = [];
    const e = (plan && plan.enseignes) || {};
    Object.keys(e).forEach((u) => {
      const pts = String(e[u]).split(" ");
      for (let i = 0; i < pts.length; i++) {
        const c = pts[i].split(",");
        if (c.length === 2) semis.push({ x: +c[0], y: +c[1], u: u });
      }
    });
    // Du plus rare au plus commun, UNE FOIS : c'est l'ordre dans lequel on
    // remplit le plafond, et le retrier à chaque cran de molette serait la
    // seule chose coûteuse de la couche.
    const n = (u) => (((plan.types || {})[u] || {}).n) || 0;
    semis.sort((a, b) => n(a.u) - n(b.u));
  }

  function enseignes() {
    const g = svg && svg.querySelector(".cv-enseignes");
    if (!g) return;
    const mpp = metresParPixel();
    const vider = () => { if (posees !== "") { g.innerHTML = ""; posees = ""; } };
    if (!mpp || !semis) return vider();
    if (mpp > MPP_RUE) return vider();
    const x0 = vue[0], y0 = vue[1], x1 = x0 + vue[2], y1 = y0 + vue[3];
    const t = plan.types || {};
    const out = [];
    for (let i = 0; i < semis.length && out.length < PLAFOND; i++) {
      const p = semis[i];
      if (p.x < x0 || p.x > x1 || p.y < y0 || p.y > y1) continue;
      const d = t[p.u] || {};
      if (!d.signe) continue;
      // PAS DE `<title>` ICI NON PLUS, et pour une raison de plus : la couche
      // ne prend pas la souris (`pointer-events:none`), donc il ne se serait
      // jamais montré. Le survol d'une enseigne traverse jusqu'au bâtiment qui
      // est dessous — et comme la marque est posée dans sa silhouette, c'est
      // bien son nom qui sort, par la bulle. Deux cent quatre-vingts nœuds de
      // moins à écrire à chaque recadrage.
      out.push('<text class="cv-enseigne" x="' + p.x + '" y="' + p.y + '">' +
        d.signe + "</text>");
    }
    // Le volet qui s'ouvre, un redessin, un glissé qui ne sort personne du
    // cadre : la couche est souvent la même d'un appel à l'autre. Bâtir la
    // chaîne ne coûte rien, l'écrire coûte tout — on ne l'écrit que si elle a
    // changé.
    const neuf = out.join("");
    if (neuf !== posees) { g.innerHTML = neuf; posees = neuf; }
  }

  // ---- ce qu'on survole ----------------------------------------------------
  // La bulle porte le nom du type À LA COULEUR DU BÂTIMENT, et pas d'un ton
  // approchant : on lit la teinte calculée sur le chemin lui-même
  // (`getComputedStyle`), c'est-à-dire exactement celle que l'œil a sous le
  // curseur, famille et clarté du type comprises. Aucune table à recopier ici,
  // et un type dont on changerait la nuance dans la feuille de style change
  // dans la bulle le jour même.
  //
  // L'ENCRE SE CHOISIT SUR LA LUMINANCE. Les neuf familles sont claires de
  // jour et très sombres de nuit (le beige d'habitat passe de #d9cbb0 à
  // #2e2820) : une bulle qui écrirait toujours en foncé serait illisible une
  // fois sur deux. On mesure donc le fond et l'on pose l'encre en face.
  let bulle = null, bulleType = null;
  // Ce que la bataille éclaire en ce moment. On le garde pour ne rappeler le
  // module que lorsque la sélection CHANGE : un survol traverse des milliers de
  // `pointermove` sur le même homme, et rallumer la même escouade à chacun
  // salirait vingt fois par seconde une carte qui ne bouge pas.
  let soulignait = null;
  // Les deux encres possibles, et leur luminance une fois pour toutes : ce sont
  // le noir et le blanc cassés du plan, pas ceux de l'interface.
  const ENCRE_SOMBRE = .0086;   // #1b1712
  const ENCRE_CLAIRE = .8320;   // #f2ece0

  // CE QUI COÛTE, C'EST DE LIRE APRÈS AVOIR ÉCRIT. Mesuré sur ce document de
  // quarante-cinq mille silhouettes : rester sur la même maison coûte 0,06 ms,
  // sortir du bâti 0,05 — mais changer de type en coûtait ONZE. Deux tiers
  // d'une image à chaque façade traversée : c'est ce qui hachait le survol
  // dans un quartier dense, et c'est exactement ce qu'on voulait supprimer.
  //
  // Deux lectures étaient en cause, et toutes deux tombaient JUSTE APRÈS avoir
  // changé le texte de la bulle — donc au moment précis où la mise en page du
  // document était sale, ce qui force le navigateur à la refaire en entier :
  //
  //   • `getComputedStyle(...).fill` pour la teinte. Or une teinte ne dépend
  //     que du type — deux classes sur un chemin, rien qui bouge d'un survol à
  //     l'autre. On la retient à la première rencontre. La table se vide au
  //     redessin et à la bascule jour/nuit du système, qui est la seule
  //     commande de thème de cette page.
  //   • `offsetWidth`/`offsetHeight` pour retourner la bulle au bord du volet.
  //     Celle-là ne se met pas en cache : elle change avec le mot affiché. On
  //     s'en passe donc — voir `MARGE_BULLE`.
  let teintes = {}, teintesNuit = null;
  // La largeur qu'on suppose à la bulle plutôt que de la mesurer. Le plus long
  // des trente-sept noms (« Chantier à bois et charbon ») tient sous 190 px à
  // cette taille ; on retourne la bulle dès qu'il resterait moins que ça, quitte
  // à la retourner un peu tôt pour un nom court. Personne ne voit qu'elle se
  // retourne trente pixels trop tôt ; tout le monde voit une image sautée.
  const MARGE_BULLE = 190, HAUT_BULLE = 26;
  // Une fiche de bataille fait de trois à six lignes. On majore : ici aussi il
  // vaut mieux la retourner un peu tôt que la laisser sortir du volet, où elle
  // serait rognée juste au moment où l'on veut lire l'ordre qu'un homme porte.
  const HAUT_BULLE_BAT = 108;
  // Et elle est plus large : « Ser Criston Cole · 1re aile   107 debout » passe
  // les deux cents pixels là où un nom de métier en fait cent.
  const MARGE_BULLE_BAT = 260;
  // Le cadre du volet, relu seulement quand il bouge : `getBoundingClientRect`
  // est gratuit sur une mise en page propre et cher sur une mise en page sale,
  // et l'on ne veut pas dépendre de laquelle des deux on a.
  let cadreHote = null;
  // Le cadre du SVG, pour convertir un pixel de souris en mètres du plan sans
  // relire la mise en page à chaque `pointermove`. Il se vide exactement où
  // l'autre se vide.
  let cadreSvg = null;

  // ---- PIXELS → MÈTRES -----------------------------------------------------
  // LA CARTE NE REMPLIT PAS SON VOLET, ET C'EST TOUTE L'IMPRÉCISION DU CLIC.
  // Le SVG porte `preserveAspectRatio="xMidYMid meet"` : le viewBox est mis à
  // l'échelle UNIFORMÉMENT et centré, avec du vide de part et d'autre du côté
  // qui n'est pas contraignant. Or toutes les conversions étaient écrites comme
  // si le dessin était étiré sur les deux axes — `(x - b.left) / b.width *
  // vue[2]` d'un côté, `/ b.height * vue[3]` de l'autre. Les deux échelles
  // diffèrent dès que le cadre du plan et le cadre du volet n'ont pas la même
  // proportion, ce qui est le cas général : `base` est l'emprise de la ville,
  // le volet est ce que le décor lui laisse.
  //
  // Le coût de l'erreur n'est pas cosmétique. Emprise de 5 280 × 3 300 m dans
  // un volet de 528 × 700 px : l'échelle réelle est 0,1 px/m, celle qu'on
  // calculait sur la hauteur en vaut 0,21 — un clic à mi-hauteur tombait à
  // huit cents mètres de l'endroit visé, soit un quartier plus loin. On visait
  // la porte de la Gadoue et l'on partait pour Culpucier.
  //
  // Une seule fonction rend le repère, et TOUT en dépend : le clic-pour-
  // marcher, le zoom vers le pointeur, le glissé, le viseur de la bataille et
  // les seuils de grain. Deux conversions différentes dans la même carte, c'est
  // un survol qui nomme une maison et un clic qui part vers une autre.
  //
  //   k  = pixels par mètre (le même sur les deux axes, c'est le point)
  //   gx = l'abscisse écran du coin haut-gauche du viewBox, marge comprise
  function repere() {
    if (!svg || !vue) return null;
    const b = cadreSvg || (cadreSvg = svg.getBoundingClientRect());
    if (!b.width || !b.height) { cadreSvg = null; return null; }
    const k = Math.min(b.width / vue[2], b.height / vue[3]);
    return { b, k,
             gx: b.left + (b.width - vue[2] * k) / 2,
             gy: b.top + (b.height - vue[3] * k) / 2 };
  }

  /** Le point du plan, en mètres, sous un événement de souris. */
  function enMetres(ev) {
    const r = repere();
    return r ? [vue[0] + (ev.clientX - r.gx) / r.k,
                vue[1] + (ev.clientY - r.gy) / r.k] : null;
  }

  /** Mètres par pixel à l'écran — l'échelle vraie, celle qui s'affiche. */
  function metresParPixel() {
    const r = repere();
    return r ? 1 / r.k : null;
  }
  // ON NE S'ABONNE PAS À LA BASCULE JOUR/NUIT, ON LA CONSTATE. Un écouteur
  // `change` sur `matchMedia` avait l'air propre et ne s'est pas déclenché à
  // l'essai : la table gardait les teintes du jour pendant que le plan passait
  // à la nuit, et la bulle sortait un beige de midi sur une ville noire. Une
  // table de cache qu'un signal peut manquer est une table fausse.
  // On lit donc l'état à chaque changement de type — c'est-à-dire rarement, et
  // `matchMedia` ne coûte ni style ni mise en page —, et l'on vide quand il a
  // tourné. Ça ne peut rien rater, et il n'y a rien à désabonner.
  const nuit = () => !!(window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches);
  // DEUX ÉCRITURES POUR UNE COULEUR, et l'oubli de la seconde inversait toute
  // l'encre. Une teinte simple revient en `rgb(217, 203, 176)`, de 0 à 255 ;
  // mais le bâti est un `color-mix`, et le navigateur rend alors
  // `color(srgb 0.85 0.79 0.69)`, de 0 à 1. Les lire tous deux sur 255 donnait
  // une luminance de deux millièmes pour un beige clair : la bulle écrivait en
  // clair sur du clair, et le seul cas qui compte est justement celui-là.
  const lum = (couleur) => {
    const m = String(couleur).match(/\d*\.?\d+/g);
    if (!m || m.length < 3) return 1;
    const div = /^\s*color\(/.test(couleur) ? 1 : 255;
    const v = m.slice(0, 3).map((s) => {
      const c = +s / div;
      return c <= .03928 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4);
    });
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2];
  };

  // ---- CE QU'ON SURVOLE PENDANT UN ASSAUT ----------------------------------
  // La bataille est peinte sur une toile qui ne prend pas la souris, et il ne
  // faut surtout pas qu'elle la prenne : trois couches empilées qui se
  // disputent le pointeur, c'est une carte qu'on ne peut plus tirer. Le plan
  // garde donc la main et POSE LA QUESTION à `Bataille2d.sous()` — le même
  // geste que `Foule2d` fait déjà avec `derange()`.
  //
  // ELLE PASSE AVANT LA MAISON, et c'est le bon ordre : quand deux mille
  // hommes traversent une rue, ce qu'on montre du doigt est un homme, pas la
  // façade derrière lui. La maison reprend la main dès qu'il n'y a personne.
  const MOTS_ETAT = {
    colonne: "en marche", forme: "en formation", melee: "au corps à corps",
    tient: "tient sa position", deroute: "en déroute", repli: "se replie",
    coureur: "porte un ordre", commande: "commande", pille: "pille",
    blesse: "à terre, vivant", mort: "mort",
  };
  const MOTS_ORDRE = {
    avancer: "avancer", tenir: "tenir", presser: "presser", replier: "se replier",
  };

  function ligneDeBataille(s) {
    const l = [];
    const t = (c) => (c === "assaut" ? "assaut" : c === "garde" ? "défense" : "ville");
    if (s.quoi === "porte") {
      l.push(["<b>" + esc(s.nom) + "</b>", null]);
      l.push([s.etat === "ouvert" ? "enfoncée"
              : Math.round(s.part * 100) + " % de battant", null]);
      if (s.frappeurs) l.push([s.frappeurs + " qui cognent", null]);
      return l;
    }
    if (s.quoi === "figure") {
      l.push(["<b>" + esc(s.nom) + "</b>", null]);
      if (s.role) l.push([esc(s.role), null]);
      l.push(["ne se bat pas", null]);
      return l;
    }
    // Le titre : son nom s'il en a un, son grade sinon. « Un chef d'escouade »
    // est une identité suffisante — c'est même la seule que quatre cent
    // soixante-quinze d'entre eux auront jamais.
    const grade = { roi: "Le roi", tete: "Le chef de corps",
                    capitaine: "Le porte-bannière", chef: "Chef d'escouade",
                    coureur: "Un coureur", homme: null }[s.quoi];
    l.push(["<b>" + esc(s.nom || grade || "Un homme") + "</b>", null]);
    // LE RÔLE PASSE AVANT LE GRADE, quand il y en a un : « roi — s'il tombe,
    // tout s'arrête » dit quelque chose, « le roi » sous le nom du roi ne dit
    // rien du tout. Le grade ne sert qu'à ceux que personne n'a nommés.
    if (s.role) l.push([esc(s.role), null]);
    else if (s.nom && grade) l.push([esc(grade.toLowerCase()), null]);
    // L'ÉTAT, ET AUSSITÔT POURQUOI. « tient » recouvre quatre décisions
    // différentes dans la machine ; sans `branche`, la bulle affiche le même
    // mot pour un homme qui souffle, un qui cède le pas et un qui garde un
    // poste — donc elle n'apprend rien à qui regarde une ligne se défaire.
    l.push([MOTS_ETAT[s.etat] || esc(s.etat), null]);
    if (s.branche) l.push(["<i>" + esc(s.branche) + "</i>", null]);
    // CE QUE SON CORPS DIT, A COTE DE CE QUE SA TETE A DECIDE. Les deux lignes
    // ensemble sont tout l'interet : on lit d'un coup d'oeil quand la couche 1
    // est d'accord avec la cascade et quand elle ne l'est pas — et le jour ou
    // elle prend la main, on voit LEQUEL des deux a conduit.
    if (s.corpsDit)
      l.push([(s.corpsAgi ? "<b>le corps a agi</b> — " : "son corps : ") +
              esc(s.corpsDit),
              s.reflexe != null ? "réflexe " + String(s.reflexe).replace(".", ",") : null]);
    if (s.empriseCorps != null)
      l.push(["emprise du corps " + String(s.empriseCorps).replace(".", ","),
              s.empriseCorps > 0.6 ? "il a la main" : null]);
    // Ce qu'il porte, et jusqu'où ça va. L'allonge est la moitié qui compte :
    // c'est elle qui dit qui, de lui ou de son vis-à-vis, touchera le premier.
    if (s.arme)
      l.push([esc(s.arme), s.allonge ? s.allonge.toFixed(1).replace(".", ",") +
              " m" : null]);
    // CE QU'IL SAIT DE SA PROPRE JOURNÉE : sous quel chef, dans quelle aile,
    // avec quel ordre. C'est mot pour mot ce que le sac promet de retrouver au
    // matin sur un blessé — on ne fait que le lire du vivant.
    if (s.escorte) l.push(["de la garde du roi", null]);
    else if (s.chefDuCorps) {
      // Une tête ne se présente pas comme servant sous elle-même : à sa ligne,
      // son corps n'a plus de nom à donner — il n'a qu'un compte.
      const sous = s.nom === s.chefDuCorps ? "son corps" : esc(s.chefDuCorps);
      const rang = s.aile
        ? " · " + s.aile + "<sup>" + (s.aile === 1 ? "re" : "e") + "</sup> aile" : "";
      l.push([sous + rang, s.vivants ? s.vivants + " debout" : null]);
    }
    if (s.quoi === "coureur" && s.porte)
      l.push(["il porte l'ordre de <b>" + esc(MOTS_ORDRE[s.porte] || s.porte) +
              "</b>", null]);
    else if (s.ordre)
      l.push(["ordre : " + esc(MOTS_ORDRE[s.ordre] || s.ordre) +
              (s.sourde ? " — <i>n'entend plus rien</i>" : ""), null]);
    if (s.banniere === false) l.push(["sa bannière est à terre", null]);
    if (s.camp) l.push([t(s.camp), null]);

    // ---- LA MACHINE, EN CLAIR -------------------------------------------------
    // Les trois entrées de toutes les décisions du fichier — le corps, la tête,
    // le nombre —, plus ce qui le distingue de son voisin. On les met EN
    // DERNIER et dans cet ordre parce que la fiche doit rester lisible pour qui
    // ne débogue pas : le nom, l'état, l'ordre d'abord ; la mécanique ensuite,
    // pour qui descend jusque-là.
    //
    // ON MONTRE LE SEUIL À CÔTÉ DE LA VALEUR, jamais la valeur seule. « morale
    // 0,21 » ne dit rien ; « 0,21 — rompt à 0,15 » dit qu'il tient à six
    // centièmes près, ce qui est exactement ce qu'on cherche à savoir en
    // regardant une aile qui plie.
    const n2 = (v) => v.toFixed(2).replace(".", ",");
    if (s.pv != null)
      l.push([s.entame ? "<b>entamé</b>" : "intact",
              s.pv + " / " + s.pvMax + " pv"]);
    if (s.morale != null)
      l.push(["morale " + n2(s.morale), "rompt à " + n2(s.rompt)]);
    if (s.souffle != null)
      l.push([(s.soufflant ? "<b>il souffle</b> " : "souffle ") + n2(s.souffle),
              s.humeur && s.humeur !== "-" ? esc(s.humeur) : null]);
    if (s.ennemis != null)
      l.push([s.amis + " des siens · " + s.ennemis + " en face",
              s.avantage ? "il a le nombre" : "il ne l'a pas"]);
    if (s.recule != null) l.push(["il cède le pas encore", s.recule + " s"]);
    if (s.patience != null && s.patience > 0)
      l.push(["il patiente encore", n2(s.patience) + " s"]);
    // Les trois déviations, tirées une fois pour toutes : c'est ce qui explique
    // que deux hommes du même rang, même morale et même souffle, ne fassent pas
    // la même chose. `oeil` est rendu à l'endroit — plus il est haut, plus il
    // est vif — parce que la valeur brute du modèle est un facteur de délai et
    // qu'elle se lit à l'envers de son nom.
    if (s.trempe != null)
      l.push(["cœur " + n2(s.trempe) + " · œil " + n2(s.oeil) +
              " · fond " + n2(s.fond), null]);
    return l;
  }

  // ON PLACE AVANT D'ÉCRIRE, et l'ordre est tout : lire le cadre du volet après
  // avoir changé le texte de la bulle, c'est demander au navigateur de refaire
  // la mise en page du plan entier. Ici la lecture tombe pendant que tout est
  // encore propre, et il n'y a plus une seule lecture après.
  //
  // La hauteur est passée par l'appelant : une fiche de bataille fait six
  // lignes là où un nom de maison en fait une, et c'est elle qui décide si la
  // bulle doit passer au-dessus du curseur pour ne pas sortir du volet.
  function placerBulle(ev, haut, marge) {
    const h = cadreHote || (cadreHote = hote().getBoundingClientRect());
    const m = marge || MARGE_BULLE;
    let x = ev.clientX - h.left + 14, y = ev.clientY - h.top + 16;
    if (x + m > h.width) x = Math.max(4, x - m - 26);
    if (y + haut > h.height) y = Math.max(4, y - haut - 26);
    bulle.style.transform = "translate(" + Math.round(x) + "px," +
      Math.round(y) + "px)";
  }

  function survolerBataille(ev) {
    if (!window.Bataille2d || !Bataille2d.sous || !vue || !svg) return null;
    // LE CADRE SE RELIT QUAND IL BOUGE, PAS À CHAQUE MOUVEMENT DE SOURIS. Un
    // `getBoundingClientRect` par `pointermove` est une lecture de mise en page
    // par image — précisément ce que la bulle des maisons prend soin d'éviter
    // trente lignes plus bas. On se range derrière le même cache, qui est déjà
    // vidé par le `ResizeObserver` et par chaque redessin.
    const r = repere();
    if (!r) return null;
    const mpp = 1 / r.k;
    const [x, y] = enMetres(ev);
    // LE RAYON SE COMPTE EN PIXELS, PAS EN MÈTRES. À la ville entière un homme
    // vaut un huitième de pixel : viser au mètre reviendrait à viser un cheveu,
    // et l'on ne toucherait jamais rien. Sept pixels, c'est la pointe du
    // curseur — et c'est vrai à toutes les approches.
    return Bataille2d.sous(x, y, Math.max(1.5, 7 * mpp));
  }

  function survoler(ev) {
    if (!bulle) return;
    // Le glissé prime : on tire la carte, on ne lit pas les maisons.
    const s = prise ? null : survolerBataille(ev);
    // CE QU'ON DÉSIGNE S'ALLUME SUR LA CARTE, pas seulement dans la bulle. La
    // fiche dit à quelle escouade il appartient ; ça, ça le MONTRE — et montre
    // du même coup la hampe sous laquelle il se range, qui est la seule chose
    // du modèle qu'aucun point rouge ne pouvait laisser deviner.
    if (window.Bataille2d && Bataille2d.souligner) {
      const sel = s && s._sel && s._sel.escouade !== null ? s._sel : null;
      if (sel !== soulignait) { soulignait = sel; Bataille2d.souligner(sel); }
    }
    if (s) {
      placerBulle(ev, HAUT_BULLE_BAT, MARGE_BULLE_BAT);
      // LA CLEF DOIT CONTENIR CE QUI BOUGE, sinon la mécanique qu'on vient
      // d'ajouter reste figée sous le curseur : morale et souffle changent à
      // chaque battement, et une bulle qui affiche « morale 0,42 » pendant dix
      // secondes est pire que pas de morale du tout.
      // ON LES QUANTIFIE AU VINGTIÈME plutôt que de les mettre au centième :
      // la valeur affichée garde ses deux décimales, mais la bulle ne se
      // réécrit que lorsqu'elle a bougé assez pour qu'on le voie. C'est le même
      // marché que partout ici — on ne réécrit que ce qui change.
      const cran = (v) => (v == null ? "" : Math.round(v * 20));
      const clef = "bat:" + s.quoi + ":" + (s.nom || "") + ":" + s.etat +
                   ":" + (s.branche || "") +
                   ":" + (s.ordre || "") + ":" + (s.vivants || "") +
                   ":" + (s.corpsDit || "") + ":" + cran(s.empriseCorps) +
                   ":" + s.pv + ":" + cran(s.morale) + ":" + cran(s.souffle) +
                   ":" + s.amis + "/" + s.ennemis;
      if (clef !== bulleType) {
        bulle.classList.add("cv-bulle-bat");
        bulle.style.background = "";
        bulle.style.color = "";
        bulle.innerHTML = ligneDeBataille(s)
          .map(([g, d]) => "<span>" + g + (d ? "<em>" + esc(d) + "</em>" : "") +
                           "</span>").join("");
        bulle.style.display = "block";
        bulleType = clef;
      }
      return;
    }
    const cible = prise ? null :
      (ev.target && ev.target.closest && ev.target.closest("path.cv-bati"));
    if (!cible) {
      if (bulleType !== null) { bulle.style.display = "none"; bulleType = null; }
      return;
    }
    bulle.classList.remove("cv-bulle-bat");
    // ON NE RÉÉCRIT QUE CE QUI CHANGE. Un survol traverse des milliers de
    // pointermove sur la même maison ; recalculer la couleur et réécrire le
    // texte à chacun ferait ramer la seule chose qui devait être instantanée.
    const nom = cible.dataset.nom || "";
    placerBulle(ev, HAUT_BULLE);
    if (nom !== bulleType) {
      const n = nuit();
      if (n !== teintesNuit) { teintes = {}; teintesNuit = n; }
      const fond = teintes[nom] ||
        (teintes[nom] = getComputedStyle(cible).fill);
      // ON NE DEVINE PAS L'ENCRE, ON LA CALCULE. Un seuil posé à vue tranchait
      // mal la moitié brune de la palette — la boulangerie, la voilerie, la
      // corderie sont assez claires pour porter du noir et prenaient du blanc.
      // On compare donc les deux contrastes et l'on garde le meilleur : c'est
      // une ligne de plus et ça ne se trompe sur aucune des trente-sept
      // nuances, ni de jour ni de nuit.
      const L = lum(fond);
      const contraste = (a, b) => (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
      bulle.textContent = nom;
      bulle.style.background = fond;
      bulle.style.color =
        contraste(L, ENCRE_SOMBRE) >= contraste(L, ENCRE_CLAIRE)
          ? "#1b1712" : "#f2ece0";
      bulle.style.display = "block";
      bulleType = nom;
    }
  }

  // « VOUS ÊTES ICI » — et il vaut mieux ne rien montrer que montrer faux.
  // Tant que le lieu du joueur n'a pas d'adresse en mètres (`affecter.py`), on
  // n'invente pas un point : une marque plantée sur l'enceinte du Donjon Rouge
  // pendant qu'on répète au Grenier est pire qu'une carte sans marque.
  // LE POINT FAIT LA TAILLE D'UN HOMME, À TOUTE APPROCHE. Il y avait ici un
  // palier — pastille de 16 m au-delà de 1,2 m/px, homme en deçà —, et un
  // palier sur une taille est toujours un mensonge d'un côté du seuil : on
  // était à 1,3 sur une rue de six mètres, et le joueur voyait une bille de
  // trente-deux mètres de large posée sur trois maisons. Le seuil ne se
  // règle pas, il se supprime : le plan est au 1:1 comme tout le reste du
  // monde, donc le joueur y fait 0,55 m d'épaules et rien d'autre.
  //
  // Ce qui le rend TROUVABLE n'est pas sa taille, c'est le halo — et celui-là
  // se mesure à l'écran, jamais au sol : 26 pixels de rayon, qu'on regarde
  // cinq kilomètres de ville ou six mètres de chaussée. Écrit en mètres
  // puisque le SVG l'est, d'où la multiplication par l'échelle.
  const HOMME_M = 0.275;          // le demi-largeur d'épaules
  const HALO_PX = 26;

  function vous() {
    if (!moi) return "";
    // Une carte cachée n'a pas de largeur : on ne peut alors pas convertir les
    // pixels du halo en mètres. Le point, lui, ne dépend d'aucune mesure — on
    // le pose, et le halo prend un repli plutôt que de disparaître.
    const mpp = metresParPixel();
    const rPoint = HOMME_M;
    const rHalo = mpp !== null ? Math.max(1, HALO_PX * mpp) : 70;
    const dNom = rHalo + 1.2;
    return '<g class="cv-ici cv-ici-pres"><title>Vous êtes ici' +
      (moi.nom ? " — " + esc(moi.nom) : "") + "</title>" +
      '<circle class="cv-ici-halo" cx="' + moi.x + '" cy="' + moi.y +
        '" r="' + rHalo.toFixed(2) + '"/>' +
      '<circle class="cv-ici-point" cx="' + moi.x + '" cy="' + moi.y +
        '" r="' + rPoint.toFixed(2) + '"/>' +
      (moi.nom ? '<text x="' + moi.x + '" y="' + (moi.y - dNom).toFixed(2) + '">' +
        esc(moi.nom) + "</text>" : "") + "</g>";
  }

  // Le marqueur est le seul objet du plan dont la FORME dépend de l'approche —
  // tout le reste ne change que de couleur ou d'épaisseur, ce que la feuille de
  // style fait seule. Il faut donc le redessiner quand on zoome, sans quoi on
  // reste au marqueur de loin après avoir approché.
  function rafraichirVous() {
    const g = svg && svg.querySelector(".cv-vous");
    if (g) g.innerHTML = vous();
    // Le marqueur et le bouton disent la même chose — « on sait où vous êtes »
    // — et doivent donc changer d'avis en même temps. C'est le seul endroit par
    // où passent les deux cas qui font apparaître une adresse : le changement
    // de salle et le recadrage.
    majCentrer();
  }

  // ---- le grain ------------------------------------------------------------
  // Trois paliers, et le seuil se mesure en MÈTRES PAR PIXEL — pas en niveau de
  // zoom, qui ne veut rien dire tant qu'on ne sait pas la taille de la case.
  // Au-delà de 12 m/px une maison fait un demi-pixel : la dessiner, c'est
  // peindre du gris. En deçà de 1,2 m/px les ruelles se séparent et le bâti se
  // lit maison par maison. Entre les deux — c'est-à-dire tout le plein écran,
  // du plus large recul au quartier —, on montre la ville entière.
  function grain() {
    if (!svg || !vue) return;
    // UNE CARTE CACHÉE N'A PAS DE LARGEUR, et deviner la sienne ne donne pas un
    // palier approximatif : ça en donne un FAUX, figé jusqu'au prochain geste.
    // On ne fait rien tant qu'elle n'est pas mesurable ; le ResizeObserver
    // rappelle dès que le décor lui rend de la place.
    const mpp = metresParPixel();
    if (!mpp) return;
    // LE SEUIL ÉTAIT À 4 m/px, ET IL TOMBAIT TROP TÔT. La ville entière tient
    // dans un volet de 700 à 900 px, soit 6 à 7,5 m/px : un cran de molette en
    // arrière depuis la vue courante et tout le bâti s'éteignait — c'est-à-dire
    // exactement quand la carte devient belle. Or ce n'est pas la lisibilité
    // qui commandait ce seuil, c'est une prudence de rendu qui ne se justifie
    // pas : le SVG dessine ses 27 000 silhouettes qu'on les regarde de près ou
    // de loin, la vue n'y change rien.
    //
    // On le repousse donc à 12, choisi pour que RIEN NE S'ÉTEIGNE AU PLEIN
    // ÉCRAN : le dézoom s'arrête à deux fois l'emprise, soit 10 560 m, ce qui
    // fait 11,7 m/px dans un volet de 900 px — juste en deçà. Les toits
    // tiennent donc jusqu'au bout du recul. Au-delà de 12, on n'est plus au
    // plein écran mais dans la vignette du décor (la ville dans 440 px), où
    // une maison mesure un demi-pixel et où la peindre revient à passer du
    // gris : là, et là seulement, le bâti s'efface.
    svg.classList.toggle("cv-loin", mpp > 12);
    svg.classList.toggle("cv-moyen", mpp <= 12 && mpp > 1.2);
    svg.classList.toggle("cv-pres", mpp <= 1.2);
    // LE BÂTI ET LA TOILE DES RUELLES N'ONT PAS LE MÊME SEUIL, et les confondre
    // était la faute : en repoussant l'effacement du bâti de 4 à 12 m/px, on a
    // repoussé du même coup les quatorze mille ruelles, qui se sont mises à
    // baver sur toute la carte — surtout sur le flanc de Rhaenys, où le semis
    // a tracé près de trois mille points de venelles pour PAS UNE maison.
    //
    // Deux choses de nature différente : une maison de loin est un grain de
    // ville, elle fait masse et elle est juste ; une ruelle de loin est un
    // cheveu qu'aucun œil ne suit, et mille cheveux font un voile. La toile
    // fine — venelles, abords, escaliers — s'éteint donc dès 3,5 m/px, là où
    // deux ruelles voisines cessent d'être distinguables, et le bâti tient
    // jusqu'au bout du recul.
    // 3,5 ÉTAIT ENCORE TROP TARD. La vue qui montre les quartiers d'un coup
    // d'œil tourne autour de 3 m/px : elle passait donc juste sous le seuil, et
    // c'est exactement là que la toile est le plus nuisible — quatorze mille
    // venelles à un demi-pixel, plus larges que vraies à cause du plancher,
    // qui font un grillage par-dessus la ville au lieu de la dire.
    //
    // On coupe donc à 2, et surtout ON NE COUPE PLUS D'UN COUP : entre 1,2 et
    // 2 la toile pâlit d'abord. Une couche qui disparaît net d'un cran de
    // molette se remarque ; une couche qui s'efface ne se remarque pas, et
    // c'est tout ce qu'on lui demande.
    svg.classList.toggle("cv-sans-toile", mpp > 2);
    svg.classList.toggle("cv-toile-pale", mpp > 1.2 && mpp <= 2);
    // DANS LA RUE : ce qui sert à traverser la ville s'en va. Les noms de
    // quartier et les repères sont l'appareil d'une carte qu'on lit de haut ;
    // à deux cents mètres de large on lit une rue, et ils ne désignent plus
    // rien qu'on ne voie déjà. C'est le même seuil que les enseignes, qui
    // s'allument à la seconde où ceux-là s'éteignent — l'un remplace l'autre.
    svg.classList.toggle("cv-rue", mpp <= MPP_RUE);
    // Les traits sont écrits en mètres : sans correction ils épaississent en
    // approchant, et une artère finit large comme un quartier. On les tient à
    // une épaisseur APPARENTE constante en les divisant par l'échelle.
    svg.style.setProperty("--mpp", mpp.toFixed(3));
  }

  function cadrer() {
    if (!svg || !vue) return;
    // TROIS DÉCIMALES, PAS UNE. Ce qu'on écrit ici est ce que le navigateur
    // dessine ; `vue` garde sa pleine précision, et arrondir au décimètre à
    // chaque cadrage remettait un écart entre le plan affiché et le plan
    // calculé — un dixième de mètre à la fois, qui se voit au millimètre près
    // quand on zoome vers le pointeur cran après cran. Au millimètre, il n'y a
    // plus rien à rattraper.
    svg.setAttribute("viewBox", vue.map((v) => v.toFixed(3)).join(" "));
    grain();
    enseignes();
    rafraichirVous();
    if (window.Foule2d) Foule2d.recadrer();
    if (window.Bataille2d) Bataille2d.recadrer();
  }

  // ---- la prise ------------------------------------------------------------
  // Exactement les gestes du plan du château : molette pour approcher, glissé
  // pour déplacer. Deux cartes dans le même décor qui ne se prendraient pas de
  // la même main, c'est une carte qu'on n'ouvre plus.
  function brancher() {
    if (!svg || svg.dataset.branche) return;
    svg.dataset.branche = "1";
    svg.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const p = enMetres(ev);
      if (!p) return;
      const [mx, my] = p;
      // On zoome VERS LE POINTEUR : le point sous le doigt ne bouge pas. Un
      // zoom qui recentre sur le milieu fait perdre ce qu'on regardait à
      // chaque cran, et l'on passe son temps à se rattraper.
      const k = ev.deltaY > 0 ? 1.18 : 1 / 1.18;
      // On peut reculer jusqu'à DEUX FOIS l'emprise : la ville tient alors au
      // milieu avec sa marge de champs et de rade autour, ce qui est le bon
      // cadrage pour montrer où l'on va. Au-delà, on regarde du vide.
      //
      // EN AVANT, LE PLANCHER ÉTAIT À 140 M, ET C'EST UNE RUE QU'ON NE PEUT PAS
      // APPROCHER. À 140 m de large, une maison de six mètres fait quarante
      // pixels : on voit le quartier, jamais la porte. Or le bâti est dessiné
      // maison par maison et les venelles sont tracées — il y a quelque chose à
      // regarder de plus près, et le plancher l'interdisait seul.
      // On descend à 30 m, soit la largeur d'une place : la maison prend deux
      // cents pixels, la venelle se traverse à l'œil, et l'on est encore loin
      // de la précision réelle du semis. En deçà on regarderait des traits.
      //
      // PUIS DEUX CRANS DE PLUS, PARCE QU'IL Y A DÉSORMAIS QUELQUE CHOSE À
      // REGARDER À CETTE ÉCHELLE-LÀ. Le plancher de 30 m datait d'un temps où
      // un homme était un point : l'approcher davantage n'aurait montré qu'un
      // carré plus gros. Depuis que chacun porte un fer dessiné à son allonge
      // vraie, la rue à 21 m de large donne l'homme à vingt pixels et sa lance
      // à cent — on voit enfin une haie de pointes se tourner, ce qui est
      // exactement ce que le modèle calcule et qu'on ne pouvait pas voir.
      const l = Math.max(PLANCHER, Math.min(base[2] * 2, vue[2] * k));
      const r = l / vue[2];
      vue = [mx - (mx - vue[0]) * r, my - (my - vue[1]) * r, l, vue[3] * r];
      cadrer();
    }, { passive: false });
    svg.addEventListener("pointerdown", (ev) => {
      // ON RELIT LE CADRE AU MOMENT OÙ L'ON SAISIT, une fois par geste. Le
      // cache ne se vide qu'au redessin et au redimensionnement — or la page
      // DÉFILE, et un cadre gardé depuis avant le défilement place la carte
      // ailleurs qu'elle n'est : le point saisi n'est pas celui qu'on touche.
      // Une lecture de mise en page par saisie ne se sent pas ; par mouvement,
      // si — c'est pour ça qu'elle est ici et pas dans `pointermove`.
      cadreSvg = null;
      const r = repere();
      prise = { x: ev.clientX, y: ev.clientY, v: vue.slice(), bouge: 0,
                k: r ? r.k : 1 };
      svg.setPointerCapture(ev.pointerId);
      svg.classList.add("cv-tire");
    });
    // UN SEUL `pointermove` POUR LES DEUX, et c'est voulu : le survol se sert
    // de la cible que le navigateur a déjà trouvée pour l'événement, sans
    // second passage ni second écouteur. Lire une maison ne coûte donc rien de
    // plus que bouger la souris au-dessus du plan.
    svg.addEventListener("pointermove", (ev) => {
      survoler(ev);
      if (!prise) return;
      prise.bouge = Math.max(prise.bouge,
        Math.abs(ev.clientX - prise.x) + Math.abs(ev.clientY - prise.y));
      // LE PLAN SUIT LE DOIGT AU PIXEL PRÈS : on divise par l'échelle réelle,
      // la même sur les deux axes. Étalé sur la largeur d'un côté et sur la
      // hauteur de l'autre, le dessin glissait plus vite que la main sur un
      // axe et moins vite sur l'autre — on tirait la carte en biais.
      vue = [prise.v[0] - (ev.clientX - prise.x) / prise.k,
             prise.v[1] - (ev.clientY - prise.y) / prise.k,
             prise.v[2], prise.v[3]];
      cadrer();
    });
    // Un glissé qui finit sur la carte n'est pas un clic : sans ce garde-fou,
    // déplacer le plan d'un doigt lancerait une marche vers l'endroit lâché.
    dernierBouge = 0;
    const lacher = () => {
      dernierBouge = prise ? prise.bouge : 0;
      prise = null;
      svg.classList.remove("cv-tire");
    };
    svg.addEventListener("pointerup", lacher);
    svg.addEventListener("pointercancel", lacher);
    // La souris sort du plan : la bulle s'en va avec elle, sinon elle reste
    // collée dans un coin du décor à nommer une maison qu'on ne regarde plus.
    svg.addEventListener("pointerleave", () => {
      if (bulle) { bulle.style.display = "none"; bulleType = null; }
      // La souris sort : ce qu'elle éclairait s'éteint avec elle, sinon une
      // escouade reste allumée sur une carte que plus personne ne survole.
      if (soulignait && window.Bataille2d && Bataille2d.souligner) {
        soulignait = null; Bataille2d.souligner(null);
      }
    });
    // PAS DE DOUBLE-CLIC QUI DÉZOOME. Il y en avait un, qui ramenait la carte
    // au cadrage d'origine, et il était une faute pour deux raisons.
    //
    // La première est qu'un clic sur la carte est un ORDRE DE MARCHE : cliquer
    // deux fois de suite — parce qu'on hésite, parce que le premier clic n'a
    // pas eu l'air de prendre — envoyait donc partir, repartir, puis jetait le
    // cadrage par-dessus le marché. On perdait d'un geste involontaire ce
    // qu'on avait mis dix crans de molette à trouver, au pire moment : quand
    // on est descendu dans une rue pour y regarder quelque chose de près.
    //
    // La seconde est que la parité qu'il invoquait n'existait pas. L'en-tête
    // de ce module promettait « les mêmes gestes que le plan du château » —
    // or le plan du château n'a jamais écouté le double-clic. Le retirer ne
    // rompt donc rien : il rétablit.
    //
    // Et l'on ne perd aucun moyen de reculer : la molette dézoome jusqu'à deux
    // fois l'emprise, c'est-à-dire au-delà du cadrage d'origine.
    // Un repère cliqué se pense, comme un nom en gras du fil : c'est le même
    // canal d'introspection, et il ne coûte pas une minute. Un point de la
    // ville cliqué, lui, est un BUT : on demande le chemin pour y aller.
    svg.addEventListener("click", (ev) => {
      if (bougeAuClic(ev)) return;
      const r = ev.target.closest(".cv-repere");
      if (r && window.Bus && Bus.poster) {
        Bus.poster({ type: "pensee", cible: r.dataset.nom, cible_type: "lieu" });
        return;
      }
      // On ne part pas de nulle part. Sans adresse en mètres, le clic ne
      // faisait RIEN et rien ne le disait — on le dit.
      if (!moi) {
        barre("On ne sait pas d'où vous partez : ce lieu n'a pas d'adresse.");
        return;
      }
      // ON NE PART PAS POUR LA MARGE. Sous « meet », le volet est plus grand
      // que le dessin d'un côté : le vide autour n'est pas de la ville, et un
      // clic qui tombe dedans se serrait jusqu'au bord sans rien dire. On le
      // dit, plutôt que d'envoyer marcher vers un point qui n'a pas été visé.
      const p = enMetres(ev);
      if (!p) return;
      if (p[0] < base[0] - 1 || p[0] > base[0] + base[2] + 1 ||
          p[1] < base[1] - 1 || p[1] > base[1] + base[3] + 1) {
        barre("Il n'y a rien là : vous avez visé hors du plan.");
        return;
      }
      partirVers(p);
    });
    // Le volet qui s'ouvre change les mètres par pixel sans toucher au cadre :
    // le grain ET les enseignes en dépendent, et la couche restait vide tant
    // qu'on n'avait pas fait tourner la molette une fois.
    if (window.ResizeObserver)
      new ResizeObserver(() => { cadreHote = null; cadreSvg = null; grain(); enseignes(); })
        .observe(svg);
  }

  // =========================================================================
  // LA MARCHE — jouer une balade à travers la ville
  //
  // On pose un but d'un clic, le serveur rend l'itinéraire par les rues, et
  // l'on y va. Ce qui compte, et qui n'est pas de la décoration :
  //
  //   • LA VITESSE SORT DU CHEMIN. Le serveur chiffre l'itinéraire en minutes
  //     — une artère se descend plus vite qu'un escalier de Visenya —, et
  //     l'allure de la balade en découle. Le sélecteur ×1…×10 n'accélère pas
  //     le marcheur : il accélère LE JEU. À ×1, une minute de fiction coûte
  //     une minute de vraie vie ; à ×10, six secondes.
  //   • LA MONTRE TOURNE POUR DE BON. Chaque tronçon de vingt mètres est
  //     envoyé au serveur, qui avance l'horloge du siège et celle du monde. On
  //     ne traverse pas Port-Réal gratuitement.
  //   • LE MJ REÇOIT LA TRACE, pas la position. Tous les vingt mètres, ce
  //     qu'on longe — le métier des maisons, le quartier, le repère le plus
  //     proche. C'est de ça qu'une balade se raconte.
  // =========================================================================
  const PAS_M = 20;         // le tronçon qu'on rapporte au MJ, en mètres
  let route = null;         // {points, metres, minutes, vers}
  let avance = 0;           // mètres parcourus depuis le départ
  let rapporte = 0;         // mètres déjà rapportés au MJ
  let vitesse = 3;          // le multiplicateur de la barre
  let enMarche = false;
  let derniereImage = 0;
  let dernierBouge = 0;

  const bougeAuClic = () => dernierBouge > 6;

  // Le point du chemin à `m` mètres du départ, et le nom de la rue qu'on suit.
  function surLeChemin(m) {
    const p = route.points;
    let reste = m;
    for (let i = 1; i < p.length; i++) {
      const d = Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
      if (reste <= d || i === p.length - 1) {
        const t = d ? Math.max(0, Math.min(1, reste / d)) : 1;
        return [p[i - 1][0] + (p[i][0] - p[i - 1][0]) * t,
                p[i - 1][1] + (p[i][1] - p[i - 1][1]) * t];
      }
      reste -= d;
    }
    return p[p.length - 1];
  }

  // Le métier d'un bâtiment, écrit comme le plan l'écrit — `plan.types` porte
  // déjà les trente-sept noms en clair et accentués, et c'est ce que le survol
  // affiche : la barre doit dire le MÊME mot que la bulle, sinon on croit avoir
  // visé autre chose.
  const metierDit = (u) => {
    const n = ((plan && plan.types) || {})[u];
    const s = (n && n.nom) || u || "un bâtiment";
    return s.charAt(0).toLowerCase() + s.slice(1);
  };

  // « près de la porte de Fer », « près du Donjon Rouge » : les repères portent
  // leur article, et « de » collé devant donnait « près de La porte de Fer ».
  const deLieu = (nom) => {
    const s = String(nom || "").trim();
    const m = s.match(/^(les|la|le|l')\s*/i);
    if (!m) return (/^[aeiouyàâéèêîïôöûü]/i.test(s) ? "d'" : "de ") + s;
    const a = m[1].toLowerCase(), reste = s.slice(m[0].length);
    return (a === "le" ? "du " : a === "les" ? "des " :
            a === "la" ? "de la " : "de l'") + reste;
  };

  function partirVers(but) {
    if (!moi) return;
    const q = "?de=" + moi.x + "," + moi.y + "&vers=" + but[0].toFixed(1) + "," +
      but[1].toFixed(1);
    fetch("/chemin" + q).then((r) => r.json()).then((d) => {
      if (!d || !d.chemin) { barre("Aucune rue n'y mène."); return; }
      route = Object.assign({}, d.chemin, { vers: d.vers, but: d.but });
      avance = 0;
      rapporte = 0;
      // ON PART. Le chemin s'affichait et l'on attendait que le joueur presse
      // ▶ : deux gestes pour une seule intention, et le premier ne faisait
      // rien de visible qu'un trait. Un clic sur la ville est un ORDRE DE
      // MARCHE — tu bouges, tu cliques —, et un ordre qui demande à être
      // confirmé n'est pas un ordre, c'est une proposition.
      // Le bouton de la barre ne disparaît pas pour autant : il devient ce
      // qu'il aurait toujours dû être, une PAUSE. On s'arrête quand on veut,
      // on renonce quand on veut, et l'on n'a rien à presser pour avancer.
      enMarche = true;
      derniereImage = 0;
      tracer();
      barre();
      pas();
    }).catch(() => {});
  }

  function tracer() {
    const g = svg && svg.querySelector(".cv-route");
    if (!g) return;
    if (!route) { g.innerHTML = ""; return; }
    const d = "M" + route.points.map((p) => p[0].toFixed(1) + " " + p[1].toFixed(1))
      .join("L");
    const ici = surLeChemin(avance);
    g.innerHTML = '<path class="cv-route-trait" d="' + d + '"/>' +
      '<circle class="cv-route-but" cx="' + route.points[route.points.length - 1][0] +
      '" cy="' + route.points[route.points.length - 1][1] + '" r="14"/>';
    // la marque du joueur suit le pas, sans redessiner la ville
    const v = svg.querySelector(".cv-vous");
    if (v) {
      moi = { x: ici[0], y: ici[1], nom: moi ? moi.nom : null };
      v.innerHTML = vous();
    }
  }

  // ---- le plein écran -------------------------------------------------------
  // Une carte de cinq kilomètres dans un panneau d'un tiers d'écran, c'est une
  // carte qu'on lit à la molette. Ici on prend tout, et l'on rend la place
  // ensuite — c'est le seul bouton du plan qui ne parle pas de la fiction, donc
  // il se fait petit et il se tient dans le coin.
  //
  // LE SVG SE RECADRE TOUT SEUL (`preserveAspectRatio` fait le travail), LES
  // TOILES NON. La foule et la bataille sont des canvas en pixels : sans un
  // recadrage explicite, on passe en plein écran et les habitants restent
  // dessinés à l'ancienne taille, dans le coin, à côté de leurs rues. Et
  // `recadrer` REPEINT, il ne retaille pas seulement — en pause il n'y a pas
  // d'image suivante pour rattraper.
  // ---- SE RETROUVER --------------------------------------------------------
  // La molette zoome VERS LE POINTEUR et le glissé emmène où l'on veut : deux
  // gestes qui font qu'on se perd, et c'est très bien — une carte qu'on ne peut
  // pas quitter des yeux n'est pas une carte. Le double-clic ramenait à la
  // ville entière, ce qui n'est pas se retrouver : c'est renoncer.
  //
  // DEUX CENT QUARANTE MÈTRES, et le chiffre suit ce que la page sait déjà
  // faire. Sous 1,2 m par pixel le marqueur passe au 1:1 — un homme y fait la
  // taille d'un homme, avec son halo qui bat. Dans un volet de 528 px, 240 m
  // font 0,45 : on est donc du bon côté du seuil, on voit ses rues autour de
  // soi, et l'on se reconnaît sans avoir à lire un nom.
  const LARGEUR_CENTRER = 240;

  function centrerSurMoi() {
    if (!vue || !base) return;
    // SANS ADRESSE, ON NE DEVINE PAS — la même règle que le clic-pour-marcher
    // dix lignes plus bas, et pour la même raison : inventer une position,
    // c'est décider que le joueur était quelque part.
    if (!moi) {
      barre("On ne sait pas où vous êtes : ce lieu n'a pas d'adresse.");
      return;
    }
    const l = Math.max(PLANCHER, Math.min(base[2] * 2, LARGEUR_CENTRER));
    // On garde la proportion du volet : la hauteur se déduit, elle ne se
    // choisit pas, sinon le plan se déforme au premier clic.
    const ht = l * (vue[3] / vue[2]);
    vue = [moi.x - l / 2, moi.y - ht / 2, l, ht];
    cadrer();
  }

  /** Le bouton s'éteint quand il n'y a personne à centrer, et il le dit. */
  function majCentrer() {
    const h = hote();
    const b = h && h.querySelector(".cv-centrer");
    if (!b) return;
    b.disabled = !moi;
    b.title = moi ? ("Centrer sur vous" + (moi.nom ? " — " + moi.nom : ""))
                  : "Ce lieu n'a pas d'adresse en mètres";
  }

  function centrer() {
    const h = hote();
    if (!h || h.querySelector(".cv-centrer")) { majCentrer(); return; }
    const b = document.createElement("button");
    b.className = "cv-centrer";
    b.type = "button";
    b.textContent = "◎";
    h.appendChild(b);
    b.addEventListener("click", (ev) => { ev.stopPropagation(); centrerSurMoi(); });
    ["pointerdown", "wheel", "dblclick"].forEach((t) =>
      b.addEventListener(t, (ev) => ev.stopPropagation()));
    majCentrer();
  }

  function plein() {
    const h = hote();
    if (!h) return;
    let b = h.querySelector(".cv-plein");
    if (!b) {
      b = document.createElement("button");
      b.className = "cv-plein";
      b.type = "button";
      h.appendChild(b);
      b.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (document.fullscreenElement) document.exitFullscreen();
        else if (h.requestFullscreen) h.requestFullscreen().catch(() => {});
      });
      ["pointerdown", "wheel", "dblclick"].forEach((t) =>
        b.addEventListener(t, (ev) => ev.stopPropagation()));
      // Le navigateur rend la main par Échap sans passer par notre bouton : on
      // écoute donc l'événement, et pas le clic. Une seule fois pour toute la
      // session — l'hôte, lui, se réécrit à chaque redessin du plan.
      if (!plein.branche) {
        plein.branche = true;
        document.addEventListener("fullscreenchange", () => {
          const p = !!document.fullscreenElement;
          const bb = hote() && hote().querySelector(".cv-plein");
          if (bb) { bb.textContent = p ? "⤡" : "⤢";
                    bb.title = p ? "Rendre la place" : "Prendre tout l'écran"; }
          // TOUT DE SUITE, PUIS DEUX FOIS APRÈS. Le recadrage ne tenait qu'à
          // `requestAnimationFrame` — qui ne bat pas dans un onglet caché, et
          // qu'aucun test ne peut donc éprouver. Un redimensionnement ne se
          // suspend pas à une image : on le fait sur-le-champ, et les deux
          // images suivantes rattrapent les navigateurs qui n'ont pas fini
          // leur mise en page.
          const cale = () => {
            if (window.Foule2d) Foule2d.recadrer();
            if (window.Bataille2d) Bataille2d.recadrer();
          };
          cale();
          requestAnimationFrame(() => { cale(); requestAnimationFrame(cale); });
        });
      }
    }
    const p = document.fullscreenElement === h;
    b.textContent = p ? "⤡" : "⤢";
    b.title = p ? "Rendre la place" : "Prendre tout l'écran";
  }

  // La barre : ce qu'il reste, à quelle allure, et de quoi s'arrêter. Trois
  // boutons, pas douze — c'est une promenade, pas un tableau de bord.
  //
  // ON NE LA RECONSTRUIT PAS À CHAQUE IMAGE, et c'est tout le sujet : elle
  // l'était, et ⏸ comme Renoncer ne répondaient jamais. Un `innerHTML` par
  // image détruit le bouton ENTRE le `pointerdown` et le `click` — le doigt
  // appuie sur un élément qui n'existe plus quand le clic se conclut, donc le
  // clic n'a jamais lieu. Rien n'était cassé dans les gestionnaires : la barre
  // se dérobait sous le doigt soixante fois par seconde.
  //
  // D'où la coupure : `barre()` bâtit une fois des nœuds qui ne bougent plus,
  // `rafraichir()` n'écrit que du texte dedans. Le pas appelle le second.
  // `ton` ne change qu'une couleur : « halte » pour ce qui coupe la marche,
  // rien pour ce qui la refuse. La page ne dit jamais CE qu'on a croisé — le
  // récit est au MJ, et il arrive par le flux.
  function barre(message, ton) {
    const h = hote();
    if (!h) return;
    let b = h.querySelector(".cv-barre");
    if (!b) {
      b = document.createElement("div");
      b.className = "cv-barre";
      b.innerHTML =
        '<button data-cv="aller" class="cv-aller">▶</button>' +
        '<span class="cv-reste"><b></b><i></i><small></small></span>' +
        '<span class="cv-allure"><button data-cv="lent">−</button>' +
        "<b>×3</b><button data-cv=\"vite\">+</button></span>" +
        '<button data-cv="renoncer" class="cv-renoncer">Renoncer</button>' +
        '<span class="cv-dit"></span>';
      h.appendChild(b);
      b.addEventListener("click", (ev) => {
        const t = ev.target.closest("[data-cv]");
        if (!t) return;
        // On persiste la position À CHAQUE FOIS QU'ON S'ARRÊTE — pause,
        // renoncement —, parce que c'est exactement là qu'elle compte : le
        // joueur reste où il s'est arrêté, et c'est de là qu'on lui parlera.
        if (t.dataset.cv === "aller") {
          enMarche = !enMarche; derniereImage = 0;
          if (enMarche) pas(); else poserOu(true);
        }
        if (t.dataset.cv === "renoncer") {
          route = null; enMarche = false; tracer(); poserOu(true);
        }
        if (t.dataset.cv === "vite") vitesse = Math.min(10, vitesse + (vitesse < 3 ? 1 : 2));
        if (t.dataset.cv === "lent") vitesse = Math.max(1, vitesse - (vitesse > 3 ? 2 : 1));
        rafraichir();
      });
    }
    b.querySelector(".cv-dit").textContent = message || "";
    b.classList.toggle("un-mot", !!message);
    // `halte` se pose et se retire avec `un-mot`, jamais séparément : une
    // couleur qui survit à la phrase qu'elle teintait est le même défaut que
    // celui d'en dessous, en plus discret.
    b.classList.toggle("halte", !!message && ton === "halte");
    if (message) { b.classList.add("ouverte"); return; }
    rafraichir();
  }

  function rafraichir() {
    const h = hote();
    const b = h && h.querySelector(".cv-barre");
    if (!b) return;
    if (!route) { b.classList.remove("ouverte", "un-mot", "halte"); return; }
    // ON RÉTABLIT LES BOUTONS. `un-mot` masque tout sauf la phrase — il faut
    // donc le retirer dès qu'il y a de nouveau un chemin, sinon un « aucune
    // rue n'y mène » affiché une fois emportait la barre entière pour le reste
    // de la séance : les boutons étaient là, cachés par une classe qui n'avait
    // plus lieu d'être.
    b.classList.remove("un-mot", "halte");
    b.classList.add("ouverte");
    const reste = Math.max(0, route.metres - avance);
    const min = route.metres ? route.minutes * (reste / route.metres) : 0;
    b.querySelector(".cv-aller").textContent = enMarche ? "⏸" : "▶";
    b.querySelector(".cv-reste b").textContent = Math.round(reste) + " pas";
    // CE QU'ON ANNONCE EST CE QU'ON A VISÉ. On affichait le repère le plus
    // proche du clic — l'un des vingt-cinq de la ville —, donc « La porte de
    // Fer » pour une maison du Culpucier à trois cents mètres de là : le joueur
    // ne pouvait pas savoir où il allait. Quand le serveur a reconnu un
    // bâtiment sous le doigt, c'est LUI le but, avec le repère en second pour
    // situer. Un lieu baptisé en jeu passe avant son métier.
    b.querySelector(".cv-reste i").textContent = route.but
      ? " — " + (route.but.nom || metierDit(route.but.usage)) +
        (route.vers ? ", près " + deLieu(route.vers.nom) : "")
      : route.vers ? " — vers " + deLieu(route.vers.nom) : "";
    b.querySelector(".cv-reste small").textContent =
      (min < 1 ? "moins d'une minute" : Math.round(min) + " minutes") + " de marche";
    b.querySelector(".cv-allure b").textContent = "×" + vitesse;
  }

  // Le pas : une image, un peu de chemin, et tous les vingt mètres un mot au MJ.
  // ---- où je suis ----------------------------------------------------------
  // La marque de la carte EST la vraie position, donc on l'écrit souvent. Pas à
  // chaque image — trois cents écritures par minute pour trois nombres —, mais
  // à la seconde et demie, et TOUJOURS aux moments qui comptent : quand on
  // s'arrête, quand on renonce, quand on arrive. `force` court-circuite le
  // minuteur pour ces trois-là.
  //
  // Cette route n'avance pas la montre et n'écrit aucun pas : les minutes se
  // paient sur `/marche`, au grain du récit. Ici on ne fait que dire où l'on est.
  let dernierOu = 0;
  function poserOu(force) {
    if (!moi) return;
    const t = performance.now();
    if (!force && t - dernierOu < 1500) return;
    dernierOu = t;
    fetch("/ou", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x: moi.x, y: moi.y }) }).catch(() => {});
  }

  function pas(t) {
    if (!enMarche || !route) return;
    const maintenant = t || performance.now();
    if (!derniereImage) derniereImage = maintenant;
    const dt = Math.min(.25, (maintenant - derniereImage) / 1000);   // secondes
    derniereImage = maintenant;
    // mètres par seconde réelle = (mètres / minutes de fiction) × ×N / 60
    const allure = route.minutes > 0 ? route.metres / (route.minutes * 60) : 1.3;
    avance = Math.min(route.metres, avance + allure * vitesse * dt);
    tracer();
    poserOu();                    // à la seconde et demie, sans rien coûter
    if (avance - rapporte >= PAS_M || avance >= route.metres) {
      const fait = avance - rapporte;
      rapporte = avance;
      const p = surLeChemin(avance);
      const fin = avance >= route.metres - .5;
      // QUI EST LÀ SE COMPTE ICI, PAS AU SERVEUR. Les corps sont déjà chargés
      // dans cette page — `foule2d` les place à chaque image — et les
      // recalculer côté serveur voudrait dire y porter `journee.js`, la voirie
      // et quatre méga-octets de cellules pour redire ce qu'on sait déjà. Le
      // marcheur rapporte donc ce qu'il croise, comme il rapporte ses mètres.
      const gens = (window.Foule2d && Foule2d.presents(p[0], p[1])) || null;
      // LA RÉPONSE SE LIT, MAINTENANT. Elle était jetée — un POST qu'on
      // envoyait sans jamais regarder ce qui revenait. Or le serveur sait une
      // chose que la page ignore : si quelque chose s'est levé sur le chemin.
      // Une balade qui traverse un assaut sans s'arrêter est une scène perdue,
      // et c'est le genre de perte qui ne se voit pas.
      fetch("/marche", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x: p[0], y: p[1], metres: fait,
          minutes: route.metres ? route.minutes * (fait / route.metres) : 0,
          gens, fin }) })
        .then((r) => r.ok ? r.json() : null)
        .then((d) => {
          if (!d) return;
          // L'HEURE EST DICTÉE PAR LA CARTE. Marcher fait avancer l'horloge du
          // siège et celle du monde ; le bandeau n'en savait rien, parce qu'il
          // n'écrit l'heure que sur un item du fil. On marchait donc quarante
          // minutes avec le bandeau figé à l'heure du départ, et deux heures
          // différentes sur le même écran. C'est la carte qui tient la montre
          // dans ce mode-là ; le MJ garde le transport, pas l'horloge.
          if (d.date && window.Bus && Bus.heureDeLaCarte)
            Bus.heureDeLaCarte(d.date.minute);
          if (!d.arret || !enMarche) return;
          // ET ON LE DIT DANS LA SECONDE. Les jambes s'arrêtaient et la route
          // s'effaçait SANS UN MOT : le joueur restait devant un plan muet
          // jusqu'à ce que le MJ pousse la scène, ce qui peut prendre une
          // minute — et une minute de silence se lit comme une panne. La barre
          // ne dit que le corps ; ce qu'on a vu appartient au flux, et l'on ne
          // laisse rien filtrer de `croise`, pas même par une couleur.
          enMarche = false; route = null; tracer();
          poserOu(true);          // arrêté net : c'est là qu'on le trouvera
          barre("Quelque chose vous arrête net.", "halte");
        }).catch(() => {});
      if (fin) {
        enMarche = false; route = null; tracer();
        poserOu(true);            // arrivé : on fige où l'on est, au mètre
        barre("Vous y êtes.");
        return;
      }
    }
    rafraichir();
    requestAnimationFrame(pas);
  }

  // ---- où l'on se tient ----------------------------------------------------
  // Les adresses décidées en jeu (`scripts/affecter.py`) disent en mètres où
  // sont les choses de la fiction. Sans elles, pas de marque — voir `vous()`.
  function situer(lieuId, salleId) {
    return fetch(source + "/corps").then((r) => r.ok ? r.json() : null).then((d) => {
      const a = (d && d.affectations) || {};
      // L'HOMME AVANT SA MAISON. Une balade laisse au marcheur une adresse à
      // lui (`personnage:…`, écrite par `/marche` à chaque tronçon) : tant
      // qu'elle est là, elle prime sur celle du bâtiment où il logeait, sinon
      // la marque retournerait au Grenier à chaque relecture.
      const pid = (window.Moi && Moi.personnage_id) || null;
      const p = (pid && a["personnage:" + pid]) ||
                (salleId && (a["salle:" + salleId] || a["lieu:" + salleId])) ||
                (lieuId && a["lieu:" + lieuId]) || null;
      moi = (p && Array.isArray(p.xyz) && p.xyz.length >= 2)
        ? { x: p.xyz[0], y: p.xyz[1], nom: p.nom || null } : null;
    }).catch(() => { moi = null; });
  }

  // ---- l'échelle du décor --------------------------------------------------
  function charger() {
    return fetch("/carte").then((r) => r.json()).then((d) => {
      const lieu = d.joueur_lieu_id || null;
      return trouverSource(lieu).then((s) => {
        if (!s) return;
        source = s;
        return fetch(source + "/plan2d").then((r) => r.ok ? r.json() : null)
          .then((p) => {
            if (!p) return;
            plan = p;
            return situer(lieu, (window.Plan && Plan.salle) ? Plan.salle() : null);
          })
          .then(() => {
            dessiner();
            if (window.Plan && Plan.rebattre) Plan.rebattre();
          });
      });
    }).catch(() => {});
  }

  // LE TRANSPORT DU MJ — arrêter, relancer, accélérer, et rien de plus. Même
  // règle qu'au combat (voir modules/combat.js) : dans ce mode, c'est la carte
  // qui tient l'horloge, et le MJ la conduit sans jamais la poser.
  //
  //     {"type":"horloge","action":"pause"}      il s'arrête où il est
  //     {"type":"horloge","action":"marche"}     il repart
  //     {"type":"horloge","action":"vitesse","vitesse":8}
  //
  // « pause » persiste la position dans la foulée : le joueur reste où on l'a
  // arrêté, et c'est de là qu'on lui parlera.
  if (window.Bus && Bus.enregistrer) {
    Bus.enregistrer("horloge", (it) => {
      if (!route) return;
      if (it.action === "pause") { enMarche = false; poserOu(true); }
      else if (it.action === "marche") {
        if (!enMarche) { enMarche = true; derniereImage = 0; pas(); }
      } else if (it.action === "vitesse") {
        const v = +it.vitesse;
        if (isFinite(v)) vitesse = Math.max(1, Math.min(10, Math.round(v)));
      }
      rafraichir();
    });
  }

  window.addEventListener("DOMContentLoaded", () => {
    charger();
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "ville2d", nom: "La ville", hote: HOTE, ordre: 2,
        dispo: () => !!plan,
        reparu: () => { dessiner(); },
      });
    }
    // La scène change de salle : la marque suit, sans redessiner la ville.
    document.addEventListener("scene-changee", () => {
      if (!plan || !source) return;
      situer(null, (window.Plan && Plan.salle) ? Plan.salle() : null)
        .then(rafraichirVous);
    });
  });

  // `ou` : où se tient le joueur, en mètres. C'est la seule chose que
  // `combat.js` a besoin de savoir, et elle est déjà résolue ici (`situer`) —
  // la lui faire recalculer voudrait dire recopier la chaîne entière du lieu
  // au bâtiment, pour deux nombres qu'on a sous la main.
  return { charger, dessiner, plan: () => plan, ou: () => moi,
           viser: (v) => { vue = v; cadrer(); } };
})();
