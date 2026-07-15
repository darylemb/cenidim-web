import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUiStore } from '../ui';

describe('ui store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('starts with timeline tab and closed mobile menu', () => {
    const ui = useUiStore();
    expect(ui.activeTab).toBe('timeline');
    expect(ui.mobileMenuOpen).toBe(false);
    expect(ui.showAuth).toBe(false);
  });

  it('setActiveTab updates the tab', () => {
    const ui = useUiStore();
    ui.setActiveTab('dashboards');
    expect(ui.activeTab).toBe('dashboards');
    ui.setActiveTab('admin');
    expect(ui.activeTab).toBe('admin');
  });

  it('toggleMobileMenu flips the flag', () => {
    const ui = useUiStore();
    ui.toggleMobileMenu();
    expect(ui.mobileMenuOpen).toBe(true);
    ui.toggleMobileMenu();
    expect(ui.mobileMenuOpen).toBe(false);
  });

  it('openAuth sets showAuth to true', () => {
    const ui = useUiStore();
    ui.openAuth();
    expect(ui.showAuth).toBe(true);
  });

  it('closeAuth sets showAuth to false', () => {
    const ui = useUiStore();
    ui.showAuth = true;
    ui.closeAuth();
    expect(ui.showAuth).toBe(false);
  });
});
