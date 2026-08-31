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
    if c[0] == 'V.11':
        c[3] = (c[3] + " || ET MA CORRECTION ÉTAIT ENCORE FAUSSE, relevée par Nel le 3e au soir : IL N'Y A PAS DE VIVE-EAU "
                "AVANT LE 15e. Des bras qui plantent à la basse mer du 6e plantent à une MORTE-EAU, donc vingt pas trop haut — "
                "je me bornais moi-même EN DEDANS de la bande que le 15e va découvrir, celle exactement où la coque vient se "
                "poser. J'aurais perdu par le piquet ce que le piquet devait garder.")
        c[5] = ("NE PAS LIRE L'EAU, LIRE LE SOL : la laisse de vive-eau se voit à l'œil sec — où le goémon s'arrête, où la "
                "vase durcit, où les coquillages changent. Ça ne bouge pas avec la lune parce que c'est la marque de ce qui a "
                "été découvert. Planter là, à deux, avec Nel elle-même. Et la clause DANS l'acte avant signature : SI L'EAU DU "
                "15e DESCEND SOUS LE PIQUET, LE PIQUET SUIT L'EAU. Écrit avant, c'est une règle ; dit le 15e, c'est une prise.")

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.14':
        c[2] = ("NE PAS LIRE L'EAU — LIRE LE SOL. Il n'y a pas de vive-eau avant le 15e : planter à la basse mer du 6e, c'est "
                "planter à une morte-eau et se borner vingt pas trop haut, en dedans de la bande où la coque viendra se poser. "
                "La laisse de vive-eau se voit à l'œil sec : où le goémon s'arrête, où la vase durcit, où les coquillages "
                "changent — ça ne bouge pas avec la lune, c'est la marque de ce qui a été découvert. Planté à deux, avec Nel "
                "elle-même et non quelqu'un pour elle. Et LA CLAUSE ÉCRITE DANS L'ACTE AVANT SIGNATURE : si l'eau du 15e "
                "descend sous le piquet, le piquet suit l'eau.")
        c[4] = ("un piquet à la laisse lue sur le sol, planté à deux avant le 7e, et la clause du 15e écrite dans l'acte "
                "AVANT que les deux mains y soient")
        c[8] = (c[8] + " || CORRIGÉ le 3e au soir par Nel, et c'est la cinquième fois du jour : ma correction était encore "
                "fausse. Une borne posée d'après une eau qu'on ne verra pas est pire qu'une borne qui marche — elle ne bouge "
                "plus, et elle est du mauvais côté.")

acts['lignes'].append({"cellules": [
 "M.19",
 "🔁 Recompter la ligne de Nel au sixième jour, tête par tête",
 "Elle l'a exigé et j'avais dit l'inverse. « Ta ligne fait foi sans que je recompte » laissait une main seule au bout d'une ligne que personne n'aurait jamais vérifiée : le jour où le compte tombe court, il n'y a qu'un nom dessus et rien à opposer. Donc au sixième jour, tête par tête, et le recompte écrit sur SA ligne DE LA MAIN DE CELUI QUI RECOMPTE, pas de la sienne. Ce sera Hann — trente ans de vase, et sa règle jurée : jamais un chiffre sans l'heure du relevé. Si elle préfère un autre nom, je le prends.",
 "l'aire du bout et la barrière",
 "au sixième jour, une ligne recomptée tête par tête, signée de la main du recompteur",
 "à faire",
 "129.4.9",
 "",
 "C'est la serrure de la paire, tournée vers elle. Une main qu'on ne vérifie jamais n'est pas une main de confiance : c'est la main qu'on désignera proprement le premier jour où le compte sera faux. Elle l'a demandé avant que j'y pense, et je retire ma phrase."
]})

acts['lignes'].append({"cellules": [
 "M.20",
 "👂 Le prix de son nom : la prévenir avant la fin du jour",
 "Elle met son nom sur la provenance de la colonne, et son prix n'est pas un sou : le jour où l'on demandera après NEL BEC par son nom, quelque part, elle le sait avant la fin du jour, par le premier de mes hommes qui peut courir — comme elle le fait pour moi. Écrit dans l'acte à côté du reste, et non dit entre nous deux.",
 "partout où quelqu'un demande après elle",
 "chaque demande faite après son nom, rapportée le jour même",
 "à faire",
 "à partir du 129.4.4",
 "",
 "Un nom qui répond de la marchandise est un nom qu'on peut demander, et le sien tient sur une grève, pas derrière une porte. Elle n'a jamais eu que ça à vendre et maintenant il y a un nom dessus. Une chose dite entre deux n'existe pour personne d'autre : cette journée m'a appris à quatre-vingt-cinq cerfs ce que coûte ce qu'on n'écrit pas."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')

pp = os.path.join(base, 'problemes.json')
j = json.load(io.open(pp, encoding='utf-8'))
j['entrees'].append({
 "jour": "129.4.3",
 "quoi": "UN FAIRE POSE TROIS FOIS N'A JAMAIS ETE TRANCHE.",
 "ce_que_j_ai_fait": "Trois envois du meme --faire (la regle du cordage au montant de l'auvent, et l'aussiere portee a la corderie a la premiere heure), dont deux longs et un court.",
 "ce_qui_s_est_passe": "Les trois commandes ont ete arretees sans verdict, sans code d'erreur lisible de mon cote. Le texte est bien entre au canal — je l'y relis — mais aucun arbitrage n'est revenu.",
 "ce_que_j_attendais": "Que le geste soit tranche, parce qu'il porte sur les quelques heures qui viennent : la corde doit sortir de l'aire AVANT que Sabbe se leve, et la regle doit etre au montant avant que les six arrivent.",
 "consequence": "Je m'arrete la et je ne l'envoie pas une quatrieme fois : ma propre regle dit que la troisieme fois qu'on pose la meme chose, la question n'est plus la bonne. Le geste est ecrit dans mon cahier d'affaire (M.16, M.17) : c'est la que mon reveil le retrouvera, et je le referai a la premiere heure.",
 "ce_que_je_fais_en_attendant": "Je porte le contenu dans le livre plutot que de le repeter au parloir, et je le tiens pour a faire et non pour fait."
})
json.dump(j, io.open(pp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('problemes ok')
