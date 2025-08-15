-- convert_created_at_to_timestamptz.sql
--
-- Converts the `created_at` column on the `report` table from
-- TIMESTAMP (without time zone) to TIMESTAMPTZ (with time zone).
--
-- IMPORTANT:
-- 1) Backup your database before running this script.
-- 2) This script assumes the `report` table is named `report`.
-- 3) The conversion treats existing timestamp values as UTC.
--
-- To run:
--   psql "$DATABASE_URL" -f convert_created_at_to_timestamptz.sql
-- or
--   psql "$DATABASE_URL" -c "ALTER TABLE report ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'; ALTER TABLE report ALTER COLUMN created_at SET DEFAULT now();"

BEGIN;

-- Convert the column to timestamptz, interpreting stored values as UTC
ALTER TABLE report
    ALTER COLUMN created_at TYPE timestamptz
    USING created_at AT TIME ZONE 'UTC';

-- Ensure the default is a timezone-aware current timestamp
ALTER TABLE report
    ALTER COLUMN created_at SET DEFAULT now();

COMMIT;

-- Rollback (if needed):
-- You can convert back to timestamp without time zone with:
-- ALTER TABLE report ALTER COLUMN created_at TYPE timestamp WITHOUT time zone USING created_at AT TIME ZONE 'UTC';
