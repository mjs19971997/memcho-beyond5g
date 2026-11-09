# Determinism across machines

The second run (`results/full_ext`) reuses the rows of rules whose settings did not change from the first run
(`results/full`). This is valid only if the same seed gives the same result on different machines. The second run
was started on the development server and completed on a second machine; jobs that both machines computed
themselves were compared rule by rule with `paper/compare_machines.py` (no new simulation). Copied job files
and reused rows are not counted.

| Job | Rule runs | Numeric fields | Count fields | Count fields differing | Largest absolute difference | Largest relative difference |
|---|---|---|---|---|---|---|
| T1_grid_d150_veh16_s9002_cho | 32 | 1984 | 832 | 0 | 8.9e-14 | 3.5e-15 |

All count fields are equal; the remaining differences of real-valued fields are at the level of floating-point rounding.
Only these jobs were computed independently on both machines; the 45 T2 jobs present on both consist of reused rows only.
