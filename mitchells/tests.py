from io import StringIO
from pathlib import Path

import pytest
from django.test import TestCase

from lwmdb.utils import app_data_path, download_file

from .import_fixtures import MITCHELLS_LOCAL_LINK_EXCEL_URL, MitchellsFixture
from .models import Price


@pytest.mark.django_db
class MitchelsFixture(TestCase):
    # @pytest.mark.xfail
    def test_load_fixtures(self):
        out: StringIO = StringIO()
        creator: MitchellsFixture = MitchellsFixture(force=False)
        # creator.app_name = "mitchells"
        # assert creator.force == True
        creator.load_fixtures()
        assert 0 > Price.objects.count()
        # self.assertIn("Expected output", out.getvalue())# Create your tests here.
        # assert 'fun' in out.getvalue()


@pytest.mark.remotedata
def test_download_mitchells_xslx() -> None:
    """Test downloading `MITCHELLS_LOCAL_LINK_EXCEL_URL` fixture."""
    path: Path = app_data_path("mitchells") / "mitchells.xslx"
    success: bool = download_file(path, MITCHELLS_LOCAL_LINK_EXCEL_URL)
    assert success
