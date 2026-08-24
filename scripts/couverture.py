# -*- coding: utf-8 -*-
# La couverture d'une affaire — calculee, jamais saisie.
#
# POURQUOI. Une couverture ecrite a la main ment en trois jours : on ajoute une
# action et l'on oublie de redire, en tete, qu'elle attend une piece d'ailleurs.
# Tout ce qui se DEDUIT du graphe se recalcule donc ici, et l'on ne laisse a la
# plume que ce qu'aucun calcul ne peut trouver : la conclusion, et fermee quand.
#
# LES LIENS SONT TYPES, ET LA MOITIE SE DERIVE.
#   ecrits  : decoupe / decoupee par · contredit · remplace / remplacee par · exclut
#   derives : attend / attendue par · sert / servie par · partage
# Un lien derive ne se saisit jamais : on le refait, il ne peut pas mentir.
#
# Usage :
#     python scripts/couverture.py              toutes les affaires
#     python scripts/couverture.py --affaire "L'entree sans bataille"
#     python scripts/couverture.py --verifier   dit ce qui bougerait, n'ecrit rien
import io, json, os, re, sys, unicodedata

import bibliotheque

# La console Windows est en cp1252 : une fleche ou un embleme dans un
# message de progression tuait le script APRES qu'il eut ecrit une partie
# de son travail. Le rapport ne doit jamais pouvoir faire tomber le calcul.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


# ─────────────────────────────────────────────── ce que chaque renvoi attend
# La chaîne du guide descend : état → verrou → clef → action. Une colonne de
# renvoi attend donc un genre PRÉCIS, et rien d'autre — « ⛔ Bloque » veut un
# état cible, « 🔓 Ouvre » un verrou, « 🗝️ Réalise » une clef. Un état, lui,
# sert un autre état.
ATTENDU = {"etat": "etat", "verrou": "etat", "clef": "verrou", "action": "clef"}
# Le rang de chaque genre dans la descente. Il départage deux fautes qu'on
# confondait, et qui n'ont rien à voir :
#   RACCOURCI       le renvoi monte, mais saute un rang — une action qui
#                   désigne directement un état cible. La chaîne tient, elle est
#                   seulement plus courte que le guide ne la veut. 83 fois sur
#                   ce plan : c'est une manière d'écrire, pas un accident.
#   ERREUR DE GENRE le renvoi ne monte pas : il pointe de côté ou vers le bas —
#                   un verrou dont la colonne « Bloque » porte une action. Là,
#                   quelqu'un s'est trompé de case, et ça ne se lit pas.
RANG = {"etat": 0, "verrou": 1, "clef": 2, "action": 3}

# L'état d'une action, réduit à son premier mot — le reste de la cellule porte
# souvent autre chose (« à faire · j−35 »), et ce n'est pas le sujet ici.
FINI = re.compile(u"^(fait|faite|faits|faites)\\b", re.I)


def tete_ornee(texte):
    """Un signe plante DEVANT le mot (« ✅ faite ») est une troisieme
    orthographe ; le meme signe ailleurs dans la phrase n'est rien du tout. On
    ne regarde donc que la tete, jusqu'a la premiere lettre."""
    for c in nu(texte or u""):
        if c.isalpha():
            return False
        if unicodedata.category(c) == "So":
            return True
    return False


def premier_mot(texte):
    """Le premier mot, sans sa ponctuation. « **FAITE.** ET SI CA CASSE » finit
    une phrase par un point : ce point n'est pas une orthographe de plus, et
    exiger qu'on l'efface pour que le compte tombe juste, ce serait faire plier
    la prose devant le detecteur."""
    t = sans_emoji(texte or u"").strip().lower()
    if not t:
        return u""
    return re.split(u"[ 	·,;(]", t)[0].strip(u".*:-_")


# ─────────────────────────────────────────────── les blocs calculés
def marque(n, pieces):
    p = pieces.get(n)
    return (NOM_GENRE.get(p["genre"], u"") + u" " + n) if p else n


