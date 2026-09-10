// LE SIÈGE ET LE BROUILLARD — qui frappe à la porte, ce qu'il a le droit de
// voir, et à quelle audience appartient ce qu'il dit. C'est le seul endroit du
// serveur où un bug rend visible à un joueur ce qu'un autre a entendu.
// ---- les sièges : qui est à la table ------------------------------------
// `etat/joueurs.json` est un roster EN DUR — technique, hors docs/schema.md :
// [{jeton, personnage_id, nom}]. Le jeton fait office de clé : on ouvre le jeu
// une fois sur /?jeton=xxx, le serveur pose un cookie, et tout ce qui suit est
// signé. Sans roster, le jeu reste mono-joueur et rien ne change.

const fs = require("fs");
const path = require("path");
const { RACINE } = require("./contexte");
const { absolues } = require("./dates");

function roster() {
  try {
    const l = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "joueurs.json"), "utf-8"));
    return Array.isArray(l) && l.length ? l : null;
  } catch (e) { return null; }
}

// L'ÉCART DE FRONT — de combien ce joueur devance ou traîne sur l'autre.
// À deux, les horloges divergent : l'un tient un conseil de trois heures
// pendant que l'autre traverse la cour. Tant que l'écart reste petit, personne
// n'a besoin de le savoir ; passé quelques heures, une scène commune devient
// impossible sans que l'un des deux le sache, et c'est ce que dit le signe.

// Rend un nombre de minutes signé (positif = en avance), ou null.
const ECART_SEUIL = 300; // 5 heures
function ecartDe(siege) {
  const l = roster();
  if (!siege || !l || l.length < 2) return null;
  let h;
  try { h = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "horloges.json"), "utf-8")); }
  catch (e) { return null; }
  const mien = absolues(h && h[siege.personnage_id]);
  if (mien === null) return null;
  // On se compare aux sièges OCCUPÉS : un siège vacant avance au fil du monde
  // et n'a personne devant l'écran à qui l'écart voudrait dire quelque chose.
  const autres = l.filter((j) => j.personnage_id !== siege.personnage_id && j.occupe !== false)
    .map((j) => absolues(h && h[j.personnage_id])).filter((m) => m !== null);
  if (!autres.length) return null;
  // Le plus grand écart en valeur absolue : c'est celui qui gêne.
  let pire = 0;
  autres.forEach((m) => { if (Math.abs(mien - m) > Math.abs(pire)) pire = mien - m; });
  return Math.abs(pire) >= ECART_SEUIL ? pire : null;
}

