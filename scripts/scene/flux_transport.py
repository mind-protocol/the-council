# -*- coding: utf-8 -*-
"""Sérialisation et idempotence de l'unique plume du flux."""
import atexit
import hashlib
import io
import json
import os
import time
import uuid


def prendre_verrou(runtime, timeout=15, stale=120):
    os.makedirs(runtime, exist_ok=True)
    chemin = os.path.join(runtime, "ecriture.lock")
    limite = time.time() + timeout
    while True:
        try:
            fd = os.open(chemin, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(chemin) > stale:
                    os.remove(chemin)
                    continue
            except OSError:
                continue
            if time.time() >= limite:
                raise RuntimeError("la plume du flux est occupee depuis %d secondes"
                                   % timeout)
            time.sleep(.02)

    def liberer():
        try:
            os.remove(chemin)
        except OSError:
            pass
    atexit.register(liberer)
    return liberer


def empreinte(item):
    """Le contenu adressé, sans les estampilles produites par la plume."""
    matiere = {k: v for k, v in item.items() if k not in ("heure", "date")}
    brut = json.dumps(matiere, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()


def lire(chemin, maintenant, ttl):
    try:
        with io.open(chemin, encoding="utf-8") as f:
            marques = json.load(f)
    except (OSError, ValueError):
        marques = {}
    return {k: v for k, v in marques.items()
            if isinstance(v, (int, float)) and maintenant - v <= ttl}


def ecrire(chemin, marques):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    temporaire = chemin + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(marques, f, ensure_ascii=False, sort_keys=True)
    os.replace(temporaire, chemin)
