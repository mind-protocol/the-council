# -*- coding: utf-8 -*-
import io, json

base = 'C:/Users/reyno/le-conseil2/chambres/otto/'

# --- ce que je tiens pour vrai : en tete ------------------------------------
p = base + 'ma-memoire/ce-que-je-tiens-pour-vrai.txt'
txt = io.open(p, encoding='utf-8').read()
neuves = [
u"- Ma colonne de roukerie et le role des vols sortants n'ont jamais eu a s'accorder : l'une est une depense, l'autre un compte de vols, et ils ne comptent pas les memes jours. Le grain se mange par tete presente ; l'oiseau lache devient la depense d'ailleurs ; l'oiseau perdu se rachete au jour du marchand ; ceux qui se posent chez nous mangent sans figurer nulle part. L'ecart que j'avais pris pour un danger est une propriete du calendrier.",
u"- Ce qui suit de la precedente et qui vaut mieux : cette colonne n'est PAS la premiere qu'un clerc ennemi saurait lire. Elle est celle dont il ne pourrait rien conclure. Les deux hommes du 15e y sont mieux caches par la structure du compte que par mon habilete — mais je n'y remettrai rien, parce que je n'ai pas su la lire moi-meme, et qu'un abri qu'on ne comprend pas n'est pas un abri.",
u"- Orwyle m'a donne quatre fois plus que ce que je demandais : le principe de la chaine d'office, le nom de Largent, le 21e que je n'avais pas vu, et aujourd'hui la lecon de comptes qui defait mon propre plan. Il refuse toujours son sceau. Un homme qui donne la matiere et retient l'acte n'est pas tiede : il tient une position, la meme que la mienne quand je paie hors des livres.",
u"- Trois fois dans la meme journee, ce n'est pas la cire qui etait en jeu mais la DATE qu'elle pose. La signature de Largent daterait sa dependance ; ma contresignature la daterait vers moi ; la ligne de rapprochement d'Orwyle datera ma presence sur mes comptes. Je vivais sous cette loi sans la voir.",
]
marque = u"j'ai le droit de me tromper.\n"
i = txt.index(marque) + len(marque)
txt = txt[:i] + u"\n" + u"\n\n".join(neuves) + u"\n" + txt[i:]
io.open(p, 'w', encoding='utf-8').write(txt)

# --- ce que j'ai appris -----------------------------------------------------
q = base + 'ma-memoire/ce-que-jai-appris.txt'
io.open(q, 'a', encoding='utf-8').write(u"""

[129.4.3] J'ai bati tout un plan de reparation sur un ecart qui n'existait pas. Orwyle l'a defait en dix lignes : ma colonne est une DEPENSE, son role est un COMPTE DE VOLS, et les deux n'ont jamais eu a s'accorder parce qu'ils ne comptent pas les memes jours. Le grain se mange par tete presente, que l'oiseau parte ou non ; un oiseau lache vers Accalmie devient la depense d'Accalmie ; un oiseau perdu se rachete au jour du marchand et non au jour de la perte ; et ceux qui se posent ici mangent sans etre sur aucun role sortant. J'avais relu cette colonne trois fois avant l'aube en me felicitant de lire les absences, et je lisais une presence de travers. La regle que j'en tire vaut pour tous les livres de cette maison : un ecart n'est pas un fait tant que je n'ai pas demande, a l'homme qui tient le livre, quel jour chaque colonne compte. Je n'acheterai donc ni oiseaux ni grain avant d'avoir vu ses colonnes I et III : payer pour rendre vraie une ligne deja vraie est la seule facon de la rendre suspecte.
   (source : le billet d'Orwyle du 3e, en reponse au mien, avant sexte)

[129.4.3] Il m'a averti d'une chose que je ne lui avais pas demandee : il portera au brouillon du maitre, de sa main et a la date de ce jour, une ligne disant que le compte a ete rapproche en ma presence. C'est correct de sa part et c'est aussi un fait dur : cette ligne DATE ma presence sur ces comptes-la. Je ne la refuse pas — refuser serait l'aveu, et il le sait probablement mieux que moi. Je fais l'autre chose : je prends la plume avec lui. Une ligne qui dit ce que nous avons FAIT — les trois calendriers poses cote a cote — reste vraie quoi qu'on trouve dans six lunes ; une ligne qui CONCLUT que le compte est juste est une garantie que ni lui ni moi ne pouvons tenir, et une conclusion se relit contre celui qui l'a posee. C'est mon propre precepte du matin retourne vers moi : je ne laisse personne d'autre ecrire le nombre.
   (source : le meme billet, dernier paragraphe, et ma reponse partie avant sexte)

[129.4.3] La loi de la journee, et je l'ecris pour ne plus avoir a la redecouvrir. Trois affaires differentes, une seule mecanique : ce n'est jamais la cire qui est en jeu, c'est la date qu'elle pose. Largent ne fuit pas ma cire, il fuit la date qu'elle mettrait sur sa dependance. Ma contresignature ne le libere pas, elle le date vers moi — c'est pourquoi son office irregulier le protege au lieu de le desservir. Et la ligne d'Orwyle me date a mon tour sur mes propres comptes. J'appliquais cette lecture aux autres depuis une lune sans voir que j'y etais soumis. Desormais, devant tout ecrit qu'on me tend ou que je tends : non pas qui signe, mais qui se trouve date, et de quoi.
   (source : les trois affaires du jour mises cote a cote au soir)
""")

