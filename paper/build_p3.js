// Third paper: MemCHO, conditional handover steered by a place-keyed outcome memory.
// Every number in the text, the tables and the captions is read from the result files of the finished study
// (results/full_i9/results/full/analysis/report.json) or from data/p3.json (derive.py, which reads runs.csv, the
// event logs, the calibration and the table of 2026 papers).  Each qualitative statement that depends on a result
// is guarded by a check that stops the build if the result no longer supports it.
//
//     node build_p3.js <out.tex>          single column;   P3_COLS=2 node build_p3.js <out_2col.tex>  two-column preview
//     P3_JOURNAL="Journal of Network and Computer Applications" switches the journal (p3_tex.js holds the default).
const fs = require('fs');
const path = require('path');
const K = require('./p3_tex');
const { c, F, TB, E, SEC, P, L, H, Hsub, fig, EQ, table, push, frontmatter, build, JOURNAL } = K;
const { rfix } = require('./round_dec');


const HERE = __dirname;
const ANA = [path.join(HERE, '..', 'results', 'full', 'analysis'), path.join(HERE, '..', 'results', 'full_i9', 'results', 'full', 'analysis')].find((p) => fs.existsSync(p));
const R = JSON.parse(fs.readFileSync(path.join(ANA, 'report.json'), 'utf8').replace(/\bNaN\b/g, 'null'));
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'data', 'p3.json'), 'utf8'));
const REFS = require('./refs3');
K.setRefs(REFS);

// ---------------------------------------------------------------- helpers
const must = (cond, msg) => { if (!cond) throw new Error('claim no longer supported by the results: ' + msg); };
const fx = (x, d = 2) => rfix(x, d);
const ab = (x, d = 1) => rfix(Math.abs(x), d);                       // magnitude of a change, for "fewer"/"more"
const ng = (x, d = 2) => rfix(x, d).replace('-', '−');                // signed number with a typographic minus
const sg = (x, d = 1) => { const a = rfix(Math.abs(x), d); return (parseFloat(a) === 0 ? '' : x >= 0 ? '+' : '−') + a; };
const pv = (p) => (p < 0.001 ? '$p$ < 0.001' : `$p$ = ${fx(p, 3)}`);
const pvc = (p) => (p < 0.001 ? '< 0.001' : fx(p, 3));
const nf = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
const cmp = (st, a, b, k, bud = 'std') => {
  const q = R[`${st}_cmp_${bud}`][`${a}@${bud}|${b}@${bud}|${k}`];
  if (!q) throw new Error(`no comparison ${st} ${a} ${b} ${k}`);
  return q;
};
const ci = (st, rule, k) => D.ci[`${st}|${rule}`][k];
const mean = (st, rule, k) => ci(st, rule, k).mean;
const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'];
const word = (n) => (n < WORDS.length ? WORDS[n] : String(n));
const Word = (n) => { const w = word(n); return w[0].toUpperCase() + w.slice(1); };

// ---------------------------------------------------------------- numbers used throughout
const H1 = R.S1_H1;
const uC = H1.uho, fC = H1.fail, pC = H1.prep;
const uA = cmp('S1', 'memcho', 'a3', 'uho_pm'), fA = cmp('S1', 'memcho', 'a3', 'fail_pm');
const dC = cmp('S1', 'memcho', 'cho', 'delivered'), iC = cmp('S1', 'memcho', 'cho', 'int_s_pm');
const repM = mean('S1', 'memcho@std', 'reports_pm'), repC = mean('S1', 'cho@std', 'reports_pm');
const repRatio = repM / repC;
const pumA = cmp('S1', 'pum', 'a3', 'uho_pm'), pumAf = cmp('S1', 'pum', 'a3', 'fail_pm');
const choA = cmp('S1', 'cho', 'a3', 'uho_pm'), choAf = cmp('S1', 'cho', 'a3', 'fail_pm');
const xU = R.X3_H1.uho, xF = R.X3_H1.fail, xP = R.X3_H1.prep;
const oU = R.O3_H1.uho, oF = R.O3_H1.fail, oP = R.O3_H1.prep;
const LEV = ['0.25', '0.5', '1.0', '2.0'];
const eqf = LEV.map((l) => R.S2_equal_failure[`${l}|memcho|cho`]);
const eqLo = Math.min(...eqf.map((q) => Math.abs(q.rel_pct))), eqHi = Math.max(...eqf.map((q) => Math.abs(q.rel_pct)));
const S3 = R.S3, SV = Object.keys(S3);
const s3uLow = SV.filter((v) => S3[v].uho_pm.rel_pct < 0), s3uHigh = SV.filter((v) => S3[v].uho_pm.rel_pct > 0);
const s3uSig = SV.filter((v) => S3[v].uho_pm.ci_hi < 0), s3uSigHigh = SV.filter((v) => S3[v].uho_pm.ci_lo > 0);
const s3fLow = SV.filter((v) => S3[v].fail_pm.diff < 0), s3fSig = SV.filter((v) => S3[v].fail_pm.ci_hi < 0);
const B3 = D.s3_base;
const W = D.windows.rate, Wm = W['memcho@std'], Wc = W['cho@std'];
const wDropM = 100 * (Wm[Wm.length - 1] - Wm[0]) / Wm[0], wDropC = 100 * (Wc[Wc.length - 1] - Wc[0]) / Wc[0];
const T3 = R.windows;
const exM = mean('S1', 'mc_exec@std', 'uho_pm'), mcM = mean('S1', 'memcho@std', 'uho_pm');
const exCfg = mean('S1', 'mc_exec@std', 'cfg_lost_pm'), mcCfg = mean('S1', 'memcho@std', 'cfg_lost_pm');
const exDel = mean('S1', 'mc_exec@std', 'delivered'), mcDel = mean('S1', 'memcho@std', 'delivered');
const memEx = cmp('S1', 'memcho', 'mc_exec', 'uho_pm'), memMem = cmp('S1', 'memcho', 'mc_mem', 'uho_pm');
const P1a = R.S1_P1_a3, P1p = R.S1_P1_pum;
const CAL = D.calib.summary;
const SC = D.scenario, DS = D.design, MC = D.memcho_const;
const nJobs = Object.values(R.completeness.done).reduce((a, b) => a + b, 0);
const nPairs = uC.n, nX = xU.n, nO = oU.n;
const SVY = D.survey;
const budStd = (d) => R.tuning_grid[String(d)].budget.std;
const sel = (d, m, b = 'std') => R.tuning_grid[String(d)].methods[m][b];
const SITES = D.sites;
const ueMinRun = DS.n_ue * (DS.t_sim - DS.discard) / 60;

// ---------------------------------------------------------------- guards on every qualitative claim
must(R.completeness.failed.length === 0 && nJobs === 2382, 'all 2382 jobs finished, none failed');
must(uC.rel_pct < 0 && uC.ci_hi < 0 && uC.p < 0.001, 'MemCHO fewer unnecessary handovers than CHO (H1a)');
must(fC.rel_pct < 0 && fC.ci_hi < 0, 'MemCHO fewer failures than CHO');
must(fC.ci_hi < H1.margin, 'H1(b) holds: upper end below the margin');
must(pC.rel_pct > 0 && pC.ci_lo > 0, 'H1(c) rejected: more prepared cells');
must(uA.rel_pct < 0 && fA.rel_pct < 0 && uA.ci_hi < 0 && fA.ci_hi < 0, 'MemCHO fewer UHO and failures than A3');
must(dC.rel_pct > 0 && dC.ci_lo > 0, 'delivered rate higher than CHO');
must(iC.ci_hi < 0, 'interruption lower than CHO');
must(repRatio > 1.8 && repRatio < 2.5, 'measurement reports about twice those of CHO');
must(pumA.rel_pct > 0 && pumA.ci_lo > 0, 'per-user margin has more UHO than A3');
must(pumAf.rel_pct < 0, 'per-user margin has fewer failures than A3');
must(xU.ci_hi < 0 && xF.ci_hi < 0 && xP.ci_lo > 0, 'chi = 1: fewer UHO and failures, more prepared cells');
must(oU.ci_lo > 0 && oF.ci_hi < 0 && oP.ci_lo > 0, 'open area: more UHO, fewer failures, more prepared cells');
must(eqf.every((q) => q.ci_hi < 0), 'equal failure level: MemCHO fewer UHO than CHO at every level');
must(s3fLow.length === SV.length, 'failures lower in all sensitivities (point estimate)');
must(s3uLow.length > SV.length / 2, 'UHO lower in most sensitivities');
must(S3.place0.uho_pm.ci_lo > 0 && S3.place50.uho_pm.ci_lo > 0, 'gain reverses without place-tied shadowing');
must(S3.place0.uho_pm.rel_pct > S3.place50.uho_pm.rel_pct, 'reversal larger with no place share than with half');
must(S3.place0.fail_pm.ci_hi < 0 && S3.place50.fail_pm.ci_hi < 0, 'failures still lower without place-tied shadowing');
must(SV.length === 23, '23 sensitivity variants');
must(wDropM < -10 && Math.abs(wDropC) < 5, 'MemCHO improves over the run, CHO flat');
must(T3['memcho@std'][0] > T3['memcho@std'][1] && T3['memcho@std'][1] > T3['memcho@std'][2], 'thirds decrease for MemCHO');
must(exM < mcM && memEx.ci_lo > 0, 'execution-only ablation has fewer UHO than the full scheme');
must(exCfg > mcCfg && exDel < mcDel && cmp('S1', 'memcho', 'mc_exec', 'delivered').ci_lo > 0, 'full scheme: fewer lost configurations, higher delivered rate than execution-only');
must(memMem.ci_lo > 0 && cmp('S1', 'memcho', 'mc_mem', 'fail_pm').ci_hi < 0, 'memory-only: fewer UHO but more failures than full scheme');
must(P1a.late / P1a.failures > 0.5 && P1p.late / P1p.failures > 0.5, 'P1 holds');
must(CAL.ho_spearman > 0.95 && CAL.uho_spearman > 0.95 && CAL.fail_mean_ns3 > 2 * CAL.fail_mean_sim, 'calibration: rates follow ns-3, failures do not');
must(['50', '100', '150'].every((d) => ['a3', 'cho'].every((m) => sel(d, m).spec[m === 'a3' ? 'off' : 'o_exec'] === 8)), 'tuned A3 and CHO offsets at the top of the grid');
must(Math.max(...D.grids.cho.grid.o_exec) === 8 && MC.O_HI === 12, 'grid edge 8 dB, MemCHO bound 12 dB');
must(COND_PED_WORSE(), 'pedestrian conditions: MemCHO slightly more UHO than CHO');
function COND_PED_WORSE() { return ['50', '100', '150'].every((d) => R.S1_percell[`${d}|ped|uho_pm`].ci_lo > 0); }
must(SVY.n === 15 && SVY.test === 0, 'survey: 15 papers, none with a statistical test');

