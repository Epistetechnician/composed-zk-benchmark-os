#!/bin/sh
set -eu

paper_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$paper_dir/build"
output_pdf="$paper_dir/../../../output/pdf/evidence-bounded-ai.pdf"

mkdir -p "$build_dir"
cd "$paper_dir"

fiziko_dir="$build_dir/fiziko"
fiziko_commit="54a63dba8e6700a5e70d3508838edebcbf0f45fe"
fiziko_url="https://github.com/jemmybutton/fiziko.git"
if [ ! -f "$fiziko_dir/fiziko.mp" ] || [ "$(git -C "$fiziko_dir" rev-parse HEAD 2>/dev/null || true)" != "$fiziko_commit" ]; then
  rm -rf "$fiziko_dir"
  git clone --filter=blob:none --no-checkout "$fiziko_url" "$fiziko_dir"
  git -C "$fiziko_dir" checkout --detach "$fiziko_commit"
fi

lualatex -interaction=nonstopmode -halt-on-error -output-directory="$build_dir" evidence-bounded-ai.tex
biber --input-directory="$build_dir" --output-directory="$build_dir" evidence-bounded-ai
lualatex -interaction=nonstopmode -halt-on-error -output-directory="$build_dir" evidence-bounded-ai.tex
lualatex -interaction=nonstopmode -halt-on-error -output-directory="$build_dir" evidence-bounded-ai.tex

mkdir -p "$(dirname -- "$output_pdf")"
cp "$build_dir/evidence-bounded-ai.pdf" "$output_pdf"
pdfinfo "$output_pdf" | sed -n '1,18p'
