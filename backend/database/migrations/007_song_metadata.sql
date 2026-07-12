-- 007_song_metadata.sql
-- Add structured columns for song-level metadata that was previously
-- embedded in the lyrics body (Dura:, Tema: Personajes: blocks) or
-- printed as author initials at the end of each lyrics file. With
-- these columns populated by the build-db loader and the
-- classify_songs.py step, the dashboard, admin panel, and any
-- future exports can surface the metadata directly instead of
-- scraping it out of the lyrics text.
--
-- Idempotent: the loader tolerates pre-existing rows.

ALTER TABLE songs ADD COLUMN autor TEXT;
ALTER TABLE songs ADD COLUMN compositor TEXT;
ALTER TABLE songs ADD COLUMN duracion TEXT;
ALTER TABLE songs ADD COLUMN personajes TEXT;
