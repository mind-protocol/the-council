# -*- coding: utf-8 -*-
"""MISSION — le texte de mission servi a l'homme, l'etagere et le parloir
poses dans sa session, l'archive du prompt, et l'appel claude -p.

L'ISOLATION EST MESUREE, PAS SUPPOSEE (docs/habitant.md pas 2, reveils-jouets
du 30.8) : `--restricted --tools <liste>` remplace `--allowedTools`.
  - --restricted ignore les settings USER et PROJET — les hooks parasites de
    la machine ne frappent plus (deux reveils d'essai sur trois y finissaient
    leur vie) — et garde les outils nommes par --tools ;
  - un fichier passe EXPLICITEMENT par --settings frappe ENCORE : le
    parloir-hook des depeches, qui passe deja par --settings, continue donc
    de battre en mode call. C'est un sursis, pas un avenir : le modele
    habitant remplace ce hook par les canaux des chambres (transition
    assumee, pas 3-5 du chantier) ;
  - Write/Edit dans la chambre montee (--add-dir) exigent
    --permission-mode acceptEdits, deja pose.

CALL ET CAST (habitant.md §4) : on appelle quand on a besoin de la reponse
(attendre=True — le comportement historique), on depeche quand on lance une
vie (attendre=False — spawn detache, stdout dans fil/ de sa chambre, la
suite arrive par les canaux). Le defaut CLI reste le call tant que les
reveils-bancs 3-5 n'ont pas tourne.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

from etat.expose import tables

from agents.depeche.brief import (RACINE, ETAT, DEPOT_RAPPORTS,
                                  livre,
                                  OUTILS, PARLOIR_PY, travaux_ids,
                                  OUTIL_PARLOIR, SEL, lire, date_du_monde,
                                  identifiant_de_session, brief_de,
                                  feuille_de_route, travaux_ouverts_de,
                                  dossier_journee)
from agents.depeche.manuel import (manuel_de, contexte_message,
                                   message_tentative, manuel_narrateur_local,
                                   memoire_activation, etagere_systeme)
from agents.depeche.narrateur import (contrat_rapport_narrateur,
                                      _mission_historique)
from agents.depeche.trous import ses_trous, sa_charge_ailleurs, on_lattend
from agents.depeche.retour import (verser_sur_le_champ, proposer_la_tete,
                                   _poser)

def mission(qui, brief, consigne, contexte=None):
    """Donne l'interface du jour ; l'identité et le contexte vivent au système."""
    depot = os.path.join(RACINE, "").replace("\\", "/")
    aujourdhui = dict(zip(("annee", "lune", "jour"), date_du_monde()))
    contexte = contexte or dossier_journee(qui, brief)
    ajout = (u"\n## L'élan particulier de ce jour\n\n" + consigne.strip() + u"\n"
             if consigne and consigne.strip() else u"")
    # Ses cahiers d'abord — c'est ce dont il répond. Puis ce qui tombe sur lui
    # de dehors, et qu'aucun chemin ne lui portait.
    ajout = ses_trous(qui) + sa_charge_ailleurs(qui) + on_lattend(qui) + ajout
    from agents.expose import chambre as _ch
    sa_chambre = _ch.chemin(qui).replace("\\", "/")
    # SON ARBITRE DE ZONE (habitant.md §3, pas 4) : d'apres sa ville — la
    # zone du joueur est `mj`, les autres `mj-<ville>` ; a defaut, `mj`.
    from agents.expose import zone as _zone
    arbitre = _zone.arbitre_de(qui)
    # LES BILLETS ENTRENT EN PERCEPT (habitant.md §3) : « Untel t'a écrit :
    # "…" » — jamais une invitation à ouvrir un fichier (2/2 ignorée aux
    # essais). Le curseur n'avance qu'au lancement réussi (marquer_lus, dans
    # depecher) : un départ raté ne mange pas les billets.
    billets = u""
    for b in _ch.non_lus(qui):
        d = b.get("date")
        if isinstance(d, dict):
            d = u"%s.%s.%s" % (d.get("annee", u"?"), d.get("lune", u"?"),
                               d.get("jour", u"?"))
        quand = u" (%s%s)" % (d or u"", u", %s" % b["heure"]
                              if b.get("heure") else u"")
        billets += (u"\n%s t'a écrit%s : « %s »\n"
                    % (b.get("de") or b.get("avec"),
                       quand if quand != u" ()" else u"",
                       (b.get("texte") or u"").strip()))
    if billets:
        billets = (u"\n## On t'a écrit\n" + billets +
                   u"\nCes mots te sont arrivés : ils font partie de ta journée."
                   u" Réponds-y à ta façon — dans tes gestes, tes cahiers, ou en"
                   u" notant ta réponse dans ta chambre pour la lui porter.\n")
    ajout = billets + ajout
    # LA OU IL S'ETAIT LAISSE : le mot qu'il s'est laisse hier (demain.md,
    # ecrit par depecher en fin de journee) se relit en tete de la journee
    # neuve — puis sera ecrase par la conclusion de ce soir. L'ordre :
    # injecte au reveil N+1, ecrase en fin de N+1.
    hier = u""
    chemin_demain = os.path.join(_ch.chemin(qui), "demain.md")
    if os.path.exists(chemin_demain):
        with io.open(chemin_demain, encoding="utf-8") as f:
            mot_dhier = f.read().strip()
        if mot_dhier:
            hier = (u"\n## Là où tu t'étais laissé\n\n" + mot_dhier +
                    u"\n\nC'est le mot que tu t'es laissé hier. Reprends de"
                    u" là, ou contredis-le — c'est le tien.\n")
    return u"""%(contexte)s

