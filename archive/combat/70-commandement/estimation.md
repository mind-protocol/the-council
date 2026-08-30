# Estimation

## 1. Ce que c'est

Ce qu'un chef déduit de ses seules croyances : où il en est, ce qui le menace, et
ce qui lui manque pour décider.

## 2. Ce qu'il possède

- **Le rapport de force tel qu'il le croit**, en intervalles et non en ratio
  net : ce qu'il a d'engageable ici contre ce qu'il croit avoir en face. Un
  rapport déduit d'intervalles reste un intervalle.
- **La menace** : ce qui peut lui arriver, d'où, dans combien de temps. Une
  direction, un délai, une confiance — pas une note.
- **La vulnérabilité** : ce qu'il expose et ne couvre pas — flanc, arrière,
  seuil, liaison avec un voisin.
- **La pression sur ses corps** : fatigue, cohésion, pertes. Croyance encore.
- **Ce qui manque pour décider** : la liste explicite des inconnues dont la levée
  changerait le choix. C'est ce qui rend une reconnaissance justifiable.

## 3. Ce qu'il lit

Du socle : horloge, mesures. Du monde : le terrain, pour convertir une distance
en délai et savoir ce qui couvre ou expose ; les seuils, parce qu'une porte change
une menace. De l'unité : ce qu'un corps de tel effectif et de telle forme peut
encaisser — des capacités génériques, pas l'état réel d'un corps qu'il ne voit
pas. **Des croyances du commandant, et d'elles seules**, pour la situation.

Il ne lit **aucun état réel du camp adverse**, ni les croyances d'un autre
commandant. Deux chefs voisins peuvent estimer la même situation de deux façons
opposées, et c'est le sujet.

## 4. Ce qu'il produit

- **Un état estimé**, daté, avec l'âge de la plus vieille croyance qui le fonde.
- **Les inconnues qui décideraient**, chacune avec ce qu'il faudrait pour la
  lever : envoyer voir, attendre un rapport, demander à un voisin.
- **Un degré de confiance** : ce sur quoi l'estimation repose, et ce qui
  là-dedans est vieux ou de seconde main.

## 5. Invariants

- **Toute estimation cite ses croyances.** Une sonde extérieure vérifie qu'aucune
  conclusion ne s'appuie sur une donnée absente de la carte du chef.
- Une estimation fondée sur des croyances vieilles se déclare telle : on n'est
  pas sûr d'un rapport de force calculé sur un rapport d'il y a dix minutes.
- Une zone inconnue produit une inconnue explicite, jamais une hypothèse
  favorable par défaut.
- **Toute sortie de ce module est lue par un autre.** Une grandeur estimée que
  personne ne consomme est supprimée, pas conservée.

## 6. Ce qu'il ne fait pas

- **Il ne propose aucune action.** Il dit où l'on en est, pas quoi faire.
- **Il ne classe pas les options** et ne pondère rien en vue d'un choix.
- **Il n'écrit pas dans les croyances.** Une déduction n'est pas un fait ; si
  elle doit en devenir une, elle y entre comme déduction enregistrée.
- **Il ne prête pas d'intention à l'ennemi comme si c'était une donnée** : une
  intention supposée est une hypothèse, jamais un fait.
- **Il ne produit pas d'étiquette globale.** Un mot unique résumant la posture
  d'un chef est précisément ce qu'on ne veut plus — voir la section 7.

## 7. Ce que l'ancien moteur faisait mal ici

C'est la faute la plus exactement documentée du dossier. **Le seul module qui
déduisait quelque chose des croyances produisait un champ « posture » écrit et LU
NULLE PART** — une déduction calculée à chaque battement, consommée par personne.

L'effet en aval est mesuré : sur quinze chefs, **zéro ordre adapté** à une
observation, alors que le renseignement circulait — **41 observations typées de
cavalerie**, **94 de longues hampes**, **478 communications entre chefs** sur une
seule bataille. La chaîne s'arrêtait précisément ici. Deux contraintes dures en
découlent :

- **Aucune sortie de ce module ne se livre sans son consommateur.** L'invariant
  « toute sortie est lue » n'est pas une élégance, c'est la sonde qui aurait fait
  tomber la posture le jour où elle a été écrite.
- **On ne remplace pas une déduction par un mot.** « Posture » agrégeait en une
  étiquette ce qui devait rester un rapport chiffré, une menace datée et une
  liste d'inconnues. Un chef ne décide pas depuis un adjectif.
