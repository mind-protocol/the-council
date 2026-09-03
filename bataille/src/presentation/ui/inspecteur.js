/**
 * 🖥️ UI / Inspecteur — panneau droit, ouvert au clic sur un homme. Affiche
 * la machinerie interne (introspection 🧠 : {brain, etat, machine, details}),
 * rendu générique rafraîchi en continu : le graphe de la machine à états
 * (état courant en surbrillance), le POURQUOI (journal des transitions
 * justifiées), puis les détails. Il AFFICHE, il n'interprète pas.
 */

import { dessinerMachine } from './machine-graphe.js';
import { rendreEtatMajor } from './etat-major.js';

const formater = (v) => {
  if (v == null) return '—';
  if (typeof v === 'number') return v.toFixed(2);
  if (typeof v === 'object' && 'x' in v && 'y' in v)
    return `(${v.x.toFixed(1)}, ${v.y.toFixed(1)})`;
  return String(v);
};

const chip = (texte, classe = '') => {
  const c = document.createElement('span');
  c.className = `pd-chip ${classe}`;
  c.textContent = texte;
  return c;
};

/** Un compte en points (blessures, flèches) — au-delà de 10, le chiffre. */
const pips = (valeur, classe = '') => {
  const bloc = document.createElement('span');
  bloc.className = `pd-pips ${classe}`;
  const n = Math.max(0, Math.round(valeur));
  for (let i = 0; i < Math.min(n, 10); i++) {
    const p = document.createElement('span');
    p.className = 'pd-pip';
    bloc.append(p);
  }
  if (n > 10) bloc.append(chip(`×${n}`));
  if (n === 0) bloc.append(chip('0', 'eteinte'));
  return bloc;
};

/** Une petite barre qui se vide (compte à rebours). */
const tempo = (valeur, max) => {
  const barre = document.createElement('span');
  barre.className = 'pd-tempo';
  const rempli = document.createElement('span');
  rempli.className = 'pd-tempo-rempli';
  rempli.style.width = `${Math.max(0, Math.min(1, valeur / max)) * 100}%`;
  barre.append(rempli);
  return barre;
};

/**
 * @param {HTMLElement} element — le panneau droit du layout
 * @param {{surFermeture?: () => void}} [options]
 */
