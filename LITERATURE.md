# Literature scan: conditional handover, lower-layer mobility, upper mid-band, ultra-dense networks

Date of the scan: 12 October 2026. Purpose: decide whether the working idea is free, and what the
study may claim.

**How the sources were checked.** Every entry below was confirmed on a page that could be opened:
an arXiv abstract page, the Crossref or OpenAlex record of the DOI, the 3GPP portal, an ETSI PDF,
or a public mirror of the specification text. IEEE Xplore and the doi.org landing pages refused
automated access, so for IEEE papers the DOI was confirmed through Crossref/OpenAlex and the
content through the abstract stored there or the arXiv version. Where only the existence of a paper
could be confirmed, this is said. Nothing here was read in full text unless stated; before the
manuscript cites a result, the paper itself must be read.

## 1. Sources

### Conditional handover (CHO): principle and performance

1. H. Martikainen, I. Viering, A. Lobinger, T. Jokela, "On the Basics of Conditional Handover for
   5G Mobility," IEEE PIMRC 2018. DOI 10.1109/PIMRC.2018.8580946.
   CHO gains robustness, but signalling can rise sharply if it is badly parameterised; the abstract
   already names self-optimisation of CHO and source-quality-based triggering as remedies.
2. J. Stanczak, U. Karabulut, A. Awada, "Conditional Handover in 5G - Principles, Future Use Cases
   and FR2 Performance," IWCMC 2022. DOI 10.1109/IWCMC55113.2022.9824571; arXiv:2204.01283.
   FR2 system simulations: CHO removes most mobility failures of the Rel-15 handover; recovery
   through a prepared cell is used in more than 80 % of the failures in some scenarios.
3. S. B. Iqbal, A. Awada, U. Karabulut, I. Viering, P. Schulz, G. P. Fettweis, "On the Modeling and
   Analysis of Fast Conditional Handover for 5G-Advanced," IEEE PIMRC 2022.
   DOI 10.1109/PIMRC54779.2022.9977719; arXiv:2204.06909.
   Keeping prepared cells after a handover (FCHO) lowers CHO signalling and failures in FR2.
4. S. B. Iqbal, S. Nadaf, A. Awada, U. Karabulut, P. Schulz, G. P. Fettweis, "On the Analysis and
   Optimization of Fast Conditional Handover With Hand Blockage for Mobility," IEEE Access 2023.
   DOI 10.1109/ACCESS.2023.3260630; arXiv:2211.00573.
   Three resource-reservation variants that trade reservation time and signalling against failures.

### Prediction or learning for the prepared set and for CHO parameters (closest prior work)

5. A. Prado, H. Vijayaraghavan, W. Kellerer, "ECHO: Enhanced Conditional Handover boosted by
   Trajectory Prediction," IEEE GLOBECOM 2021. DOI 10.1109/GLOBECOM46510.2021.9685348.
   A sequence model predicts the trajectory and selects the cells to prepare. Abstract: with one
   prepared cell it beats CHO with three (handover rate -23 %, RLF rate -77 %, control messages
   -69 %). It adapts the prepared set per UE from motion; no per-candidate execution offset and no
   outcome memory are mentioned in the abstract (full text not read).
6. C. Lee, H. Cho, S. Song, J.-M. Chung, "Prediction-Based Conditional Handover for 5G mm-Wave
   Networks: A Deep-Learning Approach," IEEE Vehicular Technology Magazine 15(1), 2020.
   DOI 10.1109/MVT.2019.2959065.
   Deep learning on signal and blockage patterns predicts the next cell, so that fewer cells are prepared.
7. S. C. Sundararaju, S. Ramamoorthy, D. P. Basavaraj, V. Phanindhar, "Advanced Conditional
   Handover in 5G and Beyond Using Q-Learning," IEEE WCNC 2024. DOI 10.1109/WCNC57260.2024.10570840.
   The UE learns handover parameters for CHO targets from current conditions and past handover
   results. Closest work on adapting CHO execution parameters from past outcomes; which parameters,
   whether keyed by place, and which metrics are not clear from the abstract (full text not read).
8. M. Kalntis, F. A. Kuipers, G. Iosifidis, "CHOMET: Conditional Handovers via Meta-Learning,"
   arXiv:2507.07581 (2025). Online meta-learning decides which cells to prepare (at most J per UE)
   from SINR, bandwidth and availability, trading rate against preparation signalling. No location
   or trajectory input; execution offsets are given, not learned.
9. S. Deb, M. Rathod, R. Balamurugan, S. K. Ghosh, R. K. Singh, S. Sanyal, "Performance evaluation
   of conditional handover in 5G systems under fading scenario," arXiv:2403.04379 (2024).
   A Markov model: the best preparation and execution offsets and timers depend on UE speed and
   fading. An analysis, not a controller.
