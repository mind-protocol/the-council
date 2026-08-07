#!/bin/sh
# Guetteur d'inbox : attend qu'un fichier NOUVEAU apparaisse dans etat/inbox/,
# puis sort en listant tout ce qui s'y trouve. Ignore les fichiers deja presents
# au moment de l'armement (passes en arguments).
#
# Il MEURT en sonnant : c'est sa fin de processus qui reveille le MJ. Il faut
# donc le reamorcer a chaque tour, et EN PREMIER (voir CLAUDE.md, point 6) —
# tant qu'il est eteint, les actions du joueur s'empilent en silence.
#
# Filet de securite : il rend aussi la main au bout de LIMITE secondes sans
# rien recevoir. Un reamorcage oublie se repare donc tout seul au cycle
# suivant, au lieu de durer jusqu'a ce que le joueur s'en apercoive.
#
# A DEUX MJ : chaque session guette SON joueur. On passe le dossier en premier
# argument (ou par GUETTEUR_DIR) :
#     scripts/guetteur.sh etat/inbox/daemon [fichiers deja connus...]
# Sans argument de dossier, c'est etat/inbox/ — le comportement d'une partie
# seule, inchange.
LIMITE=${GUETTEUR_LIMITE:-1200}

# --code-reveil : sortir 2 (et non 0) quand une action arrive.
# C'est ce que reclame un hook `asyncRewake` : il ne reveille le MJ que sur un
# code 2. L'expiration garde 0, sinon on se ferait reveiller par le silence.
CODE_ACTION=0
for a in "$@"; do
  if [ "$a" = "--code-reveil" ]; then CODE_ACTION=2; fi
done

cd "$(dirname "$0")/.." || exit 1

DOSSIER=${GUETTEUR_DIR:-etat/inbox}
case "$1" in
  etat/inbox*|*/inbox/*) DOSSIER=$1; shift ;;
esac
mkdir -p "$DOSSIER"

# --auto : prendre soi-meme l'empreinte de l'inbox au lieu de se faire dicter la
# liste des fichiers deja vus. C'est LE geste qui rate quand on reamorce a la
# main — on oublie un nom, le guetteur sonne aussitot dans le vide, et de faux
# reveils en faux reveils on finit par ne plus le rallumer du tout. Avec --auto,
# reamorcer est toujours la MEME commande, quel que soit ce qui traine :
#     scripts/guetteur.sh etat/inbox/<joueur> --auto
# Ce qui est la au moment de l'armement est repute deja traite ; seule une
# action NOUVELLE reveille le MJ.
if [ "$1" = "--auto" ]; then
  shift
  connus=" "
  for f in "$DOSSIER"/*.json; do
    [ -e "$f" ] || continue
    connus="$connus$(basename "$f") "
  done
else
  connus=" $* "
fi
ecoule=0
while :; do
  for f in "$DOSSIER"/*.json; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    case "$connus" in
      *" $base "*) continue ;;
    esac
    # Bruit connu : des apercus PNG de plusieurs centaines de Ko atterrissent
    # parfois dans l'inbox. Ce n'est pas une action de jeu — on les ecarte
    # sans reveiller le MJ, sinon le guetteur sonne dans le vide.
    if grep -q '"apercu-ville"' "$f" 2>/dev/null; then
      rm -f "$f"
      continue
    fi
    echo "NOUVELLE ACTION : $base"
    for g in "$DOSSIER"/*.json; do
      echo "== $g"
      cat "$g"
      echo
    done
    exit "$CODE_ACTION"
  done
  if [ "$ecoule" -ge "$LIMITE" ]; then
    echo "RIEN RECU depuis ${LIMITE}s — le guetteur rend la main. Reamorce-le."
    echo "(inbox au moment de l'expiration :)"
    ls -1 "$DOSSIER"/ 2>/dev/null || echo "  vide"
    exit 0
  fi
  sleep 3
  ecoule=$((ecoule + 3))
done
