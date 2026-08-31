// CHAMBRE-LIVRES — les coffrets de chambre de l'onglet « Les livres ».
//
// Les chambres ne sont PAS des livres d'état : rien d'ici ne s'écrit dans
// `etat/books.json` ni ailleurs. On ASSEMBLE À LA VOLÉE, en lecture seule de
// `chambres/`, des boîtes virtuelles au format exact de `etat/boites.json` et
// des volumes au format de `etat/books.json` — le front les rend sans savoir
// qu'ils n'existent sur aucune étagère.
//
// LE BROUILLARD EST CELUI DU SIÈGE, décidé ici même : un siège incarné voit SA
// chambre ; un siège de régie voit un coffret par habitant dont la chambre a
// du contenu ; un siège du roster ne voit la sienne que s'il en a une. Chaque
// volume servi porte `acteur_id` = le personnage du REGARDEUR : c'est ce qui
// le fait passer le brouillard du front (`portee.js` : « sur moi, toujours
// visible ») sans toucher une ligne du rendu.
//
// SEEDÉ-VIDE NE FAIT PAS DE VOLUME. Une fiche de relation qui ne porte que son
// titre et sa ligne de semis (« Je n'ai encore rien écrit de lui ») n'est pas
// un volume ; un `en-souffrance.json` aux listes vides non plus. Et la chambre
// dont il ne reste QUE le claude.md de semis (« Je n'y ai encore rien écrit »)
// n'a pas de coffret : cent vingt-deux chambres semées feraient cent vingt-deux
// onglets qui mentent.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");

const CHAMBRES = path.join(RACINE, "chambres");

function lireTexte(p) {
  try { return fs.readFileSync(p, "utf-8"); } catch (e) { return ""; }
}
function lireJson(p, defaut) {
  try { return JSON.parse(fs.readFileSync(p, "utf-8")); } catch (e) { return defaut; }
}

// Le nom d'un habitant : sa fiche s'il en a une ; le MJ n'a pas de fiche.
function carteDesNoms() {
  const noms = {};
  const liste = lireJson(path.join(RACINE, "etat", "personnages.json"), []);
  (Array.isArray(liste) ? liste : []).forEach((p) => {
    if (p && p.id) noms[p.id] = p.nom || p.id;
  });
  return noms;
}
function nomDe(noms, id) {
  if (id === "mj") return "Le MJ";
  return noms[id] || String(id || "").replace(/-/g, " ");
}

