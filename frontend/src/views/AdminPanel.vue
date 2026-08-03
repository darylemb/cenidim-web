<template>
  <div class="content-area admin-panel">
    <div class="admin-panel-header">
      <h2 class="page-title">Panel de Administración</h2>
      <div class="admin-user-info">
        <span class="admin-username">{{ auth.user?.username }}</span>
        <span :class="['role-badge', `role-${auth.user?.role}`]">{{ auth.user?.role }}</span>
      </div>
    </div>

    <div class="admin-tabs">
      <button :class="{ active: activeTab === 'fonogramas' }" @click="activeTab = 'fonogramas'">
        Fonogramas
      </button>
      <button :class="{ active: activeTab === 'songs' }" @click="activeTab = 'songs'">
        Canciones
      </button>
      <button
        v-if="auth.isAdmin"
        :class="{ active: activeTab === 'users' }"
        @click="activeTab = 'users'"
      >
        Usuarios
      </button>
    </div>

    <!-- Fonogramas Tab -->
    <div v-if="activeTab === 'fonogramas'">
      <div class="admin-section-header">
        <h3>Fonogramas</h3>
        <button v-if="auth.isEditor" class="btn-primary" @click="openFonoForm(null)">
          + Agregar
        </button>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <colgroup>
            <col style="width: 84px" />
            <col style="width: 30%" />
            <col style="width: 22%" />
            <col style="width: 80px" />
            <col style="width: 110px" />
            <col style="width: 18%" />
            <col style="width: 170px" />
          </colgroup>
          <thead>
            <tr>
              <SortableHeader
                v-for="col in fonoCols"
                :key="col.key"
                :col="col"
                :sort-key="fonoSortKey"
                :sort-dir="fonoSortDir"
                @sort="fonoSort(col.key)"
              />
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in fonogramas" :key="f.clave_fonograma">
              <td>{{ f.clave_fonograma }}</td>
              <td class="table-cell-truncate">{{ f.titulo }}</td>
              <td>{{ f.interprete_principal }}</td>
              <td>{{ f.anio }}</td>
              <td>{{ f.pais_edicion }}</td>
              <td>{{ f.editora }}</td>
              <td>
                <div class="admin-actions">
                  <button v-if="auth.isEditor" class="btn-primary btn-sm" @click="openFonoForm(f)">
                    Editar
                  </button>
                  <button
                    v-if="auth.isAdmin"
                    class="btn-danger btn-sm"
                    @click="confirmDeleteFono(f)"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="admin-pagination">
        <button
          :disabled="fonoPage === 1"
          @click="
            fonoPage--;
            loadFonos();
          "
        >
          Anterior
        </button>
        <span>Página {{ fonoPage }}</span>
        <button
          :disabled="!hasMoreFonos"
          @click="
            fonoPage++;
            loadFonos();
          "
        >
          Siguiente
        </button>
      </div>
    </div>

    <!-- Songs Tab -->
    <div v-if="activeTab === 'songs'">
      <div class="admin-section-header">
        <h3>Canciones</h3>
        <button v-if="auth.isEditor" class="btn-primary" @click="openSongForm(null)">
          + Agregar
        </button>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <colgroup>
            <col style="width: 70px" />
            <col style="width: 40%" />
            <col style="width: 110px" />
            <col style="width: 22%" />
            <col style="width: 170px" />
          </colgroup>
          <thead>
            <tr>
              <SortableHeader
                v-for="col in songCols"
                :key="col.key"
                :col="col"
                :sort-key="songSortKey"
                :sort-dir="songSortDir"
                @sort="songSort(col.key)"
              />
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in songs" :key="s.id">
              <td>{{ s.id }}</td>
              <td class="table-cell-truncate">{{ s.title }}</td>
              <td>{{ s.fonograma_id }}</td>
              <td>{{ s.clasificacion }}</td>
              <td>
                <div class="admin-actions">
                  <button v-if="auth.isEditor" class="btn-primary btn-sm" @click="openSongForm(s)">
                    Editar
                  </button>
                  <button
                    v-if="auth.isAdmin"
                    class="btn-danger btn-sm"
                    @click="confirmDeleteSong(s)"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="admin-pagination">
        <button
          :disabled="songPage === 1"
          @click="
            songPage--;
            loadSongs();
          "
        >
          Anterior
        </button>
        <span>Página {{ songPage }}</span>
        <button
          :disabled="!hasMoreSongs"
          @click="
            songPage++;
            loadSongs();
          "
        >
          Siguiente
        </button>
      </div>
    </div>

    <!-- Users Tab -->
    <div v-if="activeTab === 'users' && auth.isAdmin">
      <div class="admin-section-header">
        <h3>Usuarios</h3>
        <button class="btn-primary" @click="openUserForm(null)">+ Agregar</button>
      </div>
      <div class="admin-table-wrap">
        <table class="admin-table">
          <colgroup>
            <col style="width: 70px" />
            <col style="width: 25%" />
            <col style="width: 35%" />
            <col style="width: 100px" />
            <col style="width: 170px" />
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>Usuario</th>
              <th>Correo</th>
              <th>Rol</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.username }}</td>
              <td>{{ u.email }}</td>
              <td>
                <span :class="['role-badge', `role-${u.role}`]">{{ u.role }}</span>
              </td>
              <td>
                <div class="admin-actions">
                  <button class="btn-secondary btn-sm" @click="openUserForm(u)">Editar</button>
                  <button class="btn-danger btn-sm" @click="confirmDeleteUser(u.id)">
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Confirm Modal (delete) -->
    <ConfirmModal
      v-if="confirmTarget"
      :title="confirmTitle"
      :message="confirmMessage"
      :loading="confirmLoading"
      confirm-label="Eliminar"
      loading-label="Eliminando..."
      variant="danger"
      @confirm="executeDelete"
      @cancel="confirmTarget = null"
    />

    <!-- Form Modal -->
    <AdminFormModal
      v-if="showFormModal"
      :form-type="formType"
      :item="formItem"
      @cancel="showFormModal = false"
      @submitted="handleFormSubmitted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { apiService } from '@/services/api';
