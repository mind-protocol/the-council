# -*- coding: utf-8 -*-
"""Mon livre, tenu au 5e de la 4e lune, an 129, a midi. Les etats en UN MOT
dans la colonne d'etat ; la prose dans la note, jamais ailleurs."""
import io, json, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(D, 'books', 'affaire-sarro-vaeth.json')
d = json.load(io.open(P, encoding='utf-8'))

tables = dict((t['titre'], t) for t in d['tables'])
act = tables[u'⚔️ Actions']
cib = tables[u'🎯 Ce que je veux']
c = act['colonnes']
I_ETAT, I_FAIT, I_NOTE = c.index(u'⏳ État'), c.index(u'📅 Jour fait'), c.index(u'📝 Note')
I_DU = c.index(u'📅 Jour dû')


def maj(ref, etat, fait, note):
    for l in act['lignes']:
        if l['cellules'][0] == ref:
            l['cellules'][I_ETAT] = etat
            l['cellules'][I_FAIT] = fait
            l['cellules'][I_NOTE] = note
            return True
    return False


maj(u'P.1', u'faite', u'129.4.4', u"Lu, et deux fois amende depuis.")
maj(u'P.2', u'faite', u'129.4.4',
    u"Quatre amendements dates a ce jour. Le dernier du 5e a midi : quand on "
    u"me reclame une ligne, je regarde d'abord si j'ai un livre ou l'ecrire.")
maj(u'P.3', u'bloquée', u'',
    u"Demande un FAIRE tranche par l'arbitre. Parloir ferme trois jours de "
    u"suite (voir problemes.json, 3 entrees). NON FAIT et ecrit comme tel : "
    u"je n'invente pas mon passe faute d'arbitre.")
maj(u'P.4', u'faite', u'129.4.5', u"C.4 pose de ma main ce jour.")
maj(u'P.5', u'faite', u'129.4.4',
    u"Le 4e sur les cinq heures de vol refusees ; le 5e sur le role qui "
    u"n'existait pas.")
maj(u'P.6', u'faite', u'129.4.5',
    u"Trois actions de mon office ecrites ci-dessous, F.1 a F.3. Ce volume "
    u"cesse d'etre une prise en main.")
maj(u'P.7', u'faite', u'129.4.4',
    u"Les deux tenus tous les jours depuis. problemes.json : 3 entrees, dont "
    u"une qui RAYE mon propre diagnostic de la veille. en-souffrance.json : "
    u"4 fils que j'attends, 5 qu'on attend de moi, avec la date de la "
    u"demande et non celle du souvenir.")
maj(u'P.8', u'bloquée', u'',
    u"Trois jours de parloir ferme. MAIS la question des cinquante hommes, je "
    u"l'ai resolue sans lui : elle dormait ecrite dans le registre des "
    u"charges, ligne 4, depuis le 1er. Avant de demander au monde, fouiller "
    u"l'etagere.")
maj(u'P.9', u'bloquée', u'',
    u"Meme cause. --demander pend, --dire tombe sur uv_spawn : c'est le "
    u"reveil du destinataire qui casse, pas la parole.")
maj(u'P.10', u'faite', u'129.4.5',
    u"Trois billets poses a la main dans les canaux de paire, faute de "
    u"facteur : au prince le 5e au matin, a ser Robert le 5e au matin et le "
    u"5e a midi. Deux canaux dans relations/, plus la fiche que je tiens sur "
    u"chacun.")

cib['lignes'].append({"cellules": [
    u"C.4",
    u"Aucun homme et aucune bete de ce rocher ne mange sans figurer dans un livre",
    u"Tout ce qui a une bouche aux fosses est porte a un role ou a un compte "
    u"tenu de ma main, avec le jour de son entree et qui le nourrit ; et ce "
    u"qui entre chez moi sans etre ecrit ailleurs, c'est moi qui l'ecris.",
    u"Le role des fosses, l'ardoise de la porte des oeufs et le compte des "
    u"matins d'Ossa, tous trois ouverts de ma main entre le 5e a l'aube et le "
    u"5e a midi ; et le meme nombre dit chez moi et chez le castellan a sept "
    u"heures."]})

for ref, titre, quoi, ou, preuve, etat, du, fait, note in [
    (u"F.1", u"Appeler le role des fosses nom par nom",
     u"Premier appel nominatif des cinquante de la chaine de sable chaud, a "
     u"l'aube, un homme une colonne. Ecrire ce qu'il fait et qui le nourrit. "
     u"Signer le nombre APPELE, pas le nombre recu.",
     u"les fosses, a l'aube",
     u"Le role des fosses rempli, et le meme nombre dit a sept heures chez moi "
     u"et chez ser Robert",
     u"à faire", u"129.4.6", u"",
     u"Si l'appel rend moins de cinquante, la difference est MIENNE et je la "
     u"dis moi-meme le 7e. Je l'ai ecrit a ser Robert avant de compter."),
    (u"F.2", u"Lire la veine au front de la onzieme galerie",
     u"Craie, deux hommes, torches. Descendre jusqu'au front. Meme veine que "
     u"la douzieme, ou non — et pas un mot avant d'avoir la pierre sous le "
     u"pouce.",
     u"onzieme galerie, sous la Montagne",
     u"La reponse rendue de ma bouche a ser Robert",
     u"en cours", u"129.4.3", u"",
     u"DEUX JOURS DE RETARD. La douzieme n'est dans aucun de mes registres : "
     u"je l'ai apprise dans le cahier d'un autre, et c'est la reponse avant "
     u"d'etre l'excuse. Rendue le 6e a la premiere lumiere."),
    (u"F.3", u"Peser les trois oeufs sous deux signatures",
     u"Meme heure, meme balance, memes poids, contresigne par deux dont un qui "
     u"n'est pas de la fosse. Ecrire les trois chiffres meme quand ils n'ont "
     u"pas bouge.",
     u"la chambre des trois oeufs",
     u"Deux pesees comparables d'un matin a l'autre sur l'ardoise de la porte",
     u"en cours", u"129.4.6", u"",
     u"Le chiffre du 5e est un PLANCHER et non une preuve : entre le septieme "
     u"jour et aujourd'hui la garde est tombee de dix-huit hommes a six et "
     u"aucune ligne ne nomme un entrant. C'est la perte jour apres jour qui "
     u"parle, pas un chiffre pris tout seul."),
]:
    act['lignes'].append({"cellules": [ref, titre, quoi, ou, preuve, etat, du,
                                       fait, note]})

with io.open(P, 'w', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=1))
print("actions:", len(act['lignes']), "| etats cibles:", len(cib['lignes']))
