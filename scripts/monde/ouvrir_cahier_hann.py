# -*- coding: utf-8 -*-
# Ouvre a la main le cahier de l'office O01 — l'aire de bris, chantier de la
# vase. Le verseur ne cree ni livre ni table : ceci est le geste manuel, fait en
# connaissance de cause, le 2e jour de la 4e lune de l'an 129.
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(R, 'scripts'))
import bibliotheque
from etat.expose import tables  # LA PORTE de etat/

BOITES = os.path.join(R, 'etat', 'boites.json')


lire = tables.lire


def ecrire(p, d):
    tables.ecrire(p, d, indent=1)


def L(*c):
    return {"cellules": list(c)}


ouverture = {
 "titre": "\U0001F3F0 Ouverture de l'Affaire — chantier de la vase, 2e jour de la 4e lune",
 "colonnes": ["\U0001F9F1 Le champ", "✍️ Ce qu'on y écrit",
              "\U0001F4D6 La règle du champ", "✅ Rempli ?"],
 "lignes": [
  L("\U0001F3F7️ **LE NOM**",
    "L'AIRE DE BRIS. Le sujet est l'aire elle-même : le bois qu'on y casse, les bras qui le cassent, l'ordre dans lequel on le casse. Pas ce qu'on en fait après, pas qui le paie.",
    "Le sujet dont on traite, **jamais la solution**.", "**oui**"),
  L("\U0001F3AF **L'OBJET**",
    "FONCTIONNER écrit que la maison paie et qu'elle tient trois jours sans Marlo. Elle tient parce que je suis là. **Personne n'a écrit ce qui se passe si c'est moi qui manque**, ni ce que les six bras font le matin où il n'y a plus rien sous la hache. Trois lignes de mon office dorment dans son cahier — 64030, 64031, 64032 — et elles sont faites, toutes les trois. Ce qui n'est pas fait n'est écrit nulle part, et c'est de ça que je réponds.",
    "Une phrase : pourquoi cette affaire mérite qu'on ouvre un volume.", "**oui**"),
  L("\U0001F9F1 **LE PÉRIMÈTRE — DANS**",
    "Le bois sur l'aire et ce qu'on en tire. Les six bras : leurs journées, leur terme, qui sait faire quoi. La cadence du démontage et l'ordre des tâches. Les outils et la corde. Ce qu'on dit à qui entre sur l'aire.",
    "Ce qui appartient à l'affaire, énuméré.", "**oui**"),
  L("\U0001F6AB **LE PÉRIMÈTRE — HORS**",
    "**D'où vient la bourse, où va Marlo, le nom de qui paie et les prix du dehors** : c'est FONCTIONNER, et ce n'est pas mon office. Hors aussi : la vente du bordé (⚔️ 64030, close le 1er), la proclamation du 26e (⚔️ 64031) et la caisse de paie (⚔️ 64032) — faites, je les cite et je n'en récris pas un mot. Hors enfin : la porte de la Gadoue et les deux gosses payés pour compter nos entrées — voir l'état actuel, j'y dis pourquoi je ne l'écris pas en verrou.",
    "Ce qui n'y appartient pas, énuméré aussi. C'est la moitié qu'on oublie.", "**oui**"),
  L("\U0001F4CC **L'ÉTAT ACTUEL**",
    "— **L'aire est nette et vide depuis le soir du 1er** : la coque du 15 descendue jusqu'au lest à la basse de l'aube, triée avant la nuit.\n"
    "— **Six bras sont payés d'avance de sept journées et un tiers** — 1056 sous en caisse contre 142 sous la journée — et il n'y a rien à briser demain matin. J'ai fouillé les quatre volumes au feu : pas une ligne datée qui dise d'où vient la coque suivante.\n"
    "— **Deux des six ne sont là que par Marlo.** Sabbe, quarante ans, aucun métier annoncé ; Ren, quatorze. Arrivés le même jour avec quarante brasses de trois-torons neuf, donnés pour le travail, sans un mot d'où ni de jusqu'à quand.\n"
    "— **Je ne sais pas ce que mon office a le droit d'engager.** Le registre écrit sous O01 : pas les prix du dehors, pas les engagements, pas le nom de qui paie. Il ne dit aucun chiffre.\n"
    "— **Ce que je reconnais ignorer** : d'où vient la bourse du 21e, et où va Marlo quand il part. Et ceci, vu de mes yeux le 1er en changeant de sentier avec treize cerfs sur le dos : deux gosses sont payés deux sous la journée pour compter ce qui entre chez nous. **Ce n'est pas un verrou de ce cahier** — si tout le reste était acquis et que cela restait vrai, l'aire tournerait quand même. C'est une gêne ; elle a sa place ici, et pas plus loin.",
    "Ce qu'on sait, et ce qu'on avoue ignorer. **Jamais ce qu'on espère faire.**", "**oui**"),
  L("\U0001F522 **LA PLAGE**", "**65000 à 65099**",
    "Millier vérifié le 2e de la 4e lune : aucune pièce de la maison ni du royaume n'occupe le 65. Un chiffre est une adresse, non un rang.",
    "**oui**"),
  L("\U0001F4A1 **LA CONCLUSION**",
    "Trente ans que l'aire tourne sur ce que j'ai dans les mains, et c'est exactement ce qui la rend fragile. Un homme irremplaçable est un trou dans un plan, pas une garantie. Je n'écris pas ce cahier pour qu'on me lise : je l'écris pour qu'on puisse me remplacer un jour, et pour qu'on me dise enfin un chiffre.",
    "Ce que ce volume a appris à celui qui le tient.", "**oui**"),
  L("\U0001F51A **FERMÉE QUAND**",
    "Quand un autre que moi aura mené trois jours de bris de suite, la matière étant venue sans que j'aie eu à la demander.",
    "Écrit à froid : à quoi l'on verra qu'il n'y a plus lieu de rouvrir ce cahier.", "**oui**"),
 ]}