def blocs(nom_affaire, pieces, inventaire):
    miennes = {n: p for n, p in pieces.items() if p["affaire"] == nom_affaire}

    # ⛓️ ce qui pend — les `dépend de` qui traversent, dans les deux sens
    pend = []
    for n, p in sorted(miennes.items()):
        for d in p["dep"]:
            q = pieces.get(d)
            if q and q["affaire"] and q["affaire"] != nom_affaire:
                pend.append([u"⬅ nous attendons", marque(n, pieces), marque(d, pieces), q["affaire"]])
    for n, p in sorted(pieces.items()):
        if p["affaire"] == nom_affaire or not p["affaire"]:
            continue
        for d in p["dep"]:
            if d in miennes:
                pend.append([u"➡ on nous attend", marque(d, pieces), marque(n, pieces), p["affaire"]])

    # 🔨🪶 ce qu'on engage — et qui d'autre le veut
    engage = {}
    for n, p in sorted(miennes.items()):
        for m in p["moyens"] + ([p["office"]] if EST_MO.match(p["office"] or u"") else []):
            engage.setdefault(m, []).append(n)
    autres = {}
    for n, p in pieces.items():
        if p["affaire"] in (nom_affaire, u""):
            continue
        for m in p["moyens"] + ([p["office"]] if EST_MO.match(p["office"] or u"") else []):
            autres.setdefault(m, set()).add(p["affaire"])
    lignes_eng = [[etiquette(m, inventaire),
                   u" · ".join(marque(x, pieces) for x in sorted(v)),
                   u" · ".join(sorted(autres.get(m, []))) or u"—"]
                  for m, v in sorted(engage.items())]

    # 🕳️ les trous — cinq défauts, tous dérivés des relations
    # LE PÉRIMÈTRE EST CELUI DU GRAPHE, PAS CELUI DU CAHIER. On ne cherchait ce
    # qui couvre une pièce que dans SA propre affaire : un état bloqué par un
    # verrou d'une autre affaire était donc déclaré « intention sans plan »,
    # alors que le lien est écrit noir sur blanc. Les affaires se découpent et
    # se servent l'une l'autre — c'est même ce que la table des liens dérivés
    # passe son temps à établir deux blocs plus haut.
    ouvre_par, bloque_par, realise_par = set(), set(), set()
    for n, p in pieces.items():
        if p["genre"] == "clef":
            ouvre_par |= set(p["vers"])
        if p["genre"] == "verrou":
            bloque_par |= set(p["vers"])
        if p["genre"] == "action":
            realise_par |= set(p["vers"])
    trous = [
        (u"⚔️ action que personne ne peut porter — aucun office, aucun nom",
         [n for n, p in miennes.items() if p["genre"] == "action"
          and (not p["office"] or p["office"] == u"SANS OFFICE")]),
        (u"🔒 verrou qu'aucune clef n'ouvre — il est mal nommé",
         [n for n, p in miennes.items() if p["genre"] == "verrou" and n not in ouvre_par]),
        (u"🗝️ clef retenue qu'aucune action ne réalise — une décision sans geste",
         [n for n, p in miennes.items() if p["genre"] == "clef"
          and re.search(u"retenue", p["etat"] or u"", re.I) and n not in realise_par]),
        (u"🎯 état qu'aucun verrou ne bloque — une intention sans plan",
         [n for n, p in miennes.items() if p["genre"] == "etat" and n not in bloque_par]),
        (u"🔤 office ou moyen nommé en clair — écrire son numéro, sans quoi le lien "
         u"n'existe pas pour la machine",
         [n for n, p in miennes.items() if p.get("clair")]),
        (u"⚔️ action dont la chaîne ne remonte à aucun état cible",
         [n for n, p in miennes.items() if p["genre"] == "action" and not remonte(n, pieces)]),
        # ── LA CHAÎNE ROMPUE AU MILIEU ──────────────────────────────────────
        # Les six défauts du dessus disent ce qui manque au BOUT de la chaîne :
        # pas de clef, pas d'action, pas d'office. Ces deux-ci disent autre
        # chose, et c'est plus grave : la chaîne est rompue EN SON MILIEU. Une
        # pièce désigne un numéro qui n'existe nulle part, ou n'en désigne
        # aucun — et le test disqualifiant du guide tombe, mot pour mot : « si
        # la remontée est impossible, l'action n'a pas de raison stratégique
        # démontrée : elle se supprime ou se requalifie ».
        #
        # ON NE RAPPROCHE JAMAIS AU PLUS PROCHE. Trois actions qui désignent la
        # clef 21020, laquelle n'existe pas : renumérotage ? clef supprimée ?
        # doigt glissé depuis 21021 ? Écrire la réponse à leur place, ce serait
        # écrire une FAUSSE raison stratégique, et une fausse raison est pire
        # que pas de raison — elle ne se voit plus. Même règle que le verseur de
        # cahiers : refuser plutôt que deviner.
        (u"⛓️‍💥 référence pendante — le numéro désigné n'existe nulle part dans le plan",
         [n for n, p in miennes.items()
          if any(v not in pieces for v in p["vers"])]),
        # LA RÉFÉRENCE QUI NE TIENT QU'AU REGISTRE. Elle résout — mais seulement
        # parce qu'on lit les deux plans à la fois. L'écran, lui, ne lit que les
        # cahiers : pour lui, ces renvois-là pendent dans le vide, et l'action
        # n'a plus de raison stratégique démontrée. Ce n'est donc pas une faute
        # de saisie, c'est la trace exacte de la question qui reste à trancher :
        # deux plans, ou un seul.
        (u"🪢 référence qui ne tient qu'au registre — la pièce désignée n'est dans "
         u"aucun cahier",
         [n for n, p in miennes.items()
          if any(v in pieces and not pieces[v].get("cahier") for v in p["vers"])]),
        (u"⚔️ action orpheline — elle ne désigne aucune clef, elle n'a jamais rien remonté",
         [n for n, p in miennes.items() if p["genre"] == "action" and not p["vers"]]),
        # Un numéro qui existe, mais du mauvais genre : « ⛔ Bloque » qui porte
        # une action au lieu d'un état cible. La colonne dit ce qu'elle attend ;
        # ce qu'on y a mis dit ce qu'on a cru y mettre.
        (u"🔀 erreur de genre — la colonne attend un rang et porte l'autre : "
         u"le renvoi ne remonte pas",
         [n for n, p in miennes.items()
          if any(v in pieces and RANG.get(pieces[v]["genre"], 9) >= RANG.get(p["genre"], 0)
                 and not (p["genre"] == "etat" and pieces[v]["genre"] == "etat")
                 for v in p["vers"])]),
        (u"↗️ raccourci — le renvoi saute un rang de la chaîne du guide",
         [n for n, p in miennes.items()
          if any(v in pieces and pieces[v]["genre"] != ATTENDU.get(p["genre"])
                 and RANG.get(pieces[v]["genre"], 9) < RANG.get(p["genre"], 0)
                 for v in p["vers"])]),
        # Trente-six actions terminées sous trois orthographes : aucun compte ne
        # peut dire si le plan avance. Ce n'est pas une faute de chaîne, c'est
        # une faute de tenue — et elle se répare d'un mot.
        (u"🏷️ « fait » écrit de plusieurs façons — rien ne peut se compter tant que ça dure",
         [n for n, p in miennes.items()
          if p["genre"] == "action" and FINI.match(premier_mot(p["etat"]) or u"")
          and (premier_mot(p["etat"]) != u"faite" or tete_ornee(p["etat"]))]),
    ]
    lignes_trous = [[t, u" · ".join(marque(x, pieces) for x in sorted(l))]
                    for t, l in trous if l]

    # 🔗 les liens dérivés entre affaires
    liens = set()
    for l in pend:
        liens.add((u"attend" if l[0].startswith(u"⬅") else u"attendue par", l[3],
                   l[1], l[2]))
    for n, p in miennes.items():
        if p["genre"] != "etat":
            continue
        for v in p["vers"]:
            q = pieces.get(v)
            if q and q["affaire"] and q["affaire"] != nom_affaire:
                liens.add((u"sert", q["affaire"], marque(n, pieces), marque(v, pieces)))
    for n, p in pieces.items():
        if p["genre"] != "etat" or p["affaire"] in (nom_affaire, u""):
            continue
        for v in p["vers"]:
            if v in miennes:
                liens.add((u"servie par", p["affaire"], marque(v, pieces), marque(n, pieces)))
    for m, v in engage.items():
        for a in sorted(autres.get(m, [])):
            liens.add((u"partage", a, etiquette(m, inventaire), u""))

    # ⏳ la prochaine échéance : ce qui porte une date, au plus tôt
    ech = sorted((p["etat"], n) for n, p in miennes.items()
                 if p["genre"] == "action" and re.search(r"\d+e\b|avant|le \d", p["etat"] or u""))
    return pend, lignes_eng, lignes_trous, sorted(liens), (ech[0] if ech else None)


