# -*- coding: utf-8 -*-
u"""Normaliser la colonne d'état des actions du grand plan.

POURQUOI. La colonne « ⏳ État » d'une action est devenue un champ de récit :
au lieu de « faite », on y lit deux cents signes de prose datée. Trois
conséquences, toutes mesurées :

  · `etat_du_plan.py` imprime un paragraphe là où il devrait dire un mot ;
  · rien ne se compte — dix-sept pièces écrivent « fait » de six façons ;
  · la date de réalisation est NOYÉE dans la prose, donc personne ne peut dire
    ce qui a été fait cette lune.

CE QU'ON FAIT. Trois colonnes au lieu d'une, et le vocabulaire fermé :

  ⏳ État      un mot, pris dans six et pas un de plus
  📅 Jour fait la date du monde, quand le texte la donne — JAMAIS devinée
  📝 Note      toute la prose retirée, à la virgule près, rien de perdu

ON NE TRANCHE PAS LES AMBIGUS TOUT SEUL. « en réserve », « portée »,
« engagée », « ⏳ verdict aujourd'hui », « 🔸 à moitié faite » ne se rangent pas
au calcul : chacun a une recommandation écrite ici, motivée, et rien ne
s'applique sans `--ambigus`. Même règle que le verseur de cahiers : refuser
plutôt que deviner.

Usage :
    python scripts/plan/normaliser_etats.py                 rapport à blanc
    python scripts/plan/normaliser_etats.py --rapport f.md   le poser dans un fichier
    python scripts/plan/normaliser_etats.py --vraiment       applique les CLAIRS seuls
    python scripts/plan/normaliser_etats.py --vraiment --ambigus
                                                        applique aussi les recommandations
"""
import io, os, re, sys, time, unicodedata, collections

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVRES = os.path.join(RACINE, "etat", "books.json")
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from plan.expose import couverture as C  # noqa: E402  — genre_de, sans_emoji, nu, col
import bibliotheque  # noqa: E402

# ─────────────────────────────────────────────── le vocabulaire fermé
# Six valeurs. Toute autre est une faute, et `tick.py --verifier` doit la dire.
VOCABULAIRE = [u"à faire", u"en cours", u"bloquée", u"faite", u"close",
               u"abandonnée"]

COL_ETAT = u"⏳ État"
COL_JOUR = u"📅 Jour fait"
COL_NOTE = u"📝 Note"

# ─────────────────────────────────────────────── ce qui se lit sans hésiter
# La valeur se lit EN TÊTE de cellule, jamais au milieu : un « faite » qui
# arrive à la troisième phrase raconte autre chose que l'état de la ligne.
CLAIRES = [
    (u"^(?:à|a)\\s+faire\\b",              u"à faire"),
    (u"^en\\s+cours\\b",                    u"en cours"),
    (u"^d(?:é|e)bloqu(?:é|e)e?\\b",         None),   # traité en ambigu
    (u"^bloqu(?:é|e)e?\\b",                 u"bloquée"),
    (u"^suspendue\\b",                      u"bloquée"),
    (u"^clos(?:e|es)?\\b",                  u"close"),
    (u"^abandonn(?:é|e)e?s?\\b",            u"abandonnée"),
    (u"^fai(?:te|tes|t|ts)\\b",             u"faite"),
]

# Ce qui, APRÈS un « faite » de tête, contredit ce « faite » : la ligne n'est
# pas close, elle est à cheval. On refuse de la ranger toute seule.
CONTREDIT_FAITE = u"reste à faire|et en cours|à moitié|moiti(?:é|e) rendue|non close"

# Une tête claire dont la SUITE déplace la ligne ailleurs : « à faire ·
# transférée au 8000 » n'est pas un « à faire », c'est peut-être un abandon. On
# ne le tranche pas au calcul.
DEPLACEE = u"transf(?:é|e)r(?:é|e)e?\\s+(?:au|à|a)\\s+\\d|absorb(?:é|e)e?\\s+par\\s+\\d"

