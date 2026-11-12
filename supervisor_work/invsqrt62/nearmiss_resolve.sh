#!/bin/sh
# Supervisor 2026-11-12 05:xx UTC. Exact repair test for SA near-misses: take the last best gate list of a cswap_win_sa_dump log
# (K-1 gates with residual > 0), append one dummy gate, and run the exact transvection-model tests with the dummy dropped:
#   tv_merge2 (drop any gate, re-solve any 1 gate), tv_merge3 / tv_merge3g (drop any gate, re-solve any pair). The tests loop over
#   every dropped gate (dummy included); every reported MERGE is asserted exact, i.e. a (K-1)-gate exact network.  Usage: sh nearmiss_resolve.sh in_tv.txt dump.log outprefix
IN=$1; LOG=$2; OUT=$3; D=$(dirname "$0")
awk '/^restart/{n++; delete g; k=0} /^bgate/{g[k++]=$2" "$3" "$4} END{for(i=0;i<k;i++) print g[i]}' "$LOG" > "$OUT.gates"
K=$(wc -l < "$OUT.gates"); echo "0 1 1" >> "$OUT.gates"
echo "near-miss gates $K + dummy (index $K)"
export TV_NEARMISS=1
for t in tv_merge2 tv_merge3 tv_merge3g; do echo "$t: $(python3.13 "$D/$t.py" "$IN" "$OUT.gates" | grep -c MERGE) merges"; done
