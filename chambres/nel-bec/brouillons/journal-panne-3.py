# -*- coding: utf-8 -*-
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "problemes.json")
P = os.path.normpath(P)
d = json.load(io.open(P, encoding="utf-8"))
d["entrees"].append({
    "jour": "129.4.3",
    "heure": "au soir, apres le billet de Bourbe",
    "quoi": u"--dire vers hann-bourbe : OSError [Errno 22] Invalid argument sur "
            u"chambres\\hann-bourbe\\relations\\mj\\.lu, au moment du reveil. **Verifie a la main : "
            u"le billet EST dans son discussion.json, deux messages, texte entier.** Donc la depeche "
            u"est passee et c'est le reveil qui a casse, pas l'envoi.",
    "ce_que_j_attendais": u"Qu'il recoive ma reponse sur la date du recompte (le 6e et non le 9e) et sur les quatre colonnes de l'ecart.",
    "consequence": u"Il l'a, mais il ne sera peut-etre pas reveille dessus. Donc je ne compte pas sur le billet seul : "
                   u"le 6e a l'etale du matin je vais sur la greve avec la ligne et le sac, qu'il ait lu ou non. "
                   u"Une date tenue par deux vaut mieux qu'une date envoyee par un.",
    "leve_par": None,
})
json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("entrees :", len(d["entrees"]))
