import json, sys
d = json.load(open('etat/plans.json', encoding='utf-8'))
for p in d['plans']:
    if p['id'] != 'baratheon':
        continue
    for k, v in p.items():
        if isinstance(v, list):
            print('===', k.upper(), '===')
            for x in v:
                if isinstance(x, dict):
                    print(' ', json.dumps(x, ensure_ascii=False)[:700])
                else:
                    print(' ', x)
        else:
            print(k, ':', str(v)[:600])