def remonte(n, pieces, vu=None):
    """Une action remonte-t-elle jusqu'à un état cible ? action → clef → verrou → état."""
    vu = vu or set()
    if n in vu:
        return False
    vu.add(n)
    p = pieces.get(n)
    if not p:
        return False
    if p["genre"] == "etat":
        return True
    return any(remonte(v, pieces, vu) for v in p["vers"])


# ═══════════════════════════════════════════════ LES REGISTRES DÉRIVÉS
#
# UN SEUL PLAN. Les cahiers d'affaire sont la vérité ; les quatre registres par
# type sont un INDEX, régénéré depuis eux et jamais écrit à la main. La règle du
# guide — « quand l'affaire et le registre se contredisent, c'est le registre qui
# a raison » — supposait un registre tenu ; il ne l'était plus (108 lignes contre
# 1312), et deux copies d'un même plan n'est pas un défaut de propreté : c'est
# une machine à envoyer les hommes contre des fantômes. Voir docs/echiquier.md.
#
# `plan-moyens` ET `plan-offices` N'EN SONT PAS, ET NE LE SERONT JAMAIS. Ce ne
# sont pas des copies : ce sont les SOURCES de l'inventaire M/O. Six moyens et
# dix-sept offices n'existent nulle part ailleurs, et quarante-huit numéros M/O
# sont cités par les actions des cahiers, qui ne les définissent jamais. On ne
# dérive pas d'un vide — les régénérer « par symétrie » n'en laisserait rien.
REGISTRES = {u"plan-etats-cibles": "etat", u"plan-verrous": "verrou",
             u"plan-clefs": "clef", u"plan-actions": "action"}