# ─────────────────────────────────────────────── ce qui demande un arbitrage
# (motif de tête, recommandation, pourquoi celle-là)
AMBIGUS = [
    (u"^engag(?:é|e)e?\\b", u"en cours",
     u"« engagée » dit qu'on a mis la main dessus, pas que c'est fini — et deux "
     u"des trois cellules écrivent NON CLOSE en toutes lettres. Mais le mot "
     u"sert aussi d'« accordée » (une dépense engagée EST tranchée)."),
    (u"^accord(?:é|e)e?\\b", u"en cours",
     u"la reine a accordé, l'exécution court : la cellule dit « ACCORDÉE … et "
     u"ENGAGÉE le matin même », puis donne un premier compte à venir."),
    (u"^accept(?:é|e)e?\\b", u"en cours",
     u"la charge est acceptée et dite debout, mais la ligne au registre des "
     u"offices et les deux sceaux manquent. Arbitré « en cours » : une charge "
     u"n'est prise qu'écrite et scellée — c'est la règle appliquée à Corlys, "
     u"on ne l'assouplit pas ici."),
    (u"^port(?:é|e)e?\\b", u"en cours",
     u"« portée — note remise à sa main …, réponse attendue » : le geste est "
     u"fait, l'affaire ne l'est pas."),
    (u"^en\\s+r(?:é|e)serve\\b", u"à faire",
     u"rien n'est commencé et rien ne l'empêche : c'est un « à faire » qu'on "
     u"garde sous le coude. Se lit « bloquée » si la mise en réserve est un "
     u"empêchement écrit ailleurs."),
    (u"^en\\s+usage\\b", u"en cours",
     u"« en usage à partir du 28e au soir — À REPRENDRE À LA LUNE PROCHAINE » : "
     u"ça tourne, et ça a un terme."),
    (u"^(?:à|a)\\s+refaire\\b", u"à faire",
     u"le travail est à reprendre depuis le début et son chiffre est déclaré "
     u"faux : c'est un « à faire », pas un « faite »."),
    (u"^demand(?:é|e)\\b", u"en cours",
     u"« demandé le 28e — on saura demain à sept heures » : la demande est "
     u"partie, on attend. « bloquée » si l'on tient l'attente pour un blocage."),
    (u"^commenc(?:é|e)e?\\b", u"en cours",
     u"« COMMENCÉE le 30e, première ligne portée » — sans réserve."),
    (u"^pay(?:é|e)e?\\b", u"faite",
     u"« PAYÉE ET REÇUE », l'or est sorti de caisse et le reçu contresigné : "
     u"rien ne pend."),
    (u"^pr(?:é|e)par(?:é|e)e?\\b", u"bloquée",
     u"« PRÉPARÉE, ARRÊTÉE SUR UN SEUL GESTE … elle attend le sceau de la "
     u"reine » : c'est un empêchement nommé, pas un travail en cours."),
    (u"^toujours\\s+suspendue\\b", u"bloquée",
     u"suspendue avec son motif écrit (24008) et sa condition de reprise."),
    (u"^non\\s+engag(?:é|e)e?\\b", u"à faire",
     u"l'aveu dit que rien n'a été demandé ; l'empêchement est un scrupule, pas "
     u"un verrou. « bloquée » si l'on tient le crédit dépensé ailleurs pour un "
     u"empêchement réel."),
    (u"^non\\s+d(?:é|e)clench(?:é|e)e?\\b", u"à faire",
     u"« non déclenchée … cette ligne reprend vie telle qu'écrite si le regard "
     u"daté de 8025 ne revient pas avant J−24 » : elle dort, elle n'est pas morte. "
     u"« abandonnée » serait faux — la condition de réveil est écrite."),
    (u"^d(?:é|e)bloqu(?:é|e)e?\\b", u"en cours",
     u"« DÉBLOQUÉE PAR LE HAUT … je cesse d'y suspendre mon chiffre » : le "
     u"verrou tombe, le travail reprend. Une des deux cellules pourrait se lire "
     u"« à faire » (rien n'a encore été fait après le déblocage)."),
    (u"^sans\\s+objet\\b", u"close",
     u"« sans objet — absorbée par 40024 » : la ligne ne se fera pas ici, mais "
     u"elle se fait ailleurs. Arbitré `close` et non `abandonnée`, même motif "
     u"que les lignes transférées."),
    (u"^nom\\s+(?:é|e)crit\\b", u"en cours",
     u"le nom est posé mais « RESTE À DIRE DEVANT LES DOUZE », et les douze "
     u"n'existent pas encore : l'affaire n'est pas close."),
    (u"^deuxi(?:è|e)me\\s+jour\\s+de\\s+silence\\b", u"en cours",
     u"une veille qui court, avec sa règle d'alarme datée de demain."),
    (u"^rouvre\\b", u"bloquée",
     u"« rouvre le 9e jour de la 4e lune, nom dû le 17e ». Arbitré « bloquée » : "
     u"une date d'ouverture non atteinte est un empêchement, pas une tâche "
     u"disponible — la ranger en « à faire » la ferait remonter dans ce qui "
     u"peut se prendre aujourd'hui, et c'est faux."),
    (u"^(?:é|e)tat\\s*:", u"en cours",
     u"la cellule s'écrit « État : à faire → en cours, moitié rendue le 28e » — "
     u"la valeur y est, mais rédigée comme une transition."),
    (u"^en\\s+retard\\b", u"à faire",
     u"un retard n'est pas une valeur : la ligne n'est pas faite et rien ne "
     u"l'empêche. Le retard appartient à la note, ou à « Jour dû »."),
    (u"^verdict\\b", u"bloquée",
     u"« ⏳ verdict aujourd'hui … Rien à faire d'ici là » : on attend quelqu'un "
     u"d'autre, c'est la définition d'un blocage."),
    (u"^pas\\s+commenc(?:é|e)e?\\b", u"bloquée",
     u"« ⚠️ pas commencée — suspendue au 63023 » : l'empêchement est nommé."),
    (u"^impossible\\b", u"bloquée",
     u"« ⛔ impossible tant que 21220 dort »."),
    (u"^(?:à|a)\\s+moiti(?:é|e)\\s+faite\\b", u"en cours",
     u"reste la relecture à voix haute et la remise de la colonne des prix : "
     u"c'est un travail en cours, pas un travail fait."),
    (u"^(?:é|e)crite,\\s*scell(?:é|e)e", u"en cours",
     u"« ÉCRITE, SCELLÉE, ET JAMAIS PARTIE … cavalier non lancé » : le pli "
     u"existe, l'action ne s'est pas produite. Se lit « bloquée » si l'on tient "
     u"le cavalier qui ne part pas pour un empêchement."),
    (u"^deux\\s+choses\\b", u"en cours",
     u"la cellule sépare un acte fait (scellé, retenu chez le mestre) d'une "
     u"garantie « pas écrite du tout » : à cheval, donc en cours."),
    (u"^le\\s+castellan\\b", u"en cours",
     u"aucune valeur d'état n'est écrite : la cellule est un compte rendu. "
     u"Le bois est tenu prêt en permanence — c'est une tenue, donc en cours."),
]

