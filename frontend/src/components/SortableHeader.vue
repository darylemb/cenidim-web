<template>
  <th class="sortable-th" @click="$emit('sort', col.key)">
    {{ col.label }}
    <span :class="['sort-arrow', { 'sort-active': sortKey === col.key }]">
      {{ sortKey === col.key ? (sortDir === 'asc' ? '▲' : '▼') : '▲' }}
    </span>
  </th>
</template>

<script setup lang="ts">
defineProps<{
  col: { key: string; label: string };
  sortKey: string;
  sortDir: 'asc' | 'desc';
}>();

defineEmits<{ (e: 'sort', _key: string): void }>(); // eslint-disable-line no-unused-vars
</script>
