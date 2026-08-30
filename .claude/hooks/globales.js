#!/usr/bin/env node
// -*- coding: utf-8 -*-
/**
 * GLOBALES — pas de `window.X =` neuve : le front n'a le droit qu'aux portes.
 *
 * PostToolUse sur Write|Edit, cliquet comme taille.js : un fichier garde les
 * globales qu'il posait au dernier commit, il n'en gagne pas. Un fichier neuf
 * n'en pose qu'UNE — la porte de son dossier, le motif que `books/books.js` a
 * demontre (quatorze modules, une seule globale posee par l'assembleur).
 *
 * POURQUOI UN CLIQUET. Le depot compte ~64 globales window.* pour ~110
 * fichiers en IIFE ; une interdiction seche crierait sur chaque edition d'un
 * fichier existant et serait debranchee le jour meme. Le cliquet ne demande
 * aucun chantier : il rend seulement la 65e impossible en silence.
 *
 * IL SE TAIT quand une globale disparait, et il ne dit rien du contenu — il
 * compte des NOMS poses (`window.X =`), pas des usages.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const sepWin = String.fromCharCode(92);

const NEUF_MAX = 1;                       // un fichier neuf = une porte au plus
const FRONT = /(^|[/\\])ecrans[/\\].*\.js$/i;
const PASSER = /([.]min[.]js$|[/\\]vendor[/\\]|node_modules)/i;
const MOTIF = /window\.([A-Za-z_$][\w$]*)\s*=(?!=)/g;

let brut = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => { brut += c; });
process.stdin.on("end", () => { try { juger(); } catch (e) { /* un hook ne casse rien */ } });

function globalesDe(texte) {
  const noms = new Set();
  let m;
  while ((m = MOTIF.exec(texte)) !== null) noms.add(m[1]);
  return noms;
}

/** Les globales posees au dernier commit, ou null si le fichier n'y etait pas. */
function globalesAuDernierCommit(racine, relatif) {
  try {
    const s = execFileSync("git", ["show", "HEAD:" + relatif.split(sepWin).join("/")],
      { cwd: racine, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"],
        maxBuffer: 64 * 1024 * 1024 });
    return globalesDe(s);
  } catch (e) { return null; }
}

function juger() {
  const entree = JSON.parse(brut);
  const fichier = (entree.tool_response && entree.tool_response.filePath)
    || (entree.tool_input && entree.tool_input.file_path);
  if (!fichier || PASSER.test(fichier) || !FRONT.test(fichier)) return;

  const racine = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  let contenu;
  try { contenu = fs.readFileSync(fichier, "utf8"); } catch (e) { return; }

  const relatif = path.relative(racine, path.resolve(fichier));
  if (relatif.startsWith("..")) return;

  const maintenant = globalesDe(contenu);
  const avant = globalesAuDernierCommit(racine, relatif);

  const neuves = avant === null
    ? (maintenant.size > NEUF_MAX ? [...maintenant] : [])
    : [...maintenant].filter((g) => !avant.has(g));
  if (!neuves.length) return;

  const nom = path.basename(fichier);
  const message = avant === null
    ? `${nom} : ${maintenant.size} globales posees — un fichier neuf n'en pose qu'une, sa porte.`
    : `${nom} : globale(s) neuve(s) — ${neuves.join(", ")}. Le front n'a le droit qu'aux portes.`;

  const detail = `Le fichier ${relatif} pose ${neuves.length} globale(s) window.* `
    + `qui n'existai(en)t pas au dernier commit : ${neuves.join(", ")}. La regle du `
    + `depot (docs/organisation.md §2) : un dossier d'ecran = UNE globale, posee par `
    + `sa porte — le motif de books/books.js. Range la piece dans le dossier de son `
    + `sujet et fais-la porter par la globale existante, ou si cette globale doit `
    + `vraiment naitre (une porte nouvelle), dis-le explicitement en rendant la main.`;

  process.stdout.write(JSON.stringify({
    systemMessage: message,
    hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: detail },
  }));
}
