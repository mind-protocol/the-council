// GET /presence — qui est où, à cette minute, pour CE siège.
const fs = require("fs");
const path = require("path");
const { RACINE, dateDe, resoudrePresence } = require("../contexte");
const { envoyer } = require("../http");
const { qui, roster } = require("../siege");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/presence") {
      try {
        const siege = qui(req, url);
        const lire = (f) => JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8"));
        let moi = siege && siege.personnage_id;
        // LA RÉGIE N'EST NULLE PART, donc elle se tient où se tient le siège
        // principal — sinon son plan resterait vide et il n'y aurait aucun
        // visage à toucher, ce qui est tout ce qu'elle vient faire ici. Elle
        // ne perd rien au passage : le brouillard ne s'applique pas à un
        // siège qui n'incarne personne (voir `regie` dans etat/joueurs.json).
        const enRegie = !!(siege && siege.regie);
        if (enRegie) {
          const principal = (roster() || []).find((s) => s.role === "principal")
            || (roster() || [])[0];
          moi = (principal && principal.personnage_id) || null;
        }
        // Le repli sur le journal n'est bon qu'en partie SEULE. À deux, un
        // visiteur sans jeton hériterait de la pièce de la reine — et donc de
        // qui s'y trouve. Sans siège, on ne sait pas qui regarde : on ne dit rien.
        if (!moi) {
          const l = roster();
          if (!l || l.length < 2) {
            try { moi = lire("journal.json").personnage_joueur_id || null; } catch (e) {}
          }
        }
        // La position ne se stocke pas, elle se calcule — scripts/presence.py.
        // `presence` ne tient que les EXCEPTIONS (ce qu'une scène a constaté) ;
        // le reste se résout à L'HEURE DE CELUI QUI REGARDE.
        //
        // On lisait ici l'instantané `resolu` que `append_flux.py` fige à
        // chaque poussée. C'était faux d'une façon qu'on ne voyait pas : entre
        // deux items — c'est-à-dire presque toujours — le château restait
        // arrêté à la minute du dernier push, et PERSONNE N'ÉTAIT JAMAIS EN
        // MARCHE. Mesuré sur une journée de Peyredragon, quelqu'un traverse
        // 38 % des minutes ; le cache n'en montrait aucune. On recalcule donc
        // pour de bon, avec un cache court pour ne pas relancer Python à
        // chaque battement de sonde. Si le calcul échoue, on retombe sur
        // `resolu`, puis sur les exceptions nues : le jeu ne s'arrête pas.
        let presence = {};
        let connus = [];
        try {
          const f = lire("presence.json");
          presence = f.presence || {};
          const r = resoudrePresence(dateDe({ personnage_id: moi }))
            || (f.resolu && f.resolu.gens);
          if (r) {
            presence = {};
            // Qui est SUIVI, transit compris : un homme dans l'escalier n'est
            // dans aucune pièce, mais on sait où il est — il ne doit pas passer
            // pour un inconnu de passage.
            connus = Object.keys(r);
            for (const id of Object.keys(r)) {
              // En chemin, on n'est dans la pièce de personne : on est dans
              // l'escalier, et l'on n'y partage rien. Un joueur ne le voit
              // donc pas — il ne le croise pas.
              //
              // LA RÉGIE, SI. Elle ne partage aucune pièce avec personne :
              // elle regarde le château, et un homme qui traverse est
              // justement ce qu'elle vient voir. On lui rend le tracé entier
              // (`route`), le rang de la salle franchie et la fraction du pas
              // en cours — de quoi le poser entre deux portes. Il reste hors
              // de `avec` et son `ici` reste faux : il n'est chez personne.
              if (r[id].etat === "en-chemin") {
                if (!enRegie) continue;
                presence[id] = {
                  salle: r[id].salle, lieu: null,
                  marche: {
                    de: r[id].de || null, vers: r[id].vers || null,
                    vers_lieu: r[id].vers_lieu || null,
                    prochaine: r[id].prochaine || null,
                    route: r[id].route || [], franchi: r[id].franchi || 0,
                    pas: r[id].pas || 0, arrive_dans: r[id].arrive_dans || 0,
                  },
                };
                continue;
              }
              presence[id] = { salle: r[id].salle, lieu: r[id].lieu };
            }
          }
        } catch (e) {}
        // ET L'EXCEPTION REPREND LE DESSUS QUAND LE CALCUL NE SAIT PAS. Le
        // résolu ne connaît que les salles de la topologie du château : un
        // joueur posé par une scène dans un endroit qui n'y figure pas — une
        // taverne du bourg, un comptoir de change — en sort ABSENT, et il
        // passait alors pour n'être nulle part. Or une pièce constatée par une
        // scène est plus vraie qu'un calcul qui ne sait pas la placer : c'est
        // la règle de tout le fichier, « l'item poussé fait foi ».
        try {
          const brut = lire("presence.json").presence || {};
          for (const id of Object.keys(brut)) {
            if (!presence[id] && brut[id] && brut[id].salle) {
              presence[id] = { salle: brut[id].salle, lieu: brut[id].lieu };
              if (!connus.includes(id)) connus.push(id);
            }
          }
        } catch (e) {}
        // LA RÉGIE SE TIENT QUELQUE PART, et c'est elle qui le dit. Son
        // entrée de `etat/joueurs.json` porte `salle` et `lieu` : elle n'a
        // pas de corps dans `presence.json` — rien ne l'y met, rien ne l'en
        // sort —, mais elle a un poste d'observation, et le plan s'ouvre là.
        // Sans cette déclaration, elle retombe sur l'épaule du principal.
        let mien = moi && presence[moi];
        if (enRegie && siege.salle) mien = { salle: siege.salle, lieu: siege.lieu || "" };
        // Sans entrée pour le regardeur, on ne sait pas où il est : on ne dit
        // rien plutôt que de nommer une pièce au hasard. `connue: false` dit au
        // navigateur de s'en tenir à ce que le flux lui montre, comme avant.
        if (!mien) return envoyer(res, 200, JSON.stringify({ connue: false, avec: [] }));
        const meme = (a, b) => (a.salle && b.salle)
          ? a.salle === b.salle : (a.lieu || "") === (b.lieu || "");
        const noms = {};
        // le titre vient avec : c'est lui qui dit l'office, et le décor en
        // tire le signe qu'il pose sur chaque tache (voir taches.js)
        const titres = {};
        try {
          lire("personnages.json").forEach((p) => {
            noms[p.id] = p.nom;
            if (p.titre) titres[p.id] = p.titre;
          });
        } catch (e) {}
        const avec = Object.keys(presence)
          .filter((id) => id !== moi && !presence[id].marche
            && meme(presence[id], mien))
          .map((id) => ({ id, nom: noms[id] || id }));
        // `connus` : les gens dont la présence est tenue. Le navigateur en a
        // besoin pour distinguer « ailleurs » de « pas suivi » — un pêcheur de
        // passage n'est dans aucun fichier et garde son visage. Cela ne dit
        // toujours pas OÙ sont les autres : seulement qu'ils ne sont pas ici,
        // ce que le regardeur voit de ses yeux.
        // `places` : la maisonnée du château où l'on se tient, salle par
        // salle — de quoi poser un visage sur le plan. Ce n'est pas une
        // trahison du brouillard : ce sont ses propres gens, dans ses propres
        // murs, dont l'office dit l'endroit. Les personnages des AUTRES
        // joueurs en restent exclus tant qu'ils ne sont pas sous vos yeux :
        // savoir où se tient sa maîtresse de la voix ne se lit pas sur un plan.
        const autresJoueurs = new Set((roster() || [])
          .map((s) => s.personnage_id).filter((id) => id && id !== moi));
        const places = {};
        Object.keys(presence).forEach((id) => {
          // La régie voit aussi les autres joueurs, où qu'ils soient : c'est
          // le seul siège à qui l'on ne cache rien, et c'est sa définition.
          if (!enRegie && autresJoueurs.has(id) && !meme(presence[id], mien)) return;
          places[id] = {
            nom: noms[id] || id,
            titre: titres[id] || "",
            salle: presence[id].salle || null,
            lieu: presence[id].lieu || null,
            // un homme en marche n'est chez personne, pas même chez celui
            // dont il vient de franchir la porte
            ici: !presence[id].marche && meme(presence[id], mien),
            marche: presence[id].marche || null,
          };
        });
        return envoyer(res, 200, JSON.stringify({
          connue: true, salle: mien.salle || null, lieu: mien.lieu || null, avec,
          places,
          connus: connus.length ? connus : Object.keys(presence) }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ connue: false, avec: [] }));
      }
    }
  }
  return false;
}

module.exports = traiter;
