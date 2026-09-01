# -*- coding: utf-8 -*-
"""Oracle en lecture seule des effets durables d'un travail continu."""

import os

from agents import work_identity


def observer(work_id):
    registre = work_identity.observer(work_id)
    terme = registre.get("term") or {}
    artifact = terme.get("artifact")
    existe = bool(artifact and os.path.isfile(artifact))
    taille = os.path.getsize(artifact) if existe else 0
    return {
        "work_id": registre["work_id"],
        "effect_key": registre["effect_key"],
        "attempt_id": terme.get("attempt_id"),
        "state": terme.get("state"),
        "compute_event_id": terme.get("compute_event_id"),
        "artifact": artifact,
        "effect_count": int(existe and taille > 0),
        "bytes": taille,
        "attempts": registre["attempts"],
    }