---

# Cette journée
%(hier)s
Ton contexte vivant est déjà auprès de toi. Le dépôt %(depot)s matérialise le
monde que tes yeux et tes mains peuvent consulter. Ton étagère se trouve dans
`./livres/`, un fichier par volume. `Read`, `Grep` et `Glob` servent à toucher
ces sources ; `Grep` localise un passage dans les grands journaux avant sa
lecture.

## Ton arbitre, et tes trois verbes

Ton arbitre de zone est `%(arbitre)s`. Quand ton geste engage le monde, tu le
lui adresses par l'un des trois verbes — le verdict revient comme retour de
commande, dans le fil de ta pensée :

    python %(parloir)s --tenter --de %(qui)s --a %(arbitre)s "je pars sur mon cheval"
    python %(parloir)s --faire --de %(qui)s --a %(arbitre)s "je déplace ce livre"
    python %(parloir)s --demander --de %(qui)s --a %(arbitre)s "l'histoire de cette tour ?"

TENTER : tu tentes, l'arbitre tranche en coulisse. FAIRE : tu proposes un
changement au monde. DEMANDER : tu demandes ce que le monde dit — la réponse
vient des registres seuls.

Le parloir apporte aussi une parole au milieu de ton travail. Lorsqu'une
parole y arrive, cette commande porte ta réponse dans la pièce :

    python %(parloir)s --dire --de %(qui)s --a %(arbitre)s "..."

Puis ta journée continue depuis ce nouvel échange.

## Ta chambre

Ta chambre est le dossier `%(chambre)s` — elle est à toi, et à toi seul.

- `claude.md` : ta manière, de ta main. Amende-le quand ta journée te contredit.
- `brouillons/` : ce qui mûrit. Rature, reprends, ne rends que le propre.
- `fil/` : les traces de tes journées passées — relis-les si un souvenir te manque.
- `relations/<untel>/claude.md` : ce que TU retiens de chacun.

Rien dans ta chambre ne fait foi sur le monde : elle est ta mémoire et ton
caractère. Ce qui doit devenir vrai passe par tes gestes dans la journée.

## Ton retour

Plus de formulaire : ta journée EST ton retour. Ce que tu apprends, écris-le
dans tes cahiers et ta chambre à mesure ; ce que tu conclus, note-le où tu
sauras le retrouver. Ta dernière réponse est ta conclusion à toi — ce que ta
journée a changé, et ce que tu comptes faire ensuite, dit à ta façon, en
quelques lignes au plus. Tu te la laisses comme on se laisse un mot sur sa
table : c'est elle que tu retrouveras à ton prochain réveil.

Tes affaires ouvertes, pour mémoire :

