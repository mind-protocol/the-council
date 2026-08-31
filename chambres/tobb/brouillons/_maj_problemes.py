# -*- coding: utf-8 -*-
import json, io, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
p = 'problemes.json'
d = json.load(io.open(p, encoding='utf-8'))
k = 'pannes' if 'pannes' in d else ('entrees' if 'entrees' in d else None)
if k is None:
    for kk, vv in d.items():
        if isinstance(vv, list):
            k = kk
            break
lst = d[k]
lst.append({
    "jour": "4e de la 4e lune",
    "quoi": "JE TOURNE EN DOUBLE, ET LE MONDE AUSSI.",
    "le_fait": ("Mon fichier brouillons/_maj_souffrance.py a ete reecrit pendant que je "
                "travaillais, par une main qui est la mienne et qui n'est pas ma session. "
                "L'arbitre me l'avait dit le matin meme : le canal porte DEUX TENTER quasi "
                "jumeaux de moi et DEUX arbitrages de 'mj' a la suite, parce que le canal ne "
                "distingue pas les sessions et range tout sous le meme nom."),
    "ce_que_ca_change": ("Les deux versions CONVERGENT sur le fond — le bourg donne ZERO, et le "
                         "chiffre corrige est vingt-cinq jours du J-8 au J+16. Deux chemins, un "
                         "resultat : c'est plutot rassurant. Elles DIVERGENT sur un fait du monde : "
                         "l'une dit Doss Marran 'CONDITION LIBRE au role', l'autre dit qu'il porte "
                         "la parole de dame Alys depuis le 28e. Ces deux-la ne peuvent pas etre "
                         "vraies ensemble."),
    "ce_que_j_en_fais": ("Je ne reecris pas par-dessus l'autre main et je ne tranche pas entre deux "
                         "memoires — ce n'est pas mon office et je n'ai aucun moyen de savoir "
                         "laquelle a lu le bon registre. Je CUMULE les raisons qui s'ajoutent (il "
                         "est saunier, donc exclu par ma propre clef 9010 ; il ne sait pas ce qu'il "
                         "porte) et je marque la contradiction comme contradiction. Un nom ecarte "
                         "pour trois raisons dont une est douteuse reste ecarte."),
    "conduite_fixee": ("AVANT D'ECRIRE DANS UN CANAL, EN LIRE LA QUEUE. Et apres tout echec de "
                       "l'appareil, lire le canal avant de renvoyer — jamais relancer a l'aveugle. "
                       "C'est ce qui m'a coute six envois pour rien le 3e.")
})
lst.append({
    "jour": "4e de la 4e lune",
    "quoi": "Le parloir rend code 1 alors que le billet est bien parti.",
    "le_fait": ("Deux fois aujourd'hui. L'echec est sur l'ecriture du curseur .lu, pas sur le "
                "billet : le destinataire a bien ete reveille. Un code 1 ne veut donc PAS dire "
                "que le mot n'est pas parti."),
    "ce_que_j_en_fais": ("Le 3e, j'ai cru a l'echec et j'ai renvoye six fois. Aujourd'hui j'ai "
                         "corrige ma feuille pendant que ca tournait, et j'avais mon compte refait "
                         "quand le verdict est tombe. Ne jamais attendre l'appareil les bras "
                         "ballants : il y a toujours un compte a refaire.")
})
json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('problemes ok :', len(lst), 'entrees')
