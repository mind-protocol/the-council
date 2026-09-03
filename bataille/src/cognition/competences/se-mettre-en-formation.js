/**
 * 🧠 Compétences / Se mettre en formation — l'exécution de l'ordre. Le REPÈRE
 * vient du langage (resoudre-lieu : sur moi / première ligne auto-référente /
 * amorçage devant le locuteur), l'ancrage de la doctrine (rangs), la cible du
 * DRESSAGE : moyenne entre « près de mon ancre crue » et « mon slot dans
 * l'alignement de l'origine » — sans quoi l'erreur s'accumule en chaîne.
 * Fabrique STATEFULE (ancrages précalculés, anti-churn) au contrat commun :
 * agir(recu) → {intention, objectifHumain, cible, debug}.
 */

import { allerA, attendre } from '../intentions.js';
import { ancrageRangs } from '../doctrine/formes/rangs.js';
import { resoudreEnFormation, capDeDirection } from '../langage/resoudre-lieu.js';

export function creerSeMettreEnFormation({ representation, drill, params }) {
  const monId = representation.monId;
  const estChef = drill.ordreDrill[0] === monId;
  // deux drills possibles : locuteur dedans (sur moi) ou dehors (implicite)
  const ancrageAvec = ancrageRangs(drill.forme, drill.ordreDrill, monId);
  const ancrageSans = estChef ? null : ancrageRangs(drill.forme, drill.ordreDrill.slice(1), monId);
  for (const a of [ancrageAvec, ancrageSans]) {
    if (a && a.type !== 'tenir') representation.suivre(a.ancreId);
  }
  let derniereCible = null;
  // le repère ACQUIS pour l'ordre en cours : une fois la formation devenue
  // son propre repère (premiereLigne), on ne rechute jamais sur l'amorçage
  // (sinon un instant de netteté basse fait suivre le chef à toute l'unité)
  let repereRetenu = null;
  let dernierRecu = null;

  const projeter = (origine, base, off) => {
    const avant = { x: Math.cos(origine.cap), y: Math.sin(origine.cap) };
    const droite = { x: -avant.y, y: avant.x };
    return {
      x: base.x + droite.x * off.droite + avant.x * off.avant,
      y: base.y + droite.y * off.droite + avant.y * off.avant,
    };
  };

  return {
    /** @param {{ordre, emetteur}} recu @returns {{intention, objectifHumain, cible, debug}} */
    agir(recu) {
      if (recu !== dernierRecu) {
        dernierRecu = recu;
        repereRetenu = null; // nouvel ordre : le repère se ré-acquiert
      }
      let res = resoudreEnFormation(recu, representation, params, drill);
      const verbe = recu.ordre.verbe;
      const enBond = verbe === 'RATISSER' || verbe === 'RECULER';
      const capOrdre = enBond ? capDeDirection(recu.ordre.vers?.nom) : null;

      if (capOrdre !== null) {
        // BOND de formation : chaque cri désigne UN saut — je résous ma ligne
        // crue, je la déplace dans la direction criée, et je FIGE ce
        // ralliement (entendu une fois). L'unité s'y reforme en contournant
        // les obstacles (A*) ; la marche, c'est la SUCCESSION des cris.
        // RATISSER avance front devant ; RECULER décroche FRONT AU DANGER
        // (le cap de la formation reste opposé au mouvement).
        if (!repereRetenu && res) {
          const saut = verbe === 'RECULER' ? params.recul.saut : params.ratissage.sautSecteur;
          repereRetenu = {
            ...res,
            origine: {
              pos: {
                x: res.origine.pos.x + Math.cos(capOrdre) * saut,
                y: res.origine.pos.y + Math.sin(capOrdre) * saut,
              },
              cap: verbe === 'RECULER' ? capOrdre + Math.PI : capOrdre,
            },
          };
        }
        res = repereRetenu ?? null;
      } else if (res?.source === 'premiereLigne') {
        repereRetenu = res; // le meilleur repère : auto-référent, rafraîchi
      } else if (res?.source === 'devantLocuteur') {
        // le point de ralliement S'ENTEND UNE FOIS : on retient l'endroit
        // désigné à la réception — pas déplacé parce que le chef a tourné la
        // tête (sinon la formation danse autour de sa girouette)
        if (!repereRetenu) repereRetenu = res;
        res = repereRetenu;
      } else if (!res && repereRetenu) {
        res = repereRetenu; // mémoire plutôt que « je ne sais pas »
      }
      // (surLocuteur reste dynamique : « sur moi » SUIT le locuteur, c'est son sens)
      if (!res) {
        return { intention: attendre(), objectifHumain: 'je cherche celui qui commande', cible: null, debug: null };
      }
      const { origine, source } = res;
      const debugBase = { origine, source };
      const ancrage = res.chefDedans ? ancrageAvec : ancrageSans;
      const moi = representation.moi;

      // MON POSTE (croyance déposée par le rôle — tenir) : le guide s'y porte
      // AVANT de se planter ; la formation « sur moi » l'y suit d'elle-même
      const poste = representation.poste?.();
      const horsPoste =
        poste && moi.pos && Math.hypot(moi.pos.x - poste.x, moi.pos.y - poste.y) > params.formation.seuilArrive * 2;

      // je ne fais pas partie de cette formation (locuteur dehors, et c'est moi)
      if (!ancrage) {
        if (horsPoste) {
          return { intention: allerA(poste), objectifHumain: 'me porter à mon poste', cible: poste, debug: { ...debugBase, cible: poste } };
        }
        return { intention: attendre(), objectifHumain: "faire former l'unité devant moi", cible: null, debug: debugBase };
      }

      if (ancrage.type === 'tenir') {
        // le guide : il TIENT l'origine (sur moi : c'est le locuteur lui-même)
        if (source === 'surLocuteur' || !moi.pos) {
          if (horsPoste) {
            return { intention: allerA(poste), objectifHumain: 'me porter à mon poste', cible: poste, debug: { ...debugBase, cible: poste } };
          }
          return { intention: attendre(), objectifHumain: 'tenir ma position (la formation se range sur moi)', cible: null, debug: debugBase };
        }
        const d = Math.hypot(moi.pos.x - origine.pos.x, moi.pos.y - origine.pos.y);
        if (d > params.formation.seuilArrive) {
          return { intention: allerA(origine.pos), objectifHumain: 'prendre la tête de la formation', cible: origine.pos, debug: { ...debugBase, cible: origine.pos } };
        }
        return { intention: attendre(), objectifHumain: 'tenir la tête de la formation', cible: null, debug: debugBase };
      }

      const nomAncre = representation.nomDe(ancrage.ancreId);
      const objectifHumain =
        ancrage.type === 'derriere'
          ? `me mettre derrière ${nomAncre}`
          : `me mettre à ${ancrage.cote > 0 ? 'droite' : 'gauche'} de ${nomAncre}`;
      const ancre = representation.individuCru(ancrage.ancreId);
      if (!moi.pos || (!ancre?.pos && !origine.pos)) {
        return { intention: attendre(), objectifHumain: `${objectifHumain} (je ne le vois pas)`, cible: null, debug: debugBase };
      }

      // le DRESSAGE : ancre crue + offset local, moyenné avec l'alignement
      const surAncre = ancre?.pos ? projeter(origine, ancre.pos, ancrage.offset) : null;
      const surOrigine = projeter(origine, origine.pos, ancrage.offsetChef);
      const cible = surAncre
        ? { x: (surAncre.x + surOrigine.x) / 2, y: (surAncre.y + surOrigine.y) / 2 }
        : surOrigine;
      const d = Math.hypot(moi.pos.x - cible.x, moi.pos.y - cible.y);
      const debug = {
        ...debugBase,
        ancreId: ancrage.ancreId,
        nomAncre,
        ancrePosCrue: ancre?.pos ?? origine.pos,
        cible,
        capFormation: origine.cap,
        enPlace: d < params.formation.seuilArrive,
      };

      if (debug.enPlace) {
        derniereCible = cible;
        return { intention: attendre(), objectifHumain: `en place (${objectifHumain})`, cible, debug };
      }
      if (derniereCible && Math.hypot(cible.x - derniereCible.x, cible.y - derniereCible.y) < params.formation.seuilRecalcul) {
        return { intention: null, objectifHumain, cible, debug }; // anti-churn
      }
      derniereCible = cible;
      return { intention: allerA(cible), objectifHumain, cible, debug };
    },
  };
}
