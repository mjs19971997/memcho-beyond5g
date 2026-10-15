# Amendment 2: baselines tuned on extended grids - before / after

Before = full run on the student's i9 (`results/full_i9/results/full`, A3 offset and CHO execution offset 0-8 dB, CHO preparation offset -6..0 dB, CHO execution TTT 0-0.32 s). After = `results/full_ext` (A3 offset 0-16 dB, CHO execution offset 0-16 dB, preparation offset -6..+4 dB, execution TTT 0-1.28 s; same 32 + 16 settings per method; all other rules' rows reused unchanged on identical worlds). Standard failure budget unless stated. Rates per UE-minute; differences are paired by seed, mean with 95 % t interval, exact Wilcoxon p.

## 1. Frozen baseline settings

Edge = at the top of the extended grid; floor = at a natural lower bound (TTT 0 s, prepared-set limit 1).

| setting | site distance | rule | budget | before | after | validation UHO before -> after | validation failures before -> after | flags after |
|---|---|---|---|---|---|---|---|---|
| street grid, chi 0.3 | 50 m | A3 | std | off 8, ttt 0 | off 10, ttt 0 | 0.720 -> 0.619 | 0.0000 -> 0.0003 | floor: ttt |
| street grid, chi 0.3 | 50 m | A3 | strict | off 8, ttt 0 | off 10, ttt 0 | 0.720 -> 0.619 | 0.0000 -> 0.0003 | floor: ttt |
| street grid, chi 0.3 | 50 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 1, rel_hys 2 | o_prep -4, o_exec 12, ttt_exec 0.04, n_max 2, rel_hys 2 | 0.588 -> 0.480 | 0.0014 -> 0.0000 | - |
| street grid, chi 0.3 | 50 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.16, n_max 1, rel_hys 2 | o_prep -4, o_exec 12, ttt_exec 0.04, n_max 2, rel_hys 2 | 0.666 -> 0.480 | 0.0000 -> 0.0000 | - |
| street grid, chi 0.3 | 100 m | A3 | std | off 8, ttt 0.16 | off 12, ttt 0 | 0.099 -> 0.060 | 0.0031 -> 0.0053 | floor: ttt |
| street grid, chi 0.3 | 100 m | A3 | strict | off 8, ttt 0.04 | off 10, ttt 0.04 | 0.116 -> 0.080 | 0.0014 -> 0.0003 | - |
| street grid, chi 0.3 | 100 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 1, rel_hys 2 | o_prep 4, o_exec 6, ttt_exec 1.28, n_max 2, rel_hys 2 | 0.077 -> 0.014 | 0.0011 -> 0.0078 | edge: o_prep; edge: ttt_exec |
| street grid, chi 0.3 | 100 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 1, rel_hys 2 | o_prep 4, o_exec 10, ttt_exec 0.64, n_max 2, rel_hys 4 | 0.077 -> 0.043 | 0.0011 -> 0.0019 | edge: o_prep |
| street grid, chi 0.3 | 150 m | A3 | std | off 8, ttt 0.04 | off 12, ttt 0 | 0.666 -> 0.288 | 0.0103 -> 0.0300 | floor: ttt |
| street grid, chi 0.3 | 150 m | A3 | strict | off 8, ttt 0 | off 10, ttt 0 | 0.691 -> 0.437 | 0.0064 -> 0.0075 | floor: ttt |
| street grid, chi 0.3 | 150 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 1, rel_hys 2 | o_prep 2, o_exec 14, ttt_exec 0.32, n_max 2, rel_hys 4 | 0.460 -> 0.138 | 0.0272 -> 0.0222 | - |
| street grid, chi 0.3 | 150 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.16, n_max 1, rel_hys 2 | o_prep -2, o_exec 14, ttt_exec 0, n_max 2, rel_hys 4 | 0.607 -> 0.202 | 0.0103 -> 0.0072 | floor: ttt_exec |
| street grid, chi 1 | 50 m | A3 | std | off 6, ttt 0 | off 6, ttt 0 | 0.194 -> 0.194 | 0.0039 -> 0.0039 | floor: ttt |
| street grid, chi 1 | 50 m | A3 | strict | off 6, ttt 0 | off 6, ttt 0 | 0.194 -> 0.194 | 0.0039 -> 0.0039 | floor: ttt |
| street grid, chi 1 | 50 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.04, n_max 2, rel_hys 2 | o_prep 2, o_exec 8, ttt_exec 0.04, n_max 4, rel_hys 2 | 0.161 -> 0.161 | 0.0003 -> 0.0003 | - |
| street grid, chi 1 | 50 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.04, n_max 2, rel_hys 2 | o_prep 2, o_exec 8, ttt_exec 0.04, n_max 4, rel_hys 2 | 0.161 -> 0.161 | 0.0003 -> 0.0003 | - |
| street grid, chi 1 | 100 m | A3 | std | off 6, ttt 0.04 | off 6, ttt 0.04 | 0.129 -> 0.129 | 0.0167 -> 0.0167 | - |
| street grid, chi 1 | 100 m | A3 | strict | off 5, ttt 0 | off 5, ttt 0 | 0.191 -> 0.191 | 0.0092 -> 0.0092 | floor: ttt |
| street grid, chi 1 | 100 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 1, rel_hys 2 | o_prep 2, o_exec 10, ttt_exec 0.08, n_max 1, rel_hys 2 | 0.040 -> 0.041 | 0.0142 -> 0.0328 | floor: n_max |
| street grid, chi 1 | 100 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 2, rel_hys 4 | o_prep -6, o_exec 8, ttt_exec 0.16, n_max 2, rel_hys 2 | 0.049 -> 0.060 | 0.0064 -> 0.0022 | lower end: o_prep |
| street grid, chi 1 | 150 m | A3 | std | off 6, ttt 0.04 | off 6, ttt 0.04 | 0.860 -> 0.860 | 0.0508 -> 0.0508 | - |
| street grid, chi 1 | 150 m | A3 | strict | off 5, ttt 0 | off 5, ttt 0 | 1.157 -> 1.157 | 0.0283 -> 0.0283 | floor: ttt |
| street grid, chi 1 | 150 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 2, rel_hys 4 | o_prep 0, o_exec 12, ttt_exec 0, n_max 4, rel_hys 2 | 0.343 -> 0.197 | 0.0567 -> 0.0908 | floor: ttt_exec |
| street grid, chi 1 | 150 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.04, n_max 4, rel_hys 2 | o_prep 0, o_exec 8, ttt_exec 0.04, n_max 4, rel_hys 2 | 0.484 -> 0.484 | 0.0131 -> 0.0131 | - |
| open area | 100 m | A3 | std | off 8, ttt 0.24 | off 12, ttt 0.04 | 1.886 -> 1.248 | 0.5294 -> 0.4100 | - |
| open area | 100 m | A3 | strict | off 8, ttt 0 | off 10, ttt 0 | 3.158 -> 2.117 | 0.2183 -> 0.1919 | floor: ttt |
| open area | 100 m | CHO | std | o_prep 0, o_exec 8, ttt_exec 0.32, n_max 1, rel_hys 2 | o_prep 0, o_exec 16, ttt_exec 0.32, n_max 1, rel_hys 2 | 1.548 -> 0.280 | 0.1972 -> 0.5192 | edge: o_exec; floor: n_max |
| open area | 100 m | CHO | strict | o_prep 0, o_exec 8, ttt_exec 0.04, n_max 4, rel_hys 2 | o_prep 0, o_exec 14, ttt_exec 0.16, n_max 2, rel_hys 2 | 2.939 -> 0.732 | 0.1061 -> 0.1108 | - |

