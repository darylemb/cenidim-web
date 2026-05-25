<template>
  <div>
    <AppHeader />
    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue';
</script>
