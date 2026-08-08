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

      <h2 class="auth-title">Crear nueva contraseña</h2>
      <p class="auth-lede">
        Escribe tu nueva contraseña. Después de guardarla podrás
        entrar con ella.
      </p>

      <div v-if="error" class="auth-error">{{ error }}</div>
      <div v-if="done" class="auth-success">
        Tu contraseña se actualizó correctamente. Ya puedes
        <router-link class="auth-success__link" to="/login">iniciar sesión</router-link>.
      </div>

      <form v-if="!done && hasToken" class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="password">Nueva contraseña</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </div>
        <div class="form-group">
          <label for="confirm">Repite la contraseña</label>
          <input
            id="confirm"
            v-model="confirm"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </div>
        <button type="submit" class="auth-submit" :disabled="loading">
          {{ loading ? 'Guardando…' : 'Guardar contraseña' }}
        </button>
      </form>

      <div v-if="!hasToken && !done" class="auth-error">
        El enlace de recuperación no es válido o ya expiró.
        <router-link class="auth-success__link" to="/forgot"
          >Solicita uno nuevo</router-link
        >.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { apiService } from '@/services/api';

const route = useRoute();
const password = ref('');
const confirm = ref('');
const loading = ref(false);
const error = ref('');
const done = ref(false);

const hasToken = computed(() => typeof route.query.token === 'string' && route.query.token.length > 0);

async function handleSubmit() {
  error.value = '';
  if (password.value !== confirm.value) {
    error.value = 'Las contraseñas no coinciden.';
    return;
  }
  loading.value = true;
  try {
    await apiService.resetPassword(String(route.query.token), password.value);
    done.value = true;
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo restablecer la contraseña.';
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

.auth-success__link {
  color: var(--color-brand);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 4px;
}
</style>
