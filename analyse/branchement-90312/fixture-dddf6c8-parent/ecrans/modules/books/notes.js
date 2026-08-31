// notes.js — LE CARNET DU JOUEUR, hors du monde.
//
// Le seul volume de l'étagère qui ne soit pas un objet de la fiction : personne
// ne l'écrit dans la salle, aucun PNJ ne le lit, le MJ n'y touche pas. Il ne
// vient pas de `etat/books.json` et n'y retourne pas — le serveur le garde tel
// quel, un fichier de texte par siège (`/notes`).
//
// DÉPLACEMENT, PAS RÉÉCRITURE : pas une ligne de logique n'a changé.
"use strict";

(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (racine) racine.BooksNotes = api;
})(typeof window !== "undefined" ? window : globalThis, function () {

  function creer(S, A) {
    const { teinte } = A.lecture;

    // ---- Les notes : le carnet du JOUEUR, hors du monde ---------------------
    // Un volume de plus sur l'étagère, et le seul qui ne soit pas un objet de la
    // fiction : personne ne l'écrit dans la salle, aucun PNJ ne le lit, le MJ
    // n'y touche pas. Le joueur y met ce qu'il veut, tel quel, et ça reste. Il
    // est toujours à portée — on ne pose pas ses propres notes sur une table, et
    // l'on n'a pas à traverser le château pour noter un nom.
    const NOTES = "vos-notes";
    // Son emblème est une main, et pas une plume : ce volume-ci n'est écrit par
    // personne dans la fiction. C'est le seul de l'étagère dont le signe dise
    // « hors du monde ».
    const NOTE = { id: NOTES, notes: true, titre: "Vos notes", embleme: "✋",
                   couleur: "var(--book-carnet)" };

    function direEtat(m) {
      S.notesEtat = m;
      const el = document.getElementById("book-notes-etat");
      if (el) el.textContent = m;
    }

    function enregistrer() {
      clearTimeout(S.notesMinuteur);
      if (S.notesEcrit === null || S.notes === S.notesEcrit) return;
      const envoi = S.notes;
      fetch("/notes", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texte: envoi }),
      }).then((r) => {
        if (!r.ok) throw new Error("refus");
        S.notesEcrit = envoi;
        if (S.notes === envoi) direEtat("Gardé.");
      }).catch(() => direEtat("Pas gardé — le serveur n'a pas répondu."));
    }

    // On n'écrit pas à chaque touche : on attend que la main s'arrête.
    function planifier() {
      direEtat("…");
      clearTimeout(S.notesMinuteur);
      S.notesMinuteur = setTimeout(enregistrer, 700);
    }

    function chargerNotes() {
      fetch("/notes").then((r) => r.json()).then((d) => {
        // Une relecture ne doit pas manger une phrase en train d'être tapée :
        // ce qui n'est pas encore parti au serveur reste ce qui fait foi.
        if (S.notesEcrit !== null && S.notes !== S.notesEcrit) return;
        S.notes = (d && typeof d.texte === "string") ? d.texte : "";
        S.notesEcrit = S.notes;
        const z = document.getElementById("book-notes-zone");
        if (z && z !== document.activeElement) z.value = S.notes;
      }).catch(() => { if (S.notesEcrit === null) S.notesEcrit = ""; });
    }

    function carteNotes() {
      const art = document.createElement("article");
      art.className = "book book-notes";
      art.style.setProperty("--book-teinte", teinte(NOTE));

      const t = document.createElement("h3");
      t.textContent = NOTE.titre;
      const et = document.createElement("span");
      et.className = "book-genre";
      et.textContent = "De votre main";
      t.appendChild(et);
      art.appendChild(A.tete(NOTE, t));

      const s = document.createElement("div");
      s.className = "book-sous-titre";
      s.textContent = "Hors du monde : nul ne le lit, et rien de ce qui s'y écrit n'a lieu.";
      art.appendChild(s);

      const zone = document.createElement("textarea");
      zone.id = "book-notes-zone";
      zone.className = "book-notes-zone";
      zone.spellcheck = false;
      zone.placeholder = "Ce que vous voulez garder — un nom, un chiffre, une rancune.";
      zone.value = S.notes;
      zone.addEventListener("input", () => { S.notes = zone.value; planifier(); });
      zone.addEventListener("blur", enregistrer);
      art.appendChild(zone);

      const etat = document.createElement("div");
      etat.id = "book-notes-etat";
      etat.className = "book-notes-etat";
      etat.textContent = S.notesEtat;
      art.appendChild(etat);
      return art;
    }

    // Une page qu'on ferme sur une phrase à moitié tapée : le minuteur n'aura
    // pas le temps de tomber, et une requête ordinaire serait coupée en vol. Le
    // beacon part quand même.
    function veiller() {
      window.addEventListener("pagehide", () => {
        if (S.notesEcrit === null || S.notes === S.notesEcrit) return;
        try {
          navigator.sendBeacon("/notes", new Blob(
            [JSON.stringify({ texte: S.notes })], { type: "application/json" }));
        } catch (e) {}
      });
    }

    return { NOTES, NOTE, direEtat, enregistrer, planifier, chargerNotes,
             carteNotes, veiller };
  }

  return { creer };
});
