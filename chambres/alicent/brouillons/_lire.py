import json, sys
for f in sys.argv[1:]:
    d = json.load(open('etat/books/%s.json' % f, encoding='utf-8'))
    print(d.get('id'), '|', d.get('tenu_par'), '|', d.get('titre'))
    for t in d.get('tables', []):
        print('==', t['titre'], t['colonnes'])
        for l in t['lignes']:
            print('   ', ' | '.join(str(x)[:90] for x in l['cellules'][:5]))