# ─── QUATRE COLONNES, ET UNE SEULE DE SENS. Pourquoi celles-là.
#
# La forme minimale — numéro, nom, affaire, renvoi — pesait un dixième et TUAIT
# LA RECHERCHE PAR CONTENU : « quelle clef parle des coques » ne rendait plus
# rien, et c'est exactement ce pour quoi on ouvre un index. On garde donc la
# seule colonne qui IDENTIFIE la chose.
#
# Ce qu'on retire — la preuve, le levé-quand, le prix, la dépendance, l'office,
# les moyens, l'avancement, le `📍 Où` — sert à TRAVAILLER, donc appartient au
# cahier. L'index dit où la chose est écrite ; il ne la refait pas.
#
# ET LE VRAI GAIN N'EST PAS LES OCTETS : ce qui reste est ce qui ne bouge
# presque jamais. Un nom et une définition changent rarement — Le Sanglier en a
# corrigé cinq en une nuit, et c'était un événement. Les colonnes qu'on retire
# sont les plus volatiles de toutes : un avancement bouge chaque jour, un office
# à chaque nomination. MOINS L'INDEX PORTE DE CHOSES QUI CHANGENT, MOINS IL A
# D'OCCASIONS DE MENTIR. C'est la même raison qui a fait dériver ces registres,
# poussée d'un cran.
SENS = {"etat": u"✅ Ce qui doit être vrai", "verrou": u"📌 Ce qui est vrai aujourd'hui",
        "clef": u"💡 Le principe", "action": u"📝 Ce qu'on fait"}
NUMERO = {"etat": u"🎯 N°", "verrou": u"🔒 N°", "clef": u"🗝️ N°", "action": u"⚔️ N°"}
NOM = {"etat": u"🏷️ L'état", "verrou": u"🏷️ Le verrou", "clef": u"🏷️ La clef",
       "action": u"🏷️ L'action"}
AFFAIRE = u"🏰 Affaire"


def colonnes_de(genre):
    return [NUMERO[genre], NOM[genre], SENS[genre], AFFAIRE]

# LA TRANSPOSITION SE FAIT PAR EN-TÊTE, JAMAIS PAR RANG : les deux formes n'ont
# pas les colonnes dans le même ordre. Exact d'abord, puis ces alias explicites —
# et rien d'autre. Un repli par inclusion a déjà coûté huit chaînes : `sq("N°")`
# vaut « n », qui est un sous-mot de « ou ca en est », et la colonne d'avancement
# atterrissait en position 0, à la place du numéro.
ALIAS = {u"ce qu'on fait, et ou": u"ce qu'on fait",
         u"ou ca en est": u"etat",
         u"ce qu'elle coute et ce qu'elle ferme": u"le prix",
         u"la preuve attendue": u"la preuve",
         u"retenue": u"decision"}

# CE QUI NE DESCEND PAS, ET CE N'EST PAS UNE PERTE. Quatre colonnes de cahier
# n'ont aucun logis au registre : `📍 Où` (pour les actions — l'état cible, lui,
# a bien la sienne), `⛓️ Dépend de`, `🚪 Ce que cela ferme`, `📅 Jour dû`. Le
# registre dérivé est donc PLUS PAUVRE que les cahiers, et c'est sa nature : un
# index n'a pas à tout porter, il a à dire où la chose est écrite. Le jour où
# quelqu'un criera à la perte d'information, la réponse est cette phrase-ci.


def _sq(s):
    """L'en-tête réduit à ce qui l'identifie : sans signe, sans accent, sans casse."""
    s = sans_emoji(s).lower().replace(u"’", u"'")
    for a, b in ((u"àâä", u"a"), (u"éèêë", u"e"), (u"îï", u"i"),
                 (u"ôö", u"o"), (u"ùûü", u"u"), (u"ç", u"c")):
        for c in a:
            s = s.replace(c, b)
    return u" ".join(s.split())


def lire_cahiers(livres):
    """Les pièces de plan telles qu'elles sont ÉCRITES dans les cahiers :
    en-tête → cellule, plus le nom de l'affaire qui les porte. C'est la matière
    de l'index, et elle ne vient de nulle part ailleurs."""
    par_genre = {g: {} for g in set(REGISTRES.values())}
    tous = {}
    for b in livres:
        # LES CAHIERS `nera-*` N'ALIMENTENT PAS CES REGISTRES — ils sont d'un
        # AUTRE SIÈGE. Le plan de la Néra a ses propres index dans le coffret
        # `boite-plan-nera` (`nera-etats`, `nera-verrous`, `nera-clefs`,
        # `nera-actions`) ; les six d'ici vivent dans `boite-grand-plan`. Verser
        # les 49 pièces de la Néra dans l'index de la reine mélangerait deux
        # plans que rien ne relie — et leur M01 n'est même pas le nôtre : c'est
        # « La porte de la Gadoue », quand le nôtre est « Les voiles du Gosier ».
        if not str(b.get("id") or u"").startswith("affaire-"):
            continue
        for t in (b.get("tables") or []):
            g = genre_de(t.get("titre") or u"")
            if g not in par_genre:
                continue
            cols = t.get("colonnes") or []
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
                if len(c) < 2 or not c[0] or not c[1]:
                    continue
                m = numero_de(c[0])
                if not m:
                    continue
                par_genre[g][m.group(1)] = {
                    "brut": c[0], "nom": c[1], "affaire": nu(b.get("titre")),
                    "cellules": dict(zip([_sq(x) for x in cols], c))}
                tous.setdefault(m.group(1), set()).add(g)
    return par_genre, tous


