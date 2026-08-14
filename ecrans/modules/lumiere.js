// lumiere.js — la lumière du jour sur la page. L'heure de la fiction ne change
// pas le thème (clair ou sombre restent au système, c'est-à-dire à la pièce où
// le joueur est assis) : elle ne teinte que le FOND, et d'un souffle.
//
// Trois règles, et elles ne sont pas décoratives :
//   1. On ne touche jamais `--ink` ni `--muted`. Le contraste du texte est fixe
//      quelle que soit l'heure — sinon on paie une humeur avec de la lisibilité.
//   2. L'amplitude est faible. On doit le SENTIR, pas le voir : entre midi et
//      minuit il y a quelques pour cent de luminance et un virage tiède/froid.
//   3. Le glissement se voit parce que le temps saute. Un `recit` de 420
//      minutes fait passer la nuit d'un coup ; la transition de 1,8 s
//      transforme le saut en coucher de soleil. C'est là qu'on sent l'heure
//      tourner, et c'est le seul endroit du jeu où c'est vrai.
//
// Bus.poserHeure() appelle Lumiere.poser(minute) — un seul point d'entrée, la
// même minute que la montre du bandeau.
"use strict";
window.Lumiere = (() => {
  // Les stops de la journée, en minutes depuis minuit. On interpole entre eux.
  // `fond` = le papier de la page ; `lueur` = le jour qui tombe par le haut,
  // un dégradé posé derrière tout le contenu (jamais par-dessus).
  const JOUR = {
    clair: [
      { m:    0, fond: "#e9e8e8", lueur: "rgba(70,90,130,.10)" },  // nuit, froide
      { m:  330, fond: "#f2eae6", lueur: "rgba(190,120,110,.10)" }, // aube (5h30)
      { m:  480, fond: "#f5f0e7", lueur: "rgba(140,170,200,.09)" }, // matin (8h)
      { m:  750, fond: "#f8f5ec", lueur: "rgba(210,200,170,.10)" }, // midi (12h30)
      { m: 1020, fond: "#f5eee1", lueur: "rgba(205,165,110,.10)" }, // relevée (17h)
      { m: 1200, fond: "#f1e5d2", lueur: "rgba(190,110,60,.13)" },  // vêpres (20h)
      { m: 1320, fond: "#e9e8e8", lueur: "rgba(70,90,130,.10)" },   // nuit (22h)
      { m: 1440, fond: "#e9e8e8", lueur: "rgba(70,90,130,.10)" },
    ],
    sombre: [
      { m:    0, fond: "#12131a", lueur: "rgba(80,110,180,.10)" },
      { m:  330, fond: "#1a1614", lueur: "rgba(200,120,100,.09)" },
      { m:  480, fond: "#181614", lueur: "rgba(120,160,200,.07)" },
      { m:  750, fond: "#1c1a16", lueur: "rgba(210,195,160,.08)" },
      { m: 1020, fond: "#1a1613", lueur: "rgba(200,160,110,.08)" },
      { m: 1200, fond: "#1d1510", lueur: "rgba(190,105,55,.12)" },
      { m: 1320, fond: "#12131a", lueur: "rgba(80,110,180,.10)" },
      { m: 1440, fond: "#12131a", lueur: "rgba(80,110,180,.10)" },
    ],
  };

  const hex = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  const rgba = (c) => c.slice(c.indexOf("(") + 1, -1).split(",").map(Number);
  const melange = (a, b, t) => a.map((v, i) => a[i] + (b[i] - a[i]) * t);
  const enHex = (v) => "#" + v.map((n) =>
    Math.round(n).toString(16).padStart(2, "0")).join("");
  const enRgba = (v) => "rgba(" + v.slice(0, 3).map(Math.round).join(",") +
    "," + v[3].toFixed(3) + ")";

  let derniere = null;

  function poser(min) {
    if (typeof min !== "number" || !isFinite(min)) return;
    derniere = ((min % 1440) + 1440) % 1440;
    const sombre = window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    const stops = sombre ? JOUR.sombre : JOUR.clair;

    let i = 0;
    while (i < stops.length - 2 && stops[i + 1].m <= derniere) i++;
    const a = stops[i], b = stops[i + 1];
    const t = b.m === a.m ? 0 : (derniere - a.m) / (b.m - a.m);

    const r = document.documentElement.style;
    r.setProperty("--fond", enHex(melange(hex(a.fond), hex(b.fond), t)));
    r.setProperty("--jour-lueur", enRgba(melange(rgba(a.lueur), rgba(b.lueur), t)));
  }

  // Le joueur peut basculer son système en pleine partie : on repeint sur la
  // même minute, sinon on lui laisse un fond de jour sur un thème de nuit.
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const relire = () => { if (derniere !== null) poser(derniere); };
    if (mq.addEventListener) mq.addEventListener("change", relire);
    else if (mq.addListener) mq.addListener(relire);
  }

  return { poser };
})();
