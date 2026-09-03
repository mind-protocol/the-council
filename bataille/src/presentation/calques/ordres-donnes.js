/**
 * 🖥️ Calque ordres donnés — l'onde du clic droit : un anneau qui s'ouvre et
 * s'efface a l'endroit qu'on vient de designer.
 *
 * C'est de l'ACCUSE DE RECEPTION, pas un fait du monde : personne dans la
 * bataille ne voit ce cercle, il ne se sauvegarde pas, et il bat en temps
 * REEL — il s'anime meme en pause, parce qu'un geste du joueur doit repondre
 * quand le joueur le fait, pas quand la sim veut bien avancer.
 *
 * Ancre au MONDE et non a l'ecran : on peut deplacer la camera pendant que
 * l'onde s'ouvre, elle reste sur le pave qu'on a designe.
 *
 * @viz ordres-donnes
 */

const DUREE_MS = 550;
const RAYON_M = 2.2;   // la ou l'homme se considere arrive (cognition : ARRIVE_M)

export function dessinerOrdresDonnes(ctx, camera, vues) {
  const marques = vues.ordresDonnes?.() ?? [];
  if (!marques.length) return;
  const maintenant = performance.now();

  for (const m of marques) {
    const t = (maintenant - m.t0) / DUREE_MS;
    if (t < 0 || t > 1) continue;
    const e = camera.versEcran(m.pos);
    const ppm = camera.echelle();
    // l'onde part large et se referme sur le point : le geste DESIGNE,
    // il ne rayonne pas
    const rayon = RAYON_M * ppm * (1.5 - 0.5 * t);
    ctx.beginPath();
    ctx.arc(e.x, e.y, Math.max(2, rayon), 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(255, 216, 102, ${(1 - t) * 0.9})`;
    ctx.lineWidth = 2;
    ctx.stroke();

    // le point vise, qui reste net tout du long
    ctx.beginPath();
    ctx.arc(e.x, e.y, Math.max(1.5, 0.25 * ppm), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 216, 102, ${(1 - t) * 0.75})`;
    ctx.fill();
  }
}
