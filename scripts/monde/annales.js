// -*- coding: utf-8 -*-
/**
 * ANNALES — tailler dans un sac déjà cuit, sans y retoucher.
 *
 *     node scripts/monde/annales.js monde/essai.sac.annales.json
 *     node scripts/monde/annales.js <fichier> --niveau 1
 *     node scripts/monde/annales.js <fichier> --aspect commandement,ville
 *     node scripts/monde/annales.js <fichier> --depuis 5m --jusqu-a 12m30
 *     node scripts/monde/annales.js --liste          (les niveaux et les aspects)
 *
 * POURQUOI PAS DANS LE FOUR. Une cuisson coûte des minutes ; une lecture coûte
 * un battement de cil. Poser les filtres sur `sac.js` obligerait à recuire la
 * nuit entière pour changer d'avis sur ce qu'on veut en lire — et l'on
 * n'oserait plus changer d'avis. Les annales complètes sont la SOURCE ; ce
 * script en tire des VUES, autant qu'on veut, et n'écrit jamais dans `monde/`.
 *
 * ON NE REFORMULE RIEN. `recit[i]` et `detail[i]` sont la même chose vue deux
 * fois — la phrase et ses champs, dans le même ordre, écrites ensemble par
 * `sac.js`. On filtre sur les champs et l'on ressort la phrase telle quelle.
 * Réécrire la mise en mots ici donnerait deux façons de dire un même fait,
 * c'est-à-dire deux comptes rendus d'une même nuit qui divergeraient à la
 * première ligne qu'on toucherait d'un côté — exactement ce que le four
 * s'interdit en important `bataille2d.js` au lieu de le réécrire.
 *
 * DEUX FILTRES QUI NE FONT PAS LE MÊME MÉTIER.
 *
 *   Le NIVEAU coupe en profondeur : ce qu'un rapport retient, ce qu'un témoin
 *   raconte, ce que la nuit a réellement contenu. Il est cumulatif — le 3
 *   contient tout le 2.
 *
 *   L'ASPECT coupe en travers : la chaîne de commandement, la ville, le fer,
 *   les ouvrages. Un même fait sert plusieurs aspects (un coureur qui tombe
 *   est du commandement ET de ce qui se sait), et c'est voulu : on ne lit pas
 *   la même nuit selon la question qu'on lui pose.
 *
 * Les deux se croisent : `--niveau 3 --aspect commandement` donne la chaîne de
 * com telle qu'elle s'est jouée, sans les blessés ni les habitants.
 */
"use strict";
const fs = require("fs");
const path = require("path");

const RACINE = path.dirname(path.dirname(__dirname));

// ---------------------------------------------------------------------------
// LES NIVEAUX — cumulatifs, du tournant au moindre râle.
//
// Ce qui décide du rang d'un fait, c'est CE QU'IL CHANGE, pas sa gravité
// apparente. Un blessé qui succombe est une mort, et il est au dernier niveau ;
// une porte qui commence à céder ne tue personne, et elle est au deuxième —
// parce que la première ne change rien à la nuit et que la seconde la décide.
// ---------------------------------------------------------------------------
const NIVEAUX = [
  { n: 1, nom: "le tournant",
    dit: "ce sans quoi la nuit n'aurait pas eu lieu — dix lignes au plus",
    quoi: ["contact", "premier-sang", "porte-enfoncee", "porte-ouverte",
           "donjon-ouvert", "donjon-tranche", "roi-tombe", "roi-averti",
           "assaut-au-donjon", "tete-tombe"] },
  { n: 2, nom: "ce qu'un rapport retient",
    dit: "ce qu'un clerc à tablette de cire aurait su écrire au matin",
    quoi: ["porte-cede", "chef-tombe", "escouade-rompt", "guet-a-vu",
           "maison-brulee", "corps-ferme", "corps-sourd", "corps-versatile",
           // L'état d'un ouvrage AVANT qu'on le frappe : ça n'a tué personne,
           // et ça décide de l'heure à laquelle la ville tombe.
           "porte-abimee"] },
  { n: 3, nom: "la nuit telle qu'elle s'est jouée",
    dit: "les ordres, les coureurs, les bannières, la peur qui court",
    quoi: ["ordre", "coureur-part", "coureur-arrive", "coureur-tombe", "ordre-sans-personne",
           "ordre-deforme", "declencheur-tombe", "initiative",
           "escouade-sourde", "escouade-reprise", "nouveau-chef",
           "banniere-tombe", "banniere-relevee", "ralliement",
           "peur-gagne", "rumeur-gagne", "prend-les-armes"] },
  { n: 4, nom: "tout",
    dit: "chaque homme à terre, chaque habitant nommé",
    quoi: ["blesse", "blesse-tient", "blesse-succombe", "habitant"] },
];

