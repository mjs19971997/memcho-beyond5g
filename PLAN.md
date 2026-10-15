# Study plan: handover control in ultra-dense upper-mid-band networks

Written on 12 October 2026, **before any tuned comparison of the methods was run**. Section 11
lists everything that had been looked at by then. The plan is coded in `bh6/study.py`; if code and
plan disagree, that is an error to be reported, not silently fixed.

Wording rule for every write-up: the study simulates 3GPP Rel-16 procedures under conditions
expected beyond 5G (upper mid-band carrier, ultra-dense sites). It does not simulate "6G"; no such
standard exists.

## 1. Research question

In ultra-dense upper-mid-band street deployments (carrier 7-15 GHz, site distance 50-150 m,
blockage tied to place), margin-based handover trades unnecessary handovers against late-handover
failures. Conditional handover (CHO) removes the late command but costs prepared cells and can
execute into poor targets.

**Question.** Can a memory of handover outcomes keyed by place, together with the motion of the
user, decide per user and per neighbour which cells to prepare and with which execution offset, so
that unnecessary handovers, failures and preparation overhead fall together against a tuned
standard CHO? And under which conditions does this stop working?

The literature scan (`LITERATURE.md`) narrowed the claim: selecting CHO candidates by prediction,
adapting CHO parameters from past outcomes and location-keyed handover parameters each exist. What
was not found is the combination, its joint effect on the three quantities, and a procedure-level
evaluation in this deployment.

## 2. Hypotheses

Premises (checked first; if they fail, the question changes and this is reported):

* **P1.** For the baseline-handover rules (A3, per-user margin) most failures are late ones
  (command lost, link failure during preparation, link failure without a handover): more than half
  of all failures, pooled over the main test.
* **P2.** The per-user margin of the earlier 5G work, tuned under the same budget as A3, has fewer
  unnecessary handovers than A3 and not fewer failures.
* **P3.** At equal failure rate (stage S2), standard CHO has fewer unnecessary handovers than A3,
  with a mean prepared set above zero.

Main hypothesis (confirmatory, stage S1, standard budget, all conditions pooled, paired by seed):

* **H1.** The memory- and motion-steered CHO ("MemCHO") against tuned standard CHO has
  (a) fewer unnecessary handovers per UE-minute,
  (b) a failure rate that is not higher: upper end of the 95 % interval of the difference below
      0.2 x the mean failure budget of the three site distances,
  (c) a smaller mean prepared set.
  "Fall together" needs (a), (b) and (c). Each is reported separately; the three p-values are
  Holm-corrected. If only some hold, that is the result.

Secondary (reported with tests, not part of the main claim):

* **H2.** MemCHO has fewer unnecessary handovers than each of its ablations (section 4) at the
  standard budget.
* **H3.** The same comparisons at the strict budget.
* **H4.** Interruption time and delivered rate of MemCHO are not worse than those of CHO.

Boundary (direction stated in advance, stage O3 and S3):

* **B1.** In the open area, where nothing is tied to place, MemCHO has no advantage in unnecessary
  handovers over CHO (interval of the difference includes zero or favours CHO).
* **B2.** The advantage shrinks when the place-tied share of the shadowing goes to zero, when the
  reported position is wrong by 15 m, and for pedestrians.

Everything else in S3 is exploratory.

## 3. Simulator (what is modelled, what is abstracted)

`bh6/` is a system-level simulator in Python; details in the module docstrings.

Modelled:
* Geometry: urban grid of TR 37.885 Annex A (blocks 433 m x 250 m, streets 20 m), 2 x 2 blocks,
  4.1 km of street; sites on the pavement every 50 / 100 / 150 m along every street (79 / 40 / 26
  sites), 10 m high; users follow the streets and turn at intersections (0.5 / 0.25 / 0.25).
* Path loss: TR 38.901 UMi street canyon, LOS and NLOS, at 10 GHz (7 and 15 GHz as sensitivity).
  The formulas are specified for 0.5-100 GHz; their basis in 7-24 GHz is weaker and was
  re-examined in Rel-19, and measurements at 6.75 and 16.95 GHz deviate in part. Results are
  therefore model results.
