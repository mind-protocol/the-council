// HORLOGES LOCALES DES ACTEURS — miroir de la règle d'ancrage de la boucle.
//
// La vérité persistante reste `etat/horloges.json` : une horloge par siège.
// Un acteur montre ici l'horloge du siège qui le porte explicitement ; sinon
// celle du siège occupé physiquement le plus proche. Ce module ne décide ni
// n'avance rien : il rend seulement visible, dans la régie, l'heure que
// `agents/activation/horloges.py` sert à sa prochaine activation.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");

function lire(rel, defaut) {
  try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", rel), "utf-8")); }
  catch (e) { return defaut; }
}

function minuteAbsolue(d) {
  if (!d || d.annee == null) return null;
  return ((((+d.annee * 12) + (+d.lune - 1)) * 30 + (+d.jour - 1)) * 1440)
    + (+d.minute || 0);
}

function depuisMinute(n) {
  if (!Number.isFinite(n)) return null;
  const jourAbsolu = Math.floor(n / 1440);
  const minute = ((n % 1440) + 1440) % 1440;
  const moisAbsolu = Math.floor(jourAbsolu / 30);
  const jour = ((jourAbsolu % 30) + 30) % 30 + 1;
  const annee = Math.floor(moisAbsolu / 12);
  const lune = ((moisAbsolu % 12) + 12) % 12 + 1;
  return { annee, lune, jour, minute };
}

function contexte(maintenantMs) {
  const horloges = lire("horloges.json", {});
  const rosterBrut = lire("joueurs.json", []);
  const roster = Array.isArray(rosterBrut) ? rosterBrut : [];
  const personnagesBrut = lire("personnages.json", []);
  const personnages = Array.isArray(personnagesBrut) ? personnagesBrut : [];
  const lieuxBrut = lire("lieux.json", []);
  const lieux = Array.isArray(lieuxBrut) ? lieuxBrut : [];
  const boucle = lire(path.join("activations", "boucle.json"), {});
  const parId = Object.fromEntries(personnages.filter((p) => p && p.id)
    .map((p) => [p.id, p]));
  const lieuxParId = Object.fromEntries(lieux.filter((l) => l && l.id)
    .map((l) => [l.id, l]));
  let actifs = roster.filter((s) => s && !s.regie && !s.partie
    && s.occupe !== false && horloges[s.personnage_id]);
  if (!actifs.length) actifs = roster.filter((s) => s && !s.regie && !s.partie
    && horloges[s.personnage_id]);
  const hVague = boucle.horloge || {};
  const sourceMinute = minuteAbsolue(horloges[hVague.source_id]);
  const frontMinute = minuteAbsolue(horloges[hVague.front_id]);
  const memeRepere = hVague.source_cle === hVague.source_id + ":" + sourceMinute
    && hVague.front_cle === hVague.front_id + ":" + frontMinute;
  const ecoulees = memeRepere ? Math.max(0, (+maintenantMs / 1000)
    - (+hVague.ancre_mur || (+maintenantMs / 1000))) : 0;
  return { horloges, roster, parId, lieuxParId, actifs, hVague, ecoulees };
}

function distancePhysique(a, b, lieux) {
  if (!a || !b) return null;
  if (a === b) return 0;
  const da = +(lieux[a] || {}).jours_de_pr;
  const db = +(lieux[b] || {}).jours_de_pr;
  if (!Number.isFinite(da) || !Number.isFinite(db)) return null;
  return da === 0 || db === 0 ? Math.abs(da - db) : da + db;
}

function ancreDe(id, c) {
  if (c.horloges[id]) return id;
  const explicite = c.actifs.find((s) => (s.pnj || []).includes(id));
  if (explicite) return explicite.personnage_id;
  const acteur = c.parId[id] || {};
  const candidats = c.actifs.map((s) => {
    const siege = c.parId[s.personnage_id] || {};
    const distance = distancePhysique(acteur.lieu_id, siege.lieu_id, c.lieuxParId);
    return distance == null ? null
      : { id: s.personnage_id, distance, priorite: s.role === "principal" ? 0 : 1 };
  }).filter(Boolean).sort((a, b) => (a.distance - b.distance)
    || (a.priorite - b.priorite) || a.id.localeCompare(b.id));
  if (candidats.length) return candidats[0].id;
  return c.hVague.front_id || c.hVague.source_id
    || ((c.roster.find((s) => s.role === "principal") || {}).personnage_id);
}

function locales(ids, maintenantMs) {
  const c = contexte(maintenantMs == null ? Date.now() : maintenantMs);
  const sortie = {};
  for (const id of ids || []) {
    const ancre = ancreDe(id, c);
    const depart = minuteAbsolue(c.horloges[ancre]);
    if (depart == null) { sortie[id] = null; continue; }
    sortie[id] = { ancre, date: depuisMinute(depart + Math.floor(c.ecoulees / 60)) };
  }
  return sortie;
}

module.exports = { locales, minuteAbsolue, depuisMinute };
