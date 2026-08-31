# -*- coding: utf-8 -*-
"""CHAMBRE — le domicile d'un habitant (docs/habitant.md §2).

LA SEULE REGLE, ET ELLE EST DE GEOGRAPHIE : RIEN DANS chambres/ NE FAIT FOI.
La chambre est de la memoire et du caractere ; la verite vit dans etat/, et
tout ce qui doit devenir vrai passe par la porte (tables, versements,
staging). Une chambre peut se tromper sur le monde — c'est meme son droit.

Tout ce qui pense a une chambre : les hommes, les MJ de zone (mj,
mj-peyredragon…), le MJ du joueur. Memes fonctions pour tous, aucune branche
speciale — un MJ sans fiche dans personnages.json recoit simplement un cahier
plus nu.

    chambres/<id>/
       claude.md            sa maniere, DE SA MAIN — seedee UNE FOIS depuis la
                            fiche, plus jamais touchee par nous
       problemes.json       les pannes de l'APPAREIL qu'il rencontre
       en-souffrance.json   les fils ouverts : ce qu'il attend, ce qu'on attend
       fil/                 les traces de ses sessions
       books/               ses volumes, sous sa main
       brouillons/          l'iteratif — ce qui murit avant de se verser
       relations/<autre>/
          claude.md         ce que LUI retient de l'autre (subjectif)
          discussion.json   le canal — canonique chez l'un des deux
          .lu               le curseur de lecture de CE cote-ci du canal

LES DEUX JSON SONT UNE INVENTION D'HABITANT, PROMUE AU TEMPLATE. Le mestre
Gerardys les a ouverts de sa propre main, sans que rien ne les lui demande, et
ils tiennent tous deux ce qu'aucune autre table ne tient : `problemes.json` les
pannes de la MACHINE (un versement refuse en silence, sept coordonnees qui
n'atteignent jamais la file) par opposition aux empechements du monde, qui sont
des verrous et vont au registre ; `en-souffrance.json` les GENS qui n'ont pas
repondu et depuis quand, la ou le plan ne compte que des pas. Un habitant qui
naissait apres lui repartait de rien. On les seme donc vides, avec leur regle
en tete et pas une entree : la doctrine est de nous, le contenu est de lui.
"""
import io
import json
import os

from etat.expose import tables  # LA PORTE de etat/ — meme pour une lecture

# Deux etages au-dessus : scripts/agents/ -> la racine du depot.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CHAMBRES = os.path.join(RACINE, "chambres")

DOSSIERS = ("fil", "books", "brouillons", "relations")

ENTETE = u"Ce cahier est à moi. Je l'amende quand ma journée me contredit."

# Les deux cahiers semes vides : leur regle en tete, aucune entree. Les textes
# sont ceux du mestre, generalises — c'est lui qui a trouve la distinction, et
# elle est trop bonne pour rester dans une seule chambre.
PROBLEMES = "problemes.json"
EN_SOUFFRANCE = "en-souffrance.json"

GABARIT_PROBLEMES = {
    "quoi": u"Les pannes de l'APPAREIL, non les empêchements du monde. Un "
            u"empêchement du monde est un verrou et va au registre, de ma "
            u"main. Ceci est l'autre chose : ce que j'ai tenté, ce que la "
            u"machine en a fait, et ce que j'attendais. On l'écrit même quand "
            u"on ne sait pas l'expliquer ; c'est la RÉCIDIVE qui parlera.",
    "regle": u"Une entrée par friction, datée. On ne referme jamais une "
             u"entrée sans dire ce qui l'a levée.",
    "entrees": [],
}

GABARIT_EN_SOUFFRANCE = {
    "quoi": u"Ce que j'attends de quelqu'un, et ce que quelqu'un attend de "
            u"moi. Le plan compte des PAS ; ceci compte des GENS qui n'ont "
            u"pas répondu, et depuis quand. Ce n'est pas la même chose et "
            u"cela ne se calcule pas.",
    "regle": u"Une ligne par fil ouvert. Le jour où j'ai demandé, non le jour "
             u"où je m'en suis souvenu. Un fil qu'on n'a pas relancé depuis "
             u"trois jours se relance ou se ferme.",
    "j_attends": [],
    "on_attend_de_moi": [],
}


def chemin(qui):
    """Le domicile de cet habitant : chambres/<qui>/, a la racine du depot."""
    return os.path.join(CHAMBRES, qui)


def _arbitre(qui):
    """Son arbitre de zone, ou « mj ». Import TARDIF et enveloppe : `zone`
    relit la porte des agents, et une chambre doit pouvoir s'ouvrir meme si
    la topologie est muette."""
    try:
        from agents import zone
        return zone.arbitre_de(qui) or "mj"
    except Exception:
        return "mj"


