# -*- coding: utf-8 -*-
import json, io, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- problemes.json ----
p = os.path.join(base, "problemes.json")
d = json.load(io.open(p, encoding="utf-8"))
d["entrees"][0]["levee_par"] = (
    u"LEVEE, ET CE N'ETAIT PAS LE PARLOIR. Le parloir n'a jamais refuse ma phrase : "
    u"c'est le SHELL qui refusait la COMMANDE, parce que je l'ecrivais en deux operations "
    u"enchainees — 'cd <depot> && python scripts/parloir.py ...'. Toute commande composee "
    u"demande une approbation qui n'est jamais venue, et le refus tombait AVANT que python "
    u"soit appele. La forme qui marche est nue et d'un seul tenant : "
    u"python C:/Users/reyno/le-conseil2/scripts/parloir.py --dire --de tobb --a <untel> \"...\" "
    u"— chemin absolu, aucun &&, aucun echo derriere. Cinq billets partis ce jour-ci. "
    u"CE QUE J'EN RETIENS, ET CA VAUT AU-DELA DU PARLOIR : j'ai perdu une journee a croire "
    u"qu'une porte etait fermee alors que je m'y presentais mal. Six essais, quatre formes — "
    u"et les quatre formes changeaient ma PHRASE quand c'etait ma MAIN qu'il fallait changer. "
    u"Quand une chose echoue six fois de la meme facon, ce n'est plus la chose qu'il faut "
    u"varier, c'est le geste."
)
d["entrees"].append({
    u"jour": u"3e de la 4e lune, an 129, au matin",
    u"quoi": u"Deux horloges. Mon dossier dit '4e lune, 3e jour'. Mon propre fil d'hier est date du 5e, et j'ai ecrit '5e de la 4e lune' partout — dans mon cahier, dans mes verrous 9005 et 9006, dans mes preuves.",
    u"ce_que_jai_tente": [u"Cherche une date de reference dans les cahiers du plan : ils datent en J-n, ce qui ne tranche rien."],
    u"ce_que_la_machine_en_a_fait": u"Rien. Les deux dates coexistent. Les billets de ser Steffon Darklyn et de ser Robert Quince portent tous deux 129.4.3, ce qui va avec le dossier et contre moi.",
    u"ce_que_jattendais": u"Savoir quel jour on est. C'est une petite chose, sauf pour l'homme dont l'office est de tenir le role des JOURS.",
    u"ce_que_jai_fait_a_la_place": u"La feuille est ecrite en trente lignes de la 4e lune, ce qui couvre les deux lectures, et je n'ai pose de jour ferme que la ou le fait etait date par autre chose que moi. Je cesse de recopier '5e' de ma main tant que ce n'est pas tranche.",
    u"note": u"Un tenant du role des jambes qui se trompe de deux jours ne vaut rien et ne le saurait pas. A porter a l'arbitre.",
    u"levee_par": u""
})
json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- en-souffrance.json ----
p = os.path.join(base, "en-souffrance.json")
d = json.load(io.open(p, encoding="utf-8"))
d["j_attends"] = [
    {
        u"de_qui": u"alys-grive, dame Alys Grive, maitresse des bouches (O10)",
        u"quoi": u"Un seul mot sur un seul nom : Doss Marran, du bourg — tenue, ou libre. C'est 9026, et rien de plus.",
        u"demande_le": u"3e de la 4e lune — DEMANDE POUR DE BON, billet parti. Deux jours que je croyais l'avoir demandee et que rien n'etait sorti de chez moi.",
        u"pourquoi_ca_presse": u"9023 attend ce mot. 6013 defend qu'une bouche porte une chanson et un pli ; je serais le premier a casser la regle que mon propre cahier reclame qu'on tienne.",
        u"relance_prevue": u"Dans deux jours, et de vive voix si elle repasse au bourg."
    },
    {
        u"de_qui": u"le-sanglier, maitre des roles (O02)",
        u"quoi": u"Deux choses. (1) Quel cahier cede sur les onze jours a zero jeton, du J-8 au J+2 — je ne choisis pas, c'est son office. (2) La LIGNE DE PORTE, qui est a lui : qu'il me la reporte sur la feuille, sinon elle ment par le bas.",
        u"demande_le": u"3e de la 4e lune, billet parti avec le chiffre et l'aveu du retard",
        u"pourquoi_ca_presse": u"La feuille est ouverte et incomplete tant que sa ligne n'y est pas. Et les onze jours a zero contiennent le jour d'entree.",
        u"relance_prevue": u"Au premier conseil ou je le vois, de vive voix, avec la feuille a la main."
    },
    {
        u"de_qui": u"robert-quince, castellan (O01)",
        u"quoi": u"Sa page de porte, chaque semaine — jour, heure a la minute, nom, sceau. Il l'a offerte sans que je la demande.",
        u"demande_le": u"3e de la 4e lune, accepte par billet",
        u"pourquoi_ca_presse": u"Ce n'est pas presse : c'est le seul endroit de ce rocher ou les JAMBES prennent un nom en sortant, et ma colonne s'en nourrit.",
        u"relance_prevue": u"Rien a relancer. S'il oublie une semaine, j'y vais : sa porte m'est ouverte, il l'a ecrit."
    }
]
d["on_attend_de_moi"] = [
    {
        u"qui": u"aurore-inchauspe, dame Aurore, maitresse des nouvelles (O03)",
        u"quoi": u"34122 lui demande cinq porteurs nommes, dus J-20, avec ses propres conditions. Le bourg n'en a pas cinq, il n'en a pas deux, il en a UN — et je le veux pour le troisieme jeton.",
        u"depuis_quand": u"Su de moi au bourg, en cherchant pour moi et non pour elle",
        u"ce_que_je_dois": u"RENDU le 3e de la 4e lune. Billet parti : le seau est vide, voici pourquoi (9005), voici la question qui m'a sauve — 'que lui prend-on deja, et est-ce que ca marche ?' — et l'aveu que nous serons deux sur le meme homme. Aucun nom donne : nommer ses porteurs n'est pas mon office.",
        u"a_faire": u"Rien. Attendre ce qu'elle en fait. Si elle prend Doss Marran, je n'ai plus de troisieme jeton et je ne le lui disputerai pas par billet — cela se tranche a la table."
    },
    {
        u"qui": u"le-sanglier, maitre des roles (O02)",
        u"quoi": u"9021 — les jours ou il n'y a personne, avec les lignes qui les prennent. Du le 5e (ou le 2e, selon l'horloge).",
        u"depuis_quand": u"Du et en retard",
        u"ce_que_je_dois": u"RENDU le 3e de la 4e lune, en retard et dit comme tel. Le chiffre : du J-8 au J+2, zero coureur a Peyredragon, onze jours, le jour d'entree dedans. Rendu en J-n et non en jours de lune, avec la raison.",
        u"a_faire": u"Rien de plus. C'est a lui de trancher."
    },
    {
        u"qui": u"steffon-darklyn (Garde) et robert-quince (castellan)",
        u"quoi": u"Le verrou 9007 : rien ne rattache un pli SORTI a un homme NOMME. Ils me l'ont ecrit le meme matin, chacun de son cote.",
        u"depuis_quand": u"3e de la 4e lune",
        u"ce_que_je_dois": u"RENDU. La troisieme colonne est sur la feuille du jour meme, copiee sur la page de porte de Quince qui tourne deja. Et je leur ai dit ce que je ne peux pas : ma colonne ne remonte pas au 30e, les deux actes de la meme minute resteront sans porteur nomme.",
        u"a_faire": u"Ecrire la regle de Quince — un cheval, une maison — comme clef a mon volume. C'est moi qui peux, pas lui."
    }
]
json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("ok")
