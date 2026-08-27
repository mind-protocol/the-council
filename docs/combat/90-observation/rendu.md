# Rendu

## 1. Ce que c'est

Ce qui doit être visible à l'écran, par acteur, pour qu'**une capture suffise à
diagnostiquer une mauvaise décision à une seconde donnée.**

## 2. Ce qu'il possède

- **La liste de ce qui est montré par type d'acteur**, et la source de chaque
  chose montrée — toujours une trace ou une donnée possédée, jamais une valeur
  recalculée pour l'affichage.
- **Les états d'affichage** : ce qui est allumé, ce qui est masqué, à quel niveau
  de détail. Cela appartient à l'écran et à personne d'autre.
- **L'empreinte de ce qui est réellement servi** : de quelle version du code
  vient l'image qu'on regarde.

## 3. Ce qu'il lit

Tout, et d'abord les traces de décision. Le monde pour les obstacles et les
seuils, les unités pour leur forme, le commandement et la conduite pour ce
qu'ils croient et ce qu'ils ont ordonné.

## 4. Ce qu'il produit

Ce qui doit être visible, par acteur :

- **un chef** : la phrase de son ordre, **seulement quand il la prononce** ;
- **un combattant** : au survol, ce qu'il essaie et pourquoi, avec la couche qui
  le conduit — lue de sa trace ;
- **une unité** : son ancre, son front, sa route, sa cohésion, l'allure de son
  guide ;
- **un commandant** : son champ de vision, ses croyances **avec leur âge**,
  l'option retenue et celles écartées avec leur motif ;
- **la conduite** : les buts courants et leur poids, les missions ouvertes avec
  leur état, la réserve et sa portée ;
- **le monde** : les obstacles, les seuils, la densité, les points bloqués.

Et une sortie de contrôle : **l'empreinte servie**, lisible à l'écran, pour
qu'on sache quelle version on regarde.

## 5. Invariants

- **Une capture suffit à diagnostiquer une mauvaise décision à une seconde
  donnée.** Si elle ne suffit pas, il manque une trace — pas un panneau de plus.
- Tout ce qui est affiché est justifiable par une trace ou par une donnée
  possédée. Aucune valeur calculée pour l'écran seul.
- Ce qu'un acteur affiche penser sort de ce qui le conduit réellement.
- Une croyance affichée montre son âge ; sans âge, elle se lit comme un fait.
- Ce qui est servi porte une empreinte dérivée de son contenu, et cette empreinte
  est visible. Sinon on regarde peut-être hier.
- Le brouillard tient à l'écran comme ailleurs : ce qui montre plus que ce qu'un
  acteur sait est déclaré comme vue d'observation, jamais mêlé à sa vue.

## 6. Ce qu'il ne fait pas

- **Il n'écrit rien dans la simulation.** Ouvrir un panneau, survoler un homme,
  allumer un calque : rien de tout cela ne touche la bataille, et rien ne
  consomme l'urne.
- **Il ne calcule rien qui décide.** Aucune valeur affichée n'est produite par
  l'écran ; il montre ce qu'on lui remet.
- **Il n'est lu par aucun module de la simulation.** Un moteur qui dépend de ce
  qui est affiché ne se mesure plus hors écran.
- **Il ne comble pas les trous.** Une donnée absente s'affiche absente ; une
  valeur de remplacement fait passer un défaut de trace pour un état.
- **Il ne fait pas parler un chef en continu.** La phrase d'ordre paraît quand
  elle est prononcée, et disparaît ; un bandeau permanent n'est plus une trace.
- **Il ne remplace pas les sondes.** Ce qu'on voit sur trois hommes ne dit rien
  d'une distribution sur deux mille.

## 7. Ce que l'ancien moteur faisait mal ici

**Vérifier dans un onglet de navigateur neuf ne disait rien du cache.** Le code
changeait, le joueur voyait l'ancien, et les mesures en ligne de commande ne
pouvaient pas l'attraper puisqu'elles lisent le disque. Rien à l'écran ne disait
quelle version était servie — d'où l'empreinte visible exigée plus haut.

Le reste des grandeurs de cette fiche — part des décisions diagnosticables sur
une seule capture, part des croyances affichées avec leur âge — **n'a pas été
mesuré** sur le moteur précédent.
