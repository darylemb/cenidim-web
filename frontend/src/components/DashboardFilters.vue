<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFiltersStore } from '@/stores/filters'
import { swatchFor } from '@/config/themes'

const emit = defineEmits<{ change: [] }>()

const filters = useFiltersStore()
const route = useRoute()
const router = useRouter()

// Local mirror of store — kept for two-way binding with debounce.
// Years are tracked as raw strings so the input never "loses" what
// the user typed mid-typing; parseInt-or-null conversion happens at
// commit time. The previous v-model.number + type=number combination
// coerced empty input to an empty string, which Vue replaced with
// the placeholder — making the value appear to vanish between
// blur and re-render.
const localThemesInput = ref<string[]>([])
const localYearFrom = ref<string>('')
const localYearTo = ref<string>('')
const localClasificaciones = ref<string[]>([])
const localAlbum = ref('')
const localQ = ref('')

/**
 * Raw themes come from the `Tema: ...` line at the end of each song in
 * `LetrasTXT/*.txt`. We do NOT infer them via keyword matching — the
 * field is the source of truth (see scripts/classify_songs.py).
 *
 * The chip list is seeded with the most common values from the catalog
 * (pre-computed in the backend and exposed via /api/stats' songs_by_theme
 * when filters are empty). For a brand-new deployment the store can be
 * empty and the user can still type into the album/free-text inputs.
 */
const knownThemes = ref<string[]>([])
// Total distinct themes in the catalog (before the chip cap). Kept
// separate from ``knownThemes`` so the hint can say "24 de 28" instead
// of the misleading "24 temas en catálogo completo" that the review
// (01/jul/2026) flagged — the truncation is a UI choice, not a count.
const totalThemeCount = ref(0)

async function refreshKnownThemes() {
  try {
    const res = await fetch('/api/stats')
    if (!res.ok) return
    const data = await res.json()
    const map = data.songs_by_theme ?? {}
    // Sort by count desc, then alphabetically. Cap to 24 to keep the UI
    // manageable (the long tail of one-off themes can still match via
    // URL deep-linking).
    const entries = (Object.entries(map) as [string, number][])
      .filter(([k]) => k && k.length > 0)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'es'))
    totalThemeCount.value = entries.length
    knownThemes.value = entries.slice(0, 24).map(([k]) => k)
  } catch {
    // network failure — keep what we have
  }
}

const themeHint = computed(() => {
  if (totalThemeCount.value === 0) return ''
  if (knownThemes.value.length < totalThemeCount.value) {
    return `(${knownThemes.value.length} de ${totalThemeCount.value} temas en catálogo completo)`
  }
  return `(${totalThemeCount.value} temas en catálogo completo)`
})

function commitToUrl() {
  const query = filters.toQuery()
  router.replace({ query }).catch(() => {})
}

function applyFilters() {
  filters.themes = [...localThemesInput.value]
  const fromRaw = localYearFrom.value.trim()
  const toRaw = localYearTo.value.trim()
  const from = fromRaw === '' ? null : Number.parseInt(fromRaw, 10)
  const to = toRaw === '' ? null : Number.parseInt(toRaw, 10)
  filters.setYearRange(
    Number.isFinite(from) ? from : null,
    Number.isFinite(to) ? to : null,
  )
  filters.clasificaciones = [...localClasificaciones.value]
  filters.album = localAlbum.value || null
  filters.setQ(localQ.value)
  commitToUrl()
  emit('change')
}

function clearAll() {
  filters.clear()
  syncFromStore()
  commitToUrl()
  emit('change')
}

function syncFromStore() {
  localThemesInput.value = [...filters.themes]
  localYearFrom.value = filters.yearFrom != null ? String(filters.yearFrom) : ''
  localYearTo.value = filters.yearTo != null ? String(filters.yearTo) : ''
  localClasificaciones.value = [...filters.clasificaciones]
  localAlbum.value = filters.album ?? ''
  localQ.value = filters.q
}

onMounted(async () => {
  filters.applyFromQuery(route.query)
  syncFromStore()
  await refreshKnownThemes()
})

