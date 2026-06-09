#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="${1:-.}"
BATCH_SIZE="${BATCH_SIZE:-40}"
OUT_DIR="${OUT_DIR:-review-reports/code-review-$(date +%Y%m%d-%H%M%S)}"
DRY_RUN="${DRY_RUN:-0}"

if ! command -v opencode >/dev/null 2>&1; then
  echo "Error: opencode no esta instalado o no esta en PATH."
  exit 1
fi

if [[ ! "$BATCH_SIZE" =~ ^[0-9]+$ ]] || [[ "$BATCH_SIZE" -le 0 ]]; then
  echo "Error: BATCH_SIZE debe ser un entero positivo."
  exit 1
fi

mkdir -p "$OUT_DIR"

SUMMARY_CSV="$OUT_DIR/summary.csv"
SUMMARY_MD="$OUT_DIR/summary.md"
FILE_LIST_TXT="$OUT_DIR/files.txt"

echo "batch,status,exit_code,file_count,output_file" > "$SUMMARY_CSV"

# Excluye directorios de build/dependencias para mantener la revision enfocada.
FILES=()
while IFS= read -r -d '' file; do
  FILES+=("$file")
done < <(
  find "$ROOT_DIR" \
    \( -name .git -o -name node_modules -o -name dist -o -name coverage -o -name .cache -o -name .opencode -o -name LetrasTXT -o -name .playwright-mcp -o -name bin \) -prune -o \
    -type f \
    \( -name '*.go' -o -name '*.ts' -o -name '*.vue' -o -name '*.js' -o -name '*.py' -o -name '*.sh' -o -name '*.sql' \) \
    -print0
)

TOTAL="${#FILES[@]}"

if [[ "$TOTAL" -eq 0 ]]; then
  echo "No se encontraron archivos para revisar en $ROOT_DIR"
  exit 0
fi

printf '%s\n' "${FILES[@]}" > "$FILE_LIST_TXT"

BATCH_COUNT=$(( (TOTAL + BATCH_SIZE - 1) / BATCH_SIZE ))

echo "Iniciando revision de $TOTAL archivos en $BATCH_COUNT lotes."
echo "Salida en: $OUT_DIR"

echo "=== Lote 0: audit_design_tokens.sh (sin LLM) ==="
audit_output="$OUT_DIR/batch_000_audit.log"
if bash scripts/audit_design_tokens.sh frontend/src 0.05 > "$audit_output" 2>&1; then
  echo "audit,ok,0,1,$audit_output" >> "$SUMMARY_CSV"
  echo "  OK: design-token audit passed"
else
  audit_exit=$?
  echo "audit,failed,$audit_exit,1,$audit_output" >> "$SUMMARY_CSV"
  echo "  FAIL: design-token audit (see $audit_output)"
fi

for ((idx=0; idx<TOTAL; idx+=BATCH_SIZE)); do
  batch_num=$((idx / BATCH_SIZE + 1))
  padded_batch_num=$(printf "%03d" "$batch_num")

  BATCH=("${FILES[@]:idx:BATCH_SIZE}")
  batch_file_count="${#BATCH[@]}"
  output_file="$OUT_DIR/batch_${padded_batch_num}.log"

  echo "[$batch_num/$BATCH_COUNT] Revisando $batch_file_count archivos..."

  if [[ "$DRY_RUN" == "1" ]]; then
    {
      echo "DRY RUN"
      printf "Files: %s\n" "${BATCH[@]}"
    } > "$output_file"
    echo "$batch_num,skipped,0,$batch_file_count,$output_file" >> "$SUMMARY_CSV"
    continue
  fi

  set +e
  opencode run /code-review "${BATCH[@]}" --agent reviewer > "$output_file" 2>&1
  exit_code=$?
  set -e

  if [[ "$exit_code" -eq 0 ]]; then
    status="ok"
  else
    status="failed"
  fi

  echo "$batch_num,$status,$exit_code,$batch_file_count,$output_file" >> "$SUMMARY_CSV"
done

ok_count=$(awk -F',' 'NR>1 && $2=="ok" {c++} END {print c+0}' "$SUMMARY_CSV")
failed_count=$(awk -F',' 'NR>1 && $2=="failed" {c++} END {print c+0}' "$SUMMARY_CSV")
skipped_count=$(awk -F',' 'NR>1 && $2=="skipped" {c++} END {print c+0}' "$SUMMARY_CSV")

{
  echo "# Code Review Summary"
  echo
  echo "- Root: $ROOT_DIR"
  echo "- Total archivos: $TOTAL"
  echo "- Lotes: $BATCH_COUNT"
  echo "- OK: $ok_count"
  echo "- Failed: $failed_count"
  echo "- Skipped: $skipped_count"
  echo
  echo "## Archivos"
  echo
  echo "Listado completo en: $FILE_LIST_TXT"
  echo
  echo "## Lotes"
  echo
  echo "Detalle CSV: $SUMMARY_CSV"
} > "$SUMMARY_MD"

echo "Revision finalizada."
echo "Resumen: $SUMMARY_MD"
echo "Detalle: $SUMMARY_CSV"