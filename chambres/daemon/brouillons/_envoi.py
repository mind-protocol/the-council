# -*- coding: utf-8 -*-
import io, os, subprocess, sys

racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
racine = os.path.abspath(racine)
chemin = sys.argv[1]
dest = sys.argv[2]
verbe = sys.argv[3] if len(sys.argv) > 3 else "--dire"
with io.open(chemin, encoding="utf-8") as f:
    texte = f.read()
cmd = [sys.executable, os.path.join(racine, "scripts", "parloir.py"),
       verbe, "--de", "daemon", "--a", dest, texte]
sys.exit(subprocess.call(cmd, cwd=racine))
