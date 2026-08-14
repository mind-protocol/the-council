# -*- coding: utf-8 -*-
# J'avais numerote a la mode du cahier d'a cote — deux etats en tete de bloc,
# verrous en 10, clefs en 20, actions en 30. Le guide dit autre chose, et la
# machine le lit comme le guide : UN BLOC DE CENT PAR ETAT CIBLE, verrous en 01
# a 09, clefs en 10 a 19, actions en 20 a 99. Mon 65010 se lisait clef alors
# qu'il est verrou. Corrige le jour meme, avant que personne l'ait ouvert.
import io, json, os, re, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOOKS = os.path.join(R, 'etat', 'books.json')

MAP = {
 "65000": "65000",   # etat  — du bois sous la hache
 "65001": "65100",   # etat  — l'aire tient un jour sans moi
 "65010": "65001",   # verrou — l'office ne peut engager
 "65011": "65101",   # verrou — deux bras sans terme
 "65012": "65102",   # verrou — la cadence n'est ecrite nulle part
 "65020": "65010",   # clef  — un plafond en cerfs
 "65021": "65110",   # clef  — un terme a la feuille
 "65022": "65111",   # clef  — le second du second
 "65030": "65020",   # action — demander le plafond
 "65031": "65120",   # action — porter le terme
 "65032": "65121",   # action — clouer la cadence
 "65033": "65122",   # action — un jour de bris a Wat
}

RE = re.compile(r"\b(650\d{2})\b")


def remap(s):
    if not isinstance(s, str):
        return s
    return RE.sub(lambda m: MAP.get(m.group(1), m.group(1)), s)


with io.open(BOOKS, encoding='utf-8') as f:
    books = json.load(f)

v = [b for b in books if b.get('id') == 'nera-l-aire-de-bris'][0]
v['sous_titre'] = v['sous_titre'].replace("Plage 65000 à 65099", "Plage 65000 à 65199")
for t in v['tables']:
    for l in t['lignes']:
        l['cellules'] = [remap(c) for c in l['cellules']]

# la ligne de plage, dans l'ouverture
for l in v['tables'][0]['lignes']:
    if 'PLAGE' in l['cellules'][0]:
        l['cellules'][1] = "**65000 à 65199** — deux blocs de cent, un par état cible"
        l['cellules'][2] = ("Millier 65 vérifié libre le 2e. **Un bloc de cent par état cible** : "
                            "verrous en 01 à 09, clefs en 10 à 19, actions en 20 à 99. "
                            "J'avais d'abord numéroté à la mode du cahier d'à côté et la lecture "
                            "s'en trouvait fausse — corrigé le jour même, avant que le volume ait été ouvert.")

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(BOOKS), suffix='.tmp')
os.close(fd)
with io.open(tmp, 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=1)
    f.write(u'\n')
os.replace(tmp, BOOKS)
print('renumerote — plage 65000 a 65199')
