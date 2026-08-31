// -*- coding: utf-8 -*-
"use strict";
const { planter, chargerBataille, DEFAUTS } = require("./banc-moteur.js");

const exiger=(vrai,dit)=>{
  console.log((vrai?"ok  ":"NON ")+dit);
  if(!vrai)process.exitCode=1;
};

function couloir(B,tous,ignores){
  const base=tous.find((h)=>h.camp==="garde"&&!h.hors);
  for(let r=20;r<=180;r+=10)for(let k=0;k<32;k++){
    const a=k*Math.PI/16,ux=Math.cos(a),uy=Math.sin(a);
    const x=base.x+ux*r,y=base.y+uy*r;
    const pts=[[x,y],[x+ux*.85,y+uy*.85],[x+ux*12,y+uy*12],
      [x-uy,y+ux],[x+uy,y-ux]];
    if(!pts.every((p)=>B.libre(p[0],p[1])===true))continue;
    if(tous.some((h)=>!ignores.has(h)&&h.etat!=="mort"&&
      Math.hypot(h.x-x,h.y-y)<4))continue;
    return {x,y,ux,uy};
  }
  throw new Error("aucun couloir libre pour le banc de circulation");
}

function poser(h,x,y,etat){
  h.x=x;h.y=y;h.ex=x;h.ey=y;h.px=x;h.py=y;h.interieur=null;
  h.cible=null;h.etat=etat||"rassemble";h.vit=1.5;
  h.cedePassageA=-Infinity;h.cedePour=null;h.cedePourChef=false;h.cedeDistance=0;
  h.immobileDepuis=-10;
}

async function main(){
  planter(DEFAUTS.serveur);
  const B=chargerBataille();
  await B.preparer(DEFAUTS.source);
  B.echelle(.05);B.rejouer();

  let tous=B.troupe(),us=B.unites();
  const u=us.find((q)=>q.camp==="garde"&&q.debout>=3);
  const n=us.findIndex((q)=>q.id===u.id);
  const chef=tous.find((h)=>h.formation===n&&h.chefFormation);
  const bloque=tous.find((h)=>h.camp==="garde"&&h!==chef&&!h.chefFormation);
  const p=couloir(B,tous,new Set([chef,bloque]));
  poser(chef,p.x,p.y);poser(bloque,p.x+p.ux*.85,p.y+p.uy*.85,"prisonnier");
  B.ordonnerFormation(u.id,{id:"banc:passage-chef",nom:"le bout du passage",
    x:p.x+p.ux*12,y:p.y+p.uy*12});
  B.pas(.1);
  const distanceChef=bloque.cedeDistance;

  B.rejouer();tous=B.troupe();us=B.unites();
  const u2=us.find((x)=>x.camp==="garde"&&x.debout>=3);
  const n2=us.findIndex((x)=>x.id===u2.id);
  const marcheur=tous.find((h)=>h.formation===n2&&h.chefFormation);
  const bloque2=tous.find((h)=>h.camp==="garde"&&h!==marcheur&&!h.chefFormation);
  const q=couloir(B,tous,new Set([marcheur,bloque2]));
  poser(marcheur,q.x,q.y);poser(bloque2,q.x+q.ux*.85,q.y+q.uy*.85,"prisonnier");
  // Il reste le guide concret de son unité, mais le micro-comportement ne le
  // voit plus comme un chef : même trajet, seule la priorité sociale change.
  marcheur.chefFormation=false;marcheur.capitaine=false;marcheur.tete=false;
  B.ordonnerFormation(u2.id,{id:"banc:passage-allie",nom:"le bout du passage",
    x:q.x+q.ux*12,y:q.y+q.uy*12});
  B.pas(.1);
  const distanceAllie=bloque2.cedeDistance;

  console.log("\nBANC DE CIRCULATION — céder le passage\n");
  exiger(bloque2.cedePour===marcheur.debugId&&!bloque2.cedePourChef,
    "un homme immobile cède devant un allié qui avance");
  exiger(bloque.cedePour===chef.debugId&&bloque.cedePourChef,
    "un homme immobile reconnaît la priorité d'un chef en mouvement");
  exiger(distanceChef>distanceAllie*1.8,
    "le pas de côté est nettement plus franc pour le chef");
  console.log("\nallié "+distanceAllie.toFixed(3)+" m · chef "+distanceChef.toFixed(3)+" m\n");
}

main().catch((e)=>{console.error("banc-circulation : "+(e&&e.stack||e));process.exit(1);});