# ─────────────────────────────────────────────── les dates du monde
MOIS_MOT = {u"première": 1, u"premiere": 1, u"deuxième": 2, u"deuxieme": 2,
            u"troisième": 3, u"troisieme": 3, u"quatrième": 4, u"quatrieme": 4,
            u"cinquième": 5, u"cinquieme": 5}
UNITES = {u"premier": 1, u"deuxième": 2, u"troisième": 3, u"quatrième": 4,
          u"cinquième": 5, u"sixième": 6, u"septième": 7, u"huitième": 8,
          u"neuvième": 9, u"dixième": 10, u"onzième": 11, u"douzième": 12,
          u"treizième": 13, u"quatorzième": 14, u"quinzième": 15,
          u"seizième": 16, u"dix-septième": 17, u"dix-huitième": 18,
          u"dix-neuvième": 19, u"vingtième": 20, u"vingt-et-unième": 21,
          u"vingt-deuxième": 22, u"vingt-troisième": 23, u"vingt-quatrième": 24,
          u"vingt-cinquième": 25, u"vingt-sixième": 26, u"vingt-septième": 27,
          u"vingt-huitième": 28, u"vingt-neuvième": 29, u"trentième": 30,
          u"trente-et-unième": 31}

# « 1er de la 4e lune, an 129 » · « 30e j., 3e lune, an 129 » · « 1er jour de la 4e lune »
D_PLEINE = re.compile(
    u"(?:le\\s+)?(\\d{1,2})\\s*(?:er|e|ère|re)\\b\\s*"
    u"(?:jour\\s*)?(?:j\\.\\s*)?"
    u"(?:de\\s+la\\s+|,\\s*)"
    u"(\\d{1,2})\\s*(?:e|ère|re)(?:\\s+lune)?"
    u"(?:\\s*,\\s*an\\s+(\\d+))?", re.I)
