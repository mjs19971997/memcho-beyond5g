# -*- coding: utf-8 -*-
"""The study: designs, methods and their tuning spaces, stages and jobs.

Everything that PLAN.md fixes in advance is coded here and nowhere else: which
conditions are simulated, which settings each method may take, how many
settings each method gets (the same number for all), how a setting is selected
and which seeds are used for tuning and for the test.

A *job* is one simulated world (condition + seed) with a list of rules that
all run on the same radio samples.  A job writes one JSON file; a stage is a
list of jobs.  Stages in order of importance:

    T1  tuning, round 1 (random settings)            street grid
    T2  tuning, round 2 (refinement around the best) street grid
    S1  main test with the frozen settings           street grid
    O1  tuning, round 1                              open area (no place-tied blockage)
    O2  tuning, round 2                              open area
    O3  test with the frozen settings                open area
    X1  tuning, round 1                              street grid without beam isolation (chi = 1)
    X2  tuning, round 2                              the same
    X3  test with the frozen settings                the same  (X stages: added after the pilot, see PLAN.md)
    S2  all tuned settings on test seeds (comparison at equal failure rate)
    S3  sensitivities with the frozen settings
"""
import gzip
import json
import os
import random
import time
import traceback

from .params import Scenario

STAGES = ("T1", "T2", "S1", "O1", "O2", "O3", "X1", "X2", "X3", "S2", "S3")
TUNE_STAGE = {("grid", 1): "T1", ("grid", 2): "T2", ("open", 1): "O1", ("open", 2): "O2", ("gridx", 1): "X1", ("gridx", 2): "X2"}
TEST_STAGE = {"S1": "grid", "O3": "open", "X3": "gridx"}
MAIN = ("a3", "pum", "cho", "memcho")
ABLATIONS = ("mc_exec", "mc_prep", "mc_mem", "mc_mot", "mc_pair")
REF_A3 = dict(rule="a3", off=3.0, ttt=0.16, name="a3@ref")     # reference that sets the failure budget
STRICT = 0.25                                                    # strict budget = this share of the standard one
EVENT_SEEDS = 10                                                 # per-event logs are kept for test seeds 1..10
UHO_TOL = 0.05                                                   # settings within 5 % of the best UHO count as equal

# ----------------------------------------------------------------------------
# designs
# ----------------------------------------------------------------------------
DESIGNS = {
    # the study as planned (PLAN.md)
    "full": dict(t_sim=660.0, discard=60.0, n_ue=60, isds=(50, 100, 150), profiles=("ped", "veh8", "veh16"),
                 n1=32, n2=16, val_seeds=(9001, 9002), test_seeds=tuple(range(1, 41)),
                 open_isds=(100,), open_test_seeds=tuple(range(1, 31)), x_test_seeds=tuple(range(1, 21)),
                 front_seeds=tuple(range(1, 13)), sens_seeds=tuple(range(1, 13)),
                 sens_cells=((100, "veh16"), (100, "ped"), (50, "veh16")), ablations=ABLATIONS, long_t=1980.0),
    # preliminary answer on the development server (13 October 2026): street grid at 100 m, both interference
    # settings, the four main methods, reduced tuning (18 instead of 48 settings, 3 validation traces), 7 test seeds.
    # A size option only: rules, labels, environment and selection are those of the full design.
    "prelim": dict(t_sim=360.0, discard=60.0, n_ue=60, isds=(100,), profiles=("ped", "veh8", "veh16"),
                   n1=12, n2=6, val_seeds=(9001,), test_seeds=tuple(range(1, 8)),
                   open_isds=(100,), open_test_seeds=(1,), x_test_seeds=tuple(range(1, 8)),
                   front_seeds=(1,), sens_seeds=(1,), sens_cells=((100, "veh16"),), ablations=(), long_t=360.0,
                   stages=("T1", "T2", "S1", "X1", "X2", "X3")),
    # small version run on the development server to show that everything works and to size the study
    "pilot": dict(t_sim=150.0, discard=30.0, n_ue=40, isds=(100,), profiles=("ped", "veh16"),
                  n1=10, n2=4, val_seeds=(9001,), test_seeds=(1, 2, 3),
                  open_isds=(100,), open_test_seeds=(1, 2), x_test_seeds=(1, 2),
                  front_seeds=(1,), sens_seeds=(1,), sens_cells=((100, "veh16"),), ablations=("mc_mem", "mc_mot"),
                  long_t=300.0, sens_only=("chi100", "noclutter", "place0", "pos15")),
    # a few minutes on the target machine: every stage and the analysis run once
    "smoke": dict(t_sim=60.0, discard=10.0, n_ue=20, isds=(100,), profiles=("veh16",),
                  n1=4, n2=2, val_seeds=(9001,), test_seeds=(1, 2),
                  open_isds=(100,), open_test_seeds=(1, 2), x_test_seeds=(1, 2),
                  front_seeds=(1,), sens_seeds=(1,), sens_cells=((100, "veh16"),), ablations=("mc_mem",),
                  long_t=90.0, sens_only=("chi100", "pos15")),
}

