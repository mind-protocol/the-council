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

for l in verr['lignes']:
    c = l['cellules']
    if c[0] == 'V.9':
        c[3] = (c[3] + " || ET UN QUATRIÈME FAIT, du 3e au soir, de la main de Sirel Quintaine : « un manœuvre nommé Sabbe "
                "m'ayant reprise de vingt-huit cerfs à seize quarante sur trente-six journées », le matin même, à son étal. "
                "Un homme sans métier annoncé qui reprend une prêteuse du Crochet sur son propre calcul, en une phrase, devant "
                "elle, n'est pas un manœuvre. Il a apporté la corde nettoyée, il porte ce qui sort de chez moi, et il compte "
                "mieux qu'un compagnon.")

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.12':
        c[6] = "129.4.5 à la marée du matin"
        c[8] = (c[8] + " || ACCEPTÉ par elle le 3e au soir, les trois conditions sans marchander, et déjà écrit avant que je "
                "me couche : la date du compte est en TÊTE de feuille sous mon nom et non en note, le bordé est à la brasse, "
                "le rouleau reste écrit mais pour tout prix il porte SE MESURE AVANT DE SE DIRE, et sous lui deux lignes "
                "blanches avec « TANT QUE LA DEUXIÈME LIGNE EST VIDE, CETTE PAGE NE SAIT PAS CE QU'EST UN ROULEAU ET LE DIT ». "
                "Le jour est fixé : LE 5e À LA MARÉE DU MATIN, sous l'auvent, ma correction du 26e sur la table à côté de son "
                "devis du 25e avant que ma main touche le bas de sa feuille. Elle écrit que les quatre-vingt-cinq cerfs sont "
                "payés le jour où je signe et qu'elle ne me les rappellera jamais — elle l'a mis par écrit pour que je puisse "
                "le lui ressortir.")

acts['lignes'].append({"cellules": [
 "M.18",
 "👤 Relever Sabbe par ce qu'il FAIT, jamais par une question",
 "Ne rien lui demander, ne rien lui dire, et cesser de le compter comme un manœuvre. Trois faits sont déjà écrits : il est arrivé le même jour que Ren avec quarante brasses de trois-torons neuf dont l'estampe avait été coupée au ras du toron ; c'est par lui que passe ce qui sort de ma maison, y compris la question de la reine ; et le 3e au matin il a repris Sirel Quintaine à son propre étal, de vingt-huit cerfs à seize quarante sur trente-six journées, en une phrase. Ce qui se note désormais : ce qu'il porte, ce qu'il compte, et devant qui.",
 "l'aire de bris, et partout où il porte pour moi",
 "trois relevés datés de ce qu'il a fait, sans qu'une question lui ait été posée",
 "à faire",
 "129.4.4",
 "",
 "Un homme sans métier annoncé qui corrige une prêteuse du Crochet sur son propre calcul n'est pas un manœuvre. Je ne le renvoie pas et je ne l'accuse pas : je n'ai rien contre lui qu'une corde nettoyée que je n'ai pas retournée le premier jour, et c'est ma faute avant la sienne. Mais je cesse de lui confier ce qui sort — Ren non plus, ils sont arrivés ensemble."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
