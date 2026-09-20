# Migration plan

- Use Alembic autogenerate when models stabilise
- For SQLite→Postgres: export data and run migrations on new DB
- Verify data types and numeric precision
