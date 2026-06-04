<template>
  <div class="modal-overlay" @click="$emit('cancel')">
    <div class="admin-form-modal modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ modalTitle }}</h3>
        <button class="close-btn" @click="$emit('cancel')" aria-label="Cerrar">×</button>
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
            <div class="form-group">
              <label for="subtitulo">Subtítulo</label>
              <input id="subtitulo" v-model="form.subtitulo" type="text" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="interprete_principal">Intérprete Principal</label>
                <input id="interprete_principal" v-model="form.interprete_principal" type="text" />
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
              <input id="interpretes_invitados" v-model="form.interpretes_invitados" type="text" />
            </div>
            <div class="form-group">
              <label for="soporte_fisico">Soporte Físico</label>
              <input id="soporte_fisico" v-model="form.soporte_fisico" type="text" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="numero_catalogo">Número Catálogo</label>
                <input id="numero_catalogo" v-model="form.numero_catalogo" type="text" />
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
          </template>

          <template v-else-if="formType === 'song'">
            <div class="form-row">
              <div class="form-group">
                <label for="id">ID</label>
                <input id="id" v-model="form.id" type="number" readonly class="input-readonly" />
              </div>
              <div class="form-group">
                <label for="fonograma_id">Fonograma ID</label>
                <input id="fonograma_id" v-model="form.fonograma_id" type="number" required />
              </div>
            </div>
            <div class="form-group">
              <label for="title">Título</label>
              <input id="title" v-model="form.title" type="text" required />
            </div>
            <div class="form-group">
              <label for="album">Álbum</label>
              <input id="album" v-model="form.album" type="text" />
            </div>
            <div class="form-group">
              <label for="subtitulo">Subtítulo</label>
              <input id="subtitulo" v-model="form.subtitulo" type="text" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="interprete_principal">Intérprete Principal</label>
                <input id="interprete_principal" v-model="form.interprete_principal" type="text" />
              </div>
              <div class="form-group">
                <label for="year">Año</label>
                <input id="year" v-model="form.year" type="text" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="pais_edicion">País</label>
                <input id="pais_edicion" v-model="form.pais_edicion" type="text" />
              </div>
              <div class="form-group">
                <label for="editora">Editora</label>
                <input id="editora" v-model="form.editora" type="text" />
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
              <input id="interpretes_invitados" v-model="form.interpretes_invitados" type="text" />
            </div>
            <div class="form-group">
              <label for="filename">Nombre Archivo</label>
              <input id="filename" v-model="form.filename" type="text" />
            </div>
            <div class="form-group">
              <label for="pistas">Pistas</label>
              <textarea id="pistas" v-model="form.pistas" rows="2"></textarea>
            </div>
            <div class="form-group">
              <label for="observaciones">Observaciones</label>
              <textarea id="observaciones" v-model="form.observaciones" rows="2"></textarea>
            </div>
          </template>

          <template v-else-if="formType === 'user'">
            <div class="form-group">
              <label for="id">ID</label>
              <input id="id" v-model="form.id" type="number" readonly class="input-readonly" />
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
              <select id="role" v-model="form.role" required>
                <option value="viewer">Viewer</option>
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </template>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="$emit('cancel')" :disabled="loading">
              Cancelar
            </button>
            <button type="submit" class="btn-primary" :disabled="loading">
              {{ loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Fonograma, Song, User } from '@/types';
import { apiService } from '@/services/api';

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

const isEditing = computed(() => props.item !== null);

const modalTitle = computed(() => {
  const action = isEditing.value ? 'Editar' : 'Agregar';
  const typeMap: Record<FormType, string> = {
    fonograma: 'Fonograma',
    song: 'Canción',
    user: 'Usuario',
  };
  return `${action} ${typeMap[props.formType]}`;
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const form = ref<Record<string, any>>({});

watch(
  () => props.item,
  (newItem) => {
    error.value = '';
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
  },
  { immediate: true }
);

async function handleSubmit() {
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
  padding: 1.5rem 2rem;
  overflow-y: auto;
}

.form-error {
  background: #fee2e2;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 1rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary, #374151);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-light, #d1d5db);
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary, #3b82f6);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.input-readonly {
  background: var(--bg-disabled, #f3f4f6);
  color: var(--text-muted, #6b7280);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-light, #e5e7eb);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-muted, #6b7280);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-primary, #374151);
}
</style>
