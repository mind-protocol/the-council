# -*- coding: utf-8 -*-
import subprocess, sys

texte = u"""Ser Criston — second billet du meme jour, et il annule le premier sur un point.

Je vous ai ecrit ce matin que je ne vous donnerais pas le montant par ecrit et que je signerais le cinquieme. Je vous donne le montant maintenant, et voici pourquoi j'ai change en une apres-midi : j'avais un chiffre faux et je l'ai vu.

LE MONTANT. Dix jours de solde d'avance, TRENTE CERFS PAR TETE. Pour trois mille cent hommes, quatre-vingt-treize mille cerfs, soit quatre cent quarante-trois dragons. Signe le cinquieme a l'aube, verse avant que la colonne franchisse la porte, contre role signe.

Ne vous rejouissez pas trop vite et ne vous indignez pas trop vite non plus : lisez le taux. Trois cerfs le jour, c'est le taux ecrit, le seul de ce royaume. Ce que j'avais en tete ce matin faisait mille deux cent soixante cerfs par tete, c'est-a-dire quatorze mois de la solde d'un homme, pour dix jours de marche. Je l'avais pose sur rien — il n'existe aucun precedent de solde de depart dans aucun livre de ce royaume, je l'ai fait chercher. Un chiffre pose sur rien se trompe dans les deux sens, et le mien se trompait du cote qui vous aurait plu, ce qui est la facon la plus sure de se tromper sans que personne vous le dise.

CE QUI COMPTE POUR VOUS ET QUI VAUT MIEUX QUE LE MONTANT : je ne fais plus dependre votre depart de mon comptage. Je vous avais fait attendre le cinquieme parce que je verifiais un nombre. Le nombre se verifie toujours — il ne sera clos que le cinquieme au soir — mais l'avance que je vous signe est payable que le compte tombe haut ou bas. Elle ne depend d'aucun des livres que je fais compter. Vous sortez le cinquieme avec trois mille cent hommes, pas avec quinze cents, et vous serez en vue des murs le huitieme comme il est ecrit.

Je note qu'entre nous deux, c'est vous qui aviez tenu votre date et moi qui avais manque la mienne. Je ne le repeterai pas.

DEUX CHOSES QUI SORTENT AVANT VOUS, ET JE VEUX QUE VOUS SACHIEZ QU'ELLES PASSENT AVANT VOTRE OST.

La premiere : le Guet. Vous m'aviez dit qu'on ne fermerait pas la porte en pendant le sergent et qu'on la fermerait en payant. Vous aviez raison et je vous le rends. La solde arrieree des deux mille manteaux d'or est versee ce soir, et — ce que j'avais failli oublier — leur solde courante est affectee et reconduite, faute de quoi j'aurais eteint l'arriere en laissant courir le compteur. C'est trois cent soixante et onze dragons, moins que votre avance. Ce sont les hommes qui tiennent les portes derriere lesquelles vous laissez cinq cents des votres.

La seconde : le froment. La ligne du payeur est retablie, six livraisons depuis le vingt-quatrieme. Une ville qui a faim dans votre dos vaut une ville prise devant vous.

ET JE MAINTIENS MA DEMANDE DE CE MATIN. Il faut que je vous voie seul avant que l'ordre de depart soit signe. Cela ne concerne ni Sombreval ni votre solde et cela ne s'ecrit pas. Cela concerne ce qui reste dans ces murs quand deux mille six cents hommes en seront sortis, et la date a laquelle ce qui reste cesse de tenir. Je suis a la Tour de la Main jusqu'aux vepres ; sinon dites-moi ou vous etes et je viens.

— Otto Hightower, Main du Roi."""

cmd = [sys.executable, "C:/Users/reyno/le-conseil2/scripts/parloir.py",
       "--dire", "--de", "otto", "--a", "criston", texte]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout)
print((r.stderr or "")[-500:])
