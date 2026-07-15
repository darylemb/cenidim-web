import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ConfirmModal from '../ConfirmModal.vue';

describe('ConfirmModal.vue', () => {
  it('renders the message', () => {
    const w = mount(ConfirmModal, { props: { message: '¿Eliminar?', loading: false } });
    expect(w.find('p').text()).toBe('¿Eliminar?');
  });

  it('emits confirm when Eliminar is clicked', async () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: false } });
    await w.find('.btn-danger').trigger('click');
    expect(w.emitted('confirm')).toHaveLength(1);
  });

  it('emits cancel when Cancelar is clicked', async () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: false } });
    await w.find('.btn-secondary').trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('disables the danger button when loading is true', () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: true } });
    expect((w.find('.btn-danger').element as HTMLButtonElement).disabled).toBe(true);
    // Cancel stays enabled so the user can abort a long delete.
    expect((w.find('.btn-secondary').element as HTMLButtonElement).disabled).toBe(false);
  });

  it('shows "Eliminando…" instead of "Eliminar" while loading', () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: true } });
    expect(w.find('.btn-danger').text()).toContain('Eliminando');
  });
});