* Blockage tied to place: (i) buildings: a link is blocked if the straight line crosses a building
  block; (ii) obstacles inside the street ("clutter"): the spatially consistent LOS state of
  TR 38.901 clause 7.6.3.3 (random field, 50 m correlation distance, UMi LOS probability), fixed
  per place and site; (iii) a static shadowing field per site (4 dB LOS / 7.82 dB NLOS, 10 m
  decorrelation, correlation 0.5 between sites), shared by all users.
* Not tied to place: a time-varying component (1.5 dB, 1 s) and the error of an L1 sample (1 dB);
  optionally a share of the shadowing as a process along each user's own path (`place_share`).
* Measurement chain: L1 sample every 40 ms, L3 filter k = 4 with the time characteristic of the
  200 ms reference rate, Event A3 with time-to-trigger, reporting.
* Baseline handover: report, preparation 50 ms, command (lost if T310 is running when it arrives),
  execution 40 ms, target check.
* Conditional handover (Rel-16): reporting event, preparation by the network, prepared set with a
  size limit, release, conditional configuration (lost if T310 is running), execution condition
  evaluated by the UE per prepared cell with its own offset, release of the other cells after
  execution, faster recovery into a prepared cell after a failure.
* Failures: Qout -8 dB over 200 ms, Qin -6 dB over 100 ms, N310 = N311 = 1, T310 = 1 s,
  re-establishment 1 s (0.4 s into a prepared cell).
* Load-coupled interference as in the group's earlier simulator: background load per cell
  (25 % hotspot cells), service rates of the users, interference of a cell proportional to its load.
* Outcome label of every attempt (useful, unnecessary, too early, wrong cell, too late, censored)
  and cause of every failure; per-event logs.

Abstracted, and said so in every write-up:
* Antennas: one number for the beam gain (20 dB) towards served and measuring users, one number
  for the isolation of interfering beams (`chi` = 0.3, about -5 dB). No beam management, beam
  failure, panels or SSB sweeps. `chi` is an assumption: beams in a street point along the street,
  so isolation between users of the same street is limited; 0.1 and 1.0 are run as sensitivities.
* No fast fading, no HARQ, no RACH failure model, no uplink, no core-network signalling.
* The label SINR assumes all cells transmit; it is a property of the radio environment and does
  not depend on what a rule does to the load.
* The memory is fed with observable quantities only (reports, dwell time, failure type, reported
  position), but the report of a position is assumed available; its error is a sensitivity.
* One carrier, outdoor users only, 60 users.

## 4. Methods compared

| Key | Method | What is tuned |
|---|---|---|
| `a3` | baseline handover, Event A3 | offset, time-to-trigger |
| `pum` | per-user, per-neighbour A3 margin of the earlier 5G work (history of the cell pair, late term, path overlap) | base offset, TTT, three weights, cap |
| `cho` | standard conditional handover, fixed offsets | preparation offset, execution offset, execution TTT, prepared-set limit, release hysteresis |
| `memcho` | CHO whose preparation offset and execution offset are shifted per user and neighbour by place memory and path overlap | CHO parameters plus six weights |
| `mc_exec` | ablation: execution offsets only | |
| `mc_prep` | ablation: preparation only | |
| `mc_mem` | ablation: memory only, no motion | |
| `mc_mot` | ablation: motion only, no memory (trajectory-style preparation, as in prior work) | |
| `mc_pair` | ablation: memory per cell pair, no place | |

With all weights zero `memcho` is exactly `cho`, and `pum` is exactly `a3` (checked on event logs).
A reference A3 (3 dB, 160 ms) runs in every tuning and test job; it only defines the failure budget.

## 5. Conditions and factors

Main conditions (street grid, 10 GHz): site distance 50 / 100 / 150 m x mobility pedestrian
(1.2-1.8 m/s) / vehicle 8 m/s / vehicle 16 m/s = 9 conditions. 60 users, runs of 660 s with the
first 60 s discarded (600 UE-minutes per run). The memory starts empty in every run and learns
during it, the discarded minute included.

