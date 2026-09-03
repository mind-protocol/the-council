# -*- coding: utf-8 -*-
# FLUX_SCRIBE — les gestes d'ecriture du fil qui ne dependent pas de la poussee
# en cours : les chemins de l'etat, la teinte et le portrait d'un locuteur,
# l'empreinte d'un dessin, la montre d'un livre (toucher, extrait), l'heure et
# l'avancee de la date. Matiere de scripts/append_flux.py (lot 2), deplacee
# telle quelle ; flux.py, le script, importe d'ici.
import hashlib
import io
import json
import os
import re
import unicodedata

from plan.expose import bibliotheque  # LA PORTE de plan/
from etat.expose import tables  # LA PORTE de etat/

racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
chemin = os.path.join(racine, "etat", "flux.jsonl")
monde_p = os.path.join(racine, "etat", "monde.json")
joueurs_p = os.path.join(racine, "etat", "joueurs.json")
horloges_p = os.path.join(racine, "etat", "horloges.json")
# Les affectations : ou les choses de la fiction se tiennent dans le monde en
# volume, et qui a le droit d'en voir le nom (voir scripts/affecter.py).
corps_p = os.path.join(racine, "etat", "corps.json")

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12


def teinte_du_nom(nom):
    """Une teinte stable tiree du nom. Meme calcul que `serveur/serveur.js`."""
    h = 0
    for c in (nom or ""):
        h = (h * 31 + ord(c)) % 360
    return h


def portrait(pid, nom=None):
    """Le SVG de quelqu'un — ou la silhouette anonyme : personne sans son rond.

    Faute de portrait dessine, on sert le gabarit `_defaut.svg` teinte d'apres
    le nom : deux inconnus ne se confondent pas, et le meme homme garde sa
    couleur d'un ecran a l'autre.
    """
    dossier = os.path.join(racine, "ecrans", "portraits")
    propre = os.path.join(dossier, pid + ".svg")
    if os.path.exists(propre):
        return io.open(propre, encoding="utf-8").read()
    gabarit = os.path.join(dossier, "_defaut.svg")
    if not os.path.exists(gabarit):
        return ""
    svg = io.open(gabarit, encoding="utf-8").read()
    h = teinte_du_nom(nom or pid)
    cle = re.sub(r"[^a-zA-Z0-9_-]", "", nom or pid) or "x"
    for marque, valeur in (
        ("{{CLE}}", cle),
        ("{{TEINTE}}", "hsl(%d,32%%,52%%)" % h),
        ("{{TEINTE_SOMBRE}}", "hsl(%d,22%%,22%%)" % h),
        ("{{TEINTE_ETOFFE}}", "hsl(%d,20%%,28%%)" % h),
        ("{{TEINTE_CHAIR}}", "hsl(%d,18%%,38%%)" % h),
        ("{{TEINTE_FOND}}", "hsl(%d,18%%,17%%)" % h),
    ):
        svg = svg.replace(marque, valeur)
    return svg


def empreinte_du_dessin(nom):
    """Fige la feuille SANS la coller dans le flux, et rend son nom fige.

    Un leve au pas pese deux cent mille signes. L'inliner dans l'item — comme on
    fait des portraits — mettrait ce poids dans CHAQUE ligne qui le montre, et
    le fil est append-only : on ne le reprend jamais. On copie donc le dessin
    sous un nom qui porte l'empreinte de son contenu, et l'item ne garde que ce
    nom ; le serveur l'inline au service (voir inlinerFigure dans serveur.js).

    Meme contenu, meme empreinte, meme fichier : montrer dix fois la meme feuille
    ne fait pas dix copies. Et une feuille refaite demain porte une empreinte
    neuve, donc n'ecrase pas celle qu'on a montree — ce que le joueur a vu ce
    jour-la reste ce qu'il a vu.
    """
    dossier = os.path.join(racine, "ecrans", "dessins")
    source = os.path.join(dossier, str(nom))
    if not os.path.exists(source):
        sys.stderr.write("append_flux : dessin introuvable — %s\n" % source)
        return nom
    brut = io.open(source, "rb").read()
    sceau = hashlib.sha1(brut).hexdigest()[:8]
    base, ext = os.path.splitext(os.path.basename(str(nom)))
    # Deja empreinte (on remontre la meme page) : rien a copier.
    if re.match(r"^[0-9a-f]{8}$", base.rsplit(".", 1)[-1] if "." in base else ""):
        return nom
    fige = "%s.%s%s" % (base, sceau, ext)
    cible = os.path.join(dossier, fige)
    if not os.path.exists(cible):
        with io.open(cible, "wb") as f:
            f.write(brut)
    return fige


