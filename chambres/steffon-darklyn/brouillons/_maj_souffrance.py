# -*- coding: utf-8 -*-
import json, io, os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'en-souffrance.json')
d = json.load(io.open(p, encoding='utf-8'))

for e in d['j_attends']:
    if 'Gunthor' in e['qui']:
        e['quoi'] = "CLOS PAR SA MORT. Un mot disant s'il rouvre son quai, a quel prix, et le nombre d'hommes qu'il tient reellement"
        e['decision'] = (
            "FERME LE 4e DE LA 4e LUNE. Lord Gunthor Darklyn a ete decapite sur son propre quai le 3e de cette lune, "
            "quand ser Criston Cole a pris la ville ; la ville pillee, la flotte brulee sur ses amarres. Une seule bouche : "
            "MAREC FOSSE, intendant de Sombreval, par ecrit, ce jour, aux granges - il ne l'a PAS vu, il rend ce que portent "
            "les registres, et je le tiens RAPPORTE et non VU meme si c'est mon frere. Dix-sept jours de quai et huit jours de "
            "nouvelles se ferment par la plume du seul homme dont j'avais sali le nom dans un registre. Le chiffre des hommes "
            "reels n'existe plus : il n'y a plus d'hommes de Gunthor. Ce qui reste ouvert n'est plus lui, c'est ROBIN.")
    if 'Rhaenys' in e['qui']:
        e['decision'] = (
            "MORT AVEC LA VILLE, LE 4e. Le prix qu'elle avait mis - le nombre d'hommes reels de Gunthor contre trois jours - "
            "ne peut plus etre paye : il n'y a plus d'hommes de Gunthor, et la course de la barque ne rapporterait qu'un compte "
            "de ruines. Je ne lui porte rien et je le lui dis en face plutot que de laisser le marche pendre. Ce que je retiens "
            "d'elle : elle m'avait repondu par un chiffre a trouver plutot que par un refus, et c'etait juste ; c'est le monde "
            "qui a ote le chiffre, pas elle.")
    if 'Hask' in e['qui']:
        e['decision'] = (
            "FERME LE 4e. La ligne n'est plus suspendue, elle est morte : le destinataire est mort le 3e. Mention NON PORTE "
            "avec sa raison en toutes lettres - destinataire mort le 3e, rapporte par une bouche le 4e - et les treize dragons "
            "rendus au coffre contre sa marque, comptes piece a piece. Je n'ai pas pose ma marque sur son deuxieme etat : un or "
            "dont le destinataire est mort n'a pas de porteur. Propose en retour : que son troisieme etat porte un AGE, et qu'un "
            "or sorti non remis depuis plus de trois jours se dise tout haut a sept heures avec le nom de qui le tient.")

d['j_attends'].insert(0, {
    "qui": "Marec Fosse, intendant de Sombreval, aux granges",
    "quoi": "Le jour, l'heure et la BOUCHE par qui il sait que Robin vit - le nom de l'homme, et s'il l'a vu ou entendu dire. Rien d'autre.",
    "demande_le": "129-4-4 - billet parti ce matin, en reponse au sien",
    "relance_le": None,
    "decision": (
        "Je ne lui demande ni de voir mon neveu ni de payer pour lui : je lui demande une bouche et une date, ce qu'un intendant "
        "peut savoir sans sortir de sa cour, et je lui ecris que NE SAIS PAS est une bonne reponse. Ce qu'il m'a deja donne et "
        "qui vaut de l'or : 204 muids comptes au boisseau de sa main ce matin, dont 96 aux deux granges du haut serrures intactes ; "
        "il annonce 194 a qui demande, arrondi de vingt ans, et il dit sa marge en la disant. Ce que je lui ai repondu : son lord "
        "est Robin, il ne prend RIEN de moi, il garde le pli de protection scelle et le rend sans discuter s'il est demande sous "
        "les armes en ecrivant qui l'a pris et sous quel titre, et son registre des titres pretendus se tient EN DEUX EXEMPLAIRES "
        "dont un hors des granges.")
})

d['j_attends'].insert(1, {
    "qui": "Rhaenyra Targaryen, ma reine",
    "quoi": "Un ecrit sous son sceau disant DE QUI l'intendant de Sombreval tient un ordre tant que son lord est prisonnier",
    "demande_le": "129-4-4 - demande de vive voix devant la Table, le matin meme de la nouvelle",
    "relance_le": None,
    "decision": (
        "Je n'ai rien demande pour moi et je l'ai dit en le demandant : je ne suis lord de rien et je ne veux pas l'etre ce matin. "
        "Un intendant sans ordre qui ouvre une grange est un voleur ou un complice selon qui ecrira l'histoire, et cet homme-la "
        "nous a rendu le seul compte vrai sorti de cette ville en dix-sept jours. C'est un trait de plume et un sceau ; cela ne "
        "coute ni un homme ni un dragon.")
})

for e in d['on_attend_de_moi']:
    if '20120' in e['quoi']:
        e['etat'] = (
            "RENDUE LE 4e DE LA 4e LUNE, ET LA REPONSE EST ZERO. Le quai de Sombreval ne s'ouvre pas et ne prend aucune coque : "
            "il est aux mains de ser Criston Cole depuis le 3e, la flotte y a brule sur ses amarres. Dit a la Table le matin meme, "
            "devant la reine et lord Corlys, et non garde pour le jour de l'embarquement. Tout ce qui pendait a ce quai - le "
            "debarquement de l'ost, les six journees de route depuis la porte de terre, les vingt-cinq montures, les deux depots "
            "de route - pendait au meme clou et tombe avec lui.")

with io.open(p, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print('ok')