import type { Fonograma, Song, User } from '@/types';
import SortableHeader from '@/components/SortableHeader.vue';
import ConfirmModal from '@/components/ConfirmModal.vue';
import AdminFormModal from '@/components/AdminFormModal.vue';

const auth = useAuthStore();

const activeTab = ref<'fonogramas' | 'songs' | 'users'>('fonogramas');
const fonogramas = ref<Fonograma[]>([]);
const songs = ref<Song[]>([]);
const users = ref<User[]>([]);
const fonoPage = ref(1);
const songPage = ref(1);
const fonoSortKey = ref('');
const fonoSortDir = ref<'asc' | 'desc'>('asc');
const songSortKey = ref('');
const songSortDir = ref<'asc' | 'desc'>('asc');
const hasMoreFonos = ref(false);
const hasMoreSongs = ref(false);
const confirmTarget = ref<
  | { type: 'fonograma' | 'song' | 'user'; id: number; label?: string }
  | null
>(null);
const confirmMessage = ref('');
const confirmTitle = ref('');
const confirmLoading = ref(false);

const showFormModal = ref(false);
const formType = ref<'fonograma' | 'song' | 'user'>('fonograma');
const formItem = ref<Fonograma | Song | User | null>(null);

const fonoCols = [
  { key: 'clave_fonograma', label: 'Clave' },
  { key: 'titulo', label: 'Título' },
  { key: 'interprete_principal', label: 'Intérprete' },
  { key: 'anio', label: 'Año' },
  { key: 'pais_edicion', label: 'País' },
  { key: 'editora', label: 'Editora' },
  { key: 'actions', label: 'Acciones' },
];

const songCols = [
  { key: 'id', label: 'ID' },
  { key: 'title', label: 'Título' },
  { key: 'fonograma_id', label: 'Fonograma' },
  { key: 'clasificacion', label: 'Clasificación' },
  { key: 'actions', label: 'Acciones' },
];

onMounted(() => {
  loadFonos();
  loadSongs();
  if (auth.isAdmin) loadUsers();
});

