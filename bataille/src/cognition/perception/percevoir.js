/**
 * 🧠 Perception / Percevoir — l'assemblage : cercle 360° (pas de cône, on
 * regarde par-dessus son épaule), portée bornée, puis :
 * 1. attention DIRIGÉE : je cherche du regard mes suivis (chef, ancre) →
 *    percepts `corpsVu` individuels
 * 2. au CONTACT (rayonContact) : percepts INDIVIDUELS en plus des tas —
 *    on voit des hommes, plus une masse (readiness, cibles de frappe)
 * 3. le reste est agrégé en TAS (clusters.js)
 * 3. étiquetage par connaissance : tas majoritairement mon escouade →
 *    'escouade' ; mon unité → 'unite' ; sinon anonyme
 * 4. budget d'attention en OBJETS (attention.js)
 * Ne lit le monde que par la vue injectée ; n'écrit rien.
 */

import { regrouperEnTas } from './clusters.js';
import { retenir } from './attention.js';
import { analyserFormeTas } from './forme-tas.js';

/**
 * L'étiquetage par connaissance — d'abord l'ÉTRANGER (la livrée se VOIT :
 * un tas majoritairement d'une autre livrée = « ennemis ») ; puis « mon
 * escouade » seulement si le tas est MAJORITAIREMENT mon escouade ; un gros
 * tas qui les contient est « mon unité ». Partagé détail / masse.
 */
function etiqueterGroupe(groupe, contexte) {
  // on compte les GENS : un cheval sous un cavalier n'est pas un inconnu de
  // plus — sans ça une unité montée n'était jamais « mon unité » (moitié de
  // chevaux, jamais la majorité), mesuré sur la colonne de Gallipoli
  const gens = groupe.filter((v) => v.gabarit !== 'cheval' && !(v.gabarit == null && v.rayon >= 0.5));
  const n = gens.length || groupe.length;
  const nbAmis = gens.filter((v) => contexte.amisIds.has(v.id)).length;
  const nbUnite = gens.filter((v) => contexte.uniteIds.has(v.id)).length;
  const nbEtrangers = contexte.maLivree
    ? groupe.filter((v) => v.livree !== contexte.maLivree).length
    : 0;
  let etiquette = null;
  if (nbEtrangers > groupe.length / 2) etiquette = 'ennemis';
  else if (
    contexte.amisIds.size > 0 &&
    nbAmis >= Math.ceil(contexte.amisIds.size / 2) &&
    nbAmis >= n / 2
  ) etiquette = 'escouade';
  else if (nbUnite > n / 2) etiquette = 'unite';

  // la livree DOMINANTE se voit — l'interpretation (ami/ennemi)
  // restera une croyance du recepteur, jamais un tag
  const parLivree = new Map();
  for (const v of groupe) parLivree.set(v.livree, (parLivree.get(v.livree) ?? 0) + 1);
  const livree = [...parLivree.entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))[0][0];
  return { etiquette, livree };
}

/**
 * @param {Object} deps
 * @param {{posDe, autourDe, tous}} deps.vuePerception — vue 🌍 (snapshot du tick).
 *   `tous` sert le regroupement PARTAGE de l'horizon (voir plus bas).
 * @param {{perception: {portee, budgetAttention, chainageTas}}} deps.params
 */