// ---------------------------------------------------------------- equations
K.setEqs({
  prep: String.raw`F_{n}(t)-F_{s}(t)\;\ge\;O_{\mathrm{prep}}(u,n,t)`,
  exec: String.raw`F_{n}(t')-F_{s}(t')\;>\;O_{\mathrm{exec}}(u,n)\qquad\text{for all } t'\in[t-T_{\mathrm{exec}},\,t]`,
  unn: { w: String.raw`I_{\mathrm{un}}=1\iff\text{completed}\;\wedge\;\text{no failure of the source in the window}\;\wedge\;\bigl(T_{\mathrm{stay}}<T_{\min}^{s}\;\vee\;\Delta\bar{\gamma}<\theta_{Q}^{s}\bigr)`,
    n: String.raw`\begin{aligned}I_{\mathrm{un}}=1\iff{}&\text{completed}\;\wedge\;\text{no source failure in the window}\\&\wedge\;\bigl(T_{\mathrm{stay}}<T_{\min}^{s}\;\vee\;\Delta\bar{\gamma}<\theta_{Q}^{s}\bigr)\end{aligned}` },
  forget: String.raw`N\;\leftarrow\;N\,e^{-\Delta t/\tau}`,
  pair: { w: String.raw`\mathrm{bad}_{c}(s,n)=\frac{N_{\mathrm{U}}+N_{\mathrm{E}}+\kappa_{0}\,\bar{b}}{N_{\mathrm{ok}}+\kappa_{0}},\qquad \mathrm{late}_{c}(s,n)=\frac{N_{\mathrm{L}}}{N_{\mathrm{ok}}+N_{\mathrm{L}}+\kappa_{0}},\qquad \bar{b}=\frac{G_{\mathrm{U}}+G_{\mathrm{E}}+1}{G_{\mathrm{Y}}+G_{\mathrm{U}}+G_{\mathrm{E}}+2}`,
    n: String.raw`\begin{gathered}\mathrm{bad}_{c}(s,n)=\frac{N_{\mathrm{U}}+N_{\mathrm{E}}+\kappa_{0}\,\bar{b}}{N_{\mathrm{ok}}+\kappa_{0}},\qquad \mathrm{late}_{c}(s,n)=\frac{N_{\mathrm{L}}}{N_{\mathrm{ok}}+N_{\mathrm{L}}+\kappa_{0}},\\ \bar{b}=\frac{G_{\mathrm{U}}+G_{\mathrm{E}}+1}{G_{\mathrm{Y}}+G_{\mathrm{U}}+G_{\mathrm{E}}+2}\end{gathered}` },
  place: { w: String.raw`\mathrm{bad}(b,n)=\frac{C_{\mathrm{U}}+C_{\mathrm{E}}+\kappa\,\mathrm{bad}_{c}(s,n)}{C_{\mathrm{ok}}+\kappa},\qquad \mathrm{late}(b,n)=\frac{C_{\mathrm{L}}+\kappa\,\mathrm{late}_{c}(s,n)}{C_{\mathrm{ok}}+C_{\mathrm{L}}+\kappa},\qquad \Delta\mathrm{bad}=\mathrm{bad}(b,n)-\bar{b}`,
    n: String.raw`\begin{gathered}\mathrm{bad}(b,n)=\frac{C_{\mathrm{U}}+C_{\mathrm{E}}+\kappa\,\mathrm{bad}_{c}(s,n)}{C_{\mathrm{ok}}+\kappa},\\ \mathrm{late}(b,n)=\frac{C_{\mathrm{L}}+\kappa\,\mathrm{late}_{c}(s,n)}{C_{\mathrm{ok}}+C_{\mathrm{L}}+\kappa},\qquad \Delta\mathrm{bad}=\mathrm{bad}(b,n)-\bar{b}\end{gathered}` },
  ovl: String.raw`\mathrm{ovl}(u,n)=\frac{|S_{u}\cap A_{n}|}{|S_{u}|}`,
  oprep: { w: String.raw`O_{\mathrm{prep}}(u,n)=\max\bigl\{o_{\mathrm{prep}}+v_{\mathrm{U}}\,\Delta\mathrm{bad}-v_{\mathrm{L}}\,\mathrm{late}-v_{\mathrm{A}}\,\mathrm{ovl},\;O_{\mathrm{rep}}\bigr\},\qquad O_{\mathrm{rep}}=o_{\mathrm{prep}}-\min\{v_{\mathrm{U}}+v_{\mathrm{L}}+v_{\mathrm{A}},\,${MC.REP_CAP}\ \mathrm{dB}\}`,
    n: String.raw`\begin{gathered}O_{\mathrm{prep}}(u,n)=\max\bigl\{o_{\mathrm{prep}}+v_{\mathrm{U}}\,\Delta\mathrm{bad}-v_{\mathrm{L}}\,\mathrm{late}-v_{\mathrm{A}}\,\mathrm{ovl},\;O_{\mathrm{rep}}\bigr\},\\ O_{\mathrm{rep}}=o_{\mathrm{prep}}-\min\{v_{\mathrm{U}}+v_{\mathrm{L}}+v_{\mathrm{A}},\,${MC.REP_CAP}\ \mathrm{dB}\}\end{gathered}` },
  oexec: { w: String.raw`O_{\mathrm{exec}}(u,n)=\min\Bigl\{\max\bigl\{o_{\mathrm{exec}}+w_{\mathrm{U}}\,\Delta\mathrm{bad}-w_{\mathrm{L}}\,\mathrm{late}-w_{\mathrm{A}}\,\mathrm{ovl},\;${MC.O_LO}\ \mathrm{dB}\bigr\},\;${MC.O_HI}\ \mathrm{dB}\Bigr\}`,
    n: String.raw`\begin{aligned}O_{\mathrm{exec}}(u,n)=\min\Bigl\{&\max\bigl\{o_{\mathrm{exec}}+w_{\mathrm{U}}\,\Delta\mathrm{bad}-w_{\mathrm{L}}\,\mathrm{late}-w_{\mathrm{A}}\,\mathrm{ovl},\\&\;${MC.O_LO}\ \mathrm{dB}\bigr\},\;${MC.O_HI}\ \mathrm{dB}\Bigr\}\end{aligned}` },
});

// ---------------------------------------------------------------- front matter
const TITLE = 'Conditional handover steered by a place-keyed memory of handover outcomes in ultra-dense upper mid-band street networks';
const ABSTRACT = `In ultra-dense street deployments of the upper mid-band, users cross a cell in seconds and blockage changes abruptly at corners and building edges. Conditional handover (CHO) removes the late handover command, but it still executes into cells that the user soon leaves again. We propose MemCHO, a CHO controller that counts, for every 10 m place and direction of travel, how earlier handovers decided there ended, combines these counts with the predicted path of the user, and sets per user and candidate cell both the preparation threshold and the execution offset that the Rel-16 conditional configuration already carries. We evaluated it in a procedure-level system simulation of a street grid at 10 GHz with sites every 50, 100 and 150 m, against A3 handover, a per-user margin rule and CHO, each tuned with the same budget of 48 settings. Over ${nPairs} paired runs MemCHO had ${ab(uC.rel_pct)}% fewer unnecessary handovers and ${ab(fC.rel_pct)}% fewer failures than tuned CHO (${ab(uA.rel_pct)}% and ${ab(fA.rel_pct)}% fewer than tuned A3), and a ${ab(dC.rel_pct)}% higher delivered rate. It needed ${ab(pC.rel_pct)}% more prepared cells and ${fx(repRatio, 1)} times as many measurement reports, so our hypothesis of lower preparation overhead was rejected. At equal failure rate the reduction against CHO was ${ab(eqLo, 0)}–${ab(eqHi, 0)}%. The gain grew as the memory filled and disappeared where blockage was not tied to place: in an open area MemCHO had ${ab(oU.rel_pct)}% more unnecessary handovers than CHO. Handover rates of the simulator agree with ns-3/5G-LENA; failure rates were not calibrated.`;
const KEYWORDS = ['Conditional handover', 'Mobility robustness', 'Unnecessary handover', 'Handover failure', 'Upper mid-band', 'Ultra-dense network', 'System-level simulation'];
const nWords = ABSTRACT.replace(/\$[^$]*\$/g, 'x').split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w)).length;
must(nWords <= 250, `abstract has ${nWords} words`);
const HIGHLIGHTS = [
  'A place-keyed memory of handover outcomes sets CHO candidates and offsets per user',
  `Against tuned CHO: ${ab(uC.rel_pct, 0)}% fewer unnecessary handovers, ${ab(fC.rel_pct, 0)}% fewer failures`,
  `The price: ${ab(pC.rel_pct, 0)}% more prepared cells and ${fx(repRatio, 1)} times the measurement reports`,
  `Open area, nothing tied to place: ${ab(oU.rel_pct, 0)}% more unnecessary handovers than CHO`,
  'All methods tuned with one budget; 2,382 simulation jobs; code and data are public',
];
HIGHLIGHTS.forEach((h) => must(h.length <= 85, `highlight longer than 85 characters (${h.length}): ${h}`));
must(HIGHLIGHTS.length >= 3 && HIGHLIGHTS.length <= 5, 'three to five highlights');
frontmatter(TITLE, ABSTRACT, KEYWORDS);

// ================================================================= 1 Introduction
push(H('intro', 'Introduction'));
push(P(`A street of an ultra-dense deployment in the upper mid-band (7–24 GHz) has a site every 50 to 150 m. A car at 60 km/h crosses such a cell in three to nine seconds, and the signal of a cell does not fade smoothly as it does in a macro network: it drops by tens of decibels when a building edge or a parked truck comes between user and site ${c('tr38901', 'kang')}. Two errors of handover control then become frequent. A handover may lead into a cell that the user leaves again before the move has paid off; we call it unnecessary. Or the handover may come too late, so that the command no longer reaches the user and the link fails. A larger handover margin removes some of the first kind and creates more of the second ${c('tayyab', 'arshad')}.`));
push(P(`Conditional handover (CHO), introduced in 3GPP Release 16, changes this trade-off ${c('ts38300', 'martikainen', 'stanczak')}. The network prepares candidate cells early and sends the user a conditional configuration with an execution condition for each candidate. The user executes on its own when a condition holds, so no command can arrive too late. CHO has two costs: the prepared cells occupy resources in the target cells and need signalling, and the execution condition is still a fixed offset, so CHO also executes into cells that will not hold the user for long ${c('martikainen', 'iqbal22')}. Much of the work on CHO since then has reduced the first cost, by predicting which cells the user will reach ${c('prado', 'lee', 'chomet')} or by keeping preparations across handovers ${c('iqbal22', 'iqbal23')}.`));
push(P(`In a street grid, much of what makes a handover go wrong is tied to a place: the same corner, the same building edge, the same direction of travel. A network can record where its handovers went wrong and use the record for the next user who reaches the same place in the same direction. The standard already has the means to act on such a record per user and per candidate cell: every candidate in a conditional configuration carries its own execution condition ${c('ts38331')}. In earlier work on 5G networks we reduced handovers with an ensemble-learning predictor ${c('jalili1')} and with a per-user margin for the baseline handover; this paper moves the idea to CHO and to the conditions expected beyond 5G.`));
push(P(`We propose MemCHO (${F('scheme')}). It keeps counts of how earlier handovers ended, for every 10 m square, direction of travel and target cell, and combines them with the overlap of the user's predicted path with each neighbour. From the two it sets, for each user and candidate, the threshold at which the cell is prepared and the execution offset written into the conditional configuration. The paper makes three contributions:`));
push(L([
  `The controller (${SEC('scheme')}). Selecting CHO candidates by prediction, adapting CHO parameters from past outcomes and keying handover parameters by location have each been studied before ${c('prado', 'sundararaju', 'awada')}. MemCHO combines them: a memory of outcome classes (unnecessary, too early or wrong cell, too late), keyed by place and heading, steers both the prepared set and the per-candidate execution offset. With all weights at zero it is standard CHO.`,
  `A procedure-level evaluation in an ultra-dense street grid at 10 GHz with sites every 50, 100 and 150 m (${SEC('setup')}): measurement chain, preparation delay, radio-link failure, failure causes and prepared-cell overhead, with every method tuned under the same budget, ${nf(nJobs)} simulation jobs, paired statistical tests and five ablations that separate the known ingredients. The plan and the hypotheses were written before any tuned comparison was run.`,
  `The conditions under which the memory stops helping, and a rejected hypothesis: MemCHO does not reduce the preparation overhead, it increases it (${SEC('results')}).`,
]));
push(P(`In the main test MemCHO had ${ab(uC.rel_pct)}% fewer unnecessary handovers and ${ab(fC.rel_pct)}% fewer failures than tuned CHO, but ${ab(pC.rel_pct)}% more prepared cells. In an open area, where nothing about blockage repeats at a place, it had more unnecessary handovers than CHO. We use "beyond-5G conditions" for what is simulated: Release-16 procedures with an upper mid-band carrier and ultra-dense sites. No 6G system is simulated, since none is specified. ${SEC('related')} reviews related work and how recent handover studies are evaluated, ${SEC('scheme')} describes MemCHO, ${SEC('setup')} the simulation study, ${SEC('results')} the results; the last three sections discuss them, state their limits and conclude.`));
push(fig('scheme', 'fig_scheme', `MemCHO at a glance. The source cell keeps outcome counts per 10 m place, heading quadrant and target cell, and a motion term from the predicted path. Both shift the preparation threshold $O_prep$ and the execution offset $O_exec$ per user and target; $O_exec$ travels in the Rel-16 conditional configuration, and the outcome of every attempt is written back under the place where it was decided.`, 165));

