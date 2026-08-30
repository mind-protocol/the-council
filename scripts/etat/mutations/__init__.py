"""Applique une proposition de etat/ a etat/*.json.

Usage :
    python scripts/appliquer.py tick-20260806-024652.json              -> blanc
    python scripts/appliquer.py tick-20260806-024652.json --vraiment   -> ecrit
    python scripts/appliquer.py <fichier> --vraiment --forcer          -> passe outre
                                                                          les gardes

Le pendant de scripts/tick.py. Le tick CALCULE et propose ; celui-ci APPLIQUE ce
que le MJ a validé. Entre les deux, le MJ relit la proposition et ajoute a la main
ses mutations narratives dans la liste "mutations_proposees" — ce que produit une
etape tombee, la croyance qu'une nouvelle installe, la tete qu'il vient de reecrire.

Trois gardes, dans cet ordre :
1. EMPREINTES — la proposition porte le sha1 des tables lues au moment du calcul.
   Si une table a bouge depuis, un autre ecrivain est passe : on refuse. C'est la
   protection contre deux sessions qui jouent en meme temps (voir CLAUDE.md).
2. VALIDATION — tout est verifie avant que rien ne soit ecrit : cible existante,
   operation connue, champs autorises, valeurs dans les enums. Une seule mutation
   invalide annule le lot entier.
3. ATOMICITE — ecriture par fichier temporaire puis remplacement, et le fichier de
   proposition est marque "applique_le" pour qu'on ne l'applique pas deux fois.

Vocabulaire des mutations — FERME, et c'est voulu : pas de chemin JSON arbitraire,
sinon n'importe quelle faute de frappe corrompt l'etat en silence.

    {table: "intentions", cible: <personnage_id>, operation: ...}
        etape            + etape: <id>, champs: {etat|jours_restants|quoi|cout|
                                                 si_bloque|depend_de|accompli}
        etape_ajouter    + valeur: <objet etape complet>
        tete             + champs: {echelle|intention|attitude_joueur|date_maj}
        croyance_ajouter | croyance_retirer   + valeur: <texte>
        ignore_ajouter   | ignore_retirer     + valeur: <texte>

    {table: "intentions", operation: "tete_ajouter", valeur: <objet intention>}
        CREE la tete d'un personnage qui n'en a pas encore (un dormant qu'on
        promeut). Pas de "cible" — le personnage_id est dans la valeur ; s'il y
        en a une, elle doit correspondre. La valeur porte personnage_id,
        echelle, croyances, intention, plan, date_maj (requis), et ignore,
        declencheurs, attitude_joueur (attendus). Refuse : une tete deja
        existante, un personnage inconnu de personnages.json, le personnage
        joueur (sa tete appartient au joueur), une echelle hors enumeration,
        une etape mal formee ou dont l'id est deja pris ailleurs dans le
        fichier, et tout depassement des budgets de l'echelle (docs/schema.md).

    {table: "evenements", cible: <evenement_id>, operation: ...}
        diffusion_livree   + index: <n>
        diffusion_ajouter  + valeur: <objet diffusion>
        evenement          + champs: {statut|effets|date_prevue|importance}

    {table: "personnages", cible: <personnage_id>, operation: "personnage",
     champs: {lieu_id|condition|etat}}

    {table: "monde", operation: "monde", champs: {date|tension|phase}}

    {table: "mains", cible: <main_id>, operation: ...}   (les mains)
        mesure     + mesure: <mesure_id>, champs: {valeur|reliquat}  ENTIERS SEULS
        seuil      + seuil:  <seuil_id>,  champs: {franchi_le}
        main   + champs: {mandat|porteur|dernier_rapport|date_maj|salle}
        Le reste d'une main (quoi, rythme, plancher, plafond, depend_de,
        libelle des seuils) s'ecrit a la main : ce sont des choix de conception,
        pas des mutations de partie.

    {table: "plis", cible: <pli_id>, operation: ...}   (le courrier)
        pli         + champs: {etat|main|attendu_le|canal|scelle|porte}
        Un pli remis, ouvert ou retenu DOIT avoir une main : c'est tout
        l'interet de la table (docs/plis.md). Un pli en route n'en a pas.
    {table: "plis", operation: "pli_ajouter", valeur: <objet pli complet>}
        Requiert id, canal, porte, de, pour, vers, parti_le, attendu_le, etat.
        `porte` est le texte FIGE au depart : on ne le relit pas a l'arrivee.

    {table: "jetons", cible: <incident_id>, operation: ...}   (la rumeur)
        incident_propage  + valeur: {ou, date, certitude, contenu, ames?,
                                     depuis?, note?}
            AJOUTE un endroit gagne a l'incident (docs/carte.md). `contenu` est
            OBLIGATOIRE et non vide : c'est ce qui se dit LA-BAS, deforme. Le
            tick propose le saut avec contenu null — le lot est refuse tant que
            le MJ n'a pas ecrit la prose. Une machine ne fabrique pas de
            brouillard. La certitude doit avoir DECRU d'au moins un cran par
            rapport au foyer : rien ne devient plus vrai en se repetant.
        incident          + champs: {feu|certitude|statut|ames|contenu|detail}

    {table: "lieux", cible: <lieu_id>, operation: "roukerie",
     champs: {<lieu_id d'origine>: <entier >= 0>}}
        Le stock de corbeaux. Un oiseau ne vole que vers la ou il est ne :
        ecrire de A vers B consomme lieux[A].roukerie[B].

Chaque mutation accepte un champ libre "pourquoi", ignore a l'application mais
precieux a la relecture.

Doc : docs/schema.md

CE PAQUET est la matiere de scripts/appliquer.py, descendue au lot 2
(docs/organisation.md §7) :

    vocabulaire.py    les enums, champs autorises, OPERATIONS, aides sans etat
    lecture.py        chemins des tables, lecture par la porte, empreintes
    validation.py     valider() - le cadre ; les branches par famille :
    val_plan.py       intentions (tetes, etapes, croyances)
    val_registres.py  books (affaires) et mains
    val_courrier.py   plis, jetons (rumeur), lieux (roukerie)
    val_social.py     evenements, personnages, relations, monde
    application.py    appliquer() et ecrire()
    cli.py            resumer() et main() - la commande

La facade scripts/appliquer.py et la porte etat/expose reexportent d'ici.
"""
import sys

