# -*- coding: utf-8 -*-
"""RESUME — le calcul de la fenetre, en francais, pour le MJ.

CE QUE CE MODULE POSSEDE : l'impression lisible du calcul d'un tick —
les mains d'abord (c'est l'ordre de la boucle, et l'ordre de lecture), puis
les pensees, les seuils, les evenements, les nouvelles, les bouches, les
rumeurs, le courrier, les etapes et les declencheurs.

CE QU'IL REFUSE : calculer quoi que ce soit — il ne fait que dire ce que
fenetre.calculer() a deja calcule.

CONSOMMATEURS : fenetre.py.
"""


from temps.calendrier import fmt
from temps.bouche import FENETRE_ROYAUME


def resumer(prop):
    """Le meme calcul, en francais, pour le MJ."""
    f = prop["fenetre"]
    print("Fenetre : {} -> {} ({} jour(s))".format(
        fmt(f["de"]), fmt(f["a"]), f["jours"]))
    print("Acteurs simules : {}".format(len(prop["acteurs_simules"])))
    if prop["acteurs_sautes_royaume"]:
        print("  Echelle 'royaume' non rafraichie (fenetre < {} jours) : {}"
              .format(FENETRE_ROYAUME,
                      ", ".join(prop["acteurs_sautes_royaume"])))
        print("  (croyances et declencheurs sautes — leurs echeances tombent"
              " quand meme, marquees 'malgre saut')")

    # Les mains d'abord — c'est l'ordre de la boucle, et l'ordre de lecture.
    if prop.get("mains"):
        print("\nLes mains ({}) — ou en sont les choses :".format(
            len(prop["mains"])))
        for a in prop["mains"]:
            p = a.get("porteur") or {}
            qui = p.get("id") or "personne"
            print("  {:<26} ({}{})".format(
                a["id"], qui, ", ABSENT" if a.get("porteur_absent") else ""))
            for m in a["mesures"]:
                fleche = "{} -> {}".format(m["avant"], m["apres"])
                notes = []
                if m.get("gelee_par"):
                    notes.append("gelee par " + ", ".join(m["gelee_par"]))
                if m.get("porteur_absent"):
                    notes.append("ne produit plus, faute de porteur")
                if m.get("bute_sur"):
                    notes.append("bute sur le " + m["bute_sur"])
                print("      {:<34} {:>14} {} {}".format(
                    m["adresse"], fleche, m.get("unite") or "",
                    "— " + " ; ".join(notes) if notes else ""))

    # Les pensees ensuite : c'est l'entree de la salle. On lit qui a de quoi
    # parler AVANT d'elire qui parle — sinon on elit celui qui n'a rien.
    # Ce que `travaux` porte depuis que l'excitation a disparu : la feuille de
    # route d'evaluer.py — sa force sur le graphe, ses questions, et le temps
    # que sa journee lui laisse. Plus de verdict, plus de conclusion mure.
    if prop.get("travaux"):
        erreur = next((t["erreur"] for t in prop["travaux"] if t.get("erreur")),
                      None)
        if erreur:
            print("\nLes pensees -- feuille de route indisponible : " + erreur)
        else:
            print("\nLes pensees -- qui a du temps aujourd'hui ({}) :".format(
                len(prop["travaux"])))
            for t in sorted(prop["travaux"],
                            key=lambda x: -(x.get("force") or 0)):
                print("  [{:>5}] {:<20} {} question(s), {} min de creux{}".format(
                    t.get("force"), t.get("qui"), t.get("questions"),
                    t.get("creux_total"),
                    " -- {} deja posee(s)".format(t["questions_posees"])
                    if t.get("questions_posees") else ""))

    if prop.get("seuils_franchis"):
        print("\nSEUILS ({}) :".format(len(prop["seuils_franchis"])))
        for s in prop["seuils_franchis"]:
            if s["sens"] == "retombe":
                print("  [retombe] {}.{} — la crise est close, redescends le"
                      " porteur d'echelle".format(s["main_id"], s["seuil"]))
                continue
            p = s.get("porteur") or {}
            print("  [FRANCHI] {}.{} — {} {} {} (valeur {})".format(
                s["main_id"], s["seuil"], s["adresse"], s["quand"],
                s["borne"], s["valeur"]))
            if p.get("type") == "personnage" and p.get("id"):
                print("      porteur : {} -> promouvoir en '{}'".format(
                    p["id"], s["promeut"]))
            else:
                # Un lieu ou une maison ne monte pas l'escalier. La crise est
                # reelle et n'a aucune bouche pour la dire : c'est au MJ de lui
                # en trouver une, ou d'assumer que le joueur l'apprenne trop tard.
                print("      porteur : {} — RIEN A PROMOUVOIR. La crise n'a "
                      "personne pour la porter :".format(
                          p.get("id") or "personne"))
                print("      donne-lui une bouche, ou laisse le joueur "
                      "l'apprendre trop tard (c'est une option, pas un bug).")
            print("      affaire : {}".format(s["affaire"]))

    print("\nEvenements a resoudre ({}) :".format(
        len(prop["evenements_a_resoudre"])))
    for ev in prop["evenements_a_resoudre"]:
        print("  {} {:<28} imp {} {}".format(
            fmt(ev["date"]), ev["id"], ev["importance"],
            "(EN RETARD)" if ev["en_retard"] else ""))
        if ev["conditions"]:
            print("      a arbitrer : {}".format(" | ".join(ev["conditions"])))

    print("\nNouvelles a livrer ({}) :".format(len(prop["nouvelles_a_livrer"])))
    for n in prop["nouvelles_a_livrer"]:
        cible = n["ou"] or ", ".join(n["qui"]) or "?"
        print("  {} {} par {} vers {} (fiab. {}){}{}".format(
            fmt(n["date"]), n["evenement_id"], n["canal"], cible,
            n["fiabilite"],
            " [qui deduit]" if n["qui_deduit"] else "",
            " [TOUCHE LE JOUEUR -> info.json]" if n["touche_joueur"] else ""))

    if prop.get("nouvelles_conditionnelles"):
        print("\nNouvelles SUSPENDUES ({}) — l'evenement n'est pas encore resolu,"
              " elles ne partent qu'apres ton arbitrage :"
              .format(len(prop["nouvelles_conditionnelles"])))
        for n in prop["nouvelles_conditionnelles"]:
            print("  {} {} vers {} (fiab. {}) — depend de {}".format(
                fmt(n["date"]), n["evenement_id"],
                n["ou"] or ", ".join(n["qui"]) or "?", n["fiabilite"],
                n["depend_de_evenement"]))

    if prop.get("bouches"):
        print("\nLes bouches ({}) — qui arrive, et ce qu'il porte dans la tete :"
              .format(len(prop["bouches"])))
        for b in prop["bouches"]:
            print("  {} : {} -> {} ({} {}){}".format(
                b["personnage_id"], b["de"] or "?", b["vers"], b["source"],
                b["indice"],
                "   << ARRIVE CHEZ LE JOUEUR" if b["arrive_chez_le_joueur"]
                else ""))
            if b["arrive_chez_le_joueur"]:
                print("      -> une entree info.json, avec une bouche et un "
                      "visage. Pas une croyance qui se recopie en silence.")
            if not b["apporte"]:
                print("      n'apporte rien qu'on ne sache deja ici.")
            for croyance in b["apporte"]:
                print("      + {}".format(croyance[:150]))
            if b["deja_su_sur_place"]:
                print("      ({} croyance(s) deja sue(s) sur place)".format(
                    len(b["deja_su_sur_place"])))
        print("      Le script ne recopie RIEN : a toi de dire ce qui se dit, "
              "ce qui se tait, et ce qui se ment.")

    if prop.get("rumeurs_qui_sautent") or prop.get("rumeurs_immobiles"):
        print("\nLes rumeurs ({} saut(s)) — de proche en proche, sans porteur :"
              .format(len(prop.get("rumeurs_qui_sautent") or [])))
        for s in prop.get("rumeurs_qui_sautent") or []:
            print("  {} {} : {} -> {} ({}, {} -> {}){}".format(
                fmt(s["date"]), s["incident_id"], s["depuis"], s["vers"],
                s["raison"], s["certitude_source"], s["certitude_proposee"],
                "   << ATTEINT LE JOUEUR" if s["atteint_le_joueur"] else ""))
            if s["atteint_le_joueur"]:
                print("      -> une entree info.json : source de bouche a "
                      "oreille, fiabilite basse. Personne ne l'a apportee.")
            if s["note_du_mj"]:
                print("      ta crainte : {}".format(s["note_du_mj"]))
        for i in prop.get("rumeurs_immobiles") or []:
            print("  [immobile] {} ({}) — rien de neuf depuis {} jours (derniere "
                  "prise {}) : fais-la avancer ou eteins-la.".format(
                      i["incident_id"], i["feu"], i["silence_jours"],
                      fmt(i["derniere_prise"])))

    if prop.get("plis_remis") or prop.get("plis_encore_en_route"):
        print("\nLe courrier — plis remis ({}) :".format(
            len(prop.get("plis_remis") or [])))
        for p in prop.get("plis_remis") or []:
            print("  {} {:<24} {} de {} pour {} -> {}{}".format(
                fmt(p["attendu_le"]), p["id"], p["canal"], p["de"], p["pour"],
                p["vers"], " (EN RETARD)" if p.get("en_retard") else ""))
            if p.get("main"):
                print("      remis en main de {} — ce n'est pas {} qui le "
                      "sait, c'est lui.".format(p["main"], p["pour"]))
            else:
                print("      {}".format(p.get("probleme")))
        for p in prop.get("plis_encore_en_route") or []:
            print("  [en route] {} vers {}, encore {} jour(s)".format(
                p["id"], p["vers"], p["jours_encore"]))

    print("\nEtapes qui tombent ({}) :".format(len(prop["etapes_qui_tombent"])))
    for s in prop["etapes_qui_tombent"]:
        print("  {} {}{} — {}".format(
            fmt(s["date_estimee"]), s["personnage_id"],
            " [malgre saut]" if s.get("malgre_saut") else "", s["quoi"]))
        if s["cout"]:
            print("      cout : {}".format(", ".join(str(c) for c in s["cout"])))
        if s["si_bloque"]:
            print("      si bloque : {}".format(s["si_bloque"]))

    print("\nEtapes qui avancent ({}) :".format(
        len(prop["etapes_qui_avancent"])))
    for s in prop["etapes_qui_avancent"]:
        print("  {} — {} : {} -> {} jour(s)".format(
            s["personnage_id"], s["etape"], s["jours_restants"],
            s["jours_restants_apres"]))

    print("\nEtapes en attente ({}) :".format(len(prop["etapes_en_attente"])))
    for s in prop["etapes_en_attente"]:
        motif = s.get("probleme") or "attend {}".format(
            ", ".join(s.get("depend_de_non_fait") or []))
        print("  {} — {} ({})".format(s["personnage_id"], s["etape"], motif))

    if prop["postures_permanentes"]:
        print("\nPostures permanentes (horloge null, jamais decomptees) : {}"
              .format(prop["postures_permanentes"]))

    print("\nDeclencheurs a evaluer ({}) — le MJ seul juge :".format(
        len(prop["declencheurs_a_evaluer"])))
    for d in prop["declencheurs_a_evaluer"]:
        print("  {} : si {} -> {}".format(d["personnage_id"], d["si"],
                                          d["alors"]))

    print("\nTetes a rafraichir ({}) : {}".format(
        len(prop["tetes_a_rafraichir"]),
        ", ".join(t["personnage_id"] for t in prop["tetes_a_rafraichir"])))
