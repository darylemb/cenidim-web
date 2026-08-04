<template>
  <div class="modal-overlay" @click="$emit('cancel')">
    <div class="admin-form-modal modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ modalTitle }}</h3>
        <button class="close-btn" @click="requestCancel" aria-label="Cerrar">×</button>
      </div>

      <div class="modal-body">
        <div v-if="error" class="form-error">{{ error }}</div>

        <form @submit.prevent="handleSubmit">
          <template v-if="formType === 'fonograma'">
            <div class="form-row">
              <div class="form-group">
                <label for="clave_fonograma">Clave</label>
                <input
                  id="clave_fonograma"
                  v-model="form.clave_fonograma"
                  type="number"
                  required
                  :readonly="isEditing"
                  :class="{ 'input-readonly': isEditing }"
                />
              </div>
              <div class="form-group">
                <label for="anio">Año</label>
                <input id="anio" v-model="form.anio" type="text" />
              </div>
            </div>
            <div class="form-group">
              <label for="titulo">Título</label>
              <input id="titulo" v-model="form.titulo" type="text" required />
            </div>

            <details class="form-details">
              <summary>Detalles adicionales</summary>
              <div class="form-details-body">
                <div class="form-group">
                  <label for="subtitulo">Subtítulo</label>
                  <input id="subtitulo" v-model="form.subtitulo" type="text" />
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label for="interprete_principal">Intérprete Principal</label>
                    <input
                      id="interprete_principal"
                      v-model="form.interprete_principal"
                      type="text"
                    />
                  </div>
                  <div class="form-group">
                    <label for="pais_edicion">País</label>
                    <input id="pais_edicion" v-model="form.pais_edicion" type="text" />
                  </div>
                </div>
                <div class="form-group">
                  <label for="editora">Editora</label>
                  <input id="editora" v-model="form.editora" type="text" />
                </div>
                <div class="form-group">
                  <label for="interpretes_invitados">Intérpretes Invitados</label>
                  <input
                    id="interpretes_invitados"
                    v-model="form.interpretes_invitados"
                    type="text"
                  />
                </div>
                <div class="form-group">
                  <label for="soporte_fisico">Soporte Físico</label>
                  <input id="soporte_fisico" v-model="form.soporte_fisico" type="text" />
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label for="numero_catalogo">Número Catálogo</label>
                    <input
                      id="numero_catalogo"
                      v-model="form.numero_catalogo"
                      type="text"
                    />
                  </div>
                  <div class="form-group">
                    <label for="ciudad_edicion">Ciudad Edición</label>
                    <input id="ciudad_edicion" v-model="form.ciudad_edicion" type="text" />
                  </div>
                </div>
                <div class="form-group">
                  <label for="pistas">Pistas</label>
                  <textarea id="pistas" v-model="form.pistas" rows="2"></textarea>
                </div>
                <div class="form-group">
                  <label for="observaciones">Observaciones</label>
                  <textarea id="observaciones" v-model="form.observaciones" rows="2"></textarea>
                </div>
              </div>
            </details>
          </template>

          <template v-else-if="formType === 'song'">
            <div class="form-context">
              <span v-if="isEditing"><strong>ID:</strong> {{ form.id }}</span>
            </div>
            <div class="form-group">
              <label for="fonograma_id">Fonograma</label>
              <input
                id="fonograma_id"
                v-model="form.fonograma_id"
                type="number"
                required
                :readonly="isEditing"
                :class="{ 'input-readonly': isEditing }"
                :title="isEditing ? 'Inmutable: el fonograma no se puede cambiar al editar' : ''"
              />
            </div>
            <div class="form-group">
              <label for="title">Título</label>
              <input id="title" v-model="form.title" type="text" required />
            </div>
            <div class="form-group">
              <label for="album">Álbum</label>
              <input
                id="album"
                v-model="form.album"
                type="text"
                readonly
                class="input-readonly"
                title="Derivado del fonograma asociado"
              />
            </div>
            <div class="form-group">
              <label for="lyrics">Letra</label>
              <textarea id="lyrics" v-model="form.lyrics" rows="6" required></textarea>
            </div>

            <details class="form-details">
              <summary>Detalles adicionales</summary>
              <div class="form-details-body">
                <div class="form-group">
                  <label for="subtitulo">Subtítulo</label>
                  <input
                    id="subtitulo_song"
                    v-model="form.subtitulo"
                    type="text"
                    readonly
                    class="input-readonly"
                    title="Derivado del fonograma asociado"
                  />
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label for="interprete_principal">Intérprete Principal</label>
                    <input
                      id="interprete_principal_song"
                      v-model="form.interprete_principal"
                      type="text"
                      readonly
                      class="input-readonly"
                      title="Derivado del fonograma asociado"
                    />
                  </div>
                  <div class="form-group">
                    <label for="year">Año</label>
                    <input
                      id="year_song"
                      v-model="form.year"
                      type="text"
                      readonly
                      class="input-readonly"
                      title="Derivado del fonograma asociado"
                    />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label for="pais_edicion">País</label>
                    <input
                      id="pais_edicion_song"
                      v-model="form.pais_edicion"
                      type="text"
                      readonly
                      class="input-readonly"
                      title="Derivado del fonograma asociado"
                    />
                  </div>
                  <div class="form-group">
                    <label for="editora">Editora</label>
                    <input
                      id="editora_song"
                      v-model="form.editora"
                      type="text"
                      readonly
                      class="input-readonly"
                      title="Derivado del fonograma asociado"
                    />
                  </div>
                </div>
                <div class="form-group">
                  <label for="clasificacion">Clasificación</label>
                  <select id="clasificacion" v-model="form.clasificacion">
                    <option value="">Sin clasificación</option>
                    <option value="ESPAÑOL_ESTANDAR">Español Estándar</option>
                    <option value="ESPAÑOL_REGIONAL">Español Regional</option>
                    <option value="LENGUA_INDIGENA">Lengua Indígena</option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="interpretes_invitados">Intérpretes Invitados</label>
                  <input
                    id="interpretes_invitados_song"
                    v-model="form.interpretes_invitados"
                    type="text"
                    readonly
                    class="input-readonly"
                    title="Derivado del fonograma asociado"
                  />
                </div>
                <div class="form-group">
                  <label for="filename">Nombre Archivo</label>
                  <input id="filename" v-model="form.filename" type="text" />
                </div>
                <div class="form-group">
                  <label for="pistas">Pistas</label>
                  <textarea
                    id="pistas_song"
                    v-model="form.pistas"
                    rows="2"
                    readonly
                    class="input-readonly"
                    title="Derivado del fonograma asociado"
                  ></textarea>
                </div>
                <div class="form-group">
                  <label for="observaciones">Observaciones</label>
                  <textarea
                    id="observaciones_song"
                    v-model="form.observaciones"
                    rows="2"
                    readonly
                    class="input-readonly"
                    title="Derivado del fonograma asociado"
                  ></textarea>
                </div>
              </div>
            </details>
          </template>

          <template v-else-if="formType === 'user'">
            <div v-if="isEditing" class="form-context">
              <span><strong>ID:</strong> {{ form.id }}</span>
            </div>
            <div class="form-group">
              <label for="username">Usuario</label>
              <input id="username" v-model="form.username" type="text" required />
            </div>
            <div class="form-group">
              <label for="email">Correo</label>
              <input id="email" v-model="form.email" type="email" required />
            </div>
            <div class="form-group">
              <label :for="isEditing ? 'password-optional' : 'password'">
                Contraseña{{ isEditing ? ' (opcional)' : '' }}
              </label>
              <input
                :id="isEditing ? 'password-optional' : 'password'"
                v-model="form.password"
                :type="isEditing ? 'password' : 'password'"
                :required="!isEditing"
              />
            </div>
            <div class="form-group">
              <label for="role">Rol</label>
              <select id="role" v-model="form.role">
                <option value="viewer">Viewer (predeterminado)</option>
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </template>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="requestCancel" :disabled="loading">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="loading">
              {{ loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmModal
      v-if="pendingCancel"
      title="Cambios sin guardar"
      :message="dirtyCancelMessage"
      confirm-label="Salir sin guardar"
      cancel-label="Seguir editando"
      variant="warning"
      :loading="false"
      @confirm="confirmCancel"
      @cancel="pendingCancel = false"
    />

    <ConfirmModal
      v-if="pendingSubmit"
      :title="submitTitle"
      :message="submitMessage"
      confirm-label="Sí, guardar"
      cancel-label="Volver"
      variant="primary"
      :loading="false"
      @confirm="confirmSubmit"
      @cancel="pendingSubmit = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Fonograma, Song, User } from '@/types';
import { apiService } from '@/services/api';
import ConfirmModal from './ConfirmModal.vue';

type FormType = 'fonograma' | 'song' | 'user';

const props = defineProps<{
  formType: FormType;
  item: Fonograma | Song | User | null;
}>();

const emit = defineEmits<{
  cancel: [];
  submitted: [result: Fonograma | Song | User];
}>();

const loading = ref(false);
const error = ref('');
const pendingCancel = ref(false);
const pendingSubmit = ref(false);
const originalSnapshot = ref<string>('');

const isEditing = computed(() => props.item !== null);

const typeLabel = computed(() => {
  const typeMap: Record<FormType, string> = {
    fonograma: 'Fonograma',
    song: 'Canción',
    user: 'Usuario',
  };
  return typeMap[props.formType];
});

const modalTitle = computed(() => {
  const action = isEditing.value ? 'Editar' : 'Agregar';
  return `${action} ${typeLabel.value}`;
});

const isDirty = computed(() => {
  if (!originalSnapshot.value) return false;
  // JSON.stringify is fine for the flat object shape these forms
  // produce (no functions, no cycles). We exclude ``password`` from
  // the user form so a freshly-typed-but-unsubmitted password doesn't
  // keep the form "dirty" forever.
  if (props.formType === 'user') {
    const { password: _pw, ...rest } = form.value as Record<string, any>;
    return JSON.stringify(rest) !== originalSnapshot.value;
  }
  return JSON.stringify(form.value) !== originalSnapshot.value;
});

function snapshotForm(): string {
  if (props.formType === 'user') {
    const { password: _pw, ...rest } = form.value as Record<string, any>;
    return JSON.stringify(rest);
  }
  return JSON.stringify(form.value);
}

// Human-readable label per field, per form type. Used to describe
// the change in the confirm dialogs so the operator sees *what* is
// about to be written, not just "the form".
const fieldLabels: Record<FormType, Record<string, string>> = {
  fonograma: {
    clave_fonograma: 'Clave',
    titulo: 'Título',
    subtitulo: 'Subtítulo',
    interprete_principal: 'Intérprete principal',
    interpretes_invitados: 'Intérpretes invitados',
    interprete_participante: 'Intérprete participante',
    soporte_fisico: 'Soporte físico',
    editora: 'Editora',
    numero_catalogo: 'N° Catálogo',
    ciudad_edicion: 'Ciudad de edición',
    pais_edicion: 'País de edición',
    anio: 'Año',
    pistas: 'Pistas',
    observaciones: 'Observaciones',
  },
  song: {
    id: 'ID',
    fonograma_id: 'Fonograma',
    title: 'Título',
    lyrics: 'Letra',
    filename: 'Nombre de archivo',
    clasificacion: 'Clasificación',
    album: 'Álbum',
    subtitulo: 'Subtítulo',
    interprete_principal: 'Intérprete principal',
    interpretes_invitados: 'Intérpretes invitados',
    interprete_participante: 'Intérprete participante',
    soporte_fisico: 'Soporte físico',
    editora: 'Editora',
    numero_catalogo: 'N° Catálogo',
    ciudad_edicion: 'Ciudad',
    pais_edicion: 'País',
    year: 'Año',
    pistas: 'Pistas',
    observaciones: 'Observaciones',
  },
  user: {
    id: 'ID',
    username: 'Usuario',
    email: 'Correo',
    role: 'Rol',
    // password is intentionally omitted — never show it back to the operator
  },
};

function currentComparableForm(): Record<string, any> {
  if (props.formType === 'user') {
    const { password: _pw, ...rest } = form.value as Record<string, any>;
    return rest;
  }
  return { ...form.value };
}

const dirtyFields = computed<Array<{ key: string; label: string; before: unknown; after: unknown }>>(() => {
  if (!isDirty.value || !originalSnapshot.value) return [];
  let original: Record<string, unknown>;
  try {
    original = JSON.parse(originalSnapshot.value);
  } catch {
    return [];
  }
  const labels = fieldLabels[props.formType] ?? {};
  const current = currentComparableForm();
  return Object.keys(current)
    .filter((key) => JSON.stringify(current[key]) !== JSON.stringify(original?.[key]))
    .map((key) => ({
      key,
      label: labels[key] ?? key,
      before: original?.[key],
      after: current[key],
    }));
});

function formatDirtyFields(max = 3): string {
  const fields = dirtyFields.value;
  if (fields.length === 0) return '';
  if (fields.length === 1) return `1 campo: ${fields[0].label}`;
  const shown = fields.slice(0, max).map((f) => f.label).join(', ');
  const rest = fields.length - max;
  return rest > 0 ? `${fields.length} campos: ${shown} y ${rest} más` : `${fields.length} campos: ${shown}`;
}

function describeItem(): string {
  // For create: the form has no `id` yet, so pull whatever the user
  // typed. For edit: prefer the original item so the operator sees
  // the canonical identifier (clave, id, email) even if they cleared
  // it from the form.
  if (props.formType === 'fonograma') {
    const f = (props.item as Fonograma | null) ?? (form.value as Record<string, any>);
    const clave = f?.clave_fonograma ?? 0;
    const titulo = f?.titulo?.trim() || 'sin título';
    return `el fonograma clave ${clave} — "${titulo}"`;
  }
  if (props.formType === 'song') {
    const s = (props.item as Song | null) ?? (form.value as Record<string, any>);
    const title = s?.title?.trim() || 'sin título';
    return `la canción "${title}"`;
  }
  if (props.formType === 'user') {
    const u = (props.item as User | null) ?? (form.value as Record<string, any>);
    const username = u?.username?.trim() || 'sin usuario';
    const email = u?.email ? ` (${u.email})` : '';
    return `el usuario "${username}"${email}`;
  }
  return 'el registro';
}

const submitTitle = computed(() =>
  isEditing.value ? `Guardar ${typeLabel.value}` : `Crear ${typeLabel.value}`
);

const submitMessage = computed(() => {
  const desc = describeItem();
  if (isEditing.value) {
    const fields = formatDirtyFields();
    return fields
      ? `Vas a actualizar ${desc}.\n\nCampos modificados: ${fields}.`
      : `Vas a actualizar ${desc}. ¿Confirmas los cambios?`;
  }
  return `Vas a crear ${desc}. ¿Confirmas?`;
});

const dirtyCancelMessage = computed(() => {
  const fields = formatDirtyFields();
  const base = isEditing.value
    ? `Tienes cambios sin guardar en ${describeItem()}.`
    : `Tienes cambios sin guardar en este ${typeLabel.value.toLowerCase()}.`;
  return fields ? `${base} (${fields}) ¿Salir sin guardar?` : `${base} ¿Salir sin guardar?`;
});

const defaultFonograma = (): Record<string, any> => ({
  clave_fonograma: 0,
  titulo: '',
  subtitulo: '',
  interprete_principal: '',
  interpretes_invitados: '',
  interprete_participante: '',
  soporte_fisico: '',
  editora: '',
  numero_catalogo: '',
  ciudad_edicion: '',
  pais_edicion: '',
  anio: '',
  pistas: '',
  observaciones: '',
});

const defaultSong = (): Record<string, any> => ({
  id: 0,
  fonograma_id: 0,
  title: '',
  lyrics: '',
  album: '',
  subtitulo: '',
  interprete_principal: '',
  interpretes_invitados: '',
  interprete_participante: '',
  soporte_fisico: '',
  editora: '',
  numero_catalogo: '',
  ciudad_edicion: '',
  pais_edicion: '',
  year: '',
  pistas: '',
  observaciones: '',
  filename: '',
  clasificacion: '',
});

const defaultUser = (): Record<string, any> => ({
  id: 0,
  username: '',
  email: '',
  password: '',
  role: 'viewer',
});

const form = ref<Record<string, any>>({});

watch(
  () => props.item,
  (newItem) => {
    error.value = '';
    pendingCancel.value = false;
    pendingSubmit.value = false;
    if (newItem) {
      form.value = { ...newItem };
      if (props.formType === 'user') {
        (form.value as Partial<User & { password: string }>).password = '';
      }
    } else {
      if (props.formType === 'fonograma') form.value = defaultFonograma();
      else if (props.formType === 'song') form.value = defaultSong();
      else form.value = defaultUser();
    }
    // Snapshot the freshly-populated form so isDirty can detect
    // any subsequent user edits.
    originalSnapshot.value = snapshotForm();
  },
  { immediate: true }
);

function requestCancel() {
  if (isDirty.value) {
    pendingCancel.value = true;
  } else {
    emit('cancel');
  }
}

function confirmCancel() {
  pendingCancel.value = false;
  emit('cancel');
}

async function handleSubmit() {
  // Confirm before doing anything destructive-ish: a no-op create is
  // cheap to undo (just delete the row) but an edit overwrites real
  // data in the catalog.
  if (pendingSubmit.value) return;
  pendingSubmit.value = true;
}

async function confirmSubmit() {
  pendingSubmit.value = false;
  error.value = '';
  loading.value = true;

  try {
    let result: Fonograma | Song | User;

    if (props.formType === 'fonograma') {
      const data = form.value;
      if (isEditing.value) {
        result = await apiService.adminUpdateFonograma(data.clave_fonograma, data);
      } else {
        result = await apiService.adminCreateFonograma(data);
      }
    } else if (props.formType === 'song') {
      const data = form.value;
      if (isEditing.value) {
        result = await apiService.adminUpdateSong(data.id, data);
      } else {
        result = await apiService.adminCreateSong(data);
      }
    } else {
      const data = form.value;
      if (isEditing.value) {
        const { password, ...updateData } = data;
        result = await apiService.adminUpdateUser(data.id, password ? data : updateData);
      } else {
        result = await apiService.adminCreateUser({
          username: data.username,
          email: data.email,
          password: data.password,
          role: data.role,
        });
      }
    }

    emit('submitted', result);
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error al guardar';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.admin-form-modal {
  max-width: 600px;
}

.modal-body {
  padding: var(--space-5) var(--space-6);
  overflow-y: auto;
}

.form-error {
  background: rgba(154, 42, 42, 0.08);
  color: var(--color-danger);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  font-size: var(--font-size-sm);
  border: 1px solid var(--color-danger);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  margin-bottom: var(--space-4);
}

.form-group label {
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-family: inherit;
  background: var(--color-bg);
  color: var(--color-text);
  min-height: var(--tap-target-min);
  transition: var(--transition-fast);
}

.form-group input:hover,
.form-group select:hover,
.form-group textarea:hover {
  border-color: var(--color-border-strong);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-brand);
  box-shadow: 0 0 0 3px rgba(117, 20, 40, 0.1);
}

.input-readonly {
  background: var(--color-bg-soft);
  color: var(--color-text-muted);
}

.form-context {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-5);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-4);
  background: var(--color-bg-soft);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.form-context strong {
  color: var(--color-text);
  font-weight: 500;
}

.form-details {
  margin-bottom: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-soft);
}

.form-details > summary {
  cursor: pointer;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
  list-style: none;
  user-select: none;
  min-height: var(--tap-target-min);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: var(--transition-fast);
}

.form-details > summary::-webkit-details-marker {
  display: none;
}

.form-details > summary::before {
  content: '▸';
  font-size: 0.75em;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.form-details[open] > summary::before {
  transform: rotate(90deg);
}

.form-details > summary:hover {
  color: var(--color-brand);
}

.form-details > summary:focus-visible {
  outline: 2px solid var(--color-brand);
  outline-offset: 2px;
}

.form-details-body {
  padding: var(--space-2) var(--space-4) var(--space-3);
  border-top: var(--hairline-soft);
}

.form-details-body .form-group:last-child {
  margin-bottom: 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: var(--hairline-soft);
}

.close-btn {
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0;
  line-height: 1;
  min-width: var(--tap-target-min);
  min-height: var(--tap-target-min);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
}
</style>
