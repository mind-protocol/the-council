# -*- coding: utf-8 -*-
import json, io, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(base, 'books', 'affaire-marlo-vasse.json')
d = json.load(io.open(p, encoding='utf-8'))

verr = acts = None
for t in d['tables']:
    if 'Verrous' in t['titre']:
        verr = t
    if t['titre'].endswith('Actions'):
        acts = t

verr['lignes'].append({"cellules": [
 "V.11",
 "J'ai écrit une borne qui MARCHE : la ligne de basse mer n'est pas une borne, c'est une heure",
 "M.2 — Une coque sur l'aire à la vive-eau du 15e",
 "J'ai porté le partage « de la borne du cordier jusqu'à la ligne de basse mer ». Cette ligne recule de trois quarts d'heure par jour et de vingt pas et plus quand la lune tire : à la morte-eau mon aire s'arrête où celle de Nel commence, à la vive-eau elle a gagné le double sans que personne ait bougé une pierre. Et le jour où ça comptera vraiment, c'est LE 15e : la carcasse que j'attends viendra s'échouer exactement sur la ligne qui bouge, et ce jour-là on se demandera à qui est le sol sous elle. Deux hommes de bonne foi peuvent tenir le même papier et n'être pas d'accord sur un pas de grève.",
 "Nel Bec, le 3e au soir : la borne du cordier tient, la ligne de basse mer non — elle a refusé la seconde et pris la première",
 "Écrire DE LA BORNE DU CORDIER À LA LAISSE DE VIVE-EAU, et faire planter un piquet à cette laisse AVANT LE 7e, pendant que les quatre bras y sont et que ça ne coûte que le bois. Une borne plantée avant qu'on en ait besoin ne se discute pas ; plantée après, c'est une prise. Et plantée à deux, jamais seul."
]})

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.6':
        c[2] = c[2].replace("bornes et dates", "bornes et dates — DE LA BORNE DU CORDIER À LA LAISSE DE VIVE-EAU, et non « à la ligne de basse mer », qui est une heure et non une borne")
        c[8] = (c[8] + " || CORRIGÉ le 3e au soir par elle : ma seconde borne marchait. Elle prend la borne du cordier et refuse "
                "la ligne de basse mer, et elle a vu plus loin que moi — la carcasse du 15e s'échouera sur la ligne qui bouge.")
    if c[0] == 'M.8':
        c[2] = ("Une planche, une chaîne, un charbon, trois mots : QUI · QUOI · QUELLE HEURE. Le métier et non le nom. Et ce "
                "qui se compte n'est pas le regard mais LE RETOUR : combien de fois, à quelle heure, de quel métier — une fois "
                "on passe, deux fois à la même heure on a un motif. Tenue par DEUX TÊTES APPARIÉES À LA MARÉE et non par une "
                "tête au piquet : celle qui a la basse mer du matin prend la barrière l'après-midi, l'autre l'inverse. Louées "
                "PAR LA MAIN DE NEL, même prix que ses six, même sac : un sou et demi la journée, pain compris. Copie à "
                "l'ardoise chaque soir, sous le nom de sa main et non de la mienne.")
        c[8] = (c[8] + " || CORRIGÉ le 3e au soir par Nel Bec, sur quatre points, et j'ai pris les quatre. Un gosse au piquet "
                "du matin au soir ne mange pas ce jour-là : il tient trois jours puis ment doucement et toujours vers le bas — "
                "un compte qui coûte un repas à celui qui le tient est un faux compte à retardement. Et je ne les paie pas "
                "moi-même : payer soi-même n'empêche personne d'être déjà payé, ça pose seulement un SECOND PRIX sur la grève, "
                "et deux prix qui ne se parlent pas montent l'un contre l'autre. Une seule main paie, un seul prix — et le sou "
                "du sixième est dû À LA PAIRE, sur l'accord des deux ficelles : on ne peut pas acheter une des deux têtes sans "
                "acheter l'autre, et qui n'en achète qu'une perd son sou et se découvre.")

acts['lignes'].append({"cellules": [
 "M.14",
 "🪧 Planter le piquet de la laisse de vive-eau avant le 7e",
 "Pendant que les quatre bras sont sur l'aire du bout et que ça ne coûte que le bois : un piquet à la laisse de vive-eau, planté à deux — moi et qui Nel enverra — et porté sur les deux exemplaires du partage. Pas à la ligne de basse mer, qui recule de trois quarts d'heure par jour et de vingt pas quand la lune tire.",
 "l'aire du bout, à la laisse de vive-eau",
 "un piquet en terre avant le 7e, vu par deux, et la même phrase sur les deux exemplaires du partage",
 "à faire",
 "129.4.6",
 "",
 "Lève V.11. Le 15e, la carcasse s'échouera exactement sur la ligne qui bouge, et ce jour-là il sera trop tard pour discuter du sol sous elle. Une borne plantée avant qu'on en ait besoin ne se discute pas."
]})

acts['lignes'].append({"cellules": [
 "M.15",
 "🚪 61001 — six jours de colonnes sans un trou, dont trois où je n'y suis pas",
 "Ce que je vends, ce sont les portes en colonnes : une colonne avec un trou ne vaut pas la moitié, elle ne vaut RIEN, parce que l'acheteur ne sait pas où est le trou et doit tout recompter. Donc : ce qui entre et sort par la Gadoue et par le port relevé chaque jour SANS QUE J'Y AILLE. La preuve n'est pas une impression : six jours de colonnes sans une journée manquante, sans une journée de ma main, sans un homme qui ait attendu ma parole pour écrire — et trois de ces six jours passés hors de Port-Réal.",
 "porte de la Gadoue · bureau du port",
 "six jours de colonnes sans un trou, dont trois d'absence, et la colonne signée d'une autre main que la mienne",
 "à faire",
 "129.4.10",
 "",
 "Rendu à Nel Bec le 3e, en une ligne, parce qu'elle l'avait demandé deux fois : elle comptait bien sans savoir pour quoi, et c'était ma faute. La seule raison pour laquelle je vais encore aux portes de mes pieds, c'est que le compte d'un autre ne se croit pas encore ; le jour où le sien se croit sans moi, j'ai une marchandise — aujourd'hui je n'ai qu'une habitude. Et la colonne se lit sous SON nom, pas le mien : c'est ainsi qu'elle se vend deux fois sans mentir une seule."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
