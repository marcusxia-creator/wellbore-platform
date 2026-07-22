"""Test settings.

Removes the GeoDjango (`django.contrib.gis`) app and swaps the PostGIS engine
for the plain PostgreSQL engine, so the suite can run without the GDAL/GEOS
system libraries installed locally. The wells models store coordinates as plain
Float fields (no geometry columns), so nothing is lost for testing purposes.

Database connection defaults to the local Docker Postgres published on port
5433, overridable via TEST_POSTGRES_* environment variables (e.g. host "db" and
port 5432 when running inside the Docker network).
"""

import os

from config.settings import *  # noqa: F401,F403

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.gis"]  # noqa: F405

DATABASES = {
    "default": {
        **DATABASES["default"],  # noqa: F405
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("TEST_POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("TEST_POSTGRES_PORT", "5433"),
        "NAME": os.getenv("TEST_POSTGRES_DB", "wellbore_db"),
        "USER": os.getenv("TEST_POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("TEST_POSTGRES_PASSWORD", "postgres"),
    }
}
