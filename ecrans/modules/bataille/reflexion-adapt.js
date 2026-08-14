// reflexion-adapt.js — la prise entre la bataille et la couche 2.
//
// LE JUMEAU DE `corps-adapt.js`, ET IL MANQUAIT. `2-reflexion.js` était écrite,
// relue, éprouvée, chargée par `jeu.html` — et appelée NULLE PART :
// `grep -rn "Reflexion" ecrans/ scripts/ serveur/` hors du module rendait zéro
// occurrence, et `h.l2` n'existait pas dans les 6 957 lignes de `bataille2d.js`.
// Une couche chargée et jamais appelée est plus dangereuse qu'une couche
// absente, parce qu'elle a l'air d'être là (🔒 90370).
//
// Les trois autres couches ont leur pourvoyeur : la 1 a `corps-adapt.js`, la 3
// et la 4 sont nourries en ligne dans `soldat()`. Celui-ci est celui de la 2.
//
// ELLE NE CONDUIT RIEN, ET C'EST VOULU POUR CETTE PASSE. Ce fichier écrit
// `h.l2`, et `h.conduit` — la trace, voir tout en bas. Il ne touche ni `h.etat`,
// ni `h.cible`, ni `h.recule`, ni la boîte aux lettres `h.recu` (qui appartient
// à `corps-adapt`, et qu'un second lecteur viderait sous son nez).
//
// ═════════════════════════════════════════════════════════════════════════════
// CE QU'IL BÂTIT, ET D'OÙ ÇA SORT
// ═════════════════════════════════════════════════════════════════════════════
//
// La couche 2 lit onze signaux. Aucun n'existait sous ce nom dans la bataille ;
// tous se dérivent de ce qu'elle tient déjà. Le tableau, source par source —
// c'est la seule partie de ce fichier qui mérite d'être relue avant de le juger.
//
//   `nombre`   amis/ennemis du cercle, comme `balance()` les compte
//   `alarme`   le plus menaçant des ennemis vus, par sa distance et son geste
//   `entame`   `h.pv / h.pvMax`
//   `frais`    `h.souffle`
//   `epaule`   la distance du plus proche des siens
//   `lachent`  la part de ceux qui reculent autour de lui — `b.reculent`
//   `trempe`   `h.trempe`, déjà sur [−1, 1], tiré à la naissance
//   `deja`     SA PROPRE SORTIE DU BATTEMENT D'AVANT, et non `h.recule`
//   `depuis`   l'horloge d'attente, tenue ICI (la couche n'en tient aucune)
//   `versLui`  le cap vers ce qui le menace
//   `versEux`  le cap vers le centre des siens (`b.ax, b.ay`)
//   `degage`   TROIS SONDES DERRIÈRE LUI — voir plus bas, c'est le morceau
//
// `deja` NE LIT PAS `h.recule`, ET C'EST DÉLIBÉRÉ. `h.recule` est posé par
// `decider()`, c'est-à-dire par la cascade que ⚔️ 90312 va déposer morceau par
// morceau. Un pourvoyeur qui s'y branche fabrique une couche qui cesse de
// fonctionner le jour où le remplacement réussit — l'hystérésis doit vivre dans
// la couche, pas dans la pièce qu'on retire. On lit donc `h.l2.tient` du
// battement précédent, ce qui est la même mécanique et survit à la dépose.
//
// ─── `degage` — LE SIGNAL POUR LEQUEL LA COUCHE A ÉTÉ ÉCRITE ─────────────────
//
// 🔒 90350 : « `degage` n'existe pas, aucun homme ne sait s'il a une retraite ».
// `decider()` fait céder le pas sur le seul compte local et ne regarde jamais
// derrière : un homme dos au mur recule dans le mur. On le lève ici, et par où
// le verrou disait qu'on le lèverait — TROIS SONDES EN ÉVENTAIL DERRIÈRE
// L'HOMME, à la distance qu'il couvrirait en trois secondes de repli.
//
// Le sol franchissable, lui, existait déjà et personne ne s'en servait pour ça :
// c'est le masque du bâti que `enterrer()` charge pour pénaliser les rues
// enterrées. Il est désormais tenu par `bataille2d.js` et rendu ici par
// `ctx.libre(x, y)`.
//
// DEUX FAÇONS D'ÊTRE ACCULÉ, ET ON GARDE LA PIRE. Le bâti derrière soi en est
// une ; la presse des corps en est une autre, et elle est aussi vraie — un
// homme au milieu d'un tas ne recule pas davantage qu'un homme contre un mur.
// `h.presse` la donne, la bataille la tient déjà.
//
// ⚠ QUAND LE MASQUE MANQUE, `degage` NE MONTE PAS AU-DESSUS DE ZÉRO. Le four
// peut tourner sans lui (pas de plan, pas de `fetch`). Zéro veut dire « on ne
// sait pas » et non « la retraite est ouverte » : supposer la retraite ouverte
// est exactement l'erreur que cette couche répare. La presse, elle, se lit
// toujours — on peut donc savoir un homme acculé sans savoir aucun homme libre.
//
// ─── AUCUN TIRAGE ICI ────────────────────────────────────────────────────────
// Une seule ligne de `Math.random()` dans `corps-adapt.js` a contourné la graine
// de `hasard.js` : écart pire 329 m, 931 172 états faux (🔒 90120). Ce fichier
// ne tire rien, ne prend pas de `u`, et n'en prendra pas. Tout ce qu'il fait est
// une lecture de géométrie.
"use strict";
(() => {

  const R2 = (typeof window !== "undefined" && window.Reflexion)
    || (typeof require !== "undefined" && require("../survival-stack/2-reflexion.js"));
  const QC = () => (typeof window !== "undefined" && window.QuiConduit) || null;

  const bornes = (v) => Math.max(-1, Math.min(1, v));

  // ⚠ DÉPENDANCE DE FAIT, ET ON LA NOMME PLUTÔT QUE DE SE MENTIR (règle du
  // README). `RAYON_COMPTE` est le `RAYON_LOCAL` de `bataille2d.js` : c'est le
  // cercle dans lequel `balance()` compte, donc le cercle dans lequel la
  // cascade décide. Si l'un bouge sans l'autre, la couche 2 se met à compter
  // autre chose que ce que la cascade compte, et le jour où l'on comparera les
  // deux on comparera deux cercles.
  const RAYON_COMPTE = 5;
  // On voit plus loin qu'on ne compte : un ennemi à huit mètres n'entre pas
  // dans le rapport de forces local, mais personne ne le dira calme.
  const RAYON_VU     = 8;
  const PORTEE_BRAS  = 2.2;   // `PORTEE` de la bataille : au-delà, il ne touche pas
  const SEUL_A       = 10;    // « personne à dix pas », le −1 d'`epaule`
  const ATTENTE_S    = 5;     // l'horloge de `depuis` : au-delà, un homme entre
  const REPLI_MS     = 1.3;   // `MARCHE` : on ne recule pas au pas de course
  const SONDE_S      = 3;     // « la distance de trois secondes »
  const SONDE_PAS    = 4;     // combien d'échantillons le long d'une sonde
  const EVENTAIL     = 0.61;  // ±35° — un éventail, pas un cône de vision
  const PRESSE_PLEIN = 6;     // `h.presse` à partir de quoi on ne recule plus

  /** Le cap unitaire de `a` vers `b`, ou null si les deux se confondent. */
  function vers(ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay, n = Math.hypot(dx, dy);
    return n > 1e-6 ? [dx / n, dy / n] : null;
  }

  // ===========================================================================
  // LES SONDES
  // ===========================================================================

  /** +1 la retraite est ouverte, −1 il est acculé, 0 on ne sait pas.
   *
   *  `dos` est le cap de sa retraite : l'opposé de ce qui le menace, et à
   *  défaut de menace l'opposé de son propre cap tenu — un homme sans ennemi
   *  visible recule par où il est venu, ce qui est encore le plus vrai.
   *
   *  UNE SONDE EST BLOQUÉE DÈS LE PREMIER PAS QUI TOMBE SOUS UN TOIT, et non
   *  seulement à son bout : un mur à un mètre arrête un repli de quatre mètres,
   *  et c'est tout l'intérêt d'échantillonner plutôt que de tester l'arrivée. */
  function sonder(h, dos, ctx) {
    if (!ctx.libre) return null;              // pas de masque : on ne sait pas
    const portee = REPLI_MS * SONDE_S;
    let libres = 0;
    for (const a of [-EVENTAIL, 0, EVENTAIL]) {
      const cx = dos[0] * Math.cos(a) - dos[1] * Math.sin(a);
      const cy = dos[0] * Math.sin(a) + dos[1] * Math.cos(a);
      let bonne = true;
      for (let k = 1; k <= SONDE_PAS && bonne; k++) {
        const d = portee * k / SONDE_PAS;
        if (!ctx.libre(h.x + cx * d, h.y + cy * d)) bonne = false;
      }
      if (bonne) libres++;
    }
    return libres / 3;                         // 0, ⅓, ⅔ ou 1
  }

  // ===========================================================================
  // UN BATTEMENT
  // ===========================================================================

  /**
   * @param h    l'homme de `bataille2d`
   * @param ctx  { autour, temps, pese, libre }
   * @param dt   secondes depuis son dernier passage ici
   */
  function observer(h, ctx, dt) {
    // ---- UN SEUL BALAYAGE, ET IL SERT À TOUT ------------------------------
    // Le même que `balance()` fait pour la cascade et que `observer()` fait
    // pour la couche 1. On ne le mutualise pas encore : les trois n'ont ni le
    // même rayon ni le même contenu, et un rayon mutualisé à la va-vite est la
    // façon la plus sûre de faire compter à quelqu'un un cercle qui n'est pas
    // le sien. C'est noté, ce n'est pas oublié.
    let amis = 0, ennemis = 0, ax = 0, ay = 0, reculent = 0;
    let ami = Infinity, men = null, menForce = 0;
    ctx.autour(h.x, h.y, RAYON_VU, (o) => {
      if (o === h || !ctx.pese(o)) return;
      const d = Math.hypot(o.x - h.x, o.y - h.y);
      if (d > RAYON_VU) return;
      if (o.camp === h.camp) {
        if (d < ami) ami = d;
        if (d <= RAYON_COMPTE) {
          amis++; ax += o.x; ay += o.y;
          if (o.recule) reculent++;
        }
        return;
      }
      if (d <= RAYON_COMPTE) ennemis++;
      // CE QUI MENACE LE PLUS N'EST PAS LE PLUS PROCHE, et l'écart est réel :
      // un homme au fer à trois mètres pèse plus qu'un homme qui marche à un
      // mètre. La distance domine, le geste module.
      const f = (1 - d / RAYON_VU)
              * (o.etat === "melee" || o.etat === "assaut" ? 1 : 0.7);
      if (f > menForce) { menForce = f; men = o; }
    });

    // ---- L'ÉTAT QUE CE FICHIER TIENT POUR LA COUCHE -----------------------
    // La couche est pure : elle ne tient ni horloge ni mémoire. Les deux
    // choses qui se souviennent vivent donc ici, comme `h.l1etat` pour la
    // couche 1.
    const e = h.l2etat || (h.l2etat = { attendDepuis: 0 });

    const pvMax = h.pvMax || 25;
    const avant = h.l2;
    const dMen = men ? Math.hypot(men.x - h.x, men.y - h.y) : Infinity;
    const nombre = bornes((amis + 1 - ennemis) / 3);

    // ── L'HORLOGE D'ATTENTE, ET LE BASSIN A PRIS SA PREMIÈRE ÉCRITURE ────────
    // `depuis` est le temps déjà passé à attendre le nombre, normalisé sur cinq
    // secondes : passé ce délai un homme entre, gagnant ou non.
    //
    // ⚠ ELLE ÉTAIT ARMÉE PAR LA SORTIE DE LA COUCHE — « il tourne tant que
    // `attend` dépasse 0,35 » —, ET C'EST UNE BOUCLE. À cinq secondes `attend`
    // retombe sous le seuil, l'horloge se remettait à zéro, donc `attend`
    // remontait au battement suivant, donc l'horloge repartait : une dent de
    // scie au rythme de l'œil, un homme qui entre et ressort de son attente
    // vingt fois par minute. Mesuré : 0,72 → 0,43 → 0,72, sans que rien n'ait
    // bougé autour de lui.
    //
    // UNE HORLOGE SE TIENT SUR LE MONDE, JAMAIS SUR L'AVIS QU'ELLE NOURRIT.
    // Ce qui dure ici n'est pas une opinion, c'est une SITUATION : il est en
    // infériorité et il n'est pas encore au fer. Tant qu'elle dure, le compteur
    // monte ; qu'il touche l'ennemi ou que le nombre tourne, il retombe — et
    // pour de bonnes raisons, pas parce que la couche a changé d'avis.
    if (nombre < 0 && dMen > PORTEE_BRAS) e.attendDepuis += dt;
    else e.attendDepuis = 0;

    const cap = vers(0, 0, h.fx || 0, h.fy || 0);
    const versLui = men ? vers(h.x, h.y, men.x, men.y) : null;
    const versEux = amis ? vers(h.x, h.y, ax / amis, ay / amis) : null;
    // Le dos : l'opposé de la menace, sinon l'opposé du cap tenu, sinon rien.
    const dos = versLui ? [-versLui[0], -versLui[1]]
              : cap ? [-cap[0], -cap[1]] : null;

    const sol = dos ? sonder(h, dos, ctx) : null;
    const parLeBati = sol === null ? 0 : bornes(2 * sol - 1);
    const parLesCorps = bornes(1 - 2 * Math.min(1, (h.presse || 0) / PRESSE_PLEIN));
    // ON GARDE LA PIRE DES DEUX. Et quand le bâti est inconnu, `parLeBati` vaut
    // zéro : la presse peut alors rendre un homme acculé, jamais dégagé.
    const degage = Math.min(parLeBati, parLesCorps);

    const s = {
      nombre,
      alarme:  bornes(1 - 2 * Math.min(1, menForce * 1.35)),
      entame:  bornes(2 * Math.max(0, h.pv) / pvMax - 1),
      frais:   bornes(2 * (h.souffle == null ? 1 : h.souffle) - 1),
      epaule:  ami === Infinity ? -1 : bornes(1 - 2 * (ami / SEUL_A)),
      lachent: amis ? bornes(1 - 2 * (reculent / amis)) : 0,
      trempe:  bornes(h.trempe || 0),
      // Son propre avis d'il y a un battement, et rien d'autre : l'hystérésis
      // appartient à la couche, pas à la cascade qu'on dépose.
      deja:    avant ? bornes(-avant.tient) : 0,
      depuis:  Math.min(1, e.attendDepuis / ATTENTE_S),
      degage,
      versLuiX: versLui ? versLui[0] : 0, versLuiY: versLui ? versLui[1] : 0,
      versEuxX: versEux ? versEux[0] : 0, versEuxY: versEux ? versEux[1] : 0,
    };

    const r = R2.pas(s);
    // CE QUI SERT À LA LOUPE ET À RIEN D'AUTRE : de quoi relire une décision
    // sans avoir à refaire le balayage. Trois nombres, pas les onze signaux.
    r.degage = degage;
    r.aPortee = dMen <= PORTEE_BRAS;
    r.depuis = e.attendDepuis;
    h.l2 = r;

    // =========================================================================
    // LA TRACE — ET C'EST LA MOITIÉ DU TRAVAIL DE 🎯 90200 FAITE AU PASSAGE
    // =========================================================================
    // Ce que Bren a établi le 3e : la vue de bataille peint chaque homme par
    // `h.etat` et `h.camp` SEULS (`couleurDe`, l. 5528‑5531) ; `h.l1` ne paraît
    // nulle part entre `peindre` et le relevé. Et quand une couche conduit, elle
    // s'exprime en RÉÉCRIVANT `h.etat`. Donc un homme sidéré par son corps est
    // peint, compté et additionné exactement comme un homme que sa tête tient en
    // ligne : tant que tout passe par `h.etat`, rien de ce qu'on branche n'est
    // distinguable à l'écran de ce qui existait avant.
    //
    // ON POSE DONC UN CHAMP QUE LA PEINTURE SAURA LIRE, et qui ne se confond
    // avec rien : `h.conduit` — laquelle des quatre tient les jambes de cet
    // homme à ce battement-ci. Un mot d'un répertoire fermé, du même genre que
    // `h.etat`, posé au même rythme que le reste, et que `couleurDe` peut
    // prendre le jour où l'on voudra voir la stack sur le plan. L'autre moitié
    // de 90200 est là-bas, et elle n'est pas de ce fichier.
    //
    // ⚠ RIEN NE LE LIT AUJOURD'HUI, ET C'EST EXACTEMENT CE QUI REND CETTE PASSE
    // SÛRE : aucune conduite ne change, l'étalon du four ne peut pas bouger. Le
    // jour où la peinture le lira, on verra la stack sans lui avoir donné la
    // main — ce qui est l'ordre honnête des deux gestes.
    //
    // C'EST L'INSTANT DE 🔒 90360, ET IL EST À MOITIÉ VRAI. `h.l1` vient d'être
    // posé au battement d'à côté, `h.l2` à l'instant : ces deux-là sont frais
    // ensemble. `h.l3` date du dernier ordre reçu et `h.l4` du dernier pillage —
    // ils sont ce qu'ils sont. La main les lit tels quels, ce qui est encore la
    // lecture la plus juste possible aujourd'hui, et il faut le savoir en lisant
    // `h.conduit`.
    const M = QC();
    if (M) {
      const q = M.pas({ l1: h.l1, l2: r, l3: h.l3, envie: h.l4 },
                      h.conduitEtat || (h.conduitEtat = {}), ctx.temps);
      if (h.conduit !== q.jambes.main) {
        h.conduit = q.jambes.main;
        h.conduitDepuis = ctx.temps;
      }
      h.conduitBras = q.bras.main;
      h.conduitPhrase = q.phrase;
    }
    return r;
  }

  const API = { observer, RAYON_COMPTE, RAYON_VU, SONDE_S, sonder, pilote: false };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.BatailleReflexion = API;
})();
