# -*- coding: utf-8 -*-
import io, os
d = os.path.join(os.path.dirname(__file__), '..')
cahier = os.path.join(d, 'claude.md')
ajout = os.path.join(d, 'brouillons', 'amendement-3e-soir.md')
with io.open(cahier, encoding='utf-8') as f:
    a = f.read()
with io.open(ajout, encoding='utf-8') as f:
    b = f.read()
if u"une coque n'est ni un nom ni un volume" not in a:
    with io.open(cahier, 'w', encoding='utf-8') as f:
        f.write(a + b)
    print(u"cousu — deux titres de plus")
else:
    print(u"deja cousu")