Settings still at the top of an extended grid: street grid, chi 0.3 100 m CHO std (edge: o_prep, edge: ttt_exec); street grid, chi 0.3 100 m CHO strict (edge: o_prep); open area 100 m CHO std (edge: o_exec)

## 2. Test stages (frozen settings, held-out seeds)

### S1 main test, street grid, chi 0.3 (9 conditions x 40 seeds)

| comparison | endpoint | before: ref -> MemCHO, diff [95 %], p | after: ref -> MemCHO, diff [95 %], p |
|---|---|---|---|
| MemCHO vs CHO | unnecessary HO | 0.397 -> 0.319, -0.078 [-0.094, -0.063], -19.7%, p = 1e-21 (n = 360) | 0.209 -> 0.319, 0.110 [0.097, 0.123], 52.8%, p = 2.6e-84 (n = 360) |
| MemCHO vs CHO | failures | 0.0053 -> 0.0023, -0.0030 [-0.0041, -0.0020], -57.3%, p = 1.3e-10 (n = 360) | 0.0204 -> 0.0023, -0.0182 [-0.0233, -0.0130], -88.9%, p = 2e-28 (n = 360) |
| MemCHO vs CHO | prepared cells | 0.165 -> 0.225, 0.060 [0.056, 0.064], 36.1%, p = 2.2e-93 (n = 360) | 0.287 -> 0.225, -0.062 [-0.072, -0.053], -21.7%, p = 4.4e-27 (n = 360) |
| MemCHO vs CHO | rate Mbit/s | 14.122 -> 14.261, 0.139 [0.123, 0.154], 1.0%, p = 1.7e-108 (n = 360) | 13.864 -> 14.261, 0.397 [0.340, 0.454], 2.9%, p = 8.5e-109 (n = 360) |
| MemCHO vs CHO | delivered share | 0.9803 -> 0.9899, 0.0096 [0.0085, 0.0107], 1.0%, p = 1.7e-108 (n = 360) | 0.9624 -> 0.9899, 0.0275 [0.0236, 0.0314], 2.9%, p = 8.5e-109 (n = 360) |
| MemCHO vs A3 | unnecessary HO | 0.514 -> 0.319, -0.195 [-0.222, -0.169], -38.0%, p = 1.4e-61 (n = 360) | 0.328 -> 0.319, -0.010 [-0.018, -0.001], -2.9%, p = 0.01 (n = 360) |
| MemCHO vs A3 | failures | 0.0069 -> 0.0023, -0.0046 [-0.0063, -0.0028], -66.9%, p = 1.4e-07 (n = 360) | 0.0100 -> 0.0023, -0.0077 [-0.0093, -0.0061], -77.2%, p = 7.4e-38 (n = 360) |
| MemCHO vs A3 | prepared cells | 0.000 -> 0.225, 0.225 [0.216, 0.234], n/a%, p = 8.5e-109 (n = 360) | 0.000 -> 0.225, 0.225 [0.216, 0.234], n/a%, p = 8.5e-109 (n = 360) |
| MemCHO vs A3 | rate Mbit/s | 14.236 -> 14.261, 0.025 [0.016, 0.034], 0.2%, p = 0.82 (n = 360) | 14.196 -> 14.261, 0.065 [0.058, 0.072], 0.5%, p = 8.5e-109 (n = 360) |
| MemCHO vs A3 | delivered share | 0.9882 -> 0.9899, 0.0017 [0.0011, 0.0023], 0.2%, p = 0.84 (n = 360) | 0.9854 -> 0.9899, 0.0045 [0.0040, 0.0049], 0.5%, p = 8.5e-109 (n = 360) |