# Comme l'ancien scripts/appliquer.py au chargement : les resumes portent des
# fleches et des accents, le shell d'ici est en cp1252.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from etat.mutations.vocabulaire import (  # noqa: E402,F401
    BUDGETS, ETATS_ETAPE, ETATS_ETAPE_VIVANTS, ECHELLES, STATUTS_EVENEMENT,
    ETATS_PERSO, CHAMPS_ETAPE, CHAMPS_TETE, CHAMPS_TETE_REQUIS,
    CHAMPS_EVENEMENT, CHAMPS_PERSO, CHAMPS_MONDE, CHAMPS_MESURE, CHAMPS_SEUIL,
    CHAMPS_MAIN, CANAUX_PLI, ETATS_PLI, ETATS_PLI_EN_MAIN, CHAMPS_PLI,
    CHAMPS_PLI_REQUIS, CERTITUDES, FEUX, CHAMPS_INCIDENT,
    CHAMPS_PROPAGE_REQUIS, OPERATIONS, TITRE_TABLE_ACTIONS,
    COLONNES_AFFAIRE_NEUVE, CHAMPS_PERSO_REQUIS, CHAMPS_MAIN_REQUIS,
    CHAMPS_RELATION, TYPES_PORTEUR, prochaine_ligne_action, liste_books,
    table_actions, plat_titre, charge_relation, rang_certitude, liste_jetons,
    liste_simple, date_lisible, normaliser_date)
from etat.mutations.lecture import (  # noqa: E402,F401
    SCRIPTS, RACINE, ETAT, STAGING, CROYANCES, chemin_table, lire,
    liste_mains, liste_plis, empreinte, par_id)
from etat.mutations.val_plan import valider_tete_neuve  # noqa: E402,F401
from etat.mutations.validation import valider  # noqa: E402,F401
from etat.mutations.application import appliquer, ecrire  # noqa: E402,F401
from etat.mutations.cli import resumer, main  # noqa: E402,F401
