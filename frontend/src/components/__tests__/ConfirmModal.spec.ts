import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ConfirmModal from '../ConfirmModal.vue';

describe('ConfirmModal.vue', () => {
  it('renders the message', () => {
    const w = mount(ConfirmModal, { props: { message: '¿Eliminar?', loading: false } });
    expect(w.find('.admin-confirm-message').text()).toBe('¿Eliminar?');
  });

  it('renders the title when provided', () => {
    const w = mount(ConfirmModal, {
      props: { message: '¿Eliminar?', loading: false, title: 'Eliminar fonograma' },
    });
    expect(w.find('.admin-confirm-title').text()).toBe('Eliminar fonograma');
  });

  it('does not render the title element when title is empty', () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: false } });
    expect(w.find('.admin-confirm-title').exists()).toBe(false);
  });

  it('emits confirm when the confirm button is clicked (default variant=danger)', async () => {
    const w = mount(ConfirmModal, {
      props: { message: 'x', loading: false, confirmLabel: 'Eliminar' },
    });
    await w.find('.btn-danger').trigger('click');
    expect(w.emitted('confirm')).toHaveLength(1);
  });

  it('emits cancel when the cancel button is clicked', async () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: false } });
    await w.find('.btn-secondary').trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('uses the custom confirmLabel', () => {
    const w = mount(ConfirmModal, {
      props: { message: 'x', loading: false, confirmLabel: 'Sí, guardar' },
    });
    expect(w.find('.btn-danger').text()).toBe('Sí, guardar');
  });

  it('uses the custom cancelLabel', () => {
    const w = mount(ConfirmModal, {
      props: { message: 'x', loading: false, cancelLabel: 'Atrás' },
    });
    expect(w.find('.btn-secondary').text()).toBe('Atrás');
  });

  it('disables the confirm button when loading is true', () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: true } });
    expect((w.find('.btn-danger').element as HTMLButtonElement).disabled).toBe(true);
    // Cancel stays enabled so the user can abort a long delete.
    expect((w.find('.btn-secondary').element as HTMLButtonElement).disabled).toBe(false);
  });

  it('shows the loadingLabel while loading', () => {
    const w = mount(ConfirmModal, {
      props: { message: 'x', loading: true, loadingLabel: 'Eliminando...' },
    });
    expect(w.find('.btn-danger').text()).toBe('Eliminando...');
  });

  it('uses the warning variant class', () => {
    const w = mount(ConfirmModal, {
      props: { message: 'x', loading: false, variant: 'warning' },
    });
    expect(w.find('.btn-warning').exists()).toBe(true);
    expect(w.find('.btn-danger').exists()).toBe(false);
  });

  it('uses the primary variant class', () => {
    const w = mount(ConfirmModal, {
      props: { message: 'x', loading: false, variant: 'primary' },
    });
    expect(w.find('.btn-primary').exists()).toBe(true);
    expect(w.find('.btn-danger').exists()).toBe(false);
  });

  it('defaults to the danger variant', () => {
    const w = mount(ConfirmModal, { props: { message: 'x', loading: false } });
    expect(w.find('.btn-danger').exists()).toBe(true);
  });
});
