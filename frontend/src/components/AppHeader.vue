<template>
  <header class="combined-header">
    <div class="app-header">
      <div class="header-branding">
        <div class="logo-icon-small">C</div>
        <div class="logo-text-small">
          <h2>CENIDIM</h2>
          <span class="sub-text">Archivo Musical</span>
        </div>
      </div>
      <div v-if="user" class="header-user">
        <span class="header-username">{{ user.username }}</span>
        <span :class="['role-badge', `role-${user.role}`]">{{ user.role }}</span>
        <button class="btn-secondary btn-sm" @click="handleLogout">Cerrar</button>
      </div>
      <button v-else class="btn-primary" @click="openAuth">Acceder</button>
    </div>
    <AppNavBar />
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import AppNavBar from '@/components/AppNavBar.vue';

const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();
const user = auth.user;

function handleLogout() {
  auth.logout();
  ui.setActiveTab('timeline');
}

function openAuth() {
  router.push({ name: 'login' });
}
</script>
