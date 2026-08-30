// criticite.js — LES CHIFFRES QUI NE SONT PAS DANS LE VOLUME.
//
// Trois colonnes par-dessus les registres d'adresse, un poids par cahier
// d'affaire, et un volume entier qui n'est écrit nulle part : « Les pas ». Tout
// vient de la route `/criticite`, tout est refait à l'ouverture, et rien n'est
// jamais gardé sur disque. Le volume qu'on copie, qu'on imprime, qu'on emporte,
// reste celui qui est écrit — c'est la lecture qui est augmentée, pas le livre.
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksCriticite = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {

    // ─────────────────────────────────────────── la criticité, par-dessus
    //
    // TROIS COLONNES QUI NE SONT PAS DANS LE VOLUME, et qui ne doivent pas y être.
    // `couverture.py` régénère les registres à quatre colonnes pour qu'ils ne
    // portent rien de volatil ; un score bouge à chaque action cochée. Il se
    // calcule donc à la demande (`/criticite`) et l'écran l'AJOUTE au tableau, par
    // numéro. Le volume qu'on copie, qu'on imprime, qu'on emporte, reste celui
    // qui est écrit — c'est la lecture qui est augmentée, pas le livre.
    //
    //   perte    ce que le plan perd si ce pas rate — zéro = quelqu'un d'autre peut
    //   portée   la masse d'états cibles servie en aval
    //   attendu  ce qui, dans un AUTRE cahier, se casse la figure sans ce pas
    //
    // On ne les pose que sur les tableaux D'ADRESSE (première colonne « N° ») et
    // seulement si la ligne a un score : une colonne de tirets sur trente lignes
    // n'apprend rien et double la largeur.
    const COLS_CRIT = ["📉 Perte", "📡 Portée", "⏳ Attendu"];
    const COLS_BUT = ["⚖️ Poids", "🎯 Atteint ?"];
    // CES COLONNES NE SONT PAS DANS LE VOLUME, donc personne ne peut deviner ce
    // qu'elles veulent dire en lisant autour. L'aide se pose sur l'en-tête, là où
    // le doigt est déjà quand la question se pose — trente lignes plus bas, une
    // note en tête de page n'est plus lue.
    const AIDE = {
      "📉 Perte": "Combien d'états cibles deviennent inatteignables sans cette pièce."
        + " On la retire, on recalcule, on fait la différence. Pour une action ou une"
        + " clef : si ce pas rate. Pour un VERROU : tant qu'il tient, c'est-à-dire ce"
        + " que cet empêchement coûte au plan. Zéro ne veut pas dire sans importance :"
        + " il veut dire qu'un autre chemin existe."
        + " 🔁 = pris dans un cercle de dépendances, rien ne part.",
      "📡 Portée": "Les états cibles atteignables servis en aval, doublures comprises."
        + " L'écart avec la perte est la redondance : portée haute et perte nulle,"
        + " quelqu'un d'autre peut le faire ; portée nulle, ce pas ne mène nulle part.",
      "⏳ Attendu": "Ce qui, dans un AUTRE cahier, se casse la figure sans ce pas."
        + " Un homme à prévenir, pas un travail à sécuriser.",
      "⚖️ Poids": "Ce que vaut cet état cible. Le seul nombre saisi à la main de tout"
        + " le calcul (etat/poids-etats.json) ; sans le fichier, tout vaut 1.",
      "🎯 Atteint ?": "✅ une chaîne écrite mène jusqu'à lui. 🚫 aucune — le plan le"
        + " poursuit sans avoir écrit par où.",
    };
    const HORS = " — calculé à l'ouverture, pas écrit au registre.";
    function chargerCriticite() {
      if (S.critDemande) return;
      S.critDemande = true;
      fetch("/criticite").then((r) => r.json()).then((d) => {
        S.crit = (d && d.pas) ? d : null;
        if (S.crit) A.dessiner();
      }).catch(() => { S.critDemande = false; });
    }

    // Ce qu'un cahier pèse, et de combien ça a bougé depuis hier. Sert la liste
    // d'affaires ; `null` tant que le calcul n'est pas rentré, et la colonne
    // n'existe alors pas du tout — une colonne de tirets n'apprend rien.
    function poidsDe(b) {
      if (!S.crit || !S.crit.affaires) return null;
      const t = String(b.titre == null ? "" : b.titre).replace(/\*\*/g, "").trim();
      return S.crit.affaires[t] || null;
    }

    // ─────────────────────────────────────────── « Les pas », volume calculé
    //
    // UN ONGLET, PAS UNE PAGE À PART. La page `/pas` existe et sert la régie ;
    // mais la question qu'elle pose — par quoi commencer — se pose LE NEZ DANS
    // LES REGISTRES, pas dans un autre écran qu'il faut penser à ouvrir. Un lien
    // qu'on ne voit pas depuis l'endroit où l'on travaille n'est pas un lien.
    //
    // C'EST UN VOLUME SYNTHÉTIQUE, comme « Vos notes » : il n'est écrit par
    // personne dans la fiction, son emblème le dit, et il ne se range dans aucun
    // coffret. Le reste vient gratuitement — les onglets, le tri des colonnes, la
    // teinte des chiffres, les renvois cliquables vers la pièce citée : ce sont
    // les mêmes tables que partout, et l'on n'a pas eu à réécrire une grille.
    //
    // IL SE REFAIT À CHAQUE DESSIN, ET C'EST VOULU : il n'a pas d'existence sur
    // disque, donc rien à périmer. Sans criticité chargée, il n'existe pas du
    // tout — mieux vaut pas d'onglet qu'un onglet vide.
    const PAS = "les-pas";

    // La borne du brouillard vit dans `portee.js` (`affairesVues`) : ce volume
    // ne montre que les affaires que ce siège peut ouvrir, et les deux écrans
    // qui s'en servent la prennent de la même main.
    function volumePas() {
      if (!S.crit || !S.crit.pas) return null;
      const vues = A.affairesVues();
      const ici = (a) => !a || vues.has(a);
      const par = (a, b) => (b.perte + b.attendu) - (a.perte + a.attendu);
      const gs = { etat: "🎯", verrou: "🔒", clef: "🗝️", action: "⚔️" };
      const lignes = Object.keys(S.crit.pas).map((n) => Object.assign({ n }, S.crit.pas[n]))
        .filter((p) => (p.perte > 0 || p.attendu > 0 || p.cercle != null) && ici(p.affaire))
        .sort(par)
        .map((p) => ({ cellules: [
          (gs[p.genre] || "") + " " + p.n, p.nom, p.affaire, p.etat || "—",
          p.cercle != null ? "🔁" : String(p.perte || "—"),
          String(p.portee || "—"), String(p.attendu || "—")] }));
      const idees = (S.crit.idees || []).filter((i) => i.score > 0 && ici(i.affaire)).map((i) => ({
        cellules: [String(i.score), i.piece ? ((gs[i.genre] || "") + " " + i.piece) : "—",
          i.texte, i.affaire] }));
      const cercles = (S.crit.cercles || [])
        .filter((g) => g.pieces.some((m) => ici(m.affaire)))
        .map((g) => ({ cellules: [
        String(g.taille),
        g.pieces.map((m) => (gs[m.genre] || "") + " " + m.n).join(" → "),
        g.pieces.map((m) => m.nom).join(" · ")] }));
      const buts = Object.keys(S.crit.etats || {}).map((n) => Object.assign({ n }, S.crit.etats[n]))
        .filter((e) => ici(e.affaire))
        .sort((a, b) => (a.atteignable - b.atteignable) || a.n.localeCompare(b.n))
        .map((e) => ({ cellules: ["🎯 " + e.n, e.nom, e.affaire,
          String(e.poids), e.atteignable ? "✅" : "🚫"] }));
      const tables = [];
      if (idees.length) tables.push({
        titre: "💡 CE QU'IL FAUDRAIT ÉCRIRE — rangé par ce que ça ouvrirait",
        colonnes: ["⚖️ Ouvre", "🔢 La pièce", "💡 L'idée", "🏰 Affaire"], lignes: idees });
      if (lignes.length) tables.push({
        titre: "🔺 LES GOULOTS — ce que le plan perd si ce pas rate",
        colonnes: ["🔢 N°", "🏷️ Le pas", "🏰 Affaire", "⏳ Où ça en est",
                   "📉 Perte", "📡 Portée", "⏳ Attendu"], lignes: lignes });
      if (cercles.length) tables.push({
        titre: "🔁 LES CERCLES — des chaînes qui se mordent la queue",
        colonnes: ["🔢 Pièces", "⛓️ La chaîne", "🏷️ Ce qu'elles disent"], lignes: cercles });
      if (buts.length) tables.push({
        titre: "🎯 LES ÉTATS CIBLES — poids, et atteignables ou non",
        colonnes: ["🎯 N°", "🏷️ L'état", "🏰 Affaire", "⚖️ Poids", "🎯 Atteint ?"],
        lignes: buts });
      if (!tables.length) return null;
      return { id: PAS, calcule: true, titre: "Les pas", embleme: "⚖️",
               couleur: "var(--book-carnet)",
               sous_titre: "Calculé à l'ouverture, écrit nulle part — "
                 + lignes.length + " pas, "
                 + idees.length + " idées, "
                 + cercles.length + " cercle" + (cercles.length > 1 ? "s" : ""),
               tables: tables };
  }

    return { COLS_CRIT, COLS_BUT, AIDE, HORS, PAS, chargerCriticite, poidsDe,
             volumePas };
  }

  return { creer };
});