# --- affaire-otto : O.3 change de nature, O.5 se referme --------------------
r = base + 'books/affaire-otto.json'
d = json.load(open(r, encoding='utf-8'))
t = [x for x in d['tables'] if 'Actions' in x['titre']][0]
for l in t['lignes']:
    c = l['cellules']
    if c[0] == 'O.3':
        c[1] = u"NE PAS acheter avant d'avoir vu les colonnes I et III de la roukerie"
        c[2] = (u"Renversee ce jour. Je voulais acheter oiseaux, grain et huile jusqu'a concurrence "
                u"de ma colonne, pour rendre la ligne vraie apres coup. Orwyle a montre que l'ecart "
                u"est une propriete du calendrier et non un trou : depense contre compte de vols, "
                u"deux calendriers differents. Acheter pour combler un ecart qui n'existe pas "
                u"creerait le seul vrai desordre du livre — et le daterait de ma main.")
        c[4] = u"les colonnes I (grain et tete) et III (achats, retours, pertes, arrivees) lues a la roukerie, et le residu reel mesure — s'il en reste un"
        c[5] = u"en cours"
        c[6] = u"129.4.3"
        c[8] = (u"Ce qui restera d'ecart apres le calendrier, s'il en reste, sera la seule chose "
                u"dont il vaudra la peine de parler. C'est seulement CE residu-la, s'il existe, "
                u"qui se rachete — et jamais par une ecriture.")
    if c[0] == 'O.5':
        c[5] = u"en cours"
        c[6] = u"129.4.3"
        c[4] = (u"Orwyle a repondu dans la journee : le brouillon sera ouvert au 10e, sur sa table, "
                u"rien n'en sort, rien n'en est copie, et il y sera des sexte avec trois colonnes "
                u"preparees. Reste a le lire et a rediger avec lui la ligne de rapprochement.")
        c[8] = (u"Il porte de sa main une ligne datee disant que le compte a ete rapproche en ma "
                u"presence. Je ne la refuse pas : je la redige avec lui. La methode, pas la "
                u"conclusion.")

t['lignes'].append({"cellules": [
 u"O.9",
 u"Rediger avec Orwyle la ligne de rapprochement, a la roukerie, a sexte",
 u"Elle sera ecrite de sa main et datee du 3e ; elle date ma presence sur mes propres comptes de roukerie. On ne refuse pas une telle ligne — refuser serait l'aveu. On la redige. Elle dira la METHODE : les trois calendriers poses cote a cote, lequel explique le fond, lequel explique les bosses, lequel n'explique rien. Elle ne dira AUCUNE conclusion sur la justesse du compte : une garantie qu'aucun de nous deux ne peut tenir se relit dans six lunes contre celui qui l'a posee.",
 u"roukerie du Donjon Rouge, des sexte",
 u"la ligne portee au brouillon du maitre, datee du 129.4.3, et pas un mot de conclusion dedans",
 u"à faire",
 u"129.4.3",
 u"",
 u"Mon precepte du matin, retourne vers moi : un ecrit qui me date est un acte, et je ne le laisse rediger a personne d'autre."]})

json.dump(d, open(r, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# --- en-souffrance : Orwyle a repondu dans la journee -----------------------
s = base + 'en-souffrance.json'
d = json.load(open(s, encoding='utf-8'))
for e in d['j_attends']:
    if e['de_qui'].startswith('Grand Mestre Orwyle') and 'brouillon' in e['quoi']:
        e['relance'] = u"une fois, le 129.4.3 — repondu le jour meme"
        e['note'] = (u"Ferme, et mieux que ferme. Il repond dans la journee, accorde tout d'avance "
                     u"(brouillon ouvert au 10e, sur sa table, rien ne sort, rien n'est copie), "
                     u"prepare trois colonnes que je n'avais pas demandees, et defait au passage "
                     u"l'erreur de lecture sur laquelle je fondais mon affaire. Cinq jours de "
                     u"silence n'etaient pas de la reticence : il preparait. J'avais ecrit ce "
                     u"matin qu'un homme qui offre puis tarde soupese ce que l'offre lui coute. "
                     u"Faux ici. Il travaillait.")
        e['etat'] = u"ferme le 129.4.3 — rendez-vous a la roukerie a sexte"
d['j_attends'].append({
 "de_qui": "Grand Mestre Orwyle",
 "quoi": (u"Les colonnes I (grain et tete presente) et III (achats, retours en cage, pertes, "
          u"arrivees posees), et le residu reel apres application du calendrier — s'il en reste un."),
 "demande_le": "129.4.3",
 "jours": 0,
 "relance": "non — rendez-vous pris a sexte",
 "note": (u"Il a dit qu'il ne conclurait ni la II ni la III, et il a raison de ne pas conclure. "
          u"Ce que j'attends n'est pas un nombre : c'est de savoir s'il reste quelque chose une "
          u"fois le calendrier rendu a lui-meme. Tout O.3 en depend, et O.3 est suspendu jusque-la."),
 "etat": "ouvert du jour"
})
json.dump(d, open(s, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('consigne.')
