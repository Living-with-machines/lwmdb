import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from lib_metadata_db.press_directories.models.mitchells import Mitchells
from lib_metadata_db.newspapers.models.mitchells_publication import MitchellsPublication

mitchells_publication_mappings = pd.read_csv(
    "lib_metadata_db/newspapers/import_files/newspapers_overview_with_links.csv", low_memory=False
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


if __name__ == "__main__":
    mitchells_publication_foreign_key_mappings()
