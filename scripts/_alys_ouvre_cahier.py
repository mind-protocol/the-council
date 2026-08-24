# -*- coding: utf-8 -*-
"""Alys Grive, O10, ouvre son cahier — 2e jour de la 4e lune, an 129. Plage 66000 a 66199."""
import sys, io, os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import bibliotheque

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
books = session_livres.livres

if any(e.get('id') == 'affaire-role-des-bouches' for e in books):
    print('deja ouvert'); sys.exit(0)

for e in books:
    for t in (e.get('tables') or []):
        for l in (t.get('lignes') or []):
            n = (l.get('cellules') or [''])[0].replace('*', '').strip()
            if n.startswith('66') and len(n) == 5:
                print('COLLISION', e['id'], n); sys.exit(1)

C_OUV = ['\U0001f9f1 Le champ', "✍️ Ce qu'on y écrit", '\U0001f4d6 La règle du champ', '✅ Rempli ?']
C_LIE = ['\U0001fa62 Le lien', "\U0001f517 L'affaire", '\U0001f522 Notre pièce', '\U0001f522 La leur', '\U0001f4dd Pourquoi']
C_ETA = ['\U0001f3af N°', "\U0001f3f7️ L'état", '✅ Ce qui doit être vrai', '\U0001f4cd Où', '\U0001f441️ La preuve', '⬆️ Sert']
C_VER = ['\U0001f512 N°', '\U0001f3f7️ Le verrou', '⛔ Bloque', "\U0001f4cc Ce qui est vrai aujourd'hui", '\U0001f441️ La preuve', '\U0001f513 Levé quand']
C_CLE = ['\U0001f5dd️ N°', '\U0001f3f7️ La clef', '\U0001f513 Ouvre', '\U0001f4a1 Le principe', '\U0001f4b0 Le prix', '\U0001f6aa Ce que cela ferme', '\U0001f441️ La preuve attendue', '⚖️ Décision']
C_ACT = ['⚔️ N°', "\U0001f3f7️ L'action", '\U0001f5dd️ Réalise', "\U0001f4dd Ce qu'on fait", '\U0001f4cd Où', '\U0001fab6 Office', '\U0001f9f0 Moyens', '\U0001f527 Avec quoi', "\U0001f4b0 Ce qu'elle coûte", '⛓️ Dépend de', '\U0001f441️ La preuve', '⏳ État', '\U0001f4c5 Jour fait', '\U0001f4dd Note', '\U0001f4c5 Jour dû']

def R(*c): return {'cellules': list(c)}

