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
 "V.8",
 "Mon devis du 26e est faux de quatre-vingt-cinq cerfs, et il court la ville dans la poche d'une prêteuse",
 "C.5 — Les six sont payés jusqu'à la vive-eau du 15e",
 "Je l'ai écrit le soir du 25e en recopiant le chiffre de l'avant-veille, sans recompter après une vente faite le MATIN MÊME par mon second. Dix-huit membrures au papier, DOUZE sur l'aire — six parties aux Trois-Marches le 25e au matin. Deux rouleaux de bordé au papier, UN sur l'aire — le second parti le 27e à la première marée. Au barème du 3e le lot vaut CENT QUARANTE-TROIS cerfs ; mon devis en fait porter deux cent vingt-huit. Quatre-vingt-cinq cerfs de bois déjà vendu que mon papier promet encore : quatre mille sept cent soixante sous, trente-trois journées des six. Et le papier n'est pas chez moi : parti plié en quatre le 26e sans copie gardée, il sert à placer le lot contre le cinquième. Le jour où un acheteur comptera les membrures, c'est mon nom au bas de la feuille.",
 "recompte pièce par pièce contre le devis remis le 26e ; les deux ventes datées, 25e au matin et 27e à la première marée",
 "Fait le 3e à la chandelle : la correction du 26e, datée et signée, le faux et le vrai côte à côte sans effacer la première colonne, trois copies — au montant, à l'ardoise, et portée contre reçu à qui détient le devis. Et le bordé ne se vend plus au rouleau mais à la brasse : quarante et un sous la brasse."
]})

verr['lignes'].append({"cellules": [
 "V.9",
 "Les deux bouches de ma maison vers le dehors sont arrivées ensemble, le même jour, avec la même corde",
 "C.6 — Je sais qui achète, et par quelle porte l'argent entre",
 "Sabbe, quarante ans, aucun métier annoncé, et Ren, quatorze ans : arrivés le même jour au chantier de la vase avec QUARANTE BRASSES de trois-torons neuf d'un seul tenant, données pour le travail, sans un mot d'où ni de jusqu'à quand. Et ce sont ces deux-là que j'emploie pour tout ce qui sort de chez moi : Ren a porté mon arrangement à la relève du Guet le 29e, et c'est par Sabbe que j'ai renvoyé la question de la reine. Quarante brasses d'un seul tenant ne s'enlèvent pas à l'étal : il faut un nom au contrat. Je ne l'ai jamais demandé, et j'ai relevé quatre portes de mes pieds pendant ce temps.",
 "le relevé de l'aire de bris : deux des six ne sont là que par moi, arrivés le même jour avec quarante brasses de trois-torons neuf",
 "Le nom porté au contrat de corderie, avec sa date et sa quantité — demandé aux registres le 3e au soir. Et le même nom cherché par l'autre bout : quarante bras et deux galères au chantier du bout consomment du filin par centaines de brasses ; un homme peut se payer comptant et rester sans nom, sa corde non."
]})

verr['lignes'].append({"cellules": [
 "V.10",
 "Je mets quatre bras le 7e à l'aire du bout, mitoyenne d'un chantier de quarante bras qui n'a aucun nom",
 "M.2 — Une coque sur l'aire à la vive-eau du 15e",
 "Derrière les entrepôts à sel : deux galères sur bers, une troisième quille, quarante bras payés comptant, aucun nom nulle part. Je cherche depuis cinq jours qui paie ce chantier — pour lui vendre mon bois — et je ne l'ai pas trouvé. À partir du 7e, mes quatre bras dévaseront un ber à sa porte, huit jours de suite, en plein jour. Ils le verront, et ils seront vus. Je ne peux pas décider si c'est mon meilleur client ou l'homme qui paie les gosses de ma barrière tant que je n'ai pas son nom.",
 "quatre portes relevées, le chantier du bout compté de nuit ; « aucun nom nulle part », et un tiers y a déjà porté copie à la grille",
 "Le nom de qui paie le chantier du bout, écrit et tenu de deux bouches qui ne se connaissent pas. Tant qu'il manque, les quatre bras du 7e travaillent le dos tourné à une porte dont j'ignore de quel côté elle s'ouvre."
]})

acts['lignes'].append({"cellules": [
 "M.10",
 "🧾 La correction du 26e — mon faux devis, rendu juste avant qu'il coûte à un autre",
 "Écrire à la chandelle la correction datée et signée du devis du 26e : le devis faux et le recompte côte à côte, sans effacer la première colonne. Trois copies de la même main — une clouée au montant de l'auvent, une à l'ardoise de l'aire, une portée dès le matin à qui détient le devis, contre reçu. Et la ligne qui vaut pour tout ce qui sortira : le bordé se vend à la brasse, quarante et un sous, jamais plus au rouleau.",
 "sous l'auvent, puis chez qui détient le devis",
 "un reçu de la main de qui détient le devis, et la correction lisible au montant par tout homme qui passe",
 "en cours",
 "129.4.4 au matin",
 "",
 "Lève V.8. Un compte raturé se relit, un compte effacé se refait. Je ne négocie pas le cinquième de la prêteuse et je ne demande rien en échange : je rends le chiffre juste, et je le rends avant qu'il coûte à un autre que moi. C'est aussi la première feuille qui sort de chez moi avec sa copie gardée — M.4 commence par celle-là."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
