Convert `crypto_report.created_at` to timestamptz
======================================

What this does
---------------
The SQL script `convert_created_at_to_timestamptz.sql` converts the `created_at`
column on the `crypto_report` table from `timestamp without time zone` to
`timestamp with time zone` (Postgres: `timestamptz`). The script treats existing
values as UTC.

Safety first
------------
- Backup your database before running anything:

  ```bash
  pg_dump "$DATABASE_URL" > backup-before-created_at.sql
  ```

- Run the conversion in a transaction (script already uses BEGIN/COMMIT):

  ```bash
  export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
  psql "$DATABASE_URL" -f deploy/convert_created_at_to_timestamptz.sql
  ```

Using Alembic / Flask-Migrate
-----------------------------
If you use Flask-Migrate / Alembic, you can create a revision with this SQL
inside the upgrade() function or use the `op.execute(...)` helper.

Example snippet for an Alembic revision (inside `upgrade()`):

```python
from alembic import op

op.execute("""
ALTER TABLE crypto_report ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';
ALTER TABLE crypto_report ALTER COLUMN created_at SET DEFAULT now();
""")
```

If you want, I can also create an Alembic revision file for you.
