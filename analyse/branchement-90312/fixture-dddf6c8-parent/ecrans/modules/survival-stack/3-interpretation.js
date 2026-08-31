// 3-interpretation.js — la troisième couche.
//
//   la question, dans SA bouche : « comment faire ce qu'on m'a dit comme je
//                                   veux ? »
//   ce qu'elle produit             : une manière de tenir l'ordre
//
// ELLE NE DEMANDE PAS S'IL OBÉIT. Elle SUPPOSE qu'il obéit — c'est le cas
// ordinaire, et de très loin — et elle cherche COMMENT, ce qui est toute la
// matière. La désobéissance n'a pas besoin d'une couche à elle : c'est le cas
// limite de celle-ci, quand la manière qu'un homme veut ne ressemble plus du
// tout à ce qu'on lui a dit.
//
// ─────────────────────────────────────────────────────────────────────────────
// POURQUOI ELLE A UNE PLACE, ET CE QU'ELLE N'EST PAS
//
// UN ORDRE EST SOUS-DÉTERMINÉ, TOUJOURS. « Appuyer la première aile à quatre
// -vingts pas » ne dit pas si l'on se tient à soixante ou à cent, ni si l'on y
// va en traînant ou en courant, ni ce qu'on fait du cousin blessé qu'on
// dépasse. C'est dans cet écart que l'homme met le sien — et c'est ce qui
// produit une troupe qui obéit sans être une troupe de pions.
//
// ET L'ÉCART S'ÉLARGIT EN CHEMIN. La chaîne d'ordres de `bataille2d.js` ne
// transmet pas une intention, elle transmet une PHRASE, et un coureur perd ses
// subordonnées avant son verbe : `interdit`, puis `declencheur`, puis `marge`,
// puis `objet`. Un ordre qui arrive amputé n'est pas un ordre déformé au sens
// du bruit — c'est un ordre qui laisse PLUS DE PLACE à cette couche-ci, et
// c'est la raison pour laquelle une aile mal renseignée se met à faire ce
// qu'elle veut. La déformation et l'interprétation sont la même mécanique vue
// des deux bouts.
//
// CE QU'ELLE NE FAIT PAS : elle ne choisit pas le verbe. Avancer, tenir, se
// replier, suivre, appuyer — ça vient de la tête, par la bannière ou par un
// homme qui court, et cette couche n'a pas à en discuter. Elle ne rend donc pas
// un ordre : elle rend TROIS NOMBRES qui disent comment celui qu'on a reçu sera
// tenu. C'est ce qui la garde composable avec les trois autres, comme l'exige
// la règle n°2 — une couche qui rendrait un objet obligerait l'arbitre à cesser
// d'être une somme.
// ─────────────────────────────────────────────────────────────────────────────
//
// EN OBSERVATION. Rien ici ne conduit : la cascade de `soldat()` fait le travail
// des couches hautes depuis toujours, et l'on ne remplace un morceau qu'après
// l'avoir regardé se tromper sur une vraie nuit. Voir le branchement progressif
// dans le README.
"use strict";
(() => {

  /** Lecture d'un signal, zéro par défaut — zéro étant l'ordinaire. */
  const G = (s, k, d) => (typeof s[k] === "number" ? s[k] : (d || 0));

  // ===========================================================================
  // CE QUE L'ORDRE LAISSE COMME PLACE
  // ===========================================================================
  // LA MESURE EST DANS LA PHRASE, et c'est ce qui rend cette couche calculable
  // au lieu d'être une intention de plus. Un ordre qui porte son objet, sa
  // marge, son interdit et son déclencheur ne laisse presque rien à décider ;
  // le même réduit à son verbe ne laisse que ça.
  //
  // On compte les clauses SURVIVANTES dans l'ordre exact où la transmission les
  // arrache — la liste est celle de `bataille2d.js`, et si elle change là-bas
  // elle doit changer ici. Quatre clauses possibles, donc quatre quarts de
  // détermination.
  const CLAUSES = ["interdit", "declencheur", "marge", "objet"];

  /** De +1 (tout est dit) à −1 (il ne reste qu'un verbe). */
  function place(ordre) {
    if (!ordre) return -1;
    let n = 0;
    for (const c of CLAUSES) {
      const v = ordre[c];
      if (v === undefined || v === null) continue;
      if (Array.isArray(v) && !v.length) continue;
      n++;
    }
    // ET LE VERBE COMPTE, LUI AUSSI. « Tenir » est plus déterminé que
    // « avancer » : il dit où l'on est, et c'est déjà la moitié de la question.
    // « Suivre » et « appuyer » sont les plus vagues des cinq, parce que leur
    // but bouge — se tenir à côté de quelqu'un qui marche demande de décider
    // quelque chose à chaque pas.
    const duVerbe = { tenir: +0.5, repli: +0.2, avancer: 0,
                      appuyer: -0.2, suivre: -0.3 }[ordre.verbe] || 0;
    return Math.tanh(n * 0.9 - 1.35 + duVerbe);
  }

  // ===========================================================================
  // LES TROIS NOMBRES
  // ===========================================================================
  // Signaux, tous dans [−1, 1] :
  //   `place`    ce que l'ordre laisse à décider — sortie de `place()`
  //   `docile`   son tempérament, celui de la couche 4
  //   `alarme`   +1 tout est calme · −1 le fer est sur lui
  //   `epaule`   +1 les siens sont autour · −1 il est seul
  //   `frais`    +1 il a des jambes · −1 il n'en peut plus
  //   `vu`       +1 un chef le regarde · −1 personne ne le regarde
  //   `depuis`   +1 l'ordre vient de tomber · −1 il date d'une heure

  /** OÙ IL SE TIENT, contre la marge qu'on lui a dite. +1 il serre plus court
   *  que l'ordre, −1 il traîne derrière. Un homme qu'on regarde tient sa place ;
   *  un homme seul et fatigué la perd, et un homme qui a peur se colle aux
   *  siens — c'est le grégarisme, et il ferme les rangs bien plus sûrement
   *  qu'un ordre. */
  function serre(s) {
    return Math.tanh(+0.55 * G(s, "vu")
                   + 0.45 * Math.max(0, -G(s, "alarme"))   // la peur resserre
                   - 0.50 * Math.max(0, -G(s, "frais"))    // la fatigue étire
                   - 0.35 * Math.max(0, -G(s, "epaule"))); // seul, on décroche
  }

  /** AVEC QUELLE HÂTE. +1 il presse le pas, −1 il traîne. La place laissée par
   *  l'ordre joue ici dans les DEUX sens et c'est voulu : un homme bien
   *  renseigné va au rythme qu'on lui a dit, un homme qui n'a plus qu'un verbe
   *  va au sien — et le sien dépend de son tempérament, donc il accélère ou il
   *  s'assoit selon l'homme. */
  function hate(s) {
    const libre = Math.max(0, -G(s, "place"));
    return Math.tanh(+0.60 * G(s, "frais")
                   - 0.35 * G(s, "docile") * libre
                   + 0.40 * Math.max(0, G(s, "depuis"))
                   - 0.30 * Math.max(0, -G(s, "alarme")));
  }

  /** À QUEL POINT SA MANIÈRE RESSEMBLE ENCORE À CE QU'ON LUI A DIT. +1 il tient
   *  la lettre, −1 il fait autre chose — et c'est là, et seulement là, que
   *  vit la désobéissance de ce modèle. Elle n'est pas une décision : c'est ce
   *  qui reste quand un ordre vieux, vague, invérifiable et contraire à ce
   *  qu'on veut a fini de s'user. */
  function lettre(s) {
    // LA PLACE RETIRE, ELLE N'AJOUTE PAS. Écrite comme un terme plein, elle
    // faisait de l'homme ordinaire — tous signaux à zéro, un ordre à une seule
    // clause — quelqu'un qui « arrange l'ordre à sa façon ». Un ordre précis ne
    // rend pas plus obéissant : c'est un ordre vague qui laisse s'user la
    // lettre, faute de lettre à tenir.
    return Math.tanh(+0.70 * G(s, "docile")
                   - 0.55 * Math.max(0, -G(s, "place"))
                   + 0.45 * G(s, "vu")
                   + 0.40 * Math.max(0, G(s, "depuis")));
  }

  /** Les trois d'un coup, plus le mot qui les résume — c'est celui-là qu'on
   *  lit sous le doigt, et c'est tout ce qu'on demande à cette passe. */
  function pas(ordre, signaux) {
    const s = Object.assign({}, signaux, { place: place(ordre) });
    const r = { place: s.place, serre: serre(s), hate: hate(s), lettre: lettre(s) };
    r.maniere = maniere(r);
    r.deSoiMeme = deSoiMeme(r);
    return r;
  }

  /** LE MOT, ET IL N'A AUCUN EFFET. On le lit dans la loupe à côté de la
   *  `branche` que la cascade a prise : la question qu'on se pose en regardant
   *  une nuit est « cet homme-là tient-il son ordre comme je le croirais ? »,
   *  et trois décimales n'y répondent pas. */
  function maniere(r) {
    if (r.lettre < -0.45) return "il n'en fait plus qu'à sa tête";
    if (r.lettre < -0.30) return "il arrange l'ordre à sa façon";
    if (r.serre > 0.35 && r.hate > 0.25) return "il serre et il presse";
    if (r.serre > 0.35) return "il se tient plus court qu'on ne lui a dit";
    if (r.hate < -0.35) return "il y va en traînant";
    if (r.hate > 0.35) return "il y va vite";
    if (r.serre < -0.35) return "il laisse filer la distance";
    return "il tient son ordre comme il est dit";
  }

  // ---- CE QU'IL S'INVENTE QUAND IL N'A PLUS RIEN À TENIR -------------------
  // LE DERNIER ENDROIT OÙ `humeur` SURVIVAIT, et c'était un reste, pas un
  // choix. `bataille2d` portait une table `DE_SOI_MEME = { "-": avancer,
  // ferme: tenir, versatile: repli }` : trois mots câblés qui décidaient de
  // ce qu'une escouade fait sans nouvelles. La couche 1 avait déjà résorbé
  // `humeur` de son côté (`ECOLE_CORPS`), donc DEUX MODÈLES disaient la même
  // chose avec des pièces différentes — exactement le risque qu'on s'était
  // promis d'éviter, et qu'un audit a trouvé.
  //
  // Or c'est ICI que ça se décide : « qu'est-ce que je fais de ce qu'on m'a
  // dit » couvre aussi le cas où l'ordre est mort et où personne ne vient.
  // Un homme n'invente pas dans le vide — il prolonge la manière dont il
  // tenait déjà.
  //
  // ET ÇA SE DÉRIVE DE CE QU'ON A DÉJÀ. Celui qui tenait la lettre serré
  // continue de tenir : c'est ce que « ferme » disait. Celui qui l'avait
  // lâchée n'a plus de raison de rester : c'est « versatile ». Entre les
  // deux, on avance, parce qu'un soldat ordinaire ne reste pas trois minutes
  // à regarder ses pieds. Les trois humeurs sortent de deux nombres.
  function deSoiMeme(r) {
    if (!r) return "avancer";
    if (r.lettre < -0.35) return "repli";
    if (r.lettre > 0.15 || r.serre > 0.30) return "tenir";
    return "avancer";
  }

  // ===========================================================================
  const API = { place, serre, hate, lettre, pas, maniere, deSoiMeme, CLAUSES };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.Interpretation = API;
})();
