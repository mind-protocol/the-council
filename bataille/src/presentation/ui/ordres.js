/**
 * 🖥️ UI / Ordres — section du menu gauche : les trois ordres testables.
 * « Sur moi » (explicite), « En formation » (implicite — le récepteur déduit
 * le repère : première ligne auto-référente, sinon devant le locuteur),
 * « Repos ». ÉCHAFAUDAGE assumé : la commande injecte l'ordre en direct —
 * demain elle passera par le chef et la chaîne 📯.
 * @viz ordre-formation
 */

const MODES = [
  { mode: 'surMoi', libelle: '⚔ Sur moi' },
  { mode: 'nu', libelle: '⚔ En formation' },
  { mode: 'repos', libelle: '✕ Repos' },
];

/**
 * @param {{donnerOrdre: (mode) => void, modeActif: () => string}} commandes
 * @returns {{element: HTMLElement, rafraichir: Function}}
 */
export function creerOrdres(commandes) {
  const element = document.createElement('div');
  element.className = 'ordres';
  const boutons = MODES.map(({ mode, libelle }) => {
    const b = document.createElement('button');
    b.className = 'ordre-bouton';
    b.textContent = libelle;
    b.addEventListener('click', () => commandes.donnerOrdre(mode));
    element.append(b);
    return { mode, b };
  });

  return {
    element,
    rafraichir() {
      const actif = commandes.modeActif();
      for (const { mode, b } of boutons) b.classList.toggle('actif', mode === actif);
    },
  };
}
