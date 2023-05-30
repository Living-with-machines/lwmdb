import json
from pathlib import Path
from typing import Final, Type

import numpy as np
import pandas as pd
from django.db.models import Model

from lwmdb.management.commands.fixtures import AUTO_FILE_LOCATIONS, Fixture

from .models import (
    Entry,
    EntryPoliticalLeanings,
    EntryPrices,
    Issue,
    PoliticalLeaning,
    Price,
)

MITCHELLS_PUB_FOR_LINK_KEY: str = "mitchells_publication_for_linking"
MITCHELLS_CSV_URL: str = (
    "https://bl.iro.bl.uk/downloads/da65047c-4d62-4ab7-946f-8e61e5f6f331?locale=en"
)
MITCHELLS_EXCEL_URL: str = (
    "https://bl.iro.bl.uk/downloads/9d515cf9-c76d-484f-86ee-ddc642f32479?locale=en"
)
MITCHELLS_CSV_PATH: Path = Path(MITCHELLS_PUB_FOR_LINK_KEY + ".csv")
MITCHELLS_EXCEL_PATH: Path = Path(MITCHELLS_PUB_FOR_LINK_KEY + ".xlsx")

LOCAL_DATA_PATH: Path = Path("mitchells") / "data"

# TODO: We want to look closer into the SettingWithCopyWarning that this script generates
# pd.options.mode.chained_assignment = None
DB_COLS: Final[list[str]] = [
    "title",
    "political_leaning_raw",
    "price_raw",
    "day_of_publication_raw",
    "year",
    "date_established_raw",
    "place_circulation_raw",
    "publication_district_raw",
    "publication_county_raw",
    "persons",
    "organisations",
    "place_of_publication_id",
    "political_leaning_1",
    "price_1",
    "political_leaning_2",
    "price_2",
]

PROJECT_PAPERS_COLS: Final[list[str]] = [
    "NLP",
    "Title",
    "AcquiredYears",
    "Editions",
    "EditionTitles",
    "City",
    "Publisher",
    "UnavailableYears",
    "Collection",
    "UK",
    "Complete",
    "Notes",
    "County",
    "HistoricCounty",
    "First date held",
    "Publication title",
    "link_to_mpd",
]

SELECTED_DB_COLS: Final[list[str]] = [
    "NLP",
    "title",
    "political_leaning_raw",
    "price_raw",
    "day_of_publication_raw",
    "year",
    "date_established_raw",
    "publication_district_raw",
    "publication_county_raw",
    "persons",
    "organisations",
    "political_leaning_1",
    "price_1",
    "political_leaning_2",
    "price_2",
    "place_of_circulation_raw",
    "place_of_publication_id",
]


