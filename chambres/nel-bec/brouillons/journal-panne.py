# -*- coding: utf-8 -*-
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "problemes.json")
P = os.path.normpath(P)
d = json.load(io.open(P, encoding="utf-8"))
d["entrees"].append({
    "jour": "129.4.3",
    "heure": "au soir",
    "quoi": u"--demander vers mj-portreal : sept minutes, puis rien du tout. Le fichier de sortie est reste a zero octet — aucun verdict, aucune erreur ecrite. Troisieme fois du meme jour que le parloir ne rend rien vers cet arbitre (deux --tenter a midi, un --demander au soir). Le --dire vers marlo-vasse, lui, est parti du premier coup : ce n'est pas le parloir qui est casse, c'est ce chemin-la.",
    "ce_que_j_attendais": u"L'intitule de l'etat cible 61001 dans INSPECTER, ce qui doit y etre vrai, sa preuve. Mes 69000 et 69100 declarent le servir ; le trou du plan dit que la remontee ne va nulle part, et INSPECTER n'est pas sur mon etagere.",
    "consequence": u"Le trou reste ouvert un jour de plus. RECIDIVE : trois sur trois. Je n'y depense plus d'heures. Le meme renseignement a une bouche : Marlo Vasse tient INSPECTER, c'est elle qui m'a donne le mandat le 2e. Je le lui demande le 6e a La Gaffe, ou par billet si le 5e passe sans elle.",
    "leve_par": None,
})
json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("entrees :", len(d["entrees"]))
