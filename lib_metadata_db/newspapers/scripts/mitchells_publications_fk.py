import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from lib_metadata_db.press_directories.models.mitchells import Mitchells
from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication
from lib_metadata_db.newspapers.models.mitchells_publication import MitchellsPublication
from lib_metadata_db.newspapers.models.publications import Publication

mitchells_publication_mappings = pd.read_csv(
    "lib_metadata_db/newspapers/import_files/newspapers_overview_with_links.csv", low_memory=False
)

place_of_publication_mappings = pd.read_csv(
    "lib_metadata_db/press_directories/import_files/MPD_export_1846_1920_geo_coded.csv", low_memory=False
)


def update_publication_keys(mitchells_publication):
    associated_mitchells_publications = mitchells_publication_mappings.loc[
        mitchells_publication_mappings["AcquiredYears"]
        == mitchells_publication.year,
        "link_to_mpd",
    ]
    Publication.objects.filter(publication_code__in=associated_mitchells_publications).update(
        mitchells_publication_id=mitchells_publication.id
    )


def publication_foreign_key_mappings():
    Parallel(n_jobs=-1, prefer="threads", verbose=5)(
        delayed(update_publication_keys)(mitchells_publication) for mitchells_publication in tqdm(MitchellsPublication.objects.all())
    )


def update_mitchells_publications_keys(mitchells):
    associated_mitchells = mitchells_publication_mappings.loc[
        mitchells_publication_mappings["Title"]
        == mitchells.title,
        "AcquiredYears",
    ]
    MitchellsPublication.objects.filter(year__in=associated_mitchells).update(
        mitchells_id=mitchells.id
    )


def mitchells_publication_foreign_key_mappings():
    Parallel(n_jobs=-1, prefer="threads", verbose=5)(
        delayed(update_mitchells_publications_keys)(mitchells) for mitchells in tqdm(Mitchells.objects.all())
    )


def update_place_of_publication_keys(place_of_publication):
    associated_mitchells_publications = place_of_publication_mappings.loc[
        place_of_publication_mappings["wiki_id"]
        == place_of_publication.place_wikidata_id,
        "S-TITLE",
    ]
    Publication.objects.filter(publication_code__in=associated_mitchells_publications).update(
        mitchells_publication_id=mitchells_publication.id
    )


def place_of_publication_foreign_key_mappings():
    Parallel(n_jobs=-1, prefer="threads", verbose=5)(
        delayed(update_place_of_publication_keys)(place_of_publication) for place_of_publication in tqdm(PlaceOfPublication.objects.all())
    )

def update_mitchells_keys(place_of_publication):
    associated_place_of_publication = place_of_pub_press_directory_mappings.loc[
        place_of_pub_press_directory_mappings["wiki_id"]
        == place_of_publication.place_wikidata_id,
        "id",
    ]
    Mitchells.objects.filter(title__in=associated_place_of_publication).update(
        place_of_publication_id=place_of_publication.id
    )


def mitchells_foreign_key_mappings():
    Parallel(n_jobs=-1, prefer="threads", verbose=5)(
        delayed(update_mitchells_keys)(place_of_publication) for place_of_publication in tqdm(PlaceOfPublication.objects.all())
    )


if __name__ == "__main__":
    publication_foreign_key_mappings()

    mitchells_publication_foreign_key_mappings()
