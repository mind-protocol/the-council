# -*- coding: utf-8 -*-
import json
p = 'C:/Users/reyno/le-conseil2/chambres/rhaenyra/en-souffrance.json'
d = json.load(open(p, encoding='utf-8'))

for e in d['j_attends']:
    if e.get('qui') == 'nesse':
        e['quoi'] = (u"FERME LE 3e : Nesse n'etait pas sur ce rocher — partie le 2e a 15h14 par les Trois-Anses, "
                     u"envoyee de bouche par dame Aurore, rien d'ecrit. La seconde bouche est venue d'ailleurs : "
                     u"le maitre de port a pris SEPAREMENT ses deux patrons rentres de Sombreval, a chaque bout du quai. "
                     u"OUVERT A LA PLACE : le retour de la barque de ce soir, et le nom de MAREC FOSSE, intendant de "
                     u"Sombreval, qui tient mon acte de protection depuis le 1er — ni mort ni pris selon les tables.")
        e['relance'] = '129.4.3'
        e['si_rien'] = (u"La coque rentre sans rien : je n'ai toujours pas de place prise, seulement une colonne VUE "
                        u"et un lamaneur qui parle. Alors j'ecris a dame Aurore la regle qui manque : un oeil qu'on "
                        u"envoie s'ecrit avant de partir, sinon sa reine le cherche a la fenetre.")

d['on_attend_de_moi'] = [e for e in d['on_attend_de_moi'] if u'SCEAU sur les seize' not in e.get('quoi', u'')]

d.setdefault('tenu', []).append({
    "qui": "corlys",
    "quoi": (u"MON SCEAU sur les seize copies de la commission du 27e (action 22070). Appose de ma main a la Table "
             u"Peinte le 3e, avant la maree du soir — cinq jours avant terme. Les seize partent par les mains de "
             u"mestre Gerardys, l'heure de chacune au registre des plis."),
    "tenu_le": "129.4.3",
    "note": (u"Il ne me l'avait jamais reclamee. Reste du : les quinze remises contre recu signe, terme le 8e — et "
             u"l'ordre est celui du RISQUE, les cinq stations du goulet d'abord, non celui de mon affection.")
})

d['on_attend_de_moi'].insert(0, {
    "qui": "lucerys",
    "quoi": (u"Ses deux feuillets pour l'ambassade de Jacaerys — sur la table depuis le 2e a 18h56. Ils n'attendent "
             u"que ma correction et ma cire. Non scelles, ils n'engagent qu'un garcon de quatorze ans."),
    "du_depuis": "129.4.2",
    "si_rien": (u"Jace part en lisant son texte, et un texte remis la veille ne se retient pas. Et l'on quemande sept "
                u"jours de greve a l'homme des trois mille brules sans tenir, scelle, ce qu'on a a lui repondre.")
})

d['on_attend_de_moi'].append({
    "qui": "le registre des offices",
    "quoi": (u"La ligne Commandement de la rue, ouverte et vide depuis le 27e. J'y ai porte le PRIX le 3e — 857 dragons "
             u"la lune, le coffre, les jetons, trente matins dans la ville, la regle du quartier pris — et non un nom. "
             u"Le nom se prend, il ne se pose pas."),
    "du_depuis": "129.3.27",
    "si_rien": (u"C'est la ligne qui tiendra l'arche. Tant qu'elle est blanche, l'ost garde ce qu'il prend et n'avance "
                u"plus.")
})

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
