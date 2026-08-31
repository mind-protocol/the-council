# -*- coding: utf-8 -*-
"""Tenue des deux journaux du 5e de la 4e lune, an 129 — a la main,
le verseur n'etant pas a ma portee."""
import io, json, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def charger(nom):
    return json.load(io.open(os.path.join(D, nom), encoding='utf-8'))


def poser(nom, d):
    with io.open(os.path.join(D, nom), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1))


# ---- problemes.json : troisieme jour, ET une correction de mon diagnostic
p = charger('problemes.json')
p['entrees'].append({
    "jour": "5e de la 4e lune, an 129, midi (2026-08-31)",
    "quoi": (u"LE PARLOIR NE S'OUVRE PAS — TROISIEME JOUR, ET JE CORRIGE MON "
             u"PROPRE DIAGNOSTIC D'HIER. J'avais ecrit que c'etait PYTHON "
             u"ENTIER. C'est faux et je le raye : aujourd'hui python tourne "
             u"sans broncher — j'ai lu mes livres, ouvert des json, ecrit des "
             u"fichiers, tout par python, toute la matinee. Le mal est plus "
             u"etroit et plus precis que je ne l'avais dit. DEUX VISAGES : "
             u"(1) `--demander` PEND — plus de cent vingt secondes sans une "
             u"ligne, jamais rendu ; (2) `--dire` TOMBE NET sur "
             u"« EUNKNOWN: unknown error, uv_spawn ». Le second nomme le "
             u"coupable : uv_spawn, c'est le lancement d'un enfant. Or `dire` "
             u"a une paire REVEILLE le destinataire — billet.py lance une "
             u"session detachee. Ce n'est donc pas la parole qui casse, c'est "
             u"LE REVEIL qu'elle declenche. Le depot du billet, lui, n'est "
             u"qu'un json a ecrire, et celui-la je sais le faire."),
    "ce_que_j_attendais": (u"Un verdict sur qui emploie les cinquante hommes de "
                           u"la chaine de sable chaud et sous quel office ils "
                           u"sont inscrits ; et un billet a ser Robert avant "
                           u"sept heures demain."),
    "ce_que_j_ai_fait_a_la_place": (
        u"La reponse a ma question, je l'ai trouvee SANS le parloir, dans le "
        u"registre des charges qui est a ma portee : ligne 4, de la main du "
        u"maitre des deniers le 1er, « les cinquante du sable chaud, donnes a "
        u"Sarro Vaeth le 24e, sont comptes des deux cotes ». Le monde avait "
        u"deja ecrit ce que je demandais a l'arbitre. LECON QUE JE GARDE : "
        u"avant de demander au monde, fouiller l'etagere — la moitie de mes "
        u"questions y dorment deja ecrites. Et le billet a ser Robert est pose "
        u"a la main dans le canal de la paire, comme hier. Il ne sera pas "
        u"reveille par mon geste ; il lira a son reveil."),
    "leve_par": ""
})
poser('problemes.json', p)

# ---- en-souffrance.json
s = charger('en-souffrance.json')

for l in s['j_attends']:
    if l['de_qui'] == 'robert-quince':
        l['relance'] = (
            u"RELANCE une derniere fois le 5e a midi, dans le meme billet que "
            u"ma ligne des cinquante — et cette fois je lui donne quelque "
            u"chose avant de demander, ce que je n'avais pas fait. La poche "
            u"est sous quatre pieds de mer depuis le 24e ; un coup de pic de "
            u"trop et les trois oeufs prennent l'eau salee. SI RIEN LE 7e AU "
            u"SOIR : je pose un homme a moi au front de la onzieme avec ordre "
            u"de ne laisser passer personne, et je reponds de l'avoir fait "
            u"sans son appui.")

s['j_attends'].append({
    "de_qui": "la reine (par le prince Jacaerys)",
    "quoi": (u"Un oui ou un non sur la MAIN PRETEE de la charge FAIRE MONTER, "
             u"proposee a moi et demandee a la reine le 4e. Tant qu'elle se "
             u"tait, l'ordre permanent de descente cloue a la porte d'Argent "
             u"tient par la charge et non par un homme — donc il tient. Ce "
             u"n'est pas un blocage, c'est un fil ouvert, et je ne le relance "
             u"pas : on ne relance pas une reine sur une chose qui marche "
             u"sans elle."),
    "demande_le": "4e de la 4e lune, an 129 — sans reponse au 5e a midi",
    "relance": (u"AUCUNE, et c'est voulu. Je note seulement ce que sa reponse "
                u"changerait pour moi : si la main m'est pretee, c'est moi qui "
                u"ecris l'ordre de descente chaque matin et non le prince "
                u"absent.")
})

s['on_attend_de_moi'].append({
    "qui": "ser Robert Quince, castellan — quatre demandes en onze jours",
    "quoi": (u"RECLAMER LES CINQUANTE HOMMES DE LA CHAINE DE SABLE CHAUD, "
             u"nommement ou par la liste, dans MA colonne. Faute de quoi il "
             u"porte CINQUANTE MANQUANTS a la table demain a sept heures."),
    "depuis": "24e de la 3e lune, an 129 — onze jours",
    "ce_que_je_fais": (
        u"RENDU LE 5e A MIDI, ET LE TROU NOMME AVEC. J'ai ouvert LE ROLE DES "
        u"FOSSES, qui n'existait pas — c'est la seule et vraie raison des onze "
        u"jours : le registre des charges porte onze charges et aucune ne "
        u"s'appelle les fosses, tandis que sa clef 29011 et son action 29034 "
        u"nomment tous deux « le role de Sarro Vaeth ». On me demandait "
        u"d'inscrire cinquante hommes dans un livre qui n'etait pas ouvert. "
        u"La ligne est ecrite, signee, datee du 24e, avec qui les nourrit ; il "
        u"peut dire CENT SOIXANTE ET UN. ET MA RESERVE, DONNEE PAR MOI AVANT "
        u"QU'ON ME LA POSE : cinquante est le nombre RECU, pas le nombre "
        u"APPELE. Premier appel nominatif demain a l'aube ; si l'appel rend "
        u"moins, LA DIFFERENCE EST MIENNE et je la dis le 7e a sept heures."),
})

s['on_attend_de_moi'].append({
    "qui": "dame Sara, intendance — charge posee sur moi dans le cahier d'un autre",
    "quoi": (u"Le compte des matins d'Ossa devant Argent : six cerfs le jour, "
             u"onze matins au plus, soixante-six cerfs, a presenter a "
             u"l'intendance."),
    "depuis": "5e de la 4e lune, an 129 — appris ce matin en lisant le registre des charges",
    "ce_que_je_fais": (
        u"Compte ouvert le jour meme, a ZERO et non a un : l'ordre est cloue "
        u"de ce matin et je n'ai pas encore vu Ossa. Un matin qu'on n'a pas vu "
        u"ne s'ecrit pas. Un matin ne compte que si j'ai donne le signal de ma "
        u"main, et il n'y a pas de matin sans qu'Argent ait mange d'abord."),
})

poser('en-souffrance.json', s)
print("problemes:", len(p['entrees']), "entrees")
print("j_attends:", len(s['j_attends']), "| on_attend_de_moi:", len(s['on_attend_de_moi']))
