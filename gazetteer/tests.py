import pytest
from django.contrib.gis.geos import Point

from .models import Place


@pytest.fixture
def manc_point() -> Point:
    """Return example centre of Manchester coordinate Point.

    Note:
        * Point.x is usually latitude and Point.y longitude.
    """
    return Point(53.4808, -2.2426)


@pytest.fixture
def liverpool_point() -> Point:
    """Return example centre of Manchester coordinate Point."""
    return Point(53.400, -2.983333)


@pytest.mark.django_db
class TestGeoSpatial:

    """Test using geospatial functionality of `coordinates` `Point`."""

    def test_create_place_and_distance(self, manc_point, liverpool_point) -> None:
        """Test creating a Place with `coordinates` and calc distance.

        Note:
            * Curvature not included in distance between points see:
              https://docs.djangoproject.com/en/4.2/ref/contrib/gis/geos/#django.contrib.gis.geos.GEOSGeometry.distance
        """
        manc_to_liverpool_2d_dist: float = 0.745126846442269
        test_manc = Place(
            wikidata_id="an-id-for-manchester",
            label="Manchester",
            latitude=manc_point.x,
            longitude=manc_point.y,
            coordinates=manc_point,
        )
        assert test_manc.coordinates == manc_point
        test_manc.save()
        assert (
            test_manc.coordinates.distance(liverpool_point) == manc_to_liverpool_2d_dist
        )
