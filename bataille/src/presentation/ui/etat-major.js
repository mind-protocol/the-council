/**
 * 🖥️ UI / État-major — la viz de la délibération du commandant (inspecteur,
 * quand l'homme sélectionné commande), en VISUEL, pas en tableau de texte :
 * les candidates en BARRES de score divergentes (l'engagée en dorée, zéro au
 * centre — le plancher d'engagement se voit), les 6 AXES de la gagnante en
 * mini-barres signées (l'outil de réglage des poids), la phase en POINTS,
 * la situation en PASTILLES (les faits vrais allumés). Il AFFICHE, il
 * n'interprète pas.
 * @viz etat-major, manoeuvres
 */

const el = (classe, texte) => {
  const e = document.createElement('div');
  e.className = classe;
  if (texte !== undefined) e.textContent = texte;
  return e;
};

/** Une barre divergente : zéro au centre, positif vers la droite. */
const barreSignee = (valeur, portee, classe) => {
  const barre = el(`pd-em-barre ${classe ?? ''}`);
  const zero = el('pd-em-zero');
  const rempli = el('pd-em-rempli');
  const part = Math.max(-1, Math.min(1, valeur / portee)) * 50; // en % depuis le centre
  rempli.style.left = part < 0 ? `${50 + part}%` : '50%';
  rempli.style.width = `${Math.max(1, Math.abs(part))}%`;
  rempli.classList.add(valeur >= 0 ? 'positif' : 'negatif');
  barre.append(zero, rempli);
  return barre;
};

/**
 * @param {Object} debug — introspection.etatMajor (arbitre.etatMajorDebug())
 * @returns {HTMLElement}
 */
export function rendreEtatMajor(debug) {
  const bloc = el('pd-etat-major');
  bloc.append(el('pd-pourquoi-titre', 'état-major'));

  // ── les CANDIDATES : nom + barre de score (zéro au centre = le plancher)
  const candidates = debug.candidates ?? [];
  const portee = Math.max(0.5, ...candidates.filter((c) => Number.isFinite(c.score)).map((c) => Math.abs(c.score)));
  for (const c of candidates) {
    const engagee = debug.engagee?.nom === c.nom;
    const l = el(`pd-em-candidate${engagee ? ' engagee' : ''}${!c.applicable || c.boudee ? ' eteinte' : ''}`);
    l.append(el('pd-em-nom', `${engagee ? '⚔ ' : ''}${c.nom}`));
    if (c.boudee) l.append(el('pd-em-etat', '⏳ boudée'));
    else if (!c.applicable) l.append(el('pd-em-etat', '∅'));
    else {
      l.append(barreSignee(c.score, portee, engagee ? 'engagee' : ''));
      l.append(el('pd-em-score', c.score.toFixed(2)));
    }
    bloc.append(l);
  }

  // ── les AXES de l'engagée (sinon la meilleure applicable) : le réglage se
  // fait en regardant CES barres — chaque axe est signé, ~[-1, 1]
  const detaillee =
    candidates.find((c) => debug.engagee?.nom === c.nom && c.axes) ??
    candidates.filter((c) => c.axes).reduce((a, b) => (b.score > (a?.score ?? -Infinity) ? b : a), null);
  if (detaillee?.axes) {
    const cadre = el('pd-em-axes');
    for (const [axe, v] of Object.entries(detaillee.axes)) {
      const l = el('pd-em-axe');
      l.append(el('pd-em-axe-nom', axe), barreSignee(v, 1), el('pd-em-axe-val', v.toFixed(2)));
      cadre.append(l);
    }
    bloc.append(cadre);
  }

  // ── l'ENGAGÉE : la phase en points ● ● ○, puis la justification
  if (debug.engagee) {
    const l = el('pd-em-phase');
    l.append(el('pd-em-nom engagee', debug.engagee.nom));
    const points = el('pd-em-points');
    const total = debug.engagee.phases ?? debug.engagee.phase + 1;
    for (let i = 0; i < total; i++) {
      points.append(el(`pd-em-point${i <= debug.engagee.phase ? ' fait' : ''}`));
    }
    l.append(points, el('pd-em-etat', `${Math.round(debug.engagee.tempsPhase ?? 0)} s`));
    bloc.append(l);
  }
  if (debug.justification) bloc.append(el('pd-pourquoi-raison', `« ${debug.justification} »`));
  if (debug.abandon) bloc.append(el('pd-pourquoi-quand', `abandon : ${debug.abandon}`));

  // ── la SITUATION : pastilles — les faits VRAIS allumés, les faux éteints,
  // les scalaires en chiffres
  const faits = el('pd-em-faits');
  for (const [fait, v] of Object.entries(debug.situation ?? {})) {
    if (typeof v === 'boolean') faits.append(el(`pd-em-fait${v ? ' vrai' : ''}`, fait));
    else faits.append(el('pd-em-fait chiffre', `${fait} ${typeof v === 'number' ? v.toFixed(1) : v}`));
  }
  bloc.append(faits);

  return bloc;
}
