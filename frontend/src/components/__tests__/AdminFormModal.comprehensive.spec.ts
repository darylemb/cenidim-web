import { describe, it, expect, vi } from 'vitest';
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

describe('AdminFormModal.vue', () => {
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

  it('emits cancel when × is clicked', async () => {
    const w = makeWrapper();
    await w.find('.close-btn').trigger('click');
    expect(w.emitted('cancel')).toHaveLength(1);
  });

  it('does not emit cancel when clicking inside the modal body', async () => {
    const w = makeWrapper();
    await w.find('.modal-body').trigger('click');
    expect(w.emitted('cancel')).toBeUndefined();
  });

  it('creating a fonograma calls adminCreateFonograma', async () => {
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('99');
    await w.find('#titulo').setValue('Nuevo');
    await w.find('form').trigger('submit.prevent');
    await flushPromises();
    expect(apiService.adminCreateFonograma).toHaveBeenCalledWith(
      expect.objectContaining({ clave_fonograma: 99, titulo: 'Nuevo' })
    );
    expect(w.emitted('submitted')).toBeTruthy();
  });

  it('updating a fonograma calls adminUpdateFonograma', async () => {
    const w = makeWrapper({
      formType: 'fonograma',
      item: { clave_fonograma: 7, titulo: 'Old' },
    });
    await w.find('#titulo').setValue('Updated');
    await w.find('form').trigger('submit.prevent');
    await flushPromises();
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
    await flushPromises();
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
    await flushPromises();
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
    await flushPromises();
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
    await flushPromises();
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
    await flushPromises();
    expect(w.find('.form-error').text()).toContain('Bad input');
  });

  it('disables submit button while loading', async () => {
    vi.mocked(apiService.adminCreateFonograma).mockImplementation(() => new Promise(() => {}));
    const w = makeWrapper({ formType: 'fonograma' });
    await w.find('#clave_fonograma').setValue('1');
    await w.find('#titulo').setValue('X');
    await w.find('form').trigger('submit.prevent');
    await nextTick();
    const submitBtn = w.find('button[type="submit"]');
    expect((submitBtn.element as HTMLButtonElement).disabled).toBe(true);
  });
});