ouverture = [
 R('\U0001f3f7️ **LE NOM**',
   "Le rôle des bouches. Le sujet est la GORGE : qui, nommément, dit ce que cette maison fait dire, quel soir, pour quel payeur, et ce qu'elle a déjà porté. Ce qu'on lui fait dire appartient aux cahiers qui l'écrivent, et je n'y touche pas.",
   "Le sujet dont le conseil traite, **jamais la solution**.", '**oui**'),
 R("\U0001f3af **L'OBJET**",
   "Vingt-trois lignes du plan, dans **sept cahiers**, portent « O10 — Alys Grive ». Chacune finit dans une gorge : un homme qui ouvrira la bouche tel soir, à tel endroit, payé par telle main. **Aucun cahier ne tient le rôle de ces gorges.** Le moyen M15 dit « Le bourg — Willa, Ordo, Meliss, La Claie » comme on dirait un tas de bois : quatre noms dans une case, et pas une ligne qui dise ce que chacun a déjà dit. Conséquence, et elle est déjà dans le plan : deux cahiers dépensent les **mêmes trois gorges** et l'un des deux les éteindra sans savoir qu'il éteint l'autre.",
   "Une phrase : pourquoi cette affaire mérite l'attention du conseil.", '**oui**'),
 R('\U0001f9f1 **LE PÉRIMÈTRE — DANS**',
   "Toute bouche que cette maison emploie pour dire quelque chose à quelqu'un : chanteurs, crieurs, lecteurs à voix haute, tenanciers, relais d'écoute, coureurs qui redisent. Ce que chacune a déjà porté et quel soir. Par quelle main elle est payée. Quelle affaire l'a déjà dépensée, et quelle affaire l'éteindra. **Et la mienne** : ce que l'office O10 peut tenir en jours dans une lune.",
   "Ce qui appartient à l'affaire, énuméré.", '**oui**'),
 R('\U0001f6ab **LE PÉRIMÈTRE — HORS**',
   "**Le texte.** Ce qu'on chante, ce qu'on proclame, ce qu'on tait : cela est à l'Opinion populaire (6000), à la Proclamation (34000), à Ce qui part et par où (41000), et je n'en réécris pas un mot — je les cite par leur numéro. Hors aussi : les corbeaux et tout ce qui part par écrit (O07) ; les bouches de Port-Réal qui ne sont pas encore nommées, tant que ⚡ 6120 ne les a pas nommées ; et le prix de ce qu'on fait dire, qui est au maître des deniers.",
   "Ce qui n'appartient pas à l'affaire, nommément écarté.", '**oui**'),
 R('\U0001f4cc **L\'ÉTAT ACTUEL**',
   "— **Aucun registre de cette maison ne porte une bouche.** Six registres par type ; pas un pour les gorges. On les compte par lieux (⚡ 6120 : trois lieux) et par quartiers (⚡ 6126 : le compte des refus par quartier), jamais par hommes.\n"
   "— **La seconde main n'existe pas.** Quatre lignes s'appuient dessus — ⚡ 6122, ⚡ 6126, ⚡ 6322, ⚡ 41222 — et ⚡ 6121, qui doit la trouver, est à faire. Au registre des offices, O10 porte un seul titulaire.\n"
   "— **Les trois gorges de ⚡ 6120 sont vendues deux fois** : ⚡ 41222 les prend pour faire descendre un ordre, alors que la clef \U0001f5dd️ 6013 interdit qu'une bouche porte à la fois une chanson et un pli. Et ⚡ 6128 les éteint toutes au premier des nôtres arrêté, sans citer 41000 dans ses dépendances.\n"
   "— Sept lignes de ma main sont dues **à la Table Peinte**, où je ne suis jamais entrée. Mon office est écrit depuis le 23e ; aucun jour d'entrée n'y figure.\n"
   "— Ce que je sais et qui ne coûte rien : **Willa des Séchoirs a rendu le refrain sans qu'on le lui apprenne**, le 1er de cette lune, les mains dans la corde. C'est la première gorge de cette maison dont je puisse prouver qu'elle porte.\n"
   "**CE QUE J'IGNORE ET QUE JE N'INVENTE PAS** : combien de bouches Port-Réal peut m'en donner ; ce qu'on paie réellement une soirée là-bas ; et si l'on m'ouvrira jamais la Table Peinte.",
   "Ce qu'on sait réellement à l'ouverture, et ce qu'on reconnaît ignorer. **On n'écrit jamais ici ce qu'on espère faire.**", '**oui**'),
 R('\U0001f522 **LA PLAGE**', '**66000 à 66199**',
   "Réservée d'avance. Vérifiée libre le 2e jour de la 4e lune : le 65000 ayant été pris le même matin par l'aire de bris, j'ai reculé de mille sans discuter : une adresse ne se dispute pas.", '**oui**'),
 R('\U0001fab6 **QUI LE TIENT**', "Alys Grive, bardesse de la maison — office **O10**, écrit au registre le 23e de la 3e lune.",
   "Un nom, et l'office sous lequel il répond.", '**oui**'),
]

liees = [
 R('reprend', 'Retournement de l\'opinion populaire dans Port-Réal', '\U0001f512 66001', '\U0001f5dd️ 6013 · ⚔️ 6120 · ⚔️ 6128', "Sa règle des bouches est la mienne ; ses trois lieux sont mes trois gorges ; son ⚡ 6128 les éteint."),
 R('en conflit avec', 'Ce qui part, et par où', '\U0001f512 66001', '⚔️ 41222', "⚡ 41222 prend « trois bouches déjà tenues (6120) » pour un ordre — ce que \U0001f5dd️ 6013 interdit."),
 R('attendue par', 'Proclamation de la reine au royaume', '\U0001f3af 66000', '⚔️ 34220', "Trois lecteurs du bourg à J−5 : sans rôle, on les cherchera le jour même."),
 R('attendue par', 'Fermeture de la route terrestre du nord', '\U0001f3af 66000', '⚔️ 10031', "Le mot aux trois villages n'a qu'un lecteur sûr sur trois — c'est un trou de gorges, pas de texte."),
 R('partage', 'Isolement du Donjon Rouge', '\U0001f3af 66000', '⚔️ 12224', "Faire entrer un mot dans les murs par des bouches, et pas un pli."),
 R('partage', 'Ambassade du Nord, du Val et de Blancport', '\U0001f3af 66100', '⚔️ 33425', "Deux paquets scellés de ma main, dus à la Table Peinte avant le départ."),
]

