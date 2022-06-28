import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication
from lib_metadata_db.press_directories.models.mitchells import Mitchells

place_of_pub_press_directory_mappings = pd.read_csv(
    "lib_metadata_db/press_directories/import_files/MPD_export_1846_1920_geo_coded.csv", low_memory=False
)


def update_mitchells_keys(place_of_publication):
    associated_place_of_publication = place_of_pub_press_directory_mappings.loc[
        place_of_pub_press_directory_mappings["wiki_id"]
        == place_of_publication.place_wikidata_id,
        "S-TITLE",
    ]
    Mitchells.objects.filter(title__in=associated_place_of_publication).update(
        place_of_publication_id=place_of_publication.id
    )


def mitchells_foreign_key_mappings():
    Parallel(n_jobs=-1, prefer="threads", verbose=5)(
        delayed(update_mitchells_keys)(place_of_publication) for place_of_publication in tqdm(PlaceOfPublication.objects.all())
    )


if __name__ == "__main__":
    mitchells_foreign_key_mappings()