// ---- le markdown brut, en pages -------------------------------------------
// Le lecteur du front rend chaque page en un paragraphe (`poser` : texte
// échappé, `**gras**` respecté). On découpe donc aux lignes vides, et l'on
// détache titres et items de liste — un item de liste noyé dans un pavé ne se
// lit plus. Les fichiers sont durs-pliés à ~75 colonnes : les lignes d'un même
// bloc se recollent d'une espace.
function pagesDe(md) {
  const pages = [];
  let bloc = [];
  const fermer = () => {
    if (bloc.length) {
      // Un titre `#` se rend en gras : le lecteur (`poser`) ne connaît que
      // `**…**`, et un croisillon brut à l'écran est du bruit.
      let t = bloc.join(" ").trim();
      const m = /^#{1,6}\s+(.*)$/.exec(t);
      if (m) t = "**" + m[1].replace(/\*\*/g, "") + "**";
      pages.push(t);
    }
    bloc = [];
  };
  String(md || "").split(/\r?\n/).forEach((l) => {
    if (!l.trim()) return fermer();
    if (/^(#{1,6}\s|[-*]\s|\d+[.)]\s)/.test(l.trim())) fermer();
    bloc.push(l.trim());
  });
  fermer();
  return pages.filter(Boolean);
}

// Une fiche de relation seedée-vide : rien d'autre que des titres, des lignes
// vides et la ligne de semis en italique (« *Vu le … Je n'ai encore rien
// écrit de lui.* »). Elle ne fait pas de volume.
function ficheVide(md) {
  return !String(md || "").split(/\r?\n/).some((l) => {
    const t = l.trim();
    return t && t[0] !== "#" && !/^\*[^*].*\*$/.test(t);
  });
}

// Le claude.md de semis : l'habitant y dit lui-même qu'il n'a rien écrit.
// Il compte pour la porte du COFFRET (une chambre qui n'a que ça n'en a pas),
// mais s'il y a coffret, il s'y range — c'est sa manière, elle se lit.
// Deux formes historiques de semis restent lisibles dans les archives.
const estSemis = (md) => md.indexOf("Je n'y ai encore rien écrit") !== -1
  || md.indexOf("Ce cahier s'ouvre vide") !== -1;

// ---- les dates du monde ---------------------------------------------------
const jourAbs = (d) => (d && d.annee != null)
  ? ((d.annee * 12 + ((d.lune || 1) - 1)) * 30) + ((d.jour || 1) - 1) : null;
const dateDite = (d) => (d && d.annee != null)
  ? "le " + d.jour + "e j., " + d.lune + "e lune" : "sans jour";
function depuisDit(d, aujourdhui) {
  const a = jourAbs(d);
  if (a === null) return "sans jour";
  if (aujourdhui === null) return dateDite(d);
  const n = aujourdhui - a;
  if (n <= 0) return "aujourd'hui";
  return (n === 1 ? "hier" : "il y a " + n + " j.") + " (" + dateDite(d) + ")";
}
// Le jour du monde : l'horloge de l'habitant s'il en tient une, celle du
// siège principal à défaut — le MJ n'a pas d'horloge.
function jourDuMonde(h) {
  const horloges = lireJson(path.join(RACINE, "etat", "horloges.json"), {});
  if (horloges[h]) return jourAbs(horloges[h]);
  const roster = lireJson(path.join(RACINE, "etat", "joueurs.json"), []);
  const principal = (Array.isArray(roster) ? roster : [])
    .find((s) => s.role === "principal");
  return principal ? jourAbs(horloges[principal.personnage_id]) : null;
}

// ---- les deux coffrets d'un habitant --------------------------------------
// `regardeur` est le personnage du siège qui regarde : chaque volume et chaque
// boîte le portent en `acteur_id` (voir l'en-tête). `prive` dit le fond des
// choses — une chambre ne se montre pas — même si c'est le serveur qui trie.
function coffretsDe(h, regardeur, noms) {
  const dossier = path.join(CHAMBRES, h);
  const nom = nomDe(noms, h);
  const commun = { acteur_id: regardeur, prive: true, tenu_par: h };

  // 1. « Sa chambre » — les écrits de sa main.
  const chambre = [];
  const maniere = lireTexte(path.join(dossier, "claude.md"));
  if (maniere.trim()) {
    chambre.push(Object.assign({
      id: "chambre-" + h + "-maniere", boite: "chambre-" + h,
      titre: "Sa manière, de sa main", type: "carnet", embleme: "📜",
      pages: pagesDe(maniere) }, commun));
  }
  const demain = lireTexte(path.join(dossier, "demain.md"));
  if (demain.trim()) {
    chambre.push(Object.assign({
      id: "chambre-" + h + "-demain", boite: "chambre-" + h,
      titre: "Là où il s'est laissé", type: "carnet", embleme: "🌙",
      pages: pagesDe(demain) }, commun));
  }
  let brouillons = [];
  try { brouillons = fs.readdirSync(path.join(dossier, "brouillons")).sort(); }
  catch (e) {}
  brouillons.forEach((f) => {
    const texte = lireTexte(path.join(dossier, "brouillons", f));
    if (!texte.trim()) return;
    const slug = f.replace(/\.[^.]+$/, "");
    chambre.push(Object.assign({
      id: "chambre-" + h + "-brouillon-" + slug, boite: "chambre-" + h,
      titre: "Brouillon — " + slug.replace(/-/g, " "), type: "carnet",
      embleme: "✍️", pages: pagesDe(texte) }, commun));
  });
  let relations = [];
  try { relations = fs.readdirSync(path.join(dossier, "relations")).sort(); }
  catch (e) {}
  relations.forEach((autre) => {
    const fiche = lireTexte(path.join(dossier, "relations", autre, "claude.md"));
    if (!fiche.trim() || ficheVide(fiche)) return;
    chambre.push(Object.assign({
      id: "chambre-" + h + "-fiche-" + autre, boite: "chambre-" + h,
      titre: "Sa fiche sur " + nomDe(noms, autre), type: "carnet",
      embleme: "👤", pages: pagesDe(fiche) }, commun));
  });

  // 2. « Ses affaires » — les deux JSON, rendus en tables, jamais en JSON brut.
  const affaires = [];
  const aujourdhui = jourDuMonde(h);
  const souffrance = lireJson(path.join(dossier, "en-souffrance.json"), {});
  const jAttends = Array.isArray(souffrance.j_attends) ? souffrance.j_attends : [];
  const onAttend = Array.isArray(souffrance.on_attend_de_moi)
    ? souffrance.on_attend_de_moi : [];
  if (jAttends.length || onAttend.length) {
    const tables = [];
    if (jAttends.length) {
      tables.push({
        titre: "⏳ J'attends", colonnes: ["De", "Quoi", "Depuis", "État"],
        lignes: jAttends.map((f) => ({
          cellules: ["**" + nomDe(noms, f.de) + "**", f.quoi || "",
            depuisDit(f.demande_le, aujourdhui) + (f.heure ? ", " + f.heure : ""),
            f.etat || ""],
          note: [f.borne ? "Borne : " + f.borne : "",
            f.ce_qui_en_depend ? "En dépend : " + f.ce_qui_en_depend : ""]
            .filter(Boolean).join(" — ") || undefined,
        })),
      });
    }
    if (onAttend.length) {
      tables.push({
        titre: "🤝 On attend de moi",
        colonnes: ["Pour", "Quoi", "Pour quand", "Tenu"],
        lignes: onAttend.map((f) => ({
          cellules: ["**" + nomDe(noms, f.pour) + "**", f.quoi || "",
            f.du ? dateDite(f.du) + (f.heure ? ", " + f.heure : "") : "sans jour",
            f.tenu ? "✅ tenu" : "❌ pas encore"],
          note: f.note || undefined,
        })),
      });
    }
    affaires.push(Object.assign({
      id: "chambre-" + h + "-souffrance", boite: "affaires-" + h,
      titre: "En souffrance", type: "registre", embleme: "⏳",
      sous_titre: souffrance.quoi || "", tables: tables,
      pages: souffrance.regle ? [souffrance.regle] : [] }, commun));
  }
  const pannes = lireJson(path.join(dossier, "problemes.json"), {});
  const entrees = Array.isArray(pannes.entrees) ? pannes.entrees : [];
  if (entrees.length) {
    affaires.push(Object.assign({
      id: "chambre-" + h + "-pannes", boite: "affaires-" + h,
      titre: "Pannes de l'appareil", type: "dossier", embleme: "🛠️",
      sous_titre: pannes.quoi || "",
      tables: [{
        titre: "🛠️ Entrées",
        colonnes: ["N°", "Date", "Quoi", "Gravité", "État"],
        lignes: entrees.map((e) => ({
          cellules: [e.id || "", dateDite(e.date), e.quoi || "",
            e.gravite || "", e.etat || ""],
          note: e.ce_que_j_y_fais || undefined,
        })),
      }],
      pages: pannes.ce_que_ces_entrees_ont_en_commun
        ? [pannes.ce_que_ces_entrees_ont_en_commun] : [] }, commun));
  }

  // 3. « Ses volumes » — chambres/<h>/books/ : des volumes déjà AU FORMAT de
  // `etat/books.json` (les .json, servis tels quels) ou du markdown (les .md,
  // rendus en pages comme les brouillons). Rien n'y fait foi — leur sous-titre
  // le dit souvent lui-même — mais ce sont ses cahiers, sous sa main. On ne
  // garde du .json que son CONTENU : sa place (lieu, salle, lecteurs) est
  // écrasée par celle de la boîte virtuelle, sinon un volume de chambre qui se
  // dit posé quelque part passerait le brouillard du front pour tout le monde.
  const volumes = [];
  let cahiers = [];
  try { cahiers = fs.readdirSync(path.join(dossier, "books")).sort(); }
  catch (e) {}
  cahiers.forEach((f) => {
    const p = path.join(dossier, "books", f);
    if (/\.json$/i.test(f)) {
      const livre = lireJson(p, null);
      if (!livre || Array.isArray(livre) || typeof livre !== "object") return;
      const v = Object.assign({}, livre, commun, {
        id: "chambre-" + h + "-" + String(livre.id || f.replace(/\.[^.]+$/, "")),
        boite: "volumes-" + h,
        lieu_id: null, salle_id: null, lecteurs: undefined,
        tenu_par: livre.tenu_par || h,
      });
      volumes.push(v);
      return;
    }
    if (!/\.md$/i.test(f)) return;
    const texte = lireTexte(p);
    if (!texte.trim()) return;
    const slug = f.replace(/\.[^.]+$/, "");
    // Le titre est la première ligne `#` du cahier ; le nom du fichier à défaut.
    const entete = /^#\s+(.+)$/m.exec(texte);
    volumes.push(Object.assign({
      id: "chambre-" + h + "-cahier-" + slug, boite: "volumes-" + h,
      titre: entete ? entete[1].trim() : slug.replace(/-/g, " "),
      type: "carnet", embleme: "📓",
      pages: pagesDe(texte) }, commun));
  });

  // La porte du coffret : une chambre dont il ne reste que le semis n'en a pas.
  const seulLeSemis = chambre.length === 1 && !affaires.length && !volumes.length
    && chambre[0].id === "chambre-" + h + "-maniere" && estSemis(maniere);
  const books = [];
  const boites = [];
  if (chambre.length && !seulLeSemis) {
    boites.push({ id: "chambre-" + h, titre: "Sa chambre — " + nom,
      sous_titre: "Les écrits de sa main : sa manière, ses brouillons, ses fiches.",
      embleme: "🛏️", couleur: "var(--book-carnet)",
      acteur_id: regardeur, prive: true });
    books.push.apply(books, chambre);
  }
  if (affaires.length && !seulLeSemis) {
    boites.push({ id: "affaires-" + h, titre: "Ses affaires — " + nom,
      sous_titre: "Ce qu'il attend, ce qu'on attend de lui, et les pannes de l'appareil.",
      embleme: "⚖️", couleur: "var(--book-dossier)",
      acteur_id: regardeur, prive: true });
    books.push.apply(books, affaires);
  }
  if (volumes.length && !seulLeSemis) {
    boites.push({ id: "volumes-" + h, titre: "Ses volumes — " + nom,
      sous_titre: "Les cahiers de sa chambre, de sa main — rien n'y fait foi.",
      embleme: "📚", couleur: "var(--book-memento)",
      acteur_id: regardeur, prive: true });
    books.push.apply(books, volumes);
  }
  return { books, boites };
}

// ---- l'entrée : quels coffrets pour ce siège ------------------------------
// `siege` vient de `qui()` (null en mono-joueur), `moi` de `monPersonnage()`.
function coffretsChambre(siege, moi) {
  const vide = { books: [], boites: [] };
  if (!moi) return vide;
  const noms = carteDesNoms();
  // La régie voit un coffret par habitant dont la chambre a du contenu.
  if (siege && siege.regie) {
    let habitants = [];
    try {
      habitants = fs.readdirSync(CHAMBRES).filter((n) => {
        try { return fs.statSync(path.join(CHAMBRES, n)).isDirectory(); }
        catch (e) { return false; }
      });
    } catch (e) { return vide; }
    habitants.sort((a, b) => nomDe(noms, a).localeCompare(nomDe(noms, b), "fr"));
    const tout = { books: [], boites: [] };
    habitants.forEach((h) => {
      const c = coffretsDe(h, moi, noms);
      tout.books.push.apply(tout.books, c.books);
      tout.boites.push.apply(tout.boites, c.boites);
    });
    return tout;
  }
  // Tout autre siège — incarné hors roster, PJ du roster, mono-joueur — ne
  // voit que SA chambre, s'il en a une qui porte quelque chose.
  try {
    if (!fs.statSync(path.join(CHAMBRES, moi)).isDirectory()) return vide;
  } catch (e) { return vide; }
  return coffretsDe(moi, moi, noms);
}

module.exports = { coffretsChambre };