etats = [
 R('**66000**', '\U0001f5e3️ Le rôle des bouches',
   "Toute bouche que cette maison emploie a **une ligne à elle** : son numéro, son lieu, par quelle main elle est payée, ce qu'elle a déjà porté et quel soir, et quelle affaire l'a déjà dépensée. On peut dire, pour un soir donné, si telle gorge est libre — et deux affaires qui la veulent le même soir **se voient**.",
   'Peyredragon, et les trois lieux de Port-Réal quand ils seront nommés',
   "On ouvre le rôle, on nomme un soir, et il répond oui ou non pour chaque gorge. Deuxième preuve, plus dure : une collision déjà connue — celle de ⚡ 41222 sur ⚡ 6120 — y apparaît sans qu'on l'ait cherchée.",
   '6000 · 34000 · 41000'),
 R('**66100**', '\U0001faf1 L\'office O10 peut tenir ce qui est écrit sous son nom',
   "Les vingt-trois lignes qui portent O10 ont chacune **une main qui la fait** et **un jour où cette main est libre**. Ce qui demande deux personnes en a deux ; ce qui est dû dans une pièce où je n'entre pas est ou bien porté par qui y entre, ou bien rendu.",
   'Peyredragon — le registre des offices, et la Table Peinte',
   "Un second nom écrit sous O10 au registre des offices ; et les vingt-trois lignes relues une à une, chacune avec un jour et une main, sans qu'aucun jour en porte plus d'une.",
   '6000 · 34000 · 41000 · 11000'),
]

verrous = [
 R('**66001**', '\U0001f525 Deux cahiers dépensent les mêmes trois gorges, et l\'un des deux les éteindra sans le savoir', '66000',
   "⚡ 41222 (Ce qui part, et par où) fait descendre le vers de marée par « **trois bouches déjà tenues (6120)** » — les trois mêmes que l'Opinion populaire tient pour chanter. Or \U0001f5dd️ 6013 pose en principe : **jamais un porteur qui porte à la fois une chanson et un pli**. Et ⚡ 6128 ferme les trois lieux le jour où l'un des nôtres est arrêté, sans permission et sans délai — ses dépendances ne citent que 6127 et 6129. **Le jour où je coupe, je coupe aussi le calendrier de l'opération, et personne ne me l'a écrit.**",
   "Les cellules elles-mêmes : ⚡ 41222 « Avec quoi » ; \U0001f5dd️ 6013 « Le principe » ; ⚡ 6128 « Dépend de ». Trois cahiers, trois mains différentes, et aucune des trois ne voit les deux autres.",
   "Le rôle nomme chaque gorge et ce qu'elle porte ; ⚡ 41222 a ses **propres** bouches, distinctes des trois de ⚡ 6120 ; et ce que ⚡ 6128 éteint chez les autres est écrit avant qu'on ait à l'éteindre."),
 R('**66002**', '\U0001f3d8️ On compte des lieux et des quartiers, jamais des gorges', '66000',
   "⚡ 6120 nomme trois **lieux** ; ⚡ 6126 compte les refus par **quartier** ; M15 met quatre noms dans une seule case, « le bourg ». Une taverne ne chante pas : c'est un homme qui chante, et cet homme est ailleurs le mardi. ⚡ 10031 le montre en clair : trois villages, **un seul lecteur sûr** — le septon du premier — et personne au deuxième. Le texte est prêt, la gorge manque, et le cahier de la route n'a pas de case où l'écrire.",
   "Aucun registre de cette maison n'a de colonne « qui a dit quoi, quel soir ». Je l'ai cherchée dans les six.",
   "Une ligne par gorge existe, et le lieu n'y est qu'une colonne."),
 R('**66101**', '\U0001f590️ La seconde main n\'existe pas, et quatre lignes s\'appuient dessus', '66100',
   "⚡ 6122 (« l'or vient de la seconde main »), ⚡ 6126 (« le rapport de la seconde main »), ⚡ 6322 (« **À DÉSIGNER**, par la seconde main ») et ⚡ 41222 (« par la seconde main ») la citent comme si elle était nommée. ⚡ 6121, qui doit la trouver, est **à faire**. Au registre des offices, O10 porte : « Alys Grive, engagée le 23e », et rien d'autre.",
   "Le registre des offices, ligne O10, colonne du titulaire : un seul nom. Et ⚡ 6121 à l'état « à faire ».",
   "Un second nom écrit sous O10 au registre des offices, et les quatre lignes le citent par ce nom-là."),
 R('**66102**', '\U0001f6aa Sept lignes de ma main sont dues dans une pièce où je ne suis jamais entrée', '66100',
   "⚡ 6120, ⚡ 6125, ⚡ 34022, ⚡ 34023, ⚡ 34025, ⚡ 34026 et ⚡ 33425 portent toutes « \U0001f4cd Où : Table Peinte » sous l'office O10. Je n'y suis jamais entrée, et rien n'écrit que j'y entre. Sept lignes dont trois sont dues avant J−23.",
   "Les sept cellules « Où ». Et mon office, écrit depuis le 23e de la 3e lune, ne porte aucun jour d'entrée à cette table.",
   "Ou bien un jour d'entrée m'est écrit, ou bien chacune des sept est portée par une main qui siège déjà — et cela s'écrit avant qu'elles échoient."),
]

