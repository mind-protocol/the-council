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
    if c[0] == 'V.12':
        c[5] = ("Deux gestes, pas un. UN : la règle au montant — tout cordage s'ouvre à la main avant d'être mis en prise, "
                "l'âme regardée, le mou refait au commettage ; Hann la passe sur LES TROIS filins du dépôt en commençant par "
                "celui du haut, pas par celle-ci. DEUX : elle SORT de l'aire à la première heure, portée à deux, sur l'épaule, "
                "par la rue, et dit tout haut avant que personne ne se lève. Une corde qui disparaît de nuit accuse ; une corde "
                "qu'on emporte à deux au grand jour ne raconte rien. Quand il ira la chercher, elle n'y sera plus et il saura "
                "où elle est.")

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.11':
        c[5] = "faite"
        c[7] = "129.4.3"
        c[8] = ("FAITE, et le second temps est annulé au profit de M.16. La marque : ESTAMPE COUPÉE au ras du départ du toron, "
                "proprement, là où c'est écrit — par quelqu'un qui savait où couper — et le fil de couleur intact dans l'âme : "
                "la corderie sous la Néra, celle de ma propre maison. Je ne tiens pas un nom, je tiens la preuve qu'un nom a "
                "été retiré et l'endroit où il était écrit. Je NE demanderai PAS qui est parti avant son quinzième jour : cette "
                "question n'apprend rien sur le moment et tout plus tard — on y répond sans y penser et l'on s'en souvient le "
                "jour où le nom vaut quelque chose. J'achèterais un délai au prix d'un aveu.")
    if c[0] == 'M.16':
        c[2] = (c[2] + " || ET LEUR DEMANDER LA SEULE CHOSE QU'UN HOMME DU MÉTIER DEMANDE EN PAREIL CAS, qui ne renseigne "
                "personne sur ce que je cherche : QU'ILS LA RECOMMETTENT ET Y REMETTENT LEUR MARQUE À MON NOM. Une corde "
                "réparée sous leur estampe et à mon nom cesse d'être à quelqu'un d'autre.")
        c[4] = ("une réponse rapportée sans que j'aie prononcé un nom ni une date de départ — et quarante brasses recommises "
                "portant leur marque neuve à mon nom")
        c[6] = "129.4.4 à la première heure"
        c[8] = (c[8] + " || Et c'est le seul geste de la journée qui me RENDE quelque chose au lieu de m'en coûter.")

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