// ---------------------------------------------------------------------------
// LES ASPECTS — en travers, et ils se recouvrent exprès.
// ---------------------------------------------------------------------------
const ASPECTS = {
  commandement: {
    nom: "La chaîne de commandement",
    dit: "qui ordonne, qui transmet, qui n'entend plus rien",
    quoi: ["ordre", "coureur-part", "coureur-arrive", "coureur-tombe", "ordre-sans-personne",
           // Ce que la chaîne fait quand elle ne marche pas : elle s'abîme,
           // elle attend, ou elle se passe de tête. Les trois sont ici, avec
           // le reste, parce que c'est le même sujet.
           "ordre-deforme", "declencheur-tombe", "initiative",
           "escouade-sourde", "escouade-reprise", "nouveau-chef",
           "tete-tombe", "chef-tombe", "banniere-tombe", "banniere-relevee",
           "corps-ferme", "corps-sourd", "corps-versatile"] },
  ville: {
    nom: "La ville",
    dit: "ce que la population fait pendant qu'on se bat dessus",
    quoi: ["habitant", "prend-les-armes", "peur-gagne", "rumeur-gagne",
           "maison-brulee"] },
  fer: {
    nom: "Le fer",
    dit: "le contact, les corps à terre, les escouades qui cessent d'en être",
    quoi: ["contact", "premier-sang", "blesse", "blesse-succombe",
           "blesse-tient", "escouade-rompt", "ralliement", "assaut-au-donjon"] },
  nouvelles: {
    nom: "Ce qui se sait",
    dit: "l'information qui circule — ou qui tombe en chemin",
    quoi: ["guet-a-vu", "rumeur-gagne", "peur-gagne", "roi-averti",
           "coureur-part", "coureur-arrive", "coureur-tombe", "ordre-sans-personne", "ordre-deforme",
           "escouade-sourde", "escouade-reprise"] },
  ouvrages: {
    nom: "Les ouvrages",
    dit: "les portes, et par où l'on entre",
    quoi: ["porte-abimee", "porte-cede", "porte-enfoncee", "porte-ouverte",
           "donjon-ouvert"] },
  issue: {
    nom: "L'issue",
    dit: "comment la nuit s'est décidée",
    quoi: ["contact", "premier-sang", "porte-enfoncee", "porte-ouverte",
           "donjon-ouvert", "donjon-tranche", "roi-averti", "roi-tombe",
           "assaut-au-donjon"] },
  // Le filet de sécurité : un `quoi` qu'aucune liste ci-dessus ne nomme tombe
  // ici, et le script le dit sur la sortie d'erreur. Sans ça, ajouter un fait
  // dans `bataille2d.js` le ferait disparaître en silence de toutes les vues —
  // et l'on chercherait le défaut dans le four, qui n'y serait pour rien.
  divers: { nom: "Divers", dit: "ce qu'aucun aspect ne réclame encore", quoi: [] },
};

const CONNUS = new Set([].concat(...NIVEAUX.map((n) => n.quoi)));

/** Le niveau d'un fait — 4 par défaut, jamais 5 : rien ne se perd en bas. */
function niveauDe(quoi) {
  for (const n of NIVEAUX) if (n.quoi.includes(quoi)) return n.n;
  return 4;
}

/** Tous les aspects d'un fait ; `divers` s'il n'en a aucun. */
function aspectsDe(quoi) {
  const a = Object.keys(ASPECTS).filter((k) => ASPECTS[k].quoi.includes(quoi));
  return a.length ? a : ["divers"];
}

// ---------------------------------------------------------------------------
// LE TEMPS — on l'écrit comme on le lit dans le document.
// `300`, `5m`, `5m30`, `5:30`, `5′30″` : toutes ces formes disent la même
// chose, et l'on n'oblige personne à convertir de tête ce que le fichier
// affiche déjà en minutes et secondes.
// ---------------------------------------------------------------------------
function secondes(v) {
  if (v == null || v === "") return null;
  const s = String(v).trim();
  if (/^\d+(\.\d+)?$/.test(s)) return +s;
  const m = s.match(/^(\d+)\s*(?:m|:|′)\s*(\d+)?/u);
  if (m) return +m[1] * 60 + (m[2] ? +m[2] : 0);
  throw new Error("durée incomprise : « " + v + " » (essayez 300, 5m, 5m30, 5:30)");
}

const HEURE = (s) => Math.floor(s / 60) + "′" +
                     String(Math.floor(s % 60)).padStart(2, "0") + "″";

