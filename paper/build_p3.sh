#!/bin/bash
# Third paper: derived numbers -> figures -> LaTeX (single column + two-column preview) -> checks
# [-> submission documents -> packages, when those scripts are present].
#     bash build_p3.sh [nofig] [nopack]
# Tools are taken from PATH unless given:  PY, NODE, TECTONIC, SOFFICE (and LO_PROFILE, a LibreOffice profile URL).
# Output folder: P3_OUT (default ./out).  Journal: P3_JOURNAL (default in p3_tex.js).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
PY=${PY:-python}
N=${NODE:-node}
TEC=${TECTONIC:-tectonic}
SOFFICE=${SOFFICE:-soffice}
OUT=${P3_OUT:-$HERE/out}
export PYTHONIOENCODING=utf-8 MPLBACKEND=Agg
NAME=MemCHO_B5G
winpath() { if command -v cygpath > /dev/null; then cygpath -w "$1"; else echo "$1"; fi; }
mkdir -p "$OUT"
if [ "$1" != "nofig" ]; then $PY derive.py; $PY p3_figs.py; fi
$N build_p3.js "$OUT/$NAME.tex"
P3_COLS=2 $N build_p3.js "$OUT/${NAME}_2col.tex"
cd "$OUT"
for f in $NAME ${NAME}_2col; do
  $TEC -X compile $f.tex --outdir . --keep-logs > /dev/null 2>&1 || { echo "tectonic failed on $f"; exit 1; }
  $PY "$HERE/check_tex.py" $f.tex
done
rm -f *.aux *.out
# figures as separate files, numbered in the order of the manuscript (vector PDF and 600-dpi PNG)
mkdir -p figure_files; rm -f figure_files/Figure_*
i=0
for f in $(grep -o 'includegraphics\[[^]]*\]{figures/[a-z0-9_]*' $NAME.tex | sed 's/.*figures\///'); do
  i=$((i+1)); cp "$HERE/figures/$f.pdf" figure_files/Figure_$i.pdf; cp "$HERE/figures/$f.png" figure_files/Figure_$i.png
done
echo "figure files: $i"
cd "$HERE"
if [ -f build_submission_p3.js ]; then
  $N build_submission_p3.js "$OUT"
  LOPT=(); [ -n "$LO_PROFILE" ] && LOPT=(-env:UserInstallation=$LO_PROFILE)
  "$SOFFICE" --headless --norestore "${LOPT[@]}" --convert-to pdf:writer_pdf_Export --outdir "$(winpath "$OUT")" "$(winpath "$OUT/Cover_Letter.docx")" > /dev/null 2>&1
  [ -f "$OUT/Cover_Letter.pdf" ] || { echo "cover letter PDF missing"; exit 1; }
fi
if [ "$2" != "nopack" ] && [ -f build_packages_p3.py ]; then $PY build_packages_p3.py "$(winpath "$OUT")"; fi
echo BUILT_P3