# ----------------------------------------------------------------------------
# methods and tuning spaces (declared before any run)
# ----------------------------------------------------------------------------
_CHO = dict(o_prep=(-6.0, -4.0, -2.0, 0.0), o_exec=(0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0),
            ttt_exec=(0.0, 0.04, 0.08, 0.16, 0.32), n_max=(1, 2, 4), rel_hys=(2.0, 4.0))
_W = dict(w_u=(0.0, 4.0, 8.0, 12.0), w_l=(0.0, 4.0, 8.0), w_a=(0.0, 2.0, 4.0))
_V = dict(v_u=(0.0, 4.0, 8.0), v_l=(0.0, 4.0, 8.0), v_a=(0.0, 2.0, 4.0))

METHODS = {
    "a3": dict(rule="a3", label="A3 handover",
               grid=dict(off=(0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0), ttt=(0.0, 0.04, 0.08, 0.16, 0.24, 0.32, 0.48, 0.64))),
    "pum": dict(rule="pum", label="per-user margin (5G rule)",
                grid=dict(h0=(0.0, 1.0, 2.0, 3.0, 4.0), ttt=(0.04, 0.08, 0.16, 0.32), eta_h=(0.0, 4.0, 8.0, 14.0),
                          eta_l=(0.0, 4.0, 8.0), eta_a=(0.0, 2.0, 4.0, 8.0), cap=(6.0, 9.0, 12.0))),
    "cho": dict(rule="cho", label="conditional handover", grid=dict(_CHO)),
    "memcho": dict(rule="memcho", label="memory- and motion-steered CHO", grid=dict(_CHO, **_W, **_V)),
    # ablations of the scheme under study, each tuned with the same budget
    "mc_exec": dict(rule="memcho", label="execution offsets only", grid=dict(_CHO, **_W)),
    "mc_prep": dict(rule="memcho", label="preparation only", grid=dict(_CHO, **_V)),
    "mc_mem": dict(rule="memcho", label="memory only (no motion)",
                   grid=dict(_CHO, w_u=_W["w_u"], w_l=_W["w_l"], v_u=_V["v_u"], v_l=_V["v_l"])),
    "mc_mot": dict(rule="memcho", label="motion only (no memory)", grid=dict(_CHO, w_a=_W["w_a"], v_a=_V["v_a"])),
    "mc_pair": dict(rule="memcho", label="cell-pair memory (no place)", grid=dict(_CHO, **_W, **_V), fixed=dict(place=False)),
}