def deriver(livres):
    """Refait les quatre registres depuis les cahiers. Ne touche à rien : rend
    ce qu'il ÉCRIRAIT, plus la liste de ce qu'il refuse de toucher.

    ON N'EFFACE JAMAIS PAR OMISSION. Le temps précédent effaçait explicitement,
    sous garde ; celui-ci pourrait effacer par silence, ce qui est bien pire —
    une ligne qui disparaît d'un index régénéré ne laisse pas de trace. Deux
    familles sont donc CONSERVÉES telles quelles, et dites à chaque passage :

      · sans cahier — aucune source ne la produit (21010, 21020 : la clef et son
        verrou dont les trois actions portent « CÉDÉ AU 6000 » dans leur propre
        prose, et qui attendent un repointage qu'un homme seul peut décider) ;
      · nom divergent — un cahier porte bien ce numéro, mais sous un autre nom.
        Ce peut être un renommage (23000 : « Donjon ouvert » devenu « Le Donjon
        a changé de main sans combat dans les murs ») ou un NUMÉRO RECYCLÉ par
        une autre affaire (le bloc 7xxx, où « La ville de Port-Réal » a cédé la
        place au Trident et à Harrenhal). Les deux se ressemblent trait pour
        trait et ne se distinguent pas au calcul. Écraser un recyclage, ce
        serait perdre la dernière trace d'une affaire entière. On refuse.
    """
    cah, tous = lire_cahiers(livres)
    sorties = {}
    for b in livres:
        bid = str(b.get("id") or u"")
        if bid not in REGISTRES:
            continue
        g = REGISTRES[bid]
        neuves_cols = colonnes_de(g)
        # OÙ LIRE LE SENS DANS LA FORME QU'ON TROUVE SUR LE DISQUE. Les lignes
        # conservées viennent de l'ancienne forme (huit ou neuf colonnes) ou de
        # la neuve (quatre), selon qu'on repasse ou non. On repère donc la
        # colonne de sens dans les en-têtes ACTUELS du registre : exact d'abord,
        # puis un préfixe ancré — « ce qu'on fait, et où » commence par « ce
        # qu'on fait ». Le préfixe ne sert QUE sur les en-têtes du registre,
        # jamais sur ceux des cahiers, où il rouvrirait le repli par inclusion
        # qui a fait atterrir l'avancement à la place du numéro.
        vieilles = [_sq(x) for x in (b.get("colonnes") or [])]
        cible = _sq(SENS[g])
        i_sens = next((i for i, k in enumerate(vieilles) if k == cible), None)
        if i_sens is None:
            i_sens = next((i for i, k in enumerate(vieilles) if k.startswith(cible)), None)
        i_aff = next((i for i, k in enumerate(vieilles) if k == u"affaire"), None)

        anciennes = {}
        for l in (b.get("lignes") or []):
            c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
            if not c or not c[0]:
                continue
            m = numero_de(c[0])
            if m:
                anciennes[m.group(1)] = c

        def transposer(c, motif):
            """Une ligne conservée passe à la forme neuve : deux formes dans un
            même tableau est une invitation à la confusion, et ce qu'elle perd
            est justement ce qui ne devait plus y être."""
            return {"cellules": [
                c[0],
                c[1] if len(c) > 1 else u"",
                c[i_sens] if (i_sens is not None and i_sens < len(c)) else u"",
                (c[i_aff] if (i_aff is not None and i_aff < len(c)) else u"") or motif]}

        lignes, gardees, sans_logis = {}, [], set()
        for n, p in cah[g].items():
            v = anciennes.get(n)
            if v is not None and len(v) > 1 and sans_emoji(v[1]) != sans_emoji(p["nom"]):
                lignes[n] = transposer(v, u"—")
                gardees.append((n, u"nom divergent", v[1], p["nom"]))
                continue
            # LES DEUX PREMIÈRES COLONNES SE PRENNENT AU RANG, et elles seules :
            # le numéro et le nom sont en tête de toute table de plan, quel que
            # soit l'en-tête écrit au-dessus — `charger()` en fait déjà
            # l'hypothèse. Ça sauve les cinq verrous d'un cahier dont la table
            # porte par erreur les en-têtes des clefs : sans ça, l'index recevait
            # cinq lignes sans nom, ce qui est pire qu'une ligne absente.
            # LES SYNONYMES SE PRENNENT DANS LA TABLE, JAMAIS PAR INCLUSION. Un
            # cahier peut porter l'ancien en-tête du registre — `📝 Ce qu'on
            # fait, et où` pour `📝 Ce qu'on fait`. On accepte donc la cible et
            # tout en-tête que la table d'alias fait pointer sur elle, et rien
            # d'autre : pas de préfixe, pas d'inclusion, pas d'alias daté. « Ce
            # qui est vrai au matin du 30e » ne descendra pas, et c'est voulu —
            # il deviendrait « du 31e », et le repli qui l'attraperait est celui
            # qui a fait atterrir l'avancement à la place du numéro.
            cible = _sq(SENS[g])
            sens = None
            for k in [cible, ALIAS.get(cible)] + [a for a, v in ALIAS.items() if v == cible]:
                if k and k in p["cellules"]:
                    sens = p["cellules"][k]
                    break
            if sens is None:
                # UNE COLONNE SANS LOGIS EST DITE, jamais perdue en silence — avec
                # le cahier qui la lui refuse, pour qu'on sache où aligner
                # l'en-tête. La cellule reste vide dans l'INDEX ; le cahier, lui,
                # garde tout. Un index n'a pas à tout porter.
                sans_logis.add(p["affaire"][:34])
                sens = u""
            lignes[n] = {"cellules": [p["brut"], p["nom"], sens, p["affaire"]]}
        for n, c in anciennes.items():
            if n not in lignes:
                # TROIS MOTIFS, PAS UN. « Aucun cahier ne connaît ce numéro » et
                # « un cahier le connaît, mais d'un autre rang » ne se soignent
                # pas de la même main : le second est une collision de numéro
                # (44001, action ici et verrou au cahier de la présence), et
                # c'est un homme qui tranche laquelle des deux garde l'adresse.
                autre = sorted(tous.get(n, set()) - {g})
                motif = (u"genre " + u"/".join(autre)) if autre else u"sans cahier"
                lignes[n] = transposer(c, u"—")
                gardees.append((n, motif, c[1] if len(c) > 1 else u"", u""))
        # L'ORDRE EST LE NUMÉRO, toujours. Un index dont l'ordre dépend de celui
        # de lecture des livres produit un diff a chaque passage, et le bruit est
        # exactement ce sous quoi la prochaine divergence se cacherait.
        neuves = [lignes[n] for n in sorted(lignes, key=lambda x: (len(x), x))]
        titre = nu(b.get("titre"))
        if not titre.endswith(CALCULE):
            titre += CALCULE
        sorties[bid] = {"lignes": neuves, "titre": titre, "colonnes": neuves_cols,
                        "gardees": sorted(gardees), "sans_logis": sorted(sans_logis),
                        "avant": len(anciennes)}
    return sorties


