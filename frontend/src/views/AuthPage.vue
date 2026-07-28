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
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();

const mode = ref<'login' | 'register'>('login');
const username = ref('');
const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

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