Baselines themselves, before -> after (pooled means): A3 UHO 0.514 -> 0.328, failures 0.0069 -> 0.0100, prepared 0.000 -> 0.000; CHO UHO 0.397 -> 0.209, failures 0.0053 -> 0.0204, prepared 0.165 -> 0.287
before, H1 criteria MemCHO vs CHO: (a) UHO lower: diff -0.078, Holm p 2.1e-21 -> holds; (b) failures not higher: upper end -0.0020 vs margin 0.0037 -> holds; (c) prepared set smaller: diff 0.060, Holm p 6.7e-93 -> does not hold

after, H1 criteria MemCHO vs CHO: (a) UHO lower: diff 0.110, Holm p 7.9e-84 -> does not hold; (b) failures not higher: upper end -0.0130 vs margin 0.0037 -> holds; (c) prepared set smaller: diff -0.062, Holm p 4.4e-27 -> holds


### X3 street grid, chi 1 (9 conditions x 20 seeds)

| comparison | endpoint | before: ref -> MemCHO, diff [95 %], p | after: ref -> MemCHO, diff [95 %], p |
|---|---|---|---|
| MemCHO vs CHO | unnecessary HO | 0.195 -> 0.125, -0.071 [-0.086, -0.055], -36.1%, p = 1.3e-27 (n = 180) | 0.150 -> 0.125, -0.025 [-0.036, -0.013], -16.6%, p = 0.01 (n = 180) |
| MemCHO vs CHO | failures | 0.0278 -> 0.0199, -0.0079 [-0.0140, -0.0018], -28.4%, p = 0.0043 (n = 180) | 0.0480 -> 0.0199, -0.0281 [-0.0354, -0.0209], -58.6%, p = 3.6e-14 (n = 180) |
| MemCHO vs CHO | prepared cells | 0.161 -> 0.251, 0.090 [0.077, 0.103], 55.9%, p = 5.8e-48 (n = 180) | 0.136 -> 0.251, 0.116 [0.099, 0.132], 85.2%, p = 2.6e-54 (n = 180) |
| MemCHO vs CHO | rate Mbit/s | 14.018 -> 14.168, 0.150 [0.118, 0.183], 1.1%, p = 4e-17 (n = 180) | 14.068 -> 14.168, 0.100 [0.081, 0.119], 0.7%, p = 1.6e-18 (n = 180) |
| MemCHO vs CHO | delivered share | 0.9688 -> 0.9791, 0.0103 [0.0082, 0.0125], 1.1%, p = 2.4e-17 (n = 180) | 0.9723 -> 0.9791, 0.0069 [0.0056, 0.0081], 0.7%, p = 7.7e-19 (n = 180) |
| MemCHO vs A3 | unnecessary HO | 0.387 -> 0.125, -0.263 [-0.308, -0.217], -67.8%, p = 2.6e-54 (n = 180) | 0.387 -> 0.125, -0.263 [-0.308, -0.217], -67.8%, p = 2.6e-54 (n = 180) |
| MemCHO vs A3 | failures | 0.0345 -> 0.0199, -0.0146 [-0.0207, -0.0085], -42.4%, p = 3.3e-07 (n = 180) | 0.0345 -> 0.0199, -0.0146 [-0.0207, -0.0085], -42.4%, p = 3.3e-07 (n = 180) |
| MemCHO vs A3 | prepared cells | 0.000 -> 0.251, 0.251 [0.233, 0.269], n/a%, p = 1.3e-54 (n = 180) | 0.000 -> 0.251, 0.251 [0.233, 0.269], n/a%, p = 1.3e-54 (n = 180) |
| MemCHO vs A3 | rate Mbit/s | 14.213 -> 14.168, -0.045 [-0.057, -0.033], -0.3%, p = 8.8e-14 (n = 180) | 14.213 -> 14.168, -0.045 [-0.057, -0.033], -0.3%, p = 8.8e-14 (n = 180) |
| MemCHO vs A3 | delivered share | 0.9822 -> 0.9791, -0.0031 [-0.0039, -0.0023], -0.3%, p = 8.6e-14 (n = 180) | 0.9822 -> 0.9791, -0.0031 [-0.0039, -0.0023], -0.3%, p = 8.6e-14 (n = 180) |

