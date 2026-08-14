# -*- coding: utf-8 -*-
"""POSER UNE PARCELLE — la primitive commune au semis réglé et au semis organique.

Elle vivait dans `densifier.py`, où l'organique aurait dû la recopier. Deux
copies d'une géométrie, c'est deux villes qui divergent au premier réglage.

CE QU'ELLE FAIT, et c'est tout le sujet : elle ne répond pas « oui » ou « non »,
elle rend LA PARCELLE QUI RENTRE. Le test d'avant était tout ou rien — une
parcelle entrait à sa taille tirée ou elle était jetée. Or une ville n'est pas
bâtie de gabarits, elle est bâtie de ce qui rentre : un reste de sept mètres ne
peut pas recevoir une parcelle de onze, donc il restait vide, et c'est ainsi que
la moitié du sol de Port-Réal était du terrain vague au cœur des îlots.

Deux gestes, dans cet ordre :

    tailler()   rogne jusqu'à ce que ça tienne — la PROFONDEUR d'abord (une
                maison de coin est courte, elle n'est pas étroite), la façade
                ensuite. Sous F_MINI par P_MINI, ce n'est plus une maison.
    coller()    ferme le jour qui reste avec le voisin. Rogner laisse forcément
                des lisières de deux ou trois décimètres, qu'aucun maçon ne
                laisse et qu'aucune ville ne tolère : on étire jusqu'au contact.
                C'est la mitoyenneté comme GESTE, au lieu de l'espérer d'un pas
                de progression bien calculé.

Le sol est passé en callback (`case_libre`) : le semis réglé interdit la
chaussée déjà tracée, l'organique interdit ce qu'il vient de bâtir. La
géométrie, elle, est la même.
"""
import math

DOS = 0.8        # ce qu'on laisse entre deux rangs qui se tournent le dos
TOL = 0.05       # deux maisons qui se touchent JUSTE ne se refusent pas
COLLAGE = 1.2    # au-delà de ce jour, on n'étire plus : c'est une venelle
BOITE = 12.0     # le pas du casier de recherche, en mètres
F_MINI = 2.5     # sous quoi ce n'est plus une maison mais un appentis
P_MINI = 3.5

# les rognages successifs, du plus généreux au plus maigre
PAS_P = (1.0, .82, .66, .52, .40, .30)
PAS_F = (1.0, .84, .70, .56, .44, .34)


class Occupation(object):
    """Ce qui est déjà bâti, rangé en casiers pour qu'on le retrouve vite."""

    def __init__(self, case_libre):
        self.case_libre = case_libre
        self.cases = {}

    def _casiers(self, x, y, r):
        for i in range(int((x-r)//BOITE), int((x+r)//BOITE)+1):
            for j in range(int((y-r)//BOITE), int((y+r)//BOITE)+1):
                yield (i, j)

    def occuper(self, x, y, f, p, cap):
        a = math.radians(cap)
        e = (x, y, f*0.5, p*0.5, math.cos(a), math.sin(a))
        for c in self._casiers(x, y, 0.5*math.hypot(f, p)):
            self.cases.setdefault(c, []).append(e)

    def voisins(self, x, y, f, p, cap):
        """Les emprises voisines, dans MON repère : l'écart le long de la
        façade, l'écart vers le fond, et leur demi-emprise projetée sur mes
        axes — un voisin peut être de biais, deux rues qui se croisent n'ayant
        pas le même cap."""
        a = math.radians(cap)
        vx, vy = math.cos(a), math.sin(a)
        r = 0.5*math.hypot(f, p) + DOS + 2.0
        for c in self._casiers(x, y, r):
            for (ox, oy, ohf, ohp, wx, wy) in self.cases.get(c, ()):
                dl = (ox-x)*vx + (oy-y)*vy
                dt = (oy-y)*vx - (ox-x)*vy
                co = abs(wx*vx + wy*vy)
                si = abs(wy*vx - wx*vy)
                yield dl, dt, ohf*co + ohp*si, ohf*si + ohp*co

    def tient(self, x, y, f, p, cap, joint):
        """l'emprise tient-elle ici, sans toucher le sol interdit ni un voisin ?"""
        a = math.radians(cap)
        vx, vy = math.cos(a), math.sin(a)
        for sf, sp in ((-.48,-.48), (.48,-.48), (.48,.48), (-.48,.48), (0,-.48), (0,.48)):
            if not self.case_libre(x + vx*f*sf - vy*p*sp, y + vy*f*sf + vx*p*sp):
                return False
        hf, hp = f*0.5, p*0.5
        for dl, dt, ef, ep in self.voisins(x, y, f, p, cap):
            if abs(dl) < hf + ef + joint - TOL and abs(dt) < hp + ep + DOS - TOL:
                return False
        return True

    def tailler(self, xf, yf, f, p, cap, joint):
        """La parcelle réellement posable ici, rognée sur ce qui est libre.

        `(xf, yf)` est le MILIEU DE LA FAÇADE, jamais le centre : c'est lui qui
        doit rester sur la rue quand la profondeur se raccourcit.

        Rend `(x, y, f, p)` — centre et mesures — ou None.
        """
        a = math.radians(cap)
        nx, ny = -math.sin(a), math.cos(a)
        for kp in PAS_P:
            p2 = p*kp
            if p2 < P_MINI: break
            for kf in PAS_F:
                f2 = f*kf
                if f2 < F_MINI: break
                x, y = xf + nx*p2*0.5, yf + ny*p2*0.5
                if self.tient(x, y, f2, p2, cap, joint):
                    return self.coller(x, y, f2, p2, cap, joint)
        return None

    def coller(self, x, y, f, p, cap, joint):
        """Étire la façade jusqu'au contact quand le voisin est à portée."""
        a = math.radians(cap)
        vx, vy = math.cos(a), math.sin(a)
        hf, hp = f*0.5, p*0.5
        gains = [0.0, 0.0]                     # à droite, à gauche
        for dl, dt, ef, ep in self.voisins(x, y, f, p, cap):
            if abs(dt) >= hp + ep + DOS - TOL: continue     # pas au même rang
            jeu = abs(dl) - hf - ef                          # le jour qui sépare
            if 0.0 <= jeu <= COLLAGE:
                k = 0 if dl > 0 else 1
                gains[k] = max(gains[k], jeu)
        if gains[0] or gains[1]:
            f2 = f + gains[0] + gains[1]
            d = (gains[0] - gains[1])*0.5      # le centre glisse de la moitié
            x2, y2 = x + vx*d, y + vy*d
            if self.tient(x2, y2, f2 - 2*TOL, p, cap, 0.0):
                return x2, y2, f2, p
        return x, y, f, p
