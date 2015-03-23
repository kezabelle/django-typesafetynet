# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import django
from django.conf import settings

def pytest_configure():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:"
                    }
                },
            INSTALLED_APPS=(
                'django.contrib.auth',
                'django.contrib.contenttypes',
            ),
            MIDDLEWARE_CLASSES=(),
            # allegedly this might work ... http://stackoverflow.com/a/25267435
            # and https://gist.github.com/nealtodd/2869341f38f5b1eeb86d
            MIGRATION_MODULES={
                'auth': 'test_auth.migrations',
                'contenttypes': 'test_contenttypes.migrations',
            }
        )
    if hasattr(django, 'setup'):
        django.setup()
