/**
 * 🖥️ Interactions / Navigation — déplacer le regard : molette = zoom centré
 * sur le curseur, drag (bouton gauche) = pan. Ne parle qu'à la caméra.
 */

/**
 * @param {Object} deps
 * @param {HTMLCanvasElement} deps.canvas
 * @param {ReturnType<import('../camera.js').creerCamera>} deps.camera
 */
export function brancherNavigation({ canvas, camera }) {
  canvas.addEventListener(
    'wheel',
    (ev) => {
      ev.preventDefault();
      const r = canvas.getBoundingClientRect();
      const pivot = { x: ev.clientX - r.left, y: ev.clientY - r.top };
      camera.zoomer(Math.pow(1.0015, -ev.deltaY), pivot);
    },
    { passive: false }
  );

  let precedent = null;
  canvas.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0) return;
    precedent = { x: ev.clientX, y: ev.clientY };
    canvas.setPointerCapture(ev.pointerId);
  });
  canvas.addEventListener('pointermove', (ev) => {
    if (!precedent) return;
    camera.deplacer({ x: ev.clientX - precedent.x, y: ev.clientY - precedent.y });
    precedent = { x: ev.clientX, y: ev.clientY };
  });
  canvas.addEventListener('pointerup', () => {
    precedent = null;
  });
}
