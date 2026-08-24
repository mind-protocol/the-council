# -*- coding: utf-8 -*-
"""Ouvre le cahier de la porte de mer (Wend, office O08). Ecriture atomique."""
import os, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import bibliotheque

O = ['\U0001f9f1 Le champ', "✍️ Ce qu'on y écrit", '\U0001f4d6 La règle du champ', '✅ Rempli ?']

ouverture = [
 ["\U0001f3f7️ **LE NOM**",
  "La porte de mer — ce qu'un homme porte quand il entre, ce qui ressort, et ce qu'on refuse. Le sujet est LE SEUIL, non les gens qui le franchissent : qui ils sont et pourquoi ils viennent est au rôle et aux nouvelles, et je n'y touche pas.",
  "Le sujet dont le conseil traite, **jamais la solution**.", "**oui**"],
 ["\U0001f3af **L'OBJET**",
  "Onze ans que je tiens cette porte et elle n'a jamais eu de cahier. **Cinq pas dont mon office répond vivent dans cinq cahiers d'autres hommes** — 41020, 32025, 25121, 11029, 39031 — et sur les quatre qui restent à faire, **la case du jour dû est vide sur les quatre** ; personne ne me les porte, et je ne les ai vus qu'en les cherchant. Pendant ce temps ma charge est écrite NON BORNÉE au registre des offices, sans sceau de la reine ni marque de qui décide, et je refuse ou laisse passer trente hommes par jour sur ma seule parole. Ce cahier n'ouvre rien de neuf : il ramasse ce qui était déjà à moi et qui n'était nulle part.",
  "Une phrase : pourquoi cette affaire mérite l'attention du conseil.", "**oui**"],
 ["\U0001f9f1 **LE PÉRIMÈTRE — DANS**",
  "Le seuil de la porte de mer, des deux côtés de l'arche. Le livre du jour : ce qui entre, ce qui sort (seconde colonne tracée le 28e au matin), et le compte des refus. Le compte des débarquements, pris de ma bouche le 28e à dix heures trente-cinq. Les six hommes du poste que le maître de port peut lever sur sa seule parole, et leurs six remplaçants, tenus au dos du rôle. La borne écrite de ma charge et les deux sceaux qui manquent.",
  "Ce qui appartient à l'affaire, énuméré.", "**oui**"],
 ["\U0001f6ab **LE PÉRIMÈTRE — HORS**",
  "**QUI est l'homme et pourquoi il vient** : ce n'est pas ma case, le registre l'écrit noir sur blanc — je ne refuse ni sur le nom ni sur la mine. Les grèves et les mouillages de nuit, qui sont à Rulf Corne (O05). La fouille des coques, qui m'a été retirée le 28e à midi et passée à Onn du Levant : je ne la redemande pas. Le plan lui-même — j'ai demandé à n'en rien savoir, et compter des ballots ne m'en apprend pas un mot. Les quatre actions des autres cahiers : **je les cite par leur numéro et je n'en déplace pas une.**",
  "Ce qui n'y appartient pas, énuméré aussi. C'est la moitié qu'on oublie.", "**oui**"],
 ["\U0001f4cc **L'ÉTAT ACTUEL**",
  "— **Une mesure existe depuis le 28e** : le compte des refus, écrit chaque nuit sur la page du jour, relu chaque semaine par le castellan. Premier chiffre : neuf refusés dans la nuit du 27e au 28e, nommés avec leur motif. **Mais le registre des offices du plan porte encore « AUCUNE ÉCRITE » sur ma ligne O08** — le plan ne compte donc pas cette porte comme tenue. — Les deux sceaux de ma charge sont NON APPOSÉS, avec la mention « à borner AVANT LA FIN DE LA LUNE (OF.5) ». **La 3e lune est close depuis deux jours.** — Le compte des débarquements m'a été donné le 28e et attend le sceau de Sa Grâce depuis cinq jours. — **CE QUE J'IGNORE ET QUE JE N'INVENTE PAS** : combien de nuits, depuis le 28e, la porte a été tenue par un seul homme — je n'ai pas relu mon livre à l'envers ; et sur quoi exactement j'ai refusé les neuf de cette nuit-là, autrement que par ma mémoire et les mots que j'ai écrits sans règle.",
  "Ce qu'on sait, et ce qu'on avoue ignorer. **Jamais ce qu'on espère faire.**", "**oui**"],
 ["\U0001f522 **LA PLAGE**", "**46000 à 46900**",
  "Réservée d'avance ; vérifiée libre au 2e de la 4e lune — aucune pièce en 46xxx dans aucun des cent vingt-neuf volumes.", "**oui**"],
 ["\U0001f4a1 **LA CONCLUSION**",
  "**Ce que j'ai compris en cherchant, et que je n'aurais pas trouvé à ma porte : ce rocher a déjà inventé le remède, et ne l'a pas appliqué chez moi.** Quand ser Robert a vu que six hommes pouvaient lui être pris la nuit sans qu'il le sache, il n'a pas demandé six hommes de plus : il a **nommé les six d'avance et nommé six remplaçants avec eux**, et cela n'a coûté que douze noms au dos du rôle. Le même trou est ouvert à mon seuil et personne ne l'a vu, parce qu'il ne s'ouvre qu'aux heures où c'est MOI qui m'absente — la nuit du 27e au 28e, onze personnes sont passées sans qu'un nom soit écrit pendant que je fouillais une coque, et l'on m'a retiré la fouille. On m'a ensuite donné le compte des débarquements, qui me retire du seuil chaque matin à l'heure où l'on parle, **et personne n'a nommé l'homme qui tient l'arche pendant ce temps-là.** On a soigné la cause et rouvert la même plaie neuf jours plus tard.",
  "", ""],
 ["\U0001f51a **FERMÉE QUAND**",
  "Quand ma ligne au registre des offices porte les deux sceaux sur une borne écrite, et que la page du jour rend ses trois nombres — entrés, sortis, refusés — sans que personne ait à monter les chercher, huit jours de suite.",
  "Écrit à l'ouverture, à froid : à quoi l'on verra qu'il n'y a plus lieu de rouvrir ce cahier.", "**oui**"],
]

