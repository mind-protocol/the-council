# -*- coding: utf-8 -*-
"""Facade publique du miroir CLAUDE.md -> AGENTS.md.

    python scripts/copier_claude_vers_agents.py
    python scripts/copier_claude_vers_agents.py --verifier

La matiere vit dans scripts/agents/prompts/, comme demande. Cette facade est le
runner au chemin public de scripts/ (docs/organisation.md section 2).
"""
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from agents.expose import copier_claude_vers_agents_main as main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