liees = {
 "titre": "\U0001F517 Affaires liées — les liens écrits, puis les calculés",
 "colonnes": ["\U0001FAA2 Le lien", "\U0001F517 L'affaire", "\U0001F522 Notre pièce",
              "\U0001F522 La leur", "\U0001F4DD Pourquoi"],
 "lignes": [
  L("dépend de", "FONCTIONNER", "\U0001F3AF 65000", "\U0001F512 64011",
    "Tant qu'aucune entrée de matière n'est écrite avec un jour, un payeur et un prix, mon aire n'a rien sous la hache. Le verrou est à lui, le chômage est à moi. Je le cite, je ne le recopie pas."),
  L("achève", "FONCTIONNER", "\U0001F3AF 65001", "\U0001F3AF 64001",
    "Sa maison tient trois jours sans lui parce que je suis là. Le même test, un rang plus bas, n'avait jamais été posé."),
  L("partage", "FONCTIONNER", "M06 \U0001FAB5 L'aire et six bras", "",
    "Il n'y a qu'une aire, et elle porte ses actions comme les miennes."),
  L("partage", "FONCTIONNER", "O01 \U0001FAB5 Le chantier", "",
    "Mon office. Il en tient la mesure : le lot part et les hommes sont payés le 31e, même s'il ne rentre pas."),
 ]}


def vide(t, c):
    return {"titre": t, "colonnes": c, "lignes": []}


etats = {
 "titre": "\U0001F3AF États cibles",
 "colonnes": ["\U0001F3AF N°", "\U0001F3F7️ L'état", "✅ Ce qui doit être vrai",
              "\U0001F4CD Où", "\U0001F441️ La preuve", "⬆️ Sert"],
 "lignes": [
  L("65000", "\U0001FAB5 Il y a du bois sous la hache le matin qui suit le dernier tri",
    "Au réveil du jour qui suit la fin d'un lot, les six bras savent sur quoi ils frappent — et ce n'est pas moi qui l'ai trouvé la veille au soir en courant.",
    "Le chantier de la vase",
    "L'aire n'est pas vide deux matins de suite, et la feuille des gages ne porte aucune journée payée sans bois en face.",
    "64000 · 64011"),
  L("65001", "\U0001F9CD L'aire tient un jour sans moi, comme la maison tient trois jours sans Marlo",
    "Un homme de l'aire, nommé et connu des cinq autres, mène un jour de bris entier — l'ordre des tâches, le tri, le compte du soir — sans que j'y sois. Et les six sont toujours six le lendemain matin.",
    "Le chantier de la vase",
    "Un jour de bris conduit par un autre, le compte du soir qui tombe juste contre le mien, et six noms à la feuille au matin suivant.",
    "64001"),
 ]}

