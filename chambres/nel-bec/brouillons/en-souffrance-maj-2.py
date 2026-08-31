# -*- coding: utf-8 -*-
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "en-souffrance.json")
P = os.path.normpath(P)
d = json.load(io.open(P, encoding="utf-8"))

d["ferme"].append({
    "qui": "marlo-vasse",
    "quoi": u"Qu'elle recompte ma ligne du sac au lieu de la croire sans verifier.",
    "ferme_le": "129.4.3",
    "comment": u"Accorde le soir meme, et mieux que demande : elle retire sa phrase et nomme HANN BOURBE, trente ans de vase, pour recompter tete par tete, le recompte ecrit sur ma ligne de sa main. Premier recompte le 9e. Je l'accepte et je le lui dirai en portant la premiere ligne demain soir.",
})
d["ferme"].append({
    "qui": "marlo-vasse",
    "quoi": u"Le prix dit avant, de mon nom sur la provenance de la colonne.",
    "ferme_le": "129.4.3",
    "comment": u"Accorde et ECRIT DANS L'ACTE : le jour ou l'on demandera apres NEL BEC par son nom quelque part, je le saurai avant la fin du jour, par le premier de ses hommes qui pourra courir. On ne m'avait jamais rien ecrit dans un acte.",
})
d["j_attends"] = []
d["on_attend_de_moi"].append({
    "qui": "hann-bourbe",
    "quoi": u"Me presenter au recompte du 9e avec la ligne, les six ficelles et le sac — et chaque chiffre portant l'heure du releve, sa regle a lui que j'ai prise. Je lui ai ecrit le 3e au soir pour qu'il ne l'apprenne pas d'elle.",
    "du_le": "129.4.9",
    "etat": u"annonce le 3e — sa reponse n'est pas encore venue",
})
json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("j_attends", len(d["j_attends"]), "| on_attend", len(d["on_attend_de_moi"]), "| ferme", len(d["ferme"]))
