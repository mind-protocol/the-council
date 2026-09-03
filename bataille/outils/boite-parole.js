// PARLER DEPUIS LA CARTE — la boite en bas a droite de la page.
//
// Ce qu'on y tape est une PAROLE du corps du siege : le scenario affecte un
// corps a la fiche du joueur (`personnage`), et c'est de la ou ce corps se
// tient que la voix porte (⚙️ acoustique : `conduire.quiEntend`). Tout le
// monde a portee entend, et personne d'autre. Sans corps sur ce champ, pas de
// voix : la boite le dit et n'envoie rien — on ne parle pas d'ou l'on n'est
// pas. La page ne choisit personne : elle MESURE qui est a portee et le dit au
// serveur qui l'heberge (POST /action, le meme que la barre du jeu), qui
// reveille ceux qui ont une ecritoire. Un `!` final = un cri (25 m) au lieu
// d'une parole (8 m). Servie seule (outils/serveur.mjs), /moi et /action
// tombent en 404 et la boite le dit.
(function () {
  const boite = document.createElement('div');
  boite.id = 'boite-messages';
  boite.style.cssText = 'position:absolute;bottom:20px;right:20px;z-index:9999;background:rgba(0,0,0,.7);padding:10px;border-radius:8px;color:#ddd;font:12px sans-serif';
  boite.innerHTML =
    '<div id="msg-qui" style="margin-bottom:4px;opacity:.8"></div>' +
    '<input type="text" id="msg-input" placeholder="Parler (un ! final = crier)" style="width:250px;padding:5px;font-family:sans-serif">' +
    ' <button id="msg-btn" style="padding:5px;cursor:pointer">Dire</button>' +
    '<div id="msg-oreilles" style="margin-top:4px;min-height:1em;opacity:.8"></div>';
  // Le bootstrap VIDE le body a chaque scenario (`replaceChildren`) : la
  // boite se repose d'elle-meme des qu'elle en est sortie.
  const poser = () => { if (!document.body.contains(boite)) document.body.appendChild(boite); };
  poser();
  new MutationObserver(poser).observe(document.body, { childList: true });
  const qui = boite.querySelector('#msg-qui');
  const input = boite.querySelector('#msg-input');
  const oreilles = boite.querySelector('#msg-oreilles');

  // Le siege : qui l'on est a la table (le cookie de jeton fait foi).
  let moi = null;
  fetch('/moi').then((r) => (r.ok ? r.json() : null)).then((d) => {
    moi = (d && d.moi) || null;
    qui.textContent = moi ? 'Vous : ' + (moi.nom || moi.personnage_id) : 'aucun siege (pas de jeton)';
  }).catch(() => { qui.textContent = 'pas de serveur de jeu'; });

  const dire = () => {
    const texte = input.value.trim();
    if (!texte) return;
    const c = window.conduire;
    if (!c || !c.quiEntend) { oreilles.textContent = 'la carte n’est pas encore chargee'; return; }
    if (!moi) { oreilles.textContent = 'aucun siege : ouvrez le jeu par votre jeton'; return; }
    const locuteurId = c.corpsDe(moi.personnage_id);
    if (locuteurId == null) {
      oreilles.textContent = (moi.nom || moi.personnage_id) + ' n’a pas de corps sur ce champ : pas de voix d’ici';
      return;
    }
    const intensite = /!\s*$/.test(texte) ? 'cri' : 'parole';
    const entendus = c.quiEntend(locuteurId, { intensite });
    const lui = (window.asciiHommes ? window.asciiHommes() : []).find((h) => h.id === locuteurId) || { id: locuteurId };
    const compte = entendus.length + ' personne' + (entendus.length > 1 ? 's' : '');
    // MA PROPRE BULLE, tout de suite : je vois mes mots sur mon corps sans
    // attendre le tour du serveur. Les autres l'entendent par leur reveil.
    if (c.dire) c.dire(moi.personnage_id, texte, 6);
    fetch('/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'libre', mode: 'dire', texte,
        adresse: 'portee', intensite,
        locuteur: { id: lui.id, nom: lui.nom, personnage_id: moi.personnage_id },
        entendu_par: entendus.map((h) => ({ id: h.id, nom: h.nom, personnage_id: h.personnage || undefined })),
      }),
    }).then((r) => {
      oreilles.textContent = (r.ok ? '' : 'refuse (' + r.status + ') — ') +
        (intensite === 'cri' ? 'crie' : 'dit') + ' devant ' + compte;
    }).catch((e) => { oreilles.textContent = 'pas de serveur de jeu : ' + e; });
    input.value = '';
  };
  boite.querySelector('#msg-btn').addEventListener('click', dire);
  input.addEventListener('keypress', (e) => { if (e.key === 'Enter') dire(); });
})();
