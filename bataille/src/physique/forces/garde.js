/**
 * ⚙️ Physique / Forces / Garde — la MESURE d'escrime : deux corps de livrées
 * ADVERSES se repoussent à distance de lance (centre à centre : allonge +
 * marge). C'est la menace de la pointe, lue comme un fait du corps (la livrée
 * est physique, comme le rayon — l'interprétation ami/ennemi reste une
 * croyance 🧠). La FENTE (🏃, pendant le geste de frappe) est ce qui perce la
 * garde : au repos les lignes se tiennent à portée, au coup elles se
 * pénètrent. Profil linéaire, intensités en m/s. O(n²) assumé.
 */

const clamp = (v, min, max) => Math.min(Math.max(v, min), max);

/**
 * ASYMÉTRIQUE par construction : chacun recule devant la pointe ADVERSE —
 * l'épéiste craint la pique à 4,7 m, le piquier ne craint l'épée qu'à 1,3 m.
 * C'est de cette asymétrie que la dynamique piques-qui-tiennent /
 * épées-qui-cherchent-l'entrée doit émerger, sans une ligne de plus.
 * @param {Iterable<Object>} tousCorps — vue 🌍 (pos, livree)
 * @param {Map<number, {x, y}>} forces — accumulateur partagé
 * @param {(id: number) => {allonge: number}} armeDe — vue ❤️ (la pointe se voit)
 * @param {number} marge — m, au-delà de l'allonge adverse
 * @param {number} intensite — m/s au contact
 */
export function ajouterGarde(tousCorps, forces, armeDe, marge, intensite, paires = null) {
  const ajouter = (id, fx, fy) => {
    const f = forces.get(id) ?? { x: 0, y: 0 };
    f.x += fx;
    f.y += fy;
    forces.set(id, f);
  };

  const surPaire = (ca, cb) => {
    if (ca.livree === cb.livree) return; // la garde ne vaut qu'entre adverses

    const dx = cb.pos.x - ca.pos.x;
    const dy = cb.pos.y - ca.pos.y;
    const d = Math.hypot(dx, dy);
    const ux = d > 1e-9 ? dx / d : 1;
    const uy = d > 1e-9 ? dy / d : 0;

    // ca recule devant la pointe de cb, cb devant celle de ca — chacun la
    // sienne. UN DOS EN FUITE NE MENACE PERSONNE : sa pointe ne tient plus
    // la mesure — c'est ce qui rend le fuyard rattrapable, et la curée
    // possible ; sa propre peur de la pointe adverse le pousse, elle, en avant
    const porteeA = cb.posture === 'fuit' || cb.posture === 'renverse' ? 0 : armeDe(cb.id).allonge + marge;
    if (d < porteeA) {
      const t = 1 - clamp(d, 0, porteeA) / porteeA;
      ajouter(ca.id, -ux * intensite * t, -uy * intensite * t);
    }
    const porteeB = ca.posture === 'fuit' || ca.posture === 'renverse' ? 0 : armeDe(ca.id).allonge + marge;
    if (d < porteeB) {
      const t = 1 - clamp(d, 0, porteeB) / porteeB;
      ajouter(cb.id, ux * intensite * t, uy * intensite * t);
    }
  };
  if (paires) {
    for (const [ca, cb] of paires) surPaire(ca, cb);
  } else {
    const corps = [...tousCorps];
    for (let a = 0; a < corps.length; a++) {
      for (let b = a + 1; b < corps.length; b++) surPaire(corps[a], corps[b]);
    }
  }
}
