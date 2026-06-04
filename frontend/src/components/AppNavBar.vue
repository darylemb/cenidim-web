<template>
  <nav class="main-nav">
    <div class="nav-left">
      <button class="menu-toggle" :aria-expanded="mobileMenuOpen" @click="toggleMobileMenu">
        <span class="hamburger-icon"></span>
      </button>
      <div :class="['nav-links', { open: mobileMenuOpen }]">
        <button
          v-for="tab in tabs"
          :key="tab.name"
          :class="['nav-tab', { active: activeTab === tab.name }]"
          @click="navigate(tab.name)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>
    <div :class="['nav-search', { open: mobileMenuOpen }]">
      <select v-model="searchFieldModel" class="nav-field-select">
        <option value="all">Todos</option>
        <option value="title">Pista</option>
        <option value="album">Álbum</option>
        <option value="lyrics">Letra</option>
      </select>
      <input
        v-model="searchTerm"
        type="text"
        placeholder="Buscar canciones..."
        @keyup.enter="doSearch"
      />
      <div class="nav-search-actions">
        <button class="nav-action-btn" @click="doSearch">Buscar</button>
        <button class="nav-btn-reset" @click="doReset">Reset</button>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUiStore } from '@/stores/ui';
import { useSearchStore } from '@/stores/search';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';

const router = useRouter();
const ui = useUiStore();
const search = useSearchStore();
const auth = useAuthStore();
const { mobileMenuOpen, activeTab } = storeToRefs(ui);

const searchTerm = ref('');
const searchFieldModel = computed({
  get: () => search.field,
  set: (val) => { search.field = val; }
});

const tabs = [
  { name: 'timeline' as const, label: 'Línea de tiempo' },
  { name: 'canciones' as const, label: 'Canciones' },
  { name: 'dashboards' as const, label: 'Dashboards' },
  { name: 'admin' as const, label: 'Admin' },
];

function toggleMobileMenu() {
  ui.toggleMobileMenu();
}

function navigate(tab: typeof activeTab.value) {
  if (tab === 'admin' && !auth.isAuthenticated) {
    router.push({ name: 'login' });
    return;
  }
  ui.setActiveTab(tab);
  router.push({ name: tab });
  toggleMobileMenu();
}

function doSearch() {
  ui.setActiveTab('canciones');
  router.push({ name: 'canciones' });
  search.performSearch(searchTerm.value, search.field, 1, search.limit);
}

function doReset() {
  searchTerm.value = '';
  search.resetSearch();
}
</script>