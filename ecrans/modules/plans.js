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
        etiq: [300, 175], lignes: ["La cour"],
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
        forme: { c: [280, 92, 20] }, etiq: [272, 95], lignes: ["La roukerie"],
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

      { id: "communs", nom: "Les communs",
        forme: { r: [172, 68, 84, 26, 5] }, etiq: [214, 80],
        lignes: ["Les communs"],
        quoi: "Le long du mur nord : les paillasses de la maisonnee, pages, filles de cuisine, gens de service. On y dort a quinze, tete contre le mur.",
        orne: ["paillasses", 190, 82, 5],
        alias: ["les communs"], motifs: ["communs", "paillasses"] },

      { id: "chambres-hotes", nom: "Les chambres d'hotes", etage: "sommet",
        forme: { r: [266, 176, 24, 26, 4] }, etiq: [278, 185],
        lignes: ["Chambres", "d'hotes"],
        quoi: "Un corps de logis a l'ecart, pour qui arrive avec un nom. Qui y couche, et qui n'y couche pas, se remarque le soir meme.",
        orne: ["lit", 278, 198, 3.5],
        alias: ["chambres d'hotes"], motifs: ["chambre d'hote", "chambres d'hotes"] },

      { id: "baraques", nom: "Les baraques", dehors: true,
        forme: { r: [38, 250, 50, 26, 3] }, etiq: [63, 262],
        lignes: ["Les baraques"],
        quoi: "Hors les murs, contre la porte : les toiles et les appentis ou couchent les hommes marques au role. Ils dorment dehors, et ils comptent ceux qui dorment dedans.",
        orne: ["toiles", 63, 271, 5],
        alias: ["les baraques"], motifs: ["baraques", "appentis"] },

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

      // Trois endroits que les routines des gens nomment (etat/routines.json) et
      // que le plan ignorait : sans forme ici, personne ne s'y voit sur la carte.
      { id: "porte-de-mer", nom: "La porte de mer", dehors: true,
        forme: { r: [222, 274, 70, 22, 4] }, etiq: [257, 288], lignes: ["La porte de mer"],
        quoi: "La poterne basse et le guet qu'on double la nuit. Tout ce qui vient du quai passe là.",
        orne: ["herse", 232, 285, 3.6],
        alias: ["porte de mer"], motifs: ["porte de mer"] },

      { id: "galeries", nom: "Les galeries", etage: "dessous",
        forme: { r: [12, 296, 130, 26, 4] }, etiq: [77, 312], lignes: ["Les galeries"],
        quoi: "Quatre-vingts pas sous la mer : on y taille le verredragon, à la chandelle.",
        alias: ["les galeries"], motifs: ["galerie", "verredragon", "obsidienne"] },

      { id: "bourg", nom: "Le bourg", dehors: true,
        forme: { r: [0, 108, 30, 68, 4] }, etiq: [15, 134], lignes: ["Le", "bourg"],
        quoi: "Trois cent quarante âmes sous les murs : les séchoirs, les barques, la rue basse.",
        alias: [], motifs: ["bourg sous les murs", "le bourg"] },
      // ---- les onze salles de la proposition ---------------------------
      // Placées à la mesure (voir SEUIL_TOUS dans plan.js) : aucune étiquette
      // n'en touche une autre au seuil de densité. Les `etage` ont le droit de
      // se poser SUR leur salle mère — c'est l'idiome du plan, la Table Peinte
      // est dans le Tambour et l'archive sous la salle du levant.

      { id: "cuisines", nom: "Les cuisines",
        forme: { r: [46, 92, 42, 22, 4] }, etiq: [67, 105],
        lignes: ["Les cuisines"],
        quoi: "Feux, billots, le va-et-vient qui commence avant tout le monde. C'est ici qu'on sait le premier combien de bouches il y a en trop.",
        orne: ["chaudron", 78, 99, 5],
        alias: ["les cuisines"], motifs: ["cuisines", "cuisine"] },

      { id: "cellier", nom: "Le cellier", etage: "dessous",
        forme: { c: [58, 112, 9] }, etiq: [56, 120],
        lignes: ["Le cellier"],
        quoi: "Sous les cuisines, dans le roc : le grain, le sel, les tonneaux. Le chiffre des vivres se vérifie ici, pas au registre.",
        orne: ["tonneaux", 58, 108, 4],
        alias: ["le cellier"], motifs: ["cellier", "reserves"] },

      { id: "salle-froide", nom: "La salle froide", etage: "dessous",
        forme: { c: [112, 84, 9] }, etiq: [98, 84],
        lignes: ["La salle froide"],
        quoi: "Sous le septuaire, contre la roche : on y couche les morts en attendant le bûcher ou la mer. Il y fait froid même en été.",
        orne: ["cierge", 118, 92, 4],
        alias: ["la salle froide"], motifs: ["salle froide", "chapelle ardente"] },

      { id: "etuves", nom: "Les étuves", etage: "dessous",
        forme: { c: [180, 128, 12] }, etiq: [180, 128],
        lignes: ["Les étuves"],
        quoi: "Cuves, vapeur, le seul endroit du château où l'on est sans rang. On vient toujours vous y déranger.",
        orne: ["cuve", 180, 138, 4.5],
        alias: ["les étuves"], motifs: ["etuves", "etuve", "bain"] },

      { id: "chambre-enfants", nom: "La chambre des enfants", etage: "sommet",
        forme: { c: [246, 120, 12] }, etiq: [246, 120],
        lignes: ["Les", "enfants"],
        quoi: "Où couchent les princes. La porte à laquelle on frappe en dernier, et celle qu'on regarde en premier quand tout va mal.",
        orne: ["berceau", 246, 131, 4.5],
        alias: ["chambre des enfants"], motifs: ["chambre des enfants", "les enfants"] },

      { id: "antichambre", nom: "L'antichambre",
        forme: { r: [272, 116, 20, 54, 4] }, etiq: [282, 138],
        lignes: ["L'anti-", "chambre"],
        quoi: "Le banc contre le mur, devant la Table Peinte. On y attend d'être reçu, et l'on y apprend qui passe avant soi.",
        orne: ["banc", 282, 158, 4.5],
        alias: ["l'antichambre"], motifs: ["antichambre", "vestibule"] },

      { id: "officine", nom: "L'officine",
        forme: { r: [300, 78, 46, 22, 4] }, etiq: [323, 91],
        lignes: ["L'officine"],
        quoi: "Le cabinet du mestre, contre la roukerie : fioles, onguents, ce qui soigne et ce qui ne soigne pas.",
        orne: ["fiole", 310, 86, 5],
        alias: ["l'officine"], motifs: ["officine", "apothicaire"] },

      { id: "forge", nom: "La forge",
        forme: { r: [154, 262, 62, 16, 3] }, etiq: [185, 272],
        lignes: ["La forge"],
        quoi: "Contre la courtine : l'enclume, les carreaux, ce qu'on répare et ce qu'on arme. Elle chauffe depuis le sacre.",
        orne: ["enclume", 163, 270, 4],
        alias: ["la forge"], motifs: ["forge", "armurerie"] },

      { id: "chemin-ronde", nom: "Le chemin de ronde", dehors: true,
        forme: { d: "M354,82 L388,152 L374,238 L366,236 L380,152 L348,86 Z" },
        etiq: [398, 196], lignes: ["Chemin", "de ronde"],
        quoi: "Le haut de la courtine, face au large. On y marche à deux quand on ne veut pas être entendu, et le guet compte les voiles.",
        orne: ["creneaux", 378, 196, 5],
        alias: ["chemin de ronde"], motifs: ["chemin de ronde", "courtine", "rempart"] },

      { id: "lices", nom: "Les lices", dehors: true,
        forme: { r: [0, 200, 44, 46, 4] }, etiq: [22, 226],
        lignes: ["Les lices"],
        quoi: "Hors les murs : la quintaine, le sable, les jeunes qu'on entraîne. Ce qui s'y casse se sait le soir même.",
        orne: ["quintaine", 22, 210, 6],
        alias: ["les lices"], motifs: ["lices", "quintaine"] },

      { id: "greve", nom: "La grève", dehors: true,
        forme: { r: [150, 286, 66, 20, 3] }, etiq: [183, 299],
        lignes: ["La grève"],
        quoi: "Les vieux hangars à nefs, sous le château. Ce qui débarque discrètement ne passe pas par le quai.",
        orne: ["coques", 200, 296, 5],
        alias: ["la grève"], motifs: ["greve", "hangars"] },
    ],
  },

  // Port-Réal — le DONJON ROUGE, et la ville reléguée au bord.
  //
  // L'échelle « Le château » répond à « où suis-je, et qui est à trois portes de
  // moi » : elle doit donc montrer le Donjon Rouge salle par salle, pas la ville
  // vue de haut avec le château tassé dans un coin. La courtine tient le cadre,
  // les sept collines et les portes retombent en bande pâle hors les murs —
  // elles restent cliquables et reconnaissables par leurs `motifs`, mais ce
  // n'est plus le sujet du dessin. Pour ce qu'il y a hors les murs à portée de
  // voix, l'échelle « La ville » (etat/ville.json) existe et fait mieux.
  //
  // Dessiné du souvenir : la reine y a grandi. Ce qui est ici est de la
  // géographie, non du renseignement — les hommes, les relèves et les clefs
  // n'y sont pas, et c'est ce qui manque. Six portes sur les sept : la septième
  // attend qu'on nous la nomme.
  "port-real": {
    nom: "Port-Réal — le Donjon Rouge",
    viewBox: "0 0 460 340",

    fonds: [
      // la Néra au sud, la baie à l'est
      { classe: "plan-mer", d: "M0,320 Q120,312 240,320 Q344,328 460,314 L460,340 L0,340 Z" },
      { classe: "plan-mer", d: "M414,30 L460,24 L460,318 L412,316 Q400,178 408,104 Z" },
      // la colline d'Aegon : le château est posé dessus, et c'est elle qui
      // explique pourquoi l'on monte pour venir vous parler.
      { classe: "plan-roche", d: "M126,50 Q252,22 382,62 Q408,166 366,268 Q248,300 138,270 Q100,158 126,50 Z" },
    ],
    // La courtine du Donjon Rouge : huit pans, une tour à chaque angle.
    mur: "M150,72 L286,58 L370,96 L384,176 L352,252 L246,278 L146,258 L118,166 Z",
    guet: [[150, 72], [286, 58], [370, 96], [384, 176],
           [352, 252], [246, 278], [146, 258], [118, 166]],
    decor: [
      { classe: "plan-arete", d: "M26,44 L52,20 L78,44" },
      { classe: "plan-arete", d: "M16,142 L40,120 L64,142" },
      { classe: "plan-vague", d: "M22,332 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M160,336 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M300,330 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M424,238 q16,-7 32,0 q16,7 32,0" },
      { classe: "plan-vague", d: "M424,164 q16,-7 32,0 q16,7 32,0" },
    ],
    etiquettes: [
      { x: 122, y: 24, texte: "La ville", classe: "plan-large" },
      { x: 408, y: 272, texte: "La colline d'Aegon", classe: "plan-large" },
      { x: 62, y: 334, texte: "La Néra", classe: "plan-eau" },
      { x: 436, y: 74, texte: "La baie", classe: "plan-eau" },
    ],
    rose: [436, 322, 12],

    salles: [
      // ---- dans les murs -------------------------------------------------
      { id: "cour-donjon-rouge", nom: "La cour du Donjon Rouge", fond: true,
        forme: { d: "M150,72 L286,58 L370,96 L384,176 L352,252 L246,278 L146,258 L118,166 Z" },
        etiq: [312, 190], lignes: ["La cour"],
        quoi: "Tout ce qui entre au château y passe, et l'on y voit qui entre.",
        orne: ["puits", 312, 172, 7],
        alias: [], motifs: ["cour du donjon rouge"] },

      { id: "salle-du-trone", nom: "La salle du Trône", cle: true,
        forme: { c: [234, 142, 38] }, etiq: [234, 136],
        lignes: ["La salle", "du Trône"],
        quoi: "Le Trône de Fer, et la longue marche qu'il faut faire pour l'atteindre.",
        orne: ["tables", 234, 162, 7],
        alias: ["salle du Trône"], motifs: ["salle du trone", "trone de fer"] },

      { id: "tour-de-la-main", nom: "La tour de la Main", cle: true,
        forme: { c: [326, 146, 28] }, etiq: [326, 138],
        lignes: ["Tour de", "la Main"],
        quoi: "Là où l'on écrit ce qui se fera. La chancellerie du royaume tient dans cette tour.",
        orne: ["rouleau", 326, 162, 6],
        alias: ["tour de la Main"], motifs: ["tour de la main"] },

      { id: "petit-conseil", nom: "La chambre du petit conseil", etage: "sommet",
        forme: { c: [326, 150, 13] }, etiq: [326, 152], lignes: ["Le conseil"],
        quoi: "Sept sièges, une table longue : c'est là qu'on décide au nom du roi.",
        alias: ["petit conseil"], motifs: ["petit conseil"] },

      { id: "donjon-de-maegor", nom: "Le donjon de Maegor", cle: true,
        forme: { c: [258, 222, 38] }, etiq: [258, 212],
        lignes: ["Le donjon", "de Maegor"],
        quoi: "Un château dans le château : douves sèches, pieux de fer, un seul pont-levis.",
        orne: ["lances", 258, 244, 7],
        alias: ["donjon de Maegor"], motifs: ["donjon de maegor", "maegor"] },

      { id: "appartements-royaux", nom: "Les appartements royaux", etage: "sommet",
        forme: { c: [258, 226, 17] }, etiq: [258, 228], lignes: ["Le roi"],
        quoi: "Dans Maegor, donc derrière les pieux : on n'y entre que par le pont.",
        orne: ["lit", 258, 240, 5],
        alias: [], motifs: ["appartements royaux"] },

      { id: "tour-blanche", nom: "La Tour Blanche", cle: true,
        forme: { c: [164, 200, 24] }, etiq: [164, 194],
        lignes: ["La Tour", "Blanche"],
        quoi: "La tour de la Garde Royale : sept chambres, une table ronde, et le Livre Blanc où l'on écrit ce que chacun a fait.",
        orne: ["rouleau", 164, 214, 5],
        alias: ["Tour Blanche"], motifs: ["tour blanche", "garde royale"] },

      { id: "roukerie-port-real", nom: "La roukerie",
        forme: { c: [344, 206, 20] }, etiq: [344, 210], lignes: ["La roukerie"],
        quoi: "Tout ce que le royaume apprend d'eux part d'ici. Un seul canal, et il est à eux.",
        orne: ["corbeau", 344, 194, 6],
        alias: [], motifs: ["roukerie de port-real"] },

      { id: "septuaire-royal", nom: "Le septuaire royal",
        forme: { c: [206, 248, 19] }, etiq: [206, 246], lignes: ["Le septuaire"],
        quoi: "Sept autels, et les septons de la maison. On y prête et l'on y rompt.",
        orne: ["etoile", 206, 260, 5],
        alias: [], motifs: ["septuaire royal"] },

      { id: "bois-des-dieux-port-real", nom: "Le bois des dieux",
        forme: { r: [158, 78, 96, 22, 10] }, etiq: [206, 92], lignes: ["Le bois des dieux"],
        quoi: "Des ormes, un barral sans visage. On y parle sans être entendu.",
        orne: ["arbres", 176, 88, 4],
        alias: [], motifs: ["bois des dieux"] },

      { id: "cuisines-donjon-rouge", nom: "Les cuisines",
        forme: { r: [136, 118, 54, 20, 4] }, etiq: [163, 131], lignes: ["Les cuisines"],
        quoi: "Trois feux qui ne s'éteignent pas. C'est ici qu'on sait le premier combien de bouches il y a en trop au château.",
        orne: ["chaudron", 148, 128, 5],
        alias: [], motifs: ["cuisines du donjon rouge"] },

      { id: "cellier-donjon-rouge", nom: "Le cellier", etage: "dessous",
        forme: { c: [152, 144, 9] }, etiq: [152, 152], lignes: ["Le cellier"],
        quoi: "Sous les cuisines : le grain, le sel, les tonneaux. Un siège se compte là, pas au registre.",
        orne: ["tonneaux", 152, 140, 4],
        alias: [], motifs: ["cellier du donjon rouge"] },

      { id: "ecuries-donjon-rouge", nom: "Les écuries",
        forme: { r: [296, 230, 54, 20, 4] }, etiq: [323, 243], lignes: ["Les écuries"],
        quoi: "Contre la courtine, près de la poterne : qui fait seller à cette heure-ci ne passe pas inaperçu.",
        alias: [], motifs: ["ecuries du donjon rouge"] },

      { id: "promenade-des-traitres", nom: "La promenade des Traîtres",
        forme: { c: [164, 242, 15] }, etiq: [164, 244],
        lignes: ["Les", "Traîtres"],
        quoi: "La tour de guet et ses cellules hautes, au-dessus de la porte. On y garde ceux qu'on n'a pas encore décidé de tuer.",
        orne: ["barreaux", 164, 232, 4],
        alias: ["promenade des Traîtres"], motifs: ["promenade des traitres"] },

      { id: "geoles-noires", nom: "Les geôles noires", etage: "dessous",
        forme: { r: [190, 264, 100, 16, 4] }, etiq: [240, 276], lignes: ["Les geôles noires"],
        quoi: "Sous la colline, sans fenêtre. On y descend, on n'en remonte pas seul.",
        orne: ["barreaux", 202, 272, 4],
        alias: ["geôles noires"], motifs: ["geoles noires", "cachots de port-real"] },

      { id: "passages-maegor", nom: "Les passages", etage: "dessous",
        forme: { r: [214, 288, 142, 14, 4] }, etiq: [285, 299], lignes: ["Les passages"],
        quoi: "Maegor a fait tuer ceux qui les creusèrent. Une enfant qui y a joué s'en souvient mieux qu'un plan.",
        orne: ["colimacon", 228, 295, 4],
        alias: [], motifs: ["passages", "passages secrets"] },

      // ---- hors les murs : la ville, au bord du plan ----------------------
      // Elle n'est plus le sujet — elle borde. Ce qui compte ici, c'est de
      // savoir de quel côté du château elle se trouve et par où l'on y entre.
      { id: "fosse-aux-dragons", nom: "La fosse aux dragons", cle: true, dehors: true,
        forme: { c: [52, 42, 30] }, etiq: [52, 34],
        lignes: ["La fosse", "aux dragons"],
        quoi: "Sur la colline de Rhaenys, sous le grand dôme. C'est là qu'on a couronné Aegon.",
        orne: ["flamme", 52, 58, 6],
        alias: ["fosse aux dragons"], motifs: ["fosse aux dragons", "colline de rhaenys"] },

      { id: "colline-visenya", nom: "La colline de Visenya", dehors: true,
        forme: { c: [40, 152, 26] }, etiq: [40, 146],
        lignes: ["La colline", "de Visenya"],
        quoi: "La troisième colline, à l'ouest : les septs, et la ville qui monte autour.",
        orne: ["etoile", 40, 166, 5],
        alias: ["colline de Visenya"], motifs: ["colline de visenya"] },

      { id: "rue-de-la-soie", nom: "La rue de la Soie", dehors: true,
        forme: { r: [6, 196, 74, 18, 4] }, etiq: [43, 208], lignes: ["La rue de la Soie"],
        quoi: "Les maisons de plaisir. On y sait des choses avant le petit conseil.",
        orne: ["toiles", 18, 205, 4],
        alias: ["rue de la Soie"], motifs: ["rue de la soie"] },

      { id: "culpucier", nom: "Le Culpucier", dehors: true,
        forme: { r: [4, 228, 84, 30, 6] }, etiq: [46, 246], lignes: ["Le Culpucier"],
        quoi: "Le fond de la ville : la soupe brune, les ruelles, et le premier endroit qui a faim.",
        orne: ["paillasses", 26, 240, 4],
        alias: ["Culpucier"], motifs: ["culpucier"] },

      { id: "guilde-alchimistes", nom: "La guilde des alchimistes", dehors: true,
        forme: { c: [46, 292, 20] }, etiq: [46, 288],
        lignes: ["Les", "alchimistes"],
        quoi: "Les pyromants et leurs caves. Ils comptent leurs jarres et ne les montrent pas.",
        orne: ["flamme", 46, 304, 5],
        alias: ["guilde des alchimistes"], motifs: ["alchimistes", "pyromants"] },

      { id: "guet-port-real", nom: "La caserne du guet", cle: true, dehors: true,
        forme: { r: [104, 300, 68, 18, 4] }, etiq: [138, 312], lignes: ["Le guet"],
        quoi: "Deux mille manteaux d'or. Ce sont eux, et non les murs, qui décident qui entre.",
        orne: ["lances", 116, 309, 4],
        alias: ["manteaux d'or"], motifs: ["caserne du guet", "manteaux d'or", "le guet"] },

      { id: "quais-de-la-nera", nom: "Les quais de la Néra", dehors: true,
        forme: { r: [196, 302, 116, 16, 4] }, etiq: [254, 314], lignes: ["Les quais"],
        quoi: "Le port de rivière : quatre cinquièmes de ce que la ville mange arrive là.",
        orne: ["nef", 210, 310, 5],
        alias: [], motifs: ["quais de la nera", "le port de port-real"] },

      // Le chantier de la vase, la cabane, la grève basse et la Mérette ne sont
      // PAS ici : ils appartiennent au plan `port-real@marlo-vasse`. Une reine
      // qui a grandi au Donjon Rouge ne sait pas qu'un brise-coques tient une
      // aire sous la porte de la Gadoue — l'écrire sur SA carte serait la
      // première fuite du brouillard, et sur une carte on ne la verrait pas.

      // ---- les portes ----------------------------------------------------
      { id: "porte-de-la-gadoue", nom: "La porte de la Gadoue", cle: true, dehors: true,
        forme: { r: [330, 296, 58, 14, 3] }, etiq: [359, 307], lignes: ["Porte de la Gadoue"],
        quoi: "Elle ouvre sur le port. Tout ce qui se mange dans cette ville la franchit.",
        orne: ["herse", 339, 303, 3.4],
        alias: ["porte de la Gadoue"], motifs: ["porte de la gadoue"] },

      { id: "porte-du-roi", nom: "La porte du Roi", cle: true, dehors: true,
        forme: { r: [0, 104, 42, 14, 3] }, etiq: [21, 115], lignes: ["Porte du Roi"],
        quoi: "L'ouest, et la route royale. On y compte les cavaliers qui entrent.",
        orne: ["herse", 9, 111, 3.4],
        alias: ["porte du Roi"], motifs: ["porte du roi"] },

      { id: "porte-des-dieux", nom: "La porte des Dieux", dehors: true,
        forme: { r: [86, 6, 50, 14, 3] }, etiq: [111, 17], lignes: ["Porte des Dieux"],
        quoi: "Le nord-ouest. Les pèlerins, les charrettes, et ce qui vient du Conflans.",
        orne: ["herse", 95, 13, 3.4],
        alias: ["porte des Dieux"], motifs: ["porte des dieux"] },

      { id: "porte-vieille", nom: "La Porte Vieille", dehors: true,
        forme: { r: [186, 4, 46, 14, 3] }, etiq: [209, 15], lignes: ["Porte Vieille"],
        quoi: "La plus ancienne, et la plus étroite. Deux chariots n'y passent pas de front.",
        orne: ["herse", 195, 11, 3.4],
        alias: ["Porte Vieille"], motifs: ["porte vieille"] },

      { id: "porte-de-fer", nom: "La porte de Fer", dehors: true,
        forme: { r: [318, 10, 46, 14, 3] }, etiq: [341, 21], lignes: ["Porte de Fer"],
        quoi: "Le nord-est, vers la route de Sombreval et de Rosby.",
        orne: ["herse", 327, 17, 3.4],
        alias: ["porte de Fer"], motifs: ["porte de fer"] },

      { id: "porte-du-lion", nom: "La porte du Lion", dehors: true,
        forme: { r: [0, 258, 44, 14, 3] }, etiq: [22, 269], lignes: ["Porte du Lion"],
        quoi: "Le sud-ouest, vers la Néra en amont et les gués.",
        orne: ["herse", 9, 265, 3.4],
        alias: ["porte du Lion"], motifs: ["porte du lion"] },
    ],
  },

  // Port-Réal vu de la vase — le plan de Marlo Vasse.
  //
  // Ce n'est pas la même ville que celle d'au-dessus, et c'est le sujet. Le plan
  // de la reine met le Donjon Rouge au centre et jette la boue au bord ; celui-ci
  // fait l'inverse, parce qu'un homme qui casse des coques entre deux marées ne
  // vit pas dans un château — il vit sur trois cents pas de vase, et le château
  // est une chose lointaine qu'il n'a jamais vue de près.
  //
  // Ce qui décide de la place des choses, ici, c'est LA MARÉE : le mur au nord,
  // l'eau au sud, et entre les deux une bande qui se découvre deux fois par jour
  // et se reprend deux fois par jour. Tout ce qui compte est posé sur cette
  // bande-là, et rien n'y est à personne — c'est pour cela qu'on peut y tenir
  // une base sans qu'aucun seigneur ait à le permettre, et c'est pour cela
  // qu'on peut tout y perdre en une nuit sans que personne ait à le décider.
  "port-real@marlo-vasse": {
    nom: "Le chantier de la vase",
    viewBox: "0 0 560 420",

    fonds: [
      // la ville, au-dessus du mur : de la terre ferme, et elle n'est pas à lui
      { classe: "plan-roche", d: "M0,0 L560,0 L560,72 L0,64 Z" },
      // la vase : ce qui n'est ni la ville ni la rivière, et qui change deux
      // fois par jour de camp
      { classe: "plan-vase", d: "M0,272 Q150,262 306,274 Q440,284 560,268 L560,372 Q432,384 300,374 Q150,362 0,374 Z" },
      // la Néra
      { classe: "plan-mer", d: "M0,352 Q150,340 300,352 Q432,362 560,346 L560,420 L0,420 Z" },
    ],

    // La muraille de Port-Réal, vue du dehors et par en dessous : elle ne
    // l'enferme pas, elle lui bouche le nord. Pas de tours de guet sur ce
    // plan — il n'en a jamais monté une, et ce qu'on n'a pas vu ne se dessine
    // pas. Le crénelage est posé à la main, du seul côté qu'il regarde.
    mur: "M40,78 L540,86 L540,98 L40,90 Z",
    guet: [],

    decor: [
      // les merlons, face sud — ceux qu'on voit d'en bas, gate exceptée
      { classe: "plan-merlon", d: "M40,90 v3.2" },
      { classe: "plan-merlon", d: "M81.7,90.7 v3.2" },
      { classe: "plan-merlon", d: "M123.3,91.3 v3.2" },
      { classe: "plan-merlon", d: "M165,92 v3.2" },
      { classe: "plan-merlon", d: "M206.7,92.7 v3.2" },
      { classe: "plan-merlon", d: "M373.3,95.3 v3.2" },
      { classe: "plan-merlon", d: "M415,96 v3.2" },
      { classe: "plan-merlon", d: "M456.7,96.7 v3.2" },
      { classe: "plan-merlon", d: "M498.3,97.3 v3.2" },
      { classe: "plan-merlon", d: "M540,98 v3.2" },
      // les rigoles de la vase : l'eau qui se retire laisse toujours les mêmes
      { classe: "plan-vague", d: "M64,286 q22,16 14,38 q-8,22 10,40" },
      { classe: "plan-vague", d: "M196,284 q18,18 8,40 q-10,20 6,42" },
      { classe: "plan-vague", d: "M448,282 q-16,18 -6,40 q10,20 -6,40" },
      // la Néra
      { classe: "plan-vague", d: "M36,372 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M196,378 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M380,370 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M120,404 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
      { classe: "plan-vague", d: "M320,406 q16,-7 32,0 q16,7 32,0 q16,-7 32,0" },
    ],

    etiquettes: [
      { x: 462, y: 40, texte: "Port-Réal, dedans", classe: "plan-large" },
      { x: 118, y: 300, texte: "La vase", classe: "plan-large" },
      { x: 208, y: 414, texte: "La Néra", classe: "plan-eau" },
      { x: 500, y: 232, texte: "Vers l'amont", classe: "plan-eau" },
    ],
    // Posée dans l'eau au sud-ouest. Le plan est orienté comme la marée :
    // la ville en haut, le large en bas.
    rose: [42, 392, 13],

    salles: [
      // ---- l'aire, dessinée d'abord : c'est le sol de tout le reste --------
      { id: "chantier-de-la-vase", nom: "Le chantier de la vase", fond: true, cle: true,
        forme: { r: [84, 160, 296, 140, 8] },
        etiq: [232, 178], lignes: ["L'aire de bris"],
        quoi: "Trois cents pas de vase où l'on démonte les coques mortes, planche par planche, entre deux marées. Vingt-deux bouches en vivent.",
        alias: ["chantier de la vase", "l'aire de bris", "le chantier"],
        motifs: ["chantier de la vase", "aire de bris", "le chantier", "l'aire"] },

      // ---- au-delà du mur : la ville, qui n'est pas à lui ------------------
      { id: "culpucier", nom: "Le Culpucier", dehors: true,
        forme: { r: [36, 10, 164, 30, 6] }, etiq: [118, 30], lignes: ["Le Culpucier"],
        quoi: "Le fond de la ville. C'est de là que descendent ceux qui n'ont plus rien à vendre que leurs bras — et il en descend plus chaque semaine.",
        orne: ["paillasses", 60, 25, 4],
        alias: ["Culpucier"], motifs: ["culpucier"] },

      { id: "etal-de-sirel", nom: "L'étal de Sirel", dehors: true,
        forme: { r: [236, 14, 148, 28, 4] }, etiq: [310, 32], lignes: ["L'étal de Sirel"],
        quoi: "Le bois du chantier s'y vend à la planche, et le fer au poids. Elle tient les comptes — dont onze dragons d'or contre la coque du chantier.",
        orne: ["tonneaux", 256, 28, 4],
        alias: ["l'étal de Sirel"], motifs: ["etal de sirel", "les marches", "le marche"] },

      // ---- la porte, et l'homme qui est dessous ---------------------------
      { id: "porte-de-la-gadoue", nom: "La porte de la Gadoue", cle: true,
        forme: { r: [232, 66, 96, 34, 4] }, etiq: [280, 82], lignes: ["Porte de la Gadoue"],
        quoi: "La seule porte qui compte : tout ce qui se mange dans cette ville la franchit, et tout ce qui sort du chantier aussi.",
        orne: ["herse", 248, 90, 4],
        alias: ["porte de la Gadoue", "la Gadoue"], motifs: ["porte de la gadoue", "la gadoue"] },

      { id: "arche-de-waltyr", nom: "L'ombre de l'arche",
        forme: { c: [280, 114, 17] }, etiq: [280, 112], lignes: ["L'arche"],
        quoi: "Waltyr Poix s'y tient du matin au soir, hors du vent. Deux cerfs la semaine, et personne au-dessus de lui ne l'a jamais su.",
        orne: ["lances", 280, 122, 4],
        alias: ["l'ombre de l'arche"], motifs: ["ombre de l'arche", "l'arche"] },

      { id: "bureau-du-port", nom: "Le bureau du maître de port", cle: true, dehors: true,
        forme: { r: [332, 102, 96, 26, 4] }, etiq: [380, 119], lignes: ["Les rôles"],
        quoi: "Les rôles d'entrée : tout ce qui remonte la Néra y est écrit d'une main. Ollo Marran tient la plume, et le rôle du dix-neuf est faux.",
        orne: ["rouleau", 350, 115, 4],
        alias: ["les rôles d'entrée", "le bureau du maître de port"],
        motifs: ["bureau du maitre de port", "les roles", "maitre de port"] },

      // ---- dans l'aire ----------------------------------------------------
      { id: "la-cale", nom: "La cale", cle: true,
        forme: { c: [144, 222, 32] }, etiq: [144, 216], lignes: ["La cale"],
        quoi: "Le plan incliné où l'on hale une coque à la marée haute pour la casser à la basse. Une seule à la fois : c'est ce qui fixe le rythme de tout.",
        orne: ["coques", 144, 236, 5],
        alias: ["la cale"], motifs: ["la cale", "le ber"] },

      { id: "la-carcasse", nom: "La carcasse",
        forme: { c: [228, 216, 29] }, etiq: [228, 210], lignes: ["La", "carcasse"],
        quoi: "Ce qui reste de la coque en cours : membrures à nu, le pont ôté. On dort dedans quand il pleut, et l'on y parle sans être vu de la porte.",
        orne: ["nef", 228, 230, 5],
        alias: ["la carcasse"], motifs: ["la carcasse"] },

      { id: "la-forge", nom: "La forge",
        forme: { c: [318, 220, 24] }, etiq: [318, 216], lignes: ["La forge"],
        quoi: "On y redresse le fer tiré des coques : clous, chevilles, cercles. Un feu qui brûle tous les jours n'étonne personne — c'est ce qui le rend utile.",
        orne: ["enclume", 318, 230, 5],
        alias: ["la forge"], motifs: ["la forge"] },

      { id: "les-paillasses", nom: "Les paillasses",
        forme: { r: [96, 258, 98, 26, 4] }, etiq: [145, 274], lignes: ["Les vingt-deux"],
        quoi: "Sous un toit de planches récupérées. Ils mangent au chantier et dorment au chantier : c'est le salaire, autant que les cerfs.",
        orne: ["paillasses", 114, 270, 4],
        alias: [], motifs: ["les paillasses", "les vingt-deux"] },

      { id: "le-feu-de-l-aire", nom: "Le feu de l'aire",
        forme: { c: [216, 266, 16] }, etiq: [216, 264], lignes: ["Le feu"],
        quoi: "Le brai qu'on fond, la soupe qu'on tient chaude. Il ne s'éteint pas, et c'est autour de lui qu'on apprend la moitié de ce qu'on sait.",
        orne: ["flamme", 216, 273, 4],
        alias: [], motifs: ["le feu de l'aire", "le feu"] },

      { id: "le-tas-de-planches", nom: "Le tas de planches",
        forme: { r: [274, 252, 98, 26, 4] }, etiq: [323, 268], lignes: ["Le bois"],
        quoi: "Le stock, empilé à hauteur d'homme. C'est la seule richesse visible du chantier — et la seule chose que Sirel Quintaine puisse saisir.",
        orne: ["tonneaux", 292, 264, 4],
        alias: [], motifs: ["le tas de planches", "le bois"] },

      // ---- la cabane : sa chambre, son bureau, son coffre -----------------
      { id: "cabane-du-peigne", nom: "La cabane du Peigne", cle: true,
        forme: { c: [50, 206, 29] }, etiq: [50, 200], lignes: ["La", "cabane"],
        quoi: "Une porte, un banc, un coffre sous le banc. C'est là qu'on écrit ce qu'on a appris, et personne d'autre n'y entre.",
        orne: ["rouleau", 50, 216, 5],
        alias: ["cabane du Peigne", "la cabane"], motifs: ["cabane du peigne", "la cabane"] },

      // ---- ce qui descend du mur, et ce qui longe l'eau -------------------
      { id: "le-boyau", nom: "Le Boyau", dehors: true,
        forme: { r: [4, 252, 74, 26, 4] }, etiq: [41, 268], lignes: ["Le Boyau"],
        quoi: "La ruelle qui descend de la ville à la vase, trop étroite pour une charrette. Les gosses de Nel Bec y remontent quand la marée prend tout.",
        orne: ["toiles", 20, 264, 4],
        alias: ["le Boyau"], motifs: ["le boyau"] },

      { id: "le-ru-de-la-gadoue", nom: "Le ru de la Gadoue", etage: "dessous",
        forme: { d: "M436,96 L456,96 L470,300 L450,302 Z" },
        etiq: [462, 206], lignes: ["Le ru"],
        quoi: "Ce que la ville rejette sort là, sous le mur, et descend à la Néra. Voûté sur trente pas : on y passe courbé, et le guet n'y va jamais.",
        orne: ["barreaux", 452, 240, 4],
        alias: ["le ru de la Gadoue", "le ru"], motifs: ["ru de la gadoue", "le ru"] },

      { id: "greve-basse", nom: "La grève basse", cle: true,
        forme: { r: [24, 304, 340, 30, 4] }, etiq: [194, 323], lignes: ["La grève basse"],
        quoi: "Découverte deux fois par jour. Trente gosses la peignent pour la ferraille, et la marée reprend tout ce qu'on n'a pas ramassé avant.",
        orne: ["toiles", 48, 319, 4],
        alias: ["la grève basse"], motifs: ["greve basse", "la greve", "la vase"] },

      { id: "quais-de-la-nera", nom: "Les quais de la Néra", dehors: true,
        forme: { r: [396, 306, 150, 28, 4] }, etiq: [471, 324], lignes: ["Les quais"],
        quoi: "Le vrai port, en amont : quatre cinquièmes de ce que la ville mange y débarque. On n'y casse rien, on y décharge — et l'on y compte.",
        orne: ["nef", 416, 320, 5],
        alias: [], motifs: ["quais de la nera", "les quais"] },

      // ---- ce qui flotte --------------------------------------------------
      { id: "la-merette", nom: "La Mérette", cle: true,
        forme: { c: [112, 382, 25] }, etiq: [112, 378], lignes: ["La", "Mérette"],
        quoi: "Coque de pêche. Remonte à Peyredragon tous les six jours et repart le lendemain — la seule chose ici qui touche l'autre bout de la baie.",
        orne: ["nef", 112, 392, 5],
        alias: ["la Mérette", "Mérette"], motifs: ["la merette", "merette"] },

      { id: "le-chien-de-mer", nom: "Le Chien de Mer",
        forme: { c: [300, 384, 28] }, etiq: [300, 378], lignes: ["Le Chien", "de Mer"],
        quoi: "Grosse coque au mouillage depuis huit jours, qui ne décharge rien. Nel Bec a compté cent vingt lances en descendre la nuit du vingt-deuxième.",
        orne: ["ondes", 300, 396, 5],
        alias: ["le Chien de Mer"], motifs: ["chien de mer"] },

      { id: "le-mouillage", nom: "Le mouillage des mortes",
        forme: { r: [402, 366, 144, 26, 4] }, etiq: [474, 382], lignes: ["Le mouillage"],
        quoi: "Les coques qui attendent leur tour de cale. On les paie au tonneau, on les prend à la marée, et l'une d'elles coule toujours avant.",
        orne: ["coques", 422, 378, 4],
        alias: [], motifs: ["le mouillage", "mouillage des mortes"] },
    ],
  },
};
