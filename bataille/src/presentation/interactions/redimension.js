/**
 * 🖥️ Interactions / Redimension — poignée de redimensionnement d'un panneau
 * ancré à droite : on tire son bord GAUCHE. Générique (réutilisable le jour
 * d'un second panneau), pixels seulement — aucun métier.
 */

/**
 * @param {Object} deps
 * @param {HTMLElement} deps.panneau — le panneau à redimensionner
 * @param {number} [deps.largeurMin]
 * @param {number} [deps.partMax] — part max de la fenêtre (0..1)
 */
export function brancherRedimension({ panneau, largeurMin = 260, partMax = 0.6 }) {
  const poignee = document.createElement('div');
  poignee.className = 'poignee-redim';
  panneau.append(poignee);

  poignee.addEventListener('pointerdown', (down) => {
    down.preventDefault();
    poignee.setPointerCapture(down.pointerId);
    const bordDroit = panneau.getBoundingClientRect().right;
    const bouger = (ev) => {
      const largeur = Math.min(
        Math.max(bordDroit - ev.clientX, largeurMin),
        window.innerWidth * partMax
      );
      panneau.style.width = `${largeur}px`;
    };
    const lacher = () => {
      poignee.removeEventListener('pointermove', bouger);
      poignee.removeEventListener('pointerup', lacher);
    };
    poignee.addEventListener('pointermove', bouger);
    poignee.addEventListener('pointerup', lacher);
  });
}
