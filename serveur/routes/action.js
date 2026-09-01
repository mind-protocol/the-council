// POST /action — la parole et les gestes du joueur, versés dans son inbox.
const fs = require("fs");
const path = require("path");
const { RACINE } = require("../http");
const { envoyer } = require("../http");
const { audienceCourante, qui, roster } = require("../http");

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/action") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const action = JSON.parse(corps);
        action.recu_a = new Date().toISOString();
        // Signature du siège : sans elle, le MJ ne saurait pas lequel des
        // deux vient de parler. Roster absent = rien ne change.
        const siege = qui(req, url);
        if (siege) action.joueur_id = siege.personnage_id;
        // À deux MJ, chacun guette SON joueur : l'action tombe dans le
        // sous-dossier de son siège. Sans roster (ou siège inconnu), tout
        // atterrit à la racine comme avant — le guetteur d'une partie seule
        // ne voit aucune différence.
        const dossier = siege
          ? path.join(RACINE, "etat", "inbox", siege.personnage_id)
          : path.join(RACINE, "etat", "inbox");
        // L'adresse de la ligne, partagée entre l'inbox et le flux : c'est
        // par elle que le MJ retrouve la phrase à reformuler.
        const maintenant = Date.now();
        const ref = "v" + maintenant.toString(36) +
          Math.random().toString(36).slice(2, 6);
        action.ref = ref;
        fs.mkdirSync(dossier, { recursive: true });
        const cheminAction = path.join(dossier, "action-" + maintenant + ".json");
        fs.writeFileSync(cheminAction, JSON.stringify(action, null, 2), "utf-8");
        // Ce que le joueur dit ou fait entre dans le flux : sans cela, sa parole
        // n'existe que dans le navigateur et disparaît au premier rechargement.
        // « Laisser faire » se poste même vide : l'absence de consigne EST la
        // consigne — on joue le personnage comme on le connaît.
        if (action.type === "libre" && ((action.texte || "").trim() ||
            action.mode === "run" || action.mode === "jump" ||
            action.mode === "composer")) {
          // Une question est hors fiction : elle ne devient jamais une parole
          // prononcée par le personnage. Les coulisses le sont plus encore :
          // on y parle DE la partie, et rien de ce qui s'y dit n'a eu lieu.
          // Hors fiction, c'est une affaire privée : une question ou une
          // remarque de coulisses ne part qu'à celui qui l'a posée. Ce qui
          // est DIT ou FAIT, en revanche, se joue devant tout le monde.
          const prive = siege ? { pour: siege.personnage_id } : {};
          const item = action.mode === "question"
            ? Object.assign({ type: "question", texte: action.texte, delai_s: 0, ref }, prive)
            : action.mode === "meta"
            ? Object.assign({ type: "meta", texte: action.texte, delai_s: 0, ref }, prive)
            // Lâcher la bride n'est pas un geste dans la fiction : personne
            // dans la salle ne voit le joueur s'écarter. Ce qui suivra, en
            // revanche, sera bien du personnage — le MJ le poussera en
            // `vous`, à sa place et devant tout le monde.
            : action.mode === "run"
            ? Object.assign({ type: "run", texte: action.texte || "", delai_s: 0, ref }, prive)
            // Jump est une commande de régie privée : sa préparation ne
            // constitue ni une parole ni une action du personnage.
            : action.mode === "jump"
            ? Object.assign({ type: "jump", texte: action.texte || "", delai_s: 0, ref }, prive)
            // L'atelier : on compose SUR la partie. Rien n'entre dans la
            // fiction, personne ne l'entend, l'horloge ne bouge pas.
            // La main par-dessus le monde : on ne joue pas, on répare. Rien
            // de ce qui se dit ici n'a été prononcé dans la salle — mais ce
            // qu'on y demande change le fil et l'état pour de bon.
            : action.mode === "intervention"
            ? Object.assign({ type: "intervention", texte: action.texte, delai_s: 0, ref }, prive)
            : action.mode === "composer"
            ? Object.assign({ type: "composer", texte: action.texte || "", delai_s: 0, ref }, prive)
            : Object.assign(
                { type: "vous", mode: action.mode || "dire", texte: action.texte, delai_s: 0,
                  joueur_id: siege ? siege.personnage_id : undefined,
                  // L'adresse de la ligne, et le fait qu'elle attend d'être
                  // reformulée : le MJ répond par un `reecrit` portant ce
                  // même `ref`, et la page remplace le brouillon en place.
                  ref: ref,
                  ameliorer: action.ameliorer ? true : undefined },
                // Ce qui est dit dans une scene privee y reste : le joueur
                // herite de l'audience de la scene, comme tout le reste.
                //
                // Et quand rien ne l'etablit, ON SE FERME. `append_flux.py`
                // refuse d'ecrire dans ce cas-la ; le serveur n'a pas ce luxe
                // — un joueur qui parle attend que sa parole existe — alors il
                // se rabat sur le plus etroit : sa propre scene. Une parole
                // qu'on garde trop privee se rattrape d'un item ; une parole
                // lachee au camp d'en face ne se rattrape pas.
                //
                // MAIS LA PIECE PASSE AVANT LA SCENE. Deux joueuses debout
                // dans la meme roukerie s'entendent : c'est de la physique, et
                // aucune etiquette de scene ne doit pouvoir le contredire. Le
                // `pour` herite d'un `effacer` ouvert ailleurs, plus tot, a
                // rendu muette une joueuse qui parlait pourtant a trois pieds
                // de l'autre — six repliques tapees pour personne. On consulte
                // donc `presence.json` en PREMIER : meme piece, parole
                // entendue de la piece. (Meme regle dans `scripts/append_flux.py`.)
                //
                // ENTENDUE DE LA PIECE, PAS DU FICHIER. Rendre ici un `{}` —
                // « pas de pour », donc public — donnait la parole de la reine
                // et de sa maitresse de la voix au troisieme siege, qui se
                // tenait a deux lieues de la. On nomme donc les oreilles :
                // celles qui sont dans la salle, et elles seules.
                (function () {
                  const moi = siege && siege.personnage_id;
                  const l = roster();
                  if (moi && l && l.length > 1) {
                    try {
                      const pr = JSON.parse(fs.readFileSync(
                        path.join(RACINE, "etat", "presence.json"), "utf-8")).presence || {};
                      // LA SALLE D'ABORD, LE LIEU ENSUITE. `lieu` est un
                      // en-tete de TEXTE : il ne vaut que si le MJ l'a ecrit,
                      // et il s'orthographie comme il veut. Deux sieges
                      // debout dans `grenier-salle` avaient donc, l'un « La
                      // salle du Grenier, rue des Sœurs », l'autre `null` —
                      // et ne s'entendaient pas, dans la meme piece, tout un
                      // soir. `salle` est un ID : c'est lui qui tranche des
                      // que les deux en portent un.
                      const cle = (x) => (x && (x.salle || x.lieu)) || null;
                      const parSalle = pr[moi] && pr[moi].salle;
                      const ici = cle(pr[moi]);
                      const meme = (a) => a && (parSalle && a.salle
                        ? a.salle === parSalle : cle(a) === ici);
                      const voisins = !ici ? [] : l
                        .filter((j) => j.personnage_id !== moi
                            && meme(pr[j.personnage_id]))
                        .map((j) => j.personnage_id);
                      if (voisins.length) {
                        return { pour: [moi].concat(voisins).sort() };
                      }
                    } catch (e) {}
                  }
                  const a = audienceCourante(moi || null, (siege && siege.depuis) || 0);
                  // À PLUSIEURS, AUCUNE SORTIE NE REND UN ITEM MUET. Un `{}`
                  // écrit ici est un item sans audience, et un item sans
                  // audience finissait chez tout le monde. Même le commun se
                  // NOMME : la liste des sièges occupés, jamais une absence.
                  const tous = () => (l || []).filter((j) => j.occupe && j.personnage_id)
                    .map((j) => j.personnage_id).sort();
                  if (!moi || !l || l.length < 2) return {};
                  if (a === "commun") return { pour: tous() };
                  if (a) return { pour: a };
                  // Audience inconnue : on se ferme sur l'auteur. C'est le
                  // seul défaut sûr — au pire il se parle à lui-même, jamais
                  // il ne parle au camp d'en face.
                  return { pour: moi };
                })());
          fs.appendFileSync(path.join(RACINE, "etat", "flux.jsonl"),
            JSON.stringify(item) + "\n", "utf-8");
        }
        // PREMIÈRE COUCHE : la ref part au routeur direct APRÈS que l'action
        // et sa ligne de flux existent. Une parole atteint les habitants
        // physiquement présents ; les gestes et la régie atteignent le MJ.
        if (process.env.CONSEIL_SANS_REVEIL !== "1") {
          try {
            const { spawn } = require("child_process");
            const p = spawn(process.env.PYTHON || "python",
              [path.join(RACINE, "scripts", "router_message.py"),
               "--de", (siege && siege.personnage_id) || "joueur",
               "--ref", ref],
              { cwd: RACINE, detached: true, stdio: "ignore",
                windowsHide: true });  // sinon chaque action ouvre une console
            p.unref();
          } catch (e) { /* un reveil rate ne perd rien : l'inbox garde l'acte */ }
        }
        return envoyer(res, 200, JSON.stringify({ ok: true, ref }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ ok: false, erreur: String(e) }));
      }
    });
    return;
  }
  return false;
}

module.exports = traiter;
