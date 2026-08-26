// index.js — LA FAÇADE INTERNE DE LA SIMULATION.
//
// CE QU'ELLE EST AUJOURD'HUI, ET IL FAUT LE DIRE SANS FARD : une enveloppe. Elle
// délègue tout à `window.Bataille2d`, qui fait encore onze mille lignes et
// possède encore toutes les règles. Elle n'ajoute pas un comportement, ne
// change pas un chiffre, et le banc du moteur doit rendre exactement la même
// bataille avec ou sans elle. C'est voulu : le lot 1 du refactor est une
// PLOMBERIE, et une plomberie qui change le débit est une plomberie ratée.
//
// CE QU'ELLE SERA. Le sens de la flèche va s'inverser. Aujourd'hui `Moteur`
// appelle `Bataille2d` ; à mesure que le monde physique, le combattant, l'unité
// et le commandant sortent du monolithe, ce sont eux que `Moteur` appellera, et
// `Bataille2d` ne sera plus qu'un nom qu'on garde pour les vieux appelants
// jusqu'au dernier lot. Les consommateurs qu'on migre maintenant vers `Moteur`
// n'auront alors rien à changer — c'est toute la raison de la poser avant, et
// vide.
//
// CE QU'ELLE APPORTE DÈS MAINTENANT, ET QUI N'EXISTAIT PAS :
//
//   `Moteur.chaine`     le manifeste unique, pour vérifier ce qui est monté ;
//   `Moteur.contrats`   la forme des six objets échangés ;
//   `Moteur.traces`     le journal de décision, avec son horloge branchée ;
//   `Moteur.brancher()` le geste qui relie les trois au moteur qui tourne.
//
// L'HORLOGE EST LE SEUL VRAI SERVICE. Un journal dont les lignes n'ont pas
// d'heure de simulation ne se filtre pas « par seconde », et c'est précisément
// ce que le panneau de debug doit savoir faire. On la prend dans `etat().temps`
// du moteur qui tourne — une seule source, jamais une horloge de plus.
"use strict";

(function (racine, fabrique) {
  const api = fabrique(racine);
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BatailleMoteur = api;
})(typeof window !== "undefined" ? window : globalThis, function (racine) {

  const chaine   = racine && racine.BatailleChaine;
  const contrats = racine && racine.BatailleContrats;
  const traces   = racine && racine.BatailleTraces;

  /** Le moteur qui tourne, résolu À L'APPEL et jamais capturé au chargement. */
  function noyauSiLa() { return (racine && racine.Bataille2d) || null; }

  let branche = false;

  /**
   * `brancher` — poser l'horloge des traces sur le temps du moteur.
   *
   * Idempotent, et appelable avant que `bataille2d.js` soit arrivé : l'horloge
   * rend `null` tant qu'il n'y a pas de bataille, ce qui est la bonne réponse.
   * On le fait ici plutôt que dans `bataille2d.js` pour que le monolithe n'ait
   * pas à connaître le journal — c'est l'enveloppe qui câble, jamais le noyau.
   */
  function brancher() {
    if (branche || !traces) return branche;
    traces.reglerHorloge(() => {
      const n = noyauSiLa();
      if (!n || !n.etat) return null;
      try { const e = n.etat(); return e && typeof e.temps === "number" ? e.temps : null; }
      catch (_) { return null; }
    });
    branche = true;
    return true;
  }

  /**
   * `verifier` — ce qui manque à la chaîne, par son nom de fichier.
   *
   * Rend une liste, jamais une exception : un appelant qui veut mordre le fait
   * lui-même. C'est la version programmable du contrôle que `bataille2d.js`
   * fait déjà sur les couches, étendue à tout le manifeste.
   */
  function verifier(ensemble) {
    if (!chaine) return ["moteur/chaine.js"];
    return chaine.manquants(ensemble || "moteur", racine);
  }

  // -------------------------------------------------------------------------
  // LA DÉLÉGATION
  //
  // Une liste écrite à la main serait une neuvième liste à tenir, et l'on vient
  // d'en supprimer huit. On délègue donc par `Proxy` : toute clef inconnue est
  // cherchée sur le moteur qui tourne, au moment de l'appel. Le jour où une
  // fonction quitte le monolithe, on la pose ici et le Proxy cesse de la
  // chercher là-bas — sans qu'aucun appelant s'en aperçoive.
  //
  // Le repli sans `Proxy` n'existe pas : il est dans tous les navigateurs
  // depuis dix ans et dans Node depuis toujours. Une copie de clefs prise au
  // chargement serait pire que rien — elle figerait la surface d'un objet qui
  // n'est même pas encore posé.
  // -------------------------------------------------------------------------
  const propre = {
    chaine, contrats, traces,
    brancher, verifier,
    /** Le noyau, pour les rares appelants qui doivent le voir en face. */
    noyau: noyauSiLa,
    /** `vider` passe au noyau ET au journal : une nouvelle scène, un journal neuf. */
    vider: function () {
      if (traces) traces.vider();
      const n = noyauSiLa();
      return n && n.vider ? n.vider() : undefined;
    },
  };

  const facade = new Proxy(propre, {
    get(cible, clef) {
      if (clef in cible) return cible[clef];
      const n = noyauSiLa();
      if (!n) return undefined;
      const v = n[clef];
      return (typeof v === "function") ? v.bind(n) : v;
    },
    has(cible, clef) {
      if (clef in cible) return true;
      const n = noyauSiLa();
      return !!(n && clef in n);
    },
    ownKeys(cible) {
      const n = noyauSiLa();
      const tout = new Set(Reflect.ownKeys(cible));
      if (n) Reflect.ownKeys(n).forEach((k) => tout.add(k));
      return Array.from(tout);
    },
    getOwnPropertyDescriptor(cible, clef) {
      if (clef in cible) return Reflect.getOwnPropertyDescriptor(cible, clef);
      const n = noyauSiLa();
      if (n && clef in n) return { configurable: true, enumerable: true, value: n[clef] };
      return undefined;
    },
  });

  brancher();
  return facade;
});
