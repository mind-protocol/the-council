/**
 * 🖥️ Interactions / Dépôt — réceptionne le drag & drop depuis la
 * bibliothèque (menu gauche) : dragover/drop sur le canvas, pixels → mètres
 * via la caméra, puis spawner(posMonde) — l'écrivain 2/2, via le câblage.
 */

/**
 * @param {Object} deps
 * @param {HTMLCanvasElement} deps.canvas
 * @param {ReturnType<import('../camera.js').creerCamera>} deps.camera
 * @param {(posMonde) => void} deps.spawner
 */
export function brancherDepot({ canvas, camera, spawner }) {
  canvas.addEventListener('dragover', (ev) => {
    ev.preventDefault();
    ev.dataTransfer.dropEffect = 'copy';
  });
  canvas.addEventListener('drop', (ev) => {
    ev.preventDefault();
    const r = canvas.getBoundingClientRect();
    spawner(camera.versMonde({ x: ev.clientX - r.left, y: ev.clientY - r.top }));
  });
}
