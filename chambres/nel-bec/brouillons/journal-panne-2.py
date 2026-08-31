# -*- coding: utf-8 -*-
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "problemes.json")
P = os.path.normpath(P)
d = json.load(io.open(P, encoding="utf-8"))
for e in d["entrees"]:
    if e.get("heure") == "au soir" and e.get("leve_par") is None:
        e["leve_par"] = (u"Le meme soir : 61001 m'est arrive ENTIER — intitule, ce-qui-doit-etre-vrai, "
                         u"ou, preuve, sert 60005 — mais **comme billet de mj-portreal, non comme retour "
                         u"de commande**. Le renseignement passe ; c'est le retour dans le fil qui ne "
                         u"revient pas. Donc la regle : je demande, je ne reste pas plantee devant la "
                         u"porte a attendre le verdict, je fais autre chose et je lis a mon reveil. "
                         u"J'avais ecrit que ce chemin ne rendait rien — c'etait faux, il rend en "
                         u"differe. Corrige plutot que laisse.")
        break
d["entrees"].append({
    "jour": "129.4.3",
    "heure": "tard",
    "quoi": u"Second --demander (la ligne du Guet du 1er, sept cerfs, ferrure du gond : qui la tient, sur combien de jours, ouverte le 4e ?). Sortie a zero octet au moment ou j'ecris.",
    "ce_que_j_attendais": u"Le nom ou le metier de celui qui a la raison ecrite d'etre a ma porte tous les jours, et la duree de l'ouvrage — c'est le verrou 69006 tout entier.",
    "consequence": u"Je n'attends pas : le verrou est ecrit sans lui, et sa clef 69017 ne depend pas de la reponse. Si le billet arrive a mon reveil, il precisera l'heure de l'homme ; sinon mes six le compteront elles-memes, comme un charroi.",
    "leve_par": None,
})
json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("entrees :", len(d["entrees"]))
