#!/bin/bash
cd ~/Desktop/CLAUDE-HUB/kaggle-qcircuit; P=.venv/bin/python; V=data/verifiers
/usr/bin/time -l $P $V/invsqrt/verify_submission_invsqrt.py ext/top_v12/invsqrt.kmb --salt notebook-verification > runs/top_v12/invsqrt.json 2> runs/top_v12/invsqrt.err
/usr/bin/time -l $P $V/dqi/verify_submission_dqi.py ext/top_v12/dqi.kmb --salt notebook-verification > runs/top_v12/dqi.json 2> runs/top_v12/dqi.err
/usr/bin/time -l $P $V/dqi/verify_submission_dqi.py runs/ref/dqi_ref.kmb > runs/ref/dqi.json 2> runs/ref/dqi.err
