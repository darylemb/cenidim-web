# Quickstart: Data Quality & Visualization Fixes

**Feature**: 002-remaining-tasks

## Prerequisites

```bash
# Database must be built
./scripts/build_db.sh

# Dependencies installed
cd frontend && npm install
```

## Verification Commands

### 1. Verify Classification Counts

```bash
sqlite3 backend/letras.db "
SELECT
  (SELECT COUNT(*) FROM songs) as total_songs,
  (SELECT COUNT(*) FROM song_stats WHERE clasificacion = 'ESPAÑOL_ESTANDAR') as estandar,
  (SELECT COUNT(*) FROM song_stats WHERE clasificacion = 'ESPAÑOL_REGIONAL') as regional,
  (SELECT COUNT(*) FROM song_stats WHERE clasificacion = 'LENGUA_INDIGENA') as indigena,
  (SELECT COUNT(*) FROM song_stats WHERE clasificacion IS NULL) as unclassified;
"
```

**Expected output**: All songs classified, sum equals total

### 2. Check s/d Songs

```bash
sqlite3 backend/letras.db "
SELECT COUNT(*) FROM songs WHERE year = 's/d' OR year = '1111';
"
```

### 3. Run Full CI

```bash
./scripts/run_ci_local.sh
```

## Implementation Order

### Step 1: Classification Verification
- Run SQL query
- Document results in checklist

### Step 2: Word Cloud
```bash
cd frontend
npm install vue-wordcloud --legacy-peer-deps
```

### Step 3: Theme Classification
- Modify `scripts/classify_songs.py` to use keyword rules
- Re-run classification

### Step 4: Dashboard Fixes
- Edit `frontend/src/views/DashboardView.vue`
- Filter s/d from charts

### Step 5: Playwright Setup
```bash
cd frontend
npx playwright install --with-deps chromium
npx playwright test
```

## Testing

```bash
# Backend tests
cd backend && go test ./...

# Frontend tests
cd frontend && npm test -- --run

# Playwright E2E
cd frontend && npm run test:e2e

# Full CI
./scripts/run_ci_local.sh
```

## Troubleshooting

**Classification mismatch**: Check `song_stats` table has all songs
**Word cloud not showing**: Verify lyrics exist in database
**Charts showing s/d**: Filter year === 's/d' in stats handler