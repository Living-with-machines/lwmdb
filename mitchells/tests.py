from io import StringIO
from logging import INFO
from pathlib import Path

import pytest
from django.test import TestCase

from lwmdb.utils import download_file

from .import_fixtures import (
    MITCHELLS_LOCAL_LINK_EXCEL_PATH,
    MITCHELLS_LOCAL_LINK_EXCEL_URL,
    MitchellsFixture,
)
from .models import Price


@pytest.mark.xfail(reason="MitchellsFixture failes to commit changes")
@pytest.mark.django_db
class TestMitchelsFixture(TestCase):
    # @pytest.mark.xfail
    def test_load_fixtures(self) -> None:
        out: StringIO = StringIO()
        creator: MitchellsFixture = MitchellsFixture(force=False)
        # creator.app_name = "mitchells"
        # assert creator.force == True
        creator.load_fixtures()
        assert 0 > Price.objects.count()
        # self.assertIn("Expected output", out.getvalue())# Create your tests here.
        # assert 'fun' in out.getvalue()


def test_mitchells_xlsx_path(mitchells_data_path) -> None:
    """Test `app_data_path` for mitchells excel data."""
    assert (
        mitchells_data_path
        == Path("mitchells") / "data" / MITCHELLS_LOCAL_LINK_EXCEL_PATH
    )


def test_download_local_mitchells_excel(caplog, mitchells_data_path) -> None:
    """Test downloading `MITCHELLS_LOCAL_LINK_EXCEL_URL` fixture.

    Note:
        The `assert LOG in caplog.messages` is designed to work whether it's
        downloaded or not (easing caching).
    """
    caplog.set_level(INFO)
    success: bool = download_file(mitchells_data_path, MITCHELLS_LOCAL_LINK_EXCEL_URL)
    assert success
    LOG = f"{MITCHELLS_LOCAL_LINK_EXCEL_URL} file available from {mitchells_data_path}"
    assert LOG in caplog.messages
