import json, sys
sys.stdout.reconfigure(encoding='utf-8')
root = 'C:/Users/reyno/le-conseil2/'
d = json.load(open(root + 'etat/evenements.json', encoding='utf-8'))
items = d['evenements'] if isinstance(d, dict) and 'evenements' in d else d
if isinstance(items, dict):
    items = list(items.values())
mode = sys.argv[1] if len(sys.argv) > 1 else 'liste'
if mode == 'liste':
    for it in items:
        dp = it.get('date_prevue') or {}
        print(it.get('id'), '|', dp.get('annee'), dp.get('lune'), dp.get('jour'), '|',
              it.get('type'), '|', it.get('statut'), '|', it.get('lieu_id'), '|', it.get('importance'))
else:
    for it in items:
        if it.get('id') == mode:
            e = dict(it)
            e.pop('diffusion', None)
            print(json.dumps(e, ensure_ascii=False, indent=1))
            for df in it.get('diffusion', []):
                print('DIFF ->', df.get('ou'), df.get('qui'), df.get('date'), df.get('canal'), df.get('livree'))
