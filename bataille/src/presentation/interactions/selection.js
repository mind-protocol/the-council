/**
 * 🖥️ Interactions / Sélection — clic sur la scène : hit-test sur les corps
 * (pixels → mètres via la caméra), sélectionne l'homme touché ou désélec-
 * tionne (clic dans le vide). Cohabite avec le pan : un clic = moins de
 * 4 px de mouvement entre down et up.
 */

/**
 * @param {Object} deps
 * @param {HTMLCanvasElement} deps.canvas
 * @param {ReturnType<import('../camera.js').creerCamera>} deps.camera
 * @param {(posMonde) => number | null} deps.corpsSous — hit-test (vue 🌍)
 * @param {(id: number | null) => void} deps.selectionner
 */
export function brancherSelection({ canvas, camera, corpsSous, selectionner }) {
  let depart = null;
  canvas.addEventListener('pointerdown', (ev) => {
    if (ev.button === 0) depart = { x: ev.clientX, y: ev.clientY };
  });
  canvas.addEventListener('pointerup', (ev) => {
    if (!depart) return;
    const distance = Math.hypot(ev.clientX - depart.x, ev.clientY - depart.y);
    depart = null;
    if (distance > 4) return; // c'était un pan, pas un clic
    const r = canvas.getBoundingClientRect();
    const posMonde = camera.versMonde({ x: ev.clientX - r.left, y: ev.clientY - r.top });
    selectionner(corpsSous(posMonde));
  });
}
