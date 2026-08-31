# -*- coding: utf-8 -*-
import json, io

p = 'books/affaire-marec-fosse.json'
d = json.load(io.open(p, encoding='utf-8'))

etats = {
 'P.1': ('faite','129.4.3','Lu en entier. Ce qu on disait de moi, je le tiens sauf un mot.'),
 'P.2': ('faite','129.4.3','Six phrases en « je » sous le semé.'),
 'P.3': ('bloquée','','TENU sur le fond, REFUSÉ à la pose : lot laissé à etat/staging/20260831-sombreval-marec-fosse-passe-an-109.json. Mon passé est à la porte de l état, pas dedans. L arbitre a gravé trente et un ans et non trente-deux : la table gagne sur le souvenir.'),
 'P.4': ('faite','129.4.3','Trois états visés, chacun avec sa preuve.'),
 'P.5': ('faite','129.4.4','Deux fois. Le 3e : ser Steffon a lu mon nom dans une colonne muette. Le 4e : mon maître est mort et ma règle de vingt ans a perdu le nom qu elle portait au bout.'),
 'P.6': ('faite','129.4.4','Trois verrous posés et quatre actions à moi, sous ces colonnes.'),
 'P.7': ('faite','129.4.4','problemes.json : trois entrées. en-souffrance.json : deux fils, dont un que je dois à quelqu un.'),
 'P.8': ('faite','129.4.4','Demandé où était mon maître. La réponse a fait tomber ma règle.'),
 'P.9': ('faite','129.4.4','Un TENTER (le recompte, 204 muids au boisseau) et un FAIRE (le pli rendu contre reçu à Willam Wode), tous deux tranchés.'),
 'P.10': ('faite','129.4.4','Écrit à ser Steffon Darklyn à Peyredragon : la mort de son frère, mon chiffre, et la seule question que j aie à poser — de qui je prends la signature.'),
}

acts = None
for t in d['tables']:
    if t['titre'].endswith('Actions'):
        acts = t
        for l in t['lignes']:
            c = l['cellules']
            if c[0] in etats:
                e, jf, note = etats[c[0]]
                c[5] = e
                c[7] = jf
                c[8] = note

nouvelles = [
 ['M.1','Compter les caves de la citadelle au boisseau',
  'Cent douze muids y dorment, plus de la moitié du pain de la ville, et je ne les ai pas comptés moi-même : j ai écrit « pleines ». On ne répond pas « pleines » à un homme armé.',
  'les caves de la citadelle','un chiffre au boisseau, de ma main, avec sa date','à faire','129.4.5','',
  'La citadelle est à l ost depuis le 3e. Compter chez eux, c est leur montrer ce qu il y a. Je le ferai quand même : un secret ne nourrit personne, un chiffre faux tue.'],
 ['M.2','Recompter les bouches de la ville',
  'Mon rôle des bouches est du 27e au soir, d avant le sac. Je n ai compté ni les morts ni les fuis. Mes cinquante et une journées de pain ont un numérateur vrai et un dénominateur vieux, et je le dis chaque fois que je donne le chiffre.',
  'la ville','un rôle des bouches daté d après le sac','à faire','129.4.6','',
  'Tant que ce n est pas fait, je ne certifie pas les journées et je le déclare en les donnant.'],
 ['M.3','Ouvrir la colonne des titres revendiqués',
  'Une colonne neuve à mon registre : qui a ordonné, la date, et SOUS QUEL TITRE il prétend ordonner, dans ses propres mots. Première ligne déjà écrite : Willam Wode, 4e, « par ordre scellé de ser Criston Cole, Lord Commandant de la Garde Royale, pour la place de Sombreval ».',
  'mon registre','la colonne existe et porte sa première ligne','faite','','129.4.4',
  'C est ce qui reste de ma règle quand le nom au bout a disparu. Un registre qui ne peut plus dire qui a ordonné peut encore dire qui a prétendu ordonner.'],
 ['M.4','Obtenir une signature pour le pain de la ville',
  'Quatre muids par jour sortent pour le pain de Sombreval. Depuis le 3e ils sortent sans ordre de personne, parce qu il n y a plus personne à qui le demander. Je continue de les faire sortir — la ville mange — et j écris chaque jour en clair qu ils sortent SANS ORDRE, sur ma seule décision.',
  'aux granges','une ligne signée, ou une ligne qui dit qu on a refusé de signer','en cours','','',
  'Je ne me couvre pas : je me découvre par écrit. Le jour où l on me demandera de quel droit, la réponse sera datée et de ma main.'],
]
for n in nouvelles:
    acts['lignes'].append({'cellules': n})