Open area (boundary condition): same rectangle, no buildings, hexagonal sites at 100 m, LOS state
and shadowing as processes along each user's path (nothing repeatable by place), random-waypoint
motion; own tuning, three mobility profiles.

Sensitivities (frozen standard-budget settings; conditions 100 m / 16 m/s, 100 m / pedestrian,
50 m / 16 m/s): carrier 7 and 15 GHz; isolation 0.1 and 1.0; no clutter; place-tied share of the
shadowing 0.5 and 0; time-varying component 3 dB; L1 error 2 dB; preparation 20 and 100 ms; T310
0.5 and 2 s; re-establishment 0.3 s; 30 m/s; mixed population; 30 and 120 users; half of the cells
hotspots; position error 5 and 15 m; heading error 0.5 rad; runs three times as long.

## 6. Fair tuning

* Tuning is done per site distance (an operator tunes a deployment, not a speed class), on
  validation traces: 3 mobility profiles x 2 seeds (9001, 9002), never used in a test.
* **Equal budget:** every method, the ablations included, gets 48 settings: 32 drawn at random
  (seeded) from its declared grid (`bh6/study.py`, `METHODS`), then 16 around the best of the first
  round (one grid step along one or two coordinates). The scheme under study has the largest grid
  and the same 48 settings, which is a handicap for it, not an advantage.
* **Failure budget:** the failure rate of the reference A3 on the validation traces of that site
  distance ("standard"); one quarter of it ("strict").
* **Selection, automatic:** among the settings within the budget, those within 5 % of the lowest
  unnecessary-handover rate count as equal; among them the lowest prepared-cell overhead, then the
  lowest failure rate. If none meets the budget, the lowest failure rate. The selected settings
  are frozen (`tuned_grid.json`, `tuned_open.json`) before the test stages start.
* The validation tables of all 48 settings per method go into the report, so the selection can be redone.

## 7. Stages (order = importance)

| Stage | Content | Jobs | Rule-runs |
|---|---|---|---|
| T1, T2 | tuning, street grid: 3 site distances x 9 methods x 6 traces, 32 + 16 settings | 324 | 7 794 |
| S1 | main test: 9 conditions x 40 seeds (1-40), 9 methods x 2 budgets + reference | 360 | 6 840 |
| O1, O2, O3 | open area: tuning of the 4 main methods; test 3 profiles x 30 seeds | 138 | 1 968 |
| X1, X2, X3 | street grid without beam isolation (chi = 1), added after the pilot (section 12): tuning of the 4 main methods at 3 site distances; test 9 conditions x 20 seeds | 324 | 5 094 |
| S2 | all 48 settings of the 4 main methods on test seeds 1-12, 9 conditions | 432 | 20 736 |
| S3 | 23 sensitivities x up to 3 conditions x 12 seeds, 4 main methods + reference | 804 | 4 020 |
| | total | 2 382 | 46 452 |

A rule-run is one rule on one simulated world (660 s). All rules of a job run on the same radio
samples. Every stage is reported, whatever it shows; a stage that could not be run is reported as
not run. Failed jobs are listed with their error and are not replaced by other seeds.

## 8. Endpoints

Primary, per UE-minute of the measured part:
1. unnecessary handovers (label of section 3);
2. mobility failures, total and by cause (command lost; link failure during preparation; link
   failure without handover, with or without a prepared cell; execution failure; link failure in
   the target inside the window; coverage failure);
3. prepared-cell overhead: mean size of the prepared set (prepared-cell seconds per UE-second),
   preparations per UE-minute, unused preparations, lost configurations, measurement reports;
4. interruption time (execution gaps plus re-establishment outages, seconds per UE-minute);
5. delivered rate (share of the demanded rate, Mbit/s per user).

The label of "unnecessary" is the one of the group's earlier studies and is kept unchanged: the
attempt completed, the source would not have failed during the window, and the stay was shorter
than T_min of the service (2-7 s) or the mean SINR gain was below theta_Q (0.4-1.5 dB). With cells
of 50-150 m many stays are short by geometry, so the level of this rate depends on the definition.
Two alternative definitions are reported next to it as robustness, not as replacements: short
**and** low gain; ping-pong in the sense of TR 36.839 (back to the previous cell within 1 s).

