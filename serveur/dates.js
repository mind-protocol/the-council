

// ---- les têtes : où l'on CROIT que sont les gens ------------------------
// `personnages.lieu_id` est la vérité, et la vérité n'a rien à faire sur une
// table de guerre. `etat/vues.json` porte l'autre moitié : la dernière position
// CONNUE du joueur, avec sa date et de quelle bouche il la tient. Ce module la
// projette en pièces de carte — et la fait vieillir, parce que le sel n'est pas
// la position, c'est son âge.
const JOURS_PAR_LUNE = 30, LUNES_PAR_AN = 12;
// Les dates s'écrivent de deux façons dans l'état : le triplet partout, et la
// forme courte « 129.3.22 » dans `mains.json`. On accepte les deux plutôt
// que de laisser une régie muette sur la moitié des fichiers.
const jourAbsolu = (d) => {
  if (typeof d === "string") {
    const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(d.trim());
    d = m ? { annee: +m[1], lune: +m[2], jour: +m[3] } : null;
  }
  return d && d.annee != null
    ? ((d.annee * LUNES_PAR_AN + (d.lune - 1)) * JOURS_PAR_LUNE) + (d.jour - 1) : null;
};

// Une nouvelle ne reste pas fraîche : de semaine en semaine, ce qu'on tenait
// pour sûr redevient un on-dit, puis se perd. Au-delà, on ne montre plus rien —
// une carte honnête montre aussi ses trous.
const PALIERS = [[7, null], [21, "rapportee"], [45, "rumeur"]];

function vieillir(certitude, age) {
  if (age == null) return certitude;
  for (const [seuil, degre] of PALIERS) if (age <= seuil) return degre || certitude;
  return null;                        // trop vieux : la tête sort de la table
}

const AGE_DIT = (n) => n <= 0 ? "aujourd'hui" : n === 1 ? "hier"
  : "il y a " + n + " jours";

function absolues(d) {
  if (!d) return null;
  return ((((d.annee || 0) * 12 + (d.lune || 0)) * 30 + (d.jour || 0)) * 1440)
    + (typeof d.minute === "number" ? d.minute : 0);
}

// cache d'une minute est un mensonge d'une minute.
function dateCourte(d) {
  if (!d) return "";
  if (typeof d === "string") return d;
  // `dernier_rapport` est tantôt une date nue, tantôt un rapport complet qui
  // porte la sienne. On ne veut pas d'un « undefined.undefined » à l'écran :
  // une régie qui affiche du bruit ne se relit plus.
  if (d.date) return dateCourte(d.date);
  if (d.annee == null) return "";
  return d.annee + "." + d.lune + "." + d.jour;
}

module.exports = { JOURS_PAR_LUNE, jourAbsolu, vieillir, AGE_DIT, absolues, dateCourte };
