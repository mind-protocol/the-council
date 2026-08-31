import subprocess, sys
verbe, dest, chemin = sys.argv[1], sys.argv[2], sys.argv[3]
t = open(chemin, encoding='utf-8').read()
r = subprocess.run(['python', 'scripts/parloir.py', verbe, '--de', 'hallis-roon', '--a', dest, t],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout[-8000:])
print('ERR', r.stderr[-800:])