Baselines themselves, before -> after (pooled means): A3 UHO 0.387 -> 0.387, failures 0.0345 -> 0.0345, prepared 0.000 -> 0.000; CHO UHO 0.195 -> 0.150, failures 0.0278 -> 0.0480, prepared 0.161 -> 0.136
before, H1 criteria MemCHO vs CHO: (a) UHO lower: diff -0.071, Holm p 2.6e-27 -> holds; (b) failures not higher: upper end -0.0018 vs margin 0.0099 -> holds; (c) prepared set smaller: diff 0.090, Holm p 1.7e-47 -> does not hold

after, H1 criteria MemCHO vs CHO: (a) UHO lower: diff -0.025, Holm p 0.01 -> holds; (b) failures not higher: upper end -0.0209 vs margin 0.0099 -> holds; (c) prepared set smaller: diff 0.116, Holm p 7.8e-54 -> does not hold


### O3 open area (3 profiles x 30 seeds)

| comparison | endpoint | before: ref -> MemCHO, diff [95 %], p | after: ref -> MemCHO, diff [95 %], p |
|---|---|---|---|
| MemCHO vs CHO | unnecessary HO | 1.522 -> 1.861, 0.340 [0.314, 0.365], 22.3%, p = 1.6e-27 (n = 90) | 0.258 -> 1.861, 1.603 [1.451, 1.754], 620.1%, p = 1.6e-27 (n = 90) |
| MemCHO vs CHO | failures | 0.1908 -> 0.1704, -0.0204 [-0.0260, -0.0147], -10.7%, p = 4.9e-11 (n = 90) | 0.5112 -> 0.1704, -0.3408 [-0.3643, -0.3172], -66.7%, p = 1.6e-27 (n = 90) |
| MemCHO vs CHO | prepared cells | 0.243 -> 0.395, 0.152 [0.145, 0.159], 62.7%, p = 1.6e-27 (n = 90) | 0.342 -> 0.395, 0.053 [0.045, 0.061], 15.5%, p = 1.6e-27 (n = 90) |
| MemCHO vs CHO | rate Mbit/s | 13.570 -> 13.699, 0.129 [0.108, 0.150], 1.0%, p = 1.6e-27 (n = 90) | 12.878 -> 13.699, 0.821 [0.735, 0.907], 6.4%, p = 1.6e-27 (n = 90) |
| MemCHO vs CHO | delivered share | 0.9437 -> 0.9526, 0.0090 [0.0075, 0.0104], 0.9%, p = 1.6e-27 (n = 90) | 0.8957 -> 0.9526, 0.0570 [0.0512, 0.0627], 6.4%, p = 1.6e-27 (n = 90) |
| MemCHO vs A3 | unnecessary HO | 1.888 -> 1.861, -0.027 [-0.052, -0.001], -1.4%, p = 0.19 (n = 90) | 1.241 -> 1.861, 0.620 [0.586, 0.654], 50.0%, p = 1.6e-27 (n = 90) |
| MemCHO vs A3 | failures | 0.4978 -> 0.1704, -0.3274 [-0.3812, -0.2735], -65.8%, p = 1.6e-27 (n = 90) | 0.3761 -> 0.1704, -0.2057 [-0.2275, -0.1840], -54.7%, p = 1.6e-27 (n = 90) |
| MemCHO vs A3 | prepared cells | 0.000 -> 0.395, 0.395 [0.392, 0.398], n/a%, p = 1.6e-27 (n = 90) | 0.000 -> 0.395, 0.395 [0.392, 0.398], n/a%, p = 1.6e-27 (n = 90) |
| MemCHO vs A3 | rate Mbit/s | 13.545 -> 13.699, 0.154 [0.129, 0.180], 1.1%, p = 1.6e-27 (n = 90) | 13.599 -> 13.699, 0.100 [0.089, 0.111], 0.7%, p = 1.6e-27 (n = 90) |
| MemCHO vs A3 | delivered share | 0.9419 -> 0.9526, 0.0107 [0.0090, 0.0124], 1.1%, p = 1.6e-27 (n = 90) | 0.9457 -> 0.9526, 0.0069 [0.0062, 0.0076], 0.7%, p = 1.6e-27 (n = 90) |

