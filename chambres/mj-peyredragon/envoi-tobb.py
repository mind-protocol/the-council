# -*- coding: utf-8 -*-
import io
import os
import subprocess
import sys

texte = io.open("chambres/mj-peyredragon/billet-tobb.txt",
                encoding="utf-8").read().strip()
cmd = [sys.executable, "scripts/parloir.py", "--dire",
       "--de", "mj-peyredragon", "--a", "tobb", texte]
env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"
r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
print(r.returncode)
print(r.stdout[-800:])
print(r.stderr[-800:])
