import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

// ─── Shared helpers ──────────────────────────────────────────────────────────

const ROLES = ['viewer', 'editor', 'admin'];

const Pagination = ({ page, total, limit, onChange }) => {
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return null;
  return (
    <div className="admin-pagination">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ‹ Ant
      </button>
      <span>
        {page} / {totalPages}
      </span>
      <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        Sig ›
      </button>
    </div>
  );
};

const ConfirmModal = ({ message, onConfirm, onCancel }) => (
  <div className="modal-overlay" onClick={onCancel}>
    <div className="modal-content admin-confirm" onClick={(e) => e.stopPropagation()}>
      <p>{message}</p>
      <div className="admin-confirm-actions">
        <button className="btn-danger" onClick={onConfirm}>
          Eliminar
        </button>
        <button className="btn-secondary" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </div>
  </div>
);

// ─── Sort helpers ───────────────────────────────────────────────────────────

const SortableHeader = ({ label, sortKey, currentSortKey, currentSortDir, onSort }) => {
  const isActive = currentSortKey === sortKey;
  return (
    <th className={`sortable-th${isActive ? ' sort-active' : ''}`} onClick={() => onSort(sortKey)}>
      {label}
      <span className="sort-arrow">
        {isActive ? (currentSortDir === 'asc' ? ' ▲' : ' ▼') : ' ⇅'}
      </span>
    </th>
  );
};

const sortList = (list, key, dir) => {
  if (!key) return list;
  return [...list].sort((a, b) => {
    const av = a[key] ?? '';
    const bv = b[key] ?? '';
    const cmp = String(av).localeCompare(String(bv), undefined, {
      numeric: true,
      sensitivity: 'base',
    });
    return dir === 'asc' ? cmp : -cmp;
  });
};

const renderTruncatedText = (value) => {
  const text = value && String(value).trim() ? String(value) : '—';
  return (
    <span className="table-cell-text" title={text}>
      {text}
    </span>
  );
};

// ─── Fonogramas tab ──────────────────────────────────────────────────────────

const FONOGRAMA_FIELDS = [
  { key: 'clave_fonograma', label: 'Clave Fonograma', type: 'number', required: true },
  { key: 'titulo', label: 'Título', required: true },
  { key: 'subtitulo', label: 'Subtítulo' },
  { key: 'interprete_principal', label: 'Intérprete principal' },
  { key: 'interpretes_invitados', label: 'Intérpretes invitados' },
  { key: 'interprete_participante', label: 'Intérprete participante' },
  { key: 'soporte_fisico', label: 'Soporte físico' },
  { key: 'editora', label: 'Editora' },
  { key: 'numero_catalogo', label: 'Núm. catálogo' },
  { key: 'ciudad_edicion', label: 'Ciudad de edición' },
  { key: 'pais_edicion', label: 'País de edición' },
  { key: 'anio', label: 'Año' },
  { key: 'pistas', label: 'Pistas', textarea: true },
  { key: 'observaciones', label: 'Observaciones', textarea: true },
];

const emptyFonograma = () => Object.fromEntries(FONOGRAMA_FIELDS.map((f) => [f.key, '']));