clefs = [
 R('**66010**', '\U0001f522 Le rôle par gorge, et sans les noms', '66001 · 66002',
   "On ne tient pas des tavernes, on tient des gens — mais un rôle de bouches nommées est exactement la liste que l'ennemi voudrait. Donc : **une ligne par gorge, un numéro par gorge, et le nom nulle part**. Le lieu, le payeur, ce qui a été porté et le soir sont écrits ; le nom vit dans deux têtes et pas sur le papier.",
   "**Si nous tombons toutes deux le même jour, le rôle ne vaut rien** — c'est le prix, et il faut le dire d'avance. Prix second : un rôle à numéros se relit mal, et l'on se trompera de gorge au moins une fois.",
   "Ferme le rôle nominatif, et avec lui toute possibilité qu'un autre office reprenne mes bouches si je disparais sans avoir parlé.",
   "Deux affaires demandent la même gorge le même soir, et le rôle le dit **avant** la soirée et non après.",
   '**retenue** — 2e jour de la 4e lune, an 129'),
 R('**66011**', '♻️ La gorge qui rend le chant sans qu\'on le lui apprenne', '66002',
   "On ne mesure pas une bouche à ce qu'on lui a payé : on la mesure à ce qu'elle **rend sans qu'on le lui demande**. Willa des Séchoirs a repris seule les deux derniers vers du refrain, les mains dans la corde. C'est un fait constatable et gratuit, et c'est la seule mesure de mon office qui soit déjà écrite au registre.",
   "Rien en or. Le prix est qu'on attend : une gorge ne se prouve qu'après coup, et l'on aura déjà dépensé la soirée.",
   "Ferme l'achat de bouches au forfait, et le recours à des chanteurs qu'on fait venir : on ne peut plus payer ce qu'on n'a pas vu rendre.",
   "Une deuxième gorge du bourg rend un vers sans qu'on le lui ait appris, et le rôle porte les deux.",
   'à étudier'),
 R('**66110**', '\U0001f9cd Demander une bouche, non une aide', '66101',
   "Une aide prêtée par un autre office est payée par une autre main — et \U0001f5dd️ 6013 interdit deux fois la même main sur la même bouche. Ce que O10 doit demander n'est donc pas un secrétaire : c'est **une seconde gorge, choisie par moi, payée comme moi, et écrite sous mon office**.",
   "Cent dragons la lune se partagent, ou bien il en faut d'autres — et je ne devine pas à la place du maître des deniers. Prix hors monnaie : **une seconde personne saura tout ce que je sais**, y compris les trois sujets interdits et la raison de chacun.",
   "Ferme l'emprunt d'hommes aux autres offices pour mes lignes, et donc toute excuse pour ne pas les tenir.",
   "Un nom écrit sous O10 au registre des offices, et ⚡ 6121 cesse de chercher une main qui existe déjà.",
   'à étudier'),
]