export function creerPercevoir({ vuePerception, params }) {
  const { portee, budgetAttention, chainageTas, rayonContact } = params.perception;

  // ── LES TAS DU LOINTAIN SONT OBJECTIFS, DONC PARTAGES ─────────────────────
  //
  // `percevoirMasses` ramenait tout ce qui tient dans 400 m — sur un theatre
  // plus petit, TOUT LE MONDE — et le regroupait par chainage, ce qui est en
  // O(n²), une fois PAR HOMME. Soit ~0,25 · n³ operations par seconde.
  // Mesure (coding/sonde-horizon.mjs) : l'horizon coutait 26 % du pas a mille
  // corps et 60 % a deux mille — la part double quand l'effectif double, la
  // signature du cube.
  //
  // Or mille hommes qui regroupent le meme millier de corps avec le meme
  // chainage trouvent mille fois LES MEMES TAS. Un tas lointain n'a jamais ete
  // une croyance privee : ce qui est prive, c'est la distance, la visee et
  // l'etiquette (ami, ennemi, inconnu) — et tout cela reste calcule par homme.
  //
  // On regroupe donc une fois pour tous, et on rafraichit a la cadence de
  // l'horizon lui-meme : c'est « un coup d'oeil », pas une surveillance.
  let tasPartages = null;
  let depuisRegroupement = Infinity;
  const PERIODE_REGROUPEMENT_S = 1 / (params.perception.masse.cadence.moyenneHz * 4);

  const regrouperLeMonde = () => {
    const tous = (vuePerception.tous?.() ?? []).filter((v) => v.posture !== 'gisant');
    tasPartages = regrouperEnTas(tous, params.perception.masse.chainage).map((groupe) => {
      const barycentre = {
        x: groupe.reduce((s, v) => s + v.pos.x, 0) / groupe.length,
        y: groupe.reduce((s, v) => s + v.pos.y, 0) / groupe.length,
      };
      const bilan = bilanGroupe(groupe);
      const etendue =
        groupe.reduce((mx, v) => Math.max(mx, Math.hypot(v.pos.x - barycentre.x, v.pos.y - barycentre.y)), 0) +
        0.35;
      const m = params.perception.masse;
      const effectif = Math.max(m.arrondiEffectif, Math.round(groupe.length / m.arrondiEffectif) * m.arrondiEffectif);
      return { groupe, barycentre, bilan, etendue, effectif };
    });
    depuisRegroupement = 0;
  };
  // le POIDS DE GABARIT : un corps pèse sa taille, pas une tête — un homme
  // vaut 1, un cheval ~1,7, un oiseau ~0,9. C'est ce poids que lisent la
  // visibilité des masses et l'équilibre perçu (jamais un type).
  const poidsDe = (v) => (v.rayon ?? params.rayonHomme) / params.rayonHomme;
  const bilanGroupe = (groupe) => ({
    poids: groupe.reduce((s, v) => s + poidsDe(v), 0),
    // l'allure du groupe SE VOIT : le plus rapide donne la fermeture possible
    vitesse: groupe.reduce((m, v) => Math.max(m, v.vitesse ?? 0), 0),
    // l'altitude moyenne — un tas en vol est cru LÀ-HAUT
    z: groupe.reduce((s, v) => s + (v.z ?? 0), 0) / groupe.length,
  });

  return {
    tick(dt) {
      depuisRegroupement += dt;
    },

    /**
     * @param {number} id
     * @param {{suivis: number[], amisIds: Set, uniteIds: Set}} contexte
     *   — la connaissance qui guide l'attention (de la Représentation)
     * @returns {{posMoi: {x,y}, percepts: Array}}
     */
    percevoir(id, contexte) {
      const posMoi = vuePerception.posDe(id);
      // les gisants ne comptent ni dans les tas ni comme menaces — mais ils
      // SE VOIENT : le choc d'un mort est un percept (moral), hors budget
      // (un cadavre à ses pieds s'impose, il ne se retient pas)
      const tousVoisins = vuePerception.autourDe(id, portee);
      const gisantsVus = tousVoisins
        .filter((v) => v.posture === 'gisant')
        .map((v) => ({ id: v.id, livree: v.livree }));
      const voisins = tousVoisins.filter((v) => v.posture !== 'gisant');
      const suivis = new Set(contexte.suivis);

      // 1. attention dirigée
      const diriges = voisins
        .filter((v) => suivis.has(v.id))
        .map((v) => ({ type: 'corpsVu', id: v.id, pos: v.pos, cap: v.cap, posture: v.posture, livree: v.livree }));

      // 2. au contact : individus (EN PLUS des tas — les tas restent la
      // structure du groupe, les contacts donnent les corps un à un)
      const rc2 = rayonContact * rayonContact;
      const zMoi = posMoi.z ?? 0;
      const contacts = voisins
        .filter((v) => !suivis.has(v.id))
        .map((v) => ({ v, d2: (v.pos.x - posMoi.x) ** 2 + (v.pos.y - posMoi.y) ** 2 + ((v.z ?? 0) - zMoi) ** 2 }))
        .filter(({ d2 }) => d2 <= rc2)
        .map(({ v, d2 }) => ({
          type: 'contactVu',
          id: v.id,
          pos: v.pos,
          cap: v.cap,
          posture: v.posture,
          livree: v.livree,
          rayon: v.rayon, // le gabarit se voit au contact aussi
          adverse: contexte.maLivree != null && v.livree !== contexte.maLivree,
          d2,
        }));

      // 3. agrégation en tas du reste
      const restants = voisins.filter((v) => !suivis.has(v.id));
      const tas = regrouperEnTas(restants, chainageTas).map((groupe) => {
        const barycentre = {
          x: groupe.reduce((s, v) => s + v.pos.x, 0) / groupe.length,
          y: groupe.reduce((s, v) => s + v.pos.y, 0) / groupe.length,
        };
        const etendue =
          groupe.reduce((m, v) => Math.max(m, Math.hypot(v.pos.x - barycentre.x, v.pos.y - barycentre.y)), 0) + 0.35;

        const { etiquette, livree } = etiqueterGroupe(groupe, contexte);
        const bilan = bilanGroupe(groupe);

        return {
          type: 'tasVu',
          etiquette,
          livree,
          barycentre,
          etendue,
          effectif: groupe.length,
          ...bilan, // poids, vitesse, z — des faits qui se voient
          // la readiness se LIT en groupe : les lances levées se comptent
          prets: groupe.filter((v) => v.posture === 'pret').length,
          // la déroute se VOIT comme la readiness : les fuyards se comptent
          fuyards: groupe.filter((v) => v.posture === 'fuit').length,
          // la forme se voit (les lances) : cap + netteté, largeur/profondeur,
          // première ligne — absents si le groupe est une cohue
          ...analyserFormeTas(groupe, barycentre, params.perception.forme),
          d2: (barycentre.x - posMoi.x) ** 2 + (barycentre.y - posMoi.y) ** 2 + (bilan.z - zMoi) ** 2,
        };
      });

      // 4. budget en objets
      return { posMoi, percepts: retenir({ diriges, contacts, tas, budget: budgetAttention }), gisantsVus };
    },

    /**
     * L'HORIZON DE MASSE — le coup d'œil au loin, à cadence lente : au-delà
     * du détail on ne voit plus des hommes, des MASSES. Un groupe se voit
     * jusqu'à POIDS × porteeParHomme (le poids de gabarit, pas l'effectif :
     * vingt hommes, douze cavaliers ou UN corps immense se voient d'aussi
     * loin — continu, un homme seul retombe sur la portée de détail). De
     * loin on voit MOINS : effectif à la poignée, ni postures ni forme —
     * des champs ABSENTS, pas des zéros.
     * @param {number} id @param {Object} contexte
     * @returns {{posMoi: {x,y}, percepts: Array}}
     */
    percevoirMasses(id, contexte) {
      const m = params.perception.masse;
      if (!tasPartages || depuisRegroupement >= PERIODE_REGROUPEMENT_S) {
        regrouperLeMonde();
      }
      
      const posMoi = vuePerception.posDe(id);
      const tas = [];
      for (const t of tasPartages) {
        const { groupe, barycentre, bilan, etendue, effectif } = t;
        const d2 =
          (barycentre.x - posMoi.x) ** 2 + (barycentre.y - posMoi.y) ** 2 + (bilan.z - (posMoi.z ?? 0)) ** 2;
        if (d2 <= portee * portee) continue; // le champ proche appartient au détail
        const visee = Math.min(m.porteeMax, bilan.poids * m.porteeParHomme);
        if (d2 > visee * visee) continue; // trop petit pour se voir d'ici
        const { etiquette, livree } = etiqueterGroupe(groupe, contexte);
        tas.push({
          type: 'tasVu',
          lointain: true, // le percept se sait grossier
          etiquette,
          livree,
          barycentre,
          ...bilan, // poids, vitesse, z — la masse, son allure, son altitude
          etendue,
          effectif,
          d2,
        });
      }
      return { posMoi, percepts: retenir({ diriges: [], contacts: [], tas, budget: budgetAttention }) };
    },
  };
}
