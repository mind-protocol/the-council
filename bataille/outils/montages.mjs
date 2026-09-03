/**
 * MONTAGES — les données servies sous un préfixe d'URL, et où elles sont sur
 * le disque. Les villes cuites (masque + plan de cuire_ville.py) vivent DANS
 * le moteur, sous donnees/ville : c'est le serveur du jeu (routes/bataille.js)
 * qui l'a acté le 1er septembre, en sortant le moteur de l'archive. Le
 * chemin est résolu depuis ce fichier, pas depuis le dossier courant — la
 * fumée, le four et le serveur de dev tournent depuis des endroits
 * différents.
 */
import { fileURLToPath } from 'node:url';

const VILLES = fileURLToPath(new URL('../donnees/ville', import.meta.url));

export const MONTAGES = {
  'donnees/ville': VILLES,
};

/** Résout un chemin scénario (`donnees/ville/x.bin`) → chemin disque, ou null. */
export function resoudreMontage(chemin) {
  for (const [prefixe, racine] of Object.entries(MONTAGES)) {
    if (chemin.startsWith(prefixe + '/')) return racine + chemin.slice(prefixe.length);
  }
  return null;
}