// L'audience de la scene ouverte, lue dans le flux : le dernier `effacer`
// porte le `pour` de la scene en cours (voir scripts/append_flux.py). Le
// serveur doit la connaitre parce qu'il ecrit lui aussi dans le flux — la
// parole du joueur — et qu'une replique lachee sans audience dans une scene
// privee part droit chez l'autre camp.
// A DEUX JOUEURS, L'AUDIENCE N'EST PAS GLOBALE. Chacun est dans SA scene :
// pendant que la reine tient audience dans la grande salle, l'autre monte a la
// roukerie. Le dernier `effacer` du fichier appartient alors a n'importe qui —
// et prendre celui-la revient a estampiller la parole de l'un au nom de l'autre,
// ce qui la fait disparaitre de son propre ecran pour s'afficher sur celui d'en
// face. On ne retient donc que les `effacer` qui concernent CE joueur : les
// siens, et les scenes explicitement communes, qui valent pour tout le monde.
//
// UN `pour` ABSENT NE VEUT PAS DIRE « COMMUN ». Il dit « rien n'a ete declare »,
// et c'est le cas de TOUT le flux anterieur au passage a deux joueurs. Confondre
// les deux a coute une fuite entiere : la parole de la reine, heritant d'un
// `effacer` de l'ere mono-joueur, partait publique — donc sur l'ecran de sa
// maitresse de la voix, indefiniment, parce qu'aucun `effacer` ne portait son
// nom. On ne conclut donc au commun que sur le marqueur POSITIF `commun: true`
// que pose `append_flux.py --pour tous`.
//
// Rend "commun", un id de siege, ou null quand rien n'est etabli — trois etats
// distincts, parce que l'appelant doit pouvoir se fermer sur le troisieme.
function audienceCourante(siegeId, depuis) {
  try {
    const brut = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8");
    let pour = null;
    brut.split("\n").filter((l) => l.trim())
      // Ce qui precede l'arrivee du joueur a la table ne parle pas de lui : ces
      // scenes-la n'ont jamais eu d'audience a declarer.
      .slice(depuis || 0)
      .forEach((l) => {
        try {
          const it = JSON.parse(l);
          // UNE SCENE COMMUNE NE SE REFERME PAS TOUTE SEULE. Ne relire que les
          // `effacer` laissait « commun » en place indefiniment : le MJ rouvre
          // la scene privee d'un joueur avec une `salle` ou une simple replique
          // `--pour <lui>`, jamais avec un second `effacer`. L'audience restait
          // donc commune des heures apres, et tout ce que ce joueur TAPAIT
          // repartait sans `pour` — donc public, donc sur l'ecran du troisieme
          // siege, qui n'avait jamais mis les pieds dans cette salle.
          // Un item nominativement adresse a ce joueur seul REETABLIT donc son
          // audience privee. On exige un `pour` scalaire : un tableau est une
          // messe basse a l'interieur d'une scene, pas une scene nouvelle.
          if (it.type !== "effacer") {
            if (siegeId && it.pour === siegeId) pour = siegeId;
            return;
          }
          // La scene d'un tiers ne dit rien de l'endroit ou celui-ci se trouve.
          // `pour` peut nommer PLUSIEURS oreilles (une piece partagee, une
          // messe basse) : on y est concerne des qu'on y figure.
          if (it.pour && siegeId && (Array.isArray(it.pour)
                ? it.pour.indexOf(siegeId) === -1 : it.pour !== siegeId)) return;
          pour = it.pour || (it.commun ? "commun" : null);
        } catch (e) {}
      });
    return pour;
  } catch (e) { return null; }
}

// Qui frappe à la porte ? Le jeton d'abord (une URL qu'on partage), le cookie
// ensuite (les visites suivantes). Un jeton inconnu n'est personne.
// Sur QUI se centre ce qu'on rend — la carte, la ville, le terrain. C'est celui
// qui regarde, et non le personnage-joueur du journal : une carte centrée sur
// Peyredragon quand on est ailleurs ment sur l'endroit d'où l'on parle.
//
// Sauf pour un siège de RÉGIE, qui n'a pas de fiche et n'est donc nulle part :
// il regarde par-dessus l'épaule du siège principal. Sans cela sa carte n'a ni
// centre ni plan de château — et c'est le plan qu'il vient chercher, puisque
// c'est là qu'il touche un visage pour en ouvrir le fil.
function regardeur(siege, journal) {
  if (siege && siege.regie) {
    const principal = (roster() || []).find((s) => s.role === "principal");
    return (principal && principal.personnage_id) ||
      (journal && journal.personnage_joueur_id) || null;
  }
  return (siege && siege.personnage_id) ||
    (journal && journal.personnage_joueur_id) || null;
}

function qui(req, url) {
  const l = roster();
  if (!l) return null;
  const q = (req.url.split("?")[1] || "").match(/(?:^|&)jeton=([^&]*)/);
  const c = (req.headers.cookie || "").match(/(?:^|;\s*)jeton=([^;]*)/);
  const jeton = decodeURIComponent((q && q[1]) || (c && c[1]) || "");
  const j = l.find((x) => x.jeton === jeton);
  if (j) return j;
  // Le siège FABRIQUÉ d'un homme hors roster : n'importe quel personnage de
  // `etat/personnages.json` s'incarne depuis le jeu (habitant.md — tout homme
  // est un habitant). Le cookie `homme:<id>` est posé par /bascule ; le siège
  // n'existe que le temps de la requête, rien ne s'écrit dans joueurs.json.
  // `hors_roster` dit au front de router ses gestes vers /verbe et non /action.
  if (jeton.slice(0, 6) === "homme:") {
    const id = jeton.slice(6);
    // Le MJ UNIQUE n'est pas une fiche du monde : son existence est sa
    // chambre. Les anciens `mj-<ville>` restent morts ; seul `mj` ouvre ce
    // poste d'observation éphémère.
    if (id === "mj") {
      try {
        if (fs.statSync(path.join(RACINE, "chambres", "mj")).isDirectory()) {
          return { jeton: jeton, personnage_id: "mj", nom: "MJ",
                   hors_roster: true, mj: true };
        }
      } catch (e) {}
      return null;
    }
    try {
      const p = JSON.parse(fs.readFileSync(
        path.join(RACINE, "etat", "personnages.json"), "utf-8"))
        .find((x) => x.id === id);
      // Le siège porte son jeton : la route `/` re-pose le cookie depuis
      // `j.jeton`, et sans lui elle écrirait « undefined » à la place.
      if (p) return { jeton: jeton, personnage_id: p.id, nom: p.nom || p.id,
                      hors_roster: true };
    } catch (e) {}
  }
  return null;
}