liees = [
 ["porte pour eux", "Ce qui part, et par où", "\U0001f3af 46100", "⚔️ 41020",
  "Le nom du patron de barque est sorti de ma bouche le 1er de la 4e. C'est ma porte qui l'a donné ; ma porte n'avait pas de cahier où l'écrire. Faite."],
 ["porte pour eux", "La protection du secret", "\U0001f3af 46000", "⚔️ 32025",
  "Compter qui monte, et pas seulement qui porte une épée — en cours à mon seuil avec Nesta Ourse. Mon verrou 46002 est le revers de cette action."],
 ["porte pour eux", "Entrée et déploiement de l'ost dans les rues", "\U0001f3af 46000", "⚔️ 25121",
  "Chronométrer six chevaux et deux chariots à mon arche, dû J−14. **Jour dû vide.**"],
 ["porte pour eux", "Le jour d'entrée", "\U0001f3af 46100", "⚔️ 11029",
  "Recueillir l'accusé daté de chaque titulaire, dû J−46. **Jour dû vide.**"],
 ["porte pour eux", "Ce qui ferait renoncer", "\U0001f3af 46000", "⚔️ 39031",
  "H13 : compter chaque semaine les entrants inconnus de ma porte. C'est mon compte, il vit dans leur cahier."],
]

etats = [
 ["**46000**", "\U0001f6aa La porte de mer rend son compte sans qu'on vienne le chercher",
  "Trois nombres sur la page du jour, écrits la nuit même et dits à sept heures : **entrés · sortis · refusés**. Une nuit sans page se voit à la page blanche, et non à la mémoire d'un homme",
  "Le poste de la porte de mer, et la table de sept heures",
  "Un homme qui n'était pas là ouvre le livre à une date et dit les trois nombres sans demander à personne",
  "32000 · 39000 · 25100"],
 ["**46100**", "\U0001f56f️ Ce que cette porte refuse tient devant un témoin",
  "La charge est bornée par écrit et porte les deux sceaux ; et il existe une liste courte, affichée au poste, de ce qui fait refuser une charge — **sur la charge, jamais sur le nom ni sur la mine**",
  "Registre des offices, ligne « La porte de mer » ; et le montant du poste",
  "Un patron de barque qui conteste un refus s'entend lire une règle datée, et non la parole d'un sergent",
  "32000 · 41000"],
]

