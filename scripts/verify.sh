#!/usr/bin/env sh
set -eu
python -m compileall -q backend/app sandbox
node --check frontend/app.js
PYTHONPATH=backend python -c "from app.agents.catalog import roster_counts; assert roster_counts()['total']==16111; print(roster_counts())"
PYTHONPATH=backend pytest -q backend/tests