# « le vingt-huitième jour de la troisième lune, an 129 »
D_MOT = re.compile(
    u"(?:le\\s+)?([a-zàâçéèêëîïôùûü-]+(?:ième|ieme)|premier)\\s+jour\\s+"
    u"de\\s+la\\s+([a-zàâçéèêëîïôùûü-]+(?:ième|ieme|ère|ere))\\s+lune"
    u"(?:\\s*,\\s*an\\s+(\\d+))?", re.I)
# « le 28e », « 27e au soir », « fait le 26e à 11h05 » — le jour seul
D_NUE = re.compile(u"(?:le\\s+|du\\s+)?(\\d{1,2})\\s*(?:er|e)\\b(?!\\s*lune)", re.I)


def _suffixe(j):
    return u"er" if j == 1 else u"e"


def date_du_monde(texte):
    u"""La date de réalisation, telle que le TEXTE la donne. Rien d'autre.

    ON N'INVENTE JAMAIS LA LUNE. « faite — 27e au soir » ne dit pas de quelle
    lune : on rend « 27e », et pas « 27e de la 3e lune » sous prétexte que ce
    serait probablement vrai. Une date complétée de tête est une date qu'on ne
    peut plus recompter."""
    t = C.nu(texte or u"")
    if not t:
        return u""
    cands = []
    m = D_PLEINE.search(t)
    if m:
        j, lu, an = int(m.group(1)), int(m.group(2)), m.group(3)
        s = u"%d%s de la %de lune" % (j, _suffixe(j), lu)
        cands.append((m.start(), s + (u", an " + an if an else u"")))
    m = D_MOT.search(t)
    if m:
        j = UNITES.get(m.group(1).lower())
        lu = MOIS_MOT.get(m.group(2).lower())
        if j and lu:
            an = m.group(3)
            s = u"%d%s de la %de lune" % (j, _suffixe(j), lu)
            cands.append((m.start(), s + (u", an " + an if an else u"")))
    # LE JOUR NU NE SE PREND QU'EN TÊTE. « faite — les deux journaux de bord du
    # 20e remis … le 30e de la 3e lune » : le 20e est la date des journaux, pas
    # celle du travail. Une date de réalisation suit le mot d'état de près ; ce
    # qui vient plus loin dans la phrase parle d'autre chose.
    m = D_NUE.search(t[:26])
    if m:
        j = int(m.group(1))
        if 1 <= j <= 31:
            cands.append((m.start(), u"%d%s" % (j, _suffixe(j))))
    if not cands:
        return u""
    # LA PREMIÈRE DATE, PAS LA PLUS PRÉCISE : « faite, le 28e au matin … il
    # portera le 4e de la 4e lune » est faite le 28e. La seconde date parle
    # d'autre chose. On départage à égalité de position en faveur de la plus
    # complète, ce qui est le cas « 1er de la 4e lune » vu deux fois.
    p = min(x[0] for x in cands)
    proches = [s for d, s in cands if d <= p + 1]
    return max(proches, key=len)


