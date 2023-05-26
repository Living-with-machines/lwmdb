import json

import numpy as np
import pandas as pd

from lwmdb.management.commands.fixtures import AUTO_FILE_LOCATIONS, Fixture

from ...models import AdminCounty, Country, HistoricCounty, Place


class Command(Fixture):
    app_name = "gazetteer"
    models = [AdminCounty, Country, HistoricCounty, Place]

    def __init__(self, force=False):
        self.force = force
        super(Fixture, self).__init__()

    def get_main_frame(self, path, list_mitchells_wqid):
        main_frame = pd.read_csv(
            path,
            low_memory=False,
            usecols=[
                "wikidata_id",
                "english_label",
                "latitude",
                "longitude",
                "geonamesIDs",
            ],
        ).rename(
            {
                "wikidata_id": "place_wikidata_id",
                "english_label": "place_label",
                "geonamesIDs": "geonames_ids",
            },
            axis=1,
        )

        filtered = [x for x in main_frame.place_wikidata_id if x in list_mitchells_wqid]
        main_frame = main_frame.set_index("place_wikidata_id").loc[filtered]
        main_frame.reset_index(inplace=True)
        main_frame["place_pk"] = np.arange(1, len(main_frame) + 1)

        # reorder columns
        main_frame = main_frame[
            ["place_pk"] + [x for x in main_frame.columns if not x == "place_pk"]
        ]

        return main_frame

    def create_gazetteer_fixtures(self):
        output_dir = self.get_output_dir()

        wikidata_gazetteer = (
            self.get_input(
                "Where is wikidata_gazetteer.csv?",
                AUTO_FILE_LOCATIONS["wikidata_gazetteer"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["wikidata_gazetteer"]
        )
        wikidata_gazetteer = self.try_file(wikidata_gazetteer, False)

        dict_historic_counties = (
            self.get_input(
                "Where is dict_historic_counties.json?",
                AUTO_FILE_LOCATIONS["dict_historic_counties"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["dict_historic_counties"]
        )
        dict_historic_counties = self.try_file(dict_historic_counties, True, json.loads)

        dict_admin_counties = (
            self.get_input(
                "Where is dict_admin_counties.json?",
                AUTO_FILE_LOCATIONS["dict_admin_counties"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["dict_admin_counties"]
        )
        dict_admin_counties = self.try_file(dict_admin_counties, True, json.loads)

        dict_countries = (
            self.get_input(
                "Where is dict_countries.json?",
                AUTO_FILE_LOCATIONS["dict_countries"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["dict_countries"]
        )
        dict_countries = self.try_file(dict_countries, True, json.loads)

        wikidata_ids_publication_mitchells = (
            self.get_input(
                "Where is dict_countries.json?",
                AUTO_FILE_LOCATIONS["wikidata_ids_publication_mitchells"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["wikidata_ids_publication_mitchells"]
        )
        wikidata_ids_publication_mitchells = self.try_file(
            wikidata_ids_publication_mitchells
        )
        list_mitchells_wqid = [
            x.strip()
            for x in wikidata_ids_publication_mitchells.splitlines()
            if x.strip().startswith("Q")
        ]

        # Correct all the dictionaries
        correct_dict = lambda o: [
            (k, v[0], v[1]) for k, v in o.items() if not v[0].startswith("Q")
        ] + [(k, v[1], v[0]) for k, v in o.items() if v[0].startswith("Q")]

        dict_historic_counties = correct_dict(dict_historic_counties)
        dict_admin_counties = correct_dict(dict_admin_counties)
        dict_countries = correct_dict(dict_countries)

        # create assisting frames
        hcounties_df = pd.DataFrame(
            dict_historic_counties,
            columns=["place_wikidata_id", "hcounty_label", "hcounty_wikidata_id"],
        )
        admin_county_df = pd.DataFrame(
            dict_admin_counties,
            columns=[
                "place_wikidata_id",
                "admin_county_label",
                "admin_county_wikidata_id",
            ],
        ).rename({}, axis=1)
        countries_df = pd.DataFrame(
            dict_countries,
            columns=["place_wikidata_id", "country_label", "country_wikidata_id"],
        )

        # create main frame
        main_frame = self.get_main_frame(wikidata_gazetteer, list_mitchells_wqid)

        # merge with all the separate data
        main_frame = pd.merge(
            main_frame, hcounties_df, on="place_wikidata_id", how="left"
        )
        main_frame = pd.merge(
            main_frame, admin_county_df, on="place_wikidata_id", how="left"
        )
        main_frame = pd.merge(
            main_frame, countries_df, on="place_wikidata_id", how="left"
        )

        main_frame.rename(
            {
                "admin_county_label": "admin_county__label",
                "admin_county_wikidata_id": "admin_county__wikidata_id",
                "hcounty_label": "historic_county__label",
                "hcounty_wikidata_id": "historic_county__wikidata_id",
                "country_label": "country__label",
                "country_wikidata_id": "country__wikidata_id",
            },
            axis=1,
            inplace=True,
        )

        # split back up into dataframes
        historic_county_table = (
            main_frame[["historic_county__label", "historic_county__wikidata_id"]]
            .drop_duplicates()
            .copy()
        )
        historic_county_table = historic_county_table.replace({"": np.nan}).dropna()
        historic_county_table["historic_county__pk"] = np.arange(
            1, len(historic_county_table) + 1
        )

        admin_county_table = (
            main_frame[["admin_county__label", "admin_county__wikidata_id"]]
            .drop_duplicates()
            .copy()
        )
        admin_county_table = admin_county_table.replace({"": np.nan}).dropna()
        admin_county_table["admin_county__pk"] = np.arange(
            1, len(admin_county_table) + 1
        )

        country_table = (
            main_frame[["country__label", "country__wikidata_id"]]
            .drop_duplicates()
            .copy()
        )
        country_table = country_table.replace({"": np.nan}).dropna()
        country_table["country__pk"] = np.arange(1, len(country_table) + 1)

        place_table = main_frame.copy()

        place_table = (
            pd.merge(
                place_table,
                historic_county_table,
                on=["historic_county__label", "historic_county__wikidata_id"],
                how="left",
            )
            .drop(["historic_county__label", "historic_county__wikidata_id"], axis=1)
            .rename({"historic_county__pk": "historic_county_id"}, axis=1)
        )

        place_table = (
            pd.merge(
                place_table,
                admin_county_table,
                on=["admin_county__label", "admin_county__wikidata_id"],
                how="left",
            )
            .drop(["admin_county__label", "admin_county__wikidata_id"], axis=1)
            .rename({"admin_county__pk": "admin_county_id"}, axis=1)
        )

        place_table = (
            pd.merge(
                place_table,
                country_table,
                on=["country__label", "country__wikidata_id"],
                how="left",
            )
            .drop(["country__label", "country__wikidata_id"], axis=1)
            .rename({"country__pk": "country_id"}, axis=1)
        )

        place_table = place_table.fillna("").set_index("place_pk")
        place_table = place_table.rename(
            {"place_label": "label", "place_wikidata_id": "wikidata_id"}, axis=1
        )

        # place_table.to_csv("(temp)-place_table.csv")

        historic_county_table = historic_county_table.set_index(
            "historic_county__pk"
        ).rename({x: x.split("__")[1] for x in historic_county_table.columns}, axis=1)

        admin_county_table = admin_county_table.set_index("admin_county__pk").rename(
            {x: x.split("__")[1] for x in admin_county_table.columns}, axis=1
        )

        country_table = country_table.set_index("country__pk").rename(
            {x: x.split("__")[1] for x in country_table.columns}, axis=1
        )

        models = [
            (
                historic_county_table,
                HistoricCounty,
            ),
            (
                admin_county_table,
                AdminCounty,
            ),
            (country_table, Country),
            (
                place_table,
                Place,
            ),
        ]
        self.write_models(models)

        self.done()
