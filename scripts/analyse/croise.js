// -*- coding: utf-8 -*-
/**
 * CROISE — ce qui parvient à un siège LÀ OÙ IL EST, sans qu'il ait marché.
 *
 *     node scripts/analyse/croise.js                 (tous les sièges, à l'heure du monde)
 *     node scripts/analyse/croise.js --siege ostor-bray
 *     node scripts/analyse/croise.js --minute 1205   (et si l'on y était à cette heure-là ?)
 *     node scripts/analyse/croise.js --balayage      (minute par minute, ce qui va tomber)
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

const ICI = path.dirname(path.dirname(__dirname));
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
  // LES DOUZE QUI N'ÉTAIENT PERÇUS PAR PERSONNE. Ils étaient émis par le four
  // et absents de la table des portées : ils tombaient sur le défaut timide et
  // ne se disaient nulle part. Depuis qu'ils ont une portée juste
  // (`ecrans/modules/bataille/faits.js`), il leur faut une phrase — sans quoi
  // le MJ lit « [porte-abimee] » et se demande ce qu'il doit en faire.
  "porte-abimee":     "la porte de la ville porte de vieilles fentes, mal rebouchées",
  "porte-ouverte":    "la porte de la ville s'ouvre toute seule, de l'intérieur",
  "donjon-ouvert":    "les vantaux du Donjon Rouge s'écartent, et la garde s'y engouffre",
  "declencheur-tombe":"une troupe qui attendait s'ébranle, sans que personne soit venu la chercher",
  "initiative":       "un chef parle à ses hommes, et sa troupe change de cap",
  "habitant":         "quelqu'un du quartier, sur son pas de porte, qui n'a pas l'air de rentrer",
  "ordre-sans-personne": "un coureur s'arrête au milieu de la rue, cherche, et ne trouve personne",
  "roi-averti":       "un homme du guet franchit la porte du Donjon Rouge en courant",
  "messager-tombe":   "un homme qui courait vers la colline tombe et ne se relève pas",
  "roi-tombe":        "une charrette verse au milieu de la presse, et la clameur change",
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
  "porte-ouverte":    "un battant lourd qu'on ouvre, et des pas qui s'y engouffrent",
  "donjon-ouvert":    "des vantaux qu'on tire, et beaucoup de fer qui rentre quelque part",
  "initiative":       "une voix brève, tout près, et des pieds qui se remettent en marche",
  "roi-tombe":        "une clameur d'un autre genre, qui monte et ne retombe pas",
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
  "porte-abimee":     "une porte fendue de vieille date, mal rebouchée",
  "porte-ouverte":    "la porte de la ville grande ouverte, intacte, les barres posées à côté",
  "donjon-ouvert":    "les vantaux du Donjon Rouge béants, et personne pour les tenir",
  // MÊME GISEMENT QUE `prend-les-armes`, ET C'EST LE MEILLEUR : celui-ci a un
  // NOM dans le sac, une adresse, et il n'est pas sorti. On peut aller frapper.
  "habitant":         "une porte entrebâillée, et quelqu'un derrière qui a tout vu",
  "messager-tombe":   "un homme sans armes, face contre terre, tourné vers la colline",
  "roi-tombe":        "une charrette renversée, et ce qu'on a jeté dessus en hâte",
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
  const presence = (lire("presence.json", { presence: {} }) || {}).presence || {};
  const persos = lire("personnages.json", []);

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

  // OÙ EST CET HOMME, EN MÈTRES — et l'on DÉDUIT sans jamais INVENTER.
  //
  // La règle d'avant refusait tout ce qui n'était pas une marche : « un siège
  // qui n'a jamais marché n'a pas de mètres ». Prudent, et trop : elle
  // confondait deviner et déduire. Personne ne sait où est un homme dont le
  // jeu ne dit rien — mais quand `presence` dit qu'il est au Culpucier et que
  // `corps.json` dit où est le Culpucier, sa position n'est pas une invention,
  // c'est une lecture. La refuser, c'est rendre la moitié du monde aveugle à
  // une bataille qui se passe à cent pas.
  //
  // Trois prises, de la plus précise à la plus large, et l'on dit toujours
  // laquelle a servi — parce qu'un homme situé à sa SALLE n'est pas situé au
  // mètre près, et que le MJ doit pouvoir en tenir compte.
  // LES MÈTRES D'UN MONDE NE VALENT PAS DANS L'AUTRE, et c'est le premier bug
  // que ce pont a produit : Rhaenyra, à Peyredragon, « trouvait une maison
  // noircie » de la bataille de Port-Réal. Sa Table Peinte est en [4459, 2099]
  // DANS L'ESPACE DE PEYREDRAGON, et ces mètres-là tombent par hasard au milieu
  // de Port-Réal. Le doc d'`affecter.py` le dit déjà : « l'unicité porte sur la
  // PAIRE (monde, bat) ». Une position sans son monde n'est pas une position.
  // Le monde de la bataille : celui du sac, à défaut celui qu'on a demandé.
  const cible = (bataille && bataille.sac) || o.lieu || "portreal";
  const meme = (v) => ((v && v.monde) || "portreal").replace(/-/g, "") ===
                      String(cible).replace(/-/g, "");
  const ou = (pid) => {
    const a = corps.affectations;
    const p = presence[pid] || {};
    const direct = a["personnage:" + pid];
    if (direct && direct.xyz && meme(direct)) return { xyz: direct.xyz, par: "ses pas" };
    const salle = p.salle && (a["salle:" + p.salle] || a["lieu:" + p.salle]);
    if (salle && salle.xyz && meme(salle))
      return { xyz: salle.xyz, par: "la salle où il se tient (" + p.salle + ")" };
    const f = (Array.isArray(persos) ? persos : persos.personnages || [])
      .find((x) => x && x.id === pid);
    const lieu = f && f.lieu_id && a["lieu:" + f.lieu_id];
    if (lieu && lieu.xyz && meme(lieu))
      return { xyz: lieu.xyz, par: "son lieu (" + f.lieu_id + ")" };
    return null;
  };

  for (const s of sieges) {
    const trouve = ou(s.personnage_id);
    if (!trouve) {
      process.stdout.write("— " + s.nom + " : aucune position en mètres, et rien " +
        "dans presence ni corps.json d'où la déduire. Rien ne peut lui parvenir.\n\n");
      continue;
    }
    const aff = { xyz: trouve.xyz };
    // L'heure de SON siège, qui n'est pas forcément celle du monde.
    const h = horloges[s.personnage_id] || {};
    const jour = o.jour !== null ? o.jour : (h.jour !== undefined ? h.jour : d0.jour);
    const minute = o.minute !== null ? o.minute
                 : (h.minute !== undefined ? h.minute : d0.minute);

    // On DIT par quoi il est situé : « ses pas » vaut le mètre, « la salle où
    // il se tient » vaut la pièce, et la différence change ce qu'on peut lui
    // faire percevoir sans mentir.
    process.stdout.write("— " + s.nom + "  (jour " + jour + ", " + HEURE(minute) +
      ", situé par " + trouve.par + ")\n");

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
