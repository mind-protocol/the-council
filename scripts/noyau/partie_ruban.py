#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
partie_ruban.py — la partie dans le TEMPS, et non sur le plateau.

Il existait deux vues de la position — les cartes de l'onglet « Le conseil » et
l'arbre de `partie_ascii.py` —, toutes deux SPATIALES : elles disent ce qui
tient maintenant, et rien de ce qui s'est passé. Or les deux questions qui
arrêtent une partie sont temporelles, et aucune des deux vues n'y répond :

    « pourquoi je ne peux rien jouer ? »   — mes pièces sont prises ailleurs
    « où est passé mon tempo ? »           — j'ai dépensé des tours à me reprendre

Ce module replie la partie tour par tour et rend deux bandes superposées, sur
le même axe :

    LES COUPS   une voie par camp ; ce qui compte est plein, ce qui est gratuit
                (justifier, demander, consigne, la réponse à un ❓) est en creux.
                Un tour sans coup compté se voit comme un trou.
    LES PIÈCES  une ligne par pièce, sa vie du premier tour au dernier : libre,
                engagée (par quoi), gelée, détruite. C'est le ruban qui explique
                les refus — une pièce engagée par un blocage tombé mais non
                retiré reste prise, et cela ne se lit nulle part ailleurs.

On NE REJOUE PAS les règles : on rappelle `_appliquer` ligne à ligne sur une
partie vide et l'on photographie l'état des ressources à chaque passage de
tour. Le repli reste donc celui du greffe, et cette vue ne peut pas diverger.
"""
import io
import json
import os

from partie_greffe import COUPS_COMPTES, EMOJI_CAMP, EMOJI_COUP, Partie, liste

import partie_cartes


# ------------------------------------------------------------------ le repli
def _photo(p):
    """L'état de chaque ressource à cet instant, réduit à ce qui se dessine."""
    out = {}
    for rid, r in p.ressources.items():
        if r.get("en_attente"):
            etat = "attente"
        elif r.get("detruite"):
            etat = "detruite"
        elif r.get("engagee_par"):
            etat = "engagee"
        elif r.get("gel_jusqu", 0) > p.tour:
            etat = "gelee"
        else:
            etat = "libre"
        out[rid] = {"etat": etat, "par": list(r.get("engagee_par") or [])}
    return out


def replier(chemin):
    """Rend {tours:[…], pieces:{…}, camps:[…]} — un pas par tour joué."""
    p = Partie(os.devnull if os.path.exists(os.devnull) else chemin + ".vide")
    p.chemin = chemin
    lignes = []
    with io.open(chemin, "r", encoding="utf-8") as f:
        for brut in f:
            brut = brut.strip()
            if brut:
                lignes.append(json.loads(brut))

    tours, courant = [], None

    def ouvrir(n):
        return {"tour": n, "coups": [], "marques": [], "pieces": {}}

    courant = ouvrir(1)
    for l in lignes:
        p.lignes.append(l)
        p._appliquer(l)
        coup = l.get("coup")
        if coup == "tour":
            courant["pieces"] = _photo(p)
            tours.append(courant)
            courant = ouvrir(p.tour)
            continue
        if coup == "constater":
            e = p.etats.get(l.get("etat")) or {}
            courant["marques"].append({
                "camp": e.get("camp") or "arbitre",
                "vrai": l.get("verdict") == "vrai",
                "texte": partie_cartes.titre(p, l.get("etat")),
                "motif": l.get("motif") or ""})
            continue
        if coup in ("arbitrer",):
            continue
        sur = l.get("sur") or l.get("cible") or ""
        courant["coups"].append({
            "camp": l.get("camp") or "?",
            "coup": coup,
            "n": l.get("n"),
            "emoji": EMOJI_COUP.get(coup, "•"),
            "compte": coup in COUPS_COMPTES and l.get("camp") != "arbitre"
                      and not l.get("repond"),
            "id": l.get("id") or "",
            "sur": partie_cartes.titre(p, sur) if sur else "",
            "engage": [partie_cartes.titre(p, x) for x in liste(l.get("engage"))],
            "ouvre": [partie_cartes.titre(p, x) for x in liste(l.get("ouvre"))],
            "repond": l.get("repond"),
            "titre": (l.get("texte") or partie_cartes.titre(p, l.get("id") or "")
                      or coup)})
    if courant["coups"] or courant["marques"]:
        courant["pieces"] = _photo(p)
        tours.append(courant)

    camps = [c for c in p.camps() if c != "arbitre"]
    noms = {}
    for rid, r in sorted(p.ressources.items()):
        noms[rid] = {"titre": partie_cartes.titre(p, rid), "camp": r["camp"],
                     "emoji": partie_cartes.carte_piece(p, rid).get("emoji", "📦")}
    return {"partie": os.path.splitext(os.path.basename(chemin))[0],
            "camps": camps, "tours": tours, "pieces": noms,
            "trone": p.tenu_par(),
            "titres": {i: partie_cartes.titre(p, i) for i in
                       list(p.blocages) + list(p.cles) + list(p.menaces) + list(p.etats)}}


