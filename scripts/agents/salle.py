# -*- coding: utf-8 -*-
"""SALLE — ce qu'un habitant entend la ou il se tient (docs/habitant.md §2).

Deux ecritures, un seul calcul : QUI EST DANS LA PIECE.

  * le FIL DE SALLE — tout ce qui se dit et se fait devant lui entre dans
    `chambres/<lui>/fil/<date>-salle.md`. Jusqu'ici sa memoire ne gardait que
    ses propres sessions : un homme assis a un conseil de quarante repliques
    en ressortait sans une ligne, et le reveil suivant ne pouvait pas savoir
    ce qu'il avait entendu la veille.
  * les RELATIONS — deux habitants dans la meme piece ouvrent leurs
    `relations/<autre>/` tout seuls, avec un CONSTAT date et rien d'autre.
    Ce dossier est « ce que LUI retient de l'autre », donc subjectif : nous y
    ecrivons un fait verifiable, jamais un jugement. La suite est de sa main.

LE FILTRE EST LA CHAMBRE, ET IL BORNE TOUT (`chambre.existe`). On ne recopie
rien chez qui n'en a pas, et deux co-presents n'ouvrent une relation que s'ils
en ont une tous les deux. Mesure du 30.8 sur un parc jouet : a 20 habitants,
un reveil lit ses 19 relations en 5,8 ms ; a 100, 19 ms. Ce n'est pas la
charge qui compte ici, c'est que la memoire suive la population.

RIEN ICI NE FAIT FOI — regle de geographie de `chambre.py`. Le flux reste la
verite de ce qui s'est dit ; ceci en est le souvenir, chez chacun.

ON ACCUMULE, ON N'ECRIT QU'A LA FIN. `entendre()` ne touche pas le disque :
une poussee de quarante items dans une salle de vingt habitants ferait huit
cents ouvertures de fichier DANS LA PLUME DE L'HORLOGE. `deposer()` ecrit une
fois par chambre, a la fin de la poussee.
"""
import io
import os

from agents import chambre
from etat.expose import tables  # LA PORTE de etat/ — meme pour une lecture

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# Ce qui se PERCOIT dans une piece. Le hors-fiction n'y est pas : une question
# du joueur, une reponse du MJ, une pensee, les coulisses ne sont entendues de
# personne — c'est la meme liste que `HORS_FICTION` cote flux, et la meme
# raison. `pensee` est le cas d'ecole : elle ne coute pas une minute justement
# parce que nul ne l'entend.
TYPES_ENTENDUS = {
    "replique", "geste", "recit", "vous", "table", "ecrit", "marque",
    "breve", "evenement",
}

_tampon = {}         # pid -> [(jour, lieu, ligne)]
_rencontres = set()  # (a, b, lieu, jour) — paires co-presentes, a < b
_noms = None


def _nom(pid):
    """Le nom d'affichage, ou l'id. Lu une fois par processus."""
    global _noms
    if _noms is None:
        gens = tables.lire(os.path.join(RACINE, "etat", "personnages.json"), [])
        if isinstance(gens, dict):
            gens = gens.get("personnages") or []
        _noms = {p.get("id"): p.get("nom") for p in gens
                 if isinstance(p, dict) and p.get("id")}
    return _noms.get(pid) or pid


def _jour(quand):
    return u"%s.%s.%s" % (quand.get("annee"), quand.get("lune"),
                          quand.get("jour"))


