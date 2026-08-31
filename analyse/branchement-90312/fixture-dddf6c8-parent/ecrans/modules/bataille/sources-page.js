(() => {
"use strict";
const $ = (id) => document.getElementById(id);

// ═══ LES SOURCES ═══════════════════════════════════════════════════════════
// L'onglet NE RECOPIE RIEN. `/recherche` relit `docs/recherche/*.md` à chaque
// appel et rend la section « ## Sources » de chaque dossier ; ce qui s'affiche
// ici est donc ce qui est écrit là-bas, à la minute où l'on ouvre. Une source
// ajoutée au dossier apparaît sans qu'on touche à cette page — et une source
// retirée disparaît, ce qu'une copie n'aurait jamais fait.
let srcData = null, srcChoisi = 0;

const echapperSource = (s) => String(s == null ? "" : s).replace(/[&<>"]/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// L'HÔTE À CÔTÉ DU LIEN, et c'est le seul ornement qui gagne sa place :
// `cambridge.org` et `medievalchronicles.com` ne pèsent pas la même chose, et
// l'onglet existe précisément pour qu'on n'ait pas à ouvrir le lien pour le
// savoir. C'est la lecture de qualité de preuve rendue en un coup d'œil.
function hote(url) {
  try {
    return '<span class="hote">' +
      echapperSource(new URL(url).hostname.replace(/^www\./, "")) + "</span>";
  } catch (e) { return ""; }
}

function orner(md) {
  return echapperSource(md)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/\*([^*]+)\*/g, "<i>$1</i>");
}

// Les liens sont mis de côté AVANT le gras et l'italique : sans ça, une URL qui
// porte une étoile ou un souligné se fait manger par la mise en forme, et le
// lien meurt sans que rien ne le signale.
function inline(md) {
  const gardes = [];
  let t = md.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, texte, cible) => {
    let html;
    if (/^https?:\/\//.test(cible)) {
      html = '<a href="' + echapperSource(cible) + '" target="_blank" rel="noreferrer">' +
             orner(texte) + "</a>" + hote(cible);
    } else if (srcData && srcData.some((d) => d.fichier === cible)) {
      // UN RENVOI ENTRE DOSSIERS EST UN RENVOI, pas un bout de markdown a
      // regarder. Ces quatre-la se citent l'un l'autre des leur premiere ligne :
      // le clic change de dossier dans le rail, ce que la phrase promet deja.
      html = '<a class="croise" data-f="' + echapperSource(cible) + '">' + orner(texte) + "</a>";
    } else {
      // Une cible qu'on ne sert pas ici ne devient pas un lien mort : elle reste
      // du texte, et l'on voit qu'elle mene ailleurs sans cliquer dans le vide.
      html = '<span class="ailleurs">' + orner(texte) + "</span>";
    }
    gardes.push(html);
    // Le jeton est un caractere nul, pas un numero entre espaces : ces
    // dossiers sont pleins de dates et de pages, et « en 1285 » se serait
    // fait prendre pour le lien no 1285 — remplace par « undefined », en
    // silence, ce qui est la pire facon de perdre une source.
    return "\u0000" + (gardes.length - 1) + "\u0000";
  });
  return orner(t).replace(/\u0000(\d+)\u0000/g, (m, i) => gardes[+i]);
}

// Les lignes d'un bloc, recollées en paragraphes sur les vides.
function paragraphes(lignes) {
  const out = []; let cur = [];
  for (const l of lignes || []) {
    if (!l.trim()) { if (cur.length) { out.push(cur.join(" ")); cur = []; } }
    else cur.push(l.trim());
  }
  if (cur.length) out.push(cur.join(" "));
  return out;
}
const enP = (arr) => arr.map((x) => "<p>" + inline(x) + "</p>").join("");
const titreCourt = (t) => t.split(" — ")[0];

// ═══ LE RENDU DES DOSSIERS ═════════════════════════════════════════════════
// Un rendu TAILLÉ POUR CES DOSSIERS-LÀ, pas un moteur markdown général : titres,
// filets, citations, tableaux, listes, paragraphes. C'est tout ce qu'ils
// contiennent — on l'a compté avant d'écrire — et prétendre faire plus serait
// mentir sur ce que la page sait rendre.
//
// LE TABLEAU EST LA RAISON D'ÊTRE DE TOUT CECI. Ces dossiers raisonnent par
// écarts chiffrés : un homme du guet pour 200 âmes chez nous contre un pour
// 3 300 à Paris, six flèches par minute contre douze. Rendre ça en texte suivi,
// c'est perdre l'argument — et l'argument est ce qu'on vient lire.

// Ce qui ouvre un bloc, et donc ce qui INTERROMPT un paragraphe ou un item de
// liste en cours. Sans cette liste, une ligne de tableau se ferait avaler par
// le paragraphe qui la précède.
const DEBUT_BLOC = /^(#{1,6}\s|>|\||-{3,}\s*$|[-*]\s|\d+\.\s)/;

const cellules = (l) => l.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

function tableau(lignes) {
  // La ligne de séparation (`|---|---|`) est ce qui distingue un vrai en-tête
  // d'une première ligne de données. Sans elle, on ne promeut rien.
  const separateur = lignes[1] && /^[\s|:-]+$/.test(lignes[1]);
  const tete = separateur ? cellules(lignes[0]) : null;
  const corps = lignes.slice(separateur ? 2 : 0).map(cellules);
  return '<div class="tab"><table>' +
    (tete ? "<thead><tr>" + tete.map((c) => "<th>" + inline(c) + "</th>").join("") +
            "</tr></thead>" : "") +
    "<tbody>" + corps.map((r) => "<tr>" +
      r.map((c) => "<td>" + inline(c) + "</td>").join("") + "</tr>").join("") +
    "</tbody></table></div>";
}

// Le texte d'un titre sans sa mise en forme : c'est ce qui part au sommaire, où
// le gras et les liens n'ont rien à faire.
const texteNu = (md) => md.replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
                          .replace(/[*`]/g, "").trim();

function rendreMd(md) {
  const L = md.split(/\r?\n/);
  const html = [], plan = [];
  let i = 0, nAncre = 0;

  while (i < L.length) {
    const l = L[i];
    if (!l.trim()) { i++; continue; }

    const titre = l.match(/^(#{1,6})\s+(.*)$/);
    if (titre) {
      const n = titre[1].length, ancre = "sec" + (++nAncre);
      // Le sommaire s'arrête au troisième niveau : au quatrième il devient plus
      // long que ce qu'il indexe, et l'on ne s'en sert plus.
      if (n === 2 || n === 3) plan.push({ niveau: n, titre: texteNu(titre[2]), ancre });
      const h = Math.min(n + 1, 6);
      html.push("<h" + h + ' id="' + ancre + '">' + inline(titre[2]) + "</h" + h + ">");
      i++; continue;
    }

    if (/^-{3,}\s*$/.test(l.trim())) { html.push("<hr>"); i++; continue; }

    if (l.startsWith(">")) {
      const bloc = [];
      while (i < L.length && L[i].startsWith(">")) { bloc.push(L[i].replace(/^>\s?/, "")); i++; }
      const p = paragraphes(bloc);
      // Une citation qui s'ouvre sur un panneau EN EST un : ces dossiers s'en
      // servent pour dire « la version précédente de cette section était
      // fausse », et la réserve doit se voir autant que ce qu'elle corrige.
      const alerte = p.length && /^\*{0,2}⚠/.test(p[0]);
      html.push("<blockquote" + (alerte ? ' class="alerte"' : "") + ">" +
                enP(p) + "</blockquote>");
      continue;
    }

    if (l.trim().startsWith("|")) {
      const bloc = [];
      while (i < L.length && L[i].trim().startsWith("|")) { bloc.push(L[i].trim()); i++; }
      html.push(tableau(bloc));
      continue;
    }

    if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
      const ordonnee = /^\s*\d/.test(l);
      const items = [];
      while (i < L.length) {
        const p = L[i].match(/^\s*([-*]|\d+\.)\s+(.*)$/);
        if (p) { items.push([p[2]]); i++; }
        // Une ligne qui suit sans puce et sans ouvrir de bloc CONTINUE l'item :
        // ces dossiers coupent à quatre-vingt-dix signes, et empiler les
        // morceaux au lieu de les recoller donne une bouillie.
        else if (items.length && L[i].trim() && !DEBUT_BLOC.test(L[i].trim())) {
          items[items.length - 1].push(L[i].trim()); i++;
        } else break;
      }
      const t = ordonnee ? "ol" : "ul";
      html.push("<" + t + ">" +
        items.map((x) => "<li>" + inline(x.join(" ")) + "</li>").join("") + "</" + t + ">");
      continue;
    }

    const par = [];
    while (i < L.length && L[i].trim() && !DEBUT_BLOC.test(L[i].trim())) {
      par.push(L[i].trim()); i++;
    }
    // GARDE-FOU : une ligne qu'aucune branche n'a su consommer avancerait le
    // curseur de zéro et figerait l'onglet. On la saute plutôt que de boucler.
    if (!par.length) { i++; continue; }
    const t = par.join(" ");
    html.push("<p" + (/^\*\*Écart/.test(t) ? ' class="ecarte"' : "") + ">" +
              inline(t) + "</p>");
  }
  return { html: html.join("\n"), plan };
}

const nombre = (n) => n.toLocaleString("fr-FR");

function allerA(ancre) {
  const c = document.getElementById(ancre);
  if (c) c.scrollIntoView({ behavior: "smooth", block: "start" });
}

function choisir(i) {
  srcChoisi = i; rendreSources(); $("srccorps").scrollTop = 0;
}

function rendreSources() {
  if (!srcData || !srcData.length) {
    $("srcrail").innerHTML = "";
    $("srccorps").innerHTML = '<div class="dedans vide">' +
      "Aucun dossier dans <code>docs/recherche</code>.</div>";
    return;
  }
  const d = srcData[srcChoisi];
  // ON NE REND UN DOSSIER QU'UNE FOIS. Revenir dessus doit être instantané, et
  // trente mille signes de markdown n'ont pas à être relus pour un aller-retour
  // — d'autant que le sommaire du rail a besoin du rendu pour exister.
  if (!d._rendu) d._rendu = rendreMd(d.texte);

  $("srcrail").innerHTML = srcData.map((x, i) => {
    const ligne = '<div class="d' + (i === srcChoisi ? " on" : "") + '" data-i="' + i + '">' +
      '<div class="t">' + echapperSource(titreCourt(x.titre)) + "</div>" +
      '<div class="n">' + x.compte.sections + " sections · " +
        x.compte.references + " références</div></div>";
    if (i !== srcChoisi) return ligne;
    return ligne + '<nav class="plan">' + d._rendu.plan.map((p) =>
      '<a class="n' + p.niveau + '" data-a="' + p.ancre + '">' +
      echapperSource(p.titre) + "</a>").join("") + "</nav>";
  }).join("");

  for (const el of $("srcrail").querySelectorAll(".d"))
    el.onclick = () => choisir(+el.dataset.i);
  for (const a of $("srcrail").querySelectorAll(".plan a"))
    a.onclick = () => allerA(a.dataset.a);

  $("srccorps").innerHTML = '<div class="dedans">' +
    '<div class="fich">docs/recherche/' + echapperSource(d.fichier) + " · " +
      nombre(d.compte.signes) + " signes · " + d.compte.references + " références · " +
      d.compte.liens + " liens</div>" +
    d._rendu.html + "</div>";

  // Les renvois entre dossiers changent le rail au lieu de recharger quoi que
  // ce soit : on est dans un onglet, pas dans un navigateur de fichiers.
  for (const a of $("srccorps").querySelectorAll("a.croise")) {
    a.onclick = () => {
      const i = srcData.findIndex((x) => x.fichier === a.dataset.f);
      if (i >= 0) choisir(i);
    };
  }
}

function chargerSources() {
  $("srccorps").innerHTML = '<div class="dedans vide">Lecture des dossiers…</div>';
  return fetch("/recherche").then((r) => r.json()).then((j) => {
    srcData = j.dossiers || [];
    if (srcChoisi >= srcData.length) srcChoisi = 0;
    const somme = (f) => srcData.reduce((s, d) => s + f(d), 0);
    $("srccompte").textContent = srcData.length + " dossiers · " +
      nombre(somme((d) => d.compte.signes)) + " signes · " +
      somme((d) => d.compte.references) + " références";
    rendreSources();
  }).catch((err) => {
    $("srccorps").innerHTML = '<div class="dedans vide">Les dossiers n\'ont pas pu ' +
      "charger : " + echapperSource(String(err.message || err)) +
      " — le serveur sert-il bien <code>/recherche</code> ?</div>";
  });
}

window.BatailleSources = Object.freeze({
  charger: chargerSources,
  chargerSiBesoin: () => srcData ? Promise.resolve(srcData) : chargerSources(),
});
})();
