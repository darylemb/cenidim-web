-- 005_admin_email.sql
-- Re-points the seed admin's email to the operator's Google account so
-- that Google OAuth sign-in (which uses findOrCreateUser by email) can
-- match the existing admin row instead of auto-provisioning a new
-- viewer account.
--
-- The migration is idempotent and respects manual changes:
--   * If the admin email is still admin@cenidim.mx, update it.
--   * If the admin email is already darylemb@gmail.com, no-op.
--   * If the operator changed the admin email to something else
--     manually after the first deploy, the WHERE clause won't
--     match and the migration won't undo their change.

UPDATE users
SET email = 'darylemb@gmail.com'
WHERE username = 'admin' AND email = 'admin@cenidim.mx';
