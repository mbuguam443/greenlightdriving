from django.test import TestCase

# Note: this repo's migration graph is kept as no-ops (schema is repaired
# directly in production), so model-backed endpoints are verified against the
# live/local database rather than a migrated test fixture.
