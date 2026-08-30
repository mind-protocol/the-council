// GET /calendrier — les bandes, les jours et les notes d'agenda d'un siège.
const fs = require("fs");
const path = require("path");
const { RACINE, dateDe, lireCroyance } = require("../contexte");
const { envoyer } = require("../http");
const { qui } = require("../siege");

function traiter(req, res, url) {
  if (req.method === "GET") {
    if (url === "/calendrier") {
      try {
        const siege = qui(req, url);
        const aujourdhui = dateDe(siege);
        const moi = (siege && siege.personnage_id) ||
          (() => { try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", "journal.json"), "utf-8")).personnage_joueur_id; } catch (e) { return null; } })();
        const p = new URLSearchParams(req.url.split("?")[1] || "");
        const devant = Math.min(30, Math.max(1, parseInt(p.get("jours"), 10) || 8));
        const derriere = 1; // la veille : ce qu'on a manqué se voit encore
        const lire = (f, d) => {
          try { return JSON.parse(fs.readFileSync(path.join(RACINE, "etat", f), "utf-8")); }
          catch (e) { return d; }
        };
        const jour = (d) => d ? ((d.annee || 0) * 12 + ((d.lune || 1) - 1)) * 30 + (d.jour || 0) : null;
        const noms = {};
        (lire("personnages.json", []) || []).forEach((x) => {
          if (x && x.id) noms[x.id] = String(x.nom || x.id).split(",")[0].trim();
        });
        const nommer = (id) => noms[id] || String(id || "").replace(/-/g, " ");

        const j0 = jour(aujourdhui);
        const dedans = (d) => {
          const n = jour(d);
          return n !== null && j0 !== null && n >= j0 - derriere && n <= j0 + devant;
        };
        const entrees = [];
        const entame = (t, n) => {
          const s = String(t || "").replace(/\s+/g, " ").trim();
          return s.length > n ? s.slice(0, n).replace(/\s\S*$/, "") + "…" : s;
        };
        // Un programme n'a pas toujours de `titre` : sa description en tient
        // lieu. On la coupe alors en deux — la tête sert de titre, la suite de
        // détail — au lieu de servir deux fois le même paragraphe.
        const coupe = (e) => {
          const desc = String(e.description || "").replace(/\s+/g, " ").trim();
          if (e.titre) return { titre: e.titre, detail: entame(desc, 240) };
          const tete = entame(desc, 88);
          const reste = desc.slice(tete.replace(/…$/, "").length).trim();
          return { titre: tete, detail: entame(reste, 240) };
        };

        // 1. Les événements où il figure — les rendez-vous, les remises, les
        // rapports promis. `resolu` reste visible sur la veille : un joueur
        // qui se rassoit doit voir ce qui vient de tomber, pas seulement ce
        // qui vient.
        (lire("evenements.json", []) || []).forEach((e) => {
          if (!e || !e.date_prevue || !dedans(e.date_prevue)) return;
          const acteurs = Array.isArray(e.acteurs) ? e.acteurs : [];
          if (!moi || (acteurs.indexOf(moi) < 0 && e.porteur !== moi)) return;
          const st = e.statut || "a-venir";
          if (st === "annule" || st === "devie") return;
          const autres = acteurs.filter((a) => a !== moi).map(nommer);
          const c = coupe(e);
          entrees.push({
            genre: autres.length ? "rendez-vous" : "echeance",
            id: e.id,
            date: e.date_prevue,
            minute: typeof e.date_prevue.minute === "number" ? e.date_prevue.minute : null,
            titre: c.titre,
            detail: c.detail,
            lieu: e.lieu_id || null,
            avec: autres,
            statut: st,
            tenu: st === "resolu",
          });
        });

        // 2. Le courrier qu'on attend — un pli est un rendez-vous avec une
        // date, tenu par un homme qui marche. `attendu_le` est l'heure dite.
        const plis = lire("plis.json", { plis: [] });
        ((plis && plis.plis) || []).forEach((x) => {
          if (!x || !x.attendu_le || !dedans(x.attendu_le)) return;
          const mien = x.pour === moi || x.de === moi;
          if (!mien) return;
          const enRoute = (x.etat || "en-route") === "en-route";
          entrees.push({
            genre: "pli",
            id: x.id,
            date: x.attendu_le,
            minute: typeof x.attendu_le.minute === "number" ? x.attendu_le.minute : null,
            titre: (x.pour === moi ? "Attendu de " + nommer(x.de) : "Doit atteindre " + nommer(x.pour)) +
              (x.canal ? " (" + x.canal + ")" : ""),
            detail: entame(x.porte, 200),
            lieu: x.vers || null,
            avec: [nommer(x.pour === moi ? x.de : x.pour)],
            statut: x.etat || "en-route",
            tenu: !enRoute,
          });
        });

        // 3. Ce qui court et qui a un terme — ses fils, ses desseins. Ni
        // l'un ni l'autre n'a d'heure : ils se posent en tête de journée.
        const fils = lireCroyance("fils.json", siege, null);
        ((fils && fils.fils) || []).forEach((f) => {
          if (!f || !f.echeance || !dedans(f.echeance)) return;
          if ((f.statut || "en-cours") !== "en-cours") return;
          entrees.push({
            genre: "fil", id: f.id, date: f.echeance, minute: null,
            titre: f.titre, detail: entame(f.detail, 200),
            lieu: null, avec: f.sur ? [nommer(f.sur)] : [],
            statut: f.mode === "delegue" ? "delegue" : "joue", tenu: false,
          });
        });
        const miens = lireCroyance("objectifs.json", siege, []);
        (Array.isArray(miens) ? miens : []).forEach((o) => {
          if (!o || !o.echeance || !dedans(o.echeance)) return;
          if ((o.statut || "en-cours") !== "en-cours") return;
          entrees.push({
            genre: "dessein", id: o.id, date: o.echeance, minute: null,
            titre: o.titre, detail: entame(o.description, 200),
            lieu: null, avec: [], statut: "en-cours", tenu: false,
          });
        });

        // 4. LE SQUELETTE DE LA JOURNÉE — sa routine, résolue comme le fait
        // presence.py : les bandes du modèle, @dortoir et @poste remplacés.
        // Ce n'est pas un rendez-vous, c'est le fond sur lequel les autres
        // se posent : une heure déjà fermée n'est pas une heure libre.
        let bandes = [];
        try {
          const r = lire("routines.json", {});
          const fiche = (r.gens || {})[moi] || null;
          const modele = fiche && (r.modeles || {})[fiche.modele];
          if (modele) {
            const dortoir = fiche.dortoir || modele.dortoir || null;
            const poste = fiche.poste || modele.poste || null;
            bandes = (modele.bandes || []).map((b) => {
              const jeton = b.salle === "@dortoir" ? dortoir : b.salle === "@poste" ? poste : null;
              return {
                de: b.de, a: b.a,
                salle: jeton ? jeton.salle : b.salle,
                lieu: b.lieu || (jeton ? jeton.lieu : null),
                ferme: b.ferme === true,
              };
            });
          }
        } catch (e) {}

        entrees.sort((a, b) => (jour(a.date) - jour(b.date)) ||
          ((a.minute === null ? -1 : a.minute) - (b.minute === null ? -1 : b.minute)));
        const jours = [];
        for (let k = -derriere; k <= devant; k++) {
          const n = j0 + k;
          const d = {
            annee: Math.floor(n / 360),
            lune: Math.floor((n % 360) / 30) + 1,
            jour: n % 30,
          };
          // le jour 0 d'une lune est le 30e de la précédente
          if (d.jour === 0) { d.jour = 30; d.lune -= 1; if (d.lune === 0) { d.lune = 12; d.annee -= 1; } }
          jours.push({
            date: d, ecart: k,
            entrees: entrees.filter((x) => jour(x.date) === n),
          });
        }
        // Ses mémos — ce que le joueur a lui-même écrit dans les cases.
        // Hors fiction : voir POST /agenda.
        let notes = [];
        try {
          const a = lireCroyance("agenda.json", siege, null);
          notes = (a && Array.isArray(a.notes) ? a.notes : []).filter((n) => n && dedans(n.date));
        } catch (e) {}
        return envoyer(res, 200, JSON.stringify({
          aujourdhui, moi, nom: moi ? nommer(moi) : null, bandes, jours, notes,
        }));
      } catch (e) {
        return envoyer(res, 200, JSON.stringify({ jours: [], aujourdhui: null, bandes: [] }));
      }
    }
  }
  return false;
}

module.exports = traiter;
