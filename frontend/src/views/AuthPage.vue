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

      <!--
        Google OAuth se movió al panel admin (AdminUserForm →
        "Vincular cuenta Google"). Los usuarios normales ahora
        ingresan solo con password y pueden recuperar la contraseña
        desde "¿Olvidaste tu contraseña?".
      -->

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
        <button
          v-if="mode === 'login'"
          type="button"
          class="auth-link"
          @click="showForgot = true"
        >
          ¿Olvidaste tu contraseña?
        </button>
      </form>

      <div v-if="showForgot" class="auth-modal-overlay" @click.self="showForgot = false">
        <div class="auth-modal" role="dialog" aria-labelledby="forgot-title">
          <h3 id="forgot-title">Recuperar contraseña</h3>
          <p class="auth-modal-hint">
            Te enviaremos un enlace por email si la cuenta existe. En modo demo
            el enlace se imprime en la consola del backend
            (busca <code>DEV EMAIL OUTBOX</code> en los logs de Coolify).
          </p>
          <div v-if="forgotError" class="auth-error">{{ forgotError }}</div>
          <div v-if="forgotSuccess" class="auth-success">
            Si la cuenta existe, te enviamos un email con instrucciones.
          </div>
          <form @submit.prevent="handleForgot">
            <div class="form-group">
              <label for="forgot-email">Correo</label>
              <input
                id="forgot-email"
                v-model="forgotEmail"
                type="email"
                required
                autocomplete="email"
              />
            </div>
            <div class="auth-modal-actions">
              <button type="button" class="btn-secondary" @click="showForgot = false">Cerrar</button>
              <button type="submit" class="btn-primary" :disabled="forgotLoading">
                {{ forgotLoading ? 'Enviando…' : 'Enviar enlace' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { apiService } from '@/services/api';

const router = useRouter();
const auth = useAuthStore();

const mode = ref<'login' | 'register'>('login');
const username = ref('');
const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const showForgot = ref(false);
const forgotEmail = ref('');
const forgotError = ref('');
const forgotSuccess = ref(false);
const forgotLoading = ref(false);

// Google OAuth se movió al panel admin. Esta vista ya no captura el
// callback ?google=ok|err=... — la única ruta de OAuth es el flujo
// admin "Vincular cuenta Google" en AdminUserForm.

async function handleForgot() {
  forgotError.value = ''
  forgotSuccess.value = false
  forgotLoading.value = true
  try {
    await apiService.forgotPassword(forgotEmail.value)
    // The backend always returns 200 to avoid user enumeration, so we
    // always show the success message regardless of whether the email
    // was actually registered.
    forgotSuccess.value = true
    forgotEmail.value = ''
  } catch (e: unknown) {
    forgotError.value = e instanceof Error ? e.message : 'Error al enviar el enlace'
  } finally {
    forgotLoading.value = false
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
