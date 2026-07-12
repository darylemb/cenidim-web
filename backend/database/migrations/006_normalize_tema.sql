-- 006_normalize_tema.sql
-- The runtime path in handlers/stats.go already groups themes by
-- LOWER(TRIM(tema)) and re-emits each key in canonical Title-Case
-- form (canonicalTema). This means the dashboard is correct even
-- without any DB rewrite.
--
-- This migration is intentionally a no-op for now — it documents
-- the runtime invariant and reserves the migration slot. A future
-- migration could rewrite the underlying column in bulk if exports
-- or admin UI start surfacing the raw value with case-sensitive
-- keys, but until that need arises we let the runtime path do the
-- work.

SELECT '006_normalize_tema: runtime normalization is performed in handlers/stats.go' AS note;
