// navigation.js — LES ROUTES : par où un groupe passe, et jamais un homme seul.
//
// DEUXIÈME PIÈCE DU MONDE PHYSIQUE SORTIE DU MONOLITHE, et c'est un DÉPLACEMENT
// et non une réécriture : pas une ligne de ce qui suit n'a changé, commentaires
// compris.
//
// CE QU'ELLE EST. Un A* est calculé par DESTINATION ET GROUPE CONDUCTEUR, jamais
// par combattant — c'est le premier interdit du refactor, et il est déjà tenu :
// la mesure dit quatre calculs pour seize unités, soit 0,017 par homme. Les
// hommes suivent leur guide et la portion visible de la route ; aucun d'eux ne
// connaît le graphe de la ville.
//
// CE QU'ELLE NE FAIT PAS. Elle ne bouge personne. Elle rend des tracés et des
// points sur un tracé ; c'est le mouvement qui écrit une position, et la
// topologie qui dit ce qui est franchissable.
//
// ELLE PREND LA TOPOLOGIE, ELLE NE LA REFAIT PAS. Quatre de ses fonctions —
// `obstacleConnu`, `obstacleEn`, `obstaclePres`, `demiLibre` — viennent d'elle.
// Une deuxième géométrie serait la faute que le refactor interdit nommément :
// « le dessin, la navigation et la collision lisent la même autorité du bâti ».
//
// ⚠ CE QU'ELLE NE SAIT PAS FAIRE, ET QUI EST MESURÉ. La voirie ne dessert pas le
// dehors. Sur la porte de la Gadoue, la route rendue fait 223 m pour 110 m à vol
// d'oiseau, et son point le plus éloigné est à 164 m de la porte : elle s'écarte
// avant de revenir. `deplacer()` le documente de son côté depuis longtemps —
// « la réparation est dans la VOIRIE, qui doit sortir des murs et desservir les
// faubourgs par où l'assaut arrive ». Ce module hérite du défaut ; il ne le crée
// pas et ne le corrige pas.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleMondeNavigation = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  /** `creer(S, { EPAULE, topologie })` — les routes d'UNE simulation. */
  function creer(S, opts) {
    const EPAULE = (opts && opts.EPAULE) || 0.55;
    const T = (opts && opts.topologie) || {};
    const obstacleConnu = T.obstacleConnu, obstacleEn = T.obstacleEn;
    const obstaclePres = T.obstaclePres, demiLibre = T.demiLibre;

    function segmentMasqueBloque(sx,sy,tx,ty,largeurCorps) {
      if (!obstacleConnu()) return false;
      const dx=tx-sx,dy=ty-sy,d=Math.hypot(dx,dy)||1;
      const test=largeurCorps?obstaclePres:obstacleEn;
      for(let s=.8;s<d;s+=.8)if(test(sx+dx*s/d,sy+dy*s/d))return true;
      return false;
    }

    function traceLocale(pts) {
      if(!pts||pts.length<2)return null;
      const cum=[0],lar=[24];
      for(let i=1;i<pts.length;i++){
        cum[i]=cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);
        lar[i]=24;
      }
      return {pts,cum,lar,long:cum[cum.length-1]};
    }

    function assurerRouteRalliement(r,guide,u) {
      const cle=[r.deploiementId,u.id,r.x.toFixed(1),r.y.toFixed(1)].join(":");
      if(r.routeMasque&&r.routeMasque.clef===cle)return r.routeMasque;
      const bloque=segmentMasqueBloque(guide.x,guide.y,r.x,r.y,true);
      const pts=bloque?(cheminDePorte(guide.x,guide.y,r.x,r.y,true)||
        cheminDePorte(guide.x,guide.y,r.x,r.y,false)):null;
      r.routeMasque={clef:cle,direct:!bloque||!pts,trace:traceLocale(pts),s:0,
        dernierX:guide.x,dernierY:guide.y,avanceA:S.temps,recalculs:0,
        meilleurReste:Math.hypot(guide.x-r.x,guide.y-r.y)};
      if(bloque)u.cadre.calculs++;
      return r.routeMasque;
    }

    function cibleRalliementSurTrace(tr,s,p,h){
      const q=surTrace(tr,Math.max(0,Math.min(tr.long,s)));
      const ux=q[3],uy=-q[2];
      const demi=Math.max(.35,Math.min(2.4,demiLibre(h,q[0],q[1],ux,uy))-EPAULE);
      return [q[0]+q[2]*p.cote*demi,q[1]+q[3]*p.cote*demi,q];
    }

    function raccorderTraceFormation(tr, suite) {
      if (!suite || suite.length < 2) return tr;
      const pts = tr && tr.pts ? tr.pts.map((p) => p.slice()) : [];
      const lar = tr && tr.lar ? tr.lar.slice() : pts.map(() => 24);
      for (const p of suite) {
        const precedent = pts[pts.length - 1];
        if (precedent && Math.hypot(precedent[0] - p[0], precedent[1] - p[1]) < .2)
          continue;
        pts.push([p[0], p[1]]); lar.push(24);
      }
      if (pts.length < 2) return tr;
      const cum = [0];
      for (let i=1;i<pts.length;i++)
        cum[i]=cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);
      return { pts, lar, cum, long:cum[cum.length-1] };
    }

    // Une route d'échelon va jusqu'à son vrai but. Le graphe viaire peut finir
    // au bord d'une rue : la petite couture sur le masque appartient alors au
    // MÊME calcul du parent. Elle ne doit pas être redemandée par chaque
    // vintaine quand celle-ci atteint le dernier nœud du graphe.
    function calculerRouteFormation(guide, d, clef) {
      // Sur un terrain d'épreuve, la fonction d'obstacle est l'autorité entière.
      // Un segment libre ne doit surtout pas retomber sur le graphe des rues de
      // la ville cachée sous la scène.
      if (S.terrainEpreuve && !segmentMasqueBloque(guide.x,guide.y,d.x,d.y,false))
        return traceLocale([[guide.x,guide.y],[d.x,d.y]]);
      let tr=S.J.chemin(S.voirie,[guide.x,guide.y],[d.x,d.y],clef)||null;
      const p=tr&&tr.pts&&tr.pts.length ? tr.pts[tr.pts.length-1]
        : [guide.x,guide.y];
      if(Math.hypot(p[0]-d.x,p[1]-d.y)<.35)return tr;
      let suite=cheminDePorte(p[0],p[1],d.x,d.y);
      if((!suite||suite.length<2)&&!segmentMasqueBloque(p[0],p[1],d.x,d.y,false))
        suite=[[p[0],p[1]],[d.x,d.y]];
      return raccorderTraceFormation(tr,suite);
    }

    function surTrace(tr, s) {
      const pts = tr.pts, cum = tr.cum;
      let a = 0, b = cum.length - 1;
      while (a < b - 1) { const m = (a + b) >> 1; if (cum[m] <= s) a = m; else b = m; }
      const p = pts[a], q = pts[Math.min(a + 1, pts.length - 1)];
      const l = Math.max(1e-6, cum[Math.min(a + 1, cum.length - 1)] - cum[a]);
      const t = Math.max(0, Math.min(1, (s - cum[a]) / l));
      const dx = (q[0] - p[0]) / l, dy = (q[1] - p[1]) / l;
      // La largeur du tronçon qu'on foule, si le chemin la porte — voir
      // `chemin()` dans `journee.js`. Un vieux tracé en cache peut ne pas
      // l'avoir : on rend zéro, et l'appelant retombe sur son plancher.
      const w = tr.lar ? tr.lar[Math.min(a + 1, tr.lar.length - 1)] : 0;
      return [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, -dy, dx, w];
    }

    // Le graphe des rues dépose parfois une unité au bord du pâté, sans relier
    // les vingt derniers mètres jusqu'à l'huis. Ce petit BFS ne connaît que le
    // masque local ; il se paie une fois par unité et par bâtiment, puis tous
    // les hommes suivent leur guide sur la même trace.
    function cheminDePorte(sx, sy, tx, ty, largeurCorps) {
      // Quatre-vingts mètres permettent de contourner un grand pâté au lieu de
      // conclure « pas de chemin » parce que la porte est de l'autre côté. Cela
      // reste une recherche locale, payée une fois pour toute la vintaine.
      const pas = 1, marge = 80;
      // La grille doit contenir l'origine RÉELLE, pas son arrondi au mètre. À
      // l'angle d'une façade, 3341,6/667,8 devenait 3342/668 ; la reconstruction
      // partait de ce point fictif et le suiveur coupait ensuite le coin pour le
      // rejoindre. Le BFS jurait qu'une route existait, la locomotion refusait
      // son premier pas, puis le même A* était repayé deux fois. En décalant
      // l'origine d'un nombre ENTIER de pas depuis la vraie position, `debut`
      // coïncide exactement avec l'homme tout en gardant la même emprise.
      const x0 = sx - Math.ceil(Math.max(0, sx - tx) + marge);
      const y0 = sy - Math.ceil(Math.max(0, sy - ty) + marge);
      const nx = Math.ceil(Math.abs(tx - sx) + marge * 2) + 1;
      const ny = Math.ceil(Math.abs(ty - sy) + marge * 2) + 1;
      if (nx * ny > 90000) return null;
      const ix = (x, y) => Math.max(0, Math.min(nx - 1, Math.round(x - x0))) +
        Math.max(0, Math.min(ny - 1, Math.round(y - y0))) * nx;
      const debut = ix(sx, sy), fin = ix(tx, ty), precedent = new Int32Array(nx * ny);
      precedent.fill(-2); precedent[debut] = -1;
      const q = new Int32Array(nx * ny); let a = 0, z = 0; q[z++] = debut;
      // Quatre voisins : une diagonale entre deux angles libres peut couper le
      // coin du mur alors que les deux cases sont hors toit.
      const dirs = [[1,0],[-1,0],[0,1],[0,-1]];
      while (a < z && precedent[fin] === -2) {
        const c = q[a++], cx = c % nx, cy = (c / nx) | 0;
        for (const d of dirs) {
          const xx = cx + d[0], yy = cy + d[1];
          if (xx < 0 || yy < 0 || xx >= nx || yy >= ny) continue;
          const n = yy * nx + xx; if (precedent[n] !== -2) continue;
          const wx = x0 + xx * pas, wy = y0 + yy * pas;
          // Au ralliement le chemin porte une FORMATION : ses jalons ménagent
          // les épaules. Le franchissement d'un huis conserve au contraire son
          // chemin serré historique ; sinon on change aussi l'issue des fouilles.
          if (n !== fin && obstacleConnu() &&
              (largeurCorps ? obstaclePres(wx, wy) : obstacleEn(wx, wy))) continue;
          precedent[n] = c; q[z++] = n;
        }
      }
      if (precedent[fin] === -2) return null;
      const rev = []; let c = fin;
      while (c >= 0) { rev.push([x0 + c % nx, y0 + ((c / nx) | 0)]); c = precedent[c]; }
      rev.reverse(); rev.push([tx, ty]);
      return rev;
    }
    return { segmentMasqueBloque, traceLocale, assurerRouteRalliement,
             cibleRalliementSurTrace, raccorderTraceFormation,
             calculerRouteFormation, surTrace, cheminDePorte };
  }

  return { creer };
});
