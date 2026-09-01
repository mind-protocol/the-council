import json
import os
import io
import uuid
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PENSEES = os.path.join(RACINE, "etat", "pensees.json")
ECLOSIONS_CONNUES = os.path.join(RACINE, "etat", "activations", "eclosions_connues.json")
MAISON = os.path.join(RACINE, "etat", "maisons", "maison-serenissima", "documents", "books")

def charger_json(chemin, defaut=None):
    if not os.path.exists(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)

def sauvegarder_json(chemin, donnees):
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=2, ensure_ascii=False)

def evaluer_masse_critique(pensees):
    clusters = {}
    for p in pensees:
        sujet = p.get("affaire")
        if not sujet: continue
        if sujet not in clusters:
            clusters[sujet] = []
        clusters[sujet].append(p)
    
    matures = []
    for sujet, cluster in clusters.items():
        acteurs = set(p.get("qui") for p in cluster)
        # Seuil d'éclosion : 5 pensées minimum impliquant au moins 2 acteurs différents
        if len(cluster) >= 5 and len(acteurs) >= 2:
            matures.append((sujet, cluster))
    return matures

def appeler_llm(sujet, cluster):
    prompt_file = os.path.join(RACINE, "scripts", "agents", "prompts", "concepteur.md")
    
    if RACINE not in sys.path:
        sys.path.insert(0, os.path.join(RACINE, "scripts"))
    from agents.expose import runtime
    
    with io.open(prompt_file, encoding="utf-8") as f:
        manuel = f.read()
    
    lignes = [f"- Pensée de {p['qui']}: {p['texte']}" for p in cluster]
    message = f"SUJET DE FRICTION : {sujet}\n\n" + "\n".join(lignes)
    
    print(f"Appel LLM pour le sujet : '{sujet}'...")
    resultat = runtime.appeler(
        role="concepteur", 
        manuel=manuel, 
        message=message, 
        session_id=uuid.uuid4().hex,
        modele=None, 
        reprendre=False, 
        cwd=RACINE
    )
    return resultat

def main():
    print("Démarrage de l'évaluation de l'Éclosion...")
    data = charger_json(PENSEES, {"pensees": []})
    eclosions = charger_json(ECLOSIONS_CONNUES, [])
    
    matures = evaluer_masse_critique(data.get("pensees", []))
    
    eclosion_count = 0
    for sujet, cluster in matures:
        if sujet in eclosions:
            continue # Déjà traité
            
        print(f"[*] Masse critique atteinte pour : '{sujet}' ({len(cluster)} pensées par {len(set(p['qui'] for p in cluster))} acteurs)")
        try:
            reponse = appeler_llm(sujet, cluster)
            if reponse and reponse.get("message"):
                texte = reponse["message"]
                if texte.startswith("```json"):
                    texte = texte[7:]
                if texte.endswith("```"):
                    texte = texte[:-3]
                texte = texte.strip()
                
                affaire_json = json.loads(texte)
                nom_fichier = affaire_json.get("id", f"affaire-autogen-{uuid.uuid4().hex[:6]}")
                if not nom_fichier.endswith(".json"):
                    nom_fichier += ".json"
                chemin = os.path.join(MAISON, nom_fichier)
                
                sauvegarder_json(chemin, affaire_json)
                print(f"[+] Affaire créée avec succès : {chemin}")
                
                eclosions.append(sujet)
                sauvegarder_json(ECLOSIONS_CONNUES, eclosions)
                
                # On relance le tissage pour intégrer l'affaire au graphe causal
                subprocess.run([sys.executable, os.path.join(RACINE, "scripts", "tisser.py"), "--ecrire"], cwd=RACINE)
                eclosion_count += 1
        except Exception as e:
            print(f"[-] Erreur lors de l'éclosion pour '{sujet}' : {e}")

    if eclosion_count == 0:
        print("Aucune nouvelle éclosion.")

if __name__ == "__main__":
    main()