verrous = {
 "titre": "\U0001F512 Verrous",
 "colonnes": ["\U0001F512 N°", "\U0001F3F7️ Le verrou", "⛔ Bloque",
              "\U0001F4CC Ce qui est vrai aujourd'hui", "\U0001F441️ La preuve", "\U0001F513 Levé quand"],
 "lignes": [
  L("65010", "⛓️ Mon office ne peut ni engager, ni dire un prix, ni nommer un payeur", "65000",
    "Le registre des offices écrit sous O01, en toutes lettres : **pas les prix du dehors, pas les engagements, pas le nom de qui paie**. Il ne dit aucun chiffre sous lequel je déciderais seul — « les dépenses sous deux cerfs » sont le routinier de l'aire, pas une entrée de matière. Mesuré : le lot du bordé a dormi six jours sous l'auvent parce qu'il dépendait d'un nom que je n'avais pas.",
    "Le registre des offices de la Néra, ligne O01, relu le 2e au matin. Et ⚔️ 64030, où la vente s'est finalement faite sous un nom qui n'est pas le mien.",
    "Quand un chiffre en cerfs sera écrit à la feuille, sous lequel je dis oui seul sur une entrée de matière — et qu'il aura été dit devant les hommes, comme le reste l'a été le 26e."),
  L("65011", "\U0001F9CD Deux des six bras n'ont pas de terme, et je ne sais pas jusqu'à quand ils sont à moi", "65001",
    "Sabbe et Ren sont arrivés le même jour, avec une corde neuve, donnés pour le travail, sans un mot d'où ni de jusqu'à quand. Les quatre autres ont la vase depuis trente ans et une famille dans le Boyau : ceux-là, je sais où les reprendre. Ces deux-ci peuvent n'être pas là demain matin, et il n'y a personne à qui le demander.",
    "La feuille des gages : ils portent un taux — douze sous le gamin, vingt-six le grand — et pas un terme. Sabbe interrogé le 1er sur la corde : « Je l'ai portée. Je ne l'ai pas achetée. » Quatre mots, sans se troubler, et il est retourné au feu. Le registre des moyens porte Ren en M08 : **à la reine**.",
    "Quand un terme sera écrit à la feuille des gages en face de leurs deux noms, du même trait qu'un taux."),
  L("65012", "\U0001F56F️ La cadence de l'aire n'est écrite nulle part : elle est dans mes mains", "65001",
    "L'ordre du démontage — le pont, puis les membrures, la descente jusqu'au lest, le tri avant la nuit, et quelle chose se fait à quelle marée — n'est dans aucun des quatre volumes ni sur aucune feuille. La coque du 15 est tombée en une demi-journée parce que j'étais là à dire quoi après quoi. Si je manque un matin, six bras payés d'avance attendent debout qu'on leur dise.",
    "Les quatre volumes fouillés au feu le 1er au soir, sans une seule ligne de cadence. Et trente ans pendant lesquels personne n'a eu besoin de la demander — ce qui est la preuve, pas l'excuse.",
    "Quand la cadence sera clouée à la carcasse et qu'un jour de bris aura été mené dessus sans moi."),
 ]}