# ------------------------------------------------------------------- le rendu
COULEURS = {"libre": "#8aa87e", "engagee": "#c0873a", "gelee": "#7d8fa8",
            "detruite": "#a34a3a", "attente": "#9a8f7a", "absente": ""}
DITS = {"libre": "libre", "engagee": "engagée", "gelee": "gelée",
        "detruite": "perdue", "attente": "attend l'arbitrage", "absente": "pas encore au livre"}


def _ech(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _info_coup(g, tour):
    """Ce qu'un jeton de coup dit quand on le regarde : le verbe, ce qu'il vise,
    ce qu'il engage, et son numéro de ligne — de quoi retrouver le coup au livre
    sans quitter le ruban."""
    x = g[0]
    tete = "<b>%s %s</b>" % (_ech(x["emoji"]), _ech(x["coup"]))
    tete += " <span class=q style='display:inline'>%s</span>" % (
        "coup compté" if x["compte"] else "gratuit")
    corps = []
    for y in g:
        bout = _ech(y["titre"])
        if y["sur"]:
            bout += " <span class=q style='display:inline'>→ sur « %s »</span>" % _ech(y["sur"])
        if y["ouvre"]:
            bout += " <span class=q style='display:inline'>→ ouvre « %s »</span>" % _ech(", ".join(y["ouvre"]))
        corps.append("<div>%s</div>" % bout)
    pied = ["tour %d" % tour, "ligne %s" % (x["n"] if len(g) == 1 else
            "%s–%s" % (g[0]["n"], g[-1]["n"]))]
    if x["engage"]:
        pied.append("engage « %s »" % ", ".join(x["engage"]))
    if x["repond"]:
        pied.append("répond à la ligne %s, donc gratuit" % x["repond"])
    return tete + "".join(corps) + "<span class=q>%s</span>" % " · ".join(pied)


def rendre(d):
    """Le ruban, en une page qui tient toute seule — aucun script, aucun réseau."""
    tours = d["tours"]
    n = len(tours)
    larg = max(96, min(150, int(1500 / max(n, 1))))
    o = []
    a = o.append
    a("<!doctype html><html lang=fr><meta charset=utf-8>")
    a("<title>Ruban — %s</title>" % _ech(d["partie"]))
    a("""<style>
:root{--fond:#f4eee2;--encre:#2b2119;--gris:#7a6a55;--ligne:#d9cfbc;--carte:#fffbf2}
@media (prefers-color-scheme:dark){:root{--fond:#171310;--encre:#e6dbc6;--gris:#a8977c;--ligne:#3a322a;--carte:#1f1a15}}
*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--encre);font:14px/1.4 Georgia,"Times New Roman",serif}
header{padding:14px 20px;border-bottom:1px solid var(--ligne)}
h1{font-size:17px;margin:0 0 3px;font-weight:normal}
header .k{color:var(--gris);font-size:12.5px}
main{padding:12px 20px 40px;overflow-x:auto}
table{border-collapse:collapse}
th,td{padding:0;vertical-align:top}
th.t{font-weight:normal;font-size:11px;color:var(--gris);text-align:center;
  border-bottom:1px solid var(--ligne);padding:2px 0 4px}
td.lab,th.lab{position:sticky;left:0;background:var(--fond);z-index:2;
  padding-right:10px;font-size:12px;white-space:nowrap;max-width:230px;overflow:hidden;text-overflow:ellipsis}
.voie td{border-bottom:1px solid var(--ligne);padding:3px 3px 5px}
.cp{display:block;font-size:11px;line-height:1.25;margin:2px 0;padding:3px 5px;border-radius:3px;
  border:1px solid var(--ligne);background:var(--carte)}
.cp.compte{border-color:currentColor;font-weight:600}
.cp.gratuit{opacity:.62;border-style:dashed}
.rien{color:var(--gris);font-size:11px;font-style:italic;text-align:center;display:block;padding:4px 0}
.bande td{padding:0 1px}
.b{height:15px;border-radius:2px;background:var(--ligne);opacity:.35}
.b.on{opacity:1}
.pl{font-size:11.5px}
.marque{margin:3px 0;padding:3px 5px;border-radius:3px;font-size:11px;line-height:1.25;
  border-left:3px solid #6f9c62;background:color-mix(in srgb,#6f9c62 14%,transparent)}
.marque.faux{border-left-color:#a34a3a;background:color-mix(in srgb,#a34a3a 14%,transparent)}
h2{font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--gris);
  font-weight:normal;margin:22px 0 6px}
.leg{color:var(--gris);font-size:11.5px;margin:6px 0 0}
.leg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 3px 0 12px;vertical-align:-1px}
/* LE VOLET. Le `title` du navigateur mettait une seconde à paraître, coupait
   au-delà d'une ligne et ne savait pas mettre un mot en gras — sur un ruban où
   TOUT le détail est au survol, c'était la moitié de la vue rendue illisible.
   Celui-ci paraît sans délai, tient plusieurs lignes, et se pose du côté où il
   y a la place. Il ne prend jamais le curseur. */
#volet{position:fixed;z-index:99;max-width:380px;pointer-events:none;display:none;
  background:var(--carte);border:1px solid var(--encre);border-radius:4px;
  padding:7px 9px;box-shadow:0 6px 18px rgba(0,0,0,.28);font-size:12px;line-height:1.35}
#volet b{font-weight:600}
#volet .q{color:var(--gris);font-size:11px;display:block;margin-top:3px}
[data-info]{cursor:help}
</style>""")
    trone = d["trone"]
    a("<header><h1>%s</h1><div class=k>%d tours · %s · 👑 %s</div></header><main>" % (
        _ech(d["partie"]), n,
        " ".join("%s %s" % (EMOJI_CAMP[c], _ech(c)) for c in d["camps"]),
        ("%s %s" % (EMOJI_CAMP[trone], _ech(trone))) if trone else "personne"))

    # ---- les coups, une voie par camp
    a("<h2>Les coups — ce qui compte est plein, ce qui est gratuit est en creux</h2>")
    a("<table><tr><th class=lab></th>")
    for t in tours:
        a("<th class=t style='width:%dpx'>tour %d</th>" % (larg, t["tour"]))
    a("</tr>")
    for c in d["camps"]:
        a("<tr class=voie><td class=lab>%s %s</td>" % (EMOJI_CAMP[c], _ech(c)))
        for t in tours:
            siens = [x for x in t["coups"] if x["camp"] == c]
            if not siens:
                a("<td><span class=rien>—</span></td>")
                continue
            a("<td>")
            # Les coups GRATUITS du même verbe se replient en un seul jeton
            # compté : un tour d'ouverture pose six `demander` d'affilée, et six
            # jetons identiques poussaient la colonne à cinq fois sa hauteur
            # sans rien apprendre. Le détail reste au survol, ligne à ligne.
            grp = []
            for x in siens:
                if grp and not x["compte"] and not grp[-1][0]["compte"]                         and grp[-1][0]["coup"] == x["coup"]:
                    grp[-1].append(x)
                else:
                    grp.append([x])
            for g in grp:
                x = g[0]
                a("<span class='cp %s' data-info=\"%s\">%s %s%s</span>" % (
                    "compte" if x["compte"] else "gratuit",
                    _ech(_info_coup(g, t["tour"])), x["emoji"],
                    _ech(x["coup"]), (" ×%d" % len(g)) if len(g) > 1 else ""))
            a("</td>")
        a("</tr>")
    a("<tr class=voie><td class=lab>✅ constats</td>")
    for t in tours:
        if not t["marques"]:
            a("<td></td>")
            continue
        a("<td>")
        for m in t["marques"]:
            a("<div class='marque%s' data-info=\"%s\">%s %s</div>" % (
                "" if m["vrai"] else " faux",
                _ech("<b>%s</b> %s<span class=q>%s</span>" % (
                    "✅ constat : vrai" if m["vrai"] else "❌ constat : faux",
                    _ech(m["texte"]), _ech(m["motif"]))),
                EMOJI_CAMP[m["camp"]] if m["camp"] in EMOJI_CAMP else "",
                _ech(m["texte"][:46] + ("…" if len(m["texte"]) > 46 else ""))))
        a("</td>")
    a("</tr></table>")

    # ---- les pièces, une ligne chacune
    a("<h2>Les pièces — ce qui était pris, et par quoi</h2>")
    a("<table>")
    for rid, meta in sorted(d["pieces"].items(), key=lambda kv: (kv[1]["camp"], kv[1]["titre"])):
        a("<tr class=bande><td class='lab pl'>%s %s %s</td>" % (
            EMOJI_CAMP[meta["camp"]], meta["emoji"], _ech(meta["titre"])))
        for t in tours:
            e = t["pieces"].get(rid, {"etat": "absente", "par": []})
            par = ", ".join(d["titres"].get(x, x) for x in e["par"])
            info = "<b>%s</b><span class=q>tour %d · %s%s</span>" % (
                _ech(meta["emoji"] + " " + meta["titre"]), t["tour"], DITS[e["etat"]],
                (" par « %s »" % _ech(par)) if par else "")
            a("<td style='width:%dpx'><div class='b%s' style='background:%s' data-info=\"%s\"></div></td>" % (
                larg, "" if e["etat"] == "absente" else " on",
                COULEURS.get(e["etat"]) or "transparent", _ech(info)))
        a("</tr>")
    a("</table>")
    a("<p class=leg>")
    for k in ("libre", "engagee", "gelee", "attente", "detruite"):
        a("<i style='background:%s'></i>%s" % (COULEURS[k], DITS[k]))
    a("</p></main><div id=volet></div>")
    a("""<script>
(function(){
  var v=document.getElementById("volet");
  document.addEventListener("mouseover",function(e){
    var c=e.target.closest("[data-info]");
    if(!c){v.style.display="none";return;}
    v.innerHTML=c.getAttribute("data-info");
    v.style.display="block";
    poser(e);
  });
  document.addEventListener("mousemove",function(e){
    if(v.style.display==="block") poser(e);
  });
  // Il se pose du côté où il y a la place : collé au bord droit, un volet de
  // 380 px sur une pièce du dernier tour sortait de l'écran et se lisait à moitié.
  function poser(e){
    var b=v.getBoundingClientRect();
    var x=e.clientX+14, y=e.clientY+16;
    if(x+b.width>innerWidth-8) x=e.clientX-b.width-14;
    if(y+b.height>innerHeight-8) y=e.clientY-b.height-16;
    v.style.left=Math.max(6,x)+"px"; v.style.top=Math.max(6,y)+"px";
  }
})();
</script></html>""")
    return "\n".join(o)
