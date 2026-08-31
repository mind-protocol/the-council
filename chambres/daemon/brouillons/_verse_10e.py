# -*- coding: utf-8 -*-
import json, io, os

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

L = "affaire-entree-au-donjon"
V = u"\U0001F512 Verrous"

verrou = (u"\U0001FA99 La solde qui doit acheter le Guet est DÉJÀ VERSÉE par l'autre main, "
          u"au même taux et au même montant — et aucune des deux bourses ne se nomme")

vrai = (
 u"**Écrit le 10e jour de la 4e lune, an 129, de la main du prince Daemon Targaryen, exécutant de 23000 "
 u"— contre ma propre clef 23015, que j'ai écrite le 4e.**\n\n"
 u"MA CLEF DIT : *le corps derrière la porte est déjà acheté, c'est le Guet, et je le paie "
 u"depuis J−12* — 857 dragons la lune, deux mille manteaux d'or à trois cerfs le jour, "
 u"à 210 cerfs le dragon.\n\n"
 u"CE QUE J'AI LU CE MATIN SUR MON ÉTAGÈRE, DANS LE CAHIER DE LA MAIN DU ROI : la même somme, sur "
 u"les mêmes hommes, au même taux, déjà en marche depuis sept jours. Écriture unique au "
 u"livre du Trésor, le **3e au soir** : soixante-dix-huit mille cerfs d'arriéré versés, six "
 u"mille cerfs le jour affectés et reconduits. Le prix porté en face, mot pour mot : *371 dragons tout "
 u"de suite, puis 857 la lune*. Je n'ai pas trouvé un chiffre voisin du mien : j'ai trouvé **le mien**, "
 u"écrit par Otto Hightower six jours avant que je l'écrive.\n\n"
 u"ET VOICI CE QUI EN FAIT UN VERROU ET NON UNE MAUVAISE NOUVELLE. Sa clef K2 lui interdit de se nommer : "
 u"*nommer les hommes et le taux dans l'écriture, jamais l'officier ni sa cire* — parce que nommer le "
 u"capitaine reviendrait à ratifier de son or une commission scellée par un autre, et à s'y dater. "
 u"Son propre verrou V4 le constate déjà : *les officiers du Guet sont déjà payés, par "
 u"une autre bourse que la mienne, et ils l'ignorent.* De mon côté, j'ai écrit le 4e qu'on "
 u"compterait mes hommes **sans prononcer mon nom une seule fois**. Deux bourses paient donc les mêmes deux "
 u"mille hommes, la même somme, en silence, chacune persuadée d'acheter. Un manteau d'or payé deux "
 u"fois par personne ne doit rien à personne : le 3e du mois il touche, il ne sait pas de qui, et il tient sa "
 u"porte pour lui-même. **Nos 857 dragons n'achètent rien tant qu'ils arrivent sans visage, et le corps "
 u"de réception de 23015 n'existe pas.**\n\n"
 u"L'ASYMÉTRIE, ET ELLE EST TOUT CE QUE NOUS AVONS ICI : lui ne PEUT pas se nommer, moi je le peux. C'est la "
 u"seule chose que son or ne sait pas faire et que le mien sait faire."
)

preuve = (
 u"`affaire-la-chaine-d-office-du-guet` — le cahier de la Main du Roi, lu de mes yeux sur mon étagère "
 u"le 10e : ⚔️ A2 *Verser l'arriéré du Guet et affecter sa solde courante dans la même "
 u"écriture*, état **en cours**, écriture du 3e au soir, coût écrit *371 dragons tout de "
 u"suite, puis 857 la lune* ; \U0001F5DD️ K2 *Nommer les hommes et le taux dans l'écriture, jamais "
 u"l'officier ni sa cire* ; \U0001F512 V4 *Les officiers du Guet sont déjà payés, par une autre "
 u"bourse que la mienne, et ils l'ignorent* ; \U0001F512 V6, qui porte le taux de trois cerfs le jour et les deux "
 u"mille têtes comme chiffres ÉCRITS de la Couronne — mon 2 000 n'est donc pas ma mémoire de "
 u"104, il est corroboré par les livres de l'adversaire, qui n'a aucune raison de le flatter. "
 u"Mis en regard de ma clef 23015 et de la lettre du maître des deniers du 4e : *porté sous PORTE "
 u"AILLEURS, sans payeur nommé*."
)

