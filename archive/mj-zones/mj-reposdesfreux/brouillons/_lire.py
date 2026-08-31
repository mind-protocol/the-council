import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
root = 'C:/Users/reyno/le-conseil2'
path = sys.argv[1]
motif = sys.argv[2] if len(sys.argv) > 2 else 'reux'
d = json.load(open(os.path.join(root, path), encoding='utf-8'))
items = d
if isinstance(items, dict):
    for k in ('evenements', 'lieux', 'personnages', 'entrees', 'items', 'actes', 'annales'):
        if k in items:
            items = items[k]
            break
if isinstance(items, dict):
    items = [dict(v, _cle=k) if isinstance(v, dict) else {'_cle': k, 'v': v} for k, v in items.items()]
n = 0
for it in items:
    s = json.dumps(it, ensure_ascii=False)
    if motif.lower() in s.lower():
        n += 1
        print(json.dumps(it, ensure_ascii=False, indent=1)[:5000])
        print('-----')
print('total', n, 'sur', len(items))