watch(
  () => route.query,
  (q) => {
    filters.applyFromQuery(q)
    syncFromStore()
  },
)

function toggleTheme(theme: string) {
  const idx = localThemesInput.value.indexOf(theme)
  if (idx >= 0) {
    localThemesInput.value.splice(idx, 1)
  } else {
    localThemesInput.value.push(theme)
  }
  applyFilters()
}

function toggleNone() {
  if (localThemesInput.value.includes('__none__')) {
    localThemesInput.value = localThemesInput.value.filter((t) => t !== '__none__')
  } else {
    localThemesInput.value.push('__none__')
  }
  applyFilters()
}

function toggleClasificacion(value: string) {
  const idx = localClasificaciones.value.indexOf(value)
  if (idx >= 0) {
    localClasificaciones.value.splice(idx, 1)
  } else {
    localClasificaciones.value.push(value)
  }
  applyFilters()
}

// Debounced auto-apply for the year inputs. The user types a 4-digit
// year, the input fires @input on every keystroke, the timer resets,
// and 300 ms after the last keystroke the filter is committed. Enter
// (keyup.enter) bypasses the debounce and commits immediately.
//
// We accept the Event directly so we can read event.target.value
// (the raw input string) instead of the v-model mirror — which
// only updates on `change` for type=number inputs (the browser
// coerces a `number` v-model to numeric and skips string trim().
let yearDebounceTimer: number | undefined
function _syncFromInputs() {
  // ``localYearFrom`` / ``localYearTo`` are kept in sync with the
  // DOM <input> elements by ``v-model.lazy``. After ``change`` or
  // ``Enter`` they hold the string the user typed (or '' for an
  // empty field). The commit path normalises these to ints.
  applyFilters()
}
function scheduleYearApply() {
  if (yearDebounceTimer != null) {
    window.clearTimeout(yearDebounceTimer)
  }
  yearDebounceTimer = window.setTimeout(() => {
    yearDebounceTimer = undefined
    _syncFromInputs()
  }, 300)
}
function commitYearsNow(e?: Event) {
  if (yearDebounceTimer != null) {
    window.clearTimeout(yearDebounceTimer)
    yearDebounceTimer = undefined
  }
  // On Enter / blur: pull the latest value from the event target
  // before v-model.lazy catches up. That way the commit is
  // immediate, not waiting for the next render to read the
  // (still-stale) localYearFrom.
  if (e && e.target instanceof HTMLInputElement) {
    const t = e.target as HTMLInputElement
    if (t.dataset.which === "yearFrom") {
      localYearFrom.value = t.value
    } else if (t.dataset.which === "yearTo") {
      localYearTo.value = t.value
    }
  }
  _syncFromInputs()
}
onUnmounted(() => {
  if (yearDebounceTimer != null) {
    window.clearTimeout(yearDebounceTimer)
  }
})
</script>

