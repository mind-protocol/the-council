import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding='utf-8'))
sel = sys.argv[2] if len(sys.argv) > 2 else None
for t in d.get('tables', []):
    tt = t.get('titre')
    cols = [c.get('titre') if isinstance(c, dict) else c for c in t.get('colonnes', [])]
    if sel and sel not in tt:
        print('--', tt, cols)
        continue
    print('=== TABLE:', tt)
    print('COLS:', cols)
    for ln in t.get('lignes', []):
        if isinstance(ln, dict):
            cells = ln.get('cellules', ln)
            print(json.dumps(cells, ensure_ascii=False)[:1200])
        else:
            print(json.dumps(ln, ensure_ascii=False)[:1200])
    print()
