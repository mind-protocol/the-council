// -*- coding: utf-8 -*-
/**
 * VERIFIER — une commande, tous les etalons, un code de sortie.
 *
 *     node scripts/verifier.mjs              les gardes, puis les mesures
 *     node scripts/verifier.mjs --long       ajoute ce qui coute des minutes
 *     node scripts/verifier.mjs --seul tick  n'execute que ce qui matche
 *     node scripts/verifier.mjs --bavard     imprime la sortie entiere de chacun
 *
 * POURQUOI CE FICHIER EXISTE. Le depot avait dix-huit epreuves et aucune facon
 * de les lancer : il fallait connaitre dix-huit chemins, se souvenir lesquels
 * exigeaient un serveur, et savoir d'avance lesquels sont rouges pour de bonnes
 * raisons. Une verification qu'on ne peut pas invoquer d'un mot n'est pas une
 * verification : c'est une documentation. `batailles` a `node coding/fumee.mjs`
 * et le pose comme une propriete d'architecture ; c'en est une ici aussi,
 * depuis que les quatre bancs qui reclamaient `localhost:3129` lisent le monde
 * par la route en memoire (`scripts/monde/monde_local.js`).
 *
 * LE MANIFESTE EST LA DECISION, PAS UNE LISTE. Comme `bataille/moteur/chaine.js`
 * pour l'ordre de chargement : ce qui verifie ce depot est ENONCE ici, une fois,
 * avec le rang de chaque epreuve et la raison de ce rang. Une epreuve neuve
 * entre par ce fichier, et par lui seul — sinon l'on retombe sur des listes qui
 * divergent en silence, ce que ce depot a deja paye.
 *
 * DEUX RANGS, ET LE SECOND EST CE QUI REND LE PREMIER TENABLE.
 *
 *   - GARDE : un etalon a tolerance zero, VERT AUJOURD'HUI. Un rouge fait sortir
 *     la commande en 1. C'est ce qu'on met dans un hook de commit et dans une CI.
 *
 *   - MESURE : une sonde qui rend un CHIFFRE ou un diagnostic, et qui est rouge
 *     pour une raison de fond qu'on n'a pas encore reglee. Elle s'imprime, elle
 *     ne barre jamais la route.
 *
 * Le second rang n'est pas une indulgence, c'est la condition de survie du
 * premier. Une commande rouge des le premier jour est une commande qu'on
 * debranche le jour meme — c'est le meme raisonnement que le plafond en cliquet
 * de `.claude/hooks/taille.js` : on n'exige pas de reparer ce qui est deja
 * casse, on interdit que ca empire. Le rang de chaque epreuve ci-dessous a ete
 * MESURE, jamais suppose : chaque `secondes` et chaque `rang` sortent d'une
 * execution reelle le 30 du 8e mois 2026. Les `secondes` sont l'horloge du mur
 * SOUS la concurrence de cette commande — c'est le chiffre utile, pas le temps
 * qu'une epreuve prendrait seule sur une machine au repos.
 *
 * UNE MESURE QUI PASSE AU VERT DOIT MONTER EN GARDE, et la commande le dit
 * quand ca arrive. Sans quoi le second rang deviendrait le cimetiere ou l'on
 * range ce qu'on ne veut plus regarder.
 */
import { spawn } from "node:child_process";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const ICI = path.dirname(fileURLToPath(import.meta.url));
const RACINE = path.dirname(ICI);
const PY = process.env.PYTHON || "python";

