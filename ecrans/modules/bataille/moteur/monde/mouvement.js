// mouvement.js — CE QUI ECRIT UNE POSITION, et rien d'autre ne le fait.
//
// QUATRIEME PIECE SORTIE DU MONOLITHE. DEPLACEMENT et non reecriture : pas une
// ligne n'a change, commentaires compris — et ici plus qu'ailleurs ils comptent,
// parce qu'ils portent la lecon des murs traversés.
//
// CE QU'ELLE TIENT. `deplacer()` est le point de passage unique de toute
// ecriture de position : c'est ce qui fait la difference entre « la traversee
// est rare » et « la traversee est impossible ». Autour d'elle : l'allure et son
// inertie (`versLe`), le rail d'une route (`surLeRail`), la poussee entre corps
// (`pousser`), la grille de voisinage (`semer`, `caseDe`, `autour`) et
// l'orientation du fer (`tourner`).
//
// ⚠ ELLE N'EST PAS LE SEUL ECRIVAIN DE `h.vit`, ET IL FAUT LE SAVOIR. La branche
// de deroute, restee dans `bataille2d.js`, ecrit `h.vit = h.v` directement — sans
// `montureCombat`, sans le plafond d'`ACCEL`. C'est de la que sort le 3,6 m/s des
// fuyards, et c'est pourquoi un piquier en deroute est plus rapide que la
// meilleure cavalerie du moteur. Mesure, non repare : la sonde de teleport ne le
// voit pas non plus, son plafond etant a huit metres par seconde.
//
// ELLE PREND LA TOPOLOGIE. `obstacleConnu`, `obstacleEn`, `obstaclePres` et
// `demiLibre` viennent d'elle : le dessin, la navigation et la collision lisent
// la meme autorite du bati, c'est la regle du refactor.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleMondeMouvement = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, opts) {
    opts = opts || {};
    const ACCEL = opts.ACCEL, AU_CONTACT = opts.AU_CONTACT, EPAULE = opts.EPAULE;
    const FREIN_PIED = opts.FREIN_PIED, FREIN_PRESSE = opts.FREIN_PRESSE;
    const MAILLE = opts.MAILLE, MARCHE = opts.MARCHE, MARGE_C = opts.MARGE_C;
    const MONTEE = opts.MONTEE, PRES_FIGURE = opts.PRES_FIGURE;
    const RAD = opts.RAD, RECUL = opts.RECUL;
    const T = opts.topologie || {};
    const obstacleConnu = T.obstacleConnu, obstacleEn = T.obstacleEn;
    const obstaclePres = T.obstaclePres, demiLibre = T.demiLibre;
    const hasardFuite = opts.hasardFuite, memeEspace = opts.memeEspace;
    const vigueur = opts.vigueur;

    function tourner(h, dt) {
      if (!h.cx && !h.cy) return;
      // Il n'a pas encore de cap tenu : il prend celui qu'on lui donne. Le premier
      // battement d'un homme ne coûte pas une rotation.
      if (!h.fx && !h.fy) { h.fx = h.cx; h.fy = h.cy; h.w = 0; return; }
      const a = Math.atan2(h.fy, h.fx);
      let d = Math.atan2(h.cy, h.cx) - a;
      if (d > Math.PI) d -= 2 * Math.PI;
      else if (d < -Math.PI) d += 2 * Math.PI;

      const regime = ((h.arme && h.arme.pivot) || 200) * RAD
                   * (h.souplesse || 1) * vigueur(h);
      const accel = regime * MONTEE;
      const ecart = Math.abs(d);
      // La vitesse qu'on VOUDRAIT avoir ici : tout ce qu'on peut encore freiner.
      const veut = Math.min(regime, Math.sqrt(2 * accel * ecart)) * (d > 0 ? 1 : -1);
      const w = h.w || 0;
      const dw = Math.min(accel * dt, Math.abs(veut - w));
      h.w = w + (veut > w ? dw : -dw);

      const pas = h.w * dt;
      // Arrivé : on se cale et l'on tue la vitesse, sinon le reste de l'élan
      // repart de l'autre côté au battement suivant.
      if (Math.abs(pas) >= ecart) { h.fx = h.cx; h.fy = h.cy; h.w = 0; return; }
      const n = a + pas;
      h.fx = Math.cos(n); h.fy = Math.sin(n);
    }

    function presDe(x, y) {
      let n = null, dm = PRES_FIGURE * PRES_FIGURE;
      for (const f of S.figures) {
        const d = (f.x - x) ** 2 + (f.y - y) ** 2;
        if (d < dm) { dm = d; n = f; }
      }
      return n;
    }

    // ⚠ LA MARGE EST UNE PRÉFÉRENCE ET NE BLOQUE JAMAIS. C'est la leçon de la
    // passe d'avant, et elle a coûté une armée immobile : la marge posée comme
    // une CONDITION rétrécit chaque rue de cinquante-cinq centimètres, si bien
    // qu'une venelle d'un mètre cessait d'être franchissable. Trente-sept hommes
    // figés, dont douze dont la branche disait « il marche sur la porte » —
    // debout dans une ruelle, sans avancer d'un pouce, la colonne arrêtée
    // derrière eux.
    //
    // D'où les deux tours de la même boucle, et l'ordre compte : on cherche
    // d'abord un pas qui garde la largeur du corps, puis, s'il n'y en a pas, le
    // même pas au contact de la pierre. On ne peut donc JAMAIS bloquer plus que
    // ne bloquait le seul test du centre : au pire on se serre contre le mur, et
    // c'est ce que fait un homme dans une venelle étroite.
    function deplacer(h, nx, ny) {
      if (!obstacleConnu()) { h.x = nx; h.y = ny; return; }
      // Après le seuil, le masque extérieur représente le toit sous lequel
      // l'homme marche : il ne doit plus bloquer ses pas avant sa sortie par
      // l'huis.
      if (h.interieur != null) { h.x = nx; h.y = ny; return; }
      // Déjà dans la pierre — une pose ratée, un `degager` sans réponse : on ne
      // l'emmure pas, il sortira au premier pas.
      if (obstacleEn(h.x, h.y)) { h.x = nx; h.y = ny; return; }
      // À l'approche immédiate d'un huis, les hommes passent en file et peuvent
      // longer la pierre à moins d'une demi-épaule. Le centre reste toujours
      // interdit dans le mur ; seule la marge de confort est relâchée.
      for (const dur of (h.passageEtroit ? [obstacleEn] : [obstaclePres, obstacleEn])) {
        if (!dur(nx, ny)) { h.x = nx; h.y = ny; return; }
        if (!dur(nx, h.y)) { h.x = nx; return; }
        if (!dur(h.x, ny)) { h.y = ny; return; }
      }
      // ---- ET CEUX QUI N'ONT NI L'UN NI L'AUTRE ----------------------------
      // ILS S'ARRÊTENT, ET IL FAUT SAVOIR QUE C'EST LE CAS. Un homme dont le pas
      // plein, le pas en x et le pas en y entrent tous les trois dans la pierre
      // est dans une POCHE : relevé sur les quatre hommes figés devant la porte
      // du Roi, cinq des huit directions bouchées, libre au sud-ouest seulement —
      // et la porte au nord-est. Pour l'atteindre il doit d'abord s'en éloigner.
      //
      // AUCUNE RÈGLE LOCALE NE SORT DE LÀ, et l'on a essayé : glissement sur la
      // tangente du mur, puis mémoire du côté qu'on longe. Ni l'un ni l'autre n'a
      // libéré un seul homme, parce que sortir d'une poche demande de savoir où
      // l'on va — c'est-à-dire un chemin, pas un réflexe.
      //
      // ET LE RAIL D'A* NE LES SAUVE PAS — essayé, mesuré, retiré. Les états qui
      // roulent sur un rail ne se figent jamais, ceux qui visent en ligne droite
      // se figent : la conclusion semblait écrite. Mais `J.chemin` depuis ces
      // hommes-là vers leur verrou rend un tracé de DEUX POINTS sur cent dix
      // mètres — c'est-à-dire le segment droit, faute d'itinéraire. Le graphe des
      // rues ne dessert pas le dehors. Les cinquante
      // nœuds de voirie à cent vingt mètres de là sont proches et déconnectés —
      // la proximité n'est pas la connexité, et l'on ne valide un graphe qu'en
      // essayant d'aller quelque part.
      //
      // La réparation n'est donc ni ici ni dans la branche de la porte : elle est
      // dans la VOIRIE, qui doit sortir des murs et desservir les faubourgs par
      // où l'assaut arrive. Tant qu'elle ne le fait pas, un homme du dehors n'a
      // pas de chemin, et une poche de faubourg l'arrête. C'est un défaut qu'on
      // préfère voir : avant, il traversait la maison.
    }

            // au-delà, ce n'est plus une rue, c'est une place
    // POSER UN HOMME SUR SON RAIL, sans le mettre dans un mur et sans le faire
    // descendre du rail. Ce n'est pas `deplacer` : là on ne fait pas un pas, on
    // rejoint une position absolue calculée sur la trace de l'A*, et glisser
    // dessus décrocherait l'homme de sa colonne. On rentre donc l'écart à l'axe
    // — c'est toujours l'axe qui est le plus dégagé — au lieu de refuser le pas.
    function surLeRail(h, q, cote) {
      const ux = q[3], uy = -q[2];               // le long de la voie
      // La formule est celle d'avant, à ceci près que la demi-largeur du tronçon
      // est le plus petit du RELEVÉ et du MASQUE. Une rue n'est large que de ce
      // qu'elle a de plus étroit.
      const demi = Math.max(0.35,
        Math.min((q[4] || 3) / 2, demiLibre(h, q[0], q[1], ux, uy)) - EPAULE);
      for (let e = demi; ; e *= .5) {
        const nx = q[0] + q[2] * cote * e, ny = q[1] + q[3] * cote * e;
        if (e < .3 || !obstacleConnu() || !obstaclePres(nx, ny)) { h.x = nx; h.y = ny; break; }
      }
      h.surVoie = true; h.tx = ux; h.ty = uy;
    }

    function caseDe(x, y) {
      let i = Math.floor(x / MAILLE) - S.gI0, j = Math.floor(y / MAILLE) - S.gJ0;
      // Un déroutant court à quatre cents mètres hors la porte, et rien
      // n'interdit qu'un jour il aille plus loin : on borne au lieu de sortir du
      // tableau. La boîte étant taillée sur les vivants, ce garde-fou ne sert
      // qu'aux positions absurdes.
      if (i < 0) i = 0; else if (i >= S.gCol) i = S.gCol - 1;
      if (j < 0) j = 0; else if (j >= S.gLig) j = S.gLig - 1;
      return j * S.gCol + i;
    }

    function semer() {
      let i0 = Infinity, j0 = Infinity, i1 = -Infinity, j1 = -Infinity;
      for (const h of S.hommes) {
        if (h.etat === "mort") continue;
        const i = Math.floor(h.x / MAILLE), j = Math.floor(h.y / MAILLE);
        if (i < i0) i0 = i; if (i > i1) i1 = i;
        if (j < j0) j0 = j; if (j > j1) j1 = j;
      }
      if (i0 === Infinity) { S.gCol = S.gLig = 0; return; }   // plus personne debout

      S.gI0 = i0 - MARGE_C; S.gJ0 = j0 - MARGE_C;
      S.gCol = (i1 - i0) + 1 + MARGE_C * 2;
      S.gLig = (j1 - j0) + 1 + MARGE_C * 2;
      const nc = S.gCol * S.gLig;

      // On ne rend jamais les tampons : ils prennent la taille du pire pas et la
      // gardent. C'est la moitié du gain — une allocation par pas rendrait le
      // ramasse-miettes visible à l'œil nu sur une bataille de dix mille hommes.
      if (S.gDebut.length < nc + 1) S.gDebut = new Int32Array(nc + 1);
      if (S.gCorps.length < S.hommes.length) S.gCorps = new Int32Array(S.hommes.length);
      S.gDebut.fill(0, 0, nc + 1);

      // Première passe : combien d'hommes par case.
      for (let k = 0; k < S.hommes.length; k++) {
        const h = S.hommes[k];
        if (h.etat === "mort") continue;
        S.gDebut[caseDe(h.x, h.y)]++;
      }
      // Somme courante : `debut[c]` porte pour l'instant la FIN de la case c.
      let s = 0;
      for (let c = 0; c < nc; c++) { s += S.gDebut[c]; S.gDebut[c] = s; }
      S.gDebut[nc] = s;
      // Seconde passe, à REBOURS, en décrémentant : chaque case se remplit par la
      // fin, donc les hommes s'y retrouvent dans l'ordre du tableau `hommes` —
      // le même ordre que les listes d'avant. C'est ce qui rend la bataille
      // identique au pas près, et c'est la seule preuve qu'on n'a rien cassé.
      // Au passage, `debut[c]` redevient le DÉBUT de la case c, et `debut[c+1]`
      // en marque la fin.
      for (let k = S.hommes.length - 1; k >= 0; k--) {
        const h = S.hommes[k];
        if (h.etat === "mort") continue;
        S.gCorps[--S.gDebut[caseDe(h.x, h.y)]] = k;
      }
    }

    function autour(x, y, rayon, fn) {
      if (!S.gCol) return;
      const r = Math.ceil(rayon / MAILLE);
      const ci = Math.floor(x / MAILLE) - S.gI0, cj = Math.floor(y / MAILLE) - S.gJ0;
      // On rogne la fenêtre au lieu de ramener le centre dans la grille : une
      // case hors boîte est vide par construction, donc la sauter revient
      // exactement au `grille.get` qui rendait `undefined`.
      let i0 = ci - r, i1 = ci + r, j0 = cj - r, j1 = cj + r;
      if (i0 < 0) i0 = 0; if (i1 >= S.gCol) i1 = S.gCol - 1;
      if (j0 < 0) j0 = 0; if (j1 >= S.gLig) j1 = S.gLig - 1;
      for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
        const c = j * S.gCol + i;
        for (let k = S.gDebut[c], f = S.gDebut[c + 1]; k < f; k++) fn(S.hommes[S.gCorps[k]]);
      }
    }

    // Une route calculée sur le masque peut emprunter un passage où le centre
    // d'un homme passe mais où la marge de confort d'une demi-épaule ne passe
    // pas. Le planificateur le sait ; `deplacer`, lui, ne voit qu'un pas local.
    // Pendant le suivi de CETTE route seulement, on relâche donc la marge
    // `obstaclePres` tout en gardant le mur réel `obstacleEn` infranchissable.
    function versLeSurRouteMasque(h,x,y,v,dt){
      const avant=h.passageEtroit;h.passageEtroit=true;
      const reste=versLe(h,x,y,v,dt);
      h.passageEtroit=avant;return reste;
    }

    // ---- la machine du soldat -------------------------------------------------
    function pousser(h, dt) {
      // La séparation, et c'est tout ce qu'il y a de « physique » ici. Sans elle,
      // trois cents hommes tiennent dans un mètre carré devant la porte et le
      // bouchon — qui est le sujet — n'existe pas.
      // ELLE ÉTAIT MOLLE, ET C'EST POURQUOI ILS SE TRAVERSAIENT. Une force de
      // `6 × chevauchement × dt` met du temps à monter ; un homme qui charge à
      // trois mètres par seconde a déjà traversé son voisin quand elle devient
      // sensible. Trois ajouts, et aucun ne remplace la force douce — ils la
      // bornent :
      //
      //   LA BUTÉE DURE. Deux corps ne peuvent PAS être à moins d'une épaule l'un
      //   de l'autre. Ce n'est plus une force, c'est une correction de position :
      //   on les écarte, chacun de la moitié du recouvrement, à l'instant même.
      //   C'est ce qui rend la traversée impossible au lieu de la rendre chère.
      //
      //   LE FREIN. On compte la presse autour de lui et on la garde sur
      //   l'homme ; `versLe` s'en sert pour l'émousser. Un homme au milieu de six
      //   ne marche pas à la même vitesse qu'un homme seul dans une rue — et
      //   c'est ce qui donne au bouchon devant la porte son épaisseur.
      let sx = 0, sy = 0, presse = 0;
      let cedeX=0, cedeY=0, cedeForce=0, cedeA=null, cedeChef=false;
      let ennemiAuCoude=false;
      const pasH=Math.hypot(h.x-(h.px ?? h.x),h.y-(h.py ?? h.y));
      if(pasH>=.015)h.immobileDepuis=S.temps;
      const vraimentImmobile=S.temps-(h.immobileDepuis||0)>=.35;
      const hChef=!!(h.chefFormation||h.capitaine||h.tete);
      autour(h.x, h.y, EPAULE * 2.4, (o) => {
        if (o === h || !memeEspace(h, o)) return;
        const dx = h.x - o.x, dy = h.y - o.y;
        const d2 = dx * dx + dy * dy;
        const min = EPAULE * 1.8;
        if(o.camp!==h.camp){if(d2<min*min)ennemiAuCoude=true;return;}
        // CÉDER LE PASSAGE. On ne lit ni destination ni ordre : seulement deux
        // faits corporels du battement, l'un est arrêté et l'autre avance vers
        // lui. Le pas est perpendiculaire à la marche, donc il ouvre un chenal
        // sans pousser l'homme immobile devant la colonne.
        const pasX=o.x-(o.px ?? o.x),pasY=o.y-(o.py ?? o.y);
        // L'intention motrice compte aussi. Attendre que le chef ait déjà fait
        // trois centimètres par pas créait un verrou circulaire : pressé par ses
        // hommes il avançait moins que le seuil, donc personne ne cédait, donc
        // il restait pressé. `versLe` a déjà posé `pousse` et `vx/vy` avant cette
        // passe ; ils disent sans lire aucun ordre qu'un corps essaie réellement
        // d'avancer. On garde le déplacement constaté comme repli.
        const veutPasser=!!o.pousse&&Math.hypot(o.vx||0,o.vy||0)>.1;
        const ovx=veutPasser?(o.vx||0)*dt:pasX;
        const ovy=veutPasser?(o.vy||0)*dt:pasY;
        const opas=Math.hypot(ovx,ovy), oChef=!!(o.chefFormation||o.capitaine||o.tete);
        if(vraimentImmobile&&opas>.005&&d2<(EPAULE*2.4)*(EPAULE*2.4)&&(!hChef||oChef)){
          const ux=ovx/opas,uy=ovy/opas,rx=h.x-o.x,ry=h.y-o.y;
          const devant=rx*ux+ry*uy, lateral=-rx*uy+ry*ux;
          if(devant>-.1&&devant<1.45&&Math.abs(lateral)<.85){
            const force=oChef ? .95 : .38;
            if(force>cedeForce){
              const cote=Math.abs(lateral)>.04?Math.sign(lateral):(h.cote<0?-1:1);
              cedeX=-uy*cote;cedeY=ux*cote;cedeForce=force;
              cedeA=o;cedeChef=oChef;
            }
          }
        }
        if (d2 > min * min || d2 === 0) return;
        const d = Math.sqrt(d2);
        presse++;
        // La butée : au contact franc, on se décolle tout de suite et pour de
        // bon. La moitié chacun — l'autre fera sa moitié à son propre tour, et
        // les deux moitiés se rejoignent sans qu'on ait à trancher qui cède.
        //
        // ELLE VIBRAIT, et c'est ce qu'on voyait comme un frémissement de toute la
        // mêlée. Deux causes qui se nourrissent : la butée corrigeait la TOTALITÉ
        // du recouvrement d'un coup, pendant que la force douce continuait de les
        // pousser l'un vers l'autre — les deux se rendaient coup pour coup, vingt
        // fois par seconde, autour d'une position d'équilibre qu'aucune des deux
        // ne laissait tenir. Et comme on parcourt les hommes dans l'ordre du
        // tableau, le second voyait le premier DÉJÀ déplacé et sur-corrigeait.
        //
        // Deux bornes, et aucune ne touche à ce que la butée sert à empêcher :
        //   LA ZONE MORTE — sous un vingtième d'épaule de recouvrement, on ne
        //   corrige rien du tout. Deux corps qui se frôlent se frôlent.
        //   LA SOUS-RELAXATION — on ne rend que les trois cinquièmes de sa moitié.
        //   Le contact se résout en deux ou trois pas au lieu d'un seul, sans
        //   jamais dépasser la cible, donc sans rebond.
        // La traversée reste impossible : trois pas font un septième de seconde.
        if (d < EPAULE - EPAULE * .05) {
          const e = (EPAULE - d) * .5 * .6;
          deplacer(h, h.x + (dx / d) * e, h.y + (dy / d) * e);
        }
        sx += (dx / d) * (min - d); sy += (dy / d) * (min - d);
      });
      h.presse = presse;
      if(cedeA&&!ennemiAuCoude){
        const ax=h.x,ay=h.y;
        deplacer(h,h.x+cedeX*cedeForce*dt,h.y+cedeY*cedeForce*dt);
        if(Math.hypot(h.x-ax,h.y-ay)>.001){
          h.cedeDistance+=Math.hypot(h.x-ax,h.y-ay);
          h.cedePassageA=S.temps;h.cedePour=cedeA.debugId;h.cedePourChef=cedeChef;
        }
      }
      // SUR UNE VOIE, ON NE SE POUSSE QUE LE LONG DE LA VOIE. La séparation ne
      // connaît que les épaules des voisins et n'a jamais entendu parler d'un
      // mur : elle poussait donc dans les maisons tout ce qu'elle venait de
      // remettre dans la rue. On projette sa poussée sur la tangente — ce qui
      // n'ôte rien à ce qu'on lui demande, puisque ce qu'on veut d'elle dans une
      // rue est justement que les hommes se TASSENT les uns derrière les autres
      // au lieu de s'interpénétrer.
      if (h.surVoie) {
        const le = sx * h.tx + sy * h.ty;
        h.avance += le * 6 * dt;
        deplacer(h, h.x + h.tx * le * 6 * dt, h.y + h.ty * le * 6 * dt);
        return;
      }
      deplacer(h, h.x + sx * 6 * dt, h.y + sy * 6 * dt);
    }

    function versLe(h, bx, by, v, dt) {
      const dx = bx - h.x, dy = by - h.y, d = Math.hypot(dx, dy);
      if (d < .05) return 0;
      // ---- ON NE RECULE PAS À L'ALLURE OÙ L'ON AVANCE -------------------------
      // Le vecteur `fx/fy` existait depuis toujours et ne servait qu'à dessiner
      // le fer. Le voici mécanique, et c'est le premier des deux endroits.
      //
      // ON LE LIT AVANT DE L'ÉCRIRE, et c'est tout l'artifice : à l'entrée d'ici,
      // il porte encore le cap de la fin du battement précédent — celui que
      // `frapper` a tourné vers l'homme qu'on tape, ou que la branche du repli a
      // retourné vers l'ennemi qu'on ne quitte pas des yeux. Le comparer au
      // déplacement qu'on s'apprête à faire dit donc exactement ce qu'on veut
      // savoir : cet homme marche-t-il vers où il regarde, ou à reculons ?
      //
      // Trois allures pour une seule mesure : de face on va son train, de côté on
      // en perd un quart, à reculons on tombe à 45 %. Ce sont des chiffres
      // d'homme en armes et non des réglages — on ne court pas en arrière, on se
      // retire en tâtant le sol du talon.
      //
      // CE QUE ÇA PRODUIT, ET QU'ON NE POUVAIT PAS OBTENIR AUTREMENT : décrocher
      // en gardant la face devient un CHOIX QUI COÛTE. Celui qui se retire sans
      // quitter l'ennemi des yeux va deux fois moins vite que celui qui tourne le
      // dos — donc il se fait rejoindre, et c'est juste ; et celui qui tourne le
      // dos file, mais il offre son revers à qui le suit (voir `frapper`). La
      // déroute cesse d'être une option gratuite : les deux façons de partir se
      // paient, chacune dans sa monnaie.
      let ux = dx / d, uy = dy / d;
      // Un ordre donne une destination, pas le droit de traverser un foyer. Le
      // feu persistant infléchit donc le pas local sans remplacer la conduite
      // élue : l'homme continue sa mission, mais contourne ce qui brûle.
      if (h.menaceGenre === "incendie" && S.temps <= (h.menaceJus || -Infinity) &&
          (h.menaceExterieure || 0) > 0) {
        let ax = h.x - h.menaceX, ay = h.y - h.menaceY;
        let an = Math.hypot(ax, ay);
        if (an < .05) {
          const a = hasardFuite(h, 0x2c1b3c6d) * Math.PI * 2;
          ax = Math.cos(a); ay = Math.sin(a); an = 1;
        }
        ax /= an; ay /= an;
        const dot = ux * ax + uy * ay;
        const k = Math.min(1, (h.menaceExterieure || 0) * (.55 + Math.max(0, .45 - dot)));
        ux = ux * (1 - k) + ax * k; uy = uy * (1 - k) + ay * k;
        const un = Math.hypot(ux, uy) || 1; ux /= un; uy /= un;
      }
      if (h.fx || h.fy) {
        const cos = h.fx * ux + h.fy * uy;         // +1 de face, −1 à reculons
        v *= RECUL + (1 - RECUL) * (cos + 1) / 2;
      }
      // Le cheval n'invente aucune destination : il exécute seulement plus vite
      // le mouvement déjà choisi. À l'arrêt ou dans la presse, cet avantage
      // disparaît naturellement plus bas.
      if (h.montureCombat) v *= v > MARCHE * 1.25 ? 2.15 : 1.55;
      // ---- ON NE POINTE PAS SA LANCE OÙ VONT SES PIEDS ------------------------
      // Il veut regarder où il va — MAIS SEULEMENT S'IL N'EST PAS AU CONTACT, et
      // cette condition-là a coûté une cuisson entière avant d'être écrite.
      //
      // Sans elle : un homme qui tient sa ligne et va chercher l'épaule de son
      // voisin (`serrer`, qui passe par ici) posait son cap DE CÔTÉ, puis
      // `frapper` le reposait vers l'ennemi au battement suivant, puis `serrer`
      // le reprenait. Le fer balayait entre les deux sans jamais se caler dans
      // son secteur, donc le coup ne partait plus jamais : 1 700 hommes qui se
      // déhanchent en pointant à côté. Mesuré, et c'est net — 55 morts et 22
      // fuyards contre 103 et 124 à la cuisson d'avant l'inertie.
      //
      // Un homme en ligne fait face à l'ennemi et se déplace de côté ; il ne
      // tourne sa pointe que quand il marche pour de bon. La règle est celle-là,
      // et elle est plus juste que le bug qu'elle répare.
      if (!AU_CONTACT[h.etat]) { h.cx = ux; h.cy = uy; }
      // ---- LE CENTENAR EST MONTÉ — ET LE CHEVAL NE CHANGE PAS SON ALLURE ----
      // `h.monte` est posé sur le capitaine d'aile (voir `dresser`) et ne conduit
      // rien ici. Ce n'est pas un travail en cours : c'est une conclusion.
      //
      // LE CAPITAINE N'A AUCUNE BRANCHE DE DÉPLACEMENT À LUI. Il tient l'ordre de
      // son aile — « avancer / entrer » pour la première, « tenir / couvrir »
      // pour les autres — et il avance EN FORMATION avec ses hommes, comme
      // n'importe qui. Un facteur de vitesse posé dans `versLe` le ferait donc
      // sortir de son propre rang pendant l'approche, et comme la troupe
      // s'oriente sur sa bannière, c'est la colonne qu'on déferait. Un officier
      // monté qui accompagne une colonne va au pas de la colonne ; c'est vrai
      // dans le modèle comme ça l'était sur le terrain.
      //
      // ⚠ CE QUI PRÉCÈDE EST UN RAISONNEMENT, PAS UNE MESURE — et la première
      // version de ce commentaire prétendait le contraire, en citant un relevé du
      // banc à l'appui. Le banc était déjà rouge AVANT qu'on touche à ce fichier
      // (l'étalon du 24 à 18h05 contre un moteur modifié à 21h46 par une autre
      // plume) : la régression citée n'était pas la nôtre, et l'attribution était
      // fausse. On ne saura ce que le cheval coûte qu'une fois l'étalon reposé.
      //
      // CE QUE LE CHEVAL ACHÈTE VRAIMENT, ET QUI N'EST PAS DE LA VITESSE : il
      // peut QUITTER SA LIGNE ET Y REVENIR — un officier à pied qui la quitte est
      // perdu pour elle —, il se voit de loin, et un coureur peut donc le
      // trouver. C'est là qu'il faudra l'écrire, dans la course et le ralliement,
      // et jamais dans l'allure de marche.
      if (h.presse) v /= 1 + FREIN_PRESSE * h.presse;
      // Et l'on ne court pas à vide : un homme à bout ne charge plus, il avance.
      if (h.souffle !== undefined) v *= vigueur(h);
      // ---- ET LES JAMBES ONT UNE MASSE, ELLES AUSSI ---------------------------
      // Tout ce qui précède ne calcule plus une vitesse : ça calcule une vitesse
      // VOULUE. Un homme de quatre-vingts kilos avec trente de fer sur le dos ne
      // passe pas de l'arrêt à la charge en une image — il lui faut deux bonnes
      // secondes et une dizaine de pas, et c'est ce que tout le monde a vu qui
      // manquait : des lignes qui démarraient et s'arrêtaient au trait.
      //
      // Même forme que pour le fer (`tourner`), et pour la même raison : une
      // borne sur la DÉRIVÉE, jamais sur la valeur. `h.vit` est ce qu'il fait
      // réellement ; il rattrape ce qu'on lui demande à `ACCEL` près.
      //
      // DÉMARRER COÛTE PLUS CHER QUE S'ARRÊTER, et l'écart est franc : on plante
      // les talons bien plus vite qu'on ne lance quatre-vingts kilos. C'est ce
      // qui donne la bonne asymétrie — une charge se prépare, une halte est
      // immédiate — et ça évite qu'une ligne qui reçoit l'ordre de tenir continue
      // sur son erre pendant deux secondes.
      //
      // ⚠ `ACCEL` porte la souplesse ET la vigueur, alors que `v` porte déjà la
      // vigueur. Ce n'est pas un doublon : l'une dit à quelle vitesse il finit
      // par aller, l'autre en combien de temps il y arrive. Un homme vidé est
      // lent ET long à se mettre en route, ce qui n'est pas la même infirmité.
      const accel = ACCEL * (h.montureCombat ? 2.1 : 1) *
        (h.souplesse || 1) * vigueur(h);
      const vit = h.vit || 0;
      h.vit = vit < v ? Math.min(v, vit + accel * dt)
                      : Math.max(v, vit - FREIN_PIED * dt);
      h.vx = ux * h.vit; h.vy = uy * h.vit;
      // Il a poussé ce battement : `soldat` ne le freinera pas au suivant.
      h.pousse = true;
      const pas = Math.min(h.vit * dt, d);
      // B. LE SEUL PAS DE TOUTE LA LOCOMOTION. Marche, charge, retraite, fuite,
      // serrage de ligne : les vingt et un appelants finissent tous ici, et c'est
      // pour ça que le test se pose ici et nulle part ailleurs.
      deplacer(h, h.x + ux * pas, h.y + uy * pas);
      return d - pas;
    }
    return { tourner, presDe, deplacer, surLeRail, caseDe, semer, autour,
             versLeSurRouteMasque, pousser, versLe };
  }

  return { creer };
});
