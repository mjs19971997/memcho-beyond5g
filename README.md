# MemCHO: place-keyed outcome memory for conditional handover

Simulator, study plan, scripts and results of the article

> M. Jalili Sanjarani, Y. Elmi Sola, H. Hasanpour, A. A. Neghabi, *Place-keyed outcome memory for conditional handover in ultra-dense beyond-5G networks*.

MemCHO is a controller for 3GPP Release-16 conditional handover (CHO). For every 10 m square of the reported
position and every direction of travel it counts how earlier handovers decided there ended (useful, unnecessary, too
early or to the wrong cell, too late), combines these counts with the overlap of the user's predicted path with each
neighbour, and sets per user and candidate cell the preparation threshold and the execution offset that the
conditional configuration already carries. With all weights at zero it is standard CHO.

The study simulates Release-16 procedures under beyond-5G conditions (10 GHz carrier, sites every 50 to 150 m along
the streets of an urban grid after 3GPP TR 37.885, reduced to 2 x 2 blocks). It is not a 6G simulation.

## Results in brief

Two full runs are included. In the first (`results/full`, 2,382 jobs) the tuned A3 and CHO settings sat at the top of
their tuning grids. The second (`results/full_ext`, 1,638 jobs; amendment 2 of `PLAN.md`) widened those two grids and
retuned A3 and CHO with the same budget of 48 settings; rows of unchanged rules were reused. The article reports the
second run. MemCHO against tuned CHO, relative change of the pooled means:

| Environment | Pairs | Unnecessary handovers | Failures | Mean prepared cells | Unnecessary handovers, first run |
|---|---|---|---|---|---|
| Street grid, chi = 0.3 (main test) | 360 | +52.8 % | -88.9 % | -21.7 % | -19.7 % |
| Street grid, chi = 1 (added after the pilot) | 180 | -16.6 % | -58.6 % | +85.2 % | -36.1 % |
| Open area (nothing tied to place) | 90 | +620.1 % | -66.7 % | +15.5 % | +22.3 % |

* Main test: tuned CHO has fewer unnecessary handovers than MemCHO, also at every equal-failure level of stage S2
  (MemCHO 52.8 to 61.6 % more). The main hypothesis (fewer unnecessary handovers than tuned CHO) is rejected.
* MemCHO is a low-failure operating point: -88.9 % failures against CHO (-46.2 % without the 100 m
  deployment, where the tuned CHO setting exceeded its failure budget on the test seeds) and -77.2 % against A3, a
  21.7 % smaller prepared set, 2.9 % more delivered rate, 1.6 times the measurement reports.
* Without beam isolation (chi = 1) the memory lowers unnecessary handovers and failures together, at the cost of more
  prepared cells. In the open area it does not help with unnecessary handovers.
* The first run had shown -19.7 % unnecessary handovers for MemCHO against CHO; the difference came from the
  under-tuned baseline. `results/full_ext/EXT_COMPARE.md` compares the two runs setting by setting.
* Still at the top of the widened grid: the CHO setting at 100 m in the main street grid (preparation offset +4 dB,
  execution time-to-trigger 1.28 s) and in the open area (execution offset 16 dB). MemCHO's own base execution offset
  (8 dB) is at the top of its grid, which was not widened.
* The handover and unnecessary-handover rates of the simulator were compared with ns-3 / 5G-LENA
  (`calibration_report.txt`); its failure rates are not calibrated. CHO is not available in ns-3 / 5G-LENA, so MemCHO
  itself has no confirmation in a standard simulator.

All jobs of both runs finished; none failed. Rows of unchanged rules in the second run were reused from the first; jobs that the
development server and the second machine computed independently agree to floating-point rounding (`results/DETERMINISM.md`). Note: the first line of `results/full_ext/analysis/report.txt` calls the
design a test because `analyze.py` labels every design other than `full` that way; `full_ext` is the full study with
widened baseline grids.

## Contents

| Path | What it is |
|---|---|
| `bh6/` | the system-level simulator (layout, path loss, radio, mobility, engine, handover rules, study design) |
| `PLAN.md` | the study plan, written before any tuned comparison; changes after it, with dates and reasons, in its section 12 |
| `LITERATURE.md` | the literature scan behind the claims of novelty |
| `run_checks.py`, `checks_report.txt` | checks before the runs (geometry, path loss by hand, statistics, determinism, equivalences) |
| `calibrate_ns3.py`, `calibration_report.txt`, `calibration.json` | comparison with ns-3 / 5G-LENA; reference runs in `ns3_reference/` |
| `run_all.py`, `analyze.py` | the study (all stages, resumable) and its analysis |
| `results/full/` | first run: analysis report (`report.txt`, `report.json`), `runs.csv` (one row per run and rule), tuning tables, frozen settings, `jobs.zip` |
| `results/full_ext/` | run with widened baseline grids: the same files, `EXT_COMPARE.md`, and the per-attempt event logs of the main test, seeds 1-10 (`events/S1`) |
| `paper/` | scripts that compute every number, figure and table of the article from the files above |

To run `analyze.py` again, unpack `jobs.zip` into the folder next to it.

## Installation

Python 3.12 with the packages of `requirements.txt` (NumPy, SciPy, Matplotlib). The checks of the compiled manuscript
(`paper/check_tex.py`) also need PyMuPDF (`pip install pymupdf`). The LaTeX manuscript is generated with Node.js 20 and
compiled with tectonic or pdfLaTeX. PyTorch is optional (`requirements-torch.txt`) and not needed for anything here.

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
| Fig. 4, Table 5 (main test) | `p3_figs.py fig_main`, `build_p3.js` | `results/full_ext/analysis/runs.csv` via `derive.py` |
| Fig. 5 (per condition) | `p3_figs.py fig_conditions` | `report.json` (`S1_percell`, `X3_percell`) |
| Fig. 6 (failure causes) | `p3_figs.py fig_causes` | `runs.csv` |
| Fig. 7 (equal failure rate) | `p3_figs.py fig_frontier` | `report.json` (`S2_front`) |
| Fig. 8 (memory over time) | `p3_figs.py fig_time` | `results/full_ext/events/S1` via `derive.py` |
| Fig. 9 (sensitivities) | `p3_figs.py fig_sens` | `report.json` (`S3`), `runs.csv` |
| Table 2 (evaluation practice, 2026 papers) | `build_p3.js` | `paper/data/survey_2026.csv` |
| Tables 3, 4 (parameters, methods) | `build_p3.js` | `bh6/params.py`, `bh6/study.py`, `report.json` |
| Tables 6, 7 (hypotheses, environments) | `build_p3.js` | `results/full_ext/analysis/report.json` |
| Table 8 (before and after) | `build_p3.js` | `report.json` of both runs |

Table 1 (related work) is written by hand in `build_p3.js`; the references are in `refs3.js`, and
`paper/refcheck/` holds the Crossref records used to check them.

## Re-running the study

```
python run_checks.py            # checks before the runs -> checks_report.txt
python calibrate_ns3.py         # comparison with ns-3 -> calibration_report.txt, calibration.json
python run_all.py --smoke       # a few minutes, end to end
python run_all.py               # the first full run, resumable; --workers N, --status
python run_all.py --design full_ext   # amendment 2: A3 and CHO retuned on the widened grids, other rows reused from results/full
python analyze.py --design full_ext
```

The first run took 265 hours of job time and the second 52 hours (sums over parallel workers), on
CPU with NumPy. Runs are deterministic: the same seed gives identical event logs.

## Citation and licence

See `CITATION.cff`. The code is released under the MIT licence (`LICENSE`). An archived release with a DOI will follow.
