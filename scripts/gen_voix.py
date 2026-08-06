# Conçoit une voix ElevenLabs pour chaque personnage actif (Voice Design v3).
# Usage : python scripts/gen_voix.py [id ...]          (sans argument : tous les actifs)
#         python scripts/gen_voix.py --refaire <id>    (redessine trois variantes, garde la voix en place)
#         python scripts/gen_voix.py --choisir <id> <n>(adopte la variante n déjà auditionnée)
#         python scripts/gen_voix.py --essai <id>      (extraits seulement, ne crée rien)
# Sortie : voix/<id>-<n>.mp3 (extraits) + etat/voix.json.
#
# Le registre garde les TROIS variantes de chaque design avec leur poignée
# (generated_voice_id) et le seed du tirage : sans cela, une variante écoutée mais
# non retenue est perdue, et on ne peut plus l'adopter après coup.
import base64
import json
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "voix"
REGISTRE = RACINE / "etat" / "voix.json"
API = "https://api.elevenlabs.io/v1"
MODELE = "eleven_ttv_v3"

# Fiche vocale par personnage : timbre, débit, humeur — description en anglais
# (le moteur de design ne comprend bien que l'anglais), réplique d'audition en français.
VOIX = {
    # Deux voix qui n'appartiennent à personne dans la salle : celle qui raconte,
    # et celle que la reine s'entend penser.
    "narrateur": {
        "nom": "Le chroniqueur",
        "description": (
            "A plain, natural narrator: clear mid-range voice, neither deep nor gravelly, "
            "relaxed and even — someone reading a story aloud at an ordinary pace without "
            "performing it. No solemnity, no hush, no dramatic colour, no theatrical pauses. "
            "Neutral, unforced, easy to listen to for a long time. Must not sound like a "
            "character in a scene. Speaks French."
        ),
        "texte": (
            "Le vent se leva peu avant l'aube et rabattit la fumée des braseros sur la cour "
            "basse. Personne, à Peyredragon, ne dormait vraiment. Sur la table de la salle "
            "peinte, la carte était restée dépliée, deux dagues plantées aux Degrés de Pierre, "
            "et la cire du sceau avait durci dans son plat. Au-dehors, la mer montait. On "
            "attendait un cavalier de Sombreval, et l'on n'attendait rien de bon."
        ),
    },
    "pensee-joueur": {
        "nom": "Rhaenyra — voix intérieure",
        "description": (
            "The inner voice of a woman of thirty-two: her ordinary speaking voice — low, warm "
            "alto — simply plainer and more direct. Fully voiced at normal volume: NOT whispered, "
            "NOT breathy, no close-mic intimacy, no softness for its own sake. Even and matter-of-"
            "fact, a little tired, privately angry. She is thinking, not confiding. Speaks French."
        ),
        "texte": (
            "Ils me regardent tous et attendent que je saigne devant eux. Mon père est mort il "
            "y a dix jours et je l'apprends par un mestre qui tord sa chaîne. Ne pleure pas. "
            "Pas ici, pas devant Corlys, pas devant elle. Compte les nefs, compte les jours, "
            "compte les hommes qui restent. Je saurai plus tard ce que je ressens. Plus tard, "
            "quand il n'y aura plus personne dans la pièce."
        ),
    },
    "gerardys": {
        "description": (
            "An elderly man in his mid-fifties, thin and stooped: dry, reedy, slightly nasal timbre "
            "with little chest resonance. Deferential and over-articulated diction, small hesitations, "
            "a swallowed breath before bad news. Soft volume, as if afraid of being overheard in a "
            "stone corridor. Warm underneath, but perpetually anxious. Speaks French."
        ),
        "texte": (
            "Votre Grâce… le corbeau s'est posé avant l'aube. Avant l'aube, oui, et je n'ai pas voulu "
            "vous réveiller, la roukerie était glacée et vos relevailles sont récentes. La lettre porte "
            "le sceau du Grand Mestre Orwyle, et le pli n'était pas brisé, je m'en porte garant. "
            "Je préférerais que vous la lisiez vous-même, Votre Grâce. Il y est question de Port-Réal. "
            "Il y est question d'une couronne."
        ),
    },
    "robert-quince": {
        "description": (
            "A very large man in his mid-forties: thick, deep, resonant bass with a heavy breathy "
            "quality, audibly short of breath and wheezing faintly between phrases. Slow, plain, "
            "unhurried delivery with no ornament — a soldier repeating an order back word for word. "
            "Steady, loyal, faintly apologetic. Speaks French."
        ),
        "texte": (
            "Votre Grâce. Pardonnez… les marches. Je répète, pour être sûr : la garde double à la porte "
            "de mer, personne n'embarque sans mon sceau, et le sloop de Lamarck reste à quai jusqu'à "
            "votre parole. C'est bien cela. Il me faut douze hommes pour la nuit, j'en ai neuf. Je "
            "prendrai les trois autres aux cuisines, ils rechigneront, ils viendront quand même. Ce "
            "sera fait avant la marée."
        ),
    },
    "aegon-ii": {
        "description": (
            "A man of twenty-two, light baritone gone slack with wine: careless drawling delivery that "
            "turns loud and petulant without warning. Bursts of forced laughter, a sarcastic edge, a "
            "whine under the bravado. Boyish, privileged, unearned authority, easily bored. Speaks French."
        ),
        "texte": (
            "Ils me regardent tous comme si j'avais volé quelque chose. J'ai la couronne de Maegor sur "
            "la tête, messires — elle pèse, figurez-vous, on ne vous dit jamais qu'elle pèse. Alors "
            "buvons, ou parlez, mais faites l'un ou l'autre. Grand-père, tu as ta figure des mauvais "
            "jours. Ma mère aussi. Très bien. Qu'on m'explique une fois de plus pourquoi ma sœur "
            "devrait me faire peur."
        ),
    },
    "alicent": {
        "description": (
            "A woman of forty-one: cool, controlled mezzo, precise and courteous, held very tightly. "
            "A brittle tension beneath the calm that hardens into contempt. Measured pace, clipped "
            "consonants, quiet but carrying. Devout, exhausted, rancorous. Speaks French."
        ),
        "texte": (
            "Je ne discuterai pas de cela dans ce couloir. Non. Vous direz au Grand Mestre que la reine "
            "douairière le recevra après l'office, et pas avant. Mon fils est le roi couronné, oint, "
            "acclamé — cela n'est pas une opinion que l'on soupèse entre deux portes. Quant à elle… "
            "que l'on cesse de me demander ce que je ressens. Les Sept savent ce que j'ai fait, et "
            "pourquoi je l'ai fait."
        ),
    },
    "otto": {
        "description": (
            "A dry, cold man in his fifties: level baritone, never raised, every phrase weighed and "
            "properly finished. Deliberate pacing, precise consonants, faint condescension — the voice "
            "of a lawyer reading a contract clause aloud. No warmth, no haste. Speaks French."
        ),
        "texte": (
            "Reprenons dans l'ordre. Rosby et Stokeworth ont prêté serment : cela nous donne la route "
            "du nord et le grain. Sombreval se tait, et son silence coûte plus cher chaque jour. "
            "Peyredragon a des dragons, nous avons la ville, le trésor et l'onction du Père. L'un se "
            "compte, l'autre s'achète, le troisième ne s'obtient pas deux fois. Nous n'avons donc "
            "aucune raison de nous presser, et toutes les raisons de ne rien concéder."
        ),
    },
    "criston": {
        "description": (
            "A man of forty-seven: hard, resonant baritone with military crispness and a slight rough "
            "edge. Sermonizing cadence, clipped and righteous, quick to heat into anger. Chest-forward, "
            "no self-doubt. Speaks French."
        ),
        "texte": (
            "Il n'y a pas de demi-serment, messires. On jure, ou l'on trahit. J'ai vu ce que devient "
            "une cour qui s'arrange avec l'honneur : elle pourrit de l'intérieur, et ce sont les "
            "hommes d'armes qui paient la note. Donnez-moi les ordres, Votre Grâce, et je les "
            "exécuterai jusqu'au bout. Ceux qui trouvent cela dur n'ont qu'à rendre leur manteau."
        ),
    },
    "aemond": {
        "description": (
            "A young man of nineteen: cool light baritone, unusually controlled for his age. Precise, "
            "almost sibilant diction, slow and quiet, each word placed like a blade. Very little "
            "emotion on the surface, cold contempt beneath. Speaks French."
        ),
        "texte": (
            "Non. Écoutez-moi jusqu'au bout, mon frère. Vous parlez de patience comme d'une vertu, "
            "alors que ce n'est qu'un mot pour l'attente. Vhagar est vieille, plus grande que tout ce "
            "qu'ils possèdent, et elle m'obéit. Chaque jour que nous laissons passer, ils comptent "
            "leurs voiles et rallient un lord de plus. Je me souviens très bien de ce qu'on me doit. "
            "Je tiens le compte."
        ),
    },
    "larys": {
        "description": (
            "A man in his mid-thirties speaking barely above a whisper: soft, smooth, breathy tenor, "
            "unhurried and courteous, with a faint amused lilt at the end of phrases. Intimate, "
            "close-in quality, unsettlingly gentle, never hurried by anyone. Speaks French."
        ),
        "texte": (
            "Votre Grâce me pardonnera de parler si bas ; les murs de ce donjon ont des habitudes. "
            "Il y a une servante, à la buanderie, dont le frère sert aux écuries de Sombreval. Une "
            "chose sans importance. Les choses sans importance sont celles que personne ne songe à "
            "acheter, et c'est pourquoi elles se donnent presque. Non, je ne demande rien. Je préfère "
            "qu'on me doive."
        ),
    },
    "helaena": {
        "description": (
            "A young woman of twenty: soft, airy, high voice, distant and unhurried, drifting slightly "
            "off the rhythm of the conversation. Gentle and childlike, absent, as though reciting "
            "something remembered from somewhere else. Speaks French."
        ),
        "texte": (
            "Il y a un ver sous la dalle, là, près de votre pied. Ne le regardez pas, il n'aime pas "
            "cela. Mère dit que je dois répondre quand on me parle, alors je réponds : oui, j'ai bien "
            "dormi. Les enfants aussi. L'araignée avait fini sa toile pendant la nuit, tout entière, "
            "toute seule. Vous savez, quand la porte s'ouvrira, il ne faudra pas être dans l'escalier. "
            "Je peux retourner à mon fil, maintenant ?"
        ),
    },
    "orwyle": {
        "description": (
            "A plump old man of sixty-five: rounded, warm baritone, voluble and fluent, cushioning "
            "everything in courtly formula. Slightly fussy, over-eager to please, quick pace with soft "
            "edges, trailing away when contradicted. Speaks French."
        ),
        "texte": (
            "Sauf le respect que je dois à Votre Grâce — et il est immense, immense — la question a "
            "des précédents, plusieurs même, et tous instructifs. Le roi Jaehaerys, en son temps, avait "
            "coutume de dire… enfin, la Citadelle en a gardé le texte, je puis le faire porter. Il ne "
            "s'agit nullement de contredire la Main. Il s'agit, disons, de nuancer. Naturellement, je "
            "consigne tout ce qui est décidé."
        ),
    },
    "rhaenyra": {
        "description": (
            "A woman of thirty-two: low, warm alto carrying real royal authority, but weakened by "
            "recent illness — audible breath under the line. Commands come out short and dry; cold, "
            "controlled fury when contradicted. Proud, tired, dangerous. Speaks French."
        ),
        "texte": (
            "Répétez-le. Non — regardez-moi, mestre, et répétez-le avec les mots exacts de la lettre. "
            "Couronné. Devant la foule, avec la couronne de mon père et l'épée de mon père. Et personne, "
            "dans cette ville où je suis née, n'a levé la voix. Asseyez-vous, tous. Je suis debout depuis "
            "trop peu de jours pour crier, et je n'en ai pas l'intention. Nous allons compter ce que nous "
            "avons, et ensuite je dirai ce que nous ferons."
        ),
    },
    "daemon": {
        "description": (
            "A man of forty-eight: dark, smooth baritone with a mocking smile audible in it. Relaxed "
            "and slow, playful and threatening within the same breath, a rough amused edge. Never "
            "anxious, never deferential. Speaks French."
        ),
        "texte": (
            "Laissez-les prier, ils sont très occupés. Pendant qu'ils bénissent ce garçon ivre, moi je "
            "compte les coques dans le port. Vous voulez mon avis, messires ? Vous ne le voulez pas, "
            "mais je vais vous le donner quand même : une couronne, cela se reprend sur une tête, pas "
            "dans une lettre. Souriez, ser. C'était presque drôle."
        ),
    },
    "corlys": {
        "description": (
            "A man of seventy-six: deep, weathered bass, gravelled by decades of sea air but still "
            "fully commanding. Unhurried, enumerating, the voice of a captain giving orders across a "
            "deck. Dignified, patient, immovable. Speaks French."
        ),
        "texte": (
            "Avant de dire oui, on dit ce que cela coûte. Neuf nefs de guerre à Lamarck, prêtes ; "
            "trente et une en mer, entre Pierremarine et les Degrés. Il faut vingt jours pour les "
            "rappeler, davantage si les vents tournent. Un blocus tient tant qu'on le nourrit — grain, "
            "eau douce, bois de rechange. Vous aurez ma flotte, Votre Grâce. Vous l'aurez en sachant "
            "ce que vous demandez."
        ),
    },
    "rhaenys": {
        "description": (
            "A woman of fifty-five: firm, clear low alto, unsentimental, with dry ironic timing. Speaks "
            "briefly and lands hard, never needs to raise her voice. Aristocratic, weathered, entirely "
            "unimpressed. Speaks French."
        ),
        "texte": (
            "Vous parlez tous beaucoup. J'étais dans cette ville quand ils m'ont passée pour mon cousin, "
            "et personne, autour de cette table, n'a bougé un cil. Alors épargnez-moi les considérations "
            "sur le droit. Ils ont couronné le garçon, ils ont les portes et l'or. Nous avons des dragons "
            "et la mer. La question n'est pas de savoir qui a raison, c'est de savoir qui frappe le "
            "premier, et où."
        ),
    },
    "jacaerys": {
        "description": (
            "A boy of fifteen: light, clear voice right on the edge of breaking, earnest and careful, "
            "weighing every word before it leaves. Formal beyond his years, with a young man's tension "
            "and pride underneath. Speaks French."
        ),
        "texte": (
            "Mère, je peux y aller. Je ne dis pas cela pour l'honneur, je l'ai pesé. Vermax vole plus "
            "vite qu'un corbeau et personne n'arrête un dragon sur la route du Nord. Si c'est votre fils "
            "qui porte la lettre, Lord Stark comprendra ce que vaut la demande. Et… je sais ce qu'ils "
            "disent de moi. Raison de plus pour que ce soit moi qui parte."
        ),
    },
    "lucerys": {
        "description": (
            "A boy of fourteen: high, soft, unbroken voice, quiet and honest, giving short answers. "
            "Nervous, quick to apologize, but stiffening with sudden stubborn courage when his family "
            "is insulted. Speaks French."
        ),
        "texte": (
            "Oui, Mère. Je l'ai fait ce matin, comme vous l'aviez dit. Pardon — je croyais que ser Robert "
            "vous l'avait rapporté. Non, je n'ai pas peur d'Accalmie. Un peu, peut-être. Arrax est plus "
            "rapide que Vhagar, tout le monde le sait. Et si quelqu'un redit devant moi que ma mère n'est "
            "pas la reine, je ne me tairai pas, même si je dois me taire."
        ),
    },
    "mysaria": {
        "description": (
            "A woman of thirty-seven: silky, low, unhurried voice with a soft foreign lilt, every "
            "syllable placed with deliberate care. Caressing and transactional, faintly amused, never "
            "loud, always in control of the pause. Speaks French with a light exotic accent."
        ),
        "texte": (
            "Doucement, Votre Grâce. Les nouvelles n'aiment pas qu'on les bouscule. Une lavandière du "
            "Donjon Rouge a des sœurs, et ces sœurs ont des amants dans la Garde de la Ville — voilà "
            "comment j'apprends ce que les mestres n'écrivent pas. Ce que cela coûte ? Rien, aujourd'hui. "
            "Je préfère qu'on me paie plus tard. On paie toujours plus cher quand on a eu le temps "
            "d'oublier la dette."
        ),
    },
    "gunthor-darklyn": {
        "description": (
            "A man of forty-seven: taut, clipped baritone, brusque and proud, chin-up delivery. Short "
            "sentences, quick to take offense, a rasp of old grievance under the courtesy. Speaks French."
        ),
        "texte": (
            "Les Darklyn régnaient sur Sombreval quand les Targaryen n'étaient encore que des seigneurs "
            "de rocher, messire. Je ne le dis pas par vanité, je le dis parce qu'on l'oublie. Ma parole "
            "vaut acte, et je ne la donne pas deux fois. Qu'on me dise clairement à qui je jure et pour "
            "quoi, et l'affaire sera close avant la nuit. Je n'aime pas qu'on me fasse attendre dans ma "
            "propre salle."
        ),
    },
    "lord-staunton": {
        "description": (
            "A man of forty: low, tight tenor kept deliberately quiet — conspiratorial. Fast and "
            "insistent, pressing again and again for assurances; audible nerves, dry mouth, glances "
            "over the shoulder in the rhythm. Speaks French."
        ),
        "texte": (
            "Baissez la voix. Non, écoutez — je suis avec vous, je l'ai toujours été, Repos-des-Freux "
            "n'a jamais varié. Mais je veux des noms et je veux des dates. Qui tient la route de la "
            "côte ? Combien d'hommes, et sous quel commandement ? Si les Verts descendent, c'est chez "
            "moi qu'ils passeront en premier, pas chez Celtigar sur son île. Donnez-moi une garantie, "
            "Votre Grâce. Une seule."
        ),
    },
    "bartimos-celtigar": {
        "description": (
            "A man of fifty-one: hard, slightly nasal baritone, blunt and arrogant, with the cadence of "
            "a man counting coin aloud. Cutting, impatient, entirely comfortable being disliked. "
            "Speaks French."
        ),
        "texte": (
            "Parlons chiffres, puisque personne ici n'ose. Trois mille dragons d'or par lune pour tenir "
            "le détroit, et je ne compte pas les soldes. L'Île-aux-Pinces paiera sa part, elle l'a "
            "toujours payée. En échange, j'exige qu'on cesse les demi-mesures : les lords qui hésitent "
            "aujourd'hui trahiront demain. Qu'on prenne leurs fils en otage, et l'hésitation cessera. "
            "Cela ne coûte rien du tout."
        ),
    },
    "lord-bar-emmon": {
        "description": (
            "A man of twenty-nine who still sounds boyish: bright, quick, slightly reedy tenor, "
            "over-eager and enthusiastic, promising more than he owns. Volume outrunning authority, "
            "deflating fast when challenged. Speaks French."
        ),
        "texte": (
            "Votre Grâce n'a qu'à demander ! Pointe-Aiguë lèvera… quatre cents lances, sans difficulté, "
            "peut-être davantage, et deux galères — enfin, une galère prête et une seconde qu'on radoube, "
            "mais elle sera prête, je m'y engage. Mon père aurait dit la même chose, et il l'aurait dit "
            "moins bien. Vous verrez : quand on parlera de cette guerre, on parlera de nous."
        ),
    },
}


