# -*- coding: utf-8 -*-
import io, json, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
p = 'books/affaire-ollo-marran.json'
d = json.load(io.open(p, encoding='utf-8'))
tb = [t for t in d['tables'] if t['titre'].startswith(u'\u2694')][0]
n = len(tb['colonnes'])
J = '129.5.12'
faits = {
 'P.1': ('faite', u"Lu jusqu'au bout ce matin, y compris mes propres amendements du 3e et du 4e de la 4e lune."),
 'P.2': ('faite', u"Trois titres de ma main, a la premiere personne : 129.4.3, 129.4.4, 129.5.12."),
 'P.3': ('faite', u"La ligne du dix-neuf, de ma main, relue mot pour mot dans la copie tenue a la cabane du peigne (roles-de-la-gadoue) : coque sans nom, Villevieille, deux hommes d'armes, non porte. La note qui y parle de moi n'est PAS de moi : elle me nomme a la troisieme personne."),
 'P.4': ('faite', u"Six buts sous les cibles, dont C.4 (rien ne me nomme par ecrit) et C.5 (la case vide ne se remplit plus d'une main sans office)."),
 'P.5': ('faite', u"Le 12e de la 5e lune : mon silence signe, un refus annonce est une mesure, la preuve est faite de deux papiers."),
 'P.6': ('faite', u"Ouverte sous D.1 a D.3, dans cette meme table : la ligne du dix-neuf est mon affaire a moi, non celle du bureau."),
 'P.7': ('faite', u"en-souffrance.json porte trois fils (ce que j'attends du prince, ce que je lui ai promis, ce que je me dois a moi) ; problemes.json porte la panne d'ecriture du 12e."),
 'P.8': ('faite', u"Cherche sans demander a personne : la copie de la Nera, mes propres traces, et la lettre de Villevieille qui m'a appris ce que je ne pouvais pas savoir seul : le conge de la-bas porte patron, port d'armement et jour de sortie."),
 'P.9': ('faite', u"Repondu deux fois au prince Daeron de mon propre chef, en portant la ligne mot pour mot et en retirant le seul nom. Consequence laissee en attente : l'ecart des deux registres, qu'il verifie chez lui."),
 'P.10': ('faite', u"Deux billets au parloir a daeron, 129.5.12. Canal : relations/daeron/."),
}
for l in tb['lignes']:
    ref = l['cellules'][0]
    if ref in faits:
        etat, note = faits[ref]
        l['cellules'][5] = etat
        l['cellules'][7] = J
        l['cellules'][8] = note
neuves = [
 ["D.1", u"Relire chaque matin la case du destinataire au dix-neuf",
  u"Ouvrir le feuillet clos de la semaine du dix-neuf et verifier que la case du destinataire est toujours VIDE. Ne rien y ecrire, ne rien corriger : constater.",
  u"le registre du bureau des roles",
  u"la case toujours vide, ou le jour ou elle a cesse de l'etre",
  u"en cours", J, J,
  u"Ma case vide ne prouve que tant qu'elle est vide : comblee apres coup, elle accorde faussement les deux rives et efface l'ecart. Servir un registre, c'est le relire ; celui-la est dans ma charge."],
 ["D.2", u"Regarder les roles de SORTIE du dix-neuf au vingt-trois",
  u"Les avoir sous les yeux sans qu'on me demande pourquoi, et voir si la coque sans nom est repartie et vers ou. Ne pas deviner : rapporter ce qui est ecrit, ou que rien ne l'est.",
  u"hors de mon livre : les sorties ne sont pas de ma plume",
  u"une ligne de sortie, ou l'inconnu ecrit tel quel",
  u"a faire", "", "",
  u"Promis au prince Daeron le 12e, et je n'ai promis que de regarder. Le risque est d'etre vu a les ouvrir : j'attends un jour ou ma presence devant ces feuillets s'explique par l'ouvrage."],
 ["D.3", u"Attendre l'ecart des deux registres, sans le relancer",
  u"Le conge de Villevieille du dix-neuvieme doit porter patron, port d'armement et jour de sortie. S'il le porte et que mon role n'en porte pas, l'ecart se lit sans moi. Le prince le cherche chez lui.",
  u"Villevieille, pas ici",
  u"sa reponse, ou son silence au 19e",
  u"en cours", J, "",
  u"Ne rien relancer : il m'a dit qu'il ne me redemanderait rien, et je ne lui dois rien. Au 19e sans nouvelle, je ferme le fil et je tiens l'ecart pour non verifie."],
]
for c in neuves:
    assert len(c) == n, (len(c), n)
    tb['lignes'].append({"cellules": c})
io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))

pp = 'problemes.json'
q = json.load(io.open(pp, encoding='utf-8'))
q['entrees'] = [{
 "jour": "129.5.12",
 "tente": u"Ecrire mes deux cahiers de memoire par un petit script, en chemin court depuis ma chambre.",
 "ce_qu_elle_en_a_fait": u"Refus a l'ouverture en ecriture, « Invalid argument », sur le chemin court — alors que la LECTURE du meme chemin, un souffle plus tot, avait marche.",
 "ce_que_j_attendais": u"Que ce qui se lit se reecrive au meme endroit.",
 "leve_par": u"Refait en chemin entier calcule depuis le dossier, sans rien changer d'autre. Passe du premier coup.",
 "note": u"Ecrit sans l'expliquer : lire n'est pas ecrire, et un chemin qui sert a l'un ne sert pas forcement a l'autre. Si cela recommence, soupconner le chemin court en premier."
}]
io.open(pp, 'w', encoding='utf-8').write(json.dumps(q, ensure_ascii=False, indent=1))
print('livre et journaux tenus')
