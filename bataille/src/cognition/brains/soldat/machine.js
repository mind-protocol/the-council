/**
 * 🧠 Brains / Soldat / Machine — la FSM du combattant : `obeir` (sous-machine
 * enFormation / cherche — repère irrésoluble ET seul → on part chercher, la
 * LISTE DE PRIORITÉS du rôle décide qui) / `desoeuvre` (sous-machine
 * grégaire, cherche par défaut si seul). `tuer / proteger / fuir` : places
 * réservées du vocabulaire — déclarées SANS transition entrante, grisées
 * dans le graphe : la feuille de route est visible dans le diagramme.
 * Les gardes d'obéissance appellent langage/resoudre-lieu (PUR, croyances
 * seules) : la condition de la garde est LITTÉRALEMENT celle que la
 * compétence rencontre — aucune duplication. Aucun cas particulier de rôle
 * ici : le rôle vit dans la liste de priorités du chercheur (brain).
 */

import { gardesCercle, actionsCercle, menacePercue } from '../gregaire/machine.js';
import {
  ennemiAuContact,
  derriereLaLigne,
  rapportDeForce,
  cureeOuverte,
  sePreparer,
  engager,
  poursuivre,
  pousserDerriere,
  rompre,
} from '../../competences/combattre.js';
import { geometrieCercle } from '../../competences/se-regrouper.js';
import { pressionDePeur, fuir, espritsRepris } from '../../competences/moral.js';
import { voleePossible, tirer as tirerVolee } from '../../competences/tirer.js';
import { charger } from '../../competences/charger.js';
import { enSelle, elanSuffisant, seDegager } from '../../competences/monter.js';
import { resoudreEnFormation } from '../../langage/resoudre-lieu.js';

const ordreFormation = (ctx) => {
  const recu = ctx.representation.ordre();
  return recu?.ordre.verbe === 'EN_FORMATION' ? recu : null;
};

const pasSeulAuContact = (ctx) =>
  ctx.representation.contactsCrus().some((c) => c.livree === ctx.representation.maLivree) ||
  geometrieCercle(ctx) !== null;

const moralRompuBrut = (ctx) =>
  pressionDePeur(ctx.representation, ctx.params, ctx.souffle()) > ctx.params.moral.seuilRompt;

