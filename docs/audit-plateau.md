# Audit du plateau — ce que Hearthstone fait, et ce que nous ne faisons pas

Le plateau du conseil de guerre (`ecrans/modules/partie.js`, note de conception :
[`partie.md`](partie.md)) a été refait trois fois en une session sans devenir
lisible. Ce document sert à sortir de la boucle : au lieu de proposer encore une
maquette, on liste **les mécanismes d'interface d'un jeu de cartes qui marche**,
un par un, et l'on dit pour chacun ce que notre plateau en a.

Hearthstone est le point de comparaison parce que c'est le jeu de cartes dont
l'interface est la plus documentée, et parce que son designer d'interface résume
sa position en trois mots — **« our game is UI »** : l'interface n'est pas la
couche qui montre le jeu, elle EST le jeu.

**Sur les sources.** Le détail des décisions vient de la conférence GDC 2015
« Hearthstone: How to Create an Immersive User Interface » (Derek Sakamoto), qui
n'est pas transcrite en accès libre — je ne l'ai pas lue. Ce qui suit est sourcé
sur le wiki de jeu et sur les articles de design listés en fin de document ;
**ce qui vient de ma seule observation du jeu est marqué ⟨obs⟩**, et vaut ce que
vaut une observation.

Verdicts : **✅ on l'a** · **⚠️ à moitié** · **❌ absent** · **∅ sans objet ici**.

---

## 1 · Ce qui dit « voilà ce que tu peux faire, maintenant »

| Mécanisme | Ce que Hearthstone fait | Chez nous |
|---|---|---|
| **Halo des cartes jouables** | Toute carte, tout pouvoir et tout serviteur qu'on peut jouer ou commander **est cerclé d'un halo vert, en permanence**. On n'a jamais à calculer si on a les moyens : on regarde ce qui brille. | ⚠️ **à moitié, et c'est le trou le plus grave.** Nos cibles ne s'allument que *pendant* le glissé. Au repos, rien ne distingue une pièce qu'on peut poser d'une pièce gelée : il faut lire « se remet · 4 j » en 10,5 px sous la carte. Le joueur doit calculer ce que l'écran devrait montrer. |
| **Cristaux de mana** | Une rangée de cristaux dit le budget du tour, à l'œil, sans un chiffre à lire. Le coût est en haut à gauche de chaque carte : la comparaison est immédiate. | ❌ **absent.** Notre budget existe — *un coup par camp et par tour*, et les pièces libres — mais il n'est écrit nulle part. Le joueur ne sait pas qu'il n'a droit qu'à un coup avant de l'avoir joué deux fois et d'avoir lu l'avertissement. |
| **Flèche de ciblage** | Quand une carte demande une cible, une flèche part de la carte et suit le curseur ; les cibles valides sont désignées. Le lien entre l'acteur et sa cible est **dessiné**. | ❌ absent. On allume les cibles, sans tracer le lien. ⟨obs⟩ Sur un plateau à six colonnes, allumer six choses ne dit pas où l'on va. |
| **Bouton de fin de tour qui s'allume** | Le bouton passe au halo vert **quand il n'y a plus rien à faire**. Le jeu dit « tu as fini », le joueur n'a pas à s'en assurer. | ∅ / ❌ Nous avons supprimé le bouton du jour, à raison — le monde tourne, on ne clique pas dessus. Mais l'information « vous n'avez plus rien à poser » reste due au joueur, et personne ne la donne. |

## 2 · Ce qui dit l'état d'une carte — sans une ligne de texte

C'est le point où l'écart est le plus net, et c'est **une différence de nature,
pas de soin** : Hearthstone encode l'état dans l'IMAGE de la carte, nous
l'écrivons en toutes lettres sous la carte.

| État | Hearthstone ⟨obs⟩ | Chez nous |
|---|---|---|
| ne peut pas encore agir | le serviteur **dort** — des ✦ tournent au-dessus de lui | « dans 4 j » en petit gris |
| a déjà agi | la carte est **grisée et éteinte** | « posée », et un liseré |
| gelé | la carte est **prise dans un bloc de glace** | « se remet · 4 j » |
| protégé | un **bouclier doré** sur le portrait | ∅ |
| provocation | une **barrière de pierre** devant le serviteur | ∅ (nos gardes sont un mot) |
| renforcé | les chiffres passent au **vert et grossissent** | ∅ |
| détruit | la carte **se brise en morceaux** et quitte le plateau | titre barré |

**Le principe à retenir** n'est pas « ajouter des dessins ». C'est que **l'état
d'une carte se lit sur la carte, à distance, sans lecture** — et que chaque état
a sa forme propre, donc qu'on distingue « pas encore prêt » de « déjà servi » du
premier coup d'œil. Chez nous, six états passent par le même filet de texte de
10,5 px au même endroit : ils sont indiscernables sans lire.

## 3 · Ce qui donne le détail sans encombrer

| Mécanisme | Hearthstone | Chez nous |
|---|---|---|
| **Survol qui agrandit** | On survole n'importe quelle carte, **n'importe où** — main, plateau, adversaire — et elle s'affiche en grand avec tout son texte. | ❌ absent. |
| **La carte posée se réduit** | Une carte jouée sur le plateau **change de forme et perd presque toute son information** ; le détail revient au survol. C'est ce qui permet à huit serviteurs de tenir sans bouillie. | ❌ absent — et c'est la clé de la dispute qu'on vient d'avoir. Nos cartes posées gardent leur forme entière : ou bien on les garde et c'est illisible, ou bien on les supprime et le geste disparaît. **La troisième voie est celle-là**, et elle n'existe que si le survol rend le détail. |

