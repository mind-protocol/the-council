(() => {
"use strict";
const $ = (id) => document.getElementById(id);

function creer(etat) {
  let dynamiquePrecedente = null, cadenceFer = 0;
// ═══ LES SONDES — CE QU'ON EST VENU VOIR ═══════════════════════════════════
// Deux questions, et ce sont les deux défauts du jour :
//
//   COMBIEN SONT DANS UN MUR, et dans quel état. `Bataille2d.libre(x, y)` rend
//   la réponse du moteur lui-même — on ne relit pas le masque de notre côté,
//   sans quoi on aurait deux lectures du bâti à tenir d'accord.
//
//   QUI ROMPT, ET POURQUOI PAS. La déroute n'a plus que deux entrées dans tout
//   le moteur, et la principale est `h.l1.jambes === "fuite"`. On compte donc
//   ce que les jambes disent, homme par homme : si `fuite` ne sort jamais, on
//   voit ici, en direct, la cause du « zéro fuyard pour deux cent quatorze
//   morts » qu'aucune cuisson n'expliquait.
function sonder() {
  const e = Bataille2d.etat();
  if (!e || e.dressee === false) return;
  // L'horloge du moteur, mais NOTRE état de marche : `e.marche` est celui de la
  // boucle du moteur, qu'on n'utilise plus — il vaut faux en permanence, et il
  // remettait le bouton sur « ▶ Marche » cinq fois par seconde pendant qu'on
  // tournait.
  $("shorloge").textContent = e.temps.toFixed(1) + " s" +
    (etat.marche() && etat.vitesse() > 1 ? "  ×" + etat.vitesse() : "");

  const t = Bataille2d.troupe();
  const dansLeMur = {}, jambes = {}, etats = {};
  let mur = 0, vivants = 0, inconnu = 0;
  for (const h of t) {
    if (h.etat === "mort") continue;
    vivants++;
    etats[h.etat] = (etats[h.etat] || 0) + 1;
    const libre = Bataille2d.libre(h.x, h.y);
    if (libre === null) inconnu++;
    else if (!libre) { mur++; dansLeMur[h.etat] = (dansLeMur[h.etat] || 0) + 1; }
    if (h.l1 && h.l1.jambes) jambes[h.l1.jambes] = (jambes[h.l1.jambes] || 0) + 1;
  }

  const part = (n, d) => d ? (100 * n / d).toFixed(1) + " %" : "—";
  const d = e.dynamique || {};
  const unites = Bataille2d.unites ? Bataille2d.unites() : [];
  const enMarche = unites.filter((u) => u.destination);
  const routes = unites.reduce((n, u) => n + u.calculsAStar, 0);
  const sansChef = unites.filter((u) => u.debout && !u.chef).length;
  const successions = unites.filter((u) => u.successionDans != null);
  const prochaineSuccession = successions.reduce((m, u) =>
    m == null || u.successionDans < m ? u.successionDans : m, null);
  const cohesion = enMarche.length
    ? enMarche.reduce((n, u) => n + u.cohesion, 0) / enMarche.length : 1;
  const pire = enMarche.reduce((m, u) => !m || u.cohesion < m.cohesion ? u : m, null);
  if (dynamiquePrecedente && e.temps > dynamiquePrecedente.temps) {
    const instant = 60 * (d.coupsTentes - dynamiquePrecedente.coupsTentes) /
      (e.temps - dynamiquePrecedente.temps);
    cadenceFer = cadenceFer ? cadenceFer * 0.65 + instant * 0.35 : instant;
  }
  if (!dynamiquePrecedente || e.temps > dynamiquePrecedente.temps)
    dynamiquePrecedente = { temps: e.temps, coupsTentes: d.coupsTentes || 0 };
  const lignes = (o, fort) => Object.entries(o).sort((a, b) => b[1] - a[1])
    .map(([k, v]) => '<tr class="' + (fort && fort(k, v) ? "fort" : "") + '"><td>' +
         k + '</td><td class="n">' + v + "</td></tr>").join("") ||
    '<tr><td colspan="2" style="color:#4a443a">rien</td></tr>';

  // LES VERDICTS EN TÊTE, quand un scénario vient d'être joué. `null` n'est pas
  // « ça va » : c'est une sonde qui n'a pas pu répondre, et elle le dit.
  const vd = !etat.verdicts() ? "" : "<h3>Ce qu'on attendait</h3><table class=\"verdicts\">" +
    etat.verdicts().map((v) => '<tr class="verdict ' + (v.tenu === true ? "ok" :
        v.tenu === false ? "fort" : "") + '"><td>' + v.dit +
      (v.attendu ? "<small>attendu : " + v.attendu + "</small>" : "") +
      '</td><td class="n">' +
      (v.observe != null ? v.observe + "<small>" : "") +
      (v.tenu === true ? "tenu" : v.tenu === false ? "NON" : "sans objet") +
      (v.observe != null ? "</small>" : "") +
      "</td></tr>").join("") + "</table>";

  $("sondes").innerHTML = vd +
    "<h3>Rythme du fer</h3><table>" +
      '<tr><td>dans l\'allonge</td><td class="n">' + (d.enMesure || 0) + " · " +
        part(d.enMesure || 0, d.combattants || 0) + "</td></tr>" +
      '<tr><td>ont frappé depuis 5 s</td><td class="n">' + (d.frappeursRecents || 0) +
        " · " + part(d.frappeursRecents || 0, d.combattants || 0) + "</td></tr>" +
      '<tr><td>coups tentés / min</td><td class="n">' + Math.round(cadenceFer) + "</td></tr>" +
      '<tr><td>coups qui portent</td><td class="n">' + (d.coupsPortes || 0) + " / " +
        (d.coupsTentes || 0) + "</td></tr>" +
      '<tr><td>durée d\'une bouffée</td><td class="n">' + (d.boutMedian || 0) +
        " s méd. · " + (d.boutP90 || 0) + " s p90</td></tr>" +
    "</table>" +

    "<h3>Ce que portent les corps</h3><table>" +
      '<tr><td>sang-froid moyen</td><td class="n">' + (d.sangFroidMoyen ?? "—") + "</td></tr>" +
      '<tr><td>exposition</td><td class="n">' + (d.expositionMoyenne ?? "—") + "</td></tr>" +
      '<tr><td>charge nerveuse</td><td class="n">' + (d.chargeNerveuseMoyenne ?? "—") + "</td></tr>" +
      '<tr class="' + ((d.sortieFermee || 0) ? "fort" : "") +
        '"><td>sans jeu derrière</td><td class="n">' + (d.sortieFermee || 0) + "</td></tr>" +
      '<tr><td>pris dans la presse</td><td class="n">' + (d.presseForte || 0) + "</td></tr>" +
    "</table>" +

    "<h3>Chaîne de mouvement</h3><table>" +
      '<tr><td>unités en marche</td><td class="n">' + enMarche.length +
        " / " + unites.length + "</td></tr>" +
      '<tr><td>routes A* calculées</td><td class="n">' + routes + "</td></tr>" +
      '<tr><td>cohésion moyenne</td><td class="n">' +
        (100 * cohesion).toFixed(0) + " %</td></tr>" +
      '<tr class="' + (sansChef ? "fort" : "ok") + '"><td>unités sans chef</td>' +
        '<td class="n">' + sansChef + "</td></tr>" +
      (successions.length ? '<tr><td>successions en cours</td><td class="n">' +
        successions.length + " · reprise dans " + prochaineSuccession.toFixed(1) + " s</td></tr>" : "") +
      (pire ? '<tr><td>la plus étirée</td><td class="n">' + pire.id + " · " +
        (100 * pire.cohesion).toFixed(0) + " %</td></tr>" : "") +
    "</table>" +

    "<h3>Dans les murs</h3><table>" +
      '<tr class="' + (mur ? "fort" : "ok") + '"><td>hommes dans le bâti</td>' +
        '<td class="n">' + mur + " / " + vivants + "</td></tr>" +
      '<tr class="' + (mur ? "fort" : "ok") + '"><td>soit</td>' +
        '<td class="n">' + part(mur, vivants) + "</td></tr>" +
      (inconnu ? '<tr><td>masque absent pour</td><td class="n">' + inconnu +
                 "</td></tr>" : "") +
    "</table>" +
    (mur ? "<h3>…et dans quel état</h3><table>" + lignes(dansLeMur, () => true) +
           "</table>" : "") +

    "<h3>Ce que disent les jambes</h3><table>" +
      lignes(jambes, (k) => k === "fuite") + "</table>" +
    (jambes.fuite ? "" : '<p class="note">Aucune jambe ne dit « fuite ». ' +
      "C'est la principale des deux seules entrées vers la déroute — l'autre " +
      "ne s'ouvre que si la charrette du roi verse.</p>") +

    "<h3>La troupe</h3><table>" + lignes(etats) + "</table>" +

    "<h3>Le compte</h3><table>" +
      '<tr><td>morts</td><td class="n">' + e.morts + "</td></tr>" +
      '<tr><td>blessés</td><td class="n">' + e.blesses + "</td></tr>" +
      '<tr class="' + (e.morts > 20 && !e.fuyards ? "fort" : "") +
        '"><td>fuyards</td><td class="n">' + e.fuyards + "</td></tr>" +
      '<tr><td>ralliés</td><td class="n">' + (e.rallies || 0) + "</td></tr>" +
      '<tr><td>sang-froid moyen</td><td class="n">' + e.sangFroidMoyen + "</td></tr>" +
      '<tr><td>faits d\'annales</td><td class="n">' + e.faits + "</td></tr>" +
    "</table>" +

    "<h3>Les portes</h3><table>" +
      e.portes.map((p) => '<tr><td>' + p.nom.replace(/^La /, "") + "</td>" +
        '<td class="n">' + p.etat + (p.par ? " (" + p.par + ")" : "") +
        "</td></tr>").join("") + "</table>" +

    "<h3>Ce que fait l'assaut</h3><table>" + lignes(e.branches) + "</table>";
}

  return Object.freeze({
    sonder,
    remettre: () => { dynamiquePrecedente = null; cadenceFer = 0; },
  });
}

window.BatailleSondes = Object.freeze({ creer });
})();
