# Sondes

## 1. Ce que c'est

Les mesures prises **de l'extérieur**, en regardant la troupe entre deux pas, et
les mesures prises sur l'architecture elle-même. Une sonde regarde ; elle ne
touche rien.

## 2. Ce qu'il possède

- **La définition de chaque sonde** : ce qu'elle mesure, sur quel sous-ensemble,
  à quelle cadence, et **dans quel régime** — à l'arrêt, à la marche, en déroute,
  au contact. Le régime est dans la définition, pas dans le commentaire.
- **Les relevés** produits, avec leur distribution : jamais une seule valeur
  agrégée, toujours de quoi voir si la variété s'est effondrée.
- **Le plafond de chaque instrument**, déclaré : ce qu'il ne peut pas voir.

## 3. Ce qu'il lit

Tout : le monde, les corps, les unités, la transmission, le commandement, la
conduite, les traces. C'est le privilège de la couche, et son seul privilège.

## 4. Ce qu'il produit

**Les sondes de comportement**, chacune dans un régime déclaré :

- **téléports** — tout déplacement d'un pas au-delà du possible, avec son auteur ;
- **corps dans le bâti** — hommes vivants dans une emprise infranchissable ;
- **routes par homme** — combien d'itinéraires calculés par homme et par minute ;
- **densité** — la valeur, et surtout **la durée au-dessus de chaque seuil** ;
- **dispersion au chef** — l'étalement des membres autour de leur guide ;
- **hommes sans un pair de leur unité** à portée — la mesure de l'émiettement ;
- **hommes arrêtés à portée d'un ennemi** — le contact qui ne se ferme pas.

**Les sondes d'architecture**, du même rang que les précédentes :

- aucune dépendance ne remonte une couche ;
- aucun module ne dépasse sa taille sans justification écrite ;
- aucune globale partagée ;
- un seul écrivain par donnée du tableau de propriété ;
- un seul manifeste, et tous les consommateurs le lisent.

## 5. Invariants

- **Une sonde ne compare qu'à état comparable.** Une mesure qui agrège tous les
  régimes compare ce qui n'est pas comparable, et le chiffre est faux même quand
  il est bien calculé.
- **Une sonde déclare son plafond.** Ce qu'un instrument ne peut pas voir doit
  être écrit à côté de ce qu'il voit, sinon son zéro se lit comme une absence.
- **Une mesure ne dépend pas de la distribution qu'elle observe** : elle
  discrimine encore quand les valeurs se rangent.

## 6. Ce qu'il ne fait pas

- **Elle n'écrit rien dans la simulation.** Ni champ, ni compteur, ni marqueur
  « déjà vu ». Une sonde qui vit dans le moteur modifie ce qu'on cherche à
  laisser intact, et fausse l'étalon qu'elle prétend servir.
- **Elle ne corrige rien** : un téléport détecté est compté, pas annulé.
- **Elle ne juge pas** : dire si le comportement est bon est aux épreuves.
- **Elle n'est lue par personne dans la simulation.** Aucun module des couches 10
  à 80 ne consulte une sonde ; sinon la couche 90 est devenue une dépendance.

## 7. Ce que l'ancien moteur faisait mal ici

**Une sonde comparait deux régimes différents** : la vitesse de pointe de
fantassins *en déroute* contre celle de cavaliers *à la marche*, et concluait que
la cavalerie était trop lente. À état comparable, le rapport était correct — la
sonde était fausse, pas le moteur.

**La sonde de téléport avait un plafond de 8 m/s**, non déclaré. Elle ne pouvait
donc pas voir un second écrivain de vitesse qui produisait 3,6 m/s hors des
règles : l'instrument rendait zéro là où il n'y avait que de l'aveuglement.

**Une mesure est tombée de 27 % à 0 %** non par accord mais par effondrement de
la variété : les deux valeurs comparées s'étaient rangées sur la même réponse. Un
chiffre flatteur qui s'est lu comme une réussite.

**Une vérification faite dans un onglet de navigateur neuf ne disait rien du
cache** : le code changeait, le joueur voyait l'ancien, et les mesures en ligne de
commande ne pouvaient pas l'attraper puisqu'elles lisent le disque.
