"use strict";
// Une variante du vrai moteur. stdout = resultat JSON ; stderr = progression.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { pathToFileURL } = require("node:url");
const args = process.argv.slice(2);
const option = (nom, defaut) => {
  const a = args.find(x => x.startsWith(`--${nom}=`));
  return a ? a.slice(nom.length + 3) : defaut;
};
const debut = performance.now();
const progres = (etape, details = {}) => process.stderr.write(JSON.stringify({
  etape, secondes_reelles: +((performance.now() - debut) / 1000).toFixed(2), ...details,
}) + "\n");
const empreinte = b => crypto.createHash("sha256").update(b).digest("hex");

async function main() {
  const effectif = Number(option("effectif", option("hommes", 1700)));
  const duree = Number(option("duree", 600));
  const variante = option("variante", args.includes("--sans-arbitre") ? "temoin" : "arbitre");
  if (!Number.isInteger(effectif) || effectif < 1 || !Number.isFinite(duree) || duree < 0.05
      || Math.abs(duree * 20 - Math.round(duree * 20)) > 1e-6
      || !["temoin", "arbitre"].includes(variante)) {
    throw new Error("Effectif entier positif, duree multiple de 0.05 s, variante temoin ou arbitre attendus.");
  }
  const source = path.resolve(option("source", path.join(__dirname, "fixture-dddf6c8-parent")));
  const modules = path.join(source, "ecrans", "modules");
  const serveur = option("serveur", "http://localhost:3129");
  const cache = option("donnees", null);
  const rejouerDonnees = args.includes("--relire-donnees");
  if (cache) fs.mkdirSync(cache, { recursive: true });
  const donnees = {};
  const erreursDonnees = [];
  globalThis.window = globalThis;
  window.CHEMIN_JOURNEE = pathToFileURL(path.join(modules, "monde", "journee.js")).href;
  globalThis.requestAnimationFrame = () => 0;
  globalThis.cancelAnimationFrame = () => {};
  globalThis.document = { addEventListener() {} };
  const vraiFetch = globalThis.fetch;
  globalThis.fetch = async (u, options) => {
    const url = new URL(u, serveur).href;
    const fichier = cache && path.join(cache, empreinte(url) + ".json");
    progres("chargement_donnees", { url });
    try {
      let corps, status, headers;
      if (rejouerDonnees) {
        const sauvegarde = JSON.parse(fs.readFileSync(fichier, "utf8"));
        ({ status, headers } = sauvegarde);
        corps = Buffer.from(sauvegarde.corps, "base64");
      } else {
        const r = await vraiFetch(url, { ...options, signal: AbortSignal.timeout(15000) });
        status = r.status;
        headers = Object.fromEntries(r.headers);
        corps = Buffer.from(await r.arrayBuffer());
        if (fichier) fs.writeFileSync(fichier, JSON.stringify({ url, status, headers, corps: corps.toString("base64") }));
      }
      donnees[url] = { status, sha256: empreinte(corps), octets: corps.length };
      if (status < 200 || status >= 300) throw new Error(`HTTP ${status} pour ${url}`);
      return new Response(corps, { status, headers });
    } catch (e) {
      erreursDonnees.push(`${url}: ${e.message}`);
      throw e;
    }
  };

  progres("chargement_code", { source, variante });
  const chaine = require(path.join(modules, "bataille", "moteur", "chaine.js")).fichiers("moteur");
  const compteurs = { appels_arbitre: 0, appels_ralliement: 0, decisions_ralliement: 0 };
  globalThis.__mesureRalliement = compteurs;
  for (const f of chaine) {
    let texte = fs.readFileSync(path.join(modules, f), "utf8");
    if (f === "bataille2d.js") {
      // Fenetres de lecture et compteurs seulement : aucune decision modifiee.
      const ancres = [
        ["  return { poser, preparer,", "  return { _observerEssai: () => ({hommes: S.hommes, temps: S.temps}), poser, preparer,"],
        ["  function rallier(h, dt) {", "  function rallier(h, dt) { globalThis.__mesureRalliement.appels_ralliement++;"],
        ["    if (h.conduit) { if (h.conduit !== \"ordre\") return true; }", "    globalThis.__mesureRalliement.decisions_ralliement++;\n    if (h.conduit) { if (h.conduit !== \"ordre\") return true; }"],
      ];
      for (const [avant, apres] of ancres) {
        if (texte.split(avant).length !== 2) throw new Error(`Ancre de mesure absente ou ambigue : ${avant}`);
        texte = texte.replace(avant, apres);
      }
    }
    (0, eval)(texte);
  }
  if (!window.Bataille2d || !window.QuiConduit) throw new Error("Moteur ou arbitre absent de la chaine.");
  if (variante === "temoin") delete window.QuiConduit;
  else {
    const pas = window.QuiConduit.pas;
    window.QuiConduit.pas = function (...a) { compteurs.appels_arbitre++; return pas.apply(this, a); };
  }
  const bataille = window.Bataille2d;
  await bataille.preparer("/monde");
  // Le moteur tolere certaines donnees absentes ; une comparaison ne le fait pas.
  if (erreursDonnees.length) throw new Error(erreursDonnees.join(" ; "));
  progres("installation_scenario");
  bataille.rejouer("La porte de la Gadoue", effectif);
  const initial = bataille._observerEssai();
  const initialHash = empreinte(JSON.stringify(initial.hommes));
  const effectifObserve = initial.hommes.length;
  if (!effectifObserve) throw new Error("Scenario sans soldats.");
  progres("simulation", { secondes_simulees: 0, effectif_observe: effectifObserve });
  let derniere = performance.now();
  for (let i = 0, n = Math.round(duree * 20); i < n; i++) {
    bataille.pas(0.05);
    if (performance.now() - derniere > 2000) {
      progres("simulation", { secondes_simulees: bataille._observerEssai().temps, pas: i + 1 });
      derniere = performance.now();
    }
  }
  const observation = bataille._observerEssai();
  const etat = bataille.etat();
  const faits = bataille.faits();
  const parType = {};
  for (const f of faits) parType[f.quoi] = (parType[f.quoi] || 0) + 1;
  const commandes = {};
  for (const h of observation.hommes) {
    if (h.etat === "mort" || h.tete) continue;
    const nom = h.conduit || "sans_arbitre";
    commandes[nom] = (commandes[nom] || 0) + 1;
  }
  const resultat = {
    version: "resultat-ralliement/1", variante, effectif_demande: effectif,
    effectif_observe: effectifObserve, duree_demandee_s: duree,
    duree_simulee_s: +observation.temps.toFixed(6), graine: 20161219,
    etat_initial_sha256: initialHash, donnees,
    duree_reelle_s: +((performance.now() - debut) / 1000).toFixed(3),
    ...compteurs, ralliements: parType.ralliement || 0,
    morts: etat.morts, blesses: etat.blesses, fuyards: etat.fuyards,
    commandes_des_soldats: commandes, faits_total: faits.length, faits_par_type: parType,
  };
  progres("termine", { secondes_simulees: resultat.duree_simulee_s });
  process.stdout.write(JSON.stringify(resultat, null, 2) + "\n");
}
main().catch(e => { progres("erreur", { message: e.stack || String(e) }); process.exitCode = 1; });
