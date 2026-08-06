# Seed etat/scene.json — beat courant : le conseil noir (ouverture), format salle multi-acteurs.
import json, io, os

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def svg(pid):
    return io.open(os.path.join(racine, "ecrans", "portraits", pid + ".svg"), encoding="utf-8").read()

scene = {
    "version": 2,
    "sequence": [
        {"type": "breve", "delai_s": 0,
         "date": {"annee": 129, "lune": 3, "jour": 13},
         "lieu": "Chambre de la Table Peinte, Peyredragon", "tension": 60,
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
         "texte": "Nous tenons la mer, pas les routes. Fermons le Gosier : pas un grain, pas un tonneau n'entrera dans Port-Réal sans notre congé. Les sièges se gagnent au compte, Votre Grâce — pas au cri."},
        {"type": "replique", "delai_s": 7, "locuteur_id": "rhaenys",
         "texte": "Et pendant que la ville maigrit, les Verts mangeront nos petits vassaux de la baie, un château à la fois. Quelqu'un devra garder la côte. Meleys ne demande qu'à voler."},
        {"type": "replique", "delai_s": 7, "locuteur_id": "daemon",
         "texte": "Chaque heure où tu n'es pas couronnée, l'usurpateur achète un seigneur de plus. Donne-moi Caraxès et dix jours, et je t'apporte Harrenhal — ou la tête d'Otto. Les deux, si tu me souris."},
        {"type": "recit", "delai_s": 6,
         "texte": "Jace se tient droit, trop droit — il attend que vous le regardiez pour proposer quelque chose qu'il a répété cette nuit. La couronne de votre père est en mer, quelque part entre les manteaux blancs en fuite et vos quais."},
        {"type": "pensee", "delai_s": 5,
         "texte": "Harrenhal — c'est là qu'un millier de seigneurs ont écarté Rhaenys parce qu'elle portait jupon, et Daemon me l'offre comme un présent de deuil. Sous mes doigts la table est froide, froide comme le petit front de Visenya."},
        {"type": "choix", "delai_s": 4,
         "choix": [
             {"id": "couronnement-d-abord",
              "texte": "La couronne d'abord. Qu'on me couronne devant dieux et hommes — ensuite le royaume saura à qui parler. Convoquez mes bannerets."},
             {"id": "lacher-daemon-harrenhal",
              "texte": "Dix jours, pas un de plus. Prends Caraxès, prends Harrenhal — et rapporte-moi une victoire, pas une guerre nouvelle."},
             {"id": "fausses-negociations",
              "texte": "Otto veut des corbeaux ? Il en aura. Écrivons-lui des réponses assez douces pour l'endormir — pendant que la flotte se déploie sans bruit."},
         ],
         "placeholder_libre": "Autre chose — vos mots à vous…"},
    ],
}

with io.open(os.path.join(racine, "etat", "scene.json"), "w", encoding="utf-8") as f:
    json.dump(scene, f, ensure_ascii=False, indent=2)
print("scene.json seede, version", scene["version"])
