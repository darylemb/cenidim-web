import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { nextTick } from 'vue';
import AdminFormModal from '../AdminFormModal.vue';
import { apiService } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiService: {
    adminCreateFonograma: vi.fn().mockResolvedValue({ clave_fonograma: 99, titulo: 'New' }),
    adminUpdateFonograma: vi.fn().mockResolvedValue({ clave_fonograma: 1, titulo: 'Updated' }),
    adminCreateSong: vi.fn().mockResolvedValue({ id: 99, title: 'New' }),
    adminUpdateSong: vi.fn().mockResolvedValue({ message: 'Song updated' }),
    adminCreateUser: vi.fn().mockResolvedValue({
      user: { id: 1, username: 'new', email: 'new@x', role: 'viewer' },
    }),
    adminUpdateUser: vi.fn().mockResolvedValue({ message: 'User updated' }),
  },
}));

function makeWrapper(props: Record<string, unknown> = {}) {
  return mount(AdminFormModal, {
    props: { formType: 'fonograma', item: null, ...props },
  });
}

// After submit, the modal shows a confirmation. Click the confirm
// button (the btn-primary of the ConfirmModal) to actually fire the
// API call. We find the right button by its label.
async function confirmPendingSubmit(w: ReturnType<typeof makeWrapper>) {
  await flushPromises();
  const confirmBtn = w
    .findAll('.admin-confirm .btn-primary')
    .find((b) => /guardar/i.test(b.text()));
  if (!confirmBtn) {
    // Find any confirm modal that's open
    const openConfirm = w.find('.admin-confirm');
    if (openConfirm.exists()) {
      await openConfirm.find('.btn-primary').trigger('click');
    }
  } else {
    await confirmBtn.trigger('click');
  }
  await flushPromises();
}

