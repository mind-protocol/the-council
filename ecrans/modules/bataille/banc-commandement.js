// La faculté seule : aucune ville, aucune formation, aucun moteur.
"use strict";
const C = require("./commandement.js");
let echecs = 0;
function ok(dit, tenu) { if (!tenu) echecs++; console.log((tenu ? "ok  " : "NON ") + dit); }

const a = C.memoire({ proprietaire:"chef-a", echelon:"aile", camp:"rouge" });
const b = C.memoire({ proprietaire:"chef-b", echelon:"aile", camp:"rouge" });
C.recevoirOrdre(a, "Tenez le gué.", 0);
C.recevoirOrdre(b, "Prenez la rive.", 0);
C.assimiler(a, { id:"vue:1", genre:"ennemi", sujet:{ genre:"zone", id:"gue" },
  statut:"actif", position:{ x:11, y:1 }, forceMin:8, forceMax:12,
  signatures:{ montes:{ min:3, max:5 }, longuesHampes:{ min:6, max:9 } },
  source:"vu", auteur:"chef-a", observeA:10 }, 10);

ok("un ordre reçu reste littéral", a.ordre.texte === "Tenez le gué.");
ok("voir n'informe pas magiquement le voisin", b.faits.size === 0 && b.croyances.size === 0);
const recus = C.transmettre(a, b, { maintenant:20 });
ok("la parole transmet le fait", recus.length === 1 && b.croyances.size === 1);
const cb = [...b.croyances.values()][0];
ok("la provenance racine survit à la parole",
  cb.source === "dit" && cb.apprisDe === "chef-a" && cb.auteur === "chef-a");
ok("les signatures observées survivent à la parole sans devenir un type omniscient",
  cb.signatures.montes.min === 3 && cb.signatures.longuesHampes.max === 9);
ok("une parole est moins certaine que la vue",
  C.confiance(cb, 20) < C.confiance([...a.croyances.values()][0], 20));
ok("le renseignement rapporté vieillit", C.confiance(cb, 300) < C.confiance(cb, 20));
const e = C.estimation(b, 20, 20);
ok("l'estimation rapporte force propre et fourchette ennemie",
  e.forcePropre === 20 && e.forceMin > 0 && e.forceMax >= e.forceMin && e.lieux === 1);
ok("l'estimation agrège chevaux et longues hampes avec la confiance",
  e.signatures.montes.min > 0 && e.signatures.longuesHampes.max > 0);

const champ = C.champVision({ position:{ x:0, y:0 }, rayon:20, rayons:48, pas:.5,
  obstacle:(x,y) => x >= 5 && x <= 6 && Math.abs(y) <= 3 });
ok("un obstacle retire des directions au champ subjectif",
  champ.bloques > 0 && champ.bloques < champ.rayons.length);
ok("ce qui est derrière le masque n'est pas visible",
  !C.visibleDansChamp(champ, { x:12, y:0 }) &&
   C.visibleDansChamp(champ, { x:0, y:12 }));

const graphe = C.grapheTactique(a, { maintenant:20, position:{ x:0, y:0 },
  objectif:{ x:20, y:0, nom:"le gué" }, champ });
ok("la carte expose ses croyances et son objectif comme un graphe sélectionnable",
  graphe.noeuds.some((n)=>n.type==="ennemi") &&
  graphe.noeuds.some((n)=>n.type==="objectif") && graphe.liens.length >= 3);
ok("le graphe conserve les indices sans coder une doctrine d'arme",
  graphe.noeuds.some((n)=>n.signatures&&n.signatures.longuesHampes) &&
  !graphe.liens.some((l)=>/pique|cavaler|contourn/i.test(l.type)));

console.log(echecs ? "\n✗ " + echecs + " NON" : "\n✓ aucun NON");
process.exit(echecs ? 1 : 0);
