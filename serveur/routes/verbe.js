// POST /verbe — les gestes d'un JOUEUR depuis le front.
// {de, verbe: tenter|faire|demander|dire, texte} → parloir en SYNCHRONE,
// le verdict du MJ revient dans la réponse HTTP — le même retour de
// commande servi au joueur qui incarne.
//
// Le marqueur --joueur est la frontière : une session PNJ qui invoque le
// parloir sans lui ne peut plus demander de verdict au MJ.
// Timeout large : la page doit attendre le verdict, c'est un CALL.
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
                    "--joueur", "--de", String(d.de), "--a", "mj",
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