class MitchellsFixture(Fixture):
    app_name: str = "mitchells"
    models: list[Type[Model]] = [
        Issue,
        Entry,
        PoliticalLeaning,
        Price,
        EntryPoliticalLeanings,
        EntryPrices,
    ]
    db_cols: list[str] = DB_COLS
    selected_db_cols: list[str] = SELECTED_DB_COLS
    project_papers_cols: list[str] = PROJECT_PAPERS_COLS

    def __init__(self, force: bool = False):
        self.force: bool = force
        super(Fixture, self).__init__()

    def get_main_frame(self, mitchells_db, newspapers_overview, wikidata_to_pk):
        data = (
            pd.read_csv(
                mitchells_db,
                dtype={"id": str},
                usecols=["id"] + self.db_cols,
                low_memory=False,
            )
            .rename(
                {
                    "id": "mpd_id",
                    "place_circulation_raw": "place_of_circulation_raw",
                },
                axis=1,
            )
            .convert_dtypes({"id": str})
        )

        # because we renamed above
        self.db_cols = [x for x in self.db_cols if not x == "place_circulation_raw"] + [
            "place_of_circulation_raw"
        ]
        # mpd stands for mitchells press directory

        project_papers = (
            pd.read_csv(
                newspapers_overview,
                dtype={"NLP": str},
                usecols=self.project_papers_cols,
            )
            .rename({"link_to_mpd": "mpd_id"}, axis=1)
            .dropna(subset=["mpd_id"])
            .convert_dtypes({"mpd_id": str})
        )

        main_frame = pd.merge(data, project_papers, on="mpd_id", how="inner")
        main_frame.index = np.arange(1, len(main_frame) + 1)

        # Fix place of publication
        main_frame.place_of_publication_id = main_frame.place_of_publication_id.fillna(
            ""
        ).apply(lambda x: wikidata_to_pk.get(x))

        # Fix year
        main_frame["year"] = main_frame["year"].astype(str) + "-01-01"

        return main_frame

    def create_mitchells_fixtures(self):
        # Get wikidata_to_pk
        PoP_fixtures = self.get_output_dir("gazetteer") / "Place-fixtures.json"
        PoP_fixtures = self.try_file(PoP_fixtures, True, json.loads)
        wikidata_to_pk = {
            x.get("fields", {}).get("wikidata_id"): x.get("pk")
            for x in PoP_fixtures
            if x.get("model") == "gazetteer.place"
        }

        # Get mitchells_db
        mitchells_db = (
            self.get_input(
                "Where is mitchells_db.csv?",
                AUTO_FILE_LOCATIONS["mitchells_db"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["mitchells_db"]
        )
        mitchells_db = self.try_file(mitchells_db, False)

        # Get newspapers_overview
        newspapers_overview = (
            self.get_input(
                "Where is newspapers_overview_with_links.csv?",
                AUTO_FILE_LOCATIONS["newspapers_overview"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["newspapers_overview"]
        )
        newspapers_overview = self.try_file(newspapers_overview, False)

        # Get main frame
        main_frame = self.get_main_frame(
            mitchells_db, newspapers_overview, wikidata_to_pk
        )

        mitchells_entries = main_frame[self.selected_db_cols].drop_duplicates(
            subset=[x for x in self.selected_db_cols if not "raw" in x]
        )
        mitchells_entries["year"] = pd.to_datetime(mitchells_entries["year"]).dt.year
        mitchells_entries.replace(
            {"progresssive": "progressive", "iberal": "liberal"}, inplace=True
        )

        # mitchells.index = PK
        mitchells_entries.index = np.arange(1, len(mitchells_entries) + 1)

        mitchells_issues = pd.DataFrame(
            mitchells_entries.year.drop_duplicates().reset_index(drop=True)
        )
        mitchells_issues.index = np.arange(1, len(mitchells_issues) + 1)

        mitchells_entries["issue_id"] = mitchells_entries.apply(
            lambda x: mitchells_issues.query(f"year == {x.year}").index[0], axis=1
        )

        # Create mitchells_publication_for_linking (for newspapers)
        mitchells_publication_for_linking = mitchells_entries.copy()
        mitchells_publication_for_linking = mitchells_publication_for_linking[["NLP"]]
        mitchells_publication_for_linking[
            "entry"
        ] = mitchells_publication_for_linking.index

        mitchells_publication_for_linking.to_csv(
            AUTO_FILE_LOCATIONS["mitchells_publication_for_linking"]
        )

        # Build political leanings + prices connect back on Mitchells
        dfs = {}
        for x in [
            [
                "mitchells.PoliticalLeaning",
                "political_leaning_1",
                "political_leaning_2",
                "political_leaning_ids",
            ],
            ["mitchells.Price", "price_1", "price_2", "price_ids"],
        ]:
            resulting_df, field1, field2, resulting_column = x
            values = {
                x
                for x in list({x for x in mitchells_entries[field1].dropna()})
                + list({x for x in mitchells_entries[field2].dropna()})
            }
            dfs[resulting_df] = pd.DataFrame(
                values,
                columns=["label"],
                index=np.arange(1, len(values) + 1),
            )

            escape_val = lambda x: x.replace("'", "\\'") if isinstance(x, str) else x
            mitchells_entries[resulting_column] = mitchells_entries.apply(
                lambda x: dfs[resulting_df]
                .query(f"label == '{escape_val(x[field1])}'")
                .index.to_list()
                + dfs[resulting_df]
                .query(f"label == '{escape_val(x[field2])}'")
                .index.to_list(),
                axis=1,
            )

            # dfs[resulting_df].to_csv(resulting_df + ".csv")

        mitchells_entries = mitchells_entries.drop(
            ["political_leaning_1", "political_leaning_2", "price_1", "price_2"], axis=1
        )

        # mitchells_entries.to_csv("(temp)mitchells_entries.csv")

        # Write the easy models the "normal" way
        models = [
            (
                mitchells_issues,
                Issue,
            ),
            (dfs["mitchells.PoliticalLeaning"], PoliticalLeaning),
            (dfs["mitchells.Price"], Price),
            (
                mitchells_entries[
                    [
                        x
                        for x in mitchells_entries.columns
                        if not x
                        in ["NLP", "index", "political_leaning_ids", "price_ids"]
                    ]
                ],
                Entry,
            ),
        ]
        self.write_models(models)

        # Create many-to-many fixtures
        path = self.get_output_dir() / "EntryPoliticalLeanings-fixtures.json"
        fixture_data = [
            {
                "fields": {
                    "political_leaning_id": _id,
                    "entry_id": ix,
                    "order": counter,
                },
            }
            for ix, rows in mitchells_entries[["political_leaning_ids"]].iterrows()
            for counter, _id in enumerate(rows.political_leaning_ids, start=1)
        ]
        fixture_data = [
            {
                "model": "mitchells.entrypoliticalleanings",
                "pk": pk,
                "fields": x.get("fields"),
            }
            for pk, x in enumerate(fixture_data, start=1)
        ]
        path.write_text(json.dumps(fixture_data))

        path = self.get_output_dir() / "EntryPrices-fixtures.json"
        fixture_data = [
            {
                "fields": {
                    "price_id": _id,
                    "entry_id": ix,
                    "order": counter,
                },
            }
            for ix, rows in mitchells_entries[["price_ids"]].iterrows()
            for counter, _id in enumerate(rows.price_ids, start=1)
        ]
        fixture_data = [
            {
                "model": "mitchells.entryprices",
                "pk": pk,
                "fields": x.get("fields"),
            }
            for pk, x in enumerate(fixture_data, start=1)
        ]
        path.write_text(json.dumps(fixture_data))

        self.done()
