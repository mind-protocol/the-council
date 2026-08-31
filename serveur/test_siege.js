// LE TRI PAR `pour` — la garantie du brouillard à deux joueurs, et le seul
// endroit du serveur où un bug rend visible à un siège ce qu'un autre a
// entendu. Rien ne le couvrait : c'est la dette que le découpage a laissée
// derrière lui (voir serveur/CLAUDE.md).
//
// Trois sièges, un flux de dix items dont six portent une audience, et l'on
// vérifie que chacun reçoit EXACTEMENT ce qu'il doit — pas « au moins », pas
// « pas trop » : la liste, dans l'ordre. Une fuite se voit alors comme un
// item de plus, et une amputation comme un item de moins.
//
// Les deux moitiés sont testées, parce qu'elles se ferment l'une l'autre :
//   — la LECTURE (`GET /scene`), qui trie ce qui descend jusqu'à la machine ;
//   — l'ÉCRITURE (`POST /action`), qui estampe la parole du joueur de
//     l'audience de sa scène. Une lecture juste sur une écriture muette
//     laisserait la parole de la reine partir chez tout le monde.
const assert = require("assert");
const childProcess = require("child_process");
const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");

function ecrire(fichier, valeur) {
  fs.mkdirSync(path.dirname(fichier), { recursive: true });
  fs.writeFileSync(fichier, JSON.stringify(valeur, null, 1), "utf-8");
}

function portLibre() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.once("error", reject);
    s.listen(0, "127.0.0.1", () => {
      const port = s.address().port;
      s.close(() => resolve(port));
    });
  });
}

// Le jeton passe par le cookie, comme dans le navigateur après la première
// visite : c'est le chemin que le jeu emprunte réellement.
function demander(port, chemin, jeton) {
  return new Promise((resolve, reject) => {
    const req = http.request({ hostname: "127.0.0.1", port, path: chemin,
      method: "GET", headers: jeton ? { cookie: "jeton=" + jeton } : {} }, (res) => {
      let rendu = "";
      res.on("data", (c) => { rendu += c; });
      res.on("end", () => resolve({ status: res.statusCode, corps: JSON.parse(rendu) }));
    });
    req.once("error", reject);
    req.end();
  });
}

function poster(port, chemin, corps, jeton) {
  return new Promise((resolve, reject) => {
    const texte = JSON.stringify(corps);
    const entetes = { "content-type": "application/json",
      "content-length": Buffer.byteLength(texte) };
    if (jeton) entetes.cookie = "jeton=" + jeton;
    const req = http.request({ hostname: "127.0.0.1", port, path: chemin,
      method: "POST", headers: entetes }, (res) => {
      let rendu = "";
      res.on("data", (c) => { rendu += c; });
      res.on("end", () => resolve({ status: res.statusCode, corps: JSON.parse(rendu) }));
    });
    req.once("error", reject);
    req.end(texte);
  });
}

async function attendreServeur(proc) {
  return new Promise((resolve, reject) => {
    const delai = setTimeout(() => reject(new Error("serveur de test muet")), 10000);
    let sortie = "";
    proc.stdout.on("data", (c) => {
      sortie += c.toString();
      if (sortie.includes("Le Conseil écoute")) { clearTimeout(delai); resolve(); }
    });
    proc.stderr.on("data", (c) => { sortie += c.toString(); });
    proc.once("exit", (code) => {
      clearTimeout(delai);
      reject(new Error("serveur arrêté avant le test (" + code + ") : " + sortie));
    });
  });
}

const textes = (r) => r.corps.items.map((it) => it.texte);

