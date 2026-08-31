# -*- coding: utf-8 -*-
"""Facade de la file de beats PNJ d'un Jump."""
import os as _os
import sys as _sys

_d = _os.path.dirname(_os.path.abspath(__file__))
if _d not in _sys.path:
    _sys.path.insert(0, _d)

from agents.jump_beats import main  # noqa: E402


if __name__ == "__main__":
    main()