def _fiche(qui):
    """La fiche de personnages.json, ou {} — un MJ n'en a pas, et c'est bien."""
    donnees = tables.lire(os.path.join(RACINE, "etat", "personnages.json"), [])
    if isinstance(donnees, dict):
        donnees = donnees.get("personnages") or []
    return next((p for p in donnees
                 if isinstance(p, dict) and p.get("id") == qui), {})


def _voix(fiche):
    """La maniere ecrite AVANT les ajouts doctrinaux universels — meme coupe
    que depeche/brief.py : la voix seedee est la sienne, pas le manuel de
    conduite qu'on a colle a tout le monde."""
    texte = str((fiche or {}).get("maniere") or "").strip()
    marqueurs = (
        " Se debrouille seul", " Se débrouille seul", " Competent :",
        " Compétent :", " OUVRE PAR :", " DEUXIEME PHRASE",
        " REPRIS,", " AUCUNE ",
    )
    coupures = [texte.find(m) for m in marqueurs if texte.find(m) >= 0]
    if coupures:
        texte = texte[:min(coupures)].strip()
    return texte


def _seed(qui):
    """Le gabarit du premier claude.md.

    IL N'AVAIT JAMAIS SERVI. La seule chambre vivante — celle du mestre — a ete
    posee a la main ; le gabarit, lui, rendait `- devoue` `- meticuleux`
    `- craintif`, c'est-a-dire les traits bruts de personnages.json, qui sont
    des etiquettes sans accents ecrites PAR NOUS SUR lui. Personne n'ecrit
    « devoue » de sa propre main dans son propre cahier. Un habitant qui
    naissait heritait donc d'une liste de mots la ou le mestre a cinq regles a
    la premiere personne.

    Deux corrections, et pas une de plus — on donne la FORME, jamais le fond :
      * les etiquettes rentrent dans une phrase, nommees pour ce qu'elles sont
        (ce que les autres disent, avant qu'il ait ecrit quoi que ce soit) ;
      * le cahier montre comment on l'amende, parce que c'est la seule chose
        qu'il ne peut pas deviner. La section datee est l'invention du mestre :
        sa dérive s'est faite en AJOUTANT sous un titre de jour, sans jamais
        raturer le seme — et c'est ce qui a produit du conditionnel par
        interlocuteur plutot qu'un remplacement.
    """
    fiche = _fiche(qui)
    nom = fiche.get("nom") or qui
    lignes = [u"# Ma manière — %s" % nom, u"", ENTETE, u""]
    dits = [t for t in (fiche.get("traits") or []) if t]
    voix = _voix(fiche)
    if dits or voix:
        lignes.append(u"Ce cahier s'ouvre le jour où l'on m'a donné une "
                      u"chambre. Je n'y ai encore rien écrit : ce qui suit "
                      u"est ce qu'on disait de moi, et c'est à moi d'en faire "
                      u"quelque chose ou de le démentir.")
        lignes.append(u"")
        if dits:
            lignes.append(u"- On me dit %s." % _enumerer(dits))
        if voix:
            lignes.append(u"- %s" % voix)
    else:
        lignes.append(u"Ce cahier s'ouvre vide — on ne disait rien de moi. "
                      u"Ma manière s'écrira ici, journée après journée.")
    lignes += [
        u"",
        u"## Comment j'amende ce cahier",
        u"",
        u"Je n'efface pas ce qui est au-dessus : j'ouvre dessous un titre au "
        u"jour où ma journée m'a contredit, et j'y écris la règle neuve avec "
        u"ce qui me l'a apprise. Une règle sans le fait qui l'a faite ne tient "
        u"pas trois lunes.",
        u"",
    ]
    return u"\n".join(lignes)


def _enumerer(mots):
    """« a, b et c » — une liste de mots dans une phrase, pas des puces."""
    mots = [str(m) for m in mots]
    if len(mots) == 1:
        return mots[0]
    return u"%s et %s" % (u", ".join(mots[:-1]), mots[-1])