clefs = {
 "titre": "\U0001F5DD️ Clefs",
 "colonnes": ["\U0001F5DD️ N°", "\U0001F3F7️ La clef", "\U0001F513 Ouvre", "\U0001F4A1 Le principe",
              "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme", "\U0001F441️ La preuve attendue", "⚖️ Décision"],
 "lignes": [
  L("65020", "\U0001F4B0 Un plafond en cerfs, dit devant les hommes", "65010",
    "Ce qui est proclamé sur le billot ne se reprend pas en silence. Il m'a nommé second devant tous ; un second sans chiffre n'est qu'un contremaître avec un titre.",
    "Il devra dire tout haut un montant qu'il peut perdre sans être là pour le rattraper. Et cela me ferme définitivement « je vais demander à Marlo » quand je ne veux pas trancher.",
    "Le chiffre écrit à la feuille, et deux hommes de l'aire qui l'ont entendu de leurs oreilles.",
    "retenue"),
  L("65021", "✍️ Un terme à la feuille, et pas seulement un taux", "65011",
    "Ce qui est écrit à la feuille se réclame ; ce qui ne l'est pas se dissout un matin sans que personne ait eu à mentir. **Je ne demande pas d'où ils viennent — je demande jusqu'à quand.**",
    "C'est demander une date à un homme qui ne m'a pas répondu devant les hommes la dernière fois. En échange, elle ferme la question de la provenance : si j'ai le terme, je m'interdis le reste, et je le lui dis en le demandant.",
    "Deux dates de ma main en face de deux noms, et un mot de Marlo dessous.",
    "retenue"),
  L("65022", "\U0001F528 Le second du second", "65012",
    "La cadence ne sort de mes mains qu'en passant une fois entière par celles d'un autre. On n'apprend pas un démontage sur une planche — mais on le rattrape sur une planche quand on l'a fait une fois.",
    "Une demi-journée de rendement, environ soixante-dix sous, et le risque qu'un lot soit mal trié. Elle ferme l'idée commode que l'aire ne tourne que sur moi.",
    "Le compte du soir d'un jour de bris que je n'ai pas conduit, posé contre le mien.",
    "retenue"),
 ]}

actions = {
 "titre": "⚔️ Actions",
 "colonnes": ["⚔️ N°", "\U0001F3F7️ L'action", "\U0001F5DD️ Réalise",
              "\U0001F4DD Ce qu'on fait", "\U0001F4CD Où", "\U0001FAB6 Office", "\U0001F9F0 Moyens",
              "\U0001F527 Avec quoi", "⛓️ Dépend de", "\U0001F4C5 Jour dû",
              "⏳ Où ça en est", "\U0001F4C5 Jour fait", "\U0001F4DD Note"],
 "lignes": [
  L("65030", "\U0001F4B0 Demander à Marlo un plafond en cerfs, au feu, devant deux hommes", "65020",
    "Un chiffre sous lequel je dis oui seul sur une entrée de matière, dit tout haut et écrit à la feuille",
    "Le feu de l'aire", "O01", "M06", "—", "—", "le 2e au soir", "en cours", "—",
    "Je ne demande ni d'où vient la bourse, ni où il va. Un chiffre, et rien d'autre. S'il ne le donne pas, je le note ici et je continue sans."),
  L("65031", "✍️ Porter un terme à la feuille des gages en face de Sabbe et de Ren", "65021",
    "Une date de fin écrite en face de deux noms qui n'en ont pas, du même trait que leur taux",
    "Le chantier de la vase", "O01", "M06", "La feuille des gages", "65030", "le 3e", "à faire", "—",
    "Si le terme ne vient pas de lui, je l'écris moi-même à trente jours et je le lui montre. Un terme faux se corrige ; un blanc, non."),
  L("65032", "\U0001FA9A Clouer la cadence du bris à la carcasse", "65022",
    "L'ordre du démontage en douze lignes, du pont au lest, avec la marée à laquelle chaque chose se fait",
    "La carcasse", "O01", "M06", "Une planche, du charbon", "—", "le 4e", "à faire", "—",
    "Une veillée. Ce que trente ans savent tient sur une planche, et je n'y avais jamais pensé avant qu'on me demande un cahier."),
  L("65033", "\U0001F528 Donner à Wat un jour de bris entier, moi à l'écart", "65022",
    "Il conduit, il trie, il fait le compte du soir ; je regarde de la cabane et je ne dis pas un mot",
    "Le chantier de la vase", "O01", "M06", "—", "65032", "le premier jour de bris après le 4e", "à faire", "—",
    "Coût : une demi-journée de rendement, environ 70 sous. Wat parce que c'est lui qui m'a crié la traverse fendue avant que je la voie."),
 ]}

