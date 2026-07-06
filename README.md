# Wellbore Inventory Platform

Django + Django REST Framework backend, PostgreSQL/PostGIS database, and React frontend for well search, status filtering, formation filtering, maps, and well register views.

## Current Features

- Django backend with REST API
- React dashboard with map, filters, and well table
- Existing PostgreSQL well tables mapped with unmanaged Django models
- Cached derived tables for fast filtering:
  - `well_status_category`
  - `well_production_formation`
- Well status categories:
  - `ABD`
  - `Suspended`
  - `Inactive`
  - `Active`
- Production/injection formation filter with semicolon-split normalized values
- OpenStreetMap, Google Map, and Google Satellite map modes

## Project Structure

```text
backend/
  manage.py
  config/
  apps/
    wells/
    casing/
    inventory/
    costs/
    formations/
    completions/
frontend/
  src/
    api/
    components/
    pages/
deployment/
  backend.Dockerfile
  frontend.Dockerfile
docker-compose.yml
.env.example
README.md
```

## Prerequisites

Install these before running the app:

- Git
- Docker Desktop
- PostgreSQL client tools if you need to restore a database dump locally:
  - `createdb`
  - `pg_restore`
  - `psql`

On Windows, Docker Desktop should show `Engine running`.

## Database Requirement

This app expects an existing PostgreSQL database named `wellbore_db` or another database with the same table structure.

Important source tables include:

```text
well_header
well_location
well_status
well_drilling
well_casing
well_production_summary
wellstor_all
```

Django reads these tables with `managed = False`, meaning Django does not create or alter those imported source tables.

Django does create and manage these cache tables:

```text
well_status_category
well_production_formation
```

## Setup From GitHub

Clone the repository:

```powershell
git clone <your-repo-url>
cd Django_PostgreSql_React
```

Create your local environment file:

```powershell
copy .env.example .env
```

Edit `.env` and set your database values:

```env
POSTGRES_DB=wellbore_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
```

Use `host.docker.internal` when PostgreSQL is running on your host computer and Django runs inside Docker.

## Restore A Database Dump

If you received a dump file such as:

```text
wellbore_db_20260617_115022.dump
```

restore it into local PostgreSQL.

Create the database:

```powershell
createdb -U postgres wellbore_db
```

Restore the dump:

```powershell
pg_restore -U postgres -d wellbore_db C:\path\to\wellbore_db_20260617_115022.dump
```

If the database already exists and should be replaced, drop and recreate it carefully:

```powershell
dropdb -U postgres wellbore_db
createdb -U postgres wellbore_db
pg_restore -U postgres -d wellbore_db C:\path\to\wellbore_db_20260617_115022.dump
```

Do not commit database dumps to GitHub. They are ignored by `.gitignore`.

## Run With Docker

Start Docker Desktop first.

Then run:

```powershell
docker compose up --build
```

Open:

```text
Frontend:    http://localhost:5173
Backend API: http://localhost:8000/api/wells/
Admin:       http://localhost:8000/admin/
```

## First-Time Backend Setup

In a second terminal, run migrations:

```powershell
cd C:\Users\gxia\Python\Django_PostgreSql_React
docker compose exec backend python manage.py migrate
```

Create a Django admin user if needed:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Refresh derived cache tables:

```powershell
docker compose exec backend python manage.py refresh_well_status_categories
docker compose exec backend python manage.py refresh_well_production_formations
```

Run the cache refresh commands again whenever the source database tables are re-imported or significantly changed.

## Google Maps

OpenStreetMap works without an API key.

Google Map and Google Satellite modes require a Google Maps JavaScript API key.

Set this in `.env`:

```env
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

Then rebuild:

```powershell
docker compose up --build
```

Without this key, Google map modes show a message instead of rendering a Google map.

## Useful API Endpoints

```text
GET /api/wells/
GET /api/wells/{base_uwi}/
GET /api/well-statuses/
GET /api/actual-well-statuses/
GET /api/well-types/
GET /api/production-injection-formations/
```

Example filters:

```text
/api/wells/?status=Inactive
/api/wells/?status=ABD&actual_status=ABD OIL
/api/wells/?well_type=OIL
/api/wells/?prod_inject_frmtn=Cbs_ss
/api/wells/?prod_inject_frmtn=Cbs_ss&prod_inject_frmtn=Cambrian
```

## Developer Notes

The frontend calls the backend at:

```text
http://localhost:8000/api
```

The backend connects to PostgreSQL using environment variables from `.env`.

For Docker on Windows with local PostgreSQL, this is usually correct:

```env
POSTGRES_HOST=host.docker.internal
```

If PostgreSQL is running as a Docker Compose service instead, use:

```env
POSTGRES_HOST=db
```

and start the optional database profile:

```powershell
docker compose --profile docker-db up --build
```

## Common Commands

Start app:

```powershell
docker compose up --build
```

Stop app:

```powershell
docker compose down
```

Run migrations:

```powershell
docker compose exec backend python manage.py migrate
```

Refresh status cache:

```powershell
docker compose exec backend python manage.py refresh_well_status_categories
```

Refresh formation cache:

```powershell
docker compose exec backend python manage.py refresh_well_production_formations
```

Open Django shell:

```powershell
docker compose exec backend python manage.py shell
```

Check backend health:

```powershell
docker compose exec backend python manage.py check
```

## Troubleshooting

If `docker` is not recognized:

- Install Docker Desktop.
- Restart PowerShell.
- Confirm:

```powershell
docker --version
docker compose version
```

If Docker cannot connect to the engine:

- Open Docker Desktop.
- Wait for `Engine running`.
- Try again.

If Django cannot connect to PostgreSQL:

- Confirm PostgreSQL is running.
- Confirm `.env` has the correct password.
- Use `POSTGRES_HOST=host.docker.internal` for host PostgreSQL from Docker.
- Test with:

```powershell
psql -h localhost -U postgres -d wellbore_db
```

If the frontend does not reflect changes:

- Hard refresh the browser with `Ctrl + F5`.
- Rebuild:

```powershell
docker compose up --build
```

If Google maps do not render:

- Confirm `VITE_GOOGLE_MAPS_API_KEY` is set in `.env`.
- Confirm the Google Maps JavaScript API is enabled for the key.
- Rebuild the frontend after changing the key.

## Production Notes

The current Docker setup is for development. For production, use:

- Django with Gunicorn instead of `runserver`
- Nginx or another reverse proxy
- HTTPS
- `DJANGO_DEBUG=0`
- strong `DJANGO_SECRET_KEY`
- restricted `DJANGO_ALLOWED_HOSTS`
- managed PostgreSQL or a secured database server
- regular database backups
