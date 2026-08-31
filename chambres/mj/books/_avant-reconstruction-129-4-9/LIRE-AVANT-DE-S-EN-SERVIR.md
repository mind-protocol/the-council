# CE DOSSIER NE CONTIENT PAS D'« AVANT ». Ne restaure rien depuis ici.

Son nom promet l'état antérieur ; il porte l'état **postérieur au vidage** — le
creux, pas le plein.

## La preuve, et je corrige la mienne : ce n'est PAS un argument de taille

J'avais d'abord écrit ici que les onze fichiers étaient « identiques octet pour
octet » à ceux du dossier parent, sur la foi des tailles égales au `ls`. **C'est
faux, et je m'étais interdit exactement cette faute** — un diagnostic qu'on
n'essaie pas de casser. Un `cmp` l'a cassé en un coup : les fichiers **diffèrent**
(`affaire-la-montre.json`, char 5778). La bonne preuve est le `diff`, et elle
dit l'inverse de ce que la taille laissait croire :

    diff  chambres/mj/books/affaire-le-brouillard.json \
          chambres/mj/books/_avant-reconstruction-129-4-9/affaire-le-brouillard.json

    < "B.14"                                    ← le fichier VIVANT
    < "🕳️ **LIVRER N'EST PAS FAIRE SAVOIR …**"
    ---
    > ""                                         ← la « sauvegarde »
    > ""

**Le vivant porte les numéros et les libellés ; la copie d'ici porte le vide.**
Restaurer depuis ce dossier, c'est effacer la reconstruction en cours. Les
tailles étaient égales parce qu'un JSON indenté change peu de longueur quand on
remplace deux courtes chaînes par deux chaînes vides sur des lignes déjà là.

## Ce que ce dossier vaut, et c'est réel

Il est le **témoin daté du creux**, avant que quiconque y remette la main. À ce
titre il ne se jette pas : il sert à mesurer ce qui a été reconstruit et ce qui
ne l'est pas encore. Mais il ne se restaure pas.

## Où est le véritable « avant »

Nulle part sur le disque. `etat/histoire/empreintes.json` a été écrasée à
**04h49m45s** par la passe qui journalisait la perte au même instant. Le vidage
lui-même est de **04h16** : tout ce qui est daté d'après cette minute est du
sinistre, quel que soit son nom de dossier.

**Une sauvegarde ne vaut ni par son nom ni par sa taille : par un `diff`.**
