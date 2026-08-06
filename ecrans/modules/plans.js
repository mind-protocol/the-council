// plans.js — les plans de château, une entrée par lieu (`window.Plans`).
// Pendant intérieur de geo.js : là où geo.js donne le royaume vu de haut, ceci
// donne la salle où l'on est. Rien n'est généré : un plan est dessiné à la main,
// une fois, et ne bouge plus — un château ne change pas de salles.
//
// Ce n'est PAS un relevé d'architecte : c'est le plan tel qu'on le tient dans
// la tête quand on y vit. On garde ce qui a un enjeu (où l'on décide, où l'on
// dort, où arrivent les corbeaux, par où l'on sort) et on jette le reste.
//
// Une salle :
//   id, nom          — l'id sert au canal de pensée (clic = on y songe)
//   forme            — {c:[cx,cy,r]} cercle | {r:[x,y,l,h,arrondi]} | {d:"…"} chemin
//   lignes           — le nom coupé pour tenir dans la forme (une ligne = un <text>)
//   etiq             — [x,y] ancre du nom (les lignes descendent de là)
//   quoi             — une ligne au survol : ce que la salle EST
//   etage            — "sommet" | "dessous" : la salle n'est pas de plain-pied.
//                      Un plan est plat ; le pointillé dit qu'on monte ou qu'on
//                      descend pour y aller, et `quoi` dit de combien.
//   dehors           — true : hors les murs (rendu plus pâle)
//   fond             — true : dessinée sous la muraille (la cour)
//   cle              — true : garde son nom dans la vignette étroite du décor.
//                      Les autres n'y sont que des formes (nom au survol) et
//                      retrouvent leur légende sur le plan déplié.
//   alias            — noms à rendre cliquables DANS LE FIL (distinctifs seulement :
//                      « la cour » ou « le quai » piégeraient toute la prose)
//   motifs           — ce qui, dans l'en-tête de lieu du bandeau, désigne cette
//                      salle (« Petite salle du levant, Peyredragon » → salle-levant)
"use strict";
window.Plans = {
  peyredragon: {
    nom: "Peyredragon",
    viewBox: "0 0 420 340",

    // Le décor : la montagne au nord, la baie au sud. Ni l'un ni l'autre ne se clique.
    fonds: [
      { classe: "plan-roche", d: "M0,0 L420,0 L420,44 Q332,72 250,52 Q168,30 96,58 Q44,76 0,50 Z" },
      { classe: "plan-mer", d: "M0,292 Q110,280 208,290 Q312,300 420,284 L420,340 L0,340 Z" },
    ],
    // La muraille : dix pans, une tour de guet à chaque angle.
    mur: "M44,88 L118,66 L252,62 L354,82 L388,152 L374,238 L302,270 L148,274 L60,246 L34,168 Z",
    guet: [[44, 88], [118, 66], [252, 62], [354, 82], [388, 152],
           [374, 238], [302, 270], [148, 274], [60, 246], [34, 168]],
    // Le relief : crêtes du Dragonmont au nord, houle dans la baie au sud.
    // Purement décoratif (classe `plan-arete` / `plan-vague`), tracé sous tout.
    decor: [
      { classe: "plan-arete", d: "M18,44 L44,20 L70,42" },
      { classe: "plan-arete", d: "M84,52 L118,14 L152,44" },
      { classe: "plan-arete", d: "M168,32 L196,8 L224,34" },
      { classe: "plan-arete", d: "M244,44 L276,16 L308,42" },
      { classe: "plan-arete", d: "M324,44 L352,22 L382,46" },
      { classe: "plan-vague", d: "M14,304 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M150,300 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M60,322 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M212,318 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M300,296 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
    ],
    etiquettes: [
      { x: 108, y: 28, texte: "Le Dragonmont", classe: "plan-large" },
      { x: 120, y: 322, texte: "La baie de la Néra", classe: "plan-eau" },
    ],
    // La rose des vents, [x, y, rayon] : le plan est orienté — le Dragonmont au
    // nord, le large au sud, et c'est pour ça que la salle du levant est à
    // droite. Posée dans l'eau à l'ouest, où rien d'autre ne se dispute la place.
    rose: [36, 306, 14],

    salles: [
      { id: "cour", nom: "La cour", fond: true,
        forme: { d: "M44,88 L118,66 L252,62 L354,82 L388,152 L374,238 L302,270 L148,274 L60,246 L34,168 Z" },
        etiq: [238, 84], lignes: ["La cour"],
        quoi: "Pavés, puits, chariots : tout ce qui entre au château passe par là.",
        orne: ["puits", 185, 92, 8],
        alias: [], motifs: ["la cour", "cour du château"] },

      { id: "tambour-de-pierre", nom: "Le Tambour de Pierre", cle: true,
        forme: { c: [212, 152, 58] }, etiq: [212, 106],
        lignes: ["Le Tambour", "de Pierre"],
        quoi: "Le donjon central. Sourd comme un tambour quand la mer monte.",
        orne: ["colimacon", 212, 202, 7],
        alias: ["Tambour de Pierre"], motifs: ["tambour de pierre", "donjon"] },

      { id: "table-peinte", nom: "La chambre de la Table Peinte", cle: true, etage: "sommet",
        forme: { c: [212, 164, 30] }, etiq: [212, 161],
        lignes: ["La Table", "Peinte"],
        quoi: "Au sommet du Tambour : Westeros taillé dans le bois, et le conseil autour.",
        orne: ["ronde", 212, 184, 7],
        alias: ["Table Peinte", "chambre de la Table Peinte"],
        motifs: ["table peinte"] },

      { id: "tour-dragon-mer", nom: "La Tour du Dragon de Mer", cle: true,
        forme: { c: [330, 140, 36] }, etiq: [330, 116],
        lignes: ["Tour du", "Dragon de Mer"],
        quoi: "La tour de la reine, face au large. On y voit venir les voiles avant tout le monde.",
        alias: ["Tour du Dragon de Mer"], motifs: ["dragon de mer"] },

      { id: "appartements-reine", nom: "Vos appartements", etage: "sommet",
        forme: { c: [330, 152, 18] }, etiq: [330, 150],
        lignes: ["Vos", "appartements"],
        quoi: "Votre lit, vos coffres, la porte que l'on vient frapper la nuit.",
        alias: [], motifs: ["vos appartements", "appartements de la reine", "appartements"] },

      { id: "guivre-des-vents", nom: "La Guivre des Vents", cle: true,
        forme: { c: [88, 150, 34] }, etiq: [88, 146],
        lignes: ["La Guivre", "des Vents"],
        quoi: "La tour de la garnison : ser Robert y couche, ses hommes en dessous.",
        orne: ["lances", 88, 173, 8],
        alias: ["Guivre des Vents"], motifs: ["guivre des vents", "garnison", "corps de garde"] },

      { id: "cachots", nom: "Les cachots", etage: "dessous",
        forme: { c: [138, 152, 16] }, etiq: [138, 153],
        lignes: ["Les", "cachots"],
        quoi: "Taillés dans la roche, sous la cour. Vides pour l'instant.",
        orne: ["barreaux", 138, 141, 4],
        alias: [], motifs: ["cachots", "geôles"] },

      { id: "roukerie", nom: "La roukerie",
        forme: { c: [280, 92, 20] }, etiq: [280, 95], lignes: ["La roukerie"],
        quoi: "Les corbeaux, le registre et le cabinet du mestre. Tout ce qui arrive y arrive d'abord.",
        orne: ["corbeau", 280, 80, 7],
        alias: ["roukerie"], motifs: ["roukerie", "cabinet du mestre"] },

      { id: "septuaire", nom: "Le septuaire",
        forme: { c: [140, 96, 24] }, etiq: [140, 99], lignes: ["Le septuaire"],
        quoi: "Sept autels sous un toit trop petit : l'île prie surtout le feu.",
        orne: ["etoile", 140, 83, 7],
        alias: ["septuaire"], motifs: ["septuaire", "sept "] },

      { id: "jardin-aegon", nom: "Le jardin d'Aegon",
        forme: { r: [62, 192, 70, 50, 10] }, etiq: [97, 213],
        lignes: ["Le jardin", "d'Aegon"],
        quoi: "Des arbres noirs plantés par le Conquérant. On y parle de ce qui ne se dit pas en salle.",
        orne: ["arbres", 97, 233, 6],
        alias: ["jardin d'Aegon"], motifs: ["jardin"] },

      { id: "grande-salle", nom: "La grande salle", cle: true,
        forme: { r: [150, 214, 124, 46, 6] }, etiq: [212, 241],
        lignes: ["La grande salle"],
        quoi: "Les longues tables, l'estrade, la place où l'on fait jurer.",
        orne: ["tables", 212, 251, 7],
        alias: [], motifs: ["grande salle", "grand hall"] },

      { id: "salle-levant", nom: "La petite salle du levant",
        forme: { r: [292, 190, 64, 46, 6] }, etiq: [324, 208],
        lignes: ["Salle du", "levant"],
        quoi: "Une table pour six, plein est : on y mange avant que le château se lève.",
        orne: ["table6", 324, 228, 7],
        alias: ["salle du levant"], motifs: ["salle du levant", "levant"] },

      { id: "archives", nom: "L'archive", etage: "dessous",
        forme: { r: [290, 230, 50, 20, 4] }, etiq: [320, 243],
        lignes: ["L'archive"],
        quoi: "Trois étages sous la salle du levant : les registres de l'île, et le froid qui va avec.",
        orne: ["rouleau", 298, 241, 4.5],
        alias: ["l'archive"], motifs: ["archive", "registres"] },

      { id: "fosses", nom: "Les fosses aux dragons", cle: true, dehors: true,
        forme: { r: [240, 6, 132, 42, 16] }, etiq: [306, 24],
        lignes: ["Les fosses", "aux dragons"],
        quoi: "Les cavernes fumantes du Dragonmont. Syrax y dort, Caraxès aussi quand il veut bien.",
        orne: ["flamme", 258, 30, 9],
        alias: ["fosses aux dragons", "fosses"], motifs: ["fosses", "dragonmont"] },

      { id: "grand-escalier", nom: "Le grand escalier", dehors: true,
        forme: { d: "M300,266 L344,252 L372,300 L316,312 Z" }, etiq: [338, 278],
        lignes: ["Le grand", "escalier"],
        quoi: "Trois cents marches taillées face à la mer. Ce qui s'y fait se voit depuis les navires.",
        traits: [
          "M302.3,272.6 L348.0,258.9",
          "M304.6,279.1 L352.0,265.7",
          "M306.9,285.7 L356.0,272.6",
          "M309.1,292.3 L360.0,279.4",
          "M311.4,298.9 L364.0,286.3",
          "M313.7,305.4 L368.0,293.1"],
        alias: ["grand escalier"], motifs: ["grand escalier", "escalier"] },

      { id: "quai", nom: "Le quai", dehors: true,
        forme: { r: [318, 306, 84, 22, 4] }, etiq: [360, 321], lignes: ["Le quai"],
        quoi: "Sous le château : ce qui part et ce qui arrive par la mer.",
        orne: ["nef", 331, 317, 6],
        alias: [], motifs: ["quai", "port"] },

      { id: "porte-dragon", nom: "La porte du Dragon", dehors: true,
        forme: { r: [92, 250, 56, 30, 4] }, etiq: [114, 264],
        lignes: ["La porte", "du Dragon"],
        quoi: "Le corps de garde et la herse. On y compte tout ce qui entre sur l'île.",
        orne: ["herse", 142, 265, 4],
        alias: [], motifs: ["porte du dragon", "la porte", "herse"] },
    ],
  },
};
