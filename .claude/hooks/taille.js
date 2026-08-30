#!/usr/bin/env node
// -*- coding: utf-8 -*-
/**
 * TAILLE — le plafond d'un fichier est sa taille au dernier commit, jamais plus.
 *
 * PostToolUse sur Write|Edit. Il ne bloque rien : il signale, et le signalement
 * revient dans le contexte de celui qui vient d'écrire.
 *
 * POURQUOI UN CLIQUET, ET PAS UNE LIMITE À 500. Le dépôt voisin `batailles`
 * refuse tout fichier au-delà de 500 lignes, et cette règle y tient parce
 * qu'elle y a toujours tenu. Ici, 61 fichiers la dépassaient déjà à
 * l'installation — le plus gros à dix mille lignes. Une limite unique en
 * refuserait autant d'un coup, crierait à chaque édition d'un fichier qu'on est justement en train de
 * réduire, et serait débranchée le jour même. Un garde-fou qu'on débranche ne
 * garde rien.
 *
 * LE CLIQUET NE DEMANDE AUCUN CHANTIER PRÉALABLE et rend pourtant
 * l'aggravation impossible dès l'installation : un fichier déjà gros ne peut
 * plus que MAIGRIR, un fichier neuf naît sous 500 lignes. C'est la seule forme
 * qui marche sur un dépôt qui a déjà dérivé — et c'est le mode d'échec exact
 * qu'on veut fermer : le plus gros fichier du dépôt avait pris quatre mille
 * lignes AVANT que son extraction commence, et rien n'empêchait la reprise de
 * poids pendant l'extraction.
 *
 * IL SE TAIT QUAND LE FICHIER MAIGRIT, même s'il reste énorme : dire à
 * quelqu'un qui vient de retirer trois cents lignes que son fichier fait encore
 * neuf mille est le meilleur moyen de lui faire couper le hook.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const sepWin = String.fromCharCode(92);   // la barre inverse de Windows

const NEUF = 500;                       // le plafond d'un fichier qui naît
const CODE = /\.(js|mjs|cjs|py|html|css)$/i;
const PASSER = /(package-lock[.]json|[.]min[.][a-z]+$|[/\]vendor[/\]|[.]avant-|node_modules)/i;

let brut = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => { brut += c; });
process.stdin.on("end", () => { try { juger(); } catch (e) { /* un hook ne casse rien */ } });

function lignes(texte) {
  const t = texte.split("\n");
  if (t[t.length - 1] === "") t.pop();
  return t.length;
}

/** La taille du fichier au dernier commit, ou null s'il n'y était pas. */
function tailleAuDernierCommit(racine, relatif) {
  try {
    const s = execFileSync("git", ["show", "HEAD:" + relatif.split(sepWin).join("/")],
      { cwd: racine, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"],
        maxBuffer: 64 * 1024 * 1024 });
    return lignes(s);
  } catch (e) { return null; }
}

function juger() {
  const entree = JSON.parse(brut);
  const fichier = (entree.tool_response && entree.tool_response.filePath)
    || (entree.tool_input && entree.tool_input.file_path);
  if (!fichier || PASSER.test(fichier) || !CODE.test(fichier)) return;

  const racine = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  let contenu;
  try { contenu = fs.readFileSync(fichier, "utf8"); } catch (e) { return; }
  const combien = lignes(contenu);

  const relatif = path.relative(racine, path.resolve(fichier));
  if (relatif.startsWith("..")) return;          // hors du dépôt : pas notre affaire

  const avant = tailleAuDernierCommit(racine, relatif);
  const plafond = avant === null ? NEUF : avant;
  if (combien <= plafond) return;

  const nom = path.basename(fichier);
  const message = avant === null
    ? `${nom} : ${combien} lignes — un fichier neuf naît sous ${NEUF}.`
    : `${nom} : ${combien} lignes, contre ${avant} au dernier commit — il ne doit que maigrir.`;

  const detail = avant === null
    ? `Le fichier ${relatif} est neuf et fait ${combien} lignes, au-delà des ${NEUF} `
      + `que ce dépôt accorde à une pièce qui naît. Nomme la pièce suivante avant `
      + `qu'elle ne fonde dans celle-ci : découpe-le en modules dont chacun porte une `
      + `responsabilité, et écris le pourquoi de la coupe dans l'en-tête ou dans la `
      + `fiche de couche correspondante. Si la coupe nuirait réellement à la lecture, `
      + `laisse le fichier et dis pourquoi.`
    : `Le fichier ${relatif} faisait ${avant} lignes au dernier commit et en fait `
      + `${combien} maintenant : il a GROSSI de ${combien - avant}. Le plafond d'un `
      + `fichier de ce dépôt est sa taille au dernier commit — un gros fichier a le `
      + `droit d'exister, jamais celui de s'aggraver. Sors ce que tu viens d'ajouter `
      + `dans une pièce nommée plutôt que de l'empiler ici. Si l'ajout doit vraiment `
      + `vivre là, dis-le explicitement en rendant la main.`;

  process.stdout.write(JSON.stringify({
    systemMessage: message,
    hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: detail },
  }));
}