# sensitivity variants: scenario overrides, or overrides of the memcho rule ("rule")
SENS = {
    "fc7": dict(sc=dict(radio__fc_ghz=7.0)), "fc15": dict(sc=dict(radio__fc_ghz=15.0)),
    "chi010": dict(sc=dict(radio__chi=0.10)), "chi100": dict(sc=dict(radio__chi=1.0)),
    "noclutter": dict(sc=dict(clutter=False)),
    "place50": dict(sc=dict(radio__place_share=0.5)), "place0": dict(sc=dict(radio__place_share=0.0)),
    "dyn3": dict(sc=dict(radio__sigma_t=3.0)), "meas2": dict(sc=dict(radio__meas_sigma=2.0)),
    "prep20": dict(sc=dict(proto__t_prep=0.02)), "prep100": dict(sc=dict(proto__t_prep=0.10)),
    "t310_05": dict(sc=dict(proto__t310=0.5)), "t310_2": dict(sc=dict(proto__t310=2.0)),
    "reest03": dict(sc=dict(proto__t_reest=0.3)),
    "veh30": dict(sc=dict(profile="veh30")), "mix": dict(sc=dict(profile="mix")),
    "ue30": dict(sc=dict(n_ue=30)), "ue120": dict(sc=dict(n_ue=120)),
    "hot50": dict(sc=dict(load__hot_frac=0.5)),
    "pos5": dict(rule=dict(pos_err=5.0)), "pos15": dict(rule=dict(pos_err=15.0)), "head05": dict(rule=dict(head_err=0.5)),
    "long": dict(sc=dict(t_sim="long_t")),
}


def base_scenario(design, env):
    """Scenario shared by all jobs of a design in one environment."""
    d = DESIGNS[design]
    sc = Scenario(name=env, env="open" if env == "open" else "grid", n_ue=d["n_ue"], t_sim=d["t_sim"], discard=d["discard"])
    if env == "open":
        sc = sc.with_(radio__place_share=0.0)      # nothing repeatable by place: shadowing and LOS state follow the user
    elif env == "gridx":
        sc = sc.with_(radio__chi=1.0)              # no beam isolation: interference as for wide control beams
    return sc


def make_scenario(design, env, over):
    d = DESIGNS[design]
    over = {k: (d[v] if k == "t_sim" and isinstance(v, str) else v) for k, v in over.items()}
    return base_scenario(design, env).with_(**over)


# ----------------------------------------------------------------------------
# settings of a method
# ----------------------------------------------------------------------------
def _spec(method, cfg, name):
    m = METHODS[method]
    return dict(rule=m["rule"], name=name, **cfg, **m.get("fixed", {}))


def _key(cfg):
    return tuple(sorted(cfg.items()))


def round1(method, n):
    """The first ``n`` settings of a method: a seeded random sample of its grid without repetition."""
    grid = METHODS[method]["grid"]
    rng = random.Random("round1-" + method)
    size = 1
    for v in grid.values():
        size *= len(v)
    out, seen = [], set()
    while len(out) < min(n, size):
        cfg = {k: rng.choice(v) for k, v in grid.items()}
        if _key(cfg) not in seen:
            seen.add(_key(cfg))
            out.append(cfg)
    return out


def round2(method, best, taken, n, tag):
    """``n`` new settings around ``best``: one grid step along one coordinate, then along two."""
    grid = METHODS[method]["grid"]
    rng = random.Random("round2-%s-%s" % (method, tag))
    seen = {_key(c) for c in taken}
    names = sorted(grid)

    def moves(cfg):
        res = []
        for k in names:
            i = grid[k].index(cfg[k])
            for j in (i - 1, i + 1):
                if 0 <= j < len(grid[k]):
                    res.append(dict(cfg, **{k: grid[k][j]}))
        return res
    one = moves(best)
    rng.shuffle(one)
    two = [c2 for c in one for c2 in moves(c)]
    rng.shuffle(two)
    out = []
    for c in one + two:
        if len(out) >= n:
            break
        if _key(c) not in seen:
            seen.add(_key(c))
            out.append(c)
    return out


def select(cands, budget):
    """Pre-registered selection among tuned settings.

    ``cands``: dicts with ``uho``, ``fail``, ``prep`` (validation means) in a
    fixed order.  Among the settings whose failure rate does not exceed
    ``budget``, those within 5 % of the lowest UHO rate are equal on UHO; among
    them the lowest prepared-cell overhead wins, then the lowest failure rate,
    then the lowest UHO rate, then the order.  If no setting meets the budget,
    the lowest failure rate wins.  Returns ``(index, met_budget)``.
    """
    ok = [i for i, c in enumerate(cands) if c["fail"] <= budget + 1e-12]
    if not ok:
        return min(range(len(cands)), key=lambda i: (cands[i]["fail"], cands[i]["uho"], i)), False
    best = min(cands[i]["uho"] for i in ok)
    near = [i for i in ok if cands[i]["uho"] <= best * (1.0 + UHO_TOL) + 1e-12]
    return min(near, key=lambda i: (round(cands[i]["prep"], 9), cands[i]["fail"], cands[i]["uho"], i)), True


