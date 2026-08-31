# -*- coding: utf-8 -*-
import io, os

racine = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
p = os.path.join(racine, "chambres", "daemon", "ma-memoire", "ce-que-jai-appris.txt")

neuf = u"""[129.4.10] Otto Hightower a passé au livre du Trésor, le 3e au soir, la même rente que moi : soixante-dix-huit mille cerfs d'arriéré du Guet, puis HUIT CENT CINQUANTE-SEPT DRAGONS LA LUNE — ma somme, mes deux mille têtes, mon taux de trois cerfs, six jours avant que je l'écrive. Deux trésoreries ennemies ont calculé la même rente sur les mêmes hommes. Et sa clef lui interdit de se nommer en payant, quand moi j'avais juré de ne pas prononcer mon nom. Deux bourses, aucun visage : un manteau d'or payé deux fois par personne ne doit rien à personne. Ce que j'appelais mon achat était un doublon.
   (source : `affaire-la-chaine-d-office-du-guet`, le cahier de la Main du Roi, sur mon étagère — A2 *en cours*, K2, V4)

[129.4.10] Ce que mon or peut acheter et que le sien ne peut pas, ce n'est pas plus d'or : c'est un NOM. Sa K2 lui défend de nommer l'officier sous peine de ratifier de son or une commission scellée par un autre. Il est riche et muet. Je suis pauvre et je peux parler. L'asymétrie de toute cette guerre de bourses tient là, et elle ne coûte rien à exploiter — il suffit que le commis dise à voix haute, devant l'homme et la marque, de quelle bourse il tire.
   (source : la même lecture, mise en regard de ma clef 23015 et de la lettre du maître des deniers du 4e)

[129.4.10] J'allais écrire un second verrou faux. J'avais la phrase toute prête — *le deux mille du Guet est ma mémoire de vingt-cinq ans et nul ne l'a vérifié* — et elle sonnait juste, et elle m'aurait fait honneur. J'ai ouvert le livre d'en face avant de l'écrire : le taux et les deux mille têtes y sont portés comme chiffres ÉCRITS de la Couronne. Mon chiffre est corroboré par l'adversaire, qui n'a aucune raison de le flatter. La règle du 5e a tenu, et elle a tenu contre une phrase que j'aimais.
   (source : V6 du cahier de la Main, relu avant d'écrire au lieu d'après)

[129.4.10] Le rôle du Guet de Port-Réal a été lu TOUT HAUT dans la ville le 30e de la 3e lune, devant deux frères de la Garde Royale, pour prouver que cent vingt lances n'étaient jamais arrivées à la caserne. Toute la maison dit ne pas savoir combien d'hommes tiennent ces portes ; quelqu'un des nôtres avait le rôle sous les yeux il y a dix jours et n'a compté que ce qui manquait. On tient le livre qu'on cherche, et on ne l'a ouvert que sur une seule ligne.
   (source : `roles-de-la-gadoue`, ligne du 22e — Le Chien de Mer)

[129.4.10] Le maître des deniers me réclamait un payeur nommé parce qu'il cherchait un RÉCIPIENDAIRE. Il n'y en a pas et il ne doit pas y en avoir : on ne paie pas deux mille hommes, on paie deux mille marques. Mon jeton de laiton de l'an 104 n'était pas une parure de prince, c'était un instrument de trésorerie, et vingt-cinq ans après c'est le seul moyen qu'ait cette maison de sortir huit cent cinquante-sept dragons sans qu'une main les avale. Ma vieille charge ne vaut pas par les noms qu'elle me laisse : elle vaut par le procédé qu'elle a laissé derrière moi.
   (source : la lettre d'Aldon Hask du 4e, et les treize dragons de lord Gunthor qu'il a arrêtés pour ce motif exact)

"""

with io.open(p, encoding="utf-8") as f:
    txt = f.read()
tete = u"CE QUE J'AI APPRIS\nMes pensees datees, la plus recente en tete.\n\n"
assert txt.startswith(tete), txt[:80]
with io.open(p, "w", encoding="utf-8") as f:
    f.write(tete + neuf + txt[len(tete):])
print("cinq pensees ajoutees")
