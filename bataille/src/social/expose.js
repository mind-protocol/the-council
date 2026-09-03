/**
 * 📯 Social — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Ouvre avec les unités (vérité sociale). Les Ordres et la Transmission
 * (voix, portée, délais) restent à venir — pour l'instant l'ordre
 * « en formation » est injecté en direct par le bootstrap (échafaudage
 * documenté dans cognition/expose.js).
 */

import { creerUnites } from './unites.js';

export function creerSocial() {
  const unites = creerUnites();

  return {
    // ── VUES / CONSTRUCTION ──
    unites: {
      creer: (desc) => unites.creer(desc),
      obtenir: (id) => unites.obtenir(id),
      duMembre: (idCorps) => unites.duMembre(idCorps),
    },
  };
}
