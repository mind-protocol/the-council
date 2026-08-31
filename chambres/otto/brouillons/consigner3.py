# -*- coding: utf-8 -*-
import io, json

base = 'C:/Users/reyno/le-conseil2/chambres/otto/'

# --- ce que je tiens pour vrai ---------------------------------------------
p = base + 'ma-memoire/ce-que-je-tiens-pour-vrai.txt'
txt = io.open(p, encoding='utf-8').read()
neuves = [
u"- Les portes de cette ville ont une DATE, et c'est le vingtieme. L'arriere de solde des manteaux d'or est de soixante-dix-huit mille cerfs, monte de six mille par jour, et le seuil ecrit est a cent quatre-vingt mille : passe ce seuil, ils cessent de tenir les portes pour qui ne les paie plus. Dix-sept jours. Trois cent soixante-dix dragons les tiennent aujourd'hui, vingt-huit de plus par jour d'attente.",
u"- Le taux du manteau d'or — trois cerfs le jour — est le compte que Daemon Targaryen a signe de sa main pour Rhaenyra, et la Couronne paie les memes hommes au meme taux. Le tarif de mes portes est de l'ecriture de mon ennemi. C'est la troisieme fois en deux jours que je trouve sa main sous un office que je croyais mien.",
u"- Deux livres du roi donnent le coffre a un contre soixante-dix : six cent mille dragons d'un cote, huit mille six cents de l'autre, et le second descend de vingt et un mille cerfs par jour. J'ai failli signer dix-huit mille dragons d'avance, soit deux fois le coffre entier si c'est le petit chiffre qui est vrai. Un chiffre qui descend a ete compte ; un chiffre rond et immobile a ete rapporte.",
u"- Aucune levee de ce royaume n'a jamais porte au livre une solde de depart par tete. Il n'y a pas de precedent — ni a suivre, ni a m'opposer. Ce que j'ecrirai FERA le precedent, et c'est la premiere fois de ma vie d'office que j'ecris sur une page reellement blanche.",
u"- Quatre choses ecrites dans quatre livres et jamais posees ensemble : l'ost sort le 5e, la garde des portes expire le 20e, cent vingt lances sans maitre dorment dans les murs depuis le 22 et onze d'entre elles gardent trois quilles de guerre sur la Nera pour un maitre sans nom, et la porte se vend a l'heure faute de solde. Je ne dis pas que c'est arrange. Je dis que si quelqu'un l'avait arrange, cela ressemblerait a ceci — et que nous le ferions pour lui.",
]
marque = u"j'ai le droit de me tromper.\n"
i = txt.index(marque) + len(marque)
txt = txt[:i] + u"\n" + u"\n\n".join(neuves) + u"\n" + txt[i:]
io.open(p, 'w', encoding='utf-8').write(txt)

# --- ce que j'ai appris -----------------------------------------------------
q = base + 'ma-memoire/ce-que-jai-appris.txt'
io.open(q, 'a', encoding='utf-8').write(u"""

[129.4.3] J'ai demande au Tresor la solde d'une marche et le Tresor m'a rendu la date de mes portes. L'arriere du Guet est a soixante-dix-huit mille cerfs, il monte de six mille par jour, le seuil ecrit est a cent quatre-vingt mille, et passe ce seuil il est note en toutes lettres que les manteaux d'or cessent de tenir les portes pour qui ne les paie plus. Dix-sept jours. J'ai passe une lune entiere a me demander pourquoi ces officiers refusaient ma contresignature, et j'ai monte tout un plan sur la regularisation de leur office — et pendant ce temps le seul nombre qui comptait courait vers une date que personne ne m'avait dite. Trois cent soixante-dix dragons. C'est la plus petite somme de tout ce dossier et c'est celle qui tient la ville. On ne l'a pas regardee pour cette raison exacte : elle etait trop petite pour qu'on la regarde. Je note la regle : dans un dossier ou tout le monde discute des grands nombres, la chose qui tue est toujours dans les petits.
   (source : le livre des mains, taux et arriere du Guet avec leur pente et leur seuil, obtenu au parloir le 3e)

[129.4.3] Et le taux lui-meme est de la main de Daemon. Trois cerfs le jour par manteau d'or : c'est le compte qu'il a signe pour Rhaenyra, et la Couronne paie les memes hommes au meme taux. Troisieme fois en deux jours que je trouve la main d'un autre sous un office que je croyais mien — la cire du Pied-Bot sur le commandement de Largent, les brevets de Daemon sur quatorze de mes dix-neuf geoliers, et maintenant son ecriture sur le tarif de mes propres portes. Ce n'est plus une serie de coincidences, c'est une methode, et elle est meilleure que la mienne : je passe mon temps a acheter des signatures pendant qu'on ecrit les baremes.
   (source : la meme reponse, note sur l'origine du taux)

[129.4.3] Le coffre. Deux livres de la Couronne, six cent mille dragons contre huit mille six cents, facteur soixante-dix, et le petit descend de vingt et un mille cerfs par jour. J'avais deja fait partir l'ordre de porter quatre ecritures au livre, dont une avance de dix-huit mille dragons : deux fois le coffre entier si c'est le petit chiffre. Je l'ai repris entre ma table et le livre, sans rature, la feuille n'entre pas. Ce que j'en tire et que je veux relire : un chiffre qui DESCEND a ete compte, un chiffre rond et immobile a ete rapporte. Le six cent mille n'a pas de pente, et un tresor sans pente n'a jamais ete ouvert par celui qui l'a ecrit. Je fais desceller et compter piece par piece devant le gardien et deux clercs qui ne se connaissent pas, et je ne signe rien avant le cinquieme au matin. J'ai ecrit cette date a Criston, ce qui me l'interdit de repousser.
   (source : contradiction relevee entre le livre des mains et le verrou 72001 du plan de la Couronne, le 3e)

[129.4.3] Il n'existe aucun precedent de solde de depart dans ce royaume : ni somme par tete, ni levee datee, nulle part. Je m'y attendais si peu que j'avais bati une clef entiere sur l'idee qu'il fallait NOMMER la chose — avance ou prime — parce que le chiffre manquait. J'avais raison sur le nom et je ne savais pas a quel point : il n'y a pas de chiffre a retrouver, il y a un chiffre a creer, et ce que j'ecrirai fera le precedent pour tous ceux qui viendront apres. C'est la premiere page reellement blanche de ma vie d'office. On ne me pourra rien opposer ; on m'opposera tout, dans dix ans, a partir de ce que j'aurai mis.
   (source : la reponse du parloir, en toutes lettres : de solde de depart, rien)
""")
print('consigne.')