def ouvrir(qui):
    """Cree l'arborescence SI ABSENTE et rend le chemin de la chambre.

    Le claude.md est seede une fois depuis la fiche ; s'il existe deja, on
    n'y touche JAMAIS — c'est sa main. Idempotent : rouvrir une chambre
    vivante ne change rien.
    """
    dossier = chemin(qui)
    for d in DOSSIERS:
        os.makedirs(os.path.join(dossier, d), exist_ok=True)
    cahier = os.path.join(dossier, "claude.md")
    if not os.path.exists(cahier):
        with io.open(cahier, "w", encoding="utf-8", newline="\n") as f:
            f.write(_seed(qui))
    for nom, gabarit in ((PROBLEMES, GABARIT_PROBLEMES),
                         (EN_SOUFFRANCE, GABARIT_EN_SOUFFRANCE)):
        fichier = os.path.join(dossier, nom)
        if os.path.exists(fichier):
            continue
        with io.open(fichier, "w", encoding="utf-8",
                     newline="\n") as f:
            f.write(json.dumps(gabarit, ensure_ascii=False, indent=1)
                    + "\n")
    # SON AFFAIRE A LUI, vide. Meme regle que le claude.md : semee une fois,
    # jamais retouchee — si le fichier existe, c'est sa main.
    from agents import chambre_affaire
    fiche = _fiche(qui)
    volume = os.path.join(dossier, "books", "affaire-%s.json" % qui)
    if not os.path.exists(volume):
        with io.open(volume, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(
                chambre_affaire.gabarit(
                    qui, fiche.get("nom") or qui,
                    # C'EST `titre` QUE PORTENT LES FICHES : 119 sur 119,
                    # et ni `office` ni `charge` n'existent. Sans ca, les
                    # 144 volumes seraient sous-titres « ce dont je réponds »
                    # — un gabarit qui ne nomme personne.
                    fiche.get("titre") or fiche.get("office"),
                    # SON ARBITRE, pour que les commandes de la prise en main
                    # soient copiables telles quelles. Import tardif : zone
                    # relit cette porte.
                    _arbitre(qui), os.path.relpath(dossier, RACINE)),
                ensure_ascii=False, indent=1) + "\n")
    return dossier


def _cahier(qui, nom, defaut):
    """Lecture tolerante d'un des deux cahiers de la chambre.

    Tolerante parce qu'une chambre posee a la main avant cette regle n'en
    a pas, et parce qu'un habitant a le droit d'avoir casse son propre
    JSON : sa chambre est a lui. On rend le gabarit vide plutot que de
    lever — rien ici ne fait foi, donc rien ici ne doit faire echouer un
    reveil.
    """
    fichier = os.path.join(chemin(qui), nom)
    if not os.path.exists(fichier):
        return dict(defaut)
    try:
        with io.open(fichier, encoding="utf-8") as f:
            d = json.load(f)
    except (ValueError, OSError):
        return dict(defaut)
    return d if isinstance(d, dict) else dict(defaut)


def problemes(qui):
    """Ce que la machine lui a fait — pour qu'un reveil le lui remette
    sous les yeux. Une panne qu'on ne relit pas se refait."""
    return _cahier(qui, PROBLEMES, GABARIT_PROBLEMES)


def en_souffrance(qui):
    """Ses fils ouverts. Meme lecon que les billets : ca se sert EN
    PERCEPT (« tu attends Alarra Rosby depuis deux jours »), jamais en
    invitation a ouvrir un fichier — mesure deux fois sur deux qu'il ne
    l'ouvre pas sous la pression de l'elan."""
    return _cahier(qui, EN_SOUFFRANCE, GABARIT_EN_SOUFFRANCE)


def existe(qui):
    """A-t-il une chambre ? C'est LE filtre de la mecanique de salle.

    Ce qui se dit dans une piece n'est recopie QUE chez ceux qui en ont une, et
    deux co-presents n'ouvrent une relation que s'ils en ont une tous les deux.
    Sans ce predicat, un conseil de treize presents ecrivait treize copies de
    chaque replique et ouvrait cent cinquante-six dossiers ; avec lui, la charge
    grandit exactement au rythme ou l'on ouvre des chambres — et ouvrir une
    chambre devient un geste qui a un effet.
    """
    return os.path.isdir(chemin(qui))


def canal(a, b, creer=True):
    """Le chemin canonique du discussion.json de la paire — et il n'y en a
    QU'UN : chez le premier des deux dans l'ordre lexical, sous
    relations/<autre>/. L'autre y accede par ce meme chemin.

    Cree les deux relations/<autre>/ (chacun a son cote : sa fiche sur
    l'autre, son curseur .lu). Tolerance de migration : si le fichier
    canonique n'existe pas mais que la paire a deja un discussion.json chez
    le second (les chambres posees a la main avant cette regle), c'est LUI
    qu'on rend — un canal ne se coupe pas en deux fichiers. La migration
    douce (chantier, pas 7) le ramenera au canonique.
    """
    premier, second = sorted((a, b))
    cote_premier = os.path.join(chemin(premier), "relations", second)
    cote_second = os.path.join(chemin(second), "relations", premier)
    # `creer=False` POUR LE CHEMIN DE LECTURE. `non_lus` appelle cette fonction
    # une fois par relation, et elle posait deux mkdir a chaque appel : une
    # ECRITURE sur un chemin qui ne fait que lire. Mesure sur un parc jouet de
    # 100 habitants (9900 relations) : 2,2 s pour ouvrir le parc contre 19 ms
    # pour un reveil. C'est peu, mais un reveil n'a aucune raison de creer quoi
    # que ce soit — et un disque en lecture seule le lui rendrait bien.
    if creer:
        os.makedirs(cote_premier, exist_ok=True)
        os.makedirs(cote_second, exist_ok=True)
    canonique = os.path.join(cote_premier, "discussion.json")
    herite = os.path.join(cote_second, "discussion.json")
    if not os.path.exists(canonique) and os.path.exists(herite):
        return herite
    return canonique


