import sys
from unittest import mock

from django.test import SimpleTestCase

import manage


class EntryPointTests(SimpleTestCase):
    def test_wsgi_and_asgi_applications_load(self):
        from config import asgi, wsgi

        self.assertIsNotNone(wsgi.application)
        self.assertIsNotNone(asgi.application)

    def test_manage_runs_command(self):
        with mock.patch("django.core.management.execute_from_command_line") as execute:
            manage.main()

        execute.assert_called_once_with(sys.argv)

    def test_manage_explains_missing_django(self):
        with mock.patch.dict(sys.modules, {"django.core.management": None}):
            with self.assertRaisesMessage(ImportError, "Couldn't import Django"):
                manage.main()