verrous = [
 ["**46001**", "\U0001f464 Le seuil retombe à un seul homme dès que le sergent fait autre chose", "46000 · 46100",
  "La fouille des coques m'a été retirée le 28e à midi pour cette raison même : pendant que je fouillais, **la porte a été tenue par un seul homme de deux à quatre heures et onze personnes sont passées sans qu'un nom soit écrit**. Puis, le même jour à dix heures trente-cinq, on m'a donné le compte des débarquements à dire tout haut chaque matin — et **rien n'écrit qui tient l'arche pendant que je le dis**",
  "Registre des offices, ligne « La porte de mer » (motif de la retraite de la fouille) et ligne « Commandement du quai » (ma condition, portée le 28e). Les deux sont de la même journée",
  "Un homme nommé d'avance ET son remplaçant tiennent le seuil à l'heure du compte, écrits au dos du rôle comme les six du maître de port"],
 ["**46002**", "\U0001f9fe Le compte des non-armés tient à une seule femme, et elle est prêtée", "46000",
  "Nesta Ourse, peseuse aux claies, s'assied à ma porte — **prise sur les séchoirs de Willa en pleine saison du sel**, et non sur la garnison. Aucune remplaçante n'est nommée. La note de l'action le dit elle-même : si Nesta manque, je compte les têtes sans les nommer et l'on perd les noms",
  "⚔️ 32025, colonnes « Office » et « Note ». Deux cents personnes en six jours n'entrent nulle part sans elle",
  "Ou bien une seconde main est nommée derrière moi, ou bien le conseil accepte de n'avoir que le nombre — et on le dit ainsi, au lieu de le découvrir le jour où elle manque"],
 ["**46101**", "\U0001f58b️ Ni sceau ni marque, et le délai d'OF.5 est passé de deux jours", "46100",
  "Ma ligne au registre des offices porte, aux deux cases de sceau : **NON APPOSÉ — charge à borner AVANT LA FIN DE LA LUNE (OF.5)**, et « Wend n'a ni sceau ni marque, et refuse ou laisse passer trente hommes par jour ». Cette lune-là est close depuis avant-hier. Rien n'a été apposé",
  "Règles du gouvernement, OF.5, et sa note qui me nomme ; registre des offices, ligne « La porte de mer », colonnes des deux sceaux. Nous sommes au 2e jour de la 4e lune",
  "Une borne écrite de ma main est portée à ser Robert, puis les deux sceaux sont apposés à MA ligne — OF.6 : un sceau s'inscrit à la ligne de la charge dont il répond, et nulle part ailleurs"],
 ["**46102**", "\U0001f4dc Rien n'écrit sur QUOI l'on refuse", "46100",
  "Je décide seul de fouiller, de refuser et de retenir une heure, et il m'est défendu de refuser sur le nom ou sur la mine. Mais **aucune ligne, nulle part, ne dit sur quoi l'on refuse**. Les neuf motifs de la nuit du 27e au 28e sont de ma main et de mon jugement ; ils sont écrits, ils ne sont mesurés par rien. Le jour où un refus est contesté devant témoin, il n'y a qu'un sergent contre un patron",
  "Cherché ce matin aux règles du gouvernement et au registre des offices : la case n'existe pas. Ce qui est écrit dit ce que je ne peux pas faire, jamais ce qui suffit à refuser",
  "Une liste courte, tirée de mes propres refus relus à l'envers, relue par le castellan et affichée au poste"],
]

clefs = [
 ["**46010**", "\U0001f501 La règle des remplaçants, appliquée au seuil", "46001 · 46002",
  "Ce rocher a déjà inventé le remède et l'a appliqué ailleurs : six hommes nommés d'avance, **six remplaçants nommés avec eux**, tenus prêts au poste, et la règle écrite de ce qui retranche un homme du compte. Je ne demande donc pas un homme de plus — je demande que la même règle couvre **l'heure où c'est le sergent qui s'absente**, qui est la seule qu'on n'ait pas couverte",
  "Deux noms, et un quart d'heure de ser Robert. Pas un homme de plus sur un rocher qui est à cent dix-neuf pour un plancher de cent vingt",
  "Ferme la brèche de la nuit du 27e au 28e pour de bon, au lieu de la déplacer d'une charge à l'autre",
  "Deux noms au dos du rôle, et une nuit vérifiée sans heure à un seul homme",
  "retenue"],
 ["**46110**", "\U0001f4c4 Ne pas demander le sceau : apporter la page à sceller", "46101 · 46102",
  "Ser Robert a écrit lui-même le 28e : « je ne scellais pas ce qui n'était pas noir sur blanc ; ça l'est ». Une charge attend son sceau depuis onze ans parce que personne n'a écrit la charge, et ce n'est pas au castellan d'écrire ce que fait ma porte — c'est à moi. **J'écris la borne et je la porte ; il scelle ou il corrige**",
  "Une demi-journée de ma main, et j'y écris ce que je NE décide pas — ce qui rétrécit ma porte autant que ça l'assoit",
  "Ferme le reproche d'avance : OF.5 dit que jusqu'à la borne, ce que je scelle engage la reine seule. Après elle, ça m'engage moi, et c'est bien ainsi",
  "Une page datée à ma ligne du registre, et les deux sceaux dessus",
  "retenue"],
]

