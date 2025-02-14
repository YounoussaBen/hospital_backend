import logging
import warnings

from django.conf import settings
from django.test.runner import DiscoverRunner


class CustomTestRunner(DiscoverRunner):
    def setup_test_environment(self):
        super().setup_test_environment()
        logging.disable(logging.CRITICAL) # Disable logging during tests
        settings.DEBUG = True

        # Update DATABASES setting to use in-memory SQLite database
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',  # Use in-memory database
            }
        }

        # Update CACHE setting to use dummy cache
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            }
        }

    def teardown_test_environment(self):
        super().teardown_test_environment()
        # Custom teardown code, if any

    def run_tests(self, test_labels, **kwargs):

        with warnings.catch_warnings():
            # warnings.simplefilter("ignore", ResourceWarning)
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            return super().run_tests(test_labels, **kwargs)
