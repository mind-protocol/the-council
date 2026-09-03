// LES RETOURS EN BULLES — ce qu'un homme reveille repond se voit sur son corps.
//
// La boite (boite-parole.js) envoie ; ceci ramene. Le siege parle depuis son
// corps ; l'homme a portee se reveille (⚙️ dispatch) et repond par le flux
// (`reponse`/`replique`, avec `pour: <siege>`). On sonde `/scene` — servi au
// siege par son jeton, deja filtre par le brouillard — et pour chaque nouvelle
// parole dont le locuteur a un corps sur ce champ, on pousse une bulle la ou il
// se tient (`conduire.dire`). Sur `/conseil`, le fil montre deja ces lignes
// dans le panneau ; ici c'est la rue qui parle, et c'est le seul endroit ou
// l'on voit QUI a repondu, et d'ou.
//
// On ne montre que ce qui ARRIVE apres l'ouverture : au premier passage on note
// tout ce qui est deja la sans le rejouer (sinon toute l'histoire poperait en
// bulles). Rien n'est consomme ni accuse : lire le flux ne l'epuise pas.
(function () {
  const vus = new Set();
  let amorce = false; // le premier passage marque l'existant sans le jouer

  const bulle = (it) => {
    const qui = it.locuteur_id;
    const texte = it.texte;
    if (!qui || !texte || !window.conduire || !window.conduire.dire) return;
    // corps sur ce champ ? sinon rien — on ne fait pas parler un absent.
    if (window.conduire.corpsDe(qui) == null) return;
    // une reponse est longue : on la borne pour la bulle, le fil garde le tout.
    window.conduire.dire(qui, texte.length > 140 ? texte.slice(0, 138) + '…' : texte, 6);
  };

  const sonder = () => fetch('/scene', { cache: 'no-store' })
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => {
      const items = (d && d.items) || [];
      for (const it of items) {
        const cle = it.ref || (it.type + ':' + (it.texte || '').slice(0, 24));
        if (vus.has(cle)) continue;
        vus.add(cle);
        // on ne bulle que ce qui ARRIVE apres l'amorce, et seulement la parole
        // d'un AUTRE : reponse/replique, jamais nos propres `vous` ni le hors
        // fiction. Le premier passage remplit `vus` sans rien jouer.
        if (amorce && (it.type === 'reponse' || it.type === 'replique')) bulle(it);
      }
      amorce = true;
    })
    .catch(() => {});

  sonder();
  setInterval(sonder, 2500);
})();
