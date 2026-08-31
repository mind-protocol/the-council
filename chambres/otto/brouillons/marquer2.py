# -*- coding: utf-8 -*-
import json

p = 'C:/Users/reyno/le-conseil2/chambres/otto/books/affaire-otto.json'
d = json.load(open(p, encoding='utf-8'))
t = [x for x in d['tables'] if 'Actions' in x['titre']][0]

maj = {
 'P.3': {
   4: u"FAIRE tranche au parloir : mon passe est retenu — six ans d'intendance de Villevieille sous mon frere Hobert, et le livre des sceaux de la Tour releve de ma main. La clause finale a ete refusee, et j'ai eu raison de la proposer plutot que de l'ecrire seul : ce n'est pas moi qui ai vu la cire de Largent.",
   5: u"faite", 7: u"129.4.3",
   8: u"Je ne tente pas mon passe, je le propose. Le monde en a retenu la moitie et corrige l'autre — c'est exactement ce a quoi sert un arbitre."},
 'P.7': {
   4: u"`problemes.json` : trois entrees datees du 129.4.3 (deux volumes pour une meme affaire, quatre plans servis vides, un parloir sans retour). `en-souffrance.json` : six fils, quatre que j'attends, deux qu'on attend de moi, chacun avec le jour de la demande et non celui du souvenir.",
   5: u"faite", 7: u"129.4.3",
   8: u"On me disait qu'`en-souffrance.json` n'avait jamais recu d'entree dans aucune chambre. Il en a six."},
 'P.10': {
   4: u"Billet porte a Orwyle, canal ouvert : `chambres/orwyle/relations/otto/discussion.json`. Deux canaux dans `relations/` — mj-portreal et orwyle.",
   5: u"faite", 7: u"129.4.3",
   8: u"Ecrit de facon a etre lu par un clerc ennemi sans dommage : je lui demande de me montrer une piece la ou elle est, non de me la porter."},
 'O.1': {
   5: u"bloquée",
   8: u"BLOQUEE PAR MA PROPRE JOURNEE, non par le monde. Trois choses tombees depuis ce matin la vident : ils sont deja payes et par une autre bourse (V4) ; il n'existe aucune page ou contresigner, Largent n'est dans aucun registre (V3) ; et l'office irregulier le protege au lieu de le desservir (V1). J'allais offrir a un homme rassasie un pain qu'il a deja. Le billet ne repart que porteur de K1 — la garantie de solde opposable au Tresor — et K1 se decide au conseil, pas sous ma cire."},
}

for l in t['lignes']:
    c = l['cellules']
    if c[0] in maj:
        for i, v in maj[c[0]].items():
            while len(c) <= i:
                c.append(u"")
            c[i] = v

# une action neuve, nee de la journee
t['lignes'].append({"cellules": [
 u"O.7",
 u"Retracer la bourse reelle de la solde du Guet de la 2e lune",
 u"Tirer du Tresor le role de solde du poste du Guet pour la 2e lune et le confronter au registre du payeur : d'ou l'argent est sorti, par quelles mains il a passe, ce qui manque au bout. Ne pas payer la 4e avant de savoir qui a paye la 2e — payer davantage sur une bourse deja pleine double le prix et laisse le lien a l'autre.",
 u"Tresor · bureau du payeur du froment",
 u"le role de la 2e lune confronte au registre, et le nom de la bourse d'origine ecrit",
 u"à faire",
 u"129.4.6",
 u"",
 u"Leve V4, et sans V4 leve la clef K1 se paie deux fois."]})

t['lignes'].append({"cellules": [
 u"O.8",
 u"Compter les bouches qui se sont tues une lune sur la cire de Largent",
 u"Tout le donjon le savait ; nul ne me l'a dit en une lune, et Orwyle l'a lache sans ouvrir un livre. Etablir qui, dans cette tour, etait en position de me le dire et ne l'a pas fait. Un silence tenu si longtemps par tant de bouches est une organisation, non un oubli — et c'est la chaine, non la cire, qui est le renseignement.",
 u"Donjon Rouge",
 u"une liste nommee des hommes en position de savoir, et la date a laquelle chacun l'a su",
 u"à faire",
 u"129.4.12",
 u"",
 u"Ne rien mettre par ecrit de cette liste qui puisse etre lu par le nomme lui-meme."]})

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for l in t['lignes']:
    print(l['cellules'][0], '->', l['cellules'][5])