Baselines themselves, before -> after (pooled means): A3 UHO 1.888 -> 1.241, failures 0.4978 -> 0.3761, prepared 0.000 -> 0.000; CHO UHO 1.522 -> 0.258, failures 0.1908 -> 0.5112, prepared 0.243 -> 0.342
before, H1 criteria MemCHO vs CHO: (a) UHO lower: diff 0.340, Holm p 4.8e-27 -> does not hold; (b) failures not higher: upper end -0.0147 vs margin 0.1080 -> holds; (c) prepared set smaller: diff 0.152, Holm p 4.8e-27 -> does not hold

after, H1 criteria MemCHO vs CHO: (a) UHO lower: diff 1.603, Holm p 4.8e-27 -> does not hold; (b) failures not higher: upper end -0.3172 vs margin 0.1080 -> holds; (c) prepared set smaller: diff 0.053, Holm p 4.8e-27 -> does not hold


## 3. S2 at equal failure level, seeds 1-4 (descriptive; settings chosen on these runs)

| failure level (x standard budget) | comparison | before: UHO ref -> new, diff [95 %], p | after |
|---|---|---|---|
| 0.25 | cho vs a3 | 0.435 -> 0.306, -0.129 [-0.219, -0.038], p = 0.0068 (n = 12) | 0.170 -> 0.077, -0.093 [-0.133, -0.054], p = 2.4e-07 (n = 24) |
| 0.25 | memcho vs cho | 0.422 -> 0.304, -0.118 [-0.167, -0.070], p = 9.9e-07 (n = 36) | 0.194 -> 0.304, 0.110 [0.061, 0.159], p = 8.7e-11 (n = 36) |
| 0.25 | pum vs a3 | 0.435 -> 0.644, 0.209 [0.094, 0.323], p = 0.00049 (n = 12) | 0.191 -> 0.644, 0.452 [0.236, 0.669], p = 0.00049 (n = 12) |
| 0.5 | cho vs a3 | 0.455 -> 0.395, -0.060 [-0.083, -0.037], p = 7e-09 (n = 36) | 0.366 -> 0.186, -0.180 [-0.268, -0.092], p = 4.9e-10 (n = 36) |
| 0.5 | memcho vs cho | 0.395 -> 0.284, -0.111 [-0.160, -0.063], p = 2.1e-07 (n = 36) | 0.186 -> 0.284, 0.098 [0.061, 0.135], p = 1.5e-09 (n = 36) |
| 0.5 | pum vs a3 | 0.455 -> 0.650, 0.194 [0.138, 0.251], p = 2.9e-11 (n = 36) | 0.366 -> 0.650, 0.284 [0.202, 0.366], p = 2.9e-11 (n = 36) |
| 1.0 | cho vs a3 | 0.444 -> 0.395, -0.049 [-0.067, -0.030], p = 2.3e-09 (n = 36) | 0.295 -> 0.180, -0.116 [-0.170, -0.062], p = 1.5e-08 (n = 36) |
| 1.0 | memcho vs cho | 0.395 -> 0.284, -0.111 [-0.160, -0.063], p = 2.1e-07 (n = 36) | 0.180 -> 0.284, 0.104 [0.066, 0.143], p = 1.5e-09 (n = 36) |
| 1.0 | pum vs a3 | 0.444 -> 0.627, 0.183 [0.125, 0.242], p = 2.6e-09 (n = 36) | 0.295 -> 0.627, 0.332 [0.242, 0.422], p = 2.9e-11 (n = 36) |
| 2.0 | cho vs a3 | 0.444 -> 0.363, -0.081 [-0.116, -0.045], p = 7e-10 (n = 36) | 0.289 -> 0.176, -0.114 [-0.165, -0.062], p = 1.5e-08 (n = 36) |
| 2.0 | memcho vs cho | 0.363 -> 0.284, -0.079 [-0.115, -0.044], p = 7.6e-06 (n = 36) | 0.176 -> 0.284, 0.108 [0.069, 0.148], p = 1.5e-09 (n = 36) |
| 2.0 | pum vs a3 | 0.444 -> 0.627, 0.183 [0.125, 0.242], p = 2.6e-09 (n = 36) | 0.289 -> 0.627, 0.338 [0.246, 0.429], p = 2.9e-11 (n = 36) |