<template>
  <section class="filters" aria-label="Filtros del catálogo">
    <header class="filters__header">
      <div class="filters__title-block">
        <span class="eyebrow">Filtrar el archivo</span>
        <h3 class="filters__title display">Criterios de búsqueda</h3>
      </div>
      <button
        v-if="!filters.isEmpty"
        type="button"
        class="filters__reset"
        @click="clearAll"
      >
        Restablecer
      </button>
    </header>

    <!-- Wrapping the body in a <form> makes Enter commit filters
         globally — pressing Enter in any input below triggers
         applyFilters() (the same handler as a chip click), which
         re-fetches /api/stats with the current local mirror state.
         The @submit.prevent stops the browser from reloading the
         page. We keep the explicit @change / @click handlers on the
         individual fields so they still fire on blur or click. -->
    <form
      class="filters__body"
      @submit.prevent="applyFilters"
    >
      <!-- Year range.
           Reviewer feedback (01/jul/2026) flagged that the "Hasta"
           input appeared to clear itself after blur, leaving the
           value only visible in the "Filtros aplicados" chips below.
           Root cause: v-model.number + number inputs coerce empty
           strings, and our commit-on-blur handler re-renders the
           input with placeholder. We switch to a string v-model,
           parse on commit, and use a clearer placeholder so the user
           can always see what they typed even while the
           dashboard is refetching stats. -->
      <fieldset class="filter-group">
        <legend class="filter-group__legend">Rango de años</legend>
        <div class="filter-group__row">
          <label class="filter-input-wrap">
            <span class="filter-input-label">Desde</span>
            <input
              v-model.lazy="localYearFrom"
              type="number"
              inputmode="numeric"
              min="1900"
              max="2100"
              step="1"
              class="filter-input mono"
              placeholder="1980"
              data-which="yearFrom"
              @input="scheduleYearApply"
              @change="commitYearsNow($event)"
              @keyup.enter="commitYearsNow($event)"
            />
          </label>
          <span class="filter-input-sep" aria-hidden="true">—</span>
          <label class="filter-input-wrap">
            <span class="filter-input-label">Hasta</span>
            <input
              v-model.lazy="localYearTo"
              type="number"
              inputmode="numeric"
              min="1900"
              max="2100"
              step="1"
              class="filter-input mono"
              placeholder="1985"
              data-which="yearTo"
              @input="scheduleYearApply"
              @change="commitYearsNow($event)"
              @keyup.enter="commitYearsNow($event)"
            />
          </label>
        </div>
        <p
          v-if="filters.yearFrom != null || filters.yearTo != null"
          class="filter-group__hint"
          id="year-range-hint"
        >
          Filtro activo: {{ filters.yearFrom ?? '*' }} – {{ filters.yearTo ?? '*' }}
        </p>
      </fieldset>

      <!-- Theme chips — dynamically populated from /api/stats.
           Previously the legend said "X valores del catálogo" which
           could be misread as "X temas distintos en el catálogo". The
           "24 valores del catálogo" hint confused reviewers because
           the KPI strip elsewhere said "33 temas distintos" under a
           filter. We now qualify the hint as "catálogo completo" and
           move the precise count to a dedicated chip-list summary
           line so the user sees the exact taxonomy size and that it
           is the catalog-wide one, not a filter-dependent one. -->
      <fieldset class="filter-group filter-group--wide">
        <legend class="filter-group__legend">
          Tema
          <span v-if="themeHint" class="filter-group__hint">
            {{ themeHint }}
          </span>
        </legend>
        <div v-if="knownThemes.length === 0" class="filter-group__empty">
          Sin temas catalogados. Ejecute
          <code>scripts/classify_songs.py</code> para extraer los
          valores del campo <code>Tema:</code> en
          <code>LetrasTXT/</code>.
        </div>
        <div v-else class="chip-grid" role="group" aria-label="Filtrar por tema">
          <button
            v-for="t in knownThemes"
            :key="t"
            type="button"
            :class="['chip', { 'chip--on': localThemesInput.includes(t) }]"
            :aria-pressed="localThemesInput.includes(t)"
            :title="t"
            @click="toggleTheme(t)"
          >
            <span
              class="chip__dot"
              :style="{ background: swatchFor(t) }"
              aria-hidden="true"
            ></span>
            <span class="chip__label">{{ t }}</span>
          </button>
          <button
            type="button"
            :class="['chip', 'chip--ghost', { 'chip--on': localThemesInput.includes('__none__') }]"
            :aria-pressed="localThemesInput.includes('__none__')"
            @click="toggleNone"
          >
            Sin tema
          </button>
        </div>
      </fieldset>

      <!-- Clasificación -->
      <fieldset class="filter-group">
        <legend class="filter-group__legend">Clasificación de lengua</legend>
        <div class="chip-grid" role="group" aria-label="Filtrar por clasificación">
          <button
            v-for="c in [
              { key: 'ESPAÑOL_ESTANDAR', label: 'Estándar' },
              { key: 'ESPAÑOL_REGIONAL', label: 'Regional' },
              { key: 'LENGUA_INDIGENA', label: 'Indígena' },
            ]"
            :key="c.key"
            type="button"
            :class="['chip', { 'chip--on': localClasificaciones.includes(c.key) }]"
            :aria-pressed="localClasificaciones.includes(c.key)"
            @click="toggleClasificacion(c.key)"
          >
            {{ c.label }}
          </button>
        </div>
      </fieldset>

      <!-- Álbum -->
      <fieldset class="filter-group">
        <legend class="filter-group__legend">Álbum</legend>
        <input
          v-model="localAlbum"
          type="text"
          class="filter-input"
          placeholder="Título del álbum"
          @change="applyFilters"
          @keyup.enter="applyFilters"
        />
      </fieldset>

      <!-- Búsqueda libre -->
      <fieldset class="filter-group filter-group--wide">
        <legend class="filter-group__legend">Búsqueda libre</legend>
        <input
          v-model="localQ"
          type="search"
          class="filter-input"
          placeholder="Palabra en título, álbum o letra"
          @input="applyFilters"
          @keyup.enter="applyFilters"
        />
      </fieldset>
    </form>
  </section>
