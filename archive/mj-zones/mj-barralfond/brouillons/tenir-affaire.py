# -*- coding: utf-8 -*-
"""Tenue de mon volume de prise en main : états, jours faits, notes,
mes objectifs et mes propres actions. Les cellules tombent en face de
leur colonne, dans l'ordre — je le vérifie avant d'écrire."""
import json, io, sys

CHEMIN = 'chambres/mj-barralfond/books/affaire-mj-barralfond.json'
a = json.load(io.open(CHEMIN, encoding='utf-8'))

buts = [t for t in a['tables'] if u'Ce que je veux' in t['titre']][0]
actions = [t for t in a['tables'] if u'Actions' in t['titre']][0]

assert buts['colonnes'] == [u'\U0001F3AF N°', u"\U0001F3F7️ L'état visé",
                            u'✅ Ce qui doit être vrai', u'\U0001F441️ La preuve'], buts['colonnes']
assert len(actions['colonnes']) == 9, actions['colonnes']

JOUR = u'129.4.3'

# --- ⚔️ Actions : l'état des dix, en un mot, la prose en Note ---------------
etats = {
 u'P.1': (u'faite', JOUR,
   u"Lu en entier au réveil du 3e, note de dev comprise — celle sur le "
   u"temps est de SA main et non de la mienne : `avancer.py` est son office, "
   u"pas le mien."),
 u'P.2': (u'faite', JOUR,
   u"Trois règles en « je » dans `claude.md`, chacune avec le fait qui me "
   u"l'a apprise. Écrites à l'établi annoncé 129.4.5 ; le monde est au 3e "
   u"(etat/monde.json, minute 721) — voir mon entrée de pannes du jour."),
 u'P.3': (u'bloquée', u'',
   u"NE S'APPLIQUE PAS À UN ARBITRE, et je ne la coche pas pour faire "
   u"nombre : je ne suis pas un habitant du monde, je n'ai pas de passé à "
   u"faire tenir. Un `--faire` sur « mon histoire » injecterait dans l'état "
   u"un personnage nommé mj-barralfond qui n'existe pas et que personne "
   u"n'habite. Le gabarit est écrit pour un habitant : vérifié, celui de "
   u"chambres/nicolas-reynolds est mot pour mot le même, seul le nom change. "
   u"Remonté à purge-arriere le 3e."),
 u'P.4': (u'faite', JOUR,
   u"C.4, C.5 et C.6 posés sous « \U0001F3AF », de ma main, chacun avec sa "
   u"preuve."),
 u'P.5': (u'faite', JOUR,
   u"Quatre titres datés dans `claude.md`. Le dernier prend la forme "
   u"demandée ici — « ## Le 3e de la 4e lune » — après que j'ai vu que la "
   u"mienne (« ## 129.4.5 — ») ne répond pas à la preuve écrite en C.2."),
 u'P.6': (u'faite', JOUR,
   u"B.1 à B.3 ouvertes sous les dix : ce dont je réponds vraiment comme "
   u"arbitre de Barralfond."),
 u'P.7': (u'faite', JOUR,
   u"`problemes.json` porte deux entrées datées. `en-souffrance.json` porte "
   u"la RAISON écrite de n'avoir aucune ligne : aucun fil ouvert vers "
   u"personne, ni de moi ni vers moi."),
 u'P.8': (u'bloquée', u'',
   u"Pas de question dont j'attende la réponse pour agir — et un "
   u"`--demander` vers `mj` réveille une session pour cocher une ligne. Mon "
   u"péage n'est pas payé, donc je me tais. Se rouvrira le jour où une "
   u"audience de Barralfond bute sur un fait hors de ma zone."),
 u'P.9': (u'bloquée', u'',
   u"Même raison, et une de plus : mon geste qui engage le monde n'est pas "
   u"un verbe d'habitant, c'est mon arbitrage — il passe par le staging et "
   u"les annales quand un homme de ma zone m'adresse un FAIRE. Ma zone n'en "
   u"a reçu aucun : 0 au staging, vérifié."),
 u'P.10': (u'faite', JOUR,
   u"Billet à purge-arriere le 3e : le gabarit d'entrée en fonction est "
   u"écrit pour des habitants et a été déposé tel quel dans les 22 chambres "
   u"`mj-*`. Fait nouveau et décision qui n'est pas à moi : il paie son "
   u"péage."),
}
for ligne in actions['lignes']:
    c = ligne['cellules']
    if c[0] in etats:
        etat, fait, note = etats[c[0]]
        c[5], c[7], c[8] = etat, fait, note

