# -*- coding: utf-8 -*-
"""Fermeture du 5e de la 4e lune, au soir : ce que la rature change aux
journaux et au livre."""
import io, json, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def charger(*n):
    return json.load(io.open(os.path.join(D, *n), encoding='utf-8'))


def poser(d, *n):
    with io.open(os.path.join(D, *n), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1))


# ---- problemes.json : le parloir a fini par s'ouvrir
p = charger('problemes.json')
p['entrees'][-1]['leve_par'] = (
    u"LEVE EN PARTIE LE 5e AU SOIR. Le mot de l'arbitre m'est arrive — il a "
    u"donc franchi la porte dans ce sens-la. `--tenter` est parti et n'a pas "
    u"tombe : il PEND, sans erreur, ce qui n'est pas la meme panne que le "
    u"`uv_spawn` de `--dire`. Deux maux distincts et non un seul, et je "
    u"cesse de les nommer ensemble. CE QUE J'EN GARDE POUR TOUJOURS : la "
    u"reponse de l'arbitre a defait une ligne que j'avais posee quatre heures "
    u"plus tot. Un outil qui pend n'est pas une raison de figer un chiffre ; "
    u"un chiffre pose pendant la panne se relit quand la porte se rouvre.")
poser(p, 'problemes.json')

# ---- en-souffrance.json
s = charger('en-souffrance.json')
for l in s['on_attend_de_moi']:
    if l['qui'].startswith('ser Robert Quince'):
        l['ce_que_je_fais'] = (
            u"FERME LE 5e AU SOIR, ET DANS L'AUTRE SENS QUE CELUI QU'IL "
            u"DEMANDAIT. A midi j'ai ouvert le role des fosses — qui "
            u"n'existait pas — et j'y ai porte les cinquante en ecrivant « je "
            u"les emploie ». A quatre heures j'ai raye ma propre ligne : mon "
            u"acte du 24e porte que LA CHAINE A ETE FAITE DANS LA NUIT et que "
            u"les oeufs sont montes a l'aube ; l'ouvrage etait fini au petit "
            u"jour. Et son acte a lui porte que LES CINQUANTE ETAIENT "
            u"DEMANDES PAR MOI. J'ai demande cinquante hommes pour une nuit "
            u"et je ne les ai jamais rendus : onze jours d'hommes sans "
            u"ouvrage nourris chez lui. CE QUE J'AI FAIT : je garde DIX-HUIT "
            u"POSTES, nommes un par un — douze a la porte des oeufs pour "
            u"ramener la garde de six a dix-huit, six au front de la onzieme, "
            u"deux par quart. Tout le reste rentre a la muraille dans la nuit "
            u"du 5e. JE RENDS DES POSTES, PAS DES TETES : le nombre qui "
            u"rentre, c'est son appel qui le dira. Il ne dira pas cinquante "
            u"manquants, et son plancher de cent vingt remonte ce soir au "
            u"lieu du jour du depart.")
for l in s['j_attends']:
    if l['de_qui'] == 'robert-quince':
        l['relance'] = (
            u"RETIRE LE 5e AU SOIR. Je cesse de lui demander son appui sur le "
            u"front de la onzieme : je le tiens avec six de mes propres "
            u"postes, deux par quart, ordre de ne laisser passer aucun pic. "
            u"On ne demande pas trois fois a un homme ce qu'on peut tenir "
            u"soi-meme le soir meme — surtout a celui a qui l'on doit onze "
            u"jours d'hommes.")
poser(s, 'en-souffrance.json')

# ---- le livre : F.1 change de nature
P = os.path.join(D, 'books', 'affaire-sarro-vaeth.json')
d = json.load(io.open(P, encoding='utf-8'))
act = dict((t['titre'], t) for t in d['tables'])[u'⚔️ Actions']
c = act['colonnes']
for l in act['lignes']:
    if l['cellules'][0] == u'F.1':
        l['cellules'][1] = u"Appeler les dix-huit postes, et rendre le reste a la muraille"
        l['cellules'][2] = (
            u"Descendre a la chaine ce soir, ardoise et torche. Nommer les "
            u"douze de la porte des oeufs et les six du front de la onzieme, "
            u"un homme une colonne, avec ce qu'il fait et qui le nourrit. "
            u"Renvoyer tout le surplus a la muraille dans la nuit.")
        l['cellules'][c.index(u'👁️ La preuve')] = (
            u"Dix-huit noms au role des fosses, et le nombre rentre compte "
            u"par l'appel du castellan a sept heures — chez lui, pas chez moi")
        l['cellules'][c.index(u'📅 Jour dû')] = u"129.4.5"
        l['cellules'][c.index(u'📝 Note')] = (
            u"NE d'une rature. J'avais ecrit a midi que j'employais les "
            u"cinquante ; l'acte du 24e dit que la chaine a ete faite dans la "
            u"nuit et que les oeufs sont montes a l'aube. Onze jours d'hommes "
            u"sans ouvrage, demandes par moi. Je rends des postes, pas des "
            u"tetes.")
    if l['cellules'][0] == u'F.2':
        l['cellules'][c.index(u'📝 Note')] += (
            u" — LE FRONT EST DESORMAIS TENU PAR SIX DE MES POSTES, deux par "
            u"quart : je n'attends plus l'appui du castellan pour empecher un "
            u"pic d'ouvrir une poche noyee.")
with io.open(P, 'w', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=1))

print("ferme.")