A = ['⚔️ N°', "\U0001f3f7️ L'action", '\U0001f5dd️ Réalise', "\U0001f4dd Ce qu'on fait",
     '\U0001f4cd Où', '\U0001fab6 Office', '\U0001f9f0 Moyens', '\U0001f527 Avec quoi',
     "\U0001f4b0 Ce qu'elle coûte", '⛓️ Dépend de', '\U0001f441️ La preuve', '⏳ État',
     '\U0001f4c5 Jour fait', '\U0001f4dd Note', '\U0001f4c5 Jour dû']

actions = [
 ["**46020**", "\U0001f50d Relire mon propre livre à l'envers, nuit par nuit, depuis le 28e", "46010",
  "Non pas qui est entré, mais **combien d'heures l'arche a été tenue par un seul homme** — et à quelle heure. C'est le seul chiffre qui dise si la brèche du 27e était une nuit ou une habitude. Le maître des rôles a rendu un marchand introuvable en relisant son rôle à l'envers un après-midi : le geste se copie",
  "Le poste de la porte de mer", "O08 — Wend", "M12", "Mon livre du jour et une planchette",
  "**Wend, un après-midi** · une fois · engagé le 2e de la 4e", "—",
  "Un nombre d'heures par nuit, sur six nuits, écrit sous le compte des refus",
  "à faire", "", "Ma seule action qui ne demande rien à personne : je la fais dans mon creux de l'après-midi",
  "3e jour de la 4e lune"],
 ["**46021**", "\U0001f5e3️ Faire nommer l'homme du seuil pour l'heure du compte, et son remplaçant", "46010",
  "Porter à ser Robert le chiffre de 46020 et lui demander **deux noms, pas un homme** : celui qui tient l'arche pendant que je dis le compte des débarquements, et celui qui le remplace. Écrits au dos du rôle, à côté des six du maître de port, sous la même règle de ce qui retranche un homme",
  "Poste de la porte de mer, puis la muraille", "O08 — Wend, avec O01 — ser Robert Quince", "",
  "Un quart d'heure de ser Robert",
  "**¼ journée de ser Robert et de Wend** · une fois · engagé le 3e de la 4e", "46020",
  "Deux noms au dos du rôle, et le maître de port averti comme il l'a été pour les six",
  "à faire", "",
  "Si ser Robert dit non faute d'hommes, la réponse s'écrit ici et le verrou 46001 reste ouvert au vu de tous — ce qui vaut mieux qu'un trou qu'on croit bouché",
  "5e jour de la 4e lune"],
 ["**46022**", "\U0001f9fe Trancher le compte des non-armés : une seconde main, ou le nombre sans les noms", "46010",
  "Aller au maître des rôles avec Nesta Ourse et poser la question une fois : ou bien on lui nomme une remplaçante comme aux six du port, ou bien le conseil sait dès aujourd'hui qu'il n'aura que le nombre le jour où elle manquera. **Je ne veux pas de la troisième réponse, qui est de n'y pas penser**",
  "Sous la voûte, et à mon seuil", "O08 — Wend, avec O02 — le Sanglier", "",
  "Le rôle, et la planchette qui ne s'efface pas",
  "**¼ journée** · une fois · engagé le 5e de la 4e", "—",
  "Un nom de remplaçante au dos du rôle, ou une phrase datée disant qu'on se passe des noms",
  "à faire", "", "", "6e jour de la 4e lune"],
 ["**46120**", "\U0001f58b️ Écrire la borne de la porte de mer en une page, de ma main", "46110",
  "Les quatre cases d'un office, telles que la règle les demande : ce dont je réponds, ce que je décide seul, ce que je ne décide pas, et à quoi l'on me juge. J'y porte la mesure qui tient déjà — le compte des refus, écrit chaque nuit, relu chaque semaine — **et les trois nombres de 46000**. Puis je la porte à ser Robert pour qu'il scelle ou corrige",
  "Le poste de la porte de mer, puis la muraille", "O08 — Wend", "M12", "Un feuillet et une plume",
  "**½ journée de Wend** · une fois · engagé le 2e de la 4e", "—",
  "Une page datée à ma ligne du registre des offices, et les deux cases de sceau remplies",
  "à faire", "",
  "OF.5 me nomme dans sa note et me donnait jusqu'à la fin de la 3e lune. Je suis en retard de deux jours, et le retard est de ma main : personne ne m'avait dit d'écrire, et je n'ai pas demandé",
  "4e jour de la 4e lune"],
 ["**46121**", "\U0001f4dc Tirer de mes propres refus la liste courte de ce qui fait refuser", "46110",
  "Reprendre un par un les neuf refusés de la nuit du 27e au 28e, et ranger chaque motif sous un mot. Ce qui revient trois fois est une règle ; ce qui ne revient qu'une fois est un jugement, et se dit tel. **Sur la charge, jamais sur l'homme.** Relue par le castellan, puis clouée au montant du poste, du côté où entrent les gens",
  "Le poste de la porte de mer", "O08 — Wend, relue par O01 — ser Robert Quince", "M12",
  "Le livre du jour, et un feuillet cloué",
  "**½ journée de Wend, et une relecture** · une fois · engagé le 4e de la 4e", "46120",
  "Une liste datée au montant du poste, et le premier refus contesté qui s'y arrête",
  "à faire", "", "", "5e jour de la 4e lune"],
]


