# -*- coding: utf-8 -*-
"""LECTURE — le graphe du plan lu depuis les cahiers, et rien decide.

CE QUE CE MODULE POSSEDE : les normalisations de texte (nu, sans_emoji), la
lecture du genre et des numeros, les deux casiers M/O (grand plan / Nera), et
charger() qui derive le graphe complet depuis etat/books.json.
"""
import os
import re
import sys
import unicodedata

import bibliotheque

# Deux etages de plus qu'a la racine : scripts/plan/couverture/ (voir scripts/CLAUDE.md).
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
LIVRES = os.path.join(RACINE, "etat", "books.json")

GENRES = [(u"états? cibles?", "etat"), (u"verrous?", "verrou"), (u"clefs?", "clef"),
          (u"actions?", "action"), (u"moyens?", "moyen"), (u"offices?", "office")]
NOM_GENRE = {"etat": u"🎯", "verrou": u"🔒", "clef": u"🗝️", "action": u"⚔️",
             "moyen": u"🔨", "office": u"🪶", "affaire": u"🏰"}

# Les liens qu'une main pose, et qu'on ne touche donc jamais.
ECRITS = {u"découpe", u"découpée par", u"contredit", u"remplace",
          u"remplacée par", u"exclut"}
# Ce qu'on trouvait avant le typage, et ce que ça devient.
VIEUX = {u"affaire mère": u"découpée par", u"affaire fille": u"découpe",
         u"mère": u"découpée par", u"fille": u"découpe"}


def nu(t):
    s = u"" if t is None else unicode(t) if sys.version_info[0] == 2 else str(t)
    s = s.replace(u"**", u"")
    s = u"".join(c for c in s if c not in u"　└")
    return u" ".join(s.split())


def sans_emoji(s):
    return u" ".join(u"".join(c for c in nu(s)
                              if unicodedata.category(c) != "So" and c != u"️").split())


def genre_de(titre):
    """LE GENRE SE LIT SUR LA TÊTE DU TITRE, PAS DANS SA PROSE.

    On cherchait le mot n'importe où dans la ligne, et l'ordre des GENRES
    tranchait : la table « 🗝️ LES CLEFS — par quel mécanisme ON LÈVE UN VERROU »
    d'un cahier était donc lue comme une table de VERROUS, parce que « verrou »
    apparaît dans sa glose et que les verrous passent avant les clefs. Cinq
    clefs comptées en verrous, dans `charger()` comme partout ailleurs — d'où
    cinq « collisions de genre » qui n'en étaient pas.

    Une glose qui explique à quoi sert la chose nomme forcément le rang du
    dessus : c'est même le propre d'une bonne glose. On ne regarde donc que ce
    qui précède le tiret, et l'on ne retombe sur la ligne entière que si cette
    tête ne dit rien — un titre nu comme « 🗝️ Clefs » n'a pas de tiret."""
    entier = sans_emoji(titre).lower()
    tete = re.split(u"[—–-]", entier)[0].strip() or entier
    for t in (tete, entier):
        for motif, g in GENRES:
            if re.search(motif, t):
                return g
    return None


NUM = re.compile(r"\b(\d{3,6})\b")
ADRESSE = re.compile(r"^(\d{3,6})\b")
MO = re.compile(r"\b([MO]\d{2,3})\b")


def numero_de(texte):
    """L'adresse d'une ligne, seulement si elle commence la premiere cellule.

    Les autres nombres de la cellule sont de la prose. En particulier,
    ``— LIGNE MORTE (doublon de 22050)`` conserve son histoire sans redevenir
    une seconde pièce 22050 pour le graphe.
    """
    return ADRESSE.match(nu(texte))

