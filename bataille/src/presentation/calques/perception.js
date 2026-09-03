/**
 * 🖥️ Calque perception — pour l'homme SÉLECTIONNÉ, ses CROYANCES en langage
 * humain : individus suivis (nom + fantôme à la position crue, lien plein si
 * vu à l'instant) et TAS (cercle pointillé au barycentre cru, étiqueté
 * « escouade ×5 » / « unité ×18 »), qui s'estompent avec l'âge du souvenir.
 * Les CONTACTS (corps vus à portée d'armes) : anneau plein à la position
 * crue — rouge sang si livrée adverse, vert doux sinon.
 * Lit vues.perception(id) (vue debug 🧠) et vues.corpsParId.
 * @viz perception-bornee, memoire-datee, perception-tas, attention-dirigee, nom-panache, forme-tas, langage-description, perception-contact, perception-masse, menace-regroupement, poids-de-gabarit
 */

const SEUIL_FRAIS_S = 0.75; // en dessous : « vu à l'instant »

export function dessinerPerception(ctx, camera, vues) {
  const id = vues.idSelectionne;
  if (id == null) return;
  const info = vues.perception(id);
  const corps = vues.corpsParId(id);
  if (!info || !corps) return;

  const ppm = camera.echelle();
  const centre = camera.versEcran(corps.pos);
  ctx.save();
  ctx.font = '11px system-ui, sans-serif';

  // rayon de perception
  ctx.beginPath();
  ctx.arc(centre.x, centre.y, info.portee * ppm, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(122, 162, 247, 0.18)';
  ctx.lineWidth = 1;
  ctx.stroke();

  // individus suivis : fantôme à la position CRUE + nom
  for (const ind of info.individus) {
    if (!ind.pos) continue;
    const p = camera.versEcran(ind.pos);
    const frais = ind.ageS < SEUIL_FRAIS_S;
    if (frais) {
      ctx.beginPath();
      ctx.moveTo(centre.x, centre.y);
      ctx.lineTo(p.x, p.y);
      ctx.strokeStyle = 'rgba(120, 220, 160, 0.5)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    const alpha = frais ? 0.8 : Math.max(0.15, 0.6 - ind.ageS * 0.04);
    ctx.setLineDash(frais ? [] : [3, 3]);
    ctx.beginPath();
    ctx.arc(p.x, p.y, 0.35 * ppm, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(240, 198, 116, ${alpha})`;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = `rgba(230, 220, 190, ${Math.max(alpha, 0.5)})`;
    ctx.fillText(ind.nom ?? `#${ind.id}`, p.x + 0.4 * ppm, p.y - 0.4 * ppm);
  }

  // contacts : les corps vus homme par homme à portée d'armes — la croyance
  // qui nourrira readiness et frappes ; rouge sang = livrée adverse
  const maLivree = corps.livree;
  for (const c of info.contacts ?? []) {
    if (!c.pos) continue;
    const p = camera.versEcran(c.pos);
    const alpha = Math.max(0.2, 0.85 - c.ageS * 0.2);
    const adverse = c.livree && c.livree !== maLivree;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 0.42 * ppm, 0, Math.PI * 2);
    ctx.strokeStyle = adverse ? `rgba(224, 82, 82, ${alpha})` : `rgba(120, 220, 160, ${alpha * 0.6})`;
    ctx.lineWidth = adverse ? 2 : 1.2;
    ctx.stroke();
  }

  // tas : la FORME CRUE si lisible (boîte orientée + première ligne en trait
  // épais), sinon cercle pointillé — étiquette en français (langage/decrire).
  // Une MASSE lointaine (horizon de masse) : cercle pâle à tirets longs,
  // étiquette « ~N (loin) » — le percept se sait grossier, la viz le montre
  for (const t of info.tas) {
    if (!t.barycentre) continue; // croyance sans position (« quelque part »)
    const p = camera.versEcran(t.barycentre);
    const alpha = Math.max(0.12, 0.55 - t.ageS * 0.04);
    if (t.lointain) {
      ctx.setLineDash([10, 8]);
      ctx.strokeStyle = `rgba(190, 200, 220, ${alpha * 0.7})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, t.etendue * ppm, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = `rgba(200, 205, 220, ${Math.max(alpha, 0.45)})`;
      ctx.fillText(`~${t.effectif} ${t.livree ?? ''} (loin)`, p.x + 4, p.y - t.etendue * ppm - 4);
      continue;
    }
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = `rgba(120, 220, 160, ${alpha})`;
    ctx.lineWidth = 1.5;

    if (t.cap !== undefined && t.largeur !== undefined) {
      // boîte orientée : profondeur dans l'axe du cap, largeur en travers
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(t.cap);
      ctx.strokeRect(
        (-t.profondeur / 2) * ppm,
        (-t.largeur / 2) * ppm,
        t.profondeur * ppm,
        t.largeur * ppm
      );
      ctx.restore();
      ctx.setLineDash([]);
      // la première ligne crue : trait épais, perpendiculaire au cap
      if (t.premiereLigne) {
        const c = camera.versEcran(t.premiereLigne.centre);
        const dx = -Math.sin(t.cap) * (t.premiereLigne.largeur / 2) * ppm;
        const dy = Math.cos(t.cap) * (t.premiereLigne.largeur / 2) * ppm;
        ctx.beginPath();
        ctx.moveTo(c.x - dx, c.y - dy);
        ctx.lineTo(c.x + dx, c.y + dy);
        ctx.strokeStyle = `rgba(120, 220, 160, ${Math.min(1, alpha + 0.25)})`;
        ctx.lineWidth = 3;
        ctx.stroke();
      }
    } else {
      ctx.beginPath();
      ctx.arc(p.x, p.y, t.etendue * ppm, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.fillStyle = `rgba(180, 230, 200, ${Math.max(alpha, 0.5)})`;
    ctx.fillText(t.description ?? `${t.etiquette} ×${t.effectif}`, p.x + 4, p.y - t.etendue * ppm - 4);
  }

  ctx.restore();
}