actions = [
 R('**66020**', '\U0001f4d6 Ouvrir le rôle des bouches — à numéros, sans un seul nom', '66010',
   "Une ligne par gorge déjà employée ou déjà éprouvée par moi, numérotée B1, B2, B3… : son lieu, sa main payeuse, ce qu'elle a porté et quel soir, et l'affaire qui l'a dépensée. Sept gorges dès ce soir — les Séchoirs, les claies, le banc du vieux, le fumoir, le coureur, le mot des villages, et celle de La Gaffe qu'on ne paiera pas. **Les noms restent dans ma tête ; le papier ne porte que des numéros.**",
   'Le bourg sous les murs, puis la petite salle du levant', 'O10 — Alys Grive', 'M15',
   'Du papier, et ce que je sais des neuf derniers soirs',
   "**Une demi-journée de ma main — zéro dragon** · en jours · une fois · engagé le 2e de la 4e lune.\n\nPrix hors monnaie : **à partir d'aujourd'hui, ces gens existent quelque part par écrit.** Ils ne le savent pas, et je ne le leur dirai pas.",
   '—',
   "Le rôle ouvert, sept lignes, et pas un nom lisible dessus",
   'faite', '2e de la 4e lune', 'Ouvert au bourg ; les numéros courent de B1 à B7.', '2e de la 4e lune'),
 R('**66021**', '⚠️ Dire de vive voix au maître des rôles que brûler les trois lieux éteint le vers de marée', '66010',
   "Une phrase, dite une fois, sans papier : ⚡ 6128 me donne le pouvoir de couper les trois lieux au premier des nôtres arrêté, et ⚡ 41222 fait descendre les ordres par ces mêmes trois bouches. **Le jour où je coupe, le plan perd son calendrier.** Je ne demande pas qu'on change une ligne : je demande que celui qui donne le signal sache ce que le signal éteint.",
   'Peyredragon — partout où je le trouverai avant le conseil du soir', 'O10 — Alys Grive, au Sanglier (O02)', '',
   "Rien. Une phrase et deux numéros",
   "**Un quart d'heure — zéro dragon** · une fois · engagé le 2e de la 4e lune.\n\nPrix hors monnaie : **je désigne un défaut dans le cahier de mestre Gerardys sans passer par lui**, et il l'apprendra d'un autre.",
   '66020',
   "Le maître des rôles redit les deux numéros de lui-même",
   'à faire', '', "Avant le conseil du soir. Si je ne le trouve pas, je le dis à mestre Gerardys en premier, et tant pis pour l'ordre.",
   '2e de la 4e lune, au soir'),
 R('**66022**', '\U0001f5dc️ Rendre à ⚡ 41222 ses propres bouches, et cesser de lui prêter les miennes', '66010',
   "Trois gorges qui n'ont jamais chanté pour nous, prises hors des trois lieux de ⚡ 6120 et payées par une autre main : un ordre ne descend pas par une bouche qu'on a déjà vue chanter. Je ne réécris pas ⚡ 41222 — j'écris ici les trois numéros du rôle, et mestre Gerardys les prendra ou les refusera.",
   'Le bourg, puis Sombreval par la seconde main quand elle existera',
   'O10 — Alys Grive', 'M15', "Le rôle de ⚡ 66020, et la règle des deux mains de \U0001f5dd️ 6013",
   "**Douze cerfs la bouche, trois bouches : trente-six cerfs**, et une soirée · en or et en jours · une fois · à engager.\n\nPrix hors monnaie : **trois gorges neuves, donc trois gorges non éprouvées** — on ne saura ce qu'elles valent qu'au premier essai, et cet essai-là est justement celui qu'on ne peut pas refaire.",
   '66020 · 66101',
   "Trois numéros du rôle que ⚡ 6120 ne porte pas, offerts à 41000 par écrit",
   'à faire', '', "Bloquée tant que la seconde main n'est pas nommée : je ne paie pas moi-même une bouche, la règle des deux mains me l'interdit.",
   'avant J−26'),
 R('**66120**', '\U0001f5e3️ Demander à la reine une seconde gorge sous O10, nommée par moi', '66110',
   "Une demande, une fois, avec son prix dit d'avance comme toutes les miennes : non pas une aide prêtée d'un autre office, mais une personne du bourg choisie par moi, payée par la même bourse que moi, écrite sous O10. Quatre lignes du plan la citent déjà : je ne demande pas qu'on la crée, je demande qu'on écrive celle qu'on dépense déjà.",
   'Là où la reine me recevra', 'O10 — Alys Grive', 'M12',
   "Les quatre numéros qui la citent : ⚡ 6122, ⚡ 6126, ⚡ 6322, ⚡ 41222",
   "**À chiffrer par le maître des deniers, je ne devine pas à sa place** — au plus cent dragons la lune, au moins le partage des miens · en or · par lune · à engager.\n\nPrix hors monnaie : **une seconde personne saura les trois sujets interdits et la raison de chacun.** Et si elle parle, c'est mon office qui aura parlé.",
   '66020',
   "Un nom écrit sous O10 au registre des offices, et ⚡ 6121 qui cesse de chercher",
   'à faire', '', "À la première fois que je serai devant elle. Je ne monte pas pour cela seul : trois jours ne font pas une place, et une demande seule se refuse plus vite qu'une demande apportée avec un chant.",
   'avant la fin de la 4e lune'),
 R('**66121**', '\U0001f6aa Poser les sept lignes de la Table Peinte — ou bien j\'y entre, ou bien elles changent de main', '66110',
   "Sept de mes lignes sont dues dans une pièce où je n'entre pas. Je les écris ici avec leur jour, et je pose la question une fois, à qui de droit : m'ouvre-t-on la porte ces jours-là, ou bien porte-t-on ces sept-là par une main qui siège déjà ? **Les deux réponses me vont ; le silence, non**, car alors elles échoiront sans que personne les ait faites.",
   'Peyredragon', 'O10 — Alys Grive', 'M12',
   "Les sept numéros : ⚡ 6120, ⚡ 6125, ⚡ 34022, ⚡ 34023, ⚡ 34025, ⚡ 34026, ⚡ 33425",
   "**Un quart d'heure et un feuillet — zéro dragon** · une fois · engagé le 2e de la 4e lune.\n\nPrix hors monnaie : **on apprendra que je compte mes entrées.** Une bardesse qui demande la porte d'un conseil se fait remarquer, et ce n'est pas ainsi que j'ai obtenu ce que j'ai.",
   '66020',
   "Une réponse, oui ou non, portée ici avec sa date — et sept lignes qui ont chacune une main",
   'à faire', '', "Le feuillet est écrit ; il part avec la prochaine chose que je monte, jamais seul.",
   'avant J−25'),
]