Ces deux lignes vont ensemble et ne valent rien séparément : **on ne peut réduire
une carte que si l'on sait où le détail est parti.**

## 4 · Ce qui dit ce qui presse

| Mécanisme | Hearthstone | Chez nous |
|---|---|---|
| **La corde qui brûle** | Aux vingt dernières secondes, **une mèche traverse le plateau et se consume**. Aucun chiffre, aucune alerte : une chose brûle. | ❌ absent. Nos échéances — une frappe qui atterrit, une pièce qui arrive, un gel qui tombe — sont dispersées dans les cartes, à égalité avec ce qui ne bouge pas. |

⟨obs⟩ La leçon de la mèche est qu'**une urgence est un objet du monde qui change,
pas une pastille rouge**. Une pastille « ⏳ 2 j » serait notre version programmeur
de la corde.

## 5 · Ce qui rend le geste physique

| Mécanisme | Hearthstone | Chez nous |
|---|---|---|
| **Le plateau est un objet** | Un coffre de taverne, avec des charnières, des loquets, des choses qu'on peut tripoter sans effet sur la partie. Le choix est explicitement **skeuomorphique** et contre le plat. Des joueurs ont fabriqué le coffre en vrai. | ⚠️ Le jeu entier a ce parti pris — parchemin, encre, blasons — mais le plateau du conseil est le seul écran qui ressemble à un formulaire. |
| **Chaque animation a un impact** | Poser une carte pèse : elle atterrit, le plateau accuse le coup, un son la valide. | ❌ absent. Un coup joué chez nous change un attribut CSS. |
| **Le poids et le son** | Le retour sonore double chaque geste. | ∅ pour l'instant. |

## 6 · Ce qui dit ce que l'autre fait

| Mécanisme | Hearthstone | Chez nous |
|---|---|---|
| **Le survol de l'adversaire est visible** | Quand l'adversaire survole une carte, **elle s'éclaire en rouge sur votre écran**. On voit l'autre hésiter. | ∅ notre adversaire est le MJ, pas un humain en ligne. |
| **Le coup adverse se joue à l'écran** | On voit la carte sortir de sa main, se poser, agir. | ❌ **absent, et c'est un trou de jeu, pas d'interface.** Rien ne montre ce que les Verts ont fait. On l'apprend en relisant le plateau et en cherchant ce qui a changé. |

---

## Ce que cet audit tranche

Cinq manques, classés par ce qu'ils coûtent au joueur — pas par ce qu'ils coûtent
à écrire.

1. **Le survol qui rend le détail.** Sans lui, aucune réduction des cartes posées
   n'est possible, et l'on tourne en rond entre « illisible » et « amputé ».
   C'est le préalable de tout le reste.
2. **L'état montré au lieu d'être écrit.** Une pièce gelée, en route, posée,
   perdue doivent se distinguer sans lecture. C'est six textes à remplacer par
   quatre traitements visuels distincts.
3. **Le halo permanent des pièces jouables**, au repos et pas seulement pendant
   le glissé — plus le budget du tour (un coup) rendu visible.
4. **Le coup adverse rejoué**, pour qu'on voie ce qui vient de nous être fait.
5. **Les échéances rendues physiques**, une seule chose qui change à l'écran,
   pas une rangée de pastilles.

Les points 1 et 2 vont ensemble et se tiennent en une passe. Le point 3 est
petit. Le 4 est une question de jeu avant d'être une question d'écran — il
touche à ce que le MJ pousse au flux quand les Verts jouent. Le 5 attendra.

**Ce qu'il ne faut PAS refaire**, et qui a été essayé dans cette session : un
cadre de plus, un mot d'état en capitales au-dessus d'une colonne, une ligne qui
récapitule une chaîne, une colonne d'objectifs. Toutes ces réponses ajoutent une
annotation au lieu de changer l'objet. **Un état s'encode dans la chose, jamais
dans une étiquette posée à côté d'elle** — c'est la seule ligne de cet audit qui
vaut pour tout ce qu'on fera ensuite.

---

## Sources

- [Video: Designing an immersive user interface for Hearthstone](https://www.gamedeveloper.com/design/video-designing-an-immersive-user-interface-for-i-hearthstone-i-) — Game Developer, la conférence de Derek Sakamoto (« our game is UI ») ; la conférence elle-même est sur [GDC Vault](https://gdcvault.com/play/1022036/Hearthstone-How-to-Create-an) et n'est pas transcrite.
- [Gameplay — Hearthstone Wiki](https://hearthstone.wiki.gg/wiki/Gameplay) — le halo vert des cartes jouables, le survol, le bouton de fin de tour, la corde de 75 secondes.
- [Mulligan — Hearthstone Wiki](https://hearthstone.fandom.com/wiki/Mulligan) — le survol partagé entre les deux joueurs.
- [The Card Games UI Design of Fairtravel Battle](https://gdkeys.com/the-card-games-ui-design-of-fairtravel-battle/) — « une carte posée change de forme et se réduit au minimum », les zones de jeu définies, le détail en infobulle plutôt que sur la carte.
- [It's all in the cards: UX/UI card design](https://uxdesign.cc/its-all-in-the-cards-ux-ui-card-design-44cf9e31d988) — hiérarchie de l'information sur une carte.
- [Progressive disclosure](https://uxuiprinciples.com/en/principles/progressive-disclosure) — montrer l'essentiel, garder le reste à un geste.
