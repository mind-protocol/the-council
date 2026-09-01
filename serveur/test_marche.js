// LA MARCHE — les invariants du moteur sorti dans `domaine/marche.js`.
//
// Ce qu'on tient ici n'est pas un chiffre en dur : le bâti de Port-Réal se
// régénère (`scripts/monde/…`), et une distance gravée dans un test se met à
// mentir au premier relief refait. On tient donc ce qui ne doit JAMAIS bouger,
// quel que soit le monde engendré :
//
//   1. le même couple de points rend le même itinéraire — au mètre, deux fois
//      de suite. C'est la garantie que le document du chantier réclame
//      nommément, parce que des `cout` d'étape et des délais de course se
//      calent dessus ;
//   2. la polyligne part du point cliqué et finit au but, et sa longueur ne
//      descend jamais sous la ligne droite — un chemin par les rues est plus
//      long qu'un vol d'oiseau, jamais plus court ;
//   3. LES SECONDES NE SE PERDENT PAS. Quatre tronçons à 0,3 minute font
//      1,2 minute : l'horloge paie UNE minute entière et garde le reste. Sans
//      ce report, une balade d'un kilomètre coûterait zéro — cinquante fois
//      un arrondi à zéro ;
//   4. la position est écrite dans `corps.json`, le bandeau dans `presence`,
//      et le sac ne tombe dans l'inbox du siège qu'à l'arrivée : c'est le
//      routeur de message qu'on protège d'un réveil par tronçon.
//
// Le monde 3D pèse plus d'un gigaoctet : on le monte en JONCTION dans une
// racine temporaire au lieu de le copier, et l'état y est réduit à ce que la
// marche touche. Si le bâti n'a pas été engendré, le test se déclare sans
// objet plutôt que d'échouer sur une absence qui n'est pas une régression.
const assert = require("assert");
const cp = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");

const DEPOT = path.join(__dirname, "..");
const JETON = "jm";

if (!fs.existsSync(path.join(DEPOT, "monde", "portreal.bati.json"))) {
  console.log("marche: sans objet (monde/portreal.* non engendré)");
  process.exit(0);
}

function racineDEssai() {
  const r = fs.mkdtempSync(path.join(os.tmpdir(), "conseil-marche-"));
  for (const d of ["monde", "ecrans", "scripts"])
    cp.execSync('cmd /c mklink /J "' + path.join(r, d) + '" "' + path.join(DEPOT, d) + '"',
      { stdio: "ignore" });
  const etat = path.join(r, "etat");
  fs.mkdirSync(etat);
  const ecrire = (f, o) => fs.writeFileSync(path.join(etat, f), JSON.stringify(o, null, 1), "utf-8");
  ecrire("joueurs.json", [{ jeton: JETON, personnage_id: "marcheur",
                            nom: "Le marcheur", occupe: true, depuis: 0 }]);
  ecrire("monde.json", { date: { annee: 129, lune: 4, jour: 3, minute: 600 } });
  ecrire("horloges.json", { marcheur: { annee: 129, lune: 4, jour: 3, minute: 600 } });
  ecrire("corps.json", { liens: {}, affectations: {} });
  ecrire("presence.json", { presence: {} });
  fs.writeFileSync(path.join(etat, "flux.jsonl"), "", "utf-8");
  return r;
}

const portLibre = () => new Promise((ok, ko) => {
  const s = net.createServer();
  s.once("error", ko);
  s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => ok(p)); });
});

function appeler(port, chemin, methode, corps) {
  return new Promise((ok, ko) => {
    const t = corps ? JSON.stringify(corps) : null;
    const e = { cookie: "jeton=" + JETON };
    if (t) { e["content-type"] = "application/json"; e["content-length"] = Buffer.byteLength(t); }
    const r = http.request({ hostname: "127.0.0.1", port, path: chemin,
      method: methode, headers: e }, (res) => {
      let rendu = "";
      res.on("data", (c) => { rendu += c; });
      res.on("end", () => ok({ status: res.statusCode, texte: rendu }));
    });
    r.once("error", ko);
    r.end(t || undefined);
  });
}

function attendre(proc) {
  return new Promise((ok, ko) => {
    const t = setTimeout(() => ko(new Error("serveur de test muet")), 20000);
    let sortie = "";
    proc.stdout.on("data", (c) => {
      sortie += c;
      if (sortie.includes("Le Conseil écoute")) { clearTimeout(t); ok(); }
    });
    proc.stderr.on("data", (c) => { sortie += c; });
    proc.once("exit", (code) => { clearTimeout(t); ko(new Error("arrêté (" + code + ") " + sortie)); });
  });
}

