// LA MÊLÉE — le moteur de bataille comme échelle du décor.
//
// Les autres échelles dessinent elles-mêmes ; celle-ci HÉBERGE. `bataille/` est
// un dépôt importé avec sa page, ses scénarios et ses huit containers (voir
// bataille/IMPORT.md) : on ne le réécrit pas dans un module, on lui donne le
// cadre. Le serveur du jeu le sert sous /bataille/ (serveur/routes/bataille.js).
//
// Ce que ça N'EST PAS, et il faut le savoir en le lisant : le conseil ne produit
// pas encore l'ordre de bataille. Le scénario se choisit à la main dans le
// catalogue du moteur. C'est le décor qui est branché, pas la simulation.
(function () {
  const P = "melee";
  let cadre = null;      // l'iframe, posée seulement à la première ouverture
  let scenario = null;   // ce qu'un item de flux a demandé, s'il en a demandé un

  function hote() { return document.getElementById(P); }

  // L'iframe coûte le chargement d'un moteur entier : on ne la pose que quand
  // le joueur vient réellement voir, et on la garde ensuite.
  function poser() {
    const h = hote();
    if (!h || cadre) return;
    cadre = document.createElement("iframe");
    cadre.src = "/bataille/" + (scenario ? "?scenario=" + encodeURIComponent(scenario) : "");
    cadre.title = "La mêlée";
    cadre.setAttribute("frameborder", "0");
    cadre.style.cssText = "width:100%;height:100%;border:0;display:block;background:#14161a";
    h.appendChild(cadre);
  }

  // Un item de flux qui nomme un scénario : on recharge si le moteur est déjà
  // là, et on bascule le décor — une bataille qui commence prend l'écran.
  function ouvrir(nom) {
    scenario = nom || null;
    poser();
    if (cadre && nom) cadre.src = "/bataille/?scenario=" + encodeURIComponent(nom);
    if (window.Echelles && Echelles.montrer) Echelles.montrer(P);
  }

  if (window.Echelles && Echelles.echelle) {
    Echelles.echelle({ id: P, nom: "La mêlée", hote: P, ordre: 5,
                   dispo: () => true,
                   reparu: poser });
  }

  // LA PORTÉE — ce qu'une parole de la barre emporte quand la mêlée est
  // ouverte : qui est à portée du locuteur, mesuré par l'acoustique du moteur
  // (`conduire.quiEntend`, même origine : la fenêtre de l'iframe est lisible).
  // Le locuteur est LE CORPS DU SIÈGE (`personnage` du scénario) : sans mêlée
  // chargée, ou sans corps sur ce champ, `null` — la pièce reste l'adresse. Un
  // `!` final crie.
  function portee(texte) {
    const w = cadre && cadre.contentWindow;
    const c = w && w.conduire;
    const moi = window.Moi && window.Moi.personnage_id;
    if (!c || !c.quiEntend || !moi) return null;
    const id = c.corpsDe(moi);
    if (id == null) return null;
    const intensite = /!\s*$/.test(texte || "") ? "cri" : "parole";
    const lui = (w.asciiHommes ? w.asciiHommes() : []).find((h) => h.id === id) || { id };
    return { adresse: "portee", intensite,
             locuteur: { id: lui.id, nom: lui.nom, personnage_id: moi },
             entendu_par: c.quiEntend(id, { intensite })
               .map((h) => ({ id: h.id, nom: h.nom, personnage_id: h.personnage || undefined })) };
  }

  window.Melee = { ouvrir, poser, portee };
})();
