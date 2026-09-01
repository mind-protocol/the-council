import fs from "node:fs";

const port = process.argv[2] || "9333";
const pages = await fetch(`http://127.0.0.1:${port}/json`).then((r) => r.json());
const page = pages.find((p) => p.type === "page");
if (!page) throw new Error("aucune page CDP");

const ws = new WebSocket(page.webSocketDebuggerUrl);
let numero = 0;
const attentes = new Map();
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (!message.id) return;
  const attente = attentes.get(message.id);
  if (!attente) return;
  attentes.delete(message.id);
  if (message.error) attente.reject(new Error(message.error.message));
  else attente.resolve(message.result);
};
await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = reject;
});

const envoyer = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++numero;
  attentes.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params }));
});
const attendre = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const evaluer = async (expression) => {
  const r = await envoyer("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text || "évaluation refusée");
  return r.result.value;
};

await envoyer("Page.enable");
await envoyer("Runtime.enable");
await envoyer("Page.navigate", { url: "http://localhost:3129/bascule?vers=future-chronicler" });
await attendre(5000);

const avant = await evaluer(`({
  siege: document.body.dataset.siege || null,
  boutons: [...document.querySelectorAll("button")].map((b) => b.textContent.trim()).filter(Boolean)
})`);
const clic = await evaluer(`(() => {
  const b = [...document.querySelectorAll("button")].find((x) => x.textContent.trim() === "Le quartier");
  if (!b) return false;
  b.click();
  return true;
})()`);
await attendre(15000);

const apres = await evaluer(`(() => {
  const hote = document.querySelector("#ville3d .ville3d-noms");
  const labels = hote ? [...hote.querySelectorAll("*")].map((e) => ({
    texte: e.textContent.trim(),
    classe: e.className,
    display: getComputedStyle(e).display,
    visibility: getComputedStyle(e).visibility,
    opacity: getComputedStyle(e).opacity
  })).filter((x) => x.texte) : [];
  return {
    siege: document.body.dataset.siege || null,
    hote: !!hote,
    classes: document.getElementById("ville3d")?.className || null,
    quai: labels.filter((x) => x.texte.includes("Quai des Deux Rives")),
    bassin: labels.filter((x) => x.texte.includes("Bassin des Fondations")),
    labels: labels.slice(0, 80)
  };
})()`);

const capture = await envoyer("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
fs.writeFileSync(
  "C:/Users/reyno/le-conseil2/chambres/future_chronicler/brouillons/audit-rendu-vmti7dah5pnl8.png",
  Buffer.from(capture.data, "base64")
);
console.log(JSON.stringify({ clic, avant, apres }, null, 2));
ws.close();
