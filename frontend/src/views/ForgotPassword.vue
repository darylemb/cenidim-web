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

      <h2 class="auth-title">Recuperar contraseña</h2>
      <p class="auth-lede">
        Escribe el correo con el que te registraste y te enviaremos un
        enlace para restablecer tu contraseña.
      </p>

      <div v-if="error" class="auth-error">{{ error }}</div>
      <div v-if="sent" class="auth-success">
        Si el correo está registrado, recibirás un enlace para
        restablecer tu contraseña. Revisa también la carpeta de correo no
        deseado.
        <template v-if="devLink">
          <br /><br />
          <span class="auth-success__dev">(Enlace de prueba: </span>
          <a :href="devLink" class="auth-success__link">{{ devLink }}</a>
          <span class="auth-success__dev">)</span>
        </template>
      </div>

      <form v-if="!sent" class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="email">Correo</label>
          <input id="email" v-model="email" type="email" required autocomplete="email" />
        </div>
        <button type="submit" class="auth-submit" :disabled="loading">
          {{ loading ? 'Enviando…' : 'Enviar enlace' }}
        </button>
        <router-link class="auth-alt" to="/login">Volver a iniciar sesión</router-link>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { apiService } from '@/services/api';

const email = ref('');
const loading = ref(false);
const error = ref('');
const sent = ref(false);
const devLink = ref('');

async function handleSubmit() {
  error.value = '';
  loading.value = true;
  try {
    const res = await apiService.forgotPassword(email.value);
    sent.value = true;
    // In demo mode the backend includes the reset link in the response
    // so local reviewers can complete the flow without a mail server.
    if (res.dev_link) devLink.value = res.dev_link;
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo enviar el enlace.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-title {
  font-family: var(--font-display);
  font-size: var(--font-size-2xl);
  font-weight: 400;
  margin: var(--space-5) 0 var(--space-2);
}

.auth-lede {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-loose);
  margin: 0 0 var(--space-5);
}

.auth-success {
  background: rgba(75, 128, 104, 0.08);
  border: 1px solid rgba(75, 128, 104, 0.4);
  color: var(--color-text);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-loose);
}

.auth-success__dev {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.auth-success__link {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  color: var(--color-brand);
  word-break: break-all;
}

.auth-alt {
  display: block;
  margin-top: var(--space-4);
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-decoration: underline;
  text-underline-offset: 4px;
}
</style>