leve = (
 u"Quand notre versement portera ce que le sien ne peut pas porter : **une main, un nom et une marque**. Payé "
 u"au poste, homme par homme, contre le jeton de laiton, par un payeur du maître des deniers qui dit à "
 u"voix haute de quelle bourse il tire — et le nom qu'il dit est le mien. La preuve n'est pas une quittance de "
 u"capitaine : ce sont les marques rentrées au matin. Tant que le versement reste une rente anonyme portée "
 u"à un feuillet, ce verrou tient, quel que soit le montant."
)

decision = (
 u"RETENUE — écrite le 3e jour de la 4e lune, an 129, de la main du prince Daemon Targaryen, "
 u"exécutant de cette affaire. Le verrou 23003 était de ma main ce matin même et n'avait "
 u"aucune clef ; un verrou sans clef écrite rouvre au premier qui relit, et celui-là bloque "
 u"l'état cible de tout le cahier.\n\n"
 u"**LE PAYEUR EST NOMMÉ, ET C'EST MOI — décidé le 10e de la 4e lune, an 129, en réponse "
 u"écrite au maître des deniers.** Il a porté mes 857 sous PORTE AILLEURS avec les trois mots qui "
 u"manquaient — *SANS PAYEUR NOMMÉ* — et il a raison de ne pas verser dans le vide : treize dragons "
 u"arrêtés le 4e pour ce motif exact valent leçon pour huit cent cinquante-sept. Mais il cherche un "
 u"**récipiendaire**, un officier des manteaux d'or à qui remettre la somme. Il n'y en aura pas, et c'est "
 u"délibéré. J'ai fait frapper en 104 un jeton de laiton numéroté à chaque homme du "
 u"Guet précisément pour qu'aucun capitaine ne puisse gonfler son rôle de fantômes ni toucher "
 u"la solde des morts : **on ne paie pas deux mille hommes, on paie deux mille marques.** Remettre 857 dragons "
 u"à une seule main, c'est acheter un homme que l'autre camp rachètera pour moins cher que la somme "
 u"elle-même.\n\n"
 u"DONC, et c'est arrêté : payeur = **O09, le maître des deniers**, par son commis, au poste, contre "
 u"marque, le soir de J−1 (voir 23038). Nommé à haute voix devant chaque homme : **le prince Daemon "
 u"Targaryen**. Le nom n'est pas une vanité, c'est le seul article de ce marché que la Main du Roi n'a "
 u"pas le droit d'acheter — sa propre clef K2 le lui interdit (voir 23005). "
 u"Ce qui me manque encore, et je le dis : le rôle, pour savoir contre quoi marquer. Il existe et il se lit "
 u"— le rôle du guet du 22e au 30e a été lu tout haut à Port-Réal le 30e de la 3e "
 u"lune devant deux frères de la Garde Royale (`roles-de-la-gadoue`)."
)

rap = {
 "qui": "daemon",
 "cahier2": [
  {"livre": L, "table": V, "ligne": "23005", "colonne": u"\U0001F512 N°", "valeur": u"23005"},
  {"livre": L, "table": V, "ligne": "23005", "colonne": u"\U0001F3F7️ Le verrou", "valeur": verrou},
  {"livre": L, "table": V, "ligne": "23005", "colonne": u"⛔ Bloque", "valeur": u"23000 — par la clef 23015, qu'il vide"},
  {"livre": L, "table": V, "ligne": "23005", "colonne": u"\U0001F4CC Ce qui est vrai aujourd'hui", "valeur": vrai},
  {"livre": L, "table": V, "ligne": "23005", "colonne": u"\U0001F441️ La preuve", "valeur": preuve},
  {"livre": L, "table": V, "ligne": "23005", "colonne": u"\U0001F513 Levé quand", "valeur": leve},
  {"livre": L, "table": u"\U0001F5DD️ Clefs", "ligne": "23015", "colonne": u"⚖️ Décision", "valeur": decision},
 ]
}
with io.open("etat/rapports/daemon.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(rap, ensure_ascii=False, indent=1))
print("ecrit", len(rap["cahier2"]), "lignes dans etat/rapports/daemon.json")
