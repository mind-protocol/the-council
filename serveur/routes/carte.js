// GET /carte et /ville — la table de guerre et l'échelle du bourg, telles que CE
// siège les croit : jetons, traits, bannières, et le vieillissement des certitudes.
const fs = require("fs");
const path = require("path");
const { RACINE, dateDe, lireCroyance } = require("../contexte");
const { AGE_DIT, jourAbsolu, vieillir } = require("../dates");
const { envoyer } = require("../http");
const { qui, regardeur } = require("../siege");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/carte") {
      try {
        const siege = qui(req, url);
        // Le monde commun se lit à la racine ; ce que le demandeur CROIT se
        // lit dans son dossier quand il en a un.
        const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
        const lireSien = (f, defaut) => lireCroyance(f, siege, defaut);
        const maisons = {};
        lire("maisons.json").forEach((m) => (maisons[m.id] = m));
        const lieux = lire("lieux.json").map((l) => ({
          // `alias` part avec le reste : la couche carte a ses propres ids, et
          // sans le pont le registre affiche « repaire-aux-corneilles » là où
          // il faut lire « Repos-des-Freux ».
          id: l.id, nom: l.nom, type: l.type, alias: l.alias || [],
          controle_id: l.controle_id,
          allegeance: (maisons[l.controle_id] || {}).allegeance_affichee || "neutre",
        }));
        let joueur_lieu_id = null, date = null, joueur_id_carte = null;
        try {
          // Sur QUI la carte se centre, et quelle tête elle tait. À deux, ce
          // n'est pas le personnage-joueur du journal : c'est celui qui
          // regarde. Une carte centrée sur Peyredragon quand on est ailleurs
          // est une carte qui ment sur l'endroit d'où l'on parle.
          const journal = lire("journal.json");
          const moi = regardeur(siege, journal);
          const pj = lire("personnages.json").find((p) => p.id === moi);
          if (pj) { joueur_lieu_id = pj.lieu_id || null; joueur_id_carte = pj.id; }
        } catch (e) {}
        date = dateDe(siege);
        // Ce que la table PORTE : osts, flottes, marches, sièges, serments.
        // Ce fichier n'est PAS la vérité du monde — c'est ce que le joueur
        // croit tenir, avec sa `certitude`. Absent = table nue.
        let jetons = [], traits = [], zones = [];
        try {
          const t = lireSien("jetons.json", { jetons: [], traits: [] });
          const vif = (m) => !m.statut || m.statut === "actif";
          jetons = (t.jetons || []).filter(vif);
          traits = (t.traits || []).filter(vif);
          zones = t.zones || [];
          // L'âge d'un pli est de l'arithmétique, pas une note que le MJ
          // retape à chaque battement : il porte la date de son départ, le
          // serveur compte les jours contre la date du monde. C'est ce
          // compte-là qui rend un silence lisible — « muet depuis neuf
          // jours » n'est pas la même chose que « muet depuis hier ».
          const jourNow = jourAbsolu(date);
          const compter = (m) => {
            if (!m) return;
            // Ce qui a eu lieu compte les jours ÉCOULÉS ; un dessein compte
            // ceux qui RESTENT. Les deux se calculent ici pour la même raison :
            // le MJ ne doit pas retaper un chiffre à chaque battement.
            if (m.jours == null && m.date) {
              const parti = jourAbsolu(m.date);
              if (parti != null && jourNow != null) m.jours = Math.max(0, jourNow - parti);
            }
            if (m.dans == null && m.echeance) {
              const du = jourAbsolu(m.echeance);
              if (du != null && jourNow != null) m.dans = du - jourNow;
            }
          };
          jetons.concat(traits).forEach((m) => {
            compter(m);
            // Un incident porte ses relais DANS lui : chacun a sa propre date
            // d'arrivée, donc son propre compte de jours. C'est la colonne de
            // chiffres qui dit à quelle vitesse la chose gagne.
            ["propage", "risque"].forEach((k) => {
              if (Array.isArray(m[k])) m[k].forEach((r) => compter(r));
            });
          });
          // Les oreilles : une oreille n'a pas d'état qu'on retape, elle a
          // un DERNIER MOT et une date. Le serveur en tire les deux choses
          // qui se lisent sur la table — depuis combien de jours elle n'a
          // rien dit, et à quel point on peut encore s'y fier.
          //
          // Le MJ n'écrit que les deux états qu'un calcul ne saurait pas
          // deviner : `nouee` (elle n'a rien donné encore) et `perdu` (on
          // SAIT qu'elle est tombée). Le reste se dérive : elle parle, ou
          // elle s'est tue. Il n'existe pas d'état « retournée » — si la
          // reine le savait, elle la couperait ; c'est le silence qui porte
          // le doute, et le silence ne dit jamais lequel des trois c'est.
          const MUETTE_APRES = 3;
          jetons.forEach((j) => {
            if (j.genre !== "oreille") return;
            if (j.etat !== "nouee" && j.etat !== "perdu") {
              j.etat = (j.jours != null && j.jours > MUETTE_APRES)
                ? "muette" : "parle";
            }
            // Elle pâlit comme une tête — mais elle ne SORT jamais de la
            // table. Une oreille qu'on n'entend plus depuis deux lunes est
            // précisément ce qu'il faut voir : la faire disparaître comme
            // une position périmée reviendrait à cacher le trou.
            if (j.jours != null && j.etat !== "nouee") {
              j.certitude = vieillir(j.certitude || "sure", j.jours) || "rumeur";
            }
          });
        } catch (e) {}
        // Les têtes : projetées de `vues.json`, jamais de `lieu_id`. Elles se
        // posent SOUS le point de la place (les osts s'empilent au-dessus),
        // et elles pâlissent toutes seules avec les jours.
        try {
          const persos = {};
          lire("personnages.json").forEach((p) => (persos[p.id] = p));
          // La couche carte a ses propres ids ; `alias` fait le pont.
          const alias = {};
          lire("lieux.json").forEach((l) => {
            alias[l.id] = (l.alias && l.alias[0]) || l.id;
          });
          const aujourdhui = jourAbsolu(date);
          const tetes = [];
          (lireSien("vues.json", { vues: [] }).vues || []).forEach((v) => {
            const p = persos[v.personnage_id];
            if (!p || p.etat === "mort" || p.id === joueur_id_carte) return;
            const quand = jourAbsolu(v.date);
            const age = (quand != null && aujourdhui != null)
              ? Math.max(0, aujourdhui - quand) : null;
            const presume = v.canal === "presume";
            const cert = presume ? (v.certitude || "rapportee")
              : vieillir(v.certitude || "sure", age);
            if (!cert) return;                       // trop vieux : on ne sait plus
            const m = maisons[p.maison_id] || {};
            tetes.push({
              id: "tete-" + p.id,
              genre: "tete",
              camp: m.allegeance_affichee || "neutre",
              ou: alias[v.lieu_id] || v.lieu_id,
              nom: p.nom.split(",")[0].trim(),
              dec: [0, 11],
              certitude: cert,
              detail: [presume ? "on l'y suppose" : AGE_DIT(age),
                       v.source, v.note].filter(Boolean).join(" — "),
              statut: "actif",
              _frais: presume ? 9999 : (age == null ? 9999 : age),
            });
          });
          // Une place où l'on croit savoir dix têtes ferait une colonne de
          // noms plus haute que le royaume. On en montre trois — les plus
          // fraîches — et la quatrième pièce dit combien on en tait.
          const parPlace = {};
          tetes.sort((a, b) => a._frais - b._frais)
            .forEach((t) => (parPlace[t.ou] = parPlace[t.ou] || []).push(t));
          Object.keys(parPlace).forEach((ou) => {
            const l = parPlace[ou];
            l.slice(0, 3).forEach((t) => { delete t._frais; jetons.push(t); });
            if (l.length > 3) {
              const reste = l.slice(3);
              jetons.push({
                id: "tetes-" + ou, genre: "tete", camp: "neutre", ou,
                nom: "et " + reste.length + " autres", dec: [0, 11],
                certitude: "rapportee", statut: "actif",
                detail: reste.map((t) => t.nom).join(", "),
              });
            }
          });
        } catch (e) {}
        return envoyer(res, 200,
          JSON.stringify({ lieux, joueur_lieu_id, joueur_id: joueur_id_carte,
                           date, jetons, traits, zones }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ lieux: [], erreur: String(e) }));
      }
    }
    // La ville : l'échelle intermédiaire — hors les murs, mais pas le royaume.
    // Même contrat que le terrain : fichier absent ou sans `id` = pas de
    // bascule pour y aller.
    // Une ville par lieu quand le fichier existe : `etat/villes/<lieu>.json`
    // est lu d'abord, `etat/ville.json` ensuite. Strictement additif — tant
    // qu'aucun fichier ne porte le nom du lieu où se tient le joueur, on sert
    // exactement ce qu'on servait avant. C'est ce qui permet de préparer une
    // ville où l'on n'est pas encore sans toucher à celle où l'on est.
    if (url === "/ville") {
      try {
        let ou = null;
        try {
          const siege = qui(req, url);
          const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
          const journal = lire("journal.json");
          const moi = regardeur(siege, journal);
          const pj = lire("personnages.json").find((p) => p.id === moi);
          if (pj) ou = pj.lieu_id || null;
        } catch (e) {}
        // UN JOUEUR DONT ON IGNORE LA POSITION N'HÉRITE D'AUCUNE CARTE.
        // Le repli sur `etat/ville.json` ne valait que pour une partie seule,
        // où il n'y a qu'un lieu possible. À deux sièges il fuit : un homme
        // du Crochet sans `lieu_id` recevait l'île de Peyredragon — la
        // garnison de la reine, ses nefs, ses têtes. C'est la même règle que
        // `lireCroyance` applique déjà aux jetons et aux vues : sans siège
        // identifié, rien.
        if (!ou) return envoyer(res, 200, JSON.stringify({ champ: null }));
        const fichiers = [];
        // un id de lieu est du kebab-case ; on refuse tout le reste, sinon
        // `..` dans un lieu_id ouvrirait le disque entier.
        if (/^[a-z0-9-]+$/.test(ou)) {
          fichiers.push(path.join(RACINE, "etat", "villes", ou + ".json"));
        }
        fichiers.push(path.join(RACINE, "etat", "ville.json"));
        for (const f of fichiers) {
          if (!fs.existsSync(f)) continue;
          const champ = JSON.parse(fs.readFileSync(f, "utf-8"));
          if (!champ || !champ.id) continue;
          // Une ville qui nomme un autre lieu que celui où l'on est n'est pas
          // la nôtre : mieux vaut pas d'échelle qu'une échelle qui ment.
          if (ou && champ.lieu_id && champ.lieu_id !== ou) continue;
          return envoyer(res, 200, JSON.stringify({ champ }));
        }
        return envoyer(res, 200, JSON.stringify({ champ: null }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ champ: null }));
      }
    }
    // Les livres : des objets posés dans les salles — un registre, un livre
    // de comptes, un rôle d'équipage. Chacun porte du JSON qu'on consulte à
    // la main.
    //
    // On les servait TOUS, en laissant à la page le soin de n'en montrer que
    // ce qui est à portée. À un joueur, c'était une commodité ; à trois
    // sièges, c'est une fuite : le carnet privé de la reine, celui de Marlo
    // et tout ce qui traîne à Port-Réal partaient sur le fil d'Aurore, où
    // l'on n'a qu'à ouvrir la console pour les lire. Le brouillard ne se
    // tient pas dans l'affichage, il se tient à la porte — donc ici.
    //
    // Trois coupes, et pas une de plus (la salle, elle, reste à la page : un
    // registre de maison se consulte de tout le château) :
    //   — un carnet `prive` n'est qu'à son porteur ;
    //   — un volume à `lecteurs` n'est qu'à ceux qui y sont nommés ;
    //   — ce qui est posé ou porté dans un AUTRE château ne descend pas.
    //
    // Et l'étagère se FERME à qui n'a pas de siège. Le repli sur le
    // personnage-joueur du journal est bon quand on joue seul ; dès qu'il y a
    // un roster, il veut dire qu'une URL nue — un lien de tunnel qui traîne,
    // un cookie perdu — ouvre le carnet de la reine. On rend alors la liste
    // vide et l'on dit pourquoi (`siege: false`), plutôt que de laisser la
    // page annoncer qu'il n'y a rien à lire.
  }
  return false;
}

module.exports = traiter;
