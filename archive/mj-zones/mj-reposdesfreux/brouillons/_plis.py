import json, sys
sys.stdout.reconfigure(encoding='utf-8')
root = 'C:/Users/reyno/le-conseil2/'
d = json.load(open(root + 'etat/plis.json', encoding='utf-8'))
items = d['plis'] if isinstance(d, dict) and 'plis' in d else d
if isinstance(items, dict):
    items = list(items.values())
print('total plis', len(items))
for p in items:
    if 'freux' in json.dumps(p, ensure_ascii=False).lower() or p.get('pour') == 'lord-staunton' or p.get('de') == 'lord-staunton':
        print(p.get('id'), '|de', p.get('de'), '|pour', p.get('pour'), '|de-lieu', p.get('depuis'), '->', p.get('vers'),
              '|', p.get('canal'), '|', p.get('parti_le'), '|', p.get('etat'))
