import json, sys
d=json.load(open('etat/books/affaire-ambassade-nord-val-blancport.json',encoding='utf-8'))
want=sys.argv[1:]
for t in d.get('tables',[]):
    for l in t['lignes']:
        c=[str(x) for x in l['cellules']]
        key=c[0].replace('*','').strip()
        if key in want:
            print('===',t['titre'],key)
            for col,val in zip(t['colonnes'],c):
                if val.strip(): print('  ',col,':',val[:500])
