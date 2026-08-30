# Exporte le Grand Plan en texte brut, un fichier par cahier, dans exports/.
#
# POURQUOI. Les cahiers vivent dans etat/books.json, qui est illisible a l'oeil
# et impossible a relire hors du jeu. Ici on rend le MEME contenu, sans rien
# resumer ni reordonner : titres, pages, tables, cellule par cellule.
#
# Usage :
#     python scripts/exporter_plan.py            # boite-grand-plan + boite-sujets
#     python scripts/exporter_plan.py --tout     # tous les livres de type plan
#     python scripts/exporter_plan.py --sortie <dossier>
import io, json, os, re, sys, unicodedata

import bibliotheque
from etat.expose import tables  # LA PORTE de etat/

# Deux etages de plus qu'a la racine : scripts/plan/ (voir scripts/CLAUDE.md).
racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOITES_DU_PLAN = ("boite-grand-plan", "boite-sujets")
LARGEUR = 100


def slug(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "sans-titre"


def trait(c="="):
    return c * LARGEUR


def plier(texte, largeur=LARGEUR, retrait=""):
    """Coupe aux espaces sans casser les mots, en gardant les sauts de ligne."""
    sorties = []
    for ligne in (texte or "").split("\n"):
        if not ligne.strip():
            sorties.append("")
            continue
        courante = retrait
        for mot in ligne.split(" "):
            if courante.strip() and len(courante) + len(mot) + 1 > largeur:
                sorties.append(courante.rstrip())
                courante = retrait + mot
            else:
                courante = (courante + " " + mot) if courante.strip() else (retrait + mot)
        sorties.append(courante.rstrip())
    return sorties


def cellules_courtes(lignes, colonnes):
    """Une table tient en grille si toutes ses cellules sont breves."""
    for l in lignes:
        for c in (l.get("cellules") or []):
            if len(str(c or "")) > 38:
                return False
    return len(colonnes) <= 6


def rendre_table(titre, colonnes, lignes, out):
    out.append("")
    out.append(trait("-"))
    out.append((titre or "TABLE").upper())
    out.append(trait("-"))
    if not lignes:
        out.append("  (vide)")
        return
    if cellules_courtes(lignes, colonnes):
        larg = []
        for i, c in enumerate(colonnes):
            m = len(str(c or ""))
            for l in lignes:
                cs = l.get("cellules") or []
                if i < len(cs):
                    m = max(m, len(str(cs[i] or "")))
            larg.append(min(m, 38))
        out.append("  " + " | ".join(str(c or "").ljust(larg[i]) for i, c in enumerate(colonnes)))
        out.append("  " + "-+-".join("-" * w for w in larg))
        for l in lignes:
            cs = l.get("cellules") or []
            out.append("  " + " | ".join(
                str(cs[i] if i < len(cs) else "" or "").ljust(larg[i]) for i in range(len(colonnes))))
            if l.get("note"):
                out.extend(plier("note : " + l["note"], LARGEUR - 6, "      "))
        return
    # Cellules longues : un enregistrement par bloc, chaque colonne nommee.
    for n, l in enumerate(lignes, 1):
        cs = l.get("cellules") or []
        if not any(str(c or "").strip() for c in cs):
            continue
        out.append("")
        out.append("  [%d]" % n)
        for i, col in enumerate(colonnes):
            val = str(cs[i] if i < len(cs) else "" or "").strip()
            if not val:
                continue
            etiquette = "    %s : " % (col or "?")
            corps = plier(val, LARGEUR - len(etiquette), " " * len(etiquette))
            if corps:
                out.append(etiquette + corps[0].strip())
                out.extend(corps[1:])
        if l.get("note"):
            out.extend(plier("note : " + l["note"], LARGEUR - 6, "      "))


def rendre_livre(b):
    out = []
    out.append(trait())
    out.append((b.get("titre") or b.get("id") or "").upper())
    out.append(trait())
    out.append("id      : %s" % b.get("id"))
    out.append("type    : %s" % b.get("type"))
    for cle in ("boite", "salle_id", "lieu_id", "acteur_id", "embleme"):
        if b.get(cle):
            out.append("%-7s : %s" % (cle, b[cle]))
    if b.get("sous_titre"):
        out.append("")
        out.extend(plier(b["sous_titre"]))
    for p in (b.get("pages") or []):
        out.append("")
        out.append(trait("-"))
        if isinstance(p, dict):
            # Une page peut etre une planche : un dessin et sa legende.
            if p.get("figure"):
                out.append("[figure : %s]" % p["figure"])
            for cle, val in p.items():
                if cle == "figure" or not isinstance(val, str):
                    continue
                out.extend(plier("%s : %s" % (cle, val)))
        else:
            out.extend(plier(p))
    if b.get("colonnes"):
        rendre_table("registre", b.get("colonnes") or [], b.get("lignes") or [], out)
    for t in (b.get("tables") or []):
        rendre_table(t.get("titre"), t.get("colonnes") or [], t.get("lignes") or [], out)
    out.append("")
    return "\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    tout = "--tout" in args
    sortie = os.path.join(racine, "exports")
    if "--sortie" in args:
        sortie = args[args.index("--sortie") + 1]
    if not os.path.isabs(sortie):
        sortie = os.path.join(racine, sortie)
    os.makedirs(sortie, exist_ok=True)

    livres = bibliotheque.charger(tables.ETAT)

    if tout:
        choisis = [b for b in livres if b.get("type") == "plan"]
    else:
        choisis = [b for b in livres
                   if b.get("boite") in BOITES_DU_PLAN or b.get("type") == "plan"]

    index = ["LE GRAND PLAN — PRISE DE PORT-REAL", trait(),
             "Export brut de etat/books.json. %d cahiers." % len(choisis), ""]
    ecrits = 0
    for b in sorted(choisis, key=lambda x: (x.get("boite") or "", x.get("id") or "")):
        nom = "%s.txt" % slug(b.get("id") or b.get("titre"))
        chemin = os.path.join(sortie, nom)
        io.open(chemin, "w", encoding="utf-8").write(rendre_livre(b))
        actions = sum(len(t.get("lignes", [])) for t in (b.get("tables") or [])
                      if "Actions" in (t.get("titre") or ""))
        index.append("%-46s %-44s %s" % (
            nom, (b.get("titre") or "")[:44],
            ("%d actions" % actions) if actions else ""))
        ecrits += 1

    io.open(os.path.join(sortie, "000-index.txt"), "w", encoding="utf-8").write(
        "\n".join(index) + "\n")
    print("%d cahiers exportes dans %s (+ 000-index.txt)" % (ecrits, sortie))


# L'ancien fichier appelait main() au chargement — le piege note dans
# scripts/CLAUDE.md (un import balayeur reecrivait exports/). La descente
# le ferme : seul l'appel par la facade (ou la porte) exporte.
