from django.test import TestCase

from providers.registry import get_provider


class ProviderRegistryTests(TestCase):
    def test_vidking_provider_exists(self):
        provider = get_provider("vidking")
        self.assertIsNotNone(provider)
        self.assertEqual(provider.name, "vidking")

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            get_provider("unknown")
