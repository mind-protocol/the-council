/**
 * 🖥️ Présentation / Renderer — canvas plein écran, compose les calques dans
 * l'ordre de la liste (dessous → dessus). Lit les vues, ne modifie jamais
 * l'état. Chaque calque est NOMMÉ : {id, dessiner(ctx, camera, vues), actif?}
 * — l'id est le contrat avec les Observables des CLAUDE.md, actif() le toggle
 * (absent = toujours dessiné).
 */

/**
 * @param {Object} deps
 * @param {HTMLCanvasElement} deps.canvas
 * @param {ReturnType<import('./camera.js').creerCamera>} deps.camera
 * @param {Array<{id: string, dessiner: (ctx, camera, vues) => void, actif?: () => boolean}>} deps.calques — ordre = z-order
 */
export function creerRenderer({ canvas, camera, calques }) {
  const ctx = canvas.getContext('2d');

  return {
    /** Une frame : efface, dessine chaque calque. @param {Object} vues */
    rendre(vues) {
      const dpr = window.devicePixelRatio || 1;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = '#14161c';
      ctx.fillRect(0, 0, canvas.width / dpr, canvas.height / dpr);
      for (const { dessiner, actif } of calques) {
        if (!actif || actif()) dessiner(ctx, camera, vues);
      }
    },

    /** Adapte le canvas à la fenêtre (taille CSS × devicePixelRatio). */
    redimensionner() {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = canvas.clientWidth * dpr;
      canvas.height = canvas.clientHeight * dpr;
    },
  };
}
