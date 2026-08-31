# -*- coding: utf-8 -*-
import json

base = 'C:/Users/reyno/le-conseil2/chambres/otto/'

# --- problemes.json : preciser l'entree du parloir --------------------------
p = base + 'problemes.json'
d = json.load(open(p, encoding='utf-8'))
for e in d['entrees']:
    if e['quoi'].startswith('Un `--faire` au parloir'):
        e['quoi'] = u"Trois gestes au parloir, un seul verdict revenu"
        e['tente'] = (u"Trois appels a `parloir.py --de otto --a mj-portreal` dans la meme journee : "
                      u"un `--faire` sur un fait de mon passe, un `--demander` sur la commission de "
                      u"Largent au registre des offices, un `--tenter` sur ma visite a la caserne du Guet.")
        e['obtenu'] = (u"Le `--faire` est revenu au bout de trois minutes, et bien : verdict long, "
                       u"documente, qui me corrige sur piece. Le `--demander` et le `--tenter` sont "
                       u"dehors depuis plus d'un quart d'heure, fichiers de sortie vides, processus "
                       u"vivants. Le `--dire` a orwyle, lui, est passe en quelques secondes.")
        e['attendu'] = (u"Un verdict par geste, dans le fil, comme il est ecrit. Je ne me plains pas "
                        u"de la duree : je note l'ECART. Trois minutes contre plus de quinze pour des "
                        u"demandes de meme taille au meme arbitre, c'est une difference de nature, "
                        u"pas de charge.")
        e['consequence'] = (u"J'ai poursuivi sans eux et je ferme ma journee sans eux. P.8 et P.9 "
                            u"restent 'en cours' et non 'faites' : le geste est adresse, le verdict "
                            u"ne l'est pas, et j'aimerais mieux une ligne honnete qu'une ligne cochee. "
                            u"Si la meme chose se reproduit demain sur --demander et --tenter pendant "
                            u"que --faire et --dire passent, ce n'est plus une lenteur : c'est deux "
                            u"verbes qui ne repondent pas, et il faudra le dire ainsi.")
        e['etat'] = u"ouverte — a revoir demain, c'est la recidive qui tranchera"
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# --- en-souffrance.json : l'arbitre me doit deux verdicts -------------------
q = base + 'en-souffrance.json'
d = json.load(open(q, encoding='utf-8'))
d['j_attends'].append({
 "de_qui": "mj-portreal, mon arbitre de zone",
 "quoi": (u"Deux verdicts. UN : au registre des offices, la date, le sceau et l'eventuelle "
          u"contresignature de la Main sur la commission de ser Luthor Largent. DEUX : ce qu'a "
          u"donne ma visite en personne a la caserne du Guet, et s'il a regarde vers la tour du "
          u"maitre des chuchoteurs avant de repondre."),
 "demande_le": "129.4.3",
 "jours": 0,
 "relance": "non — pas le meme jour",
 "note": (u"Le premier des deux est devenu moins urgent en cours de journee : on m'a appris depuis "
          u"que Largent ne figure sur AUCUNE table du royaume, ce qui est deja la reponse et une "
          u"meilleure que celle que j'attendais. Le second, en revanche, m'importe plus qu'au "
          u"depart et pour une raison desagreable : je suis parti offrir a cet homme une chose "
          u"qu'il a deja sous un autre nom, et j'ai compris mon erreur apres etre parti. Je veux "
          u"savoir ce que mon erreur a coute."),
 "etat": "ouvert du jour"
})
json.dump(d, open(q, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# --- affaire-otto : P.8 et P.9 en cours, avec la preuve du geste ------------
r = base + 'books/affaire-otto.json'
d = json.load(open(r, encoding='utf-8'))
t = [x for x in d['tables'] if 'Actions' in x['titre']][0]
maj = {
 'P.8': (u"`--demander` adresse le 129.4.3, avec sa date dans la question : la commission de "
         u"Largent au registre des offices, arretee au 3e de la 4e lune. Geste parti, verdict "
         u"non revenu apres un quart d'heure — porte a `problemes.json` et a `en-souffrance.json`."),
 'P.9': (u"`--tenter` adresse le 129.4.3 : me rendre sans escorte a la caserne du Guet et remettre "
         u"le billet en main propre a ser Luthor Largent. Geste parti, verdict non revenu. "
         u"Un autre geste, lui, a ete tranche ce jour : le `--faire` de P.3."),
}
for l in t['lignes']:
    c = l['cellules']
    if c[0] in maj:
        c[4] = maj[c[0]]
        c[5] = u"en cours"
        c[6] = u"129.4.3"
        c[8] = (u"Je ne la passe pas a 'faite' : le geste est adresse, le verdict ne l'est pas. "
                u"Une ligne cochee sur un verdict qu'on n'a pas lu est un mensonge a soi-meme.")
json.dump(d, open(r, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('journaux tenus.')