// ================================================================= 2 Related work
push(H('related', 'Related work'));
push(Hsub('rw-cho', 'Conditional handover and its cost'));
push(P(`Martikainen et al. ${c('martikainen')} described CHO and showed that it gains robustness but that its signalling can rise sharply when it is badly parameterised; they named self-optimisation of the CHO parameters as a remedy. Stanczak et al. ${c('stanczak')} found in FR2 system simulations that CHO removes most mobility failures of the Release-15 handover. Fast CHO keeps prepared cells after a handover and lowers both signalling and failures ${c('iqbal22')}; resource-reservation variants of it trade reservation time against failures under hand blockage ${c('iqbal23')}. Deb et al. ${c('deb')} showed with a Markov model that the best preparation and execution offsets depend on speed and fading, which argues against one offset for all users. Lower-layer triggered mobility of Release 18 is a different response to the same problem ${c('gundogan', 'khodapanah')}; we do not simulate it.`));
push(Hsub('rw-pred', 'Which cells to prepare, and with which offset'));
push(P(`ECHO ${c('prado')} predicts the trajectory with a sequence model and prepares one cell instead of three; its abstract reports fewer handovers, radio-link failures and control messages than CHO. Lee et al. ${c('lee')} predict the next cell from signal and blockage patterns so that fewer cells are prepared. CHOMET ${c('chomet')} decides online which cells to prepare from SINR, bandwidth and availability, trading rate against preparation signalling; its execution offsets are given, not learned. Closest to adapting the execution side is the Q-learning scheme of Sundararaju et al. ${c('sundararaju')}, in which the user learns handover parameters for CHO targets from current conditions and past handover results. Location as a key is older: Awada et al. ${c('awada')} set handover thresholds by the position of the user inside a cell and resolved failures that cell-level optimisation could not. Surveys of learning for handover cover many more schemes of these kinds ${c('mollel', 'tayyab')}.`));
push(P(`${TB('rw')} sets these works side by side. What we did not find, after searches on arXiv, Crossref and OpenAlex, is a controller that sets the prepared set and a per-candidate execution offset together from a place-keyed memory of outcome classes, and an evaluation of such a controller that reports unnecessary handovers, failures by cause and preparation overhead together in an ultra-dense upper mid-band deployment. The search did not include patents or the full text of every IEEE paper, so this is a statement about what we found.`));
push(table('rw', 'Prior work on steering conditional handover, compared with this paper. Entries are taken from the abstracts and, where available, the arXiv versions.',
  [1.25, 1.6, 1.7, 0.8, 1.65],
  ['Work', 'What is adapted', 'From what', 'Place-keyed', 'Setting evaluated'],
  [
    [`Martikainen et al. ${c('martikainen')}`, 'CHO principle; parameters discussed', '—', 'no', 'system simulation, 5G'],
    [`Iqbal et al. ${c('iqbal22', 'iqbal23')}`, 'keeping prepared cells after a handover', 'fixed rules', 'no', 'FR2, hand blockage'],
    [`Prado et al. (ECHO) ${c('prado')}`, 'prepared set', 'predicted trajectory', 'no', 'system simulation'],
    [`Lee et al. ${c('lee')}`, 'prepared set', 'predicted signal and blockage', 'no', 'mmWave'],
    [`Kalntis et al. (CHOMET) ${c('chomet')}`, 'prepared set (at most $J$ cells)', 'SINR, bandwidth, availability', 'no', 'online learning, given offsets'],
    [`Sundararaju et al. ${c('sundararaju')}`, 'handover parameters of CHO targets', 'current conditions, past results', 'not stated', '5G and beyond'],
    [`Deb et al. ${c('deb')}`, 'analysis of offsets and timers', 'speed, fading', 'no', 'Markov model'],
    [`Awada et al. ${c('awada')}`, 'handover thresholds (no CHO)', 'failures by position', 'yes', 'LTE inter-RAT'],
    [`Altmeyerhenzien et al. ${c('altmeyer')}`, '— (serving-site changes)', '—', 'no', 'FR3, ray tracing, macro sites'],
    '---',
    ['This paper (MemCHO)', 'prepared set and per-candidate execution offset', 'outcome classes by place and heading, path overlap', 'yes', '10 GHz street grid, 50–150 m sites, failure causes'],
  ], { left: [0, 1, 2, 4], hl: [10] }));

push(Hsub('rw-uppermid', 'Upper mid-band and ultra-dense networks'));
push(P(`Coverage and capacity of cellular networks in the upper mid-band have been studied in dense urban areas ${c('kang')}. Measurements at 6.75 and 16.95 GHz found path-loss exponents and spreads that differ in part from the 3GPP model ${c('shakya')}, and Release 19 re-examined TR 38.901 for 7–24 GHz ${c('poddar')}. The only mobility-related FR3 evaluation we found counts serving-site changes with ray tracing at eight macro sites ${c('altmeyer')}; it has no handover procedure, no failure model and no ultra-dense layout. Ultra-dense networks raise the handover rate in proportion to the site density, which led to handover skipping ${c('arshad')}.`));

// ---- 2.4 how 2026 studies evaluate
const survRows = SVY.rows;
const keyOf = (r) => {
  const id = r.url.replace(/^https?:\/\/(doi\.org\/|arxiv\.org\/abs\/)/, '').replace(/v\d+$/, '').toLowerCase();
  const tail = id.includes('10993/69015') ? '10993/69015' : id;
  const k = Object.keys(REFS).filter((q) => q.startsWith('s26')).find((q) => REFS[q].toLowerCase().includes(tail));
  if (!k) throw new Error('no reference for surveyed paper ' + r.url);
  return k;
};
const survKeys = survRows.map(keyOf);
must(new Set(survKeys).size === SVY.n, 'every surveyed paper has its own reference');
const pick = (f) => survRows.map((r, i) => (f(r) ? survKeys[i] : null)).filter(Boolean);
const has = (r, k, ...w) => w.some((x) => r[k].toLowerCase().includes(x));
const SROW = [
  ['Simulator written by the authors or not named', pick((r) => r.tool === 'own / not stated')],
  ['Trace-driven, with the authors’ own code', pick((r) => r.tool === 'real traces / dataset')],
  ['Established simulator (ns-3, OMNeT++, MATLAB 5G Toolbox, Sionna)', pick((r) => ['ns-3', 'OMNeT++', 'MATLAB', 'Sionna'].includes(r.tool))],
  ['Carrier in the upper mid-band (7–24 GHz)', pick((r) => r.band === 'FR3 (7-24 GHz)')],
  ['Carrier not stated', pick((r) => r.band === 'not stated')],
  ['Spread of results reported (confidence interval or standard deviation)', pick((r) => has(r, 'stats', 'ci', 'std') && !has(r, 'stats', 'no ci'))],
  ['Statistical test of a difference', pick((r) => has(r, 'stats', 'wilcoxon', 't-test', 'paired test', 'significance'))],
  ['Code released', pick((r) => r.code.toLowerCase().startsWith('yes'))],
];
must(SROW[0][1].length === SVY.own_or_unnamed && SROW[5][1].length === SVY.spread && SROW[6][1].length === SVY.test && SROW[7][1].length === SVY.code, 'survey table matches derive.py');
push(Hsub('rw-eval', 'How recent handover studies are evaluated'));
push(P(`To place our evaluation, we read the full text of ${word(SVY.n)} papers from 2026 on handover or mobility management for 6G or beyond 5G that were openly accessible ${c(...survKeys)}. They were found through OpenAlex, Crossref and arXiv and are a small sample biased towards open-access venues, so the counts in ${TB('survey')} describe this sample only. ${Word(SVY.own_or_unnamed)} of the ${word(SVY.n)} used a simulator written by the authors or did not name one, and ${word(SVY.traces)} more worked on traces with their own code; in none of them did we find a comparison of the simulator with another one. ${Word(SVY.spread)} reported a spread of their results, none tested a difference statistically, and ${word(SVY.code)} released code. Where the comparison was an A3 or signal-strength rule, we did not find a description of how its parameters were set. A gain against a baseline that was not tuned may partly be a gain from tuning. Our study answers these points directly: every method gets the same tuning budget (${SEC('tuning')}), runs are paired and tested (${SEC('stats')}), the simulator is compared with ns-3 (${SEC('calib')}), and code and results are public.`));
push(table('survey', `Evaluation practice in ${SVY.n} handover studies from 2026 (full text read; sample biased towards open-access venues)`,
  [3.2, 0.7, 3.1], ['Practice', `Papers (of ${SVY.n})`, 'References'],
  SROW.map(([lab, ks]) => [lab, String(ks.length), ks.length ? c(...ks) : '—']), { left: [0, 2], frac: '0.92' }));

