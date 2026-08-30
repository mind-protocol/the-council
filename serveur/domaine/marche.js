// LA MARCHE — où l'on est, et ce qu'on croise en y allant. Sorti de sa route
// parce que c'est un moteur : il paie la montre, écrit la position, compose ce
// que l'homme longe et ce qu'il perçoit d'une bataille, et tient le sac de la
// balade en cours. Rien de tout cela n'est du transport.
//
// Les deux fonctions prennent le corps de la requête TEL QU'IL EST ARRIVÉ, en
// texte, et le parsent elles-mêmes : un corps illisible doit rendre la même
// erreur 500 qu'avant la coupe, et il la rendrait ailleurs si la route parsait.
// Elles rendent `{ code, corps }` — jamais `res`, qu'elles ne connaissent pas.
//
// VÉRIFIER APRÈS TOUTE RETOUCHE : une même paire de points doit rendre le même
// itinéraire AU MÈTRE qu'avant. Des `cout` d'étape et des délais de course se
// calent dessus (voir serveur/CLAUDE.md).
const fs = require("fs");
const path = require("path");
const croiser = require("../croiser");
const { RACINE } = require("../contexte");
const { DEBUG_MARCHE_AU_FIL, LIEU3D_DEFAUT, LIEUX3D, PLURIELS, SESSION_SERVEUR,
        _resteMarche, batiAutour, direGens, metier, repereProche } = require("../monde3d");

// POSER SON CORPS quelque part, sans marcher : le joueur qui se déplace d'un
// geste sur le plan. Une seule écriture, dans `corps.json`.
function poser(corpsBrut, siege) {
try {
  const p = JSON.parse(corpsBrut);
  const pid = siege && siege.personnage_id;
  const x = +p.x, y = +p.y;
  if (!pid) return { code: 200, corps: { ok: false, erreur: "sans siège" } };
  if (!isFinite(x) || !isFinite(y))
    return { code: 400, corps: { erreur: "x/y" } };
  const f = path.join(RACINE, "etat", "corps.json");
  let L = { liens: {}, affectations: {} };
  try { L = JSON.parse(fs.readFileSync(f, "utf-8")); } catch (e) {}
  L.affectations = L.affectations || {};
  const cle = "personnage:" + pid;
  // ON FUSIONNE au lieu de remplacer : l'entrée peut porter un `nom`,
  // une `note` ou un `visible` qu'on n'a aucune raison d'effacer parce
  // que quelqu'un a fait trois pas.
  const avant = L.affectations[cle] || {};
  L.affectations[cle] = Object.assign({}, avant, {
    xyz: [Math.round(x * 10) / 10, Math.round(y * 10) / 10, 0],
    // LE PRÉFIXE, PAS L'IDENTIFIANT DE LIEU. `affecter.py` et
    // `bati.py` cherchent `monde/<monde>.bati.json` : écrire
    // « port-real » leur fait chercher un fichier qui n'existe pas,
    // et l'affectation devient illisible pour tout ce qui la relit.
    // C'est la même prise que `/marche` deux cents lignes plus bas.
    monde: (LIEUX3D[p.lieu || LIEU3D_DEFAUT] || {}).prefixe ||
           p.lieu || LIEU3D_DEFAUT,
    note: p.note || avant.note || "en marche",
  });
  fs.writeFileSync(f, JSON.stringify(L, null, 2), "utf-8");
  return { code: 200, corps: { ok: true } };
} catch (e) {
  return { code: 500, corps: { erreur: String(e.message || e) } };
}
}