# ─────────────────────────────────────────────── lire une cellule
def tete(texte):
    u"""La cellule sans ce qui la précède : signes, gras, ponctuation, blancs.
    C'est là que se lit la valeur, et nulle part ailleurs."""
    t = C.nu(texte or u"").replace(u"**", u"")
    i = 0
    while i < len(t) and (t[i].isspace()
                          or unicodedata.category(t[i]) in ("So", "Mn", "Cf")
                          or t[i] in u"·-–—*:.!‼⚠⏳⛔✅🔸️"):
        i += 1
    return t[i:]


def _sansacc(s):
    for a, b in ((u"àâä", u"a"), (u"éèêë", u"e"), (u"îï", u"i"),
                 (u"ôö", u"o"), (u"ùûü", u"u"), (u"ç", u"c")):
        for c in a:
            s = s.replace(c, b)
    return s


def lire(cellule):
    u"""Rend (valeur, note, ambigu, motif).

    `valeur`  la valeur cible, ou u"" si l'on ne sait pas ;
    `note`    ce qui reste de la cellule une fois la valeur retirée ;
    `ambigu`  True si le rangement demande un arbitrage humain ;
    `motif`   pourquoi cette recommandation-là (vide si le cas est clair).
    """
    brut = C.nu(cellule or u"")
    if not brut:
        return u"à faire", u"", True, (
            u"cellule vide — aucune valeur écrite du tout. Arbitré : le défaut "
            u"d'une action est « pas commencée », jamais « pas d'état ».")
    t = tete(brut)
    bas = _sansacc(t.lower())

    for motif, valeur in CLAIRES:
        if valeur is None:
            continue
        m = re.match(_sansacc(motif), bas)
        if not m:
            m = re.match(motif, t, re.I)
        if not m:
            continue
        reste = t[m.end():].strip(u" ·—–-,.:;")
        if valeur == u"faite" and re.search(CONTREDIT_FAITE, brut, re.I):
            return u"en cours", brut, True, (
                u"la tête dit « faite » et la suite la contredit (« reste à "
                u"faire », « et en cours », « à moitié »). Chacune se lit à la "
                u"main : 32025 et 37121 sont bien à cheval ; 43037 est faite, "
                u"et son « Reste à faire dire les siens » ouvre une AUTRE ligne, "
                u"pas celle-ci.")
        if re.search(DEPLACEE, brut, re.I):
            return u"close", reste, True, (
                u"la ligne est renvoyée ailleurs (« transférée au … », "
                u"« absorbée par … »). Arbitré `close` et non `abandonnée` : le "
                u"travail continue sous l'autre numéro, on n'y a pas renoncé — "
                u"« abandonnée » dirait le contraire de ce qui s'est passé.")
        return valeur, reste, False, u""

    for motif, valeur, pourquoi in AMBIGUS:
        m = re.match(_sansacc(motif), bas) or re.match(motif, t, re.I)
        if m:
            reste = t[m.end():].strip(u" ·—–-,.:;")
            return valeur, reste, True, pourquoi

    return u"", brut, True, u"aucune valeur reconnue en tête de cellule"


# ─────────────────────────────────────────────── parcourir les cahiers
def tables_actions(livres):
    u"""Les tables d'actions des CAHIERS, et l'index de leur colonne d'état.

    Les quatre registres dérivés n'en ont plus (`couverture.py --registres` les
    réduit à quatre colonnes) : il n'y a donc qu'un seul endroit à toucher, et
    c'est ce qui rend l'opération sûre."""
    for b in livres:
        bid = str(b.get("id") or u"")
        if not bid.startswith(("affaire-", "nera-")):
            continue
        for t in (b.get("tables") or []):
            g = C.genre_de(t.get("titre") or u"") or C.genre_de(b.get("titre") or u"")
            if g != "action":
                continue
            cols = t.get("colonnes") or []
            i_etat = C.col(cols, u"^état$|^etat$|où ça en est|ou ca en est")
            if i_etat is None:
                continue
            yield b, t, cols, i_etat