def _entrees(fichier):
    """Les entrees d'un canal. ABSENT rend [] ; ABIME plante, et c'est voulu.

    Un canal qui ne se lit pas est une correspondance en danger, pas une
    correspondance vide : le rendre vide ici ferait ecrire par-dessus au
    premier billet suivant. La porte tient cette semantique (noyau/tables.py
    points 1 et 2) — on ne la reecrit pas a la main."""
    if not os.path.exists(fichier):
        return []
    d = tables.lire(fichier, {})
    return d.get("entrees") or [] if isinstance(d, dict) else []


def verser_histoire(a, b, entrees):
    """Verse de l'HISTOIRE en tete du canal de la paire, et marque tout lu
    des deux cotes. Le format du canal n'appartient qu'a ce module.

    C'est le geste de la migration (habitant.md pas 7) : de la memoire
    ancienne, pas des billets neufs — sans les curseurs a tout-lu, chaque
    canal migre deverserait ses percepts au prochain reveil des deux.
    """
    fichier = canal(a, b)
    existantes = _entrees(fichier)
    total = entrees + existantes
    # ATOMIQUE par la porte. C'est le SECOND ecrivain du meme fichier que
    # billet.deposer(), et il tronquait de la meme facon : c'est cette troncature
    # qui fabrique le JSON a moitie ecrit qu'un lecteur simultane ramasse.
    # Corriger un seul des deux ecrivains n'aurait ferme que la moitie de la
    # fenetre — une garde posee d'un seul cote d'une porte a deux battants.
    tables.ecrire(fichier, {"canal": sorted((a, b)), "entrees": total},
                  indent=1)
    for qui, autre in ((a, b), (b, a)):
        with io.open(_curseur(qui, autre), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(u"%d" % len(total))
    return len(total)


def _curseur(qui, autre):
    """Le fichier .lu de SON cote : combien d'entrees du canal il a deja
    vues. Un entier nu — le plus simple qui tienne."""
    return os.path.join(chemin(qui), "relations", autre, ".lu")


def non_lus(qui):
    """Les entrees de ses canaux adressees a lui et posterieures a son
    dernier reveil — ce que le brief injecte en percept (« Untel t'a
    ecrit : "…" », jamais une invitation a ouvrir un fichier).

    Rend [{avec, de, date, heure, texte}], dans l'ordre des canaux puis des
    entrees. Ne bouge PAS le curseur : c'est `marquer_lus` qui grave le
    reveil, une fois le brief servi.
    """
    base = os.path.join(chemin(qui), "relations")
    if not os.path.isdir(base):
        return []
    nouveaux = []
    for autre in sorted(os.listdir(base)):
        if not os.path.isdir(os.path.join(base, autre)):
            continue
        entrees = _entrees(canal(qui, autre, creer=False))
        lu = 0
        c = _curseur(qui, autre)
        if os.path.exists(c):
            try:
                with io.open(c, encoding="utf-8") as f:
                    lu = int(f.read().strip() or 0)
            except (ValueError, OSError):
                lu = 0
        for e in entrees[lu:]:
            if e.get("de") != qui:
                nouveaux.append({"avec": autre, "de": e.get("de"),
                                 "date": e.get("date"),
                                 "heure": e.get("heure"),
                                 "texte": e.get("texte")})
    return nouveaux


def marquer_lu(qui, autre):
    """Avance le curseur de QUI sur son canal avec AUTRE, et lui seul — pour
    un echange vecu en direct (verbe en call, mot porte par un reveil de
    zone) : re-servir ces entrees en percept au prochain reveil serait du
    double. Les autres canaux ne bougent pas."""
    n = len(_entrees(canal(qui, autre, creer=False)))
    c = _curseur(qui, autre)
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with io.open(c, "w", encoding="utf-8", newline="\n") as f:
        f.write(u"%d" % n)


def marquer_lus(qui):
    """Avance tous ses curseurs a la fin des canaux : son reveil a tout vu.
    A appeler quand le brief est parti — pas avant, pour qu'un lancement
    qui echoue ne mange pas les billets."""
    base = os.path.join(chemin(qui), "relations")
    if not os.path.isdir(base):
        return
    for autre in sorted(os.listdir(base)):
        if not os.path.isdir(os.path.join(base, autre)):
            continue
        n = len(_entrees(canal(qui, autre, creer=False)))
        with io.open(_curseur(qui, autre), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(u"%d" % n)
