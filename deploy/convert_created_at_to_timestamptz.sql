-- convert_created_at_to_timestamptz.sql
--
-- Converts the `created_at` column on the `crypto_report` table from
-- TIMESTAMP (without time zone) to TIMESTAMPTZ (with time zone).
-- 2) This script assumes the `crypto_report` table is named `crypto_report`.
--   psql "$DATABASE_URL" -c "ALTER TABLE crypto_report ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'; ALTER TABLE crypto_report ALTER COLUMN created_at SET DEFAULT now();"

BEGIN;

ALTER TABLE crypto_report
    ALTER COLUMN created_at TYPE timestamptz
    USING created_at AT TIME ZONE 'UTC';

ALTER TABLE crypto_report
    ALTER COLUMN created_at SET DEFAULT now();

COMMIT;

-- ALTER TABLE crypto_report ALTER COLUMN created_at TYPE timestamp WITHOUT time zone USING created_at AT TIME ZONE 'UTC';
