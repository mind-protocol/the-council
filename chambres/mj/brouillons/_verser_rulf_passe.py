# -*- coding: utf-8 -*-
import json, io

src = 'etat/staging/20260831-peyredragon-rulf-la-jambe-et-le-livre-an-107.json'
p = json.load(io.open(src, encoding='utf-8'))
passe = [b for b in p['a_la_main']
         if b.get('table') == 'etat/personnages.json'][0]['passe']

pourquoi = (
    "VERSE PAR MJ AU 129.4.3, MINUTE 721. mj-peyredragon avait ecrit ce passe "
    "dans un bloc a_la_main faute d'operation pour un champ libre de fiche ; "
    "l'operation personnage le prend tres bien. C'est une reparation de "
    "DONNEE, valable a n'importe quelle date : elle survit a une purge, "
    "contrairement a une ecriture de fiction. Elle donne son ancre aux "
    "vingt-deux ans de charge que Rulf compte partout, et la raison de sa "
    "regle — ce qui est ecrit sans avoir ete regarde n'est pas un fait."
)

neuve = {
    "titre": "Le passe de Rulf Corne pose sur sa fiche — la jambe et le livre, an 107",
    "par": "mj (versement du bloc a la main de 20260831-peyredragon-rulf-la-jambe-et-le-livre-an-107)",
    "mutations_proposees": [{
        "table": "personnages",
        "cible": "rulf-corne",
        "operation": "personnage",
        "champs": {"passe": passe},
        "pourquoi": pourquoi,
    }],
}
with io.open('etat/staging/20260831-mj-rulf-passe-verse.json', 'w',
             encoding='utf-8') as f:
    json.dump(neuve, f, ensure_ascii=False, indent=1)
print("ecrite")
