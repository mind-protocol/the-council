/**
 * 🖥️ UI / Scénarios — section du menu gauche : le sélecteur de scénario,
 * construit DYNAMIQUEMENT depuis le catalogue reçu (rien de codé en dur ici).
 * Choisir = recomposer un monde neuf — la commande est composée au bootstrap,
 * comme le spawn. @viz scenario-selecteur
 */

/**
 * @param {Object} commandes — composées au bootstrap
 * @param {{id: string, titre: string}[]} commandes.liste
 * @param {() => string} commandes.actif
 * @param {(id: string) => void} commandes.choisir
 * @returns {{element: HTMLElement}}
 */
export function creerScenarios({ liste, actif, choisir }) {
  const element = document.createElement('div');
  element.className = 'ordres'; // même gabarit que les ordres : pile de boutons
  for (const { id, titre } of liste) {
    const b = document.createElement('button');
    b.className = 'ordre-bouton';
    b.classList.toggle('actif', id === actif());
    b.textContent = titre;
    b.addEventListener('click', () => choisir(id));
    element.append(b);
  }
  return { element };
}
