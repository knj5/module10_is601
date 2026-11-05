# Module 9: Working with Raw SQL in pgAdmin

## Start the project
Run `docker compose up --build -d`, then `docker compose ps`.

- Calculator: http://localhost:8000
- pgAdmin: http://localhost:5050
- pgAdmin login: admin@example.com / admin

## Register PostgreSQL in pgAdmin
- Name: Module 9 PostgreSQL
- Host: db
- Port: 5432
- Maintenance database: fastapi_db
- Username: postgres
- Password: postgres

These are local classroom demonstration credentials.

## SQL execution
Open the Query Tool for fastapi_db.
Run sql/module9.sql one statement at a time against a fresh database.
The tables and records already exist after completing the assignment;
do not rerun CREATE or INSERT statements against that completed database.

The demonstrated operations create two tables, insert two users and
three calculations, retrieve records, join the tables, update ID 1,
and delete ID 2. Final calculation IDs are 1 and 3, with results 6 and 20.

## Relationship
One user can have many calculations. calculations.user_id references
users.id. ON DELETE CASCADE removes a user's calculations if that user
is deleted. The assignment deletes a calculation, not a user.

## Docker adjustments
PostgreSQL is pinned to version 16 for the supplied data directory layout.
docker-compose.override.yml runs the code built into the image instead
of using the Mac folder mount that produced an input/output error.
It also replaces the curl health check with Python's urllib and waits
for PostgreSQL to become healthy before starting the API.