10. A. Awada, B. Wegmann, I. Viering, A. Klein, "A location-based self-optimizing algorithm for the
    inter-RAT handover parameters," IEEE ICC 2013. DOI 10.1109/ICC.2013.6655592.
    Handover thresholds set by UE location inside a cell resolve failures that cell-level
    optimisation cannot. LTE inter-RAT, no CHO; it shows that location-keyed mobility robustness
    optimisation is not new in itself.

### Lower-layer (L1/L2) triggered mobility

11. A. Gündogan, A. Badalıoglu, P. Spapis, A. Awada, "On the Modelling and Performance Analysis of
    Lower Layer Mobility in 5G-Advanced," arXiv:2211.02725 (2022).
    System-level comparison of baseline handover, CHO and L1-based cell change: better reliability,
    more cell changes and ping-pongs; filtering reduces the ping-pongs at a reservation cost.
12. B. Khodapanah et al., "On L1/L2-Triggered Mobility in 3GPP Release 18 and Beyond," IEEE Access
    2024. DOI 10.1109/ACCESS.2024.3491500. Existence confirmed; content not checked.

### Upper mid-band (FR3, about 7-24 GHz)

13. S. Kang, M. Mezzavilla, S. Rangan, A. Madanayake, S. B. Venkatakrishnan, G. Hellbourg, M. Ghosh,
    H. Rahmani, A. Dhananjay, "Cellular Wireless Networks in the Upper Mid-Band," IEEE Open Journal
    of the Communications Society 5, 2024. DOI 10.1109/OJCOMS.2024.3373368; arXiv:2309.03038.
    Coverage and capacity in dense urban areas, coexistence, antennas. No handover study.
14. D. Shakya et al. (NYU Wireless), "Urban Outdoor Propagation Measurements and Channel Models at
    6.75 GHz FR1(C) and 16.95 GHz FR3 Upper Mid-Band Spectrum for 5G and 6G," arXiv:2410.17539 (2024).
    Urban microcell campaign, 40-880 m: path-loss exponents below those at mmWave; NLOS delay and
    angular spreads below the 3GPP model values. A reason to treat 7-15 GHz model results with care.
15. H. Poddar, D. Gold, D. Lee, N. Zhang, G. Sridharan, H. Asplund, M. Shafi, "Overview of 3GPP
    Release 19 Study on Channel Modeling Enhancements to TR 38.901 for 6G," arXiv:2507.19266 (2025).
    Summary of the Rel-19 validation of TR 38.901 for 7-24 GHz and of what was added.
16. C. Altmeyerhenzien, L. Simić, M. Petrova, "The Price of the Golden 6G Band: Evaluation of Beam
    Management Effort in FR3," arXiv:2609.16839 (2026).
    Ray tracing with eight macro sites at 2.1-28 GHz; the rate of serving-site changes is similar
    in FR1, FR3 and FR2. A site change is an SINR-threshold rule: no handover procedure, no failure
    model, no ultra-dense deployment. The only FR3 mobility-related evaluation found.

### Ultra-dense networks and surveys (existence confirmed through Crossref; content not re-read)

17. R. Arshad, H. ElSawy, S. Sorour, T. Y. Al-Naffouri, M.-S. Alouini, "Handover Management in 5G
    and Beyond: A Topology Aware Skipping Approach," IEEE Access 2016. DOI 10.1109/ACCESS.2016.2642538.
18. M. Tayyab, X. Gelabert, R. Jäntti, "A Survey on Handover Management: From LTE to NR," IEEE
    Access 2019. DOI 10.1109/ACCESS.2019.2937405.
19. M. S. Mollel et al., "A Survey of Machine Learning Applications to Handover Management in 5G and
    Beyond," IEEE Access 2021. DOI 10.1109/ACCESS.2021.3067503.

### Specifications

20. 3GPP TS 38.300 (NR overall description, stage 2): clause 9.2.3.4 Conditional Handover, 9.2.3.5
    L1/L2 Triggered Mobility, 15.5.2 Mobility Robustness Optimisation with the definitions of too
    late handover, too early handover and handover to wrong cell and their CHO counterparts.
    https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3191
21. 3GPP TS 38.331 (RRC): `CondTriggerConfig-r16` (condEventA3 with a3-Offset, hysteresis,
    timeToTrigger; condEventA5), `CondReconfigToAddModList-r16` with up to `maxNrofCondCells-r16`
    entries, one or two execution conditions per candidate.
    https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3197
    Not verified: the numeric value of `maxNrofCondCells-r16` (8 according to a RAN2 discussion
    paper seen only in a search snippet). Check clause 6.4 before citing the number.
