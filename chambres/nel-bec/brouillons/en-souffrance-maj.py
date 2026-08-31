# -*- coding: utf-8 -*-
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "en-souffrance.json")
P = os.path.normpath(P)
d = json.load(io.open(P, encoding="utf-8"))

# Les deux fils ouverts vers Marlo sont fermes : elle a tout accorde le meme soir.
d["ferme"].append({
    "qui": "marlo-vasse",
    "quoi": u"Que ses deux tetes de la barriere passent par ma main, au prix de mes six et du meme sac (clef 69016).",
    "ferme_le": "129.4.3",
    "comment": u"Accorde de sa main le soir meme : « Et je ne les paie pas. Loue-les par ta main, meme prix, MEME SAC. » La clef 69016 est tranchee, l'action 69026 n'est plus livree sous une decision en l'air.",
})
d["ferme"].append({
    "qui": "marlo-vasse",
    "quoi": u"La borne de mer du partage : laisse de vive-eau, et un piquet avant le 7e.",
    "ferme_le": "129.4.3",
    "comment": u"Accorde : « DE LA BORNE DU CORDIER A LA LAISSE DE VIVE-EAU », piquet avant le 7e, sur les deux exemplaires. Reste une chose que je lui ai renvoyee le soir meme : on ne voit pas une laisse de vive-eau un jour de morte-eau — ca se lit au sol, pas a l'eau.",
})
d["j_attends"] = [
    {
        "de_qui": "marlo-vasse",
        "demande_le": "129.4.3",
        "quoi": u"Qu'elle RECOMPTE ma ligne du sac au sixieme jour, tete par tete, le recompte ecrit de la main de celui qui recompte — au lieu de la croire sans verifier. Elle a offert le contraire ; je le refuse. Verrou 69007, clef 69018.",
        "relance_le": "129.4.9",
        "ferme_si": u"Si elle refuse de recompter, je tiens la ligne quand meme et je fais recompter par une tete qui n'est pas des six — mais alors le verrou reste ecrit, entier, et je le lui redis a chaque paie.",
    },
    {
        "de_qui": "marlo-vasse",
        "demande_le": "129.4.3",
        "quoi": u"Le prix dit avant de mon nom sur la provenance de la colonne : qu'on me fasse dire avant la fin du jour si l'on demande apres NEL BEC par son nom quelque part, comme je le fais pour elle.",
        "relance_le": "129.4.6",
        "ferme_si": u"Pas de mot le 6e a La Gaffe : je le redemande une fois de vive voix, puis je cesse de le demander et je m'arrange autrement.",
    },
]
d["on_attend_de_moi"].append({
    "qui": "marlo-vasse",
    "quoi": u"Planter le piquet de la laisse de vive-eau avec elle avant le 7e — a deux, et lu au SOL (fin du goemon, durcissement de la vase, changement des coquillages), non a l'eau : il n'y a pas de vive-eau avant le 15e. Et faire ecrire dans l'acte, avant signature : si l'eau du 15e descend sous le piquet, le piquet suit l'eau.",
    "du_le": "avant le 129.4.7",
    "etat": u"promis le 3e — j'y vais moi-meme, je n'envoie personne",
})
json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("j_attends", len(d["j_attends"]), "| on_attend", len(d["on_attend_de_moi"]), "| ferme", len(d["ferme"]))
