# -*- coding: utf-8 -*-
u"""Scinder « 🧰 Moyens » en deux colonnes : les NUMÉROS d'un côté, la PROSE de
l'autre.

POURQUOI. Cette colonne faisait deux métiers dans la même case. Un métier de
machine — porter les numéros `Mnn`/`Onn` du registre, sans lesquels « ce qu'on
s'arrache » ne peut pas dire quel moyen ni quel office est tiré par plusieurs
affaires. Et un métier d'homme — dire, en mots, avec quoi on fait la chose.
264 cellules sur 593 portaient déjà un numéro et fonctionnaient ; les 305 autres
étaient écrites en clair, et le détecteur « 🔤 office ou moyen nommé en clair »
les accusait TOUTES, alors qu'une douzaine seulement désigne une ressource du
registre. Un défaut qui crie trois cents fois pour douze fautes est un défaut
qu'on apprend à ne plus lire.

CE QU'ON FAIT, trois cas et pas un de plus, décidés CELLULE PAR CELLULE et
inscrits ici en toutes lettres — jamais par une heuristique qui s'exécuterait à
l'aveugle sur un fichier qui a bougé depuis :

  A · un vrai moyen du registre, nommé sans son numéro. On PRÉFIXE le numéro
      sans effacer la prose, exactement comme `reparer_renvois.py` le fait pour
      les offices : « M11 — Les adresses de corbeaux du mestre ». La prose dit
      de quel corbeau et de quel mestre, ce qu'aucun numéro ne dira jamais.
  B · du COÛT déjà écrit dans « 💰 Ce qu'elle coûte », sur la MÊME ligne. Celui-
      là se supprime : il ne se déplace pas, il est déjà ailleurs. Une
      suppression n'est légitime que PROUVÉE redondante — d'où le texte attendu
      inscrit en regard de chaque numéro, et la comparaison avant de toucher.
  C · tout le reste — prose, objet, personne, matière. Déplacé TEL QUEL dans la
      colonne neuve « 🔧 Avec quoi », sans qu'un mot soit réécrit.

ON NE SUPPRIME QUE CE QU'ON A RELU. Les cas B ont été comparés un par un à leur
cellule de coût. Trente-quatre candidats qui en avaient l'air ont été REFUSÉS et
sont partis en C : soit le coût dit autre chose (« un quart d'heure » contre
« ¼ journée » — ce n'est pas la même dépense), soit il ne porte pas l'objet que
les moyens nomment (« une page », « son livre », « le pli », « une hache »),
soit il est vide ou dit « à chiffrer ». En cas d'hésitation, la cellule part en
C : y aller coûte un déplacement, se tromper coûte une information.

IDEMPOTENT PAR CONSTRUCTION, et non par espoir. Après un passage, aucune cellule
de « 🧰 Moyens » n'est plus « en clair » : elle porte un numéro, ou elle est
vide. La boucle ne prend QUE les cellules en clair — un second passage n'en
trouve aucune et ne touche rien. La colonne neuve se cherche par son EN-TÊTE :
elle ne se crée donc qu'une fois.

Usage :
    python scripts/scinder_moyens.py                à blanc — n'écrit rien
    python scripts/scinder_moyens.py --rapport f.md le poser dans un fichier
    python scripts/scinder_moyens.py --vraiment     écrit, après sauvegarde
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
LIVRES = os.path.join(RACINE, "etat", "books.json")

import couverture as C  # noqa: E402  — nu, col, MO, NUM, RIEN, retrait

COL_MOY = u"🧰 Moyens"
COL_AVEC = u"🔧 Avec quoi"

# L'EN-TÊTE DE LA COLONNE NEUVE, EN MOTIF. Ancré, pour la raison qui vaut partout
# ici : un repli par inclusion finit toujours par attraper la mauvaise colonne.
M_AVEC = u"^avec quoi$"
# Et celui de la colonne d'origine, ancré lui aussi — sans quoi « 🔧 Avec quoi »
# ne risque rien, mais la prochaine colonne qu'on ajoutera, si.
M_MOY = u"^moyens\\b"
M_COUT = u"co[uû]te|^prix"

# Ce que `reparer_renvois.py` écrit devant une cellule d'office, et qu'on écrit
# ici devant une cellule de moyens : le numéro, un cadratin, la prose intacte.
SEP = u" — "

# ─────────────────────────────────────────────────────────────────────────────
# A · LES MOYENS DU REGISTRE NOMMÉS EN CLAIR
#
# La table est explicite et se relit : (cahier, pièce) → les numéros à préfixer,
# et LE TEXTE ATTENDU de la cellule. Si le texte a changé depuis — une autre
# session écrit dans `books.json` pendant qu'on calcule —, l'appariement est
# ABANDONNÉ et la cellule retombe en C. On n'apparie jamais au jugé : un faux
# lien ne se voit plus, alors qu'une prose déplacée se relit.
#
# Ce qui a été REFUSÉ ici, et pourquoi — c'est la moitié utile de la table :
#   · « 240 dragons d'or », « Vingt dragons la lune » : `dragons` y est une
#     MONNAIE, pas le moyen M04 « Les dragons ».
#   · « les dragons dont on écrit la règle » (4320) : ils sont le SUJET de la
#     règle qu'on écrit, pas le moyen qui l'écrit. Seul M12 y est retenu.
#   · « une ligne au rôle » (23220) : `rôle` et `hommes` s'y croisent par
#     hasard ; la cellule ne nomme pas M17 « Le rôle des hommes ».
#   · « La ligne des vivres » (21222), « tenu au bourg » (44022), « ses
#     coureurs » (39022, ceux de messire Denys et non ceux de la reine),
#     « Leurs coureurs — je n'en ai pas à moi » (32220) : chaque fois, le mot du
#     registre est là et la chose désignée n'est pas celle du registre.
A = {
    (u"affaire-isolement-du-donjon", u"12022"): (
        [u"M17"],
        u"Le tour du rocher en pas, que je n'ai pas ; le rôle des hommes débarqués"),
    (u"affaire-prise-de-port-real", u"320"): (
        [u"M09", u"M18"],
        u"les nouvelles · l'or du coffre"),
    (u"affaire-prise-de-port-real", u"820"): (
        [u"M18"],
        u"ce que la reine sait du Donjon · les nouvelles"),
    (u"affaire-prise-de-port-real", u"920"): (
        [u"M13", u"M15"],
        u"le bourg · les rendus du siège"),
    (u"affaire-prise-de-port-real", u"1020"): (
        [u"M18"],
        u"les nouvelles"),
    (u"affaire-prise-de-port-real", u"1021"): (
        [u"M01", u"M16"],
        u"les voiles du Gosier · les grèves et les mouillages"),
    (u"affaire-prise-de-port-real", u"1220"): (
        [u"M05", u"M11", u"M12"],
        u"le rouleau de l'an cent cinq · les adresses de corbeaux · le papier et la plume"),
    (u"affaire-proclamation-au-royaume", u"34122"): (
        [u"O04"],
        u"Les coureurs de la reine ; les coques du quai"),
    (u"affaire-vierge-01", u"4020"): (
        [u"M12"],
        u"Papier, plume, et le temps du mestre"),
    (u"affaire-vierge-01", u"4021"): (
        [u"M12"],
        u"Papier, plume, et le registre des offices ouvert devant elle"),
    (u"affaire-vierge-01", u"4121"): (
        [u"M11"],
        u"Les adresses de corbeaux du mestre"),
    (u"affaire-vierge-01", u"4320"): (
        [u"M12"],
        u"Papier, plume, et les dragons dont on écrit la règle"),
    (u"affaire-vierge-01", u"4321"): (
        [u"M16"],
        u"Les grèves et les mouillages, et les hommes de Rulf"),
}

# ─────────────────────────────────────────────────────────────────────────────
# B · LE COÛT ÉCRIT DEUX FOIS — ce qui se supprime
#
# Chacune de ces cellules a été lue en regard de sa voisine « 💰 Ce qu'elle
# coûte », sur la même ligne, et n'y ajoute rien : « Une demi-journée des pieds
# de Marlo Vasse » contre « ½ journée · en jours — les pieds de Marlo Vasse ».
# Le texte attendu est inscrit ; s'il a changé, la cellule retombe en C plutôt
# que de disparaître.
B = {
    (u"affaire-ambassade-nord-val-blancport", u"33121"): (None, u"L'archive, une journée de recherche"),
    (u"affaire-emploi-des-dragons", u"27022"): (None, u"Un quart d'heure par cavalier"),
    (u"affaire-emploi-des-dragons", u"27122"): (None, u"Trois minutes de conseil"),
    (u"affaire-entree-au-donjon", u"23036"): (None, u"Une question, posée devant témoins"),
    (u"affaire-entree-au-donjon", u"23120"): (None, u"Une demi-journée des pieds de Marlo Vasse"),
    (u"affaire-entree-au-donjon", u"23121"): (None, u"Une demi-journée, et une corde nouée"),
    (u"affaire-entree-au-donjon", u"23123"): (None, u"Une décision, dite tout haut"),
    (u"affaire-entree-au-donjon", u"23221"): (None, u"Une journée entière, et douze quarts d'heure"),
    (u"affaire-entree-au-donjon", u"23320"): (None, u"Une heure, le sceau, et deux témoins"),
    (u"affaire-guet-des-osts-verts", u"31027"): (None, u"Une journée par ligne, et mes pieds"),
    (u"affaire-guet-des-osts-verts", u"31124"): (
        None, u"Le compte du guet, qui existe déjà et que personne ne lit"),
    (u"affaire-homme-de-linterieur", u"8024"): (None, u"Une journée, et de quoi payer à boire"),
    (u"affaire-homme-de-linterieur", u"8025"): (None, u"Une demi-journée des pieds de Marlo Vasse"),
    (u"affaire-homme-de-linterieur", u"8026"): (None, u"240 dragons d'or, dont 40 comptant"),
    (u"affaire-homme-de-linterieur", u"8027"): (None, u"Une séance, et le sceau de la reine"),
    (u"affaire-homme-de-linterieur", u"8120"): (
        None, u"Un quart d'heure, et le silence de tous les autres"),
    (u"affaire-homme-de-linterieur", u"8124"): (None, u"Une ligne au rôle par passage"),
    (u"affaire-homme-de-linterieur", u"8126"): (None, u"Un quart d'heure"),
    (u"affaire-homme-de-linterieur", u"8221"): (None, u"Une nuit, deux paires d'yeux"),
    (u"affaire-homme-de-linterieur", u"8320"): (None, u"Le sceau, et deux témoins"),
    (u"affaire-isolement-du-donjon", u"12021"): (
        None, u"Une phrase, et deux hommes qui la relisent"),
    (u"affaire-isolement-du-donjon", u"12223"): (None, u"Une heure tous les huit jours"),
    (u"affaire-jour-dentree", u"11034"): (None, u"Une heure de conseil"),
    (u"affaire-jour-dentree", u"11035"): (None, u"Une heure de conseil"),
    (u"affaire-jour-dentree", u"11120"): (None, u"Une demi-journée par lune"),
    (u"affaire-opinion-populaire-port-real", u"6127"): (None, u"Deux passages payés d'avance"),
    (u"affaire-opinion-populaire-port-real", u"6221"): (None, u"Un scribe, une journée"),
    (u"affaire-proclamation-au-royaume", u"34125"): (None, u"Cinq cavaliers, une journée"),
    (u"affaire-proclamation-au-royaume", u"34126"): (
        None, u"Un passage de la route du sel, qui n'en offre qu'un tous les huit jours"),
    (u"affaire-proclamation-au-royaume", u"34127"): (
        None, u"Deux scribes, huit jours, soixante feuillets et de la cire"),
    (u"affaire-proclamation-au-royaume", u"34220"): (None, u"Trois lecteurs, une journée"),
    (u"affaire-proclamation-au-royaume", u"34221"): (None, u"Trois copies affichées ; trois lecteurs"),
    (u"affaire-protection-du-secret", u"32120"): (
        None, u"Un homme, tous les jours, aux heures de séance"),
    (u"affaire-protection-du-secret", u"32121"): (None, u"Une journée d'un homme, du cuir et du bois"),
    (u"affaire-protection-du-secret", u"32122"): (None, u"Une ligne, et une lecture à voix haute"),
    (u"affaire-protection-du-secret", u"32222"): (None, u"Une ligne par passage"),
    (u"affaire-protection-du-secret", u"32320"): (None, u"Le sceau, deux témoins, une heure"),
    (u"affaire-ralliement-population", u"21320"): (
        None, u"Deux hommes, deux chevaux, un jour de route chacun"),
    (u"affaire-siege-sur-le-trone", u"24034"): (None, u"Un scribe, de la cire, dix-neuf sceaux"),
    (u"affaire-siege-sur-le-trone", u"24045"): (None, u"Une demi-heure"),
    (u"affaire-siege-sur-le-trone", u"24050"): (None, u"Une matinée, et douze femmes"),
    (u"affaire-siege-sur-le-trone", u"24180"): (None, u"Un quart d'heure par lune"),
    (u"affaire-transmission-des-ordres", u"41021"): (
        None, u"Un passage entier, et six cerfs à la porteuse"),
    (u"affaire-transmission-des-ordres", u"41027"): (
        None, u"Une quille qui va au Nord, et deux cages vides"),
    (u"affaire-transmission-des-ordres", u"41029"): (None, u"Six cerfs la journée"),
    (u"affaire-transmission-des-ordres", u"41031"): (None, u"Deux équipes, une nuit d'exercice"),
    (u"affaire-transmission-des-ordres", u"41032"): (None, u"Deux porteurs par fenêtre"),
    (u"affaire-transmission-des-ordres", u"41220"): (None, u"Un passage entier"),
    (u"affaire-veille-des-hypotheses", u"39020"): (None, u"Une soirée"),
    (u"affaire-veille-des-hypotheses", u"39021"): (None, u"Un quart d'heure de séance"),
    (u"affaire-veille-des-hypotheses", u"39022"): (None, u"Une consigne à ses coureurs"),
    (u"affaire-veille-des-hypotheses", u"39023"): (
        None, u"Une demi-journée par semaine dans la ville"),
    (u"affaire-veille-des-hypotheses", u"39024"): (None, u"Trois yeux nommés"),
    (u"affaire-veille-des-hypotheses", u"39030"): (None, u"Une heure par lune"),
    (u"affaire-veille-des-hypotheses", u"39032"): (None, u"Trois lignes"),
    (u"affaire-veille-des-hypotheses", u"39120"): (None, u"Une phrase"),
    (u"affaire-veille-des-hypotheses", u"39220"): (None, u"Une demi-heure par lune"),
}

# ─────────────────────────────────────────────────────────────────────────────
# LES DEUX CELLULES MIXTES — un numéro ET de la prose dans la même case.
# Le numéro reste aux moyens, la prose descend en « Avec quoi ». Elles sont
# nommées une à une parce qu'une règle générale ferait, au second passage, subir
# le même sort aux cellules que le cas A vient d'écrire.
MIXTE = {
    (u"affaire-prise-de-port-real", u"221"): (
        [u"M18"], u"le crédit de l'époux de la reine · M18",
        u"le crédit de l'époux de la reine"),
    (u"affaire-transmission-des-ordres", u"41224"): (
        [u"M03"], u"M03 — la grève et ses trente gosses",
        u"la grève et ses trente gosses"),
}


def cellules(ligne):
    return ligne if isinstance(ligne, list) else (ligne.get("cellules") or [])


def poser(ligne, c):
    u"""Reposer les cellules DANS la ligne, quelle que soit sa forme. Une ligne
    peut être un tableau nu ou `{cellules: […]}` ; on travaille sur une copie, et
    l'oubli du cas « tableau nu » ferait perdre l'écriture en silence."""
    if isinstance(ligne, dict):
        ligne["cellules"] = c
    else:
        ligne[:] = c


def tables_moyens(livres):
    u"""Les tables qui portent une colonne « 🧰 Moyens », et rien d'autre."""
    for b in livres:
        for t in (b.get("tables") or []):
            cols = [C.nu(x) for x in (t.get("colonnes") or [])]
            if C.col(cols, M_MOY) is None:
                continue
            yield b, t


