// bus.js — cœur du viewport : consommation du flux, timings, vieillissement, envoi.
// Plus de fil : chaque module place ses éléments sur le plateau (bulles par acteur,
// bandeaux monde/récit, coin des pensées). Bus.preparer() donne à tout élément le
// vieillissement (contours qui s'affinent) et le traitement des entités.
"use strict";
window.Bus = (() => {
  const rendus = {};
  let file = [];
  let minuterie = null;
  let consommes = 0;
  let chargeInitiale = true;
  let dateAtteinte = null;

  const $ = (id) => document.getElementById(id);
  // L'heure vient de `monde.date.minute`, tenue par scripts/append_flux.py :
  // chaque item porte l'heure a laquelle il se produit. Voir docs/schema.md.
  const texteDate = (d) => d ? d.annee + " AC — " + d.lune + "e lune, " + d.jour + "e jour" : "—";
  // La montre : minutes depuis minuit → "6h13". C'est la seule source de vérité
  // de l'heure ; `moment` (ci-dessous) n'est plus qu'un libellé facultatif.
  const montre = (m) => Math.floor(m / 60) + "h" + String(m % 60).padStart(2, "0");

  // L'heure de la fiction : un item peut porter `moment` ("aube", "milieu de
  // nuit", "après-vêpres"…). Le texte est libre — on n'y cherche qu'un mot pour
  // choisir le signe qui l'accompagne. Il vaut jusqu'au prochain `moment` écrit.
  const HEURES = [
    [/nuit|minuit/i, "🌙"],
    [/aube|aurore|point du jour|matines/i, "🌅"],
    [/matin|prime|tierce/i, "🌤"],
    [/midi|mi-?journ|sexte/i, "☀️"],
    [/apr[eè]s-?midi|relev[eé]e/i, "🌤"],
    [/cr[eé]puscule|couchant|v[eê]pres|soir|complies/i, "🌇"],
  ];
  // Quand on a l'heure exacte, le signe se déduit d'elle et non du libellé.
  const signeDeLHeure = (min) => {
    const h = Math.floor(min / 60);
    if(h < 5)  return "🌙";
    if(h < 7)  return "🌅";
    if(h < 11) return "🌤";
    if(h < 14) return "☀️";
    if(h < 18) return "🌤";
    if(h < 21) return "🌇";
    return "🌙";
  };

  let moment = "";
  function poserHeure(m, min){
    moment = m;
    const trouve = m && HEURES.find(([re]) => re.test(m));
    const signe = (typeof min === "number") ? signeDeLHeure(min) : (trouve ? trouve[1] : "🕰");
    const texte = m ? signe + " " + m : "";
    // Deux endroits pour la même heure : le bandeau de la scène, et la barre
    // du joueur — là où il écrit, il doit voir quand il parle.
    [$("heure"), $("heure-barre")].forEach((h) => {
      if(!h) return;
      h.hidden = !texte;
      h.textContent = texte;
    });
  }

  // Un texte reste lisible le temps qu'on le dit, puis s'efface : il ne se relit qu'au survol.
  const DUREE_LISIBLE = 10000;
  let instantCourant = false;

  // Un type peut avoir plusieurs écoutants, dans l'ordre de chargement des
  // modules : `effacer` vide la salle (galerie) ET nettoie la table (carte).
  function enregistrer(type, fn){
    const precedent = rendus[type];
    rendus[type] = precedent ? (it, ctx)=>{ precedent(it, ctx); fn(it, ctx); } : fn;
  }

  // Un emblème pour la fonction de chacun, lu dans son titre. La table vit
  // dans `taches.js` — c'est elle qui pose aussi les signes sur le plan du
  // château, et un homme doit porter le même à côté de son nom et sur la carte.
  // Le repli local ne sert qu'au cas où le module n'est pas chargé (l'atelier
  // des voix, par exemple), et un titre non reconnu garde son point.
  function embleme(titre){
    if(!titre) return "";
    if(window.Taches && Taches.office){
      return Taches.office({ titre }) || "•";
    }
    return "•";
  }

  function preparer(el){
    el.classList.add("bloc");
    el.dataset.age = "0";
    if(window.Entites) Entites.traiter(el);
    requestAnimationFrame(()=>requestAnimationFrame(()=>el.classList.add("vue")));
    // rejeu d'historique : déjà dit, donc déjà estompé
    if(instantCourant) el.classList.add("estompe");
    else setTimeout(()=>el.classList.add("estompe"), DUREE_LISIBLE);
    return el;
  }

  async function envoyer(action){
    action.date_atteinte = dateAtteinte;
    try{
      await fetch("/action",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify(action)});
    }catch(e){ console.error(e); }
  }

  // Parler n'interrompt plus la salle : ce qui restait à jouer continue de se
  // jouer pendant que le monde prend acte. Seul le bouton Couper arrête le flux.
  function poster(action){
    const bp3=$("pause"); if(bp3) bp3.classList.toggle("actif", file.length > 0);
    $("attente").classList.add("actif");
    envoyer(action);
  }

  // Le bouton Couper : on jette ce qui restait et on fait taire la voix.
  function couper(){
    if(minuterie){ clearTimeout(minuterie); minuterie = null; }
    if(window.Voix) Voix.taire();
    attenteVoix = false;
    file = [];
    const bp=$("pause"); if(bp) bp.classList.remove("actif");
  }

  // Un jalon dans la chronique quand le jour ou le lieu change : sans repère,
  // cent entrées se ressemblent.
  let dernierRepere = "";
  function jalon(texte, classe){
    const zone = $("fil-corps");
    if(!zone) return;
    const d = document.createElement("div");
    d.className = "jalon" + (classe ? " " + classe : "");
    d.innerHTML = "<span>" + texte + "</span>";
    zone.appendChild(d);
  }

  // ---- le temps qui passe et le lieu qui change ------------------------
  // Deux repères seulement, et jamais pour rien : une durée notable écoulée,
  // un changement de lieu. Le reste (la minute qui avance pendant qu'on parle)
  // se lit dans le bandeau, pas dans le fil.
  const SEUIL_SAUT = 45; // minutes : en deçà, on est encore dans la même scène
  const minutesAbsolues = (d) => d ? ((((d.annee || 0) * 12 + (d.lune || 0)) * 30
    + (d.jour || 0)) * 1440 + (typeof d.minute === "number" ? d.minute : 0)) : null;

  // « trois heures plus tard », « le lendemain », « deux lunes plus tard ».
  // `jourChange` : quelques heures qui passent minuit ne se disent pas comme
  // quelques heures dans l'après-midi — on nomme alors le jour où l'on tombe.
  function texteEcoule(delta, date, jourChange){
    const heure = (date && typeof date.minute === "number") ? ", " + montre(date.minute) : "";
    const jours = Math.floor(delta / 1440);
    if(jours >= 30){
      const lunes = Math.round(jours / 30);
      return (lunes === 1 ? "une lune plus tard" : lunes + " lunes plus tard") + heure;
    }
    if(jours >= 1){
      if(jours === 1) return "le lendemain" + heure;
      if(jours === 2) return "le surlendemain" + heure;
      return jours + " jours plus tard" + heure;
    }
    const heures = Math.round(delta / 60);
    const suite = jourChange && date ? heure + " — " + date.jour + "e jour" : heure;
    if(heures <= 1) return "une heure plus tard" + suite;
    return heures + " heures plus tard" + suite;
  }

  let derniereMinute = null;
  let dernierLieu = "";
  function reperes(it){
    const date = it.date || dateAtteinte;
    const abs = minutesAbsolues(it.date);
    const lieu = $("lieu").textContent;
    // Le tout premier repère pose le décor en entier : on ne sait pas d'où l'on vient.
    if(derniereMinute === null && !dernierRepere){
      dernierRepere = texteDate(date) + " · " + lieu;
      jalon(dernierRepere);
      derniereMinute = abs; dernierLieu = lieu;
      return;
    }
    if(abs !== null && derniereMinute !== null && abs - derniereMinute >= SEUIL_SAUT){
      const jourChange = Math.floor(abs / 1440) !== Math.floor(derniereMinute / 1440);
      jalon(texteEcoule(abs - derniereMinute, it.date, jourChange), "jalon-temps");
    }
    if(abs !== null) derniereMinute = abs;
    if(lieu && lieu !== "—" && lieu !== dernierLieu){
      // Un changement de lieu se dit avec sa date : on a pu voyager pour y venir.
      jalon(lieu + " · " + texteDate(date), "jalon-lieu");
      dernierLieu = lieu;
    }
  }

  // Quand une réplique se dit à voix haute, l'item suivant attend la fin de la
  // phrase : sinon le fil parle par-dessus la salle. Une fois la voix éteinte,
  // le délai écrit n'a plus de raison d'être long — on écourte.
  let attenteVoix = false;
  function planifier(ms){
    const p = window.Voix && Voix.enAttente();
    if(!p){ minuterie = setTimeout(()=>jouerItem(false), ms); return; }
    attenteVoix = true;
    p.then(()=>{
      attenteVoix = false;
      minuterie = setTimeout(()=>jouerItem(false), Math.min(ms, 1200));
    });
  }

  // Ce qui vient du joueur : ses mots ne font jamais la queue derrière le monde
  // (voir `sonder`). Le serveur n'inscrit que ces deux types-là depuis la barre.
  const DU_JOUEUR = { vous:1, question:1 };

  // Peindre un item : bandeau, jalon, jauge, puis le module qui sait le rendre.
  // Séparé de `jouerItem` pour qu'on puisse rendre hors file.
  // ---- le passé, à la demande ------------------------------------------
  // Le serveur ne sert qu'une fenêtre du fil. Quand le joueur remonte la
  // chronique jusqu'en haut, on redescend la tranche d'avant et on l'insère
  // au-dessus. Ces items-là sont du PASSÉ REJOUÉ : ils n'ont rien à dire à la
  // salle, à la carte, au bandeau ni à la voix. `enArchive` est le drapeau que
  // les modules consultent pour se taire (galerie, gestes, annales).
  let enArchive = false;
  let ancreArchive = null;
  // Ce qui laisse une trace lisible dans la chronique, et rien d'autre. Un
  // `salle`, un `effacer`, un `objectif` ou une `table` rejoués défigureraient
  // le présent : on ne les redescend pas.
  const ARCHIVABLES = { replique:1, geste:1, recit:1, breve:1, pensee:1, vous:1,
    reecrit:1, question:1, reponse:1, meta:1, coulisses:1, run:1, marque:1 };

  function rendre(it, instant){
    if(enArchive){
      if(!ARCHIVABLES[it.type]) return;
      const fn = rendus[it.type];
      instantCourant = true;
      if(fn) fn(it, {preparer, poster, envoyer, instant:true});
      instantCourant = false;
      return;
    }
    // Un changement de scène vide l'écran : le repère suivant repose le décor
    // en entier plutôt que d'annoncer un écoulement depuis un fil effacé.
    if(it.type === "effacer"){ dernierRepere = ""; derniereMinute = null; dernierLieu = ""; }
    if(it.date){
      dateAtteinte = it.date;
      $("date").textContent = texteDate(it.date);
      // L'horloge de la PARTIE, publiée une fois pour toutes : le décor en
      // volume (ville3d) la lit pour savoir où sont les gens à cette
      // minute-là. Il n'en tient aucune : deux horloges, c'est une partie qui
      // diverge.
      window.Horloge = it.date;
    }
    // `salle` nomme la salle du plan local (plan.js) quand l'en-tête ne suffit
    // pas à la deviner ; elle vaut jusqu'au prochain changement de lieu.
    if(it.lieu){ $("lieu").textContent = it.lieu; delete $("lieu").dataset.salle; }
    if(it.salle) $("lieu").dataset.salle = it.salle;
    // L'heure exacte prime : elle vient de `date.minute`, tenue par
    // append_flux.py. `moment` reste accepté comme libellé quand on veut
    // nommer le temps plutôt que le chiffrer ("avant l'aube").
    if(it.date && typeof it.date.minute === "number"){
      poserHeure(montre(it.date.minute) + (it.moment ? " · " + it.moment : ""), it.date.minute);
    } else if(it.moment) poserHeure(it.moment);
    if(it.date || it.lieu || it.moment) reperes(it);
    if(typeof it.tension === "number") document.querySelector("#jauge i").style.width = it.tension + "%";
    const fn = rendus[it.type];
    instantCourant = !!instant;
    if(fn) fn(it, {preparer, poster, envoyer, instant});
    instantCourant = false;
  }

  function jouerItem(instant){
    if(!file.length) return;
    const it = file.shift();
    minuterie = null;
    rendre(it, instant);
    if(file.length){
      if(instant){ jouerItem(true); }
      else{
        const bp=$("pause"); if(bp) bp.classList.add("actif");
        planifier((file[0].delai_s ?? 5) * 1000);
      }
    } else {
      const bp2=$("pause"); if(bp2) bp2.classList.remove("actif");
    }
  }

  // Le plus ancien index de flux qu'on tienne à l'écran. null tant que rien
  // n'est chargé ; 0 quand on est remonté jusqu'au premier jour de la partie.
  let plusVieuxTenu = null;
  let chargeEnCours = false;

  async function remonter(){
    if(chargeEnCours || plusVieuxTenu === null || plusVieuxTenu <= 0) return;
    chargeEnCours = true;
    const zone = $("fil-corps");
    try{
      const r = await fetch("/scene?avant=" + plusVieuxTenu);
      const s = await r.json();
      const vieux = s.items || [];
      if(vieux.length){
        // On rattrape le défilement à la main : sans ça, insérer mille pixels
        // au-dessus jetterait le joueur au bas de ce qu'il était en train de lire.
        const h0 = zone.scrollHeight, s0 = zone.scrollTop;
        enArchive = true;
        ancreArchive = zone.firstChild;
        try{ for(const it of vieux) rendre(it, true); }
        finally{ enArchive = false; ancreArchive = null; }
        zone.scrollTop = s0 + (zone.scrollHeight - h0);
      }
      plusVieuxTenu = s.debut || 0;
    }catch(e){ /* on réessaiera au prochain défilement */ }
    chargeEnCours = false;
  }

  // Le geste : arriver en haut de la chronique appelle la tranche d'avant.
  window.addEventListener("DOMContentLoaded", ()=>{
    const zone = $("fil-corps");
    if(zone) zone.addEventListener("scroll", ()=>{
      if(zone.scrollTop < 120) remonter();
    });
  });

  let prochainSondage = null;
  async function sonderMaintenant(){
    if(prochainSondage){ clearTimeout(prochainSondage); prochainSondage = null; }
    await sonder();
  }

  // Deux sondages qui se croisent liraient le même bout de flux : chacun le
  // trouverait neuf, et la scène se jouerait deux fois.
  let enSondage = false;
  async function sonder(){
    if(enSondage){ return; }
    enSondage = true;
    try{
      const r = await fetch("/scene");
      const s = await r.json();
      const items = s.items || [];
      // Le serveur ne sert qu'une fenêtre du fil et dit, avec `debut`, combien
      // de lignes il a coupées en tête. Le curseur reste donc compté sur le flux
      // entier : sans ça, la fenêtre glissant à chaque nouvel item, `consommes`
      // resterait collé à sa longueur et plus rien ne se jouerait.
      const debut = s.debut || 0;
      const total = debut + items.length;
      if(consommes < debut) consommes = debut;
      // La tranche la plus ancienne qu'on ait à l'écran : point de départ du
      // chargement à rebours quand le joueur remonte lire.
      if(plusVieuxTenu === null) plusVieuxTenu = debut;
      if(total > consommes){
        const nouveaux = items.slice(consommes - debut);
        consommes = total;
        $("attente").classList.remove("actif");
        // Au rejeu de l'historique, l'ordre du fichier fait foi : on ne trie
        // rien, sinon toutes les paroles du joueur remonteraient en tête.
        if(chargeInitiale){ file = file.concat(nouveaux); }
        else{
          // En jeu, ce qui vient du joueur ne fait pas la queue : le monde peut
          // avoir deux minutes de dialogue en attente, ses mots à lui sortent
          // tout de suite. Effet voulu : `couper()` vide la file mais ne peut
          // plus emporter ses propres paroles, déjà à l'écran.
          const duMonde = [];
          for(const it of nouveaux){
            if(DU_JOUEUR[it.type]) rendre(it, true);
            else duMonde.push(it);
          }
          file = file.concat(duMonde);
        }
        if(file.length && !minuterie && !attenteVoix){
          if(chargeInitiale) jouerItem(true);
          else minuterie = setTimeout(()=>jouerItem(false), (file[0].delai_s ?? 0) * 1000);
        }
      }
      chargeInitiale = false;
    }catch(e){ /* serveur pas encore prêt */ }
    enSondage = false;
    prochainSondage = setTimeout(sonder, 2000);
  }

  // Vieillissement : toutes les 8 s, les contours s'affinent (jamais de gris).
  setInterval(()=>{
    document.querySelectorAll(".bloc").forEach(b=>{
      b.dataset.age = Math.min((+b.dataset.age || 0) + 1, 4);
    });
  }, 8000);

  // La chronique, à droite : trace complète, jamais estompée.
  // opts.avatar : SVG de portrait ; sinon un blason par nature d'entrée.
  // L'ordre compte : une clé plus tardive l'emporte (chr-objectif-accomplir > chr-objectif).
  const BLASONS = {
    "chr-replique":"💬", "chr-recit":"🎭", "chr-breve":"📨", "chr-pensee":"💭",
    "chr-evenement":"⚡", "chr-vous":"🗣️", "chr-acte":"✋",
    "chr-objectif":"🎯", "chr-objectif-accomplir":"✅", "chr-objectif-echouer":"❌",
    "chr-question":"❓", "chr-reponse":"💡",
  };
  function chronique(classe, qui, texte, opts){
    const zone = $("fil-corps");
    if(!zone || !texte) return null;
    const cl = classe || "";
    const o = opts || {};
    let blason = "";
    for(const k in BLASONS){ if(cl.indexOf(k) !== -1) blason = BLASONS[k]; }
    if(cl.indexOf("chr-acte") !== -1) blason = BLASONS["chr-acte"];
    const d = document.createElement("div");
    d.className = "chr " + cl;
    d.innerHTML =
      '<span class="chr-icone">' + (o.avatar || blason) + "</span>" +
      '<div class="chr-corps">' +
      (qui ? '<span class="chr-qui">' + qui +
        (o.role ? '<span class="chr-role"><i class="emb">' + embleme(o.role) + "</i>" +
          o.role + "</span>" : "") + "</span>" : "") +
      '<span class="chr-texte">' +
      (window.Attention ? Attention.html(texte, {}) : texte) + "</span></div>";
    // au rejeu de l'historique, rien ne s'anime : tout est déjà arrivé.
    if(!instantCourant) d.classList.add("entre");
    // Le passé rechargé s'insère AU-DESSUS, devant la même ancre : les items
    // arrivant dans l'ordre, l'ordre est gardé. Et on ne touche pas au défilement
    // — c'est l'appelant qui le rattrape, une fois la tranche entière posée.
    if(enArchive){
      zone.insertBefore(d, ancreArchive);
      if(window.Entites) Entites.traiter(d);
      return d;
    }
    // si le joueur est remonté lire, on ne le ramène pas de force en bas
    const enBas = zone.scrollHeight - zone.scrollTop - zone.clientHeight < 90;
    zone.appendChild(d);
    if(window.Entites) Entites.traiter(d);
    if(instantCourant) zone.scrollTop = zone.scrollHeight;
    else if(enBas) zone.scrollTo({top:zone.scrollHeight, behavior:"smooth"});
    return d;
  }

  // Délégation : les contrôles sont bâtis par actions.js, après ce module.
  document.addEventListener("click", (e)=>{
    const b = e.target.closest("[data-attente]");
    if(b){ poster({type:"mode", texte:b.dataset.attente}); return; }
    if(e.target.closest("#pause")){
      couper();
      poster({type:"pause", texte:"le joueur coupe la scène en cours"});
    }
  });

  // Qui tient ce navigateur. À deux joueurs, la même phrase doit se lire
  // « Vous » chez l'un et « Daemon » chez l'autre : c'est la seule chose que
  // le viewport ait besoin de savoir du multi. Partie seule → moi reste null
  // et tout se comporte comme avant.
  window.Moi = null;
  async function identifier(){
    try{
      const r = await fetch("/moi");
      const d = await r.json();
      window.Moi = d.moi || null;
      window.Sieges = d.sieges || [];
      if(window.Moi) document.body.dataset.siege = window.Moi.personnage_id;
    }catch(e){}
  }

  window.addEventListener("DOMContentLoaded", ()=>{
    const bascule = $("lateral-bascule");
    if(bascule) bascule.onclick = ()=>{
      const l = $("lateral");
      l.classList.toggle("ferme");
      bascule.title = l.classList.contains("ferme") ? "Ouvrir le panneau" : "Replier le panneau";
    };
    identifier().then(sonder);
  });

  // rendus est exposé pour prévisualiser un item sans toucher au flux :
  //   Bus.rendus.salle(item, {preparer:Bus.preparer, poster(){}, envoyer(){}, instant:true})
  return {enregistrer, preparer, poster, envoyer, chronique, rendus, sonderMaintenant,
    embleme, rendre, enArchive: ()=>enArchive};
})();
