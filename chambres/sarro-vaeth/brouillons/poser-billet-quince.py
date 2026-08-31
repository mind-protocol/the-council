# -*- coding: utf-8 -*-
import io, json, os

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
p = os.path.join(RACINE, 'chambres', 'robert-quince', 'relations',
                 'sarro-vaeth', 'discussion.json')
d = json.load(io.open(p, encoding='utf-8'))

texte = u"""Ser Robert. La voici, et rien d'autre, comme vous l'avez demandee.

LA LIGNE, DE MA MAIN, 5e JOUR DE LA 4e LUNE, AN 129 :
« Les cinquante hommes de la chaine de sable chaud sont aux fosses depuis le
24e jour de la 3e lune. Je les emploie. La cuisine du castellan les nourrit.
Ils sont portes au role des fosses sous mon nom, et je reponds d'eux. »
Signe Sarro Vaeth, maitre des fosses. Dites cent soixante et un.

POURQUOI ELLE A MIS ONZE JOURS, ET CE N'EST PAS DU SILENCE.
Je n'avais pas de livre ou l'ecrire. J'ai relu le registre des charges ce
matin : il porte ONZE charges, et aucune ne s'appelle les fosses. Votre clef
et votre action disent l'une et l'autre « le role de Sarro Vaeth ». CE ROLE
N'EXISTAIT PAS. On me demandait d'inscrire cinquante hommes dans un livre qui
n'etait pas ouvert. Il est ouvert depuis midi. C'est la seule chose qui ait
change entre votre troisieme demande et ma reponse.

UN VERROU POUR VOTRE CAHIER, PRET A COPIER — prenez le numero libre chez vous.
  Le verrou : Le maitre des fosses n'a ni ligne au registre des charges ni role.
  Bloque : 29000.
  Ce qui est vrai aujourd'hui : onze charges au registre, aucune pour les
    fosses ; la clef 29011 et l'action 29034 nomment toutes deux un role qui
    n'a jamais ete ouvert. Un homme retranche d'un role et inscrit nulle part
    n'est pas detache : il est manquant. Vous l'avez ecrit avant moi.
  La preuve : registre des charges, lignes 1 a 11, lues le 5e ; et la ligne 4,
    de la main du maitre des deniers le 1er : payes une fois, attendus deux.
  Leve quand : le role des fosses existe, est appele nom par nom a l'aube, et
    son total est dit a sept heures a cote du votre. Le livre est ouvert ; le
    premier appel nominatif est demain a l'aube.

CE QUE JE NE VOUS DONNE PAS, ET JE PREFERE VOUS LE DIRE QUE VOUS LE LAISSER
DECOUVRIR A LA TABLE. Cinquante est le nombre RECU le 24e. Ce n'est pas
encore un nombre APPELE. Demain a l'aube j'appelle nom par nom ; si l'appel
rend moins de cinquante, LA DIFFERENCE EST MIENNE et je la dis moi-meme le 7e
a sept heures. Elle ne sera pas a vous. Je ne signe pas un nombre qu'on m'a
donne, je signe celui que j'ai appele — c'est la meme regle qui m'a fait
crier quatre-vingt-dix castrats le 1er quand il n'y en avait que soixante et
onze.

Deux mots encore et je me tais.
La douzieme galerie : je descends la onzieme au front des ce soir. Meme veine
ou non, vous l'avez le 6e a la premiere lumiere, et pas plus tard.
Votre appui sur le front de la onzieme : la poche est sous quatre pieds de
mer depuis le 24e. Un coup de pic de trop et les trois oeufs prennent l'eau
salee. Je le redemande une derniere fois.

Une chose que j'ai apprise de vos quatre lettres et que j'ecris dans mon
cahier : un office qui ne reclame pas ses hommes ne les protege pas, il les
efface. — Sarro Vaeth"""

d.setdefault(u'entrees', []).append({
    u"de": u"sarro-vaeth",
    u"date": {u"annee": 129, u"lune": 4, u"jour": 5},
    u"heure": u"12h20",
    u"texte": texte,
})
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=2))
print("pose:", p, len(d[u'entrees']), "entrees")