def passer(livres, ecrire=False):
    u"""Le passage complet. Ne touche `livres` que si `ecrire`."""
    rap = {"A": [], "B": [], "C": [], "MIXTE": [], "desapparies": [],
           "colonnes_creees": [], "vides": 0, "rien": 0, "numerotees": 0,
           "lignes": 0}

    for b, t in tables_moyens(livres):
        bid = str(b.get("id") or u"")
        cols = [C.nu(x) for x in (t.get("colonnes") or [])]
        i_moy = C.col(cols, M_MOY)
        i_avec = C.col(cols, M_AVEC)
        i_cout = C.col(cols, M_COUT)

        # LA COLONNE NEUVE SE POSE JUSTE APRÈS LES MOYENS, et non en queue de
        # table : ces deux-là se lisent ensemble, et un registre qu'on lit avec
        # le doigt n'a pas de raison de renvoyer la moitié d'une case à l'autre
        # bout de la ligne. On paie ce confort d'un décalage d'index, calculé
        # ici une fois pour toutes.
        neuve = i_avec is None
        if neuve:
            i_avec = i_moy + 1
            rap["colonnes_creees"].append((bid, C.nu(t.get("titre"))))
            if i_cout is not None and i_cout >= i_avec:
                i_cout += 1
        largeur = len(cols) + (1 if neuve else 0)

        for l in (t.get("lignes") or []):
            c = [x for x in cellules(l)]
            if neuve:
                # toute ligne s'élargit, y compris celle qu'on ne touchera pas :
                # une table dont les lignes n'ont pas le compte des colonnes se
                # décale à l'écran, et `tick.py --verifier` le dit.
                while len(c) < len(cols):
                    c.append(u"")
                c.insert(i_avec, u"")
                if ecrire:
                    poser(l, c)
            while len(c) < largeur:
                c.append(u"")
                if ecrire:
                    poser(l, c)
            if len(c) < 2 or not C.nu(c[0]) or not C.nu(c[1]):
                continue
            m = C.NUM.search(C.nu(c[0]))
            if not m:
                continue
            rap["lignes"] += 1
            num = m.group(1)
            moy = C.nu(c[i_moy])
            cout = C.nu(c[i_cout]) if (i_cout is not None and i_cout < len(c)) else u""
            clef = (bid, num)

            if not moy:
                rap["vides"] += 1
                continue
            if C.RIEN.match(moy):
                rap["rien"] += 1
                continue

            if clef in MIXTE and moy == MIXTE[clef][1]:
                nums, _, prose = MIXTE[clef]
                rap["MIXTE"].append((bid, num, moy, u" · ".join(nums), prose))
                if ecrire:
                    c[i_moy] = u" · ".join(nums)
                    c[i_avec] = prose
                    poser(l, c)
                continue

            if C.MO.search(moy):
                # déjà numérotée : c'est le cas normal, et c'est le cas d'un
                # second passage sur ce que le cas A vient d'écrire.
                rap["numerotees"] += 1
                continue

            # ── la cellule est EN CLAIR : A, B ou C ──────────────────────────
            if clef in A:
                nums, attendu = A[clef]
                if moy == attendu:
                    rap["A"].append((bid, num, moy, u" · ".join(nums)))
                    if ecrire:
                        c[i_moy] = u" · ".join(nums) + SEP + c[i_moy]
                        poser(l, c)
                    continue
                rap["desapparies"].append((bid, num, u"A", attendu, moy))

            elif clef in B:
                attendu = B[clef][1]
                if moy == attendu:
                    # UNE SUPPRESSION NE SE FAIT PAS SUR PAROLE. Même relue à la
                    # main, on redemande au fichier que la voisine de coût soit
                    # là : si elle a été vidée depuis, la prose est la dernière
                    # trace de la dépense et elle part en C.
                    if cout and not C.RIEN.match(cout):
                        rap["B"].append((bid, num, moy, cout))
                        if ecrire:
                            c[i_moy] = u""
                            poser(l, c)
                        continue
                    rap["desapparies"].append(
                        (bid, num, u"B", u"une cellule de coût remplie", cout or u"(vide)"))
                else:
                    rap["desapparies"].append((bid, num, u"B", attendu, moy))

            rap["C"].append((bid, num, moy, cout))
            if ecrire:
                c[i_moy] = u""
                c[i_avec] = moy
                poser(l, c)

        if ecrire and neuve:
            cols_neuves = list(t.get("colonnes") or [])
            cols_neuves.insert(i_avec, COL_AVEC)
            t["colonnes"] = cols_neuves
    return rap