// ---------------------------------------------------------------------------
function args() {
  const a = process.argv.slice(2);
  const o = {
    fichier: null, niveau: 2, aspect: null, quoi: null, sauf: null,
    depuis: null, jusqua: null, zone: null, corps: null, camp: null,
    par: "temps", tranche: "5m", sortie: null, json: false, liste: false,
    muet: false,
  };
  const DRAPEAUX = new Set(["json", "liste", "muet"]);
  for (let i = 0; i < a.length; i++) {
    if (!a[i].startsWith("--")) { o.fichier = a[i]; continue; }
    const c = a[i].slice(2).replace(/-/g, "").replace(/^jusqua$/, "jusqua");
    if (DRAPEAUX.has(c)) { o[c] = true; continue; }
    if (!(c in o)) throw new Error("option inconnue : " + a[i]);
    o[c] = a[++i];
  }
  o.niveau = +o.niveau;
  if (!(o.niveau >= 1 && o.niveau <= 4)) throw new Error("--niveau va de 1 à 4");
  if (!["temps", "aspect", "zone", "corps"].includes(o.par))
    throw new Error("--par : temps, aspect, zone ou corps");
  return o;
}

function liste() {
  const l = [];
  l.push("LES NIVEAUX — cumulatifs. `--niveau 3` contient tout le 2.");
  for (const n of NIVEAUX) {
    l.push("");
    l.push("  " + n.n + ". " + n.nom + " — " + n.dit);
    l.push("     " + n.quoi.join(", "));
  }
  l.push("");
  l.push("LES ASPECTS — en travers, et ils se recouvrent. `--aspect a,b`.");
  for (const [k, a] of Object.entries(ASPECTS)) {
    l.push("");
    l.push("  " + k + " — " + a.nom + " : " + a.dit);
    if (a.quoi.length) l.push("     " + a.quoi.join(", "));
  }
  return l.join("\n");
}

// ---------------------------------------------------------------------------
function charger(fichier) {
  const brut = JSON.parse(fs.readFileSync(fichier, "utf8"));
  if (!Array.isArray(brut.detail) || !Array.isArray(brut.recit))
    throw new Error(fichier + " n'a pas la forme d'annales (detail + recit)");
  if (brut.detail.length !== brut.recit.length)
    throw new Error("annales incohérentes : " + brut.recit.length + " lignes " +
                    "pour " + brut.detail.length + " faits — recuisez le sac");
  // LES DEUX VONT ENSEMBLE, ET DÉSORMAIS ELLES NE SE SÉPARENT PLUS. Un filtre
  // qui trierait `detail` sans emporter `recit` recollerait des phrases sur les
  // mauvais faits, et le document mentirait sans qu'aucune ligne ait l'air faux.
  return {
    entete: brut,
    faits: brut.detail.map((d, i) => ({ d, ligne: brut.recit[i], i })),
  };
}

function filtrer(faits, o) {
  const dep = secondes(o.depuis), jus = secondes(o.jusqua);
  const quoi = o.quoi ? new Set(String(o.quoi).split(",").map((s) => s.trim())) : null;
  const sauf = o.sauf ? new Set(String(o.sauf).split(",").map((s) => s.trim())) : null;
  const aspects = o.aspect
    ? String(o.aspect).split(",").map((s) => s.trim()).filter(Boolean) : null;
  if (aspects) for (const a of aspects)
    if (!(a in ASPECTS)) throw new Error("aspect inconnu : " + a +
      " (connus : " + Object.keys(ASPECTS).join(", ") + ")");
  const cherche = (v, aig) => v != null &&
    String(v).toLowerCase().includes(String(aig).toLowerCase());

  return faits.filter(({ d }) => {
    if (sauf && sauf.has(d.quoi)) return false;
    // `--quoi` est une DÉSIGNATION, pas un filtre de plus : quand on nomme les
    // faits qu'on veut, le niveau et l'aspect n'ont plus voix — sinon
    // `--quoi habitant --niveau 1` rendrait un fichier vide, et l'on chercherait
    // longtemps pourquoi.
    if (quoi) return quoi.has(d.quoi);
    if (niveauDe(d.quoi) > o.niveau) return false;
    if (aspects && !aspectsDe(d.quoi).some((a) => aspects.includes(a))) return false;
    if (dep != null && d.t < dep) return false;
    if (jus != null && d.t > jus) return false;
    if (o.zone && !(cherche(d.zone, o.zone) || cherche(d.quartier, o.zone) ||
                    cherche(d.repere, o.zone) || cherche(d.ou, o.zone))) return false;
    if (o.corps && !(cherche(d.corps, o.corps) || cherche(d.chef, o.corps))) return false;
    if (o.camp && !cherche(d.camp, o.camp)) return false;
    return true;
  });
}

