# -*- coding: utf-8 -*-
"""Identite durable et tentatives d'un travail continu.

SQLite est l'autorite unique.  Un ancien registre JSON peut encore etre ecrit
par un processus deja charge : chaque nouvelle ouverture en importe donc le
snapshot de facon idempotente.  Une collision d'identite n'est jamais ecrasee;
elle est conservee dans ``migration_conflicts`` pour controle.
"""

import contextlib
import hashlib
import io
import json
import os
import sqlite3
import time
import uuid


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
REGISTRE = os.path.join(RACINE, ".agents-runtime", "work-registry.sqlite3")
REGISTRE_JSON_LEGACY = os.path.join(
    RACINE, ".agents-runtime", "work-registry.json")


SCHEMA = """
CREATE TABLE IF NOT EXISTS works (
    work_key TEXT PRIMARY KEY,
    work_id TEXT NOT NULL UNIQUE,
    effect_key TEXT NOT NULL UNIQUE,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    work_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    attempt_id TEXT NOT NULL UNIQUE,
    admitted_at REAL NOT NULL,
    state TEXT,
    compute_event_id TEXT,
    ended_at REAL,
    PRIMARY KEY(work_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS terms (
    work_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('succeeded','failed')),
    compute_event_id TEXT,
    artifact TEXT,
    durable_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS work_states (
    work_id TEXT PRIMARY KEY,
    progress TEXT,
    next_step TEXT,
    state TEXT NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS migration_conflicts (
    migration_id TEXT NOT NULL,
    work_key TEXT NOT NULL,
    existing_work_id TEXT NOT NULL,
    incoming_work_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    recorded_at REAL NOT NULL,
    PRIMARY KEY(migration_id, work_key)
);
"""


def _chemin_legacy():
    # Les tests peuvent rediriger REGISTRE vers un fichier temporaire. Dans ce
    # cas, ne jamais importer le registre reel du depot dans leur banc.
    if os.path.abspath(REGISTRE) != os.path.abspath(os.path.join(
            RACINE, ".agents-runtime", "work-registry.sqlite3")):
        return None
    return REGISTRE_JSON_LEGACY


def _snapshot_json():
    chemin = _chemin_legacy()
    if not chemin or not os.path.isfile(chemin):
        return None, None
    with io.open(chemin, "rb") as f:
        brut = f.read()
    identifiant = "legacy-json:" + hashlib.sha256(brut).hexdigest()
    return identifiant, json.loads(brut.decode("utf-8"))


def _migrer_json(conn):
    migration_id, donnees = _snapshot_json()
    if not migration_id:
        return
    if conn.execute("SELECT 1 FROM migrations WHERE migration_id=?",
                    (migration_id,)).fetchone():
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute("SELECT 1 FROM migrations WHERE migration_id=?",
                        (migration_id,)).fetchone():
            conn.commit()
            return
        works = donnees.get("works") or {}
        for work_key, work in works.items():
            existant = conn.execute(
                "SELECT work_id FROM works WHERE work_key=?", (work_key,)
            ).fetchone()
            if existant and existant[0] != work.get("work_id"):
                payload = {
                    "work": work,
                    "attempts": (donnees.get("attempts") or {}).get(
                        work.get("work_id")),
                    "term": (donnees.get("terms") or {}).get(
                        work.get("work_id")),
                    "state": (donnees.get("states") or {}).get(
                        work.get("work_id")),
                }
                conn.execute(
                    "INSERT OR IGNORE INTO migration_conflicts VALUES "
                    "(?,?,?,?,?,?)",
                    (migration_id, work_key, existant[0], work.get("work_id"),
                     json.dumps(payload, ensure_ascii=False, sort_keys=True),
                     time.time()))
                continue
            conn.execute(
                "INSERT OR IGNORE INTO works VALUES (?,?,?,?)",
                (work_key, work["work_id"], work["effect_key"],
                 float(work.get("created_at") or time.time())))
            work_id = work["work_id"]
            for tentative in (donnees.get("attempts") or {}).get(
                    work_id, []):
                conn.execute(
                    "INSERT OR IGNORE INTO attempts VALUES (?,?,?,?,?,?,?)",
                    (work_id, int(tentative["attempt_number"]),
                     tentative["attempt_id"],
                     float(tentative.get("admitted_at") or time.time()),
                     tentative.get("state"), tentative.get("compute_event_id"),
                     tentative.get("ended_at")))
            terme = (donnees.get("terms") or {}).get(work_id)
            if terme:
                conn.execute(
                    "INSERT OR REPLACE INTO terms VALUES (?,?,?,?,?,?)",
                    (work_id, terme["attempt_id"], terme["state"],
                     terme.get("compute_event_id"), terme.get("artifact"),
                     float(terme.get("durable_at") or time.time())))
            etat = (donnees.get("states") or {}).get(work_id)
            if etat:
                conn.execute(
                    "INSERT OR REPLACE INTO work_states VALUES (?,?,?,?,?)",
                    (work_id, etat.get("progress"), etat.get("next"),
                     etat.get("state") or "admitted",
                     float(etat.get("updated_at") or time.time())))
        conn.execute("INSERT INTO migrations VALUES (?,?)",
                     (migration_id, time.time()))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise


def _connexion():
    os.makedirs(os.path.dirname(os.path.abspath(REGISTRE)), exist_ok=True)
    conn = sqlite3.connect(REGISTRE, timeout=10, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    _migrer_json(conn)
    return conn


@contextlib.contextmanager
def _transaction():
    conn = _connexion()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def cle_depeche(qui, contexte_id, ref, session_id):
    ancre = ref or session_id
    if not qui or not ancre:
        raise ValueError("une admission exige acteur et ref ou session")
    return "depeche:%s:%s:%s" % (
        str(qui), str(contexte_id or "sans-contexte"), str(ancre))


def _identite(work_id, effect_key, attempt_id, attempt_number):
    return {"work_id": work_id, "attempt_id": attempt_id,
            "attempt_number": int(attempt_number),
            "effect_key": effect_key}


def admettre(work_key):
    """Rend le meme work_id et une tentative monotone sous concurrence."""
    if not work_key:
        raise ValueError("work_key vide")
    with _transaction() as conn:
        work = conn.execute(
            "SELECT work_id,effect_key FROM works WHERE work_key=?",
            (str(work_key),)).fetchone()
        if not work:
            work_id = str(uuid.uuid4())
            effect_key = "effect:" + work_id
            conn.execute("INSERT INTO works VALUES (?,?,?,?)",
                         (str(work_key), work_id, effect_key, time.time()))
        else:
            work_id, effect_key = work
        numero = conn.execute(
            "SELECT COALESCE(MAX(attempt_number),0)+1 FROM attempts "
            "WHERE work_id=?", (work_id,)).fetchone()[0]
        attempt_id = "%s:attempt:%d" % (work_id, numero)
        conn.execute(
            "INSERT INTO attempts VALUES (?,?,?,?,?,?,?)",
            (work_id, numero, attempt_id, time.time(), "admitted", None, None))
        return _identite(work_id, effect_key, attempt_id, numero)


def courante(work_key):
    conn = _connexion()
    try:
        row = conn.execute(
            "SELECT w.work_id,w.effect_key,a.attempt_id,a.attempt_number "
            "FROM works w JOIN attempts a ON a.work_id=w.work_id "
            "WHERE w.work_key=? ORDER BY a.attempt_number DESC LIMIT 1",
            (str(work_key),)).fetchone()
    finally:
        conn.close()
    if not row:
        raise ValueError("travail inconnu")
    return _identite(*row)


def noter(identity, progress=None, next_step=None, state="running"):
    if not state:
        raise ValueError("state vide")
    with _transaction() as conn:
        conn.execute(
            "INSERT INTO work_states VALUES (?,?,?,?,?) "
            "ON CONFLICT(work_id) DO UPDATE SET progress=excluded.progress," 
            "next_step=excluded.next_step,state=excluded.state," 
            "updated_at=excluded.updated_at",
            (identity["work_id"], progress, next_step, state, time.time()))


def etat(work_id):
    conn = _connexion()
    try:
        ligne = conn.execute(
            "SELECT progress,next_step,state,updated_at FROM work_states "
            "WHERE work_id=?", (work_id,)).fetchone()
    finally:
        conn.close()
    return {"work_id": work_id,
            "progress": ligne[0] if ligne else None,
            "next": ligne[1] if ligne else None,
            "state": ligne[2] if ligne else "admitted",
            "updated_at": ligne[3] if ligne else None}


def terminer_attempt(identity, compute_event_id, state, term=False,
                     artifact=None):
    if state not in ("succeeded", "failed"):
        raise ValueError("state de tentative invalide")
    with _transaction() as conn:
        curseur = conn.execute(
            "UPDATE attempts SET state=?,compute_event_id=?,ended_at=? "
            "WHERE work_id=? AND attempt_id=?",
            (state, compute_event_id, time.time(), identity["work_id"],
             identity["attempt_id"]))
        if curseur.rowcount != 1:
            raise ValueError("tentative inconnue")
        if term:
            conn.execute(
                "INSERT INTO terms VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(work_id) DO UPDATE SET "
                "attempt_id=excluded.attempt_id,state=excluded.state," 
                "compute_event_id=excluded.compute_event_id," 
                "artifact=excluded.artifact,durable_at=excluded.durable_at",
                (identity["work_id"], identity["attempt_id"], state,
                 compute_event_id, str(artifact) if artifact else None,
                 time.time()))
        final = "completed" if term and state == "succeeded" else state
        conn.execute(
            "INSERT INTO work_states VALUES (?,?,?,?,?) "
            "ON CONFLICT(work_id) DO UPDATE SET state=excluded.state," 
            "updated_at=excluded.updated_at",
            (identity["work_id"], None, None, final, time.time()))


def observer(work_id):
    """Rend les faits du registre sans imposer un moteur d'execution."""
    conn = _connexion()
    try:
        work = conn.execute(
            "SELECT effect_key FROM works WHERE work_id=?", (work_id,)
        ).fetchone()
        if not work:
            raise ValueError("travail inconnu")
        tentatives = [
            {"attempt_number": r[0], "attempt_id": r[1],
             "admitted_at": r[2], "state": r[3],
             "compute_event_id": r[4], "ended_at": r[5]}
            for r in conn.execute(
                "SELECT attempt_number,attempt_id,admitted_at,state," 
                "compute_event_id,ended_at FROM attempts WHERE work_id=? "
                "ORDER BY attempt_number", (work_id,)).fetchall()]
        terme_row = conn.execute(
            "SELECT attempt_id,state,compute_event_id,artifact,durable_at "
            "FROM terms WHERE work_id=?", (work_id,)).fetchone()
        etat_row = conn.execute(
            "SELECT progress,next_step,state,updated_at FROM work_states "
            "WHERE work_id=?", (work_id,)).fetchone()
    finally:
        conn.close()
    terme = None if not terme_row else {
        "attempt_id": terme_row[0], "state": terme_row[1],
        "compute_event_id": terme_row[2], "artifact": terme_row[3],
        "durable_at": terme_row[4]}
    etat_ = None if not etat_row else {
        "progress": etat_row[0], "next": etat_row[1],
        "state": etat_row[2], "updated_at": etat_row[3]}
    return {"work_id": work_id, "effect_key": work[0],
            "attempts": tentatives, "term": terme, "state": etat_}