# ── DEUX REGISTRES M/O, ET LEURS NUMÉROS SE TÉLESCOPENT ──────────────────────
# Le grand plan et la Néra tiennent chacun le leur, et ils ne se sont pas
# concertés : M01 vaut « Les voiles du Gosier » d'un côté et « La porte de la
# Gadoue » de l'autre, M02 à M08 et O01 de même — NEUF numéros sur les neuf que
# la Néra possède. Versés dans un seul dictionnaire, le second lu écrasait le
# premier : `inventaire["O01"]` rendait « Le chantier » de Hann Bourbe, si bien
# que « ce qu'on s'arrache » attribuait au chantier de la Néra les vingt-huit
# actions du castellan de Peyredragon, et rangeait sous un même moyen des
# affaires qui n'ont rien à voir ensemble. Pire : la même page affichait, deux
# sections plus bas, « O01 Castellan de Peyredragon » — parce que `section_charge`
# lit `plan-offices` directement. Deux chiffres justes, deux noms, un seul
# numéro : c'est le genre de contradiction qu'on relit trois fois sans la voir.
#
# LE PRÉFIXE EST UNE CLEF, JAMAIS UNE ÉCRITURE. On ne renumérote pas la Néra —
# ses cahiers restent mot pour mot ce qu'ils sont, et personne n'a à taper
# « N:M01 » nulle part. C'est le CHARGEUR qui range les deux registres dans deux
# casiers, et `etiquette()` qui rend le numéro à sa forme lisible en disant de
# quel registre il sort.
NERA = u"N:"
EST_MO = re.compile(r"^(?:N:)?[MO]\d{2,3}$")
# Un en-tête de registre M/O commence par un numéro. « L'emploi des moyens »,
# dont la première colonne s'appelle « Marque » et la seconde « Sa nature », est
# une TROISIÈME source qui s'invitait dans l'inventaire par son seul titre : elle
# y posait M02 = « GARDE » et M05 = « LES DEUX ». Elle ne faisait pas de dégât
# visible — `plan-moyens`, lu après elle, la recouvrait — mais un inventaire qui
# ne doit sa justesse qu'à l'ordre des livres dans le fichier n'est pas tenu.
# Il se lit sur `nu()` et NON sur `sans_emoji()` : le degré « ° » est un symbole
# au sens d'Unicode, donc `sans_emoji` l'efface — « 🧰 N° » devenait « N », et
# le test tombait sur les trois registres qu'il devait laisser passer.
TETE_NUM = re.compile(u"n\\s*°", re.I)
# L'IDIOME DE LA MAISON POUR « RIEN ». Un tiret seul dans une colonne ne dit pas
# qu'on y a mal écrit : il dit qu'il n'y a rien à y écrire, et c'est ainsi qu'on
# l'écrit partout ici. Compté comme « moyen nommé en clair », il produisait
# vingt-deux faux défauts de couverture — et un détecteur qui crie sur l'idiome
# du dépôt est un détecteur qu'on apprend à ne plus lire.
RIEN = re.compile(u"^[\\s—–\\-·.*]*$")


def registre_de(bid):
    """Le casier M/O d'un volume : la Néra, ou le grand plan. Sur l'IDENTIFIANT,
    comme partout ici — c'est la seule chose qui ne mente pas."""
    return NERA if str(bid or u"").startswith("nera") else u""


def etiquette(m, inventaire):
    """« M01 (Néra) La porte de la Gadoue » — le numéro tel qu'il est écrit au
    cahier, son registre quand ce n'est pas celui de la reine, et son nom. Le
    préfixe de clef ne sort jamais tel quel : il n'appartient pas à la fiction."""
    n, reg = (m[len(NERA):], u" (Néra)") if m.startswith(NERA) else (m, u"")
    return n + reg + u" " + inventaire.get(m, u"—")


def col(cols, motif):
    for i, c in enumerate(cols):
        if re.search(motif, sans_emoji(c), re.I):
            return i
    return None