def L(rows):
    return [{"cellules": r} for r in rows]


livre = {
 "id": "affaire-porte-de-mer",
 "titre": "La porte de mer",
 "sous_titre": "\U0001f6aa Affaire ouverte le 2e jour de la 4e lune, an 129, à la porte de mer de Peyredragon, de la main de WEND, sergent, onze ans en charge (office O08). Le sujet est LE SEUIL : ce qu'un homme porte quand il entre, ce qui ressort, ce qu'on refuse — jamais qui il est. Plage 46000 à 46900.",
 "type": "plan",
 "embleme": "\U0001f6aa",
 "couleur": "#4a5b63",
 "boite": "boite-sujets",
 "tenu_par": "wend",
 "office": "O08",
 "pages": [
  "**CE CAHIER N'OUVRE RIEN DE NEUF.** Il ramasse ce qui était déjà à mon office et qui n'était écrit nulle part chez moi : cinq pas qui vivent dans cinq cahiers d'autres hommes, une mesure née le 28e que le registre du plan ignore encore, et une charge que la règle OF.5 devait borner avant la fin de la lune passée. Je n'ai déplacé aucune ligne d'aucun autre livre. Ce qui est aux autres est cité par son numéro, et rien de plus.\n\n**CE QUE JE NE METS PAS DEDANS, ET C'EST LE POINT.** Qui entre, et pourquoi. Ce n'est pas ma case, le registre le dit : je ne refuse ni sur le nom ni sur la mine. J'ai demandé à ne rien savoir du plan quand on m'a donné le compte des débarquements, et l'on me l'a accordé. Un homme qui tient une porte et qui sait pourquoi les gens la franchissent commence à choisir, et ce jour-là la porte ne vaut plus rien."
 ],
 "tables": [
  {"titre": "\U0001f3f0 Ouverture de l'Affaire", "colonnes": O, "lignes": L(ouverture)},
  {"titre": "\U0001f517 Affaires liées — les liens écrits, puis les calculés",
   "colonnes": ['\U0001faa2 Le lien', "\U0001f517 L'affaire", '\U0001f522 Notre pièce', '\U0001f522 La leur', '\U0001f4dd Pourquoi'],
   "lignes": L(liees)},
  {"titre": "\U0001f3af États cibles",
   "colonnes": ['\U0001f3af N°', "\U0001f3f7️ L'état", '✅ Ce qui doit être vrai', '\U0001f4cd Où', '\U0001f441️ La preuve', '⬆️ Sert'],
   "lignes": L(etats)},
  {"titre": "\U0001f512 Verrous",
   "colonnes": ['\U0001f512 N°', '\U0001f3f7️ Le verrou', '⛔ Bloque', "\U0001f4cc Ce qui est vrai aujourd'hui", '\U0001f441️ La preuve', '\U0001f513 Levé quand'],
   "lignes": L(verrous)},
  {"titre": "\U0001f5dd️ Clefs",
   "colonnes": ['\U0001f5dd️ N°', '\U0001f3f7️ La clef', '\U0001f513 Ouvre', '\U0001f4a1 Le principe', '\U0001f4b0 Le prix', '\U0001f6aa Ce que cela ferme', '\U0001f441️ La preuve attendue', '⚖️ Décision'],
   "lignes": L(clefs)},
  {"titre": "⚔️ Actions", "colonnes": A, "lignes": L(actions)},
 ],
}

session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
books = session_livres.livres
if any(v.get("id") == livre["id"] for v in books):
    raise SystemExit("DEJA LA - rien fait")
books.append(livre)
session_livres.sauver()
print("cahier ouvert :", livre["id"], "-", len(books), "volumes")
