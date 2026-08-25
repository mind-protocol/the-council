// corps-adapt.js — la prise entre la bataille et la couche 1.
//
// ELLE NE CONDUIT RIEN, ET C'EST LE POINT DE CETTE PREMIÈRE PASSE. La couche 1
// (`survival-stack/1-corps.js`) tourne pour chaque homme, à côté de la cascade
// de `soldat()`, et se fait mesurer — sans qu'aucun de ses gestes ne remplace
// quoi que ce soit. Le drapeau `pilote` existe et vaut `false`.
//
// POURQUOI EN DEUX TEMPS. Le grégarisme est une BOUCLE DE RÉTROACTION POSITIVE :
// la peur d'un homme monte celle de son voisin, qui monte la sienne. Rien dans
// le modèle n'empêche la divergence, et ça n'a jamais tourné qu'avec des voisins
// que le banc fabriquait — deux, trois, jamais deux mille cinq cents qui se
// lisent mutuellement. Si ça s'emballe, on veut le voir sur un relevé, pas sur
// une bataille qu'on aura cassée en même temps.
//
// CE QU'ELLE FAIT, ET RIEN D'AUTRE :
//   elle construit les VOISINS — des formes autour, avec ce qu'elles montrent ;
//   elle construit les SIGNAUX — à partir de champs que la bataille tient déjà ;
//   elle appelle `Corps.pas()` au rythme de l'ŒIL de l'homme, pas à 20 Hz ;
//   elle range le résultat dans `h.l1`, que personne ne consomme encore.
//
// ═════════════════════════════════════════════════════════════════════════════
// LE MAPPING — ON REMPLACE, ON NE GREFFE PAS
// ═════════════════════════════════════════════════════════════════════════════
//
// LE CONSTAT QUI A CHANGÉ LE PLAN : les couches 2, 3 et 4 EXISTENT DÉJÀ, sous
// une autre forme. La cascade de `soldat()` EST la tête — elle exécute des
// ordres, calcule des cibles, poursuit un but. Il n'y a donc rien à attendre,
// et surtout rien à faire cohabiter.
//
// ⚠ CE N'EST PAS UN BRANCHEMENT PROGRESSIF, ET LA DIFFÉRENCE EST DE FOND.
// Le drapeau `pilote` et le seuil de 0,6 d'emprise étaient un garde-fou de
// première passe : la couche existait À CÔTÉ de la morale, et les deux
// décidaient de la même chose. Deux modèles qui disent la même chose avec des
// pièces différentes ne se départagent jamais — on garde les deux « au cas
// où », et l'on hérite du pire des deux, sans plus savoir lequel produit quoi.
//
// L'OBJECTIF EST DONC LA SUPPRESSION : `morale`, `ROMPT`, `CHOC`, `SANG`,
// `REPRISE`, `PLANCHER_FERME`, `humeur` et `survie()` doivent DISPARAÎTRE de
// `bataille2d`, et la couche 1 tenir tout leur domaine, sans seuil et sans
// drapeau.
//
// CE QUI JUSTIFIAIT LE GARDE-FOU A DÉSORMAIS UN REMPLAÇANT. Le grégarisme est
// une boucle de rétroaction positive, et rien n'empêchait la divergence à deux
// mille cinq cents hommes qui se lisent mutuellement. C'est `c.social` — le
// niveau ambiant auquel on s'habitue, dont seul le DÉPASSEMENT passe — qui la
// borne maintenant, et il est mesuré : dérive +0,13, 86 % de calmes. Le seuil
// de 0,6 ne protège donc plus de rien qu'un autre mécanisme ne protège mieux.
//
// L'ORDRE CI-DESSOUS N'EST PAS UNE COHABITATION, C'EST UN ORDRE DE DÉPOSE.
// Chaque poste marqué [ ] est une chose que la morale sait faire et que la
// couche ne sait PAS ENCORE dire. Tant qu'il en reste un, supprimer `morale`
// perdrait un comportement en silence — ce qui est la seule façon de rater un
// remplacement. On les épuise, puis on dépose d'un bloc.
//
// LE PIÈGE DU TRANSFERT, à garder en tête tout du long : ce fichier-ci contient
// aussi LE MONDE, et le monde ne monte pas dans la pile. `pese()`, `achever`,
// `saigner`, `PART_BLESSE`, la grille de voisinage, les foyers, la voirie ne
// sont pas des hommes — ce sont les choses au milieu desquelles un homme est.
//
// ─── COUCHE 1 · LE CORPS — des DOUBLONS à résorber ───────────────────────────
// La bataille a un modèle de peur complet, écrit avant la pile, qui dit les
// mêmes choses avec d'autres pièces. Il ne s'agit pas d'ajouter : il s'agit de
// retirer d'un côté ce que l'autre sait déjà dire.
//
//   [ ] `morale` + `ROMPT`      → `reflexe` + `SOUS_EMPRISE`
//         La pile a l'hystérésis physiologique (montée 3 s, descente 45 s) là où
//         `ROMPT` est un seuil nu. NE PAS retirer avant que `humeur` soit
//         résorbée : `morale` porte encore des choses que `reflexe` ne dit pas.
//   [x] `CHOC` (un mort vu à 18 m) → stimulus `voisinTombe`
//         Émis, mais à 6 m contre 18 pour `CHOC`. L'écart est à trancher : deux
//         rayons pour un seul fait, c'est un des deux qui a tort.
//   [ ] `SANG` (usure sous ½ pv)  → `integrite`
//         La pile est invariante d'échelle (test A4), `SANG` ne l'est pas.
//   [ ] `REPRISE` (la morale remonte) → `M.DESCENTE_S`
//   [x] `humeur` ferme/sourd/versatile → `dressage`/`vecu`/`sourd`/`fond`
//         QUASI-DOUBLON, ET LA PILE EST MIEUX FONDÉE : `sourd` = habituation
//         haute, `ferme` = emprise repoussée, `versatile` = dressage bas. Trois
//         planchers ad hoc contre deux axes qui les produisent. Le test : les
//         six corps doivent rester distincts SANS plancher. Si `ferme` ne se
//         reproduit pas, c'est `emprise` qui est mal réglée, et on l'apprend là.
//   [x] `sousLaBanniere` / `TIENT_BANN` → `M.APAISE_BANN`, via `apaise`
//   [x] `rallier` (un chef à 15 m)      → `M.APAISE_CHEF`, via `apaise`
//         Ces deux-là sont les seuls mécanismes par lesquels un commandement
//         PROTÈGE ses hommes au lieu de les déplacer. Ils passent par la
//         constante de DESCENTE de l'alarme — pas par sa cible : un homme sous
//         sa bannière a exactement aussi peur du même coup, il s'en remet plus
//         vite. C'est ce que `TIENT_BANN` disait déjà (il multipliait la
//         REPRISE, jamais le niveau). Mesure : 45 s seul, 17,7 s sous la
//         bannière, 12,3 s avec son chef, 7,8 s les deux.
//         L'ACTE de rallier reste dans `bataille2d` : ramener un homme qui
//         court est de l'AUTORITÉ, donc couche 3. Seule la PRÉSENCE monte ici.
//   [x] `RECUL`, `FREIN_PRESSE` → `M` / `mesures.js`
//         Mesures du monde, pas du comportement : à mutualiser, pas à monter.
//
//   LES STIMULI — la couche 1 était SOUS-ALIMENTÉE, trois sur six seulement.
//   [x] `coupRecu`    émis dans `frapper`
//   [x] `coupFrole`   émis dans `frapper`
//   [x] `voisinTombe` émis à la chute, rayon 6 m
//   [x] `ferQuiVient` dérivé ici même, du `prochain` de l'ennemi
//   [x] `dansLeDos`   dérivé ici même, de la géométrie déjà balayée
//   [x] `voisinPart`  émis par `rompre()` — LE PLUS PUISSANT DÉCLENCHEUR DE
//         FUITE QUI EXISTE, et la source même de la contagion. Sans lui, une
//         ligne ne se défaisait pas en vague : chacun rompait dans son coin.
//
// ─── COUCHE 2 · LA RÉFLEXION — elle est DÉJÀ ÉCRITE, et c'est la surprise ────
// `proieProche` EST une couche 2 complète : des options évaluées dans une
// monnaie unique (des mètres), un coût (`ENCOMBRE`, au carré), un budget de
// souffle (`EFFORT_NU`/`EFFORT_VIF`), et un REFUS quand même la moins chère
// dépasse le budget. C'est mot pour mot « comment me sortir de cette
// situation ? ».
//
//   [ ] `proieProche` + `ENCOMBRE` + le budget → le NOYAU de `2-reflexion.js`
//         À DÉPLACER, PAS À RÉÉCRIRE. La généralisation est de passer de
//         « quelle proie » à « quel verbe sur quelle cible » — le barème ne
//         change pas.
//   [ ] les trois règles « on tient à sa vie » (entamé on décroche, débordé on
//         cède, on reprend son souffle) → des candidats au même barème
//   [ ] `dehors()` + la fuite par le graphe de voirie → l'ISSUE SITUÉE : la
//         cible cesse d'être un homme pour devenir un lieu
//   [ ] `h.cible` tenue d'un battement à l'autre (le `tenu` de `proieProche`)
//         → l'ENGAGEMENT : un plan ne se relâche pas à chaque pas
//   [ ] CE QUI MANQUE VRAIMENT, et que rien ici ne contient : L'ATTENTE.
//         `proieProche` choisit et ne prédit rien, donc rien ne peut le
//         démentir. La couche 1 lâche par HORLOGE (`SEJOUR`) ; la couche 2 doit
//         lâcher par DÉMENTI. C'est la seule pièce entièrement neuve des trois
//         couches qui restent.
//
// ─── COUCHE 3 · L'INTERPRÉTATION — tout le substrat, aucune latitude ─────────
// Cinq verbes, bannière contre coureur, `DELAI_BANN`, les ordres qui se
// perdent, `h.poste`, « il attend sa place au seuil ». Le tuyau est complet.
//
//   [ ] CE QUI MANQUE EST EXACTEMENT LE SUJET DE LA COUCHE : l'ordre est
//         EXÉCUTÉ, jamais interprété. « Tenez la porte » ne produit pas deux
//         hommes qui le tiennent différemment. La couche la moins avancée en
//         substance, et la mieux outillée.
//
// ─── COUCHE 4 · L'ENVIE — un seul comportement, et il est bon ────────────────
//   [ ] `piller` — « il quitte la colonne pour une maison ». Le seul désir
//         gratuit du fichier : il concurrence l'ordre reçu, il a une durée et un
//         butin, et `sourd` ne le fait pas. La couche 4 en miniature, avec sa
//         porte d'entrée déjà écrite.
//
// ─── LE TEST QUI DIT SI L'ON DÉPOSE OU SI L'ON GREFFE ───────────────────────
// UN POSTE QUI FAIT GROSSIR `bataille2d` EST UNE GREFFE, quel que soit le
// discours autour. C'est le seul controle qui ne se laisse pas raconter, et il
// tient en une commande :
//
//   grep -vE '^\s*(//|/\*|\*)' ecrans/modules/bataille2d.js //     | grep -vE '^\s*$' | wc -l
//
// Reference : **2801 lignes de code a HEAD** (hors commentaires et lignes
// vides), avant que ce refactor commence. Le compte doit BAISSER a chaque
// poste. Au moment ou l'on ecrit ceci il est a 2982 — soit +181 : la couche 1
// a bien vide son domaine, mais les couches 3 et 4 ont ete ajoutees sans que
// tout l'ancien code parte, et la couche 2 n'existe pas.
//
// Ce n'est pas un reproche a l'ordre suivi — on ne peut pas retirer ce qu'un
// remplacant ne sait pas encore faire. C'est un compteur, pour qu'on ne puisse
// plus s'illusionner sur l'etat d'avancement.
//
// ─── LA DÉPOSE, DANS CET ORDRE ──────────────────────────────────────────────
//   1. [x] les trois stimuli manquants — la couche ne peut rien remplacer tant
//          qu'elle est sourde. `voisinPart` d'abord : sans lui une ligne ne se
//          défait pas en vague, chacun rompt dans son coin.
//   2. [x] `humeur` → `dressage`/`vecu`, corps par corps. Test : les six restent
//          distincts SANS plancher.
//   3. [ ] `sousLaBanniere` et `rallier` en signes de couche 1. Sans eux, la
//          dépose de `morale` retire au commandement le seul moyen qu'il ait de
//          PROTÉGER au lieu de déplacer.
//   4. [ ] retirer le drapeau `pilote` et le seuil de 0,6 — la couche conduit
//          ses onze gestes, tout le temps.
//   5. [ ] supprimer `survie()`, `morale`, `ROMPT`, `ROMPT_VERSATILE`, `CHOC`,
//          `SANG`, `REPRISE`, `PLANCHER_FERME`, `REPRISE_HUMEUR`.
//
// Le seuil de 0,6 n'est donc pas un bouton à régler : c'est une pièce à jeter.
// ═════════════════════════════════════════════════════════════════════════════
"use strict";
(() => {

  const C = (typeof window !== "undefined" && window.Corps)
    || (typeof require !== "undefined" && require("../survival-stack/1-corps.js"));

  // ⚠ LE HASARD DE LA COUCHE DOIT ETRE CELUI DE LA BATAILLE, ET LA DEPOSE L'A
  // PROUVE A SES DEPENS. Cette ligne appelait `Math.random()`. Tant que la
  // couche ne conduisait qu'au-dessus de 0,6 d'emprise — 3 % des hommes —, la
  // relecture du four tenait : ecart pire 0,600 m, 3 etats faux sur 2,19 M.
  //
  // Le seuil retire, elle conduit TOUT LE MONDE : ecart pire 329 m, 931 172
  // etats faux. Le sac ne rendait plus rien de ce que la simulation avait fait,
  // et toute la machinerie de `hasard.js` — une graine, une bataille rejouable
  // a l'identique — etait contournee par un seul appel.
  //
  // Ce n'est pas un defaut de la depose : c'est un defaut qu'elle a REVELE, et
  // qui attendait son heure depuis la premiere passe.
  const H = (typeof window !== "undefined" && window.BatailleHasard) || null;

  // ON NE FAIT PAS TOURNER 2 550 CERVEAUX VINGT FOIS PAR SECONDE. La bataille a
  // déjà la bonne horloge pour ça : `oeil()`, le temps qu'un homme met à
  // s'apercevoir de quelque chose — de 0,1 à 3 s, individuel, ralenti par la
  // fatigue. La couche s'y branche, et reçoit le `dt` accumulé depuis son
  // dernier passage : les constantes de temps (montée, descente, habituation)
  // sont des exponentielles, donc elles supportent un pas variable sans dériver.
  //
  // Ce qui NE supporte pas le pas variable, ce sont les stimuli : un coup reçu
  // entre deux coups d'œil doit quand même être vu. Ils s'accumulent donc dans
  // `h.recu`, et c'est la boîte aux lettres qui les garde jusqu'au réveil.
  const RAYON_VOISINS = 4.5;      // mètres : de quoi tenir un rang, pas une aile
  const RAYON_MENACE = 12;        // le second rang voit le premier travailler

  /** L'angle de `o` vu depuis `h`, RELATIF à son cap tenu. */
  function relatif(h, o) {
    const a = Math.atan2(o.y - h.y, o.x - h.x);
    const cap = (h.fx || h.fy) ? Math.atan2(h.fy, h.fx) : 0;
    let d = a - cap;
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    return d;
  }

  /**
   * @param h      l'homme de `bataille2d`
   * @param ctx    { autour, temps, nuit, degatTypique, pese }
   * @param dt     secondes depuis son dernier passage ici
   */
  function observer(h, ctx, dt) {
    const voisins = [], proches = [];
    ctx.autour(h.x, h.y, RAYON_MENACE, (o) => {
      if (o === h || !ctx.pese(o)) return;
      const d = Math.hypot(o.x - h.x, o.y - h.y);
      if (d > RAYON_MENACE) return;
      const ami = o.camp === h.camp;
      if (ami) {
        if (d > RAYON_VOISINS) return;
        // CE QU'UNE FORME MONTRE, ET RIEN DE PLUS. Pas son camp nominal, pas son
        // rang, pas sa peur : son geste, son cap, et depuis quand il le tient.
        // `h.branche` de la bataille n'est pas un geste de la couche 1 — on ne
        // traduit donc PAS, on prend l'état de la couche s'il en a un, sinon on
        // laisse vide et le voisin ne pèse que par sa présence.
          const l = o.l1;
        // CE QU'IL PORTE, EN PLUS DE CE QU'IL FAIT. Un porte-banniere debout
        // et un chef a portee de voix ne sont pas des gestes : ce sont des
        // FAITS, et ils se lisent de bien plus loin qu'un coude. La couche
        // les prend comme des formes ordinaires — elle ne sait pas ce qu'est
        // une banniere, et n'a pas a le savoir.
        const porte = (o.capitaine && ctx.banniereDebout && ctx.banniereDebout(o))
          ? "banniere" : (o.chef || o.capitaine) ? "chef" : null;
        voisins.push({
          porte: porte === "banniere" ? "bannière" : porte,
          angle: relatif(h, o), distance: d, ami: true,
          memeGroupe: !!(h.corps && o.corps === h.corps && o.escouade === h.escouade),
          jambes: l ? l.jambes : null, bras: l ? l.bras : null,
          cap: (o.fx || o.fy) ? relatif(h, { x: o.x + o.fx, y: o.y + o.fy }) : null,
          depuis: l ? Math.max(0, ctx.temps - (l.depuis || 0)) : 99,
        });
      } else {
        const a = relatif(h, o);
        voisins.push({ angle: a, distance: d, ami: false });
        proches.push({ distance: d, deFace: Math.cos(a),
                       frappe: o.etat === "melee" || o.etat === "assaut",
                       // DEUX CHOSES DE PLUS, ET ELLES NE COÛTENT RIEN : on est
                       // déjà sur cet homme, on lit deux champs au passage.
                       //   `tau`  — les secondes avant que SON coup parte. C'est
                       //     le meilleur τ possible dans ce modèle, où les coups
                       //     sont instantanés et n'ont pas de trajectoire.
                       //   `vient` — son cap voulu pointé sur moi. Faute d'une
                       //     vitesse par homme, c'est la substitution honnête :
                       //     elle dit son INTENTION, ce qu'une vitesse ne dit pas.
                       tau: o.prochain == null ? 9 : Math.max(0.05, o.prochain),
                       vient: (o.cx || o.cy)
                         ? -(o.cx * Math.cos(a) + o.cy * Math.sin(a)) : 0 });
      }
    });

    // LA MESURE DU FER, PAS L'ETIQUETTE D'ETAT. Un homme est au contact si un
    // ennemi vivant est dans l'allonge de SON arme. Les bouts se ferment ici,
    // au meme balayage qui a deja mesure les distances : aucun second parcours.
    const allonge = ((h.arme && h.arme.allonge) || 0.9) + 0.6;
    const enMesure = proches.some((x) => x.distance <= allonge);
    if (enMesure && !h.enMesure) {
      h.enMesure = true; h.mesureDepuis = ctx.temps; h.boutsMesure++;
    } else if (!enMesure && h.enMesure) {
      const duree = Math.max(0, ctx.temps - h.mesureDepuis);
      h.dernierBout = duree; h.boutMax = Math.max(h.boutMax, duree);
      h.enMesure = false;
    }
    if (enMesure) h.tempsEnMesure += dt;

    // Le degagement est une geometrie orientee : trois pas derriere le cap,
    // combines avec la presse humaine. Sans masque, on garde explicitement le
    // seul terme connu au lieu de declarer la rue ouverte.
    let sol = 1;
    if (ctx.libre) {
      const fx = h.fx || h.cx || 1, fy = h.fy || h.cy || 0;
      let libres = 0;
      for (const pas of [0.8, 1.6, 2.4])
        if (ctx.libre(h.x - fx * pas, h.y - fy * pas)) libres++;
      sol = libres / 3;
    }
    h.degagement = Math.max(0, Math.min(1, sol * (1 - Math.min(1, (h.presse || 0) / 6))));

    // ---- LES DEUX STIMULI QUI SE DÉRIVENT DE CE BALAYAGE ---------------------
    // La couche 1 était sourde de trois sens sur six : `frapper` lui envoyait le
    // coup reçu et le coup frôlé, la chute lui envoyait le voisin à terre, et
    // c'était tout. Or `ferQuiVient` est le seul stimulus du répertoire qui ARME
    // UNE PARADE — sans lui, l'appel de `parer` valait −1 en permanence et le
    // geste ne pouvait littéralement jamais être élu.
    //
    // ON LES DÉRIVE ICI ET NON DANS `frapper`, parce que la géométrie est déjà
    // balayée : les émettre à la source demanderait un second parcours par coup
    // porté. Ce sont des PERCEPTIONS CONTINUES, pas des événements — on les
    // représente à chaque coup d'œil, et l'écho de la couche garde le plus fort.
    // `C` et non `window.Corps` : ce fichier doit tourner dans node aussi.
    if (C) {
      const K = C;
      let fer = null, dos = null;
      for (const p of proches) {
        // Le plus imminent, et seulement s'il est devant : on ne voit pas partir
        // un coup qu'on n'a pas dans le champ.
        if (p.deFace > 0 && p.tau < 0.6 && (!fer || p.tau < fer.tau)) fer = p;
        // Le plus proche de ceux qui sont DERRIÈRE et qui viennent sur moi.
        if (p.deFace < 0 && p.vient > 0 && (!dos || p.distance < dos.distance))
          dos = p;
      }
      if (fer && h.recu && h.recu.length < 8)
        h.recu.push(Object.assign(K.ferQuiVient(fer.tau, fer.deFace),
                                  { t: ctx.temps }));
      if (dos && h.recu && h.recu.length < 8)
        h.recu.push(Object.assign(K.dansLeDos(dos.distance, dos.deFace, dos.vient),
                                  { t: ctx.temps }));
    }

    const pvMax = h.pvMax || 25;
    const dangerExterieur = ctx.temps <= (h.menaceJus || -Infinity)
      ? (h.menaceExterieure || 0) : 0;
    const signaux = {
      integrite: C.integrite(Math.max(0, h.pv), ctx.degatTypique),
      souffle:   C.souffle(h.souffle == null ? 1 : h.souffle),
      menace:    Math.max(C.menace(proches), dangerExterieur),
      // −1 est l'absence, +1 le danger qui prend tout le champ. Le garder
      // distinct de `menace` permet aux appels de distinguer un homme armé à
      // portée d'une masse de feu dont on doit seulement sortir.
      dangerExterieur: 2 * dangerExterieur - 1,
      // L'ISSUE N'EST PAS MODÉLISÉE DANS LA BATAILLE, et il faut le dire plutôt
      // que d'inventer. Il n'existe nulle part de « part de mon arrière qui est
      // libre » : ni mur, ni cul-de-sac, ni presse orientée. On prend donc la
      // presse comme approximation — être serré, c'est ne pas pouvoir reculer —
      // et l'on note que c'est le signal le plus faible des cinq tant que la
      // géométrie ne le donnera pas pour de bon.
      issue:     C.issue(h.degagement),
      // ⚠ `proches` N'EST PAS TRIE — il sort de la grille de voisinage, dans
      // l'ordre ou elle balaie. Prendre `[0]` revenait a tester un ennemi
      // au hasard, pas le plus proche.
      aPortee:   enMesure,
      ennemisProches: proches.length,
    };

    if (!h.l1etat) h.l1etat = {
      dressage: h.dressage == null ? 0 : h.dressage,
      vecu: h.vecu == null ? 0 : h.vecu,
      // La surdité au canal social (ce que `humeur: "sourd"` disait) et le
      // fond (ce que « versatile » disait), tirés à la naissance.
      sourd: h.sourd || 0,
      fond: h.fond == null ? 1 : h.fond,
    };
    const r = C.pas(h.l1etat, {
      t: ctx.temps, dt, stimuli: h.recu || [], signaux, voisins,
      nuit: !!ctx.nuit, presse: h.presse || 0,
      // CE QU'IL A SOUS LES YEUX ET QUI LE FAIT REDESCENDRE — sa banniere
      // debout, son chef a portee. La bataille sait les deux ; la couche ne
      // sait pas ce qu'est une banniere, et n'a pas a le savoir. Voir `activer`.
      // ⚠ DEUX MECANISMES POUR LA MEME CHOSE, ET ON N'EN GARDE QU'UN.
      // `apaise` etait un scalaire que la bataille calculait — « ta banniere
      // est debout, ton chef est la, donc tu redescends plus vite » — et il
      // accelerait la descente du reflexe. Il marchait. Mais c'est une
      // CONCLUSION pre-machee servie a la couche, exactement la faute qui a
      // deja ete corrigee deux fois aujourd'hui : lire `voisin.alarme` au
      // lieu de ce qu'il montre, et calculer la contagion hors des canaux.
      //
      // La banniere passe donc par ou tout le reste passe : c'est une FORME
      // dans la liste des voisins, avec sa portee (40 m contre 2,2 pour un
      // coude) et son canal. Ce qu'on y gagne n'est pas theorique — la nuit
      // mange la banniere, le vacarme mange le chef, et une troupe de nuit
      // dans le bruit se retrouve sans commandement sans qu'on l'ait ecrit.
      // `apaise` reste neutre : la fonction demeure dans `activer`, elle ne
      // recoit plus rien.
      apaise: 1,
    }, H ? H.R() : Math.random());

    // La boîte aux lettres se vide une fois lue : un coup ne se sent qu'une fois.
    if (h.recu && h.recu.length) h.recu.length = 0;

    // `depuis` : l'instant du dernier changement de geste, pour que les VOISINS
    // sachent qui vient de bouger. C'est l'entrée de l'initiateur, et elle ne
    // peut se tenir qu'ici — un homme ne sait pas lui-même depuis quand il fait
    // ce qu'il fait, mais celui qui le regarde, si.
    const avant = h.l1;
    r.depuis = (avant && avant.jambes === r.jambes && avant.bras === r.bras)
      ? (avant.depuis || ctx.temps) : ctx.temps;
    h.l1 = r;
    return r;
  }

  // ⚠ IL CONDUIT, MAIS SUR DEUX ETATS SEULEMENT — `sidération` et `fuite`, et
  // seulement au-dessus de 0,6 d'emprise. Voir le branchement dans `soldat()`.
  // On elargira quand ceux-ci auront tenu une cuisson entiere.
  const API = { observer, RAYON_VOISINS, pilote: true };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.BatailleCorps = API;
})();
