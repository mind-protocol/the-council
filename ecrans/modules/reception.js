(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const form = $("reception-form");
  let epreuve = null;
  let dernierePiece = null;

  // Un ouvrage peut conduire son lecteur jusqu'ici sans lui faire recopier
  // l'objet et l'adresse. L'épreuve reste obligatoire : préremplir n'est pas
  // recevoir.
  const parametres = new URLSearchParams(window.location.search);
  if (parametres.has("objet")) $("objet").value = parametres.get("objet");
  if (parametres.has("adresse")) $("adresse").value = parametres.get("adresse");
  if (parametres.has("producteur")) $("producteur").value = parametres.get("producteur");
  if (parametres.has("provenance")) $("provenance").value = parametres.get("provenance");
  if (parametres.has("critere")) $("critere").value = parametres.get("critere");

  function adresseAbsolue(valeur) {
    return new URL(valeur.trim(), window.location.href).href;
  }

  function afficherEpreuve(classe, texte) {
    const sortie = $("preuve-adresse");
    sortie.className = "preuve " + classe;
    sortie.textContent = texte;
  }

  $("adresse").addEventListener("input", () => {
    epreuve = null;
    afficherEpreuve("neutre", "Adresse modifiée : nouvelle épreuve requise.");
  });

  $("eprouver").addEventListener("click", async () => {
    const brut = $("adresse").value;
    if (!brut.trim()) return afficherEpreuve("ko", "Adresse absente.");
    const adresse = adresseAbsolue(brut);
    afficherEpreuve("neutre", "Épreuve en cours…");
    try {
      const reponse = await fetch(adresse, { method: "GET", cache: "no-store" });
      epreuve = {
        adresse,
        accessible: reponse.ok,
        statut_http: reponse.status,
        observe_a: new Date().toISOString(),
      };
      afficherEpreuve(reponse.ok ? "ok" : "ko",
        `${reponse.ok ? "Accessible" : "Refusée"} depuis ce lecteur — HTTP ${reponse.status}.`);
    } catch (erreur) {
      epreuve = {
        adresse,
        accessible: false,
        statut_http: null,
        observe_a: new Date().toISOString(),
        erreur: String(erreur.message || erreur),
      };
      afficherEpreuve("ko", "Échec depuis ce lecteur — " + epreuve.erreur + ".");
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const reserve = $("reserve").value.trim();
    const adresse = adresseAbsolue($("adresse").value);
    const adresseEprouvee = epreuve && epreuve.adresse === adresse;
    const etatResultat = $("resultat-sous-jacent").value;
    const gesteFait = Boolean(adresseEprouvee);
    const recu = gesteFait && etatResultat === "CONFORME";
    let decision = "NON REÇU — GESTE NON PROUVÉ";
    if (gesteFait && etatResultat === "NON ÉTABLI") {
      decision = "NON REÇU — RÉSULTAT NON ÉTABLI";
    } else if (gesteFait && etatResultat === "NON CONFORME") {
      decision = "NON REÇU — RÉSULTAT NON CONFORME";
    } else if (recu) {
      decision = "REÇU AVEC RÉSERVE EXPLICITE";
    }
    const origine = {};
    const producteur = $("producteur").value.trim();
    const provenance = $("provenance").value.trim();
    if (producteur) origine.producteur = producteur;
    if (provenance) origine.provenance = provenance;
    dernierePiece = {
      type: "bordereau-reception/2",
      objet: $("objet").value.trim(),
      date_constat: $("date").value.trim(),
      origine_ouvrage: origine,
      preuve_geste: {
        etat: gesteFait ? "FAIT" : "NON FAIT",
        epreuve_adresse: adresseEprouvee ? epreuve :
          { adresse, accessible: false, motif: "non éprouvée" },
      },
      resultat_sous_jacent: {
        etat: etatResultat,
        critere: $("critere").value.trim(),
        observation: $("observation").value.trim(),
        reserve,
      },
      decision,
    };
    $("piece").textContent = JSON.stringify(dernierePiece, null, 2);
    $("decision").textContent = dernierePiece.decision;
    $("decision").className = recu ? "ok" : "ko";
    $("resultat").hidden = false;
    $("depot-etat").textContent =
      "Pièce non déposée. Le dépôt ne modifiera pas votre jugement.";
    $("resultat").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  $("copier").addEventListener("click", async () => {
    if (!dernierePiece) return;
    await navigator.clipboard.writeText(JSON.stringify(dernierePiece, null, 2));
    $("copie-etat").textContent = "Pièce copiée.";
  });

  $("telecharger").addEventListener("click", () => {
    if (!dernierePiece) return;
    const blob = new Blob([JSON.stringify(dernierePiece, null, 2) + "\n"], { type: "application/json" });
    const lien = document.createElement("a");
    lien.href = URL.createObjectURL(blob);
    lien.download = "bordereau-reception.json";
    lien.click();
    URL.revokeObjectURL(lien.href);
  });

  $("deposer").addEventListener("click", async () => {
    if (!dernierePiece) return;
    const sortie = $("depot-etat");
    sortie.textContent = "Dépôt en cours…";
    try {
      const reponse = await fetch("/reception/depot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dernierePiece),
      });
      const rendu = await reponse.json();
      if (!reponse.ok || !rendu.lien) throw new Error(rendu.erreur || `HTTP ${reponse.status}`);
      const adresse = new URL(rendu.lien, window.location.href).href;
      dernierePiece.preuve_durable = adresse;
      $("piece").textContent = JSON.stringify(dernierePiece, null, 2);
      sortie.textContent = "";
      const lien = document.createElement("a");
      lien.href = adresse;
      lien.textContent = "Preuve durable — " + rendu.id;
      sortie.appendChild(lien);
    } catch (erreur) {
      sortie.textContent = "Dépôt refusé — " + String(erreur.message || erreur) + ".";
    }
  });
})();