22. 3GPP TR 38.901 (channel model 0.5-100 GHz): UMi street canyon path loss in Table 7.4.1-1, LOS
    probability in Table 7.4.2-1; Rel-19 versions (19.x) contain the 7-24 GHz study results
    (study item RP-234018).
    https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3173
23. 3GPP TR 36.839 (mobility enhancements in heterogeneous networks, Rel-11): handover-failure and
    radio-link-failure modelling (clause 5.2.1).
    https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=2540
    Not verified in the TR text itself: Qout -8 dB / Qin -6 dB. These values, T310 = 1000 ms and
    N310 = N311 = 1 were confirmed in TR 36.842 Table B.2-1 and in TR 38.744 Table 5.4.1-1 (Rel-19
    study on AI/ML for mobility), which use the same model. Cite one of those unless TR 36.839 is checked.
24. 3GPP TR 37.885 (V2X evaluation methodology), Annex A: urban grid 433 m x 250 m, lanes 3.5 m,
    two lanes per direction.
    https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3209

Also confirmed to exist, not checked for content: A. Prado, F. Mehmeti, W. Kellerer, "Cost-Efficient
Mobility Management in 5G," IEEE WoWMoM 2023, DOI 10.1109/WoWMoM57956.2023.00036 (described
elsewhere as offline optimisation of CHO preparations).

## 2. What is already done

* **Which cells to prepare.** Well covered: from trajectory prediction (5), from signal and
  blockage prediction (6), from online learning on SINR (8), by keeping preparations across
  handovers (3, 4). Reducing preparation overhead is an explicit goal in 3, 4, 5 and 8.
* **When to execute.** Covered more thinly: network-level self-optimisation of CHO parameters is
  named in 1; the dependence of the best offsets on speed and fading is shown analytically in 9;
  per-UE learning of CHO parameters from past handover results exists in 7.
* **Place.** Location-keyed handover thresholds were shown to beat cell-level optimisation in LTE (10).
* **Failure taxonomy.** Too late / too early / wrong cell, also for CHO execution, are 3GPP
  definitions (20); a study that reports them is using the standard vocabulary, not inventing one.
* **Lower-layer mobility.** Rel-18 LTM is evaluated in 11 and 12; it is a competitor to CHO that
  this study does not simulate.
* **Upper mid-band.** Propagation and system studies exist (13-15). For mobility there is one
  paper (16), at macro density and without a handover procedure or a failure model.

## 3. The gap this study can claim, and what it cannot

Not found, after searches with six phrasings on arXiv, Crossref/OpenAlex and the open web:

1. a controller that sets **both** the prepared set **and** a per-user, per-candidate execution
   offset from a **place-keyed memory of handover outcome classes** (not of predicted signal
   levels), combined with motion information;
2. an evaluation that reports **unnecessary handovers, failures by cause and preparation overhead
   together** for such a controller, with ablations that separate the known ingredients
   (motion-only preparation as in 5, cell-pair-level parameter adaptation as in 1 and 7,
   execution-only, preparation-only);
3. a **procedure-level** evaluation of handover and CHO (measurement chain, preparation delay,
   radio-link failure, failure causes) in an **ultra-dense upper-mid-band street deployment**
   (7-15 GHz, 50-150 m site distance), and a statement of the conditions under which place memory
   stops helping.

The study may claim these three points "to the authors' knowledge". It may **not** claim:

* that learning-based or trajectory-based selection of CHO candidates is new (5, 6, 8);
* that adapting CHO parameters from past outcomes is new (1, 7), or that location-based
  optimisation of handover parameters is new (10);
* that preparation overhead had not been addressed (3, 4, 5, 8);
* that mobility in FR3 is unstudied (16), or anything about "6G" as a system: there is no 6G
  standard; the study simulates Rel-16 procedures under conditions expected beyond 5G;
* superiority over L1/L2-triggered mobility, which is not simulated (11, 12);
* validity beyond the channel model: TR 38.901 in 7-24 GHz was re-examined only in Rel-19 and
  measurements (14) deviate from it in part.

**Limits of this scan.** Absence of evidence from a web search without IEEE Xplore full text and
without a patent search. Before the manuscript says "no prior work", sources 7 and the WoWMoM 2023
paper must be read in full and an IEEE Xplore and a patent search must be run.

## 4. Consequence for the research question

The working idea survives, narrowed. The contribution is not "learning for CHO" but the specific
combination (outcome memory by place, used for preparation and for the execution offset that the
standard already carries per candidate), its joint effect on three quantities that prior work
reports separately, the deployment (upper mid-band, ultra-dense, blockage tied to place), and the
boundary conditions. The ablations in PLAN.md are chosen so that each known ingredient appears as
its own comparator.