</template>

<style scoped>
.filters {
  background: var(--color-bg-soft);
  border: var(--hairline);
  padding: var(--space-6) var(--space-7);
  margin-bottom: var(--space-7);
  position: relative;
}

.filters::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: var(--space-7);
  height: 4px;
  background: var(--color-brand);
}

.filters__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: var(--hairline-soft);
  flex-wrap: wrap;
}

.filters__title-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.filters__title {
  font-family: var(--font-display);
  font-size: var(--font-size-2xl);
  font-weight: 400;
  font-variation-settings: 'opsz' 72, 'SOFT' 50, 'WONK' 0;
  color: var(--color-text);
  margin: 0;
  line-height: 1;
}

.filters__reset {
  background: transparent;
  border: var(--hairline);
  color: var(--color-text);
  padding: var(--space-2) var(--space-4);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 500;
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: var(--tap-target-min);
}

.filters__reset:hover {
  background: var(--color-brand);
  color: var(--color-text-inverse);
  border-color: var(--color-brand);
}

.filters__body {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-6) var(--space-7);
}

.filter-group {
  border: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  grid-column: span 6;
}

.filter-group--wide {
  grid-column: span 12;
}

.filter-group__legend {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: 0;
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.filter-group__hint {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
}

.filter-group__empty {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-style: italic;
}

.filter-group__row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.filter-input-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  min-width: 0;
}

.filter-input-label {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.filter-input-sep {
  color: var(--color-text-muted);
  font-family: var(--font-display);
  font-size: var(--font-size-xl);
  padding-top: var(--space-4);
}

.filter-input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: var(--hairline);
  padding: var(--space-2) 0;
  font-family: var(--font-body);
  font-size: var(--font-size-md);
  color: var(--color-text);
  transition: border-color var(--transition-fast);
  min-height: var(--tap-target-min);
}

.filter-input::placeholder {
  color: var(--color-text-muted);
  font-style: italic;
}

.filter-input:hover {
  border-bottom-color: var(--color-border-strong);
}

.filter-input:focus {
  outline: none;
  border-bottom-color: var(--color-brand);
  border-bottom-width: 2px;
  padding-bottom: calc(var(--space-2) - 1px);
}

.filter-input.mono {
  font-family: var(--font-mono);
  font-size: var(--font-size-md);
}

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: var(--hairline);
  border-radius: var(--radius-pill);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 500;
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: var(--tap-target-min);
  user-select: none;
  max-width: 100%;
}

.chip:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-strong);
}

.chip--on {
  background: var(--color-brand);
  color: var(--color-text-inverse);
  border-color: var(--color-brand);
}

.chip--on:hover {
  background: var(--color-brand-dark);
  border-color: var(--color-brand-dark);
}

.chip--ghost {
  font-style: italic;
  border-style: dashed;
}

.chip--ghost.chip--on {
  background: var(--color-ink);
  color: var(--color-text-inverse);
  border-style: solid;
  border-color: var(--color-ink);
}

.chip__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--theme-color-default);
  flex-shrink: 0;
}

.chip__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 16ch;
}

@media (max-width: 768px) {
  .filters {
    padding: var(--space-5) var(--space-5);
  }
  .filters__body {
    grid-template-columns: 1fr;
  }
  .filter-group,
  .filter-group--wide {
    grid-column: span 1;
  }
  .filters__title {
    font-size: var(--font-size-xl);
  }
}
</style>