// ================================================================= 3 MemCHO
push(H('scheme', 'MemCHO: conditional handover steered by place memory and motion'));
push(Hsub('cho', 'Conditional handover in Release 16'));
push(P(`The user filters its RSRP samples (layer-3 filter) and reports a neighbour $n$ when its filtered level $F_n$ exceeds that of the serving cell $F_s$ by a reporting offset. The serving cell asks the neighbour to prepare and, after the preparation delay, sends the user a conditional configuration. In the variant we simulate, the network prepares neighbour $n$ for user $u$ when`));
push(EQ('prep'));
push(P(`and $n$ is among the $n_max$ best neighbours by that margin; a prepared cell is released when it falls a release hysteresis below its threshold. The configuration of each candidate carries an execution condition (condEventA3 with an offset and a time-to-trigger ${c('ts38331')}). The user executes towards $n$ on its own when`));
push(EQ('exec'));
push(P(`after which the other prepared cells are released. If the radio link fails before the user executes, it recovers faster when the cell it selects is a prepared one ${c('ts38300')}. In standard CHO, $O_prep$ and $O_exec$ are the same for every user and neighbour.`));
push(Hsub('labels', 'What the memory records'));
push(P(`Every handover attempt receives exactly one label once its outcome is known. *Too late*: the command or configuration was lost, or the link failed while the handover was prepared. *Too early* or *wrong cell*: execution failed, or the link failed in the target before the evaluation window closed and the user re-established in the source or target (too early) or in a third cell (wrong cell), following the definitions of mobility robustness optimisation ${c('ts38300')}. *Unnecessary*: the handover completed and`));
push(EQ('unn'));
push(P(`where $T_stay$ is the time spent in the target, $Δ\\bar{γ}$ the mean SINR gain over the source during the window, and $T_min^s$ and $θ_Q^s$ depend on the service of the user (2–7 s and 0.4–1.5 dB for the five service classes we simulate). The remaining completed attempts are *useful*. A radio-link failure without a handover in flight is too late if the user re-establishes in another cell. The network can observe all inputs of this label: the dwell time, the reported levels, and the type of a failure.`));
push(Hsub('memory', 'Place memory'));
push(P(`The key of the memory is a place bin $b$: a ${fx(MC.res, 0)} m square of the reported position combined with the heading quadrant, so the two directions of a street are kept apart (${F('scenario')}b). For every bin and target cell the serving cell keeps the counts $C_Y$ (useful), $C_U$ (unnecessary), $C_E$ (too early or wrong cell) and $C_L$ (too late), and for the cell pair $(s,n)$ the corresponding counts $N$. All counts decay with time constant $τ$ = ${fx(MC.tau, 0)} s,`));
push(EQ('forget'));
push(P(`so the memory follows changes in the environment. A late failure is written to the bins the user occupied 0, 0.5 and 1 s before it, since the decision that should have been taken lies before the failure. The pair-level estimates are shrunk towards the share $\\bar{b}$ of bad outcomes over all handovers with $κ_0$ = ${fx(MC.kappa0, 0)} pseudo-counts,`));
push(EQ('pair'));
push(P(`with $N_ok$ = $N_Y + N_U + N_E$ and $G$ the global counts. The place estimates are shrunk towards the pair level with $κ$ = ${fx(MC.kappa, 0)} pseudo-counts:`));
push(EQ('place'));
push(P(`A place without history therefore behaves like its cell pair, and a cell pair without history like the network average. $Δbad$ is positive where handovers to $n$ have gone wrong more often than usual and negative where they have gone well.`));
push(Hsub('motion', 'Motion term'));
push(P(`The motion term is the share of the area the user is expected to cross that lies in the nominal area of neighbour $n$:`));
push(EQ('ovl'));
push(P(`$S_u$ is a circular sector ahead of the user with radius $v_u T_p$ ($T_p$ = ${fx(MC.t_p, 0)} s, at least ${fx(MC.r_min, 0)} m) and opening ±${fx(MC.half_angle, 1)} rad around the reported heading, and $A_n$ the area in which $n$ is the nearest site. The share is evaluated with a fixed 48-point quadrature. It is the trajectory-based ingredient of earlier work ${c('prado')}, reduced to a number per neighbour.`));
push(Hsub('offsets', 'Offsets per user and candidate'));
push(P(`The memory and the motion term shift the two thresholds of standard CHO:`));
push(EQ('oprep'));
push(EQ('oexec'));
push(P(`$O_exec$ is fixed when the cell is prepared and is written into its conditional configuration. A neighbour with a history of unnecessary or early handovers at this place is therefore prepared later and needs a larger margin to execute; a neighbour that users here reached too late, or that lies on the user's path, is prepared earlier and executed sooner. Because $O_prep$ can fall below $o_prep$, the user reports from the lower offset $O_rep$; this is why MemCHO produces more measurement reports than CHO (${SEC('main')}). With the six weights $w$ and $v$ at zero the controller is standard CHO; we checked on event logs that the two then produce identical events.`));
push(Hsub('deploy', 'What a network needs'));
push(P(`The execution offset per candidate is an existing field of the conditional configuration ${c('ts38331')}, so the user side needs no change. The network side needs a position and heading report of the user (for example from location reporting), the outcome labels, which are built from quantities that mobility robustness optimisation already collects ${c('ts38300')}, and a table per serving cell. The table has one key per ${fx(MC.res, 0)} m of street and direction, and each key holds four counts for the few cells reachable from there. A decision is one table lookup and a 48-point quadrature per neighbour. In the simulator the learning variants of CHO needed ${fx(R.timing.per_rule['cho (learning)'], 1)} s of computing time per simulated run of ${fx(DS.t_sim, 0)} s with ${DS.n_ue} users, against ${fx(R.timing.per_rule.cho, 1)} s for standard CHO, on one processor core with NumPy.`));

// ================================================================= 4 Setup
push(H('setup', 'Simulation study'));
push(P(`The study was planned in writing before any tuned comparison of the methods was run; the plan states the hypotheses, the conditions, the tuning budget, the selection rule and the statistics, and it is part of the repository named in the data availability statement. What changed after it was written is stated where it matters: two environment assumptions in the design phase (${SEC('net')}) and one added stage after the pilot run (${SEC('stats')}).`));
push(Hsub('net', 'Network, radio and users'));
push(P(`The layout is the urban grid of TR 37.885 ${c('tr37885')}: 2 × 2 building blocks of 433 m × 250 m separated by 20 m streets, 4.1 km of street in total (${F('scenario')}a). Sites stand on the pavement every 50, 100 or 150 m along every street (${SITES['50']}, ${SITES['100']} and ${SITES['150']} sites), 10 m high. Path loss follows the UMi street-canyon model of TR 38.901 at ${fx(SC.radio.fc_ghz, 0)} GHz, with 7 and 15 GHz as sensitivities ${c('tr38901')}. These formulas are specified for 0.5–100 GHz, but their basis between 7 and 24 GHz is thinner than elsewhere ${c('shakya', 'poddar')}, so our results are model results.`));
push(P(`Blockage is tied to place in three ways: a link is blocked when the straight line crosses a building; obstacles inside the street are modelled by the spatially consistent line-of-sight state of TR 38.901 (50 m correlation distance), fixed per place and site; and a static shadowing field per site (${fx(SC.radio.sf_los, 0)} dB in line of sight, ${fx(SC.radio.sf_nlos, 2)} dB otherwise, ${fx(SC.radio.d_corr, 0)} m decorrelation ${c('gudmundson')}, correlation ${fx(SC.radio.xcorr, 1)} between sites) is shared by all users. On top come a time-varying component (${fx(SC.radio.sigma_t, 1)} dB, ${fx(SC.radio.tau_t, 0)} s) and the error of each layer-1 sample (${fx(SC.radio.meas_sigma, 0)} dB), which are not tied to place. Interference is coupled to load as in our earlier simulator: every cell has a background load, a quarter of the cells are hotspots, and the interference of a cell scales with its load ${c('siomina')}.`));
push(P(`Antennas are abstracted by two numbers: a beam gain of ${fx(SC.radio.g_bs_db, 0)} dB towards served and measuring users, and the ratio $χ$ of the mean gain of an interfering beam to its peak (isolation). We set $χ$ = ${fx(SC.radio.chi, 1)} (about −5 dB) because beams in a street point along the street, so users of the same street are poorly isolated. This value and the street obstacles were set in the design phase, after a first 120 s run with untuned settings, $χ$ = 0.1 and no street obstacles, showed no failure for any rule; a study of a trade-off against failures is pointless without failures. Both were fixed before the tuning grids were written, and $χ$ = 0.1 and 1 are sensitivities.`));
push(P(`Sixty users per run follow the streets and turn at crossings (straight 0.5, left 0.25, right 0.25), as pedestrians at 1.2–1.8 m/s on the pavement or vehicles at about 8 and 16 m/s. Each user has one of five service classes with the 5QI characteristics of TS 23.501 and a demanded rate, from which the delivered rate follows. ${TB('param')} lists the parameters.`));
push(fig('scenario', 'fig_scenario', `Simulated street grid. (a) Layout of TR 37.885 with ${SITES['100']} sites at 100 m spacing and the paths of six vehicles over one minute. (b) Place bins of the memory near a crossing: a 10 m square combined with the heading quadrant, so users driving east and west through the same square update different entries.`, 165));
const pr = SC.proto;
push(table('param', `Simulation parameters (main conditions; sensitivities in ${SEC('bound')})`,
  [1.6, 2.6, 1.6, 2.6],
  ['Parameter', 'Value', 'Parameter', 'Value'],
  [
    ['Layout', 'TR 37.885 urban grid, 2 × 2 blocks, 4.1 km of street', 'Measurement', `L1 sample every ${fx(pr.meas_period * 1000, 0)} ms, L3 filter $k$ = ${pr.l3_k}`],
    ['Site distance', `50 / 100 / 150 m (${SITES['50']} / ${SITES['100']} / ${SITES['150']} sites), height ${fx(SC.radio.h_bs, 0)} m`, 'Reporting', `periodic every ${fx(pr.report_interval * 1000, 0)} ms while the event holds`],
    ['Carrier, bandwidth', `${fx(SC.radio.fc_ghz, 0)} GHz, ${fx(SC.radio.bw_hz / 1e6, 0)} MHz`, 'Preparation, execution', `${fx(pr.t_prep * 1000, 0)} ms, ${fx(pr.t_exec * 1000, 0)} ms`],
    ['Transmit power, gains', `${fx(SC.radio.tx_dbm, 0)} dBm per site, beam gain ${fx(SC.radio.g_bs_db, 0)} dB, noise figure ${fx(SC.radio.nf_db, 0)} dB`, 'Radio-link monitoring', `Qout ${ng(pr.qout_db, 0)} dB / ${fx(pr.qout_win * 1000, 0)} ms, Qin ${ng(pr.qin_db, 0)} dB / ${fx(pr.qin_win * 1000, 0)} ms, N310 = N311 = ${pr.n310}, T310 = ${fx(pr.t310, 0)} s ${c('tr36842')}`],
    ['Path loss', `UMi street canyon, LOS/NLOS ${c('tr38901')}`, 'Re-establishment', `${fx(pr.t_reest, 0)} s; ${fx(pr.t_cho_rec, 1)} s into a prepared cell`],
    ['Blockage', 'buildings; street obstacles (spatially consistent LOS state)', 'Ping-pong window', `${fx(pr.t_pp, 0)} s ${c('tr36839')}`],
    ['Shadowing', `${fx(SC.radio.sf_los, 0)} / ${fx(SC.radio.sf_nlos, 2)} dB, ${fx(SC.radio.d_corr, 0)} m, fully tied to place`, 'Users', `${DS.n_ue}, pedestrians 1.2–1.8 m/s, vehicles 8 and 16 m/s`],
    ['Fast variation', `${fx(SC.radio.sigma_t, 1)} dB over ${fx(SC.radio.tau_t, 0)} s; L1 error ${fx(SC.radio.meas_sigma, 0)} dB`, 'Services', `${D.services.length} classes (5QI ${D.services.map((s) => s.fiveqi).join(', ')}), 0.1–30 Mbit/s`],
    ['Beam isolation $χ$', `${fx(SC.radio.chi, 1)} (main), 1 (${SEC('chi1')})`, 'Run', `${fx(DS.t_sim, 0)} s, first ${fx(DS.discard, 0)} s not counted (${fx(ueMinRun, 0)} UE-min)`],
    ['Load', `background per cell, ${fx(100 * SC.load.hot_frac, 0)}% hotspot cells`, 'Memory', `${fx(MC.res, 0)} m bins × 4 headings, $τ$ = ${fx(MC.tau, 0)} s, $κ$ = $κ_0$ = ${fx(MC.kappa, 0)}`],
  ], { left: [0, 1, 2, 3] }));