def _heure(quand):
    m = int(quand.get("minute") or 0)
    return u"%dh%02d" % (m // 60, m % 60)


def _ligne(it, heure):
    """Une ligne de fil, dans la forme ou on la relira — jamais du JSON.

    Ce que l'habitant relit doit se lire comme une scene, pas comme un dump :
    c'est la meme lecon que les billets servis en percept. Un item qu'on ne
    sait pas rendre ne produit RIEN plutot qu'une ligne illisible.
    """
    t = it.get("type")
    texte = (it.get("texte") or "").strip()
    qui = it.get("locuteur_id") or it.get("acteur_id")
    if t == "vous" and texte:
        # Le joueur : sa parole est une parole, son acte est un geste.
        if it.get("mode") == "agir":
            return u"**%s** · *%s*" % (heure, texte)
        return u"**%s** · %s — « %s »" % (heure, _nom(qui) if qui else u"la reine",
                                          texte)
    if t == "replique" and texte:
        return u"**%s** · %s — « %s »" % (heure, _nom(qui), texte)
    if t == "geste" and texte:
        return u"**%s** · *%s*" % (heure, texte)
    if t in ("recit", "breve", "evenement") and texte:
        return u"**%s** · %s" % (heure, texte)
    if t == "table" and texte:
        return u"**%s** · %s, sur la carte : %s" % (heure, _nom(qui), texte)
    if t == "ecrit":
        titres = [e.get("titre") or e.get("quoi") or ""
                  for e in (it.get("entrees") or [])]
        porte = u" ; ".join(x for x in titres if x)
        return u"**%s** · %s%s" % (heure, texte or u"porté au registre",
                                   u" — " + porte if porte else u"")
    if t == "marque" and (it.get("titre") or texte):
        return u"**%s** · ⚑ %s" % (heure, it.get("titre") or texte)
    return None


def entendre(it, piece, auditeurs, quand):
    """Accumule ce que ces auditeurs viennent de percevoir. N'ECRIT RIEN.

    `auditeurs` est calcule par l'appelant (`scene/flux.py`), seul a tenir la
    regle de la piece (`meme_piece`) et le chuchotement : on ne la reecrit pas
    ici, une regle n'a qu'une source. Nous, on ne fait que ranger.
    """
    if not piece or not auditeurs:
        return
    presents = [p for p in dict.fromkeys(auditeurs) if p and chambre.existe(p)]
    if not presents:
        return
    lieu = piece.get("lieu") or piece.get("salle") or u"quelque part"
    jour = _jour(quand)
    # LA RENCONTRE SE NOTE MEME QUAND LA LIGNE NE SE REND PAS. Deux habitants
    # que la scene met dans la meme piece se sont vus, que l'item du moment
    # soit rendable ou non.
    for i, a in enumerate(presents):
        for b in presents[i + 1:]:
            _rencontres.add((min(a, b), max(a, b), lieu, jour))
    if it.get("type") not in TYPES_ENTENDUS:
        return
    ligne = _ligne(it, it.get("heure") or _heure(quand))
    if not ligne:
        return
    for pid in presents:
        _tampon.setdefault(pid, []).append((jour, lieu, ligne))


def deposer():
    """Ecrit une fois par chambre, ouvre les relations, et vide le tampon.

    Rend {fils, relations} pour que l'appelant puisse le dire sur sa sortie
    d'erreur — une ecriture muette est une ecriture qu'on croit faite.
    """
    fils = 0
    for pid, lignes in sorted(_tampon.items()):
        par_jour = {}
        for jour, lieu, ligne in lignes:
            par_jour.setdefault(jour, []).append((lieu, ligne))
        for jour, suite in sorted(par_jour.items()):
            dossier = os.path.join(chambre.chemin(pid), "fil")
            if not os.path.isdir(dossier):
                os.makedirs(dossier)
            fichier = os.path.join(dossier, u"%s-salle.md" % jour)
            neuf = not os.path.exists(fichier)
            # APPEND, jamais reecriture : une journee se remplit poussee apres
            # poussee, et le MJ pousse en tranches. Reecrire perdrait tout ce
            # qui precede la tranche courante.
            with io.open(fichier, "a", encoding="utf-8", newline="\n") as f:
                if neuf:
                    f.write(u"# Ce que j'ai entendu — %s\n\n"
                            u"*De ce que j'avais sous les yeux et les"
                            u" oreilles. Je peux m'être trompé sur ce que"
                            u" cela voulait dire.*\n" % jour)
                dernier = None
                for lieu, ligne in suite:
                    if lieu != dernier:
                        f.write(u"\n> 🏛 %s\n\n" % lieu)
                        dernier = lieu
                    f.write(ligne + u"\n")
            fils += 1
    relations = 0
    for a, b, lieu, jour in sorted(_rencontres):
        for qui, autre in ((a, b), (b, a)):
            fiche = os.path.join(chambre.chemin(qui), "relations", autre,
                                 "claude.md")
            if os.path.exists(fiche):
                continue
            chambre.canal(a, b)  # les deux cotes, canal canonique compris
            with io.open(fiche, "w", encoding="utf-8", newline="\n") as f:
                # UN CONSTAT, JAMAIS UNE OPINION. Cette fiche est « ce que LUI
                # retient de l'autre » : lui ecrire un jugement serait tenir sa
                # main. On pose un fait daté ; il ecrira le reste.
                f.write(u"# %s — ce que j'en retiens\n\n"
                        u"*Vu le %s, %s. Je n'ai encore rien écrit de lui.*\n"
                        % (_nom(autre), jour, lieu or u"je ne sais plus où"))
            relations += 1
    _tampon.clear()
    _rencontres.clear()
    return {"fils": fils, "relations": relations}
