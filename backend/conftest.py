"""Pytest configuration shared by the whole backend test suite.

The legacy well tables are declared with ``managed = False`` because they are
owned by an external database. For tests we flip them to ``managed = True`` so
the test runner creates them in the throwaway test database (combined with the
``--no-migrations`` flag, tables are built directly from the models).
"""


def pytest_configure(config):
    from django.apps import apps as django_apps

    for model in django_apps.get_app_config("wells").get_models():
        model._meta.managed = True