// UN TRONÇON DE MARCHE : la montre, la position, ce qu'on longe, le sac.
function marcher(corpsBrut, siege) {
try {
  const p = JSON.parse(corpsBrut);
  const pid = siege ? siege.personnage_id : null;
  const lieu = p.lieu || LIEU3D_DEFAUT;
  const x = +p.x, y = +p.y;
  if (!isFinite(x) || !isFinite(y))
    return { code: 400, corps: { erreur: "x/y" } };
  const minutes = Math.max(0, +p.minutes || 0);
  const fichier = (f) => path.join(RACINE, "etat", f);
  const lire = (f, d) => {
    try { return JSON.parse(fs.readFileSync(fichier(f), "utf-8")); }
    catch (e) { return d; }
  };
  const ecrire = (f, o) =>
    fs.writeFileSync(fichier(f), JSON.stringify(o, null, 2), "utf-8");

  // 1. LA MONTRE. Marcher coûte des minutes ; elles se paient sur
  // l'horloge du siège ET sur celle du monde, qui suit toujours la
  // plus avancée (voir « UNE SEULE NUIT, UNE SEULE HEURE »).
  const monde = lire("monde.json", null);
  const horloges = lire("horloges.json", {});
  const avancer = (d, min) => {
    if (!d) return d;
    let m = (d.minute || 0) + min;
    let j = d.jour || 1, l = d.lune || 1, a = d.annee || 0;
    while (m >= 1440) { m -= 1440; j += 1; }
    while (j > 30) { j -= 30; l += 1; }
    while (l > 12) { l -= 12; a += 1; }
    return { annee: a, lune: l, jour: j, minute: Math.round(m) };
  };
  // LES SECONDES NE SE PERDENT PAS. Vingt mètres coûtent un quart de
  // minute : arrondi à chaque tronçon, une balade d'un kilomètre ne
  // coûterait RIEN du tout — cinquante fois zéro. On garde donc le
  // reste en mémoire, siège par siège, et l'horloge n'avance que
  // lorsqu'une minute entière a été marchée. Ce reste n'est pas de
  // l'état : le perdre au redémarrage coûte moins d'une minute.
  let date = null;
  const du = minutes + (_resteMarche[pid || "?"] || 0);
  const entieres = Math.floor(du);
  _resteMarche[pid || "?"] = du - entieres;
  if (pid && entieres > 0) {
    horloges[pid] = avancer(horloges[pid] || (monde && monde.date), entieres);
    date = horloges[pid];
    ecrire("horloges.json", horloges);
  } else if (pid) {
    date = horloges[pid] || (monde && monde.date);
  }
  if (monde && entieres > 0) {
    const apres = avancer(monde.date, minutes);
    // le monde ne recule jamais : si l'autre siège est plus avancé,
    // c'est lui qui fait foi.
    const clef = (d) => ((d.annee * 12 + d.lune) * 30 + d.jour) * 1440 + d.minute;
    if (!date || clef(apres) > clef(date)) monde.date = apres;
    else monde.date = date;
    ecrire("monde.json", monde);
  }

  // 2. OÙ L'ON EST — en mètres, et en clair. Les mètres vont dans les
  // affectations (`corps.json`), qui sont le seul endroit du jeu où
  // une chose de la fiction a une adresse physique ; le clair va dans
  // `presence.lieu`, qui est ce que le bandeau affiche. On NE TOUCHE
  // PAS à `presence.salle` : les salles nommées sont la topologie de
  // `chemins.json`, et une rue de la ville n'en est pas une — écrire
  // un id inventé ferait mentir tout ce qui lit cette table.
  // Ce que la partie a déjà baptisé, par rang de bâtiment. Une seule
  // lecture de `corps.json` sert à ça et à l'écriture de la position.
  const corpsJson = lire("corps.json", { liens: {}, affectations: {} });
  corpsJson.affectations = corpsJson.affectations || {};
  const nommes = new Map();
  for (const cle in corpsJson.affectations) {
    const a = corpsJson.affectations[cle];
    // PAS DE NOM, PAS DE NOM — on ne se rabat SURTOUT pas sur la clef.
    // Une affectation sans `nom` rendait « devant
    // lieu:place-du-puits-culpucier », c'est-à-dire un identifiant nu
    // dans une phrase que le joueur lit au bandeau (elle part dans
    // `presence.lieu`) et que le MJ reçoit dans son sac. Sans nom, on
    // laisse le métier parler : « devant un puits » est vrai, lisible,
    // et n'invente rien. Le jour où quelqu'un baptise l'endroit
    // (`affecter.py --nom`), il reprend son nom tout seul.
    if (a && a.bat != null) nommes.set(a.bat, { cle, nom: a.nom || null });
  }
  const autour = batiAutour(lieu, x, y, 45, 4, nommes);
  const pres = repereProche(lieu, x, y);
  // Devant chez quelqu'un, on dit chez qui — pas ce que c'est.
  const devant = autour.connus[0] || autour.gros;
  // « de » S'ÉLIDE, et cette phrase-là est sous les yeux du joueur : elle
  // va dans `presence.lieu`, c'est-à-dire dans le bandeau, et dans le sac
  // que lit le MJ. Les repères portent leur article — « Le Donjon Rouge »,
  // « La porte de Fer » —, d'où « à 263 pas de La porte de Fer » tant
  // qu'on collait « de » devant sans regarder.
  // `les` AVANT `le` dans l'alternation : une regex essaie ses branches
  // de gauche à droite, et « le » mordait dans « Les casernes » — d'où
  // « du s casernes du guet ». C'est la faute qu'on ne voit qu'en
  // essayant les vrais noms de la table.
  const dePlace = (nom) => {
    const s = String(nom || "").trim();
    const m = s.match(/^(les|la|le|l')\s*/i);
    // Pas d'article du tout : « de » s'élide quand même devant voyelle.
    if (!m) return (/^[aeiouyàâéèêîïôöûü]/i.test(s) ? "d'" : "de ") + s;
    const reste = s.slice(m[0].length);
    const a = m[1].toLowerCase();
    return (a === "le" ? "du " : a === "les" ? "des " :
            a === "la" ? "de la " : "de l'") + reste;
  };
  const dit = (pres ? "À " + pres.a + " pas " + dePlace(pres.nom) : "Dans la ville") +
    (devant ? ", devant " + (devant.nom || metier(devant.usage)) : "");
  if (pid) {
    // Le MONDE d'une affectation est le préfixe du bâti engendré
    // (`portreal`), jamais l'id du lieu (`port-real`) : `affecter.py`
    // ouvre `monde/<monde>.bati.json`, et écrire l'id du lieu ici
    // faisait planter la liste des affectations sur un fichier absent.
    const pref = (LIEUX3D[lieu] && LIEUX3D[lieu].prefixe) || lieu;
    corpsJson.affectations["personnage:" + pid] = {
      xyz: [Math.round(x * 10) / 10, Math.round(y * 10) / 10, 0],
      monde: pref, note: p.fin ? "arrivé" : "en marche",
    };
    ecrire("corps.json", corpsJson);
    const presence = lire("presence.json", { presence: {} });
    presence.presence = presence.presence || {};
    const e = presence.presence[pid] || {};
    e.lieu = dit;
    if (date) e.date = date;
    presence.presence[pid] = e;
    ecrire("presence.json", presence);
  }

  // 3. CE QU'ON VIENT DE LONGER, pour le MJ.
  const pas = {
    x: Math.round(x), y: Math.round(y),
    metres: Math.round(+p.metres || 0), minutes: Math.round(minutes * 10) / 10,
    date, ou: dit, quartier: (autour.proches[0] || {}).quartier || null,
    // Chacun avec son RANG : c'est par lui que le MJ peut le baptiser
    // (`affecter.py --affecter lieu:<id> <bat> --nom "…"`), après quoi
    // il reviendra nommé dans toutes les balades.
    longe: autour.proches.map((b) =>
      (b.nom ? b.nom + " (" + metier(b.usage) + ", " : metier(b.usage) + " (") +
      b.a + " pas, bâtiment " + b.bat + ")"),
    connus: autour.connus.map((b) => ({ cle: b.cle, nom: b.nom, bat: b.bat, a: b.a })),
    // le tissu, en un mot : « et 14 maisons, 3 taudis »
    tissu: (autour.tissu || []).sort((p, q) => q[1] - p[1])
      .map(([u, n]) => n + " " + (n > 1 ? PLURIELS[u] || u : metier(u)))
      .join(", ") || null,
    marquant: autour.gros
      ? metier(autour.gros.usage) + ", " + autour.gros.aire + " m²" +
        (autour.gros.etages > 1 ? ", " + autour.gros.etages + " étages" : "")
      : null,
    // QUI ON CROISE — combien, et de quel métier, à trente mètres.
    // C'est la seule ligne du pas qui change d'une heure à l'autre :
    // les murs sont les mêmes à trois heures du matin et à midi, les
    // gens non. Sans elle, une balade décrivait une ville vide.
    gens: direGens(p.gens),
    // CE QU'ON CROISE DE LA BATAILLE, s'il y en a une de datée. Vu,
    // entendu, ou trouvé par terre — jamais autre chose. Un fait qui
    // n'est à portée d'aucun des trois sens ne parvient pas au joueur,
    // et c'est tout le brouillard de cette partie en une ligne.
    croise: croiser.autour(RACINE, lieu, x, y, date),
    fin: !!p.fin,
  };
  // ⚠ DEBUG — voir DEBUG_MARCHE_AU_FIL en tête de fichier. On écrit
  // dans le fil du joueur ce qui part au MJ, tel quel. `pour: [pid]`
  // le garde privé à ce siège ; `duree: 0` parce que la montre a déjà
  // été avancée dix lignes plus haut et qu'on ne la paie pas deux fois.
  if (DEBUG_MARCHE_AU_FIL && pid) {
    const c = pas.croise || {};
    const nb = (t) => (Array.isArray(t) ? t.length : 0);
    const perçus = [].concat(c.vu || [], c.entendu || [], c.traces || [])
      .slice(0, 4)
      .map((f) => "· " + (f.comment || "?") + " — " + (f.quoi || "?") +
                  (f.nom ? " (" + f.nom + ")" : "") +
                  (f.pas != null ? ", " + f.pas + " pas" : ""));
    const lignes = [
      "▣ " + (p.combat ? "COMBAT" : "BALADE") + " — " + pas.ou,
      pas.metres + " m, " + pas.minutes + " min" +
        (pas.quartier ? " — " + pas.quartier : ""),
      pas.longe && pas.longe.length ? "longe : " + pas.longe.join(" ; ") : null,
      pas.tissu ? "tissu : " + pas.tissu : null,
      pas.gens && pas.gens.en_armes
        ? "EN ARMES : " + pas.gens.en_armes +
          (pas.gens.armes ? " — " + pas.gens.armes : "") : null,
      pas.gens && pas.gens.font ? "font : " + pas.gens.font : null,
      pas.gens && pas.gens.metiers
        ? "croise : " + pas.gens.croises + " — " + pas.gens.metiers : null,
      (nb(c.vu) + nb(c.entendu) + nb(c.traces))
        ? "PERÇU (" + nb(c.vu) + " vu / " + nb(c.entendu) + " entendu / " +
          nb(c.traces) + " traces) :\n" + perçus.join("\n")
        : null,
    ].filter(Boolean);
    try {
      fs.appendFileSync(path.join(RACINE, "etat", "flux.jsonl"),
        JSON.stringify({ type: "breve", texte: lignes.join("\n"),
                         // LA DATE, et ce n'est pas du décor : le
                         // bandeau du fil n'écrit l'heure QUE sur un
                         // item qui en porte une. Sans elle, on marche
                         // quarante minutes, la carte avance, et le
                         // bandeau reste à l'heure du départ — deux
                         // heures différentes sur le même écran, ce
                         // qui est exactement ce que `bus.js` dit
                         // vouloir éviter.
                         date,
                         pour: [pid], delai_s: 0, duree: 0,
                         debug: true }) + "\n", "utf-8");
    } catch (e) { /* le debug ne casse jamais la marche */ }
  }
  const dossier = pid
    ? path.join(RACINE, "etat", "inbox", pid)
    : path.join(RACINE, "etat", "inbox");
  // Le tampon de la balade en cours, hors de l'inbox pour ne pas
  // réveiller le guetteur avant l'arrivée. Sans roster il n'y a pas
  // d'id de siège : le sac de la partie seule s'appelle
  // `_sans-siege.json`, l'underscore le distinguant d'un vrai id.
  const tampons = path.join(RACINE, "etat", "marches");
  fs.mkdirSync(tampons, { recursive: true });
  const tampon = path.join(tampons, (pid || "_sans-siege") + ".json");
  // DÉPOSER = fermer le sac dans l'inbox et oublier le tampon. C'est le
  // seul geste qui réveille le MJ, et il n'arrive qu'une fois par
  // balade. `_session` et `_touche_a` sont de la tuyauterie du tampon :
  // on les retire, le sac que lit le MJ garde exactement son format.
  const deposer = (s) => {
    delete s._session;
    delete s._touche_a;
    fs.mkdirSync(dossier, { recursive: true });
    fs.writeFileSync(path.join(dossier, "marche-" + Date.now() + ".json"),
      JSON.stringify(s, null, 2), "utf-8");
    try { fs.unlinkSync(tampon); } catch (e) {}
  };
  let sac = null;
  try { sac = JSON.parse(fs.readFileSync(tampon, "utf-8")); }
  catch (e) { sac = null; }
  // UNE BALADE ABANDONNÉE NE MANGE PAS LA SUIVANTE. Le joueur qui
  // renonce ou ferme l'onglet laisse un tampon que rien ne fermera
  // jamais. Plutôt qu'une expiration savante : si le sac trouvé porte
  // la signature d'un AUTRE démarrage du serveur, ou si son dernier
  // pas remonte à plus de cinq minutes réelles — on marche un tronçon
  // toutes les quelques secondes, cinq minutes est une éternité en
  // chemin —, c'est une autre promenade. On la ferme vers l'inbox
  // telle qu'elle est, puis on en ouvre une neuve : rien n'est perdu,
  // le MJ reçoit la balade interrompue avec ses pas et son `fini`
  // resté faux, ce qui lui dit précisément qu'elle a été abandonnée.
  if (sac && Array.isArray(sac.pas)) {
    const vieux = Date.now() - (+sac._touche_a || 0) > 5 * 60 * 1000;
    if (sac._session !== SESSION_SERVEUR || vieux) {
      deposer(sac);
      sac = null;
    }
  }
  if (!sac || !Array.isArray(sac.pas)) {
    // « combat » quand l'homme TIENT SA POSITION au lieu de marcher :
    // même route, même sac, même horloge — mais le MJ doit savoir s'il
    // lit une promenade ou dix minutes passées devant une porte qu'on
    // enfonce. Sans ce mot, il recevrait quarante pas de zéro mètre et
    // devrait le deviner. Voir ecrans/modules/combat.js.
    sac = { type: p.combat ? "combat" : "marche", joueur_id: pid, lieu,
            depart: pas.ou, recu_a: new Date().toISOString(), pas: [] };
  }
  sac.pas.push(pas);
  sac.arrivee = pas.ou;
  sac.metres = (sac.metres || 0) + pas.metres;
  sac.minutes = Math.round(((sac.minutes || 0) + pas.minutes) * 10) / 10;
  // CE QUI SE LÈVE EN CHEMIN ARRÊTE LA MARCHE. C'est la règle du
  // manuel — « alors on arrête de marcher » — et elle ne peut pas
  // rester à la main du MJ : quand le joueur traverse un assaut, ses
  // jambes doivent s'arrêter à l'instant où il le voit, pas trois pas
  // plus loin quand quelqu'un s'en aperçoit. Le sac se ferme dans la
  // foulée, sinon le guetteur attendrait une arrivée qui ne viendra
  // plus.
  const arret = !!(pas.croise && pas.croise.arret);
  // `arret` FERME UNE BALADE, PAS UN COMBAT. Ce qui se lève en chemin
  // coupe les jambes de qui marche — c'est la règle, et elle est bonne.
  // Mais celui qui TIENT SA POSITION est déjà arrêté : lui dire de
  // s'arrêter n'a aucun sens, et fermer son sac au premier « la porte
  // cède » clôturait la scène à la minute où elle commençait. Pire,
  // `combat.js` ne lit pas `arret` et continuait de ticker : le serveur
  // rouvrait un sac, que le fait suivant refermait, et l'on obtenait un
  // fichier par tic — le déluge exact que le tampon existe pour éviter.
  //
  // En combat, un fait qui arrêterait un marcheur n'est donc pas une
  // fin : c'est une nouvelle, et elle part en tranche par la règle
  // au-dessus.
  sac.fini = !!p.fin || (arret && !p.combat);
  if (arret) sac.arret = pas.croise.vu[0] || true;
  // ÇA SE RACONTE PENDANT, PAS APRÈS. C'était le concept, et le tampon
  // — qui n'a pas tort de protéger le guetteur — le perdait en route :
  // un homme qui voit une porte céder à quarante pas le faisait savoir
  // dix minutes plus tard, à l'arrivée. Une scène qui se joue en
  // différé n'est pas une scène ; le joueur attend devant un plan muet
  // pendant que le MJ ne sait rien.
  //
  // La conciliation n'est pas « tamponner OU diffuser », c'est
  // DIFFUSER CE QUI EST UNE NOUVELLE ET TAMPONNER CE QUI N'EN EST PAS
  // UNE. On dépose donc dès qu'un pas PERÇOIT quelque chose — vu,
  // entendu, ou trouvé par terre —, que l'homme marche ou qu'il tienne
  // sa position. Une promenade tranquille ne réveille toujours le MJ
  // qu'une fois, à l'arrivée : c'est le silence qui se tamponne, pas
  // la bataille.
  //
  // AVEC UN PLANCHER D'UNE MINUTE DE FICTION, sinon on retombe très
  // exactement dans le mal que le tampon vient de guérir : quarante
  // tics bruyants feraient quarante fichiers et quarante sonneries.
  // Le plancher se compte sur l'horloge du jeu et non sur la montre
  // réelle, parce que c'est ×N qui décide de la seconde des deux.
  const percu = pas.croise &&
    ((pas.croise.vu || []).length || (pas.croise.entendu || []).length ||
     (pas.croise.traces || []).length);
  const clefMin = date ? ((date.annee * 12 + date.lune) * 30 + date.jour) * 1440
                       + date.minute : 0;
  const versee = !sac.fini && percu &&
                 clefMin - (+sac._verse_a || 0) >= 1;
  if (versee) {
    sac._verse_a = clefMin;
    // On dépose une TRANCHE : ce qui est parti est parti, et la suite
    // s'accumule dans un sac neuf. Le MJ lit donc la scène par
    // morceaux dans l'ordre, jamais deux fois la même ligne. `suite`
    // lui dit que ce sac n'est pas un début — sans quoi il croirait
    // que l'homme vient d'arriver à chaque tranche.
    const tranche = sac;
    sac = { type: sac.type, joueur_id: pid, lieu, depart: pas.ou,
            recu_a: new Date().toISOString(), pas: [],
            _verse_a: clefMin, suite: true };
    deposer(tranche);
  }
  if (sac.fini) {
    deposer(sac);
  } else {
    sac._session = SESSION_SERVEUR;
    sac._touche_a = Date.now();
    fs.writeFileSync(tampon, JSON.stringify(sac, null, 2), "utf-8");
  }
  return { code: 200, corps: { date, ou: dit, autour,
                                            pas: sac.pas.length, arret } };
} catch (e) {
  return { code: 500, corps: { erreur: String(e.message || e) } };
}
}

module.exports = { poser, marcher };
