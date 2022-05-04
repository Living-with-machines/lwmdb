import pandas as pd
import json
from ast import literal_eval

from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication
from lib_metadata_db.gazetteer.models.admin_county import AdminCounty
from lib_metadata_db.gazetteer.models.historic_county import HistoricCounty
from lib_metadata_db.gazetteer.models.country import Country
from django.core.management import BaseCommand

ALREDY_LOADED_ERROR_MESSAGE = """
    If you need to reload the child data from the CSV file,
    first delete the db.sqlite3 file to destroy the database.
    Then, run `python manage.py migrate` for a new empty
    database with tables
    """

# --------------------------------------
class Command(BaseCommand):

    # Show this when the user types help
    help = "Loads data from the gazetteer files."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_location",
            type=str,
            help="Indicates the location of the file to upload.",
        )

    def handle(self, *args, **kwargs):

        data_to_load_path = kwargs["file_location"]

        # Show this if the data already exist in the database
        if PlaceOfPublication.objects.exists():
            print("child data already loaded...exiting.")
            print(ALREDY_LOADED_ERROR_MESSAGE)
            return

        # Show this before loading the data into the database
        print("Loading places data")

        # --------------------------------------
        # Load historic counties manual mapping:
        with open(data_to_load_path + "dict_historic_counties.json") as json_file:
            dict_historic_counties = json.load(json_file)

        # --------------------------------------
        # Load admin counties manual mapping:
        with open(data_to_load_path + "dict_admin_counties.json") as json_file:
            dict_admin_counties = json.load(json_file)

        # --------------------------------------
        # Load countries manual mapping:
        with open(data_to_load_path + "dict_countries.json") as json_file:
            dict_countries = json.load(json_file)

        # --------------------------------------
        # Load list of places of publication (Wikidata IDs) in Mitchells:
        with open(data_to_load_path + "wikidata_ids_publication_mitchells.txt") as file:
            list_mitchells_wqid = file.readlines()
        list_mitchells_wqid = [
            wq.strip() for wq in list_mitchells_wqid if wq.startswith("Q")
        ]

        # --------------------------------------
        # Load gazetteer:
        df = pd.read_csv(
            data_to_load_path + "wikidata_gazetteer.csv",
            low_memory=False,
            usecols=[
                "wikidata_id",
                "english_label",
                "latitude",
                "longitude",
                "geonamesIDs",
            ],
        )

        def literal_return(val):
            try:
                return literal_eval(val)
            except ValueError:
                return []

        # Parse list of geonames IDs in the gazetteer:
        df["geonamesIDs"] = df["geonamesIDs"].apply(literal_return)

        # Create dictionary of relevant locations:
        dict_gaz_entries = dict()
        for i, row in df.iterrows():
            if row["wikidata_id"] in list_mitchells_wqid:
                dict_gaz_entries[row["wikidata_id"]] = {
                    "place_wikidata_id": row["wikidata_id"],
                    "place_label": row["english_label"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "geonames_ids": ",".join(row["geonamesIDs"]),
                    "hcounty": dict_historic_counties.get(row["wikidata_id"], ["", ""]),
                    "admin_county": dict_admin_counties.get(
                        row["wikidata_id"], ["", ""]
                    ),
                    "country": dict_countries.get(row["wikidata_id"], ["", ""]),
                }

        # Code to load the data into database
        for wkqid in dict_gaz_entries:

            # Historic county record:
            historic_county = HistoricCounty(
                hcounty_wikidata_id=dict_gaz_entries[wkqid]["hcounty"][0],
                hcounty_label=dict_gaz_entries[wkqid]["hcounty"][1],
            )
            historic_county.save()

            # Admin county record:
            admin_county = AdminCounty(
                admin_county_wikidata_id=dict_gaz_entries[wkqid]["admin_county"][0],
                admin_county_label=dict_gaz_entries[wkqid]["admin_county"][1],
            )
            admin_county.save()

            # Country record:
            country = Country(
                country_wikidata_id=dict_gaz_entries[wkqid]["country"][0],
                country_label=dict_gaz_entries[wkqid]["country"][1],
            )
            country.save()

            # Place of publication record:
            place_of_publication = PlaceOfPublication(
                place_wikidata_id=dict_gaz_entries[wkqid]["place_wikidata_id"],
                place_label=dict_gaz_entries[wkqid]["place_label"],
                latitude=dict_gaz_entries[wkqid]["latitude"],
                longitude=dict_gaz_entries[wkqid]["longitude"],
                geonames_ids=dict_gaz_entries[wkqid]["geonames_ids"],
                historic_county=historic_county,
                admin_county=admin_county,
                country=country,
            )
            place_of_publication.save()