# ----------------------------------------------------------------------------
# result files
# ----------------------------------------------------------------------------
def job_path(outdir, job):
    return os.path.join(outdir, "jobs", job["stage"], job["id"] + ".json")


def load_job(outdir, job):
    try:
        with open(job_path(outdir, job), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _tuning_table(outdir, jobs):
    """Validation means per (isd, method, setting name) over the traces; None if a job is missing."""
    acc = {}
    for j in jobs:
        r = load_job(outdir, j)
        if r is None:
            return None
        for spec, res in zip(j["specs"], r["results"]):
            a = acc.setdefault((j["isd"], j["method"], spec["name"]), dict(spec=spec, n=0, uho=0.0, fail=0.0, prep=0.0, ho=0.0))
            a["n"] += 1
            a["uho"] += res["uho_pm"]; a["fail"] += res["fail_pm"]; a["prep"] += res["prep_mean"]; a["ho"] += res["att_pm"]
    for a in acc.values():
        for k in ("uho", "fail", "prep", "ho"):
            a[k] /= a["n"]
    return acc


def tuned_path(outdir, env):
    return os.path.join(outdir, "tuned_%s.json" % env)


def methods_of(design, env):
    return MAIN + (tuple(DESIGNS[design]["ablations"]) if env == "grid" else ())


def isds_of(design, env):
    d = DESIGNS[design]
    return d["open_isds"] if env == "open" else d["isds"]


def _tune_jobs(design, env, rnd, outdir):
    """Tuning jobs of one round; round 2 needs the results of round 1."""
    d = DESIGNS[design]
    stage = TUNE_STAGE[(env, rnd)]
    jobs = []
    tab1 = None
    if rnd == 2:
        tab1 = _tuning_table(outdir, _tune_jobs(design, env, 1, outdir))
        if tab1 is None:
            return None
    for isd in isds_of(design, env):
        for method in methods_of(design, env):
            first = round1(method, d["n1"])
            if rnd == 1:
                specs = [_spec(method, c, "%s/%02d" % (method, i)) for i, c in enumerate(first)]
                if method == "a3":
                    specs.append(dict(REF_A3))
            else:
                budget = tab1[(isd, "a3", REF_A3["name"])]["fail"]
                cands = [tab1[(isd, method, "%s/%02d" % (method, i))] for i in range(len(first))]
                i_best, _ = select(cands, budget)
                new = round2(method, first[i_best], first, d["n2"], "%s-%s" % (env, isd))
                specs = [_spec(method, c, "%s/r2-%02d" % (method, i)) for i, c in enumerate(new)]
            if not specs:
                continue
            for prof in d["profiles"]:
                for seed in d["val_seeds"]:
                    jobs.append(dict(id="%s_%s_d%d_%s_s%d_%s" % (stage, env, isd, prof, seed, method), stage=stage, env=env,
                                     isd=isd, profile=prof, seed=seed, method=method, variant="",
                                     sc=dict(isd=float(isd), profile=prof, seed=seed), specs=specs, events=False))
    return jobs


def tuned(design, env, outdir, write=True):
    """Frozen settings per site distance, method and budget; None until both tuning rounds are complete."""
    j1 = _tune_jobs(design, env, 1, outdir)
    j2 = _tune_jobs(design, env, 2, outdir)
    if j2 is None:
        return None
    tab = _tuning_table(outdir, j1 + j2)
    if tab is None:
        return None
    out = dict(_selection="lowest UHO within the failure budget; within 5 % of it the lowest prepared-cell overhead, "
                          "then the lowest failure rate; if no setting meets the budget, the lowest failure rate",
               _reference=REF_A3, _strict_share=STRICT, isd={})
    for isd in isds_of(design, env):
        ref = tab[(isd, "a3", REF_A3["name"])]
        budgets = dict(std=ref["fail"], strict=STRICT * ref["fail"])
        node = dict(budget=budgets, reference=dict(uho=ref["uho"], fail=ref["fail"], ho=ref["ho"]), methods={})
        for method in methods_of(design, env):
            names = sorted(k[2] for k in tab if k[0] == isd and k[1] == method and k[2] != REF_A3["name"])
            cands = [tab[(isd, method, n)] for n in names]
            mnode = dict(settings=[dict(name=n, uho=c["uho"], fail=c["fail"], prep=c["prep"], ho=c["ho"],
                                        spec={k: v for k, v in c["spec"].items() if k not in ("name",)})
                                   for n, c in zip(names, cands)])
            for b, val in budgets.items():
                i, met = select(cands, val)
                mnode[b] = dict(name=names[i], met_budget=met, n_meeting=sum(c["fail"] <= val + 1e-12 for c in cands),
                                uho=cands[i]["uho"], fail=cands[i]["fail"], prep=cands[i]["prep"], ho=cands[i]["ho"],
                                spec=dict(cands[i]["spec"]))
            node["methods"][method] = mnode
        out["isd"][str(isd)] = node
    if write:
        tmp = tuned_path(outdir, env) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
        os.replace(tmp, tuned_path(outdir, env))
    return out


def _frozen(tn, isd, methods, budgets=("std", "strict"), rule_over=None):
    specs = [dict(REF_A3)]
    for m in methods:
        for b in budgets:
            s = dict(tn["isd"][str(isd)]["methods"][m][b]["spec"])
            s["name"] = "%s@%s" % (m, b)
            if rule_over and s["rule"] == "memcho":
                s.update(rule_over)
            specs.append(s)
    return specs


def stage_jobs(stage, design, outdir):
    """Jobs of a stage, or None if an earlier stage it depends on is not complete."""
    d = DESIGNS[design]
    for (env, rnd), st in TUNE_STAGE.items():
        if st == stage:
            return _tune_jobs(design, env, rnd, outdir)
    env = TEST_STAGE.get(stage, "grid")
    tn = tuned(design, env, outdir)
    if tn is None:
        return None
    jobs = []
    if stage in TEST_STAGE:
        seeds = d[{"S1": "test_seeds", "O3": "open_test_seeds", "X3": "x_test_seeds"}[stage]]
        for isd in isds_of(design, env):
            specs = _frozen(tn, isd, methods_of(design, env))
            for prof in d["profiles"]:
                for seed in seeds:
                    jobs.append(dict(id="%s_%s_d%d_%s_s%d" % (stage, env, isd, prof, seed), stage=stage, env=env, isd=isd,
                                     profile=prof, seed=seed, method="", variant="",
                                     sc=dict(isd=float(isd), profile=prof, seed=seed), specs=specs,
                                     events=seed <= EVENT_SEEDS))
    elif stage == "S2":
        for isd in d["isds"]:
            for method in MAIN:
                specs = []
                for s in tn["isd"][str(isd)]["methods"][method]["settings"]:
                    specs.append(dict(s["spec"], name=s["name"]))
                for prof in d["profiles"]:
                    for seed in d["front_seeds"]:
                        jobs.append(dict(id="S2_grid_d%d_%s_s%d_%s" % (isd, prof, seed, method), stage=stage, env=env, isd=isd,
                                         profile=prof, seed=seed, method=method, variant="",
                                         sc=dict(isd=float(isd), profile=prof, seed=seed), specs=specs, events=False))
    elif stage == "S3":
        names = [v for v in SENS if v in d.get("sens_only", SENS)]
        for var in names:
            v = SENS[var]
            cells = []
            for isd, prof in d["sens_cells"]:
                if isd not in d["isds"]:
                    continue
                over = dict(isd=float(isd), profile=prof)
                over.update(v.get("sc", {}))
                if (isd, over["profile"]) not in [(c[0], c[1]["profile"]) for c in cells]:
                    cells.append((isd, over))
            for isd, over in cells:
                specs = _frozen(tn, isd, MAIN, budgets=("std",), rule_over=v.get("rule"))
                for seed in d["sens_seeds"]:
                    jobs.append(dict(id="S3_%s_d%d_%s_s%d" % (var, isd, over["profile"], seed), stage=stage, env=env, isd=isd,
                                     profile=over["profile"], seed=seed, method="", variant=var,
                                     sc=dict(over, seed=seed), specs=specs, events=False))
    else:
        raise ValueError(stage)
    return jobs


def planned_count(stage, design):
    """Number of jobs and rule-runs of a stage (known before anything has run)."""
    d = DESIGNS[design]
    nv = len(d["profiles"]) * len(d["val_seeds"])
    if stage[0] in "TOX" and stage[1] in "12":
        env = {"T": "grid", "O": "open", "X": "gridx"}[stage[0]]
        groups = len(isds_of(design, env)) * len(methods_of(design, env))
        per = d["n1"] if stage[1] == "1" else d["n2"]
        return groups * nv, groups * nv * per + (len(isds_of(design, env)) * nv if stage[1] == "1" else 0)
    if stage == "S1":
        n = len(d["isds"]) * len(d["profiles"]) * len(d["test_seeds"])
        return n, n * (1 + 2 * len(methods_of(design, "grid")))
    if stage == "O3":
        n = len(d["open_isds"]) * len(d["profiles"]) * len(d["open_test_seeds"])
        return n, n * (1 + 2 * len(MAIN))
    if stage == "X3":
        n = len(d["isds"]) * len(d["profiles"]) * len(d["x_test_seeds"])
        return n, n * (1 + 2 * len(MAIN))
    if stage == "S2":
        n = len(d["isds"]) * len(d["profiles"]) * len(d["front_seeds"]) * len(MAIN)
        return n, n * (d["n1"] + d["n2"])
    if stage == "S3":
        n = 0
        for var in [v for v in SENS if v in d.get("sens_only", SENS)]:
            cells = set()
            for isd, prof in d["sens_cells"]:
                if isd in d["isds"]:
                    cells.add((isd, SENS[var].get("sc", {}).get("profile", prof)))
            n += len(cells) * len(d["sens_seeds"])
        return n, n * (1 + len(MAIN))
    raise ValueError(stage)


# ----------------------------------------------------------------------------
# running one job (called in a worker process)
# ----------------------------------------------------------------------------
def run_job(job, design, outdir, device="auto"):
    """Run one job and write its result file.  Returns ``(job id, error text or None, seconds)``."""
    t0 = time.perf_counter()
    try:
        from .backend import choose_ops
        from .engine import EVENT_FIELDS
        from .sim import run_rules
        sc = make_scenario(design, job["env"], job["sc"])
        timing = {}
        res, engines = run_rules(sc, job["specs"], ops=choose_ops(device), log_events=job.get("events", False), timing=timing)
        path = job_path(outdir, job)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if job.get("events"):
            edir = os.path.join(outdir, "events", job["stage"])
            os.makedirs(edir, exist_ok=True)
            tmp = os.path.join(edir, job["id"] + ".csv.gz.tmp")
            with gzip.open(tmp, "wt", encoding="utf-8", newline="") as f:
                f.write("rule," + ",".join(EVENT_FIELDS) + "\n")
                for spec, e in zip(job["specs"], engines):
                    if spec["name"].endswith("@std") and spec["name"].split("@")[0] in MAIN:
                        for row in e.log:
                            f.write(spec["name"] + "," + ",".join(str(x) for x in row) + "\n")
            os.replace(tmp, tmp[:-4])
        meta = {k: job[k] for k in ("id", "stage", "env", "isd", "profile", "seed", "method", "variant", "sc")}
        out = dict(job=meta, names=[s["name"] for s in job["specs"]], results=res, timing=timing,
                   scenario=sc.to_dict(), wall_s=time.perf_counter() - t0)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(out, f)
        os.replace(path + ".tmp", path)
        return job["id"], None, time.perf_counter() - t0
    except Exception:
        return job["id"], traceback.format_exc(), time.perf_counter() - t0