## 4. S3 sensitivities (10 variants, 12 seeds, frozen standard settings)

| variant | MemCHO vs CHO, UHO change before | after | failures diff before | after | MemCHO vs A3, UHO change before | after |
|---|---|---|---|---|---|---|
| place0 | 17.7 % (0.835 -> 0.983), p = 2.9e-11 | 69.1 % (0.582 -> 0.983), p = 2.9e-11 | -0.0086 [-0.0118, -0.0054], p = 3.6e-06 | -0.0429 [-0.0657, -0.0200], p = 0.0022 | -12.8 % (1.128 -> 0.983), p = 1.7e-05 | 14.3 % (0.861 -> 0.983), p = 2.9e-11 |
| place50 | 8.5 % (0.751 -> 0.815), p = 0.00021 | 59.3 % (0.512 -> 0.815), p = 8.7e-11 | -0.0072 [-0.0100, -0.0045], p = 2.4e-06 | -0.0352 [-0.0544, -0.0160], p = 0.0058 | -17.1 % (0.984 -> 0.815), p = 2.7e-05 | 8.0 % (0.755 -> 0.815), p = 7.8e-08 |
| noclutter | 4.6 % (0.937 -> 0.981), p = 0.56 | 112.4 % (0.462 -> 0.981), p = 2.8e-05 | -0.0005 [-0.0011, 0.0002], p = 0.11 | -0.0017 [-0.0033, -0.0001], p = 0.026 | -17.0 % (1.182 -> 0.981), p = 2.4e-06 | 14.7 % (0.855 -> 0.981), p = 1.2e-08 |
| chi010 | -3.8 % (1.297 -> 1.248), p = 0.14 | 36.2 % (0.916 -> 1.248), p = 1e-09 | -0.0004 [-0.0009, 0.0001], p = 0.22 | -0.0109 [-0.0195, -0.0023], p = 0.0029 | -19.8 % (1.556 -> 1.248), p = 3.8e-07 | -1.7 % (1.269 -> 1.248), p = 0.35 |
| chi100 | -16.7 % (0.211 -> 0.176), p = 0.0018 | 32.9 % (0.132 -> 0.176), p = 0.0026 | -0.0347 [-0.0466, -0.0228], p = 2.3e-10 | -0.4602 [-0.6265, -0.2938], p = 2.9e-11 | -33.4 % (0.264 -> 0.176), p = 3.6e-06 | 9.5 % (0.161 -> 0.176), p = 0.029 |
| veh30 | -14.2 % (3.757 -> 3.224), p = 1.3e-05 | 16.5 % (2.768 -> 3.224), p = 2.4e-07 | -0.0084 [-0.0265, 0.0097], p = 0.1 | -0.1297 [-0.2221, -0.0374], p = 0.052 | -37.8 % (5.181 -> 3.224), p = 8.3e-07 | -23.4 % (4.206 -> 3.224), p = 1e-05 |
| fc7 | -7.8 % (0.678 -> 0.625), p = 0.016 | 42.3 % (0.439 -> 0.625), p = 4.1e-09 | -0.0032 [-0.0053, -0.0011], p = 0.00048 | -0.0291 [-0.0498, -0.0084], p = 0.00068 | -25.4 % (0.838 -> 0.625), p = 1.1e-06 | -2.7 % (0.643 -> 0.625), p = 0.46 |
| fc15 | -8.5 % (0.689 -> 0.630), p = 0.0064 | 40.8 % (0.448 -> 0.630), p = 2.2e-09 | -0.0030 [-0.0049, -0.0011], p = 0.00033 | -0.0306 [-0.0519, -0.0093], p = 0.0022 | -26.1 % (0.853 -> 0.630), p = 2.8e-07 | -3.6 % (0.654 -> 0.630), p = 0.51 |
| pos15 | -4.5 % (0.683 -> 0.653), p = 0.11 | 47.1 % (0.443 -> 0.653), p = 2.9e-11 | -0.0032 [-0.0054, -0.0010], p = 0.0007 | -0.0299 [-0.0509, -0.0088], p = 0.0009 | -22.8 % (0.845 -> 0.653), p = 1.7e-05 | 0.9 % (0.647 -> 0.653), p = 0.19 |
| long | -11.0 % (0.690 -> 0.614), p = 0.00013 | 37.7 % (0.446 -> 0.614), p = 5.2e-09 | -0.0027 [-0.0045, -0.0009], p = 0.00087 | -0.0301 [-0.0504, -0.0099], p = 0.0049 | -28.1 % (0.854 -> 0.614), p = 8.7e-10 | -6.6 % (0.657 -> 0.614), p = 0.83 |

Generated from the result files by the comparison script of amendment 2; numbers use decimal rounding (half away from zero).
