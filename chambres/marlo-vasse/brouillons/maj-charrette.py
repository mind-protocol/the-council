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
 "V.16",
 "Trente-deux journées d'hommes sans un seul moyen de rouler",
 "M.2 — Une coque sur l'aire à la vive-eau du 15e",
 "J'ai porté quatre bras du 7e au 14e à l'aire du bout — dévaser, creuser le ber, poser les cales — et je n'ai écrit nulle part avec QUOI on sort la vase ni avec quoi on amène le bois de ber, les cales et les pieux. Un ber ne se creuse pas à mains nues et la vase sortie qu'on laisse sur place retombe à la marée suivante. Trente-deux journées d'hommes sans un moyen de roulage, ce sont trente-deux journées payées pour déplacer un tas de deux pas.",
 "M.5, écrit le 3e : quatre bras, huit jours, aucun poste de roulage, aucun matériau nommé",
 "Une charrette et son meneur, à la journée et non au voyage, du 7e au 14e. Doye Rouelle, du Culpucier — charrette à onze cerfs, ni alliée ni adversaire : c'est un prix, pas une allégeance."
]})

acts['lignes'].append({"cellules": [
 "M.23",
 "🛒 La charrette de Doye Rouelle, à la journée, du 7e au 14e",
 "Louer charrette et meneur à la JOURNÉE et non au voyage — je ne veux pas qu'on se dépêche, je veux que le ber soit creusé pour la vive-eau du 15e. Bois de ber, cales, pieux, et la vase à sortir. Huit journées si elle les veut, trois, ou une pour voir ; rien ne l'engage au-delà de la journée commencée. Trois conditions dites AVANT sa réponse : une ligne écrite par jour — chargé quoi, d'où à où, heure du chargement — copie gardée sur l'aire ; aucune heure de départ convenue, jamais ; et elle ne porte rien pour moi qui ne soit pas sur sa ligne.",
 "devant l'entrepôt, à six pas de la Gadoue",
 "huit lignes de roulage écrites, et un ber creusé au 14e au soir",
 "en cours",
 "129.4.7",
 "",
 "Lève V.16. Deux questions de compte lui ont été posées et aucune question de nom : ce que vaut la journée d'une charrette au Culpucier, et combien de voyages se font d'ici aux entrepôts à sel. La seconde me dit l'état du trafic vers le chantier du bout sans que j'aie prononcé son nom. Et je ne marchande pas son premier chiffre — un homme qui marchande un prix qu'il n'a pas su calculer paie deux fois."
]})

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.5':
        c[2] = (c[2] + " || AVEC UN MOYEN DE ROULAGE, sans quoi ce sont trente-deux journées payées à déplacer un tas de deux "
                "pas : charrette et meneur à la journée, du 7e au 14e (M.23).")

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
