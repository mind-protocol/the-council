import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
def walk(o):
    if isinstance(o,dict):
        if 'lignes' in o and 'colonnes' in o:
            print('TABLE:',repr(o.get('titre')))
            print('  COLS:',o['colonnes'])
            print('  N:',len(o['lignes']))
        for v in o.values(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
walk(d)