def cellules(ligne):
    return ligne if isinstance(ligne, list) else (ligne.get("cellules") or [])


def passer(livres, appliquer_ambigus=False, ecrire=False):
    u"""Le passage complet. Ne touche `livres` que si `ecrire`.

    IDEMPOTENT PAR CONSTRUCTION : une cellule déjà réduite à son mot rend un
    `reste` vide, donc rien à verser en note ; la date extraite est la même ;
    et les colonnes ne se créent qu'une fois puisqu'on les cherche par en-tête.
    """
    rap = {"valeurs": collections.Counter(), "par_affaire": collections.Counter(),
           "ambigus": [], "dates": [], "touchees": 0, "lignes": 0,
           "colonnes_creees": [], "hors_vocabulaire": collections.Counter()}

    for b, t, cols, i_etat in tables_actions(livres):
        titre_aff = C.nu(b.get("titre"))
        # les deux colonnes d'appoint, créées une seule fois
        i_jour = C.col(cols, u"^jour fait$")
        i_note = C.col(cols, u"^note$")
        neuves = []
        if i_jour is None:
            i_jour = len(cols) + len(neuves)
            neuves.append(COL_JOUR)
        if i_note is None:
            i_note = len(cols) + len(neuves)
            neuves.append(COL_NOTE)
        if neuves:
            rap["colonnes_creees"].append((str(b.get("id")), C.nu(t.get("titre")),
                                           list(neuves)))
        largeur = len(cols) + len(neuves)

        for l in (t.get("lignes") or []):
            c = cellules(l)
            if len(c) < 2 or not C.nu(c[0]) or not C.nu(c[1]):
                continue
            if not C.NUM.search(C.nu(c[0])):
                continue
            rap["lignes"] += 1
            brut = C.nu(c[i_etat]) if i_etat < len(c) else u""
            rap["valeurs"][brut] += 1
            valeur, note, ambigu, motif = lire(brut)
            num = C.NUM.search(C.nu(c[0])).group(1)

            if ambigu:
                rap["ambigus"].append((num, titre_aff, brut, valeur, motif))
                if not appliquer_ambigus or not valeur:
                    if brut and brut not in VOCABULAIRE:
                        rap["hors_vocabulaire"][brut] += 1
                    continue

            jour = date_du_monde(brut) if valeur in (u"faite", u"close",
                                                     u"abandonnée") else u""
            # ce que la ligne PORTE déjà, pour savoir si quelque chose bouge
            av_etat = brut
            av_jour = C.nu(c[i_jour]) if i_jour < len(c) else u""
            av_note = C.nu(c[i_note]) if i_note < len(c) else u""
            ap_jour = av_jour or jour
            ap_note = av_note if (not note or note in av_note) else \
                ((av_note + u" — " + note) if av_note else note)
            if (av_etat, av_jour, av_note) == (valeur, ap_jour, ap_note):
                continue
            rap["touchees"] += 1
            rap["par_affaire"][titre_aff] += 1
            if jour and not av_jour:
                rap["dates"].append((num, jour, brut[:90]))
            if not ecrire:
                continue
            while len(c) < largeur:
                c.append(u"")
            c[i_etat], c[i_jour], c[i_note] = valeur, ap_jour, ap_note
            if isinstance(l, dict):
                l["cellules"] = c
        if ecrire and neuves:
            t["colonnes"] = list(cols) + neuves
            for l in (t.get("lignes") or []):
                c = cellules(l)
                while len(c) < largeur:
                    c.append(u"")
                if isinstance(l, dict):
                    l["cellules"] = c
    return rap


# ─────────────────────────────────────────────── écrire, sous garde
def verser(session):
    try:
        session.sauver()
    except bibliotheque.BibliothequeModifiee as exc:
        sortie(u"\n‼ %s\n" % exc)
        return False
    return True


# ─────────────────────────────────────────────── le rapport
_SORTIE = []


