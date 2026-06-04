<template>
  <div>
    <AppHeader />
    <main id="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue';
</script>
