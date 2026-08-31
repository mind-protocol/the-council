// demandes.js — un conseiller demande quelque chose, et on peut lui répondre
// sur place.
//
// POURQUOI. La reine a posé une règle le 27e au matin : personne ne lui apporte
// un problème sans l'une de ces trois choses — une SOLUTION, des VOIES, ou une
// DATE. Ces trois formes-là sont exactement ce qu'une interface sait rendre :
//   une solution -> Accordé / Refusé
//   des voies    -> des options numérotées, une seule tenue
//   une date     -> rien à cliquer, on prend acte
//
// Ce n'est PAS le menu de choix qu'on s'interdit partout ailleurs. La différence
// tient en une phrase : ici ce n'est pas le MJ qui propose au joueur ce qu'il
// pourrait faire, c'est un PERSONNAGE qui demande quelque chose et qui attend
// une réponse. Refuser est une réponse, ne rien cliquer aussi — le champ libre
// reste ouvert, et l'on peut toujours répondre de sa propre bouche.
//
// Le bloc se pose sur une `replique` ou un `geste` par une clef `demande` :
//   "demande": {
//     "id": "corlys-charge",              // pour ne pas rouvrir au rechargement
//     "quoi": "Écrire la charge de lord Corlys ce soir",
//     "echeance": "avant cinq heures",    // facultatif, s'affiche en pied
//     "cout": "zéro dragon",              // facultatif
//     "voies": [                          // facultatif : sans voies, c'est oui/non
//       {"id":"gunthor","texte":"La donner à lord Gunthor","detail":"zéro dragon"},
//       {"id":"deux-noms","texte":"Deux autres noms demain matin"}
//     ]
//   }
"use strict";
window.Demandes = (() => {
  // Le flux est append-only et se rejoue en entier au rechargement : sans cette
  // mémoire, une demande tranchée ce matin redemanderait une réponse ce soir.
  const CLE = "demandes-repondues";
  const lues = () => {
    try { return JSON.parse(localStorage.getItem(CLE) || "{}"); } catch (e) { return {}; }
  };
  const marquer = (id, verdict) => {
    if (!id) return;
    const m = lues(); m[id] = verdict || true;
    try { localStorage.setItem(CLE, JSON.stringify(m)); } catch (e) {}
  };

  function poser(entree, it) {
    const d = it && it.demande;
    if (!entree || !d || !d.quoi) return;
    const corps = entree.querySelector(".chr-corps") || entree;

    const bloc = document.createElement("div");
    bloc.className = "demande";

    const tete = document.createElement("div");
    tete.className = "demande-quoi";
    tete.textContent = d.quoi;
    bloc.appendChild(tete);

    const menus = [d.echeance ? "Dû " + d.echeance : "", d.cout || ""]
      .filter(Boolean).join(" · ");
    if (menus) {
      const m = document.createElement("div");
      m.className = "demande-menus";
      m.textContent = menus;
      bloc.appendChild(m);
    }

    const pied = document.createElement("div");
    pied.className = "demande-pied";
    bloc.appendChild(pied);

    // Déjà répondu dans une vie antérieure de la page : on montre le verdict et
    // on ne redemande rien.
    const deja = d.id ? lues()[d.id] : null;
    if (deja) {
      bloc.classList.add("close");
      pied.innerHTML = '<span class="demande-verdict"></span>';
      pied.querySelector(".demande-verdict").textContent =
        typeof deja === "string" ? deja : "Répondu";
      corps.appendChild(bloc);
      return;
    }

    function clore(verdict) {
      bloc.classList.add("close");
      pied.querySelectorAll("button").forEach((b) => { b.disabled = true; });
      pied.innerHTML = '<span class="demande-verdict"></span>';
      pied.querySelector(".demande-verdict").textContent = verdict;
      marquer(d.id, verdict);
      setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
    }

    function repondre(reponse, voie) {
      Bus.envoyer({
        type: "demande",
        demande_id: d.id || null,
        de: it.locuteur_id || it.acteur_id || null,
        quoi: d.quoi,
        reponse: reponse,                       // "accorde" | "refuse" | "voie"
        voie_id: voie ? (voie.id || null) : null,
        texte: voie ? voie.texte : (reponse === "accorde" ? "Accordé" : "Refusé"),
      });
    }

    // EXPLIQUER — et il ne consomme pas la demande. On demande de quoi décider,
    // pas de quoi remettre à plus tard : le bloc reste ouvert, la réponse du MJ
    // arrive hors fiction (elle ne coûte pas une minute et personne ne l'entend),
    // et l'on tranche ensuite en connaissance de cause.
    const expliquer = document.createElement("button");
    expliquer.className = "demande-expliquer";
    expliquer.textContent = "Expliquer";
    expliquer.onclick = () => {
      if (bloc.classList.contains("close") || expliquer.disabled) return;
      Bus.envoyer({
        type: "demande",
        demande_id: d.id || null,
        de: it.locuteur_id || it.acteur_id || null,
        quoi: d.quoi,
        reponse: "expliquer",
        texte: "De quoi s'agit-il, et qu'est-ce que ça engage ?",
      });
      expliquer.disabled = true;
      expliquer.textContent = "…";
      // On se contente d'attendre : la réponse tombera dans le fil.
      setTimeout(() => {
        expliquer.disabled = false;
        expliquer.textContent = "Expliquer encore";
      }, 8000);
      setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
    };

    const voies = (d.voies || []).filter((v) => v && v.texte);
    if (voies.length) {
      const liste = document.createElement("div");
      liste.className = "demande-voies";
      voies.forEach((v, i) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "demande-voie";
        b.innerHTML = '<span class="demande-num"></span>' +
          '<span class="demande-corps"><span class="demande-texte"></span>' +
          (v.detail ? '<span class="demande-detail"></span>' : "") + "</span>";
        b.querySelector(".demande-num").textContent = i + 1;
        b.querySelector(".demande-texte").textContent = v.texte;
        if (v.detail) b.querySelector(".demande-detail").textContent = v.detail;
        b.onclick = () => {
          if (bloc.classList.contains("close")) return;
          repondre("voie", v);
          clore("Retenu : " + v.texte);
        };
        liste.appendChild(b);
      });
      bloc.insertBefore(liste, pied);
      const non = document.createElement("button");
      non.className = "demande-non";
      non.textContent = "Aucune de ces voies";
      non.onclick = () => { repondre("refuse", null); clore("Aucune voie retenue"); };
      pied.appendChild(expliquer);
      pied.appendChild(non);
    } else {
      const oui = document.createElement("button");
      oui.className = "demande-oui";
      oui.textContent = d.oui || "Accordé";
      oui.onclick = () => { repondre("accorde", null); clore(d.oui || "Accordé"); };
      const non = document.createElement("button");
      non.className = "demande-non";
      non.textContent = d.non || "Refusé";
      non.onclick = () => { repondre("refuse", null); clore(d.non || "Refusé"); };
      pied.appendChild(expliquer);
      pied.appendChild(oui);
      pied.appendChild(non);
    }

    // LE CHAMP LIBRE, et il n'est pas un ornement : les boutons ne sont qu'un
    // raccourci pour les deux ou trois réponses qu'on avait prévues. La vraie
    // réponse est souvent « oui, mais », « demandez à Hask d'abord », ou une
    // condition qu'aucune option ne portait. Ce qu'on écrit ici prime sur tout.
    const libre = document.createElement("form");
    libre.className = "demande-libre";
    const champ = document.createElement("input");
    champ.type = "text";
    champ.className = "demande-champ";
    champ.placeholder = d.invite || "ou répondez-lui vous-même…";
    champ.autocomplete = "off";
    libre.appendChild(champ);
    libre.onsubmit = (e) => {
      e.preventDefault();
      const t = (champ.value || "").trim();
      if (!t || bloc.classList.contains("close")) return;
      // Une QUESTION n'est pas une réponse : « explique », « pourquoi ? »,
      // « c'est quoi ce porteur » ne doivent pas consommer la demande. On la
      // laisse ouverte et l'on attend le contexte, comme pour le bouton.
      if (/^(explique|expliquez|pourquoi|comment|c'?est quoi|de quoi|qui est|combien)/i.test(t)
          || t.endsWith("?")) {
        Bus.envoyer({ type: "demande", demande_id: d.id || null,
          de: it.locuteur_id || it.acteur_id || null, quoi: d.quoi,
          reponse: "expliquer", texte: t });
        champ.value = "";
        champ.placeholder = "on vous répond — le choix reste ouvert";
        setTimeout(() => Bus.sonderMaintenant && Bus.sonderMaintenant(), 120);
        return;
      }
      Bus.envoyer({
        type: "demande",
        demande_id: d.id || null,
        de: it.locuteur_id || it.acteur_id || null,
        quoi: d.quoi,
        reponse: "libre",
        texte: t,
      });
      clore("« " + t + " »");
    };
    bloc.appendChild(libre);

    corps.appendChild(bloc);
  }

  return { poser };
})();