// ---------------------------------------------------------------------------
// LE MANIFESTE
// ---------------------------------------------------------------------------
const EPREUVES = [
  // --- LES GARDES -----------------------------------------------------------
  {
    id: "banc-moteur", rang: "garde", secondes: 20,
    commande: ["node", "ecrans/modules/bataille/banc-moteur.js"],
    pourquoi: "L'etalon du moteur : l'issue et les annales comparees a zero tolerance. "
      + "C'est celui qui voit un deplacement de blocs.",
  },
  {
    id: "banc-monde", rang: "garde", secondes: 11,
    commande: ["node", "ecrans/modules/bataille/banc-monde.js"],
    pourquoi: "La ville sous les pieds : densites, distances au chef, unites.",
  },
  {
    id: "banc-combattant", rang: "garde", secondes: 11,
    commande: ["node", "ecrans/modules/bataille/banc-combattant.js"],
    pourquoi: "Les etiquettes de pensee reellement vues par la couche combattant.",
  },
  {
    id: "banc-commandement", rang: "garde", secondes: 0.1,
    commande: ["node", "ecrans/modules/bataille/banc-commandement.js"],
    pourquoi: "Le brouillard du commandement : ce qu'une parole transmet, et ce "
      + "qu'elle ne transmet pas. Douze assertions, sans charger de monde.",
  },
  {
    id: "banc-formation", rang: "garde", secondes: 12,
    commande: ["node", "ecrans/modules/bataille/banc-formation.js"],
    pourquoi: "Les formations tiennent leur forme sous le terrain.",
  },
  {
    id: "banc-circulation", rang: "garde", secondes: 1,
    commande: ["node", "ecrans/modules/bataille/banc-circulation.js"],
    pourquoi: "La circulation dans les rues : ce qui bouchonne et ce qui passe.",
  },
  {
    id: "banc-pensees", rang: "garde", secondes: 4,
    commande: ["node", "ecrans/modules/bataille/banc-pensees.js"],
    pourquoi: "Un comportement qui n'emet rien n'existe pas : les annales sont tenues.",
  },
  {
    id: "banc-reflexion-adapt", rang: "garde", secondes: 0.1,
    commande: ["node", "ecrans/modules/bataille/banc-reflexion-adapt.js"],
    pourquoi: "La prise de la couche 2 : onze signaux batis depuis la bataille.",
  },
  {
    id: "banc-qui-conduit", rang: "garde", secondes: 0.1,
    commande: ["node", "ecrans/modules/survival-stack/banc-qui-conduit.js"],
    pourquoi: "Qui conduit l'homme, couche par couche.",
  },
  {
    id: "banc-tick", rang: "garde", secondes: 0.9,
    commande: [PY, "scripts/analyse/banc_tick.py"],
    pourquoi: "L'etalon du hors-scene : la proposition de `tick.py` sur un `etat/` "
      + "fige, comparee clef par clef. La seule epreuve des 3 200 lignes qui "
      + "calculent les horloges, les echeances et les nouvelles.",
  },
  {
    id: "tests-python", rang: "garde", secondes: 0.4,
    commande: [PY, "-m", "unittest", "discover", "-s", "scripts/tests", "-p", "test_*.py"],
    pourquoi: "Les tests unitaires du Python — bibliotheque, plan, mesures.",
  },
  {
    id: "incendie-ville", rang: "garde", secondes: 1.5,
    commande: ["node", "scripts/tests/incendie-ville.test.mjs"],
    pourquoi: "La propagation d'un incendie dans la ville.",
  },
  {
    id: "serveur-bibliotheque", rang: "garde", secondes: 0.1,
    commande: ["node", "serveur/test_bibliotheque.js"],
    pourquoi: "La bibliotheque du serveur. Ecrit dans un dossier temporaire, "
      + "jamais dans `etat/`.",
  },
  {
    id: "serveur-piece-http", rang: "garde", secondes: 0.2,
    commande: ["node", "serveur/test_piece_http.js"],
    pourquoi: "La route /piece de bout en bout. Ouvre un port EPHEMERE (listen 0) "
      + "et non le 3129 : lancer la verification ne derange pas une partie en cours.",
  },
  {
    id: "porte-etat", rang: "garde", secondes: 2.6,
    commande: [PY, "scripts/noyau/tables.py", "--verifier"],
    compte: /^(\d+) fichier\(s\)/m,
    pourquoi: "Personne n'ecrit dans `etat/` sans passer par la porte unique. "
      + "Mesure nee a 45, descendue a 0 par groupes (un commit par groupe), "
      + "promue GARDE le jour du zero : le quarante-sixieme ecrivain sauvage "
      + "est refuse ici, pas decouvert trois lunes plus tard.",
  },

  // --- LES MESURES ----------------------------------------------------------
  {
    id: "banc-epreuve", rang: "mesure", secondes: 43,
    commande: ["node", "ecrans/modules/bataille/banc-epreuve.js"],
    compte: /(\d+) sonde\(s\) rouge\(s\)/,
    pourquoi: "Quatre sondes rouges de FOND, pas de regression : les cavaliers ne "
      + "tirent pas d'allure superieure, aucune pique ne recoit de charge, aucun "
      + "chef n'adapte son ordre apres renseignement. Ces sondes etaient deja la "
      + "— elles etaient seulement impossibles a lancer, faute de serveur.",
  },
  {
    id: "banc-dynamiques", rang: "mesure", long: true, secondes: 399,
    commande: ["node", "ecrans/modules/bataille/banc-dynamiques.js"],
    compte: /(\d+) NON/,
    pourquoi: "Les quatre sondes de `banc-epreuve` et quatre autres. Sept minutes : "
      + "hors du passage ordinaire, il ne tourne qu'avec --long.",
  },
  {
    id: "coherence-etat", rang: "mesure", secondes: 9.4,
    commande: [PY, "scripts/tick.py", "--verifier"],
    compte: null,
    pourquoi: "L'audit de coherence de la PARTIE — tetes en retard, croyances sans "
      + "porteur. Il parle du contenu du jeu, jamais du code : il ne peut pas "
      + "garder une porte, et il vieillit a chaque tour joue.",
  },
  {
    id: "graphe-archi", rang: "mesure", secondes: 1.5,
    commande: [PY, "scripts/analyse/graphe_archi.py", "--json"],
    compte: null,
    resume: (sortie) => {
      const d = JSON.parse(sortie);
      return d.orphelins.length + " orphelins · " + d.hors_porte.length
        + " hors porte · " + d.remontees.length + " remontees · "
        + d.commandes_bibliotheques.length + " commandes-bibliotheques";
    },
    pourquoi: "Les quatre ecarts entre la declaration (docs/containers.json) et le "
      + "cablage reel : orphelins, liens hors porte, dependances qui remontent, "
      + "commandes racine importees comme modules. Quatre chiffres qui ne doivent "
      + "que DESCENDRE — c'est la distance du chantier d'organisation.",
  },
];

// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
const aLOption = (n) => args.includes("--" + n);
const valeurDe = (n) => { const i = args.indexOf("--" + n); return i >= 0 ? args[i + 1] : null; };

const LONG = aLOption("long");
const BAVARD = aLOption("bavard");
const SEUL = valeurDe("seul");
const PLAFOND = 900_000;          // 15 min : au-dela, l'epreuve est pendue

function choisies() {
  return EPREUVES.filter((e) => {
    if (SEUL && !e.id.includes(SEUL)) return false;
    if (e.long && !LONG && !SEUL) return false;
    return true;
  });
}

function lancer(epreuve) {
  return new Promise((resoudre) => {
    const debut = Date.now();
    const [exe, ...reste] = epreuve.commande;
    const fils = spawn(exe, reste, { cwd: RACINE, shell: false });
    let sortie = "";
    const prendre = (d) => { sortie += d.toString(); };
    fils.stdout.on("data", prendre);
    fils.stderr.on("data", prendre);
    const minuterie = setTimeout(() => {
      fils.kill("SIGKILL");
      sortie += "\n[verifier] tue apres " + (PLAFOND / 1000) + " s";
    }, PLAFOND);
    fils.on("error", (e) => {
      clearTimeout(minuterie);
      resoudre({ epreuve, code: 127, sortie: String(e.message), duree: 0 });
    });
    fils.on("close", (code) => {
      clearTimeout(minuterie);
      resoudre({ epreuve, code: code === null ? 124 : code, sortie,
                 duree: (Date.now() - debut) / 1000 });
    });
  });
}

/** Les epreuves en parallele, imprimees dans l'ordre du manifeste. */
async function toutes(liste, largeur = 4) {
  const resultats = new Array(liste.length);
  let suivante = 0;
  const ouvrier = async () => {
    while (suivante < liste.length) {
      const i = suivante++;
      resultats[i] = await lancer(liste[i]);
    }
  };
  await Promise.all(Array.from({ length: Math.min(largeur, liste.length) }, ouvrier));
  return resultats;
}

// `console.log("%-22s")` n'existe pas en Node : son format ne connait ni largeur
// ni precision, et il imprime la chaine telle quelle sans rien dire. On cale les
// colonnes a la main.
const cale = (s, n) => (String(s).length >= n ? String(s)
  : String(s) + " ".repeat(n - String(s).length));
const droite = (s, n) => (String(s).length >= n ? String(s)
  : " ".repeat(n - String(s).length) + String(s));

/** Ce que l'epreuve a CONCLU, en une ligne — pas sa derniere mesure imprimee. */
function verdictCourt(r) {
  // Une epreuve dont la sortie est faite pour une machine (du JSON) porte son
  // propre resume ; s'il echoue, on retombe sur la lecture generique.
  if (r.epreuve.resume) {
    try { return r.epreuve.resume(r.sortie).slice(0, 74); } catch { /* generique */ }
  }
  const lignes = r.sortie.split("\n").map((l) => l.trimEnd()).filter((l) => l.trim());
  // QUAND C'EST ROUGE, ON MONTRE L'ECART, PAS L'EXPLICATION. Les bancs de cette
  // maison finissent par un paragraphe qui dit quoi faire ; c'est utile a lire,
  // c'est inutile en resume. La premiere ligne de refus est ce qu'on veut voir
  // sur la ligne de tableau — le detail suit juste en dessous, de toute facon.
  if (r.code !== 0) {
    const refus = lignes.find((l) => /^\s*(NON|✗|ECHEC|FAIL|Error)\b/i.test(l));
    if (refus) return refus.trim().slice(0, 74);
  }
  // Sinon : la conclusion, cherchee par sa forme, et la derniere ligne a defaut.
  const conclusion = [...lignes].reverse().find((l) =>
    /(toutes? les|epreuve\(s\)|sonde\(s\)|tenue|rouge|✓|✗|^\s*OK\s*$|: OK|fichier\(s\)|ecart)/i
      .test(l));
  return ((conclusion || lignes[lignes.length - 1] || "").trim()).slice(0, 74);
}

