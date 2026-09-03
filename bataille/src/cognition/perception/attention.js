/**
 * 🧠 Perception / Attention — le budget compte des OBJETS, pas des hommes :
 * « mon chef », « mon escouade » (un tas), « mon unité » (un tas), « une unité
 * d'environ 20 piquiers », « le roi ». Un attroupement de 200 hommes coûte
 * 1 objet — le coût par homme est constant PAR CONSTRUCTION.
 * Priorité : les suivis dirigés (on cherche son chef du regard), puis MES
 * TAS étiquetés (on sait toujours où est sa ligne — et sa readiness se lit
 * en groupe), puis les CONTACTS (les corps à portée d'armes — SAILLANCE DE
 * LA MENACE : les livrées adverses d'abord), puis les tas anonymes par
 * proximité.
 */

/**
 * @param {Object} entree
 * @param {Array} entree.diriges — percepts corpsVu (suivis individuels)
 * @param {Array} entree.tas — percepts tasVu, avec d2 (distance² au moi)
 * @param {number} entree.budget — objets max
 * @returns {Array} percepts retenus, ordre stable
 */
export function retenir({ diriges, contacts = [], tas, budget }) {
  const proches = [...contacts].sort(
    (a, b) => (b.adverse ? 1 : 0) - (a.adverse ? 1 : 0) || a.d2 - b.d2 || a.id - b.id
  );
  const etiquetes = tas.filter((t) => t.etiquette !== null);
  const anonymes = tas
    .filter((t) => t.etiquette === null)
    .sort((a, b) => a.d2 - b.d2 || a.effectif - b.effectif);
  return [...diriges, ...etiquetes, ...proches, ...anonymes].slice(0, budget);
}
