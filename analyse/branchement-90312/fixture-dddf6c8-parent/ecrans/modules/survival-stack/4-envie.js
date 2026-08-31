// 4-envie.js — la quatrième couche.
//
//   la question, dans SA bouche : « qu'est-ce que je veux, maintenant ? »
//   ce qu'elle produit             : un désir, gratuit
//
// GRATUIT VEUT DIRE QUE PERSONNE NE L'A DEMANDÉ. Aucune tête n'ordonne de
// piller, aucune ne pourrait l'empêcher, et aucun ordre ne dit combien de temps
// on supporte de n'en plus recevoir. Ces deux choses-là sortent de l'homme et
// de lui seul — c'est la définition de cette couche, et c'est pourquoi les deux
// tableaux qui les tenaient jusqu'ici n'avaient rien à faire dans le module de
// la bataille.
//
// ─────────────────────────────────────────────────────────────────────────────
// CE QU'ON REPREND, ET POURQUOI C'ÉTAIT FAUX
//
//   `APPETIT = { "-": 0.030, ferme: 0, sourd: 0.012, versatile: 0.075 }`
//   — la probabilité, par seconde, qu'un homme quitte sa colonne pour une
//   maison. Quatre nombres pour deux mille cinq cents hommes : dans un corps,
//   TOUS avaient exactement la même convoitise, à la troisième décimale près.
//   Le corps sans humeur pillait 59 % de son temps en régime établi ; celui de
//   Petit Wend, 78 %. Personne n'avait choisi ces chiffres-là — ils tombaient
//   d'un produit qu'aucun des deux tableaux ne montrait.
//
//   `SILENCE = { "-": 25, ferme: 60, versatile: 150, sourd: Infinity }`
//   — les secondes qu'un chef supporte sans nouvelles avant de s'inventer un
//   ordre. Même défaut, plus grave : c'est un seuil en SECONDES, donc il ne sait
//   rien de ce qui se passe autour. Un homme dont l'aile fond attend soixante
//   secondes exactement comme un homme dont la nuit est calme.
//
// LE TEST DE LA RÈGLE N°3 LES CONDAMNE TOUS LES DEUX : *si une autre grandeur
// du modèle double, celui-ci doit-il bouger ?* Oui — la convoitise d'un homme
// dépend de ce qu'il a devant lui, sa patience de ce qu'il croit encore
// commandé. Ce ne sont pas des constantes, ce sont deux fonctions qu'on n'avait
// pas écrites.
//
// CE QUE L'HUMEUR DEVIENT : une MOYENNE, pas une valeur. Elle déplace le centre
// autour duquel chaque homme est tiré ; elle ne dit plus ce que chacun fait.
// Deux hommes du même corps veulent des choses différentes, ce qui est la
// seule chose que les quatre nombres ne savaient pas dire.
// ─────────────────────────────────────────────────────────────────────────────
//
// TOUT EST DANS [−1, 1], entrées comme sorties, et toute borne est une
// SATURATION — `tanh`, jamais un `Math.min` posé après coup. Les fonctions sont
// pures : elles prennent un état, elles rendent un nombre, elles n'écrivent
// rien et n'appellent aucune autre couche.
"use strict";
(() => {

  // ===========================================================================
  // LE TEMPÉRAMENT — ce qu'il apporte de chez lui
  // ===========================================================================
  // DEUX TRAITS, TIRÉS UNE FOIS PAR HOMME, jamais recalculés. Ils sont dans la
  // même échelle que tout le reste : 0 est l'homme moyen d'une troupe moyenne.
  //
  //   `cupide`   +1 il vide une maison sous la mitraille · −1 il ne s'arrête
  //              devant rien
  //   `docile`   +1 il attend son ordre toute la nuit · −1 il décide au bout
  //              de trois minutes de silence
  //
  // Le corps ne les REMPLACE pas, il les DÉCALE — c'est ce qui fait qu'un homme
  // de Cranche peut être plus cupide qu'un homme de Petit Wend, ce qui doit
  // rester possible, et rare.
  //
  // ON CLASSE PAR CORPS, ET PLUS PAR HUMEUR. `humeur` a été dissoute dans la
  // couche 1 — « ferme » y est devenu du dressage et du vécu, « sourd » une
  // fermeture du canal social, « versatile » un fond court — et le champ a
  // disparu des hommes. `APPETIT[h.humeur || "-"]` lisait donc « — » pour tout
  // le monde, en silence : Cranche pillait autant que n'importe qui et le corps
  // de Petit Wend ne se dissolvait plus. C'est exactement la faute que ce
  // fichier existe pour rendre impossible — un tableau indexé sur une clef qui
  // n'existe plus ne lève rien, il rend la valeur par défaut. On s'indexe donc
  // sur le corps, comme `ECOLE_CORPS` juste à côté.
  //
  // ON CALIBRE CONTRE LES ANCIENS NOMBRES, ET C'EST LA RÈGLE N°1. Les quatre
  // valeurs d'`APPETIT` et de `SILENCE` étaient de mauvaises FORMES — un
  // nombre là où il fallait une fonction —, elles n'étaient pas de mauvaises
  // MESURES : elles sortaient d'un comportement qu'on avait regardé tourner.
  // Les pentes ci-dessous sont donc choisies pour que l'homme MOYEN de chaque
  // corps retrouve exactement son ancien chiffre, et tout le gain est dans la
  // dispersion autour — plus le fait que les signaux du moment déplacent
  // maintenant ce centre. Jeter la calibration avec la constante aurait été
  // refaire le réglage à l'oreille, ce que ce fichier existe pour interdire.
  //
  //   humeur     pillage/s   silence
  //   ferme        ~0,003      60 s
  //   —             0,030      25 s
  //   sourd         0,012     très long
  //   versatile     0,075     150 s
  //
  // Le `0` exact de Cranche est le seul chiffre qu'on ne reprend pas, et c'est
  // volontaire : une saturation ne rend jamais zéro, et « ces hommes-là ne
  // pillent JAMAIS » était de toute façon un absolu qu'aucune troupe ne tient.
  // Un arrêt toutes les cinq minutes est plus vrai que jamais, et se voit
  // moins qu'une exception écrite en dur.
  const PENTE = {
    // Cranche, « ferme » : il arrive, et c'est tout ce qu'il fait. Le seul
    // corps dont le décalage est assez fort pour que le pillage y devienne une
    // exception individuelle au lieu d'un comportement de corps.
    cranche:     { cupide: -1.30, docile: +0.38 },
    // Les faux gueux, « sourd » : ils ne pillent pas, ils brûlent — ça prend
    // moins de temps et ça ne rapporte rien. Et le silence ne leur coûte rien,
    // puisqu'ils n'ont jamais rien entendu (voir `jamaisEntendu`).
    gueux:       { cupide: -0.46, docile: +1.00 },
    // Petit Wend, « versatile » : le corps se dissout en chemin, et c'est son
    // personnage.
    bleusailles: { cupide: +0.46, docile: +1.18 },
    cole:        { cupide:  0.00, docile:  0.00 },
    vantre:      { cupide:  0.00, docile:  0.00 },
    "-":         { cupide:  0.00, docile:  0.00 },
  };

  /** Le tempérament d'un homme, tiré une fois, d'après le corps où il sert.
   *  `tirer` est une loi en cloche dans [−1, 1] — `cloche(-1, 1)` de
   *  `bataille/hasard.js` fait l'affaire. */
  function temperament(corps, tirer) {
    const p = PENTE[corps || "-"] || PENTE["-"];
    // On SOMME le tirage et la pente, puis on sature : sans la saturation, un
    // corps très décalé produirait des hommes hors bornes, et l'on retrouverait
    // l'écrêtage qu'on s'interdit. Avec elle, la pente resserre la population
    // contre une borne au lieu de la faire déborder — ce qui est exactement ce
    // qu'on veut dire par « ce corps-là ne pille pas ».
    return { cupide: Math.tanh(tirer() * 0.55 + p.cupide),
             docile: Math.tanh(tirer() * 0.55 + p.docile) };
  }

  // ===========================================================================
  // L'ENVIE DE BUTIN
  // ===========================================================================
  // CE QU'UN HOMME VEUT QUAND PERSONNE NE LE REGARDE. Elle monte avec ce qu'il
  // a sous la main et avec ce qu'il ne risque pas ; elle tombe à rien dès que
  // quelque chose lui prend l'attention — le fer, un chef, un ordre qui le
  // nomme. Ce n'est pas de la morale : un homme au contact ne pille pas parce
  // qu'il est occupé.
  //
  // Signaux attendus, tous dans [−1, 1] :
  //   `cupide`   son tempérament
  //   `porte`    +1 une maison intacte à trois pas · −1 rien à moins de trente
  //   `calme`    +1 personne autour de lui · −1 il est dans la presse
  //   `frais`    +1 il a des jambes · −1 il n'en peut plus
  //   `tenu`     +1 il est sous l'œil d'un chef et sous sa bannière · −1 seul
  //   `defendu`  +1 on lui a dit « sans piller » · −1 on ne lui a rien dit
  function butin(s) {
    const g = (k, d) => (typeof s[k] === "number" ? s[k] : (d || 0));
    // LA PORTE EST UN FACTEUR, PAS UN TERME, et c'est la seule asymétrie du
    // modèle. Toutes les autres envies se somment ; celle-ci ne peut pas
    // exister sans un objet. Un homme au milieu d'un champ ne convoite rien —
    // pas faiblement : rien.
    const aPortee = (g("porte", -1) + 1) / 2;
    if (aPortee <= 0) return -1;
    // LES SIGNAUX ABSENTS DOIVENT PESER ZÉRO, et c'est la faute que la première
    // écriture a faite : `defendu` valant −1 quand on n'a rien dit ajoutait
    // trois quarts de point à tout le monde, si bien que le corps le plus sage
    // pillait quatre-vingts pour cent de son temps. Un interdit qu'on ne
    // prononce pas ne doit pas être une permission qu'on accorde. On écrit donc
    // la clause comme une RETENUE, nulle par défaut et jamais positive — c'est
    // la seule forme qui laisse le tempérament décider quand personne n'a parlé.
    const retenue = (v) => Math.max(0, (g(v, -1) + 1) / 2);
    const somme = 0.85 * g("cupide")
                + 0.40 * g("calme")
                + 0.25 * g("frais")
                - 0.50 * Math.max(0, g("tenu"))
                // « Sans piller » est le seul mot du vocabulaire qui porte sur
                // une envie — et c'est aussi la première clause qu'un coureur
                // oublie. Un homme à qui l'on a dit se retient ; un homme très
                // cupide à qui l'on a dit se retient moins.
                - 1.20 * retenue("defendu");
    return Math.tanh(somme) * aPortee;
  }

  /** Ce que l'envie devient en une chance par seconde de quitter le rang.
   *  −1 ne pille jamais, 0 s'arrête une fois par minute environ, +1 s'arrête
   *  au premier seuil venu. La courbe est exponentielle parce que c'est un
   *  taux : la différence entre « rarement » et « jamais » est un facteur, pas
   *  une soustraction. */
  const tauxDeButin = (e) => (e <= -1 ? 0 : 0.030 * Math.exp(2.2 * e));

  // ===========================================================================
  // LA PATIENCE — ce qu'il supporte de silence
  // ===========================================================================
  // COMBIEN DE TEMPS UN CHEF ATTEND AVANT DE S'INVENTER UN ORDRE. Le tableau
  // qu'on remplace ne connaissait que son humeur ; or ce n'est pas d'une humeur
  // qu'on manque quand on décide seul, c'est d'une RAISON de continuer à
  // attendre. Un homme dont la bannière est debout et dont l'aile tient attend
  // volontiers ; le même, sa bannière à terre et ses voisins qui tombent,
  // n'attend plus du tout — et c'est la scène qu'on est venu chercher.
  //
  //   `docile`   son tempérament
  //   `signe`    +1 sa bannière est debout et il la voit · −1 rien du tout
  //   `entier`   +1 son aile est intacte · −1 elle a fondu
  //   `sur`      +1 son dernier ordre a encore un sens · −1 son objet a disparu
  //   `alarme`   +1 tout est calme · −1 le fer est sur lui
  function patience(s) {
    const g = (k, d) => (typeof s[k] === "number" ? s[k] : (d || 0));
    // Même règle que pour l'envie de butin : ce qui n'est pas là ne pèse pas.
    // Une bannière debout ne DONNE pas de la patience, c'est son absence qui en
    // retire — sinon l'homme ordinaire, dont tous les signaux sont à zéro,
    // tiendrait déjà trois minutes avant d'avoir rien vu ni rien perdu.
    // ZÉRO EST L'ORDINAIRE, ET L'ORDINAIRE NE RETIRE RIEN. Écrit `(1 − v) / 2`,
    // un signal à zéro comptait pour une demi-perte : l'homme dont tout allait
    // bien mais qu'on n'avait pas renseigné tenait sept secondes au lieu de
    // vingt-cinq. La retenue ne part donc que sous zéro, ce qui est la seule
    // lecture compatible avec l'échelle du README.
    const manque = (v, d) => Math.max(0, -g(v, d || 0));
    // LE SOURD NE COMPTE PAS LE SILENCE, et ce n'est pas un très grand nombre :
    // c'est une absence de compteur. Pour lui il n'y a jamais eu autre chose
    // que le silence, donc il n'en manque rien et il porte son premier ordre
    // jusqu'au bout de la nuit. Le dire par un `Infinity` dans un tableau était
    // juste ; le dire par une pente très raide serait faux, parce qu'une pente
    // finit toujours par céder.
    if (s.jamaisEntendu) return Infinity;
    return Math.tanh(0.90 * g("docile")
                   - 0.55 * manque("signe")
                   - 0.40 * manque("entier")
                   - 0.80 * manque("sur", 1)
                   - 0.30 * manque("alarme"));
  }

  /** Ce que la patience devient en secondes de silence tenues. Même forme
   *  exponentielle, même raison : de vingt à cent cinquante secondes n'est pas
   *  une addition, c'est un rapport. Le sourd n'est pas un cas particulier ici
   *  — il tient parce que rien ne lui a jamais manqué, donc ses signaux le
   *  portent d'eux-mêmes tout en haut. */
  const silenceTenu = (p) => (p === Infinity ? Infinity : 25 * Math.exp(2.6 * p));

  // ===========================================================================
  const API = { temperament, butin, tauxDeButin, patience, silenceTenu, PENTE };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.Envie = API;
})();
