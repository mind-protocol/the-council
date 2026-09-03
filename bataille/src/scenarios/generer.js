/**
 * Scénarios / Générer — les aides PARTAGÉES de mise en place : le vivier de
 * noms (déterministe, réutilisé par unité) et le ban en rangs. Toujours de
 * la pure donnée dérivée arithmétiquement — jamais de rng ici (le
 * déterminisme du scénario ne dépend d'aucun tirage).
 */

// Le VIVIER : les noms des bans générés (déterministe, réutilisé par unité).
const VIVIER = [
  'Aubry', 'Baudri', 'Clérambault', 'Droart', 'Estienne', 'Fromond', 'Gaucher',
  'Herbert', 'Isembart', 'Jocelin', 'Lambert', 'Milon', 'Nivelon', 'Odon',
  'Pons', 'Quentin', 'Robert', 'Simon', 'Tancrède', 'Urbain', 'Vivien',
  'Warin', 'Ysoré', 'Adhémar', 'Bouchard', 'Constant', 'Dreux', 'Evrard',
  'Foucher', 'Girart', 'Huon', 'Ithier', 'Josserand', 'Lancelin', 'Mainard',
  'Norbert', 'Otran', 'Pépin', 'Rainouart', 'Savary',
];

export const nomGenere = (i) => (i < VIVIER.length ? VIVIER[i] : `${VIVIER[i % VIVIER.length]} le Jeune`);

/** Un ban en rangs : n hommes derrière leur chef, front vers capInitial. */
export const genererBan = (n, frontX, sens, largeurRang, yCentre = 10) => {
  const hommes = [];
  for (let i = 0; i < n; i++) {
    hommes.push({
      nom: nomGenere(i),
      pos: {
        x: frontX - sens * (1.2 + Math.floor(i / largeurRang) * 1.2),
        y: yCentre - ((largeurRang - 1) * 1.2) / 2 + (i % largeurRang) * 1.2,
      },
      escouade: i % Math.ceil(n / 5),
    });
  }
  return hommes;
};
