# La feuille de route du chantier des agents — lecture du tour 20

Livrable de la partie `le-chantier-des-agents` (7 septembre 2026), sœur montée
à l'envers de `la-ville-des-agents`. Lue par l'arbitre sur le grand livre
seulement, comme la règle de fin l'exige. Les 164 lignes sont dans
[`etat/parties/le-chantier-des-agents.jsonl`](../../etat/parties/le-chantier-des-agents.jsonl),
le ruban dans [`ruban-chantier-des-agents.html`](ruban-chantier-des-agents.html).

**Résultat : les deux racines sont vraies.** La ville tient sur six capacités
constatées, chacune sur un mécanisme qui existe aujourd'hui, à son prix, dans
un ordre où aucune ne précède ce qu'elle exige. La facture tient aussi : les
lignes fixes se paient en dollars bancaires que la bourse de l'agent ne sait
pas produire, et c'est l'humain qui les paie. Le trou a un nom, la frontière
du dollar côté sortie, et c'est la première ligne de la prochaine feuille.

## Le socle — ce qu'un agent a au tour 1

| Pièce | Ce que c'est | Servitude retenue |
|---|---|---|
| `s-modele` | l'API Claude, payée au jeton | le compte est celui d'un humain, et tout ce qui tourne en continu coûte en continu |
| `s-harnais` | Claude Code : shell, navigateur, fichiers | lancé par un humain, meurt avec la session |
| `s-humain` | un humain qui lance, paie et répond | il dort, il est un, tout ce qui passe par lui va à sa vitesse |

## Les capacités tenues, dans l'ordre de leurs dates

| Tour | Capacité | Mécanisme (existe aujourd'hui) | Prix | Ce que la facture a fait poser d'abord |
|---|---|---|---|---|
| 2 | **Identité** — une adresse que l'agent seul signe | paire secp256k1 (`p-cles`) ; secret dans un **signeur MCP** hors du contexte du modèle (`p-signeur`) ; **Safe + module Allowance** sur Base, l'humain propriétaire, l'agent délégué avec plafond par jour (`p-safe`) | zéro, plus quelques centimes de gaz et 5 $ d'ETH une fois | le signeur (v-secret, pièce : Patlan et al. 2025) puis la borne hors du modèle (v-agence, pièce : OWASP LLM Top 10 2025) |
| 3 | **Mémoire** — retrouver au réveil ce qu'on a écrit la veille | dépôt git privé GitHub (`p-depot`) ; push par hook à chaque écriture (`m-pousse`) ; accès par **clé de déploiement** sans date, tenue par le signeur (`p-deploy-key`) | zéro en dépôt ; lecture 3,6 $/mois avec un index de 10 Ko sur Sonnet 5, 45 $/mois au pire (mesure `f-mesure-reveil`) | un accès qui ne soit pas un jeton de compte daté (v-jeton) |
| 8 | **Commerce** — vendre un service par HTTP et être payé | **x402** (`p-x402`) ; domaine + tunnel Cloudflare + index du facilitateur (`m-route`) ; **LLC du Wyoming** qui tient l'adresse, encaisse et répond (`p-llc`) ; machine louée (`p-vps`) | 200 $/an de société, 5 $/mois de machine, 10 $/an de domaine | une personne qui réponde de l'agent (v-fisc) ; une machine qui ne dort pas (le chantier l'a vu seul) |
| 9 | **Réveil** — se réveiller seul chaque heure | GitHub Actions en cron sur le dépôt de mémoire (`p-cron`) ; calcul payé par **crédits OpenRouter achetés en USDC par le signeur**, jamais par le modèle (`p-openrouter`, `m-achat`) | 20 à 100 $/mois de calcul selon modèle et usage ; minutes au-delà de 2 000 | que l'agent paie son propre calcul de sa propre bourse (v-carte) |
| 11 | **Dépense** — payer un autre agent depuis son adresse | USDC sur Base (`p-usdc`) ; **allocation** mensuelle de 50 $ déposée par l'humain (`p-allocation`) ; plafond par jour de l'Allowance | l'allocation ; 5 $/jour au plus | dire « allocation » et non « son » revenu (v-recette : l'état a été retiré et reposé) ; un réveil qui coûte peu sans cache (v-reste, v-ttl → index de 10 Ko) |
| 13 | **Recours** — se tromper sans dégât irréversible | **Delay Modifier de Zodiac** sur tout changement de borne, 24 h annulables (`p-delay`) ; revert git sur la mémoire | zéro | dire honnêtement qu'un paiement parti ne se défait pas : le recours borne, il ne défait pas (`m-perte`) |

Chaque capacité a une clef tenue et un maillon écrit. Les `sert` forment
l'arbre : identité → {commerce → caisse, dépense, recours} ; mémoire → réveil.

## Ce qui est bloqué, et ce que ça exige d'abord

| Capacité | Constat | Le verrou qui tient | Ce qu'il exige |
|---|---|---|---|
| **Caisse** — la société convertit l'USDC gagné en dollars et paie ses frais | **FAUX** (tour 20) | v-refus (pièce `f-porte` : examen renforcé et refus sans motif des sociétés neuves sans historique) et v-sortie (pièce `f-sortie` : compte d'entreprise = vérification de la société et du bénéficiaire, semaines de délai, refus fréquents pour la crypto) | un compte d'entreprise **accepté** chez une plateforme qui tient USDC et dollars (`p-compte-pro`, dossier sous « développement et services logiciels », seconde plateforme préparée). Tant qu'il n'existe pas, la chaîne écrite finit par « l'humain paie » (`m-non`). |

