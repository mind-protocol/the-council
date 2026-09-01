# -*- coding: utf-8 -*-
"""Un acte a mon nom au registre du monde dont tout le contenu est le mot TEST."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

A = 'etat/actes.json'
d = json.load(open(A, encoding='utf-8'))
liste = d['actes'] if isinstance(d, dict) else d
avant = len(liste)
mort = [x for x in liste if x.get('id') == 'acte-ormund-mon-trou-est-chez-mes-bannerets-129-5-12'
        and (x.get('quoi') or '').strip() == 'TEST']
if mort:
    liste[:] = [x for x in liste if x is not mort[0]]
    json.dump(d, open(A, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print("acte vide retire : %d -> %d" % (avant, len(liste)))
else:
    print("rien a retirer (%d actes)" % avant)

P = 'chambres/ormund-hightower/problemes.json'
p = json.load(open(P, encoding='utf-8'))
if not any('TEST' in json.dumps(e, ensure_ascii=False) for e in p['entrees']):
    p['entrees'].append({
     "jour": "129.5.12",
     "tente": "Une de mes journees a ecrit dans actes.json, sous mon nom et a l'heure de minuit, un acte intitule "
              "`acte-ormund-mon-trou-est-chez-mes-bannerets-129-5-12` dont tout le contenu tenait en un mot : TEST.",
     "obtenu": "Une ligne vide a mon nom dans le registre du monde. Le titre promet un fait — que mon trou est chez "
               "mes bannerets — et le corps ne le porte pas. C'est pire qu'une ligne absente : une ligne absente ne "
               "ment pas.",
     "attendu": "Soit l'acte, soit rien.",
     "contournement": "Retire. Le titre disait quelque chose de vrai et que je tiens toujours — mes quatre relais "
                      "tombent sur les terres de bannerets qui n'ont pas jure —, mais un fait ne s'ecrit pas par son "
                      "titre. Je le reecrirai quand je l'aurai compte, ou je ne l'ecrirai pas.",
     "levee": "129.5.12 — ligne retiree du registre.",
     "note": "REGLE : je n'ecris pas un acte pour eprouver une porte. Une porte s'eprouve sur ma propre table, pas "
             "dans le registre que d'autres liront. Et si je l'ai fait, je l'efface le jour meme — un homme dont la "
             "signature apparait sous le mot TEST n'est pas cru la fois suivante."
    })
    json.dump(p, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print("problemes : entree ecrite (%d au total)" % len(p['entrees']))
else:
    print("problemes : deja note")
