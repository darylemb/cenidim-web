<template>
  <div class="app-container">
    <DefaultLayout>
      <RouterView />
    </DefaultLayout>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import DefaultLayout from '@/layouts/DefaultLayout.vue';

const auth = useAuthStore();
auth.restoreSession();
</script>
