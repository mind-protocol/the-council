// attention.js — chaque PHRASE porte ses boutons de geste, inline, révélés au survol.
// Un clic envoie {type:"reaction", locuteur_id, phrase, texte} sans interrompre le flux,
// puis le geste choisi reste inscrit au bout de la phrase.
"use strict";
window.Attention = (() => {
  // Les réactions sont CUSTOM : écrites à la main par le MJ pour une réplique
  // donnée (item.reactions). Aucun set générique. Pas de réactions = pas de boutons.
  function boutons(extras) {
    return (extras || []).map((g) =>
      '<button class="geste-btn" data-g="' + (g.id || g.texte) + '">' +
      g.texte + "</button>").join("");
  }

  // Les appuis du MJ : **ce qui pèse** dans une phrase se rend en gras d'appui.
  // Écrit à la main, jamais automatique — voir CLAUDE.md, « Ton ».
  const appuis = (s) => s.replace(/\*\*(\S(?:[^*]*\S)?)\*\*/g,
    '<b class="appui">$1</b>');

  // LES RENVOIS ÉCRITS À LA MAIN — `[les neufs](44022)`, `[le Sanglier](hallis-roon)`.
  // Un conseiller cite des choses qui ont une adresse (une ligne d'affaire, un
  // homme), et le joueur n'avait aucun moyen de savoir de quoi il parlait. On
  // pose donc le lien dans la phrase, à la forme markdown, et rien d'autre :
  // qui écrit n'a pas à connaître le volume, le numéro suffit à le retrouver.
  //
  // Ici on ne fait que MARQUER — c'est `renvois.js` qui décide si la cible est
  // à portée, met l'icône et branche le clic. Une cible inconnue reste du texte
  // nu : jamais de lien mort, et le brouillard tient (un numéro dont on n'a pas
  // le registre sous la main ne doit pas s'allumer).
  const LIEN = /\[([^\][<>\n]{1,80})\]\(([A-Za-z0-9][A-Za-z0-9_-]{0,60})\)/g;
  const liens = (s) => s.replace(LIEN, (m, label, cible) =>
    // Un libellé qui contient une fin de phrase serait coupé en deux par le
    // découpage en phrases, et la balise se déchirerait au milieu. On le laisse
    // alors tel quel : mieux vaut un lien non posé qu'un fil cassé.
    /[.!?…»]\s/.test(label) ? m
      : '<b class="renvoi" data-cible="' + cible + '">' + label + "</b>");

  // Une ligne peut s'ouvrir sur un numéro ou une puce : « 1) », « 2. », « - », « • ».
  // Elle se rend alors avec sa marque à part et le texte en retrait.
  const PUCE = /^\s*(\d{1,2}\s*[).]|[a-z]\)|[-–—•])\s+/;

  // Une énumération écrite au fil de la phrase (« … 1) LE SCEAU … 2) LA PEINE … »)
  // se remet à la ligne : le texte ne change pas, la lecture oui.
  const decouper = (s) => s.replace(/([.!?…»:])\s+(\d{1,2}\s*[).]\s)/g, "$1\n$2");

  // Les capitales d'insistance se rendent en petites capitales : l'appui reste,
  // le pavé qui crie disparaît. Deux mots au moins, dont un de trois lettres.
  const CAP = /[A-ZÀ-ÖØ-Þ]/, BAS = /[a-zà-öø-ÿ]/;
  const estCap = (m) => CAP.test(m) && !BAS.test(m);
  const assezLong = (m) => m.replace(/[^A-ZÀ-ÖØ-Þ]/g, "").length >= 3;
  function petitesCapitales(s) {
    const bouts = s.split(/(\s+)/);   // les séparateurs restent, aux rangs impairs
    let out = "", i = 0;
    while (i < bouts.length) {
      if (i % 2 === 0 && estCap(bouts[i])) {
        let j = i, dur = false;
        while (j < bouts.length && (j % 2 === 1 || estCap(bouts[j]))) {
          if (j % 2 === 0 && assezLong(bouts[j])) dur = true;
          j++;
        }
        while (j > i && (j - 1) % 2 === 1) j--;   // ne pas avaler l'espace final
        const bloc = bouts.slice(i, j).join("");
        out += (dur && j - i >= 3) ? '<span class="capitales">' + bloc + "</span>" : bloc;
        i = j;
      } else { out += bouts[i]; i++; }
    }
    return out;
  }

  function html(texte, meta) {
    const loc = (meta && meta.locuteur_id) || "";
    const btns = boutons(meta && meta.extras);
    const wrap = (ph, fin) =>
      '<span class="phrase-wrap"><span class="phrase" data-loc="' + loc + '">' + ph +
      "</span>" + (fin && btns ? '<span class="gestes">' + btns + "</span>" : "") + "</span>";
    // Les renvois se posent AVANT tout le reste, sur le texte brut : leurs
    // crochets ne survivraient pas au découpage en petites capitales. Et c'est
    // le texte D'ORIGINE qui décide si l'item portait déjà du HTML — sinon un
    // simple lien ferait basculer toute la pièce en passe-plat.
    const source = texte == null ? "" : String(texte);
    const brut = liens(source);
    if (source.indexOf("<") !== -1) return wrap(appuis(brut), true);
    // Les blocs : une ligne écrite = une ligne lue. Les lignes vides ne rendent
    // rien par elles-mêmes — c'est l'écart entre blocs qui les dit.
    const blocs = [];
    decouper(brut).split(/\n/).forEach((l) => {
      const t = l.trim();
      if (!t) return;
      const m = t.match(PUCE);
      blocs.push(m ? { puce: m[1].trim(), texte: t.slice(m[0].length) } : { texte: t });
    });
    if (!blocs.length) return "";
    // On coupe les phrases sur le texte NU, et l'on n'habille qu'après : sans
    // quoi la coupe tombe au milieu d'une balise et l'emboîtement se déchire.
    const corps = (t, dernier) => t.split(/(?<=[.!?…»])\s+/)
      .map((ph, k, arr) => wrap(appuis(petitesCapitales(ph)),
        dernier && k === arr.length - 1)).join(" ");
    // Un seul bloc sans puce : rien ne change, on reste en ligne comme avant.
    if (blocs.length === 1 && !blocs[0].puce) return corps(blocs[0].texte, true);
    return blocs.map((b, i) => {
      const c = corps(b.texte, i === blocs.length - 1);
      return b.puce
        ? '<span class="ligne ligne-puce"><span class="puce">' + b.puce +
          '</span><span class="ligne-corps">' + c + "</span></span>"
        : '<span class="ligne">' + c + "</span>";
    }).join("");
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest(".geste-btn");
    if (!b) return;
    const w = b.closest(".phrase-wrap");
    const ph = w.querySelector(".phrase");
    if (ph.classList.contains("reagie")) return;
    Bus.envoyer({ type: "reaction", locuteur_id: ph.dataset.loc || null,
      phrase: (ph.textContent || "").slice(0, 120), texte: b.dataset.g });
    ph.classList.add("reagie");
    const fait = document.createElement("span");
    fait.className = "geste-fait";
    fait.textContent = " — " + b.textContent;
    w.querySelector(".gestes").replaceWith(fait);
  });

  return { html };
})();