def ecart_registres(livres=None):
    """Ce qui a été écrit à la main dans un registre dérivé. Pour tick.py.

    Sans cette garde, quelqu'un y posera une ligne de bonne foi dans six
    semaines, et l'on refera à l'identique la nuit qu'on vient de passer.

    LE TROU QU'ELLE A FAILLI AVOIR, et c'est la comparaison seule qui l'a
    trouvé : une main qui retouche un NOM dans le registre y crée une
    divergence — et la règle de conservation, qui refuse d'écraser un nom
    divergent, reproduit alors fidèlement la retouche. L'écart se referme sur
    lui-même et la garde ne voit rien. Or le nom est la colonne qui compte : la
    faute qu'on a payée le 30e était un nom.

    D'où deux sorties, et non une. La structure (lignes, colonnes, titre) se
    compare ; les noms divergents SE COMPTENT ET SE NOMMENT à chaque passage.
    Dix aujourd'hui : le jour où la liste en portera onze, quelqu'un aura
    écrit dans l'index. On ne peut pas distinguer une retouche d'une divergence
    ancienne par le calcul — on peut rendre la liste visible, et c'est assez."""
    if livres is None:
        livres = bibliotheque.charger(os.path.join(RACINE, "etat"))
    ecarts, divergences = [], []
    sorties = deriver(livres)
    for b in livres:
        bid = str(b.get("id") or u"")
        if bid not in sorties:
            continue
        s = sorties[bid]
        divergences += [(bid, n) for n, motif, a, c in s["gardees"]
                        if motif == u"nom divergent"]
        # LES COLONNES COMPTENT AUTANT QUE LES LIGNES, depuis que le générateur
        # les possède : un registre dont on aurait rajouté une colonne à la main
        # produit exactement le même compte de lignes, et la garde qui ne
        # regarderait que ce compte passerait à côté. C'est la faute que ce
        # fichier entier existe pour empêcher.
        a = json.dumps([b.get("colonnes") or [], b.get("lignes") or []],
                       ensure_ascii=False, sort_keys=True)
        n = json.dumps([s["colonnes"], s["lignes"]], ensure_ascii=False, sort_keys=True)
        if a != n:
            ecarts.append((bid, len(b.get("lignes") or []), len(s["lignes"])))
        elif not nu(b.get("titre")).endswith(CALCULE):
            ecarts.append((bid, -1, -1))
    return ecarts, sorted(divergences)