async function loadFonos() {
  try {
    const data = await apiService.adminListFonogramas(fonoPage.value, 20);
    fonogramas.value = data.results as unknown as Fonograma[];
    hasMoreFonos.value = data.results.length === 20;
  } catch (e) {
    console.error(e);
  }
}

async function loadSongs() {
  try {
    const data = await apiService.adminListSongs('', songPage.value, 50);
    songs.value = data.results;
    hasMoreSongs.value = data.results.length === 50;
  } catch (e) {
    console.error(e);
  }
}

async function loadUsers() {
  try {
    users.value = await apiService.adminListUsers();
  } catch (e) {
    console.error(e);
  }
}

function fonoSort(key: string) {
  if (fonoSortKey.value === key) {
    fonoSortDir.value = fonoSortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    fonoSortKey.value = key;
    fonoSortDir.value = 'asc';
  }
  fonogramas.value.sort((a, b) => {
    const av = (a as Record<string, unknown>)[key] ?? '';
    const bv = (b as Record<string, unknown>)[key] ?? '';
    return fonoSortDir.value === 'asc'
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });
}

function songSort(key: string) {
  if (songSortKey.value === key) {
    songSortDir.value = songSortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    songSortKey.value = key;
    songSortDir.value = 'asc';
  }
  songs.value.sort((a, b) => {
    const av = (a as Record<string, unknown>)[key] ?? '';
    const bv = (b as Record<string, unknown>)[key] ?? '';
    return songSortDir.value === 'asc'
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });
}

function openFonoForm(item?: Fonograma | null) {
  formType.value = 'fonograma';
  formItem.value = item ?? null;
  showFormModal.value = true;
}

function openSongForm(item?: Song | null) {
  formType.value = 'song';
  formItem.value = item ?? null;
  showFormModal.value = true;
}

function openUserForm(item?: User | null) {
  formType.value = 'user';
  formItem.value = item ?? null;
  showFormModal.value = true;
}

function handleFormSubmitted() {
  showFormModal.value = false;
  if (formType.value === 'fonograma') loadFonos();
  else if (formType.value === 'song') loadSongs();
  else if (formType.value === 'user') loadUsers();
}

function confirmDeleteFono(f: Fonograma) {
  confirmTarget.value = { type: 'fonograma', id: f.clave_fonograma };
  confirmTitle.value = 'Eliminar fonograma';
  const titulo = f.titulo?.trim() || 'sin título';
  confirmMessage.value = `Vas a eliminar el fonograma clave ${f.clave_fonograma} — "${titulo}". Esta acción no se puede deshacer.`;
}

function confirmDeleteSong(s: Song) {
  confirmTarget.value = { type: 'song', id: s.id };
  confirmTitle.value = 'Eliminar canción';
  const title = s.title?.trim() || 'sin título';
  confirmMessage.value = `Vas a eliminar la canción "${title}" (id ${s.id}). Esta acción no se puede deshacer.`;
}

function confirmDeleteUser(id: number) {
  const user = users.value.find((u) => u.id === id);
  confirmTarget.value = { type: 'user', id };
  confirmTitle.value = 'Eliminar usuario';
  confirmMessage.value = user
    ? `Vas a eliminar al usuario "${user.username}" (${user.email}). Perderá acceso al panel. Esta acción no se puede deshacer.`
    : 'Vas a eliminar este usuario. Perderá acceso al panel. Esta acción no se puede deshacer.';
}

async function executeDelete() {
  if (!confirmTarget.value) return;
  confirmLoading.value = true;
  try {
    if (confirmTarget.value.type === 'fonograma') {
      await apiService.adminDeleteFonograma(confirmTarget.value.id);
      loadFonos();
    } else if (confirmTarget.value.type === 'song') {
      await apiService.adminDeleteSong(confirmTarget.value.id);
      loadSongs();
    } else if (confirmTarget.value.type === 'user') {
      await apiService.adminDeleteUser(confirmTarget.value.id);
      loadUsers();
    }
  } catch (e) {
    console.error(e);
  } finally {
    confirmLoading.value = false;
    confirmTarget.value = null;
  }
}
</script>