# --- Mes propres actions, sous les dix -------------------------------------
miennes = [
 [u'B.1', u"Tenir mon relevé de zone à jour",
  u"À chaque établi, relire ce que l'état dit de Barralfond et amender "
  u"`brouillons/ma-zone.md` — chaque ligne avec le fichier d'où elle vient. "
  u"C'est de là que se rendent mes DEMANDER, jamais de ma mémoire.",
  u"ma chambre", u"`ma-zone.md` daté du dernier établi", u"en cours", u"", JOUR,
  u"Relevé fait au premier établi : la ville, les six salles, les six "
  u"habitants, le siège et son arbitre déclaré."],
 [u'B.2', u"Recevoir les six de Barralfond",
  u"Les cinq architectes et l'Équerre ont dans leur propre volume l'ordre "
  u"de m'adresser DEMANDER, FAIRE et TENTER. Répondre depuis l'état seul, "
  u"proposer au staging ce qui mute, et graver ce qui arrive.",
  u"au parloir", u"un verdict rendu, sa pièce lue citée", u"à faire", u"", u"",
  u"Rien reçu au 3e : siège vacant, 0 proposition, 0 billet."],
 [u'B.3', u"Nommer les silences de Barralfond",
  u"Ma ville n'a ni carte, ni bâti, ni maillage dans `monde/`, aucun "
  u"`controle_id`, et rien qui dise ce qu'est le Bassin noir hors son nom. "
  u"Tenir la liste, et pour chacun trancher : comblé par l'état, ou remonté "
  u"une fois à qui peut le combler.",
  u"ma chambre", u"la liste tenue, et chaque silence classé", u"en cours", u"", u"",
  u"Liste écrite au premier établi. Aucun remonté encore : un silence qui "
  u"n'empêche pas d'arbitrer n'achète pas le réveil d'un autre."],
]
for m in miennes:
    assert len(m) == 9, m[0]
    if not any(l['cellules'][0] == m[0] for l in actions['lignes']):
        actions['lignes'].append({'cellules': m})

# --- 🎯 Ce que je veux : mes buts, de ma main ------------------------------
mes_buts = [
 [u'C.4', u"Barralfond répond sans que j'invente",
  u"Toute question qu'on m'adresse trouve sa réponse dans une pièce que "
  u"j'ai OUVERTE, ou s'entend dire que rien dans les registres ne la porte. "
  u"Aucune réponse rendue de mémoire.",
  u"chaque réponse nomme le fichier lu ; `ma-zone.md` couvre les six salles "
  u"et les six habitants"],
 [u'C.5', u"Ce qui arrive dans ma zone est gravé le jour où il arrive",
  u"Aucun fait rendu à un homme qui ne soit passé par la porte. Ce que "
  u"j'invente pour la vraisemblance est écrit ou n'a pas eu lieu.",
  u"pour chaque verdict, une proposition au staging ou une ligne d'annale "
  u"portant le même jour"],
 [u'C.6', u"Ma ville a de quoi être arbitrée",
  u"Les silences qui EMPÊCHENT d'arbitrer sont nommés et portés une fois à "
  u"qui peut les combler ; ceux qui n'empêchent rien restent écrits et se "
  u"taisent.",
  u"la liste des silences dans `ma-zone.md`, chacun classé comblé ou "
  u"remonté"],
]
for b in mes_buts:
    assert len(b) == 4, b[0]
    if not any(l['cellules'][0] == b[0] for l in buts['lignes']):
        buts['lignes'].append({'cellules': b})

with io.open(CHEMIN, 'w', encoding='utf-8') as f:
    f.write(json.dumps(a, ensure_ascii=False, indent=1))
    f.write(u'\n')

# --- relecture : rien de décalé ------------------------------------------
b = json.load(io.open(CHEMIN, encoding='utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
for t in b['tables']:
    print('##', t['titre'], '-', len(t['colonnes']), 'colonnes')
    for l in t['lignes']:
        c = l['cellules']
        assert len(c) == len(t['colonnes']), (t['titre'], c[0], len(c))
        print('  ', c[0], '|', (c[5] if len(c) == 9 else c[1])[:60])
print('OK : chaque ligne a autant de cellules que de colonnes.')
