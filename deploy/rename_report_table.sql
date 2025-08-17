-- Safe migration SQL to rename the existing `report` table to `crypto_report`.
-- Run this on a backed-up database (pg_dump) and on a staging environment first.
-- Usage example:
--   psql "$DATABASE_URL" -f rename_report_table.sql

BEGIN;

-- If the new table already exists, do nothing.
-- If only the old table exists, rename it.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'crypto_report') THEN
        RAISE NOTICE 'Table crypto_report already exists; no rename performed.';
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report') THEN
        EXECUTE 'ALTER TABLE report RENAME TO crypto_report';
        RAISE NOTICE 'Renamed table report -> crypto_report';
    ELSE
        RAISE NOTICE 'Neither report nor crypto_report table found; no action taken.';
    END IF;
END$$;

COMMIT;

-- Rollback (manual):
-- ALTER TABLE IF EXISTS crypto_report RENAME TO report;
