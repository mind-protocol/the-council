// L'ÉCHIQUIER — le damier des affaires, composé à partir des cahiers.
// Sorti de la route parce que c'est un CALCUL et non un service : mille lignes
// qui relisent les plateaux d'un siège, les recollent et en tirent la chaîne.
// La route, elle, tient en dix lignes (routes/echiquier.js).

// Rend l'objet servi tel quel par `/echiquier`. Un plateau illisible ou une
// etagere vide se rendent en damier vide, jamais en erreur : le decor doit
// pouvoir s'ouvrir meme quand il n'y a rien dessus.

const fs = require("fs");
const path = require("path");
const bibliotheque = require("../plan/bibliotheque"); // meme container : import direct
const { RACINE } = require("../http");
const { numerosDesTetes, planModele } = require("../agents").activations; // LA PORTE serveur des agents
const { portraitDefaut, portraitFrais } = require("../peinture").portraits; // LA PORTE serveur de peinture
const { monPersonnage, roster } = require("../http");

function composer(req, url) {
  try {
    // ON NE LIT QUE CE QUE CE SIÈGE PEUT OUVRIR. Le damier servait
    // `books.json` en entier : Marlo, à Port-Réal, y trouvait les
    // quarante-deux plateaux du conseil de Peyredragon et pas un des
    // siens. Même tri que l'étagère, et pour la même raison — un plateau
    // qu'on ne peut pas ouvrir dans les livres est un plan qui n'est pas
    // le sien.
    const brut = bibliotheque.charger(RACINE);
    const moi = monPersonnage(req, url);
    if (!moi && roster()) {
      return { affaires: [] };
    }
    const porteePlan = planModele(moi);
    const idsVisibles = new Set(porteePlan.volumes_ids || []);
    const idsActifs = new Set(porteePlan.affaires_ids || []);
    const livres = (Array.isArray(brut) ? brut : [])
      .filter((l) => l && idsVisibles.has(l.id));
    const parId = {};
    livres.forEach((l) => { if (l && l.id) parId[l.id] = l; });
    // Une cellule de numéro porte son gras de registre : on ne garde que
    // l'adresse. « **M01** » vaut M01, et une adresse ne se renumérote
    // jamais — c'est une adresse, pas un rang.
    const adresse = (c) => String(c == null ? "" : c).replace(/[*\s]/g, "");
    const adresses = (c) => (String(c == null ? "" : c).match(/[MO]?\d+/g) || []);
    const propre = (c) => String(c == null ? "" : c).replace(/\*\*/g, "").trim();
    // Le libellé d'une pièce commence par le signe que le registre lui a
    // donné : on l'ôte du nom, parce que le plateau montre le signe du
    // RANG et l'encart le nom en clair.
    const sansSigne = (c) => propre(c).replace(
      /^(?:[←-⯿☀-➿️‍⃣]|[\uD83C-\uD83E][\uDC00-\uDFFF])+\s*/, "");
    const rien = (c) => { const t = sansSigne(c); return !t || t === "—" || t === "-"; };
    const sansAccent = (s) => String(s == null ? "" : s)
      .normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
    const chiffre = (n) => parseInt(String(n).replace(/\D/g, ""), 10) || 0;

    // ---- LA SOURCE, ET ELLE A CHANGÉ : LES CAHIERS ----------------------
    // Il y avait deux plans dans `books.json`, et cette vue lisait le petit.
    // Les six registres par type comptent 156 lignes ; les cahiers
    // d'affaire, qui portent chacun leurs propres tables 🎯 🔒 🗝️ ⚔️, en
    // comptent 1164 — dont 580 actions contre 60. La plupart des affaires
    // les plus travaillées n'avaient pas une ligne au registre, et le
    // plateau montrait donc un plan qui n'était plus celui du conseil.
    //
    // Le guide le disait déjà : « l'affaire est l'unité de TRAVAIL, les six
    // registres par type sont l'unité de RANGEMENT ». Le travail est dans
    // les cahiers ; l'index a décroché. On lit donc les cahiers.
    //
    // UN CAHIER = UNE AFFAIRE = UN PLATEAU, et le gain est plus grand que
    // le compte : l'appariement par NOM disparaît. Le volume EST l'affaire
    // — son titre, son emblème, son lien, sa main —, là où l'on rapprochait
    // deux chaînes de caractères et où l'on perdait « L'entrée sans
    // bataille » en chemin.
    //
    // LES COLONNES SE TROUVENT PAR LEUR EN-TÊTE, jamais par leur rang : un
    // cahier écrit « Le prix » et « Ce que cela ferme » là où le registre a
    // une seule colonne de coût, et l'un d'eux n'a pas de colonne « Où ».
    // Ce qu'un cahier n'écrit pas, on ne l'invente pas : la case reste vide
    // et la conclusion en tient compte.
    const CANON = {
      etat: [["l etat"], ["ce qui doit etre vrai"], ["ou"], ["la preuve"],
             ["sert"], ["affaire"]],
      verrou: [["le verrou"], ["bloque"], ["ce qui est vrai"], ["la preuve"],
               ["leve quand"]],
      clef: [["la clef"], ["ouvre"], ["le principe"],
             ["le prix", "ce qu elle coute"], ["la preuve"],
             ["decision", "retenue"]],
      // `depend de` est la HUITIÈME, et elle n'était lue par personne.
      // C'est pourtant la seule colonne du plan qui porte le lien
      // `attend` — 397 actions sur 611 y écrivent un numéro, dont 71
      // pointent hors du cahier. Sans elle, la moitié des arêtes qui
      // sortent d'une affaire n'existe pas pour l'écran.
      action: [["l action"], ["realise"], ["ce qu on fait"], ["office"],
               ["moyens"], ["la preuve"], ["ou ca en est", "etat"],
               ["depend de"]],
    };
    const TITRE = { etat: "etats cibles", verrou: "verrous",
                    clef: "clefs", action: "actions" };
    const quelleColonne = (cols, choix) => {
      let i = -1;
      choix.some((m) => { i = cols.indexOf(m); return i >= 0; });
      if (i >= 0) return i;
      choix.some((m) => { i = cols.findIndex((c) => c.indexOf(m) === 0); return i >= 0; });
      return i;
    };
    // Une ligne de cahier ou de registre, rendue à la forme que tout le
    // reste de cette route attend. Une colonne absente donne une case vide.
    const normaliser = (t, genre) => {
      const cols = ((t && t.colonnes) || []).map(sansAccent);
      const rangs = CANON[genre].map((choix) => quelleColonne(cols, choix));
      return ((t && t.lignes) || []).map((l) => {
        const c = Array.isArray(l) ? l : (l && l.cellules);
        if (!Array.isArray(c) || !c.length) return null;
        return { c: [adresse(c[0])].concat(rangs.map((i) => (i >= 0 ? c[i] : ""))),
                 num: adresse(c[0]) };
      }).filter((x) => x && x.num);
    };
    // Le titre d'une table porte parfois une suite après un tiret cadratin
    // (« Ouverture de l'Affaire — forme neuve du 26e au soir ») : on
    // apparie sur son début, jamais sur l'égalité.
    const tablesDe = (v, genre) => (v.tables || []).filter((t) => {
      const titreTable = sansAccent(String((t && t.titre) || "").split("\u2014")[0]);
      return (" " + titreTable + " ").indexOf(" " + TITRE[genre] + " ") >= 0;
    });

    const etats = [], verrous = [], clefs = [], actions = [];
    const bacs = { etat: etats, verrou: verrous, clef: clefs, action: actions };
    const groupes = [];
    // UN CAHIER D'AFFAIRE SE RECONNAÎT À SA FORME, PAS À SON NOM. La
    // règle était « un id qui commence par `affaire-` », et elle tenait
    // tant qu'une seule maison écrivait des affaires. La Néra tient les
    // siennes sous `nera-*`, au même gabarit, ouverture comprise : le
    // damier les ignorait toutes les sept. Un volume qui porte
    // l'ouverture de l'affaire EST une affaire, où qu'il soit rangé et
    // quel que soit son id — et la table des états cibles reste exigée,
    // sans quoi il n'y a pas de plateau à dessiner.
    const brouillons = porteePlan.brouillons || [];
    livres.filter((l) => idsActifs.has(l.id)).forEach((v) => {
      // `ecrites` : TOUTES les adresses que le cahier porte à ses quatre
      // tables, qu'elles atteignent le damier ou non. Ce n'est pas la
      // même chose que les pièces tracées, et l'écart est le sujet —
      // 130 lignes sur 1182 réalisent une clef qui n'existe pas, ou
      // pendent sous un état sans colonne. Le plateau a raison de ne pas
      // les dessiner ; un conseiller a le droit de les citer quand même,
      // et un renvoi vers l'une d'elles ne doit pas devenir du texte nu.
      const g = { titre: sansSigne(v.titre || v.id), volume: v, etats: [],
                  ecrites: [] };
      Object.keys(bacs).forEach((genre) => {
        tablesDe(v, genre).forEach((t) => normaliser(t, genre).forEach((r) => {
          // DE QUEL CAHIER SORT CETTE LIGNE. Les quatre bacs sont
          // GLOBAUX — un verrou d'un autre cahier tombe déjà dans notre
          // colonne s'il bloque notre état —, et rien ne disait d'où
          // venait une ligne. Sans cette marque, on ne peut pas
          // distinguer une arête qui reste chez nous d'une arête qui sort.
          r.aff = g.titre;
          if (genre === "etat") { r.c[6] = g.titre; g.etats.push(r); }
          if (/^\d{4,6}$/.test(String(r.num)) && g.ecrites.indexOf(r.num) < 0) {
            g.ecrites.push(r.num);
          }
          bacs[genre].push(r);
        }));
      });
      if (g.etats.length) groupes.push(g);
    });

    // ---- LES MOYENS ET LES OFFICES, D'OÙ QU'ILS VIENNENT ---------------
    // Ils étaient lus à deux ids fixes — `plan-moyens` et `plan-offices`,
    // les registres du Grand Plan de la reine. Une maison qui tient son
    // propre plan écrit les siens dans les TABLES d'un cahier
    // (`nera-moyens` porte les deux), et le damier lui rendait alors
    // toutes ses actions sans office et tous ses moyens inconnus. On
    // récolte donc par la FORME, dans tout ce que ce siège peut ouvrir :
    // une table qui porte une colonne « Le moyen » est un registre de
    // moyens, où qu'elle soit posée.
    //
    // LES COLONNES SE TROUVENT PAR LEUR NOM, JAMAIS PAR LEUR RANG. Le
    // registre des moyens a reçu deux colonnes de plus le jour où
    // `nos-moyens` y a été fusionné (« Ce qu'il vaut », « Ce qu'il peut
    // produire ») : lues au rang, la bulle disait « tenu par Tout ce qui
    // flotte dans la baie » et « à Corlys Velaryon ». Un registre qu'on
    // tient à la main gagne des colonnes, c'est sa vie ; une vue qui les
    // compte est une vue qui mentira un jour sans prévenir. Chaque ligne
    // emporte donc ses cases déjà résolues, et non le rang où les lire.
    const recolter = (genre) => {
      const tete = genre === "moyen" ? "le moyen" : "l office";
      const out = [];
      const prendre = (colonnes, lignes) => {
        const e = (colonnes || []).map(sansAccent);
        if (!e.some((c) => c.indexOf(tete) === 0)) return;
        const r = (mot, defaut) => {
          let i = e.indexOf(mot);
          if (i < 0) i = e.findIndex((x) => x.indexOf(mot) >= 0);
          return i >= 0 ? i : defaut;
        };
        const cases = genre === "moyen"
          ? { nom: r(tete, 1), dit: r("sait faire", 2), tient: r("qui le tient", 3),
              ou: r("ou", 4), etat: r("etat", 5) }
          : { nom: r(tete, 1), dit: r("repond", 3), tient: r("titulaire", 2),
              ou: -1, etat: r("decide seul", 4) };
        (lignes || []).forEach((l) => {
          const c = Array.isArray(l) ? l : (l && l.cellules);
          if (!Array.isArray(c) || !c.length) return;
          const x = { c: c, num: adresse(c[0]) };
          if (!x.num) return;
          Object.keys(cases).forEach((k) => {
            x[k] = cases[k] >= 0 ? propre(c[cases[k]]) : "";
          });
          out.push(x);
        });
      };
      livres.forEach((v) => {
        prendre(v.colonnes, v.lignes);
        (v.tables || []).forEach((t) => prendre(t.colonnes, t.lignes));
      });
      return out;
    };
    const moyens = recolter("moyen"), offices = recolter("office");
    if (!groupes.length) return { affaires: [], brouillons };

    const indexe = (t) => { const o = {}; t.forEach((x) => { o[x.num] = x; }); return o; };
    const iV = indexe(verrous), iM = indexe(moyens), iO = indexe(offices);
    // Un moyen et un office se citent par leur numéro — mais une action
    // écrite vite les nomme en toutes lettres. On rattrape le nom, et ce
    // qu'on ne rattrape pas devient une faute au lieu de disparaître.
    const parNom = (t) => {
      const o = {};
      t.forEach((x) => { o[sansAccent(sansSigne(x.nom))] = x; });
      return o;
    };
    const nM = parNom(moyens), nO = parNom(offices);
    // Les cases sont résolues à la récolte : il ne reste qu'à les lire.
    const cel = (t, genre, quoi) => (t && t[quoi]) || "";
    // Un article de tête n'est pas une différence : le registre écrit
    // « Maîtresse des nouvelles de la reine », l'action cite « la
    // maîtresse des nouvelles », et c'est le même office. Ce qui ne se
    // rattrape pas ainsi reste une faute et le montre — « à désigner »
    // n'est pas un office, et ne le deviendra pas par indulgence.
    const nu = (s) => sansAccent(s).replace(/^(?:l|le|la|les|du|de|des|d) /, "");
    const retrouver = (texte, index, noms) => {
      const code = adresses(texte).find((a) => index[a]);
      if (code) return index[code];
      const n = nu(sansSigne(texte));
      if (!n) return null;
      if (noms[n]) return noms[n];
      const cle = Object.keys(noms).find((k) => {
        const q = nu(k);
        return q && (n.indexOf(q) >= 0 || q.indexOf(n) >= 0);
      });
      return cle ? noms[cle] : null;
    };

    // Le volume de l'affaire — UN SEUL APPARIEMENT, et tout en sort : le
    // lien du clic, l'emblème que la maison lui a choisi, et la phrase qui
    // dit pourquoi l'affaire occupe le conseil. Le registre nomme
    // l'affaire en clair ; on la retrouve par son titre, et faute de titre
    // on n'invente ni lien mort ni emblème.
    const volumes = livres.filter((l) => l && String(l.id).indexOf("affaire-") === 0);
    const volumeDe = (nom) => {
      const n = sansAccent(nom);
      if (!n) return null;
      let v = volumes.find((l) => sansAccent(l.titre) === n);
      if (!v) v = volumes.find((l) => sansAccent(l.titre).indexOf(n) >= 0);
      return v || null;
    };
    // L'OBJET, au sens du guide : « une phrase, pourquoi cette affaire
    // mérite l'attention du conseil ». Les volumes l'écrivent dans leur
    // table d'ouverture, sous des intitulés voisins — on prend la ligne,
    // jamais on ne la compose. Faute d'ouverture écrite, le sous-titre du
    // volume dit déjà de quoi il traite.
    const objetDe = (v) => {
      if (!v) return null;
      const t = v.tables || [];
      for (const tb of t) {
        for (const l of (tb.lignes || [])) {
          const c = l && l.cellules;
          if (!c || !c[0]) continue;
          const tete = sansAccent(c[0]);
          if (tete.indexOf("objet") >= 0 || tete.indexOf("rend vrai") >= 0) {
            return propre(c[1]);
          }
        }
      }
      return v.sous_titre ? propre(v.sous_titre) : null;
    };

    // ---- LE TENEUR D'UNE ACTION, ET SON VISAGE ----
    // Une action cite son office ; l'office nomme son titulaire ; le
    // titulaire est quelqu'un de `personnages.json`. La dernière jointure
    // se fait sur un nom écrit en toutes lettres — « Ser Robert Quince,
    // onze ans en charge » — donc on la fait SOBREMENT : on ne lit que la
    // tête de la cellule (avant la première virgule, le point ou le
    // tiret), on ôte les titres, et l'on n'accepte qu'une suite de mots
    // ENTIERS commune aux deux côtés. « Wend » ne devient pas « Wenda »,
    // et un office VIDE ne prend pas le visage de qui se trouve nommé
    // dans sa ligne. Mieux vaut pas de visage qu'un mauvais visage.
    let gens = [];
    try { gens = JSON.parse(fs.readFileSync(
      path.join(RACINE, "etat", "personnages.json"), "utf-8")); } catch (e) {}
    const sansTitre = (t) => {
      let x = t;
      for (let i = 0; i < 3; i++) {
        const y = x.replace(
          /^(ser|dame|messire|mestre|maitre|maitresse|lord|lady|prince|princesse|le|la|les|l) /, "");
        if (y === x) break;
        x = y;
      }
      return x;
    };
    const tete = (c) => sansTitre(sansAccent(
      String(c == null ? "" : c).replace(/\*\*/g, "").split(/[,;.(—]/)[0]));
    const VACANT = ["vide", "vacant", "a designer", "designer", "neant"];
    const suite = (a, b) => {
      if (!a.length || a.length > b.length) return false;
      for (let i = 0; i <= b.length - a.length; i++) {
        if (a.every((m, j) => m === b[i + j])) return true;
      }
      return false;
    };
    const personneDe = (texte) => {
      const t = tete(texte);
      if (!t || VACANT.some((v) => t.indexOf(v) >= 0)) return null;
      const mots = t.split(" ");
      let pris = null, long = 0;
      gens.forEach((g) => {
        if (!g || !g.nom) return;
        const n = sansAccent(g.nom);
        [n, sansTitre(n)].forEach((cle) => {
          const m = cle.split(" ");
          if ((suite(mots, m) || suite(m, mots)) && cle.length > long) {
            pris = g; long = cle.length;
          }
        });
      });
      return pris;
    };
    // Le titulaire de l'office d'abord — c'est la chaîne du guide. À
    // défaut d'office numéroté, l'action nomme souvent la personne
    // elle-même (« Dame Aurore Inchauspé, maîtresse des nouvelles ») : on
    // la prend aussi. Ça ne lave pas la faute — aucun office ne porte
    // l'action, le fanion reste —, mais le plateau dit alors la vérité
    // entière : quelqu'un le fait, et personne n'en répond.
    const teneurDe = (o, cite) => (o ? personneDe(o.tient) : null) || personneDe(cite);
    // UN PORTRAIT NE SE SERT QU'UNE FOIS. Soixante actions, ce serait
    // soixante SVG dans la même réponse : on les range dans un
    // dictionnaire à part et l'action ne porte que l'identifiant de son
    // teneur. Le SVG est INLINÉ, jamais une URL — la page du jeu ne charge
    // aucune ressource externe.
    const portraits = {};
    const visage = (g) => {
      if (!g || !g.id) return null;
      if (portraits[g.id] === undefined) {
        let svg = "";
        const f = g.portrait && g.portrait.fichier;
        if (f) {
          try { svg = fs.readFileSync(path.join(RACINE, f), "utf-8"); } catch (e) {}
        }
        // LE CHAMP `portrait.fichier` N'EST PAS UNE CONDITION D'EXISTENCE.
        // Il manque à la moitié des fiches — Aldon Hask, le Sanglier —
        // alors que leur médaillon est peint et posé sur le disque.
        // `medaillons.py` écrit toujours `ecrans/portraits/<id>.svg` :
        // cet id EST l'adresse, comme sur la route des gens.
        if (!svg) svg = portraitFrais(g.id) || "";
        portraits[g.id] = svg || portraitDefaut(g.nom || g.id);
      }
      return g.id;
    };

    // Une clef est RETENUE, à étudier, ou écartée : c'est un état de la
    // clef, non un avancement. Une brèche dans un verrou, c'est une clef
    // retenue contre lui — rien d'autre ne perce la pierre.
    const tenueDe = (k) => {
      const e = sansAccent(k.c[6]);
      return e.indexOf("retenue") >= 0 ? "retenue"
        : e.indexOf("ecartee") >= 0 ? "ecartee" : "etudier";
    };
    const perce = (v) => clefs.some((k) =>
      adresses(k.c[2]).indexOf(v.num) >= 0 && tenueDe(k) === "retenue");

    // ---- LES MISSIONS : ce qu'il y aurait à faire ----------------------
    // La conclusion dit OÙ ça casse. Elle ne dit pas ce qu'on y ferait, et
    // c'était la moitié manquante : un plateau qui diagnostique et se tait.
    //
    // UN GABARIT, ET IL EST LUI-MÊME LE FILTRE :
    //
    //     Afin d'atteindre {X}, faire {Y} aurait effet {Z}.
    //
    // X se calcule EN REMONTANT — l'état cible que l'acte sert, et combien
    // d'autres il touche. Y est la seule part écrite en dur, par un verbe :
    // retenir, écarter, désigner, écrire, trouver. Z se calcule EN
    // REGARDANT L'AMONT IMMÉDIAT, et il doit être HONNÊTE : « le seul
    // verrou qui l'en sépare » quand c'est vrai, « un verrou sur deux »
    // quand ça ne suffit pas. Un détecteur dont on ne sait pas calculer le
    // X ou le Z n'est pas un détecteur : il se jette, il ne s'écrit pas
    // avec un Z vague.
    //
    // NI DATE NI PROSE : rien que la topologie et l'état des nœuds. Et
    // RIEN NE S'ÉCRIT — une mission s'affiche, elle ne touche aucun
    // registre. C'est du diagnostic rendu lisible, jamais une commande.
    //
    // LA DÉDUPLICATION SE FAIT PAR L'ACTE, PAS PAR LE DÉTECTEUR. « Toutes
    // les clefs de ce verrou sont à l'étude » et « cette action pend sous
    // une clef qui n'est pas retenue » désignent très souvent LE MÊME
    // ACTE : retenir cette clef-là. Un acte est donc identifié par le
    // couple (verbe, pièce) et posé UNE FOIS ; le premier détecteur qui le
    // trouve écrit sa phrase, les suivants s'y rangent. Sans cela le
    // plateau réclamerait trois fois la même décision sous trois libellés,
    // et c'est le tunnel — la faute que cette maison proscrit le plus dur.
    //
    // DEUX FAMILLES DE PORTEURS, et elles ne se confondent pas. À LA REINE
    // : retenir, écarter, désigner — c'est sa parole, personne d'autre ne
    // peut, et ça ne coûte rien à exécuter puisque le texte est déjà au
    // registre. AU CONSEIL : écrire, trouver — c'est du travail, et ça se
    // dépêche.
    const clefsDuVerrou = (v) => clefs.filter(
      (k) => adresses(k.c[2]).indexOf(v.num) >= 0);
    const actionsDeLaClef = (k) => actions.filter(
      (a) => adresses(a.c[2]).indexOf(k.num) >= 0);
    const verrousDeLetat = (n) => verrous.filter(
      (v) => adresses(v.c[2]).indexOf(n) >= 0);
    const verrousDeLaClef = (k) => verrous.filter(
      (v) => adresses(k.c[2]).indexOf(v.num) >= 0);
    const clefsDeLaction = (a) => clefs.filter(
      (k) => adresses(a.c[2]).indexOf(k.num) >= 0);
    const etatsDuVerrou = (v) => etats.filter(
      (e) => adresses(v.c[2]).indexOf(e.num) >= 0);
    const nomme = (q, genre) => ({
      genre: genre, numero: q.num, nom: sansSigne(q.c[1]) });

    // X — l'état cible qu'un verrou sert, et combien d'autres il touche.
    // On remonte, on ne devine pas : un verrou qui bloque trois états les
    // sert tous les trois, et le taire ferait mentir la mission sur sa
    // portée.
    const butDuVerrou = (v) => {
      const es = etatsDuVerrou(v);
      return { but: es.length ? nomme(es[0], "etat") : null,
               buts_autres: Math.max(0, es.length - 1) };
    };
    // Z — la clause de suffisance, mesurée sur le seul graphe : combien de
    // verrous se dressent encore devant l'état qu'on vise.
    const suffisance = (v) => {
      const es = etatsDuVerrou(v);
      const n = es.length ? verrousDeLetat(es[0].num).length : 0;
      return n <= 1 ? "le seul verrou qui l'en sépare"
        : "un verrou sur " + n;
    };

    // LA FORCE D'UN ACTE — ce qu'il débloque, mesuré sur le seul graphe et
    // non jugé. Lever le dernier verrou d'un état cible bat lever un verrou
    // sur deux, qui bat porter une action sous une clef, qui bat ce qui ne
    // lève rien. Elle classe l'idée d'une affaire ET la réserve d'un homme :
    // une seule règle, pour que les deux listes se lisent pareil.
    const forceActe = (m) => {
      const t = String((m && m.precision) || "");
      if (t.indexOf("le seul verrou") === 0) return 1;
      let x = t.match(/^un verrou sur (\d+)/);
      if (x) return 1 + parseInt(x[1], 10);
      if (t.indexOf("la seule action") === 0) return 20;
      x = t.match(/^une action sur (\d+)/);
      if (x) return 20 + parseInt(x[1], 10);
      return 60;
    };
    const catalogue = {};
    const attaches = {};
    // Le classement d'une liste d'actes : la force d'abord, puis la portée
    // (celle qui remonte au plus d'états), puis le coût — la parole de la
    // reine avant le travail du conseil.
    const classerActes = (a, b) => {
      const ma = catalogue[a], mb = catalogue[b];
      if (!ma || !mb) return 0;
      return forceActe(ma) - forceActe(mb)
        || (mb.buts_autres || 0) - (ma.buts_autres || 0)
        || (ma.sur === "reine" ? 0 : 1) - (mb.sur === "reine" ? 0 : 1);
    };
    // DEUX ESPÈCES DE TROUS, et elles ne valent pas la même chose.
    //
    // Le trou MÉCANIQUE est celui que ces six détecteurs trouvent tout
    // seuls : un verrou sans clef, une clef qu'on n'a pas tranchée, une
    // action dont l'office n'a pas de numéro. Il est exhaustif, gratuit à
    // trouver, et de faible valeur — c'est de la tenue de registre, ça
    // s'écrit à la plume et ça se coche.
    //
    // Le trou NARRATIF, lui, est introuvable par calcul : « ce plan
    // suppose que Bar Emmon dira oui ». Il se trouve en TRAVAILLANT, par
    // un homme qu'on dépêche, et c'est le seul qui déplace quelque chose.
    // Quand il le rapporte, il l'écrit comme un VERROU au cahier de son
    // affaire — c'est la définition du guide — et le mécanique reprend la
    // main aussitôt pour dire ce qui manque autour. Le mécanique est
    // l'AVAL du narratif, jamais son concurrent.
    //
    // Un seul de nos six détecteurs commande un travail narratif : « un
    // état cible sans aucun verrou » — on veut quelque chose et personne
    // n'a encore dit ce qui empêche. Il ne se coche pas : il se dépêche.
    // Il porte donc son espèce, et le plateau le marque autrement.
    const poserM = (m) => {
      m.espece = m.detecteur === "sans-verrou" ? "narratif" : "mecanique";
      if (!catalogue[m.acte]) catalogue[m.acte] = m;
      return m.acte;
    };
    const attacher = (genre, num, acte) => {
      const c = genre + "/" + num;
      if (!attaches[c]) attaches[c] = [];
      if (attaches[c].indexOf(acte) < 0) attaches[c].push(acte);
    };

    // 1. TOUTES LES CLEFS D'UN VERROU SONT À L'ÉTUDE — personne n'a
    //    tranché, et rien ne bouge tant que personne ne tranche.
    verrous.forEach((v) => {
      const ks = clefsDuVerrou(v);
      if (!ks.length || !ks.every((k) => tenueDe(k) === "etudier")) return;
      ks.forEach((k) => attacher("verrou", v.num, poserM(Object.assign(
        butDuVerrou(v), {
          acte: "retenir/" + k.num, sur: "reine", detecteur: "a-l-etude",
          verbe: "retenir ou écarter", piece: nomme(k, "clef"),
          effet: "lèverait", vers: nomme(v, "verrou"),
          precision: suffisance(v) }))));
    });

    // 2. UNE ACTION DONT PERSONNE NE RÉPOND. Deux manques se cachaient
    //    sous ce détecteur, et l'on demandait à la reine de désigner un
    //    homme DÉJÀ NOMMÉ : « aucun office du registre ne la porte » est
    //    vrai aussi quand la cellule dit « Mestre Gerardys, la roukerie ».
    //    Ce qui manque là n'est pas un homme, c'est un NUMÉRO — et ce fait
    //    est vrai de presque toutes les actions du plan. Il va donc au
    //    chapeau de l'affaire, compté une fois, jamais sur les jetons :
    //    quatre cent cinquante lampes qui disent la même chose ne disent
    //    plus rien. Ne reste ici que la vraie décision : personne, nulle
    //    part, ne répond de cette action.
    actions.forEach((a) => {
      if (retrouver(a.c[4], iO, nO)) return;
      if (personneDe(a.c[4])) return;   // quelqu'un la porte : c'est un numéro qui manque
      const ks = clefsDeLaction(a);
      const k = ks[0] || null;
      const vs = k ? verrousDeLaClef(k) : [];
      const v = vs[0] || null;
      const soeurs = k ? actionsDeLaClef(k).length : 0;
      attacher("action", a.num, poserM(Object.assign(
        v ? butDuVerrou(v) : { but: null, buts_autres: 0 }, {
          // AU CONSEIL, ET PLUS À LA REINE. Tant qu'on croyait demander
          // un homme, c'était sa parole ; maintenant qu'on demande un
          // NUMÉRO, c'est du travail de greffe — on n'appelle pas la
          // reine pour reporter une ligne au registre des offices.
          acte: "office/" + a.num, sur: "conseil", detecteur: "sans-office",
          // « Désigner qui répond de » était faux dès que la cellule
          // nomme quelqu'un en clair — « Mestre Gerardys, la roukerie » —
          // sans que ce nom se reconnaisse dans `personnages.json` :
          // quelqu'un la porte bel et bien, c'est le LIEN qui n'est pas
          // écrit. On ne demande donc pas un homme, on demande un numéro.
          verbe: "écrire le numéro de l'office de", piece: nomme(a, "action"),
          effet: k ? "porterait" : "lui donnerait une main",
          vers: k ? nomme(k, "clef") : null,
          precision: !k ? "elle ne remonte à aucune clef"
            : soeurs <= 1 ? "la seule action écrite sous elle"
            : "une action sur " + soeurs + " sous elle" })));
    });

    // 3. UN ÉTAT CIBLE SANS AUCUN VERROU — on veut, et l'on n'a pas dit ce
    //    qui empêche. X remonte alors d'un cran : l'état que celui-ci sert.
    etats.forEach((e) => {
      if (verrousDeLetat(e.num).length) return;
      const p = adresse(e.c[5]);
      const pere2 = etats.find((x) => x.num === p) || null;
      attacher("etat", e.num, poserM({
        acte: "empeche/" + e.num, sur: "conseil", detecteur: "sans-verrou",
        but: nomme(pere2 || e, "etat"), buts_autres: 0,
        verbe: "trouver ce qui empêche", piece: nomme(e, "etat"),
        // Z ne se répète pas : l'acte vise déjà cet état-là, et
        // « donnerait sa première prise sur lui-même » n'apprend rien.
        effet: "ouvrirait la première prise sur lui", vers: null,
        precision: "aucun verrou n'est écrit contre lui" }));
    });

    // 4. UN VERROU SANS AUCUNE CLEF — le fait est nommé, rien n'est
    //    envisagé contre lui.
    verrous.forEach((v) => {
      if (clefsDuVerrou(v).length) return;
      attacher("verrou", v.num, poserM(Object.assign(butDuVerrou(v), {
        acte: "clef/" + v.num, sur: "conseil", detecteur: "sans-clef",
        verbe: "écrire une clef contre", piece: nomme(v, "verrou"),
        effet: "donnerait de quoi le lever", vers: null,
        precision: suffisance(v) })));
    });

    // 5. UNE ACTION SOUS UNE CLEF NON RETENUE — elle part sans que le
    //    mécanisme qu'elle sert ait été tranché. MÊME ACTE que le premier
    //    détecteur quand la clef est à l'étude : la dédup s'en charge.
    //    L'acte SE POSE SUR LE VERROU, et pas sur l'action qui l'a fait
    //    voir : c'est là que la conclusion rend son verdict (« sa clef
    //    n'est qu'à l'étude »), et deux calculs qui accrochent la même
    //    chose à deux rangs différents finissent par se contredire — une
    //    action qui « tient » sous une mission à faire.
    actions.forEach((a) => {
      clefsDeLaction(a).forEach((k) => {
        if (tenueDe(k) === "retenue") return;
        const v = verrousDeLaClef(k)[0] || null;
        attacher(v ? "verrou" : "clef", v ? v.num : k.num, poserM(Object.assign(
          v ? butDuVerrou(v) : { but: null, buts_autres: 0 }, {
            acte: "retenir/" + k.num, sur: "reine", detecteur: "non-tranchee",
            verbe: "trancher", piece: nomme(k, "clef"),
            effet: v ? "lèverait" : "en déciderait le sort",
            vers: v ? nomme(v, "verrou") : null,
            precision: v ? suffisance(v)
              : "elle n'ouvre aucun verrou connu" })));
      });
    });

    // 6. UNE CLEF RETENUE SANS ACTION — décidée, et personne ne la fait.
    //    Aucune aujourd'hui ; le cas se garde, un plan bouge.
    clefs.forEach((k) => {
      if (tenueDe(k) !== "retenue" || actionsDeLaClef(k).length) return;
      const v = verrousDeLaClef(k)[0] || null;
      attacher("clef", k.num, poserM(Object.assign(
        v ? butDuVerrou(v) : { but: null, buts_autres: 0 }, {
          acte: "action/" + k.num, sur: "conseil", detecteur: "sans-action",
          verbe: "écrire l'action de", piece: nomme(k, "clef"),
          effet: "la mettrait en marche", vers: null,
          precision: "elle est retenue et rien ne la fait" })));
    });

    // ---- LE REPLI : ce que seuls les registres connaissent ----
    // Les six registres cessent d'être la source ; ils ne se jettent pas
    // pour autant. Six affaires y vivent que nul cahier ne porte (deux ont
    // bien un volume, mais vide de tables). On ne reprend d'elles que ce
    // qui ne collisionne avec rien et qui CHAÎNE à leurs propres états :
    // reprendre en vrac ferait rentrer par la bande le petit plan qu'on
    // vient d'écarter.
    // Par GENRE, et non en vrac : les numéros se croisent d'un rang à
    // l'autre — un verrou 100 masquait l'état 100, et le repli ne reprenait
    // plus rien du tout.
    const connu = { etat: {}, verrou: {}, clef: {}, action: {} };
    Object.keys(bacs).forEach((genre) => {
      bacs[genre].forEach((r) => { connu[genre][r.num] = 1; });
    });
    const REGISTRE_PLAN = { etat: "plan-etats-cibles", verrou: "plan-verrous",
                            clef: "plan-clefs", action: "plan-actions" };
    const repli = {};
    Object.keys(REGISTRE_PLAN).forEach((genre) => {
      repli[genre] = normaliser(parId[REGISTRE_PLAN[genre]], genre);
    });
    const memeNom = (x, y) => {
      const a3 = sansAccent(x), b3 = sansAccent(y);
      return !!a3 && !!b3 && (a3 === b3 || a3.indexOf(b3) >= 0 || b3.indexOf(a3) >= 0);
    };
    const orphelins = {};
    const horsAffaire = [];
    repli.etat.forEach((r) => {
      const nom = sansSigne(r.c[6]) || "Sans affaire";
      if (connu.etat[r.num] || groupes.some((g) => memeNom(g.titre, nom))) return;
      horsAffaire.push({ numero: r.num, titre: sansSigne(r.c[1]), affaire: nom });
      orphelins[r.num] = 1;
    });
    const chaine = (genre, pris, amont) => {
      repli[genre].forEach((r) => {
        if (connu[genre][r.num] || !adresses(r.c[2]).some((x) => amont[x])) return;
        bacs[genre].push(r); pris[r.num] = 1;
      });
    };
    const vRepli = {}, kRepli = {};
    chaine("verrou", vRepli, orphelins);
    chaine("clef", kRepli, vRepli);
    chaine("action", {}, kRepli);

    // ---- LA GOUTTIÈRE FRANCHISSABLE ------------------------------------
    // Le plateau s'arrêtait NET au bord du cahier. `pere()` traite un état
    // qui sert un état d'ailleurs comme une racine — la canopée se coupe
    // sans rien dire —, et la colonne `⛓️ Dépend de` n'était pas même lue.
    // Or ces arêtes-là existent, elles sont écrites, et elles sont
    // PROPRES : mesurées au niveau des PIÈCES, elles forment un graphe
    // acyclique de trois rangs. Ce sont les AFFAIRES qui bouclent, parce
    // qu'écraser deux cahiers en deux jetons fabrique un cycle qui n'est
    // nulle part dans le plan — c'est la raison pour laquelle il n'y a pas
    // de « plateau des affaires » et pourquoi le passage se fait ici,
    // pièce à pièce (voir docs/echiquier.md).
    //
    // QUATRE SENS, ET LEUR ORIENTATION EST CELLE DE LA CHAÎNE :
    //   sert     ⬆ notre état sert un état d'ailleurs — la canopée continue
    //   attendue ⬆ une action d'ailleurs attend cette pièce — on la nourrit
    //   servie   ⬇ un état d'ailleurs sert le nôtre — le travail est là-bas
    //   attend   ⬇ notre action attend une pièce d'ailleurs — le blocage y est
    const idAffaire = (titre) => sansAccent(titre).replace(/ /g, "-");
    // Qui porte ce numéro, et à quel rang. Les numéros se croisent d'un
    // cahier à l'autre (c'est documenté et ce n'est pas réparable au
    // calcul) : on garde donc TOUS les porteurs et l'on choisit celui qui
    // n'est pas chez nous.
    const chezQui = {};
    [["etat", etats], ["verrou", verrous], ["clef", clefs],
     ["action", actions]].forEach((paire) => {
      paire[1].forEach((r) => {
        (chezQui[r.num] = chezQui[r.num] || []).push({ genre: paire[0], r: r });
      });
    });
    // Ce qu'une action attend, retourné : le numéro attendu donne les
    // actions qui l'attendent. Une action peut dépendre de n'importe quel
    // rang — un verrou, une clef —, donc on retourne l'index une fois pour
    // toutes plutôt que de le chercher par genre.
    const attendu = {};
    actions.forEach((a) => adresses(a.c[8]).forEach((n) => {
      (attendu[n] = attendu[n] || []).push(a);
    }));
    const dehorsDe = (p, moi) => {
      const out = [], vu = {};
      const pose = (sens, r, genre) => {
        if (!r || !r.aff || r.aff === moi) return;
        const k = sens + "/" + r.num;
        if (vu[k]) return;
        vu[k] = 1;
        out.push({ sens: sens, numero: r.num, nom: sansSigne(r.c[1]),
          genre: genre, affaire: idAffaire(r.aff), affaire_titre: r.aff });
      };
      const mien = (chezQui[p.numero] || [])
        .find((x) => x.genre === p.genre && x.r.aff === moi);
      if (p.genre === "etat") {
        if (mien) adresses(mien.r.c[5]).forEach((n) => {
          const q = (chezQui[n] || [])
            .find((x) => x.genre === "etat" && x.r.aff !== moi);
          if (q) pose("sert", q.r, "etat");
        });
        etats.forEach((o) => {
          if (adresses(o.c[5]).indexOf(p.numero) >= 0) pose("servie", o, "etat");
        });
      }
      if (p.genre === "action" && mien) {
        adresses(mien.r.c[8]).forEach((n) => {
          const q = (chezQui[n] || []).find((x) => x.r.aff !== moi);
          if (q) pose("attend", q.r, q.genre);
        });
      }
      (attendu[p.numero] || []).forEach((o) => pose("attendue", o, "action"));
      return out;
    };

    // Les têtes, une fois pour toute la requête (voir numerosDesTetes).
    const tetes = numerosDesTetes();
    const affaires = groupes.map((g) => {
      const pieces = [], colonnes = [];
      // CE QUI SE DIT EN COURS SANS ÊTRE DANS LA TÊTE : un homme qui dit
      // travailler et dont le plan de journée n'en porte pas trace. Ça se
      // sert au MJ, ça NE SE PEINT PAS sur le plateau — c'est un écart
      // entre deux registres, pas une information de personnage.
      const divergents = [];
      const chez = {};
      g.etats.forEach((e) => { chez[e.num] = e; });
      // L'arbre : `Sert` pointe vers l'amont. Un état qui sert un état
      // d'une AUTRE affaire est une racine ici — on ne dessine pas la
      // moitié d'un arbre qui vit ailleurs.
      const pere = (e) => { const p = adresse(e.c[5]); return chez[p] ? p : null; };
      const enfants = {};
      g.etats.forEach((e) => { enfants[e.num] = []; });
      g.etats.forEach((e) => { const p = pere(e); if (p) enfants[p].push(e.num); });
      const racines = g.etats.filter((e) => !pere(e)).map((e) => e.num)
        .sort((a, b) => chiffre(a) - chiffre(b));

      const verrousDe = (n) => verrous.filter((v) => adresses(v.c[2]).indexOf(n) >= 0);
      // Une colonne s'ouvre sous ce qui porte quelque chose, et sous une
      // feuille même vide — c'est elle que l'épreuve du guide doit compter.
      const ouvre = (n) => verrousDe(n).length > 0 || !enfants[n].length;

      const niveau = {}, portee = {}, sienne = {};
      const descendre = (n, d) => {
        niveau[n] = d;
        const debut = colonnes.length;
        if (ouvre(n)) {
          sienne[n] = n;
          colonnes.push({ id: n, numero: n, titre: sansSigne(chez[n].c[1]),
            dit: propre(chez[n].c[2]), etat: n });
        }
        enfants[n].sort((a, b) => chiffre(a) - chiffre(b))
          .forEach((c) => descendre(c, d + 1));
        portee[n] = colonnes.slice(debut).map((c) => c.id);
      };
      racines.forEach((r) => descendre(r, 0));

      // ---- LA CONCLUSION : où ça casse, en descendant ----
      // UN SEUL MÉCANISME, pas six cas particuliers : on descend la
      // chaîne depuis la pièce et l'on s'arrête AU PREMIER TROU. Une
      // pièce, un coupable, une phrase — jamais une liste de griefs.
      // Tout se lit sur la topologie : ni date, ni prose, rien que ce que
      // le graphe dit déjà.
      //
      // Un état descend sur ses verrous ET sur les états qui le servent :
      // c'est ce que compte déjà l'épreuve du guide (la réglette rouge,
      // le fanion), et les deux calculs doivent dire la même vérité.
      const clefsDe = (v) => clefs.filter((k) => adresses(k.c[2]).indexOf(v.num) >= 0);
      const actionsDe = (k) => actions.filter((x) => adresses(x.c[2]).indexOf(k.num) >= 0);
      const dit = (q, genre) => ({
        genre: genre, numero: q.num, nom: sansSigne(q.c[1]),
      });
      const memo = {};
      const conclure = (q, genre) => {
        const memoire = genre + q.num;
        if (memo[memoire]) return memo[memoire];
        memo[memoire] = { cas: "tient" };     // garde-fou contre un cycle
        let r;
        if (genre === "action") {
          const of2 = retrouver(q.c[4], iO, nO);
          // La chaîne descend jusqu'au sol dès que QUELQU'UN la porte.
          // Mais si aucun office numéroté ne la porte, le jeton arbore
          // déjà son fanion : la conclusion doit le dire dans les mêmes
          // termes, sinon le joueur lit un drapeau rouge sous une phrase
          // qui dit que tout va bien. Ça ne casse pas la chaîne — ça
          // s'ajoute à elle.
          r = teneurDe(of2, q.c[4])
            ? (of2 ? { cas: "tient" } : { cas: "tient", sans_office: true })
            : { cas: "sans-teneur", cible: dit(q, "action") };
        } else if (genre === "clef") {
          // L'EMPÊCHEMENT D'UNE CLEF N'EST PAS SOUS ELLE, IL EST EN ELLE.
          // Une clef à l'étude concluait « la chaîne tient » dès qu'une
          // action portée pendait dessous — sur la pièce même que tout le
          // monde attend, et sur laquelle la mission se pose. Son état
          // propre passe donc AVANT ce qu'elle porte : rien ne partira
          // tant qu'on ne l'aura pas tranchée, et ce qui est écrit
          // dessous ne change rien à ça. Même règle pour une clef
          // écartée : ce qui pend sous elle ne sert plus à personne.
          const t = tenueDe(q);
          const sous = actionsDe(q);
          if (t === "etudier") r = { cas: "pas-tranchee", cible: dit(q, "clef") };
          else if (t === "ecartee") r = { cas: "ecartee", cible: dit(q, "clef") };
          else if (!sous.length) r = { cas: "sans-action", cible: dit(q, "clef") };
          else r = premier(sous.map((x) => [x, "action"]), dit(q, "clef"));
        } else if (genre === "verrou") {
          const ks = clefsDe(q);
          if (!ks.length) r = { cas: "sans-clef", cible: dit(q, "verrou") };
          else {
            const tenues = ks.filter((k) => tenueDe(k) === "retenue");
            if (!tenues.length) {
              r = { cas: "a-l-etude", cible: dit(q, "verrou"),
                    via: dit(ks[0], "clef"), autres: ks.length - 1 };
            } else r = premier(tenues.map((k) => [k, "clef"]), dit(q, "verrou"));
          }
        } else {
          const sous = verrousDe(q.num).map((v) => [v, "verrou"])
            .concat((enfants[q.num] || []).sort((a2, b2) => chiffre(a2) - chiffre(b2))
              .map((n) => [chez[n], "etat"]));
          if (!sous.length) r = { cas: "sans-verrou", cible: dit(q, "etat") };
          else r = premier(sous, dit(q, "etat"));
        }
        memo[memoire] = r;
        return r;
      };
      // Le premier enfant qui casse l'emporte ; les autres du MÊME cas se
      // comptent, pour qu'on puisse dire « et deux autres dans le même
      // cas » au lieu d'aligner les griefs.
      function premier(sous, dessus) {
        const vus = sous.map(([q, g]) => conclure(q, g));
        const i = vus.findIndex((v) => v.cas !== "tient");
        // « Personne n'en répond » NE S'ARRÊTE PAS À L'ACTION. Le caveat
        // remonte avec la chaîne, sans quoi une clef dont toutes les
        // actions sont portées hors registre dirait « la chaîne tient »
        // à plat — au-dessus de trois fanions et d'une mission à faire.
        // C'est la divergence qu'a révélée le calcul des missions ; on la
        // corrige ici, du côté qui mentait.
        if (i < 0) {
          const nu2 = vus.some((v) => v.sans_office);
          return nu2 ? { cas: "tient", sans_office: true } : { cas: "tient" };
        }
        const meme = vus.filter((v) => v.cas === vus[i].cas).length - 1;
        const r = Object.assign({}, vus[i]);
        r.autres = (r.autres || 0) + meme;
        // On garde le maillon d'où l'on est parti, pour que la phrase
        // puisse dire « X attend Y » quand ce n'est pas la pièce elle-même.
        if (!r.depuis) r.depuis = dessus;
        return r;
      }

      // ---- LA LAMPE : UNE PAR ACTE, SUR LA PIÈCE QU'IL VISE ----
      // Le champ `missions` d'une pièce est sa chaîne descendante entière
      // — c'est ce qu'il faut pour la bulle, et c'est trop pour le
      // plateau : un même acte y allumerait l'état cible, son verrou et
      // l'action qui l'a fait voir, trois lampes pour une décision. La
      // marque suit donc la même règle que les missions elles-mêmes, la
      // déduplication par l'ACTE : une idée, un acte, UNE lampe, posée sur
      // la pièce que l'acte vise — la clef à retenir, l'action dont il
      // faut désigner le teneur, le verrou contre quoi écrire une clef,
      // l'état qu'il faut mettre à l'épreuve. Les pièces d'amont
      // continuent de la DIRE dans leur bulle, ce qui est sa place.
      //
      // Une pièce peut être dessinée dans deux colonnes (un verrou qui
      // bloque deux états) : la lampe va sur la première, sans quoi on
      // compterait deux marques pour une décision.
      const posees = {};
      const lampeDe = (genre, num) => {
        const k = genre + "/" + num;
        if (posees[k]) return null;
        const a = Object.keys(catalogue).filter((x) => {
          const m = catalogue[x].piece;
          return m && m.genre === genre && m.numero === num;
        });
        if (!a.length) return null;
        posees[k] = 1;
        return a;
      };

      // ---- CE QUI PEND SOUS UNE PIÈCE, EN MISSIONS ----
      // La MÊME descente que la conclusion, et c'est voulu : les deux
      // calculs doivent dire la même vérité, sinon le joueur lit un
      // « la chaîne tient » au-dessus d'une chose à faire. On remonte les
      // actes de toute la chaîne aval, dédupliqués par l'acte, le plus
      // proche d'abord — la pièce elle-même, puis ce qui pend dessous.
      const memoM = {};
      const missionsDe = (q, genre) => {
        const memoire = genre + q.num;
        if (memoM[memoire]) return memoM[memoire];
        memoM[memoire] = [];              // garde-fou contre un cycle
        const sous = genre === "etat"
          ? verrousDe(q.num).map((v) => [v, "verrou"])
              .concat((enfants[q.num] || []).sort((a2, b2) => chiffre(a2) - chiffre(b2))
                .map((n) => [chez[n], "etat"]))
          : genre === "verrou" ? clefsDe(q).map((k) => [k, "clef"])
          : genre === "clef" ? actionsDe(q).map((a) => [a, "action"])
          : [];
        const out = [], vu = {};
        const ajoute = (a) => { if (!vu[a]) { vu[a] = 1; out.push(a); } };
        // D'ABORD L'ACTE QUI VISE CETTE PIÈCE — c'est celui dont elle
        // porte la lampe sur le plateau, et il serait absurde qu'elle
        // l'affiche au coin du sceau sans le dire dans sa bulle. Un acte
        // se pose sur le rang où la conclusion rend son verdict, mais il
        // se LIT aussi sur la pièce qu'il vise.
        Object.keys(catalogue).forEach((x) => {
          const m = catalogue[x].piece;
          if (m && m.genre === genre && m.numero === q.num) ajoute(x);
        });
        (attaches[genre + "/" + q.num] || []).forEach(ajoute);
        sous.forEach(([x, gg]) => missionsDe(x, gg).forEach(ajoute));
        memoM[memoire] = out;
        return out;
      };

      g.etats.forEach((e) => {
        const col = sienne[e.num] || null;
        const cle = (n) => (col || "arbre") + "/" + n;
        const pousse = (p) => { pieces.push(p); return p; };
        const sansPreuve = (c) => rien(c)
          ? ["sans preuve — rien ne dirait que c'est vrai"] : [];

        const mesVerrous = verrousDe(e.num);
        const mesClefs = clefs.filter((k) => adresses(k.c[2])
          .some((a) => mesVerrous.some((v) => v.num === a)));
        const mesActions = actions.filter((a) => adresses(a.c[2])
          .some((x) => mesClefs.some((k) => k.num === x)));

        // l'état cible : ce qui doit devenir vrai dans le monde
        const p = pere(e);
        pousse({
          cle: cle(e.num), genre: "etat", rang: "etat", colonne: col, numero: e.num,
          conclusion: conclure(e, "etat"), missions: missionsDe(e, "etat"),
          lampe: lampeDe("etat", e.num),
          nom: sansSigne(e.c[1]), dit: propre(e.c[2]), ou: propre(e.c[3]),
          preuve: propre(e.c[4]), sert: p, niveau: niveau[e.num] || 0,
          portee: portee[e.num] || [],
          part: mesVerrous.map((v) => ({
            numero: v.num, nom: sansSigne(v.c[1]), breche: perce(v),
          })),
          vers: p ? [(sienne[p] || "arbre") + "/" + p] : [],
          paie: "cet état en sert un autre",
          sans_preuve: rien(e.c[4]),
        });

        if (!col) return;   // un état qui coiffe n'a rien qui pende sous lui

        // les verrous : le fait du monde qui empêche l'état de tenir
        mesVerrous.forEach((v) => {
          const f = sansPreuve(v.c[4]);
          if (rien(v.c[5])) f.push("on ne sait pas dire à quoi il serait levé");
          pousse({
            cle: cle(v.num), genre: "verrou", rang: "verrou", colonne: col, numero: v.num,
            conclusion: conclure(v, "verrou"), missions: missionsDe(v, "verrou"),
            lampe: lampeDe("verrou", v.num),
            nom: sansSigne(v.c[1]), dit: propre(v.c[3]), preuve: propre(v.c[4]),
            leve_quand: propre(v.c[5]), breche: perce(v), vers: [cle(e.num)],
            paie: rien(v.c[5]) ? null : "levé quand : " + sansSigne(v.c[5]),
            fautes: f.length ? f : null,
          });
        });

        // les clefs : le mécanisme envisagé, et où il en est du jugement
        mesClefs.forEach((k) => {
          const amont = adresses(k.c[2]).filter((a) => mesVerrous.some((v) => v.num === a));
          const tenue = tenueDe(k);
          const f = [];
          // UNE RUPTURE, ET NON UNE REMARQUE. La différence commande la
          // couleur du plateau : `rupture` veut dire que la REMONTÉE est
          // cassée — il manque une pièce, la référence ne résout pas —, et
          // c'est la seule chose que l'écran peigne en rouge. Tout ce qui
          // manque et qui s'écrit à la plume (une preuve, un « levé
          // quand », un numéro d'office) est une LAMPE, pas une faute :
          // le plateau a déjà le dispositif qu'il faut pour le dire.
          let rupture = false;
          if (!adresses(k.c[2]).some((a) => iV[a])) {
            f.push("n'ouvre aucun verrou connu — la clef n'est pas reliée au plan");
            rupture = true;
          }
          pousse({
            cle: cle(k.num), genre: "clef", rang: "clef", colonne: col, numero: k.num,
            conclusion: conclure(k, "clef"), missions: missionsDe(k, "clef"),
            lampe: lampeDe("clef", k.num),
            nom: sansSigne(k.c[1]), dit: propre(k.c[3]), cout: propre(k.c[4]),
            preuve: propre(k.c[5]), tenue: tenue, vers: amont.map(cle),
            paie: tenue === "retenue" ? "clef retenue — " + sansSigne(k.c[5]) : null,
            fautes: f.length ? f : null, rupture: rupture,
          });
        });

        // les actions : ce qu'on décide effectivement de faire
        mesActions.forEach((a) => {
          const amont = adresses(a.c[2]).filter((x) => mesClefs.some((k) => k.num === x));
          const ou = sansAccent(a.c[7]);
          const marche = ou.indexOf("fait") >= 0 || ou.indexOf("en cours") >= 0;
          const of = retrouver(a.c[4], iO, nO);
          const f = sansPreuve(a.c[6]);
          let rupture = false;
          if (!amont.length) {
            f.push("ne remonte à aucune clef — l'action n'a pas de raison démontrée");
            rupture = true;
          }
          const qui_tient = teneurDe(of, a.c[4]);
          const quiId = visage(qui_tient);
          // DANS SA TÊTE, OU SEULEMENT SUR LE PAPIER. Voir numerosDesTetes
          // et la constante LIRE_LES_TETES.
          const dansLaTete = !!(quiId && tetes.par[quiId]
            && tetes.par[quiId][String(a.num)]);
          if (marche && !dansLaTete) divergents.push(a.num);
          if (!of) f.push("aucun office ne la porte : " + (propre(a.c[4]) || "à désigner"));
          // PERSONNE POUR LA PORTER : là, oui, il manque une pièce, et la
          // remontée s'arrête. Un office nommé EN CLAIR ne casse rien —
          // quelqu'un la porte très bien, ce qui lui manque est un NUMÉRO
          // et non un homme, et ce fait-là se dit une fois au chapeau.
          if (!of && !qui_tient) rupture = true;
          pousse({
            cle: cle(a.num), genre: "action", rang: "action", colonne: col, numero: a.num,
            conclusion: conclure(a, "action"), missions: missionsDe(a, "action"),
            lampe: lampeDe("action", a.num),
            nom: sansSigne(a.c[1]), dit: propre(a.c[3]), preuve: propre(a.c[6]),
            ou_ca_en_est: propre(a.c[7]), office: propre(a.c[4]), moyens: propre(a.c[5]),
            // Le visage de qui la porte : on ne sert que son identifiant,
            // le dessin est au dictionnaire commun.
            teneur_id: quiId, teneur: qui_tient ? qui_tient.nom : null,
            vers: amont.map(cle), paie: marche ? propre(a.c[7]) : null,
            fautes: f.length ? f : null, rupture: rupture,
            dans_la_tete: dansLaTete,
          });

          // les moyens et les offices : cités par leur numéro, jamais créés
          const cite = (texte, genre, index, noms) => {
            const t = retrouver(texte, index, noms);
            const k = cle(genre + "-" + (t ? t.num : sansAccent(texte).slice(0, 14)));
            let q = pieces.find((x) => x.cle === k);
            if (!q) {
              q = pousse({
                cle: k, genre: genre, rang: "moyen", colonne: col,
                numero: t ? t.num : null,
                nom: t ? sansSigne(t.nom) : sansSigne(texte),
                // La description d'une pièce est la colonne qui DIT la
                // chose, et elle n'est pas au même rang dans les deux
                // registres : « ce qu'il sait faire » pour un moyen, « ce
                // dont il répond » pour un office — jamais le titulaire.
                dit: t ? cel(t, genre, "dit") : "",
                tient: t ? cel(t, genre, "tient") : "",
                ou: t ? cel(t, genre, "ou") : "",
                tenue_du_moyen: t ? cel(t, genre, "etat") : "",
                vers: [], paie: t ? "au registre, " + t.num : null,
                fautes: t ? null : ["cité ici et absent de son registre — un moyen "
                  + "et un office ne se créent jamais dans une affaire"],
                // ET CE N'EST PAS UNE RUPTURE. « Le crédit de l'époux de
                // la reine », « ce que la reine sait du Donjon » : la
                // chose existe, elle est employée, elle est simplement
                // citée par son nom au lieu de son numéro. C'est vrai de
                // 477 pièces du plan — un fait vrai de presque tout le
                // monde va au chapeau et se dit une fois, jamais sur un
                // jeton (voir docs/echiquier.md).
                rupture: false,
              });
            }
            if (q.vers.indexOf(cle(a.num)) < 0) q.vers.push(cle(a.num));
          };
          if (!rien(a.c[4])) cite(a.c[4], "office", iO, nO);
          String(a.c[5] == null ? "" : a.c[5]).split(/·|;/).forEach((m) => {
            if (!rien(m)) cite(m, "moyen", iM, nM);
          });
        });

        // L'ÉPREUVE DU GUIDE, colonne par colonne : un état cible sous
        // lequel aucune action ne descend est une intention sans plan.
        const c = colonnes.find((x) => x.id === col);
        c.rompue = !mesActions.length;
        c.sans_verrou = !mesVerrous.length;
        // ET LE VERDICT INVERSE, qui manquait : la colonne est-elle
        // PORTÉE ? Une colonne dont la chaîne descend jusqu'à une action
        // n'est qu'un plan bien écrit ; elle n'est du travail que si l'un
        // des hommes qui la tiennent a écrit « en cours » ou « fait »
        // dans son cahier. C'est cela que le vert dit, et rien d'autre.
        c.porte = pieces.some((q) => q.genre === "action"
          && q.colonne === col && q.paie);
      });

      // ---- LES VOISINES : à quelles autres affaires celle-ci tient -----
      // PREMIÈRE VERSION ÉCARTÉE, et le joueur a tranché en la voyant : on
      // posait la sortie SUR LE JETON, un chevron par pièce et par sens.
      // Sur un damier qui porte déjà six teintes de rang, des dalles
      // d'occlusion, des lampes, des fanions, des visages et cent traits
      // de chaîne, cela faisait UN SIGNE DE PLUS et rien de lisible — et
      // ça poussait à remonter la chaîne causale pièce à pièce, ce que
      // personne ne veut faire à cette échelle.
      //
      // Ce qu'il fallait est plus petit : SAVOIR À QUI CETTE AFFAIRE
      // TIENT, et pouvoir y aller. Donc on agrège — le calcul par pièce
      // reste la source, mais rien n'en sort au niveau de la pièce. Une
      // ligne par affaire voisine, avec son emblème, servie au bandeau et
      // jamais au damier.
      const voisinage = {};
      pieces.forEach((p) => {
        if (!p.numero) return;
        dehorsDe(p, g.titre).forEach((x) => {
          const v = voisinage[x.affaire] || (voisinage[x.affaire] = {
            id: x.affaire, titre: x.affaire_titre, n: 0, sens: {} });
          v.n += 1;
          v.sens[x.sens] = (v.sens[x.sens] || 0) + 1;
        });
      });
      const voisines = Object.keys(voisinage).map((k) => {
        const v = voisinage[k];
        const vol = volumeDe(v.titre);
        return { id: v.id, titre: v.titre, n: v.n, sens: v.sens,
          embleme: (vol && vol.embleme) || null };
        // L'ORDRE EST CELUI DU POIDS, pas de l'alphabet : l'affaire à qui
        // l'on tient par onze arêtes passe avant celle qui n'en a qu'une.
      }).sort((a, b) => b.n - a.n || a.titre.localeCompare(b.titre));

      // ... et elle REMONTE dans l'arbre : un état qui coiffe des colonnes
      // toutes rompues est rompu lui-même, et le fanion se voit sur lui.
      pieces.filter((p) => p.genre === "etat").forEach((p) => {
        const sous = (p.portee || []).map((id) => colonnes.find((c) => c.id === id));
        const rompu = !sous.length || sous.every((c) => c && c.rompue);
        const f = p.sans_preuve ? ["sans preuve — rien ne dirait que c'est vrai"] : [];
        if (rompu) {
          f.push(p.portee && p.portee.length > 1
            ? "aucune action ne descend d'aucun état qu'il coiffe"
            : "aucune action ne descend jusqu'ici — une intention sans plan");
        }
        p.rompu = rompu;
        if (f.length) p.fautes = f;
        // Le SEUL défaut d'un état cible qui casse la remontée : rien ne
        // descend jusqu'à une action. Un état sans preuve écrite est mal
        // tenu, pas rompu.
        p.rupture = rompu;
        delete p.sans_preuve;
      });

      // Ce que l'affaire ENTIÈRE réclame — les actes de toutes ses pièces,
      // dédupliqués une dernière fois : deux colonnes qui pendent sous le
      // même verrou ne le réclament pas deux fois.
      const toutes = [], vuA = {};
      pieces.forEach((p) => (p.missions || []).forEach((a) => {
        if (!vuA[a]) { vuA[a] = 1; toutes.push(a); }
      }));
      // LE FAIT RETOURNÉ. « Ce verrou n'a pas de rechange » est vrai de
      // trente-deux verrous sur trente-trois : posé sur les jetons il ne
      // dirait rien et noierait le reste. Il ne se jette pas pour autant —
      // il se retourne et se dit UNE FOIS, au chapeau : aucun verrou du
      // plan n'a jamais eu deux clefs, quand le guide prévoit qu'elles
      // « se disputent la place ». Un fait vrai de presque tout le monde
      // va sur le blason, jamais sur une pièce.
      // CE QUI EST VRAI DE PRESQUE TOUTE L'AFFAIRE se dit au chapeau. Une
      // action dont l'office est nommé en clair a bien quelqu'un pour la
      // porter ; ce qui lui manque est une ligne au registre des offices,
      // et c'est une discipline à reprendre d'un coup, pas une décision
      // par action.
      const enClair = pieces.filter((q) => q.genre === "action"
        && (q.fautes || []).some((f) => f.indexOf("aucun office") === 0)
        && q.teneur).length;
      // Et le même fait, du côté des MOYENS : un galet ou une plume cités
      // par leur nom au lieu de leur numéro. Ce n'était compté nulle part,
      // donc c'était peint en rouge sur chaque jeton faute de mieux.
      const citesEnClair = pieces.filter(
        (q) => (q.genre === "moyen" || q.genre === "office") && !q.numero).length;

      const numsV = {}, mesV = [];
      pieces.filter((p) => p.genre === "verrou").forEach((p) => {
        if (!numsV[p.numero]) { numsV[p.numero] = 1; mesV.push(p.numero); }
      });
      const combienDeClefs = (n) => clefs.filter(
        (k) => adresses(k.c[2]).indexOf(n) >= 0).length;
      const rechange = {
        verrous: mesV.length,
        aucune: mesV.filter((n) => combienDeClefs(n) === 0).length,
        plusieurs: mesV.filter((n) => combienDeClefs(n) > 1).length,
      };

      // L'IDÉE PRINCIPALE — une affaire en réclame jusqu'à onze, et l'on
      // n'en montre qu'UNE là où l'on n'a la place que d'une ligne (le
      // coffret « Les sujets » en aligne trente-huit : trois idées chacune
      // seraient un mur). Le classement ne juge pas, il mesure, dans cet
      // ordre :
      //   1. LA FORCE DU Z — lever le dernier verrou d'un état cible bat
      //      lever un verrou sur deux, qui bat porter une action sous une
      //      clef, qui bat ce qui ne lève rien du tout.
      //   2. LA PORTÉE — à force égale, celle qui remonte au plus d'états.
      //   3. LE COÛT — à égalité encore, celle qui ne coûte qu'un mot au
      //      registre : la parole de la reine avant le travail du conseil.
      const idee = toutes.slice().sort((a, b) => classerActes(a, b))[0] || null;

      const v = g.volume || volumeDe(g.titre);
      return {
        // La clef de routage, telle que le cahier l'écrit — c'est elle qui
        // porte la réserve par homme, et rien d'autre.
        tenu_par: (v && v.tenu_par) || null, office: (v && v.office) || null,
        missions: toutes, rechange: rechange, idee: idee, en_clair: enClair,
        cites_en_clair: citesEnClair,
        // Ce que l'affaire porte VRAIMENT, et l'écart entre la parole et
        // la tête. Les deux vont au MJ ; seul `portees` se peint.
        portees: colonnes.filter((c) => c.porte).length,
        divergents: divergents,
        id: sansAccent(g.titre).replace(/ /g, "-"), titre: g.titre,
        livre_id: v ? v.id : null,
        // L'emblème est CELUI DU VOLUME, jamais un choix d'ici. Une
        // affaire dont aucun volume ne porte le nom garde le signe
        // générique de l'affaire, et c'est en soi une information.
        embleme: (v && v.embleme) || null, objet: objetDe(v),
        // L'INDEX DES ADRESSES, servi pour TOUTES les affaires et pas
        // seulement pour celle qu'on a ouverte. C'est ce qui permet à un
        // renvoi de scène — `[les neufs](44022)` — de savoir sur-le-champ
        // si le numéro qu'un conseiller vient de citer est une pièce du
        // plan, et laquelle. Sans lui, la page devrait interroger la route
        // pour chaque renvoi, ou pire : s'allumer à l'aveugle et parfois
        // mentir. On ne garde que les adresses qu'un renvoi peut porter —
        // quatre à six chiffres, la forme de `renvois.js` —, ce qui laisse
        // dehors les M01 et O17 des moyens et des offices.
        nums: (function () {
          const n = pieces.map((q) => q.numero)
            .filter((x) => /^\d{4,6}$/.test(String(x || "")))
            .filter((x, i, t) => t.indexOf(x) === i);
          return n;
        })(),
        // ET CE QUE LE CAHIER ÉCRIT SANS L'ATTEINDRE. Une ligne dont la
        // référence ne résout pas — l'action 21030 « réalise 21020 »
        // quand aucune clef 21020 n'existe — est écrite, numérotée,
        // citable en conseil, et n'a AUCUN jeton sur le damier. Le
        // plateau a raison de ne pas la dessiner : c'est la faute que le
        // guide veut voir. Mais la citer en scène est légitime, et un
        // renvoi vers elle doit mener à son cahier au lieu de retomber
        // en texte nu. On sert donc les deux listes, et l'écran fait la
        // différence : `nums` s'allume, `cites` ouvre le bon plateau et
        // dit pourquoi il n'y a rien à allumer.
        cites: (function () {
          const t = pieces.map((q) => String(q.numero || ""));
          return (g.ecrites || []).filter((n) => t.indexOf(n) < 0);
        })(),
        voisines: voisines,
        colonnes: colonnes, pieces: pieces,
        niveaux: Math.max(1, 1 + Math.max.apply(null,
          g.etats.map((e) => niveau[e.num] || 0))),
        rompues: colonnes.filter((c) => c.rompue).length,
      };
    });

    affaires.sort((a, b) => b.colonnes.length - a.colonnes.length);
    // ---- UN SEUL PLATEAU EN DÉTAIL ----
    // Trente-six cahiers font 2275 pièces et 1,8 Mo, quand le joueur n'en
    // regarde qu'un. Le détail ne part donc que pour l'affaire demandée ;
    // les autres n'envoient que leur chapeau — de quoi peupler la bascule,
    // les comptes et la bulle du blason. La page redemande la route quand
    // on change de plateau, et le catalogue des missions, lui, reste
    // entier : il sert aux comptes et aux livres.
    const demandee = ((req.url.split("?")[1]) || "").split("&")
      .map((x) => x.split("="))
      .filter((x) => x[0] === "affaire")
      .map((x) => decodeURIComponent(x[1] || ""))[0] || null;
    const ouverte = affaires.find((a) => a.id === demandee) || affaires[0] || null;
    const servies = affaires.map((a) => {
      if (a === ouverte) return a;
      return {
        id: a.id, titre: a.titre, livre_id: a.livre_id, embleme: a.embleme,
        objet: a.objet, missions: a.missions, rechange: a.rechange,
        en_clair: a.en_clair, cites_en_clair: a.cites_en_clair,
        portees: a.portees, divergents: a.divergents,
        nums: a.nums, cites: a.cites,
        idee: a.idee, rompues: a.rompues, colonnes: a.colonnes.length,
        // les pieds d'arbre, pour la bulle du blason : on les calcule ici
        // plutôt que d'envoyer les pièces entières.
        pieds: a.pieces.filter((q) => q.genre === "etat" && !(q.vers || []).length)
          .map((q) => ({ genre: "etat", numero: q.numero, nom: q.nom, cle: q.cle })),
      };
    });
    let aujourdhui = null;
    try {
      aujourdhui = JSON.parse(fs.readFileSync(
        path.join(RACINE, "etat", "monde.json"), "utf-8")).date || null;
    } catch (e) {}
    // LE CATALOGUE EST SERVI À PART, et les pièces ne portent que des
    // adresses d'actes. Un acte réclamé par une action, par sa clef, par
    // son verrou et par trois états ne se sérialise ainsi qu'UNE fois —
    // c'est la même économie que les portraits.
    return {
      affaires: servies, ouverte: ouverte ? ouverte.id : null,
      vue_de: moi, brouillons: brouillons,
      collisions: porteePlan.collisions || [],
      pieces_hors_affaire: porteePlan.pieces_hors_affaire || [],
      index_hors_affaire: horsAffaire,
      portraits: portraits, aujourdhui: aujourdhui,
      missions: catalogue };
  } catch (e) {
    return { affaires: [] };
  }
}

module.exports = { composer };
