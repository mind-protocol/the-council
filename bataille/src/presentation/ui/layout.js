/**
 * 🖥️ UI / Layout — construit le DOM : canvas central plein écran, panneau
 * gauche (collapsible), panneau droit (inspecteur, fermé par défaut), barre
 * de transport. Structure seulement — les comportements vivent ailleurs.
 */

/**
 * @param {HTMLElement} racine
 * @param {{habillage?: boolean}} [opts] — `habillage: false` ne pose QUE le
 *   canvas : pas de panneaux, pas de barre. C'est la carte seule (route `/`),
 *   par opposition a la vue de travail complete (route `/bataille`).
 * @returns {{canvas: HTMLCanvasElement, panneauGauche: HTMLElement | null,
 *            panneauDroit: HTMLElement | null, barreTransport: HTMLElement | null}}
 */
export function monterLayout(racine, { habillage = true } = {}) {
  const canvas = document.createElement('canvas');
  canvas.className = 'scene';

  if (!habillage) {
    racine.append(canvas);
    return { canvas, panneauGauche: null, panneauDroit: null, barreTransport: null };
  }

  const panneauGauche = document.createElement('aside');
  panneauGauche.className = 'panneau-gauche';

  const panneauDroit = document.createElement('aside');
  panneauDroit.className = 'panneau-droit cache';

  const barreTransport = document.createElement('div');
  barreTransport.className = 'transport';

  racine.append(canvas, panneauGauche, panneauDroit, barreTransport);
  return { canvas, panneauGauche, panneauDroit, barreTransport };
}
