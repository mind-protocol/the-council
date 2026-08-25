// capture.js — ce que le joueur a sous les yeux, envoyé au MJ.
//
// LE MJ EST AVEUGLE PENDANT UNE BATAILLE, et c'est le seul moment où ça compte
// vraiment. Il lit l'état, il lit les annales du sac — mais une bataille se
// comprend d'un coup d'œil et se raconte mal : où la ligne a cédé, de quel
// côté la panique court, quelle rue est vide et laquelle bouchonne, à quelle
// distance de la porte est l'homme qu'on lui demande de jouer. Trois cents
// lignes de JSONL ne rendent pas ça ; une image, oui.
//
// On lui envoie donc, à intervalle régulier tant que la bataille est dressée,
// une vue composée de la carte CENTRÉE SUR LE JOUEUR. Elle atterrit dans
// `etat/vues/<siège>.png`, à un chemin STABLE qu'il ouvre quand il en a besoin.
//
// ET SON GUETTEUR SONNE. Le serveur dépose, en même temps que l'image, une
// entrée dans `etat/inbox/<siège>/` qui en porte le CHEMIN — jamais l'image
// elle-même, qui rendrait l'inbox illisible. Sans ce mot, le miroir serait
// posé sur une table que personne ne regarde : le MJ n'a aucune raison
// d'ouvrir un fichier dont rien ne lui dit qu'il vient de changer.
//
// C'est donc `CADENCE` qui règle la fréquence à laquelle on le dérange, et
// c'est ici qu'il faut l'espacer si vingt secondes se révèlent trop courtes.
// Deux choses amortissent : le MJ lit tous ses fichiers d'inbox d'un bloc, et
// le PNG est toujours le même fichier écrasé — plusieurs pings accumulés
// pendant qu'il écrivait ne valent que par le dernier.
//
// ---------------------------------------------------------------------------
// COMMENT ON COMPOSE, ET POURQUOI PAS AUTREMENT
//
// Le décor est en TROIS couches qui ne sont pas du même matériau : le plan est
// un SVG, la foule et la bataille sont deux `<canvas>` posés par-dessus. Rien
// dans le navigateur ne sait photographier ça d'un geste — il faut rastériser
// le SVG soi-même, puis empiler les deux toiles dessus.
//
// LE PIÈGE EST LE STYLE. Un SVG sérialisé sort NU : ses classes (`cv-bati`,
// `cv-b-artisanat`, `cv-v-artere`…) vivent dans `jeu.css`, et une image
// autonome ne connaît pas la feuille de style de la page qui l'a produite. Un
// clone sérialisé tel quel donne une planche de silhouettes noires sur fond
// blanc — techniquement une capture, et rigoureusement illisible. On injecte
// donc dans le clone les règles qui le concernent ET les variables de couleur
// résolues sur la racine, ce qui fait suivre le thème du jour ou de la nuit
// sans avoir à le savoir.
//
// ON DÉPLACE LE CADRAGE, ON NE DÉCOUPE PAS L'IMAGE — et c'est la seule chose
// qui marche. Découper la vue à l'écran autour du joueur paraissait propre et
// gratuit : c'est de l'arithmétique de pixels, aucun module à toucher. Mais
// recadrer ne crée pas de résolution. Mesuré : joueur au milieu, carte à
// l'échelle de la ville, 8,5 m par pixel — la fenêtre de 260 mètres fait
// TRENTE ET UN PIXELS DE CÔTÉ. Or c'est exactement le cas ordinaire, puisqu'un
// joueur qui suit une bataille regarde la bataille et pas ses propres pieds.
//
// On demande donc à la carte de se cadrer sur le joueur le temps d'une
// photographie. `CarteVille.viser()` repose le cadrage, et `cadrer()` repeint
// la foule et le fer dans la foulée — les trois couches sont alors d'accord,
// à pleine résolution, sans qu'aucune n'ait eu à apprendre un second métier.
//
// ET LE JOUEUR NE VOIT RIEN, parce que tout se fait dans UN SEUL TOUR
// synchrone : on vise, on prend les deux toiles au vol, on remet le cadrage
// d'avant. Le navigateur ne peint qu'entre deux tours — il n'a donc jamais
// l'occasion d'afficher le cadrage intermédiaire. C'est le même principe
// qu'une mesure de mise en page : ce qui compte n'est pas ce qu'on fait, c'est
// de ne pas rendre la main au milieu.
//
// UNE SEULE CHOSE RESTE HORS DE PORTÉE, et on la dit au lieu de la maquiller :
// le nuage de la foule est trié au cadrage où il a été CALCULÉ. Viser plus
// SERRÉ ne coûte rien (on avait déjà tous ces gens-là) ; viser plus LARGE que
// ce que le joueur regarde donnerait une couronne vide, faute de les avoir
// calculés. Quand la fenêtre demandée est plus large que la vue courante, on
// garde donc la vue courante et la légende le dit.
"use strict";
window.Capture = (() => {
  const CADENCE = 30000;      // ms entre deux vues, tant que la bataille tient
  const FENETRE = 260;        // mètres de côté autour du joueur, quand on peut
  const LARGE_MAX = 760;      // px — au-delà on n'apprend plus rien et ça pèse

  // LE FORMAT EST MESURÉ, PAS CHOISI. Sur une vue de 760 pixels de large, sur
  // ce plan-ci : PNG 79 Ko, JPEG à 0,85 17 Ko, WebP à 0,85 DIX. Le WebP gagne
  // d'un facteur huit sur le PNG et de quatre sur le JPEG, et sur un dessin au
  // trait il ne bave pas autour des lettres comme le JPEG le fait.
  // On garde une descente : un navigateur qui ne sait pas encoder un format
  // rend du PNG sans prévenir (`toDataURL` retombe en silence), donc on regarde
  // ce qu'on a REÇU et non ce qu'on a demandé.
  const FORMATS = [["image/webp", .85], ["image/jpeg", .85], ["image/png", undefined]];

  // ---- le style du plan ----------------------------------------------------
  // Les variables d'abord : elles portent tout le nuancier du plan et changent
  // avec le thème. On les lit RÉSOLUES sur la racine, donc telles que l'œil du
  // joueur les a en ce moment.
  const VARIABLES = ["--cv-sol", "--cv-sol-intra", "--cv-eau", "--cv-eau-trait", "--cv-niveau",
    "--cv-bati", "--cv-bati-trait", "--cv-lum", "--cv-nuit", "--cv-mur",
    "--cv-mur-tour", "--ink", "--muted", "--accent", "--braise", "--or-joueur"];

  let regles = null;          // la CSS du plan, ramassée une fois
  function styleDuPlan() {
    if (regles !== null) return regles;
    const bouts = [];
    for (const f of document.styleSheets) {
      let rs;
      try { rs = f.cssRules; } catch (e) { continue; }   // feuille d'un autre hôte
      for (const r of rs) ramasser(r, bouts);
    }
    regles = bouts.join("\n");
    return regles;
  }
  // Les media queries comptent : c'est là que vit la moitié nuit du nuancier.
  // On les recopie telles quelles — le rastériseur est le MÊME navigateur, il
  // les évaluera comme la page.
  function ramasser(r, bouts) {
    if (r.cssRules && r.conditionText !== undefined) {
      const dedans = [];
      for (const s of r.cssRules) ramasser(s, dedans);
      if (dedans.length)
        bouts.push("@media " + r.conditionText + "{" + dedans.join("\n") + "}");
      return;
    }
    if (r.selectorText && /\.cv-/.test(r.selectorText)) bouts.push(r.cssText);
  }

  function entete() {
    const rac = getComputedStyle(document.documentElement);
    const vars = VARIABLES
      .map((v) => [v, rac.getPropertyValue(v).trim()])
      .filter(([, val]) => val)          // une variable absente ne se recopie pas
      .map(([v, val]) => v + ":" + val + ";").join("");
    // `font-family:inherit` n'hérite de rien dans une image autonome : sans
    // fonte nommée, les noms de quartier sortent en serif du système et la
    // planche ne ressemble plus à la page.
    const fonte = getComputedStyle(document.body).fontFamily ||
      "system-ui, sans-serif";
    return "<style>:root{" + vars + "}text{font-family:" +
      fonte.replace(/"/g, "'") + ";}" + styleDuPlan() + "</style>";
  }

  // ---- où est le joueur ----------------------------------------------------
  // On le lit sur le dessin plutôt que dans `CarteVille` : la marque « vous
  // êtes ici » n'est posée QUE lorsqu'on a une adresse en mètres sûre (voir
  // `vous()`), donc sa présence est déjà la bonne condition. Pas de marque, pas
  // de centrage — et on le dit.
  function joueur(svg) {
    const p = svg.querySelector(".cv-ici-point");
    if (!p) return null;
    return { x: +p.getAttribute("cx"), y: +p.getAttribute("cy") };
  }

  // Le même repère que `foule2d` : `preserveAspectRatio="xMidYMid meet"` centre
  // le cadrage et laisse des marges. Reproduit ici en pixels CSS.
  function repere(svg, boite) {
    const vb = (svg.getAttribute("viewBox") || "").split(/[ ,]+/).map(Number);
    if (vb.length !== 4 || !boite.width) return null;
    const k = Math.min(boite.width / vb[2], boite.height / vb[3]);
    return { k, vb,
             ox: (boite.width - vb[2] * k) / 2 - vb[0] * k,
             oy: (boite.height - vb[3] * k) / 2 - vb[1] * k };
  }

  // ---- composer ------------------------------------------------------------
  async function composer(opts) {
    const o = opts || {};
    const svg = document.querySelector("#cv-svg");
    const hote = document.getElementById("ville2d");
    if (!svg || !hote) throw new Error("le plan de la ville n'est pas ouvert");
    const boite = hote.getBoundingClientRect();
    if (!boite.width || !boite.height) throw new Error("le plan n'a pas de taille");

    // ---- LE TOUR SYNCHRONE : viser, saisir, remettre -----------------------
    // Rien ici ne doit `await`. Le navigateur ne peint qu'entre deux tours de
    // boucle : tant qu'on ne lui rend pas la main, le cadrage de photographie
    // n'existe que dans le document et jamais à l'écran. Une seule promesse
    // glissée au milieu, et le joueur voit la carte sauter.
    const avant = (svg.getAttribute("viewBox") || "").split(/[ ,]+/).map(Number);
    const moi = joueur(svg);
    const demande = o.centre && isFinite(+o.centre.x) && isFinite(+o.centre.y)
      ? { x: +o.centre.x, y: +o.centre.y, id: o.centre.id || null,
          nom: o.centre.nom || null } : null;
    const point = demande || moi;
    const span = o.fenetre || FENETRE;
    let vise = null, centre;
    if (!window.CarteVille || !CarteVille.viser) {
      centre = "la vue courante — la carte ne sait pas se viser";
    } else if (!point) {
      centre = "la vue courante — aucun centre n'est connu au mètre";
    } else if (span >= avant[2] || span >= avant[3]) {
      // Plus large que ce que le joueur regarde : la foule n'a pas été calculée
      // là-bas, on ferait une couronne vide. On garde sa vue.
      centre = demande ? "le combattant marqué, dans la vue courante déjà plus serrée"
                       : "la vue du joueur — plus serrée que la fenêtre demandée";
    } else {
      // La fenêtre prend la FORME du volet, sinon `xMidYMid meet` la recentre
      // en laissant des marges et l'on photographie du vide sur deux bords.
      const h = span * boite.height / boite.width;
      vise = [point.x - span / 2, point.y - h / 2, span, h];
      centre = demande ? "le combattant marqué, " + Math.round(span) + " m de large"
                       : "le joueur, " + Math.round(span) + " m de large";
    }

    const prises = [];
    const couches = [];
    if (vise) CarteVille.viser(vise);
    for (const sel of [".cv-foule", ".cv-bataille"]) {
      const c = hote.querySelector(sel);
      if (c && c.width && c.height) { prises.push(c); couches.push(sel.slice(4)); }
    }
    // Les toiles sont RECOPIÉES tout de suite : elles vont être repeintes au
    // cadrage d'avant dès la ligne suivante, et une référence ne garde rien.
    const gelees = prises.map((c) => {
      const g = document.createElement("canvas");
      g.width = c.width; g.height = c.height;
      g.getContext("2d").drawImage(c, 0, 0);
      return g;
    });
    // Le plan, lui, se cloneEND pendant qu'il porte le bon cadrage : le clone
    // emporte ainsi son `viewBox`, son `--mpp` et ses classes de palier, tous
    // calculés par `grain()` pour CETTE fenêtre. Les recalculer ici serait
    // recopier à la main ce que la carte sait déjà faire.
    const clone = svg.cloneNode(true);
    if (vise) CarteVille.viser(avant);
    // ---- fin du tour synchrone --------------------------------------------

    const rep = repere(clone, boite);
    if (!rep) throw new Error("le plan n'a pas de cadrage");
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", Math.round(boite.width));
    clone.setAttribute("height", Math.round(boite.height));
    clone.insertAdjacentHTML("afterbegin", entete());
    const texte = new XMLSerializer().serializeToString(clone);
    // `encodeURIComponent` et non base64 : le plan pèse trois mégaoctets de
    // chemins, et `btoa` sur une chaîne de cette taille est un pic de mémoire
    // pour rien. Une data-URI en pourcents se charge aussi bien.
    const img = new Image();
    img.decoding = "sync";
    await new Promise((ok, non) => {
      img.onload = ok;
      img.onerror = () => non(new Error("le plan n'a pas pu être rastérisé"));
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(texte);
    });

    const toile = document.createElement("canvas");
    toile.width = Math.round(boite.width);
    toile.height = Math.round(boite.height);
    const ctx = toile.getContext("2d");
    // Le fond du plan : le SVG a son propre `cv-sol` en fond, mais une marge de
    // letterbox resterait transparente et sortirait noire au format PNG.
    ctx.fillStyle = getComputedStyle(document.documentElement)
      .getPropertyValue("--cv-sol").trim() || "#efe7d6";
    ctx.fillRect(0, 0, toile.width, toile.height);
    ctx.drawImage(img, 0, 0, toile.width, toile.height);

    // 2. la foule, puis le fer, dans leur ordre d'empilement à l'écran. Ce sont
    // les copies prises au vol tout à l'heure, en pixels de l'appareil ; on les
    // étire sur la même boîte CSS, exactement comme le navigateur le fait.
    for (const g of gelees) ctx.drawImage(g, 0, 0, toile.width, toile.height);

    // LA MARQUE RESTE DANS L'IMAGE. Sans ce cercle, une capture de cent vingt
    // mètres contenant cent points oblige à retrouver l'homme une deuxième
    // fois. Son rayon est en pixels : constant quelle que soit l'approche.
    if (demande) {
      const mx = rep.ox + demande.x * rep.k, my = rep.oy + demande.y * rep.k;
      ctx.save();
      ctx.strokeStyle = "#ff7a3d"; ctx.fillStyle = "rgba(255,122,61,.14)";
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(mx, my, 15, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(mx - 22, my); ctx.lineTo(mx - 9, my);
      ctx.moveTo(mx + 9, my); ctx.lineTo(mx + 22, my);
      ctx.moveTo(mx, my - 22); ctx.lineTo(mx, my - 9);
      ctx.moveTo(mx, my + 9); ctx.lineTo(mx, my + 22); ctx.stroke();
      ctx.restore();
    }

    // 3. la taille de sortie. On ne grandit jamais une image — un plan tiré à
    // six cents pixels et soufflé à mille n'apprend rien de plus et pèse trois
    // fois plus lourd. On le RÉDUIT en revanche volontiers : à 760 pixels on
    // lit encore les masses, les rues et l'endroit où ça se presse, qui est
    // tout ce qu'on demande à cette image.
    let sortie = toile;
    if (toile.width > LARGE_MAX) {
      const ech = LARGE_MAX / toile.width;
      sortie = document.createElement("canvas");
      sortie.width = LARGE_MAX;
      sortie.height = Math.round(toile.height * ech);
      const sx = sortie.getContext("2d");
      // Sans ça, réduire de moitié donne un plan qui grésille : les traits
      // d'une rue à un pixel disparaissent ou doublent selon la parité.
      sx.imageSmoothingEnabled = true;
      sx.imageSmoothingQuality = "high";
      sx.drawImage(toile, 0, 0, sortie.width, sortie.height);
    }

    let image = null;
    for (const [type, q] of FORMATS) {
      image = sortie.toDataURL(type, q);
      if (image.indexOf("data:" + type) === 0) break;   // le format a bien pris
    }
    return { image, meta: legende(rep, sortie, centre, couches, moi, demande) };
  }

  // LA LÉGENDE FAIT LA MOITIÉ DU TRAVAIL. Une image sans échelle ni heure se
  // regarde et ne se cite pas : le MJ doit pouvoir en tirer une distance et une
  // minute, sinon il devine, et deviner est exactement ce qu'on lui interdit.
  function legende(rep, sortie, centre, couches, moi, cible) {
    const B = window.Bataille2d && Bataille2d.etat ? Bataille2d.etat() : null;
    const F = window.Foule2d && Foule2d.etat ? Foule2d.etat() : null;
    return {
      quand: new Date().toISOString(),
      montre: "cette vue montre : " + centre,
      // L'échelle est celle du RENDU, pas celle du volet : si l'image a été
      // réduite pour tenir sous le plafond, un mètre y vaut moins de pixel.
      metres_par_pixel: +(rep.vb[2] / sortie.width).toFixed(2),
      large_en_metres: Math.round(rep.vb[2]),
      haut_en_metres: Math.round(rep.vb[3]),
      joueur: moi ? { x: Math.round(moi.x), y: Math.round(moi.y) } : null,
      cible: cible ? { id: cible.id, nom: cible.nom,
                        x: +cible.x.toFixed(1), y: +cible.y.toFixed(1) } : null,
      couches,
      heure: F && F.heure, dehors: F && F.dehors, sous_un_toit: F && F.aEcran != null
        ? F.aEcran - F.dehors : null,
      bataille: B && B.dressee !== false ? B : null,
    };
  }

  // ---- le double au fil ----------------------------------------------------
  // ON VOIT CE QU'ON ENVOIE. Une image qui part vers le MJ sans que personne ne
  // la regarde est une image dont on ne sait pas si elle est juste : cadrée où
  // il faut, avec les bonnes couches, à la bonne heure. Elle se pose donc aussi
  // dans le fil, avec sa légende — c'est un miroir de débogage, et il est là
  // pour qu'un cadrage faux se voie tout de suite au lieu de se découvrir trois
  // batailles plus tard.
  //
  // RIEN N'ENTRE DANS `flux.jsonl`. On passe par `Bus.rendre`, qui peint un
  // item sans l'écrire ni le poster : ces vignettes ne sont pas de la partie,
  // elles ne se rejouent pas au rechargement, et le fil reste ce qu'il est.
  //
  // ET L'ON N'EN GARDE QUE QUELQUES-UNES. Une vue toutes les vingt secondes
  // fait cent quatre-vingts images à l'heure, et chacune pèse quarante
  // kilo-octets d'URL de données à demeure dans le document. Au bout d'une
  // bataille, le fil ne défile plus. On retire donc les anciennes : le débogage
  // veut la dernière et de quoi comparer, pas un album.
  const GARDE = 4;
  let auFil = localStorage.getItem("capture-fil") !== "non";

  if (window.Bus && Bus.enregistrer) Bus.enregistrer("vue", (it) => {
    const entree = Bus.chronique("chr-vue", "Vue envoyée au MJ",
      (it.meta && it.meta.montre) || "vue de la carte");
    if (!entree) return;
    const corps = entree.querySelector(".chr-corps");
    const m = it.meta || {};
    const img = document.createElement("img");
    img.className = "vue-image";
    img.src = it.image;
    img.alt = m.montre || "";
    // Un clic bascule entre la vignette et la pleine largeur : à 260 mètres de
    // large dans une colonne de fil, on distingue les masses et pas les hommes.
    img.addEventListener("click", () => img.classList.toggle("grande"));
    corps.appendChild(img);
    const l = document.createElement("div");
    l.className = "vue-legende";
    l.textContent = [m.heure, m.large_en_metres && (m.large_en_metres + " m de large"),
      m.metres_par_pixel && (m.metres_par_pixel + " m/px"),
      (m.couches || []).join(" + "),
      it.octets && Math.round(it.octets / 1024) + " Ko"]
      .filter(Boolean).join(" · ");
    corps.appendChild(l);
    const vieilles = document.querySelectorAll("#fil-corps .chr-vue");
    for (let i = 0; i < vieilles.length - GARDE; i++) vieilles[i].remove();
  });

  // ---- l'envoi -------------------------------------------------------------
  async function envoyer(opts) {
    const { image, meta } = await composer(opts);
    const r = await fetch("/vue", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image, meta }),
    });
    if (!r.ok) throw new Error("le serveur a refusé la vue (" + r.status + ")");
    const rep = await r.json();
    // Après l'envoi, pas avant : ce qu'on montre est ce qui est PARTI. Une
    // vignette posée d'abord ferait croire à une vue envoyée alors que le
    // serveur vient peut-être de la refuser.
    if (auFil && window.Bus && Bus.rendre)
      Bus.rendre({ type: "vue", image, meta, octets: rep && rep.octets });
    return rep;
  }

  // De quoi couper le miroir sans toucher au reste : `Capture.fil(false)`, et
  // ça tient au rechargement. L'envoi au MJ, lui, continue.
  function fil(oui) {
    if (oui === undefined) return auFil;
    auFil = !!oui;
    localStorage.setItem("capture-fil", auFil ? "oui" : "non");
    return auFil;
  }

  // ---- la boucle -----------------------------------------------------------
  // `setInterval` et non `requestAnimationFrame` : c'est une horloge, pas une
  // image. Et le navigateur le ralentit tout seul quand l'onglet passe au
  // second plan, ce qui est exactement ce qu'on veut — un joueur qui a changé
  // d'onglet n'a rien à montrer.
  let horloge = 0, dernierRate = null;
  function enBataille() {
    if (!window.Bataille2d || !Bataille2d.etat) return false;
    const e = Bataille2d.etat();
    return !!(e && e.dressee !== false);
  }
  async function battre() {
    if (!enBataille()) return;
    try { await envoyer(); dernierRate = null; }
    catch (e) {
      // ON LE DIT UNE FOIS, PAS À CHAQUE BATTEMENT. Une couche qui échoue en
      // silence se cherche une heure ; la même qui crie toutes les vingt
      // secondes noie la console et l'on finit par ne plus rien lire.
      const m = String(e && e.message || e);
      if (m !== dernierRate) { console.warn("capture :", m); dernierRate = m; }
    }
  }
  function suivre(ms) {
    if (horloge) clearInterval(horloge);
    horloge = setInterval(battre, ms || CADENCE);
    return horloge;
  }
  function cesser() { if (horloge) clearInterval(horloge); horloge = 0; }

  window.addEventListener("DOMContentLoaded", () => suivre());

  return { composer, envoyer, suivre, cesser, enBataille, fil };
})();
