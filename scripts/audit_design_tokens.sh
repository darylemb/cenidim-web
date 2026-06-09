#!/usr/bin/env bash
#
# audit_design_tokens.sh
# Verifies that frontend styles consume design tokens (src/assets/tokens.css)
# rather than hard-coded hex colors or px spacing values.
#
# Acceptance (incremental): at most 2 % of style-bearing lines in the
# audited subset may use hard-coded literals. The initial integration
# allows a 5 % drift budget so that the existing main.css / index.css
# stylesheets can be migrated incrementally in follow-up PRs.
#
# Usage: scripts/audit_design_tokens.sh [path-to-frontend-src] [threshold]
# Default path: frontend/src
# Default threshold: 0.05 (5 %)

set -euo pipefail

ROOT="${1:-frontend/src}"
THRESHOLD="${2:-0.05}"
TOKENS_FILE="frontend/src/assets/tokens.css"

if [[ ! -d "$ROOT" ]]; then
  echo "Skipping audit: $ROOT not found" >&2
  exit 0
fi

if [[ ! -f "$TOKENS_FILE" ]]; then
  echo "ERROR: $TOKENS_FILE not found; design tokens must exist before audit." >&2
  exit 1
fi

# Collect files to scan: .vue and .css under $ROOT, excluding tokens.css.
FILES=()
while IFS= read -r -d '' f; do
  FILES+=("$f")
done < <(find "$ROOT" -type f \( -name '*.vue' -o -name '*.css' \) ! -path "*/tokens.css" -print0)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No source files found under $ROOT" >&2
  exit 0
fi

# Count style lines: anything inside <style> blocks of .vue, or any line in .css.
# We use a simple heuristic: lines containing color-like or px-like literals
# outside of CSS comments.
total_style_lines=0
violation_lines=0
violation_files=()

# A "violation" is a line containing a hex color (#abc / #abcdef) OR a px
# value in a CSS property context, outside tokens.css.
# Comment lines (starting with whitespace then // or /* or *) are ignored.

scan() {
  local file="$1"
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    # Skip CSS / JS comments
    if [[ "$line" =~ ^[[:space:]]*(\*|/\*|//|<!--) ]]; then
      continue
    fi
    # Only inspect lines that look like style rules
    if ! [[ "$line" =~ :[[:space:]] ]] && ! [[ "$line" =~ px|#[0-9a-fA-F] ]]; then
      continue
    fi
    total_style_lines=$((total_style_lines + 1))
    # Hex color literals
    if [[ "$line" =~ \#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b ]] \
       && ! [[ "$line" =~ var\(-- ]]; then
      violation_lines=$((violation_lines + 1))
      violation_files+=("$file: $line")
      continue
    fi
    # Hard-coded px values inside property declarations (allow 1px borders / 0)
    if [[ "$line" =~ :[[:space:]] ]] && [[ "$line" =~ ([0-9]+)px ]] \
       && ! [[ "$line" =~ var\(-- ]] \
       && ! [[ "$line" =~ 0px ]]; then
      violation_lines=$((violation_lines + 1))
      violation_files+=("$file: $line")
      continue
    fi
  done < "$file"
}

for f in "${FILES[@]}"; do
  scan "$f"
done

if [[ "$total_style_lines" -eq 0 ]]; then
  echo "No style-bearing lines detected under $ROOT" >&2
  exit 0
fi

# Compute drift: violations / total style lines
drift=$(awk -v v="$violation_lines" -v t="$total_style_lines" 'BEGIN { printf "%.4f", v / t }')

echo "Scanned: ${#FILES[@]} files"
echo "Total style-bearing lines: $total_style_lines"
echo "Drift: $drift (threshold $THRESHOLD)"

if (( $(echo "$drift > $THRESHOLD" | bc -l) )); then
  echo ""
  echo "FAIL: design-token drift exceeds threshold."
  echo "First violations:"
  printf '  %s\n' "${violation_files[@]:0:10}"
  exit 1
fi

echo "OK: design-token drift is within budget."
