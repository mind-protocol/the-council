# -*- coding: utf-8 -*-
"""NARRATEUR — le contrat de rapport du narrateur local, et la mission
historique (le format d'avant les tentatives).
"""
import json
import os
import re

from etat.expose import tables

from agents.depeche.brief import (RACINE, ETAT, PARLOIR_PY, travaux_ids,
                                  livre,
                                  lire, date_du_monde,
                                  brief_de, travaux_ouverts_de,
                                  dossier_journee, positions, position_de,
                                  dans_le_rayon)

def contrat_rapport_narrateur(contexte):
    """Contrat mécanique donné seulement à la phase d'arbitrage."""
    present = float((contexte or {}).get("present_secondes") or 0)
    minimum = int((contexte or {}).get("duree_minimale_secondes") or 1)
    return u"""## Contrat du rapport

Une activité est un geste continu entre deux bifurcations. Condense toute
continuité routinière ; conserve sa durée physique. Découpe seulement si une
décision, une résistance, un témoin, un lieu, une ressource, une connaissance
ou un résultat change.

Types de résultats : observation, progression_tache, variation_mesure,
deplacement, objet_produit, communication, fait, blocage, echec.

Rends uniquement :
{
  "qui": "acteur_id",
  "activation": {
    "tache": {"id": "tache_id", "quoi": "...", "creee": false},
    "issue": "avance|termine|bloque|echoue|rien",
    "activites": [{
      "id": "act:<acteur>:<ordre>",
      "ordre": 1,
      "temps": {"debut_s": %(present)s, "duree_s": 1, "fin_s": %(present_plus_un)s},
      "action": {"verbe": "...", "quoi": "...", "cibles": ["ref:canonique"]},
      "chemin_execution": [{"ordre": 1, "de": "ref:depart", "relation": "...", "vers": "ref:arrivee", "duree_s": 1}],
      "sources_touchees": [{"ref": "ref:canonique", "mode": "voit|entend|lit|parle|manipule|parcourt|mesure"}],
      "sources_mobilisees": [{"ref": "ref:connue", "mode": "memoire|intention|croyance|mandat|cible_action"}],
      "resultats_produits": [{
        "id": "res:<activite>:1", "type": "observation",
        "cible": "ref:canonique", "avant": null, "apres": "...",
        "portee": "connaissance_acteur", "source_refs": ["ref:canonique"],
        "preuve_refs": [], "certitude": "constate"
      }],
      "blocage": null
    }],
    "suite": null,
    "reveils_suivants": []
  },
  "mutations_proposees": []
}

Contraintes : les activités sont ordonnées, continues et sans chevauchement.
Leur durée totale est comprise entre %(minimum)d secondes et le budget. Chaque
chemin totalise exactement la durée de son activité. Écrire, parler, marcher,
chercher et manipuler prennent réellement du temps ; l'ellipse économise la
prose, jamais les secondes.

Toute adresse vient du dossier. Aucun préfixe `candidate:`. Chaque résultat a
des `source_refs`, présentes dans les sources touchées ou mobilisées, le
chemin, la cible de l'action ou un résultat antérieur. Une continuité reprend
mot pour mot son dernier `apres` dans `avant`.

Une issue `avance` ou `termine` produit un `progression_tache` visant l'id exact
de `tache_elue`; `bloque` produit un `blocage`; `echoue`, un `echec`.

Les mutations sont seulement proposées. CHACUNE PORTE EXACTEMENT CETTE FORME,
et le nom des clés n'est pas négociable — une mutation qui cite son résultat
sous une autre clé que `resultat_id` est jetée sans être lue :

{
  "resultat_id": "res:act:<acteur>:1",
  "table": "intentions",
  "operation": "croyance_ajouter",
  "cible": "<id visé dans cette table>",
  "valeur": "<la valeur, pour les opérations qui en prennent une>",
  "champs": {"<champ>": "<valeur>"}
}

`resultat_id` reprend MOT POUR MOT l'`id` d'un `resultats_produits` du présent
rapport : une mutation qui ne se rattache pas à un résultat déclaré n'a pas eu
lieu. `valeur` ou `champs` selon l'opération, jamais un autre nom. Pas de clé
`cite`, `domaine`, `op`, `personnage_id` ni `table.operation` collés en un seul
mot : la table et l'opération sont deux clés distinctes.

Opérations admises, par table :
  intentions   etape, etape_ajouter, tete, tete_ajouter, croyance_ajouter,
               croyance_retirer, ignore_ajouter, ignore_retirer,
               declencheur_ajouter, declencheur_retirer
  books        affaire_ajouter, affaire_action_ajouter, affaire_action
  evenements   diffusion_livree, diffusion_ajouter, evenement
  personnages  personnage, personnage_ajouter
  monde        monde
  mains        mesure, seuil, main, main_ajouter
  plis         pli, pli_ajouter
  lieux        roukerie
  jetons       incident_propage, incident
  relations    relation, relation_ajouter

Aucune autre table n'existe. Ne propose rien que ta journée n'ait réellement
produit.

Les affaires, dont la `cible` a une forme stricte :
  books.affaire_ajouter          cible = `affaire-<nom-en-kebab>` (neuf),
                                 valeur = {"titre": "..."}
  books.affaire_action_ajouter   cible = `affaire-<...>` (l'affaire entière),
                                 valeur = la LISTE des cellules, une par
                                 colonne de sa table d'actions, dans l'ordre
  books.affaire_action           cible = `affaire-<...>:<n° de l'action>`,
                                 champs = {"<intitulé exact de colonne>": "..."}

Le numéro d'une action est celui de sa première cellule dans le cahier, jamais
l'id d'un nœud du tissu. Une affaire à toi — ce que tu poursuis et qui n'est
écrit nulle part — s'ouvre par `affaire_ajouter`.

Ta tête, dont la forme est aussi stricte, et où l'on se trompe toujours de la
même façon. « Voici ce que je poursuis maintenant », en une phrase, N'EST PAS
une étape : c'est `tete`. Une `etape` patche une étape QUI EXISTE DÉJÀ dans ton
plan, et il faut la nommer par son id :
  intentions.tete            cible = ton id, champs = {"intention": "..."} —
                             la phrase de ce que tu poursuis. Autres champs
                             admis : echelle, attitude_joueur, date_maj.
                             JAMAIS de `valeur` en texte libre.
  intentions.etape           cible = ton id, `etape` = l'id EXACT d'une étape
                             de ton plan (le dossier te le donne),
                             champs = {"etat"|"jours_restants"|"quoi"|"cout"|
                             "si_bloque"|"depend_de"|"accompli": ...}.
                             Sans clé `etape`, la mutation est jetée.
  intentions.etape_ajouter   cible = ton id, valeur = {"id": "<kebab neuf>",
                             "quoi": "..."} — les deux sont requis.
  intentions.croyance_ajouter  cible = ton id, valeur = la croyance en clair.

`cible` est TOUJOURS un personnage_id qui a déjà une tête — jamais un id
d'étape, jamais un id d'affaire. Si tu n'as pas de tête, tu n'en fabriques pas
une par `etape` : c'est `tete_ajouter`, et il faut alors personnage_id,
echelle, croyances, intention, plan et date_maj.

Les relations, où l'on oublie toujours de dire QUI regarde QUI. Une relation
est dirigée et ses deux bouts vivent DANS `valeur`, jamais dans `cible` :
  relations.relation_ajouter  valeur = {"source_id": "<celui qui juge>",
                              "cible_id": "<celui qui est jugé>",
                              "opinion": <entier de -100 à +100>,
                              "liens": [...], "connue_du_joueur": true|false}
  relations.relation          mêmes `source_id` et `cible_id` dans `valeur`
                              pour désigner la relation, puis les champs à
                              changer. La relation doit déjà exister, et le
                              sens compte : A→B n'est pas B→A.
Aucun autre champ n'est admis. Une opinion hors des bornes, ou un `liens` qui
n'est pas une liste, fait jeter la mutation entière.
""" % {
        "present": json.dumps(present),
        "present_plus_un": json.dumps(present + 1),
        "minimum": minimum,
    }


