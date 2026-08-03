#!/bin/bash
set -e

DB_NAME="letras.db"
DB_TMP="${DB_NAME}.tmp.$$"
DB_FINAL="${DB_NAME}"

cleanup() {
  rm -f "${DB_TMP}"
}
trap cleanup EXIT

echo "Building database from db_fonografia.csv (scripts/build_db.py)..."

# build_db.py needs `bcrypt`; prefer the FastAPI venv, fall back to the
# system python3.
PYTHON="${PYTHON:-python3}"
if ! "${PYTHON}" -c "import bcrypt" 2>/dev/null; then
  if [ -x backend-fastapi/.venv/bin/python ]; then
    PYTHON=backend-fastapi/.venv/bin/python
  fi
fi

if [ -n "${ADMIN_PASS}" ]; then
  "${PYTHON}" scripts/build_db.py \
    --csv db_fonografia.csv \
    --db "${DB_TMP}" \
    --letras LetrasTXT \
    --admin-pass "${ADMIN_PASS}"
else
  "${PYTHON}" scripts/build_db.py \
    --csv db_fonografia.csv \
    --db "${DB_TMP}" \
    --letras LetrasTXT
fi

echo "Classifying songs with spaCy..."
if ! python3 scripts/classify_songs.py --db "${DB_TMP}"; then
  echo "Error: Classification failed. Database not updated."
  exit 1
fi

echo "Normalizing lyrics + themes (normalize_db.py)..."
if ! python3 scripts/normalize_db.py --db "${DB_TMP}" --fix-lyrics-match --letras-dir LetrasTXT; then
  echo "Error: Normalization failed. Database not updated."
  exit 1
fi

if [ -f "${DB_FINAL}" ]; then
  rm -f "${DB_FINAL}.bak"
  cp "${DB_FINAL}" "${DB_FINAL}.bak"
fi

mv "${DB_TMP}" "${DB_FINAL}"

echo "Done."