verrous = {
 'titre': u'\U0001f512 Verrous',
 'colonnes': [u'\U0001f512 N°', u'\U0001f3f7️ Le verrou', u'\U0001f3af Ce qu il bloque',
              u'⚠️ Ce qui est vrai aujourd hui', u'\U0001f441️ La preuve',
              u'\U0001f5dd️ Ce qui le lèverait'],
 'lignes': [
  {'cellules':[
    'V.1',
    'Plus de la moitié du pain de Sombreval est sous la citadelle, et la citadelle est à l ost',
    'Voir la ville passer l hiver',
    'Sur mes 204 muids comptés, 112 sont dans les caves de la citadelle, tenue par l ost depuis le 3e. Il n en reste que 92 derrière mes portes, soit 23 journées de pain et non 51. Mes clefs y ouvrent encore ; les leurs aussi. Ce n est ni un vol ni une saisie : c est du grain qui a changé de main sans que personne ait signé. UN REGISTRE QUI DIT 204 DIT VRAI ET TROMPE : le stock d une ville et ce qu une ville peut en tirer sont deux chiffres différents, et le second n a jamais été écrit nulle part.',
    'mon compte au boisseau, cave par cave, du 4e de la 4e lune',
    'Remonter le grain des caves derrière mes serrures ; ou, à défaut, un ordre signé qui dise à qui ces 112 muids appartiennent.']},
  {'cellules':[
    'V.2',
    'Aucune main au monde ne peut signer un ordre valable sur les granges de Sombreval',
    'Que rien ne sorte d une grange sans un ordre',
    'Lord Gunthor est mort le 3e. Robin Darklyn, l héritier, est vivant et prisonnier dans la ville. Ser Steffon Darklyn est à Peyredragon et rien ne le nomme lord de quoi que ce soit. Aucune succession n est écrite nulle part. Chaque muid qui sort depuis le 3e sort sans ordre — y compris les quatre du pain quotidien, que je fais sortir moi-même.',
    'réponse des registres à ma demande du 4e : « personne ne tient Sombreval à la place de ton maître, un ost la tient à la place de sa maison »',
    'Qu une succession soit écrite. À défaut, et c est ce que je fais : inscrire le TITRE REVENDIQUÉ à côté de chaque ordre, dans les mots de celui qui l emploie.']},
  {'cellules':[
    'V.3',
    'L ost mange en moins de deux jours ce que la ville a pour cinquante et un',
    'Voir la ville passer l hiver',
    '2 202 hommes debout, une fonte de huit par jour, à vingt hommes le muid : 111 muids par jour. Il a trois journées de pain dans son train. Mes 204 muids lui font un jour et vingt-deux heures. Les 180 muids qu on devait me demander le 30e : quarante-cinq journées de pain ôtées à Sombreval, trente-neuf heures données à l ost. Ser Criston a pris cette ville sans presque toucher à son grain — vingt-quatre muids sur deux cent vingt-huit — mais son train finit dans trois jours.',
    'mes deux rôles arrêtés au soir du 4e, brouillons/les-deux-roles-129-4-4.md',
    'Que l ost s en aille, ou qu il soit nourri d ailleurs que de Sombreval. Il n y a pas de troisième terme : cette ville ne peut pas nourrir cet ost, et personne des deux camps ne l a encore écrit.']},
 ]
}
d['tables'].insert(1, verrous)

d['pages'].append({
 'titre': 'Ce que ce volume est devenu, au 4e de la 4e lune',
 'texte': "Les dix pas de la prise en main sont faits, sauf un que la porte a refusé. Ce volume cesse donc d etre une prise en main.\n\nCe que j y écris désormais est mon office : le grain, les bouches, et qui a prétendu ordonner. J ai posé trois verrous, et aucun des trois n est une inquiétude : chacun passe le test — si tout le reste était acquis et que celui-là restait vrai, Sombreval ne passerait pas l hiver.\n\nLe premier est le seul que personne d autre ne pouvait trouver. On l obtient en montant les escaliers avec un trousseau, pas en lisant un total."
})

json.dump(d, io.open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', [t['titre'] for t in d['tables']], len(acts['lignes']))
