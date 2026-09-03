/**
 * 🖥️ Interactions / Pilotage — LE CLIC DROIT : « va la ».
 *
 * C'est le seul endroit du jeu ou le joueur touche un homme directement. Le
 * bouton gauche reste le regard (pan, selection) ; le droit est la main.
 * Le menu contextuel du navigateur est supprime sur le canvas — il n'y a rien
 * a y faire, et il volerait le geste.
 */

/**
 * @param {Object} deps
 * @param {HTMLCanvasElement} deps.canvas
 * @param {ReturnType<import('../camera.js').creerCamera>} deps.camera
 * @param {(pos: {x, y}) => void} deps.allerA — l'ordre, en metres monde
 */
export function brancherPilotage({ canvas, camera, allerA }) {
  canvas.addEventListener('contextmenu', (ev) => ev.preventDefault());

  canvas.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 2) return;          // le droit, et lui seul
    ev.preventDefault();
    const r = canvas.getBoundingClientRect();
    allerA(camera.versMonde({ x: ev.clientX - r.left, y: ev.clientY - r.top }));
  });
}
