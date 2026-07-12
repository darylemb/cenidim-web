<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    unavailable?: boolean
  }>(),
  { unavailable: false },
)

const isUnavailable = ref(props.unavailable)

// The parent toggles `unavailable` after an async probe of the Google
// start endpoint. Without this watcher, the local ref would stay at its
// initial value (false) and the button would never flip to its disabled
// state when the probe completes.
watch(
  () => props.unavailable,
  (val) => {
    isUnavailable.value = val
  },
)

onMounted(() => {
  // The Google Identity Services script is loaded on the login page only.
  // We don't render the official button here because the official button
  // would call back into the GIS SDK and bypass our state cookie. Instead
  // we link directly to the backend's /api/auth/google/start endpoint, which
  // sets the state cookie and redirects to Google. This keeps the CSRF
  // protection local to our backend and avoids loading the GIS SDK on pages
  // that don't need it.
})
</script>

<template>
  <a
    v-if="!isUnavailable"
    href="/api/auth/google/start"
    class="google-signin tap-target"
    aria-label="Continuar con Google"
  >
    <span class="google-signin__icon" aria-hidden="true">
      <svg viewBox="0 0 18 18" width="18" height="18" focusable="false">
        <path
          fill="#4285F4"
          d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"
        />
        <path
          fill="#34A853"
          d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.32A9 9 0 0 0 9 18z"
        />
        <path
          fill="#FBBC05"
          d="M3.96 10.71a5.4 5.4 0 0 1 0-3.42V4.97H.96a9 9 0 0 0 0 8.06l3-2.32z"
        />
        <path
          fill="#EA4335"
          d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A9 9 0 0 0 .96 4.97l3 2.32C4.68 5.16 6.66 3.58 9 3.58z"
        />
      </svg>
    </span>
    <span class="google-signin__label">Continuar con Google</span>
  </a>
  <button
    v-else
    type="button"
    class="google-signin google-signin--unavailable tap-target"
    disabled
    aria-label="Continuar con Google (no disponible temporalmente)"
  >
    <span class="google-signin__icon" aria-hidden="true">⚠</span>
    <span class="google-signin__label">Google (temporalmente no disponible)</span>
  </button>
</template>

<style scoped>
.google-signin {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: var(--font-size-md);
  text-decoration: none;
  cursor: pointer;
  transition: var(--transition-fast);
  min-height: var(--tap-target-min);
}
.google-signin:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border-strong);
}
.google-signin--unavailable {
  cursor: not-allowed;
  color: var(--color-text-muted);
}
.google-signin__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
}
</style>
