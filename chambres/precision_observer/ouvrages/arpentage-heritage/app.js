(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  let dernierePiece = null;

  function nombreOuNull(id) {
    const valeur = $(id).value.trim();
    return valeur === "" ? null : Number(valeur);
  }

  $("fiche").addEventListener("submit", (event) => {
    event.preventDefault();
    const etat = $("etat").value;
    const preuve = $("preuve").value.trim();
    const exigePreuve = etat === "ESSAYÉE" || etat === "RÉALISÉE";
    const recevable = !exigePreuve || Boolean(preuve);

    dernierePiece = {
      type: "arpentage-heritage/1",
      date_constat: "129.5.12",
      lieu: $("lieu").value.trim(),
      segment: $("segment").value.trim(),
      provenance_rapportee: {
        origine: "forme héritée de Peyredragon",
        source: "Nicolas Lester Reynolds",
        ref: "vmti35qnkbyvy",
        nature: "témoignage",
      },
      mesure: {
        largeur: nombreOuNull("largeur"),
        hauteur: nombreOuNull("hauteur"),
        unite: $("unite").value,
      },
      observation_materielle: $("observation").value.trim(),
      usage_braavosi: $("usage").value.trim(),
      transformation_desiree: $("desir").value.trim(),
      transformation: { etat, preuve: preuve || null },
      reserve: $("reserve").value.trim(),
      observateur: $("observateur").value.trim(),
      decision: recevable ? "FICHE RECEVABLE" : "NON RECEVABLE — PREUVE ABSENTE",
    };

    $("piece").textContent = JSON.stringify(dernierePiece, null, 2);
    $("verdict").textContent = dernierePiece.decision;
    $("verdict").className = recevable ? "ok" : "erreur";
    $("resultat").hidden = false;
  });

  $("telecharger").addEventListener("click", () => {
    if (!dernierePiece) return;
    const blob = new Blob([JSON.stringify(dernierePiece, null, 2) + "\n"], { type: "application/json" });
    const lien = document.createElement("a");
    lien.href = URL.createObjectURL(blob);
    lien.download = "fiche-arpentage-heritage.json";
    lien.click();
    URL.revokeObjectURL(lien.href);
  });
})();