# ─────────────────────────────────────────────── lire tout le graphe
def charger(livres=None):
    """Lit un ensemble de volumes et en derive le graphe.

    Sans argument, conserve le comportement historique et lit tout
    ``etat/books.json``. Un appelant qui connait deja l'etagere visible d'un
    siege peut fournir cette liste : le parseur reste unique, mais aucun livre
    d'une autre maison n'entre alors dans ses index ni dans ses collisions.
    La liste fournie n'est jamais modifiee sur le disque.
    """
    if livres is None:
        livres = bibliotheque.charger(os.path.join(RACINE, "etat"))
    pieces = {}          # numero -> {genre, nom, affaire, vers[], moyens[], office, dep[], etat, ou}
    inventaire = {}      # M01 / O03 -> nom
    affaires = []        # les livres qui sont des affaires

    for b in livres:
        tables = b.get("tables") or [{"titre": b.get("titre"), "colonnes": b.get("colonnes"),
                                      "lignes": b.get("lignes")}]
        # UN CAHIER EST UN CAHIER OÙ QUE SOIT SON OUVERTURE. On ne regardait que
        # la PREMIÈRE table, et trois volumes qui posent « 📌 Où en est cette
        # affaire » avant leur ouverture n'étaient donc pas des affaires du tout :
        # ni dans la liste, ni dans les comptes, et surtout SANS TENANT — leur
        # `tenu_par` n'était jamais lu. « Commandement et chaîne d'ordres »,
        # tenu par LA REINE, figurait ainsi parmi les cahiers que personne ne
        # porte, et l'on s'apprêtait à le lui donner une seconde fois. Les deux
        # autres sont à ser Steffon Darklyn.
        #
        # La position d'une table est une commodité de lecture, jamais une
        # déclaration : mettre l'état d'avancement en tête est même la bonne
        # idée. Le détecteur, lui, cherche l'ouverture où elle est.
        # LES BORNES DE MOT SONT OBLIGATOIRES. Sans elles, « ouverture » se
        # trouve A L'INTERIEUR de « La c-ouverture de bois » — un memento de
        # Marlo, depourvu de clef `tables`, promu affaire, et `refaire()`
        # mourait dessus sur un KeyError. Les quatre registres derives du plan
        # ont cesse d'etre regeneres ce jour-la, sans que rien ne le dise.
        est_affaire = any(re.search(r"\bouverture\b", sans_emoji(t.get("titre") or u""), re.I)
                          for t in tables)
        if est_affaire:
            affaires.append(b)
        ns = registre_de(b.get("id"))      # le casier M/O de ce volume
        for t in tables:
            g = genre_de(t.get("titre") or u"") or genre_de(b.get("titre") or u"")
            if not g:
                continue
            cols = t.get("colonnes") or []
            i_num, i_nom = 0, 1
            i_vers = col(cols, u"sert|bloque|ouvre|réalise|realise")
            # ── DEUX COLONNES LÀ OÙ IL N'Y EN AVAIT QU'UNE ───────────────────
            # « 🧰 Moyens » faisait deux métiers : porter les numéros M/O du
            # registre, et dire en mots avec quoi on travaille. Le détecteur
            # « nommé en clair » accusait donc 305 cellules pour douze fautes
            # réelles, et un défaut qui crie trois cents fois ne se lit plus.
            # Depuis `scinder_moyens.py`, la prose vit dans « 🔧 Avec quoi » et
            # les moyens ne portent QUE des numéros — le détecteur retrouve son
            # sens sans changer d'une ligne : une cellule de moyens sans numéro
            # est, désormais, vraiment une faute.
            # L'EN-TÊTE SE LIT ANCRÉ. `col(cols, u"moyens")` prendrait la
            # première colonne dont le nom CONTIENT le mot ; le jour où l'on
            # ajoutera « Moyens rendus » ou « Moyens engagés », l'index
            # basculerait en silence et le détecteur mesurerait autre chose.
            # « 🔧 Avec quoi » ne risque rien — elle ne porte pas le mot — et
            # c'est précisément ce qu'il faut garder vrai.
            i_moy, i_off = col(cols, u"^moyens\\b"), col(cols, u"office")
            # LA COLONNE D'ÉTAT N'A PAS LE MÊME NOM PARTOUT, et l'oublier tuait un
            # détecteur en silence : la retenue d'une clef s'appelle « ⚖️ Retenue »
            # aux registres et « ⚖️ Décision » dans les cahiers. Le motif ne
            # connaissait que le premier — donc, depuis que le plan vit dans les
            # cahiers, `p["etat"]` restait vide pour LES 265 CLEFS, et « clef
            # retenue qu'aucune action ne réalise » ne pouvait plus jamais se
            # déclencher. Un détecteur qui ne trouve rien parce qu'il ne lit rien
            # ne se distingue pas d'un plan sain : c'est la pire panne possible.
            i_dep = col(cols, u"dépend|depend")
            # ⛔ EXCLUT — L'INCOMPATIBILITÉ EST UN LIEN, PAS UNE PHRASE.
            #
            # La colonne des clefs s'appelle « 💰 Ce qu'elle coûte ET CE QU'ELLE
            # FERME » depuis le début. Mesure du 2e de la 4e lune : sur les
            # quatre-vingt-quatre options des trente-huit fourches ouvertes,
            # QUATRE-VINGT-QUATRE portent un prix écrit et ZÉRO dit ce qu'elle
            # ferme. Ce n'est pas de la négligence — on ne peut pas écrire une
            # relation dans une cellule de prose et espérer que quoi que ce soit
            # la lise. Celui qui écrivait « cela ferme la voie du fleuve » avait
            # fait son travail ; rien ne l'entendait.
            #
            # Elle porte des numéros, comme `⛓️ Dépend de`, et elle est
            # RÉCIPROQUE : on l'écrit d'un côté, l'autre se refait tout seul.
            # Sans elle, une serrure à trois clefs retenues est une devinette —
            # trois mécanismes concurrents, ou trois compléments qu'on veut tous
            # les trois ? Avec elle, une fourche est déclarée.
            i_exclut = col(cols, u"exclut|incompatible")
            i_etat = col(cols, u"^état$|^etat$|où ça en est|ou ca en est"
                               u"|décision|decision|^retenue$")
            # La colonne « Jour du » que docs/decoupage.md reclame : quand
            # elle existe, l'echeance cesse d'etre devinee dans du texte
            # libre. Absente, rien ne change — les cahiers sans colonne
            # continuent d'etre lus au motif, comme avant.
            i_jour = col(cols, u"jour dû|jour du")
            i_preuve = col(cols, u"^(?:la )?preuve(?: attendue)?$")
            i_jour_fait = col(cols, u"jour fait")
            i_aff = col(cols, u"affaire")
            # Un vrai registre M/O a un numéro en première colonne. Sans ce
            # test, toute table dont le titre porte le mot « moyens » alimente
            # l'inventaire — voir TETE_NUM.
            est_registre_mo = g in ("moyen", "office") and bool(cols) \
                and bool(TETE_NUM.search(nu(cols[0])))
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in (l if isinstance(l, list) else l.get("cellules") or [])]
                if len(c) < 2 or not c[i_num] or not c[i_nom]:
                    continue
                if g in ("moyen", "office"):
                    m = MO.search(c[i_num]) if est_registre_mo else None
                    if m:
                        inventaire[ns + m.group(1)] = c[i_nom]
                    continue
                m = numero_de(c[i_num])
                if not m:
                    continue
                n = m.group(1)
                aff = c[i_aff] if (i_aff is not None and i_aff < len(c) and c[i_aff]) \
                    else (nu(b.get("titre")) if est_affaire else u"")
                p = pieces.setdefault(n, {"genre": g, "nom": c[i_nom], "affaire": aff,
                                          "vers": [], "moyens": [], "office": u"",
                                          "dep": [], "exclut": [], "etat": u""})
                # D'OÙ VIENT CETTE PIÈCE : d'un cahier de travail, ou seulement
                # d'un registre par type ? Les deux plans se recouvrent mal, et
                # la question n'est pas théorique — une action de cahier qui
                # désigne une clef que seul un registre connaît tient debout
                # ICI et s'écroulerait si l'on ne lisait que les cahiers, ce que
                # fait déjà l'écran.
                # LA PROVENANCE SE LIT SUR L'IDENTIFIANT, PAS SUR LA FORME DU
                # VOLUME. On la déduisait de la présence d'une table
                # « Ouverture » : trois cahiers qui n'en ont pas encore —
                # `affaire-commandement-chaine-ordres`, `affaire-repli-si-
                # entree-echoue`, `affaire-surete-personne-reine` — passaient
                # donc pour des pièces de registre. 84 sur 159. Les effacer au
                # nom d'une migration aurait détruit trois affaires entières.
                # Le cahier se reconnait par sa forme, pas par le dialecte de
                # son identifiant. Une autre maison peut employer les memes
                # tables sans adopter les prefixes historiques de Peyredragon.
                est_cahier = est_affaire
                if est_cahier:
                    p["cahier"] = True
                    source = {"volume_id": b.get("id"), "table": t.get("titre"),
                              "genre": g, "nom": c[i_nom]}
                    if source not in p.setdefault("cahier_sources", []):
                        p["cahier_sources"].append(source)
                    # ET LE DERNIER MOT SUR SON NOM. C'est la même faute que
                    # celle du bloc suivant, une case plus loin, et elle a coûté
                    # plus cher : le nom se posait au PREMIER livre lu
                    # (`setdefault`), et les six registres sont écrits avant les
                    # cahiers dans `books.json`. Pour les 96 pièces que les deux
                    # plans portent, c'était donc TOUJOURS le nom du registre qui
                    # s'affichait — ici comme dans `etat_du_plan.py`.
                    # Le Sanglier a renommé l'état 23000 dans son cahier (« Donjon
                    # ouvert » → « Le Donjon a changé de main sans combat dans les
                    # murs », parce que toute l'affaire tient à ce qu'on ne
                    # l'ouvre pas mais qu'on le déverrouille) : sa propre liste de
                    # trous lui a resservi l'ancien nom le matin même. Un peu plus
                    # et il partait travailler contre un objectif qui n'existe
                    # plus. Dix des 96 divergent ainsi sur le nom.
                    # LE GENRE N'EST PAS TOUCHÉ ICI, et c'est délibéré : 44001 est
                    # une action au registre et un verrou au cahier. Ce n'est pas
                    # un nom périmé, c'est une collision de numéro — elle se
                    # tranche par un homme, pas par une règle de préséance.
                    p["nom"] = c[i_nom]
                # LE CAHIER A LE DERNIER MOT SUR SON PROPRE NUMÉRO. Les
                # pièces sont indexées par numéro à travers TOUS les livres, et
                # le premier lu gagnait : quand un registre par type nommait
                # l'affaire autrement que le cahier qui la porte (« Ralliement
                # de la population » contre « Retournement de l'opinion
                # populaire dans Port-Réal »), la pièce restait attachée à un
                # nom d'affaire qu'aucun cahier ne porte — donc dans le
                # `miennes` de personne, donc ANALYSÉE PAR PERSONNE. 145 pièces
                # sur 1286 étaient dans ce trou, dont les trois actions qui
                # désignent la clef 21020, laquelle n'existe nulle part.
                if aff and (not p["affaire"] or est_affaire):
                    p["affaire"] = aff
                if i_vers is not None and i_vers < len(c):
                    p["vers"] = sorted(set(p["vers"]) | set(NUM.findall(c[i_vers])))
                if i_moy is not None and i_moy < len(c):
                    p["moyens"] = sorted(set(p["moyens"])
                                         | {ns + x for x in MO.findall(c[i_moy])})
                    # cite en clair, sans numero : le lien n'existe pas pour la
                    # machine, et personne ne s'en apercevra jamais a la lecture.
                    # Un « — » n'est pas de ceux-là : voir RIEN.
                    if c[i_moy] and not RIEN.match(c[i_moy]) \
                            and not MO.search(c[i_moy]):
                        p["clair"] = True
                        # LES DEUX FAUTES SE COMPTENT À PART, parce qu'elles ne
                        # se réparent pas de la même main : un moyen sans numéro
                        # se repointe sur le registre M/O, un office sans numéro
                        # se repointe sur un HOMME (`reparer_renvois.py`). Le
                        # libellé du trou reste unique — le changer rendrait
                        # d'un coup les trente-cinq couvertures au diff.
                        p["clair_moyen"] = True
                if i_off is not None and i_off < len(c):
                    # TROIS CAS, PAS DEUX. On confondait « personne ne la porte »
                    # avec « quelqu'un la porte, mais son office n'est pas écrit
                    # par son numéro » — et l'action était alors comptée DEUX
                    # FOIS, sous deux libellés dont le premier était faux : une
                    # action qui nomme Mestre Gerardys a bien quelqu'un pour la
                    # porter. Ce qui manque n'est pas un homme, c'est un numéro.
                    o = MO.findall(c[i_off])
                    if o:
                        p["office"] = ns + o[0]
                    elif re.search(u"sans office|à désigner|a designer|vacant|néant|neant",
                                   c[i_off], re.I):
                        p["office"] = u"SANS OFFICE"
                    elif c[i_off]:
                        p["clair"] = True
                        p["clair_office"] = True
                        p["office"] = u"EN CLAIR"
                if i_dep is not None and i_dep < len(c):
                    p["dep"] = sorted(set(p["dep"]) | set(NUM.findall(c[i_dep])))
                if i_exclut is not None and i_exclut < len(c):
                    p["exclut"] = sorted(set(p.get("exclut") or [])
                                         | set(NUM.findall(c[i_exclut])))
                if i_etat is not None and i_etat < len(c) and c[i_etat]:
                    p["etat"] = c[i_etat]
                if i_jour is not None and i_jour < len(c) and c[i_jour]:
                    p["jour"] = c[i_jour]
                if i_preuve is not None and i_preuve < len(c) and c[i_preuve]:
                    p["preuve"] = c[i_preuve]
                if i_jour_fait is not None and i_jour_fait < len(c) and c[i_jour_fait]:
                    p["jour_fait"] = c[i_jour_fait]
    # LA RÉCIPROQUE SE REFAIT, ELLE NE SE SAISIT PAS. Si A exclut B, B exclut A —
    # l'écrire deux fois, c'est se donner deux occasions de se contredire. Même
    # règle que `sert / servie par` : un lien dérivé ne peut pas mentir.
    for n, p in pieces.items():
        for m in (p.get("exclut") or []):
            q = pieces.get(m)
            if q is not None and n not in (q.get("exclut") or []):
                q["exclut"] = sorted((q.get("exclut") or []) + [n])
    return livres, pieces, inventaire, affaires
