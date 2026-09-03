/**
 * 🖥️ UI / Menu gauche — panneau collapsible, organisé en sections.
 * Section « Bibliothèque » : un homme drag-and-droppable vers la scène
 * (le drop lui-même — pixels → mètres → spawn — est géré par interactions/depot.js).
 */

/** @param {HTMLElement} element — le panneau gauche du layout */
export function creerMenuGauche(element) {
  const entete = document.createElement('div');
  entete.className = 'pg-entete';
  const titre = document.createElement('span');
  titre.className = 'pg-titre';
  titre.textContent = 'Batailles';
  const bouton = document.createElement('button');
  bouton.textContent = '◀';
  entete.append(titre, bouton);

  const corps = document.createElement('div');
  corps.className = 'pg-corps';
  element.append(entete, corps);

  const basculer = () => {
    element.classList.toggle('replie');
    bouton.textContent = element.classList.contains('replie') ? '▶' : '◀';
  };
  bouton.addEventListener('click', basculer);

  return {
    /**
     * @param {string} titreSection
     * @param {HTMLElement} contenu
     * @returns {{deplier: Function, replier: Function}}
     */
    ajouterSection(titreSection, contenu) {
      const section = document.createElement('div');
      section.className = 'pg-section';
      const h = document.createElement('div');
      h.className = 'pg-section-titre';
      h.textContent = titreSection;
      h.addEventListener('click', () => section.classList.toggle('repliee'));
      const c = document.createElement('div');
      c.className = 'pg-section-contenu';
      c.append(contenu);
      section.append(h, c);
      corps.append(section);
      return {
        deplier: () => section.classList.remove('repliee'),
        replier: () => section.classList.add('repliee'),
      };
    },

    /** Replie/déplie le panneau entier. */
    basculer,

    /**
     * Fabrique une liste de cases à cocher (section « Calques »).
     * @param {{id: string, libelle: string, actif: boolean}[]} items
     * @param {(id: string, actif: boolean) => void} surChangement
     */
    creerCasesACocher(items, surChangement) {
      const liste = document.createElement('div');
      liste.className = 'coches';
      for (const item of items) {
        const ligne = document.createElement('label');
        ligne.className = 'coche';
        const case_ = document.createElement('input');
        case_.type = 'checkbox';
        case_.checked = item.actif;
        case_.addEventListener('change', () => surChangement(item.id, case_.checked));
        const texte = document.createElement('span');
        texte.textContent = item.libelle;
        ligne.append(case_, texte);
        liste.append(ligne);
      }
      return liste;
    },

    /**
     * Fabrique le contenu de la section Bibliothèque : l'élément « homme »
     * draggable. @param {(ev: DragEvent) => void} surDebutDrag
     */
    creerBibliotheque(surDebutDrag) {
      const item = document.createElement('div');
      item.className = 'biblio-item';
      item.draggable = true;
      const rond = document.createElement('div');
      rond.className = 'biblio-rond';
      const label = document.createElement('span');
      label.textContent = 'Homme';
      item.append(rond, label);
      item.addEventListener('dragstart', surDebutDrag);
      return item;
    },
  };
}