volume = {
 "id": "nera-l-aire-de-bris",
 "boite": "boite-le-second",
 "lieu_id": "port-real",
 "salle_id": "chantier-de-la-vase",
 "tenu_par": "hann-bourbe",
 "office": "O01",
 "type": "plan",
 "embleme": "\U0001FAB5",
 "titre": "L'AIRE DE BRIS",
 "couleur": "var(--book-plan)",
 "sous_titre": "\U0001FAB5 Le bois, les bras, la cadence — ce dont répond l'office O01 et que personne n'avait écrit. Volume ouvert au chantier de la vase le 2e jour de la 4e lune, an 129, de la main de HANN BOURBE, second. Plage 65000 à 65099.",
 "pages": [
  "**POURQUOI CE VOLUME EXISTE.** On m'a nommé second sur le billot du feu le 26e, et pendant six jours rien n'a changé dans les faits : je faisais déjà tout ce qu'on a proclamé que je ferais. Ce qui a changé, c'est que je ne peux plus dire « je vais demander à Marlo » quand je ne veux pas trancher.\n\nJ'ai regardé où mon office était écrit. Il l'est trois fois, et les trois fois dans le cahier d'un autre : vendre le bordé, être proclamé, recevoir la caisse. Les trois sont faites. **Ce dont je réponds à partir de demain n'est écrit nulle part.**\n\nAlors j'ouvre le mien. Deux choses seulement, parce qu'un homme qui rentre avec quatorze bonnes intentions n'a rien fait : **du bois sous la hache**, et **une aire qui tourne un jour sans moi**.",
  "**CE QUE J'AI REFUSÉ D'Y METTRE, ET POURQUOI.** Deux gosses sont payés deux sous la journée pour compter ce qui entre sur cette aire. Je l'ai vu le 1er, en changeant de sentier avec treize cerfs sur le dos. Ça m'empêche de dormir et ça ne m'empêche pas de travailler : si demain j'avais le bois, les bras et la cadence, l'aire tournerait pendant qu'on nous compte.\n\nLe guide dit qu'un empêchement qui laisse l'affaire tenir n'est pas un verrou, c'est une gêne. **Alors c'est une gêne**, et elle reste à l'état actuel de l'ouverture, sur une ligne, sans clef et sans action. Le jour où on nous comptera pour entrer chez nous et pas seulement pour nous regarder, je l'écrirai en verrou et j'y mettrai une date.\n\nMême chose pour la bourse du 21e et pour les jours où Marlo n'est pas là. Ce n'est pas mon office. **Je ne le porterai pas en aveugle, et je ne le porterai pas du tout.**"
 ],
 "tables": [
  ouverture, liees,
  vide("⛓️ Ce qui pend, et sur qui — calculé, ne pas écrire à la main",
       ["\U0001F9ED Sens", "\U0001F522 Notre pièce", "\U0001F522 La leur", "\U0001F517 L'affaire"]),
  vide("\U0001F528\U0001FAB6 Ce qu'on engage, et qui d'autre le veut — calculé, ne pas écrire à la main",
       ["\U0001F522 La pièce", "⚔️ Nos actions", "\U0001F517 Aussi engagée par"]),
  vide("\U0001F573️ Les trous — calculé, ne pas écrire à la main",
       ["\U0001F573️ Le défaut", "\U0001F522 Les pièces"]),
  etats, verrous, clefs, actions,
 ],
}

session_livres = bibliotheque.ouvrir(tables.ETAT)
books = session_livres.livres
if any(b.get('id') == volume['id'] for b in books):
    print('DEJA LA — rien fait')
    raise SystemExit(1)
books.append(volume)
session_livres.sauver()

boites = lire(BOITES)
if not any(b.get('id') == 'boite-le-second' for b in boites):
    boites.append({
      "id": "boite-le-second", "lieu_id": "port-real", "salle_id": "chantier-de-la-vase",
      "lecteurs": ["hann-bourbe", "marlo-vasse"],
      "titre": "Le cahier du second", "embleme": "\U0001FAB5", "couleur": "var(--book-plan)",
      "sous_titre": "Ce dont l'aire répond quand personne ne la regarde. Une seule affaire, et elle ne bouge pas de la carcasse."})
    ecrire(BOITES, boites)
    print('boite creee : boite-le-second')
print('volume pose :', volume['id'], '— plage 65000 a 65099')
