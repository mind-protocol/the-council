// POST /piece — la pièce jouée depuis le banc d'essai.
const { bibliotheque } = require("../plan"); // LA PORTE serveur du plan
const { RACINE } = require("../http");
const { envoyer } = require("../http");

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/piece") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      try {
        const d = JSON.parse(corps);
        const sessionLivres = bibliotheque.ouvrir(RACINE);
        const livres = sessionLivres.livres;
        const nu = (t) => String(t == null ? "" : t).replace(/\*\*/g, "")
          .replace(/\s+/g, " ").trim();
        // les emblemes sortent du nom de colonne : au-dela de U+2000 il n'y a
        // plus de lettre francaise, seulement des signes et des paires hautes
        const sansEmoji = (t) => nu(t).replace(/[\u2000-\uFFFF]/g, "").trim();
        const GENRES = { etat: /états? cibles?/i, verrou: /verrous?/i,
                         clef: /clefs?/i, action: /actions?/i };
        const REGISTRE = { etat: "plan-etats-cibles", verrou: "plan-verrous",
                           clef: "plan-clefs", action: "plan-actions" };
        const PARENT = { etat: /sert/i, verrou: /bloque/i, clef: /ouvre/i,
                         action: /réalise|realise/i };
        if (!GENRES[d.genre]) throw new Error("forme inconnue : " + d.genre);
        if (!nu(d.texte)) throw new Error("une pièce sans nom ne se porte pas");
        if (d.genre !== "etat" && !/^\d{3,6}$/.test(String(d.parent || "").trim()))
          throw new Error("il faut le numéro de ce qu'elle sert");

        const aff = livres.find((b) => b.id === d.affaire);
        if (!aff || !Array.isArray(aff.tables)) throw new Error("affaire inconnue");

        // la plage, prise à la ligne LA PLAGE de l'ouverture
        let plage = 0;
        (aff.tables[0].lignes || []).forEach((l) => {
          const c = (l.cellules || []).map(nu);
          if (/LA PLAGE/i.test(sansEmoji(c[0] || ""))) {
            const m = (c[1] || "").match(/\d{3,6}/);
            if (m) plage = +m[0];
          }
        });
        // repli sur le sous-titre : un cahier vierge porte sa plage là, et la
        // case de l'ouverture n'est remplie qu'à l'ouverture de l'affaire.
        if (!plage) {
          const m = String(aff.sous_titre || "").match(/[Pp]lage\s+(\d{3,6})/);
          if (m) plage = +m[1];
        }
        if (!plage) throw new Error("cette affaire n'a pas de plage : ni dans " +
          "son ouverture, ni dans son sous-titre");

        // tout ce qui est déjà pris, dans l'affaire comme dans les registres
        const pris = new Set();
        livres.forEach((b) => (b.tables || [{ colonnes: b.colonnes, lignes: b.lignes }])
          .forEach((t) => (t.lignes || []).forEach((l) => {
            const c = (l.cellules || l || []).map(nu);
            const m = (c[0] || "").match(/^\d{3,6}$/);
            if (m) pris.add(+m[0]);
          })));

        let num = 0;
        if (d.genre === "etat") {
          for (let n = plage; n < plage + 1000; n += 100) if (!pris.has(n)) { num = n; break; }
        } else {
          const base = Math.floor(+d.parent / 100) * 100;
          const bornes = { verrou: [1, 9], clef: [10, 19], action: [20, 99] }[d.genre];
          for (let i = bornes[0]; i <= bornes[1]; i++)
            if (!pris.has(base + i)) { num = base + i; break; }
        }
        if (!num) throw new Error("plus de numéro libre pour cette forme");

        // la ligne, remplie par NOM de colonne : les tableaux n'ont pas tous
        // les mêmes, et un remplissage par rang écrirait de travers
        const valeurs = [
          [/^n°$/i, "**" + num + "**"],
          [PARENT[d.genre], d.parent ? String(d.parent) : "—"],
          [/office/i, nu(d.office) || (d.genre === "action" ? "**SANS OFFICE**" : "")],
          [/moyens/i, nu(d.moyens)],
          [/affaire/i, nu(aff.titre)],
        ];
        const ligne = (cols) => cols.map((c, i) => {
          if (i === 1) return nu(d.texte);
          const t = sansEmoji(c);
          const v = valeurs.find((x) => x[0].test(t));
          return v ? v[1] : "";
        });

        const dans = (livre) => {
          const t = (livre.tables || []).find((x) => GENRES[d.genre].test(sansEmoji(x.titre)));
          if (!t) return false;
          t.lignes = (t.lignes || []).filter((l) =>
            (l.cellules || []).some((c) => nu(c)));   // on chasse les lignes vides du patron
          t.lignes.push({ cellules: ligne(t.colonnes || []) });
          return true;
        };
        if (!dans(aff)) throw new Error("l'affaire n'a pas de tableau pour cette forme");
        const reg = livres.find((b) => b.id === REGISTRE[d.genre]);
        if (reg) {
          reg.lignes = reg.lignes || [];
          reg.lignes.push({ cellules: ligne(reg.colonnes || []) });
        }
        sessionLivres.sauver();
        return envoyer(res, 200, JSON.stringify({ num: String(num), affaire: nu(aff.titre) }));
      } catch (e) {
        return envoyer(res, 400, JSON.stringify({ erreur: String(e.message || e) }));
      }
    });
    return;
  }

  // Basculer un fil : le mode s'écrit tout de suite dans `fils.json` (sinon le
  // rail mentirait au rechargement), ET l'intention tombe dans l'inbox du
  // siège. Le clic ne JOUE rien — il dit ce que le joueur veut ; c'est au MJ
  // d'en tirer le mandat écrit et la scène qui va avec.
  return false;
}

module.exports = traiter;