# ─────────────────────────────────────────────── écrire, sous garde
def verser(livres, avant):
    u"""Les trois gardes de `couverture.verser`, dans le même ordre : relecture
    (books.json est partagé avec le MJ qui joue), sauvegarde horodatée,
    remplacement atomique. Le retrait se relit sur le fichier — il est d'UN
    espace ici, et le regonfler rendrait 3,4 Mo de bruit au diff."""
    if io.open(LIVRES, encoding="utf-8").read() != avant:
        sortie(u"\n‼ etat/books.json a changé pendant le calcul — RIEN N'A ÉTÉ "
               u"ÉCRIT.\n  Une autre session y a touché. Relancer.\n")
        return None
    sauve = LIVRES + u".avant-moyens-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(LIVRES, sauve)
    n = C.retrait()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(LIVRES), suffix=".tmp")
    os.close(fd)
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(livres, f, ensure_ascii=False, indent=n)
    os.replace(tmp, LIVRES)
    return sauve


# ─────────────────────────────────────────────── le rapport
_SORTIE = []


def sortie(s):
    _SORTIE.append(s)


def rapport(rap, applique):
    o = []
    o.append(u"# Scinder « 🧰 Moyens » — rapport\n\n")
    o.append(u"%s · %d ligne(s) d'action lue(s)\n\n" % (time.strftime("%Y-%m-%d %H:%M"),
                                                        rap["lignes"]))
    o.append(u"%s\n\n" % (u"**APPLIQUÉ.**" if applique
                          else u"**À BLANC — rien n'a été écrit.**"))
    o.append(u"| cas | cellules |\n|---|---|\n")
    o.append(u"| A · moyen du registre, numéro préfixé | %d |\n" % len(rap["A"]))
    o.append(u"| B · coût redondant, **supprimé** | %d |\n" % len(rap["B"]))
    o.append(u"| C · prose déplacée en « 🔧 Avec quoi » | %d |\n" % len(rap["C"]))
    o.append(u"| mixte · numéro gardé, prose déplacée | %d |\n" % len(rap["MIXTE"]))
    o.append(u"| déjà numérotées, intactes | %d |\n" % rap["numerotees"])
    o.append(u"| « — » (l'idiome pour « rien »), intactes | %d |\n" % rap["rien"])
    o.append(u"| vides, intactes | %d |\n" % rap["vides"])

    o.append(u"\n## A · la table de correspondance\n\n"
             u"| cahier | pièce | numéro | la cellule, gardée telle quelle |\n|---|---|---|---|\n")
    for bid, num, moy, nums in sorted(rap["A"]):
        o.append(u"| `%s` | %s | **%s** | %s |\n" % (bid, num, nums, moy.replace(u"|", u"\\|")))

    o.append(u"\n## Mixtes\n\n| cahier | pièce | reste aux moyens | descend en « Avec quoi » |\n"
             u"|---|---|---|---|\n")
    for bid, num, moy, nums, prose in sorted(rap["MIXTE"]):
        o.append(u"| `%s` | %s | %s | %s |\n" % (bid, num, nums, prose.replace(u"|", u"\\|")))

    o.append(u"\n## B · les suppressions, et leur preuve\n\n"
             u"| pièce | ce qui disparaît de « Moyens » | ce que « 💰 » porte déjà |\n"
             u"|---|---|---|\n")
    for bid, num, moy, cout in sorted(rap["B"]):
        o.append(u"| %s | %s | %s |\n" % (num, moy.replace(u"|", u"\\|"),
                                          cout[:150].replace(u"|", u"\\|")))

    if rap["desapparies"]:
        o.append(u"\n## Désappariés — la table dit une chose, le fichier une autre\n\n"
                 u"Ces cellules ont changé depuis que la décision a été prise ; elles "
                 u"retombent en C, qui ne perd rien.\n\n"
                 u"| cahier | pièce | cas | attendu | trouvé |\n|---|---|---|---|---|\n")
        for bid, num, cas, att, trouve in sorted(rap["desapparies"]):
            o.append(u"| `%s` | %s | %s | %s | %s |\n"
                     % (bid, num, cas, att[:70].replace(u"|", u"\\|"),
                        trouve[:70].replace(u"|", u"\\|")))

    if rap["colonnes_creees"]:
        o.append(u"\n## Colonne « 🔧 Avec quoi » créée dans %d table(s)\n\n"
                 % len(rap["colonnes_creees"]))
        for bid, tt in rap["colonnes_creees"]:
            o.append(u"- `%s` / %s\n" % (bid, tt[:52]))

    o.append(u"\n## C · les %d cellules déplacées telles quelles\n\n"
             u"| cahier | pièce | la prose, mot pour mot |\n|---|---|---|\n" % len(rap["C"]))
    for bid, num, moy, cout in sorted(rap["C"]):
        o.append(u"| `%s` | %s | %s |\n" % (bid, num, moy[:170].replace(u"|", u"\\|")))
    return u"".join(o)


if __name__ == "__main__":
    args = sys.argv[1:]
    vraiment = "--vraiment" in args
    dest = args[args.index("--rapport") + 1] if "--rapport" in args else None

    avant = io.open(LIVRES, encoding="utf-8").read()
    livres = json.loads(avant)
    rap = passer(livres, ecrire=vraiment)
    txt = rapport(rap, vraiment)

    sortie(u"A %d · B %d · C %d · mixtes %d · désappariés %d · colonnes créées %d\n"
           % (len(rap["A"]), len(rap["B"]), len(rap["C"]), len(rap["MIXTE"]),
              len(rap["desapparies"]), len(rap["colonnes_creees"])))
    if vraiment:
        sauve = verser(livres, avant)
        if sauve is None:
            sys.exit(1)
        sortie(u"  sauvegarde : %s\n" % os.path.basename(sauve))
    else:
        sortie(u"--vraiment absent : rien n'a été écrit.\n")

    if dest:
        with io.open(dest, "w", encoding="utf-8") as f:
            f.write(txt)
        sortie(u"rapport : %s\n" % dest)
    out = io.open(sys.stdout.fileno(), "w", encoding="utf-8", errors="replace",
                  closefd=False)
    out.write(u"".join(_SORTIE))
    out.flush()
