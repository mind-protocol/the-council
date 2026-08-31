// topologie.js — LE SOL, LE BÂTI, L'EAU : ce qu'un corps peut faire du terrain.
//
// PREMIÈRE PIÈCE DU MONDE PHYSIQUE SORTIE DU MONOLITHE, et c'est un
// DÉPLACEMENT et non une réécriture : pas une ligne de ce qui suit n'a changé,
// commentaires compris. Ces commentaires-là ne sont pas de l'ornement — ils
// portent trois fautes qu'il a fallu des semaines pour trouver, et qui se
// referaient toutes seules si on les perdait en chemin :
//
//   un homme POSÉ dans un mur (`degager`), qui y restait la nuit entière parce
//   qu'un homme qui tient ne bouge jamais ;
//   la marge de corps posée comme une CONDITION, qui rétrécissait chaque rue de
//   cinquante-cinq centimètres et immobilisait trente-sept hommes dans une
//   venelle ;
//   la rue plus large dans le relevé que dans le masque (`demiLibre`), où les
//   flancs de la colonne mordaient dans les façades.
//
// CE QU'ELLE EST. L'autorité de « qu'y a-t-il à cet endroit ». Elle répond, et
// ne bouge personne : aucune fonction d'ici n'écrit une position. Le mouvement,
// qui écrit, la lit — c'est la pièce suivante à sortir.
//
// TROIS ÉTATS ET NON DEUX, et c'est ce qui la rend sûre. Un point est libre,
// occupé, ou INCONNU : sans autorité chargée, `solConnu()` répond faux et
// personne ne prend « je ne sais pas » pour « c'est libre ». Le banc tourne
// parfois sans serveur ; un moteur qui immobiliserait une armée faute d'avoir
// pu lire un fichier serait pire que le défaut qu'il croit prévenir.
//
// ELLE PREND L'ÉTAT, ELLE NE LE POSSÈDE PAS. `creer(S)` lie ces fonctions à un
// état de simulation — celui de `moteur/etat.js` —, dont elle ne lit que cinq
// champs : `plan`, `terrainEpreuve`, `sousToit`, `sousEau`, `routesFormation`.
// C'est la forme que prendront les quatre extractions suivantes.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleMondeTopologie = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  /**
   * `creer(S, mesures)` — la topologie d'UNE simulation.
   *
   * `mesures.EPAULE` est la largeur d'un homme en armes. Elle vient de
   * `bataille2d.js`, qui la tient avec les autres mesures de corps : une
   * topologie n'a pas à savoir combien un homme est large, elle a à savoir
   * qu'il l'est.
   */
  function creer(S, mesures) {
    const EPAULE = (mesures && mesures.EPAULE) || 0.55;

    // Le dehors, c'est le côté opposé au cœur de la ville. On ne le devine pas
    // au jugé : les bornes du plan donnent le centre, et une porte regarde
    // toujours vers l'extérieur de ce centre-là.
    function dehors(p) {
      const [x0, y0, x1, y1] = S.plan.bornes;
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      const dx = p.x - cx, dy = p.y - cy, d = Math.hypot(dx, dy) || 1;
      return [dx / d, dy / d];
    }

    // Un point n'est franchissable que s'il est à la fois hors du bâti et hors
    // de l'eau. Une réponse positive exige les DEUX autorités : sans l'une des
    // deux, « libre » reste inconnu au lieu de devenir une permission implicite.
    const solConnu = () => !!S.terrainEpreuve || (!!S.sousToit && !!S.sousEau);
    const obstacleConnu = () => !!S.terrainEpreuve || !!S.sousToit || !!S.sousEau;

    const obstacleEn = (x, y) => S.terrainEpreuve
      ? !!S.terrainEpreuve.obstacle(x, y)
      : !!((S.sousToit && S.sousToit(x, y)) || (S.sousEau && S.sousEau(x, y)));

    const libreEn = (x, y) => !obstacleEn(x, y);

    function reglerTerrainEpreuve(spec) {
      if (spec == null) { S.terrainEpreuve = null; S.routesFormation.clear(); return null; }
      if (typeof spec.obstacle !== "function")
        throw new TypeError("terrain d'épreuve : obstacle(x,y) requis");
      S.terrainEpreuve = { id: spec.id || "terrain-epreuve", obstacle: spec.obstacle };
      S.routesFormation.clear();
      return { id: S.terrainEpreuve.id };
    }

    // =========================================================================
    // LES MURS, LUS PAR LES HOMMES
    // =========================================================================
    // LE MASQUE ÉTAIT JUSTE ET PERSONNE NE LE LISAIT. `sousToit` dit depuis
    // toujours si un point est sous une maison ; `libreEn` le retourne pour la
    // retraite ; et la locomotion finissait sur `h.x += (dx/d)*pas` sans un seul
    // test, à vingt et un sites d'appel. Les hommes ne traversaient pas les murs
    // par un défaut de trajectoire : pour eux, les murs n'existaient pas.
    //
    // Mesuré au vingtième, avant : 22 vivants sur 155 dans le bâti, dont neuf en
    // permanence — l'anneau du Donjon, posé par `r = 26 + (i%6)*2,2` autour du
    // donjon sans une seule lecture du masque, et qui y reste la nuit entière
    // parce qu'un homme qui `tient` ne bouge jamais. Trois fautes distinctes, et
    // trois réponses, dans l'ordre où elles mordent :
    //
    //   A. ON NE POSE PLUS UN HOMME DANS UN MUR (`degager`). C'est de la pose et
    //      non du mouvement, et ça rend d'un coup le résidu permanent.
    //   B. ON GLISSE LE LONG DU MUR (`poser`). Un seul point de passage pour
    //      toutes les écritures de position : la traversée devient impossible par
    //      construction au lieu d'être rare.
    //   C. LA RUE FAIT SA VRAIE LARGEUR (`demiLibre`). Le rail écarte les hommes
    //      de l'axe d'une fraction de la largeur DÉCLARÉE du tronçon ; là où le
    //      relevé est plus large que le masque, les flancs de la colonne mordent
    //      dans les façades. On mesure au pied.
    //
    // SANS AUCUNE AUTORITÉ, ON NE SAIT PAS — et « on ne sait pas » vaut « on
    // passe ». Avec une seule, la locomotion bloque déjà ce qu'elle connaît, mais
    // `libreEn` ne promet toujours pas que le reste du sol est libre. Le banc
    // tourne parfois sans serveur ; un moteur qui immobiliserait toute une armée
    // faute d'avoir pu charger un fichier serait pire que le défaut qu'on répare.

    // Le point libre le plus proche de celui qu'on visait. La ville densifiée
    // porte désormais des remises de dix mètres au fond des parcelles : quinze
    // mètres ne suffisent plus toujours à ressortir d'un îlot. Et seize rayons
    // laissaient passer ENTRE deux venelles étroites sans en essayer aucune.
    //
    // On parcourt donc le périmètre de chaque carré métrique : chaque case du
    // masque comprise dans les quatre-vingt-seize mètres est réellement essayée.
    // C'est la largeur maximale qu'un cœur d'îlot peut atteindre dans le semis ;
    // au-delà, `densifier.py` le traite comme un terrain et y perce une voie. Le
    // premier anneau qui répond gagne ; ce geste ne se paie qu'à la naissance
    // des hommes tombés sous un toit, jamais pendant la marche.
    const DEGAGE_MAX = 96;
    function degager(x, y) {
      if (!obstacleConnu() || !obstaclePres(x, y)) return [x, y];
      // DEUX PASSES, ET LA SECONDE EST UNE CONCESSION. On cherche d'abord une
      // place où l'homme tient de toute sa largeur ; à défaut — une venelle plus
      // étroite que deux épaules, un poste au pied d'un mur —, on se contente
      // d'un point hors de la pierre. Une place serrée vaut mieux qu'un homme
      // expédié quinze mètres plus loin parce que la marge manquait de dix
      // centimètres.
      for (const test of [obstaclePres, obstacleEn]) {
        if (!test(x, y)) return [x, y];
        for (let r = 1; r <= DEGAGE_MAX; r++) {
          for (let d = -r; d <= r; d++) {
            for (const [dx, dy] of [[d, -r], [r, d], [-d, r], [-r, -d]]) {
              const nx = x + dx, ny = y + dy;
              if (!test(nx, ny)) return [nx, ny];
            }
          }
        }
      }
      return [x, y];
    }

    // TOUTE ÉCRITURE DE POSITION PASSE PAR ICI. C'est ce qui fait la différence
    // entre « la traversée est rare » et « la traversée est impossible ».
    //
    // Le glissement est celui de tout le monde : si le pas complet entre dans un
    // mur, on essaie sa seule composante en x, puis sa seule composante en y. Un
    // homme qui longe une façade en diagonale garde donc sa vitesse le long du
    // mur au lieu de s'y coller — sans quoi une colonne s'arrête à la première
    // maison et le bouchon remonte sur trois cents hommes.
    //
    // ⚠ UN HOMME DÉJÀ DANS UN MUR A TOUJOURS LE DROIT DE BOUGER. On ne l'emmure
    // pas : `degager` a pu échouer, une pose peut avoir été faite ailleurs, et
    // un homme figé dans une maison pour la nuit est un défaut pire que celui
    // qu'on répare. Il sortira au premier pas qui tombe dehors.
    // ⚠ PAS `poser` : LE NOM EST PRIS l. 6479 par le montage du canvas dans la
    // page, et les deux déclarations vivent dans la même IIFE — la seconde écrase
    // la première en silence, si bien que le premier pas d'homme appelait
    // `hote.appendChild`. Quatrième collision de nom de ce fichier, et la
    // troisième à ne se voir qu'à l'exécution.
    // UN HOMME A UNE LARGEUR, ET LE MUR AUSSI DOIT LA VOIR. Tester le seul point
    // du milieu du corps laissait passer une faute qu'on ne voyait qu'à l'image :
    // le glissement colle l'homme à la surface, son centre reste libre, et son
    // épaule est dans la pierre. Mesuré après la première passe — 24 vivants sur
    // 146, seize pour cent de l'armée, à moins de vingt-huit centimètres d'une
    // façade, c'est-à-dire dedans.
    //
    // C'est la même largeur que celle dont les hommes se poussent entre eux
    // (`EPAULE`), et il n'y a pas de raison qu'une pierre soit plus tendre qu'un
    // voisin. Quatre points cardinaux à la demi-épaule : ce n'est pas un disque
    // exact, et il n'en faut pas un — la case du masque fait déjà un mètre.
    const RAYON = EPAULE / 2;
    function murPres(x, y) {
      return S.sousToit(x, y) ||
             S.sousToit(x + RAYON, y) || S.sousToit(x - RAYON, y) ||
             S.sousToit(x, y + RAYON) || S.sousToit(x, y - RAYON);
    }

    // Même largeur corporelle au bord de l'eau. Le nom distinct conserve la
    // différence utile : `murPres` sert encore aux diagnostics de maçonnerie,
    // tandis que la locomotion doit voir pierre ET eau.
    function obstaclePres(x, y) {
      return obstacleEn(x, y) ||
             obstacleEn(x + RAYON, y) || obstacleEn(x - RAYON, y) ||
             obstacleEn(x, y + RAYON) || obstacleEn(x, y - RAYON);
    }

    // LA DEMI-LARGEUR VRAIE SOUS SES PIEDS, en travers de la voie. Le tronçon
    // porte une largeur DÉCLARÉE (`q[4]`, venue du relevé des rues) ; là où le
    // masque est plus étroit — un auvent, une maison avancée, un relevé plus
    // vieux que le bâti —, la colonne s'étale dans les façades. On sonde à un
    // demi-mètre de part et d'autre et l'on garde le plus petit des deux côtés :
    // une rue n'est large que de ce qu'elle a de plus étroit.
    //
    // ON NE LE REFAIT PAS À CHAQUE BATTEMENT. La mesure est mise en cache sur
    // l'homme et refaite quand il a franchi deux mètres — soit une fois toutes
    // les secondes et demie à l'allure de marche. À deux mille cinq cents
    // hommes, c'est quelques dizaines de milliers de lectures de tableau par
    // seconde, c'est-à-dire rien.
    const SONDE_PAS = 0.5;
    const SONDE_MAX = 12;

    function demiLibre(h, x, y, ux, uy) {
      if (!obstacleConnu()) return SONDE_MAX;
      if (h.mesureDemi >= 0 &&
          (x - h.mesureX) ** 2 + (y - h.mesureY) ** 2 <= 4) return h.mesureDemi;
      let g = 0, d = 0;
      while (g + SONDE_PAS <= SONDE_MAX &&
             !obstacleEn(x - uy * (g + SONDE_PAS), y + ux * (g + SONDE_PAS))) {
        g += SONDE_PAS;
      }
      while (d + SONDE_PAS <= SONDE_MAX &&
             !obstacleEn(x + uy * (d + SONDE_PAS), y - ux * (d + SONDE_PAS))) {
        d += SONDE_PAS;
      }
      h.mesureX = x; h.mesureY = y; h.mesureDemi = Math.min(g, d);
      return h.mesureDemi;
    }
    return { dehors, solConnu, obstacleConnu, obstacleEn, libreEn,
             reglerTerrainEpreuve, degager, murPres, obstaclePres, demiLibre,
             RAYON, DEGAGE_MAX };
  }

  return { creer };
});
