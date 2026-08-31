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
        c[4] = ("le relevé de l'aire de bris : arrivés le même jour avec quarante brasses de trois-torons neuf. Et mon propre "
                "compte du 1er, en toutes lettres : Hann monté aux chemins de la Néra avec l'aussière « ET LA MARQUE NON "
                "REGARDÉE », un prix demandé et rien d'autre.")
        c[5] = ("L'AUSSIÈRE PORTE UNE MARQUE, et elle dort à douze pas de mon feu. Je l'ai portée sur mon épaule, Hann l'a "
                "montée la vendre, aucun des deux n'a retourné le toron. Lue à la lanterne le 3e au soir. Puis, et sans "
                "donner un nom : la corderie prend à la quinzaine et ne paie qu'au quinzième jour — je demande à MA corderie "
                "partenaire qui a été pris et n'est pas revenu à la quinzaine d'avant. Un homme sans métier qui part avant "
                "son quinzième jour part sans un sou ; celui qui part avec quarante brasses de neuf s'est payé en nature.")
    if c[0] == 'V.10':
        c[5] = ("Le nom ne sortira d'aucun registre : leur seule ligne connue, celle du 22, porte une destination fausse que "
                "le sergent de la porte de Fer ne sait pas attribuer. Mais LA CORDERIE EST SOUS LA NÉRA ET LE CHANTIER "
                "DERRIÈRE LES ENTREPÔTS À SEL — deux bouts du même bord d'eau, une seule corderie entre les deux, ET C'EST "
                "LA MIENNE. Quarante bras, deux galères sur bers et une quille consomment le filin par centaines de brasses. "
                "Je ne demanderai pas un nom : je demanderai un COMPTE — combien de brasses sont descendues vers l'aval sur "
                "trente jours, à quel quai, payées comment, portées par qui.")

acts['lignes'].append({"cellules": [
 "M.11",
 "🪢 Lire la marque, puis demander un compte de quinzaine — jamais un nom",
 "DEUX temps, et pas dans l'autre ordre. UN : dérouler l'aussière sur le billot à la lanterne et la suivre d'un bout à l'autre — marque de corderie au départ du toron, repère de longueur, et l'endroit où la marque a été COUPÉE : quarante brasses d'un seul tenant viennent d'un plus long, et on ne coupe pas au hasard, on coupe là où c'est écrit. La rerouler du même sens sur le même appui. DEUX : monter à ma corderie partenaire avec deux questions de compte et zéro nom — qui a été pris à la quinzaine d'avant et n'est pas revenu au quinzième jour ; et combien de brasses sont descendues vers l'aval sur trente jours, à quel quai, payées comment, portées par qui.",
 "sous l'auvent, à douze pas du feu — puis la corderie sous la Néra",
 "la marque lue et écrite sur la planchette, et un compte de quinzaine obtenu sans avoir prononcé un nom",
 "en cours",
 "129.4.3 au soir, puis le 4e",
 "",
 "Lève V.9, et attaque V.10 par le seul bout qui existe : aucune corderie du port n'a de registre qu'on puisse ouvrir, mais la corderie est SOUS LA NÉRA et le chantier du bout DERRIÈRE LES ENTREPÔTS À SEL — deux bouts du même bord d'eau, une seule corderie entre les deux, et c'est la mienne. On ne demande pas un nom, on demande un compte : le nom sort tout seul de la bouche de l'autre, et je n'apprends à personne ce que je cherche."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
