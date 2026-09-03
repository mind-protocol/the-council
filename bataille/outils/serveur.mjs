// Mini serveur statique de dev — zéro dépendance. Usage : node outils/serveur.mjs [port]
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { resoudreMontage } from './montages.mjs';

// Racine = le dossier du moteur, pas le cwd : le serveur est lancable
// depuis n'importe ou (entree `bataille` du launch.json de la-companie).
const RACINE = fileURLToPath(new URL('..', import.meta.url)).replace(/[\/]$/, '');
const PORT = Number(process.argv[2] ?? process.env.PORT ?? 4173);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.bin': 'application/octet-stream',
};

createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    let chemin = normalize(decodeURIComponent(url.pathname)).replace(/^([/\\])+/, '');
    if (chemin === '' || chemin === '.') chemin = 'index.html';
    // `/bataille` est une ROUTE, pas un fichier : la vue de travail complete.
    // `/` sert la carte seule (index.html) — voir le partage en pied de main.js.
    if (chemin === 'bataille' || chemin === 'bataille/') chemin = 'bataille.html';
    // montages : données externes (villes cuites) servies depuis leur dépôt
    const monte = resoudreMontage(chemin.replaceAll('\\', '/'));
    const fichier = monte ?? join(RACINE, chemin);
    if (!monte && !fichier.startsWith(RACINE)) throw new Error('hors racine');
    const contenu = await readFile(fichier);
    res.writeHead(200, {
      'Content-Type': TYPES[extname(fichier)] ?? 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    res.end(contenu);
  } catch {
    res.writeHead(404);
    res.end('404');
  }
}).listen(PORT, () => console.log(`serveur sur http://localhost:${PORT}`));
