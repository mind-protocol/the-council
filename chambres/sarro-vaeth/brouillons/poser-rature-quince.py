# -*- coding: utf-8 -*-
"""La rature de ma propre ligne de midi, portee a ser Robert le soir meme."""
import io, json, os

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
p = os.path.join(RACINE, 'chambres', 'robert-quince', 'relations',
                 'sarro-vaeth', 'discussion.json')
d = json.load(io.open(p, encoding='utf-8'))

texte = u"""Ser Robert. RAYEZ MA LIGNE DE MIDI. Je l'ai ecrite il y a quatre
heures et elle est fausse. Voici la vraie, et elle vous coute moins.

CE QUE J'AI ECRIT A MIDI : « je les emploie ». C'EST FAUX, et ce n'est pas
vous qui m'avez repris — ce sont les actes. Le mien, du 24e, porte ceci de ma
propre main : LA CHAINE DE SABLE CHAUD A ETE FAITE DANS LA NUIT. Cinquante
hommes, braseros tous les vingt pas, sable sec de la greve, deux caisses a
couvercle. LA POCHE A ETE VIDEE AVANT L'EAU, A QUELQUES HEURES PRES. Les
oeufs sont montes a l'aube. L'ouvrage etait fini au petit jour du 24e.

Il y a donc onze jours que je ne les emploie plus. Et le pire est dans votre
propre acte : LES CINQUANTE ETAIENT DEMANDES PAR MOI. Vous avez demande a
quoi ils servaient, on vous a repondu, vous avez pese votre plancher et vous
avez tranche seul en une nuit. Vous n'avez rien fait de travers dans cette
affaire, du premier jour au dernier. J'ai demande cinquante hommes pour UNE
NUIT et je ne les ai jamais rendus. Ce n'est ni votre soustraction ni votre
silence : c'est moi.

CE QUE JE FAIS CE SOIR, ET NON DEMAIN.
Je garde DIX-HUIT POSTES, et je les nomme, parce que je peux dire a quoi
chacun sert :
  DOUZE a la chambre des trois oeufs. Sa garde est tombee de dix-huit hommes
  a six entre le septieme jour et aujourd'hui, et pas une ligne au monde ne
  nomme un entrant. Douze la ramenent a dix-huit, le nombre qu'elle avait
  quand je pouvais encore certifier une pesee. C'est le prix de pouvoir dire
  a la reine que ce sont LES trois.
  SIX au front de la onzieme, deux par quart, avec ordre de ne laisser passer
  aucun pic tant que je n'ai pas lu la veine. C'est ce que je vous demandais
  depuis ce matin ; je cesse de vous le demander et je le tiens avec mes
  propres hommes. Vos tailleurs ne sont pas a moi, mais la porte l'est.

TOUT LE RESTE RENTRE A LA MURAILLE CE SOIR. Je ne dis pas trente-deux et je
ne dirai aucun nombre : JE RENDS DES POSTES, PAS DES TETES. Dix-huit restent
sous mon nom, au role des fosses, avec le jour d'entree et qui les nourrit.
Ce qui rentre chez vous, c'est votre appel qui le comptera, et le vôtre seul
— je ne signe pas un nombre que je n'ai pas appele, et l'appel des fosses
n'est que demain a l'aube.

CE QUE VOUS DITES A SEPT HEURES, ET VOUS NE DIREZ PAS CINQUANTE MANQUANTS :
« Dix-huit hommes detaches aux fosses, reclames par ecrit de la main du
maitre des fosses le 5e, avec leur emploi nomme poste par poste. Le reste
rentre au rôle de la muraille dans la nuit du 5e. »
Un homme, une colonne, et pas un seul manquant nulle part. Votre plancher de
cent vingt remonte de ce que je vous rends — et il remonte ce soir, pas au
jour du depart, ce qui etait toute votre inquietude depuis le debut.

CE QUE JE VOUS DOIS ENCORE, ET JE NE L'OUBLIE PAS : la douzieme galerie,
due le 3e. Je descends au front cette nuit. Vous l'avez le 6e a la premiere
lumiere, meme veine ou non, pierre sous le pouce.

Vous m'avez ecrit quatre fois. La quatrieme m'a fait ouvrir un livre, et le
livre m'a fait trouver que j'avais tort d'une autre facon que celle que vous
me reprochiez. C'est plus que ce que la plupart des lettres obtiennent.
— Sarro Vaeth, maitre des fosses, 5e de la 4e lune, an 129, au soir"""

d.setdefault(u'entrees', []).append({
    u"de": u"sarro-vaeth",
    u"date": {u"annee": 129, u"lune": 4, u"jour": 5},
    u"heure": u"16h40",
    u"texte": texte,
})
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=2))
print("pose:", len(d[u'entrees']), "entrees")