export const gardes = {
  ...gardesCercle,
  // ── le moral : LA RUPTURE — l'arrière d'abord (depuis engage, pas de
  // transition : au fer, pas le temps d'y penser), et la contagion fait
  // casser l'unité presque d'un coup ──
  moralRompu: moralRompuBrut,
  espritsRepris: (ctx) => espritsRepris(ctx.representation, ctx.params, ctx.souffle()),
  // ── combat : on n'attaque jamais seul, et le contact prime sur l'ordre —
  // mais un homme rompu n'entend plus rien ──
  // des ennemis AUTOUR (contact ou menace) : pas de desoeuvrement possible —
  // on se tient pret ; seul, on se regroupe (les gardes menace du desoeuvre)
  rencontre: (ctx) =>
    !moralRompuBrut(ctx) &&
    (ennemiAuContact(ctx.representation, ctx.params) || menacePercue(ctx)) &&
    pasSeulAuContact(ctx),
  ordreActifSansEnnemi: (ctx) =>
    ordreFormation(ctx) !== null &&
    !voleePossible(ctx) &&
    !menacePercue(ctx) &&
    !ennemiAuContact(ctx.representation, ctx.params, ctx.params.combat.rayonDesengagement),
  sansOrdreNiEnnemi: (ctx) => {
    const r = ctx.representation.ordre();
    // un ordre ACTIF (formation, charge…) retient : seul REPOS (ou rien) libère
    return (
      (!r || r.ordre.verbe === 'REPOS') &&
      !voleePossible(ctx) &&
      !menacePercue(ctx) &&
      !ennemiAuContact(ctx.representation, ctx.params, ctx.params.combat.rayonDesengagement)
    );
  },
  souffleBas: (ctx) => ctx.souffle() < ctx.params.combat.souffleBas,
  souffleRevenu: (ctx) => ctx.souffle() > ctx.params.combat.souffleEngage,
  derriere: (ctx) => derriereLaLigne(ctx.representation),
  enPremiereLigne: (ctx) =>
    ennemiAuContact(ctx.representation, ctx.params) && !derriereLaLigne(ctx.representation),
  // LA PASSE : un cavalier ne s'arrête pas au fer — il traverse et reprend
  // du champ ; la passe est finie avec assez d'élan (ou plus de selle)
  passeADegager: (ctx) => enSelle(ctx) && ennemiAuContact(ctx.representation, ctx.params),
  passeFinie: (ctx) => !enSelle(ctx) || elanSuffisant(ctx),
  // la VOLÉE : l'archer tire tant qu'il a une cible crue à portée, des
  // flèches, et personne au contact — sinon, le couteau comme tout le monde
  voleePossible: (ctx) => voleePossible(ctx),
  voleeFinie: (ctx) => !voleePossible(ctx),
  // la CURÉE : le combat local est fini, ils rompent tous — il ne reste qu'à
  // courir. SAUF en posture DÉFENSE : on ne quitte pas sa ligne pour un dos
  // qui fuit (c'est comme ça qu'on perd les ponts — la fausse retraite)
  cureeOuverte: (ctx) =>
    ctx.representation.posture !== 'defense' && cureeOuverte(ctx.representation),
  cureeFermee: (ctx) => !cureeOuverte(ctx.representation),
  rapportFavorable: (ctx) =>
    ctx.souffle() >= ctx.params.combat.souffleEngage &&
    !derriereLaLigne(ctx.representation) &&
    rapportDeForce(ctx.representation, ctx.params, ctx.souffle()).rapport >= 1,
  ordreActif: (ctx) =>
    !moralRompuBrut(ctx) &&
    !ennemiAuContact(ctx.representation, ctx.params) &&
    !voleePossible(ctx) && // l'ordre debout ne réaspire pas un arc qui a une cible
    ordreFormation(ctx) !== null,
  ordreLeve: (ctx) => {
    const r = ctx.representation.ordre();
    // l'émetteur d'un RATISSER n'y obéit pas : il est libéré — il MÈNE
    // (désœuvré, il suit son unité, et sa couverture s'étend avec elle)
    return (
      !r ||
      r.ordre.verbe === 'REPOS' ||
      (r.emetteur === ctx.representation.monId && r.ordre.verbe === 'RATISSER')
    );
  },
  // la charge est sonnée — l'émetteur ne s'exclut PAS : le chef charge aussi
  // AU FER, LES ORDRES ATTENDENT : aucun cri ne sort un homme du contact
  ordreCharger: (ctx) =>
    !moralRompuBrut(ctx) &&
    !ennemiAuContact(ctx.representation, ctx.params) &&
    elanSuffisant(ctx) && // monté : pas de charge sans champ — on reprend d'abord du large
    ctx.representation.ordre()?.ordre.verbe === 'CHARGER',
  // le décrochage : tout le monde recule, l'émetteur compris
  ordreReculer: (ctx) =>
    !moralRompuBrut(ctx) &&
    !ennemiAuContact(ctx.representation, ctx.params) &&
    ctx.representation.ordre()?.ordre.verbe === 'RECULER',
  // je n'obéis pas à mon propre cri : le commandant MÈNE le ratissage
  ordreRatisser: (ctx) => {
    const r = ctx.representation.ordre();
    return (
      !moralRompuBrut(ctx) &&
      !ennemiAuContact(ctx.representation, ctx.params) &&
      r?.ordre.verbe === 'RATISSER' &&
      r.emetteur !== ctx.representation.monId
    );
  },
  /** Sous ordre, repère irrésoluble, et SEUL : au milieu du monde, on tient. */
  repereIrresolubleEtSeul: (ctx) => {
    const recu = ordreFormation(ctx);
    return (
      recu !== null &&
      geometrieCercle(ctx) === null &&
      resoudreEnFormation(recu, ctx.representation, ctx.params, ctx.drill) === null
    );
  },
  repereResolu: (ctx) => {
    const recu = ordreFormation(ctx);
    return recu !== null && resoudreEnFormation(recu, ctx.representation, ctx.params, ctx.drill) !== null;
  },
  entoure: (ctx) => geometrieCercle(ctx) !== null,
};