function compteDe(r) {
  if (!r.epreuve.compte) return null;
  const m = r.sortie.match(r.epreuve.compte);
  return m ? m[1] : null;
}

async function main() {
  const liste = choisies();
  if (!liste.length) {
    console.log("Aucune epreuve ne matche --seul " + SEUL);
    return 2;
  }
  const gardes = liste.filter((e) => e.rang === "garde");
  const mesures = liste.filter((e) => e.rang === "mesure");

  console.log("VERIFIER — " + gardes.length + " garde(s), " + mesures.length
    + " mesure(s)" + (LONG ? ", --long" : "")
    + (SEUL ? ", --seul " + SEUL : ""));
  console.log("");

  const debut = Date.now();

  // DEUX PHASES, ET LA SECONDE EST SEULE. Une epreuve marquee `long` mange sept
  // minutes de processeur : la faire tourner en concurrence avec les quatorze
  // autres ne l'accelere pas, ca ralentit tout le monde — mesure faite, le
  // passage entier depassait le quart d'heure au lieu des sept minutes de la
  // seule coupable. Elle passe donc APRES, seule, et le tableau des gardes
  // s'imprime des qu'il est pret : on ne fait pas attendre sept minutes un
  // verdict qui est tombe au bout d'une.
  const court = liste.filter((e) => !e.long);
  const longues = liste.filter((e) => e.long);
  const resultats = await toutes(court);

  let rouges = 0;
  const promouvoir = [];

  if (gardes.length) console.log("  LES GARDES — un rouge barre la route");
  for (const r of resultats.filter((x) => x.epreuve.rang === "garde")) {
    const ok = r.code === 0;
    if (!ok) rouges++;
    console.log("  " + (ok ? "ok " : "NON") + "  " + cale(r.epreuve.id, 22)
      + " " + droite(r.duree.toFixed(1), 5) + "s  " + verdictCourt(r));
  }

  if (mesures.length) {
    console.log("");
    console.log("  LES MESURES — elles disent un chiffre, elles ne barrent rien");
    for (const r of resultats.filter((x) => x.epreuve.rang === "mesure")) {
      const n = compteDe(r);
      if (r.code === 0) promouvoir.push(r.epreuve.id);
      console.log("  " + (r.code === 0 ? "VERT" : "  · ") + " " + cale(r.epreuve.id, 22)
        + " " + droite(r.duree.toFixed(1), 5) + "s  "
        + (n !== null ? cale(n, 4) + " " : "") + verdictCourt(r));
    }
  }

  for (const e of longues) {
    console.log("");
    process.stdout.write("  ...  " + cale(e.id, 22) + " en cours, "
      + e.secondes + " s attendues — seul, pour ne pas rallonger les autres\n");
    const r = await lancer(e);
    resultats.push(r);
    if (r.code === 0) promouvoir.push(e.id);
    const n = compteDe(r);
    console.log("  " + (r.code === 0 ? "VERT" : "  · ") + " " + cale(e.id, 22)
      + " " + droite(r.duree.toFixed(1), 5) + "s  "
      + (n !== null ? cale(n, 4) + " " : "") + verdictCourt(r));
  }

  if (BAVARD || rouges) {
    for (const r of resultats) {
      if (!BAVARD && (r.epreuve.rang !== "garde" || r.code === 0)) continue;
      console.log("");
      console.log("  ---- " + r.epreuve.id + " (sortie " + r.code + ") ".padEnd(3, " "));
      const lignes = r.sortie.split("\n");
      for (const l of (BAVARD ? lignes : lignes.slice(-25))) console.log("     " + l);
    }
  }

  console.log("");
  const total = ((Date.now() - debut) / 1000).toFixed(1);
  if (promouvoir.length) {
    console.log("  Passe(s) au vert : " + promouvoir.join(", ")
      + " — monte-les en garde dans le manifeste, sinon elles cesseront "
      + "d'etre regardees.");
  }
  if (rouges) {
    console.log("  " + rouges + " garde(s) rouge(s) en " + total + " s. "
      + "Rien ne se commet sur un etalon casse.");
    return 1;
  }
  console.log("  Toutes les gardes tiennent (" + total + " s).");
  return 0;
}

// ON NE SORT PAS DE FORCE. `process.exit()` coupe la sortie encore en tampon des
// que stdout n'est pas un terminal — une redirection vers un fichier, un pipe
// vers `grep`, une CI. Le symptome est traitre : la commande rend le bon code,
// et le tableau qui l'explique a disparu. On pose le code et l'on laisse Node
// vider ses tampons avant de partir.
main().then((c) => { process.exitCode = c; }).catch((e) => {
  console.error("verifier : " + ((e && e.stack) || e));
  process.exitCode = 2;
});
