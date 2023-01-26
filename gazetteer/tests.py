import pytest
from django.contrib.gis.geos import Point

from .models import Place


@pytest.fixture
def manc_point() -> Point:
    """Return example centre of Manchester coordinate Point.

    Note:
        * Point.x is usually latitude and Point.y longitude.
    """
    return Point(53.4808, 2.2426)


def test_create_place(manc_point) -> None:
    """Test creating a Place with a coordinates component without saving."""
    test_place = Place(
        wikidata_id="an-id-for-manchester",
        label="Manchester",
        latitude=manc_point.x,
        longitude=manc_point.y,
        coordinates=manc_point,
    )
    assert test_place.coordinates == manc_point
