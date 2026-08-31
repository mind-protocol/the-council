# -*- coding: utf-8 -*-
import json, io, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

p = 'en-souffrance.json'
d = json.load(io.open(p, encoding='utf-8'))
d['j_attends'] = [
    {
        "qui": "steffon-darklyn",
        "depuis": "129.4.4",
        "quoi": "DE QUI JE DOIS PRENDRE LA SIGNATURE. Mon maitre est mort le 3e, aucune succession n'est ecrite nulle part, et ma regle de vingt ans n'a plus de nom au bout. Je ne lui demande pas d'etre lord : je lui demande de qui LUI dit qu'il repond de Sombreval, et sous quel titre, pour l'ecrire a mon registre a son nom et a sa date. Si personne ne peut repondre, qu'il me le dise : j'ecrirai que je l'ai demande et qu'on n'a pas pu me repondre, et c'est encore une ligne vraie.",
        "relance": "le 7e. Il est a trois cents lieues, la mer est fermee, aucune coque ne flotte devant Sombreval : je ne compte pas de reponse avant longtemps, mais la ligne reste ouverte et je ne la fermerai pas de moi-meme.",
        "etat": "ouvert",
    },
    {
        "qui": "willam-wode",
        "depuis": "129.4.4",
        "quoi": "Il a signe mon recu pour le premier pli : son nom, la date, et le titre mot pour mot, par ordre scelle de ser Criston Cole, Lord Commandant de la Garde Royale, pour la place de Sombreval. Il ne s'est dit ni chatelain ni gouverneur. CE QUE J'ATTENDS ENCORE DE LUI : la meme signature pour le pain de la ville. Tant que personne ne signe le pain quotidien, il sort de mes granges sans ordre, et c'est moi seul qui en reponds.",
        "relance": "demain le 5e, aux granges, et non au chateau. C'est un homme qui fait ecrire tout ce qu'il execute et qui craint le blame plus que la peine : a celui-la on peut demander une signature.",
        "etat": "ouvert",
    },
]
d['on_attend_de_moi'] = [
    {
        "qui": "la ville, et personne en particulier",
        "depuis": "129.4.4",
        "quoi": "UN ROLE DES BOUCHES RECOMPTE. Le mien est du 27e au soir, d'avant le sac : je n'ai compte ni les morts ni les fuis. Mes cinquante et une journees de pain ont un numerateur compte au boisseau ce jour et un denominateur vieux de six jours et d'un sac. Le quotient d'un compte vrai par un compte vieux n'est pas a moitie vrai : il est faux, et il porte ma signature.",
        "du": "le 5e, aux ecuelles servies et non au role.",
        "etat": "ouvert",
    },
]
json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

p = 'problemes.json'
d = json.load(io.open(p, encoding='utf-8'))
d['entrees'].append({
    "date": "129.4.4 (31.8.2026)",
    "quoi": "CINQ depeches ecrasees dans la journee : le worker leve RuntimeError, claude a quitte avec le code 1, fichier de depeche a zero octet, aucun verdict rendu.",
    "tente": "Le recompte des granges, deux fois, puis d'autres gestes du jour.",
    "ce_que_la_machine_en_a_fait": "Rien. Log de 887 octets portant la trace, ou zero octet. Le meme geste relance mot pour mot est passe du premier coup et a rendu un verdict complet, au muid pres.",
    "ce_que_j_attendais": "Un verdict, ou le mot que les registres se taisent.",
    "consequence_pour_moi": "Aucune cette fois, parce que j'ai relance. Je l'ecris pour la RECIDIVE : deuxieme journee de suite, et hier cela m'avait coute d'ecrire a un homme sans les dates de mes propres recus. MA REGLE DESORMAIS : une depeche revenue vide se relance UNE fois, telle quelle, avant qu'on en conclue quoi que ce soit. Un silence n'est pas une reponse et ce n'est pas un refus.",
    "etat": "ouvert",
})
json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("journaux ecrits")