push(Hsub('proc', 'Procedures and failures'));
push(P(`The simulator steps in 10 ms and models what decides the outcome of a handover at this time scale. For the baseline handover: report, preparation, command, which is lost if T310 is running when it arrives, execution and a check of the target. For CHO: report, preparation, conditional configuration, which is lost if T310 is running, the execution condition evaluated by the user per prepared cell, release, and recovery into a prepared cell. Radio-link failures follow the out-of-sync and in-sync model of TR 36.839 and TR 36.842 ${c('tr36839', 'tr36842')}. Each failure gets a cause: command lost, link failure during preparation, link failure without a handover (with or without a prepared cell), execution failure, failure in the target shortly after a handover, or coverage. Fast fading, HARQ, random access, beam management and the uplink are not modelled. The label SINR assumes that all cells transmit, so it is a property of the radio environment and does not change with the load a rule produces.`));

push(Hsub('tuning', 'Methods and tuning'));
push(P(`Four methods are compared, together with five ablations of MemCHO (${TB('methods')}). *A3* is the baseline handover with one offset and time-to-trigger. The *per-user margin* moves the A3 offset of every neighbour by the outcome history of the cell pair, a late-failure term and path overlap; we used this rule in earlier work on 5G handover, and here it shows what a margin rule gains without CHO. *CHO* has fixed offsets and five tuned parameters. The ablations remove one ingredient each: execution offsets only, preparation only, memory without motion, motion without memory (trajectory-style preparation as in ECHO ${c('prado')}), and a memory per cell pair without place.`));
push(P(`Tuning is per site distance, as an operator tunes a deployment rather than a speed class, on validation traces that are never used in a test (three mobility profiles × seeds ${DS.val_seeds.join(' and ')}). Every method, the ablations included, receives the same budget of ${DS.n1 + DS.n2} settings: ${DS.n1} drawn at random from its grid and ${DS.n2} around the best of those. MemCHO has the largest grid and the same number of settings, which works against it. The failure budget of a site distance is the failure rate of a reference A3 (3 dB, 160 ms) on the validation traces (standard budget), or a quarter of it (strict budget). Among the settings within the budget, those within ${fx(100 * MC.uho_tol, 0)}% of the lowest unnecessary-handover rate count as equal, and among them the one with the fewest prepared cells and then the fewest failures is selected. The selected settings were frozen before the test stages started.`));
const g = D.grids;
const gsz = (m) => Object.values(g[m].grid).reduce((a, v) => a * v.length, 1);
const SYM = { off: 'offset', ttt: 'TTT', h0: '$h_0$', eta_h: '$η_H$', eta_l: '$η_L$', eta_a: '$η_A$', cap: 'cap', o_prep: '$o_prep$', o_exec: '$o_exec$', ttt_exec: '$T_exec$',
  n_max: '$n_max$', rel_hys: 'rel. hyst.', w_u: '$w_U$', w_l: '$w_L$', w_a: '$w_A$', v_u: '$v_U$', v_l: '$v_L$', v_a: '$v_A$' };
const showSpec = (m) => { const s = sel(100, m).spec; return Object.keys(s).filter((q) => SYM[q]).map((q) => `${SYM[q]} ${String(s[q]).replace('-', '−')}`).join(', '); };
const MROW = [
  ['a3', 'A3 handover', 'offset, time-to-trigger'],
  ['pum', 'Per-user margin (no CHO)', 'base offset, TTT, three weights, cap'],
  ['cho', 'Standard CHO', '$o_prep$, $o_exec$, $T_exec$, $n_max$, release hysteresis'],
  ['memcho', 'MemCHO', 'CHO parameters + $w_U$, $w_L$, $w_A$, $v_U$, $v_L$, $v_A$'],
  ['mc_exec', 'Execution only', 'CHO parameters + $w$'],
  ['mc_prep', 'Preparation only', 'CHO parameters + $v$'],
  ['mc_mem', 'Memory only', 'CHO parameters + $w_U$, $w_L$, $v_U$, $v_L$'],
  ['mc_mot', 'Motion only', 'CHO parameters + $w_A$, $v_A$'],
  ['mc_pair', 'Cell-pair memory', 'as MemCHO, place switched off'],
];
push(table('methods', 'Methods compared, their tuning spaces and the setting selected at 100 m (standard budget). Every method was given 48 settings.',
  [1.35, 2.2, 0.75, 3.9],
  ['Method', 'Tuned parameters', 'Grid size', 'Selected at 100 m (dB, s)'],
  MROW.map(([m, lab, tun]) => [lab, tun, nf(gsz(m)), showSpec(m)]), { left: [0, 1, 3], size: '\\scriptsize' }));
push(P(`The tuned A3 and CHO settings have the largest offset of their grids (8 dB) at all three site distances. A larger offset might have lowered their unnecessary handovers further, at a risk of more failures. MemCHO's execution offset, in contrast, may reach ${fx(MC.O_HI, 0)} dB for single candidates through ${E('oexec')}. Part of its gain may therefore come from offsets that the grid of CHO did not allow; we return to this in ${SEC('limits')}.`));

push(Hsub('stats', 'Stages, endpoints and statistics'));
const st = R.completeness.done;
push(P(`The study has ${word(Object.keys(st).length)} stages with ${nf(nJobs)} jobs; a job is one simulated world (condition and seed) in which all rules run on the same radio samples, and the jobs comprise ${nf(D.n_rule_runs)} runs of a rule. Tuning used ${st.T1 + st.T2} jobs. The main test (S1) has nine conditions, site distance × mobility, with ${DS.test_seeds.length} seeds each, so ${nPairs} runs per rule of ${fx(ueMinRun, 0)} UE-minutes. An open area of the same size with hexagonal sites at 100 m, random-waypoint motion and shadowing that follows each user rather than the place, tuned on its own, tests the boundary (${st.O1 + st.O2 + st.O3} jobs, ${nO} test runs). A second street-grid environment without beam isolation ($χ$ = 1) was tuned and tested separately (${st.X1 + st.X2 + st.X3} jobs, ${nX} test runs). This environment was added after the pilot run, because in the pilot the reference A3 had almost no failures and the failure budget hardly constrained any method; it is not part of the main hypothesis. Stage S2 ran all 48 tuned settings of the four main methods on ${DS.front_seeds.length} test seeds per condition (${st.S2} jobs) for a comparison at equal failure rate, and S3 ran 23 sensitivities with frozen settings (${st.S3} jobs). All ${nf(nJobs)} jobs finished; none failed.`));
push(P(`Endpoints per UE-minute of the measured time are unnecessary handovers, mobility failures by cause, prepared-cell overhead (mean number of prepared cells, preparations, lost configurations, measurement reports), interruption time and the delivered share of the demanded rate. Methods are compared in pairs on the same seeds: the mean paired difference with a 95% $t$ interval, the relative change of the pooled means, and an exact two-sided Wilcoxon signed-rank test. The main hypothesis H1 states that MemCHO, against tuned CHO at the standard budget, has (a) fewer unnecessary handovers, (b) a failure rate that is not higher (upper end of the 95% interval below 0.2 times the mean failure budget) and (c) fewer prepared cells. The three $p$-values are Holm-corrected, and each part is reported on its own.`));

push(Hsub('calib', 'Checks and calibration against ns-3'));
push(P(`Before the runs the simulator passed checks of geometry, path loss against hand computation, shadowing statistics, determinism, conservation of counts (attempts equal the sum of outcomes, failures the sum of causes) and three equivalences on event logs: the per-user margin with zero weights is A3, MemCHO with zero weights is CHO, and CHO with immediate execution is A3. We then rebuilt the urban scenario of our ns-3 study with 5G-LENA ${c('ns3', 'lena')} (3.5 GHz, seven sites, twenty vehicles, Event A3) in this simulator and compared 24 A3 settings without adjusting anything to the ns-3 numbers (${F('calib')}). Handover and unnecessary-handover rates agree: the ratio of the two simulators has a median of ${fx(CAL.ho_ratio_median, 2)} for handovers and ${fx(CAL.uho_ratio_median, 2)} for unnecessary handovers, and the rank correlation over the settings is ${fx(CAL.ho_spearman, 2)} and ${fx(CAL.uho_spearman, 2)}. Failure rates do not agree: ${fx(CAL.fail_mean_sim, 3)} per UE-minute here against ${fx(CAL.fail_mean_ns3, 3)} in ns-3, with a rank correlation of ${fx(CAL.fail_spearman, 2)}. The failure model of the simulator is therefore not calibrated, and its failure rates should be read as relative. Conditional handover is not available in ns-3 with 5G-LENA, so MemCHO itself has no confirmation in a standard simulator.`));
push(fig('calib', 'fig_calib', `Calibration of the simulator against ns-3/5G-LENA for 24 A3 settings (hysteresis 1–6 dB, time-to-trigger in colour). Handover and unnecessary-handover rates agree (median ratio ${fx(CAL.ho_ratio_median, 2)} and ${fx(CAL.uho_ratio_median, 2)}); failure rates are about ${fx(CAL.fail_mean_ns3 / CAL.fail_mean_sim, 0)} times lower here and are not calibrated.`, 165));

// ================================================================= 5 Results
push(H('results', 'Results'));
push(Hsub('main', 'Main test: MemCHO against tuned CHO and A3'));
push(P(`${TB('perf')} and ${F('main')} give the means of the main test over ${nPairs} runs. Tuned CHO had ${ab(choA.rel_pct)}% fewer unnecessary handovers than tuned A3; MemCHO had ${ab(uC.rel_pct)}% fewer than CHO (${fx(uC.mean_ref, 3)} to ${fx(uC.mean_new, 3)} per UE-minute, ${pv(uC.p)}) and ${ab(uA.rel_pct)}% fewer than A3. Its failure rate was ${ab(fC.rel_pct)}% lower than that of CHO (${fx(1000 * fC.mean_ref, 2)} to ${fx(1000 * fC.mean_new, 2)} per thousand UE-minutes, ${pv(fC.p)}) and ${ab(fA.rel_pct)}% lower than that of A3. The interruption time fell by ${ab(iC.rel_pct)}% and the delivered share of the demanded rate rose from ${fx(100 * dC.mean_ref, 1)}% to ${fx(100 * dC.mean_new, 1)}%, a small but consistent gain (${pv(dC.p)}).`));
push(P(`The gains cost preparation. MemCHO kept ${fx(pC.mean_new, 3)} cells prepared on average against ${fx(pC.mean_ref, 3)} for CHO (${sg(pC.rel_pct)}%), and the users sent ${fx(repM, 0)} measurement reports per minute against ${fx(repC, 0)}, ${fx(repRatio, 1)} times as many, because MemCHO reports from the lower offset $O_rep$. The number of preparations per UE-minute was ${fx(mean('S1', 'memcho@std', 'prep_req_pm'), 2)} against ${fx(mean('S1', 'cho@std', 'prep_req_pm'), 2)}, and fewer configurations were lost (${fx(mcCfg, 3)} against ${fx(mean('S1', 'cho@std', 'cfg_lost_pm'), 3)}).`));
must(mean('S1', 'memcho@std', 'cfg_lost_pm') < mean('S1', 'cho@std', 'cfg_lost_pm'), 'fewer lost configurations than CHO');
must(mean('S1', 'memcho@std', 'prep_req_pm') > mean('S1', 'cho@std', 'prep_req_pm'), 'more preparations than CHO');
const PR = [['a3@ref', 'A3, 3 dB / 160 ms (reference)'], ['a3@std', 'A3 (tuned)'], ['pum@std', 'Per-user margin'], ['cho@std', 'CHO'], ['memcho@std', 'MemCHO'],
  ['mc_exec@std', 'Execution only'], ['mc_prep@std', 'Preparation only'], ['mc_mem@std', 'Memory only'], ['mc_mot@std', 'Motion only'], ['mc_pair@std', 'Cell-pair memory']];