# ─────────────────────────────────────────────── écrire la couverture
CHAMPS = [u"LE NOM", u"L'OBJET", u"LE PÉRIMÈTRE — DANS", u"LE PÉRIMÈTRE — HORS",
          u"L'ÉTAT ACTUEL", u"LA PLAGE", u"LA CONCLUSION", u"FERMÉE QUAND"]
SIGNE = {u"LE NOM": u"🏷️", u"L'OBJET": u"🎯", u"LE PÉRIMÈTRE — DANS": u"🧱",
         u"LE PÉRIMÈTRE — HORS": u"🚫", u"L'ÉTAT ACTUEL": u"📌", u"LA PLAGE": u"🔢",
         u"LA CONCLUSION": u"💡", u"FERMÉE QUAND": u"🔚"}
CALCULE = u" — calculé, ne pas écrire à la main"


def refaire(b, pieces, inventaire):
    nom = nu(b.get("titre"))
    pend, eng, trous, liens, ech = blocs(nom, pieces, inventaire)
    tables = b["tables"]

    # 1 · l'ouverture : on garde tout ce qui est écrit, on ajoute LA CONCLUSION
    ouv = tables[0]
    largeur = len(ouv.get("colonnes") or [u"", u"", u"", u""])
    ecrit = {}
    for l in ouv.get("lignes") or []:
        c = (l if isinstance(l, list) else l.get("cellules")) or []
        if c:
            ecrit[sans_emoji(c[0]).upper()] = c
    neuves = []
    for ch in CHAMPS:
        c = ecrit.get(ch.upper())
        if c is None:
            c = [SIGNE[ch] + u" **" + ch + u"**"] + [u""] * (largeur - 1)
        neuves.append({"cellules": (c + [u""] * largeur)[:largeur]})
    if ech:
        r = [u"⏳ **LA PROCHAINE ÉCHÉANCE**", marque(ech[1], pieces) + u" — " + ech[0]] \
            + [u""] * largeur
        neuves.append({"cellules": r[:largeur]})
    ouv["lignes"] = neuves

    # 2 · les liens : les écrits restent, les dérivés se refont
    i_liens = next((i for i, t in enumerate(tables)
                    if re.search(u"affaires? li", sans_emoji(t.get("titre") or u""), re.I)), None)
    COLS_L = [u"🪢 Le lien", u"🔗 L'affaire", u"🔢 Notre pièce", u"🔢 La leur", u"📝 Pourquoi"]
    gardees = []
    if i_liens is not None:
        for l in tables[i_liens].get("lignes") or []:
            c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
            if not any(c):
                continue
            # ancienne forme : [affaire, relation, pourquoi]
            t0 = sans_emoji(tables[i_liens].get("colonnes", [u""])[0]).lower()
            if t0.startswith(u"l'affaire") or t0.startswith(u"laffaire"):
                lien = VIEUX.get(c[1].lower(), c[1].lower()) if len(c) > 1 else u""
                c = [lien, c[0], u"", u"", c[2] if len(c) > 2 else u""]
            c = (c + [u""] * 5)[:5]
            c[0] = VIEUX.get(c[0].lower(), c[0])
            if c[0].lower() in ECRITS:
                gardees.append({"cellules": c})
    derivees = [{"cellules": [l[0], l[1], l[2], l[3], u""]} for l in liens]
    table_liens = {"titre": u"🔗 Affaires liées — les liens écrits, puis les calculés",
                   "colonnes": COLS_L,
                   "lignes": (gardees + derivees) or [{"cellules": [u""] * 5}]}

    # 3 · les trois blocs calculés
    t_pend = {"titre": u"⛓️ Ce qui pend, et sur qui" + CALCULE,
              "colonnes": [u"🧭 Sens", u"🔢 Notre pièce", u"🔢 La leur", u"🔗 L'affaire"],
              "lignes": [{"cellules": l} for l in pend] or
                        [{"cellules": [u"—", u"", u"", u"rien ne traverse"]}]}
    t_eng = {"titre": u"🔨🪶 Ce qu'on engage, et qui d'autre le veut" + CALCULE,
             "colonnes": [u"🔢 La pièce", u"⚔️ Nos actions", u"🔗 Aussi engagée par"],
             "lignes": [{"cellules": l} for l in eng] or
                       [{"cellules": [u"—", u"", u"aucun moyen, aucun office"]}]}
    t_trous = {"titre": u"🕳️ Les trous" + CALCULE,
               "colonnes": [u"🕳️ Le défaut", u"🔢 Les pièces"],
               "lignes": [{"cellules": l} for l in trous] or
                         [{"cellules": [u"aucun — la chaîne tient de bout en bout", u""]}]}

    reste = [t for i, t in enumerate(tables) if i != 0 and i != i_liens
             and not re.search(u"ce qui pend|ce qu'on engage|les trous",
                               sans_emoji(t.get("titre") or u""), re.I)]
    b["tables"] = [ouv, table_liens, t_pend, t_eng, t_trous] + reste
    return len(pend), len(eng), len(trous), len(derivees)


