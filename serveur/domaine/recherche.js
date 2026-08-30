
// ---- les dossiers de recherche, servis en lecture ------------------------
// L'onglet « Les dossiers » de `/bataille` donne à LIRE ce sur quoi le modèle
// est fondé — pas seulement la bibliographie : le raisonnement, les tableaux,
// les réserves, et la section finale qui confronte le dossier au code.
//
// ON NE RECOPIE RIEN ET ON NE RÉÉCRIT RIEN : le markdown part tel quel, et
// c'est la page qui le rend. Un dossier corrigé est à jour au rechargement
// suivant, et il n'existe nulle part de seconde version à tenir — c'est
// exactement le défaut qu'on paie ailleurs (la huitième liste de la chaîne,
// cf. l'en-tête de `sac.js`).
//
// Les deux comptes du rail ne disent pas la même chose : `references` est ce
// qui est cité, `liens` ce qu'on peut aller lire tout de suite. Un dossier de
// livres imprimés a beaucoup des premières et peu des seconds, et l'écart est
// une information sur sa nature.

const fs = require("fs");
const path = require("path");
const { RACINE } = require("../contexte");

function dossiersRecherche() {
  const dossier = path.join(RACINE, "docs", "recherche");
  let noms;
  try {
    noms = fs.readdirSync(dossier).filter((f) => f.endsWith(".md")).sort();
  } catch (e) { return []; }

  return noms.map((nom) => {
    const texte = fs.readFileSync(path.join(dossier, nom), "utf-8");
    const lignes = texte.split(/\r?\n/);
    const titre = (lignes.find((l) => l.startsWith("# ")) || "# " + nom).slice(2).trim();

    let sections = 0, references = 0, liens = 0, dansSources = false;
    for (const l of lignes) {
      if (l.startsWith("## ")) {
        sections++;
        dansSources = /^##\s+Sources\b/.test(l);
        continue;
      }
      if (!dansSources) continue;
      if (l.trim().startsWith("- ")) references++;
      liens += (l.match(/\]\(https?:\/\//g) || []).length;
    }

    return { fichier: nom, titre, texte,
             compte: { sections, references, liens, signes: texte.length } };
  });
}

module.exports = { dossiersRecherche };
