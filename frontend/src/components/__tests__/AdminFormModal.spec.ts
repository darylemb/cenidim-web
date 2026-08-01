import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AdminFormModal from '../AdminFormModal.vue';
import { apiService } from '@/services/api';
import type { Fonograma, Song, User } from '@/types';

// Spy on the service so we don't depend on network.
vi.mock('@/services/api', () => ({
  apiService: {
    adminCreateFonograma: vi.fn(async () => ({})),
    adminUpdateFonograma: vi.fn(async () => ({})),
    adminCreateSong: vi.fn(async () => ({})),
    adminUpdateSong: vi.fn(async () => ({})),
    adminCreateUser: vi.fn((async) => ({})),
    adminUpdateUser: vi.fn(async () => ({})),
  },
}));

function makeWrapper(
  formType: 'fonograma' | 'song' | 'user',
  item: Fonograma | Song | User | null = null
) {
  return mount(AdminFormModal, {
    props: { formType, item },
  });
}

// Click the submit-confirm "Sí, guardar" button after submitting the
// form. Returns nothing; awaits its own flush.
async function confirmPendingSubmit(w: ReturnType<typeof makeWrapper>) {
  await flushPromises();
  const btn = w
    .findAll('.admin-confirm .btn-primary')
    .find((b) => /guardar/i.test(b.text()));
  if (btn) {
    await btn.trigger('click');
  }
  await flushPromises();
}

describe('AdminFormModal.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('renders the correct title per form type', () => {
    expect(makeWrapper('fonograma', null).find('h3').text()).toBe('Agregar Fonograma');
    expect(makeWrapper('song', null).find('h3').text()).toBe('Agregar Canción');
    expect(makeWrapper('user', null).find('h3').text()).toBe('Agregar Usuario');
  });

  it('renders "Editar" prefix when item is provided', () => {
    const item: Fonograma = { clave_fonograma: 1, titulo: 'X' } as Fonograma;
    expect(makeWrapper('fonograma', item).find('h3').text()).toBe('Editar Fonograma');
  });

  it('emits cancel when × is clicked on a clean form', async () => {
    const w = makeWrapper('fonograma', null);
    await w.find('.close-btn').trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('emits cancel when clicking the overlay on a clean form', async () => {
    const w = makeWrapper('fonograma', null);
    await w.find('.modal-overlay').trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('does NOT emit cancel when clicking inside the modal body', async () => {
    const w = makeWrapper('fonograma', null);
    await w.find('.modal-body').trigger('click');
    expect(w.emitted('cancel')).toBeUndefined();
  });

  it('creating a fonograma calls adminCreateFonograma and emits submitted', async () => {
    const w = makeWrapper('fonograma', null);
    // Fill required fields.
    await w.find('#clave_fonograma').setValue('999');
    await w.find('#titulo').setValue('Test Album');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminCreateFonograma).toHaveBeenCalled();
    expect(w.emitted('submitted')).toHaveLength(1);
  });

  it('updating a fonograma calls adminUpdateFonograma', async () => {
    const item: Fonograma = { clave_fonograma: 1, titulo: 'Old' } as Fonograma;
    const w = makeWrapper('fonograma', item);
    await w.find('#titulo').setValue('Updated');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminUpdateFonograma).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ titulo: 'Updated' })
    );
  });

  it('creating a user requires username, email, password', async () => {
    const w = makeWrapper('user', null);
    await w.find('#username').setValue('alice');
    await w.find('#email').setValue('alice@test');
    await w.find('#password').setValue('S3cret!');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminCreateUser).toHaveBeenCalledWith({
      username: 'alice',
      email: 'alice@test',
      password: 'S3cret!',
      role: 'viewer',
    });
  });

  it('updating a user with empty password does not send password', async () => {
    const w = makeWrapper('user', {
      id: 5,
      username: 'bob',
      email: 'b@t',
      role: 'editor',
    });
    await w.find('#username').setValue('bob2');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminUpdateUser).toHaveBeenCalledWith(
      5,
      expect.objectContaining({ username: 'bob2' })
    );
    const call = (apiService.adminUpdateUser as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(call).not.toHaveProperty('password');
  });

  it('shows server error when the API throws', async () => {
    (apiService.adminCreateFonograma as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Bad input')
    );
    const w = makeWrapper('fonograma', null);
    await w.find('#clave_fonograma').setValue('1');
    await w.find('#titulo').setValue('X');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(w.find('.form-error').text()).toContain('Bad input');
  });
});