export function creerInspecteur(element, { surFermeture } = {}) {
  const entete = document.createElement('div');
  entete.className = 'pd-entete';
  const titre = document.createElement('span');
  const boutonFermer = document.createElement('button');
  boutonFermer.textContent = '✕';
  entete.append(titre, boutonFermer);
  const contenu = document.createElement('div');
  contenu.className = 'pd-contenu';
  element.append(entete, contenu);

  let idCourant = null;

  const api = {
    /** Ouvre le panneau sur un homme. @param {number} idCorps */
    ouvrir(idCorps) {
      idCourant = idCorps;
      titre.textContent = `Homme #${idCorps}`;
      element.classList.remove('cache');
    },

    /** @returns {number | null} l'homme inspecté */
    idOuvert() {
      return idCourant;
    },

    /** Met à jour l'affichage. @param {Object|undefined} introspection */
    rafraichir(introspection) {
      if (idCourant == null) return;
      contenu.innerHTML = '';
      if (!introspection) {
        contenu.textContent = 'aucune cognition attachée';
        return;
      }

      if (introspection.machine) {
        const cadre = document.createElement('div');
        cadre.className = 'pd-machine';
        cadre.append(dessinerMachine(introspection.machine));
        contenu.append(cadre);

        const pourquoi = document.createElement('div');
        pourquoi.className = 'pd-pourquoi';
        const titrePq = document.createElement('div');
        titrePq.className = 'pd-pourquoi-titre';
        titrePq.textContent = 'pourquoi';
        pourquoi.append(titrePq);
        for (const e of introspection.machine.journal.slice(0, 3)) {
          const quand = document.createElement('div');
          quand.className = 'pd-pourquoi-quand';
          quand.textContent = `il y a ${e.ilYaS.toFixed(1)} s — ${e.de} → ${e.vers}`;
          const raison = document.createElement('div');
          raison.className = 'pd-pourquoi-raison';
          raison.textContent = `« ${e.libelle} »`;
          pourquoi.append(quand, raison);
        }
        if (!introspection.machine.journal.length) {
          const rien = document.createElement('div');
          rien.className = 'pd-pourquoi-quand';
          rien.textContent = 'aucune bascule encore';
          pourquoi.append(rien);
        }
        contenu.append(pourquoi);
      }

      if (introspection.jauges) {
        const bloc = document.createElement('div');
        bloc.className = 'pd-jauges';
        for (const j of introspection.jauges) {
          const ligne = document.createElement('div');
          ligne.className = 'pd-jauge';
          const nom = document.createElement('div');
          nom.className = 'pd-jauge-nom';
          nom.textContent = j.nom;
          const barre = document.createElement('div');
          barre.className = 'pd-jauge-barre';
          const part = Math.max(0, Math.min(1, j.valeur / j.max));
          const danger = j.sens === 'hautMauvais' ? part : 1 - part;
          const rempli = document.createElement('div');
          rempli.className = 'pd-jauge-rempli';
          rempli.style.width = `${part * 100}%`;
          rempli.style.background =
            danger > 0.75 ? '#e05252' : danger > 0.45 ? '#e0a83f' : '#57c9b8';
          barre.append(rempli);
          for (const s of j.seuils ?? []) {
            const tick = document.createElement('div');
            tick.className = 'pd-jauge-seuil';
            tick.style.left = `${Math.min(100, (s / j.max) * 100)}%`;
            barre.append(tick);
          }
          ligne.append(nom, barre);
          bloc.append(ligne);
        }
        contenu.append(bloc);
      }

      if (introspection.etatMajor) {
        contenu.append(rendreEtatMajor(introspection.etatMajor));
      }

      // ── l'identité en pastilles : le brain, l'état coloré par FAMILLE
      // (obeir sarcelle, tuer rouge, fuir orange…) — l'état se lit sans lire
      const chips = document.createElement('div');
      chips.className = 'pd-chips';
      chips.append(chip(introspection.brain ?? '?'));
      if (introspection.etat) {
        chips.append(chip(introspection.etat, `pd-etat-${String(introspection.etat).split('.')[0]}`));
      }
      contenu.append(chips);

      // l'objectif : la phrase française, mise en avant (jamais réduite)
      if (introspection.objectifHumain) {
        const obj = document.createElement('div');
        obj.className = 'pd-objectif';
        obj.textContent = introspection.objectifHumain;
        contenu.append(obj);
      }

      for (const [cle, valeur] of Object.entries(introspection.details ?? {})) {
        if (valeur == null) continue;
        if (cle === 'souffle' && introspection.jauges) continue; // déjà en jauge
        if (cle === 'dernieresParoles') {
          for (const t of valeur.slice(0, 3)) {
            const p = document.createElement('div');
            p.className = 'pd-parole';
            p.textContent = `« ${t} »`;
            contenu.append(p);
          }
          continue;
        }
        const ligne = document.createElement('div');
        ligne.className = 'pd-ligne';
        const spanCle = document.createElement('span');
        spanCle.className = 'pd-cle';
        spanCle.textContent = cle;
        ligne.append(spanCle);
        if (cle === 'ordre') {
          ligne.append(chip(String(valeur), valeur === 'aucun' ? 'eteinte' : 'or'));
        } else if (cle === 'blessures' || cle === 'fleches') {
          ligne.append(pips(valeur, cle === 'blessures' ? 'rouge' : ''));
        } else if (cle === 'prochaineDecisionDansS') {
          ligne.append(tempo(valeur, 3));
        } else if (cle === 'escouadeCrue') {
          const span = document.createElement('span');
          span.className = 'pd-texte-cru';
          span.textContent = String(valeur);
          ligne.append(span);
        } else {
          ligne.append(chip(formater(valeur)));
        }
        contenu.append(ligne);
      }
    },

    fermer() {
      idCourant = null;
      element.classList.add('cache');
      surFermeture?.();
    },
  };

  boutonFermer.addEventListener('click', () => api.fermer());
  return api;
}