const pr1 = (rule) => {
  const g2 = (k) => mean('S1', rule, k);
  const cho = rule.startsWith('a3') || rule.startsWith('pum');
  return [g2('uho_pm'), g2('fail_pm') * 1000, g2('late_pm') * 1000, g2('pp_pm'), g2('prep_mean'), g2('prep_req_pm'), g2('reports_pm'), g2('cfg_lost_pm'), g2('int_s_pm'), 100 * g2('delivered')]
    .map((v, i) => ((cho && [4, 5, 7].includes(i)) ? '—' : fx(v, [3, 2, 2, 3, 3, 2, 0, 3, 3, 2][i])));
};
push(table('perf', `Performance comparison in the main test (street grid, $χ$ = 0.3, standard budget; mean over ${nPairs} runs of ${fx(ueMinRun, 0)} UE-minutes). Rates per UE-minute`,
  [1.9, 0.75, 0.75, 0.75, 0.75, 0.75, 0.8, 0.8, 0.8, 0.8, 0.85],
  ['Method', 'Unnec. HO', 'Failures (×10⁻³)', 'Late fail. (×10⁻³)', 'Ping-pong', 'Prepared cells', 'Prep.', 'Reports', 'Lost config.', 'Interr. [s]', 'Delivered [%]'].map((h) => h.replace('×10⁻³', '$×10^{-3}$').replace('­', '')),
  PR.map(([r, lab]) => [lab, ...pr1(r)]), { left: [0], hl: [4], size: '\\scriptsize',
    note: `Late fail.: failures of the too-late kind. Ping-pong: return to the previous cell within 1 s. Prepared cells: mean size of the prepared set. Prep.: preparations. Reports: measurement reports. Lost config.: conditional configurations lost because T310 was running. Interr.: interruption time per UE-minute. A dash: not applicable to a rule without CHO.` }));
push(fig('main', 'fig_main', `Main test, means with 95% intervals over ${nPairs} runs (the intervals include the spread between conditions; paired differences are much tighter, ${TB('perf')} and text). MemCHO has fewer unnecessary handovers and failures than CHO (dashed line) and a higher delivered share, at the price of more prepared cells. The execution-only and memory-only ablations have still fewer unnecessary handovers, but not the other gains.`, 165));

push(Hsub('hyp', 'Hypotheses'));
const yes = (b) => (b ? 'holds' : 'does not hold');
const h2 = ['mc_exec', 'mc_prep', 'mc_mem', 'mc_mot', 'mc_pair'].map((m) => [m, cmp('S1', 'memcho', m, 'uho_pm')]);
const h2hold = h2.filter(([, q]) => q.ci_hi < 0).map(([m]) => m), h2fail = h2.filter(([, q]) => q.ci_lo > 0).map(([m]) => m);
const LABM = { mc_exec: 'execution only', mc_prep: 'preparation only', mc_mem: 'memory only', mc_mot: 'motion only', mc_pair: 'cell-pair memory' };
const sU = cmp('S1', 'memcho', 'cho', 'uho_pm', 'strict'), sF = cmp('S1', 'memcho', 'cho', 'fail_pm', 'strict'), sP = cmp('S1', 'memcho', 'cho', 'prep_mean', 'strict');
const eq1 = R.S2_equal_failure['1.0|cho|a3'];
const pedC = ['50', '100', '150'].map((d) => R.S1_percell[`${d}|ped|uho_pm`]);
must(eq1.ci_hi < 0, 'P3: CHO fewer UHO than A3 at equal failure rate');
must(iC.ci_hi < 0 && dC.ci_lo > 0, 'H4 holds');
must(sU.ci_hi < 0 && sF.ci_hi < 0 && sP.ci_lo > 0, 'H3: strict budget same pattern');
must(S3.pos15.uho_pm.rel_pct > B3.rel_pct && S3.pos15.uho_pm.p > 0.05, 'B2: position error 15 m weakens the gain');
push(P(`${TB('hyp')} lists the outcome of every hypothesis of the plan. The main hypothesis holds in two of its three parts. MemCHO has fewer unnecessary handovers than CHO (Holm-corrected ${pv(H1.holm[0])}) and not more failures: the upper end of the interval of the difference, ${ng(1000 * fC.ci_hi, 2)} per thousand UE-minutes, lies below the margin of ${fx(1000 * H1.margin, 2)}. Part (c), fewer prepared cells, is rejected: the difference has the opposite sign (${pv(H1.holm[2])}). The unnecessary handovers and the failures do fall together; the preparation overhead does not fall with them.`));
push(P(`Of the premises, P2 failed in both parts. The per-user margin, tuned with the same budget as A3, had ${ab(pumA.rel_pct)}% *more* unnecessary handovers than A3 and ${ab(pumAf.rel_pct)}% fewer failures, the reverse of what we expected from our earlier 5G results. Under a failure budget, a margin rule without CHO gains nothing here; the tuned A3 with an 8 dB offset was hard to beat without the conditional configuration.`));
const HROW = [
  ['P1', 'Most failures of A3 and the per-user margin are late ones', `${fx(100 * P1a.late / P1a.failures, 1)}% and ${fx(100 * P1p.late / P1p.failures, 1)}% late`, 'holds'],
  ['P2', 'Per-user margin: fewer unnecessary HO than A3, not fewer failures', `${sg(pumA.rel_pct)}% unnecessary HO, ${sg(pumAf.rel_pct)}% failures`, 'does not hold'],
  ['P3', 'At equal failure rate CHO has fewer unnecessary HO than A3', `${sg(eq1.rel_pct)}% (${pvc(eq1.p) === '< 0.001' ? '$p$ < 0.001' : '$p$ = ' + pvc(eq1.p)})`, 'holds'],
  ['H1a', 'MemCHO: fewer unnecessary HO than CHO', `${sg(uC.rel_pct)}%, Holm $p$ ${pvc(H1.holm[0])}`, yes(uC.ci_hi < 0)],
  ['H1b', 'MemCHO: failures not higher than CHO', `upper end ${ng(1000 * fC.ci_hi, 2)} < ${fx(1000 * H1.margin, 2)} (×10⁻³)`.replace('×10⁻³', '$×10^{-3}$'), yes(fC.ci_hi < H1.margin)],
  ['H1c', 'MemCHO: fewer prepared cells than CHO', `${sg(pC.rel_pct)}%`, yes(pC.ci_hi < 0)],
  ['H2', 'MemCHO: fewer unnecessary HO than each ablation', `fewer than ${h2hold.map((m) => LABM[m]).join(', ')}; more than ${h2fail.map((m) => LABM[m]).join(', ')}`, 'partly'],
  ['H3', 'Same comparisons at the strict budget', `${sg(sU.rel_pct)}% unnecessary HO, ${sg(sF.rel_pct)}% failures, ${sg(sP.rel_pct)}% prepared`, '(a), (b) hold; (c) not'],
  ['H4', 'Interruption and delivered rate not worse than CHO', `${sg(iC.rel_pct)}% interruption, ${sg(dC.rel_pct)}% delivered`, 'holds'],
  ['B1', 'Open area: no advantage over CHO', `${sg(oU.rel_pct)}% unnecessary HO`, yes(oU.ci_lo > 0)],
  ['B2', 'Gain shrinks without place-tied shadowing, with 15 m position error, for pedestrians', `${sg(S3.place0.uho_pm.rel_pct)}%; ${sg(S3.pos15.uho_pm.rel_pct)}% ($p$ = ${fx(S3.pos15.uho_pm.p, 3)}); slightly more for pedestrians`, 'holds'],
];
must(h2fail.length > 0 && h2hold.length > 0, 'H2 partly');
push(table('hyp', 'Hypotheses of the plan and their outcome (main test unless stated; standard budget)',
  [0.5, 3.0, 3.0, 1.1], ['', 'Statement', 'Result', 'Outcome'], HROW, { left: [0, 1, 2], size: '\\scriptsize' }));

push(Hsub('cond', 'Where the gain comes from: site distance and speed'));
const vehDiffs = COND_V(); function COND_V() { return ['100', '150'].flatMap((d) => ['veh8', 'veh16'].map((p) => R.S1_percell[`${d}|${p}|uho_pm`])); }
must(vehDiffs.every((q) => q.ci_hi < 0), 'vehicles at 100 and 150 m: MemCHO fewer UHO');
const v50 = ['veh8', 'veh16'].map((p) => R.S1_percell[`50|${p}|uho_pm`]);
must(v50.every((q) => q.ci_lo < 0 && q.ci_hi > 0), '50 m vehicles: no significant difference');
const big = R.S1_percell['150|veh16|uho_pm'];
push(P(`${F('conditions')} splits the difference by condition. The gain comes from vehicles at 100 and 150 m, where MemCHO removed between ${ab(Math.min(...vehDiffs.map((q) => -q.rel_pct)), 0)}% and ${ab(Math.max(...vehDiffs.map((q) => -q.rel_pct)), 0)}% of the unnecessary handovers of CHO; the largest absolute reduction, ${fx(-big.diff, 3)} per UE-minute, is at 150 m and 16 m/s. At 50 m the difference for vehicles was not significant: cells are so short that most handovers there are short by geometry, and the memory cannot tell a bad place from a short cell. For pedestrians MemCHO had slightly *more* unnecessary handovers than CHO at all three site distances (${pedC.map((q) => `+${fx(q.diff, 3)}`).join(', ')} per UE-minute), from a very low level. Failures fell most where CHO had many, at 100 m and 16 m/s.`));
push(fig('conditions', 'fig_conditions', `Difference MemCHO − CHO per condition with 95% intervals, for the main environment ($χ$ = 0.3, 40 seeds) and the environment without beam isolation ($χ$ = 1, 20 seeds). The gain in unnecessary handovers (a) comes from vehicles at 100 and 150 m; pedestrians gain nothing. Without beam isolation the failures (b) fall strongly at 100 m but rise for vehicles at 8 m/s and 50 m.`, 165));