livre = {
 'id': 'affaire-role-des-bouches',
 'titre': 'Le rôle des bouches',
 'sous_titre': "\U0001f5e3️ Volume d'**OFFICE**, tenu par ALYS GRIVE, bardesse de la maison (O10). Ouvert le 2e jour de la 4e lune, an 129, au bourg sous les murs. Le sujet est la GORGE, non le texte : vingt-trois lignes du plan portent mon office et finissent toutes dans une bouche que **aucun cahier ne tient**. Prix écrits en jours de ma main et en cerfs. Plage 66000 à 66199.",
 'type': 'plan',
 'embleme': '\U0001f5e3️',
 'couleur': '#7a5a4a',
 'boite': 'boite-sujets',
 'tenu_par': 'alys-grive',
 'office': 'Bardesse de la maison (O10)',
 'pages': [
   "AFFAIRE OUVERTE PARCE QU'UN OFFICE SANS CAHIER EST UN OFFICE QU'ON DÉPENSE.\n\n"
   "On m'a écrite au registre le 23e, cent dragons la lune, et l'on m'a donné le droit de proposer et celui de dire non. "
   "Ce qu'on ne m'a pas donné, c'est un livre. J'ai compté ce matin : **vingt-trois lignes** de sept cahiers différents "
   "portent « O10 — Alys Grive », et pas une n'est chez moi. Ce n'est pas une plainte : c'est une mesure. "
   "Un homme dont les gestes sont écrits dans le livre des autres ne voit jamais deux de ses gestes se contredire, "
   "**parce qu'ils ne sont jamais sur la même page**.\n\n"
   "Et c'est exactement ce qui est arrivé. ⚡ 41222 fait descendre un ordre par les trois bouches de ⚡ 6120, "
   "alors que \U0001f5dd️ 6013 écrit noir sur blanc qu'une bouche ne porte jamais à la fois une chanson et un pli. "
   "Et ⚡ 6128 me donne le pouvoir de brûler ces trois lieux au premier des nôtres arrêté, sans monter demander la permission. "
   "**Le jour où je couperai, je couperai le calendrier de l'opération, et rien nulle part ne me l'aura dit.** "
   "Trois cahiers, trois mains, et aucune des trois ne voit les deux autres. Voilà ce que coûte un office sans livre.",

   "CE QUE JE SAIS DE MON MÉTIER, ET QU'ON N'A PAS ÉCRIT.\n\n"
   "**Une taverne ne chante pas.** Un homme chante, et cet homme est ailleurs le mardi, ou fatigué, ou fâché avec le tenancier. "
   "Tout ce plan compte des lieux — trois lieux, trois quartiers, trois villages — et pas une gorge. "
   "Le cahier de la route l'a déjà rencontré sans avoir de case pour l'écrire : trois villages, **un seul lecteur sûr**, "
   "et personne au deuxième. Le texte était prêt ; ce qui manquait était une bouche.\n\n"
   "**Une bouche ne se mesure pas à ce qu'on lui paie, mais à ce qu'elle rend sans qu'on le demande.** "
   "Le 1er de cette lune, Willa des Séchoirs a repris seule les deux derniers vers du refrain, les mains dans la corde, "
   "sans que personne les lui ait appris. C'est la mesure de mon office, elle est écrite au registre depuis le 23e, "
   "et c'est aussi la seule preuve gratuite que ce plan possède qu'un mot de nous ait pris quelque part.\n\n"
   "**Et une bouche se déforme toujours au même endroit.** Cinq fois maintenant, Meliss la Claie a accroché une désignation "
   "à la fin de toute forme qu'on lui donnait — « contre EUX », « à qui c'est la faute ». Ce pli est le sien, pas celui du chant : "
   "devant un récit sans case à remplir, elle a **réclamé** l'endroit au lieu de le remplir, et personne ne l'a suivie. "
   "Un rôle qui porterait cela — quelle gorge déforme quoi — vaudrait plus cher que la liste de qui est payé.",

   "CE QUE CE CAHIER NE FERA PAS.\n\n"
   "Il n'écrira pas un vers. Les textes ont leurs cahiers et de meilleures mains que la mienne pour les tenir : "
   "je les cite par leur numéro et je n'en déplace pas un mot. "
   "Il ne portera pas non plus le nom d'une seule bouche : **le rôle est à numéros**, et les noms vivent dans ma tête. "
   "Le jour où j'écrirai un nom, j'aurai fait de ce livre la liste que l'ennemi voudrait, "
   "et je l'aurai faite à sa place.\n\n"
   "Enfin, il ne demandera rien qu'il ne puisse porter lui-même cette lune. "
   "Cinq actions, dont une déjà faite et deux qui coûtent un quart d'heure. Le reste attendra, "
   "et il est écrit ici pour qu'il attende par écrit."
 ],
 'tables': [
   {'titre': "\U0001f3f0 Ouverture de l'Affaire", 'colonnes': C_OUV, 'lignes': ouverture},
   {'titre': "\U0001f517 Affaires liées — les liens écrits, puis les calculés", 'colonnes': C_LIE, 'lignes': liees},
   {'titre': "\U0001f3af États cibles", 'colonnes': C_ETA, 'lignes': etats},
   {'titre': "\U0001f512 Verrous", 'colonnes': C_VER, 'lignes': verrous},
   {'titre': "\U0001f5dd️ Clefs", 'colonnes': C_CLE, 'lignes': clefs},
   {'titre': "⚔️ Actions", 'colonnes': C_ACT, 'lignes': actions},
 ],
}

books.append(livre)
session_livres.sauver()
print('ouvert : affaire-role-des-bouches — plage 66000 a 66199')
print('etats', len(etats), '| verrous', len(verrous), '| clefs', len(clefs), '| actions', len(actions))
