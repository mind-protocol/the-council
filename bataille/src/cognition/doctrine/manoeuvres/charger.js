/**
 * 🧠 Doctrine / Manœuvres / Charger — la conclusion de la chasse : l'ennemi
 * est LOCALISÉ, on se forme, et sus à lui. Le succès est la MÊLÉE VUE
 * (auContact) — la manœuvre s'accomplit sans phase de repos : au contact,
 * l'état tuer a déjà préempté chaque homme. L'échec est l'ennemi PERDU
 * (croyance périmée) → l'arbitre fait tenir les rangs, et le ratissage
 * redevient applicable de lui-même — la chasse reprend, sans if/else.
 */

export const CHARGER = {
  nom: 'charger',
  applicabilite: ['ennemiLocalise', 'uniteAvecMoi', 'uniteAuFer'],

  /**
   * TROIS OPTIONS sur la forme ennemie CRUE : « de front » (toujours), et si
   * leur ligne se lit (cap + largeur perçus — la forme SE VOIT), « par la
   * gauche » / « par la droite » — contourner l'extrémité de leur ligne et
   * frapper le bout, là où les pointes ne sont pas tournées vers nous.
   * Le flanc ANNONCE son gain (qualite → gainDePosition) et son prix
   * (desordre : la marche qui tourne ; le chemin plus long paie déjà en
   * temps/fatigue). On se FORME sur la meilleure ligne (poste) — une charge
   * part d'un front constitué, pas du milieu du grumeau.
   */
  geometrie(situation) {
    const depart = situation.positionUnite;
    const ennemi = situation.positionEnnemie;
    if (!depart || !ennemi) return null;
    const poste = situation.meilleureLigne()?.centre ?? null;
    const options = [
      { nom: 'de front', chemin: [depart, ennemi], destination: ennemi, poste },
    ];

    const forme = situation.formeEnnemie; // {cap, largeur} crus, ou null
    if (forme?.cap !== undefined && forme.largeur) {
      const lat = { x: -Math.sin(forme.cap), y: Math.cos(forme.cap) }; // LEUR gauche/droite
      const marge = situation.margeDebord;
      for (const cote of [-1, 1]) {
        const bout = {
          x: ennemi.x + lat.x * cote * (forme.largeur / 2 + marge),
          y: ennemi.y + lat.y * cote * (forme.largeur / 2 + marge),
        };
        // le crochet : passer PAR le point de débord, frapper le bout de ligne
        const flanc = {
          x: ennemi.x + lat.x * cote * (forme.largeur / 2),
          y: ennemi.y + lat.y * cote * (forme.largeur / 2),
        };
        options.push({
          nom: cote > 0 ? 'par la gauche' : 'par la droite', // LEUR flanc
          chemin: [depart, bout, flanc],
          destination: flanc,
          poste,
          qualite: situation.qualiteDebord, // frapper un bout de ligne vaut cher
          desordre: situation.desordreDebord, // la marche qui tourne se paie
        });
      }
    }
    return options;
  },

  // l'agression pousse à charger ; la défense (demain : tenir) s'en méfie
  poids: { agression: 0.5, defense: -0.5 },

  phases: [
    { ordre: { verbe: 'EN_FORMATION' }, succes: 'uniteFormee', echec: 'ennemiPerdu', patience: 60 },
    { ordre: { verbe: 'CHARGER' }, succes: 'auContact', echec: 'ennemiPerdu', patience: 120 },
  ],
};
