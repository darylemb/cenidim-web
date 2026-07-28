# FastAPI ↔ Frontend endpoint parity

This document enumerates every endpoint the Vue dashboard calls
(per `frontend/src/services/api.ts`) and the corresponding
FastAPI route that fulfils it. The `openapi.json` is the source of
truth for the FastAPI contract; CI guards drift via
`tests/api/test_openapi.py`.

| Frontend call (`apiService.<x>`) | HTTP | FastAPI path | Backend handler |
| --- | --- | --- | --- |
| `searchSongs` | `GET` | `/api/search` | `app.routers.public.search_songs` |
| `getSongDetail` | `GET` | `/api/song/{song_id}` | `app.routers.public.get_song_detail` |
| `getTimeline` | `GET` | `/api/timeline` | `app.routers.public.get_timeline` |
| `getStats` | `GET` | `/api/stats` | `app.routers.public.get_stats` |
| `getWordCloud` | `GET` | `/api/word-cloud` | `app.routers.public.get_word_cloud` |
| `login` | `POST` | `/api/auth/login` | `app.routers.auth.login` |
| `forgotPassword` | `POST` | `/api/auth/forgot` | `app.routers.auth.forgot` |
| `resetPassword` | `POST` | `/api/auth/reset` | `app.routers.auth.reset` |
| `register` | `POST` | `/api/auth/register` | `app.routers.auth.register` |
| `getMe` | `GET` | `/api/auth/me` | `app.routers.auth.me` |
| `adminListFonogramas` | `GET` | `/api/admin/fonogramas` | `app.routers.admin.admin_list_fonogramas` |
| `adminGetFonograma` | `GET` | `/api/admin/fonogramas/{id}` | `app.routers.admin.admin_get_fonograma` |
| `adminCreateFonograma` | `POST` | `/api/admin/fonogramas` | `app.routers.admin.admin_create_fonograma` |
| `adminUpdateFonograma` | `PUT` | `/api/admin/fonogramas/{id}` | `app.routers.admin.admin_update_fonograma` |
| `adminDeleteFonograma` | `DELETE` | `/api/admin/fonogramas/{id}` | `app.routers.admin.admin_delete_fonograma` |
| `adminListSongs` | `GET` | `/api/admin/songs` | `app.routers.admin.admin_list_songs` |
| `adminCreateSong` | `POST` | `/api/admin/songs` | `app.routers.admin.admin_create_song` |
| `adminUpdateSong` | `PUT` | `/api/admin/songs/{id}` | `app.routers.admin.admin_update_song` |
| `adminDeleteSong` | `DELETE` | `/api/admin/songs/{id}` | `app.routers.admin.admin_delete_song` |
| `adminListUsers` | `GET` | `/api/admin/users` | `app.routers.admin.admin_list_users` |
| `adminCreateUser` | `POST` | `/api/admin/users` | `app.routers.admin.admin_create_user` |
| `adminUpdateUser` | `PUT` | `/api/admin/users/{id}` | `app.routers.admin.admin_update_user` |
| `adminDeleteUser` | `DELETE` | `/api/admin/users/{id}` | `app.routers.admin.admin_delete_user` |
| (new) | `POST` | `/api/auth/refresh` | `app.routers.auth.refresh` |
| (new) | `POST` | `/api/auth/logout` | `app.routers.auth.logout` |
| (admin) | `GET` | `/api/admin/emails` | `app.routers.admin.admin_list_emails` |
| (admin) | `GET` | `/api/admin/audit` | `app.routers.admin.admin_list_audit_log` |
| (admin) | `DELETE` | `/api/admin/users/{id}` | `app.routers.admin.admin_delete_user` |

## Request shape notes

### `/api/search`

The FastAPI implementation accepts the query text under either
`?query=...` (the Vue convention) or `?q=...` (the FastAPI
default). Both alias to the same handler.

### `/api/auth/{login,register,refresh}`

Returns:

```json
{
  "token": "<jwt>",
  "user": {"id": 1, "username": "admin", "email": "...", "role": "admin", ...}
}
```

The `token` is the access-token JWT — the same value the backend
sets as the `cenidim_session` HttpOnly cookie. Mirroring it in
the body keeps the Vue dashboard's localStorage stash working
without forcing it to read `document.cookie`.

### `/api/auth/me`

`GET /api/auth/me` returns the current `UserOut`. Mirrors the Go
contract.

### Admin song CRUD

`POST /api/admin/songs` returns the created `SongOut` (with `id`)
so the dashboard's `adminCreateSong(payload)` returns a usable
song object to its caller. The Go backend used to return
`{"message": "Song created"}`; that path now goes via the
`/api/admin/songs/{id}` GET for the dashboard to refresh.

### Admin user CRUD

`POST /api/admin/users` returns `{"user": UserOut}` per the Go
contract; `PUT/DELETE` return `{"message": "..."}`.
