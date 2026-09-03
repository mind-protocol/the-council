/**
 * Scénarios / Monde de l'état — ce que l'ÉTAT compose, à la place d'un scénario.
 *
 * À la racine du jeu, le moteur ne joue pas une entrée du catalogue : il joue
 * les lieux, les groupes et les ordres de `etat/`, composés par le serveur
 * (serveur/domaine/ost.js) et servis sur `/bataille/monde` dans la forme
 * exacte d'un scénario — terrain, zone, unités. Le catalogue reste la vue de
 * travail de `/bataille`.
 *
 * Une composition qui ne tient pas (pas de personnage assis, pas de place
 * constatée, pas de route, colonne plus longue que la route…) arrive en 503
 * avec sa raison : on la rend telle quelle, et l'appelant retombe sur le
 * catalogue en le disant. Un écran vide sans phrase serait pire.
 */
export async function chargerMondeEtat() {
  // la requête de la page passe telle quelle : `?echelle=4` (un corps pour
  // quatre hommes — mesuré, 1 462 hommes coûtent 3,5 s de machine par seconde
  // jouée au four) y voyage à côté du jeton.
  const r = await fetch('/bataille/monde' + location.search);
  if (!r.ok) {
    const corps = await r.json().catch(() => ({}));
    throw new Error("monde de l'état indisponible (" + (corps.erreur || 'HTTP ' + r.status) + ') : catalogue');
  }
  return r.json();
}
