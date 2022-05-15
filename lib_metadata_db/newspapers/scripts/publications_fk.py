import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from lib_metadata_db.newspapers.models.mitchells_publication import MitchellsPublication
from lib_metadata_db.newspapers.models.publications import Publication

mitchells_publication_mappings = pd.read_csv(
    "lib_metadata_db/newspapers/import_files/newspapers_overview_with_links.csv", low_memory=False
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


if __name__ == "__main__":
    publication_foreign_key_mappings()
