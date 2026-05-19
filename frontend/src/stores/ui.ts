import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUiStore = defineStore('ui', () => {
  const activeTab = ref<'timeline' | 'canciones' | 'dashboards' | 'admin'>('timeline');
  const mobileMenuOpen = ref(false);
  const showAuth = ref(false);

  function setActiveTab(tab: typeof activeTab.value) {
    activeTab.value = tab;
  }

  function toggleMobileMenu() {
    mobileMenuOpen.value = !mobileMenuOpen.value;
  }

  function openAuth() {
    showAuth.value = true;
  }

  function closeAuth() {
    showAuth.value = false;
  }

  return {
    activeTab,
    mobileMenuOpen,
    showAuth,
    setActiveTab,
    toggleMobileMenu,
    openAuth,
    closeAuth,
  };
});
