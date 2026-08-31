def r(nom, cerfs, dragons):
    print("%-52s %8.2f cerfs le dragon" % (nom, cerfs / dragons))

print("--- mes propres lignes, et le diviseur que chacune implique ---")
r("28022 solde : 7 200 cerfs le jour = 34 dragons", 7200, 34)
r("28022 solde : 216 000 cerfs la lune = 1 030", 7200 * 30, 1030)
r("28023 vivres : 108 000 cerfs la lune = 515", 1200 * 3 * 30, 515)
r("28024 chevaux : 24 000 cerfs la lune = 114", 800 * 30, 114)
r("28036 sergent : 5 cerfs le jour = 8 dragons 1/2 l'an", 5 * 365, 8.5)
r("28037 les douze : 2 160 cerfs la lune = 12 dragons", 12 * 6 * 30, 12)
r("26024 bras du bourg : 40 h. x 6 x 5 j = 6 dragons", 40 * 6 * 5, 6)
print()
print("--- la solde du Guet, meme compte, trois diviseurs ---")
c = 2000 * 3 * 30
for t in (209.71, 210.0, 211.76, 212.0, 214.71):
    print("  180 000 cerfs a %6.2f  ->  %7.2f dragons la lune" % (t, c / t))
print()
print("--- ce que l'ecart coute la ou il s'applique ---")
print("  857 - 849 = 8 dragons la lune, 96 l'an, sur la seule ligne du Guet")
tot = 1030 + 515 + 114
print("  et sur mes trois plus grosses lignes reunies (%d dragons la lune)," % tot)
print("  un point de diviseur en moins vaut environ %.1f dragons la lune" % (tot * (1 / 210.0 - 1 / 212.0) * 210.0))
