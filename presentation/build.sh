#!/usr/bin/env bash
# Compile the QAOA MaxCut presentation deck.
# Runs pdflatex twice so the metropolis progress bar and any refs settle.
set -euo pipefail

cd "$(dirname "$0")"
DECK="qaoa_maxcut_presentation"

pdflatex -interaction=nonstopmode -halt-on-error "$DECK.tex" >/tmp/latex1.log
pdflatex -interaction=nonstopmode -halt-on-error "$DECK.tex" >/tmp/latex2.log

# Keep the build dir clean — we only want the PDF.
rm -f "$DECK."{aux,log,nav,out,snm,toc,vrb}

echo "OK: $(pwd)/$DECK.pdf  ($(wc -c <"$DECK.pdf" | tr -d ' ') bytes)"
