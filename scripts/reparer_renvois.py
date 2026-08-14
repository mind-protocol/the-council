# -*- coding: utf-8 -*-
u"""Écrire le NUMÉRO de l'office là où le cahier n'a écrit qu'un nom d'homme.

POURQUOI. 370 actions sur 608 portent, dans leur colonne « 🪶 Office », un nom
en toutes lettres et pas un numéro : « SER STEFFON DARKLYN », « Aldon Hask »,
« Le Sanglier, maître des rôles ». Un lecteur humain sait qui c'est ; la machine
ne voit rien du tout — ni la charge par office (`etat_du_plan.py --office`), ni
le partage des moyens, ni le trou « action que personne ne peut porter ». Le
défaut est signalé affaire par affaire par `couverture.py` sous le libellé
« office ou moyen nommé en clair ».

CE QU'IL FAIT, ET CE QU'IL NE FAIT PAS.

  · Il ne REMPLACE jamais la prose : il PRÉFIXE le numéro et garde la cellule
    telle qu'elle est écrite. « Aldon Hask paie ; le Sanglier marque les noms »
    devient « O02 — Aldon Hask paie ; le Sanglier marque les noms » — parce que
    la prose dit qui fait quoi, ce qu'aucun numéro ne dira jamais.
  · Il ne touche QUE la colonne d'office des tables d'actions, repérée par son
    EN-TÊTE et jamais par son rang : le nombre de colonnes de ces tables bouge.
  · Il ne touche que les cas SÛRS — un homme dont le registre des offices ne
    donne qu'un seul office possible. Rulf Corne (O05 les grèves / O06 le port)
    et Aldon Hask (O09 le compte / O14 le quai) sont écartés d'office, comme
    tout ce que le registre ne connaît pas : la reine, Denys Bar Emmon, Sara
    Poulain, Marlo Vasse, Mysaria. Ceux-là se tranchent à la main.
  · LA RÈGLE DE CHOIX EST « LE PREMIER HOMME NOMMÉ PORTE L'ACTION », et rien
    d'autre. Une cellule qui en nomme deux — « Alys Grive et mestre Gerardys » —
    prend le numéro du premier, parce que c'est ainsi que ces cellules sont
    écrites partout : le porteur d'abord, ses concours ensuite. Le second nom
    reste dans la prose, et le rapport le dit.
  · Les cahiers `nera-*` sont écartés : leur registre M/O est un AUTRE registre
    (leur O01 est « Le chantier » de Hann Bourbe, pas notre castellan).

Usage :
    python scripts/reparer_renvois.py               à blanc — n'écrit rien
    python scripts/reparer_renvois.py --vraiment    écrit, après sauvegarde
    python scripts/reparer_renvois.py --affaire "fenetre"   une affaire

La sauvegarde est posée à côté du fichier : etat/books.json.avant-renvois-<ts>.
Le retrait du fichier est relu et reproduit (books.json est écrit à un espace) :
un passage ne doit pas rendre 2,4 Mo de bruit au diff.
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

from couverture import nu, sans_emoji, genre_de, col, MO, NUM, retrait  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── LE REGISTRE, LU À L'ENVERS ────────────────────────────────────────────────
# Titulaire → office, d'après `plan-offices` (colonne « 👤 Le titulaire ») et
# d'après les noms d'office eux-mêmes. `sur` dit si cet homme n'a QU'UN office
# possible ; les autres sont détectés pour être écartés, pas pour être écrits.
GENS = [
    (r"robert\s+quince",                                        "O01", True),
    (r"sanglier|ma[iî]tre des r[oô]les|maitre des roles",        "O02", True),
    (r"aurore\s+inchausp|ma[iî]tresse des nouvelles"
     r"|ma[iî]tresse de la voix",                                "O03", True),
    (r"\btobb\b|\bnesse\b|coureu(?:r|se)s? de la reine",         "O04", True),
    (r"gerardys|la roukerie",                                    "O07", True),
    (r"\bwend\b",                                                "O08", True),
    (r"al[yi]s grive|bardesse",                                  "O10", True),
    (r"jacaerys",                                                "O11", True),
    # « ser Steffon » tout court : un seul Steffon dans la maison, et trois
    # actions de « Voir venir » ne l'écrivent pas autrement.
    (r"steffon\s+darklyn|ser\s+steffon",                         "O12", True),
    (r"corlys\s+velaryon|lord corlys",                           "O13", True),
    (r"nicolas reynolds",                                        "O17", True),
    # connus, mais pas tranchables ici
    (r"rulf\s+corne|ma[iî]tre rulf|ma[iî]tre du port",           "O05|O06", False),
    (r"aldon hask|ma[iî]tre hask|\bhask\b",                      "O09|O14", False),
    (r"la reine|rhaenyra|votre gr[aâ]ce",                        "(la reine)", False),
    (r"denys bar emmon|bar emmon",                               "(hors registre)", False),
    (r"sara poulain|dame sara",                                  "(hors registre)", False),
    (r"marlo vasse",                                             "(hors registre)", False),
    (r"mysaria",                                                 "(hors registre)", False),
    (r"sarro vaeth",                                             "(hors registre)", False),
    (r"hann bourbe",                                             "(plan Néra)", False),
]

# Ce qui est déjà une déclaration de vacance : on n'y touche pas, c'est écrit
# exprès et `couverture.py` le compte à part (« SANS OFFICE », un vrai trou).
VACANT = re.compile(u"sans office|à désigner|a designer|vacant|néant|neant"
                    u"|la reine seule", re.I)

# ── L'IDEMPOTENCE, DITE AU LIEU D'ÊTRE ESPÉRÉE ────────────────────────────────
# Ce script PRÉFIXE. Repassé une seconde fois sur une cellule qu'il a déjà
# écrite, il produirait « O03 — O03 — Dame Aurore », et l'on ne s'en apercevrait
# qu'en lisant le cahier. Il ne le faisait pas — parce que le filtre
# `MO.findall(brut)` écarte TOUTE cellule portant un numéro, la sienne comprise.
# Mais c'était un effet de bord, pas une garde : le compte rendu ne distinguait
# pas « déjà faite » de « pas reconnue », donc rien à l'écran n'aurait dit qu'un
# second passage était sans objet — ni, le jour où quelqu'un resserre ce filtre
# pour attraper « Rulf Corne (O06) », que la protection venait de tomber.
#
# On sépare donc les trois cas, et on les COMPTE :
#   déjà faite   la cellule commence par « Onn — » : c'est notre propre écriture,
#                on la reconnaît et on la laisse intacte.
#   déjà numérotée sous une autre forme — « **O13** — la mer », « O02 » seul,
#                « Aldon Hask (**O09**) » : quelqu'un l'a écrite à la main, le
#                lien existe pour la machine, on n'y touche pas davantage.
#   à traiter    aucun numéro nulle part.
DEJA = re.compile(u"^\\s*\\**\\s*([MO]\\d{2,3})\\s*\\**\\s*—")


def numero_de(cellule):
    """(numero, sûr, tous_les_noms_trouvés) — le PREMIER homme nommé gagne."""
    trouves = []
    for motif, num, sur in GENS:
        m = re.search(motif, cellule, re.I)
        if m:
            trouves.append((m.start(), num, sur))
    trouves.sort()
    if not trouves:
        return None, False, []
    _, num, sur = trouves[0]
    return num, sur, [x[1] for x in trouves]


def passer(affaire=None):
    livres = json.load(io.open(LIVRES, encoding="utf-8"))
    faits, refus, deja, numerotees = [], [], [], []
    for b in livres:
        bid = str(b.get("id") or u"")
        if not bid.startswith("affaire-"):
            continue            # les nera-* ont leur propre registre M/O
        titre = nu(b.get("titre"))
        if affaire and sans_emoji(affaire).lower() not in sans_emoji(titre).lower() \
                and affaire not in bid:
            continue
        for t in (b.get("tables") or []):
            if genre_de(t.get("titre") or u"") != "action":
                continue
            colonnes = [nu(x) for x in (t.get("colonnes") or [])]
            i_off = col(colonnes, u"office")     # PAR L'EN-TÊTE, jamais par rang
            if i_off is None:
                continue
            for ligne in (t.get("lignes") or []):
                cellules = ligne if isinstance(ligne, list) \
                    else (ligne.get("cellules") or [])
                if len(cellules) <= i_off:
                    continue
                brut = nu(cellules[i_off])
                num_ligne = NUM.search(nu(cellules[0]) if cellules else u"")
                piece = num_ligne.group(1) if num_ligne else u"?"
                if not brut or VACANT.search(brut):
                    continue
                m_deja = DEJA.match(brut)
                if m_deja:
                    deja.append((bid, piece, brut, m_deja.group(1)))
                    continue
                if MO.findall(brut):
                    numerotees.append((bid, piece, brut,
                                       u" · ".join(MO.findall(brut))))
                    continue
                num, sur, tous = numero_de(brut)
                if num is None:
                    refus.append((bid, piece, brut, u"aucun nom reconnu"))
                    continue
                if not sur:
                    refus.append((bid, piece, brut,
                                  u"non tranchable : " + num))
                    continue
                faits.append((bid, piece, brut, num,
                              u" + ".join(tous[1:]) or u""))
                cellules[i_off] = num + u" — " + cellules[i_off]
    return livres, faits, refus, deja, numerotees


def ecrire(livres):
    sauve = LIVRES + u".avant-renvois-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(LIVRES, sauve)
    n = retrait()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(LIVRES), suffix=".tmp")
    os.close(fd)
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(livres, f, ensure_ascii=False, indent=n)
    os.replace(tmp, LIVRES)
    return sauve


if __name__ == "__main__":
    args = sys.argv[1:]
    aff = args[args.index("--affaire") + 1] if "--affaire" in args else None
    livres, faits, refus, deja, numerotees = passer(aff)

    sys.stdout.write(u"\n%d cellule(s) d'office prendraient leur numéro :\n\n"
                     % len(faits))
    for bid, piece, brut, num, autres in faits:
        sys.stdout.write(u"  %-38s %-6s %-4s  %s%s\n"
                         % (bid[:38], piece, num, brut[:74],
                            (u"   [aussi nommés : %s]" % autres) if autres else u""))
    sys.stdout.write(u"\n%d cellule(s) DÉJÀ FAITE(S) — elles commencent par leur "
                     u"numéro, on n'y retouche pas.\n" % len(deja))
    sys.stdout.write(u"%d cellule(s) déjà numérotée(s) d'une autre main "
                     u"(« **O13** — … », « O02 », « … (O09) ») — intactes aussi.\n"
                     % len(numerotees))
    if "--tout" in args:
        for bid, piece, brut, num in deja:
            sys.stdout.write(u"    = %-34s %-6s %-4s %s\n"
                             % (bid[:34], piece, num, brut[:62]))
        for bid, piece, brut, nums in numerotees:
            sys.stdout.write(u"    ~ %-34s %-6s %-10s %s\n"
                             % (bid[:34], piece, nums[:10], brut[:56]))
    sys.stdout.write(u"\n%d cellule(s) laissée(s) à la main :\n\n" % len(refus))
    for bid, piece, brut, pourquoi in refus:
        sys.stdout.write(u"  %-38s %-6s %-22s %s\n"
                         % (bid[:38], piece, pourquoi, brut[:60]))

    if "--vraiment" not in args:
        sys.stdout.write(u"\nÀ blanc : RIEN N'A ÉTÉ ÉCRIT. "
                         u"--vraiment pour appliquer.\n")
        raise SystemExit(0)
    # LA GARDE DE DERNIÈRE MINUTE. On ne se fie pas au classement du dessus
    # pour ce qui ne se rattrape pas : on relit ce qui va être écrit, et si une
    # cellule porte deux fois le même numéro en tête, RIEN ne part.
    double = re.compile(u"^\\s*([MO]\\d{2,3})\\s*—\\s*\\1\\s*—")
    for bid, piece, brut, num, autres in faits:
        if double.match(num + u" — " + brut):
            sys.stdout.write(u"\n‼ %s / %s prendrait « %s — %s » : NUMÉRO DOUBLÉ. "
                             u"Rien n'a été écrit.\n" % (bid, piece, num, brut[:50]))
            raise SystemExit(1)
    if not faits:
        sys.stdout.write(u"\nRien à écrire : les cellules reconnaissables portent "
                         u"déjà leur numéro. Le fichier n'a pas été touché.\n")
        raise SystemExit(0)
    sauve = ecrire(livres)
    sys.stdout.write(u"\nÉcrit. Sauvegarde : %s\n" % os.path.basename(sauve))
    sys.stdout.write(u"Vérifier ensuite : python scripts/etat_du_plan.py\n")