def sortie(s):
    _SORTIE.append(s)


def rapport(rap, applique):
    u"""Le rapport, en markdown, écrit dans un fichier ou sur la sortie. Écrire
    dans un fichier n'est pas un confort : le shell de cette maison est en
    cp1252 et la moitié de ces cellules porte un emoji."""
    o = []
    o.append(u"# Chantier A — la colonne d'état des actions\n")
    o.append(u"%s · %d action(s) lue(s) dans les cahiers\n"
             % (time.strftime("%Y-%m-%d %H:%M"), rap["lignes"]))
    o.append(u"\n**%d valeurs distinctes** · **%d ligne(s) touchée(s)** · "
             u"**%d ambigu(s)** laissés à l'arbitrage\n"
             % (len(rap["valeurs"]), rap["touchees"], len(rap["ambigus"])))
    o.append(u"\n%s\n" % (u"APPLIQUÉ." if applique else
                          u"À BLANC — rien n'a été écrit."))

    o.append(u"\n## Le vocabulaire cible\n\n")
    o.append(u" · ".join(u"`%s`" % v for v in VOCABULAIRE) + u"\n")

    o.append(u"\n## Les valeurs présentes aujourd'hui\n\n")
    o.append(u"| n | valeur actuelle (tronquée) | cible | statut |\n|---|---|---|---|\n")
    for v, n in sorted(rap["valeurs"].items(), key=lambda x: (-x[1], x[0])):
        val, note, amb, motif = lire(v)
        aff = (v or u"(vide)").replace(u"|", u"\\|")
        o.append(u"| %d | %s | %s | %s |\n"
                 % (n, aff[:120], val or u"—",
                    u"**AMBIGU**" if amb else u"clair"))

    o.append(u"\n## Les ambigus — recommandation et motif\n\n")
    vus = {}
    for num, aff, brut, val, motif in rap["ambigus"]:
        vus.setdefault(motif, []).append((num, aff, brut, val))
    for motif, l in sorted(vus.items(), key=lambda x: -len(x[1])):
        o.append(u"\n### %d ligne(s) — recommandation : `%s`\n\n%s\n\n"
                 % (len(l), l[0][3] or u"— (rien à recommander)", motif))
        for num, aff, brut, val in sorted(l):
            o.append(u"- **%s** *(%s)* — %s\n" % (num, aff[:40], brut[:190]))

    o.append(u"\n## Lignes touchées, par affaire\n\n| affaire | lignes |\n|---|---|\n")
    for a, n in sorted(rap["par_affaire"].items(), key=lambda x: (-x[1], x[0])):
        o.append(u"| %s | %d |\n" % (a[:60], n))

    o.append(u"\n## Dates extraites — échantillon de 20\n\n"
             u"| n° | jour fait | d'où on le tire |\n|---|---|---|\n")
    for num, jour, src in rap["dates"][:20]:
        o.append(u"| %s | %s | %s |\n" % (num, jour, src.replace(u"|", u"\\|")))
    o.append(u"\n%d date(s) extraite(s) en tout.\n" % len(rap["dates"]))

    if rap["colonnes_creees"]:
        o.append(u"\n## Colonnes à créer — %d table(s) d'actions\n\n"
                 % len(rap["colonnes_creees"]))
        for bid, tt, n in rap["colonnes_creees"]:
            o.append(u"- `%s` / %s → %s\n" % (bid, tt[:44], u" · ".join(n)))

    o.append(u"""
## La garde à poser dans `tick.py --verifier`

**Où, exactement.** Deux gestes dans `scripts/tick.py` :

1. **La fonction** se colle juste APRÈS `verifier_registres_derives`, qui se
   termine à la ligne 2274 (le dernier `r.dire(...)` du `for bid, a, n in
   ecarts:`) — donc à la ligne 2275, avant le `def` suivant. C'est son voisin
   naturel : les deux gardent la même matière, l'une la forme de l'index,
   l'autre la tenue des cellules.
2. **L'appel** s'ajoute dans la liste des vérificateurs, **ligne 2364**, juste
   après `    verifier_registres_derives(e, r)` :

```python
    verifier_etats_du_plan(e, r)
```

`e.books` est déjà chargé par le contexte (`tick.py` ligne 224) : la garde ne
relit rien du disque, et elle ne coûte donc que le parcours des 43 tables
d'actions.

**Gravité.** `grave` — c'est ce qui fait échouer l'audit, et c'est voulu : une
valeur hors vocabulaire ne dégrade pas un affichage, elle rend un compte
impossible. Passer à `avertissement` reviendrait à rouvrir la porte par
laquelle la prose est entrée.

```python
""" + GARDE + u"```\n")
    return u"".join(o)


