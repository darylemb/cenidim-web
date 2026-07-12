<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-icon-small">C</div>
        <div class="logo-text-small">
          <h2>CENIDIM</h2>
          <span class="sub-text">Archivo Musical</span>
        </div>
      </div>

      <div class="auth-tabs">
        <button :class="{ active: mode === 'login' }" @click="mode = 'login'">
          Iniciar Sesión
        </button>
        <button :class="{ active: mode === 'register' }" @click="mode = 'register'">
          Registrarse
        </button>
      </div>

      <div v-if="error" class="auth-error">{{ error }}</div>
      <div v-if="googleError" class="auth-error">{{ googleError }}</div>

      <GoogleSignInButton :unavailable="googleUnavailable" class="auth-google" />

      <div class="auth-divider">
        <span>o</span>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="username">Usuario</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            :autocomplete="mode === 'login' ? 'username' : 'username'"
          />
        </div>
        <div v-if="mode === 'register'" class="form-group">
          <label for="email">Correo</label>
          <input id="email" v-model="email" type="email" required autocomplete="email" />
        </div>
        <div class="form-group">
          <label for="password">Contraseña</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          />
        </div>
        <button type="submit" class="auth-submit" :disabled="loading">
          {{ loading ? 'Cargando...' : mode === 'login' ? 'Acceder' : 'Crear Cuenta' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import GoogleSignInButton from '@/components/GoogleSignInButton.vue';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const mode = ref<'login' | 'register'>('login');
const username = ref('');
const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');
const googleError = ref('');
const googleUnavailable = ref(false);

onMounted(async () => {
  const q = route.query.google
  if (typeof q === 'string' && q.startsWith('err=')) {
    const code = q.substring(4)
    googleError.value = humanizeGoogleError(code)
  } else if (q === 'ok') {
    // Token comes back in the URL fragment to keep it out of server logs.
    const hash = window.location.hash.replace(/^#/, '')
    const params = new URLSearchParams(hash)
    const token = params.get('token')
    const username = params.get('username')
    const role = params.get('role')
    if (token) {
      localStorage.setItem('cenidim_token', token)
      try {
        await auth.refresh()
      } catch {
        // Fall back to the values from the fragment so the user can land
        // somewhere meaningful even if /auth/me is briefly unavailable.
        auth.user = {
          id: Number(params.get('id') ?? 0),
          username: username ?? '',
          email: params.get('email') ?? '',
          role: (role as 'viewer' | 'editor' | 'admin') ?? 'viewer',
        }
      }
      const finalRole = auth.user?.role ?? ((role as 'viewer' | 'editor' | 'admin') ?? 'viewer')
      // Strip the fragment so it is not re-sent on reload.
      router.replace({ name: 'login', query: {}, hash: '' })
      router.push({ name: finalRole === 'admin' ? 'admin' : 'timeline' })
    } else {
      googleError.value = 'Google no devolvió un token. Intenta de nuevo.'
    }
  }

  // Probe the Google start endpoint to see if it's configured. A
  // properly configured endpoint replies with a 302 to Google's consent
  // screen — the browser masks that to status 0 + type 'opaqueredirect'
  // when `redirect: 'manual'`. Anything else (4xx/5xx) means OAuth
  // env vars are missing or the route is misconfigured, so the button
  // should fall back to its disabled state.
  try {
    const ctl = new AbortController()
    const timer = setTimeout(() => ctl.abort(), 1500)
    const res = await fetch('/api/auth/google/start', {
      method: 'GET',
      redirect: 'manual',
      signal: ctl.signal,
    })
    clearTimeout(timer)
    // opaqueredirect → status 0; configured backend also returns 302
    // when the browser is configured to follow it, which is harmless.
    if (res.type !== 'opaqueredirect' && res.status >= 400) {
      googleUnavailable.value = true
    }
  } catch {
    googleUnavailable.value = true
  }
})

function humanizeGoogleError(code: string): string {
  switch (code) {
    case 'state_mismatch':
      return 'La verificación de seguridad de Google falló. Por favor intenta de nuevo.'
    case 'user_cancelled':
      return 'Cancelaste el inicio de sesión con Google.'
    case 'email_not_verified':
      return 'Tu dirección de Gmail no está verificada. Verifícala en Google y vuelve a intentarlo.'
    case 'upstream':
      return 'No pudimos comunicarnos con Google en este momento. Intenta de nuevo o usa tu contraseña.'
    case 'missing_code':
      return 'Google no devolvió un código de autorización. Intenta de nuevo.'
    default:
      return 'No se pudo iniciar la sesión con Google.'
  }
}

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, email.value, password.value)
    }
    router.push({ name: auth.user?.role === 'admin' ? 'admin' : 'timeline' })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error desconocido'
  } finally {
    loading.value = false
  }
}
</script>
