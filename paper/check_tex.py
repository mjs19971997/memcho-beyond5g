# -*- coding: utf-8 -*-
"""Checks of a compiled manuscript: undefined references or citations, overfull boxes above 2 pt, floats that the
text never refers to, citations without an entry; prints page, word, figure, table and reference counts.

    python check_tex.py <file.tex>          (the .log must be next to it: tectonic --keep-logs)
Exit code 1 if a check fails.
"""
import io, os, re, sys
import fitz

tex_path = sys.argv[1]
base = os.path.splitext(tex_path)[0]
tex = io.open(tex_path, encoding='utf-8').read()
log = io.open(base + '.log', encoding='utf-8', errors='replace').read()
bad = []
for m in re.finditer(r'(LaTeX Warning: (Reference|Citation)[^\n]*undefined[^\n]*)', log):
    bad.append(m.group(1))
for m in re.finditer(r'Overfull \\hbox \(([\d.]+)pt too wide\)([^\n]*)', log):
    if float(m.group(1)) > 2.0:
        bad.append('overfull %s pt %s' % (m.group(1), m.group(2)[:60]))
labels = re.findall(r'\\label\{((?:fig|tab):[^}]*)\}', tex)
refs = set(re.findall(r'\\ref\{([^}]*)\}', tex))
for l in labels:
    if l not in refs:
        bad.append('float never referenced: ' + l)
cites = set(k.strip() for g in re.findall(r'\\cite\{([^}]*)\}', tex) for k in g.split(','))
items = re.findall(r'\\bibitem\{([^}]*)\}', tex)
for k in cites - set(items):
    bad.append('citation without entry: ' + k)
for k in set(items) - cites:
    bad.append('entry never cited: ' + k)
doc = fitz.open(base + '.pdf')
text = '\n'.join(p.get_text() for p in doc)
body = text[:text.rfind('\nReferences')] if '\nReferences' in text else text
abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.S).group(1)
print('%s: pages %d | words (PDF text before the references) %d | abstract words %d | figures %d | tables %d | references %d'
      % (os.path.basename(tex_path), doc.page_count, len(re.findall(r'[A-Za-z0-9]+(?:[-\'][A-Za-z0-9]+)*', body)),
         len(re.sub(r'\$[^$]*\$', 'x', abstract).split()), len(re.findall(r'\\begin\{figure\*?\}', tex)),
         len(re.findall(r'\\begin\{table\*?\}', tex)), len(items)))
for b in bad:
    print('  CHECK FAILED:', b)
sys.exit(1 if bad else 0)
