// LaTeX back end of the third paper (elsarticle).  A reduced copy of code/v8_tex.js of the earlier papers: the same
// helpers (T, P, H, Hsub, fig, table, c, F, TB, E, references, build) and the same text conventions ($math$, *italic*),
// without the IEEE and supplement machinery.  P3_COLS=2 gives the two-column preview.
const fs = require('fs');
const path = require('path');

const JOURNAL = process.env.P3_JOURNAL || 'Computer Networks';      // the single place where the journal is named
const TWO = process.env.P3_COLS === '2';
const HERE = __dirname;
const FIGSRC = path.join(HERE, 'figures');

let REFDB = {};
const setRefs = (db) => { REFDB = db; };

// ---------- cross references ----------
const A = '\u0001', Z = '\u0002';
const refOrder = [];
function c(...keys) {
  keys.forEach((k) => { if (!REFDB[k]) throw new Error('unknown reference ' + k); if (!refOrder.includes(k)) refOrder.push(k); });
  return `${A}cite:${keys.join(',')}${Z}`;
}
const F = (id) => `${A}fig:${id}${Z}`;
const TB = (id) => `${A}tab:${id}${Z}`;
const E = (id) => `${A}eq:${id}${Z}`;
const SEC = (id) => `${A}sec:${id}${Z}`;
function resolve(s) {
  return s.replace(/\u0001(\w+):([^\u0002]*)\u0002/g, (m, kind, v) => (
    kind === 'cite' ? `\\cite{${v}}` : kind === 'fig' ? `Fig.~\\ref{fig:${v}}` : kind === 'tab' ? `Table~\\ref{tab:${v}}`
      : kind === 'sec' ? `Section~\\ref{sec:${v}}` : `(\\ref{eq:${v}})`));
}

// ---------- math mini-language -> LaTeX ----------
const GREEK = { α: '\\alpha', β: '\\beta', γ: '\\gamma', δ: '\\delta', ε: '\\varepsilon', η: '\\eta', θ: '\\theta', κ: '\\kappa',
  λ: '\\lambda', μ: '\\mu', ρ: '\\rho', σ: '\\sigma', τ: '\\tau', φ: '\\varphi', χ: '\\chi', ω: '\\omega', π: '\\pi', Δ: '\\Delta' };
const MSYM = { '∈': '\\in', '≤': '\\le', '≥': '\\ge', '≠': '\\ne', '≈': '\\approx', '←': '\\leftarrow', '→': '\\rightarrow',
  '·': '\\cdot', '×': '\\times', '−': '-', '′': "'", '±': '\\pm', '…': '\\ldots', '–': '-' };