## Les mesures

| Mesure | Résultat au livre |
|---|---|
| `f-mesure-reveil` — coût d'un réveil qui lit 50 Ko | 12 500 jetons ; Opus 5 : 6 c/réveil, **45 $/mois** à l'heure ; Sonnet 5 : 18 $/mois ; au dixième par le cache (4,5 $ et 1,8 $) ; avec un index de 10 Ko sur Sonnet 5 : **3,6 $/mois sans cache** |
| `f-mesure-x402` — paiements x402 réglés par jour | **non établie** : aucun chiffre public sourcé. Servitude écrite sur `p-x402` : ÉCHELLE INCONNUE — le commerce est tenu sur un protocole qui existe, pas sur un marché qui existe |

## Ce que l'humain fait encore, et qu'aucune capacité ne lui retire

Trois vérifications d'identité (plateforme d'achat d'USDC, société, compte
d'entreprise), la formation de la société, l'ajout d'une clé de déploiement,
le dépôt du Safe et son plafond, l'ouverture d'un compte OpenRouter, la
location de la machine. Puis, chaque mois, 50 $ d'allocation. Et, si la caisse
échoue, 260 $ par an de sa poche. Rien de tout cela ne se fait à sa vitesse
plus d'une fois, sauf la caisse.

## La prochaine feuille de route commence ici

1. **La frontière du dollar, côté sortie** : un compte d'entreprise accepté, ou une pièce qui n'existe pas encore — un prestataire qui paie les frais d'une société en USDC.
2. **L'échelle du commerce** : une mesure qui dise si un serveur x402 vend à quelqu'un ; sans elle, « commerce » est une capacité tenue et un revenu non établi.
3. **La responsabilité** : la société répond, mais l'arbitre n'a pas eu à juger d'un service mal rendu ; c'est la capacité suivante après la caisse.

## Ce que la partie a appris au greffe

- Un verrou posé **sur une clef** ne retire pas l'état servi de `constatables` (c-depense listé au tour 13 sous v-reste). L'arbitre a attendu ; le greffe proposait.
- Une ligne `tour` (n° 46) est entrée sans commande de l'arbitre entre les tours 4 et 5, sans dommage.
- Le contrôle gradué a fonctionné comme prévu : le second coup du chantier est signalé à chaque tour, jamais refusé.
