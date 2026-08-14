# -*- coding: utf-8 -*-
"""CE QUI PESE — les osts, les betes et les coques, au jour dit.

    python scripts/figure_forces.py > ecrans/dessins/ce-qui-pese.svg

POURQUOI CETTE FIGURE. La table peinte repond a « ou », jamais a « combien
contre combien » : dix jetons poses sur dix places ne se comparent pas a l'oeil,
et c'est pourtant la seule question qu'on se pose avant d'envoyer une bete.
Des COLONNES, donc — une des quatre figures de pensee de l'epoque — et les
hommes comptes en traits de cent, comme un mestre compte des lances.

CE QU'ELLE NE PORTE PAS. Rien que le joueur ne sache : elle est batie sur
`etat/joueurs/<siege>/jetons.json`, c'est-a-dire sur ce qu'il CROIT tenir, et
elle garde la marque de sa croyance — trait plein pour ce qui est sur, trait
hachure pour ce qui n'est que rapporte. Une figure qui lisserait les deux
mentirait plus qu'un chiffre faux : elle ferait passer une rumeur pour un compte.
"""
import io, json, os, sys

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

L, H = 900, 620
MARGE = 54
PAR_TRAIT = 100          # un trait de plume vaut cent hommes
COL = {"noir": "#7a1c1c", "vert": "#1f5132"}


def charger(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    siege = "rhaenyra"
    for i, a in enumerate(argv):
        if a == "--siege" and i + 1 < len(argv):
            siege = argv[i + 1]
    d = charger(os.path.join(racine, "etat", "joueurs", siege, "jetons.json"))
    jetons = d.get("jetons", []) if isinstance(d, dict) else d
    traits = d.get("traits", []) if isinstance(d, dict) else []
    monde = charger(os.path.join(racine, "etat", "monde.json"))
    dt = monde.get("date", {})

    HOMMES = ("armee", "cavalerie", "garnison", "camp")
    rangs = {"noir": [], "vert": []}
    betes = {"noir": 0, "vert": 0}
    coques = {"noir": [], "vert": []}
    for j in jetons:
        camp = j.get("camp")
        if camp not in rangs:
            continue
        g, f = j.get("genre"), j.get("force")
        if g == "dragon":
            betes[camp] = max(betes[camp], f or 0)
        elif g == "flotte":
            coques[camp].append(j)
        elif g in HOMMES and f:
            rangs[camp].append(j)
    for c in rangs:
        rangs[c].sort(key=lambda j: -(j.get("force") or 0))
    plus = max([j.get("force") or 0 for c in rangs for j in rangs[c]] or [1])

    s = ['<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
         'font-family="Georgia,serif">' % (L, H)]
    s.append('<rect width="%d" height="%d" fill="#efe7d7"/>' % (L, H))
    s.append('<text x="%d" y="40" font-size="21" fill="#2b2118" '
             'letter-spacing="1.5">CE QUI PESE — %de jour, %de lune, an %d</text>'
             % (MARGE, dt.get("jour", 0), dt.get("lune", 0), dt.get("annee", 0)))
    s.append('<text x="%d" y="62" font-size="12" fill="#6b5c4a" font-style="italic">'
             'un trait de plume vaut cent hommes · trait plein, ce qui est sûr · '
             'trait hachuré, ce qui est seulement rapporté</text>' % MARGE)

    y = 100
    for camp, titre in (("noir", "NOUS"), ("vert", "EUX")):
        s.append('<text x="%d" y="%d" font-size="15" fill="%s" letter-spacing="2">'
                 '%s</text>' % (MARGE, y, COL[camp], titre))
        # les betes, en tetes de dragon comptees une a une
        s.append('<text x="%d" y="%d" font-size="12" fill="#4a3f33">%d dragon(s)</text>'
                 % (MARGE + 78, y, betes[camp]))
        for k in range(betes[camp]):
            x = MARGE + 178 + k * 26
            s.append('<g transform="translate(%d,%d)" fill="none" stroke="%s" '
                     'stroke-width="1.7" stroke-linejoin="round">'
                     '<path d="M-9-2.6C-5.4-5.2-2.6-3-0 2.6 2.6-3 5.4-5.2 9-2.6"/>'
                     '<path d="M0 2.6V6"/></g>' % (x, y - 4, COL[camp]))
        y += 26
        for j in rangs[camp]:
            f = j.get("force") or 0
            sur = (j.get("certitude") or "sure") == "sure"
            larg = (L - MARGE * 2 - 300) * (f / float(plus))
            n = max(1, int(round(f / float(PAR_TRAIT))))
            pas = larg / n if n else larg
            s.append('<text x="%d" y="%d" font-size="12.5" fill="#2b2118">%s</text>'
                     % (MARGE, y + 4, (j.get("nom") or j.get("ou") or "?")[:34]))
            s.append('<text x="%d" y="%d" font-size="12.5" fill="#4a3f33" '
                     'text-anchor="end">%s</text>' % (MARGE + 290, y + 4,
                     "{:,}".format(f).replace(",", " ")))
            for k in range(n):
                x = MARGE + 308 + k * pas
                s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" '
                         'stroke-width="%s"%s/>'
                         % (x, y - 7, x, y + 6, COL[camp], "2.1" if sur else "1.2",
                            "" if sur else ' stroke-dasharray="2.5 2.5"'))
            if not sur:
                s.append('<text x="%.1f" y="%d" font-size="10.5" fill="#8a7963" '
                         'font-style="italic">rapporté</text>'
                         % (MARGE + 316 + n * pas, y + 4))
            y += 24
        y += 16

    # les coques, a part : ce sont elles qui brulent le mieux
    s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#c3b49b"/>'
             % (MARGE, y - 4, L - MARGE, y - 4))
    y += 20
    s.append('<text x="%d" y="%d" font-size="15" fill="#2b2118" letter-spacing="2">'
             'CE QUI FLOTTE</text>' % (MARGE, y))
    y += 22
    for camp in ("noir", "vert"):
        for j in coques[camp]:
            s.append('<text x="%d" y="%d" font-size="12.5" fill="%s">%s — %s coque(s)'
                     '%s</text>' % (MARGE + 14, y, COL[camp], (j.get("nom") or "?")[:40],
                     j.get("force"), "" if (j.get("certitude") or "sure") == "sure"
                     else " (rapporté)"))
            y += 21
    for t in traits:
        if t.get("genre") == "mer":
            s.append('<text x="%d" y="%d" font-size="12.5" fill="%s">%s — en mer vers %s'
                     '%s</text>' % (MARGE + 14, y, COL.get(t.get("camp"), "#4a3f33"),
                     (t.get("nom") or "?")[:40], t.get("vers") or "?",
                     "" if (t.get("certitude") or "sure") == "sure" else " (rapporté)"))
            y += 21
    s.append("</svg>")
    print("\n".join(s))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