// Le personnage derrière une requête : le siège si l'on en tient un, le
// personnage joueur du journal à défaut. Rendu `null` quand un roster existe
// et qu'aucun jeton ne va avec — on ne sert alors rien plutôt que tout.
function monPersonnage(req, url) {
  const siege = qui(req, url);
  let moi = (siege && siege.personnage_id) || null;
  if (!moi && roster()) return null;
  if (!moi) {
    try {
      moi = JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "journal.json"), "utf-8"))
        .personnage_joueur_id || null;
    } catch (e) {}
  }
  return moi;
}

// QUI VOIT QUEL VOLUME — les documents de sa maison, moins ceux dont les
// `lecteurs` ne le nomment pas.
//
// PARTAGÉ AVEC L'ÉCHIQUIER, et c'est la raison d'être de cette fonction : le
// damier lisait `books.json` en entier, sans tri. Un homme de Port-Réal qui
// tient ses propres affaires y voyait donc les quarante-deux plateaux du
// conseil de Peyredragon, et pas un des siens. Un plan qu'on ne peut pas
// ouvrir dans les livres n'a rien à faire sur le damier ; deux tris qui
// divergent finissent par montrer à l'un le plan de l'autre.
function volumesVisibles(tous, moi) {
  const maison = {};
  try {
    JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "personnages.json"), "utf-8"))
      .forEach((p) => { maison[p.id] = p.maison_id || null; });
  } catch (e) {}
  // Les BOÎTES (etat/boites.json) : un coffret posé sur une table ou porté
  // sous le bras, où l'on range des volumes. Une boîte donne sa PLACE à ce
  // qu'elle contient — un volume rangé n'a plus de salle, plus de porteur,
  // plus de `prive` à lui : il prend ceux du coffret, et l'on déplace vingt
  // registres en déplaçant une boîte. On résout ici, AVANT le tri : sans quoi
  // un volume rangé n'aurait plus de place du tout, et le brouillard le
  // laisserait passer partout.
  let boites = [];
  try {
    const bb = JSON.parse(fs.readFileSync(
      path.join(RACINE, "etat", "boites.json"), "utf-8"));
    if (Array.isArray(bb)) boites = bb;
  } catch (e) {}
  const coffret = new Map(boites.map((c) => [c.id, c]));
  tous.forEach((b) => {
    const c = b.boite && coffret.get(b.boite);
    if (!c) return;
    b.lieu_id = c.lieu_id || null;
    b.salle_id = c.salle_id || null;
    b.acteur_id = c.acteur_id || null;
    b.prive = !!c.prive;
    // `lecteurs` ne se remplace pas, il s'ajoute : un coffret peut fermer plus
    // que le volume, jamais moins.
    if (Array.isArray(c.lecteurs) && c.lecteurs.length) {
      b.lecteurs = (Array.isArray(b.lecteurs) && b.lecteurs.length)
        ? b.lecteurs.filter((q) => c.lecteurs.indexOf(q) !== -1)
        : c.lecteurs.slice();
    }
  });
  const maMaison = moi ? (maison[moi] || null) : null;
  // `lecteurs` survit au 31.8, seul des trois tris : il ne dit pas une place,
  // il retire nommément. Jumeau de `documents_maison.ouvert_a` (Python).
  const liste = maMaison ? tous.filter((b) => b.maison_id === maMaison
    && !(Array.isArray(b.lecteurs) && b.lecteurs.length
         && b.lecteurs.indexOf(moi) === -1)) : [];
  return { liste, boites };
}

module.exports = { roster, ecartDe, audienceCourante, regardeur, qui, monPersonnage, volumesVisibles };
