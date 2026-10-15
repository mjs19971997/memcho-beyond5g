# MemCHO: conditional handover steered by a place-keyed memory of handover outcomes

Simulator, study plan, scripts and results of the article

> M. Jalili Sanjarani, Y. Elmi Sola, H. Hasanpour, A. A. Neghabi, *Conditional handover steered by a place-keyed memory of handover outcomes in ultra-dense upper mid-band street networks*.

MemCHO is a controller for 3GPP Release-16 conditional handover (CHO). For every 10 m square of the reported
position and every direction of travel it counts how earlier handovers decided there ended (useful, unnecessary, too
early or to the wrong cell, too late), combines these counts with the overlap of the user's predicted path with each
neighbour, and sets per user and candidate cell the preparation threshold and the execution offset that the
conditional configuration already carries. With all weights at zero it is standard CHO.

The study simulates Release-16 procedures under beyond-5G conditions (10 GHz carrier, sites every 50 to 150 m along
the streets of the 3GPP TR 37.885 urban grid). It is not a 6G simulation.

## Results in brief

Main test: 360 paired runs (9 conditions x 40 seeds, 600 UE-minutes each), every method tuned with the same
budget of 48 settings. MemCHO against tuned CHO, relative change of the pooled means:

| Environment | Pairs | Unnecessary handovers | Failures | Mean prepared cells |
|---|---|---|---|---|
| Street grid, chi = 0.3 (main test) | 360 | -19.7 % | -57.3 % | +36.1 % |
| Street grid, chi = 1 (added after the pilot) | 180 | -36.1 % | -28.4 % | +55.9 % |
| Open area (nothing tied to place) | 90 | +22.3 % | -10.7 % | +62.7 % |

* Against tuned A3 in the main test: -38.0 % unnecessary handovers, -66.9 % failures.
* Delivered share of the demanded rate 1.0 % higher than CHO; 2.2 times as many measurement reports.
* At equal failure rate (all 48 tuned settings on 12 test seeds): 20 to 29 % fewer unnecessary
  handovers than CHO.
* Negative findings: the hypothesis of a smaller preparation overhead is rejected (more prepared cells, more reports);
  the per-user margin rule without CHO has 30.3 % more unnecessary handovers than A3; the execution-offset-only
  ablation has fewer unnecessary handovers than the full scheme (0.264 vs 0.319 per UE-minute), which
  keeps more delivered rate and loses fewer configurations; with no place-tied shadowing the gain reverses
  (+17.7 % unnecessary handovers against CHO).
* The beam isolation chi = 0.3 and the in-street obstacles were set in the design phase, after a first untuned run
  showed no failures at all (`PLAN.md`, section 11); chi = 0.1 and 1 and no obstacles are sensitivities.
* The handover and unnecessary-handover rates of the simulator were compared with ns-3 / 5G-LENA
  (`calibration_report.txt`); its failure rates are not calibrated. CHO is not available in ns-3 / 5G-LENA, so MemCHO
  itself has no confirmation in a standard simulator.

All 2,382 jobs of the study finished; none failed (`results/full/run_all.log`).

## Contents

| Path | What it is |
|---|---|
| `bh6/` | the system-level simulator (layout, path loss, radio, mobility, engine, handover rules, study design) |
| `PLAN.md` | the study plan, written before any tuned comparison; changes after it are listed in its section 12 |
| `LITERATURE.md` | the literature scan behind the claims of novelty |
| `run_checks.py`, `checks_report.txt` | checks before the runs (geometry, path loss by hand, statistics, determinism, equivalences) |
| `calibrate_ns3.py`, `calibration_report.txt`, `calibration.json` | comparison with ns-3 / 5G-LENA; reference runs in `ns3_reference/` |
| `run_all.py`, `analyze.py` | the study (all stages, resumable) and its analysis |
| `results/full/analysis/` | `report.txt` and `report.json` (all tables and tests), `runs.csv` (one row per run and rule), tuning tables, overview figures |
| `results/full/jobs.zip` | the result file of every job; unpack into `results/full/` to run `analyze.py` again |
| `results/full/events/S1/` | per-attempt event logs of the main test, seeds 1-10 (the other event logs are not included, about 46 MB) |
| `results/full/tuned_*.json` | the frozen settings selected by tuning |
| `paper/` | scripts that compute every number, figure and table of the article from the files above |

## Installation

Python 3.12 with the packages of `requirements.txt` (NumPy, SciPy, Matplotlib). The checks of the compiled manuscript
(`paper/check_tex.py`) also need PyMuPDF (`pip install pymupdf`).
The LaTeX manuscript is generated with Node.js 20 and compiled with tectonic or pdfLaTeX. PyTorch is optional
(`requirements-torch.txt`) and not needed for anything here.

```
pip install -r requirements.txt
```

## Reproducing the figures and tables of the article

```
cd paper
python derive.py        # numbers not printed in report.json (confidence intervals, time windows, survey counts) -> data/p3.json
python p3_figs.py       # all figures -> figures/*.pdf, *.png
node build_p3.js out/MemCHO_B5G.tex     # the manuscript text; stops if a statement is no longer supported by the results
bash build_p3.sh        # all of the above, compiled and checked (tools from PATH or PY, NODE, TECTONIC)
```

| Item of the article | Drawn by | From |
|---|---|---|
| Fig. 1 (scheme) | `p3_figs.py fig_scheme` | drawing |
| Fig. 2 (street grid, place bins) | `p3_figs.py fig_scenario` | `bh6/layout.py`, `bh6/mobility.py` |
| Fig. 3 (calibration) | `p3_figs.py fig_calib` | `calibration.json` |
| Fig. 4, Table 5 (main test) | `p3_figs.py fig_main`, `build_p3.js` | `runs.csv` via `derive.py` |
| Fig. 5 (per condition) | `p3_figs.py fig_conditions` | `report.json` (`S1_percell`, `X3_percell`) |
| Fig. 6 (failure causes) | `p3_figs.py fig_causes` | `runs.csv` |
| Fig. 7 (equal failure rate) | `p3_figs.py fig_frontier` | `report.json` (`S2_front`) |
| Fig. 8 (memory over time) | `p3_figs.py fig_time` | `events/S1` via `derive.py` |
| Fig. 9 (sensitivities) | `p3_figs.py fig_sens` | `report.json` (`S3`), `runs.csv` |
| Table 2 (evaluation practice, 2026 papers) | `build_p3.js` | `paper/data/survey_2026.csv` |
| Tables 3, 4 (parameters, methods) | `build_p3.js` | `bh6/params.py`, `bh6/study.py`, `report.json` |
| Tables 6, 7 (hypotheses, environments) | `build_p3.js` | `report.json` |

Table 1 (related work) is written by hand in `build_p3.js`; the references are in `refs3.js`, and
`paper/refcheck/` holds the Crossref records used to check them.

## Re-running the study

```
python run_checks.py            # checks before the runs -> checks_report.txt
python calibrate_ns3.py         # comparison with ns-3 -> calibration_report.txt, calibration.json
python run_all.py --smoke       # a few minutes, end to end
python run_all.py               # the full study, resumable; --workers N, --status
python analyze.py               # -> results/full/analysis/
```

The full study took 265 hours of job time in total (sum over parallel workers),
on CPU with NumPy. Runs are deterministic: the same seed gives identical event logs.

## Citation and licence

See `CITATION.cff`. The code is released under the MIT licence (`LICENSE`). An archived release with a DOI will follow.
