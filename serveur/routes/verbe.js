// POST /verbe — les trois verbes de l'habitant depuis le front (habitant.md §3).
// {de, verbe: tenter|faire|demander|dire, texte, a?} → parloir en SYNCHRONE,
// le verdict de l'arbitre revient dans la réponse HTTP — le même retour de
// commande que lit un homme dépêché, servi au joueur qui incarne.
//
// `a` est optionnel : sans lui, l'arbitre est `mj` (la zone du joueur). Le
// front qui incarne un homme d'une autre ville passera son `mj-<ville>`.
// Timeout large (le call réveille un vrai `claude -p`, 1 à 3 minutes au
// premier réveil d'une zone) — la page doit attendre, c'est un CALL.
const path = require("path");
const { execFile } = require("child_process");
const { RACINE } = require("../http");
const { envoyer } = require("../http");

const VERBES = { tenter: "--tenter", faire: "--faire",
                 demander: "--demander", dire: "--dire",
                 // PENSER : un reveil de soi (cast) — le verdict HTTP est
                 // juste l'accuse « il y pense », la suite vit dans sa chambre.
                 penser: "--penser" };

function traiter(req, res, url) {
  if (req.method === "POST" && url === "/verbe") {
    let corps = "";
    req.on("data", (c) => (corps += c));
    req.on("end", () => {
      let d;
      try { d = JSON.parse(corps); } catch (e) {
        return envoyer(res, 400, JSON.stringify({ ok: false, erreur: "JSON illisible" }));
      }
      const drapeau = VERBES[d.verbe];
      if (!drapeau || !d.de || !(d.texte || "").trim()) {
        return envoyer(res, 400, JSON.stringify(
          { ok: false, erreur: "il faut de, verbe (tenter|faire|demander|dire) et texte" }));
      }
      const args = [path.join(RACINE, "scripts", "parloir.py"), drapeau,
                    "--de", String(d.de), "--a", String(d.a || "mj"),
                    String(d.texte)];
      execFile(process.env.PYTHON || "python", args,
        { cwd: RACINE, timeout: 300000, maxBuffer: 4 * 1024 * 1024,
          windowsHide: true,
          env: Object.assign({}, process.env, { PYTHONIOENCODING: "utf-8" }) },
        (err, stdout, stderr) => {
          if (err && !(stdout || "").trim()) {
            return envoyer(res, 502, JSON.stringify(
              { ok: false, erreur: String((stderr || err.message || "")).slice(0, 800) }));
          }
          return envoyer(res, 200, JSON.stringify(
            { ok: true, verdict: String(stdout || "").trim() }));
        });
    });
    return;
  }
  return false;
}

module.exports = traiter;