# ─────────────────────────────────────────────── la garde pour tick.py
GARDE = u'''def verifier_etats_du_plan(e, r):
    """La colonne d'etat d'une action ne porte QU'UN MOT, pris dans six.

    Elle a ete un champ de recit pendant une lune : deux cents signes de prose
    datee la ou `etat_du_plan.py` attend un mot, dix-sept pieces ecrivant
    « fait » de six facons, et la date de realisation noyee dans le texte —
    donc rien qui se compte, donc personne capable de dire ce qui a ete fait
    cette lune. Sans cette garde, la prose y revient en trois jours : elle
    revient toujours, parce qu'un homme qui a quelque chose a dire l'ecrit la
    ou il regarde. Ce qu'il a a dire va desormais en `📝 Note`, et la date en
    `📅 Jour fait`.
    """
    try:
                from plan.expose import couverture
    except ImportError:
        return
    VOC = (u"\\u00e0 faire", u"en cours", u"bloqu\\u00e9e", u"faite", u"close",
           u"abandonn\\u00e9e")
    for livre in e.books:
        bid = str(livre.get("id") or "")
        if not bid.startswith(("affaire-", "nera-")):
            continue
        for t in (livre.get("tables") or []):
            g = (couverture.genre_de((t or {}).get("titre") or "")
                 or couverture.genre_de(livre.get("titre") or ""))
            if g != "action":
                continue
            cols = (t or {}).get("colonnes") or []
            i = couverture.col(cols, u"^\\u00e9tat$|^etat$|o\\u00f9 \\u00e7a en est|ou ca en est")
            if i is None:
                continue
            for ligne in (t.get("lignes") or []):
                c = [couverture.nu(x) for x in ((ligne if isinstance(ligne, list)
                                                 else (ligne or {}).get("cellules")) or [])]
                if len(c) < 2 or not c[0] or not c[1] or i >= len(c):
                    continue
                m = couverture.NUM.search(c[0])
                if not m or c[i] in VOC:
                    continue
                r.dire("grave", "plan {}".format(m.group(1)),
                       "etat hors vocabulaire : {!r}. Six valeurs et pas une de "
                       "plus — a faire / en cours / bloquee / faite / close / "
                       "abandonnee. La prose va en « Note », la date en « Jour "
                       "fait » : `python scripts/plan/normaliser_etats.py`"
                       .format(c[i][:70]))
'''


if __name__ == "__main__":
    args = sys.argv[1:]
    vraiment = "--vraiment" in args
    amb = "--ambigus" in args
    dest = args[args.index("--rapport") + 1] if "--rapport" in args else None

    session = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    livres = session.livres
    rap = passer(livres, appliquer_ambigus=amb, ecrire=vraiment)
    txt = rapport(rap, vraiment)

    if vraiment:
        if not verser(session):
            sys.exit(1)
    else:
        sortie(u"--vraiment absent : rien n'a été écrit.\n")

    if dest:
        with io.open(dest, "w", encoding="utf-8") as f:
            f.write(txt)
        sortie(u"rapport : %s\n" % dest)
    else:
        sortie(txt)
    out = io.open(sys.stdout.fileno(), "w", encoding="utf-8", errors="replace",
                  closefd=False)
    out.write(u"".join(_SORTIE))
    out.flush()
