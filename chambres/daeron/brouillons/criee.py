# -*- coding: utf-8 -*-
import json
p = 'books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))

texte = """Écrit de ma main le 12e de la 5e lune, pour être crié le 13e sur les places et aux septuaires, et une seconde fois le 21e. Ce qu'on entend une fois, personne ne l'a entendu.

CE QUE LE CRIEUR DIT, ET RIEN DE PLUS. Il ne commente pas, il ne rassure pas, il ne nomme aucun ennemi. Vingt mots qu'une femme portant un enfant sur la hanche retient du premier coup :

  « QUAND LA CLOCHE DE MER SONNERA [—], C'EST LE CIEL.
    SOUS LA PIERRE. PAS DANS LA RUE. PAS AUX QUAIS.
    LAISSEZ LE FEU AUX HOMMES DU GUET. »

CE QUE CHAQUE LIGNE VEUT DIRE, pour le crieur qui devra répondre aux questions, et il y en aura :

SOUS LA PIERRE. Une cave voûtée, une église de pierre, un mur épais. Non un grenier, non une soupente, non sous le chaume, non sous une charpente de bois. Ce qui brûle en premier est ce qui couvre les gens, non les gens.

PAS DANS LA RUE. Une rue pleine ne peut plus être traversée, ni par un seau, ni par un blessé, ni par un homme qui court prévenir. Dix mille personnes debout entre deux murs sont dix mille personnes qu'on ne peut plus secourir. C'est le danger que je crains le plus, et il n'est pas causé par le feu : il est causé par la cloche.

PAS AUX QUAIS. On y va pour voir. C'est la découverte à ciel ouvert, sur l'eau, avec du bois goudronné partout. Personne ne va regarder.

LAISSEZ LE FEU AUX HOMMES DU GUET. Un habitant qui monte sur son toit avec un seau meurt sur son toit. Le guet a la charge et il l'a de moi.

CE QUI MANQUE, ET JE NE LE COMBLE PAS. Le premier mot du cri porte un blanc : [—], le coup de cloche lui-même. Je ne l'ai pas écrit, et je refuse de l'inventer, pour une raison que je tiens pour la plus sérieuse de tout ce papier.

Cette cloche a déjà sonné, avant moi, pour d'autres choses — un feu, une marée, une mort, un office, je l'ignore. Si je choisis un coup qui veut déjà dire autre chose dans la tête des gens, je n'ajoute pas un signal : j'en efface un, et la ville entendra deux ordres contraires le jour où il ne faudra se tromper sur aucun. On ne peut pas apprendre un mot neuf à dix mille personnes en écrasant un mot qu'elles savent.

Il me faut donc d'abord CE QUE CETTE CLOCHE A DÉJÀ SONNÉ. Demandé à mestre Norren le 12e, sans réponse à cette heure. S'il n'a rien d'écrit, je monterai le demander aux hommes qui la sonnent, et je le tiendrai de leur bouche avant de rien fixer.

Tant que ce blanc n'est pas rempli, on crie les trois lignes du dessous — sous la pierre, pas dans la rue, pas aux quais — qui sont vraies quel que soit le coup, et on ne crie pas le coup. Une ville qui sait quoi faire mais pas encore à quel signal vaut infiniment mieux qu'une ville à qui l'on a donné un signal qui en efface un autre.

ET DANS CET ORDRE, JAMAIS L'INVERSE. La criée d'abord, l'essai de nuit ensuite. Un essai avant la criée n'est pas un essai : c'est une émeute qu'on aura provoquée soi-même pour se mesurer."""

d['pages'].append({"titre": "La criée de la cloche de mer — ce qu'on dira aux gens", "texte": texte})
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('pages :', [pg['titre'] for pg in d['pages']])
