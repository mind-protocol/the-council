# -*- coding: utf-8 -*-
import io, json

base = 'C:/Users/reyno/le-conseil2/chambres/otto/'

# --- problemes.json : la recidive est confirmee, et nuancee -----------------
p = base + 'problemes.json'
d = json.load(open(p, encoding='utf-8'))
for e in d['entrees']:
    if e['quoi'].startswith('Trois gestes au parloir'):
        e['quoi'] = u"Le parloir repond, mais en un temps qui va de trois secondes a plus d'un quart d'heure"
        e['obtenu'] = (u"Deux jours de mesures. Le 3e au matin : --dire passe en secondes, --faire revient "
                       u"en trois minutes, --demander et --tenter restent dehors au-dela de vingt minutes "
                       u"et un --tenter n'est jamais revenu. Le 3e apres midi : le meme --demander revient "
                       u"au bout de vingt-cinq minutes environ, et sa reponse etait la meilleure de ma "
                       u"journee — le taux du manteau d'or, l'arriere, le seuil, et la contradiction du "
                       u"coffre. Deux --faire de suite reviennent, l'un en quelques minutes, l'autre "
                       u"toujours dehors a l'heure ou je ferme.")
        e['attendu'] = (u"Je croyais tenir une panne de deux verbes. Ce n'est pas cela : c'est une latence "
                        u"tres etalee, sans rapport avec la longueur de ma demande. Je retire mon "
                        u"hypothese d'hier plutot que de la laisser courir.")
        e['consequence'] = (u"Regle de travail que j'en tire et que je garde : je lance le geste au parloir "
                            u"EN PREMIER et je travaille pendant qu'il court, au lieu de l'attendre. J'ai "
                            u"perdu une demi-journee hier a attendre, et gagne toute celle-ci a ne plus "
                            u"attendre. Ce qui n'est pas revenu quand je ferme, je le releve au reveil.")
        e['etat'] = u"requalifiee le 129.4.3 : ce n'est pas une panne, c'est une latence — je m'organise avec"
d['entrees'].append({
 "jour": "129.4.3",
 "quoi": u"Le plan de la Couronne n'est pas un livre : on ne peut rien y verser",
 "tente": (u"Porter mes verrous du jour dans le plan `couronne` (plage 72000-72999), la ou sont les "
           u"pieces qu'ils bloquent — 72001, 72100, 72103, 72112."),
 "obtenu": (u"`etat/plans.json` n'est pas dans la bibliotheque que `verser_cahier.py` ouvre : le verseur "
            u"ne travaille que sur `etat/books/`. Une coordonnee visant `couronne` aurait ete refusee "
            u"en « livre inconnu », et je ne l'aurais peut-etre pas su."),
 "attendu": u"Pouvoir ecrire un verrou la ou est l'etat cible qu'il bloque.",
 "consequence": (u"Contourne sans perte : j'ai verse dans deux livres que je tiens — "
                 u"`affaire-la-chaine-d-office-du-guet` et `affaire-le-grain-paye-avant-decrit` — et j'ai "
                 u"ecrit les numeros du plan (72000, 72100, 72103, 72112, 72411) dans la colonne "
                 u"« Bloque ». La chaine se lit, meme si elle traverse deux registres. Je le note parce "
                 u"qu'un autre s'y cassera les dents et perdra son travail en silence."),
 "etat": "ouverte — contournee, non resolue"
})
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# --- en-souffrance : Criston, et l'arbitre ---------------------------------
q = base + 'en-souffrance.json'
d = json.load(open(q, encoding='utf-8'))
d['on_attend_de_moi'] = [x for x in d['on_attend_de_moi'] if not x['qui'].startswith('Ser Criston')]
d['on_attend_de_moi'].insert(0, {
 "qui": "Ser Criston Cole, Lord Commandant",
 "quoi": (u"Un chiffre porte en prive, promis avant les cloches du 29e. Cinq jours de retard, et la "
          u"colonne n'est pas sortie le 30e pour cette raison-la, qu'il a ecrite lui-meme."),
 "depuis": "129.3.28",
 "jours": 5,
 "note": (u"RENDU le 3e, en deux billets du meme jour. Le premier disait la forme — une avance et non une "
          u"prime — et refusait le montant, parce que deux livres du roi donnent le coffre a un contre "
          u"soixante-dix. Le second, l'apres-midi, donne le montant : trente cerfs par tete, dix jours de "
          u"solde au taux ecrit, quatre cent quarante-trois dragons pour les trois mille cent, signes le "
          u"5e a l'aube. J'ai annule mon propre premier billet en une apres-midi et je le lui ai dit en "
          u"toutes lettres : mon premier chiffre etait faux de quatorze mois de solde. Un homme qui se "
          u"corrige devant vous vous a dit quelque chose sur lui ; j'ai prefere que ce soit moi qui le "
          u"lui dise."),
 "etat": "rendu le 129.4.3 — reste du a l'aube du 5e, et il peut me le reclamer"
})
d['on_attend_de_moi'].insert(1, {
 "qui": "Ser Criston Cole",
 "quoi": u"Un entretien seul, avant que l'ordre de depart de la colonne soit signe.",
 "depuis": "129.4.3",
 "jours": 0,
 "note": (u"Demande deux fois dans la journee, par les deux billets. Ce que j'ai a lui dire ne s'ecrit "
          u"pas : ce qui reste dans ces murs quand deux mille six cents hommes en seront sortis, et la "
          u"date a laquelle ce qui reste cesse de tenir. Je porte moi-meme ce qui doit etre remis en main "
          u"propre — s'il ne vient pas avant vepres, je vais a lui."),
 "etat": "ouvert, du avant le 5e"
})
for e in d['j_attends']:
    if e['de_qui'].startswith('mj-portreal'):
        e['quoi'] = (u"Le verdict de ma correction du soir : la suspension de mes quatre ecritures, le "
                     u"versement de l'arriere du Guet avec l'affectation de sa solde courante, et l'avance "
                     u"refaite a trente cerfs par tete.")
        e['note'] = (u"Les deux verdicts d'hier sont caducs : le premier a ete rendu par un autre chemin "
                     u"— Largent ne figure sur aucune table du royaume — et le second ne reviendra pas. "
                     u"Celui-ci est le seul qui compte et il court encore quand je ferme. Je le releve au "
                     u"reveil avant toute autre chose : c'est de lui que depend ce que je signe le 5e a "
                     u"l'aube.")
        e['etat'] = u"en cours au moment ou je ferme le 3e"