push(Hsub('causes', 'Failure causes'));
const fcS = (st, rule, k) => mean(st, `${rule}@std`, k);
const FC = ['f_late_rlf_pm', 'f_exec_fail_pm', 'f_early_rlf_pm'];
must(FC.every((k) => fcS('S1', 'memcho', k) < fcS('S1', 'cho', k)), 'S1: MemCHO lowers all three CHO failure causes');
const redS1 = FC.map((k) => fcS('S1', 'cho', k) - fcS('S1', 'memcho', k));
must(redS1.indexOf(Math.max(...redS1)) === 1, 'S1: execution failures reduced most');
must(fcS('X3', 'memcho', 'f_late_rlf_pm') >= fcS('X3', 'cho', 'f_late_rlf_pm') && fcS('X3', 'memcho', 'f_exec_fail_pm') < fcS('X3', 'cho', 'f_exec_fail_pm') && fcS('X3', 'memcho', 'f_early_rlf_pm') < fcS('X3', 'cho', 'f_early_rlf_pm'), 'X3: only execution and early failures lower');
must(['cho', 'memcho'].every((m) => fcS('X3', m, 'f_late_rlf_pm') > fcS('X3', m, 'f_exec_fail_pm')), 'X3: link failures without handover dominate');
must(fcS('S1', 'a3', 'f_late_cmd_pm') / mean('S1', 'a3@std', 'fail_pm') > 0.5 && fcS('S1', 'pum', 'f_late_cmd_pm') / mean('S1', 'pum@std', 'fail_pm') > 0.5, 'lost commands more than half for A3 and PUM');
const fdiff = ['50', '100', '150'].flatMap((d) => ['ped', 'veh8', 'veh16'].map((p) => [`${d}|${p}`, R.S1_percell[`${d}|${p}|fail_pm`].diff]));
must(fdiff.reduce((a, b) => (b[1] < a[1] ? b : a))[0] === '100|veh16', 'failures fell most at 100 m, 16 m/s');
push(P(`${F('causes')} breaks the failures down by cause. With A3 and the per-user margin, more than half of the failures were lost commands (${fx(100 * P1a.late / P1a.failures, 1)}% for A3), which is the premise P1 of the plan. CHO removes this cause by design; its remaining failures are link failures before any handover started, execution failures and failures shortly after a handover. MemCHO reduced all three, execution failures most. Without beam isolation, link failures before any handover dominate both CHO variants, and MemCHO lowers only the execution failures and the failures soon after a handover.`));
push(fig('causes', 'fig_causes', `Failures by cause in the main test and without beam isolation (standard budget; causes that never occurred are not shown). CHO removes the lost commands that dominate A3; MemCHO further lowers execution failures and failures soon after a handover.`, 165));

push(Hsub('eqfail', 'Comparison at equal failure rate'));
push(P(`A comparison at the tuned settings mixes two effects: a method may have fewer unnecessary handovers because it is better, or because its tuned setting sits at a different failure rate. Stage S2 removes the second effect. For each method and site distance it ran all 48 tuned settings on ${DS.front_seeds.length} test seeds per condition, and for a list of failure levels it took the setting with the fewest unnecessary handovers among those at or below the level (${F('frontier')}). At every level from a quarter to twice the failure budget, MemCHO had ${ab(eqLo, 1)}% to ${ab(eqHi, 1)}% fewer unnecessary handovers than CHO (${Math.max(...eqf.map((q) => q.p)) < 0.001 ? '$p$ < 0.001 at every level' : 'largest ' + pv(Math.max(...eqf.map((q) => q.p)))}). Because the settings are chosen on the same seeds on which they are compared, this stage supports the main test but is not a second confirmatory test.`));
const frontBest = (d, m, lev) => Math.min(...R.S2_front[`${d}|${m}`].filter((q) => q[2] <= lev + 1e-12).map((q) => q[1]));
['50', '100', '150'].forEach((d) => LEV.forEach((l) => {
  const lev = +l * budStd(d), mm = frontBest(d, 'memcho', lev), cc = frontBest(d, 'cho', lev), aa = frontBest(d, 'a3', lev);
  must(mm < cc && (aa === Infinity || cc < aa), `frontier order at ${d} m, level ${l}`);
}));
push(fig('frontier', 'fig_frontier', `All 48 tuned settings of the four main methods on the test seeds (points) and the lowest unnecessary-handover rate reachable at each failure rate (lines). At every site distance and failure level the MemCHO line lies below the CHO line, which lies below the A3 line wherever A3 reaches that level. The dashed line marks the standard failure budget; the axis is linear below $10^{-3}$.`, 165));

push(Hsub('ablation', 'Ablation: what each part does'));
const ab1 = (m, k) => mean('S1', `${m}@std`, k);
must(ab1('mc_mot', 'uho_pm') > ab1('cho', 'uho_pm'), 'motion only worse than CHO in UHO');
must(Math.abs(ab1('mc_pair', 'uho_pm') / ab1('cho', 'uho_pm') - 1) < 0.03 && ab1('mc_pair', 'prep_mean') === Math.min(...['cho', 'memcho', 'mc_exec', 'mc_prep', 'mc_mem', 'mc_mot', 'mc_pair'].map((m) => ab1(m, 'prep_mean'))), 'cell-pair memory: UHO as CHO, fewest prepared cells');
const others = ['a3', 'pum', 'cho', 'memcho', 'mc_exec', 'mc_mem', 'mc_mot'].map((m) => ab1(m, 'fail_pm'));
must(Math.max(ab1('mc_prep', 'fail_pm'), ab1('mc_pair', 'fail_pm')) < Math.min(...others) && ab1('mc_prep', 'fail_pm') < 0.6 * mean('S1', 'memcho@std', 'fail_pm'), 'preparation only and cell-pair memory: fewest failures');
push(P(`The ablations (${TB('perf')}) show that the parts do different things. The execution-only variant had fewer unnecessary handovers than the full scheme (${fx(exM, 3)} against ${fx(mcM, 3)} per UE-minute), and so did memory without motion (${fx(ab1('mc_mem', 'uho_pm'), 3)}). The full scheme is therefore not the variant with the lowest count. What it adds is balance: against the execution-only variant it lost far fewer conditional configurations (${fx(mcCfg, 3)} against ${fx(exCfg, 3)} per UE-minute) and delivered ${fx(100 * mcDel, 1)}% of the demand instead of ${fx(100 * exDel, 1)}%; against memory without motion it had ${ab(cmp('S1', 'memcho', 'mc_mem', 'fail_pm').rel_pct, 0)}% fewer failures. Preparation alone did little for unnecessary handovers (${fx(ab1('mc_prep', 'uho_pm'), 3)}) but, together with the cell-pair memory, had the fewest failures (${fx(1000 * ab1('mc_prep', 'fail_pm'), 2)} and ${fx(1000 * ab1('mc_pair', 'fail_pm'), 2)} per thousand UE-minutes). Motion without memory, the trajectory-style ingredient, was worse than CHO in unnecessary handovers (${fx(ab1('mc_mot', 'uho_pm'), 3)} against ${fx(ab1('cho', 'uho_pm'), 3)}). A memory per cell pair without place had as many unnecessary handovers as CHO (${fx(ab1('mc_pair', 'uho_pm'), 3)}) but the fewest prepared cells and few failures, so the place key, not the memory as such, removes the unnecessary handovers. Most of the reduction of unnecessary handovers therefore comes from the place-keyed memory acting on the execution offset; motion and preparation keep the failures and the delivered rate in check.`));

push(Hsub('time', 'The memory over time'));
push(P(`The memory starts empty in every run. ${F('time')} shows the unnecessary-handover rate in six windows of 100 s over the ${D.windows.n_runs} test runs with event logs. CHO stays flat (${fx(Wc[0], 3)} in the first window, ${fx(Wc[Wc.length - 1], 3)} in the last); MemCHO falls from ${fx(Wm[0], 3)} to ${fx(Wm[Wm.length - 1], 3)}, by ${ab(wDropM, 0)}%. The gain of the main test is thus partly a gain of a memory that is still filling, and a run three times as long gave a larger gain in the sensitivity study (${sg(S3.long.uho_pm.rel_pct)}% against ${sg(B3.rel_pct)}% at the same conditions).`));
must(S3.long.uho_pm.rel_pct < B3.rel_pct, 'longer runs: larger gain');
push(fig('time', 'fig_time', `Unnecessary handovers in six windows of 100 s (${D.windows.n_runs} runs with event logs; memory empty at the start of each run). MemCHO improves as its memory fills; the rules without memory and the per-user margin stay flat.`, 110));

push(Hsub('chi1', 'Strong interference ($χ$ = 1, added after the pilot)'));
push(P(`Without beam isolation the failure rate of CHO is ${fx(xF.mean_ref / fC.mean_ref, 0)} times as high as in the main environment (${fx(1000 * xF.mean_ref, 1)} against ${fx(1000 * fC.mean_ref, 1)} per thousand UE-minutes). With its own tuning, MemCHO had ${ab(xU.rel_pct)}% fewer unnecessary handovers and ${ab(xF.rel_pct)}% fewer failures than CHO over ${nX} paired runs (${pv(xU.p)} and ${pv(xF.p)}), and ${ab(xP.rel_pct)}% more prepared cells. This environment was added after the pilot and is not part of H1. Per condition (${F('conditions')}) the failure gain is concentrated at 100 m; for vehicles at 8 m/s and 50 m MemCHO had more failures than CHO.`));
must(R.X3_percell['50|veh8|fail_pm'].ci_lo > 0, 'chi=1, 50 m veh8: more failures');

