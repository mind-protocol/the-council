# -*- coding: utf-8 -*-
import subprocess, sys

texte = u"""Ser Criston.

Je vous dois un chiffre depuis les cloches du vingt-neuvieme. Nous sommes au troisieme de la quatrieme lune. Je ne vous offrirai pas d'excuse : une promesse en retard de cinq jours n'en a pas, et la colonne n'est pas sortie le trentieme pour cette raison-la, que vous avez ecrite vous-meme le soir venu. Vous aviez raison de l'ecrire, et je ne l'ai pas contestee.

Voici ce que je peux vous donner aujourd'hui par ecrit, et ce que je ne vous donnerai pas par ecrit.

CE QUE JE VOUS DONNE. La forme de la chose est arretee, et elle ne bougera plus. Ce ne sera pas une prime. Ce sera une AVANCE sur la solde due a vos hommes : gagee sur la recette de la lune et non sur le coffre, versee en une fois avant le depart contre role signe, reprise par retenue de moitie sur les soldes des deux lunes suivantes. La difference n'est pas de mots. Une prime serait une charge neuve, elle sortirait du coffre et ne rentrerait jamais ; je vous l'aurais refusee et vous auriez attendu ma mort pour l'obtenir. Une avance ne coute rien de neuf a la Couronne : c'est de l'argent qu'elle doit de toute facon, sur lequel on avance la date. Vos hommes ne perdent pas un liard. Ils touchent plus tot.

Le prix de cette forme est pour vous et je vous le dis maintenant : ils s'en apercevront a la cinquieme lune, devant Sombreval, loin de moi et pres de vous. Il faut donc que ce soit VOUS qui le leur disiez, et avant le depart. Un homme a qui l'on avance sa solde et qui le sait marche ; un homme qui l'apprend en touchant demi-solde sous des murs a prendre se croit vole par la Main, et ce sont vos nuits qui s'en ressentiront, pas les miennes.

CE QUE JE NE VOUS ECRIRAI PAS. Le montant. Non par mauvaise volonte : parce que deux livres de cette maison ne s'accordent pas sur le seul nombre dont ce montant depend, et l'ecart entre eux n'est pas de quelques dragons. Je fais compter, pieces en main, devant le gardien que j'ai fait nommer le vingt-huitieme. Je signe les quatre ecritures le CINQUIEME au matin, et le montant y sera. Vous avez ma parole sur la date, et cette fois elle est courte assez pour que vous puissiez me la reclamer.

Je sais ce que vous allez penser : encore un jour, encore une raison. Alors jugez-moi la-dessus, ser : un Main en retard vous coute deux jours. Un Main qui signe un chiffre qu'il n'a pas arrete vous fait partir avec une caisse qui se vide a mi-route, et vous l'apprenez a trois jours de Port-Real avec trois mille hommes autour de vous. J'ai fait la premiere faute cinq jours durant. Je ne ferai pas la seconde.

ET UNE CHOSE QUI NE PEUT PAS S'ECRIRE. Il faut que je vous voie seul aujourd'hui, avant que l'ordre de depart de la colonne soit signe. Cela ne concerne pas Sombreval, cela ne concerne pas votre solde, et cela ne se discute pas devant un clerc. Cela concerne la porte par laquelle vous comptez sortir et ce qui reste derriere elle quand vous serez passe. Je serai a la Tour de la Main jusqu'aux vepres ; venez a l'heure qui vous arrange, et venez sans escorte. Si vous ne pouvez pas, dites-moi ou vous etes et je viendrai, comme je l'ai fait a la caserne.

Deux choses encore, courtes, qui peuvent s'ecrire.

La prime des tetes n'est pas abandonnee et je ne l'abandonnerai pas : elle n'est pas a moi, le roi l'a criee de sa bouche. Mais elle cesse d'etre une bouche ouverte sur votre caisse. Elle sera portee au livre comme un plafond et non comme une affectation, a un prix unique. On criait un prix Porte de la Gadoue et un autre au marche voisin, de un a cinq pour la meme tete. C'etait ma negligence et je la reprends.

Vous marchez a trois mille cent au plus, non a trois mille cinq cents. Les quatre cents lances de Strong sont a Harrenhal, rendues au prince Daemon le vingt-troisieme par une porte ouverte, et le role ne l'a pas encore dit. J'ai demande au Grand Mestre de le relever et j'ai demande un jour de plus ; je ne le redemanderai pas. Comptez sur le vrai nombre des maintenant : c'est celui qui se presentera devant les murs, quoi qu'un registre affirme.

— Otto Hightower, Main du Roi."""

cmd = [sys.executable, "C:/Users/reyno/le-conseil2/scripts/parloir.py",
       "--dire", "--de", "otto", "--a", "criston", texte]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout)
print((r.stderr or "")[-600:])