const FonogramasTab = ({ role }) => {
  const canEdit = role === 'editor' || role === 'admin';
  const canDelete = role === 'admin';

  const [list, setList] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const limit = 20;
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(null); // null | {} for create | fonograma for edit
  const [isNew, setIsNew] = useState(false);
  const [formError, setFormError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [sortKey, setSortKey] = useState('clave_fonograma');
  const [sortDir, setSortDir] = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedList = sortList(list, sortKey, sortDir);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiService.adminListFonogramas(page, limit);
      setList(data.results || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleEdit = (f) => {
    setEditing({ ...f });
    setIsNew(false);
    setFormError('');
  };
  const handleNew = () => {
    setEditing(emptyFonograma());
    setIsNew(true);
    setFormError('');
  };
  const handleCancel = () => {
    setEditing(null);
    setFormError('');
  };

  const handleSave = async () => {
    setFormError('');
    try {
      if (isNew) {
        const payload = { ...editing, clave_fonograma: Number(editing.clave_fonograma) };
        await apiService.adminCreateFonograma(payload);
      } else {
        await apiService.adminUpdateFonograma(editing.clave_fonograma, editing);
      }
      setEditing(null);
      load();
    } catch (e) {
      setFormError(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiService.adminDeleteFonograma(id);
      setConfirmDelete(null);
      load();
    } catch {
      setConfirmDelete(null);
    }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3>Fonogramas ({total})</h3>
        {canEdit && (
          <button className="btn-primary" onClick={handleNew}>
            + Nuevo fonograma
          </button>
        )}
      </div>

      {loading ? (
        <p className="admin-loading">Cargando...</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <SortableHeader
                  label="Clave"
                  sortKey="clave_fonograma"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Título"
                  sortKey="titulo"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Intérprete"
                  sortKey="interprete_principal"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Año"
                  sortKey="anio"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Soporte"
                  sortKey="soporte_fisico"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                {(canEdit || canDelete) && <th>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {sortedList.map((f) => (
                <tr key={f.clave_fonograma}>
                  <td>{f.clave_fonograma}</td>
                  <td className="table-cell-truncate">{renderTruncatedText(f.titulo)}</td>
                  <td className="table-cell-truncate">
                    {renderTruncatedText(f.interprete_principal)}
                  </td>
                  <td className="table-cell-truncate">{renderTruncatedText(f.anio)}</td>
                  <td className="table-cell-truncate">{renderTruncatedText(f.soporte_fisico)}</td>
                  {(canEdit || canDelete) && (
                    <td className="admin-actions">
                      {canEdit && (
                        <button className="btn-sm btn-secondary" onClick={() => handleEdit(f)}>
                          Editar
                        </button>
                      )}
                      {canDelete && (
                        <button
                          className="btn-sm btn-danger"
                          onClick={() => setConfirmDelete(f.clave_fonograma)}
                        >
                          Eliminar
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={page} total={total} limit={limit} onChange={setPage} />

      {/* Edit / Create modal */}
      {editing && (
        <div className="modal-overlay" onClick={handleCancel}>
          <div className="modal-content admin-form-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{isNew ? 'Nuevo fonograma' : `Editar fonograma #${editing.clave_fonograma}`}</h3>
              <button className="close-btn" onClick={handleCancel}>
                &times;
              </button>
            </div>
            <div className="modal-body admin-form-body">
              {FONOGRAMA_FIELDS.map((field) => (
                <div className="form-group" key={field.key}>
                  <label>
                    {field.label}
                    {field.required ? ' *' : ''}
                  </label>
                  {field.textarea ? (
                    <textarea
                      value={editing[field.key] || ''}
                      onChange={(e) =>
                        setEditing((prev) => ({ ...prev, [field.key]: e.target.value }))
                      }
                      rows={3}
                      disabled={field.key === 'clave_fonograma' && !isNew}
                    />
                  ) : (
                    <input
                      type={field.type || 'text'}
                      value={editing[field.key] || ''}
                      onChange={(e) =>
                        setEditing((prev) => ({ ...prev, [field.key]: e.target.value }))
                      }
                      disabled={field.key === 'clave_fonograma' && !isNew}
                    />
                  )}
                </div>
              ))}
              {formError && <p className="auth-error">{formError}</p>}
              <div className="admin-form-actions">
                <button className="btn-primary" onClick={handleSave}>
                  Guardar
                </button>
                <button className="btn-secondary" onClick={handleCancel}>
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {confirmDelete !== null && (
        <ConfirmModal
          message={`¿Eliminar fonograma #${confirmDelete} y todas sus pistas?`}
          onConfirm={() => handleDelete(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  );
};

// ─── Songs tab ───────────────────────────────────────────────────────────────

const SongsTab = ({ role }) => {
  const canEdit = role === 'editor' || role === 'admin';
  const canDelete = role === 'admin';

  const [list, setList] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const limit = 50;
  const [filterFonograma, setFilterFonograma] = useState('');
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(null);
  const [isNew, setIsNew] = useState(false);
  const [formError, setFormError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [showLyrics, setShowLyrics] = useState(null);
  const [sortKey, setSortKey] = useState('id');
  const [sortDir, setSortDir] = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedList = sortList(list, sortKey, sortDir);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiService.adminListSongs(filterFonograma, page, limit);
      setList(data.results || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, filterFonograma]);

  useEffect(() => {
    load();
  }, [load]);

  const handleEdit = (s) => {
    setEditing({ title: s.title, lyrics: s.lyrics || '', _id: s.id });
    setIsNew(false);
    setFormError('');
  };
  const handleNew = () => {
    setEditing({ fonograma_id: '', title: '', lyrics: '' });
    setIsNew(true);
    setFormError('');
  };

  const handleSave = async () => {
    setFormError('');
    try {
      if (isNew) {
        await apiService.adminCreateSong({
          fonograma_id: Number(editing.fonograma_id),
          title: editing.title,
          lyrics: editing.lyrics,
        });
      } else {
        await apiService.adminUpdateSong(editing._id, {
          title: editing.title,
          lyrics: editing.lyrics,
        });
      }
      setEditing(null);
      load();
    } catch (e) {
      setFormError(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiService.adminDeleteSong(id);
      setConfirmDelete(null);
      load();
    } catch {
      setConfirmDelete(null);
    }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3>Canciones / Letras ({total})</h3>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Filtrar por clave fonograma..."
            value={filterFonograma}
            onChange={(e) => {
              setFilterFonograma(e.target.value);
              setPage(1);
            }}
            style={{
              padding: '0.4rem',
              border: '1px solid var(--border-light)',
              fontSize: '0.8rem',
            }}
          />
          {canEdit && (
            <button className="btn-primary" onClick={handleNew}>
              + Nueva canción
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <p className="admin-loading">Cargando...</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <SortableHeader
                  label="ID"
                  sortKey="id"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Fonograma"
                  sortKey="fonograma_id"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Título"
                  sortKey="title"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <th>Tiene letra</th>
                {(canEdit || canDelete) && <th>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {sortedList.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.fonograma_id}</td>
                  <td className="table-cell-truncate">{renderTruncatedText(s.title)}</td>
                  <td>
                    {s.lyrics ? (
                      <button className="btn-sm btn-link" onClick={() => setShowLyrics(s)}>
                        Ver
                      </button>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  {(canEdit || canDelete) && (
                    <td className="admin-actions">
                      {canEdit && (
                        <button className="btn-sm btn-secondary" onClick={() => handleEdit(s)}>
                          Editar
                        </button>
                      )}
                      {canDelete && (
                        <button
                          className="btn-sm btn-danger"
                          onClick={() => setConfirmDelete(s.id)}
                        >
                          Eliminar
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={page} total={total} limit={limit} onChange={setPage} />

      {/* Lyrics view modal (read-only) */}
      {showLyrics && (
        <div className="modal-overlay" onClick={() => setShowLyrics(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{showLyrics.title}</h3>
              <button className="close-btn" onClick={() => setShowLyrics(null)}>
                &times;
              </button>
            </div>
            <div className="modal-body">{showLyrics.lyrics}</div>
          </div>
        </div>
      )}

      {/* Edit / Create modal */}
      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal-content admin-form-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{isNew ? 'Nueva canción' : `Editar canción #${editing._id}`}</h3>
              <button className="close-btn" onClick={() => setEditing(null)}>
                &times;
              </button>
            </div>
            <div className="modal-body admin-form-body">
              {isNew && (
                <div className="form-group">
                  <label>Clave Fonograma *</label>
                  <input
                    type="number"
                    value={editing.fonograma_id}
                    onChange={(e) => setEditing((p) => ({ ...p, fonograma_id: e.target.value }))}
                  />
                </div>
              )}
              <div className="form-group">
                <label>Título *</label>
                <input
                  type="text"
                  value={editing.title}
                  onChange={(e) => setEditing((p) => ({ ...p, title: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label>Letra</label>
                <textarea
                  rows={12}
                  value={editing.lyrics}
                  onChange={(e) => setEditing((p) => ({ ...p, lyrics: e.target.value }))}
                />
              </div>
              {formError && <p className="auth-error">{formError}</p>}
              <div className="admin-form-actions">
                <button className="btn-primary" onClick={handleSave}>
                  Guardar
                </button>
                <button className="btn-secondary" onClick={() => setEditing(null)}>
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {confirmDelete !== null && (
        <ConfirmModal
          message={`¿Eliminar canción #${confirmDelete}?`}
          onConfirm={() => handleDelete(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  );
};

// ─── Users tab (admin only) ──────────────────────────────────────────────────

const UsersTab = () => {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(null);
  const [isNew, setIsNew] = useState(false);
  const [formError, setFormError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [sortKey, setSortKey] = useState('id');
  const [sortDir, setSortDir] = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedList = sortList(list, sortKey, sortDir);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiService.adminListUsers();
      setList(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleEdit = (u) => {
    setEditing({ _id: u.id, username: u.username, email: u.email, role: u.role, password: '' });
    setIsNew(false);
    setFormError('');
  };
  const handleNew = () => {
    setEditing({ username: '', email: '', role: 'viewer', password: '' });
    setIsNew(true);
    setFormError('');
  };

  const handleSave = async () => {
    setFormError('');
    try {
      if (isNew) {
        await apiService.adminCreateUser({
          username: editing.username,
          email: editing.email,
          password: editing.password,
          role: editing.role,
        });
      } else {
        const payload = {};
        if (editing.username) payload.username = editing.username;
        if (editing.email) payload.email = editing.email;
        if (editing.role) payload.role = editing.role;
        if (editing.password) payload.password = editing.password;
        await apiService.adminUpdateUser(editing._id, payload);
      }
      setEditing(null);
      load();
    } catch (e) {
      setFormError(e.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiService.adminDeleteUser(id);
      setConfirmDelete(null);
      load();
    } catch {
      setConfirmDelete(null);
    }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3>Usuarios</h3>
        <button className="btn-primary" onClick={handleNew}>
          + Nuevo usuario
        </button>
      </div>

      {loading ? (
        <p className="admin-loading">Cargando...</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <SortableHeader
                  label="ID"
                  sortKey="id"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Usuario"
                  sortKey="username"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Correo"
                  sortKey="email"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Rol"
                  sortKey="role"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="Creado"
                  sortKey="created_at"
                  currentSortKey={sortKey}
                  currentSortDir={sortDir}
                  onSort={handleSort}
                />
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {sortedList.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td className="table-cell-truncate">{renderTruncatedText(u.username)}</td>
                  <td className="table-cell-truncate">{renderTruncatedText(u.email)}</td>
                  <td>
                    <span className={`role-badge role-${u.role}`}>{u.role}</span>
                  </td>
                  <td className="table-cell-truncate">
                    {renderTruncatedText(u.created_at ? u.created_at.slice(0, 10) : '')}
                  </td>
                  <td className="admin-actions">
                    <button className="btn-sm btn-secondary" onClick={() => handleEdit(u)}>
                      Editar
                    </button>
                    <button className="btn-sm btn-danger" onClick={() => setConfirmDelete(u.id)}>
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal-content admin-form-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{isNew ? 'Nuevo usuario' : `Editar usuario #${editing._id}`}</h3>
              <button className="close-btn" onClick={() => setEditing(null)}>
                &times;
              </button>
            </div>
            <div className="modal-body admin-form-body">
              <div className="form-group">
                <label>Usuario *</label>
                <input
                  type="text"
                  value={editing.username}
                  onChange={(e) => setEditing((p) => ({ ...p, username: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label>Correo *</label>
                <input
                  type="email"
                  value={editing.email}
                  onChange={(e) => setEditing((p) => ({ ...p, email: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label>Rol</label>
                <select
                  value={editing.role}
                  onChange={(e) => setEditing((p) => ({ ...p, role: e.target.value }))}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>
                  {isNew ? 'Contraseña *' : 'Nueva contraseña (dejar vacío para no cambiar)'}
                </label>
                <input
                  type="password"
                  value={editing.password}
                  onChange={(e) => setEditing((p) => ({ ...p, password: e.target.value }))}
                />
              </div>
              {formError && <p className="auth-error">{formError}</p>}
              <div className="admin-form-actions">
                <button className="btn-primary" onClick={handleSave}>
                  Guardar
                </button>
                <button className="btn-secondary" onClick={() => setEditing(null)}>
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {confirmDelete !== null && (
        <ConfirmModal
          message={`¿Eliminar usuario #${confirmDelete}?`}
          onConfirm={() => handleDelete(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  );
};

// ─── Main AdminPanel ─────────────────────────────────────────────────────────

export const AdminPanel = ({ user }) => {
  const tabs = [
    { id: 'fonogramas', label: 'Fonogramas' },
    { id: 'songs', label: 'Canciones / Letras' },
    ...(user.role === 'admin' ? [{ id: 'users', label: 'Usuarios' }] : []),
  ];
  const [activeTab, setActiveTab] = useState('fonogramas');

  return (
    <div className="content-area admin-panel">
      <div className="admin-panel-header">
        <h2 className="page-title">Panel de administración</h2>
        <div className="admin-user-info">
          <span className={`role-badge role-${user.role}`}>{user.role}</span>
          <span className="admin-username">{user.username}</span>
        </div>
      </div>

      <div className="admin-tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={activeTab === t.id ? 'active' : ''}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'fonogramas' && <FonogramasTab role={user.role} />}
      {activeTab === 'songs' && <SongsTab role={user.role} />}
      {activeTab === 'users' && user.role === 'admin' && <UsersTab />}
    </div>
  );
};