export const actions = {
  ...actionsCercle,
  fuir,
  charger,
  sePreparer,
  engager,
  poursuivre,
  tirer: tirerVolee,
  seDegager,
  pousserDerriere,
  rompre,
  suivreFormation(ctx) {
    // l'ordre est du TEXTE ({verbe, refs symboliques}) + son émetteur — la
    // résolution (langage) et l'exécution (compétence) se font dans formation
    const r = ctx.formation.agir(ctx.representation.ordre());
    return {
      intention: r.intention,
      objectifHumain: r.objectifHumain,
      cible: r.cible,
      debugFormation: r.debug,
    };
  },
};

export const MACHINE_SOLDAT = {
  brain: 'soldat',
  initial: 'desoeuvre.cherche',
  etats: {
    obeir: {
      initial: 'enFormation',
      sousEtats: {
        enFormation: { agir: 'suivreFormation' },
        ratisse: { agir: 'suivreFormation' }, // même compétence : la formation EN MARCHE
        recule: { agir: 'suivreFormation' }, // le bond ARRIÈRE — front au danger
        charge: { agir: 'charger' }, // sus à l'ennemi — chacun sur SA croyance
        cherche: { agir: 'chercher' },
      },
    },
    desoeuvre: {
      initial: 'cherche',
      sousEtats: {
        cherche: { agir: 'chercher' },
        flane: { agir: 'flaner' },
        rejoint: { agir: 'rejoindre' },
        secarte: { agir: 'ecarter' },
        discute: { agir: 'discuter' },
      },
    },
    tuer: {
      initial: 'pret',
      sousEtats: {
        pret: { agir: 'sePreparer' },
        engage: { agir: 'engager' },
        poursuit: { agir: 'poursuivre' },
        tire: { agir: 'tirer' },
        repasse: { agir: 'seDegager' }, // monté : traverser, reprendre du champ
        pousse: { agir: 'pousserDerriere' },
        recupere: { agir: 'rompre' },
      },
    },
    proteger: {},
    fuir: { agir: 'fuir' },
  },
  transitions: [
    // ── LA PANIQUE d'abord : jamais depuis engage (au fer, pas le temps d'y
    // penser) — l'arrière rompt le premier, la contagion fait le reste ──
    { de: 'fuir', vers: 'desoeuvre.cherche', quand: 'espritsRepris', libelle: 'hors de portée — je reprends mes esprits' },
    { de: 'tuer.pret', vers: 'fuir', quand: 'moralRompu', libelle: 'trop des nôtres tombés — je romps !' },
    { de: 'tuer.pousse', vers: 'fuir', quand: 'moralRompu', libelle: 'trop des nôtres tombés — je romps !' },
    { de: 'tuer.recupere', vers: 'fuir', quand: 'moralRompu', libelle: 'trop des nôtres tombés — je romps !' },
    { de: 'obeir', vers: 'fuir', quand: 'moralRompu', libelle: 'trop des nôtres tombés — je romps !' },
    { de: 'desoeuvre', vers: 'fuir', quand: 'moralRompu', libelle: 'trop des nôtres tombés — je romps !' },
    // ── le combat prime sur tout : l'ennemi est là, et je ne suis pas seul ──
    { de: '*', vers: 'tuer', quand: 'rencontre', libelle: "l'ennemi est au contact — je me tiens prêt" },
    // l'archer : sa rencontre commence à portée de trait, pas à portée de voix
    { de: '*', vers: 'tuer', quand: 'voleePossible', libelle: 'une unité à découvert, à portée de trait — halte' },
    { de: 'tuer', vers: 'obeir', quand: 'ordreActifSansEnnemi', libelle: "plus d'ennemi au contact — je reprends ma place" },
    { de: 'tuer', vers: 'desoeuvre', quand: 'sansOrdreNiEnnemi', libelle: "plus d'ennemi devant — je souffle" },
    { de: 'tuer', vers: 'tuer.recupere', quand: 'souffleBas', libelle: "plus de souffle — je romps d'un pas" },
    { de: 'tuer.recupere', vers: 'tuer.pret', quand: 'souffleRevenu', libelle: 'le souffle revient — je me tiens prêt' },
    { de: 'tuer.pret', vers: 'tuer.repasse', quand: 'passeADegager', libelle: "pas d'arrêt au fer — je traverse et reprends du champ" },
    { de: 'tuer.repasse', vers: 'tuer.pret', quand: 'passeFinie', libelle: 'assez de champ — je me reforme pour repasser' },
    { de: 'tuer.pret', vers: 'tuer.pousse', quand: 'derriere', libelle: 'un des nôtres devant moi — je pousse' },
    { de: 'tuer.pousse', vers: 'tuer.pret', quand: 'enPremiereLigne', libelle: 'me voilà en première ligne' },
    { de: 'tuer.pret', vers: 'tuer.tire', quand: 'voleePossible', libelle: 'ils traversent à découvert — nockez !' },
    { de: 'tuer.tire', vers: 'tuer.pret', quand: 'voleeFinie', libelle: 'plus une flèche ou ils sont sur nous — au couteau !' },
    { de: 'tuer.pret', vers: 'tuer.engage', quand: 'rapportFavorable', libelle: "assez de prêts autour — à l'assaut !" },
    { de: 'tuer.engage', vers: 'tuer.poursuit', quand: 'cureeOuverte', libelle: 'ils rompent tous — sus ! la curée' },
    { de: 'tuer.pret', vers: 'tuer.poursuit', quand: 'cureeOuverte', libelle: 'ils rompent tous — sus ! la curée' },
    { de: 'tuer.poursuit', vers: 'tuer.pret', quand: 'cureeFermee', libelle: 'plus de fuyard à portée — je reforme' },
    { de: '*', vers: 'obeir.charge', quand: 'ordreCharger', libelle: 'la charge est sonnée — sus à l\'ennemi' },
    { de: '*', vers: 'obeir.recule', quand: 'ordreReculer', libelle: 'on décroche — je recule sans tourner le dos' },
    { de: '*', vers: 'obeir.ratisse', quand: 'ordreRatisser', libelle: 'ratissage ordonné — je tiens mon rang en marche' },
    { de: '*', vers: 'obeir', quand: 'ordreActif', libelle: 'ordre reçu de mon chef' },
    { de: 'obeir', vers: 'desoeuvre', quand: 'ordreLeve', libelle: "l'ordre est levé — repos" },
    { de: 'obeir', vers: 'obeir.cherche', quand: 'repereIrresolubleEtSeul', libelle: 'seul et sans repère — je pars chercher' },
    { de: 'obeir.cherche', vers: 'obeir.enFormation', quand: 'repereResolu', libelle: 'repère retrouvé — je reprends ma place' },
    { de: 'obeir.cherche', vers: 'obeir.enFormation', quand: 'entoure', libelle: 'du monde autour — je reprends ma place' },
    { de: 'desoeuvre', vers: 'desoeuvre.rejoint', quand: 'menaceEtEscouadeLoin', libelle: 'une unité ennemie approche — je me regroupe' },
    { de: 'desoeuvre', vers: 'desoeuvre.cherche', quand: 'menaceEtSeul', libelle: 'une unité ennemie approche, seul — je rallie les miens' },
    { de: 'desoeuvre', vers: 'desoeuvre.cherche', quand: 'groupeReduit', libelle: "nous ne sommes qu'une poignée — je pars retrouver le gros" },
    { de: 'desoeuvre', vers: 'desoeuvre.discute', quand: 'surLeCercle', libelle: 'me voilà sur le cercle de discussion' },
    { de: 'desoeuvre', vers: 'desoeuvre.rejoint', quand: 'escouadeLoin', libelle: 'mon escouade est loin — je la rejoins' },
    { de: 'desoeuvre', vers: 'desoeuvre.secarte', quand: 'escouadeTropPres', libelle: "trop au centre du groupe — je m'écarte" },
    { de: 'desoeuvre', vers: 'desoeuvre.cherche', quand: 'seulAvecAttaches', libelle: 'je suis seul — je pars chercher les miens' },
    { de: 'desoeuvre', vers: 'desoeuvre.flane', quand: 'seulSansAttaches', libelle: 'personne à retrouver — je flâne' },
  ],
};
