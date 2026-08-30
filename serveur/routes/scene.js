// GET /scene — la fenêtre de flux servie au navigateur, triée par audience.
const fs = require("fs");
const path = require("path");
const { MAX_FIL, RACINE } = require("../contexte");
const { envoyer, inlinerFigure } = require("../http");
const { rafraichirPortraits } = require("../portraits");
const { ecartDe, qui, roster } = require("../siege");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/scene") {
      try {
        const brut = fs.readFileSync(path.join(RACINE, "etat", "flux.jsonl"), "utf-8");
        let items = brut.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
        // Le brouillard, à deux : un item peut porter `pour: "<personnage>"`
        // — une pensée, une question, un aparté. Il ne part qu'à celui-là.
        // Le tri se fait ICI et non dans le navigateur : ce qui n'est pas
        // pour vous ne descend jamais jusqu'à votre machine.
        if (roster()) {
          const j = qui(req, url);
          const moi = j && j.personnage_id;
          // LA RÉGIE VOIT TOUT, et c'est sa seule raison d'être. Le tri par
          // `pour` protège un joueur de ce que l'autre entend ; Corneille
          // n'est pas un joueur — il n'a ni tête, ni horloge, ni siège dans
          // la fiction, et un fil amputé ne lui servirait à rien. Le jeton
          // reste la serrure : sans lui, on n'est toujours personne. La
          // fenêtre et le `?avant=` ci-dessous s'appliquent comme pour tous.
          if (j && j.regie) items = items.slice();
          else {
          // Sans jeton, on n'est personne — et personne ne lit la partie.
          // Le filtre par `pour` ne suffit pas : l'immense majorite du flux
          // n'en porte aucun, donc un inconnu recevait l'histoire entiere.
          // Le jeton n'est pas qu'un siege, c'est la serrure : le jeu est
          // servi par un tunnel public, et une URL nue circule vite.
          if (!j) return envoyer(res, 200, JSON.stringify({ items: [] }));
          // Le point d'entree du siege. Un item sans `pour` est PUBLIC — ce
          // qui est juste pour la suite, et faux pour l'avant : tout
          // l'historique anterieur a l'arrivee d'un joueur n'en porte aucun,
          // et son navigateur rejouerait donc la partie entiere d'un autre.
          // On ne reecrit pas le flux pour autant (il est append-only) : on
          // coupe a la ligne ou ce joueur est entre a la table.
          const depuis = (j && j.depuis) || 0;
          if (depuis) items = items.slice(depuis);
          // `pour` peut porter PLUSIEURS oreilles : c'est la messe basse, ce
          // que deux personnes se disent a l'ecart dans une salle qui en
          // compte six. Un tableau n'est ni public ni prive a une seule
          // oreille, et il ne doit surtout pas retomber dans le cas « pas de
          // pour » — qui, lui, veut dire que tout le monde entend.
          // UN ITEM SANS `pour` N'EST PLUS PUBLIC PASSÉ L'ÈRE MULTI-JOUEURS.
          // C'est le verrou de lecture, et il ferme la faille par en bas :
          // même si un jour une plume réécrit un item sans audience — un
          // script à venir, une main dans le fichier —, il ne partira chez
          // personne au lieu de partir chez tout le monde.
          //
          // Le seuil se calcule tout seul : la ligne où le DERNIER joueur
          // s'est assis. Avant elle, un `pour` absent veut dire « il n'y
          // avait qu'une table » et reste lisible par les anciens (leur
          // propre `depuis` fait déjà le tri). Après elle, un `pour` absent
          // est un bug, et un bug ne se diffuse pas.
          const seuil = roster().reduce((m, j) => Math.max(m, j.depuis || 0), 0);
          items = items.filter((it, k) => it.pour
            ? (Array.isArray(it.pour) ? it.pour.indexOf(moi) !== -1 : it.pour === moi)
            : depuis + k < seuil);
          }
        }
        // Le flux est append-only et ne cesse de grossir : au bout de
        // quelques heures de partie, chaque sondage retransmet des milliers
        // de lignes et le navigateur rejoue tout au rechargement. On ne sert
        // donc qu'une FENÊTRE. `debut` dit combien de lignes ont été coupées
        // en tête et `total` la longueur réelle du fil : le curseur du client
        // reste ainsi compté sur le flux entier — sinon la fenêtre glissant à
        // chaque nouvel item, le neuf ne serait jamais vu.
        //
        // `?avant=N` remonte le temps : la page qui précède l'index N, servie
        // quand le joueur fait défiler la chronique vers le haut. Le passé
        // descend alors par tranches, à la demande, et jamais d'un bloc.
        const total = items.length;
        const q = (req.url.split("?")[1] || "").match(/(?:^|&)avant=(\d+)/);
        let fin = q ? Math.min(Number(q[1]), total) : total;
        if (!(fin >= 0)) fin = total;
        const debut = Math.max(0, fin - MAX_FIL);
        items = items.slice(debut, fin);
        // Un volume montré en scène : sa page peut être un dessin. Le flux
        // n'en garde que le NOM — un levé pèse deux cent mille signes, et
        // trente lignes qui le portent feraient un fil illisible à charger.
        // Le nom est empreinté (voir append_flux.py) : la feuille de ce
        // jour-là ne bouge plus, même si le dessin est refait demain.
        items.forEach((it) => {
          if (it.montre && it.montre.extrait) inlinerFigure(it.montre.extrait);
          rafraichirPortraits(it);
        });
        return envoyer(res, 200, JSON.stringify({ items, debut, total, ecart: ecartDe(qui(req, url)) }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ items: [], debut: 0 }));
      }
    }
  }
  return false;
}

module.exports = traiter;