def cle_api():
    for ligne in (RACINE / ".env").read_text(encoding="utf-8").splitlines():
        if ligne.startswith("ELEVENLABS_API_KEY="):
            return ligne.split("=", 1)[1].strip()
    raise SystemExit("ELEVENLABS_API_KEY introuvable dans .env")


def poster(cle, chemin, corps):
    requete = urllib.request.Request(
        f"{API}/{chemin}",
        data=json.dumps(corps).encode("utf-8"),
        headers={"xi-api-key": cle, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        return json.load(urllib.request.urlopen(requete, timeout=300))
    except urllib.error.HTTPError as erreur:
        raise RuntimeError(f"{erreur.code} {erreur.read().decode('utf-8')[:300]}") from None


def concevoir(cle, fiche, seed):
    reponse = poster(
        cle,
        "text-to-voice/design",
        {
            "voice_description": fiche["description"],
            "text": fiche["texte"],
            "model_id": MODELE,
            "loudness": 0.5,
            "seed": seed,
        },
    )
    return reponse["previews"]


def creer(cle, nom, fiche, generated_voice_id):
    return poster(
        cle,
        "text-to-voice",
        {
            "voice_name": nom,
            "voice_description": fiche["description"],
            "generated_voice_id": generated_voice_id,
        },
    )


def lire_registre():
    return json.loads(REGISTRE.read_text(encoding="utf-8")) if REGISTRE.exists() else {}


def ecrire_registre(registre):
    REGISTRE.write_text(json.dumps(registre, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def choisir(cle, pid, n):
    """Adopte la variante n d'un design déjà auditionné."""
    registre = lire_registre()
    inscrit = registre.get(pid)
    if not inscrit:
        raise SystemExit(f"{pid} n'est pas au registre")
    variantes = inscrit.get("variantes") or []
    if not 1 <= n <= len(variantes):
        raise SystemExit(f"{pid} : variante {n} inconnue ({len(variantes)} au registre)")
    variante = variantes[n - 1]
    voix = creer(cle, inscrit["nom"], {"description": inscrit["description"]},
                 variante["generated_voice_id"])
    inscrit["voice_id"] = voix["voice_id"]
    inscrit["variante_retenue"] = n
    inscrit["extrait"] = variante["fichier"]
    ecrire_registre(registre)
    print(f"ok     {pid} : variante {n} adoptée -> {voix['voice_id']}")


def main():
    drapeaux = {"--essai", "--refaire", "--choisir"}
    args = [a for a in sys.argv[1:] if a not in drapeaux]
    essai = "--essai" in sys.argv
    refaire = "--refaire" in sys.argv
    cle = cle_api()
    SORTIE.mkdir(exist_ok=True)

    if "--choisir" in sys.argv:
        if len(args) != 2:
            raise SystemExit("usage : --choisir <id> <n>")
        return choisir(cle, args[0], int(args[1]))

    persos = json.loads((RACINE / "etat" / "personnages.json").read_text(encoding="utf-8"))
    noms = {p["id"]: p["nom"] for p in persos}
    actifs = [p["id"] for p in persos if p.get("etat") == "actif"]
    voulus = [i for i in (args or actifs) if i in VOIX]
    if args:
        for inconnu in set(args) - set(VOIX):
            print(f"IGNORE {inconnu} (pas de fiche vocale)")

    registre = lire_registre()

    for pid in voulus:
        if pid in registre and not essai and not refaire:
            print(f"saute  {pid} (déjà dans etat/voix.json)")
            continue
        fiche = VOIX[pid]
        try:
            seed = random.randint(1, 2**31 - 1)
            extraits = concevoir(cle, fiche, seed)
            variantes = []
            for n, extrait in enumerate(extraits, 1):
                chemin = SORTIE / f"{pid}-{n}.mp3"
                chemin.write_bytes(base64.b64decode(extrait["audio_base_64"]))
                variantes.append({
                    "n": n,
                    "generated_voice_id": extrait["generated_voice_id"],
                    "fichier": f"voix/{pid}-{n}.mp3",
                })
            print(f"design {pid} : {len(extraits)} variante(s), seed {seed}")
            if essai:
                continue
            nom = fiche.get("nom") or noms.get(pid, pid)
            inscrit = registre.get(pid, {})
            # --refaire ne coupe pas la voix en place : elle sert jusqu'à ce
            # qu'une variante soit adoptée (--choisir).
            if not refaire or not inscrit.get("voice_id"):
                voix = creer(cle, nom, fiche, extraits[0]["generated_voice_id"])
                inscrit["voice_id"] = voix["voice_id"]
                inscrit["variante_retenue"] = 1
                inscrit["extrait"] = f"voix/{pid}-1.mp3"
            inscrit.update({
                "nom": nom,
                "description": fiche["description"],
                "modele_design": MODELE,
                "seed": seed,
                "variantes": variantes,
            })
            registre[pid] = inscrit
            ecrire_registre(registre)
            etat = "à choisir" if refaire else inscrit["voice_id"]
            print(f"ok     {pid} -> {etat}")
        except Exception as erreur:
            print(f"ECHEC  {pid} : {erreur}")


if __name__ == "__main__":
    main()
