/**
 * 🖥️ UI / Transport — play/pause, x1/x2/x5. Traduit les clics en commandes
 * vers ⏱️ Orchestration (injectées), et reflète l'état courant (bouton actif).
 */

/**
 * @param {HTMLElement} element — conteneur des boutons
 * @param {{basculerPause: Function, reglerVitesse: Function, etat: Function}}
 *   commandes — transport de ⏱️ Orchestration
 */
export function creerTransport(element, commandes) {
  const boutonPause = document.createElement('button');
  boutonPause.addEventListener('click', () => commandes.basculerPause());
  element.append(boutonPause);

  const boutonsVitesse = [1, 2, 5].map((v) => {
    const b = document.createElement('button');
    b.textContent = `x${v}`;
    b.addEventListener('click', () => commandes.reglerVitesse(v));
    element.append(b);
    return { v, b };
  });

  return {
    /** Resynchronise l'affichage avec commandes.etat() (pause, vitesse). */
    rafraichir() {
      const e = commandes.etat();
      boutonPause.textContent = e.enPause ? '▶' : '⏸';
      for (const { v, b } of boutonsVitesse) b.classList.toggle('actif', e.vitesse === v);
    },
  };
}
