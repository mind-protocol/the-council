# (Ré)initialise etat/flux.jsonl — beat d'ouverture : le conseil noir, format flux append-only.
import json, io, os

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def svg(pid):
    return io.open(os.path.join(racine, "ecrans", "portraits", pid + ".svg"), encoding="utf-8").read()

items = [
    {"type": "effacer", "delai_s": 0,
     "date": {"annee": 129, "lune": 3, "jour": 13},
     "lieu": "Chambre de la Table Peinte, Peyredragon", "tension": 60},
    {"type": "breve", "delai_s": 0,
     "texte": "Port-Réal, dix jours plus tôt : ton père est mort dans son sommeil. Ils l'ont caché le temps de couronner Aegon dans la Fosse Dragon."},
    {"type": "breve", "delai_s": 5,
     "texte": "Ser Steffon Darklyn et des manteaux blancs fidèles ont fui la ville — la couronne de Viserys est en mer, vers tes quais."},
    {"type": "breve", "delai_s": 5,
     "texte": "Les corbeaux d'Otto partent par volées entières : jurer à Aegon, ou être tenu pour traître."},
    {"type": "salle", "delai_s": 4,
     "presents": [
         {"id": "daemon", "nom": "Daemon", "titre": "Prince consort — votre époux", "portrait_svg": svg("daemon")},
         {"id": "corlys", "nom": "Corlys", "titre": "Lord des Marées, maître de la flotte", "portrait_svg": svg("corlys")},
         {"id": "rhaenys", "nom": "Rhaenys", "titre": "La Reine Qui Ne Fut Jamais, cavalière de Meleys", "portrait_svg": svg("rhaenys")},
         {"id": "jacaerys", "nom": "Jacaerys", "titre": "Votre héritier, cavalier de Vermax", "portrait_svg": svg("jacaerys")},
     ]},
    {"type": "recit", "delai_s": 1,
     "texte": "Vous vous tenez debout à la Table Peinte parce que vous refusez qu'on vous voie assise. Trois jours depuis les relevailles ; la fièvre est tombée, pas la douleur. Sur la carte gravée, la baie de la Néra vous sépare de Port-Réal — deux doigts d'écart, un monde. Autour de la table, ils attendent votre parole."},
    {"type": "replique", "delai_s": 6, "locuteur_id": "corlys",
     "texte": "Nous tenons la mer, pas les routes. Fermons le Gosier : pas un grain, pas un tonneau n'entrera dans Port-Réal sans notre congé. Les sièges se gagnent au compte, Votre Grâce — pas au cri.",
     "reactions": [
         {"id": "hocher-la-tete", "texte": "Hocher la tête, lentement"},
         {"id": "suivre-le-gosier-du-doigt", "texte": "Suivre le Gosier du doigt sur la carte"},
     ]},
    {"type": "replique", "delai_s": 7, "locuteur_id": "rhaenys",
     "texte": "Et pendant que la ville maigrit, les Verts mangeront nos petits vassaux de la baie, un château à la fois. Quelqu'un devra garder la côte. Meleys ne demande qu'à voler.",
     "reactions": [
         {"id": "soutenir-son-regard", "texte": "Soutenir son regard"},
         {"id": "gratitude-muette", "texte": "Un signe de gratitude muette"},
     ]},
    {"type": "replique", "delai_s": 7, "locuteur_id": "daemon",
     "texte": "Chaque heure où tu n'es pas couronnée, l'usurpateur achète un seigneur de plus. Donne-moi Caraxès et dix jours, et je t'apporte Harrenhal — ou la tête d'Otto. Les deux, si tu me souris.",
     "reactions": [
         {"id": "toiser-avec-aplomb", "texte": "Le toiser avec aplomb"},
         {"id": "sourire-froid", "texte": "Un sourire froid"},
     ]},
    {"type": "recit", "delai_s": 6,
     "texte": "Jace se tient droit, trop droit — il attend que vous le regardiez pour proposer quelque chose qu'il a répété cette nuit. La couronne de votre père est en mer, quelque part entre les manteaux blancs en fuite et vos quais."},
    {"type": "pensee", "delai_s": 5,
     "texte": "Harrenhal — c'est là qu'un millier de seigneurs ont écarté Rhaenys parce qu'elle portait jupon, et Daemon me l'offre comme un présent de deuil. Sous mes doigts la table est froide, froide comme le petit front de Visenya."},
]

with io.open(os.path.join(racine, "etat", "flux.jsonl"), "w", encoding="utf-8") as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
print("flux.jsonl initialisé :", len(items), "items")
