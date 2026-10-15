// References of the third paper.  Every entry was checked on 2026-10-15: DOIs against the Crossref record
// (refcheck/crossref.json, written by refcheck/fetch.py), arXiv entries against their abstract page, 3GPP documents
// against the 3GPP portal or the entry already checked for the group's earlier papers (code/refs7.js), and the one
// repository entry against its landing page.  Numbering follows the order of first citation in build_p3.js.
module.exports = {
  // --- the group
  jalili1: 'M. Jalili Sanjarani, Y. Elmi Sola, H. Hasanpour, A. A. Neghabi, Handover reduction in 5G mobile networks using ensemble learning method, Sci. Rep. (2026), doi: 10.1038/s41598-026-73269-1.',
  // --- conditional handover
  martikainen: 'H. Martikainen, I. Viering, A. Lobinger, T. Jokela, On the basics of conditional handover for 5G mobility, in: Proc. IEEE 29th Annu. Int. Symp. Personal, Indoor and Mobile Radio Communications (PIMRC), 2018, pp. 1–7, doi: 10.1109/PIMRC.2018.8580946.',
  stanczak: 'J. Stanczak, U. Karabulut, A. Awada, Conditional handover in 5G – principles, future use cases and FR2 performance, in: Proc. Int. Wireless Communications and Mobile Computing Conf. (IWCMC), 2022, pp. 660–665, doi: 10.1109/IWCMC55113.2022.9824571.',
  iqbal22: 'S. B. Iqbal, A. Awada, U. Karabulut, I. Viering, P. Schulz, G. P. Fettweis, On the modeling and analysis of fast conditional handover for 5G-Advanced, in: Proc. IEEE 33rd Annu. Int. Symp. Personal, Indoor and Mobile Radio Communications (PIMRC), 2022, pp. 595–601, doi: 10.1109/PIMRC54779.2022.9977719.',
  iqbal23: 'S. B. Iqbal, S. Nadaf, A. Awada, U. Karabulut, P. Schulz, G. P. Fettweis, On the analysis and optimization of fast conditional handover with hand blockage for mobility, IEEE Access 11 (2023) 30040–30056, doi: 10.1109/ACCESS.2023.3260630.',
  prado: 'A. Prado, H. Vijayaraghavan, W. Kellerer, ECHO: Enhanced conditional handover boosted by trajectory prediction, in: Proc. IEEE Global Communications Conf. (GLOBECOM), 2021, pp. 1–6, doi: 10.1109/GLOBECOM46510.2021.9685348.',
  lee: 'C. Lee, H. Cho, S. Song, J.-M. Chung, Prediction-based conditional handover for 5G mm-wave networks: A deep-learning approach, IEEE Veh. Technol. Mag. 15 (1) (2020) 54–62, doi: 10.1109/MVT.2019.2959065.',
  sundararaju: 'S. C. Sundararaju, S. Ramamoorthy, D. P. Basavaraj, V. Phanindhar, Advanced conditional handover in 5G and beyond using Q-learning, in: Proc. IEEE Wireless Communications and Networking Conf. (WCNC), 2024, pp. 1–6, doi: 10.1109/WCNC57260.2024.10570840.',
  chomet: 'M. Kalntis, F. A. Kuipers, G. Iosifidis, CHOMET: Conditional handovers via meta-learning, arXiv:2507.07581, 2025. https://arxiv.org/abs/2507.07581',
  deb: 'S. Deb, M. Rathod, R. Balamurugan, S. K. Ghosh, R. K. Singh, S. Sanyal, Performance evaluation of conditional handover in 5G systems under fading scenario, arXiv:2403.04379, 2024. https://arxiv.org/abs/2403.04379',
  awada: 'A. Awada, B. Wegmann, I. Viering, A. Klein, A location-based self-optimizing algorithm for the inter-RAT handover parameters, in: Proc. IEEE Int. Conf. Communications (ICC), 2013, pp. 6168–6173, doi: 10.1109/ICC.2013.6655592.',
  // --- lower-layer mobility, upper mid-band
  gundogan: 'A. Gündogan, A. Badalıoglu, P. Spapis, A. Awada, On the modelling and performance analysis of lower layer mobility in 5G-Advanced, arXiv:2211.02725, 2022. https://arxiv.org/abs/2211.02725',
  khodapanah: 'B. Khodapanah, S. Goyal, M. Gursu, J. Stanczak, A. Kakkavas, R. Temelli, A. Badalioglu, P. Spapis, C. Majumdar, On L1/L2-triggered mobility in 3GPP Release 18 and beyond, IEEE Access 12 (2024) 171790–171806, doi: 10.1109/ACCESS.2024.3491500.',
  kang: 'S. Kang, M. Mezzavilla, S. Rangan, A. Madanayake, S. B. Venkatakrishnan, G. Hellbourg, M. Ghosh, H. Rahmani, A. Dhananjay, Cellular wireless networks in the upper mid-band, IEEE Open J. Commun. Soc. 5 (2024) 2058–2075, doi: 10.1109/OJCOMS.2024.3373368.',
  shakya: 'D. Shakya, M. Ying, T. S. Rappaport, et al., Urban outdoor propagation measurements and channel models at 6.75 GHz FR1(C) and 16.95 GHz FR3 upper mid-band spectrum for 5G and 6G, arXiv:2410.17539, 2024. https://arxiv.org/abs/2410.17539',
  poddar: 'H. Poddar, D. Gold, D. Lee, N. Zhang, G. Sridharan, H. Asplund, M. Shafi, Overview of 3GPP Release 19 study on channel modeling enhancements to TR 38.901 for 6G, arXiv:2507.19266, 2025. https://arxiv.org/abs/2507.19266',
  altmeyer: 'C. Altmeyerhenzien, L. Simić, M. Petrova, The price of the golden 6G band: Evaluation of beam management effort in FR3, arXiv:2609.16839, 2026. https://arxiv.org/abs/2609.16839',
  // --- ultra-dense networks, surveys
  arshad: 'R. Arshad, H. ElSawy, S. Sorour, T. Y. Al-Naffouri, M.-S. Alouini, Handover management in 5G and beyond: A topology aware skipping approach, IEEE Access 4 (2016) 9073–9081, doi: 10.1109/ACCESS.2016.2642538.',
  tayyab: 'M. Tayyab, X. Gelabert, R. Jäntti, A survey on handover management: From LTE to NR, IEEE Access 7 (2019) 118907–118930, doi: 10.1109/ACCESS.2019.2937405.',
  mollel: 'M. S. Mollel, A. I. Abubakar, M. Ozturk, S. F. Kaijage, M. Kisangiri, S. Hussain, M. A. Imran, Q. H. Abbasi, A survey of machine learning applications to handover management in 5G and beyond, IEEE Access 9 (2021) 45770–45802, doi: 10.1109/ACCESS.2021.3067503.',
  // --- specifications
  ts38300: '3GPP, NR; NR and NG-RAN overall description; Stage 2 (Release 18), TS 38.300, V18.11.0, 2026.',
  ts38331: '3GPP, NR; Radio Resource Control (RRC); Protocol specification (Release 18), TS 38.331, V18.11.0, 2026.',
  tr38901: '3GPP, Study on channel model for frequencies from 0.5 to 100 GHz (Release 18), TR 38.901, V18.0.0, 2024.',
  tr36839: '3GPP, Evolved Universal Terrestrial Radio Access (E-UTRA); Mobility enhancements in heterogeneous networks (Release 11), TR 36.839, V11.1.0, 2012.',
  tr36842: '3GPP, Study on small cell enhancements for E-UTRA and E-UTRAN; Higher layer aspects (Release 12), TR 36.842, V12.0.0, 2013.',
  tr37885: '3GPP, Study on evaluation methodology of new Vehicle-to-Everything (V2X) use cases for LTE and NR (Release 15), TR 37.885, V15.3.0, 2019.',
  // --- tools and models
  ns3: 'G. F. Riley, T. R. Henderson, The ns-3 network simulator, in: K. Wehrle, M. Güneş, J. Gross (Eds.), Modeling and Tools for Network Simulation, Springer, Berlin, 2010, pp. 15–34, doi: 10.1007/978-3-642-12331-3_2.',
  lena: 'N. Patriciello, S. Lagen, B. Bojovic, L. Giupponi, An E2E simulator for 5G NR networks, Simul. Model. Pract. Theory 96 (2019) 101933, doi: 10.1016/j.simpat.2019.101933.',
  gudmundson: 'M. Gudmundson, Correlation model for shadow fading in mobile radio systems, Electron. Lett. 27 (23) (1991) 2145–2146, doi: 10.1049/el:19911328.',
  siomina: 'I. Siomina, D. Yuan, Analysis of cell load coupling for LTE network planning and optimization, IEEE Trans. Wireless Commun. 11 (6) (2012) 2287–2297, doi: 10.1109/TWC.2012.051512.111532.',
  // --- 2026 handover studies read for Section 2.5 (Review_6G_Handover/papers.csv)
  s26zhao: 'L. Zhao, Z. Fei, X. Wang, N. Ha, Y. Wang, Y. Zeng, R. Zhang, Intelligent beamforming and handover via physics-informed beam-aware CKM diffusion, arXiv:2609.34704, 2026. https://arxiv.org/abs/2609.34704',
  s26mansour: 'A. Mansour, H. Hussein, M. Albert, N. Elsharkawy, M. Shalma, DDPG-based intelligent handover for STAR-RIS-assisted 6G networks, arXiv:2609.33468, 2026. https://arxiv.org/abs/2609.33468',
  s26aslam: 'M. Z. Aslam, A. Raza, Y. A. Bangash, S. Aslam, A. Ali, F. Hassan, Performance characterization of millimeter-wave networked sensing systems under high-mobility constraints for 6G Industrial IoT, Sci. Rep. (2026), doi: 10.1038/s41598-026-71553-8.',
  s26lindenschmitt: 'D. Lindenschmitt, H. D. Schotten, Atomic handover for 6G nomadic non-public networks using edge-based spectrum brokering, in: Proc. IEEE 37th Int. Symp. Personal, Indoor and Mobile Radio Communications (PIMRC), 2026, pp. 1–6, doi: 10.1109/pimrc69400.2026.11711444.',
  s26afif: 'Y. Afif, A. Balakrishnan, P. Martins, M. Almekhlafi, A. Lesage-Landry, G. Karabulut Kurt, Multi-agent reinforcement learning for joint handover management and power allocation in multi-orbit satellite networks, arXiv:2608.14335, 2026. https://arxiv.org/abs/2608.14335',
  s26mahadasu: 'S. S. Mahadasu, N. Safavi, ISAC aware AI-RAN orchestration for mission-critical mobility and intelligent infrastructure in 6G networks, Int. J. AI Electron. Nexus Energy 2 (2) (2026) 956–962, doi: 10.64751/264n8122.',
  s26chenge: 'L. K. Chenge, C. T. Nyah, E. O. Ataro, Robust high-speed train handover optimization using velocity-adaptive fuzzy logic in 5G/B5G networks, Eng. Technol. Appl. Sci. Res. 16 (3) (2026) 35836–35847, doi: 10.48084/etasr.18362.',
  s26moreno: 'A. Y. Moreno-Locubiche, J. Vidal, O. Muñoz-Medina, M. Cabrera-Bean, Contextual bandits and reconfigurable intelligent surfaces for predictive LTM handover decisions, in: Proc. IEEE Int. Conf. Communications (ICC), 2026, pp. 1–7, doi: 10.1109/icc59461.2026.11587432.',
  s26mahenthiran: 'P. Mahenthiran, D. Muruganandam, A DBSAHO scheme for smooth movement in heterogeneous network-based distributed mobility systems, Front. Comput. Sci. 8 (2026) 1818011, doi: 10.3389/fcomp.2026.1818011.',
  s26banerjee: 'A. Banerjee, D. A. Awan, Inductive latent context persistence: Closing the post-handover cold start in 6G radio access networks, arXiv:2605.00593, 2026. https://arxiv.org/abs/2605.00593',
  s26li: 'Y. Li, Y. Zhou, Y. Hu, Z. Ji, J. Zhou, L. Zhou, Y. Liu, T. Q. S. Quek, Seamless handover in direct-to-device satellite networks: From an interference-aware perspective, arXiv:2603.00470, 2026. https://arxiv.org/abs/2603.00470',
  s26garde: 'K. Garde, Federated reinforcement learning for optimized spectrum and mobility management in 5G NR networks, Int. J. Artif. Intell. Mach. Learn. 6 (12s) (2026) 118–129, doi: 10.51483/ijaiml.6.12s.2026.118-129.',
  s26aouedi: 'O. Aouedi, T. S. Abdu, K. H. Nguyen, E. Lagunas, J. Querol, J. Grotz, Intelligent handover management for hybrid TN–NTN mobility in 6G architectures, accepted manuscript, 2026. https://orbilu.uni.lu/handle/10993/69015',
  s26kalntis: 'M. Kalntis, G. Iosifidis, J. Suárez-Varela, A. Lutu, F. A. Kuipers, Meta-learning-based handover management in NextG O-RAN, IEEE J. Sel. Areas Commun. 44 (2026) 3251–3267, doi: 10.1109/jsac.2026.3652037.',
  s26wasilewska: 'M. Wasilewska, M. Sybis, Vertical handover between terrestrial and satellite links in 6G-and-beyond systems: An ML-based method, in: Proc. XXXVIth URSI General Assembly and Scientific Symposium (GASS), 2026, doi: 10.46620/ursigass26/auan6063.',
};
