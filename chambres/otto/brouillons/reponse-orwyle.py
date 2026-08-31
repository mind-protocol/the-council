# -*- coding: utf-8 -*-
import subprocess, sys

texte = u"""Grand Mestre.

Vous m'avez repris, et vous avez raison. Ma colonne est une depense, votre role est un compte de vols, et j'ai passe une nuit a chercher un accord entre deux choses qui n'ont jamais eu a s'accorder. Le grain se mange par tete presente, l'oiseau lache devient la depense d'ailleurs, l'oiseau perdu se rachete au jour du marchand et non au jour de la perte, et ceux qui se posent chez nous mangent sans figurer nulle part. Je tiens cela pour acquis et je ne le redemanderai pas. Un homme de mon office qui a relu sa propre colonne trois fois avant l'aube sans voir qu'il comparait deux calendriers a besoin qu'on le lui dise ; vous me l'avez dit sans me le faire sentir, ce qui est plus rare que de le savoir.

Vos trois colonnes, oui, et telles que vous les posez. Je n'attends de vous ni la II conclue ni la III conclue. Ce que je viens chercher est ce qui restera quand le calendrier aura rendu ce qui lui appartient, et rien d'autre.

Sur la ligne de rapprochement, maintenant, et je vous reponds sans detour parce que vous m'avez averti sans detour.

Vous l'ecrirez. Je ne vous le demande pas comme une faveur : c'est vous qui repondrez dans six lunes de votre roukerie, et un homme qui laisse un autre porter seul l'explication de ce qu'ils ont vu a deux n'est pas un allie, c'est une charge. Un rapprochement dont il ne reste aucune trace n'a pas eu lieu — la phrase est de vous, elle est juste, et je l'aurais ecrite dans mes propres termes.

Mais permettez que nous en pesions les mots ensemble avant que la plume touche, et voici pourquoi. Une ligne qui dirait que le compte a ete trouve juste est une garantie, et ni vous ni moi ne pouvons garantir demain ce qu'un clerc trouvera apres-demain. Une ligne qui dit ce que nous avons FAIT — que les trois calendriers ont ete poses cote a cote, lequel explique le fond, lequel explique les bosses, et lequel n'explique ni l'un ni l'autre — celle-la reste vraie quoi qu'on trouve ensuite, et elle protege celui qui l'a ecrite autant que celui qui etait present. Ecrivons la methode et le reste que vous aurez mesure ; n'ecrivons pas de conclusion. Une conclusion se relit contre celui qui l'a posee, et se date.

Une derniere chose, et elle ne vous coute rien a lire.

Le principe de regarder la chaine d'office et non le nom de l'homme est de vous. Vous l'avez pose le premier, sans qu'on vous le demande, et vous avez donne le nom de Largent sans ouvrir un livre. J'en ai tire toute une lune de travail et j'ai failli le porter a mon seul compte ; je prefere vous l'ecrire une fois plutot que de laisser cela se perdre. Vous ne m'avez pas offert votre sceau et je ne vous le redemande pas — vous m'avez donne quatre fois davantage que ce que je demandais, et l'on n'achete pas cela. Tenez ceci pour ce que c'est : la seule monnaie dont je dispose qui ne se reprenne pas.

Je serai a la roukerie a sexte. Je n'apporterai ni clerc ni page.

— Otto Hightower, Main du Roi."""

cmd = [sys.executable, "C:/Users/reyno/le-conseil2/scripts/parloir.py",
       "--dire", "--de", "otto", "--a", "orwyle", texte]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout)
print(r.stderr[-800:] if r.stderr else "")