## 9. Statistics

* Unit: one run (condition x seed). Methods are paired by seed: same sites, map, trajectories,
  noise.
* Test: exact two-sided Wilcoxon signed-rank test on the paired differences (zeros dropped, ties
  with mid-ranks). Estimate: mean paired difference with a 95 % t interval, and the relative
  change of the pooled means. Pooled over all conditions and per condition.
* Confirmatory: P1-P3 and H1 on S1/S2 (Holm over H1 a-c). Secondary: H2-H4. Boundary: B1, B2.
  Exploratory: everything else in S3, the per-condition tables, the time-window analysis of the
  memory, the alternative labels.
* S2 comparison at equal failure rate: for each method the setting with the lowest unnecessary-
  handover rate among those whose pooled failure rate on the S2 seeds does not exceed a level,
  for a fixed list of levels; the paired difference between methods at each level. Because the
  setting is chosen on the same seeds, this stage is descriptive support for S1, not a second
  confirmatory test.
* Printed rates use decimal rounding, half away from zero.
* No seed, condition or job is dropped for its result. Negative and null results are reported
  with the same weight as positive ones.

## 10. Checks before the runs (results in `checks_report.txt`, `calibration_report.txt`)

1. Geometry: site placement, six line-of-sight cases by hand, map lookup against direct
   computation, trajectories inside streets at constant speed, turn statistics.
2. Path loss against hand computation (c = 299 792 458 m/s, h_E = 1 m):
   * UMi LOS, 10 GHz, d2D 50 m, h_BS 10 m, h_UT 1.5 m: d3D = sqrt(2500 + 72.25) = 50.7174 m,
     log10 = 1.705157; d'_BP = 4 x 9 x 0.5 x 10^10 / c = 600.4 m, so PL1 = 32.4 + 21 x 1.705157 + 20
     = 88.208 dB.
   * UMi NLOS, same link: 35.3 x 1.705157 + 22.4 + 21.3 = 103.892 dB (larger than LOS, so it is the result).
   * UMi LOS, 3.5 GHz, 200 m: d3D = 200.1805 m, log10 = 2.301422; d'_BP = 210.1 m; PL1 = 32.4 +
     48.3299 + 10.8814 = 91.611 dB.
   * UMi LOS, 3.5 GHz, 400 m (beyond the breakpoint): log10(d3D) = 2.602158; PL2 = 32.4 + 104.0863
     + 10.8814 - 9.5 x log10(210.145^2 + 72.25) = 147.3677 - 44.1346 = 103.233 dB.
   * UMa LOS / NLOS, 3.5 GHz, 100 m, h_BS 25 m: d3D = 102.7241 m, log10 = 2.011673; LOS 28 +
     44.2568 + 10.8814 = 83.138 dB; NLOS 13.54 + 78.6162 + 10.8814 = 103.038 dB.
   * UMi LOS probability at 100 m: 0.18 + exp(-100/36) x 0.82 = 0.2310.
3. Radio statistics: standard deviation and correlation of the shadowing field, share of
   unobstructed in-street links against the LOS probability, time-varying part, L1 error, L3 filter.
4. Determinism: same seed, identical event logs; other seed, different logs.
5. Conservation: attempts = sum of outcomes; failures = sum of causes; preparations = lost +
   cancelled + used + unused + open.
6. Equivalences on event logs: per-user margin with zero weights = A3; MemCHO with zero weights =
   CHO; CHO with immediate execution, one prepared cell and "lost configuration = lost command" =
   A3 (three settings).
7. Calibration: the ns-3 / 5G-LENA urban scenario of the group (3.5 GHz, 7 sites, 20 vehicles)
   rebuilt in this simulator; handover, unnecessary-handover and failure rates of the 24 A3
   settings and of the test settings compared with `i9_full2/campaign_urban`. Agreement and
   disagreement are reported as found; the simulator is not tuned to the ns-3 numbers.

## 11. What had been seen when this plan was written