(async () => {
  const racine = racineDEssai();
  const port = await portLibre();
  const serveur = cp.spawn(process.execPath,
    [path.join(__dirname, "serveur.js"), String(port)], {
      cwd: DEPOT, stdio: ["ignore", "pipe", "pipe"],
      env: Object.assign({}, process.env, { CONSEIL_RACINE: racine, VOIX_API: "0" }),
    });
  const etat = (f) => JSON.parse(fs.readFileSync(path.join(racine, "etat", f), "utf-8"));
  try {
    await attendre(serveur);

    // ---- 1 et 2. l'itinéraire, au mètre et deux fois ------------------------
    const q = "/chemin?lieu=port-real&de=1000,1000&vers=1400,1300";
    const un = await appeler(port, q, "GET");
    const deux = await appeler(port, q, "GET");
    assert.strictEqual(un.status, 200);
    assert.strictEqual(un.texte, deux.texte,
      "le même couple de points rend deux itinéraires différents");
    const chemin = JSON.parse(un.texte);
    if (chemin.chemin) {
      const pts = chemin.chemin.points || chemin.chemin;
      assert.ok(Array.isArray(pts) && pts.length >= 2, "itinéraire sans polyligne");
      assert.deepStrictEqual(pts[0].map(Math.round), [1000, 1000],
        "la polyligne ne part pas du point cliqué");
      let m = 0;
      for (let i = 1; i < pts.length; i++)
        m += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      assert.ok(m >= Math.hypot(400, 300) - 1,
        "l'itinéraire par les rues est plus court que la ligne droite : " + Math.round(m));
    }

    // ---- 3. les secondes ne se perdent pas ---------------------------------
    // Quatre tronçons à 0,3 minute : 1,2 minute marchée, UNE payée.
    const depart = etat("horloges.json").marcheur.minute;
    for (let i = 0; i < 4; i++) {
      const r = await appeler(port, "/marche", "POST",
        { lieu: "port-real", x: 1000 + i * 20, y: 1000 + i * 15, minutes: 0.3, metres: 25 });
      assert.strictEqual(r.status, 200, "un tronçon de marche a échoué : " + r.texte);
    }
    assert.strictEqual(etat("horloges.json").marcheur.minute, depart + 1,
      "l'arrondi mange les minutes : 4 × 0,3 doit payer 1 minute, et une seule");

    // ---- 4. ce que la marche laisse derrière elle ---------------------------
    const aff = etat("corps.json").affectations["personnage:marcheur"];
    assert.ok(aff, "la marche n'a pas écrit la position du marcheur");
    assert.deepStrictEqual(aff.xyz, [1060, 1045, 0], "la position écrite n'est pas la dernière");
    assert.strictEqual(aff.monde, "portreal",
      "l'affectation porte l'id du lieu au lieu du préfixe du bâti");
    assert.strictEqual(aff.note, "en marche");
    const dit = etat("presence.json").presence.marcheur.lieu;
    assert.ok(dit && /pas|ville/.test(dit), "le bandeau ne dit pas où l'on est : " + dit);

    const inbox = path.join(racine, "etat", "inbox", "marcheur");
    assert.ok(!fs.existsSync(inbox) || !fs.readdirSync(inbox).length,
      "le sac est tombé dans l'inbox avant l'arrivée : le MJ est réveillé par tronçon");

    const fin = await appeler(port, "/marche", "POST",
      { lieu: "port-real", x: 1080, y: 1060, minutes: 0.3, metres: 25, fin: true });
    assert.strictEqual(fin.status, 200);
    const sacs = fs.readdirSync(inbox);
    assert.strictEqual(sacs.length, 1, "l'arrivée doit déposer un sac, et un seul");
    const sac = JSON.parse(fs.readFileSync(path.join(inbox, sacs[0]), "utf-8"));
    assert.strictEqual(sac.fini, true, "le sac déposé n'est pas marqué fini");
    assert.strictEqual(sac.joueur_id, "marcheur");
    assert.strictEqual(sac.pas.length, 5, "le sac a perdu des pas en route");
    assert.ok(!("_session" in sac) && !("_touche_a" in sac),
      "la tuyauterie du tampon est partie chez le MJ");

    console.log("marche (itinéraire, minutes, position, sac): OK");
  } finally {
    serveur.kill();
    setTimeout(() => {
      // LES JONCTIONS SE DÉFONT AVANT LE RESTE, ET PAR `rmdir` NU. Un
      // effacement récursif qui suivrait le lien viderait `monde/` — 1,2 Go du
      // dépôt — au lieu du dossier temporaire. `rmdirSync` retire le point de
      // montage sans jamais descendre dedans, et l'on refuse d'effacer la
      // racine tant qu'il en reste un.
      for (const d of ["monde", "ecrans", "scripts"])
        { try { fs.rmdirSync(path.join(racine, d)); } catch (e) {} }
      const reste = ["monde", "ecrans", "scripts"]
        .filter((d) => fs.existsSync(path.join(racine, d)));
      if (reste.length) return console.error("jonctions non défaites : " + reste.join(", ") +
        " — dossier laissé en place (" + racine + ")");
      try { fs.rmSync(racine, { recursive: true, force: true }); } catch (e) {}
    }, 300);
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
