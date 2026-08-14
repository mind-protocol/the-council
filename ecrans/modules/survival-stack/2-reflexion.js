// 2-reflexion.js — la deuxième couche.
//
//   la question, dans SA bouche : « comment me sortir de cette situation ? »
//   ce qu'elle produit             : une issue, cherchée
//
// CHERCHÉE VEUT DIRE QU'ELLE PREND DU TEMPS ET QU'ELLE PEUT NE RIEN TROUVER.
// C'est toute la différence avec la couche 1 : le corps ne cherche pas, il sait
// déjà — il recule, il se fige, il rue, et il le fait avant que l'homme ait eu
// le temps d'avoir un avis. Celle-ci regarde autour, compte, et décide de se
// sortir de là PAR QUELQUE PART. Quand il n'y a pas de quelque part, elle rend
// ça aussi, et c'est le résultat le plus important qu'elle produise.
//
// ─────────────────────────────────────────────────────────────────────────────
// CE QU'ON RAMASSE, ET POURQUOI C'ÉTAIT ÉPARPILLÉ
//
// La cascade de `soldat()` fait déjà ce travail — six fois, à six endroits, sans
// jamais dire que c'est le même. Relevé sur le disque, `bataille2d.js` :
//
//   `decider()`      2542‑2585  — dois-je céder le pas ? (hystérésis, contagion)
//   céder le pas     3222‑3271  — et VERS OÙ : moitié loin de lui, moitié vers
//                                 le centre des siens
//   le même calcul   3053‑3057  — DUPLIQUÉ à l'identique dans la branche
//                                 `recul` de la couche 1 : deux écritures d'une
//                                 seule idée, et c'est ainsi qu'on les fait
//                                 diverger sans le voir
//   la patience      3313‑3326  — éviter une mêlée qu'on ne gagne pas encore
//   `serrer()`       2416‑2429  — aller chercher l'épaule du voisin
//   la déroute       3128‑3166  — fuir, et par le chemin qu'on connaît
//
// SIX MORCEAUX, UNE SEULE QUESTION. Un homme qui recule, un homme qui attend
// le nombre et un homme qui se colle à son voisin ne font pas trois choses :
// ils cherchent la même issue, et ils ne diffèrent que par ce qu'ils ont trouvé.
//
// CE QU'ELLE N'EST PAS : elle ne choisit pas le verbe non plus. Elle ne dit pas
// « je me replie » — ça, c'est un ordre, et ça vient de la tête. Elle dit à quel
// point cet homme-ci, à cet endroit-ci, tient encore ou lâche, et de quel côté
// est le moins mauvais. La conduite reste à l'arbitre.
//
// ─────────────────────────────────────────────────────────────────────────────
// LE MANQUE QU'ON CORRIGE EN L'ÉCRIVANT — L'ISSUE PEUT NE PAS EXISTER
//
// `decider()` fait céder le pas sur le seul compte local : moins d'amis que
// d'ennemis plus la marge, il recule. Il ne regarde JAMAIS s'il y a quelque
// chose derrière lui. Un homme dos à un mur recule dans le mur ; une escouade
// coincée au fond d'une rue se disperse en poussant sur de la pierre.
//
// Or c'est le fait le mieux établi de tout ce qu'on modélise ici : **un homme
// acculé se bat**, et il se bat plus dur qu'un homme libre de partir. Pas par
// courage — par arithmétique. Fuir sans issue coûte le dos, et le dos est ce
// qui tue. La férocité du désespoir n'est pas un trait de caractère à tirer au
// sort, c'est ce que rend une recherche d'issue qui échoue.
//
// D'où la règle de cette couche, et elle est dure : **`degage` multiplie tout
// ce qui part.** Aucune sortie de ce module ne fait reculer un homme qui n'a
// nulle part où reculer. S'il n'a rien, il tient — et l'on saura pourquoi en
// lisant son `idee`, au lieu de le voir vibrer contre un mur.
//
// ─────────────────────────────────────────────────────────────────────────────
// TOUT EST DANS [−1, 1], entrées comme sorties, et toute borne est une
// SATURATION — `tanh`, jamais un `Math.min` posé après coup. Les fonctions sont
// pures : elles prennent un état, elles rendent un nombre, elles n'écrivent
// rien et n'appellent aucune autre couche. La seule exception assumée est
// `issue()`, qui rend deux composantes d'un cap unitaire : une direction n'est
// pas un scalaire, et l'écraser en scalaire coûterait la moitié de la question.
//
// EN OBSERVATION. Rien ici ne conduit encore : la cascade fait toujours le
// travail, et l'on ne remplace un morceau qu'après l'avoir regardé se tromper
// sur une vraie nuit. Le branchement se fait par l'arbitre, action ⚔️ 90311.
"use strict";
(() => {

  /** Lecture d'un signal, zéro par défaut — zéro étant l'ordinaire. */
  const G = (s, k, d) => (typeof s[k] === "number" ? s[k] : (d || 0));
  /** La part positive seule — « à quel point c'est bon », 0 si ça ne l'est pas. */
  const P = (v) => Math.max(0, v);
  /** La part négative seule, rendue positive — « à quel point c'est mauvais ». */
  const N = (v) => Math.max(0, -v);

  // ===========================================================================
  // LES SIGNAUX QU'ELLE LIT
  // ===========================================================================
  // Tous dans [−1, 1], tous nommés du côté favorable en +1 — la convention est
  // celle des couches 3 et 4, et elle n'est pas négociable : un signal qui
  // s'inverse d'une couche à l'autre est une faute qu'on ne retrouve jamais.
  //
  //   `nombre`   +1 les siens sont dix contre un · −1 il est seul contre dix
  //   `alarme`   +1 tout est calme · −1 le fer est sur lui
  //   `entame`   +1 il est intact · −1 il saigne
  //   `frais`    +1 il a des jambes · −1 il n'en peut plus
  //   `epaule`   +1 un des siens est à portée de bras · −1 personne à dix pas
  //   `degage`   +1 la retraite est ouverte derrière · −1 il est acculé
  //   `lachent`  +1 les siens tiennent · −1 ils reculent déjà autour de lui
  //   `trempe`   son tempérament : +1 il tient longtemps · −1 il lâche tôt
  //   `deja`     +1 il a déjà décidé de céder · −1 il tenait — l'hystérésis
  //
  // `degage` EST CELUI QUI N'EXISTE PAS ENCORE dans `bataille2d.js`, et c'est
  // pour lui qu'on écrit ce module. Il se mesure : trois sondes en éventail
  // derrière l'homme, sur le graphe de voirie ou sur le sol franchissable, à
  // la distance qu'il couvrirait en trois secondes. Tant qu'il n'est pas
  // fourni, il vaut 0 — « on ne sait pas » — et non +1 : supposer la retraite
  // ouverte est exactement l'erreur qu'on répare.

  // ===========================================================================
  // TENIR OU CÉDER LE PAS
  // ===========================================================================

  /** +1 il tient le pas, −1 il le cède. Reprend `decider()` (2542‑2585) en
   *  gardant ses trois mécaniques et en ajoutant la quatrième qui manquait.
   *
   *  LE NOMBRE DOMINE, et c'est juste : c'est ce qu'un homme voit le mieux et
   *  le plus vite. La contagion vient ensuite, et elle est forte — un homme
   *  dont les voisins reculent recule, même quand le compte lui donne raison ;
   *  c'est ainsi qu'une ligne cède d'un bout sans que personne l'ait décidé.
   *
   *  LA BLESSURE PÈSE MOINS QUE LA PEUR, et il faut le tenir contre l'intuition
   *  du genre : un homme entamé recule, mais un homme intact et terrifié recule
   *  davantage. Les deux canaux sont séparés (règle n°1), on ne les somme pas
   *  dans une jauge unique.
   *
   *  ET L'HYSTÉRÉSIS RESTE. `deja` vaut le `MARGE_TENIR = 1` de la cascade : il
   *  faut un homme de plus pour changer d'avis. Sans elle on obtient un
   *  clignotement à la frontière, qu'aucun œil ne lit comme une conduite. */
  function tient(s) {
    return Math.tanh(+0.85 * G(s, "nombre")
                   + 0.55 * G(s, "trempe")
                   + 0.40 * P(G(s, "alarme"))
                   - 0.60 * N(G(s, "alarme"))
                   - 0.45 * N(G(s, "entame"))
                   - 0.70 * N(G(s, "lachent"))
                   - 0.35 * G(s, "deja")
                   + 0.30 * P(G(s, "epaule")));
  }

  // ===========================================================================
  // ATTENDRE LE NOMBRE
  // ===========================================================================

  /** +1 il retient son coup et laisse venir, −1 il entre tout de suite. Reprend
   *  la patience (3313‑3326), où elle était une horloge en secondes —
   *  `4.5 − trempe*3` — donc aveugle à ce qui l'entoure.
   *
   *  ELLE N'EST PAS DE LA PEUR, et c'est la distinction qui la sauve : un homme
   *  qui attend le nombre est un homme QUI VA Y ALLER, et qui choisit le moment.
   *  Un homme qui a peur ne choisit rien. D'où le signe : l'alarme haute fait
   *  entrer ou fuir, elle ne fait pas patienter. Ce qui fait patienter, c'est
   *  d'être en infériorité alors qu'on tient encore debout.
   *
   *  ET ELLE S'ÉPUISE. `depuis` est le temps déjà passé à attendre, normalisé
   *  sur cinq secondes ; passé ce délai un homme entre, gagnant ou non, parce
   *  qu'aucun homme au monde ne reste trois minutes à deux mètres d'un ennemi
   *  sans rien faire. C'est la faute mesurée sur la vidéo : 5 à terre à 3'03. */
  function attend(s) {
    return Math.tanh(-0.90 * G(s, "nombre")
                   + 0.50 * G(s, "trempe")
                   + 0.40 * P(G(s, "entame"))
                   - 0.55 * N(G(s, "alarme"))
                   - 0.45 * N(G(s, "frais"))
                   - 1.10 * P(G(s, "depuis")));
  }

  // ===========================================================================
  // L'ÉPAULE DU VOISIN
  // ===========================================================================

  /** +1 il va se coller aux siens, −1 il prend du champ. Reprend `serrer()`
   *  (2416‑2429), qui était une double butée de distance sans motif.
   *
   *  C'EST CE QUI FAIT LES LIGNES, et ça ne se commande pas : le grégarisme
   *  ferme les rangs bien plus sûrement qu'un ordre. Un homme qui a peur se
   *  colle, un homme fatigué se colle, un homme acculé se colle surtout — s'il
   *  ne peut pas partir, il lui reste à ne pas être seul.
   *
   *  LE SIGNE S'INVERSE QUAND ON GAGNE : en supériorité franche et calme, on
   *  s'écarte pour envelopper. C'est ce que faisait la chasse à l'isolé sans le
   *  dire, et c'est la même idée vue du bon côté. */
  function appui(s) {
    return Math.tanh(-0.60 * G(s, "nombre")
                   + 0.65 * N(G(s, "alarme"))
                   + 0.40 * N(G(s, "frais"))
                   + 0.50 * N(G(s, "degage"))
                   - 0.35 * G(s, "trempe")
                   - 0.30 * P(G(s, "epaule")));
  }

  // ===========================================================================
  // L'ISSUE — DE QUEL CÔTÉ
  // ===========================================================================

  /** Le cap de la sortie, unitaire. Reprend le calcul de 3222‑3271, qui est
   *  aussi celui de 3053‑3057 — deux écritures d'une seule idée, réunies ici :
   *  MOITIÉ s'éloigner de ce qui frappe, MOITIÉ rejoindre les siens.
   *
   *  LA PONDÉRATION N'EST PLUS UNE MOITIÉ FIXE. Un homme calme se retire vers
   *  ses camarades — c'est un mouvement d'ordre. Un homme paniqué s'éloigne du
   *  fer sans regarder qui est derrière — c'est ainsi qu'une déroute part en
   *  éventail au lieu de refluer par la rue. Le mélange suit l'alarme, et le
   *  même code rend les deux comportements.
   *
   *  `versLuiX/Y` est le vecteur unitaire de l'homme vers ce qui le menace ;
   *  `versEuxX/Y` celui vers le centre des siens (`b.ax, b.ay` de `balance`).
   *  Rend `{x, y, force}` — `force` étant ce que vaut cette issue : nulle
   *  quand il est acculé, et c'est là que la couche répond « il n'y en a pas ». */
  function issue(s) {
    const alarme = G(s, "alarme");
    // De 0,35 (calme : on se replie sur les siens) à 0,90 (le fer est sur lui :
    // on ne regarde plus que ce qu'on fuit).
    const brut = 0.35 + 0.55 * N(alarme);
    let x = -brut * G(s, "versLuiX") + (1 - brut) * G(s, "versEuxX");
    let y = -brut * G(s, "versLuiY") + (1 - brut) * G(s, "versEuxY");
    const n = Math.hypot(x, y);
    if (n > 1e-6) { x /= n; y /= n; } else { x = 0; y = 0; }
    // ET VOICI LA MULTIPLICATION QUI TIENT TOUT LE MODULE. Acculé, l'issue ne
    // vaut rien, quelle que soit la beauté du cap qu'on vient de calculer.
    const force = P(G(s, "degage")) * (n > 1e-6 ? 1 : 0);
    return { x, y, force };
  }

  // ===========================================================================
  // LA PASSE
  // ===========================================================================

  /** Les trois nombres, le cap, et le mot qui les résume. `depuis` doit être
   *  fourni par l'appelant (le temps déjà passé à attendre, normalisé) : cette
   *  couche ne tient aucune horloge, comme les trois autres. */
  function pas(signaux) {
    const s = signaux || {};
    const r = { tient: tient(s), attend: attend(s), appui: appui(s),
                issue: issue(s) };
    // LA CONTRAINTE D'ACCULEMENT S'APPLIQUE ICI, une fois, sur ce qui part.
    // Sans issue, céder le pas n'est plus une option : `tient` remonte vers +1
    // à proportion de ce qui manque derrière. Un homme dos au mur se bat.
    const accule = N(G(s, "degage"));
    if (accule > 0) r.tient = Math.tanh(r.tient + 1.20 * accule);
    r.idee = idee(r, s);
    return r;
  }

  /** LE MOT, ET IL N'A AUCUN EFFET. On le lit dans la loupe à côté de la
   *  `branche` que la cascade a prise, et c'est comme ça qu'on verra cette
   *  couche se tromper avant de lui donner la main. */
  function idee(r, s) {
    if (N(G(s, "degage")) > 0.5 && r.tient > 0.2)
      return "il n'a nulle part où aller, alors il se bat";
    if (r.tient < -0.45 && r.issue.force > 0.3) return "il cherche à sortir de là";
    if (r.tient < -0.45) return "il voudrait partir et ne voit pas par où";
    // LA PATIENCE PASSE AVANT LE REPLI MOU, et l'épreuve du Bassin l'a montré :
    // en infériorité, intact et calme, `tient` descend à −0,33 et `attend`
    // monte à +0,69 — c'est un homme qui attend le nombre, pas un homme qui
    // cède. Testé dans l'autre ordre, le module disait « il cède le pas » de
    // l'homme le plus délibéré du champ.
    if (r.attend > 0.35) return "il attend que le nombre tourne";
    if (r.tient < -0.15) return "il cède le pas sans lâcher";
    if (r.appui > 0.40) return "il va chercher l'épaule du voisin";
    if (r.appui < -0.35) return "il prend du champ pour envelopper";
    return "il ne voit rien de mieux que ce qu'il fait";
  }

  // ===========================================================================
  const API = { tient, attend, appui, issue, pas, idee };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.Reflexion = API;
})();