json.dump(d, open(q, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# --- affaire-otto : la journee ---------------------------------------------
r = base + 'books/affaire-otto.json'
d = json.load(open(r, encoding='utf-8'))
t = [x for x in d['tables'] if 'Actions' in x['titre']][0]
for l in t['lignes']:
    c = l['cellules']
    if c[0] in ('P.8', 'P.9'):
        c[5] = u"faite"
        c[7] = u"129.4.3"
        if c[0] == 'P.8':
            c[4] = (u"`--demander` du 3e sur le taux et la solde de depart : verdict rendu. Il m'a donne "
                    u"le taux du manteau d'or, l'arriere du Guet avec sa pente et son seuil au 20e, "
                    u"l'absence totale de precedent de solde de depart, et une contradiction d'un contre "
                    u"soixante-dix sur le coffre. C'est la meilleure chose de ma journee et je ne pouvais "
                    u"la savoir seul.")
        else:
            c[4] = (u"Quatre `--faire` tranches ou en cours le 3e : mon passe, les quatre ecritures, leur "
                    u"suspension, et leur correction. Le troisieme a arrete le second avant qu'il entre "
                    u"au livre.")

t['lignes'].append({"cellules": [
 u"O.10",
 u"Faire compter le coffre piece par piece et relever la pente trois jours",
 u"Deux livres du roi donnent le coffre a un contre soixante-dix : six cent mille dragons contre huit mille six cents, et le second descend de vingt et un mille cerfs par jour. Desceller devant le gardien nomme le 28e et deux clercs qui ne se connaissent pas ; un chiffre arrete, signe des trois ; la pente relevee trois jours de suite. Un chiffre qui descend a ete compte, un chiffre rond et immobile a ete rapporte.",
 u"chambre des comptes",
 u"un seul chiffre signe des trois, et trois releves de pente",
 u"en cours",
 u"129.4.5 au soir",
 u"",
 u"Ne clot PAS avant le soir du 5e : trois releves a partir du 3e ne se lisent pas avant. J'avais dit que je signerais le 5e au matin — c'etait signer sur la moitie de ma propre epreuve, et c'est la faute que je venais d'ecrire dans mon cahier."]})
t['lignes'].append({"cellules": [
 u"O.11",
 u"Voir Criston seul avant que l'ordre de depart soit signe",
 u"Lui dire de vive voix ce qui ne s'ecrit pas : l'ost sort le 5e, la garde des portes a un terme ecrit au 20e, cent vingt lances sans maitre dorment dans les murs depuis le 22 et onze d'entre elles gardent trois quilles de guerre sur la Nera pour un maitre que personne ne sait nommer. Quatre pieces ecrites dans quatre livres et jamais posees ensemble.",
 u"Tour de la Main, ou la ou il est",
 u"l'entretien tenu, sans clerc, avant la signature de l'ordre",
 u"à faire",
 u"129.4.4",
 u"",
 u"Demande deux fois par billet le 3e. S'il ne vient pas avant vepres, je vais a lui : je porte moi-meme ce qui doit etre remis en main propre."]})
t['lignes'].append({"cellules": [
 u"O.12",
 u"Choisir la main de garde de chaque bref de pupille sur l'origine de son brevet",
 u"Quatorze de mes dix-neuf gages sont gardes par des officiers brevetes de la main de Daemon Targaryen : quatre maisons tenues, sept qui se croient tenues. Avant de faire sortir un seul bref neuf, verifier de qui le geolier tient son pain. Mieux vaut quatre gages qu'on tient que dix-neuf qu'on croit tenir.",
 u"role des maisons de la Couronne",
 u"pour chaque bref, l'origine du brevet du gardien ecrite a cote du nom de l'enfant",
 u"à faire",
 u"129.4.7",
 u"",
 u"J'ai passe une lune a etablir qu'un homme tient a la cire dont il tient sa commission, et j'allais confier mes otages a des geoliers commissionnes par mon ennemi. Terme des gages deja comptes : le 8e."]})
json.dump(d, open(r, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('clos.')
