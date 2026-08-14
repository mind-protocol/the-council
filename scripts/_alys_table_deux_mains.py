# -*- coding: utf-8 -*-
"""La feuille a deux mains — Alys Grive (gorges) et Tobb (jambes). Table ajoutee au cahier 65xxx."""
import json, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = 'etat/books.json'
shutil.copy(P, P + '.avant-table-deux-mains')
books = json.load(open(P, encoding='utf-8'))
livre = next(e for e in books if e['id'] == 'affaire-role-des-bouches')
TITRE = "\U0001f9fe Le compte à deux mains — une ressource, ses preneurs, leurs jours"
livre['tables'] = [t for t in livre['tables'] if t['titre'] != TITRE]

COLS = ['\U0001f9f0 N°', '\U0001f5e3️ La ressource réelle', '⚔️ Qui la prend', '\U0001f4c5 Quel jour',
        '⚠️ Ce qui se heurte', "✍️ De quelle main"]
def R(*c): return {'cellules': list(c)}

lignes = [
 R('**M15**', "\U0001f5e3️ **G1 — la gorge des séchoirs.** Rend un refrain sans qu'on le lui apprenne. Éprouvée le 1er de la 4e lune.",
   '⚔️ 66020 · ⚔️ 34220 *(« trois lecteurs du bourg »)*', "J−5 pour 34220 ; déjà tenue pour 66020",
   "Rien encore. **Mais 34220 dit « trois lecteurs » et non trois numéros** : le jour venu, on ira les chercher, et ce seront ceux-là.", 'Alys Grive'),
 R('**M15**', "\U0001f5e3️ **G2 — la gorge des claies.** Accroche une désignation à la fin de toute forme qu'on lui donne : cinq endroits mesurés. Ne déforme pas un récit sans case.",
   '⚔️ 66020 · ⚔️ 34220 · ⚔️ 34021 *(l\'essai devant qui ne lit pas)*', "J−24 pour 34021 ; J−5 pour 34220",
   "**34021 mesure ce qui est retenu, et 34220 ce qui est redit — par la même gorge, qui déforme au même endroit.** Deux mesures, un seul biais, et l'on croira mesurer deux fois.", 'Alys Grive'),
 R('**M15**', "\U0001f5e3️ **G3 — la gorge du banc, aux claies.** A donné le verbe PORTER LE NOM. Rend le passif en actif : ce qu'elle dit n'est jamais ce qu'on a écrit.",
   '⚔️ 66020 · ⚔️ 34021', 'J−24', "Rien. Écrite pour qu'on cesse de la confondre avec G1.", 'Alys Grive'),
 R('**M15**', "\U0001f5e3️ **G4 — le coureur du bourg.** A porté le pourquoi de la fermeture aux trois villages et au marché du nœud, le 28e, de bouche.",
   '⚔️ 10031 *(le mot aux villages)* · ⚔️ 34220', "J−6 pour 10031 ; J−5 pour 34220",
   "**Un jour d'écart, et c'est le même homme.** Et ⚡ 10031 déclare **M18 — les nouvelles** pour payer un crieur : un crieur est une gorge, pas une nouvelle. **Mal déclaré, donc invisible au compte.**", 'Alys Grive'),
 R('**M15 ?**', "\U0001f5e3️ **G5, G6, G7 — les trois gorges de Port-Réal.** N'existent pas encore : ⚡ 6120 doit les nommer.",
   '⚔️ 6122 *(chanter, 3 soirs/semaine)* · ⚔️ 41222 *(faire descendre un ordre)* · ⚔️ 6128 *(les éteindre toutes)*',
   "J−28 pour 6122 ; **J−22 pour 41222** ; 6128 au signal, sans délai",
   "**LE CONFLIT DUR.** \U0001f5dd️ 6013 interdit qu'une bouche porte à la fois une chanson et un pli — et ⚡ 41222 prend nommément « trois bouches déjà tenues (6120) ». Puis ⚡ 6128 les éteint toutes trois au premier des nôtres arrêté **sans citer 41000** : le jour où je coupe, le plan perd son calendrier. Trois cahiers, aucun ne voit les deux autres. → \U0001f512 66001",
   'Alys Grive'),
 R('**M15 ?**', "\U0001f5e3️ **G8 — la gorge de La Gaffe qu'on ne paie pas** (Hobb Sole). Son ignorance EST la sûreté du canal.",
   '⚔️ 6123 · ⚔️ 6131 · **et ⚡ 41222 se tient sous la même arche**', 'J−28, J−26 ; J−22 pour 41222',
   "⚡ 41222 fait descendre son vers **à La Gaffe, sous l'arche** — le lieu même qu'on a juré de ne jamais approcher d'une main qui sait. Une gorge qu'on protège en ne l'approchant pas, et un essai qu'on vient jouer chez elle.", 'Alys Grive'),
 R('**M18 ?**', "\U0001f5e3️ **G9 — les lecteurs des trois villages.** Un seul sûr : le septon du premier. Le fils du meunier au troisième. **Au deuxième, personne.**",
   '⚔️ 10031', 'J−6',
   "Le texte est prêt et la gorge manque. **Ce n'est pas un trou de texte, c'est un trou de gorge, et le cahier de la route n'a pas de case où l'écrire.**", 'Alys Grive'),
 R('**sans n°**', "\U0001f9b5 **Les deux jetons de coureur, coupés le 22e.** *(à confirmer et compléter par Tobb, coureur — la ligne est ouverte pour sa main)*",
   '⚔️ 34123 *(paquets lointains — un coureur pour Harrenhal)* · ⚔️ 34126 *(trois copies par la route du sel, Nesse — six jours de marche)*',
   'J−8 pour 34123 ; J−10 pour 34126',
   "**Deux lignes du même cahier prennent les mêmes jambes à deux jours d'écart, sans se citer.** Et ⚡ 34126 note que son passage est **aussi celui du 8000**. Ni l'une ni l'autre ne déclare un moyen numéroté : pour le compte, ces jambes **n'existent pas**.", 'Tobb — *ligne ouverte*'),
 R('**—**', "\U0001f4d0 **CE QUE LA FEUILLE MESURE, ET C'EST LE VRAI CHIFFRE.** Neuf lignes de six cahiers dépensent une gorge. **Deux** citent M15 par son numéro — et l'une des deux est la mienne, écrite ce matin. Une déclare M18 pour payer un crieur. Six ne déclarent rien.",
   '—', '—',
   "**Un moyen nommé en clair n'existe pas pour le compte.** C'est pourquoi personne n'a vu que trois cahiers achetaient les mêmes trois gorges : il n'y avait rien à voir. Le défaut n'est pas dans les gorges, il est dans la déclaration.",
   'Alys Grive et Tobb'),
]

livre['tables'].append({'titre': TITRE, 'colonnes': COLS, 'lignes': lignes})
json.dump(books, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('table posee :', TITRE, '|', len(lignes), 'lignes')
