from io import StringIO

import pytest
from django.core.management import call_command

# pytestmark = [pytest.mark.django_db]


@pytest.mark.django_db
@pytest.mark.cli
class TestCustomLoadFixturesCommand:
    """Test the custom `loadfixtures` command."""

    @pytest.mark.xfail(reason="AttributeError: 'Series' object has no attribute 'NLP'")
    def test_mitchells(self):
        # monkeypatch.setattr('builtins.input', lambda _: "mitchells_publication_for_linking.csv")
        out = StringIO()
        call_command("loadfixtures", "mitchells", force=True, stdout=out)
        assert False
        # self.assertIn("Expected output", out.getvalue())

    @pytest.mark.xfail(reason="SystemExit: App(s) not allowed: ['gazzetteer']")
    def test_gazzetteer(self):
        out = StringIO()
        call_command("loadfixtures", "gazzetteer", force=True, stdout=out)
        # self.assertIn("Expected output", out.getvalue())
        assert "Expected output" in out.getvalue()
