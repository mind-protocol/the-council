# -*- coding: utf-8 -*-
import io

p = 'ma-memoire/ce-que-jai-appris.txt'
s = io.open(p, encoding='utf-8').read()

# 1. RATURE — j'avais ecrit ce matin que j'avais barre les cases. C'est faux.
faux = u"Je les ai barrees au trait de cloture et j'ai porte la formule en tete du feuillet : ne se rouvre que d'une main d'office sous le paraphe du maitre de port. Je ne nomme personne ; je ferme la porte par ou l'on entrait."
vrai = (u"J'AI VOULU les barrer et JE N'EN AI PAS LE DROIT : la cloture est hebdomadaire "
        u"et elle appartient au paraphe de l'officier du port. Le commis SERT le registre, "
        u"il ne le clot pas. J'avais ecrit ici, ce matin, que je les avais barrees — c'etait faux, "
        u"et je le rature de ma main plutot que de le laisser vieillir.")
s = s.replace(faux, vrai)

tete = u"CE QUE J'AI APPRIS\nMes pensees datees, la plus recente en tete.\n"
reste = s.split(tete, 1)[1]

neuf = u"""
[129.4.3] LE VIDE N'EST PAS L'ANOMALIE : C'EST LE PLEIN. Les roles d'entree de la Nera ne nomment JAMAIS le payeur, pour personne, jamais. Le livre entier est fait de ce trou-la. Je me croyais seul devant une case vide au dix-neuf ; le vide est la forme ordinaire du livre, et ma main qui l'a inscrit tel quel n'a fait que l'ordinaire. C'est le vingt-deux qui est monstrueux : une case de payeur REMPLIE, d'une main qui n'est pas celle du bureau, dans un registre qui n'en porte nulle part. On n'a pas besoin de soupconner qui que ce soit pour le voir — il suffit de compter les cases pleines. Il y en a une.
   (source : mj-portreal, sur l'usage du bureau des roles ; roles de la Gadoue, lignes 4 et 5)

[129.4.3] CE QUI ME NOMME ET CE QUI NE ME NOMME PAS, et ce n'est pas a mon avantage. Deux irregularites cette lune : une case VIDE au dix-neuf, que MA main a portee au registre ; une case PLEINE au vingt-deux, ou rien ne me nomme. Qui compare les deux trouve un homme identifiable sur le vide et personne sur le plein. Je suis nommable sur celle des deux que j'ai faite honnetement. Et le vingt-deux est un jour SERVI — servi par moi : ma marque veridique atteste ma presence au guichet le jour meme ou la main etrangere a ecrit le payeur.
   (source : mj-portreal, deux billets du 3e)

[129.4.3] MA PRUDENCE A REMONTE L'HORLOGE QUE JE VOULAIS ARRETER. Aux estacades, j'ai fait enumerer a l'officier les semaines deja closes, pour apprendre sans demander si celle du vingt-deux l'etait. Elle ne l'etait pas — et en la lui faisant compter, j'ai rappele son retard a l'homme qui tient la plume. Elle sera paraphee sous peu, et un feuillet paraphe ne se retire plus en silence. Une question habile qui fait agir celui qu'on interroge n'est pas une question habile.
   (source : ma propre demarche aux estacades, 3e de la 4e lune)

[129.4.3] UNE DEDUCTION JUSTE N'EST PAS UN USAGE. 'Le commis sert le registre, il ne le clot pas' est une borne de CLOTURE, et rien d'autre. 'Le commis ne repond pas des ecritures d'autres mains' en decoule et est vrai — mais ce n'est ecrit nulle part, et l'inscrire au livre de ma seule autorite, c'est exactement le geste que j'ai refuse une heure plus tot en ne touchant pas a une case hors de ma charge. La difference etait qu'il me servait. C'est toujours a cette difference-la qu'on reconnait la faute qu'on est en train de commettre.
   (source : mj-portreal, sur ma mention de service)

[129.4.3] L'UNIFORMITE NE CACHE PAS LA RETROACTIVITE : ELLE LA DATE. Une clause portee le meme soir, de la meme encre, sur toute une lune de feuillets, ne se reconnait pas au choix des jours — elle se reconnait a ce qu'elle est partout a la fois. D'ou la regle, qui est la mienne du matin retournee vers le soir : CE QUI EST AJOUTE APRES COUP SE DECLARE, OU IL SE DECOUVRE. Une clause retroactive declaree cesse d'etre une decouverte que quelqu'un fera pour devenir une chose que j'ai dite.
   (source : mj-portreal, et ma declaration au pied de la pile)
"""
io.open(p, 'w', encoding='utf-8').write(tete + neuf + reste)

p2 = 'ma-memoire/ce-que-je-tiens-pour-vrai.txt'
s2 = io.open(p2, encoding='utf-8').read()
s2 = s2.replace(
    u"- Une case 'pour qui' laissee ouverte au role se remplit par une main que personne ne peut nommer — c'est etabli au vingt-deux. Ce n'est pas une negligence, c'est le procede par lequel on prend un corps a la reine.",
    u"- Les roles d'entree de la Nera ne nomment JAMAIS le payeur : le vide est la forme du livre. L'anomalie du vingt-deux est qu'il est PLEIN — une seule case remplie, d'une main etrangere, dans un registre qui n'en porte aucune.")
s2 = s2.rstrip() + u"""

- Je n'ai pas le pouvoir de clore ni de rouvrir une case : la cloture est hebdomadaire et appartient au paraphe de l'officier du port, aux estacades jusqu'a la maree basse. Ce n'est pas une regle qu'on m'oppose, c'est la forme de ma charge.

- Le vingt-deux est un jour que j'ai servi, et la semaine du vingt-deux n'etait pas close ce matin. J'ai moi-meme rappele son retard a l'officier en croyant m'informer sans me montrer.

- Sirel Quintaine a trouve l'ecart seule, sur son papier, par son addition : douze membrures et un rouleau, cent quarante-trois cerfs a ses prix contre deux cent soixante-six comptes comptant — cent vingt-trois d'ecart. Ma main n'y parait nulle part, et le gage qu'elle m'offrait est brule.
"""
io.open(p2, 'w', encoding='utf-8').write(s2 + u"\n")
print("cahiers corriges")