// ---------------------------------------------------------------------------
// LE GROUPEMENT — un titre, et sous lui des lignes déjà écrites.
// ---------------------------------------------------------------------------
function grouper(faits, o) {
  if (o.par === "temps") {
    const tr = secondes(o.tranche);
    if (!tr) return [{ titre: null, faits }];
    const par = new Map();
    for (const f of faits) {
      const k = Math.floor(f.d.t / tr);
      if (!par.has(k)) par.set(k, []);
      par.get(k).push(f);
    }
    return [...par.entries()].sort((a, b) => a[0] - b[0]).map(([k, ff]) => ({
      titre: HEURE(k * tr) + " – " + HEURE((k + 1) * tr), faits: ff,
    }));
  }
  if (o.par === "aspect") {
    // UN FAIT, UNE SECTION. Il en sert plusieurs, mais le classer partout
    // doublerait le document et l'on relirait deux fois la même ligne en
    // croyant à deux faits. Il est donc rangé sous le PREMIER aspect de la
    // liste qui le réclame, et l'ordre de `ASPECTS` est cette décision-là.
    const ordre = Object.keys(ASPECTS);
    const par = new Map();
    for (const f of faits) {
      const k = aspectsDe(f.d.quoi).sort((a, b) => ordre.indexOf(a) - ordre.indexOf(b))[0];
      if (!par.has(k)) par.set(k, []);
      par.get(k).push(f);
    }
    return ordre.filter((k) => par.has(k)).map((k) => ({
      titre: ASPECTS[k].nom, sous: ASPECTS[k].dit, faits: par.get(k),
    }));
  }
  const clef = o.par === "zone" ? (d) => d.zone || d.quartier || "sans zone"
                                : (d) => d.corps || d.chef || "sans corps";
  const par = new Map();
  for (const f of faits) {
    const k = clef(f.d);
    if (!par.has(k)) par.set(k, []);
    par.get(k).push(f);
  }
  return [...par.entries()].sort((a, b) => b[1].length - a[1].length)
    .map(([k, ff]) => ({ titre: k, faits: ff }));
}

// ---------------------------------------------------------------------------
function rendre(source, entete, retenus, total, groupes, o) {
  const l = [];
  const niv = NIVEAUX.find((n) => n.n === o.niveau);
  l.push("# " + (entete.porte || "La bataille") + " — " +
         (o.quoi ? "faits désignés" : niv.nom));
  l.push("");
  l.push("> " + retenus + " faits sur " + total + " · " +
         (entete.hommes || "?") + " hommes · " +
         "cuisson de " + (entete.duree_s || "?") + " s");
  l.push("");
  // CE QUI A ÉTÉ DEMANDÉ S'ÉCRIT DANS LE DOCUMENT. Une vue sans sa question
  // est un compte rendu dont on ne sait plus ce qu'il tait — et six semaines
  // plus tard on la lit comme si elle était complète.
  const dem = [];
  if (o.quoi) dem.push("faits : " + o.quoi);
  else {
    dem.push("niveau " + o.niveau + " (" + niv.nom + ")");
    if (o.aspect) dem.push("aspects : " + String(o.aspect).split(",")
      .map((a) => ASPECTS[a.trim()].nom.toLowerCase()).join(", "));
  }
  if (o.sauf) dem.push("sauf : " + o.sauf);
  if (o.depuis) dem.push("depuis " + HEURE(secondes(o.depuis)));
  if (o.jusqua) dem.push("jusqu'à " + HEURE(secondes(o.jusqua)));
  if (o.zone) dem.push("zone ~ « " + o.zone + " »");
  if (o.corps) dem.push("corps ~ « " + o.corps + " »");
  if (o.camp) dem.push("camp ~ « " + o.camp + " »");
  l.push("**Ce qu'on a demandé :** " + dem.join(" · ") + ".");
  l.push("");
  l.push("*Vue tirée de `" + path.relative(RACINE, source).replace(/\\/g, "/") +
         "` par `scripts/monde/annales.js`. La source est complète ; " +
         "ce document ne l'est pas. Ni l'une ni l'autre ne s'écrit à la main.*");
  l.push("");

  if (!retenus) {
    l.push("---");
    l.push("");
    l.push("**Rien ne répond à cette demande.** Le sac contient bien des faits — " +
           "ce sont les bornes qui ne laissent rien passer. Élargissez le " +
           "niveau, ou `--liste` pour voir ce qui existe.");
    return l.join("\n") + "\n";
  }

  for (const g of groupes) {
    if (g.titre) {
      l.push("## " + g.titre);
      if (g.sous) l.push("");
      if (g.sous) l.push("*" + g.sous + "*");
      l.push("");
    }
    for (const f of g.faits) l.push("- " + f.ligne);
    l.push("");
  }
  return l.join("\n");
}

