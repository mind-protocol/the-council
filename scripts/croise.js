// -*- coding: utf-8 -*-
/**
 * CROISE — ce qui parvient à un siège LÀ OÙ IL EST, sans qu'il ait marché.
 *
 *     node scripts/croise.js                 (tous les sièges, à l'heure du monde)
 *     node scripts/croise.js --siege ostor-bray
 *     node scripts/croise.js --minute 1205   (et si l'on y était à cette heure-là ?)
 *     node scripts/croise.js --balayage      (minute par minute, ce qui va tomber)
 *
 * LE TROU QU'IL BOUCHE. `serveur/croiser.js` répond parfaitement à « que
 * perçoit-on d'ici, à cette minute » — mais il n'était appelé QUE depuis
 * `/marche`. C'est-à-dire qu'un joueur ne percevait la bataille que s'il était
 * en train de traverser la ville à pied. Assis au Grenier pendant qu'on
 * enfonce une porte à quatre cents pas, il n'entendait rien : non parce que le
 * mur l'en empêchait, mais parce que personne ne posait la question.
 *
 * Or la règle que le manuel donne n'est pas « si le joueur marche » : c'est
 * SI L'UN DES SIENS ÉTAIT À PORTÉE, À CETTE MINUTE-LÀ. Marcher n'a rien à y
 * voir. Ce script pose donc la même question depuis l'autre bout — la position
 * du siège telle qu'elle est écrite, et l'heure telle qu'elle est — et rend
 * la réponse au MJ, en français, prête à jouer.
 *
 * IL N'ÉCRIT RIEN, ET C'EST VOULU. Ni dans `etat/`, ni dans le flux, ni dans
 * une inbox. C'est un outil de MJ, comme `veille.py` ou `dossier.py` : on le
 * lance au début d'un tour, on lit, et l'on décide ce qu'on en fait. Un
 * script qui pousserait tout seul dans le fil déciderait à la place du MJ de
 * ce que ses personnages remarquent — et ça, c'est de la narration.
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ICI = path.dirname(__dirname);
const croiser = require(path.join(ICI, "serveur", "croiser.js"));

function args() {
  const a = process.argv.slice(2), o = { siege: null, minute: null, jour: null,
                                         lieu: "portreal", balayage: false };
  for (let i = 0; i < a.length; i++) {
    const c = a[i].replace(/^--/, "");
    if (c === "balayage") { o.balayage = true; continue; }
    if (c in o) o[c] = a[++i];
  }
  if (o.minute !== null) o.minute = +o.minute;
  if (o.jour !== null) o.jour = +o.jour;
  return o;
}

const lire = (f, d) => {
  try { return JSON.parse(fs.readFileSync(path.join(ICI, "etat", f), "utf-8")); }
  catch (e) { return d; }
};

// --- CE QU'ON DIT, ET COMMENT -----------------------------------------------
// Le MJ ne lira pas `{"quoi":"porte-enfoncee","comment":"entendu","pas":700}`.
// Il lira « un grand fracas de bois et de fer, au nord » — et il en fera une
// ligne de récit. La mise en mots est donc ici, pas dans `croiser.js`, qui
// doit rester une fonction pure de géométrie.
//
// TROIS VOCABULAIRES, ET ILS NE DISENT PAS LA MÊME CHOSE. C'est toute la
// discipline du brouillard, portée par la langue plutôt que par une règle :
// ce qu'on VOIT se nomme, ce qu'on ENTEND ne se nomme jamais, ce qu'on TROUVE
// se décrit au présent parce que c'est encore là.
const VU = {
  "porte-cede":       "la porte de la ville commence à céder sous les coups",
  "porte-enfoncee":   "la porte de la ville s'effondre vers l'intérieur",
  "contact":          "les deux lignes se joignent, et le fer commence",
  "premier-sang":     "un homme tombe, et il ne se relève pas",
  "blesse":           "un homme est à terre, vivant, et il appelle",
  "blesse-succombe":  "un homme à terre cesse d'appeler",
  "blesse-tient":     "un blessé a cessé de saigner — il tiendra",
  "chef-tombe":       "un chef tombe, et vingt hommes se retournent",
  "tete-tombe":       "celui qui commandait vient de tomber",
  "escouade-rompt":   "une vingtaine d'hommes lâchent et refluent",
  "ralliement":       "un chef en rattrape un qui partait, et le remet en ligne",
  "ordre":            "un homme à cheval crie un ordre à ses porte-bannières",
  "assaut-au-donjon": "les premiers assaillants sont au pied du Donjon Rouge",
  "peur-gagne":       "la rue se vide d'un coup — ils les ont vus",
  "rumeur-gagne":     "la rue se vide sans que personne ait rien vu",
  "guet-a-vu":        "un homme du guet s'avance, regarde, et repart au pas de course",
  "maison-brulee":    "une maison prend feu",
  "prend-les-armes":  "un homme du quartier sort de chez lui avec ce qu'il a trouvé",
  "barre-sa-porte":   "un voisin met une planche en travers de sa porte et s'y adosse",
  "coureur-part":     "un homme part en courant, sans armes, les mains vides",
  "coureur-arrive":   "un coureur rejoint une troupe et lui parle à l'oreille",
  "coureur-tombe":    "un homme qui courait s'effondre",
  "banniere-tombe":   "une bannière disparaît dans la presse",
  "banniere-relevee": "une bannière se relève au-dessus de la mêlée",
  "nouveau-chef":     "un homme prend la tête d'une troupe qui n'en avait plus",
  "escouade-reprise": "une troupe qui piétinait se remet en marche",
};

// CE QU'ON ENTEND N'A NI NOM NI AUTEUR — c'est la moitié du brouillard, et
// elle tient dans ce dictionnaire-ci. Le même fait qui, vu, dit « la porte de
// la ville s'effondre », entendu ne dit qu'un fracas. Un MJ qui recopierait
// le premier au lieu du second rendrait au joueur, par la bande, tout ce que
// la distance lui refuse.
const ENTENDU = {
  "porte-cede":       "des coups sourds et réguliers, du bois qu'on bat",
  "porte-enfoncee":   "un grand fracas de bois et de fer, puis une clameur",
  "contact":          "un bruit de fer, et des cris qui ne sont pas des cris de fête",
  "blesse":           "quelqu'un appelle, et ce n'est pas un ivrogne",
  "blesse-tient":     "une plainte, plus faible",
  "chef-tombe":       "une clameur brève, et puis plus rien",
  "tete-tombe":       "une clameur, et un silence qui dure trop",
  "escouade-rompt":   "une débandade, des pas nombreux qui vont dans le désordre",
  "ralliement":       "une voix qui hurle des ordres, très fort",
  "ordre":            "une voix qui porte, sans qu'on distingue les mots",
  "assaut-au-donjon": "une rumeur d'hommes en nombre, du côté de la colline",
  "peur-gagne":       "des gens qui courent, et des volets qu'on ferme",
  "maison-brulee":    "un crépitement, et l'odeur",
};

// LA TRACE SE DIT AU PRÉSENT, parce qu'elle est encore là quand on passe.
const TRACE = {
  "porte-enfoncee":   "la porte de la ville est en morceaux, les gonds arrachés",
  "premier-sang":     "du sang sur les pavés, et personne pour l'avoir nettoyé",
  "blesse":           "un homme est là, contre un mur, vivant",
  "blesse-succombe":  "un corps, encore tiède",
  "blesse-tient":     "un homme assis contre un mur, qui ne saigne plus",
  "chef-tombe":       "un corps mieux vêtu que les autres, déjà dépouillé",
  "tete-tombe":       "un corps qu'on a couvert d'un manteau",
  "coureur-tombe":    "un homme sans armes, mort, la main encore fermée",
  "banniere-tombe":   "une hampe brisée, et l'étoffe dans la boue",
  "maison-brulee":    "une maison noircie, béante, qui fume encore",
  // LA MEILLEURE TRACE DE TOUTES, et c'est celle qui a une adresse. Une porte
  // grande ouverte sur une maison vide, à trois heures du matin, dit que
  // l'homme qui y vit est sorti avec une hache et n'est pas rentré. On peut
  // entrer, on peut l'attendre, on peut demander aux voisins — et le jour où
  // il revient, il a vu la nuit entière.
  "prend-les-armes":  "une porte ouverte sur une maison vide, et rien de volé",
  "barre-sa-porte":   "une porte barrée de l'intérieur, et quelqu'un derrière",
};

const HEURE = (m) => String(Math.floor(m / 60)).padStart(2, "0") + "h" +
                     String(Math.floor(m % 60)).padStart(2, "0");

function ligne(e) {
  const t = e.comment === "vu" ? VU : e.comment === "entendu" ? ENTENDU : TRACE;
  const dit = t[e.quoi];
  // UN FAIT SANS PHRASE NE SE TAIT PAS, il se dit crûment — et le code brut
  // qui apparaît est le rappel qu'il manque une ligne ici. Le silencieux
  // serait pire : on croirait que rien n'est arrivé.
  const corps = dit || ("[" + e.quoi + "]");
  if (e.comment === "entendu")
    return "   ENTENDU  " + corps + " — " + (e.vers || "on ne sait d'où") +
           ", à " + e.pas + " pas environ";
  if (e.comment === "trace")
    return "   TROUVÉ   " + corps + " — à " + e.pas + " pas, depuis " +
           e.depuis_min + " min";
  return "   VU       " + corps + " — à " + e.pas + " pas";
}

// ---------------------------------------------------------------------------
function main() {
  const o = args();
  const monde = lire("monde.json", null);
  const horloges = lire("horloges.json", {});
  const corps = lire("corps.json", { affectations: {} });
  const joueurs = lire("joueurs.json", []);
  const bataille = lire("bataille.json", null);

  if (!bataille || !bataille.debut) {
    process.stdout.write("Aucune bataille datée (etat/bataille.json). Rien à croiser.\n");
    return;
  }

  const sieges = joueurs.filter((j) => j && j.personnage_id)
    .filter((j) => !o.siege || j.personnage_id === o.siege);
  if (!sieges.length) {
    process.stdout.write("Aucun siège" + (o.siege ? " nommé « " + o.siege + " »" : "") + ".\n");
    return;
  }

  const d0 = (monde && monde.date) || {};
  process.stdout.write("Bataille datée : jour " + bataille.debut.jour + ", " +
    HEURE(bataille.debut.minute) + "\n");

  // UN SAC PÉRIMÉ MENT SANS RIEN DIRE, et ça nous a coûté une demi-heure : le
  // fichier annonçait « le premier assaillant atteint le Donjon Rouge » à
  // quatre-vingt-onze secondes, sur le seuil de la porte, à six cents mètres
  // du donjon. On a cherché le bogue dans la simulation ; il n'y était plus
  // depuis longtemps — c'était le sac qui datait d'avant la correction.
  //
  // Rien ne le signalait, et rien ne pouvait le signaler : un fichier cuit n'a
  // aucun moyen de savoir que le four a changé. On compare donc les dates, et
  // l'on prévient. C'est grossier, et c'est exactement ce qu'il faut.
  const mt = (f) => { try { return fs.statSync(f).mtimeMs; } catch (e) { return 0; } };
  const ann = mt(path.join(ICI, "monde", (o.lieu || "portreal") + ".sac.annales.json"));
  const mod = mt(path.join(ICI, "ecrans", "modules", "bataille2d.js"));
  if (mod && ann && mod > ann)
    process.stdout.write(
      "⚠ le sac est plus vieux que la simulation qui l'a cuit — ce que vous\n" +
      "  lirez ci-dessous décrit une bataille qui n'a plus lieu ainsi.\n" +
      "  Recuisez : node scripts/monde/sac.js --sortie portreal.sac\n");
  process.stdout.write("\n");

  for (const s of sieges) {
    const aff = corps.affectations["personnage:" + s.personnage_id];
    // SANS POSITION, PAS DE PERCEPTION — et l'on ne devine pas. Un siège qui
    // n'a jamais marché n'a pas de mètres ; lui en inventer reviendrait à
    // décider qu'il était quelque part, ce qui est très exactement ce que ce
    // script ne doit pas faire.
    if (!aff || !aff.xyz) {
      process.stdout.write("— " + s.nom + " : aucune position en mètres " +
        "(il n'a pas encore marché). Rien ne peut lui parvenir.\n\n");
      continue;
    }
    // L'heure de SON siège, qui n'est pas forcément celle du monde.
    const h = horloges[s.personnage_id] || {};
    const jour = o.jour !== null ? o.jour : (h.jour !== undefined ? h.jour : d0.jour);
    const minute = o.minute !== null ? o.minute
                 : (h.minute !== undefined ? h.minute : d0.minute);

    process.stdout.write("— " + s.nom + "  (jour " + jour + ", " + HEURE(minute) + ")\n");

    if (o.balayage) {
      // CE QUI VA TOMBER, ET QUAND. Le MJ prépare son tour : il veut savoir
      // qu'à 20h04 son joueur entendra quelque chose s'il n'a pas bougé. Une
      // minute par ligne, et seulement celles qui portent.
      let rien = true;
      for (let m = minute; m < minute + 60; m++) {
        const r = croiser.autour(ICI, o.lieu, aff.xyz[0], aff.xyz[1],
                                 { jour, minute: m });
        if (!r) break;
        const n = r.vu.length + r.entendu.length;
        if (!n) continue;
        rien = false;
        process.stdout.write("  " + HEURE(m) + (r.arret ? "  ⟨arrête la marche⟩" : "") + "\n");
        for (const e of r.vu) process.stdout.write(ligne(e) + "\n");
        for (const e of r.entendu) process.stdout.write(ligne(e) + "\n");
      }
      if (rien) process.stdout.write("   (l'heure qui vient ne lui apporte rien)\n");
      process.stdout.write("\n");
      continue;
    }

    const r = croiser.autour(ICI, o.lieu, aff.xyz[0], aff.xyz[1], { jour, minute });
    if (!r) { process.stdout.write("   (pas de bataille à cette date)\n\n"); continue; }
    const tout = [...r.vu, ...r.entendu, ...r.traces];
    if (!tout.length) {
      process.stdout.write("   rien ne lui parvient d'ici, à cette minute.\n\n");
      continue;
    }
    for (const e of tout) process.stdout.write(ligne(e) + "\n");
    if (r.arret)
      process.stdout.write("   ⟨ce qu'il voit arrête une marche : c'est un fil, " +
                           "pas un décor⟩\n");
    process.stdout.write("\n");
  }
}

main();
