# -*- coding: utf-8 -*-
"""PAGE — la mise en page du rapport : largeur, titres, lignes, cales.
"""
import sys

from plan.expose import nu, sans_emoji

LARGEUR = 96


def titre(t):
    sys.stdout.write(u"\n" + t + u"\n" + u"─" * LARGEUR + u"\n")


def ligne(*cols):
    sys.stdout.write(u"  " + u"".join(cols) + u"\n")


def cale(t, n):
    t = nu(t)
    return (t[:n - 1] + u"…") if len(t) > n else t.ljust(n)

