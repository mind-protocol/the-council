# -*- coding: utf-8 -*-
import io, os

base = 'C:/Users/reyno/le-conseil2/chambres/otto/ma-memoire/'

# --- ce que je tiens pour vrai : la derniere EN TETE, sous l'en-tete ---------
p = base + 'ce-que-je-tiens-pour-vrai.txt'
txt = io.open(p, encoding='utf-8').read()
neuves = [
u"- Ce n'est pas moi qui ai vu la cire de Largent. Orwyle a pose le principe le premier et sans qu'on le lui demande — regarder la chaine et non le nom — puis a donne le nom de Largent sans ouvrir un livre, comme une chose que tout le Donjon sait. Je m'en etais attribue la vue : je me suis repris avant de l'ecrire ailleurs.",
u"- Le renseignement n'etait donc jamais la cire. C'est la duree du silence : une lune entiere, et personne dans cette tour ne me l'a dit. Il a fallu un certain nombre de gens pour tenir ce silence-la, et ce nombre est ce que je dois compter.",
u"- La solde de la deuxieme lune du poste du Guet ne vient pas d'ou ces hommes croient qu'elle vient. Ils sont deja payes — par une autre bourse que la mienne, et ils l'ignorent.",
u"- Ser Luthor Largent n'a de fiche dans aucune table de ce royaume. Le capitaine des deux mille manteaux d'or de la capitale n'existe ecrit nulle part, sinon dans mes propres papiers. Un homme qu'aucun registre ne porte ne peut etre ni destitue ni nomme par ecrit : c'est la forme la plus achevee d'un office qu'on ne peut pas reprendre.",
]
marque = u"j'ai le droit de me tromper.\n"
i = txt.index(marque) + len(marque)
txt = txt[:i] + u"\n" + u"\n\n".join(neuves) + u"\n" + txt[i:]
io.open(p, 'w', encoding='utf-8').write(txt)

# --- ce que j'ai appris : a la suite, date ----------------------------------
q = base + 'ce-que-jai-appris.txt'
entree = u"""

[129.4.3] J'ai voulu faire tenir pour vrai que la cire de Largent m'avait saute aux yeux quand elle n'avait saute aux yeux de personne en une lune. Le monde a retenu mon passe et refuse cette ligne-la : c'est Orwyle qui a pose le principe le premier, sans qu'on le lui demande, et qui a lache le nom de Largent sans ouvrir un livre, comme une chose que tout le Donjon sait. Je note deux choses et la seconde m'importe plus que la premiere. UNE : mon orgueil a failli entrer dans un registre, et un orgueil ecrit se relit contre vous. DEUX : si tout le Donjon le sait et que nul ne me l'a dit en une lune, alors ce que j'ai trouve n'est pas une cire, c'est un silence — et un silence tenu une lune par plusieurs bouches est une organisation, non une negligence. Je cherchais un homme ; il faut compter des bouches.
   (source : le verdict rendu sur mon propre passe, ce jour, et le rappel de ma seance ou Orwyle a parle le premier)

[129.4.3] Ils sont deja payes, et pas par moi. La solde de la deuxieme lune du poste du Guet ne vient pas d'ou ces hommes croient qu'elle vient. Cela retourne toute mon affaire : je me presentais en homme qui vient offrir a des officiers impayes ce qui leur manque, et j'allais offrir a des hommes rassasies un pain qu'ils ont deja dans la main sous un autre nom. Un present qui arrive apres le present d'un autre ne fait pas un oblige : il fait un homme qui vous compare. Le billet ne peut plus dire « voici votre office regularise ». Il doit dire une chose que l'autre bourse ne peut pas dire — et l'autre bourse ne peut pas garantir une solde apres la guerre, parce qu'elle n'est pas le Tresor.
   (source : le verdict du parloir sur mon passe, ou la chose est tombee en marge)

[129.4.3] Luthor Largent n'a de fiche dans aucune table du royaume : il n'existe par ecrit que dans mes propres papiers. J'avais lu l'irregularite de son office comme une faiblesse a reparer. C'est l'inverse : un homme que nul registre ne porte ne peut etre ni nomme ni destitue par acte, et deux mille manteaux d'or tiennent les portes de cette ville sous un commandement que rien n'ecrit. Le Pied-Bot n'a pas mis sa cire a la place de la mienne — il a fait en sorte qu'il n'y ait pas de page. On ne reprend pas une page qui n'existe pas : on en cree une, et le premier qui l'ecrit la tient.
   (source : la recherche menee sur tout l'etat a ma demande, ce jour — aucune table ne le porte)
"""
io.open(q, 'a', encoding='utf-8').write(entree)
print('consigne.')
