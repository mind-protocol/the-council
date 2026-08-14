// books.js — « Les livres », une échelle du décor.
// Un book est un OBJET posé dans une salle : un registre sur la Table Peinte,
// un livre de comptes à l'intendance, un rôle d'équipage au quai. Il porte du
// JSON — un tableau à colonnes, des pages de texte — et il ne se consulte que
// là où il se trouve : on ne lit pas depuis l'autre bout du château un registre
// qui est resté sur la table.
//
// Un livre peut aussi n'être posé nulle part : il est SUR QUELQU'UN. C'est le
// carnet de voyage — il suit son porteur de château en château, et on ne peut
// l'ouvrir que là où l'homme se trouve. Un carnet qu'on lit alors que son
// porteur est à trois jours de route serait une fuite, pas une commodité.
//
// Format (etat/books.json, un tableau) :
//   id                      — l'objet
//   lieu_id, salle_id       — où il est POSÉ (un registre sur une table)
//   acteur_id               — ou sur QUI il est porté (un carnet de voyage) ;
//                             l'un ou l'autre, jamais les deux
//   boite                   — ou le COFFRET où il est rangé (etat/boites.json).
//                             Une boîte est un objet du monde comme lui : elle
//                             est posée ou portée, et elle donne sa place à
//                             tout ce qu'elle contient. Un volume rangé n'a
//                             donc ni salle, ni porteur, ni `prive` à lui — le
//                             serveur les lui recopie de la boîte avant de
//                             servir l'étagère
//   prive: true             — un carnet que son porteur ne montre pas : seul
//                             le joueur qui le porte le voit. Sans `acteur_id`
//                             il ne veut rien dire — un volume posé n'a pas de
//                             porteur : c'est `lecteurs` qu'il lui faut
//   lecteurs: [ "…", … ]    — les seuls qui puissent l'ouvrir. Ça ne DONNE
//                             rien : le volume garde ses règles de lieu, mais
//                             qui n'y est pas nommé ne le voit pas — le
//                             registre où vivent les noms, posé sur la table
//                             d'une salle où deux sièges entrent
//   titre, sous_titre       — ce qu'on lit sur la couverture
//   type                    — le genre du volume (registre, carnet, plan,
//                             memento, dossier, regle, oeuvre) : il donne son
//                             mot sur l'onglet et sa teinte de tranche
//   couleur                 — pour forcer la teinte contre celle du type ;
//                             sans lui, elle est préremplie par le type
//   colonnes: [ "…", … ]    — l'en-tête du tableau (optionnel)
//   lignes: [ { cellules: [ … ], note: "…" }, … ]  (une ligne peut aussi être
//                             un simple tableau de cellules)
//   pages: [ "…", … ]       — du texte suivi, quand il n'y a pas de tableau
//
// Un dernier volume ferme l'étagère et n'est PAS dans `books.json` : les notes
// du joueur. Hors fiction, toujours à portée, gardées telles quelles par le
// serveur (`/notes`, un fichier de texte par siège). Rien de ce qui s'y écrit
// n'entre dans la partie.
"use strict";
window.Books = (() => {
  let books = null;
  let charge = false;
  let salleVue = undefined;   // la salle du dernier tracé
  let chateauVu = undefined;  // le château du dernier CHARGEMENT
  let portantsVus = "";       // qui portait un carnet au dernier tracé
  let ferme = false;          // le serveur a refusé l'étagère : pas de siège
  let ouvert = null;          // le volume qu'on a sous les yeux
  let ouverteBoite = null;    // le coffret ouvert, si c'en est un
  let perime = false;         // on a déjà redemandé l'étagère une fois
  // Les coffrets à portée (etat/boites.json), tels que le serveur les sert.
  // Une boîte donne sa PLACE à ce qu'elle contient : le serveur a déjà recopié
  // sa salle, son porteur et son `prive` sur chacun de ses volumes, et l'on n'a
  // plus ici qu'à les regrouper sous un onglet.
  let boites = [];

  // Les genres de volume. Le `type` d'un livre est facultatif ; quand il y en
  // a un, il prérremplit la teinte de la tranche — on reconnaît un carnet d'un
  // registre au coin de l'œil, sans lire l'onglet. Une clé `couleur` sur le
  // livre passe devant, pour le volume qui ne ressemble à aucun autre.
  const TYPES = {
    registre: { nom: "Registre", teinte: "var(--book-registre)" },
    carnet:   { nom: "Carnet",   teinte: "var(--book-carnet)" },
    plan:     { nom: "Plan",     teinte: "var(--book-plan)" },
    memento:  { nom: "Mémento",  teinte: "var(--book-memento)" },
    dossier:  { nom: "Dossier",  teinte: "var(--book-dossier)" },
    regle:    { nom: "Règle",    teinte: "var(--book-regle)" },
    oeuvre:   { nom: "Œuvre",    teinte: "var(--book-oeuvre)" },
  };
  const genre = (b) => TYPES[String(b.type || "").toLowerCase()] || null;
  const teinte = (b) => b.couleur || (genre(b) || {}).teinte || "var(--braise)";

  // ---- Les marques — ce qu'on lit d'un volume SANS l'ouvrir ---------------
  // Trente-sept affaires dont chaque ligne portait le même mot (« Plan ») et le
  // même début de sous-titre (« Affaire ouverte à la Table Peinte le 26e jour
  // de la 3e lune… ») : une colonne qui dit la même chose sur toutes les lignes
  // n'aide personne à choisir. Ce qui distingue une affaire d'une autre est
  // DÉJÀ écrit dedans — le pilier qu'elle sert, et l'état de ses actions. On ne
  // l'écrit donc nulle part : on le remonte.
  //
  // Deux marques, pas plus. Le PILIER dit à quoi ça sert (quatre valeurs, plus
  // les garants qui les servent tous) et porte la couleur ; l'AVANCEMENT dit où
  // ça en est, et c'est le seul chiffre qui bouge tout seul. Une troisième
  // marque ne paraît que quand elle alarme : ce qui est bloqué, ce qui n'est pas
  // écrit. Le reste est dans le volume, à un clic.
  const PILIERS = [
    { id: "attaque",  cherche: "etre pas attaque",     nom: "n'être pas attaqué" },
    { id: "ville",    cherche: "preparer la ville",    nom: "préparer la ville" },
    { id: "rallier",  cherche: "rallier la population", nom: "rallier la population" },
    { id: "portes",   cherche: "ouvrir les portes",    nom: "ouvrir les portes" },
    { id: "garant",   cherche: "garant des trois",     nom: "les trois piliers" },
  ];
  const sansAccent = (s) => String(s == null ? "" : s)
    .normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  // Le pilier tel que l'ouverture du volume le dit, dans les mots de la maison.
  // Un volume qui ne sait pas le dire n'en reçoit pas : « un volume qui ne sait
  // dire ni l'un ni l'autre n'a rien à faire dans le coffret », et l'absence de
  // marque est alors l'information.
  function pilierDe(b) {
    let dit = "";
    (b.tables || []).forEach((t) => {
      (t.lignes || []).forEach((l) => {
        const c = l.cellules || [];
        if (c.length > 1 && sansAccent(c[0]).indexOf("pilier") >= 0 && !dit) dit = c[1];
      });
    });
    if (!dit) return null;
    // Le pilier est le PREMIER nommé dans la phrase, pas le premier de notre
    // liste : « Pilier : rallier la population, sans quoi on est attaqué dans
    // les rues » sert le ralliement. Un volume nomme volontiers les autres pour
    // dire ce qu'il n'est pas.
    const n = sansAccent(dit);
    let trouve = null, ou = Infinity;
    PILIERS.forEach((p) => {
      const i = n.indexOf(p.cherche);
      if (i >= 0 && i < ou) { ou = i; trouve = p; }
    });
    return trouve;
  }

  // L'état des actions du volume : sa table ⚔️ porte une colonne à vocabulaire
  // fermé — à faire · en cours · faite · bloquée. On compte, on ne juge pas.
  function actionsDe(b) {
    const n = { total: 0, faites: 0, cours: 0, bloquees: 0 };
    (b.tables || []).forEach((t) => {
      if (String(t.titre || "").indexOf("⚔") < 0) return;
      const cols = t.colonnes || [];
      let i = cols.findIndex((c) => {
        const s = sansAccent(c);
        return s.indexOf("etat") >= 0 || s.indexOf("en est") >= 0;
      });
      if (i < 0) i = cols.length - 1;
      (t.lignes || []).forEach((l) => {
        const c = l.cellules || [];
        if (!c.length) return;
        n.total++;
        const e = sansAccent(c[i] || "").replace(/\*/g, "");
        if (e.indexOf("bloqu") >= 0) n.bloquees++;
        else if (e.indexOf("en cours") >= 0) n.cours++;
        else if (e.indexOf("fait") >= 0) n.faites++;
      });
    });
    return n;
  }

  // Le filtre courant : cliquer un pilier ne fait qu'une chose — ne garder que
  // celui-là. C'est ce qui sépare une marque d'une étiquette ; une couleur qu'on
  // ne peut pas empoigner ne sert qu'à décorer.
  let pilierTenu = null;

  // ---- LES IDÉES : la mission de tête d'une affaire, sous son volume --------
  // Le coffret « Les sujets » aligne trente-huit affaires ; l'échiquier sait,
  // pour chacune, ce qu'il y aurait à faire — et ce savoir restait sur l'autre
  // échelle, où l'on ne va pas quand on cherche un cahier. L'interrupteur le
  // fait descendre ici, une ligne par affaire, en retrait.
  //
  // ON NE RECALCULE RIEN. La route `/echiquier` dérive déjà les missions et
  // range dans chaque affaire son `idee` — l'acte de tête, classé par la force
  // de son effet, sa portée, puis son coût. On rapproche par `livre_id`, qui
  // est l'appariement affaire↔volume que le serveur a déjà fait, et par rien
  // d'autre : un volume que ce rapprochement ne trouve pas n'affiche rien, et
  // son silence est l'information — c'est une affaire ouverte qui n'a encore
  // aucune ligne aux registres du plan.
  const MEMOIRE_IDEES = "conseil-books-idees";
  let idees = false;          // l'interrupteur
  let parPoids = false;       // le coffret des affaires, rangé par criticité
  const MEMOIRE_POIDS = "book-affaires-par-poids";
  try { parPoids = localStorage.getItem(MEMOIRE_POIDS) === "1"; } catch (e) {}

  // Ce qu'un cahier pèse, et de combien ça a bougé depuis hier. Sert la liste
  // d'affaires ; `null` tant que le calcul n'est pas rentré, et la colonne
  // n'existe alors pas du tout — une colonne de tirets n'apprend rien.
  function poidsDe(b) {
    if (!crit || !crit.affaires) return null;
    const t = String(b.titre == null ? "" : b.titre).replace(/\*\*/g, "").trim();
    return crit.affaires[t] || null;
  }
  let ideesChargees = false;  // on n'a demandé la route qu'une fois
  let parLivre = {};          // livre_id -> { m: la mission, titre: l'affaire }
  try { idees = localStorage.getItem(MEMOIRE_IDEES) === "1"; } catch (e) {}

  // ─────────────────────────────────────────── la criticité, par-dessus
  //
  // TROIS COLONNES QUI NE SONT PAS DANS LE VOLUME, et qui ne doivent pas y être.
  // `couverture.py` régénère les registres à quatre colonnes pour qu'ils ne
  // portent rien de volatil ; un score bouge à chaque action cochée. Il se
  // calcule donc à la demande (`/criticite`) et l'écran l'AJOUTE au tableau, par
  // numéro. Le volume qu'on copie, qu'on imprime, qu'on emporte, reste celui
  // qui est écrit — c'est la lecture qui est augmentée, pas le livre.
  //
  //   perte    ce que le plan perd si ce pas rate — zéro = quelqu'un d'autre peut
  //   portée   la masse d'états cibles servie en aval
  //   attendu  ce qui, dans un AUTRE cahier, se casse la figure sans ce pas
  //
  // On ne les pose que sur les tableaux D'ADRESSE (première colonne « N° ») et
  // seulement si la ligne a un score : une colonne de tirets sur trente lignes
  // n'apprend rien et double la largeur.
  let crit = null;
  let critDemande = false;
  const COLS_CRIT = ["📉 Perte", "📡 Portée", "⏳ Attendu"];
  const COLS_BUT = ["⚖️ Poids", "🎯 Atteint ?"];
  // CES COLONNES NE SONT PAS DANS LE VOLUME, donc personne ne peut deviner ce
  // qu'elles veulent dire en lisant autour. L'aide se pose sur l'en-tête, là où
  // le doigt est déjà quand la question se pose — trente lignes plus bas, une
  // note en tête de page n'est plus lue.
  const AIDE = {
    "📉 Perte": "Combien d'états cibles deviennent inatteignables sans cette pièce."
      + " On la retire, on recalcule, on fait la différence. Pour une action ou une"
      + " clef : si ce pas rate. Pour un VERROU : tant qu'il tient, c'est-à-dire ce"
      + " que cet empêchement coûte au plan. Zéro ne veut pas dire sans importance :"
      + " il veut dire qu'un autre chemin existe."
      + " 🔁 = pris dans un cercle de dépendances, rien ne part.",
    "📡 Portée": "Les états cibles atteignables servis en aval, doublures comprises."
      + " L'écart avec la perte est la redondance : portée haute et perte nulle,"
      + " quelqu'un d'autre peut le faire ; portée nulle, ce pas ne mène nulle part.",
    "⏳ Attendu": "Ce qui, dans un AUTRE cahier, se casse la figure sans ce pas."
      + " Un homme à prévenir, pas un travail à sécuriser.",
    "⚖️ Poids": "Ce que vaut cet état cible. Le seul nombre saisi à la main de tout"
      + " le calcul (etat/poids-etats.json) ; sans le fichier, tout vaut 1.",
    "🎯 Atteint ?": "✅ une chaîne écrite mène jusqu'à lui. 🚫 aucune — le plan le"
      + " poursuit sans avoir écrit par où.",
  };
  const HORS = " — calculé à l'ouverture, pas écrit au registre.";
  function chargerCriticite() {
    if (critDemande) return;
    critDemande = true;
    fetch("/criticite").then((r) => r.json()).then((d) => {
      crit = (d && d.pas) ? d : null;
      if (crit) dessiner();
    }).catch(() => { critDemande = false; });
  }

  // ─────────────────────────────────────────── « Les pas », volume calculé
  //
  // UN ONGLET, PAS UNE PAGE À PART. La page `/pas` existe et sert la régie ;
  // mais la question qu'elle pose — par quoi commencer — se pose LE NEZ DANS
  // LES REGISTRES, pas dans un autre écran qu'il faut penser à ouvrir. Un lien
  // qu'on ne voit pas depuis l'endroit où l'on travaille n'est pas un lien.
  //
  // C'EST UN VOLUME SYNTHÉTIQUE, comme « Vos notes » : il n'est écrit par
  // personne dans la fiction, son emblème le dit, et il ne se range dans aucun
  // coffret. Le reste vient gratuitement — les onglets, le tri des colonnes, la
  // teinte des chiffres, les renvois cliquables vers la pièce citée : ce sont
  // les mêmes tables que partout, et l'on n'a pas eu à réécrire une grille.
  //
  // IL SE REFAIT À CHAQUE DESSIN, ET C'EST VOULU : il n'a pas d'existence sur
  // disque, donc rien à périmer. Sans criticité chargée, il n'existe pas du
  // tout — mieux vaut pas d'onglet qu'un onglet vide.
  const PAS = "les-pas";
  // LE CALCUL VOIT TOUT LE PLAN ; CE VOLUME NE DOIT MONTRER QUE CE QUE CE SIÈGE
  // PEUT OUVRIR. `/criticite` est une route de machine : elle ne connaît ni
  // siège, ni salle, ni `lecteurs`, et rend les quarante-deux affaires du
  // dépôt — les cahiers `nera-*` de Marlo compris. Poussé tel quel sur
  // l'étagère, ce volume les servait à Rhaenyra, qui n'en tient qu'une.
  //
  // On le borne donc sur L'ÉTAGÈRE ELLE-MÊME : le serveur a déjà fait le tri du
  // brouillard pour `books`, et un cahier qu'on ne peut pas ouvrir n'a pas à
  // livrer ses chiffres. C'est la même règle qu'ailleurs, appliquée une fois de
  // plus — pas une règle de plus.
  function affairesVues() {
    const vues = new Set();
    (books || []).forEach((b) => {
      if (!permis(b) || !(poseIci(b) || porteIci(b))) return;
      const t = String(b.titre == null ? "" : b.titre).replace(/\*\*/g, "").trim();
      if (t) vues.add(t);
      // Un registre par type ne PORTE pas une affaire, il la CITE : ses lignes
      // nomment des cahiers qu'on a le droit de lire d'ici, sinon il ne serait
      // pas sur l'étagère. On prend donc aussi ce qu'il nomme.
      tableauxDe(b).forEach((sec) => {
        const i = (sec.colonnes || []).findIndex((c) => /Affaire/i.test(String(c)));
        if (i < 0) return;
        (sec.lignes || []).forEach((l) => {
          const c = (l.cellules || [])[i];
          const v = String(c == null ? "" : c).replace(/\*\*/g, "").trim();
          if (v) vues.add(v);
        });
      });
    });
    return vues;
  }

  function volumePas() {
    if (!crit || !crit.pas) return null;
    const vues = affairesVues();
    const ici = (a) => !a || vues.has(a);
    const par = (a, b) => (b.perte + b.attendu) - (a.perte + a.attendu);
    const gs = { etat: "🎯", verrou: "🔒", clef: "🗝️", action: "⚔️" };
    const lignes = Object.keys(crit.pas).map((n) => Object.assign({ n }, crit.pas[n]))
      .filter((p) => (p.perte > 0 || p.attendu > 0 || p.cercle != null) && ici(p.affaire))
      .sort(par)
      .map((p) => ({ cellules: [
        (gs[p.genre] || "") + " " + p.n, p.nom, p.affaire, p.etat || "—",
        p.cercle != null ? "🔁" : String(p.perte || "—"),
        String(p.portee || "—"), String(p.attendu || "—")] }));
    const idees = (crit.idees || []).filter((i) => i.score > 0 && ici(i.affaire)).map((i) => ({
      cellules: [String(i.score), i.piece ? ((gs[i.genre] || "") + " " + i.piece) : "—",
        i.texte, i.affaire] }));
    const cercles = (crit.cercles || [])
      .filter((g) => g.pieces.some((m) => ici(m.affaire)))
      .map((g) => ({ cellules: [
      String(g.taille),
      g.pieces.map((m) => (gs[m.genre] || "") + " " + m.n).join(" → "),
      g.pieces.map((m) => m.nom).join(" · ")] }));
    const buts = Object.keys(crit.etats || {}).map((n) => Object.assign({ n }, crit.etats[n]))
      .filter((e) => ici(e.affaire))
      .sort((a, b) => (a.atteignable - b.atteignable) || a.n.localeCompare(b.n))
      .map((e) => ({ cellules: ["🎯 " + e.n, e.nom, e.affaire,
        String(e.poids), e.atteignable ? "✅" : "🚫"] }));
    const tables = [];
    if (idees.length) tables.push({
      titre: "💡 CE QU'IL FAUDRAIT ÉCRIRE — rangé par ce que ça ouvrirait",
      colonnes: ["⚖️ Ouvre", "🔢 La pièce", "💡 L'idée", "🏰 Affaire"], lignes: idees });
    if (lignes.length) tables.push({
      titre: "🔺 LES GOULOTS — ce que le plan perd si ce pas rate",
      colonnes: ["🔢 N°", "🏷️ Le pas", "🏰 Affaire", "⏳ Où ça en est",
                 "📉 Perte", "📡 Portée", "⏳ Attendu"], lignes: lignes });
    if (cercles.length) tables.push({
      titre: "🔁 LES CERCLES — des chaînes qui se mordent la queue",
      colonnes: ["🔢 Pièces", "⛓️ La chaîne", "🏷️ Ce qu'elles disent"], lignes: cercles });
    if (buts.length) tables.push({
      titre: "🎯 LES ÉTATS CIBLES — poids, et atteignables ou non",
      colonnes: ["🎯 N°", "🏷️ L'état", "🏰 Affaire", "⚖️ Poids", "🎯 Atteint ?"],
      lignes: buts });
    if (!tables.length) return null;
    return { id: PAS, calcule: true, titre: "Les pas", embleme: "⚖️",
             couleur: "var(--book-carnet)",
             sous_titre: "Calculé à l'ouverture, écrit nulle part — "
               + lignes.length + " pas, "
               + idees.length + " idées, "
               + cercles.length + " cercle" + (cercles.length > 1 ? "s" : ""),
             tables: tables };
  }

  function chargerIdees() {
    if (ideesChargees) return;
    ideesChargees = true;
    fetch("/echiquier").then((r) => r.json()).then((d) => {
      const cat = (d && d.missions) || {};
      parLivre = {};
      ((d && d.affaires) || []).forEach((a) => {
        if (a.livre_id && a.idee && cat[a.idee]) {
          parLivre[a.livre_id] = { m: cat[a.idee], titre: a.titre };
        }
      });
      if (idees) dessiner();
    }).catch(() => { ideesChargees = false; });
  }

  // La phrase, dans le gabarit de l'échiquier — afin d'atteindre X, faire Y
  // aurait effet Z — composée par la même main que la bulle du plateau, pour
  // que les deux ne disent jamais deux choses de la même affaire.
  function traitIdee(m) {
    const d = document.createElement("div");
    d.className = "book-idee book-idee-" + (m.sur === "reine" ? "reine" : "conseil");
    const lampe = document.createElement("span");
    lampe.className = "book-idee-lampe";
    lampe.textContent = "\u{1F4A1}";
    d.appendChild(lampe);
    const mot = (t) => d.appendChild(document.createTextNode(t));
    // Les signes du guide « Comment on ouvre une affaire », les mêmes que sur
    // le plateau : c'est à ça qu'on reconnaît que c'est la même chose.
    const SIGNES = { etat: "\u{1F3AF}", verrou: "\u{1F512}",
      clef: "\u{1F5DD}️", action: "⚔️" };
    const piece = (q) => {
      if (!q) return;
      const s = document.createElement("span");
      s.className = "book-idee-cite";
      if (SIGNES[q.genre]) {
        const i = document.createElement("span");
        i.className = "book-idee-signe";
        i.textContent = SIGNES[q.genre];
        s.appendChild(i);
      }
      const t = document.createElement("i");
      t.textContent = q.nom;
      s.appendChild(t);
      d.appendChild(s);
    };
    if (m.but && !(m.piece && m.but.numero === m.piece.numero)) {
      mot("Afin d'atteindre ");
      piece(m.but);
      if (m.buts_autres) {
        mot(m.buts_autres > 1 ? " (et " + m.buts_autres + " autres états cibles)"
          : " (et un autre état cible)");
      }
      mot(", ");
    }
    mot(m.verbe + " ");
    piece(m.piece);
    if (m.effet) { mot(" " + m.effet); if (m.vers) { mot(" "); piece(m.vers); } }
    if (m.precision) mot(" — " + m.precision);
    mot(".");
    return d;
  }

  // ---- Les notes : le carnet du JOUEUR, hors du monde ---------------------
  // Un volume de plus sur l'étagère, et le seul qui ne soit pas un objet de la
  // fiction : personne ne l'écrit dans la salle, aucun PNJ ne le lit, le MJ
  // n'y touche pas. Le joueur y met ce qu'il veut, tel quel, et ça reste. Il
  // est toujours à portée — on ne pose pas ses propres notes sur une table, et
  // l'on n'a pas à traverser le château pour noter un nom.
  const NOTES = "vos-notes";
  // Son emblème est une main, et pas une plume : ce volume-ci n'est écrit par
  // personne dans la fiction. C'est le seul de l'étagère dont le signe dise
  // « hors du monde ».
  const NOTE = { id: NOTES, notes: true, titre: "Vos notes", embleme: "✋",
                 couleur: "var(--book-carnet)" };
  let notes = "";          // ce qu'il y a dans la zone, à la frappe près
  let notesEcrit = null;   // ce que le serveur a effectivement gardé
  let notesMinuteur = null;
  let notesEtat = "";      // la mention sous la zone : « Gardé. »

  function direEtat(m) {
    notesEtat = m;
    const el = document.getElementById("book-notes-etat");
    if (el) el.textContent = m;
  }

  function enregistrer() {
    clearTimeout(notesMinuteur);
    if (notesEcrit === null || notes === notesEcrit) return;
    const envoi = notes;
    fetch("/notes", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texte: envoi }),
    }).then((r) => {
      if (!r.ok) throw new Error("refus");
      notesEcrit = envoi;
      if (notes === envoi) direEtat("Gardé.");
    }).catch(() => direEtat("Pas gardé — le serveur n'a pas répondu."));
  }

  // On n'écrit pas à chaque touche : on attend que la main s'arrête.
  function planifier() {
    direEtat("…");
    clearTimeout(notesMinuteur);
    notesMinuteur = setTimeout(enregistrer, 700);
  }

  function chargerNotes() {
    fetch("/notes").then((r) => r.json()).then((d) => {
      // Une relecture ne doit pas manger une phrase en train d'être tapée :
      // ce qui n'est pas encore parti au serveur reste ce qui fait foi.
      if (notesEcrit !== null && notes !== notesEcrit) return;
      notes = (d && typeof d.texte === "string") ? d.texte : "";
      notesEcrit = notes;
      const z = document.getElementById("book-notes-zone");
      if (z && z !== document.activeElement) z.value = notes;
    }).catch(() => { if (notesEcrit === null) notesEcrit = ""; });
  }

  function carteNotes() {
    const art = document.createElement("article");
    art.className = "book book-notes";
    art.style.setProperty("--book-teinte", teinte(NOTE));

    const t = document.createElement("h3");
    t.textContent = NOTE.titre;
    const et = document.createElement("span");
    et.className = "book-genre";
    et.textContent = "De votre main";
    t.appendChild(et);
    art.appendChild(tete(NOTE, t));

    const s = document.createElement("div");
    s.className = "book-sous-titre";
    s.textContent = "Hors du monde : nul ne le lit, et rien de ce qui s'y écrit n'a lieu.";
    art.appendChild(s);

    const zone = document.createElement("textarea");
    zone.id = "book-notes-zone";
    zone.className = "book-notes-zone";
    zone.spellcheck = false;
    zone.placeholder = "Ce que vous voulez garder — un nom, un chiffre, une rancune.";
    zone.value = notes;
    zone.addEventListener("input", () => { notes = zone.value; planifier(); });
    zone.addEventListener("blur", enregistrer);
    art.appendChild(zone);

    const etat = document.createElement("div");
    etat.id = "book-notes-etat";
    etat.className = "book-notes-etat";
    etat.textContent = notesEtat;
    art.appendChild(etat);
    return art;
  }

  // ---- Copier le volume -----------------------------------------------------
  // Un registre se recopie : c'est ce qu'on fait d'un registre depuis toujours.
  // On rend le volume en texte nu — le titre, les colonnes séparées par des
  // tabulations, les pages —, tel qu'il se lit, appuis compris : ce qui est
  // collé ailleurs doit être le même objet, pas un résumé.
  function texteDe(b) {
    if (b.notes) return notes;
    const l = [];
    l.push(b.titre || "Sans titre");
    if (b.sous_titre) l.push(b.sous_titre);
    tableauxDe(b).forEach((sec) => {
      if (!sec.colonnes.length && !sec.lignes.length) return;
      l.push("");
      if (sec.titre) l.push(sec.titre);
      if (sec.colonnes.length) l.push(sec.colonnes.join("\t"));
      sec.lignes.forEach((li) => {
        l.push((li.cellules || []).map((c) => c == null ? "" : String(c)).join("\t"));
        if (li.note) l.push("\t" + li.note);
      });
    });
    (b.pages || []).forEach((p) => {
      l.push("");
      // Une figure ne se recopie pas en texte : on dit qu'elle est là, avec sa
      // légende, plutôt que de laisser un trou dans la copie.
      if (p && typeof p === "object") {
        l.push("[figure" + (p.legende ? " — " + p.legende : "") + "]");
      } else {
        l.push(p == null ? "" : String(p));
      }
    });
    return l.join("\n");
  }

  // Le presse-papier moderne demande un contexte sûr ; la partie se joue aussi
  // par un tunnel qui n'en est pas toujours un. On garde la vieille manière en
  // second, sinon le bouton ment une fois sur deux.
  function auPressePapier(texte) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // Le refus arrive aussi quand l'API existe : page pas au premier plan,
      // permission coupée. On retombe alors sur la vieille manière au lieu de
      // dire au joueur que ça n'a pas marché.
      return navigator.clipboard.writeText(texte).catch(() => vieilleManiere(texte));
    }
    return vieilleManiere(texte);
  }

  function vieilleManiere(texte) {
    return new Promise((ok, non) => {
      const z = document.createElement("textarea");
      z.value = texte;
      z.setAttribute("readonly", "");
      z.style.cssText = "position:fixed;top:-9999px;opacity:0;";
      document.body.appendChild(z);
      z.select();
      let fait = false;
      try { fait = document.execCommand("copy"); } catch (e) {}
      document.body.removeChild(z);
      fait ? ok() : non(new Error("refus"));
    });
  }

  function boutonCopier(b) {
    const bt = document.createElement("button");
    bt.className = "book-copier";
    bt.type = "button";
    bt.textContent = "Copier";
    bt.title = "Recopier ce volume";
    bt.onclick = () => {
      const texte = texteDe(b);
      auPressePapier(texte).then(() => {
        bt.textContent = "Copié";
        bt.classList.add("fait");
      }).catch(() => {
        bt.textContent = "Pas copié";
      }).then(() => {
        setTimeout(() => {
          bt.textContent = "Copier";
          bt.classList.remove("fait");
        }, 1600);
      });
    };
    return bt;
  }

  // Le titre et sa main droite : on ne pose pas un bouton dans un titre, on
  // met les deux sur la même ligne.
  function tete(b, t) {
    const d = document.createElement("div");
    d.className = "book-tete";
    d.appendChild(t);
    const plateau = boutonPlateau(b);
    if (plateau) d.appendChild(plateau);
    d.appendChild(boutonCopier(b));
    return d;
  }

  // Le cahier d'une affaire a un plateau, et le plateau a ce cahier : le
  // chemin se fait dans les deux sens. Rien pour les volumes qui n'en ont pas
  // — on ne pose pas un bouton mort.
  function boutonPlateau(b) {
    if (!b || !window.Echiquier || !Echiquier.pourLivre) return null;
    const a = Echiquier.pourLivre(b.id);
    if (!a) return null;
    const bt = document.createElement("button");
    bt.className = "book-plateau";
    bt.type = "button";
    bt.innerHTML = '<i>⚄</i><span>L\'échiquier</span>';
    bt.title = "Voir cette affaire sur l'échiquier";
    bt.onclick = () => Echiquier.montrer(a.id);
    return bt;
  }

  function hote() { return document.getElementById("books"); }
  const salleCourante = () =>
    (window.Plan && Plan.salle) ? Plan.salle() : null;
  const chateauCourant = () =>
    (window.Plan && Plan.chateau) ? Plan.chateau() : null;

  function nomSalle(id) {
    const p = (window.Plans || {})[chateauCourant()];
    const s = p && (p.salles || []).find((x) => x.id === id);
    return s ? s.nom : null;
  }

  const moi = () => (window.Moi && window.Moi.personnage_id) || null;
  const present = (id) => !!(window.Presents && window.Presents[id]);
  const nomActeur = (id) => {
    const p = (window.Presents || {})[id];
    if (p && p.nom) return p.nom;
    const f = window.Gens && Gens.qui ? Gens.qui(id) : null;
    return (f && f.nom) || String(id || "").replace(/-/g, " ");
  };

  // Un livre posé : il appartient au château, et l'on peut aller le chercher.
  // On ne l'a d'abord montré que dans SA salle — et l'on a vu ce que ça donne :
  // celle qui tient les écritures descend à la porte du Dragon, et le registre
  // des communications disparaît de son écran. Un registre de maison n'est pas
  // un secret, c'est un meuble : il reste consultable de tout le château, et
  // l'on dit simplement où il se trouve. Ce qui reste strict, c'est le carnet
  // que quelqu'un porte sur lui.
  function poseIci(b) {
    if (!b.salle_id) return false;
    const chateau = chateauCourant();
    return !b.lieu_id || !chateau || b.lieu_id === chateau;
  }

  // Est-il sous la main, ou faut-il monter le chercher ?
  const sousLaMain = (b) => !!b.salle_id && b.salle_id === salleCourante();

  // Un livre porté : il vaut ce que vaut la présence de son porteur. Le mien
  // est toujours sur moi ; celui d'un autre ne s'ouvre que s'il est dans la
  // salle, et jamais s'il le tient pour lui.
  function porteIci(b) {
    if (!b.acteur_id) return false;
    if (b.acteur_id === moi()) return true;
    if (b.prive) return false;
    return present(b.acteur_id);
  }

  // Un volume peut NOMMER ses lecteurs. C'est ce qui manquait au carnet des
  // yeux : posé sur la Table Peinte, marqué `prive`, et donc privé de personne —
  // un `prive` sans porteur n'a pas de propriétaire, et le carnet s'ouvrait à
  // quiconque entrait dans le château. `lecteurs` ne DONNE rien : il retire. Le
  // volume reste où il est, avec ses règles de salle et de château ; simplement,
  // qui n'y est pas nommé ne l'ouvre pas. Un carnet qui ne quitte pas la chambre
  // ne se lit pas non plus depuis l'autre bout du royaume parce qu'on y a son nom.
  const lecteurs = (b) => Array.isArray(b.lecteurs) && b.lecteurs.length
    ? b.lecteurs : null;
  const permis = (b) => {
    const l = lecteurs(b);
    return !l || l.indexOf(moi()) !== -1;
  };

  // Ceux qu'on peut ouvrir d'où l'on est. Les notes du joueur ferment toujours
  // la marche : elles ne sont nulle part dans le château, donc partout.
  function ici() {
    const dedans = books ? books.filter(
      (b) => permis(b) && (poseIci(b) || porteIci(b))) : [];
    const p = volumePas();
    if (p) dedans.push(p);
    dedans.push(NOTE);
    return dedans;
  }

  // Qui, dans la salle, porte quelque chose : c'est ce qui fait apparaître et
  // disparaître l'onglet quand un homme entre ou sort.
  function portants() {
    if (!books) return "";
    return books.filter(porteIci).map((b) => b.acteur_id).sort().join(",");
  }

  function lignesDe(b) {
    return (b.lignes || []).map((l) =>
      Array.isArray(l) ? { cellules: l } : (l || { cellules: [] }));
  }

  // ---- les tableaux d'un volume ---------------------------------------------
  // Un registre n'a qu'un tableau : c'est une seule sorte de chose, rangée. Une
  // AFFAIRE en a plusieurs, et pas par confort — ses états cibles, ses verrous,
  // ses clefs et ses actions n'ont pas les mêmes colonnes, et les entasser dans
  // une grille commune obligerait à inventer une colonne fourre-tout par type.
  // Donc `tables: [{titre, colonnes, lignes}]`, et le vieux couple
  // colonnes/lignes reste la forme courte du volume qui n'en a qu'un.
  function tableauxDe(b) {
    if (Array.isArray(b.tables) && b.tables.length) {
      return b.tables.map((t) => ({
        titre: t.titre || "",
        colonnes: t.colonnes || [],
        lignes: lignesDe(t),
      }));
    }
    return [{ titre: "", colonnes: b.colonnes || [], lignes: lignesDe(b) }];
  }

  // ---- Les renvois : un numéro écrit, et la ligne qui le définit ------------
  // Un cahier d'affaire ne se lit pas de haut en bas, il se lit en sautant :
  // « bloque 23100 », « dépend de 24000 », « ouvre 23010 ». Tout s'y cite par
  // son numéro, et jusqu'ici il fallait aller le chercher à la main, souvent
  // dans un autre volume. On accroche donc chaque numéro à la ligne qui le
  // porte — la donnée est déjà là, il n'y manquait que le chemin.
  //
  // L'ADRESSE d'une ligne est sa première cellule, dans un tableau dont la
  // première colonne s'appelle « N° ». Quatre à six chiffres : en deçà, un
  // numéro ne se distingue plus d'une quantité, et l'on accrocherait les douze
  // hommes de la barque. L'emoji qui précède un renvoi dit sa FAMILLE (état,
  // verrou, clef, action) — il ne sert pas à le reconnaître, le numéro suffit.
  const NUMERO = /\b\d{4,6}\b/g;
  const estAdresse = (t) => !!(t.colonnes && t.colonnes.length
    && /N°/.test(String(t.colonnes[0])));
  function numeroDe(l) {
    const c = (l.cellules || [])[0];
    const m = /^\s*(?:\*\*)?\s*(\d{4,6})\b/.exec(c == null ? "" : String(c));
    return m ? m[1] : null;
  }
  // Le millier d'un numéro : 23030 → « 23 ». C'est la série de son affaire.
  const serie = (n) => n.slice(0, -3);

  let renvois = new Map();   // un numéro → l'id du volume qui le définit
  let fiches = new Map();    // un numéro → {livre, titre, icone} pour le fil

  // L'ICÔNE d'une ligne. Elle est déjà écrite : chaque intitulé s'ouvre sur son
  // emoji (« 🪶 Se donner un exécutant »), et à défaut c'est celui du tableau
  // qui la porte (🎯 états, 🔒 verrous, 🗝️ clefs, ⚔️ actions). On ne demande
  // donc rien de neuf à personne — on ramasse ce qui est là.
  const PICTO = /^\s*(\p{Extended_Pictographic}️?)/u;
  const picto = (s) => {
    const m = PICTO.exec(s == null ? "" : String(s));
    return m ? m[1] : "";
  };
  // L'intitulé nu : sans son emoji de tête, sans ses appuis.
  const intitule = (s) => String(s == null ? "" : s)
    .replace(PICTO, "").replace(/\*\*/g, "").trim();

  // On n'indexe que ce qu'on peut OUVRIR d'où l'on est. Un renvoi vers un
  // volume hors de portée — dans un autre château, dans la poche d'un absent,
  // réservé à d'autres lecteurs — ne s'allume pas, et c'est juste : le
  // brouillard vaut ici comme ailleurs, et un numéro resté en texte nu dit
  // qu'on n'a pas ce registre-là sous la main.
  function indexer() {
    renvois = new Map();
    fiches = new Map();
    const cands = new Map();    // numéro → les volumes qui le portent
    const series = new Map();   // volume → combien de numéros par millier
    const infos = new Map();    // numéro → volume → {titre, icone}
    ici().forEach((b) => {
      if (b.notes) return;
      tableauxDe(b).forEach((t) => {
        if (!estAdresse(t)) return;
        t.lignes.forEach((l) => {
          const n = numeroDe(l);
          if (!n) return;
          if (!cands.has(n)) cands.set(n, []);
          cands.get(n).push(b.id);
          if (!infos.has(n)) infos.set(n, new Map());
          const etiquette = (l.cellules || [])[1];
          infos.get(n).set(b.id, {
            titre: intitule(etiquette),
            icone: picto(etiquette) || picto(t.titre),
          });
          if (!series.has(b.id)) series.set(b.id, new Map());
          const s = series.get(b.id);
          s.set(serie(n), (s.get(serie(n)) || 0) + 1);
        });
      });
    });
    // Deux volumes peuvent porter le même numéro : un agrégat qui recopie un
    // état cible par affaire, et l'affaire qui le tient pour de bon. Celui qui
    // tient la SÉRIE gagne — l'agrégat n'a qu'un numéro du millier, l'affaire
    // en a trente. À égalité, le premier du fichier.
    cands.forEach((livres, n) => {
      let mieux = livres[0], score = -1;
      livres.forEach((id) => {
        const c = (series.get(id) || new Map()).get(serie(n)) || 0;
        if (c > score) { score = c; mieux = id; }
      });
      renvois.set(n, mieux);
      const i = (infos.get(n) || new Map()).get(mieux) || {};
      fiches.set(n, { livre: mieux, titre: i.titre || "", icone: i.icone || "" });
    });
    // Le fil a pu poser des renvois avant que l'étagère ne soit chargée : ils
    // attendent en texte nu. Maintenant qu'on sait, on les rallume.
    if (window.Renvois && Renvois.raviver) Renvois.raviver();
  }

  // Ce qu'un numéro vaut, pour qui le cite AILLEURS que dans un livre : son
  // volume, son intitulé, sa famille. Rien si le registre n'est pas à portée —
  // et c'est ce silence qui tient le brouillard.
  function fiche(n) {
    return fiches.get(String(n)) || null;
  }

  // Accrocher, dans un morceau déjà rendu, tous les numéros qui mènent quelque
  // part. On descend jusqu'aux nœuds de texte pour ne défaire ni le gras
  // d'appui ni les entités déjà posées ; on laisse tranquille la cellule qui
  // EST l'adresse (`data-ancre`) — un numéro n'a pas à se renvoyer à lui-même —
  // et l'on n'entre pas dans un dessin, où un bouton n'aurait pas de sens.
  function renvoyer(racine) {
    if (!renvois.size) return;
    const textes = [];
    (function marche(n) {
      for (let e = n.firstChild; e; e = e.nextSibling) {
        if (e.nodeType === 3) { textes.push(e); continue; }
        if (e.nodeType !== 1) continue;
        if (String(e.tagName).toLowerCase() === "svg") continue;
        if (e.dataset && e.dataset.ancre) continue;
        if (e.classList && e.classList.contains("book-renvoi")) continue;
        marche(e);
      }
    })(racine);
    textes.forEach((t) => {
      const s = t.nodeValue;
      NUMERO.lastIndex = 0;
      let m, i = 0, frag = null;
      while ((m = NUMERO.exec(s))) {
        const livre = renvois.get(m[0]);
        if (!livre) continue;
        if (!frag) frag = document.createDocumentFragment();
        if (m.index > i) frag.appendChild(document.createTextNode(s.slice(i, m.index)));
        frag.appendChild(lien(m[0], livre));
        i = m.index + m[0].length;
      }
      if (!frag) return;
      if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
      t.parentNode.replaceChild(frag, t);
    });
  }

  function lien(n, livre) {
    const bt = document.createElement("button");
    bt.type = "button";
    bt.className = "book-renvoi";
    bt.textContent = n;
    const b = (books || []).find((x) => x && x.id === livre);
    bt.title = b && b.titre ? b.titre : livre;
    bt.onclick = (e) => { e.preventDefault(); e.stopPropagation(); aller(n); };
    return bt;
  }

  // Y aller : le volume s'ouvre s'il n'était pas celui qu'on lisait, et la
  // ligne se signale un instant — sans quoi on atterrit dans une grille de
  // quarante lignes sans savoir laquelle on était venu chercher.
  function aller(n) {
    const livre = renvois.get(String(n));
    if (!livre) return false;
    if (livre !== ouvert && !ouvrir(livre)) return false;
    viser(String(n));
    return true;
  }

  // VISER SE FAIT AUSSI EN TOUTES LETTRES. Un renvoi porte un numéro, mais tout
  // ce qui s'écrit n'en a pas : une ligne de règles s'appelle « EC.4 », un
  // paragraphe n'a pas d'adresse du tout. Un lien qui ouvre le volume et laisse
  // le joueur au haut d'une grille de deux cents lignes ne l'a mené nulle part.
  // On accepte donc, pour cible, un numéro OU un bout de ce qui est écrit.
  const sansSignes = (s) => String(s == null ? "" : s)
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().replace(/\s+/g, " ").trim();

  function viser(cible) {
    const h = hote();
    if (!h || cible == null || cible === "") return false;
    const n = String(cible);
    let el = h.querySelector('tr[data-num="' + CSS.escape(n) + '"]');
    if (!el) {
      // Ce qu'on cherche en clair : d'abord les lignes de grille, puis les
      // titres de tableau et les pages. La première qui contient gagne — on ne
      // classe pas, on mène quelque part.
      const aig = sansSignes(n);
      if (!aig) return false;
      const cands = h.querySelectorAll(
        "tbody tr, .book-table-titre, .book-page, figcaption");
      for (let i = 0; i < cands.length; i++) {
        if (sansSignes(cands[i].textContent).indexOf(aig) >= 0) {
          el = cands[i];
          break;
        }
      }
    }
    if (!el) return false;
    if (el.scrollIntoView) el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.remove("book-vise");
    void el.offsetWidth;   // relancer l'animation si l'on revient sur la même
    el.classList.add("book-vise");
    setTimeout(() => el.classList.remove("book-vise"), 2600);
    return true;
  }

  // Les appuis du MJ : **ce qui pèse** se rend en gras, comme dans le fil.
  // Un registre a besoin d'appuis plus qu'un récit : c'est là que tombent les
  // états et les liens (**acquis**, **contre**, **au loin**).
  const echappe = (s) => s.replace(/[&<>]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);

  // ─────────────────────────────────────────── les chiffres, et le tri
  //
  // UN REGISTRE SE LIT AUTREMENT QU'UNE PAGE. Sur une page, un nombre est un mot
  // comme un autre ; dans une grille de trois cents lignes, c'est le seul chose
  // que l'œil cherche — un compte d'hommes, un jour, une somme, un numéro. On
  // les teinte donc, et l'on chiffre à espacement fixe pour que les colonnes
  // s'alignent d'elles-mêmes sans qu'on ait à déclarer laquelle est numérique.
  //
  // APRÈS `renvoyer`, JAMAIS AVANT : un renvoi est lui aussi un numéro, et il
  // est déjà un lien. L'envelopper d'un second signe le ferait clignoter de
  // deux façons pour dire une seule chose. On saute donc ce qui est déjà posé.
  const CHIFFRE = /\d+(?:[   ]\d{3})*(?:[.,]\d+)?/g;
  function chiffrer(racine) {
    const textes = [];
    (function marche(n) {
      for (let e = n.firstChild; e; e = e.nextSibling) {
        if (e.nodeType === 3) { textes.push(e); continue; }
        if (e.nodeType !== 1) continue;
        const nom = String(e.tagName).toLowerCase();
        if (nom === "svg" || nom === "a") continue;
        if (e.classList && (e.classList.contains("book-renvoi")
          || e.classList.contains("book-chiffre"))) continue;
        marche(e);
      }
    })(racine);
    textes.forEach((t) => {
      const s = t.nodeValue;
      if (!/\d/.test(s)) return;
      CHIFFRE.lastIndex = 0;
      let m, i = 0, frag = null;
      while ((m = CHIFFRE.exec(s))) {
        if (!frag) frag = document.createDocumentFragment();
        if (m.index > i) frag.appendChild(document.createTextNode(s.slice(i, m.index)));
        const sp = document.createElement("span");
        sp.className = "book-chiffre";
        sp.textContent = m[0];
        frag.appendChild(sp);
        i = m.index + m[0].length;
      }
      if (!frag) return;
      if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
      t.parentNode.replaceChild(frag, t);
    });
  }

  // TROIS ÉTATS, PAS DEUX — et le troisième est le plus important. L'ordre du
  // registre veut dire quelque chose : les numéros y montent par série, une
  // affaire à la suite de l'autre, et c'est ainsi que la chose a été écrite. Un
  // tri qui ne se défait pas efface cet ordre-là pour de bon aux yeux du
  // lecteur. Donc : registre → croissant → décroissant → registre.
  //
  // LE GENRE DE LA COLONNE SE MESURE, il ne se déclare pas. On regarde les
  // cellules : si tout ce qui n'est pas vide se lit comme un nombre, on compare
  // des nombres ; sinon on compare des mots, en français, l'emoji de tête et
  // les appuis retirés — sans quoi « 🪶 Se donner un exécutant » se rangerait
  // sous 🪶 et toutes les lignes d'un même signe formeraient un bloc.
  const nuTexte = (s) => String(s == null ? "" : s)
    .replace(/\*\*/g, "")
    .replace(/^\s*\p{Extended_Pictographic}️?\s*/u, "")
    .trim();
  const nombreDe = (s) => {
    const t = nuTexte(s).replace(/[   ]/g, "").replace(",", ".");
    return /^-?\d+(\.\d+)?$/.test(t) ? parseFloat(t) : null;
  };

  function trier(tab) {
    const thead = tab.tHead;
    const tbody = tab.tBodies[0];
    if (!thead || !tbody || tbody.rows.length < 3) return;
    const ordre = Array.prototype.slice.call(tbody.rows);
    ordre.forEach((tr, i) => { tr.dataset.rang = i; });
    const ths = Array.prototype.slice.call(thead.rows[0].cells);
    let colonne = -1, sens = 0;

    ths.forEach((th, i) => {
      th.dataset.triable = "1";
      // L'EXPLICATION PASSE AVANT LE MODE D'EMPLOI. `trier` s'exécute après la
      // pose des en-têtes et écrasait l'aide des colonnes calculées par
      // « Ranger sur cette colonne » — on perdait la seule phrase qui disait ce
      // que « Attendu » veut dire, pour redire ce que le curseur montre déjà.
      th.title = th.title ? (th.title + "\n\nCliquer pour ranger.")
        : "Ranger sur cette colonne";
      th.addEventListener("click", () => {
        if (colonne === i) sens = (sens + 1) % 3; else { colonne = i; sens = 1; }
        ths.forEach((x) => { delete x.dataset.tri; });
        if (sens === 0) colonne = -1; else th.dataset.tri = sens === 1 ? "haut" : "bas";

        const rangs = Array.prototype.slice.call(tbody.rows);
        if (sens === 0) {
          rangs.sort((a, b) => (+a.dataset.rang) - (+b.dataset.rang));
        } else {
          const val = (tr) => {
            const c = tr.cells[i];
            return c ? c.textContent : "";
          };
          const tout = rangs.every((tr) => {
            const t = nuTexte(val(tr));
            return !t || nombreDe(t) !== null;
          });
          rangs.sort((a, b) => {
            const x = val(a), y = val(b);
            let d;
            if (tout) {
              const nx = nombreDe(x), ny = nombreDe(y);
              // une cellule vide tombe TOUJOURS en bas, dans les deux sens :
              // « rien d'écrit » n'est pas une petite valeur, c'est un trou
              if (nx === null) return ny === null ? 0 : 1;
              if (ny === null) return -1;
              d = nx - ny;
            } else {
              d = nuTexte(x).localeCompare(nuTexte(y), "fr",
                { numeric: true, sensitivity: "base" });
            }
            return sens === 1 ? d : -d;
          });
        }
        rangs.forEach((tr) => tbody.appendChild(tr));
      });
    });
  }

  function poser(el, texte) {
    const t = texte == null ? "" : String(texte);
    el.innerHTML = echappe(t).replace(/\*\*(\S(?:[^*]*\S)?)\*\*/g,
      '<b class="appui">$1</b>');
  }

  // Une page : du texte, ou une FIGURE. Un levé au pas, un plan de salle, un
  // arbre de parenté ne se disent pas en phrases — et le volume qui les porte
  // reste un volume, posé quelque part, qu'on peut refermer et emporter.
  // Le SVG arrive inliné par le serveur (voir inlinerFigure) ; s'il manque, on
  // ne laisse pas un trou muet : un dessin qu'on ne retrouve pas est une
  // information, et le joueur a le droit de savoir que la page existe.
  function page(p) {
    if (p && typeof p === "object" && p.figure) {
      const fig = document.createElement("figure");
      fig.className = "book-figure";
      if (p.figure_svg) {
        fig.innerHTML = p.figure_svg;
      } else {
        const manque = document.createElement("p");
        manque.className = "book-page book-attente";
        manque.textContent = "La feuille manque au volume.";
        fig.appendChild(manque);
      }
      if (p.legende) {
        const l = document.createElement("figcaption");
        poser(l, p.legende);
        if (window.Entites) Entites.traiter(l);
        fig.appendChild(l);
      }
      return fig;
    }
    const par = document.createElement("p");
    par.className = "book-page";
    poser(par, p);
    if (window.Entites) Entites.traiter(par);
    return par;
  }

  function carte(b) {
    // On ne demande le calcul qu'à l'ouverture d'un volume, et une seule fois :
    // il coûte deux secondes au serveur, et la moitié des écrans du jeu n'ouvre
    // jamais un livre. C'est aussi ce qui fait apparaître l'onglet « Les pas » :
    // il n'existe qu'une fois le calcul rentré, et son arrivée redessine.
    chargerCriticite();
    const art = document.createElement("article");
    art.className = "book";
    art.style.setProperty("--book-teinte", teinte(b));

    const t = document.createElement("h3");
    if (b.embleme) {
      const e = document.createElement("span");
      e.className = "book-embleme";
      e.textContent = b.embleme;
      t.appendChild(e);
    }
    t.appendChild(document.createTextNode(b.titre || "Sans titre"));
    const g = genre(b);
    if (g) {
      const et = document.createElement("span");
      et.className = "book-genre";
      et.textContent = g.nom;
      t.appendChild(et);
    }
    art.appendChild(tete(b, t));
    if (b.sous_titre) {
      const s = document.createElement("div");
      s.className = "book-sous-titre";
      s.textContent = b.sous_titre;
      art.appendChild(s);
    }

    const tableaux = tableauxDe(b);
    let rien = 0;
    tableaux.forEach((sec) => {
      const lignes = sec.lignes;
      rien += lignes.length;
      // Un registre ouvert et encore vierge est une information : on montre ses
      // colonnes, réglées, et l'on dit qu'il attend sa première ligne.
      if (!lignes.length && !sec.colonnes.length) return;
      // Le titre d'un tableau se pose AU-DESSUS et hors de la grille : dans une
      // <caption>, il se collerait au tableau à la copie et se perdrait au
      // défilement horizontal, qui est justement le cas d'une affaire large.
      if (sec.titre) {
        const h = document.createElement("div");
        h.className = "book-table-titre";
        poser(h, sec.titre);
        art.appendChild(h);
      }
      const enveloppe = document.createElement("div");
      enveloppe.className = "book-table-enveloppe";
      const tab = document.createElement("table");
      tab.className = "book-table";
      // Une ligne qui porte un numéro devient une adresse : c'est elle qu'on
      // vise quand on clique le renvoi qui la cite, d'ici ou d'un autre volume.
      const adresse = estAdresse(sec);
      // Y a-t-il seulement un score à montrer ici ? On regarde AVANT de poser
      // les en-têtes : trois colonnes vides sur un tableau de moyens, ce serait
      // trois colonnes de largeur perdue pour dire « rien ».
      const scores = (adresse && crit && crit.pas
        && lignes.some((l) => crit.pas[numeroDe(l)])) ? crit.pas : null;
      // UN ÉTAT CIBLE N'EST PAS UN PAS : on ne le « rate » pas, on l'atteint ou
      // non. Sa colonne n'est donc pas une perte — c'est son poids, et le fait
      // qu'une chaîne mène jusqu'à lui. Vingt-six sur cent trente-neuf n'en ont
      // aucune, et c'est ce qu'un registre d'états cibles doit dire en premier.
      const buts = (!scores && adresse && crit && crit.etats
        && lignes.some((l) => crit.etats[numeroDe(l)])) ? crit.etats : null;
      const ajout = scores ? COLS_CRIT : (buts ? COLS_BUT : []);
      if (sec.colonnes.length) {
        const thead = document.createElement("thead");
        const tr = document.createElement("tr");
        sec.colonnes.concat(ajout).forEach((c) => {
          const th = document.createElement("th");
          th.textContent = c;
          if (ajout.indexOf(c) >= 0) {
            th.dataset.calcule = "1";
            th.title = (AIDE[c] || "") + HORS;
          }
          tr.appendChild(th);
        });
        thead.appendChild(tr);
        tab.appendChild(thead);
      }
      const tbody = document.createElement("tbody");
      lignes.forEach((l) => {
        const tr = document.createElement("tr");
        const num = adresse ? numeroDe(l) : null;
        if (num) tr.dataset.num = num;
        (l.cellules || []).forEach((c, i) => {
          const td = document.createElement("td");
          if (num && i === 0) td.dataset.ancre = "1";
          poser(td, c);
          // la note pend sous la dernière colonne : c'est une mention de marge
          if (l.note && i === (l.cellules.length - 1)) {
            const n = document.createElement("div");
            n.className = "book-note";
            poser(n, l.note);
            td.appendChild(n);
          }
          if (window.Entites) Entites.traiter(td);
          tr.appendChild(td);
        });
        if (scores) {
          const s = scores[num] || {};
          // UN CERCLE SE DIT AVANT UN CHIFFRE. Une pièce prise dans une chaîne
          // qui se mord la queue a une perte de zéro — non parce qu'elle est
          // substituable, mais parce que rien derrière elle n'est atteignable.
          // Afficher « 0 » là serait le contraire de la vérité.
          [s.perte, s.portee, s.attendu].forEach((v, k) => {
            const td = document.createElement("td");
            td.className = "book-calcule";
            if (s.cercle != null && k === 0) {
              td.textContent = "🔁";
              td.title = "Prise dans un cercle de dépendances : rien ne part.";
            } else {
              td.textContent = v ? String(v) : "—";
            }
            if (k === 0 && v) td.dataset.poids = v >= 10 ? "fort"
              : (v >= 3 ? "moyen" : "faible");
            tr.appendChild(td);
          });
        }
        if (buts) {
          const e = buts[num] || {};
          const tp = document.createElement("td");
          tp.className = "book-calcule";
          tp.textContent = e.poids != null ? String(e.poids) : "—";
          const ta = document.createElement("td");
          ta.className = "book-calcule";
          ta.textContent = e.poids == null ? "—" : (e.atteignable ? "✅" : "🚫");
          if (e.poids != null && !e.atteignable) {
            ta.title = "Aucune chaîne écrite ne mène jusqu'à cet état.";
            ta.dataset.poids = "fort";
          }
          tr.appendChild(tp);
          tr.appendChild(ta);
        }
        tbody.appendChild(tr);
      });
      tab.appendChild(tbody);
      trier(tab);
      enveloppe.appendChild(tab);
      art.appendChild(enveloppe);
    });

    (b.pages || []).forEach((p) => art.appendChild(page(p)));

    if (!rien && !(b.pages || []).length) {
      const vide = document.createElement("p");
      vide.className = "book-page book-attente";
      vide.textContent = "Rien n'y est encore écrit.";
      art.appendChild(vide);
    }

    // En dernier, sur le volume entier : les cellules, les notes de marge, les
    // titres de tableau et les pages suivies citent tous des numéros.
    renvoyer(art);
    // Les chiffres en dernier, et seulement dans les grilles : dans une page
    // suivie, un nombre est un mot de la phrase, et le teinter la trouerait.
    art.querySelectorAll(".book-table td").forEach(chiffrer);

    return art;
  }

  const compte = (n) => n + (n > 1 ? " volumes" : " volume");

  // Le coffret d'un volume, s'il est rangé quelque part.
  const coffret = (b) =>
    (b && b.boite && boites.find((c) => c.id === b.boite)) || null;

  // La carte d'un coffret : ce qu'il y a dedans, ligne à ligne. C'est ce qu'on
  // voit quand on l'ouvre — on ne se met pas à lire un volume au hasard, on
  // regarde ce que la boîte contient et l'on prend celui qu'on veut. Chaque
  // ligne s'ouvre d'un clic.
  function carteBoite(e) {
    const c = e.boite;
    const art = document.createElement("article");
    art.className = "book book-coffret-carte";
    art.style.setProperty("--book-teinte", teinte(c));

    const ligneTitre = document.createElement("div");
    ligneTitre.className = "book-tete";
    const t = document.createElement("h3");
    if (c.embleme) {
      const em = document.createElement("span");
      em.className = "book-embleme";
      em.textContent = c.embleme;
      t.appendChild(em);
    }
    t.appendChild(document.createTextNode(c.titre || "Sans titre"));
    const g = document.createElement("span");
    g.className = "book-genre";
    g.textContent = "Coffret";
    t.appendChild(g);
    ligneTitre.appendChild(t);
    art.appendChild(ligneTitre);

    // Un pilier tenu : le coffret ne montre plus que lui. Les mains restent —
    // on veut voir QUI porte cette part du plan, c'est même toute la raison de
    // serrer. Un pilier qui ne garde rien se relâche de lui-même, plutôt que de
    // laisser une carte vide sans dire pourquoi.
    let livres = e.livres;
    let tenu = null;
    if (pilierTenu) {
      const gardes = livres.filter((b) => (pilierDe(b) || {}).id === pilierTenu);
      if (gardes.length) {
        livres = gardes;
        tenu = PILIERS.find((p) => p.id === pilierTenu);
      } else pilierTenu = null;
    }

    const s = document.createElement("div");
    s.className = "book-sous-titre";
    s.textContent = (c.sous_titre ? c.sous_titre + " " : "")
      + "— " + provenance(c) + ", " + livres.length
      + (livres.length > 1 ? " volumes" : " volume")
      + (tenu ? " sur " + e.livres.length + ", pour " + tenu.nom + "." : ".");
    if (tenu) {
      const revoir = document.createElement("button");
      revoir.type = "button";
      revoir.className = "book-revoir";
      revoir.textContent = "Tout revoir";
      revoir.onclick = () => { pilierTenu = null; dessiner(); };
      s.appendChild(revoir);
    }
    art.appendChild(s);

    // L'INTERRUPTEUR DES IDÉES, et seulement là où il a un sens : le coffret
    // des affaires. Éteint par défaut — on vient d'abord chercher un cahier —,
    // et son état se retient d'une session à l'autre comme le reste du décor.
    if (c.id === "boite-sujets") {
      if (idees) chargerIdees();
      const outils = document.createElement("div");
      outils.className = "book-coffret-outils";
      const bt = document.createElement("button");
      bt.type = "button";
      bt.className = "book-idees-bouton" + (idees ? " allume" : "");
      bt.setAttribute("aria-pressed", idees ? "true" : "false");
      const l = document.createElement("span");
      l.className = "book-idees-lampe";
      l.textContent = "\u{1F4A1}";
      bt.appendChild(l);
      bt.appendChild(document.createTextNode("idée"));
      bt.title = idees
        ? "Masquer l'idée principale de chaque affaire"
        : "Montrer, sous chaque affaire, ce qu'il y aurait à faire";
      bt.onclick = () => {
        idees = !idees;
        try { localStorage.setItem(MEMOIRE_IDEES, idees ? "1" : "0"); } catch (e) {}
        if (idees) chargerIdees();
        dessiner();
      };
      outils.appendChild(bt);

      // RANGER PAR CE QUE ÇA PÈSE — et l'ordre par main reste le défaut, parce
      // que c'est ainsi qu'on cherche un cahier : on sait de qui il est. Le
      // classement répond à l'autre question, celle qu'aucun rangement ne peut
      // poser en même temps : lequel de ces trente-sept porte le plus ? Il
      // casse donc les groupes, et c'est voulu — un classement qui reste
      // groupé par homme n'est pas un classement, c'est trente-sept petits.
      const bc = document.createElement("button");
      bc.type = "button";
      bc.className = "book-idees-bouton" + (parPoids ? " allume" : "");
      bc.setAttribute("aria-pressed", parPoids ? "true" : "false");
      bc.textContent = "⚖ par poids";
      bc.title = parPoids
        ? "Revenir au rangement par main"
        : "Ranger les affaires par ce qu'elles pèsent au plan, toutes mains mêlées";
      bc.onclick = () => {
        parPoids = !parPoids;
        try { localStorage.setItem(MEMOIRE_POIDS, parPoids ? "1" : "0"); } catch (e) {}
        dessiner();
      };
      outils.appendChild(bc);
      art.appendChild(outils);
    }

    const env = document.createElement("div");
    env.className = "book-table-enveloppe";
    const tab = document.createElement("table");
    tab.className = "book-table book-coffret-table";
    const tbody = document.createElement("tbody");

    // PAR MAIN, quand les volumes le disent. Trente-sept affaires en file sont
    // illisibles : celui qui ouvre le coffret cherche les SIENNES, ou celles
    // d'un homme dont il vient de parler. `tenu_par` ne déplace rien — le
    // cahier reste sur la table —, il dit sur quelle épaule le volume tombe.
    // Les mains gardent l'ordre où elles paraissent (donc la fraîcheur du tri
    // au-dessus, et non l'alphabet, qui range Aldon devant ce qu'on a touché
    // ce matin) ; « sur personne » ferme la marche, et c'est une information :
    // une affaire ouverte que personne ne porte n'a pas été confiée.
    const mains = [];
    livres.forEach((b) => {
      const qui = b.tenu_par || "";
      let g = mains.find((m) => m.id === qui);
      if (!g) mains.push((g = { id: qui, livres: [] }));
      g.livres.push(b);
    });
    const groupe = mains.some((m) => m.id);
    if (groupe) mains.sort((a, b) => (a.id ? 0 : 1) - (b.id ? 0 : 1));

    // La barre d'une main : le MÉDAILLON de « Les gens », pas un nom écrit.
    // On reconnaît une cour à ses têtes ; celui qui cherche les affaires du
    // Sanglier doit le trouver au visage, comme partout ailleurs dans le
    // décor. Le clic ouvre une pensée sur lui, comme partout ailleurs aussi.
    const barre = (m) => {
      const tr = document.createElement("tr");
      tr.className = "book-coffret-main" + (m.id ? "" : " book-coffret-main-vide");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.className = "book-coffret-main-nom";
      // Le contenu vit dans un bloc À L'INTÉRIEUR de la cellule : une cellule
      // de tableau qu'on passe en `flex` cesse de participer au calcul des
      // colonnes, et la barre se met à dicter la largeur de toute la liste.
      const dedans = document.createElement("div");
      dedans.className = "book-coffret-main-bloc";
      td.appendChild(dedans);
      const face = (m.id && window.Gens && Gens.medaillon)
        ? Gens.medaillon(m.id) : null;
      if (face) {
        // Un visage de 132 pixels est une galerie ; ici c'est une barre de
        // liste, et le médaillon s'y couche : la face petite, le nom et le
        // rôle à sa droite. Le dessin ne change pas, seule sa taille change.
        face.classList.add("book-coffret-main-gars");
        dedans.appendChild(face);
      } else {
        dedans.appendChild(
          document.createTextNode(m.id ? nomActeur(m.id) : "Sur personne"));
      }
      const n = document.createElement("span");
      n.className = "book-coffret-main-compte";
      n.textContent = compte(m.livres.length);
      dedans.appendChild(n);
      tr.appendChild(td);
      tbody.appendChild(tr);
    };

    const classe = parPoids && c.id === "boite-sujets" && crit && crit.affaires;
    if (classe) {
      livres.slice().sort((x, y) => ((poidsDe(y) || {}).score || 0)
        - ((poidsDe(x) || {}).score || 0)).forEach((b) => ligneVolume(b, tbody));
    } else {
      (groupe ? mains : [{ id: "", livres: livres }]).forEach((m) => {
        if (groupe) barre(m);
        m.livres.forEach((b) => ligneVolume(b, tbody));
      });
    }
    tab.appendChild(tbody);
    env.appendChild(tab);
    art.appendChild(env);
    return art;
  }

  // Une ligne de la carte d'un coffret : le signe, le nom, et le mot qui dit
  // d'où le volume sort. Elle s'ouvre d'un clic.
  function ligneVolume(b, tbody) {
      const tr = document.createElement("tr");
      tr.className = "book-coffret-ligne";
      tr.tabIndex = 0;
      tr.title = "Ouvrir — " + (b.titre || "ce volume");
      const ouvrir = () => { ouvert = b.id; dessiner(); };
      tr.onclick = ouvrir;
      tr.onkeydown = (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); ouvrir(); }
      };
      const signe = document.createElement("td");
      signe.className = "book-coffret-signe";
      signe.textContent = b.embleme || "";
      const nom = document.createElement("td");
      nom.className = "book-coffret-nom";
      nom.appendChild(document.createTextNode(b.titre || "Sans titre"));
      // L'OFFICE sous lequel le volume est tenu. La barre au-dessus dit déjà
      // QUI ; elle ne dit pas de quel chapeau — et trois hommes de cette table
      // en portent plusieurs. C'est aussi le sceau qu'on regarderait si
      // l'affaire tournait mal, donc ça se lit sans ouvrir.
      if (b.office) {
        const o = document.createElement("span");
        o.className = "book-coffret-office";
        o.textContent = b.office;
        nom.appendChild(o);
      }
      // CE QUE LE CAHIER PÈSE, et de combien ça a bougé depuis hier. Le
      // nombre seul dit une taille ; l'écart dit un MOUVEMENT, et c'est le
      // seul des deux qu'on ne puisse pas retrouver en ouvrant le volume —
      // le plan d'hier n'existe plus nulle part une fois `books.json` réécrit.
      const po = poidsDe(b);
      const pds = document.createElement("td");
      pds.className = "book-coffret-poids";
      if (po) {
        const v = document.createElement("span");
        v.className = "book-chiffre";
        v.textContent = String(Math.round(po.score));
        pds.appendChild(v);
        if (po.ecart != null && Math.round(po.ecart) !== 0) {
          const e = document.createElement("span");
          const monte = po.ecart > 0;
          e.className = "book-ecart " + (monte ? "book-ecart-haut" : "book-ecart-bas");
          e.textContent = (monte ? "+" : "−") + Math.abs(Math.round(po.ecart));
          // UN ÉCART QUI MONTE N'EST PAS UNE BONNE NOUVELLE, et la couleur ne
          // doit pas le laisser croire : la criticité monte quand on ÉCRIT du
          // plan — un cahier qu'on vient d'étoffer pèse plus lourd sans être
          // plus avancé. Elle descend quand on FAIT, ou quand on renonce.
          e.title = monte
            ? "Plus lourd qu'hier : on y a écrit, ou un empêchement s'est ajouté."
            : "Plus léger qu'hier : des pas ont été faits, ou une chaîne a été coupée.";
          pds.appendChild(e);
        }
        tr.title = (b.titre || "ce volume") + " — " + Math.round(po.score)
          + " de criticité, " + po.pas + " pas, " + po.goulots + " sans doublure";
      }
      const mot = document.createElement("td");
      mot.className = "book-coffret-mot";
      const pil = pilierDe(b), act = actionsDe(b);
      // Le genre du volume ne s'écrit que s'il distingue. Dans un coffret
      // d'affaires, trente-sept fois le mot « Plan » occupe la place sans rien
      // apprendre ; l'onglet le dira quand on aura ouvert.
      const gg = (pil || act.total || b.tables) ? null : genre(b);
      if (gg) {
        const m = document.createElement("span");
        m.className = "book-genre";
        m.textContent = gg.nom;
        nom.appendChild(m);
      }
      if (pil || act.total) {
        // Les marques. Le sous-titre passe au survol : il dit de quelle main le
        // volume est et quand il fut ouvert, ce qui est vrai de tous et ne
        // choisit rien.
        mot.classList.add("book-marques");
        if (b.sous_titre) tr.title = (b.sous_titre || "").trim();
        if (pil) {
          // Un pilier s'empoigne : cliquer ne fait qu'une chose, ne garder que
          // celui-là. Recliquer rend le coffret.
          const p = document.createElement("button");
          p.type = "button";
          p.className = "book-marque book-pilier pilier-" + pil.id
            + (pilierTenu === pil.id ? " tenu" : "");
          p.textContent = pil.nom;
          p.title = pilierTenu === pil.id
            ? "Revoir tout le coffret" : "Ne garder que « " + pil.nom + " »";
          p.onclick = (ev) => {
            ev.stopPropagation();
            pilierTenu = pilierTenu === pil.id ? null : pil.id;
            dessiner();
          };
          mot.appendChild(p);
        }
        if (act.total) {
          // Ce qui est fait sur ce qui est écrit. Le dénominateur compte autant
          // que le numérateur : trois faites sur cinq n'est pas trois sur
          // vingt-quatre, et c'est ce rapport-là qui dit où l'on en est.
          const a = document.createElement("span");
          a.className = "book-marque book-avance"
            + (act.faites >= act.total ? " pleine" : act.faites ? "" : " nulle");
          a.textContent = act.faites + " / " + act.total;
          a.title = act.total + " actions écrites, " + act.faites + " faites, "
            + act.cours + " en cours.";
          mot.appendChild(a);
        }
        if (act.cours) {
          const c = document.createElement("span");
          c.className = "book-marque book-encours";
          c.textContent = act.cours + " en cours";
          mot.appendChild(c);
        }
        // La troisième marque n'existe que quand elle alarme.
        if (act.bloquees) {
          const bl = document.createElement("span");
          bl.className = "book-marque book-bloque";
          bl.textContent = act.bloquees > 1
            ? act.bloquees + " bloquées" : "bloquée";
          mot.appendChild(bl);
        }
      } else if (b.tables || b.lignes) {
        // Un volume ouvert où rien n'est encore écrit. On ne le laisse pas
        // ressembler aux autres : c'est précisément ce qu'on cherche quand on
        // ouvre le coffret pour savoir ce qui traîne.
        mot.classList.add("book-marques");
        const v = document.createElement("span");
        v.className = "book-marque book-vide";
        v.textContent = "rien d'écrit";
        mot.appendChild(v);
      } else {
        // Le sous-titre d'un volume dit de quelle main il est et quand il fut
        // ouvert : c'est long, et l'on ne vient ici que pour choisir.
        const d = (b.sous_titre || "").trim();
        mot.textContent = d.length > 96 ? d.slice(0, 95).replace(/[\s,;—-]+$/, "") + "…" : d;
      }
      tr.appendChild(signe);
      tr.appendChild(nom);
      tr.appendChild(pds);
      tr.appendChild(mot);
      tbody.appendChild(tr);

      // ET SOUS L'AFFAIRE, EN RETRAIT, SON IDÉE. Une ligne, jamais deux : ce
      // coffret en aligne trente-huit, et trois idées chacune seraient
      // exactement le mur que cette maison appelle le tunnel. Une affaire sans
      // mission n'affiche rien du tout — pas de ligne vide, pas de « rien à
      // signaler ».
      if (idees) {
        const q = parLivre[b.id];
        if (q) {
          const tri = document.createElement("tr");
          tri.className = "book-coffret-idee";
          const tdi = document.createElement("td");
          tdi.colSpan = 3;
          tdi.appendChild(traitIdee(q.m));
          tri.appendChild(tdi);
          tbody.appendChild(tri);
        }
      }
  }

  // D'où vient ce livre — ce qui tient lieu de sous-titre à son onglet.
  function provenance(b) {
    if (b.notes) return "Sur vous, hors du monde";
    // Un volume calculé n'est nulle part : il n'a ni salle ni porteur, et
    // demander où il est n'a pas de sens. Sans cette ligne il tombait dans le
    // dernier cas et s'annonçait « Porté par » suivi de rien.
    if (b.calcule) return "Nulle part — refait à chaque ouverture";
    if (poseIci(b)) {
      const nom = nomSalle(b.salle_id);
      if (sousLaMain(b)) return nom ? "Ici — " + nom : "Ici, sous la main";
      return nom ? "Reste " + (/^(Le |La |L')/.test(nom) ? "à " + nom : "dans " + nom)
                 : "Ailleurs dans le château";
    }
    return b.acteur_id === moi() ? "Sur vous" : "Porté par " + nomActeur(b.acteur_id);
  }

  // Plusieurs livres dans la même salle ne s'empilent pas : ils se rangent en
  // onglets, comme des volumes sur une étagère. On en ouvre un à la fois — un
  // homme ne lit pas deux registres en même temps.
  // Le plus frais devant. On rangeait par PROXIMITÉ — sous la main, puis le
  // sien, puis ce qu'il fallait aller chercher — et c'était une étagère : un
  // ordre qui ne bouge jamais, où le registre qu'on vient de remplir reste
  // enfoui au même endroit qu'hier. Une table de travail se range autrement :
  // ce qu'on vient de toucher est sur le dessus.
  //
  // La fraîcheur se lit d'abord dans `date_maj` (une date de jeu, écrite par
  // qui touche le volume), et à défaut dans la POSITION dans books.json : un
  // volume ajouté l'a été après les autres, et c'est déjà une information. Rien
  // de neuf à tenir, donc, et un volume sans date n'est pas puni — il garde son
  // rang d'arrivée.
  const quand = (b) => {
    const d = b.date_maj;
    if (!d) return -1;
    return ((d.annee || 0) * 12 + (d.lune || 0)) * 30 * 1440
      + (d.jour || 0) * 1440 + (d.minute || 0);
  };

  function rangs() {
    const dedans = ici();
    // L'ordre du fichier, pour départager ceux qui n'ont pas de date : plus
    // loin dans books.json veut dire posé plus tard.
    const arrivee = new Map((books || []).map((b, i) => [b.id, i]));
    return dedans.slice().sort((a, b) => {
      // Les notes du joueur ferment toujours la marche : elles ne sont pas du
      // monde, elles n'ont pas de fraîcheur, et elles sont toujours à portée.
      if (a.notes !== b.notes) return a.notes ? 1 : -1;
      const da = quand(a), db = quand(b);
      if (da !== db && (da >= 0 || db >= 0)) return db - da;
      return (arrivee.get(b.id) || 0) - (arrivee.get(a.id) || 0);
    });
  }

  function dessiner() {
    const h = hote();
    if (!h) return;
    // L'ONGLET DOIT ÊTRE LÀ AVANT QU'ON OUVRE QUOI QUE CE SOIT. Le calcul était
    // demandé à l'ouverture d'un volume ; « Les pas » n'apparaissait donc
    // qu'après en avoir lu un autre — c'est-à-dire jamais pour qui vient
    // justement le chercher. On le demande à l'étagère.
    chargerCriticite();
    // On refait l'étagère à neuf : si le joueur avait la main dans ses notes
    // (une salle qui change pendant qu'il écrit), on lui rend sa place à la
    // ligne près, sinon il retrouve son curseur au début du carnet.
    const z = document.getElementById("book-notes-zone");
    const ecrivait = z && z === document.activeElement
      ? { debut: z.selectionStart, fin: z.selectionEnd } : null;
    salleVue = salleCourante();
    portantsVus = portants();
    // L'index des numéros suit l'étagère : un homme qui sort avec son cahier
    // emporte les renvois qui y menaient.
    indexer();
    h.innerHTML = "";
    const corps = document.createElement("div");
    corps.className = "books-corps";

    const dedans = rangs();
    // L'étagère n'est jamais vide — le carnet du joueur y est toujours. Mais
    // une salle sans livre reste une information : on la dit au-dessus, plutôt
    // que de laisser croire qu'il n'y avait rien à y chercher.
    const seulesNotes = dedans.length === 1 && dedans[0].notes;
    if (seulesNotes && books) {
      const ou = document.createElement("div");
      ou.className = "books-ou";
      const p = document.createElement("p");
      p.className = "books-vide";
      // Une page sans siège n'a pas une étagère vide : elle n'a pas d'étagère.
      // Le serveur ferme et le dit ; on ne fait pas croire qu'il n'y avait rien
      // à chercher dans la salle — le joueur irait chercher la faute au MJ.
      if (ferme) {
        ou.textContent = "L'étagère est close";
        p.textContent = "Cette page n'est assise à aucun siège : ouvrez le jeu "
          + "par votre lien, et vos livres reviennent.";
      } else {
        const nom = nomSalle(salleVue);
        ou.textContent = nom ? "Ce qui traîne ici — " + nom : "Ce qui traîne ici";
        p.textContent = "Rien à lire ici, et personne n'a sorti son carnet.";
      }
      corps.appendChild(ou);
      corps.appendChild(p);
    }

    // La tranche du haut mêle les COFFRETS et ce qui traîne à côté d'eux : une
    // table de travail porte des boîtes et des registres posés dessus, et l'on
    // n'oblige personne à ranger. Un coffret prend le rang de son volume le
    // plus frais — ce qu'on vient de toucher reste sur le dessus.
    const entrees = [];
    const parBoite = new Map();
    dedans.forEach((b) => {
      const c = coffret(b);
      if (!c) { entrees.push({ livre: b, livres: [b] }); return; }
      let e = parBoite.get(c.id);
      if (!e) {
        e = { boite: c, livres: [] };
        parBoite.set(c.id, e);
        entrees.push(e);
      }
      e.livres.push(b);
    });
    // Ce qu'on a sous les yeux : un coffret ouvert, ou un volume — jamais les
    // deux. Un coffret ouvert sans volume montre sa carte : ce qu'il y a
    // dedans, ligne à ligne. C'est ça, ouvrir une boîte.
    let active = ouverteBoite ? (parBoite.get(ouverteBoite) || null) : null;
    if (active) {
      if (ouvert && !active.livres.some((b) => b.id === ouvert)) ouvert = null;
    } else {
      ouverteBoite = null;
      active = entrees.find((e) => e.livres.some((b) => b.id === ouvert)) || null;
      if (active && active.boite) ouverteBoite = active.boite.id;
    }
    // Plus rien de retenu (on a changé de salle, un homme est sorti) : on
    // rouvre ce qui est sur le dessus de la pile.
    if (!active) {
      active = entrees[0];
      if (active.boite) { ouverteBoite = active.boite.id; ouvert = null; }
      else { ouverteBoite = null; ouvert = active.livre.id; }
    }

    // un onglet : un signe, un titre, et d'où la chose sort.
    function onglet(o, actif, sous, clic) {
      const bt = document.createElement("button");
      bt.className = "book-onglet" + (actif ? " actif" : "");
      bt.style.setProperty("--book-teinte", teinte(o));
      const g = genre(o);
      bt.title = (g ? g.nom + " — " : "") + sous;
      const t = document.createElement("span");
      t.className = "book-onglet-titre";
      // L'emblème : de quoi reconnaître un volume SANS le lire. Trente onglets
      // de titres se ressemblent tous au coin de l'œil ; un signe et une
      // couleur, non. C'est la même fonction que les emblèmes d'office sur le
      // plan du château — on cherche une forme, pas un mot.
      if (o.embleme) {
        const e = document.createElement("span");
        e.className = "book-onglet-embleme";
        e.textContent = o.embleme;
        t.appendChild(e);
      }
      t.appendChild(document.createTextNode(o.titre || "Sans titre"));
      bt.appendChild(t);
      const ou = document.createElement("span");
      ou.className = "book-onglet-ou";
      ou.textContent = sous;
      bt.appendChild(ou);
      bt.onclick = clic;
      return bt;
    }

    // À une seule entrée, pas d'onglet — une étagère d'un seul volume n'en est
    // pas une, et la provenance suffit à dire d'où il sort.
    if (entrees.length > 1) {
      const tranche = document.createElement("div");
      tranche.className = "books-tranche";
      entrees.forEach((e) => {
        const actif = e === active;
        if (e.boite) {
          // Un clic OUVRE le coffret : on voit ce qu'il y a dedans. Il ne se
          // met pas à lire un volume à notre place — on ouvre une boîte pour
          // regarder ce qu'elle contient, on prend le volume ensuite.
          const bt = onglet(
            e.boite, actif,
            provenance(e.boite) + " — " + compte(e.livres.length),
            () => { ouverteBoite = e.boite.id; ouvert = null; dessiner(); });
          bt.classList.add("book-coffret");
          if (actif) bt.classList.add("ouvert");
          tranche.appendChild(bt);
        } else {
          tranche.appendChild(onglet(
            e.livre, actif, provenance(e.livre),
            () => { ouverteBoite = null; ouvert = e.livre.id; dessiner(); }));
        }
      });
      tranche.classList.add("books-coffrets");
      corps.appendChild(tranche);
    } else if (!seulesNotes) {
      const ou = document.createElement("div");
      ou.className = "books-ou";
      ou.textContent = active && active.boite
        ? active.boite.titre + " — " + provenance(active.boite)
        : provenance(dedans[0]);
      corps.appendChild(ou);
    }

    // Un volume pris dans le coffret : on garde sa tranche au-dessus, pour
    // pouvoir passer de l'un à l'autre sans refermer la boîte.
    if (active.boite && ouvert && active.livres.length > 1) {
      const dedansBoite = document.createElement("div");
      dedansBoite.className = "books-tranche books-dedans";
      active.livres.forEach((b) => {
        const g = genre(b);
        dedansBoite.appendChild(onglet(
          b, b.id === ouvert, g ? g.nom : provenance(b),
          () => { ouvert = b.id; dessiner(); }));
      });
      corps.appendChild(dedansBoite);
    }

    const lu = ouvert ? dedans.find((b) => b.id === ouvert) : null;
    if (lu) corps.appendChild(lu.notes ? carteNotes() : carte(lu));
    else if (active.boite) corps.appendChild(carteBoite(active));
    h.appendChild(corps);

    if (ecrivait) {
      const nz = document.getElementById("book-notes-zone");
      if (nz) {
        nz.focus();
        try { nz.setSelectionRange(ecrivait.debut, ecrivait.fin); } catch (e) {}
      }
    }
  }

  function charger() {
    if (charge) return;
    charge = true;
    chargerNotes();
    // Le serveur ne sert que l'étagère de CE siège, et il la coupe au château
    // où l'on se trouve : la réponse dépend donc d'où l'on est au moment où on
    // la demande. On retient ce château-là — un homme qui débarque ailleurs
    // doit redemander l'étagère, sans quoi il emporte celle qu'il a quittée.
    chateauVu = chateauCourant();
    fetch("/books").then((r) => r.json()).then((d) => {
      books = (d && d.books) || [];
      boites = (d && d.boites) || [];
      ferme = !!(d && d.siege === false);
      // Une page ouverte AVANT que le serveur ait appris les coffrets garde sa
      // liste jusqu'au prochain changement de château — c'est-à-dire, le plus
      // souvent, jamais : les volumes rangés disparaissent de l'étagère et l'on
      // croit le rangement cassé. Des livres qui se disent dans une boîte sans
      // qu'aucune boîte ne descende : la liste est périmée, on la redemande.
      // Une seule fois : si le serveur ne sait décidément rien des coffrets,
      // c'est qu'il est vieux, et redemander toutes les quatre secondes ne le
      // rajeunira pas.
      if (!perime && !boites.length && books.some((b) => b.boite) && !ferme) {
        perime = true;
        charge = false;
        setTimeout(charger, 4000);
      }
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
    }).catch(() => { charge = false; });
  }

  function relire() { charge = false; charger(); }

  charger();

  // Une page qu'on ferme sur une phrase à moitié tapée : le minuteur n'aura
  // pas le temps de tomber, et une requête ordinaire serait coupée en vol. Le
  // beacon part quand même.
  window.addEventListener("pagehide", () => {
    if (notesEcrit === null || notes === notesEcrit) return;
    try {
      navigator.sendBeacon("/notes", new Blob(
        [JSON.stringify({ texte: notes })], { type: "application/json" }));
    } catch (e) {}
  });

  window.addEventListener("DOMContentLoaded", () => {
    if (window.Plan && Plan.echelle) {
      Plan.echelle({
        id: "books", nom: "Les livres", hote: "books", ordre: 6,
        // L'échelle était masquée là où il n'y avait rien à ouvrir — un livre
        // se consulte dans la salle où il est posé. Depuis que le joueur a son
        // carnet, il y a toujours quelque chose : `ici()` n'est jamais vide.
        dispo: () => ici().length > 0,
        reparu: () => {
          if (salleVue !== salleCourante() || portantsVus !== portants()) dessiner();
        },
      });
    }
    // Ce qui fait un endroit ici : le coffret ouvert, et le volume qu'on y lit.
    // Sans cela, revenir aux livres rendait l'étagère fermée — l'échelle était
    // gardée, la page ne l'était pas.
    if (window.Nav) {
      Nav.enregistrer("books", {
        clefs: ["coffret", "livre"],
        etat: () => ({ coffret: ouverteBoite, livre: ouvert }),
        poser: (p) => {
          if (!p.livre && !p.coffret) return true;
          if (p.livre && p.livre === ouvert) return true;
          if (!p.livre && p.coffret === ouverteBoite) return true;
          if (!books) return false;              // l'étagère n'est pas rentrée
          if (p.livre) return ouvrir(p.livre);
          const c = boites.find((b) => b && b.id === p.coffret);
          if (!c) return false;
          ouverteBoite = p.coffret; ouvert = null;
          dessiner();
          return true;
        },
      });
    }
    // Le registre des gens arrive après la première étagère : une carte de
    // coffret dessinée avant lui montre des noms sans visage. On se fait
    // rappeler une fois, et l'on redessine avec les têtes.
    if (window.Gens && Gens.quand) Gens.quand(() => dessiner());
    // la salle change sans prévenir personne, et un homme entre avec son carnet
    // sans rien annoncer non plus : on suit les deux de loin, ça ne coûte que
    // deux comparaisons de chaînes.
    setInterval(() => {
      // Changer de château, c'est changer d'étagère : ce n'est plus un tracé à
      // refaire, c'est une liste à redemander. On ne rappelle rien tant qu'on
      // ne sait pas où l'on est (au chargement, `chateauCourant()` est nul le
      // temps que la carte arrive) — le serveur, lui, l'a toujours su.
      const ch = chateauCourant();
      if (ch && !chateauVu) chateauVu = ch;       // la carte vient d'arriver
      else if (ch && chateauVu !== ch) { relire(); return; }
      if (salleVue === salleCourante() && portantsVus === portants()) return;
      dessiner();
      if (window.Plan && Plan.rebattre) Plan.rebattre();
    }, 1000);
  });

  // `page` et `poser` sortent du module pour le fil : un extrait montré en
  // scène doit avoir EXACTEMENT la mine qu'il aura dans le volume, sans quoi
  // le joueur croit voir deux objets là où il n'y en a qu'un.
  // OUVRIR UN VOLUME NOMMÉ, depuis ailleurs que l'étagère — c'est ce qui permet
  // au fil de dire « porté au registre » avec un lien qui y mène. Sans ça, le
  // joueur doit croire le MJ sur parole que ce qui s'est dit a été écrit.
  // `cible` est facultative : un numéro d'adresse, ou un bout de ce qui est
  // écrit là (« EC.4 », « deux colonnes à tout registre »). Le volume s'ouvre
  // et l'on DESCEND jusqu'à la ligne, au lieu de laisser le joueur au haut
  // d'une grille où il doit rechercher ce qu'on venait de lui montrer.
  function ouvrir(livreId, cible) {
    if (!livreId) return false;
    const trouve = (books || []).find((b) => b && b.id === livreId);
    if (!trouve) return false;
    ouvert = livreId;
    ouverteBoite = trouve.boite || null;
    if (window.Plan && Plan.montrer) Plan.montrer("books");
    dessiner();
    const h = hote();
    if (h && h.scrollIntoView) h.scrollIntoView({ behavior: "smooth", block: "nearest" });
    // La ligne visée l'emporte sur le volume : deux `scrollIntoView` de suite
    // se règlent l'un l'autre, et c'est le second qu'on veut voir gagner.
    if (cible != null && cible !== "") viser(cible);
    return true;
  }

  // `aller` sort aussi : le fil peut vouloir renvoyer à une ligne précise —
  // « c'est écrit au 23100 » — et non seulement au volume.
  // `affairesVues` sort pour que « Mon gouvernement », dans « Les gens », borne
  // ses comptes sur la MÊME étagère que ce volume-ci. `/criticite` est une route
  // de machine qui rend les quarante-deux affaires du dépôt, cahiers d'un autre
  // siège compris : deux écrans qui s'en servent doivent la borner de la même
  // main, sinon la fuite qu'on vient de reboucher ici rouvre ailleurs.
  return { charger, relire, page, poser, teinte, genre, ouvrir, aller, viser, fiche,
           affairesVues }
})();