* Design runs of the simulator itself. A first 120 s run (one seed, arbitrary untuned settings of
  A3, per-user margin, CHO and MemCHO side by side) with isolation 0.1 and without clutter gave
  no failure for any rule. A study of a failure trade-off is pointless under that condition, so
  two environment assumptions were changed before anything else: isolation 0.1 -> 0.3 (reason in
  section 3) and in-street obstacles after TR 38.901 were added. A second 80 s run with the same
  arbitrary settings then showed failures of the baseline rules (about 0.1 per UE-minute, mostly
  late commands) and almost none for CHO. These two runs are the only side-by-side numbers seen;
  no setting was tuned and no weight of MemCHO was chosen from them. The tuning grids of section 6
  were written afterwards and are wide on purpose.
* The checks of section 10 (items 1-6) and the calibration (item 7, A3 only, 3.5 GHz).
* From the earlier ns-3 work (5G rules, not this study): in the street grid the per-user margin
  cut unnecessary handovers by 37 % and tripled failures, 94 % of them late commands; and a 14 s
  smoke run at 10 GHz with 100 m site distance (one seed, untuned).
* Not seen: any tuning result, any test result, any open-area or sensitivity result.

## 12. Pilot and full run

A pilot (`run_all.py --pilot`: one site distance, two profiles, 150 s runs, 14 settings per method,
three test seeds) is run on the development server only to show that all stages work and to
measure the run time. **Pilot numbers are not results** and do not enter the manuscript. The size
of the study (run length, number of seeds) is set from the measured run times of the pilot, before
its outcome tables are opened. Apart from that the plan is not changed after the pilot, except to
correct an error, and any such correction is listed here with its date.

Changes after the plan was first written:
* 12 October 2026, sizing only, decided from the pilot's run times and a timing probe, before the
  pilot's analysis report was opened: run length 420 s -> 660 s (600 instead of 360 UE-minutes per
  run), S2 test seeds 1-8 -> 1-12. Reason: the first size would have used only about half of the
  available machine time. Nothing else was changed.
* 12 October 2026, **amendment 1, made after the pilot's outcome tables were read**: stages X1-X3
  added. What prompted it: in the pilot (street grid, 100 m, isolation 0.3) the reference A3 had
  almost no failures (0.017 per UE-minute in 480 UE-minutes, none on the validation traces), so
  the failure budget hardly constrained any method, while the research question is about a
  trade-off against failures. This is an observation about the environment and the baseline, not
  about the difference between MemCHO and CHO. X1-X3 repeat tuning and test of the four main
  methods in the same street grid with `chi` = 1 (no isolation of interfering beams, as for
  radio-link monitoring on wide control beams; the ns-3 smoke run at 10 GHz with omni-directional
  antennas was of this kind). The X stages are **not** part of H1, which stays on S1 as planned;
  they are reported in full, with the note that they were added after the pilot. The planned
  sensitivity `chi100` (settings frozen at isolation 0.3) stays as it is. The supervisor may drop
  the amendment (`run_all.py --only T1,T2,S1,O1,O2,O3,S2,S3`); if it is run, it is reported.
* Seen in the pilot besides this (three test seeds, 150 s runs, one site distance; not results):
  MemCHO had fewer unnecessary handovers than CHO in the street grid but the interval included
  zero, and a larger, not a smaller, prepared set; in the open area it had no advantage. None of
  this changed a hypothesis, a grid, a selection rule or an endpoint.
* 13 October 2026, **preliminary run on the development server** (`run_all.py --design prelim`,
  results in `results/prelim/`), asked for by the student to get an early indication. Size option
  only: street grid, 100 m site distance, isolation 0.3 and 1 (stages T1, T2, S1, X1, X2, X3), the
  four main methods, 18 instead of 48 settings per method, 3 validation traces (one seed), 7 test
  seeds x 3 mobility profiles = 21 pairs per interference setting, runs of 360 s with 60 s
  discarded. Rules, labels, environment assumptions and the selection rule are those of this plan.
  It is not the study: its numbers do not enter the manuscript as results and no hypothesis,
  grid, endpoint or stage of this plan was changed because of it.