def toucher_le_livre(lid, quand):
    """Estampe `date_maj` : ce volume vient de servir, il remonte sur la table.

    L'etagere se range du plus frais au plus ancien (voir books.js). Sans cette
    estampe, la fraicheur dependrait de la discipline du MJ — et un registre
    qu'on vient de tendre en plein conseil resterait enfoui au meme rang
    qu'hier. Montrer un volume est le signal le plus sur qu'il compte MAINTENANT.

    Fenetre etroite : on relit et on reecrit dans la meme milliseconde, parce
    qu'a deux MJ books.json a deux plumes.
    """
    try:
        session_livres = bibliotheque.ouvrir(tables.ETAT)
        books = session_livres.livres
        b = next((x for x in books if x.get("id") == lid), None)
        if not b:
            return
        b["date_maj"] = dict(quand)
        session_livres.sauver()
    except Exception as e:
        sys.stderr.write("append_flux : date_maj non posee sur %s (%s)\n" % (lid, e))


def extrait_du_livre(montre):
    """Ce qu'on laisse voir d'un volume — GELE a la seconde ou on le montre.

    MONTRER N'EST PAS DONNER. Un homme qui tend son registre a bout de bras ne
    lache pas son registre : le joueur voit la page, pas le volume. On resout
    donc l'extrait ICI, a l'ecriture, et le fil n'en garde qu'une citation. Le
    front ne va jamais relire books.json pour un item passe — sans quoi une
    ligne corrigee trois jours plus tard changerait retroactivement ce qu'on a
    montre au joueur, et ce serait lui mentir sur ce qu'il a vu.

    C'est l'inverse exact du choix fait pour la carte (illustration.js refuse de
    reposer les pieces d'une scene passee : la table dit l'etat d'aujourd'hui).
    Une table est un tableau de bord, un extrait est une piece a conviction.

    `montre` : {livre, page?, lignes?, mention?}. Sans precision, on prend la
    premiere page, ou les trois premieres lignes d'un registre.
    """
    lid = montre.get("livre")
    if not lid or "extrait" in montre:
        return
    try:
        books = bibliotheque.charger(tables.ETAT)
    except Exception:
        return
    b = next((x for x in books if x.get("id") == lid), None)
    if not b:
        sys.stderr.write("append_flux : aucun livre « %s » — rien de montre.\n" % lid)
        return

    e = {"titre": b.get("titre"), "sous_titre": b.get("sous_titre"),
         "type": b.get("type"), "couleur": b.get("couleur")}

    pages = b.get("pages") or []
    lignes = b.get("lignes") or []
    if montre.get("lignes") is not None or (lignes and montre.get("page") is None):
        # Un registre : on montre des LIGNES, avec leurs colonnes pour qu'elles
        # veuillent dire quelque chose. Un chiffre sans son en-tete n'est pas un
        # extrait, c'est un nombre.
        indices = montre.get("lignes")
        if indices is None:
            indices = list(range(min(3, len(lignes))))
        e["colonnes"] = b.get("colonnes") or []
        e["lignes"] = [lignes[i] for i in indices if 0 <= i < len(lignes)]
        e["total_lignes"] = len(lignes)
        e["indices"] = indices
    elif pages:
        n = montre.get("page") or 0
        if not (0 <= n < len(pages)):
            sys.stderr.write("append_flux : « %s » n'a pas de page %d.\n" % (lid, n))
            n = 0
        page = pages[n]
        if isinstance(page, dict) and page.get("figure"):
            e["figure"] = empreinte_du_dessin(page["figure"])
            e["legende"] = page.get("legende")
        else:
            e["texte"] = page
        e["page"] = n
        e["total_pages"] = len(pages)
    else:
        e["texte"] = None      # un volume encore vierge : c'est une information

    if montre.get("mention"):
        e["mention"] = montre["mention"]
    montre["extrait"] = e


def format_heure(minute):
    return "%dh%02d" % (minute // 60, minute % 60)


def avancer(date, minutes):
    """Avance la date de N minutes, en cascadant jour/lune/annee."""
    total = date.get("minute", 0) + minutes
    while total >= 1440:
        total -= 1440
        date["jour"] += 1
        if date["jour"] > JOURS_PAR_LUNE:
            date["jour"] = 1
            date["lune"] += 1
            if date["lune"] > LUNES_PAR_AN:
                date["lune"] = 1
                date["annee"] += 1
    date["minute"] = total
    return date