// ---------------------------------------------------------------------------
function etiquette(o) {
  if (o.quoi) return String(o.quoi).split(",")[0].trim() + (String(o.quoi).includes(",") ? "+" : "");
  let e = "n" + o.niveau;
  if (o.aspect) e += "-" + String(o.aspect).split(",").map((s) => s.trim()).join("+");
  if (o.depuis || o.jusqua) e += "-" + (o.depuis || "0") + "a" + (o.jusqua || "fin");
  if (o.zone) e += "-" + String(o.zone).toLowerCase().replace(/[^a-z0-9]+/g, "");
  return e;
}

function main() {
  const o = args();
  if (o.liste) { console.log(liste()); return; }
  if (!o.fichier) {
    console.error("usage : node scripts/monde/annales.js <fichier.annales.json> " +
                  "[--niveau 1-4] [--aspect …] [--depuis 5m] [--par aspect]\n" +
                  "        node scripts/monde/annales.js --liste");
    process.exit(2);
  }
  const source = path.resolve(o.fichier);
  const { entete, faits } = charger(source);

  // Ce que le four sait dire et que ce fichier ne classe pas encore. On ne
  // l'enterre pas : c'est le seul avertissement qui empêche une vue de mentir
  // par omission après un ajout dans `bataille2d.js`.
  const orphelins = [...new Set(faits.map((f) => f.d.quoi))].filter((q) => !CONNUS.has(q));
  if (orphelins.length && !o.muet)
    console.error("annales : " + orphelins.length + " type(s) hors classement, " +
                  "tenus pour niveau 4 / aspect « divers » — " + orphelins.join(", ") +
                  " (à ranger dans NIVEAUX et ASPECTS de ce script)");

  const retenus = filtrer(faits, o);
  const groupes = grouper(retenus, o);
  const texte = rendre(source, entete, retenus.length, faits.length, groupes, o);

  // `--sortie -` ÉCRIT SUR LA SORTIE STANDARD au lieu d'un fichier. C'est ce
  // qui permet à un autre outil de se servir du classement par niveau sans le
  // recopier chez lui : `scripts/bataille.py --maintenant` appelle ce script
  // pour ne montrer au MJ que ce qu'un rapport retiendrait du quart d'heure qui
  // vient. Une table de niveaux tenue à deux endroits diverge le jour où l'on
  // ajoute un fait, et c'est le genre de divergence qu'on ne voit jamais.
  const base = path.basename(source).replace(/\.annales\.json$/, "");
  if (o.sortie === "-") { process.stdout.write(texte); return; }
  const sortie = o.sortie
    ? path.resolve(o.sortie)
    : path.join(RACINE, "exports", base + "." + etiquette(o) + ".md");
  fs.mkdirSync(path.dirname(sortie), { recursive: true });
  fs.writeFileSync(sortie, texte, "utf8");

  if (o.json) {
    const parQuoi = {};
    for (const f of retenus) parQuoi[f.d.quoi] = (parQuoi[f.d.quoi] || 0) + 1;
    const j = {
      _lisez_moi:
        "UNE VUE, PAS LA SOURCE. Tirée de " + path.basename(source) + " par " +
        "scripts/monde/annales.js ; il en manque ce que le filtre a écarté. " +
        "Même forme que les annales complètes, donc elle se refiltre — mais on " +
        "ne filtre jamais deux fois de suite sans le savoir : reprenez la source.",
      tiree_de: path.basename(source), demande: o,
      porte: entete.porte, hommes: entete.hommes, duree_s: entete.duree_s,
      faits: retenus.length, sur: faits.length, par_quoi: parQuoi,
      recit: retenus.map((f) => f.ligne),
      detail: retenus.map((f) => f.d),
    };
    const fj = sortie.replace(/\.md$/, "") + ".annales.json";
    fs.writeFileSync(fj, JSON.stringify(j, null, 1), "utf8");
    if (!o.muet) console.error("annales : " + path.relative(RACINE, fj).replace(/\\/g, "/"));
  }

  console.log(path.relative(RACINE, sortie).replace(/\\/g, "/") + " — " +
              retenus.length + " faits sur " + faits.length +
              " · " + groupes.length + " section(s)");
}

try { main(); }
catch (e) { console.error("annales : " + e.message); process.exit(1); }
