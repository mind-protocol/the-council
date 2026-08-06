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

cd "$(dirname "$0")/.." || exit 1

DOSSIER=${GUETTEUR_DIR:-etat/inbox}
case "$1" in
  etat/inbox*|*/inbox/*) DOSSIER=$1; shift ;;
esac
mkdir -p "$DOSSIER"
connus=" $* "
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
    exit 0
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