def _mission_historique(qui, brief, consigne):
    depot = os.path.join(RACINE, "").replace("\\", "/")
    gens = tables.lire(os.path.join(ETAT, 'personnages.json'), [])
    if isinstance(gens, dict):
        gens = gens.get('personnages', [])
    noms = {g.get('id'): g.get('nom') or g.get('id') for g in gens}
    siens, maison = livre.index(qui, noms)
    etagere = u"""
════════════════════════════════════════════════════════════════════════
CE QUE TU PEUX OUVRIR — ton etagere, et rien de plus

Cette liste est CLOSE. Un volume qui n'y est pas ne t'est pas refuse : il
n'existe pas pour toi. Tu ne le cherches pas, tu ne le devines pas, tu ne
demandes pas pourquoi il n'y est pas. Les carnets des autres, ce qui est
range chez la reine, ce que d'autres yeux se reservent — tu n'en sais rien.

Ils sont POSES A COTE DE TOI, un fichier par volume, dans ./livres/ :
    Read  ./livres/<identifiant>.txt      pour en ouvrir un
    Grep  ... --path ./livres             pour chercher dans tous a la fois

N'ouvre JAMAIS etat/books.json : il porte les volumes de toute la maison,
il fait deux millions de signes, et tu y perdrais ta journee entiere.

%(siens)s%(maison)s
""" % {
        "siens": (u"  LES TIENS — tu les portes, ils sont toujours a portee\n"
                  + u"\n".join(siens) + u"\n\n") if siens else u"",
        "maison": (u"  CEUX DE LA MAISON — poses ou portes la ou tu es\n"
                   + u"\n".join(maison)) if maison else
                  u"  (rien d'autre que les tiens)",
    }
    return u"""%(brief)s
%(etagere)s
════════════════════════════════════════════════════════════════════════
CE QUI EST A TOI AUJOURD'HUI

Le depot est ouvert en lecture a cette adresse : %(depot)s

CE QUI EST GROS, ON LE FOUILLE — ON NE LE LIT PAS. Trois fichiers pesent
plus qu'une journee d'homme : etat/books.json (2 Mo — tu as ton etagere,
n'y touche pas), etat/paroles.json (570 ko), etat/actes.json (400 ko).
Sur les deux derniers : Grep un nom, une date, un mot, et Read seulement
autour de ce que tu as trouve. Un Read entier de l'un d'eux te coute ta
journee et ne te rend rien.

Le reste de etat/ se lit normalement.
`python scripts/dossier.py --sur <sujet>` n'est PAS a ta portee :
tu n'as que des yeux, lis les fichiers.

TON RAPPORT NE SE POSE PAS SUR LE DISQUE PAR TA MAIN : ta derniere reponse
suffit, un autre l'y met. Le brief ci-dessus dit
« dans etat/rapports/... » — ignore cette phrase-la, et cela seulement.

LE PARLOIR — ON PEUT T'ADRESSER LA PAROLE PENDANT TA JOURNEE.

Si quelqu'un te parle, sa phrase te tombera dessus au milieu de ton travail,
sans que tu l'aies demandee. Ce n'est pas une note de service : c'est
quelqu'un qui s'adresse a toi. Tu lui reponds comme dans une piece — court,
dans ta langue, avec ce que tu as sous la main a cet instant :

    python %(parloir)s --dire --de %(qui)s --a mj "..."

Puis tu reprends ton travail exactement ou tu l'avais laisse. Trois choses :
· tu ne reponds que si l'on t'a parle — on ne dit pas bonjour au vide ;
· ce qui se dit au parloir ne remplace PAS ton rapport final, et n'en
  dispense pas : ta journee se rend comme d'habitude, en JSON, a la fin ;
· ce qu'on t'y apprend est une source comme une autre — si ca t'apprend
  quelque chose, ca devient une pensee, avec « au parloir » pour source.

TA DERNIERE REPONSE EST TON RAPPORT, et elle ne contient QUE lui : un objet
JSON, sans phrase avant, sans phrase apres, sans bloc de code autour.

{
  "qui": "%(qui)s",
  "journal": [
    {"heure": "7h00", "duree": 20, "lieu": "<ou tu TRAVAILLES>",
     "quoi": "<ce que tu fais, a la troisieme personne>",
     "resultat": "<ce que ca t'a donne, en clair et chiffre>"},
    {"heure": "7h20", "duree": 15, "de": "<d'ou>", "a": "<vers ou>",
     "quoi": "<il descend au bourg, sa canne sous le bras>", "resultat": "—"}
  ],
  "travaux": [
    {"travail_id": "<un des identifiants donnes plus bas, EXACTEMENT>",
     "dernier_travail": %(aujourdhui)s,
     "pensees": [{"date": %(aujourdhui)s,
                  "source": "<ce que tu as touche, en clair>",
                  "texte": "<ce que ca t'a appris>"}],
     "conclusion": null}
  ],
  "cahier2": [
    {"livre": "...", "table": "...", "ligne": "...", "colonne": "...",
     "valeur": "..."}
  ]
}

TROIS CHOSES QUI FONT REJETER UNE JOURNEE ENTIERE, et qu'on ne devine pas :
· `travail_id` doit etre un identifiant de la liste ci-dessous, au signe pres ;
· chaque pensee porte sa `date`, en objet, et c'est %(aujourdhui)s ;
· la `conclusion` est DANS le travail qu'elle conclut, jamais a la racine —
  et elle reste `null` tant qu'elle n'est pas mure.

TES IDENTIFIANTS DE TRAVAIL — recopie-les au signe pres, on ne les devine pas :
%(travaux_ids)s

DEUX SORTES DE PAS, ET ELLES NE SE CONFONDENT PAS :
· un pas de TRAVAIL porte `lieu` — c'est la que tu cherches quelque chose ;
· un pas de MARCHE porte `de` et `a`, sans `lieu` — c'est toi qui te
  deplaces, son `resultat` peut valoir « — » et personne ne t'en tiendra
  rigueur. Un homme qui marche n'a pas echoue.

UNE PENSEE A CHAQUE PAS DE TRAVAIL. C'est la regle du jour et elle est
ferme : tout pas qui porte un `lieu` doit donner AU MOINS une pensee dans
`travaux`, avec sa `source` qui renvoie a ce pas-la. Un pas de travail sans
pensee est un pas SEC — tu es alle quelque part chercher quelque chose et tu
n'en rapportes rien —, et il se compte contre toi. Si la source n'a
reellement rien donne, ce n'est pas un pas sec : c'est une pensee qui dit ce
que tu as cherche, ou tu l'as cherche, et pourquoi ce n'etait pas la. Un
« non » etabli est un resultat ; un silence n'en est pas un.

Une matinee entiere dans vingt-deux ans de relevés donne beaucoup : ecris
autant de pensees qu'elle en a donnees. La rarete porte sur les AFFAIRES
touchees, jamais sur ce que tu en apprends.

LES BORNES, et elles sont dures :
· DEUX affaires touchees au plus dans la journee. Pas trois.
· PAS DE SOURCE, PAS DE PENSEE. Une pensee sans quelque chose que tu as
  reellement touche aujourd'hui n'existe pas. C'est la seule regle que ce
  rapport fait respecter mecaniquement.
· Tu inventes largement la MATIERE — des gens, des prix, des rancunes, un
  nom qu'on te donne au banc. Tu n'inventes JAMAIS le VERDICT : ce que la
  source pouvait rendre, elle le rend, et « rien » est une reponse honnete
  qui se journalise comme les autres.
· Une `conclusion` est de TA main, en toutes lettres, et elle part dans
  ton cahier. Tant qu'elle n'est pas mure, elle reste `null`.
· Rien de ce que tu n'as pas appris ne t'est connu. Ton brief est la
  totalite de ce que tu sais.

%(consigne)s""" % {
        "brief": brief, "depot": depot, "qui": qui, "etagere": etagere,
        "parloir": PARLOIR_PY,
        "travaux_ids": travaux_ids(qui),
        "aujourdhui": json.dumps(
            dict(zip(("annee", "lune", "jour"), date_du_monde()))),
        "consigne": (u"CE QU'ON TE DEMANDE EN PLUS AUJOURD'HUI\n" + consigne
                     if consigne else u""),
    }

