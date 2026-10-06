#!/bin/bash
# simulate K variants for $RACE_CFG and keep the most exciting one
B=${BLENDER:-blender}
K=${K:-6}
rm -f sim_${RACE_CFG//:/_}_v*.npz
for v in $(seq 0 $((K-1))); do RACE_VARIANT=$v $B -b -P race.py -- --sim 2>&1 | grep -E "Error|Traceback|saved" -A3; done
${PY:-python} pick.py
