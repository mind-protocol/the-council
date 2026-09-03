// toits.js — la forme d'une maison vue du dessus.
//
// Une pièce de sol `village` ne dessine pas un contour : ses points SONT les
// toits, un par point (docs/carte.md). Un point vaut [x, y] pour un hameau
// jeté sur le sol, [x, y, angle, façade] pour une maison qui a sa façade sur
// la rue, et [x, y, angle, façade, profondeur] quand elle n'est pas carrée —
// une lame étroite et profonde vend devant et stocke derrière, une grange en
// travers rentre le grain par le pignon. La forme dit le métier.
//
// C'est ici et pas dans terrain.js parce que le calque web (ecrans/modules/
// terrain.js) dessine exactement les mêmes rectangles : le jour où l'un des
// deux change, l'autre doit pouvoir se relire d'un coup d'œil.

/** La demi-façade et la demi-profondeur d'un toit, à partir de son point. */
export function gabarit(p) {
  const larg = p.length > 3 ? +p[3] : 6;
  return [larg / 2, (p.length > 4 ? +p[4] : larg * 0.78) / 2];
}

/**
 * Ajoute au chemin un rectangle fermé par toit. Repère en mètres du monde,
 * y vers le sud : un angle positif tourne dans le sens horaire à l'écran,
 * comme le `rotate` du calque web.
 */
export function cheminToits(path, pts) {
  for (const p of pts) {
    const [w, h] = gabarit(p);
    const a = ((p.length > 2 ? +p[2] : 0) * Math.PI) / 180;
    const ca = Math.cos(a), sa = Math.sin(a);
    const coins = [[-w, -h], [w, -h], [w, h], [-w, h]];
    coins.forEach(([u, v], i) => {
      const x = p[0] + u * ca - v * sa, y = p[1] + u * sa + v * ca;
      i ? path.lineTo(x, y) : path.moveTo(x, y);
    });
    path.closePath();
  }
  return path;
}
