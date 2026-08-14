// renvois.js — un mot de la phrase qui MÈNE quelque part.
//
// POURQUOI. Un conseiller dit « les neufs », « la cinquième file », « ce que
// nous devons au Sanglier » — et le joueur devine. Il n'a aucun moyen de savoir
// que « les neufs » est une ligne d'affaire qui porte un numéro, ni d'aller la
// lire. C'est la moitié manquante de tout le registre : on l'écrit, on s'y
// réfère en scène, et rien ne relie les deux.
//
// Ce n'est PAS de l'auto-détection. C'est celui qui parle qui pose le lien,
// parce que lui seul sait de quoi il parle :
//
//     [les neufs](44022)          → une ligne d'affaire : on ouvre le volume
//                                    et la ligne se surligne
//     [le Sanglier](hallis-roon)  → un id d'entité : on pose la question au
//                                    narrateur, comme un nom cliqué dans le fil
//
// `attention.js` a déjà transformé la forme markdown en <b class="renvoi">.
// Ici on tranche ce qu'elle vaut : une cible hors de portée reste du TEXTE NU.
// Jamais de lien mort — et c'est le brouillard qui parle, pas une panne : un
// numéro dont on n'a pas le registre sous la main ne doit pas s'allumer.
"use strict";
window.Renvois = (() => {
  const ENTITE = /^[a-z][a-z0-9-]*$/;      // un id d'état : kebab-case
  const NUMERO = /^\d{4,6}$/;              // une adresse de ligne d'affaire

  // Ce qu'on sait d'une cible, ou rien. Trois registres, dans cet ordre : les
  // livres d'abord (le numéro est sans ambiguïté), le PLAN ensuite — l'adresse
  // qu'un conseiller cite est le plus souvent une pièce de l'échiquier —, les
  // gens en dernier.
  //
  // LES DEUX ÉCHELLES NE SE DISPUTENT PAS. Un numéro qui est à la fois une
  // ligne de registre et une pièce du plan fait les deux : le décor bascule sur
  // l'échiquier et la chaîne s'allume (voir `allumer` plus bas), et le clic
  // continue d'ouvrir le volume. Voir la POSITION vaut mieux que lire la ligne,
  // et la ligne reste à un geste.
  function resoudre(cible) {
    if (NUMERO.test(cible)) {
      const f = window.Books && Books.fiche && Books.fiche(cible);
      // « tracee » : un jeton l'attend sur le damier. « citee » : le cahier
      // l'écrit et sa chaîne ne remonte à rien, donc rien à allumer — on le
      // DIT, au lieu de laisser le joueur croire à une panne.
      const plan = window.Echiquier && Echiquier.sorte
        ? Echiquier.sorte(cible) : null;
      if (!f && !plan) return null;
      // LE NOM D'AUJOURD'HUI. Une pièce qui a été RENOMMÉE garde son renvoi —
      // le mot dit reste dans la réplique, parce que la pièce s'appelait bien
      // ainsi quand l'homme a parlé —, mais ce qu'on lit à côté doit être le
      // nom du jour. On ne l'écrit QUE s'il diffère de ce que la phrase dit, et
      // sans jamais renvoyer l'homme à son erreur : ce n'est pas « il disait
      // alors Donjon ouvert », c'est le nom actuel, posé simplement.
      const dujour = window.Echiquier && Echiquier.nom ? Echiquier.nom(cible) : null;
      const mot = plan === "citee"
        ? " · écrite au cahier, elle ne remonte à rien"
        : plan ? " · une pièce du plan" : "";
      if (!f) {
        // Une pièce du plan dont aucun volume ne porte la ligne : le renvoi
        // mène au PLATEAU, et il le dit par le signe de l'affaire.
        return { sorte: "piece", plan: plan, icone: "\u{1F3F0}", nom: dujour,
                 infobulle: (dujour ? dujour + " — " : "") + "n° " + cible + mot };
      }
      return { sorte: "livre", plan: plan, icone: f.icone || "📄", nom: dujour,
               infobulle: (f.titre ? f.titre + " — n° " + cible : "n° " + cible) + mot };
    }
    if (ENTITE.test(cible)) {
      const t = window.Entites && Entites.nature && Entites.nature(cible);
      if (!t) return null;
      const icones = { personnage: "👤", lieu: "📍", maison: "🛡️",
                       dragon: "🐉", salle: "🚪" };
      // Pas d'infobulle sur un nom : elle ne disait rien qu'on ne sache déjà,
      // et elle se posait par-dessus le texte à chaque passage de souris.
      return { sorte: "entite", type: t, icone: icones[t] || "•" };
    }
    return null;
  }

  // ---- ALLUMER LE PLATEAU : le joueur voit de quoi l'homme parle -----------
  // Un renvoi vers une pièce du plan ne se contente pas d'être cliquable : au
  // moment où la phrase se joue, le décor bascule sur l'échiquier et la chaîne
  // causale de la pièce s'allume — franchement, puis ça se pose. Le tout
  // recommence, sans le coup d'éclat, quand la souris repasse sur le mot.
  //
  // MAIS SEULEMENT CE QUI SE JOUE VRAIMENT. Au rechargement, la page rejoue
  // tout l'historique d'un coup ; allumer à chaque renvoi du passé ferait
  // clignoter le décor pendant une minute et mentirait sur la scène en cours.
  // `bus.js` pose la classe `entre` sur les seuls items joués en direct — c'est
  // la marque durable qui distingue le vécu du rejoué, et l'on ne s'allume que
  // sur elle.
  const enDirect = (el) => {
    if (window.Bus && Bus.enArchive && Bus.enArchive()) return false;
    // `data-montre` : `illustration.js` a déjà désigné pour cet item, parce
    // qu'il portait aussi un extrait de volume et qu'il fallait trancher le
    // décor dans le même tour. Redésigner ici ferait deux éclats pour un seul
    // énoncé.
    if (el.dataset.montre === "1") return false;
    const bloc = el.closest && el.closest(".chr");
    return !!(bloc && bloc.classList.contains("entre"));
  };

  function survoler(el) {
    if (!window.Echiquier || !Echiquier.designer) return;
    el.addEventListener("mouseenter", () => {
      clearTimeout(el._ech);
      // Un petit retard, comme sur le plateau : une souris qui traverse la
      // phrase ne doit pas faire basculer le décor au passage.
      el._ech = setTimeout(() => Echiquier.designer(el.dataset.cible,
        { franc: false }), 180);
    });
    el.addEventListener("mouseleave", () => {
      clearTimeout(el._ech);
      if (Echiquier.relacher) Echiquier.relacher();
    });
  }

  // HABILLER : le trait, l'icône, les attributs. Extrait de `traiter` parce que
  // `rafraichir` en a besoin aussi — une cible qui change de DOMICILE (du
  // registre au cahier, ou l'inverse) doit se rhabiller sur place, et non
  // rester marquée d'une sorte qui ne mène plus nulle part.
  function habiller(el, r) {
    el.dataset.vu = "1";
    el.dataset.sorte = r.sorte;
    // Le libellé est retenu AVANT qu'on y glisse l'icône : c'est lui qu'on
    // passe au narrateur, et il ne doit pas traîner un emoji derrière lui
    // (« Rappelle-moi qui est 👤le Sanglier » — vu en jeu le 12).
    el.dataset.libelle = (el.textContent || "").trim();
    if (r.type) el.dataset.type = r.type; else delete el.dataset.type;
    if (r.infobulle) el.title = r.infobulle; else el.removeAttribute("title");
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    const ic = document.createElement("span");
    ic.className = "renvoi-icone";
    ic.setAttribute("aria-hidden", "true");
    ic.textContent = r.icone;
    el.insertBefore(ic, el.firstChild);
    if (r.plan) {
      el.dataset.plan = r.plan;      // « tracee » ou « citee »
      survoler(el);
    } else {
      delete el.dataset.plan;
    }
  }

  // Habiller ce qui mène quelque part, laisser le reste en paix. On repasse
  // sur ce qui n'a pas encore été jugé (`data-vu`), jamais deux fois.
  function traiter(racine) {
    // Ce qui s'allume s'allume ENSEMBLE : deux renvois dans la même phrase
    // désignent deux pièces d'un même énoncé, et deux bascules qui se chassent
    // ne montreraient que la seconde.
    const aMontrer = [];
    (racine || document.body).querySelectorAll(".renvoi:not([data-vu])")
      .forEach((el) => {
        const cible = el.dataset.cible || "";
        const r = resoudre(cible);
        // Pas encore résolu ? On ne marque RIEN : l'étagère et l'état des gens
        // arrivent après coup, et `raviver()` repassera. Marquer ici gèlerait
        // en texte nu tout ce qui a été poussé avant le chargement.
        if (!r) return;
        habiller(el, r);
        if (r.plan && enDirect(el)) aMontrer.push(cible);
      });
    if (aMontrer.length && window.Echiquier && Echiquier.designer) {
      Echiquier.designer(aMontrer, { franc: true });
    }
  }

  // LE RATTRAPAGE, et il n'est pas cosmétique. Les registres n'arrivent pas
  // ensemble : quand l'étagère répond avant l'échiquier, un numéro qui est les
  // DEUX se fige en simple renvoi de volume — `data-vu` interdisant qu'on le
  // rejuge, il n'allumerait plus jamais le plateau de toute la session. Le
  // plan appelle donc ceci une fois, quand ses adresses arrivent, et l'on
  // repasse sur ce qui est déjà jugé mais pas encore reconnu de lui. UNE FOIS
  // et pas à chaque mutation : c'est un balayage du fil entier.
  // On dénude : le renvoi redevient exactement ce qu'il était avant qu'on le
  // juge — du texte, sans gras, sans trait, sans icône. C'est le contrat de ce
  // module, et il vaut dans les deux sens.
  function denuder(el) {
    const ic = el.querySelector(".renvoi-icone");
    if (ic) ic.remove();
    ["vu", "sorte", "plan", "type", "libelle", "montre"].forEach((k) => {
      delete el.dataset[k];
    });
    el.removeAttribute("role");
    el.removeAttribute("tabindex");
    el.removeAttribute("title");
    el.classList.remove("renvoi-perdu");
  }

  // ---- QUAND UNE PIÈCE S'ÉVAPORE ------------------------------------------
  // Les registres ne font pas que grandir : on efface une pièce de registre
  // morte, un conseiller retire un verrou de son cahier (« ce n'est pas un
  // verrou : suspension de l'action au verdict scellé »), et un renvoi qui la
  // citait dans une réplique DÉJÀ JOUÉE pointe alors dans le vide. `data-vu`
  // interdisant qu'on rejuge, il resterait allumé sur une adresse morte —
  // exactement le lien mort que ce module existe pour empêcher.
  //
  // On repasse donc dans les DEUX SENS, à chaque fois que le plan se recharge :
  // ce qui vient d'apparaître s'allume, ce qui vient de disparaître se dénude.
  // Le rejeu de l'historique n'en souffre pas : on ne touche qu'à l'habillage,
  // jamais au texte, et un renvoi dénudé est un mot comme un autre.
  function rafraichir() {
    if (!window.Echiquier || !Echiquier.sorte) return;
    document.querySelectorAll(".renvoi[data-cible]").forEach((el) => {
      const c = el.dataset.cible || "";
      if (!NUMERO.test(c)) return;
      const r = resoudre(c);
      if (!r) {
        // Plus rien ne la porte, ni volume ni plan : retour au texte nu. Elle
        // reviendra d'elle-même si le registre la réécrit — `traiter` repasse
        // sur ce qui n'a pas de `data-vu`.
        if (el.dataset.vu) denuder(el);
        return;
      }
      if (!el.dataset.vu) return;      // pas encore jugé : `traiter` s'en charge
      // ELLE A CHANGÉ DE DOMICILE. Une pièce qui DESCEND du registre au cahier
      // garde son numéro et perd sa ligne de volume : `sorte` passe de
      // « livre » à « piece », et l'inverse arrive quand un cahier remonte au
      // registre. Le lien doit TENIR — même numéro, autre maison —, mais il ne
      // tenait pas : on ne rafraîchissait que l'infobulle et le plan, si bien
      // que le clic continuait d'aller frapper à la porte d'un volume disparu
      // et se marquait « perdu ». On rhabille donc sur place. Sans allumage :
      // c'est un déménagement, pas une parole qu'on vient de prononcer.
      if (el.dataset.sorte !== r.sorte) { denuder(el); habiller(el, r); return; }
      if (r.infobulle) el.title = r.infobulle; else el.removeAttribute("title");
      if (!r.plan) { delete el.dataset.plan; return; }
      if (el.dataset.plan === r.plan) return;
      const neuf = !el.dataset.plan;
      el.dataset.plan = r.plan;
      if (neuf) survoler(el);
    });
  }

  // Les registres grandissent en cours de route : l'étagère se charge, les
  // entités arrivent du serveur, un volume change de main. Ce qui attendait en
  // texte nu s'allume alors — sans quoi un renvoi poussé trop tôt resterait
  // mort pour toute la session.
  function raviver() { traiter(document.body); }

  function suivre(el) {
    const cible = el.dataset.cible || "";
    // Une pièce du plan qu'aucun volume ne porte : le clic va au PLATEAU, et
    // il y reste — c'est le seul endroit où cette adresse existe.
    if (el.dataset.sorte === "piece") {
      if (window.Echiquier && Echiquier.designer) Echiquier.designer(cible, { franc: true });
      return;
    }
    if (el.dataset.sorte === "livre") {
      if (window.Books && Books.aller && Books.aller(cible)) return;
      // Le volume était là à l'index, il ne l'est plus : on le dit en place
      // plutôt que de laisser le joueur cliquer dans le vide.
      el.classList.add("renvoi-perdu");
      el.title = "Ce registre n'est plus à portée d'ici";
      return;
    }
    if (window.Entites && Entites.demander) {
      Entites.demander(cible, el.dataset.type || null,
        el.dataset.libelle || (el.textContent || "").trim());
    }
  }

  document.addEventListener("click", (e) => {
    const el = e.target.closest && e.target.closest(".renvoi[data-vu]");
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();
    suivre(el);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const el = e.target.closest && e.target.closest(".renvoi[data-vu]");
    if (!el) return;
    e.preventDefault();
    suivre(el);
  });

  // Le fil pousse en continu, et depuis une dizaine de modules différents.
  // Plutôt que d'aller ajouter un appel dans chacun — et d'en oublier un —, on
  // regarde ce qui se pose. Groupé, jamais à chaque nœud.
  //
  // Par un minuteur et NON par `requestAnimationFrame` : une image ne tombe que
  // si l'onglet compose. Un joueur qui laisse la partie dans un onglet de fond
  // pendant que le MJ pousse verrait ses renvois rester en texte nu.
  let attendu = null;
  new MutationObserver(() => {
    if (attendu) return;
    attendu = setTimeout(() => { attendu = null; raviver(); }, 16);
  }).observe(document.body, { childList: true, subtree: true });

  raviver();
  return { traiter, raviver, rafraichir };
})();