describe('AdminFormModal.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the right title for each form type', () => {
    expect(makeWrapper({ formType: 'fonograma' }).find('h3').text()).toBe('Agregar Fonograma');
    expect(makeWrapper({ formType: 'song' }).find('h3').text()).toBe('Agregar Canción');
    expect(makeWrapper({ formType: 'user' }).find('h3').text()).toBe('Agregar Usuario');
  });

  it('shows "Editar" prefix when item is provided', () => {
    expect(
      makeWrapper({ formType: 'fonograma', item: { clave_fonograma: 1 } })
        .find('h3')
        .text()
    ).toBe('Editar Fonograma');
  });

  it('emits cancel when × is clicked on a clean (just-opened) form', async () => {
    const w = makeWrapper();
    await w.find('.close-btn').trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('does not emit cancel when clicking inside the modal body', async () => {
    const w = makeWrapper();
    await w.find('.modal-body').trigger('click');
    expect(w.emitted('cancel')).toBeUndefined();
  });

  it('creating a fonograma calls adminCreateFonograma (after confirm)', async () => {
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('99');
    await w.find('#titulo').setValue('Nuevo');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminCreateFonograma).toHaveBeenCalledWith(
      expect.objectContaining({ clave_fonograma: 99, titulo: 'Nuevo' })
    );
    expect(w.emitted('submitted')).toBeTruthy();
  });

  it('updating a fonograma calls adminUpdateFonograma (after confirm)', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 7, titulo: 'Old' },
    });
    await w.find('#titulo').setValue('Updated');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminUpdateFonograma).toHaveBeenCalledWith(
      7,
      expect.objectContaining({ titulo: 'Updated' })
    );
  });

  it('creating a song requires fonograma_id + title + lyrics', async () => {
    const w = makeWrapper({ formType: 'song' });
    await w.find('#fonograma_id').setValue('5');
    await w.find('#title').setValue('NewSong');
    await w.find('#lyrics').setValue('Some lyrics here');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminCreateSong).toHaveBeenCalledWith(
      expect.objectContaining({
        fonograma_id: 5,
        title: 'NewSong',
        lyrics: 'Some lyrics here',
      })
    );
  });

  it('updating a song calls adminUpdateSong', async () => {
    const w = makeWrapper({
      formType: 'song',
      item: { id: 3, fonograma_id: 5, title: 'Old', lyrics: 'old lyrics' },
    });
    await w.find('#title').setValue('UpdatedSong');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminUpdateSong).toHaveBeenCalledWith(
      3,
      expect.objectContaining({ title: 'UpdatedSong' })
    );
  });

  it('creating a user requires username + email + password', async () => {
    const w = makeWrapper({ formType: 'user' });
    await w.find('#username').setValue('newuser');
    await w.find('#email').setValue('new@x');
    await w.find('#password').setValue('S3cret!');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminCreateUser).toHaveBeenCalledWith({
      username: 'newuser',
      email: 'new@x',
      password: 'S3cret!',
      role: 'viewer',
    });
  });

  it('updating a user does not send password when blank', async () => {
    const w = makeWrapper({
      formType: 'user',
      item: { id: 5, username: 'old', email: 'old@x', role: 'editor' },
    });
    await w.find('#username').setValue('newer');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(apiService.adminUpdateUser).toHaveBeenCalledWith(
      5,
      expect.objectContaining({ username: 'newer' })
    );
  });

  it('shows server error when the API throws', async () => {
    vi.mocked(apiService.adminCreateFonograma).mockRejectedValueOnce(new Error('Bad input'));
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('1');
    await w.find('#titulo').setValue('X');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    expect(w.find('.form-error').text()).toContain('Bad input');
  });

  it('disables submit button while loading', async () => {
    vi.mocked(apiService.adminCreateFonograma).mockImplementation(() => new Promise(() => {}));
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('1');
    await w.find('#titulo').setValue('X');
    await w.find('form').trigger('submit.prevent');
    await confirmPendingSubmit(w);
    const submitBtn = w.find('button[type="submit"]');
    expect((submitBtn.element as HTMLButtonElement).disabled).toBe(true);
  });

  it('cancelling a dirty form shows a confirm modal', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 1, titulo: 'Old' },
    });
    await w.find('#titulo').setValue('Changed');
    // Click the in-form "Cancelar" button (not the close ×).
    const cancelBtn = w.findAll('button').find((b) => b.text() === 'Cancelar');
    expect(cancelBtn).toBeTruthy();
    await cancelBtn!.trigger('click');
    expect(w.find('.admin-confirm').exists()).toBe(true);
    expect(w.find('.admin-confirm-title').text()).toBe('Cambios sin guardar');
    expect(w.emitted('cancel')).toBeUndefined();
  });

  it('confirming the dirty-cancel prompt emits cancel', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 1, titulo: 'Old' },
    });
    await w.find('#titulo').setValue('Changed');
    const cancelBtn = w.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancelBtn!.trigger('click');
    // Find the dirty-cancel confirm: warning variant, "Salir sin guardar"
    const warningBtns = w.findAll('.admin-confirm .btn-warning');
    expect(warningBtns.length).toBeGreaterThan(0);
    await warningBtns[0].trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('dismissing the dirty-cancel prompt keeps the form open', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 1, titulo: 'Old' },
    });
    await w.find('#titulo').setValue('Changed');
    const cancelBtn = w.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancelBtn!.trigger('click');
    await flushPromises();
    // Find the dirty-cancel confirm by its warning title; inside it,
    // the "Seguir editando" button is the secondary one.
    const confirms = w.findAll('.admin-confirm');
    expect(confirms.length).toBeGreaterThan(0);
    const dirtyConfirm = confirms.find(
      (c) => c.find('.admin-confirm-title').exists() &&
        /Cambios sin guardar/.test(c.find('.admin-confirm-title').text())
    );
    expect(dirtyConfirm).toBeTruthy();
    const seguitBtn = dirtyConfirm!.find('.btn-secondary');
    await seguitBtn.trigger('click');
    expect(w.find('.admin-confirm').exists()).toBe(false);
    expect(w.emitted('cancel')).toBeUndefined();
    // The change must still be in the form
    expect((w.find('#titulo').element as HTMLInputElement).value).toBe('Changed');
  });

  it('closing a clean form with × does not show the dirty prompt', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 1, titulo: 'Old' },
    });
    await w.find('.close-btn').trigger('click');
    expect(w.find('.admin-confirm').exists()).toBe(false);
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('the submit-confirm prompt does not fire the API on cancel', async () => {
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('99');
    await w.find('#titulo').setValue('Nuevo');
    await w.find('form').trigger('submit.prevent');
    await flushPromises();
    // The submit-confirm modal should be visible
    expect(w.find('.admin-confirm').exists()).toBe(true);
    // Click "Volver" (the cancel-side button on the submit-confirm)
    const volverBtn = w.findAll('.admin-confirm .btn-secondary').find((b) =>
      /volver/i.test(b.text())
    );
    await volverBtn!.trigger('click');
    expect(apiService.adminCreateFonograma).not.toHaveBeenCalled();
  });

  it('the create submit-confirm names the new item', async () => {
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('99');
    await w.find('#titulo').setValue('Disco prueba');
    await w.find('form').trigger('submit.prevent');
    await flushPromises();
    const text = w.find('.admin-confirm-message').text();
    expect(text).toContain('Vas a crear');
    expect(text).toContain('clave 99');
    expect(text).toContain('"Disco prueba"');
  });

  it('the edit submit-confirm lists the modified fields', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 7, titulo: 'Old' },
    });
    await w.find('#titulo').setValue('New title');
    await w.find('#anio').setValue('1982');
    await w.find('form').trigger('submit.prevent');
    await flushPromises();
    const text = w.find('.admin-confirm-message').text();
    expect(text).toContain('Vas a actualizar');
    expect(text).toContain('clave 7');
    expect(text).toContain('"Old"');
    expect(text).toContain('Campos modificados');
    expect(text).toContain('Título');
    expect(text).toContain('Año');
  });

  it('the dirty-cancel prompt names the changed fields', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 12, titulo: 'Original' },
    });
    await w.find('#titulo').setValue('Cambiado');
    await w.find('#pais_edicion').setValue('México');
    const cancelBtn = w.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancelBtn!.trigger('click');
    await flushPromises();
    const text = w.find('.admin-confirm-message').text();
    expect(text).toContain('clave 12');
    expect(text).toContain('"Original"');
    expect(text).toContain('Título');
    expect(text).toContain('País de edición');
  });

  it('edit on a user form lists role/email in the confirm, never password', async () => {
    const w = makeWrapper({
      formType: 'user',
      item: { id: 1, username: 'old', email: 'old@x', role: 'viewer' },
    });
    await w.find('#email').setValue('new@x');
    await w.find('#role').setValue('admin');
    await w.find('form').trigger('submit.prevent');
    await flushPromises();
    const text = w.find('.admin-confirm-message').text();
    expect(text).toContain('"old"');
    expect(text).toContain('old@x');
    expect(text).toContain('Correo');
    expect(text).toContain('Rol');
    // The dirtyFields comparator excludes password — a freshly typed
    // but unconfirmed password must not appear in the field list.
    expect(text).not.toContain('Contraseña');
  });
});