function mathConv(s) {
  s = s.replace(/(\\?)([A-Za-z]{2,}\d*)/g, (m, bs, w) => (bs ? m : `\\mathrm{${w}}`));
  s = s.replace(/[^\x00-\x7F]/g, (ch) => (GREEK[ch] ? GREEK[ch] + ' ' : MSYM[ch] !== undefined ? MSYM[ch] + ' ' : ch));
  return s.replace(/%/g, '\\%').replace(/#/g, '\\#');
}

// ---------- text ----------
const ACC = { á: "\\'a", é: "\\'e", í: "\\'{\\i}", ó: "\\'o", ú: "\\'u", ä: '\\"a', ö: '\\"o', ü: '\\"u', ñ: '\\~n', ç: '\\c{c}', ğ: '\\u{g}',
  ı: '{\\i}', ş: '\\c{s}', è: '\\`e', ł: '{\\l}', ć: "\\'c" };
const TSYM = { '“': '``', '”': "''", '‘': '`', '’': "'", '–': '--', '—': '---', '…': '\\ldots{}', '−': '$-$', '±': '$\\pm$', '×': '$\\times$',
  '≈': '$\\approx$', '≤': '$\\le$', '≥': '$\\ge$', '·': '$\\cdot$', '°': '$^{\\circ}$', '→': '$\\rightarrow$', '\u00a0': '~', '⇒': '$\\Rightarrow$' };
function esc(s) {
  s = s.replace(/\\/g, '\\textbackslash{}').replace(/([{}%&#_])/g, '\\$1').replace(/~/g, '\\textasciitilde{}').replace(/\^/g, '\\textasciicircum{}')
    .replace(/</g, '$<$').replace(/>/g, '$>$').replace(/\|/g, '$|$');
  return s.replace(/[^\x00-\x7F\u0001\u0002]/g, (ch) => (TSYM[ch] !== undefined ? TSYM[ch] : ACC[ch] !== undefined ? ACC[ch] : GREEK[ch] ? `$${GREEK[ch]}$` : ch));
}
function textConv(seg) {
  const urls = [];
  seg = seg.replace(/https?:\/\/[^\s)]+[^\s).,;]/g, (u) => { urls.push(u); return `\u0003${urls.length - 1}\u0003`; });
  const out = seg.split('*').map((t, m) => (m % 2 === 1 ? `\\emph{${esc(t)}}` : esc(t))).join('');
  return out.replace(/\u0003(\d+)\u0003/g, (m, i) => `\\url{${urls[+i]}}`);
}
function T(str) {
  return String(str).split('$').map((seg, k) => (k % 2 === 1 ? `$${mathConv(seg)}$` : textConv(seg))).join('');
}
function sentenceCase(str) {
  const KEEP = /^(MemCHO|CHO|A3|ns|LENA|NR|FR3|Rel|TR|TS)$/;
  let first = true;
  return String(str).split('$').map((seg, k) => (k % 2 === 1 ? seg : seg.replace(/[A-Za-z][A-Za-z0-9]*/g, (w) => {
    const f = first; first = false;
    return (!f && /^[A-Z][a-z]+$/.test(w) && !KEEP.test(w)) ? w.toLowerCase() : w;
  }))).join('$');
}

// ---------- body ----------
const body = [];
const push = (...items) => { items.flat(Infinity).forEach((x) => { if (typeof x === 'string') body.push(x); }); };
function P(text) {
  const t = T(text);
  return `${t}\n\n`;
}
function L(items) { return `\\begin{itemize}\\setlength{\\itemsep}{2pt}\n${items.map((x) => `\\item ${T(x)}`).join('\n')}\n\\end{itemize}\n`; }
const H = (id, title) => `\\section{${T(title)}}\\label{sec:${id}}\n`;
const Hsub = (id, title) => `\\subsection{${T(title)}}\\label{sec:${id}}\n`;
const unnumbered = (title) => `\\section*{${esc(title)}}\n`;

// figures: drawn at a print width in mm (text width 165 mm)
const figsUsed = [];
function fig(id, name, caption, mm = 165, spec = '!t') {
  figsUsed.push(name);
  const star = TWO && mm > 100 ? '*' : '';
  const width = TWO ? (mm > 100 ? `${Math.min(1, mm / 178).toFixed(2)}\\textwidth` : '\\columnwidth') : `${Math.min(1, mm / 165).toFixed(2)}\\textwidth`;
  return `\\begin{figure${star}}[${spec}]\n\\centering\n\\includegraphics[width=${width}]{figures/${name}.pdf}\n\\caption{${T(caption)}}\n\\label{fig:${id}}\n\\end{figure${star}}\n`;
}

// display equations, hand-set
let EQS = {};
const setEqs = (e) => { EQS = e; };
function EQ(id) {
  const e = EQS[id];
  if (!e) throw new Error('no LaTeX for equation ' + id);
  const t = typeof e === 'string' ? e : (TWO ? e.n : e.w);
  return `\\begin{equation}\\label{eq:${id}}\n${t}\n\\end{equation}\n`;
}

// tables: booktabs, paragraph columns from relative widths
function table(id, caption, rel, head, rows, o = {}) {
  const wide = TWO ? (o.wide !== false) : true;
  const star = TWO && wide ? '*' : '';
  const sum = rel.reduce((a, b) => a + b, 0);
  const left = o.left || [0];
  const total = TWO && !wide ? '\\columnwidth' : (o.frac ? `${o.frac}\\textwidth` : '\\textwidth');
  const cols = rel.map((r, i) => `>{${left.includes(i) ? '\\raggedright' : '\\centering'}\\arraybackslash}p{\\dimexpr ${(r / sum).toFixed(4)}\\tblw-2\\tabcolsep\\relax}`).join('');
  const size = o.size || (rel.length >= 8 ? '\\scriptsize' : '\\footnotesize');
  const cellT = (v) => String(v).split('$').map((seg, k) => (k % 2 === 1 ? `$${mathConv(seg)}$` : textConv(seg))).join('');
  const hl = o.hl || [];
  const lines = rows.map((r, ri) => {
    if (r === '---') return '\\midrule';
    if (typeof r === 'string') return `\\multicolumn{${rel.length}}{@{}l}{\\textit{${T(r)}}} \\\\`;
    const cells = r.map((v, i) => { const t = cellT(v); return hl.includes(ri) && t ? `\\textbf{${t}}` : t; });
    return `${cells.join(' & ')} \\\\`;
  });
  let groups = '';
  if (o.groups) {
    let col = 1; const cm = [];
    groups = o.groups.map(([lab, span]) => { const a = col, b = col + span - 1; col += span; if (lab) cm.push(`\\cmidrule(lr){${a}-${b}}`);
      return `\\multicolumn{${span}}{c}{${T(lab)}}`; }).join(' & ') + ` \\\\\n${cm.join('')}\n`;
  }
  const note = o.note ? `\n\\par\\vspace{3pt}\\parbox{\\tblw}{\\footnotesize ${T(o.note)}}` : '';
  return `\\begin{table${star}}[${o.spec || '!t'}]\n\\centering\n\\caption{${T(caption)}}\n\\label{tab:${id}}\n\\vspace{2pt}\n${size}\\setlength{\\tabcolsep}{3pt}\\setlength{\\tblw}{${total}}\n`
    + `\\begin{tabular}{@{}${cols}@{}}\n\\toprule\n${groups}${head.map((h) => cellT(h)).join(' & ')} \\\\\n\\midrule\n${lines.join('\n')}\n\\bottomrule\n\\end{tabular}${note}\n\\end{table${star}}\n`;
}

// ---------- front matter, references, output ----------
let front = '';
function frontmatter(title, abstract, keywords, highlights) {
  const kw = keywords.map((k) => esc(k));
  front = `\\begin{frontmatter}
\\title{${T(title)}}
\\author[iau]{Mostafa Jalili Sanjarani}
\\author[iau]{Yasser Elmi Sola\\corref{cor}}
\\ead{Yasser.Elmi@iau.ac.ir}
\\author[iau]{Hesam Hasanpour}
\\author[iau]{Ali Akbar Neghabi}
\\cortext[cor]{Corresponding author.}
\\affiliation[iau]{organization={Department of Computer Engineering, Sab.C., Islamic Azad University}, city={Sabzevar}, country={Iran}}
\\begin{abstract}
${T(abstract)}
\\end{abstract}
${highlights ? `\\begin{highlights}\n${highlights.map((h) => `\\item ${T(h)}`).join('\n')}\n\\end{highlights}\n` : ''}\\begin{keyword}
${kw.join(' \\sep ')}
\\end{keyword}
\\end{frontmatter}
`;
}
function refConv(s) {
  const urls = [];
  s = s.replace(/https?:\/\/\S+/g, (u) => { urls.push(u.replace(/[.,]$/, '')); return `${A}url:${urls.length - 1}${Z}`; });
  s = s.replace(/doi: (\S+?)\.?$/, (m, d) => { urls.push(d); return `${A}doi:${urls.length - 1}${Z}`; });
  s = esc(s);
  return s.replace(/\u0001url:(\d+)\u0002/g, (m, i) => `\\url{${urls[+i]}}`).replace(/\u0001doi:(\d+)\u0002/g, (m, i) => `doi:\\href{https://doi.org/${urls[+i]}}{\\nolinkurl{${urls[+i]}}}.`);
}

function build(outFile, title) {
  const dir = path.dirname(outFile);
  fs.mkdirSync(dir + '/figures', { recursive: true });
  [...new Set(figsUsed)].forEach((n) => fs.copyFileSync(`${FIGSRC}/${n}.pdf`, `${dir}/figures/${n}.pdf`));
  const doc = resolve(body.join(''));
  const bib = `\\begin{thebibliography}{${refOrder.length}}\n\\footnotesize\n${refOrder.map((k) => `\\bibitem{${k}} ${refConv(REFDB[k])}`).join('\n')}\n\\end{thebibliography}\n`;
  const cls = TWO ? 'final,5p,times,twocolumn' : 'final,3p,times';
  const tex = `%% ${title}
%% ${JOURNAL} (elsarticle).  Compile with pdfLaTeX (twice).  Generated by build_p3.js; do not edit by hand.
\\documentclass[${cls}]{elsarticle}
\\usepackage[T1]{fontenc}
\\usepackage{amsmath,amssymb}
\\usepackage{graphicx}
\\usepackage{booktabs,array}
\\usepackage[hidelinks]{hyperref}
\\usepackage{url}
\\urlstyle{same}
\\newlength{\\tblw}
\\journal{${JOURNAL}}
\\biboptions{numbers,sort&compress}
\\begin{document}
${front}
${doc}
${bib}
\\end{document}
`;
  const left = [...new Set(tex.match(/[^\x00-\x7F]/g) || [])];
  if (left.length) throw new Error('non-ASCII characters left in the LaTeX source: ' + left.join(' '));
  fs.writeFileSync(outFile, tex, 'utf8');
  console.log('WROTE', outFile, tex.length, '| refs', refOrder.length, '| figures', new Set(figsUsed).size);
}

module.exports = { JOURNAL, TWO, setRefs, setEqs, c, F, TB, E, SEC, T, P, L, H, Hsub, unnumbered, fig, EQ, table, frontmatter, build, push, refOrder, esc };