push(Hsub('bound', 'Where it stops working: open area and sensitivities'));
push(P(`In the open area nothing about blockage is tied to place: line-of-sight state and shadowing follow each user. There MemCHO, tuned on its own, had ${ab(oU.rel_pct)}% *more* unnecessary handovers than CHO (${pv(oU.p)}), still ${ab(oF.rel_pct)}% fewer failures, and ${ab(oP.rel_pct)}% more prepared cells, as the boundary hypothesis B1 predicted. At the strict budget the two were equal within ${ab(cmp('O3', 'memcho', 'cho', 'uho_pm', 'strict').rel_pct, 1)}%.`));
push(P(`The 23 sensitivities (${F('sens')}) were run with the frozen settings at three conditions (100 m with pedestrians and with 16 m/s vehicles, 50 m with 16 m/s vehicles) and ${DS.sens_seeds.length} seeds; at these conditions the main settings give ${sg(B3.rel_pct)}% unnecessary handovers against CHO. The failure rate of MemCHO was lower than that of CHO in all ${SV.length} variants, with an interval excluding zero in ${s3fSig.length}. Unnecessary handovers were lower in ${s3uLow.length} variants (interval excluding zero in ${s3uSig.length}) and higher in ${s3uHigh.length}. The gain vanishes or reverses when the place-tied structure is removed: with half of the shadowing tied to place MemCHO had ${sg(S3.place50.uho_pm.rel_pct)}% unnecessary handovers, with none ${sg(S3.place0.uho_pm.rel_pct)}%, and without street obstacles ${sg(S3.noclutter.uho_pm.rel_pct)}% (not significant). A position error of 15 m roughly halved the gain (${sg(S3.pos15.uho_pm.rel_pct)}%, ${pv(S3.pos15.uho_pm.p)}). Vehicles at 30 m/s and the case without beam isolation gave the largest gains (${sg(S3.veh30.uho_pm.rel_pct)}% and ${sg(S3.chi100.uho_pm.rel_pct)}%).`));
must(S3.noclutter.uho_pm.p > 0.05 && S3.noclutter.uho_pm.rel_pct > 0, 'no clutter: higher, not significant');
must(S3.pos15.uho_pm.rel_pct > B3.rel_pct / 2 - 1 && S3.pos15.uho_pm.rel_pct < 0, 'pos15 roughly halves the gain');
must(SV.slice().sort((a, b) => S3[a].uho_pm.rel_pct - S3[b].uho_pm.rel_pct).slice(0, 2).sort().join() === 'chi100,veh30', 'largest gains: veh30 and chi100');
push(P(`${TB('env')} collects the comparison of MemCHO with CHO in all three environments, at both budgets and at equal failure rate.`));
push(fig('sens', 'fig_sens', `Sensitivities with frozen settings (three conditions, ${DS.sens_seeds.length} seeds; 95% intervals). Red: MemCHO lower than CHO with an interval excluding zero; blue: higher; grey: interval includes zero. Failures (b) are lower in every variant; unnecessary handovers (a) rise once the shadowing is no longer tied to place.`, 165));
const ENV = [
  ['Street grid, $χ$ = 0.3 (main test)', 'S1', 'std'], ['  strict budget', 'S1', 'strict'],
  ['Street grid, $χ$ = 1 (added after pilot)', 'X3', 'std'], ['  strict budget', 'X3', 'strict'],
  ['Open area (nothing tied to place)', 'O3', 'std'], ['  strict budget', 'O3', 'strict'],
];
const envRow = ([lab, st, b]) => {
  const u = cmp(st, 'memcho', 'cho', 'uho_pm', b), f = cmp(st, 'memcho', 'cho', 'fail_pm', b), p = cmp(st, 'memcho', 'cho', 'prep_mean', b);
  return [lab, String(u.n), fx(u.mean_ref, 3), fx(u.mean_new, 3), sg(u.rel_pct), pvc(u.p), fx(1000 * f.mean_ref, 2), fx(1000 * f.mean_new, 2), sg(f.rel_pct), sg(p.rel_pct)];
};
const eqRows = LEV.map((l, i) => { const q = eqf[i]; return [`Equal failure level ${l} × budget (S2)`, String(q.n), fx(q.mean_ref, 3), fx(q.mean_new, 3), sg(q.rel_pct), pvc(q.p), '', '', '', '']; });
push(table('env', 'MemCHO against CHO in every environment and at equal failure rate',
  [2.6, 0.5, 0.7, 0.7, 0.7, 0.7, 0.75, 0.75, 0.7, 0.75],
  ['Environment', 'Pairs', 'CHO', 'MemCHO', 'Change [%]', '$p$', 'CHO', 'MemCHO', 'Change [%]', 'Prepared cells [%]'],
  [...ENV.map(envRow), '---', ...eqRows], { left: [0], groups: [['', 2], ['Unnecessary HO / UE-min', 4], ['Failures / UE-min (×10⁻³)'.replace('×10⁻³', '$×10^{-3}$'), 3], ['', 1]],
    note: 'Change: relative change of the pooled means; $p$: exact two-sided Wilcoxon signed-rank test on the paired differences. Equal failure level: for each method the setting with the fewest unnecessary handovers among those whose failure rate on the S2 seeds does not exceed the level (descriptive).' }));

// ================================================================= 6 Discussion
push(H('discussion', 'Discussion'));
push(P(`*What the memory learns.* The gains appear where blockage repeats at a place and the user passes it at speed: vehicles at 100 and 150 m in a street grid. They grow while the memory fills, they disappear when the shadowing is no longer tied to place, and they turn into a loss in the open area. A place-keyed memory is therefore not a general improvement of CHO. It pays where the radio environment is repeatable, and an operator could check this before using it, from the outcome logs that mobility robustness optimisation already collects.`));
push(P(`*The price.* MemCHO keeps more cells prepared and sends ${fx(repRatio, 1)} times as many measurement reports. In our model a prepared cell costs nothing but the preparation itself; in a network it reserves resources in the target. Whether ${ab(pC.rel_pct, 0)}% more prepared cells are acceptable for ${ab(uC.rel_pct, 0)}% fewer unnecessary handovers and ${ab(fC.rel_pct, 0)}% fewer failures depends on how scarce those resources are. The preparation-only ablation and the cell-pair memory had about half the failures of MemCHO, and the cell-pair memory had the fewest prepared cells; they are the cheaper options when failures and overhead matter more than unnecessary handovers. A version that limits the reporting offset, or caps the prepared set more tightly where the memory is confident, is an obvious next step.`));
push(P(`*The baselines.* Two results deserve attention beyond MemCHO. Tuned A3 with an 8 dB offset was a strong baseline: the per-user margin rule of our earlier 5G work did worse than it under the failure budget, and CHO beat it by ${ab(choA.rel_pct, 0)}% in unnecessary handovers. And the best settings of A3 and CHO lay at the edge of their grids. Studies that compare against an A3 with a textbook offset of 3 dB report gains that are partly gains from tuning: in our main test the reference A3 with 3 dB and 160 ms had ${fx(mean('S1', 'a3@ref', 'uho_pm') / mean('S1', 'a3@std', 'uho_pm'), 1)} times the unnecessary handovers of the tuned A3. This is the point of ${SEC('rw-eval')}, now with a number.`));
must(mean('S1', 'a3@ref', 'uho_pm') > 1.5 * mean('S1', 'a3@std', 'uho_pm'), 'reference A3 far worse than tuned A3');

// ================================================================= 7 Limitations
push(H('limits', 'Limitations'));
push(L([
  `*Model results.* Everything rests on a system-level simulator of our own. Handover and unnecessary-handover rates were compared with ns-3/5G-LENA and agree within the ranges of ${SEC('calib')}; failure rates were not calibrated and are about ${fx(CAL.fail_mean_ns3 / CAL.fail_mean_sim, 0)} times lower than in ns-3, so the failure reductions should be read as relative. Conditional handover is not available in ns-3 with 5G-LENA, and MemCHO has no confirmation in a standard simulator.`,
  `*Environment assumptions set in the design phase.* The beam isolation $χ$ = 0.3 and the street obstacles were chosen after a first untuned run showed no failures at all. Both were fixed before tuning, and $χ$ = 0.1, $χ$ = 1 and no obstacles were run as sensitivities, but the main environment is one in which failures exist by our choice.`,
  `*An added stage.* The environment without beam isolation was added after the pilot and is reported in full, but it is not part of the main hypothesis.`,
  `*Grid edge.* The tuned A3 and CHO offsets lie at the top of their grids (8 dB), while MemCHO's per-candidate execution offset can reach ${fx(MC.O_HI, 0)} dB. A wider grid for the baselines may narrow the gap.`,
  `*Abstractions.* No beam management, fast fading, random access or uplink; one number for beam gain and one for isolation; outdoor users only; one carrier. The position of the user is assumed to be reported; errors of 5 and 15 m were tested. Lower-layer triggered mobility of Release 18 ${c('khodapanah')} is not simulated, and we make no claim against it.`,
  `*Channel model.* TR 38.901 between 7 and 24 GHz was re-examined only in Release 19, and measurements deviate from it in part ${c('shakya', 'poddar')}. We call the setting beyond-5G conditions; no 6G system is simulated.`,
  `*Definition of unnecessary.* With cells of 50–150 m many stays are short by geometry, so the level of the unnecessary-handover rate depends on the definition. Under the stricter definition (short *and* low gain) MemCHO had ${ab(cmp('S1', 'memcho', 'cho', 'uho_and_pm').rel_pct, 0)}% fewer than CHO; ping-pongs within 1 s did not differ significantly (${pv(cmp('S1', 'memcho', 'cho', 'pp_pm').p)}).`,
]));
must(cmp('S1', 'memcho', 'cho', 'uho_and_pm').ci_hi < 0 && cmp('S1', 'memcho', 'cho', 'pp_pm').p > 0.05, 'alternative labels: stricter definition lower, ping-pong n.s.');

// ================================================================= 8 Conclusion
push(H('concl', 'Conclusion'));
push(P(`A memory of where handovers went wrong, keyed by 10 m of street and direction of travel, can steer conditional handover per user and candidate through fields that Release 16 already has. In a simulated street grid at 10 GHz with sites every 50 to 150 m, MemCHO had ${ab(uC.rel_pct)}% fewer unnecessary handovers and ${ab(fC.rel_pct)}% fewer failures than CHO tuned with the same budget, ${ab(eqLo, 0)}–${ab(eqHi, 0)}% fewer unnecessary handovers at equal failure rate, and a slightly higher delivered rate. It did not lower the preparation overhead, which rose by ${ab(pC.rel_pct, 0)}%, with ${fx(repRatio, 1)} times the measurement reports. The gain comes from vehicles in streets where blockage repeats at a place; it is absent for pedestrians and reverses in an open area. Before such a memory is used, the repeatability of handover outcomes in the area should be checked. Confirmation in a standard simulator with CHO, a failure model calibrated against measurements, and a variant that limits the extra reporting are the next steps.`));

// ================================================================= end matter
const SECn = (t) => push(K.unnumbered(t));
SECn('CRediT authorship contribution statement');
push(P('*Mostafa Jalili Sanjarani:* Conceptualization, Methodology, Software, Investigation, Formal analysis, Visualization, Writing – original draft. *Yasser Elmi Sola:* Conceptualization, Methodology, Supervision, Project administration, Writing – review and editing. *Hesam Hasanpour:* Validation, Writing – review and editing. *Ali Akbar Neghabi:* Validation, Writing – review and editing.'));
SECn('Declaration of competing interest');
push(P('The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.'));
SECn('Funding');
push(P('This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.'));
push(`\\section*{Data and code availability}\\label{sec:avail}\n`);
push(P(`The simulator, the study plan, the run and analysis scripts, the scripts that draw every figure and table of this paper, and the summary results of all ${nf(nJobs)} jobs (one row per run and rule, the tuning tables and the analysis report) are available at https://github.com/mjs19971997/memcho-beyond5g. An archived release with a DOI will follow.`));
SECn('Declaration of generative AI and AI-assisted technologies in the manuscript preparation process');
push(P('During the preparation of this work the authors used Claude (Anthropic) to assist with writing the simulation, analysis and plotting code and with drafting and language editing of the text. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the published article.'));

// ---- output, plus the numbers that the submission documents and the guide reuse
fs.mkdirSync(path.join(HERE, 'data'), { recursive: true });
fs.writeFileSync(path.join(HERE, 'data', 'p3_text.json'), JSON.stringify({ TITLE, ABSTRACT, KEYWORDS, HIGHLIGHTS, nWords, JOURNAL,
  num: { uho: uC.rel_pct, fail: fC.rel_pct, prep: pC.rel_pct, deliv: dC.rel_pct, uhoA3: uA.rel_pct, failA3: fA.rel_pct, rep: repRatio, eqLo, eqHi, open: oU.rel_pct, xU: xU.rel_pct, xF: xF.rel_pct,
    pumA: pumA.rel_pct, place0: S3.place0.uho_pm.rel_pct, place50: S3.place50.uho_pm.rel_pct, exM, mcM, nJobs, nPairs } }, null, 1));
build(path.resolve(process.argv[2] || path.join(HERE, 'out', 'MemCHO_ComNet.tex')), TITLE);