def verser(session):
    """Verse uniquement les volumes touchés, avec contrôle optimiste.

    Tant que le monolithe est actif, on conserve sa sauvegarde historique et
    toute écriture concurrente fait refuser le lot. Après la scission, la
    session compare seulement les cahiers qu'elle a réellement changés : deux
    titulaires peuvent enfin écrire deux livres distincts en parallèle.
    """
    import shutil, time
    scindee = bibliotheque.est_scindee(os.path.join(RACINE, "etat"))
    sauve = None
    if not scindee:
        sauve = LIVRES + u".avant-couverture-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(LIVRES, sauve)
    try:
        session.sauver()
    except bibliotheque.BibliothequeModifiee as exc:
        if sauve and os.path.exists(sauve):
            os.remove(sauve)
        sys.stdout.write(u"\n‼ %s\n" % exc)
        return False
    if sauve:
        sys.stdout.write(u"  sauvegarde : %s\n" % os.path.basename(sauve))
    return True


def refaire_registres(livres):
    """Pose les quatre index dérivés dans `livres`. Rend le compte rendu."""
    sorties = deriver(livres)
    for b in livres:
        s = sorties.get(str(b.get("id") or u""))
        if s:
            b["lignes"], b["titre"] = s["lignes"], s["titre"]
            b["colonnes"] = s["colonnes"]
    return sorties


if __name__ == "__main__":
    args = sys.argv[1:]
    verif = "--verifier" in args
    filtre = args[args.index("--affaire") + 1] if "--affaire" in args else None

    if "--registres" in args:
        session = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
        livres = session.livres
        pieces_avant = charger(livres)[1]
        sorties = refaire_registres(livres)
        for bid, s in sorted(sorties.items()):
            sys.stdout.write(u"%-20s %4d ligne(s) → %4d · conservees %d\n"
                             % (bid, s["avant"], len(s["lignes"]), len(s["gardees"])))
            for n, motif, a, b_ in s["gardees"]:
                sys.stdout.write(u"     ~ %-6s %-14s %s%s\n" % (n, motif, a[:44],
                                 (u"   ← cahier : " + b_[:40]) if b_ else u""))
            if s["sans_logis"]:
                sys.stdout.write(u"     ! colonne(s) sans logis au cahier : %s\n"
                                 % u" · ".join(s["sans_logis"]))
        # LA GARDE QUI COMPTE : le compte de references pendantes ne monte pas.
        av = set(pieces_avant)
        pend_av = sorted(v for n in av for v in pieces_avant[n]["vers"] if v not in av)
        sys.stdout.write(u"\n  pieces avant %d · pendantes avant %d %s\n"
                         % (len(av), len(pend_av), pend_av))
        if verif:
            sys.stdout.write(u"--verifier : rien n'a ete ecrit.\n")
            sys.exit(0)
        if not verser(session):
            sys.exit(1)
        ap = charger(bibliotheque.charger(os.path.join(RACINE, "etat")))[1]
        pend_ap = sorted(v for n in ap for v in ap[n]["vers"] if v not in ap)
        sys.stdout.write(u"  pieces apres %d · pendantes apres %d %s\n"
                         % (len(ap), len(pend_ap), pend_ap))
        if len(pend_ap) > len(pend_av):
            sys.stdout.write(u"‼ LES PENDANTES ONT MONTE — relire la sauvegarde.\n")
            sys.exit(1)
        sys.stdout.write(u"4 registre(s) derive(s) dans etat/books.json\n")
        sys.exit(0)

    session = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    livres, pieces, inventaire, affaires = charger(session.livres)
    if filtre:
        affaires = [a for a in affaires if sans_emoji(filtre).lower() in sans_emoji(a["titre"]).lower()]

    for b in affaires:
        n = refaire(b, pieces, inventaire)
        sys.stdout.write(u"%-46s pend %d · engage %d · trous %d · liens calcules %d\n"
                         % (nu(b["titre"])[:46], n[0], n[1], n[2], n[3]))
    if verif:
        sys.stdout.write(u"--verifier : rien n'a ete ecrit.\n")
    elif verser(session):
        sys.stdout.write(u"%d couverture(s) refaite(s) dans etat/books.json\n" % len(affaires))