(async () => {
  const racine = fs.mkdtempSync(path.join(os.tmpdir(), "conseil-siege-"));
  const etat = path.join(racine, "etat");

  // `depuis` est la ligne où chacun s'est assis à la table. Le seuil du
  // verrou de lecture en découle : ici 4, la ligne du dernier arrivé.
  ecrire(path.join(etat, "joueurs.json"), [
    { jeton: "jr", personnage_id: "reine", nom: "La reine",
      role: "principal", occupe: true, depuis: 2 },
    { jeton: "jv", personnage_id: "voix", nom: "La voix",
      role: "second", occupe: true, depuis: 4 },
    { jeton: "jc", personnage_id: "corneille", nom: "Corneille", regie: true },
  ]);

  // Dix items. Les indices comptent : ils sont l'argument du test.
  const flux = [
    { type: "recit", texte: "0 avant tout le monde" },              // ère mono-joueur
    { type: "recit", texte: "1 avant tout le monde" },              // ère mono-joueur
    { type: "recit", texte: "2 la reine descend au quai" },         // reine seule (2 < 4)
    { type: "replique", locuteur_id: "gerardys", texte: "3 pour la reine", pour: "reine" },
    { type: "effacer", texte: "4 la voix ouvre sa scène", pour: "voix" },
    { type: "replique", locuteur_id: "marna", texte: "5 messe basse",
      pour: ["reine", "voix"] },
    { type: "recit", texte: "6 sans audience, APRÈS le seuil" },    // personne
    { type: "replique", locuteur_id: "gerardys", texte: "7 pour la reine", pour: "reine" },
    { type: "replique", locuteur_id: "marlo", texte: "8 pour la voix", pour: "voix" },
    { type: "recit", texte: "9 sans audience, APRÈS le seuil" },    // personne
  ];
  fs.mkdirSync(etat, { recursive: true });
  // Un ancien dossier mj-* ne doit plus suffire a fabriquer un siege.
  fs.mkdirSync(path.join(racine, "chambres", "mj-sombreval"), { recursive: true });
  fs.writeFileSync(path.join(etat, "flux.jsonl"),
    flux.map((it) => JSON.stringify(it)).join("\n") + "\n", "utf-8");

  // Deux fronts qui divergent de six heures : au-delà du seuil, chacun doit
  // l'apprendre, sinon une scène commune devient impossible sans que personne
  // ne sache pourquoi. C'est aussi ce qui exerce la dernière ligne d'`ecartDe`
  // — celle qui lit le seuil, et qu'aucune requête ordinaire n'atteint.
  ecrire(path.join(etat, "horloges.json"), {
    reine: { annee: 129, lune: 4, jour: 3, minute: 600 },
    voix: { annee: 129, lune: 4, jour: 3, minute: 960 },
  });

  const port = await portLibre();
  const serveur = childProcess.spawn(process.execPath,
    [path.join(__dirname, "serveur.js"), String(port)], {
      cwd: path.join(__dirname, ".."),
      env: Object.assign({}, process.env, { CONSEIL_RACINE: racine,
        VOIX_API: "0", CONSEIL_SANS_REVEIL: "1" }),
      stdio: ["ignore", "pipe", "pipe"],
    });
  try {
    await attendreServeur(serveur);

    const identite = await demander(port, "/moi", "jr");
    assert.ok(!Object.prototype.hasOwnProperty.call(identite.corps, "arbitres"),
      "/moi expose encore les anciens arbitres geographiques");
    const ancienMj = await demander(port, "/bascule?vers=mj-sombreval", "jr");
    assert.strictEqual(ancienMj.status, 404,
      "un dossier mj-* permet encore de fabriquer un siege");

    // ---- 1. la lecture : chacun reçoit exactement le sien ------------------
    assert.deepStrictEqual(textes(await demander(port, "/scene", "jr")), [
      "2 la reine descend au quai",
      "3 pour la reine",
      "5 messe basse",
      "7 pour la reine",
    ], "la reine ne reçoit pas exactement sa scène");

    assert.deepStrictEqual(textes(await demander(port, "/scene", "jv")), [
      "4 la voix ouvre sa scène",
      "5 messe basse",
      "8 pour la voix",
    ], "la voix ne reçoit pas exactement sa scène");

    // LE VERROU PAR EN BAS : passé la ligne du dernier arrivé, un item sans
    // `pour` n'est plus public — il ne part chez PERSONNE. C'est ce qui fait
    // qu'une plume qui oublierait l'audience ne diffuse pas, au lieu de
    // diffuser à tout le monde.
    for (const jeton of ["jr", "jv"]) {
      const vus = textes(await demander(port, "/scene", jeton));
      assert.ok(!vus.some((t) => t.includes("sans audience")),
        "un item sans audience écrit après le seuil est parti chez " + jeton);
      assert.ok(!vus.some((t) => t.startsWith("0 ") || t.startsWith("1 ")),
        "l'histoire d'avant son arrivée est descendue chez " + jeton);
    }

    // La régie voit tout : elle n'est pas un joueur, et un fil amputé ne lui
    // servirait à rien.
    const regie = await demander(port, "/scene", "jc");
    assert.strictEqual(regie.corps.items.length, 10, "la régie ne voit pas tout le fil");

    // Sans jeton, on n'est personne — et personne ne lit la partie.
    const inconnu = await demander(port, "/scene", null);
    assert.deepStrictEqual(inconnu.corps.items, [], "un inconnu a reçu du fil");

    // L'ÉCART DE FRONT, servi avec la scène : six heures de retard sur
    // l'autre, et le signe doit le dire. La reine devance de −360 minutes.
    const front = await demander(port, "/scene", "jr");
    assert.strictEqual(front.corps.ecart, -360,
      "l'écart de front n'est pas rendu : une scène commune deviendrait impossible sans le savoir");

    // ---- 2. l'écriture : la parole part avec son audience ------------------
    const dit = await poster(port, "/action",
      { type: "libre", mode: "dire", texte: "Qu'on ferme la porte de mer." }, "jr");
    assert.strictEqual(dit.status, 200);

    const lignes = fs.readFileSync(path.join(etat, "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
    const dernier = lignes[lignes.length - 1];
    assert.strictEqual(dernier.type, "vous");
    assert.strictEqual(dernier.pour, "reine",
      "la parole de la reine est partie sans audience : elle sera lue par l'autre camp");

    // Le tour complet : ce qu'elle vient de dire est chez elle, et nulle part
    // ailleurs. C'est l'assertion qui vaut les deux précédentes réunies.
    assert.ok(textes(await demander(port, "/scene", "jr"))
      .includes("Qu'on ferme la porte de mer."), "la reine ne se relit pas");
    assert.ok(!textes(await demander(port, "/scene", "jv"))
      .includes("Qu'on ferme la porte de mer."), "FUITE : la voix entend la reine");

    // Hors fiction — une question ne part qu'à celui qui l'a posée, quelle
    // que soit la scène ouverte.
    await poster(port, "/action",
      { type: "libre", mode: "question", texte: "Qui tient la roukerie ?" }, "jv");
    const apres = fs.readFileSync(path.join(etat, "flux.jsonl"), "utf-8")
      .split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
    const question = apres[apres.length - 1];
    assert.strictEqual(question.type, "question");
    assert.strictEqual(question.pour, "voix", "une question hors fiction a fuité");

    console.log("tri par `pour` (lecture et écriture): OK");
  } finally {
    serveur.kill();
    if (serveur.exitCode === null)
      await new Promise((resolve) => serveur.once("exit", resolve));
    fs.rmSync(racine, { recursive: true, force: true,
      maxRetries: 10, retryDelay: 100 });
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
