"""Execution bornee et exclusion mutuelle, sans shell."""
import contextlib
import json
import os
import signal
import subprocess
import time


@contextlib.contextmanager
def verrou(chemin):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "a+b") as f:
        if os.name == "nt":
            import msvcrt
            if f.tell() == 0:
                f.write(b"0")
                f.flush()
            f.seek(0)
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as e:
                raise RuntimeError("Un essai occupe deja le banc. Lis son resultat avant de relancer.") from e
        else:
            import fcntl
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                raise RuntimeError("Un essai occupe deja le banc.") from e
        try:
            yield
        finally:
            if os.name == "nt":
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def arreter(p):
    if p.poll() is not None:
        return
    if os.name == "nt":
        # Le PID appartient au Popen encore vivant, jamais a un registre ancien.
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                       capture_output=True, timeout=15,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        os.killpg(p.pid, signal.SIGKILL)
    p.wait(timeout=15)


def executer(commande, cwd, sortie, erreurs, limite, annoncer, au_depart=None):
    debut = time.monotonic()
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    p = None
    depasse = False
    with open(sortie, "wb") as stdout, open(erreurs, "wb") as stderr:
        try:
            p = subprocess.Popen(commande, cwd=cwd, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, **kwargs)
            if au_depart:
                au_depart(p.pid)
            prochaine = 0
            while p.poll() is None:
                ecoule = time.monotonic() - debut
                if ecoule >= limite:
                    depasse = True
                    arreter(p)
                    break
                if ecoule >= prochaine:
                    annoncer(f"{ecoule:.0f} s — {derniere_etape(erreurs)}")
                    prochaine = ecoule + 5
                time.sleep(0.1)
        finally:
            if p is not None:
                arreter(p)
    return {"code_sortie": p.returncode, "limite_atteinte": depasse,
            "duree_reelle_s": round(time.monotonic() - debut, 3),
            "derniere_etape": derniere_etape(erreurs),
            "sortie": str(sortie), "erreurs": str(erreurs)}


def derniere_etape(chemin):
    try:
        with open(chemin, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 8192))
            lignes = f.read().decode("utf-8", errors="replace").splitlines()
        for ligne in reversed(lignes):
            try:
                d = json.loads(ligne)
                if isinstance(d, dict) and d.get("etape"):
                    return f'{d["etape"]} — {d.get("secondes_simulees", "?")} s simulees' + (
                        "; " + d["message"] if d.get("message") else "")
            except ValueError:
                pass
    except OSError:
        pass
    return "processus demarre, aucune progression recue"