%(travaux_ids)s
%(ajout)s""" % {
        "chambre": sa_chambre,
        "arbitre": arbitre,
        "hier": hier,
        "depot": depot,
        "parloir": PARLOIR_PY,
        "qui": qui,
        "aujourdhui": json.dumps(aujourdhui, ensure_ascii=False),
        "travaux_ids": travaux_ids(qui),
        "ajout": ajout,
        "contexte": contexte_message(qui, contexte).strip(),
    }


def poser_letagere(neutre, qui):
    """Materialise ses volumes en fichiers, un par volume, dans son dossier.

    C'EST LE SELECTEUR, ET IL EST PHYSIQUE. On aurait pu lui donner le
    lecteur en Bash et lui dire de s'en servir ; mais un outil qu'on autorise
    par motif de commande se contourne, et une consigne ne verrouille rien.
    La ou il travaille, il n'EXISTE que ce qu'il peut ouvrir. Le carnet de la
    reine n'est pas refuse : il n'est pas la.

    Effet de bord heureux : Grep sur ./livres/ lui donne la recherche
    plein-texte de son etagere, ce qui est exactement le geste d'un homme qui
    cherche dans ses registres — et qui evite les 547 000 jetons de
    etat/books.json, ou il s'est noye pendant huit minutes.
    """
    dossier = os.path.join(neutre, "livres")
    os.makedirs(dossier)
    n = 0
    index = []
    for b in livre.etagere(qui):
        with io.open(os.path.join(dossier, "%s.txt" % b.get("id")), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(livre.rendre(b, large=True))
        index.append("%-34s %s%s" % (
            b.get("id"), b.get("titre") or "",
            ("   (porte par %s)" % b["acteur_id"]) if b.get("acteur_id")
            else ("   (pose : %s)" % b["salle_id"]) if b.get("salle_id")
            else ""))
        n += 1
    # L'INDEX EST UN FICHIER, PLUS UN PARAGRAPHE DU REVEIL. Il pesait 7,2 Ko
    # dans le message pour dire des noms de fichiers ; il est ici, a cote de
    # ce qu'il indexe, et c'est la ou un homme le cherche.
    with io.open(os.path.join(dossier, "_index.txt"), "w", encoding="utf-8",
                 newline="\n") as f:
        f.write("LES VOLUMES A TA PORTEE — %d" % n + chr(10))
        f.write("Chacun s'ouvre sous ./livres/<identifiant>.txt ;"
                " Grep cherche dans leur texte." + chr(10) * 2)
        f.write((chr(10)).join(sorted(index)) + chr(10))
    return n


def poser_la_memoire(neutre, qui, contexte=None):
    """Materialise au pas-de-tir ce que le message ne porte plus.

    LE PENDANT OBLIGE DE LA COMPRESSION. Sortir les croyances et les pensees
    du message ne vaut que si elles EXISTENT quelque part qu'il puisse ouvrir :
    un pointeur vers rien est pire qu'un percept trop long. Deux fichiers,
    ecrits ici parce que ce sont des lectures de `etat/` mises en forme pour
    lui — sa chambre, elle, est a lui, et nous n'y ecrivons pas sa memoire.

    Rend {croyances, pensees} : le nombre de lignes posees de chaque cote.
    """
    dossier = os.path.join(neutre, "ma-memoire")
    os.makedirs(dossier, exist_ok=True)
    # `contexte` est un confort, pas une dependance : les deux chemins d'appel
    # (depeche et boucle d'activation) ne l'ont pas tous les deux sous la main,
    # et un fichier qui manque parce qu'un argument manquait serait exactement
    # le pointeur mort qu'on cherche a eviter. A defaut, on relit la tete.
    intention = (contexte or {}).get("intention")
    if not intention:
        tetes = tables.lire(os.path.join(RACINE, "etat", "intentions.json"), [])
        if isinstance(tetes, dict):
            tetes = tetes.get("intentions") or []
        intention = next((t for t in tetes
                          if isinstance(t, dict)
                          and t.get("personnage_id") == qui), {})

    croyances = [str(x) for x in (intention.get("croyances") or []) if x]
    if croyances:
        with io.open(os.path.join(dossier, "ce-que-je-tiens-pour-vrai.txt"),
                     "w", encoding="utf-8", newline=chr(10)) as f:
            f.write("CE QUE JE TIENS POUR VRAI" + chr(10))
            f.write("La derniere en tete. Rien ici n'est prouve : c'est ce que"
                    " je crois," + chr(10) + "et j'ai le droit de me tromper."
                    + chr(10) * 2)
            for x in croyances:
                f.write("- " + x + chr(10) * 2)

    pensees = [p for p in _pensees_de(qui)]
    if pensees:
        with io.open(os.path.join(dossier, "ce-que-jai-appris.txt"), "w",
                     encoding="utf-8", newline=chr(10)) as f:
            f.write("CE QUE J'AI APPRIS" + chr(10))
            f.write("Mes pensees datees, la plus recente en tete." + chr(10) * 2)
            for x in pensees:
                d = x.get("date") or {}
                f.write("[%s.%s.%s] %s" % (d.get("annee"), d.get("lune"),
                                           d.get("jour"),
                                           str(x.get("texte") or "")))
                if x.get("source"):
                    f.write(chr(10) + "   (source : %s)" % x["source"])
                f.write(chr(10) * 2)
    return {"croyances": len(croyances), "pensees": len(pensees)}


def _pensees_de(qui):
    """Ses pensees, la plus recente en tete. Lecture par la porte."""
    d = tables.lire(os.path.join(RACINE, "etat", "pensees.json"), [])
    if isinstance(d, dict):
        d = d.get("pensees") or []
    siennes = [p for p in d if isinstance(p, dict) and p.get("qui") == qui]

    def rang(p):
        j = p.get("date") or {}
        return (j.get("annee", 0), j.get("lune", 0), j.get("jour", 0))
    return sorted(siennes, key=rang, reverse=True)


def poser_le_parloir(neutre, qui):
    """Le hook qui lui met une oreille. Rend le chemin du fichier de reglages.

    UN HOOK N'EST PAS UNE HORLOGE : il bat apres chaque appel d'OUTIL, et
    seulement la. Un homme qui reflechit longtemps sans rien ouvrir n'entend
    rien pendant ce temps. En pratique cela suffit — sa journee entiere est
    faite de Read et de Grep —, mais c'est la limite du procede et il faut la
    connaitre avant de s'etonner d'un silence.

    Le matcher est `*` a dessein : on veut l'entendre au plus tot, pas
    seulement quand il lit. Le cout est nul tant que personne ne lui parle —
    `parloir.py --ecouter` n'ecrit RIEN sans message neuf, et un hook muet
    n'entre pas dans le contexte.
    """
    d = os.path.join(neutre, ".claude")
    os.makedirs(d, exist_ok=True)
    cible = os.path.join(d, "settings.json")
    py = sys.executable.replace("\\", "/")
    ecoute = "%s %s --ecouter --qui %s --hook" % (py, PARLOIR_PY, qui)
    with io.open(cible, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "env": {"LE_CONSEIL_QUI": qui},
            "hooks": {
                "PostToolUse": [{"matcher": "*", "hooks": [
                    {"type": "command", "command": ecoute, "timeout": 15}]}],
            }}, ensure_ascii=False, indent=2))
    return cible


DEPECHES = os.path.join(ETAT, "depeches")


def archiver_le_prompt(qui, sid, manuel, texte):
    """Garde sur disque CE QUI A REELLEMENT ETE INJECTE, avant l'appel.

    Le manuel partait dans un `mkdtemp` que personne ne relit et que le systeme
    balaie : on pouvait donc lire toute la journee d'un homme sans jamais savoir
    ce qu'il avait recu en entrant. La question « il est coherent » ou « on le
    re-briefe a chaque reveil » n'avait pas de piece pour la trancher.

    La boucle d'activation, elle, archive deja son `system_prompt` dans
    `etat/activations/` — c'est le meme geste, porte au chemin manuel, qui
    etait le seul des deux a n'avoir aucune trace.

    On ecrit AVANT l'appel et non apres : une session qui meurt en cours doit
    laisser son prompt, sinon il manque exactement quand il sert le plus.
    """
    horo = "%s-%06d" % (time.strftime("%Y%m%d-%H%M%S"),
                        int(time.time() * 1e6) % 1000000)
    return tables.ecrire(os.path.join(DEPECHES, "%s-%s.json" % (horo, qui)), {
        "qui": qui,
        "session": sid,
        "date_jeu": "%s.%s.%s" % date_du_monde(),
        "system_prompt": manuel,
        "mission": texte,
    }, indent=1)


def appeler(qui, manuel, texte, sid, modele, minutes, parloir=True,
            attendre=True):
    """Tente --session-id ; retombe sur --resume si l'id a deja servi.

    LE MANUEL PASSE PAR --system-prompt-file. Windows plafonne une ligne a
    32 767 caracteres ; le fichier garde donc le prompt hors des arguments,
    mais sans le faire passer pour un CLAUDE.md decouvert automatiquement.
    L'homme recoit explicitement SON manuel systeme et n'herite plus de celui
    du MJ lorsque le depot est rouvert par --add-dir.

    Le repertoire est hors du depot : la decouverte remonte l'arborescence, un
    sous-dossier de le-conseil2 aurait retrouve le manuel du MJ par-dessus.
    SA CHAMBRE est montee en plus du depot (chambre.ouvrir + --add-dir) :
    l'habitant ecrit chez lui, et chez lui seulement — rien dans chambres/
    ne fait foi, la porte-etat garde le reste.

    attendre=False est le CAST : spawn detache (Popen sans wait), stdout vers
    un log dans fil/ de sa chambre, retour immediat {cast, log, session}. Un
    cast ne sait pas retomber sur --resume (personne ne lit sa sortie a
    temps) : il part en --session-id sec, et un id deja servi se lira dans
    son log. Pas de parloir en cast : sa fin de session n'est pas connue, on
    ne laisse pas d'oreilles orphelines — les canaux des chambres prennent
    la releve (habitant.md, pas 3-5).
    """
    from agents.expose import chambre as _ch
    neutre = tempfile.mkdtemp(prefix="depeche-%s-" % qui)
    poser_letagere(neutre, qui)
    # Ce que le message ne porte plus doit exister la ou il pointe.
    poser_la_memoire(neutre, qui)
    sa_chambre = _ch.ouvrir(qui)
    prompt_systeme = os.path.join(neutre, "system-prompt.md")
    with io.open(prompt_systeme, "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(manuel)
    archiver_le_prompt(qui, sid, manuel, texte)
    # LE FIL PORTE LA SESSION, PAS L'HOMME. Deux dépêches du même acteur
    # peuvent tourner en même temps — la mienne et celle de la boucle
    # d'activation, le 9 août — et sous un seul nom elles se volaient les
    # messages. Le jeton vient de l'identifiant de session : deterministe,
    # donc retrouvable, et distinct par instance.
    identite = qui
    parloir = parloir and attendre  # jamais d'oreille orpheline sur un cast
    if parloir:
        from agents.expose import parloir as _p
        identite = _p.ouvrir_instance(qui, sid.replace("-", "")[:8],
                                      os.path.basename(neutre), minutes)
    reglages = poser_le_parloir(neutre, identite) if parloir else None

    # --restricted --tools : l'isolation mesuree (voir l'en-tete). Bash est
    # entier dans OUTILS : OUTIL_PARLOIR (un motif Bash) n'a plus a s'ajouter.
    base = ["claude", "-p",
            "--system-prompt-file", prompt_systeme,
            "--add-dir", RACINE, "--add-dir", sa_chambre,
            "--restricted", "--tools", ",".join(OUTILS)]
    if attendre:
        base += ["--output-format", "json"]
    if reglages:
        # Un --settings explicite frappe encore sous --restricted (mesure) :
        # le hook du parloir est charge sans dependre de la reconnaissance du
        # repertoire neutre comme projet.
        base += ["--settings", reglages]
    base += ["--permission-mode", "acceptEdits"]
    if modele:
        base += ["--model", modele]

    if not attendre:
        # LE CAST — on lance une vie, on ne la regarde pas vivre. La mission
        # part par un fichier tenu ouvert en stdin ; le fil de sa chambre
        # recoit la sortie, datee, relisible.
        horo = time.strftime("%Y%m%d-%H%M%S")
        log = os.path.join(sa_chambre, "fil", "depeche-%s.log" % horo)
        entree = os.path.join(neutre, "mission.txt")
        with io.open(entree, "w", encoding="utf-8", newline="\n") as f:
            f.write(texte)
        drapeaux = {}
        if os.name == "nt":  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            drapeaux["creationflags"] = 0x00000008 | 0x00000200
        else:
            drapeaux["start_new_session"] = True
        with io.open(entree, "rb") as fin, io.open(log, "wb") as flog:
            subprocess.Popen(base + ["--session-id", sid], cwd=neutre,
                             stdin=fin, stdout=flog,
                             stderr=subprocess.STDOUT, **drapeaux)
        return {"cast": True, "log": log, "session": sid}

    dernier = u""
    try:
        for tentative in (["--session-id", sid], ["--resume", sid]):
            # La mission passe par stdin pour la meme raison que le manuel par
            # un fichier : 11 ko d'argument s'ajoutent a tout le reste.
            r = subprocess.run(base + tentative, cwd=neutre,
                               input=texte.encode("utf-8"),
                               capture_output=True, timeout=minutes * 60)
            out = r.stdout.decode("utf-8", "replace")
            err = r.stderr.decode("utf-8", "replace")
            if "already in use" in out + err:
                continue  # la session existe deja : on la reprend en place
            if not out.strip():
                raise RuntimeError((err or "aucune sortie").strip()[:400])
            return json.loads(out)
        raise RuntimeError("ni --session-id ni --resume n'ont abouti : %s"
                           % dernier[:200])
    finally:
        # SA SESSION EST FINIE : ELLE N'ECOUTE PLUS. Sans ce `finally`, une
        # depeche morte laisse son instance ouverte, et l'on continue de lui
        # parler dans un fil que plus personne ne lit — trois orphelines
        # tramaient deja apres les essais du 9 aout.
        if parloir and identite != qui:
            try:
                from agents.expose import parloir as _p
                _p.fermer_instance(identite)
            except Exception:
                pass


def extraire_json(texte):
    """Sa reponse DEVRAIT etre du JSON nu. On tolere un bloc de code ou une
    phrase autour : un homme qui a bien travaille ne doit pas voir sa journee
    jetee pour trois backticks."""
    t = (texte or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t).strip()
    try:
        return json.loads(t), None
    except Exception:
        pass
    d, f = t.find("{"), t.rfind("}")
    if d >= 0 and f > d:
        try:
            return json.loads(t[d:f + 1]), u"JSON degage d'un texte enrobe"
        except Exception as e:
            return None, u"illisible : %s" % e
    return None, u"aucun objet JSON dans la reponse"


def depecher(qui, consigne, modele, minutes, sec, attendre=True):
    date = date_du_monde()
    sid = identifiant_de_session(qui, date)
    brief = brief_de(qui)
    # LA GARDE PORTE SUR CE QUI EMPECHE SA JOURNEE, pas sur un mot du dossier.
    # Elle cherchait « CONVOCATION », que l'ancien brief tenait de
    # `convoquer.py` ; le brief neuf calcule les creux lui-meme et ne l'ecrit
    # plus — la garde etait donc toujours vraie et PLUS PERSONNE NE PARTAIT.
    # Les deux vrais motifs sont les deux sorties precoces de `brief_de`.
    empeche = None
    # UN SIEGE OCCUPE N'EST PAS DEPECHE : quand un joueur incarne cet homme,
    # sa journee est vecue par le siege — une depeche parallele donnerait
    # deux volontes au meme corps le meme jour. L'anachronisme tolere le
    # desordre des dates, pas la double volonte (decision du 30.8).
    joueurs = tables.lire(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs", [])
    for j in joueurs or []:
        if isinstance(j, dict) and j.get("occupe") and not j.get("regie") \
                and (j.get("personnage_id") or j.get("id")) == qui:
            empeche = u"son siege est occupe — un joueur l'incarne"
            break
    if not brief:
        empeche = u"aucun dossier"
    elif u"Aucune tete dans intentions.json" in brief:
        empeche = u"pas de tete dans intentions.json"
    elif u"AUCUN CREUX" in brief:
        empeche = u"aucun creux aujourd'hui — il travaille, il ne pense pas"
    if empeche:
        print(u"  %-18s ne part pas — %s" % (qui, empeche))
        return False
    contexte = dossier_journee(qui, brief)
    manuel = manuel_de(qui, mode="journee", contexte=contexte)
    texte = mission(qui, brief, consigne, contexte=contexte)

    if sec:
        print(u"═" * 72)
        print(u"%s   session %s" % (qui, sid))
        print(u"  prompt système : %d caractères (nouvelle version seule)"
              % len(manuel))
        print(u"  mission        : %d caracteres" % len(texte))
        print(u"  outils         : %s" % " ".join(OUTILS))
        print(u"  lance depuis   : un repertoire neutre, --add-dir %s" % RACINE)
        print(u"─" * 72)
        print(texte)
        return True

    debut = time.time()
    try:
        rep = appeler(qui, manuel, texte, sid, modele, minutes,
                      attendre=attendre)
    except Exception as e:
        print(u"  %-18s ECHEC — %s" % (qui, e))
        return False

    # LE LANCEMENT A PRIS : son reveil a tout vu — les billets sont lus.
    # Avant ce point (echec du depart), les curseurs n'ont pas bouge.
    from agents.expose import chambre as _ch
    _ch.marquer_lus(qui)

    if not attendre:
        # Parti en cast : sa journee vit sans nous. Pas de rapport a parser —
        # le retour d'une journee, c'est l'etat de sa chambre plus ses
        # versements (habitant.md §1) ; son log dit ou la regarder.
        print(u"  %-18s parti detache → %s"
              % (qui, os.path.relpath(rep["log"], RACINE)))
        return True

    # LE VECU AU FIL, TOUJOURS — pas de hook possible sous --restricted :
    # c'est le lanceur qui depose (habitant.md pas 6).
    from agents.expose import trace as _tr
    try:
        _tr.deposer(qui, sid, etiquette=u"%d.%d.%d" % date)
    except Exception:
        pass  # un fil qui manque ne vaut pas une journee perdue

    rapport, note = extraire_json(rep.get("result", ""))
    u_ = rep.get("usage", {}) or {}
    jetons = (u_.get("input_tokens", 0) + u_.get("cache_read_input_tokens", 0)
              + u_.get("cache_creation_input_tokens", 0))

    if rapport is None:
        # PLUS UN ECHEC : le gabarit JSON est retire (habitant.md pas 3).
        # Sa derniere reponse est une phrase d'homme ; sa journee vit dans
        # sa chambre (fil/, brouillons/, cahiers) et ses versements.
        phrase = (rep.get("result") or u"").strip()
        brut = os.path.join(DEPOT_RAPPORTS, "%s.brut.txt" % qui)
        _poser(brut, phrase)
        # LE MOT SUR SA TABLE : sa conclusion s'ecrit dans sa chambre,
        # ECRASEE a chaque journee — c'est le mot le plus recent qui compte,
        # le fil garde l'historique. Elle sera reinjectee a son prochain
        # reveil (« La ou tu t'etais laisse », mission()).
        if phrase:
            with io.open(os.path.join(_ch.chemin(qui), "demain.md"), "w",
                         encoding="utf-8", newline="\n") as f:
                f.write(phrase + u"\n")
        print(u"  %-18s %5d j. · %3ds — sa phrase : %s"
              % (qui, jetons, round(time.time() - debut),
                 re.sub(r"\s+", u" ", phrase)[:160] or u"(muette)"))
        return True

    rapport.setdefault("qui", qui)
    rapport["_depeche"] = {
        "session": sid, "date_jeu": "%d.%d.%d" % date,
        "jetons": jetons, "secondes": round(time.time() - debut),
    }
    cible = os.path.join(DEPOT_RAPPORTS, "%s.json" % qui)
    tables.ecrire(cible, rapport)
    verse = verser_sur_le_champ(rapport, qui, date)
    proposer_la_tete(rapport, qui, date, sid)

    p = sum(len(t.get("pensees", []) or []) for t in rapport.get("travaux", []) or [])
    print(u"  %-18s %2d pensee(s) [%d versee(s)] · %2d etape(s) · %s · %5d j. · %3ds → %s%s"
          % (qui, p, verse, len(rapport.get("journal", []) or []),
             u"conclusion" if rapport.get("conclusion") else u"—",
             jetons, rapport["_depeche"]["secondes"],
             os.path.relpath(cible, RACINE), u"  [%s]" % note if note else u""))
    return True

